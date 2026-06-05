# Print CSS Specification

Pravidla pro print CSS A4 PDF výstupu lead magnetu.

---

## Page setup

```css
@page {
  size: A4;             /* 210mm × 297mm */
  margin: 25mm 20mm;    /* 25mm top/bottom, 20mm left/right */
}
```

**Margin override pro cover (první stránka):**
```css
@page :first {
  margin: 0;            /* Cover page má full bleed */
}
```

**Margin pro odlišné kapitoly** (volitelné):
```css
@page :left { margin-left: 25mm; margin-right: 20mm; }
@page :right { margin-left: 20mm; margin-right: 25mm; }
```

---

## Page numbers

```css
@page {
  @bottom-center {
    content: counter(page);
    font-family: var(--font-body);
    font-size: var(--fs-small);
    color: var(--color-text-muted);
  }
}

@page :first {
  @bottom-center { content: none; }   /* Bez čísla na cover */
}
```

**Volitelné — formát "1 / 24":**
```css
@bottom-center {
  content: counter(page) " / " counter(pages);
}
```

---

## Page breaks

### Před nadpisem kapitoly

```css
.content h1 {
  page-break-before: always;
  break-before: page; /* moderní syntax */
}

.content h1:first-child {
  page-break-before: auto; /* První kapitola nezačíná na nové stránce */
}
```

### Po nadpisu (zabraň osamělému nadpisu)

```css
.content h1, .content h2, .content h3 {
  page-break-after: avoid;
  break-after: avoid;
}
```

### Uvnitř bloků (zabraň rozřezání)

```css
.key-takeaways,
.cta-block,
.myth-fact,
.quiz,
.challenge,
pre,
table {
  page-break-inside: avoid;
  break-inside: avoid;
}
```

---

## Widows & orphans

```css
p, li {
  orphans: 3;   /* Min. 3 řádky odstavce na konci stránky */
  widows: 3;    /* Min. 3 řádky odstavce na začátku stránky */
}
```

---

## Print-specific media query

```css
@media print {
  /* Vynutit barvy a obrázky v Chromiu */
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  /* Skrýt prvky, které nemají v PDF být */
  .no-print { display: none; }

  /* Externí odkazy — přidat URL za text */
  a[href^="http"]::after {
    content: " (" attr(href) ")";
    font-size: var(--fs-small);
    color: var(--color-text-muted);
  }
}
```

---

## Playwright PDF options

V `render-pdf.py` použij:

```python
await page.pdf(
    path=output_path,
    format="A4",
    print_background=True,           # KRITICKÉ — bez toho nejsou barvy
    margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},  # margins jsou v @page
    prefer_css_page_size=True,       # Respektuj @page CSS
    display_header_footer=False,     # Headers/footers řešíme přes @page
)
```

**Pozn.:** Pokud `prefer_css_page_size=True`, Playwright respektuje `@page { size: A4 }` z CSS — nepřetluče ho `format="A4"`.

---

## Fonty v print kontextu

### System-ui fallback chain

Vždy končí systémovými fonty:
```css
--font-body: "Inter Variable", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
```

### Webfonty — preload

V `<head>` přidej preload pro rychlejší render:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=block" rel="stylesheet">
```

`display=block` zabrání FOIT/FOUT v PDF.

### Wait for fonts

V Playwright počkej na fonty před PDF:

```python
await page.evaluate("document.fonts.ready")
await page.wait_for_load_state("networkidle")
```

---

## Image rendering

```css
img {
  max-width: 100%;
  height: auto;
  break-inside: avoid;
  image-rendering: -webkit-optimize-contrast; /* Pro screenshot-y */
}

.cover-image {
  -webkit-print-color-adjust: exact;
}
```

**Background images:**
```css
.cover {
  background-image: url('...');
  background-size: cover;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
```

---

## Common pitfalls

### Barvy nejsou v PDF

→ Chybí `print_background=True` v Playwright NEBO `print-color-adjust: exact`.

### Page break uprostřed obrázku

→ Přidej `break-inside: avoid;` na rodiče obrázku.

### Webfonty se nenačtou

→ Chybí `await page.evaluate("document.fonts.ready")` před `page.pdf(...)`.

### Margins jsou divné

→ Konflikt mezi Playwright `margin` parametrem a `@page` CSS. Nastav Playwright margin na `0` a vše řeš v CSS.

### Velikost není A4

→ Bez `prefer_css_page_size=True` Playwright preferuje `format` parametr. Buď nastav oba, nebo jen CSS s `prefer_css_page_size=True`.

### Texty se přelévají přes margin

→ V CSS se zapomněly resetovat `padding` na `body` a `section`. Použij reset v šabloně.

---

## Velikostní cíl

| Délka | Cílová velikost PDF |
|-------|---------------------|
| 10 stran | 200–500 KB |
| 20 stran | 500 KB – 1.5 MB |
| 30 stran | 1–3 MB |
| 50 stran | 2–5 MB |

Pokud je PDF výrazně větší, hlavní viník bývá:
1. Embedded webfonty (vše v jednom souboru)
2. Vysoká rozlišení obrázků (>2400px)
3. Background images bez komprese

Kompresní strategie viz `render-pdf.py` (gs/Ghostscript fallback je volitelný).
