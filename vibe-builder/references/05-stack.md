# Stack lock-in — Next.js + ruční primitivy + Tremor + code patterns

> ⚡ **Soubor pokrývá **web i dashboard**. Při dashboardu přeskoč sekce o pohybu,
GSAP a scrollových scénách.**

Toto je **POVINNÝ** stack pro všechny vibe-builder outputy. Žádné odchylky
(žádný Vue, žádný Svelte, žádný custom CSS framework). Důvod: konzistence
napříč klientely + recyklace agent znalosti.

## Stack components

| Vrstva | Knihovna | Verze | Důvod |
|---|---|---|---|
| **Framework** | Next.js | **15.x (pin)** | App Router, RSC, static + SSR. Pin na 15 = React 18 default (Tremor compat). |
| **React** | React + ReactDOM | **18.x (pin)** | Tremor zatím nepodporuje React 19. |
| **UI components** | ruční primitivy (shadcn styl) | — | Card/Button/Badge píšeme ručně do `src/components/ui/` (vzory níže). **shadcn CLI je ZAKÁZANÉ** — viz Preflight. |
| **Data viz** | Tremor | latest | KPI cards, sparklines, charts pro dashboards |
| **Charts** | Recharts | latest (under Tremor) | Battle-tested |
| **Styling** | Tailwind CSS | v4 | Utility-first, CSS variables, design tokens |
| **Icons** | Lucide React | latest | Konzistentní stroke, large library |
| **Motion** | GSAP + @gsap/react | latest | ScrollTrigger, ScrollSmoother, SplitText, CustomEase, Flip, DrawSVG — vše zdarma (od akvizice Webflow), veřejný npm. Doktrína: 10-motion-web.md, API: gsap/ |
| **Typography** | Inter + Geist Mono (default) / display face dle webDNA.md | `next/font/google` nebo self-host | Web s vlastním světem má display font s charakterem (viz 01 editoriální podlaha); Inter zůstává UI/body default |
| **Theme tokens** | CSS custom properties (OKLCH) | — | Light/dark mode switching |

✅ **Ověřená kombinace (11. 8. 2026):** React 18.3.1 · Tremor 3.18.7 ·
Recharts 3.10.1 · Lucide 1.31.0 · Geist 1.7.2 · clsx 2.1.1 ·
tailwind-merge 3.6.0 · GSAP 3.15.0 · @gsap/react 2.1.2. Nainstalováno
společně s `--legacy-peer-deps`: prošlo bez `ERESOLVE` a bez zranitelností.
Když verzi měníš, ověř celou sadu znovu — ne jen ten jeden balíček.

⚠️ **Důležité — verze:** Vždy používej **`create-next-app@15`**, NIKDY `@latest`.
Next.js 16 instaluje React 19, který má peer dep konflikt s Tremor 3.x.
Vyzkoušeno v reálném testu — pádilo na `ERESOLVE` při `npm install`.

🛑 **Zapiš přepínač do `package.json`, jinak ho publisher nezná.** Ty stavíš
s `--legacy-peer-deps`, ale `netlify-publisher` při svém buildu spouští obyčejný
`npm install` — projekt by u něj spadl na `ERESOLVE`. Hned po vytvoření projektu
proto doplň:

```json
{
  "cliqsales": {
    "skillVersion": "1.3.4",
    "installFlags": ["--legacy-peer-deps"]
  }
}
```

Publisher to přečte a přepínač použije. Hodnoty ověřuje proti allowlistu, takže
si tam nevymýšlej vlastní argumenty.

⚠️ **`--legacy-peer-deps` flag:** Vždy přidávej k `npm install` voláním
v setup sequence. Bezpečný workaround pro Tremor peer warnings, nepřepisuje
deps, jen ignoruje warnings.

## Setup sekvence (kterou volá vibe-builder)

```bash
PROJECT_DIR="/documents/sites/<slug>"
cd /documents/sites

# 1. Create Next.js 15 project (React 18 = Tremor compat)
npx create-next-app@15 <slug> \
  --typescript \
  --tailwind \
  --app \
  --use-npm \
  --src-dir \
  --no-eslint \
  --no-turbopack \
  --import-alias "@/*"
# ⚠️ --no-turbopack je POVINNÝ: bez něj se CLI interaktivně ptá a
# v neinteraktivním běhu (agent) visí/selže.

cd <slug>

# 2. TypeScript deps explicit preinstall (Next.js auto-install se může zaseknout
#    na peer dep konfliktech — preventivně to děláme manuálně)
npm install --save-dev --legacy-peer-deps \
  typescript @types/react @types/node @types/react-dom
chmod +x node_modules/next/dist/bin/next 2>/dev/null || true

# 3. Stack dependencies (Tremor + Recharts + Lucide + Geist font)
#    Verze jsou PŘIPNUTÉ. `@latest` znamená, že každý klient dostane jiný
#    strom závislostí a jeden den to přestane jít sestavit bez naší změny.
npm install --legacy-peer-deps --save-exact \
  @tremor/react@3.18.7 recharts@3.10.1 lucide-react@1.31.0 geist@1.7.2 \
  clsx@2.1.1 tailwind-merge@3.6.0
chmod +x node_modules/next/dist/bin/next 2>/dev/null || true

# 3b. Motion (každý web — tier 1+; dashboardy tier 0 tohle přeskočí)
npm install --legacy-peer-deps --save-exact gsap@3.15.0 @gsap/react@2.1.2
chmod +x node_modules/next/dist/bin/next 2>/dev/null || true
```

