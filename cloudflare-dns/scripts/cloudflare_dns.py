#!/usr/bin/env python3
"""cloudflare-dns — connect a custom domain (managed at Cloudflare) to a Netlify site by
auto-creating a CNAME record. CNAME flattening handles apex too, so apex and subdomains are
identical. DNS-only (proxied=false) so Netlify handles TLS/CDN.

API: https://api.cloudflare.com/client/v4, auth: Authorization: Bearer $CLOUDFLARE_API_TOKEN
(Zone:DNS:Edit + Zone:Read). Stdlib only (urllib). See SKILL.md.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.cloudflare.com/client/v4"


def fail(msg: str) -> "None":
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def get_token() -> str:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token:
        fail("CLOUDFLARE_API_TOKEN není nastavený (per-tenant SecretRef).")
    return token


def api(method: str, path: str, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer " + get_token(),
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:600]
        fail(f"Cloudflare API {method} {path} → HTTP {exc.code}: {detail}")
        return
    except urllib.error.URLError as exc:
        fail(f"Cloudflare API nedostupné: {exc}")
        return
    # CF wraps everything in {success, errors, result}
    if not payload.get("success", False):
        fail(f"Cloudflare API {method} {path} chyba: {json.dumps(payload.get('errors'), ensure_ascii=False)}")
    return payload.get("result")


def list_zones() -> list:
    zones = api("GET", "/zones?per_page=50") or []
    return [{"id": z.get("id"), "name": z.get("name")} for z in zones if z.get("id") and z.get("name")]


def find_zone(fqdn: str, zones: list):
    fqdn = fqdn.rstrip(".").lower()
    matches = [z for z in zones if fqdn == z["name"].lower() or fqdn.endswith("." + z["name"].lower())]
    return max(matches, key=lambda z: len(z["name"])) if matches else None


def cmd_list(args):
    zones = list_zones()
    result = {"zones": zones}
    if args.domain:
        zone = find_zone(args.domain, zones)
        if not zone:
            fail(f"Zóna pro {args.domain} nenalezena na tomto Cloudflare účtu.")
        result["records"] = api("GET", f"/zones/{zone['id']}/dns_records?per_page=100")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_connect(args):
    fqdn = args.fqdn.rstrip(".").lower()
    target = args.target.rstrip(".").lower()
    zone = find_zone(fqdn, list_zones())
    if not zone:
        fail(f"Doménu {fqdn} nemá tento Cloudflare účet jako zónu. "
             f"Pro doménu na Active24 použij active24-dns.")
    body = {"type": "CNAME", "name": fqdn, "content": target, "ttl": args.ttl, "proxied": False}
    created = api("POST", f"/zones/{zone['id']}/dns_records", body)
    print(json.dumps({
        "ok": True,
        "zone": zone["name"],
        "name": fqdn,
        "type": "CNAME",
        "value": target,
        "ttl": args.ttl,
        "proxied": False,
        "recordId": (created or {}).get("id"),
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Cloudflare DNS — connect a domain to a Netlify site")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list zones (and records for --domain)")
    p_list.add_argument("--domain", help="show records for this domain")
    p_list.set_defaults(func=cmd_list)

    p_conn = sub.add_parser("connect", help="point a domain at a Netlify site (CNAME)")
    p_conn.add_argument("fqdn", help="domain to connect, e.g. www.example.com or example.com (apex)")
    p_conn.add_argument("--target", required=True, help="Netlify host, e.g. mysite.netlify.app")
    p_conn.add_argument("--ttl", type=int, default=3600)
    p_conn.set_defaults(func=cmd_connect)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
