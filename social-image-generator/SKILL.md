---
name: social-image-generator
description: "Vyrábí vizuály pro sociální sítě přes GPT Image 2: karusely, quote/stat/hook karty, single post vizuály a story covery — vždy v brand stylu a s texty přesně podle zadání. Funguje z visual-briefs od social-post-writera, ale i sólo („udělejte mi karusel z tohohle článku"). Ukládá obrázky + manifest pro publisher."
category: creative
status: ready
version: "2.1"
publishedAt: "2026-07-10"
metadata: {"openclaw":{"emoji":"🎨"}}
---

# Social Image Generator

Dělník výroby social vizuálů. V dvojici zrcadlí článkovou pipeline: **social-post-writer PÍŠE (texty postů + texty na vizuály do briefů) → social-image-generator VYRÁBÍ → cliqsales-social-publisher PUBLIKUJE.**

**Výroba VÝHRADNĚ přes nativní `image_generate` (GPT Image 2) — na maximum jeho schopností.** Žádný stock (na social vyhrává brand konzistence), žádné HTML rendery, žádné ruční HTTP endpointy.

**Precedence: jednorázové social zadání od klienta/operátora vlastní `content-strategist`.** Když je nainstalovaný, na „udělejte mi karusel/post z tohohle článku" VŽDY spusť jeho (dotáhne texty, vizuály i publikaci) — tenhle skill v tom běhu funguje jen jako jeho dělník. Sólo režim (degradační žebřík níže) použij pouze, když `content-strategist` k dispozici není, nebo když si klient výslovně řekne jen o vizuály k hotovým textům.

## Vstup — degradační žebřík (plně funkční i sólo)

