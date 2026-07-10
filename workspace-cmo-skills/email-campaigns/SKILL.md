---
name: email-campaigns
description: "Navrhuje emailové sekvence, segmentaci, timing a A/B testy; v draft flow ho volá email-draft-orchestrator před publisher krokem."
category: content
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---

# E-mailové kampaně

Piš e-maily, které se otevírají, proklikávají a vedou k akci. Spravuj
sekvence, segmentuj publikum, testuj vše a buduj swipe file toho, co funguje.

## Datové soubory

### Email swipe file
Udržujte v `memory/email-swipe-file.json`:

```json
{
  "highPerformers": [
    {
      "subject": "Your trial ends tomorrow (here's what you'll lose)",
      "type": "urgency/trial-expiry",
      "openRate": 62,
      "clickRate": 18,
      "sequence": "trial-nurture",
      "date": "2025-01-15",
      "whyItWorked": "Loss aversion + specificity. Listed 3 features they'd lose access to."
    }
  ],
  "subjectLineTests": [
    {
      "date": "2025-01-20",
      "variantA": "New feature: bulk invoicing",
      "variantB": "You asked, we built it",
      "winner": "B",
      "openRateA": 28,
      "openRateB": 41,
      "lesson": "Curiosity gap + 'you' language outperforms feature announcements"
    }
  ]
}
```

### Sledování sekvencí
Sledovat aktivní sekvence v `memory/email-sequences.json`:

```json
{
  "sequences": [
    {
      "name": "welcome",
      "emails": 5,
      "trigger": "signup",
      "status": "active",
      "metrics": {
        "overallOpenRate": 52,
        "overallClickRate": 12,
        "conversionToTrial": 8.5
      },
      "lastUpdated": "2025-01-15"
    }
  ]
}
```

## Psaní předmětových řádků

Každý důležitý e-mail dostane A/B testovaný předmět. Vygenerujte alespoň 2 varianty.

**Fungující rámce:**
- **Curiosity gap:** „Jediná metrika, která předpověděla náš odchod“ (nutno vědět)
- **Specifikum:** „Jak jsme zvýšili počet registrací o 34 % za 2 týdny“ (čísla budují důvěryhodnost)
- **Přímá výhoda:** „Ušetřete 3 hodiny na fakturaci tento týden“ (jasná hodnota, rychlé)
- **Personal/conversational:** „Rychlá otázka o vašem účtu“ (pocit 1:1)
- **Urgentnost (používejte střídmě):** „Vaše zkušební období končí za 24 hodin“ (pouze ve skutečnosti)

**Pravidla pro předmět:**
- Méně než 50 znaků funguje nejlépe na mobilu
- Nepoužívejte VŠECHNA VELKÁ PÍSMENA ani nadměrnou interpunkci!!!
- Personalizace (křestní jméno) pomáhá, ale není kouzelná
- Text náhledu je vaším druhým předmětem. Použijte to.
- Nikdy neuvádějte v omyl. Clickbait narušuje důvěru a zvyšuje počet odhlášek.

## E-mailové sekvence

### Uvítací sekvence (po registraci)
Cíl: aktivovat uživatele a rychle mu ukázat základní hodnotu.

1. **Okamžitě** – Vítejte + jeden jasný první krok („Zde je návod, jak odeslat první fakturu do 2 minut“)
2. **Den 1** – Sociální důkaz + rychlá výhra („Sára minulý týden poslala 14 faktur. Zde je návod, jak začít“)
3. **Den 3** – Překonejte námitku č. 1 nebo třecí bod
4. **Den 5** – Zvýraznění funkce, která řeší konkrétní bolest
5. **Den 7** – Soft CTA pro upgrade nebo dokončení nastavení

### Sekvence péče (zapojená, ale neplatící)
Cíl: vybudovat důvěru, ukázat hodnotu, přejít ke konverzi.

- Vzdělávací obsah související s případem jejich použití
- Případové studie a příběhy zákazníků
- Produktové tipy, které neobjevili
- Jemné CTAs každé 2-3 e-maily

### Spouštěcí sekvence (spuštění produktu nebo funkce)
Cíl: vybudovat předvídavost, podnítit akci v den spuštění, sledovat.

1. **T-7 dní** – Teaser („Něco nového se blíží...“)
2. **T-3 dny** – Odhalení + nabídka předběžného přístupu
3. **T-1 den** – Připomenutí + sociální důkaz od beta testerů
4. **Den spuštění** – Úplné oznámení. Vymazat CTA.
5. **T+2 dny** – Sledování pro neotevřené (jiný předmět)
6. **T+5 dní** – Důkaz výsledků/social („500 lidí ji již používá“)

### Sekvence Win-Back (uvolnění nebo neaktivní uživatelé)
Cíl: znovu oslovit uživatele, kteří přestali produkt používat.

1. **Den 1** – „Všimli jsme si, že jsi byl pryč“ (žádná vina, jen hodnota)
2. **Den 4** – Co je nového od doby, kdy odešli (funkce, vylepšení)
3. **Den 8** - "Je něco, co bychom mohli udělat lépe?" (úhel zpětné vazby)
4. **Den 14** – Konečná nabídka nebo poslední šance (v případě potřeby sleva)

