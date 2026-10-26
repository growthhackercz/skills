# Learned gotchas — 18 produkčně ověřených pastí

Všechno níže je **ověřené naživo** při stavbě referenčního produkčního funnelu
(2026-05 až 2026-07, GHL + Netlify). Nejsou to hypotézy — každá položka už
jednou stála reálný debugging. Neporušuj je.

## G1 — GHL scheduled e-maily: SEKUNDY, cancel endpoint, IDs append-only

- Plánování: `POST /conversations/messages` s `{ "type": "Email", "contactId",
  "subject", "html", "scheduledTimestamp": <UNIX SEKUNDY> }`.
  **Timestamp v milisekundách → 422** (s návodnou chybou). 201 vrací
  `emailMessageId` + `conversationId`.
- Zrušení: `DELETE /conversations/messages/email/{emailMessageId}/schedule` → 200
  „Cancelled successfully". Hromadný cancel endpoint neexistuje — iteruj přes
  uložené IDs.
- **`emailMessageId` ukládej append-only** do pole „AIQ - Scheduled IDs" (JSON
  array, LARGE_TEXT). Bez uložených IDs nejde nic zrušit → stop-on-purchase ani
  kill switch nefungují.
- GET single message přes email id vrací 400 (nefunkční); stav scheduled zpráv
  čti přes `GET /conversations/{conversationId}/messages`.

## G2 — GHL volat VÝHRADNĚ z Node fetch

python-urllib (a podobné klienty) blokuje Cloudflare před GHL API — **error 1010**.
Node `fetch` (undici) prochází spolehlivě. Všechny GHL skripty v tomhle skillu
jsou proto `.mjs`; nepřepisuj je do Pythonu a nedělej „rychlý curl z Pythonu".

## G3 — Custom fields VŽDY přes field `id`

`POST /customFields` vrací `id` — to je jediný identifikátor, přes který se
zapisuje: `customFields: [{ "id": "<fieldId>", "value": "…" }]`.
**Nikdy name/fieldKey matching** — přesně ta vrstva hádání klíčů (slugifier,
formLabels, `contact.` prefix, dvojitá podtržítka) zabila architekturu 1.3.x.
Field ID mapa žije ve `funnel-spec.json` (kvízová pole) a `fields-map.json`
(persona pole). Multi-select hodnoty → CSV string.

## G4 — LLM personalizace MUSÍ běžet v background funkci

Netlify synchronní funkce (API routes) mají **30s wall-clock limit** — LLM call
(~10–60 s) ho přeteče → 504 (stalo se při F2b). Personalizace proto běží
v **`netlify/functions/personalize-background.mts`** (background funkce, limit
15 minut). API route `/api/personalize` ověří kontakt, zkontroluje idempotenci
a **kickne** background funkci přes interně ověřenou hlavičku; stav se sleduje
přes `/api/personalize/status` (tagy pending → processing → ready).

## G5 — Žádný `import "server-only"` v lib modulech sdílených s background funkcí

Balíček `server-only` funguje jen uvnitř Next.js runtime. Netlify background
funkce běží MIMO Next → import crashne, **funkce tiše spadne a stav zůstane
navždy `idle`/`pending`** (žádná chyba v UI). Lib moduly importované z
`personalize-background.mts` (ghl.ts, personalize.ts, fields.ts, emails.ts,
vocative.ts, funnel.ts, spec.ts) NESMÍ obsahovat `import "server-only"`.

## G6 — `fields-map.json` v buildu jen read-only ověřit a obnovit

`fields-map.json` se **bunduje při buildu** (importuje ho runtime kód). GHL
schema ale nesmí vznikat jako skrytý side effect buildu. Chybějící pole nejdřív
projdou read-only plánem a potvrzeným apply; build už jen GETne stav, ověří ho a
obnoví mapu:

```
command = "node scripts/ensure-fields.mjs --verify && npm ci && next build"
```

Ruční kopie souboru se při příštím buildu **přepíše ověřenou mapou** — nikdy na
ni nespoléhej. Missing/mismatch/drift build zastaví bez POST. Změna persona polí
proto znamená nový read-only plán, stejné explicitní deploy potvrzení, apply a
redeploy; samotný build GHL schema nemění.

## G7 — Next pinovat na auditovanou verzi

Netlify **blokuje deploy zranitelných verzí Next.js** (CVE screening). Starší
15.x se odmítne s chybou až v deploy fázi. Drž přesný pin z přibaleného
`package-lock.json` a před releasem spusť `npm audit --omit=dev --audit-level=high`.

## G8 — netlify.toml: Next plugin + esbuild povinné

```toml
[[plugins]]
  package = "@netlify/plugin-nextjs"

[functions]
  node_bundler = "esbuild"
```

Bez `@netlify/plugin-nextjs` se SSR routy nevygenerují jako serverless funkce →
**404 na všech routách** (deploy přitom projde zeleně). `esbuild` bundler je
potřeba pro `.mts` background funkci.

## G9 — cron-guard: kill-check nad ČERSTVÝM GET /contacts/{id}

