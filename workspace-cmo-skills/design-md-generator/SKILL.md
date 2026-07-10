---
name: Design.md Generátor
description: Vygeneruj DESIGN.md z libovolné URL — extrahuje barvy, typografii, spacing, tvary a komponenty do YAML design tokenů + 8 markdown sekcí dle Google design.md spec.
category: creative
status: ready
version: "1.0"
publishedAt: "2026-04-28"
metadata: {"openclaw":{"homepage":"https://github.com/google-labs-code/design.md"}}
---

# Design.md Generátor

Generuje strukturovaný `DESIGN.md` z libovolné webové URL. Výstup dodržuje [Google design.md spec](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md): YAML frontmatter s typovanými design tokeny a 8 standardních markdown sekcí.

## Režim extrakce

Skill podporuje dva režimy extrakce. **Vždy nejdřív zkus Tier 1.** Na Tier 2 přejdi jen tehdy, když browser opravdu není dostupný.

### Tier 1: Plná browser extrakce (preferovaná)

Vyžaduje OpenClaw browser tool s běžícím Chromium. Poskytuje computed styles, renderované screenshoty a plné JavaScript vyhodnocení.

**Detekce:** Spusť `browser doctor` nebo `browser status`. Pokud browser běží a je zdravý, použij tento režim.

**Kroky:**

1. **Otevři stránku:**
   ```
   browser open "<TARGET_URL>"
   ```

2. **Pořiď screenshot** (vizuální kontext pro agenta):
   ```
   browser screenshot
   ```

3. **Získej DOM snapshot** (accessibility tree s refs):
   ```
   browser snapshot
   ```

4. **Extrahuj computed design tokeny přes JavaScript:**
   ```
   browser act evaluate "<EXTRACTION_SCRIPT>"
   ```

   Extrakční script má běžet v kontextu stránky a sesbírat:
   - všechny unikátní barvy z computed styles (background, text, border, accent)
   - font families, sizes, weights, line-heights, letter-spacing
   - border radii, shadows, spacing values
   - CSS custom properties (`:root` variables)
   - komponentové patterny (buttons, cards, inputs, vzorkované z DOM)

   Logika extrakce je v `{baseDir}/scripts/extract-tokens-inline.js`. Obsah scriptu vlož do `evaluate` volání.

5. **Scrolluj a opakuj** pro obsah pod foldem, pokud je potřeba:
   ```
   browser act scroll down
   browser screenshot
   browser snapshot
   ```

### Tier 2: Statický fetch fallback (bez browseru)

Když v runtime není dostupné Chromium, použij HTTP fetch a statickou analýzu. Tento režim poskytne HTML strukturu, linkované/inline CSS a meta tags, ale neposkytne computed styles ani renderované screenshoty.

**Detekce:** `browser doctor` hlásí, že browser nebyl nalezen, nebo `browser status` ukazuje `running: false` bez detekovaného Chromium.

**Kroky:**

1. **Stáhni HTML:**
   ```
   web_fetch url="<TARGET_URL>"
   ```

2. **Najdi linkované stylesheety** z HTML `<link rel="stylesheet">` tagů a stáhni je:
   ```
   web_fetch url="<STYLESHEET_URL>"
   ```

3. **Stáhni 1-2 další stránky** (např. `/about`, `/contact`, `/pricing`) pro širší pokrytí komponent:
   ```
   web_fetch url="<TARGET_URL>/about"
   ```

4. **Parsuj staticky** a extrahuj z raw HTML + CSS:
   - CSS custom properties (`--color-primary`, `--font-size-base` atd.)
   - inline styles a class-based patterny
   - `<link>` fonts (Google Fonts, Adobe Fonts, self-hosted)
   - meta tags, Open Graph colors
   - HTML strukturu (nav, hero, cards, footer patterns)

**Limity Tier 2** zapiš na začátek generovaného `DESIGN.md` jako komentář:
- barvy mohou být neúplné (computed runtime colors nejsou dostupné)
- typografické hodnoty pochází z CSS deklarací, ne z renderovaných computed styles
- stavy komponent (hover, focus, active) mohou chybět
- spacing hodnoty jsou odvozené z CSS, ne měřené z renderovaného layoutu

Při použití Tier 2 vlož na začátek generovaného souboru tuto poznámku:
```markdown
<!-- Generated via static HTML/CSS analysis (no browser). Some values are inferred. -->
```

## Generování DESIGN.md

Z extrahovaných dat (z kteréhokoli režimu) napiš `DESIGN.md` se dvěma částmi:

### Část A: YAML frontmatter (design tokeny)

Soubor MUSÍ začínat YAML frontmatter blokem s typovanými design tokeny. Dodrž toto schema:

