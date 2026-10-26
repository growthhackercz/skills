# Assembly — timeline manifest + FFmpeg (multi-scéna)

HyperFrames renderuje JEDNU kompozici. Spojení víc scén, retiming na narraci a mix = FFmpeg vrstva. Destilát Sara (Apache-2.0).

## Timeline manifest = jediný zdroj pravdy

JSON popisuje scény, retiming a mix. Captions i hudba z něj čtou — žádné hádání. Schéma (`templates/timeline-manifest.example.json`):

```json
{
  "project": { "name":"...", "width":1920, "height":1080, "fps":60, "output":"renders/final.mp4" },
  "segments": [
    { "id":"scene-01", "video":"renders/scene-01.mp4", "source_duration":9.0,
      "target_duration":10.0, "audio":"assets/s01.mp3", "strategy":"retime-to-audio" },
    { "id":"scene-02", "strategy":"segment-map",
      "maps":[ {"source_start":0.0,"source_end":4.0,"target_duration":5.8},
               {"hold_source_time":4.0,"target_duration":1.5},
               {"source_start":4.0,"source_end":13.0,"target_duration":9.2} ] }
  ],
  "music": { "file":"assets/music.mp3", "start_offset":0.7, "duck_under_narration":true, "end_silence_seconds":2.0 },
  "proofs": [ { "time":27.0, "label":"chart-visible" } ]
}
```
Script spočítá `setpts` poměry a kumulativní starty scén:
```bash
python3 scripts/timeline_manifest_to_ffmpeg.py manifest.json
```

## Smallest timing intervention ladder

Vyber NEJMENŠÍ zásah (nikdy nepřetimuj celé video kvůli jedné pauze):

```bash
# 1) celá scéna: RATIO = target/source
[0:v]setpts=RATIO*PTS,fps=60,scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p[v]

# 2) segment map (cue body na fráze)
[0:v]trim=0:4,setpts=1.25*(PTS-STARTPTS)[v0];[0:v]trim=4:10,setpts=0.90*(PTS-STARTPTS)[v1];[v0][v1]concat=n=2:v=1:a=0[v]

# 3) hold frame na ticho (ne global slowdown) — end = start + 1/fps
[0:v]trim=4:4.0167,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1.5,trim=duration=1.5[vhold]

# 4) audio-only atempo (jen když chráníš schválený downstream timeline)
```

## Concat (explicitní v/a, ne implicit mux)

```
[v0][v1][v2]concat=n=3:v=1:a=0[v]
[a0][a1][a2]concat=n=3:v=0:a=1[a]
```

## Pořadí assembly (fixní)

synced segmenty → concat do **narration-only master** → captions z masteru → burn captions → music bed → mix (ducking, viz audio.md) → export + náhledy.

**Pravidla:** netiminuj ze starých final MP4 (timing ber ze source renderů + audio); konec hudby z hudebně užitečné pozdější pasáže (neklipuj poslední beat); drž 2s+ ticho na konci.
