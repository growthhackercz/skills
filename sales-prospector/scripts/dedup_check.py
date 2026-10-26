"""Ošetření duplicit pro Sales Prospector skill.

Aplikuje pětivrstvou kontrolu na kandidáty:
  1. Povinná kritéria (předpokládá se, že je už splnili — kontroluje skill v Kroku 4)
  2. Vyřazovací kritéria (totéž — řeší skill v Krok 5 podle profilu)
  3. Černá listina (/documents/sales/blacklist.csv)
  4. Karanténa mezi kampaněmi (/documents/sales/.dedup-history.jsonl)
  5. Kontrola v CliqSales CRM (přes omezený tenantní read helper)

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
    2 = GHL read připojení není dostupné; kontrola končí fail-closed
    3 = chyba parsování vstupu
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SHARED_LIB = Path(__file__).resolve().parents[2] / "_lib"


def _sales_plan():
    script_path = Path(__file__).resolve()
    candidates: list[Path] = [SHARED_LIB]
    for env_name in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw_home = (os.environ.get(env_name) or "").strip()
        if raw_home:
            home = Path(raw_home).expanduser()
            candidates.extend((home / "cs-skills" / "_lib", home / ".openclaw" / "cs-skills" / "_lib"))
    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
    candidates.extend(parent / "cs-skills" / "_lib" for parent in script_path.parents)
    seen: set[str] = set()
    for lib_dir in candidates:
        key = str(lib_dir)
        if key in seen or not (lib_dir / "sales_ghl_plan.py").is_file():
            continue
        seen.add(key)
        if key not in sys.path:
            sys.path.insert(0, key)
        try:
            import sales_ghl_plan  # type: ignore
        except Exception:
            continue
        return sales_ghl_plan
    raise RuntimeError("sdílený Sales GHL read helper není dostupný")


def _prospect_package():
    script_path = Path(__file__).resolve()
    candidates: list[Path] = [SHARED_LIB]
    for env_name in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw_home = (os.environ.get(env_name) or "").strip()
        if raw_home:
            home = Path(raw_home).expanduser()
            candidates.extend((home / "cs-skills" / "_lib", home / ".openclaw" / "cs-skills" / "_lib"))
    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
    candidates.extend(parent / "cs-skills" / "_lib" for parent in script_path.parents)
    seen: set[str] = set()
    for lib_dir in candidates:
        key = str(lib_dir)
        if key in seen or not (lib_dir / "sales_prospect_package.py").is_file():
            continue
        seen.add(key)
        if key not in sys.path:
            sys.path.insert(0, key)
        try:
            import sales_prospect_package  # type: ignore
        except Exception:
            continue
        return sales_prospect_package
    raise RuntimeError("sdílený Sales market helper není dostupný")


def _ghl_contacts(
    identity_type: str, value: str, *, profile: str
) -> list[dict[str, Any]]:
    return _sales_plan().lookup_contact_exact(identity_type, value, profile=profile)


# ---------- normalizace identifikátorů ----------

def norm_email(value: str | None) -> str:
    return str(value or "").strip().lower()


def norm_phone(value: str | None, market: str = "CZ") -> str:
    if not value:
        return ""
    return _prospect_package().normalize_phone(value, market)


def safe_norm_phone(value: Any, market: str) -> str:
    """Normalize untrusted legacy/provider data without crashing the batch."""
    try:
        return norm_phone(value, market)
    except (TypeError, ValueError):
        return ""


def norm_ico(value: str | None) -> str:
    if not value:
        return ""
    digits = re.sub(r"\D", "", str(value))
    return digits.zfill(8) if digits else ""


def norm_registry_id(value: str | None, identifier_type: str | None, market: str) -> tuple[str, str]:
    return _prospect_package().normalize_registry_id(value, identifier_type, market)


def norm_domain(value: str | None) -> str:
    if not value:
        return ""
    raw = str(value).strip().lower()
    if "@" in raw:
        raw = raw.split("@", 1)[1]
    raw = re.sub(r"^https?://", "", raw)
    raw = raw.split("/", 1)[0]
    if raw.startswith("www."):
        raw = raw[4:]
    return raw.strip()


def candidate_keys(c: dict) -> dict[str, str]:
    market = str(c.get("market") or c.get("Market") or "CZ").strip().upper()
    registry_type = c.get("registry_id_type") or c.get("RegistryIdType")
    registry_id = c.get("registry_id") or c.get("RegistryId")
    if not registry_id and c.get("ico"):
        registry_type, registry_id = "ico", c.get("ico")
    registry_type, registry_id = norm_registry_id(registry_id, registry_type, market)
    return {
        "market": market,
        "email": norm_email(c.get("email")),
        "phone": norm_phone(c.get("phone"), market),
        "registry_id_type": registry_type,
        "registry_id": registry_id,
        "ico": registry_id if registry_type == "ico" else "",
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
        explicit_market = str(row.get("market") or "").strip().upper()
        legacy_cz_identity = bool(row.get("phone") or row.get("ico"))
        row_market = explicit_market or ("CZ" if legacy_cz_identity else candidate_keys_norm["market"])
        if row_market != candidate_keys_norm["market"]:
            continue
        if row.get("email") and norm_email(row["email"]) == candidate_keys_norm["email"] and candidate_keys_norm["email"]:
            return f"černá listina (e-mail: {row.get('reason', 'bez důvodu')})"
        if row.get("phone") and safe_norm_phone(row["phone"], row_market) == candidate_keys_norm["phone"] and candidate_keys_norm["phone"]:
            return f"černá listina (telefon: {row.get('reason', 'bez důvodu')})"
        row_registry_type = row.get("registry_id_type") or ("ico" if row.get("ico") else "")
        row_registry_id = row.get("registry_id") or row.get("ico")
        if row_registry_id and (explicit_market or row.get("ico")):
            try:
                normalized_type, normalized_id = norm_registry_id(row_registry_id, row_registry_type, row_market)
            except ValueError:
                normalized_type, normalized_id = "", ""
            if (
                normalized_id
                and normalized_type == candidate_keys_norm["registry_id_type"]
                and normalized_id == candidate_keys_norm["registry_id"]
            ):
                return f"černá listina (registry ID: {row.get('reason', 'bez důvodu')})"
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
                entry = json.loads(line)
                if not isinstance(entry, dict):
                    raise ValueError("history row must be an object")
                entries.append(entry)
            except (json.JSONDecodeError, ValueError):
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
        if e_email and e_email == candidate_keys_norm["email"]:
            return f"karanténa kampaně {window_days}d (e-mail, kampaň: {entry.get('campaign', '?')}, {date_str})"
        entry_market = str(entry.get("market") or "CZ").strip().upper()
        if entry_market != candidate_keys_norm["market"]:
            continue
        e_phone = safe_norm_phone(entry.get("phone"), entry_market)
        entry_type = entry.get("registry_id_type") or ("ico" if entry.get("ico") else "")
        entry_id = entry.get("registry_id") or entry.get("ico")
        try:
            e_type, e_registry = norm_registry_id(entry_id, entry_type, entry_market)
        except ValueError:
            e_type, e_registry = "", ""

        if (
            e_registry
            and e_type == candidate_keys_norm["registry_id_type"]
            and e_registry == candidate_keys_norm["registry_id"]
        ):
            return f"karanténa kampaně {window_days}d (registry ID, kampaň: {entry.get('campaign', '?')}, {date_str})"
        if e_phone and e_phone == candidate_keys_norm["phone"]:
            return f"karanténa kampaně {window_days}d (telefon, kampaň: {entry.get('campaign', '?')}, {date_str})"
    return None


# ---------- Vrstva 5 — CliqSales CRM ----------

def ghl_search_contact(
    email: str, phone: str, *, profile: str, market: str = "CZ"
) -> tuple[str, dict[str, Any] | None]:
    """Hledá kontakt přes exact tenantní GHL read podle e-mailu nebo telefonu.

    Vrací (state, contact) se state ∈ {found, not_found, unknown}.

    Audit P1-03: dřív se vracelo `None` jak při chybě spojení, tak když
    kontakt v CRM prostě není. Volající to nedokázal rozlišit — timeout se
    tvářil jako „čistý lead" a kandidát prošel do outboundu.
    """
    exact_by_id: dict[str, dict[str, Any]] = {}
    for key, value in (("email", email), ("phone", phone)):
        if not value:
            continue
        try:
            contacts = _ghl_contacts(key, value, profile=profile)
        except Exception:
            return "unknown", None
        if key == "email":
            matches = [
                c for c in contacts
                if any(
                    norm_email(candidate) == norm_email(value)
                    for candidate in [c.get("email"), *(c.get("additionalEmails") or [])]
                )
            ]
        else:
            try:
                wanted_phone = norm_phone(value, market)
            except (TypeError, ValueError):
                return "unknown", None
            matches = [
                c for c in contacts
                if any(
                    safe_norm_phone(candidate, market) == wanted_phone
                    for candidate in [c.get("phone"), *(c.get("additionalPhones") or [])]
                    if candidate
                )
            ]
        if len(matches) > 1:
            return "unknown", None
        if len(matches) == 1 and matches[0].get("id"):
            exact_by_id[str(matches[0]["id"])] = matches[0]
    if len(exact_by_id) > 1:
        return "unknown", None
    if len(exact_by_id) == 1:
        return "found", next(iter(exact_by_id.values()))
    return "not_found", None


def crm_decision(
    state: str,
    contact: dict[str, Any] | None,
    crm_window_days: int,
    revisit_threshold_days: int,
) -> tuple[str, dict[str, Any] | None]:
    """Vrátí (verdict, revisit_info).

    verdict ∈ {'keep', 'unknown', 'drop:dnd', 'drop:recent', 'revisit'}
    revisit_info — None nebo {"last_activity":..., "pipeline_stage":...} pro tag [PROBĚHL DLOUHO]
    """
    if state == "unknown":
        # Neznámý stav CRM nesmí kandidáta pustit do outboundu.
        return "unknown", None
    if not contact:
        # HTTP 200 a prázdno → v CRM opravdu není → čistý lead.
        return "keep", None

    if contact.get("dnd") is True:
        return "drop:dnd", None
    dnd_settings = contact.get("dndSettings") or {}
    normalized_dnd = {str(key).lower(): value for key, value in dnd_settings.items()}
    for channel in ("call", "sms", "email"):
        ch = normalized_dnd.get(channel) or {}
        if str(ch.get("status") or "").lower() == "active":
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
    parser.add_argument("--credential-profile", default="default")
    parser.add_argument(
        "--skip-crm",
        action="store_true",
        help="Deprecated safety flag; prospecting may not bypass CRM deduplication",
    )
    args = parser.parse_args()

    try:
        candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
        assert isinstance(candidates, list)
    except (json.JSONDecodeError, AssertionError, OSError) as exc:
        print(f"ERROR: Vstupní soubor nelze přečíst jako JSON pole: {exc}", file=sys.stderr)
        return 3

    blacklist = load_blacklist(args.blacklist)
    history = load_history(args.history)

    try:
        normalized_keys = [candidate_keys(candidate) for candidate in candidates]
    except (TypeError, ValueError) as exc:
        print(f"ERROR: Kandidát nemá platný market/identifikátory: {exc}", file=sys.stderr)
        return 3

    if args.skip_crm:
        print(
            "ERROR: --skip-crm je z bezpečnostních důvodů vypnuté. "
            "Bez GHL read připojení nelze kandidáty pro outbound schválit.",
            file=sys.stderr,
        )
        return 2
    try:
        # Fail before processing any candidate if the tenant integration is missing.
        _ghl_probe = _ghl_contacts(
            "email",
            "sales-read-preflight-no-match@example.invalid",
            profile=args.credential_profile,
        )
        del _ghl_probe
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    keep: list[int] = []
    drop: list[dict[str, Any]] = []
    revisit: list[dict[str, Any]] = []
    retry: list[dict[str, Any]] = []  # audit P1-03: stav CRM neznámý → k opakování
    by_reason: dict[str, int] = {}
    crm_checked = 0
    crm_unknown = 0
    crm_observed_at = datetime.now(timezone.utc).isoformat()

    for idx, candidate in enumerate(candidates):
        keys_norm = normalized_keys[idx]
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
        if not reasons:
            crm_checked += 1
            crm_state, contact = ghl_search_contact(
                keys_norm["email"],
                keys_norm["phone"],
                profile=args.credential_profile,
                market=keys_norm["market"],
            )
            crm_observed_at = datetime.now(timezone.utc).isoformat()
            verdict, revisit_info = crm_decision(crm_state, contact, args.crm_window_days, args.revisit_threshold_days)
            if verdict == "drop:dnd":
                reasons.append("DND v CliqSales (nerušit)")
                by_reason["crm_dnd"] = by_reason.get("crm_dnd", 0) + 1
            elif verdict == "drop:recent":
                reasons.append(f"nedávno v CRM (poslední {args.crm_window_days}d)")
                by_reason["crm_recent"] = by_reason.get("crm_recent", 0) + 1
            elif verdict == "unknown":
                crm_unknown += 1
                # Audit P1-03: stav v CRM nevíme (timeout / 429 / 5xx).
                # Nepouští se do outboundu, ale ani nekončí mezi zahozenými —
                # jde do vlastního bucketu `retry` k opakování, až bude CRM
                # dostupné. Kdyby padl do `drop`, výpadek CRM by tiše vykázal
                # celou dávku jako vyřazenou.
                retry.append({"index": idx, "reason": "stav v CRM neznámý (CRM nedostupné)"})
                by_reason["crm_unknown"] = by_reason.get("crm_unknown", 0) + 1
                continue
            elif verdict == "revisit":
                revisit.append({"index": idx, **(revisit_info or {})})
                by_reason["revisit"] = by_reason.get("revisit", 0) + 1
                keep.append(idx)
                continue

        if reasons:
            drop.append({"index": idx, "reasons": reasons})
        else:
            keep.append(idx)

    result = {
        "keep": keep,
        "drop": drop,
        "revisit": revisit,
        "retry": retry,
        "summary": {
            "total": len(candidates),
            "kept": len(keep),
            "dropped": len(drop),
            "revisit": len(revisit),
            "retry": len(retry),
            "by_reason": by_reason,
        },
        "crm_dedup": {
            "status": "complete" if not retry else "unknown",
            "observedAt": crm_observed_at,
            "checked": crm_checked,
            "unknown": crm_unknown,
        },
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not retry else 2


if __name__ == "__main__":
    sys.exit(main())
