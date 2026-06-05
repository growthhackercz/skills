# Přehled FAPI API

## Co to je

REST API systému **FAPI.cz** — český systém pro online prodej, faktury, objednávky, slevové kódy. API je zdarma na všech tarifech. Tento skill čte data jen pro analytiku — nikdy nezapisuje.

## Adresa a verze

- **Base URL:** `https://api.fapi.cz`
- **Bez verzového prefixu** (žádné `/v1`). Všechny cesty začínají rovnou názvem zdroje, např. `/invoices`, `/orders`, `/clients`.
- Žádné API verze nejsou v dokumentaci ani v oficiálním PHP klientu odkazované.

## Autentizace

**HTTP Basic Auth** přes hlavičku `Authorization: Basic <base64(uživatel:klíč)>`.

| Pole | Co tam patří |
|---|---|
| Uživatel | **E-mail účtu FAPI** (např. `petr@firma.cz`) |
| Heslo | **API klíč** vygenerovaný v UI (řetězec ~25 znaků) |

Klíč vygeneruješ v `Můj účet → API klíče → Nový API klíč`. Expirace ani rotace nejsou dokumentované — zachází se s ním jako s trvalým heslem.

V tomhle skillu se autentizace nikdy nepíše ručně — všechno za tebe udělá pomocný skript `{baseDir}/scripts/call_fapi.py`, který načte `FAPI_USER` a `FAPI_TOKEN` z prostředí a doplní je do Basic Auth headeru. Tajemství se nikdy nedostává do URL ani do stdout.

## Tvar odpovědi

- **Vždy JSON.**
- Pro **list endpointy** je tělo objekt s jediným klíčem podle názvu zdroje:
  ```json
  { "invoices": [ {...}, {...} ] }
  { "orders":   [ {...}, {...} ] }
  { "clients":  [ {...}, {...} ] }
  ```
  Pole se jmenuje `invoices`, `orders`, `clients` (množné číslo, podle zdroje).
- Pro **detail endpointy** (`/invoices/123`) je tělo přímo daný objekt.
- **Žádné `meta`**, žádná `pagination` sekce v těle, žádný `Link` header. Celkový počet záznamů se zjistí přes samostatný endpoint (viz `endpointy.md` — `/invoices/count`).

## Formát názvů polí

`snake_case`. **Pozor: konvence napříč zdroji není konzistentní** — Invoice má `created_on`, Order má `created`. Vždy si ověř v `endpointy.md`, jak se pole reálně jmenuje pro daný zdroj.

## Chyby

| HTTP | Význam | Co s tím |
|---|---|---|
| 400 | Validation error — špatný parametr nebo body. Odpověď obsahuje `{"message":"..."}`. | Ukaž klientovi message, oprav volání. |
| 401 | Špatný nebo chybějící Basic Auth. | Ověř `FAPI_USER` a `FAPI_TOKEN` v Control Center integraci FAPI. Pokud chybí, ukaž `{baseDir}/references/setup.md`. |
| 404 | Zdroj neexistuje (špatné ID). | Sděl klientovi, pokračuj. |
| 429 | Rate limit — **není dokumentováno**, ale teoreticky se může objevit. | Počkej 5–10 sekund a zkus znovu. |
| 5xx | Chyba na straně FAPI. | Zopakuj později. Pokud to drhne déle, oznam klientovi a zastav. |

Skript `call_fapi.py` u všech 4xx/5xx vrátí exit kód 2 a vypíše tělo odpovědi do stderr.

## Co API umí (přehled)

| Zdroj | Cesta | K čemu se hodí |
|---|---|---|
| Faktury | `/invoices` | Tržby, splatnosti, stornovaná čísla, detaily faktury |
| Objednávky | `/orders` | Co se prodalo, kdy, komu, přes jaký formulář, jaké položky |
| Klienti | `/clients` | Kdo nakupuje, kontakty, opakované nákupy |
| Slevové kódy | `/vouchers` | Stav voucheru (`valid` / `applied`), kdo si ho uplatnil |
| Souhrnné statistiky | `/statistics/total` | **Předagregované tržby/storna/po splatnosti za období** — viz `endpointy.md` |
| Šablony položek | `/item-templates` | Katalog produktů |
| Slevové akce | `/discount-codes` | Generátor a stav akcí |
| Formuláře | `/forms` | Prodejní formuláře |

Detaily polí v jednotlivých zdrojích jsou v `{baseDir}/references/endpointy.md`.

## Co API neumí

- **Tagy / segmenty kontaktů.** Pole `tags` na `/clients` neexistuje, žádný `/tags` endpoint.
- **MRR / ARR / churn / cohort analytics.** `/statistics/total` vrací jen základní časové řady.
- **Refund jako samostatný objekt.** Vrácení peněz se ve FAPI realizuje stornem faktury (`cancelled: true`) — žádný `/refunds` endpoint, žádné částečné vrácení v JSON.
- **Částečná platba na úrovni JSON.** Faktura má jen `paid: true/false` — pole typu `paid_amount` nebo `amount_due` neexistuje.
- **Webhooks přes API.** Webhooky se ve FAPI zakládají jen v UI (`Nastavení → Propojení aplikací`), ne přes API.
- **Bulk operace.** Žádný `/invoices/bulk`, vše po jednom záznamu.

Detail v `{baseDir}/references/omezeni-a-pasti.md`.

## Zdroje

- Oficiální PHP klient (autoritativní pro tvar dat): https://github.com/fapi-cz/fapi-client
- Nápověda FAPI — autentizace: https://napoveda.fapi.cz/article/128-jak-ziskat-api-klic
- Nápověda FAPI — obecně o API: https://napoveda.fapi.cz/article/84-ovladani-fapi-pres-api-rozhrani
- (Apiary `fapi.docs.apiary.io` a `web.fapi.cz/api-doc` jsou SPA bez statického obsahu — nepoužitelné k dohledávání.)
