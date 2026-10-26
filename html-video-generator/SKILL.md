---
name: html-video-generator
version: "1.1"
publishedAt: "2026-07-04"
description: Vyrobí nádherné animované produktové video (MP4 1920×1080, 30–90 s, škáluje do 2–3 min) z brand DNA + product DNA. Načte brand jazyk, vybere styl, vygeneruje frame.md (motion spec) a scénář, poskládá scény z oficiálního HyperFrames catalogu (3D, WebGL, shadery, parallax — ne ploché slidy), napojí HeyGen hudbu a HRAVÉ zvukové efekty, vyrenderuje lokálně a projde produkční QA (proof framy, kontinuita, surgical edity). Žádný cloud render. Každé utrácení kreditů schvaluješ předem. Umí i „video ze stránky / z webu / z URL": uživatel řekne „udělej mi video ze stránky" a vloží odkaz → capture webu (`hyperframes capture <URL>`) vytěží reálné texty, fotky, barvy a loga přímo do scén.
category: creative
status: stable
metadata: {"openclaw":{"requires":{"bins":["python3","ffmpeg","node"],"env":["FAL_KEY"]},"primaryEnv":"HEYGEN_API_KEY","emoji":"🎬"}}
---

# HTML Video Generator

Z brand + product DNA udělá animované produktové video. **Tenká produkční vrstva nad oficiálním HyperFrames** (engine řeší scénu/render), my řešíme: brand → styl → scénář → výběr/rebrand catalog bloků → audio → render → QA.

**Pipeline (5 fází):** Intake → Spec → Scene → Sync → Proof.

## Globální pravidla (každý krok)

- **Stavíme na oficiálním HyperFrames** (`npx hyperframes@0.6.97`): `init`, `catalog`/`add`, `lint`, `validate`, `render`, `snapshot`. NEreimplementovat engine.
- **Scény = catalog blocky + html-in-canvas + frame adapters** (3D/WebGL/shader/parallax), NE ploché GSAP slidy. „Vypadá jako prezentace" = chyba.
- **Poměr stran** (z Kroku 0: 16:9 / 9:16 / 1:1) drží **celá pipeline**: HyperFrames `init --resolution` (`landscape` 1920×1080 / `portrait` 1080×1920 / `square` 1080×1080), `data-width`/`data-height` každé scény, storyboard vizuál panely i frame.md kompozice. Mock framy a scény mají VŽDY poměr cílového videa — 9:16/1:1 se **přepočítá** (vertikální stack, hero zabírá víc výšky), ne crop z 16:9.
- **Přechody bereme z oficiální HyperFrames catalog knihovny** (`hyperframes catalog`/`add`; recepty v `references/transitions.md`). Default = čistý push/crossfade; shader přechody střídmě a lad paletu (světlo-friendly na světlém videu). „Silnější přechod" = push/swipe, ne flashy efekt navíc. Kurátorovaná sada: `flash-through-white`, `parallax-unzoom`, `light-leak`, `transitions-cover`. **Přechod NENÍ volitelný — holý střih / opacity fade mezi scénami = „rozanimovaný PowerPoint".** Scény na střídavých trackách (0/1) s překryvem ~0.5 s: stará zrychluje ven (`power4.in`), nová vlétne a gumově dosedne. Detail `production-recipes.md` §11.
- **Safe area — NIKDY nelepit obsah na okraje framu.** Texty, karty a fotky drž min. **120 px od všech okrajů** (1080p; u 9:16 min. 90 px po stranách). Headline nesmí přetékat až k hraně, hero obrázek nesmí sahat od shora dolů. „Vyplnit frame" = velké prvky UVNITŘ safe area s dýchajícím white space okolo, ne natažení ke krajům — bez toho to vypadá stísněně a amatérsky.
- **Kinetická typografie = povinná a HOJNÁ** (catalog text komponenty / GSAP; viz `references/typography.md`). Každý headline pohyblivý + zvýrazněné klíčové slovo — `caption-kinetic-slam` na pointy (používej hodně), `caption-editorial-emphasis` na kontrast velikostí. Statický text na pozadí = „prezentace" = chyba.
- **Brand font POVINNĚ** (CliqSales = Manrope), nikdy cizí font (Inter/Roboto/Helvetica jsou v brandu zakázané). Vendoruj woff2 lokálně + `@font-face` v **každé** sub-kompozici, subset **latin + latin-ext** kvůli české diakritice (ř ž č ě ů — háčkovaná leží v latin-ext, bez něj zmizí). **Google Fonts `@import`/`<link>` v headless renderu NEfunguje** (render běží offline → tichý fallback na systémový sans = cizí font, klient pozná). Po renderu zkontroluj QA frame s českým textem. Detail `production-recipes.md` §10.
- **Audio = HeyGen** (`scripts/heygen_audio.py`), NE FAL. Chybí-li `HEYGEN_API_KEY` → **NEblokuj**: upozorni uživatele „HeyGen klíč není nastavený — video vznikne bez hudby a zvukových efektů; klíč doplníte v nastavení Command Center.“ a pokračuj bez audio stopy. Zvuk musí být **HRAVÝ** (charakterní popy/whooshe/sparkly na beatech nad hudbou), ne technický. Viz `{baseDir}/references/audio.md`.
- **Render LOKÁLNĚ** (`scripts/render.sh`) — žádný cloud (fleet renderuje v openclaw kontejneru). **Finál i každá verze ke schválení = `--quality high`** (draft = nízký bitrate = rozmazané; draft jen na rychlou strukturální iteraci).
- **Proof-before-done:** po KAŽDÉM renderu zkontroluj `qa/proof/*.png` vizuálně (Read). Gates nechytí neviditelný text/flash/mrtvou scénu.
- **Carryover audit:** při změně prvku prohledej i DALŠÍ scénu na jeho kopii (viz continuity-and-qa.md).
- **Žádný FAL/credit spend bez předchozího schválení s odhadem ceny** — buď `--dry-run` prompt, nebo cena uvedená v předchozím STOPu (HeyGen audio i render jsou zdarma; platí se jen FAL obrázky).
- Texty ve videu = **vykání** (klient). Generické role agentů (AI Marketér, ne Marc). Projekt v `documents/videos/<slug>/`.

