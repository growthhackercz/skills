"""Pomocný skript pro vyhledání firmy v ARES (registr ekonomických subjektů).

Použití:
    python3 ares_lookup.py --ico 12345678
    python3 ares_lookup.py --nazev "Bioptron Medall"
    python3 ares_lookup.py --nazev "Bioptron Medall" --pocet 5

Výstup (JSON na stdout): seznam shod s vyčištěnými poli.

Exit codes:
    0 = úspěch (nalezeno alespoň 1)
    2 = úspěch (vyhledávání proběhlo, ale 0 shod)
    3 = chyba vstupu nebo síťová chyba
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

ARES_BASE = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest"
TIMEOUT = 15


def ares_request(method: str, path: str, body: dict | None = None) -> dict | None:
    url = f"{ARES_BASE}{path}"
    data: bytes | None = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    try:
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            payload = resp.read()
            return json.loads(payload) if payload else None
    except urllib.error.HTTPError as exc:
        print(f"ARES HTTP {exc.code}: {exc.reason}", file=sys.stderr)
        return None
    except urllib.error.URLError as exc:
        print(f"ARES network error: {exc.reason}", file=sys.stderr)
        return None
    except json.JSONDecodeError as exc:
        print(f"ARES parse error: {exc}", file=sys.stderr)
        return None


def lookup_by_ico(ico: str) -> list[dict[str, Any]]:
    """Vyhledání podle 8místného IČO."""
    ico = ico.zfill(8)
    body = ares_request("GET", f"/ekonomicke-subjekty/{ico}")
    if not body:
        return []
    return [clean_record(body)]


def lookup_by_nazev(nazev: str, pocet: int = 10) -> list[dict[str, Any]]:
    """Vyhledání podle názvu (přesné nebo částečné)."""
    body = ares_request(
        "POST",
        "/ekonomicke-subjekty/vyhledat",
        body={"start": 0, "pocet": pocet, "nazev": nazev},
    )
    if not body:
        return []
    rows = body.get("ekonomickeSubjekty") or []
    return [clean_record(r) for r in rows]


def clean_record(raw: dict) -> dict[str, Any]:
    """Vyčistí ARES odpověď do vyhozeného formátu pro Sales Scout."""
    sidlo = raw.get("sidlo") or {}
    statutar = []
    for entry in (raw.get("statutarniOrgan") or []):
        if isinstance(entry, dict):
            for clen in entry.get("clenoveOrganu") or []:
                if isinstance(clen, dict):
                    statutar.append({
                        "jmeno": (clen.get("jmeno") or "").strip(),
                        "prijmeni": (clen.get("prijmeni") or "").strip(),
                        "funkce": (clen.get("funkce") or {}).get("nazev", "").strip() if isinstance(clen.get("funkce"), dict) else "",
                    })

    cinnosti = []
    for c in (raw.get("czNace") or []):
        if isinstance(c, dict):
            cinnosti.append({
                "kod": c.get("kod", ""),
                "nazev": c.get("nazev", "")
            })

    forma = raw.get("pravniForma") or {}
    if isinstance(forma, dict):
        forma_str = forma.get("nazev", "")
    else:
        forma_str = str(forma) if forma else ""

    return {
        "ico": raw.get("ico", ""),
        "nazev": raw.get("obchodniJmeno", ""),
        "dic": raw.get("dic", ""),
        "sidlo": {
            "adresa": sidlo.get("textovaAdresa", ""),
            "obec": sidlo.get("nazevObce", ""),
            "okres": sidlo.get("nazevOkresu", ""),
            "psc": sidlo.get("psc", ""),
        },
        "pravniForma": forma_str,
        "datumVzniku": raw.get("datumVzniku", ""),
        "datumZaniku": raw.get("datumZaniku", ""),
        "status": (
            "v likvidaci" if raw.get("seznamRegistraci", {}).get("stavZdrojeVr") == "LIKVIDACE"
            else "zaniklý" if raw.get("datumZaniku")
            else "aktivní"
        ),
        "statutariOrganove": statutar,
        "predmetCinnosti": [c["nazev"] for c in cinnosti][:5],
        "web": (raw.get("webovaStranka") or "").strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="ARES lookup helper pro Sales Scout")
    parser.add_argument("--ico", type=str, help="8místné IČO")
    parser.add_argument("--nazev", type=str, help="Název firmy (přesný nebo částečný)")
    parser.add_argument("--pocet", type=int, default=10, help="Max počet shod při vyhledání podle názvu (výchozí 10)")
    args = parser.parse_args()

    if not args.ico and not args.nazev:
        print("ERROR: Zadej --ico nebo --nazev.", file=sys.stderr)
        return 3

    if args.ico and args.nazev:
        print("ERROR: Zadej buď --ico, nebo --nazev, ne obojí.", file=sys.stderr)
        return 3

    if args.ico:
        if not args.ico.isdigit():
            print("ERROR: IČO musí být číselné.", file=sys.stderr)
            return 3
        results = lookup_by_ico(args.ico)
    else:
        nazev = args.nazev.strip()
        if len(nazev) < 3:
            print("ERROR: Název firmy musí mít aspoň 3 znaky.", file=sys.stderr)
            return 3
        results = lookup_by_nazev(nazev, pocet=args.pocet)

    output = {
        "count": len(results),
        "results": results,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0 if results else 2


if __name__ == "__main__":
    sys.exit(main())
