# Orientace stránky — výška vs. šířka

Lead magnet může být **na výšku (portrait, A4 210×297mm)** nebo **na šířku (landscape, A4 297×210mm)**. Skill se rozhoduje podle typu obsahu — orientace má dopad na čtenost, vnímání a způsob konzumace.

---

## Výchozí volba: portrait (na výšku)

**95 % lead magnetů by mělo být na výšku.** Je to konvence, kterou čtenář očekává:

- Mobilní zobrazení — telefon je portrait, magnet se na něm čte přirozeně
- Tištěný formát — A4 portrait je standardní papír, klient si ho vytiskne a uloží
- Sloupcová sazba — text je čitelnější ve sloupci (60–70 znaků na řádek)
- Kompatibilita — všechny e-čtečky, e-mailové klienti, prohlížeče zobrazí portrait bez problémů

---

## Kdy zvolit landscape (na šířku)

Landscape **MÁ smysl jen v těchto specifických případech**:

### 1. Comparison Chart (Srovnání A vs. B)

**Důvod:** Tabulkové srovnání 3+ možností potřebuje široké sloupce. Portrait by zúžil sloupce a vznikly by nečitelné lomené řádky v každé buňce.

**Příklad:** "Stripe vs. Shopify vs. WooCommerce" se 4 sloupci a 12 kritérii.

**Vyhodnocení:**
- Sloupců > 3 → landscape
- Sloupců ≤ 2 → portrait stačí (rovněž čistší)

### 2. Kalkulačka s rozšířeným rozhodovacím stromem

**Důvod:** Pokud kalkulačka obsahuje horizontální flow ("zadej X → spočítej Y → interpretace Z" v 3-4 krocích vedle sebe), landscape umožní vidět celý flow najednou.

**Vyhodnocení:**
- Flow má 3+ horizontální kroky → landscape
- Vstup → výsledek (2 elementy) → portrait

### 3. Infographic / Datová vizualizace s časovou osou

**Důvod:** Timeline, gantt-style mapy, before/after split layouts s rozsáhlými prvky se vyplatí na šířku.

**Příklad:** "12-měsíční roadmap startupu" s 12 fázemi vedle sebe.

### 4. Workbook s wide-form cvičeními

**Důvod:** Některá pracovní cvičení (canvas-style, mind map, business model canvas) potřebují horizontální plochu. Workbook z principu funguje jako "papír na vyplňování", takže landscape může být pro něj přirozenější.

**Vyhodnocení:**
- Cvičení se skládají z buněk/zón v gridu (např. 3×4) → landscape
- Cvičení jsou seznamy / otázky → portrait

### 5. Slidové prezentace převedené do PDF

Pokud uživatel chce z prezentace vytvořit lead magnet (16:9 slidy), ponech landscape. Ale **typicky pro lead magnet je lepší prezentaci přepracovat na portrait** — čtenost na mobilu výrazně klesá u landscape PDF.

---

## Pro vs. proti per typ magnetu

| Typ magnetu | Default | Landscape OK když | Portrait je vždy lepší když |
|-------------|---------|-------------------|------------------------------|
| Checklist | **Portrait** | nikdy | vždy — je to seznam pro vytisknutí |
| Taháček | **Portrait** | nikdy | vždy — vejde se na 1-2 strany |
| Šablona | **Portrait** | wide-form business canvas | běžné textové šablony |
| Knihovna příkladů | **Portrait** | nikdy | screenshoty fungují stejně dobře |
| Mini-průvodce | **Portrait** | nikdy | čtení dlouhého textu na mobilu |
| Workbook | **Portrait nebo Landscape** | canvas-style cvičení v gridu | journaling, otázky, reflexe |
| Audit / Sebehodnocení | **Portrait** | nikdy | otázky se čtou shora dolů |
| Quick-start | **Portrait** | nikdy | day-by-day struktura |
| Srovnání A vs. B | **Landscape pokud 3+ sloupců** | tabulka >3 sloupců, >8 kritérií | 2 sloupce, krátké srovnání |
| Kalkulačka | **Portrait** | rozhodovací strom horizontálně | běžný formulář |
| Případová studie | **Portrait** | nikdy | příběh se čte vertikálně |
| Seznam zdrojů | **Portrait** | nikdy | kategorizovaný seznam |
| Scripty | **Portrait** | nikdy | dialog se čte shora dolů |
| Mini-kurz | **Portrait** | nikdy | sekvenční čtení po lekcích |

---

## Mixované orientace v jednom dokumentu

