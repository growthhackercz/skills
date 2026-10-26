# Landing a děkovací stránka k lead magnetu

Načti, když stavíš stránky k magnetu na kontakty (PDF, checklist, průvodce
zdarma). Vždy vznikají **dvě stránky**: landing (sběr kontaktu) a děkovačka.

**Dělba práce:** obsah magnetu, název, sliby a copy dodává skill
`lead-magnet-generator` (soubory `00-strategie.md`, `01-nazvy.md`,
`02-osnova.md`, `04-landing.md`, `05-dekovacka.md` ve
`/documents/lead-magnets/<slug>/`). **Stránku ale vždy stavíš ty podle
vibe-builderu** — Web DNA, koncept, `06-patterns`, subtilní reveal vrstva,
anti-slop brána. Markdown z generátoru je scénář, ne hotová stránka.

## Branding — čí je to stránka

- **Logo je povinné** v hlavičce i patičce, plus favicon. Bez loga není poznat,
  komu stránka patří, a důvěra padá dřív, než si někdo přečte nadpis.
- Magnet obvykle patří **klientovi, ne nám**. Paletu, typografii, fotografický
  styl a tón odvoď z klientova webu nebo jeho Brand DNA — ne z CliqSales brandu.
  Logo si stáhni z klientova webu do `assets/`.

## Landing — anatomie

Jeden cíl: nechat e-mail. Žádná navigace pryč ze stránky, žádné odkazy do
menu, jeden typ akce.

1. **Hero** — slib v podobě výsledku („Vyberte X podle Y, ne podle letáku“),
   podnadpis jednou větou, **mockup magnetu jako hlavní vizuál**, formulář nebo
   tlačítko hned vedle. Nad záhybem musí být vidět, co dostanu a co za to.
2. **Co je uvnitř** — 3–6 konkrétních věcí, každá jako výsledek, ne jako název
   kapitoly. Ikona nebo číslo, jedna věta.
3. **Ukázka** — jedna reálná strana nebo prvek z magnetu (tabulka, checklist,
   srovnání). Nejsilnější důkaz, že uvnitř něco je.
4. **Pro koho to je** — dvě až tři věty, ať se nesprávný čtenář sám odfiltruje.
5. **Autor a důvěra** — kdo to napsal a proč tomu rozumí; případně čísla, která
   máš doložená.
6. **Formulář podruhé** — jméno + e-mail, tlačítko v 1. osobě („Chci průvodce“),
   pod ním mikrocopy: co přijde, jak často, souhlas se zpracováním údajů.

Co na landing nepatří: cena produktu, dlouhý prodejní blok, více CTA cílů,
externí odkazy, patička plná menu.

## Děkovačka — anatomie

Stránka po odeslání formuláře. Nejlevnější místo v celém funnelu — a nejčastěji
odbyté.

1. **Potvrzení** — „Hotovo, průvodce je na cestě“ + **tlačítko ke stažení hned**
   (nenech ho čekat na e-mail).
2. **Co bude následovat** — od koho a kdy přijde e-mail, ať to nespadne do spamu;
   případně „přidejte si nás mezi kontakty“.
3. **Jeden další krok** — nevtíravý přechod k produktu: krátké video, konzultace,
   nebo odkaz na prodejní stránku. **Jedno CTA, ne tři.**
4. Volitelně: co ještě máme (druhý magnet, kalkulačka), kontakt.

Děkovačka má vlastní URL (`/<magnet-slug>/dekujeme/`), aby šla měřit jako
konverze.

## 🛑 Brána: formulář musí někam vést

**Landing, jehož formulář kontakt nikam neuloží, není hotový.** Je to nejdražší
vada celého funnelu: stránka vypadá funkčně, klient za ni platí reklamu a leady
mizí. `<form>` bez `action` a bez odesílacího handleru je vada, ne rozpracovaný
stav — nikdy ji nepředávej jako hotovou práci.

Statická stránka nesmí volat CRM přímo z prohlížeče, tam by skončil klíč
v HTML. Odesílá se přes **serverovou funkci** (`netlify/functions/lead.mjs`,
vystavená jako `/api/lead`), hodnoty se nahrávají výhradně publisherem přes
`env-set --from-variable` — nikdy argumentem, v `netlify.toml` ani v chatu.

Hotová funkce k opsání: `references/lead-form.template.mjs`.

