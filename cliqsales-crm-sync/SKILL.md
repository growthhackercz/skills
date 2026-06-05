---
name: cliqsales-crm-sync
description: "Vezme MeetingInsight z fireflies-meeting-intelligence a bezpečně propíše vybrané informace do CliqSales/GoHighLevel CRM. Použij pro párování kontaktu/dealu, vytvoření CRM poznámky, tasků, tagů, custom field update a návrh stage/score změn. Default je bezpečný zápis poznámek/tasků; citlivé změny vyžadují approval."
category: integrations
status: ready
version: "2.0"
publishedAt: "2026-05-19"
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":["GHL_API_KEY","GHL_LOCATION_ID"]},"primaryEnv":"GHL_API_KEY","emoji":"🔁"}}
---


# CliqSales CRM Sync

Tento skill je CRM adapter pro meeting insighty. Bere normalizovaný
`MeetingInsight` a rozhoduje, co z něj patří do CliqSales CRM.

Nevytváří meeting analýzu od nuly. K tomu používej `fireflies-meeting-intelligence`.

## Kdy použít

Použij, když:

- existuje `MeetingInsight` a uživatel chce propsat údaje do CliqSales
- uživatel ručně napíše do chatu údaje o klientovi/kontaktu, které chce doplnit do CRM
- uživatel nahraje CSV/XML export kontaktů, poznámek nebo úkolů z jiného CRM
- `fireflies-meeting-intelligence` dokončí `MeetingInsight` a předá `CRM handoff ready`
- webhook flow pro `meeting.summarized` skončil s jistým identity/contact/deal matchem
- Fireflies meeting má být uložen ke kontaktu, firmě nebo dealu
- je potřeba vytvořit poznámku z hovoru
- je potřeba vytvořit follow-up tasky
- je potřeba přidat tagy nebo custom field hodnoty
- agent navrhuje změnu stage, score nebo ownera

## Bezpečnostní defaulty

Automaticky smíš zapsat jen nízkorizikové položky, pokud je jistý contact/deal match:

- CRM note / meeting summary ke kontaktu po skončení meetingu
- datum meetingu a nejdůležitější body z rozhovoru
- odkaz na Fireflies transcript
- účastníky meetingu
- pain points, objections, buying signals jako interní poznámku
- tasky z jasně domluvených next steps
- neinvazivní tagy, pokud už existují a jsou v allowlistu

Approval vyžaduj pro:

- změnu existujícího telefonního čísla
- změnu existujícího e-mailu
- změnu existujícího jména nebo příjmení
- změnu existující firmy / business name
- přepsání jakéhokoli existujícího identifikačního pole kontaktem z nejistého zdroje
- změnu opportunity stage
- změnu ownera
- změnu hodnoty dealu
- označení won/lost
- vytvoření nového kontaktu při nejisté identitě
- sloučení kontaktů
- odeslání zprávy/e-mailu klientovi
- vytvoření nového custom field schema

Nikdy:

- neukládej celý raw transcript do CRM
- nemaž data
- nepřepisuj důležitá pole bez approval
- neposílej email/SMS bez explicitního příkazu

## Konfigurace

Čti credentials jen z runtime env:

```text
GHL_API_KEY
GHL_LOCATION_ID
GHL_API_BASE_URL=https://services.leadconnectorhq.com
GHL_API_VERSION=2021-07-28
```

Před každým GHL requestem použij pravidla `ghl-location-guard`:

- pokud `GHL_LOCATION_ID` obsahuje dashboard URL, extrahuj čisté ID
- pokud `GHL_LOCATION_ID` začíná `loc_`, odstraň prefix a použij čisté ID bez `loc_`
- nikdy neposílej celé URL ani `loc_...` jako `locationId`
- token nikdy nevypisuj

## Doporučené scopes pro MVP

```text
locations.readonly
contacts.readonly
contacts.write
opportunities.readonly
opportunities.write
locations/customFields.readonly
locations/tags.readonly
locations/tags.write
locations/tasks.readonly
locations/tasks.write
users.readonly
```

Volitelné pro zprávy/follow-up přes conversations:

```text
conversations.readonly
conversations.write
conversations/message.readonly
conversations/message.write
```

Volitelné pro vlastní datový model v GHL objects:

```text
objects/schema.readonly
objects/record.readonly
objects/record.write
associations.readonly
associations.write
```

## Endpoint policy

CRM endpointy pro contacts/opportunities/tasks/notes/tags/custom fields musí být
ověřené proti aktuálnímu GHL API před produkčním zápisem. Pokud endpoint nebo
payload není ověřený:

1. proveď read-only test, pokud je bezpečný
2. u write akce vytvoř `dry_run` plán
3. vrať přesný seznam chybějících endpointů/scopes
4. neprováděj naslepo write request

## CSV/XML CRM import režim

Použij tento režim, když uživatel nahraje CSV nebo XML export z jiného CRM obsahující kontakty, poznámky, firmy, úkoly, tagy nebo historii komunikace.

Podporované vstupy:

- `.csv` s hlavičkou
- `.xml` export
- soubor z `/documents/...`
- menší inline CSV/XML vložené do chatu

Bezpečnostní default:

- První běh je vždy `dry_run`, pokud uživatel výslovně neřekne „proveď import/zapiš do CRM“.
- I při povoleném importu nesmíš přepsat existující neprázdné hodnoty bez explicitního schválení změn.
- Hromadný import rozděl na dávky a reportuj počet: `create`, `safe_update`, `requires_approval`, `skipped`, `errors`.
- Nikdy neimportuj raw export naslepo. Nejdřív vytvoř mapování polí a preview.

Import limity, dávkování a ochrana proti zaseknutí:

- Před zpracováním vždy spočítej odhadovaný počet záznamů.
- `0–100` záznamů: můžeš zpracovat v jednom dry-run běhu.
- `101–1000` záznamů: rozděl na dávky max. `100` záznamů a po každé dávce ulož checkpoint.
- `>1000` záznamů: nevykonávej import v jednom běhu; vytvoř import plán, navrhni dávky a vyžádej potvrzení uživatele.
- Write dávka nesmí mít víc než `50` kontaktů bez dalšího schválení.
- Při `429` nebo rate limitu respektuj `Retry-After`; pokud není dostupný, zastav dávku a ulož stav jako `rate_limited`.
- Nedělej CRM API lookup pro každý řádek naslepo. Nejprve načti/cacheuj relevantní CRM kontakty podle dostupných identifikátorů nebo použij dávkový plán.
- U XML používej streamování (`iterparse`) pro velké soubory; nečti obří XML celé do paměti, pokud má víc než 1000 záznamů.
- Po každé dávce ulož checkpoint do `checkpoint-batch-{n}.json`.
- Import musí být obnovitelný: další běh pokračuje od posledního úspěšného checkpointu, ne od začátku.
- Pokud jeden záznam selže, nezastavuj celý import; zapiš ho do `errors` a pokračuj v dávce, pokud nejde o auth/rate-limit problém.

Checkpoint formát:

```json
{
  "schema": "openclaw.crm_import_checkpoint.v1",
  "batch_index": 1,
  "processed": 100,
  "created": 0,
  "safe_updated": 0,
  "requires_approval": 0,
  "skipped": 0,
  "errors": 0,
  "next_offset": 100,
  "status": "completed|rate_limited|blocked|failed"
}
```

Postup:

1. Načti soubor. CSV čti přes Python `csv.DictReader`; XML přes `xml.etree.ElementTree`.
2. Ověř kódování a validitu. Pokud chybí hlavičky/sloupce, zastav a vrať blocker.
3. Normalizuj pole do interního tvaru:

```json
{
  "firstName": null,
  "lastName": null,
  "fullName": null,
  "email": null,
  "phone": null,
  "companyName": null,
  "notes": [],
  "tasks": [],
  "tags": [],
  "source": "crm_import"
}
```

4. Mapuj běžné varianty názvů polí:

```text
name, full_name, contact_name, jméno -> fullName
first_name, firstname, křestní -> firstName
last_name, lastname, příjmení -> lastName
email, e-mail, mail -> email
phone, telefon, mobile, mobil -> phone
company, firma, company_name, organization -> companyName
note, notes, poznámka, comment -> notes
task, úkol, follow_up -> tasks
tag, tags, štítek -> tags
```

