#!/usr/bin/env python3
"""Preview or freeze one Sales Assistant GHL plan.

The default is a local preview. ``--create-plan`` resolves one exact contact
through the selected tenant GHL integration and atomically freezes named note,
additive-tag and optional task actions. It performs no provider write. Execute
the completed plan only through ``sales_ghl_plan.py execute`` with its exact
SHA-256 and the user's explicit confirmation.
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
ASSISTANT_TAG = "sales assistant"
SKILL_VERSION = "1.0"
TASK_CONTRACT_BY_KIND = {
    "priprava": "sales-assistant:call-prep",
    "po-jednani": "sales-assistant:post-call-actions",
    "hygiena": "sales-assistant:pipeline-hygiene-actions",
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


def _read_optional(path: str | None, inline: str | None, label: str) -> str:
    if path:
        try:
            return Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"{label} nelze načíst: {exc}") from exc
    return inline or ""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or freeze Sales Assistant note/tag/task actions into one GHL plan",
    )
    parser.add_argument("--contact-id", required=True)
    parser.add_argument("--contact-email")
    parser.add_argument("--contact-phone")
    parser.add_argument("--contact-name")
    parser.add_argument("--note-title", default="")
    parser.add_argument("--note-body-file")
    parser.add_argument("--note-body")
    parser.add_argument("--task", help="titulek úkolu obchodníkovi")
    parser.add_argument("--task-due", help="ISO 8601 datum s časovým pásmem")
    parser.add_argument("--task-body")
    parser.add_argument("--task-body-file")
    parser.add_argument("--assignee", help="GHL user ID obchodníka")
    parser.add_argument("--kind", default="priprava", choices=["priprava", "po-jednani", "hygiena"])
    parser.add_argument("--preview-html", action="store_true")
    parser.add_argument("--create-plan", action="store_true", help="vytvoří zmrazený plán; neprovede žádný GHL zápis")
    parser.add_argument("--idempotency-key", help="stabilní základ klíče; plán přidá :note, :tag a :task")
    parser.add_argument("--plan-artifact", help="kanonický JSON artefakt zmrazeného plánu")
    parser.add_argument("--plan-slot", help="stabilní kontaktový slot uvnitř aggregate plánu")
    parser.add_argument("--complete-plan", action="store_true",
                        help="zmrazí aggregate plán; použij jen na posledním kontaktu")
    parser.add_argument("--expected-slot", action="append", default=[],
                        help="úplný frozen slot set aggregate artefaktu; opakuj pro každý slot")
    parser.add_argument("--source-agent", default="cso")
    parser.add_argument("--task-id", type=int, help="povinné kladné ID existujícího CC tasku pro --create-plan")
    parser.add_argument("--source-run-id")
    parser.add_argument("--credential-profile", default="default")
    parser.add_argument("--expires-at", type=int)
    parser.add_argument(
        "--plan-revision",
        type=int,
        default=1,
        help="verze nového plánu; změněný plán musí mít nový artefakt a idempotency key",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        markdown = _read_optional(args.note_body_file, args.note_body, "tělo poznámky")
        if not markdown.strip():
            raise ValueError("chybí --note-body-file nebo --note-body")
        title = (
            f"## 🤝 {args.note_title}\n\n"
            if args.note_title and not markdown.lstrip().startswith(("#", "🤝"))
            else ""
        )
        html = _safe_render(title + markdown, tables=True)
        task_body = _read_optional(args.task_body_file, args.task_body, "tělo úkolu")
        if args.task and not task_body.strip():
            raise ValueError("--task vyžaduje --task-body nebo --task-body-file")
        if args.task and not args.task_due:
            raise ValueError("--task vyžaduje --task-due jako ISO 8601 datum s časovým pásmem")
        assignee = (args.assignee or "").strip()
        if args.task and not assignee:
            raise ValueError("--task vyžaduje neprázdné --assignee (GHL user ID ze Sales DNA §1)")
        identity = {"contactId": args.contact_id}
        if (args.contact_email or "").strip():
            identity["contactEmail"] = args.contact_email.strip()
        if (args.contact_phone or "").strip():
            identity["contactPhone"] = args.contact_phone.strip()
        if (args.contact_name or "").strip():
            identity["contactName"] = args.contact_name.strip()
        note_payload = {**identity, "body": html}
        tag_payload = {**identity, "tags": [ASSISTANT_TAG]}
        task_payload: dict[str, Any] | None = None
        if args.task:
            task_payload = {
                **identity,
                "title": args.task,
                "body": task_body.strip(),
                "assignedTo": assignee,
            }
            if args.task_due:
                task_payload["dueDate"] = args.task_due

        preview = {
            "ok": True,
            "mode": "preview",
            "producer": "sales-assistant",
            "kind": args.kind,
            "currentActions": [
                {"actionType": "sales.ghl.note.create.v1", "payload": note_payload},
                {"actionType": "sales.ghl.tags.add.v1", "payload": tag_payload},
                *(
                    [{"actionType": "sales.ghl.task.create.v1", "payload": task_payload}]
                    if task_payload
                    else []
                ),
            ],
        }
        if args.preview_html:
            print(json.dumps({**preview, "preview": True}, ensure_ascii=False, indent=2))
            return 0
        if not args.create_plan:
            print(json.dumps(preview, ensure_ascii=False, indent=2))
            return 0
        if args.task_id is None or args.task_id <= 0:
            raise ValueError("--create-plan vyžaduje kladné --task-id existujícího CC tasku")
        if not (args.idempotency_key or "").strip():
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
        note_slot = f"{args.plan_slot}:note" if args.plan_slot else "note"
        tag_slot = f"{args.plan_slot}:tag" if args.plan_slot else "tag"
        task_slot = f"{args.plan_slot}:task" if args.plan_slot else "task"
        own_slots = [note_slot, tag_slot, *([task_slot] if task_payload else [])]
        if args.plan_slot and not set(own_slots).issubset(set(frozen_expected_slots)):
            raise ValueError("--expected-slot neobsahuje všechny sloty posledního kontaktu")

        client = _sales_plan()
        exact_identity = client.lookup_contact_snapshot(
            contact_id=args.contact_id,
            email=args.contact_email,
            phone=args.contact_phone,
            profile=args.credential_profile,
        )
        note_payload = {**exact_identity, "body": html}
        tag_payload = {**exact_identity, "tags": [ASSISTANT_TAG]}
        if task_payload is not None:
            task_payload = {**task_payload, **exact_identity}
        journal = client.SalesGhlPlan(
            args.plan_artifact,
            producer="sales-assistant",
            skill_version=SKILL_VERSION,
            task_id=args.task_id,
            task_contract=TASK_CONTRACT_BY_KIND[args.kind],
            idempotency_key=args.idempotency_key.strip(),
            revision=args.plan_revision,
            source_agent=args.source_agent,
            source_run_id=args.source_run_id,
            metadata={
                "kind": args.kind,
                **({"aggregateExpectedSlots": frozen_expected_slots} if args.plan_slot else {}),
            },
        )
        if args.plan_slot and journal.value["metadata"].get("aggregateExpectedSlots") != frozen_expected_slots:
            raise ValueError("aggregateExpectedSlots se mezi kontakty změnily")
        note_action = journal.add_action(
            slot=note_slot,
            action_type="sales.ghl.note.create.v1",
            payload=note_payload,
            source_run_id=args.source_run_id,
            credential_profile=args.credential_profile,
            expires_at=args.expires_at,
        )
        note_action_id = str(note_action["actionId"])
        journal.add_action(
            slot=tag_slot,
            action_type="sales.ghl.tags.add.v1",
            payload=tag_payload,
            depends_on_action_id=note_action_id,
            source_run_id=args.source_run_id,
            credential_profile=args.credential_profile,
            expires_at=args.expires_at,
        )
        if task_payload:
            journal.add_action(
                slot=task_slot,
                action_type="sales.ghl.task.create.v1",
                payload=task_payload,
                depends_on_action_id=note_action_id,
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
    except Exception as exc:  # shared helper returns its own safe message
        code = getattr(exc, "code", "plan_failed")
        print(json.dumps({"ok": False, "code": code, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
