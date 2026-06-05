# Page Layouts — A4 stránky lead magnetu

Knihovna layoutů pro A4 stránky lead magnetu. Každý layout má strukturu HTML + CSS přes CSS proměnné z DESIGN.md/style-presets.

**Žádné animace, žádný JS.** Statický HTML pro PDF render.

---

## Univerzální struktura `.page`

Každá stránka je samostatný `<section class="page">` s `page-break-after: always`. A4 portrait, 210×297mm.

```html
<section class="page page--cover">
  <!-- obsah stránky -->
</section>
```

Společné CSS (v `html-template.md`):

```css
.page {
  width: 210mm;
  height: 297mm;
  padding: var(--space-12) var(--space-8);
  page-break-after: always;
  break-after: page;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
```

---

## 1. Cover (titulní stránka)

**Účel:** První stránka. Hero impact. Název magnetu + author + brand.

### Variant A: Text-only (bez obrázku)

```html
<section class="page page--cover cover--text">
  <header class="cover-header">
    <img class="cover-logo" src="/documents/brand/logo.png" alt="[Brand name]">
  </header>

  <div class="cover-main">
    <h1 class="cover-title">5 peněžních pravd, které tě stojí 200k Kč ročně</h1>
    <p class="cover-subtitle">Identifikace, audit a okamžité kroky pro freelancerky 28–42 let</p>
  </div>

  <footer class="cover-footer">
    <p class="cover-author">Petra Nováková · certifikovaná financial coach</p>
  </footer>
</section>
```

> ⛔ **NIKDY nedávej na cover meta info typu počtu stran ("12 stran"), času čtení ("15 minut"), informaci o tisku ("Vytištěno na 1 stránku"), datum vydání ani version number.**
>
> Cover je **emoční impact** — slibuje transformaci. Meta info má místo v Table of Contents nebo footer interních stránek, ne na obálce. Prémiové brandové publikace (Vogue, NYT Magazine, Aesop catalogues) na cover NIKDY nedávají "X stran" — degraduje to vnímanou hodnotu z artefaktu na utility.
>
> Pokud chceš čtenáře informovat o čase, dej to do **podnadpisu** přirozenou cestou ("Rychlá kartička, kterou si vytiskneš"), ne jako tech meta řádek.

```css
.page--cover {
  background: var(--color-primary);
  color: var(--color-bg);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: var(--space-16) var(--space-12);
}

.cover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--fs-small);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  opacity: 0.7;
}

.cover-badge {
  padding: var(--space-2) var(--space-3);
  border: 1pt solid currentColor;
  border-radius: var(--radius-full);
}

.cover-title {
  font-family: var(--font-display);
  font-size: clamp(36pt, 6vw, 64pt);
  line-height: 1.05;
  font-weight: var(--fw-bold);
  letter-spacing: var(--ls-display);
  margin-bottom: var(--space-6);
}

.cover-subtitle {
  font-size: var(--fs-h3);
  opacity: 0.85;
  max-width: 50ch;
}

.cover-footer {
  border-top: 1pt solid rgba(255, 255, 255, 0.2);
  padding-top: var(--space-4);
  /* ZÁKAZ: žádný počet stran, čas čtení, version, page number */
}
```

### Variant B: Hero image (full-bleed)

```html
<section class="page page--cover cover--hero" style="background-image: url('cover.png');">
  <div class="cover-overlay"></div>
  <div class="cover-content">
    <h1 class="cover-title">Money Identity Audit</h1>
    <p class="cover-subtitle">Zjisti, který ze 4 peněžních typů jsi (a co tě stojí každý měsíc)</p>
    <p class="cover-author">Petra Nováková</p>
  </div>
</section>
```

```css
.cover--hero {
  background-size: cover;
  background-position: center;
  position: relative;
  padding: 0;
}

.cover-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.7) 100%);
}

.cover--hero .cover-content {
  position: relative;
  z-index: 2;
  margin-top: auto;
  padding: var(--space-12);
  color: white;
}

.cover--hero .cover-title {
  text-shadow: 0 2pt 12pt rgba(0,0,0,0.4);
}
```

