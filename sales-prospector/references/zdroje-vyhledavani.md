# Zdroje vyhledávání — detail u každého zdroje

Všechny zdroje jsou **bezpečné** při dodržení uvedených denních limitů — nevyvolávají ochrany proti robotům. Pokud Sales Prospector narazí na HTTP 429 / 403, zastaví konkrétní zdroj a pokračuje s ostatními (neblokuje celý běh).

## 1. ARES (Administrativní registr ekonomických subjektů)

**Co dává:** všechny CZ firmy zapsané v obchodním rejstříku — IČO, název, sídlo, CZ-NACE, právní forma, statutární orgány, datum vzniku, status (aktivní / v likvidaci / v insolvenci).

**API endpoint:** `https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/`

**Query syntax (POST JSON):**
```json
{
  "start": 0,
  "pocet": 100,
  "razeniSeznamuEs": ["nazev"],
  "ico": [],
  "nazev": "*kosmetika*",
  "obecKodObce": [500054],
  "czNace": ["4711", "4719"],
  "pravniForma": ["112", "101"]
}
```

**Užitečné filtry:**
- `czNace` — Klasifikace ekonomické činnosti (např. `4711` = maloobchod v nespecializovaných prodejnách)
- `obecKodObce` — kód obce/města (Praha = 500054, Brno = 582786)
- `okresKodOkresu` — kód okresu
- `pravniForma` — `112` = s.r.o., `101` = OSVČ, `121` = a.s.
- `datumVznikuOd` / `datumVznikuDo`
- `cinnosti` — výpis předmětů činnosti

**Denní limit:** prakticky neomezeno (1000+ req/den bez nárazu). Žádný API key potřebný.

**Ochrana proti robotům:** žádná. Oficiální veřejné API státu.

**Preferovaný nástroj:** `web_fetch` (JSON odpověď, statická, žádný JavaScript)

**⚠️ Pozor:**
- ARES nedává obrat, zaměstnance, kontakty (jen statutární zástupce). Tyto údaje doplň přes doplnění informací (Krok 4) z firemního webu nebo doplňkových zdrojů.
- Insolvence se musí ověřit zvlášť přes `https://isir.justice.cz/` (Justice.cz / ISIR) — ARES status nemusí být real-time.

---

## 2. Google Maps Places API

**Co dává:** lokální firmy a POI s adresou, telefonem, webem, hodnocením, otevírací dobou. Pokrytí B2C i lokální B2B služby (restaurace, řemeslníci, zubaři, autoservisy).

**API endpoint:** `https://places.googleapis.com/v1/places:searchText`

**Auth:** `X-Goog-Api-Key` header. Klíč v env jako `GOOGLE_MAPS_API_KEY` (nebo přes `cc_credentials.get_env_or_variable("GOOGLE_MAPS_API_KEY")`).

**Příklad query (POST JSON):**
```json
{
  "textQuery": "kosmetický salon Praha 7",
  "maxResultCount": 20,
  "languageCode": "cs"
}
```

**Užitečné fields:** `places.displayName`, `places.formattedAddress`, `places.nationalPhoneNumber`, `places.websiteUri`, `places.rating`, `places.userRatingCount`, `places.businessStatus`.

**Denní limit:** Bezplatný tarif = 100 000 requests/měsíc (~3300/den). Pro běžné použití Sales Prospectora plně postačí.

**Ochrana proti robotům:** žádná (oficiální API).

**Preferovaný nástroj:** `web_fetch` (JSON odpověď)

**Náhrada bez API klíče:** OpenStreetMap Overpass (viz dále).

---

## 3. OpenStreetMap Overpass (náhrada Google Maps)

**Co dává:** POI z OSM databáze — totéž co Google Maps, ale data crowdsourced (občas méně úplná pro malé firmy).

**API endpoint:** `https://overpass-api.de/api/interpreter`

**Příklad query (Overpass QL):**
```
[out:json][timeout:25];
area["name"="Praha"]["admin_level"="6"]->.searchArea;
(
  node["shop"="cosmetics"](area.searchArea);
  node["amenity"="beauty_salon"](area.searchArea);
);
out body;
```

**Denní limit:** ~1000 req/den bez nárazu. Žádný API key.

