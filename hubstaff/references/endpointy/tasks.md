# Endpoint: `tasks` (úkoly organizace)

Vrací úkoly v organizaci. Úkol v Hubstaffu je položka pod projektem — drobnější jednotka práce, kterou si člen vybere při startu sledování (např. projekt „Redesign e-shopu" → úkol „Implementace košíku").

Volá se přes `GET /v2/organizations/{org_id}/tasks`.

CLI: `python3 hubstaff.py tasks [--org ID] [--project ID] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID úkolu. |
| `summary` | text | Stručný název úkolu (titulek). |
| `project_id` | číslo | ID projektu, pod kterým úkol visí. |
| `status` | text | `active`, `completed`, `archived`. |
| `due_at` | ISO 8601 nebo `null` | Termín dokončení (deadline). |
| `assignees` | seznam čísel | ID členů přiřazených k úkolu. |
| `lock_version` | číslo | Interní verze pro optimistické zamykání (Hubstaff používá při updatech). |
| `created_at` / `updated_at` | ISO 8601 | Časy vzniku a poslední změny. |

## Filtrování

`--project ID` (lze opakovat) — omezí na úkoly konkrétního projektu (jinak vrací všechny úkoly organizace, což u větších týmů může být hodně).

## Typické použití

- **Co dělal člen reálně** — propojení `activities.task_id` s `tasks.summary` ukáže lidsky čitelný popis práce, ne jen ID.
- **Stav úkolů projektu** — kolik je `active`, `completed`, kolik je po `due_at`.
- **Workload per člen** — agregace přes `assignees`, kolik aktivních úkolů má kdo.

## Příklad výstupu (zkrácený JSON)

```json
[
  {
    "id": 9988,
    "summary": "Implementace košíku",
    "project_id": 4567,
    "status": "active",
    "due_at": "2026-05-31T23:59:59Z",
    "assignees": [12345],
    "lock_version": 3,
    "created_at": "2026-05-01T08:00:00Z",
    "updated_at": "2026-05-15T14:20:00Z"
  }
]
```

## Pozor

- **Úkol je volitelný** — člen si při startu sledování nemusí úkol vybrat, jen projekt. Pak `activities.task_id` bude `null`.
- **Bez `--project` filtru** vrátí všechny úkoly organizace — u velkých klientů to může být tisíce záznamů a několik stránek paginace. Pokud potřebujete jen jeden projekt, filtrujte.
- **Vlastní třídění:** vrácené pořadí závisí na Hubstaffu (typicky podle `created_at` sestupně), orchestrace si pořadí může změnit klient-side.
