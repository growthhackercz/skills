# Animation Patterns Reference

**Načti tento soubor když:**
- Animuješ vstup elementů na slide (reveal, card-reveal, line-reveal, atd.)
- Voláš style-specifický efekt podle nálady (dramatic, techy, playful…)
- Implementuješ keyframes (float, glow, pulse, particle)
- Řešíš `prefers-reduced-motion` accessibility

---

## Komponentní animace — POVINNÉ (staggered reveal)

**Žádný element nesmí být viditelný bez animace.** Když slide vstoupí do viewportu, elementy se postupně odkrývají se staggered delay — to vytváří dojem orchestrované animace.

### Base reveal (fade + slide up)

```css
.reveal {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.7s var(--ease-out-expo),
              transform 0.7s var(--ease-out-expo);
}
.slide.visible .reveal { opacity: 1; transform: translateY(0); }

/* Staggered delays — třídy r1–r8 pro postupné odkrývání */
.r1 { transition-delay: 0.10s; }
.r2 { transition-delay: 0.25s; }
.r3 { transition-delay: 0.40s; }
.r4 { transition-delay: 0.55s; }
.r5 { transition-delay: 0.70s; }
.r6 { transition-delay: 0.85s; }
.r7 { transition-delay: 1.00s; }
.r8 { transition-delay: 1.15s; }
```

Použití: `<h2 class="reveal r2">...</h2>`. Třídy r1, r2, r3 podle pořadí na slidu.

### Card reveal (scale + fade)

```css
.card-reveal {
  opacity: 0;
  transform: scale(0.92) translateY(20px);
  transition: opacity 0.65s var(--ease-out-expo),
              transform 0.65s var(--ease-out-expo);
}
.slide.visible .card-reveal { opacity: 1; transform: scale(1) translateY(0); }
```

### Line reveal (separator/divider)

```css
.line-reveal {
  width: 0;
  height: 2px;
  background: var(--accent);
  transition: width 1s var(--ease-out-expo) 0.4s;
  margin: clamp(1rem, 2vw, 2rem) 0;
}
.slide.visible .line-reveal { width: clamp(60px, 8vw, 120px); }
```

### Slide from sides (split layouts)

```css
.reveal-left {
  opacity: 0;
  transform: translateX(-50px);
  transition: opacity 0.9s var(--ease-out-expo),
              transform 0.9s var(--ease-out-expo);
}
.reveal-right {
  opacity: 0;
  transform: translateX(50px);
  transition: opacity 0.9s var(--ease-out-expo),
              transform 0.9s var(--ease-out-expo);
}
.slide.visible .reveal-left,
.slide.visible .reveal-right { opacity: 1; transform: translateX(0); }
```

### Scale (citáty, obrázky)

```css
.reveal-scale {
  opacity: 0;
  transform: scale(0.85);
  transition: opacity 0.9s var(--ease-out-expo),
              transform 0.9s var(--ease-out-expo);
}
.slide.visible .reveal-scale { opacity: 1; transform: scale(1); }
```

### Blur in (obrázky)

```css
.reveal-blur {
  opacity: 0;
  filter: blur(10px);
  transition: opacity 0.8s, filter 0.8s var(--ease-out-expo);
}
.slide.visible .reveal-blur { opacity: 1; filter: blur(0); }
```

---

## Mapování elementů na animace — POVINNÁ pravidla

| Element | Třída | Delay |
|---------|-------|-------|
| Nadpis | `.reveal .r2` | 0.25s |
| Podnadpis / popisek | `.reveal .r3` | 0.40s |
| Karty v gridu | `.card-reveal .r3..r6` | rostoucí |
| Bullet pointy `<li>` | `.reveal .r1..r6` | rostoucí |
| Tabulky | `.reveal` (celá) NEBO řádky se stagger |
| Citáty | `.reveal-scale` | 0.40s |
| Čísla / statistiky | `.reveal` + `.counter` (JS count-up) |
| CTA tlačítko | `.reveal` s nejvyšším delay (přijde poslední) |
| Obrázky | `.reveal-scale` nebo `.reveal-blur` |
| Section divider linie | `.line-reveal` + nadpis `.reveal` |

---

## prefers-reduced-motion (POVINNÉ)

Vždy respektuj uživatelské preference:

```css
@media (prefers-reduced-motion: reduce) {
  .reveal, .card-reveal, .reveal-left, .reveal-right,
  .reveal-scale, .reveal-blur, .line-reveal {
    opacity: 1 !important;
    transform: none !important;
    filter: none !important;
    transition: none !important;
    animation: none !important;
  }
  .line-reveal { width: clamp(60px, 8vw, 120px) !important; }
}
```

---

## Background ambient effects (keyframes)

