# Prodejní stránka 3.0 — 21bl anatomie (ConversionWise × $100M, dvojverze)

Personalizovaná prodejní stránka `/online/[contactId]` NENÍ cold-traffic skelet. Návštěvník právě vyplnil kvíz a dostal magnet, je **solution-aware** (Schwartz). Stránka nebuduje znovu problem-awareness, **pokračuje v konverzaci z kvízu**. Nejsilnější páky: jeho vlastní odpovědi (self-persuasion přes commitment & consistency), výsledek jako **diagnóza → předpis** (Levesque ASK: předepiš, neprodávej), nabídka síly $100M (Hormozi), routing CTA dle rozpočtového signálu.

Personalizace je **náš edge** proti šablonám jako ConversionWise (osobní data nemají). Stránka **prodává okem**: každý blok má vizuální dominantu a úderný headline, ne zeď textu.

**Route:** `/online/[contactId]` (dřív `/r/`). Fallback bez ID = `/doporuceni`.

## Vrstvení (template ⅔ + proměnné ⅓, žádný uložený HTML blob)
- **L1** — statická copy ze specu (nabídka, mechanismus, garance, FAQ). Definuje strategy skill z Product DNA.
- **L2** — segmentové varianty (headline/proof per segment), runtime výběr dle segmentu leada.
- **L3** — ✨ persona pole, generují se runtime per kontakt z odpovědí kvízu.

## 21 bloků

`✨` = personalizace (L3, fallback bez ID na univerzál) · **jádro** = renderuje se vždy (i bez Product DNA/100M) · **obohacené** = z obohacené (100M) Product DNA, bez ní se skryje/zjednoduší · **podmíněný** = potřebuje obrázky / reference / data o konkurenci.

