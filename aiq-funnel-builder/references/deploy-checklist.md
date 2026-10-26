# Deploy checklist — krok za krokem

Mechanický postup nasazení AIQ funnelu z `funnel-spec.json` (obsahuje i landing `landing.*` a prodejku `sales.*`).
Před začátkem přečti `learned-gotchas.md` — odkazy [G1]–[G18] míří tam.

Konvence: `<SLUG>` = `funnel_slug` ze specu (např. `aiq-vzorovy-funnel`),
`<VSTUP>` = složka od strategy skillu (např. `/documents/lead-magnets/AIQ Vzorový funnel`).

## 0) Preflight

- [ ] Zatím probíhají jen lokální/read-only kontroly. Před prvním vytvořením
      GHL pole, Netlify site nebo Netlify env musí proběhnout společný STOP
      z kroku 5. Souhlas musí pokrýt externí změny, smoke test i placená volání
- [ ] `funnel-spec.json` je validní JSON a `spec_version == "0.5"`
- [ ] Povinné klíče: `funnel_slug`, `questions[]`, `cta_routes` (vč. `_default`),
      `persona_fields` (32 pevných + dynamická), `email_branches`, `ops`, `pilot_mode`, `main_result`,
      `temperature_rules`, `magnet_structure`, `brand`
- [ ] `brand` obsahuje SKUTEČNÉ údaje klienta: `name` (zobrazované jméno),
      `cta_url` (kam vede nákupní CTA), `privacy_email` (správce OÚ),
      `email_footer` (název + adresa do patičky e-mailů). Chybí/zástupné → STOP,
      doplnit se strategy skillem — jinak web a e-maily nemají identitu klienta
- [ ] `pilot_mode.enabled == false` (default, e-maily odcházejí rovnou) — `true` jen na explicitní přání pro interní zkoušku
- [ ] GHL, Netlify a OpenRouter integrace projdou store-first runnerem (hodnoty
      NIKDY nevypisovat). Runner pro každý deploy načte aktuální hodnoty z
      Control Center store a předá je jen krátkodobému child procesu.
      Interní secret-store soubory přímo nečti. Missing/incomplete/conflict =
      STOP před prvním provider requestem [G10]
- [ ] `funnel-spec.json` má `landing.*` (nebo legacy `landing-copy.md`)
- [ ] U existujícího funnelu zkontrolované kontakty s běžící sekvencí:
      nový přesný tvar je `[prefix] - active/processing/completed/converted/hot lead`.
      Najdeš-li staré stavové tagy bez oddělovače ` - ` → STOP; před redeployem
      musí uživatel schválit vyčíslenou jednorázovou migraci. Builder 1.0 dual
      matching neimplementuje; bez migrace může nový guard přestat staré sekvence
      po konverzi zastavovat

## 1) Kopie šablony

```bash
SRC=<baseDir skillu>/template     # šablona je PŘIBALENÁ ve skillu
DST=/documents/sites/<SLUG>
test ! -e "$DST" || { echo "STOP: cílová appka už existuje; použij režim aktualizace."; exit 1; }
mkdir -p "$DST"
cp -a "$SRC/." "$DST/"
rm -f "$DST/funnel-spec.example.json"
```

- [ ] V `$DST` NENÍ `funnel-spec.example.json` (placeholder z template)
- [ ] `package.json` má `"next": "15.5.21"` nebo novější bezpečnou verzi — nepodtékat [G7]
- [ ] `netlify.toml` obsahuje read-only build command
      `node scripts/ensure-fields.mjs --verify`, `@netlify/plugin-nextjs`
      a `node_bundler = "esbuild"` [G6][G8]
- [ ] `.aiq-build.json` vytvořený s `builderSkillVersion: "1.1.4"`,
      `strategySkillVersion: "1.9"`, `status: "preparing"` a
      `completedSteps: ["template"]`; po každém dalším hlavním kroku se pole
      atomicky aktualizuje. Existující manifest nejdřív načti a navazuj

