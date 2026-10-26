#!/usr/bin/env python3
"""Print the current Control Center email account id for a mailbox.

A Microsoft 365 reconnect creates a new account id, so cron jobs and scripts
must not hardcode `--account-id`. This helper reads the live account list and
prints the id of the enabled account with outgoing mail enabled.

Usage:
    python3 resolve_account_id.py [--email mailbox@example.com] [--provider microsoft_graph]

Selection:
  - only enabled accounts with outgoing mail enabled are considered;
  - `--email` narrows the choice to one mailbox (case-insensitive). Without it
    the instance must have exactly one such mailbox, otherwise the helper fails
    and asks for `--email` instead of guessing;
  - accounts of the requested `--provider` win when the mailbox has one;
  - among the remaining accounts the highest id (newest reconnect) wins.

Prints the id on stdout and exits 0. On failure it prints the reason to stderr
and exits 2, so callers never fall back to a stale or foreign account.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cc_email  # noqa: E402 - sibling helper next to this script

LIST_ATTEMPTS = 4
LIST_RETRY_DELAY_SECONDS = 5


def load_accounts() -> list[dict[str, Any]]:
    """Read the account list, retrying transient failures (timeouts, 5xx)."""
    last_error: Any = None
    for attempt in range(1, LIST_ATTEMPTS + 1):
        data = cc_email.request_json("GET", "/api/email/accounts")
        if data.get("ok", True):
            return [item for item in data.get("accounts", []) if isinstance(item, dict)]
        last_error = data.get("error") or data
        status = data.get("status")
        if isinstance(status, int) and 400 <= status < 500:
            break
        if attempt < LIST_ATTEMPTS:
            time.sleep(LIST_RETRY_DELAY_SECONDS)
    raise RuntimeError(f"cannot read email accounts: {last_error}")


def resolve(accounts: list[dict[str, Any]], email: str | None, provider: str | None) -> int:
    usable = [
        account for account in accounts
        if account.get("enabled") is True
        and (account.get("outgoing") or {}).get("enabled") is True
        and isinstance(account.get("id"), int)
    ]
    if email:
        wanted = email.strip().lower()
        usable = [account for account in usable if str(account.get("emailAddress") or "").strip().lower() == wanted]
        if not usable:
            raise RuntimeError(f"no enabled outgoing account found for mailbox {email}")
    else:
        mailboxes = sorted({str(account.get("emailAddress") or "").strip().lower() for account in usable})
        if not usable:
            raise RuntimeError("no enabled outgoing email account is configured")
        if len(mailboxes) > 1:
            raise RuntimeError(
                "more than one mailbox is configured (" + ", ".join(mailboxes) + "); pass --email"
            )

    preferred = [account for account in usable if provider and account.get("provider") == provider]
    pool = preferred or usable
    return max(account["id"] for account in pool)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the live Control Center email account id for a mailbox.")
    parser.add_argument("--email", help="Mailbox address. Required when more than one mailbox is configured.")
    parser.add_argument("--provider", default="microsoft_graph", help="Preferred provider when a mailbox has several accounts.")
    args = parser.parse_args()
    try:
        account_id = resolve(load_accounts(), args.email, args.provider)
    except Exception as error:  # noqa: BLE001 - CLI reports every failure the same way
        print(f"resolve_account_id: {error}", file=sys.stderr)
        return 2
    print(account_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
