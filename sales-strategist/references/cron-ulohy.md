# Naplánované úlohy v Plánovači úkolů (aktivace autopilota)

Autopilot = tyto 3 úlohy v CC → Plánovač úkolů → Přidat úlohu. Agent: **cso**. Model: nechat výchozí. Heartbeat agenta se NEMĚNÍ (zůstává liveness `HEARTBEAT_OK`) — plánovaná práce patří sem, ať není rozvrh na dvou místech.

## 1. strategist-hourly

- **Název:** `strategist-hourly`
- **Plán:** `0 * * * *` (malý provoz: `0 */4 * * *` — dle Sales DNA §1)
- **Příkaz:**
  > Spusť skill sales-strategist, hodinový běh: zpracuj nové události z CRM podle prodejního playbooku a rozdej úkoly týmu. Pokud nejsou žádné události, odpověz jen „OK".
- **Popis:** Hodinová kontrola CRM — delta kontaktů, plný bounded reconciliation známého okna objednávek, posuny obchodů a schůzky.

## 2. strategist-daily

- **Název:** `strategist-daily`
- **Plán:** `0 8 * * *`
- **Příkaz:**
  > Spusť skill sales-strategist, denní běh: noční plná rekonsiliace CRM, pipeline hygiena, aging nabídek, SLA kontrola a přehled spících kontaktů. Urgentní návrhy pošli majiteli hned.
- **Popis:** Denní úklid pipeline + rekonsiliace snapshotu.

## 3. strategist-weekly

- **Název:** `strategist-weekly`
- **Plán:** `0 8 * * 1`
- **Příkaz:**
  > Spusť skill sales-strategist, týdenní běh: sestav report pro majitele — vykonaná čísla, forecast vs. cíl, návrhy ke schválení (včetně případné reaktivační vlny nebo marketové prospecting kampaně při nedostatku pipeline). Nic hromadného nespouštěj. Eskaluj neschválené návrhy z minulého týdne.
- **Popis:** Týdenní report + návrhy ke schválení.

## Poznámky k aktivaci

- Před aktivací musí existovat `/documents/sales/salesDNA.md` (→ `sales-dna-generator`) a projít onboarding checklist enginu (tagová taxonomie ve workflows, mapping obchodníků).
- První běh po aktivaci je automaticky **plný sken** (založení snapshotu, bez událostí) — může trvat jednotky minut podle velikosti báze.
- ✅ Ověřeno (2026-07-24): běh úlohy jede v **izolované session s čistým kontextem** (`sessionTarget: isolated`) — hlavní session agenta se nenafukuje, žádný pravidelný `/new` není potřeba. Běhy jsou efemérní (nejsou v seznamu sessions) — stav sleduj v Plánovači (Poslední spuštění / logy v detailu úlohy).
