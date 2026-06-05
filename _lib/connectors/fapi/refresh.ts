/**
 * FAPI background refresh worker.
 *
 * Spouští se:
 *   - Cron přes Netlify Scheduled Function (každých 15-60 min)
 *   - Manual on-demand (klient klikne "Refresh" v dashboardu)
 *
 * Strategie:
 *   - Stáhne data z FAPI přes operations.ts
 *   - Upsertuje do Postgres cache tabulek (schema.sql)
 *   - Zaeviduje úspěch / chybu v fapi_refresh_log
 *
 * NEVOLÁ z browseru — server-side only (Netlify Function).
 *
 * Pre-requisites:
 *   - Postgres connection (via @netlify/neon nebo postgres driver)
 *   - env vars: FAPI_USER, FAPI_TOKEN, NETLIFY_DATABASE_URL
 *
 * Pattern použití v Netlify Scheduled Function:
 *
 * ```typescript
 * // netlify/functions/refresh-fapi.ts (nebo app/api/refresh/fapi/route.ts)
 * import { refreshFapiAll } from '@cliqsales/connectors/fapi/refresh';
 * export default async () => {
 *   const result = await refreshFapiAll();
 *   return new Response(JSON.stringify(result), { status: 200 });
 * };
 * export const config = { schedule: '@every 15m' };
 * ```
 */

import { loadFapiCredentials } from './auth';
import {
  getInvoices,
  getOrders,
  getClients,
  getStatistics,
  type FapiInvoice,
  type FapiOrder,
  type FapiClient,
} from './operations';

/**
 * Abstrakce Postgres clienta — vibe-builder projekt si dodá konkrétní
 * implementaci (např. @neondatabase/serverless). Tady ho přijímáme jako
 * dependency injection, aby connector nebyl vázaný na jeden driver.
 */
export interface SqlExecutor {
  /**
   * Provede SQL query s parameterizovanými hodnotami.
   * Vrátí list rows (může být prázdné).
   */
  exec(sql: string, params?: unknown[]): Promise<unknown[]>;
}

// ─── Refresh logiky per resource ──────────────────────────────────────────

export interface RefreshSummary {
  resource: string;
  ok: boolean;
  recordCount: number;
  durationMs: number;
  error?: string;
}

/**
 * Refresh invoices — stáhne posledních X dní a upsertuje.
 *
 * @param sql — Postgres executor
 * @param options.daysBack — kolik dní zpět načíst (default 90)
 */
export async function refreshFapiInvoices(
  sql: SqlExecutor,
  options: { daysBack?: number } = {},
): Promise<RefreshSummary> {
  const startMs = Date.now();
  try {
    const creds = loadFapiCredentials();
    const daysBack = options.daysBack ?? 90;
    const today = new Date();
    const from = new Date(today.getTime() - daysBack * 24 * 60 * 60 * 1000);
    const fromStr = from.toISOString().slice(0, 10) + ' 00:00:00';
    const toStr = today.toISOString().slice(0, 10) + ' 23:59:59';

    const invoices = await getInvoices(creds, { from: fromStr, to: toStr, limit: 500 });

    // Upsert přes batch
    for (const inv of invoices) {
      await sql.exec(
        `INSERT INTO fapi_invoices (
          id, number, created_on, create_date, payday_date, client_id,
          type, payment_type, currency, exchange_rate_czk, paid, cancelled,
          total, total_czk, total_vat, variable_symbol, raw, cached_at
        ) VALUES (
          $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, NOW()
        )
        ON CONFLICT (id) DO UPDATE SET
          number = EXCLUDED.number,
          paid = EXCLUDED.paid,
          cancelled = EXCLUDED.cancelled,
          total = EXCLUDED.total,
          total_czk = EXCLUDED.total_czk,
          raw = EXCLUDED.raw,
          cached_at = NOW()
        `,
        [
          inv.id,
          inv.number,
          inv.created_on,
          inv.create_date,
          inv.payday_date,
          inv.client,
          inv.type,
          inv.payment_type,
          inv.currency,
          inv.exchange_rate_czk,
          inv.paid,
          inv.cancelled,
          inv.total,
          inv.total_czk,
          inv.total_vat,
          inv.variable_symbol,
          JSON.stringify(inv),
        ],
      );
    }

    await logRefresh(sql, 'invoices', invoices.length);
    return {
      resource: 'invoices',
      ok: true,
      recordCount: invoices.length,
      durationMs: Date.now() - startMs,
    };
  } catch (err) {
    const error = err instanceof Error ? err.message : String(err);
    await logRefreshError(sql, 'invoices', error);
    return {
      resource: 'invoices',
      ok: false,
      recordCount: 0,
      durationMs: Date.now() - startMs,
      error,
    };
  }
}

