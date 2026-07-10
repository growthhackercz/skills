---
name: ultimate-webinar
description: "Vytvářejte kompletní skripty webinářů s obsahem snímků a poznámkami řečníka pomocí osvědčených rámců webinářů a prodejních prezentací."
category: content
status: ready
version: "1.0"
publishedAt: "2026-04-25"
---
# Ultimate Webinar Script Generator

Skill pro tvorbu kompletních webinar scriptů se slidy a speaker notes.
Optimalizovaný pro business, AI a prodejní webináře.

## Co tento skill vytváří

Textový výstup ve formátu Markdown obsahující:
- Obsah každého snímku (nadpis, bullet pointy, tabulky, citáty)
- Poznámky pro speakera ke každému snímku (co říct a jak)
- Časový rozvrh celého webináře

## Tři frameworky v jednom

Tento skill stojí na třech ověřených systémech. Pochopení jejich principů je
klíčové pro kvalitní výstup:

### Hormozi — Prodejní psychologie
- **Deklarativní vs. procedurální**: Uč O ČEM a PROČ (zdarma). Nikdy neuč JAK krok za krokem (to je produkt). Dávej WOW momenty, ne to-do listy.
- **Deprivace**: Prodávej v bodě největší deprivace, bez hodnoty. Buduj vnímanou propast mezi „kde jsou" a „kde mohou být" celým programem.
- **Rychlost**: Malá okamžitá odměna překoná velký vzdálený výsledek.
- **Důkazy průběžně**: Případové studie, čísla, kontrasty prolínaj celým skriptem — jen v jedné sekci.

### Penberthy — Třífázová struktura
- Fáze 1: Hook + zobrazené porozumění + autorita (10 min)
- Fáze 2: Tři tajemství / trénink s WOW momenty (30 min)
- Fáze 3: Inspirace + Stack + námitky + CTA (15–20 min)

### Brunson — Perfektní webinář
- Tři tajemství: Vehicle (metoda funguje), Interní (zvládnete to), Externí (nic nebrání)
- Epiphany Bridge: příběhy, které mění přesvědčení
- Falešná přesvědčení: identifikuj a rozbij v každém tajemství
- The Stack: nabídka po položkách s narůstající hodnotou

Detailní referenční materiál je v `references/framework.md`.

---

## WORKFLOW — Tři fáze práce (POVINNÝ POSTUP)

Tento skill pracuje ve třech oddělených fázích. NIKDY nepřeskakuj fázi. Každá fáze musí být schválena uživatelem než přejdeš na další.

### FÁZE A: Upřesňující otázky

Než cokoliv vytvoříš, zeptej se uživatele na vše, co potřebuješ. Použij nástroj
AskUserQuestion nebo se zeptej přímo v chatu. NIKDY nezačínej vytvářet
strukturu bez odpovědí.

**Povinné otázky (zeptej se vždy):**
- Téma/název webináře
- Délka (30 / 45 / 60 minut)
- Cílová skupina — kdo jsou diváci, jaký level
- Hlavní problém/bolest publika
- Co uživatel prodává (nebo „nic neprodáváme“ — edukační formát)
- Teplota publika (teplé / studené / mix)
- Počet snímků (pokud má preference)

**Kontextové otázky (zeptej se pokud relevantní):**
- Navazuje to na předchozí den nebo webinar? Pokud ano, co se tam řešilo a jaké
  koncepty nebo termíny už byly zavedené?
- Jaký je pitch/nabídka na konci? (cena, formát, garance, bonusy)
- Jsou specifické koncepty/frameworky, které musí být zahrnuty?
- Jsou konkrétní lidé/značky/case studie, které se musí zmínit?
- Jsou zakázaná slova nebo koncepty kterým se vyhnout?
- Jaký tón? (energický, klidný, provokativní, inspirativní)

**Volitelné (dovednost si poradím i bez nich):**
- Případové studie / čísla / výsledky
- Příběh původu
- Falešná přesvědčení publikací
- Bonusový profi Stack

Pokud uživatel neuvede volitelné položky, neblokuj se — odvoď je z kontextu nebo navrhni vlastní.

**Výstup Fáze A:** Shrnutí odpovědí + potvrzení od uživatele, že můžeš pokračovat.

---

### FÁZE B: Struktura (bez textů snímků)

Na základě odpovědí z Fáze A vytvoř přehlednou strukturou webináře. ZATÍM NEPÍŠ TEXTY SLIDŮ ANI POZNÁMKY REPRODUKTORU.

**Formát struktury:**

