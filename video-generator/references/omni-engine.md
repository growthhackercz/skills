# Omni engine — český lip-sync dialog + neomezená délka

Model: **Google Gemini Omni Flash** přes FAL. Jediný model s kvalitním českým lip-syncem (ověřeno 2026-07). Cena ~**$0,13/s** (720p, token-based).

## Endpoints

| Endpoint | K čemu | Vstup |
|---|---|---|
| `google/gemini-omni-flash/reference-to-video` | **dialogové scény s postavami** (default) | `image_urls[]` (reference), `prompt`, `duration` 3–10, `aspect_ratio` 16:9/9:16 |
| `google/gemini-omni-flash/image-to-video` | **inserty a fallbacky** (obrazovky, end-card, blokla scéna) | `image_url` (start image), jinak stejné |

Audio generuje omni samo (řeč + ambience). Hudbu v promptu **zakazuj** („No background music“) — jeden průběžný podklad se přidá až v postu, jinak každá scéna má jinou hudbu, co po střihu restartuje.

## Character lock (konzistence postav) — klíčový trik

1. Vygeneruj **kanonické čelní portréty** postav (refA.png, refB.png) — čisté studiové headshoty.
2. Do **každé** ref2v scény pošli oba jako `image_urls` a v promptu je navaž tagy: `<IMAGE_REF_0>` = první obrázek, `<IMAGE_REF_1>` = druhý.
3. Formulace: *„the man on the LEFT matches reference <IMAGE_REF_0>… keep their look consistent with the references“*.
4. **Postavy musí být vizuálně VÝRAZNĚ odlišné** (věk / vlasy / vousy / brýle / oblečení) — podobné postavy omni slévá do jedné tváře. Navrhuj kontrastní dvojice už v konceptu.

⚠️ **NIKDY nepiš „identical face“, „same face“, „preserve exact facial identity“** — spouští content-policy blok (ochrana proti napodobení osoby).

## Nativní multiscéna (DEFAULT) + pravidlo vyplněného času

**Jednotka renderu = generace ≤10 s s 1–3 záběry uvnitř** — omni umí vnitřní střihy nativně. Prompt vzor:

```
10-second …, TWO scenes with a hard cut at 5 seconds …
SCENE 1 (0–5s): [záběr 1 + replika 1] …
SCENE 2 (5–10s): [záběr 2 + replika 2] …
```

- **Dialog musí vyplnit CELOU generaci** (~1 s na 2–3 slova). Když je textu míň než času, omni doplní vatu — **zopakuje frázi nebo přidá vymyšlené slovo** („Bobe“ efekt). Repliky rozděl mezi záběry tak, aby nikde nezbýval hluchý čas.
- **Každý záběr uvnitř generace = jasná změna kamery** (viz Střihová skladba níže) — platí uvnitř generace i mezi generacemi.
- Výhody: méně generací, plynulejší vnitřní střihy (stejná generace = perfektní kontinuita), přirozený tok dialogu přes střih.
- **Kdy naopak samostatné krátké scény (5 s):** img2v inserty (obrazovky, end-card), policy-rizikové záběry, místa, kde chceš chirurgickou kontrolu (přesný titulek/punch timing).

**Neomezená délka** = řetězení N generací (concat), postavy drží přes character lock. 30s video ≈ 3× 10s generace (á 2–3 záběry).

## Princip editace při chybě (pořadí záchran)

1. **Vystřihnout** vadný záběr — vnitřní střih je přirozená hranice řezu (word-timestampy z whisperu).
2. **Zkrátit** (trim vadného úseku).
3. **Dogenerovat cover záběr/insert** přes chybu (img2v, levné).
4. **Re-render celé generace** — až poslední možnost.

## Osa kamery + střihy vs. repliky (KRITICKÉ — vypadá nepřirozeně, když se poruší)

1. **Střih NIKDY uprostřed repliky.** Hranice záběrů v multiscénním promptu (`SHOT k (t0–t1s)`) plánuj tak, aby **celá replika zazněla v jednom záběru** — časy SHOT hranic odvoď z délek replik (~1 s na 2–3 slova). Kamera, co „skočí“ během věty, působí rozbitě.
2. **Drž osu kamery (180° pravidlo).** V rámci jedné lokace se kamera drží NA JEDNÉ STRANĚ pomyslné osy mezi postavami — záběry se liší velikostí a úhlem, ale **NEpřeskakuj zleva doprava** (zvlášť ne se stejným pozadím — vypadá to, jako by se svět zrcadlově otočil). Do promptu piš explicitně: *„all shots from the same side of the action axis / camera stays on the driver's side“* apod.
3. Změna strany je OK jen s **motivací** (postava se otočí, projde kamera, nová lokace) — jinak střihy variovat velikostí (wide → medium → insert), ne stranou.

## Střihová skladba — sousední scény VŽDY jiný úhel/velikost záběru

Omni scény na sebe prostorově nenavazují → mezi scénami je tvrdý střih. **Dva podobné záběry za sebou = jump cut** (postava „poskočí“, vypadá to rozbitě). Pravidlo:

- **Mezi sousedními scénami změň velikost NEBO úhel záběru** (wide two-shot → medium close-up → insert na telefon → medium shot…). Nikdy dva stejné framingy za sebou.
- Plánuj už ve storyboardu: každá scéna má `shot_type` a sousední se liší (orientačně o ≥30° úhlu nebo o stupeň velikosti).
- Střídej i **stranu** (záběr na A → záběr na B → dvojzáběr) — dialogová šachovnice.
- Kde střih i tak skřípe (návaznost gest), zakryj ho **flash-to-white** přechodem (viz finishing-hyperframes.md) — ale flash je záchrana, ne náhrada za dobrou skladbu záběrů.

