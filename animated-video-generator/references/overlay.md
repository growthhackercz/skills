# Textové vrstvy přes HyperFrames (overlay nad animací)

Veškerý text jde **až sem** — nad hotovou Seedance animaci, jako HyperFrames vrstva. Důvod: Seedance text komolí; HyperFrames dá ostrý brandový text, kinetiku a **zakryje gibberish** na obrazovkách ve videu. Ověřeno v reálné výrobě.

## Princip: video jako podklad + text comps nad ním

HyperFrames umí **`<video class="clip">`** jako podkladovou vrstvu (track 0) a nad ní transparentní sub-kompozice s textem. Render = headless Chromium projede timeline a sejme složené framy → MP4. Pak **muxneš zvuk** z Kroku 4/6.

`templates/overlay/` = hotový boilerplate (zkopíruj do projektu):
```
overlay/
├── hyperframes.json
├── package.json            # npx hyperframes@0.6.97 render
├── index.html              # root: <video class="clip"> podklad (track 0) + hosty comps
├── compositions/           # transparentní text vrstvy (whatif, roles, channels, sold, cta, typing, …)
└── assets/vendor/
    ├── gsap.min.js
    └── fonts/manrope-latin.woff2 + manrope-latin-ext.woff2
```

## Klíčová pravidla (jinak se to rozbije)

- **Podkladové video** = muted finální animace (extrahuj video stopu: `ffmpeg -i clip.mp4 -an base.mp4`). V `index.html`:
  `<video class="clip" data-layout-ignore src="assets/video/base.mp4" data-start="0" data-duration="<len>" data-track-index="0" muted playsinline style="object-fit:cover">`.
- **Každá timed vrstva** = `class="clip"` + `data-start` + `data-duration` + `data-track-index` (jinak lint error / neviditelná).
- **Timeline registrace** v každé comp: `window.__timelines["<composition-id>"] = gsap.timeline({paused:true})`. Animace relativní k `data-start` (t=0 = start comp).
- **Transparentní pozadí** comps (`background:transparent`), aby video prosvítalo.
- **Brand font Manrope** — `@font-face` v **KAŽDÉ** sub-kompozici (sub-comps nesdílí CSS), subset **latin + latin-ext** (oba `@font-face` s `unicode-range`). Háčky ř ž č ě ů ň jsou v **latin-ext** — bez něj zmizí jen háčkovaná písmena (zákeřné). Vendoruj woff2, `font-display:block`.
- **Per-písmeno elastická kinetika na velké texty** (povinné, anti-„placaté"): rozsekej headline na znaky, `gsap.fromTo` s `elastic.out`/`back.out` + **squash&stretch** (scaleY/scaleX overshoot), stagger ~0.03–0.05. Slovní fade je málo.
  - ⚠️ **Mezery v znakových spanech:** mezeru dej jako **`String.fromCharCode(160)` (nbsp)**, jinak se v `inline-block` znacích sbalí na nulu (text bez mezer!).
- **immediateRender:false** na entrance tweens, jejichž „from" stav je viditelný (např. burst ring s opacity>0) — jinak se prvek ukáže hned při mountu comp (zbloudilý kroužek).
- **Zakryj gibberish** — text vrstvy posaď přes obrazovky/materiály s komoleným textem (čistá karta s reálným textem, popisky, chipy).

## Typy vrstev (univerzální stavební bloky)

Skládej dle konceptu — co dává smysl pro daný message:

- **Headline / claim** — velký kinetický text na klíčový moment (per-písmeno elastic). **🛑 VŽDY zvýrazni JEN JEDNO klíčové slovo** (gradient/velikost) — nikdy víc slov jako velké naráz. Na řádku je maximálně jedno zvýrazněné slovo (pointa), zbytek běžnou vahou. (Stejné pravidlo jako titulky ve `video-generator`.)
- **Label chipy** — krátké štítky naskakující postupně (role, vlastnosti, kroky, kanály); časuj na VO, každý s „pop".
- **Info karta / mock UI** — čistá karta s reálným textem (např. odepisovaný požadavek = typewriter + nbsp + kurzor); posaď přes gibberish obrazovku.
- **Razítko / badge** — per-písmeno slam + ring burst na výsledek/win (+ odpovídající SFX).
- **CTA + logo** — závěrečná výzva + brand mark, kinetic, outro fade do černé.

> **Příklad (ai-marketer):** headline „Co kdybyste měli celý tým?" na nápad · chipy Stratég→Copywriter→Grafik · psací karta s požadavkem přes monitor · channel chipy Landing page/E-maily/Bannery/Social · razítko „VYPRODÁNO" + kasa · CTA „Získejte svůj AI tým" + CliqSales. To je *jedno* naplnění bloků výše.

## Sync overlay na hlas (whisper word-timestamps) — POVINNÉ, ať text trefuje scény

Text NESMÍ jen „přibližně" sedět — musí naskočit přesně, když VO to slovo řekne (jinak klient vidí „text skáče moc brzo"). Nehádej časy, **změř hlas**:

