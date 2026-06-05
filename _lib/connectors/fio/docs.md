# Fio Banka — quick reference pro CTO agenta

## API základ

- **Base URL:** `https://fioapi.fio.cz/v1/rest`
- **Auth:** **Token v URL PATH** (Fio specifika — NE header, NE query)
- **Format:** JSON (taky XML, MT940, OFX, GPC, CSV, HTML, PDF)
- **Rate limit:** ⚠️ **30 sekund mezi requesty per token** (jinak HTTP 409)
- **Read-only:** Fio API jen čte, neumí vystavit / měnit
- **Token získá klient:** Internetbanka → Nastavení → Nastavení API → Vytvořit token

## Klíčové endpointy

| Endpoint | Co vrací | Použití |
|---|---|---|
| `GET /periods/{TOKEN}/{from}/{to}/transactions.json` | Transakce v období | **Hlavní pro dashboard** (idempotent) |
| `GET /by-id/{TOKEN}/{year}/{number}/transactions.json` | Konkrétní výpis | Per-statement drilling |
| `GET /last/{TOKEN}/transactions.json` | Od posledního pull pointeru | POZOR: posouvá pointer! |
| `POST /set-last-date/{TOKEN}/{date}/` | Reset pointer na datum | Pokud potřebuješ re-fetch |
| `POST /set-last-id/{TOKEN}/{id}/` | Reset pointer na ID | Pokud potřebuješ re-fetch |

## Response shape (specifický)

Fio vrací transakce jako pole s `column<N>` keys. Tento connector je
automaticky mapuje na human-readable názvy.

```json
{
  "accountStatement": {
    "info": {
      "accountId": "2400123456",
      "bankId": "2010",
      "currency": "CZK",
      "iban": "CZ12...",
      "bic": "FIOBCZPPXXX",
      "openingBalance": 12345.67,
      "closingBalance": 98765.43,
      "dateStart": "2026-05-01+0200",
      "dateEnd": "2026-05-27+0200"
    },
    "transactionList": {
      "transaction": [
        {
          "column22": { "value": 123456789, "name": "ID pohybu" },
          "column0":  { "value": "2026-05-27+0200", "name": "Datum" },
          "column1":  { "value": 1500.00, "name": "Objem" },
          "column16": { "value": "Faktura 202610001", "name": "Zpráva pro příjemce" },
          ...
        }
      ]
    }
  }
}
```

## Column mapping (= co connector dělá automaticky)

| Fio column | Human-readable | Typ | Význam |
|---|---|---|---|
| column22 | `transactionId` | int | Unikátní ID pohybu |
| column0 | `date` | string | Datum (YYYY-MM-DD) |
| column1 | `amount` | number | Částka (+ příjem / − výdej) |
| column2 | `counterAccountNumber` | string | Číslo protiúčtu |
| column3 | `counterBankCode` | string | Kód banky protiúčtu |
| column12 | `counterAccountName` | string | Název protiúčtu |
| column14 | `currency` | string | CZK / EUR |
| column16 | `recipientMessage` | string | Zpráva pro příjemce |
| column5 | `variableSymbol` | string | VS (pro párování s fakturami!) |
| column8 | `transactionType` | string | "Bezhotovostní platba", … |

Plný mapping v `operations.ts` → `FIO_COLUMN_MAP`.

## Pasti a edge cases

### 1. ⚠️ Rate limit 30 sekund per token
Pokud Refresh button v dashboardu spustí Fio + jiný worker zároveň → HTTP 409.

**Řešení:**
- Cron interval ≥ 5 min
- Client-side cooldown na Refresh tlačítko (30s lockout)
- Pokud klient má víc tokenů (víc účtů), refresh sequenčně se sleep(30s)

### 2. Token v URL = security risk v logs
Connector ho **sanitizuje** v error messages přes `sanitizeUrl()`. Nikdy
nelogovat raw URL.

### 3. `/last` endpoint POSOUVÁ pointer
Po jednom volání další volání vrátí jen NOVÉ transakce od minula.
Pro dashboard refresh **použij `/periods`** (idempotent), ne `/last`.

### 4. Datum má timezone suffix
Fio vrací `"2026-05-27+0200"` — connector automaticky striktuje na `"2026-05-27"`.

### 5. Storná v Fio
Fio nemá samostatný refund event. Storno se projeví jako:
- Originální transakce zůstává v statementu
- Nová transakce s opačným amount (= výplata zpět)

Pro klient může vypadat jako duplicitní záznam — UI by mělo páry zobrazit
jako "stornováno".

### 6. Měna
Connector ukládá `amount` v originální měně. Pokud má klient účet v EUR
+ CZK, dotazy musí filtrovat per `currency`.

## Co Fio API NEUMÍ

- ❌ Vystavit / odeslat platbu (read-only)
- ❌ Detail jednoho transaction objektu (jen list)
- ❌ Filter v query (status, amount range, counterparty) — vždy stáhneš
  všechno v období, filtruj lokálně
- ❌ Pagination (vrací vše najednou — pro 1000+ transakcí může být slow)
- ❌ Webhooks (musíš poll-ovat)
- ❌ Multi-account v jednom tokenu (= 1 token = 1 účet)

## Použití TypeScript connectoru

```typescript
import { loadFioCredentials } from '@cliqsales/connectors/fio/auth';
import {
  getTransactionsByPeriod,
  getBalanceAndCashflow,
  getIncomingByVariableSymbol,
} from '@cliqsales/connectors/fio/operations';

const creds = loadFioCredentials();

// Stáhni posledních 30 dní
const stmt = await getTransactionsByPeriod(creds, {
  from: '2026-04-27',
  to: '2026-05-27',
});
console.log(`Zůstatek: ${stmt.info.closingBalance} ${stmt.info.currency}`);
console.log(`Transakcí: ${stmt.transactions.length}`);

// Recept: cashflow summary
const summary = await getBalanceAndCashflow(creds, 30);
console.log(`Příjmy: ${summary.totalIncoming}, výdaje: ${summary.totalOutgoing}`);

// Cross-reference: našla se platba pro fakturu VS=202610042?
const payments = await getIncomingByVariableSymbol(
  creds,
  '202610042',
  { from: '2026-04-01', to: '2026-05-31' },
);
```

## Cross-reference s FAPI / Fakturoid

Hlavní use case pro Fio connector v dashboardu = **párovat příchozí platby
s vystavenými fakturami** (pro view `v_fio_incoming_with_vs`).

SQL pattern (po refresh obou connectorů):

```sql
-- Faktury, které mají match v bank statementu (zaplaceno)
SELECT
  i.number AS invoice_number,
  i.total_czk AS invoiced,
  bt.amount AS paid_amount,
  bt.date AS paid_on,
  i.total_czk - bt.amount AS difference
FROM fapi_invoices i
LEFT JOIN fio_transactions bt
  ON bt.variable_symbol = i.variable_symbol
  AND bt.amount > 0
WHERE i.create_date >= CURRENT_DATE - INTERVAL '30 days';

-- Faktury bez match v bank statementu (nezaplaceno fyzicky)
SELECT i.*
FROM fapi_invoices i
WHERE i.create_date >= CURRENT_DATE - INTERVAL '30 days'
  AND NOT EXISTS (
    SELECT 1 FROM fio_transactions bt
    WHERE bt.variable_symbol = i.variable_symbol
      AND bt.amount > 0
  );
```

## Reference

- Oficiální dokumentace Fio: https://www.fio.cz/bank-services/internetbanking-api
- (Volitelně) GitHub PHP klient: https://github.com/h4kuna/fio
- (Volitelně) Python klient: https://github.com/honzajavorek/fiobank
