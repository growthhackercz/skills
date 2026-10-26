#!/usr/bin/env python3
"""ghl_snapshot.py — jádro cron běhu AI Sales Stratéga (v0.1).

Stáhne stav CRM přes pojmenovaný tenantní GHL read helper (kontakty,
opportunities, objednávky, schůzky), porovná se
snapshotem z minulého běhu a vypíše SEZNAM UDÁLOSTÍ jako JSON. Model se dívá
jen na události — nikdy na celou bázi.

Režimy:
  --mode auto   delta pokud existuje snapshot, jinak full (výchozí)
  --mode full   plný sken celé báze (initial / noční rekonsiliace)
  --mode delta  jen kontakty změněné od minulého běhu (s překryvem)

Použití:
  python3 ghl_snapshot.py --state-dir /documents/sales/.strategist-state \
      --output /tmp/events.json [--mode auto] [--overlap-min 15]

Bez externích závislostí (stdlib only). Credential načte pouze sdílený helper
z Control Center credential store.
"""
import argparse
import json
import os
import re
import sys
import time

# --- Zámek nad snapshotem (audit P1-10) -----------------------------------
import sys as _syss
from pathlib import Path as _Paths
_syss.path.insert(0, str(_Paths(__file__).resolve().parent.parent / "lib"))
import atomic_state as _as  # noqa: E402
import state_version as _sv  # noqa: E402

# Audit P1-12: trvalý stav musí nést verzi, aby ho novější skill nepřečetl
# starým způsobem a naopak.
SKILL_NAME = "sales-strategist"
SKILL_VERSION = "1.1"

PAGE_SLEEP = 0.12  # rate limit 100 req / 10 s
MEETING_WINDOW_H = 36  # schůzky v příštích X hodinách => event


# ---------------------------------------------------------------- named reads
def _sales_plan_module():
    here = _Paths(__file__).resolve()
    candidates = [here.parents[1].parent / "_lib"]
    for env_name in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw = os.environ.get(env_name, "").strip()
        if raw:
            home = _Paths(raw).expanduser()
            candidates += [home / "cs-skills" / "_lib", home / ".openclaw" / "cs-skills" / "_lib"]
    candidates.append(_Paths.home() / ".openclaw" / "cs-skills" / "_lib")
    candidates += [parent / "cs-skills" / "_lib" for parent in here.parents]
    for directory in candidates:
        if not (directory / "sales_ghl_plan.py").exists():
            continue
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
        try:
            import sales_ghl_plan  # type: ignore

            return sales_ghl_plan
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError("sdílený Sales GHL read helper není dostupný")


def broker_call(profile, resource, query=None, retries=2):
    try:
        return _sales_plan_module().read_resource(
            resource,
            query or {},
            profile=profile,
            retries=retries,
        )
    except Exception as exc:
        raise RuntimeError(f"GHL read {resource} selhal: {exc}") from exc


# ----------------------------------------------------------------- normalizace
def norm_contact(c):
    return {
        "id": c.get("id"),
        "name": ((c.get("firstName") or "") + " " + (c.get("lastName") or "")).strip()
        or c.get("contactName") or "",
        "email": c.get("email") or "",
        "phone": c.get("phone") or "",
        "tags": sorted(t.lower() for t in (c.get("tags") or [])),
        "dnd": bool(c.get("dnd")),
        "assigned": c.get("assignedTo") or "",
        "dateUpdated": c.get("dateUpdated") or "",
        "dateAdded": c.get("dateAdded") or "",
    }


def norm_opp(o):
    return {
        "id": o.get("id"),
        "name": o.get("name") or "",
        "contactId": o.get("contactId") or (o.get("contact") or {}).get("id", ""),
        "pipelineId": o.get("pipelineId") or "",
        "stageId": o.get("pipelineStageId") or o.get("stageId") or "",
        "status": o.get("status") or "",
        "value": o.get("monetaryValue") or 0,
        "assigned": o.get("assignedTo") or "",
        "updatedAt": o.get("updatedAt") or "",
        "createdAt": o.get("createdAt") or "",
        "lostReason": o.get("lostReasonId") or o.get("lostReason") or "",
    }


