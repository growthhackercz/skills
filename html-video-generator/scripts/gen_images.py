#!/usr/bin/env python3
"""FAL flux obrázky — produktové stilly a CONCEPT images (target-state framy).

Concept image = vyrenderuj cílový frame scény (FAL/flux) → postav HTML scénu, aby ho trefila
(killer na iterace, viz references/pipeline.md). Produktové stilly = full-bleed do scén.

Použití:
  python3 gen_images.py --brief <proj>/video-brief.json --out <proj>/assets/img [--only id1,id2] [--dry-run]
  python3 gen_images.py --concept "popis cílového framu scény" --out <proj>/assets/_concept/hook.jpg [--dry-run]

Brand koherence: brief.imageStyle se přilepí ke každému promptu. FAL_KEY: env / settings.local.json.
VŽDY --dry-run + STOP před ostrou generací (FAL stojí kredity).
"""
import argparse, json, os, pathlib, sys, urllib.request

def key():
    k = os.environ.get("FAL_KEY")
    if k: return k
    for p in [pathlib.Path(__file__).resolve().parents[3]/".claude"/"settings.local.json",
              pathlib.Path.home()/".claude"/"settings.local.json"]:
        if p.exists():
            try: return json.load(open(p))["env"]["FAL_KEY"]
            except Exception: pass
    sys.exit("FAL_KEY nenalezen")

def flux(prompt, w, h, seed):
    payload = {"prompt": prompt, "image_size": {"width": w, "height": h},
               "num_inference_steps": 28, "guidance_scale": 3.5, "seed": seed,
               "num_images": 1, "enable_safety_checker": True, "output_format": "jpeg"}
    req = urllib.request.Request("https://fal.run/fal-ai/flux/dev", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Key {key()}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.load(r)["images"][0]["url"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief"); ap.add_argument("--concept")
    ap.add_argument("--out", required=True); ap.add_argument("--only")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.concept:
        prompt = a.concept + ", cinematic 16:9 product video frame, premium"
        if a.dry_run:
            print(json.dumps({"mode":"concept","odhad_usd":0.03,"prompt":prompt[:200]}, ensure_ascii=False, indent=2)); return
        dest = pathlib.Path(a.out); dest.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(flux(prompt, 1344, 768, 7), dest)
        print(f"✓ concept: {dest}"); return

    if not a.brief: sys.exit("zadej --brief nebo --concept")
    brief = json.load(open(a.brief)); style = brief.get("imageStyle","")
    only = set(a.only.split(",")) if a.only else None
    todo = [s for s in brief.get("images",[]) if not only or s["id"] in only]
    if not todo: sys.exit("žádné image sloty v briefu")
    est = round(len(todo)*0.03, 2)
    if a.dry_run:
        print(json.dumps({"pocet":len(todo),"odhad_usd":est,
            "sloty":[{"id":s["id"],"rozmer":f"{s.get('width',1344)}x{s.get('height',768)}",
                      "prompt":(s["prompt"]+(", "+style if style else ""))[:180]} for s in todo]},
            ensure_ascii=False, indent=2)); return
    outdir = pathlib.Path(a.out); outdir.mkdir(parents=True, exist_ok=True)
    fails = []
    for i, s in enumerate(todo):
        try:
            url = flux(s["prompt"] + (", "+style if style else ""), s.get("width",1344), s.get("height",768), s.get("seed",100+i))
            dest = outdir/f"{s['id']}.jpg"; urllib.request.urlretrieve(url, dest)
            print(f"✓ {s['id']}.jpg ({dest.stat().st_size//1024} KB)")
        except Exception as e:
            print(f"✗ {s['id']}: {type(e).__name__}: {e}"); fails.append(s["id"])
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
