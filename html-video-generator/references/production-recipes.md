# Produkční recepty a learningy (z reálné výroby)

Destilát z výroby dvou videí (akcelerator-1min UI-motion + AI Marketér image-based). Tyhle vzory šetří iterace — čti před stavbou.

## 1. Dva vizuální módy — vyber podle konceptu

- **UI-motion-graphics** (čistý CSS/SVG/GSAP): glass karty, prompt boxy, dashboardy, kinetická typografie. Bez FAL obrázků. Rychlé iterace, ostré, deterministické. (vzor: hook + demo-usecase)
- **Image-based hybrid** (FAL imagery + kódované overlays): scéna = FAL fotka/render jako obsah + kódované UI/bubliny/grafy/kurzor navrch. Bohatší, „obrázkovější". (vzor: AI Marketér — majitel + bublina, roboti + relay)
- Klient často chce **víc obrázků/barevnosti** → hybrid. Ale UI prvky (prompt box, štafeta, grafy, kurzor) drž **kódované** = přesně řiditelné.

## 2. Příběh = z pozice KLIENTA, ne výčet feature

- Struktura, co konvertuje: **problém → řešení → JEHO výsledek**. Ne „naše AI umí A, B, C".
- Konkrétní bolest (ne generická): „potřebuje rychle prázdninovou kampaň", ne „nemá marketéra".
- ⚠️ **„Spokojený zákazník" je NAŠE optika** — ve finále ukaž **jeho virální výsledek** z jeho pozice (kampaň letí, vyprodáno, +312 %), ne label „spokojený zákazník".
- **Min. ~6 scén** na 45s explainer (problém → co kdyby → zadání → práce/štafeta → výstup → výsledek).
- **CTA = aktivace produktu** (když video představuje funkce), ne hard-sell programu.

## 3. Paleta — NEPŘEDPOKLÁDEJ, potvrď

- Klient může chtít **světlý** canvas (Rajmoni styl, tmavé karty na světlém) NEBO **tmavý** brand dark-mode. Zeptej se / nabídni varianty (storyboard).
- „Zelenou nahraď modrou" apod. — drž **firemní barvy dominantní** (cyan/blue gradient), zelená/mint často vadí.
- Žádné ploché slidy: imagery, **myšlenkové bubliny**, reálné kreativy, grafy — ne text na barvě.

## 4. Animace — jemná, ne overshoot (opakovaná lekce)

- Default **`back.out(1.4–1.6)`**, krátké posuny, blur-in. **Žádný agresivní overshoot/rotace** ani přebujelé bubliny — „silnější + větší" se snadno přežene a klient chce zpátky.
- **Tuhé objekty:** fotky/UI/karty se NEROZTAHUJÍ (žádný non-uniformní scale). Squash&stretch jen uniformně (hloubka). Pohyb po oblouku, dojezd v pozici/rotaci. Viz [[feedback-no-flat-slides]].
- **Žádné mrtvé čekání:** scéna nesmí zmrznout a čekat. Tempo těsné, scéna **aktivně odejde** (push/fade) do přechodu. Časuj na VO segmenty.

## 5. FAL imagery — co čím

