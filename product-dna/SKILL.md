---
name: product-dna
description: "Vytvořte kompletní zprávu o DNA produktu zahrnující umístění, výhody, dodávky, ceny, námitky, důkazy, spouštěče a shrnutí."
category: marketing
status: ready
version: "1.0"
publishedAt: "2026-04-25"
---
# DNA produktu — Prodejní profil produktu

Uživatel přiloží podklady o produktu/službě. Agent analyzuje vše a vytvoří kompletní Product DNA Report.

---

## Vstup

Uživatel přiloží podklady o produktu. Čím více podkladů, tím přesnější výstup.

**Povinné podklady (alespoň jeden):**
- Popis produktu/služby — co to je, co to dělá, jak to funguje
- Cílová skupina — kdo je ideální zákazník
- Cenová struktura — kolik to stojí, jaké jsou varianty

**Doporučené podklady (posílí výsledek):**
- Prodejní stránka / webový produkt (URL nebo text)
- Prezentace, brožury, emaily o produktu
- Reference a případové studie
- FAQ / nejběžnější námitky
- Existující brandDNA (pro jaký tón)

Pokud uživatel nepřiloží žádné podklady, agent se zeptá na základní informace: co produkt dělá, pro koho je, kolik stojí.

---

## Workflow

### Krok 1: Načti kontext
1. Pokud existuje `/documents/brand/brandDNA.md` → načti ho pro druh tónu
2. Analyzujte všechny přiložené podklady

### Krok 2: Vytvoř report
Napiš kompletní Product DNA Report podle formátu níže. Vycházej VÝHRADNĚ z přiložených podkladů — nic si nevymýšlej.

### Krok 3: Ulož
Ulož výstup jako: `/documents/brand/products/{product-slug}/productDNA.md`

---

## Role

Vystupuj jako zkušený produktový stratég a obchodní architekt. Tvůj úkol je zachytit prodejní pravdu produktu — tak, aby každý, kdo si přečte DNA produktu, okamžitě pochopil co produkt dělá, proč na něm záleží a proč koupit teď.

---

## Pravidla

- Piš konkrétně — čísla, výsledky, mechanismy. Žádné vágní sliby.
- Každý benefit musí odpovědět: "A co z toho má klient?"
- Námitky řeš přímo — ne obranně, ale s důkazem.
- Piš lidsky, přímo, bez korporátních frází.
- Vyhni se klišé a prázdným superlativům.
- Vycházej VÝHRADNĚ z přiložených podkladů — nic si nevymýšlej.
- Pokud informace v podkladech není, nefabuluj — zapiš do sekce CHYBĚJÍCÍ INFORMACE.

---

## Formát zprávy

