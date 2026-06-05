# Premium Layouts — 16 layout šablon pro GPT Image 2

Každý layout má **promptovou šablonu** sestavenou z 5 částí (Style Directive + Orientation + Layout + Content + Negatives) a **adaptaci pro portrait/landscape**.

Cílem je **professional layout designer quality** — jako Phaidon, Wallpaper, Apple PDF reports. Žádný "AI-obvious" feel.

---

## Univerzální prompt struktura

```
{STYLE_DIRECTIVE}

A4 {portrait|landscape} page design, aspect ratio {2480:3508|3508:2480}, 300 DPI print quality.

Layout: {layout_name}
{layout_description — co je dominantní, kde je co umístěno}

Heading: "{exact text in Czech}"
Subheading: "{text}"
Body content: {3-5 bullet points or paragraph}
Visual elements: {photo reference / icon / diagram / number}

Premium editorial design quality, like {reference brand}.
Generous whitespace, single dominant focal element.
NO watermarks, NO stock photo aesthetic, NO AI-obvious style.
NO multiple competing subjects, NO cluttered layouts.

Czech text MUST be rendered correctly with full diacritics: á é í ó ú ů ý č ď ě ň ř š ť ž
```

---

## Layout 1: cover-hero-overlay

**Použití:** Cover stránka s full-bleed image a dramatic title overlay. Nejvíce vizuálního impactu v celém magnetu.

**Reference brandy:** Phaidon book covers, Aesop catalogues, Wallpaper City Guides.

**Portrait verze (2480×3508):**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: cover-hero-overlay
- Full-bleed background photograph or atmospheric gradient (top 60% of page)
- Bottom 40% has dark gradient overlay fading from transparent to deep solid color
- Title text positioned in bottom third, large display typography (60-80pt)
- BRAND LOGO top-left (REQUIRED — use the provided brand logo reference image, place it at small size 32-48pt height, preserve original colors if visible against background, OR use white/inverted variant if background is dark)
- Author + role at very bottom, small caps with letter-spacing, separated by horizontal divider line

Heading: "{title in Czech, max 8 words}"
Subheading: "{1-line description, max 12 words}"
Author: "{author name + role/authority}"
Brand logo: REQUIRED top-left
Visual elements: hero image — {description, e.g. "atmospheric tech workspace with subtle blue glow", "candid lifestyle portrait, natural light"}

Premium book cover aesthetic. Title MUST dominate visually.
Generous space around title. NO clutter.

CRITICAL: NO marketing pill or badge ("Magnet zdarma", "Free Guide", "Ebook" pills) — degrades visual quality.
Brand logo IS the brand signal, not a pill.

NO multiple titles, NO marketing buzzwords overlay, NO stock photo.
```

**Landscape verze (3508×2480):**
- Title se přesune doleva, foto je pravá polovina
- Subheading + author pod title
- Badge top-right

---

## Layout 2: cover-typographic

**Použití:** Cover stránka **bez fotky** — typografická dominance.

**Reference brandy:** Aesop product catalogues, Helvetica brand books, Linear changelog.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: cover-typographic
- Solid color background (primary or accent from style directive)
- Massive typography fills upper 60-70% of page
- Title broken across 3-4 lines, mixed weights for emphasis (some words bolder)
- Subheading below title in smaller display weight
- Bottom 30% has supporting metadata: brand mark, author, badge

Heading: "{title broken into emphatic phrases}"
Subheading: "{description}"
Brand mark: "{brand name in small caps}"
Author: "{author}"
Badge: "Magnet zdarma"

Premium typographic poster aesthetic. Confidence through scale.
Single color background, generous whitespace.

NO photograph, NO multiple decorative elements, NO gradients except subtle accent.
```

---

## Layout 3: intro-stats-cards

**Použití:** Druhá stránka s úvodním textem + 3 metric cards (klíčová čísla brandu/produktu).

