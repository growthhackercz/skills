---
name: ad-scout
description: "Průzkumník reklamního trhu pro Ads Engine. Když chystáte kampaň na konkrétní produkt, zadáte jeho název a skill vrátí Product Intelligence Board — kdo ten produkt prodává a za kolik (včetně dopravy), kdo právě zlevnil, komu došlo zboží, co na produktu chválí a kritizují zákazníci (hotové náměty do reklam), kde máte v sortimentu díru, kdo se zobrazuje na Googlu a kdo jede reklamy na Facebooku. Reálná data z trhu, jeden výpis stojí pár centů. Bez placeného klíče jede v omezeném režimu z volných zdrojů."
category: analytics
status: ready
version: "1.0"
publishedAt: "2026-07-13"
user-invocable: true
metadata: {"openclaw":{"emoji":"🎯","requires":{"bins":["python3"]},"primaryEnv":"APIFY_API_KEY"}}
---

# Ad Scout — Product Intelligence Board

Pull-scout Ads Enginu, který se dívá **ven na reklamní a produktový trh**. Tenhle režim řeší **produktovou konkurenční inteligenci**: spouští se **názvem konkrétního produktu** (typicky když agent nebo klient chystá kampaň na ten produkt) a vrací **Product Intelligence Board** — jeden snímek toho, s kým na trhu soupeříte a jak z toho postavit lepší kampaň.

**Osa = název produktu**, ne téma/klíčové slovo, ne B2B/B2C. Když je vstup produktově vypadající (název produktu / kategorie / produkt z DNA klienta), jede tenhle board.

**{baseDir}/scripts/scout.py** = validovaný wrapper (žádný přímý shell). Provider je vyměnitelný (`provider.py`).

**Provider = Apify** (`APIFY_API_KEY`, per-klient — klient si platí sám; jeden výpis ~$0,05–0,10). Data z ověřených zdrojů: **Heureka** (ceny + dostupnost + hodnocení + recenze konkurentů na produkt), **Google SERP** (kdo se na produkt zobrazuje organicky i placeně), **Meta Ad Library** (kdo na produkt jede reklamy a jak dlouho). Detaily zdrojů a aktorů: `{baseDir}/references/data-sources.md`.

## Výstupy ad-scoutu (rodina: boardy = šířka, karta = hloubka)

| Board | Osa (spouštěč) | Renderer | Spec |
|---|---|---|---|
| **Product Intelligence Board** | název **produktu** | `scripts/board.py` | `references/product-intelligence-board.md` |
| **Viral Ad Board** | **klíčové slovo / téma** | `scripts/adboard.py` (+ build `adboard_build.py`) | `references/viral-ad-board.md` |
| **Competitor Ad Board** | **značka** (doména konkurenta) | `adboard.render_competitor` (+ build `compboard_build.py`) | `references/competitor-ad-board.md` |
| **Search Ad Board** | **klíčové slovo ve VYHLEDÁVÁNÍ** (kdo platí za aukci) | `scripts/searchboard.py` (+ build `searchboard_build.py`) | `references/search-ad-board.md` |
| **Viral DNA Card™** | **jeden donor** (URL reklamy / obsahu) | `scripts/dnacard.py` (+ build `dnacard_build.py`) | `references/viral-dna-card.md` |

