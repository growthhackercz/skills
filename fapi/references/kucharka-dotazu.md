# Kuchařka nejčastějších dotazů

Recepty na nejběžnější otázky od klienta. Každý recept: jak otázku klient typicky položí → co volat → jak složit odpověď → na co dát pozor.

> **Před každým receptem:** Pokud klient neurčil období, **zeptej se krátce**. *„Za jaký časový rozsah? Třeba duben 2026, poslední 30 dní, letošek?"* Pak jeď.

> **Předpoklad:** všechny příklady používají `{baseDir}/scripts/call_fapi.py`. Pomocníkem na zpracování JSONu je `jq`.

---

## Recept 1 — Kolik jsem za období vydělal?

**Klient řekne:** *„Kolik mi přišlo v dubnu?" / „Jaká byla tržba v Q1?" / „Vydělali jsme letos víc než loni?"*

### Cesta A — přes `/statistics/total` (preferovaná, 1 volání)

```bash
python3 {baseDir}/scripts/call_fapi.py /statistics/total "type=monthly&start=2026-04-01&end=2026-04-30&including_vat=0"
```

Z odpovědi vezmi řadu `paid` (případně `invoiced` pokud chce klient nominální fakturáci místo skutečně přijatých peněz).

> Tvar elementů v polích `paid`/`issued`/… není v dokumentaci přesně popsaný. Při prvním volání si výstup pročti a podle toho extrahuj sumu — typicky je to objekt typu `{"date":"2026-04-30","value":12345}` nebo `{"period":"2026-04","amount":12345}`. **Zkonzultuj reálný výstup před tím, než řekneš číslo klientovi.**

### Cesta B — přes `/invoices` (jistější tvar, víc volání)

```bash
python3 {baseDir}/scripts/call_fapi.py /invoices/count "created_on_from=2026-04-01 00:00:00&created_on_to=2026-04-30 23:59:59"
# → {"count": 47}

python3 {baseDir}/scripts/call_fapi.py /invoices "created_on_from=2026-04-01 00:00:00&created_on_to=2026-04-30 23:59:59&limit=200"
```

Pak v hlavě:

```
zaplaceno  = sum(total_czk)  WHERE paid == true   AND cancelled == false
stornováno = sum(total_czk)  WHERE cancelled == true
čistá tržba = zaplaceno - stornováno
```

### Odpověď klientovi (vzor)

> **Tržba duben 2026**
> - Vystaveno: **142 300 Kč** (47 faktur)
> - Zaplaceno: **128 900 Kč** (43 faktur)
> - Stornováno: **3 200 Kč** (1 faktura)
> - **Čistá tržba: 125 700 Kč**

### Pasti

- **Mix měn** — pokud klient má i EUR/USD faktury, vždy použij `total_czk`, nebo se zeptej, jestli chce výsledek v původních měnách (viz `omezeni-a-pasti.md`, bod 3).
- **Storno** se z tržby odečítá (viz bod 1 v omezení).
- **Bez DPH vs s DPH** — `total_czk` je včetně DPH. Pokud klient chce bez, odečti `total_vat`.

---

## Recept 2 — Které produkty se za období prodaly nejvíc?

**Klient řekne:** *„Co se mi nejvíc prodávalo v dubnu?" / „Top 5 produktů za poslední čtvrtletí" / „Který kurz je trhák?"*

### Volání

`/statistics/total` produkty nevidí — musíš na `/orders`. Protože **`/orders` nemá ověřený datumový filtr**, jdi přes faktury:

```bash
# 1) Vytáhni faktury v okně
python3 {baseDir}/scripts/call_fapi.py /invoices "created_on_from=2026-04-01 00:00:00&created_on_to=2026-04-30 23:59:59&limit=200"
```

Z výstupu si vytáhni `id` všech faktur. Pak pro **každou fakturu** zavolej:

```bash
python3 {baseDir}/scripts/call_fapi.py /orders "invoice=<INVOICE_ID>&limit=10"
```

> **Tip pro středně velké datasety (řekněme <100 faktur):** procházej sekvenčně, sbírej `items[]` z každé objednávky.
> **Pro stovky+ faktur** se nejdřív klienta zeptej, jestli má cenu to projet (každá faktura = jedno volání).

### Postup výpočtu

V hlavě vytvoř mapu `product_name -> {count: 0, revenue: 0}`. Pro každou objednávku, pro každý `items[]` element:

```
key = items[i].name
mapa[key].count   += items[i].count
mapa[key].revenue += (items[i].price_czk ?? items[i].price * items[i].count)
```

Seřaď podle `revenue` sestupně, vezmi top N.

### Odpověď klientovi (vzor)

