# Endpoint: `time-entries` (časové záznamy)

Vrací **souhrnné záznamy o času** — úseky práce s explicitním začátkem a koncem. Toto je „klasická časová položka" tak, jak ji uživatelé znají z timesheetů: od–do, projekt, úkol, poznámka.

**Rozdíl proti `activities`:**
- `activities` — granulární 10minutové bloky z **automatického sledování** (timer běžel a Hubstaff měřil klávesnici/myš). Žádné ručně přidané hodiny.
- `time-entries` — **souhrnné úseky** vč. **ručně přidaných hodin** (`manual: true`). Pro plnou bilanci „kolik kdo skutečně vykázal" musíte vzít `time-entries`, ne `activities`.

Volá se přes `GET /v2/organizations/{org_id}/time_entries` s povinným časovým oknem.

CLI: `python3 hubstaff.py time-entries --from --to [--member] [--project] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID záznamu. |
| `user_id` | číslo | ID člena, který záznam vykázal. |
| `project_id` | číslo | ID projektu. |
| `task_id` | číslo nebo `null` | ID úkolu (volitelné). |
| `client_id` | číslo nebo `null` | ID klienta (zděděno z projektu). |
| `starts_at` | ISO 8601 | Začátek úseku. |
| `ends_at` | ISO 8601 nebo `null` | Konec úseku. `null` = právě běží (živý timer). |
| `tracked` | číslo | Délka úseku v sekundách. |
| `manual` | bool | `true` = člen hodiny přidal ručně (např. zapomněl spustit timer), `false` = z reálného sledování. |
| `billable` | bool | Zda je čas fakturovatelný klientovi. |
| `paid` | bool | Zda je placený (vázané na `pay_rate` člena). |
| `note` | text nebo `null` | Volitelná poznámka, kterou člen u úseku napsal. |
| `approved_at` | ISO 8601 nebo `null` | Pokud manažer záznam schválil pro fakturaci/výplatu. |
| `created_at` / `updated_at` | ISO 8601 | Čas vzniku záznamu. |

## Typické použití

- **Faktická bilance hodin** (vč. ručních) za období — sečíst `tracked` per `user_id` / `project_id`.
- **Detekce nadměrných ručních úprav** — pokud má člen 60 % `manual: true`, pravděpodobně se zapomíná nahodit, nebo s tím manipuluje.
- **Schvalování fakturace** — filtruj `billable: true, approved_at != null` pro fakturovatelné hodiny.
- **Mzdové podklady** — filtruj `paid: true`, propoj s `members.pay_rate` a získáš odměnu.
- **Poznámky** — `note` je často klíčový kontext, který v `activities` chybí (např. „klientský meeting, řešili jsme změnu rozsahu").

## Příklad výstupu (zkrácený JSON)

```json
[
  {
    "id": 778899,
    "user_id": 12345,
    "project_id": 4567,
    "task_id": 9988,
    "client_id": 88,
    "starts_at": "2026-05-19T08:00:00Z",
    "ends_at": "2026-05-19T12:00:00Z",
    "tracked": 14400,
    "manual": false,
    "billable": true,
    "paid": true,
    "note": "Implementace API pro košík, diskuse s designérem",
    "approved_at": "2026-05-19T15:00:00Z",
    "created_at": "2026-05-19T08:00:05Z",
    "updated_at": "2026-05-19T15:00:00Z"
  }
]
```

## Pozor

- **`activities` vs. `time-entries` — nezaměňovat.** Pro „kolik kdo pracoval" preferujte `time-entries` (vč. ručních hodin). Pro „jak aktivně" `activities` (procenta klávesnice).
- **Živé timery** (`ends_at: null`) — v období, které právě běží, můžete dostat záznamy bez konce. Orchestrace musí ošetřit (typicky vyfiltrovat nebo zobrazit jako „právě běží").
- **Tolerance pro ručně přidané hodiny** je nastavitelná v Hubstaffu per organizace. Některé organizace ruční přidávání zakazují (pak `manual: true` neuvidíte).
- **Schvalování** (`approved_at`) je samostatný proces — neschválené hodiny existují, ale typicky nejdou do fakturace ven.