```markdown
# NÁZEV WEBINÁŘE — STRUKTURA
## Parametry
- Délka: X min | Počet slidů: X | Typ: edukační/prodejní
- Publikum: ...
- Prodáváme: ... / Neprodáváme

## FÁZE 1: Hook + Autorita (slidy 1–X, ~Y min)
| Slide | Typ | Koncept/Obsah (stručně) |
|-------|-----|------------------------|
| 1 | Title | Název webináře |
| 2 | Cold open | Hlavní hook — otázka/číslo |
| ... | ... | ... |

## FÁZE 2: Tři tajemství (slidy X–Y, ~Z min)
### TAJEMSTVÍ 1: [Název] (slidy X–Y)
*Brunson: Vehicle/Internal/External — [popis]*
| Slide | Typ | Koncept/Obsah (stručně) |
...

### TAJEMSTVÍ 2: [Název] (slidy X–Y)
...

### TAJEMSTVÍ 3: [Název] (slidy X–Y)
...

## FÁZE 3: Stack + Pitch (slidy X–Y, ~Z min)
| Slide | Typ | Koncept/Obsah (stručně) |
...
```

**Pravidla pro strukturu:**
- Každý snímek = jeden řádek v tabulce s krátkým popisem konceptu (ne celý text)
- U každého tajemství uveď jaký Brunsonův princip pokrývá (Vehicle/Internal/External)
- Označ deprivační snímky (přechody mezi tajemstvími)
- Označ typ snímku: title, cold open, recap, most, problém, číslo, kontrast (starý vs. new), přehled, detail agenta/konceptu, case study, deprivace, section dělič, stack položka, cena, garance, CTA

**Co řešit v této fázi s uživatelem:**
- Jsou správné proporce mezi fázemi?
- Sedí počet snímků na tajemství?
- Chybí nějaký koncept nebo agent?
- Je správné pořadí?
- Sedí mapování na Brunsonova tři tajemství?
- Má každý agent/koncept vlastní snímek, nebo se párují?

**Výstup Fáze B:** Strukturální tabulka + potvrzení od uživatele. Uživatel může chtít přesouvat snímky, měnit pořadí, přidávat/odebírat. Iteruj dokud není spokojen.

---

### FÁZE C: Texty snímků + Poznámky řečníka

Teprve po schválení struktury piš jednotlivé snímky. Piš je postupně — buď všechny najednou, nebo po sekcích (jak uživatel preferuje).

**Formát každého snímku:**

```markdown
## SLIDE X — Nadpis pro publikum

**Na slidu:**
- [obsah slidu — bullet pointy, tabulky, citáty]

**Poznámky pro speakera:**
„[co speaker říká — přirozená mluvená čeština, ne čtený text]"
```

**KRITICKÉ pravidlo pro nadpisy snímků:**
- Nadpis snímku = to co PUBLIKUM vidí na obrazovce
- NIKDY nepoužívej interní/technické nadpisy jako: „Section divisioner“, „Deprivace“, „Stack položka 3“, „Cold open“, „Falešné přesvědčení“, „Case study“
- Nadpis musí být poutavý, srozumitelný a zajímavý pro diváka
- Příklady správných nadpisů: „Kdo řídí zbytek vaší firmy?", „1 000 hodin ročně", „Operativa vs. Strategie", „Kolik to stojí?", „Nulové riziko. 14 dní."
- Příklady ŠPATNÝCH nadpisů: „Cold open / Hook“, „Deprivace“, „Stack položka 2“, „Rekapitulace Den 2“

Na základě délky zvol počet snímků:

| Délka | Počet snímků | Fáze 1 | Fáze 2 | Fáze 3 |
|-------|-------------|--------|--------|--------|
| 30 min | 20–25 | 5–6 | 10–12 | 5–7 |
| 45 minut | 30–40 | 7–9 | 15–20 | 8–11 |
| 60 min | 40–50 | 8–10 | 20–28 | 12–14 |

Pokud uživatel specifikuje přesný počet snímků, dodržuj ho.

---

## Pravidla pro obsah snímků

- Jeden snímek = jedna myšlenka. Nikdy necpi víc témat na jeden snímek.
- Bullet pointy krátké a úderné — ne celé věty, ale fragmenty, které mluvčí rozvedl.
- Tabulky pro kontrasty (starý vs. nový, amatéři vs. profíci, bez X vs. s X).
- Citáty v uvozovkách jako vizuální kotvy.
- Čísla vždy zvýrazněná — jsou to WOW momenty.
- Section divisionry pro oddělení hlavních částí (Část 1, 2, 3) — ale nadpis musí být pro publikum, není interní.
- Každý agent/pozice/koncept by měl mít vlastní snímek (nepáruj pokud uživatel nechce).

## Pravidla pro poznámky pro speakera

Poznámky pro reproduktor jsou klíčové — to je, co reproduktor skutečně říká. Dodržuj:

- **Stručné a úderné.** Žádné romány. Každé slovo musí mít důvod tam být. Krátké věty. Pauzy naznačené slovem „(pauza)“.
- **Mluvená čeština.** Ne knižní, ne překládaná z angličtiny. Tak jak mluví sebevědomý řečník na pódiu.
- **Řečnické otázky.** „Kolik z vás...?“ "Víte co se stane když...?"
- **Kontrasty a páry.** „Starý svět: X. Nový svět: Y.“
- **Konkrétní čísla.** Vždy když je to možné.
- **Bez sebechvály.** Přednášející mluví o publikaci a jejích problémech, ne o sobě (kromě sekce autorita).
- **Budování deprivace.** V každém tajemství ukazuj co je možné, ale ještě to nemají.
- **Max 3–5 vět na snímku.** Pokud je poznámka delší, zkrať ji.

## Pravidla pro deprivaci (Hormozi)

Deprivace je motor celého webináře. Buduj ji průběžně:

- **Kontrasty**: „Takhle to dělá 95 % firem. Takhle to dělá top 1 %.“
- **Výsledky jiných**: Případové studie, čísla — ukazuj co druzí dosáhli.
- **Propast**: Zvětšuj vzdálenost mezi „kde publikum je" a „kde může být".
- **Nikdy nesaturuj**: Neříkej JAK to udělat. Říkej CO je možné a PROČ to funguje.
- **Bod prodeje**: Pitch přijde v momentě maximální deprivace — na konci Fáze 2, ne dřív.
- **Deprivační slidy**: Na konci každého tajemství musí být snímek, který budí napětí směrem k dalšímu tajemství nebo k pitchi.

## Pravidla pro jazykové varianty

- **Výchozí jazyk: čeština.** Přirozená, mluvená, ne knižní.
- Pokud uživatel nebo jiný jazyk, přizpůsobí vše — slidy i poznámky.
- České webináře: vykání jako default (pokud uživatel neřekne jinak).

---

## Speciální formáty

### Webinář bez prodeje (edukační)

Pokud uživatel řekne "nic neprodáváme":
- Fáze 3 nahraď shrnutím + teaserem na další den/akci + CTA (registrace, ne nákup).
- Deprivaci jdou směrem k dalšímu kroku v sérii, ne k produktu.
- Stack nahraď shrnutím „co jste dnes získali“.

### Série webinářů (vícedenní)

Pokud webinář navazuje na předchozí:
- Začni rychlou rekapitulaci (max 30 vteřin, 1 snímek).
- Postav most: "Včera X. Dnes Y."
- Udržujte paralelní strukturu (pokud Den 2 měl „Skills od marketérů“, Den 3 má „Skills od obchodníků“).
- Teaser na další den na konci.
- V upřesňujících otázkách (Fáze A) se VŽDY zeptej co se dělo v předchozích dnech a jaké koncepty/termíny jsou zavedené.

### Prodejní webinář (s pitchem)

Pokud se na konci prodává:
- V Fázi A se zeptej na: produkt, cena, formát (kurz/program/SaaS), garanci, bonusy, dodací model
- Stack budu po položkách s narůstající hodnotou — každá položka = vlastní snímek
- Odhalení ceny na samostatném snímku s dramatickým sestupem (hodnota → ne X → ne Y → skutečná cena)
- Garance na samostatném snímku
- CTA na posledním snímku

### Živá akce (1–2 dny)

Přečti `references/framework.md` sekci o živých akcích — obsahuje specifické pokyny pro:
- Povinná bezplatná zkušební verze na začátku
- Nabídka stránky s poděkováním
- Upsell jedním kliknutím
- Dvoudenní struktura se dvěma pitchi
- Okamžité odměny (VIP večeře, mastermind)

---

## Iterace a vylepšování

Uživatel často chce upravit jednotlivé snímky po prvním výstupu. Při úpravách:

- Zachovej najdete styl s ostatními snímky.
- Poznámky pro speakera vždy stručné a úderné — nikdy se nerozpovídej.
- Pokud uživatel řekne „lepší copywriting“ — přidej kontrasty, konkrétní čísla, řečnické otázky, kratší věty.
- Pokud uživatel chce sloučit slidy — zachovej všechny klíčové body, zhustí je.
- Pokud uživatel chce jiný nadpis — nabídni variantu 5–10.
- Pokud uživatel chce jiný koncept pro snímek — nabídni 10 variant konceptu (ne celý snímek, jen koncepty).
- Výstup přímo do chatu (ne do souboru), pokud uživatel neřekne jinak.
- Při úpravě jednoho snímku NIKDY neměňte ostatní snímky.

## Ukládání finálního výstupu

Po schválení všech snímků ulož kompletní skript do souboru Markdown s formátem:

```
SKRIPT_[NÁZEV]_[POČET]_SLIDES.md
```

Soubor obsahuje hlavičku s parametry a pak všechny snímky v pořadí.
