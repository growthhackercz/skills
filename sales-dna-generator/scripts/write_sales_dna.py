#!/usr/bin/env python3
"""Atomic, resumable writer for Sales DNA drafts and approved publication."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_VERSION = "1.0"
DEFAULT_OUTPUT = Path("/documents/sales/salesDNA.md")
DEFAULT_DRAFT = Path("/documents/sales/.sales-dna-draft.md")
DEFAULT_STATE = Path("/documents/sales/.sales-dna-draft-state.json")
DEFAULT_LOCK = Path("/documents/sales/.sales-dna.lock")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _versioned(text: str) -> str:
    """Return markdown with one exact artifact/version frontmatter contract."""
    body = text.strip() + "\n"
    if body.startswith("---\n"):
        end = body.find("\n---\n", 4)
        if end != -1:
            fields = [
                line for line in body[4:end].splitlines()
                if not line.startswith("artifactType:") and not line.startswith("skillVersion:")
            ]
            frontmatter = ["artifactType: sales-dna", f'skillVersion: "{SKILL_VERSION}"', *fields]
            return "---\n" + "\n".join(frontmatter) + body[end:]
    return (
        "---\n"
        "artifactType: sales-dna\n"
        f'skillVersion: "{SKILL_VERSION}"\n'
        "---\n\n"
        + body
    )


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    _atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"stav draftu {path} je poškozený; nebude přepsán") from exc
    if not isinstance(value, dict):
        raise ValueError(f"stav draftu {path} musí být JSON objekt")
    return value


@contextmanager
def _locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_input(path: str) -> str:
    try:
        return _versioned(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"vstup {path} nelze načíst: {exc}") from exc


def _draft(args: argparse.Namespace) -> dict[str, Any]:
    draft_path = Path(args.draft_path)
    state_path = Path(args.state_path)
    value = _read_input(args.input)
    with _locked(Path(args.lock_path)):
        previous = _read_state(state_path)
        # První draft po publikaci začíná novou revizi; pouze rozpracovaný
        # draft přebírá dokončené bloky pro skutečné resume.
        previous_blocks = previous.get("completedBlocks", []) if previous.get("status") == "draft" else []
        blocks = {
            int(item) for item in previous_blocks
            if isinstance(item, int) or (isinstance(item, str) and item.isdigit())
        }
        blocks.add(args.completed_block)
        _atomic_text(draft_path, value)
        state = {
            "schemaVersion": 1,
            "skillVersion": SKILL_VERSION,
            "status": "draft",
            "completedBlocks": sorted(blocks),
            "draftPath": str(draft_path),
            "draftSha256": _sha(value),
            "updatedAt": _now(),
        }
        _atomic_json(state_path, state)
    return state


def _publish(args: argparse.Namespace) -> dict[str, Any]:
    output = Path(args.output)
    state_path = Path(args.state_path)
    value = _read_input(args.input)
    with _locked(Path(args.lock_path)):
        previous_state = _read_state(state_path)
        expected = previous_state.get("draftSha256")
        if expected and expected != _sha(value):
            raise ValueError(
                "publikovaný vstup neodpovídá poslednímu uloženému draftu; "
                "nejdřív znovu uložte aktuální blok přes příkaz draft"
            )
        backup = None
        if output.exists():
            old = output.read_text(encoding="utf-8")
            if old != value:
                stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S-%f")
                backup_path = output.with_name(f"salesDNA-backup-{stamp}.md")
                _atomic_text(backup_path, old)
                backup = str(backup_path)
        _atomic_text(output, value)
        state = {
            **previous_state,
            "schemaVersion": 1,
            "skillVersion": SKILL_VERSION,
            "status": "published",
            "outputPath": str(output),
            "publishedSha256": _sha(value),
            "backupPath": backup,
            "updatedAt": _now(),
        }
        _atomic_json(state_path, state)
    return state


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Atomically save/resume or publish Sales DNA")
    commands = parser.add_subparsers(dest="command", required=True)

    draft = commands.add_parser("draft")
    draft.add_argument("--input", required=True)
    draft.add_argument("--completed-block", type=int, choices=range(1, 7), required=True)
    draft.add_argument("--draft-path", default=str(DEFAULT_DRAFT))
    draft.add_argument("--state-path", default=str(DEFAULT_STATE))
    draft.add_argument("--lock-path", default=str(DEFAULT_LOCK))

    publish = commands.add_parser("publish")
    publish.add_argument("--input", required=True)
    publish.add_argument("--approved", choices=["yes"], required=True)
    publish.add_argument("--output", default=str(DEFAULT_OUTPUT))
    publish.add_argument("--state-path", default=str(DEFAULT_STATE))
    publish.add_argument("--lock-path", default=str(DEFAULT_LOCK))

    status = commands.add_parser("status")
    status.add_argument("--state-path", default=str(DEFAULT_STATE))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "draft":
            result = _draft(args)
        elif args.command == "publish":
            result = _publish(args)
        else:
            result = _read_state(Path(args.state_path)) or {
                "schemaVersion": 1,
                "skillVersion": SKILL_VERSION,
                "status": "not_started",
                "completedBlocks": [],
            }
        print(json.dumps({"ok": True, **result}, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "code": "sales_dna_state_error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
