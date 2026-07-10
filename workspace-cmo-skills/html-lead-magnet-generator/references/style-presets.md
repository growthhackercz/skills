# Style Presets — 4 vizuální styly pro lead magnet

Předpřipravené barevné palety + typografie pro lead magnety, kdy DESIGN.md neexistuje (fallback). Pokud DESIGN.md existuje, **vždy ho použij přednostně** — preset je jen safety net.

Každý preset je inspirovaný reálnými premium brandy. Žádný "AI slop". Editorial kvalita.

---

## Preset 1: Editorial Premium

**Nálada:** Sofistikovaná, klidná, prémiová. Connotace s NYT Magazine, Aesop, Hermès.

**Pro koho:** Coaching, finance, mindfulness, prémiové služby, B2B konzultace.

```css
:root {
  /* Colors */
  --color-primary: #1a1a1a;        /* hluboká čerň */
  --color-secondary: #f7f5f0;      /* krémová */
  --color-accent: #b8856a;         /* terracota */
  --color-text: #1a1a1a;
  --color-text-muted: #6b6357;
  --color-bg: #ffffff;
  --color-bg-subtle: #f7f5f0;
  --color-success: #4a7c59;        /* tlumená zelená */
  --color-error: #a04545;          /* tlumená červená */
  --color-border: #e0dccf;

  /* Typography */
  --font-display: "GT Sectra", "Playfair Display", Georgia, serif;
  --font-body: "Inter", -apple-system, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  /* Display sizes */
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
}
```

**Signature elements:**
- Serif display font na nadpisech (GT Sectra, Playfair Display)
- Sans-serif body (Inter)
- Krémové sub-pozadí pro sekce
- Terracota accent na čísla a CTA
- Generous spacing, vertikální rytmus

---

## Preset 2: Notebook Clean

**Nálada:** Praktická, klidná, "moleskine na stole". Connotace s Field Notes, Moleskine, Linear docs.

**Pro koho:** Workbooky, checklisty, šablony, productivity, skill-based topics.

```css
:root {
  --color-primary: #2c2c2c;
  --color-secondary: #fafaf8;
  --color-accent: #5b6cff;          /* indigová */
  --color-text: #2c2c2c;
  --color-text-muted: #8a8a85;
  --color-bg: #fafaf8;              /* off-white pozadí */
  --color-bg-subtle: #f0eee8;
  --color-success: #2d8b5e;
  --color-error: #d94545;
  --color-border: #d8d6cf;

  --font-display: "Inter", system-ui, sans-serif;
  --font-body: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  --fs-display: 44pt;
  --fs-h1: 26pt;
  --fs-h2: 18pt;
  --fs-h3: 13pt;
  --fs-body: 11pt;
  --fs-small: 9pt;

  --lh-tight: 1.1;
  --lh-normal: 1.6;
  --ls-display: -0.01em;
}
```

