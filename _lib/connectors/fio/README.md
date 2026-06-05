# Fio Banka connector

TypeScript connector pro Fio Banka API. Použití ve vibe-builder dashboard
projektech pro cashflow, transakce, párování s fakturami.

## Struktura

```
fio/
├── auth.ts          # Token loader + URL sanitization
├── operations.ts    # Periods/by-id/last endpoints + 4 high-level recepty
├── refresh.ts       # Background sync (idempotentní periods)
├── schema.sql       # Postgres cache: snapshots + transactions + 5 views
├── docs.md          # CTO reference (column mapping, edge cases, cross-ref s FAPI)
└── README.md        # Tento soubor
```

## Pre-requisites

V env vars:

```bash
FIO_TOKEN=<read-only token z Internetbanky>
NETLIFY_DATABASE_URL=<auto-set po `netlify db:init`>
```

Token získáš v Fio Internetbance:
1. Nastavení → Nastavení API
2. Vytvořit nový token
3. **Read-only access** (nepotvrzuj write permissions)
4. Zkopíruj → ulož přes `netlify-publisher env-set FIO_TOKEN=xxx`

## ⚠️ Důležité — Rate limit 30 sekund

Fio API má **velmi přísný** rate limit: 1 request per 30 sec per token.

**Co to znamená v praxi:**
- Cron refresh interval ≥ 5 minut (komfortní margin)
- Klient klikne „Refresh" v dashboardu → 30s lockout button
- Pokud klient má víc Fio účtů (víc tokenů) — refresh sequentially se sleep

Connector retry-uje 1× po HTTP 409 s 35s wait. Pokud druhý pokus selže,
hodí explicit error („token used too recently").

## Workflow ve vibe-builder dashboard projektu

### Krok 1: Setup (jednorázově)

```bash
# Apply schema (po netlify db:init)
psql $NETLIFY_DATABASE_URL < node_modules/@cliqsales/connectors/fio/schema.sql

# Set token
netlify env:set FIO_TOKEN <token-z-internetbanky>
```

### Krok 2: Schedule refresh (Netlify Function)

```typescript
// app/api/refresh/fio/route.ts
import { neon } from '@neondatabase/serverless';
import { refreshFioAll } from '@cliqsales/connectors/fio/refresh';

const sql = neon(process.env.NETLIFY_DATABASE_URL!);

export async function POST() {
  return Response.json(await refreshFioAll({ exec: sql }));
}

export const config = { schedule: '@every 15m' };  // Pohodlný interval
```

### Krok 3: Dashboard view (SSR component)

```typescript
// app/page.tsx
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.NETLIFY_DATABASE_URL!);

export default async function CashflowDashboard() {
  const [snapshot] = await sql`SELECT * FROM v_fio_cashflow_snapshot LIMIT 1`;
  const dailyBalance = await sql`SELECT * FROM v_fio_daily_balance LIMIT 90`;
  const topCounter = await sql`SELECT * FROM v_fio_top_counterparties WHERE direction = 'incoming' LIMIT 10`;

  return (
    <main>
      <KPICard
        title="Aktuální zůstatek"
        value={formatCZK(snapshot.current_balance)}
      />
      <KPICard
        title="Tento měsíc příjmy"
        value={formatCZK(snapshot.month_incoming)}
        delta={`${snapshot.month_transaction_count} transakcí`}
      />
      <KPICard
        title="Tento měsíc výdaje"
        value={formatCZK(snapshot.month_outgoing)}
      />
      <KPICard
        title="Net change"
        value={formatCZK(snapshot.month_net_change)}
        trend={snapshot.month_net_change > 0 ? 'increase' : 'decrease'}
      />

      <LineChart data={dailyBalance} x="date" y="cumulative_change" />
      <DataTable data={topCounter} />
    </main>
  );
}
```

## Pre-aggregated views

| View | Vrátí | Dashboard použití |
|---|---|---|
| `v_fio_cashflow_snapshot` | Aktuální zůstatek + měsíční KPIs | Hero KPI cards (4-5 metrik) |
| `v_fio_daily_balance` | Denní zůstatky 90 dní | Line chart trendu |
| `v_fio_monthly_cashflow` | Měsíční příjmy/výdaje 12 měs | Bar chart srovnání |
| `v_fio_top_counterparties` | Top platící / placené | Sortable table |
| `v_fio_incoming_with_vs` | Příchozí platby s VS | Cross-reference s fakturami |

## Cross-reference s FAPI / Fakturoid

**Hlavní hodnota Fio connectoru = párování plateb s fakturami.**

```sql
-- "Cash gap" = fakturováno vs reálně přišlo
SELECT
  date_trunc('month', i.create_date) AS month,
  SUM(i.total_czk) AS invoiced,
  SUM(COALESCE(bt.amount, 0)) AS bank_received,
  SUM(i.total_czk) - SUM(COALESCE(bt.amount, 0)) AS gap
FROM fapi_invoices i
LEFT JOIN fio_transactions bt
  ON bt.variable_symbol = i.variable_symbol
  AND bt.amount > 0
WHERE i.create_date >= CURRENT_DATE - INTERVAL '6 months'
  AND i.paid = TRUE
GROUP BY 1
ORDER BY 1 DESC;
```

Tento JOIN je **Pavlův Top #2 cross-reference dashboard** (Cash Gap Forecast).

## Co connector NEPOUŽÍVEJ pro

- **Real-time notifikace** (klient zaplatil → ihned email) — Fio nemá webhooks,
  pollovací model
- **Vystavení platby** — Fio API je read-only
- **Multi-account v jednom volání** — 1 token = 1 účet (pro víc účtů
  spravuj víc env vars: FIO_TOKEN_BUSINESS, FIO_TOKEN_PERSONAL...)

## Pro CTO: jak rozšířit

Pokud klient potřebuje další Fio funkcionalitu:

1. **Více detailních fields z column mapping** → rozšiř `FIO_COLUMN_MAP` v
   `operations.ts` (Fio má až ~30 column polí, my používáme top 17)
2. **Multi-token support** (klient má víc Fio účtů) → upgrade `loadFioCredentials()`
   na list tokenů + iterate
3. **PDF výpisy** → Fio API podporuje, ale není v tomto connectoru
   (přidej `.pdf` endpoint)

Reference: `cs-skills/_lib/connectors/_template/README.md` (= obecný postup
pro rozšiřování connectorů).

## Verze

- v1.0 — 2026-05-27 — initial release
