# Přechody — oficiální HyperFrames knihovna → recepty

Přechody mezi scénami **bereme z oficiální HyperFrames catalog knihovny** (`npx hyperframes@0.6.97 catalog` / `add`), ne vymýšlíme vlastní od nuly. Tahle reference je mapa knihovny + praktické recepty, kdy co použít a jak to spolehlivě integrovat.

## Jak je dostat

```bash
npx hyperframes@0.6.97 catalog | grep -i transition      # seznam
npx hyperframes@0.6.97 add <jméno>                        # → compositions/<jméno>.html
```

## Katalog (k 0.6.97)

**Shader přechody (block, fragment shader, 2 textury → mix):**
`domain-warp-dissolve` · `ridged-burn` · `whip-pan` · `sdf-iris` · `ripple-waves` · `gravitational-lens` · `cinematic-zoom` · `chromatic-radial-split` · `glitch` · `swirl-vortex` · `thermal-distortion` · `flash-through-white` · `light-leak` · `cross-warp-morph`

**Komponentové přechody (CSS/SVG/GSAP, čisté, světlo-friendly):**
`parallax-zoom` (zoom karty do plného framu — eBay hero) · `parallax-unzoom` (reverz) · `grid-pixelate-wipe` · `morph-text` (gooey text morph mezi slovy)

**Showcase sety (víc variant v jednom bloku, na inspiraci/výběr):**
`transitions-3d` · `transitions-blur` · `transitions-cover` · `transitions-dissolve` · `transitions-distortion` · `transitions-grid` · `transitions-light` · `transitions-mechanical` · `transitions-push` · `transitions-radial` · `transitions-scale` · `transitions-destruction` · `transitions-other`

## Kurátorovaná sada (default — rotuj tyhle) ⭐

Ověřená paleta přechodů, kterou střídej napříč videem:

```bash
npx hyperframes add flash-through-white parallax-unzoom light-leak transitions-cover
```

- **`flash-through-white`** — bílý flash crossfade. Energický „cut" na beatu / mezi sekcemi (rychlý, čistý, světlo-friendly).
- **`parallax-unzoom`** — focus karta se zmenší z plného framu a sourozenci naparalaxují do gridu (reverz `parallax-zoom`). Ideál na **odhalení / přechod z hero detailu do přehledu**.
- **`light-leak`** — cinematic light-leak overlay. Teplý, prémiový přechod mezi „kapitolami".
- **`transitions-cover`** — cover/uncover slide (nová scéna zakryje starou). Čistý směrový přechod, blízký našemu push/swipe.
- doplňkově: `parallax-zoom` na **vstup** do hero scény, `whip-pan` / `sdf-iris` jako světlo-friendly shader.

Drž **konzistenci**: 3–4 přechody na rotaci, ne 8 různých efektů.

## Integrační kontrakt shader přechodů

Shader block = **self-contained showcase wrapper**: má vlastní demo scény + toy DOM-rasterizer (umí jen plochou barvu + centrovaný text) + fragment shader s uniformy `u_from` / `u_to` / `u_progress` / `u_resolution`, který mixuje dvě textury podle progressu (0→1) řízeného GSAP timeline.

⚠️ **Toy rasterizer nezachytí bohatý obsah** (glass karty, fotky, gradienty). Pro reálné scény ho NEpoužívej jak je — vezmi jen jeho **shader jádro** a krm ho **reálnými framy**.

### Recept A — autentický shader přechod (two-pass textury)
1. Vyrenderuj scénu A → vytáhni poslední frame (`ffmpeg -ss <end> -frames:v 1`) → `assets/textures/A.png`.
2. Vyrenderuj scénu B → první frame → `B.png`.
3. `transition-<x>.html`: WebGL, načti A/B jako `<img>` textury (`UNPACK_FLIP_Y_WEBGL`), pusť shader jádro bloku, `u_progress` 0→1 přes GSAP proxy (deterministicky, žádný `Math.random`/`Date.now`).
4. Wire: A (0→t) · transition (t-0.1→t+0.7, z-top, opaque) · B (t-0.3→…). Přechod kryje šev; na progress 0 ukazuje A-frame, na 1 B-frame → plynulý handoff.

### Recept B — čistý kódovaný přechod (spolehlivé, bez textur) ⭐ default
Often lepší než shader: **push/swipe** nebo **crossfade** uvnitř vlastních timeline scén, bez texture-capture.
- **Push (silný):** scéna A v exitu `x: 0→-660, opacity→0`; scéna B v entrance `x: +680→0`; v indexu se překryjí ~0.6 s → swipe. (Pozor: pokud má wrapper Ken Burns na `x`, ukonči ho před exitem, ať se `x` nepere.)
- **Crossfade (jemný):** A exit `opacity→0 + blur`; B entrance `opacity 0→1`; překryv ~0.4 s.
- **parallax-zoom:** komponentový, čistý — zoom prvku do framu, ideál pro „vstup do scény".

## Kdy co (lekce z produkce)

- **Default = čistý push/crossfade (Recept B).** Spolehlivé, deterministické, timing-nezávislé, sedí na světlo i tma.
- **Flashy shader přechody (smoke domain-warp, light-leak flash) klient často odmítne** — působí gimmickově a tmavě. Nasazuj je střídmě, **lad paletu** (na světlém videu světlo-friendly: whip-pan / sdf-iris / parallax-zoom, ne tmavý smoke).
- **„Silnější přechod" ≠ flashy.** Většinou znamená: z měkkého crossfade → **push/swipe** (výrazný směrový pohyb), ne přidat efekt navíc.
- **Variuj** napříč videem (push mezi setup scénami, zoom do hero scény), ale drž konzistentní jazyk — ne 6 různých efektů.
- Přechod = i **zvuková stopa**: whoosh/swoosh z HeyGen na švu (viz `audio.md`).
- **⚠️ Přechod NENÍ volitelný.** Holý střih / opacity fade mezi scénami = „rozanimovaný PowerPoint". Každý šev = vizuální přechod (push/cover/flash/zoom-through) + whoosh na stopě.
