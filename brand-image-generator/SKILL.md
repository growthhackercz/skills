---
name: brand-image-generator
description: Generuje originální vizuály věrné designovému jazyku značky z Brand DNA, Product DNA, brand boardu a brand kitu.
category: creative
status: ready
version: "1.0"
publishedAt: "2026-05-02"
metadata: {"openclaw":{"emoji":"🖼️","homepage":"https://docs.openclaw.ai/tools/skills"}}
---

# Brand Image Generator

Vytváří zcela nové, originální vizuály na zakázku — věrné designovému jazyku značky. Neopakuje existující materiály, nekopíruje reference. Místo toho analyzuje estetické principy z Brand DNA, Product DNA, brand boardu a brand kitu a aplikuje je na nový vizuál požadovaný uživatelem.

## Kdy použít

Když uživatel chce vygenerovat nový obrázek pro značku — banner, pozadí, social post, hero obrázek, thumbnail, produktový vizuál, reklamní grafiku, nebo jakýkoli jiný vizuální asset. Také když řekne "brand image", "obrázek pro značku", "vizuál", "grafika", "kreativa", "vygeneruj obrázek", "brand creative".

## Předpoklady — zdroje značky

Skill pracuje s těmito soubory ve složce `/documents/brand/`:

**Povinné:**
- **brandDNA.md** — Brand DNA report (esence, barvy, typografie, emoční tón, vizuální styl)
- **brand-board.png** — Brand Board moodboard

