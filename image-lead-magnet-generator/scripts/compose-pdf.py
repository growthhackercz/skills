#!/usr/bin/env python3
"""
compose-pdf.py

Sestaví A4 PDF z vygenerovaných obrázků. Podporuje:
- Mixované orientace (portrait + landscape per stránka)
- Clickable hyperlink annotations (CTA buttons, URLs)

Konfigurace linků v page-plan.json:

    "pages": [
      {
        "n": 10,
        ...
        "links": [
          {
            "url": "https://akcelerator.cliqsales.cz",
            "rect": { "x": 0.08, "y": 0.84, "width": 0.84, "height": 0.06 },
            "label": "CTA button"
          }
        ]
      }
    ]

Pozn: rect je ve **screen coordinates ratios** (0-1):
  - x, y = top-left corner (0,0 je top-left stránky)
  - width, height = velikost obdélníku
Skript automaticky převede do PDF coords (které mají origin bottom-left).

Usage:
    python3 compose-pdf.py \\
        --pages-dir /documents/lead-magnets/[slug]/_pages-final/ \\
        --output /documents/lead-magnets/[slug]/lead-magnet-visual.pdf \\
        [--plan /documents/lead-magnets/[slug]/page-plan.json] \\
        [--orientation portrait|landscape|auto] \\
        [--title "Lead Magnet Title"] \\
        [--author "Author Name"]

Dependencies:
    pip install Pillow pypdf
"""

import argparse
import json
import re
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("❌ Missing Pillow: pip install Pillow")
    raise SystemExit(1)


# A4 v pixelech při 300 DPI
A4_PORTRAIT = (2480, 3508)
A4_LANDSCAPE = (3508, 2480)


def normalize_image(img_path: Path, target_orientation: str = "auto"):
    """Open image, normalize to A4 portrait/landscape at 300 DPI.
    Returns (PIL.Image, orientation_used).
    """
    img = Image.open(img_path)
    src_w, src_h = img.size

    if img.mode != "RGB":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            bg.paste(img, mask=img.split()[3])
        else:
            bg.paste(img)
        img = bg

    if target_orientation == "auto":
        orientation = "landscape" if src_w > src_h else "portrait"
    else:
        orientation = target_orientation

    if orientation == "landscape":
        target_w, target_h = A4_LANDSCAPE
    else:
        target_w, target_h = A4_PORTRAIT

    src_ratio = src_w / src_h
    target_ratio = target_w / target_h

    if abs(src_ratio - target_ratio) < 0.01:
        return img.resize((target_w, target_h), Image.Resampling.LANCZOS), orientation

    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))

    return img.resize((target_w, target_h), Image.Resampling.LANCZOS), orientation


def add_links_to_pdf(pdf_path: Path, plan: dict):
    """Add clickable hyperlink annotations to PDF using pypdf.
    Maps page number from plan → PDF page index → adds /Annot dict.
    """
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import (
            ArrayObject, NameObject, NumberObject, TextStringObject,
            DictionaryObject, FloatObject,
        )
    except ImportError:
        print("⚠ pypdf not installed — skipping link annotations")
        print("  Install: pip install pypdf")
        return

    pages_with_links = [p for p in plan.get("pages", []) if p.get("links")]
    if not pages_with_links:
        return

    print(f"\n🔗 Adding {sum(len(p['links']) for p in pages_with_links)} clickable link(s)...")

    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()

    for page_idx, page in enumerate(reader.pages):
        page_n = page_idx + 1
        page_config = next((p for p in plan["pages"] if p["n"] == page_n), None)
        writer.add_page(page)

        if not page_config or not page_config.get("links"):
            continue

        page_w = float(page.mediabox.width)
        page_h = float(page.mediabox.height)

        for link in page_config["links"]:
            url = link["url"]
            rect = link["rect"]

            # Convert screen coords (top-left origin) to PDF coords (bottom-left origin)
            x1 = rect["x"] * page_w
            x2 = (rect["x"] + rect["width"]) * page_w
            y2 = (1 - rect["y"]) * page_h
            y1 = (1 - rect["y"] - rect["height"]) * page_h

            annotation = DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject([
                    FloatObject(x1), FloatObject(y1),
                    FloatObject(x2), FloatObject(y2),
                ]),
                NameObject("/Border"): ArrayObject([
                    NumberObject(0), NumberObject(0), NumberObject(0)
                ]),
                NameObject("/A"): DictionaryObject({
                    NameObject("/Type"): NameObject("/Action"),
                    NameObject("/S"): NameObject("/URI"),
                    NameObject("/URI"): TextStringObject(url),
                }),
            })

            # Attach to current page (last added)
            current_page = writer.pages[-1]
            if "/Annots" in current_page:
                current_page["/Annots"].append(annotation)
            else:
                current_page[NameObject("/Annots")] = ArrayObject([annotation])

            label = link.get("label", "")
            print(f"  ✓ Page {page_n:02d}: link → {url} {f'({label})' if label else ''}")

    # Write back
    with open(pdf_path, "wb") as f:
        writer.write(f)


