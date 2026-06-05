# Patterns — dashboard (Databox) + web (landing) layouts

Konkrétní layouty per typ projektu. Vibe-builder vybere odpovídající
pattern podle klientova briefu.

## Dashboard pattern — Databox style

Inspirace: databox.com. Compact KPI cards, sparklines, period compare,
dark mode default (reduce eye fatigue).

### Layout structure

```
┌─────────────────────────────────────────────────────────┐
│  Header: Logo  |  [Period selector]  [Refresh] [Theme]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                       │
│  │KPI 1│ │KPI 2│ │KPI 3│ │KPI 4│   ← Top KPI row       │
│  └─────┘ └─────┘ └─────┘ └─────┘                       │
│                                                         │
│  ┌───────────────────────┐ ┌──────────────────┐        │
│  │  Main chart (revenue) │ │  Donut (split)   │        │
│  │  (large area chart)   │ │                  │        │
│  └───────────────────────┘ └──────────────────┘        │
│                                                         │
│  ┌─────────────────────────────────────────────┐       │
│  │  Detail table (top products / by category)  │       │
│  └─────────────────────────────────────────────┘       │
│                                                         │
│  Footer: Aktualizováno před 3 min | Refresh             │
└─────────────────────────────────────────────────────────┘
```

### Composition rules

- **Theme:** Deep Dark Mode default (CEO/manager friendly)
- **Hero archetype:** žádný hero — dashboard nepotřebuje conversion funnel
- **Header:** kompaktní, period picker prominentně (Today / 7d / 30d / 90d / Custom)
- **Top row:** 4 KPI cards horizontálně (na desktop), 2×2 (na tablet), stack (mobile)
- **KPI card obsahuje:** label + velké číslo + delta (zelená/červená) + sparkline
- **Charts:** Recharts pod Tremor, dark theme defaults
- **Tabulky:** sortable headers, tabular-nums, alternating row bg
- **Color use:**
  - Zelená (`accent`) = positive metric, growth
  - Červená (`destructive`) = negative metric, decline
  - Modrá (`primary`) = neutral metric, accent
  - Šedá (`muted`) = secondary text, deemphasis

### Dashboard čeleď komponentů (musí mít)

1. **PeriodSelector** — Tabs nebo Select (z shadcn)
2. **KPICard** — Card s Metric + sparkline (z Tremor)
3. **MainChart** — AreaChart (z Tremor, fullwidth)
4. **SplitChart** — DonutChart nebo BarChart (z Tremor)
5. **DataTable** — Tabulka s sortable headers (shadcn Table)
6. **RefreshButton** — Button s spinning Lucide icon na loading
7. **LastUpdated** — text "Aktualizováno před X min"

### Příklad dashboard layoutu (TSX)

```tsx
import { KPICard, SparklineCard } from "@/components/kpi";
import { Card } from "@tremor/react";
import { AreaChart, DonutChart } from "@tremor/react";
import { mockRevenueData, mockTopProducts } from "@/lib/data";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Obrat dashboard</h1>
        <div className="flex items-center gap-2">
          <PeriodSelector />
          <RefreshButton />
          <ThemeToggle />
        </div>
      </header>

      <main className="px-6 py-8 space-y-8 max-w-7xl mx-auto">
        {/* KPI row */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard title="Obrat tento měsíc" value="247 350 Kč" delta="+12.4%" trend="increase" />
          <KPICard title="Faktury vystavené" value="89" delta="+3" trend="moderateIncrease" />
          <KPICard title="Nezaplacené" value="42 100 Kč" delta="-3.1%" trend="decrease" />
          <KPICard title="Průměrná faktura" value="2 780 Kč" delta="+8.2%" trend="increase" />
        </section>

        {/* Main chart + split */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="lg:col-span-2 p-6">
            <h2 className="text-base font-semibold mb-4">Obrat za období</h2>
            <AreaChart
              data={mockRevenueData}
              index="date"
              categories={["value"]}
              colors={["blue"]}
              showLegend={false}
              className="h-72"
            />
          </Card>
          <Card className="p-6">
            <h2 className="text-base font-semibold mb-4">Po kategoriích</h2>
            <DonutChart
              data={mockTopProducts}
              category="revenue"
              index="name"
              colors={["blue", "cyan", "indigo", "violet", "purple"]}
              className="h-72"
            />
          </Card>
        </section>

        {/* Detail table */}
        <section>
          <Card className="p-6">
            <h2 className="text-base font-semibold mb-4">Top 10 produktů</h2>
            <ProductsTable data={mockTopProducts} />
          </Card>
        </section>
      </main>

      <footer className="border-t border-border px-6 py-4 text-sm text-muted-foreground flex items-center justify-between">
        <span>Aktualizováno před 3 min</span>
        <span>Powered by CliqSales</span>
      </footer>
    </div>
  );
}
```

## Web / Landing pattern

