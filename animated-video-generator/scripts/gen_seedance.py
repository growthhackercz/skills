#!/usr/bin/env python3
"""Seedance 2.0 reference-to-video (FAL). Z storyboard stillu vyrobí ~15s animovaný klip.

Použití:
  python3 gen_seedance.py --ref still.png --prompt "<styl+akce>" --out clip.mp4 [--dry-run]
  [--duration 15] [--resolution 720p] [--aspect 16:9] [--endpoint bytedance/seedance-2.0/fast/reference-to-video]

VŽDY nejdřív --dry-run (vypíše prompt + cenu) + STOP. Generuj až po schválení.

⚠️ Spouštěj **systémovým python3** (fleet: 3.11, lokál mac: /usr/bin/python3 3.9) — oba mají fal_client 1.0.0
   i funkční pyexpat. NE homebrew python 3.14 (rozbitý pyexpat → fal_client neimportuje).
   `fal_client.subscribe` řeší frontu i stažení výsledku spolehlivě (ruční poll přes response_url
   u Seedance vrací 404 — pojmenovaná chyba, NEpoužívat).
"""
import argparse, json, os, sys

# app_id BEZ "fal-ai/" prefixu — bytedance je vlastní namespace; s prefixem submit/response 404.
FAST_ENDPOINT = "bytedance/seedance-2.0/fast/reference-to-video"
COST_PER_SEC_FAST = 0.022  # ~$3.6 / 15s

def load_key():
    k = os.environ.get("FAL_KEY")
    if k: return k
    for p in [".claude/settings.local.json", os.path.expanduser("~/.claude/settings.local.json")]:
        try: k = json.load(open(p)).get("env", {}).get("FAL_KEY")
        except FileNotFoundError: k = None
        if k: return k
    sys.exit("FAL_KEY nenalezen (env ani settings.local.json)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="storyboard still (reference image)")
    ap.add_argument("--prompt", required=True, help="styl deskriptor + popis akce (BEZ textu)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", default="15")
    ap.add_argument("--resolution", default="720p")
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--endpoint", default=FAST_ENDPOINT)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cost = float(a.duration) * COST_PER_SEC_FAST
    print(f"[seedance] endpoint: {a.endpoint}")
    print(f"[seedance] ref: {a.ref}  out: {a.out}  {a.resolution} {a.aspect} {a.duration}s")
    print(f"[seedance] prompt: {a.prompt}")
    print(f"[seedance] odhad ceny: ~${cost:.2f}  | generate_audio=False")
    if a.dry_run:
        print("[seedance] --dry-run → STOP. Spusť bez --dry-run po schválení."); return
    if not os.path.exists(a.ref): sys.exit(f"ref neexistuje: {a.ref}")

    os.environ["FAL_KEY"] = load_key()  # fal_client čte FAL_KEY z env
    try:
        import fal_client
    except Exception as e:
        sys.exit(f"fal_client nejde importovat ({e}). Spusť systémovým python3 (NE homebrew 3.14).")
    import urllib.request

    print("[seedance] upload reference na FAL CDN…")
    file_url = fal_client.upload_file(a.ref)
    print("[seedance] subscribe (15s klip ~1–3 min)…")
    res = fal_client.subscribe(a.endpoint, arguments={
        "image_urls": [file_url], "prompt": a.prompt, "duration": a.duration,
        "aspect_ratio": a.aspect, "resolution": a.resolution, "generate_audio": False})
    vid = res.get("video")
    url = vid.get("url") if isinstance(vid, dict) else vid
    if not url: sys.exit(f"[seedance] bez video URL (možná 422 face-moderation → face-light storyboard): {res}")
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    urllib.request.urlretrieve(url, a.out)
    print(f"[seedance] HOTOVO → {os.path.abspath(a.out)}")

if __name__ == "__main__":
    main()
