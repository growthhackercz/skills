---
name: storyboard-video-generator
version: "1.1"
publishedAt: "2026-05-10"
description: Vyrobí krátké reklamní video (4–15 s) pro Reels, TikTok, Shorts, YouTube i LinkedIn — krok po kroku přes storyboard, český voiceover a hotové MP4. Po každém kroku schvaluješ, takže se neutratí peníze za špatné video.
category: creative
status: ready
metadata: {"openclaw":{"requires":{"bins":["python3","ffmpeg","ffprobe"],"env":["FAL_KEY"]},"primaryEnv":"FAL_KEY","emoji":"🎬"}}
---

# Storyboard Video Generator

Vyrobí ti krátké reklamní video (4–15 s) na míru tvé značce a produktu — od nápadu přes obrázkový storyboard a český voiceover až po hotové MP4 připravené nahrát do Meta Ads Manageru, TikToku, YouTube nebo LinkedInu.

**Jak to funguje (5 kroků s mezi-schválením):**

1. **Brief** — zeptám se na pár věcí (formát, délku, tonalitu, scénář, cíl) a načtu si tvůj brand + produkt
2. **Storyboard** — vyrobím obrázkový plán videa (postava, prostředí, 5 záběrů, světlo, paleta) → **ty schvaluješ**
3. **Návrh voiceoveru** — nabídnu 5 variant scénáře v různých tónech, ty si vybereš
4. **Voiceover** — vyrobím český VO teplým hlasem → **ty posloucháš a schvaluješ**
5. **Finální video** — vyrenderuju 15s reklamu s hudbou, mixnu do ní voiceover s plynulým fade-outem

Mezi-schválení po Krocích 2 a 4 znamenají, že **utrácíš až za video, které víš, že chceš**. Každý krok jde rychle vrátit a předělat.

## ⚠️ NEJDŮLEŽITĚJŠÍ PRAVIDLO — REUSE vs FRESH

**Default = FRESH** (kompletně nová generace včetně nového storyboardu).

| Co user řekne | Co znamená | Co dělej |
|---|---|---|
| *„udělej nové video pro X"* | **FRESH** | Plný 5-krokový pipeline od Kroku 1 (brief) |
| *„nové video"* / *„vyrob video"* / *„udělej reklamu"* | **FRESH** | Plný pipeline od Kroku 1 |
| *„uprav video"* / *„oprav storyboard"* / *„změň VO"* | **FIX existing** | Skip Kroku 2 (storyboard) pokud sedí, pokračuj na to co user mění |
| *„remix"* / *„znovu vyrenderuj"* / *„regen video"* | **REUSE existing** | Použij existující storyboard + brief, jen Krok 5 (Seedance) znovu |
| *„MIX_ONLY"* / *„změň jen ducking"* / *„jiný fade-out"* | **REUSE + ffmpeg only** | Použij `*-seedance.mp4` backup + nový ffmpeg mix |

**Když je nejasné:** ZEPTEJ SE před spuštěním Kroku 5 (= drahé Seedance volání).

**Default při slově „nové" je VŽDY fresh.** I když existuje předchozí storyboard pro stejný produkt — pokud user neřekl „uprav" nebo „remix", smaž / ignoruj předchozí výstupy a začni od Kroku 1.

## ⚠️ KRITICKÉ — Jak skill volat

**VŽDY volej skillní Python scripty. NIKDY nepiš vlastní inline scripty.**

```bash
# Validace briefu před produkční generací
python3 {baseDir}/scripts/validate-brief.py --input <brief.json>

# Krok 2 — master storyboard (FAL gpt-image-2)
python3 {baseDir}/scripts/generate-storyboard.py \
  --brief <brief.json> --output <slug>/01-master-storyboard.png --backend fal

# Krok 4 — voiceover (Gemini 3.1 Flash TTS)
python3 {baseDir}/scripts/generate-voiceover.py \
  --brief <brief.json> --output <slug>/voiceover.mp3

# Krok 5 — finální video (Seedance + ffmpeg)
python3 {baseDir}/scripts/generate-video-singleshot.py \
  --brief <brief.json> --output <slug>/final-singleshot.mp4 \
  --voiceover <slug>/voiceover.mp3 --resolution 720p --tier standard
```

