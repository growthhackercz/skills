# Video Models And Specs

## Runtime

Primární runtime je Control Center endpoint:

```text
POST /api/media/video
```

Backend používá fal.ai:

- text-to-video: `fal-ai/kling-video/v3/standard/text-to-video`
- text-to-video pro: `fal-ai/kling-video/v3/pro/text-to-video`
- text-to-video 4k: `fal-ai/kling-video/v3/4k/text-to-video`
- image-to-video standard/pro/4k: `fal-ai/kling-video/v3/{standard|pro|4k}/image-to-video`

## Model selection

- `text-to-video`: concept video, kdy není potřeba přesný produktový obraz.
- `image-to-video`: kdy existuje schválený image asset, produktový obrázek, carousel hero nebo brand vizuál; preferuj pro konzistenci.
- `qualityTier: "pro"`: default pro produkčně použitelný paid ad asset.
- `qualityTier: "standard"`: jen pro explicitní rychlý/levný technický test.
- `qualityTier: "4k"`: jen když uživatel chce high-end/4K hero asset.
- `generateAudio: false` default, pokud není potřeba hlas/hudba. Ad musí fungovat i bez zvuku.

## Platform specs

Pozor: aktuální Control Center video helper přijímá pouze `16:9`, `9:16` a `1:1`.
Platformové poměry mimo tuto sadu neposílej do `ad-video-briefs.json`; převeď je na nejbližší podporovaný poměr.

Meta:

- Feed: použij `1:1`; pokud chceš mobile-first vertical, použij `9:16`.
- Stories/Reels: 9:16.
- Krátký hook v prvních 1-2 sekundách.
- Délka: 10 s pro direct-response short-form, 15 s pro explainer/awareness nebo když video nese celé sdělení. 5 s jen pro technický test.

LinkedIn:

- MP4 draft přes helper: použij `1:1`, `9:16` nebo `16:9`. Pokud raw platform spec uvádí `4:5`, mapuj na `1:1` nebo `9:16` podle placementu.
- LinkedIn paid video prakticky navrhuj 15 s; pokud zadání vyžaduje 30 s, vytvoř dvě 15s části/varianty nebo se zeptej na schválení postprodukce, protože aktuální Kling v3 generuje max 15 s na jeden asset.
- Thumbnail doporučený.

Google PMax:

- Video orientace: 16:9, 9:16 a 1:1.
- Google doporučuje dodat vlastní video, ne spoléhat jen na auto-generation.
- Praktický produkční draft: 15 s pro PMax/YouTube asset, pokud uživatel nezadá jinak.

## Prompt checklist

- První frame a hook.
- Subjekt, prostředí, kamera, pohyb, styl, tempo.
- Pro 15 s video použij `multiPrompt` ve 2-3 shotech: hook, demonstrace/proof, CTA/end frame.
- Viditelný text jen když je nutný a velmi krátký.
- CTA nebo finální frame.
- Negativni prompt: blur, distortion, low quality, unreadable text, watermark, fake logo.
