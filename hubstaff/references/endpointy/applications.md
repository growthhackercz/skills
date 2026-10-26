# Endpoint: `apps` (top aplikace)

Vrací, ve kterých aplikacích člen pracoval během sledovaného času — agregovaně za zvolené období. Užitečné pro pochopení, čím se tým reálně zabývá.

Volá se přes `GET /v2/organizations/{org_id}/applications` s povinným časovým oknem.

CLI: `python3 hubstaff.py apps --from --to [--member] [--limit N] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID záznamu aplikace. |
| `user_id` | číslo | ID člena. |
| `name` | text | Název aplikace, jak ho Hubstaff zachytil z operačního systému (např. `chrome.exe`, `Slack`, `IntelliJ IDEA`, `Figma`). |
| `tracked` | číslo | Celkem sekund, které člen v aplikaci za období strávil. |
| `time_slot` | ISO 8601 | Reprezentativní začátek (typicky první výskyt v období). |
| `project_id` | číslo nebo `null` | Pokud byla aplikace aktivní v době, kdy byl člen na projektu, propojení. |
| `task_id` | číslo nebo `null` | Stejně jako `project_id`, ale pro úkol. |

## Typické použití

- **Top 10 aplikací člena za týden** — orchestrace seřadí podle `tracked` sestupně, vezme prvních 10.
- **Detekce „divných" aplikací** — pokud návrhář tráví 30 % času v Excelu nebo programátor v Outlooku, stojí za otázku.
- **Per-projekt — v čem se ten projekt fakticky dělá** — agregace `tracked` per `name` pro daný `project_id`.

## Příklad výstupu (zkrácený JSON, řazeno podle `tracked`)

```json
[
  {"id": 1, "user_id": 12345, "name": "IntelliJ IDEA", "tracked": 14400, "time_slot": "2026-05-11T08:00:00Z", "project_id": 4567, "task_id": null},
  {"id": 2, "user_id": 12345, "name": "Chrome", "tracked": 7200, "time_slot": "2026-05-11T09:30:00Z", "project_id": 4567, "task_id": null},
  {"id": 3, "user_id": 12345, "name": "Slack", "tracked": 3600, "time_slot": "2026-05-11T10:15:00Z", "project_id": null, "task_id": null}
]
```

## Pozor

- **Vyžaduje, aby tracker měl povolené app tracking** — některé organizace ho mají vypnuté (kvůli GDPR / firemní politice). Pokud je vypnutý, endpoint vrátí prázdné pole, ale neselže.
- **Vyžaduje placený plán** — app tracking je v Premium a vyšších plánech Hubstaffu.
- **Název aplikace závisí na OS** — `Chrome` na macOS, `chrome.exe` na Windows, `google-chrome` na Linuxu. Orchestrace musí normalizovat, pokud chce porovnávat napříč týmem s různými OS.
