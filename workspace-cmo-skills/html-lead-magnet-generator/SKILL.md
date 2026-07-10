---
name: html-lead-magnet-generator
description: Z markdown obsahu lead magnetu vytvoří designový HTML dokument s editorial-quality layouty (cover, kapitoly, mýty/fakta, citáty, audit, CTA), 200+ ikonami, 4 style presety nebo DESIGN.md, a vyrenderuje PDF přes Playwright/Chromium. Žádné animace, statický A4 výstup.
category: marketing
status: ready
version: "1.0"
publishedAt: "2026-05-08"
metadata: {"openclaw":{"requires":{"bins":["python3"]},"emoji":"📄"}}
---

# HTML Lead Magnet Generator

Z hotového markdown obsahu lead magnetu (z `lead-magnet-generator`) vytvoří **designový HTML dokument** s editorial-quality layouty a vyrenderuje ho do produkčního PDF přes Playwright/Chromium.

**Hlavní rysy:**
- 11 page layoutů specifických pro lead magnety (cover, chapter opener, content, feature grid, mýty/fakta, audit, citát, checklist, CTA, srovnání, table of contents)
- 200+ inline SVG ikon (Lucide MIT) — feature gridy, bullety, mýty/fakta, CTA
- 4 vizuální presety (Editorial Premium / Notebook Clean / Bold Coach / Soft Therapeutic) — fallback bez DESIGN.md
- DESIGN.md integrace — primární zdroj barev, fontů, spacing
- Brand DNA load pro tonalitu microcopy
- A4 portrait, 300 DPI print CSS, page breaks, čísla stránek
- **Žádné animace, žádný JS** — statický HTML dokument pro PDF render

Inspirace: `html-presentation-generator` skill (vizuální principy, ikony), ale upraveno pro statické A4 PDF stránky místo slidů.

## Kdy použít

Použij tento skill když:
- Existuje hotový markdown lead magnetu (typicky `03-obsah.md` z `lead-magnet-generator`)
- Uživatel chce **textové designové PDF** s typografií a ikonami
- Uživatel říká "vyrenderuj PDF", "udělej PDF", "exportuj do PDF", "designové PDF"

Pro **plně obrázkové** A4 stránky generované AI (GPT Image 2) použij místo toho `image-lead-magnet-generator`.

## Vstup

1. **Markdown obsah** — typicky `/documents/lead-magnets/[nazev-magnetu]/03-obsah.md`
2. **Strategie** — typicky `/documents/lead-magnets/[nazev-magnetu]/00-strategie.md` (pro mapování typu magnetu na layouty)
3. **Brand DNA** — `/documents/brand/brandDNA.md` (pro tonalitu)
4. **Product DNA** — `/documents/brand/products/[nazev-produktu]/productDNA.md` (pro autora, citace)
5. **DESIGN.md** — `/documents/brand/DESIGN.md` (vizuální tokeny — pokud existuje)
6. **Volitelné:** cover image v `/documents/brand/products/[nazev-produktu]/images/cover.png`

## Workflow

### Krok 0a (POVINNÝ): Zvol orientaci stránky

**Default = portrait (na výšku, A4 210×297mm).** 95 % lead magnetů by mělo být na výšku — telefon je portrait, magnet se čte přirozeně, A4 portrait je standardní papír pro tisk a archiv.

**Landscape (na šířku, A4 297×210mm) jen v těchto případech:**

| Typ magnetu | Landscape OK? | Kdy |
|-------------|---------------|-----|
| Srovnání A vs. B | **Ano** | Tabulka má 3+ sloupců a 8+ kritérií — sloupce v portrait by byly nečitelně úzké |
| Workbook | **Někdy** | Obsahuje canvas-style cvičení v gridu (Business Model Canvas, Lean Canvas) |
| Kalkulačka | **Někdy** | Rozhodovací flow má 3+ horizontální kroky vedle sebe |
| Infographic / Timeline | **Někdy** | 12+ vertikálních zón v časové ose |
| Vše ostatní | **Ne** | Portrait je univerzálně lepší — mobilní čitelnost, tisk, kompatibilita |

