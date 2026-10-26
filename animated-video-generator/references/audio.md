# Zvuk — voiceover + HeyGen hudba + hravé SFX

Hotová animace je **muted** (Seedance `generate_audio:False`). Zvuk skládáme sami: voiceover (řídí timing) + HeyGen hudba (bed) + **hravé SFX na akce ve scéně**.

## Voiceover (Gemini TTS)

- **Engine:** `fal-ai/gemini-3.1-flash-tts` (FAL, přes `queue.fal.run`).
- **Args:** `{"prompt": text, "voice": "<hlas>", "style_instructions": "...", "language_code": "Czech (Czech Republic)"}`.
  - ⚠️ `language_code` přesně `"Czech (Czech Republic)"`, jinak přízvuk ujede.
- **Hlasy (mužské):** Enceladus (hluboký, hravý — osvědčený), Charon (hluboký), Algieba (vřelý), Puck (hravý). Vyber dle tónu DNA.
- **Generuj PO BEATECH**, ne jeden blok. Beat = věta/fráze + mikro-nálada ve `style_instructions`. Pak každý beat **posaď na přesný čas** ve videu → přirozené pauzy.
- **Sync podle screenshotů:** extrahuj framy z klipů (`ffmpeg`), Read, zjisti co se kdy děje → namapuj beaty na momenty (klíčové slovo na klíčový vizuál).
- **Retry + délka:** Gemini občas glitch (krátký output) → retry s kontrolou délky. Velmi krátké 1-slovní beaty občas 422 → spoj s další větou.
- **Po generaci:** ořízni ticho (`silenceremove`) + sjednoť hlasitost (`loudnorm I=-15`).
- **`atempo` na VO NEPOUŽÍVEJ** — i malý (1.05–1.12) zavádí slyšitelné artefakty (ověřený feedback: „hlas v druhé části horší"). Když beat nesedí délkou: **posuň jeho začátek (offset)** dřív/později, nebo přegeneruj s jiným tempem ve `style_instructions`. Délku videa kvůli mluvenému slovu **neprotahuj** — vejdi hlas dovnitř **posunem**, ne time-stretchingem.
- **Tón hlasu (ověřený feedback):** teplý, příjemný, vzdušný, lehce hravý — jako milá kamarádka. **NE afektovaný / přehrávaný / „announcer".** Závěrečnou frázi klidně **protáhni** (pomalu, vřele), ať vyplní konec videa — ale tak, aby se pořád vešla. Hlas radši **hlasitější** (ať není slaboučký pod hudbou). Ženské hlasy Gemini: Aoede, Kore, Leda, Zephyr (vyber dle DNA).

## HeyGen hudba + SFX (zdarma)

> **HeyGen je VOLITELNÝ** — bez `HEYGEN_API_KEY` `heygen_audio.py` jen upozorní a skončí (exit 0), video se vyrobí **bez hudby a SFX** (animace, text overlay i VO/dialog fungují dál). `HEYGEN_API_KEY` proto NENÍ v `requires.env`.

- **API:** `https://api.heygen.com/v3/audio/sounds?query=&type=music|sound_effects`, hlavička `x-api-key`. Vrací `audio_url`.
- **Hudba:** vibe z brand DNA, `type=music`, vol **~0.14** (bed pod VO).
### Postup SFX (POVINNÝ): analyzuj silné momenty → HeyGen → (fallback) FAL

1. **Analyzuj video na silné momenty.** Extrahuj framy (`ffmpeg fps=…`), Read je a najdi beaty, kde zvuk umocní dění — akce, přechody, objevení prvku, emoce: např. zívnutí, otočení listu kalendáře, padající kapsle, reveal produktu, zlatá záře / proměna, dopad chipu, povzdech… Ke každému si zapiš **přesný čas (s)**.
2. **Ke každému momentu najdi SFX na HeyGen** (`heygen_audio.py search`, query dle typu — viz tabulka níže). HeyGen 250k+ knihovna pokryje většinu (popy, whoosh, chime, sparkle, kasa…).
3. **Co HeyGen nemá kvalitně → vygeneruj přes FAL:**
   - **Lidské vokály** (zívnutí, povzdech, smích, vzdech) → **`fal-ai/elevenlabs/sound-effects/v2`** (bez `/v2` → 400).
   - **Specifická foley / ambience** → `fal-ai/mmaudio-v2/text-to-audio` (`{"prompt":"…","duration":N}`).
4. **Nasaď každý SFX `adelay` přesně na čas momentu** + ověř timing přes `silencedetect` na SFX-only stopě. Jeden charakter zvuku použij **jen 1×** (opakovaný shimmer = klient to vytkne).

- **SFX = HRAVÉ a charakterní**, ne technické. Sync na **typ momentu** ve scéně (ne na konkrétní příběh). Najdi vhodný zvuk přes search query:

| Kategorie momentu | HeyGen query (příklady) |
|---|---|
| Nápad / aha / reveal | „Clear bell chime", „idea ding" + jemný „Magic" shimmer |
| Prvek/objekt naskočí | „pop", „Standard Pop", „Soft UI Pop" |
| Akce s předmětem | dle akce: „Slam"+„Page Turn" (něco se položí), „Fast typing" (psaní), … |
| Přechod / něco letí | „Whoosh", „Swoosh" |
| Pozitivní výsledek / win | „success", „Achievement"; sales/„prodáno" → **„Cash Register Kaching" + „Coins"** (kasa) |
| Oslava / finále | „celebrate", „General Crowd Cheer", „sparkle" (konfety) |

- **Akční SFX nasaď přesně na akci** (např. zvuk klávesnice až když naskočí „psaní", ne dřív — jinak zní zvuk před obrazem).
- **Lidské vokály (zívnutí, povzdech, smích…) = ElevenLabs**, NE HeyGen/Gemini/cassetteai/mmaudio (zní slabě/uměle). Endpoint **`fal-ai/elevenlabs/sound-effects/v2`** (⚠️ **bez `/v2` vrací 400** — pojmenovaná chyba!). `fal_client.subscribe("fal-ai/elevenlabs/sound-effects/v2", arguments={"text":"a tired woman yawning, single long human yawn","duration_seconds":2.5})`. Nasaď přesně na vizuál (zívnutí ~100–150 ms před/na otevření pusy).
- **Volume:** VO ~1.15, hudba ~0.14, SFX 0.4–0.6 (silné akcenty 0.6–0.8). `alimiter limit=0.95`.
- **Fade-in na začátku (POVINNÉ):** video nesmí nastoupit zhurta. Dej **video fade-in z černé ~0.5 s** (`-vf "fade=t=in:st=0:d=0.5"`, video re-encode) + **hudbu fade-in ~1 s** na jejím busu (před mixem, ať nezahltí úvodní VO).
- **Fade-out na konci:** hudbu fadeuj **dřív** (od ~3–4 s před koncem, dlouhý gentle) — krátký fade zní uťatě. ⚠️ `loudnorm` je dynamický a fade-out po něm tahá zpět nahoru → fade-out dělej **druhým ffmpeg průchodem** po loudnormu (`afade=t=out:st=<konec−1>:d=1`).
- ⚠️ **`sidechaincompress` zkracuje výstup na délku sidechainu (VO)!** Když VO končí dřív než video, ducking utne **celou audio stopu** na konci VO → poslední ~1 s videa je bez zvuku (= „useknutý konec", pojmenovaná chyba). Fix: **apad sidechain (VO kopii) delší než video** PŘED sidechaincompress: `[vosum]asplit=2[voout][vosc0];[vosc0]apad=whole_dur=<video+1>[vosc];[mus][vosc]sidechaincompress=…[musd]`. Pak hudba hraje a duckuje až do konce.

Hotový kód: `scripts/gen_voiceover.py` (beaty + retry + loudnorm), `scripts/heygen_audio.py` (search + download).