Každý další `npm install` v tematické referenci má stejný pár řádků:
instalace vždy s `--legacy-peer-deps`, bezprostředně potom exec-bit fix. Příkaz
neodkládej „až po všech instalacích" — právě další instalace ho může znovu
zahodit.

**🛑 shadcn CLI (`npx shadcn init` / `npx shadcn add`) je ZAKÁZANÉ.**
Aktuální shadcn CLI instaluje `@base-ui/react` s rozbitými závislostmi a
setup shoří na peer-deps (ověřeno v reálných buildech — spálilo desítky
kroků). UI primitivy (Card, Button, Badge, Input…) piš **ručně** do
`src/components/ui/` podle vzorů v tomto souboru + `cn()` helper do
`src/lib/utils.ts`:

```ts
// src/lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }
```

**Po každém `npm install`** ověř `package.json` a ujisti se, že:
- `react` a `react-dom` mají verzi `^18.x` (NE `^19.x`)
- `next` má verzi `15.x` (NE `16.x`)

Pokud Next.js někdy upgrade-uje na React 19 automaticky, downgrade ručně:
```bash
npm install --save-exact react@18.3.1 react-dom@18.3.1 --legacy-peer-deps
chmod +x node_modules/next/dist/bin/next 2>/dev/null || true
```

### Primitivy per typ projektu (ručně psané)

- **Web / Landing:** Card, Button, Badge — obvykle stačí; většina sekcí je
  custom markup, primitivy nevynucuj tam, kde stačí `<section>` + Tailwind.
- **Dashboard:** Card, Button, Tabs, Badge, Skeleton (+ Tremor pro data viz).
- **Aplikace s formuláři:** Card, Button, Input, Label, Textarea, Checkbox,
  Dialog — každý ~20–60 řádků, vzor Card/Button je v tomto souboru.

## Preflight prostředí (VPS kontejner) — POVINNÉ znalosti

Agent na klientském VPS běží v openclaw kontejneru. Tři známé pasti — řeš
je preventivně, ne až po chybě (každá v reálném běhu spálila 5–15 kroků):

1. **npm zahazuje exec bit na `/documents` volume.** Po KAŽDÉM
   `npm install` spusť `chmod +x node_modules/next/dist/bin/next`.
   Symptom: `sh: 1: next: Permission denied`. Neřeš debugem — chmod a dál.
   Platí i pro jiné CLI v `node_modules/.bin` (symlinky vedou na soubory
   bez exec bitu).
2. **`chromium --headless` v kontejneru NEFUNGUJE** (chybí dbus; hlásí
   `Failed to connect to the bus`). Na screenshoty jdi ROVNOU přes
   Playwright (`node` script s `playwright.chromium.launch()`); pokud
   Playwright chybí, `npx playwright install chromium`. Nikdy neopakuj
   chromium volání — první dbus error = definitivní.
3. **`create-next-app` bez `--no-turbopack` visí** na interaktivní otázce
   (viz Setup sekvence). Flag je POVINNÝ vždy, hned napoprvé.

## File struktura

```
<slug>/
├── package.json
├── next.config.js              # static export NEBO SSR podle typu
├── tailwind.config.ts          # tokens z theme
├── tsconfig.json
├── postcss.config.mjs
├── public/
│   └── (assets — pokud nějaké)
└── src/
    ├── app/
    │   ├── layout.tsx          # Inter + Geist Mono fonts, html lang="cs"
    │   ├── page.tsx            # hlavní stránka
    │   └── globals.css         # Tailwind base + theme tokens
    ├── components/
    │   ├── sections/           # custom sekce per page
    │   │   ├── hero.tsx
    │   │   ├── features.tsx
    │   │   └── ...
    │   └── ui/                 # ručně psané primitivy (shadcn styl)
    │       ├── card.tsx
    │       ├── button.tsx
    │       └── ...
    └── lib/
        ├── utils.ts            # cn() helper (clsx + tailwind-merge)
        └── data.ts             # mock data pro dashboardy
```

## next.config.js — static export vs SSR

### Static export (default pro weby, landing pages)
```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
};
module.exports = nextConfig;
```

