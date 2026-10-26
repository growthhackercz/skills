#!/usr/bin/env python3
"""purchase_sync.py — nákupní historie pro AI Upsell & Cross-sell agent (v0.1).

Stáhne nové transakce přes pojmenovaný tenantní GHL read helper (delta
podle createdAt), ke každé dohledá
položky (detail objednávky v platformě / FAPI faktura přes číslo faktury /
fallback) a udržuje nákupní historii per kontakt. Model se dívá jen na
výsledné události, nikdy na celou bázi.

Stav: <state-dir>/purchases.json + meta.json
Použití:
  python3 purchase_sync.py --state-dir /documents/sales/.upsell-state \
      --output /tmp/purchases.json [--mode auto|full|delta] \
      [--catalog <catalog.json>] [--match-key sku|ean|feed_id]

První běh = založení historie BEZ událostí (baseline). FAPI přístup volitelný
(FAPI_USER + FAPI_API_KEY v prostředí) — bez něj se FAPI zdroj přeskočí.
Bez externích závislostí (stdlib only). GHL credential načte pouze sdílený
helper z Control Center credential store; volitelný FAPI read kontrakt zůstává
samostatný.
"""
import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
import time
import urllib.error
import urllib.request
from urllib.parse import urlencode

# --- Sdílené moduly skillu (audit P1-12, P1-13) ---------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import atomic_state as _as  # noqa: E402
import state_version as _sv  # noqa: E402

SKILL_NAME = "sales-upsell"
SKILL_VERSION = "1.0"

FAPI_BASE = "https://api.fapi.cz"
USER_AGENT = "Mozilla/5.0 (compatible; CliqSales-Upsell/0.1; +https://cliqsales.cz)"
PAGE_SLEEP = 0.12
FULL_LOOKBACK_DAYS = 365
MAX_FAPI_RESPONSE_BYTES = 5_000_000


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


_FAPI_OPENER = urllib.request.build_opener(_NoRedirect)

# Audit P1-08: `purchase_new` smí vzniknout JEN z prokazatelně zaplacené
# transakce. Dřív se stav jen uložil a event vznikl vždy, takže neúspěšný
# nebo refundovaný nákup spustil upsell.
PAID_STATES = {"paid", "succeeded", "success", "completed", "complete",
               "captured", "settled", "active", "fulfilled"}
REFUNDED_STATES = {"refunded", "partially_refunded", "chargeback", "reversed"}
FAILED_STATES = {"failed", "cancelled", "canceled", "voided", "declined",
                 "expired", "pending", "unpaid", "incomplete", "processing"}

NONPRODUCT_RE = re.compile(
    r"doprav|dobírk|dobirk|balné|balne|poštov|postov|shipping|delivery|"
    r"pojišt|pojist|sleva|discount|kupon|kupón|voucher", re.IGNORECASE)


# ---------------------------------------------------------------- credentials
def _load_cc_credentials(fn_name):
    """Najde platformní cc_credentials a vrátí požadovanou funkci."""
    here = Path(__file__).resolve()
    cands = [here.parents[1].parent / "_lib"]
    for env in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw = os.environ.get(env, "").strip()
        if raw:
            h = Path(raw).expanduser()
            cands += [h / "cs-skills" / "_lib", h / ".openclaw" / "cs-skills" / "_lib"]
    cands.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
    cands += [par / "cs-skills" / "_lib" for par in here.parents]
    for d in cands:
        if not (d / "cc_credentials.py").exists():
            continue
        if str(d) not in sys.path:
            sys.path.insert(0, str(d))
        try:
            import cc_credentials  # type: ignore
            return getattr(cc_credentials, fn_name, None)
        except Exception:  # noqa: BLE001
            continue
    return None


def _sales_plan_module():
    here = Path(__file__).resolve()
    candidates = [here.parents[1].parent / "_lib"]
    for env_name in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw = os.environ.get(env_name, "").strip()
        if raw:
            home = Path(raw).expanduser()
            candidates += [home / "cs-skills" / "_lib", home / ".openclaw" / "cs-skills" / "_lib"]
    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
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


