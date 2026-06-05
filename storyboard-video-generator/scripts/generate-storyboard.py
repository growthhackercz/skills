#!/usr/bin/env python3
"""
generate-storyboard.py — generate master storyboard PNG via OpenClaw image_generate.

Reads `video-brief.json` and produces `01-master-storyboard.png` (~2400×1600 px)
following the layout in references/storyboard-layout-spec.md.

Usage:
    python3 generate-storyboard.py \
        --brief /documents/ads/video/[slug]/video-brief.json \
        --output /documents/ads/video/[slug]/01-master-storyboard.png \
        --backend fal

Backend options:
    fal       — FAL openai/gpt-image-2/edit (default, requires FAL_KEY)
    openclaw  — OpenClaw native image_generate (fallback when image_generate is in PATH)
"""
import argparse
import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from runtime_env import ensure_env_var


def load_brief(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_storyboard_prompt(brief: dict) -> str:
    """Build a single comprehensive prompt for the master storyboard PNG."""
    sc = brief.get("shared_choices", {})
    char = brief.get("character", {})
    cuts = brief.get("cuts", [])
    product_visual = brief.get("product_visual_identity", "")

    cuts_lines = []
    for i, c in enumerate(cuts, 1):
        cuts_lines.append(
            f"Cut {i}: {c.get('shot_type', 'WIDE')} {c.get('focal_length', '50mm')}, "
            f"{c.get('duration', 4)}s, {c.get('camera_move', 'STATIC')}. "
            f"{c.get('subject_framing', '')}"
        )

    cuts_block = "\n".join(cuts_lines)

    # If product_visual_identity is provided, inject it as a TOP-PRIORITY constraint
    # at the very start of the prompt — this is critical for storyboards involving a
    # specific real-world product, where GPT Image 2 tends to hallucinate generic shapes.
    product_lock = ""
    if product_visual:
        product_lock = f"""
⚠️⚠️⚠️ ABSOLUTE TOP-PRIORITY CONSTRAINT — PRODUCT IDENTITY LOCK ⚠️⚠️⚠️

{product_visual}

ALL attached reference images show the SAME product from different angles. The product silhouette, proportions, color split, branding decals, and overall geometry described in the constraint above are FIXED. You MUST treat these reference photos as a 100% accurate product photograph that has to be REPRODUCED PIXEL-PERFECT in every section of this storyboard where the product appears (hero props panel, every section 3 cut frame, environment ref, lighting reference frames). Do not stylize, simplify, paint, soften, illustrate, or invent variations of the product shape.

If the thumbnail is small, draw the product smaller — but at exactly the same proportions, NEVER stretched, squished, rotated, or rounded into a different silhouette. Treat the product as a real physical object that has been photographed and must look identical across every frame.

If you cannot match the product perfectly in a particular thumbnail, leave a clean silhouette outline of approximately correct shape rather than drawing a wrong-looking variant.

⚠️ SMALL-THUMBNAIL PROPORTION LOCK (critical for hero props panel + section 3 frames where the product is small in the frame):
When the product is rendered SMALL in any thumbnail, GPT often distorts proportions to fill space — DO NOT do this. Preserve the EXACT proportions described in the constraint above. If the thumbnail is small, draw the product smaller but at PROPORTIONALLY EXACT silhouette of the reference photo. Never elongate, stretch, or compress the product to fit a thumbnail aspect ratio.

⚠️ ABSOLUTE: every depiction of the product across all four sections must match the constraint and the attached reference photos. Do not introduce any other product. Do not borrow visual cues from other devices.

"""

    prompt = f"""{product_lock}Professional pre-production storyboard deck composed as a single A3 landscape page (2400×1600 px), \
ivory paper background (#F8F4EC), elegant editorial layout with serif headlines and sans-serif body type. \
Hand-typed character, polished but unfussy, vintage cinematography board feel.

⚠️ CRITICAL — SECTION 4 (STORYBOARD) RULE:
The cut frames in Section 4 (the storyboard strip in the bottom half of the page) MUST be PHOTOREALISTIC cinematic still frames — \
NOT pencil sketches, NOT illustrations, NOT paintings, NOT hand-drawn artwork. Each cut frame is the \
ACTUAL keyframe that will be fed into a video generation model (Seedance 2.0 image-to-video). \
Each thumbnail must look like a sharp professional cinematography still: photorealistic skin, photorealistic product, \
photorealistic lighting, photorealistic environment. Anamorphic 35mm film aesthetic (color grade) is fine, \
but the rendering technique is PHOTOREAL CINEMA — not artwork.

Sections 1, 2, and 4 (character reference, environment + floor plan, lighting/mood reference) MAY use \
mixed media — section 1 character views = photorealistic editorial portraits, section 2 environment refs = \
photorealistic interior photography (the floor plan diagram itself is allowed to be a hand-drawn top-down \
sketch, but the environment thumbnails next to it are photorealistic), section 4 lighting refs = photorealistic.

Across the entire deck, the PRODUCT must always match the reference photos precisely (see the product identity \
constraint at the top of this prompt). Do not invent or substitute another product.

NO TOP HEADER BAR — do not draw any "SHARED CHOICES" or summary header strip at the top of the page. The page begins immediately with Section 1 + Section 2 + Section 3 columns in the top zone. The top edge of the page has only a thin baseline divider (~5 px), no big header strip — every pixel of vertical space goes to the actual sections.

⚠️ OVERALL LAYOUT — STORYBOARD-DOMINANT (PROPORTIONS ARE STRICT):

{f'''⚠️ SCENE CONTINUITY (this brief has a fixed scene set):
{brief.get("scene_continuity")}

All {len(cuts)} storyboard cut frames depict the SAME PHYSICAL LOCATION at the SAME TIME OF DAY. The hero product, the architecture, and the lighting are FIXED IN SPACE — only the CAMERA changes position and lens between cuts. The product permanently occupies one specific spot (consult the floor plan in Section 2 — the position is fixed there). Camera moves around it; the product never teleports between cuts.

''' if brief.get("scene_continuity") else f'''ℹ️ MULTI-LOCATION ad — cuts MAY take place in different locations, settings, or times of day. Continuity is NOT enforced; treat each cut as an independent vignette stitched together by editing rather than by physical space. The product or character may appear in different rooms / outdoor settings / lighting conditions between cuts as the brief dictates.

'''}⚠️ HORIZONTAL DIVIDER POSITION — CRITICAL:
The page is 1600 px tall. The horizontal divider line MUST sit at y = 533 px from the top — i.e. the divider is at exactly 1/3 of the page height. This means:
  • TOP ZONE = exactly the first 533 px (1/3 of total height) — ONE-THIRD of page.
  • BOTTOM ZONE = exactly the remaining 1067 px (2/3 of total height) — TWO-THIRDS of page.
The bottom zone MUST visually be roughly TWICE as tall as the top zone. If the divider ends up at the middle (~800 px), the layout is WRONG. Push the top zone smaller — characters and refs are compact thumbnails, not full-bleed images.

  • TOP ZONE (533 px tall, 33 % of page) — context, in 3 vertical columns of widths 1/2 + 1/4 + 1/4.
    Column 3 (right, 1/4 wide) contains ONLY Section 3 (Lighting + Color palette). Section 5 (notes/audio) is in the bottom grid, NOT in the top zone.
  • BOTTOM ZONE (1067 px tall, 67 % of page) — UNIFORM GRID of {len(cuts) + 1} EQUAL-SIZE TILES:
{("    - 16:9 landscape video → 3-column × 2-row grid (cells 1-3 in row 1 = cuts 1-3, cells 4-5 in row 2 = cuts 4-5, cell 6 in row 2 = Section 5 NOTES)." if brief.get('aspect_ratio', '16:9') == '16:9' else "    - 9:16 vertical video → 6-column × 1-row strip (cells 1-5 = cuts 1-5 as vertical 9:16 frames side by side, cell 6 = Section 5 NOTES)." if brief.get('aspect_ratio', '16:9') == '9:16' else "    - 1:1 square video → 3-column × 2-row grid (same arrangement as 16:9, cells 1-5 = cuts, cell 6 = NOTES).")}
    All tiles are the EXACT same size. Cells 1-{len(cuts)} contain cut frames (numbered). The LAST cell ({len(cuts) + 1}) contains Section 5 NOTES (text only, no frame): mood keywords + audio cues + cinematography notes.
A thin horizontal divider line separates the top and bottom zones.

TOP HALF — 3 COLUMNS:
  • Column 1 (LEFT, ~1200 px wide, FULL top-half height) → Section 1: Character + hero props.
  • Column 2 (CENTER, ~600 px wide, FULL top-half height) → Section 2: Environment SKETCH (floor plan only).
  • Column 3 (RIGHT, ~600 px wide, FULL top-half height) → Section 3: Lighting refs + color palette (full height of column, no Section 5 here — that has moved to the bottom grid).

SECTION 1 (LEFT COLUMN, ~1200 × 720 px): "CHARACTER + HERO PROPS REFERENCE"
- 5 character thumbnails labeled FRONT VIEW, SIDE PROFILE, BACK VIEW, FACIAL CLOSE-UP, RELAXED POSE.
- The reference photos attached are ONLY the product (not the character). Generate character views from this description: {char.get('description', 'protagonist')}
- Wardrobe: {char.get('wardrobe', 'editorial neutral')}
- Hero-props panel below the character thumbnails — small isolated photographs of: {', '.join((char.get('hero_props') or ['ceramic mug', 'open book', 'white orchid'])[:5])}
- ⚠️ Hero-prop continuity: when a prop is something like a tap/faucet/spout, render the prop in its REAL functional context (e.g. tap mounted on counter with the sink basin visible below the spout, not floating in midair with water falling onto bare surface). Props must look like real photographs of the prop in its actual placement — not stylized cutouts that misrepresent how the prop is used.
- Italic note about character continuity across all cuts.

SECTION 2 (CENTER COLUMN, ~600 × 720 px): "ENVIRONMENT / FLOOR PLAN"
⚠️ THIS SECTION CONTAINS ONLY A HAND-DRAWN SKETCH — NO PHOTOGRAPHIC ENVIRONMENT THUMBNAILS.
- A single top-down hand-drawn architectural sketch / blueprint diagram (pencil-style on ivory paper) showing the location's floor plan: {sc.get('environment_fingerprint', 'cinematic location')}
- Numbered camera positions (1)..({len(cuts)}) drawn into the floor plan with arrows showing each camera move.
- Labels per cut on the diagram: "Cut 1 {cuts[0].get('camera_move', 'STATIC') if cuts else 'STATIC'}", "Cut 2 {cuts[1].get('camera_move', 'STATIC') if len(cuts) > 1 else 'STATIC'}"…
- Photorealistic photos of the environment are FORBIDDEN here — they confuse the video model. Sketch only.

SECTION 3 (RIGHT COLUMN, FULL TOP-ZONE HEIGHT, ~600 × 560 px): "LIGHTING REFERENCES + COLOR PALETTE"
- 3-4 small photorealistic lighting reference thumbnails (each ~140×100 px) with labels (e.g. "Soft morning window light", "Warm walnut accents", "Backlit window glow", "Quiet stillness").
- Color palette swatches (5 colors) in a row below the lighting refs.
- Section 5 (mood/audio/notes) is NOT here — it has been moved to the LAST cell of the bottom grid.

═══════════════════════════════════════════════════════════════
SECTION 4 (BOTTOM HALF — HERO, MUST OCCUPY 50 %+ OF TOTAL PAGE HEIGHT): "STORYBOARD ({len(cuts)} CUTS)"

This is the absolute centerpiece of the deck. The cut frames are the visual hero of the page.

- {len(cuts)} sequential photorealistic cinematic still frames, numbered 1 to {len(cuts)}.

⚠️ FRAME ASPECT RATIO — STRICT {brief.get('aspect_ratio', '16:9')} (NEVER SQUARE):
Every cut frame MUST be drawn in the EXACT aspect ratio of the final video: {brief.get('aspect_ratio', '16:9')}.
{"  • 16:9 means the frame is 1.778 TIMES WIDER than tall. If the frame is 400 px tall, it must be 711 px wide. If 350 px tall, 622 px wide. Width MUST be roughly 1.78× height." if brief.get('aspect_ratio', '16:9') == '16:9' else "  • 9:16 means the frame is 1.778 TIMES TALLER than wide. If the frame is 400 px wide, it must be 711 px tall." if brief.get('aspect_ratio', '16:9') == '9:16' else "  • 1:1 means width = height (square)."}
{"  • ABSOLUTELY FORBIDDEN — square frames (1:1), 4:3 frames, 3:2 frames, 2:1 frames, or anywhere between square and 16:9. The frame must clearly look like a cinema widescreen, NOT a Polaroid, NOT an Instagram post, NOT a 4:3 TV." if brief.get('aspect_ratio', '16:9') == '16:9' else "  • FORBIDDEN — square or near-square frames. Frame must clearly be VERTICAL (smartphone/Reel style)." if brief.get('aspect_ratio', '16:9') == '9:16' else ""}
The frames must look like proper {brief.get('aspect_ratio', '16:9')} cinema frames.

⚠️ FRAME SIZING — UNIFORM EQUAL-SIZE TILES:
ALL {len(cuts) + 1} tiles in the bottom grid (5 cut frames + 1 NOTES cell) must be the SAME SIZE.

{("⚠️ MANDATORY 16:9 LAYOUT — 3 columns × 2 rows = EXACTLY 6 cells:" + chr(10) + "    ROW 1 (top): cell 1 (Cut 1) | cell 2 (Cut 2) | cell 3 (Cut 3)" + chr(10) + "    ROW 2 (bottom): cell 4 (Cut 4) | cell 5 (Cut 5) | cell 6 (NOTES)" + chr(10) + "  Each cell ~" + str((2400 - 80) // 3) + "px wide × ~" + str((1020 - 40) // 2) + "px tall. Frame inside each cell: 16:9 → " + str((2400 - 80) // 3) + "×" + str(int((2400 - 80) // 3 * 9 / 16)) + " px." + chr(10) + "  ⚠️ NEVER place all 5 cuts in a single horizontal row of 6+ cells — that compresses frames too much. ALWAYS use 3×2 grid as described above." if brief.get('aspect_ratio', '16:9') == '16:9' else "⚠️ MANDATORY 9:16 LAYOUT — 6 columns × 1 row strip:" + chr(10) + "    Cells 1..5 (left to right): vertical 9:16 cut frames" + chr(10) + "    Cell 6 (rightmost): NOTES" + chr(10) + "  Each cell ~" + str((2400 - 80) // 6) + "px wide × ~" + str((1020 - 40)) + "px tall. Frame inside each cell: 9:16 → ~" + str((2400 - 80) // 6) + "×" + str(int((2400 - 80) // 6 * 16 / 9)) + " px." if brief.get('aspect_ratio', '16:9') == '9:16' else "⚠️ MANDATORY 1:1 LAYOUT — 3 columns × 2 rows = 6 cells (same arrangement as 16:9 grid). Frame inside each cell: 1:1 square ~" + str(min((2400 - 80) // 3, (1020 - 40) // 2)) + "×" + str(min((2400 - 80) // 3, (1020 - 40) // 2)) + " px.")}
  • Cells 1–{len(cuts)} contain the cut frames (numbered 1 to {len(cuts)}).
  • The LAST cell ({len(cuts) + 1}, bottom-right in 3×2 / right-most in 6×1 strip) contains Section 5 NOTES (text only, no frame): mood keywords + audio cues + cinematography notes.
  • All cut frames are the EXACT same size — never a mix of larger and smaller frames.
  • Caption strip below each cut frame is uniform: cut number left, metadata in small caps middle, italic 1-line description right.

- Each frame is photorealistic cinema (NOT pencil sketches, illustrations, paintings, or hand-drawn artwork).
- ⚠️ PER-CUT TILE LAYOUT (frame BIG, caption strip directly below):
  Each cut tile = the {brief.get('aspect_ratio', '16:9')} cinematic frame thumbnail (LARGEST POSSIBLE), with a thin caption strip immediately below it:
    • Frame thumbnail occupies the FULL tile width and ~85 % of tile height.
    • Below the frame, a single small horizontal strip (~60 px tall) contains: large cut number on the left (e.g. "1"), then metadata in small caps in the middle (focal length · duration · camera move · shot type), then 1-line italic prose description on the right.
  Frames are the visual hero of each tile — captions are slim and unobtrusive beneath them.

Per-cut details:
{cuts_block}

Style: editorial pre-production board, polished but unfussy. Anamorphic 35mm film color grade in storyboard cut frames. \
Section 4 cut frames are PHOTOREALISTIC cinematic stills (NOT sketches/illustrations). Section 1 character thumbnails \
are also PHOTOREALISTIC (except the floor plan diagram itself which is a hand-drawn top-down sketch). \
Section 3 lighting reference thumbnails are PHOTOREALISTIC. The deck headers, labels, captions, and floor plan \
diagram have a hand-typed editorial character. Cut frame thumbnails are full-color photorealistic stills. \
NO modern app UI elements. NO digital interface decorations."""

    return prompt


def collect_reference_images(brief: dict) -> list[str]:
    """Up to 3 reference images (max for OpenClaw native + FAL gpt-image-2).

    Strategy depends on whether product_visual_identity is set (i.e. there is a
    specific product whose appearance MUST be preserved):

    A) Product-locked mode (product_visual_identity present):
       Fill ALL 3 slots with product reference photos (hero + additional). This
       concentrates the model's "subject preservation" signal on the product. The
       character and environment are described in the prompt, not referenced visually.

    B) General mode (no product_visual_identity):
       Use brand library + product hero as before — balances tonality and product.
    """
    refs = []
    brand = brief.get("brand", {})
    product = brief.get("product") or {}
    has_strict_product = bool(brief.get("product_visual_identity"))

    if has_strict_product:
        # All 3 slots = product references
        product_candidates = [product.get("hero_image")]
        product_candidates.extend(product.get("additional_images") or [])
        for c in product_candidates:
            if c and Path(c).exists():
                refs.append(str(Path(c).resolve()))
                if len(refs) == 3:
                    break
        # If we have fewer than 3 product images, pad with brand stuff
        if len(refs) < 3:
            for c in [brand.get("brand_board"), brand.get("brand_kit")]:
                if c and Path(c).exists():
                    refs.append(str(Path(c).resolve()))
                    if len(refs) == 3:
                        break
    else:
        candidates = [
            brand.get("brand_board"),
            product.get("hero_image"),
            brand.get("brand_kit"),
        ]
        candidates.extend(product.get("additional_images") or [])
        for c in candidates:
            if c and Path(c).exists():
                refs.append(str(Path(c).resolve()))
                if len(refs) == 3:
                    break

    return refs


async def generate_via_openclaw(prompt: str, refs: list[str], output: Path) -> bool:
    """Call OpenClaw native image_generate via subprocess."""
    if not shutil.which("image_generate"):
        print("⚠️  image_generate not found in PATH; cannot use openclaw backend")
        return False

    cmd = [
        "image_generate", prompt,
        "--size", "2400x1600",
        "--output", str(output),
    ]
    for ref in refs:
        cmd.extend(["--reference", ref])

    print(f"→ Running: image_generate (size 2400x1600, refs={len(refs)})")
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"⚠️  image_generate failed (rc={proc.returncode}): {stderr.decode()[:500]}")
            # Try alternative flag name --image instead of --reference
            if refs and "--reference" in cmd:
                alt_cmd = ["image_generate", prompt, "--size", "2400x1600", "--output", str(output)]
                for ref in refs:
                    alt_cmd.extend(["--image", ref])
                print("→ Retrying with --image flag")
                proc2 = await asyncio.create_subprocess_exec(
                    *alt_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc2.communicate()
                if proc2.returncode != 0:
                    print(f"⚠️  alternative call also failed: {stderr.decode()[:500]}")
                    return False
        return output.exists() and output.stat().st_size > 50_000
    except Exception as e:
        print(f"⚠️  Exception in openclaw backend: {e}")
        return False


def encode_data_url(path: str) -> str:
    """Encode local file as data URL for FAL."""
    p = Path(path)
    suffix = p.suffix.lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(suffix, "image/png")
    with open(p, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


async def generate_via_fal(prompt: str, refs: list[str], output: Path) -> bool:
    """FAL gpt-image-2 fallback."""
    fal_key = ensure_env_var("FAL_KEY")
    if not fal_key:
        print("⚠️  FAL_KEY not set in env, ~/.openclaw/.env, or Control Center secret store; cannot use fal backend")
        return False

    try:
        import fal_client
    except ImportError:
        print("⚠️  fal_client not installed in provider image")
        return False

    os.environ["FAL_KEY"] = fal_key
    ref_data_urls = [encode_data_url(r) for r in refs]

    print(f"→ FAL openai/gpt-image-2/edit (refs={len(refs)})")
    try:
        handler = await fal_client.submit_async(
            "openai/gpt-image-2/edit",
            arguments={
                "prompt": prompt,
                "image_size": {"width": 2400, "height": 1600},
                "image_urls": ref_data_urls,
            },
        )
        result = await handler.get()
        url = result.get("images", [{}])[0].get("url")
        if not url:
            print(f"⚠️  FAL returned no image url: {result}")
            return False

        import requests
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(output, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return output.exists() and output.stat().st_size > 50_000
    except Exception as e:
        print(f"⚠️  FAL backend failed: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True, help="Path to video-brief.json")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument(
        "--backend",
        choices=["fal", "openclaw"],
        default="fal",
        help="Image generation backend (default: fal — openai/gpt-image-2/edit)",
    )
    args = parser.parse_args()

    brief_path = Path(args.brief)
    output_path = Path(args.output)

    if not brief_path.exists():
        print(f"❌ Brief not found: {brief_path}")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    brief = load_brief(brief_path)
    prompt = build_storyboard_prompt(brief)
    refs = collect_reference_images(brief)

    print(f"📋 Brief: {brief['campaign_slug']}")
    print(f"   Cuts: {len(brief.get('cuts', []))}")
    print(f"   Refs: {len(refs)}")
    print(f"   Backend: {args.backend}")

    if args.backend == "openclaw":
        ok = await generate_via_openclaw(prompt, refs, output_path)
        if not ok:
            print("→ Falling back to FAL...")
            ok = await generate_via_fal(prompt, refs, output_path)
    else:
        ok = await generate_via_fal(prompt, refs, output_path)
        if not ok and shutil.which("image_generate"):
            print("→ Falling back to OpenClaw native...")
            ok = await generate_via_openclaw(prompt, refs, output_path)

    if ok:
        print(f"✅ Master storyboard saved: {output_path}")
        print(f"   Size: {output_path.stat().st_size // 1024} KB")
        sys.exit(0)
    else:
        print("❌ Storyboard generation failed (both backends)")
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
