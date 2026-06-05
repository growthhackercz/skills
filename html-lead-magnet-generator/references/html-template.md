# HTML Template — A4 Lead Magnet

Kompletní HTML šablona pro lead magnet PDF. Statický HTML, **žádný JS, žádné animace**. Používá CSS proměnné z `:root` namapované z DESIGN.md nebo style presetu.

Všechny page layouty z `page-layouts.md` jsou kompatibilní s touto šablonou.

---

## Struktura souboru

```html
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <title>{{TITLE}}</title>
  {{FONT_LINKS}}
  <style>
    /* === ROOT VARIABLES (z DESIGN.md nebo presetu) === */
    :root {
      {{ROOT_VARIABLES}}
    }

    {{BASE_RESET_AND_PRINT_CSS}}

    {{PAGE_LAYOUT_CSS}}
  </style>
</head>
<body>
  {{PAGES}}
</body>
</html>
```

Placeholdery se nahradí v `render-pdf.py` při sestavování.

---

## Base reset + print CSS

```css
/* === RESET === */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

/* === PRINT PAGE SETUP === */
@page {
  size: A4;
  margin: 0;
}

@page:first {
  margin: 0;
}

@media print {
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
  }
}

html, body {
  font-family: var(--font-body);
  font-size: var(--fs-body);
  line-height: var(--lh-normal);
  color: var(--color-text);
  background: var(--color-bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* === UNIVERZÁLNÍ PAGE === */
.page {
  width: 210mm;
  height: 297mm;
  padding: var(--space-12) var(--space-8);
  page-break-after: always;
  break-after: page;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.page:last-child {
  page-break-after: auto;
  break-after: auto;
}

/* === PAGE NUMBERING (volitelné, footer) === */
.page-footer {
  position: absolute;
  bottom: var(--space-4);
  left: 0;
  right: 0;
  text-align: center;
  font-size: var(--fs-small);
  color: var(--color-text-muted);
}

.page-footer .num {
  font-variant-numeric: tabular-nums;
}

/* === ORPHAN/WIDOW CONTROL === */
p, li {
  orphans: 3;
  widows: 3;
}

/* === PAGE BREAK PRAVIDLA === */
h1, h2, h3 {
  page-break-after: avoid;
  break-after: avoid;
}

.feature-card,
.cta-stack,
.audit-question,
.mf-pair,
.quote-text,
.checklist-list li {
  page-break-inside: avoid;
  break-inside: avoid;
}

/* === LINKS === */
a {
  color: var(--color-accent);
  text-decoration: underline;
  text-underline-offset: 2pt;
}

/* === IMAGES === */
img {
  max-width: 100%;
  height: auto;
  display: block;
}

/* === SVG IKONY === */
svg {
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* === TYPOGRAFIE — defaultní velikosti per heading level === */
h1 {
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  line-height: var(--lh-tight);
  font-weight: var(--fw-bold);
  letter-spacing: var(--ls-display);
  color: var(--color-primary);
}

h2 {
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  line-height: var(--lh-tight);
  font-weight: var(--fw-semibold);
  color: var(--color-primary);
}

h3 {
  font-size: var(--fs-h3);
  line-height: 1.3;
  font-weight: var(--fw-medium);
  color: var(--color-primary);
}

p {
  font-size: var(--fs-body);
  line-height: var(--lh-normal);
}

ul, ol {
  font-size: var(--fs-body);
  line-height: var(--lh-normal);
}

strong, b {
  font-weight: var(--fw-semibold);
}

em, i {
  font-style: italic;
}

/* === KÓDOVÉ BLOKY (volitelné) === */
code {
  font-family: var(--font-mono);
  font-size: 0.9em;
  background: var(--color-bg-subtle);
  padding: 2pt 4pt;
  border-radius: var(--radius-sm);
}

pre {
  font-family: var(--font-mono);
  background: var(--color-bg-subtle);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: var(--space-4) 0;
  page-break-inside: avoid;
}
```

---

## Page Layout CSS

