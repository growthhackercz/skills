---
name: aiq-funnel-builder
description: Postaví a po výslovném schválení spustí hotový AIQ kvízový funnel podle schválené strategie — web s kvízem, personalizovaný výsledek, prodejní stránku, propojení s CRM i automatické e-maily. Před předáním ověří celý průchod a umí také upravit jen landing, vyhodnocení, prodejní stránku nebo follow-up.
category: sales
status: ready
version: "1.1.4"
publishedAt: "2026-10-02"
metadata: {"openclaw":{"emoji":"🏗️","requires":{"bins":["node","npm","netlify","openssl","curl","python3"]},"optionalEnv":["PEXELS_API_KEY"]}}
---

# AIQ Funnel Builder 1.1.4

Runner načítá společný credential resolver z runtime katalogu `cs-skills/_lib`
i při spuštění z přiřazené nebo uživatelské kopie skillu. Nekopíruj `_lib` do
adresáře se skilly agenta; pravidla profilů a schvalování GHL změn se nemění.

**Deterministický vykonavač** strojového kontraktu `funnel-spec.json`. Nezná
kreativu — všechna rozhodnutí (otázky, skórování, segmenty, texty, větve) udělal
`aiq-strategy-generator` 1.9 a schválil je uživatel ve 4 STOP bodech. Tento skill
je mechanicky vykoná: šablona → spec → GHL pole přes API → Netlify deploy →
ověřovací test.

**Design NENÍ v tomto skillu zduplikovaný — čte se ze skillu `vibe-builder`**
(jediný zdroj design pravdy: foundation, composition, themes, anti-slop,
images, copywriting). Reference vibe-builderu čti z
`/home/node/.openclaw/cs-skills/vibe-builder/references/` (na fleet VPS vždy
existuje). Pokud vibe-builder chybí, použij zabudovaný prémiový základ šablony
a v závěrečné zprávě na to upozorni.

Známé limity (žádný template registr; guard běží automaticky jako Netlify Scheduled Function)
jsou na konci dokumentu.

## Režimy — celý funnel, nebo jen jedna vrstva

Builder má 5 vstupních režimů. Uživatel navenek pracuje s vrstvami funnelu
(landing / vyhodnocení / prodejní stránka / follow-up), technicky vše žije
v jedné appce a jednom specu — proto úprava vrstvy vždy končí redeployem téže
Netlify site.

| Režim (co uživatel řekne) | Co se dělá | Kroky |
|---|---|---|
| „postav celý funnel" | kompletní build + deploy | 1–7 |
| „uprav landing / kvíz" | texty `app/page.tsx` ze specu `landing.*`, otázky ze specu, vizuály | 2, 3a, 3c, 3d, 5, 6 (zkrácený) |
| „uprav vyhodnocení / magnet" | `/vysledek` + `/magnet` — texty `main_result.meaning`, magnet_structure, design | 2, 3d, 5, 6 (zkrácený) |
| „uprav prodejní stránku" | `/online/` + `/doporuceni` — cta_routes, offer texty, design, vizuály | 2, 3c, 3d, 5, 6 (zkrácený) |
| „uprav follow-up" | `email_branches` ve specu (větve, dny, cíle) + redeploy | 2, 5 |

Pravidla pro dílčí režimy: vždy pracuj nad AKTUÁLNÍ nasazenou appkou
(`/documents/sites/<funnel_slug>/`), needituj logiku, po změně vždy krok 5
(deploy se STOP potvrzením) a zkrácený smoke test (dotčené stránky vrací 200
a obsahují nové texty). Follow-up změny se projeví jen u NOVÝCH leadů.

## Vstup

Složka z aiq-strategy-generator 1.9, typicky `/documents/lead-magnets/AIQ [Quiz title]/`:

- `funnel-spec.json` — strojový kontrakt v0.5 (POVINNÝ; `spec_version` musí být `"0.5"`). **Obsahuje i landing copy (`landing.*`) a copy prodejní stránky (`sales.*`)** — builder je čte odtud.
- `mockup.png` — vizuál pro hero (volitelný)
- ~~`landing-copy.md`~~ — **ZRUŠENO od 2026-07-23** (relikt AI Studio 1.4). Landing copy je nově v `funnel-spec.json` `landing.*`. **Legacy fallback:** chybí-li `landing.*` a existuje `landing-copy.md`, builder ho ještě přečte (starší funnely se nerozbijí); u nových funnelů `landing-copy.md` NEočekávej.

