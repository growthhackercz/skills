---
version: alpha
name: Linear Dark
description: Ultra-minimal dark-mode-first product design with indigo-violet accent and Inter Variable typography
colors:
  primary: "#08090a"
  primary-10: "#0f1011"
  primary-20: "#191a1b"
  primary-30: "#28282c"
  secondary: "#f7f8f8"
  secondary-60: "#d0d6e0"
  secondary-40: "#8a8f98"
  secondary-20: "#62666d"
  tertiary: "#5e6ad2"
  tertiary-60: "#7170ff"
  tertiary-80: "#828fff"
  neutral: "#23252a"
  neutral-60: "#34343a"
  neutral-80: "#3e3e44"
  surface: "#010102"
  on-surface: "#f7f8f8"
  error: "#e5484d"
  success: "#27a644"
  success-alt: "#10b981"
typography:
  display-xl:
    fontFamily: Inter Variable
    fontSize: 72px
    fontWeight: 510
    lineHeight: 1.0
    letterSpacing: -0.022em
    fontFeature: '"cv01", "ss03"'
  display-lg:
    fontFamily: Inter Variable
    fontSize: 64px
    fontWeight: 510
    lineHeight: 1.0
    letterSpacing: -0.022em
    fontFeature: '"cv01", "ss03"'
  display-md:
    fontFamily: Inter Variable
    fontSize: 48px
    fontWeight: 510
    lineHeight: 1.0
    letterSpacing: -0.022em
    fontFeature: '"cv01", "ss03"'
  headline-lg:
    fontFamily: Inter Variable
    fontSize: 32px
    fontWeight: 400
    lineHeight: 1.13
    letterSpacing: -0.022em
    fontFeature: '"cv01", "ss03"'
  headline-md:
    fontFamily: Inter Variable
    fontSize: 24px
    fontWeight: 400
    lineHeight: 1.33
    letterSpacing: -0.012em
    fontFeature: '"cv01", "ss03"'
  headline-sm:
    fontFamily: Inter Variable
    fontSize: 20px
    fontWeight: 590
    lineHeight: 1.33
    letterSpacing: -0.012em
    fontFeature: '"cv01", "ss03"'
  body-lg:
    fontFamily: Inter Variable
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: -0.009em
    fontFeature: '"cv01", "ss03"'
  body-md:
    fontFamily: Inter Variable
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: '"cv01", "ss03"'
  body-sm:
    fontFamily: Inter Variable
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: -0.011em
    fontFeature: '"cv01", "ss03"'
  label-lg:
    fontFamily: Inter Variable
    fontSize: 14px
    fontWeight: 510
    lineHeight: 1.5
    letterSpacing: -0.013em
    fontFeature: '"cv01", "ss03"'
  label-md:
    fontFamily: Inter Variable
    fontSize: 13px
    fontWeight: 510
    lineHeight: 1.5
    letterSpacing: -0.01em
    fontFeature: '"cv01", "ss03"'
  label-sm:
    fontFamily: Inter Variable
    fontSize: 12px
    fontWeight: 510
    lineHeight: 1.4
    fontFeature: '"cv01", "ss03"'
  code-md:
    fontFamily: Berkeley Mono
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  code-sm:
    fontFamily: Berkeley Mono
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
rounded:
  xs: 2px
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
  2xl: 22px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 64px
  section: 80px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: 8px 16px
  button-primary-hover:
    backgroundColor: "{colors.tertiary-80}"
  button-ghost:
    backgroundColor: "rgba(255,255,255,0.02)"
    textColor: "{colors.secondary-60}"
    rounded: "{rounded.md}"
    padding: 8px 16px
  button-ghost-hover:
    backgroundColor: "rgba(255,255,255,0.05)"
  button-icon:
    backgroundColor: "rgba(255,255,255,0.03)"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.full}"
  card:
    backgroundColor: "rgba(255,255,255,0.02)"
    rounded: "{rounded.lg}"
    padding: 24px
  input:
    backgroundColor: "rgba(255,255,255,0.02)"
    textColor: "{colors.secondary-60}"
    rounded: "{rounded.md}"
    padding: 12px 14px
  badge-success:
    backgroundColor: "{colors.success-alt}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.full}"
  badge-neutral:
    backgroundColor: "transparent"
    textColor: "{colors.secondary-60}"
    rounded: "{rounded.full}"
    padding: 0px 10px
