# Camera Grammar — anamorphic style, cuts, durations, focal length

Cinematografická slovní zásoba pro storyboard frames a Seedance prompty. Fokus: **anamorphic editorial** look (Pavlovy 3 referenční ukázky), commercial cinematic, hand-held UGC, minimal product.

## Visual style presets

### 1. Anamorphic Editorial (default)

Inspirace: Big Sur road movie, Premium service editorial, Heritage luxury car film.

- **Lens:** Anamorphic 35mm, 1.33× nebo 1.55× squeeze
- **Aspect:** 2.39:1 letterboxed do 16:9 nebo 9:16 frame
- **Grain:** Light 35mm film grain (overlay v post)
- **DOF:** Shallow, smooth bokeh, subtle lens flares
- **Color:** Warm-cool split, low contrast, faded blacks
- **Mood:** Wistful, nostalgic, contemplative, premium

**Prompt phrase:** "anamorphic 35mm film aesthetic, cinematic depth of field, low-contrast nostalgic highlights with gentle halation, vintage Polaroid softness"

### 2. Commercial Cinematic

Inspirace: Apple ads, Nike commercials, brand films.

- **Lens:** Wide-aperture spherical (Cooke S4, Zeiss Master Prime)
- **Aspect:** 16:9 nebo 1.85:1
- **Grain:** Clean, minimal grain
- **DOF:** Mid-shallow, sharp subject + soft background
- **Color:** High dynamic range, clean blacks, accurate skin tones
- **Mood:** Polished, aspirational, energetic, modern

**Prompt phrase:** "commercial anamorphic look, flattering perspective and cinematic depth, polished color grade, clean blacks, accurate skin tones"

### 3. Hand-held UGC / Authentic

Inspirace: TikTok creator content, authentic Reels.

- **Lens:** Phone-like (28mm equiv) nebo handheld 35mm
- **Aspect:** 9:16 výhradně
- **Grain:** None, clean digital
- **DOF:** Mostly deep, slight subject separation
- **Color:** Slightly desaturated, natural light
- **Mood:** Authentic, relatable, intimate, unfussy

**Prompt phrase:** "handheld phone-style framing, natural light, authentic creator aesthetic, slight imperfection, intimate and relatable"

### 4. Minimal Product

Inspirace: Jacquemus product films, minimal still life motion.

- **Lens:** Macro 100mm, normal 50mm, wide 35mm — striktně controlled
- **Aspect:** 1:1 nebo 9:16
- **Grain:** None
- **DOF:** Macro-shallow nebo deep, kontrast control
- **Color:** Monochromatic-ish, single accent
- **Mood:** Minimalist, premium, sterile, design-led

**Prompt phrase:** "minimal product cinematography, controlled lighting, single light source with soft fill, monochromatic palette, premium sterile aesthetic"

## Focal length glossary

| Focal length | Equivalent | Effect | Use case |
|--------------|-----------|--------|----------|
| 14mm | Ultra-wide | Distortion at edges, dramatic perspective | Establishing wide, architecture, vista |
| 24mm | Wide | Moderate distortion, immersive | Wide environment, group, action |
| 35mm | Standard wide | Slight distortion, natural feel | Wide medium, environmental portrait |
| 40mm | Anamorphic standard | Editorial, balanced | Default for wide cinematic |
| 50mm | Normal | Eye-level natural perspective | Medium shots, dialogue, portraits |
| 75mm | Short tele | Slight compression, flattering portraits | Close-up, beauty, product mid |
| 85mm | Portrait tele | Strong compression, beautiful bokeh | Headshots, hero, intimate |
| 100mm macro | Macro | Extreme close, tight DOF | Insert details, jewelry, hands, product |
| 135mm+ | Long tele | Heavy compression, isolation | Sports, wildlife, isolated subject |

## Camera moves

### Static (no movement)

`STATIC` — zafixovaná kamera, žádný pohyb. Pro classic establishing nebo iconic ending.

### Panning (rotace)

- `PAN-LEFT` / `PAN-RIGHT` — horizontální rotace na statickém stativu
- `TILT-UP` / `TILT-DOWN` — vertikální rotace

### Dolly (translace)

- `DOLLY-IN` / `PUSH-IN` — kamera se přibližuje k subjektu, intenzifikace
- `DOLLY-OUT` / `PULL-BACK` — kamera ustupuje, reveal context, isolation
- `TRACK` / `TRACKING` — kamera jede paralelně se subjektem (běh, jízda autem)
- `LATERAL` / `CRAB` — boční pohyb (tracking shot z boku)

