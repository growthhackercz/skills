---
name: fapi
description: Dá agentovi referenční mapu nad FAPI.cz API a kuchařku nejčastějších dotazů klienta o tržbách, fakturách, objednávkách a zákaznících. Agent volá API ad-hoc podle otázky a odpoví v chatu. Read-only — nikdy do FAPI nezapisuje.
category: operations
status: ready
version: "1.0"
publishedAt: "2026-05-20"
metadata: {"openclaw":{"requires":{"bins":["python3","jq"],"env":["FAPI_USER","FAPI_TOKEN"]},"primaryEnv":"FAPI_TOKEN","emoji":"📊"}}
---

# FAPI analytika

Pomáhá ti odpovědět klientovi na otázky o jeho prodeji ve FAPI.cz — tržby, faktury, splatnost, top produkty, top zákazníci, opakované nákupy, vývoj v čase. Read-only.

## Kdy použít

- Klient se ptá na čísla z FAPI: *„Kolik jsem v dubnu vydělal?"*, *„Co se mi nejvíc prodávalo?"*, *„Kdo mi nezaplatil?"*, *„Jak rostou tržby?"*
- Klient chce souhrn / přehled / report dat, která už ve FAPI sám má.

## Kdy nepoužít

- Klient chce **vystavit fakturu**, **vyrobit slevový kód**, **odeslat upomínku** — to jsou write operace, jiný skill.
- Klient se ptá na věci, které FAPI nezná: tagy kontaktů, follow-up sekvence, MRR/churn analytika, refund jako samostatný event. V těchto případech otevřeně řekni *„FAPI o tomhle data nedrží"* — viz `{baseDir}/references/omezeni-a-pasti.md`, bod 8.
- Data jsou ve **SmartEmailing / ECOMAIL / GoHighLevel / Make.com** — sáhni do jejich skillů (až budou).

## Co potřebuješ připravené

Dva údaje v prostředí (env vars):

- `FAPI_USER` — e-mail účtu FAPI
- `FAPI_TOKEN` — API klíč z `Můj účet → API klíče` v FAPI

Pokud chybí, ukaž klientovi `{baseDir}/references/setup.md` a zastav se. Bez tokenu se dál nedá.

## Jak postupovat

### 1. Pochop, co klient chce

- Když je dotaz **nejednoznačný** (chybí období, produkt, klient), **zeptej se jednou krátce**: *„Za jaký rozsah?"* / *„Letošek nebo loni?"* Nepřemýšlej moc dlouho — krátká otázka je lepší než tipovaný report.
- Když klient řekne *„udělej report"* bez upřesnění, default je **měsíční přehled** (recept 7 v kuchařce).

### 2. Najdi recept

`{baseDir}/references/kucharka-dotazu.md` má 8 nejčastějších scénářů s hotovými volání:

1. Kolik jsem vydělal za období?
2. Top produkty
3. Kdo nezaplatil?
4. Po splatnosti
5. Top zákazníci
6. Opakovaní zákazníci
7. Měsíční vývoj tržeb
8. Detail konkrétní faktury / objednávky

Pokud klientova otázka přesně sedí, jeď podle receptu. Pokud ne, slož si volání ze stavebních kamenů:

- `{baseDir}/references/endpointy.md` — co umí který zdroj a jak vypadá JSON
- `{baseDir}/references/filtrace-a-obdobi.md` — jak filtrovat časem a stránkovat
- `{baseDir}/references/omezeni-a-pasti.md` — co FAPI **neumí** (než se začneš škrábat v JSONu)

### 3. Volej API

Vždy přes pomocný skript:

```bash
python3 {baseDir}/scripts/call_fapi.py <cesta> "<query>"
```

Příklady:

```bash
python3 {baseDir}/scripts/call_fapi.py /invoices "created_on_from=2026-04-01 00:00:00&created_on_to=2026-04-30 23:59:59&limit=200"
python3 {baseDir}/scripts/call_fapi.py /statistics/total "type=monthly&start=2026-04-01&end=2026-04-30&including_vat=0"
python3 {baseDir}/scripts/call_fapi.py /invoices/185993812
```