**Ochrana proti robotům:** žádná, ale je nastavené omezení rychlosti dotazů — pauzuj 2 sekundy mezi dotazy.

**Preferovaný nástroj:** `web_fetch` (JSON odpověď)

**⚠️ Pozor:** OSM data jsou často méně úplná pro malé firmy než Google Maps. Telefon a web bývají chybějící. Použij jen když klient nemá Google API key.

---

## 4. Brave Search API (alt: Serper.dev)

**Co dává:** webové vyhledávání pro hledání firem podle klíčových slov (např. „české eshopy s ekologickou kosmetikou"). Vrátí URLs + snippety. Užitečné pro nalezení firem, které nejsou v ARES (e-shopy, freelanceři) nebo pro objevení branžových katalogů.

**API endpoint:** `https://api.search.brave.com/res/v1/web/search?q=...`

**Auth:** `X-Subscription-Token` header. Klíč čti přes `cc_credentials.get_env_or_variable("BRAVE_API_KEY")`.

**Denní limit:** Bezplatný tarif = 2000 dotazů měsíčně (~65/den). Placené tarify od $3/měsíc.

**Alternativa:** `serper.dev` — Google search results přes API. $50/měsíc za 50k queries. Endpoint `https://google.serper.dev/search`, header `X-API-KEY`.

**Ochrana proti robotům:** žádná (oficiální API).

**Preferovaný nástroj:** `web_fetch` (JSON odpověď)

**Použití:** Krok 3 doplnění, když ARES + Google Maps nepokrývají daný profil (např. „e-shopy s X" = potřebuješ webové vyhledávání, ne registrový lookup).

---

## 5. Veřejné weby (cílený `web_fetch` per URL)

**Co dává:** hloubková extrakce z konkrétní stránky — kontakt, tým, klienti, signál zájmuy.

**Použití:** v Krok 4 (doplnění informací) — pro každou nalezenou firmu volej `web_fetch` na její `/`, `/kontakt`, `/contact`, `/o-nas`, `/about`, `/tym`, `/team`. Extrahuj e-mail, telefon, jména klíčových lidí.

**Denní limit:** ~50–100 dotazů na doménu denně je bezpečné (mnoho hostingů má omezení rychlosti dotazů na jednu IP adresu). Při našem denním cíli 30 prospektů to znamená max ~3000 dotazů denně — bezpečně pod prahem.

**Ochrana proti robotům:** nízká. Některé velké korporátní weby (banky, telekomunikace) mají firewall (WAF) — pokud HTTP 403, prostě přeskoč a označ kontakt jako `kvalita_kontaktu: nízká`. Nezkoušej to znovu agresivně.

**Preferovaný nástroj:** **hybridní** — výchozí `web_fetch`. Pokud výsledek má < 1500 znaků viditelného textu, prázdný `<body>` s SPA markerem (`<div id="root">`, `<div id="__next">`, `<div id="app">`), nebo HTTP 403 → fallback na **nativní headless Chromium** (`navigate` + 3s čekání na vykreslení + `extract` textu). Podrobnosti v Krok 4 SKILL.md („Hybridní načítání stránek").

**⚠️ Pozor:**
- Respektuj `robots.txt` (i když to není striktně povinné). Když web říká `Disallow: /kontakt`, neignoruj to.
- Nestahuj e-maily ze stránek, které vyžadují přihlášení.

---

## 6. Justice.cz / ISIR (insolvence)

**Co dává:** real-time stav insolvenčního řízení per IČO. Užitečné jako **disqualifier check** v Krok 5.

**Endpoint:** `https://isir.justice.cz/isir/ueu/vysledky_lustrace.do` (HTML form, ne JSON API)

**Použití:** dotaz per IČO. Když najdeš záznam s aktivním řízením, prospekt vyřaď (disqualifier).

**Denní limit:** ~100 req/den bez nárazu. Žádný API key.

**Ochrana proti robotům:** žádná, ale stahování HTML — může se rozbít při změně rozhraní. Drž parser jednoduchý a tolerantní k chybám.

**Preferovaný nástroj:** `web_fetch` (statické HTML, jednoduchý parser)

---

## 7. Hlídač státu (veřejné zakázky)

**Co dává:** otevřená databáze veřejných zakázek, dotací, smluv. Užitečné pro identifikaci firem, které prodávají do státní správy (signál: prošly compliance, mají reference).

**API endpoint:** `https://www.hlidacstatu.cz/api/v1/`

**Auth:** zaregistruj se → API token v env jako `HLIDACSTATU_API_TOKEN` (optional, anonymous má omezený access).

**Denní limit:** ~500 dotazů denně s tokenem, ~100 bez. Žádná ochrana proti robotům.

**Preferovaný nástroj:** `web_fetch` (JSON odpověď)

**Použití:** signál zájmu — „tato firma minulý měsíc vyhrála zakázku na X za Y mil." = horký lead pro doplňkové služby.

---

## 8. Firmy.cz / Živý.cz katalogy

**Co dává:** CZ business directories s 600k+ firmami. Často mají info, které není v ARES (web, e-mail, hodnocení).

**Ochrana proti robotům:** **Středně přísné.** Bez API. Scraping HTML — potřebuje opatrnost.

**Bezpečný denní limit:** **~30 lookups/den per katalog**. Pauzuj 3–5 s mezi dotazy. Při HTTP 403 zastav a přestaň.

**Použití:** Doplňkový zdroj — když ARES vrátí firmu bez webu, zkus dohledat v katalogu.

**Preferovaný nástroj:** `web_fetch` (statické HTML)

**⚠️ Pozor:** Nepoužívej jako primární masivní zdroj. Slouží jen jako doplnění informací doplněk.

---

## 9. News RSS (signály zájmu)

**Co dává:** signály zájmu pro firmy, které právě dostaly investici, expandují, mění tým. Horké leads.

**Feedy:**
- `https://www.lupa.cz/rss/clanky/` — IT/tech CZ scéna
- `https://www.czechcrunch.cz/feed/` — CZ startupy + investice
- `https://www.e15.cz/rss` — byznys, finance
- `https://www.businessinfo.cz/rss/` — B2B, export
- `https://feeds.feedburner.com/Hospodarskenoviny-byznys` — HN byznys

**Denní limit:** neomezeno (jsou to feedy).

**Ochrana proti robotům:** žádná.

**Preferovaný nástroj:** `web_fetch` (XML / RSS feed, statický)

**Použití:** V Kroku 4 (doplnění informací) — pro každou firmu zkus fulltextové hledání ve stažených zpravodajských kanálech (posledních 30 dní). Když najdeš shodu, ulož jako `signal_zajmu: "..."` (např. „Získali 50M Kč od Reflex Capital 2026-04-22").

---

## Doporučená kombinace zdrojů podle typu kampaně

| Use case | Primární zdroj | Doplňkový | Disqualifier check |
|---|---|---|---|
| B2B v ČR podle branže | ARES (CZ-NACE filtr) | Brave Search (firmy mimo ARES), web_fetch (doplnění informací) | Justice.cz |
| Lokální B2C (kavárny, salóny) | Google Maps Places (nebo OSM jako náhrada) | web_fetch (doplnění informací) | — |
| E-shopy v dané vertikále | Brave Search („e-shop X") | web_fetch (extrakce), ARES (firma za e-shopem) | Justice.cz |
| Firmy s investicí / expanzí | Zpravodajské RSS kanály (signály zájmu) | ARES (doplnění firmografiky), web_fetch | Justice.cz |
| Dodavatelé do státní správy | Hlídač státu (veřejné zakázky) | ARES, web_fetch | — |

## Společná pravidla pro ochranu proti robotům

1. **Pauza 2–5 vteřin** mezi dotazy do stejné domény (web_fetch, Firmy.cz, Justice.cz).
2. **Hlavička User-Agent:** vždy nastav realistický identifikátor (`Mozilla/5.0 (compatible; CliqSales-SalesProspector/1.0; +https://cliqsales.cz)`). Nikdy se nevydávej za Googlebot.
3. **HTTP 429 / 403:** zastav konkrétní zdroj, pokračuj s ostatními. Neobcházej.
4. **Žádný LinkedIn.** Žádné střídání proxy adres. Žádné obcházení Cloudflare přes prohlížeč bez okna.
5. **Respektuj `robots.txt`** u `web_fetch`.