**Volitelné (ale silně doporučené):**
- **productDNA.md** — Product DNA report (popis produktu/služby, benefity, USP, cílová skupina produktu)
- **brand-kit/** — složka s vygenerovanými brand kit mockupy (01–24)
- **products/** — složka s produkty. Každý produkt má vlastní podsložku s obrázky:
  ```
  products/
  ├── bioptron-medall/
  │   └── images/        ← fotky produktu (max 5)
  ├── therapy-air-ion/
  │   └── images/        ← fotky produktu (max 5)
  └── [další-produkt]/
      └── images/
  ```
- **logo.png** / **logo.jpg** / **logo.webp** — logo (NEPOUŽÍVÁ SE ve vizuálu, ale pomáhá pochopit vizuální jazyk)

Pokud brandDNA.md nebo brand-board.png chybí, informuj uživatele a požádej o doplnění. Ostatní zdroje jsou volitelné — skill pracuje s tím co má.

## Workflow

### Krok 1: Načti kontext značky

**Brand DNA** — přečti `/documents/brand/brandDNA.md` a extrahuj:

Ze sekce 1 — ESENCE ZNAČKY:
- Název značky, Kategorie, Slogan, USP, Emoční tón

Ze sekce 6 — VIZUÁLNÍ IDENTITA:
- Barevná paleta s HEX kódy (primární, sekundární, akcenty)
- Typografie (heading + body fonty)
- Vizuální styl, Styl fotografií, Textury a vzory, Ikonografie

Ze sekce 7 — SHRNUTÍ BRAND DNA:
- Celkový pocit ze značky

**Product DNA** — pokud existuje `/documents/brand/productDNA.md`, přečti a extrahuj:
- Název produktu/služby
- Co produkt dělá a pro koho
- Klíčové benefity a diferenciátory
- Vizuální asociace spojené s produktem

**Produktové fotografie** — pokud existuje `/documents/brand/products/`, projdi podsložky produktů. Každý produkt má strukturu `products/[nazev-produktu]/images/`. Pokud uživatel specifikuje konkrétní produkt, načti obrázky z jeho podsložky (max 5). Pokud nespecifikuje, zeptej se kterého produktu se vizuál týká. Dostupné produkty zjistíš výpisem podsložek v `products/`.

### Krok 2: Načti vizuální reference

**Brand Board** — načti `/documents/brand/brand-board.png` jako primární vizuální referenci designového jazyka.

**Brand Kit reference** — na základě toho co uživatel chce vytvořit, vyber nejrelevantnější soubor z `/documents/brand/brand-kit/`. Mapování viz `{baseDir}/references/kit-mapping.md`. Pokud složka brand-kit neexistuje nebo je prázdná, pokračuj jen s brand boardem.

**DŮLEŽITÉ:** Brand board i brand kit soubory slouží VÝHRADNĚ jako reference designového jazyka — NE jako vizuální předloha ke kopírování.

### Krok 3: Zjisti co uživatel chce

Pokud uživatel nespecifikoval co přesně chce vytvořit, zeptej se:

- **Co:** Jaký typ vizuálu? (banner, pozadí, social post, hero obrázek, thumbnail, produktový vizuál, reklamní grafika, abstraktní vizuál…)
- **Rozměr:** Jaký poměr stran? (1:1 social feed, 4:5 Instagram, 16:9 web/YouTube, 9:16 stories, 2:3 vertikální — default 2:3)
- **Mód:** Jeden obrázek, nebo grid 4×4 pro výběr? (default: single)

Pokud uživatel rovnou specifikoval vše, přeskoč na Krok 4.

### Krok 4: Analýza estetických principů (FÁZE 1)

Z načtených vizuálních referencí (brand board + brand kit soubor) interně identifikuj:

- **Barevnou paletu** — aplikuj přímo do vizuálu, NEZOBRAZUJ swatche
- **Typografický styl** — font, váhy, hierarchie (ale text pouze pokud ho uživatel výslovně chce)
- **Práci s liniemi, tvary, ořezy fotek** — geometrie, zaoblení, ostrost
- **Vrstvy, překryvy, kompoziční techniky** — gradienty, průhlednosti, hloubka
- **Celkový tón** — prémiový/hravý/minimalistický/organický/technologický…

### Krok 5: Filtruj co NEPOUŽÍVAT (FÁZE 2)

Striktně ignoruj z referencí:
- Fotografie, obličeje, osoby, scény — pokud uživatel nespecifikuje že je chce
- Ikony, ilustrace, mockupy, layouty z referencí
- Texty, slogany, HEX kódy, swatche
- Konkrétní kompozice a rozvržení z referencí

Výjimky:
- Pokud uživatel řekne "chci vizuál s produktem" → použij produktové fotografie z `/documents/brand/products/`
- Pokud uživatel řekne "chci vizuál s lidmi/osobou" → vygeneruj nové osoby ve stylu značky

### Krok 6: Sestav prompt a generuj (FÁZE 3)

Sestav prompt pro `image_generate` který kombinuje:

1. **Co vytvořit** — typ vizuálu dle požadavku uživatele
2. **Estetické principy** — extrahované v Kroku 4
3. **Kontext značky** — název, obor, emoční tón z Brand DNA
4. **Kontext produktu** — pokud je relevantní a productDNA existuje
5. **Rozměr** — poměr stran dle výběru uživatele

**SINGLE MÓD** (default):
- Vygeneruj jeden obrázek od kraje ke kraji
- Uložit jako `/documents/brand/visuals/[popisny-nazev].png`

**GRID MÓD** (když uživatel řekne "grid", "varianty", "výběr"):
- Vygeneruj JEDEN obrázek obsahující grid 4×4 (16 menších obrázků)
- Každý obrázek v gridu očísluj od 1 do 16 — bílý malý kruh vlevo nahoře s číslem
- Uložit jako `/documents/brand/visuals/grid-[popisny-nazev].png`
- Po zobrazení se zeptej: "Vyber čísla, která se ti líbí — vygeneruju je ve velkém."
- Vybraná čísla vygeneruj jako samostatné full-size obrázky

Přilož ke každému `image_generate` volání:
- Brand board jako vizuální referenci
- Relevantní brand kit soubor (pokud existuje)
- Produktové fotografie (pokud existují a jsou relevantní)

Když je lokální reference uložená pod `/documents/...`, předej ji `image_generate` přes runtime cestu `/home/node/documents/...` (např. `/home/node/documents/brand/brand-board.png`). Výstupy dál ukládej do `/documents/...`.

### Krok 7: Ulož a nabídni iteraci

Zobraz výsledek uživateli a zeptej se:

- "Spokojený? Nebo chceš úpravu?"
- Příklady úprav: "tmavší", "světlejší", "více minimalistické", "přidej texturu", "jiný styl", "více produktový", "abstraktnější"

Pokud uživatel chce změnu, uprav prompt a přegeneruj. Při iteraci zachovej kontext značky a přidej feedback jako instrukci.

Pokud uživatel po gridu vybere čísla, vygeneruj je jako samostatné obrázky v plném rozlišení.

## Pravidla

- **Žádné kopírování** — výstup musí být zcela nová, originální kompozice. Reference slouží jen pro pochopení designového jazyka.
- **Žádná koláž** — výstup je vždy jeden celistvý obrázek od kraje ke kraji (kromě grid módu).
- **Žádné logo** — výstup NIKDY neobsahuje logo značky, pokud uživatel výslovně neřekne jinak.
- **Žádné swatche/HEX** — barvy se aplikují, nezobrazují se jako vzorníky.
- **Čeština** — veškerá komunikace s uživatelem česky. Text na vizuálu pouze pokud ho uživatel chce.
- **Brand DNA je zdroj pravdy** — vizuální styl vychází z Brand DNA a vizuálních referencí.
- **Product DNA obohacuje** — pokud existuje, přidává kontext o produktu/službě do generování.
- **Kvalita** — výstup musí působit jako práce designéra znalého značky, ne jako generický AI obrázek.

## Output

Složka: `/documents/brand/visuals/`

Pojmenování: `[popisny-nazev].png` (např. `hero-pozadi-tmave.png`, `instagram-post-produkt.png`, `grid-bannery-variace.png`)

## Reference

Mapování typ výstupu → brand kit reference: `{baseDir}/references/kit-mapping.md`
