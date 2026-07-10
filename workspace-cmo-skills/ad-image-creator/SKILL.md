---
name: ad-image-creator
description: "Generuje skutečné bitmapové reklamní obrázky přes image_generate pro single image, carousel a Google asset ratios; ukládá soubory a manifest pod /documents."
category: creative
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---
# Ad Image Creator

Tento skill bere image briefy z reklamního plánu nebo copy výstupu, volá nativní `image_generate` a ukládá skutečné rastrové soubory. Prompt bez souboru není hotový výstup.

## Kdy použít

Použij pro statické reklamní obrázky, carousel karty, Meta/LinkedIn vizuály, Google Display/PMax image assety a thumbnail pro video v rámci pipeline `meta-ad-strategist` nebo `cliqsales-ad-strategist`.

## Vztah k `ad-generator-gpt-image-2`

`ad-image-creator` je kanonický image krok pro placenou reklamní pipeline: bere konkrétní `ad-image-briefs.json`, generuje přesné assety pro plánované formáty a vytváří `ad-image-manifest.json` pro publisher.

`ad-generator-gpt-image-2` je samostatný šablonový generátor statických reklam z Brand DNA/Product DNA a sady 40 template promptů. Neodstraňuj ho a nepoužívej ho jako náhradu za tento pipeline krok, pokud orchestrátor očekává `ad-image-manifest.json`.

## Vstup

Primární vstup:

```text
/documents/brand/ads/{campaign-slug}/ad-image-briefs.json
```

Pokud `ad-image-briefs.json` neexistuje, vytvoř ho z `ad-copy.json` a `ad-plan.json`.

## Reference

- `references/creative-specs.md` - poměry stran, minimální rozměry a platformové nuance.

## CLI helper

Po vytvoření manifestu vždy spusť validaci přes Python helper, ne přes složitý shell:

```bash
python3 ~/.openclaw/workspaces/cmo/skills/ad-image-creator/scripts/validate_manifest.py /documents/brand/ads/{campaign-slug}/ad-image-manifest.json
```

Helper ověřuje existenci souborů, bitmapový formát, reálné pixely a poměr stran u obrázků se `selectedForPublisher: true` nebo `status: "generated"`. Kandidáty, které nejsou vybrané pro publisher, může manifest ponechat jako `candidate`. Pokud helper skončí chybou, publisher readiness je `blocked` a workflow nesmí pokračovat do `ad-publisher` ani `meta-ads-cli`.

## Workflow

1. Načti briefy, brand vizuální zdroje a dostupné reference.
2. Pro každý brief zkontroluj `id`, `platform`, `format`, `aspectRatio`, `prompt`, `filename`.
3. Ukaž krátký plán: počet publishable obrázků, počet kandidatních variant, formáty a cílovou složku. Pro první draft preferuj poměry, které `image_generate` reálně drží spolehlivě (`1:1`, `9:16`, `16:9`). Poměry jako `4:5` nebo `1.91:1` použij jen tehdy, pokud po generování ověříš skutečné pixely a mismatch opravíš nebo označíš jako failed.
4. Pro produkční reklamní asset vytvoř aspoň 2 kandidatní varianty, pokud uživatel neřekl `smoke`, `rychlý test` nebo `šetři kredity`. Pro Meta single-image první generování dělej jako `1024x1024`, JPEG, `quality: medium`; pro 9:16 thumbnail/video asset použij explicitní `size: "1024x1792"`, JPEG, `quality: medium` místo samotného `aspectRatio`, pokud nástroj size podporuje. `2048x2048`/PNG/high často překročí transportní limit gatewaye před uložením assetu. Vyšší kvalitu použij jen tehdy, když výstup umíš uložit, případně zmenšit/komprimovat a následně znovu validovat. Kandidáty mohou být v manifestu jako `candidate`, ale publisher smí dostat jen vybraný `status: "generated"`.
5. Zavolej `image_generate` pro každý obrázek. Pro placené statické reklamy preferuj `openai/gpt-image-2`, pokud ho nástroj podporuje; pokud použije fallback, zapiš skutečný model/provider z tool resultu do manifestu a netvrď, že výstup je z image-2. Použij reference images, pokud záleží na přesném produktu nebo brand stylu.
6. Ulož soubory do `/documents/brand/ads/{campaign-slug}/images/`.
7. Vytvoř `ad-image-manifest.json` včetně `actualWidth`, `actualHeight`, `expectedAspectRatio`, `actualAspectRatio`, `status` a `selectedForPublisher`.
8. Spusť `scripts/validate_manifest.py` nad manifestem. Pokud validace neprojde, neopravuj to slovně; regeneruj podporovaný poměr nebo označ konkrétní asset jako failed/blocker.
9. Pokud skutečný poměr stran neodpovídá briefu, neoznačuj asset jako `generated` a nepokračuj do publisheru s vadným manifestem. Buď změň brief/format na skutečně podporovaný poměr a regeneruj, nebo označ asset jako `failed_aspect_ratio_mismatch` s `actualWidth`, `actualHeight` a `expectedAspectRatio`.
10. Pokud jde o task, zaregistruj obrázky/manifest jako deliverable před přesunem do review.

