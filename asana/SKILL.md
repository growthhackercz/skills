---
name: asana
description: "Spravuje Asanu přes Asana REST API pomocí bezpečného helperu. Použij pro workspaces, projekty, úkoly, hledání, komentáře, vytvoření úkolu, update nebo dokončení úkolu."
category: operations
status: ready
version: "1.0"
publishedAt: "2026-05-20"
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":["ASANA_PAT"]},"primaryEnv":"ASANA_PAT","emoji":"✅"}}
---

# Asana

Tento skill dává agentovi řízený přístup k Asana REST API. Používej ho pro projektovou operativu: výpis workspace, projektů a úkolů, hledání úkolů, doplnění komentáře, vytvoření úkolu nebo změnu jasně určeného úkolu.

## Konfigurace

Asana PAT se nastavuje v Control Center > Integrace > Asana jako `ASANA_PAT`.

Token nikdy neposílej v argumentech příkazu, URL, chatu, deliverable ani do souborů. Nepoužívej vlastní `curl` s tokenem. Vždy volej helper:

```bash
python3 {baseDir}/scripts/asana_api.py me
```

Helper čte `ASANA_PAT` z runtime env nebo z Control Center credential store. Lokální config `~/.openclaw/asana/config.json` smí obsahovat jen non-secret default workspace.

## Bezpečnost zápisu

- Read-only dotazy můžeš provádět podle zadání.
- Vytvoření úkolu, komentář, přesun, update nebo dokončení úkolu dělej jen když je záměr uživatele explicitní.
- Pokud existuje víc možných úkolů/projektů, nejdřív vypiš kandidáty a zeptej se.
- Nepoužívej první nalezenou shodu jako cíl write operace.
- Před hromadnou změnou vytvoř plán a vyžádej potvrzení.

## Příkazy

```bash
# Ověření přístupu
python3 {baseDir}/scripts/asana_api.py me

# Workspaces a projekty
python3 {baseDir}/scripts/asana_api.py workspaces
python3 {baseDir}/scripts/asana_api.py projects --workspace <workspace_gid>
python3 {baseDir}/scripts/asana_api.py set-default-workspace --workspace <workspace_gid>

# Úkoly
python3 {baseDir}/scripts/asana_api.py tasks-in-project --project <project_gid>
python3 {baseDir}/scripts/asana_api.py tasks-assigned --workspace <workspace_gid> --assignee me
python3 {baseDir}/scripts/asana_api.py search-tasks --workspace <workspace_gid> --text "část názvu"
python3 {baseDir}/scripts/asana_api.py task <task_gid>

# Write operace po jasném zadání
python3 {baseDir}/scripts/asana_api.py create-task --workspace <workspace_gid> --name "Název" --notes "Popis" --project <project_gid>
python3 {baseDir}/scripts/asana_api.py update-task <task_gid> --name "Nový název"
python3 {baseDir}/scripts/asana_api.py comment <task_gid> --text "Komentář"
python3 {baseDir}/scripts/asana_api.py complete-task <task_gid>
```

Detailní mapu API najdeš v `{baseDir}/references/asana-endpoints.md`.
