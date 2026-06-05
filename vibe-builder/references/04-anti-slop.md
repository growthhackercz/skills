# Anti-slop checklist — 29 patternů, banned copy, banned brandnames

Před hand-offem na publisher PROJDI tento checklist. Pokud najdeš issue,
oprav před deployem (max 3 retry kola). Slop = generic AI cliché. Klient
za 49 970 Kč nepřijme generic.

## Visual slop — 13 patternů

### Layout slop
1. ❌ **Purple/blue AI gradient** — `from-purple-500 to-blue-500` na hero
   nebo cards. Cliché #1. Použij low-chroma tonal gradient z theme palette.

2. ❌ **Side-tab cards** — thick border accent stripe vlevo/vpravo na card.
   Bootstrap admin template vibe. Použij subtle border nebo shadow, ne stripe.

3. ❌ **Cardocalypse** — nested cards (card inside card). Wrap content
   přímo v sekci, ne v dalším card.

4. ❌ **Endless centered sections** — 5 sekcí za sebou všechny centrované.
   Variuj composition anchors (z `02-composition.md`).

5. ❌ **Identical card rows repeated** — feature1, feature2, feature3 ve
   stejném layoutu × 6. Variuj density mezi sekcemi.

6. ❌ **Left-text + right-image hero** — #1 AI cliché hero. Použij hero
   archetype Giant nebo Mid (image-as-canvas), ne split layout.

7. ❌ **Cloned testimonial cards** — 3 cards s "Lorem ipsum"-style quotes,
   všechny stejný layout. Variuj quote presentation.

### Color slop
8. ❌ **Default AI color palette** — purple-500, indigo-500, pink-500 mix.
   Použij theme palette (`03-themes-and-dials.md`).

9. ❌ **Glassmorphism stacked without reason** — backdrop-blur cards na
   background, který není image. Jen když máš full-bleed image podklad.

10. ❌ **Too many glowing edges** — box-shadow s velkým blur + bright color
    na každý card. Glow jen na 1-2 highlight elements per page.

### Typography slop
11. ❌ **Gradient-text headings** — `bg-gradient-to-r bg-clip-text`. Lazy
    premium effect. Použij solid color s strong weight místo gradientu.

12. ❌ **Inter Everywhere** — celá stránka v Inter regular. Variuj weights
    (semi/bold na display), kombinuj s Geist Mono na čísla.

13. ❌ **Italic-serif display heroes** — Fraunces, Recoleta, Playfair na
    hero. Hipster cliché 2024-2026. Použij sans-serif display s weight contrast.

## Content slop — 8 patternů

### Banned copy (anglicky aj. v překladech)
14. ❌ **"unleash, elevate, revolutionize, next-gen, seamless, transformative,
    powerful solution, comprehensive platform, innovative"** — generic AI
    marketing copy. Použij konkrétní outcomes.

15. ❌ **Banned česky:** „revoluce v X / transformace vašeho byznysu / posunout
    byznys na další úroveň / inovativní řešení / next-gen platforma / seamless
    integrace / powerful nástroj / comprehensive solution / posouvejte hranice"

### Banned fake brandnames
16. ❌ **Acme, Nexus, Flowbit, Quantumly, NovaCore, Apex, Vertex, Synergy,
    Catalyst, Pulse** — generic SaaS fake brand. Použij realistická česká
    fake jména (Krajec, Modřínová s.r.o., Kafe a Strom, ...) nebo
    placeholder typu „[Client Brand Name]".

### Banned trust patterns
17. ❌ **Fake "trusted by" logo strip** — infinite scrolling 8-15
    nečitelných loga. Buď nech být, nebo dej 3-5 reálných loga klienta.

18. ❌ **Lorem ipsum** v finálním kódu. Vždy nahrazuj real copy nebo
    realistic Czech placeholder.

