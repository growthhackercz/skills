# Styles — 4 styly + generování frame.md z DNA

## frame.md = motion-design spec (obdoba design.md pro video)

Oficiální HyperFrames čte spec v pořadí **`frame.md` → `design.md` → `DESIGN.md`**. `frame.md` je preferovaný pro video: stejný formát, ale přepsaný pro **video frame ve zvoleném poměru stran (16:9 / 9:16 / 1:1 z Kroku 0) — pacing, scale, dwell, motion, kompozice** (ne web-UI měřítko). Pro 9:16/1:1 přepočítej kompozici (vertikální stack, hero zabírá víc výšky), ne jen crop 16:9.

**Generování (Krok 1):** z `brandDNA.md` (vizuální sekce) + `DESIGN.md` vytvoř `documents/videos/<slug>/frame.md` se sekcemi: Overview · Colors (s rolemi pro video) · Typography (scale pro 1080p, větší než web) · Motion (easing podpis, kontinuální kamera, depth) · Frame composition · Voice & content · Do's/Don'ts. Hotová CliqSales předloha: `{baseDir}/assets/frame.cliqsales.md`.

## Volba stylu z tónu DNA (doporuč, uživatel potvrdí)

| Signál v DNA | Styl |
|---|---|
| prémiový B2B SaaS, klid, důvěra | **Elegant SaaS** |
| hravost, B2C, mladá cílovka, energie | **Playful Pop** |
| tech autorita, tmavý brand (CliqSales!), data, výkon | **Dark Premium** |
| řemeslo, autenticita, lidskost, print feel | **Light Editorial** |

CliqSales own-brand = **Dark Premium**: navy `#01071A`, cyan `#119CFF` → mint `#97F8F4` gradient, Manrope (fallback Inter), velká tučná typografie. ⚠️ logo je bílé → vždy tmavé pozadí.

## Styl = paleta + typo + motion podpis + transitions + SFX paleta + music brief

| Styl | Motion podpis | Transitions | SFX (audio.md) | Music brief |
|---|---|---|---|---|
| **Elegant SaaS** | zdrženlivý, power3/expo.out, pomalé kamery | blur-through, gentle zoom | chimes, soft whoosh | „warm minimal piano + soft pads, sparse, 100–110 BPM, instrumental, resolves" |
| **Playful Pop** | spring, back.out(1.4–1.8), elastic, squash&stretch | push slide, zoom-through | boings, marimba, popy | „upbeat marimba + plucks, bouncy, 118–124 BPM, fun but premium" |
| **Dark Premium** | přesný, power4/expo.out, min overshoot, glow | zoom-through, shader (gravitational-lens), burn | měkké popy + sparkle, toggle | „dark ambient synth, focused, minimal perc, 95–105 BPM, resolves quietly" |
| **Light Editorial** | organický, kurzor-herec, typing, mikro-rotace | vertical push, blur crossfade | typing, soft pop, warm chime | „soft acoustic-electronic, warm, craft feel, 100–112 BPM" |

## Aplikace (Krok 4)

1. Vyber catalog bloky per beat (scene-catalog.md). 2. Rebrand na frame.md paletu (class override). 3. Uprav eases dle motion podpisu. 4. Beat grid: BPM z music briefu → časuj entrances na násobky doby. 5. Kontrast: akcent na světlém ztmav, na tmavém zesvětli (WCAG).

## Organika (každá scéna — „není to slide")

Kontinuální znatelná kamera (ne scale 1.05/8s — to oko nevidí) · overshoot + mikro-nedokonalosti (rotace ±1–2° co se srovná) · 3+ vrstvy hloubky · idle mikro-float po dopadu · nepravidelný stagger · vyplň frame (hero 60–80 % šířky) · kotvi k hraně, ne centrovaný stack.
