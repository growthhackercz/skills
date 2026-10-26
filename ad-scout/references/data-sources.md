# Datové zdroje — ověřené aktory, inputy, ceny (INTERNÍ)

> 🛑 **INTERNÍ dokument. Názvy zdrojů/aktorů níže se NIKDY nedostanou do klientského výstupu** — viz `output-sanitization.md`. Ve výstupu jen „veřejně dostupná tržní data / výsledky vyhledávání / veřejná knihovna reklam".

Ověřeno v návrhové session (2026-07-12) na produktu „Venum Challenger 4.0", trh CZ. Ceny jsou pay-per-result (útratu vidíš v Apify dashboardu). Aktory jsou **konfigurovatelné přes env** (`AD_SCOUT_PRICE_ACTOR` / `_REVIEWS_ACTOR` / `_SEARCH_ACTOR` / `_ADLIB_ACTOR`) — provider je zaměnitelný.

## ⚖️ Právní / ToS riziko podle typu zdroje (řídí sourcing)

Dvě různá rizika, ne stejná (laický rozbor, ne právní rada — při škálování ověřit s právníkem):

- **Reklamní knihovny (Meta Ad Library, Google Ads Transparency) = nízké riziko.** Jsou to **veřejné transparency registry, které platformy samy zveřejňují** (Meta má i oficiální API), dělané aby byly veřejné → databázová práva se prakticky neřeší. **OK.**
- **Srovnávače / agregátory (Heureka, Zboží) = reálné riziko.** Jejich hodnota JE ta sestavená databáze (ceny + nabídky). Chrání ji **zvláštní právo pořizovatele databáze** (sui generis, směrnice 96/9/ES, v ČR autorský zákon) proti extrakci **„podstatné části"** + ToS zakazují automatický sběr. **Týká se Product Intelligence Boardu.**

