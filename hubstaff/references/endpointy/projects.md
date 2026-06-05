# Endpoint: `projects` (projekty organizace)

Vrací seznam projektů v organizaci. Projekt je hlavní organizační jednotka pro sledování času — každý záznam aktivity je přiřazen k projektu (a volitelně k úkolu pod projektem).

Volá se přes `GET /v2/organizations/{org_id}/projects`.

CLI: `python3 hubstaff.py projects [--org ID] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID projektu. Používejte ve filtrech `--project`. |
| `name` | text | Název projektu. |
| `status` | text | `active`, `archived`. |
| `description` | text | Volitelný popis. |
| `client_id` | číslo nebo `null` | ID klienta, pokud je projekt vázán na klienta (CRM-like funkce Hubstaffu). |
| `billable` | bool | Zda se projekt fakturuje klientovi. |
| `budget` | objekt | Rozpočet projektu (viz níže). |
| `created_at` / `updated_at` | ISO 8601 | Časy vzniku a poslední změny. |

### Pole `budget` — struktura

| Podpole | Typ | Popis |
|---|---|---|
| `type` | text | `hours` (rozpočet v hodinách) nebo `money` (rozpočet v penězích). |
| `budget` | číslo | Velikost rozpočtu (např. `100` = 100 hodin nebo 100 jednotek měny). |
| `currency` | text | Měna (pro `type: money`). |
| `remaining` | číslo | Kolik z rozpočtu ještě zbývá (Hubstaff počítá průběžně). |
| `used_percent` | číslo | Procento využití rozpočtu. |

`budget` může být `null`, pokud projekt rozpočet nemá.

## Typické použití

- **Detekce přepálení rozpočtu** — orchestrace projde projekty a kde `budget.used_percent > 100`, vystaví upozornění.
- **Sledování stavu klientských projektů** — propojení `client_id` s vlastním CRM a generování měsíčních přehledů.
- **Mapování ID projektu na název** v přehledu nad `activities`.

## Příklad výstupu (zkrácený JSON)

```json
[
  {
    "id": 4567,
    "name": "Redesign e-shopu",
    "status": "active",
    "client_id": 88,
    "billable": true,
    "budget": {
      "type": "hours",
      "budget": 120,
      "remaining": 23.5,
      "used_percent": 80.4
    },
    "created_at": "2026-02-10T08:00:00Z",
    "updated_at": "2026-05-18T16:30:00Z"
  }
]
```

## Pozor

- Pokud chcete vidět **kdo na projektu pracuje**, potřebujete navíc dotaz na `members` (Hubstaff nemá v `projects` přiřazení členů automaticky).
- `budget` v Hubstaffu odráží `tracked` (zaznamenaný sledovaný čas), ne `manual` (ručně přidané hodiny bez sledování). Pokud tým hodně přidává ručně, čísla `used_percent` můžou být zavádějící.