CSS pro každý ze 11 layoutů z `page-layouts.md`. Vlož všechny do šablony, layouty se aktivují přes class na `.page` elementu (`.page--cover`, `.page--chapter-opener`, atd.).

Plný CSS kód každého layoutu je v `page-layouts.md` u každého layoutu.

V šabloně se vkládají všechny najednou — skill si vybere který layout použít přes class.

```css
/* === COVER === */
.page--cover { /* viz page-layouts.md sekce 1 */ }
.cover-header { ... }
.cover-title { ... }
.cover-subtitle { ... }
.cover-footer { ... }

/* === HERO COVER === */
.cover--hero { ... }
.cover-overlay { ... }

/* === TOC === */
.page--toc { ... }
.toc-title { ... }
.toc-list { ... }
.toc-item { ... }

/* === CHAPTER OPENER === */
.page--chapter-opener { ... }
.chapter-frame { ... }
.chapter-num { ... }
.chapter-title { ... }
.chapter-tease { ... }
.chapter-quote { ... }

/* === CONTENT === */
.page--content { ... }
.content-header { ... }
.content-h2 { ... }
.content-lead { ... }
.content-bullets { ... }
.bullet-icon { ... }
.content-aha { ... }

/* === FEATURE GRID === */
.page--feature-grid { ... }
.grid-3 { ... }
.feature-card { ... }
.feature-icon { ... }
.feature-tag { ... }

/* === MYTH-FACT === */
.page--myth-fact { ... }
.mf-pair { ... }
.mf-myth { ... }
.mf-fact { ... }
.mf-icon { ... }
.mf-label { ... }

/* === QUOTE === */
.page--quote { ... }
.quote-mark { ... }
.quote-text { ... }
.quote-author { ... }

/* === CHECKLIST === */
.page--checklist { ... }
.checklist-header { ... }
.checklist-list { ... }
.checklist-day { ... }
.checklist-tip { ... }

/* === AUDIT === */
.page--audit { ... }
.audit-header { ... }
.audit-question { ... }
.audit-num { ... }
.audit-options { ... }
.audit-radio { ... }

/* === CTA === */
.page--cta { ... }
.cta-eyebrow { ... }
.cta-title { ... }
.cta-stack { ... }
.cta-item { ... }
.cta-button { ... }
.cta-meta { ... }

/* === COMPARISON === */
.page--comparison { ... }
.comp-table { ... }
.comp-good { ... }
```

---

## Příklad sestaveného HTML (cover + 1 content + cta)