## 2) Vložení specu + úprava identifikátorů

```bash
cp "<VSTUP>/funnel-spec.json" "$DST/funnel-spec.json"
```

- [ ] `components/Quiz.tsx`: ověř, že `STORAGE_KEY` se skládá z `funnel_slug`
      (šablona to dělá ze spec — jen kontrola, nepřepisovat)
- [ ] `lib/spec.ts`: BASE_URL se bere výhradně z env `AIQ_BASE_URL` (krok 4) —
      žádný hardcoded fallback, jen kontrola
- [ ] `package.json`: `"name": "<SLUG>"` (kosmetické, ale drž pořádek)

## 3) Texty

### 3a) Landing (`app/page.tsx`) + kontrola všech user-facing textů

Propiš ze `funnel-spec.json` `landing.*`: hero headline, podnadpis, 3 měřitelné
oblasti, autorita, text tlačítka. (Legacy fallback: chybí-li `landing.*` a existuje
`landing-copy.md`, propiš z něj.) Mockup (pokud dodán) → `public/` + reference v hero.
Needituj logiku, jen texty/JSX obsah.

Identita klienta (titulky stránek, patičky, obálka e-mailů, zásady OÚ, nákupní
CTA) se skládá automaticky ze `spec.brand` — nic dalšího nepřepisuj.

- [ ] Po přepisu: `grep -ri "vzorová firma\|priklad-firmy" app components lib funnel-spec.json`
      nevrací nic (zástupné texty šablony nesmí do produkce)

### 3c) Vizuální assets (detail v SKILL.md krok 3c)

```bash
mkdir -p "$DST/public/img"
cp "<VSTUP>/mockup.png" "$DST/public/img/mockup.png"
# 1) brand assety klienta (pokud vhodné) → public/img/hero.jpg + process.jpg
# 2) Pexels API (exit 2 = chybí PEXELS_API_KEY → další krok):
node <baseDir>/scripts/fetch-images.mjs --query "<EN dotaz na scénu>" --out "$DST/public/img/hero.jpg"
node <baseDir>/scripts/fetch-images.mjs --query "<EN dotaz č. 2>" --out "$DST/public/img/process.jpg"
# 3) browser tool na pexels.com  → 4) image_generate (anti-slop negativy)

# 5) MAGNET 2.0 result fotky — silné produktové vizuály do výsledkové stránky.
#    Zdroj = product-image-generator carousel: /documents/brand/products/<slug>/carousel/
cp /documents/brand/products/<slug>/carousel/01-hero.jpg     "$DST/public/img/result-hero.jpg"
cp /documents/brand/products/<slug>/carousel/05-pred-po.jpg  "$DST/public/img/result-beforeafter.jpg"
cp /documents/brand/products/<slug>/carousel/06-lifestyle.jpg "$DST/public/img/result-product.jpg"  # ČISTÝ záběr bez headline
cp /documents/brand/products/<slug>/carousel/04-detail.jpg   "$DST/public/img/result-detail.jpg"
```

- [ ] `public/img/` obsahuje `hero.jpg` (≥1600 px šířka), `process.jpg`, `mockup.png`
- [ ] `public/img/` obsahuje `result-hero.jpg` / `result-beforeafter.jpg` / `result-product.jpg` (+ `spec.magnet_images` na ně ukazuje) — magnet 2.0 render je rozmístí jako pásy + product reveal. Chybí-li → sloty se přeskočí (funnel jede, jen bez fotek).
- [ ] Fotky sedí k tématu a značce (vizuální kontrola, ne jen název souboru)

### 3d) Design pass (vibe-builder) + anti-slop gate

- [ ] Načtené references vibe-builderu (`/home/node/.openclaw/cs-skills/vibe-builder/references/`)
- [ ] Design doladěn pro klienta na všech 5 stránkách (/, /vysledek, /magnet, /online/, /doporuceni)
      — jen `globals.css` + JSX prezentace, logika nedotčená
