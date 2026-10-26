# competitor-tracker — datové kontrakty

Vše žije v `/documents/competitors/` (override: `--root` nebo env `COMPETITORS_ROOT`).
Soubory = kontrakt pro odběratele (ad-scout, stratégové, Obchodník, CEO) — **měnit jen zpětně kompatibilně**.

`patrol` drží po celý běh neblokující zámek `.patrol.lock`; druhý souběžný běh skončí před provider voláním. JSON a HTML se zapisují přes dočasný soubor a atomický `os.replace`. Poškozený JSON stav je terminální chyba k obnově ze zálohy, ne důvod tiše založit novou baseline. Jedinou výjimkou je `events.jsonl`, kde čtenář smí přeskočit jednotlivý poškozený řádek po přerušeném appendu.

```
/documents/competitors/
  watchlist.json                 ← zdroj pravdy sledovaných značek (vč. `ico` pro úřední stopu)
  events.jsonl                   ← append-only log eventů (1 JSON / řádek)
  history/<slug>/ads-YYYY-MM-DD.json   ← snapshot kreativ značky (po brand-filtru)
  history/<slug>/profile.json    ← agregát + interní stav diffu (milníky, killed archiv, velocity)
  history/<slug>/registry.json   ← úřední stopa (rejstřík): vedení, vlastníci, stav, flagy — diffuje se
  history/<slug>/wayback.json    ← archiv webu (cold start; vzniká 1×, při 503 se zkusí příště)
  profiles/<slug>.md             ← wiki-ingestible profil (agregát, štítek `konkurence`)
  digest/<YYYY-Www>/index.html   ← branded digest board
  digest/<YYYY-Www>/summary.json ← strojový souhrn pro agentův recap
  overview/index.html            ← SITUAČNÍ board („jak to stojí teď“) — z paměti, zdarma, přepisuje se
```

## Úřední stopa — per-trh výměnný provider (`provider_registry.py`, vše zdarma)

| Trh | Zdroj | Stav | Co diffujeme |
|---|---|---|---|
| **CZ** | **ARES v3 REST** (basic + veřejný rejstřík) — bez klíče | **✅ živě ověřeno 2026-07-10** (Notino: vedení, vlastník NOTINO GROUP LIMITED, DPH, flagy) | název · sídlo · kapitál · jednatelé · společníci · **insolvence/likvidace hint** (ostatní skutečnosti + stav) · plátcovství DPH |
| GB | Companies House REST (zdarma, klíč `CH_API_KEY`) | roadmapa | tentýž kontrakt |
| ES | Registro Mercantil / BORME | roadmapa | tentýž kontrakt |

Kontrakt: `search(name, country)` → kandidáti (klient VYBÍRÁ, nehádáme) · `fetch(ico, country)` → record · `diff(prev, curr)` → [(typ, note, severity)]. Nepodporovaný trh → tichá degradace. Insolvence z ARES = **hint** (text ostatních skutečností) — plný ISIR web service je F2.