**Před každým Krokem 5 volej napřed `--dry-run`** aby user viděl prompt + uploaded refs:

```bash
python3 {baseDir}/scripts/generate-video-singleshot.py \
  --brief <brief.json> --output <slug>/final-singleshot.mp4 \
  --voiceover <slug>/voiceover.mp3 --dry-run
```

Vlastní inline Python skripty (= napsat vlastní `generate_video.py` v output složce) **se nepíší** — obchází to:
- ✗ PRODUCT single-instance clause
- ✗ CHARACTER COUNT anti-duplication clause
- ✗ Content policy auto-fallback
- ✗ Parallel reference upload
- ✗ MIX_ONLY mode pro free iterace post-mixu
- ✗ CLI flagy pro tweak mix params (`--vo-volume`, `--ducking-ratio`, atd.)
- ✗ Dry-run validaci

## Co skill udělá za tebe

- Načte brand + produkt kontext + ad-plan / brief
- Navrhne kompletní **master storyboard** (character ref, environment, floor plan top-down, 5 cut frames, lighting/mood) — všechno v 1 PNG, jako profesionální pre-production deck
- Po schválení storyboardu vygeneruje **český voiceover** přes Gemini 3.1 Flash TTS (warm, emotive, s graduation arc + phonetic respelling pro brand names)
- Po schválení voiceoveru vygeneruje **finální video** přes Seedance 2.0 reference-to-video — jediné FAL volání s @Image1=storyboard + @Image2/3=produktové fotky, generuje native ambient SFX + instrumentální hudbu
- Post-process v ffmpeg: VO přes hudbu se sidechain duckingem, audio + video fade-out na konci

**Čeština a voiceover:** Gemini 3.1 Flash TTS dělá teplý, emotivní český voiceover s podporou inline emotion tagů ([short pause], [whispering], [sigh]) a 70+ jazyků. Lepší než ElevenLabs pro nemonotónní podání. VO se nepředává Seedance jako audio_urls (Seedance to ignoruje); místo toho se mixuje v ffmpeg post-procesu na top Seedance native music+SFX.

## Kdy použít

- Krátké reklamní videa pro Meta/IG Reels, Stories, TikTok, LinkedIn, YouTube Shorts/Pre-roll, Google PMax
- Brand film / hero asset (15 s)
- Demo / case study video s vizuální narativou (bez talking head)
- Produkt animation z hotového hero shotu

**Nepoužívat pro:**
- Talking head / podcast video (Seedance to umí, ale není to silná stránka — lip sync není perfektní)
- Dlouhé tutorialy / webináře (>15 s — Seedance limit pro single call)

## Co potřebuješ připravené

### Povinné

1. **Brand DNA** — `/documents/brand/brandDNA.md`
2. **Product DNA** (pokud je o produktu) — `/documents/brand/products/[slug]/productDNA.md`
3. **FAL_KEY** v env, `~/.openclaw/.env`, nebo Control Center secret store (pro Seedance video + Gemini TTS + gpt-image-2 storyboard)
4. **`ffmpeg` + `ffprobe`** v PATH (pro audio mix, fade-out, duration probe)
5. **Python 3.8+** s `fal-client`, `requests` a `Pillow` v provider image

### Volitelné

6. **Brand library** — `/documents/brand/brand-board.png`, `/documents/brand/brand-kit/` — visual reference
7. **Hero produktové fotky** — `/documents/brand/products/[slug]/images/` — POVINNÉ pro reference-to-video lock produktu
8. **Brand music track** — pokud chceš vlastní hudbu (jinak Seedance generuje native)

## 5-krokový workflow