**Pravidla:**
- Cover = nejvíc vizuálu v celém dokumentu. Buď text-bold (Variant A) nebo hero-image (Variant B). Mix nedělej.
- Title MUSÍ být dominantní — `clamp(36pt, 6vw, 64pt)`.
- **Logo JE POVINNÉ** — pokud existuje `/documents/brand/logo.png` (nebo .svg, .jpg). Top-left nebo top-right.
- Povolené elementy: **logo**, brand mark (jen jako fallback bez loga), eyebrow s ikonou + zaměřením/personou, title, 1-line subtitle, author + role.
- **ZAKÁZANO** na cover:
  - Marketing pill / badge ("Magnet zdarma", "Free Guide", "Ebook") — degraduje vizuální kvalitu, vypadá jako spam
  - Tech meta info — počet stran, čas čtení, "vytištěno na X stránek", datum vydání, version number, page number
  - Více než 1 výrazný visual element
- Žádné další textové bloky než výše uvedené.

---

## 2. Table of Contents

**Účel:** Druhá stránka. Navigace dokumentem.

```html
<section class="page page--toc">
  <h1 class="toc-title">Obsah</h1>
  <ol class="toc-list">
    <li class="toc-item">
      <span class="toc-num">01</span>
      <span class="toc-name">Proč ti finanční rady nikdy nefungovaly</span>
      <span class="toc-page">3</span>
    </li>
    <li class="toc-item">
      <span class="toc-num">02</span>
      <span class="toc-name">Audit peněžních pravd: 11 přesvědčení</span>
      <span class="toc-page">5</span>
    </li>
    <!-- ... -->
  </ol>
</section>
```

```css
.toc-title {
  font-family: var(--font-display);
  font-size: var(--fs-display);
  margin-bottom: var(--space-12);
  color: var(--color-primary);
}

.toc-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.toc-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: baseline;
  gap: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1pt solid var(--color-border);
}

.toc-num {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  font-weight: var(--fw-bold);
  color: var(--color-accent);
  min-width: 3ch;
}

.toc-name {
  font-size: var(--fs-h3);
  font-weight: var(--fw-medium);
}

.toc-page {
  font-size: var(--fs-small);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}
```

---

## 3. Chapter Opener (úvod kapitoly)

**Účel:** Vizuálně silný předěl mezi kapitolami. Velké číslo + název.

```html
<section class="page page--chapter-opener">
  <div class="chapter-frame">
    <span class="chapter-label">Kapitola</span>
    <span class="chapter-num">02</span>
  </div>

  <div class="chapter-main">
    <h2 class="chapter-title">Audit peněžních pravd</h2>
    <p class="chapter-tease">11 přesvědčení, která určují tvůj zůstatek — a kterým jsi nikdy neřekla "stop"</p>
  </div>

  <div class="chapter-quote">
    <blockquote>
      Peníze nejsou matematika. Peníze jsou identita.
    </blockquote>
    <cite>— Petra Nováková</cite>
  </div>
</section>
```

```css
.page--chapter-opener {
  background: var(--color-bg-subtle);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.chapter-frame {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
}

.chapter-label {
  font-size: var(--fs-small);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--color-text-muted);
}

.chapter-num {
  font-family: var(--font-display);
  font-size: clamp(120pt, 20vw, 240pt);
  font-weight: var(--fw-bold);
  line-height: 0.85;
  color: var(--color-accent);
  letter-spacing: -0.04em;
}

.chapter-title {
  font-family: var(--font-display);
  font-size: var(--fs-display);
  line-height: 1.05;
  margin-bottom: var(--space-4);
}

.chapter-tease {
  font-size: var(--fs-h3);
  max-width: 40ch;
  color: var(--color-text-muted);
}

.chapter-quote {
  border-top: 1pt solid var(--color-border);
  padding-top: var(--space-4);
}

.chapter-quote blockquote {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  font-style: italic;
  line-height: 1.4;
  margin-bottom: var(--space-2);
}

.chapter-quote cite {
  font-size: var(--fs-small);
  color: var(--color-text-muted);
  font-style: normal;
}
```

