/**
 * Fio Banka API operations.
 *
 * Endpointy (vše GET, JSON format):
 *   - /periods/{TOKEN}/{from}/{to}/transactions.json  → transakce v období
 *   - /by-id/{TOKEN}/{year}/{number}/transactions.json → konkrétní výpis
 *   - /last/{TOKEN}/transactions.json → od posledního pull pointeru
 *   - /set-last-date/{TOKEN}/{date}/ → nastav pointer (POST)
 *   - /set-last-id/{TOKEN}/{id}/ → nastav pointer (POST)
 *
 * Fio specifika:
 *   - Response používá `columnN` pole se `{value, name, id}` strukturou
 *   - Tento connector je mapuje na human-readable field names
 *   - Rate limit: 30 sec mezi requesty per token
 */

import { FIO_BASE_URL, fioHeaders, sanitizeUrl, type FioCredentials } from './auth';

// ─── Types ─────────────────────────────────────────────────────────────────

/**
 * Mapování Fio column<N> → human-readable názvy.
 * Source: Fio API dokumentace + reálné JSON responses.
 */
export const FIO_COLUMN_MAP = {
  column22: 'transactionId',      // ID pohybu (unikátní)
  column0: 'date',                 // Datum (YYYY-MM-DD+timezone)
  column1: 'amount',               // Objem (positive = příjem, negative = výdej)
  column2: 'counterAccountNumber', // Číslo protiúčtu
  column3: 'counterBankCode',      // Kód banky protiúčtu
  column12: 'counterAccountName',  // Název protiúčtu
  column4: 'constantSymbol',       // KS
  column5: 'variableSymbol',       // VS
  column6: 'specificSymbol',       // SS
  column7: 'userIdentification',   // Uživatelská identifikace
  column8: 'transactionType',      // Typ (Bezhotovostní platba, Platba kartou, ...)
  column9: 'performedBy',          // Provedl
  column10: 'description',         // Upřesnění
  column14: 'currency',            // Měna (CZK)
  column16: 'recipientMessage',    // Zpráva pro příjemce
  column17: 'instructionId',       // ID pokynu
  column18: 'paymentSpec',         // Specifický symbol detail
  column25: 'comment',             // Komentář
  column26: 'bic',                 // BIC
  column27: 'payerReference',      // Reference plátce
} as const;

export interface FioTransaction {
  transactionId: number;
  date: string;                   // ISO YYYY-MM-DD (parsed z column0)
  amount: number;                 // CZK (positive = credit, negative = debit)
  currency: string;
  counterAccountNumber?: string;
  counterBankCode?: string;
  counterAccountName?: string;
  variableSymbol?: string;
  constantSymbol?: string;
  specificSymbol?: string;
  transactionType?: string;
  performedBy?: string;
  description?: string;
  instructionId?: string;
  recipientMessage?: string;
  userIdentification?: string;
  comment?: string;
  bic?: string;
  payerReference?: string;
  raw: Record<string, unknown>;   // Původní column-based response (pro debug)
}

export interface FioAccountInfo {
  accountId: string;
  bankId: string;
  currency: string;
  iban: string;
  bic: string;
  openingBalance: number;
  closingBalance: number;
  dateStart: string;
  dateEnd: string;
  idFrom?: number;
  idTo?: number;
  idLastDownload?: number;
}

export interface FioStatementResponse {
  info: FioAccountInfo;
  transactions: FioTransaction[];
}

// ─── Low-level fetch helper ──────────────────────────────────────────────

const DEFAULT_TIMEOUT_MS = 30_000;
const MAX_RETRIES = 3;
const RATE_LIMIT_WAIT_MS = 35_000; // 35s safety margin nad 30s Fio limit

