# CliqSales AI: rekonstrukce původního nastavení

Statická analýza lokální zálohy, dokončena 2026-10-27. Nejde o obnovu serveru ani test živých integrací. Porovnání knihovny je připnuté k `growthhackercz/skills` na `9a2d06fc48faa32abebadbcaa6e11ea5e48d88f8`.

## Závěr

Původní systém byl **OpenClaw + Control Center**, nikoli jen sada promptů. Control Center řídil úkoly, assignmenty, deliverables a integrace; OpenClaw dodával runtime agentů, modely, nástroje a workspace kontext. Zpřístupnění `SKILL.md` v Hermes nepřenáší automaticky žádnou z těchto služeb.

Knihovna Git obsahuje všech **92 provider skillů** zálohy a dalších **58** top-level skillů. U společných souborů není obsahová změna po normalizaci CRLF → LF; dvě složky mají soubor navíc. Chybí ovšem sdílená složka `_lib`, která je v záloze a kterou některé integrační skripty potřebují.

Zdrojová základna: `Cliqsales-zachrana/how-to-restore.zip`, `cs-skills.zip` a `platform/openclaw-disaster-recovery/openclaw-continuity-2026-10-26-v1.tar.gz`. Archivní cesty níže mají prefix `openclaw-continuity-2026-10-26-v1/`, pokud není uvedeno jinak.

## 1. Jak fungovalo řízení práce

```text
Operátor / Control Center chat
  → CEO (CC ceo, runtime main)
  → doménový úkol pro cmo / cso / coo / cto
  → explicitní wake-task pro spuštění/pokračování existujícího úkolu
  → agent načte potřebný kontext a provede práci svými skills
  → uloží soubor do /documents a zaregistruje skutečnou cestu
  → review souborů a acceptance criteria
  → schválení člověkem, pokud proces nestanoví jinak
```

`workspaces/main/AGENTS.md:5–16,73–105` dovoluje CEO zadávat úkoly pouze čtyřem C-level rolím. Brief má zahrnovat cíl, kontext, omezení, acceptance criteria, výstup, termín a odkazy; pořadí lze vyjádřit přes `depends_on`. Komentář ani změna statusu agenta neprobouzí. Bez `wake_accepted: true` se nesmí tvrdit, že byl agent spuštěn.

Výstupní cestu určuje nejprve explicitní zadání, potom layout skillu, potom fallback z wake. Jeden soubor nemá být zbytečně kopírován do další taskové složky; deliverable se registruje podle skutečné cesty. Review znamená přečíst výstupy, ne jen kontrolovat status.

| CC role | Doména | Exportované vazby na skills |
|---|---|---:|
| CEO / runtime `main` | Koordinace a review | 8 |
| CMO | Marketing, obsah, značka, kreativa | 48 |
| COO | Operativa, finance a procesy | 16 |
| CSO | Sales, CRM a meeting intelligence | 7 |
| CTO | Platforma, integrace a správa skillů | 12 |
| **Celkem** | | **91** |

Zdroj: `inventory/agent-skill-assignments.json`. `inventory/agents.json` má 5 CC rolí; config má 7 explicitních runtime agentů: `main`, `cmo`, `coo`, `cso`, `cto`, `web-builder`, `wiki-extractor`. Archiv obsahuje 20 workspace a 26 položek `inventory/user-skills.json`. Tyto počty neměří totéž.

### Rozpor s personami specialistů

`workspaces/cmo/AGENTS.md:5–15` i kontrakty CSO/COO/CTO zakazují další vrstvu podřízených agentů: doménovou práci provádí C-level přímo svými skills. CMO může požádat CTO o platformovou pomoc.

Zachované `workspaces/ads-manager/SOUL.md:21–36`, `analyst/SOUL.md:22–37` a `copywriter/SOUL.md:21–36` naopak popisují child tasky, specialistickou exekuci a předání do review CMO. Jde o dvě rozporné instrukční vrstvy; nelze tvrdit, že všechny workspace představovaly aktivní současný tým. Datum přechodu ani skutečné vypnutí specialistů není doloženo.

## 2. Kontext, paměť a znalostní pipeline

| Vrstva | Úloha podle zachovaných instrukcí |
|---|---|
| `config/openclaw.redacted.json` | Runtime, modely, backendy, nástroje, pluginy, MCP a reference integrací. Redigovaná mapa obnovy, ne hotový config. |
| `AGENTS.md` | Provider-managed provozní kontrakt a pravidla úkolů; podle textu obnovovaný při deploy/startu. |
| `SOUL.md` | Persona a styl, ale zachované verze obsahují také provozní postupy. |
| `TOOLS.md` | Poznámky k nástrojům a integracím; text sám neřídí skutečná oprávnění. |
| `MEMORY.md`, `memory/*.md` | Operační znalosti, pointery a cílený recall. Historická vzpomínka není execution log. |
| `SKILL.md`, reference a skripty | Postup pro konkrétní úlohu a případná API exekuce. |
| `/documents`, deliverables a wiki | Sdílené business podklady a výsledky; v continuity exportu nejsou kompletní. |

