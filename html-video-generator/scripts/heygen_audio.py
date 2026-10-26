#!/usr/bin/env python3
"""HeyGen audio — hledání a stažení hudby/SFX z 250k+ knihovny (náhrada za FAL).

Sémantické hledání popisem vibe → stáhne mp3 → normalizuje → použije v lokálním renderu.
HeyGen audio knihovna NENÍ cloud render — jen fetch assetu, takže sedí na fleet.

Použití:
  # prozkoumat (žádný download):
  python3 heygen_audio.py search --query "dark premium tech, cinematic, 100 bpm" --type music
  python3 heygen_audio.py search --query "playful bouncy UI pop, soft round" --type sfx

  # stáhnout konkrétní (podle jména nebo pořadí) + zpracovat:
  python3 heygen_audio.py get --query "..." --type music --name "Astral..." --out assets/music.mp3 --duration 35
  python3 heygen_audio.py get --query "soft whoosh swipe" --type sfx --pick 0 --out assets/sfx/whoosh.mp3

Pravidla zvuku: hravé > technické. Viz references/audio.md (sound recipes).
HEYGEN_API_KEY: env, fallback .claude/settings.local.json. NIKDY nevypisovat hodnotu.
"""
import argparse, json, os, pathlib, subprocess, sys, urllib.request, urllib.parse, urllib.error

API = "https://api.heygen.com/v3/audio/sounds"

def key():
    k = os.environ.get("HEYGEN_API_KEY")
    if k:
        return k
    for p in [pathlib.Path(__file__).resolve().parents[3] / ".claude" / "settings.local.json",
              pathlib.Path.home() / ".claude" / "settings.local.json"]:
        if p.exists():
            try:
                return json.load(open(p))["env"]["HEYGEN_API_KEY"]
            except Exception:
                pass
    sys.exit("HEYGEN_API_KEY nenalezen (env ani settings.local.json)")

def api_type(t):
    return "music" if t == "music" else "sound_effects"

def search(query, typ, limit, mn):
    qs = urllib.parse.urlencode({"query": query, "type": api_type(typ), "limit": limit, "min_score": mn})
    req = urllib.request.Request(f"{API}?{qs}", headers={"x-api-key": key()})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r).get("data", [])
    except urllib.error.HTTPError as e:
        sys.exit(f"HeyGen API HTTP {e.code}: {e.read().decode()[:200]}")

def cmd_search(a):
    data = search(a.query, a.type, a.limit, a.min_score)
    print(json.dumps([{"i": i, "name": t.get("name"), "duration": t.get("duration"),
                       "score": round(t.get("score") or 0, 2), "desc": (t.get("description") or "")[:60]}
                      for i, t in enumerate(data)], ensure_ascii=False, indent=2))
    if not data:
        print("\n⚠ nic — zkus jiný popis nebo nižší --min-score", file=sys.stderr)

def cmd_get(a):
    data = search(a.query, a.type, max(a.limit, (a.pick or 0) + 1), a.min_score)
    if not data:
        sys.exit("žádný výsledek")
    pick = None
    if a.name:
        pick = next((t for t in data if t.get("name") == a.name), None)
    if pick is None:
        pick = data[a.pick or 0]
    print(f"vybráno: {pick['name']} [{pick.get('duration')}s] score {round(pick.get('score') or 0,2)}")
    out = pathlib.Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    raw = out.with_suffix(".raw.mp3")
    urllib.request.urlretrieve(pick["audio_url"], raw)
    # zpracování: music = ořez na duration + fade out; sfx = limiter na -3 dB + micro-fade
    if a.type == "music" and a.duration:
        af = f"afade=t=out:st={max(0,a.duration-0.5):.2f}:d=0.5"
        subprocess.run(["ffmpeg", "-y", "-i", str(raw), "-t", str(a.duration), "-af", af, "-ar", "44100", str(out)],
                       capture_output=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-i", str(raw), "-af",
                        "alimiter=limit=0.708,afade=t=out:st=0:d=0.02:curve=tri", "-ar", "44100", str(out)],
                       capture_output=True)
    if not out.exists():
        subprocess.run(["ffmpeg", "-y", "-i", str(raw), "-ar", "44100", str(out)], capture_output=True)
    raw.unlink(missing_ok=True)
    sz = out.stat().st_size // 1024 if out.exists() else 0
    print(f"✓ {out} ({sz} KB)")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("search", "get"):
        p = sub.add_parser(name)
        p.add_argument("--query", required=True)
        p.add_argument("--type", choices=["music", "sfx"], default="sfx")
        p.add_argument("--limit", type=int, default=6)
        p.add_argument("--min-score", type=float, default=0.3, dest="min_score")
        if name == "get":
            p.add_argument("--out", required=True)
            p.add_argument("--name", default=None, help="přesné jméno stopy ze search")
            p.add_argument("--pick", type=int, default=None, help="index ze search (0 = nejlepší)")
            p.add_argument("--duration", type=float, default=None, help="ořez hudby na X s + fade")
    a = ap.parse_args()
    (cmd_search if a.cmd == "search" else cmd_get)(a)

if __name__ == "__main__":
    main()
