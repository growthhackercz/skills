# FIO API — Praktické recepty

5 hotových receptů pro nejčastější use casy. Každý recept obsahuje **zadání**, **endpointy k volání** a **příklad Python kódu** s helpery.

> Všechny outputy ukládej do `/documents/financials/{YYYYMMDD-YYYYMMDD}/`. Cestu předej uživateli v chatu.

---

## Recept 1 — Měsíční cashflow report

**Zadání:** Uživatel chce přehled příjmů, výdajů a salda za zvolený měsíc, plus top 10 příjmů a top 10 výdajů.

**Endpointy:**
- `GET /periods/{token}/{1.-mesice}/{posledni-den-mesice}/transactions.json`

**Postup:**

```python
import subprocess, json, os, datetime
from collections import defaultdict

YEAR, MONTH = 2026, 5
date_from = f"{YEAR}-{MONTH:02d}-01"
last_day = (datetime.date(YEAR, MONTH % 12 + 1, 1) - datetime.timedelta(days=1)).day
date_to = f"{YEAR}-{MONTH:02d}-{last_day:02d}"

out_dir = f"/documents/financials/{date_from.replace('-','')}-{date_to.replace('-','')}"
os.makedirs(out_dir, exist_ok=True)
raw_path = f"{out_dir}/raw.json"
parsed_path = f"{out_dir}/transactions.json"

# 1. Stáhni pohyby
subprocess.run(["python3", "scripts/fio_get.py",
    f"/periods/{{token}}/{date_from}/{date_to}/transactions.json",
    "--output", raw_path], check=True)

# 2. Parsuj column0..26 → pojmenovaná pole
subprocess.run(["python3", "scripts/parse_transactions.py",
    raw_path, "--output", parsed_path], check=True)

# 3. Agreguj
transactions = json.load(open(parsed_path))
income = sum(t["amount"] for t in transactions if t["amount"] > 0)
expenses = sum(-t["amount"] for t in transactions if t["amount"] < 0)
balance = income - expenses

top_income = sorted([t for t in transactions if t["amount"] > 0],
                    key=lambda t: -t["amount"])[:10]
top_expense = sorted([t for t in transactions if t["amount"] < 0],
                     key=lambda t: t["amount"])[:10]

# 4. Vyrob markdown report
report = f"""# Cashflow {YEAR}-{MONTH:02d}

- **Příjmy:** {income:,.2f} Kč
- **Výdaje:** {expenses:,.2f} Kč
- **Saldo:** {balance:,.2f} Kč

## Top 10 příjmů
| Datum | Částka | Protistrana | VS | Zpráva |
|---|---|---|---|---|
""" + "\n".join(f"| {t.get('date','')} | {t['amount']:,.2f} | {t.get('counter_account_name','')} | {t.get('vs','')} | {t.get('message','')[:50]} |" for t in top_income)

# (stejně pro top_expense)

open(f"{out_dir}/cashflow-report.md", "w").write(report)
print(f"Report: {out_dir}/cashflow-report.md")
```

---

## Recept 2 — Analýza nákladů po kategoriích

**Zadání:** Uživatel chce vědět, kolik utratil za mzdy, software, reklamu, daně atd. za zvolené období.

**Princip:** Sestav slovník `category → [pravidla]`, projeď transakce, přiřaď kategorii. Pravidla regex na `counter_account`, `vs`, `ks`, `message`, `counter_account_name`.

**Postup:**

```python
import re, json

CATEGORIES = {
    "Mzdy":          [{"ks": "0558"}, {"message": r"(?i)mzda|plat|odm[ěe]na"}],
    "Daně/odvody":   [{"counter_account": r"^7724"},  # ČNB účty FÚ
                      {"vs": r"^(\d{8,10})$", "ks": "1148"}],
    "Software/SaaS": [{"counter_account_name": r"(?i)google|microsoft|adobe|notion|figma|github|openai|anthropic|fal"}],
    "Reklama":       [{"counter_account_name": r"(?i)meta|facebook|google ads|seznam|tiktok"}],
    "Nájem":         [{"message": r"(?i)n[áa]jem|n[áa]jemn[ée]"}],
    "Bankovní poplatky": [{"counter_account_name": r"(?i)fio|poplatek"}, {"type": r"(?i)poplatek"}],
    "Příjmy/Faktury":[{"amount_min": 0}],  # všechny kladné jdou sem default
}

def categorize(t: dict) -> str:
    if t["amount"] > 0:
        return "Příjmy/Faktury"
    for cat, rules in CATEGORIES.items():
        if cat == "Příjmy/Faktury":
            continue
        for rule in rules:
            match = True
            for field, pattern in rule.items():
                value = str(t.get(field, ""))
                if not re.search(pattern, value):
                    match = False
                    break
            if match:
                return cat
    return "Ostatní výdaje"

transactions = json.load(open("/documents/financials/.../transactions.json"))
totals = {}
for t in transactions:
    cat = categorize(t)
    totals.setdefault(cat, {"sum": 0, "count": 0})
    totals[cat]["sum"] += t["amount"]
    totals[cat]["count"] += 1

# Vytiskni tabulku, ulož do reportu
for cat, data in sorted(totals.items(), key=lambda x: -abs(x[1]["sum"])):
    print(f"{cat:30s} {data['sum']:>12,.2f} Kč  ({data['count']}x)")
```

