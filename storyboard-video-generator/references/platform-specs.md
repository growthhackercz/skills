# Platform Specs — Meta, IG, LinkedIn, YouTube, TikTok, Google PMax

Mapping platforma → aspect ratio → délka → typ. Skill používá pro auto-detection v Kroku 1 a validaci v Kroku 4.

## Quick reference table

| Platform | Format | Aspect | Duration (recommended) | Seedance maps to |
|----------|--------|--------|------------------------|-------------------|
| Meta | Reel | 9:16 | 15-30 s (max 90 s) | `9:16` |
| Meta | Story video | 9:16 | 15 s | `9:16` |
| Meta | Feed video | 4:5 nebo 1:1 | 15 s (max 240 s) | `1:1` (preferred) nebo `9:16` |
| Meta | In-stream video | 16:9 | 5-15 s | `16:9` |
| Meta | Carousel video card | 1:1 | max 60 s per card | `1:1` |
| Instagram | Reel | 9:16 | 15-30 s (max 90 s) | `9:16` |
| Instagram | Story video | 9:16 | 15 s | `9:16` |
| Instagram | Feed video | 4:5 nebo 1:1 | 15 s (max 60 s) | `1:1` |
| TikTok | In-feed video | 9:16 | 15-30 s (max 60 s) | `9:16` |
| TikTok | Spark Ad | 9:16 | 15-60 s | `9:16` |
| LinkedIn | Feed video | 16:9, 1:1, 9:16 | 6-15 s (max 30 s recommended) | per chosen |
| LinkedIn | Sponsored video | 16:9 | 15-30 s | `16:9` |
| YouTube | Pre-roll skippable | 16:9 | 15-30 s (skippable po 5 s) | `16:9` |
| YouTube | Bumper | 16:9 | 6 s | `16:9` |
| YouTube | Shorts | 9:16 | 15-60 s | `9:16` |
| Google PMax | Asset video | 16:9, 1:1, 9:16 | 6-15 s | per chosen |
| Pinterest | Standard width | 1:1 nebo 9:16 | 6-15 s | `1:1` nebo `9:16` |

## Per-platform detail

### Meta / Facebook + Instagram

**Reels (recommended pro paid, 2026):**
- Aspect: **9:16** (vertikální)
- Resolution: 1080×1920
- Length: 15-30 s sweet spot (testů ukázal 15 s je nejlepší pro CTR, 30 s pro completion rate)
- Audio: subtitles důležité (90% mute scrollers)
- File size: max 4 GB
- Codec: H.264, AAC

**Stories (organic + paid):**
- Aspect: **9:16**
- Resolution: 1080×1920
- Length: max 15 s per story (delší = auto-split)
- Safe zones: top 250 px (reserved username), bottom 350 px (CTA sticker)
- Audio: 50-70% s mute → titulky must

**Feed video:**
- Aspect: **4:5 (recommended)** nebo 1:1
- Resolution: 1080×1350 (4:5) nebo 1080×1080 (1:1)
- Length: 15 s sweet spot, 30-60 s max engagement
- Pravidlo: 4:5 zabere víc screen real estate než 1:1, ale Seedance to nepodporuje → **mapuj na 1:1**

**In-stream:**
- Aspect: **16:9**
- Resolution: 1280×720 (min) až 1920×1080
- Length: 5-15 s (mid-roll), 15+ s (pre-roll)

### TikTok

**In-feed:**
- Aspect: **9:16**
- Resolution: 1080×1920 (recommended), min 540×960
- Length: 15-60 s (15 s = nejvyšší completion rate)
- Audio: trending sounds + originální music funguje (ne náš case → použij brand music)
- Captions: native captions tool nebo burned-in

**Spark Ad:**
- Stejné jako in-feed
- Promote existujícího organic content jako paid

### LinkedIn

**Feed video (recommended pro B2B):**
- Aspect: **16:9 (preferred)**, **1:1**, **9:16** (mobile-first)
- Resolution: 1280×720 minimum
- Length: 6-15 s (B2B attention span je krátký), 30 s max
- Audio: 80% s mute → titulky must
- Tip: **První 3 s** musí mít hook bez VO, jinak scroll

**Sponsored video:**
- Aspect: **16:9**
- Length: 15-30 s
- Tipy: clear value prop v prvních 3 s, brand mark v posledních 2 s

### YouTube

**Pre-roll skippable:**
- Aspect: **16:9**
- Length: 15-30 s (po 5 s skippable)
- Strategie: hook v prvních 5 s předtím než skip
- Resolution: 1920×1080 (1080p) nebo vyšší

**Bumper Ads (non-skippable):**
- Aspect: **16:9**
- Length: **6 s** strict
- 1 cut, 1 message, 1 CTA

**Shorts:**
- Aspect: **9:16**
- Resolution: 1080×1920
- Length: 15-60 s
- Stejné principy jako TikTok / Reels

### Google PMax (Performance Max)

**Asset video:**
- 3 aspect ratios doporučené pro full coverage:
  - **16:9** (YouTube placement)
  - **1:1** (Display Network, Discover)
  - **9:16** (YouTube Shorts, TikTok-like inventory)
