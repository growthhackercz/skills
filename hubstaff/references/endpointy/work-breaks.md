# Endpoint: `breaks` (přestávky)

Vrací **přestávky** členů — když si během sledování dali pauzu (vypnuli tracker s důvodem `break`). Hubstaff je interně volá `work_breaks`.

Volá se přes `GET /v2/organizations/{org_id}/work_breaks` s povinným časovým oknem.

CLI: `python3 hubstaff.py breaks --from --to [--member] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID přestávky. |
| `user_id` | číslo | ID člena. |
| `starts_at` | ISO 8601 | Začátek přestávky. |
| `ends_at` | ISO 8601 nebo `null` | Konec. `null` = člen přestávku ještě neukončil (nebo zapomněl). |
| `duration` | číslo | Délka přestávky v sekundách (Hubstaff počítá z `starts_at` a `ends_at`). |
| `reason` | text | Důvod, který člen u přestávky zvolil: `lunch`, `coffee`, `personal`, `other` (záleží na nastavení organizace — některé mají vlastní kategorie). |
| `notes` | text | Volitelná poznámka. |
| `shift_id` | číslo nebo `null` | Pokud byla přestávka během naplánované směny, propojení. |

## Typické použití

- **Souhrn přestávek za den / týden** — kolik celkem strávil tým mimo pracovní čas (sečíst `duration` per `user_id`).
- **Detekce nedokončených přestávek** — `ends_at: null` (člen pauzu zapnul a zapomněl ji vypnout). Hubstaff to typicky sám ukončí po nějaké době, ale chvilku to může trvat.
- **Compliance** — některé země / smlouvy vyžadují minimální délku přestávky při směně nad X hodin. Orchestrace ověří, že `sum(duration) >= min_required`.
- **Vzorce v chování** — opakované dlouhé přestávky vždy v určitou hodinu (po obědě? když je úkol nudný?) — analýza nad delším oknem.

## Příklad výstupu (zkrácený JSON)

```json
[
  {
    "id": 222,
    "user_id": 12345,
    "starts_at": "2026-05-19T11:30:00Z",
    "ends_at": "2026-05-19T12:00:00Z",
    "duration": 1800,
    "reason": "lunch",
    "notes": null,
    "shift_id": 111
  }
]
```

## Pozor

- **Přestávky NEJSOU součástí `activities`.** Pokud sečtete `activities.tracked`, dostanete čistý sledovaný čas BEZ přestávek. Pro „kolik strávil v práci celkem" musíte přidat `breaks.duration`.
- **Důvody (`reason`) jsou pre-definované Hubstaffem nebo organizací.** Pokud nesedí na to, co potřebujete (např. detail typu „doktor"), nejde to jen tak vyfiltrovat.
- **Mobilní vs. desktop tracker** ukládá přestávky podobně, ale terénní (GPS) tracker je má jinde (`shifts`-related fields). Pro hybridní týmy ověřte.
