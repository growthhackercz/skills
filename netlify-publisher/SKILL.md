---
name: Netlify publisher
description: Buduje a publikuje hotové projekty (statické weby, Next.js apps, dashboardy) z /documents/sites/ na Netlify. Auto-create site z názvu projektu, default je production deploy (rovnou live). Smart safety pro sites s custom doménou (vyžaduje --force-prod nebo --draft). Umí rename na pretty URL, připojit klientovu vlastní doménu, init Netlify DB, rollback. Vždy běží pod klientovým NETLIFY_AUTH_TOKEN.
metadata: {"openclaw":{"requires":{"bins":["python3","netlify","node","npm"],"env":["NETLIFY_AUTH_TOKEN"]},"primaryEnv":"NETLIFY_AUTH_TOKEN","emoji":"🚀"}}
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-25"
---

# Netlify Publisher

Univerzální skill pro budování a publikaci projektů na Netlify. Pokrývá celý
lifecycle: build (detekce frameworku + npm install + překlad zdrojového kódu),
auto-create site, draft deploy, promote do produkce, rename, custom doména,
DB init, rollback.

## Co publisher dělá

1. **Build** — detekuje typ projektu (Next.js static, Next.js SSR, Vite,
   vanilla HTML) a překlene zdrojový kód na výsledné soubory, kterým rozumí
   prohlížeč. Po buildu cleanup `node_modules` a build cache pro úsporu disku.
2. **Auto-create site** — pokud projekt ještě nemá Netlify site, vytvoří ho
   s deterministickým pretty názvem (`<projekt-slug>`, fallback
   `cs-<projekt-slug>`, fallback `cs-<projekt-slug>-<6char-hash>`).
3. **Production deploy (default)** — vrátí klientovi stable URL
   `https://<site-name>.netlify.app`. Klient ji sdílí s týmem nebo zákazníky.
   **Pro sites s custom doménou** (klient má vlastní doménu připojenou)
   helper vrátí safety warning a vyžaduje explicit `--force-prod` nebo
   `--draft` — aby se nepřepsala produkce omylem.
4. **Draft deploy (opt-in, `--draft` flag)** — vrátí unique URL pro náhled
   bez impactu na produkci. Hodí se pro velké redesigny, A/B testy nebo
   prezentaci změn klientovi před live.
5. **Promote** — pokud máš draft a chceš ho povýšit na produkci, použij
   `promote` subcommand.
5. **Rename** — změna pretty URL (např. z `cs-obrat-dashboard` na `obrat`).
6. **Custom doména** — provede klienta krok-po-kroku setupem CNAME u jeho DNS
   providera a po potvrzení napojí doménu na Netlify site.
7. **Rollback** — vrátí site na předchozí deploy, pokud nový má bug.
8. **DB init** — vytvoří Netlify Database (Postgres powered by Neon) pro
   projekty s dynamickými daty.

## Kdy použít

- Po dokončení vibe-builderu (auto-handoff workflow): build → draft deploy
  → výsledná URL klientovi.
- Klient chce publikovat hotový statický web, prezentaci nebo landing page.
- Klient chce nasadit dashboard s živými daty (Next.js SSR + Netlify
  Functions + Netlify DB).
- Klient chce přepojit existující projekt na vlastní doménu.
- Klient potřebuje rollback po neúspěšném deploy.

## Kdy NEpoužívat

- Pro Control Center samotné nebo jiné CliqSales interní služby.
- Pro repozitáře s git workflow (publisher pracuje se složkami v
  `/documents`, ne s git remote).
- Pro projekty, které vyžadují non-Netlify hosting (AWS, Vercel, Cloudflare
  Pages).

## Konvence cest (POVINNÉ)

Publisher vynucuje jednotnou strukturu, aby `/documents/` zůstaly přehledné
a deploy zóny byly izolované od interních logů.

```
/documents/
├── brand/                               existing — Brand DNA, design assets
├── sites/                               POVINNÉ pro projekty — všechny publikovatelné weby
│   └── <slug>/
│       ├── index.html                   deployed soubory
│       ├── images/
│       └── ...                          (Next.js app/, public/, package.json...)
├── platform/
│   └── netlify-publisher/<slug>/        artefakty publisheru per projekt
│       ├── preflight.json
│       ├── ensure-site.json
│       └── deploys/<ISO-timestamp>.json
└── (volné root)                         user files (PDF, prezentace, ad-hoc)
```

