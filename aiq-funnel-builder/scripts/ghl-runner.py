#!/usr/bin/env python3
"""Run the AIQ GHL entrypoints with short-lived store-first credentials.

The secret is resolved only for the selected child process. It is never printed,
persisted in the generated funnel, or injected into the long-lived agent runtime.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SHARED_LIB = SKILL_DIR.parent / "_lib"


def fail(message: str, code: int = 65) -> None:
    print(f"[aiq-ghl] STOP: {message}", file=sys.stderr)
    raise SystemExit(code)


def resolve_shared_lib() -> Path:
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
    fail("sdílený credential resolver není dostupný")


def load_credentials(profile: str | None) -> dict[str, str]:
    sys.path.insert(0, str(resolve_shared_lib()))
    try:
        from cc_credentials import CredentialError, ghl_credentials_strict
    except Exception:
        fail("sdílený credential resolver se nepodařilo načíst")
    try:
        credentials = ghl_credentials_strict(profile=profile)
    except CredentialError as exc:
        code = str(getattr(exc, "code", "GHL_CREDENTIALS_INVALID"))
        fail(f"{code}: {exc}")
    except Exception:
        fail("GHL integraci se nepodařilo bezpečně načíst")
    if not credentials:
        fail(
            "GHL_CREDENTIALS_MISSING: CliqSales (GoHighLevel) integrace není nastavená; "
            "doplňte ji v Control Center → Nastavení → Integrace"
        )
    return credentials


def load_deploy_credentials(require_openrouter: bool = True) -> dict[str, str]:
    sys.path.insert(0, str(resolve_shared_lib()))
    try:
        from cc_credentials import CredentialError, get_env_or_variable, netlify_credentials
    except Exception:
        fail("sdílený credential resolver se nepodařilo načíst")

    try:
        netlify = netlify_credentials()
        openrouter_api_key = get_env_or_variable("OPENROUTER_API_KEY")
    except CredentialError:
        fail("deploy integrace se nepodařilo bezpečně načíst")
    except Exception:
        fail("deploy integrace se nepodařilo bezpečně načíst")

    netlify_auth_token = str(netlify.get("auth_token") or "").strip()
    if not netlify_auth_token:
        fail(
            "NETLIFY_CREDENTIALS_MISSING: Netlify integrace není nastavená; "
            "doplňte ji v Control Center → Nastavení → Integrace"
        )
    if require_openrouter and not openrouter_api_key:
        fail(
            "OPENROUTER_CREDENTIALS_MISSING: OpenRouter integrace není nastavená; "
            "doplňte ji v Control Center → Nastavení → Integrace"
        )
    credentials = {
        "netlify_auth_token": netlify_auth_token,
    }
    if openrouter_api_key:
        credentials["openrouter_api_key"] = openrouter_api_key
    return credentials


def child_env(
    credentials: dict[str, str], deploy_credentials: dict[str, str] | None = None
) -> dict[str, str]:
    env = os.environ.copy()
    env["GHL_API_KEY"] = credentials["api_key"]
    env["GHL_LOCATION_ID"] = credentials["location_id"]
    if credentials.get("user"):
        env["GHL_USER"] = credentials["user"]
    else:
        env.pop("GHL_USER", None)
    env["CC_GHL_CREDENTIAL_SCOPE"] = "aiq-funnel-builder"
    if deploy_credentials:
        # Store-first values intentionally replace a stale Gateway process env.
        # They exist only in this short-lived deploy child.
        env["NETLIFY_AUTH_TOKEN"] = deploy_credentials["netlify_auth_token"]
        env["OPENROUTER_API_KEY"] = deploy_credentials["openrouter_api_key"]
    return env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--profile")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    deploy = subparsers.add_parser("deploy")
    deploy.add_argument("deploy_args", nargs=argparse.REMAINDER)

    fields = subparsers.add_parser("fields")
    fields.add_argument("--app", required=True)
    mode = fields.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--verify", action="store_true")
    fields.add_argument("--confirm-plan-sha")

    netlify = subparsers.add_parser("netlify")
    netlify.add_argument("netlify_args", nargs=argparse.REMAINDER)
    return parser.parse_args()


def exec_deploy(args: argparse.Namespace, env: dict[str, str]) -> None:
    forwarded = list(args.deploy_args)
    if forwarded[:1] == ["--"]:
        forwarded = forwarded[1:]
    try:
        os.execvpe(
            "node",
            ["node", str(SCRIPT_DIR / "deploy.mjs"), *forwarded],
            env,
        )
    except OSError:
        fail("Node runtime pro deploy nelze spustit", 69)


def exec_fields(args: argparse.Namespace, env: dict[str, str]) -> None:
    app = Path(args.app).expanduser().resolve()
    script = SKILL_DIR / "template" / "scripts" / "ensure-fields.mjs"
    spec = app / "funnel-spec.json"
    if not script.is_file() or not spec.is_file():
        fail("--app musí ukazovat na připravenou funnel appku", 64)
    if args.confirm_plan_sha and not args.apply:
        fail("--confirm-plan-sha lze použít jen s --apply", 64)
    if args.apply and not args.confirm_plan_sha:
        fail("--apply vyžaduje --confirm-plan-sha", 64)

    env["AIQ_APP_ROOT"] = str(app)
    command = ["node", str(script)]
    if args.apply:
        command.extend(["--apply", "--confirm-plan-sha", args.confirm_plan_sha])
    elif args.verify:
        command.append("--verify")
    os.chdir(app)
    try:
        os.execvpe("node", command, env)
    except OSError:
        fail("Node runtime pro GHL fields nelze spustit", 69)


def exec_netlify(args: argparse.Namespace, credentials: dict[str, str]) -> None:
    forwarded = list(args.netlify_args)
    if forwarded[:1] == ["--"]:
        forwarded = forwarded[1:]
    if not forwarded:
        fail("Netlify příkaz chybí", 64)
    if any(arg == "--auth" or arg.startswith("--auth=") for arg in forwarded):
        fail("Netlify token nesmí být předán v argumentech", 64)

    env = os.environ.copy()
    env["NETLIFY_AUTH_TOKEN"] = credentials["netlify_auth_token"]
    try:
        os.execvpe("netlify", ["netlify", *forwarded], env)
    except OSError:
        fail("Netlify CLI nelze spustit", 69)


def main() -> None:
    args = parse_args()
    if args.mode == "netlify":
        exec_netlify(args, load_deploy_credentials(require_openrouter=False))
        return
    credentials = load_credentials(args.profile)
    deploy_credentials = load_deploy_credentials() if args.mode == "deploy" else None
    env = child_env(credentials, deploy_credentials)
    if args.mode == "deploy":
        exec_deploy(args, env)
    exec_fields(args, env)


if __name__ == "__main__":
    main()
