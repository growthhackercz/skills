# Image strategy — 4 priority + brand-aware AI generation

Vibe-builder řeší obrázky 4-tier strategií. Brand consistency je klíčová pro
klienty s vybudovaným brand systémem. Pro klienty bez brand DNA fallback na
neutrální generaci.

**Klíčové pravidlo:** AI generace se inspiruje brand referencemi, NIKDY je
neopakuje. Každý nový obrázek je úplně nová věc, jen v brand jazyce.

## Image strategy = inline ve vibe-builderu

Vibe-builder volá `image_generate` tool přímo. Nedelegujeme na
`brand-image-generator` skill — duplikoval by se overhead. Místo toho
vibe-builder načítá stejný brand kontext a sám sestaví prompt.

## 4-tier priority

### Priority 1: Obrázky z chatu (multimodal context)

Pokud klient přiložil obrázky k promptu při zadávání projektu, agent je má
v chat contextu. Ulož je do projektu:

```bash
mkdir -p /documents/sites/<slug>/public/from-chat
# Pro každý obrázek v chat contextu:
# - Ulož s descriptivním názvem (hero.jpg, feature-1.jpg, ...)
# - Zaeviduj v <slug>/.brand-context.md jako "asset sources"
```

**Kdy:** klient explicit poslal vlastní fotky. Vždy preferuj před generací.

### Priority 2: Existující brand assets

Glob v `/documents/brand/`:

```bash
# Per-produkt obrázky (pokud projekt souvisí s konkrétním produktem)
ls /documents/brand/products/<product-slug>/images/*.{png,jpg,jpeg,webp}

# Obecné brand obrázky
ls /documents/brand/images/*.{png,jpg,jpeg,webp}

# Brand-kit mockupy (POUZE jako reference, NIKDY nepoužij jako asset!)
ls /documents/brand/brand-kit/*.png  # 24 mockupů
```

**Pravidlo:** `images/` a `products/<slug>/images/` jsou **použitelné assety**
(kopíruj/symlink do projekt `public/brand-assets/`). `brand-kit/` jsou
**pouze inspirace pro AI prompting**, nikdy nekopíruj do generovaného webu
(jsou to mockupy, ne finální assety).

```bash
# Pro použitelné assety:
mkdir -p /documents/sites/<slug>/public/brand-assets
cp /documents/brand/products/<slug>/images/hero.jpg \
   /documents/sites/<slug>/public/brand-assets/hero.jpg
```

**Match pravidla:**
- Hero slot → hledej landscape orientation, ≥1920px wide
- Feature card → hledej square nebo 4:3
- Section background → hledej wide aspect, podtonal
- Logo → vždy `/documents/brand/logo.png`

### Priority 3: AI generace (brand-aware)

Když nemáme vhodný asset z Priority 1 nebo 2, generujeme přes `image_generate`
tool s prompt postaveným z brand kontextu.

#### Vstupy pro prompt building

Načti tyto soubory jako brand context:

```bash
cat /documents/brand/brandDNA.md       # esence, barvy, typo, vibe
cat /documents/brand/DESIGN.md         # tokens, do's & don'ts
# Volitelné:
cat /documents/brand/products/<slug>/productDNA.md
```

Načti tyto obrázky jako vizuální reference (PRO `image_generate` jako reference, ne pro kopírování):

- `/documents/brand/brand-board.png` — primární reference designového jazyka
- `/documents/brand/brand-kit/<X>.png` — vyber 1 nejrelevantnější mockup
  podle požadovaného typu obrázku (viz mapping níže)
- `/documents/brand/products/<slug>/images/*.png` — max 3 produktové reference
- `/documents/brand/logo.png` — pro pochopení vizuálního jazyka, NEPOUŽÍVÁ se
  v generovaném obrázku

#### Mapping typu requestu → brand-kit reference

