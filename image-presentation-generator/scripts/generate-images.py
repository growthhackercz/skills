#!/usr/bin/env python3
"""
generate-images.py

Batch generování 16:9 slidů prezentace přes GPT Image 2.
Podporuje 3 backendy (volba uživatele v skill Krok 0.2):
- openclaw (default): OpenClaw native image_generate tool — built-in, žádný API key
- openrouter: OpenRouter proxy s modelem openai/gpt-image-2 — vyžaduje OPENROUTER_API_KEY
- fal: FAL endpoint fal-ai/gpt-image-2 + reference images base64 — vyžaduje FAL_KEY

Reference images se posílají jako base64 (fal/openrouter) nebo file paths (openclaw).
Brand library se čte z /documents/brand/ — brand-board.png + brand-kit/*.

Každý slide v page-plan.json má pole "orientation" (typicky "widescreen" = 16:9).

Usage:
    python3 generate-images.py \\
        --plan /documents/presentations/[slug]/slide-plan.json \\
        --prompts-dir /documents/presentations/[slug]/_prompts/ \\
        --references-dir /documents/brand/ \\
        --output-dir /documents/presentations/[slug]/_slides/ \\
        --resolution draft \\
        --backend openclaw

    # Regenerace jen vybraných stránek:
    python3 generate-images.py ... --only "3,7,12"

    # OpenRouter backend
    python3 generate-images.py ... --backend openrouter

    # FAL backend (dev/test mimo OpenClaw runtime)
    python3 generate-images.py ... --backend fal

Dependencies:
    pip install fal-client requests pyyaml Pillow
    # backend-specific env:
    export FAL_KEY="..."             # pro --backend fal
    export OPENROUTER_API_KEY="..."  # pro --backend openrouter
"""

import argparse
import asyncio
import base64
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install fal-client requests pyyaml Pillow")
    sys.exit(1)


# ─── Resolution presets ─────────────────────────────────────────────
# Pro openai/gpt-image-2 (BYOK přes OpenAI) jsou limity volnější než fal-ai/*.
# Edges MUSÍ být multiples of 16, total pixels max ~8.29M.
#
# Prezentační slidy jsou 16:9 (widescreen) = výchozí orientace. Čisté 16:9,
# kde jsou OBĚ hrany násobky 16, existuje jen pro k násobek 16:
#   1280×720 (0.92M) · 2560×1440 (3.69M) · 3840×2160 (8.29M = přesně limit).
# Proto: draft 1280×720, final 2560×1440 (ostré na obrazovku i v PDF decku).
# Volitelně portrait (9:16, stories) a square (1:1, social) varianty.
RESOLUTIONS = {
    "draft":  {"widescreen": (1280, 720),   "portrait": (720, 1280),   "square": (1024, 1024)},   # rychlý review
    "final":  {"widescreen": (2560, 1440),  "portrait": (1440, 2560),  "square": (2048, 2048)},   # produkční deck
    "hi-end": {"widescreen": (2560, 1440),  "portrait": (1440, 2560),  "square": (2048, 2048)},   # 3840×2160 je na limitu → držíme final
}


# ─── Brand library detection ────────────────────────────────────────
def find_brand_board(brand_dir: Path) -> Path:
    """Find brand-board.png with fallback names."""
    candidates = ["brand-board.png", "brandboard.png", "moodboard.png",
                  "brand-board.jpg", "brandboard.jpg"]
    for name in candidates:
        path = brand_dir / name
        if path.exists():
            return path
    return None


def find_pdf_inspiration(brand_kit_dir: Path) -> Path:
    """Find layout-language brand-kit reference (PDF/prezentační inspirace).

    Pokud brand-kit obsahuje ukázku layout language (mřížky, karty, diagramy),
    použije se jako sekundární reference pro kompoziční jazyk slidů.
    """
    candidates = ["08-inspirace-pro-pdf-materialy.png", "08-pdf-inspirace.png",
                  "presentation-style.png", "slide-layout-inspiration.png",
                  "pdf-style.png", "pdf-mockups.png", "pdf-layout-inspiration.png"]
    for name in candidates:
        path = brand_kit_dir / name
        if path.exists():
            return path
    return None


