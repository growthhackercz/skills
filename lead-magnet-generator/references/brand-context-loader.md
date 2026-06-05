# Načtení brandu a produktu

Jak skill čte Brand DNA a Product DNA reporty před výběrem typu magnetu. **Reporty jsou markdown soubory bez YAML frontmatteru** — generuje je `brand-dna` a `product-dna` skill. Skill musí extrahovat informace z konkrétních markdown sekcí.

---

## Kde skill hledá

| Soubor | Cesta | Kdo ho generuje |
|--------|-------|------------------|
| Brand DNA | `/documents/brand/brandDNA.md` | skill `brand-dna` |
| Product DNA | `/documents/brand/products/[nazev-produktu]/productDNA.md` | skill `product-dna` |

**Důležité:**
- Brand DNA je **jeden** soubor pro celou firmu
- Product DNA je **per produkt** v subfolderu `/products/[slug]/`
- Jedna firma může mít více produktů → více `productDNA.md` souborů

---

## Workflow načítání

### 1. Identifikuj produkt

Pokud uživatel zmíní konkrétní produkt v zadání ("vytvoř magnet pro Money Reset"), použij jeho slug jako `[nazev-produktu]` (kebab-case).

Pokud uživatel nezmíní žádný konkrétní produkt:

- Zkus přečíst `/documents/brand/products/` — pokud existuje jeden subfolder, použij ho
- Pokud existuje více subfolderů, **zeptej se uživatele**:
  > *"Vidím, že máš ve své brandové knihovně více produktů: [seznam]. Pro který z nich má magnet vést? Pomůže mi to vybrat správný typ a tonalitu."*
- Pokud žádný produkt není definovaný, **zeptej se na produkt** (krok 3 níže)

### 2. Načti soubory

```
1. Přečti /documents/brand/brandDNA.md
2. Přečti /documents/brand/products/[nazev-produktu]/productDNA.md
```

Pokud oba existují → pokračuj na Krok 1 workflow (jedna lidská otázka uživateli).

### 3. Pokud chybí brandDNA.md

**Neptej se sám** — pošli uživatele na skill `brand-dna`:

> *"Pro vytvoření magnetu potřebuju nejdřív vědět, jak tvoje značka mluví a komu pomáhá. Pusť skill `brand-dna`, ten ti vytvoří kompletní Brand DNA report. Pak se vrať a pokračujeme."*

Pokud uživatel chce pokračovat bez Brand DNA (rychlá varianta), polož **jednoduché lidské otázky** v jedné dávce a vytvoř minimalistický `brandDNA.md`:

> *"OK, můžeme to udělat zkráceně. Řekni mi:*
> 1. *Kdo jsi a co děláš (jednou větou)*
> 2. *Komu pomáháš (popis ideálního klienta)*
> 3. *Co tě dělá jiným než konkurence*
> 4. *Jakou má značka tonalitu (formálně / neformálně / odborně / přátelsky / drsně…)*
> 5. *Jak velká je značka (začátek / děláš to chvíli / autorita v oboru)"*

Z odpovědí vytvoř `brandDNA.md` v zjednodušené struktuře (kompatibilní s plným formátem brand-dna skillu).

### 4. Pokud chybí productDNA.md

Stejný princip — pošli na skill `product-dna`:

> *"Magnet má vést k některému tvému placenému produktu. Pusť skill `product-dna` pro [název produktu], ten ti vytvoří Product DNA report. Pak se vrať."*

Pokud uživatel chce zkráceně, polož:

> *"OK, řekni mi o produktu:*
> 1. *Jak se jmenuje a co je to za formát (kurz / služba / SaaS / coaching…)*
> 2. *Kolik stojí*
> 3. *Jakou změnu klient zažije (z čeho na co)*
> 4. *Jak rychle vidí výsledky*
> 5. *Máš pojmenovaný systém / metodu? Jaké má kroky?*
> 6. *Jaká je hlavní bolest klienta před nákupem*
> 7. *3 nejčastější námitky"*

Vytvoř `/documents/brand/products/[nazev-produktu]/productDNA.md` v zjednodušené struktuře.

---

## Mapování markdown sekcí → interní hodnoty

Skill potřebuje 5 dimenzí pro výběr typu magnetu (Krok 2). Tyto se extrahují z markdown sekcí brand-dna a product-dna reportů:

### Z Brand DNA reportu