| Vibe-builder request | Brand-kit mockup typ (pokud existuje) |
|---|---|
| Hero image pro landing | 03-04 (homepage / hero) nebo 09 (web hero) |
| Hero pro dashboard | žádný — dashboard nemá foto hero |
| Section background | 11-12 (web sekce) |
| Feature card thumbnail | 05-06 (produkt mockup) |
| Testimonial pozadí | 13-14 (social proof) |
| CTA section image | 03-04 (hero variant) |
| Footer / contact | 15-16 (form / contact) |

Pokud mockup neexistuje, použij jen brand-board jako reference.

#### Prompt building pattern

```
{visual_style_from_brandDNA} + {subject_from_brief} + 
{composition_for_anchor} + {aspect_ratio} + {negative_prompts_anti_slop}
```

**Příklad pro kavárnu, Bold Studio theme, Hero archetype Mid:**

```
Editorial wide-angle photograph of modern Czech specialty café interior,
warm wood textures and large windows, golden hour light streaming in,
ochre and royal blue accent palette matching brand,
no people in frame, no text overlay, no logos visible,
no purple gradients, no glowing edges, no AI watermarks,
16:9 cinematic aspect, professional photography style.

[reference images: brand-board.png + brand-kit/04.png]
```

#### Volání image_generate

```python
image_generate(
    prompt="<prompt z patternu výše>",
    aspect_ratio="16:9",  # nebo 4:5, 1:1, 8:3 podle slotu
    model="gpt-image-2",  # default; fallback flux-pro automaticky
    reference_images=[
        "/documents/brand/brand-board.png",
        "/documents/brand/brand-kit/04.png",
    ],
    output_path="/documents/sites/<slug>/public/generated/hero.png"
)
```

#### Pravidla pro brand-aware prompting

1. **Nikdy „v stylu X"** — neforcuj specific photographer/brand name. Použij
   abstraktnější deskripce („editorial photography", „warm cinematic light").
2. **Vždy explicit „no logos, no text overlay"** — vibe-builder vloží
   typografii v TSX, ne v obrázku.