### SSR (JEN s pojmenovaným důvodem, ne pro dashboardy)

⚠️ Dashboard nad daty jede **statický export + Netlify funkce**, viz
`16-aplikace.md` (přepnutí na SSR jen kvůli datům je tam v zákazech).
SSR sáhni jen tehdy, když máš důvod, který umíš pojmenovat, a zapiš ho
do `webDNA.md`.
```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // bez output: 'export' → Next.js auto-detekuje SSR
  images: { unoptimized: false },
};
module.exports = nextConfig;
```

## app/layout.tsx — typo + theme setup

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { GeistMono } from "geist/font/mono";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "latin-ext"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "<projekt title>",
  description: "<projekt description z briefu>",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="cs" className={`${inter.variable} ${GeistMono.variable}`}>
      <body className="bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
```

## app/globals.css — theme tokens (Pristine example)

```css
@import "tailwindcss";

@theme {
  --font-sans: var(--font-sans), system-ui, sans-serif;
  --font-mono: var(--font-geist-mono), monospace;

  --color-background: oklch(98% 0.005 90);
  --color-foreground: oklch(20% 0.01 280);
  --color-muted: oklch(94% 0.008 90);
  --color-muted-foreground: oklch(45% 0.01 280);
  --color-border: oklch(90% 0.005 90);
  --color-primary: oklch(20% 0.01 280);
  --color-primary-foreground: oklch(98% 0.005 90);
  --color-accent: oklch(70% 0.18 35);
}

@layer base {
  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
  /* Tabular numerals pro metriky */
  .tabular {
    font-variant-numeric: tabular-nums;
  }
}
```

## Tremor KPI card pattern

```tsx
import { Card, Metric, Text, Flex, BadgeDelta } from "@tremor/react";

export function KPICard({
  title,
  value,
  delta,
  trend,
}: {
  title: string;
  value: string;
  delta: string;
  trend: "increase" | "decrease" | "moderateIncrease" | "moderateDecrease";
}) {
  return (
    <Card className="p-6">
      <Flex alignItems="start">
        <div>
          <Text className="text-muted-foreground">{title}</Text>
          <Metric className="tabular">{value}</Metric>
        </div>
        <BadgeDelta deltaType={trend}>{delta}</BadgeDelta>
      </Flex>
    </Card>
  );
}
```

## Tremor sparkline pattern

```tsx
import { Card, SparkAreaChart } from "@tremor/react";

export function SparklineCard({
  title,
  value,
  data,
}: {
  title: string;
  value: string;
  data: { date: string; value: number }[];
}) {
  return (
    <Card className="p-6">
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="mt-1 text-3xl font-semibold tabular">{value}</p>
      <SparkAreaChart
        data={data}
        index="date"
        categories={["value"]}
        colors={["blue"]}
        className="mt-4 h-12"
      />
    </Card>
  );
}
```

## Card pattern — ručně psaný primitiv (pro weby)

```tsx
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function FeatureCard({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: { label: string; href: string };
}) {
  return (
    <Card className="border-border/50 transition-shadow hover:shadow-md">
      <CardHeader>
        <CardTitle className="text-xl">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      {action && (
        <CardContent>
          <Button asChild variant="ghost" className="px-0">
            <a href={action.href}>{action.label} →</a>
          </Button>
        </CardContent>
      )}
    </Card>
  );
}
```

## Hero pattern — Giant Statement archetype

```tsx
export function GiantHero({
  headline,
  sub,
  cta,
}: {
  headline: string;
  sub: string;
  cta: { label: string; href: string };
}) {
  return (
    <section className="min-h-[85vh] flex items-center justify-center px-6 py-32">
      <div className="max-w-5xl text-center">
        <h1 className="text-6xl md:text-7xl lg:text-8xl font-semibold tracking-tight text-balance">
          {headline}
        </h1>
        <p className="mt-8 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto text-balance">
          {sub}
        </p>
        <div className="mt-12">
          <a
            href={cta.href}
            className="inline-flex items-center justify-center rounded-md bg-primary text-primary-foreground px-8 py-4 text-base font-semibold transition-colors hover:bg-primary/90"
          >
            {cta.label}
          </a>
        </div>
      </div>
    </section>
  );
}
```

## Lucide icons pattern

```tsx
import { ArrowUpRight, Check, TrendingUp, AlertCircle } from "lucide-react";

// V buttons / CTAs
<Button>
  Začít zdarma <ArrowUpRight className="ml-2 h-4 w-4" />
</Button>

// V KPI delta
<BadgeDelta deltaType="increase">
  <TrendingUp className="h-3 w-3" /> 12.4%
