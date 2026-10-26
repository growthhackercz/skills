# Metodika výběru kandidátů — tiery, filtry, degradovaný režim

Skript `reactivation_candidates.py` čte VÝHRADNĚ snapshot stratéga. Parametry mu dosaď ze Sales DNA §7 (provozní pravidla) — hodnoty níže jsou `[výchozí]` pro případ, že v DNA nejsou.

## Segmenty (priorita A > C > B — kontakt jen v jednom)

| Segment | Podmínka | Tier hot | Tier warm |
|---|---|---|---|
| **A — prohrané obchody** | opportunity `lost` před 60–360 dny `[60/360]` | prohra ≤ 180 dní | prohra 181–360 dní |
| **C — spící zákazníci** | vyhraný obchod NEBO tag `produkt:*`, bez aktivity ≥ 180 dní `[180]` | nákup ≤ 18 měsíců | starší |
| **B — staré leady** | tag `zajem:*`, bez aktivity ≥ 180 dní | — | vše warm (tagy nemají čas) |

**⚠️ Cold start:** taxonomie `zajem:`/`produkt:` u klientů zprvu neexistuje — segment C drží na vyhraných obchodech, segment B bývá prázdný. Návrh vlny to říká narovinu.

## Tvrdé filtry (v pořadí, transparentně reportované)

1. DND → nikdy
2. karanténa: tag `reaktivace:RRRR-MM` mladší 6 měsíců `[6]`
3. touch-cap: tag `osloven:RRRR-MM-DD` mladší 14 dní `[14]` (sdílený strop dotyků napříč odchozími skilly)
4. bez e-mailu i telefonu
5. otevřený obchod (neoslovuj uprostřed dealu)
6. aktivní v posledních 30 dnech `[30]` (není spící)

Známé omezení v0.1: „aktivní konverzace" se z snapshotu nepozná — částečně kryje filtr 6 a živý re-check při odeslání.

## Degradovaný režim (automatická detekce)

Když < 30 % prohraných obchodů má vyplněný důvod prohry → režim „degradovaný": tiery jen z recency + hodnoty + historie nákupů a **otázka vlny spadne na generickou** („Ještě to řešíte?" místo důvodu prohry). Návrh vlny to musí uvést — majitel má vědět, že přesnost zvedne vyplňování důvodů prohry (vymáhá Sales Assistant).

## Pořadí do vlny

A-hot → C-hot → A-warm → C-warm → B. Engaged/hot kontakty jdou první i kvůli reputaci odesílatele. A/B varianta se střídá po jednom (split cohort pro porovnání znění).

## Režim 2 — okno opakovaného nákupu (`cycle_reminders.py`)

Časová osa „ticho po nákupu" je gradient — Re-activator vlastní celou:

| Ticho od posledního nákupu produktu | Stav | Mechanika |
|---|---|---|
| < 1,2× cyklu | v cyklu, neruš | nic |
| 1,2×–2× cyklu | přesluhuje | jemná připomínka (Režim 2) |
| ≥ 2× cyklu | spící zákazník | vlna, segment C |

**Cyklus per produkt:** deklarovaný v §11 (podsekce Opakovaný nákup) („krém: 60 dní"), nebo `auto` = medián dnů mezi opakovanými nákupy téhož produktu napříč zákazníky (z `orders.json`; min. 5 párů `[5]`, jinak skript produkt přeskočí a řekne proč). Párování produkt ↔ objednávka: normalizovaný podřetězec (bez diakritiky) názvu produktu v položce objednávky; refundované/failed objednávky se ignorují. **Ochrana proti degeneraci** (ověřeno na reálných datech — same-day duplicity a trial→platba dávaly cykly 0–4 dny): nákupy téhož produktu < 7 dní od sebe `[7]` se slučují do jednoho, mezery < podlaha se do mediánu nepočítají, a auto cyklus < podlaha = produkt není cyklický → deklarovat ručně, nebo nehlídat.

**Filtry (sdílené ochrany):** DND · bez kontaktu · otevřený obchod · touch-cap `osloven:` s oknem **30 dní `[30]`** (globální mantinel §11 „max 1 nabídka / 30 dní" napříč vlnami, připomínkami i upsellem) · **max 1 připomínka na kontakt×produkt×cyklus** (dedup přes kohortu; nový nákup počítadlo resetuje). Karanténa `reaktivace:` se tu záměrně NEuplatňuje — připomínka není reaktivace; rozestup dotyků řeší `osloven:`.

**Odeslání:** skill připraví kandidáty, náhled a jeden exact plán. Sdílený helper před každým dispatch znovu ověří DND, touch-cap a další deklarované podmínky; provider-authoritative cenový strop v této dodávce neexistuje. Lokální `--max-spend` fail-closed porovná odhad aktuální frozen dávky (u cyklu celého běhu), ale negarantuje skutečnou cenu poskytovatele. Evidenční tagy jsou samostatné závislé additive actions `cyklus:<produkt>:<RRRR-MM>` a `osloven:<datum>`; reply tag `cyklus-reply:*` odděluje měření od vln. Zmrazený plán ani tag bez readbacku nejsou důkaz odeslání. Teprve `cycle_reminders.py --record-execution` nad exact terminálním journalem atomicky a idempotentně přidá do produktové kohorty jednotlivé message akce s provider receipt/readbackem; failed/blocked/outcome-unknown akce nic nemění.
