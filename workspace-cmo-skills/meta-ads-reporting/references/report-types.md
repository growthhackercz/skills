# Meta Ads Report Types

Podporované modes:

| Mode | Účel | Minimální data |
|---|---|---|
| `daily-check` | Rychlá denní kontrola účtu | spend, impressions, clicks, CTR, CPC, CPM, status |
| `overview` | Souhrn kampaní/ad setů/adů | campaign/adset/ad list + insights |
| `winners` | Najít nadprůměrné kampaně/kreativy | CTR, CPC, CPA/conversions, spend |
| `bleeders` | Najít položky s nízkou efektivitou | spend, CTR, CPC, conversion signal |
| `creative-fatigue` | Detekovat únavu kreativy | frequency, CTR trend, CPM/CPC trend |
| `budget-efficiency` | Posoudit využití rozpočtu | spend, result cost, trend |
| `budget-recommendations` | Read-only návrhy přesunů rozpočtu | winners/bleeders + spend context |
| `weekly-brief` | Týdenní manažerský report | overview + winners + risks |
| `dashboard` | HTML dashboard pro rychlé čtení | summary metrics + tables |
| `anomaly-detection` | Detekovat náhlé změny | denní trend spend/CTR/CPC/CPM |

Každý mode je read-only. Pokud chybí data, vrať `insufficient_data` místo
domýšlení výkonu.
