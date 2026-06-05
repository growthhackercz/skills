/**
 * Fio Banka background refresh worker.
 *
 * POZOR — Fio má extrémně přísný rate limit: 30 sekund mezi requesty per token.
 *   - Cron interval doporučujeme 5-15 min (= komfortní margin)
 *   - Manual refresh button: enforce client-side cooldown (= 30s lockout
 *     po kliknutí)
 *   - Pokud klient má víc Fio účtů (= víc tokenů), refresh per token sequentially
 *     se 30+s pauzou mezi
 *
 * Strategy:
 *   - Default: fetch posledních 90 dní transakcí (= periods endpoint, idempotent)
 *   - Alternativně: /last endpoint posouvá pointer (vhodné jen pokud máme
 *     persistent state managment)
 *
 * Pattern použití v Netlify Scheduled Function:
 *
 * ```typescript
 * // app/api/refresh/fio/route.ts
 * import { neon } from '@neondatabase/serverless';
 * import { refreshFioAll } from '@cliqsales/connectors/fio/refresh';
 *
 * const sql = neon(process.env.NETLIFY_DATABASE_URL!);
 *
 * export async function POST() {
 *   const result = await refreshFioAll({
 *     exec: async (q, p) => sql(q, p),
 *   });
 *   return Response.json(result);
 * }
 *
 * export const config = { schedule: '@every 15m' };
 * ```
 */

import { loadFioCredentials } from './auth';
import { getTransactionsByPeriod, type FioTransaction, type FioAccountInfo } from './operations';

export interface SqlExecutor {
  exec(sql: string, params?: unknown[]): Promise<unknown[]>;
}

export interface RefreshSummary {
  resource: string;
  ok: boolean;
  recordCount: number;
  durationMs: number;
  error?: string;
}

/**
 * Refresh Fio transakcí — stáhne periods endpoint pro posledních N dní
 * a upsertuje. Idempotentní (lze volat víckrát).
 *
 * @param sql — Postgres executor
 * @param options.daysBack — kolik dní zpět (default 90)
 */
export async function refreshFioTransactions(
  sql: SqlExecutor,
  options: { daysBack?: number } = {},
): Promise<RefreshSummary> {
  const startMs = Date.now();
  try {
    const creds = loadFioCredentials();
    const daysBack = options.daysBack ?? 90;
    const today = new Date();
    const from = new Date(today.getTime() - daysBack * 24 * 60 * 60 * 1000)
      .toISOString().slice(0, 10);
    const to = today.toISOString().slice(0, 10);

    const stmt = await getTransactionsByPeriod(creds, { from, to });

    // Upsert account snapshot
    await upsertAccountSnapshot(sql, stmt.info, to);

    // Upsert transactions
    for (const tx of stmt.transactions) {
      await upsertTransaction(sql, stmt.info.accountId, tx);
    }

    await logRefresh(sql, 'transactions', stmt.transactions.length);
    return {
      resource: 'transactions',
      ok: true,
      recordCount: stmt.transactions.length,
      durationMs: Date.now() - startMs,
    };
  } catch (err) {
    const error = err instanceof Error ? err.message : String(err);
    await logRefreshError(sql, 'transactions', error);
    return {
      resource: 'transactions',
      ok: false,
      recordCount: 0,
      durationMs: Date.now() - startMs,
      error,
    };
  }
}

/**
 * Refresh všeho — pro Fio = jen transactions (Fio nemá jiné resources k cache).
 */
export async function refreshFioAll(sql: SqlExecutor): Promise<{
  ok: boolean;
  results: RefreshSummary[];
  durationMs: number;
}> {
  const start = Date.now();
  const result = await refreshFioTransactions(sql);
  return {
    ok: result.ok,
    results: [result],
    durationMs: Date.now() - start,
  };
}

// ─── Upsert helpers ──────────────────────────────────────────────────────

async function upsertAccountSnapshot(
  sql: SqlExecutor,
  info: FioAccountInfo,
  dateEnd: string,
): Promise<void> {
  await sql.exec(
    `INSERT INTO fio_account_snapshots (
      account_id, bank_id, currency, iban, bic,
      opening_balance, closing_balance, date_start, date_end, fetched_at
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
    ON CONFLICT (account_id, date_end) DO UPDATE SET
      closing_balance = EXCLUDED.closing_balance,
      fetched_at = NOW()
    `,
    [
      info.accountId,
      info.bankId,
      info.currency,
      info.iban,
      info.bic,
      info.openingBalance,
      info.closingBalance,
      info.dateStart ? info.dateStart.slice(0, 10) : null,
      dateEnd,
    ],
  );
}

async function upsertTransaction(
  sql: SqlExecutor,
  accountId: string,
  tx: FioTransaction,
): Promise<void> {
  await sql.exec(
    `INSERT INTO fio_transactions (
      transaction_id, account_id, date, amount, currency,
      counter_account_number, counter_bank_code, counter_account_name, bic,
      variable_symbol, constant_symbol, specific_symbol,
      user_identification, payer_reference, recipient_message, comment,
      transaction_type, performed_by, description, instruction_id,
      raw, cached_at
    ) VALUES (
      $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
      $13, $14, $15, $16, $17, $18, $19, $20, $21, NOW()
    )
    ON CONFLICT (transaction_id) DO UPDATE SET
      raw = EXCLUDED.raw,
      cached_at = NOW()
    `,
    [
      tx.transactionId,
      accountId,
      tx.date,
      tx.amount,
      tx.currency,
      tx.counterAccountNumber ?? null,
      tx.counterBankCode ?? null,
      tx.counterAccountName ?? null,
      tx.bic ?? null,
      tx.variableSymbol ?? null,
      tx.constantSymbol ?? null,
      tx.specificSymbol ?? null,
      tx.userIdentification ?? null,
      tx.payerReference ?? null,
      tx.recipientMessage ?? null,
      tx.comment ?? null,
      tx.transactionType ?? null,
      tx.performedBy ?? null,
      tx.description ?? null,
      tx.instructionId ?? null,
      JSON.stringify(tx.raw),
    ],
  );
}

async function logRefresh(sql: SqlExecutor, resource: string, recordCount: number): Promise<void> {
  await sql.exec(
    `INSERT INTO fio_refresh_log (resource, last_refreshed_at, record_count, last_success_at, last_error)
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
    `INSERT INTO fio_refresh_log (resource, last_refreshed_at, record_count, last_error)
     VALUES ($1, NOW(), 0, $2)
     ON CONFLICT (resource) DO UPDATE SET
       last_refreshed_at = NOW(),
       last_error = EXCLUDED.last_error`,
    [resource, error.slice(0, 1000)],
  );
}
