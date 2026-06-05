#!/usr/bin/env python3
"""Control Center Email Accounts helper for agents.

Uses CC_URL + CC_API_KEY to call the Control Center Email Accounts API.
It never reads SMTP secrets directly and never prints API keys.
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


def require_env(name: str, fallback: str | None = None) -> str:
    value = os.environ.get(name) or (os.environ.get(fallback) if fallback else "")
    if not value:
        raise SystemExit(json.dumps({"ok": False, "error": f"Missing required environment variable: {name}"}))
    return value


def cc_url() -> str:
    return require_env("CC_URL").rstrip("/")


def api_key() -> str:
    return require_env("CC_API_KEY")


def read_text_arg(value: str | None, path: str | None, stdin_flag: bool = False) -> str:
    if stdin_flag:
        return sys.stdin.read()
    if path:
        return Path(path).read_text(encoding="utf-8")
    return value or ""


def normalize_attachment_path(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("--attach path cannot be empty")
    if cleaned != "/documents" and not cleaned.startswith("/documents/"):
        raise ValueError("--attach must point to a file under /documents")
    return cleaned


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{cc_url()}{path}"
    data = None
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key(),
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw.strip() else {}
            parsed.setdefault("ok", True)
            return parsed
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            detail = {"raw": raw[:1000]}
        return {
            "ok": False,
            "status": error.code,
            "error": detail.get("error") or detail.get("detail") or error.reason,
            "detail": detail,
        }
    except Exception as error:  # noqa: BLE001 - CLI must convert all failures to JSON
        return {"ok": False, "error": str(error)}


def print_json(payload: Any) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if isinstance(payload, dict) and payload.get("ok", True) else 1


def account_summary(account: dict[str, Any]) -> dict[str, Any]:
    outgoing = account.get("outgoing") or {}
    incoming = account.get("incoming") or {}
    status = account.get("status") or {}
    return {
        "id": account.get("id"),
        "slug": account.get("slug"),
        "displayName": account.get("displayName"),
        "emailAddress": account.get("emailAddress"),
        "enabled": account.get("enabled"),
        "agentAccessEnabled": account.get("agentAccessEnabled"),
        "incoming": {
            "host": incoming.get("host"),
            "port": incoming.get("port"),
            "security": incoming.get("security"),
            "username": incoming.get("username"),
            "folder": incoming.get("folder"),
            "passwordSet": incoming.get("passwordSet"),
        },
        "outgoing": {
            "enabled": outgoing.get("enabled"),
            "host": outgoing.get("host"),
            "port": outgoing.get("port"),
            "security": outgoing.get("security"),
            "username": outgoing.get("username"),
            "fromEmail": outgoing.get("fromEmail"),
            "passwordSet": outgoing.get("passwordSet"),
        },
        "status": status,
    }


def cmd_list(_args: argparse.Namespace) -> int:
    data = request_json("GET", "/api/email/accounts")
    if not data.get("ok", True):
        return print_json(data)
    accounts = [account_summary(item) for item in data.get("accounts", []) if isinstance(item, dict)]
    return print_json({"ok": True, "accounts": accounts})


def cmd_verify(args: argparse.Namespace) -> int:
    data = request_json("POST", f"/api/email/accounts/{args.account_id}/test-outgoing", {})
    return print_json(data)


def cmd_latest(args: argparse.Namespace) -> int:
    query = urllib.parse.urlencode({"limit": args.limit})
    data = request_json("GET", f"/api/email/accounts/{args.account_id}/messages/latest?{query}")
    return print_json(data)


def cmd_get_message(args: argparse.Namespace) -> int:
    data = request_json("GET", f"/api/email/accounts/{args.account_id}/messages/{args.uid}")
    return print_json(data)


def cmd_search(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {"limit": args.limit}
    if args.from_email:
        payload["from"] = args.from_email
    if args.subject:
        payload["subject"] = args.subject
    data = request_json("POST", f"/api/email/accounts/{args.account_id}/messages/search", payload)
    return print_json(data)


def cmd_send(args: argparse.Namespace) -> int:
    if args.confirm_send != "yes":
        return print_json({
            "ok": False,
            "error": "Refusing to send without --confirm-send yes",
        })

    text = read_text_arg(args.text, args.text_file, args.text_stdin).strip()
    html = read_text_arg(args.html, args.html_file).strip()
    recipients = [item.strip() for item in args.to if item.strip()]
    cc = [item.strip() for item in args.cc if item.strip()]
    bcc = [item.strip() for item in args.bcc if item.strip()]

    if not recipients:
        return print_json({"ok": False, "error": "At least one --to recipient is required"})
    if not args.subject.strip():
        return print_json({"ok": False, "error": "--subject is required"})
    if not text and not html:
        return print_json({"ok": False, "error": "Provide --text, --text-file, --text-stdin, --html, or --html-file"})

    payload: dict[str, Any] = {
        "to": recipients,
        "cc": cc,
        "bcc": bcc,
        "subject": args.subject,
        "text": text,
    }
    if html:
        payload["html"] = html
    if args.attach:
        try:
            payload["attachments"] = [{"path": normalize_attachment_path(item)} for item in args.attach]
        except ValueError as error:
            return print_json({"ok": False, "error": str(error)})

    data = request_json("POST", f"/api/email/accounts/{args.account_id}/send", payload)
    return print_json(data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Control Center Email Accounts helper")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List configured email accounts.")
    list_parser.set_defaults(func=cmd_list)

    verify = sub.add_parser("verify", help="Verify outgoing SMTP without sending an email.")
    verify.add_argument("--account-id", type=int, required=True)
    verify.set_defaults(func=cmd_verify)

    latest = sub.add_parser("latest", help="List latest mailbox messages.")
    latest.add_argument("--account-id", type=int, required=True)
    latest.add_argument("--limit", type=int, default=10)
    latest.set_defaults(func=cmd_latest)

    get_message = sub.add_parser("get-message", help="Read one mailbox message by UID.")
    get_message.add_argument("--account-id", type=int, required=True)
    get_message.add_argument("--uid", type=int, required=True)
    get_message.set_defaults(func=cmd_get_message)

    search = sub.add_parser("search", help="Search recent mailbox messages.")
    search.add_argument("--account-id", type=int, required=True)
    search.add_argument("--from", dest="from_email")
    search.add_argument("--subject")
    search.add_argument("--limit", type=int, default=20)
    search.set_defaults(func=cmd_search)

    send = sub.add_parser("send", help="Send an email through Control Center Email Accounts.")
    send.add_argument("--account-id", type=int, required=True)
    send.add_argument("--to", action="append", default=[])
    send.add_argument("--cc", action="append", default=[])
    send.add_argument("--bcc", action="append", default=[])
    send.add_argument("--subject", required=True)
    send.add_argument("--text")
    send.add_argument("--text-file")
    send.add_argument("--text-stdin", action="store_true")
    send.add_argument("--html")
    send.add_argument("--html-file")
    send.add_argument("--attach", action="append", default=[], help="Attach a file from /documents. Repeat for multiple attachments.")
    send.add_argument("--confirm-send", choices=["yes", "no"], default="no")
    send.set_defaults(func=cmd_send)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
