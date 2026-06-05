# Výběr 3–5 typů magnetu (interní logika)

Jak skill **sám** vybere 3–5 nejlepších typů magnetu z katalogu 14 — **bez dotazů na marketingové pojmy**, kterým zakladatel firmy nemusí rozumět.

Tato reference je interní (pro skill, ne pro uživatele). Skill používá pojmy jako "fáze rozhodování" a "co publikum ví o problému" interně, ale **navenek mluví lidsky**.

---

## Auto-detection z Brand DNA + Product DNA + uživatelského zadání

V Kroku 2 potřebuje skill 5 dimenzí pro skórování. Místo otázek na ně, **odhadne z markdown reportů** vygenerovaných skilly `brand-dna` a `product-dna`.

### 1. Fáze rozhodování čtenáře (interně: funnel stage)

#### Hlavní zdroj: cena produktu z Product DNA

Z `## 5. CENOVÁ STRUKTURA` extrahuj **nejvyšší balíček** a převeď na tier:

| Cena nejvyššího balíčku | Tier | Default fáze rozhodování |
|--------------------------|------|---------------------------|
| < 2 500 Kč | low | **konec rozhodování** |
| 2 500 – 25 000 Kč | mid | **střed rozhodování** |
| > 25 000 Kč | high | **střed–začátek rozhodování** (high-ticket potřebuje budovat důvěru) |

#### Modifikátor: pain typ z Product DNA benefitů

Z `## 3. HLAVNÍ BENEFITY` (mechanismy + výsledky) odvoď, jestli je pain typ **transformační/diagnostický** (→ posuň ke středu) nebo **akční/repetitive/onboarding** (→ posuň ke konci).

#### Override z uživatelského zadání

V Kroku 1 uživatel napíše vlastními slovy, co chce, aby se po stažení stalo. Hledej signály:

| Slova v uživatelské odpovědi | Fáze |
|-------------------------------|------|
| "získat nové publikum", "lidi, kteří mě neznají", "rozšířit publikum" | začátek |
| "ohřát publikum", "připravit ke koupi", "demonstrovat expertízu", "budovat důvěru" | střed |
| "konvertovat", "převést na klienty", "zvýšit prodej", "ukázat blízko nákupu" | konec |

### 2. Co publikum ví o problému (interně: awareness level)

#### Hlavní zdroj: Brand DNA sekce 2

Z `## 2. IDEÁLNÍ ZÁKAZNÍK` pole "Co hledá":

| Text v poli "Co hledá" | Co publikum ví |
|--------------------------|----------------|
| "Vágní nespokojenost", "tuší něco není OK", "neví ještě, co potřebuje" | **nikdy neslyšeli** |
| "Hledá řešení svého problému", "ví že má problém X" | **vědí o problému** |
| "Porovnává nabídky", "vybírá mezi řešeními", "ví o typech řešení" | **znají typy řešení** |
| "Zná tě/produkt", "váhá s nákupem", "ověřuje si tvou autoritu" | **znají tvůj produkt** |

#### Pokud nelze z Brand DNA odhadnout

Polož **lidskou doplňující otázku**:

> *"Tvoji čtenáři už ten problém znají a vědí, že ho mají? Nebo o něm třeba ještě nepřemýšleli a magnet je má 'probudit'?"*

### 3. Velikost značky (interně: brand stage)

Brand DNA report nemá explicitní pole "stage". Skill odhadne z kontextu:

#### Signály z Brand DNA

| Signály v reportu | Velikost |
|--------------------|----------|
| Sekce 3 příběh: "začínám", "nový brand", "buduju první rok publikum" | start |
| Sekce 7 shrnutí: zmíněné konkrétní výsledky (200 klientů, 5k followerů, 2 roky v oboru) | etablovaná |
| Sekce 3 příběh: "10 let v oboru", "3 knihy", "média", "10k+ followerů" | autorita |
| Žádné konkrétní výsledky uvedené, ale tonalita autoritativní | etablovaná (default mid) |

#### Pokud nelze odhadnout

Polož:

> *"Jak dlouho už máš svoji značku a kolik máš zhruba sledujících na sociálních sítích nebo v newsletteru? Pomůže mi to vybrat správný typ magnetu."*

### 4. Kolik času je čtenář ochotný strávit (interně: time budget)

**Default 15 minut**. Override podle:

| Signál | Čas |
|--------|-----|
| Pain typ akční / repetitive (z Product DNA) | ≤5 min (rychlá výhra) |
| Pain typ kognitivní / transformační + cena mid/high | 20–30 min |
| Pain typ diagnostický | 10–15 min |
| Brand stage `autorita` + uživatel chce hloubku | 30–60 min |
| Uživatel zmíní v zadání "rychlý" / "krátký" | ≤10 min |

**Pokud je situace nejasná**, default 15 minut a v Kroku 2 nabídni mix (1 rychlý + 1 střední + 1 hlubší).

### 5. Typ bolesti (interně: pain type)

Pain typ není v Product DNA reportu jako explicitní pole. Skill odvodí z **benefitů a transformace**:

| Signály v Product DNA `## 3. HLAVNÍ BENEFITY` mechanismech / `## 1.` transformaci | Pain typ |
|------------------------------------------------------------------------------------|----------|
| "Ušetříš čas", "automatizuje opakující se úkol" | repetitive |
| "Kompletní změna", "transformace identity", "8týdenní program" | transformacni |
| "Hotové scripty", "co říct kdy", "konverzační scénáře" | konverzacni |
| "Audit", "diagnóza", "zjisti kde stojíš", "skóre" | diagnosticky |
| "Spočítej", "kolik to bude", "ROI" | datovy |
| "Kde začít", "first 7 days", "starter pack" | onboarding |
| "Co volit", "porovnání", "rozhodni se mezi A a B" | rozhodovaci |
| "Příklady", "swipe", "inspirace", "ready-made" | inspirace |
| "Případové studie", "důkaz funguje", "social proof" | dukazni |
| "Co dělat", "checklist", "step-by-step" | akcni |
| "Pochopit proč", "kontext", "vysvětlení", "framework" | kognitivni |

**Pokud nelze jednoznačně odhadnout** → default `kognitivni` + lidská otázka:

> *"Tvoji čtenáři spíš potřebují pomoct UDĚLAT něco konkrétního, nebo pomoct POCHOPIT, jak něco funguje?"*

---

## Skórovací matice

Pro každý ze 14 typů spočítej:

```
skóre = match_faze × 1.5
      + match_co_vedi × 1.5
      + match_pain × 2.0       ← nejdůležitější
      + match_brand × 1.0
      + match_cas × 1.0
      + match_bridge × 1.5
```

### Match fáze rozhodování

| Typ | Začátek | Střed | Konec |
|-----|---------|-------|-------|
| Checklist | 2 | 4 | 5 |
| Taháček (cheat sheet) | 4 | 4 | 3 |
| Šablona | 2 | 4 | 5 |
| Knihovna příkladů | 4 | 5 | 3 |
| Mini-průvodce | 5 | 4 | 2 |
| Workbook | 2 | 5 | 3 |
| Audit / Sebehodnocení | 4 | 5 | 3 |
| Quick-start průvodce | 2 | 4 | 5 |
| Srovnání A vs. B | 2 | 5 | 3 |
| Kalkulačka | 3 | 5 | 4 |
| Případová studie | 2 | 4 | 5 |
| Seznam zdrojů | 5 | 3 | 2 |
| Scripty | 1 | 3 | 5 |
| Mini-kurz | 4 | 4 | 2 |

### Match co publikum ví

| Typ | Nikdy neslyšeli | Vědí že ho mají | Znají typy řešení | Znají tvůj produkt |
|-----|-----------------|------------------|-------------------|---------------------|
| Checklist | 2 | 4 | 5 | 4 |
| Taháček | 3 | 5 | 4 | 3 |
| Šablona | 1 | 3 | 5 | 5 |
| Knihovna příkladů | 2 | 4 | 5 | 4 |
| Mini-průvodce | 4 | 5 | 4 | 3 |
| Workbook | 1 | 3 | 5 | 5 |
| Audit | 3 | 5 | 4 | 3 |
| Quick-start | 1 | 3 | 5 | 5 |
| Srovnání | 1 | 3 | 5 | 4 |
| Kalkulačka | 1 | 4 | 5 | 4 |
| Případová studie | 2 | 3 | 5 | 5 |
| Seznam zdrojů | 4 | 5 | 3 | 2 |
| Scripty | 1 | 2 | 5 | 5 |
| Mini-kurz | 4 | 5 | 4 | 3 |

### Match pain typ

Match je **5** pokud typ matchuje pain (`lead-magnet-types.md`), **1** pokud nesedí, mezilehlé jinak.