---

## 4. Content (klasický text + ikony)

**Účel:** Hlavní obsahová stránka. Text, podnadpisy, bullety s ikonami.

```html
<section class="page page--content">
  <header class="content-header">
    <span class="content-chapter">Kapitola 2 · Audit peněžních pravd</span>
  </header>

  <h2 class="content-h2">Peněžní programy z dětství</h2>

  <p class="content-lead">
    Tvoje první peněžní pravda nebyla matematická. Byla to věta,
    kterou si zapamatovala tvá 4letá verze, když rodiče přišli z práce.
  </p>

  <ul class="content-bullets">
    <li>
      <span class="bullet-icon"><!-- check icon --></span>
      <div>
        <strong>Na to nemáme.</strong>
        <p>Zapsáno jako "buďte opatrní s penězi". Kontrolovalo to tvoje rozhodnutí o paušálu, dovolené, vybavení.</p>
      </div>
    </li>
    <li>
      <span class="bullet-icon"><!-- check icon --></span>
      <div>
        <strong>Když máš málo, neutrácej.</strong>
        <p>Zapsáno jako "rodina = chudoba". Chrání tě před ztrátou, ale zavírá tě před růstem.</p>
      </div>
    </li>
  </ul>

  <p class="content-aha">
    <strong>Aha moment:</strong> Většina mých klientek po cvičení zjistí,
    že velmi opatrně utrácí proto, že chtějí být dospělé. Ale dospělost
    není opatrnost — je to schopnost zvolit, kdy je opatrnost správně.
  </p>
</section>
```

```css
.content-header {
  font-size: var(--fs-small);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
  margin-bottom: var(--space-8);
  padding-bottom: var(--space-3);
  border-bottom: 1pt solid var(--color-border);
}

.content-h2 {
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  line-height: 1.15;
  margin-bottom: var(--space-4);
  color: var(--color-primary);
}

.content-lead {
  font-size: var(--fs-h3);
  line-height: 1.5;
  color: var(--color-text);
  margin-bottom: var(--space-6);
  max-width: 60ch;
}

.content-bullets {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.content-bullets li {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--space-3);
  align-items: start;
}

.bullet-icon {
  width: 24pt;
  height: 24pt;
  color: var(--color-accent);
  flex-shrink: 0;
}

.bullet-icon svg {
  width: 100%;
  height: 100%;
}

.content-bullets strong {
  display: block;
  font-size: var(--fs-h3);
  margin-bottom: var(--space-1);
  color: var(--color-primary);
}

.content-bullets p {
  font-size: var(--fs-body);
  line-height: 1.5;
  color: var(--color-text);
}

.content-aha {
  background: var(--color-bg-subtle);
  border-left: 4pt solid var(--color-accent);
  padding: var(--space-4) var(--space-5);
  margin-top: var(--space-6);
  border-radius: var(--radius-sm);
  font-size: var(--fs-body);
  line-height: 1.5;
}

.content-aha strong {
  color: var(--color-accent);
  font-weight: var(--fw-semibold);
}
```

---

## 4b. Content split with founder/inline image

**Účel:** Content stránka s velkým inline obrázkem (founder portrait, screenshot, hero foto). Použij **každé 3-4 stránky** ve vícestránkových magnetech (8+) pro vizuální rytmus.

```html
<section class="page page--content content--split">
  <header class="content-header">
    <span class="content-chapter">Kapitola 3 · Kdo to dělá</span>
  </header>

  <div class="content-split-body">
    <figure class="content-figure">
      <img class="content-figure-img" src="/documents/brand/products/[slug]/images/pavel.jpg" alt="Pavel Hrdlička">
      <figcaption class="content-figure-cap">
        Pavel Hrdlička<br>
        <span>CEO, CliqSales</span>
      </figcaption>
    </figure>

    <div class="content-split-text">
      <h2 class="content-h2">Postavili jsme firmu, která prodala 100+ mld. Kč</h2>
      <p class="content-lead">
        Před 16 lety jsem začal s prvním e-shopem. Po 47 spuštěných projektech a 1 750+ firmách v Akcelerátoru…
      </p>
      <ul class="content-bullets">
        <li>17 000+ vyškolených manažerů</li>
        <li>AI Summit s 16 944 účastníky</li>
        <li>Exit SocialSprinters → AI Akcelerátor</li>
      </ul>
    </div>
  </div>
</section>
```