</BadgeDelta>
```

## Mock data pattern (pro dashboardy)

```ts
// lib/data.ts
export const mockRevenueData = [
  { date: "2026-01", value: 124_500 },
  { date: "2026-02", value: 138_900 },
  { date: "2026-03", value: 156_200 },
  { date: "2026-04", value: 148_700 },
  { date: "2026-05", value: 172_300 },
];

export const mockTopProducts = [
  { name: "Produkt A", revenue: 84_200, share: 18.4 },
  { name: "Produkt B", revenue: 67_500, share: 14.7 },
  // ...
];
```

V V2 nahradíme mock data za real data connectory (Fakturoid, GA4, Meta Ads).
V0.1 vždy mock data s realistic Czech values (Kč, datumy v ISO formátu).

## next/image pattern (obrázky v generovaném kódu)

Vždy `next/image`, nikdy `<img>` tag. Důvody: lazy loading, blur placeholder,
responsive sizes, automatická WebP konverze, performance.

### Hero image (priority load)

```tsx
import Image from "next/image";

<Image
  src="/generated/hero.png"   // nebo /from-chat/, /brand-assets/
  alt="Modern Czech café interior, warm wood and large windows"
  width={1920}
  height={1080}
  priority           // ← important: hero loaduje first, bez lazy
  className="object-cover w-full h-full"
  sizes="100vw"
/>
```

### Section background

```tsx
<div className="relative w-full h-[600px]">
  <Image
    src="/generated/section-bg.png"
    alt=""             // decorative — empty alt
    fill
    className="object-cover"
    sizes="100vw"
  />
  {/* Content over background */}
  <div className="relative z-10 ...">...</div>
</div>
```

### Bento card thumbnail

```tsx
<Image
  src="/brand-assets/product-bioptron.jpg"
  alt="Bioptron MedAll therapy device"
  width={800}
  height={600}
  className="rounded-lg object-cover aspect-[4/3]"
  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
/>
```

### Logo (s dark mode aware variantami)

```tsx
{/* Pokud má klient JEN normální logo */}
<Image
  src="/brand-assets/logo.png"
  alt="<brand name>"
  width={120}
  height={32}
  priority
/>

{/* Pokud má klient OBĚ varianty (light + dark) — auto-switch */}
<picture>
  <source srcSet="/brand-assets/logo-inverse.png" media="(prefers-color-scheme: dark)" />
  <Image
    src="/brand-assets/logo.png"
    alt="<brand name>"
    width={120}
    height={32}
    priority
  />
</picture>

{/* CSS fallback pro dark mode dashboard když inverzní chybí */}
<Image
  src="/brand-assets/logo.png"
  alt="<brand name>"
  width={120}
  height={32}
  priority
  className="dark:invert dark:brightness-110"  // Tailwind dark mode utility
/>
```

### Favicon (= browser tab icon)

V `app/layout.tsx`:

```tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Site title',
  description: 'Site description',
  icons: {
    icon: '/favicon.ico',              // primary (multi-size)
    shortcut: '/favicon.ico',
    apple: '/apple-touch-icon.png',    // pro iOS home screen (180x180)
  },
};
```

**Vibe-builder MUSÍ:**
1. Detekovat `favicon.ico` / `favicon.png` v `/documents/brand/`
2. Pokud existuje → copy do `<slug>/public/favicon.ico`
3. Pokud chybí → vygenerovat z loga přes **ffmpeg** (ImageMagick `convert`
   v kontejneru NENÍ): `ffmpeg -i logo.png -vf scale=32:32 favicon.png`
4. Nastavit v `metadata.icons` v `layout.tsx`

Detail v `07-images.md` sekce „Brand identity assets".

### Asset source decision tree (komentář v kódu pro tracking)

V každém TSX souboru kde používáš obrázek, přidej komentář se zdrojem:

```tsx
{/* asset: from-chat — client uploaded in prompt */}
<Image src="/from-chat/hero.jpg" ... />

{/* asset: brand-assets — copy from /documents/brand/products/X/images/ */}
<Image src="/brand-assets/product.png" ... />

{/* asset: generated (Priority 3) — AI brand-aware, prompt v .brand-context.md */}
<Image src="/generated/hero.png" ... />

{/* asset: generated (Priority 4 fallback) — generic AI, no brand context */}
<Image src="/generated/section-bg.png" ... />
```

### Image config v next.config.js

Pro static export (default web):
```js
images: { unoptimized: true }   // next/image neoptimalizuje, ale stále lazy-loaduje
```

Pro SSR (jen s pojmenovaným důvodem, viz výš):
```js
images: {
  unoptimized: false,
  formats: ['image/webp', 'image/avif'],
  deviceSizes: [640, 768, 1024, 1280, 1536, 1920],
}
```

## Dark mode toggle (volitelný pro dashboardy)

```tsx
"use client";
import { useState, useEffect } from "react";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">("dark");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="p-2 rounded-md hover:bg-muted"
      aria-label="Toggle theme"
    >
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}
```
