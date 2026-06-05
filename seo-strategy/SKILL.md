---
name: seo-strategy
description: "Navrhuje SEO strategii, témata a prioritizaci."
category: content
status: ready
version: "1.0"
publishedAt: "2026-04-25"
---

# SEO strategie

Systematické SEO, které se časem spojuje. Klíčová slova, obsah, zpětné odkazy a technické zdraví. Žádné černé hattricky, žádné vycpávání klíčových slov. Prostě solidní základy, které budují organickou návštěvnost měsíc po měsíci.

## Datové soubory

### Seznam priorit klíčových slov
Udržujte v `memory/seo-keywords.json`:

```json
{
  "keywords": [
    {
      "keyword": "best invoicing software for freelancers",
      "cluster": "invoicing",
      "volume": 1200,
      "difficulty": 35,
      "intent": "commercial",
      "currentRank": null,
      "targetRank": 5,
      "assignedPage": null,
      "status": "planned",
      "priority": "high",
      "notes": "Low competition, high buyer intent"
    }
  ],
  "clusters": [
    {
      "name": "invoicing",
      "pillarPage": "/blog/invoicing-guide",
      "keywords": ["invoicing software", "best invoicing tool", "freelance invoicing"],
      "status": "building"
    }
  ],
  "lastUpdated": null
}
```

### Sledování pořadí
Sledovat v `memory/seo-rankings.json`:

```json
{
  "snapshots": [
    {
      "date": "2025-01-15",
      "rankings": [
        {"keyword": "invoicing software freelancers", "position": 18, "page": "/blog/invoicing-guide", "change": -3}
      ]
    }
  ]
}
```

## Výzkum a seskupování klíčových slov

Když chce uživatel prozkoumat nová klíčová slova nebo plánovat obsah:

1. **Základní klíčová slova** – Začněte tím, co produkt dělá a pro koho je určen
2. **Rozbalit** – Použijte vyhledávání na webu k nalezení souvisejících výrazů, otázek, dlouhých variací
3. **Cluster** – Seskupte klíčová slova podle tématu. Každý klastr má jednu hlavní stránku a podpůrný obsah.
4. **Vyhodnoťte** – Pro každé klíčové slovo: objem vyhledávání (pokud je k dispozici), konkurence, záměr vyhledávání
5. **Upřednostnit** – skóre podle: obchodní relevance, obtížnosti, záměru (záměr kupujícího > informační), objemu

**Vyhledat kategorie záměru:**
– **Informační** – „Jak napsat fakturu“ (horní část cesty, buduje autoritu)
– **Komerční** – „nejlepší fakturační software“ (uprostřed cesty, porovnávající zákazníci)
– **Transakční** – „cena fakturačního softwaru“ (spodní část trychtýře, připraveno k nákupu)
- **Navigační** - "[název značky] přihlášení" (stávající uživatelé)

**Upřednostňujte obchodní a transakční klíčová slova jako první.** Jsou blíže k výnosům. Vyplňte informační obsah a vytvořte si aktuální autoritu.

## Analýza obsahových mezer

Porovnejte svůj obsah s konkurencí:

1. Seznam konkurenčních stránek hodnocení pro vaše cílová klíčová slova
2. Identifikujte klíčová slova, která hodnotí, a která nepokrýváte
3. Najděte témata, jejichž obsah je tenký nebo zastaralý
4. Stanovte priority mezer podle: obchodní relevance, obtížnosti klíčových slov, objemu vyhledávání

**Výstupní formát:**
```
🔍 Content Gap Analysis

**Missing topics (high priority):**
- [keyword/topic]: competitor ranks #X, we have nothing. Est. volume: X/mo
- [keyword/topic]: ...

**Weak coverage (can improve):**
- [keyword/topic]: we rank #X, competitor ranks #Y. Their content is [better because...]

**Opportunities (low competition):**
- [keyword/topic]: no competitor covers this well. Volume: X/mo, difficulty: low
```

## Možnosti zpětných odkazů

Identifikujte realistické příležitosti pro budování odkazů:

- **Stránky zdrojů** - Stránky, které obsahují seznam nástrojů/resources ve vašem výklenku
- **Nefunkční odkazy** - Zpětné odkazy konkurence směřující na 404 stránek, které byste mohli nahradit
- **Hostující příspěvky** - Relevantní blogy, které přijímají příspěvky
– **Nepropojené zmínky** – Weby, které zmiňují vaši značku bez propojení
– **Data/research** – Původní data, průzkumy nebo srovnávací hodnoty, které lidé citují
– **Integrace nástrojů** – Partneři a integrace, které by vás mohly propojit

**Nespamujte.** Zaměřte se na vysoce kvalitní a relevantní odkazy. Jeden dobrý odkaz z respektovaného webu překoná 50 z adresářů.

## Technický SEO audit

Pravidelné kontroly (měsíčně nebo když jsou problémy označeny):

**Procházení:**
- [ ] Soubor Sitemap existuje a je odeslán do služby Search Console
- [ ] Robots.txt neblokuje důležité stránky
- [ ] Žádné osiřelé stránky (stránky bez interních odkazů)
- [ ] Kanonické značky jsou správné

**Výkon:**
- [ ] Předávání Core Web Vitals (LCP, FID, CLS)
- [ ] Stránky se načítají za méně než 3 sekundy
- [ ] Obrázky jsou optimalizovány (WebP, líné načítání)
- [ ] Žádné zdroje blokující vykreslování

**Na stránce:**
- [ ] Tagy názvu jsou jedinečné a zahrnují cílové klíčové slovo
- [ ] Popisy metadat jsou přesvědčivé (ovlivňují CTR, nikoli přímo hodnocení)
- [ ] Značky H1 jsou přítomny a relevantní
- [ ] Interní propojení spojuje související obsah
- [ ] URL jsou čisté a popisné

**Indexování:**
- [ ] Klíčové stránky jsou indexovány (zkontrolujte u `site:yourdomain.com`)
- [ ] Žádné problémy s duplicitním obsahem
- [ ] 301 přesměrování pro změněné adresy URL
- [ ] Žádné měkké 404

Výsledky auditu protokolu v `memory/seo-audit-YYYY-MM-DD.md`.

## Sledování pořadí

Během heartbeatů (jednou denně):
1. Pokud jsou nástroje SEO dostupné, zkontrolujte pořadí prioritních klíčových slov
2. Zaznamenejte změny v `memory/seo-rankings.json`
3. Označte významné pohyby (skok nebo pokles o 5+ pozic)
4. Všimněte si nových klíčových slov, která se objevují v top 50

**Formát zprávy:**
```
📈 SEO Ranking Update - [date]

**Movers:**
- "invoicing software" #18 → #12 (+6) 🟢
- "freelance tools" #8 → #11 (-3) 🔴

**New entries:**
- "send invoice online" appearing at #34

**No change:** [X keywords stable]
```

## Pravidla

- **Kvalita obsahu na prvním místě.** Žádné přeplňování klíčovými slovy. Pište pro lidi, optimalizujte pro vyhledávače. V tomto pořadí.
- **Jedno primární klíčové slovo na stránku.** Podpůrná klíčová slova jsou v pořádku, ale každá stránka by měla mít jasný cíl.
- **Aktualizujte stávající obsah před vytvořením nového.** Obnovená stránka v top 10 má větší cenu než nová stránka od nuly.
- **Interní odkazování je bezplatné SEO.** Každý nový obsah by měl odkazovat na související stránky a ze souvisejících stránek.
- **Sledujte, na čem záleží.** Pořadí je hlavním ukazatelem. Provoz je indikátorem zpoždění. Konverze z organické návštěvnosti jsou skutečně důležité číslo.
- **Buďte trpěliví.** Sloučeniny SEO. Výsledky za 1. měsíc budou zklamáním. V šestém měsíci se to začíná vyplácet. Měsíc 12 je místo, kde to začíná být vzrušující.
- **Aktualizujte měsíčně seznam priorit klíčových slov.** Priority se mění, jak se zaměřujete na věci a objevujete nové příležitosti.