```css
.content--split {
  display: flex;
  flex-direction: column;
  padding: var(--space-12) var(--space-8);
}

.content-split-body {
  display: grid;
  grid-template-columns: 40% 1fr;
  gap: var(--space-6);
  align-items: start;
  flex: 1;
}

.content-figure {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.content-figure-img {
  width: 100%;
  aspect-ratio: 4 / 5;          /* mírně portrait, není přehnaně vysoké */
  max-height: 60vh;
  object-fit: cover;
  object-position: center;
  border-radius: var(--radius-md);
  background: var(--color-bg-subtle);
}

.content-figure-cap {
  font-family: var(--font-body);
  font-size: var(--fs-small);
  font-weight: var(--fw-semibold);
  color: var(--color-primary);
}

.content-figure-cap span {
  font-weight: var(--fw-normal);
  color: var(--color-text-muted);
}

.content-split-text {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
```

**Pravidla:**
- `aspect-ratio: 4/5` u portrait fota → nikdy nedeformovaný
- `object-position: top` → hlava nezmizí při ořezu
- Foto **40% šířky**, text **60%** — při užší ratio se text zužuje pod 50ch
- Nepoužívej `content--split` 2× za sebou — sousední split stránky vypadají monotónně

---

## 5. Feature Grid (3-card layout s ikonami)

**Účel:** Klíčové poznatky / 3 typy / 3 kroky.

```html
<section class="page page--feature-grid">
  <h2 class="grid-title">3 typy peněžních programů</h2>
  <p class="grid-subtitle">Každý typ má jiný spouštěč a jiné řešení</p>

  <div class="grid-3">
    <article class="feature-card">
      <span class="feature-icon"><!-- shield icon --></span>
      <h3>Avoider</h3>
      <p>Vyhýbavý typ. Faktura zůstane neotevřená 3 dny. Bankovní app jen při převodu.</p>
      <span class="feature-tag">~3 600 Kč/měsíc</span>
    </article>

    <article class="feature-card">
      <span class="feature-icon"><!-- alert-triangle icon --></span>
      <h3>Worrier</h3>
      <p>Úzkostný typ. Kontroluje účet 5× denně, ale nic neudělá s tím, co vidí.</p>
      <span class="feature-tag">~2 100 Kč/měsíc</span>
    </article>

    <article class="feature-card">
      <span class="feature-icon"><!-- zap icon --></span>
      <h3>Spender</h3>
      <p>Utrácivý typ. Akce, slevy, bonusy = automatický nákup, i když to nepotřebuje.</p>
      <span class="feature-tag">~5 200 Kč/měsíc</span>
    </article>
  </div>
</section>
```

```css
.grid-title {
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  margin-bottom: var(--space-2);
}

.grid-subtitle {
  font-size: var(--fs-h3);
  color: var(--color-text-muted);
  margin-bottom: var(--space-8);
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
  flex: 1;
  align-content: center;
}

.feature-card {
  padding: var(--space-5);
  border: 1pt solid var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  page-break-inside: avoid;
}

.feature-icon {
  width: 36pt;
  height: 36pt;
  color: var(--color-accent);
}

.feature-card h3 {
  font-size: var(--fs-h3);
  font-weight: var(--fw-semibold);
  color: var(--color-primary);
}

.feature-card p {
  font-size: var(--fs-small);
  line-height: 1.5;
  color: var(--color-text);
  flex: 1;
}

.feature-tag {
  display: inline-block;
  padding: var(--space-1) var(--space-2);
  background: var(--color-bg-subtle);
  color: var(--color-error);
  font-size: var(--fs-small);
  font-weight: var(--fw-semibold);
  border-radius: var(--radius-sm);
  align-self: flex-start;
}
```

