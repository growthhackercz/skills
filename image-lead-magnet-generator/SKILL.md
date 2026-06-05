---
name: image-lead-magnet-generator
description: Vytvoří plně obrázkový PDF lead magnet — každá stránka A4 jako prémiový AI obrázek v duchu tvojí brand knihovny (brand-board, brand-kit, inspirace pro PDF). Na výšku i na šířku, tisková kvalita až 300 DPI. Před prvním generováním se zeptá, jakým systémem mají obrázky vznikat: vestavěný nástroj (vyžaduje OpenAI předplatné), GPT Image 2 přes OpenRouter, nebo GPT Image 2.0 přes FAL.ai.
category: marketing
status: ready
version: 1.1
publishedAt: "2026-05-13"
metadata: {"openclaw":{"requires":{"bins":["python3"]},"emoji":"🎨"}}
---

# Image Lead Magnet Generator

Generuje **plně vizuální A4 lead magnet** — každá stránka je prémiový designovaný obrázek vytvořený AI v duchu brandové vizuální knihovny. Žádné textové PDF s ikonami (na to je `html-lead-magnet-generator`), tady jsou stránky **kompozice** v editorial kvalitě, jako kdyby je dělal profesionální layout designér.

**Klíčové rysy:**
- Vstup z **brandové vizuální knihovny** (brand-board.png, brand-kit/, 08-inspirace-pro-pdf-materialy.png) — NE z DESIGN.md
- **Premium designer feel** — jako Phaidon, Wallpaper, Apple PDF reporty
- **Portrait i landscape** A4 — výchozí portrait (2480×3508), landscape pro 3+ sloupcová srovnání nebo wide canvases (3508×2480)
- **Maximální rozlišení 300 DPI** pro print kvalitu
- **GPT Image 2** výborně zvládá malé texty bez chyb (až 50+ slov per stránka, včetně diakritiky)
- **3 způsoby generování obrázků** (volba v Krok 0.2 — vyžaduje schválení uživatele):
  1. **Vestavěný nástroj pro vytváření obrázků** — doporučená volba, generuje pomocí GPT Image 2 přes uživatelovo OpenAI předplatné napojené na Command Center. Pokud OpenAI předplatné chybí, fallback na volbu 2️⃣
  2. **GPT Image 2 přes OpenRouter** — pro uživatele s aktivním OpenRouter předplatným (vyžaduje `OPENROUTER_API_KEY`); typický fallback, pokud chybí OpenAI
  3. **GPT Image 2.0 přes FAL.ai** — pro hi-end tisk až 4096 px nebo dev/test (vyžaduje `FAL_KEY`)
- Batch review HTML grid pro schválení + selektivní regenerace

## Kdy použít

Použij když uživatel chce:
- **Plně vizuální** lead magnet — každá stránka jako designovaný obrázek/poster s editorial kvalitou
- Magnet ve stylu **brandové vizuální knihovny** (brand-board mood, brand-kit estetika)
- "Lookbook", "magazine PDF", "obrázkové stránky", "vizuální průvodce"
- Skombinovat **produktové fotky** s designovými layouty (kontrolní seznamy, infografiky, sekvence kroků)

Pro **textové designové** PDF (typografie, ikony, tabulky) použij `html-lead-magnet-generator`.

## Vstup

1. **Markdown obsah** — typicky `/documents/lead-magnets/[nazev-magnetu]/03-obsah.md` z `lead-magnet-generator`
2. **Strategie** — `/documents/lead-magnets/[nazev-magnetu]/00-strategie.md`
3. **Brand DNA** — `/documents/brand/brandDNA.md` (markdown report z `brand-dna` skillu)
4. **Product DNA** — `/documents/brand/products/[nazev-produktu]/productDNA.md`
5. **Brand vizuální knihovna** (POVINNÁ):
   - `/documents/brand/brand-board.png` — moodboard značky (PRIMÁRNÍ vizuální reference)
   - `/documents/brand/brand-kit/` — složka s brand kit mockupy (nepovinný, ale silně doporučený)
   - **PDF specific reference**: `/documents/brand/brand-kit/08-inspirace-pro-pdf-materialy.png` (KRITICKÁ pokud existuje — definuje layout language pro PDF)