**Mitigace — srovnávač ZŮSTÁVÁ jádro** (jeden scrape/produkt = všechny nabídky; scrapovat každý e-shop zvlášť je HORŠÍ — víc webů, víc scrapingu, víc expozice, víc práce). Riziko držíme přes *jak* a *kolik*, ne přes změnu zdroje:
1. **Jen per-produkt na vyžádání** — jeden produkt klienta = *nepodstatná* část jejich databáze. NIKDY hromadně nesklízet katalog (= „podstatná část") ani systematicky projíždět celý sortiment.
2. **Neukládat/neredistribuovat jejich agregaci jako data** — vše transformovat na *insight pro jednoho klienta*, nikdy nebudovat konkurenční srovnávač.
3. **Přístup přes Apify/proxy** (mimo klientův server).
4. Google Shopping / feed klienta + EAN jsou jen **volitelný doplněk k ověření matche**, ne náhrada srovnávače.

## 1. Ceny + dostupnost + varianty + recenze (cenový srovnávač)

Jeden denní běh dá nabídky všech obchodů spárované na produkt + hodnocení + recenze. **Zdroj blokuje prostý HTTP fetch (403)** → přes provider aktor nebo browser tool (Chrome).

Potvrzené aktory ve Store (2026-07-12):
- **Ceny/nabídky:** `cashmere_verdict/heureka-product-scraper` (id `OmIWDdYCaj5Ux0eg5`, PAY_PER_EVENT `~$0,009/result`, 94,5 % úspěšnost). Input: `searchKeywords` (array), `includeOffers`, `includeSpecs`, `maxItems`, `startUrls`, `proxyConfiguration`.
- **Recenze:** `stealth_mode/heureka-reivews-scraper` (id `uyrAwxMUzYVbVdFqM`, `~$0,003/result`) — strukturované pros/cons; **bez jmen autorů** (GDPR). Volná alternativa: `yurko/actor-heureka-shop-reviews` (FREE).
- **Alternativa s 30+ poli/variantami:** `stealth_mode/heureka-product-search-scraper` (id `kSJ8AMLKNg3zWGjnr`, `~$0,003/result`).
- Fallback proti fragilitě: vlastní Playwright / browser tool.

Bereme: **cena, doprava (→ landed), dostupnost, hodnocení %, počet recenzí, texty recenzí (pros/cons), varianty (velikost/barva), logo obchodu.**

## 2. Google SERP (CZ) — kdo se na produkt zobrazuje

Apify `apify/google-search-scraper`. Ověřený input:
```json
{"queries":"<produkt>", "resultsPerPage":20, "maxPagesPerQuery":1,
 "countryCode":"cz", "languageCode":"cs", "mobileResults":false}
```
Vrací: `organicResults[]` (kdo se zobrazuje zdarma — pozice + doména), `paidResults[]` (kdo bidují — vč. sitelinks s inzerenty), `aiOverview` (koho Google cituje), `relatedQueries` (poptávkové signály). Náklad ~$0,003/dotaz (10 s běh). Data zploští: array pole čti přímo (`organicResults`, `paidResults`), ne přes dot-notaci projekci.

Reálně vrátilo: 9 organických (Sportisimo, BJP #2, FITexpert…), 1 placený blok se 4 inzerenty (FITexpert, BJP, Venomshop, Fighter-Shop), AI Overview cituje Srovnáme/Sportisimo/BJP.

**Fallback SERP** (`provider.SERP_FALLBACK_ACTOR`, env `AD_SCOUT_SERP_FALLBACK_ACTOR`): `igolaizola/google-search-scraper-ppe` — jen ORGANIKA ($0,15/1000 výsledků; input `{query, maxItems, country, language, domain}`). ⚠️ Paid add-on umí jen `apify/google-search-scraper` — záskok je degradace (placený blok označen `_paid_unavailable`), ne náhrada.

**Keyword metriky** (`provider.KEYWORD_CHAIN`): `s-r/google-keywords` → `burbn/semrush-keyword-magic-tool` (expanze seedu). **Dohled objemů per KONKRÉTNÍ slovo** (`provider.keyword_volumes`, env `AD_SCOUT_KWVOL_ACTOR`): `iskander/google-keyword-search-volume-api` — bulk `{keywords[], location_name:"Czechia", language_code:"cs"}`, ~$0,6/batch do 1000 slov, CPC vrací v USD (provider převádí na Kč); fallback = expanzní chain se slovem jako seedem. Ověřeno naostro 2026-07-13 („kreatin pro ženy" 480/měs, „gummies" 590/měs — expanzní actory je neznaly).

## 3. Knihovna reklam (Meta Ad Library) — kdo jede na téma reklamy

**Zdroj = Apify ad-library actory na `APIFY_API_KEY`** (bez Meta účtu, bez loginu → univerzální pro celý fleet; GHL klienti Meta API stejně nemají). Meta MCP `ads_library_search` je jen DEV nástroj (vyžaduje ad account, na serveru NENÍ). Fallback chain `provider.AD_CHAIN` (env přepíše #0 = `AD_SCOUT_ADLIB_ACTOR`):

| # | Actor | vstup | pozn. |
|---|---|---|---|
| 0 | `brilliant_gum/facebook-ads-library-scraper` | `searchTerms[]` + `countries[]` | trackuje dny běhu; často 403 → padá na #1 |
| 1 | `automation-lab/facebook-ads-library` | `searchQueries[]` + `country` | „no login / no Meta token"; vrací **`imageUrls`/`videoPreviewUrls`/`videoUrls`** (náhledy!) — hlavní tahoun |
| 2 | `apify/facebook-ads-scraper` (oficiální) | `startUrls[]` (Ad Library URL) | media v `snapshot.images[]`/`snapshot.videos[]` |

Pravidla (v kódu):
- **Dotaz frázově česky** („bojové sporty"), NE holá zkratka („MMA" = 371 tis. globálního webnovel spamu). `currency` (CZK/EUR) + `_lang_ok` dočistí.
- **Jen konkrétní reklamy** — dynamické katalogy (`{{product.description}}`) vyloučeny (`_is_concrete_ad`).
- **Náhled = obrázek NEBO video** (`_ad_media_urls`) — poster + přehrání v popupu; nikdy logo inzerenta (`pageProfilePictureUrl`). fbcdn URL se stahují lokálně (`dl_thumb`).
- **CZ→zahraničí** (SK/DE/AT/PL/US/GB): CZ < 10 konkrétních → doplní na TOP 10 (badge GLOBÁL).
- **Video díra = největší příležitost:** CZ nejede video (`pokryti.cz_video` nízké) → dotáhne nejúspěšnější zahraniční VIDEOreklamy jako inspiraci.

Winner proxy = délka běhu (dnes − start). Ověřeno naostro (Kreatin CZ, 2026-07-13): 13 konkrétních / 10 inzerentů, Zdravy-Protein 365 dní, Ronnie 295 dní; **7 z 13 video s náhledem**.

## 4. Organika — KEYWORD SEARCH discovery + komentáře (Viral Ad Board)

**Discovery podle TÉMATU (keyword), ne hashtagu/watchlistu** (`provider.content_search`, chainy `provider.SEARCH_CHAINS`, env přepíše #0 = `AD_SCOUT_*_SEARCH_ACTOR`). Každá síť = **fallback chain** (primární spadne/prázdno → další):

| Síť | Chain: primární → zálohy | Pozn. |
|---|---|---|
| TikTok | `clockworks/tiktok-scraper` → `apidojo/tiktok-scraper` → `clockworks/free-tiktok-scraper` | search mode; **geo-cílení na všech** (`proxyCountryCode`/`location`) |
| YouTube | `streamers/youtube-scraper` (`searchQueries[]` + `maxResultsShorts`) → `thedoor/youtube-video-search` → `khadinakbar/youtube-search-scraper` (`country`) | `maxResultsShorts` = i Shorts |
| Instagram | `apify/instagram-scraper` (**nativní `search`**) → hashtag explore → `apify/instagram-api-scraper` | IG nativní search vrací málo (slabý zdroj obecně) |
| Facebook | `scraper_one/facebook-posts-search` → `powerai/facebook-post-search-scraper` → `scrapeforge/facebook-search-posts` | junk filtr níže |
| **FB + IG naráz** | `seibs.co/meta-content-intel` | keyword napříč FB+IG + engagement + téma |
| LinkedIn | `harvestapi/linkedin-post-search` → `datadoping/linkedin-posts-search-scraper` → `lofomachines/linkedin-post-search-scraper` (`country`) | **B2B dlouhý obsah**, jen s `--b2b` |

- **Lokální obsah má přednost, EN jen doplněk:** český dotaz jede s **geo-cílením** (`market` → TikTok `proxyCountryCode=CZ`; YouTube i Shorts přes `maxResultsShorts`) — bez toho vrací globálně nejpopulárnější = cizí jazyk (mnoho termínů je cizojazyčně dominantních, „kreatin" = i němčina). Teprve když je lokálního < 20/síť → `--en <english>` doplní **globálně** (`market=None`), dedup dle URL. Build řadí lokální (`geo != cz`) první — EN nikdy nepředběhne.
- **Jazykový filtr `_lang_ok`:** drží jen **CZ/SK/EN**; ostatní jazyky (špan./něm./indonéš.…) ven. Pozor na falešné přátele (`creatinine` ≠ `creatine`).
- **Junk filtr `_is_content_junk`:** bazar/inzeráty + zpravodajské weby (Sport.cz, deník…) ven; tvůrčí obsah, podcasty, brandové posty projdou.
- **Časový limit NENÍ tvrdý** — engagement napřed, `since` jen široká pojistka (12–18 měs.). TikTok covery z `videoMeta.coverUrl` (Apify KV store, žije s `?token`).

**Komentáře (Raw Diet / jazyk zákazníka)** — chainy `provider.COMMENT_CHAINS`, vstup = URL top organiky (veřejné posty, **BEZ loginu** — Apify residential proxy, ~99 % success):
- IG: `apify/instagram-comment-scraper` → `apidojo/instagram-comments-scraper-api` → `louisdeconinck/instagram-comments-scraper`
- FB: `apify/facebook-comments-scraper` → `expected_knight/…` → `thedoor/facebook-comment-scraper`
- YT: `streamers/youtube-comments-scraper` → `code-node-tools/youtube-comments-scraper` (YT bývá 403 — nejkřehčí kanál)
- TikTok: `clockworks/tiktok-comments-scraper` → `apidojo/tiktok-comments-scraper` → `scrapeforge/tiktok-comments-extractor`

Volá `scout._fetch_comments` (2 posty/síť × 40) → `comments.json` → model destiluje jazyk_zakaznika (**VŽDY česky**, 5/panel). GDPR: bez jmen autorů (strháváme v `_norm_comment`).

## Náklad na jeden výpis

Heureka (~$0,01–0,03) + Google SERP (~$0,003) + Meta (přes API ~zdarma / Apify ~$0,02) ≈ **$0,05–0,10 za výpis**. Denní snímky pro celý katalog ~$10–15/měs/klient; 4 ze 7 signálů (cenopád, out-of-stock, index, historie) = zdarma derivace z uložených snímků.

## Validační nálezy (ostrý běh 2026-07-12, Dyson V15 Detect Absolute)

- **Cenový aktor: `searchKeywords` samo vrací PRÁZDNO** (0 položek) i s `proxyConfiguration`. Hledací tok je nespolehlivý → **preferuj `startUrls`** (URL produktu na srovnávači, dohledej z výsledků vyhledávání) nebo **browser fallback** (Chrome), který v testu fungoval spolehlivě (9 nabídek + recenze + varianty). `proxyConfiguration: {useApifyProxy: true}` je POVINNÉ. Odkazy na obchody jsou maskované přes redirect → názvy obchodů ber z **alt textů log** (`img[alt]`), pořadí = pořadí nabídek.
- **Vyhledávání: CZ dotaz zakotvi česky.** Čistě anglický „Dyson V15 Detect" vrátil globální organiku (Dyson UK, Currys); „…vysavač cena" vrátilo CZ organiku (srovnávač, Dyson.cz, RobotWorld, Datart). Placené jsou CZ tak jako tak.
- **Knihovna reklam u prémiových značek = zaplavená podvody.** „Dyson V15" v CZ vrátilo 513 reklam, ale drtivě dropshipping/podvod (ceny „29 $", profily na jména osob, `.site` domény), žádný legitimní autorizovaný prodejce → v boardu podat jako **`meta_note`** (varování + příležitost pro důvěryhodnou kampaň), ne jako žebříček inzerentů.

## 5. Competitor Ad Board — zdroje per ZNAČKA (ověřeno ve Store 2026-07-13)

**Google Ads Transparency (vstup = doména)** — chain `provider.GT_CHAIN` (env přepíše #0 = `AD_SCOUT_GT_ACTOR`):

| # | Actor | vstup | cena | pozn. |
|---|---|---|---|---|
| 0 | `s-r/google-ads-transparency` | `domain` (required) + `region` (CZ v enum) + `ads_count` (max 100) | $0,01 start + $0,001/ad | **100 % úspěšnost**, 205 uživatelů/měs; Search/YT/Display/Shopping; `detail:true` = dražší per-ad detail (impressions/regions) — default OFF |
| 1 | `scrapesage/google-ads-transparency-scraper` | `domains[]` + `region` + `maxAdsPerSearch` | $0,002/ad | days active + per-country reach; 99,2 % |
| 2 | `solidcode/ads-transparency-scraper` | `searchQuery` + `region` + `maxResults` | $0,001/result | 1111 uživatelů, 99,3 %; nízký rating (2,2) → až poslední |

Deep-link zdarma: `adstransparency.google.com/?region=CZ&domain=<doména>`. Transparency **nemá reach/dosah** (mimo politické) — winner signál z Googlu = dny běhu (first/last shown) + formátový mix; dosah nese Meta.

**Meta Ad Library per STRÁNKA** — chain `provider.ADP_CHAIN` (env přepíše #0 = `AD_SCOUT_ADPAGE_ACTOR`):

| # | Actor | vstup | cena | pozn. |
|---|---|---|---|---|
| 0 | `automation-lab/facebook-ads-library` | **`pageUrls[]`** (URL FB stránky) + `country` | $0,005 start + $0,0005/ad | stejný actor jako keyword chain — bere i page URL, bez page ID; vrací media |
| 1 | `apify/facebook-ads-scraper` (oficiální) | `startUrls[]` | $0,005/ad | media v `snapshot.*` |
| 2 | `azzouzana/meta-facebook-instagram-ads-library` | `startUrl` (FB page / search URL) | $0,0005/result | 99,9 % úspěšnost |

**FB stránku konkurenta najdi ZDARMA:** `provider.landing_pixels(doména)` — homepage v patičce skoro vždy linkuje FB/IG/TikTok (ověřeno: bjp-store/gymbeam/ronnie/prom-in/czechvirus 5/5). Zároveň vrací **pixely** (Meta/TikTok/LinkedIn/Google/Sklik/GTM) = router: TikTok/LinkedIn moduly zapínej jen když je pixel. Fallback: vyhledávání „<značka> facebook". `provider.sitemap_lps(doména)` = skryté kampaňové LP (`/lp/ /go/ /akce/…`) zdarma.

**Náklad základního běhu:** Meta 100 (~$0,055) + Google 50 (~$0,06) + SERP ($0,003) + landing/pixely/sitemap (zdarma) ≈ **$0,12/konkurent**. ⚠️ `ads_count` u `s-r` actoru je jen orientační — reálně vrací i ~100 při cap 50 (→ ~$0,10 za Google část). Reálný běh: **$0,15–0,20/konkurent**.

**Validační nálezy (ostré běhy GymBeam + Ronnie.cz, 2026-07-13):**
- **Meta per-page (`automation-lab`, `pageUrls`): NEVRACÍ dosah (reach)** — winner skóre se opře o varianty + dny (varianty jsou stejně nejspolehlivější signál); renderer stat „Dosah top reklamy" automaticky nahradí „Nejvíc variant". Dny běhu z `startedRunningOn` fungují spolehlivě (112/283/484/654 dní ověřeno).
- **Actor přimíchá cizí stránky** (affiliate/influencer reklamy zmiňující značku — např. „Lake Smith Farm" se slevovým kódem u GymBeamu) → `scout._filter_brand_pages` drží jen stránku konkurenta (match jména, fallback dominantní stránka).
- **Google Transparency: domain lookup umí vrátit VÍC advertiserů** — „ronnie.cz" dalo Erasport, s. r. o. (= reálný provozovatel Ronnie.cz, ✓) + „Ronnie Berg" (švédské autodíly, ✗ fuzzy jméno). → `provider.filter_gt_advertisers` (jméno značky v názvu advertisera → jinak podíl CZ/SK textů → jinak největší skupina).
- **Text copy z Google registru:** `s-r` bez `detail:true` vrací text jen u části reklam (Erasport ✓ „akce 1+1 zdarma…", GymBeam ✗ prázdné) — Google blok proto řadí reklamy S COPY napřed a bez copy dává klikací náhled kreativy (`thumb` z registru funguje). Skutečné search headliny navíc spolehlivě dodá SERP (`paidResults` + sitelinks).
- **FB stránka z homepage: 5/5 testovaných e-shopů** ji má v patičce (`landing_pixels`) — SERP fallback nebyl potřeba.

## 6. Viral DNA Card — donor podle URL (ověřeno Store + naostro 2026-07-13)

**Jeden kus podle URL** (`provider.DONOR_CHAINS`, ≥2 fallbacky/síť) + záložní přepis (`TRANSCRIPT_CHAINS`) + komentáře donora přes stávající `COMMENT_CHAINS`. Kompletní tabulka aktorů, tvary vstupů, cost ladder (~$0,10–0,18/karta) a nálezy (TikTok ASR titulky = `videoMeta.subtitleLinks` VTT v KV, s ?token; YT `startUrls` chce `maxResults≥1`): **`viral-dna-card.md` → „Ověřené actory"**. Klíčové slugy: TikTok `clockworks/tiktok-scraper` (postURLs, covers+video+transkripce v 1 běhu) · YouTube `streamers/youtube-scraper` (startUrls + downloadSubtitles) · Ad Library deep-link `automation-lab/facebook-ads-library` (`adsLibraryUrls`).

## NEDOSTUPNÉ

- **Zboží.cz** — Apify aktor neexistuje. Nedávat.
- **Product-level Meta DPA matching** — nespolehlivé, jen inzerent-level.
- **Google Trends per-produkt (CZ)** — prázdné/šum, jen kategorie.

## Machine contract — `scout-report.json` (co konzumuje `ad-strategist`)

```json
{
  "board": "product-intelligence",
  "generated_at": "2026-07-12",
  "market": "cz",
  "trigger": {"type": "product_name", "query": "Venum Challenger 4.0"},
  "client": {"name": "BJP Store", "domain": "bjp-store.cz"},
  "product": {"name": "...", "category": "boxerské rukavice", "variant": "12 oz khaki",
              "ean": null, "rating_pct": 95, "reviews_count": 4, "image_url": "...", "shops_count": 12},
  "kpi": {"lowest_price": 1167, "lowest_shop": "Allegro", "your_landed": 1569,
          "price_index_pct": 94, "rank": 3, "rank_of": 9, "price_drops_30d": 2},
  "price_map": [
    {"shop": "Allegro.cz", "domain": "allegro.cz", "price": 1167, "shipping": 89,
     "landed": 1256, "note": "marketplace", "is_client": false, "is_min": true, "drop_pct": null,
     "logo": "https://www.google.com/s2/favicons?domain=allegro.cz&sz=64"}
  ],
  "signals": {
    "price_drops": [{"shop": "FITexpert", "pct": -11, "price": 1429, "delta": -176, "note": "..."}],
    "stock": {"out_of_stock": [{"shop": "FightMarket", "variant": "16 oz"}],
              "availability": [{"shop": "BJP Store", "status": "skladem"}],
              "trigger": "FightMarket vyprodal 16 oz → skladem u vás → zvedni bid"}
  },
  "reviews": {"praise": ["..."], "criticism": ["..."],
              "hooks": [{"headline": "...", "mechanism": "námitka → servis", "source": "...", "why": "..."}],
              "lead_hook": 1, "caution": "suchý zip = slabina produktu, neslibovat opak"},
  "assortment": {"have": ["16 oz černo-bílá", "..."],
                 "gaps": [{"variant": "10 oz Pearly Pink", "demand_evidence": "FITexpert inzeruje"}]},
  "search": {"organic": [{"pos": 1, "shop": "Sportisimo.cz"}, {"pos": 2, "shop": "BJP Store", "is_client": true}],
             "paid": ["FITexpert.cz", "BJP Store", "Venomshop.cz", "Fighter-Shop.cz"],
             "ai_overview_cites": ["Srovnáme", "Sportisimo", "BJP Store"]},
  "meta_ads": [{"advertiser": "Venomshop.cz", "domain": "venomshop.cz", "ads_count": 4,
                "running_since": "2026-02", "months": 5, "note": "katalogové reklamy na Venum", "level": "advertiser"}],
  "action_plan": [{"title": "Doprava, ne sleva", "body": "..."}],
  "cost_usd": 0.07,
  "sources": ["market-prices", "market-reviews", "search", "ad-library"],
  "caveats": ["ad-library=inzerent-level", "denní snímek, ne real-time", "EAN nepotvrzen — match ověřen ručně"]
}
```
