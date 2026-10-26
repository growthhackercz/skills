---
name: sales-prospector
description: "Najde a ověří 0–100 nových B2B prospektů pro jeden konkrétní trh přes skutečně dostupné veřejné zdroje, odstraní lokální i CRM duplicity a předá hashovaný balík k review; nové CRM kontakty ani zprávy nevytváří."
category: sales
status: ready
version: "1.4"
publishedAt: "2026-09-02"
metadata: {"openclaw":{"requires":{"bins":["python3"]},"emoji":"🎯"}}
---

# Sales Prospector

Top-of-funnel producer Sales Enginu. V jednom běhu zpracuje právě jeden market,
vytvoří ověřený candidate package a skončí u lidského review. Deep research
dělá `sales-scout`; práci s existujícím dealem `sales-assistant`.

## Povinné hranice

1. Kroky 0–8 dělej v pořadí. STOP 1, STOP 2 a případný STOP 3 nepřeskakuj.
2. Jeden task a jedna složka patří právě jednomu ISO marketu. Jazyk výstupu je
   samostatný `locale`. Více zemí = umbrella task + samostatné child tasky.
3. Market/source policy vždy načti přes
   `{baseDir}/scripts/prospect_package.py market-plan`; source seznam
   nevymýšlej podle paměti ani podle jiného trhu.
4. Používej helpery `{baseDir}/scripts/prospect_package.py`,
   `{baseDir}/scripts/dedup_check.py` a `{baseDir}/scripts/ghl_contact_upsert.py`.
   Neopisuj jejich logiku do inline skriptu.
5. Google Places, Apify, LinkedIn automatizace a přímé Brave/Serper credentials
   nejsou v 1.4 aktivní. `apify_actor.py` zůstává fail-closed a neutratí kredit.
6. HTTP 403/429, CAPTCHA, login wall nebo paywall konkrétní source ukončí.
   Browser není nástroj k obcházení blokace.
7. Finální řádek musí mít veřejný e-mail nebo telefon, skutečný `Source`,
   konkrétní `Source_URL` a `VerifiedAt`. Fallback nikdy nepřejmenuj na registr
   nebo mapovou službu, kterou jsi nepoužil.
8. CRM read failure nebo nejednoznačná shoda je `unknown` a blokuje seal.
   `--skip-crm` je zakázané.
9. Nový GHL kontakt nevytvářej. Pro exact existující kontakt lze po samostatném
   souhlasu zmrazit pouze aditivní tag `sales prospector`.
10. Task contract vyber a ulož právě jednou až po volbě „jen soubory“ versus
    „CRM tag plán“. Již uložený binding nepřepisuj.

## Výstup

```text
/documents/sales/prospects/{campaign}/
├── idealni-klient.md
├── plan-vyhledavani.md
├── prospects-review.md
├── prospects.csv
├── meta.json
└── ghl-plan.json          # pouze volitelný exact tag plán
```

- `prospects.csv` generuje helper v kanonické hlavičce.
- `meta.json` je jediný machine source of truth: market/adapter, source runs,
  monotónní funnel, dokončená CRM deduplikace, počet řádků a CSV SHA-256.
- `prospects-review.md` je lidské vysvětlení fitu, důkazů a vyřazení.
- Nulový validní výsledek je pravdivý výstup, ne důvod vymyslet kontakty.

Detaily artefaktu a přesné příkazy jsou v
`{baseDir}/references/prospect-package.md`.

## Workflow

### Krok 0 — Kontext, task a market

Nezačínej sběrem. Načti Brand DNA, Product DNA a dostupnou
`/documents/sales/salesDNA.md`. Chybějící produkt/brand doplň řízenými otázkami
z `{baseDir}/references/idealni-klient-sablona.md`; neptej se na známé údaje.

Urči název kampaně, právě jeden `market` (`CZ`, `SK`, `ES` v první policy
verzi), `locale` výstupu a cílový počet 0–100. Je-li market nejasný, polož jednu
otázku. Pro cross-market zadání vytvoř jeden umbrella task a jednotlivé market
child tasky.

Pro každý běh vytvoř/reuse CSO task přes
`mc-task-api/scripts/cc_task.py create-task` podle
`~/.openclaw/cs-skills/_lib/cso_task_flow.md` s klíčem
`sales-prospector:task:<campaign>:<market>`. Vrácené kladné `task.id` je jediná
task identita balíku.

Načti policy:

```bash
python3 {baseDir}/scripts/prospect_package.py market-plan --market <MARKET> --locale <LOCALE>
```