| Co skill potřebuje | Kde to v Brand DNA je | Jak extrahovat |
|---------------------|------------------------|----------------|
| **Hlas** (tón komunikace) | Sekce `## 5. HLAS ZNAČKY` → pole "Tón" | Přímý text |
| **Slovník značky** (slova, která používat) | Sekce `## 5. HLAS ZNAČKY` → pole "Slova, která značku definují" | Seznam |
| **Slova, kterým se vyhýbat** | Sekce `## 5. HLAS ZNAČKY` → pole "Slova, kterým se značka vyhýbá" | Seznam |
| **Ukázkové věty (pro vzor)** | Sekce `## 5. HLAS ZNAČKY` → pole "Ukázkové věty" | Vzor pro každou větu obsahu |
| **Popis ideálního klienta** | Sekce `## 2. IDEÁLNÍ ZÁKAZNÍK` → pole "Kdo je" | Pro segmentaci publika |
| **Hlavní bolest publika** | Sekce `## 2. IDEÁLNÍ ZÁKAZNÍK` → pole "Co ho trápí" | Pro pain matching |
| **Co publikum hledá** | Sekce `## 2. IDEÁLNÍ ZÁKAZNÍK` → pole "Co hledá" | Pro detekci "co publikum ví o problému" |
| **Příběh zakladatele** | Sekce `## 3. PŘÍBĚH ZAKLADATELE` | Pro závěrečnou kapitolu lidského příběhu |
| **Esence + slogan** | Sekce `## 1. ESENCE ZNAČKY` | Pro názvy magnetu (souznění s brandem) |
| **Velikost značky** | Sekce `## 7. SHRNUTÍ BRAND DNA` + nepřímé signály | Heuristika (viz níže) |

### Z Product DNA reportu

| Co skill potřebuje | Kde to v Product DNA je | Jak extrahovat |
|---------------------|--------------------------|----------------|
| **Název produktu** | Sekce `## 1. ESENCE PRODUKTU` → "Název" | Přímý text |
| **Formát produktu** | Sekce `## 1. ESENCE PRODUKTU` → "Kategorie" | kurz / SaaS / coaching / služba… |
| **USP** | Sekce `## 1. ESENCE PRODUKTU` → "USP" | Pro pozvání ke koupi |
| **Transformace z → na** | Sekce `## 1. ESENCE PRODUKTU` → "Transformace PŘED → PO" | Pro názvy + závěrečnou nabídku |
| **Cena (highest tier)** | Sekce `## 5. CENOVÁ STRUKTURA` → tabulka balíčků | Vezmi nejvyšší cenu pro mapování na cena_tier |
| **Časový rámec** | Sekce `## 4. CO PŘESNĚ KLIENT DOSTANE` → "Časový rámec" | Pro názvy ("za 30 dní…") |
| **Hlavní benefity** | Sekce `## 3. HLAVNÍ BENEFITY` → 3-5 benefitů s mechanismy | Pro odrážky landing page |
| **Námitky** | Sekce `## 6. NEJČASTĚJŠÍ NÁMITKY` | Pro pre-empting v obsahu |
| **Sociální důkaz** | Sekce `## 7. SOCIÁLNÍ DŮKAZ A VÝSLEDKY` | Pro citace v obsahu |
| **Spouštěče (urgence, bonusy)** | Sekce `## 8. PRODEJNÍ SPOUŠTĚČE` | Pro děkovací stránku |
| **Mechanismus + kroky** | Odvodit z benefitů (každý má "Mechanismus") nebo z USP | Pro strukturu kapitol |
| **Pain typ** | Odvodit z benefitů a transformace | Heuristika (viz níže) |

---

## Heuristiky pro odvození chybějících údajů

### Velikost značky (start / etablovaná / autorita)

Brand DNA report nemá explicitní pole "stage". Skill odhadne:

| Signál v Brand DNA | Velikost |
|---------------------|----------|
| "Začínám", "nový brand", "první rok", "buduju publikum" | start |
| "Pár let v oboru", "200 klientů", "5 000 followerů", konkrétní výsledky bez velkých čísel | etablovaná |
| "Expert v oboru", "10 000+ followerů", "mediální zmínky", "best-selling autor" | autorita |
| Příběh zakladatele zmínuje konkrétní úspěchy, knížky, podcasty | etablovaná až autorita |

**Pokud nelze odhadnout** → polož uživateli lidskou otázku:

> *"Jak dlouho už máš svoji značku a kolik máš zhruba sledujících na sociálních sítích nebo v newsletteru? Pomůže mi to vybrat správný typ magnetu."*

### Co publikum ví o problému

Z Brand DNA sekce `## 2. IDEÁLNÍ ZÁKAZNÍK` pole "Co hledá":

