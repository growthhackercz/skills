# Master Storyboard Layout Spec

Definuje, jak skill složí 1 master storyboard PNG. Výsledek vypadá jako profesionální pre-production deck — character ref, environment, floor plan, cuts, lighting/mood — všechno na jednom obrázku, vhodné k odeslání klientovi ke schválení.

## Cílový formát

- **Rozměr:** 2400×1600 px (3:2 landscape, A4-ish)
- **DPI:** 200 (~A3 print quality)
- **Background:** ivory paper (`#F8F4EC`) — neutral pre-production board feel
- **Typo:** serif headlines (Crimson, Playfair) + sans body (Inter, Helvetica) — editorial layout pro tisk
- **Layout:** 4 sekce v gridu

## Layout v7 — top 35 % three columns, bottom 65 % uniform 3×2 (or 6×1) grid (POVINNÉ)

Storyboard PNG (2400×1600). Two zones:

- **Top zone** (~560 px, ~35 % plochy): 3 vertikální sloupce 1/2 + 1/4 + 1/4
  - **Column 1** (~1200 px wide): **Section 1** — Character + hero props reference
  - **Column 2** (~600 px wide): **Section 2** — Environment SKETCH (floor plan only, NO photos)
  - **Column 3** (~600 px wide): **Section 3** — Lighting refs + color palette (full column height)
- **Horizontal divider**
- **Bottom zone** (~1020 px, ~65 % plochy): UNIFORM grid s 6 stejně velkými dlaždicemi
  - **Section 4 — STORYBOARD CUTS** v cells 1..N (5 cuts max)
  - **Section 5 — NOTES** (mood / audio / cinematography) v LAST cell (text only, no frame)

**Section numbering:**
1. Character + hero props (top-left, 1/2 width)
2. Environment sketch (top-center, 1/4 width)
3. Lighting + palette (top-right, 1/4 width)
4. Storyboard cuts (bottom grid, hero)
5. Notes (last cell of bottom grid)

**Aspect-adaptive grid (Section 4):**
- **16:9** landscape video → **3×2 grid** (5 cuts + notes cell, total 6). Each cell ~773×490 px, frame 773×434 (16:9).
- **9:16** vertical video → **6×1 strip** (5 vertical 9:16 frames vedle sebe + notes cell). Each cell ~386×980 px.
- **1:1** square → **3×2 grid** with square frames (~490×490 px each).

All cut frames are EXACTLY same size (no mix of large/small).

**No top header bar** — žádné "SHARED CHOICES" summary strip nahoře. Page začíná hned sekcemi.

⚠️ **DŮLEŽITÉ pravidlo: Section 2 = jen sketch, ŽÁDNÉ environment photos.**

Photographic environment thumbnails byly v předchozí verzi v Section 2 — Seedance/GPT je pak interpretovaly jako "potential scene candidates" a míchaly je do generated frames. Sketch (hand-drawn floor plan) je clearer signal: model rozpozná že je to plánek, ne reference photo.

## Reference images posílané do FAL gpt-image-2

Skill posílá až 3 reference (limit FAL `openai/gpt-image-2/edit`). Strategie závisí na `product_visual_identity`:

**A) Product-locked mode** (`product_visual_identity` v briefu):
Všechny 3 sloty = produktové fotky (hero + alt angles). Postava + prostředí jsou popsané jen v promptu. Důvod: model jinak halucinuje produkt v malých thumbnailech.

**B) General mode** (bez `product_visual_identity`):
1. `brand-board.png` — vizuální tonalita, palette, mood
2. Hero produktová fotka (pokud o produktu) NEBO brand portrait
3. `brand-kit/*.png` — atmosférická reference

Logika v `scripts/generate-storyboard.py::collect_reference_images()`.

## Validation po generaci