**Pravidla:**

- **Projekt = `/documents/sites/<slug>/`** — všechno, co se deployuje (HTML,
  Next.js source, images, package.json...). Publisher subcommandy `build` a
  `deploy` **odmítnou** path mimo `/documents/sites/`.
- **Artefakty = `/documents/platform/netlify-publisher/<slug>/`** — JSON logy
  z publisheru (preflight, ensure-site, deploys). Mimo deploy scope = bezpečně
  oddělené od public souborů. Agent je tam ukládá ručně po každém volání
  publisheru.
- **Slug projektu** = lowercase, alfanumerický s pomlčkami (např.
  `bioptron-medall-landing`, `obrat-dashboard`). Stejný slug pro
  `sites/<slug>/` a `platform/netlify-publisher/<slug>/`.
- **Žádné jiné konvence** — nepoužívej `/documents/projects/`, `/documents/web/`,
  ani root `/documents/<slug>/`. Vše jednotně přes `sites/`.

## Předpoklady

V Integrace → Netlify musí být uložené:

- `NETLIFY_AUTH_TOKEN` — Personal Access Token z Netlify UI (Settings →
  Applications → Personal access tokens).

Volitelně:

- `NETLIFY_SITE_ID` — pokud klient pracuje s jediným site (legacy fallback).
- `NETLIFY_ACCOUNT_SLUG` — pokud má token přístup do více Netlify týmů.

V OpenClaw containeru musí být:

- `python3`, `netlify` CLI, `node`, `npm` (všechny součástí Docker image).

Helper resolvuje hodnoty přes Control Center runtime credential helper.
Secret nikdy nevypisuj do chatu, logu ani do výstupních souborů.

Token zůstává ručně zadaný PAT z Netlify UI. Helper ho předává CLI přes
environment proměnnou `NETLIFY_AUTH_TOKEN`, ne jako argument příkazu.

## Site naming convention

Publisher odvozuje pretty URL deterministicky ze slugu projektu:

```
Vstup: projekt slug (např. "obrat-dashboard")

Pokus 1: <projekt-slug>          (např. "obrat-dashboard" → obrat-dashboard.netlify.app)
Pokus 2: cs-<projekt-slug>       (např. "cs-obrat-dashboard.netlify.app")
Pokus 3: cs-<projekt-slug>-<6h>  (např. "cs-obrat-dashboard-a3f7c1.netlify.app")
```

Pokud `<projekt-slug>` neprojde validací (musí být 3-63 znaků, lowercase,
hyphen-separated), publisher přidá prefix `cs-` automaticky.

Klient může později rename na vlastní pretty název přes `rename` subcommand.

## Hlavní workflow — auto-publish (default po vibe-builderu)

```bash
# Krok 1: Build (npm install + framework build + cleanup)
python3 scripts/netlify_publish.py build /documents/sites/<slug> --json

# Krok 2: Ensure site (create-if-not-exists s deterministickým slugem)
python3 scripts/netlify_publish.py ensure-site --slug <slug> --json

# Krok 3: Production deploy (vrátí stable URL)
python3 scripts/netlify_publish.py deploy /documents/sites/<slug> --site-id <id> --json
```

Po úspěšném buildu a deploy vrať klientovi:

- Stable URL: `https://<site-name>.netlify.app` (= production)
- Možnosti dalšího kroku:
  - Změnit pretty název (`rename`)
  - Připojit vlastní doménu (`add-domain`)
  - Aktualizovat obsah (edit + deploy → instant live update)
  - Rollback pokud něco selže (`rollback --deploy-id <předchozí>`)

**Pro pre-publication review** (velké změny, klient chce vidět před live):
přidej flag `--draft`:

```bash
python3 scripts/netlify_publish.py deploy /documents/sites/<slug> --site-id <id> --draft --json
# Vrátí draft URL https://<hash>--<site-name>.netlify.app
# Po schválení klientem: spusť `promote --site-id <id>`
```

## Smart safety — production deploy na site s custom doménou

Pokud site má připojenou custom doménu (např. `bioptron.live100.cz`),
helper **odmítne** production deploy bez explicit potvrzení. Důvod: production
deploy by **okamžitě přepsal živý web na klientově doméně** (= zákazníci
mohou vidět rozbitou stránku během buildu).

