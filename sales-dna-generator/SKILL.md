---
name: sales-dna-generator
description: "Vytvoří s vámi prodejní playbook (Sales DNA) v řízeném rozhovoru — ptá se jen na to, co nejde vyčíst z Brand a Product DNA: jak prodáváte, ceny a kotvy, námitky, provozní pravidla. Odpověď „nevím“ je v pořádku, doplní se ověřené výchozí hodnoty. Výstup: /documents/sales/salesDNA.md — playbook, podle kterého hraje celý prodejní tým i AI Sales Stratég."
category: sales
status: ready
version: "1.0"
publishedAt: "2026-08-26"
metadata: {"openclaw":{"requires":{"bins":["python3"]},"emoji":"📖"}}
---

# Sales DNA Generator

## ⚠️ Povinný postup (pro vykonávajícího agenta — čti jako první)

Tento skill **musí** projít kroky 0 → 1 → 2 (✋ STOP) → 3 → 4 **v pořadí**. Je to konverzační onboarding bez externího API a bez credentialů. Lokální helper `{baseDir}/scripts/write_sales_dna.py` zajišťuje pouze zamčený, atomický a obnovitelný draft/publish. Výstupem je jediný kanonický soubor: `/documents/sales/salesDNA.md`.

**Zásada č. 1: neptej se na nic, co už víš.** Před rozhovorem načti existující podklady (Krok 0). Otázky pokládej jen k tomu, co v nich chybí. Uživatel nesmí odpovídat dvakrát na totéž.

**Zásada č. 2: „nevím" je platná odpověď.** Nikdy netlač na uživatele, aby si vymýšlel. Doplň ověřenou výchozí hodnotu z šablony a označ ji `[výchozí]` — uživatel tak později vidí, co může doladit.

**Zásada č. 3: klient nic nepíše.** Ty se ptáš, ty píšeš, on odpovídá a schvaluje.

## Co tento skill dělá pro váš byznys

Prodejní know-how vaší firmy dnes žije v hlavách. Tento skill ho v jednom rozhovoru (zhruba 20–30 minut) přenese do **prodejního playbooku — Sales DNA**. Podle něj pak hraje celý AI prodejní tým: Stratég z něj čte provozní pravidla, Sales Assistant argumenty a námitky, Mentor kritéria a váhy hodnocení hovorů (sekce 6), Analytik z hodnocení učí firmu (sekce 10).

1. **„Každý obchodník to říká jinak."** Playbook sjednotí metodiku, kotvy i odpovědi na námitky.
2. **„Nemám čas sepisovat dokumenty."** Odpovídáte na otázky, dokument vzniká sám.
3. **„Nevím, jaká pravidla nastavit."** Kde si nejste jistí, doplní se ověřené výchozí hodnoty.

## Jak skill pracuje — 5 kroků s 1 zastávkou

### Krok 0 — Načtení podkladů (tiše)

1. Nejprve spusť `python3 {baseDir}/scripts/write_sales_dna.py status`. Pokud vrátí `status: draft`, načti uvedený `draftPath` a pokračuj od prvního chybějícího čísla v `completedBlocks`; nezačínej rozhovor znovu. Potom načti, co existuje: `/documents/brand/brandDNA.md`, `/documents/brand/companyDNA.md`, všechny `/documents/brand/products/*/productDNA.md`, ceníky a web (pokud jsou v podkladech).
2. Zkontroluj, jestli už `/documents/sales/salesDNA.md` existuje — pokud ano, přepni do **režimu aktualizace** (projdi jen sekce, které chce uživatel měnit; zbytek nech).
3. Načti šablonu `{baseDir}/references/salesdna-sablona.md` a otázky `{baseDir}/references/otazky-onboarding.md`.
4. Pokud chybí Brand DNA nebo Product DNA, upozorni: *„Doporučuji nejdřív vytvořit Brand DNA / Product DNA (přes příslušné generátory) — Sales DNA na ně navazuje. Můžeme ale pokračovat i bez nich."* Neblokuj.
5. Z productDNA si vypiš seznam produktů — budeš ho potřebovat pro per-produktové podsekce.

### Krok 1 — Řízený rozhovor (6 bloků)

Postupuj po blocích podle `{baseDir}/references/otazky-onboarding.md`. Pravidla vedení rozhovoru:

- **Jeden blok = jedna zpráva** s 2–4 otázkami. Neptej se na všechno najednou.
- Před otázkou řekni, co už víš z podkladů, a nech si to jen potvrdit: *„Z Product DNA vidím, že prodáváte X za Y Kč — sedí to?"*
- U bloků **Ceny** a **Námitky** projdi otázky **per produkt** (pokud je produktů víc). Když má klient produktů hodně (e-shop), ptej se per kategorie a na katalog použij Google Shopping feed (blok 4).
- Odpověď „nevím" / „nemáme" → doplň `[výchozí]` hodnotu ze šablony a řekni to nahlas: *„Dám tam zatím ověřené výchozí nastavení (180 dní), kdykoli to změníme větou."*
- Pokud jsou v `/documents/` přepisy reálných obchodních jednání, můžeš bloky 4 a 5 předvyplnit z nich a nechat si je jen potvrdit.
- Po dokončení každého bloku 1–6 vykresli dosavadní celý dokument do dočasného souboru a ulož obnovitelný checkpoint: `python3 {baseDir}/scripts/write_sales_dna.py draft --input /tmp/salesDNA-current.md --completed-block <1-6>`. Helper pod zámkem atomicky aktualizuje `/documents/sales/.sales-dna-draft.md` a stav s přesnou `skillVersion: "1.0"`.

