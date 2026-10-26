# Interpretace událostí — event → akce → kanál

Skript vrací `events.json` se seznamem událostí. Každou událost přelož na akci podle téhle tabulky, s parametry ze Sales DNA (§ = sekce salesDNA.md). Kde Sales DNA říká jinak, Sales DNA vyhrává.

## Tři kanály akcí (podle rizika)

1. **Úkol pracantovi** (`cc_task.py`, idempotency key `cso:<skill>:<účel>:<YYYYMMDDHH>`) — výchozí kanál. Vždy subtask denní umbrelly + tag `sales-engine` + zápis do dispatch-logu (SKILL.md → Dispečink). Šablona zadání níže.
2. **Denní souhrn** (append do `.strategist-state/denni-souhrn.md`) — nízká priorita, počká na denní/týdenní zpracování.
3. **Návrh ke schválení** (report / zpráva majiteli) — POVINNÉ pro cokoli hromadného nebo měnícího playbook.

## Šablona zadání úkolu (kanál 1)

Parametry: `--parent-task-id <umbrella>` · `--assigned-to cso` · `--tag sales-engine` · priorita `medium` (SLA/eskalace `high`).

- **Title:** `<skill>: <účel> — <kontakt/deal>` (např. `assistant: příprava na jednání — Jan Novák, út 14:00`)
- **Description:**
  1. První věta: `Použij skill <slug> a <co udělat>.` — bez toho pracant skill neaktivuje.
  2. Kontext: kdo (jméno + ID kontaktu/dealu), co se stalo (událost + čas), relevantní historie jednou větou.
  3. Rozhodné hodnoty ze Sales DNA přímo v textu (lhůty, mantinely, kotvy) — pracant si svoje sekce DNA načte, ale parametry rozhodnutí piš do zadání.
  4. Očekávaný výstup: co přesně má být deliverable.

## Mapování událostí

| Událost | Akce | Kanál | Podmínky |
|---|---|---|---|
| `contact_new` | B2B + tým: úkol `sales-scout` „brief na kontakt X"; jinak souhrn. SLA hodiny běží (§7) | 1 / 2 | jen v pracovní době (§1). **Tag `sales prospector` → BEZ SLA + Scout briefy dávkově/na vyžádání** (jde o lov, ne příliv leadů). **Když jede Scout webhook → contact_new jen souhrn** (brief už dělá webhook, jinak duplicita + dvojí Apify útrata). |
| `contact_tags_added` s `produkt:*` | = NÁKUP → úkol `sales-upsell` „upsell doporučení pro kontakt X" (katalog + §11 mantinely) | 1 | respektuj „max 1 nabídka / X dní" (§11) |
| `contact_tags_added` s `zajem:*` | úkol `sales-assistant` (režim B) „ohřátý zájemce — navrhni další krok" | 1 | |
| `contact_tags_added` jiné (`sales scout`/`sales assistant`/`osloven:`/`upsell-*`/`cyklus:*`/`reaktivace:*`) | jen souhrn, ŽÁDNÁ akce — jsou to evidenční tagy vlastních skillů, ne signál | 2 | zabraňuje feedback loopu (vlastní zápisy vrátí snapshot jako tag-add) |
| `contact_tags_removed` | jen souhrn | 2 | |
| `contact_dnd_changed` (true) | souhrn + vyřaď ze všech běžících návrhů | 2 | DND je tvrdé pravidlo |
| `order_new` | = NÁKUP → jako `produkt:*` tag; navíc zkontroluj, zda má odpovídající deal → pokud ne, úkol `sales-assistant` „založ/uzavři deal k objednávce" | 1 | |
| `opp_new` | souhrn (deal už někdo založil — jen evidence do forecastu) | 2 | |
| `opp_stage_changed` | souhrn; pokud posun do fáze „nabídka" → připomeň aging pravidlo (§7) | 2 | |
| `opp_status_changed` na `won` | úkol `sales-upsell` „upsell po výhře" + gratulace v souhrnu | 1 | |
| `opp_status_changed` na `lost` | chybí důvod prohry → úkol `sales-assistant` „vyžádej důvod prohry od obchodníka" | 1 | datová hygiena (§7) |
| `meeting_upcoming` | úkol `sales-assistant` (režim A) „připrav přípravu na jednání: <kontakt, čas>" | 1 | jen schůzky s `contactId`; interní porady ignoruj |

## ⚠️ Import guard (vyhodnoť PŘED mapováním událostí)

Pokud jeden běh obsahuje **více než 50 událostí `contact_new`** → jde o hromadný import, NE příliv leadů:

1. NEspouštěj per-lead akce (žádné SLA, žádné Scout briefy, žádné upsell úkoly) pro tyto kontakty.
2. Polož majiteli jednu otázku (kanál 3): *„Nahráli jste N kontaktů — co to je? (a) bývalí zákazníci, (b) leadi se souhlasem, (c) jiné."*
3. Podle odpovědi zadej úkol otagovat (`produkt:*` / `zajem:*` + `import:<RRRR-MM-DD>`) — tím jsou **okamžitě způsobilé k reaktivaci** (importovaný seznam je z definice spící, nečeká se 180 dní). Bez deklarace vztahu kontakty do vln nesmí.

## Denní agendy (nad snapshotem, bez API)

| Agenda | Pravidlo (výchozí, přepisuje §7) | Akce |
|---|---|---|
| Spící kontakty | bez aktivity > 180 dní, bez DND, mimo karanténu `reaktivace:` | spočítej + segmentuj → NÁVRH vlny (kanál 3) |
| Pipeline hygiena | otevřený deal bez vlastníka / hodnoty / dalšího kroku | úkol Assistantovi (kanál 1, souhrnně za pipeline) |
| Stage aging | nabídka > 14 dní bez odpovědi → připomínka; > 30 dní → návrh uzavřít s důvodem | úkol Assistantovi |
| SLA | nový lead bez kontaktu > 1 h (v pracovní době) | úkol `sales-assistant` (urgent) — obchodník má lead kontaktovat; do souhrnu majiteli. Stratég nemá vlastní kanál k obchodníkovi, jde přes Assistantův GHL úkol |
| Opakovaný nákup („za cyklem") | zákazník ≥ 1,2× cyklu produktu bez nového nákupu (cykly v §11; z objednávek) | úkol **Re-activatoru** — průběžný režim připomínek (1,2–2× cyklu jemná připomínka; nad 2× = spící → vlna). NIKDY Upsellu — ten je čistě event nákupu |
| Forecast | Σ (hodnota dealu × pravděpodobnost fáze dle §8) per pipeline | do souhrnu / reportu |
| Pokrytí pipeline | forecast nebo počet kvalifikovaných leadů pod cílem ze Sales DNA §2 | pouze návrh marketové Prospector kampaně; task až po explicitním souhlasu majitele |

## Zásady

- **Seskupuj:** 12 dealů bez dalšího kroku = 1 úkol Assistantovi se seznamem, ne 12 úkolů.
- **Deduplikuj přes idempotency key** — `<účel>` MUSÍ obsahovat ID kontaktu/dealu (`cso:assistant:priprava:<contactId>:<YYYYMMDDHH>`), jinak dvě různé schůzky/dealy v téže hodině kolidují a druhá akce nevznikne.
- **Pipeline označená „mimo engine" (§8) se ignoruje celá.**
- **Nikdy neoslovuj kontakty sám** — stratég nemá žádný kanál ke kontaktům, jen k týmu a majiteli.
