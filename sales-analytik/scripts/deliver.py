#!/usr/bin/env python3
"""Preview or freeze a Sales Analytik report e-mail plan.

Analytik has no CRM note/tag capability and no provider credential or HTTP
surface. Its durable local report remains the primary output; this helper can
only add one typed e-mail action for an exact existing contact ID. Provider
execution is a separate exact-SHA step through the shared Sales GHL helper.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
SKILL_DIR = SCRIPT_PATH.parents[1]
SHARED_LIB = SKILL_DIR.parent / "_lib"
SKILL_VERSION = "1.0"
INTERNAL_REPORT_SAFETY = {
    "purpose": "internal_report",
    "requireDndClear": True,
    "requireChannelAddress": True,
    "touchCapDays": 0,
    "blockOpenOpportunity": False,
}

sys.path.insert(0, str(SKILL_DIR / "lib"))
from safe_html import render as _safe_render  # noqa: E402


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


def _body(args: argparse.Namespace) -> str:
    if args.body_file:
        try:
            value = Path(args.body_file).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"soubor nelze načíst: {exc}") from exc
    else:
        value = args.body or ""
    if not value.strip():
        raise ValueError("chybí --body-file nebo --body")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview or freeze a Sales Analytik report e-mail plan")
    commands = parser.add_subparsers(dest="mode", required=True)
    email = commands.add_parser("email", help="request one report email")
    email.add_argument("--to-contact-id", required=True)
    email.add_argument("--to-email", required=True, help="přesná schvalovaná adresa příjemce")
    email.add_argument("--subject", required=True)
    email.add_argument("--body-file")
    email.add_argument("--body")
    email.add_argument("--email-from", help="ověřená odesílací e-mailová adresa z Sales DNA §1")
    email.add_argument("--create-plan", action="store_true", help="vytvoří plán; nic neodešle")
    email.add_argument("--idempotency-key", help="stabilní klíč tohoto plánu")
    email.add_argument("--plan-artifact", help="kanonický JSON zmrazeného plánu")
    email.add_argument("--plan-slot", help="stabilní slot příjemce uvnitř aggregate plánu")
    email.add_argument("--complete-plan", action="store_true",
                       help="zmrazí aggregate plán; použij jen na posledním příjemci")
    email.add_argument("--expected-slot", action="append", default=[],
                       help="úplný frozen slot set aggregate artefaktu; opakuj pro každý slot")
    email.add_argument("--source-agent", default="cso")
    email.add_argument("--task-id", type=int, help="povinné kladné ID existujícího CC tasku pro --create-plan")
    email.add_argument("--source-run-id")
    email.add_argument("--credential-profile", default="default")
    email.add_argument("--expires-at", type=int)
    email.add_argument(
        "--plan-revision",
        type=int,
        default=1,
        help="verze nového plánu; změna vyžaduje nový artefakt a idempotency key",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        email_from = (args.email_from or "").strip()
        if not email_from:
            raise ValueError("email request vyžaduje neprázdné --email-from z Sales DNA §1")
        payload: dict[str, Any] = {
            "channel": "email",
            "contactId": args.to_contact_id,
            "toEmail": args.to_email,
            "subject": args.subject,
            "html": _safe_render(_body(args), tables=False),
            "emailFrom": email_from,
            "safety": INTERNAL_REPORT_SAFETY,
        }
        preview = {
            "ok": True,
            "mode": "preview",
            "producer": "sales-analytik",
            "currentActions": [{"actionType": "sales.ghl.message.send.v1", "payload": payload}],
        }
        if not args.create_plan:
            print(json.dumps(preview, ensure_ascii=False, indent=2))
            return 0
        if args.task_id is None or args.task_id <= 0:
            raise ValueError("--create-plan vyžaduje kladné --task-id existujícího CC tasku")
        key = (args.idempotency_key or "").strip()
        if not key:
            raise ValueError("--create-plan vyžaduje --idempotency-key")
        if not args.plan_artifact:
            raise ValueError("--create-plan vyžaduje --plan-artifact")
        if args.plan_revision <= 0:
            raise ValueError("--plan-revision musí být kladné číslo")
        if args.plan_slot and not args.expected_slot:
            raise ValueError("--plan-slot vyžaduje úplný frozen opakovaný --expected-slot")
        if len(args.expected_slot) != len(set(args.expected_slot)):
            raise ValueError("--expected-slot se nesmí opakovat")
        frozen_expected_slots = sorted(args.expected_slot)
        own_slot = args.plan_slot or "email"
        if args.plan_slot and own_slot not in set(frozen_expected_slots):
            raise ValueError("--expected-slot neobsahuje slot posledního příjemce")

        client = _sales_plan()
        client.lookup_contact_snapshot(
            contact_id=args.to_contact_id,
            email=args.to_email,
            profile=args.credential_profile,
        )
        journal = client.SalesGhlPlan(
            args.plan_artifact,
            producer="sales-analytik",
            skill_version=SKILL_VERSION,
            task_id=args.task_id,
            task_contract="sales-analytik:weekly-report",
            idempotency_key=key,
            revision=args.plan_revision,
            source_agent=args.source_agent,
            source_run_id=args.source_run_id,
            metadata={
                "delivery": "email",
                **({"aggregateExpectedSlots": frozen_expected_slots} if args.plan_slot else {}),
            },
        )
        if args.plan_slot and journal.value["metadata"].get("aggregateExpectedSlots") != frozen_expected_slots:
            raise ValueError("aggregateExpectedSlots se mezi příjemci změnily")
        journal.add_action(
            slot=args.plan_slot or "email",
            action_type="sales.ghl.message.send.v1",
            payload=payload,
            source_run_id=args.source_run_id,
            credential_profile=args.credential_profile,
            expires_at=args.expires_at,
        )
        expected_slots = frozen_expected_slots if args.plan_slot else [own_slot]
        artifact = (
            journal.finish(expected_slots)
            if not args.plan_slot or args.complete_plan
            else journal.value
        )
        print(json.dumps({
            "ok": True,
            **client.plan_summary(artifact, args.plan_artifact),
        }, ensure_ascii=False))
        return 0
    except ValueError as exc:
        print(json.dumps({"ok": False, "code": "invalid_input", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3
    except Exception as exc:
        print(json.dumps({"ok": False, "code": getattr(exc, "code", "plan_failed"), "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
