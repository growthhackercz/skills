#!/usr/bin/env python3
"""
generate-storyboard.py — master storyboard PNG (~2400×1600) přes FAL gpt-image-2/edit.

SEBESTAČNÝ pro video-generator (nezávislý na jiných skillech). Čte storyboard-brief
(`cuts` / `character` / `shared_choices` — adapter z video-brief.json) a vygeneruje
desku, kde je VŠECHEN vykreslený text v jazyce trhu (CZ default; EN/ES dle brief.language).

Použití:
    python3 generate-storyboard.py --brief _storyboard-brief.json --output 01-master-storyboard.png

Vyžaduje FAL_KEY + fal_client + requests. Volitelný --backend openclaw (image_generate v PATH).
"""
from __future__ import annotations
import argparse
import asyncio
import base64
import json
import os
import shutil
import sys
from pathlib import Path

# 🛑 Nadpisy/popisky desky per jazyk trhu — CZ je default. VŠECHEN vykreslený text
# musí být v jazyce trhu (žádná angličtina na CZ desce). Technické zkratky záběrů
# (WIDE, MEDIUM, 85 mm, STATIC, SLOW-MO, PUSH-IN…) jsou filmový standard a zůstávají.
LABELS = {
    "cs": {
        "lang_name": "CZECH", "diac": "with correct Czech diacritics (á č ď é ě í ň ó ř š ť ú ů ý ž)",
        "s1_title": "POSTAVY + KLÍČOVÉ REKVIZITY",
        "views": "ČELNÍ POHLED, Z PROFILU, ZEZADU, DETAIL OBLIČEJE, UVOLNĚNÁ PÓZA",
        "hero_props": "KLÍČOVÉ REKVIZITY (MUSÍ SEDĚT S FINÁLNÍM PRODUKTEM)",
        "s2_title": "PROSTŘEDÍ / PŮDORYS", "cut_word": "Záběr",
        "s3_title": "SVĚTLO + BAREVNÁ PALETA", "palette": "BAREVNÁ PALETA",
        "s4_title": "STORYBOARD", "cuts_word": "ZÁBĚRŮ",
        "notes": "POZNÁMKY", "mood": "NÁLADA / KLÍČOVÁ SLOVA",
        "audio": "ZVUK (JEN SFX)", "cine": "KAMERA / POZNÁMKY",
        "continuity_note": "Postavy a jejich charakter zůstávají konzistentní napříč všemi záběry.",
    },
    "en": {
        "lang_name": "ENGLISH", "diac": "",
        "s1_title": "CHARACTER + HERO PROPS REFERENCE",
        "views": "FRONT VIEW, SIDE PROFILE, BACK VIEW, FACIAL CLOSE-UP, RELAXED POSE",
        "hero_props": "HERO PROPS (MUST MATCH FINAL PRODUCT)",
        "s2_title": "ENVIRONMENT / FLOOR PLAN", "cut_word": "Cut",
        "s3_title": "LIGHTING REFERENCES + COLOR PALETTE", "palette": "COLOR PALETTE",
        "s4_title": "STORYBOARD", "cuts_word": "CUTS",
        "notes": "NOTES", "mood": "MOOD / KEYWORDS",
        "audio": "AUDIO CUES (SFX ONLY)", "cine": "CINEMATOGRAPHY NOTES",
        "continuity_note": "Characters stay consistent across all cuts.",
    },
    "es": {
        "lang_name": "SPANISH", "diac": "with correct Spanish accents (á é í ó ú ñ ¿ ¡)",
        "s1_title": "PERSONAJES + ATREZO CLAVE",
        "views": "VISTA FRONTAL, PERFIL, VISTA TRASERA, PRIMER PLANO, POSE RELAJADA",
        "hero_props": "ATREZO CLAVE (DEBE COINCIDIR CON EL PRODUCTO FINAL)",
        "s2_title": "ENTORNO / PLANO", "cut_word": "Plano",
        "s3_title": "ILUMINACIÓN + PALETA DE COLOR", "palette": "PALETA DE COLOR",
        "s4_title": "STORYBOARD", "cuts_word": "PLANOS",
        "notes": "NOTAS", "mood": "TONO / PALABRAS CLAVE",
        "audio": "AUDIO (SOLO SFX)", "cine": "NOTAS DE CÁMARA",
        "continuity_note": "Los personajes se mantienen consistentes en todos los planos.",
    },
}


