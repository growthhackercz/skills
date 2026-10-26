---
name: Control Center API
description: Vytvářejte a spravujte úkoly, výstupy, dokumenty a sdílený kontext prostřednictvím Control Center REST API
category: integrations
status: ready
version: "1.9"
publishedAt: "2026-10-05"
---

# Control Center API

Máš přístup k Control Center (CC), tedy k centrálnímu dashboardu orchestrace.
Používej tyto API endpointy pro koordinaci práce, publikování výstupů a práci
se sdíleným kontextem.

## Průběžné uložení rozpracovanosti

Pokud vstup aktuálního běhu výslovně obsahuje `run_id` a `generation` pro
durable progress, po zapsání a registraci smysluplného výstupu a před předáním
další fáze ulož stručný stav. Nevytvářej kvůli fázi další task. Bez těchto údajů
pokračuj běžnou registrací výstupů a komentářů; nic si nedomýšlej.

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py save-progress {task_id} \
  --run-id '{run_id_z_aktualniho_vstupu}' --generation {generation} \
  --request-id '{stabilni_uuid_pro_tento_zapis}' --expected-revision 0 --progress-file -
```

JSON ze stdin obsahuje `phase`, `completed_claims` (objekty `summary`, `evidence`),
`artifacts`, `remaining`, `next_step` (text nebo null), `pending_decisions`,
`decision_refs` a `external_operations`. Prázdné seznamy zapisuj jako `[]`.
Reference výstupu je `{"registry":"deliverables","id":123}` (případně
`task_deliverables`); nejdřív výstup zaregistruj. `completed_claims[].evidence`
odkazuje jen na položky z `artifacts`. Externí operace mají `summary`,
`outcome:"unknown"|"reported_complete"` a `evidence`; hlášené dokončení není důkaz
odeslání či publikace. Nezapisuj obsah dokumentů, hesla ani tokeny.

Začni `expected_revision:0`, další zápis používá vrácené `snapshot.revision`.
Při ztracené odpovědi opakuj přesně stejný JSON/UUID; nový údaj z novějšího běhu
nikdy nepřebírej. Konflikt znamená ověřit stav, ne založit task nebo změnit
generaci. Nejvýše 32 zápisů za běh, ne po každém tool callu nebo časovačem.
Soubory zůstávají autoritou obsahu, stav postupu je jen datované tvrzení agenta.
Uložení neznamená schválení, dokončení úkolu, povolení externí akce ani další běh.
Stejný postup platí pro AIQ, HTML prezentaci i práci bez specializovaného skillu.

## Autentizace

Všechny požadavky vyžadují záhlaví `x-api-key`:

```text
x-api-key: $CC_API_KEY
```

Základní adresa URL: `$CC_URL`

Používej runtime proměnné, ne natvrdo zadané tajné klíče:

- `$CC_URL` = aktuální základní adresa URL Control Center
- `$CC_API_KEY` = aktuální API klíč operátora z runtime prostředí

**Když dostaneš 401:** zkontroluj, že posíláš hlavičku `x-api-key` — `Authorization: Bearer`
CC API nepodporuje a vrátí 401 vždy. `$CC_API_KEY` se při aktualizacích platformy NEMĚNÍ;
401 tedy neznamená „rozešel se klíč" — než začneš stavět teorie o infrastruktuře, porovnej
svůj request přesně s příklady v tomhle dokumentu.

Hodnoty `***`, `[masked]`, `[redacted]`, `OPENCLAW_REDACTED` a
`__OPENCLAW_REDACTED__` jsou pouze zobrazovací zástupné hodnoty z historie. Nikdy
je nepoužívej jako klíč, nezapisuj je do skriptu a neopakuj s nimi požadavek.
V shell příkazu zachovej odkaz `$CC_API_KEY` nebo `${CC_API_KEY}` a nech jej
vyhodnotit až shellem. Odpověď `401` s kódem `AUTH_REDACTED_PLACEHOLDER`
znamená chybu sestavení příkazu: znovu jej vytvoř přes helper/runtime proměnnou.
Neotáčej kvůli tomu credential, nepřepínej providera ani nerestartuj runtime.
Obyčejné `401` bez tohoto kódu zůstává běžným auth selháním a vyžaduje ověřit
aktuální runtime konfiguraci.

## Bezpečný helper pro agenty

Preferuj helper `scripts/cc_task.py` před ručním skládáním JSONu v shellu.
Helper čte dlouhé texty ze souboru nebo stdin, JSON skládá bezpečně v Pythonu,
nikdy nevypisuje API klíč a u tvorby úkolu umí idempotency key proti duplicitám
při opakovaném pokusu.

Použij plnou cestu, pokud nejsi přímo v adresáři skillu:

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py get-task 42
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py list-tasks \
  --assigned-to cto --status inbox,assigned,in_progress --limit 10
```

