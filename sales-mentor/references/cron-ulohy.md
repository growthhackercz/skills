# Naplánované úlohy mentora (Plánovač úkolů)

Batch reporty = úlohy v CC → Plánovač úkolů → Přidat úlohu. Agent: **cso**. Model: výchozí. Běh jede v izolované session s čistým kontextem (`sessionTarget: isolated`, ověřeno u strategist cron 2026-07-24) — hlavní session se nenafukuje.

Každý izolovaný běh musí před případným GHL plánem použít helper skillu `mc-task-api` a vytvořit/reuse jeden task přiřazený `cso` se stabilním klíčem období:

- daily: `sales-mentor:mentor-daily:<YYYY-MM-DD>`
- weekly: `sales-mentor:mentor-weekly:<ISO-rok>-W<ISO-týden>`

Do `deliver.py --task-id` patří přesně ID vrácené tímto create/reuse krokem. Když vytvoření/reuse tasku selže, report může zůstat lokálním výstupem, ale žádný e-mailový plán nevznikne. Samotné ID cron jobu ani isolated session není task ID.

**Per-call scoring NENÍ cron** — je event-driven po předání aktuálního `MeetingInsight` v1 z `fireflies-meeting-intelligence`, stejné cesty z Assistanta, nebo po ručním předání přepisu. Sem patří jen dávkové reporty; žádný budoucí Fireflies router se nepředpokládá.

## 1. mentor-daily
- **Název:** `mentor-daily`
- **Plán:** `0 18 * * *`
- **Příkaz:**
  > Spusť skill sales-mentor, denní report. Nejdřív přes mc-task-api vytvoř/reuse per-period task přiřazený cso s idempotency key `sales-mentor:mentor-daily:<dnešní YYYY-MM-DD>` a uchovej jeho ID. Agreguj dnešní scorecardy (mentor_report.py --period day) a připrav manažerovi krátký přehled: počet hovorů, průměrné skóre, nejslabší kategorie, kdo potřebuje pozornost, případné červené vlajky. Pokud vzniká e-mailový plán, použij výhradně vrácené task ID, přesný e-mail příjemce a durable artefakt.
- **Popis:** Denní přehled výkonu týmu manažerovi.

## 2. mentor-weekly
- **Název:** `mentor-weekly`
- **Plán:** `0 8 * * 1`
- **Příkaz:**
  > Spusť skill sales-mentor, týdenní shrnutí. Nejdřív přes mc-task-api vytvoř/reuse per-period task přiřazený cso s idempotency key `sales-mentor:mentor-weekly:<ISO-rok>-W<ISO-týden>` a uchovej jeho ID. Agreguj scorecardy za týden (mentor_report.py --period week). Manažerovi připrav trend per obchodník + doporučenou dovednost k procvičení; každému obchodníkovi osobní shrnutí. Pokud vzniká e-mailový plán, použij výhradně vrácené task ID, přesný e-mail příjemce a durable artefakt.
- **Popis:** Týdenní trend obchodníků + osobní rozvoj.

## Poznámky k aktivaci
- Musí existovat `/documents/sales/salesDNA.md` (§6 = váhy scoringu; katalog námitek firmy v §5) a aspoň pár scorecardů (jinak report hlásí „žádný hovor").
- Reporty jsou deliverable úlohy + e-mail příjemcům z §1 — **do CRM se reporty nezapisují** (per-call pointer-poznámka je samostatná, viz krok 6 v SKILL).
- Frekvenci lze zvolnit dle velikosti týmu (malý tým: `mentor-daily` na `0 18 * * 1-5`).
