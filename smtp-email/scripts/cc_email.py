#!/usr/bin/env python3
"""Control Center Email Accounts helper for agents.

Uses CC_URL + CC_API_KEY to call the Control Center Email Accounts API.
It never reads mailbox secrets directly and never prints API keys.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any

MAX_INCOMING_ATTACHMENT_BYTES = 20 * 1024 * 1024


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


def normalize_document_output_path(value: str) -> str:
    cleaned = value.strip().replace("\\", "/")
    logical = PurePosixPath(cleaned)
    if not cleaned.startswith("/documents/") or ".." in logical.parts:
        raise ValueError("--output must point to a file under /documents")
    if logical.name in {"", ".", ".."}:
        raise ValueError("--output must include a filename")
    return str(logical)


def safe_download_filename(value: str) -> str:
    cleaned = "".join(" " if ord(char) < 32 else char for char in value)
    cleaned = cleaned.replace("/", "-").replace("\\", "-")
    cleaned = " ".join(cleaned.split()).strip(" .")[:180]
    return cleaned or "attachment"


def default_attachment_output(account_id: int, uid: int, attachment_id: str, filename: str) -> str:
    safe_name = safe_download_filename(filename)
    suffix = Path(safe_name).suffix
    stem = safe_name[:-len(suffix)] if suffix else safe_name
    digest = hashlib.sha256(attachment_id.encode("utf-8")).hexdigest()[:8]
    stored_name = f"{stem}-{digest}{suffix}"
    return f"/documents/email-attachments/account-{account_id}/message-{uid}/{stored_name}"


def resolve_document_output(logical_path: str) -> Path:
    logical = PurePosixPath(normalize_document_output_path(logical_path))
    root = Path(os.environ.get("CC_DOCUMENTS_PATH") or "/documents")
    root.mkdir(parents=True, exist_ok=True)
    root_real = root.resolve()
    relative = logical.relative_to("/documents")
    target = root_real.joinpath(*relative.parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    parent_real = target.parent.resolve()
    try:
        parent_real.relative_to(root_real)
    except ValueError as error:
        raise ValueError("--output escapes /documents through a symbolic link") from error
    return parent_real / target.name


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


def download_attachment(
    account_id: int,
    uid: int,
    attachment_id: str,
    output: str | None,
    overwrite: bool,
) -> dict[str, Any]:
    url = (
        f"{cc_url()}/api/email/accounts/{account_id}/messages/{uid}"
        "/attachments/download"
    )
    data = json.dumps({"attachmentId": attachment_id}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Accept": "application/octet-stream",
            "Content-Type": "application/json",
            "x-api-key": api_key(),
        },
        method="POST",
    )

    temp_path: Path | None = None
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            filename = safe_download_filename(urllib.parse.unquote(
                response.headers.get("X-CC-Attachment-Filename") or "attachment"
            ))
            logical_path = normalize_document_output_path(
                output or default_attachment_output(account_id, uid, attachment_id, filename)
            )
            target = resolve_document_output(logical_path)
            if target.exists() and not overwrite:
                return {
                    "ok": False,
                    "error": f"Output already exists: {logical_path}. Use --overwrite to replace it.",
                }

            announced_size = int(response.headers.get("Content-Length") or "0")
            if announced_size > MAX_INCOMING_ATTACHMENT_BYTES:
                return {
                    "ok": False,
                    "error": (
                        "Incoming attachment is too large "
                        f"(max {MAX_INCOMING_ATTACHMENT_BYTES} bytes)"
                    ),
                }

            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".part",
                delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                total = 0
                while True:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_INCOMING_ATTACHMENT_BYTES:
                        raise ValueError(
                            "Incoming attachment is too large "
                            f"(max {MAX_INCOMING_ATTACHMENT_BYTES} bytes)"
                        )
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())

            os.chmod(temp_path, 0o644)
            os.replace(temp_path, target)
            temp_path = None
            return {
                "ok": True,
                "path": logical_path,
                "filename": filename,
                "contentType": response.headers.get("Content-Type") or "application/octet-stream",
                "size": total,
            }
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
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def print_json(payload: Any) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if isinstance(payload, dict) and payload.get("ok", True) else 1


def account_summary(account: dict[str, Any]) -> dict[str, Any]:
    outgoing = account.get("outgoing") or {}
    incoming = account.get("incoming") or {}
    status = account.get("status") or {}
    return {
        "id": account.get("id"),
        "provider": account.get("provider"),
        "slug": account.get("slug"),
        "displayName": account.get("displayName"),
        "emailAddress": account.get("emailAddress"),
        "enabled": account.get("enabled"),
        "agentAccessEnabled": account.get("agentAccessEnabled"),
        "maxMessagesPerRead": account.get("maxMessagesPerRead"),
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
    if args.cursor:
        payload: dict[str, Any] = {"cursor": args.cursor}
    else:
        payload = {"limit": args.limit}
        if args.page_size is not None:
            payload["pageSize"] = args.page_size
        if args.after:
            payload["after"] = args.after
        if args.before:
            payload["before"] = args.before
        if args.folder_id:
            payload["folderId"] = args.folder_id
    data = request_json("POST", f"/api/email/accounts/{args.account_id}/messages/latest", payload)
    return print_json(data)


def cmd_get_message(args: argparse.Namespace) -> int:
    data = request_json("GET", f"/api/email/accounts/{args.account_id}/messages/{args.uid}")
    return print_json(data)


def cmd_folders(args: argparse.Namespace) -> int:
    data = request_json("GET", f"/api/email/accounts/{args.account_id}/folders")
    return print_json(data)


def cmd_download_attachment(args: argparse.Namespace) -> int:
    data = download_attachment(
        args.account_id,
        args.uid,
        args.attachment_id,
        args.output,
        args.overwrite,
    )
    return print_json(data)


def cmd_search(args: argparse.Namespace) -> int:
    if args.cursor:
        payload: dict[str, Any] = {"cursor": args.cursor}
    else:
        payload = {"limit": args.limit}
        if args.page_size is not None:
            payload["pageSize"] = args.page_size
        if args.from_email:
            payload["from"] = args.from_email
        if args.subject:
            payload["subject"] = args.subject
        if args.after:
            payload["after"] = args.after
        if args.before:
            payload["before"] = args.before
        if args.folder_id:
            payload["folderId"] = args.folder_id
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

    verify = sub.add_parser("verify", help="Verify outgoing email access without sending an email.")
    verify.add_argument("--account-id", type=int, required=True)
    verify.set_defaults(func=cmd_verify)

    latest = sub.add_parser("latest", help="List latest mailbox messages.")
    latest.add_argument("--account-id", type=int, required=True)
    latest.add_argument("--limit", type=int, default=10)
    latest.add_argument("--page-size", type=int)
    latest.add_argument("--after", help="Only messages received at or after this ISO date/date-time.")
    latest.add_argument("--before", help="Only messages received before this ISO date/date-time.")
    latest.add_argument("--folder-id", help="Microsoft 365 folder id or well-known name (for example sentitems).")
    latest.add_argument("--cursor", help="Opaque nextCursor returned by the previous page.")
    latest.set_defaults(func=cmd_latest)

    get_message = sub.add_parser("get-message", help="Read one mailbox message by UID.")
    get_message.add_argument("--account-id", type=int, required=True)
    get_message.add_argument("--uid", type=int, required=True)
    get_message.set_defaults(func=cmd_get_message)

    folders = sub.add_parser("folders", help="List Microsoft 365 mailbox folders.")
    folders.add_argument("--account-id", type=int, required=True)
    folders.set_defaults(func=cmd_folders)

    download = sub.add_parser(
        "download-attachment",
        help="Download one incoming attachment to /documents.",
    )
    download.add_argument("--account-id", type=int, required=True)
    download.add_argument("--uid", type=int, required=True)
    download.add_argument("--attachment-id", required=True)
    download.add_argument("--output", help="Optional destination file under /documents.")
    download.add_argument("--overwrite", action="store_true")
    download.set_defaults(func=cmd_download_attachment)

    search = sub.add_parser("search", help="Search recent mailbox messages.")
    search.add_argument("--account-id", type=int, required=True)
    search.add_argument("--from", dest="from_email")
    search.add_argument("--subject")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--page-size", type=int)
    search.add_argument("--after", help="Only messages received at or after this ISO date/date-time.")
    search.add_argument("--before", help="Only messages received before this ISO date/date-time.")
    search.add_argument("--folder-id", help="Microsoft 365 folder id or well-known name (for example sentitems).")
    search.add_argument("--cursor", help="Opaque nextCursor returned by the previous page.")
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
