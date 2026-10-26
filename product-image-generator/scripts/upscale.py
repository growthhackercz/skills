#!/usr/bin/env python3
"""Optional post-step: upscale generated 1024x1024 carousel images to a larger
square (default 2000x2000) for Shopify product pages with sharp zoom.

Originals are kept; upscaled copies go to <carousel-dir>/<size>/.
Requires Pillow. Fails fast with an install hint if it is missing.

Usage:
    python3 upscale.py /path/to/carousel/ --to 2000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Upscale carousel images to a larger square.")
    parser.add_argument("carousel_dir", help="Directory containing the generated carousel images.")
    parser.add_argument("--to", type=int, default=2000, help="Target longer-edge size in px (default 2000).")
    args = parser.parse_args()

    try:
        from PIL import Image  # noqa: WPS433 (runtime import is intentional for graceful failure)
    except ImportError:
        print(
            "ERROR: Pillow is required for upscaling. Install it with: python3 -m pip install Pillow",
            file=sys.stderr,
        )
        return 1

    src_dir = Path(args.carousel_dir)
    if not src_dir.is_dir():
        print(f"ERROR: Not a directory: {src_dir}", file=sys.stderr)
        return 1

    target = args.to
    out_dir = src_dir / str(target)
    out_dir.mkdir(parents=True, exist_ok=True)

    sources = sorted(
        p
        for p in src_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    )
    if not sources:
        print(f"ERROR: No images found in {src_dir}", file=sys.stderr)
        return 1

    done = []
    for src in sources:
        with Image.open(src) as img:
            img = img.convert("RGB")
            width, height = img.size
            longer = max(width, height)
            if longer >= target:
                scale = 1.0
            else:
                scale = target / longer
            new_size = (round(width * scale), round(height * scale))
            resized = img.resize(new_size, Image.LANCZOS)
            out_path = out_dir / (src.stem + ".jpg")
            resized.save(out_path, "JPEG", quality=92)
            done.append(out_path.name)

    print(f"Upscaled {len(done)} image(s) to {target}px -> {out_dir}")
    for name in done:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
