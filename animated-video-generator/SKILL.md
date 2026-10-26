---
name: animated-video-generator
version: "1.2"
publishedAt: "2026-09-01"
description: "Vyrobí virální animované video (MP4 16:9, ~20–60 s) z brand + product DNA pro libovolný cíl — launch, explainer, reklamu, brand story i feature highlight. Klient si vybere virální styl (Pixar 3D, Ghibli/anime, plastelína, LEGO, plyšák, 2D motion) a engine: tichá animace + voiceover (Seedance 2.0), nebo mluvící postavy s českým lip-syncem (Omni). Schvaluje každý krok. Pipeline: koncept → storyboard (GPT Image 2) → animace (Seedance / Omni) → zvuk (dialog nebo voiceover + hravé zvuky, HeyGen) → kinetické textové vrstvy (HyperFrames) → finální mix. Žádný cloud render textu, každé pálení FAL kreditů schvaluješ předem."
category: creative
status: stable
metadata: {"openclaw":{"requires":{"bins":["python3","ffmpeg","node"],"env":["FAL_KEY"]},"primaryEnv":"FAL_KEY","emoji":"🎬"}}
---

# Animated Video Generator

Z brand + product DNA udělá **virální animované video** v jednom z trendy stylů (Pixar 3D, anime, plastelína, …). Animaci řeší podle typu **Seedance 2.0** (tichá animace) nebo **Omni** (mluvící postavy s **českým lip-syncem**), text a kinetiku **HyperFrames overlay** nad hotovou animací. Univerzální — funguje pro libovolný **typ** (launch, explainer, reklama, brand story, feature) a libovolný produkt; konkrétní příběh a scény se vždy **odvodí z DNA + cíle videa**, nejsou napevno.

**Pipeline (7 kroků):** Intake → Styl+koncept → Storyboard → Animace → Zvuk → Text vrstvy → Sestavení.

Staví na nejlepších postupech z **`html-video-generator`** (brand font + diakritika, hravé HeyGen audio, HyperFrames overlay, per-písmeno kinetika, FAL `--dry-run` + STOP).

## Globální pravidla (každý krok)

- **Engine podle typu videa:** **Seedance 2.0** (`bytedance/seedance-2.0/...`) = **tichá animace / b-roll** z storyboard stillu (+ samostatný voiceover). **Omni** (`google/gemini-omni-flash/reference-to-video`) = **mluvící animované postavy s CZ lip-syncem** (dialog, testimonial, maskot, character-sales) — řeč generuje engine sám. Pro animaci je Omni **snazší** (stylizované postavy neblokuje content-policy). Jiný video model nepoužívej. Viz `references/seedance.md` a `references/omni.md`.
- **Do animace NIKDY nepiš text** — Seedance komolí (hlavně češtinu). Veškerý text = **HyperFrames vrstva nad videem** (Krok 5). Storyboard i Seedance prompty drž bez nápisů; výstupy na obrazovkách nech jako reálné vizuály (fotky, plochy), ne nápisy.
- **Příběh odvoď z DNA + cíle videa**, nepředpokládej žádnou fixní zápletku. Vyber strukturu podle typu (problém→řešení→výsledek pro reklamu, hook→jak to funguje→payoff pro explainer, atd. — viz `references/storyboard.md`). U sales/ad videí drž **POV diváka** (jeho situace, jeho výsledek), ne výčet funkcí.
- **Texty ve videu = vykání** (klient). Generické role agentů (AI Marketér, ne konkrétní jména), žádný „druhý mozek".
- **Brand font POVINNĚ** v overlay (CliqSales = Manrope), subset **latin + latin-ext** kvůli diakritice (ř ž č ě ů). Vendoruj woff2 lokálně. Detail `references/overlay.md`.
- **Zvuk = HeyGen** (`scripts/heygen_audio.py`), hravý a charakterní (popy/whooshe/sparkly na beaty), ne technický. **HeyGen je VOLITELNÝ** — bez `HEYGEN_API_KEY` skill jen upozorní a video vyrobí **bez hudby a SFX** (animace, text overlay i VO/dialog fungují dál). Viz `references/audio.md`.
- **Voiceover** = Gemini TTS (`fal-ai/gemini-3.1-flash-tts`). Generuj **po beatech** a posaď na momenty ve videu (sync podle screenshotů). Viz `references/audio.md`.
- **Render textových vrstev LOKÁLNĚ** (`npx hyperframes render`) — žádný cloud.
- **Žádné pálení FAL kreditů bez `--dry-run` + STOP.** Platí se Seedance animace (~$3.6/15 s fast) a storyboard/VO (drobné). HeyGen audio je zdarma.
- **Proof-before-done:** po každém Seedance klipu a po overlay renderu zkontroluj QA framy vizuálně (extrahuj + Read).
- Projekt v `documents/videos/<slug>/` (nebo `documents/ads/video/<slug>/`).

