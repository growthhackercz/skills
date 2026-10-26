# Sales Prospector → CliqSales bezpečný kontrakt

Prospector připravuje do CRM pouze aditivní tag u kontaktu, který tenantní
named read helper našel jako exact existující záznam. Credential načítá pouze
sdílený strict resolver a nikdy jej nevypisuje.

## Aktivní capability

- action type: `sales.ghl.tags.add.v1`
- tag: `sales prospector`
- payload nese exact `contactId` a brokerovaný e-mail/telefon
- nezaměňuje ani nemaže existující tagy

Volitelný CSV sloupec `ContactId` je autoritativní explicitní target; helper ho
před plánem načte a případný e-mail/telefon z řádku porovná s live kontaktem.
Bez `ContactId` smí e-mail/telefon vybrat mutation target jen při právě jedné
exact shodě v úplném bounded contact scanu. Duplicita, změna totalu, neúplná
stránka nebo tenant nad 10 000 kontaktů znamená STOP a doplnění `ContactId`.

CSV `Tags`, kampaň, zdroj, hook a signál zájmu se do CRM nepřenášejí; zůstávají
v `/documents/sales/prospects/<campaign>/` pro lidský audit.

## Nenalezený kontakt

Stav `not_found` není oprávnění k zápisu. Kontakt zůstane v `prospects.csv` a
`prospects-review.md` jako file/review výstup. `contact.create` i update polí
jsou deaktivované future capability, dokud platforma nemá provider-atomickou
no-duplicate/CAS operaci. Skill je nesmí nahrazovat ručním API voláním.

## Idempotence a artefakt

Dry-run i plan běh přijímají současně zapečetěné `prospects.csv`,
sesterské `meta.json` a kladné `--task-id`. Ještě před prvním GHL readem
helper ověří package 1.4, exact task/campaign, contract
`sales-prospector:prospect-actions-v1-4` a CSV hash; ruční nebo pozměněné CSV
se k provideru nedostane.

Dry-run vrátí frozen `planned_slots` pouze pro existující kontakty a každý
slot váže na právě nalezené `contactId`, ne jen na hledaný e-mail/telefon.
Změna exact targetu mezi dry-runem a tvorbou plánu proto plán fail-closed
zastaví. Plan běh
převezme celý set přes opakované `--expected-slot`, založí tag actions a
dokončí `/documents/sales/prospects/<campaign>/ghl-plan.json` pouze při
exact coverage. Provedení vyžaduje souhlas s exact SHA; stejný plán se po
chybě ani nejednoznačném výsledku neopakuje.
