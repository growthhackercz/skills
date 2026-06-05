---
name: cliqsales-email-publisher
description: "Vytvari draft email kampane v CliqSales/GoHighLevel Campaigns V2 z HTML/TXT/manifest vystupu email-draft-orchestratoru. Default je draft; schedule/send jen po explicitnim potvrzeni."
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---
# CliqSales Email Publisher

Tento skill je GHL/CliqSales adapter pro draft email kampane. Nepise copy a neprevadi Markdown; k tomu pouzij `email-writer` a `email-draft-orchestrator`.

## Vstup

Preferovany vstup:

```text
/documents/brand/content/email/{campaign-slug}/email-manifest.json
```

Podporuje i jeden `.html` soubor s `EMAIL METADATA` komentarem.

## GHL API cesta

Primarni draft target je Email Campaigns V2 draft:

```text
GET   /emails/public/v2/locations/:locationId/campaigns/emails
POST  /emails/public/v2/locations/:locationId/campaigns/email-campaign
PATCH /emails/public/v2/locations/:locationId/campaigns/:campaignId
```

Required scopes:

```text
emails/campaigns.readonly
emails/campaigns.write
```

Schedule/send endpointy nepouzivej bez realneho overeni tokenu a explicitniho potvrzeni uzivatele.

## Konfigurace

Minimalni env:

```text
GHL_API_KEY
GHL_LOCATION_ID
GHL_USER
```

Volitelne:

```text
GHL_API_VERSION=2023-02-21
GHL_API_BASE_URL=https://services.leadconnectorhq.com
GHL_USER_ID
GHL_TIME_ZONE=Europe/Prague
GHL_FROM_NAME
GHL_FROM_EMAIL
GHL_REPLY_TO
```

## Workflow

1. Spust `test` pro overeni `GET /emails/public/v2/locations/:locationId/campaigns/emails`.
2. Nacti `email-manifest.json` nebo HTML metadata.
3. Pro kazdy email vytvor GHL email campaign draft.
4. Vrat `campaignId`, `status=draft`, status a chyby.
5. Batch mod je `continue`.
6. Over dohledatelnost pres `readback --campaign-id`.

## CLI helper

```bash
python3 scripts/ghl_email_publish.py test
python3 scripts/ghl_email_publish.py draft --input email-001.html
python3 scripts/ghl_email_publish.py batch-draft --manifest email-manifest.json --mode continue
python3 scripts/ghl_email_publish.py readback --campaign-id CAMPAIGN_ID
python3 scripts/ghl_email_publish.py update --campaign-id CAMPAIGN_ID --input email-001.html --confirm-update yes
```

## Bezpecnostni pravidla

- Nikdy neposilej ani nescheduleuj kampan bez explicitniho potvrzeni.
- Samostatny `update` existujici campaign draft ID je povoleny jen s `--confirm-update yes`.
- Token nepatri do CLI argumentu ani do chatu.
- Pri `422` reportuj presnou chybu a payload keys; neprepisuj token.
- Pokud GHL schema vyzaduje upravu payloadu, uprav jen `build_campaign_payload()`.

## Output template

```markdown
# GHL email drafty pripraveny

- Target: cliqsales/ghl email campaign draft
- Total: {n}
- OK: {ok}
- Failed: {failed}

## Detail
{email id, subject, campaignId, status/error}
```