Hlavní párování:

| Pain typ | Top 3 magnety |
|----------|---------------|
| akcni | Checklist, Šablona, Quick-start |
| kognitivni | Mini-průvodce, Mini-kurz, Knihovna příkladů |
| diagnosticky | Audit, Kalkulačka, Srovnání |
| repetitive | Šablona, Scripty, Checklist |
| transformacni | Workbook, Mini-průvodce, Mini-kurz |
| inspirace | Knihovna příkladů, Seznam zdrojů |
| rozhodovaci | Srovnání, Kalkulačka, Případová studie |
| konverzacni | Scripty, Šablona |
| dukazni | Případová studie, Audit |
| onboarding | Quick-start, Checklist |
| datovy | Kalkulačka, Audit |

### Match velikost značky

| Typ | Start | Etablovaná | Autorita |
|-----|-------|------------|----------|
| Checklist | 5 | 5 | 4 |
| Taháček | 5 | 5 | 4 |
| Šablona | 4 | 5 | 5 |
| Knihovna příkladů | 1 | 4 | 5 |
| Mini-průvodce | 4 | 5 | 5 |
| Workbook | 1 | 4 | 5 |
| Audit | 3 | 5 | 5 |
| Quick-start | 4 | 5 | 4 |
| Srovnání | 4 | 5 | 4 |
| Kalkulačka | 3 | 5 | 4 |
| Případová studie | 1 | 4 | 5 |
| Seznam zdrojů | 5 | 5 | 3 |
| Scripty | 4 | 5 | 4 |
| Mini-kurz | 2 | 4 | 5 |

### Match čas

| Typ | ≤5 min | 10–15 min | 20–30 min | 60+ min |
|-----|--------|-----------|-----------|---------|
| Checklist | 5 | 4 | 1 | 1 |
| Taháček | 5 | 4 | 1 | 1 |
| Šablona | 3 | 5 | 4 | 2 |
| Knihovna příkladů | 2 | 5 | 5 | 3 |
| Mini-průvodce | 1 | 3 | 5 | 4 |
| Workbook | 1 | 1 | 3 | 5 |
| Audit | 3 | 5 | 4 | 2 |
| Quick-start | 1 | 3 | 5 | 4 |
| Srovnání | 5 | 4 | 2 | 1 |
| Kalkulačka | 5 | 4 | 2 | 1 |
| Případová studie | 2 | 5 | 4 | 2 |
| Seznam zdrojů | 4 | 5 | 3 | 1 |
| Scripty | 4 | 5 | 3 | 2 |
| Mini-kurz | 1 | 1 | 4 | 5 |

### Match bridge na placený produkt (cena tier)

| Cena | Top typy s nejsilnějším přemostěním |
|------|--------------------------------------|
| low | Checklist, Taháček, Šablona, Seznam zdrojů |
| mid | Mini-průvodce, Audit, Quick-start, Workbook, Srovnání |
| high | Případová studie, Audit, Workbook, Mini-kurz, Scripty |

---

## Pravidla pro výběr top 3–5

Po skórování:

### Pravidlo 1: Žádné 3× to samé

Top 3 musí být ze **3 různých kategorií**:

- **Akční** (checklist, šablona, scripty)
- **Vzdělávací** (mini-průvodce, mini-kurz, knihovna příkladů)
- **Diagnostická** (audit, srovnání, kalkulačka)
- **Reference** (taháček, seznam zdrojů)
- **Příběhová** (případová studie)
- **Transformační** (workbook)

Pokud jsou 3 nejvyšší skóre ze stejné kategorie → ponech #1, swap #2 a #3 za jiné kategorie z top 5.

### Pravidlo 2: Mix doby čtení

Top 3 musí obsahovat:
- Alespoň 1 rychlou variantu (≤10 min) — pro nízkou bariéru
- Alespoň 1 střední (15–30 min) — pro hodnotu, která stojí za e-mail

### Pravidlo 3: První varianta = "Doporučeno"

Top 1 podle skóre dostane label **"(Doporučeno)"** + 1 věta extra zdůvodnění proč právě ona oproti #2 a #3.

### Pravidlo 4: Žádná zakázaná kombinace

Pokud jsou splněna varovná kritéria z `lead-magnet-types.md` sekce "Anti-patterns", typ vyřaď z výběru:

