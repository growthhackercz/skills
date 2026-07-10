# Deep research (podklady se zdroji)

Kdy a jak jít do hloubky, aby článek stál na **ověřených faktech, ne na dojmech**. Cíl: žádné vymyšlené číslo, studie ani citát — vše má dohledatelný zdroj. Běží uvnitř kroku „2. Výzkum a pojetí"; article-writer tím zůstává sólo dělník (nepotřebuje k tomu strategist).

## Kdy sepnout deep research (trigger „málo dat")

Lehký competitive scan (krok 2.1) stačí u jednoduchých kusů. **Přepni na deep research, když platí aspoň jedno:**

- scout brief chybí, je **starší 7 dní**, nebo má < 5 relevantních položek
- chybí SEO data (`/documents/content/seo-keywords.json`)
- je to **autoritní typ** (datová studie, kompletní průvodce, srovnání, thought leadership) a nemáš dost tvrdých faktů/čísel
- competitive scan vrátil **< 3 použitelné zdroje**
- článek má stát na číslech/datech, která si čtenář ověří

Když je dat dost (dobrý brief, jednoduchý návod/listicle) → deep research NEspouštěj, šetři čas i kredity.

## Postup: fan-out → fetch → ověř → dossier

1. **Fan-out dotazů** — z tématu udělej **4–8 konkrétních** výzkumných dotazů (klíčová čísla, definice, srovnání, případové studie, protiargumenty). Ne jeden široký dotaz.

2. **Fetch zdrojů** — primárně přes dostupné **web vyhledávání / web_fetch**.
   - **Když web nedosáhne** (403, blokované scrapování, prázdná odpověď) NEBO je nejlepší zdroj **za sociální platformou** (YouTube přepis, LinkedIn, X — běžný web to nestáhne) → **Apify fallback** (vlastní tenký fetch, auto-detekuje zdroj z inputu):
     ```bash
     python3 {baseDir}/scripts/apify_fetch.py "<dotaz nebo URL>" --dry-run                 # napřed odhad, 0 útraty
     python3 {baseDir}/scripts/apify_fetch.py "https://youtube.com/watch?v=..." --max 1    # PŘEPIS videa
     python3 {baseDir}/scripts/apify_fetch.py "li: <téma>" --max 5                         # LinkedIn příspěvky
     python3 {baseDir}/scripts/apify_fetch.py "x: <téma>" --max 5                          # X / Twitter
     ```
     Zdroje: **`web`** (default, stránky) · **`youtube`** (přepis + metadata) · **`linkedin`** · **`x`**. Auto-detekce z URL/prefixu (`yt:` / `li:` / `x:`), nebo `--source`. Vrací `[{source,url,title,text}]`. **YouTube přepis** je pro research nejcennější (dlouhá expertní substance). `APIFY_API_KEY` je per klient; bez klíče script vrátí `skip` a research jede dál z toho, co má.
   - **Kredity = peníze klienta:** vždy napřed `--dry-run`; drž `--max` nízko (1–3 zdroje na dotaz; u YouTube často stačí 1 konkrétní video); Apify jen když web reálně nepustil nebo je zdroj za platformou, **ne plošně**.

3. **Extrakce se zdrojem** — z každého zdroje vytáhni **jen fakty, čísla, citace** a ke každému **URL + rok**. Údaj bez zdroje se do dossieru nedostane.

4. **Adversariální ověření** — u každého klíčového čísla se zeptej: *„Kdyby to bylo špatně, jak to poznám?"* Ověř proti druhému zdroji, kde to jde. Rozpor nebo jen jeden slabý zdroj → `confidence: low`, nebo zahoď. **Nikdy nedoplňuj chybějící číslo odhadem.**

5. **Dossier** — ulož podklady, ze kterých pak píšeš:

```text
/documents/content/research/{slug}/dossier.md      # čitelný přehled: klíčová zjištění + zdroje
/documents/content/research/{slug}/dossier.json    # strukturovaně (schéma níže)
```

```json
{
  "topic": "…",
  "slug": "…",
  "questions": ["…"],
  "findings": [
    {"claim": "…", "value": "42 %", "source": "https://…", "year": 2026, "confidence": "high"}
  ],
  "sources": [{"url": "https://…", "title": "…", "via": "web|apify"}],
  "gaps": ["co se nepodařilo doložit — do článku NEpatří jako fakt"]
}
```

## Jak dossier použije článek

- Answer-first úvod i tvrzení v textu berou čísla **jen z `findings`** (každé má zdroj) — navazuje na pravidlo „důkaz jen ze zdrojů" v kroku 4 workflow.
- Co skončilo v `gaps` (nedoložené) se **do článku nepíše jako fakt** — buď vynech, nebo formuluj jako otevřenou otázku.
- Dossier je **znovupoužitelný** (refresh článku, newsletter, social) — neplýtvej opakovaným researchem stejného tématu; nejdřív zkontroluj, jestli `dossier.json` k slugu už neexistuje.