# ------------------------------------------------------------------- stahování
def fetch_contacts_full(cc):
    out = {}
    for page in range(1, 101):  # podporovaný Search Contacts má 10k bezpečnostní strop
        res = broker_call(cc, "contacts.full", {"limit": 100, "page": page})
        batch = res.get("contacts", [])
        for c in batch:
            n = norm_contact(c)
            if n["id"]:
                out[n["id"]] = n
        meta = res.get("meta") or {}
        if meta.get("truncated") is True:
            raise RuntimeError(
                "Úplný snapshot kontaktů překročil bezpečný limit 10 000 záznamů; "
                "výsledek se nepoužije jako neúplný."
            )
        next_page = meta.get("nextPage")
        if next_page is None:
            break
        if next_page != page + 1 or page == 100:
            raise RuntimeError("Broker vrátil neplatné stránkování úplného snapshotu kontaktů.")
        time.sleep(PAGE_SLEEP)
    return out


def fetch_contacts_delta(cc, since_iso):
    out, page = {}, 1
    while page <= 100:  # delta okno nikdy nesmí potřebovat víc (10k strop searche)
        query = {
            "limit": 100,
            "page": page,
            "since": since_iso,
        }
        res = broker_call(cc, "contacts.delta", query)
        batch = res.get("contacts", [])
        for c in batch:
            n = norm_contact(c)
            if n["id"]:
                out[n["id"]] = n
        if len(batch) < 100:
            break
        if page == 100:
            raise RuntimeError(
                "Delta snapshot kontaktů překročil bezpečný limit 10 000 záznamů; "
                "výsledek se nepoužije jako neúplný."
            )
        page += 1
        time.sleep(PAGE_SLEEP)
    return out


def fetch_opportunities(cc):
    out, page = {}, 1
    while True:
        res = broker_call(cc, "opportunities", {"limit": 100, "page": page})
        batch = res.get("opportunities", [])
        for o in batch:
            n = norm_opp(o)
            if n["id"]:
                out[n["id"]] = n
        meta = res.get("meta") or {}
        if meta.get("truncated") is True:
            raise RuntimeError("opportunity snapshot překročil bezpečný limit 10 000 záznamů")
        next_page = meta.get("nextPage")
        if not batch or len(batch) < 100:
            break
        if not isinstance(next_page, int) or isinstance(next_page, bool) or next_page != page + 1:
            raise RuntimeError("plná opportunity stránka nemá platné pokračování")
        page = next_page
        time.sleep(PAGE_SLEEP)
    return out


def fetch_orders(cc, since_iso, end_iso):
    """Kompletní bounded reconciliation okno objednávek, stránkované po 100."""
    out, offset, expected_total = [], 0, None
    seen_ids = set()
    while offset <= 20000:  # pojistka proti nekonečné smyčce
        try:
            res = broker_call(cc, "orders", {
                "limit": 100, "offset": offset, "startAt": since_iso, "endAt": end_iso,
            })
        except RuntimeError as e:
            raise RuntimeError(
                f"objednávky selhaly na offsetu {offset}; neúplné okno se nepoužije"
            ) from e
        batch = res.get("orders", [])
        meta = res.get("meta") or {}
        total = meta.get("totalCount")
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise RuntimeError("objednávky nemají platný totalCount")
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise RuntimeError("totalCount objednávek se během stránkování změnil")
        for o in batch:
            oid = str(o.get("_id") or o.get("id") or "").strip()
            if not oid or oid in seen_ids:
                raise RuntimeError("objednávky obsahují chybějící nebo duplicitní ID")
            seen_ids.add(oid)
            status = str(o.get("paymentStatus") or o.get("status") or "").strip().lower()
            try:
                amount_refunded = float(o.get("amountRefunded") or 0)
            except (TypeError, ValueError):
                amount_refunded = 0
            if amount_refunded > 0:
                status = "refunded"
            out.append({
                "id": o.get("_id") or o.get("id"),
                "contactId": (o.get("contactSnapshot") or {}).get("id") or o.get("contactId", ""),
                "amount": o.get("amount"),
                "currency": o.get("currency"),
                "status": status,
                "createdAt": o.get("createdAt", ""),
                "items": [i.get("name") for i in (o.get("items") or []) if i.get("name")],
            })
        if len(out) == expected_total:
            break
        if not batch or len(batch) < 100 or len(out) > expected_total:
            raise RuntimeError("objednávkové stránky nepokrývají deklarovaný totalCount")
        offset += len(batch)
        if offset > 20000:
            raise RuntimeError(
                "Snapshot objednávek překročil bezpečný limit 20 000 záznamů v jednom okně"
            )
        time.sleep(PAGE_SLEEP)
    if expected_total is None or len(out) != expected_total:
        raise RuntimeError("objednávkové reconciliation okno není úplné")
    return out


