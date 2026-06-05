# Kit Mapping — typ stránky → relevantní brand-kit reference

Brand-kit je složka v `/documents/brand/brand-kit/` s vygenerovanými mockupy značky. Každý mockup má jiný účel a slouží jako **vizuální language reference** pro různé typy stránek.

GPT Image 2 přes FAL podporuje **až 3 reference images** simultaneously. Pro každou stránku magnetu vybereme:

1. **Vždy**: `brand-board.png` (globální mood)
2. **Vždy pokud existuje**: `08-inspirace-pro-pdf-materialy.png` (PDF layout language)
3. **Layout-specific**: další 1 mockup z brand-kit podle typu stránky

---

## Standardní brand-kit struktura

Pavel používá tuto convention (z `brand-image-generator` skillu):

```
/documents/brand/brand-kit/
├── 01-hero-mockup.png            # Hero — produktový mockup s glow/dramatic light
├── 02-business-card.png          # Business card mockup
├── 03-letterhead.png             # Letterhead / dopis
├── 04-social-square.png          # Instagram/social square post
├── 05-prodejni-prezentace.png    # Slide / prezentace mockup
├── 06-inspirace-pro-prezentace.png  # Inspirace pro prezentace
├── 07-app-mockup.png             # App / dashboard mockup
├── 08-inspirace-pro-pdf-materialy.png  # KRITICKÉ — PDF layout inspirace
├── 09-merchandise.png            # T-shirt, mug, atd.
├── 10-billboard.png              # Outdoor reklama
├── 11-packaging.png              # Obal produktu
├── 12-website-mockup.png         # Web design mockup
├── ...
└── 24-{další mockupy}            # Další podle značky
```

Ne všechny brandy mají všech 24 mockupů — skill pracuje s tím, co je dostupné.

---

## Mapování layoutu → kit reference

Pro každý ze 16 layoutů (`premium-layouts.md`) vyber primární reference:

| Layout | Primary kit reference | Sekundární reference (volitelná) |
|--------|------------------------|-----------------------------------|
| **cover-hero-overlay** | `01-hero-mockup.png` (dramatic atmospheric) | `08-inspirace-pro-pdf-materialy.png` (cover examples) |
| **cover-typographic** | `08-inspirace-pro-pdf-materialy.png` (typographic covers) | `02-business-card.png` (typography reference) |
| **intro-stats-cards** | `08-inspirace-pro-pdf-materialy.png` (card style example) | `07-app-mockup.png` (dashboard cards reference) |
| **toc-numbered** | `08-inspirace-pro-pdf-materialy.png` (TOC if shown) | `03-letterhead.png` (typographic hierarchy) |
| **chapter-opener-fullbleed** | `01-hero-mockup.png` (atmospheric) | `08-inspirace-pro-pdf-materialy.png` |
| **content-split-portrait** | `08-inspirace-pro-pdf-materialy.png` (text+image splits) | `06-inspirace-pro-prezentace.png` |
| **content-image-top** | `08-inspirace-pro-pdf-materialy.png` | `05-prodejni-prezentace.png` |
| **feature-grid-cards** | `08-inspirace-pro-pdf-materialy.png` (card grids) | `07-app-mockup.png` (UI card patterns) |
| **myth-fact-comparison** | `08-inspirace-pro-pdf-materialy.png` (split comparisons) | — |
| **quote-spread** | `08-inspirace-pro-pdf-materialy.png` (quote treatments) | `03-letterhead.png` (typographic dominance) |
| **checklist-detailed** | `08-inspirace-pro-pdf-materialy.png` (checklist example!) | — |
| **diagram-flow** | `08-inspirace-pro-pdf-materialy.png` (cycle diagram example!) | `07-app-mockup.png` (clean iconography) |
| **process-numbered-steps** | `08-inspirace-pro-pdf-materialy.png` (numbered process example!) | — |
| **product-mockup** | `01-hero-mockup.png` | `11-packaging.png` (pokud produkt) |
| **cta-gradient-panel** | `08-inspirace-pro-pdf-materialy.png` (CTA panel example!) | `10-billboard.png` (bold poster aesthetic) |
| **endcap-product** | `01-hero-mockup.png` (full-bleed) | `11-packaging.png` |

### Klíčový insight

