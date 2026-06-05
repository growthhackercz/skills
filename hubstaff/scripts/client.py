"""Hubstaff API klient — auth (PAT exchange + cache), GET wrapper, pagination, retry.

Tenký wrapper kolem Hubstaff API v2. Žádné externí závislosti (jen stdlib),
veškerá business logika (zprávy, anomálie, cron) patří do orchestrace nad skillem.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

TOKEN_URL = "https://account.hubstaff.com/access_tokens"
API_BASE = os.environ.get("HUBSTAFF_BASE_URL", "https://api.hubstaff.com")
CACHE_DIR = Path(os.environ.get("HUBSTAFF_CACHE_DIR", str(Path.home() / ".openclaw" / "cache" / "hubstaff")))
CACHE_FILE = CACHE_DIR / "token.json"

USER_AGENT = "cliqsales-hubstaff-skill/1.0"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 5


class HubstaffError(Exception):
    """Chyba při komunikaci s Hubstaff API."""


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
            from cc_credentials import hubstaff_pat  # type: ignore
        except Exception:
            continue
        return hubstaff_pat
    return None


def _pat() -> str:
    value = os.environ.get("HUBSTAFF_PAT", "").strip()
    if value:
        return value
    hubstaff_pat = _load_cc_credentials()
    if not hubstaff_pat:
        return ""
    return str(hubstaff_pat() or "").strip()


def _read_cache() -> dict[str, Any] | None:
    if not CACHE_FILE.exists():
        return None
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_cache(data: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.chmod(CACHE_FILE, 0o600)


def _exchange_refresh_token(refresh_token: str) -> dict[str, Any]:
    """Vymění refresh_token (PAT nebo rotovaný) za access_token."""
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HubstaffError(
            f"Výměna tokenu selhala (HTTP {exc.code}). Zkontroluj HUBSTAFF_PAT v prostředí. Odpověď: {detail[:300]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise HubstaffError(f"Nelze se připojit k Hubstaffu: {exc}") from exc

    now = int(time.time())
    return {
        "access_token": payload["access_token"],
        "refresh_token": payload.get("refresh_token", refresh_token),
        "expires_at": now + int(payload.get("expires_in", 3600)) - 60,
        "obtained_at": now,
    }


def get_access_token(force_refresh: bool = False) -> str:
    """Vrátí platný access token. Cachuje v ~/.openclaw/cache/hubstaff/token.json."""
    pat = _pat()
    if not pat:
        raise HubstaffError(
            "Chybí HUBSTAFF_PAT. Nastavte Hubstaff integraci v Control Center. Návod k vytvoření tokenu je v references/nastaveni-pat.md."
        )

    cache = _read_cache() if not force_refresh else None
    now = int(time.time())

    if cache and cache.get("source_pat_fingerprint") == _fingerprint(pat) and cache.get("expires_at", 0) > now:
        return cache["access_token"]

    refresh_token = (cache or {}).get("refresh_token") if (cache and cache.get("source_pat_fingerprint") == _fingerprint(pat)) else pat
    fresh = _exchange_refresh_token(refresh_token or pat)
    fresh["source_pat_fingerprint"] = _fingerprint(pat)
    _write_cache(fresh)
    return fresh["access_token"]


def _fingerprint(pat: str) -> str:
    """Otisk PAT (prvních 8 znaků + délka) — slouží jen k detekci, že se v cache nemíchá s jiným PAT."""
    return f"{pat[:8]}:{len(pat)}"


def _request(method: str, path: str, params: dict[str, Any] | None = None, retries: int = MAX_RETRIES) -> dict[str, Any]:
    token = get_access_token()
    url = f"{API_BASE}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"

    last_err: Exception | None = None
    backoff = 1.0

    for attempt in range(retries):
        req = urllib.request.Request(
            url,
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and attempt == 0:
                token = get_access_token(force_refresh=True)
                continue
            if exc.code in (429, 500, 502, 503, 504):
                retry_after = exc.headers.get("Retry-After")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else backoff
                time.sleep(min(wait, 60))
                backoff = min(backoff * 2, 30)
                last_err = exc
                continue
            detail = exc.read().decode("utf-8", errors="replace")
            raise HubstaffError(f"HTTP {exc.code} při {method} {path}: {detail[:300]}") from exc
        except urllib.error.URLError as exc:
            last_err = exc
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)

    raise HubstaffError(f"Hubstaff API nedostupné po {retries} pokusech: {last_err}")


def get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Jeden GET request, vrátí JSON tělo."""
    return _request("GET", path, params)


def get_paginated(path: str, params: dict[str, Any] | None = None, max_pages: int = 50) -> list[dict[str, Any]]:
    """GET s automatickým stránkováním.

    Hubstaff v2 vrací v každé odpovědi `pagination.next_page_start_id` (nebo nic).
    Klient sbírá hlavní resource list (první ne-pagination klíč obsahující list) a vrátí ho jako jeden konsolidovaný list.
    """
    collected: list[dict[str, Any]] = []
    params = dict(params or {})
    pages = 0

    while True:
        if pages >= max_pages:
            raise HubstaffError(
                f"Překročen limit {max_pages} stránek. Zužte časový rozsah nebo zvyšte --max-pages."
            )
        resp = _request("GET", path, params)
        list_key, items = _extract_list(resp)
        if list_key is None:
            return [resp]  # endpoint nevrací list — vrátíme syrový response zabalený do listu
        collected.extend(items)
        pages += 1

        next_id = (resp.get("pagination") or {}).get("next_page_start_id")
        if not next_id:
            break
        params["page_start_id"] = next_id

    return collected


def _extract_list(resp: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]]]:
    """Najde v response první klíč obsahující list (typicky 'organizations', 'members', 'activities', ...)."""
    for key, value in resp.items():
        if key == "pagination":
            continue
        if isinstance(value, list):
            return key, value
    return None, []


def get_default_org_id() -> int:
    """Vrátí ID první (typicky jediné) organizace, ke které má PAT přístup."""
    orgs = get_paginated("/v2/organizations")
    if not orgs:
        raise HubstaffError("Token nemá přístup k žádné organizaci v Hubstaffu.")
    return int(orgs[0]["id"])


def whoami() -> dict[str, Any]:
    """Vrátí identitu vlastníka tokenu (`/v2/users/me`)."""
    return get("/v2/users/me")


if __name__ == "__main__":
    # Diagnostický mód: python3 client.py --check
    if "--check" in sys.argv:
        try:
            me = whoami().get("user", {})
            org_id = get_default_org_id()
            print(f"Přihlášen jako {me.get('email', '?')} ({me.get('name', '?')}). Výchozí organizace ID: {org_id}.")
        except HubstaffError as exc:
            print(f"Chyba: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Použij: python3 client.py --check", file=sys.stderr)
        sys.exit(2)
