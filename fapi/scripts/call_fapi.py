#!/usr/bin/env python3
"""Thin read-only FAPI.cz REST API helper.

Credentials are resolved from environment variables first and then from Control
Center's credential store via ``cs-skills/_lib/cc_credentials.py``. The token is
sent in an Authorization header, never as a command-line argument or URL value.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://api.fapi.cz"
TIMEOUT_SECONDS = 30


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
            from cc_credentials import get_variable  # type: ignore
        except Exception:
            continue
        return get_variable
    return None


def credential(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    get_variable = _load_cc_credentials()
    if not get_variable:
        return ""
    return str(get_variable(name) or "").strip()


def build_url(path: str, query: str | None) -> str:
    if not path.startswith("/"):
        path = "/" + path
    url = f"{BASE_URL}{path}"
    if query:
        url = f"{url}?{query}"
    return url


def request(path: str, query: str | None, user: str, token: str) -> bytes:
    auth = base64.b64encode(f"{user}:{token}".encode("utf-8")).decode("ascii")
    req = urllib.request.Request(
        build_url(path, query),
        headers={
            "Accept": "application/json",
            "Authorization": f"Basic {auth}",
            "User-Agent": "cliqsales-fapi-skill/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        safe_path = path if path.startswith("/") else f"/{path}"
        print(f"FAPI returned HTTP {exc.code} for {safe_path}", file=sys.stderr)
        if body:
            print("--- response body ---", file=sys.stderr)
            print(body[:4000], file=sys.stderr)
            print("--- end ---", file=sys.stderr)
        raise SystemExit(2) from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"FAPI network error: {exc.reason}") from None


def main() -> int:
    parser = argparse.ArgumentParser(description="Call FAPI.cz REST API with Control Center credentials.")
    parser.add_argument("path", help="Endpoint path, e.g. /invoices")
    parser.add_argument("query", nargs="?", default="", help="Optional raw query string")
    parser.add_argument("--output", "-o", help="Write response body to this file instead of stdout")
    args = parser.parse_args()

    user = credential("FAPI_USER")
    token = credential("FAPI_TOKEN")
    if not user or not token:
        print(
            "ERROR: Missing FAPI_USER or FAPI_TOKEN. Configure FAPI in Control Center > Integrations.",
            file=sys.stderr,
        )
        return 65

    body = request(args.path, args.query or None, user, token)

    if args.path.endswith(".json") or body[:1] in (b"{", b"["):
        try:
            json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # FAPI occasionally returns non-JSON on some endpoints; keep output intact.
            pass

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(body)
        print(f"OK: wrote {len(body)} B to {out_path}")
    else:
        sys.stdout.buffer.write(body)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
