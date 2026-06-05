---
name: email-draft-orchestrator
description: "Zastrešuje cely emailing flow: podle zadani rozhodne, kdy zavolat email-writer, potom email-campaigns pro kampanovou strategii, pripravi HTML/TXT/manifest a nakonec zavola publisher pro GHL nebo SmartEmailing draft. Writer skilly mohou fungovat i samostatne."
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---
# Email Draft Orchestrator

Tento skill je ridici vrstva pro cele emailingove zadani. Chova se jako strateg/orchestrator: zastresi flow, pujci si `email-writer` pro copy, `email-campaigns` pro kampanovou logiku a potom zavola spravny publisher podle cilove platformy.

`email-writer` a `email-campaigns` zustavaji samostatne pouzitelne. Pokud uzivatel chce jen text emailu, pouzij `email-writer`. Pokud chce kampan, sekvenci, draft v GHL/SmartEmailingu nebo "nahraj to do platformy", vstupnim bodem je tento orchestrator.

## Kdy pouzit

Pouzij, kdyz uzivatel chce:

- vytvorit novou emailovou kampan nebo sekvenci od zadani az po draft
- vzit hotovy email nebo sekvenci a nahrat ji do draftu
- pripravit emaily pro CliqSales/GHL nebo SmartEmailing
- zkonvertovat stary Markdown email-writer vystup do HTML/TXT handoffu
- batch draft cele emailove sekvence

Nepouzivej, kdyz uzivatel chce jen samostatny email text bez kampane a bez platformy. V takovem pripade pouzij rovnou `email-writer`.

## Pipeline

```text
email-draft-orchestrator
-> email-writer
-> email-campaigns
-> prepare HTML/TXT/manifest
-> target publisher podle cile:
   - cliqsales-email-publisher
   - smartemailing-email-publisher
```

Pokud uz existuje hotovy vystup z `email-writer`, orchestrator preskoci copywritingovy krok a pokracuje od normalizace/validace.

## Vstup

Orchestrator prijima bud zadani kampane, nebo uz hotove podklady:

- brief kampane: cil, publikum, nabidka, pocet emailu, target platforma
- jeden `.md`, `.html` nebo `.txt` email
- slozku s emailovou sekvenci
- `email-manifest.json`, pokud uz existuje
- cil: `ghl`, `cliqsales`, `smartemailing`

Vychozi slozka:

```text
/documents/brand/content/email/{campaign-slug}/
```

## Povinne handoff soubory

Po prepare kroku ma slozka obsahovat:

```text
email-manifest.json
email-001.md      # pokud byl zdroj Markdown
email-001.html
email-001.txt
```

Manifest schema:

```json
{
  "campaign": "campaign-slug",
  "timezone": "Europe/Prague",
  "defaultPublishIntent": "draft",
  "emails": [
    {
      "id": "email-001",
      "name": "Welcome email 1",
      "subject": "rychla otazka",
      "previewText": "zabere ti to 10 sekund",
      "fromName": "Pavel",
      "fromEmail": "",
      "replyTo": "",
      "audience": "new leads",
      "htmlPath": "/documents/brand/content/email/campaign/email-001.html",
      "textPath": "/documents/brand/content/email/campaign/email-001.txt",
      "status": "draft"
    }
  ]
}
```

## Workflow

1. Rozhodni intent:
   - jen text emailu -> predej `email-writer`, orchestrator dal nepokracuje
   - kampan/sekvence/draft/platforma -> pokracuj jako orchestrator
2. Nacti brand/product kontext, pokud existuje.
3. Zavolej nebo pouzij `email-writer` pro vytvoreni emailu/sekvence, pokud hotovy obsah jeste neexistuje.
4. Zavolej nebo pouzij `email-campaigns` pro kampanovou vrstvu: segment, timing, A/B subjecty, sequence plan, poznamky k nasazeni.
5. Spust `scripts/email_prepare.py`, pokud chybi HTML/TXT/manifest.
6. Zkontroluj, ze kazdy email ma `subject`, `previewText`, `htmlPath` a `textPath`.
7. Pokud je cil `ghl` nebo `cliqsales`, zavolej `cliqsales-email-publisher`.
8. Pokud je cil `smartemailing`, zavolej `smartemailing-email-publisher`.
9. Vrat souhrn draftu: target, pocet emailu, ok/failed, ID draftu/emailu, presne chyby.

## CLI helper

```bash
python3 scripts/email_prepare.py prepare --input /documents/brand/content/email/welcome --campaign welcome
python3 scripts/email_prepare.py validate --manifest /documents/brand/content/email/welcome/email-manifest.json
```

## Bezpecnostni pravidla

- Default je vzdy draft.
- Nikdy nevolej `send`, `schedule`, `newsletter` ani `publish` bez explicitniho potvrzeni.
- Samotny prikaz "vytvor kampan" nebo "nahraj do draftu" neznamena souhlas k odeslani.
- Pokud chybi subject, zastav dany email a reportuj chybu.
- Batch mod je `continue`: chyba jedne polozky nema zastavit celou sekvenci.
- Tokeny ani API klice nikdy nevypisuj do chatu ani do prikazu.

## Target pravidla

GHL/CliqSales:

- primary target: Email Campaigns V2 draft pres `cliqsales-email-publisher`
- required scope: `emails/campaigns.write`
- schedule az po potvrzeni a overeni dostupneho schedule endpointu

SmartEmailing:

- primary target: ulozeny email asset pres `POST /api/v3/emails`
- `POST /api/v3/newsletter` je povazovan za campaign/send krok a spousti se jen po potvrzeni, vyberu contactlistu a jasnem pojmenovani email ID