def load_brief(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_storyboard_prompt(brief: dict) -> str:
    L = LABELS.get(brief.get("language", "cs"), LABELS["cs"])
    sc = brief.get("shared_choices", {})
    char = brief.get("character", {})
    cuts = brief.get("cuts", [])
    product_visual = brief.get("product_visual_identity", "")

    cuts_block = "\n".join(
        f"{L['cut_word']} {i}: {c.get('shot_type', 'WIDE')} {c.get('focal_length', '50mm')}, "
        f"{c.get('duration', 4)}s, {c.get('camera_move', 'STATIC')}. {c.get('subject_framing', '')}"
        for i, c in enumerate(cuts, 1)
    )

    product_lock = ""
    if product_visual:
        product_lock = f"""⚠️⚠️⚠️ ABSOLUTE TOP-PRIORITY CONSTRAINT — PRODUCT IDENTITY LOCK ⚠️⚠️⚠️

{product_visual}

All attached reference images show the SAME product from different angles. Reproduce it PIXEL-PERFECT wherever it appears (hero props panel, every cut frame, lighting refs). Never stylize, stretch, rotate or invent variations; if unsure in a small thumbnail, draw a clean correct-proportion silhouette instead of a wrong variant.

"""

    ar = brief.get("aspect_ratio", "16:9")
    n = len(cuts)

    lang_mandate = (
        f"🛑🛑 LANGUAGE OF ALL RENDERED DECK TEXT = {L['lang_name']} {L['diac']}. "
        f"EVERY visible word drawn on the deck — section titles, view labels, prop labels, floor-plan cut labels, "
        f"palette label, notes/mood/audio/camera headings and their content, per-cut captions — MUST be written in {L['lang_name']}. "
        f"Do NOT output any English word anywhere on the deck (unless {L['lang_name']} IS English). "
        f"Use EXACTLY these section titles verbatim: \"{L['s1_title']}\", \"{L['s2_title']}\", \"{L['s3_title']}\", "
        f"\"{L['s4_title']} ({n} {L['cuts_word']})\", \"{L['notes']}\". "
        f"Character view labels EXACTLY: {L['views']}. Palette label: \"{L['palette']}\". "
        f"Notes cell sub-headings EXACTLY: \"{L['mood']}\", \"{L['audio']}\", \"{L['cine']}\". "
        f"Technical shot abbreviations (WIDE, MEDIUM, 85mm, STATIC, SLOW-MO, HANDHELD, PUSH-IN, END-CARD) may stay as-is.\n\n"
    )

    continuity = (
        f"""⚠️ SCENE CONTINUITY (fixed scene set):
{brief.get("scene_continuity")}
All {n} cut frames = SAME physical location, SAME time of day; only the CAMERA changes between cuts.

""" if brief.get("scene_continuity") else
        "ℹ️ MULTI-LOCATION ad — cuts may be different places/times; continuity not enforced.\n\n"
    )

    if ar == "16:9":
        grid = (f"3 columns × 2 rows = 6 cells. ROW 1: cell 1 (Cut 1) | cell 2 (Cut 2) | cell 3 (Cut 3); "
                f"ROW 2: cell 4 (Cut 4) | cell 5 (Cut 5) | cell 6 (NOTES). Frame per cell 16:9 (width ≈ 1.78× height). "
                f"NEVER put all cuts in one horizontal row.")
        ar_rule = "16:9 = frame 1.78× wider than tall. FORBIDDEN: square, 4:3, 3:2. Must read as cinema widescreen."
    elif ar == "9:16":
        grid = (f"6 columns × 1 row strip. Cells 1..{n} = vertical 9:16 cut frames left→right; last cell = NOTES. "
                f"Frame per cell 9:16 (taller than wide).")
        ar_rule = "9:16 = frame 1.78× taller than wide. FORBIDDEN: square/near-square. Must read as vertical smartphone/Reel."
    else:
        grid = "3 columns × 2 rows = 6 cells (as 16:9). Frame per cell = 1:1 square."
        ar_rule = "1:1 = width equals height (square)."

    prompt = f"""{product_lock}{lang_mandate}Professional pre-production storyboard deck as a single A3 landscape page (2400×1600 px), \
ivory paper background (#F8F4EC), elegant editorial layout, serif headlines + sans-serif body, vintage cinematography board feel.

⚠️ SECTION 4 (STORYBOARD) cut frames MUST be PHOTOREALISTIC cinematic stills (NOT sketches/illustrations/paintings) — \
each is the ACTUAL keyframe fed to a video model. Photoreal skin, product, lighting, environment; anamorphic 35mm color grade is fine, technique is PHOTOREAL CINEMA.
Sections 1–3 may be mixed media: character views = photoreal editorial portraits; environment = hand-drawn top-down floor-plan sketch only; lighting refs = photoreal.

NO top header bar — page begins immediately with the Section 1 + 2 + 3 columns; only a thin baseline divider at top.

{continuity}⚠️ LAYOUT (STORYBOARD-DOMINANT, strict): page 1600 px tall, horizontal divider at y≈533 (1/3). TOP ZONE = first 533 px (context, 3 columns 1/2 + 1/4 + 1/4). BOTTOM ZONE = remaining 1067 px (2/3) = uniform grid of {n + 1} EQUAL tiles ({grid}). All tiles same size; cells 1–{n} = numbered cut frames, last cell = {L['notes']} (text only).

TOP HALF — 3 COLUMNS:
  • Column 1 (LEFT, ~1200 px) → SECTION 1 "{L['s1_title']}": 5 character thumbnails labeled {L['views']}. Character generated from description (references are the product only): {char.get('description', 'protagonist')}. Wardrobe: {char.get('wardrobe', 'editorial neutral')}. Below: hero-props panel "{L['hero_props']}" — small isolated photos of: {', '.join((char.get('hero_props') or ['produkt'])[:5])}. Italic note: "{L['continuity_note']}"
  • Column 2 (CENTER, ~600 px) → SECTION 2 "{L['s2_title']}": ONLY a hand-drawn top-down architectural floor-plan sketch (pencil on ivory) of: {sc.get('environment_fingerprint', 'cinematic location')}. Numbered camera positions (1)..({n}) with arrows; per-cut labels like "{L['cut_word']} 1 STATIC". NO photographic environment thumbnails here.
  • Column 3 (RIGHT, ~600 px) → SECTION 3 "{L['s3_title']}": 3–4 small photoreal lighting-reference thumbnails with short {L['lang_name']} labels; below them a row of 5 color-palette swatches under label "{L['palette']}".

SECTION 4 (BOTTOM HALF, HERO, 50 %+ of page) "{L['s4_title']} ({n} {L['cuts_word']})":
- {n} sequential PHOTOREALISTIC cinematic still frames, numbered 1..{n}, each in STRICT {ar} aspect ratio ({ar_rule}).
- Uniform equal tiles ({grid}). Each tile = the {ar} frame (full tile width, ~85 % height) + a thin caption strip below: big cut number left, metadata small-caps middle (focal length · duration · camera move · shot type), 1-line italic {L['lang_name']} description right.
Per-cut details:
{cuts_block}

Style: editorial pre-production board, polished but unfussy, anamorphic 35mm grade in the cut frames; deck headers/labels/captions hand-typed editorial character. NO app UI elements, NO digital interface decorations. Remember: ALL rendered deck text in {L['lang_name']}."""

    return prompt


def collect_reference_images(brief: dict) -> list:
    refs = []
    brand = brief.get("brand", {})
    product = brief.get("product") or {}
    if brief.get("product_visual_identity"):
        cands = [product.get("hero_image")] + (product.get("additional_images") or []) \
                + [brand.get("brand_board"), brand.get("brand_kit")]
    else:
        cands = [brand.get("brand_board"), product.get("hero_image"), brand.get("brand_kit")] \
                + (product.get("additional_images") or [])
    for c in cands:
        if c and Path(c).exists():
            refs.append(str(Path(c).resolve()))
            if len(refs) == 3:
                break
    return refs


def encode_data_url(path: str) -> str:
    p = Path(path); suffix = p.suffix.lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(suffix, "image/png")
    with open(p, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("utf-8")


async def generate_via_openclaw(prompt: str, refs: list, output: Path) -> bool:
    if not shutil.which("image_generate"):
        return False
    cmd = ["image_generate", prompt, "--size", "2400x1600", "--output", str(output)]
    for ref in refs:
        cmd.extend(["--reference", ref])
    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
        return output.exists() and output.stat().st_size > 50_000
    except Exception as e:
        print(f"⚠️  openclaw backend: {e}"); return False


async def generate_via_fal(prompt: str, refs: list, output: Path) -> bool:
    if not os.environ.get("FAL_KEY"):
        print("⚠️  FAL_KEY není nastavený"); return False
    try:
        import fal_client, requests
    except ImportError:
        print("⚠️  chybí fal_client / requests"); return False
    ref_urls = [encode_data_url(r) for r in refs]
    print(f"→ FAL openai/gpt-image-2/edit (refs={len(refs)})")
    for attempt in range(4):
        try:
            h = await fal_client.submit_async("openai/gpt-image-2/edit", arguments={
                "prompt": prompt, "image_size": {"width": 2400, "height": 1600}, "image_urls": ref_urls})
            result = await h.get()
            url = result.get("images", [{}])[0].get("url")
            if not url:
                print(f"⚠️  FAL bez url: {result}"); return False
            resp = requests.get(url, stream=True, timeout=90); resp.raise_for_status()
            with open(output, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return output.exists() and output.stat().st_size > 50_000
        except Exception as e:
            if attempt == 3:
                print(f"⚠️  FAL backend selhal: {e}"); return False
            await asyncio.sleep(4 * (attempt + 1))
    return False


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True, help="storyboard-brief.json (cuts/character/shared_choices)")
    ap.add_argument("--output", required=True)
    ap.add_argument("--backend", choices=["fal", "openclaw"], default="fal")
    a = ap.parse_args()

    bp = Path(a.brief); out = Path(a.output)
    if not bp.exists():
        print(f"❌ brief nenalezen: {bp}"); sys.exit(1)
    out.parent.mkdir(parents=True, exist_ok=True)

    brief = load_brief(bp)
    prompt = build_storyboard_prompt(brief)
    refs = collect_reference_images(brief)
    print(f"📋 {brief.get('campaign_slug', bp.stem)} | cuts={len(brief.get('cuts', []))} | jazyk={brief.get('language', 'cs')} | refs={len(refs)}")
    if not refs:
        print("⚠️  bez referenčního obrázku gpt-image-2/edit selže — dodej brand-board / produktovou fotku do brief.brand/product")

    if a.backend == "openclaw":
        ok = await generate_via_openclaw(prompt, refs, out) or await generate_via_fal(prompt, refs, out)
    else:
        ok = await generate_via_fal(prompt, refs, out)
        if not ok and shutil.which("image_generate"):
            ok = await generate_via_openclaw(prompt, refs, out)

    if ok:
        print(f"✅ storyboard: {out} ({out.stat().st_size // 1024} KB)"); sys.exit(0)
    print("❌ generování storyboardu selhalo"); sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
