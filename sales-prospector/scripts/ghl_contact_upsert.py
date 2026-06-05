"""CliqSales (GoHighLevel) contact upsert helper for Sales Prospector skill.

Čte creds přes sdílenou knihovnu `cc_credentials.ghl_credentials()` (z `cs-skills/_lib/`).
Tenký wrapper nad GHL API v2 `/contacts/upsert` endpoint.

Použití:
    python3 ghl_contact_upsert.py --csv path/to/prospects.csv \\
        --tags "prospector-eko-kosmetika-eshopy" \\
        [--dry-run] [--rows 1,3,5-10]

Exit codes:
    0 = success
    2 = creds chybí / config error / API auth fail
    3 = CSV parse / validation error
    4 = partial fail (některé řádky failed, ale běh dokončen)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

GHL_API_BASE = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"
TIMEOUT_SECONDS = 30
RETRY_MAX = 3
RETRY_BACKOFF_BASE = 1.0  # seconds
BATCH_PAUSE_SECONDS = 1.0

# Realistický identifikátor klienta — bez něj Cloudflare před GHL vrací 403 Error 1010
# (default `Python-urllib/X.Y` je na globálním blocklistu).
USER_AGENT = "Mozilla/5.0 (compatible; CliqSales-SalesProspector/1.0; +https://cliqsales.cz)"


# ---------- credential loading (shared with other cs-skills) ----------

def _load_cc_credentials():
    """Locate and import cc_credentials from cs-skills/_lib/."""
    script_path = Path(__file__).resolve()
    skill_dir = script_path.parents[1]
    candidates: list[Path] = [skill_dir.parent / "_lib"]

    for env_name in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw_home = os.environ.get(env_name, "").strip()
        if raw_home:
            home = Path(raw_home).expanduser()
            candidates.append(home / "cs-skills" / "_lib")
            candidates.append(home / ".openclaw" / "cs-skills" / "_lib")

    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
    candidates.extend(parent / "cs-skills" / "_lib" for parent in script_path.parents)

    seen: set[str] = set()
    for lib_dir in candidates:
        key = str(lib_dir)
        if key in seen or not (lib_dir / "cc_credentials.py").exists():
            continue
        seen.add(key)
        if key not in sys.path:
            sys.path.insert(0, key)
        try:
            from cc_credentials import ghl_credentials  # type: ignore
        except Exception:
            continue
        return ghl_credentials
    return None


def get_creds() -> dict[str, str]:
    ghl_credentials = _load_cc_credentials()
    if not ghl_credentials:
        raise SystemExit(
            "ERROR: cc_credentials.py nenalezeno v cs-skills/_lib/. "
            "Skill nemůže resolveovat GHL creds."
        )
    creds = ghl_credentials()
    if not creds or not creds.get("api_key") or not creds.get("location_id"):
        raise SystemExit(
            "ERROR: CliqSales (GoHighLevel) integrace není nakonfigurovaná. "
            "Jdi do Control Center → Nastavení → Integrace → CliqSales (GoHighLevel), "
            "vyplň Private Integration Token (PIT) + Location ID a zkus to znovu."
        )
    return creds


# ---------- CSV parsing ----------

REQUIRED_COLS = {"Company", "Source"}
OPTIONAL_COLS = {"Name", "Email", "Phone", "Web", "Tags", "Uvodni_veta", "Source_URL", "Signal_zajmu"}


def parse_csv(path: Path, row_filter: set[int] | None = None) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"ERROR: CSV soubor neexistuje: {path}")

    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("ERROR: CSV nemá hlavičku.")
        missing = REQUIRED_COLS - set(reader.fieldnames)
        if missing:
            raise SystemExit(f"ERROR: CSV chybí povinné sloupce: {sorted(missing)}")

        rows = []
        for idx, row in enumerate(reader, start=1):
            if row_filter is not None and idx not in row_filter:
                continue
            row["_csv_row"] = str(idx)
            rows.append(row)
    return rows


def validate_row(row: dict[str, str]) -> str | None:
    """Vrátí None pokud row je valid, jinak string s důvodem skipu."""
    email = (row.get("Email") or "").strip()
    phone = (row.get("Phone") or "").strip()
    if not email and not phone:
        return "missing email and phone"
    if not (row.get("Company") or "").strip():
        return "missing company name"
    return None


def parse_row_filter(spec: str | None) -> set[int] | None:
    """Parse '1,3,5-10' → {1,3,5,6,7,8,9,10}."""
    if not spec:
        return None
    result: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start, end = chunk.split("-", 1)
            result.update(range(int(start), int(end) + 1))
        else:
            result.add(int(chunk))
    return result


# ---------- GHL request helpers ----------

def _redact(token: str) -> str:
    """Otisk PAT (prvních 6 znaků + délka) pro logy. Nikdy nevypisuj plnou hodnotu."""
    if not token:
        return "<empty>"
    return f"{token[:6]}…(len={len(token)})"


def ghl_request(
    method: str,
    path: str,
    api_key: str,
    body: dict[str, Any] | None = None,
    query: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any] | None]:
    """Generic GHL request s retry na 429 / 5xx. Vrací (status, json)."""
    url = f"{GHL_API_BASE}{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"

    data: bytes | None = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Version": GHL_API_VERSION,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    last_exc: Exception | None = None
    for attempt in range(RETRY_MAX):
        try:
            req = urllib.request.Request(url, data=data, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                status = resp.status
                payload = resp.read()
                try:
                    return status, json.loads(payload) if payload else None
                except json.JSONDecodeError:
                    return status, None
        except urllib.error.HTTPError as exc:
            status = exc.code
            try:
                body_text = exc.read().decode("utf-8", errors="replace")
            except Exception:
                body_text = ""
            # Detekce Cloudflare 1010 — jasná, akční zpráva místo cryptického HTML body
            if status == 403 and ("Cloudflare" in body_text or "1010" in body_text or "Access denied" in body_text):
                return status, {
                    "error": (
                        "Cloudflare 403 Error 1010 — Access denied. CliqSales API zablokoval "
                        "podpis HTTP klienta. Zkontroluj, že scripts/ghl_contact_upsert.py "
                        "posílá hlavičku User-Agent (proměnná USER_AGENT). "
                        "NEPOKRAČUJ improvizací (vlastní inline Python) — to neobejde "
                        "Cloudflare a poškodí audit deduplikace."
                    )
                }
            if status in (429, 500, 502, 503, 504) and attempt < RETRY_MAX - 1:
                wait = RETRY_BACKOFF_BASE * (2**attempt)
                print(f"  retry {attempt+1}/{RETRY_MAX} after HTTP {status} (wait {wait}s)", file=sys.stderr)
                time.sleep(wait)
                last_exc = exc
                continue
            return status, {"error": body_text[:500]}
        except urllib.error.URLError as exc:
            if attempt < RETRY_MAX - 1:
                wait = RETRY_BACKOFF_BASE * (2**attempt)
                print(f"  retry {attempt+1}/{RETRY_MAX} after network error (wait {wait}s)", file=sys.stderr)
                time.sleep(wait)
                last_exc = exc
                continue
            return 0, {"error": str(exc.reason)}
    return 0, {"error": str(last_exc) if last_exc else "unknown"}


# ---------- mapping ----------

def map_row_to_ghl(row: dict[str, str], location_id: str, default_tags: list[str]) -> dict[str, Any]:
    """Mapuje řádek CSV na payload pro POST /contacts/upsert.

    Politika v1.0: minimalistický payload do CRM.
    - Standardní GHL pole (jméno, firma, e-mail, telefon, web)
    - Jediný tag `sales prospector` (default, pokud uživatel nepředal jiné přes --tags)
    - GHL `source` field = "Sales Prospector" (viditelné v UI kontakt detailu)
    - ŽÁDNÁ vlastní pole (custom fields). CSV sloupce Uvodni_veta, Signal_zajmu,
      Source, Source_URL slouží jen pro lidský přehled v `prospects-review.md`.
    - Sloupec `Tags` z CSV se ignoruje (drž ho prázdný).
    """
    name = (row.get("Name") or "").strip()
    first_name, _, last_name = name.partition(" ")
    if not first_name:
        first_name = (row.get("Company") or "").strip()

    payload: dict[str, Any] = {
        "locationId": location_id,
        "firstName": first_name or None,
        "lastName": last_name or None,
        "companyName": (row.get("Company") or "").strip() or None,
        "email": (row.get("Email") or "").strip() or None,
        "phone": (row.get("Phone") or "").strip() or None,
        "website": (row.get("Web") or "").strip() or None,
        "tags": list(default_tags),
        "source": "Sales Prospector",
    }

    return {k: v for k, v in payload.items() if v is not None}


# ---------- dry-run probe ----------

def search_existing_email(api_key: str, location_id: str, email: str) -> dict[str, bool]:
    """Vrátí {'exists': bool, 'dnd': bool} pro kontakt v dané location."""
    status, body = ghl_request(
        "GET",
        "/contacts/search",
        api_key,
        query={"locationId": location_id, "email": email},
    )
    if status != 200 or not body:
        return {"exists": False, "dnd": False}
    contacts = body.get("contacts") or []
    if not contacts:
        return {"exists": False, "dnd": False}
    first = contacts[0]
    dnd = first.get("dnd") is True
    if not dnd:
        dnd_settings = first.get("dndSettings") or {}
        for channel in ("Call", "SMS", "Email"):
            ch = dnd_settings.get(channel) or {}
            if ch.get("status") == "active":
                dnd = True
                break
    return {"exists": True, "dnd": dnd}


# ---------- main ----------

def main() -> int:
    parser = argparse.ArgumentParser(description="CliqSales (GHL) contact upsert helper")
    parser.add_argument("--csv", required=True, type=Path, help="Path to prospects.csv")
    parser.add_argument("--tags", default="", help="Comma-separated default tags applied to all rows")
    parser.add_argument("--rows", default=None, help="Filter rows by 1-based index (e.g. '1,3,5-10')")
    parser.add_argument("--dry-run", action="store_true", help="No POST calls; only validate + probe existing")
    args = parser.parse_args()

    creds = get_creds()
    api_key = creds["api_key"]
    location_id = creds["location_id"]

    # Default: jediný tag "sales prospector". Uživatel může přebít přes --tags.
    default_tags = [t.strip() for t in args.tags.split(",") if t.strip()] or ["sales prospector"]

    row_filter = parse_row_filter(args.rows)
    rows = parse_csv(args.csv, row_filter)

    print(f"GHL location: {location_id}", file=sys.stderr)
    print(f"PIT: {_redact(api_key)}", file=sys.stderr)
    print(f"Rows to process: {len(rows)}", file=sys.stderr)
    print(f"Default tags: {default_tags}", file=sys.stderr)
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}", file=sys.stderr)
    print("---", file=sys.stderr)

    valid_rows: list[dict[str, str]] = []
    skip_reasons: dict[str, int] = {}
    for row in rows:
        reason = validate_row(row)
        if reason:
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
        else:
            valid_rows.append(row)

    if args.dry_run:
        would_create = 0
        would_update = 0
        dnd_count = 0
        dnd_companies: list[str] = []
        for row in valid_rows:
            email = (row.get("Email") or "").strip()
            if email:
                found = search_existing_email(api_key, location_id, email)
                if found["exists"]:
                    would_update += 1
                    if found["dnd"]:
                        dnd_count += 1
                        if len(dnd_companies) < 10:
                            dnd_companies.append((row.get("Company") or email)[:60])
                else:
                    would_create += 1
            else:
                would_create += 1
            time.sleep(0.1)

        result = {
            "dry_run": True,
            "total_rows": len(rows),
            "valid": len(valid_rows),
            "skipped": sum(skip_reasons.values()),
            "skip_reasons": skip_reasons,
            "would_create": would_create,
            "would_update": would_update,
            "dnd_warning_count": dnd_count,
            "dnd_warning_examples": dnd_companies,
            "tags_to_apply": list(default_tags),
            "estimated_time_seconds": int(len(valid_rows) * 0.3),
        }
        if dnd_count:
            print(
                f"⚠️  Upozornění: {dnd_count} kontaktů z CSV má v CliqSales aktivní příznak DND (nerušit). "
                "Vložení proběhne, ale automatické kampaně (e-mail/SMS/volání) na ně nepůjdou. "
                "Pokud chceš tyto kontakty z CSV vyloučit, použij `--rows` filtr.",
                file=sys.stderr,
            )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    # LIVE upsert
    created = 0
    updated = 0
    failed = 0
    errors: list[dict[str, str]] = []

    for i, row in enumerate(valid_rows, start=1):
        payload = map_row_to_ghl(row, location_id, default_tags)
        status, body = ghl_request("POST", "/contacts/upsert", api_key, body=payload)

        if status in (200, 201) and body:
            if body.get("new"):
                created += 1
            else:
                updated += 1
        else:
            failed += 1
            err_msg = ""
            if isinstance(body, dict):
                err_msg = str(body.get("error") or body)[:200]
            errors.append({
                "csv_row": row.get("_csv_row", "?"),
                "company": (row.get("Company") or "")[:60],
                "http_status": str(status),
                "error": err_msg,
            })

        if i % 10 == 0:
            print(f"  progress: {i}/{len(valid_rows)} (created={created}, updated={updated}, failed={failed})", file=sys.stderr)
            time.sleep(BATCH_PAUSE_SECONDS)

    result = {
        "dry_run": False,
        "total_rows": len(rows),
        "processed": len(valid_rows),
        "skipped": sum(skip_reasons.values()),
        "skip_reasons": skip_reasons,
        "created": created,
        "updated": updated,
        "failed": failed,
        "errors": errors[:20],  # max 20 errors v summary
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if failed == 0 else 4


if __name__ == "__main__":
    sys.exit(main())
