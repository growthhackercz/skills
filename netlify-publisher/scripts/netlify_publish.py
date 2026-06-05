#!/usr/bin/env python3
"""Netlify publisher v1.0 — build, deploy, promote, rename, custom domain, rollback, DB."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


# ─── Konstanty ────────────────────────────────────────────────────────────

MAX_FILES = 5000
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024
NPM_INSTALL_TIMEOUT = 300  # 5 min
BUILD_TIMEOUT = 600  # 10 min
DNS_POLL_TIMEOUT = 300  # 5 min
DNS_POLL_INTERVAL = 15  # sekund
DEFAULT_CREATED_VIA = "control-center-netlify-publisher"
SITE_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])$")
DOMAIN_RE = re.compile(r"^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")

BLOCKED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".next",  # cache (po buildu by mělo být smazané)
    "node_modules",
    "__pycache__",
    ".cache",
    ".turbo",
    ".parcel-cache",
}
BLOCKED_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
}
BLOCKED_SUFFIXES = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".key",
    ".pem",
    ".p12",
    ".pfx",
}


class NetlifyPublishError(RuntimeError):
    """Doménová chyba publisheru — vždy chytaná v main()."""

    pass


# ─── Credentials ──────────────────────────────────────────────────────────


def load_credentials_helper():
    """Pokus o načtení CC credential resolveru. Fallback = env vars."""
    candidates = []
    openclaw_home = os.environ.get("OPENCLAW_HOME") or os.environ.get("CC_OPENCLAW_HOME")
    if openclaw_home:
        candidates.append(Path(openclaw_home).expanduser() / "cs-skills" / "_lib")
    candidates.append(Path(__file__).resolve().parents[2] / "_lib")

    for candidate in candidates:
        if candidate.exists():
            sys.path.insert(0, str(candidate))
            break

    try:
        from cc_credentials import netlify_credentials  # type: ignore

        return netlify_credentials
    except Exception:
        return None


def fallback_credentials() -> dict[str, str]:
    return {
        "auth_token": os.environ.get("NETLIFY_AUTH_TOKEN", "").strip(),
        "site_id": os.environ.get("NETLIFY_SITE_ID", "").strip(),
        "account_slug": os.environ.get("NETLIFY_ACCOUNT_SLUG", "").strip(),
    }


def load_netlify_credentials() -> dict[str, str]:
    resolver = load_credentials_helper()
    credentials = resolver() if resolver else fallback_credentials()
    if not isinstance(credentials, dict):
        credentials = {}
    return {
        "auth_token": str(
            credentials.get("auth_token") or os.environ.get("NETLIFY_AUTH_TOKEN") or ""
        ).strip(),
        "site_id": str(credentials.get("site_id") or os.environ.get("NETLIFY_SITE_ID") or "").strip(),
        "account_slug": str(
            credentials.get("account_slug") or os.environ.get("NETLIFY_ACCOUNT_SLUG") or ""
        ).strip(),
    }


# ─── Path helpers ──────────────────────────────────────────────────────────


def documents_root() -> Path:
    return Path(os.environ.get("DOCUMENTS_PATH") or "/documents").expanduser().resolve()


def resolve_project_dir(value: str) -> Path:
    """Resolvuje projekt path. Sandbox: musí být uvnitř /documents/sites/<slug>/.

    Konvence: všechny publikovatelné projekty žijí v /documents/sites/<slug>/.
    Artefakty publisheru (logs) patří mimo deploy scope do
    /documents/platform/netlify-publisher/<slug>/.

    Override pro testing: NETLIFY_ALLOW_OUTSIDE_DOCUMENTS=1 (nedoporučeno).
    """
    raw = Path(value).expanduser()
    path = raw if raw.is_absolute() else Path.cwd() / raw
    try:
        resolved = path.resolve()
    except FileNotFoundError:
        raise NetlifyPublishError(f"Cesta neexistuje: {value}")

    if not resolved.is_dir():
        raise NetlifyPublishError(f"Cesta není složka: {resolved}")

    root = documents_root()
    allow_outside = os.environ.get("NETLIFY_ALLOW_OUTSIDE_DOCUMENTS") == "1"
    if allow_outside:
        return resolved

    # Sandbox check #1: musí být uvnitř /documents
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise NetlifyPublishError(f"Cesta musí být uvnitř {root}") from exc

    # Sandbox check #2 (strict): musí být uvnitř /documents/sites/<slug>/
    sites_root = root / "sites"
    try:
        rel_to_sites = resolved.relative_to(sites_root)
    except ValueError:
        raise NetlifyPublishError(
            f"Projekt musí být v /documents/sites/<slug>/. Aktuálně: {resolved}. "
            f"Konvence: publikovatelné projekty → /documents/sites/<slug>/, "
            f"artefakty publisheru → /documents/platform/netlify-publisher/<slug>/."
        )

    parts = rel_to_sites.parts
    if not parts or not SLUG_RE.fullmatch(parts[0]):
        raise NetlifyPublishError(
            f"Cesta {resolved} nemá platný slug projektu hned za /documents/sites/. "
            "Slug musí být lowercase alfanumerický s pomlčkami."
        )

    return resolved


def resolve_publish_dir(value: str, require_index_html: bool = True) -> Path:
    """Validuje deploy složku (musí obsahovat index.html pro static)."""
    resolved = resolve_project_dir(value)

    if require_index_html and not (resolved / "index.html").is_file():
        raise NetlifyPublishError("Deploy složka musí obsahovat index.html")

    return resolved


# ─── File security ─────────────────────────────────────────────────────────


def is_blocked_file(path: Path) -> bool:
    name = path.name
    lower_name = name.lower()
    if lower_name in BLOCKED_FILE_NAMES:
        return True
    if lower_name.startswith(".env."):
        return True
    return path.suffix.lower() in BLOCKED_SUFFIXES


def collect_publish_files(root: Path) -> list[Path]:
    """Walk deploy složky, validuje proti BLOCKED_* + size limity."""
    files: list[Path] = []
    for current_root, dirs, filenames in os.walk(root):
        dirs[:] = sorted(
            name for name in dirs if name not in BLOCKED_DIR_NAMES and not name.endswith(".egg-info")
        )
        current = Path(current_root)
        for filename in sorted(filenames):
            path = current / filename
            rel = path.relative_to(root)
            if is_blocked_file(path):
                raise NetlifyPublishError(
                    f"Blokovaný soubor v deploy složce: {rel.as_posix()}"
                )
            if path.is_symlink():
                raise NetlifyPublishError(f"Symlinky nelze publikovat: {rel.as_posix()}")
            size = path.stat().st_size
            if size > MAX_FILE_BYTES:
                raise NetlifyPublishError(
                    f"Soubor je příliš velký (>50 MB): {rel.as_posix()}"
                )
            files.append(path)
            if len(files) > MAX_FILES:
                raise NetlifyPublishError(
                    f"Příliš mnoho souborů: limit je {MAX_FILES}"
                )
    return files


def total_publish_bytes(files: list[Path]) -> int:
    total = sum(path.stat().st_size for path in files)
    if total > MAX_TOTAL_BYTES:
        raise NetlifyPublishError("Deploy složka je větší než 100 MB")
    return total


# ─── CLI wrappers ──────────────────────────────────────────────────────────


def netlify_cli() -> str:
    configured = os.environ.get("NETLIFY_CLI", "").strip()
    candidate = configured or "netlify"
    resolved = shutil.which(candidate)
    if not resolved:
        raise NetlifyPublishError(
            "Netlify CLI je vyžadováno: nainstaluj netlify-cli a zajisti `netlify` v PATH"
        )
    return resolved


def npm_cli() -> str:
    resolved = shutil.which("npm")
    if not resolved:
        raise NetlifyPublishError("npm je vyžadováno pro build")
    return resolved


def sanitize_cli_output(value: str, token: str) -> str:
    text = value or ""
    if token:
        text = text.replace(token, "[redacted]")
    text = re.sub(r"(NETLIFY_AUTH_TOKEN=)[^\s\"']+", r"\1[redacted]", text)
    text = re.sub(r"(--auth(?:=|\s+))[^\s\"']+", r"\1[redacted]", text)
    return text.strip()


def parse_cli_json(stdout: str) -> Any:
    text = stdout.strip()
    if not text:
        return {}
    for index, char in enumerate(text):
        if char not in "{[":
            continue
        try:
            return json.loads(text[index:])
        except json.JSONDecodeError:
            continue
    raise NetlifyPublishError("Netlify CLI nevrátil JSON output")


def run_netlify_cli(args: list[str], credentials: dict[str, str], cwd: Path | None = None) -> Any:
    token = credentials.get("auth_token", "")
    if not token:
        raise NetlifyPublishError("NETLIFY_AUTH_TOKEN je vyžadován")

    env = os.environ.copy()
    env["NETLIFY_AUTH_TOKEN"] = token
    env.setdefault("NETLIFY_TELEMETRY_DISABLED", "1")
    env.setdefault("CI", "1")

    work_dir = cwd or documents_root()
    timeout = int(os.environ.get("NETLIFY_CLI_TIMEOUT_SECONDS") or "600")
    try:
        completed = subprocess.run(
            [netlify_cli(), *args],
            cwd=str(work_dir),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise NetlifyPublishError(f"Netlify CLI timeout po {timeout}s") from exc

    if completed.returncode != 0:
        stderr = sanitize_cli_output(completed.stderr, token)
        stdout = sanitize_cli_output(completed.stdout, token)
        detail = stderr or stdout or f"exit code {completed.returncode}"
        raise NetlifyPublishError(f"Netlify CLI selhal: {detail}")

    return parse_cli_json(completed.stdout)


def run_npm_command(args: list[str], cwd: Path, timeout: int) -> tuple[int, str, str]:
    """Vrátí (returncode, stdout, stderr) — npm jednorázový command."""
    env = os.environ.copy()
    env.setdefault("CI", "1")
    env.setdefault("NPM_CONFIG_FUND", "false")
    env.setdefault("NPM_CONFIG_AUDIT", "false")

    try:
        completed = subprocess.run(
            [npm_cli(), *args],
            cwd=str(cwd),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise NetlifyPublishError(f"npm timeout po {timeout}s: {' '.join(args)}") from exc

    return completed.returncode, completed.stdout, completed.stderr


# ─── Site name utilities ───────────────────────────────────────────────────


def normalize_site_name(value: str) -> str:
    name = value.strip().lower()
    if not name:
        return ""
    if not SITE_NAME_RE.fullmatch(name):
        raise NetlifyPublishError(
            "Netlify site name musí být 3-63 znaků: lowercase písmena, čísla, pomlčky"
        )
    return name


def normalize_slug(value: str) -> str:
    slug = (value or "").strip().lower()
    if not SLUG_RE.fullmatch(slug):
        raise NetlifyPublishError(
            f"Slug projektu musí být lowercase alfanumerický s pomlčkami: {value!r}"
        )
    return slug


def validate_domain(value: str) -> str:
    domain = (value or "").strip().lower().rstrip(".")
    if not DOMAIN_RE.fullmatch(domain):
        raise NetlifyPublishError(f"Doména není validní FQDN: {value!r}")
    return domain


# ─── Service credentials mapping (sync-creds) ──────────────────────────────

# Mapping: service → (CC credential helper function name, {source_field: NETLIFY_ENV_KEY})
SERVICE_CRED_HELPERS: dict[str, tuple[str, dict[str, str]]] = {
    "fakturoid": (
        "fakturoid_credentials",
        {
            "api_key": "FAKTUROID_API_KEY",
            "email": "FAKTUROID_EMAIL",
            "account_slug": "FAKTUROID_ACCOUNT_SLUG",
        },
    ),
    "meta": (
        "meta_credentials",
        {
            "access_token": "META_ACCESS_TOKEN",
            "ad_account_id": "META_AD_ACCOUNT_ID",
            "business_id": "META_BUSINESS_ID",
        },
    ),
    "google_ads": (
        "google_ads_credentials",
        {
            "developer_token": "GOOGLE_ADS_DEVELOPER_TOKEN",
            "client_id": "GOOGLE_ADS_CLIENT_ID",
            "client_secret": "GOOGLE_ADS_CLIENT_SECRET",
            "refresh_token": "GOOGLE_ADS_REFRESH_TOKEN",
            "customer_id": "GOOGLE_ADS_CUSTOMER_ID",
        },
    ),
    "ga4": (
        "ga4_credentials",
        {
            "property_id": "GA4_PROPERTY_ID",
            "service_account_json": "GA4_SERVICE_ACCOUNT_JSON",
        },
    ),
    "fio": (
        "fio_credentials",
        {
            "token": "FIO_TOKEN",
            "account_id": "FIO_ACCOUNT_ID",
        },
    ),
    "tink": (
        "tink_credentials",
        {
            "client_id": "TINK_CLIENT_ID",
            "client_secret": "TINK_CLIENT_SECRET",
            "refresh_token": "TINK_REFRESH_TOKEN",
        },
    ),
}


def load_service_credentials(service: str) -> tuple[dict[str, Any] | None, dict[str, str]]:
    """Načte credential helper z CC pro daný service. Vrátí (creds_dict | None, field_mapping)."""
    spec = SERVICE_CRED_HELPERS.get(service)
    if not spec:
        raise NetlifyPublishError(
            f"Neznámý service: {service}. Podporované: {sorted(SERVICE_CRED_HELPERS.keys())}"
        )

    func_name, field_mapping = spec

    # Pokus načíst CC credential resolver
    candidates = []
    openclaw_home = os.environ.get("OPENCLAW_HOME") or os.environ.get("CC_OPENCLAW_HOME")
    if openclaw_home:
        candidates.append(Path(openclaw_home).expanduser() / "cs-skills" / "_lib")
    candidates.append(Path(__file__).resolve().parents[2] / "_lib")

    for candidate in candidates:
        if candidate.exists():
            sys.path.insert(0, str(candidate))
            break

    try:
        import cc_credentials  # type: ignore

        resolver = getattr(cc_credentials, func_name, None)
        if not resolver:
            return None, field_mapping
        creds = resolver()
        if not isinstance(creds, dict):
            return None, field_mapping
        return creds, field_mapping
    except ImportError:
        return None, field_mapping


def set_netlify_env_var(
    site_id: str, key: str, value: str, credentials: dict[str, str]
) -> bool:
    """Wrap `netlify env:set KEY value --site <id> --context all`. Vrátí True pokud nastavené."""
    if not value:
        return False
    run_netlify_cli(
        [
            "env:set",
            key,
            str(value),
            "--context",
            "all",
            "--site",
            site_id,
            "--json",
        ],
        credentials,
    )
    return True


def generate_site_name_candidates(slug: str) -> list[str]:
    """Vrátí list 3 deterministických kandidátů: <slug>, cs-<slug>, cs-<slug>-<hash>."""
    base = normalize_slug(slug)
    candidates = []
    if SITE_NAME_RE.fullmatch(base):
        candidates.append(base)
    cs_prefixed = f"cs-{base}"
    if SITE_NAME_RE.fullmatch(cs_prefixed) and cs_prefixed not in candidates:
        candidates.append(cs_prefixed)
    hash6 = hashlib.sha256(base.encode("utf-8")).hexdigest()[:6]
    cs_hashed = f"cs-{base}-{hash6}"
    if SITE_NAME_RE.fullmatch(cs_hashed) and cs_hashed not in candidates:
        candidates.append(cs_hashed)
    return candidates


def find_site_by_name(name: str, credentials: dict[str, str]) -> dict[str, Any] | None:
    """Hledá existing site podle name. Vrátí site dict nebo None."""
    payload = run_netlify_cli(["sites:list", "--json"], credentials)
    sites = payload if isinstance(payload, list) else payload.get("sites", [])
    for site in sites:
        if site.get("name") == name:
            return site
    return None


# ─── Framework detection & build ──────────────────────────────────────────


def detect_framework(project_dir: Path) -> dict[str, Any]:
    """Detekce typu projektu z package.json + config souborů.

    Vrátí dict: {type, build_command, output_dir, ssr, needs_install}
    """
    package_json = project_dir / "package.json"

    # Vanilla HTML — bez package.json
    if not package_json.is_file():
        if (project_dir / "index.html").is_file():
            return {
                "type": "vanilla",
                "build_command": None,
                "output_dir": ".",
                "ssr": False,
                "needs_install": False,
            }
        raise NetlifyPublishError(
            f"Nenalezen package.json ani index.html v {project_dir}"
        )

    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise NetlifyPublishError(f"package.json není validní JSON: {exc}") from exc

    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    scripts = data.get("scripts", {})

    # Next.js
    if "next" in deps:
        # Detekuj static export z next.config
        ssr = _detect_next_ssr(project_dir)
        build_command = scripts.get("build", "next build")
        output_dir = ".next" if ssr else "out"
        return {
            "type": "nextjs-ssr" if ssr else "nextjs-static",
            "build_command": build_command,
            "output_dir": output_dir,
            "ssr": ssr,
            "needs_install": True,
        }

    # Vite
    if "vite" in deps:
        return {
            "type": "vite",
            "build_command": scripts.get("build", "vite build"),
            "output_dir": "dist",
            "ssr": False,
            "needs_install": True,
        }

    # Astro
    if "astro" in deps:
        return {
            "type": "astro",
            "build_command": scripts.get("build", "astro build"),
            "output_dir": "dist",
            "ssr": False,
            "needs_install": True,
        }

    # SvelteKit
    if "@sveltejs/kit" in deps:
        return {
            "type": "sveltekit",
            "build_command": scripts.get("build", "vite build"),
            "output_dir": "build",
            "ssr": True,
            "needs_install": True,
        }

    # Fallback — má package.json, ale neznámý framework
    if scripts.get("build"):
        return {
            "type": "unknown-with-build",
            "build_command": "npm run build",
            "output_dir": data.get("publishDir", "dist"),
            "ssr": False,
            "needs_install": True,
        }

    raise NetlifyPublishError(
        f"Neznámý framework v {project_dir}. Podporované: Next.js, Vite, Astro, SvelteKit, vanilla HTML."
    )


def _detect_next_ssr(project_dir: Path) -> bool:
    """True = Next.js SSR (potřebuje Functions), False = static export."""
    for config_name in ("next.config.js", "next.config.mjs", "next.config.ts"):
        config_path = project_dir / config_name
        if config_path.is_file():
            content = config_path.read_text(encoding="utf-8", errors="replace")
            if re.search(r"output\s*:\s*[\"']export[\"']", content):
                return False
    # Default Next.js (bez explicit output: export) = SSR
    return True


NPM_DEPRECATION_RE = re.compile(
    r"npm warn deprecated\s+([^@\s]+)@([^\s:]+):\s*(.+?)(?=\n(?:npm |$)|\Z)",
    re.DOTALL,
)

FRAMEWORK_CORE_PACKAGES = {
    "nextjs-static": ["next", "react", "react-dom", "tailwindcss"],
    "nextjs-ssr": ["next", "react", "react-dom", "tailwindcss"],
    "vite": ["vite", "tailwindcss"],
    "astro": ["astro", "tailwindcss"],
    "sveltekit": ["@sveltejs/kit", "vite", "tailwindcss"],
}


def parse_npm_deprecation_warnings(output: str) -> list[dict[str, str]]:
    """Extract `npm warn deprecated <pkg>@<ver>: <msg>` z npm install output."""
    seen: set[tuple[str, str]] = set()
    warnings: list[dict[str, str]] = []
    for match in NPM_DEPRECATION_RE.finditer(output or ""):
        name = match.group(1).strip()
        version = match.group(2).strip()
        key = (name, version)
        if key in seen:
            continue
        seen.add(key)
        message = " ".join(match.group(3).strip().split())
        warnings.append({"package": name, "version": version, "message": message})
    return warnings


def read_package_versions(project_dir: Path, packages: list[str]) -> dict[str, str]:
    """Načte aktuální verze daných packages z package.json."""
    package_json = project_dir / "package.json"
    if not package_json.is_file():
        return {pkg: "" for pkg in packages}
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {pkg: "" for pkg in packages}
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    return {pkg: deps.get(pkg, "") for pkg in packages}


def cleanup_build_artifacts(project_dir: Path, framework: dict[str, Any]) -> dict[str, int]:
    """Smaže node_modules + relevantní cache po buildu. Vrátí stats."""
    removed = {"node_modules": 0, "cache": 0}

    node_modules = project_dir / "node_modules"
    if node_modules.is_dir():
        size = _dir_size(node_modules)
        shutil.rmtree(node_modules, ignore_errors=True)
        removed["node_modules"] = size

    # Cache složky — smazat všechny kromě output dir
    output_dir = framework.get("output_dir", "")
    cache_candidates = [".turbo", ".parcel-cache", ".cache"]
    # Pro Next.js static smaž i .next (out/ stačí)
    if framework.get("type") == "nextjs-static":
        cache_candidates.append(".next")

    for cache_name in cache_candidates:
        if cache_name == output_dir:
            continue
        cache_path = project_dir / cache_name
        if cache_path.is_dir():
            removed["cache"] += _dir_size(cache_path)
            shutil.rmtree(cache_path, ignore_errors=True)

    return removed


def _dir_size(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total


# ─── Command handlers ─────────────────────────────────────────────────────


def command_test(args: argparse.Namespace) -> dict[str, Any]:
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]

    if site_id:
        payload = run_netlify_cli(
            ["api", "getSite", "--data", json.dumps({"site_id": site_id})], credentials
        )
        return {
            "ok": True,
            "siteId": payload.get("id") or site_id,
            "siteName": payload.get("name") or site_id,
            "url": payload.get("ssl_url") or payload.get("url") or "",
        }

    payload = run_netlify_cli(["sites:list", "--json"], credentials)
    if isinstance(payload, list):
        sites_visible = len(payload)
    elif isinstance(payload, dict) and isinstance(payload.get("sites"), list):
        sites_visible = len(payload["sites"])
    else:
        sites_visible = None
    return {"ok": True, "mode": "token", "sitesVisible": sites_visible}


def command_create_site(args: argparse.Namespace) -> dict[str, Any]:
    name = normalize_site_name(args.name or "")
    credentials = load_netlify_credentials()
    account_slug = (args.account_slug or credentials.get("account_slug") or "").strip()
    summary = {
        "ok": True,
        "dryRun": bool(args.dry_run),
        "name": name,
        "accountSlug": account_slug,
        "createdVia": DEFAULT_CREATED_VIA,
    }
    if args.dry_run:
        return summary

    if not args.confirm_create:
        raise NetlifyPublishError(
            "Vytvoření Netlify site vyžaduje --confirm-create po explicit klientově schválení"
        )

    command = ["sites:create", "--disable-linking", "--json"]
    if name:
        command.extend(["--name", name])
    if account_slug:
        command.extend(["--account-slug", account_slug])
    payload = run_netlify_cli(command, credentials)
    site_id = str(payload.get("id") or payload.get("site_id") or "")
    site_name = str(payload.get("name") or name or site_id)
    return {
        **summary,
        "siteId": site_id,
        "siteName": site_name,
        "url": payload.get("ssl_url") or payload.get("url") or "",
        "adminUrl": payload.get("admin_url") or "",
    }


def command_ensure_site(args: argparse.Namespace) -> dict[str, Any]:
    """Idempotent create-if-not-exists. Zkusí 3 kandidáty z deterministického slugu."""
    slug = normalize_slug(args.slug)
    candidates = generate_site_name_candidates(slug)
    if not candidates:
        raise NetlifyPublishError(f"Nelze vygenerovat platné site name z slugu {slug!r}")

    credentials = load_netlify_credentials()
    account_slug = (args.account_slug or credentials.get("account_slug") or "").strip()

    # Krok 1: zkus najít existing site podle prvního kandidáta
    for candidate in candidates:
        existing = find_site_by_name(candidate, credentials)
        if existing:
            return {
                "ok": True,
                "created": False,
                "siteId": existing.get("id") or existing.get("site_id"),
                "siteName": candidate,
                "url": existing.get("ssl_url") or existing.get("url") or "",
                "adminUrl": existing.get("admin_url") or "",
            }

    # Krok 2: žádný kandidát neexistuje pod tímto tokenem → vytvoř první
    last_error: Exception | None = None
    for candidate in candidates:
        try:
            command = [
                "sites:create",
                "--disable-linking",
                "--json",
                "--name",
                candidate,
            ]
            if account_slug:
                command.extend(["--account-slug", account_slug])
            payload = run_netlify_cli(command, credentials)
            site_id = str(payload.get("id") or payload.get("site_id") or "")
            return {
                "ok": True,
                "created": True,
                "siteId": site_id,
                "siteName": payload.get("name") or candidate,
                "url": payload.get("ssl_url") or payload.get("url") or "",
                "adminUrl": payload.get("admin_url") or "",
            }
        except NetlifyPublishError as exc:
            last_error = exc
            # Kolize s globálním Netlify namespace → zkus dalšího kandidáta
            if "already" in str(exc).lower() or "taken" in str(exc).lower():
                continue
            raise

    raise NetlifyPublishError(
        f"Žádný kandidát nešel vytvořit ({candidates}): {last_error}"
    )


def command_build(args: argparse.Namespace) -> dict[str, Any]:
    """Detekuj framework + npm install + build + cleanup. Vrátí cestu k output dir."""
    project_dir = resolve_project_dir(args.path)
    framework = detect_framework(project_dir)

    summary = {
        "ok": True,
        "path": str(project_dir),
        "framework": framework["type"],
        "ssr": framework["ssr"],
        "outputDir": str(project_dir / framework["output_dir"]) if framework["output_dir"] != "." else str(project_dir),
    }
    if args.dry_run:
        return {**summary, "dryRun": True, "skipped": "build (dry-run)"}

    # Vanilla — žádný build
    if not framework["needs_install"]:
        return {**summary, "built": False, "reason": "vanilla HTML — žádný build potřeba"}

    # npm install (BEZ --silent, ať vidíme deprecation warnings)
    rc, install_stdout, install_stderr = run_npm_command(
        ["install", "--no-audit", "--no-fund"],
        cwd=project_dir,
        timeout=NPM_INSTALL_TIMEOUT,
    )
    if rc != 0:
        tail = (install_stderr or install_stdout or "").strip().splitlines()[-20:]
        raise NetlifyPublishError(
            "npm install selhal:\n" + "\n".join(tail)
        )

    # Parser deprecation warnings (security CVE alerts, atd.)
    deprecation_warnings = parse_npm_deprecation_warnings(install_stdout + "\n" + install_stderr)

    # build
    build_cmd = framework["build_command"]
    if build_cmd.startswith("npm run "):
        npm_args = ["run", build_cmd.removeprefix("npm run ").strip()]
    elif build_cmd == "next build":
        npm_args = ["run", "build"]
    else:
        # custom command — fallback do `npm run build`
        npm_args = ["run", "build"]

    rc, stdout, stderr = run_npm_command(npm_args, cwd=project_dir, timeout=BUILD_TIMEOUT)
    if rc != 0:
        tail = (stderr or stdout or "").strip().splitlines()[-30:]
        raise NetlifyPublishError("Build selhal:\n" + "\n".join(tail))

    # Ověř, že output existuje
    output_path = project_dir / framework["output_dir"]
    if framework["output_dir"] != "." and not output_path.exists():
        raise NetlifyPublishError(
            f"Build neprodukoval očekávaný output: {output_path}"
        )

    # Cleanup
    cleanup_stats = {"node_modules": 0, "cache": 0}
    if not args.keep_cache:
        cleanup_stats = cleanup_build_artifacts(project_dir, framework)

    return {
        **summary,
        "built": True,
        "cleanup": {
            "nodeModulesBytes": cleanup_stats["node_modules"],
            "cacheBytes": cleanup_stats["cache"],
        },
        "deprecationWarnings": deprecation_warnings,
    }


def command_update_deps(args: argparse.Namespace) -> dict[str, Any]:
    """Aktualizuj framework dependencies na latest verze.

    Default (bez --major) = `npm update <pkg>` v rámci caret range (safe patches).
    S --major = `npm install <pkg>@latest` (může přijít breaking change).
    """
    project_dir = resolve_project_dir(args.path)
    framework = detect_framework(project_dir)

    if not framework.get("needs_install"):
        return {
            "ok": True,
            "skipped": "vanilla HTML — žádné npm dependencies k aktualizaci",
        }

    packages = FRAMEWORK_CORE_PACKAGES.get(framework["type"])
    if not packages:
        return {
            "ok": True,
            "skipped": f"framework {framework['type']} nemá známé core packages",
        }

    versions_before = read_package_versions(project_dir, packages)

    if args.dry_run:
        return {
            "ok": True,
            "dryRun": True,
            "path": str(project_dir),
            "framework": framework["type"],
            "mode": "major" if args.major else "patches",
            "packages": packages,
            "versionsBefore": versions_before,
        }

    if args.major:
        # `npm install <pkg>@latest` — překračuje caret range, můžou být breaking changes
        cmd = (
            ["install"]
            + [f"{pkg}@latest" for pkg in packages]
            + ["--no-audit", "--no-fund"]
        )
    else:
        # `npm update <pkg>` — jen v rámci semver range definovaného v package.json (safe)
        cmd = ["update"] + packages + ["--no-audit", "--no-fund"]

    rc, stdout, stderr = run_npm_command(cmd, cwd=project_dir, timeout=NPM_INSTALL_TIMEOUT)
    if rc != 0:
        tail = (stderr or stdout or "").strip().splitlines()[-20:]
        raise NetlifyPublishError(
            "npm update/install selhal:\n" + "\n".join(tail)
        )

    versions_after = read_package_versions(project_dir, packages)
    remaining_warnings = parse_npm_deprecation_warnings(stdout + "\n" + stderr)
    changed = {
        pkg: {"before": versions_before.get(pkg, ""), "after": versions_after.get(pkg, "")}
        for pkg in packages
        if versions_before.get(pkg) != versions_after.get(pkg)
    }

    return {
        "ok": True,
        "path": str(project_dir),
        "framework": framework["type"],
        "mode": "major" if args.major else "patches",
        "packages": packages,
        "versionsBefore": versions_before,
        "versionsAfter": versions_after,
        "changed": changed,
        "remainingDeprecationWarnings": remaining_warnings,
        "nextStep": "Spusť `build` + `deploy` pro novou verzi.",
    }


def command_deploy(args: argparse.Namespace) -> dict[str, Any]:
    """Deploy projekt (static nebo SSR). Default = production, --draft pro náhled.

    Smart safety: pokud site má custom doménu a klient nevyžádal --draft ani
    --force-prod, deploy se ZASTAVÍ a vrátí warning. Agent se má zeptat klienta,
    jestli chce náhled (--draft) nebo přepsat produkci (--force-prod).
    """
    project_dir = resolve_project_dir(args.path)

    # Detekuj framework, abychom věděli, kterou složku deployovat
    framework = detect_framework(project_dir)
    ssr = args.ssr or framework["ssr"]

    if ssr:
        # SSR: deploy projekt root, Netlify Runtime detekuje .next/
        deploy_dir = project_dir
        if not (project_dir / ".next").is_dir():
            raise NetlifyPublishError(
                "SSR deploy vyžaduje .next/ složku (nejdřív spusť `build`)"
            )
    else:
        # Static: deploy output_dir
        output_dir = project_dir / framework["output_dir"]
        deploy_dir = output_dir if framework["output_dir"] != "." else project_dir
        if not (deploy_dir / "index.html").is_file():
            raise NetlifyPublishError(
                f"Static deploy složka musí obsahovat index.html: {deploy_dir}"
            )

    # Bezpečnostní validace souborů
    files = collect_publish_files(deploy_dir)
    total_bytes = total_publish_bytes(files)

    # Default = production deploy. --draft je explicit opt-in.
    draft_mode = bool(args.draft)

    summary = {
        "ok": True,
        "path": str(deploy_dir),
        "framework": framework["type"],
        "ssr": ssr,
        "files": len(files),
        "bytes": total_bytes,
        "draft": draft_mode,
    }
    if args.dry_run:
        return {**summary, "dryRun": True}

    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not credentials.get("auth_token") or not site_id:
        raise NetlifyPublishError("NETLIFY_AUTH_TOKEN a site-id jsou vyžadovány")

    # Smart safety: production deploy na site s custom doménou vyžaduje
    # explicit potvrzení (--force-prod) nebo přepnutí na --draft.
    if not draft_mode and not args.force_prod:
        site_info = run_netlify_cli(
            ["api", "getSite", "--data", json.dumps({"site_id": site_id})], credentials
        )
        custom_domain = (site_info or {}).get("custom_domain")
        if custom_domain:
            raise NetlifyPublishError(
                f"Site má custom doménu '{custom_domain}'. Production deploy by "
                f"okamžitě přepsal živý web na vlastní doméně klienta. "
                f"Možnosti: (1) pro náhled spusť znovu s --draft, "
                f"(2) pro přepis produkce spusť znovu s --force-prod. "
                f"Doporučuj klientovi nejdřív náhled."
            )

    title = args.title or f"CC publish: {deploy_dir.name}"
    command = [
        "deploy",
        "--dir",
        str(deploy_dir),
        "--site",
        site_id,
        "--json",
        "--no-build",
        "--message",
        title,
    ]
    if not draft_mode:
        command.append("--prod")
    payload = run_netlify_cli(command, credentials)
    deploy_url = (
        payload.get("deploy_ssl_url")
        or payload.get("ssl_url")
        or payload.get("deploy_url")
        or payload.get("deployUrl")
        or payload.get("url")
        or ""
    )
    return {
        **summary,
        "dryRun": False,
        "siteId": payload.get("site_id") or payload.get("siteId") or site_id,
        "deployId": payload.get("id") or payload.get("deploy_id") or payload.get("deployId") or "",
        "state": payload.get("state") or "",
        "url": deploy_url,
        "adminUrl": payload.get("admin_url") or "",
    }


def command_promote(args: argparse.Namespace) -> dict[str, Any]:
    """Promote latest deploy do production přes API restoreSiteDeploy."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován pro promote")

    # Najdi poslední draft deploy
    payload = run_netlify_cli(
        ["api", "listSiteDeploys", "--data", json.dumps({"site_id": site_id, "per_page": 5})],
        credentials,
    )
    deploys = payload if isinstance(payload, list) else []
    latest_draft = next(
        (d for d in deploys if d.get("context") in ("deploy-preview", "branch-deploy") or not d.get("published_at")),
        None,
    )
    if not latest_draft:
        raise NetlifyPublishError("Žádný draft deploy nenalezen — nejprve spusť `deploy`")

    # Restore as production
    deploy_id = latest_draft.get("id")
    result = run_netlify_cli(
        ["api", "restoreSiteDeploy", "--data", json.dumps({"site_id": site_id, "deploy_id": deploy_id})],
        credentials,
    )
    return {
        "ok": True,
        "siteId": site_id,
        "promotedDeployId": deploy_id,
        "url": result.get("ssl_url") or result.get("url") or "",
        "state": result.get("state") or "",
    }


