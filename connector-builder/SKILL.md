---
name: Connector Builder
description: "Vytváří klientské custom connector skilly pro nové API providery z dodané dokumentace, aby přežily deploy a daly se použít ve vibe-builder dashboardech."
metadata: {"openclaw":{"requires":{"bins":["node","npm","tsx","python3","curl","tar"],"env":["CC_URL","CC_API_KEY"]},"emoji":"🔌"}}
category: vibecoding
status: ready
version: "1.0"
publishedAt: "2026-05-28"
---

# Connector Builder

Navrhuje, implementuje a registruje klientské custom connectory pro externí API.
Výsledek není zápis do deployem přepisované `cs-skills/_lib/connectors`, ale
`user:<provider>-connector` skill uložený v Control Center user skill knihovně.

## Workflow

1. **Ověř kontext** — zjisti providera, účel dashboardu, požadované metriky,
   typ autentizace, zdroj dokumentace a zda klient povoluje live test.
   Pokud chybí API dokumentace nebo ukázková odpověď, zeptej se přes CEO.

2. **Načti dokumentaci** — použij vše, co klient dodal: URL přes `web_fetch`
   nebo browser, PDF/Markdown/JSON soubory z `/documents`, OpenAPI specifikaci,
   ukázkový `curl`, ukázkovou odpověď i poznámky z chatu. Neodhaduj endpoint,
   pokud ho lze ověřit v dokumentaci.

3. **Urči bezpečnostní kontrakt** — connector je defaultně read-only a má dva
   server-side runtime režimy:
   - agent v Control Center čte custom variables a SecretRefs přímo z
     credential storu,
   - deploynutý dashboard čte stejné názvy z Netlify `process.env`.

   Použij dodanou TypeScript šablonu `assets/cc-credentials.ts`. Ta bez cache
   preferuje Control Center store a teprve potom zkouší přímý secret-store
   záznam, `process.env` a legacy runtime `.env`. Díky tomu nová hodnota funguje
   v agent runtime bez restartu a stejný connector package funguje v Netlify.

   Názvy Control Center custom variables nedávej do
   `metadata.openclaw.requires.env` výsledného `SKILL.md`. OpenClaw tento
   požadavek vyhodnocuje jen proti process env ještě před během agenta; takový
   skill by byl `eligible: false` a model by ho neviděl, i když jsou credentials
   správně uložené v Control Center. Do `requires` dej jen skutečné binární
   závislosti, pro tento typ connectoru `{"bins":["node","tsx"]}`. Chybějící
   credential musí `requireCredential()` odmítnout až při konkrétní operaci.

   Nikdy nevkládej token, API key, OAuth secret, session cookie ani ukázkový
   reálný bearer token do `SKILL.md`, kódu, logu, reportu nebo test fixtures.
   Nežádej klienta, aby kvůli tomu posílal token do chatu, nahrával tokenový
   soubor nebo ručně editoval `.env`.

4. **Navrhni datový model** — vyber 1-4 hlavní resources, které dashboard
   opravdu potřebuje. Pro každý resource urč `id`, časové pole, měnu/jednotku,
   pagination cursor, rate limit a minimální normalizované sloupce.

5. **Vytvoř custom skill package** — připrav temp složku se slugem
   `<provider>-connector` a soubory:
   ```text
   <provider>-connector/
   ├── SKILL.md
   ├── package.json
   ├── cc-credentials.ts
   ├── auth.ts
   ├── operations.ts
   ├── refresh.ts
   ├── schema.sql
   ├── docs.md
   └── examples/dashboard-usage.md
   ```
   `package.json` musí exportovat `./auth`, `./operations`, `./refresh` a mít
   package name `@client/<provider>-connector`.