```yaml
---
version: alpha
name: "<Design System Name>"
description: "<One-line description>"
colors:
  primary: "#hex"
  secondary: "#hex"
  tertiary: "#hex"
  neutral: "#hex"
  surface: "#hex"
  on-surface: "#hex"
  error: "#hex"
  # Additional color tokens as needed
typography:
  headline-lg:
    fontFamily: Font Name
    fontSize: 48px
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -0.02em
  body-md:
    fontFamily: Font Name
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  label-sm:
    fontFamily: Font Name
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1
    letterSpacing: 0.1em
  # 9-15 typography levels total
rounded:
  sm: 4px
  md: 8px
  lg: 12px
  full: 9999px
spacing:
  base: 16px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 32px
  xl: 64px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.secondary}"
  # Additional component tokens with variants
---
```

**Pravidla tokenů:**
- **Color** hodnoty musí začínat `#` a pokračovat hex kódem (SRGB).
- **Dimension** hodnoty jsou stringy s jednotkou: `px`, `em` nebo `rem`.
- **Typography** objekty obsahují `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing` a volitelně `fontFeature` a `fontVariation`.
- **Token references** používají `{path.to.token}` syntax, např. `"{colors.primary}"`, `"{rounded.md}"`. V sekci `components` jsou povolené reference na kompozitní hodnoty jako `"{typography.label-md}"`.
- **Component variants** používají související klíče: `button-primary`, `button-primary-hover`, `button-primary-active`.

### Část B: Markdown body (8 sekcí)

**Jazyk výstupu: čeština.** Veškerý prose text v markdown sekcích piš česky — popisy, rationale, Do's and Don'ts, filosofie designu. Následující věci zůstávají v angličtině (vyžaduje spec):
- Názvy sekcí (`## Overview`, `## Colors`, `## Typography` atd.) — povinné anglické `##` headingy dle spec
- YAML frontmatter — token names (`primary`, `body-md`, `rounded.sm`), property names (`fontFamily`, `fontSize`), hodnoty (`px`, `em`, `rem`)
- Technické CSS hodnoty, hex kódy, font-feature-settings
- Token reference syntax (`{colors.primary}`, `{rounded.md}`)

Všechny sekce používají `##` headingy a MUSÍ být v tomto pořadí:

| # | Section | Co zachytit |
|---|---------|----------------|
| 1 | **Overview** | Osobnost značky, cílová skupina, emocionální odezva UI. Nálada, hustota, designová filozofie. Piš jako art director popisující estetiku. |
| 2 | **Colors** | Barevné palety se sémantickými rolemi. Každá paleta má název a hex. Popiš KDE a PROČ se každá barva používá. |
| 3 | **Typography** | Typografické úrovně se sémantickými rolemi. Font families s odůvodněním. Každá úroveň s popisem role a kdy se používá. |
| 4 | **Layout** | Model layoutu (fluid grid, fixed-max-width atd.), strategie spacingu, grid systém, filozofie whitespace. |
| 5 | **Elevation & Depth** | Jak se vyjadřuje vizuální hierarchie — stíny, tónové vrstvy, bordery, barevný kontrast. Definuj úrovně elevace s přesnými hodnotami. |
| 6 | **Shapes** | Tvarový jazyk — filozofie corner radius, jak tvary definují estetiku. Ostré vs. zaoblené, pravidla konzistence. |
| 7 | **Components** | Buttony (primary/secondary/ghost), chipy, listy, tooltipy, checkboxy, radio buttony, input fieldy — se všemi stavy a variantami. |
| 8 | **Do's and Don'ts** | Designové mantinely. Co dělá tento systém unikátním a co ho rozbíjí. Zahrň WCAG kontrastní pravidla. |

### Pravidla psaní

- **Piš česky**: Veškerý prose v markdown sekcích je v češtině. Angličtina pouze pro povinné technické identifikátory (section headings, token names, CSS hodnoty).
- **Prose + tokeny spolu**: Markdown body poskytuje lidsky čitelné zdůvodnění a návod. YAML frontmatter poskytuje strojově čitelné hodnoty. Obojí musí být konzistentní.
- **Popisné názvy barev v prose**: Používej evokativní české názvy ("Půlnoční lesní zelená") které mapují na systematické anglické token names (`primary`) ve frontmatteru.
- **Buď konkrétní**: Přesné hex hodnoty, px velikosti, font weights — ne "tmavě modrá" nebo "velký text".
- **Buď názorový**: Popisuj atmosféru jako designový kritik, ne jako specifikace.
- **Zahrň stavy**: Každá interaktivní komponenta potřebuje default + hover + active + focus stavy.
- **Ukaž hierarchii**: Povrchy od nejhlubšího po nejvyšší, text od nejjasnějšího po nejtmavší.
- **Token reference v komponentách**: Používej `{colors.primary}` syntax v sekci components pro odkazování na tokeny definované jinde.

### Výstup

Ulož vygenerovaný soubor jako `DESIGN.md` do složky `/documents/brand/`. Pokud složka neexistuje, vytvoř ji. Výsledná cesta:

```
/documents/brand/DESIGN.md
```

`DESIGN.md` musí být přímo převoditelný do `tokens.json` (W3C Design Token JSON spec), Figma variables a Tailwind theme configů.

## Reference

Kompletní specifikace sekcí a YAML schematu je v `references/format-spec.md`.

Kvalitní příklad výstupu je v `references/example-linear.md` (Linear `DESIGN.md` v novém formátu).
