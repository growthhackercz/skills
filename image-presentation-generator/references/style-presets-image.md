# Style Presets — pro GPT Image 2 (image verze)

Toto je překlad 12 vizuálních témat z `html-presentation-generator` (kde byla jako CSS `:root` proměnné) do **textových style directiv pro GPT Image 2**. Místo CSS popíšeš stejnou estetiku slovy v promptu.

**Jak se preset používá:**
1. Vybere se JEDEN preset (nebo se odvodí z brand-board.png — viz Krok 1 v SKILL.md).
2. Z presetu se sestaví **Style Directive** = konstantní blok, který jde do KAŽDÉHO slide promptu.
3. Style Directive se **nikdy nemění mezi slidy** → vizuální konzistence celého decku, i když se layouty střídají.

**Brand-board má přednost.** Pokud existuje `/documents/brand/brand-board.png`, řídí barvy + mood ten, a preset slouží jen jako doplňkový jazyk (typografický mood, signature prvky). Bez brand-boardu je preset hlavní zdroj.

---

## Šablona Style Directive (výstup tohoto kroku)

```
═══ STYLE DIRECTIVE (konstantní napříč všemi slidy) ═══

COLOR PALETTE:
  Background: [HEX / popis] 
  Primary text: [HEX]
  Accent: [HEX]   (max 1–2 akcenty)
  Neutral: [HEX]

TYPOGRAPHY MOOD:
  Display: [název fontu nebo popis — bold geometric sans / elegant serif / mono]
  Body: [popis]
  Hierarchy: obří display headline, čitelný body, jasný kontrast velikostí

VISUAL LANGUAGE:
  Geometry: [rounded vs sharp, organické vs precizní]
  Depth: [flat vs gradient/glow/shadow]
  Texture: [clean / grain / halftone / scanlines]
  Signature: [signature prvky presetu — viz níže]

MOOD (3–5 adjektiv): [...]
REFERENCE AESTHETIC: [1–2 značky/publikace, jejichž feel chceme]
```

---

## Dark témata

### 1. Bold Signal
- **Vibe:** sebevědomé, bold, moderní, high-impact
- **Palette:** pozadí tmavě grafit `#1a1a1a` s jemným diagonálním gradientem; akcentní barevná karta (oranžová `#FF5722` / coral); text bílý, na kartě téměř černý
- **Typography mood:** ultra-bold geometric sans (à la Archivo Black) pro display, čistý grotesk pro body
- **Signature:** velké sekční číslo (01, 02…), barevná karta jako focal point, grid-based zarovnání, navigační breadcrumbs s opacity stavy
- **Prompt jazyk:** „bold confident editorial slide, dark graphite background, one vibrant accent color block as focal element, oversized section number, heavy geometric sans-serif headline, precise grid alignment, high contrast"

### 2. Electric Studio
- **Vibe:** bold, clean, profesionální, vysoký kontrast
- **Palette:** split bílá/tmavá, elektrická modrá akcent `#4361ee`
- **Typography mood:** Manrope-like bold sans, minimalistické
- **Signature:** dvoupanelový vertikální split, akcentní lišta na hraně panelu, citát jako hero prvek, sebevědomé mezery
- **Prompt jazyk:** „clean two-panel split composition, white and deep-charcoal halves, electric blue accent edge, bold sans-serif, generous confident spacing, professional studio feel"

### 3. Creative Voltage
- **Vibe:** bold, kreativní, energické, retro-modern
- **Palette:** elektrická modrá `#0066ff` + neonová žlutá `#d4ff00` na tmavém `#1a1a2e`
- **Typography mood:** výrazný display (Syne-like) + mono akcenty
- **Signature:** halftone textura, neonové badge/callouty, script akcenty pro kreativní šmrnc
- **Prompt jazyk:** „energetic retro-modern slide, electric blue and neon yellow contrast, halftone texture, neon callout badges, expressive display type, creative editorial energy"

### 4. Dark Botanical
- **Vibe:** elegantní, sofistikované, artistické, prémiové
- **Palette:** velmi tmavé `#0f0f0f`, teplé akcenty (gold `#c9b896`, pink `#e8b4b8`, terracotta `#d4a574`), text krémový `#e8e4df`
- **Typography mood:** elegantní serif (Cormorant-like) display + světlý sans body
- **Signature:** abstraktní rozostřené gradientní kruhy v rohu (NE ilustrace), tenké vertikální akcentní linky, kurzíva pro podpis
- **Prompt jazyk:** „elegant sophisticated dark slide, soft blurred gradient orbs in corner, warm gold and blush accents, refined serif headline, thin vertical accent line, premium editorial mood, abstract shapes only — no illustrations"

---

## Light témata

### 5. Notebook Tabs
- **Vibe:** editoriální, organizované, elegantní, hmatatelné
- **Palette:** krémová „papírová" karta `#f8f6f1` na tmavém pozadí, barevné taby (mint, lavender, pink, sky, cream)
- **Typography mood:** klasický editorial serif (Bodoni-like) + čistý sans body
- **Signature:** papírový container s jemným stínem, barevné sekční taby na pravé hraně (vertikální text), kroužkové děrování vlevo
- **Prompt jazyk:** „editorial notebook aesthetic, cream paper card on dark backdrop with subtle shadow, colorful section tabs on right edge, classic serif headline, tactile organized feel"

