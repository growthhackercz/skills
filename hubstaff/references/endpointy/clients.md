# Endpoint: `clients` (klienti organizace)

Vrací seznam klientů (CRM-like entit) v organizaci. Klient v Hubstaffu reprezentuje externí subjekt, pro kterého se dělá práce — používá se pro fakturaci a navázání projektů.

Volá se přes `GET /v2/organizations/{org_id}/clients`.

CLI: `python3 hubstaff.py clients [--org ID] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID klienta. |
| `name` | text | Název klienta (firma nebo osoba). |
| `status` | text | `active`, `archived`. |
| `emails` | seznam textů | Kontaktní emaily. |
| `phone` | text nebo `null` | Telefon. |
| `notes` | text nebo `null` | Volitelná poznámka. |
| `billing_email` | text nebo `null` | Email pro fakturaci. |
| `created_at` / `updated_at` | ISO 8601 | Časy vzniku a poslední změny. |

## Typické použití

- **Mapování projektů na klienty** — propojení `projects.client_id` s názvem klienta.
- **Klientský přehled** — agregace hodin / částek za projekty patřící konkrétnímu klientovi.
- **Audit aktivních klientů** — kolik klientů má `status: active` a kolik projektů na nich visí.

## Příklad výstupu (zkrácený JSON)

```json
[
  {
    "id": 88,
    "name": "Acme s.r.o.",
    "status": "active",
    "emails": ["objednavky@acme.cz"],
    "phone": "+420 222 333 444",
    "notes": null,
    "billing_email": "fakturace@acme.cz",
    "created_at": "2024-11-02T09:15:00Z",
    "updated_at": "2026-04-12T14:20:00Z"
  }
]
```

## Pozor

- Klient je čistě informační entita v Hubstaffu — pro fakturaci ven (vystavení faktury) Hubstaff používá vlastní billing engine, ale skill ho v 1.0 nečte.
- Pokud organizace klienty nepoužívá (jen interní projekty), endpoint vrátí prázdný seznam.
