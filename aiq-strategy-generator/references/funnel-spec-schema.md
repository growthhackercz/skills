# funnel-spec.json — anotované schéma v0.5

Strojový kontrakt mezi `aiq-strategy-generator` (1.9) a `aiq-funnel-builder` (1.1.4).
Příklady jsou ilustrativní — **identifikátory v ukázkách jsou zástupné**
(EXAMPLE_*), reálné hodnoty doplní builder při setupu.

Princip: **spec = myšlení, builder = mechanická exekuce.** Cokoli, co má builder
udělat deterministicky (pole, skórování, větvení, tagy), MUSÍ být ve specu
deklarativně. Builder nic neinterpretuje a nic si nedomýšlí.

## Top-level klíče (všechny povinné, pokud není řečeno jinak)

### Identifikace funnelu

```jsonc
{
  "spec_version": "0.5",                      // verze kontraktu — builder odmítne neznámou
  "funnel_slug": "aiq-vzorovy-funnel",         // ASCII kebab-case; Netlify site name + /documents/sites/<slug>/
  "product": "Vzorový produkt (příklad)",      // lidský název produktu
  "client": "Vzorová firma (příklad)",        // lidský název klienta
  "ghl_location_id": "EXAMPLE_LOCATION_ID",   // GHL sub-account; env GHL_LOCATION_ID má přednost
  "variant": "score",                         // score | audit | plan
  "lead_magnet_name": "Test: Jak velké je u vás riziko ztráty dat?",  // schválený název (Krok 2.6) — název je otázka po RIZIKU/potřebě, ne po tom „jak dobře na tom jste"
  "mode": "automatizovany_prodej",            // Builder 1.0 podporuje pouze tento režim
  "contact_position": "end",                  // Builder 1.0 podporuje pouze end
  "note": "volitelná poznámka pro lidi"       // volitelné
}
```

### `brand` — identita klienta (POVINNÝ)

```jsonc
"brand": {
  "name": "Vzorová firma",                       // zobrazované jméno (patičky webu, „tým X" v e-mailech)
  "cta_url": "https://www.priklad-firmy.cz",     // cíl hlavního nákupního/kontaktního CTA na /r/
  "privacy_email": "info@priklad-firmy.cz",      // kontakt správce osobních údajů (/zasady)
  "email_footer": "Vzorová firma · Ukázková 1, Praha"  // identifikace odesílatele v patičce e-mailů
}
```

Šablona z `brand` skládá titulky stránek, patičky, obálku e-mailů, zásady OÚ
i nákupní CTA — **builder bez kompletního `brand` odmítne stavět**. Hodnoty ber
z productDNA/brandDNA; co chybí, doplň dotazem na uživatele (STOP bod 4).

### `visuals` — podklady pro fotky funnelu (doporučený)

```jsonc
"visuals": {
  "hero_query": "small business team working in a bright modern office",   // EN dotaz pro Pexels — hero foto (landing + prodejní stránka)
  "process_query": "person reviewing documents at a desk, calm and focused",   // EN dotaz — sekce „Jak to probíhá"
  "mood": "profesionální, důvěryhodný, klidný"                   // nálada pro případnou AI generaci
}
```

Dotazy piš **anglicky a jako konkrétní scénu** (Pexels česky nehledá; „water"
je moc obecné). Builder z nich stahuje fotky řetězem brand assety → Pexels API
→ browser → image_generate. Pokud `visuals` chybí, builder si dotazy odvodí
sám — ale strategie zná téma a cílovku nejlíp, proto je dodej.

### `questions[]` — otázky kvízu

```jsonc
{
  "id": "q1",                          // stabilní ID; pořadí v poli = pořadí v kvízu
  "type": "yesno",                     // yesno | single | multi | textarea
  "field_id": "EXAMPLE_FIELD_Q1",      // GHL custom field ID — POKUD pole už existuje
  "field_name": null,                  // jméno pole k vytvoření — POKUD field_id je null
  "text": "Zkoušeli jste někdy zálohu opravdu obnovit?",
  "role": "diagnostic",                // viz „role otázky" níž — řídí problémové zrcadlo
  "options": ["Ano", "Ne"],            // yesno/single/multi; textarea nemá options
  "score": { "Ne": 20, "Ano": 0 }      // body za odpověď signalizující POTŘEBU:
                                       // „Ne, netestováno" = riziko = body. Osa = míra
                                       // rizika/potřeby, ne kompetence zákazníka.
                                       // Mix yesno + vážený single je OK (lepší rozlišení
                                       // než mechanických 5× yesno).
}
```

