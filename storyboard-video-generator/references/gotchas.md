# Gotchas — central registry of non-obvious rules

Sbírka všech "POZOR" pravidel, která jinak nejsou objevitelná. Pokud něco nedává smysl nebo skill selhává, koukni nejdřív sem.

## FAL / Seedance API

### `image_urls`, ne `reference_image_urls`
Aktuální endpoint `bytedance/seedance-2.0/reference-to-video` chce parametr `image_urls` (array). Starší FAL dokumentace mluví o `reference_image_urls` — to už nefunguje, request projde s prázdným inputem.

### Data URLs Seedance odmítá
Reference images **musí** být uploaded HTTPS URLs (FAL CDN). `data:image/png;base64,...` strings způsobí silent fail (sync) nebo block (async). Použij `fal_client.upload_file_async()`.

### `audio_urls` parametr je v reference-to-video buggy
Pro `bytedance/seedance-2.0/reference-to-video` Seedance ignoruje `audio_urls` a vrátí silent video. Voiceover se proto **mixuje až post** v ffmpeg, ne přes Seedance.

### Sync endpoint má 60 s timeout
Seedance 720p generation trvá 60–180 s. Vždy `submit_async()` + `handler.get()`, ne sync POST.

### Max 6 references v `image_urls` (FAL aktuální limit)
Skill default = 1 storyboard + až 5 produktových fotek = 6. Víc se odmítne.

### Reference image > 30 MB se odmítne
Auto-resize přes Pillow na 2048 px (long side). Nebo PNG → JPG.

## Gemini 3.1 Flash TTS

### `language_code` nechce ISO kód
Vyžaduje descriptive form: `"Czech (Czech Republic)"`, ne `"cs"`. Mapping v `generate-voiceover.py::LANG_MAP`. Bez správného formátu Gemini auto-detect a často šlápne vedle.

### Phonetic respell brand names přímo VE SCRIPTU, ne v style_instructions
TTS čte přesně co je napsáno. Brand „Aqueena" napiš ve scriptu jako „Akvýna", ne v instructions. Instructions použij jen na vysvětlení („'Akvýna' is the brand 'Aqueena'").

### „NO pauses" v style_instructions je povinné
Bez explicitního zákazu vkládá Gemini nucenou pauzu po každé tečce. Pro 15 s ad to ukrojí 2–3 s, které pak chybí. `[short pause]` tagy ve scriptu mají prioritu i nad „NO pauses".

### Inline emotion tagy fungují, ale střídmě
`[short pause]`, `[whispering]`, `[sigh]`, `[soft laugh]` — Gemini umí, ale moc tagů zní afektovaně.

## ffmpeg post-mix

### `apad` bez `whole_dur` extenduje nekonečně
Pro `apad=whole_dur=15` (přesně 15 s tichem) — bez `whole_dur` `apad` extenduje nekonečně, `-shortest` clipne nepředvídatelně.

### `asplit` je povinné když VO použiješ 2× (sidechain + main)
Bez `asplit` druhý filter dostane prázdný stream → VO mizí z výstupu.

### Same-file write conflict
ffmpeg odmítá source == output. Skill detekuje a píše do `*.__mix_tmp__.mp4`, pak rename. Ručně: explicit temp file.

### Video fade-out vyžaduje re-encode
`-c:v copy` nelze použít s `-vf fade` — musíš `-c:v libx264`.

### Reálná duration ≠ requested
Seedance vrátí 14.5–15.0 s pro „15 s" request. Probe přes `ffprobe` pro správný fade-out timing, ne hardcode.

## Skill workflow

### `cut_count` musí být 5
Storyboard layout (3×2 grid 16:9/1:1, 6×1 strip 9:16) má 6 cell — 5 cuts + 1 NOTES. Jiná hodnota rozbije layout. Validátor hard-fail.

### `product_visual_identity` je klíčové pro storyboard fidelity
GPT Image 2 halucinuje generické tvary v malých thumbnailech. Bez explicitního popisu (shape, colors, branding placement, ABSOLUTE NEGATIVE LIST) v 60 % případů produkt nesedí. Validátor warning.

### `character.description` se dynamicky vsadí do Seedance promptu
Ne hardcoded fallback. Bez něj Seedance dostane generický „protagonist" → random model každý run.

### `scene_continuity` jen když cuts sdílí lokaci
Pokud ano → vyplň, model dostane "FIXED SCENE" clause. Pokud cuts skáčou outdoor → indoor → outdoor, **NEPLŇ** — jinak model zamotá lokace.

### Aspect ratio mapping
Seedance umí jen `9:16`, `1:1`, `16:9`. `4:5` (Meta feed) → mapuj na `1:1` (preferred) nebo `9:16` + crop v post.

### Music gradation rule v promptu je povinná
Bez explicitního „MUST gradate across full {N}s arc, natural musical resolution in final 1–2s" Seedance utne hudbu brutálním cutem na 14.99s. Skill clause vkládá automaticky.

### FACES anti-AI-look clause v promptu je povinná
Bez ní Seedance/Veo/Sora produkují airbrushed plastic faces. Skill explicitně zakazuje "plastic skin, beauty-filter, symmetric features, glassy waxy sheen, fused fingers".

## Content moderation

### Face references často triggrují ByteDance content_policy
Skill má v promptu **fictional characters clause** která většinu blokací předchází. Pokud i tak block:
1. Auto-fallback na `--max-refs 1` (jen storyboard) — skill to dělá automaticky při retry
2. Manual: regen storyboard bez character close-upu v Section 1
3. Manual: `--no-storyboard` + jen produktové fotky

### Storyboard prochází lépe než per-cut keyframes
Face-heavy generated keyframes triggrují content_policy častěji. Skill default = storyboard + product photos, žádné per-cut keyframes (deprecated path).

## Cost / iterations

### `--mix-only` je zdarma
Iterace na fade/ducking parametrech bez nového FAL volání. Skill udržuje `*-seedance.mp4` clean backup automaticky.

### `--dry-run` upload OK, neplatí FAL
Build prompt + upload refs → vypíše prompt + URLs, ale neposlat Seedance request. Pro inspekci promptu před spaľovaním FAL credits.

### Mix params jako CLI flags
`--vo-volume`, `--bg-volume`, `--ducking-ratio`, `--ducking-threshold`, `--ducking-attack`, `--ducking-release`, `--vo-mix-weight`, `--fade-out`. Žádný edit Pythonu pro tweak.

### `--tier fast` ušetří 20 %
$0.2419/s vs $0.3024/s. Pro draft / koncepty. Production = standard.

### `--resolution 480p` ušetří ~50 %
~$2.40 vs $4.54 pro 15 s. Jen pro super levné koncepty, ne paid social.

---

## Pokud to fakt zlobí

1. Spusť `--dry-run` — uvidíš plný prompt + uploaded URLs bez spáleného FAL credit
2. Spusť `python3 scripts/validate-brief.py --input video-brief.json` — validátor odhalí schema problémy
3. Koukni na `_singleshot-log.json` po posledním běhu — args + result
4. `MIX_ONLY=1` pokud máš `*-seedance.mp4` a iteruješ jen post-mix