> 💡 Pravidla výše jsou **startovní set**. Pro každého klienta budou jiná — agent může s uživatelem v chatu vyladit, které protiúčty patří do které kategorie, a uložit do `/documents/financials/_config/categories.json` per-klient.

---

## Recept 3 — Export pohybů v GPC pro účetní

**Zadání:** Uživatel chce stáhnout pohyby za měsíc ve formátu GPC pro import do Pohody / Money S3.

**Endpointy:**
- `GET /periods/{token}/{datum-od}/{datum-do}/transactions.gpc`

**Postup:**

```python
import subprocess, os

out_dir = "/documents/financials/20260501-20260531"
os.makedirs(out_dir, exist_ok=True)

subprocess.run(["python3", "scripts/fio_get.py",
    "/periods/{token}/2026-05-01/2026-05-31/transactions.gpc",
    "--output", f"{out_dir}/vypis-2026-05.gpc"], check=True)

print(f"GPC výpis: {out_dir}/vypis-2026-05.gpc")
print("Tento soubor naimportuješ v Pohodě: Soubor → Datová komunikace → Banka → Import.")
```

> ⚠️ **NEPARSUJ GPC obsah agentem** — je to binární textový formát s pevnou šířkou polí. Jen ho předej uživateli.

---

## Recept 4 — Kontrola, zda přišla konkrétní platba

**Zadání:** Uživatel se ptá: „Přišla na účet platba s VS 20260519?" (typicky kontrola faktury od klienta).

**Endpointy:**
- `GET /periods/{token}/{posledni-2-tydny}/{dnes}/transactions.json`

**Postup:**

```python
import subprocess, json, datetime

today = datetime.date.today().isoformat()
two_weeks_ago = (datetime.date.today() - datetime.timedelta(days=14)).isoformat()

subprocess.run(["python3", "scripts/fio_get.py",
    f"/periods/{{token}}/{two_weeks_ago}/{today}/transactions.json",
    "--output", "/tmp/recent.json"], check=True)
subprocess.run(["python3", "scripts/parse_transactions.py",
    "/tmp/recent.json", "--output", "/tmp/recent-parsed.json"], check=True)

VS = "20260519"
matches = [t for t in json.load(open("/tmp/recent-parsed.json"))
           if t.get("vs") == VS and t["amount"] > 0]

if matches:
    for t in matches:
        print(f"✅ Nalezeno: {t['amount']:,.2f} Kč od {t.get('counter_account_name','?')} ({t.get('date','?')})")
else:
    print(f"❌ Platba s VS {VS} v posledních 14 dnech nepřišla.")
```

---

## Recept 5 — Stáhni pohyby od poslední zarážky (watcher pattern)

**Zadání:** Inkrementální stahování — chci jen nové pohyby od minule.

**Pozor:** `/last/` posune zarážku **na straně FIO**. Pokud po stažení něco selže, data jsou pryč ve smyslu, že `/last/` je už znovu nevrátí (ale `/periods/` ano).

**Best practice:** Před prvním produkčním runem nastav zarážku přes `/set-last-date/`, abys nedostal 5 let historie najednou.

**Postup:**

```python
import subprocess

# Jednorázově: nastav zarážku na začátek tohoto roku
# subprocess.run(["python3", "scripts/fio_get.py",
#     "/set-last-date/{token}/2026-01-01/"], check=True)

# Pak inkrementálně:
subprocess.run(["python3", "scripts/fio_get.py",
    "/last/{token}/transactions.json",
    "--output", "/documents/financials/_watcher/latest.json"], check=True)

print("Stáhl jsem nové pohyby od posledně. Zarážka se posunula.")
```

> 💡 Pro persistent watcher (cron každou hodinu) zvaž samostatný skill / setup. Tenhle MVP skill jen poskytuje endpoint.
