#!/usr/bin/env python3
"""active24-dns — connect a custom domain (managed at Active24) to a Netlify site by
creating the right DNS record via the Active24 **v2** REST API. Apex -> A 75.2.60.5;
subdomain -> CNAME to the netlify host. Idempotent (updates an existing record instead
of duplicating).

API: https://rest.active24.cz (v2). Auth = HMAC-SHA1 signed requests:
  canonical = "{METHOD} {path-without-query} {unix_ts}"
  signature = hex(HMAC_SHA1(secret, canonical))
  headers:  Authorization: Basic base64("{ACTIVE24_API_KEY}:{signature}")
            Date: {YYYYMMDDTHHMMSSZ}   (same instant, UTC)
Credentials (from the Active24 panel): ACTIVE24_API_KEY = identifier,
ACTIVE24_API_SECRET = secret. Per-tenant via SecretRef. Stdlib only. See SKILL.md.
"""
import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE = "https://rest.active24.cz"
NETLIFY_APEX_IP = "75.2.60.5"  # Netlify load balancer for apex A records (Netlify docs)


def fail(msg: str) -> "None":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def get_creds():
    key = os.environ.get("ACTIVE24_API_KEY", "").strip()
    secret = os.environ.get("ACTIVE24_API_SECRET", "").strip()
    if not key or not secret:
        fail("ACTIVE24_API_KEY a ACTIVE24_API_SECRET musí být nastavené (per-tenant SecretRef).")
    return key, secret


def api(method: str, path: str, body=None, silent: bool = False):
    """Signed Active24 v2 request. `path` may include a query string; only the path part
    (no query) goes into the signature. With silent=True, HTTP errors return None."""
    key, secret = get_creds()
    sign_path = path.split("?", 1)[0]
    now = datetime.now(timezone.utc)
    timestamp = int(now.timestamp())
    datez = now.strftime("%Y%m%dT%H%M%SZ")
    canonical = f"{method} {sign_path} {timestamp}"
    signature = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha1).hexdigest()
    authorization = base64.b64encode(f"{key}:{signature}".encode("utf-8")).decode("ascii")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + authorization,
            "Date": datez,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as exc:
        if silent:
            return None
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        fail(f"Active24 API {method} {sign_path} → HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        fail(f"Active24 API nedostupné: {exc}")


def resolve_service(fqdn: str):
    """Resolve the Active24 service (DNS zone) that owns fqdn, trying registrable suffixes
    longest-first. Returns (service_id, zone) or (None, None)."""
    labels = fqdn.split(".")
    for i in range(len(labels) - 1):
        candidate = ".".join(labels[i:])
        zone = api("GET", f"/v1/user/self/zone/{candidate}", silent=True)
        if isinstance(zone, dict) and zone.get("id"):
            return str(zone["id"]), candidate
    return None, None


def collect_records(service: str) -> list:
    """All DNS records for a service (follows pagination)."""
    out, page = [], 1
    while True:
        resp = api("GET", f"/v2/service/{service}/dns/record?page={page}&rowsPerPage=100")
        if not isinstance(resp, dict):
            break
        out.extend(resp.get("data") or [])
        total_pages = resp.get("totalPages") or 1
        if page >= total_pages:
            break
        page += 1
    return out


def find_record(service: str, rtype: str, fqdn: str):
    name_l = fqdn.rstrip(".").lower()
    for r in collect_records(service):
        if not isinstance(r, dict):
            continue
        if str(r.get("type", "")).upper() == rtype and str(r.get("name", "")).rstrip(".").lower() == name_l:
            return r
    return None


def managed_domains() -> list:
    resp = api("GET", "/v1/user/self/service")
    items = resp.get("items") if isinstance(resp, dict) else resp
    return [
        s["name"] for s in (items or [])
        if isinstance(s, dict) and s.get("serviceName") == "domain" and s.get("name")
    ]


def cmd_list(args):
    if args.domain:
        fqdn = args.domain.rstrip(".").lower()
        service, zone = resolve_service(fqdn)
        if not service:
            fail(f"Doménu {fqdn} nemá tento Active24 účet ve spravovaných zónách.")
        print(json.dumps({"zone": zone, "service": service, "records": collect_records(service)},
                         ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"managedDomains": managed_domains()}, ensure_ascii=False, indent=2))


def cmd_connect(args):
    fqdn = args.fqdn.rstrip(".").lower()
    target = args.target.rstrip(".").lower()
    service, zone = resolve_service(fqdn)
    if not service:
        fail(f"Doménu {fqdn} nemá tento Active24 účet ve spravovaných zónách. "
             f"Pro doménu na Cloudflare použij cloudflare-dns.")

    if fqdn == zone:  # apex → A record to Netlify
        rtype, content = "A", NETLIFY_APEX_IP
    else:  # subdomain → CNAME to the netlify host
        rtype, content = "CNAME", target

    desired = {"type": rtype, "name": fqdn, "content": content, "ttl": args.ttl}
    existing = find_record(service, rtype, fqdn)
    if existing:
        if str(existing.get("content", "")).rstrip(".").lower() == content.rstrip(".").lower():
            action = "unchanged"
        else:
            api("PUT", f"/v2/service/{service}/dns/record/{existing['id']}", desired)
            action = "updated"
    else:
        api("POST", f"/v2/service/{service}/dns/record", desired)
        action = "created"

    print(json.dumps({
        "ok": True,
        "zone": zone,
        "service": service,
        "name": fqdn,
        "type": rtype,
        "value": content,
        "ttl": args.ttl,
        "action": action,
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Active24 DNS (v2) — connect a domain to a Netlify site")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list managed domains (and records for --domain)")
    p_list.add_argument("--domain", help="show records for this domain")
    p_list.set_defaults(func=cmd_list)

    p_conn = sub.add_parser("connect", help="point a domain at a Netlify site")
    p_conn.add_argument("fqdn", help="domain to connect, e.g. www.example.cz or example.cz (apex)")
    p_conn.add_argument("--target", required=True, help="Netlify host, e.g. mysite.netlify.app")
    p_conn.add_argument("--ttl", type=int, default=3600)
    p_conn.set_defaults(func=cmd_connect)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