| Pole "Co hledá" zní jako | Co publikum ví |
|---------------------------|----------------|
| "Neví ještě, co potřebuje", "vágní nespokojenost", "tuší něco není OK" | nikdy_neslyseli |
| "Hledá řešení svého problému", "ví, že má X, hledá pomoc" | vedi_ze_ho_maji |
| "Porovnává nabídky", "ví, jaké jsou typy řešení, vybírá" | znaji_typy_reseni |
| "Zná tě/produkt, váhá s nákupem" | znaji_tvuj_produkt |

**Pokud nelze odhadnout** → polož:

> *"Tvoji čtenáři už ten problém znají a vědí, že ho mají? Nebo o něm třeba ještě nepřemýšleli a magnet je má 'probudit'?"*

### Cena tier

Z Product DNA `## 5. CENOVÁ STRUKTURA` tabulky balíčků extrahuj nejvyšší cenu:

| Nejvyšší cena | Tier |
|----------------|------|
| < 2 500 Kč | low |
| 2 500 – 25 000 Kč | mid |
| > 25 000 Kč | high |

### Pain typ

Pain typ není v reportu explicitně. Skill odvodí z benefitů a transformace:

| Signály v benefitech / transformaci | Pain typ |
|--------------------------------------|----------|
| "Ušetříš čas", "automatizuje opakující se úkol" | repetitive |
| "8týdenní program", "kompletní změna identity", "transformace" | transformacni |
| "Hotové scripty", "co říct kdy" | konverzacni |
| "Audit", "diagnóza", "kde stojím" | diagnosticky |
| "Spočítej", "kolik to bude" | datovy |
| "Kde začít", "first 7 dní", "starter pack" | onboarding |
| "Co volit", "porovnání", "rozhodni se" | rozhodovaci |
| "Příklady", "swipe", "inspirace" | inspirace |
| "Případové studie", "důkaz funguje" | dukazni |
| "Co dělat", "checklist", "kroky" | akcni |
| "Pochopit proč", "kontext", "vysvětlení" | kognitivni |

**Pokud nelze jednoznačně odhadnout** → default `kognitivni` + lidská otázka:

> *"Tvoji čtenáři spíš potřebují pomoct UDĚLAT něco konkrétního, nebo pomoct POCHOPIT, jak něco funguje?"*

---

## Aplikace v dalších krocích

### Hlas a slovník

Z Brand DNA `## 5. HLAS ZNAČKY`:
- Slova z "Slova, která značku definují" → použij přesně ve všech generovaných textech
- Slova z "Slova, kterým se značka vyhýbá" → vyhni se jim
- "Ukázkové věty" → vzor pro tonalitu každé věty

### Citáty autora

Z Brand DNA `## 3. PŘÍBĚH ZAKLADATELE` nebo `## 1. ESENCE ZNAČKY` (slogan, USP). Pokud potřebuješ citát a v reportu konkrétní citát není, vytvoř plausible v duchu značky a označ `[OVĚŘ U AUTORA]`.

### Kapitoly = mechanismus produktu

Pokud Product DNA `## 3. HLAVNÍ BENEFITY` má 3-5 benefitů s pojmenovaným mechanismem (každý benefit má "Mechanismus" pole), mohou tvořit strukturu kapitol pro:
- Mini-průvodce (3-5 kapitol = 3-5 benefitů)
- Workbook (kapitola per benefit)
- Mini-kurz (lekce per benefit)

Checklist a taháček mechanismus nepoužijí — vyberou 1 benefit a udělají z něj akční seznam.

Audit vytvoří diagnostické otázky pro každý benefit.

### Pozvání ke koupi (závěr magnetu + děkovací stránka)

Z Product DNA použij:
- `## 1. ESENCE PRODUKTU` → název, USP
- `## 5. CENOVÁ STRUKTURA` → cena + cenová kotva
- `## 8. PRODEJNÍ SPOUŠTĚČE` → urgence, vzácnost, bonusy, garance
- `## 7. SOCIÁLNÍ DŮKAZ A VÝSLEDKY` → konkrétní čísla a citace klientů

---

## Důležité: žádný YAML frontmatter

Brand DNA a Product DNA reporty **nemají YAML frontmatter** — jsou to čisté markdown reporty se sekcemi. Skill nesmí předpokládat nebo generovat YAML.

Pokud skill potřebuje strukturovaná data (např. pro generování v dalších krocích), uloží si je do **vlastního souboru** v `/documents/lead-magnets/[slug]/00-strategie.md` — ne do brand/product DNA souborů.
