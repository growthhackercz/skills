# Endpoint: `screenshots` (metadata snímků obrazovky)

Vrací **metadata** o snímcích obrazovky, které Hubstaff automaticky pořídil během sledovaného času.

**Pozor — skill obrázky NESTAHUJE.** Vrací jen informace: kdy snímek vznikl, ID, čí byl, URL na obrázek hostovaný v Hubstaffu. Pokud klient chce snímek vidět, otevře URL v prohlížeči (přihlášený do Hubstaffu).

Volá se přes `GET /v2/organizations/{org_id}/screenshots` s povinným časovým oknem.

CLI: `python3 hubstaff.py screenshots --from --to [--member] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID snímku. |
| `user_id` | číslo | ID člena, kterému snímek patří. |
| `time_slot` | ISO 8601 | Začátek 10minutového bloku, ve kterém snímek vznikl. |
| `recorded_at` | ISO 8601 | Přesný čas pořízení snímku v rámci bloku. |
| `url` | text (URL) | Odkaz na obrázek v Hubstaffu (vyžaduje přihlášení). |
| `thumb_url` | text (URL) | Odkaz na náhled (menší verze). |
| `screen` | číslo | Pokud má člen víc monitorů, index obrazovky (0 = primární). |
| `created_at` | ISO 8601 | Čas, kdy snímek dorazil na Hubstaff server. |
| `deleted_at` | ISO 8601 nebo `null` | Pokud byl snímek smazán (členem nebo manažerem), datum smazání. Smazané snímky nejsou v `url` dostupné. |

## Politika pořizování

Hubstaff pořizuje až **3 snímky za 10 minut** sledovaného času, pro každou aktivní obrazovku. To je nastavitelné v Hubstaff UI v organizaci (per člen / per role) — některé organizace mají snímky vypnuté úplně, jiné mají interval 1 min. Co skill dostane závisí na konfiguraci klienta v Hubstaffu, nikoli na skillu samotném.

## Typické použití

- **Audit aktivity v konkrétním čase** — uživatel chce vidět, co Honza dělal v úterý mezi 14:00 a 14:30 → orchestrace vyfiltruje `time_slot` a vrátí URL klientovi.
- **Počty snímků jako proxy pro intenzitu sledování** — kolik snímků člen měl za týden (vyšší počet ≠ víc pracoval, ale ≈ méně přestávek mimo PC).
- **Detekce smazaných snímků** — `deleted_at != null` může indikovat, že člen po sobě „zametá stopy" (Hubstaff smazání povoluje jen některým rolím — pro audit důležité).

## Příklad výstupu (zkrácený JSON)

```json
[
  {
    "id": 555666777,
    "user_id": 12345,
    "time_slot": "2026-05-19T08:10:00Z",
    "recorded_at": "2026-05-19T08:13:42Z",
    "url": "https://app.hubstaff.com/screenshots/555666777",
    "thumb_url": "https://app.hubstaff.com/screenshots/555666777/thumb",
    "screen": 0,
    "created_at": "2026-05-19T08:14:00Z",
    "deleted_at": null
  }
]
```

## Pozor

- **GDPR / soukromí:** snímky obsahují to, co měl člen na obrazovce — můžou tam být soukromé zprávy, hesla zobrazená v plain textu, citlivé klientské údaje. Skill záměrně **nestahuje obrázky** na disk agenta, aby nevytvářel kopii citlivých dat mimo Hubstaff. Pokud klient chce snímek vidět, ať si otevře URL v Hubstaffu (autentizovaně).
- **Plán Hubstaffu:** snímky jsou typicky součástí placených plánů. Free / nejlevnější plány je nemusí mít.
- **Pokud snímek `url` vrací 404,** byl smazán nebo Hubstaff přesunul úložiště. V `deleted_at` to bývá vidět.
