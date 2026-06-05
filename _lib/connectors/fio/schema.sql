-- Fio Banka cache schema pro Netlify Database (Postgres).
--
-- Návrh:
-- - 2 tabulky: account_snapshots (period info + balance) + transactions
-- - Transakce mají JSONB pro raw + extrahovaná pole pro indexing
-- - Pre-aggregated views pro typické dashboard queries:
--     - Cashflow snapshot (current balance, monthly net change)
--     - Daily balance series (chart data)
--     - Top counterparties (kdo platí / komu platím)
--     - Unmatched transactions (= ne-spárované s fakturami)

-- ─── Cache tables ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fio_account_snapshots (
  id BIGSERIAL PRIMARY KEY,
  account_id TEXT NOT NULL,
  bank_id TEXT NOT NULL,
  currency TEXT NOT NULL,
  iban TEXT,
  bic TEXT,
  opening_balance NUMERIC NOT NULL,
  closing_balance NUMERIC NOT NULL,
  date_start DATE NOT NULL,
  date_end DATE NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (account_id, date_end)  -- jeden snapshot per účet+den
);

CREATE INDEX IF NOT EXISTS idx_fio_snapshots_account ON fio_account_snapshots(account_id, date_end DESC);

CREATE TABLE IF NOT EXISTS fio_transactions (
  transaction_id BIGINT PRIMARY KEY,
  account_id TEXT NOT NULL,
  date DATE NOT NULL,
  amount NUMERIC NOT NULL,
  currency TEXT NOT NULL,

  -- Counterparty
  counter_account_number TEXT,
  counter_bank_code TEXT,
  counter_account_name TEXT,
  bic TEXT,

  -- Payment identification
  variable_symbol TEXT,
  constant_symbol TEXT,
  specific_symbol TEXT,
  user_identification TEXT,
  payer_reference TEXT,
  recipient_message TEXT,
  comment TEXT,

  -- Type/meta
  transaction_type TEXT,        -- "Bezhotovostní platba", "Platba kartou", ...
  performed_by TEXT,
  description TEXT,
  instruction_id TEXT,

  raw JSONB NOT NULL,
  cached_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fio_tx_date ON fio_transactions(date DESC);
CREATE INDEX IF NOT EXISTS idx_fio_tx_account_date ON fio_transactions(account_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_fio_tx_amount_direction ON fio_transactions(account_id, date) WHERE amount > 0;
CREATE INDEX IF NOT EXISTS idx_fio_tx_vs ON fio_transactions(variable_symbol) WHERE variable_symbol IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_fio_tx_counter ON fio_transactions(counter_account_number) WHERE counter_account_number IS NOT NULL;

-- ─── Refresh metadata ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fio_refresh_log (
  resource TEXT PRIMARY KEY,         -- 'transactions'
  last_refreshed_at TIMESTAMPTZ NOT NULL,
  record_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  last_success_at TIMESTAMPTZ
);

-- ─── Pre-aggregated views ────────────────────────────────────────────────

-- Cashflow snapshot — aktuální zůstatek + měsíční pohyby
CREATE OR REPLACE VIEW v_fio_cashflow_snapshot AS
WITH latest_snapshot AS (
  SELECT DISTINCT ON (account_id) account_id, closing_balance, currency, date_end
  FROM fio_account_snapshots
  ORDER BY account_id, date_end DESC
),
month_stats AS (
  SELECT
    account_id,
    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS month_incoming,
    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS month_outgoing,
    COUNT(*) AS month_tx_count
  FROM fio_transactions
  WHERE date >= date_trunc('month', CURRENT_DATE)
  GROUP BY account_id
)
SELECT
  s.account_id,
  s.currency,
  s.closing_balance AS current_balance,
  COALESCE(m.month_incoming, 0) AS month_incoming,
  COALESCE(m.month_outgoing, 0) AS month_outgoing,
  COALESCE(m.month_incoming, 0) - COALESCE(m.month_outgoing, 0) AS month_net_change,
  COALESCE(m.month_tx_count, 0) AS month_transaction_count,
  s.date_end AS balance_as_of
FROM latest_snapshot s
LEFT JOIN month_stats m ON m.account_id = s.account_id;

-- Denní zůstatky (last 90 days) — pro line chart
CREATE OR REPLACE VIEW v_fio_daily_balance AS
WITH daily_changes AS (
  SELECT
    account_id,
    date,
    SUM(amount) AS net_change
  FROM fio_transactions
  WHERE date >= CURRENT_DATE - INTERVAL '90 days'
  GROUP BY account_id, date
)
SELECT
  account_id,
  date,
  net_change,
  SUM(net_change) OVER (PARTITION BY account_id ORDER BY date) AS cumulative_change
FROM daily_changes
ORDER BY account_id, date;

-- Top protiúčty podle objemu
CREATE OR REPLACE VIEW v_fio_top_counterparties AS
SELECT
  account_id,
  COALESCE(counter_account_name, 'Neznámý') AS counterparty,
  counter_account_number,
  CASE WHEN amount > 0 THEN 'incoming' ELSE 'outgoing' END AS direction,
  SUM(ABS(amount)) AS total_amount,
  COUNT(*) AS transaction_count,
  MIN(date) AS first_transaction,
  MAX(date) AS last_transaction
FROM fio_transactions
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY account_id, COALESCE(counter_account_name, 'Neznámý'), counter_account_number, (amount > 0)
ORDER BY total_amount DESC;

-- Měsíční cashflow trend (12 měsíců)
CREATE OR REPLACE VIEW v_fio_monthly_cashflow AS
SELECT
  account_id,
  date_trunc('month', date)::date AS month,
  SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS incoming,
  SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS outgoing,
  SUM(amount) AS net_change,
  COUNT(*) AS transaction_count
FROM fio_transactions
WHERE date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY account_id, date_trunc('month', date)
ORDER BY account_id, month DESC;

-- Příchozí platby s VS (= pro cross-reference s FAPI/Fakturoid fakturami)
CREATE OR REPLACE VIEW v_fio_incoming_with_vs AS
SELECT
  transaction_id,
  account_id,
  date,
  amount,
  variable_symbol,
  counter_account_name,
  counter_account_number,
  recipient_message
FROM fio_transactions
WHERE amount > 0
  AND variable_symbol IS NOT NULL
  AND variable_symbol != ''
ORDER BY date DESC;
