# Visual Rules — Pravidla vizuální kvality

Závazná pravidla pro každou stránku lead magnetu. **Bez dodržení těchto pravidel je výstup neakceptovatelný.**

Inspirováno html-presentation-generator skillem, ale upraveno pro **statické A4 PDF stránky** (ne slide deck).

---

## Nadpisy — Big, Bold, Beautiful

Nadpisy jsou hlavní vizuální element každé stránky. Musí být VELKÉ a dominantní.

### Velikosti

```css
/* Cover title — největší v celém dokumentu */
.cover-title {
  font-size: clamp(36pt, 6vw, 64pt);
  line-height: 1.05;
}

/* Chapter title */
.chapter-title {
  font-size: clamp(28pt, 5vw, 48pt);
  line-height: 1.1;
}

/* Page H1 (uvnitř kapitoly) */
.content-h1, h1 {
  font-size: clamp(22pt, 4vw, 32pt);
  line-height: 1.15;
}

/* H2 (sekce) */
h2 {
  font-size: clamp(16pt, 3vw, 22pt);
  line-height: 1.2;
}

/* H3 (podsekce) */
h3 {
  font-size: clamp(13pt, 2vw, 16pt);
  line-height: 1.3;
}
```

**Pravidla:**
- Cover title MUSÍ být dominantní — první věc, kterou divák uvidí. Minimum 36pt.
- Chapter opener title MUSÍ být dominantní — minimum 28pt.
- Pokud nadpis nevypadá jako hlavní prvek stránky, je příliš malý. Zvětši ho.
- **`font-weight` NIKDY nehardcoduj** — vždy čti z DESIGN.md / preset `--fw-bold` / `--fw-semibold`.

### Letter-spacing

- Display nadpisy (cover, chapter opener): negativní letter-spacing `-0.015em` až `-0.025em` — působí prémiověji.
- Běžné nadpisy: `0` nebo lehce negativní.
- Body text: `0`.
- ALL CAPS labels (eyebrow, badges): pozitivní `0.1em` až `0.15em`.

---

## Layout a vertikální struktura

### Padding stránky

```css
.page {
  padding: var(--space-12) var(--space-8);
  /* nebo víc na cover */
}

.page--cover {
  padding: var(--space-16) var(--space-12);
}
```

**Minimum:** `var(--space-12)` (48pt) shora a zdola, `var(--space-8)` (32pt) z boků. Méně vypadá utlačeně.

### Max-width pro text

- Body text odstavec: `max-width: 60ch` až `70ch` pro čitelnost
- Nadpisy: bez `max-width` (mohou roztáhnout celou stránku)
- Bullety: bez `max-width` (paddings je ohraničí)

### Vertikální distribuce obsahu

Stránka MUSÍ mít smysluplnou vertikální distribuci:

| Layout | Distribuce |
|--------|------------|
| Cover (text) | space-between (top: badges, middle: title, bottom: author) |
| Chapter opener | space-between (top: label+num, middle: title, bottom: quote) |
| Content | top-down (header → h2 → lead → body → aha) |
| Quote | center (vertikálně centrovaný citát) |
| CTA | center (vše uprostřed s gradientem) |
| Audit | top-down (header → questions seznamem) |

NIKDY nenechej obsah viset nahoře s velkou prázdnou plochou pod ním. Buď ho nadech, nebo přesuň víc vzduchu okolo.

---

## Vizuální hierarchie (3 úrovně)

Každá stránka má **3 úrovně důležitosti**:

1. **Primární** — nadpis nebo hlavní číslo. Největší, nejtučnější, nejvíc kontrastní.
2. **Sekundární** — podnadpis, klíčové bullety, ikony. Střední velikost.
3. **Terciární** — body text, labels, drobné detaily. Nejmenší, nejlehčí.

Pokud má stránka víc než 3 úrovně, je příliš komplexní → rozděl na 2 stránky.

---

## Práce s obrázky

### Cover hero image

Pokud je cover Variant B (hero):

```css
.cover--hero {
  background-size: cover;
  background-position: center;
}

.cover-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.3), rgba(0,0,0,0.7));
}
```

**Pravidla:**
- Overlay je **POVINNÝ** — text na fotku bez overlay = nečitelné.
- Tmavá fotka → lehčí overlay `rgba(0,0,0,0.3)`.
- Světlá fotka → silnější overlay `rgba(0,0,0,0.6)`.
- Brand fotka → `rgba(brand-color, 0.7)` pro brand feel.

