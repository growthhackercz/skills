# FIO API — Endpointy (read-only)

**Base URL:** `https://fioapi.fio.cz/v1/rest/`

Token se vkládá **přímo do URL path** (ne do hlavičky). Helper `scripts/fio_get.py` ti ho dosadí z Control Center FIO profilu (`--profile`) nebo legacy `$FIO_API_TOKEN` fallbacku, pokud v pathu necháš placeholder `{token}` nebo path začneš lomítkem (helper si poradí oběma způsoby).

## Přehled endpointů

| Endpoint | Účel | Metoda |
|---|---|---|
| `/periods/{token}/{datum-od}/{datum-do}/transactions.{format}` | Pohyby za zvolené období | GET |
| `/last/{token}/transactions.{format}` | Pohyby od posledně nastavené zarážky | GET |
| `/by-id/{token}/{rok}/{cislo-vypisu}/transactions.{format}` | Konkrétní oficiální výpis (číslovaný) | GET |
| `/lastStatement/{token}/statement` | Číslo a rok posledního oficiálního výpisu | GET |
| `/set-last-date/{token}/{yyyy-mm-dd}/` | Posun zarážky pro `/last` na datum | GET |
| `/set-last-id/{token}/{id}/` | Posun zarážky pro `/last` na konkrétní ID pohybu | GET |

**Žádné write endpointy v tomto skillu** (import plateb existuje ve FIO API jako `/import/`, ale skill ho záměrně nepoužívá — read-only token to stejně odmítne s 403).

---

## 1. Pohyby za období — `/periods/`

**URL:**
```
/periods/{token}/{datum-od}/{datum-do}/transactions.{format}
```

**Parametry:**
- `{datum-od}`, `{datum-do}` — formát `YYYY-MM-DD`. Inkluzivní oba konce.
- `{format}` — `json` | `xml` | `csv` | `gpc` | `abo` | `ofx` | `sta` | `html` | `pdf`. Viz `output-formats.md`.

**Kdy použít:**
- Cashflow report za měsíc / čtvrtletí / rok.
- Ad-hoc dotaz „co se dělo mezi X a Y".
- Reanalýza historických dat.

**Limity:**
- FIO neomezuje, ale **počítej s rate limitem 1 req / 30 s**.
- Pro období > 1 rok je vhodné rozdělit na čtvrtletí (kvůli velikosti odpovědi a robustnosti).

**Příklad (Python přes helper):**
```python
import subprocess, json
subprocess.run(["python3", "scripts/fio_get.py",
    "--profile", "hlavni-czk",
    "/periods/{token}/2026-05-01/2026-05-19/transactions.json",
    "--output", "/documents/financials/20260501-20260519/raw.json"], check=True)
data = json.load(open("/documents/financials/20260501-20260519/raw.json"))
```

Přímý `curl` s tokenem v URL nepoužívej. Token by se mohl objevit v `ps`, shell historii nebo logu.

---

## 2. Pohyby od poslední zarážky — `/last/`

**URL:**
```
/last/{token}/transactions.{format}
```

**Jak to funguje:**
FIO si pro každý token pamatuje „zarážku" — buď ID posledního staženého pohybu, nebo datum. Volání `/last/` vrátí **všechny pohyby od této zarážky** a posune ji na aktuální poslední pohyb. Tj. opakované volání by druhým průchodem vrátilo prázdno (dokud nepřijdou nové pohyby).

**Kdy použít:**
- Watcher / inkrementální stahování (každý den / hodinu).
- Když nechceš opakovaně sahat na celé období.

**Pozor:**
- **Zarážka je stateful na FIO straně.** Pokud zavoláš `/last/` a něco se stane v tvém pipeline (crash, ztráta JSON), data jsou pryč ve smyslu, že je `/last/` už znovu nevrátí (ale `/periods/` ano).
- **Best practice:** uložit JSON do `/documents/...` PŘED tím, než s ním cokoli dál děláš.

**Reset zarážky:**
- `/set-last-date/{token}/{yyyy-mm-dd}/` → další `/last/` vrátí všechno od tohoto data.
- `/set-last-id/{token}/{id}/` → další `/last/` vrátí všechno po tomto ID (exkluzivně).

---

## 3. Konkrétní oficiální výpis — `/by-id/`

**URL:**
```
/by-id/{token}/{rok}/{cislo-vypisu}/transactions.{format}
```

**Parametry:**
- `{rok}` — čtyřciferný (např. `2026`).
- `{cislo-vypisu}` — pořadové číslo výpisu v roce (např. `5` pro pátý výpis).

**Kdy použít:**
- Export pro účetní (oficiální výpis má daňovou váhu).
- Když chceš PDF výpis identický s tím, co posílá FIO klientovi měsíčně.

**Jak najít poslední číslo výpisu:**
```
GET /lastStatement/{token}/statement
→ vrátí v plaintextu např. "2026,5" (rok, číslo)
```

---

## 4. Posun zarážky — `/set-last-date/` a `/set-last-id/`

**`/set-last-date/{token}/{yyyy-mm-dd}/`**
Nastaví zarážku tak, že další `/last/` vrátí všechny pohyby od (a včetně) tohoto data.

**`/set-last-id/{token}/{id}/`**
Nastaví zarážku tak, že další `/last/` vrátí pohyby s ID > daným ID (exkluzivně).

**Vrací:** prázdné tělo + HTTP 200 při úspěchu. Tj. žádný JSON parsing.

**Kdy použít:**
- Před prvním produkčním `/last/` runem — nastav datum, abys neměl 5 let pohybů v jedné odpovědi.
- Při testování — vrátit zarážku zpět a znovu stáhnout.
- Při výpadku pipeline — opětovně stáhnout od konkrétního ID.

---

## Volání více endpointů v jednom runu

**POZOR:** Rate limit `1 req / 30 s / token` platí napříč všemi endpointy. Tj. pokud uděláš `/set-last-date/` a hned `/last/`, druhý request dostane HTTP 409.

Helper `fio_get.py` má retry, ale počítej s tím, že 5 sekvenčních volání = ~2 minuty reálného času.

**Optimalizace:**
- `/periods/` často nahradí kombinaci `/set-last-date/` + `/last/` (jedno volání místo dvou).
- Pro většinu use casů ti stačí jediný `/periods/` request.
