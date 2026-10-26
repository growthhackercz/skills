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
import uuid
from typing import Any


CANCELLABLE_TASK_STATUSES = (
    "inbox", "assigned", "in_progress", "review", "quality_review", "blocked",
)
BULK_CANCEL_BATCH_SIZE = 100
WAKEABLE_TASK_STATUSES = ("inbox", "assigned", "in_progress", "blocked")
# `interrupted` = Control Center still holds a run claim the runtime no longer runs.
WAKEABLE_RUN_STATES = ("idle", "interrupted")


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
            if method == "HEAD" and path == "/api/tasks":
                return {
                    "task_idempotency_version": response.headers.get("x-cc-task-idempotency"),
                    "task_bulk_cancellation_version": response.headers.get("x-cc-task-bulk-cancellation"),
                }
            if method == "HEAD" and path.endswith("/progress"):
                return {"task_progress_version": response.headers.get("x-cc-task-progress")}
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


def cmd_create_task(args: argparse.Namespace) -> dict[str, Any]:
    metadata = parse_json_object(args.metadata_json, "--metadata-json")
    if args.idempotency_key is not None:
        metadata["idempotency_key"] = args.idempotency_key
    if "idempotency_key" in metadata:
        capabilities = api_request("HEAD", "/api/tasks")
        if capabilities.get("task_idempotency_version") != "1":
            raise SystemExit("Control Center does not advertise server task idempotency. Update the API before using this helper; no task was created.")

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