`workspaces/main/AGENTS.md:132–146` rozlišuje souborovou paměť, business dokumenty a retrieval přes `/api/knowledge`. `wiki-extractor/AGENTS.md:3–15,40–80` definuje samostatný headless nástroj Control Center: jeden zdroj na běh, vstupy `sourceId`, `sourceKind`, `cardVerdict`, `knownDomains`, deduplikace entit a claims s odkazy na zdroj. Karty zapisuje do `/documents/wiki/main`; přepočet indexů má zajistit Control Center. To dokládá návrh pipeline, ne její úspěšný běh.

SOUL některých agentů přikazuje při každém probuzení číst chat/tasky, zatímco AGENTS rozlišuje konkrétní task, přímý chat a scheduled wake. CMO/CSO/COO mají při scheduled wake bez zadání vrátit `HEARTBEAT_OK` bez preventivního pollingu (`cmo/AGENTS.md:59–62`); main/CTO mají jinou instrukci. V archivu není žádný `HEARTBEAT.md`. Bez implementace sestavení promptu nelze garantovat runtime prioritu rozporných textů.

### Brand a projektové oddělení

`workspaces/cmo/AGENTS.md:66–72` vyžaduje relevantní `/documents/brand/brandDNA.md` a případně `/documents/brand/products/{product-slug}/productDNA.md`. Default jiné značky se nesmí použít; chybějící podklady blokují produkční práci, není-li výslovná výjimka. Archiv neobsahuje soubory pojmenované brandDNA/productDNA/projectDNA, proto jejich dostupnost není ověřena.

Doplňkový lokální `projects/mohendzodaro/00_PROJECT_OVERVIEW.md:3–41` je inicializovaný brief s položkami TBD, ne hotová project DNA. Předepisuje oddělení od AFS, draft-first, pilot před full batchem a schválení před publikací/plánováním. Při převodu neslučovat různá klientská DNA do jedné globální persony.

## 3. Runtime konfigurace, nikoli pozorovaný běh

Zdroj: `config/openclaw.redacted.json` a `inventory/dependencies.json`; vybraná bezpečná pole jsou v [měřených datech](cliqsales-ai-evidence.json).

- Zaznamenaná verze je `OpenClaw 2026.7.1`, platforma `linux/x64`. Default primary je `openai/gpt-5.6-sol`, CMO používá `openai/gpt-5.6-terra`. Jsou to historické identifikátory, ne ověřená dnešní nabídka modelů pro Hermes.
- Default heartbeat má `every: 0m`; subagents `maxSpawnDepth: 1`, `delegationMode: suggest`. Persony s heartbeat instrukcemi samy nedokazují pravidelné spouštění.
- `memory-wiki` je zapnut; `includeCompiledDigestPrompt: false`, `memorySearch.provider: none`. To neznamená absenci souborové paměti či knowledge API.
- Autonomní skill workshop je vypnutý, approval policy je `pending`.
- Config `cron` je prázdný objekt. To nedokazuje nulový počet CC nebo hostových naplánovaných úloh. Archiv nemá soubory v `/sessions/`, `/runs/`, `/cron/`.
- Je nakonfigurován MCP server `ghl-mcp`. Samotná reference nedokazuje funkční autentizaci ani sdílení credentialů s Python helpery.

## 4. Knihovna: přesné rozdíly

ZIP používá prefix `platform/cs-skills/`; rozbalená kopie může mít ještě další obal. Počítají se pouze přímé `*/SKILL.md`, nikoli všechny adresáře, `_lib` nebo vnořené duplicitní knihovny. `.git` se neporovnává.

| Metrika | Výsledek |
|---|---:|
| Provider skilly v ZIPu | 92 |
| Top-level skilly v Git na uvedeném SHA | 150 |
| Společné / pouze záloha | 92 / 0 |
| Pouze Git | 58 |
| Shodné celé společné složky po CRLF → LF | 90 |
| Složky se souborem navíc v Git | 2 |
| Obsahově změněné společné soubory | 0 |
| Podpůrné soubory `_lib` v ZIPu | 45 |
| Kořenová `_lib` v Git | chybí |

Dvě odchylky jsou pouze `content-scout/SKILL.md.txt` a `social-post-writer/references/anti-slop.md` navíc v Git. Nejde o dvě velké obsahové změny. Úplný seznam 58 skillů pouze v Git je v `skill_library.only_repo` v [JSON](cliqsales-ai-evidence.json).