- [ ] Anti-slop checklist (29 patternů) prošel bez nálezu — jinak oprav (max 3 kola)

### 3b) Read-only GHL schema plán

U nové i existující appky nejdřív synchronizuj z aktuální skill šablony přesně
tyto bezpečnostní soubory: `scripts/ensure-fields.mjs`,
`scripts/field-plan.mjs` a `netlify.toml` build command s `--verify`. Deploy gate
odmítne starou kopii, která uměla zapisovat během buildu.

Pak spusť canonical runner; výchozí režim dělá pouze GET a lokální plán:

```bash
python3 <baseDir>/scripts/ghl-runner.py fields --app "$DST"
```

`fields-plan.json` zahrnuje target location, všechny otázky, consent,
score/segment, persona a stavová pole, create/reuse diff, typy/options a
`plan_sha256`. Neexistující explicitní `field_id`, typ/options mismatch,
duplicitní název nebo credential conflict = STOP bez zápisu.

- [ ] Provider audit/metody v tomto kroku obsahují jen `GET`
- [ ] Přesný seznam `creates` a target z plánu je součástí společného STOPu
- [ ] SHA je svázaná s current provider stavem; uživatel ji neopisuje ani
      nepotvrzuje zvlášť

## 4) Netlify site + env

Před STOPem pouze read-only zjisti, zda site existuje a komu patří. Následující
create/link/env příkazy spusť až po společném souhlasu z kroku 5.

```bash
cd "$DST"
RUNNER=<baseDir skillu>/scripts/ghl-runner.py
# existuje site?
python3 "$RUNNER" netlify -- api getSite --data '{"site_id":"<SLUG>.netlify.app"}' 2>/dev/null \
  || python3 "$RUNNER" netlify -- sites:create --name "<SLUG>"
python3 "$RUNNER" netlify -- link --name "<SLUG>"

# Env přes zabezpečený dočasný soubor + env:import. Shell tracing musí být
# vypnutý; hodnoty se nesmí objevit v argumentech, chatu ani logu.
set +x
umask 077
DEPLOY_ENV="$(mktemp /tmp/aiq-netlify-env.XXXXXX)"
cleanup_deploy_env() { rm -f "$DEPLOY_ENV"; }
trap cleanup_deploy_env EXIT HUP INT TERM
AIQ_LINK_SECRET="$(openssl rand -hex 32)"
printf '%s=%s\n' \
  AIQ_LINK_SECRET "$AIQ_LINK_SECRET" \
  AIQ_BASE_URL "https://<SLUG>.netlify.app" > "$DEPLOY_ENV"
if [ -n "${AIQ_MAX_LLM_REQUESTS_PER_CONTACT:-}" ]; then
  printf '%s=%s\n' \
    AIQ_MAX_LLM_REQUESTS_PER_CONTACT "$AIQ_MAX_LLM_REQUESTS_PER_CONTACT" \
    >> "$DEPLOY_ENV"
fi
# volitelně (jen async režim / notifikace AI Teamu): AIQ_WEBHOOK_URL + AIQ_WEBHOOK_SECRET
python3 "$RUNNER" netlify -- env:import "$DEPLOY_ENV"
cleanup_deploy_env
trap - EXIT HUP INT TERM
unset AIQ_LINK_SECRET
```

- [ ] Pokud site `<SLUG>` existuje a patří jinému projektu → STOP, zeptej se
- [ ] Hodnoty env nikdy do chatu/logu — jen názvy
- [ ] GHL ani OpenRouter env do site nepřepisuj ručně; potvrzený `deploy.mjs`
      je synchronizuje cíleně přes zabezpečený dočasný soubor ze store-first
      profilu

## 5) Deploy