### Inline obrázky v contentu

Pokud content stránka má inline obrázek (např. screenshot, diagram):

```css
.content-image {
  width: 100%;
  max-height: 50%;
  object-fit: contain;
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
}

/* Pro screenshoty s rámečkem */
.content-image--screenshot {
  border: 1pt solid var(--color-border);
  box-shadow: 0 4pt 16pt rgba(0,0,0,0.08);
}
```

### Fotky s bílým pozadím

- Na světlé stránce → **žádný stín, žádný border, žádný border-radius**. Použij `mix-blend-mode: multiply` pro odstranění bílého pozadí.
- Na tmavé stránce → bílý rámeček nebo karta s bílým pozadím dává smysl.

```css
.product-img-clean {
  background: transparent;
  border: none;
  box-shadow: none;
  mix-blend-mode: multiply;
}
```

### Pravidlo jednoho vizuálního zdroje

Na jedné stránce **MAXIMUM 1 dominantní vizuál**:

| Layout | Vizuál |
|--------|--------|
| Cover hero | 1 background image |
| Cover text | 0 obrázků (typografie dominuje) |
| Content | 0–1 inline image |
| Feature grid | Ikony v kartách (žádné fotky) |
| Mýty/Fakta | Jen × a ✓ ikony |
| Quote | Jen typografie + citation icon |
| Audit | Jen typografie a radio buttons |
| CTA | Gradient pozadí + ikony, žádné fotky |

NIKDY nekombinuj hero pozadí s dalšími inline fotkami.

---

## Ikony (POVINNĚ pro vybrané layouty)

Ikony dodávají vizuální jazyk a pomáhají rychle komunikovat koncepty.

### Kde POVINNĚ použít ikony

- **Feature grid** — POVINNĚ ikona + nadpis + 1 řádek popisu v každé kartě. Nikdy jen text.
- **Bullet pointy v contentu** — používej ikony místo klasických odrážek (check, arrow-right, zap, star).
- **Mýty vs. Fakta** — `x-circle` (červená) vs. `check-circle` (zelená).
- **CTA stack** — `check-circle` u každé položky.
- **Tipy / poznámky** — `info` ikona u info boxů.
- **Quote stránka** — `quote` ikona nahoře.

### Velikost a barva

```css
/* Standardní bullet ikona */
.bullet-icon {
  width: 24pt;
  height: 24pt;
  color: var(--color-accent);
  flex-shrink: 0;
}

/* Feature card ikona (větší) */
.feature-icon {
  width: 36pt;
  height: 36pt;
}

/* Quote/decorative ikona (velká) */
.quote-mark {
  width: 64pt;
  height: 64pt;
  opacity: 0.6;
}
```

### Pravidla

- **Konzistence** — používej **JEDNU knihovnu** v celém dokumentu (Lucide z `icons.md`). Nemíchej styly.
- **Stroke weight** — Lucide má `stroke-width: 2`. Drž ho.
- **Barva** — `stroke: currentColor` na SVG, barvu nastav přes CSS `color` na rodiči.
- **Účel** — každá ikona MUSÍ komunikovat koncept. Nikdy nepoužívej jako čistou dekoraci.
- **Sémantika:** check = pozitivní, x = negativní, arrow-right = next/CTA, alert-triangle = pozor, info = tip, gift = bonus, star = top, zap = energy/quick.

### Zdroj

`{baseDir}/references/icons.md` obsahuje 200+ inline SVG ikon z Lucide (MIT licence). Vlož přímo do HTML, žádné fetch, funguje offline.

---

## Kontrast a čitelnost

### Text barvy

```css
/* Tmavé pozadí → vždy bílá nebo světlejší než #f0f0f0 */
.dark-bg .text {
  color: var(--color-bg);  /* typicky #ffffff */
}

/* Světlé pozadí → vždy tmavší než #555555 */
.light-bg .text {
  color: var(--color-text);  /* typicky #1a1a1a nebo tmavší */
}
```

### Pravidla

- **NIKDY** nepoužívej šedý text pod `#cccccc` na tmavém pozadí — nečitelné.
- **NIKDY** nepoužívej šedý text nad `#555555` na světlém pozadí.
- **Akcentové barvy** (gold, oranžová) na tmavém pozadí: OK pro labels/tagy, NIKDY pro body text.
- **Sub-text a labels** — minimální kontrast 4.5:1 (WCAG AA).
- **Hero stránky** — `text-shadow: 0 2pt 12pt rgba(0,0,0,0.4)` pro extra čitelnost.

