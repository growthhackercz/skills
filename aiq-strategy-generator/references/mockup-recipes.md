# Mockup recipes — prémiový vizuál lead magnetu pro landing page

Tento dokument popisuje workflow Krok 2.7 v `aiq-strategy-generator` skillu — generace prémiového mockupu lead magnetu jako náhledu na landing page (nad fold).

**Cíl:** Vizuální mockup výstupu kvízu, který návštěvník na landing page okamžitě „rozumí" jako hodnotný dokument / dashboard — primární CR booster (+20–50 % konverze vs. text-only landing).

**Princip:** Mockup nesmí vypadat jako generický AI obrázek. Musí působit jako reálný designerský výstup značky — prémiově, brand-konzistentně, hodnotově.

---

## Reference hierarchie (priority order)

Mockup čerpá vizuální vodítka z těchto zdrojů ve složce `/documents/brand/`:

| # | Soubor | Role | Povinné? |
|---|---|---|---|
| 1 | `brand-kit/20-magnet-na-kontakty.png` | **Primary** — jak má lead magnet v brandu vypadat (existuje, pokud klient prošel brand-kit-generator) | volitelné (silně doporučené) |
| 2 | `brand-board.png` | Brand moodboard, designový jazyk (paleta, typografie, vrstvení) | **povinné** |
| 3 | `brandDNA.md` | Text reference — sekce 6 Vizuální identita (paleta HEX, fonty, styl, ikonografie) | **povinné** |
| 4 | `logo.png` / `.jpg` / `.webp` | Přesné logo (NIKDY ne nově generované) | **povinné** |
| 5 (volitelné) | `brand-kit/16-navrh-homepage.png` | Inspirace pro landing kontext | volitelné |
| 6 (volitelné) | `brand-kit/17-hero-sekce-na-webu.png` | Inspirace pro hero sekci | volitelné |
| 7 (volitelné) | `brand-kit/19-prodejni-cesta.png` | Inspirace pro funnel kontext | volitelné |
| 8 (volitelné) | `products/[produkt-slug]/images/*` | Produktové fotky (max 5) — pokud mockup zahrnuje produktovou ukázku | volitelné |

### Fallback graceful degradation

| Co existuje | Kvalita | Co skill udělá |
|---|---|---|
| ✅ brand-kit/20 + brand-board + brandDNA + logo (+ volitelné) | **Nejvyšší** | Full reference set — primary path |
| ⚠️ chybí brand-kit/20-magnet-na-kontakty.png | **Střední** | Fallback: jen brand-board + brandDNA + logo (analog k brand-image-generator) |
| 🛑 chybí brand-board.png nebo brandDNA.md nebo logo | **Skip Krok 2.7** | Flag `[MOCKUP TBD — chybí Brand DNA / Brand Board / logo]` v `01-strategie.md` sekci 4.5. Pokračovat na Krok 3 bez mockupu. |

---

## Format

**3:4 vertikál** (např. 1200×1600 nebo 900×1200 px).

**Důvody volby 3:4:**
- Premium dokumentový feel — návštěvník asociuje s reálným hodnotovým PDF / dashboardem / dokumentem
- Funguje na desktop landing page split layout (text 50–60 %, mockup 40–50 %)
- Funguje na mobile (full-width fit, žádný extrémní ořez)
- Pokrývá všech 5 variant lead magnetu (Skóre dashboard, Audit report, Plán kalendář, Kalkulačka result, Strategie blueprint)

**Negenerujeme** v 1:1, 4:5, 2:3, 16:9 ani 9:16 — pro různé kanály lze post-generation re-render přes druhé volání s odlišnými rozměry, ale to není součást default workflow.

---

## Mockup matrix per varianta — hybrid estetika (editorial + lifestyle)

Tabulka definuje, co konkrétně grid 4×4 (16 layoutů) obsahuje pro každou variantu kvízu. Aplikuje se po schválení názvu lead magnetu z Krok 2.6.