- Length: 6-15 s sweet spot
- 1 brand asset → 3 aspect ratios → max coverage

**Doporučení:**
Pro PMax kampaň skill nabídne **3-pack** — generuj stejný brief 3× s různými aspect ratios. Náklady ~3× ($4.54 × 3 = ~$13.60 pro 3× 15 s 720p kit).

### Pinterest

**Standard width:**
- Aspect: **1:1** (recommended) nebo **9:16**
- Resolution: 1080×1080 nebo 1080×1920
- Length: 6-15 s
- Audio: muted by default na Pinterest → titulky must

## Aspect ratio mapping (Seedance constraint)

Seedance 2.0 podporuje **JEN** `9:16`, `1:1`, `16:9`. Mapping:

| Source aspect | Maps to | Reason |
|--------------|---------|--------|
| 9:16 (mobile portrait) | `9:16` | ✓ direct |
| 1:1 (square) | `1:1` | ✓ direct |
| 16:9 (landscape) | `16:9` | ✓ direct |
| 4:5 (Meta feed) | `1:1` (preferred) nebo `9:16` | crop top/bottom v post pokud 1:1, nebo plnit 9:16 a v post crop sides |
| 2:3 (Pinterest tall) | `9:16` | smaller crop than 4:5 |
| 3:4 | `1:1` | crop top/bottom |
| 21:9 (cinematic) | `16:9` | letterbox v post pokud chceš 21:9 |

**Skill workflow:**
1. User řekne platform (např. "Meta feed video")
2. Skill mapne na nejbližší Seedance aspect (4:5 → 1:1)
3. Po finálním compose v ffmpeg crop / letterbox na cílové aspect ratio:
   ```bash
   # Crop 1:1 video na 4:5 (zachová středovou kompozici)
   ffmpeg -i final.mp4 -vf "crop=1080:1350" final-4x5.mp4
   ```

## Platform-specific produkční tipy

### "Mute-first" platforms (Meta, IG, TikTok, LinkedIn, Pinterest)

> 80% uživatelů scrolluje s mute. Musí fungovat **bez zvuku**.

- **Burned-in titulky** (ano, vždy)
- **Visual storytelling** (ne talking head)
- **First 1-2 s = hook bez VO** (text overlay nebo strong visual)
- Brand mark v rohu od začátku (recall i bez sound)

### "Sound-on" platforms (YouTube, Spotify Ads, Twitch)

- VO + music funguje
- Méně potřeba burned-in titulky (YouTube má auto-captions)
- Delší attention span — můžeš si dovolit slow build

### Vertical-first decision tree

```
User chce paid social ad?
├── Ano → 9:16 default (Meta Reels, IG Reels, TikTok, Shorts, Pinterest)
└── Ne → ptá se na platform
    ├── LinkedIn / B2B → 16:9 default
    ├── YouTube pre-roll → 16:9
    ├── Web hero / landing → 16:9
    └── Pinterest org → 1:1 nebo 9:16
```

## CTA placement v frame

Per aspect, kde má být CTA / brand mark:

### 9:16 (vertical)

```
┌────────────┐
│            │  ← top 15% safe zone (UI)
│            │
│            │
│  CONTENT   │
│            │
│            │
│            │
│  [LOGO]    │  ← brand mark bottom-left or bottom-right
│  [CTA]     │  ← CTA bottom-center, last 1-2s
│            │  ← bottom 15% safe zone (UI)
└────────────┘
```

### 1:1 (square)

```
┌──────────────┐
│              │
│   CONTENT    │
│              │
│   [LOGO]     │
│   [CTA]      │
└──────────────┘
```

### 16:9 (landscape)

```
┌──────────────────────────┐
│                          │
│       CONTENT       LOGO │
│                          │
│                    CTA   │
└──────────────────────────┘
```

## Skill auto-detection (Krok 1)

Skill z user briefu odhadne:

```python
def detect_platform_aspect(brief_text):
    text = brief_text.lower()
    if any(k in text for k in ["reel", "story", "tiktok", "shorts", "vertical", "9:16"]):
        return "9:16"
    if any(k in text for k in ["linkedin", "youtube", "16:9", "horizontal", "landscape"]):
        return "16:9"
    if any(k in text for k in ["feed", "1:1", "square", "instagram feed", "pinterest"]):
        return "1:1"
    return "9:16"  # default mobile-first
```

## Recommended length per platform (default skill)

```python
DEFAULT_LENGTHS = {
    "meta_reel": 15,         # 15s sweet spot
    "meta_story": 15,
    "meta_feed": 15,
    "meta_carousel": 10,
    "ig_reel": 15,
    "ig_story": 15,
    "tiktok": 15,
    "linkedin_feed": 12,     # B2B attention
    "linkedin_sponsored": 15,
    "youtube_preroll": 15,
    "youtube_bumper": 6,     # exact
    "youtube_shorts": 15,
    "pmax_asset": 10,
    "pinterest": 8,
}
```

User může override v briefu (`"duration": "30"`).
