---
name: article-writer
description: "Vytvářejte kvalitní výzkumně podložené články s redakčním pojetím, SEO metadaty, review-ready HTML a provider-neutral briefy pro obrázky. Použijte pro náročnější blogové články, thought leadership, SEO obsah a články určené k pozdější publikaci."
category: content
status: ready
version: "1.0"
publishedAt: "2026-04-30"
---
# Article Writer

Tento skill je pokročilý autor článků. Produkuje text, metadata a briefy pro obrázky. Negeneruje obrázky, neuploaduje assety a nepublikuje do WordPressu ani GHL.

Použij ho pro blogové články, thought leadership, SEO obsah i články, které později převezme `wordpress-publisher` nebo `cliqsales-blog-publisher`.

## Výstupy

Ulož vše do jedné složky:

```text
/documents/brand/content/blog/{slug}/
├── article.html
├── article-metadata.json
├── image-briefs.json
└── handoff.md
```

`article.html` je čisté review-ready HTML bez vložených obrázků. `image-briefs.json` je vstup pro `article-image-generator`. SEO metadata v `article-metadata.json` jsou zdroj pro publishing; finální mapování do cílového systému řeší `wordpress-publisher` nebo `cliqsales-blog-publisher`.

## Workflow

### 1. Načti kontext

1. Načti `/documents/brand/brandDNA.md`.
2. Pokud téma souvisí s produktem, načti `/documents/brand/products/{product-slug}/productDNA.md`.
3. Pokud existuje research brief z `trending-research`, použij ho jako zdroj insightů a dat.
4. Pokud existuje `/documents/brand/content/content-log.md`, ověř duplicity a navrhni interní prolinkování.

Pokud chybí zásadní brand/product kontext, zeptej se na chybějící vstup. Pokud chybí jen volitelné detaily, pokračuj s jasně uvedenými předpoklady.

### 2. Výzkum a pojetí

Než začneš psát, rozhodni, proč má článek existovat.

1. **Competitive scan** - pokud je dostupné webové vyhledávání, projdi 5-10 relevantních výsledků. Najdi konsenzus, mezery a slabiny. Pokud web není dostupný, použij research brief, brand/product DNA a známý kontext.
2. **Information gain** - napiš jednu větu, co článek přináší navíc oproti běžným textům.
3. **Redakční pojetí** - zvol jeden pohled na téma: kontrariánský, praktický z praxe, myth-busting, srovnávací, behind-the-scenes, predikční nebo zaměřený na konkrétní problém.
4. **Hook** - vyber typ otevření: silné tvrzení, konkrétní číslo, začátek uprostřed situace, relatable pain, credibility + promise nebo otázka měnící perspektivu.

Nepoužívej defaultní pojetí typu „Kompletní průvodce X“ nebo „Vše, co potřebujete vědět o X“, pokud si ho uživatel výslovně nepřeje.

### 3. Story framework

Vyber jeden framework podle tématu:

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
- redakční pojetí
- framework
- co už bylo řečeno, aby se text neopakoval

Každý článek musí obsahovat:

- konkrétní H1
- intro s hookem, kontextem a příslibem hodnoty
- 5-7 H2 sekcí podle délky
- závěr jako syntézu, ne mechanické shrnutí
- jednu konkrétní CTA

Používej data a zkušenostní signály pravdivě:

- Reálnou zkušenost použij jen pokud je ve zdrojích.
- Pokud zkušenost nemáš, používej agregované vzorce, logické before/after scénáře nebo veřejně ověřitelná data.
- Nevymýšlej jména lidí, výsledky, studie ani formulace typu „z naší zkušenosti“, pokud nejsou opřené o brand/research kontext.

### 5. Self-audit

Před uložením zkontroluj:

- Článek má něco, co čtenář nenajde v běžném generickém výsledku.
- Začátek i konec zní jako stejný autor.
- Text používá konkrétní příklady nebo data, ne vágní tvrzení.
- Neobsahuje vymyšlené studie, osoby ani výsledky.
- Primární keyword je v H1, prvních 100 slovech, vhodně v H2 a v závěru.
- Meta description má ideálně 150-160 znaků, minimálně 140 znaků, a funguje jako mini-pitch.
- Článek je review-ready bez ručních placeholderů.

## article.html

Piš čisté HTML bez `<html>`, `<head>` a `<body>`. Obrázky nevkládej.

Povolené tagy:

```text
<h1>, <h2>, <h3>, <p>, <strong>, <em>, <ul>, <ol>, <li>, <blockquote>, <a>
```

Nepoužívej CSS, třídy, inline styly, `<div>`, `<span>` ani `<section>`.

Na začátek vlož metadata komentář:

```html
<!--
ARTICLE METADATA
Title: {title}
Slug: {slug}
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
  "metaDescription": "Meta description...",
  "primaryKeyword": "keyword",
  "secondaryKeywords": ["keyword 2"],
  "editorialAngle": "redakční pojetí",
  "framework": "PAS",
  "hookType": "contrarian statement",
  "informationGain": "Co článek přináší navíc.",
  "cta": "Konkrétní CTA",
  "articlePath": "/documents/brand/content/blog/{slug}/article.html",
  "imageBriefsPath": "/documents/brand/content/blog/{slug}/image-briefs.json"
}
```

## image-briefs.json

Obrázky připrav jako provider-neutral briefy. Nepiš „Nano Banana“ ani „GPT Image 2“ do briefu, pokud to uživatel výslovně nevyžádal.

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

- Article: `/documents/brand/content/blog/{slug}/article.html`
- Metadata: `/documents/brand/content/blog/{slug}/article-metadata.json`
- Image briefs: `/documents/brand/content/blog/{slug}/image-briefs.json`
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
- Neříkej „úhel“ jako jediný termín v uživatelském výstupu; preferuj „redakční pojetí“ nebo „pojetí článku“.
- Netvrď, že je WordPress/Yoast SEO nebo CliqSales/GHL metadata vyplněné; tento skill pouze připravuje SEO metadata pro publishing krok.