---

# Design System: Linear

## Overview

Linear's website is a masterclass in dark-mode-first product design — a near-black canvas where content emerges from darkness like starlight. The overall impression is one of extreme precision engineering: every element exists in a carefully calibrated hierarchy of luminance, from barely-visible borders to soft, luminous text. This is not a dark theme applied to a light design — it is darkness as the native medium, where information density is managed through subtle gradations of white opacity rather than color variation.

The typography system is built entirely on Inter Variable with OpenType features `"cv01"` and `"ss03"` enabled globally, giving the typeface a cleaner, more geometric character. Inter is used at a remarkable range of weights — from 300 (light body) through 510 (medium, Linear's signature weight) to 590 (semibold emphasis). The 510 weight is particularly distinctive: it sits between regular and medium, creating a subtle emphasis that doesn't shout. At display sizes (72px, 64px, 48px), Inter uses aggressive negative letter-spacing, creating compressed, authoritative headlines that feel engineered rather than designed. Berkeley Mono serves as the monospace companion for code and technical labels.

The color system is almost entirely achromatic — dark backgrounds with white/gray text — punctuated by a single brand accent: Linear's signature indigo-violet. This accent is used sparingly and intentionally, appearing only on CTAs, active states, and brand elements. The border system uses ultra-thin, semi-transparent white borders that create structure without visual noise, like wireframes drawn in moonlight.

**Key Characteristics:**
- Dark-mode-native: Marketing Black (`#08090a`) background, Panel Dark (`#0f1011`) panels, Surface (`#191a1b`) elevated elements
- Inter Variable with `"cv01", "ss03"` globally — geometric alternates for a cleaner aesthetic
- Signature weight 510 (between regular and medium) for most UI text
- Aggressive negative letter-spacing at display sizes
- Brand Indigo Violet (`#5e6ad2` / `#7170ff`) — the only chromatic color in the system
- Semi-transparent white borders throughout: `rgba(255,255,255,0.05)` to `rgba(255,255,255,0.08)`
- Button backgrounds at near-zero opacity: `rgba(255,255,255,0.02)` to `rgba(255,255,255,0.05)`
- Radix UI primitives as the component foundation

## Colors

The palette is rooted in high-contrast achromatic neutrals and a single, evocative accent color.

- **Marketing Black (#08090a):** The deepest background — the canvas for hero sections and marketing pages. Near-pure black with an imperceptible cool undertone.
- **Panel Dark (#0f1011):** Sidebar and panel backgrounds. One step up from marketing black.
- **Elevated Surface (#191a1b):** Card backgrounds, dropdowns, elevated areas.
- **Secondary Surface (#28282c):** Hover states, slightly elevated components — the lightest dark surface.
- **Primary Text (#f7f8f8):** Near-white with a barely-warm cast. The default text color — not pure white, preventing eye strain.
- **Secondary Text (#d0d6e0):** Cool silver-gray for body text, descriptions, secondary content.
- **Tertiary Text (#8a8f98):** Muted gray for placeholders, metadata, de-emphasized content.
- **Quaternary Text (#62666d):** The most subdued — timestamps, disabled states, subtle labels.
- **Brand Indigo (#5e6ad2):** Primary brand color for CTA backgrounds, brand marks, key interactive surfaces.
- **Accent Violet (#7170ff):** Brighter variant for interactive elements — links, active states, selected items.
- **Accent Hover (#828fff):** Lighter, more saturated variant for hover states on accent elements.
- **Success Green (#27a644):** Primary success/active status. Used for "in progress" indicators.
- **Emerald (#10b981):** Secondary success — pill badges, completion states.
- **Border Primary (#23252a):** Solid dark border for prominent separations.
- **Border Subtle (rgba(255,255,255,0.05)):** Ultra-subtle semi-transparent — the default border.
- **Border Standard (rgba(255,255,255,0.08)):** Standard semi-transparent border for cards, inputs, code blocks.

## Typography

The typography strategy leverages Inter Variable as the sole sans-serif with OpenType features `"cv01"` (single-story lowercase 'a') and `"ss03"` (cleaner geometric letterforms) enabled on all text. Berkeley Mono serves as the monospace companion for code and technical labels, with fallbacks to ui-monospace, SF Mono, and Menlo.

- **Display (72–48px):** Inter Variable weight 510 with aggressive negative letter-spacing (-0.022em). These compressed, authoritative headlines feel engineered, not designed.
- **Headlines (32–20px):** Weights 400 to 590 with gradually relaxing letter-spacing. Used for section titles and feature cards.
- **Body (18–15px):** Weight 400 at relaxed line-heights (1.5–1.6). The reading voice of the system — clear, unhurried.
- **Labels (14–12px):** Weight 510 — Linear's signature "between-weight." Used for navigation, metadata, and UI chrome.
- **Code (14–13px):** Berkeley Mono weight 400. Reserved for code blocks, technical data, timestamps.

**Principles:**
- 510 is the signature weight — between regular (400) and medium (500), it creates subtle emphasis without heaviness.
- Compression at scale: display sizes use progressively tighter letter-spacing. Below 16px, spacing relaxes toward normal.
- Three-tier weight system: 400 (read), 510 (emphasize/navigate), 590 (announce). Weight 300 appears only in deliberately de-emphasized contexts.

## Layout

The layout follows a centered, single-column model for hero and marketing content with a max content width of approximately 1200px. Feature sections use 2-3 column grids for cards, with full-width dark sections constrained by internal max-width.

A base 8px spacing scale provides consistent rhythm. Primary values: 8px, 16px, 24px, 32px. The 4px half-step handles micro-adjustments for optical alignment. Section-level separation uses generous vertical padding (80px+) with no visible dividers — the dark background provides natural separation.

**Whitespace Philosophy:** On Linear's dark canvas, empty space isn't white — it's absence. The near-black background IS the whitespace, and content emerges from it. Display text at 72px with tight tracking is dense and compressed, but sits within vast dark padding. The contrast between typographic density and spatial generosity creates tension.

## Elevation & Depth

Depth is achieved through **tonal layers** rather than heavy shadows. On dark surfaces, traditional shadows (dark on dark) are nearly invisible. Linear solves this by using semi-transparent white borders as the primary depth indicator and background luminance stepping — each level slightly increases the white opacity of the surface background.

- **Level 0 (Flat):** No shadow, `#010102` background — the deepest canvas.
- **Level 1 (Subtle):** `rgba(0,0,0,0.03) 0px 1.2px 0px` — toolbar buttons, micro-elevation.
- **Level 2 (Surface):** `rgba(255,255,255,0.05)` background + `1px solid rgba(255,255,255,0.08)` border — cards, inputs, containers.
- **Level 2b (Inset):** `rgba(0,0,0,0.2) 0px 0px 12px 0px inset` — recessed panels, inner shadows.
- **Level 3 (Ring):** `rgba(0,0,0,0.2) 0px 0px 0px 1px` — border-as-shadow technique.
- **Level 4 (Elevated):** `rgba(0,0,0,0.4) 0px 2px 4px` — floating elements, dropdowns.
- **Level 5 (Dialog):** Multi-layer shadow stack — popovers, command palette, modals.

Elevation isn't communicated through shadow darkness but through background luminance steps: `rgba(255,255,255, 0.02 → 0.04 → 0.05)`, creating a subtle stacking effect.

## Shapes

The shape language is defined by **functional minimalism**. Interactive elements use a tight 6px corner radius — just enough softness to feel modern while maintaining precision. Cards step up to 8px, panels to 12px, and large featured elements to 22px. The system uses 9999px for pills and full-circle for icon buttons.

- **Micro (2px):** Inline badges, toolbar buttons, subtle tags.
- **Standard (4px):** Small containers, list items.
- **Comfortable (6px):** Buttons, inputs, functional elements — the workhorse radius.
- **Card (8px):** Cards, dropdowns, popovers.
- **Panel (12px):** Panels, featured cards, section containers.
- **Large (22px):** Large panel elements.
- **Pill (9999px):** Chips, filter pills, status tags.
- **Circle (50%):** Icon buttons, avatars, status dots.

The hierarchy is intentional: smaller radii for denser, more functional UI; larger radii for spatial, visual elements. Sharp corners (0px) are never used — even the smallest element has 2px rounding.

## Components

### Buttons

**Primary Brand Button:** Background `{colors.tertiary}` (brand indigo), white text, 6px radius, 8px 16px padding. Hover shifts to `{colors.tertiary-80}`. Used for primary CTAs ("Start building", "Sign up").

**Ghost Button:** Background `rgba(255,255,255,0.02)`, text `{colors.secondary-60}`, 6px radius, `1px solid rgba(255,255,255,0.08)` border. Hover increases background to `rgba(255,255,255,0.05)`. Used for standard actions and secondary CTAs.

**Subtle Button:** Background `rgba(255,255,255,0.04)`, text `{colors.secondary-60}`, 6px radius, compact padding (0px 6px). Used for toolbar actions.

**Icon Button:** Background `rgba(255,255,255,0.03)`, 50% radius (circle), `1px solid rgba(255,255,255,0.08)` border. Used for close, menu toggle, icon-only actions.

**Pill Button:** Transparent background, text `{colors.secondary-60}`, 9999px radius, `1px solid {colors.neutral}` border. Used for filter chips, tags, status indicators.

### Input Fields

**Text Input:** Background `rgba(255,255,255,0.02)`, text `{colors.secondary-60}`, `1px solid rgba(255,255,255,0.08)` border, 12px 14px padding, 6px radius. Focus adds multi-layer shadow stack.

**Search Input:** Transparent background, text `{colors.on-surface}`, icon-aware padding (1px 32px).

### Chips & Badges

**Success Badge:** Background `{colors.success-alt}` (emerald), text `{colors.on-surface}`, circle (50% radius), 10px Inter weight 510. Used for status dots.

**Neutral Chip:** Transparent background, text `{colors.secondary-60}`, 9999px radius, `1px solid {colors.neutral}` border, 12px weight 510. Used for filter chips, tags.

**Subtle Badge:** Background `rgba(255,255,255,0.05)`, text `{colors.on-surface}`, 2px radius, 10px weight 510. Used for inline labels, version tags.

### Lists & Navigation

Dark sticky header on near-black background. Links: Inter Variable 13-14px weight 510, `{colors.secondary-60}` text. Active/hover: text lightens to `{colors.on-surface}`. CTA: Brand indigo button right-aligned. Bottom border: `1px solid rgba(255,255,255,0.05)`.

## Do's and Don'ts

- Do use Inter Variable with `"cv01", "ss03"` on ALL text — these features are fundamental to Linear's typeface identity
- Do use weight 510 as the default emphasis weight — it's Linear's signature between-weight
- Do apply aggressive negative letter-spacing at display sizes (-0.022em)
- Do build on near-black backgrounds: `#08090a` for marketing, `#0f1011` for panels, `#191a1b` for elevated surfaces
- Do use semi-transparent white borders (`rgba(255,255,255,0.05)` to `rgba(255,255,255,0.08)`) instead of solid dark borders
- Do maintain WCAG AA contrast ratios (4.5:1 for normal text)
- Don't use pure white (`#ffffff`) as primary text — `#f7f8f8` prevents eye strain
- Don't use solid colored backgrounds for buttons — transparency is the system
- Don't apply brand indigo decoratively — it's reserved for interactive/CTA elements only
- Don't use positive letter-spacing on display text — Inter at large sizes always runs negative
- Don't use weight 700 (bold) — Linear's maximum weight is 590
- Don't introduce warm colors into the UI chrome — the palette is cool gray with blue-violet accent only