def command_rollback(args: argparse.Namespace) -> dict[str, Any]:
    """Rollback site na konkrétní předchozí deploy."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id or not args.deploy_id:
        raise NetlifyPublishError("--site-id a --deploy-id jsou vyžadovány")

    result = run_netlify_cli(
        ["api", "restoreSiteDeploy", "--data", json.dumps({"site_id": site_id, "deploy_id": args.deploy_id})],
        credentials,
    )
    return {
        "ok": True,
        "siteId": site_id,
        "restoredDeployId": args.deploy_id,
        "url": result.get("ssl_url") or result.get("url") or "",
        "state": result.get("state") or "",
    }


def command_list_deploys(args: argparse.Namespace) -> dict[str, Any]:
    """List recent deploys (pro rollback výběr)."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    limit = max(1, min(args.limit or 10, 50))
    payload = run_netlify_cli(
        ["api", "listSiteDeploys", "--data", json.dumps({"site_id": site_id, "per_page": limit})],
        credentials,
    )
    deploys = payload if isinstance(payload, list) else []
    simplified = [
        {
            "deployId": d.get("id"),
            "state": d.get("state"),
            "context": d.get("context"),
            "url": d.get("ssl_url") or d.get("url"),
            "createdAt": d.get("created_at"),
            "publishedAt": d.get("published_at"),
            "title": d.get("title") or d.get("commit_ref"),
        }
        for d in deploys
    ]
    return {"ok": True, "siteId": site_id, "count": len(simplified), "deploys": simplified}