**🛑 STOP — před jakýmkoli externím zápisem shrň uživateli** URL, GHL location,
počet a názvy nových GHL polí, zda vznikne nová Netlify site, výsledek kontroly
legacy tagů, `pilot_mode` (vypnutý = e-maily rovnou reálným kontaktům) a
OpenRouter náklady: každý dokončený kvíz znamená nejméně dvě modelová volání,
řízené retry mohou počet zvýšit, ale hard cap je výchozích 8 požadavků na
kontakt (konfigurovatelné jen v rozsahu 2–12). Uveď zvolenou službu, varianty
a odhad ceny, pokud je spolehlivě dostupný; jinak řekni, že přesnou cenu předem
nelze určit.
**Čekej na explicitní souhlas.** Jedno potvrzení pokrývá exact field plan,
Netlify změny, deploy, smoke i uvedený metered rozsah; běžný tok nemá druhý dotaz.
Přesné znění v SKILL.md, krok 5. Bez souhlasu nenasazuj.

```bash
python3 <baseDir>/scripts/ghl-runner.py fields \
  --app "$DST" \
  --apply \
  --confirm-plan-sha <PLAN_SHA_Z_FIELDS_PLAN_JSON>

node <baseDir>/scripts/deploy.mjs \
  --confirm-publish yes \
  --confirm-metered yes \
  --legacy-tags <new|clear|migrated>
```

- Potvrzený apply znovu GETne current stav a při jakémkoli driftu odmítne POST.
  Vytvoří jen potvrzené missing fields, udělá readback, atomicky doplní
  `field_id` do specu a `fields-map.json`. Partial failure nechá report; nic
  automaticky nemaže ani neopakuje.
- Po complete apply zkopíruj aktualizovaný `funnel-spec.json` také zpět do
  `<VSTUP>/`; appka a strategie nesmí nést dvě odlišné sady field ID.
- Build command spouští jen `ensure-fields.mjs --verify`: GET + kontrola + mapa,
  nikdy schema POST. Chybějící/mismatched pole build zastaví [G6].
- **NIKDY raw `netlify deploy`, `--no-build` ani netlify-publisher skill** —
  deploy musí projít potvrzovacím wrapperem; bez buildu je rozbitá SSR cesta [G10],
  bez Next runtime pluginu 404 na všech routách [G8].

- [ ] Kroky 3c + 3d hotové PŘED deployem (fotky + design pass + anti-slop gate)
- [ ] Apply log/report: `status=complete`; build log: `read-only verify OK`
- [ ] Deploy zelený, URL `https://<SLUG>.netlify.app` vrací 200 na `/`

## 6) Smoke test

```bash
BASE="https://<SLUG>.netlify.app"

# 1. submit testovacího leada (odpovědi dle questions[] ze specu).
#    E-mail MUSÍ být tvoje VLASTNÍ reálná schránka — pilot je vypnutý, e-mail
#    reálně odejde; vymyšlená adresa na cizí doméně = bounce.
#    Souhlas: OBĚ pole (consent + consentProcessing) musí být true, jinak 400.
curl -s -X POST "$BASE/api/submit" -H 'Content-Type: application/json' -d '{
  "answers": { "q1": "Ano", "q2": "Ano", "...": "…" },
  "contact": { "firstName": "Test", "email": "TVUJ-REALNY@email.cz",
               "consent": true, "consentProcessing": true }
}'
# → 200 { contactId, score, category, temperature, vars }

# 2. kick personalizace
curl -s -X POST "$BASE/api/personalize" -H 'Content-Type: application/json' \
  -d '{"contactId":"<ID>"}'                            # → {"status":"pending"}

# 3. poll (co ~15 s, max ~2 min)
curl -s "$BASE/api/personalize/status?c=<ID>"           # → {"status":"ready"}

# 4. personalizovaná prodejní stránka
curl -s -o /dev/null -w '%{http_code}' "$BASE/online/<ID>"   # → 200

# 5. generické čisté URL (nesmí spadnout)
curl -s -o /dev/null -w '%{http_code}' "$BASE/online"             # → 200
curl -s -o /dev/null -w '%{http_code}' "$BASE/doporuceni"         # → 200
```

Kontrola v GHL (přes API nebo UI):