---

## 6. Mýty vs. Fakta (kontrastní layout)

**Účel:** Strukturovaný blok "co si myslíš" vs. "co je pravda".

```html
<section class="page page--myth-fact">
  <h2 class="mf-title">Mýty vs. Fakta</h2>

  <div class="mf-pair">
    <div class="mf-myth">
      <span class="mf-icon"><!-- x-circle icon --></span>
      <span class="mf-label">Mýtus</span>
      <p>Stačí si vést rozpočet — disciplína vyřeší všechno.</p>
    </div>
    <div class="mf-fact">
      <span class="mf-icon"><!-- check-circle icon --></span>
      <span class="mf-label">Fakt</span>
      <p>Rozpočet je tabulka, identita je systém. Bez systému ti tabulka padne ve 3. týdnu.</p>
    </div>
  </div>

  <div class="mf-pair">
    <div class="mf-myth">
      <span class="mf-icon"><!-- x-circle icon --></span>
      <span class="mf-label">Mýtus</span>
      <p>Lidé s vyššími příjmy mají vyřešené finance.</p>
    </div>
    <div class="mf-fact">
      <span class="mf-icon"><!-- check-circle icon --></span>
      <span class="mf-label">Fakt</span>
      <p>47% Čechů s příjmem nad 80k Kč nemá ani 30denní rezervu (Air Bank, 2024).</p>
    </div>
  </div>
</section>
```

```css
.mf-title {
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  margin-bottom: var(--space-8);
}

.mf-pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  page-break-inside: avoid;
}

.mf-myth, .mf-fact {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.mf-myth {
  background: rgba(239, 68, 68, 0.05);
  border-left: 4pt solid var(--color-error);
}

.mf-fact {
  background: rgba(16, 185, 129, 0.05);
  border-left: 4pt solid var(--color-success);
}

.mf-icon {
  width: 24pt;
  height: 24pt;
}

.mf-myth .mf-icon { color: var(--color-error); }
.mf-fact .mf-icon { color: var(--color-success); }

.mf-label {
  font-size: var(--fs-small);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: var(--fw-semibold);
}

.mf-myth .mf-label { color: var(--color-error); }
.mf-fact .mf-label { color: var(--color-success); }

.mf-pair p {
  font-size: var(--fs-body);
  line-height: 1.5;
}
```

---

## 7. Quote Spread (citát autora)

**Účel:** Vizuální pauza s citátem.

```html
<section class="page page--quote">
  <div class="quote-mark"><!-- quote icon --></div>
  <blockquote class="quote-text">
    Nejdražší věc, kterou si můžeš dovolit, je přesvědčení "na to nemám".
    Stojí tě každý měsíc rozdíl mezi tím, co máš, a tím, co bys mohla mít.
  </blockquote>
  <cite class="quote-author">
    <strong>Petra Nováková</strong>
    <span>Certifikovaná financial coach · 200+ klientek</span>
  </cite>
</section>
```

```css
.page--quote {
  background: var(--color-primary);
  color: var(--color-bg);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  padding: var(--space-16) var(--space-12);
}

.quote-mark {
  width: 64pt;
  height: 64pt;
  color: var(--color-accent);
  margin-bottom: var(--space-6);
  opacity: 0.6;
}

.quote-text {
  font-family: var(--font-display);
  font-size: clamp(28pt, 4vw, 40pt);
  line-height: 1.25;
  font-weight: var(--fw-medium);
  margin-bottom: var(--space-8);
  max-width: 30ch;
}

.quote-author {
  font-style: normal;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  border-top: 1pt solid rgba(255,255,255,0.2);
  padding-top: var(--space-3);
}

.quote-author strong {
  font-size: var(--fs-h3);
  font-weight: var(--fw-semibold);
}

.quote-author span {
  font-size: var(--fs-small);
  opacity: 0.7;
}
```

---

## 8. Checklist / Šablona (pracovní stránka)

**Účel:** Akční checklist nebo šablona k vyplnění.