**Reference brandy:** McKinsey reports, Bloomberg Businessweek, Stripe reports.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: intro-stats-cards
- Top: small label "Úvod" with thin accent line, page number top-right
- Title (h2-level, 30-40pt) takes upper third, bold display
- Lead paragraph below title (11-12pt body, 3-5 lines)
- Middle: 3 stat cards side-by-side, each with large number + label
- Bottom: subtle accent line + transition to next page

Heading: "{intro title}"
Lead paragraph: "{2-3 sentence intro setting context}"
Stat 1: { value: "17,5 mil Kč", label: "Objednávky za 14 dní" }
Stat 2: { value: "16 944", label: "Účastníků AI Summitu" }
Stat 3: { value: "2 300 %", label: "Meziměsíční nárůst" }

Editorial business publication aesthetic. Numbers MUST be visually dominant in cards.
Generous space between elements.

NO chart graphics, NO complex iconography, just numbers + labels.
```

**Landscape verze:**
- Title vlevo, stats vpravo (50/50 split)
- Stats stacked vertically vpravo

---

## Layout 4: toc-numbered

**Použití:** Table of contents — očíslovaný seznam kapitol s page references.

**Reference brandy:** Phaidon book TOCs, Penguin Modern Classics, Monocle issue contents.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: toc-numbered
- "OBSAH" headline at top, large display, accent color
- Vertical list of 5-10 entries, each row:
  - Large number (01, 02, 03...) on left, accent color, display font
  - Chapter name in middle, body text bold
  - Page reference on right (str. 03), small text muted
  - Thin divider line between entries
- Generous padding, 60-70pt row height

Heading: "OBSAH" (or "INSIDE" if English)
Entries:
  01 — {chapter name} — str. 03
  02 — {chapter name} — str. 04
  ...

Editorial book TOC aesthetic. Numbers MUST be the visual hero.
Clean, Swiss-style precision.

NO icons, NO decoration, just typography and numbers.
```

---

## Layout 5: chapter-opener-fullbleed

**Použití:** Otevření nové kapitoly s full-bleed image + giant chapter number + title.

**Reference brandy:** Phaidon design books, Magnum photo books, Le Labo seasonal lookbooks.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: chapter-opener-fullbleed
- Full-bleed atmospheric image as background
- Subtle dark overlay (rgba 0.4-0.6) for text legibility
- Giant chapter number (200-300pt) in lower-left, accent color, semi-transparent or outlined
- Chapter title (40-50pt display) in lower-right or below number
- Optional teaser line (subhead) below title
- Top-left small label: "KAPITOLA"

Chapter number: "0{N}" (e.g. "01", "02", "03")
Heading: "{chapter title}"
Tease line: "{1-line teaser hinting at content}"
Visual: atmospheric image — {description matching chapter theme}

Photography book aesthetic. Drama through scale.
Number MUST dominate the lower portion.

NO body text, NO bullet points, just dramatic opening.
```

**Landscape verze:**
- Number dominant na levé straně (60% šířky), title na pravé
- Image full-bleed background

---

## Layout 6: content-split-portrait

**Použití:** Hlavní obsahová stránka — text vlevo (60%), portrait foto vpravo (40%).

**Reference brandy:** NYT Magazine feature spreads, The Gentlewoman interviews, Monocle columns.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: content-split-portrait
- Top: small label "Kapitola N · {topic}" with thin divider line
- Two-column split: left 60% text content, right 40% portrait photograph
- Left column has H2 headline (24-30pt display), 2-3 short paragraphs (body 11pt), and optional pull quote
- Right column: portrait photograph filling full height, person looking off-frame or at camera
- Bottom: small page number, no other footer

Heading: "{section heading}"
Body: "{2-3 paragraphs of content, ~150 words total}"
Pull quote (optional): "{single impactful sentence}"
Visual: portrait photograph — {person/character description}

Editorial magazine spread aesthetic. Text and image in dialogue.
Clean column layout, generous line-height in body text.

NO icons, NO decorative elements, just photo + text.
```

