#!/usr/bin/env python3
"""Preview or freeze one exact Upsell GHL plan.

The producer never calls GHL writes while planning. It can store the approved
e-mail envelope, render exact previews, freeze a chained send/schedule/tag
plan, and freeze explicit scheduled-message cancellations. Provider execution
is a separate exact-SHA step through the shared helper.

Creating or updating GHL custom fields is outside the active action contract.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
SKILL_DIR = SCRIPT_PATH.parents[1]
SHARED_LIB = SKILL_DIR.parent / "_lib"
SKILL_VERSION = "1.0"
OFFER_EXPECTED_SLOTS = [
    "step:e1:message",
    "step:e2:message",
    "step:e3:message",
    "step:e3:tags",
]

sys.path.insert(0, str(SKILL_DIR / "lib"))
import safe_html as _safe_html  # noqa: E402


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


def log_append(path: str, entry: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        **entry,
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _safe_href(url: str) -> str:
    return _safe_html._safe_url(url) or "#"


def wrap_email(
    config: dict[str, Any],
    greeting: str,
    body_html: str,
    cta_url: str,
    cta_label: str,
) -> str:
    greeting = _safe_html.esc(greeting or "")
    cta_label = _safe_html.esc(cta_label or "")
    cta = ""
    if cta_url and cta_label:
        cta = (
            f'<p style="margin:28px 0;"><a href="{_safe_href(cta_url)}" '
            f'style="display:inline-block;background:{config.get("accent", "#1a73e8")};'
            'color:#ffffff;text-decoration:none;font-weight:700;border-radius:10px;'
            'padding:14px 28px;font-family:Arial,Helvetica,sans-serif;">'
            f"{cta_label}</a></p>"
        )
    return f"""<!doctype html>
<html lang="cs">
  <body style="margin:0;padding:0;background:#f5f5f5;">
    <div style="max-width:600px;margin:0 auto;padding:32px 24px;background:#ffffff;
                font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.6;
                color:#333333;">
      <p style="margin:0 0 16px;">{greeting}</p>
      {body_html}
      {cta}
      <p style="margin:24px 0 0;">S pozdravem,<br />tým {_safe_html.esc(str(config['brand_name']))}</p>
      <hr style="border:none;border-top:1px solid #e3e6ea;margin:28px 0 16px;" />
      <p style="margin:0;font-size:13px;color:#666666;">{config['footer_html']}</p>
    </div>
  </body>
