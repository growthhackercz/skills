#!/usr/bin/env python3
"""
generate-keyframe.py — keyframe / kanonický portrét přes FAL gpt-image-2/edit (~$0.10).

Použití:
    python3 generate-keyframe.py --prompt "<scéna / headshot>" --output refs/refA.png \
        --width 720 --height 1280 --ref <reference.png> [--ref <dalsi.png>] [--dry-run]

- 9:16 keyframe = 720×1280, 16:9 = 1280×720, portrét postavy = 768×1024.
- --ref: brand-board / výřez storyboardu / reálný produktový mockup (obrazovky!).
Vyžaduje FAL_KEY + fal_client.
"""
from __future__ import annotations
import argparse, asyncio, os, sys, urllib.request
from pathlib import Path


async def run(a) -> int:
    try:
        import fal_client
    except ImportError:
        print("❌ fal_client není nainstalovaný"); return 2
    if not os.environ.get("FAL_KEY"):
        print("❌ FAL_KEY není nastavený"); return 2

    refs = [Path(r) for r in (a.ref or []) if Path(r).exists()]
    print(f"→ prompt {len(a.prompt)} znaků | {a.width}×{a.height} | refs {len(refs)}")
    if a.dry_run:
        print("🟡 --dry-run — bez FAL útraty.")
        print(f"--- PROMPT ---\n{a.prompt}\n--- KONEC ---")
        return 0

    arguments = {"prompt": a.prompt, "image_size": {"width": a.width, "height": a.height}}
    if refs:
        urls = await asyncio.gather(*[fal_client.upload_file_async(str(r)) for r in refs])
        arguments["image_urls"] = list(urls)
    else:
        print("⚠ bez reference — generuji bez identity kotvy")
        arguments["image_urls"] = []

    print("→ openai/gpt-image-2/edit (~$0.10) …")
    handler = await fal_client.submit_async("openai/gpt-image-2/edit", arguments=arguments)
    result = await handler.get()
    url = result.get("images", [{}])[0].get("url")
    if not url:
        print(f"❌ žádná image URL: {str(result)[:300]}"); return 2
    out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out)
    print(f"✅ {out} ({out.stat().st_size//1024} KB)")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--width", type=int, default=720)
    p.add_argument("--height", type=int, default=1280)
    p.add_argument("--ref", action="append")
    p.add_argument("--dry-run", action="store_true")
    sys.exit(asyncio.run(run(p.parse_args())))


if __name__ == "__main__":
    main()