6. **Implementuj connector** — nejdřív zkopíruj kanonickou credential šablonu:
   ```bash
   cp /home/node/.openclaw/cs-skills/connector-builder/assets/cc-credentials.ts \
     /tmp/connector-build/<provider>-connector/cc-credentials.ts
   ```
   `auth.ts` importuje `requireCredential` z `./cc-credentials.js` a načítá
   každou hodnotu uvnitř `loadConfig()`; nesmí číst jen `process.env` ani
   cachovat credentials při importu modulu. Interní importy mohou zachovat
   standardní `.js` specifiery (`./auth.js`, `./operations.js`), protože
   dashboard je řeší bundler a agentní runtime je spouští přes připnutý `tsx`.
   `operations.ts` obsahuje typed read-only API calls s timeoutem/retry,
   `refresh.ts` zapisuje idempotentně do Postgresu, `schema.sql` vytváří cache
   tabulky a pre-aggregated views pro dashboard a `docs.md` shrnuje endpointy,
   env vars a limity.

   Minimální tvar:
   ```typescript
   import { requireCredential } from "./cc-credentials.js";

   export function loadConfig() {
     return {
       apiKey: requireCredential("PROVIDER_API_KEY"),
       apiBase: requireCredential("PROVIDER_API_BASE").replace(/\/$/, ""),
     };
   }
   ```

7. **Přidej vibe-builder usage** — do `examples/dashboard-usage.md` dej přesný
   postup, jak vygenerovaný dashboard připojí custom connector:
   ```bash
   npm pkg set dependencies.@client/<provider>-connector="file:/home/node/.openclaw/user-skills/<provider>-connector"
   ```
   a do Next.js configu:
   ```js
   const nextConfig = { transpilePackages: ['@client/<provider>-connector'] };
   module.exports = nextConfig;
   ```

8. **Validuj lokálně bez secrets** — spusť TypeScript compile nad
   `cc-credentials.ts`, `auth.ts`, `operations.ts`, `refresh.ts` přes skutečný
   `typescript` package. Nikdy nepoužívej holé `npm exec tsc`; v prázdném
   balíčku npm stáhne deprecated package `tsc@2.x`, což není TypeScript
   compiler.
   ```bash
   npm exec --yes \
     --package typescript \
     --package @types/node \
     -- tsc --noEmit --pretty false \
       --target es2022 \
       --module esnext \
       --moduleResolution bundler \
       --lib es2022,dom \
       --types node \
       --skipLibCheck \
       cc-credentials.ts auth.ts operations.ts refresh.ts
   ```
   Credential test dělej proti dočasnému fake Control Center storu a fake env;
   ověř prioritu storu, env fallback a chybu bez vypsání hodnoty. Pokud není
   live token, použij mock/fake API fixture a ověř parsování odpovědí,
   pagination a sanitizaci chyb. Live test spusť jen po výslovném potvrzení.

9. **Registruj přes Control Center API** — zabal složku do `tar.gz` a importuj ji
   jako user skill. Nepiš hotový connector ručně do `cs-skills` ani přímo do
   `workspaces/*/skills`; tyto cesty jsou deploy/runtime materializace.
   ```bash
   cd /tmp/connector-build
   tar -czf /tmp/<provider>-connector.tar.gz <provider>-connector

   curl -s -X POST "$CC_URL/api/local-skills/upload" \
     -H "x-api-key: $CC_API_KEY" \
     -F "file=@/tmp/<provider>-connector.tar.gz"

   curl -s -X POST "$CC_URL/api/local-skills/import" \
     -H "x-api-key: $CC_API_KEY" \
     -H "content-type: application/json" \
     -d '{"temp_id":"<temp_id>","selected":["<provider>-connector"],"category":"vibecoding"}'

   curl -s -X POST "$CC_URL/api/agents/cto/skills" \
     -H "x-api-key: $CC_API_KEY" \
     -H "content-type: application/json" \
     -d '{"skill_id":"user:<provider>-connector"}'
   ```

10. **Ověř runtime dostupnost** — zkontroluj `/api/local-skills` i
    `/api/agents/cto/skills`, že skill má `id: "user:<provider>-connector"`.
    Potom spusť `openclaw skills list --agent cto --json` a ověř pro nový skill
    `eligible: true`, `modelVisible: true` a prázdné `missing.env`. Bez síťového
    volání ověř také, že připnutý `tsx` runtime dokáže importovat `auth.ts`;
    nevypisuj načtené hodnoty:
    ```bash
    tsx --eval '
      import("file:///home/node/.openclaw/user-skills/<provider>-connector/auth.ts")
        .then((module) => console.log(JSON.stringify({
          loadConfig: typeof module.loadConfig === "function"
        })));
    '
    ```
    Teprve potom klientovi vrať stručný report s použitím, env vars a testy.

