# Style Directive — sestavení konzistentní vizuální direktivy

Style Directive je **jeden textový blok**, který se aplikuje do KAŽDÉHO image promptu napříč celým magnetem. Zajišťuje vizuální konzistenci — všechny stránky vypadají jako jedna kniha, ne jako 10 nesouvisejících obrázků.

Sestavuje se v Kroku 1 workflow z **brandové vizuální knihovny** (NE z DESIGN.md).

---

## Vstupní zdroje

V tomto pořadí priority:

1. **brand-board.png** (POVINNÝ) — moodboard značky, primární vizuální zdroj
2. **brand-kit/08-inspirace-pro-pdf-materialy.png** (KRITICKÝ pro PDF kontext) — definuje layout language pro PDF materiály
3. **brand-kit/*.png** ostatní mockupy — sekundární reference per use case (viz `kit-mapping.md`)
4. **brandDNA.md** sekce 1 (ESENCE) + sekce 5 (HLAS) + sekce 7 (SHRNUTÍ) — text kontext pro mood adjektiva
5. **products/[slug]/images/** — produktové fotky pro reuse v relevantních stránkách

**NIKDY** nepoužívej DESIGN.md — design tokeny (HEX, fonty, spacing) jsou doménou `html_lead_magnet_generator`. Tady pracujeme s **vizuálním jazykem**, ne design system.

---

## Extrakce z brand-board.png

Otevři `brand-board.png` a vizuálně analyzuj. Zaznamenej:

### Color palette

3-5 dominantních barev z brand boardu. Pokud jsou viditelné swatche s HEX kódy, přepiš je. Jinak odhadni HEX z obrázku (Photoshop eyedropper nebo přes PIL):

```python
from PIL import Image
img = Image.open("/documents/brand/brand-board.png")
img_small = img.resize((200, 200))
colors = img_small.getcolors(40000)
top_5 = sorted(colors, reverse=True)[:5]
# Vyfiltruj near-white a near-black, ponech distinct hue colors
```

Klasifikace:
- **Primary** — nejvíce výrazná, brand-defining barva (logo color, hero accent)
- **Secondary** — komplementární, pozadí v některých částech
- **Accent** — pro CTA tlačítka, číslice, highlights
- **Neutral light** — typicky off-white, cream, paper texture
- **Neutral dark** — typicky deep navy nebo near-black pro typography

### Typography style

Z brand-board pozoruj nadpisy a body text. Klasifikuj:

| Pozorování | Display font kategorie | Body font kategorie |
|-------------|-------------------------|----------------------|
| Tenké, elegantní serif | "Playfair Display" / "GT Sectra" / Didone | Sans-serif komplement (Inter) |
| Bold, condensed sans | "Archivo Black" / "Inter Black" | "Inter" / "Space Grotesk" |
| Mixed (display serif + body sans) | Editorial style (NYT, Gentlewoman) | Clean grotesk |
| Tech/geometric sans | "Space Grotesk" / "Manrope" | Stejný font v lighter weight |
| Handwritten accent | Display script | Clean serif body |

**Konkrétní fonty NEZADÁVEJ** — GPT Image 2 nedokáže vždy přesně replikovat licencované fonty. Místo toho použij **kategorické popisy**:

```
Display: bold modern sans-serif (Inter Black or similar weight)
Body: clean grotesk sans-serif (Inter Regular or similar)
```

### Visual language patterns

Z brand-board zaznamenej:

- **Geometry**: rounded vs sharp corners (border-radius). Brand-board s mockupy zařízení zaoblených → rounded; brand s ostrými čárami a boxy → sharp
- **Layering**: flat (Material design) vs. depth (gradient meshes, glow, shadow)
- **Spacing**: dense informational (technical brands) vs. generous editorial (premium brands)
- **Photography style**: studio product shots / candid lifestyle / abstract gradients / editorial portraits / 3D renders
- **Decorative elements**: subtle accent lines, dividers, ornaments, geometric shapes, halftones

### Mood adjectives

Z brand DNA sekce 1+5+7 vytáhni 3-5 adjektiv, která definují mood. Příklady mappingu:

| Brand DNA tón | Mood adjectives pro prompt |
|----------------|------------------------------|
| Empatický, hřejivý | warm, organic, soft, intimate |
| Sebevědomý, energický | bold, confident, kinetic, decisive |
| Klidný, prémiový | calm, sophisticated, refined, elevated |
| Tech, futuristic | sleek, precise, modern, computational |
| Editorial, intelektuální | thoughtful, considered, literary, cultured |

---

## Extrakce z brand-kit/08-inspirace-pro-pdf-materialy.png

Pokud existuje, je to **KRITICKÝ ZDROJ** pro PDF layout language. Tento soubor obvykle obsahuje 6-12 mockupů PDF stránek v různých layoutech (cover, infographic, checklist, process, CTA, atd.).

Z něj extrahuj:

- **Card style**: bordered (s tenkým border), shadow (subtle drop shadow), gradient (gradient background), glassmorphic (frosted glass effect)
- **Number/checkmark treatment**: large numerals (1, 2, 3 jako display element), colored circles (#3 inside circle), gradient fills (number with gradient)
- **Diagram style**: circular flow (cycle s arrows), linear timeline (horizontal s milestones), split comparison (50/50 columns), tree (root + branches)
- **Section dividers**: thin colored line, gradient bar, geometric ornament
- **CTA panels**: solid color block (full bleed), gradient (linear or radial), glassmorphic (with backdrop blur)
- **Header/footer treatment**: minimal label + page number, brand mark + accent line, none

Tyto patterns se promítnou do **PDF-SPECIFIC LAYOUT LANGUAGE** sekce style directive.

---

## Reference brandy pro mood mapping

V style directive uveď **1-2 reference brandy**, jejichž estetiku odpovídá brandu. GPT Image 2 zná tyto brand aesthetics z tréninkových dat a aplikuje je. Vyber podle brand mood:

| Brand mood (z DNA) | Reference brandy v promptu |
|---------------------|------------------------------|
| Premium, sofistikovaný | "Phaidon book design, Wallpaper Magazine layouts, Apple Annual Report aesthetic" |
| Editorial, intelektuální | "NYT Magazine feature spreads, The Gentlewoman editorial, Monocle layouts" |
| Tech, futuristic | "Linear product documentation, Stripe PDFs, Vercel guides aesthetic" |
| Warm, organický | "Aesop catalogue, Le Labo product cards, Loewe Foundation publications" |
| Bold, energetický | "Nike Annual Report, MrBeast brand deck, Hormozi $100M Leads PDF aesthetic" |
| Healing, terapeutický | "Glossier brand book, Calm app design, Goop magazine layouts" |

---

## Šablona výstupní Style Directive

Sestav přesně v této struktuře. **Zachovej všechny sekce, i když některé jsou prázdné.**

```
═══ STYLE DIRECTIVE ═══

COLOR PALETTE:
- Primary: #XXXXXX (description, e.g. "deep navy")
- Secondary: #XXXXXX (e.g. "warm cream")
- Accent: #XXXXXX (e.g. "electric blue")
- Neutral light: #XXXXXX (e.g. "off-white #fafaf8")
- Neutral dark: #XXXXXX (e.g. "near-black #0a0e1a")

TYPOGRAPHY:
- Display: {category} (e.g. "bold modern sans-serif, Inter Black weight")
- Body: {category} (e.g. "clean grotesk sans, Inter Regular weight")
- Hierarchy: Display 60-80pt for hero, body 11-12pt for paragraphs, generous line-height

VISUAL LANGUAGE:
- Geometry: {rounded/sharp/mixed}, {description}
- Layering: {flat/depth}, {gradient/shadow/glow style if any}
- Spacing: {dense/generous}, {whitespace philosophy}
- Photography: {style description, e.g. "editorial candid lifestyle, natural light, warm tones"}
- Decorative: {accent elements, e.g. "subtle thin gold lines, geometric corners"}

MOOD: {3-5 adjectives}

REFERENCE AESTHETIC: "{1-2 brand references}"

PDF-SPECIFIC LAYOUT LANGUAGE (z 08-inspirace-pro-pdf-materialy.png):
- Card style: {bordered/shadow/gradient/glassmorphic}
- Numerals: {treatment description}
- Diagrams: {style preferences}
- CTA panels: {style preferences}

CZECH TEXT REQUIREMENT:
Render Czech text with full diacritics correctly: á é í ó ú ů ý č ď ě ň ř š ť ž
═══ END STYLE DIRECTIVE ═══
```

Tento blok se vloží **na začátek každého image promptu** (před layout-specific instrukce).

---

## Příklad sestavení (CliqSales AI Akcelerátor)

**Vstupy:**
- brand-board.png — tmavé pozadí, glow blue accents, professional clean mockups, deep navy + electric cyan + bright blue palette
- brandDNA.md — esence: "AI tým za 7 týdnů", tón: konfrontačně-sebejistý
- 08-inspirace-pro-pdf-materialy.png — clean cards s thin borders, large numerals, circular flow diagrams, dark navy + cyan gradient CTA panels

**Výstup Style Directive:**

```
═══ STYLE DIRECTIVE ═══

COLOR PALETTE:
- Primary: #0a0e1a (deep navy near-black)
- Secondary: #5b8cff (electric blue)
- Accent: #c4d4ff (light blue glow)
- Neutral light: #f5f6fa (off-white)
- Neutral dark: #131829 (slightly lighter navy for cards)

TYPOGRAPHY:
- Display: bold modern sans-serif, geometric (Space Grotesk Bold or Inter Black weight)
- Body: clean grotesk sans (Inter Regular weight)
- Hierarchy: Display 60-80pt for hero, body 11-12pt for paragraphs, tight letter-spacing on display

VISUAL LANGUAGE:
- Geometry: subtly rounded corners (8-16pt radius), precise grid alignment
- Layering: depth via subtle gradient meshes and blue glow accents, dark backgrounds
- Spacing: generous whitespace on dark backgrounds, clean breathing room
- Photography: tech-savvy product mockups, editorial portraits with cyan studio lighting
- Decorative: thin cyan accent lines, gradient dividers, subtle glow on key elements

MOOD: confident, decisive, futuristic, professional, premium-tech

REFERENCE AESTHETIC: "Linear product documentation meets Stripe PDF guides — clean, technical, but premium and confident"

PDF-SPECIFIC LAYOUT LANGUAGE:
- Card style: bordered with thin cyan accent line on top, dark navy background
- Numerals: large geometric display, gradient cyan-to-light-blue fill
- Diagrams: circular flow with cyan-glowing connection lines
- CTA panels: full-bleed gradient (navy → bright cyan diagonal), white CTA button with sharp corners

CZECH TEXT REQUIREMENT:
Render Czech text with full diacritics correctly: á é í ó ú ů ý č ď ě ň ř š ť ž
═══ END STYLE DIRECTIVE ═══
```

---

## Kontrola konzistence

Po sestavení Style Directive ji **zkontroluj proti brand-board** přes vizuální comparison:

- Pokud brand-board je tmavý → Style Directive musí mít dark neutral light
- Pokud brand-board má rounded corners → musí být v Geometry sekci
- Pokud brand-board má specifické fotografie → musí být reflektováno v Photography
- Pokud 08-inspirace má specifické card style → musí být v PDF-SPECIFIC LAYOUT

Style Directive je **závazek** — všechny stránky budou v tomto stylu. Pokud nejsi jistý/á, požádej uživatele o validaci před generováním.
