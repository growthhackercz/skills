# Omezení a pasti

Co se ti nepovede vyřešit „čistě" a co o tom říct klientovi.

---

## 1. Storno je jediná stopa po refundu

**FAPI nemá samostatný objekt „refund".** Pokud klient vrátí peníze zákazníkovi, ve FAPI se to zobrazí jako **stornovaná faktura** (`cancelled: true`, `cancellation_reason` vyplněné, případně `has_credit_note: true` pokud byl vystaven opravný doklad).

### Dopad na výpočty

- **Čistá tržba za období** = součet `total_czk` faktur s `paid == true && cancelled == false` mínus součet `total_czk` faktur s `cancelled == true` v daném okně.
- Pokud klient pracuje s vystavenými fakturami a později je stornuje, datum storna nikde v JSON přímo nesvítí — pouze `last_modified_on` se posune. Pro přesný „refund report" se na FAPI nedá spolehnout.

### Co říct klientovi

> *„FAPI eviduje refundy jako stornované faktury — počítám čistou tržbu jako placené minus stornované za období. Pokud potřebuješ přesný den, kdy peníze odešly zpátky, FAPI to v API neukazuje."*

---

## 2. Žádná částečná platba na úrovni JSON

Faktura má jen `paid: true / false`. **Pole typu `paid_amount` nebo `amount_due` neexistuje.**

### Dopad

- Pokud klient přijal 50 % a 50 % ještě dluží, ve FAPI to v JSONu vypadá jako nezaplacené (`paid: false`).
- „Kolik fakticky přišlo na účet" v API není.
- Reportování „cashflow" je nepřesné — buď faktura platí celá, nebo neplatí.

### Co říct klientovi

> *„FAPI nezachycuje částečné platby v API — faktura je buď celá zaplacená, nebo ne. Pokud klient zaplatil polovinu, vidím ji jako nezaplacenou."*

---

## 3. Mix měn

`currency` na faktuře může být CZK, EUR, USD nebo jiná. **Nikdy neřezat součty napříč měnami bez konverze.**

### Bezpečná pravidla

- Pokud chceš v reportu jedno číslo: použij `total_czk` (FAPI sám přepočte přes `exchange_rate_czk`). Funguje pro klienty, kteří chtějí výsledek v korunách.
- Pokud klient pracuje primárně v EUR: filtruj `currency == "EUR"` a sečti `total_native`.
- **Nikdy nesměšuj `total` (v původní měně) bez kontroly `currency` field.** Sečteš jablka s hruškami.

### Co říct klientovi

> *„Máš faktury v {CZK, EUR, …}. Zobrazuju součet přepočtený na koruny přes kurzy FAPI. Pokud chceš výsledek v původních měnách rozdělený, řekni si."*

---

## 4. Status faktury není enum — skládá se z bool flagů

Klient řekne *„zaplacené"*, *„po splatnosti"*, *„zálohové"* — ale ve FAPI to není jedno pole, jsou to **kombinace** `paid`, `cancelled`, `payday_date`, `type`.

| Klient chce | Filtruj |
|---|---|
| Zaplacené | `paid == true && cancelled == false` |
| Nezaplacené | `paid == false && cancelled == false` |
| Po splatnosti | `paid == false && cancelled == false && payday_date < dnes` |
| Stornované | `cancelled == true` |
| Zálohové | `type == "proforma"` |

Endpoint `/invoices?status=issued` přijímá jen řetězec `issued` (jediná ověřená hodnota). Jiné stavy filtruj **lokálně** po stažení.

---

## 5. Časová pásma nejsou v JSON

Datumy jako `"created_on": "2020-09-08 15:50:34"` jsou bez timezone informace. **Předpoklad: Europe/Prague.**

- Pro běžné měsíční reporty (`created_on_from=2026-04-01 00:00:00`) se chová jako „pražský čas" a pro klienta to sedí.
- Off-by-one se může objevit jen u faktur vystavených pozdě večer/v noci, nebo když klient porovná s vlastním zdrojem v UTC.