Skript načte `FAPI_USER` + `FAPI_TOKEN` z prostředí, doplní Basic Auth, vrátí JSON na stdout. Tajemství se nikdy nedostává do logů, do URL ani do shell historie. Při HTTP 4xx/5xx vypíše stav i tělo do stderr a skončí s exit kódem 2.

Pro extrakci dat použij `jq`.

### 4. Před fetchem velkého datasetu se zeptej

Pokud odhaduješ víc než ~500 záznamů (typicky roční report u aktivního klienta nebo „top produkty za rok" = stovky faktur × volání na `/orders` per fakturu), **krátce klienta upozorni**:

> *„Tohle si vyžádá cca X volání FAPI (může to trvat ~Y sekund). OK?"*

Pro `/invoices` existuje `/invoices/count` — volej ho **před** samotným fetchem, ať víš velikost.

### 5. Spočítej v hlavě nebo přes `jq`

FAPI neagreguje za tebe (kromě `/statistics/total`). Klasické součty, group-by, řazení dělej v Python heredoc nebo přes `jq`. Pro netriviální (>50 záznamů, víc skupin) volej `python3 <<'EOF' ... EOF`.

### 6. Před odpovědí zkontroluj pasti

Než pošleš klientovi čísla, projeď v hlavě tyhle položky (detaily v `{baseDir}/references/omezeni-a-pasti.md`):

- **Mix měn** — máš ve výsledku CZK + EUR? Použij `total_czk` nebo to rozděl.
- **Storno** — odečetl jsi stornované faktury z tržby?
- **Status faktury** — `paid` a `cancelled` jsou bool flagy, ne enum. Skládáš stav správně?
- **Částečné platby** — FAPI je nevidí. Pokud jde o cashflow, řekni klientovi, že vidíš jen „celá / vůbec".
- **`/orders` bez datumového filtru** — fetchovals přes spárované faktury, ne tipnutým parametrem?

Pokud na něco narazíš, **řekni to v odpovědi otevřeně.** Klient ocení, že víš, kde je nejistota.

### 7. Odpověz v chatu

- **Default formát: markdown s tabulkou.** Hlavní čísla tučně, pozadí textem (1–2 věty).
- Vždy uveď období, počet záznamů a zdroj („Spočítáno z 47 placených faktur v dubnu 2026").
- **Soubor (Excel, PDF) jen když si klient výslovně řekne** — předej `anthropic-skills:xlsx` nebo `guide-pdf-generator`.

## Navazující skilly

| Klient chce | Použij |
|---|---|
| Hezké PDF s tabulkami | `guide-pdf-generator` (popis viz jeho `description`) |
| Export do Excelu | `anthropic-skills:xlsx` |
| Něco zapsat do FAPI (faktura, voucher) | Tento skill ne — bude jiný (`fapi-write` v plánu) |
| Webhook FAPI → GoHighLevel | Tento skill ne — bude samostatný most |

## Co dělat, když narazíš

- **HTTP 401** → token je špatný nebo expirovaný (i když oficiálně neexpiruje). Ukaž `references/setup.md`, ať klient vyrobí nový.
- **HTTP 400** → špatný filtr. Často: nesprávný název parametru (zkontroluj `endpointy.md` a `filtrace-a-obdobi.md`), datum mimo měsíc (např. `2026-04-31`).
- **HTTP 404** → ID neexistuje.
- **Empty result** → odpověz prostě *„Za období … žádná data."*, nepadej.
- **„API umí X?" a ty nevíš** → `endpointy.md` má seznam ověřených endpointů. Pokud něco není potvrzené, **netvor si** — zeptej se klienta, jestli to chce empiricky vyzkoušet.

## Hlavní zdroje pro tebe

- `{baseDir}/references/prehled-api.md` — base URL, auth, formát odpovědi, chyby
- `{baseDir}/references/endpointy.md` — katalog zdrojů + reálné JSON tvary
- `{baseDir}/references/filtrace-a-obdobi.md` — datumové filtry, paginace, časová pásma
- `{baseDir}/references/omezeni-a-pasti.md` — co FAPI nemá, na co dát pozor
- `{baseDir}/references/kucharka-dotazu.md` — 8 hotových receptů
- `{baseDir}/scripts/call_fapi.py` — pomocný skript pro volání API
- `{baseDir}/references/setup.md` — nastavení FAPI_USER + FAPI_TOKEN
