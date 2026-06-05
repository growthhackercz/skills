# Components Reference

Tento soubor obsahuje **kompletní implementace všech opakovaně používaných komponent** prezentace.

**Načti tento soubor když:**
- Píšeš JavaScript pro slide navigaci
- Stylzuješ nav-dots, badge, card, CTA, progress bar nebo brand mark
- Přidáváš novou interaktivní komponentu
- Refaktoruješ existující prezentaci

---

## 1. SlidePresentation — JS třída (POVINNÁ)

Každá prezentace MUSÍ obsahovat funkční implementaci této třídy. Žádné stuby, žádné komentáře místo kódu.

```javascript
class SlidePresentation {
  constructor() {
    this.slides = document.querySelectorAll('.slide');
    this.currentSlide = 0;
    this.isAnimating = false;
    this.init();
  }

  init() {
    // Keyboard: šipky, space, page up/down, Home/End
    document.addEventListener('keydown', (e) => {
      if (['ArrowDown','ArrowRight','Space','PageDown'].includes(e.code)) { e.preventDefault(); this.next(); }
      if (['ArrowUp','ArrowLeft','PageUp'].includes(e.code)) { e.preventDefault(); this.prev(); }
      if (e.code === 'Home') { e.preventDefault(); this.goTo(0); }
      if (e.code === 'End') { e.preventDefault(); this.goTo(this.slides.length - 1); }
    });

    // Mouse wheel — KRITICKÉ: preventDefault + akumulace delta + cooldown
    // Wheel event se pálí 5–20× za jedno scrollnutí. Bez správného handlingu
    // přeskočí 2–3 slidy najednou.
    let wheelAccumulator = 0;
    const WHEEL_THRESHOLD = 50;
    window.addEventListener('wheel', (e) => {
      e.preventDefault();
      if (this.isAnimating) return;
      wheelAccumulator += e.deltaY;
      if (Math.abs(wheelAccumulator) < WHEEL_THRESHOLD) return;
      this.isAnimating = true;
      wheelAccumulator > 0 ? this.next() : this.prev();
      wheelAccumulator = 0;
      setTimeout(() => { this.isAnimating = false; }, 1000);
    }, { passive: false });

    // Touch / swipe
    let touchStartY = 0;
    document.addEventListener('touchstart', (e) => {
      touchStartY = e.touches[0].clientY;
    }, { passive: true });
    document.addEventListener('touchend', (e) => {
      const diff = touchStartY - e.changedTouches[0].clientY;
      if (this.isAnimating) return;
      if (Math.abs(diff) > 50) {
        this.isAnimating = true;
        diff > 0 ? this.next() : this.prev();
        setTimeout(() => { this.isAnimating = false; }, 1000);
      }
    });

    // Reveal observer — přidá .visible třídu když slide vstoupí do viewportu
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.classList.add('visible');
      });
    }, { threshold: 0.3 });
    this.slides.forEach(s => observer.observe(s));

    // Sync currentSlide s scroll pozicí (pro případ přímého scrollu)
    const scrollObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !this.isAnimating) {
          const idx = Array.from(this.slides).indexOf(entry.target);
          if (idx !== -1) {
            this.currentSlide = idx;
            this.updateNavDots();
            this.updateProgress();
          }
        }
      });
    }, { threshold: 0.5 });
    this.slides.forEach(s => scrollObserver.observe(s));

    this.buildNavDots();
    this.updateProgress();
  }

  goTo(index) {
    if (index < 0 || index >= this.slides.length) return;
    this.currentSlide = index;
    this.slides[index].scrollIntoView({ behavior: 'smooth' });
    this.updateNavDots();
    this.updateProgress();
  }

  next() { this.goTo(this.currentSlide + 1); }
  prev() { this.goTo(this.currentSlide - 1); }

  buildNavDots() {
    const container = document.querySelector('.nav-dots');
    if (!container) return;
    for (let i = 0; i < this.slides.length; i++) {
      const dot = document.createElement('button');
      dot.className = 'nav-dot' + (i === 0 ? ' active' : '');
      dot.setAttribute('aria-label', `Slide ${i + 1}`);
      // POVINNÉ: data-num atribut pro tooltip s číslem stránky
      dot.setAttribute('data-num', `${i + 1} / ${this.slides.length}`);
      dot.addEventListener('click', () => this.goTo(i));
      container.appendChild(dot);
    }
  }

  updateNavDots() {
    document.querySelectorAll('.nav-dot').forEach((dot, i) => {
      dot.classList.toggle('active', i === this.currentSlide);
    });
  }

  updateProgress() {
    const pct = ((this.currentSlide + 1) / this.slides.length) * 100;
    const bar = document.querySelector('.progress-bar');
    if (bar) bar.style.width = pct + '%';
  }
}

document.addEventListener('DOMContentLoaded', () => new SlidePresentation());
```