Šablona používá existující **Netlify Blobs**, ne nový vendor: trusted Netlify
IP má 10 pokusů / 10 minut a krátký CAS lease nad e-mailem + tagem zavře
souběh lookup → create. Guard má pevně 32 stříd po nejvýš 64 aktivních
identitách, prošlé položky průběžně uklízí a při konfliktu selže zavřeně.
Dokončený opakovaný submit vrátí úspěch bez druhého CRM volání; skutečně
souběžný dostane 409 místo předčasného falešného úspěchu. Chyba při read-only
lookupu krátký lease uvolní. **Před prvním remote POSTem** se ale lease změní na
durable neurčitý stav: timeout nebo pád po možném commitu už nikdy nespustí
druhý create naslepo. Další pokus pouze vyhledá kontakt a stav usmíří; dokud
provider nově vytvořený kontakt nevrací, odpoví 503 a nic nezapisuje. Lease má
owner nonce, takže opožděný run nepřepíše novější stav. Každý fetch do GHL má
timeout (default 8 s, vždy oříznutý na 0,25–15 s).

### Prostředí funkce — úplný seznam

| Proměnná | Povinná | Význam / default |
|---|---|---|
| `GHL_API_KEY` | ano | Private Integration Token; nikdy ho nevypisuj |
| `GHL_LOCATION_ID` | ano | Location, ve které se kontakt hledá a zakládá |
| `LEAD_GUARD_SECRET` | ano | HMAC klíč min. 32 znaků (`openssl rand -hex 32`) |
| `MAGNET_TAG` | ne | Tag přidaný samostatným voláním; bez hodnoty se netaguje |
| `MAGNET_SOURCE` | ne | Zdroj nového kontaktu; default `lead magnet` |
| `SOUHLAS_FIELD_ID` | ne | ID existujícího custom field pro čas souhlasu; bez něj se pole vynechá |
| `GHL_TIMEOUT_MS` | ne | Timeout jednoho GHL volání; default `8000`, rozsah `250–15000` ms |

Do projektu patří názvy a popisy v `.env.priklad`, nikdy hodnoty. `.env` musí
být v `.gitignore`. Pro lead cestu nainstaluj `@netlify/blobs` přes přesnou
sekvenci z `05-stack.md` / `16-aplikace.md` (`--legacy-peer-deps`, potom
exec-bit fix).

### Ověřená sekvence proti GoHighLevel

Ověřeno naživo 7. 8. 2026 na účtu CliqSales CZ (v2.0 API, Private Integration
Token scopovaný na location klienta).

1. `GET /contacts/search/duplicate` — nejdřív se podívej, jestli kontakt
   existuje.
2. **Existuje** → je-li `MAGNET_TAG` nastavený, jen
   `POST /contacts/{id}/tags` s tagem magnetu; bez tagu žádný vzdálený zápis.
   **Profil se nedotýkej.**
3. **Neexistuje** → `POST /contacts/` (jméno, e-mail, telefon, `source`),
   potom jen při nastaveném `MAGNET_TAG` také `POST /contacts/{id}/tags`.

- **🛑 `upsert` se nepoužívá.** Podle nastavení duplicit v location umí
  **přepsat profil**, který o zákazníkovi klient už má — jméno, telefon
  i zdroj. Magnet nesmí přepisovat data z jiných zdrojů. Proto lookup, ne upsert.
- **🛑 `tags` v těle PŘEPISUJÍ celé pole, nepřidávají.** Tagy vždy samostatným
  voláním na `/contacts/{id}/tags`.
- Hlavičky: `Authorization: Bearer <PIT>`, `Version: 2021-07-28`,
  `Content-Type: application/json` a **plný prohlížečový `User-Agent`** —
  bez něj vrací Cloudflare 403 „Error 1010" a vypadá to jako špatný klíč.
- Nekonzistence GHL: některé endpointy chtějí `locationId`, jiné `location_id`.
  Ověř v dokumentaci pro konkrétní endpoint, nehádej — hotové volání i s
  hlavičkami je v `{baseDir}/references/lead-form.template.mjs`.

### Co k tomu patří na stránce

- Tlačítko má stav odesílání a je po dobu volání neaktivní, ať se formulář
  neodešle dvakrát.
- Chyba se ukazuje u formuláře lidskou větou, ne mlčením ani `alert()`.
- Na děkovačku se přechází **až po úspěšné odpovědi**, nikdy dřív.
- Souhlas se zpracováním údajů je zaškrtávací pole a odesílá se s kontaktem.
- **Past na roboty:** ve formuláři je navíc pole `web`, skryté před člověkem
  (`position:absolute;left:-9999px`, `tabindex="-1"`, `autocomplete="off"`).
  Člověk ho nevyplní, robot ano — funkce takové odeslání tiše zahodí. Nikdy
  ho neschovávej přes `display:none`, část robotů to pozná.

