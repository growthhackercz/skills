#!/usr/bin/env python3
"""Stavový automat publisheru — každá opravená větev má svůj test.

Pokrývá nálezy, kde publisher hlásil úspěch, který se nestal:
  - direct deploy `state: building` (ani chyba, ani hotovo) se bral jako úspěch
  - restore má terminální stav `current`, ne deployový `ready`
  - odpověď patřící JINÉMU site se uložila
  - promote/rollback braly chybový stav jako ok
  - verify-domain potvrdil libovolnou doménu, když měl site aktivní SSL
  - install přepínače z package.json bez validace

Spuštění: python3 skills/netlify-publisher/tests/test_stavy.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from argparse import Namespace
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import netlify_publish as np  # noqa: E402

V: list[tuple[bool, str]] = []
ok = lambda p, d: V.append((bool(p), d))  # noqa: E731


def chyba(fn, kus: str, popis: str) -> None:
    try:
        fn()
    except np.NetlifyPublishError as e:
        ok(kus.lower() in str(e).lower(), f"{popis} ({e})" if kus.lower() in str(e).lower()
           else f"{popis} — jiná hláška: {e}")
        return
    ok(False, f"{popis} — PROŠLO, i když mělo selhat")


def main() -> int:
    # ── direct deploy: uznává se jen `ready` + exact binding ──────────────
    creds = {"auth_token": "test"}
    ok(np.validate_direct_deploy_result(
        {"state": "ready", "id": "d1", "site_id": "muj-site"}, "muj-site", creds
    ) == "d1",
       "ready + deploy ID projde")
    for stav in ("building", "enqueued", "uploading", "", "processing"):
        if not stav:
            continue  # prázdný stav může projít jen autoritativním follow-upem
        chyba(lambda s=stav: np.validate_direct_deploy_result(
                  {"state": s, "id": "d1", "site_id": "muj-site"}, "muj-site", creds),
              "očekáváno", f"nedokončený direct stav {stav!r} neprojde")
    for stav in ("error", "failed", "rejected"):
        chyba(lambda s=stav: np.validate_direct_deploy_result(
                  {"state": s, "id": "d1", "site_id": "muj-site"}, "muj-site", creds),
              "očekáváno", f"chybový stav {stav!r} neprojde")
    chyba(lambda: np.validate_direct_deploy_result(
              {"state": "ready", "site_id": "muj-site"}, "muj-site", creds),
          "deploy id", "ready bez deploy ID neprojde")
    chyba(lambda: np.validate_direct_deploy_result(
              {"state": "ready", "id": "d1", "site_id": "jiny"}, "muj-site", creds),
          "jinému site", "odpověď cizího site neprojde")

    # ── restore: promote/rollback končí `current`, ne `ready` ─────────────
    ok(np.validate_restore_result(
        {"state": "current", "id": "d1", "site_id": "muj-site"},
        "Promote", "muj-site", "d1", creds,
    ) == "d1", "restore current + exact binding projde")
    chyba(lambda: np.validate_restore_result(
              {"state": "ready", "id": "d1", "site_id": "muj-site"},
              "Rollback", "muj-site", "d1", creds),
          "current", "restore ready se neplete s direct deploy úspěchem")
    chyba(lambda: np.validate_restore_result(
              {"state": "current", "id": "jiny", "site_id": "muj-site"},
              "Rollback", "muj-site", "d1", creds),
          "jiný deploy", "restore jiného deploye neprojde")

    # ── doménový guard vidí i aliasy ──────────────────────────────────────
    ok(np.domeny_site({"custom_domain": "a.cz", "domain_aliases": ["b.cz"]}) == ["a.cz", "b.cz"],
       "domeny_site vrací hlavní i aliasy")
    chyba(lambda: np.strez_produkci({"domain_aliases": ["alias.cz"]}, False, "Promote"),
          "vlastní doménu", "alias bez --force-prod zastaví produkci")
    try:
        np.strez_produkci({"domain_aliases": ["alias.cz"]}, True, "Promote")
        ok(True, "s --force-prod projde")
    except np.NetlifyPublishError as e:
        ok(False, f"s --force-prod měl projít: {e}")
    try:
        np.strez_produkci({}, False, "Promote")
        ok(True, "site bez vlastní domény projde bez --force-prod")
    except np.NetlifyPublishError as e:
        ok(False, f"site bez domény neměl blokovat: {e}")

    # ── verify-domain: SSL na site ≠ tahle doména ─────────────────────────
    site = {"ssl_status": "active", "custom_domain": "moje.cz", "domain_aliases": ["alias.cz"]}
    ok(np._domena_patri_k_site(site, "moje.cz"), "hlavní doména se pozná")
    ok(np._domena_patri_k_site(site, "ALIAS.cz"), "alias se pozná bez ohledu na velikost písmen")
    ok(not np._domena_patri_k_site(site, "cizi.example"), "cizí doména se NEpotvrdí")

    # ── site names: vždy tři validní a unikátní kandidáti ────────────────
    for delka in (1, 2, 3, 53, 60, 61, 62, 63):
        slug = "a" * delka
        kandidati = np.generate_site_name_candidates(slug)
        ok(
            len(kandidati) == 3
            and len(set(kandidati)) == 3
            and all(np.SITE_NAME_RE.fullmatch(k) for k in kandidati),
            f"slug délky {delka} má přesně 3 unikátní validní kandidáty",
        )
        ok(
            kandidati == np.generate_site_name_candidates(slug),
            f"kandidáti délky {delka} jsou determinističtí",
        )
    dlouhy_x = "a" * 62 + "x"
    dlouhy_y = "a" * 62 + "y"
    ok(
        np.generate_site_name_candidates(dlouhy_x)[2]
        != np.generate_site_name_candidates(dlouhy_y)[2],
        "hashovaný fallback dlouhých slugů zachová rozdíl na konci",
    )

    # ── patch-only specs nesmějí překročit deklarovanou minor řadu ───────
    ok(
        np.patch_install_specs({"next": "^15.2.3", "react": "~19.0.1"})
        == ["next@~15.2.3", "react@~19.0.1"],
        "caret i tilde se převedou na explicitní patch řadu",
    )
    chyba(
        lambda: np.patch_install_specs({"next": "latest"}),
        "podporuje jen",
        "tag latest se za patch-only update nevydává",
    )
    chyba(
        lambda: np.patch_install_specs({"next": ">=15"}),
        "podporuje jen",
        "široký semver range se za patch-only update nevydává",
    )

    # ── install přepínače: allowlist ──────────────────────────────────────
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)

        # Malformed package.json musí vždy skončit doménovou chybou bez
        # tracebacku/TypeError, včetně explicitního JSON null.
        for section in ("dependencies", "devDependencies", "scripts"):
            (d / "package.json").write_text(json.dumps({section: None}))
            chyba(
                lambda: np.detect_framework(d),
                f"{section} musí být json objekt",
                f"{section}=null skončí srozumitelnou chybou",
            )
        (d / "package.json").write_text("null")
        chyba(
            lambda: np.detect_framework(d),
            "musí obsahovat json objekt",
            "null kořen package.json skončí srozumitelnou chybou",
        )
        (d / "package.json").write_text(json.dumps({"scripts": {"build": True}}))
        chyba(
            lambda: np.detect_framework(d),
            "scripts.build musí být text",
            "netextový build script skončí srozumitelnou chybou",
        )
        (d / "package.json").write_text(json.dumps({
            "scripts": {"build": "build"}, "publishDir": "/etc",
        }))
        chyba(
            lambda: np.detect_framework(d),
            "musí být relativní",
            "absolutní publishDir selže už při detekci/dry-runu",
        )

        # command_update_deps musí poslat `npm install pkg@~X.Y.Z`, ne
        # původní `npm update`, který u caret rozsahu dovoloval minor bump.
        (d / "package.json").write_text(json.dumps({
            "dependencies": {"vite": "^5.2.1", "unrelated": "^9.0.0"},
            "scripts": {"build": "vite build"},
        }))
        puvodni_resolve = np.resolve_project_dir
        puvodni_npm = np.run_npm_command
        npm_volani: list[list[str]] = []
        try:
            np.resolve_project_dir = lambda _path: d
            dry = np.command_update_deps(Namespace(path=str(d), major=False, dry_run=True))
            ok(
                dry["packageSpecs"] == ["vite@~5.2.1"]
                and dry["packages"] == ["vite"],
                "update-deps dry-run ukáže jen deklarovaný core balík a patch spec",
            )

            def fake_npm(argv, **_kwargs):
                npm_volani.append(list(argv))
                return 0, "", ""

            np.run_npm_command = fake_npm
            np.command_update_deps(Namespace(path=str(d), major=False, dry_run=False))
            ok(
                npm_volani == [["install", "vite@~5.2.1", "--no-audit", "--no-fund"]],
                "ostrý patch update používá omezený npm install místo npm update",
            )

            (d / "package.json").write_text(json.dumps({
                "dependencies": {"vite": "latest"},
                "scripts": {"build": "vite build"},
            }))
            chyba(
                lambda: np.command_update_deps(
                    Namespace(path=str(d), major=False, dry_run=True)
                ),
                "podporuje jen",
                "neomezený range selže už v dry-runu",
            )
        finally:
            np.resolve_project_dir = puvodni_resolve
            np.run_npm_command = puvodni_npm

        (d / "package.json").write_text(json.dumps(
            {"name": "t", "cliqsales": {"installFlags": ["--legacy-peer-deps"]}}))
        ok(np.install_flags_for(d) == ["--legacy-peer-deps"], "povolený přepínač projde")

        (d / "package.json").write_text(json.dumps(
            {"name": "t", "cliqsales": {"installFlags": ["--registry=http://zlo"]}}))
        chyba(lambda: np.install_flags_for(d), "nepovolený", "podstrčený argument neprojde")

        (d / "package.json").write_text(json.dumps(
            {"name": "t", "cliqsales": {"installFlags": ["--force"]}}))
        chyba(lambda: np.install_flags_for(d), "nepovolený", "nedoložený --force neprojde")

        (d / "package.json").write_text(json.dumps(
            {"name": "t", "cliqsales": "rozbite"}))
        chyba(lambda: np.install_flags_for(d), "json objekt", "malformed cliqsales metadata skončí doménovou chybou")

        (d / "package.json").write_text("{not-json")
        chyba(lambda: np.install_flags_for(d), "nelze přečíst", "malformed package JSON není tiše ignorován")

        (d / "package.json").write_text(json.dumps({"name": "t"}))
        ok(np.install_flags_for(d) == [], "projekt bez deklarace nedostane nic navíc")

        # Přenesené Next projekty mohou ztratit executable bit. Helper smí
        # změnit jen přesnou lokální binárku a musí ji skutečně zprovoznit.
        next_bin = d / "node_modules" / "next" / "dist" / "bin" / "next"
        next_bin.parent.mkdir(parents=True)
        next_bin.write_text("#!/usr/bin/env node\n")
        next_bin.chmod(0o644)
        np.ensure_next_binary_executable(d, {"type": "nextjs-static"})
        ok(bool(next_bin.stat().st_mode & 0o111), "Next build binárka dostane executable bit")

        next_bin.unlink()
        outside = d / "outside-next"
        outside.write_text("#!/usr/bin/env node\n")
        next_bin.symlink_to(outside)
        chyba(
            lambda: np.ensure_next_binary_executable(d, {"type": "nextjs-static"}),
            "symlink",
            "symlinkovaná Next build binárka se nikdy nemění",
        )
        ok((outside.stat().st_mode & 0o111) == 0,
           "odmítnutý symlink nezměnil režim cílového souboru")

        legacy = d / "legacy-state"
        legacy.mkdir()
        legacy_state = legacy / ".netlify-state.json"
        legacy_state.write_text(json.dumps({
            "siteId": "site-legacy",
            "prodUrl": "https://live.example",
            "draftUrl": "https://old-draft.example",
        }))
        migrated = np._migrate_project_state(legacy)
        ok(
            migrated.get("siteId") == "site-legacy"
            and migrated.get("prodUrl") == "https://live.example"
            and migrated.get("draftUrl") is None
            and migrated.get("draftDeployId") is None
            and migrated.get("stateVersion") == 2,
            "v1 migrace zachová produkci a zneplatní neověřitelný draft",
        )
        first_bytes = legacy_state.read_bytes()
        np._migrate_project_state(legacy)
        ok(legacy_state.read_bytes() == first_bytes, "v1 migrace je idempotentní")

        future = d / "future-state"
        future.mkdir()
        (future / ".netlify-state.json").write_text(json.dumps({"stateVersion": 99}))
        chyba(
            lambda: np._migrate_project_state(future),
            "nepodporovanou",
            "budoucí state verze se nikdy tiše nedowngradují",
        )

    # ── verify-domain: polluje jen skutečně připojený pending SSL ─────────
    puvodni_creds = np.load_netlify_credentials
    puvodni_cli = np.run_netlify_cli
    puvodni_sleep = np.time.sleep
    args_domain = Namespace(site_id="site-1", domain="example.cz")
    try:
        np.load_netlify_credentials = lambda: {"auth_token": "test", "site_id": ""}

        calls: list[list[str]] = []
        sleeps: list[float] = []

        def missing_domain(argv, _credentials, **_kwargs):
            calls.append(list(argv))
            return {"ssl_status": "active", "custom_domain": "jina.cz"}

        np.run_netlify_cli = missing_domain
        np.time.sleep = lambda seconds: sleeps.append(seconds)
        chyba(
            lambda: np.command_verify_domain(args_domain),
            "není u tohoto site",
            "nepřipojená doména selže okamžitě",
        )
        ok(len(calls) == 1 and not sleeps, "nepřipojená doména se nepolluje")

        calls.clear()

        def auth_error(argv, _credentials, **_kwargs):
            calls.append(list(argv))
            raise np.NetlifyPublishError("auth selhalo")

        np.run_netlify_cli = auth_error
        chyba(
            lambda: np.command_verify_domain(args_domain),
            "auth selhalo",
            "CLI/auth chyba se propíše okamžitě",
        )
        ok(len(calls) == 1 and not sleeps, "CLI/auth chyba se nepolluje")

        odpovedi = [
            {"ssl_status": "provisioning", "custom_domain": "example.cz"},
            {"ssl_status": "active", "domain_aliases": ["EXAMPLE.CZ"]},
        ]
        np.run_netlify_cli = lambda *_args, **_kwargs: odpovedi.pop(0)
        vysledek = np.command_verify_domain(args_domain)
        ok(
            vysledek["ok"] is True and vysledek["sslStatus"] == "active"
            and len(sleeps) == 1,
            "připojená pending doména se polluje do active",
        )

        np.run_netlify_cli = lambda *_args, **_kwargs: []
        chyba(
            lambda: np.command_verify_domain(args_domain),
            "nevrátil json objekt",
            "malformed getSite payload selže doménovou chybou",
        )
    finally:
        np.load_netlify_credentials = puvodni_creds
        np.run_netlify_cli = puvodni_cli
        np.time.sleep = puvodni_sleep

    # ── add-domain a production guard sdílejí per-site publish lock ───────
    puvodni_creds = np.load_netlify_credentials
    puvodni_cli = np.run_netlify_cli
    puvodni_site_lock = np.site_operation_lock
    puvodni_pub_locks = np.publication_operation_locks
    puvodni_resolve = np.resolve_project_dir
    uvnitr_locku = False

    @contextmanager
    def fake_site_lock(_site_id, _operation):
        nonlocal uvnitr_locku
        uvnitr_locku = True
        try:
            yield
        finally:
            uvnitr_locku = False

    try:
        np.load_netlify_credentials = lambda: {"auth_token": "test", "site_id": "site-1"}
        np.site_operation_lock = fake_site_lock

        def domain_update(_argv, _credentials, **_kwargs):
            if not uvnitr_locku:
                raise np.NetlifyPublishError("updateSite proběhl mimo publish lock")
            return {"ssl_status": "provisioning"}

        np.run_netlify_cli = domain_update
        added = np.command_add_domain(args_domain)
        ok(added["ok"] is True, "add-domain mutuje site uvnitř publish locku")

        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / "index.html").write_text("<!doctype html><title>x</title>")
            np.resolve_project_dir = lambda _path: project
            np.publication_operation_locks = fake_site_lock
            calls = []

            def guarded_get_site(argv, _credentials, **_kwargs):
                calls.append(list(argv))
                if not uvnitr_locku:
                    raise np.NetlifyPublishError("getSite proběhl mimo publish lock")
                return {"id": "site-1", "custom_domain": "live.example.cz"}

            np.run_netlify_cli = guarded_get_site
            deploy_args = Namespace(
                path=str(project), ssr=False, dry_run=False, confirm_publish="yes",
                draft=False, force_prod=False, title="", site_id="site-1",
            )
            chyba(
                lambda: np.command_deploy(deploy_args),
                "vlastní doménu",
                "production guard načte doménu pod publish lockem",
            )
            ok(
                len(calls) == 1 and calls[0][1] == "getSite",
                "guard zastaví produkci před deploy mutací",
            )
    finally:
        np.load_netlify_credentials = puvodni_creds
        np.run_netlify_cli = puvodni_cli
        np.site_operation_lock = puvodni_site_lock
        np.publication_operation_locks = puvodni_pub_locks
        np.resolve_project_dir = puvodni_resolve

    for stav, popis in V:
        print(f"{'PASS' if stav else 'FAIL'}  {popis}")
    selhalo = sum(1 for s, _ in V if not s)
    print(f"\n{len(V) - selhalo}/{len(V)} prošlo")
    return 1 if selhalo else 0


if __name__ == "__main__":
    raise SystemExit(main())