```html
<section class="page page--checklist">
  <header class="checklist-header">
    <h2>14denní audit peněžních pravd</h2>
    <p>Každý den jedna věta. Trvá to 5 minut.</p>
  </header>

  <ol class="checklist-list">
    <li>
      <span class="checklist-day">Den 1</span>
      <p>Když rodiče v dětství řešili peníze, vzpomeneš si nejčastěji na: ___</p>
    </li>
    <li>
      <span class="checklist-day">Den 2</span>
      <p>Když jsi v dětství dostala peníze (kapesné, dárek), první reakce byla: ___</p>
    </li>
    <li>
      <span class="checklist-day">Den 3</span>
      <p>Vzpomeneš si na první moment, kdy ses styděla za peníze nebo jejich nedostatek: ___</p>
    </li>
    <!-- ... -->
  </ol>

  <p class="checklist-tip">
    <span class="bullet-icon"><!-- info icon --></span>
    Odpovídej spontánně, ne tak, jak by sis přála reagovat. První instinkt = pravda.
  </p>
</section>
```

```css
.checklist-header {
  margin-bottom: var(--space-8);
}

.checklist-header h2 {
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  margin-bottom: var(--space-2);
}

.checklist-header p {
  font-size: var(--fs-h3);
  color: var(--color-text-muted);
}

.checklist-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.checklist-list li {
  display: grid;
  grid-template-columns: 80pt 1fr;
  gap: var(--space-4);
  align-items: baseline;
  padding-bottom: var(--space-3);
  border-bottom: 1pt dashed var(--color-border);
}

.checklist-day {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  font-weight: var(--fw-semibold);
  color: var(--color-accent);
}

.checklist-list p {
  font-size: var(--fs-body);
  line-height: 1.5;
  min-height: 2lh;
}

.checklist-tip {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  background: var(--color-bg-subtle);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm);
  font-size: var(--fs-small);
  color: var(--color-text-muted);
}
```

---

## 9. Audit Question Page (pro audit magnety)

**Účel:** Stránka s diagnostickými otázkami.

```html
<section class="page page--audit">
  <header class="audit-header">
    <span class="audit-section">Sekce A · Peněžní programy z dětství</span>
    <span class="audit-progress">5 z 23 otázek</span>
  </header>

  <ol class="audit-list">
    <li class="audit-question">
      <span class="audit-num">A1</span>
      <div class="audit-body">
        <p class="audit-text">Když rodiče v dětství řešili peníze, vzpomeneš si nejčastěji na:</p>
        <ul class="audit-options">
          <li><span class="audit-radio"></span> Hádky a stres <span class="audit-points">(3 b.)</span></li>
          <li><span class="audit-radio"></span> Tichou opatrnost <span class="audit-points">(2 b.)</span></li>
          <li><span class="audit-radio"></span> Šetřivost a "na to nemáme" <span class="audit-points">(1 b.)</span></li>
          <li><span class="audit-radio"></span> Otevřenou diskusi o financích <span class="audit-points">(0 b.)</span></li>
        </ul>
      </div>
    </li>
    <!-- ... -->
  </ol>
</section>
```

```css
.audit-header {
  display: flex;
  justify-content: space-between;
  font-size: var(--fs-small);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
  margin-bottom: var(--space-8);
  padding-bottom: var(--space-3);
  border-bottom: 1pt solid var(--color-border);
}

.audit-question {
  display: grid;
  grid-template-columns: 48pt 1fr;
  gap: var(--space-4);
  padding: var(--space-4) 0;
  border-bottom: 1pt dashed var(--color-border);
  page-break-inside: avoid;
}

.audit-num {
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  font-weight: var(--fw-bold);
  color: var(--color-accent);
}

.audit-text {
  font-size: var(--fs-body);
  font-weight: var(--fw-medium);
  margin-bottom: var(--space-2);
}

.audit-options {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.audit-options li {
  display: grid;
  grid-template-columns: 16pt 1fr auto;
  gap: var(--space-2);
  align-items: baseline;
  font-size: var(--fs-small);
}

.audit-radio {
  width: 12pt;
  height: 12pt;
  border: 1pt solid var(--color-text-muted);
  border-radius: 50%;
}

.audit-points {
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}
```

