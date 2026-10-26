# Storyboard + keyframy — kontrola nákladů PŘED renderem

**Princip: schválit směr na obrázku je levné (centy), přerenderovat špatné video drahé (dolary).** Proto VŽDY: storyboard → STOP → keyframy → STOP → proof scéna → STOP → teprve full render.

## Ceník pro rozhodování (orientačně)

| Krok | Nástroj | Cena |
|---|---|---|
| Master storyboard (1 PNG) | gpt-image-2/edit | ~$0,20–0,35 |
| Keyframe / portrét (1 ks) | gpt-image-2/edit | ~$0,10 |
| Proof scéna 5 s | omni | ~$0,65 |
| Full render 30 s (6 scén) | omni | ~$3,90 |
| HyperFrames render + mux | lokálně | zdarma |

## Master storyboard (Krok 2)

Jeden A3 landscape PNG (2400×1600): character ref panel, floor plan, lighting/paleta, storyboard strip se všemi scénami v poměru cílového videa. Generuj **skillním skriptem `{baseDir}/scripts/generate-storyboard.py`** (sebestačný, součást skillu — NEodkazovat na externí `viral-video-ad-generator`, ten se z fleetu odstraňuje). Skript má **české nadpisy natvrdo** + jazykový přepínač (`brief.language`: cs default / en / es). Vstup = `_storyboard-brief.json` (adapter s poli `cuts` / `character` / `shared_choices` / `scene_continuity` — sestav z `video-brief.json`). Reference: brand-board + produktové fotky. **Gpt-image-2/edit vyžaduje ≥1 referenční obrázek** — bez brand referencí selže.

```bash
python3 {baseDir}/scripts/generate-storyboard.py --brief _storyboard-brief.json --output 01-master-storyboard.png
```

**🛑 Jazyk storyboardu = ČESKY (skript to hlídá, ale VŽDY Read-checkni výstup).** Úplně VŠECHEN text na desce — nadpisy sekcí, popisky pohledů, popisky záběrů, poznámky, audio cues, paleta — musí být česky (deska je pro klienta ke schválení). Skript vynucuje tyto přesné české nadpisy:

| Anglicky (NEpoužívat) | Česky (použít na desce) |
|---|---|
| CHARACTER + HERO PROPS REFERENCE | POSTAVY + KLÍČOVÉ REKVIZITY |
| FRONT VIEW / SIDE PROFILE / BACK VIEW / FACIAL CLOSE-UP / RELAXED POSE | ČELNÍ POHLED / Z PROFILU / ZEZADU / DETAIL OBLIČEJE / UVOLNĚNÁ PÓZA |
| HERO PROPS (MUST MATCH FINAL PRODUCT) | KLÍČOVÉ REKVIZITY (MUSÍ SEDĚT S FINÁLNÍM PRODUKTEM) |
| ENVIRONMENT / FLOOR PLAN | PROSTŘEDÍ / PŮDORYS |
| LIGHTING REFERENCES + COLOR PALETTE | SVĚTLO + BAREVNÁ PALETA |
| COLOR PALETTE | BAREVNÁ PALETA |
| STORYBOARD (N CUTS) | STORYBOARD (N ZÁBĚRŮ) |
| NOTES / AUDIO & CINEMATOGRAPHY | POZNÁMKY / ZVUK & KAMERA |
| MOOD / KEYWORDS | NÁLADA / KLÍČOVÁ SLOVA |
| AUDIO CUES (SFX ONLY) | ZVUK (JEN SFX) |
| CINEMATOGRAPHY NOTES | KAMERA / POZNÁMKY |

Technické zkratky záběrů (WIDE, MEDIUM, 85 mm, STATIC, SLOW-MO, HANDHELD, PUSH-IN, END-CARD) jsou filmový standard a smí zůstat; **všechno ostatní česky**. Po vygenerování storyboardu **zkontroluj Read**, že na desce není žádný anglický nadpis — když je, přegeneruj (u EN/ES trhu je naopak deska v daném jazyce).

**🛑 ŽÁDNÁ HUDBA ve storyboardu ani ve scénách.** Audio cues na desce = pouze zvukové efekty a ambience (ruch ulice, kavárna, whoosh na střih…). Hudba se NIKDY nespecifikuje per scéna — je to VŽDY jeden průběžný podklad přidaný až v postu (mux-final.py). Zmínka hudby ve storyboardu/scéně = chyba, přegeneruj.

## Master storyboard = jediné schválení; breakdown do generací je interní