6. **Produktové fotografie** — `/documents/brand/products/[nazev-produktu]/images/` (volitelné)
7. **API klíč podle zvoleného systému** (Krok 0.2). Klíče se spravují v **Nastavení → Integrace**:
   - **Vestavěný nástroj** → vyžaduje OpenAI předplatné připojené v integracích (typicky `OPENAI_API_KEY` env). Pokud chybí, doporuč fallback na volbu 2️⃣
   - **GPT Image 2 přes OpenRouter** → `OPENROUTER_API_KEY` v env
   - **GPT Image 2.0 přes FAL.ai** → `FAL_KEY` v env

## Workflow

### Krok 0 (POVINNÝ): Načtení kontextu

Krok 0 má tři fáze: **(0.1)** detekce existujícího magnetu, **(0.2)** výběr systému pro generování obrázků (vyžaduje schválení uživatele), **(0.3)** načtení brand vizuální knihovny + strategie + obsahu.

#### 0.1 — Detekce existujícího magnetu

Pokud `/documents/lead-magnets/[slug]/page-plan.json` existuje, jsou zde dříve vygenerované draft stránky (`_pages/`) nebo finální (`_pages-final/`):

| Co existuje | Skill nabídne |
|-------------|---------------|
| jen `page-plan.json` | Pokračovat na Krok 5 (batch generuj draft) |
| + `_pages/page-XX.png` | Pokračovat na Krok 6 (batch review) — backend načti z page-plan |
| + `_pages-final/page-XX.png` | Pokračovat na Krok 8 (komponuj PDF) — backend načti z page-plan |
| nic z toho | Pokračovat normálně na 0.2 + 0.3 |

**Pokud existující page-plan obsahuje pole `backend`** → přeskoč 0.2 (systém už byl zvolen v předchozím běhu). Pokud uživatel chce změnit, polož otázku **lidsky** podle uloženého slug → human label:

| `backend` v page-planu | Co řekneš uživateli |
|------------------------|---------------------|
| `openclaw` | „Magnet máš nastavený na vestavěný nástroj. Chceš ponechat, nebo přepnout?" |
| `openrouter` | „Magnet jede přes GPT Image 2 / OpenRouter. Chceš ponechat, nebo přepnout?" |
| `fal` | „Magnet jede přes GPT Image 2.0 / FAL.ai. Chceš ponechat, nebo přepnout?" |

#### 0.2 — Jakým systémem chceš vygenerovat obrázky

**🛑 Vyžaduje schválení uživatele. Skill MUSÍ zastavit a vyčkat na výběr — NEPOKRAČOVAT na 0.3 dokud uživatel explicitně nevybere systém.**