### Background barvy

```css
/* Standardní stránka */
.page { background: var(--color-bg); }

/* Sub-page (chapter opener, callout sekce) */
.page--subtle { background: var(--color-bg-subtle); }

/* Hero (cover, quote, CTA) */
.page--hero { background: var(--color-primary); color: var(--color-bg); }
```

---

## Čistota a prostor

- Každá stránka potřebuje "vzduch" — minimálně **20% volného prostoru**.
- Neplň celou plochu obsahem. Prázdný prostor je designový element.
- Karty/boxy: maximum **3 vedle sebe** na full-width, 2 na half-width.
- Mezi kartami vždy gap: `clamp(1rem, 2vw, 2rem)`.
- Badges/tagy: NIKDY nepřilepovat na text — vždy `margin-top: clamp(0.75rem, 1.5vw, 1.5rem)`.
- Mezi body textem a CTA boxem: minimálně `var(--space-6)` (24pt) mezera.

---

## Page break pravidla

Pro PDF rendering jsou kritická:

```css
.page {
  page-break-after: always;
  break-after: page;
}

.page:last-child {
  page-break-after: auto;
}

/* Nepřerušuj uvnitř */
.feature-card,
.cta-stack,
.audit-question,
.mf-pair,
.quote-text {
  page-break-inside: avoid;
  break-inside: avoid;
}

/* Nadpis se nesmí osamotit nahoře další stránky */
h1, h2, h3 {
  page-break-after: avoid;
  break-after: avoid;
}

/* Min 3 řádky odstavce na konci/začátku stránky */
p, li {
  orphans: 3;
  widows: 3;
}
```

---

## Žádné animace, žádný JS

**Lead magnet je statický PDF dokument.**

- ❌ Žádné `transition`, `animation`, `transform` (kromě jednorázových v print rendering)
- ❌ Žádný JavaScript
- ❌ Žádné `scroll-snap`, `Intersection Observer`, `nav dots`
- ❌ Žádné hover efekty (PDF je papír)
- ✅ Pouze CSS pro vzhled, vše statické při render time

**Důvod:** PDF render screenshot zachytí jen statický stav. Animace v PDF nefungují.

Pokud HTML verzi distribuuješ jako webovou stránku (např. interactive workbook), můžeš přidat animace pro web verzi a `@media print` zakázat — ale **default = statický**.

---

## Page overflow prevention (KRITICKÉ)

A4 stránka je pevný kontejner **210×297mm**. Obsah NIKDY nesmí přetékat — žádný text, ikona, image ani CTA box nesmí narazit na okraj nebo zmizet pod obrysem.

### Závazná pravidla

```css
.page {
  width: 210mm;
  height: 297mm;
  padding: var(--space-12) var(--space-8);  /* 48pt × 32pt minimum */
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
```

- **`overflow: hidden`** je POVINNÝ — bez něj přetékající obsah unikne mimo stránku v PDF
- **Padding minimum**: `var(--space-12)` (48pt) shora i zdola, `var(--space-8)` (32pt) z boků
- **Vertikálně silnější padding** než boční — print konvence (čtenář drží papír za boční okraj, top/bottom potřebuje víc dýchacího prostoru)
- **Cover** může mít zvýšený padding `var(--space-16) var(--space-12)` (64pt × 48pt)

### Density limit per stránka

Pokud obsah překročí limit, **rozděl na víc stránek** — nikdy nezmenšuj font ani padding.

| Layout | Maximum |
|--------|---------|
| Cover | 1 title (max 2 řádky) + 1 subtitle (max 1.5 řádku) + author + badge |
| Chapter opener | 1 title + 1 tease + 1 quote |
| Content | 1 H2 + 1 lead odstavec + 4-6 bullets + 1 aha box |
| Feature grid | Max 6 karet (3×2 nebo 2×3) |
| Mýty/Fakta | Max 4 páry per stránka |
| Audit | Max 6 otázek per stránka |
| Quote | 1 citát (max 4 řádky) + atribuce |
| CTA | 1 title + 4-5 stack items + button + meta (1 řádek) |

### Validace před doručením

Pro každou stránku spočítej výšku obsahu:
- Suma `height` všech direct children + suma `gap` + `padding-top + padding-bottom` MUSÍ být ≤ 297mm
- Pokud používáš `flex-direction: column` s `flex: 1` na hlavní zóně, max výška centrální zóny = 297mm − header_height − footer_height − 2×padding
- Při pochybnosti **rozděl na 2 stránky** — overflow je horší než nadbytečná stránka