### Re-Engagement Sequence (cold email list subscribers)
Goal: clean your list and re-engage the interested.

1. **E-mail 1** – „Stále máte zájem?“ s jasným ano/no CTA
2. **E-mail 2** – Nejlepší obsah nebo nabídka, kterou máte
3. **E-mail 3** – „Poslední e-mail, pokud nekliknete“ (a to myslíte vážně)
4. **Žádné kliknutí po 3 e-mailech** - Odebrat z aktivního seznamu. Čisté seznamy = lepší doručitelnost.

## Segmentace publika

Segmentujte podle chování, nejen podle demografických údajů:

- **Podle zapojení:** aktivní otvírače, příležitostní čtenáři, studení předplatitelé
- **Podle fáze:** bezplatný uživatel, zkušební uživatel, platící zákazník, staženo
- **Podle zdroje:** jak vás našli (organické, placené, doporučení, hledání produktu)
- **Podle zájmu:** na jaký obsah klikli, jaké funkce používají
– **Podle hodnoty:** zákazníci s vysokou LTV vs. s nízkou úrovní

**Pravidla segmentace:**
– Čím cílenější e-mail, tím lepší výkon
- Cílený segment 500 osob překoná výbuch 5 000 osob
- Aktualizujte segmenty měsíčně na základě změn chování
- Sledujte konverzní poměry podle segmentů, abyste našli své nejlepší publikum

## Metriky a srovnávací hodnoty

Sledovat při každém odeslání:
- **Otevřená míra** - Průměr v oboru ~20–25 %. Váš vlastní historický průměr je lepší benchmark.
– **Míra prokliku** – Průměr ~2–5 %. Nad 5 % je vynikající.
- **Míra odhlášení** - Udržujte pod 0,5 % za odeslání. Nad 1 % znamená, že něco není v pořádku.
- **Míra okamžitého opuštění** - Udržujte pod 2 %. Problémy s kvalitou seznamu signálů nad 3 %.
– **Konverzní poměr** – Kliknutí, která vedla k požadované akci. Číslo, na kterém skutečně záleží.

**Kdy se bát:**
- Otevřené sazby v průběhu času klesají (problém s doručením nebo únava seznamu)
– Klesající míra prokliku (obsah neodpovídá zájmu publika)
- Odhlásit odběr (odeslali jste něco špatně nebo příliš často)
- Odskoky (špatná hygiena seznamu)

## Optimalizace času odeslání

**Výchozí body:**
– B2B: úterý–čtvrtek, 9–11 hodin, časové pásmo příjemce
- B2C: večery a víkendy mohou fungovat dobře
- Informační bulletiny: důslednost je důležitější než načasování. Vyberte si den a držte se ho.

**Potom otestujte.** Vaše publikum se může lišit. Spusťte testy času odeslání po dobu 4–6 týdnů, abyste našli své sladké místo.

## Pravidla

- **Před odesláním vždy získejte souhlas.** Navrhněte e-mail, ukažte jej, získejte souhlas.
- **Každé odeslání je test.** A/B testovací řádky předmětu na libovolném seznamu nad 1 000. Testujte vždy jednu proměnnou.
- **Všechno zaznamenejte do souboru s přejetím.** Vysoce výkonní a propadáky. Obojí tě něco naučí.
- **Čistěte svůj seznam čtvrtletně.** Okamžitě odstraňte tvrdé bounce. Znovu připojte nebo odstraňte studené předplatitele.
- **Respektujte odhlášení.** Usnadněte si to, nechte to fungovat, nikdy neposílejte někomu, kdo se odhlásil.
- **Na textu náhledu záleží.** Nenechávejte to jako „Zobrazit tento e-mail ve vašem prohlížeči.“ Použijte jej jako druhý předmět.
- **Mobil nejprve.** Více než 60 % e-mailů se čte na mobilu. Krátké odstavce. Velká tlačítka. Žádné drobné odkazy.

## Draft handoff do platforem

Tento skill muze fungovat samostatne pro strategii kampane, ale v kompletnim draft flow ho typicky vola `email-draft-orchestrator`.

Spravne poradi pro kampan:

1. `email-draft-orchestrator` zastresi zadani.
2. Orchestrator pouzije `email-writer` pro copy a sekvenci.
3. Orchestrator pouzije tento skill (`email-campaigns`) pro segmentaci, timing, A/B testy a kampanove poznamky.
4. Orchestrator pripravi HTML/TXT/manifest.
5. Orchestrator zvoli cilovy publisher:
   - `cliqsales-email-publisher` pro CliqSales/GHL
   - `smartemailing-email-publisher` pro SmartEmailing

Pokud uzivatel chce jen text jednoho emailu, nepoustej kampanovy flow; pouzij pouze `email-writer`.

Default je vzdy draft. Newsletter, schedule nebo send krok je povoleny jen po explicitnim potvrzeni uzivatele v aktualni konverzaci.
