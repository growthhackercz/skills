#!/usr/bin/env python3
"""Runtime environment helpers for Control Center distributed skills."""
from __future__ import annotations

import json
import os
from pathlib import Path


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


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        values[key] = value
    return values


def _read_secret_store(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {key: value for key, value in payload.items() if isinstance(value, str) and value}


def resolve_env_var(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value

    root = openclaw_home()
    value = _read_dotenv(root / ".env").get(name)
    if value:
        return value

    return _read_secret_store(root / "control-center-secrets.json").get(name, "")


def ensure_env_var(name: str) -> str:
    value = resolve_env_var(name)
    if value:
        os.environ[name] = value
    return value
