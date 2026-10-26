# Trello REST API — rychlá mapa

Base URL:

```text
https://api.trello.com/1
```

Trello používá `key` a `token` v query parametrech. Agent je nikdy neskládá ručně v chatu ani v shellu. Helper `scripts/trello_api.py` je přidá interně a chybové zprávy vypisují jen cestu endpointu bez query stringu.

Používané endpointy:

| Účel | Endpoint |
|---|---|
| Aktuální uživatel | `GET /members/me` |
| Boardy | `GET /members/me/boards` |
| Listy boardu | `GET /boards/{boardId}/lists` |
| Karty boardu | `GET /boards/{boardId}/cards` |
| Karty listu | `GET /lists/{listId}/cards` |
| Detail karty | `GET /cards/{cardId}` |
| Vytvoření karty | `POST /cards` |
| Přesun karty | `PUT /cards/{cardId}` s `idList` |
| Komentář | `POST /cards/{cardId}/actions/comments` |
| Archivace | `PUT /cards/{cardId}` s `closed=true` |

Rate limity Trella jsou přibližně 300 requestů / 10 s na API key a 100 requestů / 10 s na token. U větších boardů preferuj jeden list/board dotaz a lokální filtrování.
