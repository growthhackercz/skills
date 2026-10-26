# Šablona přípravy na jednání — battle-ready brief

Cíl: obchodník po přečtení **ví přesně, co říct a v jakém pořadí** — ne kostru, ale munici. Vyplní se do jedné poznámky ke kontaktu (Markdown → GHL Rich Text přes `ghl_assistant_push.py`).

## Zdroje (čti PŘED psaním)
1. **Kontext:** `ghl_context.py` balík (historie, deal, poznámky, Scout brief).
2. **Firemní playbook:** Sales DNA §3 (ceny/kotvy), §4 (metodika), §5 (námitky), §1/§8.
3. **Metodika (pro taktickou hloubku):** `python3 {baseDir}/scripts/kb_read.py INDEX hormozi belfort` — z ní ber KONKRÉTNÍ formulace: otevírací věty, strukturu hovoru (CLOSER), skripty na námitky (looping/DISARM), Value Equation, tonalitu. Bez ní vzniká generická kostra; s ní battle-ready brief. **Když §6 „Zdroj metodiky" ukazuje na vlastní knihovnu klienta, čti ji místo closing-system.**

## Omezení GHL Rich Text (drž)
Žádné tabulky/code blocky. Nadpisy jen H2 s emoji. Bullety nebo `**Klíč:** hodnota`.

## Hlavička (POVINNÝ první řádek — GHL nezobrazuje název poznámky)
```markdown
## Prodejní příprava - [deal/událost] - [datum schůzky]
```

## Blok 1 — 👤 Kdo & kontext (buď konkrétní, ne 2 věty)
```markdown
## 👤 Kdo & kontext
- **Firma / osoba:** [název, pozice, obor]
- **Vztah a historie:** [odkud přišel, kdy, kolik interakcí, na co reagoval — konkrétně]
- **Co ho pálí (jeho slovy, pokud padlo):** [bolest z poznámek/Scout briefu]
- **Rozhodování:** [kdo rozhoduje, rozpočet, časový tlak — co víme]
- **Otevřený obchod:** [název, fáze, hodnota]
- **Dřívější námitky/obavy:** [co už zaznělo, ať to nepřekvapí]
```
Když Scout brief existuje, shrň do 2–3 vět a odkaž (nepřepisuj celý).

## Blok 2 — 🎯 Plán hovoru s formulacemi (CLOSER + §4)
Ne „1) otevření", ale konkrétní věty. Strukturu ber z metodiky.
```markdown
## 🎯 Jak vést hovor
- **Otevření (konkrétní věta):** [navázání na minule + „důvod dnešního hovoru je…"]
- **Discovery — otázky, které musí zaznít:** [2–3 otázky na situaci a hlavně DOPAD, ať si ho pojmenuje sám]
- **Zrcadlo / pojmenování bolesti:** [jak restatovat to, co řekne, ať cítí „on mi rozumí"]
- **Přechod na řešení:** [věta, kterou mostíš z bolesti na nabídku]
- **Uzávěr (konkrétní věta + termín):** [jak požádat o další krok s konkrétním datem]
```

## Blok 3 — 💰 Hodnota a nabídka (Value Equation + §3)
```markdown
## 💰 Co nabídnout a jak
- **Produkt a proč sedí:** [fit v 1 větě, navázaný na jeho bolest]
- **Hodnota (Value Equation):** vysněný výsledek [X] · proč je pravděpodobný [důkaz/reference] · jak rychle [čas] · s jak malým úsilím [na klíč?]
- **Kotva a pořadí:** hodnota balíčku [číslo z §3] → cena [číslo z §3]; VŽDY hodnota před cenou
- **Slevy:** [pravidlo z §3]
```
Čísla VÝHRADNĚ z §3. Nikdy nevymýšlej.

