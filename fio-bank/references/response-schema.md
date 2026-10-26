# FIO API — JSON response schéma

## Top-level struktura

```json
{
  "accountStatement": {
    "info": { ... },
    "transactionList": {
      "transaction": [ ... ]
    }
  }
}
```

## `info` — hlavička výpisu

| Pole | Typ | Význam |
|---|---|---|
| `accountId` | string | Číslo účtu (bez kódu banky) |
| `bankId` | string | Kód banky (`2010` pro FIO) |
| `currency` | string | ISO měna účtu (např. `CZK`) |
| `iban` | string | IBAN účtu |
| `bic` | string | BIC/SWIFT |
| `openingBalance` | number | Zůstatek na začátku období |
| `closingBalance` | number | Zůstatek na konci období |
| `dateStart` | string | Datum začátku období (`YYYY-MM-DDZ`) |
| `dateEnd` | string | Datum konce období |
| `idFrom` | number | ID prvního pohybu v odpovědi |
| `idTo` | number | ID posledního pohybu v odpovědi |
| `idLastDownload` | number / null | ID posledně staženého pohybu (pokud byla nastavená zarážka) |
| `yearList` | number / null | Rok výpisu (jen pro `/by-id/`) |
| `idList` | number / null | Číslo výpisu (jen pro `/by-id/`) |

## `transaction[]` — pole transakcí

Každá transakce je objekt s číslovanými klíči `column0` až `column26`. Každý sloupec má strukturu:

```json
"column1": {
  "value": 1500.00,
  "name": "Objem",
  "id": 1
}
```

Pole `value` obsahuje vlastní hodnotu, `name` český popisek, `id` číselný identifikátor sloupce. **Některé sloupce v dané transakci nemusí existovat** (např. když platba nemá VS, `column7` chybí).

## Mapping `column0..column26` → field names

Tohle je **závazné mapování** z FIO dokumentace. Helper `scripts/parse_transactions.py` ho používá pro převod na čitelná pole.

| Sloupec | Field name | Český popisek (`name` z FIO) | Typ | Příklad |
|---|---|---|---|---|
| `column0` | `id` | ID pohybu | number | `26962199316` |
| `column1` | `amount` | Objem | number | `1500.00` |
| `column2` | `counter_account` | Protiúčet | string | `1234567890` |
| `column3` | `counter_account_name` | Název protiúčtu | string | `Jan Novák` |
| `column4` | `counter_bank_code` | Kód banky | string | `0100` |
| `column5` | `ks` | KS (konstantní symbol) | string | `0558` |
| `column6` | `counter_bank_name` | Název banky | string | `Komerční banka, a.s.` |
| `column7` | `vs` | VS (variabilní symbol) | string | `20260519` |
| `column8` | `ss` | SS (specifický symbol) | string | `0` |
| `column9` | `user_identification` | Uživatelská identifikace | string | `Jan Novák` |
| `column10` | `type` | Typ pohybu | string | `Bezhotovostní příjem` |
| `column12` | `executor` | Provedl | string | `Jan Novák` |
| `column14` | `currency` | Měna | string | `CZK` |
| `column16` | `message` | Zpráva pro příjemce | string | `Faktura 2026/05/123` |
| `column17` | `comment` | Komentář | string | volný text |
| `column18` | `payment_order_id` | ID příkazu | string | `123456` |
| `column22` | `payment_order_id_full` | ID pokynu (interní) | string | `12345678` |
| `column25` | `comment_alt` | Upřesnění (varianta) | string | volný text |
| `column26` | `bic` | BIC protiúčtu | string | `KOMBCZPP` |

**Sloupce `column11`, `column13`, `column15`, `column19`, `column20`, `column21`, `column23`, `column24` nejsou FIO API dokumentací standardně používány** — pokud se objeví, helper je ignoruje (nebo je ukládá do `extra`).

## Praktické tipy

### Datum transakce

⚠️ **Pozor:** Datum vlastního pohybu **není** přímo ve `column0..26`. FIO ho dává odděleně v poli `column0.value` (ID je číslo, ale **datum musíš odvodit z ID, nebo použít atribut `name` přes parsing**).

**Robustní řešení:** Datum je v poli na úrovni transakce mimo „columnXX" jako `column0.value` číselné ID — ale skutečné datum účtování je v `column0` přes `name` jako odkaz, nebo lépe ho parsuj z **vlastního `name` atributu transakce** (FIO ho posílá v sub-poli).

> 🚨 **Doporučení:** Při prvním reálném testu (s Pavlovým testovacím tokenem) **dump celého JSON** a ověř přesné umístění data. Mapování výše je z dokumentace, ale FIO občas posílá datum mimo column strukturu. Aktualizuj tenhle dokument po prvním reálném runu.

### Záporná částka = výdaj

`column1.value` je **podepsaná**:
- `> 0` → příjem (kredit)
- `< 0` → výdaj (debet)

Pro agregaci:
```python
income = sum(t["amount"] for t in transactions if t["amount"] > 0)
expenses = sum(-t["amount"] for t in transactions if t["amount"] < 0)
balance = income - expenses
```

### Chybějící sloupce

Při zpracování transakcí **neuvažuj přítomnost všech sloupců**. Mnoho transakcí (zejména poplatky, úroky) nemá `counter_account`, `vs`, `ss` atd.

```python
# ❌ KeyError
vs = transaction["column7"]["value"]

# ✅ Bezpečně
vs = transaction.get("column7", {}).get("value", "")
```

Helper `parse_transactions.py` to řeší automaticky (chybějící sloupec → prázdný string nebo None).

## Příklad parsované transakce

Po průchodu `scripts/parse_transactions.py`:

```json
{
  "id": "26962199316",
  "amount": 1500.00,
  "currency": "CZK",
  "counter_account": "1234567890",
  "counter_account_name": "Jan Novák",
  "counter_bank_code": "0100",
  "counter_bank_name": "Komerční banka, a.s.",
  "vs": "20260519",
  "ss": "0",
  "ks": "0558",
  "message": "Faktura 2026/05/123",
  "comment": "",
  "type": "Bezhotovostní příjem",
  "executor": "Jan Novák",
  "bic": "KOMBCZPP"
}
```
