---
name: smartemailing-email-publisher
description: "Vytvari draft/ulozeny email asset ve SmartEmailingu z HTML/TXT/manifest vystupu email-draft-orchestratoru pres API v3. Newsletter/send krok je zakazany bez explicitniho potvrzeni."
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---
# SmartEmailing Email Publisher

Tento skill je SmartEmailing adapter pro email drafty. Nepise copy a neposila kampane.

## Vstup

Preferovany vstup:

```text
/documents/brand/content/email/{campaign-slug}/email-manifest.json
```

Podporuje i jeden `.html` soubor s `EMAIL METADATA` komentarem.

## SmartEmailing API cesta

Autentizace:

```text
Basic auth: SMARTEMAILING_USERNAME + SMARTEMAILING_API_KEY
Base URL: https://app.smartemailing.cz/api/v3
```

Draft/ulozeny email asset:

```text
POST /api/v3/emails
```

Payload:

```json
{
  "title": "Nazev emailu",
  "name": "Nazev emailu",
  "htmlbody": "<html>...</html>",
  "textbody": "plain text"
}
```

Newsletter krok:

```text
POST /api/v3/newsletter
```

Payload:

```json
{
  "email_id": 123,
  "contactlists": [456]
}
```

`newsletter` nespoustej automaticky. Je to dalsi krok po vytvoreni email assetu a vyzaduje explicitni potvrzeni + contactlist.

## Konfigurace

Preferovana konfigurace je Control Center integrace SmartEmailing v Settings -> Integrations.
Helper cte `SMARTEMAILING_USERNAME` a `SMARTEMAILING_API_KEY` z runtime env,
`${OPENCLAW_HOME}/.env` a sdileneho Control Center credential store. Samostatny
`secrets/smartemailing.env` je jen legacy fallback.

Minimalni hodnoty:

```text
SMARTEMAILING_USERNAME
SMARTEMAILING_API_KEY
```

Volitelne:

```text
SMARTEMAILING_API_BASE_URL=https://app.smartemailing.cz/api/v3
SMARTEMAILING_ACCOUNT_ID
```

## Workflow

1. Spust `test` (`ping`, `contactlists`, `emails`, `newsletters` read-only).
2. Nacti HTML/TXT z manifestu.
3. Vytvor ulozeny email pres `POST /emails`.
4. Batch mod je `continue`.
5. Vrat `email_id`/`id`, status a chyby.

## CLI helper

```bash
python3 scripts/smartemailing_publish.py test
python3 scripts/smartemailing_publish.py draft --input email-001.html
python3 scripts/smartemailing_publish.py batch-draft --manifest email-manifest.json --mode continue
python3 scripts/smartemailing_publish.py newsletter --email-id 123 --contactlist-id 456 --confirm-newsletter yes
```

## Bezpecnostni pravidla

- Nikdy nevolej `send/*`.
- `newsletter` pouze po explicitnim potvrzeni uzivatele.
- API key nepatri do CLI argumentu ani do chatu.
- Pri chybe reportuj endpoint, status a redigovanou API odpoved.

## Output template

```markdown
# SmartEmailing email drafty pripraveny

- Target: smartemailing emails
- Total: {n}
- OK: {ok}
- Failed: {failed}

## Detail
{email id, subject, smartemailing email_id, status/error}
```
