# Product Intelligence Board — spec

Produktová konkurenční intel spuštěná **názvem produktu**. Killer feature pro e-shopy. **Golden pár** (reálná data, renderer-generovaný): vstup `{baseDir}/assets/board-example-report.json` → výstup `{baseDir}/assets/board-template.html` (Dyson V15 Detect Absolute, klient roboticky-vysavac.cz; 6 sekcí + 6 námětů, sanitizováno). Vyrenderuješ přes `python3 {baseDir}/scripts/board.py <report.json> <out.html>`.

## Kdy se spouští

Osa = **název produktu**, ne téma. Trigger = produktově vypadající dotaz: konkrétní název produktu, kategorie produktu, nebo produkt z Product DNA klienta při chystání kampaně. Ne B2B/B2C — rozhoduje tvar dotazu.

## Sekce (a jak se skórují)

| # | Sekce | Vstup | Logika |
|---|---|---|---|
| — | **Hlava** | Heureka produkt | Foto + hodnocení (%) + počet recenzí + počet obchodů. KPI: nejnižší cena/obchod · vaše cena + cenový index · pozice v žebříčku · počet cenopádů 30 d. |
| 01 | **Cenová mapa** | Heureka nabídky | Žebříček obchodů podle **landed = cena + doprava** (ne sticker!). Označ MIN (nejlevnější), klienta (VY), cenopády. Bar = relativní landed. |
| 02 | **Živé signály** | denní snímky | **Cenopád** (kdo dnes zlevnil o kolik) + **out-of-stock trigger** (konkurent vyprodán → klient skladem = zvedni bid / spusť kampaň). Out-of-stock = **nejakčnější**, přímo generuje tržbu. |
| 03 | **Recenze → náměty do reklam** | Heureka recenze | Strukturované +/− (chvála/stížnost) → **náměty do reklam** (model, viz níže). |
| 04 | **Sortiment — díra** | Heureka varianty | Které varianty konkurence prodává a klient **nemá v katalogu** = doložená poptávka. |
| 05 | **Google — kdo se zobrazí** | Google SERP CZ | Organický žebříček (kdo se zobrazuje zdarma) + placené (kdo bidují na produkt) + AI Overview (koho cituje). |
| 06 | **Reklamní aktivita (Meta)** | Meta Ad Library | Kdo jede na produkt/značku reklamy a **jak dlouho** (doba běhu = winner proxy). Počet aktivních reklam. **Inzerent-level.** |
| → | **Akční plán** | syntéza | 3–4 konkrétní tahy z výše uvedeného (model). |

## Scoring / odvozené signály

- **Landed price** = cena + doprava (dopočti z Heureka nabídky; doprava zdarma od částky → zohledni práh). Bez landed je srovnání zavádějící — **musí být**.
- **Cenový index** = `round(vaše_landed / medián_landed * 100)` %. Agregát přes celý katalog = manažerský pohled (dělá z nástroje board, ne tabulku).
- **Cenopád** = pokles ceny obchodu proti předchozímu snímku (derived, $0). „≥3 obchody dolů = cenová válka."
- **Pozice** = rank klienta v žebříčku landed.
- **Winner proxy (Meta)** = délka běhu nejstarší aktivní reklamy inzerenta (dlouho běží = performuje).

## Náměty do reklam (Krok 6 — práce modelu, ne scriptu)

Pro každý silný recenzní signál vyrob objekt:
```json
{"headline":"reálný text do reklamy",
 "mechanism":"námitka → servis | cena → důkaz zákazníků | dlouhověkost | estetika/identita",
 "source":"z které recenze to vychází (doslovná citace zákazníka)",
 "why":"proč to funguje (1 věta)"}
```
Pravidla:
- **Nejčastější stížnost = nejsilnější námět.** Proměň ji ve **servis** (poradenství, výměna), ne ve slevu — odliší klienta a nesáhne na marži.
- **Chvála → důkaz.** Cenová námitka se vyvrací slovy zákazníků, ne diskontem.
- **Pozor na slabinu produktu:** stížnost na samotný produkt (ne na obchod) **neslibuj opačně** — směřuj na výměnu/poradenství. (Např. „suchý zip po čase povoluje" → neslibuj „zip, co nepovolí"; nabídni výměnu.)
- **Doslovný jazyk zákazníka** (Raw Diet) — cituj, jak to napsali, ne učesaná parafráze.
- Veď **jedním** námětem (ten z nejčastější stížnosti) a zbytek nabídni jako A/B.

## Fable pasti (kritické — bez nich board lže)

1. **EAN product matching** — bez EAN je párování „můj produkt ↔ Heureka karta" fuzzy → board lže. Párovat přes EAN z feedu klienta; jinak jednorázové potvrzení matche.
2. **Varianty** (10 oz vs 12 oz, barva) — srovnání jiné varianty = falešný cenopád. Vždy stejná varianta.
3. **Heureka pořadí = biddované (CPC)**, ne organické → neinterpretovat jako kvalitu.
4. **GDPR** — recenze bez jmen autorů.
5. **Freshness** — denní snímek stačí, **neprodávat real-time**.
6. **Meta = inzerent-level**, ne přesný produkt (product-level DPA nespolehlivé) — popiš jako „inzerenti, kteří jedou na značku/sortiment".

## ⚖️ Sourcing vs. databázová práva

Srovnávač (Heureka) **ZŮSTÁVÁ jádro** — jeden scrape dá všechny nabídky na produkt; scrapovat každý e-shop zvlášť je horší (víc webů, víc expozice, víc práce). Databáze je ale chráněná (sui generis), takže riziko držíme přes *jak a kolik*: **jen per-produkt na vyžádání** (nepodstatná část), **nikdy hromadně katalog**, **nikdy neukládej/neredistribuuj jejich agregaci jako data** (jen insight pro klienta); přes Apify. Reklamní knihovny (Meta/Google) = veřejné registry, nízké riziko. Plný rozbor: `data-sources.md`.

## NEDÁVAT (zbožné přání, zničí důvěru)

Zboží.cz (aktor neexistuje) · product-level Meta DPA matching · odhad obratu/spendu konkurence (věštění) · Google Trends per-produkt v CZ (šum, jen kategorie).

## Advanced v2 (roadmapa, ne teď)

Google Shopping PLA (kdo je v aukci) · Hlídač shopů (fake slevy u velkých) · Allegro EAN + sales-velocity (proxy reálných prodejů).

## Česká copy pravidla (klientský výstup)

- **Vykání.** Žádné vendor/aktor jména, skóre, skill názvy, „druhý mozek". „Monitorujeme trh", ne „scrapujeme Heureku".
- **Minimum anglicismů:** landed price → „cena včetně dopravy" / „celkem"; ad angle → „námět do reklamy"; hook → „námět"; free shipping → „doprava zdarma"; snapshot → „snímek"; board → „přehled" (v klientské řeči).
- **Loga obchodů** = favicona z domény (Google `s2/favicons` → DuckDuckGo `ip3` jako fallback dává iniciálu místo glóbu). Reálný Heureka scrape logo obchodu nese taky.
- **Vizuál:** velký gradientní nadpis (masthead) + „REÁLNÁ DATA" pill, sekce vedené velkým číslem bez oddělovačů, pozadí = 3 radiální gradienty (CC redesign 2.0). Design tokeny v templatu.
