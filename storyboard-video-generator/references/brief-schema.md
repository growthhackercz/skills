# Brief Schema — `video-brief.json`

JSON schema pro brief, který skill produkuje v Kroku 1 a používá ve všech dalších krocích.

## Plný příklad

```json
{
  "campaign_slug": "bioptron-medall-anti-aging",
  "version": "1.0",
  "created_at": "2026-05-06T11:20:00Z",

  "goal": "Premium anti-aging video pro Bioptron Medall — žena 40-55 vidí device jako tichou denní investici do své pleti.",
  "platform": "youtube_preroll",
  "aspect_ratio": "16:9",
  "duration_total_s": 15,
  "tier": "standard",

  "brand": {
    "name": "Bioptron / Zepter",
    "voice_summary": "Premium Swiss medical wellness — klidný, sebevědomý, vědecký.",
    "color_palette": ["#F5F1EA", "#D4C7B8", "#8B6F47", "#2C2418"],
    "primary_font": "Crimson Text",
    "logo_path": null,
    "brand_board": null,
    "brand_kit": null
  },

  "product": {
    "slug": "bioptron-medall",
    "name": "Bioptron Medall",
    "main_promise": "Polarizované polychromatické světlo zlepší kvalitu pleti.",
    "main_pain": "Stárnutí pleti, jemné vrásky, ztráta jasu.",
    "hero_image": "/documents/ads/video/bioptron-medall-anti-aging/images/HERO.jpg",
    "additional_images": [
      "/documents/ads/video/bioptron-medall-anti-aging/images/ALT-ANGLE.jpg"
    ]
  },

  "product_visual_identity": "STRICT PRODUCT IDENTITY — Bioptron MedAll: pistol-grip handheld biolamp with glossy white shell + dark charcoal grey grip + circular yellow emitter lens (Ø 5cm). BIOPTRON wordmark + Swiss cross + yellow MedAll badge visible. ABSOLUTELY DO NOT depict as flat pad, razor, phone, tablet, hairdryer barrel — it is COMPACT and STOUT, not elongated.",

  "shared_choices": {
    "cut_count": 5,
    "color_palette_label": "warm cream + sun-faded ivory + caramel beige",
    "environment_fingerprint": "Quiet morning vanity area; linen curtains diffusing cool morning light; minimal Scandinavian-meets-Italian aesthetic.",
    "style_preset": "anamorphic-editorial",
    "mood_keywords": ["serene", "premium", "intentional", "wellness-ritual", "morning-clarity"],
    "audio_tone": ["soft water sound", "linen rustle", "distant city hum", "low warm piano with reverb"],
    "scene_continuity": "All 5 cuts unfold in the SAME morning vanity location — marble vanity, linen curtains, ceramic mug, white orchid, device resting horizontally on tray. Camera moves through the SAME space; props remain fixed."
  },

  "character": {
    "description": "Czech woman in her late 40s to early 50s, naturally aged with grace, soft blonde-grey hair loosely pulled back, no heavy makeup, luminous skin, calm composed presence.",
    "wardrobe": "Cream silk slip top or natural linen robe, no jewelry except small gold studs",
    "hero_props": ["Bioptron MedAll device", "ceramic mug with herbal tea", "open hardcover book", "single white orchid"]
  },

  "cuts": [
    {
      "id": "cut-01",
      "duration": 3,
      "shot_type": "WIDE",
      "focal_length": "35mm anamorphic",
      "camera_move": "DOLLY-IN",
      "lighting_mood": "Soft cool morning light through linen curtains, low contrast",
      "subject_framing": "Wide establishing of woman seated calmly at vanity, device on marble tray. Subtle dolly-in.",
      "depth_description": "Foreground: marble vanity with device, mug, orchid sharp / Midground: woman in soft focus / Background: blurred",
      "environment_description": "Elegant Czech apartment morning vanity area",
      "video_prompt": "Wide 35mm anamorphic establishing shot... NO dialog."
    }
    // ... cuts 2-5
  ],

  "audio": {
    "preset": "ambient-music",
    "music_track": null,
    "music_volume": -18,
    "subtitles": "none",
    "end_card": false
  },

  "voiceover": {
    "backend": "gemini",
    "language": "cs",
    "voice": "Aoede",
    "style_instructions": "Speak in Czech with warm intimate tone... PRONUNCIATION RULES: 'Bioptron' is pronounced as Czech 'BI-OP-TRON'. 'MedÓl' is pronounced as Czech 'MED-ÓL' (long Ó as in 'móda'). GRADUATION ARC: ... Female voice mid-40s, mature, calm.",
    "temperature": 0.75,
    "script": "Stárnutí se nezastaví. Ale zpomalí. Deset minut světla denně. Bioptron MedÓl. Pleť, která zůstává sama sebou."
  },

  "options": {
    "concurrent_seedance_requests": 1,
    "image_backend": "fal_gpt_image_2",
    "video_backend": "fal_seedance_v2_reference_to_video"
  }
}
```

## Schema reference

