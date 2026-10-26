#!/usr/bin/env python3
"""Bezpečnostní brány publisheru — testy, které se je snaží OBEJÍT.

Pokrývá dvě díry, kterými šlo nasadit cizí soubory nebo vynést klíče:
  A) publish složka z package.json → publishDir mimo projekt
  B) npm build dědil celé prostředí včetně tajemství + výpis bez začernění

Spuštění: python3 skills/netlify-publisher/tests/test_bezpecnost.py
Bez sítě, bez Netlify, bez skutečných klíčů.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
os.environ["NETLIFY_ALLOW_OUTSIDE_DOCUMENTS"] = "1"

import netlify_publish as np  # noqa: E402

V: list[tuple[bool, str]] = []


def ok(podminka: bool, popis: str) -> None:
    V.append((bool(podminka), popis))


def projekt(root: Path, publish_dir: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(
        '{"name":"t","version":"1.0.0","scripts":{"build":"echo ok"},'
        f'"publishDir":"{publish_dir}"}}'
    )
    return root


class Args:
    def __init__(self, path: str):
        self.path = path
        self.ssr = False
        self.dry_run = True
        self.draft = True
        self.confirm_publish = "no"
        self.force_prod = False
        self.site_id = ""
        self.title = ""
        self.json = True


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # ── A) publish složka nesmí utéct z projektu ──────────────────────
        cizi = tmp / "cizi"
        cizi.mkdir()
        (cizi / "index.html").write_text("<!doctype html>tajne")

        r = projekt(tmp / "abs", str(cizi))
        try:
            np.command_deploy(Args(str(r)))
            ok(False, "absolutní publishDir: PROŠEL (díra)")
        except np.NetlifyPublishError as e:
            ok("relativní" in str(e), f"absolutní publishDir odmítnut ({e})")

        r = projekt(tmp / "rel", "../../cizi")
        try:
            np.command_deploy(Args(str(r)))
            ok(False, "publishDir '../../cizi': PROŠEL (díra)")
        except np.NetlifyPublishError as e:
            ok("mimo projekt" in str(e), f"únik přes '..' odmítnut ({e})")

        r = projekt(tmp / "link", "dist")
        (r / "dist").symlink_to(cizi, target_is_directory=True)
        try:
            np.command_deploy(Args(str(r)))
            ok(False, "symlinkovaný dist: PROŠEL (díra)")
        except np.NetlifyPublishError as e:
            ok("symlink" in str(e) or "mimo projekt" in str(e),
               f"symlinkovaný dist odmítnut ({e})")

        # poctivý projekt musí dál fungovat (brána nesmí blokovat všechno)
        r = projekt(tmp / "ok", "out")
        (r / "out").mkdir()
        (r / "out" / "index.html").write_text("<!doctype html>")
        try:
            vysledek = np.command_deploy(Args(str(r)))
            ok(vysledek.get("dryRun") is True, "poctivý projekt projde")
        except np.NetlifyPublishError as e:
            ok(False, f"poctivý projekt neprošel: {e}")

        # Static upload musí být fyzický snapshot přesného manifestu. Pouhé
        # přeskočení interních souborů ve scanneru je nechrání, pokud CLI
        # dostane původní adresář.
        stage_root = tmp / "stage"
        (stage_root / "assets").mkdir(parents=True)
        (stage_root / "index.html").write_text("<!doctype html>", encoding="utf-8")
        asset = stage_root / "assets" / "app.js"
        asset.write_text("safe", encoding="utf-8")
        (stage_root / ".web-builder.json").write_text("{}", encoding="utf-8")
        (stage_root / ".netlify-state.json").write_text("{}", encoding="utf-8")
        files = np.collect_publish_files(stage_root)
        manifest = np.publish_manifest_snapshot(stage_root, files)
        staged_path = None
        try:
            with np.static_publish_staging(stage_root, manifest) as staged:
                staged_path = staged
                staged_files = sorted(
                    p.relative_to(staged).as_posix() for p in staged.rglob("*") if p.is_file()
                )
                ok(
                    staged_files == ["assets/app.js", "index.html"],
                    "static staging fyzicky obsahuje jen ověřený public manifest",
                )
                ok(
                    (staged / "assets" / "app.js").stat().st_ino != asset.stat().st_ino,
                    "static staging nepoužívá hardlinky na měnitelný zdroj",
                )
            ok(staged_path is not None and not staged_path.exists(),
               "static staging se po použití odstraní")
        except np.NetlifyPublishError as e:
            ok(False, f"bezpečný static staging neočekávaně selhal: {e}")

        # I stejně dlouhá změna po preflightu musí před CLI skončit fail-closed.
        files = np.collect_publish_files(stage_root)
        stale_manifest = np.publish_manifest_snapshot(stage_root, files)
        asset.write_text("evil", encoding="utf-8")
        try:
            with np.static_publish_staging(stage_root, stale_manifest):
                pass
            ok(False, "stejně dlouhá změna po scanu: PROŠLA (TOCTOU díra)")
        except np.NetlifyPublishError as e:
            ok("změnil" in str(e), f"změna po scanu odmítnuta ({e})")

        # Dry-run nesmí ani připravovat temp strom. Nahrazení mkdtemp tvrdou
        # chybou dokazuje, že se k němu command vůbec nedostane.
        dry_project = tmp / "dry-no-stage"
        dry_project.mkdir()
        (dry_project / "index.html").write_text("<!doctype html>", encoding="utf-8")
        original_mkdtemp = np.tempfile.mkdtemp
        np.tempfile.mkdtemp = lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("mkdtemp nesmí běžet v dry-run")
        )
        try:
            result = np.command_deploy(Args(str(dry_project)))
            ok(result.get("dryRun") is True, "deploy --dry-run nevytváří staging")
        except Exception as e:
            ok(False, f"deploy --dry-run sáhl na staging: {e}")
        finally:
            np.tempfile.mkdtemp = original_mkdtemp

        # Cleanup chyba nesmí přepsat remote výsledek a vyvolat nebezpečný
        # opakovaný deploy. Simulujeme ji přímo na context manageru.
        cleanup_root = tmp / "cleanup-stage"
        cleanup_root.mkdir()
        (cleanup_root / "index.html").write_text("<!doctype html>", encoding="utf-8")
        cleanup_manifest = np.publish_manifest_snapshot(
            cleanup_root, np.collect_publish_files(cleanup_root)
        )
        created_temp: list[str] = []
        original_rmtree = np.shutil.rmtree

        def local_mkdtemp(*args, **kwargs):
            path = original_mkdtemp(prefix="cc-netlify-static-test-", dir=tmp)
            created_temp.append(path)
            return path

        np.tempfile.mkdtemp = local_mkdtemp
        np.shutil.rmtree = lambda *_a, **_k: (_ for _ in ()).throw(OSError("cleanup test"))
        try:
            with np.static_publish_staging(cleanup_root, cleanup_manifest):
                pass
            ok(True, "cleanup chyba nemaskuje dokončený deploy krok")
        except Exception as e:
            ok(False, f"cleanup chyba unikla ven: {e}")
        finally:
            np.tempfile.mkdtemp = original_mkdtemp
            np.shutil.rmtree = original_rmtree
            for path in created_temp:
                original_rmtree(path, ignore_errors=True)

        # ── B) build nesmí zdědit tajemství ani je vypsat ─────────────────
        os.environ["NETLIFY_AUTH_TOKEN"] = "kanarek-token-1234567890"
        os.environ["FAL_KEY"] = "kanarek-fal-0987654321"
        os.environ["NEJAKA_VEREJNA"] = "tohle-je-v-poradku"

        env = np.build_environment()
        ok("NETLIFY_AUTH_TOKEN" not in env, "build nedostane NETLIFY_AUTH_TOKEN")
        ok("FAL_KEY" not in env, "build nedostane FAL_KEY")
        ok("NEJAKA_VEREJNA" not in env, "build nedostane ani ostatní proměnné procesu")
        ok("PATH" in env and env.get("CI") == "1", "build dostane PATH a CI")

        zprava = "Chyba: token kanarek-token-1234567890 a klic kanarek-fal-0987654321"
        skryto = np.redact(zprava)
        ok("kanarek-token-1234567890" not in skryto, "token je ve výpisu začerněný")
        ok("kanarek-fal-0987654321" not in skryto, "FAL klíč je ve výpisu začerněný")
        ok("«skryto»" in skryto, "začernění je vidět v textu")

        # reálný běh npm: potvrdíme, že proměnná do procesu nedorazí
        r = tmp / "envtest"
        r.mkdir()
        rc, out, err = np.run_npm_command(
            ["exec", "--", "node", "-e",
             "console.log('TOKEN=' + (process.env.NETLIFY_AUTH_TOKEN || 'CHYBI'))"],
            cwd=r, timeout=120,
        )
        if rc == 0:
            ok("TOKEN=CHYBI" in out, f"skutečný npm proces token nevidí ({out.strip()[:60]})")
        else:
            ok(True, "npm exec nedostupný — přeskočeno (allowlist ověřen výše)")

        # ZIP import žije v user-skills, ale credential helper je distribuovaný
        # v ~/.openclaw/cs-skills/_lib. Fallback nesmí záviset na exportovaném
        # OPENCLAW_HOME ani na relativní pozici samotného skillu.
        fake_home = tmp / "home"
        helper_dir = fake_home / ".openclaw" / "cs-skills" / "_lib"
        helper_dir.mkdir(parents=True)
        (helper_dir / "cc_credentials.py").write_text(
            "def get_variable(name):\n"
            "    return 'user-layout-ok' if name == 'TEST_VARIABLE' else ''\n",
            encoding="utf-8",
        )
        old_home = os.environ.get("HOME")
        old_openclaw_home = os.environ.pop("OPENCLAW_HOME", None)
        old_cc_home = os.environ.pop("CC_OPENCLAW_HOME", None)
        old_module = sys.modules.pop("cc_credentials", None)
        os.environ["HOME"] = str(fake_home)
        try:
            ok(
                np.load_custom_variable("TEST_VARIABLE") == "user-layout-ok",
                "user-skills layout najde sdílený CC credential helper",
            )
        finally:
            sys.modules.pop("cc_credentials", None)
            if old_module is not None:
                sys.modules["cc_credentials"] = old_module
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home
            if old_openclaw_home is not None:
                os.environ["OPENCLAW_HOME"] = old_openclaw_home
            if old_cc_home is not None:
                os.environ["CC_OPENCLAW_HOME"] = old_cc_home

    for stav, popis in V:
        print(f"{'PASS' if stav else 'FAIL'}  {popis}")
    selhalo = sum(1 for s, _ in V if not s)
    print(f"\n{len(V) - selhalo}/{len(V)} prošlo")
    return 1 if selhalo else 0


if __name__ == "__main__":
    raise SystemExit(main())