def compose(pages_dir: Path, output_path: Path,
            orientation: str = "auto",
            title: str = None, author: str = None,
            plan: dict = None):
    images = sorted(pages_dir.glob("page-*.png"))
    # Filter out -final.png variants — pokud existuje page-XX-final.png, použij ten
    final_images = sorted(pages_dir.glob("page-*-final.png"))
    if final_images:
        # Replace base page-XX.png with page-XX-final.png where applicable
        final_map = {f.stem.replace("-final", ""): f for f in final_images}
        images = [final_map.get(p.stem, p) for p in images if not p.stem.endswith("-final")]

    if not images:
        raise SystemExit(f"❌ No page-*.png files in {pages_dir}")

    print(f"📚 Composing {len(images)} pages → {output_path.name}")
    print(f"   Orientation mode: {orientation}")

    pil_pages = []
    orientations_used = []

    for img_path in images:
        m = re.match(r"page-(\d+)(-final)?\.png", img_path.name)
        if not m:
            continue
        page_n = int(m.group(1))
        normalized, used_orient = normalize_image(img_path, orientation)
        pil_pages.append(normalized)
        orientations_used.append(used_orient)
        print(f"  ▸ Page {page_n:02d} — {used_orient}")

    if not pil_pages:
        raise SystemExit("❌ No valid pages")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    save_kwargs = {
        "save_all": True,
        "append_images": pil_pages[1:],
        "resolution": 300.0,
        "format": "PDF",
    }
    if title:
        save_kwargs["title"] = title
    if author:
        save_kwargs["author"] = author

    pil_pages[0].save(output_path, **save_kwargs)

    # Post-process: add clickable links from plan
    if plan:
        add_links_to_pdf(output_path, plan)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    portrait_count = orientations_used.count("portrait")
    landscape_count = orientations_used.count("landscape")

    print()
    print(f"✅ PDF created → {output_path}")
    print(f"   Size: {size_mb:.2f} MB")
    print(f"   Pages: {len(pil_pages)} ({portrait_count} portrait + {landscape_count} landscape)")
    if landscape_count and portrait_count:
        print(f"   ℹ Mixed orientation — PDF reader auto-rotates pages")


def main():
    parser = argparse.ArgumentParser(description="Compose lead magnet PDF (mixed orientation + clickable links)")
    parser.add_argument("--pages-dir", required=True, help="Directory with page-XX.png files")
    parser.add_argument("--output", required=True, help="Output PDF path")
    parser.add_argument("--plan", help="Path to page-plan.json (for clickable links)")
    parser.add_argument("--orientation", choices=["portrait", "landscape", "auto"],
                        default="auto",
                        help="Orientation mode (default: auto-detect per page)")
    parser.add_argument("--title", help="PDF metadata title")
    parser.add_argument("--author", help="PDF metadata author")
    args = parser.parse_args()

    plan = None
    if args.plan:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))

    compose(
        Path(args.pages_dir),
        Path(args.output),
        orientation=args.orientation,
        title=args.title,
        author=args.author,
        plan=plan,
    )


if __name__ == "__main__":
    main()
