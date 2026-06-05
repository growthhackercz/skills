# Audio Rules — Voiceover + Music + SFX

Default audio strategie skillu má **3 vrstvy**, všechny generované jiným systémem a smíchané ve finálním ffmpeg post-procesu.

## Layer architektura

```
┌──────────────────────────────────────────────┐
│ Layer 3: CZ Voiceover (voiceover.mp3)        │  ← Gemini 3.1 Flash TTS, FAL
│           sidechain ducking přes ffmpeg      │
├──────────────────────────────────────────────┤
│ Layer 2: Native instrumentální music         │  ← Seedance 2.0, generate_audio: True
│           gradace soft → swell → resolution   │
├──────────────────────────────────────────────┤
│ Layer 1: Native ambient SFX                  │  ← Seedance 2.0, generate_audio: True
│           per scene (water, wind, footsteps) │
└──────────────────────────────────────────────┘
```

Layer 1+2 generuje Seedance v jednom volání, Layer 3 se přidá přes ffmpeg po stažení Seedance MP4.

## Layer 1+2: Seedance native audio

V Kroku 3b vždy posíláme `generate_audio: True`. Seedance vyrobí kompletní soundtrack:

- **Ambient SFX odpovídající scéně** (water sound, linen rustle, distant city hum, footsteps, atd.)
- **Instrumentální podkres** (low warm piano, soft strings, ambient pad — záleží na briefu)

Co řídí Seedance soundtrack:

```json
"shared_choices": {
  "audio_tone": ["soft water sound", "linen rustle", "distant city hum", "low warm piano with reverb"],
  "mood_keywords": ["serene", "premium", "intentional", "wellness-ritual"]
}
```

Skript `generate-video-singleshot.py` rozdělí `audio_tone` na **SFX cues** (vše ne-music) a **music cues** (obsahuje keywords: piano, strings, guitar, synth, music, melody, score, soundtrack, reverb) a vsadí je do promptu separately.

### Pravidla pro audio_tone

✓ **Konkrétní popis SFX:** „soft water sound", „linen rustle", „distant city hum"
✓ **Konkrétní popis music:** „low warm piano with reverb", „cinematic strings", „acoustic guitar"
✗ **Vyhni se:** „voiceover", „dialog", „singing" — Seedance to vezme doslovně a pokusí se generovat cizí hlas, což zní špatně

### Music gradation rule

Prompt obsahuje klauzuli:

> „The music score MUST gradate across the full {total}-second arc — start gently in the opening seconds, gradually swell through the middle as the action peaks, and ARRIVE at a natural musical resolution in the final 1-2 seconds (a held note, a final chord, or a soft ritardando). NEVER cut the music abruptly, NEVER fade out mid-phrase, NEVER end on a note that feels unfinished."

Bez tohohle Seedance často skončí hudbu brutálním cutem na 14.99s.

### Mood keywords

| Brand mood | Doporučená audio_tone slova |
|------------|---------------------------|
| Aspirační / luxury | cinematic strings, subtle piano, warm orchestral, gentle reverb |
| Wellness / quiet luxury | low warm piano, soft string pad, ambient stillness, delicate harp |
| Autentický / UGC | acoustic guitar, lo-fi, indie, room tone |
| Tech / SaaS | minimal electronic, ambient pad, subtle synth, clean reverb |
| Action / energy | driving electronic, percussion, rock, punchy bass |
| Wistful / nostalgic | solo cello, ambient guitar, vintage strings, slow piano |
| Minimalist | sparse piano, single instrument, room tone, breathing reverb |

## Layer 3: CZ Voiceover

Vygenerovaný v Kroku 2c přes Gemini 3.1 Flash TTS. Detail v `voiceover-rules.md`.

### Prompt klauzule pro Seedance (když VO je v hře)

Pokud `voiceover.mp3` existuje a je předán jako `--voiceover` flag, generate-video-singleshot.py přidá do promptu:

> „A pre-rendered voiceover is mixed on top in post — leave mid-range headroom for the spoken voice; do not peak loud where dialog lands. NO dialog/lyrics/voiceover in the generated audio."

Bez této instrukce by Seedance mohl generovat hudbu která maskuje VO frekvenční pásmo a finální mix by byl srozumitelně tichý ve VO.

### Sidechain ducking architektura

VO je vždy mixován NAD Seedance music+SFX, ne místo nich. Sidechain compressor automaticky ztiší music když VO mluví, plnou hlasitost vrátí v pauzách.

**Defaults a jejich ladění → viz `post-mix-recipes.md` (canonical).** Mix params jsou nastavitelné přes CLI flagy (`--vo-volume`, `--bg-volume`, `--ducking-ratio`, `--ducking-threshold`, atd.) bez editace skriptu.