**`08-inspirace-pro-pdf-materialy.png` je nejvíce hodnotný reference pro většinu PDF layoutů.** Je to "Rosetta stone" který GPT Image 2 sděluje:
- Card style (border, shadow, gradient)
- Typography hierarchy v PDF kontextu
- Number/checkmark/icon treatment
- Diagram style (cycle, linear, split)
- CTA panel style

Pokud brand má **jen brand-board + 08-inspirace-pro-pdf-materialy.png**, skill funguje téměř plně. Ostatní mockupy přidávají detail, ale nejsou kritické.

---

## Jak skill skládá reference per stránku

Pro stránku N v page-plan.json:

```python
def get_references_for_page(page, brand_kit_dir):
    refs = []

    # 1. Vždy brand-board
    brand_board = brand_kit_dir.parent / "brand-board.png"
    if brand_board.exists():
        refs.append(str(brand_board))

    # 2. Vždy PDF inspiration pokud existuje
    pdf_insp = brand_kit_dir / "08-inspirace-pro-pdf-materialy.png"
    if pdf_insp.exists():
        refs.append(str(pdf_insp))

    # 3. Layout-specific (pokud existuje a není už v refs)
    layout_to_kit = {
        "cover-hero-overlay": "01-hero-mockup.png",
        "endcap-product": "01-hero-mockup.png",
        "product-mockup": "01-hero-mockup.png",
        "feature-grid-cards": "07-app-mockup.png",
        "diagram-flow": "07-app-mockup.png",
        "quote-spread": "03-letterhead.png",
        # ostatní default na 08-inspirace pro většinu
    }

    layout = page["layout"]
    if layout in layout_to_kit:
        kit_file = brand_kit_dir / layout_to_kit[layout]
        if kit_file.exists() and str(kit_file) not in refs:
            refs.append(str(kit_file))

    # 4. Per stránka product image (pokud relevantní)
    if page.get("use_product_photo"):
        product_dir = Path("/documents/brand/products") / page["product_slug"] / "images"
        product_img = product_dir / page.get("product_image_filename", "hero.jpg")
        if product_img.exists():
            refs.append(str(product_img))

    # FAL limit: max 3 reference images
    return refs[:3]
```

---

## Co dělat když brand-kit chybí

Pokud `/documents/brand/brand-kit/` neexistuje nebo je prázdný, skill funguje **jen s brand-board.png**. Output bude méně specifický pro PDF formát, ale stále vizuálně konzistentní.

Doporučení uživateli:

> *"Tvůj magnet ti udělám z `brand-board.png`, ale pro **prémiovější PDF kvalitu** doporučuju pustit `brand-image-generator` skill a vygenerovat `brand-kit/08-inspirace-pro-pdf-materialy.png`. Bez něj GPT Image 2 generuje generic PDF estetiku — s ním dostane konkrétní layout language tvé značky."*

---

## Co dělat když brand-board.png chybí

**STOP.** Image Lead Magnet Generator vyžaduje minimálně brand-board. Doporuč uživateli:

- Pusť `brand-dna` skill pro vygenerování (ten vytvoří moodboard jako součást Brand DNA reportu)
- Nebo pusť `brand-image-generator` skill pro vygenerování standalone brand-board.png
- Nebo dodej vlastní brand-board manuálně (export z Figma, screenshot z brand guidelines)

Bez brand-board nemáme **vizuální DNA značky** — výstup by byl generický.

---

## Custom kit files (per-brand variants)

Některé brandy mají jiné názvy souborů. Skill detekuje:

- `brand-board.png` ALE i `brandboard.png`, `moodboard.png`, `brand-board.jpg`
- `08-inspirace-pro-pdf-materialy.png` ALE i `08-pdf-inspirace.png`, `pdf-style.png`, `pdf-mockups.png`

Heuristika v `generate-images.py`:

```python
def find_brand_board(brand_dir):
    candidates = ["brand-board.png", "brandboard.png", "moodboard.png",
                  "brand-board.jpg", "brandboard.jpg"]
    for name in candidates:
        path = brand_dir / name
        if path.exists():
            return path
    return None

def find_pdf_inspiration(brand_kit_dir):
    candidates = ["08-inspirace-pro-pdf-materialy.png", "08-pdf-inspirace.png",
                  "pdf-style.png", "pdf-mockups.png", "pdf-layout-inspiration.png"]
    for name in candidates:
        path = brand_kit_dir / name
        if path.exists():
            return path
    return None
```
