# Sekce „Upsell, cross-sell a katalog" (salesDNA §11) — formát a bootstrap

Kurátorská pravidla doporučování žijí jako **POSLEDNÍ sekce salesDNA** (`/documents/sales/salesDNA.md`, §11) — žádný samostatný soubor. Skript `upsell_recommend.py` sekci parsuje a dává jí **přednost před evidencí** z objednávek. Se synchronizací AI Data Centra jde salesDNA do LLM wiki, takže bundly a flagshipy vidí celý AI tým.

Kompletní vzor sekce je v šabloně salesDNA (skill sales-dna-generator, `references/salesdna-sablona.md`). Tady je kontrakt pro parser a bootstrap.

## Formát (skript ho vyžaduje)

- Sekce se pozná podle nadpisu `## 11. Upsell…` (slovo „Upsell" v nadpisu ## sekce).
- Podsekce s tabulkami — názvy `###` musí začínat PŘESNĚ takto:
  - `### Flagship produkty` — sloupce: Skupina | Produkt | Kdy nabízet
  - `### Bundly` — sloupce: Bundle | Skupiny (čárkami) | Poznámka
  - `### Přibité páry…` — sloupce: Koupil | Nabídni | Poznámka
  - `### Upgrade cesty…` — sloupce: Ze skupiny | Na skupinu | Podmínka
  - `### Nikdy nenabízet` — sloupce: Ke skupině | Nenabízet | Důvod
- Podsekce `### Mantinely a sekvence`, `### Feed` a `### Opakovaný nákup…` jsou volný text — čte je agent, skript je ignoruje.
- Klíč = **skupina produktů** (item_group z feedu; u služeb slug z productDNA). `*` = platí pro vše. Řádky začínající `<` (vzor šablony) skript přeskakuje.
- Neznámý kód skupiny hlásí skript v `rules_unknown_groups` (překlep) — po každé úpravě zkontroluj výstup.
- Změny vždy schvaluje majitel; zapisuje je agent (single writer salesDNA pravidel upsellu).

## Priorita vrstev v doporučení

`Nikdy nenabízet` filtruje vše → **přibitý pár → bundle (doplní chybějící kousky) → upgrade cesta → evidence (co-purchase) → flagship**. Upgrade cesty jsou jediný povolený „upsell" (dražší varianta téhož) — cokoli mimo ně judge blokuje.

## Bootstrap při aktivaci (sekce se nepíše ručně)

1. Spusť `upsell_recommend.py --mine` → top páry z reálných objednávek + bestsellery.
2. Navrhni vyplnění §11: bestsellery s vysokou marží → kandidáti flagship; nejsilnější páry → Přibité páry; skupiny kupované v jedné objednávce → kandidáti bundlů; spotřební zboží s větším balením → Upgrade cesty.
3. Majitel projde a schválí (zážitek: „AI mi z mých objednávek napsala pravidla mého sortimentu"). S nevyplněnými tabulkami jede skill čistě na evidenci — pravidla jsou vylepšení, ne podmínka.
4. Průběžně: páry 2× blokované judgem navrhuj (po schválení) do `Nikdy nenabízet`; ověřené vítězné páry do `Přibité páry`.
