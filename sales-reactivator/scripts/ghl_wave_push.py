#!/usr/bin/env python3
"""Preview or freeze one bounded Sales Reactivator wave batch.

The default is an exact local batch preview. ``--create-plan`` freezes the
current batch, including every immutable message and dependent additive-tag
action in that batch. It performs no provider write. The completed batch plan
is executed only by the shared helper with its exact SHA-256 and explicit
confirmation.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from html import escape as html_escape
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
SKILL_DIR = SCRIPT_PATH.parents[1]
SHARED_LIB = SKILL_DIR.parent / "_lib"
SKILL_VERSION = "1.0"
MAX_AS_OF_PAST_SECONDS = 60 * 60
MAX_AS_OF_FUTURE_SECONDS = 5 * 60


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


def personalize(template: str, name: str | None) -> str:
    """Replace ``{jmeno}`` with the first name and clean an empty salutation."""
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


def build_wave_action_plans(
    wave: dict[str, Any],
    *,
    message_a: str,
    message_b: str | None,
    subject: str,
    email_only: bool,
    batch_offset: int,
    batch_size: int,
    touch_cap_days: int,
    quarantine_months: int,
    email_from: str | None,
    requested_at: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Materialize exact per-recipient payloads; no provider lookup happens here."""
    templates = {"a": message_a, "b": message_b or message_a}
    contacts = wave.get("contacts")
    if not isinstance(contacts, list):
        raise ValueError("soubor vlny nemá pole contacts")
    selected = contacts[batch_offset:batch_offset + batch_size]
    tag_month = time.strftime("%Y-%m", time.gmtime(requested_at))
    tag_day = time.strftime("%Y-%m-%d", time.gmtime(requested_at))
    slug = str(wave.get("slug") or "").strip()
    if not slug:
        raise ValueError("soubor vlny nemá slug")

    plans: list[dict[str, Any]] = []
    recipients: list[dict[str, Any]] = []
    skipped = {"duplicate": 0, "no_channel": 0, "invalid": 0}
    seen: set[str] = set()
    for contact in selected:
        if not isinstance(contact, dict):
            skipped["invalid"] += 1
            continue
        contact_id = str(contact.get("contactId") or "").strip()
        if not contact_id:
            skipped["invalid"] += 1
            continue
        if contact_id in seen:
            skipped["duplicate"] += 1
            continue
        seen.add(contact_id)
        variant = str(contact.get("variant") or "a").strip().lower()
        if variant not in templates:
            raise ValueError(f"kontakt {contact_id} má neplatnou variantu {variant!r}")
        text = personalize(templates[variant], str(contact.get("name") or ""))
        if not text:
            raise ValueError(f"kontakt {contact_id} má prázdný výsledný text")

        if not email_only and contact.get("phone"):
            channel = "sms"
            message_payload: dict[str, Any] = {
                "channel": "sms",
                "contactId": contact_id,
                "toPhone": str(contact["phone"]),
                "text": text,
                "safety": {
                    "purpose": "customer_outreach",
                    "requireDndClear": True,
                    "requireChannelAddress": True,
                    "touchCapDays": touch_cap_days,
                    "blockOpenOpportunity": True,
                    "quarantineMonths": quarantine_months,
                    "quarantineTagPrefix": "reaktivace:",
                },
            }
        elif contact.get("email"):
            sender = (email_from or "").strip()
            if not sender:
                raise ValueError("e-mailová vlna vyžaduje neprázdné --email-from z Sales DNA §1")
            channel = "email"
            message_payload = {
                "channel": "email",
                "contactId": contact_id,
                "toEmail": str(contact["email"]),
                "subject": subject,
                "html": text_to_html(text),
                "emailFrom": sender,
                "safety": {
                    "purpose": "customer_outreach",
                    "requireDndClear": True,
                    "requireChannelAddress": True,
                    "touchCapDays": touch_cap_days,
                    "blockOpenOpportunity": True,
                    "quarantineMonths": quarantine_months,
                    "quarantineTagPrefix": "reaktivace:",
                },
            }
        else:
            skipped["no_channel"] += 1
            continue

        message_suffix = f"recipient:{contact_id}:message"
        tag_suffix = f"recipient:{contact_id}:tags"
        contact_identity: dict[str, Any] = {"contactId": contact_id}
        if str(contact.get("email") or "").strip():
            contact_identity["contactEmail"] = str(contact["email"]).strip()
        if str(contact.get("phone") or "").strip():
            contact_identity["contactPhone"] = str(contact["phone"]).strip()
        if str(contact.get("name") or "").strip():
            contact_identity["contactName"] = str(contact["name"]).strip()
        plans.append({
            "actionType": "sales.ghl.message.send.v1",
            "suffix": message_suffix,
            "payload": message_payload,
        })
        plans.append({
            "actionType": "sales.ghl.tags.add.v1",
            "suffix": tag_suffix,
            "dependsOnSuffix": message_suffix,
            "payload": {
                **contact_identity,
                "tags": [
                    f"reaktivace:{tag_month}",
                    f"vlna:{slug}:{variant}",
                    f"osloven:{tag_day}",
                ],
            },
        })
        recipients.append({
            "contactId": contact_id,
            "name": contact.get("name") or "",
            "segment": contact.get("segment") or "",
            "variant": variant,
            "channel": channel,
            "text": text,
        })
    return plans, recipients, skipped


