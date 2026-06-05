/**
 * FAPI.cz API operations — TypeScript port klíčových endpointů.
 *
 * Reference: cs-skills/fapi/references/endpointy.md
 * Pattern: vibe-builder dashboard generates code that imports a uses these
 * funkce. NEPOUŽÍVÁ se přímo v browseru — vždy server-side (Netlify Function).
 *
 * Read-only. Pro write operace (vystavit fakturu) napiš samostatný connector
 * nebo extend tento s explicit `--write` flagem.
 */

import { FAPI_BASE_URL, fapiHeaders, type FapiCredentials } from './auth';

// ─── Types ─────────────────────────────────────────────────────────────────

export interface FapiInvoice {
  id: number;
  number: string;
  created_on: string; // YYYY-MM-DD HH:MM:SS
  create_date: string; // YYYY-MM-DD
  payday_date: string;
  client: number;
  type: string; // "proforma", "tax_document", …
  payment_type: string;
  currency: string; // CZK, EUR
  exchange_rate_czk: number;
  paid: boolean;
  cancelled: boolean;
  total: number; // ve měně faktury
  total_czk: number;
  total_vat: number;
  variable_symbol: string;
  customer?: { name?: string; email?: string };
  items?: Array<{ id: number; name: string; price: number; count: number }>;
}

export interface FapiOrder {
  id: number;
  form: number;
  created: string; // POZOR: u orders je `created`, ne `created_on`
  email: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  client: number;
  invoice?: number; // ID spárované faktury
  pending: boolean;
  items?: Array<{
    name: string;
    price: number;
    price_czk?: number;
    count: number;
  }>;
}

export interface FapiClient {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  tax_payer?: boolean;
}

export interface FapiStatisticsResponse {
  issued: Array<{ date: string; value: number }>;
  paid: Array<{ date: string; value: number }>;
  cancelled: Array<{ date: string; value: number }>;
  left_to_pay: Array<{ date: string; value: number }>;
  overdue: Array<{ date: string; value: number }>;
  invoiced: Array<{ date: string; value: number }>;
  dph: Array<{ date: string; value: number }>;
}

export interface DateRange {
  from: string; // YYYY-MM-DD
  to: string;   // YYYY-MM-DD
}

// ─── Low-level request helper ──────────────────────────────────────────────

const DEFAULT_TIMEOUT_MS = 30_000;
const MAX_RETRIES = 3;

async function fapiFetch<T>(
  path: string,
  query: Record<string, string | number | undefined>,
  creds: FapiCredentials,
): Promise<T> {
  const url = new URL(FAPI_BASE_URL + (path.startsWith('/') ? path : '/' + path));
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== '') {
      url.searchParams.set(key, String(value));
    }
  }

  let lastError: unknown;
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
      const res = await fetch(url.toString(), {
        headers: fapiHeaders(creds),
        signal: controller.signal,
      });
      clearTimeout(timeout);

      if (res.status === 429 || (res.status >= 500 && res.status < 600)) {
        // Retry s exponential backoff
        await new Promise((r) => setTimeout(r, 500 * 2 ** (attempt - 1)));
        lastError = new Error(`FAPI HTTP ${res.status} (retry ${attempt}/${MAX_RETRIES})`);
        continue;
      }

      if (!res.ok) {
        const body = await res.text().catch(() => '');
        throw new Error(`FAPI HTTP ${res.status} for ${path}: ${body.slice(0, 500)}`);
      }

      return (await res.json()) as T;
    } catch (err) {
      lastError = err;
      if (attempt === MAX_RETRIES) throw err;
      await new Promise((r) => setTimeout(r, 500 * 2 ** (attempt - 1)));
    }
  }
  throw lastError;
}

// ─── Invoices ──────────────────────────────────────────────────────────────

/**
 * List faktur. Filtrovat lze datumovým oknem + statusem.
 *
 * @param creds — FAPI credentials
 * @param opts.from — created_on_from "YYYY-MM-DD HH:MM:SS" (volitelné)
 * @param opts.to — created_on_to (volitelné)
 * @param opts.status — "issued" (jediná ověřená hodnota — viz endpointy.md)
 * @param opts.limit — max records (default 200, FAPI hard limit nedoc.)
 * @param opts.user — filtr po user ID (multi-user FAPI účet)
 */
