---
name: "product-image-generator"
description: "Vytvoří kompletní sadu konverzních produktových fotek pro e-shop / PDP carousel z reálné fotky produktu a brand DNA"
---

# Product Image Generator

**Vytvoří kompletní sadu konverzních produktových fotek pro e-shop / PDP carousel (hero výsledek, nabídka, social proof, detail produktu, před-po, lifestyle) z reálné fotky produktu a brand DNA. Pro Shopify a další e-shopy.**

## Engine
Generuje se přes nativní tool `image_generate` (GPT image 2, default backend OpenClaw — žádný API klíč navíc, billing přes Control Center).

Reference se předávají parametrem `images` (pole cest, max 3) — NE jako CLI flag `--reference`. Cesty jsou runtime `/home/node/documents/...` (ne `/documents/...`).

Výstupy ukládej do `/documents/brand/products/<produkt-slug>/carousel/`.

Pořadí referencí: `[fotka produktu, (po pilotu) schválený hero jako style anchor, brand-board]`.

Plné prompt šablony pro všech 6 typů: `{baseDir}/references/carousel-types.md`. Rozměry, poměry, upscale a quality checklist: `{baseDir}/references/creative-specs.md`.

## Workflow

### Krok 0 — Kontext
Zjisti:
- Který produkt (slug ve `/documents/brand/products/`). Pokud uživatel neřekl, vypiš dostupné produkty (`ls products/`) a zeptej se.
- Jazyk / trh pro text na obrázcích (CZ / EN / ES). Text se objevuje na víc kartách (nabídka, recenze u social proof, callouty/složení u detailu, BEFORE/AFTER labely u transformace). Default = jazyk komunikace uživatele.

### Krok 1 — Načti produkt a brand kontext
- **Fotky produktu** — z `/documents/brand/products/<slug>/images/` načti max 3 nejlepší fotky (různé úhly produktu). Pokud složka prázdná → **STOP**, vyžádej fotku.
- **Product DNA** — pokud `productDNA.md` existuje, vytáhni: název produktu, co dělá a pro koho, klíčové benefity, USP, cílovou skupinu, transformaci před→po. Z toho připrav pro každý z 6 typů JINÝ konkrétní úhel (`{ANGLE}`) — mapování typ → co čerpat je v `carousel-types.md`. Žádné dva typy nesmí mít stejný úhel.
- **Brand DNA** — pokud `brandDNA.md` existuje, vytáhni: paletu (HEX), fotografický styl, emoční tón, vizuální asociace.
- **Brand board** — pokud `🖼brand-board.png` existuje, drž ho jako referenci vizuálního jazyka (NE jako předlohu ke kopírování).

Pokud volitelné zdroje chybí, pokračuj s tím, co máš — ale řekni uživateli, že brand konzistence bude slabší (generická prémiová art direction místo věrné značce).