## Krok 0 — Intake

**Vstupní režim — zjisti hned:**
- **(a) z DNA** (default) — načti `documents/brand/brandDNA.md`, `frame.md`/`DESIGN.md` (pokud je), `documents/brand/products/<slug>/productDNA.md`.
- **(b) ze stránky / URL** (uživatel řekl „udělej video ze stránky" + vložil odkaz) — spusť `npx hyperframes@0.6.97 capture <URL>` → vytěží do `capture/`: screenshoty, assety (fotky, loga, dashboardy), `extracted/visible-text.txt` (copy), `tokens.json` (barvy/fonty). Scény stav **z reálných assetů** (image-hybrid), NE holý text. Brand pořád drž (frame.cliqsales.md); web dodá obsah + fotky. **Storyboard vizuál (Krok 2.5) přeskoč** — máš reálné podklady; textový storyboard (Krok 2) jen na výběr/pořadí scén z capture. Oficiální flow: `references/hyperframes-official/website-to-video/`.

Zjisti dál: typ (launch/feature/sales), délku, **poměr stran** (na šířku 16:9 / na výšku 9:16 / čtverec 1:1 — default 16:9), jazyk (default CZ), **voiceover** (bude video mít český mluvený VO? ano/ne — pokud ano, VO řídí timing scén, takže jeho text se píše už v Kroku 2 a audio se generuje v Kroku 3.5 PŘED stavbou scén). Žádný spend.

## Krok 1 — Spec + styl 🛑

Načti `{baseDir}/references/styles.md`. Z tónu DNA doporuč styl (Elegant SaaS / Playful Pop / Dark Premium / Light Editorial) + vygeneruj **`frame.md`** (motion-design spec: barvy/fonty/pacing/scale z DNA). Navrhni **3 koncepty** (hook → story → proof → CTA, beaty, odhad FAL nákladů). Pokud video má VO (z Kroku 0), u každého konceptu naznač i **tón a hrubou délku VO** (řídí pacing).

**STOP 1 — styl + frame.md + 3 koncepty. Uživatel vybírá.**

## Krok 2 — Storyboard 🛑

Načti `{baseDir}/references/storyboard.md` (a šablonu `templates/storyboard.md`, `templates/scene-spec.md`). Rozpracuj koncept: scéna po scéně (catalog blok / vlastní kompozice, beat timeline s **timestamp sémantikou**, copy ve vykání, audio plán, proof body). Sestav `documents/videos/<slug>/` (catalog blocky přes `npx hyperframes add`). Zdarma.

**Pokud video má VO (z Kroku 0):** napiš **přesný VO script** — mluvený text ve vykání, brand hlas (viz `references/voiceover-rules.md`); nabídni 1–3 varianty podle úhlu příběhu. VO script **řídí délku a copy scén** (scény se časují na jeho segmenty), proto musí být hotový a schválený teď, ne až u audia. Ulož ho do storyboardu.

**STOP 2 — storyboard (čas | scéna | copy | audio | proof) + VO script (pokud video má VO) + FAL náklady vč. storyboard vizuálu (~$0.03–0.19). Schválení = rovnou generuju storyboard vizuál (Krok 2.5), bez dalšího mezi-STOPu.**

## Krok 2.5 — Storyboard VIZUÁL (GPT Image 2) 🛑

**Než stavíš jedinou HTML scénu**, vygeneruj **velký storyboard obrázek** přes GPT Image 2 (FAL `gpt-image-2`) — panelový list, kde je **každý beat jako vlastní panel** (mock frame scény + popisek beatu + klíčový text). Slouží k **vizuálnímu schválení konceptu PŘED** stavbou kompozic: schválit směr na jednom obrázku je levné, přestavovat hotové HTML scény drahé. (Default workflow — ne opt-in.)

- **Obsah panelů:** layout scény, klíčové texty (vykání), barvy/typografie z `frame.md`, styl (premium SaaS motion design — ne ploché slidy). GPT Image 2 text zvládá dobře → dej přesné popisky do promptu.
- **Formát:** každý panel (mock frame scény) má **poměr stran cílového videa** (16:9 landscape / 9:16 portrait / 1:1 čtverec — z Kroku 0), ne natvrdo landscape. Grid podle počtu beatů a poměru (16:9 → 3×2; 9:16 → 2×3 nebo 6×1 s portrait panely; 1:1 → 3×2). Panel zrcadlí reálnou kompozici scény.
- **Inspirace, ne kopie:** pokud uživatel dá referenci (jiné video/web), vytěž z ní pacing/náladu/zvuk — negeneruj reskin.
- **FAL spend** (1 obrázek, ~$0.03–0.19) je **už autorizovaný schválením STOP 2** → vygeneruj rovnou (žádný další STOP), ukaž, `open`. Ulož do `documents/videos/<slug>/_storyboard/`.

**STOP 2.5 — storyboard vizuál. Uživatel schvaluje VIZUÁLNÍ směr. Teprve po OK jdeš na Krok 3/4 (assety + stavba scén).**

## Krok 3 — Obrázky (FAL spend, jen pokud potřeba) 🛑

Ze schváleného storyboardu (Krok 2) + vizuálu sestav **`video-brief.json`** — slot per image-scéna (`id`, `prompt` z popisu scény, rozměr dle poměru stran, `seed`); `imageStyle` = vizuální podpis z `frame.md` (přilepí se ke každému promptu kvůli brand koherenci). Pak concept-image / produktové stilly přes FAL flux: `scripts/gen_images.py --brief <proj>/video-brief.json --dry-run`. **STOP — dry-run prompty + cena.** Viz `references/scene-catalog.md`.

**Volitelný B-roll (oživení foto-scén):** u scén s člověkem (problém / „co kdyby" / výsledek) **aktivně nabídni** rozanimovat statickou fotku na živé video přes **Seedance 2.0 image-to-video** (`bytedance/seedance-2.0/image-to-video`; fast tier pro draft) — fotka = přesný start frame, jemný realistický pohyb (dýchání, mikrovýraz) místo Ken Burns. Štafetu / prompt box / kreativy nech kódované. **Pořadí:** B-roll generuj/časuj až **po Kroku 3.5** (má-li video VO — délka klipu se ladí na finální délku scény z VO segmentů). Vždy `--dry-run` + STOP (~$0.30/s standard, $0.24/s fast; 2× 5 s ≈ $2,4–$3). Postup (Seedance params, retiming na délku scény, `<video class="clip">` integrace) viz `production-recipes.md` §9.

## Krok 3.5 — Voiceover audio (jen pokud video má VO) 🛑

Schválený VO script (z Kroku 2) → vygeneruj **VO audio** přes Gemini TTS (`fal-ai/gemini-3.1-flash-tts`, viz `references/voiceover-rules.md`). Nabídni **2–3 hlasy** na výběr (`open`), uživatel vybere. Změř délku segmentů (`ffprobe`) → **timing master**: scény v Kroku 4 se časují na VO segmenty (VO je primární — scény se přizpůsobí jemu, ne naopak).

**STOP 3.5 — VO varianty na výběr + finální stopáž. VO (FAL Gemini) je levný (~$0.04/1M znaků) → výběr hlasu = autorizace.**

## Krok 4 — Scény + draft render 🛑

Načti `references/scene-catalog.md` (výběr+rebrand catalog bloků na frame.md barvy) + `references/continuity-and-qa.md`. Postav scény **na timing z Kroku 3.5** (má-li video VO — scény sedí na VO segmenty; bez VO si timing určují samy), gates, draft render + proof:

```bash
bash {baseDir}/scripts/render.sh --project documents/videos/<slug> --draft
```

**STOP 4 — draft + proof framy. Iteruj TADY (levné). Schválené scény ZAMKNI** (surgical-change kontrakt).

## Krok 5 — Audio (Sync) 🛑

Načti `references/audio.md`. HeyGen hudba (vibe z frame.md) + **hravé SFX na beaty** (sound recipes) + ducking. **VO už je hotový z Kroku 3.5** (má-li video VO) — tady ho jen **zamícháš pod hudbu** (VO hlavní vol 1.0, hudba potichu ~0.10–0.12 pod ním, SFX light). HeyGen `scripts/heygen_audio.py`.

**STOP 5 — audio plán (event → zvuk → čas → volume). HeyGen audio je zdarma → po schválení rovnou.**

## Krok 6 — Assembly + mix + final 🛑

Načti `references/assembly.md`. Více scén → timeline manifest + FFmpeg assembly (retiming ladder). Mix (ducking), render `--final`, proof + per-sekundový audio profil.

**STOP 6 — final s audiem + proof + mix tabulka. Finální schválení.**

## Krok 7 — Delivery

Vypiš absolutní cestu k MP4 + `open`. Handoff: styl, délka, co lze re-renderovat. **Surgical edity** = `templates/change-request.md` (jen co se mění, zbytek zamčený).

## 📦 Oficiální HyperFrames skilly — VENDOROVANÉ (engine zdroj pravdy)

V `{baseDir}/references/hyperframes-official/` je **kompletních 20 oficiálních skillů od HeyGen** (sync z github.com/heygen-com/hyperframes/skills). Pro engine detaily jsou **zdroj pravdy** — mají přednost před našimi destiláty, když se liší. Routování podle úlohy:

| Úloha | Načti (`{baseDir}/references/hyperframes-official/…`) |
|---|---|
| Stavba kompozice, data-atributy, timelines, media | `hyperframes/SKILL.md` + `hyperframes-core/SKILL.md` |
| CLI: init/catalog/add/lint/validate/render/preview | `hyperframes-cli/SKILL.md` |
| Titulky do videa | `embedded-captions/SKILL.md` |
| Animace, keyframy, pohyb | `hyperframes-animation/SKILL.md` + `hyperframes-keyframes/SKILL.md` |
| Kreativní/vizuální komponenty | `hyperframes-creative/SKILL.md` |
| Media preprocessing (tts, transcribe, remove-bg) | `hyperframes-media/SKILL.md` + `media-use/SKILL.md` |
| Instalace bloků z registru | `hyperframes-registry/SKILL.md` |
| Hotové video žánry (inspirace/skeleton) | `general-video`, `product-launch-video`, `motion-graphics`, `slideshow`, `faceless-explainer`, `website-to-video`, `music-to-video`, `talking-head-recut`, `pr-to-video`, `remotion-to-hyperframes` |

Naše vrstva (references níže) řeší to, co oficiální skilly neznají: brand/DNA intake, styly z DNA, český VO, HeyGen audio doktrína, storyboard schvalování, QA/continuity, credit STOPy. Při bumpu enginu re-vendorovat celou složku (demo MP4 vynechat — viz `_VYNECHANO.md`).

## Reference (načítej průběžně)

- `references/pipeline.md` — celá produkční doktrína (5 fází, layered build order, „feels off" ladder). **Vždy.**
- `references/production-recipes.md` — learningy z reálné výroby (image-hybrid vs UI-motion, klient-POV příběh, jemná animace, FAL imagery, **B-roll/image-to-video §9**, **brand font + diakritika §10**, VO Gemini, audio mix). **Vždy.**
- `references/styles.md` — 4 styly, generování frame.md z DNA. Krok 1.
- `references/storyboard.md` — timestamp sémantika, scene-spec, scaffolding. Krok 2.
- `references/scene-catalog.md` — výběr+rebrand catalog bloků, html-in-canvas hero. Krok 3–4.
- `references/transitions.md` — **oficiální HyperFrames přechody (catalog knihovna) → recepty** (push/crossfade default, shader two-pass, kurátorovaná sada). Krok 4.
- `references/typography.md` — **kinetická typografie (catalog text komponenty) → recepty** (kinetic-slam, editorial-emphasis, anti-„prezentace"). Krok 4.
- `references/audio.md` — HeyGen hudba + HRAVÉ SFX (sound recipes) + ducking. Krok 5.
- `references/voiceover-rules.md` — **volitelný český VO** přes Gemini TTS (voice presety, style_instructions, pitch-down, glitch-retry, queue API, VO řídí timing). Krok 5–6.
- `references/continuity-and-qa.md` — carryover audit, proof-before-done, surgical kontrakt. Krok 4–7.
- `references/assembly.md` — timeline manifest, FFmpeg retiming + concat. Krok 6.
