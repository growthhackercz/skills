---
name: trending-research
description: "Prozkoumejte trendový a vysoce výkonný obsah napříč kanály a vytvářejte strukturované briefy pro články a tvorbu obsahu."
category: analytics
status: ready
version: "1.0"
publishedAt: "2026-04-25"
---
# Trending Content Research Skill

Prozkoumejte a sestavte strukturované přehledy trendů, virů a vysoce výkonného obsahu. Výstupem je **research brief** — strukturovaný dokument navržený tak, aby jej mohl zkonzumovat následný agent nebo dovednost pro vytváření obsahu.

## Kdy použít

- Uživatel žádá o nalezení trendového nebo virálního obsahu v konkrétním výklenku
– Uživatel chce před napsáním článku nebo příspěvku na blog výzkumný materiál
- Uživatel potřebuje vědět, jaká témata jsou aktuálně v jeho oboru aktuální
– Uživatel říká „vyhledat článek“, „najdi mi populární témata“, „co se stalo virální“

## Jak to funguje

Tento skill funguje ve dvou fázích:

### Fáze 1: Objevování

Vyhledávejte populární a vysoce výkonný obsah z různých typů zdrojů:

1. **YouTube** – populární videa, vysoký počet zhlédnutí nedávno nahraných videí, virální krátké filmy
2. **News & Industry Sites** – nejnovější zprávy, myšlenkové vedení, oznámení
3. **Příspěvky a články na blogu** – virální příspěvky, články s vysokým zapojením, seznamy
4. **Sociální signály** – témata generující diskusi na X/Twitter, LinkedIn, Reddit

K nalezení obsahu použijte vyhledávání na webu. Proveďte **alespoň 5 vyhledávání** z různých úhlů:

- `[topic] trending 2026`
- `[topic] viral video youtube`
- `[topic] latest news`
- `[topic] most shared article`
- `[topic] reddit discussion`

Pro každý slibný výsledek načtěte celou stránku, abyste získali klíčové podrobnosti (název, autor, datum, hlavní body, metriky zapojení, pokud jsou viditelné).

### Fáze 2: Syntéza

Sestavte zjištění do **Research Brief** s použitím přesného výstupního formátu níže.

## Výstupní formát

Vždy vytiskněte jeden strukturovaný dokument v tomto formátu:

```
# RESEARCH BRIEF: [Topic/Niche]

**Generated:** [date]
**Niche/Industry:** [specified by user]
**Language for output article:** [as defined in soul.md or specified by user]

---

## 🔥 TOP TRENDING TOPICS

### Topic 1: [Title]
- **Why it's trending:** [1-2 sentence explanation]
- **Virality score:** [HIGH / MEDIUM / LOW] based on cross-platform presence
- **Content angle:** [suggested angle for an original article]
- **Key data points:** [statistics, quotes, facts worth mentioning]

### Topic 2: [Title]
...

(Include 3-7 topics, ranked by relevance and virality)

---

## 📺 YOUTUBE INSIGHTS

For each relevant video found:
- **Title:** [video title]
- **Channel:** [channel name]
- **Views:** [view count if available]
- **Published:** [date]
- **Key takeaway:** [1-2 sentences on what makes this video successful]
- **Content hook:** [what makes people click — the hook or angle]

(Include 3-5 videos)

---

## 📰 TOP ARTICLES & BLOG POSTS

For each relevant article:
- **Title:** [article title]
- **Source:** [publication/blog name]
- **Date:** [publication date]
- **Core argument:** [2-3 sentence summary]
- **Why it performs:** [what makes this piece shareable/engaging]
- **Unique angle:** [what sets it apart from other coverage]

(Include 3-5 articles)

---

## 💡 CONTENT OPPORTUNITIES

Based on the research above, identify gaps and opportunities:

1. **[Opportunity 1]:** [description — what's missing from aktuální coverage that an original article could fill]
2. **[Opportunity 2]:** ...
3. **[Opportunity 3]:** ...

---

## 🎯 RECOMMENDED ARTICLE BRIEF

Based on all findings, recommend the single best article to write:

- **Suggested title:** [compelling, click-worthy title]
- **Format:** [listicle / how-to / opinion / explainer / case study / roundup]
- **Target length:** [word count recommendation]
- **Core thesis:** [1 sentence — the main argument or value proposition]
- **Outline:**
  1. [Section 1]
  2. [Section 2]
  3. [Section 3]
  ...
- **SEO keywords:** [5-10 recommended keywords]
- **Sources to reference:** [list of sources from the research above]

---

## 📋 RAW SOURCES

| # | Type | Title | URL | Date |
|---|------|-------|-----|------|
| 1 | YouTube | ... | ... | ... |
| 2 | Article | ... | ... | ... |
| ... | ... | ... | ... | ... |
```

## Pravidla chování

1. **Na aktuálnosti záleží.** Upřednostněte obsah publikovaný během posledních 7–14 dnů. Starší obsah je relevantní pouze v případě, že dochází k jeho oživení.

2. **Ověření napříč platformami.** Téma populární na více platformách (YouTube + zprávy + sociální sítě) má vyšší skóre než jedno, které se objeví na jedné platformě.

3. **Zapojení nad autoritu.** Virální vlákno na Redditu nebo video na YouTube s neobvyklým nárůstem zapojení může být cennější než prestižní, ale málo angažovaná publikace.

4. **Respektujte mezeru.** Pokud uživatel zadá mezeru (např. „AI pro malé firmy“), musí být veškerý výzkum relevantní pro tuto mezeru. Nevracejte obecná populární témata.

5. **Jazykové povědomí.** Samotný výzkumný brief je vždy v angličtině. Sekce "Doporučený článek Stručný" by měla poznamenat cílový jazyk konečného článku (jak je definován uživatelem nebo jeho soul.md).

6. **Žádné halucinace.** Každý uvedený zdroj musí pocházet ze skutečného výsledku vyhledávání. Pokud nemůžete najít dostatek populárního obsahu, řekněte to – nevytvářejte si zdroje.

7. **Buďte přesvědčeni.** Sekce „Příležitosti k obsahu“ a „Doporučený článek Stručný“ by měly odrážet skutečný redakční úsudek. Nejen vypisovat – doporučovat.

## Okrajové pouzdra

– **Široké téma (např. „AI“):** Upřesněte tím, že požádáte uživatele o dílčí výklenek nebo publikum. Pokud žádná odpověď, vyberte 3 nejvýraznější dílčí úhly.
- **Nic trendy:** Upřímně oznamte, že výklenek je právě teď tichý. Místo toho navrhněte stálezelené úhly.
- **Neanglický výklenek:** Hledejte v cílovém jazyce i v angličtině. Všimněte si, které zdroje jsou v jakém jazyce.

## Poznámky k integraci

Tento skill vytváří stručný výzkum. Nepíše konečný článek. Zadání je navrženo tak, aby bylo předáno agentovi pro vytváření obsahu/skill jako vstup. Stručný popis obsahuje vše, co agent potřebuje: téma, úhel pohledu, zdroje, osnovu a klíčová slova.
