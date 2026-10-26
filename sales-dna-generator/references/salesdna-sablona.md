# Šablona salesDNA.md — 11 sekcí

Cílový soubor: `/documents/sales/salesDNA.md`. VŠE v jednom souboru — víc produktů = podsekce `### <produkt>` uvnitř sekcí, nikdy další soubory. Hodnoty, které uživatel nedodal, označ `[výchozí]`.

Hranice obsahu: **KOMU prodávat a CO** žije v productDNA (ideální klient, popis produktu). **JAK prodávat** žije tady. Nezdvojuj.

---

```markdown
---
artifactType: sales-dna
skillVersion: "1.0"
---

# Sales DNA — <název firmy>

> Prodejní playbook. Čte ho celý AI prodejní tým. Změny jen po schválení majitele.
> Verze: v1 · vytvořeno <datum>

## 1. Nastavení enginu

- Prodejní tým: <ano — N obchodníků / ne — jednání vede majitel / žádná jednání (čistý online prodej)>
- Obchodníci a mapování na CliqSales uživatele: <jméno → GHL user → e-mail obchodníka> (pokud tým) <!-- e-mail slouží pro per-call hodnocení: hned po ohodnocení hovoru dostane obchodník e-mail se svou kartou. Prázdný e-mail → jen deliverable v Control Centru. -->
- Ověřená odesílací e-mailová adresa: <adresa dostupná v GHL pro `emailFrom`; bez ní se e-mailové žádosti nevytvářejí>
- Pracovní doba: <Po–Pá 9–17 [výchozí]> — SLA a eskalace platí jen v ní; dovolené hlásit stratégovi
- Trh: <B2B / B2C / obojí>
- Režim funnelů (míra člověka v uzavření): <online — prodá sám / hybridní — online vstup + prodejce u uzavření / osobní — cílem je jednání>
- Frekvence kontroly (cron): <každou hodinu [výchozí] / každé 4 hodiny / denně>
- **Příjemci reportů (Mentor/Analytik):** <jméno manažera → e-mail> <!-- kam chodí denní/týdenní reporty výkonu týmu a učení firmy. Reporty jdou vždy do Control Centra (deliverable) a navíc e-mailem na tento e-mail. Víc příjemců = víc řádků. Prázdné → jen Control Center. -->
- **Hodnocení hovorů na kartu klienta:** <zapnuto [výchozí] / vypnuto> <!-- zapnuto: Mentor přidá ke kontaktu klienta krátkou poznámku „Prodejní hodnocení – obchodník X – skóre %" s odkazem na detail v Data Center (pozor: skóre obchodníka je pak viditelné komukoli s přístupem do CRM). Plný scorecard žije v Data Center per obchodník. Vypnuto: hodnocení zůstává jen v Data Center, na kartu klienta nic nejde. -->

## 2. Cíle

- Měsíční cíl: <Kč> · <počet obchodů / schůzek>
- Týdenní rytmus reportu: <pondělí 8:00 [výchozí]>

## 3. Produkty a ceny

<!-- Per produkt podsekce. Odkazuj na productDNA, neopisuj popis produktu. -->
### <produkt A> (productDNA: /documents/brand/products/<slug>/productDNA.md)
- Cena a kotva: <hodnota balíčku X Kč → cena Y Kč; pořadí prezentace: nejdřív hodnota, pak cena>
- Pravidlo slev: <neslevovat [výchozí] / max X % po schválení majitele>

<!-- E-shop s mnoha produkty místo podsekcí: -->
- Katalog a feed: viz sekce 11 (Feed) — agent z něj čte názvy, kategorie, ceny, dostupnost

## 4. Prodejní metodika

- Struktura jednání: <kroky 1..N — jak vést schůzku od úvodu po závazek> [výchozí: 1) otevření a důvěra, 2) otázky na situaci a bolest, 3) klient sám pojmenuje dopad, 4) nabídka přes hodnotu, 5) další krok s termínem]
- Klíčové otázky: <3–5 otázek, které musí zaznít>
- Čemu se vyhnout: <např. cena před hodnotou>
### <produkt s odlišným postupem — jen pokud se reálně liší>

## 5. Námitky a odpovědi

### Společné
- „<námitka>" → <ověřená odpověď>
### <produkt A>
- „<námitka k produktu>" → <odpověď>

## 6. Skórovací kritéria a váhy jednání

<!-- Podle nich MENTOR (sales-mentor) hodnotí každý nahraný hovor: skóre 0–100 v 8 kategoriích
     dle univerzální metodiky (Hormozi + Belfort + Human-Centric pro high-ticket). Zde se jen LADÍ VÁHY pro tuto firmu
     (součet musí být 100); katalog námitek k hodnocení je v §5. Necháte-li výchozí, platí
     univerzální váhy. Analytik z hotových hodnocení pak agreguje vzorce do §10. -->

| Kategorie | Výchozí váha | Váha pro tuto firmu |
|---|---:|---:|
| Vedení a struktura hovoru | 15 | 15 |
| Discovery a diagnostika | 20 | 20 |
| Kvalifikace | 10 | 10 |
| Vytvoření hodnoty a jistoty | 15 | 15 |
| Prezentace řešení | 10 | 10 |
| Práce s námitkami | 15 | 15 |
| Closing a další krok | 10 | 10 |
| Etika a zákaznická vhodnost | 5 | 5 |
| **Součet** | **100** | **100** |

- Co pro tuto firmu znamená „dobře odvedený hovor" (z onboardingu): <volně, promítne se do vah>
- **Typ prodeje:** `transakční` / `vztahový (high-ticket)` <!-- vztahový → nakloň váhy k Etice a Hodnotě/jistotě (důvěra); mentor u vztahových dealů odměňuje urgenci POSTAVENOU na důvěře a penalizuje jen falešný/manipulativní tlak (SCORING_ENGINE pravidlo 5) — zavírání a urgence se odměňují vždy. Transakční → víc váhy Closingu a Prezentaci. -->
- Katalog námitek k hodnocení: viz §5 (typy dle univerzální taxonomie).
- **Zdroj metodiky:** `CliqSales Closing System` <!-- výchozí: proprietární metodika CliqSales Closing System™ (Hormozi + Belfort + Human-Centric). Chce-li firma hodnotit podle VLASTNÍHO frameworku, napiš sem místo `CliqSales Closing System` cestu k vlastní knihovně, např. `/documents/sales/vlastni-metodika/` (jeden nebo víc .md souborů). Mentor i Analytik pak čtou tu firemní místo naší. Váhy a 8 kategorií výše zůstávají, mění se jen obsahové měřítko. -->

## 7. Provozní pravidla stratéga

<!-- Lidské věty. Stratég je interpretuje v každém cron běhu. -->
- Kontakt bez aktivity <180 dní [výchozí]> a bez DND → kandidát reaktivační vlny (max 1× za <6 měsíců [výchozí]>)
- Nový lead bez kontaktu do <1 h [výchozí]> v pracovní době → eskalace obchodníkovi/majiteli
- Nabídka bez odpovědi <14 dní [výchozí]> → připomínka; <30 dní [výchozí]> → návrh uzavřít jako ztracené s důvodem
- Nový nákup → spustit upsell dle sekce 11
- Deal zavřený bez důvodu prohry → vyžádat důvod od obchodníka
- Globální touch-cap: max <2 oslovení za 14 dní [výchozí]> na kontakt napříč všemi odchozími skilly (evidence tagem `osloven:<datum>`, viz sekce 9)
- Hromadné odeslání (vlna) NIKDY bez schválení majitele

## 8. Mapa pipelines

| Pipeline | Účel | Pravidla |
|---|---|---|
| <Hlavní prodej> | nové obchody | plná údržba; pravděpodobnosti per fáze: <fáze = %> |
| <Reaktivace> | obchody z vln | kratší aging <7 dní [výchozí]>; nepočítá se do hlavního forecastu |
| <mimo engine> | <servis apod.> | stratég ignoruje |

## 9. Tagová taxonomie a detekce nákupů

- Nákup: <objednávky přes platformu (Orders) / tag `produkt:<slug>` přidává workflow či obchodník / obojí>
- `zajem:<slug>` — projevil zájem (quiz, nabídka)
- `reaktivace:<RRRR-MM>` — byl ve vlně (karanténa)
- `osloven:<RRRR-MM-DD>` — každý odchozí dotyk (zapisují odchozí skilly; podklad touch-capu ze sekce 7)
- Evidenční tagy skillů (automatické, needitovat ručně): `upsell-sent:` / `upsell-holdout` / `vlna-reply:` / `cyklus:*`
- DND — nerušit, tvrdě respektovat

## 10. Ověřené poznatky (zapisuje smyčka — jen po schválení)

<!-- Sem analytik/stratég navrhují poznatky z praxe. Zápis vždy až po schválení majitele. -->
- <datum> v1 — vytvořeno onboarding rozhovorem

## 11. Upsell, cross-sell a katalog (kurátorská pravidla — VŽDY poslední sekce)

<!-- Čte AI Upsell & Cross-sell Agent; tabulky parsuje skript — zachovat PŘESNĚ
     názvy podsekcí a sloupce. Klíč = skupina produktů (item_group z feedu;
     u služeb slug z productDNA). `*` = platí pro vše. Změny schvaluje majitel. -->

### Mantinely a sekvence
- Max 1 nabídka (= celá sekvence 3 e-mailů) za <30 dní [výchozí]> — platí napříč upsellem, cross-sellem i opakovaným nákupem
- Sekvence: E1 hned · E2 +<7 dní> · E3 +<14 dní> [výchozí fyzické zboží; služby/digitál +2/+7]
- Nenabízet levnější, než co právě koupil [výchozí; neplatí pro doplňky z Přibitých párů a bundlů]
- Doporučení vybírá agent VÝHRADNĚ z pravidel níže + evidence z objednávek (feed / productDNA)

### Opakovaný nákup (produkty kupované v cyklu) — vykonává Re-activator
- <produkt>: cyklus <X dní / „spočítat z objednávek" [výchozí]>
- Připomínka „Nedochází vám X?" od 1,2× cyklu (průběžný režim — pravidlo se schvaluje jednou); nad 2× cyklu = spící → vlna
- Upsell/cross-sell se spouští VÝHRADNĚ nákupem — časové připomínky mu nepatří

### Feed
- Zdroj: <URL Google Shopping feedu (XML); u služeb „productDNA">
- Párovací klíč: <feed_id / sku / ean> — rozhodl audit při aktivaci, neměnit bez ověření
- Obnova katalogu: <denně [výchozí]>

### Flagship produkty
| Skupina | Produkt | Kdy nabízet |
|---|---|---|
| <kód> | <název> | <komu/kdy> |

### Bundly
| Bundle | Skupiny (čárkami) | Poznámka |
|---|---|---|
| <název sady> | <kód1, kód2, kód3> | <pořadí nabízení> |

### Přibité páry (po X vždy nabídni Y)
| Koupil | Nabídni | Poznámka |
|---|---|---|
| <kód> | <kód> | <důvod do e-mailu> |

### Upgrade cesty (jediný povolený „upsell" — dražší varianta téhož)
| Ze skupiny | Na skupinu | Podmínka |
|---|---|---|
| <kód> | <kód> | <lhůta / doplatek / předplatné> |

### Nikdy nenabízet
| Ke skupině | Nenabízet | Důvod |
|---|---|---|
| * | <kód> | <důvod> |
```

---

## Výchozí hodnoty (když uživatel řekne „nevím")

| Parametr | Výchozí |
|---|---|
| Pracovní doba | Po–Pá 9:00–17:00 |
| Frekvence cronu | každou hodinu |
| Spící kontakt | bez aktivity 180 dní |
| Karanténa reaktivace | max 1× za 6 měsíců |
| SLA nový lead | kontakt do 1 h (v pracovní době) |
| Aging nabídky | připomínka 14 dní, návrh uzavření 30 dní |
| Aging reaktivační pipeline | 7 dní |
| Upsell frekvence | max 1 nabídka (sekvence) / 30 dní |
| Upsell sekvence | E1 hned · E2 +7 dní · E3 +14 dní (služby/digitál +2/+7) |
| Obnova katalogu | denně |
| Report | pondělí 8:00 |
| Slevy | neslevovat |