`unsupported_market` znamená STOP; nepoužívej český fallback.

### Krok 1 — Ideální klient ✋ STOP 1

Sestav profil podle marketu: segment a místní klasifikaci oboru, velikost,
region, právní formu, stáří firmy, produktové/signální podmínky, exclusions,
minimální veřejný kontakt a marketový registry ID typ. Ukaž profil a čekej na
„ano / uprav“. Schválenou verzi později ulož jako `idealni-klient.md`.

### Krok 2 — Source plán a dedup pravidla ✋ STOP 2

Z výstupu `market-plan` vyber 2–3 vhodné zdroje a u každého ukaž kanonické
source ID/roli, konkrétní dotaz, execution mode, bezpečný limit a povolený
fallback. Současně potvrď karanténu (default 180 dní), blacklist, CRM recent
window a revisit threshold podle `{baseDir}/references/dedup-strategie.md`.

Uživatel schválí zdroje, počet a deduplikaci. Ulož `plan-vyhledavani.md`.

### Krok 3 — Sběr

Spusť pouze schválené source runy. Pro každý drž:

```text
source, role, status, query, sourceUrl,
startedAt, verifiedAt, candidateCount, errorCode
```

Stavy jsou `complete`, `partial`, `unavailable`, `blocked`. Raw chyba se do
artefaktu neukládá; jen sanitizovaný `errorCode`. Progress hlásí skutečná ID,
například `ares: 12, overpass: 8`, nikdy „Mapy Google“, pokud neběžely.

### Krok 4 — Veřejné obohacení

U kandidáta dohledávej veřejný firemní web, e-mail/telefon, veřejnou osobu,
popis činnosti a doložený signál zájmu. `web_fetch` je výchozí. Headless browser
použij jen na stejném firemním webu, když statické HTML prokazatelně obsahuje
prázdný JS shell; ne po 403/429 a nikdy na vyhledávač/LinkedIn.

Kontakt bez veřejného e-mailu i telefonu může zůstat v pracovní poznámce, ale
nejde do finálního candidate JSON ani CSV.

### Krok 5 — Normalizace a pět vrstev deduplikace

Nejdřív normalizuj marketové identifikátory:

```bash
python3 {baseDir}/scripts/prospect_package.py normalize --market <MARKET> --input /tmp/raw-candidates.json --output /tmp/normalized-candidates.json
```

Potom spusť `dedup_check.py` nad normalizovanými kandidáty. Pořadí je povinný
ICP fit, exclusions/risk, blacklist, lokální historie a úplný bounded exact CRM
lookup e-mailu/telefonu.

Uchovej funnel `rawCandidates → withPublicContact → afterProfileFilter →
afterLocalDedup → afterCrmDedup → final`. Každý další počet musí být menší nebo
stejný. Jakýkoli CRM `unknown` blokuje pokračování.

### Krok 6 — Fit a úvodní věta

Pro každý finální řádek připrav jednu až dvě konkrétní věty z doloženého
signálu, veřejného webu nebo skutečného oborového fitu. Neověřený odhad označ a
nesmí zvýšit confidence. `Confidence` je pouze `high`, `medium`, `low`.

### Krok 7 — Review podklady a volba režimu

Ulož `idealni-klient.md`, `plan-vyhledavani.md` a `prospects-review.md`. V chatu
ukaž prvních 20 kandidátů a funnel. Pak se zeptej:

- **„jen soubory“** → budoucí contract `sales-prospector:prospect-package-v1-4`;
- **„tag plán pro existující“** → budoucí contract
  `sales-prospector:prospect-actions-v1-4`, případně výběr řádků.

Toto není nový STOP navíc; nahrazuje dnešní volbu na začátku Kroku 8.

### Krok 8 — Seal, checkpoint a volitelný CRM plán

Podle volby vytvoř `/tmp/prospect-meta-<taskId>.json` a zapečeť balík příkazem
z `{baseDir}/references/prospect-package.md`. Seal provider-free vytvoří
`prospects.csv` a `meta.json`, ověří market/source policy, funnel, CRM dedup,
řádky a SHA.

V obou režimech potom jednou appendni finální normalizované identity včetně
`market`, `registry_id_type`, `registry_id`, kampaně a data do
`/documents/sales/.dedup-history.jsonl`. Opakovaný běh nejdřív ověří, zda
stejná kampaň a identita už v historii je; stejný řádek nepřidává podruhé.

#### Jen soubory

