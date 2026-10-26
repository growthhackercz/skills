# Endpoint: `members` (členové organizace)

Vrací seznam zaměstnanců / spolupracovníků v organizaci. Volá se přes `GET /v2/organizations/{org_id}/members`.

CLI: `python3 hubstaff.py members [--org ID] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | Vnitřní ID člena v Hubstaffu. Toto ID používejte ve filtrech `--member` na ostatních endpointech. |
| `name` | text | Celé jméno, jak ho člen má nastavené ve svém profilu. |
| `email` | text | Email člena. |
| `user_id` | číslo | Globální ID uživatele Hubstaffu (jeden uživatel může být členem víc organizací — `id` se liší per organizace, `user_id` je stejný). |
| `role` | text | Role v organizaci: `owner` (majitel), `manager` (manažer), `user` (běžný člen). |
| `status` | text | `active`, `inactive`, `removed`. Filtrujte na `active`, pokud chcete pracující členy. |
| `pay_rate` | objekt | Hodinová sazba pro výpočet odměn (`amount`, `currency`). Viditelné jen pro role s oprávněním vidět finance. |
| `bill_rate` | objekt | Fakturační sazba klientovi (`amount`, `currency`). |
| `created_at` | ISO 8601 | Datum, kdy byl člen do organizace přidán. |
| `last_activity` | ISO 8601 nebo `null` | Čas posledního zaznamenaného sledování. `null` znamená, že člen ještě nikdy nesledoval. |

## Typické použití

- **Mapování ID na jména** — když dostanete `user_id` z `activities`, propojte si je se jmény z `members`.
- **Detekce neaktivních členů** — filtruje se na `status: active` a porovnává `last_activity` s aktuálním datem (např. „nesledoval déle než 7 dní" = neaktivní).
- **Audit oprávnění** — kdo má roli `manager` / `owner` (=má přístup k datům celé organizace).

## Příklad výstupu (zkrácený JSON)

```json
[
  {
    "id": 12345,
    "name": "Jan Novák",
    "email": "jan.novak@firma.cz",
    "user_id": 9876543,
    "role": "user",
    "status": "active",
    "pay_rate": {"amount": "350.00", "currency": "CZK"},
    "bill_rate": {"amount": "800.00", "currency": "CZK"},
    "created_at": "2024-08-15T10:23:00Z",
    "last_activity": "2026-05-19T13:42:00Z"
  }
]
```

## Pozor

- `pay_rate` a `bill_rate` se nevrátí, pokud token nemá oprávnění vidět finanční data.
- `status: removed` člen už není v organizaci, ale jeho historická data v `activities` a `time_entries` zůstanou — pro plný audit ho stále potřebujete znát.
