# CliqSales connectors — knihovna integrací pro dashboard projekty

TypeScript connectory pro externí API služby. Používané vibe-builder
dashboard projekty pro stahování + cache + dotazy dat.

## Architektura

```
cs-skills/_lib/connectors/
├── README.md                    ← tento soubor (overview)
│
├── _template/                   ← KOSTRA pro nový connector
│   ├── auth.ts.template
│   ├── operations.ts.template
│   ├── schema.sql.template
│   ├── refresh.ts.template
│   ├── docs.md.template
│   └── README.md                (krok-po-kroku návod pro CTO)
│
├── fapi/                        ← Výchozí connector (FAPI.cz)
│   ├── auth.ts, operations.ts, schema.sql, refresh.ts, docs.md, README.md
│
├── fio/                         ← Výchozí connector (Fio Banka)
│   ├── auth.ts, operations.ts, schema.sql, refresh.ts, docs.md, README.md
│
├── (TODO) fakturoid/
├── (TODO) ga4/
├── (TODO) meta-ads/
├── (TODO) google-ads/
└── (TODO) ghl-crm/
```

## Princip

Každý connector je **standalone TypeScript modul** se 4-6 soubory:

| Soubor | Účel |
|---|---|
| `auth.ts` | Načítá env vars + sestavuje auth headers |
| `operations.ts` | API operace (fetch z provider) + high-level recepty |
| `schema.sql` | Postgres cache tabulky + pre-aggregated views |
| `refresh.ts` | Background sync worker (cron + manual) |
| `docs.md` | Quick reference pro CTO agenta |
| `README.md` | Jak používat, jak rozšířit |

## Použití ve vibe-builder dashboard projektu

Nejdřív přidej lokální dependency do vygenerovaného projektu:

```bash
npm pkg set dependencies.@cliqsales/connectors="file:/home/node/.openclaw/cs-skills/_lib/connectors"
```

U Next.js projektu, který importuje connectory, přidej do `next.config.js`:

```js
const nextConfig = {
  transpilePackages: ['@cliqsales/connectors'],
};
module.exports = nextConfig;
```

```typescript
// app/page.tsx (SSR — serveroviá komponenta)
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.NETLIFY_DATABASE_URL!);

export default async function Dashboard() {
  // Dotazujeme se pre-aggregated views — NE přímo provider API
  const [snapshot] = await sql`SELECT * FROM v_fapi_daily_snapshot`;
  return <KPICard value={snapshot.revenue_this_month} />;
}
```

```typescript
// app/api/refresh/route.ts (Netlify Function)
import { refreshFapiAll } from '@cliqsales/connectors/fapi/refresh';
const sql = neon(process.env.NETLIFY_DATABASE_URL!);
export async function POST() {
  return Response.json(await refreshFapiAll({ exec: sql }));
}
export const config = { schedule: '@every 15m' };
```

## Dva use cases

### A) Top provideri (výchozí connectory)

Pro nejpoužívanější služby (FAPI, Fakturoid, Fio, GA4, Meta Ads, GHL)
máme **production-ready** connectory v této složce.

Vibe-builder je při generování dashboardu rovnou importuje. **Klient
nečeká** — connector už existuje, dashboard je za 2 minuty.

### B) Obscure / custom provideri (CTO replikuje template)

Když klient požaduje integraci na službu, pro kterou tady connector
nemáme (např. Stormware Pohoda, Shoptet, vlastní firemní API):

1. CTO si načte API dokumentaci přes WebFetch
2. Zkopíruje `_template/` jako `<provider-slug>/`
3. Adaptuje podle docs (auth + endpoints + JSON shapes)
4. Otestuje ad hoc
5. Uloží — další klient s tímto providerem má connector ready

**Detail postupu:** `_template/README.md`

## Pravidla

### Bezpečnost

- ✅ Vždy server-side (Netlify Function nebo SSR), nikdy browser
- ✅ Tokeny v env vars (přes `netlify-publisher env-set`), nikdy hardcoded
- ✅ Token sanitization v error logs
- ✅ Read-only default (pro write operace separátní connector s explicit flagy)

### Performance

- ✅ Cache vrstva v Netlify Postgres — dashboard čte z views, ne z provider API
- ✅ Background refresh každých 15-60 min (Scheduled Function)
- ✅ Pre-aggregated views pro dashboard queries (žádné raw scans)
- ✅ Indexes na často filtrovaná pole

### Konzistence

- ✅ Stejné rozhraní napříč connectory (`loadCredentials`, `getX`, `refreshAll`)
- ✅ Stejný retry / timeout pattern (exponential backoff, 30s timeout)
- ✅ Stejné error handling (typed exceptions, NEVER swallow errors)
- ✅ Stejný cache schema pattern (raw JSONB + extracted columns + views)

## Roadmap připravených connectorů

| Provider | Status | Use case |
|---|---|---|
| **FAPI.cz** | ✅ v1.0 | České fakturační SaaS, tržby, klienti, splatnost |
| **Fio Banka** | ✅ v1.0 | Bankovní transakce, cashflow, párování s fakturami |
| **Fakturoid** | 🔄 TODO | České fakturační SaaS (větší market share) |
| **GA4** | 🔄 TODO | Google Analytics — návštěvy, konverze |
| **Meta Ads** | 🔄 TODO | Facebook/Instagram reklama — spend, ROAS |
| **Google Ads** | 🔄 TODO | Search/Display reklama |
| **GHL CRM** | 🔄 TODO | CliqSales platforma — leads, deals |

## Pro CTO agenta: kdy NEpoužít connector

- **Custom data od klienta** (CSV upload, jednorázový import) → bez connectoru,
  použij vibe-builder generic webhook receiver pattern
- **One-shot dotazy v chatu** (klient: "Kolik jsem vydělal v dubnu?")
  → použij existing `cs-skills/fapi` Python skill (pro FAPI) místo
  inicializace celého dashboardu
- **Real-time event-driven** (webhook → action) → použij FAPI/GHL webhooks
  + samostatný handler, ne tento connector pattern

## Verze knihovny

- v1.0 — 2026-05-27 — initial release s FAPI connectorem + template
