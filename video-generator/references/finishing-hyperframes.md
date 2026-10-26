# Finishing — HyperFrames titulky/flash/punch + hudba + mux

Finishing vrstva nad vyrenderovanými (a ořezanými) klipy. Engine: **oficiální HyperFrames** (`npx hyperframes@0.6.97`), render lokálně, silent → zvuk se domixuje ffmpegem. Šablona: `{baseDir}/templates/hf-index.template.html`.

## Setup

```bash
npx hyperframes@0.6.97 init hf --resolution portrait     # 9:16 → portrait, 16:9 → landscape
cd hf && mkdir -p assets/clips assets/vendor/fonts
cp ../_shots_trim/*.mp4 assets/clips/
# font s českou diakritikou (latin + latin-ext!) — např. Poppins:
curl -s -o assets/vendor/fonts/poppins-500-latin.woff2    "https://cdn.jsdelivr.net/npm/@fontsource/poppins@5/files/poppins-latin-500-normal.woff2"
curl -s -o assets/vendor/fonts/poppins-500-latinext.woff2 "https://cdn.jsdelivr.net/npm/@fontsource/poppins@5/files/poppins-latin-ext-500-normal.woff2"
# stejně 800 + 900
```

⚠️ **latin-ext je povinný** — háčkovaná písmena (ř ž č ě š ů) jsou v latin-ext; bez něj zmizí jen háčky (zákeřné). Po renderu vždy zkontroluj QA frame s českým textem.

## Pravidla kompozice (HyperFrames kontrakt)

- Každý časovaný element: `class="clip"` + `data-start` + `data-duration` + `data-track-index` + **unikátní `id`** (video bez id je v renderu ZAMRZLÉ).
- Videa `muted playsinline`; timeline `gsap.timeline({paused:true})` registrovaná na `window.__timelines["main"]`.
- Žádný `Math.random()` / `Date.now()` — deterministický render.
- Po každé změně: `npx hyperframes lint` (0 errors) → `npm run render`.

## Titulky — ZÁVAZNÁ pravidla (opakovaně vyladěno s Pavlem)

1. **Verbatim** — přesně co postava říká, žádné parafráze/headliny.
2. **NIKDY přes obličej** — spodní třetina, scrim gradient pod nimi pro čitelnost; při zvětšování kontroluj proof frame.
3. **Kineticky po slovech** — slova naskakují postupně (stagger rozprostřený přes řečové okno), ne celá věta naráz.
4. **Váhy:** běžná slova normální (500), **tučně jen zvýrazněné** (800/900).
4b. **🛑 VŽDY JEN JEDNO zvýrazněné klíčové slovo na titulek (big).** Nikdy víc slov jako velké — jen jedno (pointa repliky). `build-finishing.py` to i vynucuje: má-li `big` víc slov, přebytek přesune do běžných slov a zvýrazní jen poslední. V briefu proto do `big` piš jedno slovo. (Platí i pro `animated-video-generator` — viz jeho `references/overlay.md`.)
5. **Klíčové slovo:** VĚTŠÍ, gradient, a **vždy na samostatném řádku** (nikdy nenavazuje na běžný text); utažené řádkování (line-height ~0.9–1.0).
6. **Gradient klíčových slov = brand barvy, směr světlá → tmavší**, ale čitelný (neon, ne temný odstín). **Zdroj barev (pořadí):** 1) `brand/DESIGN.md` (přesné HEX akcenty/gradient), 2) není-li DESIGN.md → **extrakce z `logo.png`** (vysampluj světlý a tmavý konec gradientu loga, viz PIL postup v `storyboard-a-keyframy.md`), 3) fallback `brand-board.png`. Stejné barvy pro punch, end-card glow i storyboard paletu — jeden zdroj pravdy do briefu (`subtitles.gradient`). CliqSales aktuálně: `#5AE8FF → #14A8FF → #0056C8`.
6b. **Titulek NIKDY nezasahuje do další scény (POVINNÉ).** Každý titulek patří své scéně — `build-finishing.py` clampuje jeho konec na hranici scény (`scene_end − 0.06 s`). Když scénu zkrátíš (mid-cut/trim), stačí znovu spustit `build-finishing.py`: přewhisperuje finální `_base` a časy se **samy zkrátí i posunou** (řez → kratší scéna → kratší i posunuté následné titulky), takže se nic ručně nedočasovává ani nekontroluje. Bez clampu titulek předchozí repliky „problikne“ přes první framy dalšího záběru.

7. **Časování slovo-na-slovo z FINÁLNÍHO videa (POVINNÝ POSLEDNÍ KROK):** Titulky **NIKDY nečasuj z per-scene klipů** — mid-cuty, trimy a ořezy posouvají časy a titulky pak „lítají“. Jako **úplně poslední krok před schválením**, až je sestřih hotový: přewhisperuj **finální sestříhanou dialogovou stopu** (`_base.mp4` = concat ořezaných klipů = přesná finální timeline) přes `fal-ai/whisper` `chunk_level: word` → dostaneš **absolutní časy slov ve výsledném videu**. Titulky (v pořadí scén) namapuj na tyhle absolutní časy — žádný přepočet start scény/lead, žádný stagger. Sloučená whisper slova („dorána“, „Teď už“) rozděl proporcionálně dle délky znaků. **Big/klíčové slovo o více slovech** (např. „Teď už to umím“) v alignmentu spotřebuj po slovech (jinak se vše za ním posune). Po každém dalším střihu časování **znovu** (whisper finálu → přemapuj).
8. **Vždy na střed** — celý titulek i velké klíčové slovo horizontálně centrované (`text-align:center`, flex `justify-content:center`, container full-width). Nikdy doleva.
9. **Jedna replika = jeden titulek (NIKDY nemíchat mluvčí).** Když mluví dvě postavy, titulky se nespojují do jednoho bloku: replika postavy A se zobrazí, po dořečení **zmizí**, teprve pak naskočí replika postavy B. I delší monolog děl po větách/replikách. Hranice = word-timestampy (konec poslední word repliky + ~0,3 s).

