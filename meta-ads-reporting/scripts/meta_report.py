#!/usr/bin/env python3
"""Validate, plan, and render Meta Ads reporting jobs.

This helper intentionally does not call Meta. Agents collect raw read-only JSON
with the official ``meta`` CLI, then this helper renders deterministic reports
from those files.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


MODES = (
    "daily-check",
    "overview",
    "winners",
    "bleeders",
    "creative-fatigue",
    "budget-efficiency",
    "budget-recommendations",
    "weekly-brief",
    "dashboard",
    "anomaly-detection",
)

THRESHOLDS = {
    "bleederCtrLt": 0.01,
    "highFrequencyGt": 3.5,
    "fatigueCtrDropGt": 0.20,
    "cpcSpikeGt": 0.30,
    "cpmSpikeGt": 0.25,
    "dailySpendNoiseLt": 50,
}

CLIENT_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
NUMBER_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


class ReportError(RuntimeError):
    pass


def parse_report_date(value: str | None) -> str:
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


def output_dir(client: str, report_date: str, mode: str) -> str:
    return str(PurePosixPath("/documents") / client / "meta-ads" / "reports" / f"{report_date}-{mode}")


def command_plan(mode: str) -> list[list[str]]:
    base = [
        ["meta", "-o", "json", "ads", "campaign", "list"],
        ["meta", "-o", "json", "ads", "adset", "list"],
        ["meta", "-o", "json", "ads", "ad", "list"],
        ["meta", "-o", "json", "ads", "insights", "list"],
    ]
    if mode in {"daily-check", "overview", "weekly-brief", "dashboard"}:
        return base
    if mode in {"winners", "bleeders", "creative-fatigue", "budget-efficiency", "budget-recommendations", "anomaly-detection"}:
        return [base[0], base[2], base[3]]
    return base


def parse_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if text.endswith("%"):
        text = text[:-1].strip()
    if not NUMBER_RE.match(text):
        return None
    return float(text)


def metric_ratio(record: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        raw = record.get(key)
        value = parse_float(raw)
        if value is None:
            continue
        if isinstance(raw, str) and raw.strip().endswith("%"):
            return value / 100
        if value > 1 and key in {"ctr", "inline_link_click_ctr", "outbound_ctr"}:
            return value / 100
        return value
    return None


def metric_number(record: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = parse_float(record.get(key))
        if value is not None:
            return value
    return None


def first_string(record: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, int):
            return str(value)
    return None


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReportError(f"Invalid JSON in {path}: {exc}") from exc


def collect_records(value: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(value, list):
        for item in value:
            records.extend(collect_records(item))
    elif isinstance(value, dict):
        data = value.get("data")
        if isinstance(data, list):
            records.extend(collect_records(data))
        elif any(key in value for key in ("campaign_id", "ad_id", "adset_id", "ctr", "spend", "impressions")):
            records.append(value)
        else:
            for key in ("campaigns", "adsets", "ads", "insights", "items", "results"):
                nested = value.get(key)
                if isinstance(nested, list):
                    records.extend(collect_records(nested))
    return records


def load_raw_records(raw_dir: Path) -> list[dict[str, Any]]:
    if not raw_dir.exists():
        raise ReportError(f"raw dir does not exist: {raw_dir}")
    records: list[dict[str, Any]] = []
    for path in sorted(raw_dir.glob("*.json")):
        for record in collect_records(load_json(path)):
            item = dict(record)
            item["_rawFile"] = path.name
            records.append(item)
    return records


def normalized_record(record: dict[str, Any]) -> dict[str, Any]:
    ctr = metric_ratio(record, "ctr", "inline_link_click_ctr", "outbound_ctr")
    spend = metric_number(record, "spend")
    cpc = metric_number(record, "cpc", "cost_per_inline_link_click", "cost_per_unique_click")
    cpm = metric_number(record, "cpm")
    frequency = metric_number(record, "frequency")
    impressions = metric_number(record, "impressions")
    clicks = metric_number(record, "clicks", "inline_link_clicks", "outbound_clicks")
    results = metric_number(record, "results", "conversions", "actions")
    return {
        "id": first_string(record, "ad_id", "adset_id", "campaign_id", "id") or "unknown",
        "name": first_string(record, "ad_name", "adset_name", "campaign_name", "name") or "Unnamed",
        "level": "ad" if first_string(record, "ad_id") else "adset" if first_string(record, "adset_id") else "campaign",
        "status": first_string(record, "status", "effective_status") or "unknown",
        "spend": spend,
        "ctr": ctr,
        "cpc": cpc,
        "cpm": cpm,
        "frequency": frequency,
        "impressions": impressions,
        "clicks": clicks,
        "results": results,
        "rawFile": record.get("_rawFile"),
        "previousCtr": metric_ratio(record, "previous_ctr", "ctr_previous", "ctrPrev"),
        "previousCpc": metric_number(record, "previous_cpc", "cpc_previous", "cpcPrev"),
        "previousCpm": metric_number(record, "previous_cpm", "cpm_previous", "cpmPrev"),
    }


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"


def money(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def detect_signals(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    bleeders: list[dict[str, Any]] = []
    winners: list[dict[str, Any]] = []
    fatigue: list[dict[str, Any]] = []
    for row in rows:
        spend = row.get("spend")
        ctr = row.get("ctr")
        frequency = row.get("frequency")
        cpc = row.get("cpc")
        cpm = row.get("cpm")
        if spend is not None and spend < THRESHOLDS["dailySpendNoiseLt"]:
            continue
        if ctr is not None and ctr < THRESHOLDS["bleederCtrLt"]:
            bleeders.append({"type": "low_ctr", "severity": "warning", "item": row})
        if frequency is not None and frequency > THRESHOLDS["highFrequencyGt"]:
            fatigue.append({"type": "high_frequency", "severity": "warning", "item": row})
        previous_ctr = row.get("previousCtr")
        if ctr is not None and previous_ctr and previous_ctr > 0:
            drop = (previous_ctr - ctr) / previous_ctr
            if drop > THRESHOLDS["fatigueCtrDropGt"]:
                fatigue.append({"type": "ctr_drop", "severity": "warning", "drop": drop, "item": row})
        previous_cpc = row.get("previousCpc")
        if cpc is not None and previous_cpc and previous_cpc > 0:
            spike = (cpc - previous_cpc) / previous_cpc
            if spike > THRESHOLDS["cpcSpikeGt"]:
                fatigue.append({"type": "cpc_spike", "severity": "warning", "spike": spike, "item": row})
        previous_cpm = row.get("previousCpm")
        if cpm is not None and previous_cpm and previous_cpm > 0:
            spike = (cpm - previous_cpm) / previous_cpm
            if spike > THRESHOLDS["cpmSpikeGt"]:
                fatigue.append({"type": "cpm_spike", "severity": "warning", "spike": spike, "item": row})
    ranked = [row for row in rows if row.get("ctr") is not None]
    ranked.sort(key=lambda item: (item.get("ctr") or 0, -(item.get("cpc") or 999999)), reverse=True)
    winners = [{"type": "high_ctr", "severity": "info", "item": item} for item in ranked[:5]]
    return winners, bleeders, fatigue


def recommendation_text(signal: dict[str, Any]) -> str:
    item = signal["item"]
    name = item["name"]
    signal_type = signal["type"]
    if signal_type == "low_ctr":
        return f"Review or refresh creative for {name}; CTR is {pct(item.get('ctr'))}."
    if signal_type == "high_frequency":
        return f"Check audience saturation for {name}; frequency is {money(item.get('frequency'))}."
    if signal_type == "ctr_drop":
        return f"Investigate creative fatigue on {name}; CTR dropped by {pct(signal.get('drop'))}."
    if signal_type == "cpc_spike":
        return f"Investigate CPC movement on {name}; CPC spike is {pct(signal.get('spike'))}."
    if signal_type == "cpm_spike":
        return f"Investigate CPM movement on {name}; CPM spike is {pct(signal.get('spike'))}."
    if signal_type == "high_ctr":
        return f"Consider controlled scale test for {name}; CTR is {pct(item.get('ctr'))}."
    return f"Review {name}."


def build_summary(client: str, mode: str, report_date: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    winners, bleeders, fatigue = detect_signals(rows)
    signals = winners + bleeders + fatigue
    recommendations = [{"text": recommendation_text(signal), "readOnly": True, "source": signal["type"]} for signal in signals]
    total_spend = sum(row["spend"] for row in rows if isinstance(row.get("spend"), (int, float)))
    return {
        "client": client,
        "reportType": mode,
        "date": report_date,
        "readOnly": True,
        "accountId": None,
        "period": {"since": None, "until": report_date},
        "metrics": {
            "rowCount": len(rows),
            "totalSpend": round(total_spend, 2),
        },
        "signals": signals,
        "recommendations": recommendations,
        "thresholds": THRESHOLDS,
        "dataQuality": {
            "status": "ok" if rows else "insufficient_data",
            "notes": [] if rows else ["No raw Meta Ads JSON records were available."],
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# Meta Ads {summary['reportType']} Report",
        "",
        f"- Client: `{summary['client']}`",
        f"- Date: `{summary['date']}`",
        "- Mode: read-only",
        f"- Raw rows: {summary['metrics']['rowCount']}",
        f"- Total spend: {money(summary['metrics']['totalSpend'])}",
        "",
        "## Signals",
    ]
    if not summary["signals"]:
        lines.append("- No strong signals detected from available data.")
    for signal in summary["signals"][:20]:
        item = signal["item"]
        lines.append(
            f"- {signal['type']}: {item['name']} | spend {money(item.get('spend'))} | "
            f"CTR {pct(item.get('ctr'))} | freq {money(item.get('frequency'))}"
        )
    lines.extend(["", "## Read-only Recommendations"])
    if not summary["recommendations"]:
        lines.append("- No recommendations from available data.")
    for recommendation in summary["recommendations"][:20]:
        lines.append(f"- {recommendation['text']}")
    lines.extend(["", "## Limits"])
    for note in summary["dataQuality"]["notes"]:
        lines.append(f"- {note}")
    if not summary["dataQuality"]["notes"]:
        lines.append("- Recommendations are read-only and require human review before any Meta change.")
    return "\n".join(lines) + "\n"


def render_dashboard(summary: dict[str, Any]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(signal['type'])}</td>"
        f"<td>{html.escape(signal['item']['name'])}</td>"
        f"<td>{money(signal['item'].get('spend'))}</td>"
        f"<td>{pct(signal['item'].get('ctr'))}</td>"
        f"<td>{money(signal['item'].get('frequency'))}</td>"
        "</tr>"
        for signal in summary["signals"][:50]
    )
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Meta Ads {html.escape(summary['reportType'])} Dashboard</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #151515; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #ddd; padding: 8px; text-align: left; }}
.muted {{ color: #666; }}
</style>
<h1>Meta Ads {html.escape(summary['reportType'])}</h1>
<p class="muted">Read-only report for {html.escape(summary['client'])} on {html.escape(summary['date'])}</p>
<p>Total spend: {money(summary['metrics']['totalSpend'])} | Raw rows: {summary['metrics']['rowCount']}</p>
<table>
<thead><tr><th>Signal</th><th>Item</th><th>Spend</th><th>CTR</th><th>Frequency</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</html>
"""