**KRITICKÁ pravidla:**
- `wheel` event: vždy `preventDefault()` + akumulace + cooldown 1000 ms (jinak skok přes 2–3 slidy).
- `touchend`: porovnej `clientY`, ne `pageY`.
- `Intersection Observer` má dva: jeden pro `.visible` (threshold 0.3), druhý pro sync currentSlide (threshold 0.5).

---

## 2. Nav Dots — POVINNÉ (jemné, nerušící)

Vertikální seznam dotů vpravo. Při hoveru ukáže tooltip s číslem stránky.

**HTML:**
```html
<nav class="nav-dots"><!-- Generováno JS-em buildNavDots() --></nav>
```

**CSS:**
```css
.nav-dots {
  position: fixed;
  right: clamp(12px, 1.5vw, 24px);
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.nav-dot {
  position: relative;          /* kotví tooltip */
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.15;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: opacity 0.3s, transform 0.3s;
}
.nav-dot:hover { opacity: 0.35; }
.nav-dot.active {
  opacity: 0.5;
  transform: scale(1.4);
  border-radius: 3px;
  height: 14px;                /* pill shape */
}

/* Tooltip s číslem stránky — vlevo od dotu, fade na hover */
.nav-dot::after {
  content: attr(data-num);
  position: absolute;
  right: calc(100% + 12px);
  top: 50%;
  transform: translateY(-50%) translateX(8px);
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 0.3em 0.65em;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.05em;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.nav-dot:hover::after {
  opacity: 1;
  transform: translateY(-50%) translateX(0);
}
```

**Pravidla:**
- Malé (6px), nízká opacity (0.15), aktivní pill shape (opacity 0.5).
- NIKDY velké, NIKDY plně viditelné, NIKDY s barevným akcentem.
- Tooltip s číslem (`1 / 22`) je POVINNÝ — JS musí nastavit `data-num` atribut.

---

## 3. Badge — POVINNÉ (vysoký kontrast + ikona)

Eyebrow tag nad nadpisem. VŽDY obsahuje malou SVG ikonu vlevo.

**HTML:**
```html
<div class="badge">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
    <circle cx="12" cy="12" r="3" fill="currentColor"/>
  </svg>
  Live představení
</div>
```

**CSS — base:**
```css
.badge {
  display: inline-flex;        /* NIKDY block */
  align-items: center;
  gap: 0.55em;
  padding: 0.55em 1.1em;
  background: var(--accent, #c9a961);
  color: var(--badge-text, #0a1628);
  border-radius: 999px;        /* pill */
  font-weight: 800;
  font-size: clamp(0.7rem, 0.95vw, 0.82rem);
  text-transform: uppercase;
  letter-spacing: 0.13em;
  width: fit-content;          /* POVINNÉ */
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  margin-bottom: clamp(1.2rem, 2vw, 2rem);
}
.badge svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}
```

**Varianty — vyber podle kontextu:**
```css
/* SOLID — silný akcent (CTA, hook, hero, varování) */
.badge.solid-gold  { background: #c9a961; color: #0a1628; box-shadow: 0 4px 16px rgba(201,169,97,0.25); }
.badge.solid-blue  { background: #00a3e0; color: #fff; box-shadow: 0 4px 16px rgba(0,163,224,0.3); }
.badge.warn        { background: #d42d2d; color: #fff; }
.badge.green       { background: #0e9b6e; color: #fff; box-shadow: 0 4px 16px rgba(14,155,110,0.3); }

/* OUTLINE — sekundární (section divider, jemnější eyebrow) */
.badge.outline {
  background: transparent;
  color: var(--accent, #c9a961);
  border: 1.5px solid currentColor;
  box-shadow: none;
  font-weight: 700;
}
```

**Pravidla badge — POVINNÁ:**
- **VŽDY ikona vlevo** (12–16px). Mapování: live=puls, varování=trojúhelník, info=kruh-i, čas=hodiny, hvězda=achievement.
- **VŽDY `inline-flex` + `width: fit-content`.** NIKDY block, NIKDY plná šířka.
- **Dva styly: SOLID nebo OUTLINE.** Solid = primární akcent. Outline = decentnější.
- **Kontrast:** Solid 7:1 (WCAG AAA). Outline: text/border musí jasně odskočit od pozadí.
- **Font-weight:** solid 800, outline 700. Nikdy normal weight.
- **Uppercase + letter-spacing 0.1–0.15em.**
- **Pill shape `border-radius: 999px`.**
- **Box-shadow JEN pro solid.** Outline NIKDY nemá shadow.
- **Žádné dvě badges vedle sebe** — badge je jeden, slouží jako eyebrow.