### Krok 2 — Návrh Sales DNA ✋ STOP

Sestav kompletní `salesDNA.md` podle šablony (11 sekcí, per-produktové podsekce tam, kde se produkty liší), ulož poslední draft přes helper a ukaž uživateli **shrnutí po sekcích** (ne celý soubor najednou) + počet hodnot označených `[výchozí]`.

**✋ STOP** — *„Souhlasíte s tímto playbookem? (ano / upravit sekci X / projít znovu blok Y)"*. Bez výslovného souhlasu neukládej.

### Krok 3 — Uložení

1. Až po výslovném „ano" publikuj přes `python3 {baseDir}/scripts/write_sales_dna.py publish --input /documents/sales/.sales-dna-draft.md --approved yes`. Helper ověří, že vstup odpovídá poslednímu uloženému draftu, pod zámkem vytvoří kolizně bezpečnou zálohu a atomicky nahradí `/documents/sales/salesDNA.md`. Nikdy finální soubor ani zálohu nezapisuj ručně.
2. Do sekce 10 (Ověřené poznatky) zapiš první řádek changelogu: `[datum] v1 — vytvořeno onboarding rozhovorem`.
3. Soubor v `/documents` je zdroj pravdy; do LLM wiki se dostane synchronizací AI Data Centra. Skill sám žádnou synchronizaci nevolá — nenabízej ji jako krok.
4. V task módu nastav přes task API metadata `contract: "sales-dna-generator:sales-dna"` a `contractParams: {}`. Do review přejdi až po úspěšném atomickém publish; checkpoint vyžaduje přesnou `skillVersion: "1.0"`.

### Krok 4 — Co dál (doporučení)

Vypiš uživateli další kroky aktivace prodejního enginu:
1. Nastavit tagovou taxonomii v CliqSales workflows (`produkt:` / `zajem:` — podle sekce 9).
2. Aktivovat úlohy AI Sales Stratéga v Plánovači úkolů.
3. První pilotní reaktivační vlnu na malém segmentu.

## Antipatterns — co NEDĚLAT

| Antipattern | Proč je špatný | Co dělat místo toho |
|---|---|---|
| Ptát se na věci, které jsou v Brand/Product DNA | Uživatel odpovídá dvakrát, ztrácí důvěru | Krok 0: načti podklady, nech si je jen potvrdit |
| Vytvořit per-produkt soubory (salesDNA-produktX.md) | Rozbíjí konvenci JEDEN soubor; údržbové peklo | Per-produktové rozdíly = podsekce `### <produkt>` uvnitř sekcí |
| Nutit uživatele vymýšlet hodnoty („kolik dní je kontakt spící?") | Vymyšlená čísla jsou horší než výchozí | „nevím" → `[výchozí]` hodnota ze šablony |
| Uložit bez ✋ STOP schválení | Playbook řídí celý tým — nesmí vzniknout bez souhlasu majitele | Vždy shrnutí po sekcích + explicitní „ano" |
| Po přerušení začít onboarding znovu | uživatel odpovídá podruhé a vznikají dvě verze draftu | načti `write_sales_dna.py status` a pokračuj z atomického draftu |
| Přepsat `salesDNA.md` nebo backup ručně | souběh/pád může zničit poslední platnou verzi | výhradně `write_sales_dna.py publish --approved yes` |
| Vypsat celý soubor do chatu najednou | 11 sekcí = zeď textu, nikdo to nepřečte | Shrnutí po sekcích, detail na vyžádání |
| Zapisovat provozní data (kontakty, objednávky) do salesDNA | Sales DNA = pravidla a znalost; data žijí v CRM | Jen pravidla, kotvy, námitky, poznatky |

## Návaznost na další skilly

- **Čtou z výstupu:** `sales-strategist` (sekce 1, 2, 7, 8, 9), `sales-assistant` (1, 3, 4, 5, 8), `sales-mentor` (1, 5, 6), `sales-analytik` (1, 5, 6, 10), upsell (11), `sales-reactivator` (7, 9, 11)
- **Vstupy:** `brand-dna`, `product-dna` (pokud podklady chybí)

## Doplňkové soubory (reference)

- `{baseDir}/references/salesdna-sablona.md` — šablona 11 sekcí + výchozí hodnoty + vzor per-produktových podsekcí
- `{baseDir}/references/otazky-onboarding.md` — 6 bloků otázek s vazbou na sekce