Pro čtení úkolů v heartbeatu, cronu nebo skriptu používej `list-tasks` /
`get-task`, ne ruční `curl … | python3 -c "…d.get('tasks', [])"`. Helper si klíč
bere z prostředí, takže v příkazu ani historii není hlavička s klíčem. Při
chybě autorizace nebo sítě skončí nenulovým kódem a vypíše status na stderr.
Ruční parsování naopak z odpovědi `401` tiše udělá „0 úkolů".

**Pravidla robustnosti:**

- Nevytvářej JSON ručně přes heredoc, `echo`, `printf` nebo shell interpolaci,
  pokud obsahuje víceřádkový text. Použij helper a `--description-file` /
  `--content-file`.
- Když tvorba úkolu selže po možném `POST /api/tasks`, nereš znovu stejný
  úkol slepě. Použij stejné `--idempotency-key` a stejné původní zadání.
  Helper vždy volá `POST /api/tasks`; Control Center v jedné transakci vrátí
  existující task jako `reused: true`, nebo založí nový. Opakované volání
  neprobouzí agenta podruhé a není omezené na prvních 200 úkolů.
- Klíč patří původnímu zadání a původnímu přiřazení v daném workspace.
  `task_idempotency_conflict` znamená jiné zadání pod stejným klíčem: načti
  existující task a uprav jej přes běžné API. Neobcházej konflikt náhodným klíčem.
  `task_idempotency_ambiguous` znamená nejednoznačná historická data; vyžádej
  výběr existujícího úkolu. Žádné automatické mazání ani slučování.
- `task_recovery_required` znamená, že původní task je zrušený nebo selhal.
  Nezakládej náhradní úkol; vyžádej explicitní obnovení existujícího.
  `resume-task` je pouze pro operátorem pozastavený běh, nikoli zrušený task.
- Při `legacy_idempotency: true` chybí otisk původního zadání. Task byl pouze
  nalezen podle historického klíče; nejdřív ověř jeho obsah a stav.
- `metadata.idempotency_key` a serverové `metadata.cc_task_creation` po vytvoření
  neměň ani nekopíruj do nového tasku. Helper 1.4 vyžaduje odpovídající verzi CC
  s podporou serverové idempotence; před zápisem ji ověřuje přes `HEAD /api/tasks`.
  Pokud podpora chybí, žádný task nevytvoří. Nepublikuj jej samostatně na starší backend.
- Nepoužívej pattern `curl ... | python3 - <<'PY'`; heredoc obsadí stdin a
  Python pak nečte odpověď z `curl`. Ulož odpověď do souboru, nebo použij
  helper.
- Pro nadpisy do shell logu používej `printf '%s\n' '--- text ---'`, ne
  `printf '--- text ---\n'`; některé `/bin/sh` implementace berou počáteční
  `--` jako volbu.

## Správa úloh

### Vytvořit úkol

```bash
cat > /tmp/task-description.md <<'EOF'
Detailed description
EOF

python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py create-task \
  --title "Task title" \
  --description-file /tmp/task-description.md \
  --assigned-to agent_name \
  --project-id 5 \
  --priority medium \
  --status assigned \
  --tag tag1 \
  --tag tag2 \
  --metadata-json '{"cc_delegation_origin_input":{"conversation_id":"coord:operator:ceo:0123456789ab","message_id":123}}' \
  --idempotency-key "agent-name:project:requested-work"
```

**Pole:**