# ─── Reference image selection per layout ───────────────────────────
# Slugy odpovídají layoutům v references/slide-layouts.md. Layouty, které tu
# nejsou, dostanou jen brand-board (řeší get_references_for_page default).
LAYOUT_TO_KIT_FILE = {
    # Produkt / showcase → hero mockup
    "product-hero-mockup": "01-hero-mockup.png",
    "product-annotated": "01-hero-mockup.png",
    "endcap-product-context": "01-hero-mockup.png",
    "cover-floating-3d": "01-hero-mockup.png",
    # Data / mřížky / UI → app mockup
    "kpi-dashboard": "07-app-mockup.png",
    "feature-grid": "07-app-mockup.png",
    "icon-grid": "07-app-mockup.png",
    "bento-box": "07-app-mockup.png",
    # Citáty / dopis → letterhead
    "pull-quote-spread": "03-letterhead.png",
    "founder-letter": "03-letterhead.png",
}


def find_brand_logo(brand_dir: Path) -> Path:
    """Find brand logo with fallback names."""
    candidates = ["logo.png", "logo.svg", "logo.jpg", "logo.webp",
                  "brand-logo.png", "brand-logo.svg"]
    for name in candidates:
        path = brand_dir / name
        if path.exists():
            return path
    return None


def resolve_product_image(page: dict, brand_dir: Path) -> Path:
    """Najdi produktovou referenční fotku pro slide, pokud je zadaná.

    Dva způsoby zadání v slide-plan.json:
      a) page.content.product_image_path — cesta relativní k projekt rootu (parent of brand/)
      b) legacy: page.product_slug + page.product_image_filename
         → brand/products/<slug>/images/<filename>
    """
    content = page.get("content", {})
    p = content.get("product_image_path")
    if p:
        cand = brand_dir.parent / p
        if cand.exists():
            return cand
    slug = page.get("product_slug")
    fn = page.get("product_image_filename")
    if slug and fn:
        cand = brand_dir / "products" / slug / "images" / fn
        if cand.exists():
            return cand
    return None


def get_references_for_page(page: dict, brand_dir: Path) -> list:
    """Return up to 3 reference image paths for given page.

    KRITICKÉ: pokud je u slidu zadaná produktová fotka, MÁ PŘEDNOST — musí se
    vejít do top 3 referencí, aby GPT Image 2 reprodukoval reálný produkt a ne
    vymyšlený. Proto se vkládá hned po logu, PŘED brand-board / kit inspirací.

    Priorita (max 3):
    1. Logo (jen cover/CTA slidy) — malé, jen pro brand mark
    2. Produktová fotka (pokud zadaná) — věrnost reálnému produktu
    3. brand-board.png (global mood / paleta)
    4. 08-inspirace / layout-specific kit (jen pokud zbývá místo)
    """
    refs = []

    layout = page.get("layout", "")
    is_cover_or_cta = layout in ("cover-cinematic", "cover-typographic",
                                  "cover-diagonal-split", "cover-floating-3d",
                                  "cta-gradient-panel", "endcap-product-context",
                                  "contact-card")

    # 1. Logo (cover/CTA nebo explicitně vyžádané) — jako brand mark
    if is_cover_or_cta or page.get("content", {}).get("logo_required"):
        logo = find_brand_logo(brand_dir)
        if logo:
            refs.append(logo)

    # 2. Produktová fotka — VYSOKÁ PRIORITA (hned po logu), aby se vždy vešla do top 3
    product_img = resolve_product_image(page, brand_dir)
    if product_img and product_img not in refs:
        refs.append(product_img)

    # 3. brand-board (global mood / paleta)
    brand_board = find_brand_board(brand_dir)
    if brand_board and brand_board not in refs and len(refs) < 3:
        refs.append(brand_board)

    # 4. Doplň layout-language referencí jen pokud zbývá místo:
    #    nejdřív layout-specific kit, jinak 08-inspirace.
    brand_kit_dir = brand_dir / "brand-kit"
    if brand_kit_dir.exists() and len(refs) < 3:
        kit_filename = LAYOUT_TO_KIT_FILE.get(layout)
        added = False
        if kit_filename:
            kit_file = brand_kit_dir / kit_filename
            if kit_file.exists() and kit_file not in refs:
                refs.append(kit_file)
                added = True
        if not added and len(refs) < 3:
            pdf_insp = find_pdf_inspiration(brand_kit_dir)
            if pdf_insp and pdf_insp not in refs:
                refs.append(pdf_insp)

    # FAL/OpenClaw limit: max 3 reference images
    return refs[:3]


