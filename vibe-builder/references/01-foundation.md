# Foundation — typografie, barvy, spacing, motion

Základní design principy. Agent je aplikuje napříč všemi výstupy bez ohledu
na zvolenou theme nebo composition.

## Typografie

### Stack lock-in
- **UI text:** Inter (Google Fonts via `next/font/google`)
- **Čísla / metriky:** Geist Mono nebo Inter s `font-variant-numeric: tabular-nums`
- **Display / hero:** Inter Display (volitelně) nebo theme-specific

### Banned fonts (overused = AI cliché)
- Geist (sans variant) jako hero font — overused v 2025-2026 AI-generated UI
- Plus Jakarta Sans, Space Grotesk, Mona Sans — generic AI defaults
- Fraunces, Recoleta, Newsreader, Playfair, Cormorant — italic-serif heroes
  jsou hipster cliché
- Žádné `<i>` na display headlines (italic serif hero = no-go)

### Hierarchie
- **Hero h1:** 48-96 px (mobile-first scaling)
- **Section h2:** 32-48 px
- **Body:** 16-18 px (ne 14 — moc malé)
- **Caption:** 13-14 px
- **KPI numbers:** 36-60 px, tabular-nums, font-medium nebo font-semibold

### Pravidla
- **1 typo family per page** (default = Inter celé)
- **2 weight max** v body kontextu (regular + medium NEBO regular + semibold)
- **Display weights** (bold, black) — jen na hero a section h2
- **Letter-spacing:** -0.02em na velkém typu (32 px+), 0 na body
- **Line-height:** 1.1-1.2 na display, 1.5-1.6 na body

## Barvy

### Stack
- **Tailwind v4** + CSS custom properties
- **OKLCH** preferován (lepší perceptual uniformita) nad HSL/RGB
- **Tokens v `tailwind.config.ts`** odvozené z theme (z `03-themes-and-dials.md`)

### Pravidlo „Palette discipline"
- **1 primary** (brand color z brandDNA)
- **1 secondary** (komplementární, méně dominantní)
- **1 accent** (pro CTA, highlights — high chroma)
- **Neutral scale** (50, 100, 200, ..., 950) — pro text a backgrounds
- **Žádné rainbow** — víc než 3 distinct hues na jedné stránce = slop

### Banned color patterns
- ❌ Purple gradient (`from-purple-500 to-blue-500`) — #1 AI cliché
- ❌ Gradient text na headlines — lazy premium effect
- ❌ Rainbow mesh blobs — chatGPT cover art vibe
- ❌ Pink-to-orange „creator" defaults
- ❌ Glassmorphism (backdrop-blur) bez konkrétního důvodu

### Allowed gradients
- Low-chroma tonal (např. `from-slate-50 to-slate-100`)
- Single-hue atmospheric (např. `from-blue-50 via-transparent to-transparent`)
- Soft vignettes na image backgrounds

## Spacing

### Princip — víc whitespace než default AI
- **VISUAL_DENSITY = 4/10** (airy, ne packed)
- **SPACING_GENEROSITY = 8/10** (much breathing room)
- Pravidlo: „o ~20 % víc whitespace mezi sekcemi než default Bootstrap/Tailwind"

### Konkrétní values (Tailwind)
- **Section vertical padding:** `py-20 md:py-32` (žádné `py-12` na hlavní sekce)
- **Container max-width:** `max-w-7xl` pro většinu, `max-w-5xl` pro content-heavy
- **Card padding:** `p-6 md:p-8` (ne `p-4` — moc compressed)
- **Gap mezi cards:** `gap-6 md:gap-8`
- **Body copy ne na viewport edge:** `px-6 md:px-12 lg:px-16`

### Section rhythm
- Alternuj density: **dense → calm → dense** (ne všechny sekce stejné)
- Hero = calm (lots of negative space)
- Features = dense (kompaktní cards)
- Testimonials = calm (1-2 quotes, breathing room)
- CTA = dense (visual weight pro conversion)

## Motion

### Princip — restrained, ne flashy
- Animace **dvě maximálně 2 typy per page** (např. fade-in on scroll + hover scale)
- Žádné scroll-jacking (parallax full-page)
- Žádné gratuitous animations (rotating logos, pulsing buttons, particle effects)

### Allowed motion
- **Fade-in on scroll** (Framer Motion `whileInView`, opacity 0→1, y 20→0)
- **Hover state** na cards (subtle scale 1.02, shadow elevation)
- **Smooth scroll** na anchor links
- **Skeleton loading** na async data (dashboard fetch)

### Banned motion
- Bouncy spring animations everywhere
- Auto-playing video backgrounds
- Animated emojis nebo Lottie complex animations
- Parallax mouse-tracking effects

### Durations
- **Hover/tap:** 150-200 ms
- **Page transitions:** 300-400 ms
- **Scroll reveals:** 400-600 ms s `ease-out`
- Žádná animace delší než 800 ms

## Interaction

### Buttons
- **Primary CTA:** filled, brand color, font-semibold
- **Secondary:** outline nebo ghost, font-medium
- **Destructive:** red-500 fill, jen na delete actions
- **Disabled:** opacity-50, cursor-not-allowed, no hover

### Forms
- **Labels nad inputy** (ne placeholder-only — accessibility)
- **Focus ring:** 2px brand color, `ring-2 ring-offset-2`
- **Validation:** inline pod input (ne tooltip)
- **Submit button:** loading state s spinnerem

### Cards
- **Padding:** `p-6` minimum
- **Border:** subtle (`border border-slate-200 dark:border-slate-800`) NEBO shadow (`shadow-sm`), ne oba
- **Radius:** `rounded-lg` (8 px) nebo `rounded-xl` (12 px), konzistentně per page
- **Hover:** subtle elevation increase, ne color flash

## Responsive

### Breakpoints (Tailwind)
- **Mobile-first** vždy
- `sm:` 640 px — tablet portrait
- `md:` 768 px — tablet landscape
- `lg:` 1024 px — desktop small
- `xl:` 1280 px — desktop large
- `2xl:` 1536 px — wide screens

### Pravidla
- **Hero font-size:** `text-4xl md:text-6xl lg:text-7xl`
- **Section padding:** `py-16 md:py-24 lg:py-32`
- **Grid:** `grid-cols-1 md:grid-cols-2 lg:grid-cols-3` (default)
- **Container padding:** `px-6 md:px-12 lg:px-16`

## UX writing

### Pravidla v češtině
- **Vykání** (klient = user koncového produktu)
- **Konkrétní, ne abstraktní:** „Ušetříte 4 hodiny týdně" ne „Zvýšíte produktivitu"
- **Aktivní hlas:** „Stáhněte si přehled" ne „Přehled je možné stáhnout"
- **Stručné CTA:** „Začít zdarma" / „Stáhnout" / „Domluvit hovor"
  (ne „Klikněte sem pro zahájení vašeho..."v)

### Banned copy patterns (v češtině)
- „revoluce v X"
- „transformace vašeho byznysu"
- „posunout byznys na další úroveň"
- „inovativní řešení"
- „next-gen platforma"
- „seamless integrace"
- „powerful nástroj"
- „comprehensive solution"

### Tone podle context
- **B2B SaaS / dashboardy:** neutrální, technicky důvěryhodné
- **Landing page service biz:** přátelské, výsledkově orientované
- **Premium brand:** restrained, sofistikované, méně exclamace
- **E-commerce:** akční, jasné value prop
