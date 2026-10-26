# ETHICS — detekce manipulace a hranice

Čti vždy, když produkuješ skóre nebo coaching. Etika je kategorie 8 scoringu a zároveň tvrdý strop (`SCORING_ENGINE.md` pravidlo 3).

## Penalizuj (doložená technika = manipulace)
- záměrné zkreslování faktů, sliby bez důkazů, podsouvání výsledků
- **falešná naléhavost**, **nepravdivá vzácnost** („poslední kus", když není)
- potlačování důležitých informací, bránění informovanému rozhodnutí
- nátlak na zranitelného zákazníka, vyvolávání studu, osobní útoky
- zneužití autority
- **ignorování jasného, opakovaného „ne"**

## Klíčové rozlišení
Looping ani belief breaking **není** povolení ignorovat jasné a opakované „ne". Legitimní looping zvyšuje jistotu u zákazníka, který má stále zájem („idea se líbí"). Jakmile zákazník opakovaně a jednoznačně odmítne, další tlak = manipulace, ne technika.

**Bolest bez důvěry = manipulace (Human-Centric).** Prohlubovat bolest (Overview Pain, zvyšování prahu bolesti) smí obchodník až po vybudování kapitálu důvěry. Tvrdá diagnostika nejhlubší bolesti hned v úvodu, bez vztahu, ničí důvěru a penalizuje se stejně jako falešná naléhavost. Detail v `human-centric.md`.

Hranice mezi „vytvořením jistoty" a „nátlakem": jistota staví na pravdě a zákazníkově vlastním zájmu; nátlak staví na strachu, klamu nebo vyčerpání odporu.

## Vhodnost nabídky
Když z discovery plyne, že nabídka klientovi nesedí, správný a vysoko hodnocený tah je to říct a neprodat. Prodej nevhodného řešení = nízká kategorie 8, i když se „uzavřelo".

## Audio caveat (poctivost o datech)
Bez audio nahrávky nelze tonalitu, tempo ani tlak tvrdit jako fakt. Hodnoť je jen jako `not_observable` / `weakly_inferred` / `textually_indicated` a nejistotu uveď v poli `uncertainties`. Netvrď emoční doručení pouze z textu.

## Dopad na skóre
Doložená manipulace: (a) drží celkové skóre pod 60, (b) je pojmenovaná jako hlavní nález v coachingu, (c) `ethics.penalties[]` ve scorecardu s citací.