`POST /contacts/search` je **eventually consistent** — tag `[prefix] - converted`
přidaný před chvílí v indexu ještě není (ověřeno při F2b). Search proto slouží JEN
k nalezení kandidátů; rozhodnutí „zrušit e-maily?" se dělá VŽDY nad čerstvým
`GET /contacts/{id}` detailem. Přesně tak to dělá `template/lib/guard-core.ts`
(`searchContactsByTag` → `getContact`) — nezjednodušuj to na search-only.

## G10 — GHL creds na klientově serveru; netlify-publisher v1.0 nepoužívat

- GHL API klíč + location zpřístupňuje **spravované runtime prostředí klienta**
  z CC Nastavení → Integrace. Builder vždy běží tam, kde jsou klientovy
  integrace; interní secret-store soubory přímo nečte.
- Skill **netlify-publisher v1.0 má rozbitou SSR deploy cestu** (`--no-build`
  nahraje jen statické artefakty → 404). Pro Next SSR funnel ho NEPOUŽÍVEJ —
  produkční deploy vždy spusť přes `{baseDir}/scripts/deploy.mjs`.

## G11 — Vokativ deterministicky, nikdy LLM

Oslovení 5. pádem řeší **tabulka v `lib/vocative.ts`** (lookup českých jmen).
Fallback při neznámém jménu = **„Dobrý den"** — nikdy nominativ („Milý Jan"),
nikdy celé jméno, nikdy LLM odhad (halucinuje tvary). Platí pro E0, generované
e-maily i hero prodejní stránky.

## G12 — Unsubscribe vkládá GHL, obálka má hardcoded identifikaci

- **Odhlašovací patičku vkládá GHL automaticky na úrovni sub-accountu** — v kódu
  se neřeší a API ji nevystavuje. Při smoke testu VIZUÁLNĚ ověř na doručeném e-mailu,
  že tam je (bez ní jde o porušení pravidel rozesílky).
- **Identifikace odesílatele** (název + adresa firmy) se bere ze
  `spec.brand.email_footer` (`lib/emails.ts` ji čte přes BRAND) — v kódu nic
  nepřepisuj, jen ověř, že `brand` má reálné údaje klienta. LLM generuje jen
  tělo e-mailu, obálku nikdy.

## G13 — LLM vrací JSON v markdown fence (```json)