Inspirace: Linear, Vercel, Stripe, Cal.com landing pages.

### Layout structure (standard 6-sekce)

```
┌─────────────────────────────────────────┐
│  1. Hero (Giant / Mid / Mini)           │ ← composition anchor #1, #2 nebo #5
├─────────────────────────────────────────┤
│  2. Social proof (logos / trust signals)│ ← anchor #10 (metrics strip)
├─────────────────────────────────────────┤
│  3. Features (bento grid)               │ ← anchor #7 (bento) nebo #3 (off-grid)
├─────────────────────────────────────────┤
│  4. Detail / how it works               │ ← anchor #9 (vertical rhythm)
├─────────────────────────────────────────┤
│  5. Testimonials                        │ ← anchor #11 (split quote wall)
├─────────────────────────────────────────┤
│  6. CTA + Footer                        │ ← anchor #5 (stacked center)
└─────────────────────────────────────────┘
```

### Composition rules

- **Theme:** Pristine Light Mode default pro většinu B2B
  (Bold Studio pro creative, Quiet Premium pro luxury)
- **Section padding:** `py-24 md:py-32` minimum
- **Container:** `max-w-7xl mx-auto px-6 md:px-12`
- **Hero conversion:** 1 primary CTA prominentně, 1 secondary (volitelně)
- **Pricing section:** pokud klient prodává, ABOVE THE FOLD na desktop

### Landing layout (TSX příklad — Mid hero archetype)

```tsx
import { Hero } from "@/components/sections/hero";
import { LogosStrip } from "@/components/sections/logos";
import { Features } from "@/components/sections/features";
import { HowItWorks } from "@/components/sections/how";
import { Testimonials } from "@/components/sections/testimonials";
import { CTA } from "@/components/sections/cta";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <Hero
        headline="Vaše firma. Vaše data. Vaše dashboardy."
        sub="Vytvoříme vám personalizovaný dashboard nad Fakturoidem, bankovním účtem a Meta Ads. Za 2 minuty místo 2 měsíců s programátorem."
        cta={{ label: "Začít zdarma", href: "/start" }}
      />

      <LogosStrip
        title="Důvěřuje nám 1 750+ českých firem"
        logos={[/* real client logos */]}
      />

      <Features
        title="Co všechno postavíte"
        items={[
          { title: "Cashflow cockpit", description: "..." },
          { title: "True ROAS", description: "..." },
          { title: "Pohledávky", description: "..." },
        ]}
      />

      <HowItWorks
        steps={[
          { number: "01", title: "Připojte data", description: "..." },
          { number: "02", title: "Popište co chcete", description: "..." },
          { number: "03", title: "Dostaňte URL", description: "..." },
        ]}
      />

      <Testimonials quotes={[/* ... */]} />

      <CTA
        headline="Začněte dnes. Bez programátora."
        cta={{ label: "Vyzkoušet 7 dní zdarma", href: "/signup" }}
      />
    </main>
  );
}
```

## Per-industry presety

### E-commerce (Shoptet / WooCommerce klient)
- Top KPIs: tržby dnes, objednávky dnes, AOV, conversion rate
- Charts: trend tržeb, top produkty (bar chart), funnel
- Theme: Deep Dark (CEO dashboard) nebo Pristine (denní hub)

### Služby / konzultace (B2B)
- Top KPIs: aktivní zakázky, fakturováno měsíc, pohledávky, kapacita
- Charts: utilization, revenue pipeline
- Theme: Pristine Light (corporate trust)

### Řemeslo / lokální business
- Top KPIs: zakázky dnes, kalendář, příjmy měsíc, pohledávky
- Charts: kalendář heatmap, weekly revenue
- Theme: Bold Studio (statement) nebo Pristine

### Restaurace / kavárna
- Top KPIs: tržby dnes, průměrný účet, top jídla, obsazenost
- Charts: hodinová tržba, top items
- Theme: Bold Studio (warm, inviting)

## Loading / empty / error states

Každá komponenta MUSÍ mít 3 states:

### Loading
```tsx
import { Skeleton } from "@/components/ui/skeleton";

<Card className="p-6">
  <Skeleton className="h-4 w-24 mb-2" />
  <Skeleton className="h-10 w-32 mb-4" />
  <Skeleton className="h-12 w-full" />
</Card>
```

### Empty
```tsx
<div className="text-center py-12 text-muted-foreground">
  <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
  <p className="text-sm">Žádná data k zobrazení.</p>
  <p className="text-xs mt-2">Připojte zdroj dat v nastavení.</p>
</div>
```

### Error
```tsx
<div className="text-center py-12">
  <AlertCircle className="h-12 w-12 mx-auto mb-4 text-destructive opacity-70" />
  <p className="text-sm font-medium">Nepodařilo se načíst data.</p>
  <Button variant="outline" size="sm" className="mt-4">Zkusit znovu</Button>
</div>
```
