---
name: article-image-generator
description: "Generujte článkové obrázky z provider-neutral image briefů přes nativní image_generate, uložte rastrové soubory pod /documents a vytvořte image-manifest.json pro cílový publisher assets krok."
category: creative
status: ready
version: "1.0"
publishedAt: "2026-04-30"
---
# Article Image Generator

Tento skill je mezikrok mezi článkem a publishingem. Bere `image-briefs.json`, volá nativní `image_generate`, ukládá obrázky a vytváří manifest.

Nepoužívej shell wrapper ani ručně volané OpenRouter/OpenAI HTTP endpointy. Runtime default/fallback pro obrázky řeší nativní `image_generate`.

## Vstup

Primární vstup:

```text
/documents/brand/content/blog/{slug}/image-briefs.json
```

Volitelně:

- cílová složka, výchozí `/documents/brand/content/blog/{slug}/images`
- počet obrázků nebo subset `brief.id`
- požadavek na regeneraci konkrétního obrázku

## Workflow

1. Načti `image-briefs.json`.
2. Zkontroluj, že každý brief má `id`, `filename`, `prompt`, `aspectRatio` a `alt`.
3. Ukaž krátký plán: počet obrázků, cílovou složku, poměry stran.
4. Pro každý brief zavolej native `image_generate`.
5. Ulož rastrový soubor pod `/documents/brand/content/blog/{slug}/images/{filename}`.
6. Ověř, že každý soubor existuje a není prázdný.
7. Vytvoř `/documents/brand/content/blog/{slug}/image-manifest.json`.

## image-manifest.json

```json
{
  "articleSlug": "{slug}",
  "sourceBriefs": "/documents/brand/content/blog/{slug}/image-briefs.json",
  "generatedAt": "YYYY-MM-DDTHH:mm:ssZ",
  "generator": "native:image_generate",
  "images": [
    {
      "id": "hero",
      "placement": "hero",
      "localPath": "/documents/brand/content/blog/{slug}/images/hero.png",
      "filename": "hero.png",
      "aspectRatio": "16:9",
      "alt": "Alt text",
      "prompt": "Prompt actually used",
      "status": "generated"
    }
  ]
}
```

## Prompt pravidla

- Prompt piš anglicky, pokud uživatel nechce jinak.
- Popiš subjekt, scénu, styl, kompozici, světlo, náladu a účel.
- Pokud obrázek nemá obsahovat text, přidej `NO text, NO logos, NO watermarks`.
- Pokud má obsahovat text, drž text krátký a přesně ho uveď.
- Zachovej provider-neutral prompt. Neoptimalizuj zvlášť pro Gemini nebo GPT Image 2, pokud uživatel výslovně nechce provider-specific variantu.

## Výstup do chatu

```markdown
# Obrázky vygenerovány

- **Manifest:** `/documents/brand/content/blog/{slug}/image-manifest.json`
- **Složka:** `/documents/brand/content/blog/{slug}/images/`
- **Počet:** {count}

Další krok: cílový publisher `assets` příkaz (`wordpress-publisher` nebo `cliqsales-blog-publisher`).
```

## Failure handling

Pokud `image_generate` selže, nehlaš úspěch. Zapiš do manifestu jen úspěšné obrázky a vrať přesnou chybu pro selhané briefy. Pokud selže hero image, zastav pipeline.
