#!/usr/bin/env python3
"""upsell_recommend.py — kandidáti na upsell/cross-sell (v0.1).

Tři vrstvy doporučení (v tomto pořadí přednosti):
  1. Kurátorská pravidla — poslední sekce salesDNA „Upsell, cross-sell a katalog"
     (§11): přibité páry → bundly → upgrade cesty; flagship jako doplněk.
     Podsekce „Nikdy nenabízet" filtruje VŠE.
  2. Evidence — co-purchase mining nad nákupní historií (purchases.json):
     které skupiny se kupují spolu / týmž zákazníkem do N dní. Žádné ML.
  3. Bez kandidátů → agent sáhne po productDNA (fallback), nefabuluje.

Režimy:
  --contact <id>   kandidáti pro konkrétní kontakt (po nákupu)
  --mine           globální přehled top párů (dry-run / bootstrap pravidel §11)

Použití:
  python3 upsell_recommend.py --state-dir /documents/sales/.upsell-state \
      --catalog /documents/sales/.upsell-state/catalog.json \
      [--rules /documents/sales/salesDNA.md] \
      (--contact <id> | --mine) [--days 60] [--top 5] [--min-support 3]

Bez externích závislostí (stdlib only). Read-only (nic nezapisuje do CRM).
"""
import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import atomic_state as _as  # noqa: E402

PAID_STATES = {"paid", "succeeded", "success", "completed", "complete",
               "captured", "settled", "active", "fulfilled"}
