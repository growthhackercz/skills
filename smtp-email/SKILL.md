---
name: smtp-email
description: "Ověřuje a odesílá běžné SMTP e-maily přes Control Center Email Accounts API. Nepoužívá legacy SMTP_* env ani nečte tajné hodnoty přímo."
category: integrations
status: ready
version: "1.1"
publishedAt: "2026-05-10"
---

# SMTP Email přes Control Center

Použij tento skill, když uživatel chce ověřit nebo odeslat běžný e-mail přes
mailbox nastavený v Control Center -> Integrace -> Email.

Tento skill je pro **Control Center Email Accounts API**. Není určený pro
GHL/CliqSales kampaně, SmartEmailing drafty ani copywriting. Na tyto případy
použij `cliqsales-email-publisher`, `smartemailing-email-publisher`,
`email-draft-orchestrator` nebo `email-writer`.

## Zdroj pravdy

Používej pouze:

- `$CC_URL`
- `$CC_API_KEY`
- endpointy `/api/email/accounts/...`

Nepoužívej a nevyžaduj:

- `SMTP_HOST`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_PORT`
- `SMTP_SECURE`
- `IMAP_HOST`
- `IMAP_USER`
- `IMAP_PASSWORD`
- přímé čtení `control-center-secrets.json`
- přímý SMTP login z agenta

Email Accounts API samo načte aktuální mailbox konfiguraci, secret a workspace
scope. Když API vrátí chybu, reportuj přesnou chybu bez tajných hodnot.

## Bezpečný helper

Preferuj helper:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py list
```

Helper nikdy nevypisuje API klíč ani secret hodnoty.

## Ověření bez odeslání

Když uživatel chce ověřit, že se lze přihlásit, ale nic neposílat, spusť:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py verify --account-id 1
```

To volá:

```text
POST /api/email/accounts/{id}/test-outgoing
body: {}
```

Bez `testRecipient` se žádný e-mail neodesílá. Ověřuje se pouze SMTP
konfigurace přes Control Center.

Nikdy nepřidávej `testRecipient`, pokud uživatel výslovně nechce poslat
testovací e-mail na konkrétní adresu.

## Reálné odeslání

E-mail odešli pouze když jsou splněny všechny podmínky:

1. uživatel výslovně chce e-mail odeslat,
2. příjemce je jasný,
3. předmět je jasný,
4. tělo e-mailu je jasné nebo je v souboru,
5. nejsi v režimu “jen ověř / nic neposílej”.

Použij helper a povinné potvrzení:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py send \
  --account-id 1 \
  --to "recipient@example.com" \
  --subject "Předmět" \
  --text-file /tmp/email-body.txt \
  --confirm-send yes
```

Pro HTML e-mail přidej `--html-file`. Plain text je stále povinný fallback,
pokud uživatel výslovně nedodal jen HTML.

### Přílohy

Přílohy posílej pouze jako soubory uložené pod `/documents`. Neposílej base64
obsah příloh do chatu, stdout ani payloadu helperu.

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py send \
  --account-id 1 \
  --to "recipient@example.com" \
  --subject "Předmět" \
  --text-file /tmp/email-body.txt \
  --attach /documents/reports/report.pdf \
  --attach /documents/reports/detail.csv \
  --confirm-send yes
```

API podporuje jen bezpečné `/documents/...` path přílohy. `contentBase64`
nepoužívej; pokud ho API odmítne, nepřepínej na přímý SMTP fallback.

Po odeslání vrať:

- `ok`
- account id
- příjemce
- subject
- `messageId`, pokud ho API vrátí
- názvy, typy a velikosti příloh, pokud je API vrátí

Nepřepisuj odpověď jako “odesláno”, pokud API nevrátilo `ok: true`.

## Čtení mailboxu

Seznam účtů:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py list
```

Poslední zprávy:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py latest --account-id 1 --limit 10
```

Vyhledání zpráv:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py search \
  --account-id 1 \
  --from "sender@example.com" \
  --subject "část předmětu" \
  --limit 10
```

Detail zprávy:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py get-message \
  --account-id 1 \
  --uid 123
```

Při práci s příchozími zprávami nevypisuj citlivé osobní údaje zbytečně do
chatu. Shrň jen relevantní obsah.

## Rozhodovací pravidla

- “ověř SMTP”, “ověř přihlášení”, “nic neposílej” -> `verify`.
- “pošli e-mail” / “odešli e-mail” -> `send` po ověření příjemce, předmětu a těla.
- “zkontroluj inbox” / “najdi e-mail” -> `latest`, `search` nebo `get-message`.
- Pokud API hlásí, že účet je disabled nebo agent access disabled, neposílej
  přes jinou cestu. Vrať přesný blocker.
- Pokud chybí `CC_URL` nebo `CC_API_KEY`, nepoužívej legacy SMTP env jako
  fallback. Vrať blocker: Control Center API credentials nejsou dostupné.

## Zakázané fallbacky

Neposílej e-maily přes:

- `python smtplib` s ručním čtením `SMTP_*`,
- `sendmail`,
- `mail`,
- nativní OpenClaw `message send`, pokud není k dispozici skutečný email channel,
- GHL/SmartEmailing publisher skills, pokud uživatel chce běžný SMTP e-mail.

Tyto cesty vedou k duplicitní konfiguraci nebo k jinému typu emailingu.