### Krok 2 — Vyber typy
Default = celá sada 6 typů (kompletní carousel). Uživatel si může vyžádat jen podmnožinu (např. „jen hero a lifestyle").

Sada 6 typů (detail v `references/carousel-types.md`):
| # | Typ | Co dělá | Text/grafika v obrázku |
|---|-----|---------|------------------------|
| 1 | Hero — výsledek | Komunikuje kýžený výsledek/transformaci, ne jen „tady je produkt" | Min. (produkt + scéna) |
| 2 | Nabídka / hodnota | Jasná nabídka (2+1, doprava zdarma, záruka, balíček) | Ano — nabídkový text |
| 3 | Social proof / důvěra | UGC styl, spokojení zákazníci + recenze | Ano — hvězdy, citáty recenzí |
| 4 | Detail / vlastnosti | Apple-style detail, materiály, složení | Ano — callouty, ingredience |
| 5 | Před → po | Emoční kontrast, problém → řešení | BEFORE / AFTER labely |
| 6 | Lifestyle / identita | Aspirace, „tím člověkem chci být" | Min. |

### Krok 3 — 🛑 STOP: plán generování (povinný checkpoint před pálením kreditů)
Než cokoli vygeneruješ, ukaž uživateli a počkej na schválení:
- Produkt + počet vybraných typů
- Počet volání `image_generate` = 1 (pilot) + zbytek sady (např. 6 typů = 6 volání; regenerace navíc se počítají zvlášť)
- Cílová složka `/documents/brand/products/<slug>/carousel/`
- Rozměr: 1:1, 1024x1024, JPEG (spolehlivé). Upscale na 2000×2000 nabídnu na konci.
- Hláška ve stylu: „Vygeneruji sadu 6 produktových fotek pro [produkt] — nejdřív 1 pilotní hero ke schválení, pak zbylých 5. Celkem ~6 volání generátoru. Pokračovat?"

Bez „ano" negeneruj.

### Krok 4 — Pilot: Hero ke schválení
Vygeneruj jen typ 1 (Hero) jako pilot:
```
🖼image_generate (tool) s parametry:
  prompt: <celý Hero prompt z carousel-types.md, dosazené {PRODUCT} + {BRAND_CONTEXT}>
  images: ["/home/node/documents/brand/products/<slug>/images/<foto>.jpg", "/home/node/documents/brand/brand-board.png"]
  size: "1024x1024"
  quality: "medium"
  outputFormat: "jpeg"
  filename: "/home/node/documents/brand/products/<slug>/carousel/01-hero.jpg"
```

Reference produktu jdou v poli `images` (ne flag `--reference`). Rozměr řídí `size`, ne text promptu.

Ukaž výsledek a zeptej se: „Sedí styl a věrnost produktu? Schválit jako vzor pro zbytek sady, nebo upravit?"

Pokud úprava → uprav prompt, přegeneruj hero (krátká hláška „generuji znovu, volání #N").

Pokud OK → schválený hero je style anchor pro zbylých 5.

### Krok 5 — Dogeneruj zbytek sady (konzistentně)
Pro každý zbylý vybraný typ vygeneruj obrázek. Konzistenci drž takto:
- Stejná fotka produktu jako 1. položka `images`.
- Schválený hero jako 2. položka `images` (style anchor — stejné světlo, grading, produkt). ⚠️ Hero drží jen styl/světlo/produkt, NE lidi — na každé kartě musí být vizuálně jiní lidé/rodina.
- Celý prompt typu ze šablony (`carousel-types.md`) s dosazeným `{PRODUCT}` + `{BRAND_CONTEXT}` + `{ANGLE}` (per typ jiný úhel z Product DNA) — neparafrázuj, nezkracuj.

```
🖼image_generate (tool) s parametry:
  prompt: <celý prompt typu N z carousel-types.md, dosazené {PRODUCT} + {BRAND_CONTEXT}>
  images: ["/home/node/documents/brand/products/<slug>/images/<foto>.jpg", "/home/node/documents/brand/products/<slug>/carousel/01-hero.jpg", "/home/node/documents/brand/brand-board.png"]
  size: "1024x1024"
  quality: "medium"
  outputFormat: "jpeg"
  filename: "/home/node/documents/brand/products/<slug>/carousel/0N-<typ>.jpg"
```

Pojmenování výstupů: `🖼01-hero.jpg`, `🖼02-nabidka.jpg`, `🖼03-social-proof.jpg`, `🖼04-detail.jpg`, `🖼05-pred-po.jpg`, `🖼06-lifestyle.jpg`.

### Krok 6 — Manifest + validace
Zapiš `/documents/brand/products/<slug>/carousel/carousel-manifest.json` (schema níž) se skutečnými rozměry každého obrázku.

Spusť validaci (ne ručně shellem):
```bash
python3 {baseDir}/scripts/validate_carousel.py /home/node/documents/brand/products/<slug>/carousel/carousel-manifest.json
```

Helper ověří: soubor existuje a je bitmapa, reálné pixely odpovídají manifestu, poměr je 1:1, a všechny obrázky v sadě mají stejné rozměry (konzistence carousel). Pokud validace selže, neoznačuj sadu jako hotovou — oprav nebo přegeneruj vadný kus.

### Krok 7 — Zobraz, nabídni iteraci a upscale
Ukaž sadu uživateli (cesty k souborům).

Nabídni regeneraci jednotlivého typu (např. „lifestyle víc do tepla", „detail s viditelnějším složením").

Nabídni upscale na 2000×2000 pro Shopify:
```bash
python3 {baseDir}/scripts/upscale.py /home/node/documents/brand/products/<slug>/carousel/ --to 2000
```

Upscale je volitelný post-krok (vyžaduje Pillow). Originály 1024² zůstávají, upscalované jdou do `carousel/2000/`.

#### carousel-manifest.json schema
```json
{
  "productSlug": "bioptron-medall",
  "generator": "native:image_generate",
  "generatorModel": "openai/gpt-image-2",
  "language": "cs",
  "generatedAt": "YYYY-MM-DDTHH:mm:ssZ",
  "images": [
    {
      "id": "01-hero",
      "type": "hero",
      "expectedAspectRatio": "1:1",
      "actualWidth": 1024,
      "actualHeight": 1024,
      "actualAspectRatio": "1:1",
      "localPath": "/documents/brand/products/bioptron-medall/carousel/01-hero.jpg",
      "prompt": "Prompt actually used",
      "visibleText": null,
      "status": "generated"
    }
  ]
}
```

## Pravidla
- **Produkt je svatý** — výstup musí věrně zachovat reálný produkt z dodané fotky. Vždy předávej fotku produktu jako referenci. Nikdy nenech AI vymyslet jiný tvar/barvu/logo produktu.
- **Konzistence sady** — všech 6 obrázků působí jako jedna kampaň: stejné rozměry, sladěné světlo/grading (drženo přes hero style anchor).
- **Veškerý viditelný text v jazyce trhu** (default čeština) — text, který má být VIDĚT na obrázku (nabídka, recenze, callouty, labely), piš česky se správnou diakritikou; i PŘED/PO (ne anglicky BEFORE/AFTER). Technický popis scény piš anglicky (lepší výsledky GPT image).
- **Nech prompty generovat text/grafiku** — Kenyonovy prompty samy tvoří recenze a hvězdy (social proof), callouty a složení (detail), před/po labely (transformace) i nabídku. Nepotlačuj je — jsou jádrem konverzního charakteru karet.
- **🚫 Žádné brand logo / wordmark / watermark jako overlay** — výstup NESMÍ mít v rohu „Zepter", „Live100", „Club Live 100" apod. Povolené je jen značení fyzicky na produktu (potisk na těle přístroje). ⚠️ Brand-board reference logo obsahuje — v promptu explicitně instruuj „do NOT copy any logo from references".
- **🎩 Prémiový editoriál + čitelnost + neopakovat se** — tři pravidla, co rozhodují o kvalitě sady:
  1. **Copywriting prémiový editoriál** — elegantní, sebevědomý, moderní, benefit-led ale jemný; jako reklama v luxusním lifestyle časopise. NE hard-sell, NE výprodejový leták, NE křiklavé claimy typu „ušetřete 6 000 Kč".
  2. **Moderní editoriální typografie** — čisté nadpisy mixed-case (vyhni se křiklavým VERZÁLKÁM), krátké a úderné (2–3 řádky max), ALE hlavní headline dostatečně výrazný/tučný (semi-bold), nikdy tenký/světlý — musí jasně vystupovat a být čitelný i v náhledu. Hra s kontrastem velikostí/vah jako v designovém časopise. Text na jemných/světlých/průhledných panelech — ne těžké tmavé bloky (nech fotku dýchat). Žádné mini popisky.
  3. **Detail (karta 4)**: ukaž rozložené prvky produktu — komponenty / filtrační stupně jako fyzické objekty kolem produktu (exploded view), ne jen textový seznam.
- Každá karta vyzdvihne JINÝ úhel/benefit — neopakuj stejný headline, claim ani výčet benefitů napříč sadou. 6 karet = 6 různých argumentů (výsledek / nabídka / důvěra / vlastnosti / transformace / identita). Taky žádný sdílený spodní pruh / callout řada / footer opakovaný z jiné karty — podpůrné prvky každé karty jsou unikátní.
- **Vizuálně jiní lidé na každé kartě** — měň věk, pohlaví, vzhled, typ domácnosti; nikdy stejná osoba/rodina napříč sadou (hero drží jen styl, ne lidi).
- **Před→po = přesně 50/50**, produkt jen v POTOM — vertikální split na dvě stejné poloviny (PŘEDTÍM vlevo, POTOM vpravo). Produkt NIKDY na straně PŘEDTÍM (předtím = problém bez produktu; potom = produkt jako řešení).
- **🚫 Nerozsekávat layouty** — každá karta = JEDNA čistá kompozice, NE koláž z 6–7 mini-panelů. Hero a Lifestyle = jedna velká čistá fotka (žádné multi-panel mřížky). Detail smí mít produkt + rozložené komponenty, ale čistě, ne přehlcené panely. Radši míň silných prvků než moc malých.
- **STOP před kredity** — krok 3 (plán) a pilot v kroku 4 jsou povinné. Negeneruj celou sadu naslepo.
- **Žádný ruční shell na validaci/upscale** — používej Python helpery ze `scripts/`.
- **Komunikace s uživatelem** vykáním, česky (klient e-shopu). Generické pojmenování rolí.

## Output
- **Složka**: `/documents/brand/products/<produkt-slug>/carousel/`
- **Soubory**: `🖼01-hero.jpg` … `🖼06-lifestyle.jpg` + `carousel-manifest.json` (+ volitelně `carousel/2000/` po upscale).

## Reference
- `{baseDir}/references/carousel-types.md` — 6 typů: účel, proč funguje, Kenyonovy ověřené prompty 1:1 s placeholdery `{PRODUCT}` + `{BRAND_CONTEXT}`.
- `{baseDir}/references/creative-specs.md` — rozměry, spolehlivé poměry, upscale, quality checklist.
