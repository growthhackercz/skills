#!/usr/bin/env python3
"""
Pexels API wrapper pro article-image-generator.
Umožňuje agentovi NEJDŘÍV se podívat na reálné fotky a posoudit kvalitu,
teprve pak rozhodnout Pexels vs. generování.

  search:   python3 pexels.py search "office team meeting" --orientation landscape --per-page 6 [--min-width 1600]
            -> JSON kandidátů na stdout (id, náhled, rozměry, autor) — agent posoudí a vybere
  download: python3 pexels.py download "<download_url>" "<out_path>"

Klíč: PEXELS_API_KEY v env (per klient, Nastavení -> Integrace).
Bez klíče -> exit 3 s JSON {"error":"no_key"} -> agent fallne na image_generate.
Žádné externí závislosti (jen stdlib).
"""
import os, sys, json, argparse, urllib.request, urllib.parse

API = "https://api.pexels.com/v1/search"

def _cc_variable(name):
    """Control Center proměnné (Nastavení -> Integrace) — store má přednost před env."""
    try:
        import sys as _sys
        _sys.path.insert(0, "/home/node/.openclaw/cs-skills/_lib")
        from cc_credentials import get_variable  # type: ignore
        return (get_variable(name) or "").strip()
    except Exception:
        return ""

def _key():
    k = _cc_variable("PEXELS_API_KEY") or os.environ.get("PEXELS_API_KEY")
    if not k:
        print(json.dumps({"error": "no_key",
                          "message": "PEXELS_API_KEY není nastavený — použij image_generate."}))
        sys.exit(3)
    return k

def cmd_search(a):
    params = {"query": a.query, "per_page": a.per_page, "orientation": a.orientation}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                 headers={"Authorization": _key()})
    try:
        data = json.load(urllib.request.urlopen(req, timeout=30))
    except Exception as e:
        print(json.dumps({"error": "request_failed", "message": str(e)}))
        sys.exit(4)
    results = []
    for p in data.get("photos", []):
        if a.min_width and p.get("width", 0) < a.min_width:
            continue
        src = p.get("src", {})
        results.append({
            "id": p.get("id"),
            "download": src.get("large2x") or src.get("original"),
            "preview": src.get("medium"),
            "width": p.get("width"), "height": p.get("height"),
            "alt": p.get("alt", ""),
            "photographer": p.get("photographer", ""),
            "pexels_url": p.get("url", ""),
        })
    print(json.dumps({"query": a.query, "count": len(results), "results": results},
                     ensure_ascii=False, indent=2))

def cmd_download(a):
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    urllib.request.urlretrieve(a.url, a.out)
    size = os.path.getsize(a.out)
    print(json.dumps({"saved": a.out, "bytes": size}))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--orientation", default="landscape",
                   choices=["landscape", "portrait", "square"])
    s.add_argument("--per-page", type=int, default=6, dest="per_page")
    s.add_argument("--min-width", type=int, default=0, dest="min_width")
    s.set_defaults(func=cmd_search)
    d = sub.add_parser("download")
    d.add_argument("url")
    d.add_argument("out")
    d.set_defaults(func=cmd_download)
    args = ap.parse_args()
    args.func(args)
