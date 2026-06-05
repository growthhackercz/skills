# Text Overlay Fallback

GPT Image 2 zvládne text lépe než předchozí modely, ale není 100% spolehlivé.
Pokud renderovaný text na stránce vychází chybně (typo, garbled, illegible),
použij fallback strategii: **text vypálit přes Pillow** na čistý obrázek.

---

## Detekce problému

Po batch generování ověř (manuálně nebo přes OCR):
- Title je čitelný a obsahuje očekávaný text
- Bullets neobsahují garbled characters
- Pull quotes jsou ve správném jazyce (čeština)

**Známky problému:**
- Mix anglických a českých znaků uprostřed slov
- Nečitelné fonty (rozmazané, deformované)
- Chybějící diakritika
- Náhodné znaky vložené do textu

---

## Fallback workflow

### Strategie 1: Re-prompt s důrazem na text

Přepiš prompt s explicitními instrukcemi:

```
CRITICAL: render the following text EXACTLY as written, in Czech language with
full diacritics (á, é, í, ó, ú, ů, ý, č, ď, ě, ň, ř, š, ť, ž).
Title text: "{{EXACT_TITLE}}"
Subtitle: "{{EXACT_SUBTITLE}}"

Use a clean sans-serif font. NO stylized lettering. NO custom typography.
The text must be 100% legible and grammatically correct in Czech.
```

Vygeneruj 2-3 variants, vyber nejlepší.

### Strategie 2: Generuj bez textu + Pillow overlay

Pokud text stále selhává, **odstraň text z promptu** a vygeneruj jen vizuální vrstvu:

```
{{PREFIX}}

A magazine page background composition.
Visual elements only — NO text, NO typography, NO words.

[zbytek popisu vizuálu...]

{{NEGATIVE}} + ", any text or typography, lettering, words, characters"
```

Pak v `compose-pdf.py` nebo separátním skriptu **vlož text přes Pillow**:

```python
from PIL import Image, ImageDraw, ImageFont

img = Image.open("page-01.png")
draw = ImageDraw.Draw(img)

# Načti font (z system fontů nebo z DESIGN.md fonta path)
font_title = ImageFont.truetype("/path/to/Inter-Bold.ttf", 96)
font_body = ImageFont.truetype("/path/to/Inter-Regular.ttf", 32)

# Vlož title
draw.text((150, 1800), "5 kroků k 6měsíční rezervě za 90 dní", font=font_title, fill="#08090a")

# Vlož subtitle
draw.text((150, 2000), "Konkrétní 4-účtový systém + 14denní audit", font=font_body, fill="#6b7280")

img.save("page-01-final.png")
```

### Strategie 3: Hybrid — text v generaci + post-process kontrola

1. Vygeneruj s textem
2. Spustí OCR (Tesseract) na výsledný obrázek
3. Porovnej OCR výstup s expected textem
4. Pokud match >85%, accept
5. Pokud ne, fallback na strategii 2 (Pillow overlay)

---

## Pillow text positioning per page type

### cover

```python
# Title — bottom 40% area
draw.text(
    (margin_x, height * 0.65),
    title,
    font=ImageFont.truetype(brand_display_font, 144),
    fill=primary_color
)
# Subtitle
draw.text(
    (margin_x, height * 0.78),
    subtitle,
    font=ImageFont.truetype(brand_body_font, 48),
    fill=text_muted
)
```

### chapter-opener

```python
# Chapter number — large decorative
draw.text(
    (margin_x, height * 0.15),
    f"0{chapter_n}",
    font=ImageFont.truetype(brand_display_font, 360),
    fill=accent_color
)
# Chapter title — below
draw.text(
    (margin_x, height * 0.45),
    chapter_title,
    font=ImageFont.truetype(brand_display_font, 96),
    fill=primary_color
)
```

### content-spread

```python
# Headline left side
draw.text(
    (margin_x, margin_y + 100),
    headline,
    font=ImageFont.truetype(brand_display_font, 72),
    fill=primary_color
)
# Bullets
for i, bullet in enumerate(bullets):
    y = margin_y + 400 + (i * 80)
    draw.text((margin_x + 60, y), f"•  {bullet}", font=body_font, fill=text_color)
```

---

## Font sourcing

### System fonts (rychlé)

```python
import platform
if platform.system() == "Darwin":
    DEFAULT_FONT = "/System/Library/Fonts/Helvetica.ttc"
elif platform.system() == "Linux":
    DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
elif platform.system() == "Windows":
    DEFAULT_FONT = "C:/Windows/Fonts/arial.ttf"
```

### Brand fonts (z DESIGN.md)

Pokud DESIGN.md odkazuje na specifický font (Inter, Manrope, Plus Jakarta), stáhni z Google Fonts:

```python
import urllib.request

def download_google_font(family: str, weight: int = 400, dest: str = "/tmp/fonts"):
    """Download a Google Font TTF file."""
    family_url = family.replace(" ", "+")
    css_url = f"https://fonts.googleapis.com/css2?family={family_url}:wght@{weight}"
    # Parse @font-face → src url(...) z CSS odpovědi
    # Download .ttf na dest
    # Return cesta k souboru
```

### Diakritika test

Před použitím fonta v Pillow ověř, že obsahuje české znaky:

```python
def supports_czech(font_path: str) -> bool:
    from PIL import ImageFont
    try:
        f = ImageFont.truetype(font_path, 24)
        # Zkus vyrenderovat český řetězec
        f.getbbox("ěščřžýáíéůú")
        return True
    except Exception:
        return False
```

---

## Performance tip

Vždy preferuj **strategie 1 (re-prompt)** — text v originálním renderingu vypadá lépe (spojený s vizuálem). Fallback na Pillow overlay používej **jen když re-prompt selže 2x**.
