---
name: sales-upsell
description: "Po nákupu vybere vhodný upsell nebo cross-sell, připraví a zkontroluje personalizovanou sekvenci a zmrazí ji do jednoho přesného plánu k explicitnímu schválení. Bez potvrzení exact SHA nic neposílá ani neruší."
category: sales
status: ready
version: "1.0"
publishedAt: "2026-08-26"
metadata: {"openclaw":{"requires":{"bins":["python3"]},"emoji":"🛒"}}
---

# AI Upsell & Cross-sell Agent

## ⚠️ Povinný postup (pro vykonávajícího agenta — čti jako první)

Železná pravidla každého běhu:

1. **Bez Sales DNA STOP.** Skill potřebuje `/documents/sales/salesDNA.md` — minimálně §11 (Upsell a katalog: mantinely, Feed, pravidla). Pokud chybí → STOP: *„Chybí prodejní playbook — spusťte nejdřív sales-dna-generator."*
2. **Vždy skripty, nikdy ručně nad celou bází.** Pořadí: `purchase_sync.py` (read-only nové nákupy) → `upsell_recommend.py` (kandidáti s evidencí) → judge → `ghl_offer_push.py` (preview a zmrazený plán). Model se dívá jen na výstupy skriptů.
3. **Judge gate je povinný pro každý návrh**, ale hodnotí jen kvalitu. Není lidským schválením a neopravňuje k odeslání.
4. **Nejdřív jeden celý plán.** Default je exact preview; `--create-plan` skládá E1/E2/E3/tag do jednoho artefaktu. Teprve `complete: true` + exact `planSha256` lze jednou schválit a provést podle `~/.openclaw/cs-skills/_lib/sales-ghl-plan-workflow.md`.
5. **Žádný ruční curl ani provider fallback.** `--setup` uloží pouze schválenou e-mailovou obálku. Create/update custom fields jsou zakázané. Guard je pouze ruční exact cancellation plán; pro e-mail vyžaduje svázané hlavní `messageId` i `emailMessageId` z provider receipt.
6. **Zdroj pravdy o nákupech = prokazatelně zaplacené transakce (`purchase_sync.py`), ne tagy.** Pending/failed/unpaid/unknown se ukládají jen pro audit a nikdy nevstupují do owned ani evidence. Stejné transaction ID se při pozdější změně stavu znovu vyhodnotí: pending→paid vytvoří právě jednu nákupní událost, paid→refund vlastnictví i evidence odvolá. Tag `produkt:*` je jen doplňkový signál.
7. **Doporučuj jen z pravidel a evidence.** Kandidáty dává skript ve vrstvách: kurátorská pravidla (salesDNA §11) → reálné nákupní vzorce → flagship. Žádné páry z hlavy — když nic nevrátí, řekni to a použij productDNA (fallback).

## Co tento skill dělá pro váš byznys

1. **„Zákazník koupí a tím to končí."** Po nákupu lze připravit krátkou osobní E1–E3 sekvenci. Automatické rozpoznání odpovědi a zrušení zbytku tato verze nemá; cancellation je jen ruční exact plán nad ověřenými ID z provider receipt.
2. **„Doporučení jsou náhodná."** Nabídky vycházejí z toho, co se u vás reálně kupuje spolu: *„34 % zákazníků, kteří koupili kávovar, si do 60 dní pořídilo odvápňovač."* Váš e-shop, vaše čísla — žádné odhady.
3. **„Nevím, jestli to opravdu vydělává."** Report ukazuje celý trychtýř: kolik nabídek odešlo, kolik lidí odpovědělo, kolik koupilo doporučený produkt a kolik Kč se tím připsalo.

## Kdy se skill spouští