## Dokumentární režim titulků (rodina „dokument“)

U **dokumentárního příběhu** (viz `concept-families.md`) NEpoužívej velké kinetické big-slovo ani flash-to-white — to prozradí reklamu a zabije „native“ pocit. Místo toho střídmý dokumentární look:

- **Dialogové titulky decentní** — v briefu nastav `subtitles.style: "documentary"`; `build-finishing.py` pak vykreslí VŠECHNA slova (i klíčová) jako menší bílá slova bez velkého gradientového big-slova a bez per-letter kinetiky (jen jemný fade). Časování stále z whisperu finálního `_base` (clamp na střihy platí stejně).
- **Lower-third** (jméno + role, např. „**Marek** · majitel e-shopu“) = **ruční overlay** — přidej do `hf/index.html` malý `<div>` vlevo dole (track-index nad videem), zobraz ho jednou při prvním záběru postavy s jemným fade-in/out. `build-finishing.py` ho negeneruje (je to jednorázový prvek per video).
- **`flashes` v briefu nech PRÁZDNÉ** a **`punch` = null** — dokument nemá flash-to-white ani obří slovo (prozradí reklamu). Nanejvýš jemný dip-to-black u velkého časového skoku (ruční).
- Grade tlumený, případně lehký film grain overlay v HF; ambientní zvuk hlasitější v mixu (dokument žije atmosférou), hudba velmi decentní nebo žádná.

## Flash-to-white přechody (na hrubé střihy)

**Flash je záchrana, ne default.** Používej ho JEN na střihy s vyloženou nesouvislostí (skok kontextu, nenavazující gesta, přechod do end-cardu) — flash na každém střihu působí rušivě, zvlášť když jdou rychle za sebou. Běžné konverzační střihy (OTS šachovnice, motivovaný insert „vytáhne telefon → detail telefonu“) nech čisté. Crossfade vypadá špatně; fix na nesouvislost = plynulý fade do PLNÉ bílé přes střih:

```js
// cut = čas střihu; první/hlavní flash klidně delší
tl.fromTo("#flashN", {opacity:0}, {opacity:1, duration:0.50, ease:"sine.inOut"}, cut - 0.54);
tl.to("#flashN", {opacity:0, duration:0.58, ease:"sine.inOut"}, cut + 0.10);
```
Ověř luma scanem, že bílá reálně dojede na ~250 (jinak je to „vachrlaté“). Flash dej na každý hrubý střih (i do end-cardu).

## Punch slovo (volitelné — obří slovo na flash)

Obří slovo (např. „NE!“) v brand gradientu přes celý obraz, **synced přesně na vyslovené slovo** (změř silencedetectem):
- **Rychlý pop** na slově (`duration 0.14, back.out(2)`), NE pozvolný náběh předem.
- Zmizí **bez fade** (`tl.set(..., {opacity:0})`) v okamžiku, kdy je flash ještě plně bílý — schová se pod bílou.

## Hudba (HeyGen) + mux

1. `scripts/heygen-music.py --query "cinematic build epic" --min-duration <délka>` → stáhne track z HeyGen knihovny.
2. `scripts/mux-final.py --video <hf-render.mp4> --dialog <concat-dialogu.mp4> --music <track.wav>`:
   - dialog = hlavní stopa; hudba **s gradací** (intro ~0.09 → build → vrchol ~0.40 na CTA scéně),
   - sidechain ducking pod řeč, fade-in 1 s, **fade-out delší ~2,8 s** (doznění na end-cardu).

## Pořadí operací

trim klipů → concat dialogové stopy (`_base.mp4`) → HF projekt (klipy + titulky + flash + punch) → `npm run render` (silent) → mux (render video + dialog audio + hudba) → proof framy + poslech → finál.

## Mid-cut UVNITŘ generace — VŽDY řež na scene-hranici (KRITICKÉ)

Když vyřezáváš kus uvnitř jedné omni generace (odstranění vaty, hluchého gesta, zvednuté ruky…), **bod, na který skočíš (cutB), MUSÍ být přesně vnitřní scene-cut generace** — moment, kdy omni přepnul na další záběr. Jinak po řezu ještě probleskne konec předchozího záběru a vznikne viditelný ošklivý hard-cut „uprostřed pohybu“.

Postup: detekuj scene-cuty (`ffmpeg -vf "select='gt(scene,0.25)',showinfo"` → `pts_time`), a cutB nastav na první scene-cut za místem, kde chceš řezat. cutA (odkud) může být kdekoli (např. konec repliky), ale **cutB VŽDY = scene-hranice**, ať navazuješ na čistý začátek dalšího záběru, ne doprostřed předchozího. Když v požadovaném okně žádná scene-hranice není, generaci nelze čistě mid-cutnout — zkrať jinde nebo přegeneruj s tvrdým střihem na tom místě.

## Trim — pozor na bezdialogový závěrečný beat

Auto-trim „konec = poslední slovo + pad“ **uřízne bezdialogové dohrání scény** (podání ruky, úsměv, reakce, tap). Když scéna končí záměrným němým beatem (v shot_type/prompt je závěrečný akční moment bez repliky), nastav `trim.out` ručně **až za ten beat** (do briefu), ne na poslední slovo. Radši nech scénu dohrát než useknout pointu.
