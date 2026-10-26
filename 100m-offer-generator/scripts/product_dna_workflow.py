#!/usr/bin/env python3
"""Resumable, task-bound and atomic workflow for one versioned Product DNA.

The active Product DNA keeps the existing nine-section contract. Drafts and
step approvals stay in hidden WIP files until the exact final bytes are approved
and contain no explicit unverified-claim marker.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_VERSION = "1.1"
STATE_VERSION = 1
DEFAULT_PRODUCTS_DIR = Path("/documents/brand/products")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SCHEMA_VERSION_RE = re.compile(r"^\s*schemaVersion\s*:", flags=re.I | re.M)
UNVERIFIED_MARKER = "[OVĚŘ S KLIENTEM]"
WIP_MARKERS = (UNVERIFIED_MARKER, "[ROZPRACOVÁNO]")
EXPECTED_H2 = [
    "1. ESENCE PRODUKTU",
    "2. PRO KOHO TO JE (A PRO KOHO NE)",
    "3. HLAVNÍ BENEFITY",
    "4. CO PŘESNĚ KLIENT DOSTANE",
    "5. CENOVÁ STRUKTURA",
    "6. NEJČASTĚJŠÍ NÁMITKY",
    "7. SOCIÁLNÍ DŮKAZ A VÝSLEDKY",
    "8. PRODEJNÍ SPOUŠTĚČE",
    "9. SHRNUTÍ PRODUCT DNA",
    "CHYBĚJÍCÍ INFORMACE",
]


class WorkflowError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _sha_file(path: Path) -> str | None:
    try:
        return _sha_bytes(path.read_bytes())
    except FileNotFoundError:
        return None


def _fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_text(path: Path, value: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_dir(path.parent)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _atomic_json(path: Path, value: dict[str, Any], mode: int = 0o600) -> None:
    _atomic_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        mode,
    )


def _read_json(path: Path, *, missing_ok: bool = False) -> dict[str, Any]:
    if not path.exists() and missing_ok:
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError("state_missing", f"Chybí stav workflow: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(
            "state_corrupt",
            f"Stav workflow {path} je nečitelný; nebude automaticky přepsán.",
        ) from exc
    if not isinstance(parsed, dict):
        raise WorkflowError("state_corrupt", f"Stav workflow {path} není JSON objekt.")
    return parsed


def _read_state(path: Path, *, missing_ok: bool = False) -> dict[str, Any]:
    state = _read_json(path, missing_ok=missing_ok)
    if not state:
        return state
    valid_operation = False
    try:
        valid_operation = str(uuid.UUID(str(state.get("operationId")))) == state.get("operationId")
    except (ValueError, TypeError, AttributeError):
        pass
    completed = state.get("completedSteps")
    task_id = state.get("taskId")
    if (
        state.get("stateVersion") != STATE_VERSION
        or state.get("skillVersion") != SKILL_VERSION
        or state.get("status") not in {"draft", "publishing", "published", "abandoned"}
        or state.get("mode") not in {"guided", "fast"}
        or not valid_operation
        or not isinstance(state.get("revision"), int)
        or int(state["revision"]) <= 0
        or not isinstance(completed, list)
        or any(not isinstance(step, int) or step < 1 or step > 5 for step in completed)
        or not isinstance(state.get("approvals"), dict)
        or (task_id is not None and (not isinstance(task_id, int) or task_id <= 0))
    ):
        raise WorkflowError(
            "state_corrupt",
            f"Stav workflow {path} neodpovídá podporovanému tvaru; nebude automaticky přepsán.",
        )
    _validate_slug(str(state.get("productSlug") or ""))
    return state


def _validate_slug(value: str) -> str:
    slug = str(value or "").strip()
    if not SLUG_RE.fullmatch(slug):
        raise WorkflowError(
            "invalid_product_slug",
            "Product slug musí být neprázdný lowercase kebab-case bez cesty.",
        )
    return slug


def _paths(products_dir: str, product_slug: str) -> dict[str, Path]:
    root = Path(products_dir).expanduser().resolve()
    slug = _validate_slug(product_slug)
    product = (root / slug).resolve()
    if product.parent != root:
        raise WorkflowError("invalid_product_slug", "Product slug opouští products root.")
    paths = {
        "root": root,
        "product": product,
        "active": product / "productDNA.md",
        "state": product / ".100m-offer-state.json",
        "wip": product / ".100m-offer-wip.md",
        "manifest": product / ".100m-offer-manifest.json",
        "lock": product / ".product-dna.lock",
        "approvals": product / ".100m-offer-approvals",
        "backups": product / "_backups",
    }
    for key, path in paths.items():
        if key in {"root", "product"}:
            continue
        resolved = path.resolve(strict=False)
        if resolved != product and product not in resolved.parents:
            raise WorkflowError(
                "unsafe_product_path",
                f"Spravovaná cesta {path} opouští adresář produktu.",
            )
    return paths


@contextmanager
def _locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _assert_operation(state: dict[str, Any], operation_id: str) -> None:
    if state.get("operationId") != operation_id:
        raise WorkflowError(
            "operation_mismatch",
            "Požadovaná operace neodpovídá aktuálnímu rozpracovanému workflow.",
        )


def _inject_artifact_frontmatter(text: str, revision: int) -> str:
    body = str(text or "").strip() + "\n"
    if SCHEMA_VERSION_RE.search(body):
        raise WorkflowError(
            "unapproved_schema_version",
            "Product DNA nesmí zavést schemaVersion bez samostatně schváleného kontraktu.",
        )
    preserved: list[str] = []
    content = body
    if body.startswith("---\n"):
        end = body.find("\n---\n", 4)
        if end == -1:
            raise WorkflowError("invalid_frontmatter", "Product DNA má neukončený frontmatter.")
        for line in body[4:end].splitlines():
            key = line.split(":", 1)[0].strip()
            if key not in {"artifactType", "skillVersion", "revision"}:
                preserved.append(line)
        content = body[end + len("\n---\n"):].lstrip("\n")
    header = [
        "artifactType: product-dna",
        f'skillVersion: "{SKILL_VERSION}"',
        f"revision: {revision}",
        *preserved,
    ]
    return "---\n" + "\n".join(header) + "\n---\n\n" + content


def _validate_document(text: str, *, final: bool) -> None:
    if SCHEMA_VERSION_RE.search(text):
        raise WorkflowError(
            "unapproved_schema_version",
            "Product DNA nesmí obsahovat neodsouhlasený schemaVersion.",
        )
    h1 = re.findall(r"^#\s+(.+?)\s*$", text, flags=re.M)
    if len(h1) != 1 or not h1[0].startswith("PRODUCT DNA:"):
        raise WorkflowError(
            "invalid_product_dna_structure",
            "Product DNA musí mít právě jeden H1 ve tvaru '# PRODUCT DNA: …'.",
        )
    headings = [match.strip() for match in re.findall(r"^##\s+(.+?)\s*$", text, flags=re.M)]
    if headings != EXPECTED_H2:
        raise WorkflowError(
            "invalid_product_dna_structure",
            "Product DNA musí zachovat přesných devět kanonických sekcí a závěrečnou sekci chybějících informací.",
        )
    if len(text.encode("utf-8")) < 500:
        raise WorkflowError("invalid_product_dna_structure", "Product DNA je neočekávaně krátká.")
    if final:
        found = [marker for marker in WIP_MARKERS if marker.casefold() in text.casefold()]
        if found:
            raise WorkflowError(
                "unverified_claims_remain",
                "Aktivní Product DNA nesmí obsahovat WIP ani neověřené tvrzení; ponechte je pouze v rozpracované verzi.",
            )


def _read_input(path: str, revision: int, *, final: bool = False) -> str:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkflowError("input_unreadable", f"Vstup {path} nelze načíst: {exc}") from exc
    value = _inject_artifact_frontmatter(raw, revision)
    _validate_document(value, final=final)
    return value


def _base_idempotency_key(slug: str, operation_id: str) -> str:
    return f"cso:100m-offer:{slug}:{operation_id}"


def _manifest_revision(path: Path) -> int:
    manifest = _read_json(path, missing_ok=True)
    value = manifest.get("revision")
    return int(value) if isinstance(value, int) and value > 0 else 0


def _recover_publishing(paths: dict[str, Path], state: dict[str, Any]) -> dict[str, Any]:
    if state.get("status") != "publishing":
        return state
    intent = state.get("publishIntent")
    if not isinstance(intent, dict):
        raise WorkflowError("publish_state_corrupt", "Publish journal nemá platný záměr.")
    expected = intent.get("sha256")
    manifest = intent.get("manifest")
    if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
        raise WorkflowError("publish_state_corrupt", "Publish journal nemá platný SHA-256.")
    if not isinstance(manifest, dict):
        raise WorkflowError("publish_state_corrupt", "Publish journal nemá platný manifest.")
    if _sha_file(paths["active"]) != expected:
        return state
    _atomic_json(paths["manifest"], manifest, 0o644)
    completed = {
        **state,
        "status": "published",
        "publishedSha256": expected,
        "publishedAt": manifest.get("publishedAt"),
        "manifestPath": str(paths["manifest"]),
        "outputPath": str(paths["active"]),
        "updatedAt": _now(),
    }
    completed.pop("publishIntent", None)
    _atomic_json(paths["state"], completed)
    return completed


def _start(args: argparse.Namespace) -> dict[str, Any]:
    paths = _paths(args.products_dir, args.product_slug)
    with _locked(paths["lock"]):
        state = _read_state(paths["state"], missing_ok=True)
        if state:
            state = _recover_publishing(paths, state)
            if state.get("status") in {"draft", "publishing"}:
                if state.get("mode") != args.mode:
                    raise WorkflowError(
                        "workflow_mode_conflict",
                        "Produkt už má rozpracovanou operaci v jiném režimu.",
                    )
                return {"reused": True, **state}
            if state.get("status") == "published" and args.new_revision != "yes":
                return {"reused": True, **state}
            if state.get("status") == "abandoned" and args.new_revision != "yes":
                return {"reused": True, **state}
        last_published_revision = _manifest_revision(paths["manifest"])
        if state and state.get("status") == "published":
            last_published_revision = max(last_published_revision, int(state.get("revision") or 0))
        revision = last_published_revision + 1
        operation_id = str(uuid.uuid4())
        now = _now()
        created = {
            "stateVersion": STATE_VERSION,
            "skillVersion": SKILL_VERSION,
            "status": "draft",
            "mode": args.mode,
            "productSlug": _validate_slug(args.product_slug),
            "operationId": operation_id,
            "idempotencyKey": _base_idempotency_key(args.product_slug, operation_id),
            "revision": revision,
            "taskId": None,
            "baseSha256": _sha_file(paths["active"]),
            "completedSteps": [],
            "approvals": {},
            "startedAt": now,
            "updatedAt": now,
            "wipPath": str(paths["wip"]),
            "outputPath": str(paths["active"]),
        }
        _atomic_json(paths["state"], created)
        return {"reused": False, **created}


def _bind_task(args: argparse.Namespace) -> dict[str, Any]:
    paths = _paths(args.products_dir, args.product_slug)
    if not isinstance(args.task_id, int) or args.task_id <= 0:
        raise WorkflowError("invalid_task_id", "Task ID musí být kladné celé číslo.")
    with _locked(paths["lock"]):
        state = _recover_publishing(paths, _read_state(paths["state"]))
        _assert_operation(state, args.operation_id)
        current = state.get("taskId")
        if current not in {None, args.task_id}:
            raise WorkflowError("task_binding_conflict", "Workflow je už svázané s jiným taskem.")
        state = {**state, "taskId": args.task_id, "updatedAt": _now()}
        _atomic_json(paths["state"], state)
        return state


def _draft(args: argparse.Namespace) -> dict[str, Any]:
    paths = _paths(args.products_dir, args.product_slug)
    with _locked(paths["lock"]):
        state = _recover_publishing(paths, _read_state(paths["state"]))
        _assert_operation(state, args.operation_id)
        if state.get("status") != "draft":
            raise WorkflowError("workflow_not_draft", "Workflow už není ve stavu rozpracování.")
        mode = state.get("mode")
        completed = {
            int(step) for step in state.get("completedSteps", [])
            if isinstance(step, int) and 1 <= step <= 5
        }
        if mode == "guided" and args.completed_step > (max(completed, default=0) + 1):
            raise WorkflowError("step_order_invalid", "V řízeném režimu nelze přeskočit schvalovací krok.")
        if mode == "fast" and args.completed_step != 5:
            raise WorkflowError("step_order_invalid", "Rychlý draft ukládá pouze kompletní krok 5.")
        value = _read_input(args.input, int(state["revision"]), final=False)
        approvals = {
            key: approval for key, approval in (state.get("approvals") or {}).items()
            if str(key).isdigit() and int(key) < args.completed_step
        }
        completed = {step for step in completed if step <= args.completed_step}
        completed.add(args.completed_step)
        _atomic_text(paths["wip"], value)
        state = {
            **state,
            "completedSteps": sorted(completed),
            "approvals": approvals,
            "wipSha256": _sha_text(value),
            "updatedAt": _now(),
        }
        _atomic_json(paths["state"], state)
        return state


def _abandon(args: argparse.Namespace) -> dict[str, Any]:
    paths = _paths(args.products_dir, args.product_slug)
    with _locked(paths["lock"]):
        state = _recover_publishing(paths, _read_state(paths["state"]))
        _assert_operation(state, args.operation_id)
        if state.get("status") == "published":
            raise WorkflowError("workflow_already_published", "Publikovanou revizi nelze označit jako opuštěnou.")
        if state.get("status") == "abandoned":
            return {"reused": True, **state}
        state = {
            **state,
            "status": "abandoned",
            "abandonedAt": _now(),
            "updatedAt": _now(),
        }
        state.pop("publishIntent", None)
        _atomic_json(paths["state"], state)
        return {"reused": False, **state}


def _approve(args: argparse.Namespace) -> dict[str, Any]:
    paths = _paths(args.products_dir, args.product_slug)
    expected = str(args.expected_sha256 or "").lower()
    if not SHA256_RE.fullmatch(expected):
        raise WorkflowError("invalid_sha256", "Schválení vyžaduje přesný SHA-256 rozpracované verze.")
    with _locked(paths["lock"]):
        state = _recover_publishing(paths, _read_state(paths["state"]))
        _assert_operation(state, args.operation_id)
        if state.get("status") != "draft":
            raise WorkflowError("workflow_not_draft", "Workflow už není ve stavu rozpracování.")
        actual = _sha_file(paths["wip"])
        if actual != expected or state.get("wipSha256") != expected:
            raise WorkflowError("stale_approval", "Schvalovaný obsah neodpovídá aktuální rozpracované verzi.")
        completed = set(state.get("completedSteps") or [])
        if args.step not in completed:
            raise WorkflowError("step_not_completed", "Nelze schválit dosud neuložený krok.")
        if state.get("mode") == "guided":
            missing = [step for step in range(1, args.step) if str(step) not in (state.get("approvals") or {})]
            if missing:
                raise WorkflowError("prior_step_not_approved", "Předchozí schvalovací krok ještě není potvrzený.")
        elif args.step != 5:
            raise WorkflowError("step_order_invalid", "Rychlý draft má pouze finální schválení kroku 5.")
        snapshot = paths["approvals"] / args.operation_id / f"step-{args.step}.md"
        _atomic_text(snapshot, paths["wip"].read_text(encoding="utf-8"))
        approvals = dict(state.get("approvals") or {})
        approvals[str(args.step)] = {
            "sha256": expected,
            "approvedAt": _now(),
            "snapshotPath": str(snapshot),
        }
        state = {**state, "approvals": approvals, "updatedAt": _now()}
        _atomic_json(paths["state"], state)
        return state


def _backup_path(paths: dict[str, Path], revision: int) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S-%f")
    return paths["backups"] / f"productDNA.before-r{revision}.{stamp}.md"


def _publish(args: argparse.Namespace) -> dict[str, Any]:
    paths = _paths(args.products_dir, args.product_slug)
    expected = str(args.expected_sha256 or "").lower()
    if not SHA256_RE.fullmatch(expected):
        raise WorkflowError("invalid_sha256", "Publish vyžaduje přesný SHA-256 schválené verze.")
    with _locked(paths["lock"]):
        state = _recover_publishing(paths, _read_state(paths["state"]))
        _assert_operation(state, args.operation_id)
        if state.get("status") == "published":
            if state.get("publishedSha256") != expected:
                raise WorkflowError("publish_conflict", "Operace už publikovala jiný obsah.")
            return {"reused": True, **state}
        if state.get("status") not in {"draft", "publishing"}:
            raise WorkflowError("workflow_not_publishable", "Workflow není připravené k publikování.")
        if not isinstance(state.get("taskId"), int) or int(state["taskId"]) <= 0:
            raise WorkflowError("task_not_bound", "Finální Product DNA musí být svázaná s platným CSO taskem.")
        actual = _sha_file(paths["wip"])
        if actual != expected or state.get("wipSha256") != expected:
            raise WorkflowError("stale_approval", "Publikovaný obsah neodpovídá schválené rozpracované verzi.")
        approvals = state.get("approvals") or {}
        required = range(1, 6) if state.get("mode") == "guided" else [5]
        missing = [step for step in required if str(step) not in approvals]
        if missing:
            raise WorkflowError("approval_incomplete", "Chybí povinné schválení jednoho nebo více kroků.")
        final_approval = approvals.get("5")
        if not isinstance(final_approval, dict) or final_approval.get("sha256") != expected:
            raise WorkflowError("stale_approval", "Finální schválení neodpovídá publikovaným bytes.")
        value = paths["wip"].read_text(encoding="utf-8")
        _validate_document(value, final=True)
        current_sha = _sha_file(paths["active"])
        base_sha = state.get("baseSha256")
        if current_sha not in {base_sha, expected}:
            raise WorkflowError(
                "product_dna_changed",
                "Aktivní Product DNA se během práce změnila; novější obsah nebude přepsán.",
            )
        now = _now()
        manifest = {
            "formatVersion": 1,
            "artifactType": "product-dna",
            "producer": "100m-offer-generator",
            "skillVersion": SKILL_VERSION,
            "revision": int(state["revision"]),
            "taskId": int(state["taskId"]),
            "productSlug": state["productSlug"],
            "operationId": state["operationId"],
            "sha256": expected,
            "publishedAt": now,
        }
        state = {
            **state,
            "status": "publishing",
            "criticalClaimsConfirmedAt": now,
            "publishIntent": {
                "sha256": expected,
                "baseSha256": base_sha,
                "manifest": manifest,
                "backupPath": None,
            },
            "updatedAt": now,
        }
        _atomic_json(paths["state"], state)
        backup: Path | None = None
        if current_sha is not None and current_sha != expected:
            backup = _backup_path(paths, int(state["revision"]))
            _atomic_text(backup, paths["active"].read_text(encoding="utf-8"), 0o644)
            state["publishIntent"]["backupPath"] = str(backup)
            _atomic_json(paths["state"], state)
        if current_sha != expected:
            _atomic_text(paths["active"], value, 0o644)
        _atomic_json(paths["manifest"], manifest, 0o644)
        completed = {
            **state,
            "status": "published",
            "publishedSha256": expected,
            "publishedAt": now,
            "backupPath": str(backup) if backup else None,
            "manifestPath": str(paths["manifest"]),
            "outputPath": str(paths["active"]),
            "updatedAt": now,
        }
        completed.pop("publishIntent", None)
        _atomic_json(paths["state"], completed)
        return {"reused": False, **completed}


def _status(args: argparse.Namespace) -> dict[str, Any]:
    paths = _paths(args.products_dir, args.product_slug)
    if not paths["state"].exists():
        return {
            "stateVersion": STATE_VERSION,
            "skillVersion": SKILL_VERSION,
            "status": "not_started",
            "productSlug": _validate_slug(args.product_slug),
            "activeSha256": _sha_file(paths["active"]),
            "outputPath": str(paths["active"]),
        }
    with _locked(paths["lock"]):
        state = _read_state(paths["state"], missing_ok=True)
        if state:
            state = _recover_publishing(paths, state)
            return state
        raise WorkflowError("state_missing", "Workflow state zmizel během načtení.")


def _add_common(command: argparse.ArgumentParser) -> None:
    command.add_argument("--product-slug", required=True)
    command.add_argument("--products-dir", default=str(DEFAULT_PRODUCTS_DIR))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely draft, approve and publish one Product DNA revision")
    commands = parser.add_subparsers(dest="command", required=True)

    status = commands.add_parser("status")
    _add_common(status)

    start = commands.add_parser("start")
    _add_common(start)
    start.add_argument("--mode", choices=["guided", "fast"], default="guided")
    start.add_argument("--new-revision", choices=["yes"], default=None)

    bind = commands.add_parser("bind-task")
    _add_common(bind)
    bind.add_argument("--operation-id", required=True)
    bind.add_argument("--task-id", type=int, required=True)

    abandon = commands.add_parser("abandon")
    _add_common(abandon)
    abandon.add_argument("--operation-id", required=True)
    abandon.add_argument("--confirmed", choices=["yes"], required=True)

    draft = commands.add_parser("draft")
    _add_common(draft)
    draft.add_argument("--operation-id", required=True)
    draft.add_argument("--input", required=True)
    draft.add_argument("--completed-step", type=int, choices=range(1, 6), required=True)

    approve = commands.add_parser("approve")
    _add_common(approve)
    approve.add_argument("--operation-id", required=True)
    approve.add_argument("--step", type=int, choices=range(1, 6), required=True)
    approve.add_argument("--expected-sha256", required=True)

    publish = commands.add_parser("publish")
    _add_common(publish)
    publish.add_argument("--operation-id", required=True)
    publish.add_argument("--expected-sha256", required=True)
    publish.add_argument("--approved", choices=["yes"], required=True)
    publish.add_argument("--critical-claims-confirmed", choices=["yes"], required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "start":
            result = _start(args)
        elif args.command == "bind-task":
            result = _bind_task(args)
        elif args.command == "draft":
            result = _draft(args)
        elif args.command == "abandon":
            result = _abandon(args)
        elif args.command == "approve":
            result = _approve(args)
        elif args.command == "publish":
            result = _publish(args)
        else:
            result = _status(args)
        print(json.dumps({"ok": True, **result}, ensure_ascii=False))
        return 0
    except (WorkflowError, OSError, ValueError) as exc:
        code = exc.code if isinstance(exc, WorkflowError) else "product_dna_workflow_error"
        print(json.dumps({"ok": False, "code": code, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
