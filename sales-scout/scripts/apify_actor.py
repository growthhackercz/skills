#!/usr/bin/env python3
"""Fail-closed compatibility CLI for metered Apify runs.

Control Center does not yet expose a typed metered Apify external-action type.
The skill therefore cannot spend credits, load a token, or call an actor. The
historical arguments remain so existing workflows get a truthful, actionable
error instead of silently falling back to a direct paid POST.
"""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apify paid runs are disabled until Control Center provides a typed metered action"
    )
    parser.add_argument("--actor", required=True)
    parser.add_argument("--input-json")
    parser.add_argument("--input-file")
    parser.add_argument("--max-items", type=int)
    parser.add_argument("--max-cost", type=float, default=0.15)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    error = {
        "ok": False,
        "code": "metered_action_type_unavailable",
        "error": (
            "Placený Apify běh nebyl spuštěn. Control Center zatím nemá exact typed metered "
            "action pro Apify; přímý token ani placený provider call nejsou povolené."
        ),
        "actor": args.actor,
        "requestedMaxCostUsd": args.max_cost,
    }
    print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