def command_rename(args: argparse.Namespace) -> dict[str, Any]:
    """Rename Netlify site na nový pretty name."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    new_name = normalize_site_name(args.new_name)

    # Check kolize
    existing = find_site_by_name(new_name, credentials)
    if existing and existing.get("id") != site_id:
        candidates = generate_site_name_candidates(new_name)
        raise NetlifyPublishError(
            f"Site name {new_name!r} už existuje. Zkus alternativu: {candidates[1:]}"
        )

    result = run_netlify_cli(
        ["api", "updateSite", "--data", json.dumps({"site_id": site_id, "body": {"name": new_name}})],
        credentials,
    )
    return {
        "ok": True,
        "siteId": site_id,
        "newName": new_name,
        "url": result.get("ssl_url") or result.get("url") or "",
    }


def command_add_domain(args: argparse.Namespace) -> dict[str, Any]:
    """Připojí custom doménu k Netlify site."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    domain = validate_domain(args.domain)

    result = run_netlify_cli(
        [
            "api",
            "updateSite",
            "--data",
            json.dumps({"site_id": site_id, "body": {"custom_domain": domain}}),
        ],
        credentials,
    )
    return {
        "ok": True,
        "siteId": site_id,
        "domain": domain,
        "sslStatus": result.get("ssl_status") or "provisioning",
        "url": f"https://{domain}",
        "nextStep": "Zavolej `verify-domain` pro check SSL provisioning (poll max 5 min).",
    }


