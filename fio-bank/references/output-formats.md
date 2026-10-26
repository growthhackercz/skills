# FIO API — Output formáty

FIO API umí vrátit data v **9 formátech**. Volíš příponou v URL (`...transactions.json`, `...transactions.csv`, …).

## Přehledová tabulka

| Formát | Přípona | Kdy použít | Kompatibilita |
|---|---|---|---|
| **JSON** | `.json` | Programatické zpracování, agent ho parsuje | Univerzální |
| **XML** | `.xml` | Když konzumující systém vyžaduje XML | Pohoda, některé ERP |
| **CSV** | `.csv` | Excel, Google Sheets, ad-hoc analýza | Excel, Numbers |
| **GPC** | `.gpc` | České účetnictví — standardní formát | Pohoda, Money S3, Helios |
| **ABO** | `.abo` | Bankovní výpis pro účetnictví | Pohoda, Money S3 |
| **OFX** | `.ofx` | Mezinárodní standard | QuickBooks, GnuCash |
| **MT940** | `.sta` | SWIFT standard | SAP, mezinárodní účetní systémy |
| **HTML** | `.html` | Náhled v prohlížeči, mail attachment | Univerzální |
| **PDF** | `.pdf` | Tisk, archivace, příloha k daňovým dokladům | Univerzální |

## Doporučení podle use case

### Agent zpracovává data → JSON
Default volba. Helper `fio_get.py` automaticky parsuje JSON pokud má path příponu `.json`. Pak použij `parse_transactions.py` pro mapování na pojmenovaná pole.

```python
fio_get("/periods/{token}/2026-05-01/2026-05-19/transactions.json", output="raw.json")
```

### Export pro českou účetní (Pohoda / Money S3) → GPC
GPC je v ČR standardní formát pro import bankovních pohybů do účetních systémů.

```python
fio_get("/periods/{token}/2026-05-01/2026-05-19/transactions.gpc", output="vypis.gpc")
```

> ⚠️ GPC je **binární textový formát** s pevnou šířkou polí. Neparsuj ho agentem — jen ho vygeneruj a předej uživateli.

### Export pro mezinárodní účetnictví → MT940
SWIFT standard, podporuje SAP a další ERP.

```python
fio_get("/periods/{token}/2026-05-01/2026-05-19/transactions.sta", output="vypis.sta")
```

### Náhled pro klienta v prohlížeči → HTML
FIO vrátí pre-formátovaný HTML výpis s logem FIO. Vhodné jako příloha mailu.

### Archivace / daňový doklad → PDF
Použij **`/by-id/`** endpoint místo `/periods/`, abys dostal **oficiální výpis** s daňovou váhou:

```python
fio_get("/by-id/{token}/2026/5/transactions.pdf", output="vypis-2026-05.pdf")
```

### Excel analýza → CSV
Pro klienta, který si chce data sám prokutat v Excelu:

```python
fio_get("/periods/{token}/2026-05-01/2026-05-19/transactions.csv", output="pohyby.csv")
```

> ⚠️ FIO CSV používá **středník** jako oddělovač (české lokále) a kódování **Windows-1250**. Pokud chceš UTF-8, požádej uživatele, aby ho v Excelu uložil jako UTF-8 CSV, nebo to transcoduj v Pythonu.

## Doporučení pro skill

**Default formát: `.json`** — pro programatické zpracování.

**Vedlejší formát: `.gpc` nebo `.csv`** — pokud uživatel explicit zmíní účetní / Excel export.

**Nikdy nezpracovávej PDF/HTML/MT940/GPC programaticky** — jen je předej uživateli jako soubor v `/documents/financials/...`.

## Kombinace více formátů

Pokud chce uživatel **JSON pro analýzu + GPC pro účetní**, udělej **dvě volání** (s 30s pauzou kvůli rate limitu) na stejné období:

```python
fio_get("/periods/{token}/2026-05-01/2026-05-19/transactions.json", output="data.json")
time.sleep(30)  # rate limit
fio_get("/periods/{token}/2026-05-01/2026-05-19/transactions.gpc", output="vypis.gpc")
```

Helper `fio_get.py` rate-limit retry zvládá sám, ale počítej s tím, že druhé volání bude čekat ~30 s.
