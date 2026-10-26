#!/usr/bin/env python3
"""mentor_report.py — agreguje scorecardy do reportu (batch/cron).

Čte JEN scorecardy z /documents/sales/scorecards/ (nikdy surové přepisy).
Sestaví agregát za období a vytiskne podklad reportu (model z něj složí
finální zprávu manažerovi / obchodníkovi).

Použití:
  python3 mentor_report.py --period day                 # denní team digest → manažer
  python3 mentor_report.py --period week                # týdenní trend → manažer + obchodníci
  python3 mentor_report.py --period week --today 2026-07-26   # deterministicky pro test
  python3 mentor_report.py --period week --json         # strojový výstup

Exit: 0 OK (i když prázdno) · 3 chyba vstupu.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

DOCS_ROOT = Path("/documents/sales/scorecards")
SKILL_VERSION = "1.0"
CAT_LABEL = {
    "vedeni_struktura": "Vedení a struktura", "discovery": "Discovery a diagnostika",
    "kvalifikace": "Kvalifikace", "hodnota_jistota": "Hodnota a jistota",
    "prezentace": "Prezentace řešení", "namitky": "Práce s námitkami",
    "closing": "Closing a další krok", "etika": "Etika prodeje",
}


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
        y, m, d = (int(x) for x in s.split("-"))
        return date(y, m, d)
    except Exception:
        return None


def load_cards(root: Path) -> list[dict]:
    """Load only exact-version scorecard data, never bundle metadata JSON."""
    out = []
    if not root.exists():
        return out
    for p in root.glob("**/*.json"):
        if p.name.startswith(".") or p.name.startswith("_"):
            continue
        if not valid_card_path(p, root):
            continue
        try:
            sc = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(sc, dict) or not isinstance(sc.get("meta"), dict) \
                or not isinstance(sc.get("scores"), dict):
            continue
        if sc.get("skillVersion") != SKILL_VERSION:
            continue
        sc["_obchodnik_dir"] = p.parent.parent.name if (p.parent / "_manifest.json").is_file() else p.parent.name
        sc["_detail_path"] = str(p.with_name(p.stem + "-detail.md"))
        out.append(sc)
    return out


def in_window(sc: dict, start: date, end: date) -> bool:
    d = parse_date(str((sc.get("meta") or {}).get("datum", "")))
    return bool(d and start <= d <= end)


def weakest_category(cards: list[dict]) -> str | None:
    acc = defaultdict(list)
    for sc in cards:
        for c in (sc.get("scores") or {}).get("categories") or []:
            if c.get("key") and isinstance(c.get("skore"), (int, float)):
                acc[c["key"]].append(c["skore"])
    if not acc:
        return None
    key = min(acc, key=lambda k: statistics.mean(acc[k]))
    return f"{CAT_LABEL.get(key, key)} (prům. {round(statistics.mean(acc[key]))}%)"


def agg(cards: list[dict]) -> dict:
    totals = [(sc.get("scores") or {}).get("total") for sc in cards
              if isinstance((sc.get("scores") or {}).get("total"), (int, float))]
    issues = Counter((sc.get("coaching") or {}).get("primary_issue", "").strip()
                     for sc in cards if (sc.get("coaching") or {}).get("primary_issue"))
    manip = sum(1 for sc in cards if (sc.get("ethics") or {}).get("manipulace_detekovana"))
    return {
        "pocet": len(cards),
        "prumer": round(statistics.mean(totals), 1) if totals else None,
        "nejslabsi_kategorie": weakest_category(cards),
        "caste_priciny": issues.most_common(3),
        "manipulace_pripadu": manip,
    }


def per_obchodnik(cards: list[dict]) -> dict:
    by = defaultdict(list)
    for sc in cards:
        name = (sc.get("meta") or {}).get("obchodnik") or sc.get("_obchodnik_dir") or "neznámý"
        by[name].append(sc)
    return {name: agg(cs) for name, cs in by.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", choices=["day", "week"], required=True)
    ap.add_argument("--today", default=None, help="YYYY-MM-DD (default systémové datum)")
    ap.add_argument("--root", default=str(DOCS_ROOT))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    today = parse_date(args.today) if args.today else date.today()
    if not today:
        print("CHYBA: --today musí být YYYY-MM-DD", file=sys.stderr)
        sys.exit(3)
    # day = dnešek (běh v 18:00, hovory už proběhly); week = UZAVŘENÝ předchozí týden
    # (běh po ráno, dnešní scorecardy ještě nejsou a minulopondělní by jinak vypadly).
    if args.period == "day":
        start, end = today, today
    else:
        end = today - timedelta(days=1)
        start = today - timedelta(days=7)
    win = end - start
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - win

    all_cards = load_cards(Path(args.root))
    cur = [sc for sc in all_cards if in_window(sc, start, end)]
    prev = [sc for sc in all_cards if in_window(sc, prev_start, prev_end)]

    team = agg(cur)
    team_prev = agg(prev)
    trend = None
    if team["prumer"] is not None and team_prev["prumer"] is not None:
        trend = round(team["prumer"] - team_prev["prumer"], 1)

    obchodnici = per_obchodnik(cur)
    obchodnici_prev = per_obchodnik(prev)

    result = {
        "skillVersion": SKILL_VERSION,
        "obdobi": args.period, "od": str(start), "do": str(end),
        "team": team, "team_trend_vs_minule": trend,
        "obchodnici": obchodnici,
        "obchodnici_prev_prumer": {n: a["prumer"] for n, a in obchodnici_prev.items()},
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # human-readable podklad
    L = [f"# Podklad reportu — {'denní' if args.period == 'day' else 'týdenní'} ({start}–{end})", ""]
    if team["pocet"] == 0:
        L.append("Za období nebyl ohodnocen žádný hovor.")
        print("\n".join(L))
        return
    L += [f"**Tým:** {team['pocet']} hovorů · průměr {team['prumer']} %"
          + (f" · trend {trend:+} vs. minulé období" if trend is not None else ""),
          f"**Nejslabší kategorie týmu:** {team['nejslabsi_kategorie'] or '—'}",
          f"**Manipulace:** {team['manipulace_pripadu']} případ(ů)" if team["manipulace_pripadu"] else None,
          "", "## Časté příčiny (tým)"]
    L += [f"- {p} ({n}×)" for p, n in team["caste_priciny"]] or ["- —"]
    L += ["", "## Obchodníci"]
    for name, a in sorted(obchodnici.items(), key=lambda kv: (kv[1]["prumer"] is None, kv[1]["prumer"] or 0)):
        pv = obchodnici_prev.get(name, {}).get("prumer")
        t = f" (trend {round(a['prumer']-pv,1):+})" if (a["prumer"] is not None and pv is not None) else ""
        L.append(f"- **{name}** — {a['pocet']} hovorů · průměr {a['prumer']} %{t}"
                 f" · nejslabší: {a['nejslabsi_kategorie'] or '—'}")
    # drill-down: odkazy na detailní rozbor každého hovoru (manažer si otevře v Data Center)
    L += ["", "## Detaily hovorů (drill-down v Data Center)"]
    for sc in sorted(cur, key=lambda s: str((s.get("meta") or {}).get("datum") or ""), reverse=True):
        m = sc.get("meta") or {}
        tot = (sc.get("scores") or {}).get("total")
        skore = f"{round(tot)} %" if isinstance(tot, (int, float)) else "?"
        L.append(f"- {m.get('datum', '?')} · {m.get('obchodnik', '?')} · {m.get('firma', '?')} · "
                 f"{skore} → `{sc.get('_detail_path', '')}`")
    L += ["", "_Pozn.: kdo potřebuje pozornost = nejnižší průměr nebo největší propad. "
          "Do finálního reportu vlož konkrétní dovednost k procvičení pro každého obchodníka._"]
    print("\n".join([x for x in L if x is not None]))


if __name__ == "__main__":
    main()
