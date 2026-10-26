#!/usr/bin/env python3
"""Preview or freeze a Sales Prospector GHL plan.

The historical filename is kept for compatibility, but this script never loads
a GHL write endpoint while planning. Reads use the selected tenant GHL
integration. Writes become immutable named actions in one exact plan:

* a contact that is not found remains file/review-only;
* an existing contact receives additive tags only;
* standard fields are never overwritten and the whole ``tags`` array is never
  replaced;
* contact creation is outside the active action contract.

Exit codes: 0=plan prepared/reused, 2=integration/read failure,
3=input validation failure, 4=one or more plan actions failed safely.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_TAG = "sales prospector"
SOURCE_AGENT = "cso"
SKILL_VERSION = "1.4"


def _sales_plan():
    script_path = Path(__file__).resolve()
    skill_dir = script_path.parents[1]
    candidates: list[Path] = [skill_dir.parent / "_lib"]
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
    script_path = Path(__file__).resolve()
    skill_dir = script_path.parents[1]
    candidates: list[Path] = [skill_dir.parent / "_lib"]
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


def _norm_email(value: str | None) -> str:
    return (value or "").strip().lower()


def _norm_phone(value: str | None, market: str = "CZ") -> str:
    normalized = _prospect_package().normalize_phone(value, market) if value else ""
    return normalized.lstrip("+")


def _safe_norm_phone(value: Any, market: str) -> str:
    try:
        return _norm_phone(str(value or ""), market)
    except (TypeError, ValueError):
        return ""


def _exact_matches(
    contacts: list[dict[str, Any]], *, email: str = "", phone: str = "", market: str = "CZ"
) -> list[dict[str, Any]]:
    if email:
        wanted = _norm_email(email)
        return [
            item for item in contacts
            if any(
                _norm_email(str(candidate or "")) == wanted
                for candidate in [item.get("email"), *(item.get("additionalEmails") or [])]
            )
        ]
    wanted_phone = _norm_phone(phone, market)
    return [
        item for item in contacts
        if any(
            _safe_norm_phone(candidate, market) == wanted_phone
            for candidate in [item.get("phone"), *(item.get("additionalPhones") or [])]
            if candidate
        )
    ]


def lookup_contact(
    email: str, phone: str, *, profile: str, contact_id: str = "", market: str = "CZ"
) -> tuple[str, dict[str, Any] | None, str | None, str]:
    """Return found/not_found/unknown plus fresh lookup timestamp."""
    if contact_id:
        try:
            identity = _sales_plan().lookup_contact_snapshot(
                contact_id=contact_id,
                email=email or None,
                phone=phone or None,
                profile=profile,
            )
        except Exception as exc:
            return "unknown", None, str(exc), datetime.now(timezone.utc).isoformat()
        return "found", {
            "id": identity["contactId"],
            "email": identity.get("contactEmail", ""),
            "phone": identity.get("contactPhone", ""),
            "name": identity.get("contactName", ""),
        }, None, datetime.now(timezone.utc).isoformat()
    completed_at = ""
    exact_by_id: dict[str, dict[str, Any]] = {}
    for key, value in (("email", _norm_email(email)), ("phone", _norm_phone(phone, market))):
        if not value:
            continue
        try:
            contacts = _sales_plan().lookup_contact_exact(key, value, profile=profile)
        except Exception as exc:
            return "unknown", None, str(exc), datetime.now(timezone.utc).isoformat()
        completed_at = datetime.now(timezone.utc).isoformat()
        matches = _exact_matches(contacts, market=market, **{key: value})
        if len(matches) > 1:
            return "unknown", None, f"CRM obsahuje více přesných shod pro {key}", completed_at
        if len(matches) == 1 and matches[0].get("id"):
            exact_by_id[str(matches[0]["id"])] = matches[0]
    if len(exact_by_id) > 1:
        return "unknown", None, "E-mail a telefon patří v CRM různým kontaktům", completed_at
    if len(exact_by_id) == 1:
        return "found", next(iter(exact_by_id.values())), None, completed_at
    return "not_found", None, None, completed_at or datetime.now(timezone.utc).isoformat()


REQUIRED_COLS = {"Company", "Source"}


def parse_csv(path: Path, row_filter: set[int] | None = None) -> list[dict[str, str]]:
    if not path.exists():
        raise ValueError(f"CSV soubor neexistuje: {path}")
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV nemá hlavičku")
        missing = REQUIRED_COLS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV chybí povinné sloupce: {sorted(missing)}")
        rows: list[dict[str, str]] = []
        for index, raw_row in enumerate(reader, start=1):
            if row_filter is not None and index not in row_filter:
                continue
            row = {str(key): str(value or "") for key, value in raw_row.items() if key is not None}
            row["_csv_row"] = str(index)
            rows.append(row)
        return rows


def parse_row_filter(spec: str | None) -> set[int] | None:
    if not spec:
        return None
    result: set[int] = set()
    for chunk in spec.split(","):
        clean = chunk.strip()
        if not clean:
            continue
        if "-" in clean:
            start, end = clean.split("-", 1)
            result.update(range(int(start), int(end) + 1))
        else:
            result.add(int(clean))
    return result


def validate_row(row: dict[str, str]) -> str | None:
    market = (row.get("Market") or "CZ").strip().upper()
    try:
        normalized_phone = _norm_phone(row.get("Phone"), market)
        _prospect_package().market_config(market)
    except ValueError:
        return "invalid market or phone"
    if (
        not (row.get("ContactId") or "").strip()
        and not _norm_email(row.get("Email"))
        and not normalized_phone
    ):
        return "missing ContactId, email and phone"
    if not (row.get("Company") or "").strip():
        return "missing company name"
    return None


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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Připraví zmrazený GHL plán Sales Prospectoru; nic přímo nezapisuje"
    )
    parser.add_argument("--csv", required=True, type=Path, help="Path to prospects.csv")
    parser.add_argument("--meta", required=True, type=Path, help="Sealed prospect package meta.json")
    parser.add_argument("--tags", default="", help="Comma-separated additive tags (default: sales prospector)")
    parser.add_argument("--rows", default=None, help="Filter rows by 1-based index (e.g. 1,3,5-10)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Jen validuje a provede exact read lookup")
    mode.add_argument("--create-plan", action="store_true",
                      help="Vytvoří exact plán; vyžaduje --task-id")
    parser.add_argument("--task-id", type=int)
    parser.add_argument("--source-run-id")
    parser.add_argument("--credential-profile", default="default")
    parser.add_argument("--idempotency-key", help="stabilní základ klíče kampaně")
    parser.add_argument("--plan-artifact", help="kanonický durable JSON plánu kampaně")
    parser.add_argument("--expected-slot", action="append", default=[],
                        help="úplný frozen slot set existujících kontaktů; opakuj pro každý tag slot")
    parser.add_argument("--plan-revision", type=int, default=1,
                        help="Změněný plán musí mít nový artefakt a idempotency key")
    args = parser.parse_args()

    if args.task_id is not None and args.task_id <= 0:
        parser.error("--task-id musí být kladné číslo")
    if not args.task_id:
        parser.error("dry-run i --create-plan vyžadují kladné --task-id pro package provenance")
    if args.create_plan and not (args.idempotency_key or "").strip():
        parser.error("--create-plan vyžaduje --idempotency-key")
    if args.create_plan and not args.plan_artifact:
        parser.error("--create-plan vyžaduje --plan-artifact")
    if args.create_plan and not args.expected_slot:
        parser.error("--create-plan vyžaduje frozen opakovaný --expected-slot z dry-run plánu")
    if len(args.expected_slot) != len(set(args.expected_slot)):
        parser.error("--expected-slot se nesmí opakovat")
    if args.plan_revision <= 0:
        parser.error("--plan-revision musí být kladné číslo")
    tags = list(dict.fromkeys(tag.strip() for tag in args.tags.split(",") if tag.strip())) or [DEFAULT_TAG]
    if len(tags) > 20 or any(len(tag) > 100 for tag in tags):
        parser.error("Nejvýše 20 tagů, každý maximálně 100 znaků")

    package_errors = _prospect_package().validate_package(
        args.meta,
        args.csv,
        expected_task_id=args.task_id,
        expected_campaign=args.csv.parent.name,
        expected_skill_version=SKILL_VERSION,
        expected_task_contract="sales-prospector:prospect-actions-v1-4",
    )
    if package_errors:
        print(json.dumps({"ok": False, "code": "prospect_package_invalid", "errors": package_errors}, ensure_ascii=False), file=sys.stderr)
        return 3

    try:
        rows = parse_csv(args.csv, parse_row_filter(args.rows))
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    valid_rows: list[dict[str, str]] = []
    skip_reasons: dict[str, int] = {}
    for row in rows:
        reason = validate_row(row)
        if reason:
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
        else:
            valid_rows.append(row)

    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    counts = {"not_found_file_only": 0, "would_tag_existing": 0, "unknown": 0,
              "planned_tags": 0, "reused": 0}
    client = None
    journal = None
    expected_slots: set[str] = set()
    frozen_expected_slots = sorted(args.expected_slot)
    create_plan = bool(args.create_plan)
    if create_plan:
        try:
            client = _sales_plan()
            journal = client.SalesGhlPlan(
                args.plan_artifact,
                producer="sales-prospector",
                skill_version=SKILL_VERSION,
                task_id=args.task_id,
                task_contract="sales-prospector:prospect-actions-v1-4",
                idempotency_key=args.idempotency_key.strip(),
                revision=args.plan_revision,
                source_agent=SOURCE_AGENT,
                source_run_id=args.source_run_id,
                metadata={"csv": str(args.csv), "aggregateExpectedSlots": frozen_expected_slots},
            )
            if journal.value["metadata"].get("aggregateExpectedSlots") != frozen_expected_slots:
                raise ValueError("aggregateExpectedSlots se mezi fázemi změnily")
            expected_slots.update(
                str(item.get("slot"))
                for item in journal.value.get("actions", [])
                if isinstance(item, dict) and item.get("slot")
            )
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        except Exception as exc:
            print(json.dumps({"ok": False, "code": getattr(exc, "code", "artifact_failed"),
                              "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 4

    for row in valid_rows:
        market = (row.get("Market") or "CZ").strip().upper()
        email = (row.get("Email") or "").strip()
        phone = (row.get("Phone") or "").strip()
        provided_contact_id = (row.get("ContactId") or "").strip()
        state, contact, reason, _lookup_completed_at = lookup_contact(
            email,
            phone,
            profile=args.credential_profile,
            contact_id=provided_contact_id,
            market=market,
        )
        if state == "unknown":
            counts["unknown"] += 1
            errors.append({"csv_row": row.get("_csv_row"), "company": row.get("Company"), "error": reason})
            continue

        if state == "not_found":
            counts["not_found_file_only"] += 1
            continue
        else:
            contact_id = str((contact or {}).get("id") or "").strip()
            if not contact_id:
                counts["unknown"] += 1
                errors.append({"csv_row": row.get("_csv_row"), "company": row.get("Company"),
                               "error": "Přesná shoda nemá contactId"})
                continue
            counts["would_tag_existing"] += 1
            slot = _request_slot("tags-add", contact_id, args.credential_profile)
            expected_slots.add(slot)
            if not create_plan:
                continue
            action_type = "sales.ghl.tags.add.v1"
            assert client is not None
            payload = {**client.contact_identity_fields(contact or {}, contact_id), "tags": tags}

        try:
            assert journal is not None
            if slot not in frozen_expected_slots:
                raise ValueError(f"slot {slot} chybí ve frozen --expected-slot plánu")
            expected_slots.add(slot)
            record = journal.add_action(
                slot=slot,
                action_type=action_type,
                payload=payload,
                source_run_id=args.source_run_id,
                credential_profile=args.credential_profile,
                detail={"csvRow": int(row.get("_csv_row") or 0), "company": row.get("Company") or ""},
            )
            summary = _action_summary(record)
            summary.update({"csv_row": row.get("_csv_row"), "company": row.get("Company")})
            results.append(summary)
            if summary["reused"]:
                counts["reused"] += 1
            else:
                counts["planned_tags"] += 1
        except Exception as exc:
            errors.append({
                "csv_row": row.get("_csv_row"),
                "company": row.get("Company"),
                "code": getattr(exc, "code", "plan_failed"),
                "error": str(exc),
            })

    artifact_complete = False
    if journal is not None and results and not errors:
        journal.finish(frozen_expected_slots)
        artifact_complete = True
    output = {
        "dry_run": not create_plan,
        "direct_provider_writes": 0,
        "total_rows": len(rows),
        "valid": len(valid_rows),
        "skipped": sum(skip_reasons.values()),
        "skip_reasons": skip_reasons,
        **counts,
        "actions": results,
        "planned_slots": sorted(expected_slots),
        "plan_artifact": args.plan_artifact if create_plan else None,
        "plan_complete": artifact_complete,
        "plan_sha256": journal.value.get("planSha256") if journal is not None else None,
        "errors": errors[:50],
        "note": (
            "Kontakty nenalezené v CRM zůstávají pouze ve file/review výstupu; skill je nevytváří. "
            "Existující kontakty mohou dostat jen aditivní tag po schválení exact SHA celého plánu."
        ),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if not create_plan:
        return 0 if counts["unknown"] == 0 else 2
    return 0 if artifact_complete and not errors else 4


if __name__ == "__main__":
    raise SystemExit(main())