Detailní logika v `{baseDir}/references/orientation.md`. Pokud nejasné → polož lidskou otázku:

> *"Tvůj magnet ti udělám na výšku (A4 portrait) — to je standard pro 95 % lead magnetů, čte se dobře na mobilu i v tisku. Chceš jiný formát?"*

**Mixované orientace** (cover portrait + 1 stránka landscape se srovnáním + závěr portrait) jsou možné, ale max 20 % stránek v jiné orientaci než výchozí.

### Krok 0b (POVINNÝ): Načti všechny vstupy

```
1. /documents/lead-magnets/[nazev-magnetu]/00-strategie.md  (vybraný typ magnetu)
2. /documents/lead-magnets/[nazev-magnetu]/03-obsah.md      (hotový obsah)
3. /documents/brand/brandDNA.md                              (markdown report)
4. /documents/brand/products/[nazev-produktu]/productDNA.md  (markdown report)
5. /documents/brand/DESIGN.md                                (volitelné — pokud existuje)
```

**Pokud `03-obsah.md` chybí** → uživatele odkaž na `lead-magnet-generator`. Tento skill nevytváří obsah, jen ho rendeuje.

**Pokud `DESIGN.md` chybí** → fallback na style preset (Krok 2).

### Krok 1: Identifikuj typ magnetu a mapování layoutů

Z `00-strategie.md` přečti vybraný typ magnetu (Checklist / Mini-průvodce / Audit / Workbook / atd.).

Podle typu vyber **sekvenci layoutů** podle tabulky v `{baseDir}/references/page-layouts.md` sekce "Mapování typů magnetu → layouty":

| Typ magnetu | Pořadí layoutů |
|-------------|----------------|
| Checklist | Cover → Content → CTA |
| Mini-průvodce | Cover → TOC → (Chapter Opener + Content × 2) × N → Quote → CTA |
| Audit | Cover → Content (úvod) → Audit Question × N → Content (výklad) × M → CTA |
| Workbook | Cover → TOC → (Chapter Opener + Checklist) × N → Quote → CTA |
| ... | viz `page-layouts.md` |

### Krok 2: Vyber vizuální styl

#### Pokud existuje DESIGN.md

Použij ho přímo. Z YAML frontmatteru extrahuj a namapuj na CSS proměnné v `:root` podle `{baseDir}/references/design-token-mapping.md`.

#### Pokud DESIGN.md neexistuje

Vyber preset z `{baseDir}/references/style-presets.md` na základě brand DNA:

| Brand DNA signál (sekce 1 ESENCE + sekce 5 HLAS) | Preset |
|---------------------------------------------------|--------|
| "klidný, prémiový, sofistikovaný"; "moudrý průvodce" | Editorial Premium |
| "intelektuální, expertní"; produktivita, B2B | Notebook Clean |
| "sebevědomý, konfrontační, energický"; brand stage autorita | Bold Coach |
| "empatický, hřejivý, ženský, healing"; terapeutika, mindfulness | Soft Therapeutic |

**Pokud signály matou** → default Editorial Premium + zeptej se uživatele potvrdit.

### Krok 3: Parsuj markdown na strukturu stránek

Z `03-obsah.md` rozparsuj sekce na **logické bloky** a mapuj na layouty:

| Markdown vzor | Layout |
|---------------|--------|
| Frontmatter title + úvodní 2 odstavce | `cover` (Variant A nebo B podle dostupnosti hero image) |
| `## Obsah` nebo automatický TOC | `toc` |
| `# Kapitola N: ...` | `chapter-opener` (s velkým číslem N) |
| Standardní `## podsekce` + odstavce + bullety | `content` |
| `## Mýty vs. Fakta` blok | `myth-fact` |
| `> Citát autora` | `quote` |
| `### 3 typy / 3 kroky / 3 benefity` se strukturovanými body | `feature-grid` |
| `## Tvůj X audit` se strukturou otázek | `audit` |
| `## Šablona / Checklist` se seznamem polí | `checklist` |
| `## Srovnání A vs. B` s tabulkou | `comparison` |
| `# Kapitola závěrečná` (Brunson HSO) nebo `## Co dál` | `cta` |

**Algoritmus mapování:**

1. Rozděl markdown na sekce (split na `^# ` headings)
2. První sekce = cover (frontmatter title + meta)
3. Pro každou další sekci:
   - Pokud `# Kapitola N:` → emit `chapter-opener` page + následný content jako `content` page(s)
   - Pokud obsahuje `## Mýty vs. Fakta` → emit `myth-fact` page
   - Pokud obsahuje strukturované 3-6 boxů → emit `feature-grid` page
   - Pokud obsahuje `> citát` na samostatné stránce → emit `quote` page
   - Pokud obsahuje `## Šablona` nebo `## Checklist` → emit `checklist` page
   - Jinak → `content` page
4. Poslední sekce s CTA blokem → emit `cta` page

**Pravidlo content density:** žádná stránka nesmí přetékat A4 výšku (297mm). Pokud sekce má >800 slov, rozděl na víc `content` stránek.

### Krok 4: Vlož ikony

Pro každou stránku, která potřebuje ikony, načti SVG z `{baseDir}/references/icons.md` a vlož inline.

**Mapování typu obsahu → ikona:**

| Použití | Doporučená ikona |
|---------|------------------|
| Bullet pozitivní | `check`, `check-circle` |
| Bullet negativní | `x`, `x-circle` |
| Bullet next step | `arrow-right` |
| Mýtus | `x-circle` (červená) |
| Fakt | `check-circle` (zelená) |
| Tip / poznámka | `info` |
| Pozor / warning | `alert-triangle` |
| Bonus | `gift` |
| Top / hodnocení | `star` |
| Energy / urgence | `zap` |
| Cíl | `target` |
| Růst | `trending-up` |
| Pokles | `trending-down` |
| Quote mark | `quote` |
| CTA tlačítko | `arrow-right` |

Konkrétní SVG kód v `{baseDir}/references/icons.md`.

### Krok 5: Sestav HTML

Použij šablonu z `{baseDir}/references/html-template.md`. Šablona obsahuje:

- `<head>` s Google Fonts (preload pro detekované fonty z DESIGN.md/preset)
- `:root` s CSS proměnnými (z DESIGN.md nebo presetu)
- `@page` rules pro A4 print
- Page-specific CSS classes (`.page--cover`, `.page--chapter-opener`, atd.)
- Print CSS (page breaks, widows, orphans, color-adjust)

Skládej stránky v pořadí dle Kroku 3, vkládej ikony podle Kroku 4.

**Tonalita microcopy** přebírej z `brandDNA.md` sekce 5 "Hlas značky":
- Cover badge text — z brand slovníku
- Eyebrow labels (`OBSAH`, `KAPITOLA 02`) — formálnost dle hlasu
- CTA button text — energie dle tónu

### Krok 6: Vyrenderuj PDF přes Playwright

Spusť `{baseDir}/scripts/render-pdf.py`:

```bash
python3 "{baseDir}/scripts/render-pdf.py" \
  --markdown "/documents/lead-magnets/[nazev-magnetu]/03-obsah.md" \
  --strategy "/documents/lead-magnets/[nazev-magnetu]/00-strategie.md" \
  --brand-dna "/documents/brand/brandDNA.md" \
  --product-dna "/documents/brand/products/[nazev-produktu]/productDNA.md" \
  --design "/documents/brand/DESIGN.md" \
  --preset "editorial-premium"  # fallback pokud DESIGN.md chybí
  --output "/documents/lead-magnets/[nazev-magnetu]/lead-magnet.pdf" \
  --cover "/documents/brand/products/[nazev-produktu]/images/cover.png"  # volitelné
```