## ad-image-briefs.json schema

```json
{
  "campaignSlug": "free-kurz-strategie-ctverecek",
  "briefs": [
    {
      "id": "img-card-01",
      "platform": "meta",
      "format": "carousel_card",
      "aspectRatio": "1:1",
      "size": "1024x1024",
      "quality": "medium",
      "outputFormat": "jpeg",
      "filename": "img-card-01.jpg",
      "prompt": "English production prompt. Visible ad text in campaign language.",
      "visibleText": "Krok 1",
      "alt": "Popis obrázku",
      "sourceAdId": "meta-carousel-001"
    }
  ]
}
```

## ad-image-manifest.json schema

```json
{
  "campaignSlug": "free-kurz-strategie-ctverecek",
  "generator": "native:image_generate",
  "generatorModel": "openai/gpt-image-2",
  "generatedAt": "YYYY-MM-DDTHH:mm:ssZ",
  "images": [
    {
      "id": "img-card-01",
      "platform": "meta",
      "format": "carousel_card",
      "aspectRatio": "1:1",
      "expectedAspectRatio": "1:1",
      "actualWidth": 1024,
      "actualHeight": 1024,
      "actualAspectRatio": "1:1",
      "localPath": "/documents/brand/ads/free-kurz/images/img-card-01.jpg",
      "prompt": "Prompt actually used",
      "status": "generated",
      "selectedForPublisher": true,
      "sourceAdId": "meta-carousel-001"
    }
  ]
}
```

## Prompt rules

- Technický prompt piš anglicky; viditelný text v obrázku piš jazykem kampaně.
- Pokud text není nutný, přidej `NO text, NO logos, NO watermarks`.
- Pro social ads používej jeden focal point a minimum textu v obrázku.
- Prompt nesmí být jen generický popis scény. Musí obsahovat creative angle, composition, lighting, mood, foreground/background, audience cue a konkrétní zakázané prvky.
- Pokud nejsou brand reference, napiš do manifestu `brandVisualContext: "missing"` a použij výraznou, ale nepřisuzovanou art direction; nevymýšlej logo ani brand prvky.
- Pro carousel udrž konzistentní styl mezi kartami a jasně odlišný point každé karty.
- Nepoužívej lokální SVG/HTML jako náhražku za generovaný reklamní obrázek, pokud uživatel chce image ad asset.

## Failure handling

Pokud `image_generate` není dostupný nebo selže, nehlaš hotovo. Pokud chyba říká `Media exceeds 5MB limit`, zkus jednou znovu s menším JPEG (`1024x1024`, `quality: medium`) a do reportu zapiš, že první high/PNG pokus byl nahrazen validním assetem. V manifestu označ selhané briefy a vrať přesnou chybu. Do `ad-publisher` nepokračuj, pokud formát vyžaduje obrázek.

Aspect ratio mismatch je produkční chyba, ne kosmetická poznámka. Pokud např. brief chce `4:5`, ale soubor má `1024 x 1536` (`2:3`), výsledek není validní `4:5` asset. Oprav/regeneruj před publisherem, nebo explicitně zablokuj publisher readiness.
