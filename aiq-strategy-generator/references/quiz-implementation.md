# Pokyny pro implementaci kvízu — pravidla generace `02-pokyny-landing-kviz.md`

Tento reference soubor definuje, jak skill generuje **platformově neutrální dokument s pokyny pro AI agenta** (v GoHighLevel AI Studio, ScoreApp, Webflow forms, Typeform, n8n, Make atd.) pro vytvoření landing page + kvízu + thank you page.

**Klíčový princip:** dokument neobsahuje žádné CRM-specific zmínky, žádné e-mailové sekvence ani webhook routing. Jen landing + pole + kvíz + thank you. E-maily zůstávají v `01-strategie.md`.

---

## Quiz slug — auto-generace

V Krok 2.5 (po výběru varianty v Krok 2, před autonomní generací) skill rozhodne quiz slug:

1. **Quiz name = kombinace produktu/služby + typu kvízu** (kontext + identifikace v jednom řetězci).

   **Mapování vybrané varianty → base code (interní slug) + Type label (UI ve field name):**

   | Varianta | Base code (interní, složka) | Type label (UI ve field name) |
   |---|---|---|
   | Skóre / Osobní hodnocení | `score` | `Skóre` |
   | Diagnostický audit | `audit` | `Audit` |
   | Personalizovaný plán / Harmonogram | `plan` | `Plán` |
   | Kalkulačka přínosů | `calc` | `Kalk` |
   | Strategický plán na míru | `blueprint` | `Strategie` |

   **Sestavení Quiz name:**
   ```
   Quiz name = [Krátký název produktu/služby] [Type label]
   ```
   Příklady napříč doménami:
   - Wellness produkt + varianta Skóre → Quiz name = `[Produkt] Skóre` (např. `Spánkové skóre`)
   - B2B SaaS + varianta Audit → Quiz name = `[Produkt] Audit` (např. `Prodejní audit`)
   - Online kurz + varianta Plán → Quiz name = `[Produkt] Plán` (např. `Plán prvního milionu`)
   - High-ticket konzultace + varianta Strategický plán → Quiz name = `[Produkt] Strategie` (např. `Růstová strategie`)
   - E-commerce produkt + varianta Skóre → Quiz name = `[Produkt] Skóre` (např. `Skóre péče o pleť`)

   **Pravidla pro krátký název produktu:**
   - Zkratka 1–3 slova, ne plný oficiální název (odstraň generické sufixy jako „MedAll", „Pro", „Plus")
   - S diakritikou OK
   - Maximum ~15 znaků (aby celý field name zůstal pod 50)
   - Pokud má brand jednotný produkt, použij jeho hlavní benefit nebo USP keyword

2. **Detekce kolize** (více kvízů stejné varianty pro stejný produkt):
   - Pokud `[base_code]/` neexistuje → quiz_slug = `[base_code]`, Quiz name = `[Produkt] [Type label]`
   - Pokud existuje → inkrementuj:
     - `score` → `score2` → `score3`
     - Quiz name = `[Produkt] [Type label] 2`, `[Produkt] [Type label] 3`
     - Příklad: `[Produkt] Skóre`, `[Produkt] Skóre 2`, `[Produkt] Skóre 3`

3. **Quiz title** (popisek pro folder v GHL UI) — vymysli sám podle primárního benefitu / bolesti z Product DNA:
   - Příklady napříč doménami: wellness + Skóre + bolest „nekvalitní spánek" → `Skóre kvality spánku`; B2B SaaS + Audit + „pomalé follow-upy" → `Audit prodejní cesty`; online kurz + Plán + „chybí čas" → `Plán prvního milionu`
   - Max 40 znaků, s diakritikou OK

4. **Output folder (z Krok 2.6):** `/documents/lead-magnets/AIQ [Quiz title]/`. Žádná migrace ze starých `/documents/aiq-strategies/` cest — skill je ignoruje.

---

## Naming convention — KRITICKÉ ✋

### Pozadí (proč to děláme takhle)

**GoHighLevel a podobné platformy posílají do webhooku field NAME jako klíč JSON payloadu**, ne interní field key. Příklad reálného GHL webhook payloadu:

```json
{
  "body": {
    "AIQ - Pravidelná domácí regenerace": "Ano",
    "AIQ - Rodinné využití přístroje": "Ne",
    ...
  }
}
```

Field name v platformě = klíč ve webhook payloadu = co vidí uživatel v UI kontaktu.

**Důsledek:** field name musí být současně:
1. **Lidsky čitelné** (uživatel v CliqSales / GHL admin to vidí v Contact Details)
2. **Identifikovatelné pro AI agenta** (filter podle prefixu, parsovatelné z webhook payloadu)
3. **Krátké** (max ~50 znaků, jinak nepřehledné v UI)
4. **Jednoznačné napříč kvízy** (nesmí kolidovat mezi kvízy stejného produktu)

### Tři vrstvy identifikace pole

Každé custom pole má **tři identifikátory**, každý slouží jiné roli:

| Vrstva | Pattern | Komu slouží | Příklad |
|---|---|---|---|
| **Field name** (zobrazení v Contact Details + klíč ve webhook payloadu) | `AIQ - [Quiz short name] - [CELÝ TEXT OTÁZKY]` | Admin / klient v GHL UI, model v automatizaci (n8n/Make) — vidí plný kontext otázky bez slovníku | `AIQ - Dýcháte čistý vzduch - Vnímáte v některých místnostech zhoršený vzduch, prach nebo pachy?` |
| **Field key (slug)** (GHL template tagy, REST API filter) | `aiq_[quiz_slug]_[max 3 slova]` | E-mail/SMS personalizace (`{{contact.X}}`), filter přes API, automation rules | `aiq_dychate_cisty_vzduch_zhorseny_vzduch_pachy` |
| **Question text** (co návštěvník vidí v kvízu) | = Field name **po prefixu** `AIQ - [Quiz short name] - ` | Návštěvník kvízu — čte plné znění otázky | „Vnímáte v některých místnostech zhoršený vzduch, prach nebo pachy?" |

### Pattern Field name (3 části, vždy)

```
AIQ - [Quiz short name] - [CELÝ TEXT OTÁZKY]
```

| Část | Funkce | Pravidla | Příklad |
|---|---|---|---|
| **`AIQ - `** | Filter prefix — backend filtruje `key.startsWith("AIQ - ")` | Vždy přesně tento string, s mezerami kolem pomlčky | `AIQ - ` |
| **`[Quiz short name] - `** | Identifikace kvízu — krátký marketing slogan / esence názvu kvízu | Lidsky čitelné, sentence case, s diakritikou OK, max ~25 znaků | `Dýcháte čistý vzduch - ` |
| **`[CELÝ TEXT OTÁZKY]`** | **Plné znění otázky** (s otazníkem, diakritikou, vykáním) | Identický s Question text | `Vnímáte v některých místnostech zhoršený vzduch, prach nebo pachy?` |

**Bez stropu znaků** — GHL nemá rigidní limit na field name. **Field name = Question text** v 1:1 mapování po prefixu.

### Pattern Field key (3 části, vždy)

```
aiq_[quiz_slug]_[max 3 slova z otázky]
```

| Část | Pravidla | Příklad |
|---|---|---|
| **`aiq_`** | Filter prefix pro API / template tagy | `aiq_` |
| **`[quiz_slug]_`** | Quiz short name převedený do ASCII snake_case. Může být víc slov (1–4). | `dychate_cisty_vzduch_` |
| **`[max 3 slova z otázky]`** | Sémantická esence otázky — vyber max 3 klíčová slova, ASCII bez diakritiky, snake_case | `zhorseny_vzduch_pachy` |

**Pravidla pro field key:**
- ASCII snake_case (lowercase + číslice + podtržítka)
- Bez diakritiky (`á→a`, `š→s`, `ě→e`...)
- **Max 3 slova** v otázkové části — stručná esence, ne celá otázka
- Vždy obsahuje quiz slug v prefixu (filtrovatelné napříč všemi poli kvízu)

### Quiz short name vs Quiz title vs Quiz slug

| Pojem | Použití | Příklad |
|---|---|---|
| **Base code** (interní technický slug) | Idempotency key CC tasku + meta.json záznam (NE folder) | `score`, `score2`, `audit` |
| **Quiz title** (UI popisek, interní reference) | Krok 2.5 popisek | `Skóre regenerace doma` |
| **Quiz short name** (ve Field name) | Krátký marketing slogan v prefixu Field name (s diakritikou OK) | `Dýcháte čistý vzduch`, `Spánkové skóre`, `Prodejní audit` |
| **Quiz slug (ASCII)** (ve Field key) | ASCII snake_case z Quiz short name pro Field key | `dychate_cisty_vzduch`, `spankove_skore`, `prodejni_audit` |

Quiz short name odvodí skill v Krok 2.6 ze schváleného názvu lead magnetu. Quiz slug (ASCII) skill odvodí automaticky z Quiz short name: lowercase + transliterace + snake_case.

### Proč 3 vrstvy?

GHL webhook posílá payload klíče = **Field name** (lidský). Admin / klient v Contact Details a model v automatizaci dostanou plný kontext otázky.

GHL template tagy a REST API používají **Field key** (krátký slug). Když chceš v e-mailu personalizovat `{{contact.aiq_dychate_cisty_vzduch_zhorseny_vzduch_pachy}}`, je to čitelnější než 100-znakový lidský label. Stejně tak filter přes API: `GET /v1/customFields?key_prefix=aiq_dychate_cisty_vzduch_` = všechna pole kvízu v jednom requestu.

### Příklady správně × špatně

**Field name:**

| ✅ Správně | ❌ Špatně | Důvod |
|---|---|---|
| `AIQ - Dýcháte čistý vzduch - Vnímáte v některých místnostech zhoršený vzduch nebo pachy?` | `AIQ - Skóre - Projevy znečištění` | Krátký popisek bez kontextu — model v automatizaci neví, co znamená |
| `AIQ - Spánkové skóre - Jak dlouho vám večer trvá usnout?` | `AIQ - Skóre - Usínání` | Krátký popisek bez kontextu otázky |
| `AIQ - Prodejní audit - Kolik leadů měsíčně ztrácíte na pomalé odezvě?` | `AIQ - Pomalá odezva` | Chybí Quiz short name + plný text otázky |
| `AIQ - Dýcháte čistý vzduch - Je něco dalšího, co bychom měli vědět?` | `AIQ - Dýcháte čistý vzduch - Cokoli dalšího` | Plný text otázky vč. otazníku |

**Field key:**

| ✅ Správně (max 3 slova v otázkové části) | ❌ Špatně | Důvod |
|---|---|---|
| `aiq_dychate_cisty_vzduch_zhorseny_vzduch_pachy` | `aiq_dychate_cisty_vzduch_vnimate_v_nekterych_mistnostech_zhorseny_vzduch_prach_nebo_pachy` | Otázková část = celá otázka, ne max 3 slova |
| `aiq_spankove_skore_usinani_vecer_dlouho` | `aiq_spankove_skore_usinani` | Jen 1 slovo — málo informace o kontextu |
| `aiq_prodejni_audit_pomala_odezva_leady` | `aiq__prodejni__audit__pomala__odezva` | Auto-vygenerovaný GHL slug s dvojitými podtržítky — manuálně přejmenovat |
| `aiq_plan_milionu_hodiny_tydne_investice` | `Aiq_Plan_Milionu_Hodiny` | UpperCase / CamelCase — vždy lowercase |

### Question text (text v kvízu pro návštěvníka) = SAMOSTATNĚ

Lidská otázka, kterou návštěvník vidí v kvízu, je **vlastní entita**, ne totožná s field name. Field name je krátký technický popisek; question text je plná otázka.

| Field name | Question text v kvízu |
|---|---|
| `AIQ - Spánkové skóre - Pravidelný režim` | „Chodíte spát každý den ve stejnou hodinu (±30 minut)?" |
| `AIQ - Spánkové skóre - Rodinné využití` | „Týká se nekvalitní spánek víc členů domácnosti než jen vás?" |
| `AIQ - Prodejní audit - Hlavní problém` | „Který hlavní problém v prodeji řešíte v tuto chvíli?" |

### Folder strategy (GHL omezení)

**⚠️ AI Studio agent v aktuální verzi GHL NEUMÍ přes API vytvářet ani specifikovat folder při tvorbě pole.** Pole automaticky spadnou do default folderu **„Additional Info"**.

**Důsledek pro náš design:**
- **Žádný folder neuvádíme** v tabulce vlastních polí ani v promptu pro AI agenta — bylo by to falešné očekávání
- **Veškerá identifikace kvízu je vmáčknutá do field name** (`AIQ - [Quiz short name] - [Otázka]`) — ne do folderu
- **Backend filter pracuje s prefixem field name**, ne s folderem
- **Klient / admin** může v GHL UI po deployi pole ručně přesunout do vlastního folderu (klik na ⋮ → Move to folder) — funkčně nic nezmění, jen vizuální organizace v Settings → Custom Fields

Pokud někdy GHL API začne podporovat folder při tvorbě pole, vrátíme se k folder strategy.

### Mapování typu otázky → typ pole

| Typ otázky v dotazníku | Typ pole | Možnosti |
|---|---|---|
| Ano/Ne (5 doporučených postupů) | Single select / Radio | `Ano`, `Ne` |
| Single choice (současná situace) | Single select / Dropdown | 4–5 variant podle Product DNA |
| Multiple choice (priority, problémy) | Multi-checkbox | 4–6 variant |
| Open text (cíl, závěrečný box) | Long text / Textarea | (max 500 znaků default / 2000 v režimu pro osobní setkání) |
| Numerické (kalkulačka) | Number | min/max validace pokud relevant |
| Skála 1–10 | Slider / Number | min 1 max 10 |

---

## Filter příklady pro AI agenta / backend

S touto naming convention dokáže AI agent (v n8n, Make, vlastní webhook handler) jednoduše parsovat:

```javascript
// Všechna AIQ data napříč všemi produkty / kvízy
const aiqFields = Object.keys(body).filter(k => k.startsWith("AIQ - "));

// Všechno z jednoho produktu (napříč všemi kvízy pro něj) — nahraď [Produkt] prefixem svého kvízu
const productAFields = Object.keys(body).filter(k => k.startsWith("AIQ - [Produkt A] "));
const productBFields = Object.keys(body).filter(k => k.startsWith("AIQ - [Produkt B] "));

// Konkrétní kvíz
const quiz1Fields = Object.keys(body).filter(k => k.startsWith("AIQ - [Quiz short name 1] - "));
const quiz2Fields = Object.keys(body).filter(k => k.startsWith("AIQ - [Quiz short name 2] - "));

// Pro personalizaci e-mailu
const personalProblem = body["AIQ - [Quiz short name] - Hlavní problém"];
const personalBudget = body["AIQ - [Quiz short name] - Preferovaný rozpočet"];
```

V GHL e-mail / SMS template tagy:

```
{{contact.AIQ - [Quiz short name] - [Esence otázky 1]}}
{{contact.AIQ - [Quiz short name] - [Esence otázky 2]}}
```

(GHL template engine podporuje mezery a diakritiku v field name.)

---

## Struktura `02-pokyny-landing-kviz.md` (template) — POŘADÍ KROKŮ 1.3.6+

Dokument musí mít přesně tuto strukturu (technická závislost — pole MUSÍ vzniknout napřed):

```
## Projekt
   (Lead magnet, Produkt, Quiz title, Quiz short name, Quiz slug, Varianta, Režim)

## KROK 1 — Landing page
   Hook · Podnadpis · Tři měřitelné oblasti · Autorita · CTA
   + VIZUÁL design tokens (z DESIGN.md, pokud existuje)
   + HERO MOCKUP pokyny (cesta + umístění + format)

## KROK 2 — Custom pole (jen seznam field names)
   Seznam Field names z tabulky výše
   ŽÁDNÉ fieldKey, dataType, options, API endpoint, contact. prefix —
   agent v GHL AI Studio si zbytek vyřídí sám (interní nástroj + Quiz.tsx)

## KROK 3 — Kvíz / dotazník (jen seznam otázek + UX pravidla)
   UX patterns (progress · selected · transition · required markers)
   Pořadí kontaktu (krátký → na KONEC, dlouhý → na ZAČÁTEK)
   Seznam otázek (= shodné s Field names z KROK 2) + typy odpovědí
   Skórování (pro Skóre/Audit varianty)
   ŽÁDNÝ form action URL, payload struktura, contact. prefix —
   agent si vyřídí ve Quiz.tsx form post

## KROK 4 — Thank you page
   Rychlé vyhodnocení · Segmenty · Dynamický další krok
   + VIZUÁL design tokens (z DESIGN.md, pokud existuje)
```

**🚨 ULTRA-SIMPLIFIED 1.3.8 (zjednodušení proti 1.3.6–1.3.7):**

Pavel ověřil **outgoing webhook test:** GHL forwarduje payload **s field name jako klíč** (= ne field key). Tj. klient v n8n / Make automation jednoduše filtruje:

```javascript
const aiqFields = Object.entries(body).filter(([k]) => k.startsWith("AIQ - "));
```

→ Získá všechny AIQ data podle field name. **Field key v CRM je destruktivní auto-slug, ale to nevadí — nikdy ho nepoužíváme.**

**Důsledek pro spec:**
- Agent v GHL AI Studio dostane **jen seznam field names** v KROK 2 (= žádné fieldKey, dataType, options, API instrukce, contact. prefix)
- Agent dostane **jen seznam otázek + UX pravidla** v KROK 3 (= žádný form action URL, payload struktura)
- **Agent si všechno ostatní vyřídí sám** (interní nástroj pro create fields, default GHL form post pro Quiz.tsx)
- N8n / Make automation parsuje **podle field name** v outgoing webhook

**🚨 KRITICKÉ pravidlo z 1.3.6 (Pavlův insight ze screenshotu task #94):**

Agent v AI Studio v reálném testu Pavlovi řekl „nemůžu nastavit fieldKey, CRM si ho generuje sám". **TO JE NEPRAVDA** — agent v některých polích explicit fieldKey poslal správně, v jiných ne. Tj. agent to UMÍ, jen ho default chování zjednodušuje (pošle jen `name`, CRM vygeneruje destruktivní auto-slug `aiq__audit_vzduchu__xxx__`).

Naše instrukce v KROK 2 musí být **maximálně imperativní** — VŽDY oba parametry, ne někdy.

**🚨 DATA SE ODESÍLAJÍ PŘES FORM POST, NE PŘES WEBHOOK (Pavlův insight 1.3.6):**

Quiz.tsx odesílá data PŘES GHL form post endpoint (interní GHL form submission), NE přes custom webhook URL.
- Form action = GHL form endpoint (agent v AI Studio si ho dohledá interně přes svůj integration layer)
- Method = POST
- Payload obsahuje `contact.${fieldKey}` prefix u všech custom fields
- Důvod: uživatelský flow (landing → kvíz → fields → thank you), ne technická závislost

```markdown
# Pokyny pro AI agenta — [Quiz title]

> **Tento dokument je platformově neutrální.** Použij ho v GoHighLevel AI Studio,
> ScoreApp, Webflow, Typeform, Tally, Make/n8n nebo jakémkoli quiz/funnel builderu.

**Produkt:** [název produktu]
**Varianta lead magnetu:** [Skóre / Audit / Plán / Kalkulačka / Strategický plán]
**Schválený název lead magnetu (z Krok 2.6):** „[plný název]"
**Quiz title (interní popisek):** [Quiz title z Krok 2.5]
**Quiz short name (ve field name):** [krátká esence schváleného názvu, max ~25 znaků] — např. `Dýcháte čistý vzduch`, `Spánkové skóre`, `Prodejní audit`
**Quiz slug (ASCII):** [snake_case verze quiz short name]

---

## Tabulka vlastních polí (= zdroj pravdy)

**Field name = Question text** (po prefixu `AIQ - [Quiz short name] - `) — plný text otázky. **Field key** = krátký ASCII slug (max 3 slova v otázkové části) pro template tagy a API filter.

| # | ID | Field name (= Question text v kvízu, = webhook key) | Field key (= API slug, template tag) | Typ | Možnosti |
|---|---|---|---|---|---|
| 1 | Q1 | `AIQ - [Quiz short name] - [Plné znění otázky 1]?` | `aiq_[quiz_slug]_[3_slova_1]` | Single select | Ano · Ne |
| 2 | Q2 | `AIQ - [Quiz short name] - [Plné znění otázky 2]?` | `aiq_[quiz_slug]_[3_slova_2]` | Single select | Ano · Ne |
| ... | ... | ... | ... | ... | ... |
| N | QN | `AIQ - [Quiz short name] - Je něco dalšího, co bychom měli vědět?` | `aiq_[quiz_slug]_cokoli_dalsiho` | Long text | (otevřený text) |

**Konkrétní příklad** (doména wellness — produkt řešící kvalitu vzduchu doma, kvíz „Dýcháte opravdu doma čistý vzduch?", quiz short name `Dýcháte čistý vzduch`, quiz slug ASCII `dychate_cisty_vzduch`):

| # | ID | Field name | Field key | Typ | Možnosti |
|---|---|---|---|---|---|
| 1 | Q1 | `AIQ - Dýcháte čistý vzduch - Vnímáte v některých místnostech zhoršený vzduch, prach nebo pachy?` | `aiq_dychate_cisty_vzduch_zhorseny_vzduch_pachy` | Single select | Ano · Ne |
| 2 | Q2 | `AIQ - Dýcháte čistý vzduch - Větráte denně alespoň 2× 5 minut?` | `aiq_dychate_cisty_vzduch_pravidelne_vetrani_denne` | Single select | Ano · Ne |
| 3 | Q3 | `AIQ - Dýcháte čistý vzduch - Která místnost je pro vás klíčová?` | `aiq_dychate_cisty_vzduch_klicova_mistnost_cisticka` | Single select | Dětský pokoj · Ložnice · Obývák · Celá domácnost |
| 4 | Q4 | `AIQ - Dýcháte čistý vzduch - Sledujete pravidelně účinnost čističky?` | `aiq_dychate_cisty_vzduch_sledovani_ucinnosti` | Single select | Ano · Ne |
| ... | ... | ... | ... | ... | ... |
| 13 | Q13 | `AIQ - Dýcháte čistý vzduch - Je něco dalšího, co bychom měli vědět?` | `aiq_dychate_cisty_vzduch_cokoli_dalsiho` | Long text | (otevřený text) |

**Tato tabulka je jediný zdroj pravdy.** AI agent v platformě se musí držet PŘESNÝCH field names i field keys — nezkracovat, nepřejmenovávat, nepřidávat / nemazat slova.

**Tabulka NEZAHRNUJE kontaktní pole** (jméno, e-mail, telefon) — ty jsou system fields v GHL a posílají se v payloadu pod standardními keys (`first_name`, `email`, `phone`). Pořadí v kvízu řeší KROK 3.

---

## Design tokens (vizuální identita stránek)

> Tyto tokeny jsou **extrahované z `/documents/brand/DESIGN.md` klienta**. AI agent v platformě nemá přístup k brand library, proto **konkrétní HEX hodnoty a fonty jsou tady v dokumentu**. Použij přesně tyto hodnoty pro landing page (KROK 1) i thank you page (KROK 4).

### Barvy

| Role | HEX | Použití |
|---|---|---|
| **Primary / background** | `[#primary]` | Hlavní pozadí stránky |
| **Surface** | `[#surface]` | Karty, boxy, kontejnery |
| **Surface elevated** | `[#surface-elevated]` | Akcenty, hover stavy |
| **Text — strong** | `[#text-strong]` | Nadpisy, hlavní zpráva |
| **Text — body** | `[#text-body]` | Běžný text, popisky |
| **Accent gradient start** | `[#accent-1]` | Začátek gradientu (tlačítka, akcenty) |
| **Accent gradient end** | `[#accent-2]` | Konec gradientu |
| **CTA / link** | `[#cta]` | Tlačítka, klikací prvky |
| **Success / hot** | `[#success]` | Pozitivní výsledky |
| **Warning** | `[#warning]` | Upozornění |

### Gradient signature

```
linear-gradient(165deg, [#accent-1] 0%, [#accent-2] 100%)
```

Použij pro: tlačítka CTA, hero akcenty na landing page, ikona ⏳ na thank you page.

### Typografie

| Role | Font | Váha | Velikost (desktop / mobile) | Letter-spacing |
|---|---|---|---|---|
| **Display hero (landing h1)** | `[Display font]` | `[váha]` | `[velikost]` / `[velikost]` | `[letter-spacing]` |
| **Heading (h2)** | `[Headline font]` | `[váha]` | `[velikost]` / `[velikost]` | `[letter-spacing]` |
| **Subheading (h3)** | `[Sub-heading font]` | `[váha]` | `[velikost]` / `[velikost]` | — |
| **Body** | `[Body font]` | `[váha]` | `[velikost]` | — |
| **Eyebrow / label** | `[Label font]` | `[váha]` | `[velikost]` | UPPERCASE, tracking |

### Border radius (jediný layout token)

- **Border radius signature:** `[radius]px` (karty, tlačítka, boxy) — z DESIGN.md

> 🚨 **NIKDY nediktuj pevné rozměry layoutu** (max content width, hero padding, grid proporce, sekce padding). Agent v AI Studio rozhodne layout sám podle svého designového citu. My dáváme jen barvy + typografii + radius (= brand identity), ne konkrétní rozmístění.

#### 🚨 ANTI-LAYOUT-INSTRUCTION pravidlo (1.3.11+)

V CELÉM `02-pokyny-landing-kviz.md` (= včetně KROK 1, KROK 4, VIZUÁL sekce) **NIKDY nepíši explicit layout instrukce**. Layout je výhradně v rukou agenta v platformě.

**❌ ZAKÁZANÉ fráze** (Pavel je v 1.3.10 testu vrátil zpět do výstupu — must NOT appear):

- ❌ `Max šířka stránky: 1180–1240 px`
- ❌ `Padding hero: 96px top, 64px bottom`
- ❌ `Container: 1200 px, gap 80 px mezi sekcemi`
- ❌ `Grid: 2 columns desktop, 1 column mobile, gap 24 px`
- ❌ `Section padding: 64px vertikálně, 24px horizontálně`
- ❌ `rounded-2xl`, `shadow-lg`, `py-12`, `gap-8` (Tailwind utility classes)
- ❌ `Vertical rhythm: 8px baseline, 1.5 line-height`
- ❌ `Hero proporce: text 60 %, mockup 40 %` s konkrétní px hodnotou

**✅ POVOLENÉ** (= brand identity + obsahové pokyny):

- ✅ HEX barvy z DESIGN.md (`#0F172A`, `linear-gradient(165deg, #06B6D4 0%, #10B981 100%)`)
- ✅ Font names + váhy + velikosti (např. `Inter 700, 56px desktop / 36px mobile`)
- ✅ Radius v px jako single brand token (např. `8px`)
- ✅ Obsahové pokyny: „Nadpis (max 14 slov)", „3 oblasti — ikona + věta", „CTA tlačítko: <text>"
- ✅ Pozice ve významu „kde to logicky patří": „logo vlevo nahoře v headeru", „hero mockup vedle textu na desktop / pod textem na mobile" (= NE px proporce)

**Důvod:** AI agent v GHL AI Studio má vlastní container/grid engine. Naše px hodnoty buď ignoruje (= layout vypadá jako builder default), nebo respektuje nesprávně (= kolize s platformou). Layout je práce agenta; my dáváme jen brand identity.

**Pokud se ti to chce psát do dokumentu** („mělo by to být uspořádané takhle…") → **NEPIŠ to**. Místo toho dej agentovi jen obsah a brand tokeny — layout vyřeší sám.

### Logo

- **Použij přiložené logo značky** (klient ti ho přiloží do promptu spolu s tímto dokumentem). Nemáš přístup k lokálnímu filesystem klienta — logo dostaneš jako attachment.
- **Min šířka:** 120 px, **max:** 240 px
- **Pozice:** vlevo nahoře v headeru landing page
- Pokud klient logo NEPŘILOŽIL → vlož placeholder `[LOGO]` text v headeru a v notes pro klienta uveď: „Logo chybí. Přiložte prosím PNG/SVG logo k promptu."

### Brand-board reference

Pokud platforma podporuje upload moodboard obrázku jako referenci pro AI generování:
- Path: `/documents/brand/brand-board.png` (lokálně) nebo `[veřejná URL]`
- Použij jako vizuální referenci stylu (atmosféra, kompozice, color treatment)

### Anti-pattern (čemu se vyhnout)

- ❌ Použít barvy mimo paletu z DESIGN.md (žádné placeholder modré z platform templatů)
- ❌ Sans-serif náhrada za designové fonty bez fallback ladění (font stack: `[Display font]`, `Inter`, `system-ui`, sans-serif)
- ❌ Žádné stock fotky lidí, kteří se nepodobají cílovce
- ❌ Kulaté radiusy `> 16px` (signature je `[radius]px`, ne pill-shape)
- ❌ Akcent jako celé pozadí (gradient jen na akcenty, ne na page background)

---

## KROK 1 — Landing page

**🔑 Klíčové pravidlo:** Tento prompt jde k AI agentovi v platformě (GHL AI Studio / ScoreApp / Webflow / Typeform). Agent v platformě **nemá přístup k Brand DNA, Product DNA ani `01-strategie.md`**. Proto všechny texty MUSÍ být v promptu **kompletní a hotové** — žádné odkazy typu „použij hook z 01-strategie.md", žádné formuly typu „kvantifikuj výsledek + aktivní sloveso", žádné placeholdery `[…]`. Vše copy-paste-ready.

**Tvoje (Alex / cso) práce v Krok 3:** vyplnit níže uvedený template **konkrétními finálními texty** odvozenými z brand kontextu + schváleného názvu lead magnetu + Product DNA. Žádné `[OVĚŘ S KLIENTEM]` ve výstupu. Pokud podklad chybí, vymysli konzervativní default a poznámku „doporučujeme ověřit" dej do `01-strategie.md` (strategický dokument pro klienta), ne do `02-pokyny-landing-kviz.md` (pokyny pro agenta).

**Prompt pro AI agenta** (kompletní hotové texty, tykání, žádné placeholdery):

```
Vytvoř landing page s následující strukturou. Vlož přesně texty níže —
nepřepisuj je, neinterpretuj, neměň formulace.

═══ NADPIS (h1) ═══

[VLOŽ KOMPLETNÍ NADPIS — schválený hook lead magnetu z Krok 2.6 nebo
jeho landing varianta. Konkrétní výsledek + číslo/čas + emoční náboj.
Bez brand jména. Max 60 znaků.]

Příklad konkrétního vyplnění:
„Spočítej si, kolik tě doma opravdu stojí pitná voda"

═══ PODNADPIS (h2) ═══

[VLOŽ KOMPLETNÍ PODNADPIS — 1–2 věty. Kvantifikovaný výsledek
(% / Kč / dny / litry) + konkrétní akce, kterou kvíz nabídne.]

Příklad konkrétního vyplnění:
„Krátká kalkulačka ti ukáže orientační roční náklady, počet plastových
lahví a praktickou zátěž současného systému pití doma — a doporučí, jaký
další krok dává smysl pro tvoji domácnost."

═══ TŘI MĚŘITELNÉ OBLASTI (bullet list pod podnadpisem) ═══

[VLOŽ 3 BULLET POINTY — každý začíná aktivním slovesem v 1. os. mn.
(Spočítáme / Zjistíme / Najdeme / Změříme / Porovnáme / Ukážeme) +
konkrétní výsledek s číslem nebo benefitem.]

Příklad konkrétního vyplnění:
• Spočítáme, kolik ročně utrácíš za balenou vodu nebo náhradní řešení.
• Zjistíme, kolik plastových lahví prochází tvojí domácností za rok.
• Najdeme, jestli je pro tebe hlavní téma cena, pohodlí, chuť nebo rodina.

═══ AUTORITA (boxík nebo sekce pod oblastmi) ═══

[VLOŽ KOMPLETNÍ TEXT — kdo lead magnet vytvořil + důvěryhodnost +
volitelný social proof. 2–4 věty. ŽÁDNÉ instrukce typu „komunikace má
znít klidně" — ty patří do 01-strategie.md, ne sem.]

Příklad konkrétního vyplnění:
„Live100.cz je specializovaný Zepter e-shop s osobním přístupem.
Nejde o anonymní prodej — pokud si nejsi jistý/á, můžeš se poradit
s člověkem, který produkty zná a pomůže ti ověřit, jestli řešení dává
smysl právě pro tvoji domácnost. Aqueena Pro je domácí filtrační systém
s 5stupňovou reverzní osmózou, inteligentním displejem a hlídáním
stavu filtrů."

═══ VÝZVA K AKCI (CTA tlačítko + mikrotext) ═══

[VLOŽ KOMPLETNÍ CTA — text tlačítka (akce + benefit) + mikrotext pod
tlačítkem (doba + nákladovost + co bude dál).]

Příklad konkrétního vyplnění:
Tlačítko: „Spočítat moje náklady na pitnou vodu"
Mikrotext: „Zabere přibližně 5 minut. Výsledek ti pošleme e-mailem."

═══ HERO MOCKUP — POVINNÝ PRVEK NAD FOLD ═══

VIZUÁL LEAD MAGNETU (mockup):

**Použij přiložený mockup lead magnetu** (klient ti ho přiloží do promptu
spolu s tímto dokumentem). Nemáš přístup k lokálnímu filesystem klienta
— mockup obrázek dostaneš jako attachment.

Vlož vedle textu hooku/podnadpisu jako náhled toho, co návštěvník
po vyplnění kvízu dostane:
- Desktop: split layout — text 50–60 % vlevo, mockup 40–50 % vpravo,
  oba zarovnané na střed vertikálně
- Mobile: mockup full-width pod podnadpisem (nad CTA tlačítkem)
- Format mockupu: 3:4 vertikál (premium dokumentový feel)
- Žádný další ořez, padding ani styling — mockup byl předem vygenerován
  v brand-konzistentním designu

CÍL: vizuálně potvrdit „dostanu hodnotný dokument / dashboard / analýzu"
= primární CR booster (+20–50 % konverze vs. text-only landing).

⚠️ Pokud klient mockup NEPŘILOŽIL k promptu → vlož placeholder
[MOCKUP TBD] a v notes pro klienta uveď: „Mockup chybí. Přiložte
prosím obrázek lead magnetu (3:4 vertikál) k tomuto promptu a regenerujte
landing page."

═══ VIZUÁL — POVINNÉ DESIGN TOKENY ═══

POZADÍ STRÁNKY: [#primary] (tmavé navy / klientův primary)
KARTY A BOXY: [#surface] s border radius [radius]px
TEXT NADPISŮ: [#text-strong]
TEXT BODY: [#text-body]

GRADIENT (pro hero akcent + tlačítko CTA):
linear-gradient(165deg, [#accent-1] 0%, [#accent-2] 100%)

TLAČÍTKO CTA:
- Pozadí: gradient výše
- Text: [#primary] nebo bílá (kontrast)
- Radius: [radius]px (NE pill shape)

TYPOGRAFIE:
- H1 nadpis: [Display font] [váha], [velikost] desktop / [velikost] mobile
  Letter-spacing: [letter-spacing]
- H2 podnadpis: [Headline font] [váha], [velikost]
- Body: [Body font], [velikost]
- Eyebrow nad nadpisem: [Label font], UPPERCASE, 11–13px, tracking 2px

LOGO: Použij přiložené logo značky (klient ti ho dal jako attachment v promptu) — vlevo nahoře v headeru

LAYOUT: Rozhodni podle svého designového citu — žádné pevné šířky, paddingy ani grid proporce nediktujeme. Drž se brand identity (barvy, typografie, radius), ale rozmístění / proporce / spacing jsou na tobě. Cíl: kreativní, zajímavý hero, ne sterilní template.

ŽÁDNÉ: violet/purple/pink barvy, stock fotky lidí, pill-shape tlačítka
(radius >16px), placeholder template barvy z builder UI.

Tlačítko CTA vede na kvíz (následující krok).

CÍL: konverze landing → vyplněný kvíz 20–40 %.
```

---

## KROK 2 — Custom pole (POVINNĚ TEĎ vytvoř, NEPTEJ SE)

🚨 **IMPERATIV:** Pole MUSÍ vzniknout PŘED tím, než půjdeš na KROK 3. Quiz.tsx v KROK 3 odkazuje na tyto field keys přes `contact.X` prefix — pokud pole v CRM neexistují, form data nepřitečou nikam (= unmapped fields, data ztracená).

🚨 **NEPTEJ SE uživatele** „Mám pole vytvořit, nebo už je máš?" — vždy JEDNEJ podle postupu níže. Test Therapy Air iOn 25.5.2026 ukázal, že agent v AI Studio v 1.3.8/1.3.12 zapsal field keys do Quiz.tsx, ale pole fyzicky nevytvořil — pak se zeptal. To je ZAKÁZÁNO. 1.3.13 vyžaduje aktivní jednání.

### Postup (čiň, neptej se)

1. **ZKONTROLUJ stávající custom fields v CRM.** Pro každý Field name ze seznamu níže ověř, jestli pole už existuje (např. z minulé generace).

2. **Pro KAŽDÝ Field name který NEEXISTUJE → vytvoř ho TEĎ** pomocí svého interního CRM nástroje / GHL integration layer. GHL si automaticky vygeneruje field key z field name destruktivním slugifierem (= náš algoritmus v KROK 3 match přesně tomu, viz sekce „Field keys v Quiz.tsx form data").

3. **Pro KAŽDÝ Field name který UŽ existuje → NEDUPLIKUJ.** Použij existující pole as-is (zachová se i historická data v existujících kontaktech).

4. **Po dokončení oznam JEDNOU zprávou:**
   ```
   ✅ KROK 2 hotový: vytvořeno X nových polí, použito Y existujících
   (celkem N). Pokračuji na KROK 3 (Quiz.tsx).
   ```

5. **POKRAČUJ na KROK 3 BEZ čekání na potvrzení uživatele.**

### Field names k vytvoření / ověření

```
1. AIQ - [Quiz short name] - [Question text 1]
2. AIQ - [Quiz short name] - [Question text 2]
...
N. AIQ - [Quiz short name] - [Question text N]
```

(= shodné s tabulkou „Tabulka vlastních polí" výše, sloupec Field name)

### ❌ ZAKÁZANÉ chování

- ❌ **Ptát se uživatele** „Mám pole vytvořit nebo už je máš v CRM?" → VŽDY jednej sám podle bodů 1–5 výše. Když pole z minulé generace existují, použij je. Když chybí, vytvoř.
- ❌ **Žádat o explicit fieldKey / dataType / options od uživatele** → GHL si key vygeneruje destruktivně sám, dataType default „Single line" stačí, options se neukládají (multi-select = CSV string v jednom poli).
- ❌ **Přeskočit KROK 2 a zapsat field keys do Quiz.tsx bez fyzického vytvoření polí** → Quiz.tsx by posílal data do neexistujících polí = unmapped fields = data ztracená.
- ❌ **Zastavit se po KROK 2 a čekat na user input** → Po oznámení výsledku pokračuj rovnou na KROK 3.
- ❌ **Smazat existující pole a vytvořit znova** → ztratil bys historická data v existujících kontaktech. Pouze přidávej chybějící.

### Proč není potřeba dávat agentovi víc

GHL outgoing webhook forwarduje data pod **field name jako klíč** (= ne field key). Klient v n8n / Make / vlastní backend filtruje:

```javascript
const aiqFields = Object.entries(body).filter(([k]) => k.startsWith("AIQ - "));
```

Quiz.tsx v KROK 3 posílá data **pod field key** (= `aiq__quiz_slug__esence` BEZ `contact.` prefixu) přes GHL form post endpoint. Match na CRM custom field zajišťuje `formLabels` mapping v payloadu — detail v sekci „🚨 KRITICKÉ — Mapping do CRM" v KROK 3.

Tj. v KROK 2 stačí dát agentovi **seznam field names** + imperativ „vytvoř TEĎ". Agent v AI Studio zbytek (field key auto-slug, dataType, API endpoint) vyřídí interním nástrojem.

---

## KROK 3 — Kvíz / dotazník (jen seznam otázek + UX pravidla)

🚨 ULTRA-SIMPLIFIED 1.3.8: Agent si vyřídí form action, payload mapping, contact. prefix. Stačí mu seznam otázek + UX pravidla.

### UX pravidla

- Progress bar s textem `Otázka X z N`
- Vybraná odpověď má jiné pozadí (selected state highlight)
- Plynulý přechod mezi otázkami (animaci si zvol sám). Pozor na React stale closure — validace tlačítka „Pokračovat" musí číst answers state přes latest ref / useEffect, NE inline ve event handleru (jinak první klik nepustí dál, druhý ano)
- Tlačítko „Pokračovat" je disabled, dokud answer pro aktuální otázku není v state — ne aktivní s validation message
- Povinné fields s asterisk markerem; validační error inline pod polem
- Kontakt (jméno, e-mail, telefon volitelný) je VŽDY POSLEDNÍ krok

### Pořadí kontaktu (per režim z Krok 1)

- **Krátký kvíz** (10–15 otázek, default „automatizovaný prodej"): kontakt **na KONEC** (konverze e-mail gate 40 %+ vs 5 % na začátku)
- **Dlouhý kvíz** (až 35 otázek, režim „pro osobní setkání"): kontakt **na ZAČÁTEK** (filtr serióznosti, kvalita kontaktů místo kvantity)

### Prompt pro agenta

```
Vytvoř multi-step kvíz s těmito otázkami (= shodné s Field names z KROK 2):

1. Question text 1?
   Typ odpovědi: [RADIO ano/ne | RADIO 1 z víc | CHECKBOX víc současně | LARGE_TEXT textarea]
   Možnosti (pokud RADIO/CHECKBOX): [z sloupce „Možnosti" v tabulce]

2. Question text 2?
   ...

Kontakt na [KONEC | ZAČÁTEK] podle režimu.

Form post pošli do GHL form endpoint (= znáš interně).
```

### Skórování (pro Skóre / Audit varianty)

Otázky 1–5 (ano/ne) tvoří základní skóre připravenosti / zátěže:

- Každé „Ano" = 20 bodů (max 100)
- 80–100 bodů: vysoká zátěž / vysoká připravenost → doporuč produkt rovnou
- 40–60 bodů: střední → doporuč edukaci, poradenský další krok
- 0–20 bodů: nízká → netlač na prodej, nabídni jen informace

### 🚨 KRITICKÉ — Mapping do CRM (form post payload)

**Pozadí (Série testů Therapy Air iOn 25.–26.5.2026):** Quiz.tsx form post payload MUSÍ splnit 3 podmínky, jinak AIQ pole skončí v `Unmapped Fields` a data nepřitečou do CRM contact custom fields. Agent v AI Studio žádnou z nich defaultně neimplementuje správně — MUSÍŠ mu je explicitně říct.

---

#### Pravidlo 1 — Field keys BEZ `contact.` prefixu

V payloadu posílej field keys **prostá** (`aiq__quiz_slug__esence`), NIKDY s `contact.` prefixem.

**Důvod:** GHL form post parser tečku v `contact.` eskapuje na `__DOT__` (= konflikt s template tag syntax `{{contact.X}}`) — v Form submission details / Contact Details view se zobrazí jako „Contact D O T A I Q -..." (cosmetic rozbité, rušivé pro klienta). `contact.` prefix patří JEN do template tagů v e-mailech / SMS, NIKDY do form data klíčů.

```typescript
// ❌ ŠPATNĚ
formData: {
  "contact.aiq__audit_vzduchu__alergie": "Ano"
}

// ✅ SPRÁVNĚ
formData: {
  "aiq__audit_vzduchu__alergie": "Ano"
}
```

---

#### Pravidlo 2 — formLabels obsahuje PLNÝ field name vč. prefixu

`formLabels[fieldKey]` MUSÍ obsahovat **plný field name z CRM** (= včetně prefixu `AIQ - [Quiz short name] - `), NE jen samotný question text.

**Důvod:** GHL form post matchuje field_key → CRM custom field tím, že hledá custom field, jehož **field name PŘESNĚ odpovídá** hodnotě v `formLabels[fieldKey]`. Pokud pošleš jen `"Co vás trápí?"`, GHL nenajde CRM pole s tímto názvem (= reálné pole má název `"AIQ - Audit vzduchu - Co vás trápí?"`) → unmapped.

```typescript
// ❌ ŠPATNĚ — jen question text, GHL nenajde shodu
formLabels[q.fieldKey] = q.question;
// = formLabels["aiq__audit_vzduchu__alergie"] = "Máte doma alergie?"

// ✅ SPRÁVNĚ — plný field name vč. prefixu
formLabels[q.fieldKey] = "AIQ - " + quizShortName + " - " + q.question;
// = formLabels["aiq__audit_vzduchu__alergie"] = "AIQ - Audit vzduchu - Máte doma alergie?"
```

---

#### Pravidlo 3 — Array hodnoty převést na CSV string

Multi-select checkbox otázky vrací array `["Děti", "Senior"]`. PŘED odesláním převeď na CSV string:

```typescript
const processedAnswers = Object.entries(answers).reduce(
  (acc, [key, value]) => {
    acc[key] = Array.isArray(value) ? value.join(", ") : value;
    return acc;
  }, {} as Record<string, string>
);
// Výsledek: ["Děti", "Senior"] → "Děti, Senior"
```

---

#### Kompletní payload struktura

```typescript
// 1. processedAnswers — arrays → CSV
const processedAnswers = Object.entries(answers).reduce(
  (acc, [key, value]) => {
    acc[key] = Array.isArray(value) ? value.join(", ") : value;
    return acc;
  }, {} as Record<string, string>
);

// 2. formLabels — field_key → PLNÝ field name vč. "AIQ - [Quiz short name] - " prefixu
const quizShortName = "Audit vzduchu";  // z meta.json.quiz_short_name
const formLabels: Record<string, string> = {
  first_name: "Jméno",
  last_name: "Příjmení",
  email: "E-mail",
  phone: "Telefon",
  // Souhlas (pokud má kvíz consent checkbox)
  "aiq__audit_vzduchu__souhlas": "AIQ - " + quizShortName + " - Souhlas",
};
questions.forEach(q => {
  formLabels[q.fieldKey] = "AIQ - " + quizShortName + " - " + q.question;
});

// 3. payload — keys BEZ contact. prefixu
const trackingPayload = {
  type: "external_form_submission",
  timestamp: Date.now(),
  formId: "[Quiz title z meta.json]",   // např. "Audit Vzduchu"
  formData: {
    first_name: contactForm.firstName,
    last_name: contactForm.lastName,
    email: contactForm.email,
    phone: contactForm.phone,
    "aiq__audit_vzduchu__souhlas": contactForm.consent ? "Ano" : "Ne",
    ...processedAnswers  // ← keys BEZ contact. prefixu
  },
  formLabels             // ← KRITICKÉ pro GHL párování
};
```

---

#### ✅ Validace po deployi

Po testovacím submitu zkontroluj **Form submission details** v GHL admin:

| Sekce | Co očekáváš |
|---|---|
| **Mapped Fields** | first_name, last_name, email + **VŠECHNA AIQ pole** |
| **Unmapped Fields** | **PRÁZDNÉ** `{}`. Pokud něco v Unmapped → zkontroluj 3 pravidla výše |
| **Form Data** | AIQ pole jako string (CSV pro multi-select), ne arrays |
| **Audit log v UI** | čisté `A I Q - Audit vzduchu -...`, NE `Contact D O T A I Q -...` (= prefix v keys je odstraněn) |
| **Contact Details v CRM** | Po refreshi vidíš AIQ custom fields s hodnotami |

---

## KROK 4 — Thank you page

**Pevná struktura** (uprav jen části v hranatých závorkách):

```
NADPIS (h1): „Gratuluji ke spuštění vašeho hodnocení"
PODNADPIS (h2): „Tady je vaše rychlé vyhodnocení."

─────────────────────────────────────────

RYCHLÉ VYHODNOCENÍ (zobrazit hned, klientský render z odpovědí kvízu):
  • [Hlavní výsledek per varianta:
     - Skóre: ukazatel 0–100 % + kategorie horký/vlažný/studený
     - Audit: shrnutí kategorií
     - Plán: časová osa preview
     - Kalkulačka: hlavní číslo s měnou
     - Strategický plán: 3 strategické příležitosti]
  • 2–3 věty kontextu („Patříte mezi X %...")

─────────────────────────────────────────

HLAVNÍ ZPRÁVA (zvýrazněný box s ikonou ⏳ nebo loading animation):

  „⏳ Připravujeme na pozadí vaši pokročilou analýzu — postavenou
  přesně na vašich odpovědích. Váš personalizovaný [název magnetu]
  vám pošleme do 5 minut do e-mailu na {{contact.email}}."

─────────────────────────────────────────

VOLITELNĚ:
  • 1–2 testimoniály z Product DNA `## 7.`
  • 3–4 bullet pointy: co najdete uvnitř analýzy
  • Odkaz na kontakt / podporu
```

**Prompt pro AI agenta:**

```
Vytvoř thank you page s následující strukturou.

PEVNÝ NADPIS: „Gratuluji ke spuštění vašeho hodnocení"
PEVNÝ PODNADPIS: „Tady je vaše rychlé vyhodnocení."

RYCHLÉ VYHODNOCENÍ (sekce nad fold):
[per varianta — viz výše, přizpůs odpovědím z kvízu]

KLÍČOVÝ TEXT — zvýrazněný kontrastní box s ikonou hodin / loading:
„⏳ Připravujeme na pozadí vaši pokročilou analýzu — postavenou
přesně na vašich odpovědích. Váš personalizovaný [název magnetu]
vám pošleme do 5 minut do e-mailu na {{contact.email}}."

POZICE: Klíčový text MUSÍ být viditelný hned po načtení stránky
(nad fold, kontrastní barva, vlevo ikona ⏳). Klient nesmí mít
pochybnost, že něco přijde.

VOLITELNĚ pod fold:
  • 1–2 testimoniály (z Product DNA `## 7.`)
  • Bullet pointy „Co najdete uvnitř vaší [varianta]" (3–4)
  • Kontakt / odkaz na podporu

═══ VIZUÁL — POVINNÉ DESIGN TOKENY ═══

(Stejné jako landing page, ať vznikne vizuální kontinuita.)

POZADÍ: [#primary]
KARTY: [#surface], radius [radius]px
TEXT NADPISŮ: [#text-strong], TEXT BODY: [#text-body]

KLÍČOVÝ ZVÝRAZNĚNÝ BOX („Připravujeme analýzu…"):
- Pozadí: [#surface-elevated] nebo soft gradient [#accent-1] s opacity 15 %
- Border-left: 4px solid [#accent-1] (vizuální značka)
- Radius: [radius]px
- Padding: 24px 28px
- Ikona ⏳ vlevo, 32px, barva [#accent-1] nebo [#warning]
- Text: [#text-strong] [Body font] 16–18px

TYPOGRAFIE (stejně jako landing):
- H1 nadpis: [Display font] [váha], [velikost] / [velikost mobile]
- H2 podnadpis: [Headline font] [váha], [velikost]
- Body: [Body font]

LOGO: Použij stejné přiložené logo jako na landing page — vlevo nahoře
GRADIENT: pro skóre ukazatel / kategorie indikátor:
linear-gradient(165deg, [#accent-1] 0%, [#accent-2] 100%)

ŽÁDNÉ: jiné barvy než z palety výše, žádné stock images, žádné
celostránkové gradient backgroundy.
```

---

## Validační checklist

Po dokončení v platformě odškrtni:

```
[ ] Landing page existuje, hook + 3 oblasti + autorita + CTA viditelné
[ ] Tlačítko CTA na landing page vede na kvíz
[ ] [N] vlastních polí existuje v GHL Settings → Custom Fields
    (folder „Additional Info" je default, OK)
[ ] Každé Field name začíná „AIQ - [Quiz short name] - "
    (např. „AIQ - Dýcháte čistý vzduch - ")
[ ] Field name = Question text v kvízu (1:1 mapování, plný text otázky)
[ ] Každý Field key (slug) odpovídá tabulce 1:1 — ASCII snake_case
    `aiq_[quiz_slug]_[max 3 slova]`, žádný auto-vygenerovaný `aiq__skre__zneitn`
[ ] Kvíz má správné pořadí podle režimu:
    • Krátký (10–15 otázek): obsah → KONTAKT NA KONEC před thank you
    • Dlouhý (35 otázek, osobní setkání): KONTAKT NA ZAČÁTEK → obsah
[ ] Po odeslání kontaktu (krátký) / posledního kroku (dlouhý) →
    redirect na thank you page
[ ] Thank you page má rychlé vyhodnocení + klíčový text „připravujeme analýzu"
[ ] Test submit: vyplň testovací kontakt → otevři Contact Details v GHL
    → pole „AIQ - [Quiz short name] - …" mají vyplněné hodnoty
    (NESMÍ skončit v Unmapped Fields → znamenalo by, že field names
    v platformě neodpovídají tabulce)
[ ] Webhook payload obsahuje klíče s prefixem „AIQ - [Quiz short name] - "
    (lidský label, NE slug s prefixem „contact.")
[ ] Template tag `{{contact.aiq_[quiz_slug]_[X]}}` funguje v test e-mailu —
    nahradí se skutečnou hodnotou (= field key v platformě sedí s tabulkou)
[ ] Landing page i thank you page používají PŘESNÉ HEX barvy + fonty
    z „Design tokens" sekce výše — žádné default builder barvy
[ ] Tlačítko CTA má brand gradient (cyan→mint nebo dle klienta), radius [radius]px
[ ] Logo viditelné v headeru obou stránek
```
```

---

## Co se generuje DO `02-pokyny-landing-kviz.md`

**🔴 POVINNÝ KROK PŘED GENERACÍ:** Načti `/documents/brand/DESIGN.md` klienta a extrahuj **konkrétní HEX hodnoty, font names, radius, gradient stack**.

**Pokud DESIGN.md chybí:**

🚫 **ŽÁDNÁ default CliqSales paleta jako fallback** (= brand pollution — klient by dostal cizí CliqSales-feel místo svého).

✅ **VIZUÁL sekce v `02-pokyny-landing-kviz.md` se ÚPLNĚ VYNECHÁ.** Žádný flag, žádný placeholder, žádná poznámka v `01-strategie.md`. Vygeneruj jen texty (Nadpis, Podnadpis, Tři oblasti, Autorita, CTA) bez design tokenů. Klient si DESIGN.md doplní později manuálně pokud bude potřebovat brand styling — pak může spustit AIQ skill znovu v režimu „regeneruj design tokens pro AIQ [Quiz title]".

Pokračuj na Krok 3 bez blocking.

**Pokud DESIGN.md existuje:**

**Tokeny vlož do dokumentu jako KONKRÉTNÍ HEX/FONT hodnoty** (ne placeholdery `[#primary]`). AI agent v platformě nemá přístup k brand library, takže pokud necháš placeholder, agent zvolí náhodné barvy z builder template.

Skill v Krok 3 (autonomní generace) vyplní template výše s konkrétními daty:

1. **Header dokumentu:** název kvízu, produkt, varianta, Quiz short name, Quiz slug (ASCII)
2. **Tabulka polí:** 12–35 řádků podle struktury dotazníku z `01-strategie.md`
   - Pro každé pole vyplň: ID, **Field name** (`AIQ - [Quiz short name] - [plný text otázky]`), **Field key** (`aiq_[quiz_slug]_[max 3 slova]` ASCII snake_case), typ, možnosti
   - Question text = Field name po prefixu — neopakuj v separátním sloupci
   - Q1–Q5 = ano/ne pole z části 2 dotazníku
   - Q6–Q(N) = otevřené kvalifikační z části 3 dotazníku
   - Poslední = závěrečný otevřený box („Je něco dalšího…")
3. **KROK 1 prompt:** vyplnit konkrétní hook / podnadpis / 3 oblasti / autoritu / CTA z `01-strategie.md`
4. **KROK 2 prompt:** přilož tabulku vlastních polí (zkopírovat z úvodu dokumentu)
5. **KROK 3 prompt:** propoj question text z tabulky na field name z tabulky
6. **KROK 4 prompt:** vyplnit konkrétní variantu (Skóre / Audit / ...) + název magnetu z `01-strategie.md` sekce 2
7. **Validační checklist:** vyplnit konkrétní N (počet polí) a Quiz name
