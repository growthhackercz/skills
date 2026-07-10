---
name: article-writer
description: "Píše kvalitní články podle typu (návod, listicle, kompletní průvodce, srovnání, case study, prodejní článek/advertorial, datová studie, názor, vysvětlení pojmu) — každý typ má vlastní ověřenou strukturu, titulky a CTA. Texty optimalizuje pro Google i AI vyhledávače a umí aktualizovat starší článek (refresh). Připraví review-ready HTML, SEO metadata a podklady pro obrázky; negeneruje obrázky a nepublikuje."
category: content
status: ready
version: "2.2"
publishedAt: "2026-07-08"
metadata: {"openclaw":{"emoji":"✍️","requires":{"bins":["python3"]},"optionalEnv":"APIFY_API_KEY"}}
---
# Article Writer

Pokročilý autor článků všech typů. Produkuje text, metadata a briefy pro obrázky. Negeneruje obrázky, neuploaduje assety a nepublikuje do WordPressu ani CliqSales blogu. Funguje **samostatně** (stačí „napiš mi článek o X"), i jako dělník uvnitř `content-strategist` pipeline.

**Precedence: jednorázové zadání článku od klienta/operátora vlastní `content-strategist`.** Když je nainstalovaný, na „napiš(te) mi článek o X" VŽDY spusť jeho (dotáhne obrázky, nahrání draftu do redakčního systému a nabídku atomizace) — tenhle skill v tom běhu funguje jen jako jeho dělník. Sólo režim tohohle skillu použij pouze, když `content-strategist` k dispozici není, nebo když si klient výslovně řekne jen o text. Po sólo běhu úkol NENÍ kompletní obsahový balík — do handoffu napiš, že chybí obrázky a draft, a neoznačuj to za hotový článek k publikaci.

Dva režimy:
- **NOVÝ ČLÁNEK** (default) — workflow níže.
- **REFRESH** — aktualizace existujícího článku (trigger: „aktualizuj článek X", recyklační pravidlo 90+ dní, nebo upozornění na zastaralost — např. změna ceny produktu). Postup v sekci „Režim REFRESH".

Použij ho pro blogové články, thought leadership, SEO obsah, konverzní články i články, které později převezme `wordpress-publisher` nebo `cliqsales-blog-publisher`.

## Výstupy

Ulož vše do jedné složky:

```text
/documents/content/blog/{slug}/
├── article.html
├── article-metadata.json
├── image-briefs.json
└── handoff.md
```

`article.html` je čisté review-ready HTML bez vložených obrázků. `image-briefs.json` je vstup pro `article-image-generator`. SEO metadata v `article-metadata.json` jsou zdroj pro publishing; finální mapování do cílového systému řeší `wordpress-publisher` nebo `cliqsales-blog-publisher`.

## Workflow

### 0. Typ článku

Typ určuje strukturu, titulek, délku i CTA — rozhodni ho PŘED researchem.

1. **Ze zadání:** `content-strategist` typ předává v zadání; uživatel ho často řekne sám („napiš srovnání / návod / prodejní článek…"). Pak ho použij.
2. **Odvoď z cíle**, když typ v zadání není:

| Cíl kusu | Vhodné typy |
|---|---|
| návštěvnost / dosah | listicle · návod |
| autorita / zpětné odkazy | datová studie · kompletní průvodce · vysvětlení pojmu |
| konverze / poptávky | srovnání a alternativy · case study · prodejní článek (advertorial) |
| důvěra / odborná pozice | thought leadership |

3. **Nejasný cíl → jedna otázka:** *„Má článek hlavně přivést čtenáře (návštěvnost), přesvědčit k poptávce (konverze), nebo budovat odbornou pozici?"*
4. **Načti playbook zvoleného typu z `{baseDir}/references/article-types.md`** — kostra, titulkové vzorce, délka a CTA se řídí playbookem, ne univerzální šablonou.

### 1. Načti kontext

1. Načti `/documents/brand/brandDNA.md`.
2. Pokud téma souvisí s produktem, načti `/documents/brand/products/{product-slug}/productDNA.md`.
3. **Signály (pokud existují):**
   - research brief z `content-scout`: nejnovější běh k tématu v `/documents/content/research/runs/{slug}/{datum}/brief.json` — témata, virální kusy, otázky lidí, doporučené úhly a hooky
   - SEO data od `seo-strategist`: `/documents/content/seo-keywords.json` — primární keyword, cluster, striking-distance příležitosti
4. Pokud existuje `/documents/content/content-log.md`, ověř duplicity a navrhni **2–5 interních odkazů** na související publikované články (popisný anchor text, ne „zde").

Pokud chybí zásadní brand/product kontext, zeptej se na chybějící vstup. Pokud chybí jen volitelné detaily (signály, SEO data), pokračuj s jasně uvedenými předpoklady.

### 2. Výzkum a pojetí

Než začneš psát, rozhodni, proč má článek existovat.

1. **Competitive scan** - pokud je dostupné webové vyhledávání, projdi 5-10 relevantních výsledků. Najdi konsenzus, mezery a slabiny. Pokud web není dostupný, použij research brief, brand/product DNA a známý kontext.
   - **Když je podkladů málo** (scout brief chybí/starší 7 dní/tenký, chybí SEO data, autoritní typ bez tvrdých faktů, nebo < 3 použitelné zdroje) → jdi do **deep research** podle `{baseDir}/references/research.md`: fan-out dotazů → fetch → ověření faktů/čísel **se zdroji** → citovaný dossier do `/documents/content/research/{slug}/`.
   - **Když web něco nepustí** (403, scrapování) nebo je zdroj **za sociální platformou** (YouTube přepis, LinkedIn, X — web to nestáhne) → **Apify fallback** `python3 {baseDir}/scripts/apify_fetch.py "<dotaz|URL>" --dry-run` (napřed odhad), pak bez `--dry-run`; zdroj se auto-detekuje z URL/prefixu (`yt:`/`li:`/`x:`) nebo `--source`. Kredity = peníze klienta: `--max` nízko, jen cíleně.
   - Při **dostatku dat** deep research nespouštěj (šetři čas i kredity) — lehký scan stačí.
2. **Information gain** - napiš jednu větu, co článek přináší navíc oproti běžným textům. „Kompletní" už není výhoda — výhoda je to, co ostatní nemají: vlastní čísla, reálná zkušenost, odvážný závěr, konkrétní segment publika.
3. **Fan-out otázky** - vypiš 3-8 pod-otázek, na které se lidé k tématu reálně ptají (z research briefu, „lidé se také ptají", vlastní úvahy). Každá dostane vlastní sekci, nebo položku ve FAQ bloku.
4. **Redakční pojetí** - zvol jeden pohled na téma: kontrariánský, praktický z praxe, myth-busting, srovnávací, behind-the-scenes, predikční nebo zaměřený na konkrétní problém.
5. **Hook** - vyber typ otevření: silné tvrzení, konkrétní číslo, začátek uprostřed situace, relatable pain, credibility + promise nebo otázka měnící perspektivu.

Nepoužívej defaultní pojetí typu „Kompletní průvodce X" nebo „Vše, co potřebujete vědět o X", pokud si ho uživatel výslovně nepřeje.

### 3. Struktura a vyprávění

**Kostru článku přebírá playbook typu** (`{baseDir}/references/article-types.md`) — počet a podoba sekcí, pořadí bloků, tabulky, FAQ.

**Story framework** je narativní vrstva UVNITŘ té kostry — jak text vyprávět:

| Framework | Kdy použít |
|---|---|
| PAS | problémové/how-to články |
| Before-After-Bridge | transformační příběhy a case-study tón |
| Thesis-Antithesis-Synthesis | thought leadership a názorové články |
| Loop & Callback | narativní články s návratem k úvodnímu hooku |
| ABT | krátké přesvědčivé články |
| Inverted Pyramid | rychlé informační články |
| Constellation | průřezová témata s více podtématy |

Framework je interní pomůcka. Neopisuj jeho název do článku, pokud se to nehodí.

### 4. Piš po sekcích

Negeneruj dlouhý článek jedním souvislým výdechem. Piš po sekcích a před každou H2 sekcí si připomeň:

- brand voice
- redakční pojetí a zvolený typ
- framework
- co už bylo řečeno, aby se text neopakoval

Každý článek musí obsahovat:

- konkrétní H1 podle titulkového vzorce typu — jako pracovní verze; **finální titulek vyber po dopsání v titulkové dílně** (`{baseDir}/references/headlines.md`): 5-10 variant, SERP-intent check, 4U kontrola, dvojí titulek
- **answer-first úvod**: přímá odpověď na hlavní otázku článku v prvních 40-75 slovech, hned za ní **krátký důkaz, proč článku věřit** (číslo, výsledek, reálná zkušenost — jen ze zdrojů), pak kontext a příslib hodnoty
- sekce podle kostry typu (ne univerzálních 5-7 H2)
- závěr jako syntézu s **jasným dalším krokem** — nikdy pod nadpisem „Závěrem" či „Shrnutí", nikdy jen rekapitulace; doporuč související článek (interní odkaz)
- CTA podle playbooku typu (viz krok 5)

**Pravidla pro AI vyhledávače** (detail a zdůvodnění v `{baseDir}/references/ai-search-2026.md`):

- H2, které odpovídají reálným otázkám, formuluj jako otázku a odpověz v první větě pod nadpisem
- klíčová tvrzení piš jako samostatné, citovatelné věty s podmětem plným jménem (ne zájmenem)
- konkrétní čísla se jmenovaným zdrojem všude, kde to typ snese (orientačně 1 číslo na 150-200 slov)
- minimálně jedna tabulka všude, kde se něco srovnává nebo vyčísluje
- FAQ blok (3-6 otázek, odpovědi 40-60 slov), pokud ho playbook typu uvádí
- u článků nad ~1 200 slov přidej box „Shrnutí v kostce" (3-5 odrážek) hned za úvod

Používej data a zkušenostní signály pravdivě:

- Reálnou zkušenost použij jen pokud je ve zdrojích.
- Pokud zkušenost nemáš, používej agregované vzorce, logické before/after scénáře nebo veřejně ověřitelná data.
- Nevymýšlej jména lidí, výsledky, studie ani formulace typu „z naší zkušenosti", pokud nejsou opřené o brand/research kontext.

**Anti-slop průchod** (`{baseDir}/references/anti-slop.md`) — po dopsání a PŘED self-auditem projdi celý text proti pravidlům lidského jazyka: zakázaný slovník AI klišé (najdi a nahraď), střídavý rytmus vět a odstavců, max 1 trojice-výčet na sekci, pomlčka „—" střídmě, konkrét ke každému obecnému tvrzení, test čtení úvodu a závěru nahlas.

### 5. CTA podle typu

- **Redakční typy** (návod, listicle, průvodce, datová studie, explainer, thought leadership): **jedna konkrétní CTA v závěru**.
- **Konverzní typy** (srovnání, case study, prodejní článek): CTA strategie dle playbooku — typicky měkká CTA po prvním důkazním bloku + tvrdá CTA v závěru; u srovnání navíc hned po verdiktu. Nikdy víc CTA, než playbook uvádí.

### 6. Self-audit

Před uložením zkontroluj:

- Článek má něco, co čtenář nenajde v běžném generickém výsledku (information gain je splněný, ne jen deklarovaný).
- Odpověď na hlavní otázku článku zazní v prvních 60 slovech.
- Struktura odpovídá playbooku typu (listicle má číslici v H1 a položky jako H2; srovnání má tabulku; prodejní článek má správné CTA a případné označení).
- Začátek i konec zní jako stejný autor.
- Text používá konkrétní příklady nebo data, ne vágní tvrzení; čísla mají uvedený zdroj.
- Neobsahuje vymyšlené studie, osoby ani výsledky.
- Pokud běžel deep research, klíčová čísla sedí na `dossier.json` (findings se zdrojem); nedoložené věci (gaps) nejsou v článku uvedené jako fakt.
- Primární keyword je co nejblíž začátku title tagu, v H1, prvních 100 slovech, vhodně v H2 a v závěru.
- Titulek prošel dílnou: vznikl výběrem z 5-10 variant a splňuje 4U kontrolu (headlines.md).
- Článek prošel anti-slop průchodem: žádné klišé ze zakázaného slovníku, střídavý rytmus vět, pomlčky střídmě, obecná tvrzení mají konkrét (anti-slop.md).
- Interní odkazy: 2-5 s popisným anchorem (pokud content-log existuje).
- Meta description má ideálně 150-160 znaků, minimálně 140 znaků, a funguje jako mini-pitch.
- Článek je review-ready bez ručních placeholderů.

## Režim REFRESH (aktualizace existujícího článku)

1. Načti existující `article.html` + `article-metadata.json` z `/documents/content/blog/{slug}/`. Když tam není, zkus starší umístění `/documents/brand/content/blog/{slug}/` (články před sjednocením cest) — aktualizovanou verzi pak ulož už do `/documents/content/blog/{slug}/`. Pokud článek nenajdeš nikde, požádej o text nebo URL.
2. Urči, CO je zastaralé: důvod ze zadání (změna ceny, parametru, názvu) · stará čísla a příklady · posunutý search intent · chybějící otázky, které dnes lidé řeší.
3. Aktualizuj **podstatně, ne kosmeticky**: vyměň zastaralé statistiky za aktuální se zdrojem, přepiš answer-first úvod podle dnešního intentu, doplň nové otázky jako H2/FAQ, aktualizuj příklady, doplň interní odkazy na novější články, smaž sekce, které už neodpovídají intentu.
4. **Slug ani URL nikdy neměň.** Do metadata doplň `refreshedAt` (YYYY-MM-DD) a `refreshReason` (1 věta). Obrázkové briefy měň jen pokud vizuály zastaraly.
5. Handoff: stručně co se změnilo (podklad pro publisher update) + připomeň zapsat refresh do `/documents/content/content-log.md`.

Změna data bez podstatné změny obsahu je zakázaná — vyhledávače ji ignorují a podkopává důvěru.

## article.html

Piš čisté HTML bez `<html>`, `<head>` a `<body>`. Obrázky nevkládej.

Povolené tagy:

```text
<h1>, <h2>, <h3>, <p>, <strong>, <em>, <ul>, <ol>, <li>, <blockquote>, <a>,
<table>, <thead>, <tbody>, <tr>, <th>, <td>
```

Nepoužívej CSS, třídy, inline styly, `<div>`, `<span>` ani `<section>`. Tabulky drž jednoduché (bez colspan/rowspan).

Na začátek vlož metadata komentář:

```html
<!--
ARTICLE METADATA
Title: {title}
Slug: {slug}
Article type: {article_type}
Meta description: {meta_description}
Primary keyword: {primary_keyword}
Secondary keywords: {secondary_keywords}
Redakční pojetí: {editorial_angle}
Framework: {framework}
Hook type: {hook_type}
Information gain: {information_gain}
CTA: {cta}
-->
```

## article-metadata.json

Ulož minimálně:

```json
{
  "title": "Název článku",
  "slug": "nazev-clanku",
  "articleType": "listicle",
  "metaDescription": "Meta description...",
  "primaryKeyword": "keyword",
  "secondaryKeywords": ["keyword 2"],
  "editorialAngle": "redakční pojetí",
  "framework": "PAS",
  "hookType": "contrarian statement",
  "informationGain": "Co článek přináší navíc.",
  "cta": "Konkrétní CTA",
  "articlePath": "/documents/content/blog/{slug}/article.html",
  "imageBriefsPath": "/documents/content/blog/{slug}/image-briefs.json"
}
```

`articleType` je jeden z: `navod`, `listicle`, `kompletni-pruvodce`, `srovnani`, `case-study`, `prodejni-clanek`, `datova-studie`, `thought-leadership`, `explainer`. V režimu REFRESH přidej `refreshedAt` a `refreshReason`. `slug` drž krátký (4-7 slov, s primárním keywordem, bez roku a diakritiky) — kratší URL mají vyšší proklik i víc citací v AI.

## image-briefs.json

Obrázky připrav jako provider-neutral briefy. Nepiš „Nano Banana" ani „GPT Image 2" do briefu, pokud to uživatel výslovně nevyžádal.

```json
{
  "articleSlug": "{slug}",
  "articleTitle": "{title}",
  "briefs": [
    {
      "id": "hero",
      "placement": "hero",
      "filename": "hero.png",
      "aspectRatio": "16:9",
      "alt": "Popis obrázku pro alt text",
      "prompt": "English image prompt with subject, scene, style, composition, lighting, mood. NO text, NO logos, NO watermarks."
    },
    {
      "id": "section-1",
      "placement": "after_h2:3",
      "supportsSections": [1, 2, 3],
      "visualType": "process",
      "purpose": "Proč obrázek pomáhá konkrétnímu bloku textu.",
      "filename": "section-1.png",
      "aspectRatio": "16:9",
      "alt": "Alt text",
      "prompt": "English image prompt..."
    }
  ]
}
```

Hero image je povinný.

Podpůrné obrázky plánuj podle struktury článku, ne jen podle počtu slov:

- po každých 2-3 H2 sekcích navrhni jeden podpůrný obrázek
- obrázek musí podporovat konkrétní část textu, ne jen dekorovat článek
- poslední obrázek neumísťuj na konec článku ani za poslední H2 sekci
- pokud poslední blok obsahuje jen závěr, shrnutí nebo CTA, obrázek už nepřidávej
- u krátkých článků do 4 H2 sekcí stačí hero + 0-1 podpůrný obrázek
- u běžných článků s 5-8 H2 sekcemi použij typicky hero + 2-3 podpůrné obrázky
- u delších článků s 9+ H2 sekcemi použij typicky hero + 3-4 podpůrné obrázky

Před vytvořením `image-briefs.json` projdi H2 sekce a seskup je do bloků po 2-3 sekcích. Pro každý blok rozhodni, jestli vizuál skutečně pomůže čtenáři.

Vizuál může být:

- realistická ilustrační fotografie
- jednoduchý diagram bez drobného textu
- procesní schéma
- srovnávací vizuál
- praktická ukázka situace
- mood/context image, pokud podporuje téma bloku

Infografiky s přesným textem negeneruj jako obrázek, pokud text musí být čitelný a přesný. Přesný text, čísla, tabulky a checklisty patří do HTML článku; obrázek může být jen vizuální podpora.

Každý podpůrný brief musí uvést:

- které H2 sekce podporuje (`supportsSections`)
- proč tam obrázek patří (`purpose`)
- typ vizuálu (`visualType`: `photo`, `diagram`, `process`, `comparison`, `context`, `illustration`)
- placement ve formátu `after_h2:{index}`, nikdy za poslední H2

Před handoffem proveď kontrolu:

- spočítej přibližný počet slov článku a počet H2 sekcí
- urč minimální počet briefů podle strukturálních pravidel výše
- pokud `briefs.length` neobsahuje povinný hero + minimální počet podpůrných obrázků, není hotovo; doplň další funkční briefy před předáním
- samotný hero nestačí pro článek s 5+ H2 sekcemi
- žádný podpůrný brief nesmí mít placement za poslední H2 sekcí nebo čistě po závěru/CTA

## handoff.md

Na závěr ulož krátký handoff:

```markdown
# Article Handoff

- Article: `/documents/content/blog/{slug}/article.html`
- Article type: `{article_type}`
- Metadata: `/documents/content/blog/{slug}/article-metadata.json`
- Image briefs: `/documents/content/blog/{slug}/image-briefs.json`
- Image brief count: `{brief_count}`; words: `{word_count}`; H2 sections: `{h2_count}`

## Next steps

1. Generate images with `article-image-generator`.
2. Upload assets with target publisher assets command: `wordpress-publisher assets` or `cliqsales-blog-publisher assets`.
3. Create draft with target publisher: `wordpress-publisher draft` or `cliqsales-blog-publisher draft`.
```

## Zakázané vzory

- Nepublikuj článek do WP/GHL.
- Negeneruj obrázky v tomto skillu, pokud uživatel výslovně nepožádá o celý pipeline přes `content-strategist`.
- Nevkládej placeholdery typu `TODO`, `EXPERIENCE HERE` nebo `IMAGE HERE`.
- Nevytvářej paralelní cesty mimo `/documents`.
- Neříkej „úhel" jako jediný termín v uživatelském výstupu; preferuj „redakční pojetí" nebo „pojetí článku".
- Netvrď, že je WordPress/Yoast SEO nebo CliqSales/GHL metadata vyplněné; tento skill pouze připravuje SEO metadata pro publishing krok.
- Prodejní článek publikovaný mimo vlastní platformu (cizí médium, placená native distribuce) musí nést zákonné označení (např. „Komerční sdělení"). Na vlastní platformě se označení nevyžaduje.
- Neměň datum publikace bez podstatné změny obsahu.
