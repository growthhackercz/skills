# Brief schema — `video-brief.json`

Řídí celou pipeline (render, trim, finishing). Šablona: `templates/video-brief.template.json`.

Nové briefy používají `briefVersion: 2` a povinný dialogue gate:

```json
{"briefVersion":2,"dialogueQa":{"required":true,"aliases":{}}}
```

`aliases` slouží jen pro explicitní ASR varianty konkrétního projektu. Nesmí skrýt chybějící víceslovnou frázi.

## Top-level

| Pole | Typ | Povinné | Popis |
|---|---|---|---|
| `briefVersion` | integer | ✅ | `2` pro fail-closed dialogue QA; legacy brief bez pole zůstává kompatibilní |
| `dialogueQa` | object | ✅ pro Omni v2 | `{required:true, aliases:{}}`; sdílený gate nad existujícím Whisper přepisem |
| `campaign_slug` | string | ✅ | kebab-case, = název složky v `documents/videos/` |
| `version` | string | ✅ | verze briefu |
| `language` | string | ✅ | `cs` / `en` / `es` |
| `engine` | enum | ✅ | `omni` (CZ dialog lip-sync, default) / `seedance-vo` (VO přes obraz) / `seedance-native` (EN/ES dialog) |
| `aspect_ratio` | enum | ✅ | `9:16` / `16:9` |
| `style` | string | ✅ | sdílený vizuální styl — prefix promptu každé scény |
| `characters` | array | ref2v | `{id, ref_image, description}` — pořadí = `<IMAGE_REF_n>` indexy |
| `scenes` | array | ✅ | viz níže; celková délka = Σ durations (neomezená) |
| `subtitles` | object | — | `{enabled, font, gradient[], bottom_px, lines, style}`. **`lines`** = `{ "<scene_id>": [ [pre, big, post], ... ] }` — repliky per scéna: `pre`/`post` = běžná slova, `big` = **jedno** velké gradientové klíčové slovo (pointa) na vlastním řádku — VŽDY jen jedno slovo (víc slov skript automaticky ořízne na poslední). Jedna položka = jedna replika (mluvčí se NEmíchají). Časuje `build-finishing.py` z FINÁLNÍHO videa. **`style`**: `"kinetic"` (default — velké kinetické big-slovo) / `"documentary"` (dokumentární rodina — všechna slova decentní a menší, žádné velké gradientové slovo). |
| `flashes` | array | — | id scén, PŘED kterými je flash-to-white (jen na nesouvislé/hrubé střihy — ne na každý) |
| `punch` | object | — | `{text, scene, word}` — obří slovo přes obraz, pop přesně na vyslovené slovo (nesmí duplikovat big titulek) |
| `_sfx` | array | — | zvukové efekty na eventy: `[{t, file, vol}]` (t = čas ve finálním videu). Premix do dialogu před muxem. Hudba se sem NEdává (jen jeden HeyGen podklad v postu). |
| `flashes` | array | — | id scén, PŘED kterými je flash-to-white (hrubé střihy) |
| `punch` | object | — | `{text, at_time}` — obří slovo na prvním flashi, synced na řeč |
| `music` | object | — | `{query, arc: true}` — HeyGen track + gradace |

## `scenes[]`

| Pole | Typ | Popis |
|---|---|---|
| `id` | string | `s1a`, `s1b`… (pořadí = pořadí ve videu) |
| `mode` | enum | `ref2v` (dialog s postavami) / `img2v` (insert/end-card/fallback) |
| `shot_type` | string | velikost/úhel záběru — **sousední scény se MUSÍ lišit** (anti jump-cut, viz omni-engine.md) |
| `duration` | int | 3–10 s; **≈ délka repliky** (pravidlo 5 s — viz omni-engine.md) |
| `prompt` | string | akce scény; u dialogu obsahuje repliku doslovně v „uvozovkách“ + „exactly“ |
| `line` | object | `{speaker, text}` — verbatim replika (zdroj titulků); `null` u scén bez řeči |
| `start_image` | string | jen img2v — cesta ke keyframu |
| `trim` | object | volitelné `{lead, out}` — fixní ořezové okno (jinak auto silencedetect) |

## Pravidla

- `engine=omni` + dialog → `mode=ref2v` + `characters` vyplněné.
- Scéna s obrazovkou zařízení / end-card → `mode=img2v` + `start_image` (reálný mockup v keyframu).
- Content-policy fallback: scéna se dá kdykoli přepnout na `img2v` + `start_image` ze snímku jiné scény.
- `line.text` = přesně to, co má zaznít — používá se pro lip-sync prompt I pro titulky (jeden zdroj pravdy).