---

## Layout 7: content-image-top

**Použití:** Stránka s landscape image v horních 40 %, text dole.

**Reference brandy:** Wallpaper Magazine product features, Apple Newsroom articles.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: content-image-top
- Top 40%: landscape photograph or product mockup, full-width
- Middle: H2 headline (24-30pt display) right below image
- Below: 2-3 paragraphs body text (11-12pt)
- Bottom: optional callout box with key takeaway

Heading: "{section heading}"
Body: "{paragraphs}"
Callout: "{key insight, 1-2 sentences}"
Visual: landscape image — {description}

Editorial magazine aesthetic. Image as emotional anchor.
Comfortable text rhythm.

NO multiple images, NO sidebar, just hero + text.
```

---

## Layout 8: feature-grid-cards

**Použití:** 3-6 cards v gridu (typy, fáze, benefity).

**Reference brandy:** Linear feature pages, Stripe products grid, Vercel docs.

**Portrait verze (3 cards):**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: feature-grid-cards (3-card vertical)
- Top: H1 headline (28-36pt) + subheading
- Middle: 3 cards stacked vertically OR 1 row × 3 cards (depending on content density)
- Each card has:
  - Icon or large number in circle (top-left)
  - Card title (16-18pt bold)
  - Description (11pt, 2-3 lines)
  - Optional metric/tag (bottom)
- Subtle border or background per card, consistent style across cards

Heading: "{section heading}"
Subheading: "{lead}"
Cards:
  Card 1: { icon: "{description}", title: "{name}", desc: "{2-3 lines}", metric: "{optional}" }
  Card 2: { ... }
  Card 3: { ... }

Linear-product-page aesthetic. Cards equal weight.
Clean grid alignment, identical card structure.

NO competing visual hierarchy, NO ornaments.
```

**Landscape verze (3-6 cards):**
- Grid 2×2, 2×3 nebo 3×2 podle počtu
- Title a subheading nahoře přes celou šířku

---

## Layout 9: myth-fact-comparison

**Použití:** Side-by-side red × Mýtus vs. green ✓ Fakt s vysvětlením.

**Reference brandy:** Bloomberg explainer charts, NYT Upshot, Nieman Lab visualizations.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: myth-fact-comparison
- Top: H1 "Mýty vs. Fakta" + thin divider
- Below: 3-5 paired rows, each row split 50/50:
  - LEFT: red/orange × icon + "MÝTUS" label + statement (italic)
  - RIGHT: green ✓ icon + "FAKT" label + statement (regular)
- Subtle background tint per side (rgba 0.05-0.1)
- Padding between pairs

Heading: "Mýty vs. Fakta"
Pairs:
  1. MÝTUS: "{misconception}" / FAKT: "{truth}"
  2. ...

Bloomberg explainer aesthetic. Color-coded for instant scanning.
Clean dual-column structure.

NO complex graphics, just typography + clear color coding.
```

**Landscape verze:** identický layout, jen širší — víc prostoru pro delší věty.

---

## Layout 10: quote-spread

**Použití:** Full-page citát autora s velkou typografií + atribuce.

**Reference brandy:** It's Nice That typographic posters, Pentagram brand books, Working Not Working features.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: quote-spread
- Solid color background (primary or accent)
- Decorative quote mark icon top-left, 60-80pt, semi-transparent
- Quote text centered or left-aligned, massive scale (40-60pt display, italic)
- Quote breaks across 3-5 lines naturally
- Below quote: thin divider line + author name + role/role description
- Optional subtle author portrait (small, top-right) — OR no portrait, pure typography

Quote: "{text, max 50 words}"
Author: "{name}"
Role: "{role/title}"

Typography poster aesthetic. Quote MUST dominate everything.
Generous breathing room around text.

NO photo background, NO ornamental decoration, just confident typography.
```

---

## Layout 11: checklist-detailed

