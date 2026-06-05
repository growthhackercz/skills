---
name: content-ideation
description: Vytvářejte bodované nápady na obsah na základě trendů, dotazů publika a odborných znalostí tvůrců. Použijte, když tvůrce potřebuje nápady na témata, při týdenním plánování obsahu nebo když je třeba vyplnit mezery v obsahu.
status: ready
version: "1.0"
publishedAt: "2026-04-25"
category: content
---

# Content Ideation

Vytvářej nápady na obsah na základě trendů, minulého výkonu, dotazů publika a
expertizy tvůrce. Udržuj backlog nápadů a přemýšlej od začátku napříč
platformami.

## Výstupní struktura

### Datové soubory
```
memory/content-ideas.json       # Scored idea backlog
memory/content-log.json         # Published content tracker
```

### Formát výstupu
```
/documents/{project-slug}/content/
├── ideation-{YYYY-MM-DD}.md    # Ideation session output
└── content-backlog.md           # Current prioritized backlog
```

## Šablona nápadu

Každá myšlenková relace produkuje přesně tento výstup:

```markdown
# Content Ideas — {YYYY-MM-DD}

**Creator:** {Name}
**Niche:** {Primary niche}
**Ideas generated:** {N}
**Top picks:** {N with score 4.0+}

---

## Top Ideas (Score 4.0+)

### 1. {Title} — Score: {X.X}

**Hook:** "{First line that stops the scroll}"

**Why this works:** {One sentence — what makes this idea uniquely valuable}

**Scoring:**
| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Audience Demand | {1-5} | {Why this score} |
| Expertise | {1-5} | {Why this score} |
| Timeliness | {1-5} | {Why this score} |
| Repurpose Potential | {1-5} | {Why this score} |
| Unique Angle | {1-5} | {Why this score} |

**Cross-Platform Plan:**
| Platform | Format | Angle |
|----------|--------|-------|
| {Platform 1} | {Format} | {How it adapts} |
| {Platform 2} | {Format} | {How it adapts} |
| {Platform 3} | {Format} | {How it adapts} |

**Source:** {What triggered this idea — analytics, question, trend, conversation}

---

### 2. {Title} — Score: {X.X}
...

---

## Backlog Updates

**Added:** {N new ideas}
**Promoted:** {Ideas moved to "in progress"}
**Pruned:** {Ideas removed and why}
```

## Kdy použít

- Tvůrce se ptá "o čem bych měl psát?" nebo "Potřebuji nápady"
- Během týdenních relací plánování obsahu
- Když je téma trendy ve výklenku tvůrce
- Během heartbeatů při označování potenciálních úhlů obsahu
- Když otázky publika odhalí mezery v obsahu

## Struktura datového souboru

Udržujte nápady v `memory/content-ideas.json`:

```json
{
  "ideas": [
    {
      "id": 1,
      "title": "Why most tutorial videos fail (and how to fix yours)",
      "hook": "I analyzed my 50 best and worst performing tutorials. The pattern is embarrassingly obvious.",
      "source": "analytics-review",
      "platforms": ["youtube", "twitter-thread", "blog"],
      "score": 4.2,
      "scoring": {
        "audienceDemand": 5,
        "expertise": 4,
        "timeliness": 3,
        "repurposePotential": 5,
        "uniqueAngle": 4
      },
      "status": "idea",
      "addedDate": "2025-01-15",
      "notes": "Based on real data. Could include screenshots."
    }
  ],
  "lastBrainstorm": null
}
```

## Bodovací systém

Ohodnoťte každý nápad 1–5 v pěti dimenzích. Průměr pro konečné skóre.