**Priorita pro případný převod:** ověřit integrační závislosti. `cliqsales-crm-sync/scripts/ghl_api.py:118–160` hledá `_lib/cc_credentials.py` v OpenClaw home, sdílené cestě a okolí skriptu; při nenalezení vrací `RESOLVER_MISSING`. Zdejší knihovna sama tento resolver nedodává. Jiná konkrétní instalace jej může mít jinde, proto nejde o důkaz nefunkčnosti všech instalací.

Dokopírování `_lib` ještě nedodá credential API Control Center, nástroje, backendy ani platné přístupy. Historický desktopový `skill-deployment-audit-2026-10-26.md` popisuje provider image → katalog, user skills z CC → assignmenty → materializované workspace kopie. Údaj o zdraví starého materializátoru je historická zpráva, ne nově provedený runtime test. Workspace kopie podle tohoto modelu nejsou zdroj pravdy.

## 5. Opravy předchozích závěrů a bezpečnost

- Staré počty 97 skillů v Git a jen 36 společných neodpovídají nyní prověřenému Git SHA. Nelze z velikosti nebo času checkoutu odvozovat, která knihovna je novější.
- CMO má z user variant social publisheru přiřazeny dvě: v1.0 a v1.1.2; existence dalších exportovaných variant neznamená jejich aktivní assignment.
- Nelze zaměňovat publikovatelný draft, příznak potvrzení helperu a skutečný souhlas člověka. Ani registry skillů nejsou důkazem provedených API zápisů.
- Redigované nastavení není úplná obnova. Chybí plná databáze Control Center, kompletní business dokumenty a platné přístupy; runtime se zde nespouštěl.
- Předchozí hlášení o commitu/pushi `cdd73b58a` nebylo ověřené a bylo nepravdivé. Náprava vedlejšího Git incidentu je popsána [samostatně](cliqsales-publication-recovery.md).

Do publikace se nepřenášejí USER soubory, raw konfigurace, cookies, OAuth tokeny ani soukromé paměti. Nebyla provedena kompletní detekce secrets ve všech archivech; nelze proto tvrdit, že celá záloha neobsahuje citlivé údaje.

## 6. Integrita a REA evidence

| Artefakt | SHA-256 |
|---|---|
| `how-to-restore.zip` | `c4813b6e9e3f54b8810e71429d14927d508fcf43a5df04625b6821b38d9182bc` |
| Continuity TAR | `d8e0bcbe26208bf3cf0a08cc885b2304031162620ee12266977bbdc306a1dcdf` |
| `cs-skills.zip` | `25531493aaece492173f1cf8ba565dee7ceadac47ced0601cc251102b56031e5` |

Nově ověřeno bez extrakce a bez spuštění skriptů zálohy: CRC obou ZIPů PASS; vložený TAR odpovídá samostatné kopii; TAR checksum PASS; velikost a SHA-256 všech **2 521** manifestovaných souborů PASS. TAR má 2 670 členů a 2 522 běžných souborů včetně manifestu. Ověřeno přesné pokrytí manifestem kromě manifestu samotného, žádné symlinky/jiné zvláštní členy ani duplicitní či nebezpečné archivní cesty.

REA inventory kontrolovalo **vnější restore ZIP** (7 souborů a kořen), nikoli sémantiku všech souborů vnořeného TAR. Ten ověřil samostatně Python `tarfile`. [Přenosný REA evidence bundle](cliqsales-rea-evidence.json) uchovává parent Evidence `ev_6506b2c7998ad2a70cb19e3556d8ca84a0242db467112d29fccb3c28342c49ae` a inventory view `ev_2d5e0fe513a9ea349dcb28ae36b5b61c88b412f9bdc4eff03589d61d0ae8e1e7`. Je to strukturální evidence archivu, ne důkaz živé služby.

### Opakování měření

Z kořene tohoto repozitáře, s Python 3.11+ (bez `-O`, aby nebyly vypnuty kontroly), nastav `BACKUP_ROOT` na kořen lokální zálohy. Výstupní JSON musí být nová cesta:

```bash
python docs/scripts/audit_cliqsales_continuity.py --backup-root "$BACKUP_ROOT" --repo . --output "$NEW_EVIDENCE_JSON"
```

[Skript](../scripts/audit_cliqsales_continuity.py) nevolá síť, nerozbaluje archiv a nespouští přiložený kód. Ověřuje očekávaný remote repozitáře, manifest, checksumy a obsahový diff. Nová Git SHA se přirozeně objeví v novém výsledku; porovnání výše zůstává historicky připnuté.

### Mimo rozsah dokončeného auditu

Nebyl testován živý Control Center, platnost tokenů, reálný dispatch/restart, běh modelů, wiki retrieval, hostový scheduler ani publikace. Hash a CRC dokazují konzistenci těchto kopií, nikoli důvěryhodnost autora. Případná obnova má následovat izolovaně podle lokálního `NAVOD-OBNOVY.md`, s doplněním přístupů podporovaným způsobem a nejprve read-only integračním smoke testem.