### Floating glow blobs (atmosferický efekt na tmavém slidu)

```css
.ambient-glow {
  position: absolute;
  inset: 0;
  overflow: hidden;
  z-index: 1;
  pointer-events: none;
}
.ambient-glow::before, .ambient-glow::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
}
.ambient-glow::before {
  width: 700px; height: 700px;
  background: radial-gradient(circle, rgba(0,163,224,0.35), transparent 70%);
  top: -250px; left: -150px;
  animation: float 22s ease-in-out infinite;
}
.ambient-glow::after {
  width: 550px; height: 550px;
  background: radial-gradient(circle, rgba(201,169,97,0.28), transparent 70%);
  bottom: -180px; right: -100px;
  animation: float 28s ease-in-out infinite reverse;
}
@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(80px, 50px); }
  66% { transform: translate(-40px, 80px); }
}
```

### Pulse (live indikátor)

```css
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.7; }
}
.pulse-dot { animation: pulse 2s ease-in-out infinite; }
```

---

## Effect-to-Feeling Guide

Vyber animační styl podle zamýšleného pocitu prezentace.

| Feeling | Animations | Visual Cues |
|---------|-----------|-------------|
| **Dramatic / Cinematic** | Slow fade-ins (1-1.5s), large scale transitions (0.9 to 1), parallax scrolling | Dark backgrounds, spotlight effects, full-bleed images |
| **Techy / Futuristic** | Neon glow (box-shadow), glitch/scramble text, grid reveals | Particle systems (canvas), grid patterns, monospace accents, cyan/magenta/electric blue |
| **Playful / Friendly** | Bouncy easing (spring physics), floating/bobbing | Rounded corners, pastel/bright colors, hand-drawn elements |
| **Professional / Corporate** | Subtle fast animations (200-300ms), clean slides | Navy/slate/charcoal, precise spacing, data visualization focus |
| **Calm / Minimal** | Very slow subtle motion, gentle fades | High whitespace, muted palette, serif typography, generous padding |
| **Editorial / Magazine** | Staggered text reveals, image-text interplay | Strong type hierarchy, pull quotes, grid-breaking layouts, serif headlines + sans body |

## Entrance Animations

```css
/* Fade + Slide Up (most versatile) */
.reveal {
    opacity: 0;
    transform: translateY(30px);
    transition: opacity 0.6s var(--ease-out-expo),
                transform 0.6s var(--ease-out-expo);
}
.visible .reveal {
    opacity: 1;
    transform: translateY(0);
}

/* Scale In */
.reveal-scale {
    opacity: 0;
    transform: scale(0.9);
    transition: opacity 0.6s, transform 0.6s var(--ease-out-expo);
}

/* Slide from Left */
.reveal-left {
    opacity: 0;
    transform: translateX(-50px);
    transition: opacity 0.6s, transform 0.6s var(--ease-out-expo);
}

/* Blur In */
.reveal-blur {
    opacity: 0;
    filter: blur(10px);
    transition: opacity 0.8s, filter 0.8s var(--ease-out-expo);
}
```

## Background Effects

```css
/* Gradient Mesh — layered radial gradients for depth */
.gradient-bg {
    background:
        radial-gradient(ellipse at 20% 80%, rgba(120, 0, 255, 0.3) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(0, 255, 200, 0.2) 0%, transparent 50%),
        var(--bg-primary);
}

/* Noise Texture — inline SVG for grain */
.noise-bg {
    background-image: url("data:image/svg+xml,..."); /* Inline SVG noise */
}

/* Grid Pattern — subtle structural lines */
.grid-bg {
    background-image:
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 50px 50px;
}
```

## Interactive Effects

```javascript
/* 3D Tilt on Hover — adds depth to cards/panels */
class TiltEffect {
    constructor(element) {
        this.element = element;
        this.element.style.transformStyle = 'preserve-3d';
        this.element.style.perspective = '1000px';

        this.element.addEventListener('mousemove', (e) => {
            const rect = this.element.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            this.element.style.transform = `rotateY(${x * 10}deg) rotateX(${-y * 10}deg)`;
        });

        this.element.addEventListener('mouseleave', () => {
            this.element.style.transform = 'rotateY(0) rotateX(0)';
        });
    }
}
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Fonts not loading | Check Fontshare/Google Fonts URL; ensure font names match in CSS |
| Animations not triggering | Verify Intersection Observer is running; check `.visible` class is being added |
| Scroll snap not working | Ensure `scroll-snap-type: y mandatory` on html; each slide needs `scroll-snap-align: start` |
| Mobile issues | Disable heavy effects at 768px breakpoint; test touch events; reduce particle count |
| Performance issues | Use `will-change` sparingly; prefer `transform`/`opacity` animations; throttle scroll handlers |