### POVINNÝ overflow re-check po každé úpravě

**Po každé úpravě obsahu nebo stylů** (přidání textu, změna fontu, vložení obrázku, přejmenování) **MUSÍŠ projít všechny stránky a ověřit, že nepřetékají**.

Postup re-checku:

1. Pro každou stránku vypočítej content height:
   - Sečti výšku všech přímých dětí `.page` (nebo `.agent-page` apod.)
   - Přičti vertikální gaps mezi nimi
   - Přičti padding-top + padding-bottom stránky
2. Porovnej s 297mm (A4 výška)
3. Pokud `content_height > 297mm`:
   - **Zmenši font-size** o 1pt (lead, body)
   - **Zmenši gap mezi sekcemi** (--space-4 → --space-3 → --space-2)
   - **Zkrať text** v dlouhých sekcích (max 4 bullets, max 3 odstavce)
   - **Rozděl** na 2 stránky pokud nelze jinak

**Skill NIKDY nemůže vydat magnet bez tohoto re-checku.** Když přidáš obrázek nebo změníš layout, vždy:

```
1. Aplikuj změnu
2. Re-check overflow všech ovlivněných stránek
3. Pokud overflow → adjust
4. Re-check znovu
5. Až když všechny stránky fit → doručit uživateli
```

Tento step je často overlooked a způsobuje, že obsah na stránce zmizí nebo se rozseká přes page break — největší vizuální chyba PDF magnetu.

### Foto poměry stran — výběr layoutu podle formátu zdroje

Inline obrázky NIKDY nesmí být deformované nebo natažené. Skill **detekuje aspect ratio zdroje** a podle něj zvolí layout. Pro každý formát existuje optimální použití:

| Zdrojový poměr | Typ formátu | Optimální use case | Layout |
|----------------|-------------|---------------------|--------|
| **3:4 / 4:5** | Portrait | Foto agenta, founder portrét, lifestyle person | Split layout vpravo (38% šířky), `aspect-ratio: 3/4` |
| **16:9 / 3:2** | Landscape | Screenshot, dashboard, krajina, product overview | Full-width hero nahoře (`max-height: 40%`), nebo full-bleed cover |
| **1:1** | Square | Produkt, instagram-style, logo s prostorem | Feature grid (3×2 karty po 1:1), nebo side-by-side accent |
| **21:9** | Panorama | Wide banner, panorama foto | Full-bleed strip (max výška 25 %), nebo dělící prvek mezi sekcemi |
| **9:16** | Vertical (story) | Mobile screenshot, story-formát foto | Split layout 60/40 (foto úzké vpravo), `aspect-ratio: 9/16`, max-height stránky |
| **Neznámý / variabilní** | Mix | Brand assets bez konzistence | Detekuj přes `naturalWidth/naturalHeight`, mapuj na nejbližší kategorii výše |

**Detekce aspect ratio zdroje:**

Pokud obrázek je **brand asset** (lokální soubor v `/documents/brand/`), ověř jeho dimensions přes file metadata. Pokud je **remote URL** (Unsplash, web), ověř přes HEAD request nebo Image preload:

```javascript
// Ověření zdroje přes Chrome plugin / Image preload
new Promise(resolve => {
  const img = new Image();
  img.onload = () => resolve({
    w: img.naturalWidth,
    h: img.naturalHeight,
    ratio: img.naturalWidth / img.naturalHeight
  });
  img.src = imageUrl;
});

// Mapování ratio → kategorie
function categorize(ratio) {
  if (ratio < 0.65) return "vertical";      // < 9:14
  if (ratio < 0.85) return "portrait";       // 9:14 - 4:5
  if (ratio < 1.15) return "square";         // 4:5 - 6:5
  if (ratio < 1.85) return "landscape";      // 6:5 - 16:9
  return "panorama";                         // > 16:9
}
```

**CSS šablony per kategorie:**

```css
/* Portrait — split layout */
.image--portrait {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  object-position: center top;
}

/* Landscape — full-width hero */
.image--landscape {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  max-height: 40%;
}

/* Square — feature grid karty / accent */
.image--square {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: var(--radius-md);
}

/* Panorama — full-bleed strip */
.image--panorama {
  width: 100%;
  aspect-ratio: 21 / 9;
  object-fit: cover;
  max-height: 25%;
}

/* Vertical (story) — narrow split */
.image--vertical {
  width: 100%;
  aspect-ratio: 9 / 16;
  object-fit: cover;
  object-position: center;
  max-height: 80%;
}
```