```markdown
# PRODUCT DNA: [Název produktu]

---

## 1. ESENCE PRODUKTU

- **Název:** [název produktu/služby]
- **Kategorie:** [typ produktu — kurz / SaaS / služba / fyzický produkt / ...]
- **Jednořádkový popis:** [max 15 slov — co to je a co to dělá]
- **Slogan:** [emoční zkratka, ne popis funkce]
- **USP:** [Co děláme jinak] + [Jak] + [Výsledek] — jedna věta
- **Transformace PŘED → PO:**
  - Vnější změna: [co se konkrétně změní v životě/byznysu klienta]
  - Vnitřní změna: [jak se klient cítí po transformaci]

---

## 2. PRO KOHO TO JE (A PRO KOHO NE)

**Ideální zákazník:**
- Pozice / role: [kdo to je]
- Firma / situace: [v jakém kontextu se nachází]
- Spouštěč nákupu: [co se musí stát, aby začal hledat řešení]
- Pocit při prvním kontaktu: [co si myslí když poprvé narazí na produkt]

**Anti-persona (pro koho to NENÍ):**
- [Kdo z produktu nebude mít užitek a proč]

---

## 3. HLAVNÍ BENEFITY

### Benefit 1: [Název]
- **Mechanismus:** [co to konkrétně dělá]
- **Výsledek:** [co z toho klient má — měřitelně]
- **Emoce:** [jak se díky tomu cítí]

### Benefit 2: [Název]
...

### Benefit 3: [Název]
...

(3-5 benefitů, seřazených od nejsilnějšího)

---

## 4. CO PŘESNĚ KLIENT DOSTANE

- **Výčet dodávaného:** [kompletní seznam — co všechno je v ceně]
- **Formát dodání:** [online / osobně / kombinace / ...]
- **Časový rámec:** [kdy může očekávat první výsledky]
- **Co se od klienta očekává:** [jaký je jeho podíl na úspěchu]

---

## 5. CENOVÁ STRUKTURA

**Varianty / balíčky:**
| Balíček | Cena | Co obsahuje |
|---------|------|------------|
| [název] | [cena] | [stručný popis] |
| ... | ... | ... |

**Cenová kotva:** [Kolik by klienta stálo řešit tento problém bez produktu — čas, peníze, ztracené příležitosti]

**Garance / snížení rizika:** [Jakou garanci nabízíme — vrácení peněz, trial, ...]

---

## 6. NEJČASTĚJŠÍ NÁMITKY

### Námitka 1: „[Tak jak ji klient řekne]"
- **Přerámování:** [jak na ni odpovědět]
- **Důkaz:** [konkrétní příklad nebo číslo]

### Námitka 2: „[...]"
...

(5-7 námitek)

---

## 7. SOCIÁLNÍ DŮKAZ A VÝSLEDKY

**Konkrétní čísla a metriky:**
- [metrika 1]
- [metrika 2]

**Případové studie:**

### [Jméno / Firma]
- **Situace:** [kde byli]
- **Řešení:** [co udělali]
- **Výsledek:** [co se změnilo — konkrétně]

**Použitelné typy důkazů v marketingu:**
- [jaké typy důkazů máme k dispozici — čísla, reference, certifikace, média, ...]

---

## 8. PRODEJNÍ SPOUŠTĚČE

- **Naléhavost (proč teď):** [proč by měl klient jednat hned, ne za měsíc]
- **Vzácnost (co je omezené):** [limitovaná místa, čas, bonusy]
- **Bonusy (co dostane navíc):** [co je nad rámec základní nabídky]
- **Odstranění rizika:** [garance, trial, podmínky vrácení]

---

## 9. SHRNUTÍ PRODUCT DNA

[Jeden odstavec — esence nabídky, pro koho, proč, jaký výsledek. Elevator pitch celého produktu.]

---

## CHYBĚJÍCÍ INFORMACE

[Seznam toho, co v podkladech chybělo a co by Product DNA posílilo. Pokud nechybí nic, napiš: „Podklady byly kompletní."]
```

---

## Iterace

Po prvním výstupu uživatel může požádat o úpravy:
- "Změň USP — chci zdůraznit úsporu času, ne peněz."
- "Přidej námitku o bezpečí dat."
- „Benefit 2 není dost silný — přepiš ho z pohledu majitele e-shopu.“
- "Zkrátit shrnutí na 3 věty."

Při úpravě jedné sekce NIKDY neměň ostatní sekce.

---

## Jak se Produkt DNA používá dál

Product DNA je podklad pro celý marketingový ekosystém. Ostatní dovednosti (článek, email, sociální sítě, webinář) z ní čerpají:
- **Copywriting** — tón, argumentace, USP, benefity
- **Prodej** — hotové odpovědi na námitky, cenová kotva
- **Strategie** — kampaně založené na USP a spouštěcích
- **Zavádění** — nový člen týmu pochopí produkt za 5 minut

DNA značky = KDO jste (hodnoty, tóny, emoce, vizuální identita).
Produkt DNA = CO prodáváte (benefity, cena, námitky, důkazy).

Značka DNA je jedna pro celou firmu. Produkt DNA se vytváří pro každý produkt zvlášť.
