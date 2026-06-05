# Post-mix Recipes — ffmpeg

ffmpeg pipeline pro post-process Seedance videa: VO mix přes nativně generovanou hudbu/SFX, sidechain ducking, audio + video fade-out, MIX_ONLY iterativní mod.

Tento dokument NAHRAZUJE starý `compose-recipes.md` (per-cut concat pipeline byl opuštěn).

## Architektura

```
                                  ┌─────────────────────────────────┐
Seedance MP4 ──[probe duration]──▶│                                 │
(music + SFX)                     │  ffmpeg filter_complex          │
                                  │                                 │
voiceover.mp3 ───────────────────▶│  [1:a] VO   ─┬─[vo_sc]──→       │
(Gemini TTS)                      │              │                  │
                                  │              └─[vo_main]──→     │
                                  │                                 │
                                  │  [0:a] BG  ──→ sidechaincompress │
                                  │       (ducked by [vo_sc])        │
                                  │                                 │
                                  │  ducked_BG + vo_main → amix      │
                                  │       │                         │
                                  │       └─→ alimiter + afade=out  │
                                  │              │                  │
                                  │              ▼                  │
                                  │  [aout] (mixed audio)            │
                                  │                                 │
                                  │  [0:v] video ──→ fade=out        │
                                  └─────────────────────────────────┘
                                                 │
                                                 ▼
                                          final.mp4
```

## Klíčové filtery

### 1. asplit — VO duplikace pro sidechain + main path

```
[1:a]volume=2.5,apad=whole_dur=15,asplit=2[vo_main][vo_sc]
```

⚠️ **Kritické:** ffmpeg vyžaduje `asplit` pokud chceš stream použít vícekrát. Bez asplit jeden output label nelze konzumovat dvěma filtery a druhý filter dostane prázdný stream → VO mizí z výstupu.

- `volume=2.5` — boost VO aby seděl nad music bedem
- `apad=whole_dur=15` — extend audio na přesnou délku videa (tichem, ne loop). **Bez `whole_dur` apad extenduje nekonečně** → `-shortest` clipne nepředvídatelně.
- `asplit=2[vo_main][vo_sc]` — dvě kopie

### 2. sidechaincompress — ducking music pod VO

```
[bg][vo_sc]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300:makeup=1[bgduck]
```

- `[bg]` = ducked input (music+SFX)
- `[vo_sc]` = sidechain control (VO)
- `threshold=0.05` — VO nad tuto úroveň aktivuje ducking
- `ratio=8` — kompresní poměr 8:1 (silné ducking)
- `attack=20` — 20ms ramp-down, dost rychlý aby chytl začátek slov
- `release=300` — 300ms ramp-up, dost dlouhý aby music neblikla mezi slovy
- `makeup=1` — kompenzace gain (žádná, sidechaincompress není makeup-needing)

Když VO mlčí (apad = ticho v posledních 2-3 s), threshold neaktivuje, music plyne plnou hlasitostí.

### 3. amix — finální spojení

```
[bgduck][vo_main]amix=inputs=2:duration=longest:dropout_transition=0:weights=1 1.6
```

- `duration=longest` — výsledná stopa = délka delšího vstupu (v praxi BG s padded VO oba ~15s)
- `weights=1 1.6` — BG full weight, VO 1.6× (další boost nad sidechain)
- `dropout_transition=0` — žádný fade když jeden vstup skončí (apad to už řeší)

### 4. alimiter — peak protection

```
alimiter=limit=0.95
```

Brutto limiter na 0.95 (-0.4 dBFS) — chrání před clippingem po amix + sidechain manipulacích. Bez něj může mix peakovat nad 1.0.

### 5. afade — audio fade-out na konci

```
afade=t=out:st=13.4:d=1.5
```

- `st=13.4` — start fade na 14.9s − 1.5s = 13.4s
- `d=1.5` — délka 1.5s
- Reálná duration se získá přes `ffprobe`, ne z briefu (Seedance může vrátit 14.5-15.0s)

### 6. fade (video) — video fade-out

```
fade=t=out:st=13.7:d=1.2
```

- Video fade je **kratší** než audio fade (1.2 vs 1.5s) — zvuk doznívá ještě po tom co obraz zčerná
- Při video fade-out se musí re-encodovat (`-c:v copy` nelze použít s `-vf`)

## Plný filter_complex

### S audiem v inputu (default — Seedance generate_audio: True)

```
[1:a]volume=2.5,apad=whole_dur=14.93,asplit=2[vo_main][vo_sc];
[0:a]volume=0.8[bg];
[bg][vo_sc]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300:makeup=1[bgduck];
[bgduck][vo_main]amix=inputs=2:duration=longest:dropout_transition=0:weights=1 1.6,alimiter=limit=0.95,afade=t=out:st=13.43:d=1.50[aout]
```

### Bez audia v inputu (silent fallback)