> **Top 5 produktů — duben 2026**
> | # | Produkt | Prodáno ks | Tržba |
> |---|---|---:|---:|
> | 1 | AI Akcelerátor | 12 | 599 640 Kč |
> | 2 | Workshop AI marketing | 18 | 142 200 Kč |
> | 3 | … |
>
> _Spočítáno z 47 placených objednávek za období._

### Pasti

- **Stornované faktury** by se měly z výpočtu vyřadit (`cancelled == true` skipni).
- **Cena v `price` vs `price_czk`** — pokud klient měl objednávky v EUR, `price_czk` je přepočet. Konzistentně použij jeden field.

---

## Recept 3 — Kdo mi ještě nezaplatil?

**Klient řekne:** *„Kdo mi dluží?" / „Které faktury mám otevřené?"*

### Volání

```bash
python3 {baseDir}/scripts/call_fapi.py /invoices/count "created_on_from=2026-01-01 00:00:00&created_on_to=2026-12-31 23:59:59"
python3 {baseDir}/scripts/call_fapi.py /invoices "created_on_from=2026-01-01 00:00:00&created_on_to=2026-12-31 23:59:59&limit=300"
```

(Bez explicitního omezení období se zeptej; default „letošek" je rozumný.)

### Filtr lokálně

```
nezaplacené = WHERE paid == false AND cancelled == false
```

Seřaď podle `payday_date` vzestupně. Vyznač ty, kde `payday_date < dnes` (po splatnosti).

### Odpověď (vzor)

> **Otevřené faktury (12 ks, celkem 87 400 Kč)**
> | Číslo | Klient | Vystaveno | Splatnost | Částka | Stav |
> |---|---|---|---|---:|---|
> | 202604001 | Nováková s.r.o. | 2026-04-02 | 2026-04-16 | 12 500 Kč | 🔴 po splatnosti (33 dní) |
> | 202604012 | Pavel Novák | 2026-04-10 | 2026-04-24 | 4 200 Kč | 🔴 po splatnosti (25 dní) |
> | 202605007 | … | 2026-05-15 | 2026-05-29 | 8 900 Kč | čeká |
>
> Tučně po splatnosti = **5 faktur za 38 200 Kč**.

### Pasti

- Storno nepočítej do dluhu (vyřadit `cancelled == true`).
- Jméno klienta nemusí být přímo na faktuře — pokud `customer.name` chybí, dotáhni si přes `/clients/{client}`.

---

## Recept 4 — Kolik faktur je po splatnosti?

**Klient řekne:** *„Co mám po splatnosti?" / „Kolik mám overdue?"*

### Cesta A — z `/statistics/total`

```bash
python3 {baseDir}/scripts/call_fapi.py /statistics/total "type=daily&start=2026-01-01&end=2026-05-19&including_vat=0"
```

Vezmi řadu `overdue` — FAPI tě její denní hodnotu spočítá samo. (Tvar elementu ověř při prvním volání.)

### Cesta B — z `/invoices` + lokální filtr

Stejné jako recept 3, ale ostře filtruj `payday_date < dnes`. Drobnější, ale dáš klientovi i seznam konkrétních dluhů, nejen souhrn.

### Odpověď

> **Po splatnosti k 19. 5. 2026:** 5 faktur, **38 200 Kč** dohromady.
> Nejstarší: Nováková s.r.o., po splatnosti 33 dní.

---

## Recept 5 — Kdo jsou moji top zákazníci?

**Klient řekne:** *„Kdo u mě nejvíc utrácí?" / „Top 10 zákazníků letos"*

### Volání

```bash
python3 {baseDir}/scripts/call_fapi.py /invoices "created_on_from=2026-01-01 00:00:00&created_on_to=2026-12-31 23:59:59&limit=300"
```

### Postup

V hlavě vytvoř mapu `client_id -> revenue` (jen placené, nestornované). Vezmi top N. Pro každého top zákazníka dotáhni jméno:

```bash
python3 {baseDir}/scripts/call_fapi.py /clients/1808089
```

Nebo (pokud klientů je víc) využij `customer.name` přímo z faktury — bývá tam vyplněné.

### Odpověď (vzor)

> **Top 10 zákazníků 2026 (zatím)**
> | # | Klient | Tržba | Počet faktur |
> |---|---|---:|---:|
> | 1 | Petr Adamík | 89 400 Kč | 4 |
> | 2 | Anna Nováková | 64 200 Kč | 2 |
> | … |

### Pasti

- Pokud jeden klient platí pod různými emaily (B2B vs osobní), `client` ID rozdělí jeho útratu. Není co s tím — FAPI nezná „merge".

---

## Recept 6 — Kolik mám opakovaných zákazníků?

**Klient řekne:** *„Kolik lidí ode mě koupilo víckrát?"*

### Volání

```bash
python3 {baseDir}/scripts/call_fapi.py /invoices "created_on_from=2026-01-01 00:00:00&created_on_to=2026-12-31 23:59:59&limit=300"
```

### Postup

Group-by `client` field (filtruj `paid == true AND cancelled == false`). Spočítej:

```
opakovaní = klienti, kde COUNT(faktur) > 1
jednorázoví = klienti, kde COUNT(faktur) == 1
```

### Odpověď (vzor)

> **Klientská struktura — 2026**
> - Celkem aktivních zákazníků: **142**
> - Opakovaní (≥ 2 nákupy): **38 (27 %)**
> - Jednorázoví: **104 (73 %)**

### Past

- Tahle metrika se mění v čase. Klient ji intuitivně bere jako absolutní, ale fakticky závisí na zvoleném okně — *„opakovaný v dubnu"* a *„opakovaný za rok"* jsou různé počty.

---

## Recept 7 — Jak vypadá tržbový vývoj po měsících?

**Klient řekne:** *„Ukaž mi vývoj tržeb" / „Měsíční přehled" / „Roste mi to?"*

### Volání (jedna jediná, levně)

```bash
python3 {baseDir}/scripts/call_fapi.py /statistics/total "type=monthly&start=2026-01-01&end=2026-12-31&including_vat=0"
```

(Pokud `type=monthly` FAPI nepřijme, zkus `type=daily` a agreguj po měsících sám.)

### Odpověď (vzor)

> **Měsíční tržby — 2026**
> | Měsíc | Zaplaceno | Vystaveno | Stornováno |
> |---|---:|---:|---:|
> | Leden | 142 300 | 156 800 | 4 200 |
> | Únor | 128 900 | 132 500 | — |
> | Březen | 198 400 | 210 200 | 8 900 |
> | Duben | 174 600 | 182 100 | 2 100 |
> | Květen (dosud) | 89 200 | 92 700 | — |
>
> Trend: **růst Q1→Q2 +18 %**.

### Past

- Pokud klient porovnává letošek vs. loni, udělej dvě volání a postav je vedle sebe — neexistuje endpoint, který by srovnání udělal sám.

---

## Recept 8 — Detail jedné konkrétní faktury / objednávky

**Klient řekne:** *„Co bylo na faktuře 202604012?" / „Detail objednávky 12440538"*

### Volání

```bash
# Po čísle faktury — VS bývá v poli `number`. Není přímý lookup, takže přes filtrace:
python3 {baseDir}/scripts/call_fapi.py /invoices "limit=1&created_on_from=2026-04-01 00:00:00&created_on_to=2026-04-30 23:59:59" \
  | jq '.invoices[] | select(.number == "202604012")'

# Po ID (rychlejší, pokud klient ho má):
python3 {baseDir}/scripts/call_fapi.py /invoices/185993812

# Detail objednávky po ID:
python3 {baseDir}/scripts/call_fapi.py /orders/12440538
```

### Co ukázat klientovi

- Číslo, datum, klient (jméno + email z `customer`)
- Položky (`items[]`)
- Stav (zaplaceno / nezaplaceno / stornováno — viz složení stavu v `omezeni-a-pasti.md` bod 4)
- Splatnost a kolik dní do/po
- Celkem v měně faktury i v CZK

### Past

- Pokud klient zná jen variabilní symbol (`number`), musíš si ho vyhledat lokálně — FAPI nemá `/invoices?number=...` filtr ověřený. Buď fetch v dostatečném okně a `jq` filtr, nebo se zeptej klienta na rozsah období.

---

## Kdy klient chce hezký výstup do souboru

**Default:** odpověz v chatu (markdown tabulky). Soubory dělej jen, když si klient řekne.

| Klient chce | Co s tím |
|---|---|
| „pošli mi to v Excelu" | Předej data dál — vyvolej skill `anthropic-skills:xlsx` s naplněnými daty |
| „udělej z toho hezké PDF" | Předej skill `guide-pdf-generator` (klient má prostě tabulky a čísla, na grafy stačí markdown text) |
| „pošli to e-mailem zákazníkovi" | FAPI má `/invoices/{id}/send-email` — ale to už je write operace, mimo scope tohoto skillu |

---

## Co dělat, když dotaz nepasuje na žádný recept

1. Identifikuj, který zdroj má potřebná data (viz `endpointy.md`).
2. Slož filtr (viz `filtrace-a-obdobi.md`).
3. Postav volání a otestuj malým `limit=5` ať vidíš, co reálně chodí.
4. Pokud zjistíš, že **data v FAPI prostě nejsou** (např. tagy, cohort, MRR), řekni to klientovi rovnou — viz `omezeni-a-pasti.md` bod 8.
