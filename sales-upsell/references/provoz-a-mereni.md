# Provoz a měření — aktivace, tagy, sekvence, trychtýř, log

## Jednorázová aktivace (s majitelem, cca 15 minut)

1. **Sales DNA:** ověř §11 — podsekci Feed (zdroj: veřejná HTTPS URL Google Shopping feedu NEBO lokální soubor/productDNA u služeb; řádek „Párovací klíč: feed_id/sku/ean") a Mantinely a sekvence. HTTP, URL na private/loopback/link-local síť a nestandardní port jsou zakázané. Vzdálený feed má výchozí strop 20 MB, 30 s a 3 znovu validované redirecty. Chybí → doplnit přes sales-dna-generator.
2. **Ověření párování na 1 reálné zaplacené objednávce:** bezpečně načti katalog (`feed_catalog.py`), spusť `purchase_sync.py --mode full`, u poslední paid objednávky zkontroluj, že kód položky sedí na feed. Pending/failed/refund se pro doporučení ignorují. Nesedí → zkus jiný párovací klíč, výsledek zapiš do §11 (Feed).
3. **Obálka e-mailu:** operátor spustí `python3 {baseDir}/scripts/ghl_offer_push.py --setup --brand-name "<název firmy>" --footer "<patička vč. možnosti odhlášení>" --email-from "<ověřená odesílací adresa ze Sales DNA §1>"`. Skill uloží jen `config.json` s obálkou a `email_from`; starý config bez neprázdné adresy je neplatný a nabídka fail-closed vyžádá nový setup. Custom-field create/update a podmíněné tracking fields zůstávají future capability, dokud není provider-atomický CAS. **Patičku i odesílací adresu majitel výslovně schválí.**
4. **Odpovědi:** tato verze sama nevytváří ani neověřuje reply bridge, `upsell-reply` workflow nebo DND automatizaci. Pokud je klient má mimo skill prokazatelně nasazené, lze jejich data použít pro report; jinak je označ jako chybějící integraci a netvrď automatické předání/rušení.
5. **Kurátorské tabulky §11 (bootstrap):** spusť `upsell_recommend.py --mine` a z top párů + bestsellerů navrhni vyplnění tabulek §11 podle `{baseDir}/references/salesdna-upsell-sekce.md`. Majitel projde a schválí; s prázdnými tabulkami jede skill čistě na evidenci. Po uložení zkontroluj `rules_unknown_groups` (překlepy kódů).
6. **Režim:** zapiš do salesDNA §1 řádek `Upsell režim: se schválením` (výchozí start pro každého).
7. **Test:** seed kontakt (vlastní e-mail) → zmrazit celý exact E1/E2/E3 plán → jednou potvrdit jeho SHA → ověřit provider receipt/readback a teprve potom doručení/plán/tagy. E-mailový cancellation test používá svázané `messageId` + `emailMessageId` z provider receipt v `--guard-input`, vytvoří samostatný exact plán a ověřuje jeho journal; žádný krok nesmí volat GHL mimo sdílený helper.

## Tagový slovník (single writer = tento skill, pokud není řečeno jinak)

| Tag | Význam | Kdo zapisuje |
|---|---|---|
| `produkt:<slug>` | koupil produkt (fallback identifikace) | tento skill |
| `upsell-sent:<RRRR-MM-DD>` | evidenční datum nabídky; cooldown 30 dní §11 se v této verzi kontroluje ručně | tento skill |
| `osloven:<RRRR-MM-DD>` | globální touch-cap napříč skilly (max 2 / 14 dní §7) | každý odchozí skill |
| `upsell-reply` | volitelný externí signál reakce | pouze již existující a ověřený workflow; skill jej nezakládá |
| DND | nerušit — tvrdě respektovat | platforma |

Skill připravuje exact preview a jeden zmrazený čtyřslotový plán. E2 závisí na E1, E3 na E2 a compliance tag až na E3; tag nemůže předběhnout naplánování sekvence. E-maily provede pouze sdílený helper po souhlasu s exact SHA. Důkazem provedení je jen kompletní execution journal s provider receipt a readbackem.

## Sekvence a ruční guard

- **Sekvence se plánuje celá dopředu** hned po nákupu. Výchozí časy dle best practices (cross-sell až po doručení a první zkušenosti s produktem): fyzické zboží **E1 hned · E2 +7 dní · E3 +14 dní**; služby/digitál (doručení okamžité) **E1 hned · E2 +2 dny · E3 +7 dní**. Klient ladí v salesDNA §11 (Mantinely a sekvence). Všechny e-maily jsou vidět na kartě v Konverzacích jako naplánované.
- **Guard (pouze ruční):** producent přijme explicitní `--guard-input` s hlavním `messageId`, kanálem a ověřeným důvodem; e-mail povinně přidává `emailMessageId` ze stejného receipt, SMS ho naopak nesmí nést. Volitelně lze společně uvést `sourcePlanSha256` + `sourceActionId` pro audit. Jeden cancellation plán obsahuje právě jednu zprávu. Helper před dispatch ověří vazbu ID, location a stav `scheduled`. Automatická detekce reply/DND v této verzi neexistuje.
- Po E3 sekvence KONČÍ. Žádný čtvrtý dotyk; další slovo má Conversation AI po odpovědi.

## Měření a trychtýř

- Trychtýř z úspěšných execution receipt/readbacků + tagů: **nabídky → odpovědi (`upsell-reply`) → nákupy doporučené skupiny do 30 dní → Kč**. `upsell-log.jsonl` eviduje pouze vznik nebo doplnění plánu.
- Do reportu stratéga: `Upsell: N nabídek → X odpovědí → Y nákupů, Z Kč připsáno. Nejlepší pár: A → B.`
- **Poctivé vykazování:** report uvádí tržby **připsané** nabídkám (zákazník koupil doporučenou skupinu do 30 dní po nabídce), NE „přírůstkové" — bez kontrolní skupiny nevíme, kolik by koupil i bez nabídky. Nevydávej připsané za to, „co nabídky přidaly navíc".
- Malé vzorky: pod ~30 oslovených uváděj jen trend, ne procenta.

## Formát logu (`/documents/sales/upsell-log.jsonl`, zapisuje skript)

Log sleduje pouze přípravu, ne provider doručení. Každý řádek má `ts`,
`producer: sales-upsell`, `contactId`, `step`, `slug` a jeden ze dvou tvarů:

- `action: block` + `note` — judge návrh zablokoval;
- `action: plan-updated` + `planArtifact`, případné `planSha256` a
  `planActionIds` — vznikl nebo se doplnil frozen plán.

Provider `messageId`, `emailMessageId`, stav odeslání a readback žijí pouze v
kanonickém execution journalu podle SHA plánu. Trychtýř ani doručení proto nikdy
neodvozuj z `upsell-log.jsonl`; log slouží jen pro audit návrhů a blokací a
ručně se needituje.

## Budoucí automatický guard — nyní neaktivní

`upsell-provoz` v této verzi nevytvářej v Plánovači. Chybí named read projekce, která by svázala live reply/DND s exact provider `messageId`; bez ní by cron pouze předstíral autonomii. Guard lze spustit ručně nad jedním ověřeným kandidátem a samostatným CSO taskem. Budoucí aktivace musí současně dodat projekci, exact declared cron name a setup checkpoint.

Nabídky po nákupu spouští stratég (hodinový běh vidí novou transakci → zadá úkol); tento skill vlastní cron na nabídky nepotřebuje.
