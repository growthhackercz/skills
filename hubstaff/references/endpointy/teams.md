# Endpoint: `teams` (týmy organizace)

Vrací seznam týmů — logická seskupení členů uvnitř organizace (např. „Vývoj", „Obchod", „Podpora"). Týmy se v Hubstaffu používají pro filtrování přehledů a přidělování projektů.

Volá se přes `GET /v2/organizations/{org_id}/teams`.

CLI: `python3 hubstaff.py teams [--org ID] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID týmu. |
| `name` | text | Název týmu. |
| `status` | text | `active`, `archived`. |
| `members` | seznam čísel | ID členů (jako `members[].id`), kteří patří do týmu. |
| `created_at` / `updated_at` | ISO 8601 | Časy vzniku a poslední změny. |

## Typické použití

- **Týmový přehled** — agregace hodin nebo aktivity za všechny členy v týmu.
- **Filtr v ad-hoc dotazu** — „kolik hodin tým Vývoj odpracoval minulý týden" → najdi `id` týmu, vezmi `members`, použij jako filtr `--member` na `activities`.
- **Mapování organizační struktury** — pro HR / manažerský přehled, kdo patří kam.

## Příklad výstupu (zkrácený JSON)

```json
[
  {
    "id": 7,
    "name": "Vývoj",
    "status": "active",
    "members": [12345, 67890, 11111],
    "created_at": "2024-09-01T08:00:00Z",
    "updated_at": "2026-03-15T10:30:00Z"
  }
]
```

## Pozor

- Členství v týmu je čistě organizační — neomezuje, na čem může člen pracovat. Člen může být ve více týmech zároveň.
- Pokud organizace týmy nepoužívá, endpoint vrátí prázdný seznam.
- Vrácený seznam `members` je „aktuální stav" — historicky kdo do týmu kdy patřil Hubstaff netrackuje.
