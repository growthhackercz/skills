# Jak číst agregát — signál vs. šum

Analytik hledá **vzorce**, ne jednotlivosti. Cíl: z opakování udělat pravidlo do playbooku.

## Co je signál
- Námitka nebo příčina ztráty, která se opakuje **napříč obchodníky** (ne jen u jednoho — to je práce Mentora).
- Fáze funnelu trvale slabá napříč týmem (např. closing < 50 % u většiny hovorů).
- Konzistentní rozdíl mezi hovory s vysokým a nízkým skóre (co nejlepší dělají jinak).
- Korelace: nízké skóre v kategorii ↔ vyšší podíl `lost`.

## Co je šum (nevyvozuj z toho pravidlo)
- Jednorázová námitka u jednoho hovoru.
- Vzorek < ~5 hovorů — uveď jako „předběžný signál, malý vzorek", ne jako závěr.
- Výkyv jednoho obchodníka (patří Mentorovi, ne do playbooku).

## Postup interpretace
1. Seřaď opakující se námitky podle četnosti → top 3 jsou kandidáti do §5 (odpověď do playbooku).
2. Najdi nejslabší fázi funnelu → kandidát do §4 (metodika) nebo §10 (poznatek).
3. Porovnej nejlepší vs. slabší hovory → co odlišuje úspěch = kandidát do §10.
4. Každý návrh opři o číslo („námitka ceny 12×, dnes bez jednotné odpovědi").

## Hranice
- Analytik **nepíše do salesDNA** — jen návrh ke schválení majitele.
- Nehodnotí obchodníka jménem (to Mentor). Když narazíš na osobní vzorec, předej Mentorovi, nedávej do playbooku.
- Slovník (typy námitek, fáze, failure patterns) ber z `cliqsales-closing-system/TAXONOMY.md`, ať jsou data napříč obdobími porovnatelná.
