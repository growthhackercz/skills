# Competitor Ad Board — spec

Osa = **ZNAČKA** (vstup = **doména konkurenta**, např. `gymbeam.cz`). Cíl: majitel firmy vidí, **co konkurent dělá v reklamách**, a vytěží z toho (a) DNA ke klonování a (b) místa, kde na něj zaútočit. Rodina: Viral Ad Board (téma) · **Competitor Ad Board (značka)** · Product Intelligence Board (produkt). Plán a plná vize 9 sekcí: `documents/projects/ad-scout-handoff/competitor-ad-board-plan.md`.

> **Pozor na záměnu:** tohle je board v ad-scoutu (ad-focused). Skill `competitor-tracker` (CMO) je jiná věc — širší hlídka s diff eventy. Board si od trackeru půjčí mechaniky, ale je samostatný výstup ad-scoutu.

Build `scripts/compboard_build.py` (deterministická kostra) → renderer `adboard.render_competitor` (kind=competitor, stejný design language, CSS/SVG z `_adboard_assets.py` + `COMP_CSS`).

## Datové zdroje (JÁDRO — základní běh ~$0,12–0,25/konkurent)

| Zdroj | Jak | Cena |
|---|---|---|
| **Meta Ad Library per STRÁNKA** | `provider.page_ads(fb_page_url)` — chain `ADP_CHAIN` (page-based vstup) | ~$0,055 / 100 reklam |
| **Google Ads Transparency** (Search/YT/Display/Shopping) | `provider.transparency_ads(doména)` — chain `GT_CHAIN`, **vstup = doména** | ~$0,06 / 50 reklam |
| **Landing + pixel-router** | `provider.landing_pixels(doména)` — prostý fetch homepage, ZDARMA | zdarma |
| **Sitemap → skryté LP** | `provider.sitemap_lps(doména)` — `/lp/ /go/ /akce/…` = kampaně mimo registry | zdarma |
| **Vyhledávání (kontext)** | `provider.search_results` | ~$0,003 |

**Pixel-detekce = router ZDARMA:** homepage prozradí (a) reklamní pixely (Meta/TikTok/LinkedIn/Google/Sklik) → **zapínej jen moduly, kde pixel je** (TikTok/LinkedIn ad library = doplňkové moduly, v MVP nejsou), (b) **odkaz na FB stránku** → vstup pro `page_ads` bez hledání page ID. Fallback hledání FB stránky: výsledky vyhledávání („<značka> facebook“).

Konkrétní ověřené actory + fallback chainy: `references/data-sources.md` §5 (interní — nikdy do výstupu).

## Sekce MVP (stohované, vše česky, vykání)

| # | Sekce | Co ukazuje |
|---|---|---|
| **stat row** | 5 čísel | Aktivních reklam (Meta+Google split) · Nejdéle běžící (dní) · Dosah top reklamy v EU · Volné úhly · Nových za 30 dní |
| — | Reklamní kanály značky | chipy z pixel-routeru + deep-link do registru Googlu (kanály SMÍME jmenovat) |
| **01** | **Jejich vítězové** | TOP 10 konceptů dle skóre; karta = náhled, dny běhu, dosah EU, varianty, úhel + fáze povědomí, typ (výkonová/image/nábor), CZ překlad copy, 3× proč, **„Naklonovat na váš produkt“** + deep-link do knihovny. Pod tím kompaktní blok Google/YouTube reklam (formátový mix + headliny). |
| **02** | **Mapa úhlů — kde je díra** | matice úhly × fáze povědomí; buňky 🔴 plno (3+) / 🟡 slabé (1–2) / 🟢 volno (0); pod maticí `prilezitosti` (nejcennější zelené buňky s odůvodněním) |
| **03** | **Útočný plán — 3 tahy** | ① KLONUJTE vítěze ② OBSAĎTE DÍRU ③ UDEŘTE NA SLABINU — každý tah s tlačítkem **„Zadat AI Marketérovi“** (zkopíruje hotové zadání; v Command Center jde handoff přes task API) |

Zbylých 6 sekcí (recenze→protiúhly, hřbitov, hooky, offer teardown, rukopis, tempo) = plán, ne MVP.

## Winner scoring (poctivost — plán §3)

- **Skóre** (`compboard_build.score_comp`): `55·log10(dosah EU)/6 + 30·min(varianty,8)/8 + 15·min(dní,180)/180` — **primárně dosah × varianty**, dny jen sekundárně (brandové/náborové kampaně běží dlouho bez ohledu na výkon).
- **Varianty = nejspolehlivější signál** (5+ verzí téže copy = interní data konkurenta prosakují ven). Počítají se **per KONCEPT** (seskupení dle copy, ne per inzerent — všechny reklamy jsou téže stránky).
- **Typ kampaně:** nábor detekuje build deterministicky (klíčová slova); **image/brand označí model** (`typ:"image"`) — karta dostane štítek „Image kampaň — neklonovat jako výkonovou“.
- **Dynamické katalogy** (`{{…}}`) jdou mimo vítěze (nejsou klonovatelné), ale zůstávají ve stat row.
- **Řídká data přiznat:** konkurent skoro neinzeruje → říct to („jedeme po webu, LP, vyhledávání“), ne natahovat prázdné sekce.