def command_verify_domain(args: argparse.Namespace) -> dict[str, Any]:
    """Poll SSL + DNS status custom domény. Max 5 min."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    domain = validate_domain(args.domain)
    deadline = time.time() + DNS_POLL_TIMEOUT

    last_status = "unknown"
    while time.time() < deadline:
        try:
            payload = run_netlify_cli(
                ["api", "getSite", "--data", json.dumps({"site_id": site_id})],
                credentials,
            )
            ssl_status = payload.get("ssl_status") or "unknown"
            last_status = ssl_status
            if ssl_status == "active":
                return {
                    "ok": True,
                    "siteId": site_id,
                    "domain": domain,
                    "sslStatus": "active",
                    "url": f"https://{domain}",
                }
        except NetlifyPublishError:
            pass
        time.sleep(DNS_POLL_INTERVAL)

    return {
        "ok": False,
        "siteId": site_id,
        "domain": domain,
        "sslStatus": last_status,
        "message": (
            "SSL provisioning trvá obvykle 5-30 minut, max 24h. "
            "Zkontroluj DNS záznam a zavolej `verify-domain` znovu za chvíli."
        ),
    }


def command_db_share(args: argparse.Namespace) -> dict[str, Any]:
    """Sdílení existing DB mezi sites — vezme DATABASE_URL z jednoho site a nastaví do dalšího.

    Hodí se pro sdílenou DB napříč dashboardovými sites (= cs-data sdílená pro N dashboardů).
    Pro plnou samostatnou DB nové aplikace použij db-init.
    """
    credentials = load_netlify_credentials()
    if not args.from_site_id or not args.to_site_id:
        raise NetlifyPublishError(
            "--from-site-id a --to-site-id jsou vyžadovány"
        )
    if args.from_site_id == args.to_site_id:
        raise NetlifyPublishError("--from-site-id a --to-site-id musí být odlišné")

    env_keys = [k.strip() for k in (args.keys or "DATABASE_URL").split(",") if k.strip()]
    if not env_keys:
        raise NetlifyPublishError("--keys nesmí být prázdný")

    # Načti env vars z source site
    source_env = run_netlify_cli(
        ["env:list", "--site", args.from_site_id, "--json"], credentials
    )
    source_map: dict[str, str] = {}
    if isinstance(source_env, list):
        for item in source_env:
            if isinstance(item, dict) and item.get("key"):
                # Hodnota přes API:
                #   `values` array s {context, value}, nebo přímo `value`.
                value = ""
                if "value" in item and item["value"]:
                    value = str(item["value"])
                elif "values" in item and isinstance(item["values"], list):
                    for v in item["values"]:
                        if isinstance(v, dict) and v.get("value"):
                            value = str(v["value"])
                            break
                source_map[item["key"]] = value
    elif isinstance(source_env, dict):
        for k, v in source_env.items():
            if isinstance(v, dict) and v.get("value"):
                source_map[k] = str(v["value"])
            else:
                source_map[k] = str(v) if v else ""

    # Pro každý požadovaný klíč: get value, set v target
    shared: list[str] = []
    missing: list[str] = []
    for key in env_keys:
        value = source_map.get(key)
        if not value:
            missing.append(key)
            continue
        set_netlify_env_var(args.to_site_id, key, value, credentials)
        shared.append(key)

    return {
        "ok": True,
        "fromSiteId": args.from_site_id,
        "toSiteId": args.to_site_id,
        "shared": shared,
        "missing": missing,
        "nextStep": (
            "Restart deploy target site, aby se nové env vars načetly: "
            "spusť `deploy` na target site."
        ),
    }


def command_db_init(args: argparse.Namespace) -> dict[str, Any]:
    """Init Netlify Database (Postgres powered by Neon) pro projekt."""
    project_dir = resolve_project_dir(args.path) if args.path else None
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    cwd = project_dir if project_dir else documents_root()
    payload = run_netlify_cli(
        ["database", "init", "--yes", "--json"],
        credentials,
        cwd=cwd,
    )
    return {
        "ok": True,
        "siteId": site_id,
        "dbUrl": payload.get("database_url") or payload.get("connection_string") or "",
        "provider": payload.get("provider") or "neon",
        "nextStep": "Connection string je v env vars projektu. Použij `netlify env:list` pro výpis.",
    }


def command_env_set(args: argparse.Namespace) -> dict[str, Any]:
    """Nastav jednu env var pro Netlify site."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")
    if not args.key:
        raise NetlifyPublishError("--key je vyžadován")
    if args.value is None:
        raise NetlifyPublishError("--value je vyžadován")

    set_netlify_env_var(site_id, args.key, args.value, credentials)
    return {"ok": True, "siteId": site_id, "key": args.key, "set": True}


