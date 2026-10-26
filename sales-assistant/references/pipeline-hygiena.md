# Pipeline hygiena — typy zásahů (workflow B)

Assistant dostane **konkrétní seznam dealů** (stratég je vyjmenoval v úkolu) nebo jeden deal v manuálu. **Nikdy nerescanuje bázi.** Pro každý deal urči typ zásahu a proveď přes `ghl_assistant_push.py`.

## Typy zásahů

| Situace (z `ghl_context.py` + §7/§8) | Zásah | Kanál |
|---|---|---|
| Otevřený deal **bez dalšího kroku** | navrhni konkrétní krok s termínem (úsudek nad fází + historií) → úkol obchodníkovi | úkol |
| Nabídka **stárne** (aging §7: >14 dní bez odpovědi) | připrav follow-up **návrh** (draft) + úkol „ozvěte se" | poznámka + úkol |
| Deal zavřený jako **lost bez důvodu** | úkol obchodníkovi „doplňte důvod prohry" (datová hygiena) | úkol |
| **Objednávka bez dealu** | založ deal do správné pipeline (§8), hodnotu z objednávky — je to evidence, ne úsudek | (v1: úkol „založte deal"; automatické zakládání = až po ověření) |
| **Nový lead bez kontaktu** (SLA §7, v pracovní době) | urgentní úkol obchodníkovi/majiteli | úkol (priorita high) |

## Pravidla

- **Stage NEPŘEPISUJEŠ úsudkem** — deterministické posuny dělá cron stratéga; ty úsudkový posun jen **navrhneš** v poznámce.
- **Seskupuj:** 12 dealů = 1 běh, 1 souhrnná poznámka/odpověď, úkoly per obchodník. Ne 12 samostatných poznámek.
- **Další krok musí být konkrétní a s termínem** („zavolat do pátku a domluvit demo"), ne „ozvat se".
- Parametry aging/SLA ber ze salesDNA §7 (výchozí: nabídka 14/30 dní, SLA lead 1 h).
- Pipeline „mimo engine" (§8) ignoruj celou.
