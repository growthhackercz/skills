#!/usr/bin/env python3
"""
heygen-music.py — najde a stáhne hudební podklad z HeyGen knihovny (250k+ tracků zdarma).

Použití:
    python3 heygen-music.py --query "cinematic build epic" --min-duration 21 --output music/track.wav
    python3 heygen-music.py --query "upbeat corporate" --list       # jen vypsat kandidáty

HEYGEN_API_KEY: env, nebo .claude/settings.local.json (env blok) — hodnotu nikdy nevypisovat.
"""
from __future__ import annotations
import argparse, json, os, sys, urllib.parse, urllib.request
from pathlib import Path

API = "https://api.heygen.com/v3/audio/sounds"


def get_key() -> str:
    k = os.environ.get("HEYGEN_API_KEY")
    if k:
        return k
    for p in (Path.cwd() / ".claude/settings.local.json",
              Path.home() / "Documents/Claude/Projects/CliqSales/.claude/settings.local.json"):
        if p.exists():
            try:
                d = json.load(open(p))
                k = (d.get("env") or {}).get("HEYGEN_API_KEY") or d.get("HEYGEN_API_KEY")
                if k:
                    return k
            except Exception:
                pass
    print("❌ HEYGEN_API_KEY nenalezen (env ani settings.local.json)"); sys.exit(2)


def search(key: str, query: str, limit: int = 10) -> list[dict]:
    url = f"{API}?{urllib.parse.urlencode({'query': query, 'limit': limit})}"
    req = urllib.request.Request(url, headers={"x-api-key": key})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    node = d.get("data", d)
    if isinstance(node, dict):
        for k in ("sounds", "list", "items", "result"):
            if k in node:
                node = node[k]; break
    return node if isinstance(node, list) else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--min-duration", type=float, default=20)
    ap.add_argument("--output")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--pick", type=int, default=0, help="index kandidáta (default první vyhovující)")
    a = ap.parse_args()

    key = get_key()
    items = [it for it in search(key, a.query) if it.get("duration", 0) >= a.min_duration]
    if not items:
        print(f"❌ žádný track ≥{a.min_duration}s pro dotaz „{a.query}“ — zkus jiný dotaz"); sys.exit(1)

    if a.list or not a.output:
        for i, it in enumerate(items):
            print(f"[{i}] {it.get('name','?')} — {it.get('duration')}s")
        if not a.output:
            print("↪ přidej --output music/track.wav pro stažení (--pick N pro výběr)")
        return

    it = items[min(a.pick, len(items) - 1)]
    out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(it["audio_url"], out)
    print(f"✅ {it.get('name','track')} ({it.get('duration')}s) -> {out} ({out.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