def cmd_list_tasks(args: argparse.Namespace) -> dict[str, Any]:
    result = api_request("GET", "/api/tasks", query={
        "assigned_to": args.assigned_to,
        "status": args.status,
        "limit": args.limit,
        "offset": args.offset,
    })
    if not isinstance(result.get("tasks"), list):
        print(json.dumps({"ok": False, "error": "Control Center response has no tasks list"}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
    return result


def cmd_add_comment(args: argparse.Namespace) -> dict[str, Any]:
    content = read_text(args.content, args.content_file)
    if content is None or not content.strip():
        raise SystemExit("Comment content must not be empty")
    payload: dict[str, Any] = {"content": content}
    if args.author is not None:
        payload["author"] = args.author
    if args.parent_id is not None:
        payload["parent_id"] = args.parent_id
    return api_request("POST", f"/api/tasks/{args.task_id}/comments", payload=payload)


def cmd_cancel_task(args: argparse.Namespace) -> dict[str, Any]:
    return api_request(
        "POST",
        f"/api/tasks/{args.task_id}/cancel",
        payload={"operation_id": args.operation_id or str(uuid.uuid4())},
    )


def normalize_task_snapshots(payload: Any) -> list[dict[str, Any]]:
    records = payload.get("tasks") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise SystemExit("Task snapshot must be a JSON list or an object with tasks[]")
    snapshots: list[dict[str, Any]] = []
    seen: set[int] = set()
    for record in records:
        if not isinstance(record, dict):
            raise SystemExit("Every task snapshot must be a JSON object")
        task_id = record.get("id")
        status = record.get("status", record.get("expected_status"))
        updated_at = record.get("updated_at", record.get("expected_updated_at"))
        if not isinstance(task_id, int) or isinstance(task_id, bool) or task_id <= 0:
            raise SystemExit("Every task snapshot requires a positive integer id")
        if status not in CANCELLABLE_TASK_STATUSES:
            raise SystemExit(f"Task {task_id} is not in a cancellable status")
        if not isinstance(updated_at, int) or isinstance(updated_at, bool) or updated_at < 0:
            raise SystemExit(f"Task {task_id} requires integer updated_at")
        if task_id in seen:
            raise SystemExit(f"Duplicate task id in snapshot: {task_id}")
        seen.add(task_id)
        snapshots.append({
            "id": task_id,
            "expected_status": status,
            "expected_updated_at": updated_at,
        })
    snapshots.sort(key=lambda item: item["id"])
    if not snapshots:
        raise SystemExit("Task snapshot is empty")
    return snapshots


def snapshots_from_file(file_path: str) -> list[dict[str, Any]]:
    raw = read_text(None, file_path)
    try:
        payload = json.loads(raw or "")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--tasks-file must contain valid JSON: {exc}") from exc
    return normalize_task_snapshots(payload)


def snapshots_from_filter(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.created_before is None and args.updated_before is None:
        raise SystemExit("Filtered bulk cancellation requires --created-before or --updated-before")
    records: list[dict[str, Any]] = []
    offset = 0
    while True:
        page = api_request("GET", "/api/tasks", query={
            "status": args.status,
            "limit": 200,
            "offset": offset,
        })
        tasks = page.get("tasks")
        if not isinstance(tasks, list):
            raise SystemExit("Control Center task list response is missing tasks[]")
        for task in tasks:
            if not isinstance(task, dict):
                continue
            created_at = task.get("created_at")
            updated_at = task.get("updated_at")
            if args.created_before is not None and (
                not isinstance(created_at, int) or created_at >= args.created_before
            ):
                continue
            if args.updated_before is not None and (
                not isinstance(updated_at, int) or updated_at >= args.updated_before
            ):
                continue
            records.append(task)
        offset += len(tasks)
        total = page.get("total")
        if len(tasks) == 0 or (isinstance(total, int) and offset >= total) or len(tasks) < 200:
            break
    return normalize_task_snapshots(records)


def cmd_cancel_tasks(args: argparse.Namespace) -> dict[str, Any]:
    capabilities = api_request("HEAD", "/api/tasks")
    if capabilities.get("task_bulk_cancellation_version") != "1":
        raise SystemExit("Control Center does not advertise bulk task cancellation; no task was changed")
    snapshots = snapshots_from_file(args.tasks_file) if args.tasks_file else snapshots_from_filter(args)
    operation_id = args.operation_id or str(uuid.uuid4())
    print(json.dumps({
        "phase": "bulk_cancel_start",
        "operation_id": operation_id,
        "task_count": len(snapshots),
        "dry_run": args.dry_run,
    }, ensure_ascii=False), file=sys.stderr)
    batches = []
    for offset in range(0, len(snapshots), BULK_CANCEL_BATCH_SIZE):
        batch = snapshots[offset:offset + BULK_CANCEL_BATCH_SIZE]
        batches.append(api_request("POST", "/api/tasks/cancel", payload={
            "operation_id": operation_id,
            "tasks": batch,
            "dry_run": args.dry_run,
            **({"note": args.note} if args.note else {}),
        }))
    expected_outcome = "ready" if args.dry_run else "cancelled"
    outcome = expected_outcome if all(batch.get("outcome") == expected_outcome for batch in batches) else "partial"
    return {
        "outcome": outcome,
        "operation_id": operation_id,
        "dry_run": args.dry_run,
        "task_count": len(snapshots),
        "batches": batches,
    }


def cmd_save_progress(args: argparse.Namespace) -> dict[str, Any]:
    progress = parse_json_object(read_text(None, args.progress_file), "--progress-file")
    path = f"/api/tasks/{args.task_id}/progress"
    if api_request("HEAD", path).get("task_progress_version") != "1":
        raise SystemExit("Task progress is not available. No progress or task was changed.")
    return api_request("POST", path, payload={
        "run_id": args.run_id, "generation": args.generation, "request_id": args.request_id,
        "expected_revision": args.expected_revision, "progress": progress,
    })


def cmd_resume_task(args: argparse.Namespace) -> dict[str, Any]:
    clarification = read_text(args.clarification, args.clarification_file)
    payload: dict[str, Any] = {
        "operation_id": args.operation_id or str(uuid.uuid4()),
        "decision": "resume",
    }
    if clarification is not None:
        payload["clarification"] = clarification.strip()
    return api_request(
        "POST",
        f"/api/tasks/{args.task_id}/execution-decision",
        payload=payload,
    )


def cmd_run_state(args: argparse.Namespace) -> dict[str, Any]:
    return api_request("GET", f"/api/tasks/{args.task_id}/run-control")


def cmd_wake_task(args: argparse.Namespace) -> dict[str, Any]:
    """Wake the assignee of an existing task; report only what Control Center accepted.

    A comment, a priority/due-date change or a repeated move to in_progress does
    not start the assignee. This is the explicit path, guarded against stacking a
    second run on a task that is already running.
    """
    message = read_text(args.message, args.message_file)
    if message is None or not message.strip():
        raise SystemExit("Wake message must not be empty")

    task_response = api_request("GET", f"/api/tasks/{args.task_id}")
    task = task_response.get("task") if isinstance(task_response, dict) else None
    if not isinstance(task, dict) or task.get("id") != args.task_id:
        raise SystemExit("Control Center response has no matching task")
    assignee = task.get("assigned_to")
    if not isinstance(assignee, str) or not assignee.strip():
        raise SystemExit("Task has no assignee to wake")
    if task.get("status") not in WAKEABLE_TASK_STATUSES:
        raise SystemExit(f"Task in status {task.get('status')} cannot be woken; use its review or operator flow")

    run_control = api_request("GET", f"/api/tasks/{args.task_id}/run-control")
    state = run_control.get("state") if isinstance(run_control, dict) else None
    result: dict[str, Any] = {"task_id": args.task_id, "agent": assignee, "run_state": state}
    if state not in WAKEABLE_RUN_STATES:
        return {**result, "wake_accepted": False, "reason": f"run_{state or 'unknown'}"}

    woke = api_request("POST", "/api/agents/wake", payload={
        "agent_name": assignee,
        "task_id": args.task_id,
        "message": message.strip(),
    })
    execution = woke.get("execution") if isinstance(woke, dict) else None
    outcome = execution.get("outcome") if isinstance(execution, dict) else None
    run_id = execution.get("runId") if isinstance(execution, dict) else None
    if outcome == "intake_recorded":
        return {**result, "wake_accepted": True, "run_id": run_id}
    return {**result, "wake_accepted": False, "reason": outcome or "no_execution", "run_id": run_id}


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


def cmd_request_review_checkpoint(args: argparse.Namespace) -> dict[str, Any]:
    """Persist one retry-safe operator checkpoint and expose the task in review."""
    content = read_text(args.content, args.content_file)
    if content is None or not content.strip():
        raise SystemExit("Checkpoint content must not be empty")

    task_response = api_request("GET", f"/api/tasks/{args.task_id}")
    task = task_response.get("task") if isinstance(task_response, dict) else None
    if not isinstance(task, dict) or task.get("id") != args.task_id:
        raise SystemExit("Control Center response has no matching task")
    if task.get("status") not in ("in_progress", "review"):
        raise SystemExit("Review checkpoint requires a task in in_progress or review")

    listed = api_request(
        "GET",
        "/api/deliverables",
        query={"task_id": args.task_id, "limit": 100},
    )
    deliverables = listed.get("deliverables") if isinstance(listed, dict) else None
    if not isinstance(deliverables, list):
        raise SystemExit("Control Center response has no deliverables list")

    same_title = [
        item for item in deliverables
        if isinstance(item, dict) and item.get("title") == args.title
    ]
    exact = [
        item for item in same_title
        if item.get("task_id") == args.task_id
        and item.get("type") == "text"
        and item.get("content") == content
        and item.get("created_by") == args.created_by
    ]
    if len(exact) > 1:
        raise SystemExit("Checkpoint deliverable is duplicated; stop for operator repair")
    if same_title and not exact:
        raise SystemExit("Checkpoint title already exists with different content")

    reused = len(exact) == 1
    if reused:
        deliverable = exact[0]
    else:
        created = api_request("POST", "/api/deliverables", payload={
            "task_id": args.task_id,
            "title": args.title,
            "type": "text",
            "content": content,
            "created_by": args.created_by,
        })
        deliverable = created.get("deliverable") if isinstance(created, dict) else None
        if not isinstance(deliverable, dict) or deliverable.get("task_id") != args.task_id:
            raise SystemExit("Control Center did not confirm the checkpoint deliverable")

    refreshed_response = api_request("GET", f"/api/tasks/{args.task_id}")
    refreshed = refreshed_response.get("task") if isinstance(refreshed_response, dict) else None
    if not isinstance(refreshed, dict) or refreshed.get("id") != args.task_id:
        raise SystemExit("Control Center did not return the checkpoint task")

    status_changed = False
    if refreshed.get("status") == "in_progress":
        updated = api_request("PUT", f"/api/tasks/{args.task_id}", payload={"status": "review"})
        refreshed = updated.get("task") if isinstance(updated, dict) else None
        status_changed = True
    if not isinstance(refreshed, dict) or refreshed.get("status") != "review":
        raise SystemExit("Checkpoint task did not converge to review")

    return {
        "task": refreshed,
        "deliverable": deliverable,
        "deliverable_reused": reused,
        "status_changed": status_changed,
    }


TASK_STATUSES = ["inbox", "assigned", "in_progress", "review", "quality_review", "done", "failed", "blocked"]
CREATE_TASK_STATUSES = ["inbox", "assigned", "in_progress"]


def add_common_task_fields(
    parser: argparse.ArgumentParser,
    *,
    include_title: bool = True,
    allowed_statuses: list[str] = TASK_STATUSES,
) -> None:
    if include_title:
        parser.add_argument("--title")
    parser.add_argument("--description")
    parser.add_argument("--description-file")
    parser.add_argument("--status", choices=allowed_statuses)
    parser.add_argument("--priority", choices=["critical", "high", "medium", "low"])
    parser.add_argument("--assigned-to", dest="assigned_to")
    parser.add_argument("--tag", action="append")
    parser.add_argument("--metadata-json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Control Center task helper")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-task", help="Create a task with safe JSON encoding")
    add_common_task_fields(create, include_title=False, allowed_statuses=CREATE_TASK_STATUSES)
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

    list_tasks = sub.add_parser("list-tasks", help="List tasks; fails loudly instead of returning an empty list on API errors")
    list_tasks.add_argument("--assigned-to", dest="assigned_to")
    list_tasks.add_argument("--status", help="Comma-separated statuses, e.g. inbox,assigned,in_progress")
    list_tasks.add_argument("--limit", type=int, default=50)
    list_tasks.add_argument("--offset", type=int)
    list_tasks.set_defaults(func=cmd_list_tasks)

    add_comment = sub.add_parser("add-comment", help="Add a task comment with safe JSON encoding")
    add_comment.add_argument("task_id", type=int)
    comment_content = add_comment.add_mutually_exclusive_group(required=True)
    comment_content.add_argument("--content")
    comment_content.add_argument("--content-file")
    add_comment.add_argument("--author")
    add_comment.add_argument("--parent-id", dest="parent_id", type=int)
    add_comment.set_defaults(func=cmd_add_comment)

    cancel_task = sub.add_parser("cancel-task", help="Safely cancel one task and its active execution")
    cancel_task.add_argument("task_id", type=int)
    cancel_task.add_argument("--operation-id")
    cancel_task.set_defaults(func=cmd_cancel_task)

    cancel_tasks = sub.add_parser("cancel-tasks", help="Safely cancel exact task snapshots in batches")
    selection = cancel_tasks.add_mutually_exclusive_group(required=True)
    selection.add_argument("--tasks-file")
    selection.add_argument("--status", choices=CANCELLABLE_TASK_STATUSES)
    cancel_tasks.add_argument("--created-before", type=int)
    cancel_tasks.add_argument("--updated-before", type=int)
    cancel_tasks.add_argument("--operation-id")
    cancel_tasks.add_argument("--note")
    cancel_tasks.add_argument("--dry-run", action="store_true")
    cancel_tasks.set_defaults(func=cmd_cancel_tasks)

    progress = sub.add_parser("save-progress", help="Save bounded progress for the exact dispatched task run")
    progress.add_argument("task_id", type=int)
    progress.add_argument("--run-id", required=True)
    progress.add_argument("--generation", type=int, required=True)
    progress.add_argument("--request-id", required=True)
    progress.add_argument("--expected-revision", type=int, required=True)
    progress.add_argument("--progress-file", required=True)
    progress.set_defaults(func=cmd_save_progress)

    resume_task = sub.add_parser("resume-task", help="Explicitly resume an operator-stopped task")
    resume_task.add_argument("task_id", type=int)
    resume_task.add_argument("--clarification")
    resume_task.add_argument("--clarification-file")
    resume_task.add_argument("--operation-id")
    resume_task.set_defaults(func=cmd_resume_task)

    run_state = sub.add_parser("run-state", help="Show whether the task assignee is running on the task right now")
    run_state.add_argument("task_id", type=int)
    run_state.set_defaults(func=cmd_run_state)

    wake_task = sub.add_parser("wake-task", help="Wake the assignee of an existing task with a new concrete instruction")
    wake_task.add_argument("task_id", type=int)
    wake_message = wake_task.add_mutually_exclusive_group(required=True)
    wake_message.add_argument("--message")
    wake_message.add_argument("--message-file")
    wake_task.set_defaults(func=cmd_wake_task)

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

    checkpoint = sub.add_parser(
        "request-review-checkpoint",
        help="Idempotently persist an operator checkpoint and expose the task in review",
    )
    checkpoint.add_argument("--task-id", dest="task_id", type=int, required=True)
    checkpoint.add_argument("--title", required=True)
    checkpoint_content = checkpoint.add_mutually_exclusive_group(required=True)
    checkpoint_content.add_argument("--content")
    checkpoint_content.add_argument("--content-file")
    checkpoint.add_argument("--created-by", dest="created_by", required=True)
    checkpoint.set_defaults(func=cmd_request_review_checkpoint)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    result = args.func(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