Helper vrátí error:
```
Site má custom doménu 'bioptron.live100.cz'. Production deploy by okamžitě
přepsal živý web na vlastní doméně klienta. Možnosti:
  (1) pro náhled spusť znovu s --draft
  (2) pro přepis produkce spusť znovu s --force-prod
Doporučuj klientovi nejdřív náhled.
```

**Doporučený postup:**

1. Při deploy bez flagů → helper detekuje custom doménu a vrátí warning
2. Agent zastaví a zeptá se klienta:
   > „Tento web je na vaší doméně bioptron.live100.cz. Chcete rovnou
   > publikovat (zákazníci uvidí změnu okamžitě), nebo nejdřív náhled?"
3. Klient řekne „rovnou live" → agent spustí `deploy --force-prod`
4. Klient řekne „nejdřív náhled" → agent spustí `deploy --draft` → vrátí
   draft URL → po schválení `promote`

Sites bez custom domény (jen Netlify subdomain) tuto safety obejdou — production
deploy proběhne rovnou.

## Workflow — Promote draft do produkce

```bash
python3 scripts/netlify_publish.py promote --site-id <id> --json
```

Re-deployne posledně nahranou verzi s `--prod` flagem. Klient dostane stable
URL `https://<site-name>.netlify.app`, která se nemění s každým novým buildem.

## Workflow — Rename na pretty URL

```bash
python3 scripts/netlify_publish.py rename --site-id <id> --new-name <new-slug> --json
```

Změní site name přes Netlify API. Pokud cílový název už existuje
(kolize), publisher vrátí chybu s návrhem alternativ. Nikdy neoverwrite
existující site někoho jiného.

## Workflow — Custom doména (klient vede krok-po-kroku)

```bash
# Krok 1: Informuj klienta o DNS setupu
# (publisher vrátí instrukce z references/01-custom-domain-guide.md)

# Krok 2: Po klientově "hotovo" napoj doménu
python3 scripts/netlify_publish.py add-domain --site-id <id> --domain dashboard.firma.cz --json

# Krok 3: Verify SSL provisioning (poll max 5 min)
python3 scripts/netlify_publish.py verify-domain --site-id <id> --domain dashboard.firma.cz --json
```

Reference `references/01-custom-domain-guide.md` obsahuje krok-po-kroku
návod pro typické české registrátory (Forpsi, CZ.NIC, Active 24, Wedos,
Cloudflare). Použij ho při komunikaci s klientem.

## Workflow — Rollback

```bash
# Krok 1: List recent deploys
python3 scripts/netlify_publish.py list-deploys --site-id <id> --json

# Krok 2: Rollback na konkrétní deploy
python3 scripts/netlify_publish.py rollback --site-id <id> --deploy-id <prev-id> --json
```

Po rollbacku je site instantně na předchozí verzi (Netlify cache je
invalidovaná během 5-10 sekund). Předchozí build se uchovává jako draft a
lze ho zpět promote.

## Workflow — DB init (pro projekty s daty)

```bash
python3 scripts/netlify_publish.py db-init --site-id <id> --json
```

Vyvolá `netlify database init --yes` v projekt složce. Auto-provisionuje
Postgres database (powered by Neon) v regionu Netlify Functions
deploye pro nízkou latenci. Vrátí connection string, který se zapíše do
projekt env vars.

## Konvence pojmenování databází

Konvence pro klientelu CliqSales (= per klient Netlify account):

```
DB #1: cs-data           VŽDY první, pro dashboardy & analytics
DB #2+: cs-<aplikace>    klient si pojmenuje per aplikace
                         (např. cs-booking, cs-portal, cs-helpdesk)
```

**Pravidla:**

- **`cs-data`** je **sdílená** mezi všemi dashboardovými sites. Drží
  source tabulky (fakturoid, meta, ga4, ...) + pre-aggregated views per
  dashboard. Cross-reference dashboardy (= True ROAS, Cash Gap Forecast)
  potřebují SQL JOIN přes tyto zdroje, proto **1 DB sdílená**.
- **`cs-<aplikace>`** je **per aplikace**. Každá samostatná aplikace
  (booking systém, klientský portal, helpdesk) má vlastní DB, protože
  schema je business-specific a izolace je čistější.