</html>"""


def add_action_plans(
    args: argparse.Namespace,
    plans: list[dict[str, Any]],
    artifact: dict[str, Any],
    *,
    task_contract: str,
    frozen_expected_slots: list[str],
    finalize: bool,
) -> dict[str, Any]:
    client = _sales_plan()
    journal = client.SalesGhlPlan(
        args.plan_artifact,
        producer="sales-upsell",
        skill_version=SKILL_VERSION,
        task_id=args.task_id,
        task_contract=task_contract,
        idempotency_key=args.idempotency_key.strip(),
        revision=args.plan_revision,
        source_agent=args.source_agent,
        source_run_id=args.source_run_id,
        metadata=artifact,
    )
    if journal.value["metadata"].get("aggregateExpectedSlots") != frozen_expected_slots:
        raise RuntimeError("aggregateExpectedSlots se mezi běhy změnily")
    for plan in plans:
        parent_slot = str(plan.get("dependsOnSuffix") or "").strip()
        depends_on_action_id = (
            str(plan.get("dependsOnActionId") or "").strip()
            or (journal.action_id_for_slot(parent_slot) if parent_slot else "")
        )
        if (parent_slot or plan.get("dependsOnActionId")) and not depends_on_action_id:
            raise RuntimeError("chybí parent action ID pro závislou akci")
        journal.add_action(
            slot=plan["suffix"],
            action_type=plan["actionType"],
            payload=plan["payload"],
            depends_on_action_id=depends_on_action_id or None,
            source_run_id=args.source_run_id,
            credential_profile=args.credential_profile,
            expires_at=args.expires_at,
        )
    return journal.finish(frozen_expected_slots) if finalize else journal.value


def _validate_setup(args: argparse.Namespace) -> dict[str, Any]:
    email_from = (args.email_from or "").strip()
    if not args.brand_name or not args.footer or not email_from:
        raise ValueError("--setup vyžaduje --brand-name, --footer a neprázdné --email-from")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", args.accent or ""):
        raise ValueError("--accent musí být hex barva ve tvaru #1a73e8")
    config = {
        "brand_name": args.brand_name,
        "footer_html": args.footer,
        "accent": args.accent,
        "email_from": email_from,
    }
    return config


def do_setup(args: argparse.Namespace) -> int:
    config = _validate_setup(args)
    state_dir = Path(args.state_dir)
    client = _sales_plan()
    client.write_artifact(str(state_dir / "config.json"), config)
    print(json.dumps({
        "ok": True,
        "mode": "email-envelope-setup",
        "note": "uložena je pouze schválená e-mailová obálka; custom-field writes jsou vypnuté",
        "stateDir": str(state_dir),
    }, ensure_ascii=False))
    return 0


def _parse_scheduled_at(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("--scheduled-at musí být ISO 8601 datum s časovým pásmem") from exc
    if parsed.tzinfo is None:
        raise ValueError("--scheduled-at musí obsahovat časové pásmo")
    return parsed.isoformat()


def build_offer_action_plans(
    args: argparse.Namespace,
    *,
    html: str,
    scheduled_at: str | None,
    contact_identity: dict[str, str],
    email_from: str,
    plan_date: str,
) -> list[dict[str, Any]]:
    message_payload: dict[str, Any] = {
        "channel": "email",
        "contactId": args.contact,
        "toEmail": args.to_email,
        "subject": args.subject,
        "html": html,
        "emailFrom": email_from,
        "safety": {
            "purpose": "customer_outreach",
            "requireDndClear": True,
            "requireChannelAddress": True,
            "touchCapDays": args.touch_cap_days,
            "blockOpenOpportunity": True,
        },
    }
    action_type = "sales.ghl.message.send.v1"
    if scheduled_at:
        action_type = "sales.ghl.message.schedule.v1"
        message_payload["scheduledAt"] = scheduled_at
    message_suffix = f"step:{args.step}:message"
    plans: list[dict[str, Any]] = [{
        "actionType": action_type,
        "suffix": message_suffix,
        **(
            {"dependsOnSuffix": "step:e1:message"}
            if args.step == "e2"
            else {"dependsOnSuffix": "step:e2:message"}
            if args.step == "e3"
            else {}
        ),
        "payload": message_payload,
    }]
    if args.step == "e3":
        plans.append({
            "actionType": "sales.ghl.tags.add.v1",
            "suffix": "step:e3:tags",
            "dependsOnSuffix": message_suffix,
            "payload": {
                **contact_identity,
                "tags": [f"upsell-sent:{plan_date}", f"osloven:{plan_date}"],
            },
        })
    return plans


def _load_guard_candidates(path: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"guard input nelze načíst: {exc}") from exc
    if isinstance(parsed, dict):
        parsed = parsed.get("cancellations")
    if not isinstance(parsed, list):
        raise ValueError("guard input musí být pole nebo objekt s polem cancellations")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in parsed:
        if not isinstance(item, dict):
            raise ValueError("každý guard kandidát musí být objekt")
        message_id = str(item.get("messageId") or "").strip()
        channel = str(item.get("channel") or "email").strip().lower()
        email_message_id = str(item.get("emailMessageId") or "").strip()
        reason = str(item.get("reason") or "").strip()
        source_plan_sha = str(item.get("sourcePlanSha256") or "").strip()
        source_action_id = str(item.get("sourceActionId") or "").strip()
        if not message_id or channel not in {"email", "sms"} or not reason:
            raise ValueError(
                "guard kandidát vyžaduje messageId, channel=email|sms a reason"
            )
        if channel == "email" and not email_message_id:
            raise ValueError("e-mailový guard kandidát vyžaduje také emailMessageId z provider receipt")
        if channel == "sms" and email_message_id:
            raise ValueError("SMS guard kandidát nesmí obsahovat emailMessageId")
        if source_plan_sha and not re.fullmatch(r"[a-f0-9]{64}", source_plan_sha):
            raise ValueError("sourcePlanSha256 musí být přesné SHA-256")
        if bool(source_plan_sha) != bool(source_action_id):
            raise ValueError("sourcePlanSha256 a sourceActionId se uvádějí společně")
        if message_id in seen:
            continue
        seen.add(message_id)
        result.append({
            **item,
            "messageId": message_id,
            "channel": channel,
            "reason": reason,
            **({"emailMessageId": email_message_id} if email_message_id else {}),
            **({"sourcePlanSha256": source_plan_sha, "sourceActionId": source_action_id}
               if source_plan_sha else {}),
        })
    return result


def do_guard(args: argparse.Namespace) -> int:
    if not args.guard_input:
        raise ValueError(
            "--guard už nesmí číst ani měnit GHL přímo; vyžaduje --guard-input s "
            "operátorem/CC ověřenými messageId a důvody zrušení"
        )
    candidates = _load_guard_candidates(args.guard_input)
    plans = [{
        "actionType": "sales.ghl.scheduled-message.cancel.v1",
        "suffix": f"cancel:{item['messageId']}",
        "payload": {
            "messageId": item["messageId"],
            "channel": item["channel"],
            **({"emailMessageId": item["emailMessageId"]} if item["channel"] == "email" else {}),
        },
    } for item in candidates]
    preview = {
        "schemaVersion": 1,
        "producer": "sales-upsell",
        "kind": "scheduled-message-cancellations",
        "taskId": args.task_id,
        "aggregateExpectedSlots": [plan["suffix"] for plan in plans],
        "candidates": candidates,
        "actions": [
            {"actionType": plan["actionType"], "payload": plan["payload"]}
            for plan in plans
        ],
    }
    if not args.create_plan:
        print(json.dumps({"ok": True, "mode": "preview", **preview}, ensure_ascii=False, indent=2))
        return 0
    _require_plan_args(args)
    if len(candidates) != 1:
        raise ValueError("cancellation plán vyžaduje právě jeden messageId")
    artifact = add_action_plans(
        args,
        plans,
        {**preview, "idempotencyKey": args.idempotency_key.strip()},
        task_contract="sales-upsell:scheduled-cancellation",
        frozen_expected_slots=[plans[0]["suffix"]],
        finalize=True,
    )
    print(json.dumps({
        "ok": True,
        **_sales_plan().plan_summary(artifact, args.plan_artifact),
    }, ensure_ascii=False))
    return 0


def _require_plan_args(args: argparse.Namespace) -> None:
    if not (args.idempotency_key or "").strip():
        raise ValueError("--create-plan vyžaduje --idempotency-key")
    if not args.plan_artifact:
        raise ValueError("--create-plan vyžaduje --plan-artifact")
    if args.task_id is None or args.task_id <= 0:
        raise ValueError("--create-plan vyžaduje kladné --task-id")
    if args.plan_revision <= 0:
        raise ValueError("--plan-revision musí být kladné číslo")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or freeze one exact Sales Upsell GHL plan",
    )
    parser.add_argument("--state-dir", default="/documents/sales/.upsell-state")
    parser.add_argument("--log", default="/documents/sales/upsell-log.jsonl")
    parser.add_argument("--setup", action="store_true", help="uloží schválenou e-mailovou obálku")
    parser.add_argument("--brand-name")
    parser.add_argument("--footer")
    parser.add_argument("--email-from", help="ověřená odesílací e-mailová adresa uložená při --setup")
    parser.add_argument("--accent", default="#1a73e8")
    parser.add_argument("--guard", action="store_true")
    parser.add_argument("--guard-input", help="JSON se CC/operátorem ověřenými cancellation kandidáty")
    parser.add_argument("--contact")
    parser.add_argument("--to-email", help="přesná schvalovaná e-mailová adresa kontaktu")
    parser.add_argument("--step", choices=["e1", "e2", "e3"], default="e1")
    parser.add_argument("--subject")
    parser.add_argument("--body-file")
    parser.add_argument("--greeting", default="Dobrý den,")
    parser.add_argument("--cta-url", default="")
    parser.add_argument("--cta-label", default="")
    parser.add_argument("--product-name")
    parser.add_argument("--reason")
    parser.add_argument("--slug")
    parser.add_argument("--scheduled-at", help="exact ISO 8601 čas pro naplánovanou akci")
    parser.add_argument("--plan-date", help="stabilní YYYY-MM-DD pro celý E1–E3 plán")
    parser.add_argument("--delay-days", type=float, default=0, help="jen pro preview; plán vyžaduje --scheduled-at")
    parser.add_argument("--block", action="store_true")
    parser.add_argument("--verdict", help="judge verdict; musí být APPROVE")
    parser.add_argument("--cost-per-email", type=float, default=0.0)
    parser.add_argument("--max-spend", type=float)
    parser.add_argument("--currency", default="CZK")
    parser.add_argument("--touch-cap-days", type=int, default=14, help="exact mantinel ze Sales DNA")
    parser.add_argument("--dry-run", action="store_true", help="kompatibilní alias preview režimu")
    parser.add_argument("--create-plan", action="store_true", help="vytvoří nebo dokončí plán; nic přímo neprovede")
    parser.add_argument("--idempotency-key", help="stabilní klíč konkrétní nákupní sekvence")
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
        if args.setup:
            return do_setup(args)
        if args.guard:
            return do_guard(args)
        if not args.contact:
            raise ValueError("chybí --contact")
        if args.block:
            log_append(args.log, {
                "producer": "sales-upsell",
                "action": "block",
                "contactId": args.contact,
                "step": args.step,
                "slug": args.slug or "",
                "note": args.reason or "",
            })
            print(json.dumps({"ok": True, "blocked": True}, ensure_ascii=False))
            return 0
        if args.cost_per_email < 0:
            raise ValueError("--cost-per-email nesmí být záporný")
        if not 1 <= args.touch_cap_days <= 365:
            raise ValueError("--touch-cap-days musí být v rozsahu 1–365")
        if _sales_plan().contact_has_local_suppression(args.contact, args.touch_cap_days):
            raise ValueError("kontakt má uvnitř touch-capu ověřenou dřívější Sales zprávu")
        if args.max_spend is not None and args.max_spend < 0:
            raise ValueError("--max-spend nesmí být záporný")
        if args.plan_revision <= 0:
            raise ValueError("--plan-revision musí být kladné číslo")
        required = {
            "--to-email": args.to_email,
            "--subject": args.subject,
            "--body-file": args.body_file,
            "--product-name": args.product_name,
            "--reason": args.reason,
            "--slug": args.slug,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"nabídka vyžaduje {', '.join(missing)}")
        if args.verdict != "APPROVE":
            raise ValueError("judge verdict musí být explicitně APPROVE")

        config = load_json(os.path.join(args.state_dir, "config.json"))
        email_from = str(config.get("email_from") or "").strip() if isinstance(config, dict) else ""
        if (
            not isinstance(config, dict)
            or not config.get("brand_name")
            or not config.get("footer_html")
            or not email_from
        ):
            raise ValueError(
                "chybí úplný config.json; operátor musí zopakovat --setup včetně --email-from"
            )
        try:
            body_html = Path(args.body_file).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ValueError(f"tělo e-mailu nelze načíst: {exc}") from exc
        if not body_html:
            raise ValueError("tělo e-mailu je prázdné")

        scheduled_at = _parse_scheduled_at(args.scheduled_at)
        plan_date = (args.plan_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")).strip()
        try:
            plan_day = datetime.strptime(plan_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise ValueError("--plan-date musí být YYYY-MM-DD")
        if args.create_plan and not args.plan_date:
            raise ValueError("--create-plan vyžaduje stabilní --plan-date pro celý E1–E3 plán")
        if args.create_plan and plan_day.date() != datetime.now(timezone.utc).date():
            raise ValueError("--plan-date musí být dnešní datum v UTC")
        if args.create_plan and args.expires_at is None:
            args.expires_at = int(plan_day.timestamp()) + 48 * 60 * 60
        if args.create_plan and args.expires_at <= int(time.time()) + 60:
            raise ValueError("plán musí zůstat platný alespoň 60 sekund")
        if (
            args.create_plan
            and args.expires_at > int(time.time()) + _sales_plan().MAX_ACTION_EXPIRY_FUTURE_SECONDS
        ):
            raise ValueError("--expires-at nesmí být více než 48 hodin v budoucnosti")
        if not scheduled_at and args.delay_days > 0:
            if args.create_plan:
                raise ValueError(
                    "relativní --delay-days není immutable; pro plán použij exact --scheduled-at"
                )
            scheduled_at = (
                datetime.now(timezone.utc) + timedelta(days=args.delay_days)
            ).isoformat()
        if args.create_plan and args.step in {"e2", "e3"} and not scheduled_at:
            raise ValueError(f"krok {args.step} vyžaduje exact --scheduled-at")

        html = wrap_email(config, args.greeting, body_html, args.cta_url, args.cta_label)
        plans = build_offer_action_plans(
            args,
            html=html,
            scheduled_at=scheduled_at,
            contact_identity={"contactId": args.contact, "contactEmail": args.to_email},
            email_from=email_from,
            plan_date=plan_date,
        )
        preview = {
            "schemaVersion": 1,
            "producer": "sales-upsell",
            "kind": "offer-step",
            "contactId": args.contact,
            "step": args.step,
            "slug": args.slug,
            "product": args.product_name,
            "reason": args.reason,
            "subject": args.subject,
            "scheduledAt": scheduled_at,
            "estimatedSpend": args.cost_per_email,
            "maxSpend": args.max_spend,
            "currency": args.currency,
            "touchCapDays": args.touch_cap_days,
            "taskId": args.task_id,
            "htmlChars": len(html),
            "aggregateExpectedSlots": OFFER_EXPECTED_SLOTS,
            "currentActions": [
                {"actionType": plan["actionType"], "payload": plan["payload"]}
                for plan in plans
            ],
        }
        if not args.create_plan:
            print(json.dumps({"ok": True, "mode": "preview", **preview}, ensure_ascii=False, indent=2))
            return 0
        _require_plan_args(args)
        exact_identity = _sales_plan().lookup_contact_snapshot(
            contact_id=args.contact,
            email=args.to_email,
            profile=args.credential_profile,
        )
        plans = build_offer_action_plans(
            args,
            html=html,
            scheduled_at=scheduled_at,
            contact_identity=exact_identity,
            email_from=email_from,
            plan_date=plan_date,
        )
        if args.max_spend is None:
            raise ValueError("--create-plan vyžaduje --max-spend")
        total_estimated_spend = round(args.cost_per_email * 3, 2)
        if total_estimated_spend > args.max_spend:
            raise ValueError(
                f"odhad celé tříkrokové sekvence {total_estimated_spend} {args.currency} překračuje limit "
                f"{args.max_spend} {args.currency}"
            )
        plan_metadata = {
            "kind": "offer-sequence",
            "contactId": args.contact,
            "slug": args.slug,
            "product": args.product_name,
            "reason": args.reason,
            "estimatedSpend": f"{total_estimated_spend:.2f}",
            "maxSpend": f"{args.max_spend:.2f}",
            "costPerEmail": f"{args.cost_per_email:.2f}",
            "currency": args.currency,
            "touchCapDays": args.touch_cap_days,
            "planDate": plan_date,
            "aggregateExpectedSlots": OFFER_EXPECTED_SLOTS,
        }
        artifact = add_action_plans(
            args,
            plans,
            plan_metadata,
            task_contract="sales-upsell:offer-sequence",
            frozen_expected_slots=OFFER_EXPECTED_SLOTS,
            finalize=args.step == "e3",
        )
        log_append(args.log, {
            "producer": "sales-upsell",
            "action": "plan-updated",
            "contactId": args.contact,
            "step": args.step,
            "slug": args.slug,
            "planArtifact": args.plan_artifact,
            "planSha256": artifact.get("planSha256"),
            "planActionIds": [record["actionId"] for record in artifact["actions"]],
        })
        print(json.dumps({
            "ok": True,
            **_sales_plan().plan_summary(artifact, args.plan_artifact),
            "step": args.step,
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