```html
<div aria-hidden="true" style="position:absolute;left:-9999px">
  <label>Web <input name="web" tabindex="-1" autocomplete="off"></label>
</div>
```

### Test před předáním

Nejdřív bez sítě spusť behaviorální test nad skutečnou šablonou:

```bash
node {baseDir}/tests/test_lead.mjs
```

Test podvrhne fetch i Blobs a ověří no-overwrite existujícího kontaktu,
oddělené create/tag volání, souběžnou idempotenci, reconcile neurčitého remote
výsledku bez druhého create, IP limit, bounded názvy Blobů a skutečné
přerušení timeoutem. Jeho úspěch nenahrazuje následující
produkční smoke test, ale rozbitá šablona se nesmí dostat až k němu.

Odešli formulář na nasazené stránce a **dolož kontakt v CRM** — jméno, e-mail,
zdroj a při nastaveném `MAGNET_TAG` také tag magnetu. Bez tohohle důkazu se landing nepředává. Testovací kontakt
používej rozpoznatelný (`test.<slug>@…`) a řekni klientovi, že tam je; mazat ho
v CRM smíš jen na výslovné svolení.

## Mockup magnetu

Hlavní vizuál landingu. Většina mockupů selže tím, že je z nich mrtvý předmět
na stole.

- **Živá scéna, ne aranžmá:** ruce držící brožuru nebo tablet, člověk u okna,
  prostředí, kde se produkt reálně používá. Pohyb a energie.
- **Téma poznatelné na první pohled** — v záběru je vidět, čeho se magnet týká
  (u čističky vzduchu obývák a samotná čistička, u služby prostředí zásahu).
- **Teplé přirozené světlo**, hloubka, bokeh, bohatý tonální kontrast,
  magazínová kvalita. Nikdy plochý packshot na bílém.
- **Název na obálce velký a čitelný**, v jazyce trhu se správnou diakritikou.
- **Reference reálné fotky produktu je povinná** (viz `14-carousel-images.md`) —
  bez ní si model produkt domyslí.
- Displej v záběru vždy čelem ke kameře, obsah vzpřímený, nikdy zrcadlený.
- **Jeden obrázek**, maximálně jeden opravný pokus. Pálí to kredity.

## Kdy vzniká PDF

- **Ukázka pro video, demo, nácvik funnelu** → stačí landing + děkovačka. PDF
  negeneruj, zbytečně to zdržuje.
- **Ostrý magnet pro klienta** → obsah z `lead-magnet-generator`, sazba a PDF
  přes `html-lead-magnet-generator` (Playwright, bez kreditů).

Ptej se na to na začátku, ne až po vysázení dokumentu.

## Kontrola před předáním

- [ ] Logo klienta v hlavičce, patičce a jako favicon
- [ ] Na landingu jeden cíl a žádná navigace pryč
- [ ] Formulář nad záhybem i na konci, mikrocopy o zpracování údajů
- [ ] Mockup je živá scéna s viditelným tématem, ne předmět na bílém
- [ ] Děkovačka má tlačítko ke stažení a právě jedno další CTA
- [ ] Děkovačka má vlastní URL
- [ ] **Formulář odesílá do CRM a je to doložené** — odeslaný testovací kontakt
      v CRM se zdrojem a, je-li `MAGNET_TAG` nastavený, i s tagem magnetu.
      Klíč v prostředí funkce, ne v HTML
- [ ] Offline `tests/test_lead.mjs` prošel; timeout, IP limit, idempotence a
      reconcile neurčitého remote výsledku zůstaly zapnuté
- [ ] Všechny povinné env z tabulky jsou nahrané přes `env-set --from-variable`;
      volitelné mají vědomě zvolený default
- [ ] Je-li `MAGNET_TAG` nastavený, tag se přidává přes
      `/contacts/{id}/tags`, ne přes `tags` v upsertu; bez něj se tag neočekává
- [ ] Tlačítko má stav odesílání, chyba se zobrazí u formuláře, na děkovačku
      se přechází až po úspěšné odpovědi
- [ ] Obě stránky bez vodorovného scrollu na 390 px a bez chyb v konzoli
- [ ] Prošla anti-slop brána (`scripts/design-gate.js`)
