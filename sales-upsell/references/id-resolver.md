# ID-resolver — jak se z transakce stane spolehlivé „co koupil"

Bez důvěryhodné odpovědi na „co přesně zákazník koupil" je celé doporučování na písku. Resolver běží uvnitř `purchase_sync.py`; tento dokument vysvětluje logiku, abys věděl, čemu věřit a co říkat v návrzích.

## Zdroj nákupních událostí: transakce v CRM

Primární zdroj = **transakce** (Payments → Transactions). Nesou kontakt,
částku, stav a původ platby. GHL `startAt/endAt` vymezuje interval podle data,
není to cursor změn; proto každý běh znovu stránkuje celé známé bounded historické
okno a kontroluje stabilní `totalCount` i unikátní ID. Jen tak se pozdější
pending→paid nebo paid→refund změna starší transakce neztratí. Položky s
produktem se dohledávají podle původu:

| Původ transakce | Jak resolver získá položky | Spolehlivost |
|---|---|---|
| Objednávka v platformě (funnel / checkout) | detail objednávky — seznam objednávek položky NEVRACÍ, detail ano (vč. produktu) | vysoká |
| Faktura z FAPI (vytváří automatizace) | transakce nese **číslo FAPI faktury** → dotaz do FAPI → položky s **katalogovými kódy** | vysoká (deterministický join) |
| Ruční platba / jiné | položky se neurčí (`match: none`) — doporučení stavěj jen na dřívějších rozpoznaných nákupech kontaktu | nízká |

Pozn.: schéma položky faktury v CRM žádné pole pro katalogový kód nemá (jen název/částka/množství/daň) — proto je join přes číslo faktury do FAPI nutný a nejde obejít.

## Čtyři fáze resolveru

1. **Hygiena položek:** do párování vstupují JEN produktové řádky. Doprava, dobírka, balné, pojištění a slevové řádky (záporná cena) se vyřazují. „Hlavní položka" nákupu = nejdražší produktový řádek.
2. **Párovací klíč — konfigurovatelný per klient** (salesDNA §11, podsekce Feed, řádek „Párovací klíč"):
   - `feed_id` — kód z objednávky odpovídá `g:id` ve feedu (typicky Shoptet/Heureka interní ID)
   - `sku` — odpovídá `g:mpn` (katalogové/výrobní číslo) [výchozí]
   - `ean` — odpovídá `g:gtin` (čárový kód)
   Který klíč sedí, rozhodl audit při aktivaci — NIKDY neměň bez ověření na reálné objednávce. Když kód nesedí na nic, zkusí se opatrné párování podle názvu s příznakem `match: name` (nízká jistota — v návrhu to přiznej).
3. **Varianty přes skupinu produktů (`item_group_id`):** vlastnictví, vyřazování i doporučování se počítá na úrovni skupiny, ne jednotlivého SKU. Jinak bychom doporučili koupené tričko v jiné barvě.
4. **Měny a ceny:** ceny se normalizují parserem, který zvládne `1 299,00 CZK` i `1299.00` — porovnávej vždy hodnoty ze skriptu, nepočítej ceny z hlavy.

## „Co už má" (owned)

- Množina skupin produktů per kontakt pouze z řádků s kanonickým stavem `paid` v `purchases.json`. Pending, failed, unpaid i neznámý stav jsou auditní data, nikoli nákup, a nevstupují ani do párové evidence.
- Stejné transaction ID není navždy „seen": pozdější změna pending→paid aktualizuje existující řádek a vytvoří právě jednu nákupní událost. Opakovaný paid snapshot nevytvoří duplikát.
- **Storno/vratka:** pozdější paid→refund aktualizace nebo samostatná refund transakce se stejnou objednávkou zachová identitu položek, odebere skupinu z „owned" i z co-purchase miningu a současně ji drží v `refunded` blacklistu (vratka = negativní signál).
- **Slepé okno před integrací:** historie je spolehlivá až od data napojení skillu. Skript označuje `history_since` — u kontaktů s krátkou historií formuluj opatrně („podle dostupné historie…") a nefabuluj, co koupili dřív.

## Co s tím v praxi

- `upsell_recommend.py --contact <id>` ti vrátí: co koupil (s jistotou párování), co už má a kandidáty. Důvěřuj polím `match` a `history_since`.
- `purchase_count` počítá jen stále platné zaplacené nákupy; refundované a nezaplacené řádky nikdy nemění tón na „opakovaný zákazník".
- Kandidát s evidencí z `match: name` položek ber s rezervou — pokud je na výběr kandidát s tvrdým párováním, má přednost.
- Když resolver nic nespároval (`match: none` u hlavní položky), NEdoporučuj z evidence — použij přibité páry ze salesDNA §11, případně productDNA, a v logu to přiznej.
