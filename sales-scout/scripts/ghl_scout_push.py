#!/usr/bin/env python3
"""Preview or freeze CliqSales actions for a Sales Scout brief.

The script never calls a provider write endpoint. Contact reads use the
selected tenant GHL integration. Note and additive tag actions are frozen into
one plan; contact creation remains impossible. Execution requires a separate
exact-SHA confirmation through the shared Sales GHL helper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
from safe_html import render as _safe_render  # noqa: E402
import ghl_client as _gc  # noqa: E402

SCRIPT_PATH = Path(__file__).resolve()
SKILL_DIR = SCRIPT_PATH.parents[1]
SHARED_LIB = SKILL_DIR.parent / "_lib"
SCOUT_TAG = "sales scout"
SOURCE_AGENT = "cso"
SKILL_VERSION = "1.4"
DEFAULT_HISTORY_PATH = Path("/documents/sales/.scout-history.jsonl")


def _sales_plan():
    script_path = SCRIPT_PATH
    candidates: list[Path] = [SHARED_LIB]
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
        if key in seen or not (lib_dir / "sales_ghl_plan.py").exists():
            continue
        seen.add(key)
        if key not in sys.path:
            sys.path.insert(0, key)
        try:
            import sales_ghl_plan  # type: ignore
        except Exception:
            continue
        return sales_ghl_plan
    raise RuntimeError("sales_ghl_plan.py nebyl nalezen v cs-skills/_lib/")


def _prospect_package():
    script_path = SCRIPT_PATH
    candidates: list[Path] = [SHARED_LIB]
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
        if key in seen or not (lib_dir / "sales_prospect_package.py").is_file():
            continue
        seen.add(key)
        if key not in sys.path:
            sys.path.insert(0, key)
        try:
            import sales_prospect_package  # type: ignore
        except Exception:
            continue
        return sales_prospect_package
    raise RuntimeError("sales_prospect_package.py nebyl nalezen v cs-skills/_lib/")


def md_to_ghl_html(markdown: str) -> str:
    return _safe_render(markdown, tables=True)


def _norm_phone(value: str | None, market: str = "CZ") -> str:
    normalized = _prospect_package().normalize_phone(value, market) if value else ""
    return normalized.lstrip("+")


def _safe_norm_phone(value: Any, market: str) -> str:
    try:
        return _norm_phone(str(value or ""), market)
    except (TypeError, ValueError):
        return ""


def find_contact(
    email: str | None, phone: str | None, *, profile: str, market: str = "CZ"
) -> tuple[str, dict[str, Any] | None, str | None, str]:
    """Resolve only exact provider matches and preserve unknown fail-closed."""
    exact_by_id: dict[str, dict[str, Any]] = {}
    timestamp = ""
    if email:
        try:
            candidates = _sales_plan().lookup_contact_exact("email", email, profile=profile)
        except Exception as exc:
            return _gc.UNKNOWN, None, str(exc), datetime.now(timezone.utc).isoformat()
        timestamp = datetime.now(timezone.utc).isoformat()
        wanted = _gc.norm_email(email)
        matches = [
            item for item in candidates
            if any(
                _gc.norm_email(candidate) == wanted
                for candidate in [item.get("email"), *(item.get("additionalEmails") or [])]
            )
        ]
        if len(matches) > 1:
            return _gc.UNKNOWN, None, "CRM obsahuje více přesných shod e-mailu", timestamp
        if len(matches) == 1 and matches[0].get("id"):
            exact_by_id[str(matches[0]["id"])] = matches[0]

    if phone:
        try:
            wanted = _norm_phone(phone, market)
        except (TypeError, ValueError) as exc:
            return _gc.UNKNOWN, None, f"Telefon nelze marketově normalizovat: {exc}", datetime.now(timezone.utc).isoformat()
        try:
            candidates = _sales_plan().lookup_contact_exact("phone", wanted, profile=profile)
        except Exception as exc:
            return _gc.UNKNOWN, None, str(exc), datetime.now(timezone.utc).isoformat()
        timestamp = datetime.now(timezone.utc).isoformat()
        matches = [
            item for item in candidates
            if any(
                _safe_norm_phone(candidate, market) == wanted
                for candidate in [item.get("phone"), *(item.get("additionalPhones") or [])]
                if candidate
            )
        ]
        if len(matches) > 1:
            return _gc.UNKNOWN, None, "CRM obsahuje více přesných shod telefonu", timestamp
        if len(matches) == 1 and matches[0].get("id"):
            exact_by_id[str(matches[0]["id"])] = matches[0]

    if len(exact_by_id) > 1:
        return _gc.UNKNOWN, None, "E-mail a telefon patří v CRM různým kontaktům", timestamp
    if len(exact_by_id) == 1:
        return _gc.FOUND, next(iter(exact_by_id.values())), None, timestamp
    reason = "žádná přesná shoda" if email or phone else "nezadán e-mail ani telefon"
    return _gc.NOT_FOUND, None, reason, timestamp or datetime.now(timezone.utc).isoformat()


def _request_slot(action: str, identity: str, profile: str) -> str:
    digest = hashlib.sha256(f"{profile}\0{identity}".encode("utf-8")).hexdigest()[:32]
    return f"{action}:{digest}"


def _action_summary(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": action.get("actionId"),
        "status": "planned",
        "actionType": action.get("actionType"),
        "idempotencyKey": action.get("idempotencyKey"),
        "payloadSha256": action.get("payloadSha256"),
        "reused": False,
    }


def append_history(history_path: Path, entry: dict[str, Any]) -> bool:
    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return True
    except OSError as exc:
        print(f"WARN: nelze zapsat do {history_path}: {exc}", file=sys.stderr)
        return False


def write_review(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _history_rows(history_path: Path) -> list[dict[str, Any]]:
    if not history_path.exists():
        return []
    try:
        lines = history_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"Scout historii nelze načíst: {exc}") from exc
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _recent_history(entry: dict[str, Any], now: datetime) -> bool:
    raw = str(entry.get("date") or "").strip()
    try:
        timestamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return False
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return now - timedelta(days=60) <= timestamp <= now + timedelta(minutes=5)


def _history_matches(entry: dict[str, Any], contact_id: str, email: str) -> bool:
    if contact_id and str(entry.get("contactId") or "").strip() == contact_id:
        return True
    return bool(email) and _gc.norm_email(entry.get("email")) == _gc.norm_email(email)


def check_cached_brief(history_path: Path, contact_id: str, email: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    for entry in reversed(_history_rows(history_path)):
        if not _recent_history(entry, now) or not _history_matches(entry, contact_id, email):
            continue
        legacy_note_id = str(entry.get("ghl_note_id") or "").strip()
        if legacy_note_id:
            return {
                "ok": True,
                "cached": True,
                "contactId": entry.get("contactId") or contact_id or None,
                "deliveryState": "succeeded",
                "legacyGhlNoteId": legacy_note_id,
            }
        if entry.get("delivery_state") == "succeeded":
            return {
                "ok": True,
                "cached": True,
                "contactId": entry.get("contactId") or contact_id or None,
                "deliveryState": "succeeded",
                "externalActionIds": entry.get("external_action_ids") or [],
            }
        if entry.get("delivery_state") != "plan_frozen":
            continue
        artifact_path = str(entry.get("plan_artifact") or "").strip()
        if not artifact_path:
            return {"ok": True, "cached": False, "reason": "čekající plán nemá durable artefakt"}
        client = _sales_plan()
        artifact = client.validate_plan(client.read_artifact(artifact_path))
        planned_actions = artifact.get("actions") if isinstance(artifact, dict) else None
        note_actions = [
            item for item in (planned_actions or [])
            if isinstance(item, dict) and item.get("actionType") == "sales.ghl.note.create.v1"
        ]
        def matches_history_identity(item: dict[str, Any]) -> bool:
            payload = item.get("payload")
            if not isinstance(payload, dict):
                return False
            entry_contact = str(entry.get("contactId") or contact_id or "").strip()
            if entry_contact:
                return str(payload.get("contactId") or "").strip() == entry_contact
            return bool(email) and _gc.norm_email(payload.get("contactEmail")) == _gc.norm_email(email)
        report_path = client.execution_report_path(str(artifact["planSha256"]))
        try:
            report = client.validate_execution_report(
                client.read_artifact(report_path),
                artifact,
            )
        except FileNotFoundError:
            return {
                "ok": True,
                "cached": False,
                "reason": "zmrazený plán ještě nebyl proveden",
                "planArtifact": artifact_path,
                "planSha256": artifact["planSha256"],
            }
        report_by_id = {
            str(item.get("actionId") or ""): item
            for item in report.get("actions", [])
            if isinstance(item, dict)
        }
        succeeded = []
        for action in note_actions:
            result = report_by_id.get(str(action.get("actionId") or ""))
            if (
                result
                and result.get("status") == "succeeded"
                and isinstance(result.get("providerReceipt"), dict)
                and str(result["providerReceipt"].get("id") or "").strip()
                and matches_history_identity(action)
            ):
                succeeded.append((action, result))
        if not succeeded:
            return {
                "ok": True,
                "cached": False,
                "reason": "plán ještě nemá prokázaný note readback",
                "planArtifact": artifact_path,
            }
        promotion = {
            **entry,
            "date": now.isoformat(),
            "delivery_state": "succeeded",
            "plan_action_ids": [action.get("actionId") for action, _result in succeeded],
            "provider_receipt_ids": [result["providerReceipt"].get("id") for _action, result in succeeded],
            "promoted_from": "plan_frozen",
        }
        if not append_history(history_path, promotion):
            raise ValueError("prokázaný Scout cache stav nelze zapsat do historie")
        return {
            "ok": True,
            "cached": True,
            "promoted": True,
            "contactId": promotion.get("contactId") or contact_id or None,
            "deliveryState": "succeeded",
            "planActionIds": promotion["plan_action_ids"],
            "planArtifact": artifact_path,
        }
    return {"ok": True, "cached": False, "reason": "bez úspěšného briefu mladšího 60 dnů"}


def _add_action(
    journal: Any,
    *,
    action_type: str,
    slot: str,
    payload: dict[str, Any],
    args: argparse.Namespace,
    depends_on_action_id: str | None = None,
) -> dict[str, Any]:
    return journal.add_action(
        slot=slot,
        action_type=action_type,
        payload=payload,
        depends_on_action_id=depends_on_action_id,
        source_run_id=args.source_run_id,
        credential_profile=args.credential_profile,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Připraví zmrazený GHL plán pro Scout brief; nic přímo nezapisuje"
    )
    parser.add_argument("--contact-id")
    parser.add_argument("--email")
    parser.add_argument("--phone")
    parser.add_argument("--first-name")
    parser.add_argument("--last-name")
    parser.add_argument("--company")
    parser.add_argument("--market", default="CZ", help="ISO alpha-2 market (CZ, SK, ES)")
    parser.add_argument("--note-body-file", type=Path)
    parser.add_argument("--no-tag", action="store_true")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--check-cache", action="store_true",
                            help="před research ověří historii a execution journal")
    mode_group.add_argument("--preview-html", action="store_true")
    mode_group.add_argument("--create-plan", action="store_true",
                            help="Vytvoří exact plán; vyžaduje --task-id")
    parser.add_argument("--history-path", type=Path, default=DEFAULT_HISTORY_PATH)
    parser.add_argument("--plan-artifact", help="kanonický durable JSON plánu briefu")
    parser.add_argument("--review-output", type=Path,
                        help="file/review výstup pro kontakt, který v CRM neexistuje")
    parser.add_argument("--idempotency-key", help="stabilní základ klíče briefu")
    parser.add_argument("--product-mode", choices=["single", "multi"], default="single")
    parser.add_argument("--products", default="")
    parser.add_argument("--fit-grades", default="{}")
    parser.add_argument("--mode", choices=["webhook", "manual"], default="manual")
    parser.add_argument("--task-id", type=int)
    parser.add_argument("--source-run-id")
    parser.add_argument("--credential-profile", default="default")
    parser.add_argument("--plan-revision", type=int, default=1,
                        help="Změněný plán musí mít nový artefakt a idempotency key")
    args = parser.parse_args()

    try:
        args.market, _market_config = _prospect_package().market_config(args.market)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    if not args.contact_id and not args.email and not args.phone:
        print("ERROR: Zadej --contact-id, --email nebo --phone.", file=sys.stderr)
        return 3
    if args.check_cache:
        try:
            print(json.dumps(check_cached_brief(
                args.history_path,
                (args.contact_id or "").strip(),
                (args.email or "").strip(),
            ), ensure_ascii=False))
            return 0
        except Exception as exc:
            print(json.dumps({"ok": False, "code": getattr(exc, "code", "cache_check_failed"),
                              "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 2
    if args.task_id is not None and args.task_id <= 0:
        parser.error("--task-id musí být kladné číslo")
    if args.create_plan and not args.task_id:
        parser.error("--create-plan vyžaduje kladné --task-id pro provenance")
    if args.create_plan and not args.plan_artifact:
        parser.error("--create-plan vyžaduje --plan-artifact")
    if args.create_plan and not (args.idempotency_key or "").strip():
        parser.error("--create-plan vyžaduje --idempotency-key")
    if not args.preview_html and not args.create_plan:
        parser.error("Zvol --preview-html nebo --create-plan s --task-id")
    if args.plan_revision <= 0:
        parser.error("--plan-revision musí být kladné číslo")
    if args.note_body_file is None or not args.note_body_file.exists():
        print(f"ERROR: Soubor s briefem neexistuje: {args.note_body_file}", file=sys.stderr)
        return 3
    note_md = args.note_body_file.read_text(encoding="utf-8")
    if not note_md.strip():
        print("ERROR: Soubor s briefem je prázdný.", file=sys.stderr)
        return 3
    html_body = md_to_ghl_html(note_md)
    if len(html_body) > 200_000:
        print("ERROR: Brief po HTML konverzi překračuje limit 200 000 znaků.", file=sys.stderr)
        return 3

    if args.preview_html:
        print(json.dumps({
            "ok": True,
            "mode": "preview",
            "preview": True,
            "noteHtml": html_body,
            "htmlLength": len(html_body),
            "directProviderWrites": 0,
        }, indent=2, ensure_ascii=False))
        return 0

    try:
        client = _sales_plan()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(json.dumps({"ok": False, "code": getattr(exc, "code", "artifact_failed"),
                          "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 4

    contact_id = (args.contact_id or "").strip()
    resolution = "provided_contact_id" if contact_id else ""
    exact_identity: dict[str, str] | None = None
    if contact_id:
        try:
            exact_identity = client.lookup_contact_snapshot(
                contact_id=contact_id,
                email=args.email,
                phone=args.phone,
                profile=args.credential_profile,
            )
        except Exception as exc:
            print(json.dumps({"ok": False, "code": getattr(exc, "code", "contact_lookup_failed"),
                              "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 5
    if not contact_id:
        state, contact, reason, _lookup_completed_at = find_contact(
            args.email, args.phone, profile=args.credential_profile, market=args.market
        )
        if state == _gc.UNKNOWN:
            print(f"ERROR: stav kontaktu v CRM je neznámý ({reason}); žádná akce nebyla vytvořena.", file=sys.stderr)
            return 5
        if state == _gc.FOUND and contact:
            contact_id = str(contact.get("id") or "").strip()
            if not contact_id:
                print("ERROR: exact GHL kontakt nemá contactId.", file=sys.stderr)
                return 5
            exact_identity = client.contact_identity_fields(contact, contact_id)
            resolution = "found_by_exact_lookup"
        else:
            review_output = args.review_output or Path(
                f"/documents/sales/scout-review/{args.task_id}-brief.md"
            )
            write_review(review_output, note_md)
            print(json.dumps({
                "success": False,
                "planned": False,
                "fileReviewOnly": True,
                "directProviderWrites": 0,
                "reason": "Kontakt v CliqSales neexistuje; Scout jej v této verzi nevytváří.",
                "reviewOutput": str(review_output),
            }, ensure_ascii=False))
            return 0

    assert contact_id
    assert exact_identity is not None
    journal = client.SalesGhlPlan(
        args.plan_artifact,
        producer="sales-scout",
        skill_version=SKILL_VERSION,
        task_id=args.task_id,
        task_contract="sales-scout:brief-actions-v1-4",
        idempotency_key=args.idempotency_key.strip(),
        revision=args.plan_revision,
        source_agent=SOURCE_AGENT,
        source_run_id=args.source_run_id,
        metadata={"mode": args.mode, "market": args.market, "historyPath": str(args.history_path)},
    )
    expected_slots = {
        str(item.get("slot"))
        for item in journal.value.get("actions", [])
        if isinstance(item, dict) and item.get("slot")
    }
    actions: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    note_slot = _request_slot("note-create", contact_id, args.credential_profile)
    expected_slots.add(note_slot)
    note_action_id: str | None = None
    try:
        record = _add_action(
            journal,
            action_type="sales.ghl.note.create.v1",
            slot=note_slot,
            payload={**exact_identity, "body": html_body},
            args=args,
        )
        note_summary = _action_summary(record)
        actions.append(note_summary)
        note_action_id = str(note_summary.get("id") or "").strip() or None
    except Exception as exc:
        failures.append({"actionType": "sales.ghl.note.create.v1",
                         "code": getattr(exc, "code", "plan_failed"), "error": str(exc)})

    # Tag must never overtake the note. Bind it to the preceding immutable action.
    if not args.no_tag and note_action_id:
        try:
            tag_slot = _request_slot("tags-add", contact_id, args.credential_profile)
            expected_slots.add(tag_slot)
            record = _add_action(
                journal,
                action_type="sales.ghl.tags.add.v1",
                slot=tag_slot,
                payload={**exact_identity, "tags": [SCOUT_TAG]},
                args=args,
                depends_on_action_id=note_action_id,
            )
            actions.append(_action_summary(record))
        except Exception as exc:
            failures.append({"actionType": "sales.ghl.tags.add.v1",
                             "code": getattr(exc, "code", "plan_failed"), "error": str(exc)})
    elif not args.no_tag and not note_action_id:
        failures.append({
            "actionType": "sales.ghl.tags.add.v1",
            "code": "dependency_missing",
            "error": "Tag nebyl přidán, protože plán nemá ID předchozí note akce.",
        })

    try:
        fit_grades = json.loads(args.fit_grades) if args.fit_grades else {}
    except json.JSONDecodeError:
        fit_grades = {}
    products = [item.strip() for item in args.products.split(",") if item.strip()]
    artifact_complete = False
    if actions and not failures:
        journal.finish(expected_slots)
        artifact_complete = True
    delivery_state = "plan_frozen" if artifact_complete else "plan_incomplete"
    history_entry = {
        "date": datetime.now(timezone.utc).isoformat(),
        "contactId": contact_id,
        "firma": args.company or "",
        "email": args.email or "",
        "mode": args.mode,
        "product_mode": args.product_mode,
        "products": products,
        "fit_grades": fit_grades,
        "delivery_state": delivery_state,
        "plan_action_ids": [item.get("id") for item in actions if item.get("id")],
        "plan_artifact": args.plan_artifact,
        "plan_sha256": journal.value.get("planSha256"),
        "skill_version": SKILL_VERSION,
        "contact_resolution": resolution,
    }
    append_history(args.history_path, history_entry)

    result = {
        "success": artifact_complete and not failures,
        "planned": bool(actions),
        "direct_provider_writes": 0,
        "contactId": contact_id,
        "contactResolution": resolution,
        "actions": actions,
        "failures": failures,
        "deliveryState": delivery_state,
        "planArtifact": args.plan_artifact,
        "planSha256": journal.value.get("planSha256"),
        "planComplete": artifact_complete,
        "note": "GHL zápis vyžaduje samostatné potvrzení exact SHA celého zmrazeného plánu.",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 4


if __name__ == "__main__":
    raise SystemExit(main())
