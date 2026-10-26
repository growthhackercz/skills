#!/usr/bin/env python3
"""Throttle-aware mailbox reads on top of cc_email.py.

For mailboxes that hit Microsoft 365 Graph throttling or read timeouts:
  - small hard limit per query and targeted lookups (--from / --subject);
  - retry with exponential backoff and jitter, honouring Retry-After;
  - after the retries are exhausted a short cooldown stops further reads from
    hammering the mailbox until it expires (`status`, `clear-cooldown`);
  - `search --use-index` answers from an optional local message index without
    calling the mailbox at all.

When `--account-id` is omitted the account is resolved at runtime with
resolve_account_id.py (the instance must have one mailbox, or pass --email).
There is no hardcoded fallback account. This wrapper never sends email.

Environment:
  CC_EMAIL_READ_STATE_DIR  cooldown state directory (default: <tmp>/cc-email-read)
  CC_EMAIL_READ_INDEX_DIR  optional index directory with email-index.jsonl and
                           email-index-sent.jsonl
                           (default: $CC_DOCUMENTS_PATH or /documents, /email-archiv/index)
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
HELPER = SCRIPT_DIR / "cc_email.py"
RESOLVE_ACCOUNT = SCRIPT_DIR / "resolve_account_id.py"

STATE_DIR = Path(os.environ.get("CC_EMAIL_READ_STATE_DIR") or Path(tempfile.gettempdir()) / "cc-email-read")
COOLDOWN_FILE = STATE_DIR / "read-cooldown.json"
INDEX_DIR = Path(
    os.environ.get("CC_EMAIL_READ_INDEX_DIR")
    or Path(os.environ.get("CC_DOCUMENTS_PATH") or "/documents") / "email-archiv" / "index"
)
INDEX_INBOX = INDEX_DIR / "email-index.jsonl"
INDEX_SENT = INDEX_DIR / "email-index-sent.jsonl"

HARD_LIMIT = 15
DEFAULT_RETRIES = 3
BASE_BACKOFF = 20.0
MAX_BACKOFF = 90.0
COOLDOWN_AFTER_FAIL = 600
TIMEOUT_MARKERS = ("timed out", "timeout", "etimedout")
THROTTLE_MARKERS = ("429", "too many requests", "throttl", "service unavailable", "503")


def log(message: str) -> None:
    print(f"[cc_email_read] {message}", file=sys.stderr)


def print_json(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 1


def resolve_account(email: str | None) -> int | None:
    command = [sys.executable, str(RESOLVE_ACCOUNT)]
    if email:
        command += ["--email", email]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    except Exception as error:  # noqa: BLE001
        log(f"account resolution failed: {error}")
        return None
    value = (result.stdout or "").strip()
    if result.returncode == 0 and value.isdigit():
        return int(value)
    log(f"account resolution failed: {(result.stderr or value).strip()}")
    return None


# ---- Cooldown state --------------------------------------------------------

def read_cooldown() -> dict[str, Any]:
    try:
        return json.loads(COOLDOWN_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def cooldown_remaining() -> int:
    until = float(read_cooldown().get("cooldown_until", 0) or 0)
    remaining = int(until - time.time())
    return remaining if remaining > 0 else 0


def write_cooldown(update: dict[str, Any]) -> None:
    state = read_cooldown()
    state.update(update)
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        COOLDOWN_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as error:
        log(f"cannot write cooldown state: {error}")


def set_cooldown(seconds: int, reason: str) -> None:
    write_cooldown({
        "cooldown_until": time.time() + seconds,
        "cooldown_set_at": time.time(),
        "cooldown_seconds": seconds,
        "reason": reason,
        "consecutive_failures": int(read_cooldown().get("consecutive_failures", 0)) + 1,
    })


def clear_cooldown(note: str = "ok") -> None:
    write_cooldown({"cooldown_until": 0, "cleared_at": time.time(), "consecutive_failures": 0, "last_ok_note": note})


# ---- Helper calls with retry/backoff ---------------------------------------

def call_helper(helper_args: list[str], timeout: int = 55) -> dict[str, Any]:
    raw = ""
    try:
        result = subprocess.run([sys.executable, str(HELPER), *helper_args], capture_output=True, text=True, timeout=timeout)
        raw = (result.stdout or "").strip()
        if not raw:
            return {"ok": False, "error": (result.stderr or "").strip() or "empty response"}
        return json.loads(raw)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timed out (wrapper subprocess)"}
    except json.JSONDecodeError:
        return {"ok": False, "error": "non-json response", "raw": raw[:500]}
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "error": str(error)}


def is_throttle(result: dict[str, Any]) -> bool:
    if str(result.get("status", "")) in {"429", "503"}:
        return True
    error = str(result.get("error", "")).lower()
    return any(marker in error for marker in TIMEOUT_MARKERS + THROTTLE_MARKERS)


def retry_after_seconds(result: dict[str, Any]) -> float | None:
    detail = result.get("detail")
    if not isinstance(detail, dict):
        return None
    for key in ("retryAfter", "retry_after", "Retry-After"):
        value = detail.get(key)
        if value:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    return None


def resilient_call(helper_args: list[str], retries: int = DEFAULT_RETRIES) -> dict[str, Any]:
    remaining = cooldown_remaining()
    if remaining > 0:
        return {
            "ok": False,
            "cooled_down": True,
            "cooldown_remaining_s": remaining,
            "error": (
                f"Mailbox reads are cooling down for another {remaining}s after repeated throttling. "
                "Do not retry in a loop; wait, or use `search --use-index` when a local index exists."
            ),
        }

    last: dict[str, Any] = {}
    for attempt in range(1, retries + 1):
        result = call_helper(helper_args)
        if result.get("ok"):
            clear_cooldown(note=f"ok after attempt {attempt}")
            result["_attempts"] = attempt
            return result
        last = result
        if not is_throttle(result):
            result["_attempts"] = attempt
            return result
        if attempt < retries:
            wait = retry_after_seconds(result)
            wait = min(wait if wait is not None else BASE_BACKOFF * (2 ** (attempt - 1)), MAX_BACKOFF)
            wait += random.uniform(0, wait * 0.2)
            log(f"attempt {attempt}/{retries} throttled or timed out, backing off {wait:.0f}s")
            time.sleep(wait)

    set_cooldown(COOLDOWN_AFTER_FAIL, reason=str(last.get("error", "throttle")))
    last["_attempts"] = retries
    last["cooldown_set_s"] = COOLDOWN_AFTER_FAIL
    last["guidance"] = (
        "Throttling persists; a cooldown is set. Do not retry in a loop. "
        "Use `search --use-index` when a local index exists, or try again after the cooldown."
    )
    return last


# ---- Local index ------------------------------------------------------------

def load_index(direction: str = "in") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = (INDEX_SENT if direction == "out" else INDEX_INBOX).read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def search_index(from_email: str | None, subject: str | None, after: str | None, limit: int, direction: str) -> list[dict[str, Any]]:
    found = []
    for row in load_index(direction):
        sender = str(row.get("from") or row.get("sender") or "").lower()
        row_subject = str(row.get("subject") or "")
        date = str(row.get("receivedAt") or row.get("date") or "")
        if from_email and from_email.lower() not in sender:
            continue
        if subject and subject.lower() not in row_subject.lower():
            continue
        if after and date and date < after:
            continue
        found.append({
            "date": date,
            "from": row.get("from") or row.get("sender"),
            "subject": row_subject,
            "uid": row.get("uid") or row.get("id"),
            "preview": str(row.get("preview") or "")[:200],
            "messageId": row.get("messageId"),
        })
    found.sort(key=lambda item: item["date"], reverse=True)
    return found[:limit]


# ---- Commands ----------------------------------------------------------------

def cmd_status(_args: argparse.Namespace) -> int:
    state = read_cooldown()
    remaining = cooldown_remaining()
    index_mtime = None
    try:
        index_mtime = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(INDEX_INBOX.stat().st_mtime))
    except OSError:
        pass
    return print_json({
        "ok": True,
        "cooldown_active": remaining > 0,
        "cooldown_remaining_s": remaining,
        "consecutive_failures": state.get("consecutive_failures", 0),
        "last_reason": state.get("reason"),
        "index_inbox_exists": INDEX_INBOX.exists(),
        "index_inbox_mtime_utc": index_mtime,
    })


def cmd_clear(_args: argparse.Namespace) -> int:
    clear_cooldown(note="manual clear")
    return print_json({"ok": True, "cleared": True})


def cmd_search(args: argparse.Namespace) -> int:
    limit = min(args.limit, HARD_LIMIT)
    if args.use_index:
        rows = search_index(args.from_email, args.subject, args.after, limit, args.direction)
        return print_json({"ok": True, "source": "local-index", "count": len(rows), "messages": rows})
    helper_args = ["search", "--account-id", str(args.account_id), "--limit", str(limit)]
    for flag, value in (("--from", args.from_email), ("--subject", args.subject), ("--after", args.after), ("--before", args.before)):
        if value:
            helper_args += [flag, value]
    return print_json(resilient_call(helper_args))


def cmd_latest(args: argparse.Namespace) -> int:
    helper_args = ["latest", "--account-id", str(args.account_id), "--limit", str(min(args.limit, HARD_LIMIT))]
    if args.folder_id:
        helper_args += ["--folder-id", args.folder_id]
    return print_json(resilient_call(helper_args))


def cmd_get_message(args: argparse.Namespace) -> int:
    return print_json(resilient_call(["get-message", "--account-id", str(args.account_id), "--uid", str(args.uid)]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Throttle-aware mailbox reads (no sending).")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Cooldown and local index status.")
    status.set_defaults(func=cmd_status)

    clear = sub.add_parser("clear-cooldown", help="Reset the cooldown after the mailbox recovered.")
    clear.set_defaults(func=cmd_clear)

    search = sub.add_parser("search", help="Targeted search with a small limit and backoff; --use-index reads the local index.")
    search.add_argument("--account-id", type=int)
    search.add_argument("--email", help="Mailbox used to resolve the account when --account-id is omitted.")
    search.add_argument("--from", dest="from_email")
    search.add_argument("--subject")
    search.add_argument("--after")
    search.add_argument("--before")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--use-index", action="store_true", help="Read the local index instead of the mailbox.")
    search.add_argument("--direction", choices=["in", "out"], default="in")
    search.set_defaults(func=cmd_search)

    latest = sub.add_parser("latest", help="Latest messages with a small limit and backoff.")
    latest.add_argument("--account-id", type=int)
    latest.add_argument("--email", help="Mailbox used to resolve the account when --account-id is omitted.")
    latest.add_argument("--limit", type=int, default=10)
    latest.add_argument("--folder-id")
    latest.set_defaults(func=cmd_latest)

    get_message = sub.add_parser("get-message", help="One message by UID with backoff.")
    get_message.add_argument("--account-id", type=int)
    get_message.add_argument("--email", help="Mailbox used to resolve the account when --account-id is omitted.")
    get_message.add_argument("--uid", type=int, required=True)
    get_message.set_defaults(func=cmd_get_message)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    needs_account = args.func in (cmd_latest, cmd_get_message) or (args.func is cmd_search and not args.use_index)
    if needs_account and args.account_id is None:
        args.account_id = resolve_account(args.email)
        if args.account_id is None:
            return print_json({
                "ok": False,
                "error": "Could not resolve the email account; pass --account-id or --email (see resolve_account_id.py).",
            })
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