def command_env_list(args: argparse.Namespace) -> dict[str, Any]:
    """List env var keys (BEZ hodnot — security)."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    payload = run_netlify_cli(["env:list", "--site", site_id, "--json"], credentials)
    keys: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and item.get("key"):
                keys.append({"key": item["key"], "scopes": item.get("scopes", [])})
    elif isinstance(payload, dict):
        for key, meta in payload.items():
            if isinstance(meta, dict):
                keys.append({"key": key, "scopes": meta.get("scopes", [])})
            else:
                keys.append({"key": key})
    return {"ok": True, "siteId": site_id, "count": len(keys), "keys": keys}


def command_env_unset(args: argparse.Namespace) -> dict[str, Any]:
    """Smaže env var pro Netlify site."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")
    if not args.key:
        raise NetlifyPublishError("--key je vyžadován")

    run_netlify_cli(
        ["env:unset", args.key, "--site", site_id, "--json"], credentials
    )
    return {"ok": True, "siteId": site_id, "key": args.key, "unset": True}


def command_sync_creds(args: argparse.Namespace) -> dict[str, Any]:
    """Sync klientovy credentials z Control Center do Netlify env vars."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    services = [s.strip() for s in (args.services or "").split(",") if s.strip()]
    if not services:
        services = list(SERVICE_CRED_HELPERS.keys())

    results: dict[str, Any] = {}
    for service in services:
        try:
            creds, field_mapping = load_service_credentials(service)
        except NetlifyPublishError as exc:
            results[service] = {"ok": False, "error": str(exc)}
            continue

        if not creds:
            results[service] = {
                "ok": False,
                "error": "Credentials nejsou v CC nakonfigurované (nebo cc_credentials helper chybí).",
            }
            continue

        set_keys: list[str] = []
        skipped_keys: list[str] = []
        for source_field, env_key in field_mapping.items():
            value = creds.get(source_field)
            if value:
                set_netlify_env_var(site_id, env_key, str(value), credentials)
                set_keys.append(env_key)
            else:
                skipped_keys.append(env_key)

        results[service] = {
            "ok": True,
            "set": set_keys,
            "skipped": skipped_keys,
        }

    return {"ok": True, "siteId": site_id, "services": results}


def command_identity_enable(args: argparse.Namespace) -> dict[str, Any]:
    """Aktivuje Netlify Identity (built-in auth) pro site."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    run_netlify_cli(
        ["api", "enableSiteIdentity", "--data", json.dumps({"site_id": site_id})],
        credentials,
    )
    return {
        "ok": True,
        "siteId": site_id,
        "identityEnabled": True,
        "nextStep": (
            "Do aplikace přidej netlify-identity-widget JS lib pro login UI. "
            "Doc: https://docs.netlify.com/manage/security/identity/"
        ),
    }


