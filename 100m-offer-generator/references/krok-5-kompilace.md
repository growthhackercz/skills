# Krok 5 — Kompilace a finální kontrola

Cíl: vybrat název nabídky a sešít schválený obsah do kompatibilní
devítisekční Product DNA bez WIP tvrzení.

## Název nabídky

Připrav 8–12 variant z různých úhlů. Kombinuj zákazníka, výsledek, skutečný
mechanismus, případný doložený čas a vhodný formát. U každé varianty uveď krátký
důvod a riziko; první je doporučená.

Název musí být vyslovitelný, zapamatovatelný, srozumitelný a obhajitelný.
Časový nebo výsledkový slib smí obsahovat pouze doložený údaj.

## Silná čísla

Do aktivního souboru vyber jen doložená čísla s kontextem a zdrojem. Kandidáti
označení `[OVĚŘ S KLIENTEM]` zůstávají ve WIP, nikoli v aktivní Product DNA.

## Povinná QA před finálním schválením

- přesných devět kanonických H2 a `CHYBĚJÍCÍ INFORMACE`, žádné další H2;
- žádný `schemaVersion` ani paralelní offer dokument;
- doložená původní fakta zůstala zachována;
- mechanismus popisuje reálný proces;
- žádná pseudověda, falešná urgence ani uměle nafouknutá hodnota;
- žádný marker `[OVĚŘ S KLIENTEM]` nebo `[ROZPRACOVÁNO]` ve finální verzi;
- ceny, garance, reference, metriky, zdravotní tvrzení a urgence jsou doložené
  a výslovně potvrzené, nebo z finálního textu odstraněné;
- chybějící nekritické informace jsou popsány jako otázky, ne jako kandidátní
  tvrzení;
- text odpovídá jazyku klienta, top-level kanonické H2 zůstávají beze změny.

## Finální zastávka

Předlož uživateli celý marker-free obsah a stručný přehled změn oproti aktivní
Product DNA. Explicitně se zeptej na schválení přesných bytes a potvrzení
kritických tvrzení. Teprve poté použij workflow helper k publish.