**Free tier 3 databáze:** klient se vejde s 1 dashboardovou + 2 aplikačními
DB. Personal $9 = 5 DB. Pro $20 = 50 DB.

## Workflow — Sdílení DB mezi sites (= cs-data napříč dashboardy)

Když má klient víc dashboardových sites, všechny by měly číst ze stejné
`cs-data` DB. Publisher to vyřeší jedním příkazem:

```bash
python3 scripts/netlify_publish.py db-share \
    --from-site-id <cs-data-site> \
    --to-site-id <nový-dashboard-site> \
    --json
```

Default sdílí `DATABASE_URL`. Pro víc env vars (např. `DATABASE_URL_POOLED`,
`DIRECT_URL`) předej `--keys DATABASE_URL,DIRECT_URL`.

Po `db-share` musíš target site **redeployovat**, aby nové env vars
načetly Functions.

**Kdy NEpoužívat db-share:** mezi aplikačními sites (= každá aplikace má
vlastní DB, ne sdílí).

## Workflow — Env vars (API klíče, secrets)

Aplikace na Netlify používá env vars pro tokeny ke třetím službám (Fakturoid,
Meta, GA4, banka, ...). Publisher má 3 subcommandy pro plnou správu:

```bash
# Set jednu env var
python3 scripts/netlify_publish.py env-set --site-id <id> --key FAKTUROID_API_KEY --value <token> --json

# List všech env keys (bez hodnot — security)
python3 scripts/netlify_publish.py env-list --site-id <id> --json

# Smaž env var
python3 scripts/netlify_publish.py env-unset --site-id <id> --key STALE_TOKEN --json
```

## Workflow — Sync credentials z Control Center

Klient zadá credentials JEN JEDNOU v CC (Integrace → Fakturoid, Meta, GA4, ...).
Publisher je propíše do Netlify env vars přes jeden příkaz:

```bash
# Sync všech dostupných services
python3 scripts/netlify_publish.py sync-creds --site-id <id> --json

# Nebo jen vybrané services
python3 scripts/netlify_publish.py sync-creds --site-id <id> --services fakturoid,meta --json
```

Podporované services (pokud má CC nakonfigurovaný credential helper):
`fakturoid`, `meta`, `google_ads`, `ga4`, `fio`, `tink`.

**Mapping (service → Netlify env vars):**

| Service | Env vars nastavené |
|---|---|
| `fakturoid` | `FAKTUROID_API_KEY`, `FAKTUROID_EMAIL`, `FAKTUROID_ACCOUNT_SLUG` |
| `meta` | `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID`, `META_BUSINESS_ID` |
| `google_ads` | `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID` |
| `ga4` | `GA4_PROPERTY_ID`, `GA4_SERVICE_ACCOUNT_JSON` |
| `fio` | `FIO_TOKEN`, `FIO_ACCOUNT_ID` |
| `tink` | `TINK_CLIENT_ID`, `TINK_CLIENT_SECRET`, `TINK_REFRESH_TOKEN` |

Klient pak ve své aplikaci jen čte `process.env.FAKTUROID_API_KEY`. Žádné
manuální klikání v Netlify dashboardu.

## Workflow — Identity (built-in auth)

```bash
python3 scripts/netlify_publish.py identity-enable --site-id <id> --json
```

Aktivuje Netlify Identity pro site — zdarma do 1 000 active users / měsíc.
Po aktivaci aplikace přidá `netlify-identity-widget` JS knihovnu pro login UI
(generuje vibe-builder při generování aplikace s auth potřebou).

Pro plný kontrol (NextAuth, Clerk, vlastní login) Identity neaktivuj — řešení
je v aplikačním kódu.

## Workflow — Trigger initial refresh po deployi

Po prvním deployi aplikace má prázdnou DB. Aby klient hned viděl data,
spusť jednorázový refresh endpoint:

```bash
python3 scripts/netlify_publish.py trigger-refresh --site-id <id> --endpoint /api/refresh --json
```

Defaultní endpoint je `/api/refresh`. Volá HTTP POST. Pokud aplikace
vyžaduje auth na refresh (např. `CRON_SECRET`), předej `--token <secret>`.

