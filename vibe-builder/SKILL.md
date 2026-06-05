---
name: Vibe Builder
description: Generuje krásné webové stránky, dashboardy a aplikace z klientova briefu v češtině. Použij když klient řekne "chci web / dashboard / landing page / aplikaci / microsite". Skill kombinuje principy taste-skill (composition matrix, hero archetypes, themes) a Impeccable (foundation, anti-slop rules) + lockuje stack na Next.js 15 + shadcn/ui + Tremor + Tailwind v4 + Recharts + Lucide. Generuje zdrojový kód (TSX, config) do /documents/sites/<slug>/. Po dokončení automaticky předá kontrolu netlify-publisher pro build + draft deploy. Brand DNA, Product DNA i DESIGN.md jsou VOLITELNÉ — pokud chybí, skill nabídne fallback (mini brief, URL referenčního webu, nebo 4 themes preset).
metadata: {"openclaw":{"requires":{"bins":["node","npm","npx"]},"emoji":"🎨"}}
category: vibecoding
status: ready
version: "1.0"
publishedAt: "2026-05-27"
---

# Vibe Builder

Generuje produkční-grade webové projekty (statické weby, dashboardy, aplikace)
ze klientova briefu v češtině. Aplikuje hybrid design system —
**foundation z Impeccable + composition matrix z taste-skill + stack lock-in
na Next.js/Tremor/shadcn** — aby výstup vypadal jako Vercel, Linear,
Stripe nebo Databox. Žádný AI slop, žádné generic templates.

Po dokončení **automaticky** předává kontrolu `netlify-publisher` skillu
pro build + draft deploy. Klient dostane URL k náhledu v jednom flow.

## Co skill dělá

1. **Najde dostupné brand context** z `/documents/brand/` (vše volitelné):
   - `brandDNA.md` — pokud existuje, použij; pokud ne, fallback flow (níže)
   - `productDNA.md` — pokud existuje a souvisí s projektem
   - `DESIGN.md` — pokud existuje, použij; pokud ne, fallback themes

2. **Pokud `brandDNA.md` chybí**, nabídne klientovi 3 cesty (nebrání pokračování):
   - **(a) Mini brief** — 3-4 rychlé otázky (jméno brandu, co dělá, pro koho, vibe)
   - **(b) URL referenčního webu** — klient pošle odkaz, agent extrahuje principy
     (barvy, typo, tone) přes WebFetch
   - **(c) Skip** — vibe-builder zvolí neutrální defaults z theme

   Mini Brand DNA z (a) nebo (b) se ukládá inline do projekt složky
   (`<slug>/.brand-context.md`), neukládá se do `/documents/brand/` (může to být
   projekt pro úplně jiný brand než klientův vlastní).

3. **Pokud `DESIGN.md` chybí**, nabídne klientovi výběr ze **4 fallback themes**
   (z `references/03-themes-and-dials.md`):
   - Pristine Light Mode (off-white, paper feel, sharp dark text)
   - Deep Dark Mode (charcoal, elegant glow only when justified)
   - Bold Studio Solid (ochre, royal blue, forest tones)
   - Quiet Premium Neutral (bone, sand, taupe, stone)

3. **Vede klienta krátkým briefem** (3-5 otázek):
   - Typ projektu (web / dashboard / landing page / aplikace)
   - Hlavní účel (1-2 věty)
   - Sekce nebo KPI (záleží na typu)
   - Tone přizpůsobení (default z brandDNA)
   - Slug projektu

4. **Vybere designová rozhodnutí** z reference files:
   - **Hero archetype** (Giant / Mid / Mini — z `02-composition.md`)
   - **Composition anchors per sekce** (4-8 z 12 dostupných)
   - **Dials** (8 hodnot — variance, density, art-direction, …)

5. **Vygeneruje Next.js projekt** s lockovaným stackem:
   - **Next.js 15.x pin** (`create-next-app@15`, NE `@latest` — Next.js 16
     instaluje React 19 a Tremor 3.x to nepodporuje)
   - **React 18.x pin** (Tremor compat)
   - shadcn/ui + Tremor (KPI cards, sparklines)
   - Tailwind v4 + CSS variables z theme
   - Recharts (charts pod Tremorem)
   - Lucide React (ikony)
   - Inter (UI) + Geist Mono (čísla)
   - Output do `/documents/sites/<slug>/`
   - **`--legacy-peer-deps`** na všech `npm install` voláních (Tremor + React peer warnings)

