#!/usr/bin/env python3
"""Storyboard still přes GPT Image 2 (FAL fal-ai/gpt-image-2/edit). Stdlib-only (urllib).
Slouží jako reference pro Seedance + k vizuálnímu schválení. BEZ velkého textu.

Použití:
  python3 gen_storyboard.py --prompt "<styl + scéna, no text>" --out _storyboard/sb1.png [--ref prev.png] [--dry-run]
  [--size landscape_16_9]

--ref = předchozí schválený still (drží konzistenci postavy). --dry-run vypíše prompt + cenu + STOP.

⚠️ image_size MUSÍ být jeden z presetů (ne {width,height} dict → jinak 422):
   square_hd | square | portrait_4_3 | portrait_16_9 | landscape_4_3 | landscape_16_9 | auto
⚠️ endpoint je fal-ai/gpt-image-2/edit (BEZ "openai/" — to vrací 404).
⚠️ reference obrázky jdou jako HTTPS URL z FAL CDN (ne data URL).
"""
import argparse, json, os, sys, time, urllib.request

ENDPOINT = "fal-ai/gpt-image-2/edit"
SIZES = {"square_hd", "square", "portrait_4_3", "portrait_16_9", "landscape_4_3", "landscape_16_9", "auto"}

def load_key():
    k = os.environ.get("FAL_KEY")
    if k: return k
    for p in [".claude/settings.local.json", os.path.expanduser("~/.claude/settings.local.json")]:
        try: k = json.load(open(p)).get("env", {}).get("FAL_KEY")
        except FileNotFoundError: k = None
        if k: return k
    sys.exit("FAL_KEY nenalezen")

def fal_upload(path, key):
    """Nahraje obrázek na FAL CDN, vrátí HTTPS file_url (gpt-image-2/edit nebere data URL)."""
    H = {"Authorization": "Key " + key, "Content-Type": "application/json"}
    ct = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    init = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://rest.alpha.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3",
        data=json.dumps({"content_type": ct, "file_name": os.path.basename(path)}).encode(), headers=H), timeout=60))
    req = urllib.request.Request(init["upload_url"], data=open(path, "rb").read(), method="PUT")
    req.add_header("Content-Type", ct)
    urllib.request.urlopen(req, timeout=120)
    return init["file_url"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", action="append", help="reference still(y) — konzistence postavy / produkt (lze víckrát)")
    ap.add_argument("--size", default="landscape_16_9", choices=sorted(SIZES))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    print(f"[storyboard] size: {a.size}  out: {a.out}")
    print(f"[storyboard] prompt: {a.prompt}")
    print(f"[storyboard] odhad ceny: ~$0.03–0.10 / still")
    if a.dry_run:
        print("[storyboard] --dry-run → STOP."); return
    key = load_key(); H = {"Authorization": "Key " + key, "Content-Type": "application/json"}
    refs = [fal_upload(r, key) for r in (a.ref or []) if os.path.exists(r)]
    payload = {"prompt": a.prompt + " — no text, no captions, no letters.",
               "image_urls": refs, "image_size": a.size}
    sub = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://queue.fal.run/" + ENDPOINT, data=json.dumps(payload).encode(), headers=H), timeout=120))
    surl, rurl = sub["status_url"], sub["response_url"]
    for _ in range(90):
        time.sleep(4)
        s = json.load(urllib.request.urlopen(urllib.request.Request(surl, headers={"Authorization":"Key "+key}), timeout=30))
        if s.get("status") == "COMPLETED": break
        if s.get("status") in ("FAILED","ERROR"): sys.exit(f"FAILED: {s}")
    r = json.load(urllib.request.urlopen(urllib.request.Request(rurl, headers={"Authorization":"Key "+key}), timeout=120))
    imgs = r.get("images") or []
    if not imgs: sys.exit(f"bez obrázku: {r}")
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    urllib.request.urlretrieve(imgs[0]["url"], a.out)
    print(f"[storyboard] HOTOVO → {os.path.abspath(a.out)}")

if __name__ == "__main__":
    main()