```
[1:a]volume=1.8,apad=whole_dur=14.93,alimiter=limit=0.95,afade=t=out:st=13.43:d=1.50[aout]
```

VO se stane jediným audiem. Volume×1.8 (vyšší než ×2.5 v sidechain mode protože není music co konkurovat).

## Plný ffmpeg cmd

```bash
ffmpeg -y \
  -i seedance.mp4 \
  -i voiceover.mp3 \
  -filter_complex "[1:a]volume=2.5,apad=whole_dur=14.93,asplit=2[vo_main][vo_sc];[0:a]volume=0.8[bg];[bg][vo_sc]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300:makeup=1[bgduck];[bgduck][vo_main]amix=inputs=2:duration=longest:weights=1 1.6,alimiter=limit=0.95,afade=t=out:st=13.43:d=1.5[aout]" \
  -map 0:v \
  -map "[aout]" \
  -vf "fade=t=out:st=13.73:d=1.2" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -shortest \
  final.mp4
```

## Edge cases

### probe_has_audio — silent input detection

Seedance **někdy vrátí video bez audio streamu** (rare, hlavně v kombinaci `generate_audio: False`). Funkce `probe_has_audio()` v `generate-video-singleshot.py` to detekuje přes ffprobe a přepne na silent-input fallback (VO becomes sole audio).

```python
def probe_has_audio(video_path):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ], capture_output=True, text=True)
    return bool(result.stdout.strip())
```

### Same-file write conflict

Když `source == output` (např. mix-only na finální mp4), ffmpeg odmítne s „Output same as Input — exiting". Funkce `mix_voiceover_with_video` detekuje a zapíše do `*.__mix_tmp__.mp4` → po success rename přes původní.

```python
same_file = video_path.resolve() == output_path.resolve()
write_to = output_path.with_name(output_path.stem + ".__mix_tmp__" + output_path.suffix) if same_file else output_path
# ... ffmpeg run ...
if same_file:
    write_to.replace(output_path)
```

### probe_duration — fade timing

Seedance vrací 14.5-15.0 s (ne přesně 15). Hardcoded fade=out:st=13.5 by způsobil neúplný fade. ffprobe zjistí reálnou duration:

```python
duration = probe_duration(video_path)
fade_start_audio = max(0.0, duration - 1.5)
fade_start_video = max(0.0, duration - 1.2)
```

## MIX_ONLY mode

Re-run jen ffmpeg post-process bez nového FAL volání. Použij když iteruješ na mix parametrech (volume, ducking threshold, fade délka) — ušetříš ~$4.50 a ~5 minut každou iteraci.

```bash
MIX_ONLY=1 bash run-step-3b-video.sh
```

Logika v `generate-video-singleshot.py`:

1. Hledá `<output>-seedance.mp4` (clean Seedance backup)
2. Pokud nenalezne, **snapshotuje** existující `<output>` jako `-seedance.mp4` (aby další iterace neodvíjely fade-out na sebe)
3. Spustí `mix_voiceover_with_video(seedance_path, vo_path, output_path)`

Plný režim (bez MIX_ONLY) automaticky vytvoří `-seedance.mp4` snapshot při každém běhu — clean Seedance výstup zůstává zachován pro budoucí mix-only iterace.

## Ladění mix parametrů

### VO je moc tichý vůči music

Zvyš `volume=2.5` na `volume=3.0` nebo `weights=1 1.6` na `weights=1 2.0`.

### Music je moc hlasitá při VO

Zesil ducking — `ratio=8` na `ratio=12`, nebo sniž `[bg]volume=0.8` na `0.6`.

### Music příliš silně dipuje pod VO (zní amaterskeji)

Změkči ducking — `ratio=8` na `ratio=4`, prodlouž `release=300` na `release=500`.

### Fade-out moc rychlý

Zvyš `afade d=1.5` na `2.0` nebo `2.5`. `--fade-out 2.5` flag v `generate-video-singleshot.py`.

### VO „pumpuje" (slyšitelné kompresorové dýchání)

Sniž `ratio=8` na `ratio=4-6`, prodlouž `attack=20` na `attack=40`. Sidechain by neměl být audibly aggressive.

### VO se začíná dřív/později než video

Zkrať/prodluž leading silence — Gemini TTS exportuje `start: 0.046` (46ms leadingu). Pokud potřebuješ jiný offset, použij `adelay=NNN|NNN` před `apad`:

```
[1:a]volume=2.5,adelay=500|500,apad=whole_dur=15,asplit=2[vo_main][vo_sc]
```

(500ms leading silence před VO)

## Cena

Post-mix běží **lokálně přes ffmpeg**, žádné FAL volání. Cena = elektřina + CPU čas (~5-15 s na M-class Macu pro 15 s 720p video s libx264 medium preset CRF 18).

MIX_ONLY iterace = zdarma + rychlé.
