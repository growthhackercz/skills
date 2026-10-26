# Omni engine — mluvící animované postavy s CZ lip-syncem

Model: **Google Gemini Omni Flash** přes FAL. Jediný model s kvalitním **českým lip-syncem**. Cena ~**$0,13/s** (720p). Používej ho, když má **animovaná postava mluvit** (dialog, testimonial, maskot, character-sales). Pro tichou animaci / b-roll zůstává Seedance (`seedance.md`).

## Proč Omni pro animaci (a ne pro živé lidi je to komplikace)

**Stylizované animované postavy (Pixar / anime / plastelína / LEGO / plyšák / 2D) content-policy NEBLOKUJE** — nejsou to reální lidé, takže **všechny dialogy jdou přímo `reference-to-video`**, bez fallbacků, které trápí živou větev. Animace je pro Omni ta **jednodušší** větev. (Seedance/Kling nemají kvalitní CZ lip-sync → mluvící CZ postavy vždy přes Omni.)

## Endpointy

| Endpoint | K čemu | Vstup |
|---|---|---|
| `google/gemini-omni-flash/reference-to-video` | **dialogové scény s postavami** (default) | `image_urls[]` (portréty postav), `prompt`, `duration` 3–10, `aspect_ratio` 16:9/9:16 |
| `google/gemini-omni-flash/image-to-video` | **inserty a fallbacky** (obrazovky/UI, end-card) | `image_url` (start image), jinak stejné |

Audio generuje Omni samo (řeč + ambience). **Hudbu v promptu ZAKAZUJ** („No background music“) — jeden průběžný podklad se přidá až v postu (HeyGen), jinak každá scéna má jinou hudbu, co po střihu restartuje.

## Character lock (konzistence postav) — klíčový trik

1. Vygeneruj **kanonické čelní portréty** postav ve zvoleném stylu (`refA.png`, `refB.png`) přes GPT Image 2 (styl deskriptor z `styles.md`) — čisté portréty postavy.
2. Do **každé** ref2v scény pošli portréty jako `image_urls` a v promptu je navaž tagy: `<IMAGE_REF_0>` = první, `<IMAGE_REF_1>` = druhý.
3. Formulace: *„the character on the LEFT matches reference `<IMAGE_REF_0>`… keep their look consistent with the references“*.
4. **Postavy vizuálně VÝRAZNĚ odlišné** (věk / vlasy / barva / oblečení) — podobné postavy Omni slévá do jedné. Kontrastní dvojice navrhni už v konceptu.

⚠️ I u animace nepiš „identical face / same face / preserve exact facial identity“ — zbytečně dráždí policy. „matches reference / consistent with“ stačí.

## Nativní multiscéna + pravidlo vyplněného času

**Jednotka renderu = generace ≤10 s s 1–3 záběry uvnitř** (Omni umí vnitřní střihy nativně). Vzor:
```
10-second …, TWO scenes with a hard cut at 5 seconds …
SCENE 1 (0–5s): [záběr 1 + replika 1] …
SCENE 2 (5–10s): [záběr 2 + replika 2] …
```
- **Dialog musí vyplnit CELOU generaci** (~1 s na 2–3 slova). Když je textu míň než času → Omni doplní vatu (zopakuje frázi / vymyšlené slovo = **„Bobe“ efekt**). Repliky rozděl mezi záběry, ať nikde nezbývá hluchý čas.
- **Neomezená délka** = řetězení N generací (concat), postavy drží přes character lock. 30 s ≈ 3× 10 s.
- Samostatné krátké scény (5 s) jen pro **img2v inserty** (obrazovky/end-card) nebo místa s chirurgickou kontrolou titulku.

## Prompt vzor (ref2v, animovaná dialogová scéna)

```
<STYL DESKRIPTOR z styles.md, např. modern Pixar/Disney 3D film still, warm cinematic light>.
Two characters at a table: the one on the LEFT matches reference <IMAGE_REF_0>, the one on
the RIGHT matches reference <IMAGE_REF_1>; keep their look consistent with the references.
Medium two-shot, slow push-in. The LEFT character leans in and says, in natural fluent Czech
with accurate lip-sync, exactly: „Počkej. Ty děláš marketing, obchod i provoz sám?“
No background music at all — only the spoken Czech line and quiet ambience.
No English, no subtitles, no on-screen text. Fictional cartoon character.
```
- Repliku piš **doslovně v uvozovkách + „exactly“** — je to zdroj lip-syncu i verbatim titulků.
- „No subtitles, no on-screen text“ — titulky děláme sami v overlay (přesné, pod tváří).

