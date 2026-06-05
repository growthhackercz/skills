/**
 * Fio Banka authentication wrapper.
 *
 * Fio API specifika:
 *   - Token = read-only API key, získaný v Internetbance:
 *     Nastavení → Nastavení API → Vytvořit token
 *   - Token je vázaný na konkrétní účet (klient může mít víc tokenů pro
 *     víc účtů)
 *   - Token jde do URL PATH (ne header!) — Fio API design
 *   - Rate limit: max 1 request / 30 sekund per token (jinak HTTP 409)
 *
 * Env vars (set přes netlify-publisher env-set):
 *   FIO_TOKEN   — povinné, read-only token
 *
 * Security note:
 *   - Token v URL = riziko log leakage. Connector ho sanitizuje v error
 *     messages.
 *   - Nikdy nezpřístupnit FIO_TOKEN v JavaScriptu klientského browseru —
 *     vždy server-side (Netlify Function).
 */

export const FIO_BASE_URL = 'https://fioapi.fio.cz/v1/rest';

export interface FioCredentials {
  token: string;
}

export function loadFioCredentials(): FioCredentials {
  const token = (process.env.FIO_TOKEN ?? '').trim();
  if (!token) {
    throw new Error(
      'FIO_TOKEN chybí v env vars. Nastav přes netlify-publisher env-set ' +
        '(token získáš v Internetbance Fio: Nastavení → Nastavení API).',
    );
  }
  // Basic sanity check — Fio tokeny jsou ~64 znaků
  if (token.length < 20) {
    throw new Error('FIO_TOKEN je podezřele krátký. Ověř, že jsi zkopíroval celý token.');
  }
  return { token };
}

/**
 * Sanitizace URL pro error logy — odstraní token z PATH.
 */
export function sanitizeUrl(url: string, token: string): string {
  return url.replace(token, '[REDACTED_TOKEN]');
}

/**
 * Standardní hlavičky pro Fio request. Token jde do URL, ne header.
 */
export function fioHeaders(): Record<string, string> {
  return {
    Accept: 'application/json',
    'User-Agent': 'cliqsales-fio-connector/1.0',
  };
}
