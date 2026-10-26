#!/usr/bin/env python3
"""Hranice složky s funkcemi — sedm případů, které dřív prošly tiše.

Spuštění: python3 skills/netlify-publisher/tests/test_functions_dir.py
Bez sítě, bez Netlify, bez klíčů — jen dočasné složky.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import netlify_publish as np  # noqa: E402

VYSLEDKY: list[tuple[bool, str]] = []


def projekt(tmp: Path, toml: str | None, slozky: tuple[str, ...] = ()) -> Path:
    root = tmp / "projekt"
    (root / "out").mkdir(parents=True, exist_ok=True)
    (root / "out" / "index.html").write_text("<!doctype html>")
    for s in slozky:
        (root / s).mkdir(parents=True, exist_ok=True)
        (root / s / "api.mjs").write_text("export default () => {}")
    if toml is not None:
        (root / "netlify.toml").write_text(toml)
    return root


def ceka_chybu(nazev: str, root: Path, kus_hlasky: str) -> None:
    try:
        np.functions_dir_for(root)
    except np.NetlifyPublishError as exc:
        ok = kus_hlasky.lower() in str(exc).lower()
        VYSLEDKY.append((ok, f"{nazev}: {'chyba dle očekávání' if ok else f'jiná hláška: {exc}'}"))
        return
    VYSLEDKY.append((False, f"{nazev}: PROŠLO, i když mělo selhat"))


def ceka_cestu(nazev: str, root: Path, ocekavany_nazev: str | None) -> None:
    try:
        vysledek = np.functions_dir_for(root)
    except np.NetlifyPublishError as exc:
        VYSLEDKY.append((False, f"{nazev}: neočekávaná chyba {exc}"))
        return
    skutecny = vysledek.name if vysledek else None
    ok = skutecny == ocekavany_nazev
    VYSLEDKY.append((ok, f"{nazev}: {skutecny!r} (čekáno {ocekavany_nazev!r})"))


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # 1) dvojité uvozovky — základní případ
        r = projekt(tmp / "a", '[functions]\ndirectory = "server-functions"\n', ("server-functions",))
        ceka_cestu("dvojité uvozovky", r, "server-functions")

        # 2) jednoduché uvozovky — platný TOML, dřív se funkce tiše zahodily
        r = projekt(tmp / "b", "[functions]\ndirectory = 'server-functions'\n", ("server-functions",))
        ceka_cestu("jednoduché uvozovky", r, "server-functions")

        # 3) nastavená, ale chybějící složka — dřív None = mrtvý frontend
        r = projekt(tmp / "c", '[functions]\ndirectory = "chybi"\n')
        ceka_chybu("chybějící složka", r, "neexistuje")

        # 4) únik z projektu
        r = projekt(tmp / "d", '[functions]\ndirectory = "../../ven"\n')
        (tmp / "d" / "ven").mkdir(parents=True, exist_ok=True)
        ceka_chybu("cesta ven z projektu", r, "mimo projekt")

        # 5) absolutní cesta
        r = projekt(tmp / "e", '[functions]\ndirectory = "/etc"\n')
        ceka_chybu("absolutní cesta", r, "relativní")

        # 6a) symlink ven z projektu — chytí ho hranice projektu
        r = projekt(tmp / "f", '[functions]\ndirectory = "fn"\n')
        cil = tmp / "f" / "cizi"
        cil.mkdir(parents=True, exist_ok=True)
        (r / "fn").symlink_to(cil, target_is_directory=True)
        ceka_chybu("symlink ven", r, "mimo projekt")

        # 6b) symlink dovnitř projektu — musí ho zastavit pravidlo o symlinku
        r = projekt(tmp / "i", '[functions]\ndirectory = "fn"\n', ("skutecne-fn",))
        (r / "fn").symlink_to(r / "skutecne-fn", target_is_directory=True)
        ceka_chybu("symlink dovnitř", r, "symlink")

        # 7) přetečení do jiné sekce — [functions] bez directory + [dev] s ním
        r = projekt(tmp / "g", '[functions]\n\n[dev]\ndirectory = "public"\n', ("public",))
        ceka_cestu("přetečení do [dev]", r, None)

        # 8) výchozí netlify/functions bez tomlu
        r = projekt(tmp / "h", None, ("netlify/functions",))
        ceka_cestu("výchozí netlify/functions", r, "functions")

        # 9) deklarované directory jiného typu není totéž jako "nenastavené".
        # Tiché None by nasadilo frontend bez funkcí.
        r = projekt(tmp / "j", "[functions]\ndirectory = false\n")
        ceka_chybu("directory jako boolean", r, "řetězec")

        r = projekt(tmp / "k", "[functions]\ndirectory = [\"fn\"]\n")
        ceka_chybu("directory jako pole", r, "řetězec")

        # 10) included_files umí přibalit libovolný root soubor mimo scan
        # functions tree. Dokud publisher nevaliduje celý dependency graph,
        # musí tato Netlify zkratka skončit fail-closed.
        r = projekt(
            tmp / "l",
            '[functions]\ndirectory = "fn"\nincluded_files = ["../../secret.json"]\n',
            ("fn",),
        )
        ceka_chybu("globální included_files", r, "included_files")

        r = projekt(
            tmp / "m",
            '[functions]\ndirectory = "fn"\n\n'
            '[functions."api"]\nincluded_files = ["../../secret.json"]\n',
            ("fn",),
        )
        ceka_chybu("per-function included_files", r, "included_files")

    for ok, popis in VYSLEDKY:
        print(f"{'PASS' if ok else 'FAIL'}  {popis}")
    selhalo = sum(1 for ok, _ in VYSLEDKY if not ok)
    print(f"\n{len(VYSLEDKY) - selhalo}/{len(VYSLEDKY)} prošlo")
    return 1 if selhalo else 0


if __name__ == "__main__":
    raise SystemExit(main())
