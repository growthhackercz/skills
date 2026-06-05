# Zdroje výzkumu — kdy `web_fetch` vs `browser`

Sales Scout používá dva nástroje pro stahování dat z webu:

- **`web_fetch`** — rychlé, levné, pro statické HTML stránky a JSON API
- **`browser`** — vestavěný Chromium, pro JavaScript-heavy stránky, moderní SPA a LinkedIn

Pravidlo: **vždy nejdřív zkus `web_fetch`** (rychlejší, levnější), **náhradně přes `browser`** jen pokud:
- HTML má `<body>` pod 1500 znaků
- `<body>` neobsahuje žádný viditelný text (jen `<script>` tagy)
- Hlavní obsah je render přes JavaScript (běžně React / Next.js / Vue.js)

**Výjimka:** pro LinkedIn vždy rovnou `browser` (žádný pokus s `web_fetch`).

---

## 1. ARES — registr ekonomických subjektů

**K čemu:** ověření IČO, právní formy, sídla, statutárních zástupců, statusu (aktivní / v insolvenci / v likvidaci), předmětu činnosti.

**Endpoint:** `https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/`

**Nástroj:** `web_fetch` (JSON odpověď)

**Typický dotaz (vyhledání podle názvu):**
```
POST /ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat
{
  "start": 0,
  "pocet": 10,
  "nazev": "Bioptron Medall"
}
```

**Typický dotaz (vyhledání podle IČO):**
```
GET /ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/12345678
```

**Denní limit:** prakticky neomezeno (státní API).

**Pomocný skript:** `scripts/ares_lookup.py` — předá ti vyčištěný JSON s polem `{ico, nazev, sidlo, pravniForma, statutariOrgany, predmetCinnosti, datumVzniku, status}`.

---

## 2. Web firmy

**K čemu:** popis činnosti, produkty, ceník, klienti (reference), tonalita, hodnoty, kontakty.

**Stránky k navštívení (v tomto pořadí, dokud nezískáš dostatek dat):**
1. `https://[domena]/` — domovská stránka (popis činnosti, USP)
2. `https://[domena]/o-nas` nebo `/o-firme` nebo `/about` — kdo jsou
3. `https://[domena]/produkty` nebo `/sluzby` nebo `/products` — co prodávají
4. `https://[domena]/cenik` nebo `/pricing` — ceník (pokud veřejný)
5. `https://[domena]/blog` (jen titulky posledních 3 článků — co řeší, jak komunikují)
6. `https://[domena]/kontakt` — kontakt + osoba (často jméno + pozice)

**Nástroj:** `web_fetch` pro každou stránku. Pokud `<body>` pod 1500 znaků nebo prázdný → náhradně přes `browser` (jedna návštěva s extrakcí).

**Pauza:** žádná není potřeba (vlastní web firmy, ne agresivní crawl).

**Anti-bot riziko:** nízké. Některé velké korporátní weby (banky, telekomunikace) mají firewall (WAF) — pokud HTTP 403, skip stránku, pokračuj s ostatními.

---

## 3. LinkedIn — firma

**K čemu:** popis firmy z LinkedIn, počet zaměstnanců, sektor, lokace, web, headquarter.

**URL pattern:** `https://www.linkedin.com/company/[slug]`

**Jak najít slug:**
1. **Pokus 1:** automatický odhad z názvu firmy (lowercase, mezery → spojovníky, odstranit „s.r.o.", „a.s." atd.)
   - „Bioptron Medall s.r.o." → `bioptron-medall`
2. **Pokus 2:** Brave Search `site:linkedin.com/company "Bioptron Medall"` → výsledek URL

**Nástroj:** **vždy `browser`** (`web_fetch` vrátí prázdný kostrový HTML, LinkedIn obsah je celý render přes JS).

**Pauza:** 5–10 vteřin před každou LinkedIn navigací (jakoukoli).

**Anti-bot — okamžitě stop, pokud:**
- Stránka obsahuje „Verify you're human"
- Stránka obsahuje „Sign in to LinkedIn"
- Stránka obsahuje „Just a moment…" (Cloudflare challenge)
- HTTP 999 (LinkedIn-specifický rate-limit kód)

Při těchto signálech: **STOP LinkedIn pro tento Scout běh**, zápis do briefu: *„LinkedIn nedostupný (anti-bot ochrana). Zkus znovu za 2–4 hodiny."*

**Max 3 LinkedIn page views per Scout brief** (1 firma + 2 osoby).

---

## 4. LinkedIn — osoba

**K čemu:** pozice, předchozí role, vzdělání, síť.

**URL pattern:** `https://www.linkedin.com/in/[slug]`

**Jak najít slug:**
1. **Pokus 1:** automatický odhad z jména (lowercase, mezery → spojovníky, bez diakritiky)
   - „Marek Novák" → `marek-novak`
2. **Pokus 2:** Brave Search `site:linkedin.com/in "Marek Novák" "Bioptron"` → výsledek URL

**Nástroj a pravidla:** stejně jako u LinkedIn firmy (vždy `browser`, pauza, anti-bot stop).

