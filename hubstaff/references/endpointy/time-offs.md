# Endpoint: `time-offs` (žádosti o volno)

Vrací **žádosti o volno** (dovolená, nemoc, osobní volno) za zvolené období. Hubstaff má vlastní engine pro PTO (paid time off) — členové podávají žádosti, manažeři schvalují, systém udržuje zůstatky.

Volá se přes `GET /v2/organizations/{org_id}/time_offs` s povinným časovým oknem.

CLI: `python3 hubstaff.py time-offs --from --to [--member] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID žádosti. |
| `user_id` | číslo | ID člena, kterému volno patří. |
| `policy_id` | číslo | ID politiky (typu volna) — viz „Politiky" níže. |
| `policy_name` | text | Lidský název politiky (`Dovolená`, `Nemoc`, `Sick leave`, `Personal day`...). |
| `start_date` | ISO 8601 (date) | První den volna. |
| `end_date` | ISO 8601 (date) | Poslední den volna (inclusive). |
| `hours` | číslo | Kolik hodin se z volna „odečte" (typicky 8 × počet pracovních dní). |
| `status` | text | `pending` (čeká na schválení), `approved`, `denied`, `cancelled`. |
| `reason` | text nebo `null` | Důvod, který člen uvedl. |
| `approved_by_user_id` | číslo nebo `null` | Kdo žádost schválil/zamítl. |
| `created_at` / `updated_at` | ISO 8601 | Časy vzniku a poslední změny. |

## Politiky (`policy_id`, `policy_name`)

Hubstaff podporuje **vlastní politiky volna** per organizace. Typické příklady:

- **Dovolená** / **Vacation** — placené pracovní volno
- **Nemoc** / **Sick leave** — nemocenská
- **Osobní volno** / **Personal day** — drobné rezervy
- **Neplacené volno** / **Unpaid leave**
- **Rodičovská** / **Maternity / Paternity**

Skill politiky samostatně neenumerace (Hubstaff API endpoint pro `time_off_policies` existuje, ale není v 1.0) — `policy_name` v každé žádosti stačí pro reporting.

## Typické použití

- **Kalendář absencí** — kdo má v daný týden volno (filtr `status: approved`).
- **Detekce „nízká aktivita = volno"** — pokud má člen v určitý den 0 aktivit a má v `time-offs` schválenou žádost překrývající ten den, **není to anomálie**, je to volno. Orchestrace má `time-offs` křížit s `activities` před vystavením upozornění.
- **Zůstatek volna** — Hubstaff má vlastní balances endpoint, ale jednoduchá aproximace je: politika má roční fond − sum `hours` v daném roce.
- **Schvalovací queue manažera** — filtr `status: pending`.

## Příklad výstupu (zkrácený JSON)

```json
[
  {
    "id": 4321,
    "user_id": 12345,
    "policy_id": 5,
    "policy_name": "Dovolená",
    "start_date": "2026-06-01",
    "end_date": "2026-06-05",
    "hours": 40,
    "status": "approved",
    "reason": "Letní dovolená s rodinou",
    "approved_by_user_id": 1,
    "created_at": "2026-05-10T10:00:00Z",
    "updated_at": "2026-05-11T09:30:00Z"
  }
]
```

## Pozor

- **Volné dny vs. hodiny:** Hubstaff počítá v hodinách. 5denní dovolená = `hours: 40` (předpokládá 8h/den). Pokud má organizace jinou pracovní dobu, čísla mohou nesedět.
- **Časové zóny:** `start_date` a `end_date` jsou jen datumy (bez času). Pro „pracovní den" platí zóna člena, ne UTC.
- **Status `cancelled`** vs. `denied` — `cancelled` zrušil sám člen, `denied` zamítl manažer. Pro reporting absencí filtrujte typicky `status: approved`.
- **Politika volna může být placená nebo neplacená.** Pole `policy_name` to neříká přímo — pro mzdy musíte mít zvlášť mapování per politika.
