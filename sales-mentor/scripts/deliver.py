#!/usr/bin/env python3
"""Preview or freeze protected Sales Mentor delivery actions.

No GHL credential or provider HTTP implementation exists here. Note/tag and
email operations become one typed frozen plan; default mode is an exact payload
preview. Execution is a separate exact-SHA step in the shared GHL helper.
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
MENTOR_TAG = "sales mentor"
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


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--body-file")
    parser.add_argument("--body")
    parser.add_argument("--create-plan", action="store_true", help="vytvoří plán; nic neodešle ani nezapíše")
    parser.add_argument("--idempotency-key", help="stabilní základ klíče plánu")
    parser.add_argument("--plan-artifact", help="kanonický JSON zmrazeného plánu")
    parser.add_argument("--plan-slot", help="stabilní slot příjemce uvnitř aggregate plánu")
    parser.add_argument("--complete-plan", action="store_true",
                        help="zmrazí aggregate plán; použij jen na posledním příjemci")
    parser.add_argument("--expected-slot", action="append", default=[],
                        help="úplný frozen slot set aggregate artefaktu; opakuj pro každý slot")
    parser.add_argument("--source-agent", default="cso")
    parser.add_argument("--task-id", type=int, help="povinné kladné ID existujícího CC tasku pro --create-plan")
    parser.add_argument(
        "--task-contract",
        choices=["sales-mentor:call-scorecard-actions", "sales-mentor:report-delivery"],
        help="exact action checkpoint aktuálního tasku",
    )
    parser.add_argument("--source-run-id")
    parser.add_argument("--credential-profile", default="default")
    parser.add_argument("--expires-at", type=int)
    parser.add_argument(
        "--plan-revision",
        type=int,
        default=1,
        help="verze nového plánu; změna vyžaduje nový artefakt a idempotency key",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview or freeze a Sales Mentor GHL delivery plan")
    commands = parser.add_subparsers(dest="mode", required=True)
    note = commands.add_parser("note", help="pointer note plus additive mentor tag")
    note.add_argument("--contact-id", required=True)
    note.add_argument("--contact-email")
    note.add_argument("--contact-phone")
    note.add_argument("--contact-name")
    _common(note)
    email = commands.add_parser("email", help="email to an exact existing contact ID")
    email.add_argument("--to-contact-id", required=True)
    email.add_argument("--to-email", required=True, help="přesná schvalovaná adresa příjemce")
    email.add_argument("--subject", required=True)
    email.add_argument("--email-from", help="ověřená odesílací e-mailová adresa z Sales DNA §1")
    _common(email)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        html = _safe_render(_body(args), tables=False)
        if args.mode == "note":
            if not (args.contact_email or "").strip() and not (args.contact_phone or "").strip():
                raise ValueError("note vyžaduje --contact-email nebo --contact-phone z exact CC snapshotu")
            identity = {"contactId": args.contact_id}
            if (args.contact_email or "").strip():
                identity["contactEmail"] = args.contact_email.strip()
            if (args.contact_phone or "").strip():
                identity["contactPhone"] = args.contact_phone.strip()
            if (args.contact_name or "").strip():
                identity["contactName"] = args.contact_name.strip()
            payloads = [
                ("sales.ghl.note.create.v1", "note", {**identity, "body": html}),
                ("sales.ghl.tags.add.v1", "tag", {**identity, "tags": [MENTOR_TAG]}),
            ]
        else:
            email_from = (args.email_from or "").strip()
            if not email_from:
                raise ValueError("email request vyžaduje neprázdné --email-from z Sales DNA §1")
            email_payload: dict[str, Any] = {
                "channel": "email",
                "contactId": args.to_contact_id,
                "toEmail": args.to_email,
                "subject": args.subject,
                "html": html,
                "emailFrom": email_from,
                "safety": INTERNAL_REPORT_SAFETY,
            }
            payloads = [("sales.ghl.message.send.v1", "email", email_payload)]

        preview = {
            "ok": True,
            "mode": "preview",
            "producer": "sales-mentor",
            "delivery": args.mode,
            "currentActions": [{"actionType": action_type, "payload": payload} for action_type, _suffix, payload in payloads],
        }
        if not args.create_plan:
            print(json.dumps(preview, ensure_ascii=False, indent=2))
            return 0
        if args.task_id is None or args.task_id <= 0:
            raise ValueError("--create-plan vyžaduje kladné --task-id existujícího CC tasku")
        if not (args.idempotency_key or "").strip():
            raise ValueError("--create-plan vyžaduje --idempotency-key")
        if not args.plan_artifact:
            raise ValueError("--create-plan vyžaduje --plan-artifact")
        if not args.task_contract:
            raise ValueError("--create-plan vyžaduje --task-contract")
        if args.plan_revision <= 0:
            raise ValueError("--plan-revision musí být kladné číslo")
        if args.plan_slot and not args.expected_slot:
            raise ValueError("--plan-slot vyžaduje úplný frozen opakovaný --expected-slot")
        if len(args.expected_slot) != len(set(args.expected_slot)):
            raise ValueError("--expected-slot se nesmí opakovat")
        frozen_expected_slots = sorted(args.expected_slot)
        if args.mode == "note":
            own_slots = [
                f"{args.plan_slot}:note" if args.plan_slot else "note",
                f"{args.plan_slot}:tag" if args.plan_slot else "tag",
            ]
        else:
            own_slots = [args.plan_slot or "email"]
        if args.plan_slot and not set(own_slots).issubset(set(frozen_expected_slots)):
            raise ValueError("--expected-slot neobsahuje všechny sloty posledního doručení")

        client = _sales_plan()
        if args.mode == "note":
            exact_identity = client.lookup_contact_snapshot(
                contact_id=args.contact_id,
                email=args.contact_email,
                phone=args.contact_phone,
                profile=args.credential_profile,
            )
            payloads = [
                ("sales.ghl.note.create.v1", "note", {**exact_identity, "body": html}),
                ("sales.ghl.tags.add.v1", "tag", {**exact_identity, "tags": [MENTOR_TAG]}),
            ]
        else:
            client.lookup_contact_snapshot(
                contact_id=args.to_contact_id,
                email=args.to_email,
                profile=args.credential_profile,
            )
        journal = client.SalesGhlPlan(
            args.plan_artifact,
            producer="sales-mentor",
            skill_version=SKILL_VERSION,
            task_id=args.task_id,
            task_contract=args.task_contract,
            idempotency_key=args.idempotency_key.strip(),
            revision=args.plan_revision,
            source_agent=args.source_agent,
            source_run_id=args.source_run_id,
            metadata={
                "delivery": "aggregate" if args.plan_slot else args.mode,
                **({"aggregateExpectedSlots": frozen_expected_slots} if args.plan_slot else {}),
            },
        )
        if args.plan_slot and journal.value["metadata"].get("aggregateExpectedSlots") != frozen_expected_slots:
            raise ValueError("aggregateExpectedSlots se mezi doručeními změnily")
        if args.mode == "note":
            note_type, note_suffix, note_payload = payloads[0]
            note_slot = f"{args.plan_slot}:note" if args.plan_slot else note_suffix
            note_action = journal.add_action(
                slot=note_slot,
                action_type=note_type,
                payload=note_payload,
                source_run_id=args.source_run_id,
                credential_profile=args.credential_profile,
                expires_at=args.expires_at,
            )
            note_action_id = str(note_action["actionId"])
            tag_type, tag_suffix, tag_payload = payloads[1]
            tag_slot = f"{args.plan_slot}:tag" if args.plan_slot else tag_suffix
            journal.add_action(
                slot=tag_slot,
                action_type=tag_type,
                payload=tag_payload,
                depends_on_action_id=note_action_id,
                source_run_id=args.source_run_id,
                credential_profile=args.credential_profile,
                expires_at=args.expires_at,
            )
        else:
            for action_type, suffix, payload in payloads:
                journal.add_action(
                    slot=args.plan_slot or suffix,
                    action_type=action_type,
                    payload=payload,
                    source_run_id=args.source_run_id,
                    credential_profile=args.credential_profile,
                    expires_at=args.expires_at,
                )
        expected_slots = frozen_expected_slots if args.plan_slot else own_slots
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