| Rozměr | 5 (Výborně) | 3 (průměr) | 1 (chudý) |
|-----------|---------------|-------------|----------|
| **Poptávka publika** | Lidé toto aktivně hledají/asking | Obecný zájem, nikoli naléhavý | Tohle nikdo nehledá |
| **Odbornost** | Tvůrce má jedinečná data nebo hluboké zkušenosti | Tvůrce téma dobře zná | Tvůrce by hádal |
| **Včasnost** | Trendy právě teď NEBO nadčasový evergreen | Relevantní, ale ne naléhavé | Okamžik uplynul |
| **Potenciál opětovného použití** | 5+ kusů napříč platformami snadno | 2-3 kusy s námahou | Jednorázový obsah |
| **Unikátní úhel** | Nikdo jiný nemá toto take/data | Poněkud diferencovaný | Všichni to říkají |

### Hranice skóre
- **4.0+** = Udělejte to do 7 dnů. Vysoká priorita. Okamžitě přiřadit do kalendáře.
- **3,0–3,9** = Solidní nápad. Plán do 2-4 týdnů.
- **2,0-2,9** = Vyžaduje lepší úhel, načasování nebo hák. Zaparkuj to.
- **Pod 2.0** = Zabijte jej nebo uložte pouze v případě, že by jej mohl oživit konkrétní spouštěč.

## Ideový proces

### 1. Shromážděte vstupy

Před generováním nápadů zkontrolujte:
- sdílené dokumenty/wiki – nejvýkonnější vzorce obsahu, statistiky publika
- `memory/content-log.json` – co bylo nedávno publikováno (vyhněte se opakování do 60 dnů)
- `USER.md` – nika, témata, publikum, hlas značky
- Nedávné rozhovory – cokoliv, co tvůrce zmínil, je zajímavé
– Populární témata ve svém výklenku (pokud jsou dostupná)
- `MEMORY.md` pouze v případě, že se jedná o trvalý pracovní prostor, který zachovává kurátorský překryv

### 2. Generování nápadů

Zaměřte se na 10 syrových nápadů. Kvalita před chytrostí. Každý nápad potřebuje:
- Pracovní název (konkrétní, ne vágní)
- Háček (první řádek, který někoho přiměje přestat rolovat)
- Na jaké platformy se hodí
- Proč by to fungovalo (to "tak co")

**Zdroje nápadů, které trvale produkují vítěze:**
- Problémy, které tvůrce nedávno vyřešil (vysoká odbornost + jedinečný úhel pohledu)
- Otázky, které si publikum neustále klade (vysoká poptávka)
- Contrarian přijímá populární rady ve výklenku (vysoký jedinečný úhel)
- Osobní příběhy s ponaučením (vysoký potenciál opětovného použití)
- Data/results ze skutečných zkušeností (ve své podstatě jedinečné)
- "Věci, které bych si přál vědět, když jsem začínal X" (vysoká poptávka + odbornost)
- Reakce na trendy novinky/discourse ve výklenku (vysoká aktuálnost)
- Zákulisí procesu tvůrce (vysoký jedinečný úhel)
– Srovnání a rozdělení „X vs Y“ (vysoká poptávka)
- Chyby a selhání (vysoká angažovanost – vždy fungují)

**Vzorce názvů, které fungují:**
- "Proč je [běžný přístup] špatný (a co dělat místo toho)"
- "Udělal jsem X] na [čas]. Tady je to, co se stalo."
- "[Počet] [věcí], které jsem se naučil z [konkrétní zkušenosti]"
- "Průvodce [přídavné jméno] k [tématu] (o kterém nikdo nemluví)"
- "Jak [konkrétní osoba/company] [dosáhl výsledku]"

### 3. Skóre a pořadí

Ohodnoťte každý nápad pomocí 5 dimenzí. Seřadit podle skóre. Prezentujte top 5 pomocí háčků.

### 4. Úhly napříč platformami

U každého nejlepšího nápadu načrtněte, jak žije na každé platformě:

| Platforma | Formát | Úhel | Úsilí |
|----------|--------|-------|--------|
| YouTube | 10minutové video | Celý tutoriál se záznamem obrazovky | Vysoká |
| Twitter/X | Vlákno (8 tweetů) | Verze s rychlými tipy se snímky obrazovky | Střední |
| Newsletter | Sekce funkcí | Osobní příběh + lekce | Střední |
| Blog | Dlouhý příspěvek | Hluboký ponor optimalizovaný pro SEO | Vysoká |
| Instagram | Kolotoč (10 snímků) | Vizuální shrnutí klíčových bodů | Střední |
| LinkedIn | Textový příspěvek | Profesionální úhel, zaměřený na výsledky | Nízká |
| TikTok/Reels | Video ze 60. let | Háček + 3 rychlé odběry | Střední |

### 5. Uložit a sledovat

- Přidejte bodované nápady do `memory/content-ideas.json`
- Aktualizujte stav, jak se nápady pohybují v kanálu: `idea` → `planned` → `in-progress` → `published`
- Když je nápad publikován, přesuňte jej do `memory/content-log.json`
- Během týdenních recenzí znovu vynořte nápady s vysokým skóre, které nebyly použity
- Oříznout nápady starší než 90 dní bez akce (zkontrolovat, obnovit nebo odstranit)

## Pravidla

- Nikdy nenavrhujte nápady mimo výklenek tvůrce, pokud nepožadují experimenty.
- Háčky jsou důležitější než témata. Skvělý háček na nudné téma poráží nudný háček na skvělé téma.
– Pokud má tvůrce data (analytika, osobní výsledky, experimenty), vždy navrhujte obsah založený na datech. Je to ze své podstaty jedinečné.
- Nenavrhujte, co všichni ostatní zveřejňují. Hodnota je v jedinečném úhlu.
- Evergreen obsah má vyšší skóre než reaktivní obsah, pokud trend není masivní.
- Udržujte nevyřízené položky. Nápady starší než 3 měsíce bez akce by měly být zkontrolovány a buď obnoveny, nebo odstraněny.
– Když se tvůrce mimochodem zmíní o něčem zajímavém („Právě jsem přišel na to, proč moje poslední video propadlo“), okamžitě to označte jako nápad na obsah.
- Nikdy neprezentujte více než 5 nápadů najednou. Overwhelm zabíjí akci.
- Každý nápad musí mít háček. Žádný háček = není připraven k prezentaci.

## Workflow

1. **Shromážděte vstupy** – Načtěte `content-log.json`, `USER.md`, nedávné konverzace, relevantní sdílené dokumenty a výsledky wiki/memory, abyste porozuměli výklenku tvůrce, publiku a minulému výkonu. Používejte `MEMORY.md` pouze jako volitelný kurátorský překryv v perzistentních pracovních prostorech na úrovni C.
2. **Generujte nezpracované nápady** — Brainstormujte 10+ nápadů z ověřených zdrojů: vyřešené problémy, dotazy publika, protichůdné názory, osobní příběhy, data/results a trendy témata.
3. **Skóre a hodnocení** — Ohodnoťte každý nápad v 5 dimenzích (poptávka publika, odbornost, aktuálnost, potenciál opětovného použití, jedinečný úhel) pomocí stupnice 1–5; vypočítat průměrné skóre.
4. **Vyberte nejlepší nápady** — Vyberte 5 nejlepších nápadů (skóre 4,0+) a ke každému napište působivý háček.
5. **Plánujte úhly napříč platformami** – U každého nejlepšího nápadu zmapujte, jak se přizpůsobí YouTube, Twitter/X, Newsletter, Blog, Instagram, LinkedIn a TikTok/Reels.
6. **Uložit a prezentovat** — Přidejte ohodnocené nápady do `memory/content-ideas.json`, vygenerujte výstup myšlenkové relace a prezentujte 5 nejlepších s háčky tvůrci.
7. **Udržování nevyřízených věcí** – Aktualizujte stavy nápadů (idea/planned/in-progress/published), ořezejte nápady starší než 90 dní a obnovte nepoužité nápady s vysokým skóre během týdenních recenzí.

## Decision Criteria

