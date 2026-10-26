# Endpoint: `urls` (top URL)

Vrací, jaké webové stránky člen navštěvoval během sledovaného času. Stejný princip jako `apps`, ale pro webový prohlížeč.

Volá se přes `GET /v2/organizations/{org_id}/urls` s povinným časovým oknem.

CLI: `python3 hubstaff.py urls --from --to [--member] [--limit N] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID záznamu. |
| `user_id` | číslo | ID člena. |
| `name` | text | URL stránky (typicky doména + cesta, např. `github.com/cliqsales/repo`). |
| `tracked` | číslo | Celkem sekund strávených na stránce v rámci období. |
| `time_slot` | ISO 8601 | Reprezentativní začátek. |
| `project_id` | číslo nebo `null` | Pokud byl člen v té době na projektu. |
| `task_id` | číslo nebo `null` | Pokud byl na úkolu. |

## Typické použití

- **Top 10 navštívených stránek** — `--limit 10`, seřazeno podle `tracked`.
- **Detekce úniků pozornosti** — kolik času na sociálních sítích, YouTube apod. (pokud organizace tracker povolila i mimo „pracovní" software).
- **Per-projekt research stopa** — co konkrétně člen hledal, když dělal na projektu X (filtr `--project`).

## Příklad výstupu (zkrácený JSON)

```json
[
  {"id": 1, "user_id": 12345, "name": "github.com/cliqsales/repo", "tracked": 5400, "time_slot": "2026-05-11T09:00:00Z", "project_id": 4567, "task_id": null},
  {"id": 2, "user_id": 12345, "name": "stackoverflow.com", "tracked": 1800, "time_slot": "2026-05-11T10:30:00Z", "project_id": 4567, "task_id": null}
]
```

## Pozor

- **GDPR / privacy:** URL můžou obsahovat citlivé parametry (tokeny, query stringy s osobními údaji). Pokud generujete pro klienta zprávu s top URL, **maskujte** dlouhé query stringy (např. `example.com/api?token=xxxxx` → `example.com/api`).
- **Vyžaduje URL tracking zapnutý v Hubstaffu** + placený plán.
- **Hubstaff sleduje jen aktivní záložku** prohlížeče. Pozadí (otevřené taby) se nepočítá.
- **HTTPS vs HTTP:** Hubstaff typicky ukládá bez schématu (`example.com/path`), ale konzistentní to není napříč klienty — testujte.
