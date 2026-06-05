"""Ošetření duplicit pro Sales Prospector skill.

Aplikuje pětivrstvou kontrolu na kandidáty:
  1. Povinná kritéria (předpokládá se, že je už splnili — kontroluje skill v Kroku 4)
  2. Vyřazovací kritéria (totéž — řeší skill v Krok 5 podle profilu)
  3. Černá listina (/documents/sales/blacklist.csv)
  4. Karanténa mezi kampaněmi (/documents/sales/.dedup-history.jsonl)
  5. Kontrola v CliqSales CRM (přes GHL API)

Tento skript dělá vrstvy 3, 4, 5. Vrstvy 1 a 2 si řeší skill sám podle profilu.

Použití:
    python3 dedup_check.py \\
        --candidates kandidati.json \\
        --history /documents/sales/.dedup-history.jsonl \\
        --blacklist /documents/sales/blacklist.csv \\
        --history-window-days 180 \\
        --crm-window-days 180 \\
        --revisit-threshold-days 180

Vstup `kandidati.json` (UTF-8, JSON pole objektů):
    [
      {"email":"info@firma.cz","phone":"+420777123456","ico":"12345678",
       "domain":"firma.cz","company":"Firma s.r.o."},
      ...
    ]

Výstup na stdout (JSON):
    {
      "keep": [...],            # kandidáti, kteří prošli všemi vrstvami
      "drop": [{"index":3,"reasons":["blacklist:domain","crm:recent_180d"]}, ...],
      "revisit": [{"index":5,"last_activity":"2024-08-15","pipeline_stage":"lead"}, ...],
      "summary": {"total":47,"kept":25,"dropped":22,"revisit":3,
                  "by_reason":{"blacklist":2,"history_180d":8,"crm_recent":3,"crm_dnd":1}}
    }

Exit codes:
    0 = úspěch
    2 = chyba přístupu k CliqSales (creds chybí, API auth fail) — ale skript vrátí keep/drop podle vrstev 3+4
    3 = chyba parsování vstupu
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

GHL_API_BASE = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"
TIMEOUT_SECONDS = 20
RETRY_MAX = 3
RETRY_BACKOFF_BASE = 1.0

# Realistický identifikátor klienta — bez něj Cloudflare před GHL vrací 403 Error 1010
# (default `Python-urllib/X.Y` je na globálním blocklistu).
USER_AGENT = "Mozilla/5.0 (compatible; CliqSales-SalesProspector/1.0; +https://cliqsales.cz)"


# ---------- načtení přístupových údajů ----------

def _load_cc_credentials():
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


def get_ghl_creds() -> dict[str, str] | None:
    fn = _load_cc_credentials()
    if not fn:
        return None
    creds = fn()
    if not creds or not creds.get("api_key") or not creds.get("location_id"):
        return None
    return creds


# ---------- normalizace identifikátorů ----------

def norm_email(value: str | None) -> str:
    return (value or "").strip().lower()


def norm_phone(value: str | None) -> str:
    """Normalize na E.164-like: jen číslice a vedoucí '+'."""
    if not value:
        return ""
    raw = value.strip()
    # Default CZ pokud začíná na 9, 6, 7 a má 9 číslic
    digits_only = re.sub(r"[^\d+]", "", raw)
    if digits_only.startswith("+"):
        return "+" + re.sub(r"\D", "", digits_only[1:])
    digits = re.sub(r"\D", "", digits_only)
    if len(digits) == 9 and digits[0] in "679":
        return "+420" + digits
    return "+" + digits if digits else ""


def norm_ico(value: str | None) -> str:
    if not value:
        return ""
    digits = re.sub(r"\D", "", str(value))
    return digits.zfill(8) if digits else ""


def norm_domain(value: str | None) -> str:
    if not value:
        return ""
    raw = value.strip().lower()
    if "@" in raw:
        raw = raw.split("@", 1)[1]
    raw = re.sub(r"^https?://", "", raw)
    raw = raw.split("/", 1)[0]
    return raw.lstrip("www.").strip()


def candidate_keys(c: dict) -> dict[str, str]:
    return {
        "email": norm_email(c.get("email")),
        "phone": norm_phone(c.get("phone")),
        "ico": norm_ico(c.get("ico")),
        "domain": norm_domain(c.get("domain") or c.get("web") or c.get("email")),
    }


# ---------- Vrstva 3 — Černá listina ----------

def load_blacklist(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: (v or "").strip() for k, v in row.items()})
    return rows


def blacklist_match(candidate_keys_norm: dict[str, str], company: str, blacklist: list[dict[str, str]]) -> str | None:
    """Vrátí důvod, pokud kandidát odpovídá záznamu v černé listině."""
    for row in blacklist:
        if row.get("email") and norm_email(row["email"]) == candidate_keys_norm["email"] and candidate_keys_norm["email"]:
            return f"černá listina (e-mail: {row.get('reason', 'bez důvodu')})"
        if row.get("phone") and norm_phone(row["phone"]) == candidate_keys_norm["phone"] and candidate_keys_norm["phone"]:
            return f"černá listina (telefon: {row.get('reason', 'bez důvodu')})"
        if row.get("ico") and norm_ico(row["ico"]) == candidate_keys_norm["ico"] and candidate_keys_norm["ico"]:
            return f"černá listina (IČO: {row.get('reason', 'bez důvodu')})"
        if row.get("domain") and norm_domain(row["domain"]) == candidate_keys_norm["domain"] and candidate_keys_norm["domain"]:
            return f"černá listina (doména: {row.get('reason', 'bez důvodu')})"
        pattern = row.get("company_pattern")
        if pattern and company:
            try:
                regex_pattern = pattern.replace("*", ".*")
                if re.search(regex_pattern, company, re.IGNORECASE):
                    return f"černá listina (název: {row.get('reason', 'bez důvodu')})"
            except re.error:
                continue
    return None


# ---------- Vrstva 4 — Karanténa mezi kampaněmi ----------

def load_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    parse_errors = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                parse_errors += 1
    if parse_errors:
        print(f"⚠️  dedup-history.jsonl: {parse_errors} vadné řádky, přeskočeno", file=sys.stderr)
    return entries


def history_match(
    candidate_keys_norm: dict[str, str],
    history: list[dict[str, Any]],
    window_days: int,
) -> str | None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    for entry in history:
        date_str = entry.get("date") or ""
        try:
            entry_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        if entry_date < cutoff:
            continue

        e_email = norm_email(entry.get("email"))
        e_phone = norm_phone(entry.get("phone"))
        e_ico = norm_ico(entry.get("ico"))
        e_domain = norm_domain(entry.get("domain"))

        if e_email and e_email == candidate_keys_norm["email"]:
            return f"karanténa kampaně {window_days}d (e-mail, kampaň: {entry.get('campaign', '?')}, {date_str})"
        if e_ico and e_ico == candidate_keys_norm["ico"]:
            return f"karanténa kampaně {window_days}d (IČO, kampaň: {entry.get('campaign', '?')}, {date_str})"
        if e_phone and e_phone == candidate_keys_norm["phone"]:
            return f"karanténa kampaně {window_days}d (telefon, kampaň: {entry.get('campaign', '?')}, {date_str})"
    return None


# ---------- Vrstva 5 — CliqSales CRM ----------

def ghl_search_contact(api_key: str, location_id: str, email: str, phone: str) -> dict[str, Any] | None:
    """Hledá kontakt v CliqSales podle e-mailu nebo telefonu. Vrátí první match nebo None."""
    for key, value in (("email", email), ("phone", phone)):
        if not value:
            continue
        query = {"locationId": location_id, key: value}
        url = f"{GHL_API_BASE}/contacts/search?{urllib.parse.urlencode(query)}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Version": GHL_API_VERSION,
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        for attempt in range(RETRY_MAX):
            try:
                req = urllib.request.Request(url, method="GET", headers=headers)
                with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                    body = json.loads(resp.read() or b"{}")
                    contacts = body.get("contacts") or []
                    if contacts:
                        return contacts[0]
                    break
            except urllib.error.HTTPError as exc:
                # Cloudflare 1010 — okamžitě raise, ať skill nezakrývá problém
                if exc.code == 403:
                    try:
                        body_text = exc.read().decode("utf-8", errors="replace")
                    except Exception:
                        body_text = ""
                    if "Cloudflare" in body_text or "1010" in body_text or "Access denied" in body_text:
                        raise SystemExit(
                            "Cloudflare 403 Error 1010 — Access denied. "
                            "CliqSales API zablokoval podpis HTTP klienta. "
                            "Zkontroluj proměnnou USER_AGENT v scripts/dedup_check.py."
                        )
                if exc.code in (429, 500, 502, 503, 504) and attempt < RETRY_MAX - 1:
                    time.sleep(RETRY_BACKOFF_BASE * (2**attempt))
                    continue
                return None
            except urllib.error.URLError:
                if attempt < RETRY_MAX - 1:
                    time.sleep(RETRY_BACKOFF_BASE * (2**attempt))
                    continue
                return None
    return None


def crm_decision(
    contact: dict[str, Any] | None,
    crm_window_days: int,
    revisit_threshold_days: int,
) -> tuple[str, dict[str, Any] | None]:
    """Vrátí (verdict, revisit_info).

    verdict ∈ {'keep', 'drop:dnd', 'drop:recent', 'revisit'}
    revisit_info — None nebo {"last_activity":..., "pipeline_stage":...} pro tag [PROBĚHL DLOUHO]
    """
    if not contact:
        return "keep", None

    if contact.get("dnd") is True:
        return "drop:dnd", None
    dnd_settings = contact.get("dndSettings") or {}
    for channel in ("Call", "SMS", "Email"):
        ch = dnd_settings.get(channel) or {}
        if ch.get("status") == "active":
            return "drop:dnd", None

    last_activity_str = contact.get("lastActivity") or contact.get("dateUpdated") or contact.get("dateAdded")
    if last_activity_str:
        try:
            last_activity = datetime.fromisoformat(last_activity_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            last_activity = None
    else:
        last_activity = None

    if not last_activity:
        return "keep", None

    now = datetime.now(timezone.utc)
    days_ago = (now - last_activity).days

    if days_ago < crm_window_days:
        return "drop:recent", None

    if days_ago >= revisit_threshold_days:
        pipeline_stage = contact.get("pipelineStageName") or contact.get("pipelineStage") or "?"
        if pipeline_stage in ("won", "lost"):
            return "drop:recent", None
        return "revisit", {
            "last_activity": last_activity_str,
            "pipeline_stage": pipeline_stage,
            "days_ago": days_ago,
        }

    return "keep", None


# ---------- hlavní funkce ----------

def main() -> int:
    parser = argparse.ArgumentParser(description="Ošetření duplicit pro Sales Prospector")
    parser.add_argument("--candidates", required=True, type=Path, help="JSON soubor s kandidáty")
    parser.add_argument("--history", type=Path, default=Path("/documents/sales/.dedup-history.jsonl"))
    parser.add_argument("--blacklist", type=Path, default=Path("/documents/sales/blacklist.csv"))
    parser.add_argument("--history-window-days", type=int, default=180)
    parser.add_argument("--crm-window-days", type=int, default=180)
    parser.add_argument("--revisit-threshold-days", type=int, default=180)
    parser.add_argument("--skip-crm", action="store_true", help="Přeskočit vrstvu 5 (CRM check)")
    args = parser.parse_args()

    try:
        candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
        assert isinstance(candidates, list)
    except (json.JSONDecodeError, AssertionError, OSError) as exc:
        print(f"ERROR: Vstupní soubor nelze přečíst jako JSON pole: {exc}", file=sys.stderr)
        return 3

    blacklist = load_blacklist(args.blacklist)
    history = load_history(args.history)

    creds = None
    if not args.skip_crm:
        creds = get_ghl_creds()
        if not creds:
            print(
                "⚠️  Vrstva 5 přeskočena — CliqSales integrace není nastavená. "
                "Riziko duplikátů zůstává.",
                file=sys.stderr,
            )

    keep: list[int] = []
    drop: list[dict[str, Any]] = []
    revisit: list[dict[str, Any]] = []
    by_reason: dict[str, int] = {}

    for idx, candidate in enumerate(candidates):
        keys_norm = candidate_keys(candidate)
        company = candidate.get("company", "")
        reasons: list[str] = []

        # Vrstva 3 — Černá listina
        bl_reason = blacklist_match(keys_norm, company, blacklist)
        if bl_reason:
            reasons.append(bl_reason)
            by_reason["blacklist"] = by_reason.get("blacklist", 0) + 1

        # Vrstva 4 — Karanténa kampaní
        if not reasons:
            hist_reason = history_match(keys_norm, history, args.history_window_days)
            if hist_reason:
                reasons.append(hist_reason)
                by_reason[f"history_{args.history_window_days}d"] = by_reason.get(f"history_{args.history_window_days}d", 0) + 1

        # Vrstva 5 — CliqSales CRM
        if not reasons and creds:
            contact = ghl_search_contact(creds["api_key"], creds["location_id"], keys_norm["email"], keys_norm["phone"])
            verdict, revisit_info = crm_decision(contact, args.crm_window_days, args.revisit_threshold_days)
            if verdict == "drop:dnd":
                reasons.append("DND v CliqSales (nerušit)")
                by_reason["crm_dnd"] = by_reason.get("crm_dnd", 0) + 1
            elif verdict == "drop:recent":
                reasons.append(f"nedávno v CRM (poslední {args.crm_window_days}d)")
                by_reason["crm_recent"] = by_reason.get("crm_recent", 0) + 1
            elif verdict == "revisit":
                revisit.append({"index": idx, **(revisit_info or {})})
                by_reason["revisit"] = by_reason.get("revisit", 0) + 1
                keep.append(idx)
                continue
            # mírná pauza, GHL rate limit (100 req / 10s)
            time.sleep(0.12)

        if reasons:
            drop.append({"index": idx, "reasons": reasons})
        else:
            keep.append(idx)

    result = {
        "keep": keep,
        "drop": drop,
        "revisit": revisit,
        "summary": {
            "total": len(candidates),
            "kept": len(keep),
            "dropped": len(drop),
            "revisit": len(revisit),
            "by_reason": by_reason,
        },
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