1. Přepiš hotový VO na slova s časy: `fal_client.subscribe("fal-ai/whisper", arguments={"audio_url":url, "task":"transcribe", "language":"cs", "chunk_level":"word"})` → `chunks[].timestamp` dá přesný čas (s) každého slova. Počítej **absolutní** čas = `vo_offset + slovo_ts` (kde `vo_offset` = kam v timeline beat sázíš; u atempo beatu `vo_offset + ts/atempo`).
2. Pro každou text vrstvu najdi v transkriptu klíčové slovo (brand, benefit, pointa) a nastav `data-start` tak, aby prvek naskočil ~0–0.2 s **před** tím slovem (text vyjede, pak ho hlas „dořekne").
3. Chipy/odrážky časuj postupně na výčet ve VO (každý na své slovo), ne všechny naráz.
4. Po každé změně VO (jiný přednes = jiné délky slov) **znovu změř** a přerovnej — staré časy neplatí.
5. **Délku videa neprotahuj kvůli VO** — když mluvené přeteče konec, vejdi hlas dovnitř (lehké `atempo` na beat, ne natahování videa).

## Workflow

1. Zkopíruj `templates/overlay/` do `documents/videos/<slug>/_overlay/`, dej `base.mp4` do `assets/video/`.
2. Uprav `index.html` (délka, hosty vrstev) — **časy vrstev odvoď z whisper přepisu VO** (viz „Sync overlay na hlas" výše), ne od oka. Napiš/uprav comps.
3. `npx hyperframes@0.6.97 lint` → **0 errors** (warnings o self-selektoru jsou OK).
4. `npx hyperframes@0.6.97 render` → `renders/*.mp4` (muted, s textem).
5. QA frame (Read) — diakritika sedí, kinetika, pozice, gibberish zakrytý.
6. Muxni zvuk (Krok 6).

## Finální endcard (prolnutí do bílé/barvy) — ať NEZMIZÍ text

Ověřený recept (klient typicky chce: hero se prolne do bílé/barvy + zůstane CTA text + objeví se logo):
- **Barevná vrstva (bílá) jde PŘES hero, ale POD textem a logem** — vlastní full-screen comp `opacity:0→1` (`ease:"power2.in"` = pomalu→zrychlí), `z-index` **nižší** než CTA a logo, **vyšší** než hero. Jinak bílá překryje i text (a bílý/světlý text na bílé **zmizí**).
- **CTA text drží do konce a má svůj scrim** (tmavý/barevný gradient dole) — na bílé je díky scrimu pořád čitelný. Prodluž jeho `data-duration` až do konce.
- **Logo `fade in` (opacity, POMALU ~2 s, bez pop/scale)** nad bílou; tmavé logo na bílé je vidět bez halo.
- **Hero zmraž do konce:** base video je kratší než celkové video → předpřiprav `base-hold.mp4` (`ffmpeg -vf tpad=stop_mode=clone:stop_duration=N`) a dej ho jako base track s `data-duration` do konce; jinak po konci klipu černá.
- ❌ NEDĚLEJ fade-do-barvy přes celý obraz (skryje text), ❌ NEDĚLEJ ostrý freeze-pak-fade (pohyb se viditelně „zasekne" — prolínej **přes živý pohyb**, ease-in).
