/**
 * FAPI.cz authentication wrapper.
 *
 * FAPI používá HTTP Basic auth (user email + API token).
 * Token získáš v FAPI UI: Můj účet → API klíče.
 *
 * Env vars (set přes netlify-publisher env-set):
 *   FAPI_USER   — email účtu
 *   FAPI_TOKEN  — API klíč
 *
 * Token NIKDY nedávej do query stringu, žádných shell argumentů ani do logů.
 * Vždy přes Authorization header.
 */

export const FAPI_BASE_URL = 'https://api.fapi.cz';

export interface FapiCredentials {
  user: string;
  token: string;
}

/**
 * Načti credentials z env vars. Vyhoď chybu, pokud chybí (lépe early-fail
 * než silently bez tokenu).
 */
export function loadFapiCredentials(): FapiCredentials {
  const user = (process.env.FAPI_USER ?? '').trim();
  const token = (process.env.FAPI_TOKEN ?? '').trim();
  if (!user || !token) {
    throw new Error(
      'FAPI_USER nebo FAPI_TOKEN chybí v env vars. ' +
        'Nastav přes netlify-publisher env-set, nebo v Netlify UI → Settings → Environment.',
    );
  }
  return { user, token };
}

/**
 * Vrátí Basic auth header value.
 */
export function fapiAuthHeader(creds: FapiCredentials): string {
  const encoded = Buffer.from(`${creds.user}:${creds.token}`, 'utf8').toString('base64');
  return `Basic ${encoded}`;
}

/**
 * Standardní hlavičky pro každý FAPI request.
 */
export function fapiHeaders(creds: FapiCredentials): Record<string, string> {
  return {
    Accept: 'application/json',
    Authorization: fapiAuthHeader(creds),
    'User-Agent': 'cliqsales-fapi-connector/1.0',
  };
}
