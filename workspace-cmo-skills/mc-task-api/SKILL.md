---
name: Control Center API
description: Vytvářejte a spravujte úkoly, výstupy, dokumenty a sdílený kontext prostřednictvím Control Center REST API
category: integrations
status: ready
version: "1.1"
publishedAt: "2026-05-08"
---

# Control Center API

Máš přístup k Control Center (CC), tedy k centrálnímu dashboardu orchestrace.
Používej tyto API endpointy pro koordinaci práce, publikování výstupů a práci
se sdíleným kontextem.

## Autentizace

Všechny požadavky vyžadují záhlaví `x-api-key`:

```text
x-api-key: $CC_API_KEY
```

Základní adresa URL: `$CC_URL`

Používej runtime proměnné, ne natvrdo zadané tajné klíče:

- `$CC_URL` = aktuální základní adresa URL Control Center
- `$CC_API_KEY` = aktuální API klíč operátora z runtime prostředí

## Bezpečný helper pro agenty

Preferuj helper `scripts/cc_task.py` před ručním skládáním JSONu v shellu.
Helper čte dlouhé texty ze souboru nebo stdin, JSON skládá bezpečně v Pythonu,
nikdy nevypisuje API klíč a u tvorby úkolu umí idempotency key proti duplicitám
při opakovaném pokusu.

Použij plnou cestu, pokud nejsi přímo v adresáři skillu:

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py get-task 42
```

**Pravidla robustnosti:**

- Nevytvářej JSON ručně přes heredoc, `echo`, `printf` nebo shell interpolaci,
  pokud obsahuje víceřádkový text. Použij helper a `--description-file` /
  `--content-file`.
- Když tvorba úkolu selže po možném `POST /api/tasks`, nereš znovu stejný
  úkol slepě. Použij stejné `--idempotency-key`; helper nejdřív najde již
  vytvořený aktivní task a vrátí ho jako `reused: true`.
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
  --priority medium \
  --status assigned \
  --tag tag1 \
  --tag tag2 \
  --idempotency-key "agent-name:task-title:YYYYMMDDHHMM"
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
- `project_id` (volitelné): celočíselné ID projektu. Výchozí hodnota je `1`.
- `metadata` (volitelné): Libovolný objekt JSON pro další data.

**Aktuální runtime chování:** když je poskytnuto `assigned_to`, Control Center
okamžitě probudí přiřazeného agenta a vrácený task už bude obvykle ve stavu
`in_progress`.

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

**Platné stavy:** `inbox` | `assigned` | `in_progress` | `review` |
`quality_review` | `done` | `blocked` | `failed` | `cancelled`

**Tok stavu:**

```text
inbox -> assigned -> in_progress -> review
review -> done                 [after required quality approval]
review -> in_progress          [after rejection]
any -> blocked | failed | cancelled
```

**Důležité:** přesunutí úkolu do `done` bez požadovaného schválení kvality
vrátí `403`.

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

Deliverables jsou výstupy dokončené práce. Každý úkol by měl produkovat na
alespoň jeden výstup před přechodem ke kontrole.

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
- `approved` požadovaným recenzentem přesune úkol do `done`.
- `rejected` přesune úlohu zpět na `in_progress` a probudí přiděleného agenta.

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

5. **Nejdříve dodání, pak kontrola.** Nikdy nepřesouvejte úkol do `review` bez dodávky.
6. **Vložte skutečný výstup do dodávky.** Recenzent a operátor posoudí, co je tam skutečně uloženo.
7. **Uchovávejte poznatky prostřednictvím výstupů, dokumentů a zdrojových materiálů podporovaných wiki.** Umožněte znovu použít důležité znalosti.
8. **Hlášení stavu z aktuálního běhového prostředí.** Místo hádání použijte samostatný koncový bod nebo seznamy úkolů.
