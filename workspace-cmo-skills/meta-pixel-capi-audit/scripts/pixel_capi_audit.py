#!/usr/bin/env python3
"""Read-only Meta Pixel/CAPI audit helper from sanitized evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


CLIENT_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
PII_KEYS = {
    "email",
    "phone",
    "first_name",
    "last_name",
    "firstname",
    "lastname",
    "client_ip_address",
    "client_user_agent",
    "user_agent",
    "ip",
    "ua",
    "fbp",
    "fbc",
}
FIELD_WEIGHTS = {
    "em": 2.1,
    "ph": 1.8,
    "fn": 0.7,
    "ln": 0.7,
    "external_id": 1.0,
    "fbp": 0.9,
    "fbc": 0.9,
    "client_ip_address": 0.6,
    "client_user_agent": 0.6,
    "ct": 0.4,
    "st": 0.3,
    "zp": 0.4,
    "country": 0.3,
    "db": 0.3,
    "ge": 0.2,
}


class AuditError(RuntimeError):
    pass


def parse_date(value: str | None) -> str:
    if not value:
        return dt.date.today().isoformat()
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD") from exc


def validate_client(value: str) -> str:
    client = value.strip()
    if not CLIENT_RE.match(client):
        raise argparse.ArgumentTypeError("client must be a slug: letters, digits, dot, underscore or dash")
    return client


def output_dir(client: str, audit_date: str) -> str:
    return str(PurePosixPath("/documents") / client / "meta-ads" / "pixel-capi-audits" / audit_date)


def load_json(path: str) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuditError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AuditError("Evidence must be a JSON object")
    return payload


def assert_no_pii(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = re.sub(r"[^a-z0-9_]+", "_", str(key).strip().lower())
            if normalized in PII_KEYS and normalized not in {"client_ip_address", "client_user_agent"}:
                raise AuditError(f"Evidence contains raw PII-like key at {path}.{key}; use matchingFields names only")
            if normalized in {"client_ip_address", "client_user_agent", "user_agent", "fbp", "fbc"} and not isinstance(item, bool):
                raise AuditError(f"Evidence contains raw client metadata at {path}.{key}; use matchingFields names only")
            assert_no_pii(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_pii(item, f"{path}[{index}]")


def normalize_field(value: Any) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower()).strip("_")


def estimate_emq(fields: list[str]) -> float:
    score = 0.0
    for field in sorted({normalize_field(field) for field in fields}):
        score += FIELD_WEIGHTS.get(field, 0.0)
    return round(min(score, 10.0), 1)


def target_for_event(name: str) -> float:
    key = normalize_field(name)
    if key == "purchase":
        return 9.3
    if key in {"lead", "complete_registration", "contact", "subscribe"}:
        return 8.0
    return 7.0


def event_findings(event: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    name = str(event.get("eventName") or event.get("name") or "Unknown").strip() or "Unknown"
    fields = [normalize_field(field) for field in event.get("matchingFields", []) if normalize_field(field)]
    emq = estimate_emq(fields)
    target = target_for_event(name)
    findings: list[dict[str, Any]] = []

    browser = bool(event.get("browserPixel"))
    server = bool(event.get("serverCapi"))
    dedup = bool(event.get("eventIdDedup"))
    test_seen = bool(event.get("testEventSeen"))

    if not browser:
        findings.append({"eventName": name, "severity": "critical", "code": "missing_browser_pixel", "message": "Browser Pixel event is not evidenced."})
    if not server:
        findings.append({"eventName": name, "severity": "critical", "code": "missing_capi", "message": "Server-side CAPI event is not evidenced."})
    if browser and server and not dedup:
        findings.append({"eventName": name, "severity": "critical", "code": "missing_event_id_dedup", "message": "Browser and server events need shared event_id deduplication."})
    if "em" not in fields:
        findings.append({"eventName": name, "severity": "warning", "code": "missing_email_match", "message": "Email matching field is missing."})
    if "fbp" not in fields or "fbc" not in fields:
        findings.append({"eventName": name, "severity": "warning", "code": "missing_click_cookies", "message": "fbp/fbc capture is incomplete."})
    if emq < target:
        findings.append({"eventName": name, "severity": "warning", "code": "low_estimated_emq", "message": f"Estimated EMQ {emq} is below target {target}."})
    if not test_seen:
        findings.append({"eventName": name, "severity": "info", "code": "missing_test_event_evidence", "message": "No Test Events evidence was provided."})

    return {
        "eventName": name,
        "browserPixel": browser,
        "serverCapi": server,
        "eventIdDedup": dedup,
        "matchingFields": fields,
        "estimatedEmq": emq,
        "targetEmq": target,
        "testEventSeen": test_seen,
    }, findings


def recommendation_for_finding(finding: dict[str, Any]) -> str:
    code = finding["code"]
    event = finding["eventName"]
    if code == "missing_browser_pixel":
        return f"Install or verify browser Pixel event for {event}."
    if code == "missing_capi":
        return f"Add server-side CAPI event for {event}."
    if code == "missing_event_id_dedup":
        return f"Pass the same event_id from browser Pixel to CAPI for {event}."
    if code == "missing_email_match":
        return f"Pass hashed email as `em` for {event} when consent and data collection allow it."
    if code == "missing_click_cookies":
        return f"Capture `_fbp` and `_fbc` and pass them server-side for {event}."
    if code == "low_estimated_emq":
        return f"Improve matching fields for {event}; prioritize em, ph, fbp, fbc, IP and user agent."
    if code == "missing_test_event_evidence":
        return f"Verify {event} in Meta Events Manager Test Events."
    return f"Review {event}."


def build_summary(client: str, audit_date: str, evidence: dict[str, Any]) -> dict[str, Any]:
    assert_no_pii(evidence)
    events_input = evidence.get("events")
    if not isinstance(events_input, list):
        events_input = []
    events: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for item in events_input:
        if isinstance(item, dict):
            event, event_level_findings = event_findings(item)
            events.append(event)
            findings.extend(event_level_findings)
    recommendations = [
        {"text": recommendation_for_finding(finding), "source": finding["code"], "readOnly": True}
        for finding in findings
    ]
    return {
        "client": client,
        "date": audit_date,
        "readOnly": True,
        "pixelId": str(evidence.get("pixelId") or ""),
        "platform": str(evidence.get("platform") or "unknown"),
        "events": events,
        "findings": findings,
        "recommendations": recommendations,
        "dataQuality": {
            "status": "ok" if events else "insufficient_data",
            "notes": [] if events else ["No sanitized Pixel/CAPI event evidence was provided."],
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Meta Pixel CAPI Audit",
        "",
        f"- Client: `{summary['client']}`",
        f"- Date: `{summary['date']}`",
        f"- Platform: `{summary['platform']}`",
        f"- Pixel ID: `{summary['pixelId'] or 'unknown'}`",
        "- Mode: read-only",
        "",
        "## Event Scorecard",
    ]
    if not summary["events"]:
        lines.append("- No event evidence provided.")
    for event in summary["events"]:
        lines.append(
            f"- {event['eventName']}: browser={event['browserPixel']} "
            f"capi={event['serverCapi']} dedup={event['eventIdDedup']} "
            f"estimated EMQ={event['estimatedEmq']}/{event['targetEmq']}"
        )
    lines.extend(["", "## Findings"])
    if not summary["findings"]:
        lines.append("- No findings from provided evidence.")
    for finding in summary["findings"]:
        lines.append(f"- {finding['severity']}: {finding['eventName']} - {finding['message']}")
    lines.extend(["", "## Read-only Fix List"])
    if not summary["recommendations"]:
        lines.append("- No fixes suggested from provided evidence.")
    for recommendation in summary["recommendations"]:
        lines.append(f"- {recommendation['text']}")
    lines.extend(["", "## Verification Note", "- EMQ values are estimates. Verify actual scores in Meta Events Manager."])
    return "\n".join(lines) + "\n"


def command_validate(args: argparse.Namespace) -> int:
    audit_date = parse_date(args.date)
    payload = {
        "ok": True,
        "readOnly": True,
        "client": args.client,
        "date": audit_date,
        "outputDir": output_dir(args.client, audit_date),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_dry_run(args: argparse.Namespace) -> int:
    audit_date = parse_date(args.date)
    payload = {
        "ok": True,
        "readOnly": True,
        "client": args.client,
        "date": audit_date,
        "outputDir": output_dir(args.client, audit_date),
        "checks": [
            "browser_pixel",
            "server_capi",
            "event_id_dedup",
            "advanced_matching",
            "fbp_fbc",
            "test_events_evidence",
        ],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_audit(args: argparse.Namespace) -> int:
    audit_date = parse_date(args.date)
    evidence = load_json(args.input)
    summary = build_summary(args.client, audit_date, evidence)
    out_dir = Path(args.output_dir or output_dir(args.client, audit_date))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "report.md").write_text(render_report(summary), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "readOnly": True,
        "outputDir": str(out_dir),
        "files": ["summary.json", "report.md"],
        "findings": len(summary["findings"]),
        "dataQuality": summary["dataQuality"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--client", required=True, type=validate_client, help="Client/project slug under /documents.")
    parser.add_argument("--date", help="Audit date in YYYY-MM-DD; defaults to today.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Meta Pixel/CAPI audit helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate output contract arguments.")
    add_common_args(validate_parser)
    validate_parser.set_defaults(func=command_validate)

    dry_run_parser = subparsers.add_parser("dry-run", help="Print the audit plan without reading evidence.")
    add_common_args(dry_run_parser)
    dry_run_parser.set_defaults(func=command_dry_run)

    audit_parser = subparsers.add_parser("audit", help="Render audit from sanitized evidence JSON.")
    add_common_args(audit_parser)
    audit_parser.add_argument("--input", required=True, help="Sanitized evidence JSON file.")
    audit_parser.add_argument("--output-dir", help="Output audit directory.")
    audit_parser.set_defaults(func=command_audit)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except AuditError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
