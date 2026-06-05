# DESIGN.md Format Specification

Based on the [Google design.md open-source spec](https://github.com/google-labs-code/design.md/blob/main/docs/spec.md). A DESIGN.md file is a self-contained, plain-text representation of a design system. It defines the visual identity of a brand and product, ensuring stylistic choices are followed across design sessions and between different AI agents and tools.

A DESIGN.md file contains two parts: an optional YAML frontmatter with machine-readable design tokens, and a markdown body with human-readable design rationale and guidance.

---

## YAML Frontmatter: Design Tokens

Design tokens are embedded as YAML front matter at the beginning of the file. The block begins with `---` and ends with `---`. The token system is inspired by the [W3C Design Token JSON spec](https://www.designtokens.org/tr/2025.10/format/#abstract) — typed token groups (colors, typography, spacing) with `{path.to.token}` reference syntax.

### Schema

```yaml
version: <string>          # optional, current version: "alpha"
name: <string>             # required — design system name
description: <string>      # optional
colors:
  <token-name>: <Color>
typography:
  <token-name>: <Typography>
rounded:
  <scale-level>: <Dimension>
spacing:
  <scale-level>: <Dimension | number>
components:
  <component-name>:
    <token-name>: <string | token reference>
```

### Value Types

**Color**: Must start with `#` followed by a hex color code in SRGB color space. Example: `"#1A1C1E"`.

**Dimension**: A string with a unit suffix. Valid units: `px`, `em`, `rem`. Example: `"48px"`, `"-0.02em"`.

**Typography**: An object with these properties:
- `fontFamily` (string) — required
- `fontSize` (Dimension) — required
- `fontWeight` (number) — e.g., `400`, `700`
- `lineHeight` (Dimension | number) — unitless number = multiplier of fontSize (recommended)
- `letterSpacing` (Dimension)
- `fontFeature` (string) — maps to CSS `font-feature-settings`
- `fontVariation` (string) — maps to CSS `font-variation-settings`

**Scale levels**: Named levels like `xs`, `sm`, `md`, `lg`, `xl`, `full`. Any descriptive string key is valid.

### Token References

Use `{path.to.token}` to cross-reference values. For most token groups, references must point to a primitive value (e.g., `{colors.primary}`), not a group. Within `components`, references to composite values (e.g., `{typography.label-md}`) are permitted.

### Example Frontmatter

```yaml
---
version: alpha
name: Daylight Prestige
colors:
  primary: "#1A1C1E"
  secondary: "#6C7278"
  tertiary: "#B8422E"
  neutral: "#F7F5F2"
typography:
  h1:
    fontFamily: Public Sans
    fontSize: 48px
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -0.02em
  body-md:
    fontFamily: Public Sans
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  label-caps:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1
    letterSpacing: 0.1em
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
    textColor: "{colors.neutral}"
    rounded: "{rounded.md}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.secondary}"
---
```

---

## Markdown Body: 8 Sections

All sections use `##` headings. An optional `#` heading may appear for document titling. Sections MUST appear in this order. Sections can be omitted if not relevant, but those present must follow this sequence.

### Section 1: Overview

Also known as "Brand & Style".

**Purpose:** Holistic description of the product's look and feel. Defines brand personality, target audience, and the emotional response the UI should evoke.

**What to include:**
- Opening paragraph: 3-5 sentences describing the overall feel, like an art director's brief
- Whether the design should feel playful or professional, dense or spacious
- Typography philosophy: what fonts are used and why
- Color philosophy: how color is used strategically
- Key characteristics: 7-10 specific technical traits as bullet points

**Tone:** Opinionated, descriptive, almost poetic. This is foundational context for guiding an agent's high-level stylistic decisions when a specific rule or token isn't defined.

### Section 2: Colors

**Purpose:** Define the color palettes for the design system.

**Rules:**
- At least the `primary` palette must be defined
- Additional palettes may be added as needed
- When multiple palettes exist, assign semantic roles
- Common naming convention: `primary`, `secondary`, `tertiary`, `neutral`

**Format per color:**
```markdown
- **Descriptive Name (#hex):** Where and why this color is used. Be specific about context.
```

**Name colors evocatively in prose:** "Deep Sea" not "Background Dark". The prose names map to systematic token names in the frontmatter.

### Section 3: Typography

**Purpose:** Define typography levels with semantic roles.

**Guidelines:**
- Most design systems have 9-15 typography levels
- Use semantic categories: `headline`, `display`, `body`, `label`, `caption`
- Each category may divide into sizes: `small`, `medium`, `large`
- Include font families with rationale for why they create the intended feel

**Must include:**
- Font family descriptions with fallback stacks
- OpenType features if any
- Role descriptions for each typography level

### Section 4: Layout

Also known as "Layout & Spacing".

**Purpose:** Describe the layout and spacing strategy.

**Common approaches:**
- Grid-based layout (fixed or fluid)
- Margins, safe areas, dynamic padding
- 8px spacing scale with 4px half-step

**Must include:**
- Layout model description (fluid grid, fixed-max-width, etc.)
- Spacing scale values
- Grid system specs (max-width, columns, gutter)
- Whitespace philosophy paragraph

### Section 5: Elevation & Depth

Also known as "Elevation".

**Purpose:** How visual hierarchy is conveyed.

**Approaches vary by design style:**
- Shadow-based: define spread, blur, color per level
- Flat designs: explain alternative methods (borders, color contrast, tonal layers)
- Mixed: combine both

**Structure:**
- Elevation levels from deepest to highest
- Exact CSS values for each level
- Philosophy paragraph explaining the approach

### Section 6: Shapes

**Purpose:** Describe how visual elements are shaped.

**Must include:**
- Shape language description (architectural sharpness, soft rounding, etc.)
- Corner radius philosophy
- How shapes define the aesthetic identity
- Consistency rules across component types

### Section 7: Components

**Purpose:** Style guidance for component atoms.

**Common component types:**
- **Buttons**: Primary, secondary, tertiary variants with sizing, padding, and states
- **Chips**: Selection chips, filter chips, action chips
- **Lists**: List items, dividers, leading/trailing elements
- **Tooltips**: Positioning, colors, timing
- **Checkboxes**: Checked, unchecked, indeterminate states
- **Radio buttons**: Selected and unselected states
- **Input fields**: Text inputs, text areas, labels, helper text, error states

**Variants:** Components may have variants for different UI states (active, hover, pressed). Define under related keys: `button-primary`, `button-primary-hover`, `button-primary-active`.

**Component property tokens:**
- `backgroundColor`: Color
- `textColor`: Color
- `typography`: Typography
- `rounded`: Dimension
- `padding`: Dimension
- `size`: Dimension
- `height`: Dimension
- `width`: Dimension

### Section 8: Do's and Don'ts

**Purpose:** Design guardrails — what makes this system unique and what breaks it.

**Format:** Lists with clear Do and Don't items.
- 5-8 items each
- Each item explains WHY, not just WHAT
- Focus on what's unique about THIS system
- Include WCAG contrast guidance (4.5:1 for normal text)

---

## Recommended Token Names (Non-Normative)

These names are commonly used across design systems. Not required but recommended for consistency.

**Colors:** `primary`, `secondary`, `tertiary`, `neutral`, `surface`, `on-surface`, `error`

**Typography:** `headline-display`, `headline-lg`, `headline-md`, `body-lg`, `body-md`, `body-sm`, `label-lg`, `label-md`, `label-sm`

**Rounded:** `none`, `sm`, `md`, `lg`, `xl`, `full`

---

## Consumer Behavior for Unknown Content

| Scenario | Behavior | Example |
|----------|----------|---------|
| Unknown section heading | Preserve; do not error | `## Iconography` |
| Unknown color token name | Accept if value is valid | `surface-container-high: '#ede7dd'` |
| Unknown typography token name | Accept as valid typography | `telemetry-data` |
| Unknown spacing value | Accept; store as string if not a valid dimension | `grid-columns: '5'` |
| Unknown component property | Accept with warning | `borderColor` |
| Duplicate section heading | Error; reject the file | Two `## Colors` headings |
