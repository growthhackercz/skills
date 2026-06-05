#!/usr/bin/env python3
"""Safe Trello REST API helper for OpenClaw skills.

Trello requires key/token query parameters. This helper builds those URLs
internally so secrets are not placed in command-line arguments or examples.
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

API_BASE = "https://api.trello.com/1"
TIMEOUT_SECONDS = 30
USER_AGENT = "cliqsales-trello-skill/1.0"


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


def credentials() -> tuple[str, str]:
    key = credential("TRELLO_API_KEY")
    token = credential("TRELLO_TOKEN")
    if not key or not token:
        print(
            "ERROR: Missing TRELLO_API_KEY or TRELLO_TOKEN. Configure Trello in Control Center > Integrations.",
            file=sys.stderr,
        )
        raise SystemExit(65)
    return key, token


def build_url(path: str, auth: tuple[str, str], params: dict[str, Any] | None = None) -> str:
    if not path.startswith("/"):
        path = "/" + path
    key, token = auth
    query = {
        "key": key,
        "token": token,
        **{k: v for k, v in (params or {}).items() if v is not None and str(v) != ""},
    }
    return f"{API_BASE}{path}?{urllib.parse.urlencode(query, doseq=True)}"


def request_json(
    method: str,
    path: str,
    auth: tuple[str, str],
    params: dict[str, Any] | None = None,
    form: dict[str, Any] | None = None,
) -> Any:
    payload = urllib.parse.urlencode({k: v for k, v in (form or {}).items() if v is not None}).encode("utf-8") if form else None
    req = urllib.request.Request(
        build_url(path, auth, params),
        data=payload,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"Trello API HTTP {exc.code} for {method} {path}", file=sys.stderr)
        if detail:
            print(detail[:1000], file=sys.stderr)
        raise SystemExit(2) from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"Trello network error: {exc.reason}") from None

    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def print_json(data: Any) -> int:
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def common_card_fields() -> str:
    return "id,name,desc,closed,idBoard,idList,url,due,dateLastActivity"


def main() -> int:
    parser = argparse.ArgumentParser(description="Call Trello REST API with Control Center credentials.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("me")

    boards = sub.add_parser("boards")
    boards.add_argument("--fields", default="id,name,url,closed")

    lists = sub.add_parser("lists")
    lists.add_argument("board_id")

    cards_board = sub.add_parser("cards-board")
    cards_board.add_argument("board_id")

    cards_list = sub.add_parser("cards-list")
    cards_list.add_argument("list_id")

    card = sub.add_parser("card")
    card.add_argument("card_id")

    create = sub.add_parser("create-card")
    create.add_argument("--list", dest="list_id", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--desc", default="")
    create.add_argument("--due")

    move = sub.add_parser("move-card")
    move.add_argument("card_id")
    move.add_argument("--list", dest="list_id", required=True)

    comment = sub.add_parser("comment-card")
    comment.add_argument("card_id")
    comment.add_argument("--text", required=True)

    archive = sub.add_parser("archive-card")
    archive.add_argument("card_id")
    archive.add_argument("--confirm", choices=["yes", "no"], default="no")

    args = parser.parse_args()
    auth = credentials()
    cmd = args.command

    if cmd == "me":
        return print_json(request_json("GET", "/members/me", auth, {"fields": "id,username,fullName,email"}))
    if cmd == "boards":
        return print_json(request_json("GET", "/members/me/boards", auth, {"fields": args.fields}))
    if cmd == "lists":
        return print_json(request_json("GET", f"/boards/{urllib.parse.quote(args.board_id)}/lists", auth, {"fields": "id,name,closed,pos"}))
    if cmd == "cards-board":
        return print_json(request_json("GET", f"/boards/{urllib.parse.quote(args.board_id)}/cards", auth, {"fields": common_card_fields()}))
    if cmd == "cards-list":
        return print_json(request_json("GET", f"/lists/{urllib.parse.quote(args.list_id)}/cards", auth, {"fields": common_card_fields()}))
    if cmd == "card":
        return print_json(request_json("GET", f"/cards/{urllib.parse.quote(args.card_id)}", auth, {"fields": "all"}))
    if cmd == "create-card":
        form = {"idList": args.list_id, "name": args.name, "desc": args.desc, "due": args.due}
        return print_json(request_json("POST", "/cards", auth, form=form))
    if cmd == "move-card":
        return print_json(request_json("PUT", f"/cards/{urllib.parse.quote(args.card_id)}", auth, form={"idList": args.list_id}))
    if cmd == "comment-card":
        return print_json(request_json("POST", f"/cards/{urllib.parse.quote(args.card_id)}/actions/comments", auth, form={"text": args.text}))
    if cmd == "archive-card":
        if args.confirm != "yes":
            raise SystemExit("Refusing to archive without --confirm yes.")
        return print_json(request_json("PUT", f"/cards/{urllib.parse.quote(args.card_id)}", auth, form={"closed": "true"}))

    raise SystemExit(f"Unknown command: {cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