1. Nastav task metadata jedním voláním na
   `contract: "sales-prospector:prospect-package-v1-4"` a
   `contractParams: {"campaign":"<campaign>"}`.
2. Přesuň task do review. CC balík nezávisle znovu ověří.

#### Tag plán pro existující kontakty ✋ STOP 3

1. Seal použije `taskContract: "sales-prospector:prospect-actions-v1-4"`.
2. Spusť read-only dry-run:

```bash
python3 {baseDir}/scripts/ghl_contact_upsert.py --csv /documents/sales/prospects/<campaign>/prospects.csv --meta /documents/sales/prospects/<campaign>/meta.json --task-id <taskId> --dry-run
```

3. Zmraz všechny vrácené `planned_slots` do jednoho plánu přes
   `--create-plan --task-id <taskId> --idempotency-key
   "sales-prospector:<campaign>:<taskId>" --plan-artifact
   "/documents/sales/prospects/<campaign>/ghl-plan.json"` a opakované
   `--expected-slot`.
4. Nastav task metadata právě jednou na
   `sales-prospector:prospect-actions-v1-4` + `campaign`.
5. Ukaž exact `planSha256`. Teprve explicitní souhlas v aktuální konverzaci
   dovolí provedení podle
   `~/.openclaw/cs-skills/_lib/sales-ghl-plan-workflow.md`.
6. Tag je pouze `sales prospector`; žádné custom fields, create/update kontaktu,
   whole-tag replace ani kampaňové/source tagy.
7. Po `outcome_unknown` nic automaticky neopakuj. Task review vyžaduje současně
   validní prospect package i úplný GHL plán.

Checkpointy bez suffixu (`prospect-package`, `prospect-actions`) jsou pouze
kompatibilita pro už uložené tasky 1.3. Nový běh je nesmí bindovat ani převádět;
existující immutable binding se naopak nikdy nepřepisuje na 1.4.

## Napojení na Sales Engine

- `sales-strategist` může navrhnout market campaign task, ale zdroje nespouští.
- `sales-scout` převezme vybraný normalizovaný řádek a stejný market adapter pro
  hluboký brief.
- Nový kontakt zůstává file/review-only do ručního importu nebo budoucího
  samostatného typed lead-import publisheru.
- `sales-assistant` pracuje až nad skutečným CRM kontaktem/dealem.
- `sales-analytik` nesmí vydávat source conversion za změřenou, dokud neexistuje
  CRM admission/link; `meta.json` pouze připravuje budoucí provenance.

## Reference

- `{baseDir}/references/prospect-package.md` — schema, seal a contract volba
- `{baseDir}/references/zdroje-vyhledavani.md` — market policy a source role
- `{baseDir}/references/idealni-klient-sablona.md` — fallback ICP rozhovor
- `{baseDir}/references/dedup-strategie.md` — lokální/CRM dedup
- `{baseDir}/references/ghl-upsert-mapping.md` — existující CRM tag boundary

## Antipatterns

| Nedělej | Proč | Místo toho |
|---|---|---|
| Použít ARES mimo CZ | Falešná registry provenance | `market-plan` a správný adapter |
| Označit OSM/web jako Google Maps | Lživý zdroj | Skutečné source ID + URL |
| Přímý Brave/Serper/Apify/Places call | Obchází capability/cost policy | Jen aktivní policy source |
| Browser po 403/429/CAPTCHA | Obchází blokaci a škodí IP | Source ukončit a zapsat stav |
| Ručně vyrobit CSV/meta | Lze obejít schema/hash | `prospect_package.py seal` |
| Změnit task contract po uložení | Binding je neměnný | Režim vybrat před jediným bindem |
| Přeskočit CRM dedup | Riziko duplicity/DND | Fail-closed `dedup_check.py` |
| Vytvořit nový CRM kontakt | Capability neexistuje | File/review nebo samostatný importer |
| Ručně volat GHL write | Obejde SHA/journal/readback | Jen shared Sales plan workflow |

## Quality checklist

- [ ] Jeden podporovaný market a správný adapter
- [ ] STOP 1 a STOP 2 doložené
- [ ] Source runy mají skutečná ID, URL, časy a stavy
- [ ] Finální řádky mají veřejný kontakt a provenance
- [ ] Funnel je monotónní a CRM dedup `complete`, `unknown: 0`
- [ ] Seal i ruční validator vrací `ok: true`
- [ ] Task contract byl nastaven právě jednou
- [ ] Žádný nový kontakt, custom field ani zpráva nebyly vytvořeny
- [ ] Případný GHL plán má exact SHA a samostatný souhlas
