# Composition — layout anchors, background modes, hero archetypes

Vynucená variety napříč sekcemi. Žádné 3 stejné sekce za sebou. Žádný
default „left-text + right-image" hero (= AI cliché #1).

## Hero archetypy — vyber 1 ze 3 PŘED generováním

Hero je první sekce stránky. Rozhoduje o celkovém vibe. Commit before
generating, ne improvize během kódu.

### A) Giant Statement Hero
- Massive type (text-6xl až text-8xl), dominant viewport
- Minimum 80vh height
- Background = full-bleed solid color nebo tonal gradient
- 1 CTA, prominent
- Žádný image vedle textu — text JE artwork
- **Kdy:** statement landing, manifesto-driven brand, conversion-focused

### B) Mid Editorial Hero
- Balanced typo (text-4xl až text-5xl) + cinematic image
- 60-70vh height
- Background = vrstvený (image + overlay) nebo subtle texture
- 1-2 CTAs
- **Kdy:** většina webů, default volba pro service businesses

### C) Mini Minimalist Hero
- Tiny logo + statement (text-3xl max) + thin CTA
- 40-50vh height, mostly negative space
- Background = solid neutral
- Žádný image
- **Kdy:** premium brands, high-end products, design-conscious audience

## 12 Composition Anchors — vyber 4-8 pro sekce stránky

Každá sekce má vlastní layout anchor. Variuj — žádné 2 stejné sousedící.

| # | Anchor | Popis | Vhodné pro |
|---|---|---|---|
| 1 | **Centered statement** | Velký text centrovaný, žádný image | Manifesto, value prop |
| 2 | **Bottom-left text over image** | Full-bleed image, text v levém dolním rohu | Editorial hero, brand story |
| 3 | **Off-grid editorial offset** | Asymmetric, text vlevo o 1/3, content vpravo o 2/3 | Features, premium products |
| 4 | **Right-third + left-two-thirds visual** | Inverted classic, 2/3 image vlevo, 1/3 text vpravo | Product showcase |
| 5 | **Stacked center (ultra minimalist)** | Vše centrované, jen typo + CTA | Premium CTA, signup gate |
| 6 | **Image-as-canvas** | Full-bleed image, text overlay s tonal mask | Mood section, brand story |
| 7 | **Pristine gapless bento grid** | 4-6 cards různých velikostí, žádné mezery | Features, capabilities |
| 8 | **3D cascading card deck** | Cards rotated/stacked s perspective | Testimonials, product variants |
| 9 | **Vertical rhythm lines** | Sekce dělené tenkými horizontal lines + číslováním | Process steps, methodology |
| 10 | **Oversized metrics strip** | 3-4 velká čísla horizontálně | Stats / proof |
| 11 | **Split testimonial quote wall** | 2-sloupec, velká quote vlevo, foto vpravo | Social proof |
| 12 | **Diagonal staggered masonry** | Cards offsetnuté, neuspořádaná mřížka | Gallery, portfolio |

### Pravidlo variety
- Žádné 2 stejné anchors sousedící
- Max 1× per page typ #7 (bento grid — overuse = generic)
- Hero + 1. content sekce vždy DIFFERENT anchor

## 12 Background Modes — vyber per sekce

Background mode je nezávislý na anchor. Variuj backgrounds podobně jako
anchors — žádné 2 stejné sousedící.

| # | Background mode | Popis |
|---|---|---|
| 1 | **Solid surface + inline asset** | Plný background color, image jako card uvnitř |
| 2 | **Subtle texture or grid** | Light texture (noise, grid SVG), low opacity |
| 3 | **Full-bleed image + tonal overlay** | Image cover + barevný overlay (50-70% opacity) |
| 4 | **Editorial side-image 50/50** | Půlka sekce image, půlka content |
| 5 | **Editorial side-image 60/40** | 60% content, 40% image (text-dominant) |
| 6 | **Editorial side-image 40/60** | 40% content, 60% image (image-dominant) |
| 7 | **Duotone treated image** | Image s 2-color tonal treatment (brand colors) |
| 8 | **Color-blocked diptych** | 2 horizontal stripes různých colors |
| 9 | **Micro-noise gradient** | Subtle gradient s film grain texture |
| 10 | **Soft vignette** | Centered light vignette, dark edges |
| 11 | **Pristine off-white** | Pure white nebo off-white #F8F8F6, nothing else |
| 12 | **Deep charcoal canvas** | Dark mode default, #0F1419 nebo darker |

## Section rhythm — overall page composition

### Pravidlo: dense → calm → dense
- Hero: **calm** (lots of negative space)
- Sekce 2 (features): **dense** (kompaktní bento grid)
- Sekce 3 (proof/stats): **calm** (oversized metrics, breathing room)
- Sekce 4 (deeper content): **dense** (split layout, content-heavy)
- CTA section: **dense** (visual weight pro conversion)
- Footer: **calm** (minimální)

### Continuity enforcement
- **Jedna palette** napříč sekcemi (z theme)
- **Jedna typo family** (Inter + Geist Mono jako secondary)
- **Jeden CTA styl** (button shape, color, font) — neměň od sekce k sekci

## Conversion path (i artistický web musí mít)

Každá stránka musí obsahovat:

1. **HOOK** (hero) — value prop v sekundách
2. **PROOF** — logos, quotes, metrics (earned, ne stuffed s fake logos)
3. **ACTION** — pricing nebo primary CTA, jasné, ne buried
4. **CLOSE** — final CTA + supporting trust cue (testimonial, guarantee)

Bez tohoto = mood reel, ne web. Mood reel pro klienta = neplatí faktury.

## Druhé čtení („second-read moment")

Každá stránka by měla mít **1 element**, který klient objeví až při druhém
průchodu — detail, který odlišuje od templatu.

Příklady:
- Subtle ASCII art v komentáři kódu (viditelný v dev tools)
- Hover effect na inconspicuous element (číslo verze, year stamp)
- Mikro-detail v hero (gradient, který se mění s time of day)
- Tiny easter egg v 404 page

Nepřehánět — 1 per page max. Cíl = „rád jsem to našel", ne „klient si toho
nevšimne nikdy".