**Pravidla:**
- `aspect-ratio` JE POVINNÝ — bez něj se obrázek může roztáhnout nebo zmenšit nepřirozeně
- `object-fit: cover` zachová poměr a ořeže přebytek (ne `fill` který deformuje)
- `object-position: center top` na portrétech — aby nebyly oříznuté hlavy
- NIKDY `height: 100%` bez `aspect-ratio` v gridu — obrázek se roztáhne na výšku celého kontejneru a vznikne deformace
- Pokud zdroj má **jiný poměr než cílový layout** (např. máš landscape foto, ale chceš ho do split portrait), buď:
  1. Vyber jiný layout který formátu vyhovuje (full-width hero místo split)
  2. Nebo `object-fit: cover` + `object-position` ořezem na portrait — ale ztratíš hodně z fotky

### Kontrola obrázků

Inline obrázky v contentu MUSÍ mít `max-height` constraint:

```css
.content-image {
  width: 100%;
  max-height: 50%;        /* nikdy víc než půl stránky */
  object-fit: cover;
  border-radius: var(--radius-md);
}

.content-image--small {
  max-height: 35%;        /* pokud je nad/pod text */
}
```

Bez `max-height` foto stáhne stránku dolů a obsah pod ním zmizí.

---

## Inline obrázky pro vizuální rytmus

### Pravidla podle délky magnetu

| Délka magnetu | Typ stran | Doporučený počet inline fotek | Rozložení |
|---------------|-----------|-------------------------------|-----------|
| **1–2 strany** | Taháček, kalkulačka | 0 inline (jen cover hero) | Cover s background image, content stránka jen typografie + ikony |
| **3 strany** | Krátký taháček, srovnání | 0–1 inline | Cover hero (povinné) + 1 inline na content (volitelné) + CTA hero (povinné) |
| **4–5 stran** | Quick-start, krátká šablona | 1–2 inline | Cover hero + 1 inline na střední stránce + CTA hero |
| **6–7 stran** | Audit, případová studie | 2–3 inline | Cover hero + 2 inline na strategických místech + CTA hero |
| **8–12 stran** | Mini-průvodce | 3–4 inline | Cover + inline každé 3 stránky + CTA |
| **13–20 stran** | Workbook, dlouhý průvodce | 5–7 inline | Cover + inline každé 3-4 stránky + quote spread × 1 + CTA |
| **20+ stran** | Mini-kurz, knihovna příkladů | 8+ inline | Cover + chapter openery s hero image + inline každé 3-4 stránky + CTA |

### Klíčové principy (společné pro všechny délky)

- **Cover + CTA mají VŽDY hero imagery** (background + overlay) bez ohledu na délku magnetu — i 1stránkový taháček musí mít vizuálně silný cover
- **Inline image jen na content stránkách** — Audit, Checklist, Comparison Table, Quote spread mají vlastní vizuální logiku, NEpřidávej do nich foto
- **Nikdy 2 sousední content stránky s inline foto** — porušuje rytmus
- **Pro 3-stránkové magnety** vyber jednu strategii: buď cover-only (silný cover hero, pak typografie), nebo trio (cover + 1 inline + CTA hero) — žádný mix
- **Pro stránky bez fotek** kompenzuj vizuální váhu **silnou typografií, ikonami v gridu, barevnými boxy** (callout, ROI, mýty/fakta) — nikdy "zeď textu"

### Strategická místa pro inline fotky

Když máš omezený počet fotek, vlož je tam, kde mají **největší vliv**:

1. **První content stránka** (po úvodu) — udává tón celého magnetu
2. **Strana se silným tvrzením** (klíčový aha moment, kontroverzní názor) — fotka tvrzení dramatizuje
3. **Případová studie / Story** — fotka klienta nebo situace (s GDPR souhlasem, jinak `[PLACEHOLDER]`)
4. **Závěrečná content stránka** před CTA — emoční vrchol

---

## Unsplash fallback (když brand nemá vlastní fotky)

Pokud `/documents/brand/products/[slug]/images/` neobsahuje vhodné fotky, **fallback na Unsplash**. Skill MUSÍ projít tento workflow, aby zachoval brand konzistenci a dodržel licenční pravidla.

### Workflow vyhledávání

#### 1. Sestav search query z Brand DNA

