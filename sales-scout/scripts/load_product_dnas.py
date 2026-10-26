"""Pomocný skript pro načtení všech Product DNA z /documents/brand/products/.

Použití:
    python3 load_product_dnas.py
    python3 load_product_dnas.py --products-dir /documents/brand/products
    python3 load_product_dnas.py --slug produkt-a   # jen jeden produkt

Výstup (JSON na stdout):

Pro celý seznam:
{
  "count": 3,
  "products": [
    {
      "slug": "produkt-a",
      "name": "Produkt A",
      "path": "/documents/brand/products/produkt-a/productDNA.md",
      "ideal_customer": "estetické kliniky, wellness centra, fyzioterapie...",
      "value_proposition": "doplňková regenerační procedura...",
      "raw_md_chars": 12450
    },
    ...
  ]
}

Pro --slug:
{
  "found": true,
  "product": { ... }
}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_LIB_DIR = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))
import product_dna as _pdna  # noqa: E402


def read_productdna(path: Path) -> dict[str, Any] | None:
    """Načte productDNA.md soubor a vytáhne klíčové sekce."""
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"WARN: nelze přečíst {path}: {exc}", file=sys.stderr)
        return None

    slug = path.parent.name
    # Audit P1-11: dřív se hledaly tři přesné nadpisy a když nesedly, vrátila
    # se prázdná pole a Scout skóroval fit naslepo. Dual-reader zná synonyma,
    # ignoruje úroveň i číslování nadpisu a chybějící sekce NAHLÁSÍ.
    parsed = _pdna.parse(content, slug=slug, path=str(path))
    for line in _pdna.warn_lines(parsed):
        print(line, file=sys.stderr)
    return {
        "slug": slug,
        "name": parsed["name"],
        "path": str(path),
        "ideal_customer": parsed["ideal_customer"],
        "value_proposition": parsed["value_proposition"],
        "positioning": parsed["positioning"],
        "objections": parsed["objections"],
        "pricing": parsed.get("pricing", ""),
        "proof": parsed.get("proof", ""),
        "missing_sections": parsed["missing"],
        "usable_for_scoring": parsed["usable_for_scoring"],
        "raw_md_chars": len(content),
    }


def extract_name(content: str) -> str | None:
    """Extrahuje název produktu z prvního H1 nadpisu."""
    match = re.search(r"^#\s+(.+?)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def extract_section(content: str, header_keywords: list[str]) -> str | None:
    """Najde H2 / H3 sekci s nadpisem obsahujícím jeden z keywords a vrátí její obsah až do dalšího nadpisu."""
    pattern = re.compile(
        r"^#{2,3}\s+.*?(" + "|".join(re.escape(k) for k in header_keywords) + r").*?$",
        re.MULTILINE | re.IGNORECASE,
    )
    match = pattern.search(content)
    if not match:
        return None
    start = match.end()
    # najdi další nadpis stejné nebo vyšší úrovně
    next_match = re.search(r"^#{1,3}\s+", content[start:], re.MULTILINE)
    end = start + next_match.start() if next_match else len(content)
    return content[start:end].strip()


def list_all_products(products_dir: Path) -> list[dict[str, Any]]:
    """Najde všechny productDNA.md v podsložkách."""
    if not products_dir.exists():
        return []
    products = []
    for sub in sorted(products_dir.iterdir()):
        if not sub.is_dir():
            continue
        dna_path = sub / "productDNA.md"
        if dna_path.exists():
            product = read_productdna(dna_path)
            if product:
                products.append(product)
    return products


def main() -> int:
    parser = argparse.ArgumentParser(description="Načte Product DNA pro Sales Scout")
    parser.add_argument(
        "--products-dir",
        type=Path,
        default=Path("/documents/brand/products"),
        help="Adresář s produktovými podsložkami (default /documents/brand/products)",
    )
    parser.add_argument(
        "--slug",
        type=str,
        help="Načti jen jeden produkt podle slugu (název podsložky)",
    )
    args = parser.parse_args()

    if args.slug:
        dna_path = args.products_dir / args.slug / "productDNA.md"
        product = read_productdna(dna_path)
        result = {"found": product is not None, "product": product}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if product else 2

    products = list_all_products(args.products_dir)
    result = {
        "count": len(products),
        "products_dir": str(args.products_dir),
        "products": products,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