- `title` (povinné, max. 500 znaků): Jasný a použitelný název.
- `description` (volitelné, max. 5000 znaků): Podrobný kontext, požadavky a odkazy.
- `assigned_to` (volitelné, max. 100 znaků): Jméno agenta nebo klíč relace, jako je `ceo`, `cmo`, `cso`, `coo`, `cto`.
- `priority`: `low` | `medium` (výchozí) | `high` | `critical`
- `status`: `inbox` (výchozí) | `assigned` | `in_progress`
- `tags`: Pole řetězců, např. `["marketing", "urgent"]`
- `due_date` (volitelné): Časové razítko Unix (v sekundách).
- `estimated_hours` (volitelné): Číslo >= 0.
- `parent_task_id` (volitelné): Celočíselné ID rodičovské úlohy pro podřízené úlohy.
- `depends_on` (volitelné, max. 500 znaků): Popis závislosti volného textu.
- `project_id` (volitelné): celočíselné ID projektu. U projektové práce ho
  posílej vždy. Při vynechání Control Center převezme projekt rodičovského
  tasku nebo jediného jednoznačně odkazovaného `tasku #N`; nejednoznačný či
  neexistující odkaz odmítne. Pouze skutečně ad-hoc práce bez takové vazby
  spadne do výchozí Operativy.
- `metadata` (volitelné): Libovolný objekt JSON pro další data.
- `metadata.cc_delegation_origin_input` (volitelné pouze pro koordinátorem
  delegovaný top-level task): použij přesné `conversation_id` a `message_id`
  vložené do aktuálního CEO chatového zadání. CC je serverově ověří, vstupní
  namespace před uložením odstraní a podle workspace nastavení do tohoto chatu
  vrátí handoff. Nevymýšlej je a nepoužívej je pro child tasky nebo běhy mimo
  operátorský chat.

Approval policy nastavuje Control Center podle autentizovaného ingressu. Agent
ji nesmí vkládat do metadata ani posílat jako `approval_policy`: top-level task
vytvořený agentem čeká po interní kontrole na operátora, interní child task
používá quality review.

**Aktuální runtime chování:** když je poskytnuto `assigned_to`, Control Center
okamžitě probudí přiřazeného agenta a vrácený task už bude obvykle ve stavu
`in_progress`.

Task vždy vytvoř před zahájením práce. Nevytvářej po dokončení práce nový task
rovnou ve `review`, `done`, `blocked` ani jiném navazujícím stavu jako pouhou
evidenci — create endpoint takový stav odmítne, aby už hotovou práci omylem
nespustil znovu. Existující task posouvej do `review` až přes `update-task` po
registraci výstupů.

**Odpověď (201):**

```json
{ "task": { "id": 42, "title": "...", "status": "in_progress", ... } }
```

### Aktualizovat úkol

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py update-task {task_id} \
  --status review
```

Všechna pole od vytvoření jsou aktualizovatelná. Zahrňte pouze pole, která chcete změnit.
Další aktualizovatelné pole:

- `actual_hours` (číslo >= 0): Sledujte strávený čas.

Po každé změně stavu znovu načtěte úkol a ověřte výsledný stav. Neříkejte, že
úkol přešel do `review`, dokud `GET /api/tasks/{task_id}` skutečně nevrátí
`status: "review"`. Pokud ověření selže, vraťte přesnou odpověď API.

Změna stavu na `in_progress` není restart. Přiděleného agenta probudí jen
poprvé; opakované vrácení stejného úkolu do `in_progress` nový běh nespustí.
K popohnání řešitele použij `wake-task` níže.

**Platné stavy:** `inbox` | `assigned` | `in_progress` | `review` |
`quality_review` | `done` | `blocked` | `failed`

**Tok stavu:**

```text
inbox -> assigned -> in_progress -> review
review -> done                 [child po quality approval, top-level po operator decision]
review -> in_progress          [after rejection]
any -> blocked | failed | cancelled
```

`cancelled` není běžný update. Zrušení musí nejdřív bezpečně zastavit přesný
běh úkolu, proto vždy použij `cancel-task` nebo `cancel-tasks` níže. Odpověď
`task_cancel_endpoint_required` neopakuj přes jiný status endpoint.

**Důležité:** přesunutí úkolu do `done` bez rozhodnutí požadovaného aktuální
policy a review revize vrátí `403`.

Pokud update vrátí `409 task_resume_decision_required`, task byl operátorem
zastavený. Nezkoušej update opakovat, netvrď, že agent pokračuje, a nepropojuj
task s další zprávou jen podle podobnosti tématu. Bez explicitního rozhodnutí
operátora zůstává task pozastavený.

### Přidat komentář

Pro víceřádkový komentář použij soubor nebo stdin, aby shell neměnil obsah:

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py add-comment {task_id} \
  --content-file /tmp/task-comment.md
```

