---
name: competitor-tracker
description: "Sleduje změny u vybraných konkurentů z veřejných zdrojů; použijte ho pro pravidelnou konkurenční hlídku, aktuální přehled nebo battlecard."
version: "1.1"
publishedAt: "2026-09-03"
category: analytics
status: ready
user-invocable: true
metadata: {"openclaw":{"emoji":"🐾","requires":{"bins":["python3"]},"optionalEnv":"APIFY_API_KEY"}}
---

# Stopař konkurence (competitor-tracker)

Scout vyráží na výzvědy na povel — **stopař drží stopu pořád**. Samostatný skill (mimo Ads Engine): stavová hlídka s watchlistem, historií a diffem. Ostatní skilly (ad-scout, stratégové, Obchodník) si tvoje soubory jen čtou z `/documents/competitors/` — ty nikoho nevoláš, oni nevolají tebe.

**Zlaté pravidlo: hlásíš JEN změny.** Tichý týden je legitimní výstup („nic podstatného — to je taky informace"). Tři plané poplachy = klient tě přestane číst.

**Orchestrátor:** `{baseDir}/scripts/tracker.py` (validovaný wrapper, žádný přímý shell). Datové kontrakty: `{baseDir}/references/data-contracts.md`.

## Workflow

### Krok 0 — kontext, klíč a stav

Nejdřív ověř, zda máš dost kontextu. Pokud klient neřekl, koho nebo co chce sledovat, polož jednu stručnou otázku. Pokud je zadání jasné, pokračuj bez zbytečného vyptávání.

```bash
python3 {baseDir}/scripts/tracker.py status
```

- `initialized: false` → jdi do režimu **NASTAVENÍ**.
- Chybí `APIFY_API_KEY` (pozná se při `patrol --dry-run`, pole `klic_nalezen`) → bezplatné zdroje dál fungují, ale výsledek je **neúplný** a nesmí se popsat jako „beze změn“. Placené zdroje se zapnou doplněním klíče v **Control Center → Nastavení → Integrace**. Ceny a bezplatné kredity se řídí aktuálním účtem klienta v Apify; neslibuj konkrétní tarif.

### Režim NASTAVENÍ (poprvé — „hlídej mi konkurenci")

1. **Zeptej se na konkurenty** (3–10 značek). Pokud je klient nezná nebo váhá, nabídni dohledání podle oboru a Product/Brand DNA. U každé značky potřebuješ název a pokud možno web.
2. **Dohledej IČO zdarma:** `tracker.py find-ico --name "Značka"`. Ukaž kandidáty s adresou a nech klienta potvrdit správný subjekt. Nehádej sám.
3. **Shrň seznam, rozsah zdrojů a rozpočet a ZASTAV.** Potvrzení seznamu ještě není souhlas s placenými voláními.
4. **Založ lokální stav bez placeného lookupu:**
   ```bash
   python3 {baseDir}/scripts/tracker.py init --country CZ --apify-monthly-usd 5
   python3 {baseDir}/scripts/tracker.py add-brand --name "Značka" --ico 12345678 --web "https://..."
   ```
   `add-brand` samo placené dohledání nespouští. Kombinaci `--find-page --confirm-paid` použij jen po samostatném výslovném souhlasu. U marketplace značek lze přes `--query` zadat přesnou Facebook stránku nebo URL pro Meta.
   Volitelně **brandová slova klienta** pro SERP hlídku („kdo inzeruje na vaše jméno"):
   `tracker.py add-keyword --term "jméno-klienta" --own-web "klientova-domena.cz"` (max 5).
   Volitelně **sledované stránky** konkurenta (ceník, klíčová kategorie, hlavní landing):
   `tracker.py add-url --brand <slug> --url "https://…"` (max 10/značku — vybírejte jen to, co vás opravdu zajímá). A **YouTube kanál** přes `add-brand --youtube "https://youtube.com/@kanal"`; **sociální sítě (organika)** přes `--facebook`, `--instagram`, `--linkedin` (URL/handle profilu konkurenta).

   **Měsíční bezpečnostní práh Apify:** musí být kladný. Skill před během čte aktuální útratu; při dosažení prahu nebo při neúspěšném ověření placené zdroje fail-closed přeskočí. Není to transakční účetní limit — právě běžící obchůzka jej může překročit, proto nastavte tvrdý strop také v Apify. Počet účtovaných pay-per-result položek každého actoru je omezen stejně jako počet požadovaných výsledků. Změna: `tracker.py set-budget --usd 10`.
5. **Dry-run a samostatný STOP před placenou prací:**
   ```bash
   python3 {baseDir}/scripts/tracker.py patrol --dry-run
   ```
   Ukaž `apify_actor_calls.minimum` a `.maximum`, aktuální rozpočtový stav a seznam zdrojů. Připomeň, že ceny actorů určuje Apify a mohou se měnit. Vyžádej výslovný souhlas s jednorázovými lookupy i prvním během.
6. **Teprve po souhlasu** spusť podle potřeby `find-page --confirm-paid` / `find-place --confirm-paid`, nech klienta potvrdit kandidáty a pak spusť `patrol --confirm-paid`. První snímek nespamuje NEW/KILLED; založí srovnávací základnu.
7. Ukaž board a vždy vypiš absolutní cestu. `open` volej jen na lokálním macOS. Nabídni týdenní naplánovanou úlohu v **Control Center** s vlastníkem AI Provozní manažer (COO). Souhlas musí pokrývat frekvenci i opakovaná placená volání.

### Režim OBCHŮZKA (týdně, naplánovaná úloha)

**Governance (rozhodnuto 2026-07-10):** rutinu provozuje **COO** (spouští, hlídá že běží, eskaluje výpadek zdroje) → **strategické změny reportuje AI CEO** (vstup do board reportu; CEO rozhoduje o strategické reakci — posun trhu, nový hráč, změna cen) → **akční doporučení** jdou handoffem roli podle povahy akce: marketingová (úhel, kreativa) → AI Marketér, obchodní (battlecard, námitky) → AI Obchodník.

```bash
python3 {baseDir}/scripts/tracker.py patrol --confirm-paid
```

Pak si přečti `digest/<týden>/summary.json` a napiš recap do chatu:

- **Tichý týden** smíš oznámit jen při `quiet: true` **a zároveň** `complete: true`: jedna věta — „U sledované konkurence beze změn. Nikdo neškáluje nic nového — to je taky informace." Nic víc. Nevyráběj obsah z ničeho.
- **Neúplná obchůzka** (`complete: false`): nejdřív přesně vyjmenuj přeskočené nebo nedostupné zdroje. Nikdy ji nepopisuj jako tichý týden.
- **Jsou eventy:** max 5 odrážek, seřazené podle důležitosti: **ALERT** (insolvence/likvidace = nejvyšší akční hodnota — „jejich zákazníci budou hledat náhradu") → RERUN (návrat winnera) → REGISTRY_CHANGE (změna vedení/vlastníků) → VELOCITY → NEW s velkým dosahem → KILLED → MILESTONE. Ke každé odrážce JEDNA věta „co to znamená".
- **Vždy zakonči DOPORUČENÍM AKCE s handoffem** (pokud eventy dávají důvod):
  > „Konkurent X vrátil reklamu na úhel 'úspora času' — prokázaný winner. Chcete, abych to předal stratégovi k návrhu odpovědi?"
  Úkol založ **až po souhlasu** klienta — pak REÁLNĚ, přes CC helper (žádné „předám" bez tasku):
  ```bash
  python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py create-task \
    --title "Reakce na konkurenta: <co>" --description-file /tmp/handoff.md \
    --assigned-to cmo --priority high --idempotency-key "tracker:<slug>:<týden>"
  ```
  (marketingová akce → `cmo`, obchodní/battlecard → `cso`; popis = event + doporučení + odkaz na board)
- Přilož cestu k boardu (`digest/<týden>/index.html`).

### Režim PŘEHLED („jak si konkurence stojí?" / „aktuální situace")

```bash
python3 {baseDir}/scripts/tracker.py overview
```
Jednorázový **situační board** — jak konkurence stojí PRÁVĚ TEĎ (aktivní kreativy, evergreeny, EU dosah, vedení/vlastníci z rejstříku, kdo neinzeruje). **Z paměti, zdarma, okamžitě** — žádný scrape. Rozdíl proti digestu: digest = co se ZMĚNILO tento týden, přehled = jak to STOJÍ teď. Pokud jsou snímky starší ~7 dní (pole `updated`) nebo `bez_snimku` není prázdné, nabídni čerstvý `patrol` (cena = běžná obchůzka) — spusť jen po souhlasu.

### Režim DOTAZ („co dělá konkurent X?")

`tracker.py status` → odpověz **z paměti** (agregáty + poslední události + profil `profiles/<slug>.md`). Žádné nové načítání. Nabídni čerstvý snímek a spusť ho jen po souhlasu (`patrol --brand <slug> --confirm-paid`).

### Wiki (Data Center)

- `patrol` zapisuje profily do `/documents/competitors/profiles/<slug>.md`. Samotný zápis na disk je **automaticky nevkládá do wiki**.
- Při běhu v úloze zaregistruj HTML board jako souborový výstup podle skutečné cesty a klientský recap jako úplný textový/reportový výstup. Do wiki se dostane jen podporovanou ingest cestou a jen pokud ji má klient zapnutou.
- Pokud má instance wiki karty typu **Firma**, lze potvrzeného konkurenta vést jako kartu Firma se štítkem `konkurence`. Neslibuj vznik karty, dokud ingest skutečně neproběhl.
- Zdroj pravdy watchlistu = `watchlist.json`, štítek ve wiki je pro lidi a agenty.

### Co obchůzka sleduje (zdroje a kadence)

| Zdroj | Kadence | Provoz | Události |
|---|---|---|---|
| Meta Ad Library (seznam + detail top 10 s EU dosahem) | týdně | placené dle aktuální ceny actoru | NEW/KILLED/RERUN/MILESTONE/VELOCITY |
| **Obchodní rejstřík** (ARES) | týdně | zdarma | REGISTRY_CHANGE, **ALERT** (insolvence/likvidace) |
| **Sbírka listin** (justice.cz) | týdně | zdarma | FILING — výroční zpráva/závěrka může obsahovat údaje o hospodaření |
| Homepage + **sledované stránky** (`add-url`, max 10 — ceník, kategorie, landing) | týdně | zdarma | WEB_CHANGE (titulek/H1/**ceny**) |
| Sitemap (blog/obsah/kariéra/nové stránky) | týdně | zdarma | BLOG_NEW, CONTENT_NEW, JOBS_NEW |
| YouTube kanál (`add-brand --youtube`) | týdně | placené dle aktuální ceny actoru | YOUTUBE (nová videa + zhlédnutí) |
| Sociální sítě — FB / IG / LinkedIn profil (`add-brand --facebook/--instagram/--linkedin`) | týdně | placené dle aktuální ceny actoru | SOCIAL_NEW; první snímek = SOCIAL_BASELINE |
| Google Ads Transparency (agregát) | týdně | placené dle aktuální ceny actoru | GOOGLE_ADS |
| LinkedIn Ad Library (B2B, imprese po zemích) | týdně | placené dle aktuální ceny actoru | LINKEDIN_ADS |
| Recenze Google Maps | **měsíčně, jen po potvrzení konkrétního místa** | placené dle aktuální ceny actoru | REVIEWS |
| SERP brandová slova klienta (`add-keyword`) | **měsíčně** | placené dle aktuální ceny actoru | SERP_ADS („kdo inzeruje na vaše jméno") |
| **Newslettery konkurence** (CC schránka, viz níže) | při obchůzce | zdarma | NEWSLETTER (přes `log-event`) |
| Wayback (historie webu) | 1× při setupu | zdarma | WAYBACK |

**Report je klikací:** každá karta značky má nahoře **pás náhledů aktivních kreativ** (nejdéle běžící = winnery, klik = Ad Library, i při první obchůzce) a každá událost nese odkazy (kreativa → Meta Ad Library + cílová stránka, příspěvek, video, recenze na Mapách, rejstřík ARES, Google Ads Transparency, nová stránka webu) a u nových / vypnutých / vrácených kreativ **náhled obrázku**. Co provider nedodá, se nevykreslí — žádné mrtvé odkazy. První obchůzka má vlastní hlavičku („základna pro příští porovnání"), není to „tichý týden".

Náhledy jsou vzdálené obrázky z veřejných zdrojů. Report neposílá cílovým webům adresu dokumentu (`no-referrer`), ale při otevření mohou jako každý vzdálený obrázek vidět IP adresu prohlížeče. Pro citlivé použití report otevři bez načítání vzdálených obrázků.

Placené zdroje jedou jen s APIFY_API_KEY; bez něj jedou všechny zdarma vrstvy. **Produktová/cenová hlídka e-shopů (tisíce SKU) je mimo záběr** — separátní budoucí skill; tracker hlásí jen agregát „hýbou sortimentem".

#### Bezpečnost sledovaných adres

Adresu sledované stránky zadává klient (`add-url`) a nachází se i uvnitř cizí sitemapy. **Každé stažení proto prochází `scripts/net_guard.py`:** jen http/https, jen porty 80/443, host se přeloží a **všechny** jeho adresy musí být veřejné (odmítá se loopback, privátní rozsahy, 169.254.169.254, CGNAT, multicast, rezervované). Přesměrování se **nenásleduje automaticky** — každý hop se validuje znovu, protože veřejná adresa smí odpovědět přesměrováním dovnitř.

Kontrola běží už při `add-url`, takže klient dostane chybu hned, ne až za týden při obchůzce.

🛑 **Nikdy nestahuj URL mimo `net_guard`.** Ani „jen sitemapu", ani „jen ověření, že web žije".

#### Odolnost zdrojů — tichý týden smí být jen OVĚŘENÉ ticho

Každý placený zdroj má **řetěz actorů** (primár + záloha). Když primár selže, automaticky se zkusí záloha; při čisté prázdné odpovědi se záloha nevolá. Řetěz lze změnit proměnnou v Control Center → Nastavení → Integrace: `COMP_REVIEWS_ACTORS`, `COMP_GOOGLE_ACTORS`, `COMP_LINKEDIN_ACTORS`, `COMP_YOUTUBE_ACTORS`, `COMP_FACEBOOK_ACTORS`, `COMP_INSTAGRAM_ACTORS`, `COMP_LINKEDIN_POSTS_ACTORS`, `COMP_SERP_ACTORS`. Hodnota je seznam platných ID ve tvaru `vlastnik~actor` oddělených čárkou.

Zdroj končí v jednom ze čtyř stavů a **každý znamená v reportu něco jiného**:

| Stav | Kdy nastane | Co se stane |
|---|---|---|
| **OK** | zdroj vrátil čitelná data | normální porovnání se snímkem |
| **PRÁZDNO** | zdroj čistě odpověděl, ale nic tam není | legitimní „beze změn" |
| **NEDOSTUPNÝ** | padl celý řetěz, nebo data přišla v neznámém formátu | event `SOURCE_UNAVAILABLE` + `complete: false` |
| **PŘESKOČENÝ** | chybí klíč, rozpočet je vyčerpaný/neplatný nebo nejde ověřit útratu | event `SOURCE_SKIPPED` + `complete: false` |

**Platí pro všechny zdroje, ne jen placené.** Výpadek webu, obchodního rejstříku i sbírky listin je taky `SOURCE_UNAVAILABLE` — dřív se jen přeskočil, takže u klienta bez `APIFY_API_KEY` (kde web je jediná vrstva) vypadal nedostupný web jako klidný týden.

**Záloha se volá jen při selhání, ne při prázdné odpovědi.** Konkurent, který zrovna neinzeruje, je běžný stav; řetěz proto končí u prvního actora, který **odpověděl** — ať už něco našel, nebo poctivě nic. Jinak by se u každého klidného konkurenta platily oba actory a pád zálohy by přebil čistou odpověď primáru.

🛑 **Když je `complete: false`, NIKDY klientovi nenapiš „u konkurence nic nového".** To by z rozbitého scraperu udělalo falešné ticho — přesný opak toho, co skill slibuje. Místo toho vždy přiznej rozsah: *„Tento týden jsem nezkontroloval [zdroj] — ten je dočasně nedostupný. Ze zbytku zdrojů žádné změny."*

### Newslettery konkurence

1. **Nastavení po samostatném souhlasu klienta:** použij monitorovací e-mailový účet napojený v Control Center. Přihlášení k newsletteru je externí akce; proveď ji jen pro konkrétně schválené značky a adresu poznamenej do watchlistu (`note`).
2. **Při obchůzce:** zkontroluj schránku e-mailovými nástroji (od poslední obchůzky). Nový newsletter konkurence → zaloguj do event streamu:
   ```bash
   python3 {baseDir}/scripts/tracker.py log-event --brand <slug> --type NEWSLETTER \
     --note "Předmět: '…' — promo X % na Y, CTA na Z"
   ```
   Event se objeví v digestu, profilu i CEO reportu. Sleduj: frekvenci, promo kalendář, předměty (hooky), nabídky.

### Battlecard (pro Obchodníka) a CEO report

- **„připrav battlecard na konkurenta X"** → `tracker.py battlecard --brand <slug>` → `battlecards/<slug>.md` (fakta z rejstříku + reklamní přítomnost + slabiny z recenzí + poslední pohyby). Sekci „Jak proti nim" DOPLŇ ty (prodejní argumenty z dat).
- **Měsíčně / „report pro vedení"** → `tracker.py ceo-report` → `reports/<měsíc>.md` — strategický roll-up (ALERTy nahoře) do board reportu AI CEO. CEO je měsíční příjemce, ne týdenní schvalovací brána.

### Tvrdá pravidla

1. **Nikdy nespouštěj placený zdroj bez potvrzeného rozsahu a kladného rozpočtového prahu.** Výchozí limit je 50 reklam/značku, max 10 značek a max 5 brandových slov.
2. **Cache:** `patrol` stejný den nespouštěj dvakrát. Pokud už existuje dnešní souhrn, příkaz ho vrátí bez dalších provider volání; `--force` používej jen po kontrole.
3. **Poctivé labelování:** délka běhu = „za tohle dál platí" (proxy útraty). **Dosah v EU = reálné číslo** z transparentnosti dle nařízení EU (DSA) — když je k dispozici, používej ho jako hlavní důkaz. Nikdy netvrď, že znáš přesnou útratu.
4. **Terminologie:** nikdy „špehování/špionáž" — vždy „veřejně dostupná data z knihoven reklam (transparentnost dle nařízení EU)". Klientovi vykej.
5. **Klíče:** APIFY_API_KEY nikdy nevypisuj do chatu ani logů.
6. **Neblokuj ostatní:** když jiná role potřebuje tvá data a nejsou (`initialized: false`), NEspouštěj setup sám od sebe — řekni, že hlídka není zapnutá, a nabídni ji.

### Trhy

Knihovny reklam fungují ve všech trzích (DSA — v EU všude s čísly dosahu). **Úřední stopa je per-trh výměnná**: CZ = obchodní rejstřík ARES (plně funkční, zdarma) · GB = Companies House (roadmapa, zdarma s klíčem) · ES = Registro Mercantil/BORME (roadmapa). Nepodporovaný trh → úřední stopa se tiše vynechá (`find-ico` to řekne), zbytek jede. User-facing texty jsou zatím česky — lokalizace ES/EN je samostatná práce, neslibuj ji.

## Output Template

```markdown
**Stopař konkurence — týden {W}.** {Jedna věta souhrnu.}

- {Událost 1: co se stalo a co to znamená.}
- {Událost 2; nejvýše 5 odrážek.}

{Doporučení akce a nabídka handoffu; při úplném tichém týdnu jen jedna věta.}
{Při `complete: false`: „Neověřené zdroje: {seznam}. Ze zbývajících zdrojů: {závěr}.“}

Board: {absolutní cesta}
```

## Decision Criteria

| Podmínka | Práh | Akce |
|---|---:|---|
| Nejasný seznam konkurentů | chybí název nebo trh | Polož jednu doplňující otázku; nic placeného nespouštěj. |
| Rozsah watchlistu | 3–10 značek | Nad 10 odmítni a navrhni zúžení; pod 3 upozorni na slabé srovnání. |
| Placený setup nebo patrol | chybí výslovný souhlas | Zastav před prvním actor voláním. |
| Rozpočtový stav | vyčerpáno, neplatný práh nebo útratu nelze ověřit | Placené zdroje fail-closed přeskoč; bezplatné mohou pokračovat. |
| Úplnost výsledku | `complete: false` | Vyjmenuj neověřené zdroje; nepoužij formulaci „beze změn“. |
| Tichý týden | `quiet: true` a `complete: true` | Odpověz jednou větou bez uměle vytvořených doporučení. |
| Opakovaný běh | dnešní snapshot a summary už existují | Vrať uložený výsledek; nespouštěj actory znovu. |
| Nová strategická událost | ALERT, RERUN nebo významná změna | Nabídni konkrétní handoff; úlohu založ až po souhlasu. |

## Anti-patterns

| Nedělej | Proč | Místo toho |
|---|---|---|
| Neoznamuj tichý týden při neúplném běhu. | Výpadek zdroje by vypadal jako klid trhu. | Otevřeně uveď `sources_unavailable` a rozsah platných zjištění. |
| Nevolej placené lookupy automaticky při `add-brand`. | Potvrzení seznamu není souhlas s útratou. | Nejdřív dry-run, potom explicitní souhlas a až pak `find-page`/`find-place`/`patrol`. |
| Neobcházej rozpočet přes `--force`. | `--force` slouží jen k novému snapshotu, ne k obejití pojistky. | Uprav kladný práh po souhlasu klienta nebo nastav limit v Apify. |
| Nekopíruj výstupy do další složky. | Vznikají duplicity v Data Center. | Ukládej pouze do `/documents/competitors/` a registruj skutečnou cestu. |
| Neslibuj automatický vznik wiki karty. | Přímý zápis souboru není wiki ingest. | Ověř podporovanou ingest cestu a zapnuté nastavení wiki. |
| Nezakládej handoff jen větou v chatu. | Práce by nebyla dohledatelná. | Po souhlasu vytvoř skutečnou úlohu přes `mc-task-api`. |

## Integration

**Uses:**

- `APIFY_API_KEY` v Control Center → Nastavení → Integrace — volitelné placené zdroje; čte se za běhu ze store.
- `mc-task-api` — registrace výstupu a potvrzené předání navazující práce.
- `/documents/competitors/` — jediný kořen trvalých souborů skillu.
- ARES, justice.cz, Wayback a veřejné weby — bezplatné zdroje; jejich výpadek se vždy přizná.

**Used by:**

- AI Provozní manažer (COO) — vlastník pravidelné obchůzky.
- AI CEO — příjemce strategického souhrnu a rozhodnutí o reakci.
- AI Marketér / AI Obchodník — navazující úlohy a battlecards po schváleném handoffu.

## Quality Checklist

- [ ] Watchlist obsahuje pouze klientem potvrzené značky a subjekty.
- [ ] Před placenou akcí proběhl dry-run a výslovný souhlas s rozsahem i frekvencí.
- [ ] Rozpočtový práh je kladný a aktuální útrata byla ověřena; jinak placené zdroje neběžely.
- [ ] `summary.json` obsahuje `complete`, `quiet`, `sources_unavailable` a `paid_sources`.
- [ ] Formulace „beze změn“ je použita jen při `complete: true` a `quiet: true`.
- [ ] HTML board neukazuje tichý týden současně s neověřeným zdrojem.
- [ ] Každý trvalý soubor existuje jen na jedné cestě pod `/documents/competitors/`.
- [ ] Board a recap jsou zaregistrované jako výstupy podle skutečné cesty/obsahu.
- [ ] Případný wiki obsah prošel podporovanou ingest cestou; nevznikl jen zápisem na disk.
- [ ] Handoff úloha vznikla až po souhlasu a má idempotency key.

## Data Files

Přesný strom, kompatibilní JSON kontrakty a pravidla migrace jsou v `{baseDir}/references/data-contracts.md`. Poškozený stav neopravuj založením nové základny; zastav a obnov ho ze zálohy.

## File Naming Convention

Všechny soubory patří výhradně pod `/documents/competitors/`. Týdenní board je `digest/<YYYY-Www>/index.html`, strojový souhrn `summary.json`, profil značky `profiles/<slug>.md` a měsíční report `reports/<YYYY-MM>.md`.