**Rozliš podle vstupu:** produktově vypadající dotaz (název/kategorie/produkt z DNA) → Product Intelligence Board (kroky níže). **Klíčové slovo / téma** (co inzeruje konkurence na téma X, z čeho čerpat kreativu) → **Viral Ad Board** (viz sekce níže). **Konkrétní konkurent** (doména / název značky — „co běží GymBeamu", „podívej se na konkurenta X") → **Competitor Ad Board** (viz sekce níže). **Vyhledávání / PPC** („kdo inzeruje na slovo X v Googlu", „vyplatí se nám PPC na Y", „za jaká slova platí konkurence") → **Search Ad Board** (viz sekce níže). **Jeden konkrétní kus** (URL reklamy/videa/postu — „rozeber mi tohle", „proč tohle funguje") → **Viral DNA Card** (viz sekce níže).

**Raw Diet** (`voice-of-customer.json` = agregace hlasu zákazníka z recenzí) = **roadmapa** — než existuje, dodávají jazyk zákazníka recenzní blok Product Boardu a sekce Jazyk zákazníka / Reakce publika.

---

## Viral Ad Board — když je osa TÉMA (ne produkt)

Vítězné cizí kreativy na téma → **přenositelné vzorce (hook · úhel · formát)** ke klonování (jádro VIRAL DNA Cloning). **Stohované sekce** (ke klientovi VŠE česky): přehled + mapa úhlů + „proč se inspirovat" + knihovna hooků · **01 Placené reklamy** · **02 Organický obsah** (Krátký obsah / Dlouhý obsah) · **03 Úhly ve vyhledávání** · **04 Jazyk zákazníka**. Plný spec + schéma contractu + taxonomie úhlů: **`references/viral-ad-board.md`**.

1. **Fetch + kostra** — `python3 {baseDir}/scripts/scout.py viral-fetch "<téma>" --market cz [--b2b] [--since '18 months']`. **VŽDY nejdřív `--dry-run`** (odhad ~$0,11 + STOP). Stáhne reklamy (knihovna reklam) + **organiku přes `content_search` = KEYWORD SEARCH** (TikTok/YouTube/Instagram/Facebook, `--b2b` přidá **LinkedIn** — podle TÉMATU, ne hashtagu/watchlistu, obsah neuteče) + vyhledávání → deterministicky sestaví `rich-contract.json` (KOSTRA: skóre, výběr max 3/inzerent, CZ→globál, thumbnaily, `format` short/long). **Bez tvrdého časového limitu** (engagement napřed, `--since` jen pojistka). Denní cache.
2. **Doplň sémantiku (TVOJE práce jako modelu)** do `rich-contract.json`: **titulek `nm`** — když kus nemá jasný titulek, **shrň z textu, max 3 řádky** (nikdy útržek); **přelož cizí copy** (`nm` český + `orig` originál); **úhel** + **fázi povědomí**; **3× why**; **mapa úhlů** (plno/sporné/volno); **syntéza** + **knihovna hooků**; **`search_uhly`** (jaké úhly, NE share of voice); **`jazyk_zakaznika`** z komentářů (`content_comments` na TOP kusy — námitky/touhy/fráze/frustrace/otázky/triggery, bez jmen). Co přesně: `references/viral-ad-board.md` → „Co plní MODEL".
3. **Render** — `python3 {baseDir}/scripts/scout.py viral-render "<téma>"` → `viral-ad-board.html` (zobrazí 10/sekce + „načíst dalších"). Golden pár: `assets/viral-ad-board-example.{json,html}`.

**Krátká vs dlouhá:** short (reels/shorts) = hooky+formáty, long (YouTube dlouhé/podcast/LinkedIn) = úhly+argumenty (LinkedIn/long-form podmíněné B2B tématem). **Ke klientovi vše česky** — anglicismy (hook, awareness, share of voice, feed) jen interně.

**Sanitizace tu je nízké riziko** (reklamní knihovny + veřejná organika = veřejné registry) — Meta/Google jmenovat SMÍŠ; řádek „zdroje" držíme obecný pro čistotu. Srovnávače se netýkají.

## Competitor Ad Board — když je osa ZNAČKA (doména konkurenta)

Co **konkrétní konkurent** platí v reklamách → jeho ověření **vítězové ke klonování** + **mapa úhlů s dírou** (kde na něj zaútočit) + **útočný plán 3 tahy** s hotovým zadáním pro AI Marketéra. Spec + schéma contractu + „Co plní MODEL": **`references/competitor-ad-board.md`**. (≠ skill `competitor-tracker` — to je širší hlídka CMO; tohle je ad-focused board ad-scoutu.)

1. **Fetch + kostra** — `python3 {baseDir}/scripts/scout.py comp-fetch "<doména>" --brand "<Značka>" --market cz [--client-domain <klient>]`. **VŽDY nejdřív `--dry-run`** (odhad ~$0,12 + STOP). Krok 0 běží ZDARMA: homepage konkurenta → **pixel-router** (jaké reklamní kanály jede) + **FB stránka** (vstup pro knihovnu reklam bez hledání ID) + sitemap (skryté kampaňové LP). Pak placené: **knihovna reklam Meta per stránka** (všechny aktivní reklamy značky) + **registr transparentnosti Google podle domény** (Search/YouTube/Display/Shopping) + vyhledávání. Deterministicky sestaví `competitor-contract.json` (koncepty + varianty, winner skóre **dosah EU × varianty** — dny běhu jen sekundárně, stat row, deep-linky do registrů). Denní cache per doména.
2. **Doplň sémantiku (TVOJE práce jako modelu):** `vitezove` (smíš kurátorovat z celého poolu v raw.json — diverzita úhlů; nm česky + orig, úhel per obor, fáze povědomí, **typ — označ image/náborové kampaně, ty se neklonují jako výkonové**, 3× why, `klon` = jak kostru přenést na produkt klienta) · `mapa_utoku` (**úhly × 3 pásma trychtýře** `vrsek/stred/spodek` s počty ze VŠECH reklam; u každého řádku **`relevantni`** = fáze, kde úhel dává smysl — nerelevantní prázdné buňky = šedé „—"; `prilezitosti` = **min 6** zelených buněk, každá s **`pokyn`** co přesně udělat) · **`google_reklamy` — vision kontrola trhu** (registr vrací všechny trhy inzerenta → zahraniční kusy `mimo_trh` + poznámka `google_expanze`; v mřížce musí zbýt ≥12 domácích) · **`stat.registr_total`** — reálné počty přečti **browser toolem** z obou registrů (žádný scraping, 2 page loady) · `utocny_plan` (3 tahy: ① KLONUJTE ② OBSAĎTE DÍRU ③ UDEŘTE NA SLABINU — každý s `handoff` = hotové zadání pro AI Marketéra). Kostru lze kdykoli přestavět z cache bez kreditů: `comp-build "<doména>" --brand "<Značka>"`. Detaily: reference → „Co plní MODEL".
3. **Render** — `python3 {baseDir}/scripts/scout.py comp-render "<doména>"` → `competitor-ad-board.html`. **Handoff:** v Command Center založ tahy z `utocny_plan` jako tasky pro AI Marketéra přes task API (payload = `handoff` text); v HTML boardu má klient tlačítko, které zadání zkopíruje.

**Poctivost:** brandové/náborové kampaně běží dlouho bez ohledu na výkon → **nikdy je nedoporučuj klonovat jako výkonové** (štítek na kartě). Řídká data přiznat („konkurent teď skoro neinzeruje — jedeme po webu, LP a vyhledávání"), ne natahovat prázdné sekce. **Nikdy nerehostuj cizí kreativu** — jen destilát + náhled k rozboru + deep-link do oficiálního registru.

## Search Ad Board — když je osa VYHLEDÁVÁNÍ (klíčové slovo v aukci)

**Kdo platí za vaše zákazníky ve vyhledávání** na slovo → jejich reklamy k převzetí (s hotovými klony na klienta), mezera ve slovech s cenou za klik, landing rozbor konkurence, semafor rozpočtu a plán na 30 dní. Spec + schéma + „Co plní MODEL": **`references/search-ad-board.md`**.

1. **Fetch + kostra** — `python3 {baseDir}/scripts/scout.py search-fetch "<slovo>" --market cz --client-domain <klient>`. **VŽDY nejdřív `--dry-run`** (odhad ~$0,15–0,25 + STOP). Živý placený blok SERP (slovo + související + probe pokrytí) + **registr Google per top inzerent** (ověření: kolik reklam, jak dlouho) + **keyword metriky** (objem/CPC → mezera) → `search-report.json`. Denní cache per slovo.
2. **Doplň sémantiku (TVOJE práce jako modelu):** `proc_nebezpecny` u top bidderů · **`klon`** u reklam k převzetí (na produkt KLIENTA) · `zamer/pozn` u mezery · **`landing_gaps` přes browser tool** (otevři landing top 3 a vyplň slib/cenu/CTA/trust/co chybí + `landing_pointa` + `landing_stavba`) · `budget_semafor` (benchmark + příklad rozpočtu, vše rámuj jako odhad) · `action_plan` (3 kroky s časováním). Rebuild kostry sémantiku zachovává (merge). **Doporučená landing = advertorial → výroba přes skill `article-writer` (typ prodejní článek)** — board mezeru najde, article-writer stránku napíše; klientovi „zadejte AI Marketérovi".
3. **Render** — `python3 {baseDir}/scripts/scout.py search-render "<slovo>"` → `search-ad-board.html`.

**Poctivost:** SERP je momentka + capnutý fetch → počty rámuj jako **vzorek**; SERP-only hráči bez registru = možná nárazoví (`provereno`); odhady CPC = plánovač, ne slib.

## Viral DNA Card™ — když je osa JEDEN DONOR (URL kusu)

Hloubkový rozbor **jednoho vítěze** (reklama NEBO organický obsah) → DNA karta = **klon-šablona pro makery** (krok Dekóduj-hloubka → vstup Neural Clone). Spouští se URL („rozeberte mi tuhle reklamu / tohle video", drill-down z boardu). Dvě úrovně v1: **(A) kondenzát** = 3 mini-karty přímo ve Viral Ad Boardu (`dna_kondenzat`, default, skoro zadarmo) + **(B) standalone full karta** (postup níže, ~$0,10–0,18). Plný spec + schéma + „Co plní MODEL": **`references/viral-dna-card.md`**.

1. **Fetch + kostra** — `python3 {baseDir}/scripts/scout.py dna-fetch "<URL>" --tema "<téma>"`. **VŽDY nejdřív `--dry-run`** (odhad + STOP). Stáhne meta donora (chainy per síť, vč. Ad Library deep-linku) + náhled + podle formátu: **krátké** = video → 6 framů (ffmpeg zdarma) + titulky/transkripce; **dlouhé** = jen přepis (titulky first) + 1 náhled. K tomu komentáře publika (cap 60, bez jmen). Denní cache per donor → `/documents/ads/scout/dna/<sit>-<id>/<datum>/dna-card.json`.
2. **Doplň sémantiku (TVOJE práce jako modelu):** `donor.nm` česky + `orig` + `proc_donor` · **`vizualni_dna` — PROHLÉDNI thumb + framy očima (vision)** · `textova_dna` + `kostra` (z přepisu, když je) · `prepis.hook_3s` · `publikum` (destilát z `_surovina.komentare`, VŽDY česky, `{q, e}`) · **`klon` V/H/U/F přeložený na produkt klienta** = hotové zadání pro makery. Detaily: reference → „Co plní MODEL".
3. **Render** — `python3 {baseDir}/scripts/scout.py dna-render "<URL>"` → `viral-dna-card.html`. Karta je **interní podklad** (pill v hlavičce) — cizí kreativa se jen analyzuje, nerehostuje; do klientských kampaní jde až klon od makerů.

**Kondenzát (A) v boardu:** build boardu předvyplní `dna_kondenzat` (TOP-1 Reklama · Organika · Longform) — doplňte `hook · proc · inspirace` (max ~5 řádků/kus, jinak board přeteče) a renderer ukáže sekci „Viral DNA — nejlepší kus z každého světa". Nevyplněné kbelíky se nekreslí.

## Krok 0 — poznej, že jde o produkt

Board spusť, když dostaneš **název produktu** (od uživatele, nebo z Product DNA klienta při chystání kampaně). Zjisti:
1. **Produkt** — přesný název + varianta, na kterou se cílí (velikost/barva). Bez konkrétní varianty se ptej — srovnávat jinou variantu = falešný cenopád.
2. **Klient** — čí je to e-shop (doména), aby se jeho řádek zvýraznil a počítala se „vaše pozice".
3. **EAN, pokud je** — z produktového feedu klienta. Bez EAN je párování produktu fuzzy; když EAN není, po fetchi **jednorázově potvrď s klientem, že nalezené nabídky jsou opravdu tentýž produkt** (ne jiná varianta).

## Krok 1 — cache (šetři kredity)

Run-dir: `/documents/ads/scout/products/<slug>/<datum>/`. Když existuje běh na stejný produkt **z dneška** → použij ho (`build` z něj), nefetchuj znovu. Denní snímek stačí — **neprodávej to jako real-time**. `refresh=true` v zadání = nový běh.

## Krok 2 — dry-run (POVINNÉ před pálením kreditu)

```bash
python3 {baseDir}/scripts/scout.py fetch "<produkt>" --market cz --dry-run
```
Vrátí odhad počtu výsledků + ~$ za výpis. **STOP a ukaž odhad**, než pustíš ostrý fetch. Kredity jsou klientské peníze.

## Krok 3 — fetch (ostře, s capy)

```bash
python3 {baseDir}/scripts/scout.py fetch "<produkt>" --market cz --client-domain <domena>
```
Stáhne přes provider (konkrétní aktory jsou **interní** — viz `references/data-sources.md`, do výstupu nikdy nejdou):
- **Ceny a nabídky** — cena, doprava, dostupnost, varianty + hodnocení a recenze všech obchodů na produkt.
- **Výsledky vyhledávání** (CZ) — organické (kdo se zobrazuje) + placené (kdo bidují) + AI přehled.
- **Veřejná knihovna reklam** — inzerenti, kteří na produkt/značku jedou reklamy, + doba běhu (winner proxy).

Capy jsou natvrdo ve scriptu; provider je pay-per-result (útratu vidíš v dashboardu). **Bez `APIFY_API_KEY`** fetch přeskočí placené → jdi na Krok 4 (volné zdroje).

## Krok 4 — doplň volné zdroje sám (když chybí klíč nebo aktor)

Do `run-dir/agent_items.json` doplň, co script nestáhl:
- **Výsledky vyhledávání** jdou i přes `web_search` / browser tool (kdo se zobrazuje na produkt).
- **Cenový zdroj** (srovnávač) blokuje prostý fetch (403) → **přednostně přes provider aktor (Apify, proxovaný)**. Browser tool jen když provider selže **a jde vést přes proxy** — z holé IP klientského VPS srovnávač nikdy nescrapuj (viz guardrail), radši sekci vynech a poznamenej.
- **Knihovna reklam** jde přes Meta Ad Library API (MCP `ads_library_search`). Bez ní sekci vynech a poznamenej, že chybí.

## Krok 5 — build (signály + machine JSON + board)

```bash
python3 {baseDir}/scripts/scout.py build "<produkt>"                 # scout-report.json (machine contract)
python3 {baseDir}/scripts/scout.py build "<produkt>" --board          # + Product Intelligence Board HTML
```
Script spočítá signály a zapíše **machine contract** `scout-report.json` (co konzumuje `ad-strategist`) a na `--board` vyrenderuje HTML z `assets/board-template.html`. Signály (spec a scoring: `references/product-intelligence-board.md`):

1. **Cenová mapa** — kdo prodává, za kolik, **včetně dopravy (landed)**, min/medián/max, vaše pozice.
2. **Živé signály** — kdo dnes zlevnil (cenopád) · komu došlo zboží (out-of-stock trigger = nejakčnější).
3. **Cenový index** — jedno číslo „jste na X % mediánu".
4. **Recenze → náměty do reklam** — z chval a stížností postav konkrétní reklamní úhly (mechanismus + zdroj + proč). To je **tvoje práce jako modelu** — script dá surová +/−, ty vyrobíš náměty.
5. **Sortiment — díra** — které varianty konkurence prodává a klient ne (doložená poptávka).
6. **Google — kdo se zobrazí** — organický žebříček + kdo bidují + AI Overview.
7. **Reklamní aktivita (Meta)** — kdo jede reklamy a jak dlouho (winner proxy). **Inzerent-level**, ne přesný produkt — tak to i popiš.
8. **Akční plán** — 3–4 konkrétní tahy pro klienta z výše uvedeného.

## Krok 6 — dopiš to, co script neumí (TVOJE práce jako modelu)

- **Náměty do reklam** z recenzí (**min 4, ideálně 6** — ať mřížka není prázdná): pro každý silný signál (chvála i stížnost) vyrob **headline + mechanismus + zdroj (z které recenze) + proč funguje**. Nejčastější stížnost → nejsilnější námět (řeš servisem, ne slevou). **Pozor:** stížnost na samotný produkt (ne na obchod) neslibuj opačně — směřuj na výměnu/poradenství.
- **Akční plán** — z cenové mapy, dostupnosti a Meta díry poskládej 3–4 tahy.
- **Relevance sémanticky** — nalezené nabídky posuď významem, ne slovem: je to opravdu tentýž produkt/varianta? Off-topic vyhoď.

## Krok 7 — výstup

- **Interní / pro `ad-strategist` (default):** vrať **jen destilát** — pozice v ceně, nejakčnější signál (out-of-stock / cenopád), top 1–2 náměty, největší díra. Machine contract je v `scout-report.json`, **nevlévej ho do konverzace**.
- **Klientovi** (na vyžádání „ukaž mi to"): **Product Intelligence Board** HTML. **Vykání**, žádný „druhý mozek". **🛑 Sanitizace rizikově vázaná:** nikdy nejmenuj **srovnávače** (Heureka/Zboží) ani metodu sběru (Apify/„scraping/snapshot/DPA") — databázové právo. **Reklamní registry (Meta Ad Library, Google Ads Transparency) + kanály** (Google, Facebook/Instagram) jmenovat **SMÍŠ**. U srovnávačů generická formulace „z veřejných tržních zdrojů". Detail + seznam zakázaných slov: `references/output-sanitization.md`. Renderer to už drží. Footer „CliqSales · Ad Scout".

## Jak to konzumuje Ads Engine

`ad-strategist` čte `scout-report.json`: cenová pozice + dostupnost → objective/nabídka, náměty z recenzí → creative úhly, Meta díra → kde chybí klientova reklama. Board je jen vizuální pohled na tentýž běh (z cache = 0 kreditů).

## Wiki (AI Data Center) — když je k dispozici

Mechanismus = `WikiManager` (na fleetu syncuje markdown→wiki, drží i Brand/Product DNA). **Elegantní fallback:** když wiki nebo daný typ karty na instanci není, přeskoč **BEZ chyby** a klientovi nic nehlas. Wiki je **zrcadlo** — provozní pravda zůstává v souborech (`scout-report.json`, `voice-of-customer.json`). Scout je *outward-looking* → píše jiné vrstvy než `ad-analyst`.

| Co (jen destilát / insight, ne data) | Vrstva | Konvence |
|---|---|---|
| **DNA karta konkurenta** (`hook · kostra · úhel · formát · proč`) | Entity — **Firma + štítek `konkurence`** | Sjednoceno s `competitor-tracker` (žádný nový typ karty, agregát přes WikiManager). |
| **Product Intelligence destilát** | Entity — **Produkt** | Cenová pozice · díra v sortimentu · top 1–2 náměty. Insight, ne data. |
| **Raw Diet / voice-of-customer** | **Zdroje** | Jazyk zákazníka + awareness. Bez jmen (GDPR). |
| **Knihovna hooků / mapa úhlů** | **Koncepty** | Znovupoužitelné vzorce — najde je příští kampaň přes wiki hledání. Sem tečou i **vlastní výherci** (níže). |

**🛑 Tvrdé caveaty (drž striktně — proto to není triviální zápis):**
1. **Databázová práva** — NIKDY nerehostuj agregaci srovnávače (Heureka) jako data do wiki; jen insight/destilát. Wiki žije u klienta = neukládat cizí DB.
2. **Copyright** — NIKDY nerehostuj cizí reklamní kreativu (obrázek/video/copy) do wiki; jen **DNA destilát textem**.
3. **Sanitizace** — nejmenovat srovnávače ani metodu sběru ani ve wiki (stejné pravidlo jako u boardu).
4. **GDPR** — recenze/komentáře bez jmen autorů.
5. **Fallback** — chybí wiki / typ karty → skip bez chyby, klientovi nehlásit.

**Konzistence rodiny:** kartu **Kampaň** píše `ad-strategist` (Entity) a výkon dopisuje `ad-analyst` — **scout do ní nesahá**. Scout přispívá **Firma / Produkt / Zdroje / Koncepty**.

**Vlastní výherci (compounding smyčka):** `ad-analyst` vrací vítězné bloky zpět do scoutu (`evergreen-ads.json` → `own-winners.json`). Scout je bere jako **volitelný vstup Viral Ad Boardu** (donoři označení „VÁŠ VÝHERCE", **vyjmuti ze sanitizace** — je to klientova vlastní kreativa) a jejich úhly/hooky ukládá do vrstvy **Koncepty**. Kontrakt: `references/viral-ad-board.md`.

## Guardraily
- **🔒 Cesty — struktura `/documents/ads/` je FIXNÍ.** 1. úroveň (`campaigns/ · scout/ · sets/ · video/ · reports/ · pixel-capi-audits/ · ad-score/ · evergreen-ads.json`) je daná — **NIKDY tam nezakládej novou složku** (žádná složka se jménem kampaně/značky přímo pod `ads/`, jinak se v tom reporty ztratí). Nové kampaně/běhy/sady = vždy **PODsložka**. Ty píšeš **jen** do `scout/` (`products/` · `keywords/` · `competitors/` · `dna/` · `assets/`) — běhy jako `{slug}/{datum}/`.

- **Kredity = klientské peníze:** vždy nejdřív `--dry-run`; STOP před ostrým fetchem; denní cache místo opakovaných běhů.
- **🛑 Sanitizace výstupu (rizikově vázaná):** povinné skrýt **jen zdroje s ToS/právním rizikem = srovnávače (Heureka, Zboží)** — nikdy jménem. **Veřejné registry (Meta Ad Library, Google Ads Transparency) + kanály SMÍŠ jmenovat.** Apify/„scraping"/„snapshot" vynech kvůli čistotě, ne právu. Renderer drží obecný default. Detail: `references/output-sanitization.md`.
- **🛑 Kudy scrapovat (ochrana infrastruktury):** ceny/recenze/vyhledávání tahej **VÝHRADNĚ přes Apify** (jejich IP + proxy absorbují ToS/ban riziko) — **NIKDY přímo z klientského serveru** (rate-limit/ban by dopadl na klientovu IP a zanechal stopu). Když padáš na browser fallback, i ten veď přes proxy, ne z holé IP klientského VPS. Produktovou fotku **stahuj lokálně** (ať v HTML není CDN doména zdroje).
- **🛑 Databázová práva (srovnávače):** srovnávač (Heureka) **JE jádro** — jeden scrape/produkt dá všechny nabídky; scrapovat každý e-shop zvlášť je horší (víc webů/expozice). Riziko drž přes *jak a kolik*: **jen per-produkt na vyžádání** (nepodstatná část DB), **nikdy hromadně katalog**, **nikdy neukládej/neredistribuuj jejich agregaci jako data** (jen insight pro klienta); přes Apify. Reklamní knihovny (Meta/Google) = nízké riziko. Detail: `references/data-sources.md` → „Právní / ToS riziko".
- **EAN / varianty:** bez jistoty, že jde o tentýž produkt a stejnou variantu, board **lže** — radši potvrdit match, než ukázat falešný cenopád.
- **Pořadí obchodů u cenového zdroje = biddované (CPC)**, ne kvalita. Knihovna reklam = **inzerent-level**. Neslibuj real-time (denní snímek).
- **Žádný přímý shell** — vše přes `scout.py`. **GDPR** — recenze i komentáře bez jmen autorů (provider je strhává už na hranici).
- **🛑 Wiki (AI Data Center):** zapisuj **jen destiláty** do vrstev Firma+štítek `konkurence` / Produkt / Zdroje / Koncepty — **nikdy syrová data srovnávače ani cizí kreativu**; scout **nesahá** do karty Kampaň; chybí-li wiki → skip bez chyby. Viz sekce **Wiki** výše.
- **Bez klíče se nikdy nezastav** — jeď z volných zdrojů a poznamenej, co chybělo.
