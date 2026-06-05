---
name: HTML prezentace
description: "Vytváří animované HTML prezentace od nuly nebo z webinářového skriptu bez build závislostí, s 12 vizuálními tématy, integrací DESIGN.md a důrazem na negenerický design."
metadata: {"openclaw":{"homepage":"https://github.com/zarazhangrui/frontend-slides","emoji":"🎨"}}
category: content
status: ready
version: "1.0"
publishedAt: "2026-05-02"
---


# HTML Prezentace

Vytváří zero-dependency, animačně bohaté HTML prezentace, které běží přímo v prohlížeči. Žádný npm, žádné build tools. Výstup = složka s `index.html` + `images/`, ready pro Netlify Drop.

## Kdy použít

Když uživatel chce: vytvořit prezentaci, slidy, deck, pitch deck, vylepšit existující HTML prezentaci, exportovat slidy do PDF, nebo vizualizovat webinářový skript jako HTML slidy.

## Základní principy

1. **Zero Dependencies** — HTML s inline CSS/JS + složka `images/`.
2. **Show, Don't Tell** — Generuj vizuální preview, ne abstraktní volby.
3. **Distinctive Design** — Žádný generický "AI slop". Každá prezentace musí vypadat custom.
4. **Viewport Fitting** — Každý slide MUSÍ být přesně `100vh`. Žádné scrollování.

---

## POVINNÁ MAPA: PŘED → ČTI X

Při tvorbě prezentace MUSÍŠ načíst odpovídající referenční soubory **DŘÍV** než začneš psát kód. Improvizace = produkce nekonzistentních výstupů.

| Před krokem… | POVINNĚ načti |
|---|---|
| Před výběrem stylu / barev / typografie | `references/style-presets.md` |
| Před psaním JS pro slide navigaci, nav-dots, badge, card, CTA, brand mark | `references/components.md` |
| Před stylováním nadpisů, layoutu, obrázků (hero/split/lidé), kontrastu, hierarchie | `references/visual-rules.md` |
| Před aplikací animací (reveal, card-reveal, line-reveal, keyframes) | `references/animation-patterns.md` |
| Před vložením HTML kostry | `references/html-template.md` |
| Před vložením base CSS | `references/viewport-base.css` (vlož CELÝ obsah do `<style>`) |
| Před výběrem ikony | `references/icons.md` |

**NIKDY neimprovizuj komponenty** — vždy nejdřív přečti reference. Když zapomeneš, výstup bude nekonzistentní s ostatními prezentacemi.

---

## Viewport Fitting Rules (NON-NEGOTIABLE)

Tyto invarianty platí pro KAŽDÝ slide v KAŽDÉ prezentaci. Nikdy neporušuj:

```css
html { scroll-snap-type: y mandatory; scroll-behavior: smooth; }
.slide {
  width: 100vw;
  height: 100vh; height: 100dvh;
  overflow: hidden;              /* KRITICKÉ — žádný overflow */
  scroll-snap-align: start;
}
```

- **Všechny font-size a spacing v `clamp(min, preferred, max)`** — nikdy fixní px/rem.
- **Obrázky:** `max-height: min(50vh, 400px)`.
- **Breakpointy pro výšku:** 700px, 600px, 500px.
- **`prefers-reduced-motion` podpora** je POVINNÁ (viz `animation-patterns.md`).
- **CSS gotcha:** `-clamp(...)` je tiše ignorováno. Vždy `calc(-1 * clamp(...))`.

---

## WORKFLOW

### Fáze 0: Detekce režimu a brand kontextu

**Režim:**
- **A: Nová prezentace** — od nuly → Fáze 1.
- **B: Z webinářového skriptu** — vstup od `ultimate-webinar` skillu → Fáze 4.
- **C: Vylepšení** — existující HTML → načti, pochop, vylepši (zkontroluj density limity v `visual-rules.md`).

**Brand kontext (POVINNÝ KROK):**
1. **Brand DNA** — přečti `/documents/brand/brandDNA.md` (esence, hlas, USP).
2. **Product DNA** — přečti `/documents/brand/productDNA.md` pokud existuje.
3. **Produktové fotografie** — projdi `/documents/brand/products/[nazev]/images/`.
4. **DESIGN.md** — přečti `/documents/brand/DESIGN.md` a extrahuj design tokeny (barvy, typografie, spacing, komponenty). Mapuj 1:1 na CSS proměnné v `:root`.

**Priorita zdrojů:**
1. DESIGN.md = vizuální specifikace (závazné).
2. Brand DNA = hlas a tón (ovlivní copy).
3. Style preset (Fáze 2) = fallback pokud chybí brand kontext.

Pokud chybí oboje → pokračuj do Fáze 2 a zeptej se na brand identitu.

### Fáze 1: Zjištění obsahu (pro režim A)

Zeptej se uživatele najednou:
1. **Účel** — Pitch deck / Tutorial / Konferenční talk / Interní.
2. **Délka** — Krátká (5–10) / Střední (10–20) / Dlouhá (20+).
3. **Obsah** — Vše připraveno / Hrubé poznámky / Jen téma.
4. **Inline editace** — Ano (editovatelný text v prohlížeči) / Ne.

**Získání obrázků:**
- **A. Lokální** — z `/documents/brand/products/.../images/` nebo upload.
- **B. Z URL** — `browser open` + `browser snapshot` pro analýzu, `web_fetch` pro download do `images/`. Potvrď výběr.
- **C. Žádné** — CSS-only vizuály (gradienty, tvary). Plně podporováno.

### Fáze 2: Style discovery

**Pokud existuje DESIGN.md:** přeskoč preset, použij tokeny. Generuj 1 preview pro potvrzení.