```html
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <title>Money Identity Audit</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@700&display=block" rel="stylesheet">

  <style>
    :root {
      --color-primary: #1a1a1a;
      --color-secondary: #f7f5f0;
      --color-accent: #b8856a;
      --color-text: #1a1a1a;
      --color-text-muted: #6b6357;
      --color-bg: #ffffff;
      --color-bg-subtle: #f7f5f0;
      --color-success: #4a7c59;
      --color-error: #a04545;
      --color-border: #e0dccf;

      --font-display: "Playfair Display", Georgia, serif;
      --font-body: "Inter", -apple-system, system-ui, sans-serif;

      --fs-display: 56pt;
      --fs-h1: 32pt;
      --fs-h2: 22pt;
      --fs-h3: 14pt;
      --fs-body: 11pt;
      --fs-small: 9pt;

      --lh-tight: 1.05;
      --lh-normal: 1.55;
      --ls-display: -0.015em;

      --fw-normal: 400;
      --fw-medium: 500;
      --fw-semibold: 600;
      --fw-bold: 700;

      --space-1: 4pt;
      --space-2: 8pt;
      --space-3: 12pt;
      --space-4: 16pt;
      --space-5: 20pt;
      --space-6: 24pt;
      --space-8: 32pt;
      --space-12: 48pt;
      --space-16: 64pt;

      --radius-sm: 4pt;
      --radius-md: 8pt;
      --radius-lg: 16pt;
      --radius-full: 9999pt;
    }

    /* [Base reset + print CSS] */
    /* [Všechny page layouts CSS] */
  </style>
</head>
<body>

  <!-- COVER -->
  <section class="page page--cover cover--text">
    <header class="cover-header">
      <span class="cover-badge">Magnet zdarma</span>
      <span class="cover-brand">Money Reset</span>
    </header>
    <div class="cover-main">
      <h1 class="cover-title">Money Identity Audit</h1>
      <p class="cover-subtitle">Zjisti, který ze 4 peněžních typů jsi (a co tě stojí každý měsíc)</p>
    </div>
    <footer class="cover-footer">
      <p class="cover-author">Petra Nováková · certifikovaná financial coach</p>
      <p class="cover-meta">15 minut čtení · 10 stran</p>
    </footer>
  </section>

  <!-- CONTENT (kapitola 1, podsekce s bullety) -->
  <section class="page page--content">
    <header class="content-header">
      Kapitola 1 · Peněžní programy z dětství
    </header>
    <h2 class="content-h2">Tvoje první peněžní pravda</h2>
    <p class="content-lead">
      78% peněžních rozhodnutí běží automaticky — z programů, které sis nevybrala.
      Tahle kapitola ti dá nástroj, jak je vidět.
    </p>
    <ul class="content-bullets">
      <li>
        <span class="bullet-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </span>
        <div>
          <strong>"Na to nemáme."</strong>
          <p>Zapsáno jako "buďte opatrní s penězi". Kontrolovalo to tvoje rozhodnutí o paušálu, dovolené, vybavení.</p>
        </div>
      </li>
    </ul>
    <p class="content-aha">
      <strong>Aha moment:</strong> Dospělost není opatrnost — je to schopnost zvolit, kdy je opatrnost správně.
    </p>
  </section>

  <!-- CTA -->
  <section class="page page--cta">
    <div class="cta-content">
      <span class="cta-eyebrow">Co teď dál?</span>
      <h2 class="cta-title">Tvůj audit ti dal diagnostiku.<br>Money Reset ti dá systém.</h2>
      <!-- ... cta-stack, cta-button atd. ... -->
    </div>
  </section>

</body>
</html>
```

---

## Webfonty — preload pro print

V `<head>` šablony detekuj fonty z DESIGN.md / presetu a přidej Google Fonts link:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@700&display=block" rel="stylesheet">
```

`display=block` zabrání FOIT/FOUT v PDF.

V Playwright počkej na fonty před PDF:

```python
await page.evaluate("document.fonts.ready")
await page.wait_for_load_state("networkidle")
```

---

## Custom HTML komponenty (volitelné rozšíření)

Pokud markdown obsahuje speciální syntax, parser v `render-pdf.py` ho převede na HTML komponenty:

| Markdown | HTML |
|----------|------|
| `> [!myth-fact]` blok | `<div class="page--myth-fact">...</div>` |
| `> [!feature-grid]` blok | `<section class="grid-3">...</section>` |
| `> [!quote] ... — autor` | `<section class="page page--quote">...</section>` |
| `> [!checklist]` blok | `<section class="page page--checklist">...</section>` |
| `> [!cta]` blok | `<section class="page page--cta">...</section>` |
| `> [!audit]` blok | `<section class="page page--audit">...</section>` |

Toto je volitelné — pokud markdown použije obyčejné headings a bullety, parser je sám rozpozná dle struktury (algoritmus z SKILL.md Krok 3).

---

## Edge cases

### Cover bez hero image

Pokud `cover.png` neexistuje, použij `cover--text` variantu (full-text cover na primary background).

### Příliš dlouhý nadpis na cover

Pokud title má >80 znaků, skill automaticky zmenší `cover-title` font-size na `clamp(28pt, 5vw, 48pt)`.

### Žádné kapitoly v markdownu

Pokud markdown nemá `# Kapitola N` headings (např. plochý checklist), vynech `chapter-opener` layouty a TOC. Použij Cover → Content → CTA.

### DESIGN.md má dark theme jako primární

Lead magnet PDF je **vždy light mode** (print). Pokud DESIGN.md má dark theme, použij `colors.bg = #ffffff` a invertuj logicky text.
