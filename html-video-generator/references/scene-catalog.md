# Scene catalog — výběr + rebrand oficiálních bloků

**Klíč k „vypadá jako film, ne slide": použij oficiální catalog bloky (3D/WebGL/shader/parallax), nestav ploché GSAP scény.** HyperFrames má 110+ produkčních bloků.

## Procházení + instalace

```bash
npx hyperframes@0.6.97 catalog            # všechny bloky + tagy
npx hyperframes@0.6.97 catalog --json     # strojově (filtruj tagem)
npx hyperframes@0.6.97 add <jméno>        # nainstaluje do compositions/<jméno>.html
```

## Filmové bloky (podle tagu)

- **WebGL VFX:** `vfx-portal`, `vfx-magnetic`, `vfx-shatter`, `vfx-liquid-glass`
- **Shader transitions:** `gravitational-lens`, `domain-warp-dissolve`, `whip-pan`, `ripple-waves`, `sdf-iris`, `glitch`
- **Parallax + kamera:** `parallax-zoom`, `parallax-unzoom`, `caption-parallax-layers`
- **3D:** `app-showcase` (floating phones, CSS-3D), `ui-3d-reveal`, `vfx-iphone-device` (GLTF)
- **Částice/morf/post:** `caption-particle-burst`, `morph-text`, `motion-blur`, `vignette`, `grain-overlay`
- **html-in-canvas hero** (1–3 beaty/video): živý DOM jako GPU textura (`drawElementImage`) — iPhone/MacBook mockup, liquid glass, portal, shatter. Viz oficiální `guides/html-in-canvas.md`.

## ⚠️ Render viabilita (ověřeno lokálně headless)

- ✅ **CSS-3D** (`app-showcase`) — 100% jistota, žádná závislost.
- ✅ **WebGL** (`vfx-portal`, THREE z CDN) — renderuje headless (WebGL probe prošel).
- ⚠️ **WebGPU / liquid-glass** — chce lokální `lib/*.iife.js`, co se bare instalací NEstáhne → `ReferenceError` → černé video. Před nasazením OVĚŘ renderem.
- html-in-canvas se auto-detekuje a pinuje 1 worker (fleet-OK).

**Pravidlo: každý blok nejdřív vyrenderuj „as-is" (test viability), než ho rebrandneš.**

## Rebrand na frame.md (ověřený postup)

Bloky jsou plné HTML dokumenty s hardcoded hex (fitness/demo brand). Přebarvení = **class-based override, NE slepý hex-swap** (ten rozbije role):

1. **Globální safe swap** jednoznačného akcentu: `#<lime/demo-accent>` → frame.md `--accent`; muted text → frame.md muted. (String replace na celém souboru — chytí i SVG `fill=`/`stroke=`.)
2. **Override `<style>`** na konci kompozice s `!important` per třída (pozadí, povrchy, text colors) — neřeší role-guessing, jen přepíše: `[data-composition-id="X"] .bg { background: <navy> !important; }`.
3. **Text content** swap (fitness copy → CliqSales AI-tým copy, vykání, generické role).

Ověř `scan_theme_colors.py` (jen frame.md paleta) + proof framy.

## Wiring scén (root index.html)

- Sub-komp = **plný HTML dokument** přes `data-composition-src`. Host v rootu: `class="clip"`, `data-composition-id` IDENTICKÉ s id v souboru bloku, `data-start/duration/track-index`, rostoucí `z-index`.
- Scény střídají track 0/1 (stejný track nesmí overlap), overlap 0.4–0.6s. **Captions = vlastní kompozice na vyšším tracku.** Root má vlastní master timeline (může řídit přechod).
- ⚠️ Root index.html bez HTML komentářů (linter je parsuje). Vendoruj GSAP/THREE do `assets/vendor/` pro fleet (dev CDN OK).

## Hero strategie per video

1–3 „wow" beaty z catalogu (portal/3D/glass/shader) + zbytek lehčí (kinetic type, cards, stat). Příliš mnoho WebGL = pomalý render + flatten dojmu. Mezi scénami shader transition na hero reveal, blur/zoom na spojovací.