def fapi_credentials():
    """Audit P1-08: store-first přes platformní helper.

    Dřív se čtlo jen z prostředí a pod názvem `FAPI_API_KEY`. Custom variables
    Control Centra ale NEJSOU environment variables a kanonický název tokenu je
    `FAPI_TOKEN` — standardně nakonfigurované FAPI tak skill nikdy neviděl
    a reálné nákupy se vynechávaly.
    """
    fn = _load_cc_credentials("fapi_credentials")
    if fn:
        try:
            c = fn() or {}
            if c.get("user") and c.get("token"):
                return (c["user"], c["token"])
        except Exception:  # noqa: BLE001 - store nedostupný → zkusíme env
            pass
    # Fallback na prostředí, včetně staršího názvu.
    user = os.environ.get("FAPI_USER")
    token = os.environ.get("FAPI_TOKEN") or os.environ.get("FAPI_API_KEY")
    return (user, token) if user and token else None


# ---------------------------------------------------------------------- http
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


def fapi_call(auth, path, query=None):
    if path != "/invoices":
        raise RuntimeError("FAPI read cesta není povolená")
    url = FAPI_BASE + path + (("?" + urlencode(query)) if query else "")
    token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    })
    try:
        with _FAPI_OPENER.open(req, timeout=45) as response:
            raw = response.read(MAX_FAPI_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            raise RuntimeError("FAPI redirect byl bezpečně odmítnut") from exc
        raise RuntimeError(f"FAPI vrátil HTTP {exc.code}") from exc
    if len(raw) > MAX_FAPI_RESPONSE_BYTES:
        raise RuntimeError("FAPI odpověď překročila bezpečný limit")
    try:
        parsed = json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("FAPI vrátilo neplatnou JSON odpověď") from exc
    if not isinstance(parsed, (dict, list)):
        raise RuntimeError("FAPI vrátilo neočekávaný tvar odpovědi")
    return parsed


# ------------------------------------------------------------------- katalog
def load_catalog_indexes(catalog_path, match_key):
    if not catalog_path:
        return None, None
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import feed_catalog  # type: ignore
    cat = feed_catalog.load_catalog(catalog_path)
    if not cat:
        print(f"POZN: katalog {catalog_path} nenačten — párování jen podle kódu.", file=sys.stderr)
        return None, None
    return feed_catalog.build_index(cat, match_key), feed_catalog.build_name_index(cat)


def match_item(name, code, idx, name_idx):
    """→ (item_group, match). match: sleva/klíč = jistý, name = nízká jistota, none."""
    if idx and code:
        hit = idx.get(str(code).strip().lower())
        if hit:
            return hit[1]["group"], "key"
    if name_idx and name:
        hit = name_idx.get(re.sub(r"\s+", " ", name.strip().lower()))
        if hit:
            return hit[1]["group"], "name"
    if code:
        return f"code:{str(code).strip().lower()}", "code"
    if name:
        return "name:" + re.sub(r"[^a-z0-9]+", "-", name.strip().lower())[:60], "none"
    return "", "none"


# ------------------------------------------------------------------ transakce
def fetch_transactions(cc, since_iso, end_iso):
    """Transakce od since_iso. Stránkuje přes limit+offset, jistí klientský filtr."""
    out, offset, expected_total = [], 0, None
    seen_ids = set()
    while offset <= 20000:
        res = broker_call(cc, "transactions", {
            "limit": 100, "offset": offset, "startAt": since_iso, "endAt": end_iso,
        })
        batch = res.get("transactions") or []
        if not isinstance(batch, list):
            raise RuntimeError("GHL transactions vrátily neplatný seznam")
        meta = res.get("meta") or {}
        total = meta.get("totalCount")
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise RuntimeError("GHL transactions nemají platný totalCount")
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise RuntimeError("GHL transactions změnily totalCount během stránkování")
        for transaction in batch:
            txn_id = str(
                transaction.get("_id") or transaction.get("id") or ""
            ).strip() if isinstance(transaction, dict) else ""
            if not txn_id or txn_id in seen_ids:
                raise RuntimeError("GHL transactions obsahují chybějící nebo duplicitní ID")
            seen_ids.add(txn_id)
        # Trust the provider window. Do not discard an older ``createdAt`` row
        # returned because its status changed; that is how pending→paid and
        # paid→refunded transitions reach the reconciler.
        out.extend(t for t in batch if isinstance(t, dict))
        if len(out) == expected_total:
            break
        if not batch or len(batch) < 100 or len(out) > expected_total:
            raise RuntimeError("GHL transaction stránky nepokrývají deklarovaný totalCount")
        offset += len(batch)
        if offset > 20000:
            raise RuntimeError(
                "GHL transactions překročily bezpečný limit 20 000 záznamů v jednom okně"
            )
        time.sleep(PAGE_SLEEP)
    if expected_total is None or len(out) != expected_total:
        raise RuntimeError("GHL transaction reconciliation okno není úplné")
    return out


def state_timestamp(value):
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.timestamp() if parsed.tzinfo is not None else None


def txn_fapi_invoice(t):
    meta = t.get("entitySourceMeta") or {}
    inv = meta.get("invoiceNumber")
    if inv:
        return str(inv)
    m = re.search(r"FAPI\D*?(\d{6,})", t.get("entitySourceName") or "")
    return m.group(1) if m else None


def resolve_items(cc, fapi_auth, t, idx, name_idx):
    """Položky transakce → (items, src). Zdroje: FAPI faktura / detail objednávky."""
    inv_num = txn_fapi_invoice(t)
    if inv_num and fapi_auth:
        try:
            res = fapi_call(fapi_auth, "/invoices", {"number": inv_num})
            invs = res if isinstance(res, list) else res.get("invoices") or res.get("data") or []
            if isinstance(invs, dict):
                invs = [invs]
            if invs:
                items = []
                for it in invs[0].get("items", []):
                    name, code = it.get("name", ""), str(it.get("code") or "").strip()
                    group, match = match_item(name, code, idx, name_idx)
                    items.append(_norm_item(name, code, it.get("price"), it.get("quantity"), group, match))
                if items:
                    return items, "fapi"
        except Exception as e:
            print(f"POZN: FAPI faktura {inv_num} nedostupná ({e}) — zkouším jiný zdroj.", file=sys.stderr)
    elif inv_num and not fapi_auth:
        print(f"POZN: transakce s FAPI fakturou {inv_num}, ale FAPI_USER/FAPI_API_KEY chybí — položky neurčeny.", file=sys.stderr)

    order_id = t.get("entityId") or t.get("orderId")
    if order_id and not inv_num:
        try:
            o = broker_call(cc, "order.detail", {"orderId": order_id}).get("order") or {}
            items = []
            for it in (o.get("items") or []):
                prod = it.get("product") or {}
                name = it.get("name") or prod.get("name", "")
                code = str(it.get("sku") or prod.get("sku") or prod.get("_id") or "").strip()
                price = it.get("price") or it.get("amount") or prod.get("amount")
                group, match = match_item(name, code, idx, name_idx)
                items.append(_norm_item(name, code, price, it.get("qty") or it.get("quantity"), group, match))
            if items:
                return items, "order"
        except RuntimeError as e:
            print(f"POZN: detail objednávky {order_id} nedostupný ({e}).", file=sys.stderr)
    return [], "txn"


def _norm_item(name, code, price, qty, group, match):
    try:
        price = float(price) if price is not None else None
    except (TypeError, ValueError):
        price = None
    is_product = not NONPRODUCT_RE.search(name or "") and (price is None or price >= 0)
    return {"name": name, "code": code, "price": price, "qty": qty or 1,
            "group": group, "match": match, "is_product": is_product}


def classify_status(status):
    """Return the canonical transaction state; unknown is always non-paid."""
    normalized = str(status or "").strip().lower()
    if normalized in PAID_STATES:
        return "paid", None
    if normalized in REFUNDED_STATES:
        return "refunded", "refundováno"
    if normalized in FAILED_STATES:
        return "unpaid", "neúspěšná nebo nedokončená platba"
    return "unknown", f"neznámý stav '{normalized or 'chybí'}' — nepovažuje se za zaplacené"


def entry_state(entry):
    """Read new and legacy rows fail-closed."""
    state = str((entry or {}).get("state") or "").strip().lower()
    if state in {"paid", "refunded", "unpaid", "unknown"}:
        return state
    if (entry or {}).get("refunded") is True:
        return "refunded"
    if (entry or {}).get("paid") is True:
        return "paid"
    if (entry or {}).get("paid") is False:
        classified, _reason = classify_status((entry or {}).get("status"))
        return "refunded" if classified == "refunded" else "unpaid"
    classified, _reason = classify_status((entry or {}).get("status"))
    return classified


def _normalize_store(purchases):
    """Remove malformed rows and duplicate transaction keys, last row wins."""
    normalized = {}
    for contact_id, rows in (purchases or {}).items():
        if not isinstance(rows, list):
            continue
        by_key = {}
        key_order = []
        anonymous = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            key = str(row.get("key") or "").strip()
            if not key:
                anonymous.append(dict(row))
                continue
            if key not in by_key:
                key_order.append(key)
            by_key[key] = dict(row)
        clean = anonymous + [by_key[key] for key in key_order]
        if clean:
            normalized[str(contact_id)] = clean
    return normalized


def _indexes(purchases):
    by_key = {}
    by_entity = {}
    for contact_id, rows in purchases.items():
        for row in rows:
            key = str(row.get("key") or "").strip()
            if key:
                by_key[key] = (contact_id, row)
            entity_id = str(row.get("entity_id") or "").strip()
            if entity_id:
                by_entity.setdefault((contact_id, entity_id), []).append(row)
    return by_key, by_entity


def reconcile_transactions(purchases, transactions, resolve, baseline=False):
    """Merge provider snapshots and emit only real state transitions.

    Repeated IDs are updates, not permanent skips. Pending/failed/unknown rows
    stay auditable but never become purchases. A later paid transition emits
    exactly one ``purchase_new``; a later refund replaces/revokes ownership.
    """
    purchases = _normalize_store(purchases)
    by_key, by_entity = _indexes(purchases)
    events = []
    skipped_unpaid = []
    processed_ids = []
    state_changes = []

    for transaction in transactions:
        if not isinstance(transaction, dict):
            continue
        txn_id = str(transaction.get("_id") or transaction.get("id") or "").strip()
        if not txn_id:
            continue
        prior_location = by_key.get(txn_id)
        prior = dict(prior_location[1]) if prior_location else None
        contact_id = str(
            transaction.get("contactId")
            or (transaction.get("contactSnapshot") or {}).get("id", "")
            or (prior_location[0] if prior_location else "")
        ).strip()
        if not contact_id:
            continue
        status = str(transaction.get("paymentStatus") or transaction.get("status") or "").lower()
        try:
            amount_refunded = float(transaction.get("amountRefunded") or 0)
        except (TypeError, ValueError):
            amount_refunded = 0
        if amount_refunded > 0:
            status = "refunded"
        state, reason = classify_status(status)
        items, source = resolve(transaction)
        entity_id = str(transaction.get("entityId") or transaction.get("orderId") or "").strip()

        # Status-only updates/refunds often omit line items. Preserve the
        # previously resolved evidence for the same transaction or order.
        if not items and prior and prior.get("items"):
            items = prior["items"]
            source = prior.get("src") or source
        if not items and entity_id:
            related = by_entity.get((contact_id, entity_id), [])
            evidence = next((row for row in reversed(related) if row.get("items")), None)
            if evidence:
                items = evidence["items"]
                source = evidence.get("src") or source

        product_items = [
            item for item in (items or [])
            if isinstance(item, dict) and item.get("is_product")
        ]
        main_group = (
            max(product_items, key=lambda item: item.get("price") or 0).get("group", "")
            if product_items
            else (prior or {}).get("main_group", "")
        )
        entry = {
            "key": txn_id,
            "entity_id": entity_id or (prior or {}).get("entity_id", ""),
            "src": source or (prior or {}).get("src", "txn"),
            "at": transaction.get("createdAt") or (prior or {}).get("at", ""),
            "updated_at": transaction.get("updatedAt") or transaction.get("dateUpdated") or "",
            "amount": transaction.get("amount", (prior or {}).get("amount")),
            "currency": transaction.get("currency") or (prior or {}).get("currency", ""),
            "status": status,
            "state": state,
            "paid": state == "paid",
            "refunded": state == "refunded",
            "items": items or [],
            "main_group": main_group,
        }
        if reason:
            entry["storno"] = reason

        previous_state = entry_state(prior or {}) if prior else None
        if prior_location:
            old_contact, old_row = prior_location
            if old_contact == contact_id:
                old_row.clear()
                old_row.update(entry)
                stored = old_row
            else:
                purchases[old_contact] = [row for row in purchases[old_contact] if row is not old_row]
                if not purchases[old_contact]:
                    purchases.pop(old_contact, None)
                stored = entry
                purchases.setdefault(contact_id, []).append(stored)
        else:
            stored = entry
            purchases.setdefault(contact_id, []).append(stored)
        by_key[txn_id] = (contact_id, stored)
        if stored.get("entity_id"):
            by_entity.setdefault((contact_id, stored["entity_id"]), []).append(stored)

        processed_ids.append(txn_id)
        if previous_state != state:
            state_changes.append({
                "txnId": txn_id,
                "contactId": contact_id,
                "from": previous_state,
                "to": state,
            })
        event_base = {
            "contactId": contact_id,
            "txnId": txn_id,
            "src": entry["src"],
            "amount": entry["amount"],
            "currency": entry["currency"],
            "items": [item.get("name", "") for item in product_items]
            or [item.get("name", "") for item in (items or []) if isinstance(item, dict)],
            "main_group": main_group,
            "match": product_items[0].get("match", "none") if product_items else "none",
        }
        if not baseline and state == "paid" and previous_state != "paid":
            events.append({"type": "purchase_new", **event_base})
        elif not baseline and state == "refunded" and previous_state != "refunded":
            events.append({"type": "purchase_refunded", **event_base})
        elif not baseline and previous_state == "paid" and state != "paid":
            events.append({"type": "purchase_invalidated", "state": state, **event_base})

        if state != "paid":
            skipped_unpaid.append({
                "txnId": txn_id,
                "contactId": contact_id,
                "status": status,
                "state": state,
                "duvod": reason,
            })

    return {
        "purchases": purchases,
        "events": events,
        "skipped_unpaid": skipped_unpaid,
        "processed_ids": processed_ids,
        "state_changes": state_changes,
    }


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
    """Atomický zápis s verzí stavu (audit P1-12)."""
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
    ap.add_argument("--state-dir", default="/documents/sales/.upsell-state")
    ap.add_argument("--output", default=None)
    ap.add_argument("--mode", choices=["auto", "full", "delta"], default="auto")
    ap.add_argument("--overlap-min", type=int, default=15)
    ap.add_argument("--catalog", default=None, help="catalog.json z feed_catalog.py")
    ap.add_argument("--match-key", choices=["feed_id", "sku", "ean"], default="sku",
                    help="párovací klíč dle salesDNA §11 (Feed)")
    ap.add_argument("--credential-profile", default="default")
    args = ap.parse_args()

    if args.overlap_min < 1:
        ap.error("--overlap-min musí být kladný")
    cc = args.credential_profile
    fapi_auth = fapi_credentials()
    idx, name_idx = load_catalog_indexes(args.catalog, args.match_key)

    os.makedirs(args.state_dir, exist_ok=True)
    p_purch = os.path.join(args.state_dir, "purchases.json")
    p_meta = os.path.join(args.state_dir, "meta.json")
    try:
        with _as.locked(Path(args.state_dir) / "purchase-sync", timeout=90):
            check_state_version(args.state_dir)
            purchases = load_json(p_purch, {})
            meta = load_json(p_meta, {})
            if not isinstance(purchases, dict) or not isinstance(meta, dict):
                raise RuntimeError("stav nákupů má neplatný tvar")
            seen_order = [str(value) for value in meta.get("seen_txn", []) if str(value)]
            baseline = not purchases and not seen_order

            mode = args.mode
            if mode == "auto":
                mode = "delta" if meta.get("last_run") else "full"
            run_started = time.time()
            default_since = run_started - FULL_LOOKBACK_DAYS * 86400
            history_since = str(meta.get("history_since") or "").strip()
            try:
                history_epoch = time.mktime(time.strptime(history_since, "%Y-%m-%d")) - time.timezone
            except ValueError:
                history_epoch = default_since
            known_timestamps = [
                timestamp
                for rows in purchases.values()
                if isinstance(rows, list)
                for row in rows
                if isinstance(row, dict)
                for timestamp in [state_timestamp(row.get("at"))]
                if timestamp is not None
            ]
            since_epoch = min([history_epoch, *known_timestamps]) if known_timestamps else history_epoch
            since_iso = time.strftime("%Y-%m-%d", time.gmtime(since_epoch))
            end_iso = time.strftime("%Y-%m-%d", time.gmtime(run_started))

            transactions = fetch_transactions(cc, since_iso, end_iso)

            def resolver(transaction):
                resolved = resolve_items(cc, fapi_auth, transaction, idx, name_idx)
                time.sleep(PAGE_SLEEP)
                return resolved

            merged = reconcile_transactions(
                purchases,
                transactions,
                resolver,
                baseline=baseline,
            )
            purchases = merged["purchases"]
            processed_ids = merged["processed_ids"]
            seen_order = list(dict.fromkeys(seen_order + processed_ids))[-20000:]
            paid_contacts = sum(
                1 for rows in purchases.values()
                if any(entry_state(row) == "paid" for row in rows)
            )
            meta.update({
                "last_run": run_started,
                "last_mode": mode,
                "seen_txn": seen_order,
                "history_since": time.strftime("%Y-%m-%d", time.gmtime(since_epoch)),
                "contacts_with_transactions": len(purchases),
                "contacts_with_paid_purchases": paid_contacts,
                "contacts_with_purchases": paid_contacts,
            })
            # Readers use the same lock; each committed file is replaced atomically.
            save_json(p_purch, purchases)
            save_json(p_meta, meta)

            result = {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(run_started)),
                "mode": mode,
                "baseline": baseline,
                "history_since": meta["history_since"],
                "totals": {
                    "contacts_with_transactions": len(purchases),
                    "contacts_with_paid_purchases": paid_contacts,
                    "contacts_with_purchases": paid_contacts,
                    "txn_seen": len(seen_order),
                },
                "event_count": len(merged["events"]),
                "events": merged["events"],
                "state_change_count": len(merged["state_changes"]),
                "state_changes": merged["state_changes"],
                "skipped_unpaid_count": len(merged["skipped_unpaid"]),
                "skipped_unpaid": merged["skipped_unpaid"],
            }
    except TimeoutError as exc:
        print(f"PŘESKOČENO: {exc}", file=sys.stderr)
        return 3
    except StateReadError as exc:
        print(f"CHYBA: {exc}", file=sys.stderr)
        return 4
    except RuntimeError as exc:
        print(f"CHYBA: {exc}", file=sys.stderr)
        return 2

    out = json.dumps(result, ensure_ascii=False, indent=1)
    if args.output:
        _as.write_json_atomic(args.output, result)
        print(f"OK mode={mode} nákupčí={len(purchases)} události={result['event_count']} "
              f"nezaplacené/storno={result['skipped_unpaid_count']} → {args.output}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
