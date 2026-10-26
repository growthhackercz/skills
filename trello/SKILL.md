---
name: trello
description: "Spravuje Trello boards, listy a karty přes bezpečný Trello REST API helper. Použij pro výpis boardů/listů/karet, detail karty, vytvoření karty, přesun, komentář nebo archivaci po potvrzení."
category: operations
status: ready
version: "1.0"
publishedAt: "2026-05-20"
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":["TRELLO_API_KEY","TRELLO_TOKEN"]},"primaryEnv":"TRELLO_TOKEN","emoji":"📋"}}
---

# Trello

Tento skill poskytuje bezpečný wrapper nad Trello REST API. Nepoužívej raw `curl` s `key=` a `token=` v URL; token by se dostal do shell historie, logů nebo chatu. Vždy volej helper:

```bash
python3 {baseDir}/scripts/trello_api.py me
```

## Konfigurace

V Control Center > Integrace > Trello nastav:

- `TRELLO_API_KEY`
- `TRELLO_TOKEN`

Helper je čte z runtime env nebo z Control Center credential store a nikdy je nevypisuje.

## Bezpečnost zápisu

- Read-only dotazy (`me`, `boards`, `lists`, `cards-*`, `card`) můžeš provést podle zadání.
- Vytvoření karty, přesun a komentář dělej jen když je cíl jasný.
- Archivace karty vyžaduje explicitní potvrzení v příkazu `--confirm yes`.
- Pokud název boardu/listu/karty není jednoznačný, vypiš kandidáty a zeptej se.
- Neposílej automaticky hromadné write operace bez plánu a potvrzení.

## Příklady

```bash
# Ověření přístupu
python3 {baseDir}/scripts/trello_api.py me

# Navigace
python3 {baseDir}/scripts/trello_api.py boards
python3 {baseDir}/scripts/trello_api.py lists <board_id>
python3 {baseDir}/scripts/trello_api.py cards-board <board_id>
python3 {baseDir}/scripts/trello_api.py cards-list <list_id>
python3 {baseDir}/scripts/trello_api.py card <card_id>

# Write operace po jasném zadání
python3 {baseDir}/scripts/trello_api.py create-card --list <list_id> --name "Název" --desc "Popis"
python3 {baseDir}/scripts/trello_api.py move-card <card_id> --list <list_id>
python3 {baseDir}/scripts/trello_api.py comment-card <card_id> --text "Komentář"
python3 {baseDir}/scripts/trello_api.py archive-card <card_id> --confirm yes
```

Detailní mapu API najdeš v `{baseDir}/references/trello-endpoints.md`.
