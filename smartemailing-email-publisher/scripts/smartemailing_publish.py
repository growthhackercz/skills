#!/usr/bin/env python3
"""Create SmartEmailing saved email assets from email HTML files."""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_ENV_FILES = (
    "/home/node/.openclaw/secrets/smartemailing.env",
    "/home/node/.openclaw/secrets/email.env",
    "/home/node/.openclaw/.env",
)
DEFAULT_API_BASE_URL = "https://app.smartemailing.cz/api/v3"


class SmartEmailingError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, detail: Any | None = None):
        super().__init__(message)
        self.status = status
        self.detail = detail


def parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return key, value


def default_env_file_candidates() -> list[str]:
    candidates: list[str] = []
    openclaw_home = os.environ.get("OPENCLAW_HOME") or os.environ.get("CC_OPENCLAW_HOME")
    if openclaw_home:
        home = Path(openclaw_home).expanduser()
        if home.name not in {".openclaw", ".clawdbot"} and (home / ".openclaw").exists():
            home = home / ".openclaw"
        candidates.extend([
            str(home / "secrets" / "smartemailing.env"),
            str(home / "secrets" / "email.env"),
            str(home / ".env"),
        ])
    candidates.extend(candidate for candidate in DEFAULT_ENV_FILES if candidate not in candidates)
    return candidates


def load_env_file(path: str | None) -> None:
    candidates = [path] if path else default_env_file_candidates()
    for candidate in candidates:
        if not candidate:
            continue
        env_path = Path(candidate)
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            parsed = parse_env_line(line)
            if parsed:
                key, value = parsed
                os.environ.setdefault(key, value)


def _load_cc_credentials():
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
            from cc_credentials import smartemailing_credentials  # type: ignore
        except Exception:
            continue
        return smartemailing_credentials
    return None


def load_control_center_credentials() -> None:
    smartemailing_credentials = _load_cc_credentials()
    if not smartemailing_credentials:
        return
    data = smartemailing_credentials()
    values = {
        "SMARTEMAILING_USERNAME": data.get("username"),
        "SMARTEMAILING_API_KEY": data.get("api_key"),
    }
    for key, value in values.items():
        if value and not os.environ.get(key):
            os.environ[key] = value


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SmartEmailingError(f"Missing required environment variable: {name}")
    return value