Pro odpověď ve vlákně přidej `--parent-id {comment_id}`. `--author` používej jen
pro vlastní kanonické jméno agenta; jinak jej vynech a nech autora odvodit z
ověřeného požadavku.

Komentář pouze uloží sdělení a spustí existující notifikační pravidla. Sám o
sobě úkol neschválí, nevrátí k přepracování, nezmění stav a neobnoví operátorem
zastavený běh. Pro takové rozhodnutí použij odpovídající task/UI flow; nevytvářej
náhradní úkol jen proto, že komentář nezměnil stav. Přiděleného agenta komentář
nespustí; uvidí ho až při svém dalším běhu.

### Popohnat řešitele u existujícího úkolu

Komentář, změna priority nebo termínu ani opakované vrácení stavu na
`in_progress` přiděleného agenta nespustí. Když má agent na existujícím úkolu
začít nebo pokračovat (nový pokyn, nová informace, odstraněná překážka,
urgence operátora), použij:

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py wake-task {task_id} \
  --message-file /tmp/wake-pokyn.md
```

Helper ověří úkol a přiděleného agenta, přes `GET /api/tasks/{id}/run-control`
zjistí, jestli na úkolu už neběží práce, a teprve potom zavolá
`POST /api/agents/wake` s `task_id`. Agent naběhne v sezení úkolu a Control
Center k pokynu samo přidá celé zadání. Do pokynu proto nepiš znovu zadání, ale
co je nového, jeden konkrétní krok, který se vejde do jednoho běhu, a jak má
výsledek zapsat. Stejný text podruhé nový běh nespustí.

Výsledek:

- `"wake_accepted": true` — Control Center probuzení přijalo a běh (`run_id`)
  zařadilo. Operátorovi napiš, koho a s jakým krokem jsi probudil. Že agent na
  úkolu skutečně pracuje, tvrď až když `run-state {task_id}` vrátí
  `"state": "active"`.
- `"wake_accepted": false` s `reason` — nic se nespustilo:
  - `run_active` — na úkolu už se pracuje; nebuď znovu.
  - `run_paused` — operátor běh zastavil; pokračuj jen přes `resume-task` po
    jeho výslovném rozhodnutí.
  - `run_unavailable` / `run_ambiguous` — stav nejde ověřit; netvrď, že se
    pracuje ani že se nepracuje.
  - `replayed` — stejný pokyn už byl zpracován; formuluj nový konkrétní krok.
  - jiný důvod — uveď ho operátorovi přesně.

Úkol ve stavu `review`, `quality_review`, `done`, `failed` nebo `cancelled`
helper odmítne; použij review nebo operátorský flow. Když běh skončí bez
výsledku, zkus nejvýše jeden další, menší krok a pak operátorovi popiš, co brání
dokončení. Hromadné komentáře nebo termíny do více úkolů nejsou řízení práce.

Aktuální stav běhu úkolu bez probouzení:

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py run-state {task_id}
```

### Bezpečně zrušit úkol

Jeden úkol:

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py cancel-task {task_id}
```

Helper vytvoří operation UUID a volá výhradně `POST /api/tasks/{id}/cancel`.
Zrušení nemaže soubory ani výstupy. `stopping` nebo `unconfirmed` není hotové
zrušení; použij stejné `--operation-id` a ověř stav, nevytvářej novou operaci
naslepo.

Hromadné zrušení vždy začni náhledem bez zápisu. Následující příklad vybere jen
blokované úkoly, které byly vytvořené i naposledy změněné před uvedeným Unix
časem:

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py cancel-tasks \
  --status blocked \
  --created-before 1788307200 \
  --updated-before 1788307200 \
  --note "archiv 9. 9. 2026" \
  --dry-run
```