**Použití:** 5-15 položek s checkbox + detailní popis.

**Reference brandy:** Notion templates, Sunday morning planner aesthetic, Field Notes.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: checklist-detailed
- Top: H1 headline + subheading
- Middle: 5-15 list items, each with:
  - Empty checkbox (square, thin border, 18-20pt)
  - Item title (12-14pt bold)
  - Optional 1-line description below title (10pt muted)
  - Thin divider between items
- Bottom: small tip box "Jak používat" with info icon

Heading: "{checklist title}"
Subheading: "{lead, when/how to use}"
Items:
  ☐ {Item 1}: {description}
  ☐ {Item 2}: {description}
  ...
Tip: "{usage tip}"

Field Notes journal aesthetic. Practical, usable.
Clean row structure, easy to mark off.

NO decorative graphics, just typography + checkboxes.
```

---

## Layout 12: diagram-flow

**Použití:** Circular nebo linear diagram s ikonami v uzlech (jako "Náš Ekosystém AI" z 08-inspirace).

**Reference brandy:** McKinsey strategy diagrams, BCG matrices, Atlassian docs diagrams.

**Portrait verze (circular flow):**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: diagram-flow (circular cycle)
- Top: H1 headline (24-30pt) + 1-line subheading
- Middle: circular diagram, 3-5 nodes connected with arrows in cycle
  - Each node: filled colored circle (60-80pt diameter) with white icon inside
  - Node label below circle, small bold text
  - Arrows between nodes show flow direction, accent color
  - Center of cycle: optional label or central concept
- Bottom: 2-3 sentence description supporting the diagram

Heading: "{diagram title, e.g. 'Náš Ekosystém AI'}"
Subheading: "{1-line context}"
Nodes: ["{node 1 label}", "{node 2}", "{node 3}", "{node 4}"]
Center label (optional): "{concept}"
Description: "{2-3 sentences}"

McKinsey strategy diagram aesthetic. Clean geometric flow.
Equal node weights, professional iconography.

NO 3D effects, NO complex shading, flat design.
```

**Linear timeline verze:**
- Horizontal nodes connected with arrows
- Phase labels below
- Use landscape orientation for 6+ phases

---

## Layout 13: process-numbered-steps

**Použití:** Vertikální seznam očíslovaných kroků s ikonami a popisy (jako "Postup Implementace AI" z 08-inspirace).

**Reference brandy:** Apple support tutorials, Stripe integration guides, Linear how-to docs.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: process-numbered-steps
- Top: H1 headline + 1-line subheading
- Middle: 3-5 numbered step rows, each with:
  - Massive number on left (1, 2, 3...) — 80-120pt display, accent color
  - Step title (14-16pt bold) on right
  - Description (11pt, 2-3 lines) below title
  - Small icon on far right corner (optional)
  - Thin divider between steps
- Bottom: small CTA hint or transition

Heading: "{process title, e.g. 'Postup Implementace AI'}"
Subheading: "{1-line lead}"
Steps:
  1. { title: "{step 1}", desc: "{description}", icon: "{description}" }
  2. ...

Stripe integration guide aesthetic. Numbers as design hero.
Clean rhythm between steps.

NO complex flowcharts, just numbered list with strong typography.
```

---

## Layout 14: product-mockup

**Použití:** Produktový vizuál + benefits side panel.

**Reference brandy:** Apple product pages, Bose campaigns, Le Labo product cards.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: product-mockup
- Top 60%: hero product mockup (device, package, app screen) on subtle gradient or clean background
- Bottom 40%: 3-5 benefit bullets with small icons, in 1 column or 2-column grid
- Optional product name as caption below mockup

Heading: "{product name or proposition}"
Mockup: {device/product description for image generation}
Benefits: ["{benefit 1 with icon}", "{benefit 2}", ...]

Apple product page aesthetic. Product as hero.
Clean, premium, single dominant subject.

NO multiple products, NO competing colors, focused composition.
```

---

