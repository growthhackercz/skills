-- FAPI.cz cache schema pro Netlify Database (Postgres).
--
-- Návrh:
-- - Cache tables pro každý FAPI resource — uchovávají raw JSON + extrahovaná
--   klíčová pole pro rychlé filtrování.
-- - Pre-aggregated views pro typické dashboard queries.
-- - Refresh metadata table — kdy se naposledy synchronizovalo.
--
-- Použití ve vibe-builder dashboard projektu:
--   1. Kopíruj do migrations/0001_fapi.sql
--   2. Apply migration: `netlify db:push` (nebo součást netlify-publisher
--      db-init flow)
--   3. Refresh worker (lib/connectors/fapi/refresh.ts) populuje data
--   4. Dashboard čte z views, ne raw tables

-- ─── Cache tables ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fapi_invoices (
  id BIGINT PRIMARY KEY,
  number TEXT NOT NULL,
  created_on TIMESTAMPTZ NOT NULL,
  create_date DATE NOT NULL,
  payday_date DATE,
  client_id BIGINT,
  type TEXT,
  payment_type TEXT,
  currency TEXT,
  exchange_rate_czk NUMERIC,
  paid BOOLEAN NOT NULL DEFAULT FALSE,
  cancelled BOOLEAN NOT NULL DEFAULT FALSE,
  total NUMERIC,
  total_czk NUMERIC,
  total_vat NUMERIC,
  variable_symbol TEXT,
  raw JSONB NOT NULL,
  cached_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fapi_invoices_create_date ON fapi_invoices(create_date);
CREATE INDEX IF NOT EXISTS idx_fapi_invoices_paid ON fapi_invoices(paid) WHERE NOT cancelled;
CREATE INDEX IF NOT EXISTS idx_fapi_invoices_payday ON fapi_invoices(payday_date) WHERE NOT paid AND NOT cancelled;
CREATE INDEX IF NOT EXISTS idx_fapi_invoices_client ON fapi_invoices(client_id);

CREATE TABLE IF NOT EXISTS fapi_orders (
  id BIGINT PRIMARY KEY,
  form_id BIGINT,
  created TIMESTAMPTZ NOT NULL,
  client_id BIGINT,
  invoice_id BIGINT,
  email TEXT,
  first_name TEXT,
  last_name TEXT,
  company TEXT,
  pending BOOLEAN,
  raw JSONB NOT NULL,
  cached_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fapi_orders_created ON fapi_orders(created);
CREATE INDEX IF NOT EXISTS idx_fapi_orders_client ON fapi_orders(client_id);
CREATE INDEX IF NOT EXISTS idx_fapi_orders_invoice ON fapi_orders(invoice_id);

CREATE TABLE IF NOT EXISTS fapi_order_items (
  order_id BIGINT NOT NULL REFERENCES fapi_orders(id) ON DELETE CASCADE,
  position INT NOT NULL,
  name TEXT NOT NULL,
  price NUMERIC,
  price_czk NUMERIC,
  count INT NOT NULL DEFAULT 1,
  raw JSONB NOT NULL,
  PRIMARY KEY (order_id, position)
);

CREATE INDEX IF NOT EXISTS idx_fapi_order_items_name ON fapi_order_items(name);

CREATE TABLE IF NOT EXISTS fapi_clients (
  id BIGINT PRIMARY KEY,
  email TEXT,
  first_name TEXT,
  last_name TEXT,
  company TEXT,
  tax_payer BOOLEAN,
  raw JSONB NOT NULL,
  cached_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fapi_clients_email ON fapi_clients(email);

-- ─── Refresh metadata ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fapi_refresh_log (
  resource TEXT PRIMARY KEY,         -- 'invoices', 'orders', 'clients', 'statistics'
  last_refreshed_at TIMESTAMPTZ NOT NULL,
  record_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  last_success_at TIMESTAMPTZ
);

-- ─── Pre-aggregated views (= rychlé queries pro dashboard) ───────────────

-- Tržby po měsících (jen placené, ne stornované, v CZK)
CREATE OR REPLACE VIEW v_fapi_revenue_by_month AS
SELECT
  date_trunc('month', create_date)::date AS month,
  SUM(total_czk) AS revenue_czk,
  COUNT(*) AS invoice_count
FROM fapi_invoices
WHERE paid = TRUE AND cancelled = FALSE
GROUP BY 1
ORDER BY 1 DESC;

-- Nezaplacené faktury (s dny po splatnosti)
CREATE OR REPLACE VIEW v_fapi_unpaid_invoices AS
SELECT
  id,
  number,
  client_id,
  payday_date,
  total_czk,
  (CURRENT_DATE - payday_date) AS days_overdue,
  CASE
    WHEN payday_date IS NULL THEN 'no_due_date'
    WHEN payday_date >= CURRENT_DATE THEN 'within_due'
    WHEN CURRENT_DATE - payday_date <= 30 THEN 'overdue_1_30'
    WHEN CURRENT_DATE - payday_date <= 60 THEN 'overdue_31_60'
    ELSE 'overdue_60_plus'
  END AS overdue_bucket
FROM fapi_invoices
WHERE paid = FALSE AND cancelled = FALSE
ORDER BY payday_date NULLS LAST;

-- Top zákazníci podle placených CZK
CREATE OR REPLACE VIEW v_fapi_top_customers AS
SELECT
  i.client_id,
  c.email,
  c.company,
  SUM(i.total_czk) AS revenue_czk,
  COUNT(*) AS paid_invoice_count
FROM fapi_invoices i
LEFT JOIN fapi_clients c ON c.id = i.client_id
WHERE i.paid = TRUE AND i.cancelled = FALSE
GROUP BY i.client_id, c.email, c.company
ORDER BY revenue_czk DESC;

-- Top produkty podle revenue
CREATE OR REPLACE VIEW v_fapi_top_products AS
SELECT
  name,
  SUM(COALESCE(price_czk, price) * count) AS revenue_czk,
  SUM(count) AS units_sold,
  COUNT(DISTINCT order_id) AS order_count
FROM fapi_order_items
GROUP BY name
ORDER BY revenue_czk DESC;

-- Daily snapshot KPIs (pro dashboard hero metrics)
CREATE OR REPLACE VIEW v_fapi_daily_snapshot AS
SELECT
  (SELECT SUM(total_czk) FROM fapi_invoices
     WHERE paid = TRUE AND cancelled = FALSE
       AND create_date >= date_trunc('month', CURRENT_DATE)) AS revenue_this_month,
  (SELECT SUM(total_czk) FROM fapi_invoices
     WHERE paid = TRUE AND cancelled = FALSE
       AND create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month')
       AND create_date < date_trunc('month', CURRENT_DATE)) AS revenue_last_month,
  (SELECT SUM(total_czk) FROM fapi_invoices
     WHERE paid = FALSE AND cancelled = FALSE) AS unpaid_total_czk,
  (SELECT COUNT(*) FROM fapi_invoices
     WHERE paid = FALSE AND cancelled = FALSE
       AND payday_date < CURRENT_DATE) AS overdue_count,
  (SELECT SUM(total_czk) FROM fapi_invoices
     WHERE paid = FALSE AND cancelled = FALSE
       AND payday_date < CURRENT_DATE) AS overdue_total_czk;
