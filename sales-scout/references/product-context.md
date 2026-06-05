# Product context — jak Scout pracuje s Product DNA

Sales Scout nemůže vyrobit hodnotný brief bez kontextu **kterého produktu** se týká. Tento dokument popisuje, jak skill v Kroku 0.5 produkt identifikuje a jak v Kroku 5 posuzuje fit firmy pro konkrétní produkt.

## Zdroj pravdy: `/documents/brand/products/[slug]/productDNA.md`

Každý váš produkt má vlastní Product DNA — markdown soubor se strukturovaným popisem. Vytváří se přes skill `product-dna-generator`. Obsahuje sekce:

- **Pozicování** (kategorie, segment, USP)
- **Hodnotová propozice** (co řeší, pro koho, jaký výsledek)
- **Ideální klient** (firmografika, technografika, behaviorální signály)
- **Cenotvorba a balíčky**
- **Námitky a odpovědi**
- **Důkazy** (reference, případové studie)
- **Spouštěče** (trigger události)
- **Souhrn**

Sales Scout primárně čerpá ze sekcí **Ideální klient** (pro fit posouzení) a **Pozicování** + **Hodnotová propozice** (pro sales úhly a e-mail).

## Krok 0.5 — Identifikace produktu (autonomně)

### Rozhodovací tabulka

| Vstup z Krok 0 | Počet Product DNA v `/documents/brand/products/` | Akce |
|---|---|---|
| `product=bioptron-medall` v promptu | irelevantní | použij jen ten (`product_mode = "single"`) |
| Bez explicitního produktu | **0 produktů** | exit kód 4 + zpráva *„Žádný Product DNA. Vytvoř aspoň jeden přes product-dna-generator."* |
| Bez explicitního produktu | **1 produkt** | použij ten automaticky (`product_mode = "single"`) |
| Bez explicitního produktu | **2+ produktů** | **multi-product režim** (`product_mode = "multi"`): v Kroku 5 spočti fit pro každý produkt, vyber top 1–3 |

### Extrakce produktu z promptu (regex + LLM)

**Pokus 1 — strukturovaný klíč:**

```python
match = re.search(r'product[=:]\s*([a-z0-9\-]+)', prompt, re.IGNORECASE)
```

Zachytí `product=bioptron-medall`, `product: ai-akcelerator`, `Product=Live100`.

**Pokus 2 — zmínka v textu (LLM uvažování):**

Hledej v promptu fráze:
- „pro [Název produktu]"
- „nabízíme [Název produktu]"
- „[Název produktu] pro firmu"
- „prodáváme [Název produktu]"

Příklady:
- *„Scout brief na Effect Clinic pro Bioptron"* → `product = "bioptron"`
- *„Brief na info@firma.cz, nabízíme Bioptron MedAll"* → `product = "bioptron-medall"`
- *„Připrav brief, prodáváme AI Akcelerátor"* → `product = "ai-akcelerator"`

