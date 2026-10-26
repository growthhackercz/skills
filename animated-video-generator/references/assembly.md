# Sestavení + mix (ffmpeg)

Finál = **overlay render (video s textem)** + **namixované audio** (VO beaty + hudba + SFX) + outro fade. Vše přes `ffmpeg` (stdlib Python staví příkaz). Ověřeno v reálné výrobě.

U Omni projektů přidej do manifestu dialogue QA bránu:

```json
{"dialogueQa":{"required":true,"reports":["_qa/s1-dialogue-qa.json","_qa/s2-dialogue-qa.json"]}}
```

`assemble.py` před ffmpeg ověří, že každý report má PASS stav a odpovídá hashi aktuálního klipu. Starší manifest bez `dialogueQa` se chová beze změny.

## Spojení klipů (pokud skládáš z víc klipů před overlay)

3 klipy → `xfade` přechody (jemný `smoothleft`/`circleopen`/`fade`, duration ~0.6 s, offset = součet délek minus překryv). Scale na jednotné rozlišení + `fps=30` + `setsar=1` před xfade.

## Střih duplicitní / zacyklené scény (Seedance artefakt)

Seedance občas **zopakuje pohyb** (scéna proběhne 2×). Najdi bod (hustý odběr framů `fps=2..4` + Read), vystřihni ~2 s: rozděl klip na část A (0–X) a B (Y–konec), spoj s jemným `xfade=fade:0.3` v místě střihu (zamaskuje skok). Po střihu se zkrátí video → **zkrať i audio**, ať skončí dřív než obraz.

## Audio mix (jedna `amix` plocha)

- **VO beaty:** každý `adelay=<ms>:all=1, volume=1.15`, posazený na svůj scénový moment.
- **Hudba bed:** `volume=0.14` + **`afade=t=out:st=<~konec-4s>:d=4`** (fade dřív = ne uťaté).
- **SFX:** každý na svůj beat `adelay`, vol 0.4–0.6 (akcenty kasa/success 0.6–0.8). Krátké ořezy `atrim` + `afade` out.
- `amix=inputs=N:normalize=0:duration=longest, alimiter=limit=0.95` (normalize=0 zachová tvé hlasitosti, alimiter chrání před ořezem).

## Outro fade (povinné — ať konec není uťatý)

Na finálním muxu drž poslední frame + ztmav do černé:
```
[0:v]tpad=stop_mode=clone:stop_duration=0.7,fade=t=out:st=<len>:d=0.65[v];
[1:a]apad=pad_dur=0.9,afade=t=out:st=<len-0.4>:d=1.0[a]
-map [v] -map [a] -t <len+0.65>
```

## Mux overlay render + audio

Overlay render je muted → vezmi z něj video, z audio-mixu zvuk:
`ffmpeg -i overlay_render.mp4 -i mix.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest out.mp4`
(Pokud přidáváš outro fade, video re-enkóduj s `fade` filtrem místo `copy`.)

## QA finálu

- **Proof frame** na klíčové momenty (nápad, tým, výsledek, CTA) + frame v fade (ztmavuje).
- **Per-sekundový profil:** `volumedetect` (max ≤ ~-1 dB, žádný clip).
- Délka sedí, VO končí **před** koncem videa, diakritika v textu OK.
- Absolutní cesta k MP4 + `open`.

Hotový kód: `scripts/assemble.py` (parametrický: klipy/overlay + beaty + SFX + hudba + fade).