```
┌─────────────────┐
│ Krok 1: Brief   │  načti kontext + 5 otázek + napiš video-brief.json
│ (interaktivní)  │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Krok 2: Master  │  generate-storyboard.py → 1 PNG kompozit
│ storyboard      │  (5 cuts v 3×2 gridu pro 16:9/1:1, 6×1 pro 9:16)
└────────┬────────┘
         ▼
   👤 USER schvaluje storyboard. Pokud ne → upravit brief, regen Krok 2.
         ▼
┌─────────────────┐
│ Krok 3: Návrh   │  5 variant scénáře + výběr hlasu (M/F)
│ VO scénáře      │  user vybere variantu nebo dá vlastní
└────────┬────────┘
         ▼
┌─────────────────┐
│ Krok 4:         │  generate-voiceover.py → voiceover.mp3
│ Voiceover       │  Gemini 3.1 Flash TTS s graduation arc + phonetic respell
└────────┬────────┘
         ▼
   👤 USER schvaluje voiceover. Pokud ne → upravit script/style, regen Krok 4.
         ▼
┌─────────────────┐
│ Krok 5: Finální │  generate-video-singleshot.py → final-singleshot.mp4
│ video + post-mix│  Seedance + ffmpeg sidechain VO ducking + fade-out
└─────────────────┘
         ▼
    📦 Finální MP4 (15 s, 720p)
```

### Krok 1: Načtení kontextu + brief (interaktivní)

**Skill nesmí pokračovat na Krok 2, dokud user nepotvrdí ZÁKLADNÍ parametry.**

Skill načte:

| Soubor | Cesta | Co z něj získá |
|--------|-------|---------------|
| Brand DNA | `/documents/brand/brandDNA.md` | hlas, vizuální tonalita, USP |
| Product DNA | `/documents/brand/products/[slug]/productDNA.md` | hlavní bolest, slib, vizuální identita produktu |
| Brand library | `/documents/brand/brand-board.png` + `brand-kit/` | vizuální reference (mood, paleta, typo) |
| Hero produktové fotky | `/documents/brand/products/[slug]/images/` | reference pro Seedance product fidelity (@Image2/3) |

Pokud něco chybí, zeptej se přirozeně.

**Povinné otázky před Krokem 2:**

1. **Poměr stran / platforma:** *„V jakém poměru stran a pro jakou platformu? (1) 9:16 — Meta Reels, IG Stories, TikTok, Shorts (2) 1:1 — Meta/IG feed (3) 16:9 — YouTube pre-roll, LinkedIn, web hero"*
2. **Délka:** *„Jak dlouhé video? Default 15 s = 5 cuts × 3 s. Min 4 s, max 15 s pro Seedance single call."*
3. **Voiceover scénář:** *„Pošli český VO scénář (1-4 věty pro 15 s ad). Případně mám navrhnout 5 variant?"*
4. **Cíl / akce:** *„Co má video diváka donutit udělat? (klik na link, zapamatovat značku, demo, koupit)"*
5. **Tonalita:** *„Aspirační / autentický UGC / vtipný / luxusní / minimalistický / direct-response?"*

**Volitelné:**

6. *„Hlavní hrdina(é)? Konkrétní persona (žena 40s, rodina, profesionál)? Produkt sólo?"*
7. *„Hudba — preferuješ konkrétní žánr? (Seedance generuje native, default sedí brand mood)"*
8. *„Rozpočet test vs prod — 480p test (~$1.50) nebo rovnou 720p produkce (~$4.50)?"*

Z odpovědí + brand/product kontextu skill **sám odhadne**:
- Cut count (default 5 — vyplní 3×2 grid + Notes v 6. buňce)
- Style preset (anamorphic-editorial / commercial-cinematic / handheld-ugc / minimal-product)
- Camera grammar — viz `{baseDir}/references/camera-grammar.md`
- Color palette (z brand library nebo z user override)
- Scene continuity (povinný popis pokud cuts sdílí lokaci)

**Output Kroku 1:** `video-brief.json` — viz `{baseDir}/references/brief-schema.md`. Před Krokem 2 spusť `validate-brief.py` ať odchytíš schema chyby.

### Krok 2: Master storyboard

**Klíčový krok — žádné drahé video, dokud user neschválí storyboard.**

Skill spustí:

