---
name: ad-video-creator
description: "Vytváří produkčně použitelná reklamní videa přes fal.ai pro placené reklamy; podle platformy, cíle, zadání a budget omezení volí formát, délku, audio, model/quality tier a text-to-video vs image-to-video. Krátký testový klip použije jen když zadání chce rychlý nebo levný draft."
category: creative
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---
# Ad Video Creator

Tento skill vytváří skutečné reklamní video assety. Používá fal.ai přes Control Center video API/helper nebo přímo přes fal.ai konfiguraci v runtime. Textový scénář bez MP4 není hotový video výstup.

## Kdy použít

Použij pro krátké placené video ads, UGC/demo concept, Meta Reels/Stories video, LinkedIn video, Google PMax video asset nebo video complement ke carouselu.

## Vstup

Primární vstup:

```text
/documents/brand/ads/{campaign-slug}/ad-video-briefs.json
```

Pokud soubor neexistuje, vytvoř ho z `ad-plan.json`, `ad-copy.json` a dostupných image assetů.

## Reference

- `references/video-models.md` - model selection, ratios, durations.

## Preferovaný helper

Použij:

```bash
python3 scripts/ad_video.py validate --input /documents/brand/ads/{campaign-slug}/ad-video-briefs.json
python3 scripts/ad_video.py generate \
  --input /documents/brand/ads/{campaign-slug}/ad-video-briefs.json \
  --output-dir /documents/brand/ads/{campaign-slug}/videos \
  --mode continue \
  --result-file /documents/brand/ads/{campaign-slug}/ad-video-generate-result.json
```

Helper volá `$CC_URL/api/media/video` s `$CC_API_KEY`; backend pak použije fal.ai. Pokud `CC_URL`, `CC_API_KEY` nebo backend `FAL_KEY` chybí, vrať přesný blocker. Tokeny nikdy nevypisuj.

Pokud je brief uložený už v adresáři `.../videos/ad-video-briefs.json`, můžeš `--output-dir` vynechat; helper ukládá MP4 do stejného `videos` adresáře a nevytváří vnořené `videos/videos`.

U dlouhých běhů nerediriguj stdout do result souboru. Použij `--result-file`; helper průběžně zapisuje `ad-video-manifest.json` i result JSON po každém dokončeném assetu, takže operator vidí, která videa už existují, i když další fal.ai request ještě běží.

## Workflow

1. Rozhodni, zda video nahrazuje nebo doplňuje carousel.
2. Vyber `text-to-video` pro koncept bez schváleného obrázku, nebo `image-to-video` pro animaci konkrétního vizuálu/produktu.
3. Použij jen poměry podporované helperem: `9:16`, `1:1` nebo `16:9`. Pokud platformová specifikace uvádí `4:5`, pro video ji mapuj na `9:16` pro mobile-first kreativu nebo `1:1` pro feed draft.
4. Zvol délku podle platformy a cíle, ne podle ceny testu. Produkční defaulty: Meta Reels/Stories/short-form 10 s, Meta explainer/awareness 15 s, LinkedIn 15 s, Google PMax/YouTube 15 s. 3-5 s použij jen pro explicitní rychlý/levný technický E2E test. Aktuální Kling v3 helper podporuje 3-15 s na jeden asset; pokud uživatel chce LinkedIn 30 s, navrhni dvě 15s části/varianty nebo se zeptej na schválení delší postprodukce.
5. Ulož `ad-video-briefs.json`.
6. Spusť helper, ověř soubor `test -s` a `file`.
7. Vytvoř `ad-video-manifest.json`.
8. Pokud jde o task, zaregistruj MP4 a manifest jako deliverable.

## ad-video-briefs.json schema

```json
{
  "campaignSlug": "free-kurz-strategie-ctverecek",
  "videos": [
    {
      "id": "vid-001",
      "platform": "meta",
      "format": "story_video",
      "mode": "text-to-video",
      "prompt": "Short production prompt for the final ad video.",
      "duration": "15",
      "aspectRatio": "9:16",
      "qualityTier": "pro",
      "generateAudio": false,
      "filename": "vid-001.mp4",
      "sourceAdId": "meta-video-001"
    }
  ]
}
```

Pro image-to-video použij:

```json
{
  "mode": "image-to-video",
  "imageUrl": "https://public-url-or-uploaded-asset.png",
  "prompt": "Animate the subject with subtle camera motion..."
}
```

Volitelně pro produkční multi-shot video:

```json
{
  "duration": "15",
  "qualityTier": "pro",
  "multiPrompt": [
    { "prompt": "0-4 s: scroll-stopping problem hook, mobile-first framing.", "duration": "4" },
    { "prompt": "4-10 s: product/offer demonstration with brand-consistent visual rhythm.", "duration": "6" },
    { "prompt": "10-15 s: proof point and clear CTA end frame.", "duration": "5" }
  ],
  "shotType": "customize"
}
```

## Quality a spend pravidla

- Default pro produkční placenou reklamu je `qualityTier: "pro"`.
- `qualityTier: "standard"` použij jen když zadání explicitně chce rychlý, levný nebo technický test.
- `qualityTier: "4k"` použij jen při explicitním požadavku na 4K/high-end hero asset; bez požadavku není 4K nutné pro běžné social placements.
- `generateAudio: false` zůstává default, pokud není zadaný voiceover/hudba. Reklama musí fungovat i bez zvuku.
- Preferuj `image-to-video`, když existuje schválený image asset, produktový obrázek nebo brand vizuál; pomáhá konzistenci. `text-to-video` použij pro koncept bez vizuálu.

## Failure handling

- Pokud fal.ai není nakonfigurovaný, ulož briefy a vrať `blocked_missing_fal_key`.
- Pokud API vrátí chybu, nehlaš hotovo a nepředstírej video.
- Pokud video není veřejně dostupné pro publisher, doplň upload krok nebo označ `blocked_missing_public_video_url`.
- Do `ad-publisher` nepokračuj s video placeholderem, pokud formát vyžaduje video.
- Do `meta-ads-cli` předávej video jen s `ad-video-manifest.json` a současně s thumbnail obrázkem z `ad-image-manifest.json`; samotné MP4 bez thumbnailu není pro Meta video creative připravený asset.