---

## 4. Cards — základní třídy

```css
/* Standardní bílá karta na světlém slidu */
.card {
  background: var(--white, #fff);
  border-radius: 16px;
  padding: clamp(1.2rem, 2vw, 2rem);
  box-shadow: 0 4px 12px rgba(10,22,40,0.04), 0 12px 32px rgba(10,22,40,0.06);
  border: 1px solid rgba(10,22,40,0.05);
}

/* Glass karta na tmavém slidu */
.card-glass {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-radius: 16px;
  padding: clamp(1.2rem, 2vw, 1.8rem);
  color: var(--white, #fff);
}

/* Stat card — pro velká čísla */
.stat-card { text-align: center; padding: clamp(1.2rem, 2vw, 2rem); }
.stat-num {
  font-size: clamp(2.5rem, 5.5vw, 4.5rem);
  font-weight: 900;
  color: var(--accent);
  line-height: 1;
  letter-spacing: -0.04em;
  font-variant-numeric: tabular-nums;
}
.stat-label {
  font-size: clamp(0.85rem, 1.2vw, 1.1rem);
  color: var(--gray, #5b6670);
  line-height: 1.4;
  font-weight: 500;
}
```

---

## 5. CTA Button

```css
.cta {
  display: inline-flex;
  align-items: center;
  gap: 0.7em;
  background: linear-gradient(135deg, var(--accent-light), var(--accent));
  color: var(--text-on-accent, #0a1628);
  padding: clamp(0.95rem, 1.5vw, 1.25rem) clamp(2rem, 3.5vw, 3rem);
  border-radius: 999px;
  text-decoration: none;
  font-weight: 800;
  font-size: clamp(0.95rem, 1.35vw, 1.15rem);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
  transition: transform 0.3s, box-shadow 0.3s;
  border: none;
  cursor: pointer;
}
.cta:hover {
  transform: translateY(-3px);
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
}
```

**Pravidla:** ikona vpravo (šipka, externí link), uppercase, gradient pozadí, výrazný stín pro depth, hover lift.

---

## 6. Progress Bar

```css
.progress-bar {
  position: fixed;
  top: 0; left: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--accent-cool), var(--accent-warm));
  z-index: 200;
  transition: width 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 0 12px rgba(255, 200, 100, 0.4);
}
```

JS aktualizuje `style.width` v `updateProgress()` (viz SlidePresentation třída).

---

## 7. Brand Mark — corner logo

Volitelný — fixní emblem v rohu, který se barevně přizpůsobuje pozadí slidu.

**HTML:**
```html
<div class="brand-mark" id="brandMark">
  <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <rect class="bg-rect" width="100" height="100" rx="14"/>
    <g class="stripes"><!-- brand glyph --></g>
  </svg>
</div>
```

**CSS:**
```css
.brand-mark {
  position: fixed;
  bottom: clamp(16px, 2vw, 28px);
  right: clamp(16px, 2vw, 28px);
  width: clamp(36px, 4vw, 50px);
  height: clamp(36px, 4vw, 50px);
  z-index: 100;
  opacity: 0.75;
  pointer-events: none;
}
```

**JS — invertuje barvy podle pozadí:**
```javascript
updateBrandMark(slide) {
  const bgRect = document.querySelector('.brand-mark .bg-rect');
  const stripes = document.querySelector('.brand-mark .stripes');
  if (!bgRect || !stripes) return;
  const isLight = ['light','pale','cream','warm'].some(c => slide.classList.contains(c));
  bgRect.setAttribute('fill', isLight ? '#0a1628' : '#ffffff');
  stripes.setAttribute('fill', isLight ? '#ffffff' : '#0a1628');
}
```

Volej v scrollObserver callback i v `goTo()`.

---

## 8. Section Divider — decor mezi sekcemi

```html
<div class="divider-decor">
  <div class="line"></div>
  <div class="diamond"></div>
  <div class="line"></div>
</div>
```

```css
.divider-decor {
  display: flex;
  align-items: center;
  gap: clamp(1rem, 2vw, 1.5rem);
  margin: clamp(1rem, 2vw, 1.5rem) 0;
}
.divider-decor .line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent) 20%, var(--accent) 80%, transparent);
  opacity: 0.4;
}
.divider-decor .diamond {
  width: 8px; height: 8px;
  background: var(--accent);
  transform: rotate(45deg);
  opacity: 0.5;
}
```