Z `brandDNA.md` extrahuj:
- **Mood words** (sekce 1 ESENCE → "Emoční tón", sekce 7 SHRNUTÍ) — např. "klidný, prémiový", "empatický, hřejivý", "sebevědomý, energický"
- **Photography style** (z sekce 5 nebo 7, pokud popisuje vizuální preferenci) — např. "candid lifestyle, natural light"
- **ICP situace** (sekce 2 IDEÁLNÍ ZÁKAZNÍK → "Kdo je") — např. "freelancer, woman, home office"

Sestav 3 search queries pro každou roli:

| Role v magnetu | Query template | Příklad pro Money Reset |
|----------------|----------------|--------------------------|
| Cover hero | `[ICP] + [primary mood]` | `freelance woman calm` |
| Inline content | `[ICP situation] + [topic]` | `journal writing reflection` |
| CTA / endcap (transformace) | `[transformation symbol] + [warm mood]` | `golden sunrise mountains hope` |

#### 2. Otevři Unsplash search přes Chrome plugin

```
https://unsplash.com/s/photos/[search-query]
```

#### 3. Extrahuj kandidáty s alt texty

```javascript
// Najdi všechny img elementy a vyfiltruj jen free
const imgs = Array.from(document.images);
const free = imgs
  .map(i => {
    const src = i.currentSrc || i.src;
    const m = src.match(/images\.unsplash\.com\/photo-([a-f0-9-]+)/);
    return m ? { id: m[1], alt: (i.alt||'').slice(0, 80) } : null;
  })
  .filter(Boolean);
```

**KRITICKÉ:** Vyfiltruj jen `images.unsplash.com/photo-` (free). Vyřaď `plus.unsplash.com/premium_photo-` (placené, vrátí 404 bez auth).

#### 4. Vyber 1 podle alt textu match

Vyber kandidáta jehož alt text nejvíc souzní s tvým use case (např. pro "calm woman journaling" hledej "person writing on paper").

#### 5. Ověř URL přes HEAD request

```javascript
fetch(`https://images.unsplash.com/photo-${id}?w=2400&q=85&auto=format&fit=crop`, {method:'HEAD'})
  .then(r => ({status: r.status, ct: r.headers.get('content-type')}));
```

Status MUSÍ být **200** a Content-Type **image/jpeg**. Pokud 404, kandidát je premium nebo deprecated — vyber jiného.

#### 6. Detekuj aspect ratio kandidáta

```javascript
new Promise(resolve => {
  const img = new Image();
  img.onload = () => resolve({ w: img.naturalWidth, h: img.naturalHeight, ratio: img.naturalWidth/img.naturalHeight });
  img.src = `https://images.unsplash.com/photo-${id}?w=400&q=80&auto=format&fit=crop`;
});
```

Mapuj ratio → kategorii (portrait / landscape / square / panorama / vertical) a podle toho zvol layout (viz tabulka výše).

### Použití v HTML

URL šablona pro embed:
```css
url('https://images.unsplash.com/photo-{id}?w=2400&q=85&auto=format&fit=crop')
```

Parametry:
- `w=2400` — šířka (pro A4 print 300 DPI ideální 2400px, pro 150 DPI draft stačí 1200)
- `q=85` — JPEG quality (lossy, sweet spot)
- `auto=format` — Imgix vybere optimální formát (WebP / AVIF / JPEG)
- `fit=crop` — ořez na požadovanou šířku

### Pravidla pro Unsplash fallback

- **Vždy ověř host** před embedem — `images.unsplash.com` = OK, `plus.unsplash.com` = vyřaď
- **Konzistence napříč magnetem** — všechny Unsplash fotky v jednom magnetu by měly mít **stejný mood** (stejné světlo, stejná paleta, stejná kompozice). Když to nejde z jednoho photographer/series, drž alespoň konzistentní téma a barevnou tonalitu.
- **Atribuce** — Unsplash 2.0 license neviezduje atribuci, ale **dobrá praxe** je v poslední (CTA) stránce nebo footer impressum přidat *"Photos: Unsplash"*. Pro lead magnety je to volitelné.
- **Komerční použití** — Unsplash povoluje free komerční použití, ale **nepoužívej fotky lidí** k reklamě produktů, které tito lidé neschválili (právní riziko v některých jurisdikcích). Pro lifestyle a abstract pozadí je to bezpečné.

### Komentář v HTML pro budoucnost

Když vložíš Unsplash fotku, přidej HTML komentář se zdroji aby další update věděl:

```html
<!-- Fallback Unsplash photo (free license)
     Search: "freelance woman calm"
     Photo ID: 1456324504439-367cee3b3c32
     Alt: "person writing in book"
     Když brand získá vlastní fotky, vyměň za /documents/brand/products/[slug]/images/cover.jpg -->
