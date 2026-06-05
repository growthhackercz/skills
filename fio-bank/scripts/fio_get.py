#!/usr/bin/env python3
"""Thin HTTP wrapper for FIO Bank read-only API.

- Reads token from a Control Center FIO profile or legacy FIO_API_TOKEN env.
- Retries HTTP 409 (rate limit) with exponential backoff: 30s, 60s, 120s.
- Never prints the token (masks it in error messages and debug output).
- For .json paths, validates JSON; for other formats, writes raw bytes.

Usage:
    python3 fio_get.py "/periods/{token}/2026-05-01/2026-05-19/transactions.json" --output raw.json
    python3 fio_get.py "/periods/2026-05-01/2026-05-19/transactions.json" --output raw.json
    python3 fio_get.py --profile hlavni-czk "/periods/{token}/2026-05-01/2026-05-19/transactions.json" --output raw.json

The {token} placeholder is replaced with the resolved token. If no placeholder
is present, the token is inserted immediately after "/rest/" in the URL path.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://fioapi.fio.cz/v1/rest"
RETRY_DELAYS = (30, 60, 120)
TIMEOUT_SECONDS = 30
TOKEN_PLACEHOLDER = "{token}"
TOKEN_MASK = "{TOKEN}"


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
            from cc_credentials import fio_profile  # type: ignore
        except Exception:
            continue
        return fio_profile
    return None


def resolve_token(profile: str | None) -> tuple[str, str]:
    fio_profile = _load_cc_credentials()
    if fio_profile:
        resolved = fio_profile(profile)
        token = str(resolved.get("token") or "").strip()
        if token:
            label = str(resolved.get("profile") or profile or "default")
            return token, label

    token = os.environ.get("FIO_API_TOKEN", "").strip()
    if token:
        return token, "legacy-env"

    return "", profile or ""


def build_url(path: str, token: str) -> str:
    """Insert token into the path. Accept either {token} placeholder or insert
    after the leading slash."""
    if TOKEN_PLACEHOLDER in path:
        return BASE_URL + path.replace(TOKEN_PLACEHOLDER, token)
    if not path.startswith("/"):
        path = "/" + path
    # Insert token as the first segment after /rest/.
    segments = path.lstrip("/").split("/", 1)
    head = segments[0]
    rest = segments[1] if len(segments) > 1 else ""
    return f"{BASE_URL}/{head}/{token}/{rest}".rstrip("/")


def mask_token_in_url(url: str, token: str) -> str:
    return url.replace(token, TOKEN_MASK)


def fetch(url: str, token: str, debug: bool = False) -> bytes:
    last_err: Exception | None = None
    delays = (0,) + RETRY_DELAYS
    for attempt, delay in enumerate(delays, start=1):
        if delay:
            if debug:
                print(f"[debug] retry {attempt}/{len(delays)} po {delay}s (HTTP 409 rate limit)", file=sys.stderr)
            time.sleep(delay)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "cliqsales-fio-bank/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            safe_url = mask_token_in_url(url, token)
            if exc.code == 409 and attempt <= len(RETRY_DELAYS):
                last_err = exc
                if debug:
                    print(f"[debug] HTTP 409 z {safe_url}, retry pending", file=sys.stderr)
                continue
            # Build user-safe error.
            raise RuntimeError(f"FIO API HTTP {exc.code} pro {safe_url}: {exc.reason}") from None
        except urllib.error.URLError as exc:
            raise RuntimeError(f"FIO API network error pro {mask_token_in_url(url, token)}: {exc.reason}") from None
    raise RuntimeError(
        f"FIO API rate limit retry vyčerpán pro {mask_token_in_url(url, token)}: {last_err}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="FIO API read-only fetch helper.")
    parser.add_argument("path", help="Endpoint path, např. /periods/{token}/2026-05-01/2026-05-19/transactions.json")
    parser.add_argument("--profile", help="Control Center FIO profile slug. Defaults to configured default profile.")
    parser.add_argument("--output", "-o", help="Cesta k výstupnímu souboru (jinak stdout).")
    parser.add_argument("--debug", action="store_true", help="Verbose debug (token v URL je vždy maskovaný).")
    args = parser.parse_args()

    token, token_source = resolve_token(args.profile)
    if not token:
        print(
            "ERROR: FIO token is not configured. Add a FIO Bank profile in Control Center > Integrations.",
            file=sys.stderr,
        )
        return 2

    url = build_url(args.path, token)
    if args.debug:
        print(f"[debug] profile={token_source} GET {mask_token_in_url(url, token)}", file=sys.stderr)

    body = fetch(url, token, debug=args.debug)

    # JSON validace pokud .json
    if args.path.endswith(".json"):
        try:
            json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            print(f"ERROR: Odpověď není validní JSON: {exc}", file=sys.stderr)
            return 3

    if args.output:
        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "wb") as f:
            f.write(body)
        size_kb = len(body) / 1024
        print(f"OK: zapsáno {len(body)} B ({size_kb:.1f} kB) → {args.output}")
    else:
        sys.stdout.buffer.write(body)

    return 0


if __name__ == "__main__":
    sys.exit(main())
