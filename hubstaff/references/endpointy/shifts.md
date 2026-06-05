# Endpoint: `shifts` (plánované směny)

Vrací **naplánované směny** členů — kdy mají podle rozvrhu pracovat. Toto **není** záznam o tom, jestli reálně pracovali (to vrací `activities`) — je to plán, vůči kterému se realita porovnává.

Volá se přes `GET /v2/organizations/{org_id}/shifts` s povinným časovým oknem.

CLI: `python3 hubstaff.py shifts --from --to [--member] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID směny. |
| `user_id` | číslo | ID člena, kterému je směna naplánována. |
| `job_site_id` | číslo nebo `null` | ID pracoviště (Hubstaff má koncept „job sites" — fyzické lokace pro terénní práci). |
| `starts_at` | ISO 8601 | Plánovaný začátek směny. |
| `ends_at` | ISO 8601 | Plánovaný konec. |
| `time_zone` | text | Časové pásmo, ve kterém je směna definována (důležité — `starts_at` je vždy v UTC, ale plánoval ji někdo v lokálním čase). |
| `status` | text | `scheduled` (naplánovaná, ještě neproběhla), `in_progress`, `completed`, `missed`, `late`, `cancelled`. |
| `late_started_at` | ISO 8601 nebo `null` | Pokud člen začal pozdě, tady je čas reálného začátku. |
| `actual_starts_at` / `actual_ends_at` | ISO 8601 nebo `null` | Reálný čas, pokud směna proběhla. |
| `notes` | text | Volitelná poznámka k směně. |

## Stavy směny (`status`)

- **`scheduled`** — naplánovaná, ještě nepřišel čas.
- **`in_progress`** — právě probíhá (člen sleduje).
- **`completed`** — proběhla úspěšně.
- **`missed`** — naplánovaná směna proběhla, ale člen vůbec nezačal sledovat. **Toto je „zameškaná směna"** — typický cíl monitorování.
- **`late`** — člen začal sledovat, ale se zpožděním (víc než tolerance povolená v Hubstaff nastavení).
- **`cancelled`** — směna byla zrušena (manažerem nebo členem).

Pozor: `status` Hubstaff vyhodnocuje automaticky, ale s mírnou prodlevou. Pro směnu, která právě skončila před 5 minutami a člen nezačal, může status být ještě `scheduled` (než se přepočítá). Orchestrace na to spoléhá málo a porovnává `activities` ručně.

## Typické použití

- **Detekce zameškaných směn** za období: filtruj `status: missed`.
- **Detekce opožděných začátků:** filtruj `status: late` a koukni na `late_started_at` vs. `starts_at`.
- **Adherence k rozvrhu:** % směn v `completed` vs. celkový počet.
- **Vlastní detekce „zameškané"** (pokud nechceš spoléhat na Hubstaff status): stáhni `shifts` + `activities` ve stejném okně, pro každou směnu spočítej, zda existuje aspoň jedna aktivita stejného `user_id` v okně `[starts_at, ends_at]`.

## Příklad výstupu (zkrácený JSON)

```json
[
  {
    "id": 111,
    "user_id": 12345,
    "job_site_id": null,
    "starts_at": "2026-05-19T07:00:00Z",
    "ends_at": "2026-05-19T15:00:00Z",
    "time_zone": "Europe/Prague",
    "status": "completed",
    "late_started_at": null,
    "actual_starts_at": "2026-05-19T07:02:00Z",
    "actual_ends_at": "2026-05-19T15:08:00Z",
    "notes": null
  },
  {
    "id": 112,
    "user_id": 67890,
    "job_site_id": null,
    "starts_at": "2026-05-19T08:00:00Z",
    "ends_at": "2026-05-19T16:00:00Z",
    "time_zone": "Europe/Prague",
    "status": "missed",
    "late_started_at": null,
    "actual_starts_at": null,
    "actual_ends_at": null,
    "notes": null
  }
]
```

## Pozor

- **Vyžaduje, aby organizace měla rozvrhy nastavené.** Pokud tým funguje bez naplánovaných směn (volný flexibilní režim), tento endpoint vrátí prázdné pole — to není chyba.
- **Tolerance pozdního startu** (kolik minut po `starts_at` se ještě počítá včas) je konfigurovatelná v Hubstaff UI per organizace, typicky 5–15 min.
- **Časová zóna** je důležitá pro lidský výstup — pokud generujete zprávu klientovi, zobrazte časy v `time_zone` směny, ne v UTC.
