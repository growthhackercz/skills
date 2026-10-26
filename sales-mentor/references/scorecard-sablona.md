# Karta pro obchodníka — struktura

Human-readable výstup per-call (vyrábí `scorecard_write.py render_card`). **První řádek = název karty** (obchodník ho pozná mezi ostatními): `Prodejní hodnocení - obchodník <jméno> - <datum>`.

## Bloky
1. **Skóre X %** (velké, hlavní číslo) + rozpad 8 kategorií (každá v % + jedna věta s evidencí).
2. **Co se povedlo** — 3 nejsilnější momenty s citací. Vždy první, ať to není jen kritika.
3. **Jedna věc ke zlepšení** — hlavní příčina · dovednost · chování na příště · drill · metrika (nikdy víc než jedna hlavní věc, `COACHING_ENGINE`).
4. **Nejistoty** — co nešlo posoudit (typicky tonalita bez audia).
5. **⚠️ Manipulace** — jen když detekována; skóre je pak stropováno pod 60.

## Zásady
- Vykání vůči obchodníkovi (klientský tón) ve všech textech karty.
- Evidence-first: každý závěr má citaci z jeho hovoru („v pasáži o ceně jste…").
- Rozvíjející tón, ne likvidační. Cíl: obchodník ví JEDNU věc, kterou udělá zítra jinak.
- Trend zmiň, pokud stejná chyba padá opakovaně (z předchozích scorecardů téhož obchodníka).

## Kam se ukládá
`/documents/sales/scorecards/<obchodnik-slug>/<datum>-<firma-slug>-<callId>/` obsahuje JSON data, souhrnnou kartu, detail a `_manifest.json`. Scorecard vlastní **jen mentor** (single-writer) — analytik z něj čte, nepřepisuje.