**Pokud LinkedIn URL nelze najít** ani jednou metodou → sekce „Pozice" v briefu zůstane prázdná s poznámkou *„LinkedIn profil nenalezen"*.

---

## 5. Justice.cz / ISIR — insolvence

**K čemu:** ověření, zda firma není v insolvenčním řízení nebo likvidaci. Kritická informace pro „Rizika" sekci briefu.

**Endpoint:** `https://isir.justice.cz/isir/ueu/vysledky_lustrace.do`

**Nástroj:** `web_fetch` (statické HTML formuláře a výsledky).

**Dotaz podle IČO:** `?ico_subjektu_form=12345678&typ_subjektu_form=O`

**Pauza:** 2–3 vteřiny mezi dotazy.

**Anti-bot:** žádná, ale tradiční HTML scrape — drž parser tolerantní k změnám rozhraní.

**Pokud najdeš aktivní řízení** → do sekce „Rizika" zápis: *„⚠️ Aktivní insolvenční řízení od [datum], spis. zn. [číslo]. Doporučuju neoslovo­vat dokud se status nezmění."*

---

## 6. Hlídač státu — veřejné zakázky a smlouvy

**K čemu:** identifikace firem, které prodávají do státní správy (signál: prošly compliance, mají reference, jsou likvidní).

**Endpoint:** `https://www.hlidacstatu.cz/api/v2/`

**Nástroj:** `web_fetch` (JSON API).

**Dotaz:** `GET /smlouvy/hledat?dotaz=ico:12345678&order=date_desc&limit=10`

**Auth:** doporučená registrace pro `HLIDACSTATU_API_TOKEN` v `cc_credentials` (anonymně omezený přístup).

**Denní limit:** ~500 dotazů denně s tokenem.

**Použití:** pokud najdeš nedávné zakázky (< 6 měsíců), do „Signály zájmu" zápis: *„Vyhráli zakázku na [téma] za [částka] Kč v [datum] od [úřad] — firma je aktivní v B2G, má reference."*

---

## 7. News a signály zájmu

**K čemu:** intent — firmy, které právě dostaly investici, expandují, mění tým, nabírají, mají negativní press.

**Dvě cesty:**

### 7a. Zpravodajské kanály (RSS)

**Feedy:**
- `https://www.lupa.cz/rss/clanky/` — IT a tech scéna v ČR
- `https://www.czechcrunch.cz/feed/` — CZ startupy + investice
- `https://www.e15.cz/rss` — byznys, finance
- `https://www.businessinfo.cz/rss/` — B2B, export
- `https://feeds.feedburner.com/Hospodarskenoviny-byznys` — HN byznys

**Nástroj:** `web_fetch` (XML feedy, statické).

**Postup:** stáhnout posledních 30 dní feedů, fulltextové hledání pro `[název firmy]`. Pokud najdeš zmínku, vytáhnout titulek + URL + datum.

### 7b. Brave Search — nedávné zmínky

**Endpoint:** `https://api.search.brave.com/res/v1/web/search`

**Nástroj:** `web_fetch` (JSON API).

**Dotaz:** `?q="[Firma s.r.o.]" 2026&freshness=pm` (posledních 30 dní)

**Auth:** `BRAVE_API_KEY` přes `cc_credentials.get_env_or_variable("BRAVE_API_KEY")`.

**Denní limit:** 2000 dotazů měsíčně (~65 / den) na bezplatném tarifu.

---

## 8. Brave Search — pomocný (pro LinkedIn lookup)

Když automatický odhad LinkedIn slug selže (typicky pro firmy s neobvyklým názvem nebo pro osoby s běžným jménem), použij Brave Search jako náhradní cestu:

- Pro firmu: `site:linkedin.com/company "[přesný název firmy]"`
- Pro osobu: `site:linkedin.com/in "[Jméno Příjmení]" "[Firma]"`

**Nástroj:** `web_fetch` (JSON API, viz 7b).

První výsledek = pravděpodobně správný LinkedIn URL. Před `browser` navigací zkontroluj, že URL skutečně začíná `https://www.linkedin.com/`.

---

## Shrnutí — co používat pro co

| Zdroj | Nástroj | Anti-bot pauza | Denní limit |
|---|---|---|---|
| ARES | `web_fetch` | žádná | neomezeno |
| Web firmy (statický) | `web_fetch` | žádná | žádný (vlastní web) |
| Web firmy (SPA / pod 1500 znaků) | `browser` (náhradně) | 2 vteřiny | bezpečně ~50 dotazů na doménu denně |
| LinkedIn firmy | `browser` (vždy) | 5–10 vteřin | max 1× per Scout brief |
| LinkedIn osoby | `browser` (vždy) | 5–10 vteřin | max 2× per Scout brief |
| Justice.cz / ISIR | `web_fetch` | 2–3 vteřiny | ~100/den |
| Hlídač státu | `web_fetch` | žádná | ~500/den s tokenem |
| Zpravodajské RSS | `web_fetch` | žádná | neomezeno (feedy) |
| Brave Search | `web_fetch` | žádná | ~65/den (bezplatný tarif) |

**Celková doba běhu jednoho Scout briefu:** 60–90 vteřin (paralelní výzkum + 1 LinkedIn pauza).