Po prvním refreshi aplikace má aktuální data z Fakturoidu / Meta / atd.
Další refreshe běží automaticky přes Netlify Scheduled Functions (cron
config v `netlify.toml`, generuje vibe-builder).

## Auto-handoff s vibe-builderem

Když vibe-builder skončí svou práci (vygeneruje projekt), **automaticky**
vyvolává publisher v pořadí:

```
vibe-builder → publisher build
            → publisher ensure-site
            → publisher db-init           (pokud projekt potřebuje DB)
            → publisher sync-creds        (propíše API klíče z CC do Netlify)
            → publisher identity-enable   (pokud projekt potřebuje auth)
            → publisher deploy (draft)
            → publisher trigger-refresh   (initial data load po deployi)
```

Klient nemusí publisher explicit vyvolávat. Default flow:

1. Klient: "Vytvoř dashboard nad fakturoidem"
2. Vibe-builder: generuje kód
3. Publisher (auto): build + site + DB + sync-creds + identity + deploy + refresh
4. Klient dostane URL v chatu, klikne, prohlédne v browseru
5. Klient: "Posun do produkce" → publisher promote
6. Klient: "Připoj doménu dashboard.firma.cz" → publisher add-domain workflow

## Bezpečnostní pravidla

- Nepublikuj složku bez `index.html` (pro static) nebo bez `package.json`
  + build output (pro SSR).
- Nepublikuj `.env`, privátní klíče, certifikáty, databáze, `.git`,
  `node_modules`, `.next` cache, dočasné runtime soubory.
- Když build nebo deploy najde blokovaný soubor, zastav se a požádej
  klienta o vyčištění výstupní složky.
- Default je draft deploy. Produkce vyžaduje explicitní potvrzení
  klientem (volání `promote` subcommandu).
- Nehádej `site_id`; pokud chybí, použij `ensure-site` s deterministickým
  slugem nebo explicitní `create-site` s `--confirm-create`.
- `create-site` a `delete-site` vyžadují explicit flagy (`--confirm-create`
  / `--confirm-delete`).
- Nepoužívej `netlify login`; integrace používá ručně vložený
  `NETLIFY_AUTH_TOKEN`.
- Token sanitizuj v error logs (helper to dělá automaticky).
- Site name validuj proti regex `^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])$`.
- Custom doména musí být validní FQDN (regex check).

## Limity (zděděné z v1)

- Max 5 000 souborů v deploy složce.
- Max 50 MB per soubor.
- Max 100 MB celková velikost deploy složky.
- npm install timeout: 5 minut.
- next build timeout: 10 minut.
- Netlify CLI timeout: 10 minut (configurable přes
  `NETLIFY_CLI_TIMEOUT_SECONDS`).
- DNS / SSL verification poll: max 5 minut.

## Edge cases

- **Build selže** (npm error, next build fail) → vrátí log + návrh
  (např. „zkus s jinou theme" nebo „dependency conflict v package.json").
- **Site name kolize** → auto-fallback s prefix `cs-` a 6-char hash.
- **DNS propagation timeout** (> 5 min) → vrátí klientovi instrukce
  „zkontroluj DNS záznam, případně počkej 30 minut a zavolej
  `verify-domain` znovu".
- **SSL provisioning timeout** → vrátí „provisioning trvá obvykle 5-30
  minut, max 24 hodin, status zkontroluj později".
- **DB init na non-existent site** → publisher nejdřív zavolá
  `ensure-site`, pak `db-init`.
- **Promote bez previous draft** → error „nejprve spusť `deploy` v draft
  modu".
- **Rollback na neexistující deploy** → vrátí seznam dostupných deployů.
- **`npm install` timeout** → návrh: smaž `package-lock.json` a zkus znovu,
  nebo přepni na `npm ci` mode.

## Rychlý test integrace

```bash
python3 scripts/netlify_publish.py test --json
```

Test bez `--site-id` ověří jen Netlify token. Se `--site-id` ověří
přístup ke konkrétnímu site.

## Co NENÍ v v1.0 (= odložené do v1.1+)

- Edge Functions deploy (optimalizace, ne nový use case)
- Build cache reuse mezi deployy (optimalizace, klient si nevšimne)
- Multi-environment (staging vs production na stejném site)
- Git-based deploy (CliqSales workflow je file-based přes `/documents`)
