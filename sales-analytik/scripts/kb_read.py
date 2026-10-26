#!/usr/bin/env python3
"""kb_read.py — vytiskne požadované kapitoly sdílené cliqsales-closing-system (Belfort+Hormozi).

Token disciplína: čte se KAPITOLOVĚ, ne celý KB. Nejdřív `INDEX`, pak jen to,
co hovor vyžaduje (viz INDEX → Retrieval pravidla).

Použití:
  python3 kb_read.py INDEX
  python3 kb_read.py SYSTEM_PROMPT SCORING_ENGINE COACHING_ENGINE ethics
  python3 kb_read.py hormozi belfort
  python3 kb_read.py --list

Názvy jsou basename bez .md (case-insensitive). Exit: 0 OK · 2 KB nenalezen · 3 kapitola nenalezena.
"""
from __future__ import annotations

import sys
from pathlib import Path


def find_kb_dir() -> Path | None:
    """Knowledge base leží pod {baseDir}/kb/.

    Audit P1-16: dřív se hledala jako `_lib/cliqsales-closing-system` šplháním
    po nadřazených složkách. `_lib` ale není skill, takže ho ZIP importér
    Control Centra zahazoval a skill po instalaci padal na exit 2. Teď je KB
    součástí skillu a instaluje se s ním.
    """
    kb = Path(__file__).resolve().parent.parent / "kb"
    return kb if (kb / "INDEX.md").exists() else None
def main() -> None:
    args = [a for a in sys.argv[1:]]
    if any(a in ("--help", "-h") for a in args):
        print(__doc__ or "kb_read.py — čtečka knowledge base")
        print("Použití: kb_read.py [--help | --list | --version | <kapitola>]")
        return
    kb = find_kb_dir()
    if not kb:
        print("CHYBA: knowledge base nenalezena. Od auditu 2026-07-28 je součástí skillu ve `{baseDir}/kb/` — pokud chybí, instalace skillu je neúplná. Přeinstalujte skill z celého balíku; nepokračujte bez metodiky.", file=sys.stderr)
        sys.exit(2)

    if "--version" in args:
        vf = kb / "VERSION"
        print(vf.read_text(encoding="utf-8").strip() if vf.exists() else "unknown")
        return

    if not args or "--list" in args:
        names = sorted(p.stem for p in kb.glob("*.md"))
        print("Dostupné kapitoly: " + ", ".join(names))
        print("(+ schemas/scorecard.schema.json · VERSION · CHANGELOG.md)")
        return

    missing = []
    out_parts = []
    for name in args:
        stem = name[:-3] if name.lower().endswith(".md") else name
        # case-insensitive match na basename
        match = next((p for p in kb.glob("*.md") if p.stem.lower() == stem.lower()), None)
        if not match:
            missing.append(name)
            continue
        out_parts.append(f"\n===== {match.stem} =====\n" + match.read_text(encoding="utf-8"))

    if out_parts:
        print("".join(out_parts))
    if missing:
        print(f"CHYBA: kapitola nenalezena: {', '.join(missing)} "
              f"(zkus --list)", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