def fetch_order_items(cc, order_id):
    """Názvy položek z detailu objednávky (List Orders items NEVRACÍ — ověřeno
    2026-07-23 na CZ účtu: 0/226 v listu, detail ano). None = chyba dotazu."""
    try:
        res = broker_call(cc, "order.detail", {"orderId": order_id})
        order = res.get("order") or {}
        return [i.get("name") for i in (order.get("items") or []) if i.get("name")]
    except RuntimeError as e:
        print(f"POZN: detail objednávky {order_id} nedostupný ({e}).", file=sys.stderr)
        return None


def fetch_meetings(cc):
    """Schůzky v příštích MEETING_WINDOW_H hodinách (přes seznam kalendářů).
    Při nedostupnosti None."""
    now_ms = int(time.time() * 1000)
    try:
        cals = broker_call(cc, "calendars").get("calendars", [])
    except RuntimeError as e:
        print(f"POZN: kalendáře nedostupné ({e}) — zdroj přeskočen.", file=sys.stderr)
        return None
    out = []
    for cal in cals:
        cal_id = cal.get("id")
        if not cal_id:
            continue
        try:
            res = broker_call(cc, "calendar.events", {
                "calendarId": cal_id,
                "startTime": now_ms,
                "endTime": now_ms + MEETING_WINDOW_H * 3600 * 1000,
            })
        except RuntimeError as e:
            print(f"POZN: kalendář {cal.get('name', cal_id)} nedostupný ({e}).", file=sys.stderr)
            continue
        for e in res.get("events", []):
            out.append({
                "id": e.get("id"),
                "title": e.get("title", ""),
                "calendar": cal.get("name", ""),
                "contactId": e.get("contactId", ""),
                "assigned": e.get("assignedUserId", ""),
                "startTime": e.get("startTime", ""),
            })
        time.sleep(PAGE_SLEEP)
    return out


# ------------------------------------------------------------------------ diff
def diff_contacts(old, new, baseline):
    if baseline:  # první běh = jen založení snapshotu, žádné události
        return []
    events = []
    for cid, c in new.items():
        prev = old.get(cid)
        ctx = {"contactId": cid, "name": c["name"], "email": c["email"]}
        if prev is None:
            events.append({"type": "contact_new", **ctx, "tags": c["tags"]})
            continue
        added = sorted(set(c["tags"]) - set(prev["tags"]))
        removed = sorted(set(prev["tags"]) - set(c["tags"]))
        if added:
            events.append({"type": "contact_tags_added", **ctx, "tags": added})
        if removed:
            events.append({"type": "contact_tags_removed", **ctx, "tags": removed})
        if c["dnd"] != prev["dnd"]:
            events.append({"type": "contact_dnd_changed", **ctx, "dnd": c["dnd"]})
    return events


def diff_opps(old, new, baseline):
    if baseline:
        return []
    events = []
    for oid, o in new.items():
        prev = old.get(oid)
        ctx = {"opportunityId": oid, "name": o["name"], "contactId": o["contactId"],
               "pipelineId": o["pipelineId"], "value": o["value"], "assigned": o["assigned"]}
        if prev is None:
            events.append({"type": "opp_new", **ctx, "stageId": o["stageId"], "status": o["status"]})
            continue
        if o["stageId"] != prev["stageId"]:
            events.append({"type": "opp_stage_changed", **ctx,
                           "fromStageId": prev["stageId"], "toStageId": o["stageId"]})
        if o["status"] != prev["status"]:
            events.append({"type": "opp_status_changed", **ctx,
                           "fromStatus": prev["status"], "toStatus": o["status"]})
    return events


# ------------------------------------------------------------------------ main
class StateReadError(RuntimeError):
    """Existing durable state is corrupt and must remain untouched for recovery."""


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        raise StateReadError(
            f"trvalý stav {path} je nečitelný; běh jej nepřepíše. "
            "Opravte nebo archivujte poškozený soubor a spusťte běh znovu."
        ) from exc


def save_json(path, data):
    """Atomický zápis s verzí stavu (audit P1-10 atomicita, P1-12 verze)."""
    _as.write_json_atomic(path, data)