5a. **Copy generation** (z `08-copywriting.md`):
   - Identifikuj awareness stage návštěvníka (cold/warm/hot traffic)
   - Vyber framework per blok: PAS (hero), AIDA (full landing), FAB (features),
     BAB (testimonials), TIMER (offer)
   - Aplikuj brand voice z `brandDNA.md` (sekce „hlas značky")
   - **Headline pravidlo:** 50 % úsilí na hero h1. ≥2 ze 4 U's (Useful/Urgent/
     Unique/Ultra-specific).
   - **Czech pravidla:** ≤14 slov/věta, malá slova, vykání, „vy" víc než „my",
     žádné banned phrases („revoluce", „transformace", „posunout byznys", …)
   - **CTA pravidlo:** jedna akce per sekce, verb-led, names outcome (NE „Klikněte zde")
   - Run preflight checklist (33-point) z `08-copywriting.md` na každý kritický
     blok

6. **Anti-slop kontrola** (z `04-anti-slop.md`):
   - Žádné purple/blue AI gradients
   - Žádné banned copy ("revoluce", "transformace", "posunout byznys")
   - Žádné Acme/Nexus/Flowbit brandnames
   - Composition variety check (3 různé sekce za sebou)

7. **Auto-handoff na publisher**:
   ```
   netlify-publisher build /documents/sites/<slug>
   netlify-publisher ensure-site --slug <slug>
   netlify-publisher deploy /documents/sites/<slug> --site-id <id>
   ```
   Klient dostane draft URL v chatu, klikne, prohlédne v browseru.

## Kdy použít

- Klient řekne: „chci dashboard nad fakturoidem", „udělej mi landing page",
  „potřebuju microsite pro nový produkt", „vytvoř mi web pro firmu".
- Klient chce iterovat existující projekt (re-run s upraveným briefem).
- Klient potřebuje rychlý prototyp k validaci nápadu.

## Kdy NEpoužívat

- Klient chce **redesign existujícího webu** s vlastním kódem — vibe-builder
  generuje **nový** projekt, ne edituje existující.
- Klient potřebuje **e-commerce s plnou checkout pipeline** — zatím
  nepodporujeme (V2+).
- Klient potřebuje **mobilní nativní app** (iOS/Android) — vibe-builder
  generuje jen web/PWA.
- Klient chce **CMS s editorem obsahu** — generujeme statický kód, ne
  CMS instalace.

## Předpoklady

V containeru:
- `node`, `npm`, `npx` — pro create-next-app + dependency install
- `netlify` CLI — pro publisher hand-off

V `/documents/brand/` (vše VOLITELNÉ — žádný blocker pokud chybí):
- `brandDNA.md` — pokud existuje, použij. Pokud ne, nabídni 3 fallback cesty
  (mini brief, URL referenčního webu, neutrální defaults).
- `DESIGN.md` — pokud existuje, použij. Pokud ne, nabídni 4 themes preset.
- `productDNA.md` v `/products/<slug>/` — volitelně, jen pokud projekt souvisí
  s konkrétním produktem klienta.

**Důležité:** klient může stavět projekt pro **úplně jiný brand** (např. pro
jeho klienta jeho klienta). Vibe-builder nikdy neforcuje použití klientova
vlastního brandu, vždy se ptá na kontext aktuálního projektu.

## Workflow — krok po kroku

### Krok 1: Zjisti brand context (volitelně)

**Nejdřív se zeptej klienta**: „Stavíme pro tvůj brand, nebo pro někoho
jiného?" (klient může dělat web/dashboard pro vlastního klienta).

**Pokud klientův vlastní brand**:
```bash
ls /documents/brand/
cat /documents/brand/brandDNA.md 2>/dev/null
cat /documents/brand/DESIGN.md 2>/dev/null
# Pokud relevant produkt:
cat /documents/brand/products/<slug>/productDNA.md 2>/dev/null
```

**Pokud `brandDNA.md` chybí** (nebo klient staví pro jiný brand) → nabídni
3 cesty:

1. **Mini brief** — agent se zeptá:
   - „Jméno brandu / projektu?"
   - „Co děláte / co projekt prodává?" (1 věta)
   - „Pro koho je to? Jaká cílovka?" (1 věta)
   - „Jaký vibe? (premium / přátelské / technické / luxury / hravé)"

2. **URL referenčního webu** — agent řekne:
   - „Pošli mi URL webu, který se ti líbí jako reference, nebo URL tvého
     současného webu. Vytáhnu si principy."
   - Agent zavolá WebFetch na URL, extrahuje barvy (z meta tags, CSS), typo,
     tone of voice z copy.

3. **Skip** — agent zvolí neutrální defaults:
   - Theme = Pristine (nejbezpečnější)
   - Vibe = professional neutral

Mini Brand DNA z (1) nebo (2) ulož do `<slug>/.brand-context.md` (projekt
lokální, ne globální `/documents/brand/`).

**Pokud `DESIGN.md` chybí** → nabídni 4 themes (Pristine/Deep/Bold/Quiet).

### Krok 2: Brief s klientem (krátký dialog)

Zeptej se klienta postupně (ne všechno najednou):

1. **„Co stavíme — web, dashboard, landing page nebo aplikaci?"**
2. **„Hlavní účel v jedné větě?"** (např. „přehled obratu z Fakturoidu")
3. Podle typu:
   - Web / landing: **„Jaké sekce by tam měly být?"** (hero, features, CTA, ...)
   - Dashboard: **„Jaké KPI nebo metriky?"** (obrat, faktury, leads, ...)
4. **„Slug projektu?"** (např. `obrat-dashboard`, lowercase, hyphen-separated)

### Krok 3: Theme selection

Pokud `DESIGN.md` existuje → použij jeho specifikaci.

Pokud chybí → nabídni klientovi výběr ze 4 themes (z `03-themes-and-dials.md`):
- Pristine — světlé, papírové, sharp typo (default pro většinu B2B)
- Deep — temné, glow only when justified (default pro dashboardy)
- Bold — výrazné barvy, statement (pro creative brands)
- Quiet — neutrální, taupe/stone (pro premium luxury brands)

### Krok 4: Designová rozhodnutí

Načti `references/02-composition.md` a `03-themes-and-dials.md`:

- **Hero archetype** — vyber 1 ze 3:
  - **Giant**: massive type, dominant viewport (pro statement landing)
  - **Mid**: balanced, cinematic, ne screen-filling (pro většinu webů)
  - **Mini**: tiny logo + thin CTA, mostly negative space (pro premium)

- **Composition anchors** — vyber 4-8 z 12 pool podle počtu sekcí:
  - Centered statement / Bottom-left text over image / Off-grid editorial /
    Stacked center / Right-third + left-two-thirds / ... atd.
  - **Pravidlo:** žádné 3 stejné sekce za sebou.

- **Dials** (8 hodnot) — default podle typu projektu:
  - Dashboard: `density=6, art-direction=7, conversion=9, implementation-clarity=10`
  - Landing: `density=4, art-direction=8, conversion=8`
  - Web: `density=5, art-direction=7, conversion=6`

### Krok 5: Generování projektu

```bash
PROJECT_DIR="/documents/sites/<slug>"

# 1. Vytvoř Next.js 15 projekt (= React 18 default → Tremor compat)
#    NIKDY @latest — Next.js 16 instaluje React 19 → ERESOLVE konflikt s Tremor.
cd /documents/sites
npx create-next-app@15 <slug> \
  --typescript --tailwind --app --use-npm --src-dir \
  --no-eslint --import-alias "@/*"

cd <slug>

# 2. TypeScript deps explicit preinstall (Next.js auto-install se zasekne na peer deps)
npm install --save-dev --legacy-peer-deps \
  typescript @types/react @types/node @types/react-dom

# 3. Stack lock-in dependencies (vždy --legacy-peer-deps kvůli Tremor + React peer warnings)
npm install --legacy-peer-deps \
  @tremor/react@latest recharts lucide-react geist clsx tailwind-merge

# 4. Init shadcn/ui
npx shadcn@latest init -d
# Přidej komponenty podle typu projektu (z 05-stack.md)
npx shadcn@latest add card button input label
```

**Generuj soubory:**

- `next.config.js` — s `output: 'export'` pro statický web,
  bez tohoto flagu pro dashboard s daty (SSR)
- `tailwind.config.ts` — s CSS variables z theme (foundation tokens)
- `app/globals.css` — light/dark mode tokens
- `app/layout.tsx` — Inter (UI) + Geist Mono (čísla), `<html lang="cs">`,
  dark mode pro dashboardy
- `app/page.tsx` — hlavní stránka s vybranými sekcemi
- `components/sections/*` — sekce podle composition anchors
- `components/ui/*` — shadcn primitives (z předchozího `shadcn add`)
- `lib/utils.ts` — utility funkce
- (pro dashboardy) `lib/data.ts` — mock data nebo data fetcher

**Detail kód patterns** — viz `references/05-stack.md` a `06-patterns.md`.

### Krok 6: Image strategy (před generováním kódu)

Vibe-builder vyřeší obrázky **inline** (neděleguje na `brand-image-generator`
skill — duplikovaný overhead). 4-tier priority (detail v `07-images.md`):

**Priority 1 — Obrázky z chatu:** Pokud klient přiložil obrázky k promptu,
ulož je do `<slug>/public/from-chat/` a použij. Vždy preferuj před generací.

**Priority 2 — Existující brand assets:**
- `/documents/brand/products/<product-slug>/images/` — per-produkt fotky
- `/documents/brand/images/` — obecné brand obrázky
- `/documents/brand/brand-kit/` — POZOR, jen jako reference pro AI prompting,
  NIKDY nekopírovat do generovaného webu (jsou to mockupy)

Kopíruj použitelné assety do `<slug>/public/brand-assets/`.

**Priority 3 — AI generace (brand-aware) přes `image_generate` tool:**

Načti brand kontext (`brandDNA.md`, `DESIGN.md`, brand-board, relevant
brand-kit mockup jako reference). Sestav prompt podle patternu z
`07-images.md`. **Klíčové pravidlo: AI generuje úplně novou věc v brand
jazyce, NIKDY neopakuje prvky z reference.**

```python
image_generate(
    prompt="<brand-aware prompt + anti-slop negatives>",
    aspect_ratio="16:9",
    model="gpt-image-2",
    reference_images=["/documents/brand/brand-board.png", "..."],
    output_path="/documents/sites/<slug>/public/generated/hero.png"
)
```

**Priority 4 — Fallback (generic image_generate):**

Aktivuje se ve dvou případech:
- (a) Klient nemá `brandDNA.md` / `brand-board.png` (externí brand projekt)
- (b) Priority 3 selže technicky (rate limit, content reject, timeout)

Generic prompt jen s briefem + theme tokens, bez brand reference images.

**Brand identity assets** (POVINNÁ detekce — z `07-images.md` sekce „Brand identity assets"):

- **Logo:** hledej `logo.png` + `logo-inverse.png` (pro dark mode). Pokud chybí
  inverzní, použij CSS invert filter na light verzi jako fallback. Log warning
  do `<slug>/.brand-context.md` s doporučením klientovi nahrát inverzní logo.
- **Favicon:** hledej `favicon.ico` nebo `favicon.png`. Pokud chybí, vygeneruj
  z loga přes ImageMagick (`convert logo.png -resize 32x32 favicon.png`).
  Pokud ani logo není, použij theme accent color square. Log warning.
- **Vždy kopíruj** favicon do `<slug>/public/` a nastav v `app/layout.tsx`
  Metadata.icons.
- **Použij `<picture>`** s media query `prefers-color-scheme: dark` pokud má
  klient obě varianty loga (auto-switch light/dark).

**Per-anchor specs** (viz `07-images.md` tabulka):
- Giant/Mid Hero: 1920×1080, 16:9
- Image-as-canvas: 2400×1350, 16:9
- Bento card: 800×600, 4:3
- Section bg: 2400×900, 8:3
- Testimonial portrait: 600×750, 4:5

**Pravidlo brand discipline:**
- Žádný re-use obrázku napříč projekty (každý projekt vlastní set)
- Brand-kit mockupy SLOUŽÍ jen jako inspirace, nikdy se nesmí opakovat
- Vibe-builder vede log v `<slug>/.brand-context.md`: zdroj per slot,
  použité prompty, model path (gpt-image-2 = paušál, fal = per-image cost)

**Cost model (důležité):**
- **GPT Image 2** (default) = kryto CC paušálem, **klient neplatí per obrázek**
- **FAL fallback** = jen když GPT Image 2 selže, **per-image cost ze
  `FAL_KEY`** (~3-7 Kč / obrázek)
- Nezatěžuj klienta cenovkou GPT Image 2 generace. Jen pokud spadlo na FAL,
  zmínit „použil jsem fallback model, ~3 Kč ze tvého FAL kreditu" v output reportu.

### Krok 7: Anti-slop check

Načti `references/04-anti-slop.md` a projdi checklist:

- [ ] Žádné `bg-gradient-to-*` s `from-purple-*` nebo `from-blue-*` na hero
- [ ] Žádné slovo z banned list v copy: „revoluce / transformace / posunout
      byznys / inovativní řešení / next-gen / seamless"
- [ ] Žádné Acme / Nexus / Flowbit / NovaCore brandnames v ukázkách
- [ ] Žádné 3 stejné sekce za sebou (composition variety)
- [ ] Žádné nested cards (Cardocalypse)
- [ ] Žádný hero pattern „left-text + right-image" (default AI cliché)
- [ ] Inter Everywhere check — typo má variace (Inter UI + Geist Mono čísla)
- [ ] Tabular numerals pro číselné metriky (`font-variant-numeric: tabular-nums`)

Pokud najdeš slop → oprav před hand-offem (max 3 retry kola).

### Krok 8: Auto-handoff na publisher

Bez ptaní klienta, automaticky:

```bash
# Detekuj framework + build + cleanup
python3 /home/node/.openclaw/cs-skills/netlify-publisher/scripts/netlify_publish.py \
  build /documents/sites/<slug> --json

# Vytvoř nebo najdi Netlify site
python3 .../netlify_publish.py ensure-site --slug <slug> --json
# → vrátí site_id

# Draft deploy
python3 .../netlify_publish.py deploy /documents/sites/<slug> \
  --site-id <site_id> --draft --json
# → vrátí draft URL
```

### Krok 9: Output klientovi

V chatu:

```
✓ Hotovo!

Náhled: https://<hash>--<slug>.netlify.app
(otevři v browseru → prohlédni)

Použitá theme: <theme name>
Hero archetype: <Giant/Mid/Mini>
Sekce: <list>

Co dál?
• Posunout do produkce (volá publisher promote)
• Změnit barvy nebo layout (re-run s upraveným briefem)
• Připojit vlastní doménu (publisher add-domain workflow)
• Nechat takhle (draft URL zůstává)
```

## Edge cases

- **`brandDNA.md` chybí** → NENÍ blocker. Nabídni 3 fallback cesty (mini
  brief / URL reference / skip s defaults). Viz Krok 1 workflow.
- **Klient staví pro jiný brand než svůj** → použij mini brief nebo URL
  reference. NEPOUŽÍVEJ klientův vlastní `brandDNA.md` (mate brandy).
- **Klient neumí formulovat brief** → pomoz mu otázkami z 02 (typ → účel
  → sekce → slug). Default theme = Pristine, hero = Mid.
- **`create-next-app` selže** (npm registry timeout, disk plný) → vrať
  chybu klientovi, navrhuj retry za 30 s.
- **Anti-slop loop nekonverguje** (3 retry kola, stále issues) → eskaluj
  klientovi: „Designové pravidla narážejí na specifikaci. Můžeme zkusit
  jinou theme nebo briefnejte konkrétněji."
- **Disk plný** (< 500 MB volných) → vyčisti staré `node_modules` v
  `/documents/sites/*`, pak retry.
- **Slug kolize** (`/documents/sites/<slug>` už existuje) → zeptej se
  klienta: overwrite / nový slug / iterace existujícího?

## Limity (MVP — v0.1)

- 1 projekt per session (sekvenční generování, ne parallel)
- Max 8 sekcí na web
- Max 12 KPI cards na dashboard
- Bez vlastního assetu z uploadu (jen icons z Lucide + fallback obrázky)
- Bez i18n (jen čeština pro klientovy weby; agent SKILL je v češtině)
- Bez auth flow generování (login/signup — V2+)
- Bez datových connectorů (Fakturoid/GA4/Meta — V2+, zatím mock data)

## Co NENÍ v v0.1 (= odložené)

- ❌ Live Mode (Chrome extension) — V2+
- ❌ Iterace existujícího projektu bez re-generace — `vibe-edit` skill V2+
- ❌ Multi-page weby (jen single-page; Next.js routing přijde v V2)
- ❌ Data connectors na live APIs — V2 (zatím mock data v `lib/data.ts`)
- ❌ Form handling (kontaktní formuláře) — V1.5
- ❌ A11y audit (WCAG checker) — V2+

## Reference files

- `references/01-foundation.md` — typografie, barvy, spacing, motion
- `references/02-composition.md` — 12 anchors, hero archetypes
- `references/03-themes-and-dials.md` — 4 themes, 8 dials
- `references/04-anti-slop.md` — banned patterns, copy, brandnames + image
- `references/05-stack.md` — Next.js + shadcn + Tremor + next/image patterns
- `references/06-patterns.md` — dashboard (Databox) + web (landing) layouts
- `references/07-images.md` — 4-tier image strategy, brand-aware AI prompting
- `references/08-copywriting.md` — frameworky (PAS/AIDA/BAB/FAB/TIMER), 5
  awareness stages, czech jazyk pravidla, website-specific patterns, 33-point
  preflight checklist. Extrakt z `cs-skills/copywriting/` v1.0 + website overlay.
