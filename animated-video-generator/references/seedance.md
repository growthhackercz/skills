# Seedance 2.0 — reference-to-video (FAL)

Animaci dělá výhradně **Seedance 2.0**. Z jednoho storyboard stillu (reference) vyrobí ~15 s klip ve zvoleném stylu. Ověřeno v reálné výrobě (ai-marketer Pixar video).

## Endpoint + parametry

- **Endpoint:** `bytedance/seedance-2.0/fast/reference-to-video` (fast tier ~$0.022/s → **~$3.6 / 15 s**). Standard tier `bytedance/seedance-2.0/reference-to-video` je dražší (~$4.5/15 s), lepší detail — fast stačí na draft i většinu finálů.
- ⚠️ **FAL katalog driftuje** — endpoint ID ověř probe voláním na začátku (precedens: ID se mění mezi verzemi). Když 404, zkus bez `/fast` nebo zkontroluj `fal.ai/models`.
- **Klíčové parametry:**
  - `image_urls` — **HTTPS URL** reference stillu (NE data URL!). Nahraj přes FAL CDN (viz níž).
  - `prompt` — styl deskriptor (z `styles.md`) + popis akce/kamery. **Bez textu** (`no text, no letters`).
  - `duration` — `"15"` (string), default cíl.
  - `aspect_ratio` — `"16:9"`.
  - `resolution` — `"720p"` (draft/default), `"1080p"` jen na schválený finál.
  - `generate_audio` — `False` (zvuk řešíme sami v Kroku 4–6; ušetří a nemícháš cizí zvuk).

## Submit přes fal_client.subscribe (POVINNÉ — řeší frontu i stažení spolehlivě)

```python
import os, urllib.request, fal_client
os.environ["FAL_KEY"] = FAL_KEY
file_url = fal_client.upload_file("still.png")            # reference still na FAL CDN (Seedance nebere data URL)
res = fal_client.subscribe("bytedance/seedance-2.0/fast/reference-to-video", arguments={
    "image_urls":[file_url], "prompt":PROMPT, "duration":"15",
    "aspect_ratio":"16:9", "resolution":"720p", "generate_audio":False})
urllib.request.urlretrieve(res["video"]["url"], "clip.mp4")
```

> ⚠️ **NEpoužívej ruční urllib `response_url` poll** — u bytedance/seedance endpointu vrací **404** (pojmenovaná chyba, ověřeno). `fal_client.subscribe` queue/poll/výsledek řeší správně.
> ⚠️ **app_id BEZ `fal-ai/` prefixu** (`bytedance/...`) — s prefixem submit/response 404.
> ⚠️ **Spouštěj systémovým python3** (fleet openclaw = 3.11, lokál mac = /usr/bin/python3 3.9 — oba mají `fal_client` 1.0.0 i funkční pyexpat). Jen **homebrew python 3.14** má rozbitý pyexpat → tam `fal_client` neimportuje; to NENÍ fleet problém.

## Face moderation 422 (Unprocessable Entity)

Seedance blokuje detaily reálně vypadajícího obličeje → klip 422.

**Fix (osvědčené):**
1. **Face-light / wide storyboard** — postava z dálky, zezadu, 3/4, nebo akce-bez-detailu. Žádný extrémní close-up obličeje.
2. **„Fictional cartoon character" klauzule** v promptu (a v storyboard promptu) — explicitně, že jde o smyšlenou kreslenou postavu.
3. Když 422 přesto padne → regeneruj storyboard still face-light verzi, pak Seedance znovu.

## Pravidla výroby

- **`--dry-run` první** — vypiš prompty + cenu (počet klipů × ~$3.6) + STOP. Generuj až po schválení.
- **Žádný text do promptu jako obsah** — Seedance komolí (hlavně češtinu). Text = HyperFrames vrstva.
- **QA po každém klipu** — extrahuj 4–6 framů (`ffmpeg fps=0.4 tile`), Read. Hledej: komolený text, zacyklený/duplicitní pohyb (Seedance občas zopakuje scénu — pozn. do `assembly.md` na střih), špatnou kompozici.
- **Konzistence** — všechny klipy ze stejné postavy/prostředí (stejný styl deskriptor + reference still ze stejné série).
- Klipy ukládej do `documents/videos/<slug>/_clips/` (`v-clip1.mp4`, …), každý ~15 s.

Hotový kód: `scripts/gen_seedance.py` (upload + submit + poll + download, `--dry-run`).
