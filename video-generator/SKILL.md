---
name: video-generator
version: "1.2"
publishedAt: "2026-09-01"
description: "Vyrobí hrané reklamní video s reálnými postavami — český dialog s lip-syncem (Omni engine), libovolná délka řetězením scén, konzistentní postavy napříč záběry. Alternativně Seedance + český voiceover. Vždy nejdřív levný storyboard a keyframy ke schválení, teprve pak placený render. Finálně kinetické titulky, flash přechody a hudba přes HyperFrames finishing."
category: creative
status: stable
metadata: {"openclaw":{"requires":{"bins":["python3","ffmpeg","node"],"env":["FAL_KEY"]},"primaryEnv":"FAL_KEY","emoji":"🎬"}}
---

# Video Generator (hrané video)

Vlajkový video skill: **reální lidé v záběru**. Unikát = **český dialog s lip-syncem** (jediný model, který to umí — Gemini Omni Flash) a **neomezená délka** řetězením krátkých scén se zamčenými postavami. Pro animaci použij `animated-video-generator`, pro grafické/produktové video bez video modelů `html-video-generator`.

## 🛑 Globální pravidla (každý krok)

1. **Storyboard + keyframy PŘED placeným renderem — POVINNÉ.** Schválit směr na obrázku stojí centy, přerenderovat špatné video dolary. Bez schváleného storyboardu se video negeneruje.
2. **STOP po každém kroku** — uživatel schvaluje koncept, storyboard, keyframy, proof scénu i finál. `--dry-run` před každým FAL voláním.
3. **VŽDY volej skillní scripty** (`{baseDir}/scripts/`), nikdy vlastní inline scripty.
4. **Titulky:** verbatim (přesně co se mluví), kineticky po slovech, časované na řeč, NIKDY přes obličej. Detail `{baseDir}/references/finishing-hyperframes.md`.
5. Brand kontext: načti `/documents/brand/brandDNA.md` + `/documents/brand/products/<slug>/productDNA.md` před psaním konceptů. Klientské texty ve videu = vykání, generické role agentů.
6. **Výstup do `documents/videos/<campaign-slug>/`** (lokálně i server `/documents/videos/<slug>/`). **Struktura je správná OD ZAČÁTKU — nic se neuklízí zpětně:**
   - **Hned na začátku vytvoř `<kampaň>/assets/` a VŠECHNU práci dělej uvnitř** (`cwd=assets/`): brief, `_base.mp4`, `_trim.txt`, `_shots/`, `_shots_trim/`, `hf/`, `screens/`, `refs/`, `images/`, `music/`, `sfx/`, `logs/`; kontrolní PNG do `assets/proof/`. Galerie `assets/` ignoruje → v galerii je vidět jen finál.
   - **Root složky = JEN verzované finály** `final-v1.mp4`, `final-v2.mp4`, … (poslední iterace = nejvyšší číslo, historie se NEpřepisuje).
   - Po schváleném renderu: `scripts/organize-output.py <kampaň> --promote assets/<vyrenderovaný>.mp4` → přesune ho do rootu jako další `final-vN.mp4`. (Root nikdy nezaneřádíš, takže žádný úklid netřeba.)

## Workflow

```
Krok 0  Intake: jazyk + délka + formát + engine
Krok 1  Koncepty (3–5 z brand+product DNA)          → STOP
Krok 2  Storyboard (1 PNG, ~$0,2)                    → STOP
Krok 3  Keyframy scén + kanonické portréty postav    → STOP (kontakt sheet)
Krok 4  Proof scéna (1× ~5s, ~$0,65)                 → STOP (lip-sync check)
Krok 5  Render všech scén + trim mrtvých pauz
Krok 6  Finishing: HyperFrames titulky/flash/punch + HeyGen hudba + mux → final.mp4
```

## Krok 0 — Intake: polož 2–3 otázky, zbytek odvoď sám

Načti DNA produktu a polož uživateli **max 3 otázky** (víc ne — není marketér):

1. **„Co má video prodat a komu?“** (produkt/nabídka + cílovka — pokud není jasné z DNA)
2. **„Mají ve videu mluvit lidé na kameru, nebo stačí hlas přes obraz?“** (+ jazyk, pokud není CZ)
3. **„Jak dlouhé a kam?“** (délka + platforma — Reels/TikTok 9:16 default)

**Z odpovědí sám odvoď rodinu konceptu → engine (uživatel to neřeší)** — rodiny detailně v `references/concept-families.md`:

| Odpovědi | Rodina konceptu | Engine |
|---|---|---|
| mluví CZ na kameru + prodat produkt / přesvědčit skeptika | **stealth dvojrozhovor** (`references/stealth-concepts.md`) | **Omni** ref2v |
| mluví CZ na kameru + autenticita / osobní doporučení | **UGC talking-head** (`references/concept-families.md`) | **Omni** ref2v (⚠ proof scéna povinná — policy) |
| delší formát / emoce / transformace | **mini-příběh** (`references/concept-families.md`) | Omni / Seedance+VO dle vyprávění |
| virální / akční / „wow“ | **akční skill-download** (`references/concept-families.md`) | **Omni** multiscénní generace |
| autenticita / důvěra / nemá vypadat jako reklama / realistický native pocit | **dokumentární příběh** (`references/concept-families.md`) | **Omni** / **Seedance + VO** (délka volná, doporuč 30–60 s) |
| hlas přes obraz (nikdo nemluví) | VO příběh / product-story | **Seedance + VO** (`references/seedance-vo.md`) |
| EN/ES dialog | stealth dvojrozhovor | Seedance native (≤15 s) / Omni |
| delší než 15 s v jakékoli variantě | řetězení ~5s scén | **Omni** (character lock) |

## Krok 1 — Koncepty 🛑

Podle rodiny z Kroku 0 navrhni **3–5 konceptů** z brand + product DNA (klidně mix rodin — `references/concept-families.md`; dialogové podle 10 stealth principů). Ke každému: beaty po scénách (~5 s/scéna), repliky (verbatim — budou i titulky), engine, odhad ceny (omni ~$0,13/s videa + keyframy ~$0,10/ks). **Repliky TTS-safe:** čísla slovy, žádná anglicky vypadající slova, komolené brand jméno nechat na end-card. Postavy dvojrozhovoru **vizuálně výrazně odlišné** (omni jinak tváře slévá). **STOP — uživatel vybírá.**

## Krok 2 — Storyboard 🛑

Vyplň `{baseDir}/templates/video-brief.template.json` → `video-brief.json` (schema: `references/brief-schema.md`). Vygeneruj **master storyboard PNG na celou délku** (1 panel = 1 záběr ~3 s, bez hudby) — viz `references/storyboard-a-keyframy.md`. **🛑 VŠECHEN text desky ČESKY** — nadpisy sekcí, popisky pohledů/záběrů, poznámky, paleta (přesné české nadpisy v referenci; pozor: externí generátor má anglické nadpisy natvrdo → přepiš). Po vygenerování Read-check, že tam není anglický nadpis. **STOP — schválení storyboardu (jediné).** Breakdown záběrů do ≤10s multiscénních generací pak udělej **interně bez STOPu** (`references/omni-engine.md` — Nativní multiscéna); mini-diff ke schválení jen při odchylce od storyboardu.

## Krok 3 — Keyframy + postavy 🛑

1. **Kanonické portréty postav** (`refs/refA.png`, `refs/refB.png`) — čisté čelní portréty přes `scripts/generate-keyframe.py` s referencí ze storyboardu. Tyto 2 fotky se zamknou do KAŽDÉ scény → konzistence.
2. **Keyframy scén** (9:16) per scéna — start image pro img2v scény (obrazovky, end-card) + vizuální kontrola. Reálné produktové UI vkládej z mockupů (ne vymyšlené dashboardy).
3. Sestav **kontakt sheet** a **STOP — schválení keyframů** (zkontroluj: displeje čelem, čitelná čeština, konzistence tváří).

## Krok 4 — Proof scéna 🛑

Vyrenderuj **JEDNU** dialogovou scénu přes `scripts/omni-render.py --only <scene>` (~$0,65/5 s). Uživatel posoudí **český lip-sync + konzistenci tváří**. Teprve po OK renderuj zbytek. **STOP.**

## Krok 5 — Render + Audio QA + trim

```bash
python3 {baseDir}/scripts/omni-render.py --brief video-brief.json --all      # zbývající scény (existující přeskočí)
python3 {baseDir}/scripts/trim-clips.py --brief video-brief.json            # ořez mrtvých pauz (přikyvování)
```
- Content-policy blok u scény → fallbacky v `references/omni-engine.md` (dvojzáběr → img2v ze snímku).
- **Audio QA (POVINNÉ):** transcript porovnej deterministicky s `scene.line.text`. Řez je povolen jen pro `cut_fixable` (všechna očekávaná slova existují, navíc je opakování/extra úsek). `missing_words`, záměna, prázdná nebo nesrozumitelná řeč jsou hard block; ukaž diff a bez nového souhlasu nic nerenderuj. Detail v `references/omni-engine.md`.
- **Kontrola sekvence:** framy přes hranice střihů (konec scény N + začátek N+1) — držené/opakované záběry a hrubé střihy se poznají jen v návaznosti.

## Krok 6 — Finishing → final.mp4

Detailní recepty: `{baseDir}/references/finishing-hyperframes.md`. Pořadí:

1. **HyperFrames projekt** (`npx hyperframes init hf --resolution portrait`), vendoruj Poppins (latin + latin-ext), zkopíruj ořezané klipy do `hf/assets/clips/`.
2. **Concat dialogové stopy** ořezaných klipů → `_base.mp4`; premix případných `_sfx` (tap/interface tóny na eventy) do `_base`.
3. **🛑 Dialogue gate + časování titulků z FINÁLNÍHO videa (POVINNÝ POSLEDNÍ KROK):** `scripts/build-finishing.py --brief video-brief.json --base _base.mp4` použije svůj stávající jediný Whisper přepis zároveň pro dialogue QA i pro přesné titulky. Nevzniká druhý transcript request; při shodném media SHA-256 znovu použije uložený transcript bez provider callu. `--refresh-transcript` vynutí nový placený přepis a smí se použít jen po novém explicitním schválení nákladu. U `briefVersion: 2` nevygeneruje `hf/index.html`, dokud každá mluvená scéna nemá `pass`; raw přepis a report uloží do `logs/`. NIKDY nečasuj z per-scene klipů. Po každém střihu spusť finishing znovu — změněný media hash cache automaticky zneplatní.
4. `npx hyperframes lint` (0 errorů) → `npm run render` (silent). **Ověř, že vznikl NOVÝ render** (jinak mux vezme starý).
5. **Hudba + mux:** `scripts/heygen-music.py` (jeden HeyGen podklad) → `scripts/mux-final.py --video <NOVÝ hf render, absolutní cesta> --dialog _base.mp4 --music <track> --cta <start end-cardu> --fadeout 4.5` (gradace intro→build→vrchol na CTA, ducking, delší fade-out). ⚠️ Absolutní cesta k renderu (pozor na `hf/hf/...`).
6. Proof framy + poslech → **STOP — finál**. Ověř mtime final.mp4 (aktuální!), pošli absolutní cestu + otevři.

## Failure handling

- `FAL_KEY` chybí → blokuj (bez něj nejde generovat).
- `HEYGEN_API_KEY` chybí → **NEblokuj**: upozorni uživatele *„HeyGen klíč není nastavený — video vznikne bez hudby (jen dialog + zvukové efekty). Klíč doplníte v nastavení Control Center.“* a pokračuj; mux udělej bez hudební stopy.
- **Content policy** (`content_policy_violation`) → NIKDY „identical face“ formulace; dvojzáběr místo detailu; poslední záchrana img2v ze snímku už vyrenderované scény. Detail `references/omni-engine.md`.
- Omni opakuje/natahuje repliku → scéna je moc dlouhá vs. text: zkrať duration (~1 s na 2–3 slova) nebo rozděl.
- Dialogue QA `missing_words` / `substitution_or_order_error` / `no_speech` / `unexpected_speech` / `unreadable` → hard block. Nabídni zkrácení nebo rozdělení repliky; rerender pouze vadné scény až po novém dry-run + souhlasu.
- Dialogue QA `cut_fixable` → navrhni přesný řez podle timestampů, proveď jej až po schválení a QA zopakuj; finishing vyžaduje výsledný `pass`.
- Titulek přes obličej → sniž pozici, NIKDY nerenderuj finál s textem přes tvář.
- Displej ve scéně zrcadlově/rozbitě → přegeneruj keyframe (SCREEN ACCURACY klauzule do promptu).

## Reference

- `{baseDir}/references/concept-families.md` — rodiny konceptů: stealth / UGC talking-head / mini-příběh + výběr rodiny
- `{baseDir}/references/stealth-concepts.md` — „neviditelný prodej“: 10 stealth principů, role Autorita/Skeptik, setting presety, mapování na scény
- `{baseDir}/references/omni-engine.md` — Omni endpoints, character lock, 5s pravidlo, content-policy
- `{baseDir}/references/seedance-vo.md` — Seedance + český voiceover (ponechaná cesta)
- `{baseDir}/references/finishing-hyperframes.md` — titulky/flash/punch/hudba/mux
- `{baseDir}/references/storyboard-a-keyframy.md` — storyboard před utrácením, keyframy, kontakt sheet
- `{baseDir}/references/brief-schema.md` — video-brief.json (vč. `subtitles.lines`, `_sfx`)
- `{baseDir}/references/concept-families.md` — rodiny konceptů (stealth / UGC / mini-příběh / akční skill-download)
- `{baseDir}/scripts/build-finishing.py` — generátor HF finishingu, časování z FINÁLNÍHO videa

## Návaznost

- **Před:** brand/product DNA; mockupy produktu (reálné UI do obrazovek)
- **Sourozenci:** `animated-video-generator` (AI stylizace), `html-video-generator` (motion-design bez video modelů)
- **Po:** final.mp4 → Meta Ads / TikTok / YouTube