## Co plní MODEL (sémantika — po `comp-fetch`, před `comp-render`)

Do `competitor-contract.json`:
- **`vitezove[]` — smíš KURÁTOROVAT z celého poolu konceptů** (raw.json), ne jen doplnit deterministický TOP 10: když deterministický výběr zaplaví 6 skoro identických always-on produktových reklam, vyměň část za reprezentativní koncepty jiných úhlů (launch vlna, video, obsah, sleva) — board má ukázat CELOU strategii konkurenta. Skóre karty ale počítej vždy deterministicky (`compboard_build.score_comp`), pořadí = podle skóre. (Pomůcka: `comp-build` přestaví kostru z cache za 0 kreditů.)
- **`vitezove[]` pole:** `nm` VŽDY česky (reálná copy konkurenta, přeložená; originál → `orig`; pravidla jako Viral board) · `uhel` (taxonomie PER TRH — přizpůsob oboru, ne default AI témata) · `aw` (fáze povědomí) · `typ` (potvrdit/označit image kampaně!) · `why` (3 odrážky: důkaz — dosah/varianty/dny · úhel · co si vzít) · **`klon`** (1–2 věty: jak kostru přenést na produkt KLIENTA — jeho jazykem, bez značky konkurenta).
- **`mapa_utoku`:** `{faze:["vrsek","stred","spodek"], radky:[{uhel, bunky:[N,N,N], relevantni:[faze…]}], prilezitosti:[{uhel, faze, proc, pokyn}]}` — **sloupce = 3 pásma trychtýře** (renderer je vykreslí s lidským popiskem: „ještě neví" / „hledá řešení — googlí" / „vybírá a je připraven koupit"), NE 4 fáze povědomí — trychtýř zná každý podnikatel. Mapování z povědomí: problem→vršek, solution→střed, product+most→spodek. Počty syt ze VŠECH reklam (Meta + Google), ne jen z TOP 10. Buňky obarví renderer sám (0=🟢, 1–2=🟡, 3+=🔴). `prilezitosti` = **MINIMÁLNĚ 6** zelených buněk; každá povinně s **`pokyn`** = praktický pokyn co PŘESNĚ udělat (formát, počet kusů, jak natočit/postavit — proveditelné bez další otázky). Renderer je skládá do karet ve dvou sloupcích („→ Udělejte:").
- **`radky[].relevantni` — POVINNĚ označ fáze, kde úhel dává reálně smysl** (např. „Sleva · výprodej · dárek" jen `most-aware` — sleva je z podstaty spodek trychtýře). Prázdná nerelevantní buňka se vykreslí šedě „—" a NEPOČÍTÁ se jako volno (jinak mapa hlásí desítky falešných příležitostí a působí amatérsky); buňka s reklamami se ukáže vždy (důkaz z registru přebíjí teorii). Stat „Volné úhly" pak renderer počítá deterministicky = zelené buňky po tomto filtru. `prilezitosti` vybírej JEN ze zelených (relevantních prázdných) buněk.
- **`utocny_plan`:** PŘESNĚ 3 tahy `{tah, titulek, popis, zdroj, handoff}`. Tahy: ① KLONUJTE (vítěz #1, pokud výkonový) ② OBSAĎTE DÍRU (nejcennější 🟢) ③ UDEŘTE NA SLABINU (protiúhel — z recenzí/serpu, dokud sekce 03 není, ber slabinu z mapy/копy). **`handoff` = hotové, samostatně srozumitelné zadání pro AI Marketéra** (co vyrobit, úhel, formát, na jaký produkt klienta) — vykání, žádná jména zdrojových nástrojů.
- **`google_reklamy[]` — VISION kontrola trhu:** registr vrací reklamy na úrovni INZERENTA (všechny jeho trhy), metadata doménu neobsahují — **prohlédni náhledy kreativ očima** (doména/jazyk je vidět ve screenshotu) a zahraniční kusy označ `mimo_trh: true` + `trh: "si|pl|hu|…"`. Mřížka pak ukáže jen domácí trh — **po filtru musí zůstat ≥12 domácích kusů** (proto pool `GOOGLE_SHOW=30`; když nestačí, vezmi další z raw.json). Pomůcka: build předznačí kusy s neprázdným textem mimo jazyk trhu a řadí kreativy s přímým obrázkem první.
- **⚠️ JS preview registru** (`…/ads/preview/content.js`) nejde vložit jako `<img>` ani spolehlivě vyrenderovat (Playwright vrací prázdno) — build je řadí na konec poolu, renderer u nich ukáže „náhled jen v registru". Počty v úvodu sekce rámuj jako **vzorek** (fetch je capnutý, plný registr je větší) — renderer to dělá automaticky.
- **`google_expanze`** (string | null): když zahraniční kusy existují, napiš 2–3 věty analytické poznámky (na jakých trzích jede, co to znamená pro klienta) — renderer ji ukáže pod mřížkou Google kreativ jako „🌍 Zahraniční expanze (z registru)".
- **`stat.registr_total` — reálné počty z registrů přes BROWSER TOOL (ne Apify!):** otevři v prohlížeči `kanaly.registry.meta_adlib` (nahoře „~N výsledků") a `kanaly.registry.google` („přibližně N reklam") a přečti první číslo na stránce → `{"meta": N, "google": N}`. Stat dlaždice pak ukáže skutečný rozsah (`~3 180`) a fetch z Apify zůstává jen levný vzorek (2 page loady místo scrapingu celého registru).
- **`stat.uhly_volne`** (počet 🟢 buněk) · volitelně **`meta.podtitulek`**.
- **Jazyk:** vše česky, vykání, žádné anglicismy na ploše (hook→úvodní hook, awareness→fáze povědomí).

## Handoff (sekce 03 → AI Marketér)

V HTML boardu tlačítko **zkopíruje** hotové zadání (lean-back klient ho vloží do chatu). V Command Center agent místo kopírování založí task pro AI Marketéra přímo přes task API (vzor competitor-tracker F1) — handoff text = payload tasku.

## Guardraily (navíc k SKILL.md)

- **🛑 Nikdy nerehostovat cizí kreativu** — board ukládá DNA destilát (copy překlad, úhel, proč) + náhled jen k rozboru + **deep-link do oficiálního registru** (řeší copyright i stale data).
- **Sanitizace rizikově vázaná:** reklamní registry (Meta Ad Library, Google Ads Transparency) + kanály SMÍME jmenovat; srovnávače NIKDY; Apify/metodu vynech. Rámování: „veřejná data z registrů, které EU přikázala zveřejnit“ — nikde slovo „špehování“.
- **GDPR:** až přibude sekce recenzí — bez jmen autorů.
- **Kredity:** `--dry-run` + STOP před ostrým během; denní cache per doména.
- **Wiki:** destilát vítězů → Entity **Firma + štítek `konkurence`** (konvence competitor-tracker), úhly/hooky → Koncepty. Jen text-destilát, nikdy kreativa. Fallback bez chyby.

## Machine contract (schéma)
```json
{
  "meta": {"skill":"ad-scout","vystup":"competitor-ad-board","trh":"cz","sken":"…",
           "konkurent":{"znacka":"GymBeam","domena":"gymbeam.cz"},"klient":{"domena":"…"},"podtitulek":"…|auto"},
  "stat": {"aktivnich_reklam":N,"meta_reklam":N,"google_reklam":N,"konceptu":N,"katalogovych":N,
           "nejdele_bezici_dni":N,"top_dosah_eu":N,"nove_30d":N,"uhly_volne":N},
  "kanaly": {"pixely":["meta","google-ads"],"site":{"facebook":"…"},"registry":{"google":"…","meta":"…"}},
  "vitezove": [{"poradi":1,"nm":"česká copy","orig":"originál|null","uhel":"…","aw":"problem-aware",
                "typ":null,"score":88,"dosah_eu":843842,"dni":132,"varianty":5,"site":["facebook","instagram"],
                "url":"…","thumb":"/abs.jpg","video_url":null,"why":["…","…","…"],"klon":"…"}],
  "google_reklamy": [{"nm":"…","format":"text|image|video","dni":N,"url":"…"}],
  "google_mix": {"text":N,"image":N,"video":N},
  "landing_pages": ["https://…/akce/…"],
  "serp": {"organic":[…],"paid":[…],"ai_overview":true},
  "mapa_utoku": {"faze":["problem-aware","…"],"radky":[{"uhel":"…","bunky":[3,1,0]}],
                 "prilezitosti":[{"uhel":"…","faze":"…","proc":"…"}]},
  "utocny_plan": [{"tah":"KLONUJTE","titulek":"…","popis":"…","zdroj":"vítěz #1 · 132 dní · 5 variant","handoff":"…"}],
  "pokryti": {"meta":N,"google":N,"koncepty":N,"vitezove":N,"landing_pages":N}
}
```
Render: `python3 scripts/scout.py comp-render "<doména>"` (nebo `adboard.py <contract.json> <out.html>` — pozná `vystup`).
