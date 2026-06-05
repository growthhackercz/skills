---
name: fio-bank
description: Dá agentovi referenční mapu nad FIO API a kuchařku nejčastějších dotazů klienta o pohybech, zůstatcích, výpisech a cashflow. Agent volá API ad-hoc podle otázky. Read-only — nikdy do FIO nezapisuje.
category: operations
status: ready
version: "1.0"
publishedAt: "2026-05-20"
metadata: {"openclaw":{"requires":{"bins":["python3"]},"primaryEnv":"FIO_API_TOKEN","emoji":"🏦"}}
---

# FIO Bank (read-only API wrapper)

## Kdy tento skill načíst

- Uživatel zmíní **FIO banku** nebo požaduje práci s firemními bankovními daty z FIO.
- Stahování pohybů na účtu, výpisů, kontroly zůstatku.
- Cashflow report za období (den / týden / měsíc / čtvrtletí / rok).
- Analýza nákladů po kategoriích z bankovních pohybů.
- Kontrola, zda konkrétní platba (VS / částka) přišla na účet.
- Export transakcí pro účetní (CSV / GPC / ABO / MT940 / OFX).

## Co tento skill dělá

Tento skill **NENÍ** předdefinovaný pipeline s pevnými kroky. Je to **znalostní balíček** o FIO API + minimální fetch helper.

**Ty (agent) sám rozhoduješ**, jaké endpointy zavolat a co s daty dál uděláš, podle toho, co uživatel chce. Skill ti dává všechno know-how, abys to zvládl bez halucinací URL / parametrů / response formátů.

## Kde co najdeš

| Téma | Reference |
|---|---|
| Všechny REST endpointy + URL templates | `references/endpoints.md` |
| Token: generování, platnost, rotace, bezpečnost | `references/authentication.md` |
| Rate limit (1 req / 30 s / token) + retry | `references/rate-limits.md` |
| JSON schéma odpovědi + mapping `column0..column26` | `references/response-schema.md` |
| Output formáty (kdy JSON vs CSV vs GPC vs ABO vs MT940) | `references/output-formats.md` |
| Chybové kódy 401 / 403 / 404 / 409 / 500 | `references/error-handling.md` |
| Hotové recepty (cashflow, kategorizace, export pro účetní) | `references/examples.md` |

## Helper scripty

**`scripts/fio_get.py`** — rate-limit-safe HTTP GET na FIO API. Token bere z Control Center integrace FIO podle profilu (`--profile`) nebo z legacy `$FIO_API_TOKEN` fallbacku a vkládá do URL path. Automaticky retry na HTTP 409 s exp. backoffem (30 s → 60 s → 120 s).

```bash
python3 scripts/fio_get.py --profile hlavni-czk "/periods/{token}/2026-05-01/2026-05-19/transactions.json" --output transactions.json
```

**`scripts/parse_transactions.py`** — převede raw FIO JSON (`column0..column26`) na čitelná pojmenovaná pole (`id`, `date`, `amount`, `counter_account`, `vs`, `ss`, `ks`, `message`, …).

```bash
python3 scripts/parse_transactions.py transactions.json --output transactions-parsed.json
```

## Bezpečnost (kritické)

- **Token je v Control Center integraci FIO** (profil účtu). NIKDY ho neukazuj v chatu, logu, output souboru ani v error hlášce.
- **Token MUSÍ být read-only.** Klient ho takhle generuje v IB FIO. Skill nikdy nevolá write endpointy (import platebních příkazů, atd.).
- Pokud není nastaven žádný FIO profil ani legacy `$FIO_API_TOKEN`, **nepokračuj** — řekni uživateli, ať si token vygeneruje (návod v `references/authentication.md`) a přidá ho v Control Center > Integrace > FIO Bank.
- Pokud klient má víc FIO účtů, vždy použij explicitní `--profile <slug>` nebo si profil nejdřív vyjasni. Více účtů může mít stejnou měnu, takže samotná měna není bezpečný identifikátor.
- **Outputs** ukládej do `/documents/financials/{YYYYMMDD-YYYYMMDD}/` (sdílený volume mezi CC a openclaw — klient i CC backend je tam vidí).

## Typický flow pro agenta

1. Zjisti od uživatele, co konkrétně chce (cashflow / kategorizace / kontrola platby / export).
2. Najdi v `references/examples.md` nejbližší recept — nebo si poskládej vlastní z endpointů + schema.
3. Zavolej `scripts/fio_get.py` s odpovídajícím endpoint pathem.
4. Zpracuj data přes `scripts/parse_transactions.py` (pokud chceš strukturovaný output).
5. Vyrob výstup (markdown report / CSV / souhrn v chatu / …) do `/documents/financials/...`.
6. Předej uživateli absolutní cestu k výstupnímu souboru.