5. Pro každý řádek/záznam najdi CRM match v pořadí:
   - přesný e-mail
   - přesný telefon
   - přesná jedinečná shoda jména a příjmení
   - firma + jméno
6. Rozhodni akci:
   - `create`: kontakt neexistuje a záznam má jméno + e-mail nebo telefon
   - `safe_update`: kontakt existuje a doplňují se jen prázdná pole / poznámka / tag
   - `requires_approval`: existující neprázdná hodnota by se změnila, je více matchů, nebo chybí silný identifikátor
   - `skipped`: nevalidní nebo nedostatečný záznam
7. Před jakýmkoli update vytvoř diff podle přísného pravidla pro existující kontakt.
8. V `dry_run` ulož import plán, ale nevolej write endpointy.
9. Pokud import přesahuje limity výše, vytvoř dávkový plán a skonči s jasným dalším krokem.
10. Ve write režimu proveď jen schválené dávky `create` a `safe_update`, které neobsahují konfliktní změny.
11. Po každém zápisu proveď readback.
12. Po každé dávce ulož checkpoint.

Výstup importu ulož jako:

```text
/documents/sales/crm-imports/{yyyy-mm-dd}-{import-slug}/import-plan.json
/documents/sales/crm-imports/{yyyy-mm-dd}-{import-slug}/import-report.md
/documents/sales/crm-imports/{yyyy-mm-dd}-{import-slug}/normalized-records.json
```

`import-plan.json` musí obsahovat:

```json
{
  "schema": "openclaw.crm_import_plan.v1",
  "mode": "dry_run|write",
  "source_file": "...",
  "counts": {
    "total": 0,
    "create": 0,
    "safe_update": 0,
    "requires_approval": 0,
    "skipped": 0,
    "errors": 0
  },
  "creates": [],
  "safe_updates": [],
  "requires_approval": [],
  "skipped": [],
  "errors": [],
  "batching": {
    "batch_size": 100,
    "write_batch_size": 50,
    "checkpoint_dir": "..."
  }
}
```

Anti-patterny:

- Nepovažuj chybějící hodnotu v importu za pokyn smazat hodnotu v CRM.
- Nepřepisuj telefon/e-mail/jméno/firmu jen proto, že import obsahuje jinou hodnotu.
- Nevytvářej kontakt pouze ze samotného jména bez e-mailu nebo telefonu, pokud to uživatel výslovně neschválí.
- Neprováděj hromadný write bez `dry_run` reportu a explicitního souhlasu.

## Manual CRM update režim

Použij tento režim, když uživatel v chatu ručně dodá informace o klientovi nebo kontaktu, které nemusí pocházet z Fireflies meetingu. Například:

```text
Pavel Novák tel +420 565 453432 email pavel.novak@seznam.cz firma ABC s.r.o.
Poznámka: zajímá se o implementaci Fireflies a CRM sync.
```

Postup:

1. Z textu extrahuj strukturovaná pole: `firstName`, `lastName`, `email`, `phone`, `companyName`, poznámku, tagy, případné úkoly.
2. Normalizuj telefon a email, ale původní hodnotu zachovej v poznámce/plánu, pokud si nejsi jistý.
3. Najdi kontakt v CRM v tomto pořadí:
   - přesný e-mail
   - přesný telefon
   - přesná jedinečná shoda jména a příjmení
   - firma + jméno
4. Pokud najdeš jednoznačný kontakt:
   - nejdřív načti existující detail kontaktu
   - vytvoř diff proti navrženým hodnotám
   - doplň prázdná pole bez dotazu
   - jakoukoli změnu existující neprázdné hodnoty dej do `requires_approval` a bez potvrzení ji nezapisuj
   - můžeš přidat CRM note s ruční poznámkou od uživatele
