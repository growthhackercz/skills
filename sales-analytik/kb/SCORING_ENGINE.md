# SCORING ENGINE — 0–100

Celkové skóre hovoru 0–100 jako vážený součet 8 kategorií. Váhy jsou **výchozí univerzální**; konkrétní firma je ladí v Sales DNA §6 (musí dát součet 100).

## Kategorie a výchozí váhy

| # | Kategorie | Váha | Co hodnotí (opři o evidenci) |
|---|---|---:|---|
| 1 | Vedení a struktura hovoru | 15 | kontrola linie (Straight Line), pořadí fází, přechody, žádné předčasné uzavírání ani zbytečné vracení |
| 2 | Discovery a diagnostika | 20 | otázky na situaci, bolest a její dopad; **zákazník sám pojmenoval důsledek** (ne obchodník za něj); odhalení skutečné motivace |
| 3 | Kvalifikace | 10 | rozpočet, rozhodovací pravomoc, časování, vhodnost nabídky pro klienta |
| 4 | Vytvoření hodnoty a jistoty | 15 | Value Equation (výsledek × pravděpodobnost / prodleva × úsilí); Three Tens (produkt/obchodník/firma) |
| 5 | Prezentace řešení | 10 | nabídka navázaná na zjištěnou potřebu; „prodej dovolenou" (výsledek), ne výčet funkcí |
| 6 | Práce s námitkami | 15 | správná diagnóza skutečné námitky; looping/reframe místo logického boje; adresované všechny |
| 7 | Closing a další krok | 10 | přirozený přechod k závazku; domluven **konkrétní další krok s termínem**; žádný tlak na pilu |
| 8 | Etika prodeje | 5 | žádná manipulace; respekt k „ne"; nabídka byla pro klienta reálně vhodná (`ethics.md`) |

Skóre kategorie = 0–100 % naplnění × váha. Součet = 0–100.

## Povinná pravidla (přebíjejí body)
1. **Výsledek ≠ skóre.** Nákup sám o sobě nezvedá skóre. Slabý proces, který omylem prodal, dostane nízké skóre za proces. Dobrý proces vedoucí k oprávněnému „ne" může mít vysoké skóre.
2. **Bez evidence není bod.** Každé podskóre má oporu v přepisu; kde chybí data (audio pro doručení), sniž jistotu, ne skóre naslepo.
3. **Manipulace = strop.** Doložená manipulativní technika (`ethics.md`) drží celkové skóre pod 60 bez ohledu na ostatní kategorie, a pojmenuje se jako hlavní nález.
4. **Chybějící fáze se počítá.** Vynechaná discovery nebo chybějící další krok se promítne do příslušné kategorie, i když „hovor dobře plynul".
5. **Urgence a uzávěr se ODMĚŇUJÍ; trestá se jen falešný tlak.** Prodejní tým má tlačit na uzávěr a je to správně. Vytvořená urgence (náklad nečinnosti, „proč teď", jasný další krok s termínem, dotažený uzávěr) je **plus u všech typů dealů**. Penalizuje se jen **manipulace**: falešná naléhavost/vzácnost, tlak přes jasné „ne", zesilování bolesti bez špetky důvěry (`ethics.md`). Urgence ≠ manipulace.
   - **Transakční deal** (menší, rychlé, spíš jeden hovor): zdravý tlak a rychlý close jsou plus; **měkký, pasivní závěr bez urgence = chyba.**
   - **Skutečně high-ticket / vztahový** (velká zakázka, víc schůzek): urgence musí stát na vybudované důvěře, jinak backfiruje (`human-centric.md`). I tam ale „nedomluvil další krok s termínem" = chyba. Netlačit tam, kde bylo potřeba zavřít, NENÍ ctnost.
   Typ prodeje bere z Sales DNA §6 (pole „Typ prodeje"); bez něj rozliš podle ceny/délky cyklu (high-ticket ~ nad 5 000 USD). **Default = zdravá urgence se odměňuje.**

## Pásma (pro rychlou orientaci, ne náhrada evidence)
Název pásma se používá i v hodnocení pro obchodníka — drž profesionální, věcný tón (žádné hovorové nálepky).

- **85–100 · Vzorový hovor** — silný a replikovatelný proces.
- **70–84 · Nadprůměrný hovor** — solidní vedení, prostor pro dílčí zlepšení.
- **55–69 · Průměrný hovor s rezervami** — funguje, ale jedna klíčová fáze zůstala nedotažená (nejčastěji discovery nebo závěr).
- **40–54 · Podprůměrný hovor** — proces obchod netáhl; výsledek spíš navzdory hovoru.
- **pod 40 · Kritické nedostatky** — zásadní mezery v procesu nebo etický problém.

## Výstup skóre
Vždy: celkové skóre + rozpad po 8 kategoriích + 1–2 věty proč u každé kategorie s citací. Formát viz `schemas/scorecard.schema.json`.