```

Tím skill ví, že je to dočasný fallback a má být upgrade na brand-specific asset.

### Kde vložit (per typ stránky)

| Typ stránky | Inline image |
|-------------|--------------|
| Content (intro téma) | Hero image nahoře (max-height 35-40%) |
| Content (case story) | Foto klienta / situace pod heading |
| Content (autoritní) | Portrét autora vedle textu (split 50/50) |
| Chapter opener | Volitelně full-bleed image jako Variant B |
| Audit, Checklist, Comparison | NIKDY inline foto — narušuje strukturu |

### Zdroje inline fotek

1. **Brand-specific** (preferováno): `/documents/brand/products/[nazev-produktu]/images/` — produktové fotky, founder portréty (jako `pavel.jpg`)
2. **Unsplash free** — kontrola hostu (`images.unsplash.com`, ne `plus.unsplash.com`)
3. **AI generated** přes Image Lead Magnet Generator (pokud uživatel chce custom estetiku)

### Pravidla pro brand fotky

Pokud `/documents/brand/.../images/` obsahuje founder portréty (jako CliqSales `founders/pavel.jpg`):

- Použij na stránku **autoritního příběhu** ("Kdo jsem", "Náš příběh", "O nás")
- Split layout 40/60 — foto 40% šířky, text 60%
- `object-position: top` aby nebyl ořezaný obličej
- `border-radius: var(--radius-md)` pro premium feel

```css
.founder-split {
  display: grid;
  grid-template-columns: 40% 1fr;
  gap: var(--space-6);
  align-items: center;
}

.founder-portrait {
  width: 100%;
  aspect-ratio: 4/5;
  object-fit: cover;
  object-position: top;
  border-radius: var(--radius-md);
}
```

---

## Cover stránka — speciální pravidla

Cover je **emoční impact první vrstvy** — určuje, jestli čtenář otevře PDF nebo ho odloží. Podléhá přísnějším pravidlům než interní stránky.

### Co na cover PATŘÍ

- **Logo** — POVINNÉ, pokud existuje v `/documents/brand/logo.svg` nebo `/documents/brand/logo.png` (nebo .jpg, .webp). Top-left typicky, výška 32–48pt. Na hero/dark variant zachovat originál nebo použít white/inverted variantu pokud existuje. Logo je **základní brand identita** — bez něj cover vypadá generic. Skill MUSÍ logo vždy vyhledat a vložit, pokud je dostupné.
- **Title** — dominantní, 36–64pt
- **Subtitle** — 1 řádek (max 1.5 řádku), rozšiřuje title
- **Brand mark** (jako fallback **POUZE pokud logo neexistuje**) — jméno značky v small caps, top-right
- **Eyebrow** — kategorie/persona ("Taháček pro freelancerky", "Pro coaches"), max 1 řádek + ikona
- **Author footer** — jméno autora + role/autorita ("certifikovaná financial coach · 200+ klientek")
- **Hero image** (volitelně) — full-bleed s overlay

### Logo pravidla (cover)

```css
.cover-logo {
  height: clamp(28pt, 4vw, 48pt);
  width: auto;
  object-fit: contain;
}

/* Na světlé cover */
.cover--text .cover-logo {
  /* bez filteru — použít původní barvu loga */
}

