# Production recipes — univerzální principy

Tvrdě naučené vzory z reálné výroby. Platí pro libovolné animované video. Čti vždy — ušetří iterace.

## Příběh & koncept

- **Odvoď z DNA + cíle**, nepředpokládej zápletku. Vyber story-arc dle typu (viz `storyboard.md`).
- **Jeden jasný message** na video. U sales/ad drž **POV diváka** (jeho situace → jeho výsledek), ne výčet funkcí.
- **CTA = akce, kterou chceš** (aktivace/získání produktu), ne hard-sell. Vykání, čistá čeština, žádné anglické patvary (LUNCH×launch).

## Seedance (animace)

- **Nikdy text do animace** — komolí (hlavně CZ). Výstupy na obrazovkách = reálné vizuály; text až overlay.
- **Face moderation 422** u detailů obličeje → face-light storyboard (postava z dálky/zezadu/3-4) + „fictional cartoon character" klauzule.
- **Reference HTTPS URL** (FAL CDN), ne data URL. `generate_audio:False`.
- **Zacyklená/duplicitní scéna** je běžný artefakt → počítej se střihem ~2 s (viz `assembly.md`).
- Když klient chce „úplně jiné" — změň celý setting i postavu, ne jen detail.

## Audio / VO

- **VO sync podle screenshotů scén** — nejdřív zjisti co se kdy děje, pak posaď beaty. Klíčové slovo na klíčový vizuál.
- **Beaty, ne jeden blok** — přesné posazení + přirozené pauzy. Uniformní `atempo` zrychlení **zní divně** — radši přegeneruj beat s jiným tempem.
- **Akční SFX nasaď přesně na akci** (zvuk až když naskočí příslušný vizuál, ne dřív).
- **Win moment potřebuje výrazný zvuk** — slabý/technický zvuk na pointu nestačí (např. sales „prodáno" = slyšitelná kasa + mince, zvýrazněné).
- **Fade hudby dřív** (od ~4 s před koncem, dlouhý) — krátký fade zní uťatě.
- **SFX hravé, ne technické** — charakterní popy/whooshe/sparkly na beaty nad hudbou.

## Overlay (text)

- **Per-písmeno kinetika na velké texty** (elastic + squash&stretch). Slovní fade = málo, vypadá „placatě/AI".
- **Mezery v znakových spanech přes nbsp** (`String.fromCharCode(160)`) — jinak `inline-block` znaky sbalí mezery → text bez mezer.
- **`immediateRender:false`** na tweens s viditelným „from" stavem (burst ring apod.) — jinak zbloudilý prvek hned při mountu comp.
- **Diakritika = latin-ext subset** Manrope v každé comp — bez něj zmizí háčkovaná písmena (ř ž č ě ů).
- **Text na obrazovce drž krátký a svižný** — dlouhý odepisovaný text působí dlouze.
- **Zakryj gibberish** — overlay karty/popisky posaď přes komolené obrazovky.
- **Outro fade** (obraz i zvuk do černé) — bez něj je konec „useknutý".

## Příklad z první výroby (ai-marketer)

Reklamní video „AI Marketér": Pixar styl, 3 Seedance klipy (problém → tým vyrábí kampaň → výsledek), český VO (Enceladus) po ~8 beatech, HeyGen hudba + hravé SFX (klávesnice na psaní, kasa na „Vyprodáno"), HyperFrames overlay (headline, role chipy, psací karta, channel chipy, razítko VYPRODÁNO, CTA + logo), outro fade. ~42 s, 16:9. Slouží jako vzorová instance pipeline — ne povinná šablona.

## Workspace / lifecycle

- **Skill se vyvíjí v `../skills/`** (dev workspace), kreativní výstupy v `documents/videos/<slug>/`.
- **Verzi bumpuj jen na explicitní pokyn** („finalizujeme/posílám"). Iterace = beze změny verze.
- **`--dry-run` + STOP před každým FAL spendem** (Seedance ~$3.6/klip). HeyGen audio zdarma.
