"""Vložení Scout briefu jako poznámky do CliqSales (GoHighLevel) CRM.

Plně autonomní — žádné ptaní uživatele. Default --create-if-missing=true.

Funkce:
  1. Najde kontakt v CliqSales podle contactId / email / phone.
  2. Pokud kontakt neexistuje, automaticky ho vytvoří.
  3. Konvertuje Markdown brief na GHL Rich Text HTML.
  4. Vloží poznámku přes POST /contacts/{id}/notes.
  5. Přidá idempotentní tag `sales scout` (lowercase, s mezerou).
  6. Připíše audit řádek do /documents/sales/.scout-history.jsonl.

Použití:

  # Webhook režim (máme contactId):
  python3 ghl_scout_push.py --contact-id abc123 --note-body-file brief.md

  # Manuální režim (Scout najde nebo vytvoří):
  python3 ghl_scout_push.py --email marek@firma.cz --first-name Marek --last-name Novák \\
      --company "Effect Clinic" --note-body-file brief.md

  # Debug — preview konvertovaného HTML, žádný POST:
  python3 ghl_scout_push.py --contact-id abc123 --note-body-file brief.md --preview-html

  # Audit meta (pro řádek do .scout-history.jsonl):
  python3 ghl_scout_push.py ... --product-mode single --products bioptron-medall \\
      --fit-grades '{"bioptron-medall":"A"}'

Exit codes:
  0 = úspěch
  2 = chybí přístupové údaje
  3 = chyba vstupu
  4 = chyba GHL API
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GHL_API_BASE = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"
TIMEOUT = 20
RETRY_MAX = 3
RETRY_BACKOFF = 1.0

# Realistický User-Agent — bez něj Cloudflare před GHL vrací 403.
USER_AGENT = "Mozilla/5.0 (compatible; CliqSales-SalesScout/1.0; +https://cliqsales.cz)"

# Jediný tag — žádné dynamické, žádné per-produkt
SCOUT_TAG = "sales scout"

# Audit log
DEFAULT_HISTORY_PATH = Path("/documents/sales/.scout-history.jsonl")


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


def get_creds() -> dict[str, str]:
    fn = _load_cc_credentials()
    if not fn:
        print("ERROR: cc_credentials.py nenalezeno v cs-skills/_lib/.", file=sys.stderr)
        sys.exit(2)
    creds = fn()
    if not creds or not creds.get("api_key") or not creds.get("location_id"):
        print(
            "ERROR: CliqSales (GoHighLevel) integrace není nakonfigurovaná. "
            "Jdi do Control Center → Nastavení → Integrace → CliqSales (GoHighLevel), "
            "vyplň Private Integration Token a Location ID.",
            file=sys.stderr,
        )
        sys.exit(2)
    return creds


# ---------- konverze Markdown → GHL Rich Text HTML ----------

def md_to_ghl_html(markdown: str) -> str:
    """Konvertuje Markdown na GHL Rich Text HTML.

    GHL Rich Text v poznámkách podporuje: <strong>, <em>, <u>, <s>, <ul>, <ol>, <li>, <a>, <p>.
    Headings, tabulky, code blocks se převádí na <p><strong> / bullety / <blockquote>.
    Pravidla v references/ghl-html-konverze.md.
    """
    text = markdown.strip()

    # 1) Code blocks (```...```) → <blockquote>
    def _code_block(m):
        return "<blockquote>" + escape_html(m.group(1).strip()) + "</blockquote>"
    text = re.sub(r"```[a-z]*\n?(.*?)```", _code_block, text, flags=re.DOTALL)

    # 2) Tabulky | a | b | → bullet list s bold-prefixem
    text = convert_tables_to_bullets(text)

    # 3) Headings ## / ### / #### → <p><strong>...</strong></p>
    text = re.sub(r"^####\s+(.+)$", r"<p><strong><em>\1</em></strong></p>", text, flags=re.MULTILINE)
    text = re.sub(r"^###\s+(.+)$", r"<p><strong><em>\1</em></strong></p>", text, flags=re.MULTILINE)
    text = re.sub(r"^##\s+(.+)$", r"<p><strong>\1</strong></p>", text, flags=re.MULTILINE)
    text = re.sub(r"^#\s+(.+)$", r"<p><strong>\1</strong></p>", text, flags=re.MULTILINE)

    # 4) Číslované listy: skupiny po sobě jdoucích `N. text` → <ol><li>...</li></ol>
    text = convert_numbered_lists(text)

    # 5) Bullet listy: skupiny po sobě jdoucích `- text` → <ul><li>...</li></ul>
    text = convert_bullet_lists(text)

    # 6) Inline code `code` → <em>code</em>
    text = re.sub(r"`([^`\n]+)`", r"<em>\1</em>", text)

    # 7) Bold **text** → <strong>text</strong>
    text = re.sub(r"\*\*([^\*\n]+)\*\*", r"<strong>\1</strong>", text)

    # 8) Kurzíva *text* nebo _text_ → <em>text</em>
    text = re.sub(r"(?<![\w\*])\*([^\*\n]+)\*(?![\w\*])", r"<em>\1</em>", text)
    text = re.sub(r"(?<![\w_])_([^_\n]+)_(?![\w_])", r"<em>\1</em>", text)

    # 9) Přeškrtnutí ~~text~~ → <s>text</s>
    text = re.sub(r"~~([^~\n]+)~~", r"<s>\1</s>", text)

    # 10) Obrázky ![alt](url) → <a href="url">[obrázek: alt]</a>
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<a href="\2">[obrázek: \1]</a>', text)

    # 11) Odkazy [text](url) → <a href="url">text</a>
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    # 12) Horizontální čára --- → <p>— — —</p>
    text = re.sub(r"^---\s*$", r"<p>— — —</p>", text, flags=re.MULTILINE)

    # 13) Zbylé odstavce — řádky / bloky textu oddělené prázdným řádkem → <p>...</p>
    text = wrap_paragraphs(text)

    return text.strip()


def escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def convert_tables_to_bullets(text: str) -> str:
    """Najde markdown tabulky a převede je na bullety s bold-prefixem."""
    lines = text.split("\n")
    result: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detekce hlavičky tabulky: `| a | b |` následovaný `|---|---|`
        if (
            i + 1 < len(lines)
            and re.match(r"^\s*\|.+\|\s*$", line)
            and re.match(r"^\s*\|[\s\-:|]+\|\s*$", lines[i + 1])
        ):
            headers = [h.strip() for h in line.strip().strip("|").split("|")]
            i += 2  # přeskoč hlavičku + separator
            bullets = []
            while i < len(lines) and re.match(r"^\s*\|.+\|\s*$", lines[i]):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                # Spojit hlavičku a buňku do bullet: **Header:** value | **Header2:** value2 ...
                parts = [f"**{headers[j]}:** {cells[j]}" for j in range(min(len(headers), len(cells))) if cells[j]]
                if parts:
                    bullets.append("- " + " | ".join(parts))
                i += 1
            result.extend(bullets)
            continue
        result.append(line)
        i += 1
    return "\n".join(result)


def convert_bullet_lists(text: str) -> str:
    """Skupiny `- text` převést na <ul><li>...</li></ul>."""
    lines = text.split("\n")
    result: list[str] = []
    i = 0
    while i < len(lines):
        if re.match(r"^\s*-\s+", lines[i]):
            block = []
            while i < len(lines) and re.match(r"^\s*-\s+", lines[i]):
                item = re.sub(r"^\s*-\s+", "", lines[i])
                block.append(f"<li>{item}</li>")
                i += 1
            result.append("<ul>" + "".join(block) + "</ul>")
        else:
            result.append(lines[i])
            i += 1
    return "\n".join(result)


def convert_numbered_lists(text: str) -> str:
    """Skupiny `N. text` převést na <ol><li>...</li></ol>."""
    lines = text.split("\n")
    result: list[str] = []
    i = 0
    while i < len(lines):
        if re.match(r"^\s*\d+\.\s+", lines[i]):
            block = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                item = re.sub(r"^\s*\d+\.\s+", "", lines[i])
                block.append(f"<li>{item}</li>")
                i += 1
            result.append("<ol>" + "".join(block) + "</ol>")
        else:
            result.append(lines[i])
            i += 1
    return "\n".join(result)


def wrap_paragraphs(text: str) -> str:
    """Zbylé bloky textu oddělené prázdným řádkem obal do <p>...</p>."""
    blocks = re.split(r"\n\s*\n", text)
    out = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Pokud blok začíná HTML tagem (z předchozích konverzí), nech tak
        if re.match(r"^\s*<(p|ul|ol|blockquote|h\d)\b", block):
            out.append(block)
        else:
            # Pokud blok obsahuje newline, použij <br/> mezi řádky
            inner = block.replace("\n", "<br/>")
            out.append(f"<p>{inner}</p>")
    return "\n".join(out)


# ---------- GHL API ----------

def _redact(token: str) -> str:
    return f"{token[:6]}…(len={len(token)})" if token else "<empty>"


def ghl_request(method: str, path: str, api_key: str, body: dict | None = None,
                query: dict | None = None) -> tuple[int, dict | None]:
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
    for attempt in range(RETRY_MAX):
        try:
            req = urllib.request.Request(url, data=data, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                payload = resp.read()
                return resp.status, json.loads(payload) if payload else None
        except urllib.error.HTTPError as exc:
            status = exc.code
            try:
                body_text = exc.read().decode("utf-8", errors="replace")
            except Exception:
                body_text = ""
            if status in (429, 500, 502, 503, 504) and attempt < RETRY_MAX - 1:
                wait = RETRY_BACKOFF * (2**attempt)
                print(f"  retry {attempt+1}/{RETRY_MAX} after HTTP {status} (wait {wait}s)", file=sys.stderr)
                time.sleep(wait)
                continue
            return status, {"error": body_text[:500]}
        except urllib.error.URLError as exc:
            if attempt < RETRY_MAX - 1:
                time.sleep(RETRY_BACKOFF * (2**attempt))
                continue
            return 0, {"error": str(exc.reason)}
    return 0, {"error": "unknown"}


def find_contact(api_key: str, location_id: str, email: str | None, phone: str | None) -> str | None:
    for key, value in (("email", email), ("phone", phone)):
        if not value:
            continue
        status, body = ghl_request(
            "GET", "/contacts/search", api_key,
            query={"locationId": location_id, key: value},
        )
        if status == 200 and body and (body.get("contacts") or []):
            return body["contacts"][0].get("id")
    return None


def create_contact(api_key: str, location_id: str, email: str | None, phone: str | None,
                   first_name: str | None, last_name: str | None, company: str | None) -> tuple[str | None, dict | None]:
    payload = {
        "locationId": location_id,
        "firstName": first_name or None,
        "lastName": last_name or None,
        "companyName": company or None,
        "email": email or None,
        "phone": phone or None,
        "source": "Sales Scout",
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    status, body = ghl_request("POST", "/contacts/upsert", api_key, body=payload)
    if status in (200, 201) and body:
        contact = body.get("contact") or {}
        return contact.get("id"), body
    return None, body


def add_note(api_key: str, contact_id: str, html_body: str) -> tuple[bool, dict | None]:
    payload = {"body": html_body}
    status, body = ghl_request("POST", f"/contacts/{contact_id}/notes", api_key, body=payload)
    return status in (200, 201), body


def add_tag(api_key: str, contact_id: str, tag: str = SCOUT_TAG) -> bool:
    """Přidá tag — GHL POST je idempotent, duplicita se neresetuje."""
    payload = {"tags": [tag]}
    status, _ = ghl_request("POST", f"/contacts/{contact_id}/tags", api_key, body=payload)
    return status in (200, 201)


# ---------- audit log ----------

def append_history(history_path: Path, entry: dict) -> bool:
    """Připíše JSON řádek do .scout-history.jsonl. Vytvoří soubor pokud neexistuje."""
    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except OSError as exc:
        print(f"WARN: nelze zapsat do {history_path}: {exc}", file=sys.stderr)
        return False


# ---------- hlavní funkce ----------

def main() -> int:
    parser = argparse.ArgumentParser(description="Vložení Scout briefu do CliqSales CRM")
    parser.add_argument("--contact-id", type=str, help="Existující contactId (webhook režim)")
    parser.add_argument("--email", type=str, help="E-mail pro vyhledání nebo vytvoření")
    parser.add_argument("--phone", type=str, help="Telefon pro vyhledání nebo vytvoření")
    parser.add_argument("--first-name", type=str)
    parser.add_argument("--last-name", type=str)
    parser.add_argument("--company", type=str, help="Název firmy")
    parser.add_argument("--note-body-file", required=True, type=Path, help="Markdown soubor s briefem")
    parser.add_argument("--no-create", action="store_true",
                        help="Pokud kontakt neexistuje, NEvytvářej (default je create-if-missing)")
    parser.add_argument("--no-tag", action="store_true", help="Nepřidávej tag `sales scout`")
    parser.add_argument("--preview-html", action="store_true",
                        help="Vypiš konvertovaný HTML do stderr, neproveď POST")
    parser.add_argument("--history-path", type=Path, default=DEFAULT_HISTORY_PATH,
                        help="Cesta k .scout-history.jsonl (default /documents/sales/.scout-history.jsonl)")
    parser.add_argument("--product-mode", choices=["single", "multi"], default="single",
                        help="Pro audit log — single nebo multi-product brief")
    parser.add_argument("--products", type=str, default="",
                        help="Comma-separated slugy produktů (pro audit log)")
    parser.add_argument("--fit-grades", type=str, default="{}",
                        help='JSON s fit grade per produkt, např. \'{"bioptron-medall":"A"}\' (pro audit log)')
    parser.add_argument("--mode", choices=["webhook", "manual"], default="manual",
                        help="Pro audit log — typ spuštění")
    args = parser.parse_args()

    if not args.contact_id and not args.email and not args.phone:
        print("ERROR: Zadej --contact-id, --email nebo --phone.", file=sys.stderr)
        return 3

    if not args.note_body_file.exists():
        print(f"ERROR: Soubor s briefem neexistuje: {args.note_body_file}", file=sys.stderr)
        return 3

    note_md = args.note_body_file.read_text(encoding="utf-8")
    if not note_md.strip():
        print("ERROR: Soubor s briefem je prázdný.", file=sys.stderr)
        return 3

    # Konverze MD → GHL Rich Text HTML
    html_body = md_to_ghl_html(note_md)

    # Preview režim — žádné POST
    if args.preview_html:
        print("<!-- GHL Rich Text preview -->", file=sys.stderr)
        print(html_body, file=sys.stderr)
        result = {
            "preview": True,
            "html_length": len(html_body),
            "html_first_200": html_body[:200],
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    # Reálný běh — potřebujeme creds
    creds = get_creds()
    api_key = creds["api_key"]
    location_id = creds["location_id"]

    print(f"GHL location: {location_id}", file=sys.stderr)
    print(f"PIT: {_redact(api_key)}", file=sys.stderr)

    # 1. Najít / získat contactId
    contact_id = args.contact_id
    action = "use_existing"
    if not contact_id:
        contact_id = find_contact(api_key, location_id, args.email, args.phone)
        if contact_id:
            action = "found_by_search"
        elif not args.no_create:
            # Default: auto-create
            contact_id, create_body = create_contact(
                api_key, location_id,
                args.email, args.phone,
                args.first_name, args.last_name,
                args.company,
            )
            if not contact_id:
                print(f"ERROR: Vytvoření kontaktu selhalo: {create_body}", file=sys.stderr)
                return 4
            action = "created"
        else:
            print(
                "ERROR: Kontakt v CliqSales neexistuje a --no-create bylo zadáno. Vynech --no-create pro auto-vytvoření.",
                file=sys.stderr,
            )
            return 3

    # 2. Vložit poznámku
    note_ok, note_resp = add_note(api_key, contact_id, html_body)
    if not note_ok:
        print(f"ERROR: Vložení poznámky selhalo: {note_resp}", file=sys.stderr)
        return 4
    note_id = ((note_resp or {}).get("note") or {}).get("id") or ((note_resp or {}).get("id"))

    # 3. Tag (jediný, idempotent)
    tagged = False
    if not args.no_tag:
        tagged = add_tag(api_key, contact_id, SCOUT_TAG)

    # 4. Audit log
    try:
        fit_grades = json.loads(args.fit_grades) if args.fit_grades else {}
    except json.JSONDecodeError:
        fit_grades = {}
    products = [p.strip() for p in args.products.split(",") if p.strip()]
    audit_entry = {
        "date": datetime.now(timezone.utc).isoformat(),
        "contactId": contact_id,
        "firma": args.company or "",
        "email": args.email or "",
        "mode": args.mode,
        "product_mode": args.product_mode,
        "products": products,
        "fit_grades": fit_grades,
        "ghl_note_id": note_id,
        "tagged": tagged,
        "action": action,
    }
    append_history(args.history_path, audit_entry)

    result = {
        "success": True,
        "contactId": contact_id,
        "noteId": note_id,
        "action": action,
        "tagged": tagged,
        "mode": args.mode,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