5. Pokud kontakt neexistuje a vstup obsahuje alespoň jméno + jeden silný údaj (`email` nebo `phone`), můžeš založit nový kontakt.
6. Pokud kontakt neexistuje a vstup obsahuje jen jméno bez emailu/telefonu, vytvoření kontaktu dej do `requires_approval`.
7. Pokud existuje více možných shod, nepokračuj v zápisu a zeptej se, který kontakt upravit.
8. Po create/update vždy proveď readback a ulož `crm-sync-result.json`.

Manual režim není povolení k hromadnému importu ani k přepisování dat. Je to řízený single-contact update/create flow.

Výstup pro manual režim:

```json
{
  "schema": "openclaw.crm_sync_result.v1",
  "mode": "manual_update|manual_create|dry_run",
  "source": "operator_chat",
  "input_summary": "Pavel Novák, phone, email...",
  "crm_target": {"contact_ids": []},
  "written": {"contact_updates": [], "notes": [], "tasks": [], "tags": []},
  "requires_approval": [],
  "skipped": [],
  "errors": []
}
```

## Vstup

Preferovaný vstup:

```text
/documents/sales/meetings/{company}/{date}-{meeting}/meeting-insight.json
```

Podporovaný inline vstup:

```json
{
  "schema": "openclaw.meeting_insight.v1",
  "source": {"provider": "fireflies", "meeting_id": "..."},
  "identity_resolution": {},
  "sales_insight": {},
  "crm_recommendations": {}
}
```

## Workflow

1. Načti `MeetingInsight`.
2. Ověř schema `openclaw.meeting_insight.v1`.
3. Ověř GHL env a sanitizuj `GHL_LOCATION_ID`.
4. Najdi CRM target:
   - nejdřív explicitní `matched_contact_ids` / `matched_deal_id`
   - potom e-mail účastníka
   - potom přesná jedinečná shoda jména a příjmení v CRM
   - potom doména firmy
   - potom fuzzy jméno + kontext
5. Pokud je přesná jedinečná shoda jména bez konfliktu, neptej se na CRM note/task zápis. Pokud je shoda nejistá, duplicitní nebo konfliktní, zastav a vyžádej potvrzení.
6. Pokud je vstup multi-company, aplikuj „Multi-company CRM sync guardrail“.
7. Připrav CRM note z meetingu podle sekce „Automatická CRM note po meetingu“: datum + nejdůležitější body + dohody + next steps.
8. Připrav tasky z next steps.
9. Připrav tagy a custom field updates.
10. Porovnej navrhované změny proti existujícím CRM hodnotám; doplnění prázdných polí odděl od přepsání existujících hodnot.
11. Rozděl změny na `auto_write` a `requires_approval` podle Contact update safety policy.
12. V dry-run režimu vypiš plán bez zápisu.
13. V write režimu proveď jen povolené a/nebo uživatelem explicitně schválené akce.
14. Po zápisu proveď readback, pokud endpoint existuje.
15. Ulož `crm-sync-result.json`.

## Webhook handoff behavior

Když tento skill spouští Fireflies webhook flow, používej konzervativní režim:

```text
meeting.transcribed handoff -> dry_run nebo skip CRM sync, pokud chybí summary
meeting.summarized handoff  -> povol CRM-safe write, pokud match confidence >= 0.85
uncertain identity          -> žádný CRM write; vytvoř approval/manual review
```

Webhook flow nikdy neposílá klientovi zprávy. Follow-up email může vzniknout jen
jako draft přes `email-draft-orchestrator`, pokud to uživatel nebo workflow
výslovně požaduje.

## Multi-company CRM sync guardrail

Pokud vstupní `MeetingInsight` obsahuje `multi_company=true`, `meeting_context.multi_company=true`, více firemních targetů, nebo `company_specific_context[]` / `ambiguous_items[]`, nepoužívej běžný single-contact zápis naslepo.

Pravidla:

1. Zapisuj pouze položky, které mají jasný CRM target: `contact_id`, jednoznačný kontakt, nebo jasně přiřazenou firmu/deal.
2. Shared meeting note může být zapsaná více potvrzeným účastníkům, ale jen pokud uživatel nebo insight jasně určuje targety.
3. Company-specific body zapisuj jen k odpovídající firmě/kontaktu.
4. `ambiguous_items` nikdy nezapisuj automaticky; dej je do `requires_approval`.
5. Pokud je meeting multi-company a není jasné, komu note patří, vytvoř dry-run plán a vyžádej potvrzení.
6. Nikdy nepřipojuj celý multi-company meeting k jednomu kontaktu jen proto, že je první v seznamu.

