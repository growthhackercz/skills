#!/usr/bin/env python3
"""
Google Search Console query helper pro skill google-search-console.

Auth: service account JWT bearer flow — bez pip závislostí (stdlib + openssl CLI).
Stejný service account jako google-analytics, jen jiný scope (webmasters.readonly)
a jiný zdroj (Search Console API).

Credentials (v tomto pořadí):
  1. env GA_SERVICE_ACCOUNT_JSON  (celý service account JSON, minified — sdílený s GA)
  2. env GA4_CLIENT_EMAIL + GA4_PRIVATE_KEY  (split varianta)
  3. Control Center custom variables přes cc_credentials helper (fallback)
Vždy: GSC_SITE_URL (adresa property v Search Console, např. "sc-domain:vasedomena.cz"
       nebo "https://vasedomena.cz/").

Použití:
  gsc_query.py queries [--days 28] [--limit 20] [--path /blog]
  gsc_query.py pages [--days 28] [--limit 20]
  gsc_query.py page-detail --url /blog/muj-clanek [--days 28]
  gsc_query.py rank-tracking --keywords "jak vybrat x,cena y" [--days 28]
  gsc_query.py weekly-summary          # JSON pro seo-strategist / obsahový report
  Společné: --format table|json (default table)
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
API_BASE = "https://searchconsole.googleapis.com/webmasters/v3"

NAVOD = (
    "Chybí přístup ke Google Search Console. Postup nastavení (jednou):\n"
    "  1. Použijte stejný service account jako pro Google Analytics (nebo vytvořte\n"
    "     nový v Google Cloud a stáhněte JSON klíč).\n"
    "  2. V Search Console (search.google.com/search-console): Nastavení →\n"
    "     Uživatelé a oprávnění → Přidat uživatele → e-mail service accountu →\n"
    "     oprávnění Úplné nebo Omezené.\n"
    "  3. V AI Teamu: Nastavení → Integrace → vložte celý JSON jako\n"
    "     GA_SERVICE_ACCOUNT_JSON a adresu webu jako GSC_SITE_URL\n"
    "     (např. sc-domain:vasedomena.cz nebo https://vasedomena.cz/).\n"
    "  4. Hotovo — zeptejte se agenta: „Na jaká slova nás lidé najdou?“"
)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _fail(msg: str, code: int = 2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def _cc_variable(name: str):
    try:
        sys.path.insert(0, "/home/node/.openclaw/cs-skills/_lib")
        from cc_credentials import get_variable  # type: ignore
        return get_variable(name)
    except Exception:
        return None


def load_credentials():
    """Vrátí (client_email, private_key_pem, site_url)."""
    raw = _cc_variable("GA_SERVICE_ACCOUNT_JSON") or os.environ.get("GA_SERVICE_ACCOUNT_JSON")
    email = _cc_variable("GA4_CLIENT_EMAIL") or os.environ.get("GA4_CLIENT_EMAIL")
    key = _cc_variable("GA4_PRIVATE_KEY") or os.environ.get("GA4_PRIVATE_KEY")
    site = _cc_variable("GSC_SITE_URL") or os.environ.get("GSC_SITE_URL")

    if raw:
        try:
            sa = json.loads(raw)
            email = sa.get("client_email") or email
            key = sa.get("private_key") or key
        except json.JSONDecodeError:
            _fail("GA_SERVICE_ACCOUNT_JSON není platný JSON — vložte celý obsah staženého souboru klíče.\n\n" + NAVOD)

    if key:
        key = key.replace("\\n", "\n")
    if not (email and key):
        _fail(NAVOD)
    if not site:
        _fail("Chybí GSC_SITE_URL (adresa webu v Search Console).\n"
              "Např. sc-domain:vasedomena.cz (doménová property) nebo https://vasedomena.cz/ (s lomítkem).\n"
              "Vložte do Nastavení → Integrace.")
    return email, key, str(site).strip()


def get_access_token(email: str, key_pem: str) -> str:
    now = int(time.time())
    header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claims = _b64url(json.dumps({
        "iss": email, "scope": SCOPE, "aud": TOKEN_URL, "iat": now, "exp": now + 3600,
    }).encode())
    signing_input = f"{header}.{claims}".encode()

    fd, keyfile = tempfile.mkstemp(suffix=".pem")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(key_pem)
        proc = subprocess.run(["openssl", "dgst", "-sha256", "-sign", keyfile],
                              input=signing_input, capture_output=True)
        if proc.returncode != 0:
            _fail("Podpis klíče selhal — private key v integracích vypadá poškozený (zkopírujte celý JSON znovu).")
        signature = proc.stdout
    finally:
        try:
            os.unlink(keyfile)
        except OSError:
            pass

    jwt = signing_input.decode() + "." + _b64url(signature)
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)["access_token"]
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        if "invalid_grant" in detail:
            _fail("Google klíč nepřijal (invalid_grant) — nejčastěji smazaný service account nebo špatně vložený JSON. Vložte klíč do Integrací znovu.")
        _fail(f"Přihlášení ke Google selhalo (HTTP {e.code}). Zkuste to za chvíli znovu.")


def query_sa(token: str, site: str, body: dict) -> dict:
    url = f"{API_BASE}/sites/{urllib.parse.quote(site, safe='')}/searchAnalytics/query"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 403:
            _fail("Search Console odmítl přístup (403).\nNejčastější příčina: e-mail service accountu není přidaný v Search Console.\nSearch Console → Nastavení → Uživatelé a oprávnění → Přidat uživatele (e-mail končí na .iam.gserviceaccount.com).")
        if e.code == 404:
            _fail(f"Web {site} nenalezen (404) — zkontrolujte GSC_SITE_URL.\nDoménová property: sc-domain:vasedomena.cz · URL property: https://vasedomena.cz/ (přesně jak je v Search Console, i s lomítkem).")
        if e.code == 429:
            _fail("Search Console hlásí příliš mnoho dotazů (429). Zkuste to za pár minut.")
        _fail(f"Dotaz na Search Console selhal (HTTP {e.code}): {e.read().decode(errors='replace')[:200]}")


def date_range(days: int):
    # GSC data mají ~2-3denní zpoždění → posuň okno o 3 dny zpět
    end = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 3 * 86400))
    start = time.strftime("%Y-%m-%d", time.gmtime(time.time() - (days + 3) * 86400))
    return start, end


def rows(data: dict, keys: list) -> list:
    out = []
    for r in data.get("rows", []):
        rec = {}
        for i, k in enumerate(keys):
            rec[k] = r.get("keys", [])[i] if i < len(r.get("keys", [])) else ""
        rec["imprese"] = int(r.get("impressions", 0))
        rec["prokliky"] = int(r.get("clicks", 0))
        rec["CTR"] = f"{r.get('ctr', 0) * 100:.1f} %"
        rec["pozice"] = round(r.get("position", 0), 1)
        out.append(rec)
    return out


def emit(records, fmt):
    if fmt == "json":
        print(json.dumps(records, ensure_ascii=False, indent=2))
    else:
        if not records:
            print("(žádná data — u nové property se data načítají několik dní)")
            return
        cols = list(records[0].keys())
        w = {c: max(len(str(c)), *(len(str(r[c])) for r in records)) for c in cols}
        print("  ".join(str(c).ljust(w[c]) for c in cols))
        print("  ".join("-" * w[c] for c in cols))
        for r in records:
            print("  ".join(str(r[c]).ljust(w[c]) for c in cols))


def _base(days, dims):
    s, e = date_range(days)
    return {"startDate": s, "endDate": e, "dimensions": dims, "rowLimit": 25000}


def cmd_queries(token, site, args):
    body = _base(args.days, ["query"])
    body["rowLimit"] = args.limit
    if args.path:
        body["dimensionFilterGroups"] = [{"filters": [
            {"dimension": "page", "operator": "contains", "expression": args.path}]}]
    emit(rows(query_sa(token, site, body), ["query"]), args.format)


def cmd_pages(token, site, args):
    body = _base(args.days, ["page"])
    body["rowLimit"] = args.limit
    emit(rows(query_sa(token, site, body), ["page"]), args.format)


def cmd_page_detail(token, site, args):
    if not args.url:
        _fail("--url je povinné (cesta nebo celá adresa stránky)")
    body = _base(args.days, ["query"])
    body["rowLimit"] = args.limit
    body["dimensionFilterGroups"] = [{"filters": [
        {"dimension": "page", "operator": "contains", "expression": args.url}]}]
    emit(rows(query_sa(token, site, body), ["query"]), args.format)


def cmd_rank_tracking(token, site, args):
    if not args.keywords:
        _fail("--keywords je povinné (klíčová slova oddělená čárkou)")
    wanted = [k.strip().lower() for k in args.keywords.split(",") if k.strip()]
    body = _base(args.days, ["query"])
    all_rows = rows(query_sa(token, site, body), ["query"])
    idx = {r["query"].lower(): r for r in all_rows}
    out = []
    for kw in wanted:
        r = idx.get(kw)
        out.append(r if r else {"query": kw, "imprese": 0, "prokliky": 0, "CTR": "—", "pozice": "mimo top"})
    emit(out, args.format)


def cmd_weekly_summary(token, site, args):
    q = rows(query_sa(token, site, {**_base(7, ["query"]), "rowLimit": 10}), ["query"])
    p = rows(query_sa(token, site, {**_base(7, ["page"]), "rowLimit": 10}), ["page"])
    tot = query_sa(token, site, _base(7, []))
    agg = tot.get("rows", [{}])
    total = agg[0] if agg else {}
    print(json.dumps({
        "period_days": 7,
        "total_clicks": int(total.get("clicks", 0)),
        "total_impressions": int(total.get("impressions", 0)),
        "avg_position": round(total.get("position", 0), 1),
        "top_queries": q, "top_pages": p,
    }, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Google Search Console query helper")
    ap.add_argument("command", choices=["queries", "pages", "page-detail",
                                        "rank-tracking", "weekly-summary"])
    ap.add_argument("--days", type=int, default=28)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--path", default=None)
    ap.add_argument("--url", default=None)
    ap.add_argument("--keywords", default=None)
    ap.add_argument("--format", choices=["table", "json"], default="table")
    args = ap.parse_args()

    email, key, site = load_credentials()
    token = get_access_token(email, key)
    {
        "queries": cmd_queries, "pages": cmd_pages, "page-detail": cmd_page_detail,
        "rank-tracking": cmd_rank_tracking, "weekly-summary": cmd_weekly_summary,
    }[args.command](token, site, args)


if __name__ == "__main__":
    main()
