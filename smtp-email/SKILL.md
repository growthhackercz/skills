---
name: smtp-email
description: "Čte, ověřuje a odesílá běžné e-maily přes Control Center Email Accounts API. Podporuje nakonfigurované IMAP/SMTP i Microsoft 365 účty bez přímého čtení tajných hodnot."
category: integrations
status: ready
version: "1.5"
publishedAt: "2026-10-05"
---

# Email přes Control Center

Použij tento skill, když uživatel chce ověřit nebo odeslat běžný e-mail přes
mailbox nastavený v Control Center -> Integrace -> Email nebo Microsoft 365 Email.

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

Email Accounts API samo vybere správné připojení, načte aktuální mailbox
konfiguraci a workspace scope. Když API vrátí chybu, reportuj přesnou chybu bez
tajných hodnot.

## Bezpečný helper

Preferuj helper:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py list
```

Každý účet ve výstupu obsahuje `maxMessagesPerRead`. Před použitím vyššího
`--limit` než výchozí hodnota příkazu vždy nejdřív načti seznam účtů a
nepoužívej limit vyšší než tento strop. Pokud uživatel potřebuje starší zprávu
za nastaveným stropem, řekni mu, že správce musí zvýšit maximum u Microsoft 365
účtu v Integracích; netvrď, že ve schránce další zprávy nejsou.

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

Bez `testRecipient` se žádný e-mail neodesílá. Ověřuje se pouze odchozí
připojení přes Control Center.

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

Složky Microsoft 365:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py folders --account-id 1
```

Čtení konkrétní složky Microsoft 365 (například Odeslaná pošta):

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py latest \
  --account-id 1 \
  --folder-id sentitems \
  --limit 100
```

`--folder-id` přijímá opaque `id` vrácené příkazem `folders` nebo podporovaný
well-known název Microsoftu, například `inbox` či `sentitems`. Je určený pouze
pro Microsoft 365; u IMAP účtu je požadavek odmítnut, aby se složka nikdy tiše
neignorovala.

Vyhledání zpráv:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py search \
  --account-id 1 \
  --from "sender@example.com" \
  --subject "část předmětu" \
  --after "2026-01-01" \
  --before "2026-09-01" \
  --limit 10
```

`--limit` je celkový počet nejnovějších zpráv, které smí jeden požadavek
projít, nikoli záruka stejného počtu výsledků. Microsoft 365 může mít v Control
Centeru povolený rozsah až 2 000, ale jedna odpověď obsahuje nejvýše 500
procházených zpráv. Pro menší výstup použij `--page-size`, například:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py search \
  --account-id 1 \
  --from "sender@example.com" \
  --limit 2000 \
  --page-size 200
```

Pokud odpověď obsahuje `paging.hasMore: true`, pokračuj stejným příkazem
(`latest` nebo `search`) a opaque hodnotou `paging.nextCursor`:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py search \
  --account-id 1 \
  --cursor "<nextCursor>"
```

Cursor je krátkodobý a vázaný na účet, původní filtry a operaci. Neupravuj ho,
nekombinuj ho s novými filtry a nevypisuj ho uživateli. Stránkuj jen dokud
nenajdeš dostatečný výsledek nebo `hasMore` není `false`. U velkého rozsahu
preferuj `search` s odesílatelem, předmětem nebo datem před neomezeným `latest`.
`paging.scanLimit` je skutečný celkový rozsah přijatý Control Centerem a
`paging.scannedTotal` počet zpráv dosud projitých v této sekvenci. Pokud je
`scanLimit` nižší než požadovaný `--limit`, hledání omezilo nastavení účtu.
Vybraná Microsoft složka je také uvnitř cursoru; při pokračování posílej jen
`--cursor`, nikoli nové `--folder-id` nebo jiné filtry.

Detail zprávy:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py get-message \
  --account-id 1 \
  --uid 123
```

U Microsoft 365 detail obsahuje také pole `attachments` s `id`, názvem,
MIME typem, velikostí, informací o inline obsahu a stavem `downloadable`.
Vybranou přílohu ulož do sdílených dokumentů:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email.py download-attachment \
  --account-id 1 \
  --uid 123 \
  --attachment-id "opaque-id-from-message"
```

Helper zvolí stabilní cestu pod `/documents/email-attachments/...` a vrátí ji
v poli `path`. Jinou cestu lze zadat pomocí `--output /documents/...`.
Existující soubor nepřepisuj bez výslovného `--overwrite`.

Microsoft 365 dovoluje stáhnout nejvýše 20 MB na jednu přílohu. Počet příloh
není omezený. Cloudové referenční přílohy se musí otevřít v Microsoft 365;
generic IMAP účty zatím download příchozích příloh přes tento helper
nepodporují. Stažené soubory považuj za nedůvěryhodné: automaticky je
nespouštěj a neposílej jejich obsah do chatu, pokud to úkol nevyžaduje.

Při práci s příchozími zprávami nevypisuj citlivé osobní údaje zbytečně do
chatu. Shrň jen relevantní obsah.

## Aktuální ID účtu a odolné čtení

Po znovupřipojení Microsoft 365 dostane účet nové ID, proto ho v cronech a
skriptech nezapisuj natvrdo. Aktuální ID vrátí:

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/resolve_account_id.py
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/resolve_account_id.py --email "mailbox@example.com"
```

Bez `--email` funguje jen tehdy, když je nastavená jediná schránka s povoleným
odesíláním; jinak skončí chybou a je potřeba `--email` doplnit. Při chybě
nikdy nepoužívej jiné nebo staré ID účtu.

Když Microsoft 365 schránku přetěžuje nebo čtení končí timeoutem, použij
`cc_email_read.py`. Čte s malým limitem, opakuje s rostoucí pauzou a po
opakovaném selhání na 10 minut přestane schránku zatěžovat. Nic neodesílá.

```bash
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email_read.py search --from "sender@example.com" --limit 10
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email_read.py latest --limit 10
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email_read.py get-message --uid 123
python3 /home/node/.openclaw/cs-skills/smtp-email/scripts/cc_email_read.py status
```

Bez `--account-id` se účet dohledá stejně jako u `resolve_account_id.py`
(případně s `--email`). Pokud odpověď obsahuje `cooled_down: true`, neopakuj
dotaz ve smyčce; počkej, nebo použij `search --use-index`, pokud je k dispozici
lokální index zpráv.

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