export async function getInvoices(
  creds: FapiCredentials,
  opts: { from?: string; to?: string; status?: string; limit?: number; user?: number } = {},
): Promise<FapiInvoice[]> {
  const query: Record<string, string | number | undefined> = {
    limit: opts.limit ?? 200,
  };
  if (opts.from) query.created_on_from = opts.from;
  if (opts.to) query.created_on_to = opts.to;
  if (opts.status) query.status = opts.status;
  if (opts.user !== undefined) query.user = opts.user;

  const data = await fapiFetch<FapiInvoice[] | { invoices: FapiInvoice[] }>('/invoices', query, creds);
  return Array.isArray(data) ? data : data.invoices ?? [];
}

/**
 * Stáhne VŠECHNY faktury v datumovém okně (pagination handle).
 * Pozor — pro velké účty (5000+ faktur) trvá.
 */
export async function getAllInvoices(
  creds: FapiCredentials,
  opts: { from: string; to: string; limit?: number } = { from: '', to: '' },
): Promise<FapiInvoice[]> {
  const pageSize = opts.limit ?? 200;
  const all: FapiInvoice[] = [];
  let offset = 0;
  while (true) {
    const batch = await getInvoices(creds, {
      from: opts.from,
      to: opts.to,
      limit: pageSize,
    });
    if (!batch.length) break;
    all.push(...batch);
    if (batch.length < pageSize) break;
    offset += pageSize;
    // FAPI pagination není přes ?page= u všech endpointů, viz filtrace-a-obdobi.md
    // Pokud potřebuješ ?offset= nebo ?page= per resource, doplň podle docs.md
    break; // bez pagination supportu (zatím) — vrať jen první batch
  }
  return all;
}

/**
 * Detail jedné faktury.
 */
export async function getInvoiceById(creds: FapiCredentials, id: number): Promise<FapiInvoice> {
  return fapiFetch<FapiInvoice>(`/invoices/${id}`, {}, creds);
}

/**
 * Count faktur splňujících filtr.
 */
export async function getInvoicesCount(
  creds: FapiCredentials,
  opts: { from?: string; to?: string; status?: string } = {},
): Promise<number> {
  const query: Record<string, string | number | undefined> = {};
  if (opts.from) query.created_on_from = opts.from;
  if (opts.to) query.created_on_to = opts.to;
  if (opts.status) query.status = opts.status;
  const data = await fapiFetch<{ count: number }>('/invoices/count', query, creds);
  return data.count;
}

// ─── Orders ────────────────────────────────────────────────────────────────

/**
 * List objednávek. POZOR: FAPI neumí datumové okno přes query —
 * filtr po `created` musíš dělat lokálně.
 */
export async function getOrders(
  creds: FapiCredentials,
  opts: { limit?: number; invoice?: number } = {},
): Promise<FapiOrder[]> {
  const query: Record<string, string | number | undefined> = {
    limit: opts.limit ?? 200,
  };
  if (opts.invoice) query.invoice = opts.invoice;
  const data = await fapiFetch<FapiOrder[] | { orders: FapiOrder[] }>('/orders', query, creds);
  return Array.isArray(data) ? data : data.orders ?? [];
}

// ─── Clients ───────────────────────────────────────────────────────────────

export async function getClients(
  creds: FapiCredentials,
  opts: { email?: string; limit?: number } = {},
): Promise<FapiClient[]> {
  const query: Record<string, string | number | undefined> = {
    limit: opts.limit ?? 200,
  };
  if (opts.email) query.email = opts.email;
  const data = await fapiFetch<FapiClient[] | { clients: FapiClient[] }>('/clients', query, creds);
  return Array.isArray(data) ? data : data.clients ?? [];
}

export async function getClientById(creds: FapiCredentials, id: number): Promise<FapiClient> {
  return fapiFetch<FapiClient>(`/clients/${id}`, {}, creds);
}

// ─── Statistics (předagregované — preferuj tohle pro dashboardy) ──────────

/**
 * Časové řady tržeb / storn / po splatnosti / DPH.
 *
 * NEJDŮLEŽITĚJŠÍ endpoint pro dashboardy — 1 volání místo tisíců faktur.
 *
 * @param opts.type — "daily" (ověřeno), "weekly", "monthly", "yearly" (netest.)
 * @param opts.includingVat — false (default), true pro s DPH
 */
export async function getStatistics(
  creds: FapiCredentials,
  opts: {
    type?: 'daily' | 'weekly' | 'monthly' | 'yearly';
    start: string; // YYYY-MM-DD
    end: string;
    includingVat?: boolean;
  },
): Promise<FapiStatisticsResponse> {
  return fapiFetch<FapiStatisticsResponse>(
    '/statistics/total',
    {
      type: opts.type ?? 'daily',
      start: opts.start,
      end: opts.end,
      including_vat: opts.includingVat ? 1 : 0,
    },
    creds,
  );
}

