# Seedance 2.0 — FAL endpoints, params, pricing

ByteDance Seedance 2.0 — produkční video generation model launched April 9, 2026 na fal.ai. Cinematic quality, native audio, real-world physics, director-level camera control.

## Endpoints

| Endpoint ID | Mode | Use case |
|-------------|------|----------|
| `bytedance/seedance-2.0/reference-to-video` | Reference→Video (1-N refs) | **DEFAULT** — multi-reference identity lock (storyboard + product photos) |
| `bytedance/seedance-2.0/image-to-video` | Image→Video (1 ref) | Single keyframe → animation. Méně fidelity než reference-to-video |
| `bytedance/seedance-2.0/text-to-video` | Text→Video | Bez reference, jen prompt. Pro abstraktní pozadí |
| `bytedance/seedance-2.0/fast/reference-to-video` | Reference→Video (fast tier) | Levnější / rychlejší ($0.24/s vs $0.30/s) — pro draft |
| `bytedance/seedance-2.0/fast/image-to-video` | Image→Video (fast) | Levnější varianta |

**Default:** `reference-to-video` standard tier — protože používáme storyboard + až 5 product photos jako multi-reference identity lock. Single-image image-to-video je legacy.

## Authentication

```
Authorization: Key {{FAL_KEY}}
```

`FAL_KEY` v env. Skill ho vyžaduje:

```yaml
metadata: {"openclaw":{"requires":{"env":["FAL_KEY"]},"primaryEnv":"FAL_KEY"}}
```

## Reference-to-Video request body (DEFAULT)

```json
{
  "image_urls": [
    "https://v3.fal.media/files/abc/storyboard-uploaded.png",
    "https://v3.fal.media/files/abc/product-hero-uploaded.jpg",
    "https://v3.fal.media/files/abc/product-alt-uploaded.jpg"
  ],
  "prompt": "Multi-shot video prompt with @Image1/@Image2/@Image3 tagged references...",
  "duration": "15",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "generate_audio": true,
  "seed": null
}
```

⚠️ **Klíčové gotchy:**

1. **Parametr je `image_urls` (NE `reference_image_urls`).** Starší dokumentace na FAL používala druhý název, ale aktuální endpoint chce `image_urls`.
2. **Reference image musí být uploaded HTTPS URL, NE data URL.** Seedance video endpointy odmítají `data:image/png;base64,...` strings (sync endpoint vrátí silent fail s prázdným inputem v dashboardu, async jen blocks).

   ```python
   import fal_client
   url = await fal_client.upload_file_async(str(local_path))
   # url je HTTPS na fal CDN, použij jako image_urls[i]
   ```

3. **Pořadí v `image_urls` poli mapuje na `@ImageN` tagy v promptu:**
   - `image_urls[0]` → `@Image1` (default = master storyboard)
   - `image_urls[1..5]` → `@Image2..@Image6` (úhlové varianty STEJNÉHO produktu — hero + alt angles)
4. **Max 6 reference images** v `image_urls` (FAL aktuální limit). Skill default `--max-refs 6` = 1 storyboard + až 5 produktových fotek.

### Parametry

| Param | Values | Default | Note |
|-------|--------|---------|------|
| `image_urls` | array of HTTPS URLs | _povinné_ | 1-4 referenčních obrázků. Tagy `@Image1..@ImageN` v promptu |
| `prompt` | string | _povinné_ | ~500 slov, Seedance recommended structure (Subject/Action/Environment/Camera/Audio) |
| `duration` | "4"-"15" nebo "auto" | "auto" | Sekundy. Pro skill default 15 |
| `aspect_ratio` | "9:16" / "1:1" / "16:9" | "16:9" | Z briefu |
| `resolution` | "480p" / "720p" / "1080p" | "720p" | Standard tier 720p, 1080p za příplatek |
| `generate_audio` | bool | true | Native ambient SFX + instrumental music |
| `audio_urls` | array (NEPOUŽÍVAT pro reference-to-video) | — | **Bug/undocumented** — Seedance reference-to-video tento parametr ignoruje pro VO output. Pro VO použij ffmpeg post-mix |
| `seed` | int nebo null | null | Pro reprodukovatelnost |

## Image-to-Video request body (legacy)

Pokud chceš jen 1 referenci jako přesný start frame (méně fidelity než multi-ref):

```json
{
  "image_url": "https://v3.fal.media/files/.../keyframe.png",
  "prompt": "...",
  "duration": "8",
  "aspect_ratio": "9:16",
  "resolution": "720p",
  "generate_audio": true
}
```

| Param | Note |
|-------|------|
| `image_url` | Single uploaded HTTPS URL (nikdy data URL) |