### 6. Pastel Geometry
- **Vibe:** přátelské, organizované, moderní, přístupné
- **Palette:** pastelově modré pozadí `#c8d9e6`, off-white karta `#faf9f7`, pastelové piluly (pink, mint, sage, lavender)
- **Typography mood:** Plus Jakarta Sans-like, kulaté
- **Signature:** zaoblená karta s měkkým stínem, vertikální piluly na pravé hraně s různou výškou
- **Prompt jazyk:** „friendly modern slide, rounded off-white card with soft shadow on pastel background, vertical pastel pills on right edge varying heights, rounded geometric sans, approachable"

### 7. Split Pastel
- **Vibe:** hravé, moderní, přátelské, kreativní
- **Palette:** dvoubarevný split (broskvová `#f5e6dc` / levandulová `#e4dff0`), pastelové badge
- **Typography mood:** Outfit-like geometric
- **Signature:** split background, hravé badge piluly s ikonami, grid pattern overlay na jednom panelu, zaoblená CTA tlačítka
- **Prompt jazyk:** „playful two-color split slide, peach and lavender halves, pastel badge pills with icons, subtle grid pattern overlay, rounded buttons, friendly creative mood"

### 8. Vintage Editorial
- **Vibe:** vtipné, sebevědomé, editoriální, s osobností
- **Palette:** krémová `#f5f3ee`, černý text, teplý akcent `#e8d4c0`
- **Typography mood:** výrazný serif (Fraunces-like)
- **Signature:** abstraktní geometrické tvary (obrys kruhu + linka + tečka), bold orámované CTA boxy, konverzační styl
- **Prompt jazyk:** „witty vintage editorial slide, warm cream background, distinctive serif headline, abstract geometric accents (circle outline, line, dot), bold bordered call-out box, personality-driven"

---

## Specialty témata

### 9. Neon Cyber
- **Vibe:** futuristické, techy, sebevědomé
- **Palette:** deep navy `#0a0f1c`, cyan `#00ffcc`, magenta `#ff00aa`
- **Typography mood:** Clash Display-like + clean sans
- **Signature:** částicová pozadí, neonový glow, grid patterny
- **Prompt jazyk:** „futuristic tech slide, deep navy background, cyan and magenta neon glow, subtle particle field and grid pattern, sharp modern display type, high-tech confident mood"

### 10. Terminal Green
- **Vibe:** developerské, hacker estetika
- **Palette:** GitHub dark `#0d1117`, terminálová zelená `#39d353`
- **Typography mood:** monospace (JetBrains Mono-like)
- **Signature:** scan lines, blikající kurzor, code syntax styling
- **Prompt jazyk:** „developer terminal slide, dark code-editor background, terminal green monospace text, subtle scanlines, blinking cursor motif, code syntax styling, hacker aesthetic"

### 11. Swiss Modern
- **Vibe:** čisté, precizní, Bauhaus
- **Palette:** čistá bílá, čistá černá, červený akcent `#ff3300`
- **Typography mood:** Archivo-like heavy sans + clean body
- **Signature:** viditelný grid, asymetrické layouty, geometrické tvary
- **Prompt jazyk:** „Swiss International style slide, pure white, heavy black headline, single red accent, visible structural grid, asymmetric Bauhaus layout, precise geometric shapes"

### 12. Paper & Ink
- **Vibe:** editoriální, literární, promyšlené
- **Palette:** teplá krémová `#faf9f7`, charcoal `#1a1a1a`, crimson akcent `#c41e3a`
- **Typography mood:** Cormorant Garamond-like serif + serif body
- **Signature:** drop caps, pull quotes, elegantní horizontální linky
- **Prompt jazyk:** „literary editorial slide, warm cream paper, elegant serif typography, dramatic drop cap, crimson accent, refined horizontal rules, thoughtful magazine feel"

---

## Font párování (rychlý přehled)

| Preset | Display | Body |
|--------|---------|------|
| Bold Signal | Archivo Black | Space Grotesk |
| Electric Studio | Manrope | Manrope |
| Creative Voltage | Syne | Space Mono |
| Dark Botanical | Cormorant | IBM Plex Sans |
| Notebook Tabs | Bodoni Moda | DM Sans |
| Pastel Geometry | Plus Jakarta Sans | Plus Jakarta Sans |
| Split Pastel | Outfit | Outfit |
| Vintage Editorial | Fraunces | Work Sans |
| Neon Cyber | Clash Display | Satoshi |
| Terminal Green | JetBrains Mono | JetBrains Mono |
| Swiss Modern | Archivo | Nunito |
| Paper & Ink | Cormorant Garamond | Source Serif 4 |

GPT Image 2 fonty negeneruje přesně podle názvu — uváděj je jako **mood** („heavy geometric sans-serif similar to Archivo Black"), ne jako tvrdý požadavek.

---

## NEPOUŽÍVAT (generický AI slop)

- **Fonty (jako mood):** Inter, Roboto, Arial, systémové fonty jako display
- **Barvy:** generický indigo `#6366f1`, fialové gradienty na bílé (typický AI tell)
- **Layouty:** všechno vystředěné, generické hero sekce, identické karetní mřížky
- **Dekorace:** realistické ilustrace, samoúčelný glassmorphism, stíny bez důvodu, stock-photo feel

Tyhle vzorce dej do **negative promptu** každého slidu (viz `slide-layouts.md`).
