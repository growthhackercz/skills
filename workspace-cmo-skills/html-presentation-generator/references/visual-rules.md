# Visual Rules Reference

Tento soubor obsahuje **POVINNÁ vizuální pravidla**, která musí dodržovat každá prezentace. Bez jejich dodržení je výstup NEAKCEPTOVATELNÝ.

**Načti tento soubor když:**
- Začínáš design jakéhokoliv slidu (typografie, layout, hierarchie)
- Pracuješ s obrázky (hero, split, inline, lidé, produkty)
- Řešíš kontrast, čitelnost nebo whitespace
- Volíš mezi hero a inline obrázkem

---

## 1. Nadpisy — BIG, BOLD, BEAUTIFUL

Nadpisy jsou hlavní vizuální element každého slidu. Musí být VELKÉ a dominantní — první věc, kterou divák uvidí.

```css
h1 { font-size: clamp(3rem, 8vw, 6rem); line-height: 1.05; letter-spacing: -0.035em; }
h2 { font-size: clamp(2.2rem, 6vw, 4.5rem); line-height: 1.1; letter-spacing: -0.03em; }
h3 { font-size: clamp(1.4rem, 3vw, 2.4rem); line-height: 1.15; }
```

**Pravidla:**
- Minimum: h1 `clamp(3rem, 8vw, 6rem)`, h2 `clamp(2.2rem, 6vw, 4.5rem)`. Pokud nadpis nevypadá jako hlavní prvek slidu, je příliš malý.
- **Font-weight NIKDY nehardcoduj** — vždy čti z DESIGN.md typography tokenů. Bez DESIGN.md použij font-weight fontu (regular/medium/semibold dle fontu).
- Velký negativní letter-spacing (-0.025em až -0.04em) pro display sizes.

---

## 2. Layout a vertikální centrování

```css
.slide-content {
  padding: clamp(3rem, 6vw, 6rem);   /* min 3rem, ne 2rem */
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;            /* POVINNÉ — obsah uprostřed */
  min-height: 100%;
}
```

**Pravidla:**
- **ŽÁDNÝ `max-width`** na slide-content — vytváří úzký sloupec s prázdnými okraji.
- **Padding minimum 3rem** — na widescreen monitorech 2rem vypadá utlačeně.
- **Vertikální centrování povinné.** Obsah nesmí viset nahoře s prázdnem dole.
- **Textový odstavec:** `max-width: 70ch` (čitelnost), ale **nadpisy bez limitu**.
- **Split layout:** dvě poloviny, každá 50% minus gap.
- **Grid karet:** roztáhne se na celou šířku.

---

## 3. Hero (full-bleed) obrázky — BIG, BOLD, BEAUTIFUL

Pokud má obrázek landscape orientaci a šířku ≥ 1200px, použij ho jako celoplošné pozadí slidu.

```css
.slide-hero {
  background-size: cover;
  background-position: center;
  position: relative;
}
/* Overlay pro čitelnost — POVINNÝ */
.slide-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg,
    rgba(5,13,24,0.92) 0%,
    rgba(10,22,40,0.7) 50%,
    rgba(5,13,24,0.92) 100%);
  z-index: 1;
}
.slide-hero .slide-content { position: relative; z-index: 2; }
```

**Pravidla:**
- **Overlay je POVINNÝ.** Nikdy text přímo na obrázek bez overlay.
- **Typ overlay:**
  - Tmavý obrázek → lehčí overlay `rgba(0,0,0,0.3)`.
  - Světlý obrázek → silnější `rgba(0,0,0,0.6)` nebo brand color s opacity.
  - Barevný brand → `rgba(brand,0.7)` pro brand feel.
- **Text vždy bílý** s `text-shadow: 0 2px 30px rgba(0,0,0,0.5)`.
- **Minimální obsah:** nadpis + max 1 řádek podnadpisu.
- **Použij sparingly** — max 3–4 hero slidy v celé prezentaci (title, section dividers, CTA).