- **Master storyboard pokrývá CELOU délku videa**: 1 panel = 1 záběr (~3 s). Uživatel schvaluje TENHLE artefakt (záběry, repliky, pořadí) — jediný storyboard STOP.
- **Breakdown do ≤10s generací** (seskupení záběrů do multiscénních promptů, viz omni-engine.md „Nativní multiscéna“) dělej **interně, bez dalšího STOPu** — je to technické seskupení už schválených záběrů.
- **Výjimka:** když breakdown vynutí změnu proti schválenému storyboardu (rozdělená/zkrácená replika, sloučený záběr, policy reframe) → ukaž mini-diff ke schválení.
- Reálná pojistka před full renderem = **proof generace** (Krok 4).

## Skladba záběrů (už ve storyboardu!)

**Sousední scény musí mít jiný úhel/velikost záběru** — dva podobné framingy za sebou = jump cut na tvrdém střihu (viz omni-engine.md). Do storyboardu piš `shot_type` per scéna a střídej: wide two-shot → medium close-up A → close-up B → insert telefon → medium shot → end-card. Zkontroluj to na storyboard PNG PŘED schválením — oprava tady je zdarma, po renderu drahá.

## 🛑 Realismus postav (POVINNÁ klauzule ve VŠECH promptech s lidmi — storyboard i keyframy i scény)

AI výstupy mají tendenci k „vyžehleným“, nepřirozeně hladkým, symetrickým tvářím — **okamžitě prozradí AI původ** a sníží důvěryhodnost reklamy. Do KAŽDÉHO promptu, kde je člověk (master storyboard, kanonické portréty, keyframy scén, omni scénové prompty), povinně přidej:

> *photorealistic candid film still shot on a digital cinema camera, natural realistic skin with visible pores, fine lines and subtle imperfections, unretouched faces with natural asymmetry, natural flyaway hairs and stray strands, real ambient lighting, no airbrushing, no beauty retouch, no plastic/waxy skin, must look like a real photograph of a real person, must NOT look AI-generated, CGI or overly polished*

Platí i pro **master storyboard** — do jeho promptu dej „all character thumbnails and cut frames must show realistic, natural, non-airbrushed faces, not AI-smooth“.

Po vygenerování VŽDY zkontroluj (storyboard i keyframy): kůže má texturu (ne porcelán/vosk), vlasy nejsou „helma“, tváře nejsou přehnaně souměrné a drží charakter referencí. Vyžehlené → **přegenerovat**, nepouštět dál.

## Kanonické portréty postav (Krok 3a)

Pro každou postavu **jeden čistý čelní studiový headshot** (`refs/refA.png`, …):
- Generuj přes `scripts/generate-keyframe.py` s referencí výřezu ze storyboardu (drží kontinuitu vzhledu).
- Prompt: „clean sharp front-facing studio-style headshot… preserve his look from the reference“ (NE „identical face“ — content policy, viz omni-engine.md).
- Tyto portréty se zamykají do každé ref2v scény → konzistence tváří napříč celým videem.

## Keyframy scén (Krok 3b)

- **9:16 = 720×1280** (16:9 = 1280×720) — poměr keyframu určuje poměr videa.
- img2v scény (obrazovky, end-card) keyframe POTŘEBUJÍ; ref2v dialogové scény ho mají jen pro vizuální kontrolu ve storyboardu/kontakt sheetu.
- **Obrazovky zařízení:** vlož REÁLNÉ produktové mockupy jako referenci (image_urls) + SCREEN ACCURACY klauzuli: obrazovka čelem ke kameře, vzpřímená, čitelná, nikdy zrcadlená/obrácená/deformovaná, reálné proporce.
- **Česká diakritika v UI/end-cardu:** gpt-image-2 ji UMÍ — piš plné české texty s diakritikou přímo do promptu (přesné znění, ať se netrefuje volně).
- **End-card:** brand pozadí + brand gradient + logo (referencí logo.png) + přesný claim + CTA.

## Zdroj barev (gradient titulků, punch, end-card, paleta storyboardu)

Pořadí: **1) `brand/DESIGN.md`** (přesné HEX) → **2) extrakce z `logo.png`** → 3) `brand-board.png`. Extrakce z loga (PIL): projdi pixely s alpha >180, vezmi nejsvětlejší a nejtmavší „brand-barevný“ pixel + nejsytější střed → gradient světlá → tmavá. Výsledek zapiš do briefu (`subtitles.gradient`) — jeden zdroj pravdy pro celý finishing. Gradient na textu musí zůstat čitelný (světlý/neonový konec nahoře, tmavý dole; nikdy celotmavý).

## Kontakt sheet + STOP

Slep keyframy do jednoho kontakt sheetu (PIL grid, popisky scén), otevři, projdi s uživatelem:
- tváře konzistentní? displeje čelem a česky? end-card správně? kompozice sedí na storyboard?
- Teprve po schválení → Krok 4 (proof scéna).
