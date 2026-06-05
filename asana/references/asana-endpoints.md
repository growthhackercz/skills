# Asana REST API — rychlá mapa

Base URL:

```text
https://app.asana.com/api/1.0
```

Auth:

```text
Authorization: Bearer $ASANA_PAT
Accept: application/json
Content-Type: application/json
```

Používané endpointy:

| Účel | Endpoint |
|---|---|
| Aktuální uživatel | `GET /users/me` |
| Workspaces | `GET /workspaces` |
| Projekty workspace | `GET /projects?workspace={gid}` |
| Úkoly projektu | `GET /projects/{project_gid}/tasks` |
| Úkoly uživatele | `GET /tasks?workspace={gid}&assignee=me` |
| Hledání úkolů | `GET /workspaces/{workspace_gid}/tasks/search?text={query}` |
| Detail úkolu | `GET /tasks/{task_gid}` |
| Vytvoření úkolu | `POST /tasks` |
| Update úkolu | `PUT /tasks/{task_gid}` |
| Komentář | `POST /tasks/{task_gid}/stories` |

Asana obvykle vrací JSON ve tvaru:

```json
{"data": {...}}
```

U list endpointů helper přidává `limit=100`. Pokud odpověď obsahuje `next_page`, zopakuj dotaz podle potřeby s offsetem.
