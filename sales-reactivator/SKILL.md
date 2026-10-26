---
name: sales-reactivator
description: "Najde spící kontakty a zákazníky před termínem opakovaného nákupu, připraví bezpečně filtrované kohorty a přesné zprávy a zmrazí je do jednoho plánu k explicitnímu schválení. Bez potvrzení exact SHA nic neposílá."
category: sales
status: ready
version: "1.0"
publishedAt: "2026-08-26"
metadata: {"openclaw":{"requires":{"bins":["python3"]},"emoji":"🔄"}}
---

# AI Sales Re-activator

## ⚠️ Povinný postup (pro vykonávajícího agenta — čti jako první)

Tento skill **musí** projít kroky 0 → 1 → 2 → 3 (✋ STOP) → 4 **v pořadí**. Železná pravidla:

1. **Vlna neprodává — ptá se.** Jedna krátká osobní otázka (reply-first), žádné odkazy, žádný pitch, žádná sekvence. Cíl je odpověď; odpovědi přebírá konverzační agent platformy (půlka 2).
2. **Nejdřív plán dávky, potom jeden souhlas.** Skill připraví přesný náhled a přes `--create-plan` zmrazí nejvýše 50 kontaktů. Každý příjemce má vlastní message action a závislou add-tags action. Provider write smí následovat pouze podle `~/.openclaw/cs-skills/_lib/sales-ghl-plan-workflow.md` po explicitním souhlasu s exact SHA; nikdy se neschvaluje po kontaktech.
3. **Skript čte snapshot stratéga, ne API** (`/documents/sales/.strategist-state/`). Nikdy nenačítej celou bázi do kontextu — pracuj jen se souhrny a soubory vln.
4. **Parametry ber ze Sales DNA** (`/documents/sales/salesDNA.md`): §1 nastavení (pracovní doba), §7 provozní pravidla (spící = X dní, karanténa, touch-cap, SLA), §9 taxonomie, §11 mantinely a cykly (podsekce Opakovaný nákup). Znění otázek vln: vzory v `{baseDir}/references/vlna-workflow.md`, ověřené vítězné znění v §10 (Ověřené poznatky) má přednost. Sales DNA je i v LLM wiki (hledej „Sales DNA"). Pokud neexistuje → STOP: *„Nejdřív spusťte sales-dna-generator."*
5. **Bez ověřené půlky 2 se vlna nespouští** (krok 0) — odpovědi by padaly do ticha a spálily segment.
6. Tvrdé filtry (DND, karanténa `reaktivace:`, touch-cap `osloven:`, otevřený obchod) **nikdy neobcházej** — jsou v obou skriptech a platí i při ručních zásazích.

## Co tento skill dělá pro váš byznys

Ve vaší databázi leží kontakty, které vás už znají — a nikdo se jim neozývá. Tento skill je oživí, bezpečně a s vaším souhlasem:

1. **„Máme stovky starých kontaktů a nikdo s nimi nepracuje."** Skill je najde, roztřídí a navrhne, koho oslovit.
2. **„Nechci nikoho spamovat."** Jedna slušná otázka, tvrdé filtry (nerušit, nedávno oslovení, rozjednaní), karanténa 6 měsíců a vždy váš souhlas předem.
3. **„Kdo bude odpovídat?"** AI asistentka platformy — odpoví, doptá se a rovnou nabídne termín. Když si neví rady, předá člověku.

## Jak to vidíte vy — 3 momenty

1. Řeknete: **„Oživ mi databázi."** (nebo vlnu navrhne stratég v týdenním reportu)
2. Dostanete **jednu kartu aktuální dávky**: koho, kolik, jakou otázkou, za kolik a exact SHA plánu.
3. Odpovíte **„schvaluji dávku"** v aktuální konverzaci. Helper provede nejvýše 50 kontaktů a vrátí journal. Další dávka vznikne až po kontrole výsledku první.

## Kroky (pro agenta)

Před vytvořením plánu ověř nebo vytvoř/reuse CSO task přes
`mc-task-api/scripts/cc_task.py create-task` podle
`~/.openclaw/cs-skills/_lib/cso_task_flow.md`. Wave používá stabilní klíč
`sales-reactivator:task:wave:<slug>:<offset>`, cycle běh
`sales-reactivator:task:cycle:<YYYY-MM-DD>`; vrácené `task.id` sdílí všechny
action sloty daného plánu.

### Krok 0 — Prerekvizity (tiše, ale tvrdě)

1. `salesDNA.md` existuje (jinak STOP → sales-dna-generator). Vyčti parametry §1/§7 a znění otázek (vzory ve vlna-workflow.md, vítěz z §10).
2. Snapshot stratéga čerstvý < 24 h — jinak spusť `sales-strategist/scripts/ghl_snapshot.py --mode auto`.
3. **Půlka 2 musí být připravená před budoucím ostrým spuštěním.** V této verzi pouze ověř konfiguraci reply/STOP workflow bez seed odeslání a zapiš výsledek do `/documents/sales/vlny/setup-check.json`. Chybí-li workflow, vypiš setup cesty a skonči; netvrď, že přímé odeslání je dostupné.

### Krok 1 — Kandidáti

```bash
python3 {baseDir}/scripts/reactivation_candidates.py \
  --sleep-days <§7> --quarantine-months <§7> --touch-cap-days <§7> \
  --output /tmp/kandidati.json
```

Přečti si jen souhrn (počty per segment, vyřazení, režim plný/degradovaný). ⚠️ Cold start: u nového klienta bude segment B prázdný a C jen z vyhraných obchodů — to je normální, řekni to.

### Krok 2 — Návrh a kohorta bez provider write

Jedna karta, lidsky (vykání), podle vzoru:

> *„Našel jsem **240 spících kontaktů** (180 prohraných obchodů, 60 zákazníků bez aktivity). Připravuji kohortu **100 nejnadějnějších** s otázkou **„Ještě řešíte zateplení?"** (testujeme 2 znění). První plán bude mít nejvýše 50 kontaktů; před odesláním ukážu jeho cenu a SHA k jednomu potvrzení. Druhou dávku připravím až podle výsledku první."*

Velikost = min(50–150, kapacita na odpovědi, SMS rozpočet). Kohortu vytvoř
write-free rovnou: `--make-wave /documents/sales/vlny/<slug>.json --wave-slug
<slug> --wave-size N`. V této fázi se uživatele na další „ano“ neptej. V tasku
nastav `contract: "sales-reactivator:wave-package"` a
`contractParams: {"slug":"<slug>"}`; do review ho přesuň až po vytvoření
kohorty.

### Krok 3 — ✋ STOP: jedna finální karta zmrazeného plánu

Obě znění (A/B — vzory z vlna-workflow.md, případný ověřený vítěz z §10) nech zkontrolovat **judge modelem**: pravdivost, vykání, brand, žádný pitch. Judge hodnotí kvalitu, nenahrazuje lidské schválení.

Před vytvořením plánu přepni **tentýž** CSO task z package checkpointu na
`contract: "sales-reactivator:wave-actions"` a ponech
`contractParams: {"slug":"<slug>","offset":"<offset>"}`. Změnu ověř přes `cc_task.py get-task <ID>`;
nový task pro plan fázi nevytvářej.

Každý `--create-plan` zmrazí právě jednu souvislou dávku nejvýše 50 kontaktů
podle `--batch-offset`. Stejný offset při retry používá stejné `--as-of`,
task ID, idempotency key a plan path. Další offset připrav až po vyhodnocení
předchozí dávky; tím je ramp gate skutečný, nikoli jen text v dokumentaci.

```bash
python3 {baseDir}/scripts/ghl_wave_push.py --wave /documents/sales/vlny/<slug>.json \
  --message-a "<znění A, placeholder {jmeno}>" --message-b "<znění B>" \
  --subject "<předmět pro e-mail>" --email-from "<ověřená adresa ze Sales DNA §1>" \
  --touch-cap-days <§7> \
  --quarantine-months <§7, výchozí 6> --max-spend <limit> \
  --batch-size 50 --batch-offset <0|50|100|…> \
  --as-of "<stabilní ISO8601 čas s offsetem>" \
  --create-plan --idempotency-key "sales-reactivator:wave:<slug>:<offset>" \
  --plan-artifact /documents/sales/vlny/<slug>.batch-<offset>.ghl-plan.json \
  --task-id <ID aktuálního CC tasku>
```

Bez `--create-plan` skript vypíše exact preview zvolené dávky. Každý e-mailový payload vyžaduje neprázdné `--email-from`; SMS-only kohorta jej nepotřebuje. Wave safety nese `quarantineMonths` a `quarantineTagPrefix: "reaktivace:"`; sdílený helper je před každým dispatch znovu ověří proti live tagům. `osloven:` zůstává oddělený touch-cap.

Po `complete: true` ukaž **jednu finální kartu dávky**: segmenty a počet kontaktů,
kanály, obě exact znění, pracovní časy, DND/touch/karanténní mantinely, odhad,
limit a `planSha256`. Teprve zde se jednou zeptej „Schvalujete tento plán?“.
Po explicitním souhlasu proveď přesně toto SHA podle sdíleného workflow.

`--max-spend` se porovnává s lokálním odhadem **aktuální dávky** včetně počtu
SMS segmentů. Odhad celé vlny zůstává v preview pro orientaci. Jednotkové ceny,
měna a limit dávky se v plánu zmrazí. Je to
fail-closed kontrola; není to provider-authoritative ceník, kumulativní spend
ledger ani finanční garance skutečné ceny.

Po execution zkontroluj journal, provider chyby, opt-out a kapacitu na odpovědi.
Teprve potom vytvoř nový task/plán pro další offset a vyžádej jedno potvrzení
této další dávky. Jeden souhlas tedy znamená jednu bounded dávku, nikdy stovky
per-item kliknutí.

### Krok 4 — Uzávěrka (po 14 dnech, zadá stratég)

Trychtýř z tagů a pipeline Reaktivace: oslovení → `vlna-reply:` → schůzky → dealy/Kč + opt-out. Vítězné znění A/B → **návrh** zápisu do Sales DNA §10 (Ověřené poznatky) (zapisuje se až po schválení; do LLM wiki se soubor dostane synchronizací AI Data Centra). Soubor vlny v `/documents/sales/vlny/` je dohledatelný přes knowledge/wiki.

## Režim 2 — Hlídání opakovaných nákupů (průběžný)

Pro produkty kupované v cyklu (kosmetika, doplňky, servis). **Klientská terminologie: „hlídání opakovaných nákupů" — NIKDY „reaktivace"** (zákazník 75 dní po nákupu krému není mrtvý kontakt). Zákazník, který přesluhuje svůj cyklus (1,2×–2×), dostane jemnou připomínku „Nedochází vám X?"; **nad 2× cyklu už nepřipomínáme** — kontakt je spící a patří do vlny (segment C).

Schválené pravidlo určuje výběr kandidátů a texty, ale samo neopravňuje skill k odesílání jednotlivých připomínek.

### R0 — Prerekvizity

1. Sales DNA §11 podsekce „Opakovaný nákup" s produkty a cykly (deklarované dny, nebo `[výchozí]` = spočítat z objednávek).
2. Snapshot stratéga obsahuje `orders.json` (historie objednávek). Pokud ne → STOP: hlídání zatím nelze zapnout, jede jen vlnový režim (čeká na rozšíření snapshotu stratéga).
3. Půlka 2 rozšířená o cyklus: reply workflow má přidávat `cyklus-reply:*` u kontaktů s tagem `cyklus:*`. V této verzi konfiguraci pouze popiš a ověř bez odesílání.

### R1 — Zapnutí pravidla (✋ STOP — jen poprvé)

Pokud §11 (podsekce Opakovaný nákup) neobsahuje „Hlídání: zapnuto", předlož majiteli jednu kartu: které produkty, jaké cykly (odkud), vzor připomínky, mantinely (max 1 nabídka / 30 dní napříč vším). Po výslovném „ano, hlídej" zapiš do §11 řádek `Hlídání: zapnuto (<datum>)` ; do LLM wiki se soubor dostane synchronizací AI Data Centra. Bez zapnutého pravidla se Režim 2 nespouští.

### R2 — Běh výběru kandidátů (z denního úkolu stratéga)

```bash
python3 {baseDir}/scripts/cycle_reminders.py --cycles "<produkt>=<dny|auto>,…" \
  --touch-cap-days <§11, výchozí 30> \
  --batch-size 50 --as-of "<stabilní ISO8601 čas s offsetem>" \
  --messages '{"<produkt>": "<schválená šablona, placeholder {jmeno}>"}' \
  --email-from "<ověřená adresa ze Sales DNA §1>" \
  --max-spend <limit> --create-plan \
  --idempotency-key "sales-reactivator:cycle:<RRRR-MM-DD>" \
  --plan-artifact /documents/sales/vlny/cycle-<RRRR-MM-DD>.ghl-plan.json \
  --task-id <ID aktuálního CC tasku>
```

Skript spočítá cykly, globálně vybere nejvýše 50 unikátních kontaktů (jeden kontakt nedostane dvě produktové připomínky v témže běhu), aplikuje snapshotové filtry a materializuje přesný text, kanál a safety policy. U SMS počítá segmenty do odhadu. Default je preview. `--create-plan` zmrazí jeden message/tag plán bez provider write; při retry musí zůstat stejné `--as-of`. Pro task nastav `contract: "sales-reactivator:cycle-actions"`, `contractParams: {"date":"<RRRR-MM-DD>"}`; checkpoint ověří `/documents/sales/vlny/cycle-<date>.ghl-plan.json`. Do review až po `complete: true`; potom jeden souhlas a execute podle sdíleného workflow.

Po execute s `status: complete` materializuj ověřený denominator kohort výhradně
z execution journalu (nikdy z pouhého plánu nebo domnělého odeslání):

```bash
python3 {baseDir}/scripts/cycle_reminders.py --record-execution \
  --cohort-dir /documents/sales/vlny \
  --plan-artifact /documents/sales/vlny/cycle-<RRRR-MM-DD>.ghl-plan.json \
  --confirm-plan-sha <planSha256>
```

Příkaz je idempotentní. Přijme pouze plán `sales-reactivator:cycle-actions`,
kanonický SHA a terminální `complete` nebo `partial_failure` journal. Do kohorty
vezme výhradně jednotlivé message akce se stavem `succeeded`, provider receipt
a readbackem; failed/blocked akce vynechá. `outcome_unknown` kohortu neposune.
Pro bezpečně neprovedené cíle je po kontrole nutný nový plán.

### R3 — Měření

Kohorty `cyklus-<produkt>.json` odděleně od vln: jednotlivé ověřeně úspěšné připomínky z terminálního journalu → `cyklus-reply:` → nákupy per produkt (čitatele sbírá cron stratéga z tagů). Kohortní záznam zároveň zajišťuje max jednu připomínku na kontakt×produkt×poslední nákup; novější nákup pravidlo resetuje. Po čase → návrh úprav cyklů do Sales DNA §11 (po schválení; do LLM wiki se soubor dostane synchronizací AI Data Centra).

## Antipatterns — co NEDĚLAT

| Antipattern | Proč je špatný | Co dělat místo toho |
|---|---|---|
| Volat GHL ručně mimo helper | obejde exact SHA, live safety a journal | vytvoř plán přes `--create-plan`, ukaž celý souhrn a proveď jen sdíleným helperem |
| Poslat nabídku/sekvenci místo jedné otázky | zabíjí reply rate; vlna není kampaň | jedna krátká otázka, plain text, bez odkazů |
| Spustit vlnu bez ověřené půlky 2 | odpovědi padají do ticha → spálený segment | krok 0 seed test, jinak setup a konec |
| Načíst celou bázi / kandidáty do kontextu | tisíce kontaktů = spálené tokeny | jen souhrny; detail v souborech |
| Obejít karanténu/touch-cap („jen tentokrát") | kontakt dostane vlnu + upsell týž týden | filtry jsou tvrdé v obou skriptech |
| Poslat celou vlnu najednou | reputace odesílatele, rate limit, kapacita na odpovědi | max 50 kontaktů na plán + skutečný ramp gate před dalším offsetem |
| Slibovat 10–20 % odpovědí | marketingový hype; realita 3–7 % | konzervativní čísla, výsledky za 14 dní |
| Vymýšlet otázky ad hoc | nejde se učit mezi vlnami | vzory z vlna-workflow.md + vítěz z §10; nový vítěz do §10 po schválení |
| Říkat zákazníkovi v cyklu „reaktivace" | 75 dní po nákupu krému není mrtvý kontakt | terminologie „hlídání opakovaných nákupů" |
| Připomínat nad 2× cyklu / bez zapnutého pravidla | obtěžování spících; pravidlo = souhlas majitele | nad 2× → vlna (segment C); Režim 2 jen se zapnutým pravidlem v §11 |

## Návaznost na další skilly

- **Zadává:** `sales-strategist` (návrh vlny v reportu, uzávěrka po 14 dnech, měření z cron delty; denní agenda „za cyklem" → úkol pro Režim 2)
- **Čte:** `salesDNA.md` (§1, §7, §9, §10, §11 — i přes LLM wiki), snapshot stratéga (vč. `orders.json` pro Režim 2)
- **Předává:** top B2B kandidáty Scoutovi (refresh brief); schůzky z vln obsluhuje Sales Assistant; poznatky → Sales DNA §10 + wiki
- **Koordinace dotyků:** tag `osloven:<datum>` sdílí s Upsell/Cross-sell agentem (touch-cap §7); každý ověřený message readback se navíc zapisuje do lokální suppression evidence, takže selhání následného tagu neotevře cestu k duplicitě.

## Doplňkové soubory (reference)

- `{baseDir}/references/skore-metodika.md` — segmenty, tiery, filtry, degradovaný režim, cold start
- `{baseDir}/references/vlna-workflow.md` — dvě půlky, setup (fleet snapshot / Workflow AI prompt), Conversation AI taxonomie + GO/NO-GO čeština, dávkování, měření
- `~/.openclaw/cs-skills/_lib/sales-ghl-plan-workflow.md` — společný souhlas, execute, journal a no-retry pravidla

## Bezpečnost a citlivá data

- Kandidátní skript je 100% offline a čte snapshot. Producer při `--create-plan` nedělá provider write; credential načítá pouze sdílený helper a nikdy jej nevypisuje.
- Zmrazený plán není doklad o odeslání. Autoritou je `status: complete`, provider receipt a readback v execution journalu. Lokální `--max-spend` není garance skutečných nákladů.
- Stejný plán po chybě neopakuj. U `outcome_unknown` ručně ověř GHL; po opravě vytvoř nový plán a vyžádej nový souhlas.
- V B2C se oslovují jen kontakty s existujícím vztahem (zákazník / projevený zájem) — žádné studené záznamy.
