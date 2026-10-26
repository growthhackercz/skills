# Návrh do playbooku — formát ke schválení

Analytik nikdy nezapisuje do salesDNA sám. Sestaví NÁVRH a předloží majiteli. Po schválení se teprve zapíše do §5/§10 (single-writer playbooku = analytik po schválení).

## Struktura návrhu
Pro každý bod:
- **Kam:** §5 (odpověď na námitku) / §10 (ověřený poznatek) / §4 (úprava metodiky)
- **Důkaz:** číslo z agregátu („námitka `price` 12× za měsíc, průměrné skóre kategorie námitek 48 %")
- **Návrh textu:** přesně to, co se má do playbooku doplnit (hotová věta, ne popis)
- **Očekávaný dopad:** co se tím zlepší

Příklad:
```
Kam: §5 (Společné námitky)
Důkaz: „Je to drahé" padlo 12× / měsíc, jednotná odpověď v playbooku chybí,
        skóre kategorie námitek u těchto hovorů prům. 44 %.
Návrh textu: „Je to drahé" → „Rozumím. Když to srovnáme s tím, co vás stojí
        nechat to tak, jak to je [náklad nečinnosti z discovery] — vyjde
        vám to jako investice, nebo jako výdaj?" (Value Equation: vrať se k
        vyčíslenému dopadu, ne k obhajobě ceny.)
Dopad: sjednocená odpověď na nejčastější námitku → vyšší skóre kategorie námitek.
```

## Zásady
- Návrhy seřaď dle četnosti/dopadu (nejčastější problém první).
- Max ~5 návrhů za běh — víc majitel neschválí a ztratí to sílu.
- Vykání ve všech textech, které půjdou do playbooku (čte je pak celý tým i AI agenti).
- Nepiš návrh z jednoho hovoru. Vzorek < 5 → označ „předběžné, sbíráme dál".
- Po schválení: zapiš do salesDNA §5/§10, přidej datum a „zdroj: analytik <období>".
