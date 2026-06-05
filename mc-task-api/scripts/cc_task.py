#!/usr/bin/env python3
"""Small Control Center API helper for agents.

The goal is to keep agents away from hand-built shell JSON. It intentionally
uses only the Python standard library so it works in the OpenClaw runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


ACTIVE_TASK_STATUSES = {
    "inbox",
    "assigned",
    "in_progress",
    "review",
    "quality_review",
    "done",
    "blocked",
}


def read_text(value: str | None, file_path: str | None) -> str | None:
    if value is not None:
        return value
    if file_path is None:
        return None
    if file_path == "-":
        return sys.stdin.read()
    with open(file_path, "r", encoding="utf-8") as handle:
        return handle.read()


def parse_json_object(raw: str | None, name: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{name} must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise SystemExit(f"{name} must be a JSON object")
    return parsed


def tags_from_args(values: list[str] | None) -> list[str]:
    tags: list[str] = []
    for value in values or []:
        for item in value.split(","):
            tag = item.strip()
            if tag and tag not in tags:
                tags.append(tag)
    return tags


def base_url() -> str:
    url = os.environ.get("CC_URL", "").strip()
    if not url:
        raise SystemExit("CC_URL is not set")
    return url.rstrip("/")


def api_key() -> str:
    key = os.environ.get("CC_API_KEY", "").strip()
    if not key:
        raise SystemExit("CC_API_KEY is not set")
    return key


def api_request(method: str, path: str, payload: dict[str, Any] | None = None, query: dict[str, Any] | None = None) -> dict[str, Any]:
    query_string = ""
    if query:
        query_string = "?" + urllib.parse.urlencode({key: value for key, value in query.items() if value is not None})
    request = urllib.request.Request(
        f"{base_url()}{path}{query_string}",
        method=method,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key(),
        },
    )
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        with urllib.request.urlopen(request, data=data, timeout=60) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(json.dumps({"ok": False, "status": exc.code, "error": body}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1) from exc
    except urllib.error.URLError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1) from exc

    if not body.strip():
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        print(body, file=sys.stderr)
        raise SystemExit(f"Control Center returned invalid JSON: {exc}") from exc


def find_task_by_idempotency_key(key: str, assigned_to: str | None) -> dict[str, Any] | None:
    query: dict[str, Any] = {"limit": 200}
    if assigned_to:
        query["assigned_to"] = assigned_to
    response = api_request("GET", "/api/tasks", query=query)
    for task in response.get("tasks", []):
        metadata = task.get("metadata") if isinstance(task, dict) else None
        status = str(task.get("status", "")).lower() if isinstance(task, dict) else ""
        if isinstance(metadata, dict) and metadata.get("idempotency_key") == key and status in ACTIVE_TASK_STATUSES:
            return task
    return None


def cmd_create_task(args: argparse.Namespace) -> dict[str, Any]:
    metadata = parse_json_object(args.metadata_json, "--metadata-json")
    if args.idempotency_key:
        metadata["idempotency_key"] = args.idempotency_key
        existing = find_task_by_idempotency_key(args.idempotency_key, args.assigned_to)
        if existing:
            return {"task": existing, "reused": True}

    payload: dict[str, Any] = {
        "title": args.title,
        "status": args.status,
        "priority": args.priority,
        "tags": tags_from_args(args.tag),
        "metadata": metadata,
    }
    optional_fields = {
        "description": read_text(args.description, args.description_file),
        "assigned_to": args.assigned_to,
        "created_by": args.created_by,
        "due_date": args.due_date,
        "estimated_hours": args.estimated_hours,
        "parent_task_id": args.parent_task_id,
        "depends_on": args.depends_on,
        "project_id": args.project_id,
    }
    payload.update({key: value for key, value in optional_fields.items() if value is not None})
    return api_request("POST", "/api/tasks", payload=payload)


def cmd_update_task(args: argparse.Namespace) -> dict[str, Any]:
    metadata = parse_json_object(args.metadata_json, "--metadata-json") if args.metadata_json else None
    payload: dict[str, Any] = {}
    for key in ("title", "status", "priority", "assigned_to", "actual_hours"):
        value = getattr(args, key)
        if value is not None:
            payload[key] = value
    description = read_text(args.description, args.description_file)
    if description is not None:
        payload["description"] = description
    if args.tag:
        payload["tags"] = tags_from_args(args.tag)
    if metadata is not None:
        payload["metadata"] = metadata
    if not payload:
        raise SystemExit("No update fields provided")
    return api_request("PUT", f"/api/tasks/{args.task_id}", payload=payload)


def cmd_get_task(args: argparse.Namespace) -> dict[str, Any]:
    return api_request("GET", f"/api/tasks/{args.task_id}")


def cmd_create_deliverable(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task_id": args.task_id,
        "title": args.title,
        "type": args.type,
    }
    optional_fields = {
        "content": read_text(args.content, args.content_file),
        "file_path": args.file_path,
        "created_by": args.created_by,
        "project_id": args.project_id,
    }
    payload.update({key: value for key, value in optional_fields.items() if value is not None})
    return api_request("POST", "/api/deliverables", payload=payload)


def add_common_task_fields(parser: argparse.ArgumentParser, *, include_title: bool = True) -> None:
    if include_title:
        parser.add_argument("--title")
    parser.add_argument("--description")
    parser.add_argument("--description-file")
    parser.add_argument("--status", choices=["inbox", "assigned", "in_progress", "review", "quality_review", "done", "failed", "blocked", "cancelled"])
    parser.add_argument("--priority", choices=["critical", "high", "medium", "low"])
    parser.add_argument("--assigned-to", dest="assigned_to")
    parser.add_argument("--tag", action="append")
    parser.add_argument("--metadata-json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Control Center task helper")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-task", help="Create a task with safe JSON encoding")
    add_common_task_fields(create, include_title=False)
    create.add_argument("--title", required=True)
    create.set_defaults(status="assigned", priority="medium")
    create.add_argument("--created-by", dest="created_by")
    create.add_argument("--due-date", dest="due_date", type=int)
    create.add_argument("--estimated-hours", dest="estimated_hours", type=float)
    create.add_argument("--parent-task-id", dest="parent_task_id", type=int)
    create.add_argument("--depends-on", dest="depends_on")
    create.add_argument("--project-id", dest="project_id", type=int)
    create.add_argument("--idempotency-key", dest="idempotency_key")
    create.set_defaults(func=cmd_create_task)

    update = sub.add_parser("update-task", help="Update a task with safe JSON encoding")
    update.add_argument("task_id", type=int)
    add_common_task_fields(update)
    update.add_argument("--actual-hours", dest="actual_hours", type=float)
    update.set_defaults(func=cmd_update_task)

    get_task = sub.add_parser("get-task", help="Fetch one task")
    get_task.add_argument("task_id", type=int)
    get_task.set_defaults(func=cmd_get_task)

    deliverable = sub.add_parser("create-deliverable", help="Create a task deliverable")
    deliverable.add_argument("--task-id", dest="task_id", type=int, required=True)
    deliverable.add_argument("--title", required=True)
    deliverable.add_argument("--type", default="file", choices=["text", "report", "file", "link"])
    deliverable.add_argument("--content")
    deliverable.add_argument("--content-file")
    deliverable.add_argument("--file-path", dest="file_path")
    deliverable.add_argument("--created-by", dest="created_by")
    deliverable.add_argument("--project-id", dest="project_id", type=int)
    deliverable.set_defaults(func=cmd_create_deliverable)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    result = args.func(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