Výstup musí uvést:

```json
{
  "multi_company": true,
  "targeted_writes": [],
  "requires_approval": [
    {"type": "ambiguous_multi_company_item", "reason": "Cannot safely assign to one company/contact"}
  ]
}
```

## Automatická CRM note po meetingu

Po každém zpracovaném Fireflies meetingu připrav CRM note pro příslušný kontakt.

Write pravidla:

- Pokud existuje jistý kontakt (`confidence >= 0.85`, e-mail, CRM contact id, nebo přesná jedinečná shoda jména bez konfliktu), CRM note může být zapsaná jako nízkorizikový write.
- Pokud kontakt není jistý, existuje více stejných jmen, nebo je rozpor v údajích, CRM note nezapisuj; vlož ji do `requires_approval` s důvodem `uncertain_contact_match` nebo `data_conflict`.
- Pokud meeting patří k dealu/opportunity a match je jistý, note může obsahovat i odkaz na deal, ale primárně se ukládá ke kontaktu.
- Nikdy do CRM note nevkládej celý raw transcript. Pouze výtah.
- Note musí obsahovat datum meetingu a nejdůležitější body.

Minimální obsah CRM note:

1. Datum meetingu
2. Název/téma meetingu
3. Účastníci
4. 3–7 nejdůležitějších bodů z rozhovoru
5. Dohody / rozhodnutí
6. Next steps / úkoly
7. Rizika nebo otevřené otázky
8. Odkaz na Fireflies transcript, pokud je dostupný

V `crm-sync-result.json` zaznamenej note plán takto:

```json
{
  "type": "note",
  "target": "contact",
  "contact_id": "contact_id",
  "would_create": true,
  "date": "YYYY-MM-DD",
  "title": "Fireflies meeting note — topic",
  "body_preview": "..."
}
```

## CRM note template

```text
Fireflies meeting note

Datum: {date}
Meeting: {title}
Kontakt / účastníci: {participants}
Fireflies: {transcript_url}

Nejdůležitější body:
- {key_point_1}
- {key_point_2}
- {key_point_3}

Dohody / rozhodnutí:
- {agreement_or_decision}

Next steps / úkoly:
- {next_step}

Rizika / otevřené otázky:
- {risk_or_open_question}

Doporučení agenta:
{recommended_next_action}
```

Note má být stručná a použitelná v CRM. Preferuj 3–7 bodů, ne dlouhý přepis.

## Contact update safety policy

Rozlišuj doplnění prázdného pole a přepsání existující hodnoty.

Pokud v přepisu hovoru chybí e-mail, telefon, firma nebo jiný údaj, ale v CRM už existuje, neber to jako rozpor a neptej se uživatele. Stávající CRM hodnotu ponech.

Pokud transcript přinese novou informaci a odpovídající CRM pole je prázdné, můžeš ji doplnit bez dotazu při jistém matchi.

Ptát se máš pouze při rozporu: CRM hodnota existuje a nová hodnota z meetingu je jiná.

Přísné pravidlo pro existující kontakt: pokud CRM kontakt už existuje, žádnou existující neprázdnou hodnotu nepřepisuj bez explicitního potvrzení uživatele. To platí pro manuální vstup, Fireflies transcript i jiné zdroje. Bez potvrzení smíš pouze doplnit pole, která jsou v CRM prázdná.

Před každým `PUT /contacts/{id}` nebo jiným update requestem vytvoř diff:

```json
{
  "contact_id": "...",
  "safe_empty_field_fills": [],
  "changes_requiring_approval": [
    {"field": "phone", "current_value": "+420111111111", "proposed_value": "+420222222222"}
  ]
}
```

Pokud `changes_requiring_approval` není prázdné a uživatel změny explicitně neschválil, update request nespouštěj.

Bez dalšího schválení můžeš připravit nebo provést jen nízkorizikové doplnění, pokud je identity match jistý (`confidence >= 0.85`) a zdroj je důvěryhodný:

- doplnit prázdné pole `phone`, `email`, `companyName`, pokud je hodnota jednoznačná
- přidat CRM note / meeting summary
- přidat existující allowlist tag
- vytvořit follow-up task z jasně domluveného next step

Vždy vyžaduj explicitní potvrzení uživatelem před změnou existující hodnoty, zejména:

- existující telefonní číslo → nové telefonní číslo
- existující e-mail → nový e-mail
- existující jméno/příjmení → jiné jméno/příjmení
- existující firma/business name → jiná firma
- změna ownera, opportunity stage, deal value, won/lost stav
- vytvoření nového kontaktu, pokud match není jistý
- merge/sloučení kontaktů

Když je navržena vážná změna, nedělej write request. Vrať ji do `requires_approval` ve tvaru:

```json
{
  "type": "contact_update",
  "risk": "high",
  "field": "email",
  "current_value": "old@example.com",
  "proposed_value": "new@example.com",
  "reason": "Fireflies transcript / user-provided data suggests a different email",
  "requires_user_confirmation": true
}
```

Pokud uživatel změnu schválí, proveď jen schválená pole a po zápisu udělej readback.

Bez schválení se změna existující hodnoty považuje za blocker, ne za automatický write.

## Contact create/update payload pravidla

Při vytváření nebo aktualizaci kontaktu používej čistá CRM pole, ne technické testovací hodnoty:

```json
{
  "locationId": "<clean location id bez loc_>",
  "firstName": "Jan",
  "lastName": "Novák",
  "email": "jan.novak@example.com",
  "phone": "+420777000999",
  "companyName": "Firma s.r.o.",
  "source": "Fireflies meeting",
  "tags": ["fireflies"]
}
```

Pravidla:

- Neposílej pole `name` jako náhradu za `firstName`/`lastName`; GHL UI a list endpoint ho nemusí použít konzistentně.
- Do `lastName` nedávej timestamp, meeting id ani technickou poznámku. Technické údaje patří do `source`, tagu nebo CRM note.
- Pokud nemáš jistý e-mail nebo telefon, nezakládej kontakt automaticky; dej návrh do `requires_approval`.
- Po create/update proveď readback. Detail endpoint se může aktualizovat hned, zatímco seznam kontaktů může být krátce eventual-consistent; ověř i list po krátké prodlevě, pokud řešíš UI zobrazení.
- Testovací kontakty označ tagem `openclaw-scope-test` a nepoužívej je jako důkaz správného business matchingu.

## Task mapping

Každý `sales_insight.tasks[]` mapuj na CRM task:

```json
{
  "title": "Poslat nabídku do pátku",
  "description": "Vzniklo z Fireflies meetingu {meeting_id}. Kontext: ...",
  "dueDate": "optional",
  "contactId": "optional",
  "opportunityId": "optional",
  "assignedTo": "optional"
}
```

Nejasné tasky nedávej do CRM automaticky. Ulož je do `requires_approval`.

## Duplicate-name protection

Přesná shoda jména je použitelná jen pokud je v CRM jednoznačná.

Před použitím přesné shody jména:

1. Vyhledej kontakty podle normalizovaného `firstName + lastName`.
2. Pokud je nalezen přesně jeden kontakt a neexistuje konflikt v e-mailu/telefonu/firmě, můžeš ho použít pro nízkorizikové akce.
3. Pokud jsou nalezeny dva nebo více kontaktů se stejným jménem, zastav auto-write a vrať `requires_approval` se seznamem kandidátů.
4. Pokud je jméno stejné, ale e-mail/telefon/firma se liší, považuj to za konflikt a vyžádej potvrzení.
5. Pokud import nebo transcript neobsahuje e-mail/telefon a v CRM existuje více kontaktů se stejným jménem, nikdy nevybírej první kontakt automaticky.

`requires_approval` příklad:

```json
{
  "type": "duplicate_name_match",
  "risk": "high",
  "normalized_name": "pavel novak",
  "candidates": [
    {"contact_id": "...", "email": "pavel@example.com", "phone": "+420...", "companyName": "..."}
  ],
  "question": "Kterého Pavla Nováka mám upravit?"
}
```

