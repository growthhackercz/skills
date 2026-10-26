#!/usr/bin/env python3
"""Store-first, fail-closed GHL REST helper for CliqSales CRM Sync.

Reads are separate from writes. A write can only execute from a canonical plan
whose SHA-256 is confirmed on the same invocation, and every write requires a
readback endpoint. DELETE, messaging, and custom-field schema writes are not
implemented by this helper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SHARED_LIB = SKILL_DIR.parent / "_lib"
DEFAULT_API_BASE = "https://services.leadconnectorhq.com"
API_VERSION = "2021-07-28"
USER_AGENT = "CliqSales-CRM-Sync/2.0.2"
PRECONDITION_HASH_MODE = "response-without-root-trace-id-v1"
ID = r"[A-Za-z0-9_-]+"
MAX_RESPONSE_BYTES = 10 * 1024 * 1024

READ_PATHS = [
    re.compile(rf"^/locations/{ID}$"),
    re.compile(rf"^/locations/{ID}/customFields$"),
    re.compile(rf"^/locations/{ID}/tags$"),
    re.compile(r"^/contacts/?$"),
    re.compile(rf"^/contacts/{ID}$"),
    re.compile(rf"^/contacts/{ID}/notes/?$"),
    re.compile(rf"^/contacts/{ID}/tasks/?$"),
    re.compile(r"^/opportunities/search$"),
    re.compile(r"^/opportunities/pipelines/?$"),
    re.compile(rf"^/opportunities/pipelines/{ID}$"),
    re.compile(rf"^/opportunities/{ID}$"),
    re.compile(r"^/users/?$"),
]
WRITE_PATHS: dict[str, list[re.Pattern[str]]] = {
    "POST": [
        re.compile(r"^/contacts/?$"),
        re.compile(rf"^/contacts/{ID}/notes/?$"),
        re.compile(rf"^/contacts/{ID}/tasks/?$"),
        re.compile(rf"^/contacts/{ID}/tags/?$"),
        re.compile(r"^/opportunities/?$"),
    ],
    "PUT": [
        re.compile(rf"^/contacts/{ID}$"),
        re.compile(rf"^/contacts/{ID}/tasks/{ID}$"),
        re.compile(rf"^/opportunities/{ID}$"),
    ],
    "PATCH": [],
}


class CliError(RuntimeError):
    def __init__(self, code: str, message: str, exit_code: int = 65):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class ProviderError(RuntimeError):
    def __init__(self, status: int | None):
        super().__init__(
            "GHL request selhal"
            if status is None
            else f"GHL request selhal (HTTP {status})"
        )
        self.status = status


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


HTTP_OPENER = urllib.request.build_opener(NoRedirect)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CliError("INVALID_INPUT", f"{label} není čitelný validní JSON") from exc
    if not isinstance(value, dict):
        raise CliError("INVALID_INPUT", f"{label} musí být JSON objekt")
    return value


def resolve_shared_lib() -> Path:
    # Match the existing Netlify/publisher lookup: workspace and user copies
    # consume the runtime catalog, never a copied workspace _lib pseudo-skill.
    candidates: list[Path] = []
    for env_name in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw_home = os.environ.get(env_name, "").strip()
        if raw_home:
            home = Path(raw_home).expanduser()
            candidates.extend((home / "cs-skills" / "_lib", home / ".openclaw" / "cs-skills" / "_lib"))
    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
    candidates.append(SHARED_LIB)
    candidates.extend(parent / "cs-skills" / "_lib" for parent in SCRIPT_DIR.parents)
    for candidate in candidates:
        if (candidate / "cc_credentials.py").is_file():
            return candidate
    raise CliError("RESOLVER_MISSING", "sdílený credential resolver není dostupný")


def load_credentials(profile: str | None) -> dict[str, str]:
    sys.path.insert(0, str(resolve_shared_lib()))
    try:
        from cc_credentials import CredentialError, ghl_credentials_strict
    except Exception as exc:
        raise CliError(
            "RESOLVER_MISSING", "sdílený credential resolver se nepodařilo načíst"
        ) from exc
    try:
        credentials = ghl_credentials_strict(profile=profile)
    except CredentialError as exc:
        raise CliError(
            str(getattr(exc, "code", "GHL_CREDENTIALS_INVALID")), str(exc)
        ) from exc
    except Exception as exc:
        raise CliError(
            "GHL_CREDENTIALS_INVALID", "GHL integraci se nepodařilo bezpečně načíst"
        ) from exc
    if not credentials:
        raise CliError(
            "GHL_CREDENTIALS_MISSING",
            "CliqSales (GoHighLevel) integrace není nastavená; "
            "doplňte ji v Control Center → Nastavení → Integrace",
        )
    return credentials


def api_base() -> str:
    configured = os.environ.get("GHL_API_BASE_URL", "").strip()
    if not configured:
        return DEFAULT_API_BASE
    if os.environ.get("CC_GHL_ALLOW_TEST_BASE_URL") != "1":
        raise CliError(
            "UNSAFE_API_BASE", "vlastní GHL API base URL není v produkčním běhu povolená"
        )
    parsed = urllib.parse.urlsplit(configured)
    if parsed.hostname not in {"127.0.0.1", "::1", "localhost"}:
        raise CliError(
            "UNSAFE_API_BASE", "testovací GHL API base URL musí být loopback"
        )
    return configured.rstrip("/")


def substitute_location(value: Any, location_id: str) -> Any:
    if isinstance(value, str):
        return value.replace("{locationId}", location_id)
    if isinstance(value, list):
        return [substitute_location(item, location_id) for item in value]
    if isinstance(value, dict):
        return {key: substitute_location(item, location_id) for key, item in value.items()}
    return value


def normalize_path(raw_path: str, location_id: str) -> str:
    path = raw_path.replace("{locationId}", location_id).strip()
    if not path.startswith("/") or "\\" in path or ".." in path:
        raise CliError("PATH_BLOCKED", "GHL path není povolený")
    parsed = urllib.parse.urlsplit(path)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise CliError("PATH_BLOCKED", "GHL path nesmí obsahovat URL ani query string")
    return parsed.path


def allowed_read(path: str) -> bool:
    return any(pattern.fullmatch(path) for pattern in READ_PATHS)


def allowed_write(method: str, path: str) -> bool:
    return any(pattern.fullmatch(path) for pattern in WRITE_PATHS.get(method, []))


def required_approval_class(path: str) -> str:
    if re.fullmatch(r"/contacts/?", path):
        return "contact-create"
    if re.fullmatch(rf"/contacts/{ID}", path):
        return "identity-update"
    if re.fullmatch(rf"/contacts/{ID}/(?:notes|tasks|tags)/?", path) or re.fullmatch(
        rf"/contacts/{ID}/tasks/{ID}", path
    ):
        return "safe-note-task-tag"
    return "opportunity-update"


def canonical_sha(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def redact_secret(value: Any, secret: str) -> Any:
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, list):
        return [redact_secret(item, secret) for item in value]
    if isinstance(value, dict):
        return {key: redact_secret(item, secret) for key, item in value.items()}
    return value


def reject_secret_payload(value: Any, secret: str, label: str) -> None:
    if redact_secret(value, secret) != value:
        raise CliError("SECRET_IN_PAYLOAD", f"{label} nesmí obsahovat GHL credential")


def bind_location(body: dict[str, Any], path: str, location_id: str) -> None:
    if path in {"/contacts", "/contacts/", "/opportunities", "/opportunities/"}:
        body.setdefault("locationId", location_id)

    def validate(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower().replace("_", "") == "locationid":
                    if str(item or "").strip() != location_id:
                        raise CliError(
                            "LOCATION_DRIFT", "write body obsahuje jinou GHL location"
                        )
                validate(item)
        elif isinstance(value, list):
            for item in value:
                validate(item)

    validate(body)


def request_json(
    credentials: dict[str, str],
    method: str,
    path: str,
    query: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    url = f"{api_base()}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query, doseq=True)}"
    data = None
    headers = {
        "Authorization": f"Bearer {credentials['api_key']}",
        "Version": API_VERSION,
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with HTTP_OPENER.open(request, timeout=20) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        exc.read()
        raise ProviderError(exc.code) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderError(None) from exc
    if not payload:
        return None
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ProviderError(None)
    try:
        return redact_secret(json.loads(payload), credentials["api_key"])
    except json.JSONDecodeError as exc:
        raise ProviderError(None) from exc


def result_pointer(document: Any, pointer: str) -> str:
    current = document
    if not pointer.startswith("/"):
        raise CliError("INVALID_PLAN", "result_id_pointer musí být JSON pointer")
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise CliError("READBACK_FAILED", "write response neobsahuje readback id")
        current = current[token]
    value = str(current or "").strip()
    if not re.fullmatch(ID, value):
        raise CliError("READBACK_FAILED", "write response vrátila neplatné readback id")
    return value


def precondition_sha(response: Any, mode: str | None) -> str:
    if mode is None:
        # Historical plans bind the whole response. Never reinterpret an
        # already approved hash under a weaker policy.
        return canonical_sha({"response": response})
    if mode != PRECONDITION_HASH_MODE:
        raise CliError("INVALID_PLAN", "write plan má neznámý způsob kontroly změn")
    # Only the provider envelope's string request ID is volatile. Nested
    # business data, including a field named traceId, remains authoritative.
    if isinstance(response, dict) and isinstance(response.get("traceId"), str):
        response = {key: value for key, value in response.items() if key != "traceId"}
    return canonical_sha({"response": response})


def canonical_plan(args: argparse.Namespace, credentials: dict[str, str]) -> dict[str, Any]:
    method = args.method.upper()
    path = normalize_path(args.path, credentials["location_id"])
    if not allowed_write(method, path):
        raise CliError("WRITE_BLOCKED", "tento GHL write endpoint nebo metoda nejsou povolené")
    expected_approval = required_approval_class(path)
    if args.approval_class != expected_approval:
        raise CliError(
            "APPROVAL_CLASS_MISMATCH",
            f"endpoint vyžaduje approval class {expected_approval}",
        )
    body = substitute_location(read_json_object(Path(args.body), "--body"), credentials["location_id"])
    reject_secret_payload(body, credentials["api_key"], "write body")
    bind_location(body, path, credentials["location_id"])
    readback_path = normalize_path(args.readback_path, credentials["location_id"])
    if "{resultId}" not in args.readback_path and not allowed_read(readback_path):
        raise CliError("READBACK_BLOCKED", "readback endpoint není povolený")
    if "{resultId}" in args.readback_path:
        candidate = normalize_path(
            args.readback_path.replace("{resultId}", "RESULTID"),
            credentials["location_id"],
        )
        if not allowed_read(candidate) or not args.result_id_pointer:
            raise CliError(
                "READBACK_BLOCKED",
                "dynamický readback vyžaduje povolený path a --result-id-pointer",
            )
    elif args.result_id_pointer:
        raise CliError(
            "INVALID_PLAN", "--result-id-pointer lze použít jen s {resultId} v readback path"
        )
    raw_precondition_path = args.precondition_path
    if not raw_precondition_path and "{resultId}" not in args.readback_path:
        raw_precondition_path = args.readback_path
    if not raw_precondition_path:
        raise CliError(
            "PRECONDITION_REQUIRED",
            "create plán vyžaduje --precondition-path pro duplicate/drift kontrolu",
        )
    precondition_path = normalize_path(raw_precondition_path, credentials["location_id"])
    if not allowed_read(precondition_path):
        raise CliError("READ_BLOCKED", "precondition read endpoint není povolený")
    precondition_query = (
        substitute_location(
            read_json_object(Path(args.precondition_query), "--precondition-query"),
            credentials["location_id"],
        )
        if args.precondition_query
        else {}
    )
    reject_secret_payload(
        precondition_query, credentials["api_key"], "precondition query"
    )
    precondition_response = request_json(
        credentials,
        "GET",
        precondition_path,
        query=precondition_query,
    )
    return {
        "schema": "cliqsales.ghl_write_plan.v1",
        "location_id": credentials["location_id"],
        "method": method,
        "path": path,
        "body": body,
        "readback_path": args.readback_path.replace(
            "{locationId}", credentials["location_id"]
        ),
        "result_id_pointer": args.result_id_pointer or None,
        "approval_class": args.approval_class,
        "precondition_path": precondition_path,
        "precondition_query": precondition_query,
        "precondition_hash_mode": PRECONDITION_HASH_MODE,
        "precondition_sha256": precondition_sha(precondition_response, PRECONDITION_HASH_MODE),
    }


def command_status(args: argparse.Namespace, credentials: dict[str, str]) -> None:
    print(
        json.dumps(
            {
                "ok": True,
                "source": credentials["source"],
                "profile": credentials.get("profile") or None,
                "label": credentials.get("label") or None,
                "location_id": credentials["location_id"],
            },
            ensure_ascii=False,
        )
    )


def command_read(args: argparse.Namespace, credentials: dict[str, str]) -> None:
    path = normalize_path(args.path, credentials["location_id"])
    if not allowed_read(path):
        raise CliError("READ_BLOCKED", "tento GHL read endpoint není povolený")
    query = (
        substitute_location(
            read_json_object(Path(args.query), "--query"), credentials["location_id"]
        )
        if args.query
        else {}
    )
    reject_secret_payload(query, credentials["api_key"], "read query")
    response = request_json(credentials, "GET", path, query=query)
    atomic_json(Path(args.output), response)
    print(json.dumps({"ok": True, "output": args.output}, ensure_ascii=False))


def command_plan(args: argparse.Namespace, credentials: dict[str, str]) -> None:
    canonical = canonical_plan(args, credentials)
    sha256 = canonical_sha(canonical)
    document = {
        **canonical,
        "plan_sha256": sha256,
    }
    atomic_json(Path(args.output), document)
    print(
        json.dumps(
            {
                "ok": True,
                "mode": "plan",
                "plan_sha256": sha256,
                "output": args.output,
                "provider_requests": 1,
                "provider_writes": 0,
            },
            ensure_ascii=False,
        )
    )


def command_apply(args: argparse.Namespace, credentials: dict[str, str]) -> None:
    plan = read_json_object(Path(args.plan), "--plan")
    supplied_sha = str(plan.pop("plan_sha256", ""))
    if plan.get("schema") != "cliqsales.ghl_write_plan.v1":
        raise CliError("INVALID_PLAN", "write plan má neplatné schema")
    actual_sha = canonical_sha(plan)
    if not supplied_sha or supplied_sha != actual_sha or args.confirm_plan_sha != actual_sha:
        raise CliError("PLAN_HASH_MISMATCH", "write plan SHA-256 nesouhlasí")
    if plan.get("location_id") != credentials["location_id"]:
        raise CliError("LOCATION_DRIFT", "write plan míří do jiné GHL location")
    method = str(plan.get("method") or "").upper()
    path = normalize_path(str(plan.get("path") or ""), credentials["location_id"])
    if not allowed_write(method, path):
        raise CliError("WRITE_BLOCKED", "write endpoint už není povolený")
    if plan.get("approval_class") != required_approval_class(path):
        raise CliError("APPROVAL_CLASS_MISMATCH", "write plan má neplatnou approval class")
    body = plan.get("body")
    if not isinstance(body, dict):
        raise CliError("INVALID_PLAN", "write plan body není JSON objekt")
    precondition_path = normalize_path(
        str(plan.get("precondition_path") or ""), credentials["location_id"]
    )
    precondition_query = plan.get("precondition_query")
    if not allowed_read(precondition_path) or not isinstance(precondition_query, dict):
        raise CliError("INVALID_PLAN", "write plan nemá platnou read precondition")
    precondition_mode = plan.get("precondition_hash_mode")
    if "precondition_hash_mode" in plan and precondition_mode != PRECONDITION_HASH_MODE:
        raise CliError("INVALID_PLAN", "write plan má neznámý způsob kontroly změn")
    current_precondition = request_json(
        credentials,
        "GET",
        precondition_path,
        query=precondition_query,
    )
    if precondition_sha(current_precondition, precondition_mode) != plan.get(
        "precondition_sha256"
    ):
        raise CliError(
            "PROVIDER_DRIFT",
            "GHL stav se od plánu změnil; vytvořte nový read-only plán",
        )

    report = {
        "schema": "cliqsales.ghl_write_report.v1",
        "plan_sha256": actual_sha,
        "location_id": credentials["location_id"],
        "method": method,
        "path": path,
        "approval_class": plan.get("approval_class"),
        "status": "running",
        "provider_status": None,
        "write_response": None,
        "readback_response": None,
    }
    atomic_json(Path(args.report), report)
    try:
        write_response = request_json(credentials, method, path, body=body)
        report.update(
            {
                "status": "write_complete_readback_pending",
                "provider_status": "write_ok",
                "write_response": write_response,
            }
        )
        atomic_json(Path(args.report), report)
        readback_path = str(plan.get("readback_path") or "")
        pointer = plan.get("result_id_pointer")
        if "{resultId}" in readback_path:
            result_id = result_pointer(write_response, str(pointer or ""))
            readback_path = readback_path.replace("{resultId}", result_id)
        readback_path = normalize_path(readback_path, credentials["location_id"])
        if not allowed_read(readback_path):
            raise CliError("READBACK_BLOCKED", "readback endpoint už není povolený")
        readback_response = request_json(credentials, "GET", readback_path)
        report.update(
            {
                "status": "complete",
                "provider_status": "write_and_readback_ok",
                "readback_response": readback_response,
            }
        )
        atomic_json(Path(args.report), report)
    except Exception as exc:
        report["status"] = "failed_after_write_attempt"
        report["provider_status"] = (
            f"http_{exc.status}" if isinstance(exc, ProviderError) and exc.status else "failed"
        )
        atomic_json(Path(args.report), report)
        raise
    print(
        json.dumps(
            {"ok": True, "mode": "apply", "report": args.report},
            ensure_ascii=False,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status")

    read = subparsers.add_parser("read")
    read.add_argument("--path", required=True)
    read.add_argument("--query")
    read.add_argument("--output", required=True)

    plan = subparsers.add_parser("plan")
    plan.add_argument("--method", required=True, choices=["POST", "PUT", "PATCH"])
    plan.add_argument("--path", required=True)
    plan.add_argument("--body", required=True)
    plan.add_argument("--readback-path", required=True)
    plan.add_argument("--result-id-pointer")
    plan.add_argument("--precondition-path")
    plan.add_argument("--precondition-query")
    plan.add_argument(
        "--approval-class",
        required=True,
        choices=["safe-note-task-tag", "contact-create", "identity-update", "opportunity-update"],
    )
    plan.add_argument("--output", required=True)

    apply = subparsers.add_parser("apply")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--confirm-plan-sha", required=True)
    apply.add_argument("--report", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    credentials = load_credentials(args.profile)
    if args.command == "status":
        command_status(args, credentials)
    elif args.command == "read":
        command_read(args, credentials)
    elif args.command == "plan":
        command_plan(args, credentials)
    else:
        command_apply(args, credentials)


if __name__ == "__main__":
    try:
        main()
    except CliError as exc:
        print(
            json.dumps({"ok": False, "code": exc.code, "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        raise SystemExit(exc.exit_code)
    except ProviderError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "code": "GHL_PROVIDER_ERROR",
                    "status": exc.status,
                    "error": str(exc),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise SystemExit(69)
