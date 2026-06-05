"""Control Center credential resolver for distributed skills.

This module reads public credential metadata from
``~/.openclaw/control-center-credentials.json`` and sensitive values from
``~/.openclaw/control-center-secrets.json``. It never prints secret values.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class CredentialError(RuntimeError):
    pass


def openclaw_home() -> Path:
    configured = os.environ.get("OPENCLAW_HOME") or os.environ.get("CC_OPENCLAW_HOME")
    if configured:
        path = Path(configured).expanduser()
        if path.name in {".openclaw", ".clawdbot"}:
            return path
        nested = path / ".openclaw"
        if nested.exists():
            return nested
        return path
    return Path.home() / ".openclaw"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CredentialError(f"Invalid credential file: {path}") from exc
    if not isinstance(data, dict):
        return {}
    return data


def credential_store(home: Path | None = None) -> dict[str, Any]:
    root = home or openclaw_home()
    return _read_json(root / "control-center-credentials.json")


def secret_store(home: Path | None = None) -> dict[str, str]:
    root = home or openclaw_home()
    raw = _read_json(root / "control-center-secrets.json")
    return {key: value for key, value in raw.items() if isinstance(value, str) and value}


def runtime_env(home: Path | None = None) -> dict[str, str]:
    root = home or openclaw_home()
    path = root / ".env"
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        values[key] = value
    return values


def secret_key_from_ref(secret_ref: str) -> str:
    return secret_ref.strip().lstrip("/")


def resolve_secret_ref(secret_ref: str, home: Path | None = None) -> str:
    key = secret_key_from_ref(secret_ref)
    if not key:
        return ""
    return secret_store(home).get(key, "")


def get_variable(name: str, home: Path | None = None) -> str:
    normalized = name.strip().upper()
    store = credential_store(home)
    variables = store.get("variables")
    if not isinstance(variables, dict):
        return ""
    entry = variables.get(normalized)
    if not isinstance(entry, dict):
        return ""
    if entry.get("visibility") == "secret":
        secret_ref = entry.get("secretRef")
        return resolve_secret_ref(secret_ref, home) if isinstance(secret_ref, str) else ""
    value = entry.get("value")
    return value if isinstance(value, str) else ""


def get_env_or_variable(name: str, home: Path | None = None) -> str:
    """Resolve a value from process env, runtime .env, custom variables, or secret store."""
    normalized = name.strip().upper()
    value = os.environ.get(normalized, "").strip()
    if value:
        return value
    value = runtime_env(home).get(normalized, "").strip()
    if value:
        return value
    value = get_variable(normalized, home)
    if value:
        return value
    return secret_store(home).get(normalized, "").strip()


def wordpress_profile(profile: str | None = None, home: Path | None = None) -> dict[str, str]:
    store = credential_store(home)
    wordpress = store.get("wordpress")
    if not isinstance(wordpress, dict):
        return {}
    profiles = wordpress.get("profiles")
    if not isinstance(profiles, dict):
        return {}

    slug = (profile or wordpress.get("defaultProfile") or "").strip().lower()
    if not slug and profiles:
        slug = next(iter(profiles.keys()))
    entry = profiles.get(slug)
    if not isinstance(entry, dict):
        return {}

    site_url = str(entry.get("siteUrl") or "").rstrip("/")
    username = str(entry.get("username") or "").strip()
    secret_ref = entry.get("applicationPasswordRef")
    application_password = resolve_secret_ref(secret_ref, home) if isinstance(secret_ref, str) else ""
    if not site_url or not username or not application_password:
        return {}
    return {
        "profile": slug,
        "site_url": site_url,
        "username": username,
        "application_password": application_password,
    }


def fio_profile(profile: str | None = None, home: Path | None = None) -> dict[str, str]:
    """Resolve a FIO Bank profile from Control Center credential store.

    Returns an empty dict when no matching complete profile exists. Legacy
    ``FIO_API_TOKEN`` remains supported by callers as an explicit fallback, but
    profile storage is preferred because clients may have multiple accounts.
    """
    store = credential_store(home)
    fio_bank = store.get("fioBank")
    if not isinstance(fio_bank, dict):
        return {}
    profiles = fio_bank.get("profiles")
    if not isinstance(profiles, dict):
        return {}

    slug = (profile or fio_bank.get("defaultProfile") or "").strip().lower()
    if not slug and profiles:
        slug = next(iter(profiles.keys()))
    entry = profiles.get(slug)
    if not isinstance(entry, dict):
        return {}

    secret_ref = entry.get("tokenRef")
    token = resolve_secret_ref(secret_ref, home) if isinstance(secret_ref, str) else ""
    if not token:
        return {}
    return {
        "profile": slug,
        "token": token.strip(),
        "label": str(entry.get("label") or entry.get("name") or slug),
        "currency": str(entry.get("currency") or "").upper(),
        "account_number": str(entry.get("accountNumber") or ""),
    }


def fapi_credentials(home: Path | None = None) -> dict[str, str]:
    user = get_env_or_variable("FAPI_USER", home)
    token = get_env_or_variable("FAPI_TOKEN", home)
    if not user or not token:
        return {}
    return {"user": user, "token": token}


def hubstaff_pat(home: Path | None = None) -> str:
    return get_env_or_variable("HUBSTAFF_PAT", home)


def asana_pat(home: Path | None = None) -> str:
    return get_env_or_variable("ASANA_PAT", home)


def trello_credentials(home: Path | None = None) -> dict[str, str]:
    api_key = get_env_or_variable("TRELLO_API_KEY", home)
    token = get_env_or_variable("TRELLO_TOKEN", home)
    if not api_key or not token:
        return {}
    return {"api_key": api_key, "token": token}


def fireflies_api_key(home: Path | None = None) -> str:
    return get_env_or_variable("FIREFLIES_API_KEY", home)


def ghl_credentials(home: Path | None = None) -> dict[str, str]:
    api_key = get_env_or_variable("GHL_API_KEY", home)
    location_id = get_env_or_variable("GHL_LOCATION_ID", home)
    user = get_env_or_variable("GHL_USER", home)
    if not api_key or not location_id:
        return {}
    return {"api_key": api_key, "location_id": location_id, "user": user}


def smartemailing_credentials(home: Path | None = None) -> dict[str, str]:
    username = get_env_or_variable("SMARTEMAILING_USERNAME", home)
    api_key = get_env_or_variable("SMARTEMAILING_API_KEY", home)
    if not username or not api_key:
        return {}
    return {"username": username, "api_key": api_key}


def netlify_credentials(home: Path | None = None) -> dict[str, str]:
    auth_token = get_env_or_variable("NETLIFY_AUTH_TOKEN", home)
    site_id = get_env_or_variable("NETLIFY_SITE_ID", home)
    account_slug = get_env_or_variable("NETLIFY_ACCOUNT_SLUG", home)
    if not auth_token:
        return {}
    return {"auth_token": auth_token, "site_id": site_id, "account_slug": account_slug}