## Output Template

````markdown
## Custom Connector: <provider>

- Skill ID: `user:<provider>-connector`
- Package: `@client/<provider>-connector`
- Kategorie: `vibecoding`
- Stav: `<ready|blocked>`

### Co umí
- Resource 1: <co čte a kam se ukládá>
- Resource 2: <co čte a kam se ukládá>
- Dashboard views: `<view_1>`, `<view_2>`

### Credentials
- `<ENV_VAR_1>`: <kde ho klient získá a že se nastaví do Netlify env, bez hodnoty>
- `<ENV_VAR_2>`: <kde ho klient získá a že se nastaví do Netlify env, bez hodnoty>

### Použití ve vibe-builder projektu
```bash
npm pkg set dependencies.@client/<provider>-connector="file:/home/node/.openclaw/user-skills/<provider>-connector"
```

### Ověření
- TypeScript compile: <passed|failed>
- Schema sanity: <passed|failed>
- Mock API test: <passed|failed|not needed>
- Live API test: <passed|skipped, proč>

### Další kroky pro klienta
1. Nastavit credentials v Control Center Integrace / custom variables.
2. Nastavit stejné env vars do Netlify přes `netlify-publisher env-set`.
3. Spustit první refresh endpoint ve vygenerovaném dashboardu.
4. Zkontrolovat dashboard views v Netlify DB.
````

## Decision Criteria

| Condition | Threshold | Action |
|-----------|-----------|--------|
| API dokumentace chybí | žádný endpoint ani ukázková odpověď | Zastav a zeptej se na dokumentaci nebo export odpovědi. |
| Auth je write-capable | token umožňuje zápis/mazání | Použij read-only scope/token; write operace do v1 connectoru nedávej. |
| Resource count | více než 4 hlavní resources | Začni 1-4 dashboard-critical resources, zbytek dej do backlogu. |
| Rate limit | méně než 60 requestů/min nebo provider hlásí lockout | Přidej sequential refresh, backoff a minimální cron interval do docs. |
| Live test | chybí explicitní souhlas nebo credentials | Proveď jen mock test; live test označ jako skipped. |

## Anti-patterns

| Don't | Why | Instead |
|-------|-----|---------|
| Nevytvářej klientský connector v `cs-skills/_lib/connectors`. | Deploy provider verze ho přepíše nebo nesynchronizuje všem tenantům správně. | Vytvoř `user:<provider>-connector` přes Control Center API/import. |
| Nevkládej secrets do kódu, fixtures, URL ani shell historie. | Token může leaknout do chatu, logu nebo dokumentů. | Použij CC custom variables pro agent runtime, Netlify env vars pro dashboard runtime a sanitizuj error output. |
| Nečti v `auth.ts` jen `process.env`. | CC custom variables nejsou garantované jako process env, takže agentní běh credential nenajde ani po restartu. | Přibal `cc-credentials.ts` a používej `requireCredential()`. |
| Nedávej názvy CC custom variables do `metadata.openclaw.requires.env`. | OpenClaw skill skryje před modelem ještě předtím, než může resolver přečíst CC store. | V metadata vyžaduj jen skutečné binární závislosti; credential kontroluj v `loadConfig()`. |
| Nespouštěj connector přes holé `node auth.ts` / `node operations.ts`. | Nativní Node nepřemapuje standardní `.js` import specifier na uložený `.ts` zdroj. | Pro agentní běh používej připnutý `tsx`; dashboard dál používá Next bundler. |
| Nežádej klienta o poslání tokenu do chatu nebo upload token souboru kvůli `.env`. | Secret tím projde chatem/dokumenty a musí se považovat za kompromitovaný. | Ať klient uloží hodnotu v Control Center custom variables; agent ji načte helperem. |
| Nevolej provider API z browser komponenty. | Credentials by skončily v klientském bundle. | Volej API jen v SSR/server route/Netlify Function. |
| Nedělej dashboard query přímo proti provider API. | Je to pomalé, rate-limitované a křehké. | Refreshuj do Postgres cache a dashboard čti z SQL views. |
| Nespouštěj `npm exec tsc`. | Npm může stáhnout deprecated balík `tsc@2.x` místo TypeScript compileru. | Použij `npm exec --yes --package typescript --package @types/node -- tsc ...`. |
| Neimportuj archiv a nepředpokládej hotovo bez přiřazení agentovi. | Skill může existovat v knihovně, ale CTO ho neuvidí v runtime. | Po importu vždy přiřaď `user:<slug>` CTO a ověř `/api/agents/cto/skills`. |