async function fioFetch(url: string, token: string): Promise<any> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
      const res = await fetch(url, {
        headers: fioHeaders(),
        signal: controller.signal,
      });
      clearTimeout(timeout);

      if (res.status === 409) {
        // Rate limit — wait + retry (max 1x, jinak fail)
        if (attempt === 1) {
          await new Promise((r) => setTimeout(r, RATE_LIMIT_WAIT_MS));
          lastError = new Error('Fio rate limit (409) — waited 35s, retrying');
          continue;
        }
        throw new Error(
          'Fio rate limit (HTTP 409). Token byl použit příliš nedávno. ' +
            'Wait 30+ sekund mezi requesty per token.',
        );
      }

      if (res.status >= 500) {
        await new Promise((r) => setTimeout(r, 1_000 * 2 ** (attempt - 1)));
        lastError = new Error(`Fio HTTP ${res.status} (retry ${attempt}/${MAX_RETRIES})`);
        continue;
      }

      if (!res.ok) {
        const body = await res.text().catch(() => '');
        const safe = sanitizeUrl(url, token);
        throw new Error(`Fio HTTP ${res.status} for ${safe}: ${body.slice(0, 500)}`);
      }

      return await res.json();
    } catch (err) {
      lastError = err;
      if (attempt === MAX_RETRIES) throw err;
    }
  }
  throw lastError;
}

// ─── Mapping helpers ─────────────────────────────────────────────────────

function mapRawTransaction(raw: Record<string, any>): FioTransaction {
  const result: any = { raw };
  for (const [columnKey, fieldName] of Object.entries(FIO_COLUMN_MAP)) {
    const cell = raw[columnKey];
    if (cell && cell.value !== undefined && cell.value !== null) {
      result[fieldName] = cell.value;
    }
  }
  // Date normalization: "2026-05-27+0200" → "2026-05-27"
  if (typeof result.date === 'string' && result.date.length >= 10) {
    result.date = result.date.slice(0, 10);
  }
  return result as FioTransaction;
}

function mapStatement(raw: any): FioStatementResponse {
  const stmt = raw?.accountStatement;
  if (!stmt) {
    throw new Error('Fio response missing accountStatement field');
  }
  const transactions: FioTransaction[] = (stmt.transactionList?.transaction ?? []).map(mapRawTransaction);
  return {
    info: stmt.info as FioAccountInfo,
    transactions,
  };
}

// ─── Operations ──────────────────────────────────────────────────────────

/**
 * Stáhne transakce v zadaném datumovém období.
 *
 * @param dateRange.from "YYYY-MM-DD"
 * @param dateRange.to "YYYY-MM-DD"
 */
export async function getTransactionsByPeriod(
  creds: FioCredentials,
  dateRange: { from: string; to: string },
): Promise<FioStatementResponse> {
  const url = `${FIO_BASE_URL}/periods/${creds.token}/${dateRange.from}/${dateRange.to}/transactions.json`;
  const raw = await fioFetch(url, creds.token);
  return mapStatement(raw);
}

/**
 * Stáhne konkrétní výpis podle roku + čísla výpisu.
 */
export async function getStatementById(
  creds: FioCredentials,
  year: number,
  number: number,
): Promise<FioStatementResponse> {
  const url = `${FIO_BASE_URL}/by-id/${creds.token}/${year}/${number}/transactions.json`;
  const raw = await fioFetch(url, creds.token);
  return mapStatement(raw);
}

/**
 * Stáhne nové transakce od posledního pull pointeru.
 *
 * POZOR: tento endpoint posouvá pointer! Po stažení další volání vrátí
 * jen DALŠÍ nové transakce. Pro idempotentní refresh použij
 * getTransactionsByPeriod.
 */
export async function getNewTransactions(creds: FioCredentials): Promise<FioStatementResponse> {
  const url = `${FIO_BASE_URL}/last/${creds.token}/transactions.json`;
  const raw = await fioFetch(url, creds.token);
  return mapStatement(raw);
}

// ─── High-level recipes ──────────────────────────────────────────────────

/**
 * Recept 1: Aktuální zůstatek + cash flow za posledních N dní.
 */
