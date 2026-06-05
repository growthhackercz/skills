# Recipes — quick brief presets per use case

Plně vyplněné `video-brief.json` snippets pro typické scénáře. Zkopíruj relevantní recept, doplň `campaign_slug` + `product` + `character.description` a jdeš.

Hodnoty, které mění recept, jsou v **bold**. Zbytek je společný pro všechny.

---

## 1. Premium wellness / beauty — 15 s 9:16 Reel

**Cílová platforma:** Meta/IG Reels, TikTok, Shorts. Mobile-first, 80 % mute scrollers.

```json
{
  "platform": "ig_reel",
  "aspect_ratio": "9:16",
  "duration_total_s": 15,
  "tier": "standard",
  "shared_choices": {
    "cut_count": 5,
    "style_preset": "anamorphic-editorial",
    "mood_keywords": ["serene", "premium", "intentional", "wellness-ritual", "morning-clarity"],
    "audio_tone": ["soft water sound", "linen rustle", "low warm piano with reverb"],
    "scene_continuity": "All 5 cuts unfold in the SAME morning vanity location."
  },
  "voiceover": {
    "backend": "gemini",
    "language": "cs",
    "voice": "Aoede",
    "temperature": 0.75
  }
}
```

**Voice:** `Aoede` (warm female mid-30s). **Style instructions:** „warm intimate tone, NO pauses, graduation arc soft → conviction → calm landing, NOT a commercial announcer voice."

---

## 2. B2B LinkedIn — 12 s 16:9

**Cílová platforma:** LinkedIn feed, sponsored video. Krátká attention span, 80 % mute, hook v prvních 3 s **bez VO**.

```json
{
  "platform": "linkedin_feed",
  "aspect_ratio": "16:9",
  "duration_total_s": 12,
  "tier": "standard",
  "shared_choices": {
    "cut_count": 5,
    "style_preset": "commercial-cinematic",
    "mood_keywords": ["trustworthy", "polished", "modern", "efficient"],
    "audio_tone": ["minimal electronic", "subtle synth", "clean reverb"]
  },
  "voiceover": {
    "backend": "gemini",
    "language": "cs",
    "voice": "Charon",
    "temperature": 0.6
  }
}
```

**Voice:** `Charon` (deep male, authoritative). **První cut bez VO** — text overlay nebo strong visual hook. **Burned-in titulky** doporučené v post.

---

## 3. Snappy TikTok / Reel — 15 s UGC-style

**Cílová platforma:** TikTok in-feed, IG Reels. Authentic creator aesthetic, ne commercial.

```json
{
  "platform": "tiktok",
  "aspect_ratio": "9:16",
  "duration_total_s": 15,
  "tier": "fast",
  "shared_choices": {
    "cut_count": 5,
    "style_preset": "handheld-ugc",
    "mood_keywords": ["authentic", "intimate", "candid", "raw", "conversational"],
    "audio_tone": ["acoustic guitar", "lo-fi", "room tone"]
  },
  "voiceover": {
    "backend": "gemini",
    "language": "cs",
    "voice": "Algieba",
    "temperature": 0.85
  }
}
```

**Tier `fast`** ($3.63 vs $4.54) — pro UGC test concepts. **Voice:** `Algieba` (warm conversational male) nebo `Sulafat` (younger female). Higher temperature 0.85 pro expressive delivery.

---

## 4. Heritage luxury / brand film — 15 s 16:9

**Cílová platforma:** YouTube pre-roll, web hero, brand film. Slow build, contemplative pacing.

```json
{
  "platform": "youtube_preroll",
  "aspect_ratio": "16:9",
  "duration_total_s": 15,
  "tier": "standard",
  "shared_choices": {
    "cut_count": 5,
    "style_preset": "anamorphic-editorial",
    "mood_keywords": ["timeless", "inherited-luxury", "restrained", "aristocratic", "heritage-performance"],
    "audio_tone": ["solo cello", "vintage strings", "ambient guitar"]
  },
  "voiceover": {
    "backend": "gemini",
    "language": "cs",
    "voice": "Callirrhoe",
    "temperature": 0.65
  }
}
```

**Voice:** `Callirrhoe` (mature female) nebo `Charon` (authoritative male). Lower temperature 0.65 pro composed, restrained delivery.

---

## 5. Minimal product film — 10 s 1:1

**Cílová platforma:** IG feed, Pinterest. Design-led, controlled, premium product story.

```json
{
  "platform": "ig_feed",
  "aspect_ratio": "1:1",
  "duration_total_s": 10,
  "tier": "standard",
  "shared_choices": {
    "cut_count": 5,
    "style_preset": "minimal-product",
    "mood_keywords": ["sterile", "premium", "refined", "monochromatic", "design-led"],
    "audio_tone": ["sparse piano", "single instrument", "breathing reverb"],
    "scene_continuity": "All 5 cuts in the same controlled studio environment with single key light."
  },
  "voiceover": null
}
```

**Bez voiceoveru** — produkt mluví sám. Seedance native music+SFX. **Cut durations:** 2 s × 5 = 10 s (každý cut krátký, snappy product reveal montage).

---

## 6. PMax 3-pack — same brief × 3 aspect ratios

Pro Google Performance Max kampaně potřebuješ 16:9 + 1:1 + 9:16. Workflow:

1. Vytvoř plný brief pro hlavní aspect (např. 16:9 hero)
2. Klonuj brief 2× pro `1:1` a `9:16` — **zachovej vše** kromě `aspect_ratio`
3. Generuj zvlášť — 3× $4.54 = ~$13.60

Hooks a CTA musí fungovat **napříč všemi aspect ratios** (žádné off-frame elementy v 9:16 vs 16:9).

---

## Quick decision tree

```
Co je hlavní cíl?
├── Awareness / brand hero  → anamorphic-editorial 15s
│   ├── Web/YouTube preroll → 16:9 (recipe #4)
│   ├── IG/TikTok           → 9:16 (recipe #1)
│   └── PMax full coverage  → 3-pack (recipe #6)
│
├── B2B / lead gen          → commercial-cinematic 12s 16:9 LinkedIn (recipe #2)
│
├── DR / TikTok ad          → handheld-ugc 15s 9:16 (recipe #3)
│
└── Product showcase / PDP  → minimal-product 10s 1:1 (recipe #5)
```

**Pravidlo:** vždy začni s recipe co matchuje use case, pak ho jen doplň brand-specific údaji. Nechtěj rovnou tweakovat `mood_keywords` / `audio_tone` — defaults jsou ladné.

---

## Související soubory

- `brief-schema.md` — kompletní schema všech polí
- `platform-specs.md` — platform-specific spec sheets (aspect, délka, safe zones, CTA placement)
- `voiceover-rules.md` — voice presets, style_instructions best practices
- `camera-grammar.md` — style presets, focal length, camera moves, cut sequence templates