REFUNDED_STATES = {"refunded", "partially_refunded", "chargeback", "reversed",
                   "storno", "vraceno", "vráceno"}


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def parse_ts(iso):
    try:
        return time.mktime(time.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S"))
    except (ValueError, TypeError):
        return None


def transaction_state(purchase):
    """Read canonical and legacy rows; unknown/failed is never paid."""
    state = str((purchase or {}).get("state") or "").strip().lower()
    if state in {"paid", "refunded", "unpaid", "unknown"}:
        return state
    if (purchase or {}).get("refunded") is True:
        return "refunded"
    if (purchase or {}).get("paid") is True:
        return "paid"
    status = str((purchase or {}).get("status") or "").strip().lower()
    if status in REFUNDED_STATES:
        return "refunded"
    if (purchase or {}).get("paid") is False:
        return "unpaid"
    if status in PAID_STATES:
        return "paid"
    return "unpaid"


def purchase_groups(purchase):
    groups = {
        str(item.get("group"))
        for item in (purchase or {}).get("items", [])
        if isinstance(item, dict) and item.get("is_product") and item.get("group")
    }
    main_group = str((purchase or {}).get("main_group") or "").strip()
    if main_group:
        groups.add(main_group)
    return groups


def eligible_paid_entries(rows):
    """Paid rows with later-refunded groups removed from ownership/evidence."""
    refunded = set()
    for purchase in rows or []:
        if isinstance(purchase, dict) and transaction_state(purchase) == "refunded":
            refunded.update(purchase_groups(purchase))
    eligible = []
    for purchase in rows or []:
        if not isinstance(purchase, dict) or transaction_state(purchase) != "paid":
            continue
        row = dict(purchase)
        items = [
            item for item in purchase.get("items", [])
            if isinstance(item, dict)
            and item.get("is_product")
            and item.get("group") not in refunded
        ]
        row["items"] = items
        if row.get("main_group") in refunded:
            row["main_group"] = max(
                items,
                key=lambda item: item.get("price") or 0,
                default={},
            ).get("group", "")
        if items or row.get("main_group"):
            eligible.append(row)
    return eligible, refunded


def contact_groups(purchases, cid):
    """→ (owned bez vratek, vratky) — skupiny produktů kontaktu."""
    paid_rows, refunded = eligible_paid_entries(purchases.get(cid, []))
    owned = set()
    for purchase in paid_rows:
        owned.update(purchase_groups(purchase))
    return owned, refunded


def build_events(purchases):
    """→ per kontakt: [(group, ts, purchase_key)] jen produktové, bez vratek."""
    ev = {}
    for cid, plist in purchases.items():
        rows = []
        paid_rows, _refunded = eligible_paid_entries(plist)
        for p in paid_rows:
            ts = parse_ts(p.get("at", ""))
            for i in p.get("items", []):
                if i.get("is_product") and i.get("group"):
                    rows.append((i["group"], ts, p.get("key")))
        if rows:
            ev[cid] = rows
    return ev


def pair_stats(events, days):
    """→ {A: {B: {both, same_order, within, gaps[]}}}, {group: customers}."""
    window = days * 86400
    stats = defaultdict(lambda: defaultdict(lambda: {"both": 0, "same_order": 0, "within": 0, "gaps": []}))
    customers = defaultdict(int)
    for _cid, rows in events.items():
        groups = {}
        for g, ts, key in rows:
            if g not in groups or (ts and (groups[g][0] is None or ts < groups[g][0])):
                groups[g] = (ts, key)
        for g in groups:
            customers[g] += 1
        glist = list(groups.items())
        for a, (ts_a, key_a) in glist:
            for b, (ts_b, key_b) in glist:
                if a == b:
                    continue
                s = stats[a][b]
                s["both"] += 1
                if key_a and key_a == key_b:
                    s["same_order"] += 1
                elif ts_a and ts_b and 0 < ts_b - ts_a <= window:
                    s["within"] += 1
                    s["gaps"].append(int((ts_b - ts_a) / 86400))
    return stats, customers


def enrich(group, catalog):
    """Reprezentativní produkt skupiny z katalogu (nejlevnější skladem)."""
    best = None
    for pid, it in (catalog or {}).get("items", {}).items():
        if it.get("group") != group:
            continue
        # skladem má vždy přednost před vyprodaným; v rámci stejné dostupnosti nejnižší cena
        rank = (not it.get("availability", "").startswith(("in", "preorder")),
                it.get("price") or 1e12)
        if best is None or rank < best[0]:
            best = (rank, it)
    if not best:
        return {"title": group, "availability": "unknown", "price": None,
                "currency": "", "link": "", "in_catalog": False}
    it = best[1]
    return {"title": it.get("title", group), "availability": it.get("availability", ""),
            "price": it.get("price"), "currency": it.get("currency", ""),
            "link": it.get("link", ""), "category": it.get("category", ""),
            "in_catalog": True}


def in_stock(info):
    return not info["in_catalog"] or info["availability"].startswith(("in", "preorder"))


def median(vals):
    if not vals:
        return None
    v = sorted(vals)
    return v[len(v) // 2]


# -------------------------------- kurátorská pravidla = salesDNA §11 (vrstva 1)
RULE_SUBSECTIONS = (("flagship", "flagship"), ("bundly", "bundles"),
                    ("přibité páry", "pairs"), ("upgrade", "upgrades"),
                    ("nikdy", "never"))


def parse_rules(path):
    """Parsuje poslední sekci salesDNA „Upsell … a katalog" (## 11.): podsekce
    ### Flagship/Bundly/Přibité páry/Upgrade cesty/Nikdy nenabízet s tabulkami.
    → dict sekcí se seznamy řádků (sloupce a/b/c) nebo None (sekce chybí)."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    rules = {name: [] for _, name in RULE_SUBSECTIONS}
    in_section, current, section_seen = False, None, False
    for line in text.splitlines():
        m = re.match(r"^##\s*\d+\.\s*(.+)$", line)
        if m:
            in_section = "upsell" in m.group(1).lower()
            section_seen = section_seen or in_section
            current = None
            continue
        if not in_section:
            continue
        m = re.match(r"^###\s*(.+)$", line)
        if m:
            head = m.group(1).lower()
            current = next((name for kw, name in RULE_SUBSECTIONS if head.startswith(kw)), None)
            continue
        if current and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 2 or set(cells[0]) <= {"-", ":", " "}:
                continue
            low = cells[0].lower()
            if low in ("skupina", "bundle", "koupil", "ze skupiny", "ke skupině"):
                continue  # hlavička tabulky
            if cells[0].startswith("<"):
                continue  # nevyplněný vzorový řádek šablony
            rules[current].append({"a": cells[0], "b": cells[1],
                                   "c": cells[2] if len(cells) > 2 else ""})
    return rules if section_seen else None


def rules_warnings(rules, catalog):
    """Kódy skupin v pravidlech, které nejsou v katalogu (překlepy)."""
    if not rules or not catalog:
        return []
    known = {it.get("group") for it in catalog.get("items", {}).values()}
    unknown = set()
    for sec, rows in rules.items():
        for r in rows:
            if sec == "flagship":
                codes = [r["a"]]  # sloupec b je název produktu, ne kód
            elif sec == "bundles":
                codes = [g.strip() for g in r["b"].split(",")]
            else:
                codes = [r["a"], r["b"]]
            for code in codes:
                code = code.strip()
                if code and code != "*" and code not in known:
                    unknown.add(code)
    return sorted(unknown)


def rule_candidates(rules, src_group, owned, refunded, banned, catalog):
    """→ (primární: pár → bundle → upgrade, flagship zvlášť — řadí se až ZA evidenci)."""
    out, flags = [], []

    def add(target, group, source, note):
        group = group.strip()
        seen = {c["group"] for c in out} | {c["group"] for c in flags}
        if (not group or group in owned or group in refunded or group in banned
                or group in seen):
            return
        info = enrich(group, catalog)
        if not in_stock(info):
            return
        target.append({"group": group, **info, "source": source, "rule_note": note,
                       "evidence": None})

    for r in rules.get("pairs", []):
        if r["a"] == src_group:
            add(out, r["b"], "pravidlo-par", r["c"])
    for r in rules.get("bundles", []):
        groups = [g.strip() for g in r["b"].split(",")]
        if src_group in groups:
            for g in groups:
                if g != src_group:
                    add(out, g, f"bundle:{r['a']}", r["c"])
    for r in rules.get("upgrades", []):
        if r["a"] == src_group:
            add(out, r["b"], "upgrade", r["c"])  # jediný povolený „upsell"
    for r in rules.get("flagship", []):
        add(flags, r["a"], "flagship", r["c"])
    return out, flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir", default="/documents/sales/.upsell-state")
    ap.add_argument("--catalog", default=None)
    ap.add_argument("--rules", default="/documents/sales/salesDNA.md",
                    help="soubor s kurátorskou sekcí Upsell a katalog (§11)")
    ap.add_argument("--contact", default=None)
    ap.add_argument("--mine", action="store_true")
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--min-support", type=int, default=3)
    args = ap.parse_args()
    if not args.contact and not args.mine:
        ap.error("zadej --contact <id> nebo --mine")

    try:
        with _as.locked(Path(args.state_dir) / "purchase-sync", timeout=30):
            purchases = load_json(os.path.join(args.state_dir, "purchases.json"), {})
            meta = load_json(os.path.join(args.state_dir, "meta.json"), {})
    except TimeoutError as exc:
        print(json.dumps({"error": str(exc), "code": "purchase_state_locked"}, ensure_ascii=False))
        return 3
    catalog = load_json(args.catalog, None) if args.catalog else None
    if not purchases:
        print(json.dumps({"error": "prázdná nákupní historie — spusť nejdřív purchase_sync.py"},
                         ensure_ascii=False))
        return

    events = build_events(purchases)
    stats, customers = pair_stats(events, args.days)
    rules = parse_rules(args.rules)
    warn = rules_warnings(rules, catalog)

    if args.mine:
        rows = []
        for a, targets in stats.items():
            for b, s in targets.items():
                if s["both"] < args.min_support:
                    continue
                rows.append({
                    "koupil": a, "pak": b, "zakazniku_obou": s["both"],
                    "zakazniku_A": customers[a],
                    "pct": round(100 * s["both"] / customers[a]) if customers[a] else 0,
                    "same_order": s["same_order"], "do_N_dni": s["within"],
                    "median_dni": median(s["gaps"]),
                })
        rows.sort(key=lambda r: (r["zakazniku_obou"], r["pct"]), reverse=True)
        if catalog:
            for r in rows[:50]:
                r["koupil_nazev"] = enrich(r["koupil"], catalog)["title"]
                r["pak_nazev"] = enrich(r["pak"], catalog)["title"]
        print(json.dumps({
            "mode": "mine", "days_window": args.days, "min_support": args.min_support,
            "customers_total": len(events), "pairs": rows[:50],
            "history_since": meta.get("history_since"),
            "rules_loaded": bool(rules),
            "rules_unknown_groups": warn or None,
        }, ensure_ascii=False, indent=1))
        return

    cid = args.contact
    owned, refunded = contact_groups(purchases, cid)
    plist = purchases.get(cid, [])
    paid_rows, _refunded_groups = eligible_paid_entries(plist)
    last = max(paid_rows, key=lambda row: parse_ts(row.get("at", "")) or 0, default=None)
    src_group = (last or {}).get("main_group", "")

    # sekce 5 pravidel filtruje VŠECHNY vrstvy
    banned = set()
    if rules:
        banned = {r["b"].strip() for r in rules.get("never", [])
                  if r["a"].strip() in (src_group, "*")}

    # vrstva 1: kurátorská pravidla (pár → bundle → upgrade; flagship až za evidenci)
    rule_cands, flagship_cands = ([], [])
    if rules and src_group:
        rule_cands, flagship_cands = rule_candidates(
            rules, src_group, owned, refunded, banned, catalog)

    # vrstva 2: evidence (co-purchase mining)
    evidence_cands = []
    if src_group and src_group in stats:
        for b, s in sorted(stats[src_group].items(),
                           key=lambda kv: (kv[1]["both"], kv[1]["within"]), reverse=True):
            if (s["both"] < args.min_support or b in owned or b in refunded
                    or b in banned):
                continue
            info = enrich(b, catalog)
            if not in_stock(info):
                continue
            base = customers[src_group]
            evidence_cands.append({
                "group": b, **info, "source": "evidence", "rule_note": "",
                "evidence": {
                    "zakazniku_obou": s["both"], "zakazniku_zaklad": base,
                    "pct": round(100 * s["both"] / base) if base else 0,
                    "same_order": s["same_order"], "do_N_dni": s["within"],
                    "median_dni": median(s["gaps"]), "okno_dni": args.days,
                },
            })

    # sloučení vrstev: pravidla → evidence → flagship, dedup, strop --top
    candidates, seen = [], set()
    for c in rule_cands + evidence_cands + flagship_cands:
        if c["group"] in seen:
            continue
        seen.add(c["group"])
        candidates.append(c)
        if len(candidates) >= args.top:
            break

    print(json.dumps({
        "contact": cid,
        "purchase_count": len(paid_rows),  # jen platné zaplacené nákupy
        "last_purchase": {
            "at": (last or {}).get("at"), "src": (last or {}).get("src"),
            "items": [i["name"] for i in (last or {}).get("items", []) if i.get("is_product")],
            "main_group": src_group,
            "main_group_title": enrich(src_group, catalog)["title"] if src_group else "",
            "match": next((i["match"] for i in (last or {}).get("items", [])
                           if i.get("is_product")), "none"),
        } if last else None,
        "owned_groups": sorted(owned), "refunded_groups": sorted(refunded),
        "history_since": meta.get("history_since"),
        "rules_loaded": bool(rules),
        "rules_unknown_groups": warn or None,
        "candidates": candidates,
        "note": None if candidates else
        "žádné pravidlo ani evidence s dostatečnou podporou — použij productDNA (fallback), nefabuluj",
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    raise SystemExit(main() or 0)
