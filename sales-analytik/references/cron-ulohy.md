# Naplánovaná úloha analytika (Plánovač úkolů)

Analytik jede dávkově, typicky týdně. Úloha v CC → Plánovač úkolů → Přidat úlohu. Agent: **cso**. Izolovaná session (`sessionTarget: isolated`).

Každý běh před případným e-mailovým plánem použije `mc-task-api`: vytvoří/reuse task přiřazený `cso` se stabilním per-period idempotency key `sales-analytik:analytik-weekly:<ISO-rok>-W<ISO-týden>`. Do produceru předá pouze ID vrácené tímto krokem. Když task nelze vytvořit/reuse, zůstane report deliverablem bez e-mailového plánu; cron ID ani session ID nejsou task provenance.

## analytik-weekly
- **Název:** `analytik-weekly`
- **Plán:** `0 9 * * 1` (po mentor-weekly v 8:00 — pracuje nad čerstvými scorecardy týdne)
- **Příkaz:**
  > Spusť skill sales-analytik, týdenní analýza. Nejdřív přes mc-task-api vytvoř/reuse task přiřazený cso s idempotency key `sales-analytik:analytik-weekly:<ISO-rok>-W<ISO-týden>` a uchovej jeho ID. Agreguj scorecardy týdne (analytik_aggregate.py --period week). Najdi opakující se námitky, nejslabší fáze funnelu a korelaci skóre×výsledek. Sestav max 5 návrhů do playbooku (§5/§10) ke schválení majitele + krátký byznys report. E-mailový plán smí použít jen vrácené task ID, přesný e-mail příjemce, ověřenou odesílací adresu ze Sales DNA §1 a durable artefakt; bez odesílací adresy zůstane report jen deliverablem.
- **Popis:** Týdenní učení firmy — návrhy do playbooku + byznys report.

## Poznámky
- Běží **po** `mentor-weekly` jen kvůli pořadí reportů (manažer má nejdřív výkon lidí, pak učení firmy). Scorecardy vznikají průběžně per-call, ne v mentor-weekly, takže analytik má z čeho číst nezávisle na tom.
- Návrhy do playbooku jsou vždy ke schválení majitele — analytik nikdy nezapisuje do salesDNA tiše.
- Malý tým / málo hovorů: přepni na `0 9 1 * *` (měsíčně), ať je vzorek dost velký na vzorce.
- Alternativně lze pustit `--all` pro analýzu celé historie (např. čtvrtletní revize playbooku).