1. **`/documents/content/social/{slug}/visual-briefs.json`** od social-post-writera (orchestrace) — per post: typ vizuálu, texty na vizuál, formát, alt.
2. **Briefs chybí, ale existují texty postů** (social-posts.json / text od klienta): odvoď briefy sám — typ podle obsahu (návod/kroky → karusel · citát → quote karta · číslo → stat karta · jinak single) a texty na vizuál zkrať z postu.
3. **Je jen téma/článek** („udělejte mi karusel z tohohle článku"): vytáhni strukturu (H2/kroky) → texty slidů → karusel.

Nikdy neblokuj; vždy řekni, z čeho jsi vycházel.

## Typy vizuálů a formáty

| Typ | Formát (default) | Poznámka |
|---|---|---|
| **Karusel** | 4:5 (1080×1350), všechny slidy stejně | 5–8 slidů, **max 10 (IG/FB API)**; IG/FB = obrázková sada, **LinkedIn = PDF dokument** (viz limity níže); nejvyšší save-rate |
| Single post vizuál | 4:5 IG/FB · 1:1 LinkedIn | fotorealistický nebo ilustrační námět v brandu |
| Quote / stat / hook karta | 1:1 nebo 4:5 | jedno generování, velký text na brand pozadí |
| Story | 9:16 (1080×1920) | text jen v centrální safe zóně (UI overlays nahoře/dole) |

**Tvrdé limity Social Planner API (GHL) — dodržuj při výrobě:**
- **IG karusel/post:** max 10 obrázků, ≤8 MB/ks, poměr 4:5 až 1.91:1 · **FB:** max 10 obrázků, ≤10 MB
- **IG Story:** až 10 médií, obrázky **JPEG ≤8 MB** → story vizuály ukládej/konvertuj do JPEG · jen Professional účty · **API nepodporuje captions, tagy ani stickery — veškerý text MUSÍ být součástí obrázku** (přesně to děláme: text vypálený přes GPT Image 2)
- **FB Story:** pouze **1 obrázek, ≤4 MB** (JPEG/PNG) — pro FB story vyrob jediný vizuál
- **LinkedIn karusel/dokument = PDF** (GHL to umí přes „post PDF as photos"; LinkedIn limit 300 stran / 100 MB): vygeneruj slidy jako obrázky (**4:5**, dokumentový čitelný styl) a **slož je do PDF** přes `{baseDir}/scripts/slides_to_pdf.py <out.pdf> <slide-01.png>…`. Publisher pak nahraje PDF jako LinkedIn document. Držíme 5–10 slidů.
- Po uložení zkontroluj velikosti souborů; nad limit → ulož s nižší kvalitou/JPEG

**Vstupní `type` z `visual-briefs.json`** (od `social-post-writer`) mapuje na typy výše: `carousel` → Karusel · `single` → Single post vizuál · `quote-card`/`stat-card`/`hook-card` → Quote/stat/hook karta · `story-cover` → Story. Neznámý token → fallback `single`. (Writer posílá `carousel` pro IG/FB jako obrázkovou sadu, pro LinkedIn jako PDF dokument — viz LinkedIn řádek výše.)

**Struktura karuselu:** slide 1 = **COVER/HOOK — priorita č. 1** (cover rozhoduje o všem). **Vizuál-first:** bohatá editorial scéna / produkt / model jako HERO, typografie výrazná ale **integrovaná do vizuálu** — nikdy obří slovo na ploché barvě (to je placka). **Mix 2 fontů** v nadpisu (serif + kurzíva/clean sans = hravost, ne sterilní). Magazine art-direction, **střední škála** typografie, kicker nahoře. · slidy 2–N = 1 myšlenka/slide, max ~15 slov · poslední = shrnutí/CTA.

**Zóny slidu (drž napříč celým karuselem):** headline · content. **ŽÁDNÝ vpálený navigační indikátor** (tečky ani „X/N") — Instagram i LinkedIn carousel ho zobrazují **nativně** pod postem; vpálený by byl dvakrát a bral místo. Volitelně jen decentní **šipka →** na coveru pro naznačení swipe. **ŽÁDNÉ brand logo ani wordmark na slidu** — carousel logo nenosí. Jediné logo smí být **na produktu**, a to pouze když je produkt **reálný přes few-shot** (= správné logo); nikdy nenech GPT vymyslet značku/logo.

**Layout patterny (vyber podle obsahu):**
- **Číslovaný step** (nejčastější vzdělávací): cover „N kroků / chyb / tipů" → N slidů, každý `Krok X` + headline + bullety + patička.
- **Seamless karusel** (nejvyšší save-rate): jeden panoramatický design roztažený přes slidy (2160×1350 = 2 slidy, 3240×1350 = 3…), swipe = plynulý přechod. Pro silná/vizuální témata.
- **Foto + text overlay + karta:** foto pozadí + velký headline + malá karta s detailem/bullety (estetický styl).

## Brand styl (povinný u KAŽDÉHO vizuálu)

Řiď se `{baseDir}/references/brand-style.md`. **Dvě vrstvy zámku stylu:**
1. ⭐ **Few-shot reference (nejsilnější):** načti **2–4 brand vizuály** (`brand-board.png` + `brand-kit/23-inspirace-pro-instagram.png` + 1–2 reálné povedené posty) a předhoď je `image_generate` jako **style reference** — odvoď paletu/typografii/layout, **NEkopíruj** (guardrail: vodítko, ne předloha).
2. **Styl blok** v promptu: **3 barvy s rolemi** (background/text/accent, 60/30/10) + **2 fonty s hierarchií** (1 klíčové slovo větší v akcentní barvě + clean body).

Bez brand podkladů generuj neutrálně kvalitně a do manifestu dej `"brandStyle": "none"`.

## Konzistence karuselu — master šablona (kritická disciplína)

Generace jsou nezávislé, konzistenci drží PROMPT:

1. Před prvním slidem sestav **„master šablonový blok"**: vizuál-first scéna (produkt/model/prostředí jako hero), brand pozadí (3 barvy s rolemi), layout zóny (headline / content — **bez vpálených navigačních teček**, ty má platforma nativně), **mix 2 fontů** („high-contrast serif + italic script or clean sans, medium scale, integrated with the image"), styl dekorace. Bez brand logo na slidu. 
2. **Opakuj blok DOSLOVA u každého slidu** — měň jen text slidu a označení „slide 3/7". Blok mezi slidy nikdy nepřeformulovávej.
3. Texty na vizuál piš do promptu PŘESNĚ v uvozovkách, česky s diakritikou + „exactly as written, correct Czech diacritics".
4. Hotové slidy zkontroluj vedle sebe — vybočující slide přegeneruj se STEJNÝM blokem (1 retry; pak text zkrať/zjednoduš).

## Grid — střídání, ne uniformita

Napříč kampaní/plánem **záměrně střídej typy** (karusel · quote karta · foto · reel cover) a **light/dark varianty** — ale drž **jeden systém** (3 barvy s rolemi, 2 fonty, layout logika). Cíl: profil = **jedna značka, ale ne kopírák**.
**Grid test:** oddal profil — vypadá prvních ~9 postů jako jeden svět? Vše identické → přidej rozlišnost (jiný typ, jiná dominantní barva ze 3). Vše jiné → sjednoť systém.

## Variations + face-lock (na vyžádání)

- **Variations (A/B):** z jednoho schváleného vizuálu vyrob 2–3 barevné/textové varianty na test (jiná dominantní barva ze 3, jiný hook text). Spusť na „udělej varianty".
- **Face-lock (founders / personal brand):** je-li ve vizuálu reálná osoba (Pavel, Tomáš, klientský majitel), zamkni identitu — reálné foto jako reference + „preserve exact face/identity, do not stylize the face". Pro personal-brand posty.

## Workflow

1. Získej briefy (žebřík výše); u karuselu zkontroluj počet slidů (5–8) a délky textů (≤15 slov/slide) — delší zkrať (jsi copywriterův editor, ne přepisovač: smysl zachovej).
2. **Kreditový checkpoint:** batch nad ~15 obrázků → nejdřív souhrn („12 postů, z toho 2 karusely = 24 obrázků") a čekej na potvrzení. Single/karta/1 karusel → jeď rovnou. **Výjimka: když zadání říká, že výroba běží ze SCHVÁLENÉHO plánu/kalendáře (od strategista), checkpoint přeskoč** — klient už výrobu schválil, druhé ptaní je otrava.
3. **Načti 2–4 few-shot reference** (brand-board + `23-inspirace-pro-instagram.png` + reálné posty). Sestav master blok (u karuselu) / brand blok (vždy) a generuj přes `image_generate` **s referencemi** (odvoď styl, nekopíruj).
4. Ulož do `/documents/content/social/{slug}/images/` (`slide-01.png…`, `post-{id}.png`, `cover.png`). **LinkedIn carousel:** po uložení slidů je slož do PDF přes `python3 {baseDir}/scripts/slides_to_pdf.py {slug}/images/{postId}-linkedin.pdf {slug}/images/{postId}-slide-01.png …` (výstup do `images/`).
5. Ověř texty na vizuálech (diakritika, překlepy) — vadné přegeneruj (max 1 retry per obrázek, pak zjednoduš text).
6. Zapiš `/documents/content/social/{slug}/image-manifest.json`.

## image-manifest.json

```json
{
  "slug": "{slug}",
  "generatedAt": "YYYY-MM-DDTHH:mm:ssZ",
  "brandStyle": "designmd",
  "items": [
    {
      "postId": "post-2",
      "type": "carousel",
      "aspectRatio": "4:5",
      "slides": [
        {"order": 1, "filename": "post-2-slide-01.png", "text": "Hook text", "alt": "Alt slidu 1"},
        {"order": 2, "filename": "post-2-slide-02.png", "text": "Myšlenka 1", "alt": "Alt slidu 2"}
      ]
    },
    {"postId": "post-3", "type": "single", "aspectRatio": "4:5", "filename": "post-3.png", "alt": "Alt"}
  ]
}
```

`cliqsales-social-publisher` z manifestu nahrává média ve správném pořadí (`slides[].order`). **U LinkedIn carousel** přidej k položce `pdfFile` (cesta k PDF) — publisher nahraje PDF jako LinkedIn document; `slides[]` slouží jako záloha/náhled.

## Hranice (co NEdělá)

- **OG karty článků** → `article-image-generator` (články vč. stock rozhodování jsou jeho).
- **Video** → video větev (`html-video-generator` default pro reels z obsahu · `animated-video-generator` · `video-generator`); video koncept/scénář píše social-post-writer, tenhle skill vyrábí jen statické vizuály.
- **Reklamní kreativy** → ad skilly. **Produktové fotky** → `product-image-generator`.

## Failure handling

- `image_generate` selže → do manifestu jen úspěšné, vrať přesnou chybu; nikdy nehlaš hotový karusel s dírou (chybějící slide = přegeneruj, nebo karusel zkrať a řekni to).
- Vadný text na vizuálu po retry → zjednoduš text (kratší hook), NE ticho.
- Chybí brand podklady → neutrální generování + `"brandStyle": "none"` + poznámka v odpovědi.
- Publisher/manifest nesoulad (post bez vizuálu) → řekni, který post čeká; nevytvářej drafty s rozbitými médii.
