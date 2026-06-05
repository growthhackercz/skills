# Themes a Dials — 4 fallback themes + 8 design dials

Pokud klient nemá `DESIGN.md`, použij jednu ze 4 fallback themes. Pak ladič
8 dials podle typu projektu nebo klientovy preference.

## 4 Fallback Themes

### A) Pristine Light Mode
**Vibe:** off-white, papírové tóny, sharp dark text. Akademické, čisté,
důvěryhodné. Default pro většinu B2B.

**Palette:**
```css
--background: oklch(98% 0.005 90);   /* #F8F7F4 — off-white paper */
--foreground: oklch(20% 0.01 280);   /* near-black, slight cool */
--muted: oklch(94% 0.008 90);         /* very light card bg */
--muted-foreground: oklch(45% 0.01 280); /* secondary text */
--border: oklch(90% 0.005 90);        /* hairline border */
--primary: oklch(20% 0.01 280);       /* same as foreground (mono CTAs) */
--primary-foreground: oklch(98% 0.005 90);
--accent: oklch(70% 0.18 35);         /* warm orange/amber accent */
```

**Typography:** Inter celé, sharp hierarchy
**Cards:** subtle border `border-stone-200`, žádný shadow
**Hover:** subtle color shift, ne elevation

### B) Deep Dark Mode
**Vibe:** charcoal, graphite, elegant glow only when justified. Default pro
dashboardy. Reduce eye fatigue.

**Palette:**
```css
--background: oklch(15% 0.01 240);    /* #0F1419 — deep charcoal */
--foreground: oklch(94% 0.005 240);   /* near-white */
--muted: oklch(20% 0.01 240);          /* card bg, subtle elevation */
--muted-foreground: oklch(70% 0.01 240); /* secondary text */
--border: oklch(25% 0.01 240);         /* hairline */
--primary: oklch(70% 0.18 220);        /* cyan/blue accent */
--primary-foreground: oklch(15% 0.01 240);
--accent: oklch(75% 0.15 145);         /* emerald accent pro positive metriky */
--destructive: oklch(60% 0.20 30);    /* red pro negative metriky */
```

**Typography:** Inter UI + Geist Mono pro čísla
**Cards:** `bg-slate-900` s `border-slate-800`, subtle inner glow only on focus
**Hover:** slight `bg-slate-800` shift

### C) Bold Studio Solid
**Vibe:** ochre, royal blue, forest tones, sharp UI. Statement brand,
creative agency, premium B2C.

**Palette:**
```css
--background: oklch(96% 0.02 70);     /* warm cream */
--foreground: oklch(18% 0.05 250);    /* deep navy */
--muted: oklch(92% 0.04 70);
--primary: oklch(45% 0.20 250);       /* royal blue */
--primary-foreground: oklch(98% 0.02 70);
--accent: oklch(70% 0.20 60);         /* ochre */
--secondary: oklch(35% 0.15 145);     /* forest green */
```

**Typography:** Inter UI + bold display weights (font-black na hero)
**Cards:** filled color blocks, ne white-on-white
**Hover:** color invert nebo bold shadow

### D) Quiet Premium Neutral
**Vibe:** bone, sand, taupe, stone. Restrained luxury. Aesop, Hermès, Loro
Piana feel. Pro premium products / luxury services.

**Palette:**
```css
--background: oklch(94% 0.015 80);    /* bone #EDE9E1 */
--foreground: oklch(30% 0.02 60);     /* taupe brown */
--muted: oklch(89% 0.015 80);          /* sand */
--muted-foreground: oklch(50% 0.02 60); /* warm gray */
--border: oklch(85% 0.015 80);         /* sand border */
--primary: oklch(30% 0.02 60);         /* deep taupe = mono CTA */
--primary-foreground: oklch(94% 0.015 80);
--accent: oklch(55% 0.12 35);          /* terracotta accent */
```

**Typography:** Inter UI + serif display (Cormorant Garamond OPTIONAL na display)
**Cards:** no borders, subtle shadow `shadow-stone-200/50`
**Hover:** barely-there opacity shift

## 8 Dials — design parametry

Každá stránka má 8 dimenzí, které lze tunit. Default values jsou per
project type (web / dashboard / landing).

### 1. DESIGN_VARIANCE (1=rigid, 10=artsy)
- Jak moc se layout odchyluje od konvencí
- **Web default:** 5
- **Dashboard default:** 3 (clarity > variance)
- **Premium landing default:** 8

### 2. VISUAL_DENSITY (1=airy, 10=packed)
- Kolik content per viewport
- **Web default:** 5
- **Dashboard default:** 6 (KPIs need information density)
- **Landing default:** 4 (breathing room sells)

### 3. ART_DIRECTION (1=safe, 10=bold creative)
- Risk-taking v vizuálních volbách
- **Web default:** 6
- **Dashboard default:** 4 (data > drama)
- **Landing default:** 8

### 4. IMPLEMENTATION_CLARITY (1=moodboard, 10=codeable)
- Jak strict je následování stack lock-in
- **Vždy default:** 10 (musíme vždy generovat valid kód)

### 5. IMAGE_USAGE_PRIORITY (1=typographic, 10=image-led)
- Důraz na images vs typografii
- **Web default:** 6
- **Dashboard default:** 2 (typo + data viz, no decorative images)
- **Landing default:** 7

### 6. SPACING_GENEROSITY (1=compact, 10=spacious)
- Whitespace tolerance
- **Web default:** 7
- **Dashboard default:** 5 (compact KPIs, but ne packed)
- **Landing default:** 8 (premium breathing room)

### 7. LAYOUT_VARIATION (1=same repeat, 10=bold variety)
- Variety mezi sekcemi
- **Web default:** 7
- **Dashboard default:** 5
- **Landing default:** 8

### 8. CONVERSION_DISCIPLINE (1=art mood, 10=clear funnel)
- Důraz na conversion funnel
- **Web default:** 7
- **Dashboard default:** 4 (internal tool, ne sales)
- **Landing default:** 9 (sales primary)

## Jak dials aplikovat na generování kódu

### Vysoký VISUAL_DENSITY (6+)
- Bento grid s ≥6 cards
- Compact card padding (`p-4` místo `p-8`)
- Sparkly se line-height 1.4 místo 1.6

### Nízký VISUAL_DENSITY (3-)
- Max 3 cards per row
- Generous padding (`p-8` nebo `p-12`)
- Sekce min `py-32`

### Vysoký ART_DIRECTION (7+)
- Hero archetype Giant nebo unusual anchor (#3, #6, #12)
- Allow unusual color combinations (within theme palette)
- Mix typographic weights bolder

### Nízký ART_DIRECTION (3-)
- Hero archetype Mid (safest)
- Standard anchors (#1, #4, #7)
- Konzervativní typographic palette

### Vysoký CONVERSION_DISCIPLINE (8+)
- CTA above the fold
- Pricing sekce vidí klient bez scroll na desktop
- Trust signals (logos, testimonials) v top 50% stránky
- Repeat CTA každé 2-3 sekce

### Nízký CONVERSION_DISCIPLINE (3-)
- Hero může být pure manifesto bez CTA
- CTA až v poslední sekci
- Content > sales