## Prompt vzor (ref2v dialogová scéna)

```
Vertical 9:16, cinematic anamorphic 35mm, warm morning cafe light, deep navy and cyan
brand tones, shallow depth of field. Two businessmen at a cafe table: the man on the
LEFT matches reference <IMAGE_REF_0>, the man on the RIGHT matches reference
<IMAGE_REF_1>; keep their look consistent with the references.
Medium two-shot, slow push-in. The LEFT man leans forward and says, in natural fluent
Czech with accurate lip-sync, exactly: „Počkej. Ty děláš marketing, obchod i provoz sám?“
No background music at all — only the spoken Czech line and quiet cafe ambience.
No English, no subtitles, no on-screen text.
```

- Repliku piš **doslovně v uvozovkách** + „exactly“ — je to zároveň zdroj verbatim titulků.
- „No subtitles, no on-screen text“ — titulky děláme sami ve finishing (přesné a pod tváří).

## Content-policy fallback žebřík

Gemini blokuje prompty, co „replikují konkrétní reálnou tvář“. Ověřená eskalace:

0. **Nikdy nepiš „close-up on his/her FACE“** (ani „facial close-up“, „medium close-up on the man“) — detail tváře v textu promptu spouští blok i u img2v. Piš „reaction shot: the woman watches amazed“, „medium shot: the man leans against the desk“ — záběr popiš akcí/tělem, ne tváří.
1. **Dvojzáběr** (oba v obraze) místo těsného detailu jedné tváře — detaily blokuje nejčastěji.
2. Změkčit identitu: „matches reference / consistent with“ místo „identical“.
3. **img2v fallback:** vytáhni snímek z už vyrenderované scény (`ffmpeg -ss X -frames:v 1`) → `image-to-video` s replikou. Image-to-video content-policy prakticky neblokuje a postavy sedí (snímek je z téže scény).
4. **img2v z keyframu generace (když ref2v blokuje celý projekt):** dramatické/akční portréty (noční rim light, filmový look) zvyšují citlivost likeness policy — ref2v pak padá i na dvojzáběrech. Řešení: vygeneruj **start keyframe celé generace** přes gpt-image-2 (portréty jako reference — ten je bere bez problému) a generaci renderuj `image-to-video`. **Funguje včetně multiscény a dialogu s lip-syncem** (ověřeno). Bonus: přesnější kontrola kompozice.

Render scén pouštěj **odolně** — pád jedné scény nesmí shodit ostatní (script to řeší per-scene guardem).

**FAL upload má transientní výpadky** („Invalid storage type“, 400 na upload/initiate) — každý `upload_file_async` obal retry smyčkou (3–4 pokusy, backoff 3·n s) a delší řetěz (QA→trim→finishing) stav ověřuj fail-fast, ať prázdný mezivýsledek nepodtrhne zbytek.

## Audio QA — POVINNÝ krok po renderu (Omni TTS dělá neviditelné chyby)

Omni občas repliku zkomolí a **bez přepisu to nejde poznat**: anglická záměna („AI Team“ místo „AI tým“), zdvojení slov, přeřek čísel, komolení brand jména.

1. **Přepiš každý klip** přes FAL whisper: `fal-ai/whisper` s `chunk_level: "word"` (word-level timestampy).
2. Porovnej s `line.text` z briefu přes sdílený deterministický dialogue QA comparator.
3. `cut_fixable` znamená, že všechna očekávaná slova existují a navíc je opakování/extra úsek — pouze tento stav lze opravit řezem podle word timestampů.
4. `missing_words`, `substitution_or_order_error`, `no_speech` nebo `unreadable` jsou hard block. Řez chybějící slova nevytvoří; zkrať/rozděl repliku, nebo po novém dry-run + souhlasu rerenderuj jen vadnou scénu.
5. **TTS-safe repliky už v konceptu (Krok 1):** čísla slovy („sedm týdnů“, ne „7 týdnů“), žádná anglicky vypadající slova, brand jméno ven z replik, pokud ho model komolí (nech ho na end-card).
6. Finální `build-finishing.py` znovu použije svůj existující Whisper výsledek jako gate a uloží raw přepis i `logs/dialogue-qa-final.json`; žádný druhý transcript request nepřidává. Stejné timestampy slouží pro titulky.

## Analýza sekvence (ne jen izolovaných scén)

Opakovaný/držený záběr a hrubý střih se pozná **až v návaznosti klipů** — po renderu si vytáhni framy přes hranice střihů (poslední frame scény N + první frame N+1) a zkontroluj sekvenci jako celek, ne scény izolovaně. img2v inserty (obrazovky/end-card) bývají statické → ořezat tight kolem VO (fixní `trim` okno v briefu).

## Obrazovky zařízení ve scéně

Reálné produktové UI (mockupy) vlož do **keyframu** (gpt-image-2 edit s mockup referencí) a scénu renderuj **img2v** s instrukcí: *„the on-screen UI stays FIXED, sharp and readable, never warping, morphing or changing text; only light, camera, particles move“*. SCREEN ACCURACY: obrazovka čelem, vzpřímená, nikdy zrcadlená.