Před prvním generováním obrázků polož uživateli otázku **lidským jazykem** (žádné slovo „backend" navenek). Vypiš:

```
═══════════════════════════════════════════════════════════
  JAKÝM SYSTÉMEM CHCEŠ VYGENEROVAT OBRÁZKY?

  1️⃣  VESTAVĚNÝ NÁSTROJ PRO VYTVÁŘENÍ OBRÁZKŮ — doporučeno
      • Použije GPT Image 2 přes tvoje OpenAI předplatné
      • Funguje, jen pokud máš v integracích připojené OpenAI předplatné

  2️⃣  GPT IMAGE 2 PŘES OPENROUTER
      • Stejný GPT Image 2 model, jen účtování jde přes tvůj OpenRouter účet
      • Typický fallback, když uživatel nemá OpenAI předplatné
      • Předpoklad: vyplněný OPENROUTER_API_KEY v nastavení integrací
      • Cena: cca $0.04–0.20 / stránku (≈ $1–2 za 10-stránkový magnet)

  3️⃣  GPT IMAGE 2.0 PŘES FAL.AI
      • Přímé napojení na FAL.ai (špička pro tiskovou kvalitu až 4096 px)
      • Vhodné pro velkoformátový tisk nebo dev/test
      • Předpoklad: vyplněný FAL_KEY v nastavení integrací
      • Cena: cca $0.03 draft / $0.10 final / $0.20 hi-end za stránku (≈ $1.40 za 10-stránkový magnet)

═══════════════════════════════════════════════════════════

Doporučuju 1️⃣, pokud máš v integracích připojené OpenAI předplatné.
Bez OpenAI je standardní volba 2️⃣ (OpenRouter).

Která volba? (1 / 2 / 3)
```

**Po výběru:**
1. **Ulož volbu** do `page-plan.json` jako `backend: "openclaw" | "openrouter" | "fal"` (interní pole — uživatel ho nikdy nevidí). Všechna další volání `generate-images.py` použijí tento flag.
2. **Ověř, jestli má skill přístupový klíč** podle volby. **API klíče se v CliqSales spravují v Nastavení → Integrace** (ne v konfiguraci skillu).
   - `1` (vestavěný nástroj) → musí existovat OpenAI klíč (typicky `OPENAI_API_KEY` env). Pokud chybí → STOP a vysvětli **lidsky**: *„Tato volba potřebuje aktivní OpenAI předplatné připojené v integracích. Klíč zatím nemáš nastavený. Chceš ho doplnit (Nastavení → Integrace → OpenAI), nebo radši zvolíš 2️⃣ (OpenRouter)?"*
   - `2` (OpenRouter) → musí existovat `OPENROUTER_API_KEY` v env. Pokud chybí → STOP a vysvětli **lidsky**: *„Tato volba potřebuje vyplněný klíč pro OpenRouter v integracích. Chceš ho zadat teď (Nastavení → Integrace → OpenRouter), nebo radši zvolíš jiný systém?"*
   - `3` (FAL) → musí existovat `FAL_KEY` v env. Pokud chybí → STOP a vysvětli **lidsky**: *„Tato volba potřebuje vyplněný klíč pro FAL.ai v integracích. Chceš ho zadat teď (Nastavení → Integrace → FAL.ai), nebo radši zvolíš jiný systém?"*
3. **Nikdy v komunikaci s uživatelem nepoužívej slovo „backend"** ani „OpenClaw" — místo toho „systém pro generování obrázků" / „vestavěný nástroj" / „volba".

⚠️ **NEPOKRAČOVAT na 0.3 bez explicitní volby + ověření klíče.**

#### 0.3 — Načti brand vizuální knihovnu, strategii a obsah

```
1. /documents/lead-magnets/[slug]/00-strategie.md       (YAML frontmatter — typ, orientace, slug, produkt_slug, ...)
2. /documents/lead-magnets/[slug]/03-obsah.md           (text obsah z lead-magnet-generator)
3. /documents/brand/brandDNA.md                         (markdown report — esence, hlas)
4. /documents/brand/brand-board.png                     (POVINNÝ — vizuální mood)
5. /documents/brand/brand-kit/08-inspirace-pro-pdf-materialy.png (KRITICKÝ pokud existuje — PDF layout language)
6. /documents/brand/brand-kit/*.png                     (ostatní mockupy — volitelné)
7. /documents/brand/products/[produkt_slug]/productDNA.md  (markdown report)
8. /documents/brand/products/[produkt_slug]/images/     (volitelné fotky produktu)
```

**Z `00-strategie.md` parsuj YAML frontmatter** (uložený lead-magnet-generatorem):

```yaml
typ: audit
orientace: portrait
delka_stran: 12
publikum_faze: solution-aware
produkt_slug: money-reset
slug: money-identity-audit
nazev: "Money Identity Audit"
```

Tato pole jdou přímo do `page-plan.json` (Krok 2) — žádný re-parsing volného textu.

**Pokud frontmatter chybí** (starší magnet bez strukturovaného YAML) → polož otázku uživateli a manuálně doplň `typ` + `orientace` před pokračováním.

**Pokud `brand-board.png` chybí** → STOP. Skill vyžaduje vizuální moodboard. Doporuč uživateli pustit `brand-image-generator` nebo `brand-dna` skill pro vytvoření brand boardu.

**Pokud `brand-kit/08-inspirace-pro-pdf-materialy.png` chybí** → skill funguje jen z brand-board, ale výsledek bude méně specifický pro PDF formát. Doporuč uživateli vygenerovat tento brand-kit asset (přes `brand-image-generator`).

**NIKDY nepoužívej DESIGN.md** — tento skill pracuje s **vizuální** knihovnou, ne design tokeny. DESIGN.md je doménou `html-lead-magnet-generator`.

### Krok 1: Sestav Style Directive z brand vizuální knihovny

Z brandových vstupů sestav **JEDNU konzistentní vizuální direktivu**, která se aplikuje na KAŽDÝ prompt napříč magnetem. Detailní extrakce v `{baseDir}/references/style-directive.md`.

Style Directive obsahuje:

```
STYLE DIRECTIVE (sděleno GPT Image 2 v každém promptu):

═══ COLOR PALETTE ═══
Primary: [HEX] — visible from brand-board
Secondary: [HEX]
Accent: [HEX]
Neutral light: [HEX]
Neutral dark: [HEX]

═══ TYPOGRAPHY ═══
Display font: [Name] (bold, condensed, serif/sans depending on brand)
Body font: [Name] (clean, readable)
Hierarchy: Display 60-80pt for hero text, body 11-12pt for paragraphs

═══ VISUAL LANGUAGE (z brand-board.png + 08-inspirace-pro-pdf-materialy.png) ═══
- Geometry: [rounded vs sharp, corners, organic vs precise]
- Layering: [flat vs depth, gradients, glows, shadows]
- Spacing: [generous vs dense, whitespace philosophy]
- Photography style: [editorial portrait vs lifestyle vs abstract]
- Decorative elements: [accent lines, dividers, ornaments]

═══ MOOD ═══
- Adjectives from brand DNA section 1+5: [3-5 words]
- Reference brands implied: [Apple, Aesop, Wallpaper, Phaidon, Linear...]

═══ PDF-SPECIFIC LAYOUT LANGUAGE (z 08-inspirace-pro-pdf-materialy.png pokud existuje) ═══
- Card style: [bordered, shadow, gradient]
- Number/checkmark treatment: [large numerals, colored circles, gradient fills]
- Diagram style: [circular flow, linear timeline, split comparison]
- CTA panels: [solid color block, gradient, glassmorphic]
```

Tato direktiva se NIKDY nemění mezi stránkami — zajišťuje vizuální konzistenci napříč celým magnetem.

### Krok 2: Naplánuj sekvenci stránek + orientaci

Z **YAML frontmatteru `00-strategie.md`** přečti `typ` a `orientace` (Krok 0.3). Z `03-obsah.md` rozparsuj sekce. Vytvoř `page-plan.json` se zachováním backendu z Krok 0.2:

```json
{
  "magnet_type": "audit",
  "orientation": "portrait",
  "backend": "openclaw",
  "resolution": {
    "draft": [1240, 1754],
    "final": [2480, 3508]
  },
  "style_directive": "...",
  "pages": [
    { "n": 1, "type": "cover", "layout": "hero-portrait-overlay", ... },
    { "n": 2, "type": "intro-stats", "layout": "split-text-cards", ... },
    { "n": 3, "type": "agent-feature", "layout": "split-portrait-roi", ... }
  ]
}
```

**Pole `backend`** = volba uživatele z Krok 0.2 (`"openclaw" | "openrouter" | "fal"`). Při re-runu skill se podle tohoto pole rozhodne, jestli volá `image_generate`, OpenRouter API, nebo FAL.

#### Volba orientace

| Typ obsahu | Orientace | Důvod |
|------------|-----------|-------|
| Většina lead magnetů | **Portrait** (2480×3508) | Default — telefon, tisk, čitelnost |
| Srovnání A vs. B s 3+ sloupci | **Landscape** (3508×2480) | Široké tabulky |
| Workbook s wide canvas | **Landscape** | Mind maps, business model canvas |
| Timeline s 8+ fázemi | **Landscape** | Horizontální flow |
| Kalkulačka s rozhodovacím flow | **Landscape** | Sekvenční horizontální |

Pro mixované magnety (cover/intro portrait + 1 stránka landscape) zachovej max 20 % stránek v jiné orientaci než výchozí.

#### Layouty per typ stránky (page layouts)

Detailní specifikace v `{baseDir}/references/premium-layouts.md`. Hlavní typy:

- **cover-hero-overlay** — full-bleed image + gradient overlay + dominant title (jako Phaidon book covers)
- **cover-typographic** — typografická dominance, žádný hero image (Aesop catalogue feel)
- **intro-stats-cards** — title + 3 metric cards + úvodní odstavec
- **toc-numbered** — nadpis "Obsah" + očíslovaný seznam s page refs
- **chapter-opener-fullbleed** — full-bleed image + giant chapter number + title
- **content-split-portrait** — text levá strana 60% + portrait foto pravá 40%
- **content-image-top** — landscape image nahoře (40%) + text dole
- **feature-grid-cards** — 3-6 cards v gridu, každá s ikonou/číslem
- **myth-fact-comparison** — side-by-side red × vs. green ✓ s vysvětlením
- **quote-spread** — full-page citát s velkou typografií + atribuce
- **checklist-detailed** — 5-15 položek s checkbox + detailní popis
- **diagram-flow** — circulární nebo lineární diagram s ikonami v uzlech (jako "Náš Ekosystém AI" z 08-inspirace)
- **process-numbered-steps** — vertikální seznam očíslovaných kroků s ikonami a popisy
- **product-mockup** — produktový vizuál + benefits side panel
- **cta-gradient-panel** — full-bleed gradient + dominant title + button mockup
- **endcap-product** — full-bleed brand asset image (mockup ukazující produkt v kontextu)

**STOP** a ukaž page plan + style directive uživateli ke schválení.

### Krok 3: Připrav prompty per stránka

Pro každou stránku z page-plan vygeneruj GPT Image 2 prompt podle šablon v `{baseDir}/references/premium-layouts.md`. Každý prompt má 5 částí:

```
═══ [1. STYLE DIRECTIVE] ═══
{kompletní brand style directive z Kroku 1}

═══ [2. ORIENTATION + RESOLUTION] ═══
A4 portrait page design, aspect ratio 2480:3508, 300 DPI print quality.
[nebo landscape: A4 landscape, 3508:2480]

═══ [3. LAYOUT TEMPLATE] ═══
Layout: {layout_name}
{layout_description z premium-layouts.md}

═══ [4. CONTENT] ═══
Heading text: "{přesný nadpis v češtině s diakritikou}"
Subheading: "{podnadpis}"
Body points: ["{bod1}", "{bod2}", "{bod3}"]
{visual elements per layout: ikona/číslo/foto reference}

═══ [5. NEGATIVE PROMPTS + DETAILS] ═══
- Premium editorial design quality, like Phaidon/Wallpaper/Apple PDF reports
- Generous whitespace, single dominant focal element
- NO watermarks, NO stock photo aesthetic, NO AI-obvious style
- NO multiple subjects, NO cluttered layouts
- Czech text MUST be rendered correctly with full diacritics (á, é, í, ó, ú, ů, ý, č, ď, ě, ň, ř, š, ť, ž)
```

Ulož prompty do `/documents/lead-magnets/[nazev-magnetu]/_prompts/page-XX.txt`.

### Krok 4: Připoj brand reference k promptům

GPT Image 2 přes FAL podporuje **reference images** (image-to-image guidance). Připoj k promptům:

1. **Vždy**: `brand-board.png` — globální vizuální mood
2. **Vždy pokud existuje**: `08-inspirace-pro-pdf-materialy.png` — PDF-specific layout language
3. **Per stránka podle layoutu** — viz `{baseDir}/references/kit-mapping.md`:
   - Cover, endcap, hero stránky → `01-hero-mockup.png` nebo `02-business-card.png`
   - Diagram/flow → `08-inspirace-pro-pdf-materialy.png` (cycle diagram příklad)
   - Process steps → `08-inspirace-pro-pdf-materialy.png` (postup implementace příklad)
   - Stats / kontrolní seznam → `08-inspirace-pro-pdf-materialy.png` (kontrolní seznam příklad)
   - CTA → `08-inspirace-pro-pdf-materialy.png` (CTA panel příklad)
4. **Per stránka podle obsahu**:
   - Foto autora / týmu → `/documents/brand/products/[slug]/images/team.jpg` (pokud existuje)
   - Produkt mockup → `/documents/brand/products/[slug]/images/product.jpg`

**KRITICKÉ:** Brand reference nejsou vzor ke kopírování — jsou **language guidance**. GPT Image 2 z nich extrahuje barvy, mood, texturu, kompoziční principy a aplikuje je na NOVÉ kompozice. Nikdy nesmí výsledek vypadat jako kopie reference.

### Krok 5: Batch generuj draft všech stránek

Použij **backend z page-plan.json** (zvolený v Krok 0.2):

```bash
BACKEND=$(python3 -c "import json; print(json.load(open('/documents/lead-magnets/[slug]/page-plan.json'))['backend'])")

python3 "{baseDir}/scripts/generate-images.py" \
  --plan "/documents/lead-magnets/[slug]/page-plan.json" \
  --prompts-dir "/documents/lead-magnets/[slug]/_prompts/" \
  --references-dir "/documents/brand/" \
  --output-dir "/documents/lead-magnets/[slug]/_pages/" \
  --resolution draft \
  --backend "$BACKEND"
```

Skript pro každou stránku:
1. Načte prompt z `_prompts/page-XX.txt`
2. Připojí brand reference images podle `kit-mapping.md`
3. Volá zvolený backend:
   - `openclaw` → `image_generate "<prompt>" --size WxH --output PATH --reference PATH...`
   - `openrouter` → `POST openrouter.ai/api/v1/images/generations` s `model: "openai/gpt-image-2"`
   - `fal` → `POST queue.fal.run/fal-ai/gpt-image-2` s base64 reference images
4. Vygenerovaný obrázek se uloží do `_pages/page-XX.png`

Detail per backend v `{baseDir}/references/image-generation-backends.md`.

### Krok 6: Schválení draftů a selektivní regenerace

**🛑 Vyžaduje schválení uživatele. Skill MUSÍ zastavit a vyčkat na review výsledku — NEPOKRAČOVAT na Krok 7 (final generaci) dokud uživatel explicitně neřekne „OK, schvaluji".**

Vytvoř review HTML grid:

```bash
python3 "{baseDir}/scripts/build-review.py" \
  --pages-dir "/documents/lead-magnets/[nazev-magnetu]/_pages/" \
  --output "/documents/lead-magnets/[nazev-magnetu]/_review.html" \
  --plan "/documents/lead-magnets/[nazev-magnetu]/page-plan.json"
```

Otevři `_review.html` v browseru. Uživatel:
1. Vidí všech N stránek v gridu (grid přizpůsobený orientaci — 4 sloupce pro portrait, 2 pro landscape)
2. Označí stránky k regeneraci s krátkým komentářem (text není čitelný / nesprávný layout / špatné barvy / atd.)
3. Pošle Claude seznam (např. "3, 7, 12 — text na #3 má překlepy v diakritice")

**Cyklus regenerace:**
- Uprav prompt(y) konkrétních stránek (např. zdůrazni "render Czech diacritics correctly: á é í ó ú ů ý č ď ě ň ř š ť ž")
- Regeneruj jen ty stránky s flag `--only "3,7,12"`
- Aktualizuj `_review.html`
- Opakuj dokud uživatel není spokojen

**NEPOKRAČUJ na finální generaci, dokud uživatel explicitně neřekne "OK, schvaluji".**

### Krok 7: Finální generace v plné kvalitě

Po schválení regeneruj všechny stránky v 300 DPI:

```bash
python3 "{baseDir}/scripts/generate-images.py" \
  ... --resolution final \
  ... --output-dir "/documents/lead-magnets/[nazev-magnetu]/_pages-final/"
```

### Krok 8: Komponuj PDF

```bash
python3 "{baseDir}/scripts/compose-pdf.py" \
  --pages-dir "/documents/lead-magnets/[nazev-magnetu]/_pages-final/" \
  --output "/documents/lead-magnets/[nazev-magnetu]/lead-magnet-visual.pdf" \
  --orientation portrait \
  --title "{Název magnetu}" \
  --author "{Autor}"
```

Skript:
1. Načte všechny `page-XX.png` v alfabetickém pořadí
2. Vytvoří A4 PDF v zadané orientaci, 300 DPI
3. Embeduje metadata
4. Optimalizuje velikost (Pillow + komprese)

### Krok 9: Output

```
✅ Vizuální PDF vytvořeno: /documents/lead-magnets/[nazev-magnetu]/lead-magnet-visual.pdf
   Orientace: {portrait/landscape/mixed}
   Velikost: XX MB
   Stran: XX
```

## Pravidla pro kvalitu výstupu

### Premium designer feel (závazné)

Cílem je výstup, který by mohl pocházet od **profesionálního layout designéra** — žádný "AI-obvious" feel. Závazná pravidla:

1. **Single dominant focal element** per stránka — nikdy více souboje vizuálních prvků
2. **Generous whitespace** — minimum 20-30 % volné plochy per stránka, jako prémiové publikace
3. **Editorial typography** — display font pro hero text, body font pro paragraphs, jasná hierarchie
4. **Sophisticated color usage** — nikdy více než 3-4 barvy na stránce, plus neutrální
5. **Subtle decorative elements** — tenké linky, subtle gradient ornaments, nikdy busy patterns
6. **Professional photography** — editorial, candid lifestyle, high-end product shots — nikdy stock-photo aesthetic

### Reference brandy pro layout language

V style directive uveď reference brandy, kterých estetiku chceš (vyber 1-2 podle brand DNA):

| Brand mood | Reference |
|------------|-----------|
| Premium, sofistikovaný | **Phaidon** (book design), **Wallpaper Magazine**, **Apple Annual Report** |
| Editorial, intelektuální | **NYT Magazine**, **The Gentlewoman**, **Monocle** |
| Tech, futuristic | **Linear product docs**, **Stripe.com PDFs**, **Vercel guides** |
| Warm, organický | **Aesop catalogue**, **Le Labo product cards**, **Loewe Foundation** |
| Bold, energetický | **Nike Annual Report**, **Hormozi $100M Leads PDF**, **MrBeast brand decks** |

### Konzistence napříč stránkami (POVINNÁ)

Všechny stránky v rámci jednoho magnetu MUSÍ mít:
- Stejnou paletu (z brand-board) — `{{PRIMARY_HEX}}, {{ACCENT_HEX}}` v každém promptu
- Stejný photography mood (warm vs. cool, soft vs. dramatic)
- Stejný typography mood (modern sans, elegant serif, mixed)
- Stejnou texture/material aesthetic
- Stejný layout language (z 08-inspirace-pro-pdf-materialy.png)

### Czech text (zvláštní pozornost)

GPT Image 2 obecně zvládá český text dobře, ale:

- **Vždy explicitně uveď diakritiku** v promptu jako příklad: `"Czech text with full diacritics: á é í ó ú ů ý č ď ě ň ř š ť ž"`
- **Maximum 50 slov per stránka** — víc textu = vyšší šance na chyby
- **Zkontroluj každou stránku po renderu** přes OCR nebo manuálně
- **Pokud vrátí chybný text** → fallback strategie v `{baseDir}/references/text-overlay-fallback.md`:
  1. Re-prompt s ještě explicitnějšími instrukcemi
  2. Generuj bez textu + Pillow text overlay v `compose-pdf.py`
  3. Hybrid: GPT Image 2 pro background + Pillow text na konkrétní pozici

### Maximum rozlišení

| Fáze | Šířka × výška | DPI | Use case |
|------|----------------|-----|----------|
| Draft (review) | 1240×1754 / 1754×1240 | 150 | Rychlý preview, levnější ($0.03/img) |
| Final (production) | 2480×3508 / 3508×2480 | 300 | Print quality, finální output ($0.10/img) |
| Hi-end (volitelné) | 4096×4096 max area | 360+ | Pro velkoformátový tisk (drahé, jen on-request) |

GPT Image 2 podporuje až 4096×4096 area max — pro A4 portrait na 300 DPI je 2480×3508 stale OK (pod 4096 area). Pro hi-end print použij 4096×3072 nebo 3072×4096.

## Output

```
/documents/lead-magnets/[nazev-magnetu]/
├── 00-strategie.md             # vstup z lead-magnet-generator
├── 03-obsah.md                 # vstup
├── page-plan.json              # plán stránek + orientace + style directive (Krok 2)
├── _prompts/
│   ├── page-01.txt             # GPT Image 2 prompt
│   ├── page-02.txt
│   └── ...
├── _pages/                     # draft (1240×1754, 150 DPI)
│   ├── page-01.png
│   └── ...
├── _pages-final/               # final (2480×3508, 300 DPI)
│   ├── page-01.png
│   └── ...
├── _review.html                # batch review grid
└── lead-magnet-visual.pdf      # FINAL OUTPUT
```

## Reference

- `{baseDir}/references/style-directive.md` — jak sestavit konzistentní style directive z brandové vizuální knihovny
- `{baseDir}/references/premium-layouts.md` — 16 layoutů s GPT Image 2 promptovými šablonami (portrait + landscape)
- `{baseDir}/references/kit-mapping.md` — mapování typu stránky → relevantní brand-kit reference soubor
- `{baseDir}/references/landscape-orientation.md` — kdy použít landscape, layout adaptace
- `{baseDir}/references/text-overlay-fallback.md` — fallback strategie pro špatně vykreslený text
- `{baseDir}/references/image-generation-backends.md` — technický detail 3 systémů (vestavěný nástroj, OpenRouter, FAL.ai), endpointy, auth, request/response, fallback chain
- `{baseDir}/scripts/generate-images.py` — batch generování pro všechny 3 systémy (`--backend openclaw|openrouter|fal`)
- `{baseDir}/scripts/build-review.py` — review HTML grid builder
- `{baseDir}/scripts/compose-pdf.py` — finální PDF kompozice z PNG (portrait + landscape)