**Pokud žádný brand kontext:**
- "Ukaž mi možnosti" → 3 single-slide HTML preview, otevři v browseru přes `exec open style-a.html`.
- "Vím co chci" → ukaž presety přímo z `references/style-presets.md`.

**Mood → preset mapping:**
- Impressed/Confident → Bold Signal, Electric Studio, Dark Botanical.
- Excited/Energized → Creative Voltage, Neon Cyber, Split Pastel.
- Calm/Focused → Notebook Tabs, Paper & Ink, Swiss Modern.
- Inspired/Moved → Dark Botanical, Vintage Editorial, Pastel Geometry.

### Fáze 3: Generování prezentace

**Před generováním načti:** `html-template.md`, `viewport-base.css`, `components.md`, `visual-rules.md`, `animation-patterns.md`.

**Výstupní struktura (Netlify Drop ready):**
```
/documents/presentations/nazev-prezentace/
├── index.html              # CSS/JS inline
└── images/                 # obrázky (pokud jsou)
```

**Verzování:** existuje-li složka, použij suffix (`-v2`, `-v3`). Nikdy nepřepisuj bez souhlasu.

**Požadavky:**
- HTML s veškerým CSS/JS inline.
- Obrázky vždy relativní cestou: `src="images/photo.jpg"`.
- Vlož CELÝ `viewport-base.css` do `<style>` bloku.
- Fonty z Fontshare nebo Google Fonts — nikdy systémové (pokud uživatel neřekne jinak).
- Komentáře `/* === SECTION NAME === */`.
- Pokud je DESIGN.md: `:root` mapuj 1:1 na tokeny.

### Fáze 4: Z webinářového skriptu

Pokud vstup pochází z `ultimate-webinar` nebo dodaného Markdown skriptu:

1. **Parsuj skript:**
   - Nadpisy `## SLIDE X — Nadpis`.
   - Obsah z `**Na slidu:**`.
   - Speaker notes z `**Poznámky pro speakera:**` → HTML komentář `<!-- Speaker: ... -->`.

2. **Mapuj typy slidů:**
   - Title → title-slide layout, velký nadpis.
   - Cold open / Hook → dramatický layout s číslem nebo otázkou.
   - Kontrasty → split layout nebo grid.
   - Case study → card layout s čísly.
   - Stack položky → list s narůstající hodnotou.
   - CTA → accent barva, velké tlačítko (viz `components.md`).
   - Section divider → full-bleed slide s názvem sekce.
   - Deprivace → tmavší pozadí, dramatický kontrast.

3. **Zachovej strukturu** — pořadí slidů, fáze, tajemství.
4. **Pokračuj na Fázi 2** (style) a Fázi 3 (generation).

### Fáze 5: Doručení

Ulož vše do `/documents/presentations/nazev-prezentace/`. Ověř `index.html` + případně `images/`.

### Fáze 6: Export do PDF (volitelné)

Nabídni po doručení. Používá nativní `browser` tool, žádné externí dependencies.

1. Otevři: `browser open "file:///documents/presentations/nazev-prezentace/index.html"`.
2. Pro každý slide: naviguj → 500ms wait → `browser screenshot` → uloží `slide-001.png`...
3. Sloč do PDF:
   ```
   exec python3 -c "
   import img2pdf, glob, os
   imgs = sorted(glob.glob('slide-*.png'))
   with open('prezentace.pdf', 'wb') as f:
       f.write(img2pdf.convert(imgs))
   for i in imgs: os.remove(i)
   "
   ```
4. Pokud chybí dependency: `exec pip install img2pdf`.

Animace nejsou zachovány — statický snapshot. Sděl uživateli předem.

---

## Referenční soubory

| Soubor | Obsah | Načti když |
|---|---|---|
| `references/components.md` | SlidePresentation JS, nav-dots, badge, cards, CTA, brand mark, progress bar, dividers | Píšeš JS nebo stylzuješ jakoukoliv komponentu |
| `references/visual-rules.md` | Typografie, layout, obrázky (hero/split/lidé), kontrast, hierarchie, density limity | Designuješ jakýkoliv slide |
| `references/animation-patterns.md` | Reveal classes, staggered delays, keyframes, prefers-reduced-motion, mood-effect mapping | Animuješ vstup elementů |
| `references/html-template.md` | HTML kostra prezentace | Začínáš novou prezentaci |
| `references/viewport-base.css` | Base CSS + breakpointy + reset | Vždy vlož CELÝ obsah do `<style>` |
| `references/style-presets.md` | 12 vizuálních témat s ukázkovými barvami a typografií | Style discovery (Fáze 2) |
| `references/icons.md` | 35+ inline SVG ikon v 8 kategoriích | Vkládáš ikonu do badge, karty, gridu |

---

## Iterace a vylepšování

Když uživatel chce upravit jednotlivé slidy po prvním výstupu:

- Zachovej konzistentní styl s ostatními slidy.
- Při úpravě jednoho slidu **NIKDY neměň ostatní**.
- Pokud uživatel řekne „lepší copywriting" → kontrasty, čísla, řečnické otázky, kratší věty.
- Pokud chce sloučit slidy → zachovej všechny klíčové body, zhustí.
- Pokud chce jiný nadpis → nabídni 5–10 variant.
- Pokud chce jiný koncept → nabídni 10 variant konceptu (ne celý slide).

**Bez dodržení vizuálních pravidel a kompoznentních specifikací je prezentace NEAKCEPTOVATELNÁ.** Vždy ověř před doručením, že slidy splňují invarianty z `visual-rules.md` a komponenty z `components.md`.