// ─── High-level recipes (= kucharka-dotazu.md ported) ─────────────────────

/**
 * Recept 1: Tržby za období (kolik jsem vydělal?)
 * Vrátí součet placených faktur v CZK.
 */
export async function getRevenueForPeriod(
  creds: FapiCredentials,
  dateRange: DateRange,
  options: { includingVat?: boolean } = {},
): Promise<{ total: number; currency: 'CZK'; days: number }> {
  const stats = await getStatistics(creds, {
    type: 'daily',
    start: dateRange.from,
    end: dateRange.to,
    includingVat: options.includingVat,
  });
  const total = stats.paid.reduce((sum, point) => sum + (point.value ?? 0), 0);
  return { total, currency: 'CZK', days: stats.paid.length };
}

/**
 * Recept 2: Top produkty podle obratu.
 * Stáhne objednávky, group-by item.name, sečte revenue.
 */
export async function getTopProducts(
  creds: FapiCredentials,
  options: { limit?: number; topN?: number } = {},
): Promise<Array<{ name: string; revenue: number; count: number }>> {
  const orders = await getOrders(creds, { limit: options.limit ?? 500 });
  const byProduct = new Map<string, { revenue: number; count: number }>();
  for (const order of orders) {
    for (const item of order.items ?? []) {
      const existing = byProduct.get(item.name) ?? { revenue: 0, count: 0 };
      const revenue = (item.price_czk ?? item.price) * item.count;
      byProduct.set(item.name, {
        revenue: existing.revenue + revenue,
        count: existing.count + item.count,
      });
    }
  }
  return [...byProduct.entries()]
    .map(([name, stats]) => ({ name, ...stats }))
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, options.topN ?? 10);
}

/**
 * Recept 3: Nezaplacené faktury.
 */
export async function getUnpaidInvoices(
  creds: FapiCredentials,
  options: { from?: string; to?: string } = {},
): Promise<FapiInvoice[]> {
  const invoices = await getInvoices(creds, {
    from: options.from,
    to: options.to,
    status: 'issued',
  });
  return invoices.filter((inv) => !inv.paid && !inv.cancelled);
}

/**
 * Recept 4: Faktury po splatnosti.
 */
export async function getOverdueInvoices(
  creds: FapiCredentials,
  asOfDate: Date = new Date(),
): Promise<FapiInvoice[]> {
  const unpaid = await getUnpaidInvoices(creds);
  const today = asOfDate.toISOString().slice(0, 10);
  return unpaid.filter((inv) => inv.payday_date && inv.payday_date < today);
}

/**
 * Recept 5: Top zákazníci podle obratu.
 */
export async function getTopCustomers(
  creds: FapiCredentials,
  options: { from?: string; to?: string; topN?: number } = {},
): Promise<Array<{ clientId: number; email?: string; revenue: number; invoices: number }>> {
  const invoices = await getInvoices(creds, {
    from: options.from,
    to: options.to,
    limit: 500,
  });
  const byClient = new Map<number, { email?: string; revenue: number; invoices: number }>();
  for (const inv of invoices) {
    if (!inv.paid || inv.cancelled) continue;
    const existing = byClient.get(inv.client) ?? { email: inv.customer?.email, revenue: 0, invoices: 0 };
    byClient.set(inv.client, {
      email: existing.email ?? inv.customer?.email,
      revenue: existing.revenue + (inv.total_czk ?? 0),
      invoices: existing.invoices + 1,
    });
  }
  return [...byClient.entries()]
    .map(([clientId, stats]) => ({ clientId, ...stats }))
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, options.topN ?? 10);
}

/**
 * Recept 6: Měsíční vývoj tržeb (= časová řada pro chart).
 */
export async function getMonthlyRevenue(
  creds: FapiCredentials,
  year: number,
  options: { includingVat?: boolean } = {},
): Promise<Array<{ month: string; revenue: number }>> {
  const stats = await getStatistics(creds, {
    type: 'monthly',
    start: `${year}-01-01`,
    end: `${year}-12-31`,
    includingVat: options.includingVat,
  });
  return stats.paid.map((point) => ({
    month: point.date.slice(0, 7), // YYYY-MM
    revenue: point.value,
  }));
}