**Mapování na slug:** porovnej extrahované jméno se slugy v `/documents/brand/products/`. Použij case-insensitive substring match (lichý slug `bioptron-medall` matchuje text „Bioptron", „Bioptron MedAll", „bioptron medall").

Pokud match nejednoznačný (text „Bioptron" matchuje slugy `bioptron`, `bioptron-medall`, `bioptron-light` současně), vyber **nejdelší slug** (typicky nejspecifičtější).

Pokud match není žádný, ale fráze „pro/nabízíme/prodáváme" v textu je, → **`product_mode = "multi"`** s upozorněním do .scout-history.jsonl: *„extrahovaný produkt nematchoval žádný slug, použit multi-product režim".*

## Krok 5 — Fit posouzení (per produkt)

### Algoritmus fit grade

Pro každý produkt v scope (single nebo multi) Scout porovná:

| Dimenze | Z Product DNA „Ideální klient" | Z firmy (Krok 2–4) | Váha |
|---|---|---|---|
| **Sektor / branže** | např. „estetika, wellness, fyzioterapie" | sektor z ARES + popis z webu | 30 % |
| **Velikost firmy** | např. „1–10 zaměstnanců" | velikost z ARES + LinkedIn | 20 % |
| **Region** | např. „ČR + SK" | sídlo z ARES | 15 % |
| **Segment B2B/B2C** | např. „B2B (kliniky)" | typ klientů z webu | 15 % |
| **Behaviorální signály** | např. „expanze, nábor, prémiový pricing" | signály zájmu z News, ceník z webu | 20 % |

### Skóre → grade

- **A (velmi dobrý fit)** — všechny povinné dimenze splněny, plus aspoň 1 silný signál zájmu
- **B (dobrý fit)** — povinné dimenze splněny, ale bez silných signálů
- **C (okrajový fit)** — některé povinné dimenze chybí, ale produkt by mohl být užitečný; ne primární priorita

### Vyřazovací (disqualifiers)

Pokud firma odpovídá vyloučení v Product DNA „Ideální klient → Disqualifiers" (např. konkurence, branže mimo segment, příliš malí / příliš velcí), Scout produkt **vyloučí** z fit posouzení — neobjeví se v briefu.

## Multi-product strategie

### Když 2+ produktů a žádný nebyl v promptu

1. Spočítej fit pro **všechny** Product DNA v adresáři
2. Seřaď podle gradu: A > B > C
3. Vyber **top 1–3 produkty** podle pravidla:
   - Pokud aspoň 1 produkt má fit A → vrať všechny s gradem A (max 3)
   - Pokud žádný A, ale aspoň 1 B → vrať top 3 B
   - Pokud žádný A ani B → vrať top 1 C (signál uživateli: žádný silný fit)
4. **Per-produkt sekce** (2, 6, 7, 8, 9, 10) v briefu vyrobí jen pro vybrané top 1–3

### Layout briefu v multi-product režimu

Společné sekce (1, 3, 4, 5, 11) jsou **jednou**. Per-produkt sekce (2, 6–10) se opakují:

```markdown
## 📋 Základní údaje                  ← společná, 1×

## 🎯 Shrnutí fitu pro Bioptron       ← per produkt, top 1
## 🎯 Shrnutí fitu pro AI Akcelerátor ← per produkt, top 2

## 🚀 Relevantní signály               ← společná, 1×
## 💡 Pravděpodobné potřeby            ← společná, 1×
## ⚠️ Rizika a námitky                 ← společná, 1×

## 🎯 Doporučený sales úhel pro Bioptron       ← per produkt
## 🎯 Doporučený sales úhel pro AI Akcelerátor ← per produkt

## 🎬 Next-best-action pro Bioptron       ← per produkt
## 🎬 Next-best-action pro AI Akcelerátor ← per produkt

## ✉️ E-mail pro Bioptron                 ← per produkt
## ✉️ E-mail pro AI Akcelerátor           ← per produkt

## 📞 Call opener pro Bioptron            ← per produkt
## 📞 Call opener pro AI Akcelerátor      ← per produkt

## ❓ Kvalifikační otázky pro Bioptron    ← per produkt
## ❓ Kvalifikační otázky pro AI Akcelerátor ← per produkt

## 🗂️ Doporučený další krok v CRM         ← společná, vychází z top fit produktu
```

## Příklady

### Příklad 1 — webhook s produktem

**Vstup:**
> *„Scout brief, contactId=abc123, jméno=Marek Novák, email=marek@effectclinic.cz, firma=Effect Clinic, product=bioptron-medall"*

**Krok 0.5:**
- `product=bioptron-medall` → `product_mode = "single"`, produkt = `bioptron-medall`
- Načti `/documents/brand/products/bioptron-medall/productDNA.md`

**Brief:**
- Sekce 2 jednou: „🎯 Shrnutí fitu pro Bioptron MedAll: A"
- Sekce 6–10 jednou: per Bioptron MedAll

### Příklad 2 — manuální bez produktu, máte 3 Product DNA

**Vstup:**
> *„Scout brief na Effect Clinic"*

**Krok 0.5:**
- Žádný `product=` v promptu
- `ls /documents/brand/products/` → 3 produkty: `bioptron-medall`, `ai-akcelerator`, `live100-vitaminy`
- → `product_mode = "multi"`

**Krok 5 (fit posouzení):**
- Bioptron MedAll → fit A (klinika, estetika, pasuje na ideálního klienta)
- AI Akcelerátor → fit B (firma 7 zaměstnanců, mohla by mít užitek)
- Live100 vitamíny → fit C (re-seller scenarie není primary fit)

**Vybráno:** top 1 s A → Bioptron MedAll, dále B → AI Akcelerátor. Live100 vynechán (C, ne primary).

**Brief:**
- Sekce 2 dvakrát: pro Bioptron + AI Akcelerátor
- Sekce 6–10 dvakrát: pro Bioptron + AI Akcelerátor

### Příklad 3 — manuální bez produktu, máte 1 Product DNA

**Vstup:**
> *„Scout brief na Effect Clinic"*

**Krok 0.5:**
- Žádný `product=` v promptu
- `ls /documents/brand/products/` → 1 produkt: `bioptron-medall`
- → `product_mode = "single"`, produkt = `bioptron-medall` (jediný možný)

**Brief:** stejný jako příklad 1.

### Příklad 4 — manuální bez produktu, žádný Product DNA

**Vstup:**
> *„Scout brief na Effect Clinic"*

**Krok 0.5:**
- Žádný `product=` v promptu
- `ls /documents/brand/products/` → 0 produktů
- → **exit kód 4** + chybová zpráva v stderr: *„Žádný Product DNA v /documents/brand/products/. Sales Scout potřebuje aspoň jeden Product DNA pro fit posouzení. Vytvoř ho přes product-dna-generator skill."*

Skill skončí, žádný brief se nevyrobí, žádný řádek do .scout-history.jsonl.