**Wayback** (`provider_wayback.py`): archive.org CDX, zdarma; ~kvartální snímky za poslední rok, odkazy do archivu. Řeší cold start funnel-spy („takhle se jejich nabídka vyvíjela").

**Režim bez Apify klíče:** patrol NEspadne — reklamní zdroj se vynechá s poznámkou, úřední stopa + wayback jedou (tracker má hodnotu od prvního dne, klíč jen odemyká reklamy).

## watchlist.json

```json
{"version": 1, "created": "2026-07-10", "country": "CZ",
 "caps": {"ads_per_brand": 50, "apify_monthly_usd": 5.0},
 "brands": [{"slug": "neuralflow", "name": "NeuralFlow",
             "ad_library": "NeuralFlow", "web": "https://neuralflow.cz", "note": ""}],
 "keywords": []}
```

- `ad_library` = dotaz do Meta Ad Library (jméno stránky, nebo celá Ad Library URL pro přesné zacílení na page).
- `keywords` = rezerva pro F4 (témata, ne značky).
- Max 10 značek (nákladový cap v `add-brand`).
- `apify_monthly_usd` = kladný bezpečnostní práh nad aktuální měsíční útratou účtu. Při neplatné hodnotě, dosažení prahu nebo nemožnosti útratu ověřit se placené zdroje nespustí. Práh se kontroluje před obchůzkou a nemusí zastavit právě běžící obchůzku přesně na částce; tvrdý účetní limit se nastavuje také přímo v Apify. Každý actor navíc dostává `maxItems` shodné s validovaným limitem výsledků, aby pay-per-result účtování nepřekročilo požadovaný počet položek.
- Placené příkazy navíc vyžadují explicitní `--confirm-paid`. Bez něj `patrol` dokončí jen bezplatné zdroje a zapíše `SOURCE_SKIPPED`; `find-page`, `find-place` a placený lookup při `add-brand` skončí před provider voláním.

## Normalizovaná kreativa (snapshot `ads[]`)

```json
{"advertiser": "...", "hook": "první smysluplná řádka copy",
 "full_copy": "...600 znaků", "cta": "Zjistit více", "offer": "title/caption",
 "destination": "https://...", "days_running": 34, "started": "2026-06-06",
 "ad_archive_id": "123...", "is_active": true,
 "eu_reach": 48200, "creative_hash": "a1b2c3...", "variants": 3,
 "creative_url": "https://scontent.../img.jpg", "ad_library_url": "https://www.facebook.com/ads/library/?id=123..."}
```

- **`creative_hash`** = identita KREATIVY (sha1 z copy+offer+cta+cíl), ne placementu — `ad_archive_id` šumí (duplikace per placement). Diff jede výhradně přes hash. Prázdná kreativa (image-only) → fallback `id:<ad_archive_id>` (žádné falešné slučování).
- **`creative_url`** = náhled kreativy ze snapshotu (obrázek / náhled videa / první karta karuselu), **`ad_library_url`** = trvalý odkaz do Meta Ad Library. Diff je kopíruje do eventů NEW / KILLED / RERUN / MILESTONE; report z nich dělá thumbnail + odkaz. Hash se z nich NEPOČÍTÁ (URL náhledu se mění, identita ne). `hook` a `full_copy` mají vyfiltrované prosáklé šablonové proměnné (`{{product.brand}}`), do hashe jde syrový text (stabilita identity).
- HTML board povolí jen validní veřejný tvar `http(s)` odkazu bez vložených credentials a používá `no-referrer` pro odkazy i vzdálené obrázky. Vzdálený image host přesto při otevření vidí IP adresu prohlížeče; obrázky se lokálně neproxyují.
- **Identifikace inzerenta (2026-09-03):** watchlist nese `fb_page_id` + `fb_page_url` (z `provider_ads.find_page`: hledání podle jména → seskupení podle `page_id` → skóre `to_domain*3 + jméno*2`; jednoznačné = uloženo v `add-brand`, jinak `find-page`/`set-page`) a `footprint` (`provider_web.ad_footprint`: `{platforms:[…], ids:{meta_pixel, google_ads, linkedin, sklik, tiktok, gtm, ga4}}`). Patrol: `pull(fb_page_url or ad_library)`; u stránky se `filter_to_brand` nespouští. Pixel/AW ID nejsou veřejně dohledatelná v žádné knihovně — jen platformy.
- **`filter_to_brand`** je přísný: nechá jen reklamy, jejichž `advertiser` obsahuje token značky; žádný fallback „málo shod → nech všechno“. Nula shod při neprázdném výsledku = `SOURCE_STALE`, prázdný snímek se neuloží a klient musí potvrdit správnou Facebook stránku. Karta značky navíc nese `top_creatives[]` (pás náhledů) a `dest_cards[]` (karty cílových stránek reklam).
- **`cards[]`** = „karty stránek" `{url, image, title}` z og:image / og:title (jako při sdílení na FB) u BLOG_NEW / CONTENT_NEW / JOBS_NEW / WEB_CHANGE a u cílové stránky nových/vrácených kreativ (`provider_web.page_card`, zdarma, max 3 na event, cache per URL v běhu). Logo/SVG/favicon se za náhled nepovažuje; karta bez obrázku se nevykreslí.
- **`links[]`** na kterémkoli eventu = klikací chipy v reportu (REVIEWS → Mapy, REGISTRY → ARES, GOOGLE_ADS → Ads Transparency, WEB_CHANGE → stránka, SERP_ADS → výsledky, SOCIAL_* → příspěvky / profily). Bez pole se nic nevykreslí — žádné mrtvé odkazy.
- **`eu_reach`** = reálný dosah v EU z DSA transparentnosti (`aaa_info.eu_total_reach`). Žije jen na detailu reklamy (seznam má `reach_estimate: null`) → patrol běžně dělá dvě primární actor volání na značku: seznam a detail top-N (`--deep`, výchozí 10). Ověřeno živě 2026-07-10. Bez detailu zůstane hodnota prázdná a report používá jen délku běhu.
- **`audience`** = cílení z EU transparentnosti (jen obohacené reklamy): `{gender, age_min, age_max, locations[]}` — munice pro battlecardy.
- `variants` = kolik placementů téže kreativy jsme slepili (`collationCount` u oficiálního aktoru).
- ⚠️ **Keyword dotaz u marketplace jmen šumí** („Alza" vrátí katalogové reklamy Silan/Bref prodávané NA Alze, hooky s `{{product.brand}}` šablonami) → pro e-shopy/marketplaces zadávej do `ad_library` **celou Ad Library URL stránky**, ne jméno.
- Meta actor primár `curious_coder~…` vyžaduje **count ≥ 10** (MIN_CAP); při selhání auto-fallback na oficiální `apify~facebook-ads-scraper` (normalize umí obě schémata: snake_case epoch i camelCase ISO).
- **Fallback chainy doplňkových zdrojů** (`provider_extras.configured_chain`): každý zdroj = seznam actorů, bere se první, který odpověděl čitelným výsledkem. Konkrétní výchozí řetězce jsou v `provider_extras.DEFAULT_CHAINS`; stejnou funkci používá dry-run i skutečný běh, aby se plán nerozcházel s exekucí. Přepis přes `COMP_<ZDROJ>_ACTORS` musí obsahovat jen ID ve tvaru `vlastnik~nazev-actoru`.
- **Anti-SSRF** (`net_guard.py`): každé stažení klientem zadané URL prochází `zkontroluj_url` (jen http/https, porty 80/443, všechny přeložené adresy musí být veřejné) a `bezpecne_stahni` (přesměrování se nenásleduje automaticky, každý hop se validuje). Platí i pro adresy vytažené z cizí sitemapy. Zbytkové riziko: DNS rebinding (vědomě neřešeno, viz docstring).
- **Řetěz končí u prvního actora, který ODPOVĚDĚL** — prázdná odpověď primáru zálohu nespouští (kredity + falešné STALE). Zálohu volá jen selhání nebo nečitelný formát.
- **Tři stavy zdroje** (`_run_chain`): OK (čitelná data) · PRÁZDNO (čistá odpověď bez dat = legit ticho) · STALE (`SourceError` — padl celý řetěz, NEBO přišla syrová data v neznámém formátu). Normalizéry jsou schéma-tolerantní (`_g()` zkouší víc názvů polí), ale **neparsovatelný řádek se nezapočítává** — jinak by 10 řádků šumu vypadalo jako použitelný výsledek. STALE → tracker zapíše `SOURCE_UNAVAILABLE` a nastaví `summary.complete = false`; ticho se pak nesmí interpretovat jako „konkurence nic nedělá".

## events.jsonl — typy eventů

| Typ | Kdy | Klíčová pole navíc |
|---|---|---|
| `BASELINE` | první snímek značky | `count`, `oldest_days`, `evergreens[]`, `eu_reach_total` |
| `NEW` | nová kreativa (hash nebyl v minulém snímku) | `hook`, `days`, `eu_reach`, `cta`, `destination` |
| `RERUN` | nová kreativa, jejíž hash je v archivu killnutých → **prokázaný winner, nejsilnější signál** | + `prev_run_days`, `killed_on` |
| `KILLED` | kreativa zmizela a běžela ≥ 7 dní | `hook`, `days` |
| `KILLED_SHORT` | souhrn kreativ zabitých do 7 dní (testovací šum — NIKDY jednotlivě) | `count` |
| `MILESTONE` | aktivní kreativa překročila 30/60/90 dní (každý práh jen 1×) | `milestone`, `days` |
| `VELOCITY` | nové kreativy ≥2× / ≤0,5× mediánu posledních běhů (min. rozdíl 3, min. 2 předchozí běhy) | `direction`, `new`, `base` |
| `QUIET` | žádný event — legitimní „beze změn" | `note` |
| `SOURCE_STALE` | knihovna reklam Meta: pád zdroje NEBO kolaps výsledků (0 kreativ / <20 % minula při ≥5) — **diff se přeskočí, poslední známý stav zůstává** (žádná falešná vlna KILLED→RERUN); nastavuje `complete: false` | `note` (česky, klientsky) |
| `SOURCE_UNAVAILABLE` | doplňkový zdroj (web, sitemap, YouTube, sítě, recenze, Google/LinkedIn, SERP) tento týden nešel načíst — řetěz actorů padl nebo neznámý formát; **není to tichý týden**, nastavuje `complete: false` a `sources_unavailable[]` | `note`, `severity` |
| `SOURCE_SKIPPED` | placené zdroje nebyly spuštěny: chybí klíč, práh je vyčerpaný/neplatný nebo nelze ověřit útratu; **není to tichý týden** | `note`, `severity`, `reason_code` |
| `REGISTRY` | úřední stopa založena (baseline: firma, IČO, vznik, vedení) | `note` |
| `REGISTRY_CHANGE` | změna v rejstříku: název · sídlo · kapitál · **jednatelé/statutáři · společníci** (přišli/odešli) | `note`, `severity: info` |
| `ALERT` | **nejvyšší akční hodnota**: zmínka o insolvenci/úpadku · likvidace/zánik · konec plátcovství DPH → „jejich zákazníci budou hledat náhradu" | `note`, `severity: alert` |
| `WAYBACK` | historie webu z archive.org při baseline (cold start — vývoj nabídky za poslední rok) | `note`, `links[]` |
| `WEB_CHANGE` | významná změna webu: titulek / H1 / ceny (meta+CTA = šum, nediffují se) — `provider_web` (stdlib, zdarma) | `note` |
| `BLOG_NEW` / `JOBS_NEW` | nové obsahové / kariérní URL ze sitemap (content velocity / náborový signál) | `note`, `links[]` |
| `REVIEWS` | měsíčně: posun ratingu/počtu + **doslovné stížnosti ≤2★** (Raw Diet = úhly pro nás) — `history/<slug>/reviews.json` | `note` |
| `GOOGLE_ADS` / `LINKEDIN_ADS` | týdenní AGREGÁT (počty, longevita, formáty / imprese po zemích) — `google.json` / `linkedin.json`; event jen při významné změně (±3 / ±2 nebo 0↔N) | `note` |
| `FILING` | nová listina ve sbírce (justice.cz, cookie session) — **výroční zpráva/závěrka = tržby konkurenta (severity alert)**; první běh = tichá baseline | `note`, `severity` |
| `CONTENT_NEW` | nové ne-blogové stránky ze sitemap (≤8 položkově); **>30 productish URL = jen agregát** („hýbou sortimentem" — produktová hlídka je separátní skill, rozhodnutí 2026-07-10) | `note`, `links[]` |
| `YOUTUBE` | nová videa na kanálu konkurenta (organika bez ToS problému; `add-brand --youtube`) | `note`, `links[]` |
| `SOCIAL_NEW` | nové příspěvky na FB / IG / LinkedIn profilu konkurenta + engagement (per-profile; `add-brand --facebook/--instagram/--linkedin`; snímek `history/<slug>/social-<síť>.json`; první běh = baseline) | `note`, `links[]` |
| `SOCIAL_BASELINE` | první snímek sítí značky (jeden souhrnný event: „Facebook 10 · Instagram 12 příspěvků — od příště hlásím jen nové"); report z BASELINE + SOCIAL_BASELINE bez diff-eventů pozná **první obchůzku** (vlastní hlavička, ne „tichý týden") | `note`, `count`, `links[]` (URL profilů) |
| `REVIEWS` (doplněk) | recenze se čtou jen z **potvrzeného místa** (`find-place` → `set-place`, pole `maps_place` ve watchlistu: URL nebo placeId). Bez `maps_place` patrol recenze nevolá ani je nezapočítá do dry-runu; nesmí automaticky založit baseline z libovolné pobočky řetězce. Snímek nese `maps_url`, `place_id`, `website` | `links[]` = Mapy |
| `NEWSLETTER` / `NOTE` | agentem logované pozorování přes `log-event` (validované typy) — newslettery z CC POP3/IMAP schránky | `note` |
| `SERP_ADS` | měsíčně, watchlist-level: kdo inzeruje na klientova brandová slova (`keywords` + `own_web` ve watchlistu, `serp.json`) | `note`, brand=`brandova-slova` |

Sledované stránky: `watch_urls` na značce (max 10, `add-url`) → `history/<slug>/web-<hash8>.json`. Listiny: `history/<slug>/filings.json`. YouTube: `history/<slug>/youtube.json`.

Další soubory: `battlecards/<slug>.md` (příkaz `battlecard --brand`) · `reports/<YYYY-MM>.md` (příkaz `ceo-report`, měsíční roll-up pro AI CEO; neúplné kontroly mají vlastní sekci a nikdy se neoznačí jako klidný trh) · `history/<slug>/{web,blog-urls,google,linkedin,reviews}.json`.

Noise-engineering shrnutí: identita přes hash · krátké killy jen souhrnně · milníky dedup přes `profile.milestones_reported` · velocity až od 3. běhu · tichý týden je výstup jen při `quiet: true` a `complete: true` · **výpadek/přeskočení zdroje ≠ tichý týden** (`SOURCE_STALE`, `SOURCE_UNAVAILABLE`, `SOURCE_SKIPPED`) · opakovaný běh stejného dne vrací uložený summary/board bez dalšího provider volání · `--force` nepřekračuje rozpočtovou pojistku · `killed_archive` je omezen na 365 dní / 400 položek.

## profile.json (agregát + stav)

Agregát: `active_creatives`, `active_placements`, `oldest_days`, `evergreens[]` (30+ dní),
`top_hooks[]`, `eu_reach_total`, `top_by_reach[]`.
Interní stav diffu (nemazat!): `milestones_reported{hash:[30,60]}`, `killed_archive{hash:{hook,days,date}}` (pro RERUN detekci), `velocity_history[]` (posledních 12 běhů).

## summary.json (pro agentův recap)

```json
{"week": "2026-W28", "generated": "2026-07-10", "quiet": false, "complete": true,
 "sources_unavailable": [], "paid_sources": {"enabled": true, "budget": {}, "actor_calls": {}},
 "board": ".../index.html",
 "brands": [{"slug": "...", "name": "...", "active": 12, "oldest": 120, "dropped": 4,
             "events": [...], "evergreens": [...], "profile_md": "...", "prev_snapshot": "2026-07-03"}]}
```

## Zdroje — kompatibilita ověřena 2026-07-10

Jde o historický compatibility checkpoint, ne ceník. Dostupnost actorů, jejich schéma a cenu ověř v Apify před placeným během.

| Síť | Co REÁLNĚ umí (EU) | Tvrdé limity | Actor (ověřen na Store) | Fáze |
|---|---|---|---|---|
| **Meta** Ad Library | `eu_total_reach` per reklama + rozpad věk/pohlaví/země (`age_country_gender_reach_breakdown`) | **bez spendu** u komerčních (útrata jen politické); mimo EU komerční reklamy bez reach | `curious_coder~facebook-ads-library-scraper` · `apify~facebook-ads-scraper` | **F1** |
| **Google** Ads Transparency | per inzerent Search/YouTube/Display/Shopping/Maps, v EU odhad počtu příjemců | jen podle inzerenta/domény; targeting keywords nezveřejňuje | `solidcode~ads-transparency-scraper` | F4 |
| **LinkedIn** Ad Library | hledání podle inzerenta i klíčového slova; v EU odhad impresí + rozpad po zemích | retence a schéma se mohou měnit | `ivanvs~linkedin-ad-library-scraper` | F4 |
| **TikTok** — 2 knihovny! | **Creative Center Top Ads** = CTR percentil („Top 5% CTR"), lajky, budget tier, key-frame analýza → „co frčí" · **Commercial Content Library** (library.tiktok.com) = úplný DSA repozitář EEA+CH+UK, unikátní uživatelé + targeting → „co běží značce X" | Top Ads = **výkonnostní práh + souhlas inzerenta** (opt-in/withdraw) → z principu NEúplný; CCL bez CTR | Creative Center: `beyondops~tiktok-ad-library-scraper` (CZ v enum, CTR sort) · CCL: `ivanvs~tiktok-ad-library-scraper` | F4 |

**„Kdo biduje na moje brandová slova":** žádná knihovna targeting keywords nezveřejňuje (DSA chce jen „main targeting parameters"). Legální cesty: ① **SERP scrape** vlastních brandových dotazů (vidíš, čí reklamy tam reálně jsou) — plán F4; ② **Google Auction Insights** z klientova vlastního Google Ads účtu (přes GHL/nativní napojení) — kandidát pro `ad-analyst`.

Další povrchy dle PLAN (projekt `documents/projects/competitor-tracker/`): funnel spy + **blog diff (RSS/sitemap, ~zdarma)** = F2 (Playwright primár, Apify crawler fallback) · recenze konkurence (Raw Diet) = F2 · organika per konkurent (IG/FB/TikTok/YT/X, aktory z content-scoutu) = F3 · SERP + nábory = F4.

## Provider kontrakt (výměna zdroje)

`provider_ads.pull(query, country, cap) -> list[raw]` + `normalize(raw) -> normalizovaná kreativa` (schéma výše). Nový zdroj (Google/LinkedIn/TikTok) = nový `provider_*.py` se stejným povrchem; diff_engine a board se nemění.
