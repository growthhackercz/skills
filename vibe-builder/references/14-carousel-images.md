# Carousel images — sada 6 snímků pro prodejní stránku

Načti spolu s `13-sales-page.md`, když stavíš prodejní stránku a potřebuješ
obrazy. Obecná pravidla obrázků (priority zdrojů, řetězení světa, slug mapping)
jsou v `07-images.md` — tenhle soubor řeší **konverzní sadu 6 snímků** pro
carousel a obrazy pro ostatní sekce stránky.

> **Je-li ve workspace skill `product-image-generator`, použij jeho** — má
> doslovné odladěné prompty (framework Olivera Kenyona / ConversionWise),
> validátor sady a upscale. Tenhle soubor je plnohodnotná náhrada pro případ,
> že ve workspace není.

## Sada = 6 typů, jen pro carousel

| # | Soubor | Účel | Text v obraze |
|---|---|---|---|
| 1 | `01-hero.jpg` | **výsledek**, ne produkt — „tohle chci“ | žádný |
| 2 | `02-nabidka.jpg` | co přesně dostane (balíček, záruka, dárky) | nadpis + 2–3 body |
| 3 | `03-social-proof.jpg` | důvěra, UGC styl, spokojení zákazníci | hodnocení + krátký citát |
| 4 | `04-detail.jpg` | jedno nejsilnější USP, materiály, složení | 3–4 popisné callouty |
| 5 | `05-pred-po.jpg` | emoční kontrast problém → řešení | PŘED / PO + co se změnilo |
| 6 | `06-lifestyle.jpg` | identita, „tímhle člověkem chci být“ | žádný |

**Sada nahrazuje popis produktu v e-shopu.** Zákazník má příběh přečíst
z carouselu samotného, z kombinace obrazu a textu v něm — proto karty 2 až 5
nesou **víc textu, než se zdá nutné**: nadpis a k němu dva až tři nosné body,
ne jediné slovo. Karty 1 a 6 zůstávají čistě obrazové, ty prodávají atmosféru.

Text musí být čitelný **v náhledu, ne až po rozkliknutí** — velký, na světlé
nebo poloprůhledné destičce, nikdy drobným písmem přes fotku. Držte krátké jisté
řetězce (dvě až čtyři slova na řádek); dlouhé české věty s diakritikou model
komolí, u kratších je spolehlivý. Každý vygenerovaný text si po vykreslení
**přečti a zkontroluj** — zkomolené slovo je důvod snímek zahodit.

**Carousel stojí sám o sobě.** Těchhle 6 snímků žije jen v sekci 10.
Obrazy do ostatních sekcí stránky (hero, sociální důkaz, komponenty, předtím /
potom, stack, případovka, příběh) se generují **samostatně** — viz „Obrazy mimo
carousel“ níže. **Nikdy nepoužij kartu z carouselu podruhé jinde na stránce**;
opakovaný obraz stránku okamžitě zlevní.

Jediná povolená výjimka: hero stránky smí být totožný s `01-hero.jpg`, pokud
scéna sedí. I tak je lepší mít pro hero vlastní snímek.

## Jak sada vypadá na stránce

Pás jde **přes celou šířku okna (full-bleed)**, ne uvnitř obsahového sloupce:
tři plné karty, po krajích ukrojené karty, kulaté šipky přes ty kraje, tečky pod
pásem. Nad pásem jen eyebrow a nadpis, **žádný podnadpis**. Ověřený vzor je `.wf-carousel` na AIQ prodejní
stránce (vodorovný flex, mezera 10 px, zaoblené zhruba čtvercové karty). Detail
sekce a chování je v `13-sales-page.md` → sekce 10.

## Hmatatelnost — nejdůležitější pravidlo sady

Zákazník musí **vidět, jak se to používá**. Studiový packshot na bílém pozadí
neprodává ani fyzický produkt, natož službu.

- **Minimálně 4 ze 6 snímků jsou lifestyle nebo mockup** — reálné prostředí,
  reálný člověk, reálné použití. Čistý produkt na pozadí smí být maximálně
  u typu 4 (detail).
- **Fyzický produkt** → v prostoru, v rukou, v provozu; vidět měřítko a kontext
  (kdo, kde, při čem).