---

## 10. CTA Page (závěrečné pozvání ke koupi)

**Účel:** Poslední stránka. Brunson Hook–Story–Offer + button.

```html
<section class="page page--cta">
  <div class="cta-content">
    <span class="cta-eyebrow">Co teď dál?</span>
    <h2 class="cta-title">Tvůj audit ti dal diagnostiku.<br>Money Reset ti dá systém.</h2>

    <div class="cta-stack">
      <div class="cta-item">
        <span class="cta-icon"><!-- check-circle --></span>
        <p><strong>8 týdnů provedené detoxikace</strong> — 14 cvičení s feedbackem od Petry</p>
      </div>
      <div class="cta-item">
        <span class="cta-icon"><!-- check-circle --></span>
        <p><strong>4účtový systém</strong> — konkrétní setup pro Air Bank a ČSOB</p>
      </div>
      <div class="cta-item">
        <span class="cta-icon"><!-- check-circle --></span>
        <p><strong>Komunita 12 žen</strong> — týdenní check-iny, kde 90% sólových resetů selže</p>
      </div>
      <div class="cta-item cta-bonus">
        <span class="cta-icon"><!-- gift --></span>
        <p><strong>BONUS pro tebe:</strong> 1:1 onboarding call zdarma (1 950 Kč hodnota)</p>
      </div>
    </div>

    <div class="cta-action">
      <a class="cta-button" href="https://...">
        Chci program Money Reset
        <span class="cta-arrow"><!-- arrow-right --></span>
      </a>
      <p class="cta-meta">29 800 Kč · Nejbližší cohorta startuje za 2 týdny · Záruka vrácení peněz po 4. týdnu</p>
    </div>
  </div>
</section>
```

```css
.page--cta {
  background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
  color: var(--color-bg);
  display: flex;
  align-items: center;
  padding: var(--space-12);
}

.cta-eyebrow {
  font-size: var(--fs-small);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  opacity: 0.7;
  margin-bottom: var(--space-3);
  display: block;
}

.cta-title {
  font-family: var(--font-display);
  font-size: clamp(28pt, 5vw, 48pt);
  line-height: 1.1;
  font-weight: var(--fw-bold);
  margin-bottom: var(--space-8);
}

.cta-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-8);
}

.cta-item {
  display: grid;
  grid-template-columns: 24pt 1fr;
  gap: var(--space-3);
  align-items: start;
}

.cta-icon {
  width: 24pt;
  height: 24pt;
  color: var(--color-accent);
  background: var(--color-bg);
  border-radius: 50%;
  padding: 4pt;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cta-bonus .cta-icon {
  background: gold;
}

.cta-item p {
  font-size: var(--fs-body);
  line-height: 1.5;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  background: var(--color-bg);
  color: var(--color-primary);
  border-radius: var(--radius-md);
  text-decoration: none;
  font-size: var(--fs-h3);
  font-weight: var(--fw-semibold);
  margin-bottom: var(--space-3);
}

.cta-arrow {
  width: 24pt;
  height: 24pt;
}

.cta-meta {
  font-size: var(--fs-small);
  opacity: 0.7;
  max-width: 50ch;
}
```

---

## 11. Comparison Table (srovnání A vs. B)

**Účel:** Pro typ "Srovnání A vs. B".

```html
<section class="page page--comparison">
  <h2 class="comp-title">Stripe vs. Shopify Payments vs. WooCommerce</h2>
  <p class="comp-sub">Kompletní srovnání pro český e-shop</p>

  <table class="comp-table">
    <thead>
      <tr>
        <th></th>
        <th>Stripe</th>
        <th>Shopify Payments</th>
        <th>WooCommerce</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="comp-criteria">Fee per transakci</td>
        <td>1.4% + 6 Kč</td>
        <td class="comp-good">2.4% + 0 Kč</td>
        <td>0%* (jen gateway)</td>
      </tr>
      <tr>
        <td class="comp-criteria">CZK podpora</td>
        <td class="comp-good">Plná</td>
        <td class="comp-good">Plná</td>
        <td>Závisí na gateway</td>
      </tr>
      <!-- ... -->
    </tbody>
  </table>
</section>
```