def command_trigger_refresh(args: argparse.Namespace) -> dict[str, Any]:
    """Spustí HTTP POST na klientovu refresh endpoint (= initial data load po deployi)."""
    import urllib.error
    import urllib.request

    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    # Najdi URL site
    payload = run_netlify_cli(
        ["api", "getSite", "--data", json.dumps({"site_id": site_id})], credentials
    )
    site_url = payload.get("ssl_url") or payload.get("url") or ""
    if not site_url:
        raise NetlifyPublishError("Site nemá URL — možná není ještě deployovaná")

    endpoint = (args.endpoint or "/api/refresh").strip()
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    full_url = site_url.rstrip("/") + endpoint

    headers = {"User-Agent": "cliqsales-netlify-publisher/1.0"}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    timeout = int(args.timeout or 120)
    req = urllib.request.Request(full_url, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310 (klient-controlled URL)
            status = response.status
            body = response.read(4096).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "url": full_url,
            "error": exc.reason,
        }
    except urllib.error.URLError as exc:
        raise NetlifyPublishError(f"Refresh request selhal: {exc.reason}") from exc

    return {
        "ok": status < 400,
        "status": status,
        "url": full_url,
        "body": body[:500],
    }


def command_list_sites(args: argparse.Namespace) -> dict[str, Any]:
    """List všech sites pod tokenem (klient inventory)."""
    credentials = load_netlify_credentials()
    payload = run_netlify_cli(["sites:list", "--json"], credentials)
    sites = payload if isinstance(payload, list) else payload.get("sites", [])
    simplified = [
        {
            "siteId": s.get("id") or s.get("site_id"),
            "name": s.get("name"),
            "url": s.get("ssl_url") or s.get("url"),
            "customDomain": s.get("custom_domain"),
            "createdAt": s.get("created_at"),
            "updatedAt": s.get("updated_at"),
        }
        for s in sites
    ]
    return {"ok": True, "count": len(simplified), "sites": simplified}


