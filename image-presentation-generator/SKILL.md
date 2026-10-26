---
name: image-presentation-generator
description: Vytvoří plně obrázkovou prezentaci — každý slide (16:9) je prémiový AI obrázek z GPT Image 2.0, takže texty a diakritika sedí přesně a slidy vypadají jako od profi designéra. Pestrá knihovna 49 layoutů + 12 stylů v duchu brandové vizuální knihovny. Výstup je PDF deck. Použij, když uživatel chce „obrázkovou prezentaci", slidy jako obrázky, vizuální deck, nebo prezentaci, kde má jistotu, že text vyjde správně. Pro klasické HTML slidy použij html-presentation-generator.
category: marketing
status: ready
version: 1.0
publishedAt: "2026-06-30"
metadata: {"openclaw":{"requires":{"bins":["python3"]},"emoji":"🖼️"}}
---

# Image Presentation Generator

Generuje **plně vizuální prezentaci** — každý slide je prémiový designovaný 16:9 obrázek vytvořený přes **GPT Image 2.0**. Na rozdíl od HTML slidů (`html-presentation-generator`) nebo video slidů tady **text vychází přesně** — GPT Image 2 zvládá český text s plnou diakritikou — a slidy vypadají jako editorial kompozice od profesionálního designéra.

> **⭐ Důvod existence skillu (PRAVIDLO 0):** každý slide musí mít **reálný vizuální impact — prémiový editoriální design s fotografií, hloubkou, světlem a materiálem**, který by HTML/CSS neudělalo. Pokud slide vypadá jako ploché ikonky + text na jednobarevném pozadí, nemá smysl pálit kredity na image generator — na to stačí `html-presentation-generator`. Detail + litmus test v `references/slide-layouts.md` (Pravidlo 0).

**Klíčové rysy:**
- Vstup z **brandové vizuální knihovny** (`brand-board.png` + `brand-kit/`) — NE z DESIGN.md
- **49 layoutů v 8 rodinách** + **variety engine** → deck je vizuálně pestrý, ne monotónní
- **12 stylů** (Bold Signal, Dark Botanical, Neon Cyber, Swiss Modern, Paper & Ink…) přeložených do GPT Image 2 style directiv
- **16:9 widescreen** (draft 1280×720, final 2560×1440); volitelně 9:16 (stories) / 1:1 (social)
- **3 způsoby generování** (volba v Krok 0.2, vyžaduje schválení): vestavěný nástroj / GPT Image 2 přes OpenRouter / GPT Image 2.0 přes FAL.ai
- **Draft → review → final** workflow s checkpointy proti pálení kreditů
- **Výstup: PDF deck** (16:9), s clickable CTA odkazy

## Kdy použít

Použij, když uživatel chce:
- **Obrázkovou prezentaci** — každý slide jako designovaný obrázek/poster
- Slidy, kde má **jistotu, že text (a diakritika) vyjde správně**
- Vizuální deck v duchu **brandové vizuální knihovny** (brand-board mood)
- Vizualizovat **webinářový skript** jako obrázkové slidy

Pro **kódované HTML slidy** (animace, inline editace, Netlify) použij `html-presentation-generator`. Pro **A4 PDF magnet** použij `image-lead-magnet-generator`.

## Vstup

1. **Téma / obsah** — od uživatele, hrubé poznámky, nebo hotová osnova
2. **Webinářový skript** (Mód B) — výstup `ultimate-webinar` nebo MD se slidy + speaker notes
3. **Brand DNA** — `/documents/brand/brandDNA.md` (esence, hlas → tón a mood)
4. **Brand vizuální knihovna** (POVINNÁ):
   - `/documents/brand/brand-board.png` — moodboard značky (PRIMÁRNÍ vizuální reference)
   - `/documents/brand/brand-kit/` — mockupy (volitelné, doporučené)
5. **Produktové fotografie** — `/documents/brand/products/[produkt]/images/` (volitelné)
6. **Logo** — `/documents/brand/logo.png` (pro cover/CTA slidy)
7. **API klíč podle zvoleného systému** (Krok 0.2) — spravuje se v **Nastavení → Integrace**

---

## Workflow

### Krok 0 (POVINNÝ): Detekce + volba systému + načtení kontextu

#### 0.1 — Detekce režimu a existující prezentace