- **Knihovna příkladů** pro start značku (bez archivu příkladů)
- **Případová studie** bez reálných dat (Product DNA `## 7. SOCIÁLNÍ DŮKAZ` je prázdný nebo "Podklady byly chybějící")
- **Workbook** pro start značku (bez sociálního důkazu pro 60min závazek)
- **Mini-kurz** pro publikum, které tě nezná
- **Kalkulačka jako PDF** pokud lze udělat web widget

---

## Worked example

### Vstupy

**`/documents/brand/brandDNA.md`** (markdown report z `brand-dna` skillu, zkráceno):

```markdown
# BRAND DNA: Money Reset

## 1. ESENCE ZNAČKY
- Název: Money Reset
- Slogan: "Peníze nejsou matematika, peníze jsou identita."
- USP: "Pracujeme s penězi přes identitu, ne přes Excel — výsledek je 6měsíční rezerva za 90 dní bez disciplíny."

## 2. IDEÁLNÍ ZÁKAZNÍK
- Kdo je: Ženy freelancerky 28-42 let, příjem 40-100k Kč
- Co hledá: Hledá řešení svého chaotického vztahu k penězům — ví, že má problém, ale standardní rady o rozpočtech nefungují
- Co ho trápí: Chronický cash-flow chaos. "Jsem dobrá ve své práci, ale s penězi pořád v háji."

## 3. PŘÍBĚH ZAKLADATELE
Petra Nováková, certifikovaná financial coach. 5 let v oboru, 200+ klientek prošlo programem. Vlastní podcast s 50+ epizodami. Newsletter s 5 000 odběrateli.

## 5. HLAS ZNAČKY
- Tón: Empatický, ale konfrontační. Příběhy klientek.
- Slova, která značku definují: "vztah s penězi", "vědomé utrácení", "peněžní identita", "detoxikace přesvědčení"
- Slova, kterým se značka vyhýbá: "rozpočet", "spoření", "disciplína", "finanční gramotnost"
```

**`/documents/brand/products/money-reset/productDNA.md`** (zkráceno):

```markdown
# PRODUCT DNA: Money Reset

## 1. ESENCE PRODUKTU
- Název: Money Reset
- Kategorie: 8týdenní skupinový program (kurz + 1:1 sessions)
- USP: "Detoxikace přesvědčení místo rozpočtových tabulek — ty, které prošly, mají 6měsíční rezervu za 90 dní."
- Transformace PŘED → PO:
  - Vnější změna: chaos, dluhy, neotevírané faktury → 6měsíční rezerva, jistota, první investice
  - Vnitřní změna: stud a vyhýbání → klid a vědomé rozhodování

## 3. HLAVNÍ BENEFITY
### Benefit 1: Identifikace peněžního typu
- Mechanismus: Diagnostický audit pojmenuje 1 ze 4 typů (Avoider, Worrier, Spender, Monk)
- Výsledek: Klientka pochopí, že její chaos není o IQ, ale o programu z dětství
- Emoce: úleva, pochopení sebe sama

### Benefit 2: Detoxikace blokujících přesvědčení
- Mechanismus: 14denní cvičení, která systematicky přepíší top 2 nejdražší přesvědčení
- Výsledek: Sníží automatické "na to nemám" reakce o 70%
- Emoce: svoboda

### Benefit 3: Architektura 4účtového systému
...

## 5. CENOVÁ STRUKTURA
| Balíček | Cena | Co obsahuje |
|---------|------|------------|
| Money Reset Group | 29 800 Kč | 8 týdnů skupinového programu + 1 1:1 session |
| Money Reset 1:1 | 49 800 Kč | Plně 1:1 verze |

## 7. SOCIÁLNÍ DŮKAZ A VÝSLEDKY
- 200+ klientek prošlo programem
- 87% má po 90 dnech alespoň 1měsíční rezervu
- Případová studie: Marie K. — z -8 400 Kč na 80 000 Kč rezervě za 6 měsíců
```

**Uživatelské zadání:** *"Chci, aby čtenářka pochopila, že její finanční chaos není matematický problém, ale identitní."*

### Auto-detect (interní)