`JSON.parse` na surovém LLM outputu padá s `Unexpected token '`'` a personalizace
tiše sjede na fallback (usedFallback=true). **Před parse VŽDY stripnout fence:**
`content.trim().replace(/^```(?:json)?\s*/i,"").replace(/\s*```\s*$/,"")`.
Ověřeno naživo 2026-07-02: bez strip byl 100% fallback rate, se stripem plná
LLM personalizace. Template to už obsahuje (lib/personalize.ts).

## G14 — Fallback texty MUSÍ být generické (spec-driven)

Fallback persona/e-maily se nikdy nesmí psát pro konkrétní produkt — při
zkopírování template pro jiný funnel by lead dostal texty cizího produktu
(reálně se stalo: Bioptron lead dostal „čistší vzduch ve vaší domácnosti").
Template lib/fallback.ts skládá texty ze spec (offer.product, lead_magnet_name,
guarantee) — při kopii pro nový funnel ho NEUPRAVUJ, funguje sám. Totéž platí
pro ctaOffer(): kategorie klíče jsou per funnel → switchovat přes pořadí
spec.scoring_bands, ne přes natvrdo zapsané názvy kategorií.


## G15 — Šablona MUSÍ být přibalená ve skillu (klientský VPS nemá referenční funnel)

První reálné nasazení mimo vývojový server (2026-07-02) se zablokovalo: builder
odkazoval na `/documents/sites/aiq-audit-vzduchu/` — ta existuje jen na
vývojovém serveru, na klientském VPS ne. **Šablona je proto od 0.5.1 součástí
skillu (`{baseDir}/template/`)** a builder z ní kopíruje vždy. Nikdy neodkazuj
na soubory mimo skill/vstupní složku — skill musí fungovat na čistém VPS.

## G16 — Identita klienta VÝHRADNĚ přes spec.brand (žádné texty cizího klienta)

Šablona kdysi obsahovala natvrdo zapsané texty referenčního klienta (nákupní
CTA, správce osobních údajů v zásadách, LLM system prompt, patičky). Při kopii
pro jiného klienta by leady i právní identita „odtékaly" k cizí firmě. Od 0.5.2
se všechna identita (název, nákupní URL, kontakt správce OÚ, patička e-mailů)
skládá ze `spec.brand` a zástupné hodnoty šablony jsou „Vzorová firma /
priklad-firmy.cz" — grep kontrola v checklistu (krok 3a) je povinná.

## G17 — Obsah produktu VÝHRADNĚ ze spec, nikdy natvrdo v šabloně (ani „jen pro jeden funnel")

G14 a G16 už tohle říkaly pro fallback texty a identitu klienta, přesto to
šablona porušovala dál — proto samostatná poznámka i pro **obsah produktu**.

Sekce „Jak to funguje" na prodejní stránce měla v `lib/ui.ts` natvrdo
kurátorovaná data čističky vzduchu (HEPA H13, aktivní uhlí, 21 dB noční režim)
a obcházela se to podmínkou:

```ts
if (_spec.funnel_slug !== "aiq-audit-vzduchu") return genericMechanisms();
```

Dvě škody najednou:

1. **Cizí produkt v šabloně.** Data jednoho klienta žila v kódu, který se kopíruje
   všem. Stačilo, aby se slug trefil, a lead na vodu čte o HEPA filtraci.
2. **Rozbitá sekce u všech ostatních.** `genericMechanisms()` řezal `offer.usp`
   jen na `[.;]`, jenže usp je typicky JEDNO souvětí s čárkami → vypadl jediný
   blok, kde byl nadpis useknutá kopie vlastního textu. Každý ne-audit funnel
   měl tuhle sekci viditelně rozbitou a nikdo si toho půl roku nevšiml, protože
   podmínka „vypadala jako fallback".

**Pravidlo:** jakmile v šabloně píšeš `if (spec.funnel_slug === ...)` nebo
konkrétní vlastnost produktu (materiál, technologie, číslo, jednotka), je to
chyba. Obsah patří do `spec` — tady `spec.mechanisms.by_pain` /
`spec.mechanisms.default`, které generuje strategie per funnel.

**Fallback nikdy nefabuluje.** Bez `spec.mechanisms` se poskládají karty
z `offer.usp` (jen nadpisy — usp je výčet vlastností, ne vysvětlení mechanismu)
a při prázdném výsledku se sekce **skryje**. Radši chybějící sekce než sekce
s cizím nebo useknutým obsahem.

**Grep guard (povinný před ZIPem):**

```bash
# Musí vrátit prázdno. CLIENT_SPECIFIC_TERMS sestav z názvu, značky,
# technologií a unikátních tvrzení referenčního produktu, ze kterého se
# šablona vyvíjela. Nikdy tento seznam neukládej do distribuovaného skillu.
T=template
grep -rnE 'funnel_slug\s*[!=]==' $T/lib $T/app $T/components
test -n "$CLIENT_SPECIFIC_TERMS"
grep -rniE "$CLIENT_SPECIFIC_TERMS" \
  $T/lib $T/app $T/components $T/funnel-spec.example.json
```

⚠️ **Rozsah guardu je půlka jeho hodnoty.** První verze tohohle grepu hlídala jen
`lib/app/components` — a `funnel-spec.example.json` s kompletním produktem
referenčního klienta (včetně `mechanisms` s HEPA) jí prošel bez povšimnutí.
Když guard rozšiřuješ o nový vzor, rozšiř i seznam souborů.

## G18 — Šablona nesmí být zaujatá na obor referenčního klienta (ani nepřímo)

G16/G17 řešily jméno klienta a obsah produktu. **Tohle je o úroveň jemnější a
uniklo to i grepu na názvy produktů:** šablona byla napsaná pro B2C funnel do
domácnosti, takže nesla oborovou zaujatost i tam, kde žádný produkt nejmenovala.

Nalezeno při kritickém review šablony, osm míst:

- `Quiz.tsx` — povinné zaškrtávátko: „Souhlasím se zpracováním odpovědí
  **(včetně údajů o zdraví členů domácnosti)**". Souhlas je povinný VŽDY
  (`canProceed`), takže i B2B funnel na účetní software nutil zákazníka
  odsouhlasit zpracování zdravotních údajů o rodině. **Nepravdivé, právně
  zavádějící a odrazující.**
- `PersonalizeKicker.tsx` — „Vyhodnocujeme hlavní rezervy vaší domácnosti…"
- `magnet/[contactId]/page.tsx` — „Jak to řeší podobné domácnosti"
- `vysledek/page.tsx`, `fallback.ts`, `personalize.ts` (i v bezpečnostním
  pravidle LLM promptu), `funnel-spec.example.json`

**Pravidlo:** šablona mluví o **klientovi a jeho situaci**, nikdy o „domácnosti",
„firmě", „pacientovi" ani jiném konkrétním publiku. Cokoli, co publikum
předjímá, patří do specu a rozhoduje o tom agent per funnel.

**Souhlas je spec-driven (`spec.consent_text`).** Text musí odpovídat tomu, na
co se kvíz OPRAVDU ptá. Zmínka o citlivých údajích (zdraví, děti, finance) jen
tehdy, když se na ně kvíz ptá. Výchozí text v šabloně je neutrální.

**Vzorový spec je záměrně zjevně zástupný a B2B.** Ne proto, že by B2B bylo
lepší, ale protože:
1. G14 vznikla tím, že **realistický** vzorový obsah šel omylem zkopírovat do
   cizího funnelu („Bioptron lead dostal čistší vzduch"). Co vypadá jako vzor,
   nikdo nenasadí.
2. B2B příklad rozbíjí domácnostní zaujatost — agent, který čte example jako
   schéma, z něj nasaje i tón.

**Grep guard (rozšíření G17):**

```bash
# musí vrátit prázdno napříč CELOU šablonou včetně example specu
grep -rniE '(domácnost|údaj[eů] o zdraví|členů rodiny)' \
  template/lib template/app template/components template/funnel-spec.example.json
```
