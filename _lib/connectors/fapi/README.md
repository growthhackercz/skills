# FAPI.cz connector

TypeScript connector pro FAPI.cz fakturační systém. Pro použití ve vibe-builder
dashboard projektech.

## Struktura

```
fapi/
├── auth.ts          # Basic auth wrapper, env vars loader
├── operations.ts    # Read-only API operace + 6 high-level receptů
├── refresh.ts       # Background sync worker (cron/manual)
├── schema.sql       # Postgres cache tables + pre-aggregated views
├── docs.md          # Quick reference pro CTO agenta
└── README.md        # Tento soubor
```

## Pre-requisites

V env vars (přes `netlify-publisher env-set` nebo Netlify UI):

```bash
FAPI_USER=email@firma.cz
FAPI_TOKEN=<api-key z FAPI UI: Můj účet → API klíče>
NETLIFY_DATABASE_URL=<auto-set po `netlify db:init`>
```

## Workflow v vibe-builder dashboard projektu

### Krok 1: Init projekt (vibe-builder vygeneruje)

```
/documents/sites/<slug>/
├── package.json
│   "@cliqsales/connectors": "file:/home/node/.openclaw/cs-skills/_lib/connectors"
│   "@neondatabase/serverless": "latest"
├── migrations/0001_fapi.sql            # kopie schema.sql
├── netlify/functions/refresh-fapi.ts   # Scheduled Function
├── app/page.tsx                         # SSR fetch z DB views
└── netlify.toml                         # scheduled function config
```

### Krok 2: Apply migration

```bash
# Přes netlify-publisher:
python3 netlify_publish.py db-init --site-id <id>
# Pak ručně:
netlify db:push   # apply migrations/0001_fapi.sql
```

### Krok 3: Trigger first refresh (initial data load)

```bash
curl -X POST https://<slug>.netlify.app/.netlify/functions/refresh-fapi
```

Po prvním refreshi DB obsahuje data — dashboard začne fungovat.

### Krok 4: Scheduled refresh (každých 15 min)

Netlify Scheduled Function se sama spouští — žádný cron setup needed
na klientově straně.

## Dashboard usage

### Z server component (SSR):

```typescript
// app/page.tsx
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.NETLIFY_DATABASE_URL!);

export default async function Dashboard() {
  const [snapshot] = await sql`SELECT * FROM v_fapi_daily_snapshot`;
  const monthly = await sql`SELECT * FROM v_fapi_revenue_by_month LIMIT 12`;
  const topProducts = await sql`SELECT * FROM v_fapi_top_products LIMIT 10`;

  return (
    <main>
      <KPICard
        title="Obrat tento měsíc"
        value={formatCZK(snapshot.revenue_this_month)}
        delta={calcDelta(snapshot.revenue_this_month, snapshot.revenue_last_month)}
      />
      <KPICard title="Nezaplacené" value={formatCZK(snapshot.unpaid_total_czk)} />
      <KPICard title="Po splatnosti" value={String(snapshot.overdue_count)} />
      <AreaChart data={monthly} />
      <ProductsTable data={topProducts} />
    </main>
  );
}
```

### Z API route (klient refresh button):

```typescript
// app/api/refresh/route.ts
import { neon } from '@neondatabase/serverless';
import { refreshFapiAll } from '@cliqsales/connectors/fapi/refresh';

const sql = neon(process.env.NETLIFY_DATABASE_URL!);

export async function POST() {
  const result = await refreshFapiAll({
    exec: async (q, p) => sql(q, p),
  });
  return Response.json(result);
}
```

## Pre-aggregated views (dashboard-ready queries)

| View | Vrátí | Použití |
|---|---|---|
| `v_fapi_daily_snapshot` | KPI bar (5 metrik na jednom row) | Hero KPI cards |
| `v_fapi_revenue_by_month` | Časová řada tržeb po měsících | Area chart |
| `v_fapi_unpaid_invoices` | Nezaplacené faktury s bucket overdue | Table + filter |
| `v_fapi_top_customers` | Top zákazníci podle revenue | Sortable table |
| `v_fapi_top_products` | Top produkty podle revenue | Donut + table |

Detail v `schema.sql`.

## Co connector NEPOUŽÍVEJ pro

- **Write operace** (vystavit fakturu, refundovat) — read-only design.
- **Real-time data** (do 15 min lag je default). Pro real-time event-driven
  (např. „klient zaplatil → ihned email") použij FAPI webhooks (mimo
  scope tohoto connectoru).
- **Browser fetch** — vždy server-side (Function nebo SSR), nikdy direct
  z `app/page.tsx` client component (token v env, ne v JS bundle).

## Pro CTO: jak rozšířit connector

Pokud klient potřebuje další FAPI funkcionalitu, kterou tady nemáme:

1. **Přidej operaci do `operations.ts`** — podle pattern existing funkcí
2. **Pokud potřebuje nová data v cache** → přidej tabulku do `schema.sql`
3. **Update `refresh.ts`** o nový resource sync
4. **(Volitelně) přidej view** do `schema.sql` pro rychlý query

Reference materiály pro neviděné endpointy:
- `cs-skills/fapi/references/endpointy.md` — kompletní endpoint katalog
- https://napoveda.fapi.cz/article/84-ovladani-fapi-pres-api-rozhrani

## Verze

- v1.0 — 2026-05-27 — initial port z `cs-skills/fapi` Python helper
