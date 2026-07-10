---
name: Brand Board
description: Vygeneruje profesionální brand board moodboard z Brand DNA, loga a referenčních obrázků pomocí AI image generation.
category: creative
status: ready
version: "1.0"
publishedAt: "2026-05-02"
metadata: {"openclaw":{"emoji":"🎨","homepage":"https://docs.openclaw.ai/tools/skills"}}
---

# Brand Board

Vytvoří profesionální vertikální brand board (moodboard) na základě existujícího Brand DNA reportu, loga a volitelných referenčních obrázků. Výstupem je prémiový vizuál ve stylu Behance, připravený pro klienta nebo interní použití. Neřeší logo — to už musí existovat.

## Kdy použít

Když uživatel řekne "brand board", "moodboard", "vizuální identita", "brandboard", "vytvoř brand board", "vygeneruj brand board", nebo chce vizuální shrnutí značky.

## Předpoklady

Skill očekává tyto soubory ve složce `/documents/brand/`:

- **brandDNA.md** — Brand DNA report (povinný)
- **logo.png** nebo **logo.jpg** nebo **logo.webp** — hotové logo (povinný)
- **images/** — složka s referenčními obrázky (volitelné, max 5 obrázků)

Pokud brandDNA.md nebo logo chybí, informuj uživatele a požádej o doplnění. Složka images/ je volitelná — pokud existuje a obsahuje obrázky, použijí se jako vizuální reference pro brand board.

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

**Ze sekce 6 — VIZUÁLNÍ IDENTITA (klíčová sekce pro brand board):**
- Barevná paleta — primární a sekundární barvy s HEX kódy
- Typografie — doporučené fonty (heading + body), vč. Google Fonts alternativ
- Vizuální styl — celkový směr (minimalistický, luxusní, organický…)
- Styl fotografií — nálada, světlo, kompozice
- Textury a vzory
- Ikonografie — styl ikon (line, filled, hand-drawn…)

**Ze sekce 7 — SHRNUTÍ BRAND DNA:**
- Celkový pocit ze značky (jeden odstavec)

### Krok 2: Najdi logo

Hledej v `/documents/brand/` soubor loga v tomto pořadí priority:
1. `logo.png`
2. `logo.jpg`
3. `logo.webp`

Použij první nalezený a před generováním ověř, že soubor opravdu existuje přes filesystem. Použij přesně přiložené logo, žádné vlastní logo/wordmark. Pokud logo neexistuje, `image_generate` nevolej a požádej uživatele o doplnění loga.

### Krok 3: Načti referenční obrázky

Zkontroluj zda existuje složka `/documents/brand/images/`. Pokud ano:

1. Načti seznam obrázků (podporované formáty: .png, .jpg, .jpeg, .webp)
2. Vyber maximálně 5 obrázků — pokud jich je víc, použij prvních 5 (podle abecedy)
3. Tyto obrázky přilož jako vizuální reference k image_generate volání

Referenční obrázky mohou být: fotky produktů, inspirační moodboardy, ukázky stylu, fotky prostředí, cokoliv co pomůže AI pochopit vizuální směr značky.

Pokud složka neexistuje nebo je prázdná, pokračuj bez referenčních obrázků — brand board se vygeneruje jen z Brand DNA a loga.

### Krok 4: Sestav prompt pro image_generate

Na základě extrahovaných dat z Brand DNA sestav prompt pro generování brand boardu. Použij šablonu z `{baseDir}/references/prompt-template.md` a doplň ji konkrétními údaji ze značky:

- Nahraď všechny placeholdery (`{{BRAND_NAME}}`, `{{NICHE}}`, `{{COLORS}}` atd.) skutečnými hodnotami
- Pokud Brand DNA neobsahuje některé údaje (např. barvy), vynech příslušnou část nebo nech AI rozhodnout na základě esence značky
- Prompt musí být v **češtině**

### Krok 5: Vygeneruj brand board

Zavolej `image_generate` s:
- Sestaveným promptem
- Přiloženým logem jako referenčním obrázkem; použij přesně přiložené logo, žádné vlastní logo/wordmark
- Referenčními obrázky z `/documents/brand/images/` (pokud existují, max 5)

Když `image_generate` přikládáš lokální soubor z `/documents/...` jako referenci, použij pro parametr obrázku runtime cestu přes symlink `/home/node/documents/...` (např. `/home/node/documents/brand/logo.png`). Výstup pořád ukládej do `/documents/...`. Některé runtime validace nepovažují `/documents/...` za povolený vstupní media root, i když je to správná výstupní složka.

Pokud `image_generate` není dostupný, informuj uživatele že potřebuje nakonfigurovat image generation provider v OpenClaw.

### Krok 6: Ulož výstup

Ulož vygenerovaný obrázek jako `/documents/brand/brand-board.png`.

Zobraz uživateli:
1. Vygenerovaný brand board
2. Stručné shrnutí značky (2–4 věty česky) — co vizuál komunikuje

### Krok 7: Nabídni iteraci

Zeptej se uživatele zda je s výsledkem spokojený. Nabídni možnosti úprav:

- „Chcete tmavší/světlejší paletu?"
- „Jiný styl fotografií?"
- „Více minimalistické?"
- „Jiné rozvržení?"

Pokud uživatel chce změnu, uprav prompt na základě feedbacku a opakuj od Kroku 5. Při iteraci zachovej původní Brand DNA data a přidej uživatelův feedback jako dodatečnou instrukci do promptu.

## Pravidla

- **Žádné vlastní logo/wordmark** — tento skill NIKDY negeneruje logo. Logo musí být hotové předem. Použij přesně přiložené logo, žádné vlastní logo/wordmark.
- **Čeština** — veškerý text na brand boardu i v komunikaci s uživatelem je česky.
- **Kvalita** — výstup musí vypadat jako profesionální prezentace pro klienta, ne jako generický AI obrázek.
- **Brand DNA je zdroj pravdy** — vše vychází z brandDNA.md, skill si nic nevymýšlí.
- **Přepisování** — při opakovaném generování se brand-board.png přepíše (není verzování).

## Output

Soubor: `/documents/brand/brand-board.png`

## Reference

Šablona promptu pro generování: `{baseDir}/references/prompt-template.md`
