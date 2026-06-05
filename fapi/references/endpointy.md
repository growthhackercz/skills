# Katalog endpointů

Pro každý zdroj: cesta, klíčová pole v JSON, jaké filtry jsou ověřené, co umí, co neumí.

> Tvary JSON dole jsou **doslovné výňatky z testovacích fixtur oficiálního PHP klienta** (`fapi-cz/fapi-client`). Žádné domněnky.

---

## `/invoices` — Faktury

Hlavní zdroj dat o tržbách.

### Tvar jedné faktury (zkráceno na klíčová pole)

```json
{
  "id": 185993812,
  "number": "202010004",
  "created_on": "2020-09-08 15:50:34",
  "last_modified_on": "2020-09-08 15:50:34",
  "create_date": "2020-09-08",
  "payday_date": "2020-09-22",
  "client": 1808089,
  "type": "proforma",
  "payment_type": "credit card",
  "currency": "CZK",
  "exchange_rate_czk": 1,
  "exchange_rate": 1,
  "language": "cs",
  "paid": false,
  "cancelled": false,
  "cancellation_reason": null,
  "reverse_charge": false,
  "tax_exempt": false,
  "has_credit_note": false,
  "variable_symbol": "202010004",
  "supplier": { "name": "...", "ic": "...", "email": "...", "address": {...} },
  "customer": { "name": "...", "email": "..." },
  "project": 31862,
  "items": [
    { "id": 10182751, "name": "Sample Item", "price": 10, "count": 1 }
  ],
  "custom_fields": [],
  "total": 10,
  "total_vat": 0,
  "total_czk": 10,
  "total_native": 10,
  "proforma": true,
  "payment_confirmation": false,
  "simplified_invoice": false,
  "credit_note": false
}
```

### Klíčová pole pro analytiku

| Pole | Typ | Význam |
|---|---|---|
| `id` | int | Unikátní identifikátor faktury |
| `number` | string | Variabilní symbol / číslo faktury, jak ho vidí klient |
| `created_on` | datetime `YYYY-MM-DD HH:MM:SS` | Kdy faktura vznikla |
| `create_date` | date `YYYY-MM-DD` | Den vystavení (užitečné pro denní/měsíční seskupení) |
| `payday_date` | date | Datum splatnosti |
| `client` | int | ID klienta (vazba na `/clients/{id}`) |
| `paid` | bool | **Jediný indikátor zaplacení.** Žádná hodnota mezi (částečná platba) — buď ano, nebo ne. |
| `cancelled` | bool | Faktura je stornovaná. Storno je v FAPI **jediná stopa po refundu**. |
| `currency` | string | `"CZK"`, `"EUR"`, … |
| `exchange_rate_czk` | number | Kurz pro převod na koruny |
| `total` | number | Celková částka v měně faktury (`currency`) |
| `total_czk` | number | Totéž přepočtené na CZK přes `exchange_rate_czk` |
| `total_vat` | number | DPH část |
| `total_native` | number | Celková částka v původní měně (často shodné s `total`) |
| `type` | string | Typ dokumentu — pozorované hodnoty: `"proforma"` (zálohová), dále existují daňový doklad, opravný atd. — přesné enum **není dokumentováno** |
| `items[]` | array | Položky faktury, embedded přímo v dokumentu — viz `items` níže |

### Jak skládat „stav" faktury

**Status jako samostatný enum field NEEXISTUJE.** Stav se odvozuje z kombinace bool flagů:

| Klient řekne | Filtruj na |
|---|---|
| „zaplacené" | `paid == true && cancelled == false` |
| „nezaplacené" | `paid == false && cancelled == false` |
| „po splatnosti" | `paid == false && cancelled == false && payday_date < dnes` |
| „stornované" (refundy) | `cancelled == true` |
| „zálohové" | `type == "proforma"` |

> Endpoint `/invoices/count?status=issued` přijímá řetězec `status` — ale **jediná empiricky ověřená hodnota je `issued`**. Další hodnoty (`paid`, `cancelled`) nejsou v zdrojích potvrzené. Pro skutečné filtrování spolehněte se na flagy v JSONu (nebo si je dotáhněte přes datumové okno a vyfiltrujte sami).

### Ověřené filtry