## Integration

**Uses:**
- `web_fetch` / browser — načtení API dokumentace z URL.
- `vibe-builder` — dashboard projekt použije výsledný package jako lokální
  dependency.
- `netlify-publisher` — nastaví Netlify env vars, DB a deploy pro dashboard,
  který connector používá.
- `POST /api/local-skills/upload` a `POST /api/local-skills/import` — import
  multi-file custom skillu do user skill knihovny.
- `POST /api/agents/cto/skills` — přiřazení výsledného custom skillu CTO.

**Used by:**
- CTO agent — když klient potřebuje nový API connector, který není součástí
  distribuované connector knihovny.
- `vibe-builder` projekty — když dashboard potřebuje custom data source.

## Quality Checklist

- [ ] Connector je `user:<provider>-connector`, ne provider `_lib` edit.
- [ ] `SKILL.md` výsledného connectoru má `name`, `description`, `category`,
      `status`, `version`, `publishedAt`.
- [ ] `package.json` má name `@client/<provider>-connector`, `type: "module"`
      a exporty pro `auth`, `operations`, `refresh`.
- [ ] Connector obsahuje nezměněnou šablonu `cc-credentials.ts`; agent runtime
      čte CC store a dashboard runtime používá Netlify env fallback.
- [ ] `auth.ts` používá `requireCredential()` uvnitř `loadConfig()` a
      credentials necachuje při importu modulu.
- [ ] `auth.ts` jde importovat přes připnutý `tsx` runtime a výsledný
      `SKILL.md` uvádí `tsx` v `requires.bins`.
- [ ] Výsledný `SKILL.md` nedává CC custom variables do
      `metadata.openclaw.requires.env`.
- [ ] Žádná credential hodnota není v kódu, logu, docs ani fixtures.
- [ ] API calls jsou server-side only, read-only a mají timeout + retry/backoff.
- [ ] `schema.sql` obsahuje cache tabulky, indexy a aspoň 1 dashboard-ready view.
- [ ] TypeScript compile včetně `cc-credentials.ts` proběhl přes
      `npm exec --package typescript -- tsc`, ne přes deprecated
      `npm exec tsc`.
- [ ] Mock nebo live test ověřil parsing odpovědi a refresh path.
- [ ] Skill byl importován přes Control Center a přiřazen CTO jako `user:<slug>`.

## Discovery Questions

1. Jaký provider/API napojujeme a k čemu má dashboard sloužit?
2. Máme URL dokumentace, OpenAPI soubor, PDF, ukázkový `curl` nebo ukázkovou
   JSON odpověď?
3. Jaký auth mechanismus provider používá a umí read-only token/scope?
4. Jaké 3-5 metrik nebo tabulek má dashboard po prvním refreshi ukázat?
5. Smí agent provést live API test, nebo jen mock test bez credentials?

## File Naming Convention

- Výsledný custom skill slug: `<provider>-connector`
- Package name: `@client/<provider>-connector`
- Runtime source: `~/.openclaw/user-skills/<provider>-connector/`
- CTO materializace: `~/.openclaw/workspaces/cto/skills/<provider>-connector/`
- Dashboard dependency:
  `file:/home/node/.openclaw/user-skills/<provider>-connector`