V aktuálním pipelinu skill používá image-to-video jen výjimečně (např. krátké testy s 1 keyframe). Default je reference-to-video.

## End frame control (volitelné, image-to-video)

Seedance 2.0 podporuje **start + end frame** control v image-to-video:

```json
{
  "image_url": "https://...keyframe-start.png",
  "end_image_url": "https://...keyframe-end.png",
  "prompt": "...",
  "duration": "8"
}
```

V aktuálním pipelinu **nepoužíváme** — single-shot reference-to-video drží continuity přes storyboard panel reference.

## Text-to-Video (jen pro abstraktní pozadí)

```json
{
  "prompt": "Cinematic anamorphic shot of {scene}, {camera move}, {mood}",
  "duration": "8",
  "aspect_ratio": "9:16",
  "resolution": "720p",
  "generate_audio": true
}
```

V aktuálním pipelinu **nepoužíváme** — vždy máme storyboard + product photos jako reference.

## Pricing (k květnu 2026)

| Tier | Resolution | Price |
|------|-----------|-------|
| Standard | 720p | $0.3024 / sekunda |
| Standard | 1080p | $0.4536 / sekunda (~50% premium) |
| Fast | 720p | $0.2419 / sekunda (-20%) |

**Per-ad cost examples (single Seedance call):**

| Video length | Standard 720p | Fast 720p |
|--------------|---------------|-----------|
| 15 s | $4.54 | $3.63 |
| 10 s | $3.02 | $2.42 |
| 8 s | $2.42 | $1.94 |

Default skill workflow = single 15 s call = ~$4.50 za asset (standard tier 720p).

## Aspect ratios + Seedance constraints

**Podporované:**
- `9:16` — mobile portrait (Meta Reels, Stories, TikTok, YouTube Shorts)
- `1:1` — square (Meta feed, IG feed)
- `16:9` — landscape (YouTube, LinkedIn feed, web)

**Nepodporované přímo:**
- `4:5` (Meta feed video) → mapuj na `1:1` (loss minimal) nebo `9:16` (vertical-first)
- `2:3`, `3:4`, jiné → mapuj na nejbližší

## Async submit workflow (povinný)

Sync endpoint má timeout 60 s, Seedance 720p trvá 60-180 s. Vždy používej async submit:

```python
import fal_client

handler = await fal_client.submit_async(
    "bytedance/seedance-2.0/reference-to-video",
    arguments={
        "image_urls": uploaded_urls,
        "prompt": prompt,
        "duration": "15",
        "aspect_ratio": "16:9",
        "resolution": "720p",
        "generate_audio": True,
    }
)
result = await handler.get()  # blokuje až do dokončení
video_url = result["video"]["url"]
```

## Concurrency / rate limits

**FAL Seedance 2.0 limits (k 2026):**
- Concurrent requests: 3 (free/hobby), 8 (pro), 16 (enterprise)
- Requests per minute: 30
- Requests per day: depends on plan + budget

**Skill default:** **1 concurrent request** — single-shot pipeline dělá jen 1 volání per video, žádný concurrency potřeba.

## Response format

```json
{
  "video": {
    "url": "https://v3.fal.media/files/.../output.mp4",
    "content_type": "video/mp4",
    "file_size": 4521234
  },
  "seed": 12345,
  "request_id": "abc-123-xyz"
}
```

Stáhni `video.url` přes requests do `_clips/cut-NN.mp4`:

```python
import requests

response = requests.get(result["video"]["url"], stream=True)
response.raise_for_status()
with open(output_path, "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
```

## Prompt structure (Seedance recommended)

Per FAL docs, Seedance 2.0 reaguje nejlépe na strukturovaný prompt:

1. **Subjekt** — kdo / co je v záběru (popis postavy, oblečení, produktu)
2. **Akce** — co dělají (konkrétní slovesa, intenzita pohybu)
3. **Prostředí** — kde, světlo, atmosféra
4. **Kamera** — pohyb, focal length, shot type
5. **Audio** — quoted dialog (pro lip sync) NEBO music/SFX cues

V aktuálním pipelinu skill posílá ~500 slov prompt s následující strukturou:

1. Opening (duration + aspect + style + mood) — 1 řádek
2. **FICTIONAL CHARACTERS** clause — character archetype z briefu, loose face match
3. References legend (@Image1/2/3 role + panel locator)
4. Per-shot lines (5×) ve formátu „Start frame: panel N. Action: ... Camera: ..."
5. **START FRAME RULE** — pixel-precise reprodukce panelu N
6. **PRODUCT FIDELITY + SINGLE INSTANCE** — match @Image2..@Image6 (úhly stejného produktu), **přesně 1 instance per shot, žádné duplicaty / mirror / echo**
7. **CHARACTER COUNT** — exact counts, no duplicates
8. **FACES** forbidden list — anti AI-tells
9. **Audio** — SFX + music s graduation arc + headroom pro post-mix VO