## Blok 4 — 🛡️ Námitky: skripty, ne hesla (§5 + looping)
Pro 2–3 námitky, které u TOHOTO klienta reálně hrozí, napiš **postup na 2–3 kroky** (deflektuj → izoluj → smyčkuj/reframe), ne jednořádkovou odpověď.
```markdown
## 🛡️ Když přijde námitka
- **„[námitka]"**
  1. [deflekce/izolace — „Rozumím. Dává vám ta myšlenka sama o sobě smysl?"]
  2. [reframe / návrat k jeho číslu nebo hodnotě — konkrétní věta z §5]
  3. [snížení prahu — záruka / malý krok / pilot]
- **Předejít předem (labeling):** [námitku, co skoro jistě přijde, pojmenuj sám dřív, než ji řekne]
```

## Blok 5 — ⚠️ Na co pozor u tohohle klienta
```markdown
## ⚠️ Pasti a tón
- **Nedělej:** [past specifická pro tenhle typ — např. cena před hodnotou, feature dumping]
- **Tón:** [1 věta — např. „má rád konkrétní čísla, ne obecné sliby; drž klid a jistotu"]
```

---

## Vyplněný příklad (RICH — takhle bohaté to má být)
```markdown
## Prodejní příprava - Firma Alfa (Produkt A) - 25.7.

## 👤 Kdo & kontext
- **Firma / osoba:** Firma Alfa, jednatelka, síť klinik (2 pobočky, roste)
- **Vztah a historie:** lead z webináře 12.7., poptala Produkt A, 1 hovor; reagovala na téma „padající leady", řešila kapacitu recepce
- **Co ji pálí:** „leady nám padají mezi prsty", nikdo je nestíhá odbavit
- **Rozhodování:** ona + provozní ředitel; chce to mít do konce srpna; rozpočet neřešen
- **Otevřený obchod:** Produkt A — fáze „nabídka", <cena> Kč
- **Dřívější obavy:** jestli to zvládnou nasadit bez zásahu do recepce

## 🎯 Jak vést hovor
- **Otevření:** „Minule jsme skončili u toho, že vám leady padají mezi prsty. Důvod dnešního hovoru je ukázat vám na vašich číslech, kolik vás to reálně stojí — a jak to zastavit."
- **Discovery:** „Kolik poptávek měsíčně vám reálně proteče bez odpovědi?" → „A co se stane s klientem, který se neozve zpět?" → „Kdybyste to měla vyčíslit v penězích, na kolik to přijde?"
- **Zrcadlo:** až řekne číslo, zopakuj: „Takže vás to stojí zhruba [její číslo] měsíčně jen tím, že se nikdo neozve včas — chápu to správně?"
- **Přechod:** „Přesně tuhle díru Produkt A zavírá — ozve se každému leadu do minuty, 24/7."
- **Uzávěr:** „Navrhuju rozjet jednu pobočku jako pilot do 14 dní, ať to vidíte na reálných číslech. Sedělo by spuštění příští týden ve středu?"

## 💰 Co nabídnout a jak
- **Produkt a proč sedí:** Produkt A — řeší přesně padající leady, odbaví je 24/7 bez zátěže recepce
- **Hodnota:** výsledek = žádný ztracený lead · pravděpodobné díky [reference/číslo z §3] · rychle (pilot do 14 dní) · na klíč (ona nic neprogramuje)
- **Kotva a pořadí:** hodnota balíčku <hodnota balíčku> → cena <cena>; nejdřív hodnota, pak cena
- **Slevy:** neslevovat

## 🛡️ Když přijde námitka
- **„Je to drahé."**
  1. „Rozumím. Ale dovolte otázku — dává vám ta myšlenka, že by vám leady hlídal někdo 24/7, sama o sobě smysl?"
  2. „Řekla jste [její číslo] měsíčně ztracených. Bavíme se o zlomku, který tuhle díru zastaví — je to pro vás výdaj, nebo investice?"
  3. „Rozjedeme jednu pobočku jako pilot, ať se rozhodujete podle reálných čísel."
- **Předejít předem:** „Nejspíš vás napadá, jestli to nezasáhne do práce recepce — proto to jede na klíč, vaši lidé nic nenastavují."

## ⚠️ Pasti a tón
- **Nedělej:** neříkej cenu dřív, než si sama vyčíslí ztrátu; nesypej funkce
- **Tón:** konkrétní čísla, ne obecné sliby; klid a jistota, ne tlak
```