## Krok 0 — Intake

Načti `documents/brand/brandDNA.md`, `DESIGN.md`, `documents/brand/products/<slug>/productDNA.md`. Zjisti: produkt, **typ videa + cíl** (launch / explainer / reklama / brand story / feature), délka (default ~20–45 s = 1–3 klipy po 15 s), jazyk (default CZ), publikum. Žádný spend.

## Krok 1 — Styl + koncept 🛑

Načti `references/styles.md`. Ukaž **menu virálních stylů** (Pixar 3D / Ghibli-anime / plastelína / LEGO / plyšák / 2D motion) s krátkým popisem vibe + pro koho. Podle konceptu urči **engine**: **mluví postava** (dialog / testimonial / maskot / character-sales) → **Omni** (CZ lip-sync); **tichá animace + voiceover** → Seedance. Navrhni **3 koncepty** odvozené z DNA + cíle (každý: struktura příběhu, beaty, hlavní message, engine, odhad FAL nákladů — Seedance ~$3,6/15 s, Omni ~$0,13/s). U Omni piš **TTS-safe repliky** (čísla slovy, bez anglicismů, brand ven z repliky). Volitelně 1 ukázkový still na top styl.

**STOP 1 — klient vybírá STYL + koncept + engine.**

## Krok 2 — Storyboard 🛑

Načti `references/storyboard.md`. Ve zvoleném stylu vygeneruj **storyboard** přes GPT Image 2 (`openai/gpt-image-2/edit`) — per-scéna stilly (počet dle délky/konceptu), **postava + prostředí konzistentní**, výstupy = reálné vizuály, **bez velkého textu**. Slouží jako reference stills pro Seedance + k vizuálnímu schválení.

**STOP 2 — storyboard. Klient schvaluje vizuální směr. Ulož do `documents/videos/<slug>/_storyboard/`.**

## Krok 3 — Animace (Seedance nebo Omni) 🛑

Podle zvoleného enginu:

**A) Tichá animace → Seedance 2.0** (`references/seedance.md`). Z každého stillu klip: `scripts/gen_seedance.py --dry-run`. Params: reference-to-video, `duration:"15"`, `16:9`, `720p`, `generate_audio:False`. Face moderation 422 → face-light + „fictional cartoon character". QA frame po klipu. Klipy do `_clips/`.