Po dokončení skill zkontroluje:
- File exists, non-zero size, valid PNG
- Width ≥ 2200, height ≥ 1400 (sanity check)
- Pokud fail → retry 1× s mírně upraveným promptem (přidat "high quality, detailed editorial layout")
- Pokud fail druhý pokus → vrátit blocking error

## Photorealistic faces — anti-AI-look rule (POVINNÉ)

Při single-shot Seedance reference-to-video volání se v promptu MUSÍ vyskytnout explicitní instrukce proti vyhlazenému AI-look:

> Every visible human face must look like a real photographed person: natural skin pores, micro-imperfections, slight asymmetry, individual visible hair strands, realistic catchlights and moisture in the eyes, soft subsurface scattering. Show age-appropriate texture (fine lines for adults, freckles/baby skin for kids). DO NOT render AI-looking smooth-plastic doll-like airbrushed perfect faces; DO NOT smooth out pores or symmetrize features. The character must feel like an actual human captured on a 35mm camera, not generated.

Bez této clause Seedance i Veo i Sora produkují airbrushed plastic faces (viditelná značka AI). S clause faces vypadají jako reálná fotografie člověka.

Stejné pravidlo pro generate-storyboard.py prompt — character ref sheet v Section 1 musí mít stejnou anti-AI-look rule.

## Scene continuity rule (CONDITIONAL — only when brief.scene_continuity is set)

Pokud brief.scene_continuity field je nastavený (multi-line popis fixed scene), skill prompt automaticky vloží continuity rule:
- Všechny cuts ve **stejné** lokaci
- Produkt + architektura + lighting jsou fixed in space
- Camera mění úhly, ale prostor se nemění

Pokud brief.scene_continuity NENÍ nastavený, prompt místo toho vloží **multi-location** notice:
- Cuts MOHOU být v různých lokacích / settings / times of day
- Continuity je NOT enforced
- Each cut = independent vignette

⚠️ Když je ad zasazený do **jediné lokace** (např. ranní rituál v kuchyni), VŽDY přidat scene_continuity do briefu jako field s textem typu:
```json
"scene_continuity": "FIXED SCENE — all cuts happen in [location]. Product is at [position]. Furniture: [layout]. Light direction: [angle]. Camera moves between cuts but the space stays the same."
```

Plus do každého cut.subject_framing přidat fixed-scene prefix:
```
"[FIXED SCENE — Product at left, table right, window back wall.] [original framing description]"
```

Když je ad **multi-location** (např. cuts skáčou outdoor → indoor → outdoor), scene_continuity field NEVYPLŇOVAT.

## Music gradation rule (POVINNÉ pro audio prompts)

Seedance native audio bez explicitní instrukce **utne hudbu uprostřed** (jednoduše skončí video → music abruptly cut). Aby music měla přirozený konec, prompt MUSÍ obsahovat:

> The music score MUST gradate across the full {N}-second arc — start gently in the opening seconds, gradually swell through the middle as the action peaks, and ARRIVE at a natural musical resolution in the final 1–2 seconds (a held note, a final chord, or a soft ritardando). NEVER cut the music abruptly, NEVER fade out mid-phrase, NEVER end on a note that feels unfinished. The audio must feel like a complete piece of music written for this exact runtime, with a deliberate ending.

Bez této clause music feels jako "ripped 15 seconds out of a longer track". S clause feels jako "composed specifically for this 15s ad".

## Style anchor reference

Skill používá 3 ověřené layout reference jako style anchor:
1. **Big Sur Highway 1** — anamorphic road-movie, 5 cuts
2. **Premium Auto Care** — service editorial, 6 cuts s floor plan
3. **Heritage car film** — vintage luxury, 5 cuts, magic-hour

Všechny mají: ivory paper background, sekce dle výše uvedeného layoutu, serif headers + sans body, camera grammar v cut frames (focal length / duration / move / shot type), mood keywords + cinematography notes + audio block.

Pokud user dodá vlastní storyboard reference, skill použije jeho místo defaultů.