**Signature elements:**
- Jeden font napříč (Inter) — typografická čistota
- Off-white pozadí (#fafaf8) — paper-like feel
- Indigová akce — intelektuální, ne hravá
- Tabulky a checklisty dominují
- Grid layout dominuje, hodně whitespace

---

## Preset 3: Bold Coach

**Nálada:** Sebevědomá, energická, contrast-driven. Connotace s Hormozi, MrBeast, fitness coaches.

**Pro koho:** Coaching s tvrdým postojem, sales, business growth, transformační programy.

```css
:root {
  --color-primary: #0a0a0a;
  --color-secondary: #ff5722;       /* outbound oranž */
  --color-accent: #ff5722;
  --color-text: #0a0a0a;
  --color-text-muted: #555;
  --color-bg: #ffffff;
  --color-bg-subtle: #fff5f0;       /* peach tint */
  --color-success: #00b87c;
  --color-error: #ff3838;
  --color-border: #1a1a1a;          /* tlustý černý border */

  --font-display: "Archivo Black", "Inter Black", sans-serif;
  --font-body: "Space Grotesk", "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  --fs-display: 64pt;
  --fs-h1: 36pt;
  --fs-h2: 24pt;
  --fs-h3: 14pt;
  --fs-body: 11pt;
  --fs-small: 9pt;

  --lh-tight: 0.95;
  --lh-normal: 1.5;
  --ls-display: -0.025em;

  --fw-normal: 400;
  --fw-bold: 900;
}
```

**Signature elements:**
- Tlusté display fonty (Archivo Black, font-weight 900)
- Vysoký kontrast (#0a0a0a vs. #ffffff)
- Oranžový accent — energy + urgency
- Tlusté borders (1.5pt) místo jemných
- ALL CAPS labels, výrazné čísla
- Tight letter-spacing na nadpisech

---

## Preset 4: Soft Therapeutic

**Nálada:** Empatická, ženská, healing. Connotace s Glossier, Aesop, terapeutické brandy.

**Pro koho:** Coaching pro ženy, mindfulness, self-care, terapeutické služby, emotional intelligence.

```css
:root {
  --color-primary: #4a3a3a;         /* tmavá růžovohnědá */
  --color-secondary: #faf5f0;
  --color-accent: #c89696;          /* dusty rose */
  --color-text: #4a3a3a;
  --color-text-muted: #8a7a7a;
  --color-bg: #fefcfa;
  --color-bg-subtle: #f5ede5;
  --color-success: #7a9070;
  --color-error: #b86060;
  --color-border: #e8ddd5;

  --font-display: "Cormorant Garamond", "Playfair Display", Georgia, serif;
  --font-body: "Crimson Pro", "Source Serif Pro", Georgia, serif;
  --font-mono: "JetBrains Mono", monospace;

  --fs-display: 56pt;
  --fs-h1: 32pt;
  --fs-h2: 22pt;
  --fs-h3: 14pt;
  --fs-body: 12pt;                  /* o 1pt větší pro lepší čitelnost serifu */
  --fs-small: 10pt;

  --lh-tight: 1.1;
  --lh-normal: 1.6;
  --ls-display: 0;

  --fw-normal: 400;
  --fw-medium: 500;
  --fw-semibold: 600;
}
```

**Signature elements:**
- Serif napříč (display i body) — literární feel
- Teplé peach a dusty rose tóny
- Light-medium font weights — žádné bold
- Větší body text (12pt) pro pohodlí čtení
- Generous line-height, plenty of space
- Žádné tvrdé borders, jemné stíny

---

## Jak skill vybírá preset

Pokud `/documents/brand/DESIGN.md` **existuje** → použij ho, ignoruj presety.

Pokud `DESIGN.md` **neexistuje**, skill odhadne preset z **brand DNA**:

| Brand DNA signál | Preset |
|------------------|--------|
| `## 1. ESENCE` esence: "klidný, prémiový, sofistikovaný", "moudrý průvodce" | Editorial Premium |
| `## 5. HLAS` tón: "intelektuální, klidný, expertní"; obor: produktivita, B2B | Notebook Clean |
| `## 5. HLAS` tón: "sebevědomý, konfrontační, energický"; brand stage: autorita | Bold Coach |
| `## 1. ESENCE` esence: "empatický, hřejivý, ženský, healing"; obor: terapeutika, mindfulness | Soft Therapeutic |

**Pokud nelze odhadnout** (signály matou) → default **Editorial Premium** (univerzálně použitelný) + zeptej se uživatele:

> *"DESIGN.md nemáš, takže jsem zvolil styl 'Editorial Premium' — sofistikovaný a univerzálně použitelný. Pokud chceš jiný směr, zde jsou alternativy: [seznam 4 presetů]. Která ti sedí nejvíc?"*

---

## Override per stránka

I když DESIGN.md nebo preset definuje hlavní paletu, některé stránky mohou mít jinou náladu:

- **Cover** — vždy nejvíc kontrastní (typicky tmavé pozadí, světlý text)
- **Quote stránka** — invertovaná barva (tmavé pozadí)
- **CTA** — gradient z primary → accent
- **Chapter opener** — sub-pozadí (`--color-bg-subtle`)
- **Audit pages** — čisté pozadí pro koncentraci, žádné akcenty

Tyto inverze jsou v `page-layouts.md` zabudované — preset jen poskytuje proměnné.

---

## Custom override z brand DNA

I s presetem skill zachová některé prvky z Brand DNA:

- **Slovník** (sekce 5 "Slova, která značku definují") — použít přesně ve všech textech
- **Tonalita** (sekce 5 "Tón") — ovlivní úvody, citáty, microcopy
- **Vybudování autority autora** (sekce 3 "Příběh zakladatele") — pro footer cover stránky a quote spreads

Preset = vizuální obal. Brand DNA = obsah uvnitř obalu.