**🎯 Estetika cíl:** **HYBRID** — kombinace 6 archetypů napříč gridem (viz sekce „Povinné archetype variety" níže) s **emocionálními domain-specific anchory** v každém layoutu. Cíl: každý layout vypadá jako premium landing page hero (NYT-level editorial OR domain-emocional anchor scene), ne jako embedded dashboard widget.

### Per varianta — vizuální obsah + povinné domain-specific elementy

| Varianta | Co mockup zobrazuje (jádro výstupu) | Povinné domain-specific emoční elementy napříč gridem |
|---|---|---|
| **🎯 Skóre / Osobní hodnocení** | Náhled výstupu hodnocení — 0–100% gauge / sub-kategorie / klíčové insights | Wellness/zdraví doména: ruce držící šálek čaje / domácí scéna spánku / běžecká scéna · Pro B2B/SaaS: dashboard graf trendu · Pro kurz: studentova workstation s laptopem |
| **🩺 Diagnostický audit** | A4 portrait PDF report — cover + sample inside page | Authority anchor: brýle na PDF / pero / profesionální tmavé pozadí · Konzultační scéna · Tištěný report s closeupem |
| **📋 Personalizovaný plán / Harmonogram** | 7/14/30-denní kalendář / habit tracker / sequential roadmap | Domain-specific: ranní rutina (hrnek kávy + planner) / domácí stůl s rodinou / sportovní gear (pro fitness) · Sequential motion feel |
| **📊 Kalkulačka přínosů** | Result dashboard — Kč úspora + breakdown + before/after | **DOMAIN-SPECIFIC POVINNÉ:** např. pro vodu = sklenice + plastové láhve + filtrační systém + kuchyně + krajina/příroda · pro AI service = team workspace + dashboard · pro kurz = ROI graf + studentova growth · pro fitness = před/po + měřič · pro e-commerce = produkty + spokojené ruce |
| **🎨 Strategický plán na míru** | A4 blueprint cover + obsah / executive summary | Premium scena: konferenční místnost / strategic whiteboard / executive desk s reportem · Roadmap timeline jako designový element · 3-pillar diagram |

**Důležité:** Mockup zobrazuje **náhled výstupu + emoční kontext domény**, ne celý funnel ani jen UI. Cíl: návštěvník landing page okamžitě cítí „tohle mi pomůže" + „tohle je premium" + „rozumím o co jde" (domain anchor).

### Povinné archetype variety napříč gridem (cíl: 6 archetypů přes 16 layoutů)

**Žádných 16 variací jedné archetype.** Grid 4×4 MUSÍ pokrýt minimálně **5 distinct archetypů** (ideálně všech 6) v této distribuci:

| # | Archetype | Layouty v gridu | Charakteristika |
|---|---|---|---|
| 1 | **HERO NUMBER** | 2 | Jedno dominantní číslo (úspora Kč / skóre % / dnů) zabírá 40–50 % plochy. Supporting elements minimalisticky pod tím. Magazine editorial style, dramatic whitespace. |
| 2 | **SIDE-BY-SIDE COMPARISON** | 3 | Předtím / Potom jako 2 velké karty vedle sebe, vizuálně kontrastní (Brand DNA primary vs accent). Žádné tabulky pod tím, jen vizuální kontrast. |
| 3 | **CHART-DOMINANT** | 3 | Donut / pie / bar / line chart zabírá 50–60 % plochy. Hero číslo jen jako label u chartu. Visual storytelling přes data viz. |
| 4 | **EDITORIAL / MAGAZINE** | 3 | Large display typography (headline jako designový element), dramatic whitespace, jeden dominantní vizuální prvek (foto / ilustrace / large chart). Hospodářské noviny / NYT feel. |
| 5 | **LIFESTYLE / EMOČNÍ** | 3 | Domain-specific scéna dominantní (pro vodu = sklenice + lahve + kuchyně; pro wellness = domácí scéna; pro B2B = team workspace). Čísla podřízena emoci. |
| 6 | **TIMELINE / JOURNEY** | 2 | Vizualizace cesty (12 měsíců, ROI projection, before→after timeline, journey map). Motion/animation feel. |

**Distribuce:** 2 + 3 + 3 + 3 + 3 + 2 = 16 layoutů, 6 archetypů. Minimum 5 archetypů = ✅, méně = porušení a regeneruj.

---

## Headline lead magnetu + logo v mockupu — KDY ANO, KDY NE

Pravidlo závisí na ARCHETYPU layoutu. **Stejné pravidlo platí pro headline i logo** — oba jsou design prvky dokumentu, ne prvky scény.

### ✅ NÁZEV LEAD MAGNETU + LOGO NA MOCKUPU

Pouze pokud mockup zobrazuje **dokumentový artefakt** (klient si představuje, že dostane konkrétní dokument):

- **EDITORIAL / MAGAZINE archetype** — PDF cover, e-book cover, blueprint cover, A4 report cover, workbook cover
- Název je očekávaný design element jako titulek na knize
- Logo je očekávaný design element jako publisher branding

### ❌ NÁZEV LEAD MAGNETU + LOGO SE NEPOUŽÍVAJÍ

Na všech ostatních archetypech — mockup zobrazuje **výsledek / scénu / data**, ne dokument:

- **HERO NUMBER** — jedno velké číslo dominuje, název/logo přebývá
- **CHART-DOMINANT** — chart je hero element
- **LIFESTYLE / EMOČNÍ** — produkt v kontextu (kuchyně, scéna), logo kazí emoční pull
- **SIDE-BY-SIDE COMPARISON** — předtím/potom karty, název/logo by mezi ně nepatřil
- **TIMELINE / JOURNEY** — vizualizace cesty bez cover frame
- **Dashboard / scorecard widget** — data jsou hero element

**Důvod:** Mockup tady zobrazuje *výsledek / scénu / data*, ne dokument. Název už žije na landing page jako H1 — duplikace kazí hierarchii. Logo na lifestyle scéně působí jako stockový product placement, kazí premium feel.

### Per varianta — default použití

| Varianta | Archetypy S NÁZVEM + LOGEM (typicky 1–3 layouty) | Archetypy BEZ (zbytek) |
|---|---|---|
| 🎯 Skóre | EDITORIAL (PDF scorecard report cover) | HERO NUMBER, CHART, LIFESTYLE, TIMELINE, SIDE-BY-SIDE |
| 🩺 Audit | EDITORIAL (A4 audit report cover) — POVINNÉ | HERO NUMBER, CHART, LIFESTYLE, SIDE-BY-SIDE |
| 📋 Plán | EDITORIAL (workbook / planner cover) — POVINNÉ | HERO NUMBER, LIFESTYLE, SIDE-BY-SIDE; TIMELINE bez cover frame |
| 📊 **Kalkulačka** | **— žádný layout s názvem ani logem** | VŠECHNY archetypy bez (kalkulačka = výsledek, ne dokument) |
| 🎨 Strategie | EDITORIAL (blueprint cover) — POVINNÉ | HERO NUMBER, CHART, LIFESTYLE, TIMELINE, SIDE-BY-SIDE |

**V 16-layout gridu typicky:**
- 3 layouty s názvem + logem (EDITORIAL archetype variations)
- 13 layoutů bez názvu a bez loga

**Pro variantu Kalkulačka:** všech 16 layoutů bez názvu i bez loga (= kalkulačka není dokument, výsledek mluví sám).

---

## Prompt template

Pro každou variantu skill sestaví prompt pro `image_generate` tool podle této šablony:

```
ROLE
Jsi prémiový brand designér a konverzně orientovaný funnelový stratég.
Tvůj výstup nesmí působit jako generický AI obrázek — musí vypadat jako
práce designéra, který zná značku, pracuje s reálným obsahem a vytváří
mockup ke konverzi.

ÚKOL
Vygeneruj **grid 4×4** (16 menších mockupů v jednom obrázku) prémiového
vizuálního náhledu lead magnetu pro značku z přiložených referencí.

**🚫 ŽÁDNÝCH 16 VARIACÍ JEDNÉ ARCHETYPE.** Grid MUSÍ pokrýt 6 distinct
archetypů přes 16 layoutů (minimum 5 archetypů = ✅, méně = porušení):

| # | Archetype | Layouty | Charakteristika |
|---|---|---|---|
| 1 | HERO NUMBER | 2 | Jedno dominantní číslo zabírá 40–50 % plochy. Magazine editorial style, dramatic whitespace. |
| 2 | SIDE-BY-SIDE COMPARISON | 3 | Předtím / Potom jako 2 velké karty vedle sebe, vizuálně kontrastní. |
| 3 | CHART-DOMINANT | 3 | Donut / pie / bar / line chart zabírá 50–60 % plochy. Visual storytelling přes data viz. |
| 4 | EDITORIAL / MAGAZINE | 3 | Large display typography, dramatic whitespace, NYT-level feel. |
| 5 | LIFESTYLE / EMOČNÍ | 3 | Domain-specific scéna dominantní (viz „Povinné domain-specific elementy" níže). |
| 6 | TIMELINE / JOURNEY | 2 | Vizualizace cesty (12 měsíců, ROI, before→after). |

Vizuální jazyk značky zůstává konzistentní napříč všemi 16 (paleta,
typografie, logo), ale **archetypy a kompozice se dramaticky liší**.

Každý mockup v gridu očísluj 1–16 (bílý malý kruh vlevo nahoře s číslem).

FORMAT
- Celkový obrázek: 3:4 vertikální (např. 1200×1600 px)
- Grid: 4 sloupce × 4 řádky
- Každý jednotlivý mockup v gridu: také 3:4 vertikální mini-mockup
- Spacing mezi mockupy: minimální, ale čitelný (1–2 % šířky)

OBSAH PER MOCKUP — VARIANTA: [VARIANTA]
[Per varianta plnění z mockup matrix výše — Skóre / Audit / Plán /
Kalkulačka / Strategie]

POVINNÉ DOMAIN-SPECIFIC EMOČNÍ ELEMENTY napříč gridem (per produkt):
[Konkrétní seznam scén / objektů, které model MUSÍ rozdělit napříč
16 layouty — viz tabulka „Per varianta — vizuální obsah" v mockup-recipes.md.
Příklady:
- Kalkulačka pro vodu: sklenice (6+ layoutů), plastové lahve (4+),
  domácí kuchyně (3+), filtrační systém (2+), krajina (2+), rodinné ruce (2+)
- Skóre pro wellness: domácí scéna spánku, šálek čaje, ranní rutina
- Audit pro B2B: brýle na PDF, tištěný report closeup, konzultační scéna
- Plán pro kurz: ranní rutina + planner, studentův workstation
- Strategie pro konzultaci: konferenční místnost, executive desk, whiteboard]

Žádný layout nesmí být pure UI bez emočního/domain anchoru.

Headline lead magnetu „[SCHVÁLENÝ NÁZEV Z KROK 2.6]":
- POUŽÍVEJ POUZE na EDITORIAL archetype layoutech (PDF / e-book /
  blueprint / workbook cover) — typicky 3 layouty ze 16
- NEPOUŽÍVEJ na HERO NUMBER, CHART, LIFESTYLE, SIDE-BY-SIDE, TIMELINE
  (bez cover frame), dashboard widgets — duplikuje H1 z landing page
- Pro variantu KALKULAČKA: ŽÁDNÝ layout neobsahuje headline (kalkulačka
  není dokument, výsledek mluví sám)

USP / mechanism keyword: „[USP keyword z Product DNA sekce 1]"

Cílová skupina: [krátký popis z Product DNA / Brand DNA]

REFERENCE STYLU
Aplikuj designový jazyk z přiložených souborů:
1. brand-kit/20-magnet-na-kontakty.png — primary vzor, jak má lead magnet
   v této značce vypadat (převezmi paletu, typografii, vrstvení, density)
2. brand-board.png — moodboard značky
3. brandDNA sekce 6 — Vizuální identita: [extrahovaná paleta HEX, fonty,
   styl, ikonografie]
4. Logo přesně z přiloženého souboru:
   - POUŽÍVEJ POUZE na EDITORIAL archetype layoutech (jako publisher
     branding na dokumentu) — typicky stejné 3 layouty co mají headline
   - NEPOUŽÍVEJ na ostatních archetypech (HERO NUMBER, CHART, LIFESTYLE,
     SIDE-BY-SIDE, TIMELINE, dashboard widgets) — kazí emoční pull,
     působí jako product placement
   - Pro variantu KALKULAČKA: ŽÁDNÝ layout neobsahuje logo
   - Žádné vlastní logo/wordmark generování

PRÉMIOVÁ KVALITA — POŽADAVKY (HYBRID: editorial + lifestyle estetika)

Každý mockup musí vypadat jako **landing page hero**, ne jako embedded
widget. Inspirace estetikou:
- Editorial magazine landing pages (Wall Street Journal, Bloomberg, NYT)
- Premium SaaS hero sections (Stripe, Linear, Notion, Superhuman)
- Premium D2C product pages (Allbirds, Casper, Glossier, Aesop)
- High-end finance app dashboards (Mercury, Brex hero shots)

NE estetika:
- GHL / Wix / Squarespace template feel
- Generic dashboard UI components
- Excel/Sheets table preview
- Stock infographic templates
- Mini-card embedded look

Konkrétní pravidla:
- **Dramatic whitespace** — minimum 25–35 % plochy je prázdná
- **Jeden dominantní prvek** — 40–60 % plochy zabírá jeden hero element
  (číslo / chart / foto / dominantní typografie). Žádných 5–8 elementů
  stejné vizuální váhy.
- **Magazine typografická hierarchie** — výrazný display font pro headline
  / hero number, menší pro supporting copy. Letter-spacing, kerning,
  font weight ladění.
- **Jemné stíny, vrstvení, hloubka** — výsledek působí trojrozměrně, ne flat
- **Žádný lorem ipsum** — všechny texty mají reálný obsah v češtině
- **Konzistentní paleta značky** napříč všemi 16 layouty
- **Logo přesně z přiloženého souboru**, nikdy nevytváříš nové
- **Veškerý text v ČEŠTINĚ**
- **Čísla čitelná a dávají SMYSL** pro variantu
- **Domain-specific anchor v každém layoutu** (viz POVINNÉ EMOČNÍ ELEMENTY
  výše) — žádný layout nesmí být pure UI bez context

ANTI-PATTERNS — CO NESMÍ BÝT V MOCKUPU
- ❌ Brand name v hlavičce mockupu (např. „Bioptron Test") — používáme
  USP / mechanism keyword. Brand patří na landing jako autorita pod fold.
- ❌ **CTA tlačítka v mockupu** („Spočítat úsporu", „Spustit kvíz", „Zobrazit
  výsledek", „Získat doporučení") — mockup zobrazuje JEN náhled výstupu
  lead magnetu (= dashboard / report / kalendář / blueprint / result).
  CTA tlačítko žije na landing page SAMOSTATNĚ vedle mockupu, ne uvnitř
  něho. Mockup s CTA = duplikát CTA na landing = vizuální noise, matoucí
  hierarchie. Pozn.: `brand-kit/20-magnet-na-kontakty.png` obsahuje
  CTA jako součást opt-in stránky — TO JE celý funnel preview, AIQ mockup
  je jen výřez (výstup, ne opt-in). NEPŘENÁŠEJ CTA z primary reference.
- ❌ 16 variací jedné archetype — minimum 5 distinct archetypes
- ❌ Mini-tabulka čísel jako dominantní prvek (vyjma archetypu Chart-dominant)
- ❌ Embedded-widget feel — každý layout designovaný jako landing hero
- ❌ Více než 6 elementů stejné vizuální váhy — chybí hierarchie
- ❌ Pure UI bez emočního / domain-specific anchoru
- ❌ Stock photo lidé v generic poses (corporate handshake, smiling
  woman with laptop, atd.)
- ❌ Korporátní wireframe vibe — chceme finální mockup, ne návrh
- ❌ Nečitelná čísla / nečitelný text
- ❌ Generický anglický UI text („Submit", „Click here", „Lorem ipsum")
- ❌ Builder UI template feel (Squarespace / Wix / GHL default)
- ❌ Identifikační číslo 1–16 v levém horním rohu finálního mockupu
  (to bylo jen pro grid labeling; ve full-size mockupu nemá být)
- ❌ **Headline lead magnetu na non-EDITORIAL archetypech** (HERO NUMBER,
  CHART, LIFESTYLE, SIDE-BY-SIDE, TIMELINE bez cover frame, dashboard
  widget) — duplikuje H1 z landing page. Headline patří JEN na
  EDITORIAL cover (PDF / e-book / blueprint / workbook). Pro variantu
  Kalkulačka: ŽÁDNÝ layout nemá headline.
- ❌ **Logo na non-EDITORIAL archetypech** — kazí emoční pull, působí
  jako product placement. Logo patří JEN na EDITORIAL cover (jako
  publisher branding na dokumentu). Pro variantu Kalkulačka: ŽÁDNÝ
  layout nemá logo.

OUTPUT
Uložit jako `/documents/brand/visuals/grid-aiq-[base_code]-[YYYYMMDD].png`
```

---

## Workflow generace (pro Krok 2.7)

### A. Primary path — nativní `image_generate` (GPT image 2)

```
1. Načti reference soubory podle hierarchie výše
2. Sestav prompt podle template + per-varianta plnění
3. Zavolej image_generate tool JEDINKRÁT:
   - prompt: [sestavený text — instruuje grid 4×4 v jednom obrázku]
   - reference_images: [list cest k brand assets]
   - format: 3:4 vertikál (1200×1600 px)
   - provider/model: GPT image 2 (nativní default)
   - output: /documents/brand/visuals/grid-aiq-[base_code]-[YYYYMMDD].png
4. Pokud uspěch → pokračuj na user selection
```

**🚫 KRITICKÉ — zákaz post-processingu gridu:**

- **1 image_generate volání = 1 PNG soubor (grid). Konec.**
- Model dostane prompt „vygeneruj grid 4×4 v jednom obrázku" a vrátí celý grid najednou.
- ❌ ŽÁDNÉ Python PIL compositing 16 samostatných obrázků do gridu (= 16 image_generate volání + Python slepení)
- ❌ ŽÁDNÉ přidávání frame / hlavičky / wrapperu kolem výstupu
- ❌ ŽÁDNÉ overlay čísel po factu (čísla 1–16 v levém horním rohu musí být součástí promptu, ne post-processing)
- ❌ ŽÁDNÉ intermediate soubory typu `grid-raw.png`, `grid-with-numbers.png`, `grid-final.png` — jen jeden výstup `grid-aiq-[base_code]-[YYYYMMDD].png`
- ❌ ŽÁDNÉ Python `.py` scripty uložené do `/documents/`

### B. Fallback path — openrouter / FAL

Pokud nativní `image_generate` selže (provider nedostupný, network error, model error) → fallback hierarchie:

```
1. Pokus 1: openrouter API
   - endpoint: https://openrouter.ai/api/v1/chat/completions (modal: gpt-image-2 nebo dalle-3)
   - env: OPENROUTER_API_KEY
   - reference images: base64 encoded inline
   - format: 3:4 (1200×1600)

2. Pokus 2: FAL API
   - endpoint: https://fal.run/fal-ai/flux-pro nebo gpt-image-2
   - env: FAL_KEY
   - reference images: upload first, pak reference URL
   - format: 3:4

3. Pokud všechny selžou → flag v output [MOCKUP TBD — image gen nedostupný]
   pokračuj na Krok 3 bez mockupu
```

**Bezpečnost klíčů:** OPENROUTER_API_KEY a FAL_KEY se nikdy nesmí dostat do logu / promptu / agentní paměti. Vždy přes env var v scriptu.

### C. User selection

Po doručení gridu:

```
> „Tady je grid 16 mockup variant lead magnetu „[schválený název]".
>  Vyber 1 (nebo více), kterou chceš použít jako finální mockup na landing.
>  Můžeš taky napsat „regeneruj [s úpravou]" pokud žádný nesedí —
>  např. „regeneruj minimalističtější" nebo „regeneruj víc dashboard-like"."

STOP a čekej na user input.
```

### D. Finální render — full-size verze vybraného mockupu (NE re-generation)

Po user selection (např. „číslo 7"):

**Princip (stejný jako brand-image-generator workflow):** Vezmi vybraný mockup z gridu a vyrob ho v plné velikosti. **Zachovej VŠECHNY detaily** — typografii, čísla, kompozici, barvy, layout. Pouze zobraz ho ve full resolution. Nic nepřidávej, nic neměň.

```
1. Sestav prompt pro full-size render (popisuje rendering, ne kreativní variation):

   „Z přiloženého gridu vyber mockup č. [N] (pozice řádek=R, sloupec=C
   v gridu 4×4) a vyrob ho v plné velikosti 1200×1600 px (3:4 vertikál).

   ZACHOVEJ PŘESNĚ:
   - Stejnou typografii (velikost, font, váhu, letter-spacing)
   - Stejná čísla, popisy, texty 1:1 (texty obsahu mockupu)
   - Stejnou kompozici a layout
   - Stejné barvy z brand palety
   - Stejné ilustrace, ikony, fotografie, vrstvení

   🚫 ODSTRAŇ identifikační číslo 1–16 z levého horního rohu — to bylo
   jen pro identifikaci layoutu v gridu, ve finálním mockupu nemá být.
   (POZOR: NEJDE o čísla obsahu jako skóre, Kč, %, dny — ta zachovej.
   Jde o malý bílý kruh s číslem 1–16 v rohu, který byl součástí grid
   labelingu.)

   NIC JINÉHO NEPŘIDÁVEJ a NIC NEMĚŇ — toto NENÍ re-generation. Cíl je
   zobrazit přesně mockup č. [N] z gridu v plné velikosti, bez
   identifikačního labelu."

2. Zavolej image_generate JEDINKRÁT (GPT image 2):
   - prompt: [text výše s vyplněným N + R + C]
   - reference_images:
     • /documents/brand/visuals/grid-aiq-[base_code]-[YYYYMMDD].png  ← grid jako primary reference
     • + stejné brand assety jako pro grid (brand-board.png, logo, brandDNA-extrakt)
   - format: 3:4 vertikál (1200×1600 px)
   - provider/model: GPT image 2 (vždy primary, fallback níže)
   - output: /documents/lead-magnets/AIQ [Quiz title]/mockup.png

3. Propiš cestu do meta.json (vznikne v Krok 4):
   - mockup_path: "/documents/lead-magnets/AIQ [Quiz title]/mockup.png"
   - mockup_layout_number: 7
   - mockup_grid_source: "/documents/brand/visuals/grid-aiq-[base_code]-[YYYYMMDD].png"
   - mockup_status: "generated"
```

**🚫 KRITICKÉ — NE re-generation:**

- ❌ ŽÁDNÉ nové image_generate volání s textovým promptem typu „vygeneruj náhled výstupu pro Kalkulačku s headline X" — to by vyrobilo **jiný layout**, ne render gridového #N
- ❌ ŽÁDNÉ samostatné upscale tools (FAL clarity-upscaler, flux-upscale, Real-ESRGAN) — generujeme **vždy přes GPT image 2** s gridem jako referencí
- ❌ ŽÁDNÉ přidávání detailů, čísel, ilustrací nad rámec gridového #N — model dělá **render at full resolution**, ne kreativní variation
- ❌ ŽÁDNÉ Python crop + AI upscale pipeline — model dostane grid jako reference a vyrobí jeden mockup, žádné mezikroky

**VÝJIMKA — user explicit modifikace:**

Pokud user řekne *„vyber #7, ale udělej ho minimalističtější"* / *„#3 a změň barvu CTA na zelenou"* / *„#5 a přidej fotku produktu"* → pak ANO jde o **upravenou re-generation** s modifikovaným promptem. Bez explicit modifikace = full-size render s zachováním všech detailů.

**Fallback pro full-size render** (stále GPT image 2 jako model, mění se jen provider):

```
1. Pokus 1: openrouter API (model: gpt-image-2)
2. Pokus 2: FAL API (model: gpt-image-2)
3. Pokud všechny selžou → mockup_status: "tbd_render_failed",
   mockup_path: null, oznam uživateli a pokračuj na Krok 3 bez mockupu
```

### E. Regenerace gridu

Pokud uživatel řekne „regeneruj [úprava]":
- Skill modifikuje prompt podle úpravy (např. „minimalističtější" → přidá „prioritizuj whitespace, méně density")
- Zavolá image_generate znovu pro nový grid
- Žádný cap na regeneraci — klient platí svůj FAL/openrouter klíč, rozhoduje sám
- Před každou regenerací: krátká hláška „Generuju další grid (image_generate volání #N)"

---

## Soubory vytvářené v Krok 2.7 — MAXIMUM 2 per kvíz

**Jen tyto dva soubory existují po dokončení Krok 2.7:**

```
1. /documents/brand/visuals/grid-aiq-[base_code]-[YYYYMMDD].png
   = výstup z 1 image_generate volání (grid 4×4, 16 mockupů v jednom obrázku)

2. /documents/lead-magnets/AIQ [Quiz title]/mockup.png
   = vybraný layout po full-size renderu (1 image_generate volání s gridem
     jako referencí, žádná re-generation)
```

**🚫 ŽÁDNÉ DALŠÍ soubory:**

- ❌ Intermediate `grid-raw.png` / `grid-with-numbers.png` / `grid-final.png`
- ❌ Samostatné `mockup-1.png` ... `mockup-16.png` (= 16 image_generate volání + Python compositing)
- ❌ `mockup-upscaled.png` / `mockup-final.png` / `mockup-cropped.png` (= upscale pipeline ne)
- ❌ Python scripty `.py` uložené do `/documents/`
- ❌ Debug anotace `.json` / `.txt` vedle PNG souborů
- ❌ Kopie originálu (např. `aiq-[base_code]-[YYYYMMDD].png` ve `/documents/brand/visuals/`) — finální mockup žije jen v `/documents/lead-magnets/AIQ [Quiz title]/mockup.png`

Pokud agent potřebuje intermediate state (crop coordinates, pozice #N, identifikátory), drž ho v conversation memory, ne na disku.

**Verzování při přegenerování:** Pokud uživatel později chce přegenerovat mockup pro stávající kvíz, viz „Verzování mockupů" níže.

---

## Verzování mockupů per kvíz

Pokud uživatel později chce přegenerovat mockup pro stávající kvíz:

```
/documents/lead-magnets/AIQ [Quiz title]/
├── mockup.png         ← aktuální verze (overwrite při regeneraci)
├── mockup.v1.png      ← předchozí verze (auto-archived při overwrite)
├── mockup.v2.png      ← další předchozí
└── ...
```

Před overwrite `mockup.png` → přesuň starý na `mockup.v[N].png` (kde N je další volný index).

---

## Propsání do output dokumentů

### 1. `01-strategie.md` — sekce 4.5 (Vizuál lead magnetu)

Nová subsekce v rámci sekce 4 (Landing page):

```markdown
### 4.5 Vizuál lead magnetu (mockup)

**Soubor:** `/documents/lead-magnets/AIQ [Quiz title]/mockup.png`

**Umístění na landing page:** nad fold, vedle hooku a podnadpisu
(desktop: split layout text 50–60 % / mockup 40–50 %; mobile: full-width
pod hookem).

**Cíl:** Vizualizovat, co návštěvník po vyplnění kvízu dostane —
primární CR booster (+20–50 % konverze vs. text-only varianta).

**Brand konzistence:** Mockup byl generován s referencemi
brand-kit/20-magnet-na-kontakty.png + brand-board.png + brandDNA.md,
takže respektuje vizuální identitu značky.

**Pokud klient chce přegenerovat:** stačí znovu spustit AIQ skill
v režimu „regeneruj mockup pro AIQ [Quiz title]". Stará verze se zazálohuje
jako `mockup.v[N].png` ve stejném folderu.
```

### 2. `02-pokyny-landing-kviz.md` — KROK 1 (Landing page)

V KROK 1 instrukce pro AI agenta:

```markdown
### HERO sekce — povinné prvky

- **Hook:** „[hook text]"
- **Podnadpis:** „[podnadpis text]"
- **Vizuál (POVINNÝ):** `/documents/lead-magnets/AIQ [Quiz title]/mockup.png`
  - Umístění: nad fold, vedle textu (desktop split layout, mobile pod textem)
  - Velikost: 40–50 % šířky landing na desktop, full-width na mobile
  - Žádný další ořez ani styling — mockup byl generován v 3:4 a má
    brand-konzistentní design
- **CTA tlačítko:** „Spustit dotazník — [X] minut, zdarma"
```

---

## Anti-AI-slop checklist (před prezentací gridu uživateli)

Před tím, než agent prezentuje grid uživateli, projde mockup tímto check listem. Pokud cokoli selhává → regeneruj automaticky se silnějším anti-pattern instrukcemi v promptu.

**Obsah & brand:**
- [ ] Žádný lorem ipsum text — všechny texty jsou v češtině s reálným obsahem
- [ ] Headline lead magnetu odpovídá schválenému názvu z Krok 2.6
- [ ] Brand name (např. „Bioptron", „Aqueena Pro") NENÍ v mockupu hlavičce
- [ ] USP / mechanism keyword JE v mockupu (pokud existuje v Product DNA)
- [ ] Čísla v mockupu (skóre, Kč, dny) jsou čitelná a dávají smysl pro variantu
- [ ] Logo přesně odpovídá přiloženému souboru (žádné AI variace)
- [ ] Brand paleta je konzistentně použita ve všech 16 layoutech

**Archetype variety (hybrid estetika):**
- [ ] Grid obsahuje **minimálně 5 distinct archetypes** (HERO NUMBER / SIDE-BY-SIDE / CHART-DOMINANT / EDITORIAL / LIFESTYLE / TIMELINE)
- [ ] Žádný archetype se neopakuje 5+ krát v gridu
- [ ] Distribuce odpovídá: HERO 2 · SIDE-BY-SIDE 3 · CHART 3 · EDITORIAL 3 · LIFESTYLE 3 · TIMELINE 2 (tolerance ±1 per archetype)

**Premium hero quality:**
- [ ] Každý layout vypadá jako landing page hero (NE embedded widget)
- [ ] Dramatic whitespace — 25–35 % plochy prázdné v každém layoutu
- [ ] Jeden dominantní prvek 40–60 % plochy (číslo / chart / foto / typografie)
- [ ] Magazine typografická hierarchie — výrazný display font pro headline
- [ ] Jemné stíny, vrstvení, hloubka — působí trojrozměrně, ne flat
- [ ] Žádných 5+ elementů stejné vizuální váhy — jasná hierarchie

**Domain-specific emoční anchor:**
- [ ] Každý layout obsahuje minimálně 1 domain-specific element (sklenice / lahve / kuchyně / produktová scéna / lifestyle scéna podle varianty)
- [ ] Žádný pure UI layout bez context (mimo archetype CHART-DOMINANT, kde je hero data viz)
- [ ] Domain elementy systematicky distribuované napříč gridem (ne jen v 2-3 layouts)

**Anti-pattern:**
- [ ] **Žádné CTA tlačítka v mockupu** („Spočítat úsporu", „Zobrazit výsledek", „Spustit kvíz", „Získat doporučení") — mockup = náhled výstupu LM, ne demo landing. CTA žije na landing page samostatně.
- [ ] Žádné identifikační číslo 1–16 v rohu finálního (full-size) mockupu
- [ ] **Headline lead magnetu JEN na EDITORIAL cover layouts** (PDF / e-book / blueprint / workbook) — NIKDY na HERO NUMBER / CHART / LIFESTYLE / SIDE-BY-SIDE / TIMELINE / dashboard widgets
- [ ] **Logo JEN na EDITORIAL cover layouts** — NIKDY na HERO NUMBER / CHART / LIFESTYLE / SIDE-BY-SIDE / TIMELINE / dashboard widgets
- [ ] Pro variantu **Kalkulačka**: ŽÁDNÝ layout nemá headline ani logo (kalkulačka = výsledek, ne dokument)
- [ ] Žádný „korporátní wireframe" feel
- [ ] Žádné stock photo lidé v generic poses (handshake, smiling laptop woman)
- [ ] Žádný builder template feel (Squarespace / Wix / GHL default)
- [ ] Žádné mini-tabulky čísel jako dominantní prvek (vyjma CHART-DOMINANT)

Pokud auto-regenerace 2× za sebou nesplní checklist → STOP, oznámit uživateli a požádat o explicit feedback („Co konkrétně mám změnit?").

---

## Reference na další dokumenty

- `framework.md` — pravidla pro tvorbu názvu lead magnetu (Krok 2.6), USP keyword, brand vs. mechanism
- `dynamic-lead-magnet-types.md` — popis 5 variant lead magnetu (Skóre / Audit / Plán / Kalkulačka / Strategie)
- `output-template.md` — template `01-strategie.md` se sekcí 4.5 Vizuál lead magnetu
- `quiz-implementation.md` — `02-pokyny-landing-kviz.md` template s povinným mockupem v HERO sekci
- `brand-context-loader.md` — 3-way načítání brand kontextu (Product DNA / URL / manuál)

Souvisejíci cs-skills:
- `brand-image-generator` — pro generic brand vizuály (hero, social, abstrakt)
- `brand-kit-generator` — generuje 24 brand mockupů včetně `20-magnet-na-kontakty.png` (primary reference pro AIQ Krok 2.7)
