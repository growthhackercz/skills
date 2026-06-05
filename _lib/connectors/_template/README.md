# Connector template — krok po kroku pro CTO

Tento template je **kostra** pro vytvoření nového connectoru, když klient
požádá o integraci na nějakou službu, pro kterou ještě nemáme výchozí
connector (např. Stormware Pohoda, Shoptet, vlastní firemní API).

CTO agent (GPT-5.5) má **přístup k webu a celému disku** — dokáže si:
1. Načíst API dokumentaci klientovy služby přes WebFetch
2. Extrahovat auth model, endpoints, formáty
3. Adaptovat tento template a vytvořit funkční connector
4. Otestovat ad hoc voláním
5. Uložit pro budoucí klienty

## Kdy použít

- Klient ti dal URL na API dokumentaci své obscure služby
- Chce dashboard nad ní
- Pro tohoto providera ještě neexistuje connector v `_lib/connectors/`

## Kdy NEpoužít

- Pro top providery (FAPI, Fakturoid, Fio, GA4, Meta Ads, Google Ads,
  GHL) existují **výchozí connectory** — ty použij přímo, neduplikuj
- Pro úplně custom data (CSV upload, vlastní webhook) použij generic
  pattern, ne tenhle template

## Postup (8 kroků, ~10-15 min)

### Krok 1: Získej URL API dokumentace od klienta

```
Klient: "Mám Pohoda eShop"
CTO: "Pošli mi URL na jejich API dokumentaci."
Klient: "https://www.stormware.cz/api/eshop/"
```

### Krok 2: Načti dokumentaci přes WebFetch

```
WebFetch(
  url="https://www.stormware.cz/api/eshop/",
  prompt="Extract:
    1. Auth method (Basic / Bearer / OAuth2 / API key in header / query param)
    2. Base URL format
    3. Rate limits (calls per minute/hour)
    4. Pagination pattern (?page=, ?offset=, cursor-based)
    5. Top 5 endpoints for typical sales dashboard (invoices, orders, customers, products, payments)
    6. JSON response shape for each endpoint (klíčová pole)
    7. Date filter syntax (?from=, ?since=, etc.)
  "
)
```

Z výstupu si vytvoř **mental model** API před tím, než píšeš kód.

### Krok 3: Zkopíruj template do nové složky

```bash
cp -r /home/node/.openclaw/cs-skills/_lib/connectors/_template \
      /home/node/.openclaw/cs-skills/_lib/connectors/<provider-slug>
```

`<provider-slug>` = lowercase, hyphen-separated (`pohoda-eshop`, `shoptet`,
`mailerlite`).

### Krok 4: Vyplň `auth.ts`

Podle auth modelu z Kroku 2:

**Basic auth:**
```typescript
export function authHeader(creds): string {
  const enc = Buffer.from(`${creds.user}:${creds.token}`).toString('base64');
  return `Basic ${enc}`;
}
```

**Bearer token:**
```typescript
export function authHeader(creds): string {
  return `Bearer ${creds.token}`;
}
```

**API key v header:**
```typescript
export function headers(creds): Record<string, string> {
  return { 'X-API-Key': creds.apiKey };
}
```

**OAuth2 (komplikovanější):**
```typescript
// Vyžaduje refresh token flow — pravděpodobně potřebuješ samostatný
// OAuth dance při onboardingu. Pokud klient nemá pre-existing OAuth
// access token, doporuč mu jednorázový login flow.
```

### Krok 5: Vyplň `operations.ts`

Pro každý top endpoint z Kroku 2 napiš funkci:

```typescript
export async function getInvoices(creds: Credentials, opts: {...}): Promise<Invoice[]> {
  const url = new URL(BASE_URL + '/invoices');
  // ... add query params podle dokumentace
  const res = await fetch(url, { headers: headers(creds) });
  if (!res.ok) throw new Error(`<Provider> HTTP ${res.status}`);
  return res.json();
}
```

**Pravidla:**
- Vždy retry s exponential backoff (kopíruj pattern z `fapi/operations.ts`)
- Vždy timeout (~30s)
- TypeScript types odvoď z reálných response (ne z dokumentace, ta lže)

### Krok 6: Vyplň `schema.sql`

Cache tabulky podle JSON shapes z Kroku 2:

```sql
CREATE TABLE IF NOT EXISTS <provider>_invoices (
  id BIGINT PRIMARY KEY,
  -- ... pole z JSONu
  raw JSONB NOT NULL,        -- vždy ulož raw JSON pro debugging
  cached_at TIMESTAMPTZ DEFAULT NOW()
);

-- Plus indexes pro typické queries
CREATE INDEX idx_<provider>_invoices_created ON <provider>_invoices(created_at);
```

### Krok 7: Vyplň `refresh.ts`

Background sync worker. Kopíruj pattern z `fapi/refresh.ts`:

```typescript
export async function refresh<Provider>All(sql: SqlExecutor) {
  const creds = load<Provider>Credentials();
  const invoices = await getInvoices(creds, { /* recent days */ });
  for (const inv of invoices) {
    await sql.exec(`INSERT INTO <provider>_invoices ... ON CONFLICT DO UPDATE ...`, [...]);
  }
}
```

### Krok 8: Otestuj ad hoc

```bash
# V CTO session:
node -e "
  process.env.<PROVIDER>_USER='test@klient.cz';
  process.env.<PROVIDER>_TOKEN='xxx';
  const { getInvoices } = require('./operations');
  const { load<Provider>Credentials } = require('./auth');
  getInvoices(load<Provider>Credentials()).then(r => console.log(JSON.stringify(r[0], null, 2)));
"
```

Pokud vrátí strukturovaná data → connector funguje.

## Co nikdy nedělej

- **NEPUTUJ tokeny do gitu** — vždy v env vars
- **NEPOUŽÍVEJ klientovy produkční tokeny pro debug** — vyžádej si test token
- **NEHARDCODE base URL** — některé služby mají region-specific endpointy
- **NEPRODUKUJ kód, který volá API z browseru** — vždy server-side (CORS, security)
- **NEPRETIPUJ rate limits** — vždy přidej retry s exponential backoff

## Co po vytvoření connectoru

1. **Otestuj end-to-end** s vibe-builder dashboard projektem
2. **Pokud funguje** → vibe-builder ho může používat pro další klienty
3. **Pokud nefunguje** → debugnij, oprav, retry
4. **Aktualizuj `docs.md`** s edge cases, které jsi narazil

## Reálný příklad: Pohoda eShop connector (hypotetický)

```bash
# Krok 1-2: WebFetch docs.pohoda.cz/api → OAuth2, base https://api.pohoda.cz/v2
# Krok 3:
cp -r _template pohoda-eshop
cd pohoda-eshop

# Krok 4-7: vyplň 5 souborů (viz výše)

# Krok 8: test
node -e "..."
# → vrací list faktur ✓

# Done. Klient může nyní vibe-builderem požádat o Pohoda dashboard.
```

## Reference

- `_lib/connectors/fapi/` — vzorový hotový connector (Basic auth + REST)
- `_lib/connectors/README.md` — overview všech connectorů
- `cs-skills/fapi/references/endpointy.md` — příklad detailní API mapy

## Limity templatu

Template pokrývá:
- ✅ REST APIs s Basic / Bearer / API key auth
- ✅ JSON response format
- ✅ Standard pagination patterns

Nepokrývá:
- ❌ GraphQL APIs (musíš adaptovat sám)
- ❌ gRPC / WebSocket
- ❌ SOAP / XML (legacy)
- ❌ OAuth2 full flow (klient musí předat pre-existing access token)
