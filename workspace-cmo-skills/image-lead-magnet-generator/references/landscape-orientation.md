# Landscape Orientation — kdy a jak

Default je portrait (2480×3508). Landscape (3508×2480) je správná volba **jen v 5 specifických případech**. V ostatních případech zůstává portrait.

---

## Kdy použít landscape

### 1. Srovnání A vs. B vs. C (3+ sloupců)

**Důvod:** Tabulkové srovnání 3+ možností potřebuje široké sloupce. Portrait by zúžil sloupce a vznikly by nečitelné lomené řádky v každé buňce.

**Layout:** `feature-grid-cards` v 3-sloupcovém variantu (3508×2480, 3 cards horizontálně).

**Příklad:** "Stripe vs. Shopify Payments vs. WooCommerce" se 4 sloupci a 12 kritérii.

### 2. Workbook s wide-form cvičeními (canvas-style)

**Důvod:** Business Model Canvas, Lean Canvas, mind maps potřebují horizontální plochu. Portrait by je deformoval do nečitelného úzkého sloupce.

**Layout:** custom canvas layout, typicky 9 boxů v gridu 3×3 nebo 5+4 split.

### 3. Timeline s 8+ fázemi

**Důvod:** Horizontální časová osa s mnoha milestones je čitelnější na šířku.

**Layout:** `process-numbered-steps` linear horizontal (3508×2480, kroky horizontálně).

### 4. Kalkulačka s rozhodovacím flow

**Důvod:** "Vstup → Výsledek → Interpretace → Akce" v 3-4 sloupcích vedle sebe.

**Layout:** custom flow layout, 4 cards horizontálně + arrows mezi nimi.

### 5. Wide hero / brand showcase

**Důvod:** Pokud brand má panoramic produktové mockupy nebo wide brand assets, landscape umožní use full canvas.

**Layout:** `cover-hero-overlay` landscape variant (3508×2480, dramatic full-bleed).

---

## Mixované orientace v jednom magnetu

Magnet může mít **mix portrait + landscape**:

- **Cover, intro, závěr (CTA, endcap)** = vždy portrait — společný úvodní/závěrečný rytmus
- **Speciální stránky** (canvas, wide srovnání, timeline) = landscape, pokud zlepší čitelnost
- **Maximum mix:** 80 % portrait + 20 % landscape v jednom magnetu

PDF kompozice (`compose-pdf.py`) podporuje mixované stránky:

```python
img = Image.open(page_path)
if img.width > img.height:
    pdf.add_page("Landscape", "A4")  # 297×210mm
else:
    pdf.add_page("Portrait", "A4")  # 210×297mm
pdf.image(page_path, ...)
```

---

## Layout adaptace per orientace

Většina layoutů z `premium-layouts.md` má **jiný design pro portrait vs. landscape**. Klíčové principy:

### Portrait → Landscape přechod

Při přechodu z portrait na landscape:
- Title se z **horní třetiny** přesune doleva (50% šířky)
- Foto/visual se z **pravé strany** přesune napravo (50% šířky)
- Bullet points / cards se z **vertikálního stacku** přesunou do **horizontálního gridu**
- Padding zboku zvětšit (víc místa) — `var(--space-12)` → `var(--space-16)`
- Padding shora/zdola zmenšit (méně místa) — `var(--space-12)` → `var(--space-8)`

### Landscape orientation pravidla

- **Title font může zůstat 60-80pt** (na šířku se vejde víc znaků)
- **Body text 12-13pt** (na šířku víc komfortní čtení)
- **Maximum 70-80 znaků na řádek** (čtenost klesá nad 80)
- **Žádný 2-sloupcový text** (čtení zigzag mezi sloupci v PDF je špatné)
- **Foto v split layoutu max 45 % šířky** (60 % šířky bylo by moc, oslabuje text)

---

## Prompt template pro landscape

```
{STYLE_DIRECTIVE}

A4 LANDSCAPE page design, aspect ratio 3508:2480, 300 DPI print quality.

Layout: {layout_name} — landscape variant
{layout description with horizontal arrangement noted}

[zbytek standardní jako portrait]

ORIENTATION-SPECIFIC NOTES:
- Layout uses full horizontal canvas
- Title positioned in left third or top-left
- Visual elements (photo, diagram, cards) span horizontal flow
- Generous padding sides (~80pt), tighter top/bottom (~40pt)
```

---

## Kdy NIKDY NEpoužít landscape

- **Mini-průvodce, Workbook s text-heavy obsahem** — portrait je čitelnější
- **Cover stránky** — portrait je standardně očekávaný formát
- **Audit / Sebehodnocení** — vertikální seznam otázek
- **Quote spread** — portrait dramatizuje vertical typography
- **Když uživatel nezadá důvod** — default vždy portrait

---

## Decision flow pro orientaci

V Kroku 2 workflow (page plan):

```
Default = portrait

For each page:
  IF layout == "feature-grid-cards" AND number_of_cards > 3:
    → landscape (3-sloupcový grid)
  ELIF layout == "diagram-flow" AND nodes > 5:
    → landscape (linear timeline)
  ELIF layout == "comparison" AND columns >= 3:
    → landscape (wide table)
  ELIF page.type == "workbook-canvas":
    → landscape (Business Model Canvas style)
  ELSE:
    → portrait

Always portrait:
  - cover-hero-overlay
  - cover-typographic
  - intro-stats-cards
  - toc-numbered
  - chapter-opener-fullbleed
  - quote-spread
  - cta-gradient-panel
  - endcap-product
```

---

## Pavlův příklad

Pro **AI Akcelerátor magnet** (7 agentů + cover/intro/CTA):

- Stránka 1 cover-hero-overlay → **portrait**
- Stránka 2 intro-stats-cards → **portrait**
- Stránky 3-9 (7 agentů) content-split-portrait → **portrait**
- Stránka 10 cta-gradient-panel → **portrait**
- Stránka 11 endcap-product → **portrait**

Pokud by Pavel chtěl přidat **srovnání 4 cenových plánů** (Akcelerátor lite vs. standard vs. premium vs. enterprise), to by byla **landscape** stránka — jediná v jinak portrait magnetu.

Pokud by chtěl **timeline 7 týdnů** s milestones (workshopy 1-14), mohla by být **landscape** s linear horizontal flow.

---

## PDF kompozice mixovaných orientací

```python
# compose-pdf.py logika:
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape

c = canvas.Canvas(output_path)

for png_path in sorted(pages_dir.glob("page-*.png")):
    img = Image.open(png_path)
    if img.width > img.height:
        c.setPageSize(landscape(A4))  # 297×210mm
    else:
        c.setPageSize(A4)  # 210×297mm

    page_w, page_h = c._pagesize
    c.drawInlineImage(str(png_path), 0, 0, page_w, page_h)
    c.showPage()

c.save()
```

PDF reader automaticky rotuje landscape stránky pro čtení — uživatel jednoduše scrolluje a stránka se sama otočí.