- [ ] Kontakt existuje, kvízová pole vyplněná (multi jako CSV), skóre + segment +
      temperature zapsané
- [ ] Persona pole „AIQ P - …" vyplněná po `ready`
- [ ] Tagy: `[prefix]` (base — každý lead) + `[prefix] - active` po ready — a `[prefix] - hot lead`, pokud testovací odpovědi daly hot. `[prefix]` = tag prefix funnelu (GHL je ukládá lowercase, např. `aiq - skóre jistoty pitné vody`)
- [ ] Konverzace kontaktu: E0 odeslaný + E1+ viditelné jako **Scheduled**
- [ ] E0 dorazil na e-mail testovacího leada (použij vlastní adresu pro smoke
      test; při zapnutém `pilot_mode` má předmět prefix [PILOT]) a **v patičce
      je odhlašovací odkaz** (vkládá GHL sub-account [G12])
- [ ] Status `pending` po >5 min = personalizace spadla → čti Netlify function log
      `personalize-background` [G4][G5]
- [ ] **Vizuální kontrola browser toolem:** landing + /doporuceni + /vysledek
      (s testovacím leadem) — fotky se zobrazují, texty čitelné, layout drží

Po úspěšném deployi a smoke testu ulož bez tajných hodnot:

```bash
cat > "$DST/.aiq-build.json" <<JSON
{
  "builderSkillVersion": "1.1.4",
  "strategySkillVersion": "1.9",
  "status": "complete",
  "completedSteps": [
    "template",
    "spec",
    "fields-planned",
    "visuals",
    "design",
    "legacy-preflight",
    "approved",
    "deployed",
    "smoke-tested"
  ],
  "deployedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "siteUrl": "https://<SLUG>.netlify.app"
}
JSON
```

## 7) Cron guard (Netlify Scheduled Function — běží automaticky)

Guard `netlify/functions/cron-guard.mts` je **Netlify Scheduled Function** —
Netlify ho spouští **@hourly sám** (rozvrh se registruje při deployi z
`export const config`). Žádné ruční nastavení ani CC Plánovač. V Netlify →
**Functions** se objeví `cron-guard` se štítkem **„Scheduled"**; běhy v
**Logs → Functions**. Per web: každý funnel má svůj cron scoped na svoje
namespacnuté tagy.

Co dělá (vše z GHL search payloadu, žádný per-kontakt GET pro běžící leady):
- `[prefix] - converted` (klient přidá) → zruší zbývající naplánované e-maily,
  sundá `active`, vyprázdní Scheduled IDs pole.
- `[prefix] - active` s prošlým `Sequence End` → přirozený konec → `completed`.

- [ ] Deploy log ukazuje registraci scheduled function; v Netlify Functions je
      `cron-guard` se štítkem „Scheduled".
- [ ] Ověř: přidej testovacímu kontaktu tag `[prefix] - converted` → do hodiny
      (nebo funkci invokni ručně) se naplánované e-maily zruší a `active` zmizí.

**Onboarding klienta (POVINNÉ):** stop follow-upu = **klientův trigger**. Napoj
v GHL automatizaci, která na klientův event (nákup, rezervace…) přidá tag
`[prefix] - converted` — **jinak se sekvence nezastaví.**

## 8) Předání uživateli

```
✅ Váš kvízový funnel je nasazený.

URL: https://<SLUG>.netlify.app

Funnel je rovnou v ostrém provozu — e-maily odcházejí skutečným kontaktům.
Doporučení: projděte si kvíz nanečisto s vlastní adresou, než pustíte návštěvníky.

Automatické zastavení navazujících e-mailů po nákupu/rezervaci je
<zapojené a ověřené | ještě vyžaduje napojení klientské události>.
Volitelné: napojení vlastní domény místo <SLUG>.netlify.app (důvěryhodnost odkazů).
```

Interní zkouška (volitelná, na přání): nastav `pilot_mode.enabled: true`, znovu
získej souhlas s popsaným rozsahem a spusť potvrzovací deploy wrapper z kroku 5.