- **Datumové okno:** `?created_on_from=YYYY-MM-DD HH:MM:SS&created_on_to=YYYY-MM-DD HH:MM:SS` (URL-encoded — viz `filtrace-a-obdobi.md`).
- **Status:** `?status=issued` (jediná ověřená hodnota).
- **Uživatel:** `?user=<id>` (relevantní jen u multi-user účtů).
- **Limit:** `?limit=N` (kolik záznamů vrátit).

### Pomocné endpointy

| Cesta | Co vrací |
|---|---|
| `GET /invoices` | List |
| `GET /invoices/{id}` | Detail jedné faktury |
| `GET /invoices/count?...` | `{"count": N}` — kolik faktur splňuje filtr |
| `GET /invoices/{id}.pdf` | PDF binárka (mimo scope tohoto skillu) |

---

## `/orders` — Objednávky

Vznikají, když někdo vyplní prodejní formulář. Spárované s fakturou (`invoice` field), pokud byla vystavena.

### Tvar jedné objednávky

```json
{
  "id": 12440538,
  "form": 60693,
  "created": "2025-12-05 14:07:18",
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com",
  "phone": "+420123456789",
  "company": "...", "ic": "...", "dic": "...",
  "address": { "street": "...", "city": "...", "zip": "...", "country": "..." },
  "shipping_address": { ... },
  "payment_type": "wire",
  "bank": "wire",
  "currency": null,
  "pending": true,
  "client": 1808102,
  "invoice": 209820339,
  "items": [
    {
      "name": "Sample Item",
      "price": 2700,
      "price_czk": 2700,
      "price_eur": 100,
      "vat": 0,
      "count": 1,
      "prices": [
        { "price": 2700, "type": "one_time", "currency_code": "CZK" }
      ]
    }
  ],
  "discount_code": null,
  "gopay_payment": null,
  "stripe": null
}
```

### Klíčová pole

| Pole | Význam |
|---|---|
| `id` | ID objednávky |
| `form` | ID formuláře, ze kterého přišla |
| `created` | **Pozor: zde `created`, ne `created_on` jako u invoice** |
| `client` | ID klienta |
| `invoice` | ID faktury (pokud existuje) |
| `pending` | Čeká na zaplacení / dokončení |
| `items[]` | Co bylo objednáno — z toho jdou nejlépe spočítat „top produkty" |
| `items[].name` | Název produktu (klíč pro Pareto analýzu) |
| `items[].price` | Cena za kus v měně objednávky |
| `items[].count` | Kolik kusů |
| `items[].price_czk`, `price_eur` | Přepočty (dostupné někdy) |

### Ověřené filtry

- `?invoice=<id>` — vrátí objednávku spárovanou s danou fakturou
- `?sources[0]=form&sources[1]=api` — odkud objednávka přišla (PHP-style pole)
- `?limit=N`

> **Datumové okno** (`created_from` / `created_to` apod.) **nedokumentováno**. Pokud potřebuješ filtrovat objednávky po datumu, je bezpečnější to udělat přes spárovanou fakturu (`/invoices?created_on_from=...` → vzít `id` → dotázat `/orders?invoice=<id>`), nebo stáhnout vše a vyfiltrovat lokálně podle `created`.

### Co `/orders` nepodporuje

- **Delete** — objednávky se nemažou přes API.
- **Samostatný `/count`** endpoint není.

---

## `/clients` — Klienti

Adresář kontaktů. Spárované s fakturami a objednávkami přes `client` field (číselné ID).

### Tvar (testovací fixtura má jen minimum)

```json
{ "id": 1808080, "email": "test@example.cz", "tax_payer": false }
```

Reálné objekty mají typicky i `first_name`, `last_name`, `company`, `phone`, `address {…}`, `ic`, `dic`. Přesné enum polí v plné odpovědi není v dokumentaci, ale tyto klíče se objevují v embed `customer` na faktuře a `address` na objednávce.

### Ověřené filtry

- `?email=<přesný email>` — najde klienta po emailu
- `?limit=N`

### Užitečné scénáře

- Spočítat opakované zákazníky: stáhnout `/orders` přes okno → group-by `client` → komu vyšel `count > 1`.
- Top zákazníci: stáhnout `/orders` nebo placené `/invoices` → group-by `client` → seřadit podle součtu `total_czk`.

---

## `/vouchers` — Slevové kódy

### Tvar

```json
{
  "id": 1656,
  "user_id": 13057,
  "code": "ABUCRQ",
  "status": "valid",
  "created_on": "2021-03-11 17:36:23",
  "expiration_date": "2021-03-31",
  "applied_on": null,
  "invoice_id": null,
  "product_name": "test",
  "item_template_code": null,
  "applicant": null
}
```

