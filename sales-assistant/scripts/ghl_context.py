#!/usr/bin/env python3
"""Fetch or normalize one read-only CRM context snapshot.

This helper intentionally has no provider HTTP or credential surface. The
snapshot can be supplied by task handoff or fetched through the selected tenant
GHL integration. It validates the selected contact and produces the compact
bundle consumed by Sales Assistant.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
SHARED_LIB = SCRIPT_PATH.parents[2] / "_lib"


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
    raise RuntimeError("sdílený Sales GHL read klient není dostupný")


def _read_object(path: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"context snapshot není čitelný validní JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("context snapshot musí být JSON objekt")
    return value


def _contact(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not value.get("id"):
        raise ValueError("context snapshot neobsahuje jednoznačný contact.id")
    return {
        "id": value.get("id"),
        "name": value.get("contactName") or value.get("name") or " ".join(
            str(part) for part in (value.get("firstName"), value.get("lastName")) if part
        ).strip(),
        "firstName": value.get("firstName"),
        "lastName": value.get("lastName"),
        "email": value.get("email"),
        "phone": value.get("phone"),
        "company": value.get("companyName") or value.get("company"),
        "dnd": bool(value.get("dnd")),
        "tags": list(value.get("tags") or []),
        "customFields": list(value.get("customFields") or []),
        "dateAdded": value.get("dateAdded"),
        "lastActivity": value.get("lastActivity"),
    }


def _list(value: Any) -> list[dict[str, Any]]:
    return [item for item in (value or []) if isinstance(item, dict)] if isinstance(value, list) else []


def normalize(snapshot: dict[str, Any], contact_id: str | None, email: str | None) -> dict[str, Any]:
    contact = _contact(snapshot.get("contact"))
    if contact_id and contact["id"] != contact_id:
        raise ValueError("contact.id v snapshotu neodpovídá --contact")
    if email and str(contact.get("email") or "").strip().lower() != email.strip().lower():
        raise ValueError("contact.email v snapshotu neodpovídá --email")

    notes = _list(snapshot.get("notes"))
    notes.sort(key=lambda item: str(item.get("createdAt") or item.get("dateAdded") or ""), reverse=True)
    opportunities = _list(snapshot.get("opportunities"))
    orders = _list(snapshot.get("orders"))
    appointments = _list(snapshot.get("appointments"))

    def is_scout(note: dict[str, Any]) -> bool:
        body = str(note.get("body") or "")
        return "🔎" in body[:40] and "scout brief" in body[:200].lower()

    scout = next((note for note in notes if is_scout(note)), None)
    return {
        "contact": contact,
        "opportunities": opportunities,
        "open_opportunities": [item for item in opportunities if item.get("status") == "open"],
        "notes": notes,
        "scout_brief_note_id": (scout or {}).get("id"),
        "orders": orders,
        "appointments": appointments,
        "counts": {
            "notes": len(notes),
            "opportunities": len(opportunities),
            "orders": len(orders),
            "appointments": len(appointments),
        },
        "warnings": snapshot.get("warnings") if isinstance(snapshot.get("warnings"), (dict, list)) else {},
        "partial": bool(snapshot.get("partial")),
        "source": "tenant-ghl:contact.context" if snapshot.get("resource") == "contact.context" else "provided-read-snapshot",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch or normalize one read-only contact context")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--context-file")
    source.add_argument("--fetch-contact-id", help="načte bounded contact context z tenantní GHL integrace")
    parser.add_argument("--credential-profile", default="default")
    parser.add_argument("--contact", help="expected exact contact ID")
    parser.add_argument("--email", help="expected exact contact email")
    parser.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.fetch_contact_id:
            snapshot = _sales_plan().lookup_contact_context(
                args.fetch_contact_id,
                profile=args.credential_profile,
            )
            bundle = normalize(snapshot, args.fetch_contact_id, args.email)
        else:
            bundle = normalize(_read_object(args.context_file), args.contact, args.email)
    except ValueError as exc:
        print(json.dumps({"ok": False, "code": "invalid_context", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3
    except Exception as exc:
        print(json.dumps({"ok": False, "code": getattr(exc, "code", "context_fetch_failed"),
                          "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    output = json.dumps(bundle, ensure_ascii=False)
    if args.output:
        _sales_plan().write_artifact(args.output, bundle)
        print(json.dumps({"ok": True, "contactId": bundle["contact"]["id"], "output": args.output}, ensure_ascii=False))
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