```bash
python3 {baseDir}/scripts/generate-storyboard.py \
  --brief /documents/ads/video/[slug]/video-brief.json \
  --output /documents/ads/video/[slug]/01-master-storyboard.png \
  --backend fal
```

Backend = FAL `openai/gpt-image-2/edit` (jediný stable endpoint pro tento layout, podporuje multi-image refs).

**Output:** 1 master storyboard PNG (~2400×1600 px, A4 landscape) — kompozit jako profi pre-prod deck. Layout přesně podle `{baseDir}/references/storyboard-layout-spec.md`.

**Aspect-adaptive grid (žádný SHARED CHOICES header):**

| Aspect briefu | Storyboard layout | Cuts + Notes |
|---------------|-------------------|--------------|
| 16:9 / 1:1 | TOP: 3 sekce (Character / Floor Plan sketch / Lighting+Palette) + BOTTOM: 5 cuts + Notes v 3×2 gridu | 5+1 = 6 cells |
| 9:16 | TOP: 3 vertical sections (zúžené) + BOTTOM: 6×1 vertical strip | 5 cuts + Notes |

**5 sekcí master storyboardu (žádný horní header):**

```
┌──────────────────────┬─────────────────────┬──────────────────────────┐
│ 1. CHARACTER + HERO  │ 2. ENVIRONMENT /    │ 3. LIGHTING REFERENCES   │
│    PROPS REFERENCE   │    FLOOR PLAN       │    + COLOR PALETTE       │
│ • front/side/back    │    (SKETCH)         │ • 4 lighting/mood refs   │
│ • facial close-up    │ • top-down floor    │ • 5 palette swatches     │
│ • relaxed pose       │   plan with cuts    │   (hex codes)            │
│ • hero props row     │   numbered          │                          │
├──────────┬───────────┴──────────┬──────────┴───────┬──────────────────┤
│  Cut 1   │  Cut 2               │  Cut 3                              │
│ 35mm 3s  │ 50mm 3s STATIC       │ 85mm 3s STEADICAM                   │
│ DOLLY-IN │ MEDIUM                │ CLOSE-UP                            │
├──────────┴──────────────────────┼─────────────────────────────────────┤
│  Cut 4 (MACRO)                  │ 5. NOTES / AUDIO CUES /             │
│ 100mm 3s SLOW PUSH-IN           │    CINEMATOGRAPHY                   │
│                                 │ • mood keywords                     │
├─────────────────────────────────┤ • audio cues                        │
│  Cut 5                          │ • cinematography notes              │
│ 50mm 3s DOLLY-OUT MEDIUM        │                                     │
└─────────────────────────────────┴─────────────────────────────────────┘

(pro 9:16 stejné sekce ale 5+1 v 6×1 vertical strip)
```

**Reference images posílané do storyboard generation:**
1. Hero produktová fotka (povinné, lock product anatomy)
2. Alternate angle produktu (volitelné)
3. Brand mood reference (volitelné)

**Output Kroku 2:**
```
/documents/ads/video/[campaign-slug]/
├── 01-master-storyboard.png    ← schvalovaný visual
└── video-brief.json
```

**STOP. Polož otázku:**

> *„Master storyboard je hotový. Sedí tonalita, postava, prostředí a pacing? Pokud ano, pokračujeme na voiceover. Pokud ne, řekni co změnit a vygeneruju nový."*

Detail layoutu v `{baseDir}/references/storyboard-layout-spec.md`.

### Krok 3: Návrh VO scénáře (interaktivní)

Po schválení storyboardu **napřed se zeptej na 2 věci:**

1. **Pohlaví hlasu:** *„Mužský nebo ženský hlas?"*
2. **Text scénáře:** *„Mám navrhnout 5 variant scénáře (~10-13 s) podle různých úhlů (minimalistický refrain / smyslová poetika / autorita značky / osobní rituál / slib výsledku)? Nebo dáš vlastní text?"*

Skill vygeneruje 5 variant podle různých storytelling úhlů a user si vybere jednu (nebo upraví). Pak teprve TTS volání.

**Voice presets:**