### Crane / vertical

- `CRANE-UP` / `BOOM-UP` — kamera stoupá vzhůru, reveal expanse
- `CRANE-DOWN` / `BOOM-DOWN` — kamera sestupuje
- `CRANE-OVER` — kamera překlene přes subjekt, dramatic reveal

### Handheld

- `HANDHELD` — manuální, organická vibrace, intimate / authentic
- `STEADICAM` — stabilizovaná flowing motion, smooth ale dynamická

### Specialized

- `RACK-FOCUS` — focus shift z foreground na background nebo zpět
- `ORBIT` / `ARC` — kamera obíhá kolem subjektu
- `ZOOM-IN` / `ZOOM-OUT` — optická změna ohniska (vs. dolly = fyzický pohyb)
- `WHIP-PAN` — rychlý pan jako přechod mezi cuts
- `POV` — point of view, kamera = oči postavy
- `OTS` — over-the-shoulder

## Shot types (frame composition)

| Shot type | Frame | Use |
|-----------|-------|-----|
| `EXTREME-WIDE` (EWS) | Lidská postava jako bod v krajině | Establishing, scale |
| `WIDE` (WS) | Lidská postava plná | Action, environment, context |
| `MEDIUM-WIDE` (MWS) | Knee-up | Wide medium, walking, two-shot |
| `MEDIUM` (MS) | Waist-up | Standard dialogue, gesture |
| `MEDIUM-CU` (MCU) | Chest-up | Intimate dialogue, expression |
| `CLOSE-UP` (CU) | Head + shoulders | Emotion, beauty |
| `EXTREME-CU` (XCU) | Eyes / mouth / detail | Emotion peak, product detail |
| `INSERT` | Object detail (hands, jewelry) | Tactile, narrative beat |
| `TWO-SHOT` | 2 lidé v rámu | Dialogue, relationship |
| `OTS` | Over-the-shoulder | Conversation, perspective |
| `POV` | First-person view | Immersion |
| `RACK-FOCUS` | Mid-cut focus shift | Reveal, transition within shot |

## Cut duration rules

**Seedance min:** 4 s. Min duration per cut = 4 s (i když pacing chce 2 s).

**Pacing guidelines:**

| Pacing feel | Avg cut duration | Use case |
|-------------|-----------------|----------|
| Frenetic | 4-5 s (Seedance min) | Music video, action, energetic |
| Snappy | 5-7 s | UGC, social ads, quick story |
| Standard | 7-10 s | Most paid social, brand films |
| Contemplative | 10-15 s | Premium, luxury, mood-driven |

**Pravidla pro skill:**
- Default cut duration: **8 s** (Seedance sweet spot)
- Range: 4-15 s
- Pokud user chce 30 s video, skill navrhne **3-4 cuty** (default), ne 6-8 (každý kratší)
- Pokud user chce 60 s video, skill navrhne **4-6 cutů × 10-12 s**

**Editorial trim v post:**
Pokud chceš ostrý 2 s "moment", generuj 4 s a v ffmpeg ostříhej:

```bash
ffmpeg -ss 1.0 -t 2.0 -i cut-N.mp4 -c copy cut-N-trimmed.mp4
```

## Cut sequence templates

### 5-cut Anamorphic Road Movie (Big Sur reference)

```
1. Wide aerial CRANE-UP (3-4s) — establish coastline + winding road
2. Medium TRACK alongside car (4-5s) — character driving, wind in hair
3. Insert HANDHELD (2-3s) — tactile detail (hand, jewelry, fabric)
4. Wide DOLLY-OUT (3-4s) — character has stopped, walks toward overlook
5. Wide STATIC sunset silhouette (3-4s) — resolution, stillness
```

### 6-cut Premium Service (Auto Repair reference)

```
1. Wide STATIC exterior (3s) — establish location, mood
2. Medium TRACK walking inside (2s) — protagonist enters
3. Close-up HANDHELD (2s) — action beat (working, inspecting)
4. Push-in TWO-SHOT (3s) — dialogue / interaction with customer
5. Insert RACK-FOCUS macro (2s) — detail montage (tools, hands)
6. Wide DOLLY-OUT exterior (3s) — completed work, departure
```

