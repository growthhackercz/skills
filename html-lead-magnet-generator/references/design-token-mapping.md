# DESIGN.md → CSS Variables Mapping

Kompletní 1:1 mapování YAML frontmatteru DESIGN.md na CSS proměnné v `:root` HTML šablony.

---

## Colors

| DESIGN.md path | CSS variable | Fallback |
|----------------|--------------|----------|
| `colors.primary` | `--color-primary` | `#08090a` |
| `colors.secondary` | `--color-secondary` | `#f7f8f8` |
| `colors.tertiary` / `colors.accent` | `--color-accent` | `#5e6ad2` |
| `colors.text` | `--color-text` | `var(--color-primary)` |
| `colors.text-muted` / `colors.gray-600` | `--color-text-muted` | `#6b7280` |
| `colors.bg` / `colors.background` | `--color-bg` | `#ffffff` |
| `colors.bg-subtle` / `colors.gray-50` | `--color-bg-subtle` | `var(--color-secondary)` |
| `colors.success` | `--color-success` | `#10b981` |
| `colors.warning` | `--color-warning` | `#f59e0b` |
| `colors.error` | `--color-error` | `#ef4444` |
| `colors.border` | `--color-border` | `#e5e7eb` |

**Pravidla:**
- Hex hodnoty převést na lowercase
- Pokud DESIGN.md používá custom názvy (např. `colors.midnight`), namapuj na nejbližší sémantickou proměnnou
- Pokud nelze namapovat, vytvoř custom proměnnou: `--color-midnight: #08090a;`

---

## Typography

### Font families

| DESIGN.md path | CSS variable | Fallback |
|----------------|--------------|----------|
| `typography.display-xl.fontFamily` | `--font-display` | `system-ui, sans-serif` |
| `typography.body-md.fontFamily` | `--font-body` | `system-ui, sans-serif` |
| `typography.code.fontFamily` | `--font-mono` | `monospace` |

**Vždy přidej fallback fonty do font-family:**
```css
--font-display: "Inter Variable", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
```

### Font sizes (převést na pt pro print)

`px → pt`: `pt = px × 0.75`

| DESIGN.md typography token | CSS variable | Fallback |
|----------------------------|--------------|----------|
| `typography.display-xl.fontSize` | `--fs-display` | `48pt` |
| `typography.heading-1.fontSize` | `--fs-h1` | `28pt` |
| `typography.heading-2.fontSize` | `--fs-h2` | `20pt` |
| `typography.heading-3.fontSize` | `--fs-h3` | `14pt` |
| `typography.body-md.fontSize` | `--fs-body` | `11pt` |
| `typography.body-sm.fontSize` | `--fs-small` | `9pt` |

### Line heights

| DESIGN.md path | CSS variable | Fallback |
|----------------|--------------|----------|
| `typography.display-xl.lineHeight` | `--lh-tight` | `1.1` |
| `typography.body-md.lineHeight` | `--lh-normal` | `1.5` |
| (custom) | `--lh-loose` | `1.7` |

### Letter spacing

| DESIGN.md path | CSS variable | Fallback |
|----------------|--------------|----------|
| `typography.display-xl.letterSpacing` | `--ls-display` | `-0.022em` |
| `typography.body-md.letterSpacing` | `--ls-body` | `0` |

### Font weights

| DESIGN.md path | CSS variable | Fallback |
|----------------|--------------|----------|
| `typography.body-md.fontWeight` | `--fw-normal` | `400` |
| `typography.heading-3.fontWeight` | `--fw-medium` | `500` |
| `typography.heading-1.fontWeight` | `--fw-semibold` | `600` |
| `typography.display-xl.fontWeight` | `--fw-bold` | `700` |

---

## Spacing

DESIGN.md `spacing` scale (typicky 0, 1, 2, 3, 4, 5, 6, 8, 12, 16):

| DESIGN.md path | CSS variable | Fallback (pt) |
|----------------|--------------|----------------|
| `spacing.1` | `--space-1` | `4pt` |
| `spacing.2` | `--space-2` | `8pt` |
| `spacing.3` | `--space-3` | `12pt` |
| `spacing.4` | `--space-4` | `16pt` |
| `spacing.5` | `--space-5` | `20pt` |
| `spacing.6` | `--space-6` | `24pt` |
| `spacing.8` | `--space-8` | `32pt` |
| `spacing.12` | `--space-12` | `48pt` |
| `spacing.16` | `--space-16` | `64pt` |

**Konverze px → pt** stejná jako u typography.

---

## Rounded (border-radius)

| DESIGN.md path | CSS variable | Fallback |
|----------------|--------------|----------|
| `rounded.sm` | `--radius-sm` | `4pt` |
| `rounded.md` | `--radius-md` | `8pt` |
| `rounded.lg` | `--radius-lg` | `16pt` |
| `rounded.full` | `--radius-full` | `9999pt` |

---

## Shadow / Elevation

DESIGN.md `elevation` nebo `shadow`:

| DESIGN.md path | CSS variable | Fallback |
|----------------|--------------|----------|
| `elevation.1` | `--shadow-sm` | `0 1pt 2pt rgba(0,0,0,0.05)` |
| `elevation.2` | `--shadow-md` | `0 4pt 6pt rgba(0,0,0,0.1)` |
| `elevation.3` | `--shadow-lg` | `0 10pt 15pt rgba(0,0,0,0.1)` |

---

## Components (komponentové tokeny)

Pokud DESIGN.md má `components` sekci, mapuj sémanticky:

```yaml
# DESIGN.md
components:
  button-primary:
    background: "{colors.accent}"
    color: "#ffffff"
    padding: "{spacing.3} {spacing.4}"
    radius: "{rounded.md}"
```

→ `:root` (pokud potřebné)
→ Nebo přímo do CSS třídy `.btn-primary { ... }` v šabloně.

---

## Edge cases

### DESIGN.md neexistuje

→ Použij **kompletní fallback set** z této reference. Skill nesmí spadnout. Loguj warning.

### Custom token názvy

→ Vytvoř custom CSS proměnné, ale namapuj i na sémantické (alias):
```css
:root {
  --color-midnight: #08090a;
  --color-primary: var(--color-midnight); /* alias */
}
```

### Webfonty z DESIGN.md

Pokud `typography.display-xl.fontFamily` obsahuje fontu, která není system-ui:
1. Detekuj, jestli je to Google Font (Inter, Roboto, Plus Jakarta, atd.)
2. Pokud ano, přidej do `<head>` šablony:
   ```html
   <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
   ```
3. Pokud ne, předpokládej, že je system fonta — nech fallback chain.

### Dark mode v DESIGN.md

Lead magnet PDF je **vždy light mode** (print). Pokud DESIGN.md má dark theme jako primární, použij `colors.bg = #ffffff` a invertuj logicky text.

---

## Validační checklist

Po mapování ověř:

- [ ] Všechny CSS proměnné v `:root` mají hodnotu (žádné `undefined`)
- [ ] Font sizes jsou v `pt` (ne `px` ani `rem`)
- [ ] Spacing je v `pt`
- [ ] Webfonty jsou loaded v `<head>`
- [ ] Žádné CSS proměnné nereferencují cyklicky