def encode_reference_as_data_url(ref_path: Path) -> str:
    """Encode local image file as base64 data URL for FAL.

    Auto-padds extreme aspect ratios (>2.8:1) to fit FAL 3:1 max limit.
    Typical issue: brand logos that are very wide (e.g. 1500×400 = 3.75:1).
    Solution: add transparent/white padding to bring within 3:1.
    """
    try:
        from PIL import Image, ImageOps
    except ImportError:
        # Fallback bez PIL — encode raw, FAL může vrátit aspect error
        with open(ref_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        ext = ref_path.suffix.lower().lstrip(".")
        mime = "image/png" if ext == "png" else f"image/{ext}"
        return f"data:{mime};base64,{encoded}"

    img = Image.open(ref_path)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    w, h = img.size
    ratio = max(w, h) / min(w, h)

    # FAL limit je 3:1, padneme na bezpečných 2.5:1 aby byla rezerva
    SAFE_RATIO = 2.5

    if ratio > SAFE_RATIO:
        # Foto s extreme aspect — pad na square (1:1) zachová zdrojový obsah
        # i pro reference image to GPT Image 2.
        max_edge = max(w, h)
        new_size = max_edge

        # Vytvoř canvas a vlož image vystředěné
        if img.mode == "RGBA":
            canvas = Image.new("RGBA", (new_size, new_size), (255, 255, 255, 0))
        else:
            canvas = Image.new("RGB", (new_size, new_size), (255, 255, 255))

        offset_x = (new_size - w) // 2
        offset_y = (new_size - h) // 2
        canvas.paste(img, (offset_x, offset_y), img if img.mode == "RGBA" else None)
        img = canvas
        print(f"    ⓘ {ref_path.name}: {w}×{h} (ratio {ratio:.2f}:1) → padded to {new_size}×{new_size}")

    # Encode to PNG bytes
    import io
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


# ─── Backend: FAL ───────────────────────────────────────────────────
async def generate_via_fal(page, prompt, refs, output_path, size_wh):
    """Generate via FAL endpoint fal-ai/gpt-image-2."""
    try:
        import fal_client
    except ImportError:
        raise RuntimeError("Missing fal-client. Run: pip install fal-client")

    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise RuntimeError("FAL_KEY environment variable not set")
    os.environ["FAL_KEY"] = fal_key

    width, height = size_wh

    # Endpoint volba podle toho, jestli máme reference images:
    # - S reference: openai/gpt-image-2/edit (image-to-image, parametr image_urls)
    # - Bez reference: openai/gpt-image-2 (text-to-image)
    # Tvůj FAL account má přístup k openai/* namespace (BYOK přes OpenAI).
    if refs:
        endpoint = "openai/gpt-image-2/edit"
    else:
        endpoint = "openai/gpt-image-2"

    arguments = {
        "prompt": prompt,
        "image_size": {"width": width, "height": height},
        "num_images": 1,
        "output_format": "png",
        "quality": os.environ.get("FAL_QUALITY", "high"),  # low / medium / high
    }

    if refs:
        # /edit endpoint očekává image_urls (array of URLs nebo data URIs)
        reference_data_urls = [encode_reference_as_data_url(ref) for ref in refs]
        arguments["image_urls"] = reference_data_urls

    # BYOK — předá OpenAI key přes FAL. Routing pak jde přes vlastní OpenAI quota.
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        arguments["openai_api_key"] = openai_key

    handler = await asyncio.to_thread(
        fal_client.submit, endpoint, arguments=arguments
    )
    result = await asyncio.to_thread(handler.get)

    if not result or "images" not in result or not result["images"]:
        raise ValueError("FAL returned no images")

    image_url = result["images"][0]["url"]
    seed = result.get("seed")

    # Download
    resp = await asyncio.to_thread(requests.get, image_url, timeout=120)
    resp.raise_for_status()
    output_path.write_bytes(resp.content)

    return {
        "page_n": page["n"],
        "status": "success",
        "path": str(output_path),
        "seed": seed,
        "fal_request_id": result.get("request_id"),
    }


# ─── Backend: OpenRouter ────────────────────────────────────────────
async def generate_via_openrouter(page, prompt, refs, output_path, size_wh):
    """Generate via OpenRouter proxy s modelem openai/gpt-image-2.

    Endpoint: POST https://openrouter.ai/api/v1/images/generations
    Auth: Bearer $OPENROUTER_API_KEY
    Body kompatibilní s OpenAI Images API.

    Reference images (image-to-image): pokud model approuter routes přes
    OpenAI image edit endpoint, podporuje `image_urls` (base64 data URIs).
    Pokud OpenRouter konkrétní model image-to-image nepodporuje,
    reference images se ignorují a generuje se text-to-image.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY environment variable not set")

    width, height = size_wh
    body = {
        "model": "openai/gpt-image-2",
        "prompt": prompt,
        "size": f"{width}x{height}",
        "n": 1,
        "response_format": "b64_json",  # vrátí base64 přímo, žádný download
        "quality": os.environ.get("OPENROUTER_QUALITY", "high"),
    }

    if refs:
        # Pokud OpenRouter routes přes OpenAI image edit, reference jdou přes image_urls
        reference_data_urls = [encode_reference_as_data_url(ref) for ref in refs]
        body["image_urls"] = reference_data_urls

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://cliqsales.com",  # optional, pro OpenRouter analytics
        "X-Title": "CliqSales image-lead-magnet-generator",
    }

    resp = await asyncio.to_thread(
        requests.post,
        "https://openrouter.ai/api/v1/images/generations",
        headers=headers,
        json=body,
        timeout=180,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"OpenRouter API failed (HTTP {resp.status_code}): {resp.text[:500]}"
        )

    data = resp.json()
    if "data" not in data or not data["data"]:
        raise ValueError(f"OpenRouter returned no images: {data}")

    item = data["data"][0]
    if "b64_json" in item:
        output_path.write_bytes(base64.b64decode(item["b64_json"]))
    elif "url" in item:
        dl = await asyncio.to_thread(requests.get, item["url"], timeout=120)
        dl.raise_for_status()
        output_path.write_bytes(dl.content)
    else:
        raise ValueError(f"OpenRouter response missing b64_json/url: {item}")

    return {
        "page_n": page["n"],
        "status": "success",
        "path": str(output_path),
        "openrouter_model": body["model"],
    }


# ─── Backend: OpenClaw native (PRODUCTION DEFAULT) ──────────────────
async def generate_via_openclaw(page, prompt, refs, output_path, size_wh):
    """Generate via OpenClaw native image_generate tool.

    Vyžaduje: image_generate v PATH (built-in OpenClaw runtime).

    CLI invocation:
        image_generate "<prompt>" \
          --size WIDTHxHEIGHT \
          --output PATH \
          [--reference PATH]*  (max 3)

    Output pattern může se lišit podle OpenClaw verze:
    - Některé verze: `image_generate <prompt> -o PATH`
    - Některé: `image_generate <prompt> --output=PATH`
    - Některé: stdout obsahuje JSON s `output_path`

    Tato implementace zkusí standardní `--output PATH` nejdříve;
    pokud neuspěje, zkusí alternativní invocations.
    """
    width, height = size_wh

    # Stavba CLI command
    cmd = [
        "image_generate",
        prompt,
        "--size", f"{width}x{height}",
        "--output", str(output_path),
    ]

    # Reference images (image-to-image guidance) — až 3
    for ref in refs:
        cmd.extend(["--reference", str(ref)])

    # Spustit subprocess
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        err = stderr.decode("utf-8", errors="replace").strip()
        # Pokud `--reference` flag neexistuje, retry s alternativním názvem
        if "unrecognized" in err.lower() and "reference" in err.lower():
            return await _generate_via_openclaw_alternative(
                page, prompt, refs, output_path, size_wh, alt_flag="--image"
            )
        raise RuntimeError(f"image_generate failed (exit {proc.returncode}): {err}")

    if not output_path.exists():
        raise RuntimeError(
            f"image_generate exited 0 but output file missing: {output_path}\n"
            f"stdout: {stdout.decode('utf-8', errors='replace')[:500]}"
        )

    return {
        "page_n": page["n"],
        "status": "success",
        "path": str(output_path),
        "stdout": stdout.decode("utf-8", errors="replace")[:200],
    }


async def _generate_via_openclaw_alternative(page, prompt, refs, output_path, size_wh, alt_flag):
    """Fallback s alternativním názvem reference flag."""
    width, height = size_wh
    cmd = [
        "image_generate",
        prompt,
        "--size", f"{width}x{height}",
        "--output", str(output_path),
    ]
    for ref in refs:
        cmd.extend([alt_flag, str(ref)])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        err = stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"image_generate failed with {alt_flag}: {err}")

    if not output_path.exists():
        raise RuntimeError(f"image_generate (alt) did not produce {output_path}")

    return {
        "page_n": page["n"],
        "status": "success",
        "path": str(output_path),
        "alt_flag_used": alt_flag,
    }


# ─── Main worker ────────────────────────────────────────────────────
async def generate_one(page, prompts_dir, brand_dir, output_dir, resolution_preset,
                       backend, sem, retry_count=3):
    """Generate one page with retry."""
    async with sem:
        page_n = page["n"]
        layout = page.get("layout", "unknown")
        orientation = page.get("orientation", "widescreen")

        # Resolve resolution
        try:
            size_wh = RESOLUTIONS[resolution_preset][orientation]
        except KeyError:
            print(f"  ✗ Unknown resolution preset/orientation: {resolution_preset}/{orientation}")
            return {"page_n": page_n, "status": "failed", "error": "invalid_resolution"}

        # Load prompt
        prompt_file = prompts_dir / f"page-{page_n:02d}.txt"
        if not prompt_file.exists():
            print(f"  ✗ Page {page_n:02d}: prompt file missing")
            return {"page_n": page_n, "status": "failed", "error": "prompt_missing"}
        prompt = prompt_file.read_text(encoding="utf-8")

        # Get references
        refs = get_references_for_page(page, brand_dir)
        ref_names = [r.name for r in refs]

        output_path = output_dir / f"page-{page_n:02d}.png"
        print(f"  ▸ Page {page_n:02d} ({layout}, {orientation}, {size_wh[0]}×{size_wh[1]})")
        print(f"    refs: {ref_names}")

        # Choose backend
        if backend == "fal":
            generator = generate_via_fal
        elif backend == "openrouter":
            generator = generate_via_openrouter
        elif backend == "openclaw":
            generator = generate_via_openclaw
        else:
            return {"page_n": page_n, "status": "failed", "error": f"unknown_backend:{backend}"}

        for attempt in range(retry_count):
            try:
                result = await generator(page, prompt, refs, output_path, size_wh)

                # Save metadata
                endpoint_map = {
                    "fal": ("openai/gpt-image-2/edit" if refs else "openai/gpt-image-2", "openai/gpt-image-2"),
                    "openrouter": ("openrouter.ai/api/v1/images/generations", "openai/gpt-image-2"),
                    "openclaw": ("openclaw-native", "openclaw-native"),
                }
                endpoint_used, model_used = endpoint_map[backend]
                meta = {
                    "page_n": page_n,
                    "layout": layout,
                    "orientation": orientation,
                    "size": list(size_wh),
                    "backend": backend,
                    "endpoint": endpoint_used,
                    "model": model_used,
                    "references": [str(r) for r in refs],
                    "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16],
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    **{k: v for k, v in result.items() if k not in ("page_n", "status", "path")},
                }
                meta_path = output_dir / f"page-{page_n:02d}.meta.json"
                meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

                print(f"  ✓ Page {page_n:02d} → {output_path.name}")
                return result

            except Exception as e:
                if attempt < retry_count - 1:
                    backoff = 2 ** attempt * 30
                    print(f"  ⚠ Page {page_n:02d} attempt {attempt+1} failed: {e} — retry in {backoff}s")
                    await asyncio.sleep(backoff)
                else:
                    print(f"  ✗ Page {page_n:02d} FAILED after {retry_count} attempts: {e}")
                    return {"page_n": page_n, "status": "failed", "error": str(e)}


async def main():
    parser = argparse.ArgumentParser(description="Generate lead magnet pages via GPT Image 2")
    parser.add_argument("--plan", required=True, help="Path to page-plan.json")
    parser.add_argument("--prompts-dir", required=True, help="Directory with page-XX.txt prompts")
    parser.add_argument("--references-dir", required=True, help="Brand directory (/documents/brand/)")
    parser.add_argument("--output-dir", required=True, help="Output directory for PNG files")
    parser.add_argument("--resolution", choices=["draft", "final", "hi-end"], default="draft",
                        help="Resolution preset")
    parser.add_argument("--backend", choices=["openclaw", "openrouter", "fal"], default="openclaw",
                        help="Generation backend: openclaw (native, default), openrouter (OPENROUTER_API_KEY), fal (FAL_KEY)")
    parser.add_argument("--only", help="Comma-separated page numbers to regenerate")
    parser.add_argument("--concurrent", type=int, default=4, help="Max concurrent requests")
    args = parser.parse_args()

    plan_path = Path(args.plan)
    prompts_dir = Path(args.prompts_dir)
    brand_dir = Path(args.references_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
    pages = plan_data.get("pages", [])
    if not pages:
        print("❌ No pages in plan")
        sys.exit(1)

    # Filter pages if --only
    if args.only:
        only_ns = {int(x.strip()) for x in args.only.split(",")}
        pages = [p for p in pages if p["n"] in only_ns]
        print(f"🔍 Regenerating only pages: {sorted(only_ns)}")

    # Backend pre-check
    if args.backend == "fal" and not os.environ.get("FAL_KEY"):
        print("❌ FAL_KEY environment variable required for --backend fal")
        sys.exit(1)
    if args.backend == "openrouter" and not os.environ.get("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY environment variable required for --backend openrouter")
        sys.exit(1)
    if args.backend == "openclaw":
        # Quick check že image_generate je v PATH
        import shutil
        if not shutil.which("image_generate"):
            print("⚠️  Warning: 'image_generate' tool not found in PATH.")
            print("   Pokud běžíš mimo OpenClaw runtime, použij --backend openrouter nebo --backend fal.")
            print("   Pokračujem ale skript pravděpodobně selže.")

    print(f"🎨 Backend: {args.backend} | Resolution: {args.resolution}")
    print(f"📚 Brand library: {brand_dir}")
    if find_brand_board(brand_dir):
        print(f"   ✓ brand-board found")
    else:
        print(f"   ⚠️  brand-board.png NOT FOUND — quality will suffer")

    brand_kit = brand_dir / "brand-kit"
    if brand_kit.exists() and find_pdf_inspiration(brand_kit):
        print(f"   ✓ 08-inspirace-pro-pdf-materialy found")
    else:
        print(f"   ⚠️  08-inspirace-pro-pdf-materialy.png NOT FOUND — PDF style less specific")

    print(f"🚀 Generating {len(pages)} pages (max {args.concurrent} concurrent)…")

    sem = asyncio.Semaphore(args.concurrent)
    tasks = [
        generate_one(p, prompts_dir, brand_dir, output_dir,
                     args.resolution, args.backend, sem)
        for p in pages
    ]
    results = await asyncio.gather(*tasks)

    success = sum(1 for r in results if r and r.get("status") == "success")
    failed = [r for r in results if r and r.get("status") == "failed"]

    print()
    print(f"✅ Generated: {success}/{len(tasks)}")
    if failed:
        print(f"❌ Failed: {len(failed)}")
        for f in failed:
            print(f"   - Page {f['page_n']}: {f.get('error', 'unknown')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
