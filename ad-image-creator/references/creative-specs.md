# Ad Creative Specs

## Meta

- Feed image: preferuj 4:5 nebo 1:1.
- Stories/Reels: 9:16.
- Carousel: až 10 karet, každá může mít vlastní link; použij konzistentní styl a nenech auto-ordering rozbít sekvenční story.
- Kreativa: jeden focal point, málo textu, produkt/služba v použití, vizuální konzistence mezi variantami.

## LinkedIn

- Single image: JPG/PNG/GIF, max 5 MB.
- Landscape: 1.91:1, doporučeno 1200 x 628.
- Square: 1:1, doporučeno 1200 x 1200.
- Vertical/mobile: 4:5 doporučeno 720 x 900, případně 628 x 1200 / 600 x 900.
- Carousel: JPG/PNG, 1:1, minimálně 1080 x 1080, 2-10 karet, max 10 MB na soubor, bez video karet.

## Google PMax / Display

- Horizontal image: 1.91:1, doporučeno 1200 x 628, minimum 600 x 314, max 5 MB.
- Square image: 1:1, doporučeno 1200 x 1200, minimum 300 x 300, max 5 MB.
- Vertical image: 4:5, doporučeno 960 x 1200, minimum 480 x 600.
- Square logo: 1:1, doporučeno 1200 x 1200, minimum 128 x 128.
- Horizontal logo: 4:1, doporučeno 1200 x 300, minimum 512 x 128.

## Local generation sizes

Použij tyto velikosti jako cílové rozměry, pokud uživatel nezadá jinak. `image_generate` může některé poměry nahradit nejbližším nativním výstupem; po každém generování proto ověř reálné pixely přes `scripts/validate_manifest.py`.

Pro Meta single-image a technické E2E běhy začínej s JPEG `quality: medium` a nejbližším podporovaným rozměrem kolem 1024 px. Ověřený důvod: větší PNG/high výstupy z `openai/gpt-image-2` mohou skončit na `Media exceeds 5MB limit` ještě před uložením souboru, zatímco 1024px JPEG prošel validací i Meta uploadem.

| Aspect ratio | Size |
| --- | --- |
| 1:1 | 1024x1024 pro první Meta pass; 2048x2048 jen pokud nepřekročí transport limit |
| 4:5 | 1024x1280 pro první Meta pass; 1664x2080 jen pokud projde transport/komprese |
| 9:16 | 1024x1792 pro první Meta pass; 1440x2560 jen pokud projde transport/komprese |
| 16:9 | 1792x1024 pro první Meta pass; 2560x1440 jen pokud projde transport/komprese |
| 1.91:1 | 1200x628 pro první Meta pass; 2400x1256 jen pokud projde transport/komprese |
| 4:1 logo | 1200x300 pro první pass; 2400x600 jen pokud projde transport/komprese |

Pro první draft bez post-processingu preferuj `1:1`, `9:16` nebo `16:9`, pokud platformový požadavek dovoluje více variant. Poměry `4:5`, `1.91:1` a `4:1` jsou validní jen když skutečný soubor po generování odpovídá cílovému poměru nebo je manifest označí jako failed/blocker.

## Quality checklist

- Soubor existuje a není prázdný.
- Format je bitmapa (`png`, `jpg`, `jpeg`, `webp`), ne SVG.
- Poměr stran odpovídá briefu.
- Manifest obsahuje skutečné rozměry (`actualWidth`, `actualHeight`) a poměr (`actualAspectRatio`).
- V obrázku není nechtěný text, pseudo-logo ani watermark.
- Viditelný text je krátký a správně napsaný.
- Produkt/brand reference nejsou nahrazené smyšleným logem.