Detail v `generate-video-singleshot.py::build_combined_prompt()`.

## Co Seedance dělá dobře / hůř

✓ **Dobře:**
- Camera moves (pan, tilt, crane, dolly, tracking, handheld)
- Cinematic lighting (golden hour, low-key, neon, film noir)
- Anamorphic look (1.33× squeeze, lens flares)
- Real-world physics (water, fabric, hair, smoke)
- Subtle character animation (breathing, blinking, micro-expressions)
- Native music + ambient SFX (instrumental BGM s gradace, scene-appropriate ambient)

✗ **Hůř:**
- Komplexní choreografie (tanec, akce s víc lidmi)
- Specifická lipsync / dialog (animuje pohyb úst, ale ne specifická slova → my proto VO mixujeme v ffmpeg)
- **Český voiceover** (Seedance audio_urls parameter pro reference-to-video je undocumented/buggy → nepoužívat)
- Velké přechody scény uvnitř cutu — proto se používá storyboard s panely, každý shot začíná pixel-precise reprodukcí panelu

## Backend selection logika v skill

```python
parser.add_argument(
    "--mode",
    choices=["reference-to-video", "image-to-video", "text-to-video"],
    default="reference-to-video",
)
parser.add_argument(
    "--tier",
    choices=["standard", "fast"],
    default="standard",
)
```

Endpoint per kombinaci:

| mode | tier | endpoint |
|------|------|----------|
| reference-to-video | standard | `bytedance/seedance-2.0/reference-to-video` (DEFAULT) |
| reference-to-video | fast | `bytedance/seedance-2.0/fast/reference-to-video` |
| image-to-video | standard | `bytedance/seedance-2.0/image-to-video` |
| image-to-video | fast | `bytedance/seedance-2.0/fast/image-to-video` |
| text-to-video | standard | `bytedance/seedance-2.0/text-to-video` |
| text-to-video | fast | (zatím neexistuje) |

## Failure modes + handling

| Error | Příčina | Skill handling |
|-------|---------|----------------|
| `401 Unauthorized` | FAL_KEY invalid/missing | Block, hláška o config |
| `402 Payment Required` | Insufficient credits | Block, hláška o top-up |
| `422 Validation Error` | Invalid params (aspect, duration) | Log + zkus mapovat (4:5 → 1:1) |
| `content_policy_violation` | ByteDance moderation block (face refs nejvíc časté) | Activate **fictional characters clause** v promptu, fallback na storyboard-only (max-refs 1) |
| `429 Rate Limit` | Concurrent limit | Backoff 30s, retry max 3× |
| `500 Server Error` | FAL outage | Backoff 60s, retry max 3× |
| `Timeout` | >180 s queue | Switch z sync na async polling (default už používáme submit_async) |
| `image too large` | Reference > 30 MB | Resize via Pillow (max 2048 px on long side) |
| `aspect ratio unsupported` | User chce 4:5 / 2:3 / atd. | Auto-map na 1:1 nebo 9:16, log warning |

## Content policy bypass

ByteDance má strict moderation pro face references. **Tipy jak projít:**

1. **Fictional characters clause v promptu** — vysvětluje že postavy jsou fiktivní, není likeness reálné osoby:

   > „FICTIONAL CHARACTERS — the people in this ad are entirely fictional, generated personas not based on, modeled after, or resembling any real individual."

2. **Storyboard jako #1 reference** — abstraktní editorial deck (sketch character sheet místo fotorealistického portrétu) prochází lépe než photorealistic face reference

3. **Žádné per-cut keyframes s tvářemi** — face-heavy generated images blokují (proto skill opustil per-cut keyframe pipeline)

4. **Product photos OK** — produkty bez tváří netriggrují face moderation, takže `@Image2/@Image3 = produktové fotky` jsou bezpečné

5. **Pokud i tak block** — fallback `--max-refs 1` (jen storyboard), pokud i to fail, regen storyboard bez character close-upu v Section 1

## Cost guard

Skript `generate-video-singleshot.py` před submitem vypíše cost estimate a žádá potvrzení (kromě `--yes`):

```
📋 Brief: bioptron-medall-anti-aging
💰 Cost estimate: $4.54 (15s, tier standard)

Pokračovat? [y/N]
```

`--yes` flag skip confirmation (default v run scripts).