## Layout 15: cta-gradient-panel

**Použití:** Závěrečná CTA stránka s full-bleed gradient + dominant title + button mockup.

**Reference brandy:** Stripe pricing pages, Linear Pro CTA, Apple buy-now sections.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: cta-gradient-panel
- Full-bleed gradient background (primary → accent diagonal or radial)
- Top: small label "Co teď dál?" or "Začni dnes"
- Middle-upper: dominant headline (40-60pt display), white text, max 12 words
- Middle: 4-5 benefit bullets with white check icons, body text white
- Lower-middle: large CTA button mockup (white background, primary text, sharp or rounded corners matching brand)
- Bottom: meta line — pricing, urgency, guarantee — small text white opacity 0.7

Eyebrow: "Co teď dál?"
Heading: "{powerful CTA title, max 12 words}"
Benefits: ["{benefit 1}", "{benefit 2}", ...]
CTA button text: "{button label, e.g. 'Chci začít dnes'}"
Meta: "{price · urgency · guarantee}"

Stripe pricing page aesthetic. Confident, urgent, clean.
Button MUST be visually prominent.

NO photo background, NO complex decoration, just gradient + typography.
```

---

## Layout 16: endcap-product

**Použití:** Závěrečná stránka s full-bleed brand asset image (product mockup v kontextu) + závěrečná zpráva.

**Reference brandy:** Apple Annual Report cover, Loewe Foundation closing pages, Magnum closing spreads.

**Portrait verze:**
```
{STYLE_DIRECTIVE}

A4 portrait, 2480:3508.

Layout: endcap-product
- Full-bleed product/brand asset image
- Bottom 30-40%: dark gradient overlay
- Bottom: closing message
  - Small label "{brand name · product line}"
  - Closing headline (32-44pt display) — short, declarative
  - 1-line tagline
  - URL or contact (small, bottom)

Brand label: "{brand · product}"
Heading: "{closing headline}"
Tagline: "{1-line summary}"
URL: "{website URL}"
Visual: product mockup or brand contextual image

Premium brand book closing aesthetic. Quiet confidence.
Image speaks louder than text.

NO multiple images, NO badges, just dignified closing.
```

---

## Mapování typu magnetu → sekvence layoutů

Pro každý typ magnetu z `lead_magnet_generator` vyber sekvenci layoutů. Pro 7-stránkový "Use Case Showcase" (jako AI Akcelerátor):

```
1. cover-hero-overlay (cover s 3 founders)
2. intro-stats-cards (3 metric cards z brandu)
3. content-split-portrait (Agent 01)
4. content-image-top (Agent 02)
5. feature-grid-cards (Agenti 03-05 v gridu) — sloučí 3 agenty
6. process-numbered-steps (7-week process)
7. cta-gradient-panel
8. endcap-product (CliqSales product mockup)
```

Pro **Workbook** (15-30 stran):
- cover-typographic (clean, focus na téma)
- toc-numbered
- chapter-opener-fullbleed × N
- content-split-portrait × N
- checklist-detailed × N
- quote-spread × 1-2
- cta-gradient-panel
- endcap-product

Pro **Audit** (5-10 stran):
- cover-hero-overlay
- intro-stats-cards (proč audit)
- diagram-flow (4 typy)
- content-split-portrait × N (per typ výklad)
- cta-gradient-panel
- endcap-product

Detail per typ magnetu v kombinaci s `00-strategie.md` z `lead_magnet_generator`.

---

## Pravidlo: GPT Image 2 prompt limity

- Max prompt délka: ~2000 znaků (FAL endpoint), ~1000 znaků doporučeno pro reliability
- Style Directive může mít 400-600 znaků, layout description 200-400, content 100-300, negatives 100
- Pokud prompt přeteče, **zkrať Style Directive na bullet points** (esence per sekce)
- **Reference images** přes FAL: až 3 simultaneously (brand-board + brand-kit relevant + optional product photo)
