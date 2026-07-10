# Brand styl pro generované obrázky (sdílený postup)

Jednotný recept, jak z brand podkladů klienta vyrobit **styl blok do generovacího promptu**. Stejný postup používají i další image skilly (social-post-writer, brand-image-generator) — drž se ho, ať fleet negeneruje brand v sedmi odstínech.

## 1) Načti brand podklady (v tomto pořadí, co existuje)

| Soubor | Co si vzít |
|---|---|
| `/documents/brand/DESIGN.md` | HEX barvy (primární/sekundární/akcent/pozadí), fonty, gradient, radius, styl ilustrací |
| `/documents/brand/brandDNA.md` | nálada/tonalita značky (prémiová · hravá · technická…), slovník |
| `/documents/brand/brand-board.png` | vizuální reference (podívej se — kompozice, sytost, míra minimalismu) |

Nic z toho neexistuje → generuj neutrálně kvalitně (čistá kompozice, přirozené světlo) a v manifestu poznamenej `"brandStyle": "none"`.

## 2) Slož STYL BLOK (připoj na konec promptu)

```
Brand style: color palette {HEX primární} (dominant), {HEX akcent} (accents),
{HEX pozadí} background tones. Mood: {nálada z brandDNA — např. premium, clean,
modern tech}. {Styl z DESIGN.md — např. soft gradients cyan-to-mint, rounded
shapes, generous negative space}. Consistent with the brand's visual identity.
```

Pravidla:
- Barvy VŽDY jako HEX z DESIGN.md, ne názvy („modrá" ne).
- Nálada 2–4 slova z brandDNA, žádné eseje.
- U fotorealistických námětů barvy aplikuj na prostředí/objekty/světlo (ne jako filtr přes celou fotku).

## 3) Kdy je brand styl POVINNÝ vs. kdy stock stačí

| Použití | Brand styl |
|---|---|
| hero článku, OG karta, cokoli s textem/grafikou | **povinný** (generovat se styl blokem) |
| branded koncept / abstrakce / produkt | **povinný** |
| ilustrační inline foto (lidé, místa, situace) | netřeba — autenticita > paleta; stock OK |

## 4) Text na obrázku (OG karty, citáty, statistiky)

- Generuj přes `image_generate` (GPT Image 2 text umí) — text uveď v promptu PŘESNĚ a v uvozovkách, česky s diakritikou, a přikaž „exactly as written, correct Czech diacritics".
- Krátce: titulek max ~8 slov na OG kartě. Font popiš („bold modern sans-serif") — negeneruj název fontu z DESIGN.md doslova, modely ho neznají.
- Vždy zkontroluj výsledek — překlep v textu = regeneruj (1 retry, pak zjednoduš text).