export async function getBalanceAndCashflow(
  creds: FioCredentials,
  daysBack: number = 30,
): Promise<{
  currentBalance: number;
  currency: string;
  totalIncoming: number;
  totalOutgoing: number;
  netChange: number;
  transactionCount: number;
  periodFrom: string;
  periodTo: string;
}> {
  const today = new Date();
  const from = new Date(today.getTime() - daysBack * 24 * 60 * 60 * 1000);
  const fromStr = from.toISOString().slice(0, 10);
  const toStr = today.toISOString().slice(0, 10);

  const stmt = await getTransactionsByPeriod(creds, { from: fromStr, to: toStr });

  const totalIncoming = stmt.transactions
    .filter((t) => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0);
  const totalOutgoing = stmt.transactions
    .filter((t) => t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);

  return {
    currentBalance: stmt.info.closingBalance,
    currency: stmt.info.currency,
    totalIncoming,
    totalOutgoing,
    netChange: totalIncoming - totalOutgoing,
    transactionCount: stmt.transactions.length,
    periodFrom: fromStr,
    periodTo: toStr,
  };
}

/**
 * Recept 2: Příchozí platby s konkrétním variabilním symbolem
 * (= pro párování s vystavenými fakturami).
 */
export async function getIncomingByVariableSymbol(
  creds: FioCredentials,
  variableSymbol: string,
  dateRange: { from: string; to: string },
): Promise<FioTransaction[]> {
  const stmt = await getTransactionsByPeriod(creds, dateRange);
  return stmt.transactions.filter(
    (t) => t.amount > 0 && t.variableSymbol === variableSymbol,
  );
}

/**
 * Recept 3: Denní zůstatky (pro chart) — aproximace ze stmt
 */
export async function getDailyBalances(
  creds: FioCredentials,
  dateRange: { from: string; to: string },
): Promise<Array<{ date: string; balance: number; netChange: number }>> {
  const stmt = await getTransactionsByPeriod(creds, dateRange);
  let runningBalance = stmt.info.openingBalance;
  const byDate = new Map<string, { netChange: number }>();

  for (const t of stmt.transactions) {
    const existing = byDate.get(t.date) ?? { netChange: 0 };
    byDate.set(t.date, { netChange: existing.netChange + t.amount });
  }

  const result: Array<{ date: string; balance: number; netChange: number }> = [];
  const sortedDates = [...byDate.keys()].sort();
  for (const date of sortedDates) {
    const { netChange } = byDate.get(date)!;
    runningBalance += netChange;
    result.push({ date, balance: runningBalance, netChange });
  }
  return result;
}

/**
 * Recept 4: Top protiúčty podle objemu (= kdo mi nejvíc platí / komu nejvíc platím)
 */
export async function getTopCounterparties(
  creds: FioCredentials,
  dateRange: { from: string; to: string },
  options: { direction?: 'incoming' | 'outgoing'; topN?: number } = {},
): Promise<Array<{ name: string; account: string; totalAmount: number; count: number }>> {
  const stmt = await getTransactionsByPeriod(creds, dateRange);
  const direction = options.direction ?? 'incoming';
  const filter = direction === 'incoming' ? (t: FioTransaction) => t.amount > 0 : (t: FioTransaction) => t.amount < 0;

  const byCounterparty = new Map<string, { name: string; account: string; totalAmount: number; count: number }>();
  for (const t of stmt.transactions.filter(filter)) {
    const key = t.counterAccountNumber ?? 'unknown';
    const existing = byCounterparty.get(key) ?? {
      name: t.counterAccountName ?? 'Neznámý',
      account: key,
      totalAmount: 0,
      count: 0,
    };
    byCounterparty.set(key, {
      ...existing,
      totalAmount: existing.totalAmount + Math.abs(t.amount),
      count: existing.count + 1,
    });
  }
  return [...byCounterparty.values()]
    .sort((a, b) => b.totalAmount - a.totalAmount)
    .slice(0, options.topN ?? 10);
}