**B) Mluvící postavy → Omni** (`references/omni.md`). Vygeneruj **kanonické portréty postav** ve stylu (GPT Image 2, výrazně odlišné postavy), sestav `brief.json` (scenes s **verbatim CZ replikami** + character lock `<IMAGE_REF_n>`). Render: `scripts/gen_omni.py render --brief brief.json --dry-run` → proof 1 scéna → `--all`. Pravidla: **≤10 s / 1 replika na záběr** (jinak „Bobe" efekt), řetězení delších videí, **hudbu v promptu zakázat**, sousední scény jiný úhel/velikost, 180° osa. Klipy do `_shots/`.

**STOP 3 — `--dry-run` prompty + cena (Seedance ~$3,6/15 s, Omni ~$0,13/s). Po schválení generuj proof, pak zbytek.**

## Krok 4 — Zvuk (dialog/VO + hudba + SFX) 🛑

Načti `references/audio.md`.
- **Omni mode:** řeč je **built-in** v klipech → stávající povinný Whisper call spusť jako `scripts/gen_omni.py transcribe <klip> --brief brief.json --scene <id>`. Stejný call uloží raw transcript i dialogue QA report; žádný další provider request nepřidává. Řez je povolen jen pro `cut_fixable`; chybějící/zaměněná/nesrozumitelná řeč blokuje assembly. Samostatný VO negeneruj.
- **Seedance mode:** VO po beatech (`scripts/gen_voiceover.py`, retry+loudnorm), sync podle screenshotů scén.
- **Oba:** HeyGen hudba (vibe z DNA) + **hravé SFX na akce** (`scripts/heygen_audio.py`), hudba potichu pod (ducking) — přidej až **v postu** (u Omni byla v promptu zakázaná, ať po střihu nerestartuje).

**STOP 4 — audio plán (dialog/beat → zvuk → čas). HeyGen zdarma. VO/whisper drobný FAL spend.**

## Krok 5 — Textové vrstvy (HyperFrames overlay) 🛑

Načti `references/overlay.md`. Zkopíruj `templates/overlay/` do projektu, vlož **muted video jako `<video class="clip">` podklad** + textové sub-kompozice nad ním (headliny, label chipy, info karty, razítka/badge, CTA + logo — dle konceptu). **Per-písmeno elastická kinetika** na velké texty. Vrstvy zakryjí případný gibberish na obrazovkách. Manrope + latin-ext. `lint` (0 errors) → `render` → QA frame.

**STOP 5 — náhled vrstev. Iteruj tady.**

## Krok 6 — Sestavení + mix + final 🛑

Načti `references/assembly.md`. Sestav finál (`scripts/assemble.py`): overlay render + namixované audio (VO beaty + hudba s dřívějším fade + SFX na beaty), **outro fade do černé**. U Omni nastav v manifestu `dialogueQa.required: true` a vypiš všechny QA reporty; assembly ověří jejich PASS a hash klipu. Legacy manifest bez `dialogueQa` zůstává kompatibilní. Volitelně vystřihni duplicitní/zacyklené Seedance scény. Mix: VO ~1.15, hudba bed ~0.14 (fade dřív), SFX 0.4–0.6, alimiter.

**STOP 6 — final s audiem + proof frame. Finální schválení.**

## Krok 7 — Delivery

Vypiš absolutní cestu k MP4 + `open`. Handoff: styl, délka, co lze re-renderovat (text vrstvy bez re-animace, VO beaty, SFX). Surgical edity textu = jen příslušná sub-kompozice + re-render overlay + re-mux.

## Reference (načítej průběžně)

- `references/styles.md` — 6 virálních stylů, Seedance prompt recepty per styl. **Krok 1.**
- `references/seedance.md` — Seedance 2.0 API (tichá animace, endpoint, FAL CDN upload, face moderation, cena, async). **Krok 3.**
- `references/omni.md` — Omni CZ lip-sync (mluvící postavy, endpointy, character lock, ≤10 s/řetězení, whisper QA, cut-fix). **Krok 3–4.**
- `references/storyboard.md` — story-arc rámce dle typu videa, GPT Image 2 stilly, konzistence. **Krok 2.**
- `references/audio.md` — HeyGen hudba + HRAVÉ SFX (kategorie momentů) + VO po beatech (Gemini), sync, ducking. **Krok 4.**
- `references/overlay.md` — HyperFrames overlay (video-bg, typy vrstev, kinetika, brand font + diakritika). **Krok 5.**
- `references/assembly.md` — ffmpeg mix (beaty, SFX, hudba fade, outro fade, střih duplicit), QA. **Krok 6.**
- `references/production-recipes.md` — univerzální principy + krátký příklad z reálné výroby. **Vždy.**
