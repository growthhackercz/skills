#!/usr/bin/env python3
"""Netlify publisher v1.3.4 — bezpečný build, deploy, promote a rollback."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any


# ─── Konstanty ────────────────────────────────────────────────────────────

# Netlify bundluje i TypeScript funkce, takže report musí vidět i .ts/.mts —
# `rglob("*.*js")` je dřív mlčky zamlčel a vypadalo to, že funkce nejsou.
FUNCTION_SUFFIXES = {".js", ".mjs", ".cjs", ".ts", ".mts", ".cts"}
MAX_FILES = 5000
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024
NPM_INSTALL_TIMEOUT = 300  # 5 min
BUILD_TIMEOUT = 600  # 10 min
DNS_POLL_TIMEOUT = 300  # 5 min
DNS_POLL_INTERVAL = 15  # sekund
DEPLOY_URL_VERIFY_TIMEOUT = 45
DEPLOY_URL_VERIFY_INTERVAL = 3
DEFAULT_CREATED_VIA = "control-center-netlify-publisher"
SKILL_VERSION = "1.3.4"
STATE_VERSION = 2
NETLIFY_API_BASE = "https://api.netlify.com/api/v1"
SITE_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])$")
DOMAIN_RE = re.compile(r"^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

BLOCKED_DIR_NAMES = {
    ".git",
    ".netlify",
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
    ".npmrc",  # nese `//registry…:_authToken=` — do deploye nepatří
}
INTERNAL_FILE_NAMES = {".netlify-state.json", ".web-builder.json"}
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
    # ZIP import se instaluje do ~/.openclaw/user-skills/<slug>. Relativní
    # parents[2]/_lib tam proto nevede do distribuované knihovny cs-skills.
    # Kanonický runtime fallback musí fungovat i bez exportovaného
    # OPENCLAW_HOME (entrypoint jej historicky držel jen jako shell proměnnou).
    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
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


def load_custom_variable(name: str) -> str:
    """Resolve a named CC variable/SecretRef without accepting its value on argv."""
    normalized = (name or "").strip()
    if not ENV_KEY_RE.fullmatch(normalized):
        raise NetlifyPublishError(f"Neplatný název CC proměnné: {normalized!r}")

    candidates = []
    openclaw_home = os.environ.get("OPENCLAW_HOME") or os.environ.get("CC_OPENCLAW_HOME")
    if openclaw_home:
        candidates.append(Path(openclaw_home).expanduser() / "cs-skills" / "_lib")
    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
    candidates.append(Path(__file__).resolve().parents[2] / "_lib")
    for candidate in candidates:
        if candidate.exists():
            sys.path.insert(0, str(candidate))
            break
    try:
        from cc_credentials import get_variable  # type: ignore
    except ImportError as exc:
        raise NetlifyPublishError("CC credential resolver není dostupný") from exc

    value = str(get_variable(normalized) or "")
    if not value:
        raise NetlifyPublishError(
            f"CC proměnná {normalized} není nakonfigurovaná; žádná hodnota nebyla změněna"
        )
    return value


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
    if len(parts) != 1 or not SLUG_RE.fullmatch(parts[0]):
        raise NetlifyPublishError(
            f"Projekt musí být přesně /documents/sites/<slug>, ne jeho podsložka: {resolved}. "
            "Slug musí být lowercase alfanumerický s pomlčkami."
        )

    return resolved


def resolve_inside_project(project_dir: Path, raw: str, popis: str) -> Path:
    """Jediný resolver pro VŠECHNY cesty odvozené z projektu.

    Vznikl proto, že stejná díra byla dvakrát na dvou místech: složka funkcí
    z `netlify.toml` a publish složka z `package.json` → `publishDir`. Obojí
    šlo nasměrovat ven a publisher to nahrál na veřejný web.

    Pozor na past: `Path("/projekt") / "/etc"` vrátí `/etc` — absolutní pravá
    strana vyhraje. Proto se absolutní cesta odmítá dřív, než se skládá.
    """
    if not isinstance(raw, str):
        raise NetlifyPublishError(f"{popis} musí být řetězec, ne {type(raw).__name__}")
    hodnota = raw.strip()
    if not hodnota:
        raise NetlifyPublishError(f"{popis} je prázdný")
    if hodnota.startswith("~") or Path(hodnota).is_absolute():
        raise NetlifyPublishError(f"{popis} musí být relativní k projektu, ne {hodnota!r}")

    base = project_dir.resolve()
    declared = base / hodnota
    candidate = declared.resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        raise NetlifyPublishError(f"{popis} ukazuje mimo projekt: {hodnota!r}") from None

    # Symlink kdekoli v cestě — ne jen na konci. `out/` může být pravá složka,
    # ale `out/assets -> /cizi` už ne.
    krok = base
    for cast in Path(hodnota).parts:
        krok = krok / cast
        if krok.is_symlink():
            raise NetlifyPublishError(f"{popis} nesmí vést přes symlink: {hodnota!r}")
    return candidate


def resolve_publish_dir(value: str, require_index_html: bool = True) -> Path:
    """Validuje deploy složku (musí obsahovat index.html pro static)."""
    resolved = resolve_project_dir(value)

    if require_index_html and not (resolved / "index.html").is_file():
        raise NetlifyPublishError("Deploy složka musí obsahovat index.html")

    return resolved


def _open_lock_file(parent_parts: tuple[str, ...], lock_name: str, popis: str) -> int:
    """Create/open a lock below DOCUMENTS_PATH without following any symlink.

    A resolve-after-mkdir check is too late: an existing
    `/documents/platform -> /outside` link would already receive directories
    outside the trusted tree. Directory-fd traversal keeps every create/open
    relative to a parent opened with O_NOFOLLOW.
    """
    dir_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        parent_fd = os.open(documents_root(), dir_flags)
    except OSError as exc:
        raise NetlifyPublishError(f"Nelze otevřít DOCUMENTS_PATH pro {popis}") from exc

    try:
        for part in parent_parts:
            if not part or part in {".", ".."} or "/" in part or "\0" in part:
                raise NetlifyPublishError(f"Neplatná část lock cesty pro {popis}")
            try:
                os.mkdir(part, 0o700, dir_fd=parent_fd)
            except FileExistsError:
                pass
            try:
                child_fd = os.open(part, dir_flags, dir_fd=parent_fd)
            except OSError as exc:
                raise NetlifyPublishError(
                    f"Lock cesta pro {popis} obsahuje symlink nebo není složka"
                ) from exc
            os.close(parent_fd)
            parent_fd = child_fd

        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            return os.open(lock_name, flags, 0o600, dir_fd=parent_fd)
        except OSError as exc:
            raise NetlifyPublishError(f"Nelze otevřít {popis}") from exc
    finally:
        os.close(parent_fd)


@contextmanager
def project_operation_lock(project_dir: Path, operation: str):
    """Serialize a stateful Netlify operation for one exact project slug."""
    descriptor = _open_lock_file(
        ("platform", "netlify-publisher", project_dir.name),
        f".{operation}.lock",
        f"project lock pro {operation}",
    )

    timeout = max(1, int(os.environ.get("NETLIFY_PROJECT_LOCK_TIMEOUT_SECONDS") or "30"))
    deadline = time.monotonic() + timeout
    with os.fdopen(descriptor, "a+") as handle:
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise NetlifyPublishError(
                        f"Projekt {project_dir.name} už provádí {operation}; timeout po {timeout}s"
                    )
                time.sleep(0.1)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def site_operation_lock(site_id: str, operation: str):
    """Serialize a remote mutation for one exact Netlify site.

    Project locks alone are insufficient: two project folders may point at the
    same site. A rollback from one folder must not race a deploy/promote from
    another folder.
    """
    normalized_site_id = str(site_id or "").strip()
    if not normalized_site_id:
        raise NetlifyPublishError("Site lock vyžaduje přesné site ID")

    site_key = hashlib.sha256(normalized_site_id.encode("utf-8")).hexdigest()
    descriptor = _open_lock_file(
        ("platform", "netlify-publisher", ".site-locks"),
        f".{site_key}.{operation}.lock",
        f"site lock pro {operation}",
    )

    timeout = max(1, int(os.environ.get("NETLIFY_PROJECT_LOCK_TIMEOUT_SECONDS") or "30"))
    deadline = time.monotonic() + timeout
    with os.fdopen(descriptor, "a+") as handle:
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise NetlifyPublishError(
                        f"Site {normalized_site_id} už provádí {operation}; timeout po {timeout}s"
                    )
                time.sleep(0.1)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def ensure_site_operation_lock(slug: str, account_slug: str):
    """Serialize one deterministic ensure-site decision across local runs.

    Bez tohoto zámku mohly dva souběžné tasky oba dokončit lookup před prvním
    create. Druhý pak kolizi prvního kandidáta vyložil jako globálně zabraný
    název a založil zbytečný fallback site. Klíč zahrnuje account scope i slug;
    samotné hodnoty se do názvu souboru nepropíšou.
    """
    identity = f"{account_slug}\0{slug}".encode("utf-8")
    lock_key = hashlib.sha256(identity).hexdigest()
    descriptor = _open_lock_file(
        ("platform", "netlify-publisher", ".ensure-locks"),
        f".{lock_key}.lock",
        "ensure-site lock",
    )
    timeout = max(1, int(os.environ.get("NETLIFY_PROJECT_LOCK_TIMEOUT_SECONDS") or "30"))
    deadline = time.monotonic() + timeout
    with os.fdopen(descriptor, "a+") as handle:
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise NetlifyPublishError(
                        f"Ensure-site pro {slug!r} už běží; timeout po {timeout}s"
                    )
                time.sleep(0.1)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def publication_operation_locks(project_dir: Path, site_id: str):
    """Stable lock order shared by deploy, promote and rollback."""
    with project_operation_lock(project_dir, "publish"):
        with site_operation_lock(site_id, "publish"):
            yield


def verify_linked_site(project_dir: Path, expected_site_id: str) -> None:
    """Verify the state written by `netlify link` before a stateful command."""
    state_path = project_dir / ".netlify" / "state.json"
    try:
        state = json.loads(state_path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NetlifyPublishError(
            "Netlify link nevytvořil čitelný .netlify/state.json; database init se nespustil"
        ) from exc
    linked_site_id = str(state.get("siteId") or state.get("site_id") or "")
    if linked_site_id != expected_site_id:
        raise NetlifyPublishError(
            f"Netlify link ukazuje na jiný site ({linked_site_id or 'chybí'}); "
            "database init se nespustil"
        )


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
    """Walk deploy složky, validuje proti BLOCKED_* + size limity.

    ``os.walk(..., followlinks=False)`` samo o sobě nestačí: symlink na složku
    (včetně dangling odkazu) pouze tiše přeskočí. Preflight by pak tvrdil, že
    strom zkontroloval, i když v něm zůstala neověřená cesta. Proto kontroluj
    každou položku přes ``is_symlink()`` ještě před filtrováním adresářů.
    """
    if root.is_symlink():
        raise NetlifyPublishError(f"Kořen deploy scanu nesmí být symlink: {root}")
    if not root.is_dir():
        raise NetlifyPublishError(f"Kořen deploy scanu není složka: {root}")

    files: list[Path] = []
    for current_root, dirs, filenames in os.walk(root):
        current = Path(current_root)
        allowed_dirs: list[str] = []
        for dirname in sorted(dirs):
            path = current / dirname
            rel = path.relative_to(root)
            if path.is_symlink():
                raise NetlifyPublishError(
                    f"Symlinky nelze publikovat: {rel.as_posix()}"
                )
            if dirname in BLOCKED_DIR_NAMES or dirname.endswith(".egg-info"):
                continue
            allowed_dirs.append(dirname)
        dirs[:] = allowed_dirs

        for filename in sorted(filenames):
            path = current / filename
            rel = path.relative_to(root)
            # is_symlink() je True i pro dangling symlink; musí být před
            # is_file()/stat(), jinak by se odkaz mohl pouze tiše ztratit.
            if path.is_symlink():
                raise NetlifyPublishError(f"Symlinky nelze publikovat: {rel.as_posix()}")
            if filename.lower() in INTERNAL_FILE_NAMES:
                continue
            if is_blocked_file(path):
                raise NetlifyPublishError(
                    f"Blokovaný soubor v deploy složce: {rel.as_posix()}"
                )
            if not path.is_file():
                raise NetlifyPublishError(
                    f"Deploy strom obsahuje neověřitelnou položku: {rel.as_posix()}"
                )
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


def _file_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def publish_manifest_snapshot(
    root: Path, files: list[Path]
) -> dict[str, tuple[int, int, int, int, int]]:
    """Capture the exact identity of every validated public file."""
    snapshot: dict[str, tuple[int, int, int, int, int]] = {}
    for source in files:
        try:
            relative = source.relative_to(root)
            source_stat = source.lstat()
        except (OSError, ValueError) as exc:
            raise NetlifyPublishError(
                f"Deploy manifest nešel uzamknout na zdrojový soubor: {source} ({exc})"
            ) from exc
        key = relative.as_posix()
        if relative.is_absolute() or not relative.parts or any(
            part in {"", ".", ".."} for part in relative.parts
        ):
            raise NetlifyPublishError(f"Neplatná cesta v deploy manifestu: {key}")
        if key in snapshot:
            raise NetlifyPublishError(f"Duplicitní cesta v deploy manifestu: {key}")
        if not stat.S_ISREG(source_stat.st_mode):
            raise NetlifyPublishError(
                f"Deploy manifest obsahuje neobyčejný soubor: {key}"
            )
        snapshot[key] = _file_identity(source_stat)
    return snapshot


def _copy_publish_file(
    root_fd: int,
    relative: Path,
    destination: Path,
    expected_identity: tuple[int, int, int, int, int],
) -> int:
    """Copy one manifest entry without following source symlinks.

    The project can be modified while a deploy is starting. Resolve every
    source component relative to an already-open deploy-root descriptor, and
    reject symlinks again during the copy. The staging directory is private
    and created by us, so the Netlify CLI later sees exactly this snapshot.
    """
    if relative.is_absolute() or not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise NetlifyPublishError(
            f"Neplatná cesta v deploy manifestu: {relative.as_posix()}"
        )

    directory_fd = os.dup(root_fd)
    source_fd: int | None = None
    try:
        for part in relative.parts[:-1]:
            next_fd = os.open(
                part,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = next_fd
        source_fd = os.open(
            relative.name,
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
            dir_fd=directory_fd,
        )
        source_stat = os.fstat(source_fd)
        if not stat.S_ISREG(source_stat.st_mode):
            raise NetlifyPublishError(
                f"Deploy manifest obsahuje neobyčejný soubor: {relative.as_posix()}"
            )
        if _file_identity(source_stat) != expected_identity:
            raise NetlifyPublishError(
                f"Soubor se před přípravou deploye změnil: {relative.as_posix()}"
            )
        if source_stat.st_size > MAX_FILE_BYTES:
            raise NetlifyPublishError(
                f"Soubor je příliš velký (>50 MB): {relative.as_posix()}"
            )

        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        destination_fd = os.open(
            destination,
            os.O_CREAT
            | os.O_EXCL
            | os.O_WRONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
        copied = 0
        try:
            while True:
                chunk = os.read(source_fd, 1024 * 1024)
                if not chunk:
                    break
                view = memoryview(chunk)
                while view:
                    written = os.write(destination_fd, view)
                    if written <= 0:
                        raise OSError("zápis staging souboru vrátil nulu")
                    copied += written
                    view = view[written:]
            os.fsync(destination_fd)
        finally:
            os.close(destination_fd)

        after_stat = os.fstat(source_fd)
        if copied != source_stat.st_size or _file_identity(after_stat) != expected_identity:
            raise NetlifyPublishError(
                f"Soubor se během přípravy deploye změnil: {relative.as_posix()}"
            )
        return copied
    except (OSError, ValueError) as exc:
        raise NetlifyPublishError(
            f"Deploy soubor nešel bezpečně zkopírovat: {relative.as_posix()} ({exc})"
        ) from exc
    finally:
        if source_fd is not None:
            os.close(source_fd)
        os.close(directory_fd)


@contextmanager
def static_publish_staging(
    root: Path, expected_manifest: dict[str, tuple[int, int, int, int, int]]
):
    """Yield a private tree containing exactly the validated static manifest.

    Passing the original output directory to ``netlify deploy --dir`` would
    make scanner exclusions cosmetic: the CLI would still upload ignored CC
    metadata from a vanilla project whose output is the project root.
    """
    root_fd = os.open(
        root,
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        temp_raw = tempfile.mkdtemp(prefix="cc-netlify-static-")
        os.chmod(temp_raw, 0o700)
        try:
            # Re-scan inside the publication lock. Any change in membership or
            # inode/timestamps since the preflight aborts before Netlify runs.
            current_files = collect_publish_files(root)
            current_manifest = publish_manifest_snapshot(root, current_files)
            if current_manifest != expected_manifest:
                raise NetlifyPublishError(
                    "Publish strom se mezi kontrolou a deployem změnil; spusť deploy znovu"
                )

            work = Path(temp_raw) / "publish.work"
            staging = Path(temp_raw) / "publish"
            work.mkdir(mode=0o700)
            copied_total = 0
            for key in sorted(current_manifest):
                relative = Path(key)
                copied_total += _copy_publish_file(
                    root_fd,
                    relative,
                    work / relative,
                    current_manifest[key],
                )
                if copied_total > MAX_TOTAL_BYTES:
                    raise NetlifyPublishError("Deploy složka je větší než 100 MB")
            if not (work / "index.html").is_file():
                raise NetlifyPublishError("Připravený static deploy neobsahuje index.html")
            work.rename(staging)
            yield staging
        finally:
            # A cleanup problem must never replace the truthful result of a
            # remote deploy (which would invite a duplicate retry). The tree
            # contains public bytes only, lives in private /tmp and will be
            # reclaimed by ordinary temp cleanup if this best-effort removal
            # cannot finish.
            try:
                shutil.rmtree(temp_raw)
            except OSError:
                pass
    finally:
        os.close(root_fd)


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


@contextmanager
def protected_netlify_environment(token: str):
    """Yield a minimal CLI environment with credential-scrubbing PM shims.

    Netlify Build applies ``[build.environment]`` to build commands and plugin
    hooks, but CLI 26 auto-installs a missing framework plugin *before* that
    child environment exists. Missing plugins use ``npm``; a local plugin with
    ``yarn.lock`` uses ``yarn``. Both would otherwise inherit the parent PAT.
    Private PATH shims strip only the deploy credential while the Netlify
    parent keeps it for API/upload calls.
    """
    if not token:
        raise NetlifyPublishError("NETLIFY_AUTH_TOKEN je vyžadován")
    package_managers = {"npm": npm_cli()}
    for manager in ("yarn",):
        resolved = shutil.which(manager)
        if resolved:
            package_managers[manager] = resolved
    env = build_environment()
    env["NETLIFY_AUTH_TOKEN"] = token
    env["NETLIFY_TELEMETRY_DISABLED"] = "1"

    with tempfile.TemporaryDirectory(prefix="cc-netlify-npm-") as shim_dir_raw:
        shim_dir = Path(shim_dir_raw)
        for manager, real_manager in package_managers.items():
            shim_path = shim_dir / manager
            source = (
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                "child_env = dict(os.environ)\n"
                "child_env.pop('NETLIFY_AUTH_TOKEN', None)\n"
                f"real_manager = {str(real_manager)!r}\n"
                "os.execve(real_manager, [real_manager, *sys.argv[1:]], child_env)\n"
            ).encode("utf-8")
            descriptor = os.open(
                shim_path,
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                0o700,
            )
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(source)
                handle.flush()
                os.fsync(handle.fileno())
        env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', '')}"
        yield env


def run_netlify_cli(
    args: list[str],
    credentials: dict[str, str],
    cwd: Path | None = None,
    *,
    sensitive_output: bool = False,
) -> Any:
    token = credentials.get("auth_token", "")
    if not token:
        raise NetlifyPublishError("NETLIFY_AUTH_TOKEN je vyžadován")

    work_dir = cwd or documents_root()
    timeout = int(os.environ.get("NETLIFY_CLI_TIMEOUT_SECONDS") or "600")
    try:
        # CLI parent má PAT pro API/upload. Package-manager děti jej díky PATH
        # shimům ztratí ještě před plugin auto-install i projektovým buildem.
        with protected_netlify_environment(token) as env:
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
        if sensitive_output:
            command_name = " ".join(args[:2]) or "command"
            raise NetlifyPublishError(
                f"Netlify CLI příkaz '{command_name}' selhal "
                f"(exit code {completed.returncode}); výstup byl skryt, protože může obsahovat tajné údaje"
            )
        stderr = sanitize_cli_output(completed.stderr, token)
        stdout = sanitize_cli_output(completed.stdout, token)
        detail = redact(stderr or stdout or f"exit code {completed.returncode}")
        raise NetlifyPublishError(f"Netlify CLI selhal: {detail}")

    return parse_cli_json(completed.stdout)


def run_netlify_cli_text(
    args: list[str], credentials: dict[str, str], cwd: Path | None = None
) -> None:
    """Run a Netlify CLI command that has no JSON mode without exposing output.

    Some successful text commands print generated credentials or connection
    strings. Their stdout/stderr must therefore never become agent output.
    """
    token = credentials.get("auth_token", "")
    if not token:
        raise NetlifyPublishError("NETLIFY_AUTH_TOKEN je vyžadován")

    work_dir = cwd or documents_root()
    timeout = int(os.environ.get("NETLIFY_CLI_TIMEOUT_SECONDS") or "600")
    try:
        with protected_netlify_environment(token) as env:
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
        command_name = " ".join(args[:2]) or "command"
        raise NetlifyPublishError(
            f"Netlify CLI příkaz '{command_name}' selhal "
            f"(exit code {completed.returncode}); výstup byl skryt, protože může obsahovat tajné údaje"
        )


def run_netlify_api(
    method: str,
    resource: str,
    credentials: dict[str, str],
    *,
    query: dict[str, str] | None = None,
    payload: Any | None = None,
    allow_not_found: bool = False,
) -> Any | None:
    """Call Netlify API with secrets in headers/body, never in process argv.

    Error bodies are deliberately not surfaced because mutation responses can
    echo submitted environment values.
    """
    token = credentials.get("auth_token", "")
    if not token:
        raise NetlifyPublishError("NETLIFY_AUTH_TOKEN je vyžadován")

    url = f"{NETLIFY_API_BASE}/{resource.lstrip('/')}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "cliqsales-netlify-publisher/1.3.4",
        },
        method=method,
    )
    timeout = int(os.environ.get("NETLIFY_API_TIMEOUT_SECONDS") or "60")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        if allow_not_found and exc.code == 404:
            return None
        raise NetlifyPublishError(
            f"Netlify API {method} selhalo (HTTP {exc.code}); odpověď byla skryta, "
            "protože může obsahovat tajné údaje"
        ) from None
    except urllib.error.URLError as exc:
        raise NetlifyPublishError(f"Netlify API {method} není dostupné: {exc.reason}") from None

    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


SECRET_NAME_MARKERS = ("TOKEN", "KEY", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL", "_PAT")
# Co build skutečně potřebuje. Všechno ostatní z prostředí se mu NEPŘEDÁVÁ.
BUILD_ENV_ALLOWLIST = (
    "PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TMPDIR", "TEMP", "TMP",
    "SHELL", "TERM", "USER", "LOGNAME", "SYSTEMROOT", "COMSPEC",
    "NODE_ENV", "NODE_OPTIONS", "NODE_PATH", "XDG_CACHE_HOME", "npm_config_cache",
)


def secret_env_values() -> list[str]:
    """Hodnoty proměnných, které vypadají jako tajemství — pro začernění výpisů."""
    out = []
    for name, value in os.environ.items():
        if value and len(value) >= 8 and any(m in name.upper() for m in SECRET_NAME_MARKERS):
            out.append(value)
    return sorted(set(out), key=len, reverse=True)


def redact(text: str) -> str:
    """Začerní tajemství v diagnostice.

    Chybový výpis z buildu i z CLI se vrací uživateli a končí v logu. Bez
    tohohle filtru mohl token vypadnout doslova do chybové hlášky.
    """
    if not text:
        return text
    for value in secret_env_values():
        text = text.replace(value, "«skryto»")
    return text


def build_environment() -> dict[str, str]:
    """Prostředí pro npm — allowlist, ne kopie celého procesu.

    `os.environ.copy()` předával každému build skriptu (i z cizích balíčků
    ve stromu závislostí) NETLIFY_AUTH_TOKEN, FAL_KEY, CC_API_KEY a další.
    Jeden škodlivý balíček mezi stovkami závislostí by je odnesl pryč.
    """
    env = {name: os.environ[name] for name in BUILD_ENV_ALLOWLIST if name in os.environ}
    env.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    env["CI"] = "1"
    env["NPM_CONFIG_FUND"] = "false"
    env["NPM_CONFIG_AUDIT"] = "false"
    env["NPM_CONFIG_UPDATE_NOTIFIER"] = "false"
    # Build nesmí sáhnout na registry token uživatele.
    env["NPM_CONFIG_USERCONFIG"] = os.devnull
    return env


def run_npm_command(args: list[str], cwd: Path, timeout: int) -> tuple[int, str, str]:
    """Vrátí (returncode, stdout, stderr) — npm jednorázový command."""
    env = build_environment()

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

    return completed.returncode, redact(completed.stdout), redact(completed.stderr)


def ensure_next_binary_executable(project_dir: Path, framework: dict[str, Any]) -> None:
    """Repair the exact Next CLI mode after install, without invoking a shell.

    Some transferred/generated projects preserve the file but lose its execute
    bits. `npm run build` then fails with `next: Permission denied`. Only the
    known Next binary inside this exact project may be changed.
    """
    if framework.get("type") not in {"nextjs-static", "nextjs-ssr"}:
        return
    relative = "node_modules/next/dist/bin/next"
    binary = resolve_inside_project(project_dir, relative, "Next.js build binárka")
    if binary.is_symlink() or not binary.is_file():
        raise NetlifyPublishError(
            "npm install nevytvořil běžný soubor node_modules/next/dist/bin/next"
        )
    try:
        binary.chmod(binary.stat().st_mode | 0o111)
    except OSError as exc:
        raise NetlifyPublishError("Next.js build binárce nelze bezpečně nastavit spuštění") from exc


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


def stable_site_url(site: dict[str, Any]) -> str:
    """Return the stable production URL from a Netlify site object."""
    url = str(site.get("ssl_url") or site.get("url") or "").strip()
    if url:
        return url
    name = normalize_site_name(str(site.get("name") or ""))
    return f"https://{name}.netlify.app" if name else ""


def deploy_url_identity(value: Any) -> str:
    """Normalize only HTTP(S) scheme/trailing slash for exact deploy URL comparison."""
    raw = str(value or "").strip()
    try:
        parsed = urllib.parse.urlsplit(raw)
    except ValueError:
        return ""
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return ""
    path = parsed.path.rstrip("/")
    return f"{parsed.netloc.lower()}{path}"


def set_netlify_env_var(
    site_id: str, key: str, value: str, credentials: dict[str, str]
) -> bool:
    """Create/update a write-only Netlify secret without putting it in argv."""
    if not value:
        return False
    if not ENV_KEY_RE.fullmatch(key):
        raise NetlifyPublishError(f"Neplatný název env proměnné: {key!r}")

    site = run_netlify_cli(
        ["api", "getSite", "--data", json.dumps({"site_id": site_id})],
        credentials,
    )
    account_id = str(
        site.get("account_id")
        or site.get("account_slug")
        or credentials.get("account_slug")
        or ""
    ).strip()
    if not account_id:
        raise NetlifyPublishError(
            "Netlify site nevrátil account_id/account_slug; env secret nebyl změněn"
        )

    account = urllib.parse.quote(account_id, safe="")
    encoded_key = urllib.parse.quote(key, safe="")
    query = {"site_id": site_id}
    env_var = {
        "key": key,
        "values": [{"context": "all", "value": str(value)}],
        "is_secret": True,
    }
    existing = run_netlify_api(
        "GET",
        f"accounts/{account}/env/{encoded_key}",
        credentials,
        query=query,
        allow_not_found=True,
    )
    if existing is None:
        run_netlify_api(
            "POST",
            f"accounts/{account}/env",
            credentials,
            query=query,
            payload=[env_var],
        )
    else:
        run_netlify_api(
            "PUT",
            f"accounts/{account}/env/{encoded_key}",
            credentials,
            query=query,
            payload=env_var,
        )
    return True


def generate_site_name_candidates(slug: str) -> list[str]:
    """Vrátí tři různé deterministické kandidáty, každý validní pro Netlify."""
    base = normalize_slug(slug)
    hash6 = hashlib.sha256(base.encode("utf-8")).hexdigest()[:6]

    def fit(prefix: str, suffix: str = "") -> str:
        max_core = 63 - len(prefix) - len(suffix)
        core = base[:max_core].rstrip("-")
        return f"{prefix}{core}{suffix}"

    # U dlouhého slugu se prefixed/hash varianty bezpečně zkrátí. U 1–2znakového
    # slugu je raw base pro Netlify příliš krátká, proto pořadí doplní `cc-`
    # fallback. Pro každý validní projektový slug tak skutečně existují 3 pokusy.
    proposed = [
        base,
        fit("cs-"),
        fit("cs-", f"-{hash6}"),
        fit("cc-"),
        fit("cc-", f"-{hash6}"),
    ]
    candidates: list[str] = []
    for candidate in proposed:
        if SITE_NAME_RE.fullmatch(candidate) and candidate not in candidates:
            candidates.append(candidate)
        if len(candidates) == 3:
            break
    if len(candidates) != 3:
        raise NetlifyPublishError(f"Pro slug {slug!r} nelze odvodit tři bezpečné názvy site")
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


def read_package_manifest(project_dir: Path) -> dict[str, Any]:
    """Načti package.json a ověř tvary polí, která publisher používá."""
    package_json = project_dir / "package.json"
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NetlifyPublishError(f"package.json nelze přečíst jako JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise NetlifyPublishError("package.json musí obsahovat JSON objekt")

    for section_name in ("dependencies", "devDependencies", "scripts"):
        section = data.get(section_name, {})
        if not isinstance(section, dict):
            raise NetlifyPublishError(
                f"package.json → {section_name} musí být JSON objekt"
            )
        for key, value in section.items():
            if not isinstance(value, str):
                raise NetlifyPublishError(
                    f"package.json → {section_name}.{key} musí být text"
                )

    if "publishDir" in data:
        publish_dir = data["publishDir"]
        if not isinstance(publish_dir, str) or not publish_dir.strip():
            raise NetlifyPublishError("package.json → publishDir musí být neprázdný text")
    return data


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

    data = read_package_manifest(project_dir)
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
        output_dir = data.get("publishDir", "dist")
        # Platí i v dry-runu: unsafe output path není platný plán.
        resolve_inside_project(project_dir, output_dir, "publish složka (publishDir)")
        return {
            "type": "unknown-with-build",
            "build_command": "npm run build",
            "output_dir": output_dir,
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

PATCH_BASE_VERSION_RE = re.compile(
    r"^(?:[~^])?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


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
    data = read_package_manifest(project_dir)
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

    result: dict[str, str] = {}
    for package in packages:
        value = deps.get(package, "")
        result[package] = value
    return result


def patch_install_specs(versions: dict[str, str]) -> list[str]:
    """Připrav npm specs omezené na patch řadu deklarované verze."""
    specs: list[str] = []
    for package, raw_version in versions.items():
        version = raw_version.strip() if isinstance(raw_version, str) else ""
        match = PATCH_BASE_VERSION_RE.fullmatch(version)
        if not match:
            raise NetlifyPublishError(
                f"Balík {package!r} má rozsah {raw_version!r}; bezpečný patch update "
                "podporuje jen X.Y.Z, ^X.Y.Z nebo ~X.Y.Z. Pro jiný rozsah "
                "uprav package.json ručně a znovu spusť build."
            )
        major, minor, patch = match.groups()
        specs.append(f"{package}@~{major}.{minor}.{patch}")
    return specs


def _functions_directory_from_toml(text: str) -> str | None:
    """Hodnota `[functions].directory` z netlify.toml, nebo None.

    Čte sekci, ne celý soubor. Původní regex přes celý text přetékal do jiných
    sekcí: `[functions]` bez `directory` a někde níž `[dev] directory = "public"`
    vrátilo `public` a publisher nasadil `public/` jako funkce.
    """
    try:
        import tomllib
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

    if tomllib is not None:
        try:
            data = tomllib.loads(text)
        except Exception as exc:  # noqa: BLE001 — chceme srozumitelnou hlášku
            raise NetlifyPublishError(f"netlify.toml nejde přečíst: {exc}") from exc
        section = data.get("functions")
        if section is None:
            return None
        if not isinstance(section, dict):
            raise NetlifyPublishError("[functions] v netlify.toml musí být tabulka")

        def has_included_files(value: Any) -> bool:
            if not isinstance(value, dict):
                return False
            return "included_files" in value or any(
                has_included_files(child) for child in value.values()
            )

        if has_included_files(section):
            raise NetlifyPublishError(
                "netlify.toml: functions.included_files není podporované; může přibalit "
                "soubory mimo ověřenou functions složku"
            )
        if "directory" not in section:
            return None
        value = section["directory"]
        if not isinstance(value, str):
            raise NetlifyPublishError("[functions].directory v netlify.toml musí být řetězec")
        return value

    # Python < 3.11: ruční čtení omezené výhradně na sekci [functions].
    current: str | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            continue
        if not (current == "functions" or (current or "").startswith("functions.")) \
                or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == "included_files":
            raise NetlifyPublishError(
                "netlify.toml: functions.included_files není podporované; může přibalit "
                "soubory mimo ověřenou functions složku"
            )
        if current != "functions":
            continue
        if key.strip() != "directory":
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            return value[1:-1]
        raise NetlifyPublishError("[functions].directory v netlify.toml musí být řetězec")
    return None


DIRECT_DEPLOY_SUCCESS_STATE = "ready"
RESTORE_SUCCESS_STATE = "current"


def _response_deploy_id(payload: dict[str, Any]) -> str:
    return str(payload.get("id") or payload.get("deploy_id") or payload.get("deployId") or "").strip()


def _response_site_id(payload: dict[str, Any]) -> str:
    return str(payload.get("site_id") or payload.get("siteId") or "").strip()


def _authoritative_site_deploy(
    site_id: str,
    deploy_id: str,
    credentials: dict[str, str],
) -> dict[str, Any]:
    """Fetch one deploy from a site-scoped authoritative listing."""
    payload = run_netlify_cli(
        [
            "api",
            "listSiteDeploys",
            "--data",
            json.dumps({"site_id": site_id, "per_page": 100}),
        ],
        credentials,
    )
    deploys = payload if isinstance(payload, list) else []
    match = next(
        (item for item in deploys if isinstance(item, dict) and _response_deploy_id(item) == deploy_id),
        None,
    )
    if not match:
        raise NetlifyPublishError(
            f"Autoritativní kontrola nenašla deploy {deploy_id} na site {site_id}; "
            "lokální stav nebyl změněn"
        )
    returned_site = _response_site_id(match)
    if returned_site and returned_site != site_id:
        raise NetlifyPublishError(
            f"Autoritativní deploy odpověď patří jinému site ({returned_site} místo {site_id})"
        )
    return match


def validate_direct_deploy_result(
    payload: Any,
    expected_site_id: str,
    credentials: dict[str, str],
) -> str:
    """Validate `netlify deploy`: its terminal success state is `ready`.

    A response without an exact site binding is not trusted. In that case a
    site-scoped deploy listing must independently bind the returned deploy ID
    to the requested site before any local state is written.
    """
    if not isinstance(payload, dict):
        raise NetlifyPublishError("Deploy: Netlify nevrátilo JSON objekt")
    deploy_id = _response_deploy_id(payload)
    if not deploy_id:
        raise NetlifyPublishError("Deploy: Netlify nevrátilo deploy ID; stav nebyl změněn")

    state = str(payload.get("state") or "").strip().lower()
    returned_site = _response_site_id(payload)
    if state and state != DIRECT_DEPLOY_SUCCESS_STATE:
        reason = redact(str(payload.get("error_message") or payload.get("summary") or ""))
        raise NetlifyPublishError(
            f"Deploy: Netlify vrátilo stav {state!r}, očekáváno "
            f"{DIRECT_DEPLOY_SUCCESS_STATE!r}."
            + (f" Důvod: {reason}" if reason else "")
            + " Lokální stav nebyl změněn."
        )
    if returned_site and returned_site != expected_site_id:
        raise NetlifyPublishError(
            f"Deploy: odpověď patří jinému site ({returned_site} místo {expected_site_id}); "
            "lokální stav nebyl změněn"
        )
    if state == DIRECT_DEPLOY_SUCCESS_STATE and returned_site == expected_site_id:
        return deploy_id

    authoritative = _authoritative_site_deploy(expected_site_id, deploy_id, credentials)
    authoritative_state = str(authoritative.get("state") or "").strip().lower()
    if authoritative_state != DIRECT_DEPLOY_SUCCESS_STATE:
        raise NetlifyPublishError(
            f"Deploy: autoritativní stav je {authoritative_state or 'bez stavu'!r}, "
            f"očekáváno {DIRECT_DEPLOY_SUCCESS_STATE!r}; lokální stav nebyl změněn"
        )
    return deploy_id


def validate_restore_result(
    payload: Any,
    operation: str,
    expected_site_id: str,
    expected_deploy_id: str,
    credentials: dict[str, str],
) -> str:
    """Validate `restoreSiteDeploy`: its terminal success state is `current`.

    If Netlify omits response binding fields, `getSite` must prove that the
    exact requested deploy is now the site's published deploy. Explicitly
    conflicting fields never get papered over by a follow-up.
    """
    if not isinstance(payload, dict):
        raise NetlifyPublishError(f"{operation}: Netlify nevrátilo JSON objekt")
    state = str(payload.get("state") or "").strip().lower()
    returned_site = _response_site_id(payload)
    returned_deploy = _response_deploy_id(payload)

    if state and state != RESTORE_SUCCESS_STATE:
        raise NetlifyPublishError(
            f"{operation}: Netlify restore vrátilo stav {state!r}, očekáváno "
            f"{RESTORE_SUCCESS_STATE!r}; lokální stav nebyl změněn"
        )
    if returned_site and returned_site != expected_site_id:
        raise NetlifyPublishError(
            f"{operation}: restore odpověď patří jinému site "
            f"({returned_site} místo {expected_site_id})"
        )
    if returned_deploy and returned_deploy != expected_deploy_id:
        raise NetlifyPublishError(
            f"{operation}: restore přepnul jiný deploy "
            f"({returned_deploy} místo {expected_deploy_id})"
        )
    if (
        state == RESTORE_SUCCESS_STATE
        and returned_site == expected_site_id
        and returned_deploy == expected_deploy_id
    ):
        return expected_deploy_id

    site_payload = run_netlify_cli(
        ["api", "getSite", "--data", json.dumps({"site_id": expected_site_id})],
        credentials,
    )
    if not isinstance(site_payload, dict):
        raise NetlifyPublishError(f"{operation}: autoritativní getSite nevrátil JSON objekt")
    authoritative_site = _response_site_id(site_payload) or str(site_payload.get("id") or "").strip()
    if authoritative_site and authoritative_site != expected_site_id:
        raise NetlifyPublishError(
            f"{operation}: autoritativní getSite patří jinému site "
            f"({authoritative_site} místo {expected_site_id})"
        )
    published = site_payload.get("published_deploy")
    if isinstance(published, dict):
        published_id = _response_deploy_id(published)
    else:
        published_id = str(
            site_payload.get("published_deploy_id") or site_payload.get("publishedDeployId") or ""
        ).strip()
    if published_id != expected_deploy_id:
        raise NetlifyPublishError(
            f"{operation}: autoritativní getSite nepotvrdil deploy {expected_deploy_id} "
            "jako aktuální produkci; lokální stav nebyl změněn"
        )
    return expected_deploy_id


def domeny_site(site_info: dict) -> list[str]:
    """Všechny domény site — hlavní i aliasy. Guard musí vidět obojí."""
    hlavni = (site_info or {}).get("custom_domain") or ""
    aliasy = [d for d in ((site_info or {}).get("domain_aliases") or []) if d]
    return ([hlavni] if hlavni else []) + aliasy


def strez_produkci(site_info: dict, force_prod: bool, operace: str) -> None:
    """Site s vlastní doménou (i aliasem) chrání navíc --force-prod."""
    domeny = domeny_site(site_info)
    if domeny and not force_prod:
        raise NetlifyPublishError(
            f"{operace}: site má vlastní doménu ({', '.join(domeny)}). Zásah do "
            "produkce by ji okamžitě změnil. Potvrď s klientem a spusť znovu "
            "s --force-prod."
        )


# Vibe Builder staví Next.js 15 se závislostmi, které bez tohohle přepínače
# padají na ERESOLVE. Plošně ho ale zapnout nelze — u cizích projektů by tiše
# obcházel skutečné konflikty. Projekt si o něj proto řekne sám.
# Jediný doložený compatibility případ v generovaných projektech je peer
# dependency konflikt. Obecné `--force` přepisuje další npm ochrany a nemá
# pro publisher doložený use case, proto do allowlistu nepatří.
POVOLENE_INSTALL_FLAGY = {"--legacy-peer-deps"}


def install_flags_for(project_dir: Path) -> list[str]:
    """Přepínače pro `npm install` deklarované projektem.

    Čte `package.json` → `cliqsales.installFlags` (pole řetězců). Validuje se
    proti allowlistu: projekt nesmí publisheru podstrčit libovolný argument.
    """
    pkg = project_dir / "package.json"
    if not pkg.is_file():
        return []
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NetlifyPublishError(
            f"package.json nelze přečíst pro validaci installFlags: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise NetlifyPublishError("package.json musí obsahovat JSON objekt")
    metadata = data.get("cliqsales")
    if metadata is None:
        return []
    if not isinstance(metadata, dict):
        raise NetlifyPublishError("package.json → cliqsales musí být JSON objekt")
    deklarovane = metadata.get("installFlags", [])
    if not isinstance(deklarovane, list):
        raise NetlifyPublishError(
            "package.json → cliqsales.installFlags musí být pole řetězců"
        )
    vysledek = []
    for flag in deklarovane:
        if not isinstance(flag, str) or flag not in POVOLENE_INSTALL_FLAGY:
            raise NetlifyPublishError(
                f"Nepovolený install přepínač {flag!r}. Povolené: "
                + ", ".join(sorted(POVOLENE_INSTALL_FLAGY))
            )
        if flag not in vysledek:
            vysledek.append(flag)
    return vysledek


def functions_dir_for(project_dir: Path) -> Path | None:
    """Složka se serverovými funkcemi, nebo None.

    Čte i `netlify.toml` — natvrdo `netlify/functions` by u projektu s jinou
    cestou vedlo k tichému nasazení bez funkcí (mrtvý frontend, 404 na /api/*).

    Fail-closed ve třech místech, kde dřív procházel tichý průšvih:
    - nastavená, ale neexistující složka je chyba (dřív `None` = mrtvý frontend),
    - cesta musí zůstat uvnitř projektu (`../../jinam` dřív nahrálo cizí strom),
    - symlink se odmítá.
    """
    toml = project_dir / "netlify.toml"
    configured = (
        _functions_directory_from_toml(toml.read_text(errors="ignore"))
        if toml.is_file()
        else None
    )

    if configured is None:
        default = project_dir / "netlify" / "functions"
        if not default.is_dir():
            return None
        # I výchozí složka může být symlink mimo projekt.
        return resolve_inside_project(project_dir, "netlify/functions", "netlify/functions")

    candidate = resolve_inside_project(
        project_dir, configured, "netlify.toml: [functions].directory"
    )
    if not candidate.is_dir():
        raise NetlifyPublishError(
            f"netlify.toml: [functions].directory neexistuje: {configured!r}. Nastavená, "
            "ale chybějící složka by nasadila mrtvý frontend se 404 na /api/*."
        )
    return candidate


def uses_managed_database(project_dir: Path) -> bool:
    """Používá projekt databázi ZASTARALÝM způsobem (pevná env proměnná)?

    Jen tehdy je náhled slepý. Ověřeno 9. 8. 2026: u nahrání hotových souborů
    (--no-build) dostane připojení k databázi jen produkce → na náhledu
    /api/* vrací 502.

    ⚠️ Oprava dřívějšího závěru: NENÍ to vlastnost platformy. Netlify má
    `getConnectionString()` z `@netlify/database`, které samo míří na ostrou
    databázi u produkce a na IZOLOVANOU VĚTEV u náhledu. Projekt, který ho
    používá, má náhled funkční a tahle brána se na něj nevztahuje.
    """
    # Legacy má PŘEDNOST: projekt může mít obojí a pak je rozhodující ta
    # stará cesta — náhled je u ní pořád slepý.
    fdir = functions_dir_for(project_dir)
    if fdir:
        for f in fdir.rglob("*"):
            if f.suffix not in (".mjs", ".js", ".ts", ".mts", ".cjs", ".cts"):
                continue
            obsah = f.read_text(errors="ignore")
            if "NETLIFY_DATABASE_URL" in obsah or "NETLIFY_DB_URL" in obsah:
                return True
    return False


def uses_connection_string_api(project_dir: Path) -> bool:
    """Čte projekt adresu databáze přes `getConnectionString()`?"""
    fdir = functions_dir_for(project_dir)
    if fdir:
        for f in fdir.rglob("*"):
            if f.suffix in (".mjs", ".js", ".ts", ".mts", ".cjs", ".cts") \
               and "getConnectionString" in f.read_text(errors="ignore"):
                return True
    return False



def cleanup_build_artifacts(project_dir: Path, framework: dict[str, Any]) -> dict[str, int]:
    """Smaže node_modules + relevantní cache po buildu. Vrátí stats."""
    removed = {"node_modules": 0, "cache": 0}

    # SSR deploy uses `netlify deploy` build mode, which needs the local project
    # dependencies/config to bundle functions and framework routes. Static exports
    # upload `out/` directly and can be cleaned aggressively.
    if framework.get("ssr"):
        return removed

    # Statický projekt S FUNKCEMI je taky buildovaný: Netlify je balí esbuildem
    # až při deployi a potřebuje k tomu závislosti. Bez nich deploy projde,
    # ale /api/* spadne na 502.
    if functions_dir_for(project_dir) is not None:
        return removed

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
        return {**summary, "created": False, "wouldCreate": True}

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
    if not isinstance(payload, dict):
        raise NetlifyPublishError(
            "Vytvoření site nevrátilo JSON objekt se site ID; úspěch nelze potvrdit"
        )
    site_id = str(payload.get("id") or payload.get("site_id") or "")
    if not site_id:
        raise NetlifyPublishError(
            "Vytvoření site nevrátilo site ID; publisher nebude hlásit úspěch"
        )
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

    def find_existing() -> dict[str, Any] | None:
        for candidate in candidates:
            existing = find_site_by_name(candidate, credentials)
            if not existing:
                continue
            site_id = str(existing.get("id") or existing.get("site_id") or "").strip()
            if not site_id:
                raise NetlifyPublishError(
                    f"Existující site {candidate!r} nemá site ID; publisher nebude hlásit úspěch"
                )
            return {
                "ok": True,
                "dryRun": bool(getattr(args, "dry_run", False)),
                "created": False,
                "siteId": site_id,
                "siteName": candidate,
                "url": existing.get("ssl_url") or existing.get("url") or "",
                "adminUrl": existing.get("admin_url") or "",
            }
        return None

    dry_run = bool(getattr(args, "dry_run", False))
    confirmed = bool(getattr(args, "confirm_create", False))

    # Read-only lookup nepotřebuje lock. Ostrý create ale musí lookup zopakovat
    # až pod sdíleným zámkem, jinak dva chat runy založí primary + fallback.
    if dry_run or not confirmed:
        existing_result = find_existing()
        if existing_result:
            return existing_result
        if dry_run:
            return {
                "ok": True,
                "dryRun": True,
                "created": False,
                "wouldCreate": True,
                "siteName": candidates[0],
                "candidates": candidates,
                "accountSlug": account_slug,
            }
        raise NetlifyPublishError(
            "Ensure-site nenašel existující site. Vytvoření nové vyžaduje "
            "--confirm-create po explicitním schválení klienta; náhled použij přes --dry-run"
        )

    with ensure_site_operation_lock(slug, account_slug):
        existing_result = find_existing()
        if existing_result:
            # Volající požádal o create, ale souběžný potvrzený běh jej právě
            # dokončil. Vracíme jeden skutečný site jako idempotentní úspěch.
            existing_result["dryRun"] = False
            return existing_result

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
                if not isinstance(payload, dict):
                    raise NetlifyPublishError(
                        f"Vytvoření site {candidate!r} nevrátilo JSON objekt se site ID"
                    )
                site_id = str(payload.get("id") or payload.get("site_id") or "")
                if not site_id:
                    raise NetlifyPublishError(
                        f"Vytvoření site {candidate!r} nevrátilo site ID; "
                        "publisher nebude hlásit úspěch"
                    )
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
                # Netlify namespace je globální. Než přejdeme na fallback,
                # znovu ověříme, zda kolizi nevytvořil souběžný běh pod naším
                # účtem mimo tento proces/container.
                if "already" in str(exc).lower() or "taken" in str(exc).lower():
                    existing = find_site_by_name(candidate, credentials)
                    if existing:
                        site_id = str(existing.get("id") or existing.get("site_id") or "").strip()
                        if not site_id:
                            raise NetlifyPublishError(
                                f"Existující site {candidate!r} nemá site ID"
                            )
                        return {
                            "ok": True,
                            "dryRun": False,
                            "created": False,
                            "siteId": site_id,
                            "siteName": candidate,
                            "url": existing.get("ssl_url") or existing.get("url") or "",
                            "adminUrl": existing.get("admin_url") or "",
                        }
                    continue
                raise

        raise NetlifyPublishError(
            f"Žádný kandidát nešel vytvořit ({candidates}): {last_error}"
        )


def command_build(args: argparse.Namespace) -> dict[str, Any]:
    """Detekuj framework + npm install + build + cleanup. Vrátí cestu k output dir."""
    project_dir = resolve_project_dir(args.path)
    framework = detect_framework(project_dir)
    # Validuj metadata i v dry-runu. Jinak by náhled prošel a ostrý běh
    # teprve spadl (nebo dříve tiše ignoroval poškozený JSON).
    install_flags = install_flags_for(project_dir)

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
        ["install", "--no-audit", "--no-fund", *install_flags],
        cwd=project_dir,
        timeout=NPM_INSTALL_TIMEOUT,
    )
    if rc != 0:
        tail = (install_stderr or install_stdout or "").strip().splitlines()[-20:]
        raise NetlifyPublishError(
            "npm install selhal:\n" + "\n".join(tail)
        )

    # Přenesený projekt může mít správný soubor, ale ztracený executable bit.
    # Opravujeme jen přesnou Next binárku uvnitř projektu, bez shellu/globu.
    ensure_next_binary_executable(project_dir, framework)

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
    cleanup_skipped = ""
    if not args.keep_cache:
        if framework["ssr"]:
            cleanup_skipped = "SSR deploy needs dependencies/cache for Netlify build mode"
        cleanup_stats = cleanup_build_artifacts(project_dir, framework)

    return {
        **summary,
        "built": True,
        "cleanup": {
            "nodeModulesBytes": cleanup_stats["node_modules"],
            "cacheBytes": cleanup_stats["cache"],
        },
        **({"cleanupSkipped": cleanup_skipped} if cleanup_skipped else {}),
        "deprecationWarnings": deprecation_warnings,
    }


def command_update_deps(args: argparse.Namespace) -> dict[str, Any]:
    """Aktualizuj deklarované framework dependencies.

    Default (bez --major) připne každý balík na jeho stávající patch řadu.
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

    all_versions = read_package_versions(project_dir, packages)
    versions_before = {pkg: version for pkg, version in all_versions.items() if version}
    packages = list(versions_before)
    if not packages:
        return {
            "ok": True,
            "skipped": f"framework {framework['type']} nemá deklarované core packages",
        }

    package_specs = (
        [f"{pkg}@latest" for pkg in packages]
        if args.major
        else patch_install_specs(versions_before)
    )

    if args.dry_run:
        return {
            "ok": True,
            "dryRun": True,
            "path": str(project_dir),
            "framework": framework["type"],
            "mode": "major" if args.major else "patches",
            "packages": packages,
            "packageSpecs": package_specs,
            "versionsBefore": versions_before,
        }

    if args.major:
        # `@latest` je výslovně opt-in; může překročit major verzi.
        cmd = ["install"] + package_specs + ["--no-audit", "--no-fund"]
    else:
        # `npm update` respektuje třeba caret a směl by povýšit i minor verzi.
        # Instalace explicitního `~X.Y.Z` drží každý balík v jedné patch řadě.
        cmd = ["install"] + package_specs + ["--no-audit", "--no-fund"]

    rc, stdout, stderr = run_npm_command(cmd, cwd=project_dir, timeout=NPM_INSTALL_TIMEOUT)
    if rc != 0:
        tail = (stderr or stdout or "").strip().splitlines()[-20:]
        raise NetlifyPublishError(
            "npm install selhal:\n" + "\n".join(tail)
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
        "packageSpecs": package_specs,
        "versionsBefore": versions_before,
        "versionsAfter": versions_after,
        "changed": changed,
        "remainingDeprecationWarnings": remaining_warnings,
        "nextStep": "Spusť `build` + `deploy` pro novou verzi.",
    }


def _read_project_state(project_dir: Path) -> dict[str, Any]:
    """Read publisher-owned state without following links or accepting invalid shapes."""
    state_path = project_dir / ".netlify-state.json"
    if state_path.is_symlink():
        raise NetlifyPublishError(f"{state_path.name} je symbolický odkaz")
    if not state_path.exists():
        return {}
    if not state_path.is_file():
        raise NetlifyPublishError(f"{state_path.name} není běžný soubor")
    try:
        loaded = json.loads(state_path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NetlifyPublishError(f"{state_path.name} nelze bezpečně přečíst") from exc
    if not isinstance(loaded, dict):
        raise NetlifyPublishError(f"{state_path.name} neobsahuje JSON objekt")
    return loaded


def _write_project_state(
    project_dir: Path,
    fields: dict[str, Any],
    *,
    remote_operation_completed: bool = True,
) -> None:
    """Atomically persist deterministic deploy state or fail truthfully.

    Control Center čte tento soubor přímo (sdílený /documents volume) a slije ho do
    CC-vlastněného .web-builder.json — takže nemusí hádat Netlify site name. Hodnota
    None je explicitní tombstone (např. promote vyčistí pending draft URL).
    """
    state_path = project_dir / ".netlify-state.json"
    temp_path = project_dir / f".netlify-state.json.tmp-{os.getpid()}-{time.time_ns()}"
    try:
        existing = _read_project_state(project_dir)
        existing.update(fields)
        existing["skillVersion"] = SKILL_VERSION
        existing["stateVersion"] = STATE_VERSION
        existing["updatedAt"] = int(time.time())
        encoded = (json.dumps(existing, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        descriptor = os.open(
            temp_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, state_path)
    except NetlifyPublishError as exc:
        prefix = (
            "Netlify operace proběhla, ale stav nelze bezpečně uložit"
            if remote_operation_completed
            else "Lokální Netlify stav nelze bezpečně migrovat"
        )
        raise NetlifyPublishError(
            f"{prefix}: {exc}; Control Center může ukazovat starý stav"
        ) from exc
    except OSError as exc:
        prefix = (
            "Netlify operace proběhla, ale"
            if remote_operation_completed
            else "Lokální migrace selhala:"
        )
        raise NetlifyPublishError(
            f"{prefix} {state_path.name} se nepodařilo uložit; "
            "Control Center může ukazovat starý stav"
        ) from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


def _migrate_project_state(project_dir: Path) -> dict[str, Any]:
    """Idempotently migrate the per-project publisher state to v2.

    Legacy v1 stored a draft URL without its deploy ID, so it cannot prove
    which artifact a later promote would publish. Preserve site/production
    truth, but invalidate that unverifiable pending draft. Future state shapes
    fail closed rather than being silently downgraded.
    """
    existing = _read_project_state(project_dir)
    if not existing:
        return existing
    raw_version = existing.get("stateVersion")
    if raw_version == STATE_VERSION:
        return existing
    if raw_version not in (None, 1):
        raise NetlifyPublishError(
            f".netlify-state.json používá nepodporovanou stateVersion {raw_version!r}; "
            "stav nebyl změněn"
        )

    draft_url = str(existing.get("draftUrl") or "").strip()
    draft_id = str(existing.get("draftDeployId") or "").strip()
    fields: dict[str, Any] = {
        "migratedFromStateVersion": 1,
        "promotedDeployId": None,
        "rolledBackDeployId": None,
    }
    if not draft_url or not draft_id:
        fields.update({"draftUrl": None, "draftDeployId": None})
    _write_project_state(
        project_dir,
        fields,
        remote_operation_completed=False,
    )
    return _read_project_state(project_dir)


def ensure_next_ssr_netlify_config(project_dir: Path, framework: dict[str, Any]) -> dict[str, Any] | None:
    """Ensure SSR config masks the deploy credential from every build child."""
    if framework.get("type") != "nextjs-ssr":
        return None

    config_path = project_dir / "netlify.toml"
    if config_path.is_symlink():
        raise NetlifyPublishError(
            "netlify.toml nesmí být symlink (ani dangling); konfigurace nebyla zapsána"
        )
    if config_path.is_file():
        _validate_ssr_auth_mask(config_path)
        return {"path": str(config_path), "created": False, "authMasked": True}
    if config_path.exists():
        raise NetlifyPublishError("netlify.toml existuje, ale není běžný soubor")

    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(config_path, flags, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(
                '[build]\n'
                '  command = "npm run build"\n'
                '  publish = ".next"\n\n'
                '[build.environment]\n'
                '  NETLIFY_AUTH_TOKEN = ""\n'
            )
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise NetlifyPublishError("netlify.toml se nepodařilo bezpečně vytvořit") from exc
    _validate_ssr_auth_mask(config_path)
    return {"path": str(config_path), "created": True, "authMasked": True}


def _validate_ssr_auth_mask(config_path: Path) -> None:
    """Fail closed unless config-file precedence blanks PAT for build children."""
    try:
        import tomllib

        parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 — fail closed on malformed config
        raise NetlifyPublishError(f"netlify.toml nejde bezpečně přečíst: {exc}") from exc
    build = parsed.get("build")
    if not isinstance(build, dict):
        raise NetlifyPublishError("SSR netlify.toml musí obsahovat [build]")
    environment = build.get("environment")
    if not isinstance(environment, dict) or environment.get("NETLIFY_AUTH_TOKEN") != "":
        raise NetlifyPublishError(
            "SSR netlify.toml musí obsahovat [build.environment] "
            'NETLIFY_AUTH_TOKEN = "", jinak build zdědí deploy credential'
        )

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key == "NETLIFY_AUTH_TOKEN" and nested != "":
                    raise NetlifyPublishError(
                        "SSR netlify.toml nesmí v žádném contextu nastavit "
                        "NETLIFY_AUTH_TOKEN na neprázdnou hodnotu"
                    )
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(parsed)


def should_verify_deploy_url() -> bool:
    raw = str(os.environ.get("NETLIFY_PUBLISH_SKIP_URL_CHECK") or "").strip().lower()
    return raw not in {"1", "true", "yes", "on"}


def verify_deploy_url(url: str) -> None:
    """Poll the published URL and fail before state write if Netlify returned a 404/5xx URL."""
    import urllib.error
    import urllib.request

    if not url:
        raise NetlifyPublishError("Netlify CLI nevrátil deploy URL")

    timeout = int(os.environ.get("NETLIFY_PUBLISH_URL_VERIFY_TIMEOUT_SECONDS") or DEPLOY_URL_VERIFY_TIMEOUT)
    deadline = time.time() + max(1, timeout)
    last_error = ""
    headers = {"User-Agent": "cliqsales-netlify-publisher/1.3.4"}

    while True:
        try:
            req = urllib.request.Request(url, headers=headers, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as response:
                if 200 <= int(response.status) < 400:
                    return
                last_error = f"HTTP {response.status}"
        except urllib.error.HTTPError as exc:
            if exc.code == 405:
                try:
                    req = urllib.request.Request(url, headers=headers, method="GET")
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if 200 <= int(response.status) < 400:
                            return
                        last_error = f"HTTP {response.status}"
                except Exception as inner:
                    last_error = str(inner)
            else:
                last_error = f"HTTP {exc.code}"
        except Exception as exc:
            last_error = str(exc)

        if time.time() >= deadline:
            raise NetlifyPublishError(
                f"Deploy URL není dostupná ({url}): {last_error or 'bez detailu'}. "
                "State nebyl zapsán; neopakuj starou 404 URL jako úspěšný deploy."
            )
        time.sleep(DEPLOY_URL_VERIFY_INTERVAL)


def command_deploy(args: argparse.Namespace) -> dict[str, Any]:
    """Deploy projekt (static nebo SSR). Default = draft; production needs confirmation.

    Smart safety: production always requires --confirm-publish yes. A site
    with a custom domain additionally requires --force-prod.
    """
    project_dir = resolve_project_dir(args.path)

    # Detekuj framework, abychom věděli, kterou složku deployovat
    framework = detect_framework(project_dir)
    if args.ssr and not framework["ssr"]:
        raise NetlifyPublishError(
            "--ssr nesmí přepsat detekovaný static framework; uprav frameworkovou konfiguraci "
            "místo vynucení neověřeného build-mode deploye"
        )
    ssr = bool(framework["ssr"])
    if ssr and framework.get("type") != "nextjs-ssr":
        raise NetlifyPublishError(
            f"SSR deploy frameworku {framework.get('type')!r} zatím není bezpečně podporovaný. "
            "Publisher 1.3.4 ověřuje build-mode credential masku a výsledný strom pouze pro "
            "Next.js SSR; Netlify CLI nebylo spuštěno."
        )
    netlify_config: dict[str, Any] | None = None

    if ssr:
        # SSR: Netlify CLI musí build i upload provést v jediném procesu, aby
        # zachovalo framework config mutace. netlify.toml proto povinně maskuje
        # PAT jen v build/plugin child procesech; parent CLI si ho ponechá.
        functions_dir = None   # SSR build si funkce zabalí sám
        deploy_dir = project_dir
        if not (project_dir / ".next").is_dir():
            raise NetlifyPublishError(
                "SSR deploy vyžaduje .next/ složku (nejdřív spusť `build`)"
            )
        # Dry-run nesmí nic měnit. Případné bezpečné vytvoření netlify.toml
        # proběhne až po kompletním symlink/security scanu a pod lockem.
        if args.dry_run:
            netlify_config = {"dryRun": "netlify.toml se v náhledu nezapisuje"}
    else:
        # Static: deploy output_dir
        # `output_dir` může pocházet z package.json → publishDir, tedy ze
        # souboru v projektu. Bez tohohle resolveru šlo `publishDir: "/etc"`
        # nebo symlinkovaný `dist` nasadit na veřejný web.
        if framework["output_dir"] == ".":
            deploy_dir = project_dir.resolve()
        else:
            deploy_dir = resolve_inside_project(
                project_dir, framework["output_dir"], "publish složka (output_dir)"
            )
            if not deploy_dir.is_dir():
                raise NetlifyPublishError(
                    f"Publish složka neexistuje: {framework['output_dir']!r} "
                    "(nejdřív spusť `build`)"
                )
        functions_dir = functions_dir_for(project_dir)
        if not (deploy_dir / "index.html").is_file():
            raise NetlifyPublishError(
                f"Static deploy složka musí obsahovat index.html: {deploy_dir}"
            )

    # Bezpečnostní validace souborů musí doběhnout PŘED prvním lokálním
    # zápisem. U SSR je to preflight projektových zdrojů i lokálního `.next`
    # buildu; Netlify CLI následně sestaví vlastní bundle, takže počet
    # výsledných deploy souborů stále neznáme a nesmíme ho za tento scan vydávat.
    # Funkce jdou na Netlify taky (--functions),
    # takže musí projít stejným scanem — blokované soubory, symlinky a limity.
    # Dřív se kontroloval jen statický output a do funkcí mohl propadnout .env.
    files = collect_publish_files(deploy_dir)
    static_manifest = publish_manifest_snapshot(deploy_dir, files) if not ssr else {}
    # Root SSR scan záměrně vynechává `.next` jako BLOCKED_DIR_NAMES, aby
    # source preflight nepočítal tentýž strom dvakrát. Samotný SSR build output
    # ale musí projít vlastním scanem — jinak by v něm nested/dangling symlink
    # zůstal neověřený a report by nebyl pravdivý.
    ssr_output_files = collect_publish_files(project_dir / ".next") if ssr else []
    function_files = collect_publish_files(functions_dir) if functions_dir else []
    if len(files) + len(ssr_output_files) + len(function_files) > MAX_FILES:
        raise NetlifyPublishError(f"Příliš mnoho souborů: limit je {MAX_FILES}")
    total_bytes = total_publish_bytes(files + ssr_output_files + function_files)

    publish_confirmed = args.confirm_publish == "yes"
    if args.draft and publish_confirmed:
        raise NetlifyPublishError("--draft nelze kombinovat s --confirm-publish yes")
    if args.force_prod and not publish_confirmed:
        raise NetlifyPublishError(
            "--force-prod nestačí: produkce vyžaduje --confirm-publish yes po výslovném souhlasu klienta"
        )
    draft_mode = not publish_confirmed

    # Náhled je u NAHRANÉHO statického projektu s Netlify DB slepý: připojení
    # k databázi dostane jen produkce, takže /api/* vrací 502 a klient by
    # schvaloval rozbitý stav. U SSR (build mode) náhled databázi má.
    # Blokujeme JEN skutečné DB projekty — formulář s běžným klíčem se
    # v náhledu chová správně a náhled si zaslouží.
    if draft_mode and functions_dir is not None and uses_managed_database(project_dir):
        raise NetlifyPublishError(
            "STOP: projekt používá Netlify databázi. Náhled se k ní nedostane "
            "(/api/* by vracelo 502), takže na něm nejde nic schválit. "
            "Zastav se a vyžádej si od klienta výslovný souhlas s publikací "
            "do produkce. Souhlas nesmí nahradit pokyn 'pokračuj bez čekání' "
            "ani vlastní úsudek agenta. Teprve po souhlasu klienta spusť znovu."
        )

    summary = {
        "ok": True,
        "path": str(deploy_dir),
        "framework": framework["type"],
        "ssr": ssr,
        "deployMode": "ssr-build-token-masked" if ssr else ("static-upload+functions" if functions_dir else "static-upload"),
        "functions": sorted(p.name for p in function_files if p.suffix in FUNCTION_SUFFIXES),
        "scan": {
            "scope": "ssr-project-and-build-output-preflight" if ssr else "publish-output",
            "files": len(files) + len(ssr_output_files),
            "sourceFiles": len(files) if ssr else 0,
            "ssrBuildOutputFiles": len(ssr_output_files),
            "functionFiles": len(function_files),
            "bytes": total_bytes,
            "isFinalPublicManifest": not ssr,
            # Netlify still bundles server functions. Only a function-free
            # static upload is the complete final deploy manifest.
            "isFinalDeployManifest": not ssr and functions_dir is None,
        },
        "draft": draft_mode,
        **({"netlifyConfig": netlify_config} if netlify_config else {}),
    }
    if args.dry_run:
        return {**summary, "dryRun": True}

    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not credentials.get("auth_token") or not site_id:
        raise NetlifyPublishError("NETLIFY_AUTH_TOKEN a site-id jsou vyžadovány")

    # Produkční deploy načte site objekt až pod stejným per-site zámkem jako
    # add-domain. Jinak se doména mohla připojit mezi guardem a deployem.
    site_info: dict[str, Any] = {}

    title = args.title or f"CC publish: {deploy_dir.name}"
    if ssr:
        command = [
            "deploy",
            "--site",
            site_id,
            "--json",
            "--message",
            title,
        ]
        command.extend(["--context", "deploy-preview" if draft_mode else "production"])
        if not draft_mode:
            command.append("--prod")
    # One lock covers the remote mutation, URL verification and local state
    # commit. Atomic JSON alone cannot order two concurrent deploy/promote runs.
    with publication_operation_locks(project_dir, site_id):
        if not draft_mode:
            site_payload = run_netlify_cli(
                ["api", "getSite", "--data", json.dumps({"site_id": site_id})],
                credentials,
            )
            if not isinstance(site_payload, dict):
                raise NetlifyPublishError(
                    "Netlify getSite nevrátil JSON objekt; produkční guard nelze ověřit"
                )
            site_info = site_payload
            strez_produkci(site_info, args.force_prod, "Production deploy")
        _migrate_project_state(project_dir)
        if ssr:
            netlify_config = ensure_next_ssr_netlify_config(project_dir, framework)
            if netlify_config:
                summary["netlifyConfig"] = netlify_config
            payload = run_netlify_cli(
                command,
                credentials,
                cwd=project_dir,
                # SSR config může nést vzdálené site env metadata, jejichž
                # hodnoty wrapper nezná a neuměl by je spolehlivě redigovat.
                sensitive_output=True,
            )
        else:
            # Netlify CLI musí dostat přesně strom, který prošel scanem. Kdyby
            # dostalo původní output dir, scannerem přeskočená CC metadata by se
            # u vanilla projektu s output_dir="." přesto veřejně nahrála.
            with static_publish_staging(deploy_dir, static_manifest) as staged_dir:
                command = [
                    "deploy",
                    "--dir",
                    str(staged_dir),
                    "--site",
                    site_id,
                    "--json",
                    "--no-build",
                    "--message",
                    title,
                ]
                # Statický export sám funkce nenahraje. Bez tohohle by se
                # aplikace nasadila jako mrtvý frontend s 404 na /api/*.
                if functions_dir is not None:
                    command.extend(["--functions", str(functions_dir)])
                if not draft_mode:
                    command.append("--prod")
                payload = run_netlify_cli(
                    command,
                    credentials,
                    # S funkcemi musí CLI běžet v projektu, jinak nenajde
                    # netlify.toml ani závislosti pro jejich zabalení.
                    cwd=project_dir if functions_dir is not None else None,
                )
        # Direct deploy končí stavem `ready`; neplést s restoreSiteDeploy,
        # jehož terminální úspěch je `current`. Validator zároveň zajistí,
        # že níže pracujeme s JSON objektem svázaným s přesným site.
        overeny_deploy_id = validate_direct_deploy_result(payload, site_id, credentials)
        if draft_mode:
            result_url = (
                payload.get("deploy_ssl_url")
                or payload.get("deploy_url")
                or payload.get("deployUrl")
                or ""
            )
        else:
            # Ověřovat se musí URL TOHOTO deploye — stabilní produkční adresa
            # vrací 200 i ze staré funkční verze a zakryla by vadný deploy.
            result_url = stable_site_url(site_info)
            overovana_url = (
                payload.get("deploy_ssl_url") or payload.get("deploy_url")
                or payload.get("deployUrl") or result_url
            )
        if not result_url:
            raise NetlifyPublishError(
                "Netlify deploy nevrátil ověřitelnou URL; lokální deploy stav nebyl změněn"
            )
        if should_verify_deploy_url():
            verify_deploy_url(locals().get("overovana_url") or result_url)
        # Validator výše prokázal přesnou vazbu odpovědi na požadovaný site.
        resolved_site_id = site_id
        resolved_deploy_id = overeny_deploy_id
        if draft_mode:
            if not resolved_deploy_id:
                raise NetlifyPublishError(
                    "Draft deploy proběhl, ale Netlify nevrátil deploy ID; "
                    "náhled nelze bezpečně svázat s pozdějším promote a lokální stav nebyl změněn"
                )
            _write_project_state(
                project_dir,
                {
                    "siteId": resolved_site_id,
                    "draftUrl": result_url,
                    "draftDeployId": resolved_deploy_id,
                },
            )
        else:
            _write_project_state(
                project_dir,
                {
                    "siteId": resolved_site_id,
                    "draftUrl": None,
                    "draftDeployId": None,
                    "prodUrl": result_url,
                    "prodDeployId": resolved_deploy_id,
                    # Přímý production deploy není promote ani rollback.
                    # Tombstones brání tomu, aby stará historie falešně
                    # splnila checkpoint nové operace.
                    "promotedDeployId": None,
                    "rolledBackDeployId": None,
                },
            )
        return {
            **summary,
            "dryRun": False,
            "siteId": resolved_site_id,
            "deployId": resolved_deploy_id,
            "state": payload.get("state") or "",
            "url": result_url,
            "adminUrl": payload.get("admin_url") or "",
        }


def command_promote(args: argparse.Namespace) -> dict[str, Any]:
    """Promote the exact project-bound draft through API restoreSiteDeploy."""
    if args.confirm_publish != "yes":
        raise NetlifyPublishError(
            "Promote do produkce vyžaduje --confirm-publish yes po výslovném souhlasu klienta"
        )
    project_dir = resolve_project_dir(args.path)
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován pro promote")

    # Approval is tied to the URL currently shown for this project, not merely to
    # any ready deploy on the same site. The same lock also serializes new drafts.
    with publication_operation_locks(project_dir, site_id):
        project_state = _migrate_project_state(project_dir)
        stored_site_id = str(project_state.get("siteId") or "").strip()
        stored_deploy_id = str(project_state.get("draftDeployId") or "").strip()
        stored_draft_url = str(project_state.get("draftUrl") or "").strip()
        if not stored_site_id or not stored_deploy_id or not stored_draft_url:
            raise NetlifyPublishError(
                "Projekt nemá uloženou úplnou dvojici draft URL + deploy ID; "
                "nejdřív vytvoř nový náhled a nech jej schválit"
            )
        if stored_site_id != site_id:
            raise NetlifyPublishError(
                f"Projektový draft patří site {stored_site_id}, ne {site_id}; production nebyla změněna"
            )
        if stored_deploy_id != args.deploy_id:
            raise NetlifyPublishError(
                "Zadané deploy ID nepatří aktuálnímu náhledu tohoto projektu; "
                "production nebyla změněna"
            )

        site_payload = run_netlify_cli(
            ["api", "getSite", "--data", json.dumps({"site_id": site_id})], credentials
        )
        site_info = site_payload if isinstance(site_payload, dict) else {}
        strez_produkci(site_info, args.force_prod, "Promote")
        prod_url = stable_site_url(site_info)
        if not prod_url:
            raise NetlifyPublishError("Netlify site nevrátil stabilní production URL; promote se nespustil")

        # Publikuj přesně klientem schválený draft, nikdy pouze "nejnovější".
        payload = run_netlify_cli(
            ["api", "listSiteDeploys", "--data", json.dumps({"site_id": site_id, "per_page": 20})],
            credentials,
        )
        deploys = payload if isinstance(payload, list) else []
        approved_draft = next(
            (
                d for d in deploys
                if d.get("id") == args.deploy_id
                and d.get("state") == "ready"
                and not d.get("published_at")
                and d.get("context") in ("deploy-preview", "branch-deploy")
            ),
            None,
        )
        if not approved_draft:
            raise NetlifyPublishError(
                f"Schválený draft {args.deploy_id} není hotový nebo už není draft; "
                "production nebyla změněna"
            )
        approved_draft_url = (
            approved_draft.get("deploy_ssl_url")
            or approved_draft.get("deploy_url")
            or approved_draft.get("ssl_url")
            or approved_draft.get("url")
            or ""
        )
        if deploy_url_identity(approved_draft_url) != deploy_url_identity(stored_draft_url):
            raise NetlifyPublishError(
                "Netlify deploy ID neodpovídá URL aktuálně schváleného náhledu; "
                "production nebyla změněna"
            )

        deploy_id = approved_draft["id"]
        result = run_netlify_cli(
            ["api", "restoreSiteDeploy", "--data", json.dumps({"site_id": site_id, "deploy_id": deploy_id})],
            credentials,
        )
        restored_deploy_id = validate_restore_result(
            result,
            "Promote",
            site_id,
            deploy_id,
            credentials,
        )
        if should_verify_deploy_url():
            verify_deploy_url(prod_url)
        _write_project_state(
            project_dir,
            {
                "siteId": site_id,
                "draftUrl": None,
                "draftDeployId": None,
                "prodUrl": prod_url,
                "prodDeployId": restored_deploy_id,
                "promotedDeployId": restored_deploy_id,
                "rolledBackDeployId": None,
            },
        )
        return {
            "ok": True,
            "siteId": site_id,
            "promotedDeployId": restored_deploy_id,
            "url": prod_url,
            "state": str(result.get("state") or "") if isinstance(result, dict) else "",
        }


def command_rollback(args: argparse.Namespace) -> dict[str, Any]:
    """Rollback exact project-bound site to one exact previous deploy."""
    project_dir = resolve_project_dir(args.path)
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id or not args.deploy_id:
        raise NetlifyPublishError("--site-id a --deploy-id jsou vyžadovány")

    if args.dry_run:
        project_state = _read_project_state(project_dir)
        stored_site_id = str(project_state.get("siteId") or "").strip()
        if not stored_site_id:
            raise NetlifyPublishError(
                "Projekt nemá uložené site ID; rollback nelze bezpečně svázat s projektem"
            )
        if stored_site_id != site_id:
            raise NetlifyPublishError(
                f"Projekt patří site {stored_site_id}, ne {site_id}; rollback se nespustil"
            )
        site_payload = run_netlify_cli(
            ["api", "getSite", "--data", json.dumps({"site_id": site_id})], credentials
        )
        site_info = site_payload if isinstance(site_payload, dict) else {}
        return {
            "ok": True, "dryRun": True, "siteId": site_id,
            "path": str(project_dir),
            "restoredDeployId": args.deploy_id,
            "requiresForceProd": bool(domeny_site(site_info)),
            "pozn": "Nic se nezměnilo. Bez --dry-run se produkce přepne na tento deploy.",
        }

    # Rollback okamžitě mění to, co vidí návštěvníci.
    if args.confirm_publish != "yes":
        raise NetlifyPublishError(
            "Rollback mění produkci a vyžaduje --confirm-publish yes po výslovném "
            "souhlasu klienta"
        )

    with publication_operation_locks(project_dir, site_id):
        # Vazbu znovu čti až pod lockem: souběžný deploy nesmí mezi kontrolou
        # a restore přepnout projekt na jiný site.
        project_state = _migrate_project_state(project_dir)
        stored_site_id = str(project_state.get("siteId") or "").strip()
        if not stored_site_id:
            raise NetlifyPublishError(
                "Projekt nemá uložené site ID; rollback nelze bezpečně svázat s projektem"
            )
        if stored_site_id != site_id:
            raise NetlifyPublishError(
                f"Projekt patří site {stored_site_id}, ne {site_id}; rollback se nespustil"
            )

        site_payload = run_netlify_cli(
            ["api", "getSite", "--data", json.dumps({"site_id": site_id})], credentials
        )
        site_info = site_payload if isinstance(site_payload, dict) else {}
        strez_produkci(site_info, args.force_prod, "Rollback")
        prod_url = stable_site_url(site_info)
        if not prod_url:
            raise NetlifyPublishError(
                "Netlify site nevrátil stabilní production URL; rollback se nespustil"
            )

        result = run_netlify_cli(
            [
                "api",
                "restoreSiteDeploy",
                "--data",
                json.dumps({"site_id": site_id, "deploy_id": args.deploy_id}),
            ],
            credentials,
        )
        restored_deploy_id = validate_restore_result(
            result,
            "Rollback",
            site_id,
            args.deploy_id,
            credentials,
        )
        if should_verify_deploy_url():
            verify_deploy_url(prod_url)
        _write_project_state(
            project_dir,
            {
                "siteId": site_id,
                "prodUrl": prod_url,
                "prodDeployId": restored_deploy_id,
                "promotedDeployId": None,
                "rolledBackDeployId": restored_deploy_id,
            },
        )
        return {
            "ok": True,
            "siteId": site_id,
            "path": str(project_dir),
            "restoredDeployId": restored_deploy_id,
            "url": prod_url,
            "state": str(result.get("state") or "") if isinstance(result, dict) else "",
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

    # Sdílí přesně stejný per-site publish lock jako deploy/promote/rollback.
    # Produkční guard a změna domény proto nemohou proběhnout souběžně.
    with site_operation_lock(site_id, "publish"):
        result = run_netlify_cli(
            [
                "api",
                "updateSite",
                "--data",
                json.dumps({"site_id": site_id, "body": {"custom_domain": domain}}),
            ],
            credentials,
        )
    if not isinstance(result, dict):
        raise NetlifyPublishError("Netlify updateSite nevrátil JSON objekt")
    return {
        "ok": True,
        "siteId": site_id,
        "domain": domain,
        "sslStatus": result.get("ssl_status") or "provisioning",
        "url": f"https://{domain}",
        "nextStep": "Zavolej `verify-domain` pro check SSL provisioning (poll max 5 min).",
    }


def _domena_patri_k_site(site_info: dict, domena: str) -> bool:
    """SSL aktivní na site neznamená, že JE TAM tahle doména."""
    hledana = (domena or "").strip().lower()
    return any(hledana == d.strip().lower() for d in domeny_site(site_info))


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
        payload = run_netlify_cli(
            ["api", "getSite", "--data", json.dumps({"site_id": site_id})],
            credentials,
        )
        if not isinstance(payload, dict):
            raise NetlifyPublishError("Netlify getSite nevrátil JSON objekt")
        ssl_status = payload.get("ssl_status") or "unknown"
        last_status = ssl_status
        # `ssl_status: active` platí pro CELÝ site. Definitivně chybějící
        # doména není stav k pollování a auth/CLI chyby se nesmí pět minut skrývat.
        if not _domena_patri_k_site(payload, domain):
            raise NetlifyPublishError(
                f"Doména {domain} není u tohoto site vedená (ani jako alias). "
                "Nejdřív ji připoj přes `add-domain`."
            )
        if ssl_status == "active":
            return {
                "ok": True,
                "siteId": site_id,
                "domain": domain,
                "sslStatus": "active",
                "url": f"https://{domain}",
            }
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
    """Compatibility boundary: Netlify production secrets are write-only."""
    raise NetlifyPublishError(
        "db-share není v této CC integraci podporován a target nebyl změněn. "
        "Netlify nevrací čitelnou production hodnotu secretu a výchozí CLI context je dev; "
        "automatické kopírování by mohlo přepsat produkci dev databází. "
        "Bundled CC konektory očekávají NETLIFY_DATABASE_URL. Pokud je správná hodnota už "
        "uložená v Control Center secret store, nastav ji na cílovém site přes "
        "env-set --key NETLIFY_DATABASE_URL --from-variable <CC_PROMENNA>."
    )


def command_db_init(args: argparse.Namespace) -> dict[str, Any]:
    """Init Netlify Database (Postgres powered by Neon) pro projekt."""
    if not args.path:
        raise NetlifyPublishError(
            "--path je vyžadován, aby se databáze bezpečně svázala s konkrétním projektem"
        )
    project_dir = resolve_project_dir(args.path)
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    # Náhled nic nezakládá, takže souhlas s cenou nevyžaduje. Podmínka
    # v opačném pořadí dělala z dry-runu zbytečnou překážku.
    if args.dry_run:
        return {
            "ok": True,
            "dryRun": True,
            "siteId": site_id,
            "path": str(project_dir),
            "pozn": "Nic se nezaložilo. Ostrý běh potřebuje --confirm-cost yes.",
        }

    # Provisionování databáze je PLACENÝ zdroj na účtu klienta. Peníze klienta
    # se utrácí až po jeho výslovném souhlasu, ne na úsudek agenta.
    if args.confirm_cost != "yes":
        raise NetlifyPublishError(
            "STOP: `database init` založí u poskytovatele databázi, kterou "
            "klient platí. Sděl mu, co vzniká a co to stojí, a teprve po jeho "
            "výslovném souhlasu spusť znovu s --confirm-cost yes. Souhlas musí "
            "dát klient; pokyn 'pokračuj bez čekání' ani vlastní úsudek ho "
            "nenahrazují a nepřenáší se z jiného úkolu."
        )

    # The command has no --site flag and operates on cwd's link state. Keep
    # verify→link→state-check→init under one per-project lock so concurrent
    # chat runs cannot retarget each other between link and init.
    with project_operation_lock(project_dir, "db-init"):
        run_netlify_cli(
            ["api", "getSite", "--data", json.dumps({"site_id": site_id})],
            credentials,
        )
        run_netlify_cli_text(["link", "--id", site_id], credentials, cwd=project_dir)
        verify_linked_site(project_dir, site_id)
        run_netlify_cli_text(["database", "init", "--yes"], credentials, cwd=project_dir)
    return {
        "ok": True,
        "siteId": site_id,
        "provider": "neon",
        "nextStep": (
            "Databáze je svázaná s projektem. Connection string spravuje Netlify; "
            "publisher ho z bezpečnostních důvodů nevrací do chatu."
        ),
    }


def command_env_set(args: argparse.Namespace) -> dict[str, Any]:
    """Nastav jednu env var pro Netlify site."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")
    if not args.key:
        raise NetlifyPublishError("--key je vyžadován")
    if not args.from_variable:
        raise NetlifyPublishError(
            "--from-variable je vyžadován; tajnou hodnotu nikdy nepředávej přes argv"
        )

    value = load_custom_variable(args.from_variable)
    set_netlify_env_var(site_id, args.key, value, credentials)
    return {
        "ok": True,
        "siteId": site_id,
        "key": args.key,
        "sourceVariable": args.from_variable,
        "set": True,
    }


def command_env_list(args: argparse.Namespace) -> dict[str, Any]:
    """List env var keys (BEZ hodnot — security)."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    payload = run_netlify_cli(
        ["env:list", "--site", site_id, "--json"],
        credentials,
        sensitive_output=True,
    )
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
    """Compatibility boundary until CC exposes approved per-service resolvers."""
    raise NetlifyPublishError(
        "sync-creds není v této CC integraci aktivní a žádný Netlify secret nebyl změněn. "
        "Požadované per-service credential resolvery nejsou součástí současného CC kontraktu. "
        "Nastav každý schválený klíč explicitně přes env-set --from-variable."
    )


def command_identity_enable(args: argparse.Namespace) -> dict[str, Any]:
    """Fail closed: netlify-cli 26.x cannot enable Netlify Identity."""
    credentials = load_netlify_credentials()
    site_id = args.site_id or credentials["site_id"]
    if not site_id:
        raise NetlifyPublishError("--site-id je vyžadován")

    raise NetlifyPublishError(
        "Netlify Identity nejde v netlify-cli 26.x spolehlivě zapnout. "
        "Publisher nic nezměnil. Pokud klient Identity výslovně chce, zapněte ho ručně: "
        "Netlify → Site configuration → Identity → Enable Identity."
    )


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

    headers = {"User-Agent": "cliqsales-netlify-publisher/1.3.4"}
    if args.token_variable:
        headers["Authorization"] = f"Bearer {load_custom_variable(args.token_variable)}"

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
        "bodyReceived": bool(body),
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
    versioned = {
        **payload,
        "skillVersion": SKILL_VERSION,
        "artifactVersion": 1,
    }
    if as_json:
        print(json.dumps(versioned, ensure_ascii=False, indent=2))
        return
    if payload.get("url"):
        print(payload["url"])
    else:
        print(json.dumps(versioned, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Netlify publisher v1.3.4 — build, deploy, manage.")
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
    p.add_argument(
        "--confirm-create",
        action="store_true",
        help="Povol vytvoření jen po explicitním souhlasu; existing site potvrzení nepotřebuje.",
    )
    p.add_argument("--dry-run", action="store_true", help="Najde existing site nebo ukáže plán bez vytvoření")
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
        help="Update framework dependencies. Default = jedna patch řada, --major = breaking-allowed",
    )
    p.add_argument("path", help="Cesta k projektu uvnitř /documents/sites/<slug>/")
    p.add_argument(
        "--major",
        action="store_true",
        help="Povol major version bumps (riziko breaking changes). Default = jen deklarovaná patch řada.",
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")

    # deploy
    p = sub.add_parser(
        "deploy",
        help="Deploy projekt (default = draft; produkce jen s --confirm-publish yes)",
    )
    p.add_argument("path", help="Cesta k projektu uvnitř /documents/sites/<slug>/")
    p.add_argument("--site-id", default="")
    p.add_argument("--title", default="")
    p.add_argument(
        "--draft",
        action="store_true",
        help="Explicitní preview/náhled (je zároveň bezpečný default).",
    )
    p.add_argument(
        "--confirm-publish",
        choices=["yes", "no"],
        default="no",
        help="Produkční publish je povolen pouze hodnotou yes po výslovném souhlasu klienta.",
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
    p = sub.add_parser("promote", help="Promote přesně určený schválený draft do produkce")
    p.add_argument("--site-id", default="")
    p.add_argument("--path", required=True, help="Projektová cesta pro aktualizaci deploy stavu")
    p.add_argument("--deploy-id", required=True, help="Přesné ID klientem schváleného draftu")
    p.add_argument("--confirm-publish", choices=["yes", "no"], default="no")
    p.add_argument(
        "--force-prod",
        action="store_true",
        help="Override custom-domain safety warning po výslovném potvrzení.",
    )
    p.add_argument("--json", action="store_true")

    # rollback
    p = sub.add_parser("rollback", help="Rollback na konkrétní předchozí deploy")
    p.add_argument("--site-id", default="")
    p.add_argument("--path", required=True, help="Projektová cesta pro site binding, lock a zápis stavu")
    p.add_argument("--deploy-id", required=True)
    p.add_argument("--confirm-publish", choices=["yes", "no"], default="no",
                   help="Zásah do produkce: yes až po výslovném souhlasu klienta")
    p.add_argument("--force-prod", action="store_true",
                   help="Nutné, když má site vlastní doménu nebo alias")
    p.add_argument("--dry-run", action="store_true", help="Ukáže, co by se stalo")
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
    p.add_argument("--path", default="", help="Cesta k projektu (povinné pro bezpečný site binding)")
    p.add_argument("--confirm-cost", choices=["yes", "no"], default="no",
                   help="Placený zdroj: yes smí padnout až po výslovném souhlasu klienta")
    p.add_argument("--dry-run", action="store_true", help="Ukáže, co by vzniklo, nic nezaloží")
    p.add_argument("--json", action="store_true")

    # db-share
    p = sub.add_parser(
        "db-share",
        help="Compatibility příkaz: bezpečně odmítne automatické kopírování DB secretu",
    )
    p.add_argument("--from-site-id", required=True, help="Source site (= drží DB)")
    p.add_argument("--to-site-id", required=True, help="Target site (= připojí se k té DB)")
    p.add_argument(
        "--keys",
        default="NETLIFY_DATABASE_URL",
        help="Compatibility-only seznam klíčů (bundled CC konektory používají NETLIFY_DATABASE_URL).",
    )
    p.add_argument("--json", action="store_true")

    # env-set
    p = sub.add_parser("env-set", help="Nastav env var pro site")
    p.add_argument("--site-id", default="")
    p.add_argument("--key", required=True)
    p.add_argument(
        "--from-variable",
        required=True,
        help="Název CC variable/SecretRef; hodnota se nikdy nepředává přes argv",
    )
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
        help="Compatibility příkaz: bezpečně odmítne sync bez schválených CC resolverů",
    )
    p.add_argument("--site-id", default="")
    p.add_argument(
        "--services",
        default="",
        help="Legacy services parametr; v současné CC integraci se žádná hodnota nemění.",
    )
    p.add_argument("--json", action="store_true")

    # identity-enable
    p = sub.add_parser("identity-enable", help="Vysvětli ruční aktivaci Netlify Identity (nic nemění)")
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
        "--token-variable",
        default="",
        help="Název CC variable/SecretRef s optional Bearer tokenem (např. CRON_SECRET)",
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
        payload = {
            "ok": False,
            "error": str(exc),
            "skillVersion": SKILL_VERSION,
            "artifactVersion": 1,
        }
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
