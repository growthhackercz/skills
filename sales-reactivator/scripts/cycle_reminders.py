#!/usr/bin/env python3
"""Select repeat-purchase reminders and freeze one exact GHL plan.

The script reads only the strategist snapshot and never calls a GHL write while
planning. Preview is the default. ``--create-plan`` freezes immutable
per-recipient message and dependent additive-tag actions for separate exact-SHA
confirmation and execution by the shared helper.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from html import escape as html_escape
from pathlib import Path
from typing import Any


DAY = 86400
PAID_ORDER_STATUSES = {"paid", "completed", "succeeded"}
SCRIPT_PATH = Path(__file__).resolve()
SKILL_DIR = SCRIPT_PATH.parents[1]
SHARED_LIB = SKILL_DIR.parent / "_lib"
SKILL_VERSION = "1.0"
MAX_AS_OF_PAST_SECONDS = 60 * 60
MAX_AS_OF_FUTURE_SECONDS = 5 * 60
COHORT_KEYS = {"schemaVersion", "product", "reminders", "updatedAt"}
REMINDER_KEYS = {
    "key", "planSha256", "actionId", "taskId", "contactId", "product",
    "lastPurchase", "at", "channel", "providerMessageId", "providerState",
}


def _sales_plan():
    candidates: list[Path] = [SHARED_LIB]
    for env_name in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw_home = (os.environ.get(env_name) or "").strip()
        if raw_home:
            home = Path(raw_home).expanduser()
            candidates.extend((home / "cs-skills" / "_lib", home / ".openclaw" / "cs-skills" / "_lib"))
    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
    candidates.extend(parent / "cs-skills" / "_lib" for parent in SCRIPT_PATH.parents)
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
    raise RuntimeError("sdílený Sales GHL plánovač není dostupný")


def load_json(path: str, default: Any = None) -> Any:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


def load_cycle_cohort(path: Path, product: str) -> dict[str, Any]:
    if not path.exists():
        return {"schemaVersion": 1, "product": product, "reminders": []}
    cohort = load_json(str(path))
    if not isinstance(cohort, dict) or set(cohort) != COHORT_KEYS:
        raise ValueError(f"kohorta {path.name} má neplatný kontrakt")
    if cohort.get("schemaVersion") != 1 or cohort.get("product") != product:
        raise ValueError(f"kohorta {path.name} má jinou identitu")
    reminders = cohort.get("reminders")
    if not isinstance(reminders, list):
        raise ValueError(f"kohorta {path.name} má neplatné reminders")
    seen: set[str] = set()
    for reminder in reminders:
        if not isinstance(reminder, dict) or set(reminder) != REMINDER_KEYS:
            raise ValueError(f"kohorta {path.name} obsahuje neplatný reminder")
        key = str(reminder.get("key") or "")
        if (
            not key
            or key in seen
            or reminder.get("product") != product
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", str(reminder.get("contactId") or ""))
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(reminder.get("lastPurchase") or ""))
            or iso_to_epoch(str(reminder.get("at") or "")) is None
        ):
            raise ValueError(f"kohorta {path.name} obsahuje neplatnou identitu reminderu")
        seen.add(key)
    return cohort


def iso_to_epoch(value: str | None) -> float | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.timestamp() if parsed.tzinfo is not None else None


def days_since_date(value: str | None, now: float) -> float | None:
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value or ""):
        return None
    try:
        then = time.mktime(time.strptime(value, "%Y-%m-%d")) - time.timezone
        return (now - then) / DAY
    except ValueError:
        return None


def norm_text(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKD", (value or "").lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def median(values: list[float]) -> float | None:
    ordered = sorted(values)
    size = len(ordered)
    if not size:
        return None
    return ordered[size // 2] if size % 2 else (ordered[size // 2 - 1] + ordered[size // 2]) / 2


def personalize(template: str, name: str | None) -> str:
    first = (name or "").split()[0] if (name or "").strip() else ""
    out = template.replace("{jmeno}", first)
    if not first:
        out = out.replace(" ,", ",").replace(",,", ",").replace("  ", " ")
        out = out.lstrip(" ,").strip()
        if out and out[0].islower():
            out = out[0].upper() + out[1:]
    return out


def text_to_html(text: str) -> str:
    paras = [html_escape(part.strip()) for part in text.split("\n") if part.strip()]
    return "".join(
        '<p style="margin:0 0 14px;font-family:Arial,Helvetica,sans-serif;'
        f'font-size:15px;color:#222;">{part}</p>'
        for part in paras
    )


def parse_as_of(value: str | None, *, required: bool) -> tuple[float, str]:
    if not value:
        if required:
            raise ValueError("--create-plan vyžaduje stabilní --as-of jako ISO 8601 s časovým pásmem")
        now = datetime.now().astimezone()
        return now.timestamp(), now.isoformat()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("--as-of musí být ISO 8601 datum s časovým pásmem") from exc
    if parsed.tzinfo is None:
        raise ValueError("--as-of musí obsahovat časové pásmo")
    timestamp = parsed.timestamp()
    now = time.time()
    if timestamp < now - MAX_AS_OF_PAST_SECONDS or timestamp > now + MAX_AS_OF_FUTURE_SECONDS:
        raise ValueError("--as-of musí odpovídat aktuálnímu času (tolerance −60/+5 minut)")
    return timestamp, parsed.isoformat()


def parse_cycles(spec: str) -> dict[str, int | str]:
    result: dict[str, int | str] = {}
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"--cycles položka {part!r} nemá tvar produkt=dny|auto")
        slug, raw = (item.strip() for item in part.split("=", 1))
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", slug):
            raise ValueError("slug produktu v --cycles musí obsahovat jen a-z, 0-9 a pomlčku")
        if raw.lower() == "auto":
            result[slug] = "auto"
        else:
            days = int(raw)
            if days <= 0:
                raise ValueError(f"cyklus produktu {slug} musí být kladný")
            result[slug] = days
    if not result:
        raise ValueError("--cycles neobsahuje žádný produkt")
    return result


def purchases_by_contact(
    orders: dict[str, Any],
    product_slug: str,
    *,
    merge_days: int = 7,
) -> dict[str, list[float]]:
    needle = norm_text(product_slug).replace("-", " ")
    per: dict[str, list[float]] = {}
    for order in orders.values():
        if not isinstance(order, dict):
            continue
        contact_id = str(order.get("contactId") or "").strip()
        timestamp = iso_to_epoch(order.get("createdAt"))
        if not contact_id or not timestamp:
            continue
        status = str(order.get("status") or "").strip().lower()
        if status not in PAID_ORDER_STATUSES:
            continue
        items = " | ".join(norm_text(item) for item in (order.get("items") or []))
        if needle in items.replace("-", " "):
            per.setdefault(contact_id, []).append(timestamp)
    merged: dict[str, list[float]] = {}
    for contact_id, buys in per.items():
        buys.sort()
        result: list[float] = []
        for timestamp in buys:
            if result and timestamp - result[-1] < merge_days * DAY:
                result[-1] = timestamp
            else:
                result.append(timestamp)
        merged[contact_id] = result
    return merged


def _freeze_plan(
    args: argparse.Namespace,
    plans: list[dict[str, Any]],
    artifact: dict[str, Any],
) -> dict[str, Any]:
    client = _sales_plan()
    journal = client.SalesGhlPlan(
        args.plan_artifact,
        producer="sales-reactivator",
        skill_version=SKILL_VERSION,
        task_id=args.task_id,
        task_contract="sales-reactivator:cycle-actions",
        idempotency_key=args.idempotency_key.strip(),
        revision=args.plan_revision,
        source_agent=args.source_agent,
        source_run_id=args.source_run_id,
        metadata=artifact,
    )
    for plan in plans:
        parent_slot = str(plan.get("dependsOnSuffix") or "").strip()
        depends_on_action_id = journal.action_id_for_slot(parent_slot) if parent_slot else None
        if parent_slot and not depends_on_action_id:
            raise RuntimeError(f"chybí parent action ID pro závislost {parent_slot}")
        journal.add_action(
            slot=plan["suffix"],
            action_type=plan["actionType"],
            payload=plan["payload"],
            depends_on_action_id=depends_on_action_id,
            source_run_id=args.source_run_id,
            credential_profile=args.credential_profile,
            expires_at=args.expires_at,
            detail=plan.get("detail"),
        )
    return journal.finish([str(plan["suffix"]) for plan in plans])


def _record_execution(
    plan_artifact: str,
    confirm_plan_sha: str,
    cohort_dir: str,
) -> dict[str, Any]:
    client = _sales_plan()
    frozen = client.validate_plan(client.read_artifact(plan_artifact))
    if (
        frozen.get("producer") != "sales-reactivator"
        or frozen.get("skillVersion") != SKILL_VERSION
        or frozen.get("taskContract") != "sales-reactivator:cycle-actions"
    ):
        raise ValueError("artefakt není plán cyklických připomínek této verze")
    plan_sha = str(frozen.get("planSha256") or "")
    if confirm_plan_sha != plan_sha:
        raise ValueError("--confirm-plan-sha neodpovídá zmrazenému plánu")
    report = client.read_artifact(client.execution_report_path(plan_sha))
    succeeded = client.reconcile_message_suppressions(report, frozen)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for action, result in succeeded:
        if action.get("actionType") not in {
            "sales.ghl.message.send.v1",
            "sales.ghl.message.schedule.v1",
        }:
            continue
        detail = action.get("detail")
        if not isinstance(detail, dict) or detail.get("kind") != "cycle-reminder-message":
            raise ValueError("message akce nemá přesnou identitu cyklické kohorty")
        product = str(detail.get("productSlug") or "")
        contact_id = str(detail.get("contactId") or "")
        last_purchase = str(detail.get("lastPurchase") or "")
        if (
            not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", product)
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", contact_id)
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", last_purchase)
        ):
            raise ValueError("message akce má neplatnou identitu cyklické kohorty")
        receipt = result["providerReceipt"]
        readback = result["readback"]
        grouped.setdefault(product, []).append({
            "key": f"{plan_sha}:{action['actionId']}",
            "planSha256": plan_sha,
            "actionId": action["actionId"],
            "taskId": frozen["taskId"],
            "contactId": contact_id,
            "product": product,
            "lastPurchase": last_purchase,
            "at": result["completedAt"],
            "channel": action["payload"]["channel"],
            "providerMessageId": receipt["id"],
            "providerState": readback["state"],
        })
    if not grouped:
        raise ValueError("plán neobsahuje žádné ověřené cyklické message akce")

    root = Path(cohort_dir)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".cycle-cohorts.lock"
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    added = 0
    total = 0
    try:
        with os.fdopen(lock_fd, "r+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            for product, records in sorted(grouped.items()):
                path = root / f"cyklus-{product}.json"
                existing = load_cycle_cohort(path, product)
                reminders = existing["reminders"]
                by_key = {str(item.get("key") or ""): item for item in reminders}
                for record in records:
                    previous = by_key.get(record["key"])
                    if previous is not None and previous != record:
                        raise ValueError("existující kohortní záznam odporuje execution journalu")
                    if previous is None:
                        reminders.append(record)
                        by_key[record["key"]] = record
                        added += 1
                reminders.sort(key=lambda item: (str(item.get("at") or ""), str(item.get("key") or "")))
                total += len(reminders)
                client.write_artifact(path, {
                    "schemaVersion": 1,
                    "product": product,
                    "reminders": reminders,
                    "updatedAt": report["completedAt"],
                })
    except OSError as exc:
        raise ValueError("kohorty nelze bezpečně zamknout nebo zapsat") from exc
    return {
        "ok": True,
        "mode": "record-execution",
        "planSha256": plan_sha,
        "products": sorted(grouped),
        "addedReminders": added,
        "totalReminders": total,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or freeze one repeat-purchase reminder GHL plan",
    )
    parser.add_argument("--state-dir", default="/documents/sales/.strategist-state")
    parser.add_argument("--cycles", help="např. 'krem=60,servis=auto'")
    parser.add_argument("--cohort-dir", default="/documents/sales/vlny")
    parser.add_argument("--output")
    parser.add_argument("--messages", help="JSON objekt se šablonou per produkt")
    parser.add_argument("--subject", default="Rychlý dotaz")
    parser.add_argument("--email-from", help="ověřená odesílací e-mailová adresa z Sales DNA §1")
    parser.add_argument("--sms", action="store_true", help="povolit SMS, pokud kontakt nemá e-mail")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--as-of", help="stabilní ISO 8601 čas výběru/plánu; při retry použij stejný")
    parser.add_argument("--window-low", type=float, default=1.2)
    parser.add_argument("--window-high", type=float, default=2.0)
    parser.add_argument("--touch-cap-days", type=int, default=30)
    parser.add_argument("--min-pairs", type=int, default=5)
    parser.add_argument("--cycle-floor-days", type=int, default=7)
    parser.add_argument("--cost-per-sms", type=float, default=1.5)
    parser.add_argument("--cost-per-email", type=float, default=0.0)
    parser.add_argument("--max-spend", type=float)
    parser.add_argument("--currency", default="CZK")
    parser.add_argument("--create-plan", action="store_true", help="zmrazí plán; nic přímo neodešle")
    parser.add_argument(
        "--record-execution",
        action="store_true",
        help="z terminálního journalu idempotentně zapíše succeeded message akce do kohort",
    )
    parser.add_argument("--confirm-plan-sha")
    parser.add_argument("--idempotency-key", help="stabilní základ klíče tohoto běhu")
    parser.add_argument("--plan-artifact", help="durable JSON artefakt plánu")
    parser.add_argument("--source-agent", default="cso")
    parser.add_argument("--task-id", type=int)
    parser.add_argument("--source-run-id")
    parser.add_argument("--credential-profile", default="default")
    parser.add_argument("--expires-at", type=int)
    parser.add_argument("--plan-revision", type=int, default=1,
                        help="změněný plán musí mít nový artefakt a idempotency key")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.record_execution:
            if args.create_plan:
                raise ValueError("--record-execution nelze kombinovat s --create-plan")
            if not args.plan_artifact or not args.confirm_plan_sha:
                raise ValueError("--record-execution vyžaduje --plan-artifact a --confirm-plan-sha")
            print(json.dumps(
                _record_execution(args.plan_artifact, args.confirm_plan_sha, args.cohort_dir),
                ensure_ascii=False,
            ))
            return 0
        if not args.cycles:
            raise ValueError("výběr kandidátů vyžaduje --cycles")
        if not 1 <= args.batch_size <= 50:
            raise ValueError("--batch-size musí být v rozsahu 1–50")
        if not (0 < args.window_low < args.window_high):
            raise ValueError("okno cyklu musí splnit 0 < window-low < window-high")
        if not 1 <= args.touch_cap_days <= 365:
            raise ValueError("--touch-cap-days musí být v rozsahu 1–365")
        if args.cost_per_sms < 0 or args.cost_per_email < 0:
            raise ValueError("odhad ceny za zprávu nesmí být záporný")
        if args.max_spend is not None and args.max_spend < 0:
            raise ValueError("--max-spend nesmí být záporný")
        if args.plan_revision <= 0:
            raise ValueError("--plan-revision musí být kladné číslo")

        contacts = load_json(os.path.join(args.state_dir, "contacts.json"))
        orders = load_json(os.path.join(args.state_dir, "orders.json"))
        opportunities = load_json(os.path.join(args.state_dir, "opportunities.json"), {})
        if not isinstance(contacts, dict) or not contacts:
            raise ValueError("snapshot kontaktů nenalezen; spusť nejdřív sales-strategist")
        if not isinstance(orders, dict) or not orders:
            raise ValueError("historie objednávek orders.json ve snapshotu není")
        if not isinstance(opportunities, dict):
            opportunities = {}

        cycles = parse_cycles(args.cycles)
        templates: dict[str, str] = {}
        if args.messages:
            try:
                parsed_templates = json.loads(args.messages)
            except ValueError as exc:
                raise ValueError("--messages není validní JSON") from exc
            if not isinstance(parsed_templates, dict):
                raise ValueError("--messages musí být JSON objekt")
            templates = {
                str(key): str(value)
                for key, value in parsed_templates.items()
                if str(value).strip()
            }
        if args.create_plan and not templates:
            raise ValueError("--create-plan vyžaduje --messages")

        now, as_of = parse_as_of(args.as_of, required=args.create_plan)
        open_contacts = {
            str(item.get("contactId"))
            for item in opportunities.values()
            if isinstance(item, dict)
            and str(item.get("status") or "").lower() == "open"
            and item.get("contactId")
        }
        tag_month = time.strftime("%Y-%m", time.gmtime(now))
        tag_day = time.strftime("%Y-%m-%d", time.gmtime(now))
        summary: list[dict[str, Any]] = []
        plans: list[dict[str, Any]] = []
        estimated_spend = 0.0
        selected_contacts: set[str] = set()
        sales_client = _sales_plan()
        segment_counter = sales_client.sms_segments

        for slug, declared in cycles.items():
            purchases = purchases_by_contact(orders, slug, merge_days=args.cycle_floor_days)
            gaps = [
                later - earlier
                for buys in purchases.values()
                for earlier, later in zip(buys, buys[1:])
                if later - earlier >= args.cycle_floor_days * DAY
            ]
            if declared == "auto":
                if len(gaps) < args.min_pairs:
                    summary.append({
                        "product": slug,
                        "skipped": f"málo dat pro auto cyklus ({len(gaps)} < {args.min_pairs})",
                    })
                    continue
                cycle_days = round((median(gaps) or 0) / DAY)
                if cycle_days < args.cycle_floor_days:
                    summary.append({"product": slug, "skipped": "auto cyklus je pod podlahou"})
                    continue
                cycle_source = "auto (medián objednávek)"
            else:
                cycle_days = int(declared)
                cycle_source = "deklarovaný Sales DNA"
            low, high = cycle_days * args.window_low, cycle_days * args.window_high

            cohort = load_cycle_cohort(Path(args.cohort_dir) / f"cyklus-{slug}.json", slug)
            reminders = cohort["reminders"]
            last_reminded: dict[str, float] = {}
            for reminder in reminders if isinstance(reminders, list) else []:
                if not isinstance(reminder, dict):
                    continue
                timestamp = iso_to_epoch(reminder.get("at"))
                contact_id = str(reminder.get("contactId") or "")
                if timestamp and contact_id and timestamp > last_reminded.get(contact_id, 0):
                    last_reminded[contact_id] = timestamp

            filtered: dict[str, int] = {}
            candidates: list[dict[str, Any]] = []

            def drop(reason: str) -> None:
                filtered[reason] = filtered.get(reason, 0) + 1

            for contact_id, buys in purchases.items():
                last_buy = buys[-1]
                days = (now - last_buy) / DAY
                if days < low:
                    continue
                if days >= high:
                    drop("nad 2× cyklu"); continue
                contact = contacts.get(contact_id)
                if not isinstance(contact, dict):
                    drop("kontakt mimo snapshot"); continue
                if contact.get("dnd"):
                    drop("dnd"); continue
                if sales_client.contact_has_local_suppression(
                    contact_id,
                    args.touch_cap_days,
                    now=datetime.fromtimestamp(now, timezone.utc),
                ):
                    drop("touch-cap (ověřená Sales zpráva)"); continue
                if not contact.get("email") and not (args.sms and contact.get("phone")):
                    drop("bez použitelného kanálu"); continue
                if contact_id in open_contacts:
                    drop("otevřený obchod"); continue
                if any(
                    (age := days_since_date(str(tag).split(":", 1)[1], now)) is not None
                    and age < args.touch_cap_days
                    for tag in (contact.get("tags") or [])
                    if str(tag).startswith("osloven:") and ":" in str(tag)
                ):
                    drop("touch-cap"); continue
                if last_reminded.get(contact_id, 0) > last_buy:
                    drop("už připomenuto v tomto cyklu"); continue
                if contact_id in selected_contacts:
                    drop("kontakt už vybrán pro jiný produkt"); continue
                candidates.append({
                    "contactId": contact_id,
                    "name": contact.get("name") or "",
                    "channel": "email" if contact.get("email") else "sms",
                    "email": contact.get("email") or "",
                    "phone": contact.get("phone") or "",
                    "lastPurchase": time.strftime("%Y-%m-%d", time.gmtime(last_buy)),
                    "daysSince": round(days),
                })
            candidates.sort(key=lambda item: -item["daysSince"])
            remaining = max(0, args.batch_size - len(selected_contacts))
            candidates = candidates[:remaining]
            selected_contacts.update(str(item["contactId"]) for item in candidates)
            template = templates.get(slug)
            rendered: list[dict[str, Any]] = []
            if args.create_plan and candidates and not template:
                raise ValueError(f"pro produkt {slug} chybí šablona v --messages")
            for candidate in candidates:
                text = personalize(template, candidate["name"]) if template else ""
                candidate_preview = {**candidate, "text": text or None}
                rendered.append(candidate_preview)
                if not template:
                    continue
                contact_id = candidate["contactId"]
                logical = f"cycle:{slug}:{candidate['lastPurchase']}:{contact_id}"
                if candidate["channel"] == "email":
                    email_from = (args.email_from or "").strip()
                    if not email_from:
                        raise ValueError(
                            "e-mailové připomínky vyžadují neprázdné --email-from z Sales DNA §1"
                        )
                    payload: dict[str, Any] = {
                        "channel": "email",
                        "contactId": contact_id,
                        "toEmail": candidate["email"],
                        "subject": args.subject,
                        "html": text_to_html(text),
                        "emailFrom": email_from,
                        "safety": {
                            "purpose": "customer_outreach",
                            "requireDndClear": True,
                            "requireChannelAddress": True,
                            "touchCapDays": args.touch_cap_days,
                            "blockOpenOpportunity": True,
                        },
                    }
                    estimated_spend += args.cost_per_email
                else:
                    payload = {
                        "channel": "sms",
                        "contactId": contact_id,
                        "toPhone": candidate["phone"],
                        "text": text,
                        "safety": {
                            "purpose": "customer_outreach",
                            "requireDndClear": True,
                            "requireChannelAddress": True,
                            "touchCapDays": args.touch_cap_days,
                            "blockOpenOpportunity": True,
                        },
                    }
                    candidate_preview["smsSegments"] = segment_counter(text)
                    estimated_spend += args.cost_per_sms * candidate_preview["smsSegments"]
                plans.append({
                    "actionType": "sales.ghl.message.send.v1",
                    "suffix": f"{logical}:message",
                    "payload": payload,
                    "detail": {
                        "kind": "cycle-reminder-message",
                        "productSlug": slug,
                        "contactId": contact_id,
                        "lastPurchase": candidate["lastPurchase"],
                    },
                })
                plans.append({
                    "actionType": "sales.ghl.tags.add.v1",
                    "suffix": f"{logical}:tags",
                    "dependsOnSuffix": f"{logical}:message",
                    "payload": {
                        "contactId": contact_id,
                        **({"contactEmail": candidate["email"]} if candidate["email"] else {}),
                        **({"contactPhone": candidate["phone"]} if candidate["phone"] else {}),
                        **({"contactName": candidate["name"]} if candidate["name"] else {}),
                        "tags": [f"cyklus:{slug}:{tag_month}", f"osloven:{tag_day}"],
                    },
                })
            summary.append({
                "product": slug,
                "cycleDays": cycle_days,
                "cycleSource": cycle_source,
                "windowDays": [round(low), round(high)],
                "candidateCount": len(candidates),
                "filtered": filtered,
                "candidates": rendered,
            })

        estimated_spend = round(estimated_spend, 2)
        result = {
            "schemaVersion": 1,
            "producer": "sales-reactivator",
            "kind": "cycle-reminders",
            "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "asOf": as_of,
            "estimatedSpend": estimated_spend,
            "maxSpend": args.max_spend,
            "currency": args.currency,
            "touchCapDays": args.touch_cap_days,
            "taskId": args.task_id,
            "products": summary,
            "aggregateExpectedSlots": sorted(str(plan["suffix"]) for plan in plans),
            "currentActions": [
                {"actionType": plan["actionType"], "payload": plan["payload"]}
                for plan in plans
            ],
        }
        if args.output:
            Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.create_plan:
            print(json.dumps({"ok": True, "mode": "preview", **result}, ensure_ascii=False, indent=2))
            return 0
        if not plans:
            raise ValueError("běh nevytvořil žádnou zprávu k potvrzení")
        if not (args.idempotency_key or "").strip():
            raise ValueError("--create-plan vyžaduje --idempotency-key")
        if not args.plan_artifact:
            raise ValueError("--create-plan vyžaduje --plan-artifact")
        if args.task_id is None or args.task_id <= 0:
            raise ValueError("--create-plan vyžaduje kladné --task-id")
        if args.max_spend is None:
            raise ValueError("--create-plan vyžaduje --max-spend")
        if estimated_spend > args.max_spend:
            raise ValueError(
                f"odhad {estimated_spend} {args.currency} překračuje limit {args.max_spend} {args.currency}"
            )
        if args.expires_at is None:
            args.expires_at = int(now) + 24 * 60 * 60
        if args.expires_at <= int(time.time()) + 60:
            raise ValueError("plán musí zůstat platný alespoň 60 sekund")
        if args.expires_at > int(time.time()) + _sales_plan().MAX_ACTION_EXPIRY_FUTURE_SECONDS:
            raise ValueError("--expires-at nesmí být více než 48 hodin v budoucnosti")

        artifact = {
            **result,
            "estimatedSpend": f"{estimated_spend:.2f}",
            "maxSpend": f"{args.max_spend:.2f}",
            "idempotencyKey": args.idempotency_key.strip(),
        }
        artifact = _freeze_plan(args, plans, artifact)
        print(json.dumps({
            "ok": True,
            **_sales_plan().plan_summary(artifact, args.plan_artifact),
            "recipientCount": len(selected_contacts),
            "estimatedSpend": f"{estimated_spend:.2f}",
            "currency": args.currency,
        }, ensure_ascii=False))
        return 0
    except (ValueError, TypeError) as exc:
        print(json.dumps({"ok": False, "code": "invalid_input", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3
    except Exception as exc:
        code = getattr(exc, "code", "plan_failed")
        print(json.dumps({"ok": False, "code": code, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