Režimy:
- **Mód A: Nová prezentace** od nuly → Krok 1
- **Mód B: Z webinářového skriptu** → nejdřív `{baseDir}/references/webinar-script-mode.md`, pak Krok 1
- **Mód C: Vylepšení** existující obrázkové prezentace → načti stav, doplň/regeneruj jen co je potřeba

Pokud `/documents/presentations/[slug]/slide-plan.json` existuje, jsou tu dřívější draft slidy (`_slides/`) nebo finální (`_slides-final/`):

| Co existuje | Pokračuj na |
|-------------|-------------|
| jen `slide-plan.json` | Krok 5 (batch draft) |
| + `_slides/slide-XX.png` | Krok 6 (review) |
| + `_slides-final/` | Krok 8 (compose deck) |
| nic | normálně na 0.2 |

Pokud `slide-plan.json` obsahuje pole `backend` → přeskoč 0.2 (systém už zvolen).

#### 0.2 — Jakým systémem chceš vygenerovat slidy

**🛑 Vyžaduje schválení uživatele. Skill MUSÍ zastavit a vyčkat na výběr — NEPOKRAČOVAT na 0.3 bez explicitní volby + ověření klíče.**

Polož otázku **lidským jazykem** (žádné slovo „backend" navenek):

```
═══════════════════════════════════════════════════════════
  JAKÝM SYSTÉMEM CHCEŠ VYGENEROVAT SLIDY?

  1️⃣  VESTAVĚNÝ NÁSTROJ PRO VYTVÁŘENÍ OBRÁZKŮ — doporučeno
      • Použije GPT Image 2 přes tvoje OpenAI předplatné
      • Funguje, jen pokud máš v integracích připojené OpenAI předplatné

  2️⃣  GPT IMAGE 2 PŘES OPENROUTER
      • Stejný model, účtování přes OpenRouter účet
      • Typický fallback, když nemáš OpenAI předplatné
      • Předpoklad: OPENROUTER_API_KEY v integracích

  3️⃣  GPT IMAGE 2.0 PŘES FAL.AI
      • Přímé napojení na FAL.ai (špička, dev/test)
      • Předpoklad: FAL_KEY v integracích

═══════════════════════════════════════════════════════════

Doporučuju 1️⃣, pokud máš připojené OpenAI předplatné. Bez něj 2️⃣.

Která volba? (1 / 2 / 3)
```

Po výběru: ulož do `slide-plan.json` jako `backend: "openclaw" | "openrouter" | "fal"` a **ověř přístupový klíč** (chybí → STOP, nabídni jinou volbu). Nikdy navenek neříkej „backend" ani „OpenClaw". Detail systémů: `{baseDir}/references/image-generation-backends.md`.

#### 0.3 — Načti brand vizuální knihovnu + Brand DNA

```
1. /documents/brand/brandDNA.md            (esence, hlas → tón + mood)
2. /documents/brand/brand-board.png        (POVINNÝ — vizuální mood)
3. /documents/brand/brand-kit/*.png        (mockupy — volitelné)
4. /documents/brand/logo.png               (cover/CTA slidy)
5. /documents/brand/products/[produkt]/    (productDNA.md + images/ — volitelné)
```

**Pokud `brand-board.png` chybí** → STOP. Skill vyžaduje vizuální moodboard. Doporuč `brand-image-generator` / `brand-dna`.

**NIKDY nepoužívej DESIGN.md** — tento skill pracuje s **vizuální** knihovnou (jako `image-lead-magnet-generator`), ne s design tokeny.

### Krok 1: Sestav Style Directive z brand-board

Z brand-board.png + Brand DNA sestav **JEDNU konzistentní Style Directive**, která jde do KAŽDÉHO slide promptu (barvy, typografický mood, visual language, mood). Šablona a 12 presetů: `{baseDir}/references/style-presets-image.md`. Mood (feeling → visual cue): `{baseDir}/references/mood-mapping.md`.

**Brand-board má přednost** před presetem (řídí barvy/mood). Preset doplní typografický mood a signature prvky, nebo slouží jako fallback bez brand-boardu.

Style Directive se **nikdy nemění mezi slidy** → vizuální konzistence celého decku.

### Krok 2: Naplánuj slidy + layouty (variety engine)

Z obsahu (Mód A) nebo skriptu (Mód B) navrhni sekvenci slidů. Pro každý slide vyber **layout** z `{baseDir}/references/slide-layouts.md` a dodrž **variety engine** (žádné dva sousední slidy stejný layout, rotace napříč rodinami, max ~30 % z jedné rodiny).

Vytvoř `slide-plan.json`:

```json
{
  "title": "Název prezentace",
  "orientation": "widescreen",
  "backend": "openclaw",
  "resolution": { "draft": [1280, 720], "final": [2560, 1440] },
  "style_directive": "...",
  "pages": [
    { "n": 1, "type": "cover", "layout": "cover-cinematic", "family": "uvod-zaver",
      "variety_note": "hero open", "content": { "headline": "…", "subtitle": "…" } },
    { "n": 2, "type": "problem", "layout": "manifesto-statement", "family": "text",
      "variety_note": "po coveru silné prohlášení", "content": { "...": "..." } }
  ]
}
```

(Pole `pages` drží naming kompatibilní se skripty; jsou to slidy.)

**🛑 STOP** — ukaž slide plán (čísla, layouty, rodiny, variety_note) + Style Directive uživateli ke schválení. NEPOKRAČUJ bez „OK".

### Krok 3: Připrav prompty per slide

Pro každý slide vygeneruj GPT Image 2 prompt o 5 částech:

```
═══ [1. STYLE DIRECTIVE] ═══
{kompletní Style Directive z Kroku 1 — konstantní}

═══ [2. FORMÁT] ═══
16:9 widescreen presentation slide, aspect ratio 16:9, crisp screen quality.

═══ [3. LAYOUT] ═══
Layout: {layout_slug}
{popis kompozice z slide-layouts.md}

═══ [4. CONTENT] ═══
Headline (Czech, exact): "{nadpis s plnou diakritikou}"
{podnadpis / body / čísla / labels per layout}

═══ [4b. PRODUCT FIDELITY — POVINNÉ, pokud je na slidu produkt s referenční fotkou] ═══
{vlož snippet PRODUCT FIDELITY z slide-layouts.md — přikazuje reprodukovat PŘESNĚ
produkt z reference, ne vymyslet jiný}

═══ [4c. LOGO SIZING — pokud je na slidu logo] ═══
{vlož snippet LOGO SIZING z slide-layouts.md — logo malé, ~6–10 % šířky, v rohu}

═══ [5. QUALITY + NEGATIVE] ═══
{pravidla vizuální kvality + univerzální negative prompt z slide-layouts.md}
{když je na slidu produkt: přidej i product-specific negative — NO invented product…}
Czech text MUST render with full diacritics: á é í ó ú ů ý č ď ě ň ř š ť ž.
```

**Pravidlo:** kdykoli `slide-plan.json` slide nese `product_slug`+`product_image_filename` nebo `content.product_image_path`, prompt MUSÍ obsahovat blok 4b (PRODUCT FIDELITY) + product-specific negative. Bez nich GPT Image 2 produkt vymyslí.

Ulož do `/documents/presentations/[slug]/_prompts/slide-XX.txt` (číslování slide-01.txt… kvůli skriptu page-XX naming → ulož jako `page-XX.txt`, viz pozn. níže).

> **Naming:** skripty čtou prompty jako `page-XX.txt` a píšou slidy jako `page-XX.png`. Drž tedy soubory promptů jako `_prompts/page-01.txt`. Ve výstupech k uživateli mluv o „slidech".

### Krok 4: Brand reference k promptům

`generate-images.py` připojí automaticky (max 3 per slide) v této prioritě:
1. **Logo** (jen cover/CTA slidy) — malý brand mark
2. **Produktová fotka** (pokud slide má `product_slug`+`product_image_filename` nebo `content.product_image_path`) — **VYSOKÁ PRIORITA**, vejde se vždy do top 3
3. **brand-board.png** (global mood / paleta)
4. layout-specific kit / 08-inspirace (jen pokud zbývá místo)

**Produktová fotka je výjimka z „language guidance":** brand-board a kit jsou jen vodítka (barvy, mood, kompozice) — výsledek nesmí být jejich kopie. Ale produktová fotka je **vzor k věrné reprodukci** — produkt na slidu musí odpovídat reálnému produktu z fotky (viz blok 4b PRODUCT FIDELITY v Kroku 3). Pokud produkt vyjde vymyšlený, je to chyba k regeneraci.

### Krok 5: Batch generuj draft všech slidů

```bash
BACKEND=$(python3 -c "import json; print(json.load(open('/documents/presentations/[slug]/slide-plan.json'))['backend'])")

python3 "{baseDir}/scripts/generate-images.py" \
  --plan "/documents/presentations/[slug]/slide-plan.json" \
  --prompts-dir "/documents/presentations/[slug]/_prompts/" \
  --references-dir "/documents/brand/" \
  --output-dir "/documents/presentations/[slug]/_slides/" \
  --resolution draft \
  --backend "$BACKEND"
```

### Krok 6: Review draftů + selektivní regenerace

**🛑 Vyžaduje schválení uživatele. NEPOKRAČUJ na final, dokud uživatel neřekne „OK, schvaluji".**

```bash
python3 "{baseDir}/scripts/build-review.py" \
  --pages-dir "/documents/presentations/[slug]/_slides/" \
  --output "/documents/presentations/[slug]/_review.html" \
  --plan "/documents/presentations/[slug]/slide-plan.json"
```

Otevři `_review.html`. Uživatel označí slidy k regeneraci s komentářem (text nečitelný / špatný layout / barvy…). Uprav prompt(y) → regeneruj jen ty s `--only "3,7,12"` → aktualizuj review. Opakuj do spokojenosti.

Pokud text vychází chybně: `{baseDir}/references/text-overlay-fallback.md` (re-prompt → Pillow overlay).

### Krok 7: Finální generace (2560×1440)

Po schválení:

```bash
python3 "{baseDir}/scripts/generate-images.py" \
  ... --resolution final \
  ... --output-dir "/documents/presentations/[slug]/_slides-final/"
```

### Krok 8: Compose PDF deck

```bash
python3 "{baseDir}/scripts/compose-deck.py" \
  --pages-dir "/documents/presentations/[slug]/_slides-final/" \
  --output "/documents/presentations/[slug]/prezentace.pdf" \
  --plan "/documents/presentations/[slug]/slide-plan.json" \
  --orientation widescreen \
  --title "{Název}" \
  --author "{Autor}"
```

### Krok 9: Output

Vždy uveď absolutní cestu k PDF a otevři ho:

```
✅ Obrázková prezentace: /documents/presentations/[slug]/prezentace.pdf
   Slidů: XX • 16:9 • velikost XX MB
```

---

## Output struktura

```
/documents/presentations/[slug]/
├── slide-plan.json          # plán slidů + layouty + style directive + backend
├── _prompts/
│   ├── page-01.txt          # GPT Image 2 prompt per slide
│   └── ...
├── _slides/                 # draft (1280×720)
│   └── page-XX.png
├── _slides-final/           # final (2560×1440)
│   └── page-XX.png
├── _review.html             # batch review grid
└── prezentace.pdf           # FINÁLNÍ VÝSTUP
```

## Pravidla kvality (shrnutí — detail v slide-layouts.md)

- **⭐ PRAVIDLO 0 — vizuální impact:** každý slide = bohatá editoriální kompozice (fotografie, hloubka, světlo, materiál), kterou by HTML neudělalo. Litmus test: „vypadal by stejně v HTML? → pak přidej vizuální bohatost." Bez tohohle nemá image generator smysl.
- **Jeden vizuální důraz na slide**, BIG BOLD headline, 3úrovňová hierarchie, 20–30 % whitespace
- **Premium editorial feel** — NE PowerPoint na ploché barvě, NE stock-photo, NE AI slop
- **Style Directive konstantní** napříč deckem; **layouty se střídají** (variety engine)
- **Český text s plnou diakritikou**, max ~40–50 slov/slide
- **Vykání** ve výstupech pro klienta; terminologie dle CliqSales pravidel (AI Data Center, generické role)
- **Checkpoint proti pálení kreditů**: draft → STOP review → final

## Reference

| Soubor | Kdy číst |
|--------|----------|
| `{baseDir}/references/style-presets-image.md` | Krok 1 (Style Directive, 12 presetů) |
| `{baseDir}/references/mood-mapping.md` | Krok 1 (feeling → visual cue) |
| `{baseDir}/references/slide-layouts.md` | Krok 2 + 3 (49 layoutů, variety engine, kvalita, negative prompts) |
| `{baseDir}/references/webinar-script-mode.md` | Mód B (z webinářového skriptu) |
| `{baseDir}/references/image-generation-backends.md` | Krok 0.2 + 5 (3 systémy, endpointy) |
| `{baseDir}/references/text-overlay-fallback.md` | Krok 6 (chybný text) |
| `{baseDir}/scripts/generate-images.py` | Krok 5 + 7 (batch generování) |
| `{baseDir}/scripts/build-review.py` | Krok 6 (review grid) |
| `{baseDir}/scripts/compose-deck.py` | Krok 8 (PDF deck) |