def check_state_version(state_dir):
    """Jedna verzní kontrola složky stavu za běh (audit P1-12).

    Verze žije v sidecaru `.state-version.json`, ne uvnitř map `id -> záznam` —
    tam by ji každá iterace přes `.items()` viděla jako další záznam.
    """
    notes, ok = _sv.check_dir(state_dir, SKILL_NAME, SKILL_VERSION)
    for line in _sv.warn_lines(notes):
        print(line, file=sys.stderr)
    if not ok:
        sys.exit(4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir", default="/documents/sales/.strategist-state")
    ap.add_argument("--output", default=None, help="soubor pro events JSON (default: stdout)")
    ap.add_argument("--mode", choices=["auto", "full", "delta"], default="auto")
    ap.add_argument("--overlap-min", type=int, default=15)
    ap.add_argument("--orders-backfill-months", type=int, default=24,
                    help="hloubka historie každého úplného reconciliation okna objednávek")
    ap.add_argument("--skip", default="", help="čárkou oddělené zdroje: orders,meetings")
    ap.add_argument("--credential-profile", default="default")
    args = ap.parse_args()
    if not 1 <= args.orders_backfill_months <= 120:
        ap.error("--orders-backfill-months musí být v rozsahu 1–120")


    # Audit P1-10: hourly, daily a weekly cron se v 08:00 překrývají (v pondělí
    # tři). Bez zámku dva běhy přečtou stejný stav a oba dispatchnou. Zámek nad
    # stavovou složkou to serializuje; druhý běh se ukončí bez zápisu.
    try:
        _lock_ctx = _as.locked(_Paths(args.state_dir) / "snapshot", timeout=90)
        _lock_ctx.__enter__()
        # Uvolnění při JAKÉMKOLI ukončení (return, sys.exit, výjimka) — bez
        # toho by zámek držel do konce procesu a další cron by ho viděl jako
        # aktivní běh.
        import atexit as _atexit
        _atexit.register(lambda: _lock_ctx.__exit__(None, None, None))
    except TimeoutError as e:
        print(f"PŘESKOČENO: {e}", file=sys.stderr)
        return 0
    cc = args.credential_profile
    os.makedirs(args.state_dir, exist_ok=True)
    check_state_version(args.state_dir)
    p_contacts = os.path.join(args.state_dir, "contacts.json")
    p_opps = os.path.join(args.state_dir, "opportunities.json")
    p_orders = os.path.join(args.state_dir, "orders.json")
    p_meta = os.path.join(args.state_dir, "meta.json")

    try:
        meta = load_json(p_meta, {})
        old_contacts = load_json(p_contacts, {})
        old_opps = load_json(p_opps, {})
        orders_store = load_json(p_orders, {})
    except StateReadError as exc:
        print(f"CHYBA: {exc}", file=sys.stderr)
        return 4
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}

    mode = args.mode
    if mode == "auto":
        mode = "delta" if old_contacts and meta.get("last_run") else "full"

    run_started = time.time()
    since_epoch = None
    if mode == "delta":
        since_epoch = meta.get("last_run", run_started - 3600) - args.overlap_min * 60
    since_iso = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(since_epoch or run_started - 30 * 86400))

    events = []
    baseline = not old_contacts  # první běh = založení snapshotu bez událostí

    # 1) kontakty
    if mode == "full":
        new_contacts = fetch_contacts_full(cc)
        events += diff_contacts(old_contacts, new_contacts, baseline)
        merged_contacts = new_contacts
    else:
        changed = fetch_contacts_delta(cc, since_iso)
        events += diff_contacts(old_contacts, changed, baseline)
        merged_contacts = dict(old_contacts)
        merged_contacts.update(changed)

    # 2) opportunities (báze bývá malá — plný sken každý běh)
    new_opps = fetch_opportunities(cc)
    events += diff_opps(old_opps, new_opps, baseline or not old_opps)

    # 3) objednávky — perzistentní historie v orders.json (kontrakt pro cycle_reminders.py)
    if "orders" not in skip:
        orders_baseline = not orders_store  # první naplnění = backfill historie, bez událostí
        configured_since = time.strftime(
            "%Y-%m-%d",
            time.gmtime(run_started - args.orders_backfill_months * 30 * 86400),
        )
        known_dates = [
            str(record.get("createdAt") or "")[:10]
            for record in orders_store.values()
            if isinstance(record, dict)
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(record.get("createdAt") or "")[:10])
        ]
        o_since = min([configured_since, *known_dates]) if known_dates else configured_since
        o_end = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(run_started))
        orders = fetch_orders(cc, o_since, o_end)
        seen = set(meta.get("seen_orders", []))
        _known_before = set(orders_store.keys())   # persistentní, nikdy se nemaže
        fresh_ids = []
        if orders:
            for o in orders:
                oid = o["id"]
                if not oid:
                    continue
                projected = {k: o[k] for k in
                             ("contactId", "items", "amount", "currency", "status", "createdAt")}
                if oid not in orders_store:  # merge — nikdy nemazat
                    orders_store[oid] = projected
                else:
                    # Order identity/history is persistent, but mutable provider
                    # truth (especially paid -> refunded) must not freeze at the
                    # status observed on the first run. List responses often omit
                    # items, so preserve an already enriched item list unless the
                    # current response carries a non-empty replacement.
                    current = orders_store[oid]
                    for key in ("contactId", "amount", "currency", "status", "createdAt"):
                        current[key] = projected[key]
                    if projected["items"]:
                        current["items"] = projected["items"]
                        current["_enriched"] = True
                # Nové je jen to, co ještě NENÍ v persistentním store ani
                # v cache — jinak by vypadnutí z cache vyrobilo duplicitní event.
                if oid not in seen and oid not in _known_before:
                    fresh_ids.append(oid)
                    seen.add(oid)
        # items jen v detailu objednávky → postupný enrichment (max 500/běh)
        to_enrich = [oid for oid, rec in orders_store.items()
                     if not rec.get("items") and not rec.get("_enriched")]
        fails = 0
        for oid in to_enrich[:500]:
            items = fetch_order_items(cc, oid)
            if items is None:
                fails += 1
                if fails > 10:
                    break  # zdroj nejspíš nedostupný, doženeme příští běh
                continue
            orders_store[oid]["items"] = items
            orders_store[oid]["_enriched"] = True
            time.sleep(PAGE_SLEEP)
        for oid in fresh_ids:
            if not (baseline or orders_baseline):
                rec = orders_store.get(oid, {})
                events.append({"type": "order_new", "id": oid,
                               **{k: rec.get(k) for k in
                                  ("contactId", "items", "amount", "currency", "status", "createdAt")}})
        # Audit P1-10: strop 5000 znamenal, že po 5000 novějších objednávkách
        # vypadla stará z evidence a znovu vyrobila event. Idempotenci teď drží
        # `orders_store`, který se nikdy nemaže — `seen_orders` je jen rychlá
        # cache posledních ID a smí rotovat.
        meta["seen_orders"] = (meta.get("seen_orders", []) + fresh_ids)[-5000:]
        meta["orders_known_total"] = len(orders_store)
        if orders or orders_store:
            save_json(p_orders, orders_store)
        meta["orders_total"] = len(orders_store)

    # 4) schůzky (příštích 36 h)
    if "meetings" not in skip:
        meetings = fetch_meetings(cc)
        notified_list = meta.get("notified_meetings", [])
        notified = set(notified_list)
        if meetings:
            for m in meetings:
                if m["id"] and m["id"] not in notified:
                    if not baseline:
                        events.append({"type": "meeting_upcoming", **m})
                    notified.add(m["id"])
                    notified_list.append(m["id"])
        meta["notified_meetings"] = notified_list[-2000:]

    # ulož stav
    save_json(p_contacts, merged_contacts)
    save_json(p_opps, new_opps)
    meta.update({"last_run": run_started, "last_mode": mode,
                 "contacts_total": len(merged_contacts), "opps_total": len(new_opps)})
    save_json(p_meta, meta)

    result = {
        "skillVersion": SKILL_VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(run_started)),
        "mode": mode,
        "since": since_iso if mode == "delta" else None,
        "totals": {"contacts": len(merged_contacts), "opportunities": len(new_opps),
                   "orders": meta.get("orders_total", 0)},
        "event_count": len(events),
        "events": events,
    }
    if args.output:
        _as.write_json_atomic(args.output, result)
        print(f"OK mode={mode} kontakty={len(merged_contacts)} opps={len(new_opps)} "
              f"události={len(events)} → {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    raise SystemExit(main())