### Co říct klientovi (jen když narazí na nesoulad)

> *„FAPI datum nemá timezone, předpokládám pražský čas. Pokud porovnáváš s něčím v UTC, může to vyjít o den jinak."*

---

## 6. `/orders` nemá ověřený datumový filtr

Pokud klient chce „objednávky v dubnu":

- **Preferuj cestu přes faktury** — stáhni `/invoices` v okně, vezmi `id`, pak `/orders?invoice=<id>` per fakturu.
- Alternativně: stáhni `/orders?limit=<vysoké>` a filtruj lokálně podle pole `created`. Funguje, dokud máš max nízké tisíce objednávek.

Pojmy v doc se objevují (`created_from`?) — pokud je potřebuješ, **otestuj jeden hit** a podívej se, jestli FAPI filtr respektuje, nebo ho ignoruje.

---

## 7. Paginace bez offsetu

PHP klient nepoužívá stránkování — jen `limit`. **Pro velké datasety nasekej čas na menší okna** (viz `filtrace-a-obdobi.md`). Bezpečný strop pro jeden hit: `limit=200`. Vyšší fungují, ale nejsou potvrzené.

Pro `/invoices` máš `/invoices/count` — volej ho **před** velkým fetchem, ať víš, do čeho jdeš.

---

## 8. Co FAPI vůbec neumí — neztrácej čas

| Klient se zeptá | Realita ve FAPI |
|---|---|
| „Otaguj klienty, kteří koupili produkt X" | Tagy/segmenty nejsou. Musí být řešeno v jiném systému (SmartEmailing, ECOMAIL, GoHighLevel). |
| „Pošli follow-up sekvenci po nákupu" | Drip kampaně přes API nejdou — jen v UI FAPI nebo přes Make.com/SmartEmailing. |
| „Jaké je moje MRR?" | FAPI nemá subscription analytics. Lze hrubě odhadnout přes `/periodic-invoices`, ale není to pravé MRR. |
| „Jaký mám churn?" | Nemá analytický endpoint. Lze pokusně odvodit z `/periodic-invoices` zaniklých opakovaných. |
| „Cohort retention" | Nejde. |
| „Webhook na nový kontakt" | Webhooky existují jen v UI FAPI, ne přes API. Lze nastavit ručně v `Nastavení → Propojení aplikací`. |

**Pravidlo: pokud klient chce něco z tohoto seznamu, řekni rovnou, že FAPI o tom data nedrží.** Nelámej se v JSONu, není tam co najít.

---

## 9. Rate limity nejsou dokumentované

V kódu PHP klienta ani v napovědě se nic neuvádí. Pravděpodobně nějaké interní limity existují, ale nejsou veřejné.

**Pravidlo:** udržuj požadavky pod ~10/s, sleduj HTTP 429 (nikdy jsem nepotkal, ale teoreticky možný). Pokud přijde, počkej 5–10 s a zkus znovu.

---

## 10. Empty result je validní, ne chyba

Pokud filtr nic nenajde, FAPI vrátí 200 s prázdným polem:
```json
{ "invoices": [] }
```

**Nepadej, neházej výjimku.** Klientovi odpověz prostě *„Za období … nebyly žádné faktury."* a u toho zůstaň.

---

## 11. Voucher detail jen po `code`, ne po `id`

```
GET /vouchers/{code}     ← funguje (např. /vouchers/ABUCRQ)
GET /vouchers/{id}       ← podle PHP klienta není
```

Pokud máš jen `id`, musíš nejdřív stáhnout list a vytáhnout `code` lokálně.

---

## 12. Nepleť si pole napříč zdroji

| Zdroj | Datum vzniku |
|---|---|
| `/invoices` | `created_on` |
| `/orders` | `created` |
| `/clients` | typicky `created_on` (ne plně ověřeno z fixtur) |
| `/vouchers` | `created_on` |

Při psaní kuchařky / volání API se vždy podívej, jak se pole jmenuje v konkrétním zdroji — viz `endpointy.md`.