### Top-level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `campaign_slug` | string (kebab-case) | yes | Folder name pod `/documents/ads/video/` |
| `version` | string | yes | Schema version (currently "1.0") |
| `created_at` | ISO8601 | yes | Generation timestamp |
| `goal` | string | yes | Co má video docílit (lidsky) |
| `platform` | enum | yes | viz `references/platform-specs.md` |
| `aspect_ratio` | "9:16" \| "1:1" \| "16:9" | yes | Seedance-supported only |
| `duration_total_s` | int | yes | Default 15 (5 cuts × 3 s) |
| `tier` | "standard" \| "fast" | yes | Seedance tier |

### `brand`

```json
{
  "name": "string",
  "voice_summary": "string (1-2 sentences)",
  "color_palette": ["#hex", "#hex", ...],
  "primary_font": "string",
  "logo_path": "/path/to/logo.png or null",
  "brand_board": "/path/to/brand-board.png or null",
  "brand_kit": "/path/to/brand-kit/.../*.png or null"
}
```

### `product` (volitelné — jen pokud je o produktu)

```json
{
  "slug": "kebab-case",
  "name": "string",
  "main_promise": "string",
  "main_pain": "string",
  "hero_image": "/path/to/hero.jpg (POVINNÉ pro reference-to-video)",
  "additional_images": ["/path/to/photo2.jpg", "/path/to/photo3.jpg"]
}
```

⚠️ **`hero_image` je povinné** — Seedance reference-to-video potřebuje produktovou fotku jako `@Image2`. Bez ní se musí přejít na storyboard-only mode (nižší product fidelity).

### `product_visual_identity` (POVINNÉ když je o specifickém produktu) ⭐

Top-level field. Explicitní popis tvaru, barvy, materiálu, brandingu produktu. Skill ho injektuje do **storyboard promptu** jako "HIGHEST PRIORITY CONSTRAINT" + používá pro narrative grounding.

**Proč:** GPT Image 2 a další modely **halucinuují generické tvary**, když produkt není dominantně v rámu nebo když reference image je menšina kompozice. Master storyboard je nejhorší případ — produkt se objeví v 5 malých thumbnailech a model si ho zjednoduší. Bez explicitního popisu se v 60% případů jeden frame neshoduje s realitou.

```json
{
  "product_visual_identity": "STRICT PRODUCT IDENTITY — [Product Name]: [shape], [color/material], [distinctive features], [branding visible]. Shape resembles [analog]. ABSOLUTELY DO NOT depict the device as: [list of common AI hallucinations]. Match the reference photo PRECISELY."
}
```

**Bez tohoto pole** skill bude varovat: *„⚠️ Brief má product.hero_image ale chybí product_visual_identity — produkt se může v storyboard frames halucinovat."*

### `shared_choices`

```json
{
  "cut_count": int,                       // DEFAULT 5 (3×2 grid + Notes v 6. buňce)
  "color_palette_label": "string",        // pro storyboard header
  "environment_fingerprint": "string",    // 1 věta
  "style_preset": "anamorphic-editorial" | "commercial-cinematic" | "handheld-ugc" | "minimal-product",
  "mood_keywords": ["string", ...],       // 4-8 words
  "audio_tone": ["string", ...],          // 3-5 SFX/music cues
  "scene_continuity": "string"            // OPTIONAL — only when all cuts share location
}
```

#### `cut_count`

**Default 5.** Změna na jiný počet rozbije storyboard layout (3×2 grid pro 16:9/1:1 nebo 6×1 strip pro 9:16 — oba mají 6 buněk = 5 cuts + Notes). Pro `cut_count != 5` se layout adaptuje, ale efektivita drops.

#### `scene_continuity` (volitelné)

Použij **jen když všechny cuts sdílí stejnou lokaci**. Detail co zůstává konstantní (props v fixed positions, room layout, lighting direction). Bez toho model může mezi cuts „přelézt" do jiné místnosti.

Bioptron příklad:
> „All 5 cuts unfold in the SAME morning vanity location — marble vanity, linen curtains, ceramic mug, white orchid, device resting horizontally on tray. Camera moves through the SAME space; props remain fixed."

Pro multi-location ad (např. office → street → home) nech `scene_continuity` neuvedeno — model dostane volnost.

### `character`

```json
{
  "description": "string (1-2 sentences)",
  "wardrobe": "string",
  "hero_props": ["string", ...]
}
```

⚠️ **`character.description` je powerful** — skill ho **dynamicky** vsadí do Seedance promptu jako definici archetype (přes `FICTIONAL CHARACTERS` clause). Buď konkrétní:

```
✓ "Czech woman in her late 40s to early 50s, naturally aged with grace, soft blonde-grey hair loosely pulled back, no heavy makeup, luminous skin, calm composed presence."

✗ "A woman" (model si vyrobí random model — žádná continuity)
```

### `cuts` (array, length = cut_count)