def first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def strip_tags(value: str) -> str:
    text = re.sub(r"<(br|/p|/div|/h[1-6]|/li)>", "\n", value, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def parse_metadata(content: str) -> dict[str, str]:
    match = re.search(r"<!--\s*EMAIL METADATA\s*(.*?)-->", content, flags=re.I | re.S)
    out: dict[str, str] = {}
    if not match:
        return out
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        norm = re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")
        if norm and value.strip():
            out[norm] = value.strip().strip("*").strip()
    return out


def clean_html(content: str) -> str:
    return re.sub(r"<!--\s*EMAIL METADATA\s*.*?-->\s*", "", content, flags=re.I | re.S).strip()


def extract_tag(content: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", content, flags=re.I | re.S)
    return strip_tags(match.group(1)) if match else None


def email_from_html(path: str) -> dict[str, Any]:
    html_path = Path(path)
    content = html_path.read_text(encoding="utf-8", errors="replace")
    meta = parse_metadata(content)
    subject = first_string(meta.get("subject"), extract_tag(content, "title"), extract_tag(content, "h1"))
    name = first_string(meta.get("name"), subject, html_path.stem)
    if not subject:
        raise SmartEmailingError(f"Missing subject in {path}")
    text_path = html_path.with_suffix(".txt")
    text = text_path.read_text(encoding="utf-8", errors="replace").strip() if text_path.exists() else strip_tags(clean_html(content))
    return {
        "id": first_string(meta.get("id"), html_path.stem),
        "name": name,
        "title": name,
        "subject": subject,
        "htmlbody": clean_html(content),
        "textbody": text,
        "htmlPath": str(html_path),
        "textPath": str(text_path) if text_path.exists() else "",
    }


def email_from_manifest_item(item: dict[str, Any]) -> dict[str, Any]:
    data = email_from_html(str(item["htmlPath"]))
    if item.get("name"):
        data["name"] = item["name"]
        data["title"] = item["name"]
    if item.get("subject"):
        data["subject"] = item["subject"]
    if item.get("textPath") and Path(item["textPath"]).exists():
        data["textbody"] = Path(item["textPath"]).read_text(encoding="utf-8", errors="replace").strip()
    return data


def manifest_emails(path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    emails = data.get("emails")
    if not isinstance(emails, list):
        raise SmartEmailingError(f"Manifest missing emails[]: {path}")
    return [email_from_manifest_item(item) for item in emails if isinstance(item, dict)]


def auth_header() -> str:
    username = require_env("SMARTEMAILING_USERNAME")
    api_key = require_env("SMARTEMAILING_API_KEY")
    token = base64.b64encode(f"{username}:{api_key}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def api_request(method: str, path: str, payload: dict[str, Any] | None = None, insecure: bool = False) -> dict[str, Any]:
    base_url = os.environ.get("SMARTEMAILING_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")
    request = urllib.request.Request(f"{base_url}/{path.lstrip('/')}", method=method, data=json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None)
    request.add_header("Authorization", auth_header())
    request.add_header("Accept", "application/json")
    request.add_header("Content-Type", "application/json")
    context = ssl._create_unverified_context() if insecure else None
    try:
        with urllib.request.urlopen(request, timeout=30, context=context) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            detail: Any = json.loads(raw)
        except json.JSONDecodeError:
            detail = raw
        raise SmartEmailingError(f"SmartEmailing API error {error.code} for {method} /{path}", error.code, detail) from error
    except urllib.error.URLError as error:
        raise SmartEmailingError(f"SmartEmailing connection error: {error.reason}") from error


def find_in_tree(value: Any, keys: set[str]) -> Any | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys and item not in (None, ""):
                return item
        for item in value.values():
            found = find_in_tree(item, keys)
            if found not in (None, ""):
                return found
    if isinstance(value, list):
        for item in value:
            found = find_in_tree(item, keys)
            if found not in (None, ""):
                return found
    return None


def email_id(response: dict[str, Any]) -> str | None:
    found = find_in_tree(response, {"id", "email_id", "emailId"})
    return str(found) if found else None


def build_email_payload(email: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": email["title"],
        "name": email["name"],
        "htmlbody": email["htmlbody"],
        "textbody": email["textbody"],
    }


def create_draft(email: dict[str, Any], dry_run: bool = False, insecure: bool = False) -> dict[str, Any]:
    payload = build_email_payload(email)
    if dry_run:
        return {"ok": True, "dryRun": True, "payloadKeys": sorted(payload.keys()), "subject": email["subject"]}
    response = api_request("POST", "emails", payload, insecure=insecure)
    return {"ok": True, "emailId": email_id(response), "subject": email["subject"], "response": response}


def command_test(args: argparse.Namespace) -> None:
    checks = {}
    for path in ("ping", "contactlists", "emails", "newsletters"):
        response = api_request("GET", path, insecure=args.insecure)
        checks[path] = {"keys": sorted(response.keys()), "status": response.get("status")}
    print(json.dumps({"ok": True, "checks": checks}, ensure_ascii=False, indent=2))


def command_parse(args: argparse.Namespace) -> None:
    email = email_from_html(args.input)
    email["htmlbody"] = f"<redacted html: {len(email['htmlbody'])} chars>"
    email["textbody"] = f"<redacted text: {len(email['textbody'])} chars>"
    print(json.dumps(email, ensure_ascii=False, indent=2))


def command_draft(args: argparse.Namespace) -> None:
    print(json.dumps(create_draft(email_from_html(args.input), dry_run=args.dry_run, insecure=args.insecure), ensure_ascii=False, indent=2))


def command_batch(args: argparse.Namespace) -> None:
    results = []
    for email in manifest_emails(args.manifest):
        try:
            results.append({"id": email.get("id"), **create_draft(email, dry_run=args.dry_run, insecure=args.insecure)})
        except SmartEmailingError as error:
            results.append({"id": email.get("id"), "ok": False, "error": str(error), "status": error.status, "detail": error.detail})
            if args.mode != "continue":
                break
    print(json.dumps({"total": len(results), "ok": sum(1 for r in results if r.get("ok")), "failed": sum(1 for r in results if not r.get("ok")), "results": results}, ensure_ascii=False, indent=2))


def command_newsletter(args: argparse.Namespace) -> None:
    if args.confirm_newsletter != "yes":
        raise SmartEmailingError("Refusing to create newsletter without --confirm-newsletter yes")
    payload = {"email_id": int(args.email_id), "contactlists": [int(item) for item in args.contactlist_id]}
    response = api_request("POST", "newsletter", payload, insecure=args.insecure)
    print(json.dumps({"ok": True, "response": response}, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS verification only for broken local CA chains.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("test").set_defaults(func=command_test)
    p = sub.add_parser("parse")
    p.add_argument("--input", required=True)
    p.set_defaults(func=command_parse)
    d = sub.add_parser("draft")
    d.add_argument("--input", required=True)
    d.add_argument("--dry-run", action="store_true")
    d.set_defaults(func=command_draft)
    b = sub.add_parser("batch-draft")
    b.add_argument("--manifest", required=True)
    b.add_argument("--mode", choices=("continue", "stop"), default="continue")
    b.add_argument("--dry-run", action="store_true")
    b.set_defaults(func=command_batch)
    n = sub.add_parser("newsletter")
    n.add_argument("--email-id", required=True)
    n.add_argument("--contactlist-id", required=True, action="append")
    n.add_argument("--confirm-newsletter", choices=("yes", "no"), default="no")
    n.set_defaults(func=command_newsletter)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    load_env_file(args.env_file)
    load_control_center_credentials()
    try:
        args.func(args)
        return 0
    except SmartEmailingError as error:
        out = {"ok": False, "error": str(error)}
        if error.status:
            out["status"] = error.status
        if error.detail is not None:
            out["detail"] = error.detail
        print(json.dumps(out, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
