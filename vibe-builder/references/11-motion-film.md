# Videoscroll (tier 3) — MotionSite s generovaným filmem

Načti JEN když klient potvrdil videoscroll. Pálí FAL kredity klienta —
každý krok s cenou má STOP.

## Co to je

Skutečné video řízené rolováním: scroll přetáčí film snímek po snímku.
Dvě velikosti prvku (klient volí s cenami v ruce):

- **Motion Site - Video** („Krátké scrollovací video v úvodní (hero)
  sekci.") — standard **1 klip × 10 s = žádný šev**; zbytek stránky
  scénický/klasický. Nejspolehlivější a nejlevnější video úroveň.
- **Motion Site - Video Story** („Scrollovací video s kompletním příběhem
  vaší značky.") — standard **2 klipy × 10 s = ~20s film, 1 šev**; delší
  příběh na přání po kapitolách. Film odvypráví příběh a POD NÍM pokračuje
  normální stránka s obsahovými sekcemi.

## Engine a ceník (FAL — klientův FAL_KEY)

**Video engine: FAL `bytedance/seedance-2.0/image-to-video`.** Nativně umí
start + end frame (`image_url` + `end_image_url`) — přesně řetězový kontrakt
níže. Tohle je specifikace vstupu, ne povolení volat FAL napřímo:

| Parametr | Povinná hodnota |
|---|---|
| `prompt` | cesta od startu k cíli, jeden kamerový vektor |
| `image_url` | reálný poslední snímek předchozího klipu |
| `end_image_url` | další schválený keyframe |
| `resolution` | `720p` (1080p jen na výslovné přání) |
| `duration` | `10` nebo kratší celá kapitola |
| `aspect_ratio` | `16:9` |
| `generate_audio` | `false` — videoscroll je němý |

🛑 Generaci předej pouze přiřazenému video helperu, který před ostrým během
ukáže `--dry-run` a strojově vynutí schválený kumulativní `--max-usd`. Když
helper oba přepínače nemá, **nic negeneruj** a řekni, že chybí bezpečná
rozpočtová brzda. Přímé `fal_client`, ruční HTTP a vlastní inline skript jsou
zakázané. Teprve kompatibilní helper dostane parametry výše po kroku 2
(odhad → strop → souhlas klienta).

**Délka klipu = délka KAPITOLY, max 10 s** (engine umí 4–15 s po celých
sekundách). Zákon lokace platí dál: jeden klip = jedna lokace + jedno
světlo — kapitola s jinou lokací je VŽDY nový klip, i kdyby se do 10 s
vešla. Standardy úrovní: Video = 1×10 s (nula švů), Story = 2×10 s
(1 šev); vícelokační příběh = klip per kapitola (např. 7+7+6 s).
**Anti-střih prompt POVINNĚ v každém klipu:** „single continuous shot,
one unbroken take, no cuts, no scene change, no editing" — Seedance 2.0
umí multi-shot střihy a na delších generacích k nim tíhne; prompt je
vodítko, ne zámek, proto **preflight prvního klipu je povinný** (intra-clip
SSIM křivka: kolaps pod lokální medián = střih → klip zamítni a rozděl
kapitolu na 2×5 s — 5 s je fallback, ne default). 15 s v produkci zákaz.
Stejná pravidla platí pro **Omni** (CZ text v obraze; limit 10 s/generace
= přesně náš strop).

**Kvalita: výchozí 720p STANDARD tier.** Drafty na `fast` variantě
(levnější, stejné schopnosti), finál standard, 1080p jen na výslovné přání.

| Engine / tier | $/s | 10s klip | Video (1×10 s) | Video Story (2×10 s) |
|---|---|---|---|---|
| Seedance 2.0 · 720p fast (draft) | ~$0,24 | ~$2,4 | ~$2,4 | ~$4,8 |
| **Seedance 2.0 · 720p standard (výchozí)** | ~$0,30 | ~$3,0 | ~$3,0 | ~$6,1 |
| Seedance 2.0 · 1080p standard (na přání) | ~$0,68 | ~$6,8 | ~$6,8 | ~$13,6 |
| Omni (Gemini Omni Flash) · 720p token-based | ~$0,13 | ~$1,3 | ~$1,3 (1×10 s) | ~$2,6 (2×10 s) |

**Omni pozn.:** engine `google/gemini-omni-flash/image-to-video`
(token-based ≈ $0,13/s 720p, délka 3–10 s, aspect jen 16:9 / 9:16). Používá se
JEN pro český text/řeč v obraze. **Neumí end frame** → řetěz pouze přes
start-pin (reálný poslední snímek jako `image_url`); dojezd kapitoly řídí
přesná CESTA v promptu a kontroluje se okem. Audio generuje vždy — při
concatu zahoď (`-an`). Detailní know-how (character lock, multiscéna,
střihová skladba) ve skillu video-generator → references/omni-engine.md.

Do odhadu pro klienta VŽDY rezerva 1,5× na regenerace (krok 2 níže).
Ceny se hýbou — před odhadem ověř aktuální sazbu na fal.ai.

## Postup (brzdy jsou součást postupu, ne volitelné)

1. **Storyboard** — N kapitol, JEDEN kamerový vektor na celý film (pojmenuj
   větou: „kamera jen padá", „kamera jen letí vpřed"). Jeden klip = jeden
   směr kamery, jedna lokace, jeden stav světla — když se cokoli z toho mění,
   je to další klip. Prompt klipu popisuje CESTU od startu k cíli („pokračuje
   stejný sestup, míjí…"), nikdy stav („záběr na…"). Audit zdarma: žádný klip
   nesmí obsahovat současně slovo dovnitř i ven; klip bez směru = model si
   směr vymyslí.
   **Pohyb musí být AKCENTOVANÝ, ne naznačený.** První a poslední snímek
   klipu musí vypadat jako dva různé záběry (jiná velikost subjektu, jiné
   rámování) — nesmělý pomalý push-in čtenář vnímá jako statickou fotku
   a scrollovací film ztrácí smysl. Do promptu piš dráhu kamery výslovně
   a měřitelně („kamera urazí polovinu místnosti", „produkt naroste
   z 20 % na 70 % výšky záběru") — slova jako „slowly", „subtle", „gentle
   zoom" v promptu klipu NEPOUŽÍVEJ. Kontrola zdarma po vygenerování:
   SSIM prvního vs. posledního snímku klipu — nad ~0,55 je pohyb moc
   slabý → přegeneruj s výraznějším vektorem (+ oční test: kdyby první
   a poslední snímek byly dvě fotky vedle sebe, řekl bys „jiný záběr"?).
2. **Odhad ceny → STOP.** Počet klipů × cena za generaci (zjisti aktuální
   FAL ceník) × rezerva 1,5× na regenerace. Klient odsouhlasí **částku jako
   strop**, ne jen princip. Do stropu se počítají i regenerace — když ho
   přegenerování překročí, zastav se a řekni si o navýšení. Souhlas platí pro
   tenhle film, nepřenáší se na další úkol. Viz SKILL.md → „Peníze klienta".
3. **Keyframy řetězeně** — snímek N+1 se generuje s N jako referencí
   (dědí svět), viz 07-images.md řetězení.
   **🛑 FYZICKÝ PRODUKT ve filmu = povinná kontrola věrnosti:** každý
   keyframe polož VEDLE packshotu a srovnej PROPORCE (šířka vs. výška!),
   orientaci, pozici panelů/prvků a barvy — generátory produkt rády
   „zeštíhlí" nebo překlopí (reálný incident: čistička širší než vyšší
   vygenerovaná jako vysoká věž). Keyframe s nevěrným produktem se NIKDY
   nepouští do klipů — oprav prompt (rozměry slovně: „wider than tall,
   54×51 cm panel") a regeneruj. U klipů s produktem preferuj
   **`bytedance/seedance-2.0/reference-to-video`** a pošli packshot mezi
   referencemi — věrnost pak drží i v pohybu, ne jen na keyframech.
   **Studiové produktové momenty (exploded view, rotace, detail):** start
   z reálného packshotu drží ČELNÍ pohled, ale hloubku a boky si model
   VYMÝŠLÍ (reálný incident: štíhlá čistička ztloustla na skříň) —
   jediná fotka na 3D věrnost nestačí. Posílej **více reálných úhlů**
   přes reference-to-video (front + bok + celek); po vygenerování polož
   snímky vedle reálných fotek a srovnej hloubku/geometrii. Když produkt
   dál deformuje → generovaný produktový záběr NEPOUŽÍVEJ a řeš moment
   reálnými fotkami (Ken Burns / vrstvy / parallax) — věrnost produktu
   má přednost před efektem.
4. **Klipy SEKVENČNĚ, oba konce pinnuté.** Start klipu N = doslovný poslední
   snímek klipu N−1 vytažený ffmpegem (`ffmpeg -sseof -0.05 -i clipN.mp4
   -update 1 -q:v 1 last.png`) — NIKDY keyframe. Konec = další keyframe.
   Nikdy negeneruj klipy paralelně. **Preflight:** první junction ověř, než
   zaplatíš zbytek — když engine start pin ignoruje (přegeneruje si ho),
   řetězit nejde → jeden nepřerušený záběr ≤ 15 s a řekni to klientovi.
5. **Rozlišení: VÝCHOZÍ 720p standard tier** (drafty fast). Nikdy
   negeneruj 480p (rozmazané na full-bleed desktopu). **1080p jen na
   výslovné přání klienta** — příplatková kvalita: při objednávce 1080p
   se řetěz nejdřív ověří na 720p a přerenderují se jen schválené prompty. Po extrakci
   drž zásadu „šířka zdroje ≈ šířka canvasu"; payload krotí ředění na
   12 snímků/s + WebP (obojí STANDARD, viz krok 7) + případně mobilní sada.
   **Audio vždy OFF** (ztrojnásobuje účet; videoscroll je němý).
6. **Kontroly před stavbou stránky:**
   - Junction: `ffmpeg -i A-last.png -i B-first.png -lavfi ssim -f null -`
     → ≥ 0,88 OK; 0,80–0,88 posuď v pohybu; strukturální rozdíl (jiný
     horizont, jiný grade) = regeneruj s „Continue the exact same shot,
     identical framing, identical colour grade."
   - Kontinuita UVNITŘ klipů: seams sedí konstrukčně, střih utíká doprostřed
     klipu. Vzorkuj průběžně; posuzuj lokální tvar křivky, ne absolutní
     hodnotu (rychlá plynulá jízda skóruje nízko a je v pořádku; kolaps hluboko
     pod lokální medián = střih; ~1,0 = zamrzlá kamera = mrtvá scroll zóna).
   - Crossfade přes špatný švů je zakázaný — scrub dovolí zaparkovat přesně
     na něm.
7. **Sestřih + extrakce:** concat (zahoď duplicitní junction snímek na
   klipech 2+), `-fps_mode vfr` (jinak zamrzlé zóny). Extrahuj **12 snímků/s**
   (`fps=12, scale=1280:-2, -q:v 4`) — 20s film ≈ 240 snímků. Pro
   SCRUB je 12/s nerozeznatelných od 24/s (playhead se lerpuje, nejde
   o přehrávání) a poloviční počet = poloviční stahování i paměť.
   **Formát na webu = WebP STANDARD** (~35 % menší než JPEG, rychlý
   decode; AVIF NE — pomalý decode drhne při skoku playheadu). ffmpeg
   v kontejneru nemusí mít libwebp (reálný incident) → konvertuj JPEGy
   Pillow (v kontejneru je jistá):
   ```python
   from PIL import Image
   import glob, os
   for f in sorted(glob.glob("public/film/*.jpg")):
       Image.open(f).save(f[:-4] + ".webp", "WEBP", quality=80, method=4)
       os.remove(f)
   ```
   Engine pak fetchuje `.webp`. Ořízni hlavu filmu po první snímek, který
   už je uvnitř pohybu, a aktualizuj FRAME_COUNT.
8. **Paměťový rozpočet enginu (POVINNÝ — reálný incident: Chrome renderer
   crash „kód 11" = OOM na všech filmových stránkách):** dekódovaný snímek
   1280×720 = ~3,7 MB RAM; 500 snímků držených najednou = ~2 GB → Chrome
   proces zabije (Safari jen cuká — uvolňuje agresivněji, proto pád vidíš
   jen v Chrome). Pravidla:
   - **Bitmap okno v sekundách, ne snímcích:** ±1,5 s filmu kolem playheadu
     (při 12 fps = ±18 snímků ≈ 135 MB strop). Okno škáluj s fps — nikdy
     absolutní čísla zkopírovaná z jiné stránky.
   - **Mezi-snímkový blend POVINNÝ při 12 fps:** kresli floor snímek a přes
     něj ceil snímek s `globalAlpha = frac` (desetinná část playheadu) —
     bez blendu zoom/nájezd kamery při pomalém scrollu viditelně „cvaká"
     po snímcích (reálný incident); s blendem je 12 fps plynulých jako 24.
   - **Blob-only pipeline — NIKDY nekresli `HTMLImageElement`.** Snímky
     stahuj `fetch → Blob` (komprimované bajty, ~16 MB je nic) a
     materializuj VÝHRADNĚ přes `createImageBitmap(blob, {resizeWidth})`.
     `drawImage(HTMLImageElement)` jde přes Chromeovu interní decoded-image
     cache (discardable memory, na macOS se drží dlouho) — přesně ta při
     reverzním scrollu roste, dokud renderer nespadne. Žádné `new Image()`
     v enginu.
   - **Zavírej i in-flight bitmapy:** `createImageBitmap` promise, která
     doběhne pro snímek už mimo okno (nebo po unmountu/teardownu), musí
     výsledek okamžitě `close()` — jinak GPU zdroj visí do GC (doložený
     Chromium leak vzor).
   - **Teardown mimo viewport:** IntersectionObserver na driveru; když
     scéna opustí okolí viewportu, zavři VŠECHNY bitmapy. Na unmount navíc
     `canvas.width = 0` (uvolní GPU backing store). Resize canvasu jen při
     reálné změně rozměrů (guard) — každé přiřazení width/height realokuje
     backing.
   - **Blend jen při dojezdu** (|target − playhead| < 1 snímek) — při
     rychlém scrollu blend zdvojuje decode i draw a není vidět.
   - **Prioritní stahování kolem playheadu:** vedle sekvenční pumpy měj
     `ensureBlobs(center)` — pár fetchů navíc pro okno kolem aktuální
     pozice, které skáčou frontu. Bez toho rychlý scroll do nenačtené
     zóny čeká na sekvenční pumpu a „film se nepřehraje / chybí snímky"
     (reálný incident na čerstvém načtení).
   - **Druhá a další scrub scéna (exploded view apod.) startuje stahování
     až u viewportu** (IntersectionObserver, rootMargin ~120 %) — jinak
     na startu soupeří s filmem a hero se „nenačítá / seká".
   - **Soak test před nasazením:** Playwright 5× celá stránka rychle dolů
     a nahoru → `page.on("crash")` prázdné; ručně Chrome Task Manager
     (Shift+Esc, sloupce Memory + GPU memory) — po 20 cyklech se musí
     footprint vracet k baseline. Bez testu stránku nenasazuj.
9. **Scrub engine na stránce:** canvas + předextrahované JPEG (nikdy
   `<video currentTime>` — seek stutter). Dekóduj mimo hlavní vlákno
   (`createImageBitmap`) v posuvném okně kolem playheadu (~2 s dopředu,
   ~1,3 s dozadu; bitmapy mimo okno `close()`); lerpuj index snímku
   (`current += (target-current)*0.14`); DPR strop 1.0 a šířka zdroje ≈
   šířka canvasu (upscale vypadá pixelovaně — neřeš vyšším DPR). Mobil:
   crop guard (letterbox, když by ořez > ~22 % kompozice); pravý 9:16 film
   jen na přání (≈ 2× cena). Fallback poster + `nearestFrame()` — chybějící
   snímek nikdy nesmí zobrazit prázdný canvas.
10. **Chrome a beat texty nad filmem — Čitelnost z 10-motion-web.md platí
   dvojnásob:** header bílý text + scrim (film jde od přepalu po tmu během
   jednoho scrollu); beat texty na radiálním scrimu; adaptivní přepínání
   `.on-light` podle vzorkované luminance horního pruhu. Každá kapitola
   filmu má beat s nadpisem — film bez sdělení je spořič obrazovky.
   **Placement beatů VARIUJE — stejná pozice u všech beatů je šablona.**
   Kotvy rytmu jsou ověřené a zůstávají: hero beat bere placement z chrome
   rollu (nikdy z kanonického příkladu) a **finále = velký centrovaný
   nadpis + CTA, který zůstává stát** (obálka out=2). Slabé místo je
   STŘED filmu: střední beaty nesmí být jen malé boční popisky. Střídej
   strany (levý blok · pravý blok) a **1× uprostřed filmu dej velký
   centrovaný statement (škála h1/h2, krátká věta) jako dramatický beat
   rytmu** — velký centr tedy není vyhrazený jen finále. Vzor placementů
   (např. „hero dle rollu → P → velký centr → L → finále centr + CTA")
   zapiš do webDNA.md (## Chrome) a slaď s kompozicí záběrů: text vždy
   na klidnější polovině obrazu.
   **Choreografie beatu je TIME-BASED, nikdy scrubovaná:** scrubuje FILM,
   text ne. Progress filmu jen PŘEPÍNÁ stavy beatu (enter/peak/out prahy);
   tween mezi stavy běží na čase s brandEase — u velkých statementů
   po slovech nebo po řádcích z enginu (animace po písmenech je zakázaná,
   viz 10-motion-web.md). Text navázaný přímo na scrub se při každém
   pohybu kolečka rozpadá a skládá a nejde číst.
   **Chrome nad filmem je ROZHRANÍ, ne scénografie.** Logo, navigace, tlačítko
   menu a CTA v hlavičce se řídí rozpočtem rozhraní z 10-motion-web.md
   (pod 300 ms, `:active` stisk, hover jen za `@media (hover: hover)`),
   i když plují nad filmovou scénou. Nenech se strhnout tempem filmu —
   menu, které se otevírá 600 ms, protože „to ladí s filmem", je vada.
   **Film NENAHRAZUJE vrstvu Text v pohybu:** obsahové sekce pod filmem
   drží plnou vrstvu z 10-motion-web.md (words/linesMask/scrubText/
   countUp dle podpisu) — „film hero + statický zbytek" je přesně vzor,
   kterým vznikla statická dema. Motion budget filmu se týká kreditů,
   ne choreografie zbytku stránky.
11. **Seam handoff:** vzorkuj barvu spodního okraje posledního snímku →
    následující sekce začíná přesně touhle barvou; film → obsah bez
    viditelné linky.
12. **Účtenka:** na konci vypiš — počet generací, draft/master, celkem
    kreditů/Kč. Bez účtenky build nekončí.

## Text ve filmu

**Výchozí a silně preferované: film BEZ jakéhokoli textu v obraze.**
Všechna sdělení nesou HTML beaty nad filmem — jsou ostrá v každém
rozlišení, zdarma editovatelná, čitelná pro vyhledávače a nikdy se
„nerozmažou". Do promptů vždy „no text, no logos".

- Generativní video modely českou diakritiku v obraze poškozují —
  NIKDY nespoléhej na text vygenerovaný uvnitř záběru.
- **Klient výslovně trvá na českém textu přímo ve videu** (nápis, cedule,
  packaging s claimem) → řeš přes **Omni pipeline** (český video engine),
  ne přes prompt Seedance. Řekni klientovi, že jde o samostatný krok
  s vlastní cenou.
- Audio OFF platí i tady — videoscroll je němý.

## Rozpočtová pravidla

- Draft tier vždy před masterem; regenerace jen zamítnutých klipů
- Delší film = víc klipů, nikdy delší klipy (8s klip cestuje moc daleko →
  model střihne uprostřed)
- Jeden film může pohánět víc směrů stránky — footage je náklad, re-skin
  stránky je zdarma
- Job ID ukládej na disk hned po vystavení (selhání downloadu po zaplaceném
  renderu = jinak platíš dvakrát); CDN stahuj s browser User-Agentem