---

## 4. Kdy použít hero vs. inline obrázek

| Obrázek | Použití |
|---------|---------|
| Landscape, ≥ 1200px, kvalitní | → Full-bleed hero pozadí |
| Portrait nebo čtvercový | → Inline v obsahu, `max-height: min(50vh, 400px)` |
| Screenshot / UI | → Inline s rámečkem a stínem, NIKDY jako pozadí |
| Logo | → Inline, `max-height: min(30vh, 200px)`, na title + closing |
| Nízká kvalita / malý rozměr | → Inline zmenšený, nebo vůbec nepoužívat |

---

## 5. Fotky s bílým pozadím — čisté blendování

```css
/* SPRÁVNĚ — fotka splývá se slidem */
.product-photo {
  background: transparent;
  border: none;
  box-shadow: none;
  mix-blend-mode: multiply;   /* odstraní bílé pozadí */
}
/* Na tmavém slidu */
.dark .product-photo, .hero .product-photo {
  mix-blend-mode: screen;
  filter: drop-shadow(0 30px 60px rgba(0,0,0,0.6));
}
```

**Pravidla:**
- Bílá fotka na SVĚTLÉM slidu → žádný stín, border, ani border-radius. `mix-blend-mode: multiply`.
- Bílá fotka na TMAVÉM slidu → `mix-blend-mode: screen` NEBO bílý rámeček, NEBO zvol fotku s průhledným pozadím.
- Fotka s barevným/tmavým pozadím na světlém slidu → jemný stín a border-radius OK.

---

## 6. Obrázky s lidmi a obličeji

- **NIKDY neořezávej obličeje.** Pokud fotka obsahuje osobu, musí být vidět celý obličej. `object-position: top` nebo `object-fit: contain` místo `cover`.
- **Portraits preferuj na výšku.** V split layoutu vypadá portrétní fotka lépe než landscape ořezaný do malého rámečku.
- **Emotivní fotky (rodina, děti, péče)** → použij jako hero background, nikdy v malém rámečku.

```css
.split-image {
  width: 45%;
  height: 100vh; height: 100dvh;
  object-fit: cover;
  object-position: center top;   /* NIKDY neořezat hlavu */
}
```

---

## 7. Split layout — obrázky NA VÝŠKU

Když je slide rozdělen na dva sloupce (text + obrázek), obrázek MUSÍ být na výšku a zabírat celou výšku slidu:

- **SPRÁVNĚ:** Obrázek na výšku, `height: 100vh`, `object-fit: cover` — vyplní polovinu.
- **ŠPATNĚ:** Malý landscape obrázek uprostřed sloupce s prázdnem nahoře a dole.

Pokud je dostupný jen landscape, raději:
1. Použij ho jako hero background na celý slide.
2. Ořízni na portrait (pokud obsah dovolí).
3. Zvol jiný layout (grid, full-width).

---

## 8. Pravidlo jednoho vizuálního zdroje

NIKDY nekombinuj na jednom slidu:
- Background image + další inline fotky (přehlcení).
- Víc než 2–3 fotky na jednom slidu (vizuální chaos).
- Hero background + karty s fotkami uvnitř.

**Jeden slide = jeden vizuální důraz.**

| Layout | Max obrázků | Pravidlo |
|--------|------------|---------|
| Hero (full-bleed) | 1 (pozadí) | Žádné další fotky, jen text |
| Split (text + foto) | 1 | Velká fotka na jedné straně |
| Grid/showcase | 2–3 | Stejná velikost, rovnoměrně |
| Text-heavy | 0–1 | Malý doprovodný obrázek nebo ikona |

---

## 9. Velikost obrázků — nikdy "utopené"

Obrázky musí mít vizuální váhu. Malý obrázek ztracený v prázdném prostoru = chyba.