**`role` — role otázky (POVINNÉ u každé otázky, řídí „problémové zrcadlo" na magnetu):**

Magnet ukazuje hned pod skóre **TOP 5 verbatim odpovědí, které odhalují REÁLNÝ PROBLÉM** klienta (uvědomění problému, ještě před produktem = technika Zrcadlo). Aby se do něj nedostaly námitkové ani nákupní otázky, každá otázka nese `role`:

| role | význam | do zrcadla? |
|---|---|---|
| `diagnostic` | odhaluje mezeru/riziko (nese typicky i `score`) | **ANO** (yes/no i single/multi) |
| `problem` | problém / přání („co chcete zlepšit") | **ANO** |
| `objection` | co klienta brzdí (cena, čas, důvěra) | NE |
| `routing` | preferovaný další krok / signál rozpočtu (= otázka pro `cta_routes`) | NE |
| `qualifying` | jiná kvalifikace | NE |
| `open` | otevřená odpověď / `textarea` | NE |

- **Diagnostické/problémové otázky** (score-nesoucí + „co chcete zlepšit") = `diagnostic`/`problem`.
- **Námitková otázka** („co vás zatím odrazuje") = `objection` — NIKDY `problem`, jinak „Cena" vyskočí jako problém klienta.
- **Otázka o dalším kroku** (pro `cta_routes`/`temperature`) = `routing`.
- V zrcadle jdou **bohaté (single/multi) první** (dostanou hloubkový rozbor), diagnostické yes/no za nimi jako holý mirror. Chybí-li `role`: single/multi ≥3 možnosti se berou jako problémové, yes/no jen se `score` — ale **role vždy vyplňuj**, ať se objection/routing spolehlivě vyřadí.

**Pravidlo field_id / field_name (jádro celé architektury):**
- `field_id` vyplněné → pole v klientově GHL **prokazatelně existuje** (reuse) a zapisuje se přes ID.
- `field_id: null` + `field_name: "AIQ - [Quiz title] - [text otázky]"` → builder pole
  vytvoří přes `POST /customFields`, vrácené `id` **zapíše zpět do funnel-spec.json**.
- NIKDY name/slug/fieldKey matching za běhu. Runtime zná jen ID.
- U nového funnelu budou typicky všechna `field_id: null` + `field_name`;
  vyplněné `field_id` patří jen polím, která v klientově GHL prokazatelně existují.

Multi-select hodnoty se do GHL ukládají jako **CSV string** oddělený `", "`
(„Chuť, Jistota, Pohodlí").

⚠️ **Žádná hodnota v `options` nesmí obsahovat `", "` (čárka + mezera).** Ukládají
se jako CSV s tímhle oddělovačem a při čtení zpět z GHL se tím rozdělují — option
„Ano, chci nabídku" by se rozpadla na „Ano" + „chci nabídku" a přestala by matchovat
skóre, teplotu i mechanismy. Když potřebuješ souvětí, přeformuluj bez čárky
(„Ano chci nabídku" → radši „Chci vidět nabídku"). Platí pro **všechny** otázky,
nejvíc bolí u `multi`.

### `consent_field_id` / `consent_text` / `derived_field_ids`

```jsonc
"consent_field_id": "EXAMPLE_FIELD_CONSENT",  // pole souhlasu (povinný checkbox před submitem)
"consent_text": "Souhlasím se zpracováním odpovědí pro vytvoření personalizované analýzy — viz",
"derived_field_ids": {                        // odvozená pole — vytváří builder při setupu
  "score": null,                              // null → builder vytvoří a doplní
  "segment": null
}
```

**`consent_text` (doporučený)** — text zaškrtávacího souhlasu. Musí odpovídat
tomu, na co se kvíz OPRAVDU ptá. Zmínku o citlivých údajích (zdraví, děti,
finance) piš **jen** když se na ně kvíz ptá — jinak je nepravdivá a zbytečně
odrazuje. Bez klíče použije šablona neutrální výchozí text. Souhlas je vždy
**povinný** (submit bez něj vrací 400), text se přesto přizpůsobuje obsahu kvízu.

### `scoring_bands[]` — pásma skóre (jen varianty se skóre)

```jsonc
{ "min": 80, "max": 100, "category": "vysoke_riziko",  "label": "vysoké riziko",  "action": "prime_doporuceni" },
{ "min": 40, "max": 79,  "category": "stredni_riziko", "label": "střední riziko", "action": "edukace_a_overeni" },
{ "min": 0,  "max": 39,  "category": "nizke_riziko",   "label": "nízké riziko",   "action": "klidna_kontrola" }
```

⚠️ **Pásma monotónně s osou: nejvyšší skóre = největší potřeba/riziko = nejaktivnější
`action`.** Osu pojmenuj po riziku/mezeře („vysoké riziko"), NE po stavu zákazníka
(„dobré pokrytí" obrací význam — spokojený nahoře, nejpotřebnější dole s nejměkčí akcí).
`category`/`label` = pohled zákazníka pro výsledek, prodejní čtení nech mimo obrazovku.

### `segments[]` — segmentace pro důkazy a nadpisy

```jsonc
{
  "key": "male_firmy",
  "trigger": { "q": "q6", "contains": "Jsme do 5 lidí" },   // nebo { "q": "q10", "equals": "Chci vidět nabídku včetně ceny" }
  "headline": "Malé firmy to řeší nejčastěji až po první ztrátě",
  "proof": "U firem do pěti lidí visí zálohy typicky na jednom člověku. Stačí, aby byl týden mimo, a nikdo neví, jestli něco běží."
}
```

Trigger operátory: `contains` (multi) / `equals` (single). Pořadí v poli = priorita
(vyhrává první match). `headline` + `proof` jsou statické texty (L2 vrstva) —
runtime jen vybírá, negeneruje.

### `main_result` — hlavní výsledek magnetu (univerzální, per varianta)

```jsonc
"main_result": {
  "type": "score",                    // score | audit_areas | plan
  "label": "Jak velké je u vás riziko ztráty dat",   // odpovídá na otázku z lead_magnet_name
  "unit": "/100",
  "meaning": {                        // text per kategorie — statická copy, schvaluje se ve STOP 4
    "vysoke_riziko": "Odpovědi ukazují víc slabých míst najednou — záloha se netestuje nebo visí na jednom člověku. Vyplatí se to řešit dřív, než na to přijdete za provozu.",
    "stredni_riziko": "Něco funguje, ale objevují se mezery — typicky se zálohy nekontrolují. Pár míst stojí za doladění.",
    "nizke_riziko": "Základy máte v pořádku, riziko je zatím nízké. Hlídejte, ať to vydrží i ve chvíli, kdy bude zle."
  }
}
```

Naplnění per varianta viz `magnet-structure.md`. **Nic downstream nesmí tvrdě
záviset na skóre** — plán vrací harmonogram a audit může vracet kritické oblasti.

### `temperature_rules` — odvození lead_temperature (hot/warm/cold)

```jsonc
"temperature_rules": {
  "source": "urgency_budget",   // urgency_budget (default) | critical_areas | score
  "question": "q10",            // otázka na preferované řešení (signál rozpočtu)
  "hot": ["Chci vidět nabídku včetně ceny", "Chci řešení i s nastavením a kontrolou"],
  "warm": ["Chci ověřit, jestli se řešení hodí pro nás"],
  "hot_min": 80, "warm_min": 40   // pojistka pro source: "score"
}
```

Tři zdroje (kód je od 0.5.13 skutečně vyhodnocuje, `number_urgency` **záměrně
nemá** — runtime nezná spočítané číslo, jen skóre):

| `source` | Potřebuje | Kdy |
|---|---|---|
| `urgency_budget` | `question` + `hot[]`/`warm[]` (přesné hodnoty z options) | **default nových funnelů** |
| `critical_areas` | `question` + `critical[]` + prahy | audit (počet kritických oblastí) |
| `score` | `hot_min`, `warm_min` | jen když skóre měří naléhavost, ne spokojenost (starší specy) |

`lead_temperature` je univerzální náhrada skóre-kategorií pro větvení e-mailů
a adaptivitu prodejní stránky — vždy dostupná, stejná sémantika downstream.

### `retention_months` — doba uchování OÚ v zásadách (volitelné)

```jsonc
"retention_months": 24   // číslo měsíců; bez klíče se použije 24
```

Právní tvrzení na stránce `/zasady`. Vyplň podle skutečné politiky klienta;
bez klíče šablona uvede 24 měsíců.

### `cta_routes` — routing výzvy k akci podle otázky o preferovaném řešení

Klíč = přesné znění odpovědi (poslední single otázka o dalším kroku), `_default` povinný:

```jsonc
"cta_routes": {
  "Chci nejdřív poradit":                       { "cta": "Rezervovat nezávaznou konzultaci", "type": "consult" },
  "Chci řešení i s nastavením a kontrolou":     { "cta": "Objednat zálohování na klíč", "type": "order" },
  "Chci ověřit, jestli se řešení hodí pro nás": { "cta": "Porovnat varianty zálohování", "type": "compare" },
  "Zatím jen zjišťuji informace":               { "cta": "Poslat klidný přehled", "type": "soft" },
  "_default":                                   { "cta": "Prohlédnout doporučené řešení", "type": "soft" }
}
```

Typy: `consult` | `order` | `installments` | `compare` | `soft`.

### `urgency_source` — enum, povinný

`"capacity"` (omezená kapacita konzultací) | `"cohort"` (běh/kohorta) |
`"season"` (sezónnost) | `"bonus"` (časově omezený bonus) | `"none"` (default).
**Bez reálného zdroje = `none`** — sekvence pak jede bez urgence (cost-of-inaction
close). „Platnost analýzy" je vyřazená jako pseudo-fake. Fake countdown je zakázaný.

### `magnet_structure[]` — legacy metadata pro kompatibilitu

Builder 1.0 podle `magnet_structure` **neskládá pořadí celé výsledkové stránky**.
Pole zůstává ve specu kvůli starším funnelům a jako prompt metadata. Pevnou
psychologickou kostru vykresluje šablona; jedinou dynamicky skládanou částí je
`magnet_middle`.

Legacy sekce je objekt `{ block, key, title, render, persona_field?, instruction? }`:

```jsonc
// LLM sekce (render text/steps/openloop) — builder vezme text z persona_field
{
  "block": 2,                          // pořadí (int)
  "key": "rozbor",                     // stabilní id sekce
  "title": "Co vaše odpovědi říkají o vašem zálohování",  // nadpis, který lead uvidí
  "render": "text",                    // text | steps | openloop
  "persona_field": "magnet_rozbor",    // JEN llm sekce: kam LLM zapsal text (z persona_fields)
  "instruction": "2–3 odstavce: co říká KOMBINACE odpovědí, konkrétně a bez strašení"  // JEN llm: co napsat
}

// deterministická sekce (render main_result/segment/cta) — bez persona_field/instruction
{
  "block": 1,
  "key": "vysledek",
  "title": "Jak velké je u vás riziko ztráty dat",   // nadpis nad skóre odpovídá směru osy (riziko), ne „jak dobře"
  "render": "main_result"              // main_result | segment | cta
}
```

Legacy paleta `render`: `main_result` | `text` | `steps` | `openloop` |
`segment` | `cta`.

**Paleta `persona_field`** (jen pro `text`/`steps`/`openloop`, každé NEJVÝŠ 1×, aby
se obsah neduplikoval): `magnet_rozbor` | `magnet_dobre` | `magnet_rizika` |
`magnet_akce` | `predpis_config`. Tedy max 5 LLM sekcí + 3 deterministické
(`main_result`, `segment`, `cta`) = **strop 8 sekcí**. Každé použité `persona_field`
musí být i v `persona_fields[]`.

U nového funnelu neodvozuj z tohoto pole render ani pořadí stránky. Dynamické
analytické bloky zapisuj výhradně do `magnet_middle`.

### `magnet_middle[]` — FLEXIBILNÍ STŘED magnetu (AIQ Engine, fáze 3)

**Runtime magnetu (mag2) má PEVNOU KOSTRU** — fáze 1 (jméno, skóre, oblasti/pásma),
fáze 2 (rizika, vyčíslení Kč, klíčové odpovědi „pod lupou"), fáze 4 (Shrnutí „kde jste
teď ↔ kam chcete" + pointa), fáze 5 (řešení → předpis → urgence → CTA). Tyhle fáze
šablona vykresluje natvrdo z deterministických dat + pevných persona polí.

**`magnet_middle` je JEDINÁ část, kterou navrhuje AI per funnel** — fáze 3, flexibilní
střed mezi kostrou. Díky němu je každý magnet unikátní při STEJNÉM psychologickém
oblouku. To je jádro **AIQ Enginu** (4. motor CliqSales vedle Content / Ad / Sales) —
personalizační motor, „tajné know-how" na pozadí.

Navrhni **3 bloky (max 5)**. Každý:

```jsonc
{
  "block": 1,
  "key": "situace",                              // stabilní id
  "subtitle": "Rozbor na míru",                  // eyebrow (krátký label nad nadpisem)
  "title": "Co říká kombinace vašich odpovědí",  // H2, který lead uvidí
  "render": "text",                              // text | cards | steps
  "persona_field": "magnet_rozbor",              // kam AI zapíše obsah (MUSÍ být v persona_fields[])
  "instruction": "…"                             // co má AI napsat (volitelné — bez něj se použije FIELD_GUIDE pole)
}
```

**Renderery** (`render`):
- `text` — nadpis + odstavce (markdown). Pole typicky `magnet_rozbor` (hloubkový rozbor).
- `cards` — nadpis + 2–3 karty. Formát pole: každá karta = `první řádek = krátký nadpis`,
  `další řádek = 1–2 věty`, karty oddělené PRÁZDNÝM řádkem. Použij na „kde je největší
  prostor" / mechanismy třídy řešení.
- `steps` — nadpis + očíslované analytické body. Nesmí obsahovat prodejní CTA ani
  obecný checklist „co udělat bez nákupu".

**Doporučená skladba:** situace (`text`, `magnet_rozbor`) → prostor (`cards`,
`magnet_prostor`) → rizika (`text`, `magnet_rizika`). Karty jsou volitelné;
každé nové `persona_field` přidej i do `persona_fields[]`.

**Backward-compat:** když `magnet_middle` chybí, builder spadne na dnešní pevný střed
(rozbor → žebříček oblastí) — starší funnely fungují beze změny.

### Pevná persona pole AIQ Enginu

Builder 1.0 používá vedle původního 27polového setu dalších 5 pevných polí.
`predpis_config` už v původním setu je:
- `souhrn_ted` — Shrnutí „kde je teď" (jeho problémy zhuštěně; fáze 4).
- `souhrn_chci` — Shrnutí „kam chce" (jeho CÍLE z otázky „co chcete zlepšit"; fáze 4).
- `pointa` — silná pointa spojující jeho CÍL a jeho PROBLÉM (fáze 4); **anti-klišé** (žádné
  „mezera jde zavřít", „brzdí vás"), reframe nebo příslib.
- `nalehavost` — urgence z Product DNA (proč TEĎ), **BEZ Kč a procent** (částku doplní
  šablona deterministicky z benchmarku); fáze 5.
- `obraz_potom` — Krok 3 sekce Řešení: emoční „obraz potom" (future pacing), 4–5 vět ve 2 odstavcích.

⚠️ `souhrn_chci` čerpá z otázky „co chcete u … zlepšit" — tuhle otázku (výběrová, multi)
do kvízu ZAŘAĎ, jinak Shrnutí nemá cíle klienta.

### ⚡ AIQ Engine — finální copy & struktura konvence (ladění 2026-07-20)

Šablona (aiq-funnel-builder) drží tyhle konvence napříč funnely — strategie na ně navazuje:

- **`magnet_middle` = jen ANALYTICKÉ bloky** (situace/rozbor). **NEDÁVAT `akce` blok** („co
  udělat hned bez nákupu") — odkláněl od nákupu. **NEDÁVAT segment box** se specifikacemi do
  magnetu. Karty (`cards`) volitelně, ne povinně.
- **Sekce magnetu (nadpisy pevné v šabloně, univerzální):** Na co pozor / Vaše hlavní rizika ·
  Pod lupou / Co se skrývá za vašimi odpověďmi · Souvislosti / Jak to u vás zapadá dohromady ·
  Shrnutí / Kde jste dnes a kde byste chtěli být (Současný stav → Váš cíl) · Co s tím? / Řešení
  na míru vaší situaci (3 kroky: produkt + „Jak to řeší vaši situaci" · Co získáte / Konkrétní
  přínosy pro vás · Vaše nová realita / Vize budoucnosti) · Proč to neodkládat · Další krok.
- **Copy pravidla (vynucuje prompt šablony):** krátké věty (max 15 slov); **>2 věty → odstavce
  oddělené prázdným řádkem** (nikdy zeď textu); žádné opakování napříč poli; **produkt se jmenuje
  JEN v `predpis_config`**; technické specifikace jen v Řešení (predpis), v analýze NE; anti-klišé
  pointa; azbukový sanitizer; obrázky 04/05/06 na plnou šířku ve fázi 5.
- **URL bez tokenu** (čisté `/magnet/<contactId>`), **CTA box navy** (ne barva pásma).
- **Model (3-článkový řetěz vybraný po benchmarku a kritickém review, VŠECHNO floating latest):**
  primár `~openai/gpt-mini-latest` (→ teď GPT-5.6-luna; nejlepší poměr kvalita/rychlost/cena,
  ~$0,02/lead, ~23 s) → fallback `~anthropic/claude-sonnet-latest` (nejsilnější copy, naskočí když
  mini selže lint/JSON) → fallback2 `~openai/gpt-latest` (flagship, poslední pojistka). NEpinovat
  na verzi. Vyřazeno: Haiku (kapacitní chyby — překlepy/pády/halucinace), Gemini (zdravotní claim +
  strach + fake urgence + rozbité JSON v produkci). Prompt má self-check (tykání/ceny/zdraví/klišé).
  - **Per-volání split:** volání „fields" (magnet + prodejní stránka) = **mini primár**; volání
    „emails" (samostatné, blíž prodeji) = **Sonnet primár** (pak mini, pak GPT latest). Řízeno
    parametrem `chain` v `callLlm`/`callWithLint`.

### `personalization_vars[]` + `persona_fields[]`

`personalization_vars` — 8 deterministických proměnných počítaných při submitu
(bez LLM): `first_name`, `score`, `score_category`, `top_pain`,
`recommended_variant`, `segment_headline`, `segment_proof`, `cta_offer`.

`persona_fields` — **32 pevných LLM-generovaných polí** plus každé pole použité
v `magnet_middle` (generují se DVĚMA
nezávislými voláními — pole a e-maily zvlášť, kvůli spolehlivosti; zapisují se do
GHL jako pole „AIQ P - {name}" přes ID z fields-map):

```
main_headline, magnet_headline, sub_headline,
problem1_question, problem1_impact, problem1_source,
problem2_question, problem2_impact, problem2_source,
problem3_question, problem3_impact, problem3_source,
benefit_1_title, benefit_1_description, benefit_2_title, benefit_2_description,
benefit_3_title, benefit_3_description,
objection_1_title, objection_1_response, objection_2_title, objection_2_response,
magnet_rozbor, magnet_dobre, magnet_rizika, magnet_akce,
predpis_config,
souhrn_ted, souhrn_chci, pointa, nalehavost, obraz_potom
```

- **`magnet_headline`** = samostatný H1 výsledkové stránky (funguje sám, velké písmeno);
  `main_headline` navazuje na oslovení na /r (malé písmeno) — jsou to DVĚ různá pole.
- **`problemN_source`** = ID otázky (single/multi s ≥3 možnostmi), ze které problém N
  vychází → render spáruje verbatim citaci odpovědi s dopadem. Smí být prázdné (render
  fallne na pořadí). yes/no a textarea NEJSOU zdroj citace.
- **Hloubka:** `magnet_rozbor` = 3–4 hutné odstavce propojující KOMBINACE odpovědí (ne
  povrch); `problemN_impact` = přesná odpověď → dopad → proč poroste. Micro-markdown
  (`**tučně**`, `- odrážka`) povolen v rozbor/rizika/benefit_*_description (render parsuje).

**Názvy neměnit** — šablona builderu na ně má navázaný render (prodejní stránka
+ magnet) a `ensure-fields.mjs` z nich generuje GHL pole (`magnet_*`/rozbor → LARGE_TEXT,
zbytek TEXT). Do LLM jde jen křestní jméno + odpovědi — nikdy e-mail / telefon / příjmení.

### `score_areas[]` — dílčí skóre oblastí (volitelné, jen varianta `score`)

Rozpad hlavního skóre 0–100 na **3–4 oblasti** pro výsledkovou stránku („víc oblastí
k analýze"). Každá oblast mapuje 1–3 skórované otázky; `area% = body / max × 100`.

```jsonc
"score_areas": [
  { "key": "nejistota", "label": "Nejistota, co doma pijete", "questions": ["q1","q2"],
    "verdicts": { "high": "velká", "mid": "střední", "low": "malá" } }
]
```
- **Label = MÍRA POTŘEBY** (vyšší % = větší potřeba), stejný směr jako hlavní osa (viz
  pravidlo skóre v SKILL.md). Ne „jistota/pokrytí".
- `verdicts` (volitelné) = kvalitativní slovo per pásmo — render ukáže verdikt místo %
  u oblastí s <4 gradacemi bodů (yes/no dá jen 0/50/100, číslo by lhalo).
- Pokrytí: dohromady by měly obsáhnout všechny skórované otázky.

### `benchmark` — „šok z čísla" na výsledkové stránce (volitelné)

Předpočítané hodnoty per odpověď na JEDNU otázku (nejčastěji „kolik/jak často"). Render
ukáže velké číslo + sloupce Dnes / „S řešením" (třída řešení, NE produkt).

```jsonc
"benchmark": {
  "question": "q9",
  "solution_label": "S řešením",
  "today_text": "Současný stav a co vás stojí (BEZ jména produktu)",
  "solution_text": "Co se změní s třídou řešení (BEZ jména produktu)",
  "rows": {
    "<hodnota odpovědi>": { "headline": "<velké číslo>",
      "sub": "<1 řádek kontextu>", "assumption": "<předpoklad výpočtu, POVINNĚ u peněz>" }
  }
}
```
- **`today_text` / `solution_text`** = texty sloupců „Dnes → S řešením". Bez nich render dá generický
  fallback. VŽDY třídu řešení, NIKDY jméno produktu (produkt je až v sekci „Řešení").
- **Dvě třídy hodnot:** *počty* (kusy/rok = čistá aritmetika, bez disclaimeru) vs *peníze*
  (POVINNĚ `assumption` s předpokladem — render ho ukáže drobně „orientačně, při X").
- Čísla PŘEDPOČÍTÁ strategie do `rows` — žádná runtime matematika, žádné vymyšlené číslo.
- Validace = builder validate script (každá option-source má row; peníze jen s `assumption`),
  NE offer whitelist. Řádky jen pro odpovědi, kde má „šok" smysl (nekupuje = vynech).

### `magnet_images` — silné vizuály do výsledkové stránky (volitelné, ⭐ konverze)

Fotky, které render výsledku (magnet 2.0) rozmístí jako full-width pásy + product
reveal. Cesty pod `/public` funnelu (deploy krok: nakopírovat produktové fotky
z `/documents/brand/products/<slug>/carousel/` do `public/img/`). Chybí-li klíč →
slot se přeskočí (fleet-safe).

```jsonc
"magnet_images": {
  "band": "/img/result-hero.jpg",         // vizuální pás hned pod HERO
  "beforeafter": "/img/result-beforeafter.jpg", // benchmark „před a po"
  "product": "/img/result-product.jpg",    // „Váš předpis" = product reveal (čistý produktový/lifestyle záběr)
  "detail": "/img/result-detail.jpg"        // volitelný detail
}
```
- **Zdroj = product-image-generator** (`/documents/brand/products/<slug>/carousel/` je
  výchozí; `01-hero`, `05-pred-po`, `06-lifestyle`, `04-detail`). Pro `product`
  vyber ČISTÝ záběr bez zapečeného headline (nekonkuruje textu magnetu).
- Produkt se v magnetu ukazuje AŽ v `product` (předpis) — dřívější sekce zůstávají
  product-agnostic (třída řešení). Culminace nitě diagnóza → předpis → produkt.

### `offer` — výtah nabídky z productDNA (whitelist pro lint)

```jsonc
"offer": {
  "product": "Vzorový produkt (příklad)",
  "usp": "Automatické zálohování s kopií mimo kancelář, pravidelným testem obnovy a měsíčním přehledem.",
  "guarantee": "Nastavení provede Vzorová firma; první test obnovy proběhne společně s vámi.",
  "price_note": "Vzorové údaje — v reálném specu VŽDY z productDNA, nikdy vymyšlené.",
  "variants": ["Vzorová varianta A", "Vzorová varianta B"]
}
```

Slouží zároveň jako **whitelist pro e-mail lint** — cena/garance smí v generovaném
textu být jen odsud. Zdroj: výhradně productDNA, žádná vymyšlená čísla.

### `mechanisms` — sekce 4 prodejní stránky „Proč to bude fungovat u vás" (POVINNÝ)

Napojuje **konkrétní bolest → konkrétní mechanismus produktu**. Runtime vybere
2–3 bloky podle odpovědí na bolestivou otázku (multi-select, typicky q7).

```jsonc
"mechanisms": {
  // klíč = PŘESNÁ hodnota z options bolestivé otázky (musí sedět znak po znaku)
  "by_pain": {
    "Jistotu funkčních záloh": {
      "title": "Na jistotu: pravidelný test obnovy",
      "text": "Obnova se testuje sama v pravidelném intervalu. Nezjišťujete až v krizi, jestli záloha byla použitelná."
    },
    "Přehled o zálohách": {
      "title": "Na přehled: měsíční souhrn stavu",
      "text": "Jednou měsíčně dostanete přehled, co je zálohované a kdy proběhl poslední test. Nemusíte se ptát."
    }
  },
  // použije se, když se netrefí žádná bolest (2 bloky stačí)
  "default": [
    {
      "title": "Zálohování běží průběžně, ne nárazově",
      "text": "Proces pracuje pravidelně a hlásí se sám. Nečeká, až si někdo vzpomene."
    }
  ]
}
```

**Pravidla:**

- **Píše se per funnel z productDNA.** Nikdy neopisuj mechanismy jiného produktu
  a nevymýšlej technologie — jen to, co productDNA prokazatelně uvádí.
- **Pokryj bolesti, které reálně jdou vyřešit.** Bolest bez mechanismu klidně
  vynech (do `by_pain` nepatří prázdné sliby) — runtime doplní z `default`.
- **`title` = na co to je + čím** („Na jistotu: test obnovy"), `text` = 1–2 věty,
  jak to funguje. Ne výčet vlastností, ne marketingová superlativa.
- **Klíče musí sedět přesně** na `options` bolestivé otázky. Překlep = blok se
  nikdy nezobrazí.
- **Bez tohoto bloku** poskládá builder karty nouzově z `offer.usp` (jen nadpisy)
  a při prázdném výsledku sekci skryje — sekce prodejní stránky tím zmizí.
  Šablona buildera **nesmí** obsahovat mechanismy žádného produktu (G17).

### `reviews` — recenze pro render `reviews` (volitelné, social proof)

Blok 3 recenzí na výsledkové stránce magnetu (`magnet_structure` sekce s
`render: "reviews"`). Bez `reviews` se blok skryje.

```jsonc
"reviews": [
  { "name": "Jana", "meta": "Brno", "text": "Konečně vím, na čem jsem. Test byl rychlý a výsledek dával smysl.", "rating": 5 },
  { "name": "Petr", "meta": "Olomouc", "text": "Ocenil jsem, že to nebylo tlačení do koupě, ale věcné doporučení.", "rating": 5 },
  { "name": "Lucie", "meta": "Praha", "text": "Přehledné a hlavně na míru naší situaci.", "rating": 5 }
]
```

- **Zdroj = reálné recenze z productDNA.** Jen křestní jméno + `meta` (město / kontext),
  **žádné příjmení ani fotka**.
- ⚠️ **Placeholder flag (POVINNÉ):** když klient reálné recenze nemá, vlož **ukázkové**
  a v `AIQ-strategie.md` to **výslovně napiš** jako dočasné k nahrazení / smazání klientem.
  **Nikdy nevydávat vymyšlenou recenzi za pravou.**
- Render vezme prvních 5 (zobrazí 3). `rating` (1–5) je volitelné → hvězdičky.

### `funnel_reviews` — recenze na LANDINGU, hodnotí TEST (volitelné, ⭐ konverze)

Pás 3 recenzí **na landing stránce** (renderuje se za blokem „co změříme", před
kredibilitou). Na rozdíl od `reviews` (produkt, na výsledkové stránce magnetu)
tyhle **hodnotí samotný kvíz** — snižují tření *„má cenu to vyplňovat?"*.
Bez `funnel_reviews` se sekce skryje.

```jsonc
"funnel_reviews": [
  { "name": "Hana", "meta": "Praha", "text": "Otázky byly praktické — na chuť vody i kolik balené doma vypijeme. U pár z nich jsem se zarazila, nad tím jsem nikdy nepřemýšlela.", "rating": 5 },
  { "name": "Tomáš", "meta": "Brno", "text": "Nejvíc mě překvapil výpočet, kolik balené vody u nás za rok proteče. Vidět to černé na bílém byl aha moment.", "rating": 5 },
  { "name": "Lucie", "meta": "Olomouc", "text": "Sotva tři minuty a na konci přehledné skóre. Hezky jsem viděla, kde je u nás doma největší slabina.", "rating": 5 }
]
```

- **Hodnotí TEST, ne produkt ani prodej** — copy pravidla viz `copy-recipes.md`
  → „6) Funnel-recenze" (o kvízu: otázky / výpočet / skóre / rychlost; NE „žádný
  tlak", „místo prodejního hovoru", NE fake CTA).
- **Zdroj + placeholder flag** stejně jako `reviews`: reálné jen z productDNA,
  ukázkové výslovně označ v `AIQ-strategie.md` jako dočasná. **Nikdy vymyšlenou
  za pravou.** Jen křestní jméno + `meta`, žádné příjmení/fotka.
- Render zobrazí první 3. `rating` (1–5) volitelné → hvězdičky.

### `landing` — copy landing page (POVINNÝ od 2026-07-23)

Texty úvodní stránky (dřív samostatný `landing-copy.md`, **zrušeno**). Builder je čte odtud do `app/page.tsx`.

```json
"landing": {
  "hero_headline": "úderný hook (dilema cílovky, ne výčet vlastností)",
  "hero_sub": "podnadpis → pošli do kvízu",
  "areas": [{"title": "měřená oblast 1", "desc": "1 věta"}, {"title": "oblast 2", "desc": "…"}, {"title": "oblast 3", "desc": "…"}],
  "authority": "kredibilita — kdo to postavil a proč mu věřit",
  "cta": "text tlačítka (Získat zdarma…)",
  "quiz_microcopy": "mikrocopy u startu kvízu (volitelné)"
}
```
**Legacy fallback:** chybí-li `landing` a existuje `landing-copy.md`, builder ho ještě přečte (staré funnely).

### `sales` — copy prodejní stránky (obohacovací vrstva, render `/online/[contactId]`)

Prezentační copy prodejky. Render sekci **skryje, když klíč chybí** (fallback). **L3 persona** (hero H1/
podnadpis, zrcadlo, benefity, námitky) se generuje **runtime**, NENÍ v `sales`. Klíče (vše volitelné):
- `promo` (lišta) · `social_proof {rating:ČÍSLO, count, text}` (rating musí být číslo, ne `"5,0"` → NaN) · `authority_stats[]` `{value,label}`
- `testimonial` / `case_study` `{quote, author, meta, rating, highlight}` — `highlight` = přesná podfráze citátu (render ji zvýrazní zlatě)
- `steps[]` `{title,text}` · `day {title,before,after}` · `timeline {title,m1,m6,m12}` · `genesis {title,body,image}` — `body` = **2–3 odstavce** oddělené prázdným řádkem (`\n\n`), render je rozseká na `<p>`; `image` = `/img/…` (origin-story foto vedle textu, editorial 2-sloupec; bez `image` jen text)
- `bonuses[]` `{title,desc,value,img}` · `components[]` (3–6) `{label,title,sub,desc,img,icon}` (+ `components_title`) — **PAS bloky** (viz sales-page-blueprint): `label` = název komponenty (kicker), `title` = silný nadpis, `sub` = podnadpis (1 věta), `desc` = PAS text **jeden odstavec** (Problém→Agitace→Soluce), render alternuje foto L/R · `proof_numbers[]` `{value,label}`
- `comparison {columns[], rows[{label,cells[]}]}` — buňka „ano" → render zelené ✓, „ne" → červené ✗ · `for_whom {title,yes[],no[]}`
- `offer_image` (`/img/…` do value stacku) · `stack_items[]` (co klient reálně získá) · `price {orig,now,save,note}` · `stack2` (bool — zobrazit rekapitulaci nabídky)
- `proof_intro` (věta nad proof čísly; NEfabrikuj počty/„domácnosti") · `guarantee_aha[]` (2–4 odrážky co konkrétně garance kryje) · `guarantee_aha_lead` (1–2 věty **aha-reframe** nad odrážkami — kdo nese riziko; render zvýrazní; renderuje se JEN s `guarantee_aha[]`) · `urgency` (jen reálná) · ~~`closing_line`~~ (⚠️ zatím **nerenderováno** — nevyplňuj) · `faq[]` `{q,a}` · `carousel[]` `{img,title,desc}` (pruh zobrazí 02+; snímek 01 jde do value stacku)

⚠️ **Čísla / ceny / claims jen z `offer` whitelistu** (lint). Obrázky vždy `/img/…` (render `safeImg` sanitizuje na `/img/` fallback).

### `design_tokens`

Barvy a typografie z klientova **DESIGN.md / Brand Kitu**. **Tečou do šablony
runtime** (inline `:root` na `<html>`) — funnel tím dostane brand klienta, ne
default. Každý klíč je volitelný; co chybí, doplní builder z neutrální palety.

```jsonc
"design_tokens": {
  "source": "odkud tokens pocházejí (DESIGN.md / Brand Kit klienta / neutrální theme)",
  "primary": "#1B2A4A",      // hlavní tmavá (hero, nadpisy)
  "accent": "#006799",       // akční barva (tlačítka, odkazy, CTA v e-mailech, střední pásmo)
  "gold": "#C5A55A",         // akcent nejvyššího pásma
  "tertiary": "#4A7C59",     // akcent nejnižšího pásma (starší alias: health_green)
  "bg": "#FFFFFF", "surface": "#F5F5F5",
  "text": "#333333", "text_soft": "#666666", "radius": "10px",
  "font_head": "Montserrat", "font_body": "Open Sans"
}
```

- **`primary` / `accent` / `gold` / `tertiary`** řídí celou paletu funnelu (gauge,
  pásma, tlačítka, CTA v e-mailech). Ber je z Brand Kitu — víc kitů v brandu
  (landing / homepage / produkt) → vyber relevantní pro funnel/landing.
- **`font_head` / `font_body`** jsou jména fontů; šablona dnes renderuje
  Montserrat + Open Sans (dynamické načítání fontu je mimo aktuální builder).
- Klient bez DESIGN.md → tokeny nech neúplné, builder doplní **neutrální prémiový
  light theme**. **Nikdy CliqSales paleta** (brand pollution).

### `personalization_mode` + `pilot_mode`

```jsonc
"personalization_mode": "sync",   // sync (OpenRouter na Netlify, dokreslení na stránce)
                                  // | async (AI Team webhook, rozbor e-mailem)
"pilot_mode": {
  "enabled": false,   // DEFAULT: e-maily odcházejí rovnou skutečným kontaktům
  "note": "volitelné: true = interní zkouška, předměty dostanou prefix [PILOT]"
}
```

Sync = doporučeno (klient má vlastní OpenRouter klíč, ~halíře per kontakt,
personalizace se dokreslí přímo na stránce). Async = personalizaci dělá AI Team
přes webhook (`AIQ_WEBHOOK_URL` + HMAC secret) — pozor na limity předplatného.

### `email_branches` — e-mailové větve

```jsonc
"email_branches": {
  "delivery": "GHL scheduled messages (scheduledTimestamp v SEKUNDÁCH), cancel: DELETE /conversations/messages/email/{id}/schedule",
  "envelope": "pevná: patička s odhlášením řeší GHL sub-account automaticky; reply-to + identifikace odesílatele v šabloně obálky; LLM generuje jen tělo",
  "lint": [
    "ceny/garance jen z offer whitelistu",
    "URL jen /r/ /magnet/ + doména klienta",
    "žádná vymyšlená čísla",
    "vykání",
    "oslovení z vokativ tabulky, ne LLM"
  ],
  "hot":  [ { "id": "E1", "day": 1, "goal": "diagnóza→předpis + /r/ link" }, … ],
  "warm": [ … 5 e-mailů … ],
  "cold": [ … 3 e-maily … ]
}
```

Osnovy (day + goal per e-mail per větev) definuje strategy skill a schvalují se
ve STOP 4. Plné texty generuje runtime per kontakt. Detail: `email-branches.md`.

### `ops` — provozní kontrakt

```jsonc
"ops": {
  "hot_lead": "GHL task na kontaktu (notifikace klientovi = onboarding)",
  "reply_to": null,                                  // doplní se při onboardingu klienta
  "tag_prefix": "AIQ - Riziko ztráty dat"     // PREFIX VŠECH tagů i polí funnelu (= AIQ - [Quiz title])
}
```

**`tag_prefix` (POVINNÝ) = `AIQ - [Quiz title]`** (krátký název magnetu s pomlčkou,
STEJNÝ prefix, jaký nese `field_name` otázek — `AIQ - [Quiz title] - [otázka]`).
⚠️ **Tagy GHL ukládá lowercase** → stavové tagy vzniknou jako `aiq - [quiz] - active`
/ `- hot lead` / `- converted` … (builder je proto lowercasuje, aby porovnání
matchlo). Konvence stavu: **prefix + „ - <stav>"** (jednotný „ - " oddělovač).
Z něj se odvozují VŠECHNY tagy i custom pole, **namespacnuté per funnel** — kdyby
měl klient víc AIQ funnelů, generické (neprefixované) tagy by se mezi nimi mísily. Tagy,
persona pole (prodejní + magnet), stavová pole i otázky pak **sdílí týž prefix**.
Drž `[Quiz title]` **krátký a čitelný** (ne dlouhý marketingový titul — jde do
každého tagu i pole):

| Tag | Kdo nastaví | Stav |
|---|---|---|
| `[prefix]` | funnel (submit) | přišel z magnetu — permanentní, segmentace |
| `[prefix] - active` | funnel (po naplánování) | v sekvenci, e-maily jedou |
| `[prefix] - completed` | **guard** (poslední e-mail odešel) | sekvence dojela do konce |
| `[prefix] - converted` | **KLIENT** (jeho trigger) | dosáhl cíle → guard stáhne zbytek |
| `[prefix] - hot lead` | funnel | horký lead k obvolání |
| `[prefix] - processing` | funnel, přechodně | lease proti 2× personalizaci |

⚠️ **GHL tagy lowercasuje** → reálně `aiq - [kvíz] - active` / `- converted` … (builder
je proto drží lowercase, aby porovnání matchlo). Jednotný „ - " oddělovač před stavem.
Stav sekvence žije v polích `[prefix] - Scheduled IDs` + `[prefix] - Sequence End`
(guard z nich pracuje), ne v tazích.

**⚠️ Stop follow-upu = klientův trigger (do onboardingu/návodu!).** Sekvenci
zastaví **guard** — hodinová **Netlify Scheduled Function** — když kontakt dostane
`[prefix] - converted`. Ten tag **nenastavuje funnel**: přidá ho klient přes svou
GHL automatizaci na svůj event (nákup, rezervace, ruční…). Onboarding krok: *„napoj
checkout/prodej tak, aby při dosažení cíle přidal do GHL tag `aiq - [kvíz] - converted`
(GHL ho ukládá lowercase) — jinak se follow-up nezastaví."* Guard běží per web (každý
funnel má svůj cron scoped na svoje tagy). `[prefix] - completed` (přirozený konec bez
konverze) = kandidát na re-target. *(Legacy `state_tags`/`purchase_tag`/`kill_switch_tag` jsou
deprecated — jen kvůli parsování starých speců.)*

## Kontrolní checklist před předáním builderu (strukturní JSON)

Toto je kanonická **strukturní** kontrola specu (obsahové/strategické QA drží SKILL.md
„Kontrola na konci generace"):

- [ ] Validní JSON, `spec_version: "0.5"`
- [ ] `brand` kompletní (`name` + `cta_url` + `privacy_email` + `email_footer`) se skutečnými údaji klienta, žádné zástupné hodnoty
- [ ] Každá otázka má `field_id` NEBO `field_name` (nikdy obojí null)
- [ ] **Žádná hodnota v `options` neobsahuje `", "`** (čárka+mezera) — rozbila by CSV round-trip multi hodnot z GHL
- [ ] 5 skórovacích yesno otázek (u variant se skóre) + otevřený box na závěr
- [ ] `scoring_bands` pokrývají 0–100 bez děr a překryvů; každé pásmo má `label` (lidsky čitelný název pro klienta)
- [ ] `cta_routes` mají klíč pro KAŽDOU odpověď routovací otázky + `_default`
- [ ] `main_result.meaning` má text pro každou kategorii ze `scoring_bands`
- [ ] `variant` je `score`, `audit` nebo `plan`; `mode: "automatizovany_prodej"` a `contact_position: "end"`
- [ ] `magnet_structure` je pouze legacy metadata; nový dynamický obsah je v `magnet_middle`
- [ ] **AIQ Engine:** `magnet_middle` má 3 analytické bloky (max 5); každé `render` je z `text`/`cards`/`steps`; každé `persona_field` je i v `persona_fields[]`; žádný akční checklist ani CTA
- [ ] **AIQ Engine:** `persona_fields[]` obsahuje všech 32 pevných polí + každé pole použité v `magnet_middle`
- [ ] **AIQ Engine:** kvíz má výběrovou otázku „co chcete zlepšit" (zdroj pro `souhrn_chci`); `nalehavost` bez Kč/procent
- [ ] `mechanisms.by_pain` má klíče **znak po znaku** shodné s `options` bolestivé otázky a `mechanisms.default` má aspoň 1 blok
- [ ] `temperature_rules` (source `urgency_budget`): `question` existuje a `hot[]`/`warm[]` hodnoty jsou **znak po znaku** shodné s `options` té otázky (překlep → horký lead tiše spadne do cold)
- [ ] `persona_fields` = 32 pevných polí + dynamická pole středu; názvy pevných polí nezměněné
- [ ] `urgency_source` odpovídá realitě (default `none`)
- [ ] `pilot_mode.enabled: false` (default — e-maily odcházejí rovnou)
- [ ] `offer` výhradně z productDNA
