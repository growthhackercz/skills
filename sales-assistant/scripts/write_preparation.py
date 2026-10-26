#!/usr/bin/env python3
"""Atomically persist one immutable Sales Assistant preparation + manifest."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from contextlib import contextmanager


SKILL_VERSION = "1.0"
MAX_BYTES = 200_000


@contextmanager
def _locked(output_root: Path, slug: str):
    output_root.mkdir(parents=True, exist_ok=True)
    handle = (output_root / f".{slug}.lock").open("a+")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _write_temp(directory: Path, name: str, content: str) -> str:
    fd, path = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp", dir=str(directory))
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    return path


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("existující _manifest.json je poškozený") from exc
    if not isinstance(value, dict):
        raise ValueError("existující _manifest.json není objekt")
    return value


def write_preparation(
    input_path: Path,
    output_root: Path,
    slug: str,
    task_id: int,
    *,
    _lock_held: bool = False,
) -> dict:
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,99}[a-z0-9])?", slug):
        raise ValueError("--slug musí být bezpečný lowercase slug")
    if task_id <= 0:
        raise ValueError("--task-id musí být kladné číslo")
    try:
        body = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"přípravu nelze načíst: {exc}") from exc
    encoded = body.encode("utf-8")
    if not body.strip() or len(encoded) > MAX_BYTES:
        raise ValueError("příprava musí být neprázdná a nejvýše 200000 B")
    digest = hashlib.sha256(encoded).hexdigest()
    if not _lock_held:
        with _locked(output_root, slug):
            return write_preparation(
                input_path,
                output_root,
                slug,
                task_id,
                _lock_held=True,
            )
    target_dir = output_root / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    preparation_path = target_dir / "priprava.md"
    manifest_path = target_dir / "_manifest.json"
    existing = _read_json(manifest_path)
    if existing is not None:
        same = (
            existing.get("skillVersion") == SKILL_VERSION
            and existing.get("taskId") == task_id
            and existing.get("sha256") == digest
            and set(existing) == {"taskId", "skillVersion", "sha256"}
            and preparation_path.exists()
            and hashlib.sha256(preparation_path.read_bytes()).hexdigest() == digest
        )
        if same:
            return {
                "ok": True,
                "reused": True,
                "slug": slug,
                "preparation": str(preparation_path),
                "manifest": str(manifest_path),
                **existing,
            }
        raise ValueError("slug už je svázaný s jinou přípravou nebo taskem; použij nový stabilní slug")
    if preparation_path.exists() and hashlib.sha256(preparation_path.read_bytes()).hexdigest() != digest:
        raise ValueError("priprava.md existuje bez manifestu a má jiný obsah; použij nový stabilní slug")

    manifest = {
        "taskId": task_id,
        "skillVersion": SKILL_VERSION,
        "sha256": digest,
    }
    prep_temp = _write_temp(target_dir, preparation_path.name, body)
    manifest_temp = _write_temp(
        target_dir,
        manifest_path.name,
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    try:
        os.replace(prep_temp, preparation_path)
        os.replace(manifest_temp, manifest_path)
        directory_fd = os.open(target_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        for temporary in (prep_temp, manifest_temp):
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
    return {
        "ok": True,
        "reused": False,
        "slug": slug,
        "preparation": str(preparation_path),
        "manifest": str(manifest_path),
        **manifest,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Atomicky uloží přípravu a její task-bound manifest")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--task-id", required=True, type=int)
    parser.add_argument("--output-root", type=Path, default=Path("/documents/sales/priprava"))
    args = parser.parse_args(argv)
    try:
        result = write_preparation(args.input, args.output_root, args.slug, args.task_id)
    except ValueError as exc:
        print(json.dumps({"ok": False, "code": "invalid_preparation", "error": str(exc)}, ensure_ascii=False))
        return 3
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