- **Digitální produkt** → **mockupy**: telefon v ruce, notebook na stole,
  dashboard na monitoru v reálné scéně — a **člověk, který v tom pracuje**.
  Samotný screenshot bez zařízení a bez člověka je slabý.
- **Služba** → **lifestyle fotky**: člověk, který službu dostává, prostor před
  a po zásahu, výstup držený v ruce (report, plán, hotová věc), průběh práce.
  Služba se nezobrazuje ikonou ani abstraktní grafikou.

**Displeje:** kdykoli je v obraze telefon, notebook nebo tablet, do promptu
napiš, že obrazovka míří **čelem ke kameře**, obsah je vzpřímený a čitelný,
nikdy zrcadlený, obrácený, roztažený ani zdeformovaný, zařízení má reálné
proporce a člověk hledící na displej sedí na stejné straně jako viditelná
obrazovka. Bez téhle klauzule to model plete.

## Vstupy

**Povinné:** aspoň jedna reálná fotka produktu ve
`/documents/brand/products/<slug>/images/`. Bez ní si model produkt domyslí
a věrnost je pryč — vyžádej ji a zastav. U služby stačí fotka z realizace,
prostoru nebo výstupu; u digitálního produktu screenshot skutečné aplikace.

**Volitelné, ale silně doporučené:** `productDNA.md` (úhly a benefity),
`brandDNA.md` (paleta, tón, fotografický styl), `brand-board.png` (vizuální
jazyk jako reference, ne předloha ke kopírování). Když chybí, řekni to nahlas —
výsledek bude generická prémiová art direction, ne věrná značka.

## Engine a volání

Nativní tool **`image_generate`** (GPT Image 2). Reference se předávají
parametrem **`images`** (pole cest, max 3), rozměr parametrem `size` — ne textem
promptu. Cesty jsou runtime `/home/node/documents/...`.

```
image_generate:
  prompt:       <celý prompt typu, dosazené {PRODUCT} {BRAND_CONTEXT} {ANGLE}>
  images:       ["…/products/<slug>/images/<foto>.jpg",
                 "…/products/<slug>/carousel/01-hero.jpg",   # u typů 2–6 = style anchor
                 "…/brand/brand-board.png"]
  size:         "1024x1024"
  quality:      "medium"
  outputFormat: "jpeg"
  filename:     "…/products/<slug>/carousel/0N-<typ>.jpg"
```

Fallback při výpadku nativního toolu: FAL `openai/gpt-image-2/edit` s `image_urls`
(per-image náklad z klientova `FAL_KEY`). **Model je v obou cestách GPT Image 2** —
Flux ani Ideogram nikdy, rozbíjí konzistenci světa. FAL smí spustit jen
přiřazený helper s `--dry-run` a kumulativním `--max-usd`; bez něj se fallback
zastaví, žádné přímé API/inline volání. Detail v `07-images.md`.

## 🛑 Brána věrnosti produktu — nejčastější tiché selhání

Model si produkt vymyslí, kdykoli reference nedorazí. Výsledek vypadá dobře,
ale je to **jiný přístroj**: jiný ovládací panel, chybějící logo, jiné
proporce. Na stránce klienta je to neomluvitelné a v QA to nikdo nechytí,
protože obrázek sám o sobě vypadá hezky.

**1. Reference musí být nahraná, ne jen zmíněná.**
Cesta k souboru v promptu **není reference**. Referencí je až fotka předaná
nástroji jako obrázek — u nativního `image_generate` v poli `images`. Bez toho
generuješ naslepo, i když máš cestu k fotce napsanou v promptu.

⚠️ **Kroky 1 a 2 níž popisují Magnific/Freepik MCP, který je jen v dev labu.
Na klientském VPS nemusí být — pak jeď přes nativní `image_generate`
s `images: [...]` a zbytek brány (kroky 3–5) platí beze změny.**

Je-li Magnific/Freepik MCP dostupný: soubor **nejdřív nahraj**
(`creations_upload_image`, případně `creations_request_upload` +
`creations_finalize_upload`) a teprve vrácený **identifier** předej v poli
`references: [{type: "image", identifier: "…"}]`.