| Dimenze | Hodnota | Zdroj |
|---------|---------|-------|
| Fáze rozhodování | **střed** | Cena 29 800 Kč = mid + transformační pain (z benefitů "8týdenní program", "transformace") |
| Co publikum ví | **vědí o problému** | Brand DNA sekce 2 "Co hledá": "Hledá řešení svého chaotického vztahu" |
| Velikost značky | **etablovaná** | Brand DNA sekce 3: "200+ klientek, 5 000 odběratelů, 50+ podcastových epizod" |
| Čas | **15–30 min** | mid cena + transformační pain → spíš hloubka, default 15 |
| Pain typ | **transformacni** | Benefit 2 "detoxikace přesvědčení", transformace "stud → klid", 8týdenní program |
| Bridge | **mid** | Cena 29 800 Kč |

### Skórování (top 5)

| Typ | Faze × 1.5 | Vědí × 1.5 | Pain × 2.0 | Brand × 1.0 | Čas × 1.0 | Bridge × 1.5 | TOTAL |
|-----|------------|-------------|------------|-------------|-----------|--------------|-------|
| Audit | 5 × 1.5 = 7.5 | 5 × 1.5 = 7.5 | 5 × 2 = 10 | 5 | 5 | 4 × 1.5 = 6 | **41** |
| Mini-průvodce | 4 × 1.5 = 6 | 5 × 1.5 = 7.5 | 4 × 2 = 8 | 5 | 5 | 5 × 1.5 = 7.5 | **39** |
| Workbook | 5 × 1.5 = 7.5 | 3 × 1.5 = 4.5 | 5 × 2 = 10 | 4 | 3 | 5 × 1.5 = 7.5 | **36.5** |
| Taháček | 4 × 1.5 = 6 | 5 × 1.5 = 7.5 | 3 × 2 = 6 | 5 | 4 | 3 × 1.5 = 4.5 | **33** |
| Případová studie | 4 × 1.5 = 6 | 3 × 1.5 = 4.5 | 4 × 2 = 8 | 4 | 4 | 4 × 1.5 = 6 | **32.5** |

### Pravidla aplikovaná

- Diversity: Audit (diagnostická), Mini-průvodce (vzdělávací), Workbook (transformační), Taháček (reference) — top 4 ze 4 kategorií ✓
- Mix času: Taháček 5min ✓, Audit 15min ✓, Workbook 60min — vyšší bariéra, ale jako #4 alternativa OK
- Anti-pattern: Workbook OK pro etablovanou značku (Brand DNA sekce 3 ukazuje 200+ klientek = sociální důkaz)
- Případová studie OK — Product DNA sekce 7 obsahuje konkrétní data

### Final 3 doporučení

1. **Audit (Doporučeno)** — match 41, dá čtenářce zrcadlo + segmentuje publikum k programu
2. **Mini-průvodce** — match 39, plné edukační rozkrytí pro hluboký trust
3. **Taháček** — match 33, rychlá výhra pro testování širšího publika

---

## Edge cases

### Brand `start` (mladá značka, Brand DNA neukazuje výsledky)

Vyřaď: Workbook, Případová studie, Mini-kurz, Knihovna příkladů.
Doporučuj: Checklist, Taháček, Šablona, Seznam zdrojů, Quick-start.

### High-ticket produkt (>25 000 Kč)

Bridge musí být silný. Doporučuj: Audit (segmentuje hot leady), Případová studie, Workbook, Mini-kurz.

### Publikum nikdy neslyšelo o problému

Vyřaď: Šablona, Workbook, Scripty (předpokládají vědomí typů řešení).
Doporučuj: Mini-průvodce, Taháček, Seznam zdrojů, Mini-kurz.

### Velmi krátký čas (≤3 min)

Jediné kandidáti: Checklist, Taháček, Srovnání, Kalkulačka. Vyžaduje **velmi specifický** problém.

### Konflikt — uživatel chce konec rozhodování + publikum nezná problém

Polož doplňující otázku v lidské řeči:

> *"Pro získání lidí blízko nákupu obvykle potřebuju publikum, které tě už zná. Tvoje publikum tě ještě moc nezná — chceš spíš magnet, který je nejdřív 'probudí' k problému, a teprve pak bychom udělali další pro koupi?"*

### Product DNA má prázdné `## 7. SOCIÁLNÍ DŮKAZ`

Vyřaď Případovou studii z výběru — bez reálných dat by ji bylo problematické vytvořit.

### Brand DNA má v sekci 5 `## 5. HLAS ZNAČKY` velmi formální tonalitu

Skill ji použije pro generaci. Stage estimate posuň směrem k **autorita** (formálnost často signalizuje B2B nebo enterprise).