| Pohlaví | Default | Alternativy |
|---------|---------|-------------|
| Žena | `Aoede` (warm, mid-30s, intimate) | `Callirrhoe` (older), `Sulafat` (younger) |
| Muž | `Charon` (deep, authoritative) | `Algieba` (warmer), `Algenib` (newsy) |

Výběr podle brand voice (mladší/starší, energický/klidný).

**Brief.voiceover schema:**
```json
"voiceover": {
  "backend": "gemini",
  "language": "cs",
  "voice": "Aoede",
  "style_instructions": "Speak in Czech with warm intimate tone... PRONUNCIATION RULES: 'BrandName' is pronounced as Czech 'BREND-NEJM'... GRADUATION ARC: soft start → quiet conviction → calm landing.",
  "temperature": 0.75,
  "script": "Plný český text bez pauz."
}
```

**Best practices pro `style_instructions`:**
- Continuous flowing delivery, **NO pauses** (pauzy zní AI-robotické)
- Graduation arc napříč větami (soft → conviction → landing) místo flat tone
- **Phonetic respell pro brand names** přímo ve scriptu, ne v instructions (TTS čte přesně co je napsáno):
  - „Aqueena" → „Akvýna" (anglické „queen" čte špatně)
  - „Zepter" → „Ceptru" (německé Z = české C)
  - „MedAll" → „MedÓl" (anglické „all" čte jako jiný zvuk)
- Female voice mid-30s/40s pro premium wellness; younger pro tech/lifestyle
- NOT a commercial announcer voice

**Inline emotion tags** (Gemini je rozumí): `[short pause]`, `[whispering]`, `[sigh]`, `[soft laugh]`. Použij střídmě — moc tagů zní afektovaně.

### Krok 4: Voiceover (Gemini TTS)

Skill spustí:

```bash
python3 {baseDir}/scripts/generate-voiceover.py \
  --brief /documents/ads/video/[slug]/video-brief.json \
  --output /documents/ads/video/[slug]/voiceover.mp3
```

**Output Kroku 4:**
```
/documents/ads/video/[campaign-slug]/
├── 01-master-storyboard.png
├── voiceover.mp3              ← CZ voiceover, ~10-13 s
└── video-brief.json
```

**STOP. Polož otázku:**

> *„Voiceover je hotový. Poslechni si: [path]. Sedí tempo, výslovnost brand name, emocionální arc? Pokud ne, můžeme upravit script (pauzy/tempo/věty) nebo style_instructions (jiná barva hlasu, jiná energie). Pokud OK, jdeme na finální video."*

Detail v `{baseDir}/references/voiceover-rules.md`.

### Krok 5: Finální video (Seedance 2.0 + ffmpeg post-mix)

**Před produkčním voláním napřed `--dry-run`:**

```bash
python3 {baseDir}/scripts/generate-video-singleshot.py \
  --brief /documents/ads/video/[slug]/video-brief.json \
  --output /documents/ads/video/[slug]/final-singleshot.mp4 \
  --voiceover /documents/ads/video/[slug]/voiceover.mp3 \
  --dry-run
```

Vypíše prompt + uploaded reference URLs **bez** Seedance volání → user vidí, co půjde. Pokud OK, spusť stejný command bez `--dry-run`.

Jediné Seedance volání generuje 15 s video s native music+SFX, pak ffmpeg mixne VO + udělá fade-out.

**Endpoint:** `bytedance/seedance-2.0/reference-to-video` (NE image-to-video — tam jen 1 reference, my potřebujeme až 6).

**Reference layout:**

| Tag | Co je | Role |
|-----|-------|------|
| `@Image1` | Master storyboard PNG | Composition, character archetype, environment, framing, palette |
| `@Image2..@Image6` | Až **5 produktových fotek** (úhly STEJNÉHO produktu) | Lock product silhouette + branding + colors z různých úhlů (front, side, back, grip, in-hand). NE různé kopie produktu |

⚠️ **Doporučeno: 5 produktových fotek** (`--max-refs 6` total). Více úhlů = lepší product fidelity. Skill default je 6 references.

⚠️ **Obrázky se musí uploadnout na FAL CDN přes `fal_client.upload_file_async()`** — Seedance video endpointy odmítají data URLs. **Parametr je `image_urls` (NE `reference_image_urls`).**

**Prompt struktura (~500 slov, Seedance recommended):**
1. Opening: duration + aspect + style + mood
2. **FICTIONAL CHARACTERS** clause — postavy jsou fiktivní, ne reálné osoby; loose face match z briefu, ne 1:1 replikace; internal continuity přes všechny cuts
3. References legend (@Image1/2..6 role + panel locator)
4. Per-shot Subject/Action/Camera lines (~40 slov každý)
5. **START FRAME RULE** — každý shot začíná pixel-precise reprodukcí příslušného panelu
6. **PRODUCT FIDELITY + SINGLE INSTANCE** — match @Image2..@Image6 silhouette/branding/colors, **přesně 1 instance produktu per shot**, žádné duplicaty / mirror / echo
7. **CHARACTER COUNT** — exact counts, žádná duplikace
8. **FACES** forbidden list — anti AI-tells (plastic skin, beauty filter, symmetric features, atd.)
9. **Audio** — native SFX + instrumental music s graduation arc + headroom pro post-mix VO

**Character archetype** se vždy bere **dynamicky z `brief.character.description`** (žádný hardcoded archetyp).

**Pricing:** $0.3024/s standard (15 s = $4.54), $0.2419/s fast (15 s = $3.63).

**ffmpeg post-mix** (probíhá automaticky pokud `voiceover.mp3` existuje):

```
[1:a] = voiceover (volume×2.5, apad to whole_dur)
       │ asplit
       ├─[vo_sc]─→ sidechain control
       └─[vo_main]─→ amix
[0:a] = Seedance music+SFX (volume×0.8) ─→ sidechaincompress (ducked by VO) ─→ amix
                                                                              │
                                                          alimiter + afade=out 1.5s
                                                                              │
                                                          + video fade=out 1.2s
                                                                              │
                                                                          final.mp4
```

Detaily filtergraph + edge cases (silent input fallback, same-file detection) v `{baseDir}/references/post-mix-recipes.md`.

**Mix params jsou nastavitelné přes CLI flagy** bez editace skriptu:
- `--vo-volume 3.0` (default 2.5)
- `--bg-volume 0.6` (default 0.8)
- `--ducking-ratio 12` (default 8)
- `--ducking-threshold 0.03` (default 0.05)
- `--ducking-attack 40` ms (default 20)
- `--ducking-release 500` ms (default 300)
- `--vo-mix-weight 2.0` (default 1.6)
- `--fade-out 2.5` s (default 1.5)

**MIX_ONLY mode** (rychlé iterace post-mixu bez nového FAL volání):

```bash
python3 {baseDir}/scripts/generate-video-singleshot.py \
  --brief <brief> --output <final.mp4> --voiceover <vo.mp3> --mix-only \
  --vo-volume 3.0 --ducking-ratio 12
```

Použije existující `<output>-seedance.mp4` (clean Seedance backup) jako vstup pro ffmpeg, takže můžeš libovolně iterovat na VO/fade/ducking parametrech bez dalších FAL nákladů. Snapshot `-seedance.mp4` se vytvoří automaticky při prvním plném běhu.

**Output Kroku 5:**
```
/documents/ads/video/[campaign-slug]/
├── final-singleshot.mp4              ← finální deliverable (mixed s VO + fade)
├── final-singleshot-seedance.mp4     ← clean Seedance backup (pro MIX_ONLY iterace)
├── 01-master-storyboard.png
├── voiceover.mp3
├── video-brief.json
└── _singleshot-log.json              ← FAL volání log + cost
```

## Quality a spend pravidla

- **Default resolution:** 720p (`resolution: "720p"`) — produkční kvalita pro paid social. 480p jen pro super levné koncepty.
- **Default tier:** `standard` ($0.3024/s). `fast` jen pro 4-6 s drafts.
- **Aspect ratios:** Seedance podporuje `9:16`, `1:1`, `16:9`. `4:5` mapuj na `9:16` nebo `1:1`.
- **Duration cap:** Seedance 1 call = 4-15 s. Pro >15 s se musí dělat ručně víc volání + ffmpeg concat (rare case, default je 15 s).
- **Cuts default:** **5 cuts × 3 s = 15 s** (3×2 grid pro 16:9/1:1). Méně cutů rozbije storyboard layout. Pro 9:16 stejně 5 cuts ale v 6×1 stripu.
- **Reference policy:** vždy storyboard + ≥1 produktová fotka. Bez produktové fotky Seedance fabuluje produkt. Bez storyboardu chybí scene continuity.
- **Audio default:** `generate_audio: True` v Seedance pro native music+SFX. VO se mixuje v ffmpeg post-process.
- **Character description:** vždy v `brief.character.description` — skript pulluje dynamicky.

## Output structure

```
/documents/ads/video/[campaign-slug]/
├── final-singleshot.mp4              ← hlavní deliverable
├── final-singleshot-seedance.mp4     ← clean Seedance backup
├── 01-master-storyboard.png          ← schvalovaný storyboard
├── voiceover.mp3                     ← schvalovaný VO
├── video-brief.json                  ← parametry briefu
├── _singleshot-log.json              ← FAL volání log + cost
└── images/                           ← produktové fotky (input)
```

`[campaign-slug]` = kebab-case (např. `bioptron-medall-anti-aging`, `aqueena-pro-cista-voda`).

## Failure handling

- **`FAL_KEY` chybí** v env / `.env` / Control Center secret store → blokuj s jasnou konfigurační hláškou
- **`ffmpeg`/`ffprobe` chybí** → fallback na Seedance-only audio (žádný VO mix), warning
- **Seedance content policy block** → skript automaticky retryuje s `max_refs=1` (jen storyboard). Pokud i tak block: regen storyboard bez character close-upu, případně `--no-storyboard` + jen produktové fotky
- **Seedance vrátí chybu** → log, retry 3× s exponential backoff (30s, 60s, 120s)
- **Storyboard nesedí** → user řekne co změnit, regenerace s opraveným briefem
- **VO nesedí** → uprav script (phonetic respell, pauzy) nebo style_instructions (jiný hlas, jiná energie), regen
- **Final video produkt špatně** → posiluj `product_visual_identity` v briefu, regen
- **Final video tvář moc AI-looking** → posiluj FACES forbidden list, regen
- **VO se nepřehrál** → MIX_ONLY=1 + ffprobe verify; pokud audio stream existuje ale je tichý, problém v sidechain větvi

## Reference

- `{baseDir}/references/recipes.md` — quick-start brief snippets per use case (start here)
- `{baseDir}/references/gotchas.md` — central registry of non-obvious rules (api / TTS / ffmpeg)
- `{baseDir}/references/storyboard-layout-spec.md` — layout master storyboard PNG
- `{baseDir}/references/seedance-models.md` — FAL Seedance endpointy, params, pricing
- `{baseDir}/references/voiceover-rules.md` — Gemini TTS, voice presets, graduation arc, phonetic respell
- `{baseDir}/references/post-mix-recipes.md` — ffmpeg sidechain ducking, fade-out, MIX_ONLY mode, edge cases (canonical pro mix)
- `{baseDir}/references/audio-rules.md` — high-level 3-layer audio architecture (links to post-mix-recipes for ffmpeg detail)
- `{baseDir}/references/camera-grammar.md` — anamorphic style, cut types, durations, focal length
- `{baseDir}/references/platform-specs.md` — Meta, IG, LinkedIn, YouTube, TikTok, PMax specs
- `{baseDir}/references/brief-schema.md` — JSON schema pro `video-brief.json`

## Návaznost na další skilly

- **Před:** brand-related skilly (lead-magnet-generator, html-presentation-generator) můžou produkovat ad copy → tento skill ho použije jako VO script
- **Po:** finální MP4 → ručně do Meta Ads Manager / LinkedIn Campaign Manager / YouTube Studio / TikTok Ads Manager
