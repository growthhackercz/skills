#!/usr/bin/env python3
"""reactivation_candidates.py — kandidáti reaktivační vlny (v0.1).

ČTE POUZE snapshot stratéga (žádné API volání!):
  /documents/sales/.strategist-state/{contacts,opportunities,meta}.json

Parametry předává agent podle Sales DNA (§7 provozní pravidla) — skript má
[výchozí] hodnoty pro případ, že v DNA nejsou.

Použití:
  python3 reactivation_candidates.py --output /tmp/kandidati.json
  python3 reactivation_candidates.py --make-wave /documents/sales/vlny/vlna-2026-07.json \
      --wave-slug vlna-2026-07 --wave-size 100

Výstup: JSON s kandidáty per segment (A/B/C), tier hot/warm, transparentní
počty vyřazených per filtr a detekce degradovaného režimu.
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DAY = 86400


def _sales_plan():
    shared = Path(__file__).resolve().parents[2] / "_lib"
    script_path = Path(__file__).resolve()
    candidates: list[Path] = [shared]
    for env_name in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw_home = (os.environ.get(env_name) or "").strip()
        if raw_home:
            home = Path(raw_home).expanduser()
            candidates.extend((home / "cs-skills" / "_lib", home / ".openclaw" / "cs-skills" / "_lib"))
    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
    candidates.extend(parent / "cs-skills" / "_lib" for parent in script_path.parents)
    seen: set[str] = set()
    for lib_dir in candidates:
        key = str(lib_dir)
        if key in seen or not (lib_dir / "sales_ghl_plan.py").is_file():
            continue
        seen.add(key)
        if key not in sys.path:
            sys.path.insert(0, key)
        try:
            import sales_ghl_plan  # type: ignore
        except Exception:
            continue
        return sales_ghl_plan
    raise RuntimeError("sdílený Sales GHL helper není dostupný")


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def iso_to_epoch(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return time.mktime(time.strptime(s, fmt)) - time.timezone
        except ValueError:
            continue
    return None


def months_since(yyyy_mm, now):
    m = re.match(r"^(\d{4})-(\d{2})$", yyyy_mm)
    if not m:
        return None
    then = (int(m.group(1)), int(m.group(2)))
    cur = time.gmtime(now)
    return (cur.tm_year - then[0]) * 12 + (cur.tm_mon - then[1])


def days_since_date(yyyy_mm_dd, now):
    m = re.match(r"^(\d{4}-\d{2}-\d{2})$", yyyy_mm_dd)
    if not m:
        return None
    try:
        then = time.mktime(time.strptime(yyyy_mm_dd, "%Y-%m-%d")) - time.timezone
        return (now - then) / DAY
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir", default="/documents/sales/.strategist-state")
    ap.add_argument("--output", default=None)
    ap.add_argument("--make-wave", default=None, help="cesta pro soubor vlny (kohorta)")
    ap.add_argument("--wave-slug", default=None)
    ap.add_argument("--wave-size", type=int, default=100)
    ap.add_argument("--no-ab", action="store_true", help="vypnout A/B split")
    # parametry ze Sales DNA §7 (agent je dosadí; níže [výchozí])
    ap.add_argument("--sleep-days", type=int, default=180)
    ap.add_argument("--quarantine-months", type=int, default=6)
    ap.add_argument("--lost-min-days", type=int, default=60)
    ap.add_argument("--lost-max-days", type=int, default=360)
    ap.add_argument("--touch-cap-days", type=int, default=14)
    ap.add_argument("--recent-activity-days", type=int, default=30,
                    help="kontakt aktivní v posledních X dnech = není spící, nezařazovat")
    args = ap.parse_args()

    contacts = load_json(os.path.join(args.state_dir, "contacts.json"))
    opps = load_json(os.path.join(args.state_dir, "opportunities.json"))
    meta = load_json(os.path.join(args.state_dir, "meta.json")) or {}
    if not contacts or opps is None:
        print("CHYBA: snapshot stratéga nenalezen. Spusť nejdřív "
              "sales-strategist/scripts/ghl_snapshot.py --mode auto", file=sys.stderr)
        sys.exit(2)

    now = time.time()
    age_h = (now - meta.get("last_run", 0)) / 3600
    if age_h > 24:
        print(f"VAROVÁNÍ: snapshot je {age_h:.0f} h starý (>24 h) — doporučen refresh "
              f"(ghl_snapshot.py --mode auto).", file=sys.stderr)

    # index opportunities per kontakt
    open_by, lost_by, won_by = {}, {}, {}
    lost_total, lost_with_reason = 0, 0
    for o in opps.values():
        cid = o.get("contactId")
        if not cid:
            continue
        st = (o.get("status") or "").lower()
        if st == "open":
            open_by.setdefault(cid, []).append(o)
        elif st == "lost":
            lost_total += 1
            if o.get("lostReason"):
                lost_with_reason += 1
            lost_by.setdefault(cid, []).append(o)
        elif st == "won":
            won_by.setdefault(cid, []).append(o)

    degraded = lost_total == 0 or (lost_with_reason / max(lost_total, 1)) < 0.30
    mode = "degradovaný (chybí důvody prohry — skóre jen recency/hodnota/historie)" if degraded else "plný"

    filtered = {}
    def drop(reason):
        filtered[reason] = filtered.get(reason, 0) + 1

    segments = {"A": [], "B": [], "C": []}
    try:
        suppression = _sales_plan()
    except Exception as exc:
        print(f"CHYBA: lokální ochranu proti opakování nelze načíst ({exc})", file=sys.stderr)
        sys.exit(2)

    for cid, c in contacts.items():
        tags = c.get("tags") or []
        # --- tvrdé filtry ---
        if c.get("dnd"):
            drop("dnd"); continue
        try:
            if suppression.contact_has_local_suppression(
                str(cid), args.touch_cap_days, now=datetime.fromtimestamp(now, timezone.utc)
            ):
                drop("touch-cap (ověřená Sales zpráva)"); continue
        except Exception as exc:
            print(
                f"CHYBA: lokální ochranu proti opakování pro kontakt nelze ověřit ({exc})",
                file=sys.stderr,
            )
            sys.exit(2)
        q_block, touch_block = False, False
        for t in tags:
            if t.startswith("reaktivace:"):
                m = months_since(t.split(":", 1)[1], now)
                if m is not None and m < args.quarantine_months:
                    q_block = True
            if t.startswith("osloven:"):
                d = days_since_date(t.split(":", 1)[1], now)
                if d is not None and d < args.touch_cap_days:
                    touch_block = True
        if q_block:
            drop("karanténa reaktivace"); continue
        if touch_block:
            drop("touch-cap (osloven nedávno)"); continue
        if not c.get("email") and not c.get("phone"):
            drop("bez kontaktu (e-mail i telefon chybí)"); continue
        if cid in open_by:
            drop("otevřený obchod"); continue

        upd = iso_to_epoch(c.get("dateUpdated"))
        days_quiet = (now - upd) / DAY if upd else None
        if days_quiet is not None and days_quiet < args.recent_activity_days:
            drop("aktivní nedávno (není spící)"); continue

        channel = "sms" if c.get("phone") else "email"
        base = {"contactId": cid, "name": c.get("name"), "email": c.get("email"),
                "phone": c.get("phone"), "channel": channel}

        # --- segmenty (priorita A > C > B) ---
        lost = lost_by.get(cid)
        if lost:
            best = max(lost, key=lambda o: iso_to_epoch(o.get("updatedAt")) or 0)
            lt = iso_to_epoch(best.get("updatedAt"))
            days_lost = (now - lt) / DAY if lt else None
            if days_lost is not None and args.lost_min_days <= days_lost <= args.lost_max_days:
                tier = "hot" if days_lost <= 180 else "warm"
                segments["A"].append({**base, "tier": tier,
                    "why": f"prohraný obchod před {days_lost:.0f} dny"
                           + (f" ({best.get('lostReason')})" if best.get("lostReason") else "")
                           + (f", hodnota {best.get('value')}" if best.get("value") else "")})
                continue
            # lost mimo okno → propadá do C/B pokud splní

        is_customer = cid in won_by or any(t.startswith("produkt:") for t in tags)
        sleeping = days_quiet is None or days_quiet >= args.sleep_days
        if is_customer and sleeping:
            recent_won = max((iso_to_epoch(o.get("updatedAt")) or 0) for o in won_by.get(cid, [{}])) if cid in won_by else 0
            tier = "hot" if recent_won and (now - recent_won) / DAY <= 540 else "warm"
            segments["C"].append({**base, "tier": tier,
                "why": "zákazník bez aktivity"
                       + (f" {days_quiet:.0f} dní" if days_quiet is not None else " (bez data)")})
            continue

        if any(t.startswith("zajem:") for t in tags) and sleeping:
            zaj = [t.split(":", 1)[1] for t in tags if t.startswith("zajem:")]
            segments["B"].append({**base, "tier": "warm",
                "why": f"projevený zájem ({', '.join(zaj[:2])}), bez aktivity"})
            continue

    for seg in segments.values():
        seg.sort(key=lambda x: (x["tier"] != "hot", x["name"] or ""))

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "snapshot_age_hours": round(age_h, 1),
        "mode": mode,
        "params": {k: getattr(args, k) for k in
                   ("sleep_days", "quarantine_months", "lost_min_days",
                    "lost_max_days", "touch_cap_days", "recent_activity_days")},
        "totals": {"contacts": len(contacts),
                   "A": len(segments["A"]), "B": len(segments["B"]), "C": len(segments["C"])},
        "filtered": filtered,
        "segments": segments,
    }

    out = json.dumps(result, ensure_ascii=False, indent=1)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
    else:
        # bez --output jen souhrn (celý JSON by zahltil chat)
        print(f"Režim: {mode}")
        print(f"Kandidáti: A={len(segments['A'])} B={len(segments['B'])} C={len(segments['C'])} "
              f"(z {len(contacts)} kontaktů)")
        print("Vyřazeno:", json.dumps(filtered, ensure_ascii=False))

    if args.make_wave:
        slug = args.wave_slug or f"vlna-{time.strftime('%Y-%m-%d', time.gmtime(now))}"
        # pořadí: A-hot, C-hot, A-warm, C-warm, B
        ordered = ([x | {"segment": "A"} for x in segments["A"] if x["tier"] == "hot"]
                   + [x | {"segment": "C"} for x in segments["C"] if x["tier"] == "hot"]
                   + [x | {"segment": "A"} for x in segments["A"] if x["tier"] == "warm"]
                   + [x | {"segment": "C"} for x in segments["C"] if x["tier"] == "warm"]
                   + [x | {"segment": "B"} for x in segments["B"]])
        picked = ordered[: args.wave_size]
        for i, x in enumerate(picked):
            x["variant"] = "a" if (args.no_ab or i % 2 == 0) else "b"
        os.makedirs(os.path.dirname(args.make_wave) or ".", exist_ok=True)
        with open(args.make_wave, "w", encoding="utf-8") as f:
            json.dump({"slug": slug, "created": result["generated_at"], "mode": mode,
                       "params": result["params"], "size": len(picked),
                       "contacts": picked}, f, ensure_ascii=False, indent=1)
        print(f"Vlna: {len(picked)} kontaktů → {args.make_wave} (slug {slug})")


if __name__ == "__main__":
    main()
