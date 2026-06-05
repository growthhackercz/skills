#!/usr/bin/env python3
"""Create CliqSales/GoHighLevel email campaign drafts from email HTML files."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_ENV_FILES = (
    "/home/node/.openclaw/secrets/cliqsales.env",
    "/home/node/.openclaw/secrets/ghl.env",
    "/home/node/.openclaw/.env",
)
DEFAULT_API_BASE_URL = "https://services.leadconnectorhq.com"
DEFAULT_API_VERSION = "2023-02-21"
DEFAULT_TIME_ZONE = "Europe/Prague"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 "
    "ControlCenterCliqSalesEmailPublisher/1.0"
)


class GHLMailError(RuntimeError):
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


def load_env_file(path: str | None) -> None:
    candidates = [path] if path else list(DEFAULT_ENV_FILES)
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
        return


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise GHLMailError(f"Missing required environment variable: {name}")
    return value


def sanitize_location_id(raw: str) -> str:
    value = raw.strip()
    match = re.search(r"/location/([A-Za-z0-9]+)/?", value)
    if match:
        value = match.group(1)
    return value.removeprefix("loc_").strip()


def first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def read_json(path: str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GHLMailError(f"Expected JSON object in {path}")
    return data


def strip_tags(value: str) -> str:
    text = re.sub(r"<(br|/p|/div|/h[1-6]|/li)>", "\n", value, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_tag(content: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", content, flags=re.I | re.S)
    return strip_tags(match.group(1)) if match else None


def parse_metadata(content: str) -> dict[str, str]:
    match = re.search(r"<!--\s*EMAIL METADATA\s*(.*?)-->", content, flags=re.I | re.S)
    output: dict[str, str] = {}
    if not match:
        return output
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized = re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")
        if normalized and value.strip():
            output[normalized] = value.strip().strip("*").strip()
    return output


def clean_html(content: str) -> str:
    return re.sub(r"<!--\s*EMAIL METADATA\s*.*?-->\s*", "", content, flags=re.I | re.S).strip()


def email_from_html(path: str) -> dict[str, Any]:
    html_path = Path(path)
    content = html_path.read_text(encoding="utf-8", errors="replace")
    meta = parse_metadata(content)
    subject = first_string(meta.get("subject"), extract_tag(content, "title"), extract_tag(content, "h1"))
    if not subject:
        raise GHLMailError(f"Missing subject in {path}")
    text_path = html_path.with_suffix(".txt")
    text = text_path.read_text(encoding="utf-8", errors="replace").strip() if text_path.exists() else strip_tags(clean_html(content))
    return {
        "id": first_string(meta.get("id"), html_path.stem),
        "name": first_string(meta.get("name"), subject),
        "subject": subject,
        "previewText": first_string(meta.get("preview_text"), meta.get("preheader")) or "",
        "fromName": first_string(meta.get("from_name"), os.environ.get("GHL_FROM_NAME")) or "",
        "fromEmail": first_string(meta.get("from_email"), os.environ.get("GHL_FROM_EMAIL")) or "",
        "replyTo": first_string(meta.get("reply_to"), os.environ.get("GHL_REPLY_TO")) or "",
        "html": clean_html(content),
        "text": text,
        "htmlPath": str(html_path),
        "textPath": str(text_path) if text_path.exists() else "",
    }


def email_from_manifest_item(item: dict[str, Any]) -> dict[str, Any]:
    data = email_from_html(str(item["htmlPath"]))
    for source_key, target_key in (
        ("id", "id"),
        ("name", "name"),
        ("subject", "subject"),
        ("previewText", "previewText"),
        ("fromName", "fromName"),
        ("fromEmail", "fromEmail"),
        ("replyTo", "replyTo"),
    ):
        if item.get(source_key):
            data[target_key] = item[source_key]
    if item.get("textPath") and Path(item["textPath"]).exists():
        data["text"] = Path(item["textPath"]).read_text(encoding="utf-8", errors="replace").strip()
    return data


def manifest_emails(path: str) -> list[dict[str, Any]]:
    data = read_json(path)
    emails = data.get("emails")
    if not isinstance(emails, list):
        raise GHLMailError(f"Manifest missing emails[]: {path}")
    return [email_from_manifest_item(item) for item in emails if isinstance(item, dict)]


def json_dumps(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def api_request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    base_url = os.environ.get("GHL_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")
    token = require_env("GHL_API_KEY")
    version = os.environ.get("GHL_API_VERSION", DEFAULT_API_VERSION)
    request = urllib.request.Request(f"{base_url}{path}", data=json_dumps(payload) if payload is not None else None, method=method)
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Version", version)
    request.add_header("Content-Type", "application/json")
    request.add_header("Accept", "application/json")
    # LeadConnector can block Python's default urllib signature via Cloudflare 1010.
    request.add_header("User-Agent", os.environ.get("GHL_USER_AGENT", DEFAULT_USER_AGENT))
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            detail: Any = json.loads(raw)
        except json.JSONDecodeError:
            detail = raw
        raise GHLMailError(f"GHL API error {error.code} for {method} {path}", error.code, detail) from error


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


def template_id(response: dict[str, Any]) -> str | None:
    found = find_in_tree(response, {"templateId", "template_id", "id", "_id"})
    return str(found) if found else None


def campaign_id(response: dict[str, Any]) -> str | None:
    found = find_in_tree(response, {"campaignId", "campaign_id", "id", "_id"})
    return str(found) if found else None


def campaign_path(location_id: str, suffix: str = "") -> str:
    encoded = urllib.parse.quote(location_id)
    return f"/emails/public/v2/locations/{encoded}/campaigns{suffix}"


def campaign_user_id(dry_run: bool = False) -> str:
    if dry_run:
        return os.environ.get("GHL_USER_ID") or os.environ.get("GHL_USER") or "DRY_RUN_USER"
    return first_string(os.environ.get("GHL_USER_ID"), os.environ.get("GHL_USER")) or require_env("GHL_USER")


def campaign_time_zone(dry_run: bool = False) -> str:
    if dry_run:
        return os.environ.get("GHL_TIME_ZONE") or os.environ.get("TZ") or DEFAULT_TIME_ZONE
    return first_string(os.environ.get("GHL_TIME_ZONE"), os.environ.get("TZ")) or DEFAULT_TIME_ZONE


def public_campaign_fields(campaign: dict[str, Any]) -> dict[str, Any]:
    return {
        key: campaign.get(key)
        for key in ("id", "_id", "campaignId", "name", "title", "subject", "status", "campaignStatus", "createdAt", "updatedAt")
        if key in campaign
    }


def build_template_payload(email: dict[str, Any], location_id: str) -> dict[str, Any]:
    return {
        "locationId": location_id,
        "name": email["name"],
        "title": email["name"],
        "type": "html",
        "editorType": "html",
        "editorContent": email["html"],
        "html": email["html"],
        "subject": email["subject"],
        "previewText": email.get("previewText") or "",
        "fromName": email.get("fromName") or "",
        "fromEmail": email.get("fromEmail") or "",
        "replyTo": email.get("replyTo") or "",
    }


def build_update_payload(email: dict[str, Any], location_id: str, template_id_value: str) -> dict[str, Any]:
    return {
        "locationId": location_id,
        "templateId": template_id_value,
        "name": email["name"],
        "editorType": "html",
        "editorContent": email["html"],
        "subject": email["subject"],
        "previewText": email.get("previewText") or "",
        "fromName": email.get("fromName") or "",
        "fromEmail": email.get("fromEmail") or "",
        "replyTo": email.get("replyTo") or "",
    }


def build_campaign_payload(email: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    user_id = campaign_user_id(dry_run=dry_run)
    from_email = first_string(email.get("fromEmail"), os.environ.get("GHL_FROM_EMAIL"), os.environ.get("GHL_USER"), user_id) or ""
    reply_to = first_string(email.get("replyTo"), os.environ.get("GHL_REPLY_TO"), from_email) or ""
    return {
        "name": email["name"],
        "title": email["name"],
        "subject": email["subject"],
        "previewText": email.get("previewText") or "",
        "fromName": first_string(email.get("fromName"), os.environ.get("GHL_FROM_NAME")) or "",
        "fromEmail": from_email,
        "replyTo": reply_to,
        "replyToEmail": reply_to,
        "html": email["html"],
        "editorContent": email["html"],
        "editorType": "html",
        "type": "html",
        "timeZone": campaign_time_zone(dry_run=dry_run),
        "userId": user_id,
    }


def create_template_draft(email: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    location_id = "DRY_RUN_LOCATION" if dry_run else sanitize_location_id(require_env("GHL_LOCATION_ID"))
    payload = {k: v for k, v in build_template_payload(email, location_id).items() if v not in ("", None)}
    if dry_run:
        return {"ok": True, "dryRun": True, "target": "email_builder_template", "payloadKeys": sorted(payload.keys()), "subject": email["subject"]}
    try:
        response = api_request("POST", "/emails/builder", payload)
    except GHLMailError as error:
        if error.status != 422:
            raise
        minimal = {"locationId": location_id, "name": email["name"], "type": "html"}
        response = api_request("POST", "/emails/builder", minimal)
    tid = template_id(response)
    if tid:
        update_payload = {k: v for k, v in build_update_payload(email, location_id, tid).items() if v not in ("", None)}
        try:
            update_response = api_request("PATCH", f"/emails/builder/{urllib.parse.quote(tid)}", update_payload)
        except GHLMailError:
            update_response = api_request("POST", "/emails/builder/data", update_payload)
        return {"ok": True, "templateId": tid, "subject": email["subject"], "response": response, "updateResponse": update_response}
    return {"ok": True, "templateId": None, "subject": email["subject"], "response": response}


def create_draft(email: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    location_id = "DRY_RUN_LOCATION" if dry_run else sanitize_location_id(require_env("GHL_LOCATION_ID"))
    payload = {k: v for k, v in build_campaign_payload(email, dry_run=dry_run).items() if v not in ("", None)}
    if dry_run:
        return {"ok": True, "dryRun": True, "target": "email_campaign_draft", "payloadKeys": sorted(payload.keys()), "subject": email["subject"]}
    response = api_request("POST", campaign_path(location_id, "/email-campaign"), payload)
    cid = campaign_id(response)
    return {
        "ok": True,
        "target": "email_campaign_draft",
        "campaignId": cid,
        "subject": email["subject"],
        "status": response.get("status") if isinstance(response, dict) else None,
        "response": response,
    }


def command_test(args: argparse.Namespace) -> None:
    location_id = sanitize_location_id(require_env("GHL_LOCATION_ID"))
    response = api_request("GET", campaign_path(location_id, "/emails?limit=10"))
    print(json.dumps({
        "ok": True,
        "target": "email_campaign_draft",
        "locationId": location_id,
        "responseKeys": sorted(response.keys()),
        "total": response.get("total"),
    }, ensure_ascii=False, indent=2))


def command_parse(args: argparse.Namespace) -> None:
    email = email_from_html(args.input)
    email["html"] = f"<redacted html: {len(email['html'])} chars>"
    email["text"] = f"<redacted text: {len(email['text'])} chars>"
    print(json.dumps(email, ensure_ascii=False, indent=2))


def command_draft(args: argparse.Namespace) -> None:
    print(json.dumps(create_draft(email_from_html(args.input), dry_run=args.dry_run), ensure_ascii=False, indent=2))


def command_batch(args: argparse.Namespace) -> None:
    results = []
    for email in manifest_emails(args.manifest):
        try:
            results.append({"id": email.get("id"), **create_draft(email, dry_run=args.dry_run)})
        except GHLMailError as error:
            results.append({"id": email.get("id"), "ok": False, "error": str(error), "status": error.status, "detail": error.detail})
            if args.mode != "continue":
                break
    print(json.dumps({"total": len(results), "ok": sum(1 for r in results if r.get("ok")), "failed": sum(1 for r in results if not r.get("ok")), "results": results}, ensure_ascii=False, indent=2))


def command_update(args: argparse.Namespace) -> None:
    if args.confirm_update != "yes":
        raise GHLMailError("Refusing to update an existing GHL email campaign draft without --confirm-update yes")
    location_id = sanitize_location_id(require_env("GHL_LOCATION_ID"))
    email = email_from_html(args.input)
    payload = {k: v for k, v in build_campaign_payload(email).items() if v not in ("", None)}
    response = api_request("PATCH", campaign_path(location_id, f"/{urllib.parse.quote(args.campaign_id)}"), payload)
    print(json.dumps({
        "ok": True,
        "target": "email_campaign_draft",
        "campaignId": args.campaign_id,
        "response": response,
    }, ensure_ascii=False, indent=2))


def command_readback(args: argparse.Namespace) -> None:
    location_id = sanitize_location_id(require_env("GHL_LOCATION_ID"))
    response = api_request("GET", campaign_path(location_id, "/emails?limit=20"))
    campaigns = response.get("campaigns") if isinstance(response, dict) else None
    if not isinstance(campaigns, list):
        raise GHLMailError("Unexpected GHL campaign list response", detail=response)
    matches = []
    for campaign in campaigns:
        if not isinstance(campaign, dict):
            continue
        ids = {
            first_string(campaign.get("id")) or "",
            first_string(campaign.get("_id")) or "",
            first_string(campaign.get("campaignId")) or "",
        }
        if args.campaign_id in ids:
            matches.append(public_campaign_fields(campaign))
    print(json.dumps({
        "ok": True,
        "target": "email_campaign_draft",
        "campaignId": args.campaign_id,
        "matchCount": len(matches),
        "matches": matches,
    }, ensure_ascii=False, indent=2))


def command_template_draft(args: argparse.Namespace) -> None:
    print(json.dumps(create_template_draft(email_from_html(args.input), dry_run=args.dry_run), ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("test").set_defaults(func=command_test)
    p = sub.add_parser("parse")
    p.add_argument("--input", required=True)
    p.set_defaults(func=command_parse)
    d = sub.add_parser("draft")
    d.add_argument("--input", required=True)
    d.add_argument("--dry-run", action="store_true")
    d.set_defaults(func=command_draft)
    td = sub.add_parser("template-draft")
    td.add_argument("--input", required=True)
    td.add_argument("--dry-run", action="store_true")
    td.set_defaults(func=command_template_draft)
    b = sub.add_parser("batch-draft")
    b.add_argument("--manifest", required=True)
    b.add_argument("--mode", choices=("continue", "stop"), default="continue")
    b.add_argument("--dry-run", action="store_true")
    b.set_defaults(func=command_batch)
    u = sub.add_parser("update")
    u.add_argument("--campaign-id", required=True)
    u.add_argument("--input", required=True)
    u.add_argument("--confirm-update", choices=("yes", "no"), default="no")
    u.set_defaults(func=command_update)
    r = sub.add_parser("readback")
    r.add_argument("--campaign-id", required=True)
    r.set_defaults(func=command_readback)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    load_env_file(args.env_file)
    try:
        args.func(args)
        return 0
    except GHLMailError as error:
        out = {"ok": False, "error": str(error)}
        if error.status:
            out["status"] = error.status
        if error.detail is not None:
            out["detail"] = error.detail
        print(json.dumps(out, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