### Status — jediný **opravdový enum**

| Hodnota | Význam |
|---|---|
| `valid` | Nepoužitý, lze uplatnit |
| `applied` | Už byl uplatněn — `applied_on` a `invoice_id` jsou vyplněné |

### Operace

| Cesta | Akce |
|---|---|
| `GET /vouchers/{code}` | Detail (jen po `code`, ne po `id`!) |
| `PUT /vouchers/{code}/apply` | Uplatnit voucher (pro tento skill mimo scope — read-only) |

### Pro analytiku

- Kolik voucherů uplatněných za období: stáhnout všechny, filtrovat `status == "applied"` a `applied_on` v okně.
- Kolik voucherů „shořelo": `status == "valid"` a `expiration_date < dnes`.

---

## `/statistics/total` — Předagregované statistiky

**Zlatý poklad pro reporting** — FAPI tu nabízí přímo časové řady tržeb, storn a po splatnosti, takže se nemusíš škrábat tisíci fakturami.

### Volání

```
GET /statistics/total?type=daily&start=2026-04-01&end=2026-04-30&including_vat=0
```

### Parametry

| Parametr | Hodnoty | Význam |
|---|---|---|
| `type` | `daily` (ověřeno), pravděpodobně i `weekly`/`monthly`/`yearly` — netestováno | Granularita časové řady |
| `start`, `end` | `YYYY-MM-DD` | Datumový rozsah (jen datum, bez času — jiná konvence než `/invoices`) |
| `including_vat` | `0` nebo `1` | Bez/s DPH |

### Tvar odpovědi

```json
{
  "issued":      [...],
  "cancelled":   [...],
  "paid":        [...],
  "left_to_pay": [...],
  "overdue":     [...],
  "invoiced":    [...],
  "dph":         [...]
}
```

7 časových řad:

| Klíč | Co znamená |
|---|---|
| `issued` | Vystavené faktury |
| `paid` | Zaplacené |
| `cancelled` | Stornované |
| `left_to_pay` | Zbývá zaplatit |
| `overdue` | Po splatnosti |
| `invoiced` | Celkem fakturováno |
| `dph` | DPH část |

> **Přesný tvar prvků v každé časové řadě** (tj. co je element pole — datum + částka? jen částka? objekt?) **není v testovacích fixturách viditelný** (fixtura má prázdná pole). První volání udělej s `type=daily&start=...&end=...&limit=1` a podívej se na strukturu — pak doplň tuto sekci přesněji.

### Kdy použít `/statistics/total` místo `/invoices`

| Klient chce | Použij |
|---|---|
| Celkové tržby za měsíc/kvartál/rok | `/statistics/total` (1 volání) |
| Vývoj tržeb po dnech/měsících | `/statistics/total` (1 volání) |
| Kolik zaplatil konkrétní klient | `/invoices?...` (zdroj má detail) |
| Top produkty | `/orders?...` (statistics nezná produkty) |
| Detail konkrétní faktury | `/invoices/{id}` |

---

## Další zdroje (mimo hlavní scope tohoto skillu)

| Cesta | Co umí |
|---|---|
| `/items` | Create/Update/Delete jednotlivých položek faktury (žádný list — položky se čtou v rámci faktury) |
| `/item-templates` | Šablony produktů — kdyby klient potřeboval „kolik produktů máme v katalogu" |
| `/discount-codes` | Slevové akce na úrovni kampaně (ne jednotlivé vouchery) |
| `/periodic-invoices` | Opakované fakturace (předplatné) |
| `/forms` | Prodejní formuláře — `/orders` se na ně odkazuje přes `form` field |
| `/api-tokens` | Správa API klíčů (mimo scope read-only analytika) |
| `/countries`, `/exchange-rates`, `/message-templates`, `/settings`, `/user` | Pomocné číselníky a konfigurace |

Pokud klient položí dotaz, který spadá sem (např. „kolik opakovaných předplatných mám"), použij `/periodic-invoices` analogicky k `/invoices`.

---

## Zdroje

- `fapi-cz/fapi-client` GitHub repo — autoritativní zdroj pro tvar dat a názvy polí (`EndPoints/*.php`, `tests/.../MockHttpClients/*`)
- Nápověda FAPI: https://napoveda.fapi.cz/article/84-ovladani-fapi-pres-api-rozhrani