V některých případech může mít smysl **kombinovat orientace** uvnitř jednoho magnetu:

- Mini-průvodce má 12 stran portrait + 1 stranu landscape s velkým srovnáním tabulky
- Workbook má cover + úvod portrait + 5 stran landscape canvas cvičení + závěr portrait

**Pravidla pro mix:**
- **Cover, úvod, závěr (CTA)** = vždy portrait — společný úvodní/závěrečný rytmus
- **Speciální stránky** (canvas, srovnání, timeline) = landscape, pokud to zlepší čitelnost
- Maximum mix: 80 % portrait + 20 % landscape v jednom magnetu
- Změna orientace je pro čtenáře vizuálně rušivá — používej sparingly

V CSS pro mixované magnety:

```css
.page--portrait {
  width: 210mm;
  height: 297mm;
}

.page--landscape {
  width: 297mm;
  height: 210mm;
}
```

A v `@page` rules:

```css
@page portrait { size: A4 portrait; }
@page landscape { size: A4 landscape; }

.page--portrait { page: portrait; }
.page--landscape { page: landscape; }
```

---

## Jak skill volí orientaci

Skill v Kroku 1 (po načtení `00-strategie.md` z `lead-magnet-generator`) automaticky zvolí orientaci podle typu magnetu z tabulky výše:

```
1. Default = portrait
2. Pokud typ = "Srovnání A vs. B":
   → spočítej počet sloupců v tabulce (z markdown obsahu)
   → pokud > 3 → landscape
3. Pokud typ = "Workbook":
   → zkontroluj, jestli obsah obsahuje canvas-style cvičení
     (markdown vzor: tabulka s 3+ sloupci a 3+ řádky pro vyplnění)
   → pokud ano → landscape
4. Pokud typ = "Kalkulačka":
   → zkontroluj rozhodovací flow
   → pokud má 3+ horizontální kroky → landscape
5. Jinak → portrait
```

**Pokud je orientace nejasná**, polož uživateli:

> *"Tvůj magnet ti udělám na výšku (A4 portrait) — to je standard pro většinu lead magnetů, čte se dobře na mobilu i v tisku. Pokud chceš na šířku (např. pro tabulky se 4+ sloupci nebo wide canvas cvičení), řekni — ale 95 % lead magnetů má lepší výsledky na výšku."*

---

## Dopad na vizuální design

### Portrait

- Cover title `clamp(36pt, 6vw, 64pt)` — vejde se i delší název na 2 řádky
- Content split layout: stack (text nad obrázkem)
- Bullety: 1 sloupec
- Page padding: `var(--space-12) var(--space-8)` (větší shora/zdola)

### Landscape

- Cover title menší, max 48pt — méně vertikálního prostoru
- Content split layout: 50/50 (text vlevo, obrázek/diagram vpravo)
- Bullety: 2 sloupce možné, ale opatrně (čtení v dvou sloupcích na PDF je horší)
- Page padding: `var(--space-8) var(--space-12)` (větší zboku)
- Tabulky a grafy mají větší prostor — využij ho pro detail

```css
.page--landscape .feature-grid {
  grid-template-columns: repeat(4, 1fr);  /* místo 3 */
}

.page--landscape .content-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-8);
}
```

---

## Checklist před doručením

Před vyrenderováním ověř:

- [ ] Default je portrait, pokud není explicitní důvod na landscape
- [ ] Pokud landscape: skutečně využíváme šířku? (>50 % obsahu by se neměl vejít do portrait)
- [ ] Pokud mix: portrait/landscape stránky jsou v logickém pořadí (cover/úvod/závěr portrait)
- [ ] Webový čtenář na mobilu uvidí stránky čitelně i v landscape (text > 12pt)
- [ ] Tisk: landscape A4 = ležato, na obvyklé tiskárně to projde

---

## Příklady reálných lead magnetů — orientace

| Reálný magnet | Orientace | Důvod |
|---------------|-----------|-------|
| HubSpot 50-Page Marketing Guide | Portrait | Long-form text, mobile-friendly |
| Stripe Pricing Comparison | Portrait | 2-3 sloupce, vejde se |
| Bain & Company Industry Report | Portrait | Kombinace textu a grafů, čte se sekvenčně |
| Notion Templates | Portrait/Landscape mix | Cover portrait, canvas cvičení landscape |
| Y Combinator Startup School Deck | Landscape | Slidová prezentace |
| McKinsey Quarterly | Portrait | Magazine-style, dlouhý text |

**Závěr:** Když nevíš, je to portrait.