Po kontrole spusť stejný příkaz bez `--dry-run`. Helper načte všechny stránky,
odešle přesné snapshoty `id + status + updated_at` po dávkách nejvýše 100 a
server před prvním zápisem každé dávky ověří, že se žádný úkol nezměnil. Pro
opakování přerušeného zápisu použij stejné `--operation-id` z prvního výsledku.
Helper operation ID vypíše ještě před prvním zápisem, takže zůstane dohledatelné
i při síťovém přerušení.

Alternativně použij `--tasks-file soubor.json`. Soubor může být seznam úkolů
nebo odpověď `{ "tasks": [...] }`; každý záznam musí obsahovat `id`, `status` a
`updated_at`. Bulk cesta používá stejný cancellation engine jako jeden úkol,
ale neposílá stovky jednotlivých chatových a administrátorských notifikací.
Každý skutečně zrušený úkol má vlastní auditní záznam s batch operation ID a
volitelnou poznámkou.

### Explicitně pokračovat v zastaveném úkolu

Použij pouze když operátor výslovně potvrdil pokračování v konkrétním tasku:

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py resume-task {task_id} \
  --clarification "Doplnění potvrzené operátorem"
```

Bez doplnění vynech `--clarification`. Helper vytvoří operation UUID a použije
idempotentní execution-decision endpoint. Úspěch je pouze odpověď
`outcome: "resumed"`; teprve potom smíš říct, že agent znovu pokračuje.
`resuming` znamená neověřený/in-flight výsledek a nesmí se slepě opakovat s
novým operation ID.

### Seznam úkolů

```bash
curl -s "$CC_URL/api/tasks" \
  -H "x-api-key: $CC_API_KEY"
```

**Volitelné parametry dotazu:**

- `status` -- filtrování podle jednoho nebo více stavů, např. `?status=in_progress,review`
- `assigned_to` -- filtrovat podle názvu agenta, např. `?assigned_to=cmo`
- `priority` -- filtrovat podle priority, např. `?priority=high`
- `project_id` -- filtrovat podle projektu
- `limit` -- maximální počet výsledků, výchozí 50, max. 200
- `offset` -- posun stránkování

**Odpověď:**

```json
{ "tasks": [...], "total": 15, "page": 1, "limit": 50 }
```

### Získat jeden úkol

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py get-task {task_id}
```

### Získat standup report

```bash
curl -s -X POST $CC_URL/api/standup \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{}'
```

**Volitelná pole těla:**

- `date`: Cílové datum ve formátu `YYYY-MM-DD` (výchozí nastavení je dnes).
- `agents`: Pole názvů agentů k filtrování, např. `["cmo", "cto"]`.

**Obálka odpovědi:** `{ "standup": { ... } }`

Vnořený samostatný objekt obsahuje `summary`, `agentReports`,
`teamAccomplishments`, `teamBlockers` a `overdueTasks`.

## Deliverables

Deliverables jsou úplné kontrolovatelné výstupy: buď finální dodávka, nebo
výslovný rozhodovací checkpoint. Každý úkol musí mít před přechodem ke kontrole
alespoň jeden výstup odpovídající tomu, co má operátor právě posoudit.

### Idempotentní checkpoint pro rozhodnutí operátora

Když skill narazí na explicitní schvalovací STOP u již existujícího tasku,
neukončuj pouze run s otázkou v textu. Ulož celý lokalizovaný rozhodovací obsah
jako textový deliverable a task vystav v `review` jedním retry-safe helperem:

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py request-review-checkpoint \
  --task-id 42 \
  --title "[lokalizovaný stabilní název checkpointu]" \
  --created-by cso \
  --content-file - <<'CHECKPOINT'