## Fade-out na konci

Audio + video fade na posledních ~1.5 s (audio) / ~1.2 s (video). Zvuk doznívá ještě po tom co obraz zčerná. Defaults v `mix_voiceover_with_video()`:

```python
fade_out_s = 1.5  # audio
vfade_d = max(0.5, fade_out_s - 0.3)  # video, vždy o 300ms kratší
```

Override přes `--fade-out 2.5` flag v plnem nebo MIX_ONLY módu.

## Strategie podle scénáře

### Scénář A: Premium ad s VO (default)

```
brief.voiceover = vyplněno
brief.shared_choices.audio_tone = SFX + music cues
generate_audio: True (Seedance native)
ffmpeg post-mix: VO + ducked music + fade-out
```

### Scénář B: Music-only ad (žádný VO)

```
brief.voiceover = neuvedeno (nebo voiceover.mp3 neexistuje)
brief.shared_choices.audio_tone = SFX + music cues
generate_audio: True
ffmpeg post-mix: nepoběží (žádný VO ke zmiksování), výstup = Seedance MP4 1:1
```

### Scénář C: Brand music override (vlastní music track)

Není v aktuálním pipelinu podporováno automaticky. Workflow:

1. Plný běh produkuje `final-singleshot-seedance.mp4` (Seedance s native music)
2. Manuálně extract VO + custom music track:
   ```bash
   ffmpeg -i final-singleshot-seedance.mp4 -an no-audio.mp4
   ffmpeg -i no-audio.mp4 -i custom-music.mp3 -i voiceover.mp3 \
     -filter_complex "[2:a]volume=2.5,asplit=2[vo_main][vo_sc];[1:a]volume=0.4[bg];[bg][vo_sc]sidechaincompress=...;..." \
     -map 0:v -map "[aout]" custom-final.mp4
   ```

V budoucnosti přidat do `generate-video-singleshot.py` flag `--music-track <path>` který override Seedance native music.

### Scénář D: Silent video

```
generate_audio: False (nastavit v brief.audio.preset = "silent")
```

Pak video nemá žádný zvukový stream. ffmpeg post-mix detekuje silent vstup přes `probe_has_audio()` a:
- Pokud VO existuje → použije VO jako sole audio track (s fade-out)
- Pokud VO neexistuje → finální MP4 zůstane silent

## Subtitles (legacy, optional)

Burned-in CZ titulky byly původně Layer 3 (před Gemini TTS). Aktuálně **nepoužíváme** — VO komunikuje text mluveně místo vizuálně. Ale pokud kampaň cílí na **mute autoplay platformy** (Meta feed, LinkedIn) a chceš titulky:

- User dodá `subtitles.srt` v root složky kampaně
- ffmpeg subtitle filter (burned-in):
  ```bash
  ffmpeg -i final.mp4 \
    -vf "subtitles=subtitles.srt:force_style='FontName=Inter,FontSize=24,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BorderStyle=3,Outline=2,Alignment=2,MarginV=80'" \
    -c:a copy final-with-subs.mp4
  ```

Toto je **manuální post-process** mimo automatický skill flow.

## Audio preset volby v briefu (legacy field)

```json
"audio": {
  "preset": "ambient-music",
  "music_track": null,
  "music_volume": -18,
  "subtitles": "none",
  "end_card": false
}
```

| Preset | Seedance generate_audio | Custom music | Default v aktuálním pipelinu |
|--------|------------------------|--------------|-----------------------------|
| `silent` | False | nikdy | jen pro speciální use cases |
| `ambient-only` | True | nikdy | obsoletní (Seedance music je default) |
| `ambient-music` | True | nikdy (Seedance native) | **DEFAULT** |
| `music-driven` | False | manual ffmpeg post | obsoletní (Seedance music je default) |

V praxi `audio.preset` ovládá pouze flag `generate_audio` v Seedance volání:
- `"silent"` → `generate_audio: False`
- vše ostatní → `generate_audio: True`

## Validační pravidla

- VO existuje a je validní MP3? Pokud ne → warning, fallback na pure Seedance audio
- ffmpeg/ffprobe v PATH? Pokud ne → fallback na Seedance-only audio (žádný mix), warning
- VO duration > video duration? `apad whole_dur` ho ořízne, ale v praxi by neměl. Doporučení: VO 10-13 s pro 15 s video
- VO duration < 5 s? Seedance music může být moc dominantní — zvyš `volume=2.5` na `volume=3.5` pro krátké VO

## Související soubory

- `voiceover-rules.md` — Gemini TTS detaily (voice, style_instructions, phonetic respell)
- `post-mix-recipes.md` — ffmpeg filter graphs, edge cases, MIX_ONLY mode
- `seedance-models.md` — `generate_audio` parameter, audio output format