def command_delete_site(args: argparse.Namespace) -> dict[str, Any]:
    """Smaže Netlify site (destruktivní — vyžaduje --confirm-delete)."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    if not args.confirm_delete:
        raise NetlifyPublishError(
            "Smazání Netlify site vyžaduje --confirm-delete po explicit klientově schválení"
        )

    run_netlify_cli(
        ["api", "deleteSite", "--data", json.dumps({"site_id": site_id})],
        credentials,
    )
    return {"ok": True, "siteId": site_id, "deleted": True}


# ─── Argparse + main ──────────────────────────────────────────────────────


def print_result(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if payload.get("url"):
        print(payload["url"])
    else:
        print(json.dumps(payload, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Netlify publisher v1.0 — build, deploy, manage.")
    sub = parser.add_subparsers(dest="command", required=True)

    # test
    p = sub.add_parser("test", help="Ověř credentials a (optional) site")
    p.add_argument("--site-id", default="")
    p.add_argument("--json", action="store_true")

    # create-site (explicit, vyžaduje --confirm-create)
    p = sub.add_parser("create-site", help="Vytvoř Netlify site (vyžaduje --confirm-create)")
    p.add_argument("--name", default="")
    p.add_argument("--account-slug", default="")
    p.add_argument("--confirm-create", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")

    # ensure-site (idempotent)
    p = sub.add_parser("ensure-site", help="Idempotent create-if-not-exists podle slugu")
    p.add_argument("--slug", required=True)
    p.add_argument("--account-slug", default="")
    p.add_argument("--json", action="store_true")

    # build
    p = sub.add_parser("build", help="Detekuj framework + npm install + build + cleanup")
    p.add_argument("path", help="Cesta k projektu uvnitř /documents")
    p.add_argument("--keep-cache", action="store_true", help="Ponech node_modules + cache po buildu")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")

    # update-deps
    p = sub.add_parser(
        "update-deps",
        help="Update framework dependencies. Default = safe patches, --major = breaking-allowed",
    )
    p.add_argument("path", help="Cesta k projektu uvnitř /documents/sites/<slug>/")
    p.add_argument(
        "--major",
        action="store_true",
        help="Povol major version bumps (riziko breaking changes). Default = jen patches v rámci caret range.",
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")

    # deploy
    p = sub.add_parser(
        "deploy",
        help="Deploy projekt (default = production, --draft pro náhled)",
    )
    p.add_argument("path", help="Cesta k projektu uvnitř /documents/sites/<slug>/")
    p.add_argument("--site-id", default="")
    p.add_argument("--title", default="")
    p.add_argument(
        "--draft",
        action="store_true",
        help="Deploy jako preview/náhled. Bez tohoto flagu = production.",
    )
    p.add_argument(
        "--force-prod",
        action="store_true",
        help="Override custom-domain safety warning pro production deploy.",
    )
    p.add_argument("--ssr", action="store_true", help="Force SSR deploy (jinak auto-detect)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")

    # promote
    p = sub.add_parser("promote", help="Promote latest draft do produkce")
    p.add_argument("--site-id", default="")
    p.add_argument("--json", action="store_true")

    # rollback
    p = sub.add_parser("rollback", help="Rollback na konkrétní předchozí deploy")
    p.add_argument("--site-id", default="")
    p.add_argument("--deploy-id", required=True)
    p.add_argument("--json", action="store_true")

    # list-deploys
    p = sub.add_parser("list-deploys", help="List recent deploys (pro rollback)")
    p.add_argument("--site-id", default="")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--json", action="store_true")

    # rename
    p = sub.add_parser("rename", help="Rename site na pretty URL")
    p.add_argument("--site-id", default="")
    p.add_argument("--new-name", required=True)
    p.add_argument("--json", action="store_true")

    # add-domain
    p = sub.add_parser("add-domain", help="Připoj custom doménu k site")
    p.add_argument("--site-id", default="")
    p.add_argument("--domain", required=True)
    p.add_argument("--json", action="store_true")

    # verify-domain
    p = sub.add_parser("verify-domain", help="Poll SSL + DNS status (max 5 min)")
    p.add_argument("--site-id", default="")
    p.add_argument("--domain", required=True)
    p.add_argument("--json", action="store_true")

    # db-init
    p = sub.add_parser("db-init", help="Init Netlify Database pro projekt")
    p.add_argument("--site-id", default="")
    p.add_argument("--path", default="", help="Cesta k projektu (volitelné)")
    p.add_argument("--json", action="store_true")

    # db-share
    p = sub.add_parser(
        "db-share",
        help="Sdílení existing DB mezi sites (= cs-data sdílená přes dashboardy)",
    )
    p.add_argument("--from-site-id", required=True, help="Source site (= drží DB)")
    p.add_argument("--to-site-id", required=True, help="Target site (= připojí se k té DB)")
    p.add_argument(
        "--keys",
        default="DATABASE_URL",
        help="Comma-separated env vars k sdílení (default DATABASE_URL).",
    )
    p.add_argument("--json", action="store_true")

    # env-set
    p = sub.add_parser("env-set", help="Nastav env var pro site")
    p.add_argument("--site-id", default="")
    p.add_argument("--key", required=True)
    p.add_argument("--value", required=True)
    p.add_argument("--json", action="store_true")

    # env-list
    p = sub.add_parser("env-list", help="List env var keys (bez hodnot)")
    p.add_argument("--site-id", default="")
    p.add_argument("--json", action="store_true")

    # env-unset
    p = sub.add_parser("env-unset", help="Smaž env var pro site")
    p.add_argument("--site-id", default="")
    p.add_argument("--key", required=True)
    p.add_argument("--json", action="store_true")

    # sync-creds
    p = sub.add_parser(
        "sync-creds",
        help="Sync klientovy credentials z CC do Netlify env vars (Fakturoid, Meta, GA4, Fio, ...)",
    )
    p.add_argument("--site-id", default="")
    p.add_argument(
        "--services",
        default="",
        help="Comma-separated seznam services (fakturoid,meta,ga4,...). Default: vše dostupné.",
    )
    p.add_argument("--json", action="store_true")

    # identity-enable
    p = sub.add_parser("identity-enable", help="Aktivuj Netlify Identity (built-in auth)")
    p.add_argument("--site-id", default="")
    p.add_argument("--json", action="store_true")

    # trigger-refresh
    p = sub.add_parser(
        "trigger-refresh",
        help="HTTP POST na klientovu refresh endpoint (initial data load po deployi)",
    )
    p.add_argument("--site-id", default="")
    p.add_argument(
        "--endpoint",
        default="/api/refresh",
        help="Path k refresh endpointu (default: /api/refresh)",
    )
    p.add_argument(
        "--token",
        default="",
        help="Optional Bearer token pro auth na endpoint (např. CRON_SECRET)",
    )
    p.add_argument("--timeout", type=int, default=120, help="Request timeout v sekundách")
    p.add_argument("--json", action="store_true")

    # list-sites
    p = sub.add_parser("list-sites", help="List všech sites pod tokenem")
    p.add_argument("--json", action="store_true")

    # delete-site (destruktivní)
    p = sub.add_parser("delete-site", help="Smaž Netlify site (vyžaduje --confirm-delete)")
    p.add_argument("--site-id", default="")
    p.add_argument("--confirm-delete", action="store_true")
    p.add_argument("--json", action="store_true")

    return parser


COMMAND_DISPATCH = {
    "test": command_test,
    "create-site": command_create_site,
    "ensure-site": command_ensure_site,
    "build": command_build,
    "update-deps": command_update_deps,
    "deploy": command_deploy,
    "promote": command_promote,
    "rollback": command_rollback,
    "list-deploys": command_list_deploys,
    "rename": command_rename,
    "add-domain": command_add_domain,
    "verify-domain": command_verify_domain,
    "db-init": command_db_init,
    "db-share": command_db_share,
    "env-set": command_env_set,
    "env-list": command_env_list,
    "env-unset": command_env_unset,
    "sync-creds": command_sync_creds,
    "identity-enable": command_identity_enable,
    "trigger-refresh": command_trigger_refresh,
    "list-sites": command_list_sites,
    "delete-site": command_delete_site,
}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMAND_DISPATCH.get(args.command)
    if not handler:
        parser.error(f"Neznámý subcommand: {args.command}")
        return 2

    try:
        result = handler(args)
        print_result(result, bool(getattr(args, "json", False)))
        return 0
    except NetlifyPublishError as exc:
        payload = {"ok": False, "error": str(exc)}
        if bool(getattr(args, "json", False)):
            # --json mode: error JSON na stdout (= shell redirect ho zachytí),
            # human-readable message paralelně na stderr (pro logs / monitoring).
            # Bez tohoto by `> file.json` při chybě uložil 0-byte soubor.
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            print(f"ERROR: {exc}", file=sys.stderr)
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 65


if __name__ == "__main__":
    raise SystemExit(main())