Skript:
1. Načte všechny vstupní soubory
2. Sestaví HTML dle workflow Kroků 1–5
3. Spustí Playwright Chromium (headless)
4. Vyrenderuje PDF s A4 formátem, print backgrounds, čísly stránek
5. Vrátí cestu k výstupnímu PDF

### Krok 7: Validuj výstup

Po renderu zkontroluj:

- [ ] PDF existuje a má >0 bytes
- [ ] Velikost realistická (<10 MB pro 30str. dokument)
- [ ] Otevři první stránku jako screenshot a verifikuj cover
- [ ] Spočítej `pdf-pages` — sedí počet stran s plánem?

Pokud něco špatně → loguj problém + nabídni regeneraci.

### Krok 8: Output

```
✅ PDF vytvořeno: /documents/lead-magnets/[nazev-magnetu]/lead-magnet.pdf
   Velikost: XX KB
   Stran: XX
   Použitý styl: [DESIGN.md / preset název]

Co teď dál:
- Pokud chceš místo textového PDF plně obrázkové stránky → spusť `image-lead-magnet-generator`
- Pokud chceš editovat obsah → uprav 03-obsah.md a spusť `html-lead-magnet-generator` znovu
```

## Pravidla výstupu (závazná)

Před doručením ověř proti checklistu z `{baseDir}/references/visual-rules.md`:

- Cover title ≥ 36pt
- **Cover BEZ tech meta info** — žádný počet stran, čas čtení, datum, version, page number, info o tisku. Patří do TOC nebo footer interních stránek, ne na obálku.
- **Cover hero image** musí mít overlay s rgba 0.78–0.92 na tmavé části gradient + text-shadow na title pro čitelnost
- Chapter opener title ≥ 28pt + velké číslo (≥ 120pt)
- Vizuální hierarchie max 3 úrovně per stránka
- Feature grid POVINNĚ s ikonami (ne jen text)
- Mýty/Fakta POVINNĚ s × a ✓ ikonami
- Bullety v contentu mají ikony (ne klasické odrážky)
- Pravidlo jednoho vizuálního zdroje per stránka
- Kontrast textu/pozadí ≥ 4.5:1
- Padding stránky ≥ 32pt z boků, ≥ 48pt shora/zdola
- **ŽÁDNÉ animace, ŽÁDNÝ JS**
- Page breaks správné (chapter opener = nová stránka, feature card neporušená)
- ≥ 20% volné plochy na stránku

## Output

```
/documents/lead-magnets/[nazev-magnetu]/
├── 00-strategie.md          # vstup
├── 03-obsah.md              # vstup
├── lead-magnet.pdf          # OUTPUT
└── _temp/                   # dočasné soubory (smaž po úspěšném renderu)
    ├── content.html
    └── styles.css
```

## Reference

- `{baseDir}/references/orientation.md` — kdy portrait vs. landscape a proč
- `{baseDir}/references/page-layouts.md` — 11 layoutů pro A4 stránky lead magnetu
- `{baseDir}/references/style-presets.md` — 4 vizuální presety (fallback bez DESIGN.md)
- `{baseDir}/references/visual-rules.md` — závazná pravidla pro nadpisy, hierarchii, ikony, kontrast
- `{baseDir}/references/icons.md` — knihovna 200+ inline SVG ikon (Lucide MIT)
- `{baseDir}/references/html-template.md` — kompletní HTML šablona
- `{baseDir}/references/design-token-mapping.md` — mapování DESIGN.md → CSS proměnné
- `{baseDir}/references/print-css-spec.md` — print CSS pro A4 PDF
- `{baseDir}/scripts/render-pdf.py` — Playwright rendering script
