#!/usr/bin/env python3
"""Parse raw FIO API JSON (column0..column26) into named fields.

Input: raw JSON from /periods/, /last/, or /by-id/ with .json suffix.
Output: list of transaction dicts with readable field names + meta object with
account info (opening/closing balance, IBAN, etc.).

Usage:
    python3 parse_transactions.py raw.json --output parsed.json
    python3 parse_transactions.py raw.json                     # stdout
    python3 parse_transactions.py raw.json --flat              # transactions only, no meta

Mapping reference: references/response-schema.md
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

COLUMN_MAP: dict[str, str] = {
    "column0": "id",
    "column1": "amount",
    "column2": "counter_account",
    "column3": "counter_account_name",
    "column4": "counter_bank_code",
    "column5": "ks",
    "column6": "counter_bank_name",
    "column7": "vs",
    "column8": "ss",
    "column9": "user_identification",
    "column10": "type",
    "column12": "executor",
    "column14": "currency",
    "column16": "message",
    "column17": "comment",
    "column18": "payment_order_id",
    "column22": "payment_order_id_full",
    "column25": "comment_alt",
    "column26": "bic",
}


def extract_value(column: Any) -> Any:
    """FIO column is {"value": X, "name": "...", "id": N} or None."""
    if not isinstance(column, dict):
        return None
    return column.get("value")


def parse_transaction(raw: dict) -> dict:
    parsed: dict[str, Any] = {}
    for col_key, field_name in COLUMN_MAP.items():
        parsed[field_name] = extract_value(raw.get(col_key))
    # Normalize types
    if parsed["amount"] is not None:
        try:
            parsed["amount"] = float(parsed["amount"])
        except (TypeError, ValueError):
            pass
    return parsed


def parse_info(info: dict) -> dict:
    """The info block uses direct field names (not columnXX), already readable."""
    return {
        "account_id": info.get("accountId"),
        "bank_id": info.get("bankId"),
        "iban": info.get("iban"),
        "bic": info.get("bic"),
        "currency": info.get("currency"),
        "opening_balance": info.get("openingBalance"),
        "closing_balance": info.get("closingBalance"),
        "date_start": info.get("dateStart"),
        "date_end": info.get("dateEnd"),
        "id_from": info.get("idFrom"),
        "id_to": info.get("idTo"),
        "id_last_download": info.get("idLastDownload"),
        "year_list": info.get("yearList"),
        "id_list": info.get("idList"),
    }


def parse_response(raw: dict) -> dict:
    stmt = raw.get("accountStatement") or {}
    info = parse_info(stmt.get("info") or {})
    tx_list = (stmt.get("transactionList") or {}).get("transaction") or []
    transactions = [parse_transaction(t) for t in tx_list]
    return {"info": info, "transactions": transactions}


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse FIO API JSON into readable fields.")
    parser.add_argument("input", help="Raw JSON soubor z fio_get.py (.json odpověď).")
    parser.add_argument("--output", "-o", help="Cesta k výstupu (jinak stdout).")
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Vrať jen list transakcí (bez info bloku). Default vrací {info, transactions}.",
    )
    args = parser.parse_args()

    try:
        with open(args.input, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: Nelze načíst {args.input}: {exc}", file=sys.stderr)
        return 2

    parsed = parse_response(raw)
    out = parsed["transactions"] if args.flat else parsed
    payload = json.dumps(out, ensure_ascii=False, indent=2)

    if args.output:
        import os
        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(payload)
        n = len(parsed["transactions"])
        print(f"OK: {n} transakcí → {args.output}")
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    sys.exit(main())
