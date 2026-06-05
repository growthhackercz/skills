#!/usr/bin/env python3
"""Prepare email-writer outputs for publisher skills.

Converts Markdown email files into simple HTML/TXT files and writes a shared
email-manifest.json contract for GHL and SmartEmailing publishers.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path
from typing import Any


SUBJECT_LABELS = ("předmět", "predmet", "subject")
PREVIEW_LABELS = ("náhled textu", "nahled textu", "preview text", "preheader")
FROM_LABELS = ("odesílatel", "odesilatel", "from name", "from")
GOAL_LABELS = ("cíl", "cil", "goal")


class PrepareError(RuntimeError):
    pass


def slugify(value: str) -> str:
    raw = value.strip().lower()
    replacements = str.maketrans("áčďéěíňóřšťúůýž", "acdeeinorstuuyz")
    raw = raw.translate(replacements)
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    return raw.strip("-") or "email"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_labeled_metadata(markdown: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in markdown.splitlines():
        cleaned = line.strip()
        bold_match = re.match(r"^\*\*([^:]+):\*\*\s*(.+)$", cleaned)
        if bold_match:
            cleaned = f"{bold_match.group(1)}: {bold_match.group(2)}"
        cleaned = cleaned.strip("*").strip()
        if ":" not in cleaned:
            continue
        key, value = cleaned.split(":", 1)
        normalized = key.strip().lower()
        value = value.strip()
        if not value:
            continue
        if normalized in SUBJECT_LABELS:
            metadata["subject"] = value
        elif normalized in PREVIEW_LABELS:
            metadata["previewText"] = value
        elif normalized in FROM_LABELS:
            metadata["fromName"] = value
        elif normalized in GOAL_LABELS:
            metadata["goal"] = value
    return metadata


def parse_html_metadata(content: str) -> dict[str, str]:
    match = re.search(r"<!--\s*EMAIL METADATA\s*(.*?)-->", content, flags=re.I | re.S)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        norm = re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")
        if value.strip():
            result[norm] = value.strip().strip("*").strip()
    return {
        "id": result.get("id", ""),
        "name": result.get("name", ""),
        "subject": result.get("subject", ""),
        "previewText": result.get("preview_text", ""),
        "fromName": result.get("from_name", ""),
        "fromEmail": result.get("from_email", ""),
        "replyTo": result.get("reply_to", ""),
        "audience": result.get("audience", ""),
    }


def markdown_body(markdown: str) -> str:
    lines = markdown.splitlines()
    body_lines: list[str] = []
    in_body = False
    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            in_body = True
            continue
        if not in_body:
            continue
        if stripped.startswith("**Poznámky") or stripped.startswith("**Poznamky"):
            break
        body_lines.append(line)
    if not body_lines:
        body_lines = [line for line in lines if not re.match(r"^\*\*[^:]+:\*\*", line.strip()) and not line.startswith("#")]
    return "\n".join(body_lines).strip()


def md_to_plain(markdown: str) -> str:
    text = markdown_body(markdown)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1: \2", text)
    text = re.sub(r"[*_`#>]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def plain_to_html(plain: str, metadata: dict[str, str], campaign: str, email_id: str, name: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", plain) if part.strip()]
    body = "\n".join(f"  <p>{html.escape(paragraph).replace(chr(10), '<br>')}</p>" for paragraph in paragraphs)
    comment = "\n".join(
        [
            "<!--",
            "EMAIL METADATA",
            f"Campaign: {campaign}",
            f"Id: {email_id}",
            f"Name: {name}",
            f"Subject: {metadata.get('subject', '')}",
            f"Preview text: {metadata.get('previewText', '')}",
            f"From name: {metadata.get('fromName', '')}",
            f"From email: {metadata.get('fromEmail', '')}",
            f"Reply to: {metadata.get('replyTo', '')}",
            f"Audience: {metadata.get('audience', '')}",
            "Status: draft",
            "-->",
        ]
    )
    return f"{comment}\n<!doctype html>\n<html>\n<body>\n{body}\n</body>\n</html>\n"


def prepare_markdown(path: Path, output_dir: Path, campaign: str, index: int) -> dict[str, Any]:
    markdown = read_text(path)
    metadata = parse_labeled_metadata(markdown)
    subject = metadata.get("subject")
    if not subject:
        raise PrepareError(f"Missing subject in {path}")
    email_id = f"email-{index:03d}"
    name = path.stem.replace("-", " ").replace("_", " ").strip().title() or subject
    plain = md_to_plain(markdown)
    html_content = plain_to_html(plain, metadata, campaign, email_id, name)
    html_path = output_dir / f"{email_id}.html"
    text_path = output_dir / f"{email_id}.txt"
    html_path.write_text(html_content, encoding="utf-8")
    text_path.write_text(plain + "\n", encoding="utf-8")
    return manifest_item(email_id, name, metadata, html_path, text_path)


def prepare_html(path: Path, output_dir: Path, campaign: str, index: int) -> dict[str, Any]:
    content = read_text(path)
    metadata = parse_html_metadata(content)
    subject = metadata.get("subject") or extract_tag_text(content, "title") or extract_tag_text(content, "h1")
    if not subject:
        raise PrepareError(f"Missing subject in {path}")
    email_id = metadata.get("id") or f"email-{index:03d}"
    name = metadata.get("name") or path.stem.replace("-", " ").replace("_", " ").title()
    html_path = path
    text_path = output_dir / f"{email_id}.txt"
    if not text_path.exists():
        text_path.write_text(html_to_plain(content) + "\n", encoding="utf-8")
    metadata["subject"] = subject
    metadata["previewText"] = metadata.get("previewText", "")
    return manifest_item(email_id, name, metadata, html_path, text_path)


def extract_tag_text(content: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", content, flags=re.I | re.S)
    if not match:
        return None
    return re.sub(r"<[^>]+>", "", html.unescape(match.group(1))).strip() or None


def html_to_plain(content: str) -> str:
    cleaned = re.sub(r"<!--.*?-->", "", content, flags=re.S)
    cleaned = re.sub(r"<(br|/p|/div|/h[1-6]|/li)>", "\n", cleaned, flags=re.I)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def manifest_item(email_id: str, name: str, metadata: dict[str, str], html_path: Path, text_path: Path) -> dict[str, Any]:
    return {
        "id": email_id,
        "name": name,
        "subject": metadata.get("subject", ""),
        "previewText": metadata.get("previewText", ""),
        "fromName": metadata.get("fromName", ""),
        "fromEmail": metadata.get("fromEmail", ""),
        "replyTo": metadata.get("replyTo", ""),
        "audience": metadata.get("audience", ""),
        "htmlPath": str(html_path.resolve()),
        "textPath": str(text_path.resolve()),
        "status": "draft",
    }


def source_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    files = sorted(input_path.glob("*.html"))
    if not files:
        files = sorted(input_path.glob("*.md"))
    return [path for path in files if path.name != "email-manifest.json"]


def prepare(args: argparse.Namespace) -> None:
    input_path = Path(args.input).expanduser()
    if not input_path.exists():
        raise PrepareError(f"Input does not exist: {input_path}")
    output_dir = input_path if input_path.is_dir() else input_path.parent
    campaign = args.campaign or slugify(output_dir.name)
    items = []
    errors = []
    for index, path in enumerate(source_files(input_path), start=1):
        try:
            if path.suffix.lower() == ".html":
                items.append(prepare_html(path, output_dir, campaign, index))
            elif path.suffix.lower() == ".md":
                items.append(prepare_markdown(path, output_dir, campaign, index))
        except PrepareError as error:
            errors.append({"path": str(path), "error": str(error)})
            if args.mode != "continue":
                break
    manifest = {
        "campaign": campaign,
        "timezone": args.timezone,
        "defaultPublishIntent": "draft",
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "emails": items,
        "errors": errors,
    }
    manifest_path = output_dir / "email-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not errors, "manifest": str(manifest_path.resolve()), "emails": len(items), "errors": errors}, ensure_ascii=False, indent=2))


def validate(args: argparse.Namespace) -> None:
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    errors = []
    for item in manifest.get("emails", []):
        for key in ("id", "subject", "htmlPath", "textPath"):
            if not item.get(key):
                errors.append({"id": item.get("id"), "error": f"missing {key}"})
        for path_key in ("htmlPath", "textPath"):
            if item.get(path_key) and not Path(item[path_key]).exists():
                errors.append({"id": item.get("id"), "error": f"missing file {path_key}: {item[path_key]}"})
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--input", required=True)
    p.add_argument("--campaign")
    p.add_argument("--timezone", default="Europe/Prague")
    p.add_argument("--mode", choices=("continue", "stop"), default="continue")
    p.set_defaults(func=prepare)
    v = sub.add_parser("validate")
    v.add_argument("--manifest", required=True)
    v.set_defaults(func=validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except PrepareError as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