## Matching pravidla

Confidence prahy:

```text
>= 0.85  auto match povolený pro note/task
0.60-0.84 vyžádej potvrzení před CRM zápisem, pokud není přesná shoda jména
< 0.60   nepropojuj; nabídni možné shody nebo založení nového kontaktu
```

Přesná shoda jména/prijmení s jedním CRM kontaktem je pro nízkorizikové akce dostačující, pokud neexistuje konflikt v e-mailu/telefonu/firmě:

- CRM note k meetingu můžeš zapsat bez dotazu.
- Follow-up task k tomuto kontaktu můžeš připravit/zapsat podle běžných bezpečnostních pravidel.
- Nezakládej nový kontakt, pokud už přesná shoda existuje.

E-mail nebo existující CRM ID je stále silnější signál než jméno. Pokud je přesná shoda jména, ale existuje více kontaktů se stejným jménem, nebo je rozpor v e-mailu/telefonu/firmě, vyžádej potvrzení.

## Výstup

Po dry-run nebo zápisu vytvoř:

```json
{
  "schema": "openclaw.crm_sync_result.v1",
  "source_meeting_id": "fireflies id",
  "mode": "dry_run|write",
  "crm_target": {
    "contact_ids": [],
    "opportunity_id": null,
    "company_or_business_id": null
  },
  "planned_auto_write": [],
  "written": {
    "notes": [],
    "tasks": [],
    "tags": [],
    "custom_fields": []
  },
  "requires_approval": [],
  "approved_changes": [],
  "skipped": [],
  "errors": [],
  "readback": {}
}
```

Ulož do:

```text
/documents/sales/meetings/{company-or-unknown}/{yyyy-mm-dd}-{meeting-slug}/crm-sync-result.json
```

## Integrace

Uses:

- `fireflies-meeting-intelligence` výstup `MeetingInsight`
- `ghl-location-guard`
- GHL/CliqSales CRM API
- `mc-task-api` pro deliverables a approval tasky
- `email-draft-orchestrator` pro follow-up email draft, pokud uživatel chce follow-up

Used by:

- sales agents
- CSO workflow
- manual CRM update z operátorského chatu
- CSV/XML CRM import z uživatelských souborů
- Fireflies post-processing automation
- account memory workflow

## Quality checklist

- [ ] Žádný token není v chatu ani výstupu.
- [ ] `GHL_LOCATION_ID` je čisté ID.
- [ ] Meeting target byl nalezen s confidence nebo potvrzen člověkem.
- [ ] Přesná jedinečná shoda jména bez datového konfliktu nevyžaduje dotaz pro nízkorizikový CRM note/task zápis.
- [ ] Duplicitní jména nikdy nevybírají první kontakt automaticky; musí jít do `requires_approval`.
- [ ] Chybějící údaj v transcriptu nepřepisuje existující CRM hodnotu a nevyvolává approval.
- [ ] Raw transcript nebyl uložen do CRM.
- [ ] CRM note obsahuje datum meetingu a 3–7 nejdůležitějších bodů, ne celý transcript.
- [ ] Multi-company input zapisuje jen jasně targetované položky; ambiguous položky jsou v approval.
- [ ] Citlivé změny jsou v approval queue.
- [ ] Existující telefon/e-mail/jméno/firma nejsou přepsané bez explicitního schválení uživatelem.
- [ ] Před update requestem existuje diff a všechny změny existujících hodnot jsou buď schválené, nebo v `requires_approval`.
- [ ] Write akce má výsledek nebo přesnou chybu.
- [ ] Manual vstup z chatu má buď jednoznačný target, nebo approval dotaz.
- [ ] CSV/XML import má dry-run plán, mapování polí a konfliktní změny v `requires_approval`.
- [ ] Import nad 100 záznamů je dávkovaný a má checkpointy; nad 1000 záznamů vyžaduje potvrzený batch plán.
- [ ] Rate limit / 429 nezpůsobí tight loop; dávka se zastaví a uloží stav.
- [ ] Batch pokračuje bezpečně a nepředstírá plný úspěch při částečném selhání.
