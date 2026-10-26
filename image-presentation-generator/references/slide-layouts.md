# Slide Layouts — knihovna pro GPT Image 2 (16:9)

Knihovna **49 layoutů** ve 8 rodinách. Každý layout = popis kompozice 16:9 slidu, který se vloží do GPT Image 2 promptu (sekce „LAYOUT" — viz prompt struktura v SKILL.md Krok 3).

**Proč tak velká knihovna:** HTML generátor měl jen ~8 layoutů, protože ho svazoval CSS (flexbox/grid, viewport fitting). GPT Image 2 popíše libovolnou editoriální kompozici → deck může být pokaždé vizuálně pestrý.

**Layout slug** (kebab-case) v levém sloupci = hodnota pole `layout` v `slide-plan.json`. Skript `generate-images.py` podle něj připojuje brand reference.

---

## Pravidla vizuální kvality (NON-NEGOTIABLE — platí pro KAŽDÝ slide)

Tato pravidla jdou do každého promptu (composition guidance + negative prompts). Přenesená z `html-presentation-generator` — tam jako CSS pravidla, tady jako prompt instrukce.

### ⭐ PRAVIDLO 0 — VIZUÁLNÍ IMPACT (důvod existence tohoto skillu)

**Každý slide MUSÍ vypadat jako prémiový editoriální design s reálným vizuálním impactem — bohatá kompozice, kterou by HTML/CSS neudělalo.** Tohle je nejdůležitější pravidlo. Pokud slide vypadá jako ploché ikonky + text na jednobarevném pozadí, **selhal** — přesně tohle umí `html-presentation-generator`, a pak není důvod pálit kredity na image generator.

**Litmus test (aplikuj na KAŽDÝ slide před odesláním promptu):**
> „Vypadal by tenhle slide úplně stejně, kdyby ho někdo poskládal v HTML/CSS z ikonek a textu?"
> Pokud ANO → slide nevyužívá sílu image generátoru. Přidej vizuální bohatost.

**Čím se dosahuje impact (dej do promptu):**
- **Reálná fotografie / fotorealistický render** — produkt v prostředí, lifestyle, materiál, ne vektorová placka
- **Hloubka a světlo** — depth-of-field, nasvícení, stíny, vrstvení, atmosféra
- **Materiál a textura** — sklo, kov, papír, jemný grain/gradient, prémiové povrchy
- **Dramatické měřítko a kompozice** — výrazný focal point, editoriální art direction (Apple keynote, Stripe, Vogue, Phaidon)
- I **datové/mřížkové layouty** musí mít hloubku — karty se sklem/stínem/produktem/texturou, ne ploché bílé obdélníky s ikonou

**Editorial = ano. Generický slide template = ne.** Když si nejsi jistý, přidej fotografickou nebo materiálovou vrstvu, hloubku a světlo.

---

### Ostatní povinná pravidla

1. **BIG, BOLD, BEAUTIFUL headline** — nadpis je dominantní prvek slidu, první co divák uvidí. Velký, tučný, vysoký kontrast.
2. **Jeden vizuální důraz na slide** — buď je slide o textu (s drobným vizuálem), nebo o obrázku (s drobným textem). Nikdy obojí naplno. Žádné soupeřící focal pointy.
3. **3úrovňová hierarchie** — primární (headline/číslo) → sekundární (podnadpis/vizuál) → terciární (body/labels). Víc než 3 úrovně = rozděl na 2 slidy.
4. **Velkorysý whitespace** — minimálně 20–30 % volné plochy. Prázdný prostor je designový prvek, ne chyba.
5. **Vertikální centrování** — obsah uprostřed slidu, ne nalepený nahoře s prázdnem dole.
6. **Kontrast a čitelnost** — text na tmavém pozadí bílý/téměř bílý; na světlém téměř černý. Akcent jen pro labels/čísla, ne pro body text. Na fotkách overlay pro čitelnost.
7. **Ikony/vizuál místo zdi textu** — feature gridy a bullety s ikonami, ne holý seznam. 4+ textových bodů bez vizuálu → přidej ikony nebo rozděl.
8. **Premium editorial feel** — jako Apple keynote, Stripe deck, Linear docs. NE PowerPoint na ploché barvě, NE stock-photo, NE AI-obvious.
9. **Český text s plnou diakritikou** — vždy explicitně v promptu (á é í ó ú ů ý č ď ě ň ř š ť ž). Max ~40–50 slov na slide.
10. **Vykání ve výstupech pro klienta** (Vy/Váš/Vám) — pokud deck jde ke koncovému zákazníkovi.
11. **Věrnost produktu (POVINNÉ, když je připojená produktová fotka)** — GPT Image 2 NESMÍ vymyslet ani předělat produkt. Když má slide produktovou referenční fotku, prompt musí explicitně přikázat reprodukovat PŘESNĚ ten produkt z reference (tvar, proporce, barva, ovládací panel, branding). Viz snippet „PRODUCT FIDELITY" níže — vlož ho do promptu vždy, když je produkt na slidu.
12. **Logo vždy malé a nenápadné** — brand logo je drobný brand mark, ~6–10 % šířky slidu, v rohu. NIKDY dominantní, nikdy přes půl slidu. Dominuje headline, ne logo. Viz snippet „LOGO SIZING" níže.

### Snippet: PRODUCT FIDELITY (vlož do promptu, když je na slidu produkt s referenční fotkou)

```
PRODUCT FIDELITY: A product reference photo is attached. Reproduce THAT EXACT real
product faithfully — identical shape, proportions, colour, control panel, vents and
branding as in the reference image. Do NOT invent, redesign, restyle or substitute a
different device. The product must be instantly recognizable as the one in the photo.
```

### Snippet: LOGO SIZING (vlož do promptu vždy, když je na slidu logo)

```
LOGO SIZING: place the brand logo small and understated in one corner — roughly
6–10% of slide width. The logo is a subtle brand mark, never a dominant element.
The headline dominates the slide, not the logo.
```

### Univerzální negative prompt (přilep ke každému slidu)

```
NO PowerPoint template look, NO flat single-color background with centered text,
NO plain flat vector icon grid that looks like a basic HTML/CSS slide, NO generic
slide-deck template, NO stock-photo aesthetic, NO AI-obvious generic style,
NO cluttered layout, NO multiple competing focal points, NO watermarks,
NO gibberish text, NO misspelled words, NO generic indigo/purple gradients,
NO low contrast text, NO oversized or dominant logo.
Slide MUST look like premium editorial design with depth, light and real visual
impact — not a flat template.
```

Když je na slidu produkt s referenční fotkou, přidej do negative ještě:
`NO invented product, NO redesigned device, NO product that differs from the reference photo, NO generic placeholder gadget.`

```
Render all Czech text with correct full diacritics.
```

---

## Content density limity (max na slide)

| Typ slidu | Maximum obsahu |
|-----------|----------------|
| Cover / title | 1 headline + 1 podtitul + tagline |
| Text / bullets | 1 headline + 4–6 bodů NEBO 1 headline + 2 krátké odstavce |
| Feature grid | 1 headline + max 6 karet (ikona + nadpis + 1 řádek) |
| Big stat | 1 obří číslo + 1 popisek + max 1 věta kontextu |
| Quote | 1 citát (max 3 řádky) + atribuce |
| Comparison | 2 strany × max 4 body |

Obsah přesahuje? Rozděl na víc slidů. Nikdy necpát.

---

# Rodina 1 — Úvod / závěr (7)

| slug | účel | prompt kompozice |
|------|------|------------------|
| `cover-cinematic` | titulní, max impact | full-bleed cinematic hero image as background, dark gradient overlay bottom→top, oversized title bottom-left, logo top-left, minimal subtitle |
| `cover-typographic` | titulní bez fotky | typographic dominance, giant headline filling most of the slide, no photo, brand color background, small kicker label above title, logo corner |
| `cover-diagonal-split` | titulní, dynamický | bold diagonal split — photo/color on one triangle, solid brand color on the other, title on the solid side, energetic |
| `cover-floating-3d` | titulní, produktový | clean studio background, single floating 3D object/product centered with soft shadow, title beside or below, premium |
| `cta-gradient-panel` | závěrečná výzva | full-bleed brand gradient panel, dominant CTA headline centered, single button mockup with label, URL below, confident |
| `endcap-product-context` | produkt v kontextu | full-bleed lifestyle shot of product in real context, short closing line overlaid, brand logo, aspirational |
| `contact-card` | kontakt/poděkování | clean slide, large „Děkuji" or contact headline, contact details in tidy row with small icons, logo, generous whitespace |

# Rodina 2 — Sekční předěly (4)

| slug | účel | prompt kompozice |
|------|------|------------------|
| `section-number-fullbleed` | předěl sekce | full-bleed dark/brand background, giant section number (01, 02) as dominant element, section title beside it, minimal |
| `chapter-opener-photo` | otevření kapitoly | full-bleed editorial photo, gradient overlay, chapter title + short index/agenda line, cinematic |
| `transition-word` | přechod, jedno slovo | almost empty slide, one giant word or short phrase centered, dramatic negative space, single accent detail |
| `part-divider-roman` | díl prezentace | elegant divider, large roman numeral or part label, thin accent line, refined |

# Rodina 3 — Text / sdělení (6)

| slug | účel | prompt kompozice |
|------|------|------------------|
| `bullets-icons` | seznam bodů | headline top, 4–6 points each with a small line icon in an accent circle, clean vertical rhythm, NOT a wall of text |
| `two-column-text` | dva bloky textu | headline spanning top, two text columns below with a thin divider, editorial magazine feel |
| `manifesto-statement` | silné prohlášení | one huge bold sentence filling the slide, mixed weight emphasis on key words, dramatic, minimal else |
| `pull-quote-spread` | velký citát | oversized opening quotation mark, large quote text, author attribution with small portrait or name, lots of space |
| `definition-card` | definice pojmu | term as large headline, short definition below in a refined card, accent underline, dictionary-elegant |
| `dropcap-magazine` | magazínový odstavec | editorial paragraph with a dramatic oversized drop cap initial, multi-column or wide measure, serif feel |

# Rodina 4 — Srovnání / kontrast (6)

| slug | účel | prompt kompozice |
|------|------|------------------|
| `split-text-portrait` | text + osoba | 60/40 split, text left, full-height portrait photo right (never crop the face), clean |
| `diagonal-split` | dynamický kontrast | diagonal divider between two ideas/visuals, label on each side, energetic |
| `before-after` | před / po | exact 50:50 split, „Před" left desaturated, „Po" right vibrant, clear labels, product/result only in „Po" |
| `myth-fact` | mýtus vs fakt | two stacked or side rows, red ✗ icon + myth, green ✓ icon + fact, clear visual verdict |
| `versus-headtohead` | A vs B | head-to-head, two options facing center with a „VS" badge between, attributes listed under each |
| `pros-cons-panels` | pro / proti | two panels, plus column (accent) and minus column (muted), icons per row, balanced |

# Rodina 5 — Data / statistiky (6)

| slug | účel | prompt kompozice |
|------|------|------------------|
| `big-stat` | jedno číslo | one enormous number/percentage as hero, short label below, one context line, dramatic scale |
| `three-stat-cards` | 3 metriky | three equal stat cards in a row, each big number + small label + tiny icon, balanced grid |
| `kpi-dashboard` | dashboard mockup | clean analytics dashboard mockup, a few cards/charts, brand-colored, realistic UI but uncluttered |
| `editorial-chart` | graf | one clean bar or line chart as editorial hero, brand colors, clear axis labels, single insight headline |
| `gauge-ring` | ukazatel | large circular gauge/progress ring showing a value, headline beside it, accent fill |
| `donut-percent` | podíl | donut chart with one dominant segment highlighted, percentage in center, legend minimal |

# Rodina 6 — Proces / flow (6)

| slug | účel | prompt kompozice |
|------|------|------------------|
| `numbered-steps-vertical` | kroky | headline top, 3–5 numbered steps stacked, each number in accent circle + short text, clear vertical flow |
| `timeline-ribbon` | časová osa | horizontal timeline ribbon across slide, milestones as nodes with dates/labels, left→right progression |
| `circular-cycle` | cyklus | circular flow diagram, 3–6 nodes around a ring with arrows, central label, balanced |
| `roadmap-milestones` | roadmapa | roadmap path with milestone markers, phase labels, sense of direction toward a goal |
| `funnel-diagram` | trychtýř | funnel narrowing top→bottom, labeled stages, brand gradient, conversion feel |
| `pyramid-hierarchy` | hierarchie | layered pyramid or hierarchy, labeled tiers, foundation→peak, clean |

# Rodina 7 — Mřížky / showcase (6)

| slug | účel | prompt kompozice |
|------|------|------------------|
| `feature-grid` | funkce | 3–6 feature cards in a grid, each icon + bold title + one line, even spacing, premium |
| `icon-grid` | symboly | grid of icons with short labels, consistent line-icon style in one accent color, airy |
| `logo-wall` | loga/partneři | tidy grid of placeholder logos/marks on neutral background, „trusted by" headline, balanced |
| `bento-box` | bento mřížka | bento-box layout with tiles of varied sizes, mix of one big tile + smaller ones, modern app aesthetic |
| `image-mosaic` | koláž fotek | editorial mosaic/collage of 3–5 photos in varied frames, one short headline overlaid, dynamic |
| `polaroid-scatter` | polaroidy | a few photos styled as scattered polaroids with slight rotation, handwritten-style captions, warm |

# Rodina 8 — Lidé / produkt / kreativní (8)

| slug | účel | prompt kompozice |
|------|------|------------------|
| `team-grid` | tým | grid of team portraits, name + role under each, consistent framing, friendly professional |
| `testimonial-portrait` | reference | large customer portrait one side, big quote other side, name/role/company, trustworthy |
| `founder-letter` | dopis | letter-style layout, headline + a few warm paragraphs, signature at bottom, personal |
| `product-hero-mockup` | produkt hero | hero product/app mockup centered or angled, short benefit headline, clean studio background |
| `product-annotated` | anotovaný produkt | product/app screenshot with thin annotation lines pointing to 3–4 feature callouts, technical-elegant |
| `isometric-scene` | isometrie | isometric illustration of a system/workflow/ecosystem, labeled nodes, brand colors, modern |
| `moodboard-collage` | moodboard | curated collage of textures/colors/images expressing a concept, one headline, art-directed |
| `map-node-graph` | mapa/síť | network/node graph or stylized map with connected points, one insight headline, data-viz feel |

---

## Variety engine (POVINNÉ — aby deck nebyl monotónní)

Při tvorbě `slide-plan.json` (Krok 2) drž tato pravidla rozmanitosti:

1. **Žádné dva sousední slidy nesmí mít stejný layout.**
2. **Rotuj napříč rodinami** — po textovém slidu přijde data/proces/showcase, ne další text. Cílem je vizuální rytmus.
3. **Cover + closing jsou hero** (full-bleed, rodina 1). Sekční předěly (rodina 2) odděl logické bloky.
4. **Max ~30 % slidů ze stejné rodiny** v celém decku.
5. **Style Directive (barvy/mood/typografie z brand-board) zůstává konstantní** napříč všemi slidy → kompozice se mění, brand drží pohromadě.
6. Při výběru layoutu zohledni typ obsahu slidu (číslo → `big-stat`; 3 kroky → `numbered-steps-vertical`; citát klienta → `testimonial-portrait`), ale když se hodí víc layoutů, **vyber ten, který v decku ještě nebyl** kvůli pestrosti.

Do `slide-plan.json` ke každému slidu zapiš `layout`, `family` a krátký `variety_note`, ať je rotace viditelná a auditovatelná.