- **Lidé / scény** (majitel u stolu): `fal-ai/flux/dev` (sync, rychlé, fotoreal). Prompt: nech vlevo/vpravo prázdno na text.
- **Konzistentní postava** (stejný člověk jiný výraz: stres→radost): `openai/gpt-image-2/edit` s předchozím obrázkem jako referencí.
- **Kreativy s textem** (landing/banner „LETNÍ KOLEKCE -30%"): `gpt-image-2/edit` (umí text dobře, viz documents/CLAUDE.md). Brand-board jako style ref, ale prompt přebíjí (lze vynutit světlé/jiné barvy).
- **Průhledné pozadí** (roboti, cut-outy): flux nedělá nativně → vygeneruj na ploché šedé + **remove-bg** (`fal-ai/imageutils/rembg` / `birefnet`). gpt-image-2 umí transparent nativně, ale na FALu jen `/edit` (potřebuje ref).
- **Dlouhé generace** (gpt-image-2 2400×1600, 6 panelů): **queue API** (`https://queue.fal.run/...` + status polling), ne sync — sync `fal.run` timeoutuje na read. Klíč inline z `.claude/settings.local.json`, NIKDY nevypisovat.
- Storyboard vizuál (Krok 2.5): edit jen jednoho panelu = nakrm celý storyboard jako ref + „change ONLY panel X" → ostatní zůstanou.
- **Foto-scénu lze oživit na B-roll video** (image-to-video) — nabídni klientovi, viz §9.

## 6. Voiceover — FAL Gemini TTS

- Endpoint **`fal-ai/gemini-3.1-flash-tts`**, `language_code: "Czech (Czech Republic)"` (NE `"cs"`), `voice`, `style_instructions`, `prompt` = text. Plný VO playbook (voice presety, style_instructions, phonetic respell, pitch-down, glitch-retry, queue API, mix): **`references/voiceover-rules.md`**.
- **Mužské hlasy:** Charon (hluboký, autoritativní), Algieba (teplý, konverzační), **Enceladus** (charakterní, hluboký+hravý — osvědčil se). Female: Aoede, Kore.
- **Emoce/tempo přes `style_instructions`** (ne přes hlas): „deep, playful, NOT announcer, continuous flowing, minimal pauses". Bez explicitního „minimal pauses" Gemini cpe pauzu po každé tečce (delší stopáž).
- **Hlubší trik:** ffmpeg pitch-down `asetrate=24000*0.93,aresample=24000,atempo=1/0.93` (drží tempo). Gemini default 24 kHz mono.
- **Glitch:** občas vrátí ~1–2 s (nenamluví) → retry loop (zkontroluj duration >25 s).
- Vygeneruj **2–3 varianty hlasů** na výběr (open je klientovi), pak finál.

## 7. Audio assembly — VO + hudba + SFX (ffmpeg, NE HyperFrames mix)

- HyperFrames renderuje **silent**; audio přimíchej **ffmpeg post-mixem** (plná kontrola hladin/timingu).
- **VO = hlavní stopa** (vol 1.0, start ~0.5 s). **Hudba potichu pod VO** (vol ~0.10–0.12, fade in/out), žádný sidechain netřeba. SFX **light** (0.28–0.5).
- SFX z HeyGen (psaní/klik/pop/whoosh) na eventy: psaní během typewriteru, klik na cursor-click, pop na naskočení prvku, whoosh na přechod. Pattern (per-event adelay+volume → amix normalize=0 → alimiter) viz `audio.md`.
- Časuj scény na VO segmenty; po renderu **poslechni sync** a dolad stopáže.

## 8. Hero vzory

- **Štafeta / handoff:** „tým spolupracuje" = svítící balíček práce putuje mezi roly (linka + nody + pausy na VO jmény rolí + glow co sleduje). Silnější než statický grid.
- **Bílý kurzor co kliká** (macOS arrow `fill #fff stroke #0A1830` + ring pulz) na UI akce (send, tlačítko) → cue pro klik SFX.
- **Myšlenková bublina** (CSS rounded + ocásek k hlavě) = relatable problém na fotce majitele.

## 9. B-roll — oživení foto-scén (Seedance 2.0 image-to-video, volitelné)

Statická fotka v image-hybrid módu působí „placatě". **Aktivně nabídni klientovi** rozanimovat ji do živého B-roll záběru (jemný realistický pohyb člověka — dýchání, posun, mikrovýraz) místo pouhého Ken Burns. Default: nabídni to u scén s člověkem po schválení fotek. Seedance 2.0 přesně tohle umí dobře (subtle character animation: breathing, blinking, micro-expressions).

- **Engine:** **Seedance 2.0 image-to-video** — `bytedance/seedance-2.0/image-to-video` (standard $0,30/s) nebo `bytedance/seedance-2.0/fast/image-to-video` (draft, $0,24/s). Fotka = **přesný start frame** → drží kompozici (overlay pak sedí). NE `reference-to-video` (volnější, pro multi-ref identity — sem se nehodí).
- **Upload:** `image_url` musí být **uploaded HTTPS URL** (`fal_client.upload_file_async`), Seedance **odmítá data URLs**. Async submit povinný (`submit_async` + `handler.get()`; generace 60–180 s, sync 60 s timeoutuje).
- **Params:** `aspect_ratio` = poměr videa (9:16 / 1:1 / 16:9, z Kroku 0), `resolution` `"720p"`, `duration` `"4"`–`"15"`, **`generate_audio: False`** (B-roll je silent — audio řešíš ffmpeg post-mixem). Prompt **jemný** (Seedance struktura): „Subject: [člověk z fotky]. Action: subtle natural motion, breathing, slight shift, [emoce]. Camera: static / very slow push. Environment: [scéna]." — žádný divoký pohyb (rozbije kompozici, overlay přestane sedět).
- **Délka / timing:** generuj/časuj **až po Kroku 3.5** (znáš finální délku scény z VO segmentů). Seedance vrátí zvolenou délku (často kratší než scéna) → **zpomal ffmpegem** na délku scény: `setpts=PTS/<faktor>` (faktor = klip_dur ÷ scéna_dur, např. 5.0/9.46 ≈ 0.53). Plynulé, bez seků.
- **Integrace do HyperFrames:** `<video>` MUSÍ mít `class="clip" data-start="0" data-duration="<scéna>" data-track-index="0" muted playsinline` — jinak lint `media_missing_data_start`. Renderuje se **silent** (audio přes ffmpeg mix). Wrap do `data-layout-ignore`, Ken Burns/parallax dělej na wrapperu, ne na `<video>`.
- **Kde ANO / NE:** ANO scény s člověkem (problém / „co kdyby" / výsledek). NE štafeta, prompt box, kreativy, grafy — ty drž kódované/statické (B-roll tam nedává smysl a rozbije přesnost).
- **Cena/flow:** Seedance je dražší než statická fotka — 2× 5 s ≈ **$2,4–$3** (fast/standard). Vždy **`--dry-run` napřed** (build prompt + cost), STOP, až **po schválení fotek**. Pusť paralelně (FAL concurrency limit 3–8).

## 10. Font — brand font + česká diakritika (POVINNÉ)

- **Použij brand font** (CliqSales = **Manrope**), NIKDY cizí font (Inter / Roboto / Helvetica jsou v brandu **zakázané** — viz documents/CLAUDE.md). Headless Chrome jinak spadne na systémový fallback = ne-brandové, „placaté".
- **Vendoruj font lokálně** (`assets/vendor/fonts/*.woff2`) + `@font-face` v **KAŽDÉ** sub-kompozici (sub-comps nesdílí CSS, ani root @font-face se nedědí). Žádný Google Fonts CDN — render/fleet běží offline.
- **Česká diakritika:** stáhni **latin + latin-ext** subset a dej **oba** `@font-face` s `unicode-range`. Háčky/kroužky ř ž č ě ů ň š ť ď leží v latin-ext (U+0100–024F), zatímco á é í ó ú ý v latin (U+00xx) — bez latin-ext zmizí jen háčkovaná písmena (zákeřné, čárkovaná projdou). Variable woff2 (`font-weight:200 900`) pokryje všechny váhy jedním souborem.
- Zdroj woff2: `@fontsource-variable/<font>` přes jsdelivr (`files/<font>-latin-wght-normal.woff2` + `…-latin-ext-…`).
- `font-display:block` + lokální woff2 = font naběhne dřív, než HyperFrames sejme frame (deterministické). Po renderu **vždy zkontroluj QA frame** s českým textem (háčky sedí, font je Manrope, ne fallback).

## 11. Render, přechody, easing, čísla — learningy z web-to-video výroby

- **Finál = `--quality high`.** Draft render má nízký bitrate → rozmazané, text/pohyb „mázne". Draft jen pro rychlou strukturální iteraci; každou verzi ke schválení i finál renderuj `high`.
- **Font self-hosted woff2, NIKDY Google Fonts `@import`/`<link>`.** Headless render běží offline → CDN font se nenačte → tichý fallback na systémový sans (klient pozná cizí font). Vendoruj woff2 (latin + latin-ext) + `@font-face` v každé sub-kompozici. Viz §10.
- **Přechody mezi scénami jsou POVINNÉ, ne opacity fade.** Scény na střídavých trackách (0/1) s překryvem ~0.5–0.6 s; stará zrychluje ven (`power4.in`), nová vlétne a gumově dosedne. Rotuj 3–4: push-left / push-up / cover / flash-through-white (bílý overlay na vlastním tracku, peak 0.16 s) / zoom-through. Ne 6 efektů. Viz `transitions.md`.
- **Easing = elastika („guma"): `elastic.out(1, 0.4–0.5)`** na dopady (headliny `scaleY 1.3–1.4` → smrsknou; karty přestřelí a zhoupnou se). Ostrý kontrast rychlostí: rychlý nálet `expo.out` → dlouhý dojezd; kamera `expo.out`→`power4.inOut`; exit `power4.in`. Lineární/vlažný easing = „rozanimovaný PowerPoint".
- **Count-up = dynamic scale.** Číslo roste od ~40 % cílové velikosti do plné SOUČASNĚ s nabíháním hodnoty (`fromTo fontSize` + proxy `v`, stejný čas), ease **`power1.out`** (NE `expo.out` — ta „skočí na cíl" a dobrzdí posledních pár desetin). ~1.8–2.1 s + gumový puls na konci. Bez dynamic scale klient count-up „nevidí".
- **Karta s animovanou fotkou uvnitř: `clip-path: inset(0 round <r>)` na PŘÍMÉM rodiči obrázku + `transform: translateZ(0)`.** `overflow:hidden` NEstačí — Chromium povýší animovaný obrázek na GPU vrstvu a ořez vzdálenějšího předka ignoruje → přeteče kulaté rohy, probliká spodní hrana (nedeterministicky, ne na všech kartách stejně = matoucí příznak).
- **Ken Burns na fotce spouštěj AŽ po dosednutí prvku** (ne souběžně s elastickým entrance) — dvě transformace na stejném elementu se perou o hrany a blikají.
- **GSAP tween s `x:0`/`translateX` PŘEPÍŠE CSS `translateX(-50%)`** → prvek uskočí z osy (typicky centrovaná garance/patička). Centruj rodičem (`left:0;right:0` + flex `justify-content:center`), ne transformem, který si GSAP vlastní.
