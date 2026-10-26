# Product Carousel — Creative Specs

## Cílový formát

PDP / e-shop carousel fotky se generují jako **čtverec 1:1** (standard pro produktové carousel na Shopify i většině e-shopů, dobře se ořezává na mobilu).

| Vlastnost | Hodnota |
|---|---|
| Poměr stran | `1:1` |
| Generovaný rozměr | `1024x1024` |
| Format | JPEG, `quality: medium` |
| Upscale (volitelný) | `2000x2000` přes `scripts/upscale.py` |

## Proč 1024² a ne rovnou 2000²

`image_generate` (GPT image 2) spolehlivě drží jen `1:1`, `9:16`, `16:9` a kolem 1024 px. Větší PNG/high výstupy (např. `2048x2048`) často skončí na `Media exceeds 5MB limit` ještě před uložením souboru. Proto:

- **Default = `1024x1024` JPEG medium** — spolehlivě projde a vypadá dobře.
- **2000×2000 jen jako post-krok** (upscale z hotových 1024²), pokud klient chce plnou Shopify velikost pro ostrý zoom na PDP.

Po každém generování ověř **skutečné pixely** přes `scripts/validate_carousel.py` — `image_generate` může poměr nahradit nejbližším nativním výstupem.

## Konzistence sady (klíčové pro carousel)

Carousel působí jako jedna kampaň jen když je celá sada vizuálně sladěná:

- **Stejné rozměry** napříč všemi 6 obrázky (validátor to kontroluje a selže, pokud se liší).
- **Stejné světlo / grading / pozadí** — drženo přes schválený hero jako style anchor (2. reference u typů 2–6).
- **Stejná fotka produktu** jako 1. reference ve všech voláních → produkt je všude identický.

## Reference images (pořadí)

Max 3 na volání:
1. **Fotka produktu** (vždy) — věrnost produktu.
2. **Schválený hero** `01-hero.jpg` (typy 2–6) — style anchor. U pilotního hera místo něj brand-board.
3. **Brand-board** (pokud existuje) — vizuální jazyk značky.

Reference předávej **runtime cestou** `/home/node/documents/...`, výstup ukládej do `/documents/...`.

## Quality checklist

- [ ] Soubor existuje a není prázdný.
- [ ] Format je bitmapa (`jpg`/`jpeg`/`png`/`webp`), ne SVG.
- [ ] Poměr je `1:1` (tolerance ±1,5 %).
- [ ] Všech 6 obrázků má stejné rozměry (konzistence sady).
- [ ] Produkt na fotce odpovídá reálnému produktu (věrnost, ne smyšlený tvar/logo).
- [ ] U typu „Nabídka" je text krátký, čitelný na mobilu a správně napsaný v jazyce trhu.
- [ ] U ostatních typů není nechtěný text, watermark ani pseudo-logo.
- [ ] Žádné fake-looking AI ruce/obličeje, žádný clutter.
- [ ] Manifest obsahuje skutečné rozměry (`actualWidth`, `actualHeight`, `actualAspectRatio`).

## Cost orientačně (k 2026)

`image_generate` 1024² ≈ nízké jednotky centů / obrázek. Plná sada 6 typů = ~6 volání. Regenerace jednotlivého typu = +1 volání. Pilot-first (krok 4) šetří kredity — nepálí celou sadu, dokud klient neschválí styl na pilotním heru.