| Stav | Práh | Akce |
|-----------|-----------|--------|
| Skóre nápadu | 4,0+ průměr v 5 dimenzích | Plán do 7 dnů; okamžitě přiřadit do kalendáře |
| Skóre nápadu | Pod 2,0 | Zabijte nápad nebo jej uložte pouze v případě, že by jej mohl oživit konkrétní spouštěč |
| Nevyřízená zatuchlost | Nápad starší než 90 dní bez akce | Zkontrolujte, obnovte nebo odstraňte během týdenní kontroly |
| Duplicitní kontrola | Stejné téma zveřejněné za posledních 60 dní | Odmítnout; najít nový úhel nebo odložit |
| Prezentační limit | Maximálně 5 nápadů na relaci | Omezte nápady s nižším skóre, abyste se vyhnuli přehlcení |

## Anti-patterns

| ne | Proč | Místo toho |
|-------|-----|---------|
| Navrhujte obecná populární témata, která nesouvisejí s nikým tvůrcem | Obecné nápady oslabují autoritu značky a matou publikum – následovníci přišli pro konkrétní odbornost | Každý nápad se musí spojit se zdokumentovaným výklenkem tvůrce, jeho odborností nebo otázkami publika |
| Prezentujte nápady bez háčků | Téma bez háčku je jen kategorie — nedává tvůrci nic pro začátek a nezastaví svitek | Každý nápad musí obsahovat konkrétní, napsaný první řádek/hook před prezentací |
| Ohodnoťte všechny rozměry stejně vysoko, aby nápady vypadaly dobře | Nafouknuté skóre ničí systém hodnocení — vše vypadá jako 4,5 a skuteční vítězové jsou pohřbeni | Bodujte poctivě s odůvodněním pro každou dimenzi; a 2 na Časovost je v pořádku, pokud jsou ostatní dimenze silné |
| Navrhněte více než 15 nápadů v jedné relaci | Overwhelm zabije akci — tvůrce nevybere nic, když má příliš mnoho možností | Prezentujte max. 5 bodovaných nápadů; ponechat doplňky v nevyřízeném záznamu pro budoucí sezení |
| Recyklovat téma publikované za posledních 60 dní | Diváci si rychle všimnou opakování a při opakovaných úhlech zapojení klesá | Před prezentací zkontrolujte content-log.json; pokud podobné téma existuje do 60 dnů, najděte nový úhel pohledu nebo odložte |

## Integrace

**Použití:**
- `seo-strategy` – údaje o poptávce po klíčových slovech informují o dimenzi skóre poptávky publika
- Nástroje nativní paměti/wiki plus sdílené dokumenty – získávejte data o minulém výkonu, statistiky publika a kontext tvůrců
- `content-calendar-manager` — zkontrolujte existující kalendář, abyste předešli konfliktům v plánování

**Použito:**
- `content-calendar-manager` – nejlépe hodnocené nápady se přidávají přímo do kalendáře publikování
- `email-campaigns` — obsah newsletteru čerpaný z nevyřízeného bodovaného nápadu
- `multichannel-publisher` — multiplatformní plán ze strategie vydávání příruček nápadů
- `creative-director` – nápady na obsah kampaně tvoří podklady pro kreativní podklady

## Quality Checklist

Před prezentací jakékoli myšlenky:

- [ ] Alespoň 10 nezpracovaných nápadů vytvořených před bodováním
- [ ] Každý prezentovaný nápad má specifický háček (nejen téma)
- [ ] Skóre zahrnuje zdůvodnění pro jednotlivé dimenze (nejen čísla)
- [ ] Žádná duplicitní témata z posledních 60 dnů publikovaného obsahu
- [ ] Plán pro více platforem je zahrnut pro všechny nápady 4.0+
- [ ] Nápady jsou specifické pro výklenek a hlas tvůrce
- [ ] Alespoň 1 nápad založený na datech, pokud má tvůrce analytics/results
- [ ] Backlog aktualizován v `memory/content-ideas.json`
- [ ] Zastaralé nápady (více než 90 dní) označené ke kontrole nebo prořezání