def freeze_action_plan(
    args: argparse.Namespace,
    plans: list[dict[str, Any]],
    metadata: dict[str, Any],
    *,
    frozen_expected_slots: list[str],
) -> dict[str, Any]:
    client = _sales_plan()
    journal = client.SalesGhlPlan(
        args.plan_artifact,
        producer="sales-reactivator",
        skill_version=SKILL_VERSION,
        task_id=args.task_id,
        task_contract="sales-reactivator:wave-actions",
        idempotency_key=args.idempotency_key.strip(),
        revision=args.plan_revision,
        source_agent=args.source_agent,
        source_run_id=args.source_run_id,
        metadata=metadata,
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
        )
    return journal.finish(frozen_expected_slots)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or freeze one exact reactivation-wave GHL plan",
    )
    parser.add_argument("--wave", required=True, help="soubor vlny z reactivation_candidates.py")
    parser.add_argument("--campaign", default="vlna")
    parser.add_argument("--message-a", required=True, help="znění A; podporuje {jmeno}")
    parser.add_argument("--message-b", help="znění B; bez něj se použije A")
    parser.add_argument("--subject", default="Rychlý dotaz")
    parser.add_argument("--email-from", help="ověřená odesílací e-mailová adresa z Sales DNA §1")
    parser.add_argument("--email-only", action="store_true")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--batch-offset", type=int, default=0)
    parser.add_argument("--as-of", help="stabilní ISO 8601 čas výběru/plánu; při retry použij stejný")
    parser.add_argument("--touch-cap-days", type=int, default=14, help="exact mantinel ze Sales DNA")
    parser.add_argument("--quarantine-months", type=int, default=6,
                        help="exact karanténa ze Sales DNA; live revaliduje platforma")
    parser.add_argument("--cost-per-sms", type=float, default=1.5)
    parser.add_argument("--cost-per-email", type=float, default=0.0)
    parser.add_argument("--max-spend", type=float)
    parser.add_argument("--currency", default="CZK")
    parser.add_argument("--create-plan", action="store_true", help="zmrazí plán aktuální dávky; nic neodešle")
    parser.add_argument("--idempotency-key", help="stabilní základ klíče celé vlny")
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
        if not 1 <= args.batch_size <= 50 or args.batch_offset < 0:
            raise ValueError("batch-size musí být 1–50 a batch-offset nezáporný")
        if not 1 <= args.touch_cap_days <= 365:
            raise ValueError("--touch-cap-days musí být v rozsahu 1–365")
        if not 1 <= args.quarantine_months <= 120:
            raise ValueError("--quarantine-months musí být v rozsahu 1–120")
        if args.cost_per_sms < 0 or args.cost_per_email < 0:
            raise ValueError("odhad ceny za zprávu nesmí být záporný")
        if args.max_spend is not None and args.max_spend < 0:
            raise ValueError("--max-spend nesmí být záporný")
        if args.plan_revision <= 0:
            raise ValueError("--plan-revision musí být kladné číslo")

        try:
            wave = json.loads(Path(args.wave).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"soubor vlny nelze načíst: {exc}") from exc
        if not isinstance(wave, dict):
            raise ValueError("soubor vlny musí být JSON objekt")

        requested_at, as_of = parse_as_of(args.as_of, required=args.create_plan)
        plans, recipients, skipped = build_wave_action_plans(
            wave,
            message_a=args.message_a,
            message_b=args.message_b,
            subject=args.subject,
            email_only=args.email_only,
            batch_offset=args.batch_offset,
            batch_size=args.batch_size,
            touch_cap_days=args.touch_cap_days,
            quarantine_months=args.quarantine_months,
            email_from=args.email_from,
            requested_at=requested_at,
        )
        all_contacts = wave.get("contacts")
        assert isinstance(all_contacts, list)
        all_plans, all_recipients, _all_skipped = build_wave_action_plans(
            wave,
            message_a=args.message_a,
            message_b=args.message_b,
            subject=args.subject,
            email_only=args.email_only,
            batch_offset=0,
            batch_size=max(1, len(all_contacts)),
            touch_cap_days=args.touch_cap_days,
            quarantine_months=args.quarantine_months,
            email_from=args.email_from,
            requested_at=requested_at,
        )
        segment_counter = _sales_plan().sms_segments
        for recipient in [*recipients, *all_recipients]:
            if recipient["channel"] == "sms":
                recipient["smsSegments"] = segment_counter(recipient["text"])
        batch_estimated = round(sum(
            args.cost_per_sms * int(item.get("smsSegments") or 1)
            if item["channel"] == "sms"
            else args.cost_per_email
            for item in recipients
        ), 2)
        whole_wave_estimated = round(sum(
            args.cost_per_sms * int(item.get("smsSegments") or 1)
            if item["channel"] == "sms"
            else args.cost_per_email
            for item in all_recipients
        ), 2)
        preview = {
            "schemaVersion": 1,
            "producer": "sales-reactivator",
            "kind": "wave",
            "campaign": args.campaign,
            "waveSlug": wave.get("slug"),
            "batchOffset": args.batch_offset,
            "batchSize": args.batch_size,
            "touchCapDays": args.touch_cap_days,
            "quarantineMonths": args.quarantine_months,
            "taskId": args.task_id,
            "recipientCount": len(recipients),
            "waveRecipientCount": len(all_recipients),
            "batchEstimatedSpend": batch_estimated,
            "estimatedSpend": batch_estimated,
            "wholeWaveEstimatedSpend": whole_wave_estimated,
            "maxSpend": args.max_spend,
            "costPerSms": f"{args.cost_per_sms:.2f}",
            "costPerEmail": f"{args.cost_per_email:.2f}",
            "currency": args.currency,
            "recipients": recipients,
            "skipped": skipped,
            "expectedSlotCount": len(plans),
            "waveExpectedSlotCount": len(all_plans),
            "currentActions": [
                {"actionType": plan["actionType"], "payload": plan["payload"]}
                for plan in plans
            ],
        }
        if not args.create_plan:
            print(json.dumps({"ok": True, "mode": "preview", **preview}, ensure_ascii=False, indent=2))
            return 0
        if not recipients:
            raise ValueError("vybraná dávka nemá žádného příjemce s použitelným kanálem")
        if not (args.idempotency_key or "").strip():
            raise ValueError("--create-plan vyžaduje --idempotency-key")
        if not args.plan_artifact:
            raise ValueError("--create-plan vyžaduje --plan-artifact")
        if args.task_id is None or args.task_id <= 0:
            raise ValueError("--create-plan vyžaduje kladné --task-id")
        if args.max_spend is None:
            raise ValueError("--create-plan vyžaduje --max-spend")
        if batch_estimated > args.max_spend:
            raise ValueError(
                f"odhad dávky {batch_estimated} {args.currency} "
                f"překračuje limit {args.max_spend} {args.currency}"
            )
        if args.expires_at is None:
            args.expires_at = int(requested_at) + 24 * 60 * 60
        if args.expires_at <= int(time.time()) + 60:
            raise ValueError("plán musí zůstat platný alespoň 60 sekund")
        if args.expires_at > int(time.time()) + _sales_plan().MAX_ACTION_EXPIRY_FUTURE_SECONDS:
            raise ValueError("--expires-at nesmí být více než 48 hodin v budoucnosti")

        metadata = {
            "kind": "wave-batch",
            "campaign": args.campaign,
            "waveSlug": wave.get("slug"),
            "batchOffset": args.batch_offset,
            "batchSize": args.batch_size,
            "touchCapDays": args.touch_cap_days,
            "quarantineMonths": args.quarantine_months,
            "recipientCount": len(recipients),
            "waveRecipientCount": len(all_recipients),
            "estimatedSpend": f"{batch_estimated:.2f}",
            "wholeWaveEstimatedSpend": f"{whole_wave_estimated:.2f}",
            "maxSpend": f"{args.max_spend:.2f}",
            "costPerSms": f"{args.cost_per_sms:.2f}",
            "costPerEmail": f"{args.cost_per_email:.2f}",
            "currency": args.currency,
            "aggregateExpectedSlots": sorted(str(plan["suffix"]) for plan in plans),
            "asOf": as_of,
        }
        artifact = freeze_action_plan(
            args,
            plans,
            metadata,
            frozen_expected_slots=metadata["aggregateExpectedSlots"],
        )
        print(json.dumps({
            "ok": True,
            **_sales_plan().plan_summary(artifact, args.plan_artifact),
            "batchOffset": args.batch_offset,
            "recipientCount": len(recipients),
            "estimatedSpend": f"{batch_estimated:.2f}",
            "currency": args.currency,
        }, ensure_ascii=False))
        return 0
    except ValueError as exc:
        print(json.dumps({"ok": False, "code": "invalid_input", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3
    except Exception as exc:
        code = getattr(exc, "code", "plan_failed")
        print(json.dumps({"ok": False, "code": code, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
