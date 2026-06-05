# Filtrace a období

## Datumové filtry — důležité

**FAPI nemá jeden uniformní filtr napříč zdroji.** Každý endpoint má vlastní pojmenování. Tady jsou ověřené tvary:

### `/invoices` — `created_on_from` + `created_on_to`

Formát hodnoty: **`YYYY-MM-DD HH:MM:SS`** (ne ISO 8601 s `T`).

Příklad (URL-encoded):
```
GET /invoices?created_on_from=2026-04-01%2000%3A00%3A00&created_on_to=2026-04-30%2023%3A59%3A59&limit=200
```

V `call_fapi.py` se URL-encoding postará curl, tobě stačí předat čistý query string:
```
python3 {baseDir}/scripts/call_fapi.py /invoices "created_on_from=2026-04-01 00:00:00&created_on_to=2026-04-30 23:59:59&limit=200"
```

> Mezera v hodnotě (`2026-04-01 00:00:00`) se curlem encodne na `+` nebo `%20` automaticky. Funguje obojí.

### `/statistics/total` — `start` + `end`

**Jiný formát!** Tady stačí datum (bez času), klíče jsou `start` a `end`:

```
GET /statistics/total?type=daily&start=2026-04-01&end=2026-04-30&including_vat=0
```

### `/orders` — bez ověřeného datumového filtru

V kódu PHP klienta ani v testovacích fixturách není potvrzený datumový filtr pro objednávky.

**Bezpečné cesty, jak filtrovat objednávky podle data:**

1. **Přes faktury (preferováno):**
   - Stáhni `/invoices?created_on_from=...&created_on_to=...`
   - Pro každou fakturu, kterou potřebuješ rozbalit na položky, zavolej `/orders?invoice=<id>`
2. **Stáhnout vše a filtrovat lokálně:**
   - `GET /orders?limit=<dost vysoké>` → projít a vyfiltrovat podle `created`
   - Funguje jen, pokud máš dohromady stovky až nízké tisíce objednávek
3. **Empiricky vyzkoušet** `?created_from=...` nebo `?created_on_from=...` — pokud FAPI parametr nezná, vrátí buď úplný list (ignoruje filtr), nebo HTTP 400. Před nasazením otestuj.

### `/clients` — filtruj přes email

Datumové filtry pro klienty nejsou v dokumentaci. Klienta najdeš spolehlivě jen přes email (`?email=...`) nebo přes vazbu (`client` field na invoice/order).

### `/vouchers` — datumové filtry nedokumentované

Pro období „kolik voucherů uplatněných v dubnu" stáhni vše a filtruj lokálně podle `applied_on`.

---

## Časová pásma

- **FAPI vrací datumy bez timezone informace.** Hodnoty jako `"created_on": "2020-09-08 15:50:34"` neobsahují suffix `Z` ani offset.
- Z provozního chování systému (české fakturační SW) lze předpokládat **Europe/Prague** (CET v zimě, CEST v létě), ale **oficiálně to dokumentace neuvádí**.
- **Praktický dopad:** filtruješ-li `created_on_from=2026-04-01 00:00:00`, dostaneš faktury vystavené od půlnoci pražského času — to je pro běžné měsíční reporty správně, žádný převod není potřeba.
- Pokud klient pracuje napříč zónami a tvrdí, že chybí faktura na okraji období, posuň okno o den a porovnej čísla.

---

## Skládání období (časté potřeby)

Předpoklady: dnešní datum si zjisti přes `date -u +%Y-%m-%d` nebo z kontextu chatu.

| Klient řekne | Tvar `created_on_from` / `created_on_to` (pro `/invoices`) |
|---|---|
| „v dubnu" (letošní) | `2026-04-01 00:00:00` / `2026-04-30 23:59:59` |
| „v dubnu loni" | `2025-04-01 00:00:00` / `2025-04-30 23:59:59` |
| „posledních 30 dní" | `<dnes - 30d> 00:00:00` / `<dnes> 23:59:59` |
| „letos" | `2026-01-01 00:00:00` / `<dnes> 23:59:59` |
| „loni celý rok" | `2025-01-01 00:00:00` / `2025-12-31 23:59:59` |
| „toto čtvrtletí" | první den čtvrtletí 00:00:00 / dnes 23:59:59 |
| „minulý měsíc" | první/poslední den předchozího měsíce |