Pokud `spec_version` neodpovídá nebo chybí povinné klíče (questions, scoring_bands
u score/audit, cta_routes, persona_fields, email_branches, ops, pilot_mode,
**brand** — name + cta_url + privacy_email + email_footer) →
**STOP a vrať uživatele na strategy skill**. Nic nedomýšlej. Bez `brand` bloku
by web i e-maily neměly identitu klienta (patičky, správce OÚ, cíl nákupního CTA).

**Chybějící `mechanisms` = ptej se, nedomýšlej.** Bez tohoto bloku se sekce 4
prodejní stránky („Proč to bude fungovat u vás") **skryje** — obsah produktu do
šablony nepatří (G17) a nouzové karty z `offer.usp` jsou jen holé nadpisy. Starší
specy (před tímto blokem) tím tichou ztrátu sekce neohlásí, proto to řekni nahlas:

> *„V podkladech chybí vysvětlení, proč řešení funguje, takže tato část
> prodejní stránky nebude úplná. Chcete ji nejdřív doplnit do strategie, nebo
> mám pokračovat bez ní?"*

Mechanismy **nikdy nepiš sám v builderu** — patří do specu, jinak se při další
generaci ztratí.

### Povinný preflight při aktualizaci existujícího funnelu

Před každým redeployem zjisti, zda už funnel obsluhuje kontakty s běžícími
sekvencemi. Nová konvence stavových tagů používá přesný lowercase tvar
`[prefix] - active/processing/completed/converted/hot lead`. Starší nasazení
mohou mít stavové tagy bez oddělovače ` - `.

Pokud v GHL existují kontakty se starými stavovými tagy, **STOP**. Novou verzi
nenasazuj, dokud uživatel výslovně neschválí jednorázový převod starých tagů na
nový tvar a kontrolu počtu změněných kontaktů. Builder 1.1.4 dual matching
neimplementuje.

Bez tohoto kroku by nový guard staré běžící sekvence nenašel a nemusel by je
zastavit po konverzi. Migrace smí měnit jen tagy tohoto konkrétního funnelu,
musí mít předem vyčíslený dopad a po provedení kontrolní report.

## Co vznikne

```
/documents/sites/<funnel_slug>/     ← Next.js 15 app (kopie ověřené šablony)
Netlify site <funnel_slug>          ← https://<funnel_slug>.netlify.app
GHL custom pole                     ← kvízová + consent + score/segment + persona + stavová pole
fields-plan.json                    ← read-only přesný plán GHL schema + SHA-256
fields-map.json                     ← vytvoří apply; build ji read-only ověří a obnoví
```

Routy appky: `/` (landing + kvíz) · `/api/submit` · `/api/personalize` (+ `/status`)
· `/vysledek` · `/magnet/[contactId]` · `/online/[contactId]` · `/doporuceni` (fallback)
· `/zasady` + background funkce `netlify/functions/personalize-background.mts`.
Veřejné placené endpointy chrání Netlify Edge rate limit
(`netlify/edge-functions/paid-api-guard.ts`); `/api/personalize` navíc přijme jen
kontakt s base tagem právě tohoto funnelu.

## Workflow

Detailní krok-za-krokem postup s přesnými příkazy: `{baseDir}/references/deploy-checklist.md`.

**Dlouhý běh musí navazovat.** Na začátku načti
`/documents/sites/<funnel_slug>/.aiq-build.json`, pokud existuje. Novou práci
zahaj stavem `preparing` a po každém hlavním kroku atomicky aktualizuj
`completedSteps` (`template`, `spec`, `fields-planned`, `visuals`, `design`,
`legacy-preflight`, `approved`, `deployed`, `smoke-tested`). Po přerušení
pokračuj prvním chybějícím krokem; negeneruj znovu hotové obrázky a nezakládej
novou site. Stav `deployed` zapiš až po úspěšné odpovědi Netlify a
`smoke-tested` až po celém ověřovacím průchodu.

**Žádný externí zápis před potvrzením.** Lokální přípravu, validaci a náhled
udělej bez GHL/Netlify mutací. Než vytvoříš GHL pole, Netlify site nebo env,
spusť společný STOP z kroku 5 a čekej na explicitní souhlas. Tento souhlas
pokrývá přesně popsané GHL změny, Netlify deploy, jeden smoke test a uvedený
rozsah placených volání; při změně rozsahu se zeptej znovu.

GHL, Netlify a OpenRouter přihlašovací údaje pro produkční deploy načítej
výhradně přes `{baseDir}/scripts/ghl-runner.py`. Runner používá společný
store-first resolver, podporuje i shodný legacy `.env` fallback a aktuální
hodnoty předá jen konkrétnímu child procesu. Rotace tokenu proto nevyžaduje
restart dlouho běžící agentí session. Nikdy nečti secret-store přímo,
nepředávej token v argv a nevypisuj hodnoty proměnných. Chybějící, neúplný nebo
konfliktní profil musí skončit před prvním provider requestem.

**Prémiová prodejní stránka (21 bloků):**
- Anatomie + fallbacky + **design pravidla** (max 2 texty → vizuál, ikony všude, vlastní obrázky ne z landingu, celý wireframe): `../aiq-strategy-generator/references/sales-page-blueprint.md`.
- **Obrázky** — dvě sady: **(a) produktový carousel** = artefakt produktové složky `/documents/brand/products/<slug>/carousel/` (`product-image-generator`, snímek 01→hero), **generuj JEN když tam ještě není a VŽDY PŘED stavbou LP; LP ho jen spotřebuje** (zkopíruje do `public/img/`). **(b) lifestyle sada** (6 ks, 4:3 horizontal, center-weighted, PNG→JPG) přes `brand-image-generator`, per‑stránka rovnou do `public/img/`. Engine = **VŽDY nativní tool `image_generate`** (GPT image 2, backend OpenClaw, billing přes Control Center), reference produktu přes parametr `images[]` (runtime cesty `/home/node/documents/...`). 🚫 NIKDY Freepik/Magnific ani jiný externí generátor (ve všech skillech). Self-host `public/img/`, nikdy cross-origin/landing. Pořadí + pipeline: `{baseDir}/references/IMAGES.md`.
- **Render:** `app/online/[contactId]/page.tsx` vykresluje personalizovanou i generickou variantu; čisté `/online` a `/doporuceni` používají stejný generický fallback. Samostatný `GenericSales` už neexistuje. `sp-` třídy žijí v `app/globals.css`. Nové bloky čtou z `spec.sales.*` (autoritní čísla, bonusy, proof, srovnání, stroj času, den, carousel, hero_image…), gated `(spec as unknown as {sales?}).sales` → chybí data → blok se skryje. `safeImg()` sanitizuje obrázky na `/img/`. Design VŽDY matchuj landing (`app/page.tsx`): tokeny navy `#1b2a4a`/blue `#006799`/gold `#c5a55a`, fonty `--font-head-stack`/`--font-body-stack`, komponenty hero-media/bento/btn-gold/quote-band — NIKDY nevymýšlej nový aesthetic.
**Před začátkem si POVINNĚ přečti `{baseDir}/references/learned-gotchas.md`** — 18
produkčně ověřených pastí; každá z nich už jednou stála hodiny debugování.

### 1) Kopie šablony

**Šablona je PŘIBALENÁ ve skillu: `{baseDir}/template/`** — nezávisí na žádném
existujícím funnelu ve workspace. Zkopíruj ji do `/documents/sites/<funnel_slug>/`
— **VYNECH**: `funnel-spec.example.json` (jen referenční ukázka, NIKDY
nedeployovat). Vždy stav z přibalené šablony — nikdy
z jiného funnelu ve workspace (riziko přenosu textů cizího klienta).

### 2) Vložení nového funnel-spec.json

Zkopíruj `funnel-spec.json` ze vstupní složky do rootu nové appky. Šablona z něj
čte všechno (otázky, skórování, segmenty, cta_routes, texty výsledků, ops tagy).

### 3) Úprava textů + identifikátorů

- **`app/page.tsx`** — texty landing page čti z **`funnel-spec.json` `landing.*`**
  (headline, podnadpis, 3 oblasti, autorita, výzvy k akci, patička). Šablona je čte
  ze specu, žádný samostatný soubor. **Legacy:** existuje-li `landing-copy.md` a `landing.*`
  chybí, propiš z něj (starší funnely). Jen texty, žádné zásahy do logiky.
- **Identita klienta** (patičky, e-maily, zásady OÚ, cíl nákupního CTA) se bere
  automaticky ze `spec.brand` — nic nepřepisuj v kódu, jen ověř, že `brand`
  obsahuje skutečné údaje klienta (název, web, kontaktní e-mail, adresa).
- **`components/Quiz.tsx`** — ověř, že `STORAGE_KEY` obsahuje `funnel_slug`
  (šablona ho skládá ze spec; kolize klíče mezi funnely = rozbité „pokračujte,
  kde jste skončili").
- Design tokens bere šablona z `funnel-spec.design_tokens` — CSS neupravuj, pokud
  strategy nedodala vlastní požadavky.
- **Kontrola zbytků šablony (povinná):** po přepisu textů spusť
  `grep -ri "vzorová firma\|priklad-firmy" app components lib funnel-spec.json`
  v rootu appky — nesmí nic vrátit. Zástupné texty šablony nesmí do produkce.

### 3c) Vizuální assets (povinné — stránka bez fotek nejde do produkce)

Šablona čeká v `public/img/`: **`hero.jpg`** (na šířku, ≥1600 px — podklad
hero landing i prodejní stránky), **`process.jpg`** (na šířku, sekce „Jak to
probíhá"), **`mockup.png`** (vizuál lead magnetu ze strategie — zkopíruj
z `<VSTUP>/mockup.png`) a **`hero-video.mp4`** (DOPORUČENÉ — video pozadí
hero, mp4 1280–1920 px, klidná smyčková scéna; poster je hero.jpg, takže
chybějící video nic nerozbije). Chybějící soubor = tonální gradient, ale plná
vizuální kvalita vyžaduje fotky + video.

**Poměr stran mockupu (povinné):** zjisti reálné rozměry
(`node {baseDir}/scripts/fetch-images.mjs --probe public/img/mockup.png`)
a nastav je jako inline `style={{aspectRatio: "W / H"}}` na `.hero-mock`
v `app/page.tsx` — jinak `cover` ořízne obsah mockupu (např. čtvercový
mockup v kartě 4:5 přijde o okraje).

**Mockup nesmí mít zapečené okraje:** pokud má PNG kolem obsahu bílý/šedý
rám, ořízni ho (`magick mockup.png -fuzz 6% -trim +repage mockup.png`;
bez ImageMagick požádej o oříznutý mockup) a znovu spusť `--probe` na
aktuální poměr stran.

**Mockup je POVINNÝ viditelný prvek landing hero (scent match s reklamou).**
Vizuál lead magnetu se používá i v reklamách — návštěvník, který klikne na
reklamu s mockupem, musí TENTÝŽ vizuál okamžitě vidět na landingu (kontinuita
= důvěra). Mockup kartu z hero NIKDY neodstraňuj ani nezmenšuj pod
rozpoznatelnost; ve vizuální smyčce ověř, že je celý viditelný nad foldem
(desktop i mobil) a se správným poměrem stran.

**Obrazová dramaturgie podle fáze funnelu (důležité pochopit):**

- **Landing (`/`) je vršek funnelu** — návštěvník náš produkt ještě
  nezvažuje; kvíz funguje na ZVĚDAVOST („chci zjistit, jak na tom jsem").
  Produktová fotka tady působí prodejně a zvědavost zabíjí. **Default pro
  landing = lifestyle / situace cílovky / vytoužený výsledek** (scéna ze
  života, ne produkt). Pokud výjimečně usoudíš, že produktovka na landing
  dává smysl (např. ikonický produkt, který sám budí zvědavost), **poraď se
  s uživatelem**; v autonomním běhu default dodrž a úvahu uveď v reportu.
- **Prodejní stránka (`/online/`, `/doporuceni`) = zvažování** — tady produktové
  fotky PATŘÍ (brand assety produktu přednostně).

Vyhledávací dotazy: vezmi `spec.visuals.hero_query` / `process_query`
(pokud strategie dodala), jinak je odvoď ze SITUACE a výsledku cílovky —
**anglicky, konkrétní scéna ze života** (např. „family drinking water
kitchen morning light", ne „water filter device"). Styl: editorial
fotografie, žádní lidé hledící do kamery.

Zdroje v tomto pořadí (fallback řetěz):

1. **Brand assety klienta** — `/documents/brand/products/<slug>/images/` a
   `/documents/brand/images/`: na šířku, ≥1600 px. Pro LANDING jen
   lifestylové záběry (produktové fotky patří na prodejní stránku — viz
   dramaturgie výše); pro prodejní stránku produktové přednostně.
2. **Pexels API** — fotky: `node {baseDir}/scripts/fetch-images.mjs
   --query "…" --out public/img/hero.jpg`; video: přidej `--type video
   --out public/img/hero-video.mp4` (klíč z env `PEXELS_API_KEY`, nastavuje
   se v CC Nastavení → Integrace; exit 2 = klíč chybí → další krok).
3. **Web browser tool** — fotky: `https://www.pexels.com/search/<query>/`;
   videa: `https://www.pexels.com/search/videos/<query>/` (licence Pexels =
   volné komerční užití). ⚠️ **Browser soubory NEstahuje** — v browseru jen
   najdi přímou URL (fotky: `images.pexels.com/...`, videa:
   `videos.pexels.com/video-files/<id>/<id>-hd_1280_720_*.mp4` nebo
   `-hd_1920_1080_*`; jsou v DOM jako `src` elementů) a stáhni ji přes
   node fetch / curl do `public/img/`.
4. **`image_generate`** — editorial prompt + barvy z design_tokens +
   anti-slop negativy (žádné purple gradienty, glow, watermarky, lidé do
   kamery; viz vibe-builder `references/07-images.md` a `04-anti-slop.md`).
   Video tímto krokem nevzniká — bez videa zůstává foto (poster), to je OK.

Po stažení zkontroluj, že se fotka hodí k tématu a značce (vizuálně, ne jen
podle názvu). Nepoužitelná → další zdroj v řetězu.

### 3d) Design pass — pravidla z vibe-builderu (povinné)

Načti references skillu **vibe-builder** (`01-foundation.md`,
`02-composition.md`, `03-themes-and-dials.md`, `04-anti-slop.md`,
`08-copywriting.md`) a aplikuj je na **všech 5 stránek funnelu**:
landing `/` · `/vysledek` · `/magnet` · `/online/` · `/doporuceni`.

- Šablona má prémiový základ (vrstva „PREMIUM LAYER" v `app/globals.css`) —
  design pass ho **ladí na míru klientovi**: barvy/typografie dle
  `design_tokens`, případné úpravy kompozice dle brand DNA a tématu.
- **DESIGN.md klienta má přednost:** pokud existuje
  `/documents/brand/DESIGN.md`, načti ho a použij jeho tokeny (barvy vč.
  akcentů, typografickou škálu, radiusy) — je bohatší a závaznější než
  `design_tokens` ve specu. Rozpory řeš ve prospěch DESIGN.md.
- Edituj VÝHRADNĚ prezentační vrstvu: `app/globals.css` + JSX texty/struktura
  sekcí. **NIKDY logiku** (`lib/`, `app/api/`, `netlify/`, stavové části
  `Quiz.tsx`).
- **Kompozici NEměníš** — layout (hero + stats pás + bento + quote blok +
  kroky + CTA panel) je autorský a zapečený v šabloně. Design pass ladí
  barvy, typografii, texty a assety — ne strukturu sekcí.
- **Vizuální smyčka (povinná):** po lokálním buildu / deployi otevři stránku
  browser toolem, udělej screenshot NAHOŘE i DOLE a POROVNEJ S OKEM
  designéra: čitelnost textu na podkladu, ořezané obrázky, prázdné sloty,
  slité barvy, rozbité odsazení. Najdeš-li problém → oprav → nový
  screenshot. Max 2 kola, pak stav popiš uživateli. Screenshot až PO
  vykreslení (počkej na obrázky), ne během načítání.
- **Anti-slop gate:** před krokem 5 projdi checklist vibe-builderu
  (29 patternů — purple gradienty, side-stripe karty, nested cards, generic
  copy…). Nález = oprav; max 3 kola, pak stav ohlas uživateli. Se slop
  nálezem NIKDY nedeployuj.

### 3e) Read-only plán GHL schema

Po dokončení lokální appky, ale ještě před společným STOPem, synchronizuj do
existující appky bezpečné runtime soubory z aktuální šablony (`scripts/ensure-fields.mjs`,
`scripts/field-plan.mjs` a read-only `--verify` build command v `netlify.toml`).
Pak automaticky spusť:

```bash
python3 {baseDir}/scripts/ghl-runner.py fields --app /documents/sites/<funnel_slug>
```

Výchozí režim provede pouze `GET customFields`, vytvoří `fields-plan.json` s
přesným targetem, seznamem create/reuse/mismatch a SHA-256. Nic v GHL ani ve
specu nemění. Plán zahrnuje otázky, consent, score/segment, persona i stavová
pole. Existující `field_id` se ověřují podle ID; neexistující reference,
nekompatibilní typ, chybějící options nebo duplicitní jméno jsou STOP.

Konkrétní diff z plánu zahrň do už existujícího jednoho potvrzení v kroku 5.
Uživatel hash neopisuje a nepotvrzuje podruhé.

### 4) Netlify site + env

Zajisti site `<funnel_slug>` (existuje → použij, neexistuje → vytvoř) a nastav env:

| Proměnná | Hodnota |
|---|---|
| `GHL_API_KEY` | synchronizuje deploy wrapper cíleně ze zvoleného CC GHL profilu; NIKDY nevypisovat |
| `GHL_LOCATION_ID` | synchronizuje deploy wrapper; musí přesně odpovídat funnel-specu |
| `OPENROUTER_API_KEY` | klientův klíč (sync personalizace; NIKDY nevypisovat) |
| `OPENROUTER_MODEL` | *NEnastavuj* — šablona má vlastní 3-modelový řetěz (gpt-mini → Sonnet → gpt-latest). Haiku je vyřazený (kapacitní chyby). Env jen pro vědomý override. |
| `AIQ_MAX_LLM_REQUESTS_PER_CONTACT` | volitelné; hard cap 2–12, výchozí 8. Nezvyšuj bez nového souhlasu s dopadem na náklady. |
| `AIQ_LINK_SECRET` | vygeneruj náhodných 64 hex znaků (`openssl rand -hex 32`) |
| `AIQ_BASE_URL` | `https://<funnel_slug>.netlify.app` |
| `AIQ_WEBHOOK_URL` + `AIQ_WEBHOOK_SECRET` | volitelné — jen async režim (AI Team webhook) |

### 5) Deploy

**🛑 STOP — potvrzení před nasazením do ostrého provozu.** Před spuštěním
deploye shrň uživateli a čekej na explicitní souhlas:

> Nasazuji funnel **[název]** na `[veřejná URL]`,
> propojený s vaším CRM účtem. Pilotní režim je **vypnutý**: každému, kdo kvíz
> vyplní, rovnou odejde potvrzovací e-mail a naplánuje se série 3–5 e-mailů.
> Ověřovací průchod a každý další dokončený kvíz spouští nejméně dva placené
> požadavky na personalizaci. Při dočasné chybě nebo neúplném výstupu se mohou
> kontrolovaně zopakovat, nejvýše však osm požadavků na jeden kontakt. Použije
> se `[uveď zvolenou službu a varianty]`;
> přesnou cenu uveď, pokud ji lze spolehlivě zjistit, jinak výslovně řekni, že
> není předem známá.
> Mám nasadit?

Bez souhlasu nenasazuj. Po souhlasu nejdřív interně proveď přesně schválený
field plan a teprve potom deploy. `<PLAN_SHA>` načti z `fields-plan.json`; není
to další uživatelský krok:

```bash
python3 <baseDir>/scripts/ghl-runner.py fields \
  --app /documents/sites/<funnel_slug> \
  --apply \
  --confirm-plan-sha <PLAN_SHA>

node <baseDir>/scripts/deploy.mjs \
  --confirm-publish yes \
  --confirm-metered yes \
  --legacy-tags <new|clear|migrated>
```

Raw `netlify deploy --prod` nepoužívej. Potvrzovací flagy nastav jen v běhu,
který zpracovává právě udělený souhlas; starší souhlas nerecykluj pro změněný
rozsah.

Před STOP potvrzením musí být hotové kroky 3c (vizuály) a 3d (design pass
včetně anti-slop gate) — nedeployuj „basic" verzi s tím, že design doladíš pak.

Build command v `netlify.toml`
(`node scripts/ensure-fields.mjs --verify && npm ci && next build`) je striktně
read-only: znovu načte schema, odmítne drift/missing/mismatch a obnoví
`fields-map.json`, ale nikdy neposílá `POST`. GHL pole a `field_id` ve specu smí
vytvořit/doplnit pouze výše uvedený potvrzený apply.

### 6) Ověřovací test (smoke test) — povinný, bez něj žádné předání

1. `POST /api/submit` s testovacím leadem (testovací e-mail!) → 200 + `contactId`,
   `score`, `temperature`
2. Kick `POST /api/personalize` `{contactId}` → `{status:"pending"}`
3. Poll `GET /api/personalize/status?c=<id>` → do ~2 min `{"status":"ready"}`
4. `GET /online/<contactId>` → 200, personalizovaný obsah
5. `GET /online` a `GET /doporuceni` → 200, generický obsah
6. V GHL ověř: kontakt má kvízová pole + persona pole + tagy (`[prefix]` base +
   `[prefix] - active` po ready; GHL je lowercasuje) + naplánované e-maily
   viditelné v konverzaci + E0 doručený na testovací adresu

7. **Vizuální kontrola (povinná):** otevři nasazený web browser toolem
   (landing + /doporuceni + /vysledek s testovacím leadem), udělej screenshot
   a zkontroluj: fotky se zobrazují (žádné prázdné gradient sloty tam, kde
   měly být fotky), texty čitelné na podkladu, žádný rozbitý layout.

Cokoli selže → oprav dle `{baseDir}/references/learned-gotchas.md`, NEPŘEDÁVEJ
rozbitý funnel.

Po úspěšném deployi a smoke testu ulož do appky
`/documents/sites/<funnel_slug>/.aiq-build.json` bez tajných hodnot:

```json
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
  "deployedAt": "<ISO timestamp>",
  "siteUrl": "https://<funnel_slug>.netlify.app"
}
```

### 7) Guard — hlídač zastavení sekvencí

Naplánované e-maily hlídá **Netlify Scheduled Function** `template/netlify/functions/cron-guard.mts`
(jádro `template/lib/guard-core.ts`), která běží **@hourly automaticky** — registruje se
při deployi, není třeba nic nastavovat (žádný externí plánovač). Nad namespacnutými
tagy funnelu (`[prefix] - …`, GHL je ukládá lowercase) dělá:
- **Stop-on-purchase:** kontakt s tagem `[prefix] - converted` (klient ho přidá svou
  GHL automatizací na nákup/rezervaci) → zruší zbývající naplánované e-maily, sundá
  `[prefix] - active`, vyprázdní Scheduled IDs pole.
- **Přirozený konec:** `[prefix] - active` s prošlým `Sequence End` → `[prefix] - completed`.

**Onboarding klienta (POVINNÉ):** stop follow-upu = klientův trigger — napoj v GHL
automatizaci, která na klientův event přidá tag `[prefix] - converted`, jinak se
sekvence nezastaví.

## Bezpečnost (závazná pravidla)

1. **`pilot_mode` je default VYPNUTÝ (`enabled: false`) — e-maily odcházejí
   rovnou skutečným kontaktům.** Volitelně lze zapnout `enabled: true` pro
   interní zkoušku (předměty dostanou prefix [PILOT]); zapnutí/vypnutí =
   editace funnel-spec.json + redeploy
   po úspěšném pilotním průchodu.
2. **Tokeny a klíče nikdy do logů, promptů ani chatu** — GHL klíč jen přes
   store-first runner a cílený child env; OPENROUTER_API_KEY a
   NETLIFY_AUTH_TOKEN runner načte čerstvě z Control Center store a předá jen
   deploy child procesu; AIQ_LINK_SECRET patří jen do cílového server env. Do
   chatu smí jen NÁZVY proměnných.
3. **Testovací leady jen s testovacími e-mailovými adresami** — nikdy reálná
   adresa třetí osoby.
4. **GHL operace jsou additivní** — skill vytváří pole/tagy/kontakty, nikdy nic
   nemaže ani hromadně nepřepisuje. Jediné mazání: cancel scheduled e-mailů
   (cron-guard), a to jen nad vlastními AIQ message IDs.
5. **Žádné destruktivní zásahy do existujících Netlify sites** — deploy jen do
   site `<funnel_slug>`; pokud site s tímto názvem existuje a NENÍ to tento funnel,
   STOP a zeptej se.
6. **Žádný redeploy přes staré stavové tagy** — nejdřív preflight a explicitně
   schválená migrace.
7. **Žádné skryté placené operace** — před hromadnou tvorbou obrázků i live
   deployem sděl rozsah a dostupný odhad nákladů a čekej na explicitní souhlas.

## Reference

- `{baseDir}/references/deploy-checklist.md` — kompletní krok-za-krokem checklist s příkazy
- `{baseDir}/references/learned-gotchas.md` — 18 produkčně ověřených pastí (POVINNÉ čtení)
- `{baseDir}/scripts/ghl-runner.py` — store-first credential gate a úzký fields/deploy launcher
- `{baseDir}/scripts/deploy.mjs` — produkční deploy gate; bez tří potvrzených preflightů odmítne běžet
- `{baseDir}/template/scripts/ensure-fields.mjs` — canonical plan/apply/verify GHL schema; Netlify build smí jen `--verify`
- `{baseDir}/template/netlify/functions/cron-guard.mts` (+ `template/lib/guard-core.ts`) — stop-on-purchase (`[prefix] - converted`) + přirozený konec sekvencí; Netlify Scheduled Function @hourly
- `{baseDir}/scripts/fetch-images.mjs` — Pexels API stahování fotek (env `PEXELS_API_KEY`)
- **Závislost:** skill `vibe-builder` (design references) — `/home/node/.openclaw/cs-skills/vibe-builder/references/`

## Známé limity 1.1.1

- **Žádné behaviorální větvení** (otevřel/klikl → jiná cesta) — jen větve dle teploty.
- **Žádný template registr / mass-rebuild** — update šablony = ruční rebuild per funnel.
- **Guard běží automaticky** jako Netlify Scheduled Function (@hourly, registruje se při deployi) — žádné ruční nastavení. Stop-on-purchase spouští klient tagem `[prefix] - converted`.
- **Výchozí doména je `<funnel_slug>.netlify.app`** — napojení vlastní domény
  klienta je volitelný ruční krok (Netlify custom domain + DNS u klienta);
  doporuč ho uživateli pro důvěryhodnost odkazů v e-mailech.
- Jedna GHL location per funnel; multi-funnel souběh jednoho kontaktu = edge case
  (pravidlo: nový běh kvízu ukončuje starou sekvenci).
- **`main_result` render: plně `score` (gauge) a `plan` (text box).** Varianty
  `calc` (`type: number`) a `blueprint` (`type: opportunities`) šablona zatím
  vykreslí jako skóre-gauge — číslo kalkulačky by ukázalo kvízové skóre 0–100.
  Dokud render nepřibude, **strategie tyhle varianty nenabízí jako hotové**;
  drž se `score` / `audit` / `plan`.
- **`contact_position: "start"` (high-ticket, kontakt na začátku) šablona nečte** —
  kontakt je vždy poslední krok. High-ticket režim nenabízej ani negeneruj.
- **Bolestivá otázka pro `mechanisms.by_pain` má typicky id `q7`** — kód čte
  top_pain z `q7`. Když ji dáš jinam, ověř, že `Q7_FIELD_ID` v `fields.ts`
  ukazuje na správnou otázku (nebo pojmenuj bolestivou otázku `q7`).
- **`hint` u otázek se v kvízu nerenderuje** — detail/vysvětlení dej do `options`
  nebo do znění otázky, ne do samostatného `hint`.
