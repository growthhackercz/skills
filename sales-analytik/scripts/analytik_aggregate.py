#!/usr/bin/env python3
"""analytik_aggregate.py — agregát scorecardů pro učení firmy (NE hodnocení jednotlivce).

Čte JEN scorecardy z /documents/sales/scorecards/ (data od mentora). Hledá vzorce
napříč týmem: opakující se námitky, nejslabší fáze funnelu, korelace skóre×výsledek,
čím se liší nejlepší hovory. Výstup = podklad pro NÁVRHY do playbooku (§5/§10) —
skript nic nezapisuje do salesDNA (schvaluje majitel).

Použití:
  python3 analytik_aggregate.py --period week
  python3 analytik_aggregate.py --all
  python3 analytik_aggregate.py --all --today 2026-07-26 --json

Exit: 0 OK (i prázdno) · 3 chyba vstupu.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

# --- Sdílené moduly skillu (audit P2-03) ---------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import taxonomy as _tax  # noqa: E402

DOCS_ROOT = Path("/documents/sales/scorecards")
SKILL_VERSION = "1.0"
# Technický klíč → český název. Do výstupů VŽDY česky (klíč je jen pro data).
# Audit P2-03: labely z jediného zdroje kb/taxonomy.json.
OBJ_LABEL = _tax.obj_labels()
CAT_LABEL = _tax.cat_labels()


def valid_card_path(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return False
    if any(part.startswith(".") for part in parts):
        return False
    if len(parts) == 2:
        return True  # legacy single-file scorecard directly under seller
    if len(parts) != 3:
        return False
    manifest_path = path.parent / "_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if (
        not isinstance(manifest, dict)
        or manifest.get("schemaVersion") != "1.0"
        or manifest.get("skillVersion") != SKILL_VERSION
        or not isinstance(files, list)
        or any(not isinstance(item, str) or Path(item).name != item for item in files)
        or path.name not in files
    ):
        return False
    actual = sorted(item.name for item in path.parent.iterdir() if item.is_file())
    return actual == sorted([*files, "_manifest.json"])


def parse_date(s: str):
    try:
        y, m, d = (int(x) for x in str(s).split("-"))
        return date(y, m, d)
    except Exception:
        return None


def load_cards(root: Path) -> list[dict]:
    """Načte scorecardy. Do složky patří i soubory, které scorecard NEJSOU.

    Od auditu P1-13 zapisuje Mentor per-hovor bundle, jehož součástí je
    `_manifest.json`; verzování stavu (P1-12) přidává `.state-version.json`.
    `pathlib.glob` na rozdíl od shellu skryté soubory vidí, takže bez filtru
    by se oba počítaly jako hovor a `pocet_hovoru` by lhal.
    """
    out = []
    if not root.exists():
        return out
    for p in root.glob("**/*.json"):
        if p.name.startswith(".") or p.name.startswith("_"):
            continue
        if not valid_card_path(p, root):
            continue
        try:
            card = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        # Scorecard poznáme podle povinné kostry; cokoli jiného není hovor.
        if isinstance(card, dict) and isinstance(card.get("meta"), dict) \
                and isinstance(card.get("scores"), dict) \
                and card.get("skillVersion") == SKILL_VERSION:
            out.append(card)
    return out


def obj_type(o: dict) -> str | None:
    for k in ("typ", "type", "key", "kategorie"):
        if o.get(k):
            return str(o[k])
    return None


def cat_means(cards: list[dict]) -> dict:
    acc = defaultdict(list)
    for sc in cards:
        for c in (sc.get("scores") or {}).get("categories") or []:
            if c.get("key") and isinstance(c.get("skore"), (int, float)):
                acc[c["key"]].append(c["skore"])
    return {k: round(statistics.mean(v), 1) for k, v in acc.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", choices=["week", "month"], default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--today", default=None)
    ap.add_argument("--root", default=str(DOCS_ROOT))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cards = load_cards(Path(args.root))
    if not args.all:
        today = parse_date(args.today) if args.today else date.today()
        if not today:
            print("CHYBA: --today musí být YYYY-MM-DD", file=sys.stderr)
            sys.exit(3)
        span = 7 if (args.period or "week") == "week" else 30
        # uzavřené předchozí období (běh po skončení období, konec = včera)
        end = today - timedelta(days=1)
        start = end - timedelta(days=span - 1)
        cards = [sc for sc in cards if (d := parse_date((sc.get("meta") or {}).get("datum"))) and start <= d <= end]

    n = len(cards)
    totals = [(sc.get("scores") or {}).get("total") for sc in cards
              if isinstance((sc.get("scores") or {}).get("total"), (int, float))]

    # opakující se námitky
    objections = Counter()
    for sc in cards:
        for o in sc.get("objections") or []:
            t = obj_type(o)
            if t:
                objections[t] += 1

    # opakující se příčiny (coaching)
    issues = Counter((sc.get("coaching") or {}).get("primary_issue", "").strip()
                     for sc in cards if (sc.get("coaching") or {}).get("primary_issue"))

    # funnel: nejslabší kategorie napříč týmem
    means = cat_means(cards)
    weakest = sorted(means.items(), key=lambda kv: kv[1])[:3]

    # korelace skóre × výsledek
    by_outcome = defaultdict(list)
    for sc in cards:
        out = (sc.get("meta") or {}).get("vysledek") or "neznamy"
        t = (sc.get("scores") or {}).get("total")
        if isinstance(t, (int, float)):
            by_outcome[out].append(t)
    outcome_avg = {k: round(statistics.mean(v), 1) for k, v in by_outcome.items() if v}
    won = len(by_outcome.get("won", []))
    lost = len(by_outcome.get("lost", []))
    win_rate = round(100 * won / (won + lost)) if (won + lost) else None

    # čím se liší nejlepší hovory (horní vs dolní polovina dle total)
    diff = {}
    if len(totals) >= 4:
        med = statistics.median(totals)
        top = [sc for sc in cards if ((sc.get("scores") or {}).get("total") or 0) >= med]
        bot = [sc for sc in cards if ((sc.get("scores") or {}).get("total") or 0) < med]
        tm, bm = cat_means(top), cat_means(bot)
        for k in tm:
            if k in bm:
                diff[k] = round(tm[k] - bm[k], 1)
        diff = dict(sorted(diff.items(), key=lambda kv: -kv[1])[:3])

    result = {
        "skillVersion": SKILL_VERSION,
        "pocet_hovoru": n,
        "prumer_skore": round(statistics.mean(totals), 1) if totals else None,
        "caste_namitky": objections.most_common(5),
        "caste_priciny": issues.most_common(5),
        "nejslabsi_faze_funnelu": [(CAT_LABEL.get(k, k), v) for k, v in weakest],
        "skore_dle_vysledku": outcome_avg,
        "win_rate_pct": win_rate,
        "co_odlisuje_nejlepsi": {CAT_LABEL.get(k, k): v for k, v in diff.items()},
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    L = [f"# Podklad analytika — {'celá historie' if args.all else 'období'} · {n} hovorů", ""]
    if n == 0:
        L.append("Žádné scorecardy k analýze.")
        print("\n".join(L)); return
    L += [f"**Průměrné skóre:** {result['prumer_skore']} %"]
    if win_rate is not None:
        L.append(f"**Win-rate:** {win_rate} % · skóre dle výsledku: " +
                 ", ".join(f"{k} {v}" for k, v in outcome_avg.items()))
    L += ["", "## Opakující se námitky (→ návrh do §5)"]
    L += [f"- **{OBJ_LABEL.get(t, t)}** — {c}×" for t, c in result["caste_namitky"]] \
        or ["- (žádné klasifikované námitky ve scorecardech)"]
    L += ["", "## Nejslabší fáze funnelu (napříč týmem)"]
    L += [f"- {k} — prům. {v}%" for k, v in result["nejslabsi_faze_funnelu"]]
    L += ["", "## Opakující se příčiny ztrát (→ návrh do §10)"]
    L += [f"- {p} ({c}×)" for p, c in result["caste_priciny"]] or ["- —"]
    if diff:
        L += ["", "## Čím se liší nejlepší hovory"]
        L += [f"- {k}: +{v} bodů oproti slabším" for k, v in result["co_odlisuje_nejlepsi"].items()]
    L += ["", "_Z toho sestav konkrétní NÁVRHY do Sales DNA §5/§10 (playbook-navrh-sablona.md). "
          "Nezapisuj do salesDNA — předlož majiteli ke schválení. Malý vzorek = opatrná interpretace._"]
    print("\n".join(L))


if __name__ == "__main__":
    main()