3. **Barvy z theme tokens, ne z volné fantazie** — uveď konkrétní palette
   v promptu (např. „ochre #C8893F and royal blue #2842A8 accent").
4. **Aspect ratio explicit** — `image_generate` defaultně 1:1, vždy override.
5. **Anti-slop negatives** z `04-anti-slop.md` (sekce image-specific) —
   vždy přidat na konec promptu.

### Priority 4: Fallback — generic `image_generate` (bez brand kontextu)

**Aktivuje se ve dvou případech:**

(a) **Klient nemá brand DNA / brand-board** — vibe-builder pracuje pro
   externí brand bez DNA dokumentů. Použij generic prompt jen s briefem +
   theme tokens.

(b) **Priority 3 selže technicky** — `image_generate` vrátí error
   (rate limit, model timeout, content policy reject). Retry s generic
   prompt jako fallback.

#### Generic prompt pattern

```
{visual_style_from_theme_only} + {subject_from_brief} +
{aspect_ratio} + {anti_slop_negatives}
```

Bez reference images, bez brand colors. Theme = Pristine/Deep/Bold/Quiet,
agent vybírá podle defaults z `03-themes-and-dials.md`.

**Příklad fallback:**
```
Wide-angle editorial photograph of modern café interior,
neutral warm palette, soft natural light, no people, no text,
no purple gradients, 16:9 cinematic aspect.
```

## Per-anchor image specs

| Composition anchor | Dimensions | Aspect | Notes |
|---|---|---|---|
| Giant Statement Hero | 1920×1080 | 16:9 | Full-bleed, dominant viewport |
| Mid Editorial Hero | 1920×1080 nebo 1600×900 | 16:9 | Cinematic, balanced |
| Mini Minimalist Hero | žádný image | — | Type-first, žádná foto |
| Image-as-canvas | 2400×1350 | 16:9 | Full-bleed, text overlay |
| Bento card thumbnail | 800×600 | 4:3 | Card content |
| Section background | 2400×900 | 8:3 | Wide panoramic, low chroma |
| Testimonial portrait | 600×750 | 4:5 | Person-friendly aspect |
| Product showcase | 1200×1200 | 1:1 | Square, e-commerce style |

## Brand identity assets — logo + favicon (povinná detekce)

Vibe-builder MUSÍ při setupu projektu detekovat a použít:

### Logo (= header + footer + fav-touchpointy)

Hledá v tomto pořadí v `/documents/brand/`:

| Typ | Soubor | Použití |
|---|---|---|
| **Normální logo** | `logo.png` (nebo `.svg`, `.webp`) | Light mode, dark text on light bg |
| **Inverzní logo** | `logo-inverse.png` (nebo `logo-white.png`, `logo-dark.png`) | Dark mode, white text on dark bg |
| **Symbol** (volitelné) | `logo-symbol.png` (ikona bez wordmark) | Mobile menu, malé prostory |

**Decision rule pro vibe-builder:**

```typescript
// Pseudo-logika v generovaném layout.tsx
function pickLogo(theme: 'light' | 'dark'): string {
  if (theme === 'dark') {
    return existsLogo('logo-inverse.png')
      ?? existsLogo('logo-white.png')
      ?? existsLogo('logo.png');  // fallback
  }
  return existsLogo('logo.png');
}
```

**Pro responsive variants** (light + dark mode auto-switch):

```tsx
// layout.tsx nebo Logo komponenta
<picture>
  <source srcSet="/brand-assets/logo-inverse.png" media="(prefers-color-scheme: dark)" />
  <Image src="/brand-assets/logo.png" alt="<Brand name>" width={120} height={32} priority />
</picture>
```

**Pokud má klient JEN normální logo** (žádný inverse) a generuje se dark theme dashboard:
- Použij `logo.png` ale aplikuj CSS filter (`filter: invert(1) brightness(1.2)`) jako fallback
- Současně logni do `<slug>/.brand-context.md`: „WARN: chybí logo-inverse.png, použit CSS invert fallback. Doporučit klientovi nahrát inverzní logo."

### Favicon (= browser tab icon)

Hledá v `/documents/brand/`:

| Typ | Soubor | Priorita |
|---|---|---|
| **Modern favicon** | `favicon.ico` | 1 (multi-size, universal browser support) |
| **PNG favicon** | `favicon.png` (32×32 nebo 256×256) | 2 (modern browsers OK) |
| **SVG favicon** | `favicon.svg` | 3 (scalable, ale starší browsers nezvládnou) |
| **Apple touch icon** | `apple-touch-icon.png` (180×180) | volitelné — pro iOS home screen |

**Fallback flow pokud chybí všechny:**

1. Hledej `favicon.*` v brand assets
2. Pokud chybí, **vygeneruj z loga** automaticky:
   ```bash
   # Použij ImageMagick nebo Sharp (oba běžně dostupné)
   convert /documents/brand/logo.png -resize 32x32 \
     /documents/sites/<slug>/public/favicon.png
   ```
3. Pokud ani logo není (klient bez brand assets) → použij **theme accent color square**:
   ```bash
   convert -size 32x32 xc:'#C5A55A' /documents/sites/<slug>/public/favicon.png
   ```
4. Logni do `.brand-context.md`: „WARN: favicon vygenerován ze [zdroj]. Doporučit klientovi nahrát vlastní favicon."

**Vždy zkopíruj favicon do projekt `public/`:**

```bash
cp /documents/brand/favicon.ico /documents/sites/<slug>/public/favicon.ico
# nebo
cp /documents/brand/favicon.png /documents/sites/<slug>/public/favicon.png
```

### Použití v Next.js layout.tsx

```tsx
// app/layout.tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '<Site title>',
  description: '<Brief description>',
  icons: {
    icon: '/favicon.ico',           // nebo /favicon.png
    apple: '/apple-touch-icon.png', // volitelné
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="cs">
      <body>
        <Header />
        {children}
      </body>
    </html>
  );
}

// components/Header.tsx — dark mode aware logo
import Image from 'next/image';

export function Header() {
  return (
    <header>
      {/* Light + dark mode varianty (pokud klient má obě) */}
      <picture>
        <source srcSet="/brand-assets/logo-inverse.png" media="(prefers-color-scheme: dark)" />
        <Image
          src="/brand-assets/logo.png"
          alt="<Brand name>"
          width={120}
          height={32}
          priority
        />
      </picture>
    </header>
  );
}
```

### Audit log v `.brand-context.md`

Vibe-builder eviduje brand identity asset stav:

```markdown
## Brand identity (asset audit)

- Logo (normální): /documents/brand/logo.png ✓ (220 KB)
- Logo (inverzní): /documents/brand/logo-inverse.png ✗ MISSING
  → fallback: CSS invert filter na logo.png pro dark mode
  → DOPORUČENO: nahrát logo-inverse.png přes brand-kit-generator
- Favicon: /documents/brand/favicon.ico ✗ MISSING
  → fallback: vygenerován z logo.png přes ImageMagick (32×32 PNG)
  → DOPORUČENO: nahrát favicon.ico (multi-size, universal browser support)
```

## File organization in projektu

```
/documents/sites/<slug>/public/
├── from-chat/              # Priority 1 — z chatu
│   └── hero.jpg
├── brand-assets/           # Priority 2 — copy z brand/
│   ├── logo.png
│   └── product-bioptron.jpg
├── generated/              # Priority 3 + 4 — AI generated
│   ├── hero.png
│   ├── feature-1.png
│   └── section-bg-2.png
└── (next/image optimized cache — auto)
```

Generated images:
- Default format: PNG (transparency support) nebo WebP (file size)
- Compress before commit: `next/image` to udělá automaticky při buildu

## Anti-slop pro generované obrázky

(Detail viz `04-anti-slop.md` sekce "Image-specific patterns")

**Always negative in prompts:**
- no people staring at camera (stock photo cliché)
- no AI watermarks, no signature artifacts
- no fake brand logos, no readable text
- no purple-to-blue gradients
- no glowing edges
- no plastic skin texture (DeepFake vibe)
- no symmetrical floating spheres
- no neon glow effects without justification

## Cost model — co stojí klienta peníze a co ne

`image_generate` tool má 2 model paths s odlišnou nákladovou strukturou:

| Model path | Kdy se použije | Cost klientovi |
|---|---|---|
| **GPT Image 2** (nativní, default) | Default pro Priority 3 a 4 | **Žádný per-image fee** — kryto CC/openclaw předplatným (paušál) |
| **FAL fallback** (flux-pro / ideogram) | Když GPT Image 2 selže nebo není dostupné | **Per-image cost** z klientova `FAL_KEY` (~$0.04-0.10 / image) |

Tj. v 95 % případů klient neplatí za obrázek (paušál). Jen když GPT Image 2
spadne (rate limit, content policy, technical) → FAL fallback → drobný
per-image náklad.

**Pro klienta informativně:** vibe-builder by neměl klienta zatěžovat
cenovkou GPT Image 2 generace (je to free pro klienta). Jen pokud sekvence
sklouzne na FAL, zmínit „použil jsem fallback model, ~3 Kč ze tvého FAL
kreditu" v finálním reportu.

## Reuse a re-generation

- **Reuse obrázku napříč projekty:** ne — každý projekt má vlastní generování
  pro brand consistency v daném kontextu
- **Re-generation při edit:** pokud klient žádá změnu briefu, regeneruje se
  jen obrázek souvisejících sekcí, ne všechny
- **Asset audit log:** vibe-builder vede v `<slug>/.brand-context.md` log:
  - Zdroj per slot (chat / brand-assets / generated-gpt / generated-fal / fallback)
  - Datum generování
  - Prompt použitý (pro Priority 3+4)
  - Model path (gpt-image-2 = free, fal = per-image cost)
  - Cost approx — **jen pro FAL gen**, GPT Image 2 negeneruje cost line