| # | Blok | Person. | Vrstva | Zdroj dat | Fallback bez dat |
|---|---|---|---|---|---|
| 1 | **Hero** — hlavní ŽIVOTNÍ TRANSFORMACE jako benefit (#1 cíl leada) + 3 heslové benefity + social proof (počet recenzí, ★) + CTA nad foldem | ✨✨✨ | jádro | L3 `main_headline`,`sub_headline`,`benefit_*` · Product DNA #1 | univ. příslib + 3 obecné benefity; proof vypínatelný (bez recenzí power číslo). **Copy pravidla: viz „Copy per sekci" níže** |
| 2 | **Autoritní pás** — 3 power čísla | — | obohacené | Brand DNA · Product DNA #13 | Company DNA off → jen Brand DNA; chybí → skrýt |
| 3 | **Zrcadlo „řekli jste" + diagnóza + předpis** (+ mini-CTA) | ✨ | jádro | L3 `problem_*` · Product DNA #2/#3 | bez ID → problémová matice (L1) |
| 4 | **Social proof #2** — nejsilnější reference | — | podmíněný | L2 reference | bez referencí → skrýt |
| 5 | **Produkt + unikátní mechanismus** | výběr dle bolesti | obohacené | Product DNA #1/#3 · L1 `mechanisms.by_pain` | mělký → jen představení produktu |
| 6 | **Jak to funguje — 3 kroky** | — | jádro | Product DNA #4/#5 | vždy (generické 3 kroky) |
| 7 | **Váš den — předtím/potom** | ✨ | jádro | L3 · Product DNA #1 | bez ID → obecný den |
| 8 | **Komponenty (alternující PAS bloky)** | — | jádro | Product DNA #4/#5 | base benefity vždy |
| 9 | **Bonusy** | — | obohacené | Product DNA #8 | slabé/žádné → auto-hide |
| 10 | **Product carousel** | — | podmíněný | product-image-generator | bez obrázků → skrýt |
| 11 | **Value stack #1 + garance** (sticky CTA on) | — | obohacené | L1 `offer` · Product DNA #5/#6/#7 | **min-viable stack: dodávka + cena + garance + CTA (vždy renderuje)** |
| 12 | **Proof / tvrdá čísla** | — | obohacené | Product DNA #13/#11 · Brand DNA | jen doložená; nic → skrýt |
| 13 | **Case study** — match segmentu | ✨/segment | podmíněný | L2/L3 · Product DNA #11 | generická nebo skrýt |
| 14 | **Pro koho / pro koho NE** — potvrzení segmentu | ✨ | obohacené | Product DNA #2 · L3 | prázdné → skrýt |
| 15 | **Srovnávací tabulka** — „stará vs. nová cesta" | — | podmíněný | Product DNA #3/#10 | bez dat → skrýt |
| 16 | **Stroj času 1/6/12** | ✨ | jádro | L3 · Product DNA #1 | bez ID → obecné milníky |
| 17 | **Genesis / příběh** | — | obohacené | Product DNA #12 · Brand DNA #3 | chybí → vypnout |
| 18 | **Osobní vzkaz + urgence** | ✨ | obohacené | L3 · Product DNA #9 | bez reálné urgence → měkký close (žádný fake countdown) |
| 19 | **Value stack #2** — rekapitulace | — | obohacené | L1 `offer` | tenká → rekap pattern, ne kopie #11 |
| 20 | **Garance — aha moment** | — | obohacené | Product DNA #7 | chybí → 1 základní garance (viz #11) |
| 21 | **FAQ / námitky** — řazené dle segmentu | ✨ | jádro | L3 `objection_*` · Product DNA #10 | bez ID → obecné FAQ (L1) |

Globální: sticky mini-CTA (od hero, nese cenu) · promo lišta · ✨ ribbon jen v personalizované verzi · 3 tóny pozadí (tmavý jen 2×: autoritní pás + Value stack #1).

## 🎨 VIZUÁLNÍ HUSTOTA + OBRÁZKY (POVINNÁ pravidla — jinak stránka vypadá basic)

Prodejka NESMÍ být zeď textu. Tvrdá pravidla:

1. **Max 2 textové sekce za sebou, pak VŽDY vizuální blok** (foto / graf / ikonová mřížka / carousel / před-po / tabulka). Nikdy 3+ textové bloky po sobě.
2. **Každá sekce má vizuální kotvu** — ikona, foto, graf nebo mřížka. Žádný holý text na ploché barvě.
3. **Ikony všude** (Lucide/SVG): u benefitů, komponent nabídky, bonusů, 3 kroků, proof čísel, „pro koho". Každý list-item / karta má ikonu.
4. **Obrázky NIKDY nerecyklovat z landing stránky.** Prodejka = VLASTNÍ nové obrázky:
   - **Nový hero background** (generovaný, ne landing hero.jpg).
   - **Produktový carousel** = artefakt produktové složky `/documents/brand/products/<slug>/carousel/` (výstup `product-image-generator`). **Generuj ho jen když tam ještě není a VŽDY PŘED stavbou LP** — LP ho jen spotřebuje (zkopíruje `carousel/*.jpg` → funnel `public/img/`). **Carousel snímek 01 → hero.** Detail: `aiq-funnel-builder/references/IMAGES.md`.
   - **Bonusy a komponenty nabídky = s vlastními fotkami/vizuály**, ne jen text.
   - Landing a prodejka sdílí design SYSTÉM (tokeny, fonty, komponenty), NE konkrétní obrázky.
5. **Bonusy** (#9) a **Komponenty nabídky / value stack** (#8, #11) MUSÍ mít vizuál u každé položky (foto bonusu + ikona), ne odrážkový seznam.
6. **Renderuj CELÝ wireframe (21 bloků)** — nevynechávej. Když jsou podklady (Product DNA + obrázky), stránka musí odpovídat wireframu, ne být poloviční. Chybějící blok = jen když fakt nejsou data (fallback), ne z lenosti.
7. **Sada obrázků ke KAŽDÉ prodejce (POVINNÉ, generovat na pozadí):**
   - **Min. 5, ideálně 6–7 silných lifestyle obrázků** přes `brand-image-generator` — produkt/služba + **vysněný výsledek** (např. spokojený zákazník s dosaženým výsledkem). **Formát 4:3**, vizuálně navzájem rozdílné, **vizuální důraz na STŘED** (aby šly použít i jako pozadí sekcí na desktopu i mobilu). Silné brandové obrázky, věrné Brand/Product DNA. Lifestyle sada je **per‑stránka**, hostuje se rovnou do funnel `public/img/`.
   - **Produktový carousel (6, nesou texty, snímek 01 → hero)** — NENÍ per‑stránka: je to **artefakt produktové složky** `/documents/brand/products/<slug>/carousel/`. **Generuj ho přes `product-image-generator` jen když tam ještě není a VŽDY PŘED stavbou LP.** LP ho jen spotřebuje.
   - Tyto obrázky pak **různě používej po stránce** jako silné vizuály (hero pozadí, pozadí sekcí, přechody mezi textovými bloky). Nikdy nerecyklovat z landingu.
   - Engine = **VŽDY nativní tool `image_generate`** (GPT image 2, OpenClaw), reference produktu přes parametr `images[]` (runtime cesty). NIKDY Freepik/Magnific. Kompletní pořadí + pipeline: `aiq-funnel-builder/references/IMAGES.md`.

## 🎠 Produktový carousel + hero z carouselu 3× na stránce
- **Carousel snímek `01` (hero) NENÍ v carousel pruhu** — je to nejsilnější produktový vizuál, tak ho na stránce **zopakuj 3×**: (a) **představení produktu** (sekce hned po prvním social proofu), (b) **value stack #1** (nabídka), (c) **value stack #2** (shrnutí). Ve stacku tedy hero **2×**.
- **Carousel pruh (blok 10) = snímky `02`–`06` (5 karet)**, klasický interaktivní carousel na **PLNOU ŠÍŘKU stránky** (od kraje ke kraji, full-bleed 100vw — jediné full-width místo na stránce, záměrně naruší flow). Klientská komponenta `SalesCarousel`:
  - **Velké karty = JEN obrázky, ŽÁDNÝ render text** (carousel snímky si nesou text samy — jsou to hotové produktové karty). **Ber je PŘÍMO z produktové složky `carousel/`** (`01-hero`…`06-lifestyle`), ne přegenerovávej. Nedávej pod karty popisky.
  - **Karty 1:1 (čtverec)** dle produktových carousel snímků — zobraz **CELÉ, neořezávej** (jinak se ořízne baked-in nadpis/nabídka). `sp-car__card img { aspect-ratio: 1/1 }`.
  - **Šipky po BOCÍCH v gutterech — SAMOSTATNĚ, NE přes obrázky** (v ~100px prostoru vlevo/vpravo, ne překryté přes karty) + **tečky = počet karet** (aktivní zlatě).
  - **Jede dokola** (autoplay + seamless loop přes zdvojený track).
  - **Klik na kartu → zvětšení do POPUP (lightbox)** — karty nesou detailní text, po kliknutí se obrázek otevře velký (tmavý blur overlay, × / Esc / klik mimo zavře, autoplay se pauzne).
  - **Přesně 3 velké karty na desktopu (bez peeku), NE až do kraje** — ~100px gutter vlevo i vpravo (`viewport padding`), v němž sedí šipky / 1 a kus na mobilu (CSS `--card`).
- **Silný velký nadpis** (benefit-led, `bento-title`) — ne slabé „Od problému k řešení".

## 💬 Social proof — vždy velký výrazný citát + zvýrazněná klíčová fráze
Reference (blok 4) a case study (blok 13) běží jako **produktový foto-band** s **velkým, tučným, výrazným citátem** (ne drobný text) a **VŽDY zvýrazni nejklíčovější frázi** citátu (zlatě + tučně). Spec pole `testimonial.highlight` / `case_study.highlight` = přesná podfráze citátu; když chybí, render zvýrazní první větu (obvykle pointa). Cíl: oko chytne pointu i při pouhém skenování stránky.

## 🛟 Robustní fallback (klient bez Product DNA + bez 100M nabídky) — POVINNÉ
Cíl: i s minimem dat vznikne **funkční slušná stránka**, ne rozbitá.
- **Vždy renderuj bloky „jádro":** hero (1), zrcadlo/diagnóza (3), 3 kroky (6), váš den (7), benefity (8), **min-viable Value stack (11)**, stroj času (16), FAQ (21).
- **Bloky „obohacené" renderuj jen když mají data** (autoritní pás, mechanismus hloubka, bonusy, proof čísla, genesis, urgence, stack #2, garance aha) — jinak se **skryjí bez díry v toku**.
- **Bloky „podmíněný"** (social proof, carousel, case study, tabulka) se skryjí bez referencí/obrázků/konkurence.
- **Value stack #1 minimální varianta** (bez 100M dat): dodávka + cena + 1 garance + CTA. Nikdy prázdný ani nevyrenderovaný.
- **Nikdy nerenderuj `[OVĚŘ S KLIENTEM]`** placeholdery na živo.
- Detekce úrovně: builder spočítá, kolik offer-polí Product DNA je vyplněných; slabá DNA → jen jádro. Onboarding proaktivně nabídne `100m-offer-generator` (obohacení = default, ne výjimka).

## Fallback `/doporuceni` — bez ID (POVINNÁ routa, beze změny 2.0)
Generická plnohodnotná stránka na neutrální URL (nesmí znít prodejně). Sekce z L1/L2 (univerzální fallbacky dle tabulky výše). Servíruje se pro: `/online/` bez ID · neplatné/smazané contactId · persona pole ještě nejsou · **přeposlaný odkaz** · organický/přímý provoz. Konverzní tah: blok „Udělejte si audit na míru (5 minut)" → kvíz. Fallback = vstup do funnelu, ne mrtvý konec.

## Délka stránky — VŽDY PLNÁ (žádné schovávání sekcí podle stavu leadu)
**🚫 NESCHOVÁVEJ sekce podle `lead_temperature`.** Stránka renderuje **vždy všechny sekce** (plný wireframe) — bez ohledu na hot/warm/cold. Sekce se skryjí JEN když k nim reálně chybí data (fallback dle tabulky nahoře), nikdy ne kvůli teplotě leadu.
- Teplota leadu smí ladit **jen TÓN copy** (např. měkčí close u cold), **NE skrývat celé sekce**.
- V renderu drž `show.*` = vždy `true` (žádné `temperature === "warm"` gaty na sekce).

## Bezpečnost a soukromí (K5 — závazné)
- `/online/` a `/magnet/` jsou neautentizované, potenciálně zdravotně zabarvené → **jen křestní jméno + výsledek/doporučení**, nikdy příjmení/e-mail/telefon.
- `noindex` + `X-Robots-Tag` na personalizovaných routách.
- Zdravotní formulace zobecnit („zátěž prostředí", ne diagnózy). Žádné léčebné sliby.
- Render `/online/` zapisuje tag `aiq-videl-nabidku` (signál pro follow-up).
- **Ochrana URL (rozhodnuto):** `contactId` funguje jako **capability klíč** (neuhodnutelné ID), bez podepsaného tokenu. `/online/[contactId]` s neplatným/chybějícím ID → fallback obsah (`/doporuceni` inline). Žádné `?t=` HMAC.

## Co definuje strategy skill (spec pole, STOP schválení)
L1/L2 statická copy do funnel-specu, per blok: `hero_*` (fallback), `offer` (komponenty, bonusy, cena, garance, price_note), `mechanisms.by_pain/.default`, `segments[].headline/proof/case`, `proof_numbers`, `comparison`, `faq[]` (univerzální), `cta_routes`, `urgency` (jen reálná), osnova `/doporuceni`. Napojení na obohacenou Product DNA #5/#7/#8/#9/#11/#12/#13.

L3 ✨ persona pole (hero promise, zrcadlo, den, case match, pro koho, stroj času, osobní vzkaz, FAQ pořadí) se generují runtime per kontakt; strategy definuje jen jejich prompt kontext (offer whitelist, segmenty, lint pravidla).

## 📝 Copy per sekci — 100M frameworky (prompt kánon)

Sales copy vzniká ve dvou vrstvách: **L1/L2 statická** (strategy píše do funnel-specu `sales.*` z Product DNA) a **L3 persona** (runtime prompt `aiq-funnel-builder/template/lib/personalize.ts` — pole `main_headline`, `sub_headline`, `problem*`, `benefit_*`, `objection_*`). Tato sekce = **kánon copy pravidel per blok**, čerpá z 100M wireframe frameworků, laděno na reálné klientské stránce (2026-07). Slouží k review sekci po sekci a jako zdroj znění pro FIELD_GUIDE v personalize.ts.

**Globální hlas (VŠECHNA pole):** vřele a lidsky, jako bys situaci vysvětloval blízkému člověku u kávy (ne korporátní leták), empaticky, spisovně, **VYKÁNÍ**. Krátké věty (max ~15 slov), aktivní tvary. Konkrétní čísla JEN z Product DNA / odpovědí klienta (nic vymyšleného). Zdravotní guardrail (žádné léčebné sliby, žádné diagnózy). Bez dlouhé pomlčky „—" jako oddělovače (AI tell) a bez zakázaných klišé.

**Kapitalizace vykání (závazné, celá stránka jednotně):** oslovení klienta **vždy s velkým písmenem** — Vy, Vám, Vás, Vaše, Váš, Vámi — ve **VŠECH** polích **L1 i L3** (jinak se na jedné stránce potkají obě formy = viditelná nekonzistence). Platí i pro hardcoded fallback stringy v renderu.

**Lint / kontrola klišé:** automatický lint v `personalize.ts` běží **jen na L3 runtime pole**. **L1 copy** (`components`, `genesis`, `guarantee_*`, `stack_items`, `price.note`…) žádnou automatickou kontrolou neprochází → při STOP review projeď ručně tentýž checklist: **klišé** (princip + typické příklady viz `copy-recipes.md` §„AI klišé"), **dlouhá pomlčka**, **vata/tautologie**, **strašení**.

### Blok 1 — HERO
Cíl bloku: v jedné vteřině dát návštěvníkovi **jeho vysněný koncový stav** + 3 heslové důvody + CTA. Solution-aware lead (po kvízu) — neotvírej znovu problém, pojmenuj CÍL.

- **`main_headline` (H1 · ✨ L3):** POUZE hlavní **TRANSFORMACE v životě klienta jako BENEFIT** (vysněný pozitivní koncový stav). ⚠️ ZÁKAZ: formule „jak…bez…", mechanismus, produkt, frustrace/negace. Jedna čistá, emočně silná věta o tom NEJVĚTŠÍM, co se klientovi v životě změní k lepšímu — z jeho odpovědí a cílů. Renderuje se ZA oslovením jménem („Pavle, …") → **začni malým písmenem, pokračování věty.** Max 9 slov. Bez čísel/Kč. *Vzor (STRUKTURA, obsah z Product DNA): „[vysněný koncový stav] pro celou rodinu, každý den".* **Typografická hravost (POVINNÉ):** označ **jedno** klíčové slovo/2 slova titulku obalením do `**…**` (např. „čistá **voda** pro celou rodinu") — render to přeloží na `<em class="sp-hl">` (zvýrazní barvou/vahou). Bez zvýraznění je titulek uniformní blok = AI tell. Zvýrazni podstatu transformace, ne sloveso.
- **`sub_headline` (podnadpis · ✨ L3):** 1–2 krátké věty. Rozvine titulek + přidá dvě věci: (a) čím je řešení JINÉ než co klient dosud zkoušel (jeho alternativy z odpovědí), (b) klidný výsledek, který z toho má. Sebevědomě — **zákaz vágního „můžete mít / mohli byste"**, piš „máte / získáte / přestanete řešit". Bez produktu, bez Kč. *Vzor (STRUKTURA): „Místo [dosavadní alternativy] máte [řešení] rovnou [kde]. Získáte [klidný výsledek] a méně starostí kolem [jeho problému]."*
- **Hero bullets = `benefit_*` (3 · ✨ L3):** každý = **TRANSFORMACE** „co budete mít / umět / dělat, co dnes nejde", z jeho situace. Titulek (max 6 slov) = **výsledek, ne vlastnost** („Klid u rodinného stolu", ne „[technická vlastnost produktu]"). Popis = 1 úderná věta, bez technických čísel.
- **CTA:** dle rozpočtového routingu (`cta_routes`), nad foldem. **Social proof:** ★ + počet recenzí — `sales.social_proof.rating` MUSÍ být **číslo** (`5`), ne string (`"5,0"` → `Math.round` = NaN → prázdné hvězdičky).

### Blok 8 — Komponenty nabídky (alternující PAS bloky)
Cíl bloku: každou klíčovou součást řešení proměnit v **důvod ke koupi**, ne ve výčet vlastností. **`components[]` (8b) renderuj VŽDY jako alternující PAS bloky** (velká čtvercová foto střídavě L/R, text vedle), editoriálně, **nikdy jako mřížku ikonek**. Pozn.: nad tím běží samostatná bento sekce **benefitů (8, z L3 `benefit_*`)** — tu PAS bloky nenahrazují, jsou to dvě různé sekce. Vizuálně nejsilnější část nabídky.

- **`components_title` (L1):** krátký silný nadpis sekce napojený na emoční příslib funnelu (kicker „Co je uvnitř" řeší render zvlášť). *Vzor: „Z čeho se skládá Vaše jistota".*
- **`components[]` (3–6 · L1):** každá komponenta = jeden PAS blok, pole:
  - **`label`** (kicker, max 3 slova): název součásti/funkce do zlaté pilulky s ikonou (*„Pětistupňová filtrace"*).
  - **`title`** (silný nadpis, max 8 slov): **benefit/pointa, ne vlastnost** (*„Zachytí i to, co ve vodě neuvidíte"*, ne „5stupňová osmóza").
  - **`sub`** (podnadpis, 1 věta): konkrétní parametr/vlastnost, který nadpis podpírá.
  - **`desc`** (PAS text, 3–4 věty, **JEDEN odstavec** bez prázdných řádků — render nedělí): **P**roblém (co bez toho klient řeší) → **A**gitace (rozjitření: proč to bolí, tichá vada) → **S**oluce (jak to komponenta vyřeší + výsledek). Bez žargonu, čísla jen z Product DNA. **Agitaci piš věcně, bez strašení** (tón K5): pojmenuj reálný důsledek, žádné katastrofické scénáře — zvlášť u zdravotně zabarvených produktů.
  - **Anti-monotonie:** PAS je vnitřní kostra, **ne viditelná šablona**. Každá komponenta míří na JINOU bolest a má jiný nájezd první věty (otázka / scéna / fakt / číslo) — 6 stejně tvarovaných odstavců za sebou = přesný opak editoriálního rytmu.
  - **`icon`** (Lucide název) + **`img`** (`/img/…` foto komponenty). Render alternuje L/R sám podle pořadí.

### Blok 17 — Genesis / příběh
Cíl bloku: dát značce **lidský původ** (proč to vůbec děláme). Emoce, ne firemní CV. Editoriál: origin-story foto vedle textu.

- **`genesis.title` (L1):** o čem příběh je, ne slogan. ⚠️ Render dodává natvrdo kicker „Proč to děláme" NAD titulek → **titulek NEZAČÍNEJ slovem „Proč"** (dvě „proč" nad sebou). *Vzory: „Nezačali jsme u [produktu], ale u [hodnoty]", „[Značka] vznikla kvůli jediné věci".*
- **`genesis.body` (2–3 odstavce oddělené `\n\n`, max ~3 věty na odstavec · L1):** origin story s **emočním obloukem**: (1) přesvědčení/původ, z čeho značka vyrostla → (2) vhled, znepokojivé pozorování, které vedlo k produktu → (3) poslání, proč to děláme pro klienta (emoční vrchol). 1. os. mn. č. („my"), vykání ke klientovi. Konkrétní, ne patos. Render rozseká na `<p>`, první odstavec = lead. Zdravotní guardrail.
- **`genesis.image` (`/img/…` · L1):** lifestyle / značkové / produkt v kontextu, vedle textu (2-sloupec).

### Blok 20 — Garance / aha moment
Cíl bloku: sundat riziko z klienta. **Reframe = kdo riziko nese**, ne výčet podmínek.

- **`guarantee_aha_lead` (1–2 věty · L1):** **aha-reframe** nad odrážkami — přenes veškeré riziko na dodavatele (*„Veškerou odpovědnost za funkčnost, servis i instalaci nese [dodavatel], ne Vy. Rozhodujete se v klidu, bez obav, že na něco doplatíte."*). Render zvýrazní. ⚠️ Render má nad tím natvrdo H2 „Nenesete žádné riziko" + pečeť „Bez rizika" → **v leadu neopakuj slova „riziko / bez rizika"**, řekni KDO odpovědnost nese a co to pro klienta znamená. Renderuje se **jen společně s `guarantee_aha[]`** (samotný lead se nezobrazí).
- **`guarantee_aha[]` (2–4 odrážky · L1):** co konkrétně garance/servis kryje (záruka, instalace, certifikace) — jen reálné z Product DNA #7.

### Blok 11 — Value stack + garance (money copy, nejdůležitější)
Cíl bloku: shrnout VŠECHNO, co klient dostane, jako neodolatelný balík a ukotvit hodnotu proti ceně. Renderuje se vždy (min-viable varianta i bez 100M dat).

- **`stack_items[]` (L1):** co klient reálně získá. Každá položka = **výsledková formulace, ne inventura** (*„Čistá voda z kohoutku, kdykoli"*, ne „Filtrační jednotka 1 ks"). Konkrétní, hmatatelné, vykání.
- **`price {orig, now, save, note}` (L1):** `note` = **ukotvení hodnoty / cena v perspektivě** (denní výdaj, srovnání s dosavadní alternativou klienta), ne prázdná fráze. Čísla/ceny JEN z `offer` whitelistu.
- **Min-viable (bez 100M dat):** dodávka + cena + 1 garance + CTA. Nikdy prázdný ani nevyrenderovaný.

### Blok 18 — Osobní vzkaz + urgence
Cíl bloku: lidský most před posledním CTA + kredibilní důvod jednat teď.

- **Osobní vzkaz (L1/L3):** od autora/značky, 1. osoba, lidsky, proč tohle klientovi upřímně přeje. Bez prodejního tlaku.
- **`urgency` (L1):** JEN reálná (omezená kapacita instalace, sezónní dostupnost z Product DNA #9). Kredibilní důvod, **bez vymyšleného countdownu a bez strašení**.

*(Kánon znění zatím CHYBÍ pro bloky 3, 5, 6, 7, 9, 14, 15 (srovnání), 16 (stroj času / milníky), 19, 21 — render existuje, doplnit při dalším review. Pozn.: „vize budoucnosti" ani samostatný „recenze pás" na prodejce NEjsou — recenze žijí na landing/magnetu.)*

## 🖌️ Prémiové designové principy (baked-in, nepodkročitelné)

Prodejka i landing musí vypadat jako od **špičkového moderního webdesignera**, ne jako šablonový AI web. Principy platí pro každý render:

1. **Editoriál, ne leták:** střídej rytmus sekcí (full-bleed carousel, 2-sloupcové PAS bloky s alternací L/R, foto-pásy s overlay, centrované milníky). Žádné dvě sousední sekce se stejným layoutem.
2. **Foto/textura všude:** žádný text na ploché barvě. Každá „obohacená" sekce má foto, gradient nebo texturu (viz VIZUÁLNÍ HUSTOTA).
3. **Typografická hravost:** původní brand fonty, ale **zvýrazni klíčové slovo** v nadpisu jinou barvou/vahou (`.sp-hl`), ne uniformní blok textu.
4. **Design tokeny:** radius/shadow/type/motion škála v `:root` (`--r-*`, `--shadow-*`, `--step-*`, `--ease-out`). Nikdy ad-hoc hodnoty.
5. **Anti-slop (impeccable):** ❌ side-tab accent (tlustý barevný `border-left` na kartě = #1 AI-tell) → místo něj jemný plný rámeček nebo integrovaný accent. ❌ animace layout vlastností (`width/height/padding/margin`) → `transform`/`opacity`. ❌ emoji jako section markery. ❌ všechno centrované + `rounded-lg` všude.
6. **Pohyb střídmě:** count-up čísla, jemný scale na hoveru, Ken Burns — ne animace v každé sekci (taky AI-tell).
