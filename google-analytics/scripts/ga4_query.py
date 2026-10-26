#!/usr/bin/env python3
"""
GA4 query helper pro skill google-analytics.

Auth: service account JWT bearer flow — bez pip závislostí (stdlib + openssl CLI).
Credentials (v tomto pořadí):
  1. Control Center proměnné (Nastavení → Integrace → Vlastní proměnné) — to,
     co klient vidí v UI, vždy vyhrává
  2. env GA_SERVICE_ACCOUNT_JSON  (celý service account JSON, minified)
  3. env GA4_CLIENT_EMAIL + GA4_PRIVATE_KEY  (split varianta pro dashboardy)
Vždy: GA4_PROPERTY_ID (číselné ID property).

Bezpečnost: private key jde jen do dočasného souboru (0600) pro openssl podpis
a hned se maže; nikdy se neloguje. Chybové hlášky jsou česky a bez tajemství.

Použití:
  ga4_query.py overview [--days 7]
  ga4_query.py top-content [--days 30] [--limit 10] [--path-filter /blog]
  ga4_query.py sources [--days 30]
  ga4_query.py conversions [--days 30] [--limit 10]
  ga4_query.py realtime
  ga4_query.py weekly-summary            # JSON pro content-performance
  ga4_query.py report --metrics totalUsers,sessions --dimensions date \
               --start 2026-06-01 --end 2026-06-30 [--limit 50]
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
SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
API_BASE = "https://analyticsdata.googleapis.com/v1beta"

NAVOD = (
    "Chybí přístup ke Google Analytics. Postup nastavení (jednou):\n"
    "  1. V Google Cloud Console vytvořte service account a stáhněte JSON klíč.\n"
    "  2. V Google Analytics: Správce → Přístup k účtu/službě → přidejte e-mail\n"
    "     service accountu jako Čtenář (Viewer).\n"
    "  3. V AI Teamu: Nastavení → Integrace → vložte celý JSON jako\n"
    "     GA_SERVICE_ACCOUNT_JSON a číslo property jako GA4_PROPERTY_ID\n"
    "     (GA: Správce → Nastavení služby → ID služby).\n"
    "  4. Hotovo — zeptejte se agenta třeba: „Kolik lidí bylo tento týden na webu?“"
)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _fail(msg: str, code: int = 2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def _cc_variable(name: str):
    """Fallback: Control Center custom variables (agentův runtime)."""
    try:
        sys.path.insert(0, "/home/node/.openclaw/cs-skills/_lib")
        from cc_credentials import get_variable  # type: ignore
        return get_variable(name)
    except Exception:
        return None


def load_credentials():
    """Vrátí (client_email, private_key_pem, property_id)."""
    raw = _cc_variable("GA_SERVICE_ACCOUNT_JSON") or os.environ.get("GA_SERVICE_ACCOUNT_JSON")
    email = _cc_variable("GA4_CLIENT_EMAIL") or os.environ.get("GA4_CLIENT_EMAIL")
    key = _cc_variable("GA4_PRIVATE_KEY") or os.environ.get("GA4_PRIVATE_KEY")
    prop = _cc_variable("GA4_PROPERTY_ID") or os.environ.get("GA4_PROPERTY_ID")

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
    if not prop:
        _fail("Chybí GA4_PROPERTY_ID (číslo property).\nNajdete v GA: Správce → Nastavení služby → ID služby. Vložte do Nastavení → Integrace.")
    return email, key, str(prop).strip()


def get_access_token(email: str, key_pem: str) -> str:
    now = int(time.time())
    header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claims = _b64url(json.dumps({
        "iss": email, "scope": SCOPE, "aud": TOKEN_URL,
        "iat": now, "exp": now + 3600,
    }).encode())
    signing_input = f"{header}.{claims}".encode()

    fd, keyfile = tempfile.mkstemp(suffix=".pem")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(key_pem)
        proc = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", keyfile],
            input=signing_input, capture_output=True,
        )
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
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt,
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


def run_report(token: str, prop: str, body: dict, realtime: bool = False) -> dict:
    kind = "runRealtimeReport" if realtime else "runReport"
    url = f"{API_BASE}/properties/{prop}:{kind}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 403:
            _fail("Google Analytics odmítl přístup (403).\nNejčastější příčina: e-mail service accountu není přidaný v GA jako Čtenář.\nGA: Správce → Přístup k službě → Přidat uživatele → e-mail z klíče (končí na .iam.gserviceaccount.com).")
        if e.code == 429:
            _fail("Google Analytics hlásí příliš mnoho dotazů (429). Zkuste to za pár minut.")
        if e.code == 404:
            _fail(f"Property {prop} nenalezena (404) — zkontrolujte GA4_PROPERTY_ID (jen číslo, bez „properties/“).")
        _fail(f"Dotaz na Google Analytics selhal (HTTP {e.code}): {e.read().decode(errors='replace')[:200]}")


def rows_to_records(data: dict) -> list:
    dims = [h["name"] for h in data.get("dimensionHeaders", [])]
    mets = [h["name"] for h in data.get("metricHeaders", [])]
    out = []
    for row in data.get("rows", []):
        rec = {}
        for i, d in enumerate(dims):
            rec[d] = row.get("dimensionValues", [])[i].get("value", "")
        for i, m in enumerate(mets):
            rec[m] = row.get("metricValues", [])[i].get("value", "")
        out.append(rec)
    return out


def date_range(days: int, offset: int = 0) -> dict:
    return {"startDate": f"{days + offset}daysAgo", "endDate": f"{1 + offset}daysAgo"}


def print_table(records: list):
    if not records:
        print("(žádná data za zvolené období)")
        return
    cols = list(records[0].keys())
    widths = {c: max(len(c), *(len(str(r[c])) for r in records)) for c in cols}
    print("  ".join(c.ljust(widths[c]) for c in cols))
    print("  ".join("-" * widths[c] for c in cols))
    for r in records:
        print("  ".join(str(r[c]).ljust(widths[c]) for c in cols))


def emit(records, fmt):
    if fmt == "json":
        print(json.dumps(records, ensure_ascii=False, indent=2))
    else:
        print_table(records)


def _sum(records, field):
    return sum(int(float(r.get(field, 0) or 0)) for r in records)


def cmd_overview(token, prop, args):
    cur = rows_to_records(run_report(token, prop, {
        "dateRanges": [date_range(args.days)],
        "metrics": [{"name": m} for m in ("totalUsers", "sessions", "screenPageViews", "conversions")],
    }))
    prev = rows_to_records(run_report(token, prop, {
        "dateRanges": [date_range(args.days, offset=args.days)],
        "metrics": [{"name": m} for m in ("totalUsers", "sessions", "screenPageViews", "conversions")],
    }))
    def pick(recs, f):
        return _sum(recs, f)
    out = []
    for f, label in (("totalUsers", "Návštěvníci"), ("sessions", "Návštěvy"),
                     ("screenPageViews", "Zobrazení stránek"), ("conversions", "Konverze")):
        c, p = pick(cur, f), pick(prev, f)
        change = f"{((c - p) / p * 100):+.0f} %" if p else "—"
        out.append({"metrika": label, f"posledních {args.days} dní": c,
                    "předchozí období": p, "změna": change})
    emit(out, args.format)


def cmd_top_content(token, prop, args):
    body = {
        "dateRanges": [date_range(args.days)],
        "dimensions": [{"name": "pagePath"}, {"name": "pageTitle"}],
        "metrics": [{"name": "screenPageViews"}, {"name": "totalUsers"}],
        "orderBys": [{"metric": {"metricName": "screenPageViews"}, "desc": True}],
        "limit": args.limit,
    }
    if args.path_filter:
        body["dimensionFilter"] = {"filter": {"fieldName": "pagePath",
                                              "stringFilter": {"matchType": "CONTAINS", "value": args.path_filter}}}
    emit(rows_to_records(run_report(token, prop, body)), args.format)


def cmd_sources(token, prop, args):
    emit(rows_to_records(run_report(token, prop, {
        "dateRanges": [date_range(args.days)],
        "dimensions": [{"name": "sessionDefaultChannelGroup"}],
        "metrics": [{"name": "sessions"}, {"name": "totalUsers"}, {"name": "conversions"}],
        "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
    })), args.format)


def cmd_conversions(token, prop, args):
    emit(rows_to_records(run_report(token, prop, {
        "dateRanges": [date_range(args.days)],
        "dimensions": [{"name": "landingPage"}],
        "metrics": [{"name": "conversions"}, {"name": "sessions"}],
        "orderBys": [{"metric": {"metricName": "conversions"}, "desc": True}],
        "limit": args.limit,
    })), args.format)


def cmd_realtime(token, prop, args):
    emit(rows_to_records(run_report(token, prop, {
        "dimensions": [{"name": "unifiedScreenName"}],
        "metrics": [{"name": "activeUsers"}],
    }, realtime=True)), args.format)


def cmd_weekly_summary(token, prop, args):
    days = 7
    cur = rows_to_records(run_report(token, prop, {
        "dateRanges": [date_range(days)],
        "metrics": [{"name": m} for m in ("totalUsers", "sessions", "screenPageViews", "conversions")],
    }))
    prev = rows_to_records(run_report(token, prop, {
        "dateRanges": [date_range(days, offset=days)],
        "metrics": [{"name": m} for m in ("totalUsers", "sessions", "screenPageViews", "conversions")],
    }))
    pages = rows_to_records(run_report(token, prop, {
        "dateRanges": [date_range(days)],
        "dimensions": [{"name": "pagePath"}],
        "metrics": [{"name": "screenPageViews"}],
        "orderBys": [{"metric": {"metricName": "screenPageViews"}, "desc": True}],
        "limit": 5,
    }))
    sources = rows_to_records(run_report(token, prop, {
        "dateRanges": [date_range(days)],
        "dimensions": [{"name": "sessionDefaultChannelGroup"}],
        "metrics": [{"name": "sessions"}],
        "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        "limit": 5,
    }))
    print(json.dumps({
        "period_days": days,
        "users": _sum(cur, "totalUsers"), "users_prev": _sum(prev, "totalUsers"),
        "sessions": _sum(cur, "sessions"), "sessions_prev": _sum(prev, "sessions"),
        "pageviews": _sum(cur, "screenPageViews"), "pageviews_prev": _sum(prev, "screenPageViews"),
        "conversions": _sum(cur, "conversions"), "conversions_prev": _sum(prev, "conversions"),
        "top_pages": pages, "top_sources": sources,
    }, ensure_ascii=False, indent=2))


def cmd_report(token, prop, args):
    if not args.metrics:
        _fail("--metrics je povinné pro subcommand report")
    body = {
        "dateRanges": [{"startDate": args.start or "28daysAgo", "endDate": args.end or "yesterday"}],
        "metrics": [{"name": m.strip()} for m in args.metrics.split(",")],
        "limit": args.limit,
    }
    if args.dimensions:
        body["dimensions"] = [{"name": d.strip()} for d in args.dimensions.split(",")]
    emit(rows_to_records(run_report(token, prop, body)), args.format)


def main():
    p = argparse.ArgumentParser(description="GA4 query helper (google-analytics skill)")
    p.add_argument("command", choices=["overview", "top-content", "sources", "conversions",
                                       "realtime", "weekly-summary", "report"])
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--path-filter", default=None)
    p.add_argument("--metrics", default=None)
    p.add_argument("--dimensions", default=None)
    p.add_argument("--start", default=None)
    p.add_argument("--end", default=None)
    p.add_argument("--format", choices=["table", "json"], default="table")
    args = p.parse_args()

    email, key, prop = load_credentials()
    token = get_access_token(email, key)
    {
        "overview": cmd_overview,
        "top-content": cmd_top_content,
        "sources": cmd_sources,
        "conversions": cmd_conversions,
        "realtime": cmd_realtime,
        "weekly-summary": cmd_weekly_summary,
        "report": cmd_report,
    }[args.command](token, prop, args)


if __name__ == "__main__":
    main()