**2. Pro celou sadu založ produktové aktivum** (jen s Magnific/Freepik MCP).
`library_create` s typem `product` a 3+ fotkami reálného produktu z různých
úhlů → v generování pak odkazuj `references: [{type: "product", identifier: <id>}]`.
Tohle drží tentýž produkt napříč všemi snímky líp než jedna fotka. Bez MCP
předávej stejné 3+ fotky v `images` u každého snímku.

**3. STOP po prvním snímku — porovnej s referencí.**
Otevři vygenerovaný snímek **vedle referenční fotky** a projdi:
- tvar a proporce těla, dělení bílé a tmavé části
- ovládací panel: pozice, počet a rozvržení prvků
- **logo**: je tam, kde je fyzicky na produktu, ve správné podobě?
- nožička, mřížka, rukojeť, poměr výšky k šířce

**Když cokoli nesedí, zbytek sady negeneruj.** Oprav řetěz referencí a pilot
zopakuj. Deset krásných snímků cizího přístroje je horší než jeden správný.

**4. Když věrnost nejde uhlídat ani s referencí**, máš tři cesty v tomhle
pořadí:
- FAL `openai/gpt-image-2/edit` s `image_urls` (per-image náklad, ale drží
  předlohu nejlíp)
- **kompozice**: vygeneruj scénu bez produktu a vlož do ní výřez reálné fotky
  (produkt zůstane 1:1)
- **přerámuj scénu** tak, aby produkt nebyl hrdina snímku — částečně v záběru,
  z odstupu, hlavní roli nese člověk a prostředí

**5. Logo si model nesmí vymýšlet.** Žádné logo jako grafický overlay; značení
jen tam, kde je fyzicky na produktu, a přesně podle reference. Vymyšlené logo
je důvod snímek zahodit, ne opravit textem vedle.

## Placeholdery

**`{PRODUCT}`** = název + krátký věcný popis reálného produktu nebo služby
z Product DNA.

**`{BRAND_CONTEXT}`** = vlož hned za první větu promptu, anglicky:

```
Brand mood: {paleta HEX}, {emoční tón}, {fotografický styl}. Use the attached
photo as the exact, faithful reference for the real product — same shape,
proportions, colors and details; do not invent a different product. Render NO
brand logo, wordmark, badge or watermark as a graphic overlay; keep only
markings physically on the product. All visible text strictly in {jazyk trhu}
with correct diacritics. Premium editorial voice — confident, benefit-led,
never hard-sell or discount-flyer. Modern editorial typography: short punchy
mixed-case headlines (max 2–3 lines, clearly legible semi-bold, never thin),
generous whitespace, text on light or translucent panels — never heavy dark
blocks. Photography must be bold and premium: rich tonal contrast, depth,
dramatic but tasteful lighting, magazine-grade. This card emphasizes a
DIFFERENT angle than the other cards — never repeat a headline, claim or
benefit list across the set. Feature visually DIFFERENT people on each card
(vary age, gender, household); keep only brand style, lighting and the product
consistent, NOT the people. ONE clear composition per card — no busy collage
of mini-panels. Any screen in frame faces the camera, content upright and
legible, never mirrored, flipped or distorted.
```

Bez `brandDNA.md` nech jen obecný prémiový tón a barvy vynech — nevymýšlej
brand prvky.

**`{ANGLE}`** = pro každý typ **jiný konkrétní úhel z Product DNA**, aby sada
nesla šest argumentů, ne šestkrát jeden:

| Karta | úhel čerpá z |
|---|---|
| 1 Hero | hlavní kýžený výsledek / transformace |
| 2 Nabídka | co klient dostane — balíček, záruka, dárky |
| 3 Social proof | doložitelný důkaz důvěry (počet zákazníků, certifikace, testy) |
| 4 Detail | jedno nejsilnější USP + konkrétní vlastnosti |
| 5 Před→po | konkrétní bolest → úleva |
| 6 Lifestyle | identita cílovky a její hodnoty |

## Kostra promptu

Základ je společný, mění se první věta a blok „Focus“:

```
Create a premium, ultra high-definition ecommerce {TYP} image for {PRODUCT}.
{BRAND_CONTEXT}
Card angle (unique to this card): {ANGLE}
Focus: {co má karta udělat — viz tabulka typů}
Style: premium DTC aesthetic, clean composition, cinematic lighting, soft
natural shadows, high contrast, mobile-first composition, realistic textures,
ultra sharp focus, minimal clutter, shallow depth of field, aspirational
lifestyle vibe, high-end advertising photography.
Include: a realistic human interacting naturally with the product, emotion,
strong visual hierarchy.
Avoid: generic stock photo feel, busy backgrounds, fake-looking AI hands or
faces, cluttered props, multiple focal points.
Format: exact 1:1 square aspect ratio, all elements centered for mobile
cropping, product instantly recognizable at thumbnail size, consistent
lighting and polish across the whole set.
Output: photorealistic, conversion-focused premium campaign image.
```

Deltas per typ v poli `Focus:`
1 **Hero** — výsledek a transformace, ne produkt; jeden čistý fotografický obraz.
2 **Nabídka** — nabídka čitelná na první pohled, produkt zůstává dominantní.
3 **Social proof** — UGC styl, reálný člověk, hvězdy a krátký citát recenze.
4 **Detail** — Apple-style detail, materiály nebo složení, popisné callouty.
5 **Před→po** — stejná scéna dvakrát, štítky PŘED / PO, emoční kontrast.
6 **Lifestyle** — aspirace a identita, produkt přirozeně ve scéně, minimum textu.

## Postup

1. **STOP před generováním** — ukaž počet volání (1 pilot + zbytek sady),
   cílovou složku a rozměr. Bez „ano“ negeneruj, pálí to kredity.
2. **Pilot: hero** (`01-hero.jpg`) → ukaž a nech schválit styl a věrnost.
3. **Zbytek sady** — schválený hero jde jako **2. reference** (style anchor).
   Anchor drží **jen světlo, styl a produkt, ne lidi** — na každé kartě musí být
   viditelně jiní lidé.
4. **Kontrola sady:** všechny snímky mají stejné rozměry a poměr 1:1, produkt je
   poznatelný v náhledu, žádné dvě karty neopakují stejný nadpis ani stejný
   spodní pás, aspoň 4 snímky jsou lifestyle nebo mockup.
5. **Iterace po kusech** — regeneruj jednotlivý typ, ne celou sadu.

Pojmenování: `01-hero.jpg` · `02-nabidka.jpg` · `03-social-proof.jpg` ·
`04-detail.jpg` · `05-pred-po.jpg` · `06-lifestyle.jpg`, složka
`/documents/brand/products/<slug>/carousel/`.

## Obrazy mimo carousel

Každá sekce stránky, která má obraz, dostane **vlastní snímek s vlastní scénou**.
Postup je stejný jako u sady, mění se jen úkol snímku:

- **Reference produktu je vždy první v `images`** — tím drží věrnost produktu.
  Tohle platí pro každý obraz na stránce, ne jen pro carousel. Bez reálné fotky
  si model produkt domyslí a stránka přestane být důvěryhodná.
- **Style anchor** (schválený hero) přidej jako druhou referenci, aby světlo,
  grading a produkt seděly napříč stránkou — ale **scéna, lidé i prostředí musí
  být jiné** než na kartách carouselu.
- Ke každé sekci si napiš jednou větou, **co má obraz dokázat**, a z toho udělej
  `Focus:` v promptu:

| Sekce | Co má obraz dokázat |
|---|---|
| 1 Hero | výsledek v reálném prostředí, lifestyle, člověk po nákupu |
| 3 Zrcadlo problému | ten problém, jak vypadá v jeho dni |
| 4 Sociální důkaz | reálný zákazník s produktem, UGC charakter |
| 7 Předtím / potom | stejná scéna dvakrát, jiné světlo a stav |
| 8 Komponenty | každá komponenta zvlášť, detail v použití |
| 11 Value stack | celý balíček pohromadě — co přijde |
| 13 Případová studie | konkrétní realizace nebo zákazník |
| 17 Příběh vzniku | portrét zakladatele, dílna, prostředí vzniku |

Ukládej je mimo složku carouselu (např. `…/products/<slug>/page/`), ať se
sady nemíchají.

## Když sada nejde vyrobit

Chybí-li jakýkoli reálný podklad (fotka, screenshot, snímek z realizace),
**neposkládej stránku z generických stock scén** — vyžádej podklad a řekni,
co konkrétně potřebuješ. Carousel se skrývá až tehdy, když nejsou aspoň
4 použitelné snímky (viz `13-sales-page.md`).
