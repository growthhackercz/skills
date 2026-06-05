#!/usr/bin/env python3
"""Safe Asana REST API helper for OpenClaw skills.

Credentials are resolved from environment variables first and then from Control
Center's credential store. The PAT is sent only in an Authorization header.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_BASE = "https://app.asana.com/api/1.0"
TIMEOUT_SECONDS = 30
USER_AGENT = "cliqsales-asana-skill/1.0"


def _load_cc_variable():
    script_path = Path(__file__).resolve()
    skill_dir = script_path.parents[1]
    candidates: list[Path] = [skill_dir.parent / "_lib"]

    for env_name in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw_home = os.environ.get(env_name, "").strip()
        if raw_home:
            home = Path(raw_home).expanduser()
            candidates.append(home / "cs-skills" / "_lib")
            candidates.append(home / ".openclaw" / "cs-skills" / "_lib")

    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
    candidates.extend(parent / "cs-skills" / "_lib" for parent in script_path.parents)

    seen: set[str] = set()
    for lib_dir in candidates:
        key = str(lib_dir)
        if key in seen or not (lib_dir / "cc_credentials.py").exists():
            continue
        seen.add(key)
        if key not in sys.path:
            sys.path.insert(0, key)
        try:
            from cc_credentials import get_env_or_variable  # type: ignore
        except Exception:
            continue
        return get_env_or_variable
    return None


def credential(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    get_env_or_variable = _load_cc_variable()
    if not get_env_or_variable:
        return ""
    return str(get_env_or_variable(name) or "").strip()


def config_path() -> Path:
    return Path.home() / ".openclaw" / "asana" / "config.json"


def read_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_config(data: dict[str, Any]) -> None:
    allowed = {
        "default_workspace": str(data.get("default_workspace") or "").strip(),
    }
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(allowed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def default_workspace() -> str:
    return str(read_config().get("default_workspace") or "").strip()


def build_url(path: str, params: dict[str, Any] | None = None) -> str:
    if not path.startswith("/"):
        path = "/" + path
    url = API_BASE + path
    clean_params = {
        key: value
        for key, value in (params or {}).items()
        if value is not None and str(value) != ""
    }
    if clean_params:
        url = f"{url}?{urllib.parse.urlencode(clean_params, doseq=True)}"
    return url


def request_json(
    method: str,
    path: str,
    token: str,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        build_url(path, params),
        data=payload,
        method=method,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"Asana API HTTP {exc.code} for {method} {path}", file=sys.stderr)
        if detail:
            print(detail[:1000], file=sys.stderr)
        raise SystemExit(2) from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"Asana network error: {exc.reason}") from None

    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Asana returned invalid JSON for {method} {path}: {exc}") from None


def print_json(data: Any) -> int:
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def workspace_arg(value: str | None) -> str:
    selected = (value or "").strip() or default_workspace()
    if not selected:
        raise SystemExit("Missing workspace. Pass --workspace <gid> or set a default workspace.")
    return selected


def add_common_fields(params: dict[str, Any]) -> dict[str, Any]:
    params.setdefault("limit", 100)
    params.setdefault(
        "opt_fields",
        "gid,name,resource_type,completed,assignee.name,due_on,permalink_url,projects.name,workspace.name",
    )
    return params


def main() -> int:
    parser = argparse.ArgumentParser(description="Call Asana REST API with Control Center credentials.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("me")
    sub.add_parser("workspaces", aliases=["list-workspaces"])

    set_default = sub.add_parser("set-default-workspace")
    set_default.add_argument("--workspace", required=True)

    projects = sub.add_parser("projects")
    projects.add_argument("--workspace")

    tasks_project = sub.add_parser("tasks-in-project")
    tasks_project.add_argument("--project", required=True)

    tasks_assigned = sub.add_parser("tasks-assigned")
    tasks_assigned.add_argument("--workspace")
    tasks_assigned.add_argument("--assignee", default="me")

    search = sub.add_parser("search-tasks")
    search.add_argument("--workspace")
    search.add_argument("--text", required=True)

    task = sub.add_parser("task")
    task.add_argument("task_gid")

    update = sub.add_parser("update-task")
    update.add_argument("task_gid")
    update.add_argument("--name")
    update.add_argument("--notes")
    update.add_argument("--completed", choices=["true", "false"])
    update.add_argument("--assignee")
    update.add_argument("--due-on")

    complete = sub.add_parser("complete-task")
    complete.add_argument("task_gid")

    comment = sub.add_parser("comment")
    comment.add_argument("task_gid")
    comment.add_argument("--text", required=True)

    create = sub.add_parser("create-task")
    create.add_argument("--workspace")
    create.add_argument("--name", required=True)
    create.add_argument("--notes")
    create.add_argument("--project")
    create.add_argument("--assignee")
    create.add_argument("--due-on")

    args = parser.parse_args()
    token = credential("ASANA_PAT")
    if not token:
        print("ERROR: Missing ASANA_PAT. Configure Asana in Control Center > Integrations.", file=sys.stderr)
        return 65

    cmd = args.command
    if cmd == "me":
        return print_json(request_json("GET", "/users/me", token))
    if cmd in {"workspaces", "list-workspaces"}:
        return print_json(request_json("GET", "/workspaces", token, {"limit": 100}))
    if cmd == "set-default-workspace":
        write_config({"default_workspace": args.workspace})
        return print_json({"ok": True, "default_workspace": args.workspace, "config": str(config_path())})
    if cmd == "projects":
        return print_json(request_json("GET", "/projects", token, add_common_fields({"workspace": workspace_arg(args.workspace)})))
    if cmd == "tasks-in-project":
        return print_json(request_json("GET", f"/projects/{urllib.parse.quote(args.project)}/tasks", token, add_common_fields({})))
    if cmd == "tasks-assigned":
        return print_json(request_json("GET", "/tasks", token, add_common_fields({
            "workspace": workspace_arg(args.workspace),
            "assignee": args.assignee,
        })))
    if cmd == "search-tasks":
        workspace = workspace_arg(args.workspace)
        return print_json(request_json("GET", f"/workspaces/{urllib.parse.quote(workspace)}/tasks/search", token, add_common_fields({"text": args.text})))
    if cmd == "task":
        return print_json(request_json("GET", f"/tasks/{urllib.parse.quote(args.task_gid)}", token, {
            "opt_fields": "gid,name,notes,completed,assignee.name,due_on,permalink_url,projects.name,workspace.name,created_at,modified_at",
        }))
    if cmd == "update-task":
        data: dict[str, Any] = {}
        for field in ["name", "notes", "assignee", "due_on"]:
            value = getattr(args, field.replace("-", "_"), None)
            if value is not None:
                data[field] = value
        if args.completed is not None:
            data["completed"] = args.completed == "true"
        if not data:
            raise SystemExit("No update fields supplied.")
        return print_json(request_json("PUT", f"/tasks/{urllib.parse.quote(args.task_gid)}", token, body={"data": data}))
    if cmd == "complete-task":
        return print_json(request_json("PUT", f"/tasks/{urllib.parse.quote(args.task_gid)}", token, body={"data": {"completed": True}}))
    if cmd == "comment":
        return print_json(request_json("POST", f"/tasks/{urllib.parse.quote(args.task_gid)}/stories", token, body={"data": {"text": args.text}}))
    if cmd == "create-task":
        data = {
            "workspace": workspace_arg(args.workspace),
            "name": args.name,
        }
        if args.notes:
            data["notes"] = args.notes
        if args.project:
            data["projects"] = [args.project]
        if args.assignee:
            data["assignee"] = args.assignee
        if args.due_on:
            data["due_on"] = args.due_on
        return print_json(request_json("POST", "/tasks", token, body={"data": data}))

    raise SystemExit(f"Unknown command: {cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