```json
[
  {
    "id": "cut-NN",                          // zero-padded
    "duration": int (3-15),                  // Seedance min 4 pro single image-to-video, 3 OK pro multi-shot
    "shot_type": "WIDE" | "MEDIUM" | "CLOSE-UP" | "MACRO" | "INSERT",
    "focal_length": "35mm anamorphic" | "50mm" | "85mm" | "100mm macro" | ...,
    "camera_move": "STATIC" | "DOLLY-IN" | "DOLLY-OUT" | "STEADICAM" | "PUSH-IN" | "TRACK" | "PAN" | "TILT" | "CRANE-UP",
    "lighting_mood": "string (1 sentence)",
    "subject_framing": "string (kde je subjekt + akce + product orientation)",
    "depth_description": "string (foreground / mid / background)",
    "environment_description": "string",
    "video_prompt": "string (full Seedance prompt — orientovaný popis cutu)",
    "cz_text": "string (optional, legacy SRT field)"
  }
]
```

⚠️ Pro 15 s ad **default = 5 cuts × 3 s každý.**

### `audio` (legacy)

```json
{
  "preset": "ambient-music",
  "music_track": null,
  "music_volume": -18,
  "subtitles": "none",
  "end_card": false
}
```

V aktuálním pipelinu má `audio.preset` jen jeden efekt: `"silent"` → `generate_audio: False` v Seedance volání. Vše ostatní → `generate_audio: True` (default).

### `voiceover` ⭐ NEW

```json
{
  "backend": "gemini" | "elevenlabs",
  "language": "cs" | "en" | "de" | ...,
  "voice": "Aoede" | "Callirrhoe" | "Sulafat" | "Charon" | ...,
  "style_instructions": "string (long, detailed)",
  "temperature": 0.5 - 0.9,
  "script": "string (plný text k namluvení)"
}
```

Pokud `voiceover` je v briefu, krok 2c vygeneruje `voiceover.mp3` přes Gemini TTS. Krok 3b ho automaticky detekuje a ffmpeg-mixne na top Seedance audio.

Pokud `voiceover` chybí, krok 2c se přeskočí, krok 3b vyrobí video bez VO (pure Seedance music+SFX).

Detail v `voiceover-rules.md`.

### `options` (technical)

```json
{
  "concurrent_seedance_requests": 1,
  "image_backend": "fal_gpt_image_2",
  "video_backend": "fal_seedance_v2_reference_to_video"
}
```

## Validation rules

```python
def validate_brief(brief):
    errors = []

    # 1. Aspect ratio Seedance-supported?
    if brief["aspect_ratio"] not in ("9:16", "1:1", "16:9"):
        errors.append(f"aspect_ratio {brief['aspect_ratio']} not supported by Seedance")

    # 2. Cut count default 5
    if brief["shared_choices"]["cut_count"] != 5:
        errors.append(f"⚠️ cut_count {brief['shared_choices']['cut_count']} != 5 (default) — storyboard 3×2 grid won't fit cleanly")

    # 3. Cut durations sum to total?
    cut_total = sum(c["duration"] for c in brief["cuts"])
    if abs(cut_total - brief["duration_total_s"]) > 1:
        errors.append(f"cut durations sum to {cut_total}s but duration_total_s is {brief['duration_total_s']}s")

    # 4. Each cut min 3s, max 15s
    for cut in brief["cuts"]:
        if cut["duration"] < 3:
            errors.append(f"{cut['id']} duration {cut['duration']}s < min 3s")
        if cut["duration"] > 15:
            errors.append(f"{cut['id']} duration {cut['duration']}s > Seedance max 15s")

    # 5. Total duration <= 15s for single Seedance call
    if brief["duration_total_s"] > 15:
        errors.append(f"duration_total_s {brief['duration_total_s']}s > Seedance single-call max 15s — needs ffmpeg concat workflow (not in default skill)")

    # 6. Product reference image exists?
    if brief.get("product"):
        hero = brief["product"].get("hero_image")
        if not hero or not Path(hero).exists():
            errors.append(f"product.hero_image missing or doesn't exist — Seedance reference-to-video will run with storyboard-only refs (lower product fidelity)")

    # 7. product_visual_identity present?
    if brief.get("product") and not brief.get("product_visual_identity"):
        errors.append(f"⚠️ product but no product_visual_identity — high risk of product hallucination in storyboard frames")

    # 8. Voiceover script empty?
    vo = brief.get("voiceover")
    if vo and not vo.get("script"):
        errors.append(f"voiceover block present but script is empty — TTS won't generate")

    # 9. Character description present?
    if not brief.get("character", {}).get("description"):
        errors.append(f"⚠️ character.description missing — Seedance prompt will use fallback 'protagonist described in shots' (less specific archetype)")

    return errors
```

## Schema versioning

Pokud schema rozšíříš (přidáš pole), zvyš `version`:
- 1.0 → 1.1 (backward compat, jen přidání)
- 1.0 → 2.0 (breaking change)

Skill umí číst všechny minor verze v aktuální major.

Aktuální version: **1.0**

## Související soubory

- `voiceover-rules.md` — `voiceover` block detaily (Gemini TTS, voice, style_instructions, phonetic respell)
- `seedance-models.md` — Seedance endpoint params, `image_urls` array, FAL CDN upload
- `audio-rules.md` — vrstvení Seedance native music+SFX + post-mix VO
- `storyboard-layout-spec.md` — co `cut_count: 5` znamená pro layout
- `templates/video-brief.template.json` — template k zkopírování
