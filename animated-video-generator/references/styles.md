# Virální animované styly (všechny přes Seedance 2.0)

Klient si v Kroku 1 vybere **jeden** styl. Seedance 2.0 zvládá všechny tyhle stylizované vzhledy — rozdíl je v **prompt deskriptorech** (a v storyboard stillu, který jde do reference-to-video). Styl se „zapeče" už do storyboardu (Krok 2), Seedance ho pak rozanimuje.

## Jak klient vybírá

Ukaž tabulku níž + (volitelně) 1 ukázkový still na hero styl (Pixar). Klient řekne styl → ten se promítne do storyboard promptu i Seedance promptu. **Jeden styl na celé video** (konzistence).

| # | Styl | Vibe (1 věta) | Pro koho / kdy |
|---|---|---|---|
| 1 | **Pixar / 3D Disney** ⭐ | Teplé, barevné, výrazné postavy s cartoon proporcemi, měkké světlo | Hrdinský příběh podnikatele — nejvirálnější, default |
| 2 | **Ghibli / anime** | Měkká akvarelová pozadí, nostalgické, kouzelné, jemné postavy | Emotivní, snový, lidský tón |
| 3 | **Claymation (plastelína)** | Ručně dělaný clay povrch, otisky prstů, hravé, Aardman charm | Hravá, odlehčená značka s charakterem |
| 4 | **LEGO / kostičky** | Svět z plastových kostiček, lesklé, hravé | Metafora „postav si svůj tým z dílků" |
| 5 | **Plyšák / felt** | Měkké plyšové/plstěné postavy, šité detaily, roztomilé | Přátelský, nízkoprahový, cute tón |
| 6 | **2D flat / motion graphics** | Plochá vektorová ilustrace, čisté tvary, bold barvy | Korporátní-clean, maximální brand kontrola |

## Seedance prompt deskriptory per styl

Vlož **na začátek** Seedance promptu (i do storyboard promptu). Zbytek promptu = popis scény/akce (viz `seedance.md`). Vždy přidej anti-text + (u postav) fictional-clause kvůli moderaci.

**1) Pixar / 3D Disney**
> `A high-quality 3D animated film still in the style of a modern Pixar / Disney feature — soft cinematic lighting, warm color palette, expressive characters with friendly cartoon proportions, subsurface skin, shallow depth of field, polished render. Fictional cartoon character.`

**2) Ghibli / anime**
> `A hand-painted Studio Ghibli style anime frame — soft watercolor backgrounds, warm gentle lighting, clean cel-shaded characters, painterly clouds, nostalgic magical atmosphere, 2D anime aesthetic. Fictional anime character.`

**3) Claymation (plastelína)**
> `A stop-motion claymation scene (Aardman style) — characters and props sculpted from modeling clay with visible fingerprints and matte clay texture, handcrafted miniature set, soft studio lighting, tactile organic look. Fictional clay character.`

**4) LEGO / kostičky**
> `A LEGO brick-built animated scene — everything constructed from glossy plastic interlocking bricks and minifigure characters, studs visible, bright saturated colors, miniature brick world, playful toy-photography lighting. Fictional minifigure character.`

**5) Plyšák / felt**
> `A soft plush / needle-felt animated scene — characters made of stitched fabric, felt and yarn with visible seams and fuzzy texture, cozy handmade miniature set, warm soft lighting, adorable tactile look. Fictional plush character.`

**6) 2D flat / motion graphics**
> `A clean 2D flat-design animated frame — bold vector shapes, flat illustration, limited brand color palette, smooth gradients, minimal geometric characters, crisp motion-graphics aesthetic, no photorealism.`

## Společná pravidla pro všechny styly

- **Žádný text v obraze** — přidej do promptu `no text, no captions, no letters, no UI text` (text řešíme HyperFrames vrstvou). Výstupy na obrazovkách/materiálech nech jako reálné vizuály (fotky, plochy, grafy), ne nápisy.
- **Konzistence postavy a prostředí** napříč 3 klipy — stejná postava (popis + reference still), stejný styl, stejné prostředí. Storyboard postavu „zafixuje", Seedance z reference drží.
- **Brandové barvy** zmiň v promptu jen jemně (paleta), ať styl zůstane čistý — silný branding až v overlay vrstvě.
- **Face-light kompozice** u postav (postava z dálky / zezadu / 3/4, ne extrémní detail obličeje) — sníží šanci na Seedance face-moderation 422 (viz `seedance.md`).
- **16:9, 720p** default (rychlejší/levnější), upscale řeš až když je finál schválený.
