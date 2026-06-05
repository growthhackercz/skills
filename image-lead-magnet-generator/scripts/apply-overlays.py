#!/usr/bin/env python3
"""
apply-overlays.py

Hybrid post-processing — vloží reálné brand assets (product image, logo, foto)
přes vygenerované AI stránky. Použití když chceš mít EXAKTNÍ obrázek (ne AI
variantu) na konkrétní pozici stránky.

Konfigurace v page-plan.json:

    "pages": [
      {
        "n": 10,
        ...
        "overlays": [
          {
            "asset": "images/end-product.png",
            "position": "top",
            "height_ratio": 0.40,
            "blend_mode": "normal",
            "fade_bottom": 0.15
          }
        ]
      }
    ]

Position může být:
- "top" — horní část stránky, height_ratio určuje výšku (0.40 = 40%)
- "bottom" — dolní část
- "center" — střed s height_ratio
- "full" — celá stránka jako background
- {x, y, width, height} — explicit pixel coords (ratio 0-1)

Usage:
    python3 apply-overlays.py \\
        --plan /documents/lead-magnets/[slug]/page-plan.json \\
        --pages-dir /documents/lead-magnets/[slug]/_pages/ \\
        --base-dir /documents/lead-magnets/[slug]/.. \\
        [--in-place]   # přepíše originál; bez tohoto se uloží jako page-XX-final.png

Dependencies:
    pip install Pillow
"""

import argparse
import json
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("❌ Missing Pillow: pip install Pillow")
    raise SystemExit(1)


def resolve_asset_path(asset: str, base_dir: Path) -> Path:
    """Resolve asset path relative to base_dir."""
    p = Path(asset)
    if p.is_absolute():
        return p
    return base_dir / asset


def apply_overlay(page_img: Image.Image, asset_path: Path, overlay: dict) -> Image.Image:
    """Apply single overlay onto page image. Returns modified page image."""
    page_w, page_h = page_img.size
    overlay_img = Image.open(asset_path)
    if overlay_img.mode != "RGBA":
        overlay_img = overlay_img.convert("RGBA")

    position = overlay.get("position", "top")
    height_ratio = overlay.get("height_ratio", 0.40)
    width_ratio = overlay.get("width_ratio", 1.0)
    fade_bottom = overlay.get("fade_bottom", 0.0)
    fade_top = overlay.get("fade_top", 0.0)

    # Vypočítej cílovou velikost overlay zachováním aspektu
    if isinstance(position, dict):
        # Explicit pixel coords (ratios)
        target_w = int(page_w * position["width"])
        target_h = int(page_h * position["height"])
        target_x = int(page_w * position["x"])
        target_y = int(page_h * position["y"])
    else:
        target_h = int(page_h * height_ratio)
        target_w = int(page_w * width_ratio)
        # Resize zachová aspect, fit na width nebo height
        ow, oh = overlay_img.size
        scale = min(target_w / ow, target_h / oh)
        new_w = int(ow * scale)
        new_h = int(oh * scale)
        target_w, target_h = new_w, new_h

        if position == "top":
            target_x = (page_w - target_w) // 2
            target_y = 0
        elif position == "bottom":
            target_x = (page_w - target_w) // 2
            target_y = page_h - target_h
        elif position == "center":
            target_x = (page_w - target_w) // 2
            target_y = (page_h - target_h) // 2
        elif position == "full":
            # Roztáhnout přes celou stránku, zachovat aspect
            scale = max(page_w / ow, page_h / oh)
            target_w = int(ow * scale)
            target_h = int(oh * scale)
            target_x = (page_w - target_w) // 2
            target_y = (page_h - target_h) // 2
        else:
            raise ValueError(f"Unknown position: {position}")

    # Resize overlay
    overlay_img = overlay_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Apply fade gradient (alpha mask)
    if fade_bottom > 0 or fade_top > 0:
        # Vytvoř alpha mask s vertikálním gradient fade
        alpha = overlay_img.split()[3] if overlay_img.mode == "RGBA" else Image.new("L", overlay_img.size, 255)
        gradient = Image.new("L", (1, target_h))
        for y in range(target_h):
            opacity = 255
            if fade_bottom > 0:
                fade_start = int(target_h * (1 - fade_bottom))
                if y >= fade_start:
                    progress = (y - fade_start) / (target_h - fade_start)
                    opacity = int(255 * (1 - progress))
            if fade_top > 0:
                fade_end = int(target_h * fade_top)
                if y < fade_end:
                    progress = y / fade_end
                    opacity = int(255 * progress)
            gradient.putpixel((0, y), opacity)
        gradient = gradient.resize(overlay_img.size, Image.Resampling.NEAREST)

        # Combine alpha with fade gradient
        from PIL import ImageChops
        new_alpha = ImageChops.multiply(alpha, gradient)
        overlay_img.putalpha(new_alpha)

    # Paste s alpha
    if page_img.mode != "RGBA":
        page_img = page_img.convert("RGBA")
    page_img.alpha_composite(overlay_img, (target_x, target_y))

    return page_img


def process_page(page_path: Path, page_config: dict, base_dir: Path,
                 output_path: Path):
    """Process single page — apply all overlays defined in page_config."""
    overlays = page_config.get("overlays", [])
    if not overlays:
        return False

    page_img = Image.open(page_path)
    if page_img.mode != "RGBA":
        page_img = page_img.convert("RGBA")

    for overlay in overlays:
        asset_path = resolve_asset_path(overlay["asset"], base_dir)
        if not asset_path.exists():
            print(f"  ⚠ Asset not found: {asset_path}")
            continue
        page_img = apply_overlay(page_img, asset_path, overlay)

    # Convert back to RGB pro PNG bez alpha (pokud original byl bez alpha)
    if page_img.mode == "RGBA":
        bg = Image.new("RGB", page_img.size, (255, 255, 255))
        bg.paste(page_img, mask=page_img.split()[3])
        page_img = bg

    page_img.save(output_path, "PNG", optimize=True)
    return True


def main():
    parser = argparse.ArgumentParser(description="Apply Pillow overlays onto generated pages")
    parser.add_argument("--plan", required=True, help="Path to page-plan.json")
    parser.add_argument("--pages-dir", required=True, help="Directory with page-XX.png files")
    parser.add_argument("--base-dir", required=True, help="Base dir for resolving asset paths")
    parser.add_argument("--in-place", action="store_true",
                        help="Overwrite original page-XX.png (default: save as page-XX-final.png)")
    args = parser.parse_args()

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    pages_dir = Path(args.pages_dir)
    base_dir = Path(args.base_dir).resolve()

    print(f"🖼  Applying overlays from {Path(args.plan).name}")
    print(f"   Pages: {pages_dir}")
    print(f"   Base dir: {base_dir}")
    print()

    processed = 0
    for page in plan.get("pages", []):
        n = page["n"]
        overlays = page.get("overlays", [])
        if not overlays:
            continue

        page_path = pages_dir / f"page-{n:02d}.png"
        if not page_path.exists():
            print(f"  ⚠ Page {n:02d} source missing: {page_path.name}")
            continue

        if args.in_place:
            output_path = page_path
        else:
            output_path = pages_dir / f"page-{n:02d}-final.png"

        ok = process_page(page_path, page, base_dir, output_path)
        if ok:
            asset_names = [o["asset"] for o in overlays]
            print(f"  ✓ Page {n:02d}: {len(overlays)} overlay(s) applied → {output_path.name}")
            print(f"     assets: {asset_names}")
            processed += 1

    print()
    print(f"✅ Processed {processed} pages with overlays")


if __name__ == "__main__":
    main()