## Osa kamery + střihová skladba (KRITICKÉ)

1. **Střih NIKDY uprostřed repliky** — hranice záběrů plánuj tak, aby celá replika zazněla v jednom záběru (časy odvoď z délek replik ~1 s / 2–3 slova).
2. **180° pravidlo** — kamera drží NA JEDNÉ STRANĚ osy mezi postavami; NEpřeskakuj zleva doprava (se stejným pozadím vypadá svět zrcadlově otočený). Do promptu: *„all shots from the same side of the action axis“*.
3. **Sousední scény VŽDY jiná velikost/úhel záběru** (wide two-shot → medium → insert → medium). Dva stejné framingy za sebou = jump cut („postava poskočí“). Střídej i stranu (A → B → dvojzáběr).
4. Kde střih skřípe, zakryj **flash-to-white** v overlay — záchrana, ne náhrada za skladbu.

## Audio QA — POVINNÝ krok po renderu

Omni TTS dělá **neviditelné chyby** (anglicismy „AI Team“ místo „AI tým“, zdvojení slov, přeřek čísel, komolení brandu) — bez přepisu je nepoznáš.

1. **Přepiš každý klip** přes stávající jediný Fal Whisper call: `scripts/gen_omni.py transcribe <klip> --brief brief.json --scene <id>`.
2. Stejný call uloží raw transcript a porovná ho s replikou z briefu přes sdílený deterministický comparator; žádný druhý transcript request nepřidává.
3. `cut_fixable` lze opravit řezem, protože všechna očekávaná slova existují. `missing_words`, záměna, prázdná nebo nesrozumitelná řeč jsou hard block; řez je neopraví.
4. Rerender pouze vadné scény je poslední možnost a vyžaduje nový dry-run, cenu a souhlas.
5. **TTS-safe repliky už v konceptu:** čísla slovy („sedm týdnů“, ne „7 týdnů“), žádná anglicky vypadající slova, brand ven z replik když ho model komolí (nech na end-card).
6. Word-timestampy z přepisu slouží i pro **přesné časování titulků** v overlay.

## Princip editace při chybě (pořadí záchran)

1. **Vystřihnout** vadný záběr (vnitřní střih = přirozená hranice, word-timestampy z whisperu).
2. **Zkrátit** (trim vadného úseku).
3. **Dogenerovat cover** přes chybu (img2v, levné).
4. **Re-render** celé generace — až poslední možnost.

## Odolnost + inserty

- **Transport = `fal_client.subscribe`** (fronta + stažení spolehlivě). Spouštěj **systémovým python3** (fleet 3.11 / mac `/usr/bin/python3`), NE homebrew 3.14 (rozbitý pyexpat). Ruční urllib `response_url` poll u FAL video endpointů vrací 404 (viz `seedance.md`).
- **Per-scene guard** — pád jedné scény neshodí ostatní (řeší `gen_omni.py`). Existující klipy skip (`--force` pro re-render).
- **FAL upload transientní výpadky** („Invalid storage type“, 400 na upload/initiate) → upload obal **retry smyčkou** (3–4 pokusy, backoff 3·n s).
- **Obrazovky zařízení / UI** — vlož reálné mockupy do keyframu (GPT Image 2 edit) a scénu renderuj **img2v**: *„the on-screen UI stays FIXED, sharp and readable, never warping or changing text; only light/camera move“*. Obrazovka čelem, vzpřímená, nikdy zrcadlená.

## Kde to sedí v pipeline

Krok 3 = **volba enginu**: talking postava → Omni (tento soubor), tichá animace/b-roll → Seedance (`seedance.md`). Zvuk dialogu je u Omni **built-in** (Krok 4 = whisper QA + cut-fix; hudba/SFX až v postu). Overlay finishing (Krok 5) je **engine-agnostický** — stejný modul na Seedance i Omni klipech.

Hotový kód: `scripts/gen_omni.py` (`render` ref2v/img2v z briefu + `transcribe` whisper QA).
