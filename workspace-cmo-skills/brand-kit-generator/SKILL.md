---
name: Brand Kit Generátor
description: Vygeneruje kompletní vizuální identitu značky — 24 mockupů z Brand DNA, Brand Boardu a loga pomocí AI image generation.
category: creative
status: ready
version: "1.0"
publishedAt: "2026-05-02"
metadata: {"openclaw":{"emoji":"🎨","homepage":"https://docs.openclaw.ai/tools/skills"}}
---

# Brand Kit Generátor

Vygeneruje kompletní vizuální identitu značky jako sadu profesionálních mockupů. Každý mockup je vertikální obrázek (2:3) ve stylu Behance — od fontů a barev, přes tiskoviny, web, e-shop, až po Instagram a YouTube. Celkem 24 promptů pokrývajících všechny klíčové touchpointy značky.

## Kdy použít

Když uživatel řekne "brand kit", "brand kit generátor", "vizuální identita", "brandové materiály", "mockupy značky", "vygeneruj brand kit", nebo chce konkrétní mockup z nabídky (např. "homepage", "Instagram", "tiskoviny", "reklamní bannery").

## Předpoklady

Skill očekává tyto soubory ve složce `/documents/brand/`:

- **brandDNA.md** — Brand DNA report (povinný)
- **brand-board.png** — Brand Board moodboard (povinný)
- **logo.png** nebo **logo.jpg** nebo **logo.webp** — hotové logo (povinný)
- **images/** — složka s referenčními obrázky (volitelné, max 5 obrázků)

Pokud brandDNA.md, brand-board.png nebo logo chybí, informuj uživatele a požádej o doplnění. Složka images/ je volitelná.

## Workflow

### Krok 1: Načti Brand DNA

Přečti soubor `/documents/brand/brandDNA.md`. Brand DNA report má 7 sekcí — extrahuj z nich tyto údaje:

**Ze sekce 1 — ESENCE ZNAČKY:**
- Název značky
- Kategorie (obor/niche)
- Slogan
- Jedinečná výhoda (USP)
- Transformace PŘED → PO
- Emoční tón (3–5 specifických pocitů)

**Ze sekce 2 — IDEÁLNÍ ZÁKAZNÍK:**
- Kdo je, co hledá, jak se má cítit při kontaktu se značkou

**Ze sekce 5 — HLAS ZNAČKY:**
- Tón, rytmus, postoj v komunikaci

**Ze sekce 6 — VIZUÁLNÍ IDENTITA (klíčová sekce):**
- Barevná paleta — primární a sekundární barvy s HEX kódy
- Typografie — doporučené fonty (heading + body), vč. Google Fonts alternativ
- Vizuální styl — celkový směr (minimalistický, luxusní, organický…)
- Styl fotografií — nálada, světlo, kompozice
- Textury a vzory
- Ikonografie — styl ikon (line, filled, hand-drawn…)

**Ze sekce 7 — SHRNUTÍ BRAND DNA:**
- Celkový pocit ze značky (jeden odstavec)

### Krok 2: Najdi logo a Brand Board

Hledej v `/documents/brand/`:

**Logo** (v tomto pořadí priority):
1. `logo.png`
2. `logo.jpg`
3. `logo.webp`

**Brand Board:**
- `brand-board.png`

Oba soubory před generováním ověř přes filesystem. Pokud některý chybí, `image_generate` nevolej a požádej uživatele o doplnění. Existující soubory přikládej jako referenční obrázky ke každému `image_generate` volání. Použij přesně přiložené logo, žádné vlastní logo/wordmark.

### Krok 3: Načti referenční obrázky

Zkontroluj zda existuje složka `/documents/brand/images/`. Pokud ano, načti max 5 obrázků (.png, .jpg, .jpeg, .webp) a přilož je jako dodatečné vizuální reference.

### Krok 4: Zobraz menu a nech uživatele vybrat

Zobraz uživateli kompletní menu:

```
Které mockupy chceš vygenerovat? Napiš čísla oddělená čárkou, rozsah, nebo "vše":

 1. Fonty a barvy
 2. Logo v reálném světě
 3. Značka v reálném světě
 4. Prezentace firemní identity
 5. Prodejní prezentace
 6. Inspirace pro prezentace
 7. Tiskové materiály
 8. Inspirace pro PDF materiály
 9. Inspirace pro fotografie
10. Inspirace pro výstavy a veletrhy
11. Inspirace pro živé akce
12. Lidé ve firmě
13. Inspirace pro obrázky na pozadí
14. Doplňkové prvky
15. Podklady pro digitální marketing
16. Návrh homepage
17. Hero sekce na webu
18. Inspirace pro e-shop
19. Prodejní cesta
20. Magnet na kontakty
21. Reklamní bannery
22. E-mail Marketing
23. Inspirace pro Instagram
24. Inspirace pro YouTube

Příklady: "1, 5, 16" nebo "1-7" nebo "vše"
```

Pokud uživatel rovnou v prvním dotazu zmíní konkrétní mockup (např. "vygeneruj homepage"), přeskoč menu a rovnou generuj odpovídající prompt.

### Krok 5: Generuj vybrané mockupy

Pro každý vybraný mockup:

1. Načti odpovídající prompt z `{baseDir}/references/prompts.md`
2. V promptu jsou reference `@Brand DNA` a `@Brand Board` — ty nahraď skutečnými daty extrahovanými v Kroku 1 a referenčními obrázky z Kroku 2–3
3. Zavolej `image_generate` s promptem + přiloženými obrázky (logo, brand board, referenční obrázky). Logo musí být použité přesně z přiloženého souboru, žádné vlastní logo/wordmark. Když přikládáš lokální referenční soubor z `/documents/...`, použij pro vstupní image parametr cestu `/home/node/documents/...`; výstupy pořád ukládej do `/documents/...`.
4. Ulož výstup jako `/documents/brand/brand-kit/XX-nazev.png` kde XX je číslo promptu a nazev je slug (např. `01-fonty-a-barvy.png`, `16-navrh-homepage.png`)

Pokud `image_generate` není dostupný, informuj uživatele že potřebuje nakonfigurovat image generation provider v OpenClaw.

Při generování více mockupů informuj uživatele o průběhu: "Generuji 3/24: Značka v reálném světě…"

### Krok 6: Zobraz výsledky a nabídni iteraci

Po vygenerování zobraz uživateli výsledky a zeptej se:

- "Chceš některý mockup přegenerovat?"
- "Chceš upravit styl? (tmavší, světlejší, minimálnější…)"
- "Chceš pokračovat s dalšími mockupy?"

Pokud uživatel chce změnu konkrétního mockupu, uprav prompt na základě feedbacku a přegeneruj. Při iteraci zachovej původní Brand DNA data a přidej uživatelův feedback jako dodatečnou instrukci na konec promptu.

## Pravidla

- **Žádné vlastní logo/wordmark** — tento skill NIKDY negeneruje logo. Logo musí být hotové předem. V každém promptu je instrukce: "použij přesně přiložené logo, žádné vlastní logo/wordmark; nikdy nevytvářej nové logo či logo elementy."
- **Čeština** — veškerý text na mockupech i v komunikaci s uživatelem je česky.
- **Formát 2:3** — všechny mockupy jsou vertikální v poměru 2:3.
- **Brand DNA je zdroj pravdy** — vše vychází z brandDNA.md, skill si nic nevymýšlí.
- **Brand Board jako vizuální reference** — brand-board.png se přikládá ke každému volání jako vizuální vodítko pro designový systém.
- **Přepisování** — při opakovaném generování se soubor přepíše (není verzování).

## Output

Složka: `/documents/brand/brand-kit/`

Soubory pojmenované: `XX-nazev-slug.png` (např. `01-fonty-a-barvy.png`)

## Reference

Všech 24 promptů: `{baseDir}/references/prompts.md`