### Banned interaction patterns
19. ❌ **"Click here" CTAs** — neinformativní text. Použij outcome-driven
    („Stáhnout přehled" / „Začít zdarma" / „Domluvit hovor").

20. ❌ **Auto-playing video s sound** — okamžitě muted, ideálně lazy-load.

21. ❌ **Newsletter popup hned po načtení** — alespoň 30s scroll trigger.

## Density / component slop — 8 patternů

22. ❌ **Card overload v každém bloku** — sekce = jen 6 cards bez variace.
    Jedna sekce může být typografická (large statement), ne card grid.

23. ❌ **Tiny spacing mezi major sections** — `py-12` nebo méně. Použij
    `py-20 md:py-32` minimum (viz `01-foundation.md`).

24. ❌ **No overfilled sections** — sekce s 12+ elements. Splite na 2 sekce.

25. ❌ **Awkward line breaks** — copy je rozbitý na podivných místech přes
    `<br>` v middle of sentence. Použij CSS `text-balance` nebo `text-wrap: pretty`.

26. ❌ **Lazy all-caps everywhere** — sekce nadpisů jen `uppercase`. Allow jen
    na malých labels (eyebrow), ne na hero h1 nebo section h2.

27. ❌ **Hero eyebrow chips** — uppercase letter-spaced label nad h1 v pill
    chip podobě (`bg-purple-100 text-purple-600 uppercase tracking-widest`).
    Overused 2025 cliché. Použij jednoduché label nebo nic.

28. ❌ **Nested cards** = duplikát #3. Sekce má **jednu** úroveň hlavního
    containeru (card nebo přímo content), ne víc.

29. ❌ **Editorial-typographic reflex** — když brief řekne "premium",
    automatický skok na Fraunces italic + asymmetric layout + duotone image.
    Tohle je už-cliché premium AI pattern. Variuj — premium může být i Giant
    Statement Hero v Pristine theme.

## Composition variety check

Před hand-offem ověř:

- [ ] **Žádné 2 stejné composition anchors za sebou** (sekce 1 ≠ sekce 2 layout)
- [ ] **Žádné 3 stejné background modes za sebou**
- [ ] **Žádných 5 sekcí stejné density** (alternuj dense → calm → dense)
- [ ] **Hero ≠ jakákoli další sekce layout-wise**
- [ ] **CTA buttons konzistentní napříč stránkou** (stejný shape, color, font)
- [ ] **Typography hierarchy konzistentní** (h1 vždy stejný size, ne občas h1
      48 px občas 60 px)

## Image-specific patterns (pro AI image generation)

Tyto patterny vždy přidej jako **negative prompts** do `image_generate`
calls. Detail v `07-images.md`.

### Always negative v image promptech

- **Stock photo person** — „no people staring at camera", „no smiling office
  worker", „no thumbs up" (typický Getty/Shutterstock vibe)
- **AI watermarks / artifacts** — „no AI watermarks, no signature artifacts,
  no Midjourney logos, no DALL-E corner marks"
- **Fake brandnames v obraze** — „no readable brand text, no fake logos,
  no fictional company names"
- **Purple-to-blue gradients** — „no purple gradient, no blue glow,
  no neon haze"
- **Glowing edges** — „no glowing edges, no neon outlines unless explicitly
  brand-justified"
- **Plastic skin / deepfake vibe** — „no plastic skin texture, no
  airbrushed faces, no uncanny valley features"
- **Symmetrical floating spheres** — „no floating geometric shapes,
  no orbital spheres, no abstract bubbles" (cliché AI cover art)
- **Generic „creative office"** — „no exposed brick coworking, no neon
  pixelated wall art, no laptop with smiley sticker"

### Reference image discipline

- **Brand-board.png a brand-kit/X.png** se posílají jako reference do
  `image_generate`, ale prompt explicit říká „inspired by visual language,
  not by content" — vibe-builder vždy generuje NOVÝ obrázek, nikdy
  re-vytváří referenci.
- **Product images** z `/documents/brand/products/<slug>/images/` se mohou
  použít jen v případě, že generujeme generic „lifestyle in context"
  obrázek — nikdy přímo product shot (klient má hotové product shots,
  použij je v Priority 2).

### Image proportions

- Vždy explicit `aspect_ratio` v `image_generate` (1:1 default neuncekává)
- Hero = 16:9 nebo 21:9
- Cards = 4:3 nebo 1:1
- Portraits = 4:5
- Section backgrounds = 8:3 nebo 16:5 (wide panoramic)

### File size

- AI generované PNG = obvykle 1-3 MB
- Pro web použij WebP nebo nech `next/image` udělat optimalizaci
- Nikdy nepoužívej obrázek > 5 MB v `<Image>` bez optimization

## Tech debt slop

- [ ] **Žádné `console.log`** ve finálním kódu
- [ ] **Žádné `TODO`/`FIXME`** komentáře ve finálním kódu
- [ ] **Žádné `any` typy** v TypeScript (použij `unknown` nebo strict types)
- [ ] **Žádné inline styles** mimo dynamic values (CSS-in-JS = ne, Tailwind = ano)
- [ ] **Žádné nepoužité importy**
- [ ] **Žádné `<img>` tags** — vždy `next/image` (lepší performance)

## Pokud najdeš ≥1 issue

1. Identifikuj všechny issues v 1 průchodu (ne fix po jednom)
2. Oprav v kódu, ne v prompt re-runs (přímá edita TSX)
3. Re-run anti-slop check
4. Max 3 retry kola. Pokud po 3 stále issues:
   - **Eskaluj klientovi:** „Našel jsem [X] designových problémů, které
     se mi nedaří automaticky vyřešit s aktuální theme. Zkusíme jinou
     theme nebo upravíme brief?"
   - **NIKDY** silently deploy stránku s known slop. Reputace > rychlost.