/* Na tmavém cover (gradient/hero) */
.cover--hero .cover-logo,
.cover--dark .cover-logo {
  /* Pokud má brand bílou variantu, použij ji
     Jinak: filter: brightness(0) invert(1); — pouze pokud je logo single-color */
  filter: brightness(0) invert(1);
}
```

**Pokud má značka více variant loga** (color, monochrome, white), zvol podle pozadí cover:
- Tmavý hero cover → bílá / monochrome inverted varianta
- Světlý text cover → barevná / original varianta

**Pokud logo není dostupné**, ponech jen brand mark (text). Lepší žádné logo než deformované.

### Co na cover NIKDY NEPATŘÍ

⛔ **Tech meta info:**
- Počet stran ("12 stran", "2 strany")
- Čas čtení ("15 minut", "5 minut čtení")
- Tiskové info ("Vytištěno na 1 stránku", "Print-ready")
- Datum vydání nebo version ("v1.2", "Edition 2024")
- Page number / číslo stránky
- ISBN, copyright řádky, file format zmínky

⛔ **Marketing pill / badge:**
- "Magnet zdarma", "Free Guide", "Ebook", "Workbook" jako pill/chip element
- Tato spam-like dekorace **degraduje vizuální kvalitu** — vypadá jako infomercial / generic ebook template
- Místo toho: nech logo + autora promluvit. Pokud chceš signalizovat "free", dej to do podnadpisu přirozeně ("Stáhni si zdarma průvodce…") nebo do CTA na landing page

⛔ **Další marketing zbytky:**
- Trackovací parametry / UTM
- Watermarky ("DRAFT", "DO NOT SHARE")

⛔ **Layout chaos:**
- Více než 1 hero element (pokud je hero image, nejsou další obrázky)
- Cover divided na 4+ zón (cover má max 3 vertikální zóny: header / main / footer)

**Důvod zákazu meta info:** Prémiové brandové publikace (Vogue, NYT Magazine, Aesop catalogues, Linear product docs) na cover NIKDY nedávají počet stran ani čas čtení. Degraduje to vnímání z **artefaktu hodný uschování** na **utility dokument k odhození po přečtení**. Meta info má své místo v Table of Contents nebo footer interních stránek.

Pokud chceš čtenáře informovat o čase nebo formátu, dej to **přirozeně do podnadpisu** ("Rychlá kartička, kterou si vytiskneš") — ne jako tech řádek.

---

## Ověření před doručením

Před vyrenderováním PDF zkontroluj každou stránku proti tomuto checklistu:

- [ ] Nadpisy jsou velké a dominantní (cover ≥ 36pt, chapter ≥ 28pt)
- [ ] Vizuální hierarchie má jen 3 úrovně
- [ ] Každý feature grid má ikony (ne jen text)
- [ ] Mýty/Fakta používají × a ✓ ikony
- [ ] Bullety mají ikony (ne klasické odrážky)
- [ ] Pravidlo jednoho vizuálního zdroje na stránku dodrženo
- [ ] Kontrast textu vs. pozadí ≥ 4.5:1
- [ ] Padding stránky ≥ 32pt z boků, ≥ 48pt shora/zdola
- [ ] Žádné animace, žádný JS
- [ ] Page breaks správně (chapter opener = nová stránka, feature card neporušená)
- [ ] Čistota — minimálně 20% volné plochy
- [ ] **Cover NEOBSAHUJE počet stran, čas čtení, datum, version, page number, tisk info**
- [ ] **Cover má max 3 vertikální zóny** (header, main s title+subtitle, footer s author)
- [ ] **Cover hero image má dostatečně silný overlay** (rgba 0.78–0.92 na tmavé části gradient pro čitelnost textu)
- [ ] **Cover má logo** (pokud existuje v brand assets) — barva sladěná s pozadím
- [ ] **Žádná stránka NEPŘETÉKÁ** A4 (210×297mm) — `overflow: hidden` na `.page`, padding ≥ 32pt boční / 48pt vertikální
- [ ] **Density limity dodrženy** (cover max title+subtitle, content max H2+lead+6 bullets+aha box, feature grid max 6 karet, audit max 6 otázek per stránka)
- [ ] **Inline obrázky mají `max-height` constraint** (50% pro hero, 35% pro doprovodné)
- [ ] **Inline obrázky mají `aspect-ratio`** — portrait `3/4` nebo `4/5`, landscape `16/9` nebo `3/2`
- [ ] **Vizuální rytmus**: pokud je magnet 8+ stran, vlož inline foto každé 3-4 stránky (ne na auditech, checklistech, comparison)
- [ ] **POVINNÝ overflow re-check po každé úpravě** — projdi všechny stránky, žádná nesmí přetékat. Pokud ano → zmenši font/spacing/zkrať text → znovu zkontroluj
- [ ] **Aspect ratio detekován u všech inline fotek** — portrait / landscape / square / panorama / vertical → odpovídající layout
- [ ] **Počet inline fotek odpovídá délce magnetu** (1-2 strany: 0, 3 strany: 0-1, 4-5: 1-2, 6-7: 2-3, 8-12: 3-4, 13+: 5+)
- [ ] **Unsplash fallback** (pokud použit): host `images.unsplash.com` (ne `plus.unsplash.com`), HEAD 200, HTML komentář s atribucí, konzistentní mood napříč magnetem

Bez splnění checklistu není stránka připravena.
