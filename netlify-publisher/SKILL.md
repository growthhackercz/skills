---
name: Netlify publisher
description: Buduje a publikuje hotové projekty (statické weby, Next.js apps, dashboardy) z /documents/sites/ na Netlify. Umí schválené create/ensure site z názvu projektu, bezpečný draft deploy, promote, rollback, rename, custom doménu a DB init. Produkce i vytvoření nového site vyžadují výslovné potvrzení klienta. Token načítá z Control Center secret store.
metadata: {"openclaw":{"requires":{"bins":["python3","netlify","node","npm"]},"emoji":"🚀"}}
category: integrations
status: ready
version: "1.3.4"
publishedAt: "2026-08-31"
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
2. **Ensure site** — najde existující site podle deterministického názvu. Pokud
   žádný neexistuje, nejprve ukáže `--dry-run` plán a vytvoří ho až s
   `--confirm-create` po výslovném souhlasu klienta (`<projekt-slug>`, fallback
   `cs-<projekt-slug>`, fallback `cs-<projekt-slug>-<6char-hash>`).
3. **Draft deploy (default)** — vrátí unique URL pro náhled
   bez impactu na produkci. Hodí se pro velké redesigny, A/B testy nebo
   prezentaci změn klientovi před live.
4. **Production / Promote** — až po výslovném souhlasu klienta a pouze s
   `--confirm-publish yes`; custom doména navíc vyžaduje `--force-prod`.
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
- Klient chce nasadit dashboard s živými daty (statický export + Netlify
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
  publisheru. Každý JSON výstup helperu už nese `skillVersion: "1.3.4"` a
  `artifactVersion: 1`; při uložení je zachovej beze změny.
- **Slug projektu** = lowercase, alfanumerický s pomlčkami (např.
  `bioptron-medall-landing`, `obrat-dashboard`). Stejný slug pro
  `sites/<slug>/` a `platform/netlify-publisher/<slug>/`.
- **Žádné jiné konvence** — nepoužívej `/documents/projects/`, `/documents/web/`,
  ani root `/documents/<slug>/`. Vše jednotně přes `sites/`.

## ⚠️ Model důvěry u buildu — co publisher zaručuje a co ne

Publisher **nepředává** buildu tajné proměnné procesu (allowlist prostředí)
a **začerňuje** je v diagnostice. To omezuje nejčastější únik, ale **není to
izolace**.

Build pořád běží pod stejným uživatelem a se stejným `HOME`, takže skript
projektu nebo kterékoli jeho závislosti si může přečíst soubory na disku —
včetně uložených přihlašovacích údajů. Skutečnou hranicí by byl build
v odděleném, neprivilegovaném prostředí bez připojených klíčů; to publisher
zatím nedělá.

**Důsledek:** stavěj jen projekty, kterým klient důvěřuje. Nikdy netvrď, že
je build cizího projektu izolovaný.

## Předpoklady

V Integrace → Netlify musí být uložené:

- `NETLIFY_AUTH_TOKEN` — Personal Access Token z Netlify UI (Settings →
  Applications → Personal access tokens).

Volitelně:

- `NETLIFY_SITE_ID` — pokud klient pracuje s jediným site (legacy fallback).
- `NETLIFY_ACCOUNT_SLUG` — pokud má token přístup do více Netlify týmů.

V OpenClaw containeru musí být:

- `python3`, `netlify` CLI, `node`, `npm` (všechny součástí Docker image).

Helper resolvuje aktuální hodnoty přes Control Center runtime credential helper
při každém spuštění; nepřebírá zastaralý token z dlouho běžící Gateway session.
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

U 63znakového slugu publisher prefixované varianty deterministicky zkrátí,
aby všechny zůstaly do 63 znaků. U 1–2znakového slugu doplní bezpečnou `cc-`
variantu. Vždy tak zkusí tři různé názvy splňující Netlify validaci (3–63 znaků,
lowercase, hyphen-separated).

Klient může později rename na vlastní pretty název přes `rename` subcommand.

## Hlavní workflow — auto-publish (default po vibe-builderu)

```bash
# Krok 1: Build (npm install + framework build + cleanup)
python3 scripts/netlify_publish.py build /documents/sites/<slug> --json

# Krok 2a: Ensure site bez vytvoření (existing vrátí siteId, jinak plán)
python3 scripts/netlify_publish.py ensure-site --slug <slug> --dry-run --json

# Krok 2b: pouze když site chybí — po schválení klientem
python3 scripts/netlify_publish.py ensure-site --slug <slug> --confirm-create --json

# Krok 3: Draft deploy (bez flagu je bezpečný default)
python3 scripts/netlify_publish.py deploy /documents/sites/<slug> --site-id <id> --json
```

Deploy helper rozlišuje static a SSR:

- Static export (`output: 'export'`, `out/`, Vite `dist/`, vanilla HTML) se
  uploaduje přes `--no-build` z privátního dočasného stromu, který obsahuje
  přesně soubory prošlé bezpečnostní kontrolou. Původní projektový adresář se
  Netlify CLI nikdy nepředá jako public `--dir`; `.web-builder.json`,
  `.netlify-state.json`, cache ani jiné přeskočené interní soubory se proto
  nemohou omylem zveřejnit ani u vanilla projektu s výstupem v kořeni.
- Next.js SSR/hybrid (`.next/`) používá jediný podporovaný Netlify build+deploy
  proces, aby zachoval framework pluginy, výsledný routing i post-build změny
  konfigurace. Publisher před CLI vloží do `PATH` privátní shimy pro `npm` a,
  je-li dostupný, `yarn`; z package-manager child procesů odstraní pouze deploy
  PAT. Tím chrání první automatickou instalaci chybějícího framework pluginu i
  local-plugin instalaci s `yarn.lock`, které probíhají ještě před aplikací
  build env. Kořenový `netlify.toml` navíc musí obsahovat
  `[build.environment] NETLIFY_AUTH_TOKEN = ""`: parent CLI má PAT pro upload,
  ale projektový build a plugin child procesy díky config precedence dostanou
  prázdnou hodnotu. Chybějící maska nebo neprázdný context override skončí
  fail-closed před deployem. Nepřepisuj to na `deploy --no-build`, ruční
  `--dir <root>` ani nepřidávej `--config` — Netlify CLI 26 takový veřejný
  deploy argument nemá.

Helper po deployi ověřuje výslednou URL. Pokud vrátí 404/5xx nebo URL chybí,
nezapíše `.netlify-state.json` a agent má chybu opravit místo hlášení staré
nefunkční preview URL.

Direct deploy uzná pouze terminální stav `ready` a přesnou vazbu odpovědi na
požadovaný site; chybějící binding musí potvrdit autoritativní site-scoped
follow-up. Pole `scan.files` ve výstupu je u static `publish-output` přesný
finální public manifest předaný CLI (`isFinalPublicManifest: true`).
`scan.functionFiles` je oddělený preflight zdrojů funkcí; jejich finální
serverový bundle skládá Netlify CLI, takže `isFinalDeployManifest` je true jen
u statického webu bez funkcí. U SSR je celý scan pravdivě
`ssr-project-and-build-output-preflight`: zvlášť spočítá zdroje a lokální
`.next`, přitom má oba final-manifest příznaky false, protože finální SSR bundle
skládá až Netlify CLI.
Každý atomický state write nese `skillVersion: "1.3.4"` a `stateVersion: 2`
podle bundled `skill-contract.json`.

### Kontrakt samostatného publisher tasku

Pokud publisher běží jako krok širšího workflow (například Vibe Builder),
existující upstream `metadata.contract` **nepřepisuj**. U samostatného publisher
tasku jej nejdřív načti; při update zachovej/merge **všechna existující
metadata** a přidej jeden kontrakt podle cíle a vždy
`contractParams: {"slug":"<slug projektu>"}`:

- draft: `netlify-publisher:draft-deploy`
- přímý production deploy: `netlify-publisher:production-deploy`
- promote schváleného draftu: `netlify-publisher:production-promote`
- rollback: `netlify-publisher:production-rollback`

Checkpoint vrácený Control Center je závazný: chybějící položky oprav a přechod
do review zopakuj. ID staré operace se před novým state write explicitně maže,
takže nemůže falešně splnit jiný checkpoint.

`.netlify-state.json` z verze 1 se při první ostré publish operaci migruje
idempotentně na `stateVersion: 2`: `siteId` a produkční URL zůstávají, ale starý
draft bez `draftDeployId` se zneplatní a musí vzniknout nový náhled. Stav s
neznámou budoucí verzí se nikdy nekopíruje ani nepřepisuje — operace skončí
fail-closed. Artefakt s nižší `skillVersion` nepoužívej jako novou šablonu;
nejdřív ho nech projít touto migrací.

Po úspěšném buildu a deploy vrať klientovi:

- Draft URL: `https://<hash>--<site-name>.netlify.app`
- Možnosti dalšího kroku:
  - Změnit pretty název (`rename`)
  - Připojit vlastní doménu (`add-domain`)
  - Aktualizovat obsah (edit + nový draft deploy; do live až po schváleném promote)
  - Rollback pokud něco selže (`rollback --site-id <id> --path
    /documents/sites/<slug> --deploy-id <předchozí> --confirm-publish yes`)

`--draft` lze uvést explicitně, ale chování je stejné jako bezpečný default:

```bash
python3 scripts/netlify_publish.py deploy /documents/sites/<slug> --site-id <id> --draft --json
# Vrátí draft URL a přesné deployId a atomicky je uloží jako jednu dvojici.
# Klientovi ukaž přátelsky URL; deployId je interní vazba pro pozdější promote.
# Po schválení klientem:
# `promote --site-id <id> --path /documents/sites/<slug> \
#   --deploy-id <draft-deploy-id> --confirm-publish yes`
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
  (2) pro přepis produkce spusť znovu s --confirm-publish yes --force-prod
Doporučuj klientovi nejdřív náhled.
```

**Doporučený postup:**

1. Deploy bez publikačního potvrzení vždy vytvoří draft.
2. Agent ukáže draft a zeptá se klienta:
   > „Tento web je na vaší doméně bioptron.live100.cz. Chcete rovnou
   > publikovat (zákazníci uvidí změnu okamžitě), nebo nejdřív náhled?"
3. Klient řekne „rovnou live" → agent spustí
   `deploy /documents/sites/<slug> --site-id <id> --confirm-publish yes --force-prod`.
4. Klient schválí existující draft → agent spustí
   `promote --site-id <id> --path /documents/sites/<slug> --deploy-id <schválené-id> --confirm-publish yes --force-prod`.

Site bez custom domény nepotřebuje `--force-prod`, ale pořád vyžaduje
`--confirm-publish yes`.

## Workflow — Promote draft do produkce

```bash
python3 scripts/netlify_publish.py promote --site-id <id> \
  --path /documents/sites/<slug> --deploy-id <draft-deploy-id> \
  --confirm-publish yes --json
```

Označí přesně klientem schválený úspěšný draft jako produkční přes Netlify API
`restoreSiteDeploy`. Klient dostane stable URL
`https://<site-name>.netlify.app`, která se nemění s každým novým buildem.
Promote ověří shodu `--deploy-id`, context náhledu a draft stav `ready`.
Po `restoreSiteDeploy` uzná jen restore stav `current` s přesným site/deploy
bindingem (nebo autoritativní `getSite` follow-up). Site ID, deploy ID i URL
ověří proti pending dvojici v projektovém
`.netlify-state.json`, ověří stabilní URL a pending dvojici vyčistí. Deploy,
promote, rollback i připojení vlastní domény sdílejí per-site publish lock;
deploy navíc používá per-project lock. Souběžná novější verze nemůže být
přepsána nebo omylem odstraněna ani z jiného projektového adresáře.
U site s custom doménou vyžaduje stejně jako přímý production deploy navíc
`--force-prod`.

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
python3 scripts/netlify_publish.py rollback --site-id <id> \
  --path /documents/sites/<slug> --deploy-id <prev-id> \
  --confirm-publish yes --json
```

Rollback vyžaduje projektovou cestu, ověří její uložené site ID, běží pod
project i per-site lockem a až po restore stavu `current` aktualizuje lokální
`.netlify-state.json`. U site s custom doménou/aliasem přidej po klientově
souhlasu také `--force-prod`. Předchozí build se uchovává a lze ho později
znovu vybrat.

## Workflow — DB init (pro projekty s daty)

🛑 **Databáze je placený zdroj na účtu klienta.** Nejdřív mu řekni, co vzniká
a co to stojí, a počkej na souhlas. Bez `--confirm-cost yes` příkaz skončí
STOPem. Náhled bez založení: přidej `--dry-run`.

```bash
# 1) náhled — nic nezaloží
python3 scripts/netlify_publish.py db-init \
  --site-id <id> --path /documents/sites/<slug> --dry-run --json

# 2) ostrý běh — až po výslovném souhlasu klienta
python3 scripts/netlify_publish.py db-init \
  --site-id <id> --path /documents/sites/<slug> --confirm-cost yes --json
```

Helper nejdřív ověří explicitní site, sváže s ní přes `netlify link --id`
právě zadanou projektovou složku a teprve potom zavolá
`netlify database init --yes`. Tento Netlify příkaz nemá `--json` ani vlastní
`--site` parametr; bez předchozího linku by mohl pracovat s jiným projektem.
Connection string zůstává v Netlify a helper ho nikdy nevrací do chatu.
Auto-provisionuje Postgres database (powered by Neon) v regionu Netlify Functions
deploye pro nízkou latenci a Netlify ho spravuje jako projektovou env proměnnou.

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

Aktuální kapacity a ceny databází ověř před návrhem v platném Netlify plánu;
publisher je nehardcoduje.

## Sdílení DB mezi sites (= compatibility boundary)

`db-share` v této CC integraci záměrně nic nemění a skončí s vysvětlením.
Netlify production secrets jsou write-only, zatímco výchozí CLI čtení používá
dev context; automatické kopírování by mohlo propsat dev databázi do produkce.
Bundled CC konektory čtou connection string z `NETLIFY_DATABASE_URL`. Pokud je
správná hodnota už bezpečně uložená jako CC custom variable, nastav ji na
schváleném cílovém site explicitně přes
`env-set --key NETLIFY_DATABASE_URL --from-variable <CC_PROMENNA>` a pak vytvoř
nový draft deploy. Publisher neumí tuto hodnotu bezpečně získat zpět ze source
site. Mezi samostatnými aplikacemi DB nesdílej.

## Workflow — Env vars (API klíče, secrets)

Aplikace na Netlify používá env vars pro tokeny ke třetím službám (Fakturoid,
Meta, GA4, banka, ...). Publisher má 3 subcommandy pro plnou správu:

```bash
# Set jednu env var z CC variable/SecretRef (hodnota nikdy není v argv)
python3 scripts/netlify_publish.py env-set --site-id <id> \
  --key FAKTUROID_API_KEY --from-variable FAKTUROID_API_KEY --json

# List všech env keys (bez hodnot — security)
python3 scripts/netlify_publish.py env-list --site-id <id> --json

# Smaž env var
python3 scripts/netlify_publish.py env-unset --site-id <id> --key STALE_TOKEN --json
```

## Credential sync (= compatibility boundary)

`sync-creds` v této verzi záměrně nic nemění. Současný CC credential kontrakt
nemá schválené profilové resolvery pro slibované Fakturoid/Meta/Google
Ads/GA4/Fio/Tink mapování; tichý částečný sync by byl nepravdivý. Klíč, který
je už uložený jako CC custom variable, nastav explicitně přes
`env-set --from-variable`. Hodnota zůstane v CC secret store a nepůjde přes
argv. Tato cesta neumí sama exportovat credential uložený pouze v integračním
profilu; v takovém případě skonči s blockerem, nevytvářej duplicitní flat secret.

## Workflow — Identity (built-in auth)

`identity-enable` zůstává jako kompatibilní fail-closed příkaz, ale nic nemění:

```bash
python3 scripts/netlify_publish.py identity-enable --site-id <id> --json
```

Netlify CLI 26.x neumí Identity spolehlivě zapnout. Příkaz proto vrátí
srozumitelnou chybu a odkáže na ruční cestu
Netlify → Site configuration → Identity → Enable Identity. Vibe Builder naopak **vlastní přihlášení generuje** serverovou funkcí (scrypt
hash, podepsaná HttpOnly cookie, kontrola relace na prvním řádku každého
datového endpointu) — postup má v referenci `16-aplikace.md`. Dashboard nad
firemními čísly i aplikace mají přihlášení **vždy**, i když si o něj klient
neřekl. Netlify Identity je samostatná volba pro případ, kdy ji klient
výslovně chce.

## Workflow — Trigger initial refresh po deployi

Po prvním deployi aplikace má prázdnou DB. Aby klient hned viděl data,
spusť jednorázový refresh endpoint:

```bash
python3 scripts/netlify_publish.py trigger-refresh --site-id <id> --endpoint /api/refresh --json
```

Defaultní endpoint je `/api/refresh`. Volá HTTP POST. Pokud aplikace
vyžaduje auth na refresh (např. `CRON_SECRET`), předej pouze název uložené
proměnné: `--token-variable CRON_SECRET`.

Úspěšný příkaz dokládá jen tento jeden refresh. Další refreshe běží pouze tehdy,
když už zvlášť schválená aplikace obsahuje otestovanou Netlify Scheduled
Function a její plán. Plán obnovení (cron v `netlify.toml`) generuje **Vibe Builder** v rámci
schváleného datového kontraktu — bez něj by se data po prvním stažení už
neobnovila. Publisher ho sám nevytváří, jen spustí to první načtení.

## Auto-handoff s vibe-builderem

Když vibe-builder skončí svou práci (vygeneruje projekt), **automaticky**
vyvolává publisher v pořadí:

```
vibe-builder → publisher build
            → publisher ensure-site --dry-run
            → pokud site chybí: klientské schválení + --confirm-create
            → publisher deploy (draft)
```

`db-init`, explicitní `env-set` a `trigger-refresh` nejsou automatická součást
Vibe Builderu. Spusť je jen pro projekt se zvlášť schváleným datovým kontraktem.

Klient nemusí publisher explicit vyvolávat. Default flow:

1. Klient: "Vytvoř vizuální návrh dashboardu nad fakturací"
2. Vibe-builder: generuje statický náhled se zřetelně označenými mock daty
3. Publisher: build + lookup site; nové site vytvoří až po klientově schválení,
   potom provede draft deploy
4. Klient dostane URL v chatu, klikne, prohlédne v browseru
5. Klient: "Posun do produkce" → publisher promote s explicitním `--site-id`,
   `--path`, přesným `--deploy-id` z klientem schváleného náhledu a
   `--confirm-publish yes`
6. Klient: "Připoj doménu dashboard.firma.cz" → publisher add-domain workflow

Skutečná data, konektor, cron a přihlášení dodává Vibe Builder podle
`16-aplikace.md`, ne tenhle auto-handoff. Když ještě schválený datový kontrakt
nemáš, pravdivě nahlas, že náhled běží na ukázkových datech.

## Aplikace: funkce a databáze

**Statický projekt se serverovými funkcemi.** Když projekt obsahuje složku
funkcí (čte se i z `netlify.toml`), deploy je nahraje spolu se stránkami
(`deployMode: static-upload+functions`) a v souhrnu vypíše jejich seznam.
Závislosti se u takového projektu po buildu **nemažou**, protože Netlify
funkce balí až při nasazení. `functions.included_files` je záměrně zakázané:
obchází scan functions složky a může přibalit libovolný projektový soubor.
Lokální pomocné moduly drž vedle funkcí (např. `./_lib.mjs`); publisher
garantuje preflight této složky, ne libovolného import graphu mimo ni.

**Náhled s databází funguje u projektů na `getConnectionString()`** —
Netlify jim pro náhled přidělí izolovanou větev databáze. Publisher je pozná
a žádnou bránu na ně nepouští.

⚠️ **Starší projekty s pevnou proměnnou** (`NETLIFY_DATABASE_URL` /
`NETLIFY_DB_URL`) adresu v náhledu nedostanou — při nahrání hotových souborů
(`--no-build`) ji dostane jen produkce a `/api/*` vrací 502. U nich se deploy
**zastaví** a vyžádá si souhlas klienta s publikací rovnou do produkce.
Souhlas musí padnout od klienta; „pokračuj bez čekání" ho nenahrazuje.

Tohle je kompatibilní cesta pro existující projekty, **ne doporučený postup**.
Nový projekt patří na `getConnectionString()`.

## Bezpečnostní pravidla

- Nepublikuj složku bez `index.html` (pro static) nebo bez `package.json`
  + build output (pro SSR).
- Nepublikuj `.env`, privátní klíče, certifikáty, databáze, `.git`,
  `node_modules`, `.next` cache, dočasné runtime soubory.
- Když build nebo deploy najde blokovaný soubor, zastav se a požádej
  klienta o vyčištění výstupní složky.
- Nepoužívej `functions.included_files` ani lokální relativní importy funkcí
  vedoucí mimo jejich ověřenou složku; publisher je odmítá nebo pro ně
  neposkytuje bezpečnostní garanci.
- Default je draft deploy. Produkce vyžaduje explicitní potvrzení klientem
  a `--confirm-publish yes` u `deploy` i `promote`.
- `promote` vždy dostane přesné `--deploy-id` z téhož draft URL, které klient
  schválil; ověří je proti projektovému state a nikdy nevybírá pouze
  „nejnovější“ deploy.
- U site s custom doménou vyžaduje `deploy`, `promote` i `rollback` navíc
  `--force-prod`.
- Nehádej `site_id`; pokud chybí, použij `ensure-site --dry-run` s
  deterministickým slugem. Create větev spusť až po souhlasu s
  `--confirm-create`.
- `create-site`, create větev `ensure-site` a `delete-site` vyžadují explicit
  flagy (`--confirm-create` / `--confirm-delete`). Skutečný create/ensure
  nesmí být hlášen jako úspěch bez vráceného site ID.
- Ruční `netlify deploy` musí vždy obsahovat explicitní `--site <id>`.
  Bez něj CLI může použít dříve linknutý projekt. Helper `deploy` site id
  vyžaduje a toto pravidlo platí i pro ruční diagnostiku mimo helper.
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
- **DB init na non-existent site** → skončí bez změny; nejdřív explicitně
  spusť `ensure-site`, potom `db-init` s ověřeným site ID a cestou.
- **Promote bez úplné pending dvojice URL + deploy ID** → bez změny produkce;
  nejprve spusť nový draft `deploy` a nech jeho URL schválit.
- **Rollback na neexistující deploy nebo jiný projekt/site** → nic nezapíše;
  dostupné deploye si před výběrem načti přes `list-deploys` a rollback vždy
  spusť s odpovídající `--path`.
- **`npm install` timeout** → návrh: smaž `package-lock.json` a zkus znovu,
  nebo přepni na `npm ci` mode.

## Rychlý test integrace

```bash
python3 scripts/netlify_publish.py test --json
```

Test bez `--site-id` ověří jen Netlify token. Se `--site-id` ověří
přístup ke konkrétnímu site.

## Aktuální limity verze 1.3.4

- Edge Functions deploy (optimalizace, ne nový use case)
- Build cache reuse mezi deployy (optimalizace, klient si nevšimne)
- SSR build-mode deploy je v této verzi ověřený pouze pro Next.js. SvelteKit
  lze sestavit příkazem `build`, ale publish se zastaví před Netlify CLI, dokud
  nebude samostatně ověřený adapter, výstupní strom a stejná credential maska.
- `--ssr` nesmí přepsat framework detekovaný jako static; takové vynucení se
  zastaví před načtením tokenu a před deployem.
- Multi-environment (staging vs production na stejném site)
- Git-based deploy (CliqSales workflow je file-based přes `/documents`)
