#!/usr/bin/env python3
"""HeyGen audio (zdarma): hledá + stahuje hudbu / SFX. Stdlib-only.

Použití:
  python3 heygen_audio.py search "cash register" --type sound_effects        # vypíše kandidáty
  python3 heygen_audio.py get "Cash Register 'Kaching'" --query "cash register" --out sfx/cash.mp3
  python3 heygen_audio.py get-music "upbeat playful" --out music.mp3

HeyGen API: GET v3/audio/sounds?query=&type=music|sound_effects, hlavička x-api-key.
"""
import argparse, json, os, sys, urllib.request, urllib.parse

def load_key():
    k = os.environ.get("HEYGEN_API_KEY")
    if k: return k
    for p in [".claude/settings.local.json", os.path.expanduser("~/.claude/settings.local.json")]:
        try: k = json.load(open(p)).get("env", {}).get("HEYGEN_API_KEY")
        except FileNotFoundError: k = None
        if k: return k
    return None  # HeyGen je VOLITELNÝ — bez klíče se hudba/SFX přeskočí (viz main)

def search(query, typ, key, limit=10):
    u = "https://api.heygen.com/v3/audio/sounds?" + urllib.parse.urlencode(
        {"query": query, "type": typ, "limit": limit, "min_score": 0.2})
    r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"x-api-key": key}), timeout=40))
    data = r.get("data", r)
    items = data.get("sounds", data.get("list", data)) if isinstance(data, dict) else data
    return [(it.get("name",""), it.get("audio_url") or it.get("url"), it.get("score",0)) for it in (items or [])]

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--type", default="sound_effects")
    g = sub.add_parser("get"); g.add_argument("name"); g.add_argument("--query", required=True)
    g.add_argument("--type", default="sound_effects"); g.add_argument("--out", required=True)
    m = sub.add_parser("get-music"); m.add_argument("query"); m.add_argument("--out", required=True)
    a = ap.parse_args(); key = load_key()
    if not key:
        print("⚠️  HEYGEN_API_KEY nenastaven — HeyGen je volitelný, přeskakuji hudbu/SFX (video poběží bez nich).")
        sys.exit(0)
    if a.cmd == "search":
        for n, u, sc in search(a.query, a.type, key):
            print(f"  [{sc:.2f}] {n}")
    elif a.cmd in ("get", "get-music"):
        typ = "music" if a.cmd == "get-music" else a.type
        q = a.query if a.cmd == "get" else a.query
        results = search(q, typ, key, limit=15)
        if a.cmd == "get-music":
            pick = results[0] if results else None
        else:
            pick = next((r for r in results if r[0] == a.name), None) or (results[0] if results else None)
        if not pick or not pick[1]: sys.exit("nic nenalezeno")
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        urllib.request.urlretrieve(pick[1], a.out)
        print(f"[heygen] '{pick[0]}' → {os.path.abspath(a.out)}")

if __name__ == "__main__":
    main()