export async function refreshFapiOrders(
  sql: SqlExecutor,
  options: { limit?: number } = {},
): Promise<RefreshSummary> {
  const startMs = Date.now();
  try {
    const creds = loadFapiCredentials();
    const orders = await getOrders(creds, { limit: options.limit ?? 500 });

    for (const order of orders) {
      await sql.exec(
        `INSERT INTO fapi_orders (
          id, form_id, created, client_id, invoice_id, email,
          first_name, last_name, company, pending, raw, cached_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
        ON CONFLICT (id) DO UPDATE SET
          invoice_id = EXCLUDED.invoice_id,
          pending = EXCLUDED.pending,
          raw = EXCLUDED.raw,
          cached_at = NOW()
        `,
        [
          order.id,
          order.form,
          order.created,
          order.client,
          order.invoice ?? null,
          order.email,
          order.first_name ?? null,
          order.last_name ?? null,
          order.company ?? null,
          order.pending,
          JSON.stringify(order),
        ],
      );

      // Items — smaž staré, vlož nové
      await sql.exec(`DELETE FROM fapi_order_items WHERE order_id = $1`, [order.id]);
      const items = order.items ?? [];
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        await sql.exec(
          `INSERT INTO fapi_order_items (order_id, position, name, price, price_czk, count, raw)
           VALUES ($1, $2, $3, $4, $5, $6, $7)`,
          [order.id, i, item.name, item.price, item.price_czk ?? null, item.count, JSON.stringify(item)],
        );
      }
    }

    await logRefresh(sql, 'orders', orders.length);
    return {
      resource: 'orders',
      ok: true,
      recordCount: orders.length,
      durationMs: Date.now() - startMs,
    };
  } catch (err) {
    const error = err instanceof Error ? err.message : String(err);
    await logRefreshError(sql, 'orders', error);
    return { resource: 'orders', ok: false, recordCount: 0, durationMs: Date.now() - startMs, error };
  }
}

export async function refreshFapiClients(sql: SqlExecutor): Promise<RefreshSummary> {
  const startMs = Date.now();
  try {
    const creds = loadFapiCredentials();
    const clients = await getClients(creds, { limit: 500 });

    for (const client of clients) {
      await sql.exec(
        `INSERT INTO fapi_clients (id, email, first_name, last_name, company, tax_payer, raw, cached_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
         ON CONFLICT (id) DO UPDATE SET
           email = EXCLUDED.email, first_name = EXCLUDED.first_name,
           last_name = EXCLUDED.last_name, company = EXCLUDED.company,
           tax_payer = EXCLUDED.tax_payer, raw = EXCLUDED.raw, cached_at = NOW()`,
        [
          client.id,
          client.email,
          client.first_name ?? null,
          client.last_name ?? null,
          client.company ?? null,
          client.tax_payer ?? null,
          JSON.stringify(client),
        ],
      );
    }

    await logRefresh(sql, 'clients', clients.length);
    return { resource: 'clients', ok: true, recordCount: clients.length, durationMs: Date.now() - startMs };
  } catch (err) {
    const error = err instanceof Error ? err.message : String(err);
    await logRefreshError(sql, 'clients', error);
    return { resource: 'clients', ok: false, recordCount: 0, durationMs: Date.now() - startMs, error };
  }
}

/**
 * Refresh všeho najednou — pro daily/hourly cron nebo manual refresh tlačítko.
 */
export async function refreshFapiAll(sql: SqlExecutor): Promise<{
  ok: boolean;
  results: RefreshSummary[];
  durationMs: number;
}> {
  const start = Date.now();
  const results = await Promise.all([
    refreshFapiInvoices(sql),
    refreshFapiOrders(sql),
    refreshFapiClients(sql),
  ]);
  return {
    ok: results.every((r) => r.ok),
    results,
    durationMs: Date.now() - start,
  };
}

// ─── Logging helpers ──────────────────────────────────────────────────────

async function logRefresh(sql: SqlExecutor, resource: string, recordCount: number): Promise<void> {
  await sql.exec(
    `INSERT INTO fapi_refresh_log (resource, last_refreshed_at, record_count, last_success_at, last_error)
     VALUES ($1, NOW(), $2, NOW(), NULL)
     ON CONFLICT (resource) DO UPDATE SET
       last_refreshed_at = NOW(),
       record_count = EXCLUDED.record_count,
       last_success_at = NOW(),
       last_error = NULL`,
    [resource, recordCount],
  );
}

async function logRefreshError(sql: SqlExecutor, resource: string, error: string): Promise<void> {
  await sql.exec(
    `INSERT INTO fapi_refresh_log (resource, last_refreshed_at, record_count, last_error)
     VALUES ($1, NOW(), 0, $2)
     ON CONFLICT (resource) DO UPDATE SET
       last_refreshed_at = NOW(),
       last_error = EXCLUDED.last_error`,
    [resource, error.slice(0, 1000)],
  );
}
