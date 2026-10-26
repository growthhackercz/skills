# Karta „Prodejní zápis" — po hovoru/jednání (Workflow C)

Assistant po interakci s klientem zapíše do CRM **Prodejní zápis** = co padlo + kde deal stojí + posun + hotový follow-up. **NEHODNOTÍ výkon obchodníka** — to je scorecard Mentora. Assistant posouvá OBCHOD, mentor hodnotí ČLOVĚKA.

## Cíl: obchodník má po přečtení jasno, kde deal je a co dělat dál — a follow-up hotový k odeslání, ne k přepisování.

## Omezení GHL Rich Text
Žádné tabulky/code blocky, nadpisy jen H2 s emoji, bullety.

## Hlavička (POVINNÝ první řádek)
```markdown
## Prodejní zápis - [deal/událost] - [datum hovoru]
```

## Struktura
```markdown
## Prodejní zápis - [deal/událost] - [datum]

## 📝 Co padlo
- [3–5 klíčových bodů z hovoru — z `MeetingInsight` v1, ne celý přepis]
- [rozpočet / termín / konkurence / kdo rozhoduje — pokud padlo]
- [nálada/zájem klienta — koupěchtivý / vlažný / brzdí ho X]

## 📊 Kde deal stojí
- **Fáze teď → kam míří:** [aktuální fáze → další fáze]
- **Co brání uzávěru:** [hlavní překážka jednou větou]
- **Teplota:** [horký / vlažný / chladne — a proč]

## ✅ Dohodnuto
- [na čem jste se shodli, kdo co udělá do kdy]

## 🎯 Další krok
- [JEDEN konkrétní krok s termínem — jde i jako GHL úkol obchodníkovi]

## ✉️ Follow-up (hotový k odeslání)
**Předmět:** [konkrétní, navázaný na hovor]

[Kompletní, personalizovaný text — ne kostra. Naváž na to, co padlo, jeho vlastními čísly; jeden jasný další krok s termínem; podpis obchodníka. Obchodník ho jen zkontroluje a odešle.]
```

## Doručení follow-upu (důležité — bez zbytečného přepisování)
- Follow-up piš jako **hotový, kompletní text** (personalizovaný, ready k odeslání), ne šablonu s placeholdery.
- **Kromě zápisu vytvoř samostatný GHL úkol** obchodníkovi „Odeslat follow-up — [lead]" a **celý text follow-upu vlož do těla úkolu** — obchodník ho má v úkolech, jedním kopírováním vloží do e-mailu/SMS a odešle.
- **Assistant follow-up NEODESÍLÁ.** (GHL API neumí vytvořit neodeslaný draft v okně; proto hotový text v úkolu = nejbližší „jeden klik". Odesílá vždy člověk.)

## Pravidla
- **Vstup = `MeetingInsight` se `schema: "openclaw.meeting_insight.v1"`** z Fireflies (souhrn, akční kroky, námitky, signály) NEBO manuální popis. Nikdy celý přepis do kontextu.
- **Další krok jen NAVRHUJEŠ** (GHL úkol); stage nepřepisuješ.
- **Nehodnotíš vedení hovoru** (to Mentor). Píšeš, co dál s obchodem.
- Poznámku + úkol(y) zmraz přes `ghl_assistant_push.py --kind po-jednani --create-plan` se stabilním `--idempotency-key` a trvalým `--plan-artifact`. Proveď jen po souhlasu s exact SHA podle sdíleného Sales GHL workflow.

## Vyplněný příklad (RICH)
```markdown
## Prodejní zápis - Firma Alfa (Produkt A) - 25.7.

## 📝 Co padlo
- Potvrdila, že jim měsíčně uteče 15–20 leadů bez odpovědi
- Sama vyčíslila ztrátu na „klidně 200 tisíc měsíčně"
- Rozhoduje ona + provozní ředitel; chtějí to mít do konce srpna
- Zajímá ji hlavně, jestli to zvládnou bez zásahu do recepce; jinak koupěchtivá

## 📊 Kde deal stojí
- **Fáze teď → kam míří:** nabídka → pilotní nasazení
- **Co brání uzávěru:** obava z nasazení + potřebuje souhlas provozního
- **Teplota:** horký — sama si vyčíslila bolest, má termín

## ✅ Dohodnuto
- Pošleme pilotní návrh pro jednu pobočku
- Ona to probere s provozním do konce týdne

## 🎯 Další krok
- Poslat pilotní návrh + onboarding checklist do pátku 27.7.

## ✉️ Follow-up (hotový k odeslání)
**Předmět:** Pilotní návrh Produktu A pro Firma Alfa — jak zastavit těch 200 tis. měsíčně

Dobrý den paní doktorko,

děkuji za dnešní čas. Jak jste sama řekla, těch 15–20 leadů měsíčně vás stojí
klidně 200 tisíc — a přesně tuhle díru Produkt A zavírá: ozve se každému leadu
do minuty, 24/7, bez jakéhokoli zásahu do práce vaší recepce.

Do pátku vám připravím pilotní návrh pro jednu pobočku, ať to vidíte na reálných
číslech, než se rozhodnete do plna. Můžete ho pak v klidu probrat s provozním.

Sedělo by v týdnu potom krátké online demo, ať vidíte, jak to reálně běží?

S pozdravem
[obchodník]
```