Pro `/statistics/total` použij stejné datumy, ale **bez času** — jen `YYYY-MM-DD`.

> Pozor na poslední den měsíce — únor má 28/29, květen 31. Pokud místo „31" napíšeš datum, které v měsíci neexistuje, FAPI vrátí 400. Bezpečné je vzít první den následujícího měsíce a odečíst minutu, nebo prostě sáhnout po `23:59:59` posledního skutečného dne.

---

## Paginace

**Mechanismus:** parametr `?limit=N`. **Žádný `offset`, žádný `page`, žádný cursor v dokumentaci ani v PHP klientovi.**

| Otázka | Odpověď |
|---|---|
| Defaultní `limit`? | Nedokumentováno |
| Maximální `limit`? | Nedokumentováno — empiricky se zdá, že vysoké hodnoty (např. 200) projdou |
| Jak zjistit celkový počet? | Pro `/invoices` volej `GET /invoices/count?<stejné filtry>` → `{"count": N}`. Pro ostatní zdroje není dedikovaný count endpoint. |
| Co když `limit` chybí? | Nedokumentováno — radši `limit` vždy uveď |

### Strategie pro velké datasety

PHP klient nepoužívá `offset` ani stránkování. Doporučená pravidla:

1. **Vždy zúžit dotaz datumovým oknem.** Pokud klient řekne „roční report", neptej se najednou na celý rok — rozděl po měsících, 12 volání.
2. **Pro `/invoices`:**
   - Nejdřív `GET /invoices/count?created_on_from=...&created_on_to=...` → zjisti, kolik jich je.
   - Pokud `count <= 200`: jeden hit `GET /invoices?...&limit=300` stačí.
   - Pokud `count > 200`: rozsekej okno na menší (po týdnech / dnech), volej postupně, slep dohromady.
3. **Pro `/orders`:** count endpoint není. Začni `limit=200` a sleduj, jestli ti přišlo méně, než jsi čekal. Pokud cítíš, že chybí data, sekej okno (přes spárované faktury, viz výše).
4. **Před velkým fetchem (řekněme nad 500 záznamů odhadem) se klienta zeptej.** Krátké *„Vytáhnu cca X faktur, OK?"*.

### Pravidlo „zúžit, pak fetchnout"

Pokud klient řekne *„kolik jsem vydělal v dubnu na produktu X"*, **nestahuj rok**. Stačí:

```
GET /invoices/count?created_on_from=2026-04-01 00:00:00&created_on_to=2026-04-30 23:59:59
```

→ zjistíš, kolik volání budeš potřebovat. Pak fetch faktur a pro každou s embedovaným item shodným s X sečti `total_czk`.

> Pro tržby čistá čísla typicky stačí jeden hit na `/statistics/total` — viz kuchařka, recept č. 1.

---

## Řazení

V PHP klientu ani fixturách není ověřený `?sort=` nebo `?order=` parametr. Pokud potřebuješ seřazený výstup (např. top N po tržbě), seřaď si data lokálně v hlavě po stažení.

---

## Co nedělat

- ❌ **Nepokoušej se uniformní `created[gte]` syntax** napříč zdroji — `/invoices` chce `created_on_from`, `/statistics/total` chce `start`. Není to REST konvence à la JSON:API.
- ❌ **Nepředpokládej, že chybějící parametr filtr ignoruje** — některé endpointy ho ignorují, jiné vrátí 400. Vždy ověř první volání.
- ❌ **Nestahuj „pro jistotu" celý rok**, když klient chtěl měsíc. FAPI nemá rate limity dokumentované, ale pokud spustíš desítky tisíc dotazů, můžeš narazit.