```css
.comp-title {
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  margin-bottom: var(--space-2);
}

.comp-sub {
  font-size: var(--fs-h3);
  color: var(--color-text-muted);
  margin-bottom: var(--space-8);
}

.comp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-small);
}

.comp-table th {
  background: var(--color-primary);
  color: var(--color-bg);
  padding: var(--space-3);
  text-align: left;
  font-weight: var(--fw-semibold);
}

.comp-table th:first-child {
  width: 30%;
}

.comp-table td {
  padding: var(--space-3);
  border-bottom: 1pt solid var(--color-border);
}

.comp-criteria {
  font-weight: var(--fw-semibold);
  background: var(--color-bg-subtle);
}

.comp-good {
  color: var(--color-success);
  font-weight: var(--fw-semibold);
}
```

---

## Mapování typů magnetu → layouty

Každý typ magnetu používá jinou kombinaci layoutů:

| Typ magnetu | Pořadí stránek (typicky) |
|-------------|--------------------------|
| Checklist | Cover → Content (akční seznam) → CTA |
| Taháček | Cover → Feature Grid (4-8 boxů) → Quote/CTA |
| Šablona | Cover → Content (úvod) → Checklist (šablona) → Content (příklad) → CTA |
| Knihovna příkladů | Cover → TOC → Feature Grid (5-15 příkladů) → CTA |
| Mini-průvodce | Cover → TOC → Chapter Opener × 3-5 + Content × 2 + Quote → CTA |
| Workbook | Cover → TOC → Chapter Opener + Checklist (cvičení) × N → Quote → CTA |
| Audit | Cover → Content (úvod) → Audit Question × 3-4 → Content (výklad) × N → CTA |
| Quick-start | Cover → Content (den 1) × N → CTA |
| Srovnání | Cover → Content (kontext) → Comparison Table → CTA |
| Případová studie | Cover → Content (před) → Content (akce) → Content (po) → CTA |
| Mini-kurz | Cover → TOC → Chapter Opener + Content × 5 → CTA |

Skill mapuje markdown sekce z `03-obsah.md` na tyto layouty podle typu magnetu (viz `00-strategie.md` z `lead-magnet-generator`).

---

## Pravidlo: jeden vizuální zdroj na stránku

NIKDY nekombinuj na jedné stránce:
- Hero pozadí + další inline obrázky
- Více než 2-3 ikony na jednom contentu
- Hero background + karty s ikonami uvnitř

**Jedna stránka = jeden vizuální důraz.** Buď je o textu (s drobnými ikonami) nebo o obrázku/citátu (s minimum textu).

| Layout | Vizuální obsah |
|--------|----------------|
| Cover (hero) | 1 hero image + minimální text |
| Cover (text) | 0 obrázků, dominantní typografie |
| Chapter Opener | 0 obrázků, velké číslo |
| Content | 0–1 obrázek (volitelný hero v sekci), ikony v bulletech |
| Feature Grid | Ikony v každé kartě, žádné fotky |
| Mýty/Fakta | Jen ikony (x-circle vs. check-circle) |
| Quote | 0 obrázků, dominantní typografie |
| Checklist | 0–1 ikona v tipu, žádné fotky |
| Audit | 0 obrázků, jen typografie a radio buttons |
| CTA | Gradient pozadí + ikony, žádné fotky |
| Comparison | Jen tabulka s ikonami |

---

## Reference

- `{baseDir}/references/icons.md` — knihovna 200+ inline SVG ikon
- `{baseDir}/references/style-presets.md` — 4 vizuální presety (fallback bez DESIGN.md)
- `{baseDir}/references/visual-rules.md` — pravidla pro nadpisy, hierarchii, kontrast
- `{baseDir}/references/html-template.md` — kompletní HTML šablona
- `{baseDir}/references/print-css-spec.md` — print CSS pro A4 PDF