[úplný text rozhodnutí, možnosti a doporučení v jazyce klienta]
CHECKPOINT
```

Helper přijímá pouze task v `in_progress|review`, před zápisem hledá
byte-exact textový deliverable se stejným názvem a autorem a při retry jej
znovu použije. Stejný název s jiným obsahem je konflikt, ne pokyn k vytvoření
duplicity. Task `in_progress` přesune do `review`; task, který už v `review` je,
tam ponechá. Pokud kterýkoli krok selže, automaticky ho neopakuj naslepo a
neprezentuj checkpoint jako úspěšně odevzdaný.

Název i obsah vždy lokalizuj podle jazyka aktuální konverzace. Technický helper
nepřekládá text a nesmí z otázníku nebo formulace odpovědi odvozovat lifecycle
stav. Skutečný runtime `waiting_for_user` je jiný kontrakt.

### Vytvořit deliverable

```bash
cat > /tmp/deliverable.md <<'EOF'
FULL output here - the complete deliverable text, not a summary.
EOF

python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py create-deliverable \
  --task-id 42 \
  --title "Instagram Posts - Ethiopia Sidamo" \
  --type text \
  --content-file /tmp/deliverable.md \
  --created-by cmo
```

**Pole:**

- `task_id` (požadováno pro výstupy úkolu): Úkol, ke kterému tento výstup patří.
- `title` (povinné): Popisný název.
- `type` (vyžadováno): `text` | `report` | `file` | `link`
- `content` (vyžadováno pro text/report): Úplný doručitelný obsah.
- `file_path` (volitelné): Cesta k vygenerovanému souboru, např. `/documents/output/report.pdf`.
- `created_by` (volitelné): Jméno agenta. Výchozí hodnota je ověřený uživatel.

**Kritická pravidla:**

1. **Nejdříve dodávka, potom kontrola.** Před přesunem úkolu do `review` vytvořte dodávku.
2. **Je vyžadován úplný obsah.** Neukládejte pouze souhrn, pokud je skutečným výstupem text.
3. **Jeden výstup na koherentní výstup.** Spojte související textové položky dohromady, pokud patří k jednomu výsledku.
4. **Upřednostňujte `type: "file"` pro binární soubory.** Rozhraní API normalizuje původní hodnoty `image` a `document` na `file`, ale v nových voláních použijte `file`.

### Seznam deliverables

```bash
curl -s "$CC_URL/api/deliverables?task_id=42" \
  -H "x-api-key: $CC_API_KEY"
```

**Parametry dotazu:**

- `task_id` -- filtrovat podle úkolu
- `created_by` -- filtrovat podle agenta
- `limit` -- maximální počet výsledků (výchozí 50)

## Kontrola kvality

Použijte toto, když nadřazený agent na úrovni C kontroluje podřízenou úlohu již v `review`.

### Odeslat quality review

```bash
curl -s -X POST $CC_URL/api/quality-review \
  -H "Content-Type: application/json" \
  -H "x-api-key: $CC_API_KEY" \
  -d '{
    "taskId": 42,
    "reviewer": "cmo",
    "status": "approved",
    "notes": "Output is acceptable. Proceeding to the next phase."
  }'
```

**Pravidla:**

- Použijte `/api/quality-review` ke schválení nebo odmítnutí podřízeného úkolu již v `review` nebo `quality_review`.
- **ne** vynucujte si schválení zasláním `status: "done"` přímo na `/api/tasks/{id}`.
- `approved` požadovaným recenzentem přesune interní `quality` task do `done`.
  U top-level `operator` tasku pouze zaznamená interní kontrolu a task zůstane
  v `review`, dokud ho operátor neschválí v Control Center.
- `rejected` přesune úlohu zpět na `in_progress` a probudí přiděleného agenta.
- Nikdy nevolejte `/api/tasks/{id}/operator-decision`; přijímá pouze skutečnou
  operátorskou session a API key správně odmítne.

## Dokumenty a kontext Wiki

Sdílené důkazy žijí pod `DOCUMENTS_PATH`. Ve výchozích lokálních runtimech to je
obvykle `/documents/`.

### Seznam dokumentů

```bash
curl -s "$CC_URL/api/knowledge?search=brand&limit=20" \
  -H "x-api-key: $CC_API_KEY"
