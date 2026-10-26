#!/usr/bin/env python3
"""Workspace-safe market policy and candidate normalization for Sales Scout."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ALLOWED_COMMANDS = {"market-plan", "normalize"}


def _load_shared():
    script_path = Path(__file__).resolve()
    candidates = [script_path.parents[2] / "_lib"]
    for env_name in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw = (os.environ.get(env_name) or "").strip()
        if raw:
            home = Path(raw).expanduser()
            candidates.extend((home / "cs-skills" / "_lib", home / ".openclaw" / "cs-skills" / "_lib"))
    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
    candidates.extend(parent / "cs-skills" / "_lib" for parent in script_path.parents)
    seen: set[str] = set()
    for lib_dir in candidates:
        key = str(lib_dir)
        if key in seen or not (lib_dir / "sales_prospect_package.py").is_file():
            continue
        seen.add(key)
        if key not in sys.path:
            sys.path.insert(0, key)
        try:
            import sales_prospect_package  # type: ignore
        except Exception:
            continue
        return sales_prospect_package
    raise RuntimeError("sales_prospect_package.py nebyl nalezen v cs-skills/_lib")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ALLOWED_COMMANDS:
        print("usage: market_context.py {market-plan,normalize} ...", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(_load_shared().main())