- **Split:** obrázek min. 40–50% šířky slidu, `min-height: 50vh`.
- **Karta s fotkou:** fotka vyplňuje min. 70% plochy karty.
- **Dvě fotky vedle sebe:** obě stejné, dohromady min. 50% plochy slidu.
- **Min. 200px šířka.** Menší → radši nepoužívej.

---

## 10. Ikony místo textu

Prezentace nesmí být "zeď textu".

- **Feature grid** → POVINNĚ ikona + nadpis + 1 řádek popisu v každé kartě.
- **Bullet pointy** → ikony místo klasických odrážek (check, arrow-right, zap, star).
- **Statistiky** → velké číslo + ikona + popisek.
- **Kontrasty (starý vs. nový)** → ✕ (červená) vs. ✓ (zelená).
- **4+ textových bodů bez vizuálu** → přidej ikony nebo rozděl na víc slidů.

**Zdroje ikon:**
- **Preferovaný:** `references/icons.md` (35 inline SVG, offline).
- Lucide (https://lucide.dev/icons/) — 1600+ ikon.
- Phosphor, Heroicons, Tabler — alternativy.

**Vždy inline SVG v HTML, nikdy externí závislosti za běhu.**

```css
.icon {
  width: clamp(24px, 3vw, 48px);
  height: clamp(24px, 3vw, 48px);
  stroke: currentColor;        /* nebo fill: var(--accent) */
}
```

**Pravidla:**
- Konzistence: jedna knihovna v celé prezentaci, nemíchej styly.
- Každá ikona musí komunikovat koncept — žádné dekorace bez významu.

---

## 11. Kontrast a čitelnost

- **Text na tmavém pozadí:** vždy `#ffffff` nebo `#f0f0f0`, nikdy šedivý pod `#cccccc`.
- **Text na světlém pozadí:** vždy `#1a1a1a` nebo tmavší, nikdy šedivý nad `#555555`.
- **Akcentové barvy (gold, žlutá) na tmavém pozadí:** OK pro labels/tagy, NIKDY pro body text.
- **Sub-text a labels:** kontrast min. 4.5:1 (WCAG AA).
- **Hero slidy:** `text-shadow: 0 2px 20px rgba(0,0,0,0.5)` pro extra čitelnost.

---

## 12. Vizuální hierarchie — 3 úrovně

Každý slide musí mít 3 úrovně důležitosti:

1. **Primární** — nadpis nebo hlavní číslo (největší, nejtučnější, nejvíc kontrastní).
2. **Sekundární** — podnadpis, klíčový text, obrázek (střední velikost).
3. **Terciární** — body text, labels, drobné detaily (nejmenší, nejlehčí).

Víc než 3 úrovně = slide je příliš komplexní → rozděl na 2.

---

## 13. Čistota a prostor

- **Min. 20% volného prostoru** na každém slidu. Prázdný prostor = designový element.
- **Karty/boxy:** max. 3 vedle sebe na full-width, 2 na half-width.
- **Mezi kartami:** vždy `gap: clamp(1rem, 2vw, 2rem)`.
- **Badges/tagy:** NIKDY nepřilepuj na text — `margin-top: clamp(0.75rem, 1.5vw, 1.5rem)`.
- **Mezi body textem a badges/CTA:** min. 1rem.
- **Obrázky v kartách:** vždy `margin-bottom` nebo `gap` od textu pod nimi.

---

## 14. Density limity per slide

| Typ | Maximum |
|-----|---------|
| Title | 1 heading + 1 subtitle + tagline |
| Content | 1 heading + 4–6 bodů NEBO 1 heading + 2 odstavce |
| Feature grid | 1 heading + max 6 karet |
| Code | 1 heading + 8–10 řádků kódu |
| Quote | 1 citát (max 3 řádky) + autor |

Obsah přesahuje? **Rozděl na víc slidů.** Nikdy necpi, nikdy nescrolluj.