```

**Užitečné parametry dotazu:**

- `agent` -- filtrovat dokumenty podle jména agenta
- `path_prefix` -- omezení na jeden podstrom
- `source_type` -- omezení na jeden typ zdroje
- `search` -- vyhledejte `original_name`, `description` a extrahovaný text
- `latest=0` -- zahrnout starší revize
- `limit` -- maximální počet výsledků, omezen na 500

**Odpověď:**

```json
{
  "documents": [
    {
      "id": 1,
      "original_name": "brand-guide.pdf",
      "path": "brands/client-a/brand-guide.pdf",
      "file_type": "pdf",
      "agent_name": "cmo"
    }
  ]
}
```

### Přečtěte si dokument

Použijte příkazy shellu proti kanonickému sdílenému kořenovému adresáři:

```bash
test -f "/documents/{path}" && sed -n '1,200p' "/documents/{path}"
```

Pole `path` z odpovědi API je relativní ke kořenu sdílených dokumentů.
Nečtěte ani nezapisujte místní `documents` adresáře pracovního prostoru; oni nejsou
objem sdílených dokumentů.

### Jak nyní fungují sdílené znalosti

Primární sdílený kontext nyní pochází z:

- dokumenty a výstupy související s úkoly
- registr dokumentů (`/api/knowledge`)
- wiki zdrojové a syntetické stránky pod `DOCUMENTS_PATH/wiki/main`
- nástroje nativní paměti/wiki, pokud jsou dostupné za běhu

Dokončené úkoly, výstupy text/report, nahrané dokumenty a těla e-mailů
se automaticky změní na zdrojové stránky wiki. Nepotřebujete manuál
krok požití.

## Workflow Pravidla

### Pro generálního ředitele (koordinátora)

1. **Směrujte práci pouze vlastníkům úrovně C.** Jako příjemce použijte `cmo`, `cso`, `coo` nebo `cto`.
2. **Nejprve zkontrolujte sdílený kontext.** Než napíšete zadání úkolu, zkontrolujte dokumenty, výstupy a kontext wiki.
3. **Před vytvořením nové práce zkontrolujte existující práci.** Nejprve uveďte příslušné úkoly, abyste nevytvářeli paralelní duplikáty.
4. ** Pečlivě zkontrolujte kvalitu.** Když úkol dosáhne kontroly, přečtěte si dodaný obsah, než jej schválíte nebo zamítnete.
5. **Řešitele popoháněj přes `wake-task`.** Komentář ani změna stavu, priority nebo termínu práci nespustí. Bez `"wake_accepted": true` netvrď, že jsi agenta spustil.

#### Zachování delivery intentu

Při vytváření tasku zachovej cílový výstup z požadavku operátora. Nepřepisuj
produkční požadavek na pouhý ruční/review deliverable, pokud o to operátor
výslovně nepožádal.

Pro social posty na `facebook`, `instagram` nebo `linkedin` platí:

- Výchozí delivery target je CliqSales/GHL Social Planner `draft`.
- CMO task má explicitně požadovat social pipeline až do `cliqsales-social-publisher`.
- Acceptance criteria mají obsahovat vytvoření `social-posts.md`, `social-posts.json`, případných médií a CliqSales draftu.
- CMO má vrátit draft ID, nebo přesnou chybu publisheru.
- Ruční/review-only výstup použij jen pokud operátor řekl „jen text“, „jen návrh“, „bez draftu“, „nezakládat do CliqSales“ nebo podobně.
- Chybějící nebo operátorem přeskočený brand neznamená `manual_review`; znamená unbranded draft s poznámkou o chybějícím brand kontextu.

### Pro všechny agenty

6. **Nejdříve dodání, pak kontrola.** Nikdy nepřesouvejte úkol do `review` bez dodávky.
7. **Vložte skutečný výstup do dodávky.** Recenzent a operátor posoudí, co je tam skutečně uloženo.
8. **Uchovávejte poznatky prostřednictvím výstupů, dokumentů a zdrojových materiálů podporovaných wiki.** Umožněte znovu použít důležité znalosti.
9. **Hlášení stavu z aktuálního běhového prostředí.** Místo hádání použijte samostatný koncový bod nebo seznamy úkolů.