| Spouštěč | Co se stane |
|---|---|
| Úkol od stratéga (nový nákup v CRM) | zpracuje konkrétní nákup → nabídka |
| Ručně: „Co nabídnout zákazníkovi X?" | doporučení + důvod, bez odeslání (jen návrh) |
| Ruční guard (future cron `upsell-provoz` je neaktivní) | SMS nad exact `messageId`; e-mail nad svázanými `messageId` + `emailMessageId`; automatická projekce zatím chybí |
| Webhook z externího e-shopu | zatím neaktivní — plánováno pro v2 (režim „intake") |

## Kroky běhu (nabídka po nákupu)

Před vytvořením plánu ověř existující CSO task, nebo přes
`mc-task-api/scripts/cc_task.py create-task` vytvoř/reuse task podle
`~/.openclaw/cs-skills/_lib/cso_task_flow.md` s klíčem
`sales-upsell:task:<txnId>:<contactId>`. Vrácené `task.id` sdílí E1/E2/E3 a
jediný aggregate artefakt; chatový souhlas není náhradou task provenance.

0. **Prerekvizity:** salesDNA §1/§7/§11 · čerstvý katalog · jednorázová aktivace obálky přes `--setup`, která uloží i neprázdnou ověřenou `email_from`. Vzdálený feed smí být jen HTTPS na veřejné IP a pod bounded limity. Setup task jde do review po vzniku úplného `config.json`; starý config bez odesílací adresy je neplatný a setup se musí zopakovat. Žádný `fields.json` ani custom-field zápis se nepoužívá.
1. **Nákupy:** `python3 {baseDir}/scripts/purchase_sync.py --state-dir /documents/sales/.upsell-state --output /tmp/purchases.json` — pod jedním stavovým zámkem atomicky sloučí nové i změněné transakce. `purchase_new` vzniká jen při přechodu do paid; `purchase_refunded`/`purchase_invalidated` ruší dřívější nákupní signál. `event_count: 0` → „OK, žádné nové nákupy." a konec.
2. **Kandidáti:** pro každý nákup `python3 {baseDir}/scripts/upsell_recommend.py --contact <id> ...` → co koupil, co už má, kandidátní páry s evidencí (kolik zákazníků, za kolik dní).
3. **Výběr a texty — celá sekvence najednou:** vyber 1 (max 2) doporučení podle vrstev, které vrací skript (`source` u kandidáta): **kurátorská pravidla** ze salesDNA §11 (přibitý pár → bundle → upgrade) → **evidence** (co-purchase čísla) → flagship → fallback productDNA. Napiš **3 maximálně personalizované e-maily** (vokativ, konkrétní koupený produkt, čísla z evidence / poznámka pravidla, hlas dle brandDNA, vykání, bez AI frází). `purchase_count: 1` = první nákup → E1 vítá a potvrzuje dobrou volbu; opakovaný zákazník → poděkování za věrnost, osobnější tón:
   - **E1 — poděkování (hned):** poděkování + tipy k použití koupeného produktu (hodnota, žádné tlačení; NESMÍ připomínat potvrzení objednávky — to už zákazník od e-shopu má) + měkká zmínka, co se k produktu hodí
   - **E2 — hlavní nabídka (+7 dní ≈ pár dní po doručení):** cross-sell s jednou lidskou konkrétní větou proč + CTA
   - **E3 — dovření (+14 dní):** návrh poslední připomínky jiným úhlem (druhý benefit, sociální důkaz). Tato verze sama nepozná odpověď ani změnu skladovosti; před schválením ji ověř operátor a již naplánovanou zprávu lze zrušit jen ručním exact guardem z kroku 7.
   - Služby a digitální produkty (doručení okamžité): E2 +2 dny, E3 +7 dní. Časy ladí klient v salesDNA §11 (Mantinely a sekvence).
4. **Judge gate:** nezávislý subagent (vlastní model) podle `{baseDir}/references/judge-rubrika.md` — posoudí všechny 3 e-maily v jednom vstupu, verdikt per e-mail. Sekvence vznikne jen tehdy, když E1, E2 i E3 skončí `APPROVE`; `REVISE` → 1 přepis daného e-mailu a znovu judge · kterýkoli definitivní `BLOCK` → celá sekvence stop (`--block`).
5. **Náhled:** slož všechny tři e-maily bez `--create-plan`; ukaž klientovi exact obsah, příjemce, kanál, čas a odhad celé sekvence. E2/E3 musí mít konkrétní `--scheduled-at`.
6. **Plán:** E1/E2/E3 použijí stejný task, base key, stabilní `--plan-date <YYYY-MM-DD>` a `/documents/sales/ghl-plans/upsell/<txnId>-<contactId>.json`. Frozen slot set je přesně `step:e1:message`, `step:e2:message`, `step:e3:message`, `step:e3:tags`. Řetěz je E2 → E1, E3 → E2 a compliance tagy → E3. Producer drží po E1/E2 `complete: false`; E3 dokončí coverage a vrátí SHA. Lokální rozpočet se počítá pro všechny tři e-maily. Task používá `sales-upsell:offer-sequence`.
7. **Guard je manuální/future, ne aktivní cron.** Automatickou reply projekci tato verze nemá, proto `upsell-provoz` neinstaluj. `ghl_offer_push.py --guard --guard-input <ověřené-candidates.json>` nejprve ukáže preview a přes `--create-plan` připraví právě jeden cancellation plán. Kandidát vyžaduje `messageId`, `channel` a `reason`; u e-mailu navíc povinné `emailMessageId` ze stejného provider receipt. Volitelně může nést společně `sourcePlanSha256` + `sourceActionId` pro audit. Artefakt je `/documents/sales/ghl-plans/upsell/cancel-<taskId>-<messageId>.json`; task používá `sales-upsell:scheduled-cancellation`. Před dispatch helper sváže obě e-mailová ID a živě ověří location i stav `scheduled`.
8. **Souhlas, audit a měření:** po dokončení E3 ukaž všechny čtyři akce, příjemce, časy, rozpočet a exact SHA; proveď až po explicitním souhlasu. `/documents/sales/upsell-log.jsonl` eviduje plán, ne provider úspěch. Trychtýř čte execution journal + reply/nákup data.

## Kdy cross-sell, kdy upsell (metodika)

- **Cross-sell = doplněk k tomu, co koupil** (kávovar → odvápňovač). Jediná disciplína, která přirozeně funguje PO nákupu → **výchozí volba tohoto skillu**.
- **Upsell = dražší/lepší verze téhož.** Po nákupu je nebezpečný („koupil jste blbě") — povolený VÝHRADNĚ přes **upgrade cesty** v salesDNA §11: doplatková lhůta na vyšší model, větší balení / předplatné u spotřebního zboží, rozšířená záruka či servis. U **služeb a B2B** je naopak upsell král (vyšší tarif, roční platba) — katalog = productDNA.
- **Upsell v košíku / na checkoutu** (order bump, one-click upsell) = území funnelu (A.I.Q. / checkout e-shopu), NE tohoto skillu.
- Dražší varianta právě koupeného mimo upgrade cesty = judge BLOCK.

## Režim přípravy

| Režim | Jak funguje | Pro koho |
|---|---|---|
| **Plán se schválením** [jediný dostupný] | skill zmrazí exact payloady a uživatel jednou schválí celé SHA | všichni klienti |
| **Autonomie** | nedostupná; bez aktuálního souhlasu se plán neprovede | budoucí samostatně schválená policy fáze |

Kalibraci judge lze sbírat nad návrhy, ale nesmí automaticky přepnout skill do odesílacího režimu.

## Co se ověřuje při přípravě a před provedením

Sdílený GHL helper bezprostředně před provedením ověřuje tyto live podmínky:

- DND → nikdy
- globální touch-cap z live `osloven:<datum>` i immutable lokální evidence každého ověřeného message readbacku; E1–E3 uvnitř jednoho tasku tvoří jednu explicitní sekvenci, ale jiný task ve stejném okně zůstává zablokovaný i tehdy, když po úspěšné zprávě selhal tag
- otevřená opportunity → neoslovovat uprostřed dealu

Při přípravě musí operátor ze svého aktuálního zdroje navíc ručně ověřit:

- zda zákazník po předchozím kroku neodpověděl a produkt je stále dostupný; platforma tyto signály v této verzi sama nečte ani podle nich automaticky neruší
- zda evidenční `upsell-sent:` neporušuje klientem zvolený cooldown; helper samostatný cooldown tohoto tagu nevynucuje
- exact časy E1/E2/E3 podle pracovní doby v Sales DNA; helper je live nepřepočítává, plán používá konkrétní `--scheduled-at`

## Antipatterns — co NEDĚLAT

| Antipattern | Proč je špatný | Co dělat místo toho |
|---|---|---|
| Doporučit produkt „od oka" bez pravidla či evidence | halucinace pod klientovým brandem | jen kandidáti ze skriptu (pravidla → evidence → flagship) |
| Nabídnout dražší variantu právě koupeného | „koupil jste blbě" — buyer's remorse | upsell jen přes upgrade cesty (salesDNA §11) |
| Volat GHL ručně mimo helper | obejde exact SHA, live safety a journal | vytvoř plán a proveď pouze přes sdílený helper |
| Provést E1 dřív, než je hotová E3 | uživatel by neschvaloval celý neměnný celek | nejdřív všechny čtyři sloty a `complete: true`, potom jeden souhlas |
| Nabídnout variantu téhož (jiná barva/velikost) | zákazník to už má | dedup na úrovni skupiny produktů (item_group) |
| Přidávat dotyky nad rámec sekvence E1–E3 | z nabídky se stane spam | 3 e-maily a konec; další slovo má jen Conversation AI po odpovědi |
| Načíst celý katalog/bázi do kontextu | spálené tokeny | skripty vrací jen kandidáty a události |
| Fabulovat historii před integrací | data jsou spolehlivá až od data napojení | slepé okno přiznat (skript ho označuje) |

## Návaznost na další skilly a AI Data Center

- **sales-strategist** — zdroj událostí (nový nákup → úkol tomuto skillu) a odběratel čísel do týdenního reportu.
- **sales-reactivator** — sdílí globální touch-cap přes `osloven:` i lokální suppression evidenci a karanténní logiku; nikdy neoslovovat téhož člověka oběma skilly v témže okně.
- **Volitelná externí reply integrace** — lze ji číst jen když je u klienta skutečně ověřená; skill ji nevytváří ani neslibuje.
- **sales-dna-generator** — vyrábí a aktualizuje salesDNA, odkud tento skill čte pravidla.
- **AI Data Center (LLM wiki):** salesDNA, brandDNA i productDNA žijí jako markdown v `/documents` a AI Data Centrum je synchronizuje do LLM wiki — ostatní agenti z nich čtou přes wiki vyhledávání (bundly a flagshipy tak využije i marketing). Tento skill čte soubory přímo (zdroj pravdy): pravidla ze `/documents/sales/salesDNA.md` (vč. kurátorské §11), hlas z `/documents/brand/brandDNA.md`, u služeb katalog z `/documents/brand/products/<slug>/productDNA.md`. **Ověřené páry** (co funguje) navrhuj po schválení majitele k zápisu do salesDNA §11 (Přibité páry / Nikdy nenabízet) a poznatky do §10 — přes sync se dostanou do wiki celému týmu.

## Doplňkové soubory (reference)

- `{baseDir}/references/id-resolver.md` — jak se z transakce stane spolehlivé „co koupil": zdroje položek, párovací klíč, skupiny variant, slepé okno
- `{baseDir}/references/judge-rubrika.md` — nezávislá kontrola kvality: rubrika, verdikty, kalibrace, logování
- `{baseDir}/references/salesdna-upsell-sekce.md` — formát kurátorské sekce salesDNA §11 (flagship, bundly, páry, upgrade cesty, blacklist) + bootstrap z miningu
- `{baseDir}/references/provoz-a-mereni.md` — jednorázová aktivace, tagový slovník, sekvence a guard, měření a trychtýř, formát logu, text naplánované úlohy
- `~/.openclaw/cs-skills/_lib/sales-ghl-plan-workflow.md` — společný souhlas, execute, journal a no-retry pravidla

## Bezpečnost a citlivá data

- `purchase_sync.py` čte jen pojmenované resources přes sdílený helper a strict tenantní credential resolver; žádnou URL nepřijímá. Payment stránky rekonsiluje v celém známém historickém okně se stabilním `totalCount` a unikátními ID. Volitelný FAPI read credential zůstává oddělený a jeho klient odmítá redirect i nadlimitní odpověď. Poškozený durable stav se nikdy nepřepíše. Stav se mění pod file lockem pomocí atomických replace zápisů.
- `feed_catalog.py` nepoužívá obecný URL opener: HTTPS URL validuje při každém redirectu, blokuje neveřejné DNS odpovědi, připojuje se k přesně ověřené IP se zachovanou TLS hostname kontrolou a vynucuje velikostní i časový limit.
- Rate limity CRM řeší skripty (pauzy, retry s backoff).
- Producer nemá execute surface. Zmrazený plán není doklad o provedení; credential načte pouze sdílený helper ze store a nikdy jej nevypíše. Reply, skladovost, pracovní doba a samostatný `upsell-sent:` cooldown zůstávají ruční/future.
- Stejný plán po chybě neopakuj. U `outcome_unknown` ručně ověř GHL; po opravě vytvoř nový plán a vyžádej nový souhlas.
- Patička s možností odhlášení je povinná součást každého návrhu a judge ji hlídá (rubrika bod 5).
