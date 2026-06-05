# Endpoint: `activities` (aktivita v 10-min blocích)

Klíčový endpoint pro monitorování zaměstnanců. Vrací jednotlivé **10minutové bloky sledovaného času** — pro každý blok víte, kdo sledoval, na čem pracoval (projekt + úkol) a jaká byla aktivita (procenta klávesnice a myši).

Volá se přes `GET /v2/organizations/{org_id}/activities` s povinným časovým oknem.

CLI: `python3 hubstaff.py activities --from --to [--member] [--project] [--format ...]`

## Význam polí

| Pole | Typ | Popis |
|---|---|---|
| `id` | číslo | ID záznamu aktivity. |
| `user_id` | číslo | ID člena, kterému aktivita patří. Propojte se jménem přes `members`. |
| `project_id` | číslo | ID projektu, na kterém se pracovalo. |
| `task_id` | číslo nebo `null` | ID úkolu pod projektem (pokud byl zvolen). |
| `time_slot` | objekt | Časový blok: `start` (ISO 8601 UTC) a `stop` (ISO 8601 UTC). Hubstaff blok ukládá jako 10minutový interval. |
| `tracked` | číslo | Kolik sekund člen v rámci bloku skutečně **sledoval** (max 600 = 10 min). Pokud blok začal v polovině 10minutového okna, bude `tracked` menší. |
| `keyboard` | číslo | Počet stisků kláves v bloku. |
| `mouse` | číslo | Počet pohybů / kliků myši v bloku. |
| `overall` | číslo | Souhrnný počet vstupů (klávesnice + myš), použito pro výpočet `activity`. |
| `activity` | číslo (0–100) | **Procento aktivity** v bloku. Hubstaff počítá: kolik 10sekundových intervalů z bloku obsahovalo aspoň jeden vstup z klávesnice nebo myši. 100 % = vstup byl v každém 10s intervalu; 0 % = nečinnost. |
| `paid` | bool | Zda je čas placený (vázané na `pay_rate` člena). |
| `billable` | bool | Zda je čas fakturovatelný klientovi. |
| `created_at` / `updated_at` | ISO 8601 | Čas vzniku záznamu na serveru. |

## Jak se počítá `activity` v procentech

Hubstaff každých **10 sekund** zkontroluje, jestli během toho intervalu člen použil klávesnici nebo myš. Pokud ano, ten interval se počítá jako „aktivní". 10minutový blok obsahuje 60 takových intervalů. Aktivita v procentech = aktivní intervaly / 60.

Praktický důsledek:
- **Aktivita 100 %** = člen se klávesnice / myši dotkl alespoň jednou každých 10 s po celých 10 min. Reálné jen u tvrdého psaní.
- **Aktivita 60–80 %** = soustředěná práce s občasným zaváháním (čtení, čekání). Zdravá normála pro většinu kancelářské práce.
- **Aktivita 30–50 %** = telefonáty, meetingy, čtení dokumentů. Není to nutně problém, ale stojí za diskusi, jestli má pro takovou práci smysl mít zapnutý tracker.
- **Aktivita pod 30 %** = člen má tracker zapnutý, ale nepracuje aktivně (na callu, mimo počítač, pauza bez vypnutí trackeru).

**Důležité:** nízká aktivita ≠ nepracoval. Návrhář dělající rešerši v knize, programátor přemýšlející nad bugem, prodejce na telefonu — všichni mají nízkou aktivitu, ale pracují. Aktivita je signál k otázce, ne k závěru.

## Typické použití

- **Souhrn hodin** — orchestrace sečte `tracked` napříč záznamy (děleno 3600 pro hodiny).
- **Průměrná aktivita člena za den / týden** — váhový průměr `activity` vážený přes `tracked` (kratší bloky mají menší váhu).
- **Per-projekt summary** — agregace `tracked` per `project_id`.
- **Detekce, kdy člen pracoval** — kombinace `time_slot.start` napříč záznamy ukáže, ve kterých hodinách reálně sledoval.

## Příklad výstupu (zkrácený JSON)

```json
[
  {
    "id": 987654321,
    "user_id": 12345,
    "project_id": 4567,
    "task_id": null,
    "time_slot": {
      "start": "2026-05-19T08:10:00Z",
      "stop": "2026-05-19T08:20:00Z"
    },
    "tracked": 600,
    "keyboard": 432,
    "mouse": 215,
    "overall": 647,
    "activity": 78,
    "paid": true,
    "billable": true,
    "created_at": "2026-05-19T08:20:05Z",
    "updated_at": "2026-05-19T08:20:05Z"
  }
]
```

## Pozor

- **Manuálně zadaný čas** (`manual time entries` v Hubstaffu) v tomto endpointu **není** — `activities` vrací jen sledované bloky. Pro plnou bilanci hodin sčítejte i `time_entries` s `time_type: manual`.
- Při dlouhých oknech (měsíc+) může být odpověď velká (tisíce záznamů). Klient stránkuje automaticky, ale překročíte-li `--max-pages`, zužte období nebo filtrujte.
- `activity` neukazuje **kvalitu** práce — jen aktivitu vstupů. Nikdy z ní samotné nečiňte personální rozhodnutí.
