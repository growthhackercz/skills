# FAPI.cz — quick reference pro CTO agenta

Krátký cheat-sheet pro práci s FAPI API v dashboard projektech.

Plný reference materiál (endpointy, filtry, pasti) viz existing skill
`cs-skills/fapi/references/` — tento dokument je extrakt klíčových věcí.

## API základ

- **Base URL:** `https://api.fapi.cz`
- **Auth:** HTTP Basic auth (user email + API token)
- **Format:** JSON
- **Rate limit:** nedokumentován (empiricky ~60 req/min bezpečně)
- **Read-only operace** v tomto connectoru — pro write (vystavit fakturu)
  napiš samostatný skill nebo extend explicit

## Klíčové endpointy

| Endpoint | Co vrací | Použití |
|---|---|---|
| `GET /invoices` | List faktur | Detail tržeb, splatnost, top zákazníci |
| `GET /invoices/{id}` | Detail jedné faktury | Drilling |
| `GET /invoices/count` | `{count: N}` | Rychlý count bez fetchování dat |
| `GET /orders` | List objednávek | Top produkty, items breakdown |
| `GET /clients` | List klientů | Adresář, lookup po emailu |
| `GET /statistics/total` | Časové řady tržeb | **Preferuj pro dashboardy** (1 call vs tisíce) |
| `GET /vouchers/{code}` | Detail voucheru | Slevové kódy |

## Pasti a edge cases

### 1. `status` field NEEXISTUJE jako enum
Stav faktury se odvozuje z `paid` + `cancelled`:

| Klient řekne | Filtr |
|---|---|
| „zaplacené" | `paid == true && cancelled == false` |
| „nezaplacené" | `paid == false && cancelled == false` |
| „po splatnosti" | `paid == false && cancelled == false && payday_date < dnes` |
| „stornované" | `cancelled == true` |

### 2. `/invoices?status=` přijímá jen `issued`
Žádné `paid` / `cancelled` v query. Filtrování dělej **lokálně** na JSONu.

### 3. Datumový formát se liší per endpoint
- `/invoices`: `?created_on_from=YYYY-MM-DD HH:MM:SS` (URL-encoded mezera)
- `/statistics/total`: `?start=YYYY-MM-DD&end=YYYY-MM-DD` (jen datum)

### 4. `/orders` neumí datumové okno přes query
Filtruj `created` field lokálně po stažení batche. Alternativa: jít přes
spárovanou fakturu (`/invoices` → `id` → `/orders?invoice=<id>`).

### 5. Currency conversion
Pole faktury:
- `total` — v měně faktury (CZK/EUR/USD)
- `total_czk` — přepočteno na CZK přes `exchange_rate_czk`
- Pro analytiku **vždy používej `total_czk`** (jednotná měna).

### 6. Stornované faktury vs refundy
FAPI nemá samostatný refund event. Storno (`cancelled == true`) je
**jediná stopa po refundu**. Refundovaná částka = `total_czk` stornované
faktury.

## Co FAPI NEUMÍ (= nehledejte)

- MRR / churn analytika (musíš spočítat z `/orders` historie sám)
- Tagy / segmenty kontaktů (jen v SmartEmailing / GHL)
- Marketing attribution (UTM, kampaně)
- Refundy jako separate events
- Follow-up sekvence
- Stock / sklad

Pokud klient chce něco z tohoto, řekni mu otevřeně „FAPI tohle nedrží"
+ navrhuj jiný zdroj.

## Použití TypeScript connectoru (vibe-builder dashboard)

```typescript
import { loadFapiCredentials } from '@cliqsales/connectors/fapi/auth';
import {
  getStatistics,
  getUnpaidInvoices,
  getTopProducts,
  getRevenueForPeriod,
} from '@cliqsales/connectors/fapi/operations';

const creds = loadFapiCredentials();

// Recept 1: Tržby za měsíc
const revenue = await getRevenueForPeriod(creds, {
  from: '2026-05-01',
  to: '2026-05-31',
});
console.log(`Tržby v květnu: ${revenue.total} ${revenue.currency}`);

// Recept 2: Top produkty
const topProducts = await getTopProducts(creds, { topN: 5 });

// Recept 3: Po splatnosti
const overdue = await getOverdueInvoices(creds);
```

## Background refresh pattern

```typescript
// app/api/refresh/route.ts (Netlify Function)
import { neon } from '@neondatabase/serverless';
import { refreshFapiAll } from '@cliqsales/connectors/fapi/refresh';

const sql = neon(process.env.NETLIFY_DATABASE_URL!);

export async function POST() {
  const result = await refreshFapiAll({
    exec: async (query, params) => sql(query, params),
  });
  return Response.json(result);
}

// Pro Scheduled Function:
export const config = { schedule: '@every 15m' };
```

## Reference materials

Full detail v cs-skills/fapi/references/:
- `endpointy.md` — všechny endpointy + tvar JSONu
- `kucharka-dotazu.md` — 8 hotových receptů
- `filtrace-a-obdobi.md` — pagination, datumy, URL encoding
- `omezeni-a-pasti.md` — full seznam edge cases
- `prehled-api.md` — high-level overview
- `setup.md` — token management