def build_payload(args: argparse.Namespace) -> dict[str, object]:
    report_date = parse_report_date(args.date)
    out_dir = output_dir(args.client, report_date, args.mode)
    files = ["raw/", "summary.json", "report.md"]
    if args.mode == "dashboard":
        files.append("dashboard.html")
    return {
        "ok": True,
        "readOnly": True,
        "client": args.client,
        "mode": args.mode,
        "date": report_date,
        "outputDir": out_dir,
        "files": files,
        "thresholds": THRESHOLDS,
        "plannedCommands": command_plan(args.mode),
    }


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--client", required=True, type=validate_client, help="Client/project slug under /documents.")
    parser.add_argument("--mode", required=True, choices=MODES, help="Report mode.")
    parser.add_argument("--date", help="Report date in YYYY-MM-DD; defaults to today.")


def command_render(args: argparse.Namespace) -> int:
    report_date = parse_report_date(args.date)
    out_dir = Path(args.output_dir or output_dir(args.client, report_date, args.mode))
    raw_dir = Path(args.raw_dir or out_dir / "raw")
    rows = [normalized_record(record) for record in load_raw_records(raw_dir)]
    summary = build_summary(args.client, args.mode, report_date, rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "report.md").write_text(render_report(summary), encoding="utf-8")
    files = ["summary.json", "report.md"]
    if args.mode == "dashboard":
        (out_dir / "dashboard.html").write_text(render_dashboard(summary), encoding="utf-8")
        files.append("dashboard.html")

    print(json.dumps({
        "ok": True,
        "readOnly": True,
        "outputDir": str(out_dir),
        "files": files,
        "signals": len(summary["signals"]),
        "dataQuality": summary["dataQuality"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Meta Ads reporting validate/dry-run helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate report arguments and print output contract.")
    add_common_args(validate_parser)

    dry_run_parser = subparsers.add_parser("dry-run", help="Print a read-only command plan without calling Meta.")
    add_common_args(dry_run_parser)

    render_parser = subparsers.add_parser("render", help="Render summary/report/dashboard from raw Meta JSON files.")
    add_common_args(render_parser)
    render_parser.add_argument("--raw-dir", help="Directory containing raw *.json files from the official meta CLI.")
    render_parser.add_argument("--output-dir", help="Output report directory; defaults to /documents/{client}/meta-ads/reports/{date}-{mode}.")

    args = parser.parse_args(argv)
    if args.command == "render":
        return command_render(args)
    payload = build_payload(args)
    if args.command == "validate":
        payload = {key: payload[key] for key in ("ok", "readOnly", "client", "mode", "date", "outputDir", "files")}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