### 5-cut Heritage Luxury (Heritage car film reference)

```
1. Wide CRANE-DOWN aerial (4s) — solitary product in landscape
2. Low-angle TRACK (3s) — product accelerates through scene
3. Steadicam EXTREME-CU driving (3s) — character + product detail
4. Insert macro (3s) — tactile / craftsmanship detail
5. Wide DOLLY-OUT magic-hour (3s) — character + product, legacy moment
```

### 4-cut Snappy Social (15s Reel)

```
1. Hook static / handheld (4s) — scroll-stopping problem framing
2. Medium track (4s) — protagonist in action / reaction
3. Insert close-up (4s) — proof point / product detail
4. CTA static / push-in (3s) — clear end frame, brand mark
```

### 3-cut Punchy Product (12s)

```
1. Wide product reveal CRANE-DOWN (4s)
2. Macro detail RACK-FOCUS (4s)
3. Hero static (4s) — final iconic shot
```

## Lighting moods

Per-cut lighting cue v storyboardu (Section 4):

| Mood label | Description | Time of day |
|-----------|-------------|-------------|
| `Coastal aerial haze` | Marine layer, sun-flares, warm coral | Late golden hour |
| `Side-lit portrait` | Golden hour rim light, hair catches wind | Golden hour |
| `Macro skin / jewelry` | Warm specular highlights, intimate | Golden hour, indoor warm |
| `Sunset silhouette` | Strong backlight, contour wrap | Sunset |
| `Bright workshop` | Overhead practical light, soft fill | Daytime indoor |
| `Soft amber rim` | Warm rim on skin, dark background | Evening / dusk |
| `Magic hour blue` | Cool ambient + warm practicals | Civil twilight |
| `Cinema noir` | Low-key, single source, deep shadows | Night |
| `Fluorescent harsh` | Cold overhead, no fill | Office, retail |
| `Sun-wash bright` | Direct sun, hard shadows | Midday |

## Mood keyword library

Per visual style (skill vybírá 3-5 z relevantní kategorie):

**Anamorphic Editorial:** wistful, free, nostalgic, contemplative, salt-air, golden-hour, California-dream, timeless, inherited-luxury, restrained, aristocratic, Mediterranean, melancholy, heritage-performance

**Commercial Cinematic:** trustworthy, polished, confident, approachable, premium, modern, efficient, transparent

**Hand-held UGC:** authentic, real, intimate, relatable, candid, raw, unfussy, conversational

**Minimal Product:** sterile, premium, refined, monochromatic, design-led, controlled, precise, elevated

**Brand-specific (per brandDNA voice):**
Skill načte z `brandDNA.md` → použije brand mood adjektiva (často 5-8 slov v sekci "Hlas a tonalita").

## Per-cut prompt template (Seedance)

Skill v Kroku 4 generuje per-cut Seedance prompt podle této šablony:

```
{shot_type} {focal_length} of {subject_described},
{camera_move}, {action 1-2 sentences}.

Setting: {environment}.
Time of day / lighting: {lighting_mood}.
Mood: {3-5 mood keywords}.

Visual style: {style preset phrase}.
{If anamorphic}: anamorphic 35mm film aesthetic, cinematic depth of field,
low-contrast nostalgic highlights with gentle halation, vintage Polaroid softness.
{If commercial}: commercial cinematic look, polished color grade, accurate skin tones.
{If UGC}: handheld phone-style framing, natural light, authentic creator aesthetic.
{If minimal}: controlled lighting, monochromatic palette, premium sterile aesthetic.

Audio: {ambient SFX cue, e.g. "wind rush, distant waves"}. NO dialog. NO voiceover.
```

**Příklad — Cut 2 z 5-cut Anamorphic Road Movie (Big Sur Track):**

```
Medium 50mm anamorphic of a blonde woman driving a vintage cream convertible,
TRACK movement gliding alongside the car, wind ripples through her hair as engine hum carries forward.

Setting: rugged Big Sur cliff road overlooking the Pacific ocean.
Time of day / lighting: late golden hour, warm coral light bathing cliffs and skin.
Mood: wistful, free, nostalgic, contemplative, salt-air.

Visual style: anamorphic 35mm film aesthetic, cinematic depth of field,
low-contrast nostalgic highlights with gentle halation, vintage Polaroid softness.

Audio: soft convertible engine hum, wind rush, distant waves. NO dialog. NO voiceover.
```
