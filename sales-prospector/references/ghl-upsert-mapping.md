# Mapování CSV → CliqSales (GoHighLevel)

Reference pro `ghl_contact_upsert.py`. Popisuje, jak helper přebírá řádky z `prospects.csv` a vytváří kontakty v CliqSales.

## Politika v1.0 — minimalistický payload do CRM

Cílem je **udržet CRM přehledné**. Do CliqSales jde jen to nejnutnější:

- Standardní GHL pole (jméno, příjmení, firma, e-mail, telefon, web)
- GHL native `source` = `"Sales Prospector"` (zobrazuje se v UI kontakt detailu)
- **Jediný tag** `sales prospector` (lowercase, s mezerou)
- **Žádná vlastní pole (custom fields)**
- **Žádný kampaňový tag, žádný zdrojový tag, žádná klíčová slova**

Cokoli „navíc" (úvodní věta, signál zájmu, zdroj, kampaň) zůstává v souborech `/documents/sales/prospects/[...]/`.

## CSV sloupce (výstup Sales Prospectoru)

| Sloupec | Typ | Povinné | Posílá se do CRM? | Popis |
|---|---|---|---|---|
| `Company` | text | ✅ | ✅ `companyName` | Název firmy |
| `Name` | text | ⚠️ | ✅ `firstName` + `lastName` (split na první mezeru) | Jméno klíčové osoby (pokud nalezeno) |
| `Email` | text | ⚠️ | ✅ `email` | Primární e-mail (alespoň Email NEBO Phone musí být) |
| `Phone` | text | ⚠️ | ✅ `phone` | Telefon v E.164 (`+420...`) |
| `Web` | text | ❌ | ✅ `website` | URL firemního webu |
| `Tags` | text | ❌ | ❌ **ignoruje se** | Drž prázdný. Helper od v1.0 sloupec nečte. |
| `Source` | text | ✅ | ❌ jen v souborech | Zdroj jako slug (`ares`, `firmy.cz`, ...) — pro lidský přehled |
| `Uvodni_veta` | text | ❌ | ❌ jen v souborech | 1–2 věty „proč právě oni" — pro `prospects-review.md` |
| `Source_URL` | text | ❌ | ❌ jen v souborech | Konkrétní URL záznamu ve zdroji |
| `Signal_zajmu` | text | ❌ | ❌ jen v souborech | Signál zájmu (např. „získali Series A 04/2026") |

⚠️ = aspoň jeden z `Email` nebo `Phone` musí být vyplněn, jinak řádek skript přeskočí (`missing email and phone`).

## Endpoint CliqSales (GoHighLevel)

```
POST https://services.leadconnectorhq.com/contacts/upsert
Headers:
  Authorization: Bearer <PIT>
  Version: 2021-07-28
  Content-Type: application/json
  Accept: application/json
  User-Agent: Mozilla/5.0 (compatible; CliqSales-SalesProspector/1.0; +https://cliqsales.cz)
```

**Pozor:** hlavička `User-Agent` je povinná — bez ní Cloudflare před GHL vrací **HTTP 403 Error 1010 — Access denied** (default `Python-urllib/X.Y` je na globálním blocklistu Cloudflare). Helper hodnotu drží v konstantě `USER_AGENT`.

## Mapování CSV → GHL JSON

```python
def map_row_to_ghl(row, location_id, default_tags):
    name = (row.get("Name") or "").strip()
    first_name, _, last_name = name.partition(" ")
    if not first_name:
        first_name = (row.get("Company") or "").strip()

    payload = {
        "locationId": location_id,
        "firstName": first_name or None,
        "lastName": last_name or None,
        "companyName": (row.get("Company") or "").strip() or None,
        "email": (row.get("Email") or "").strip() or None,
        "phone": (row.get("Phone") or "").strip() or None,
        "website": (row.get("Web") or "").strip() or None,
        "tags": list(default_tags),   # default: ["sales prospector"]
        "source": "Sales Prospector",  # GHL native field, zobrazí se v UI
    }
    return {k: v for k, v in payload.items() if v is not None}
```

## Tagy

**Default tag (vždy):** `sales prospector`

Uživatel může předat **jiný tag přes CLI** parametr `--tags`:

```bash
python3 ghl_contact_upsert.py --csv prospects.csv --tags "sales prospector,bioptron-q2"
```

Tagy se nesčítají s defaultem — pokud uživatel předá `--tags`, je to **kompletní seznam**. Pro zachování `sales prospector` ho musí explicitně uvést.

## Upsert chování (GHL native)

Endpoint `/contacts/upsert` najde shodu podle:

1. **Email** (primární identifikátor) — pokud existuje kontakt se stejným e-mailem, aktualizuje ho
2. **Phone** (sekundární) — pokud e-mail chybí ale phone se shoduje, aktualizuje
3. Pokud ani jedno → vytvoří nový kontakt

**Odpověď:**
```json
{
  "succeded": true,
  "new": true,
  "contact": {
    "id": "abc123...",
    "locationId": "2CW7dxw4pZcxJ1CMNTeW",
    "firstName": "...",
    "tags": ["sales prospector"]
  }
}
```

`new: true` → `created`. `new: false` → `updated`.

## Omezení rychlosti a ošetření chyb

- **GHL API limit:** 100 dotazů / 10 vteřin per location. Helper batchuje + pauzuje 1 vteřinu po každých 10 řádcích.
- **HTTP 403 + Cloudflare 1010:** helper detekuje a vrátí lidskou zprávu *„Cloudflare blokuje request — zkontroluj USER_AGENT v skriptu."* — agent nemá pokračovat improvizací.
- **HTTP 429:** exponenciální backoff (1 / 2 / 4 vteřiny), 3 pokusy, pak řádek selže a pokračuje další.
- **HTTP 401:** PIT je špatný nebo expirovaný → celý běh selže s lidskou zprávou (nový PIT v UI CliqSales).
- **HTTP 422 (validation):** typicky chybný formát phone / email → řádek selže, log do `errors[]`, pokračuje další.
- **Síťová chyba:** retry 3× s backoffem, pak řádek selže.

## Výstup zkušebního režimu (Krok 8 STOP 3)

Helper v `--dry-run`:

1. Načte CSV, ověří řádky (chybí současně e-mail i telefon → přeskoč)
2. Pro každý řádek volá `GET /contacts/search?email=...` (read-only)
3. Pro každý nalezený kontakt zjistí, zda má aktivní DND
4. Vrátí souhrn **BEZ jakéhokoli POST volání**:

```json
{
  "dry_run": true,
  "total_rows": 28,
  "valid": 26,
  "skipped": 2,
  "skip_reasons": {"missing email and phone": 2},
  "would_create": 19,
  "would_update": 7,
  "dnd_warning_count": 2,
  "dnd_warning_examples": ["Firma Alpha s.r.o.", "Beta Trading"],
  "tags_to_apply": ["sales prospector"],
  "estimated_time_seconds": 8
}
```

Po STOP 3 souhlasu uživatele se skript pustí znovu **bez** `--dry-run` — proběhne reálné `POST /contacts/upsert` pro každý platný řádek.
