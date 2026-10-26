# Foundation — typografie, barvy, spacing, motion

Základní design principy. Agent je aplikuje napříč všemi výstupy bez ohledu
na zvolenou theme nebo composition.

## Typografie

### Stack lock-in
- **UI text / body:** čitelný text face dle světa — Inter je JEDNA
  z možností, ne povinný default (střídej: Hanken Grotesk, Instrument
  Sans, Schibsted Grotesk, DM Sans, Geist…). Stejný body font na každém
  webu = konvergence, přesně to nechceme.
- **Čísla / metriky:** mono nebo text face s `font-variant-numeric: tabular-nums`
- **Display / hero:** dle webDNA.md — font s charakterem, který patří ke
  commitnutému světu; web s vlastním světem má vlastní display face
  (neutrální sans jako display jen pro tier 0 dashboard/aplikace).

### Výběr display fontu (web) — POŘADÍ PŘEDNOSTI

1. **Klient má fonty v DESIGN.md → platí ty.** Font je identita klienta,
   výběrový mechanismus se přeskakuje. Dvě výjimky: (a) font láme
   čitelnost → řekni to nahlas a navrhni alternativu — nikdy tichá
   výměna; (b) **experiment režim** (`identity_source:
   experiment` ve webDNA.md — klient dodal nový směr/inspiraci) → DESIGN.md
   vizuálně neřídí NIC včetně fontů; font dává Web DNA / koncept.
2. **Bez klientských fontů → font přiřazuje Web DNA.** `concept-seed.py`
   vrací `display_font` z poolu směru (deterministicky ze slugu — různí
   klienti dostávají různé fonty; NIKDY neber „oblíbený" font z hlavy,
   přesně tak vzniká konvergence na jeden řez). Self-host přes `next/font`,
   subsets `["latin","latin-ext"]` — když font latin-ext nemá, vezmi další
   z `font_pool`.
- Serif display na hero vzpřímený jako základ; kurzíva žije na akcentových
  slovech (viz Typografická hra — tahy se střídají).
- Grotesk/geometrický: výrazné váhy a šířky, škálový kontrast dělá práci.

### Ohranost fontů — řeší ROZMANITOST, ne blacklist
Žádný font není zakázaný (rozhodnutí 2026-08-05 — dřívější banned list
zrušen). AI klišé nevzniká z konkrétního řezu, ale z konvergence: stejný
default na každém webu. Proto fonty přiděluje Web DNA pool per svět
(deterministicky ze slugu) a nikdy se nebere „oblíbený" font z hlavy —
klidně i trendy řezy (Fraunces, Playfair, Space Grotesk…), když sedí světu.

### Hierarchie
- **Hero h1:** 48-96 px (mobile-first scaling)
- **Section h2:** 32-48 px
- **Body:** 16-18 px (ne 14 — moc malé)
- **Caption:** 13-14 px
- **KPI numbers:** 36-60 px, tabular-nums, font-medium nebo font-semibold

### Pravidla
- **1–2 rodiny na stránku** (display + body pár dle webDNA; žádný
  celoplošný stejný default napříč weby)
- **2 weight max** v body kontextu (regular + medium NEBO regular + semibold)
- **Display weights** (bold, black) — jen na hero a section h2
- **Letter-spacing:** -0.02em na velkém typu (32 px+), 0 na body
- **Line-height:** 1.1-1.2 na display, 1.5-1.6 na body
- **⚠️ ČESKÁ DIAKRITIKA na display typu:** háčky a kroužek na verzálkách
  (Ř, Ý, Ž, Ů) přesahují em box a těsné řádkování je sráží s řádkem nad.
  **Pravidlo NENÍ plošné číslo — je to POVINNÁ KONTROLA po vytvoření:**
  nastav řádkování těsné podle metrik fontu (typicky 1.02–1.12; fonty
  s verzálkami přes celý em box jako Anton potřebují víc, ~1.15–1.2)
  a pak na screenshotu OVĚŘ víceřádkový nadpis s Ř/Ž/Ů — háček nesmí
  kolidovat s řádkem nad, ale mezi řádky nesmí vzniknout vzduchoprázdno
  (přestřelené 1.3+ na display vypadá stejně špatně jako kolize).
  Anglický vzor „leading 0.8–0.95" v češtině neplatí.

## Barvy

### Stack
- **Tailwind v4** + CSS custom properties
- **OKLCH** preferován (lepší perceptual uniformita) nad HSL/RGB
- **Tokens v `tailwind.config.ts`** odvozené z theme (z `03-themes-and-dials.md`)

### Pravidlo „Palette discipline"
- **1 primary** (brand color z brandDNA)
- **1 secondary** (komplementární, méně dominantní)
- **1 accent** (pro CTA, highlights — high chroma)
- **Neutral scale** (50, 100, 200, ..., 950) — pro text a backgrounds
- **Žádné rainbow** — víc než 3 distinct hues na jedné stránce = slop

### Banned color patterns
- ❌ Purple gradient (`from-purple-500 to-blue-500`) — #1 AI cliché
- ❌ Rainbow mesh blobs — chatGPT cover art vibe
- ❌ Pink-to-orange „creator" defaults
- ❌ Glassmorphism (backdrop-blur) bez konkrétního důvodu

### Gradient jako nástroj (používej AKTIVNĚ — málo gradientu = plochá stránka)
- **Brandový gradient na plochách**: CTA, akcentní pásy, aktivní stavy,
  velké pozadí sekce (jedním směrem, ne duha)
- **Radiální atmosféry / glow**: světelné pole za klíčovým objektem nebo
  nadpisem (nízká opacita, z palety světa)
- **Gradient linky a okraje**: podtrhy, dividery, borders karet
- **Gradient scrimy** pod textem na obrazech
- Low-chroma tonal přechody ploch, soft vignettes
- **Gradient text v nadpisech** — povolený tah (brandový gradient z palety
  světa na klíčovém slově; střídej s ostatními tahy, ne mechanicky všude)
- ❌ Dál zakázané: purple→blue AI klišé, duhové mesh bloby

**⚠️ Banding na tmavých gradientech (vypadá jako komprese):** jemné tmavé
gradienty na 8-bit displeji dělají viditelné schody a flekaté kontury —
klient to čte jako „rozbitý/komprimovaný web". Dvě povinná opatření, kdykoli
svět stojí na tmavých plochách s glow vrstvami:
1. **Filmové zrno přes plochu** (SVG feTurbulence noise, dlaždice ~200 px,
   `opacity` 0.03–0.05, **normální míchání — NIKDY `mix-blend-mode: overlay`**,
   overlay na téměř černé nedělá nic a banding zůstane).
2. **Radiálním glow vrstvám dej mezistopy** (např. plná → 40 % síly na
   ~40 % → transparent), ať nemají ostré mach-band kontury; drž alphy nízko
   (≤ 0.06 na tmavé).

### Eyebrow — nástroj, ne reflex

Malý uppercase štítek nad nadpisem NENÍ zakázaný — zakázaná je jeho
bezmyšlenkovitá verze. Rozdíl:

- ✅ **Product/brand tag** — název produktu či řady nad hero titulkem
  (např. „MOTION SITES™"); styl dle brandu (uppercase, tracking 0.2–0.3em,
  akcentní barva nebo brand gradient)
- ✅ **Wayfinding na dlouhé stránce** — čtenář ví, v jaké kapitole je
  („Úroveň 3", „Krok 2 z 6", název sekce v dlouhém průvodci)
- ✅ **Číslované/kapitolové značení** v editoriálních směrech
- ❌ **Generický štítek bez informace** („SLUŽBY", „O NÁS", „FEATURES")
  — neříká nic, co neřekne nadpis pod ním
- ❌ **Mechanicky nad každým nadpisem** — razítko na 80 % sekcí je šablona,
  ne navigace

Brána hlídá jen slop varianty (generický text, plošné razítko) — účelový
eyebrow prochází.

### Maskované přechody sekcí (moderní tvar, ne samé rovné hrany)
Sekce nemusí končit vodorovnou čarou — používej **clip-path / mask
přechody**: oblouk, vlna, diagonála, elipsa (tvar ber ze světa: vlna pro
vodu, oblouk pro sklep, diagonála pro techniku). Střídmě: 1–3 maskované
přechody na stránku, zbytek rovný — všechno zvlněné je stejná šablona
jako všechno rovné.

## Spacing

### Princip — víc whitespace než default AI
- **VISUAL_DENSITY = 4/10** (airy, ne packed)
- **SPACING_GENEROSITY = 8/10** (much breathing room)
- Pravidlo: „o ~20 % víc whitespace mezi sekcemi než default Bootstrap/Tailwind"

### Konkrétní values (Tailwind)
- **Section vertical padding:** `py-20 md:py-32` (žádné `py-12` na hlavní sekce)
- **Container max-width:** `max-w-7xl` pro většinu, `max-w-5xl` pro content-heavy
- **Card padding:** `p-6 md:p-8` (ne `p-4` — moc compressed)
- **Gap mezi cards:** `gap-6 md:gap-8`
- **Body copy ne na viewport edge:** `px-6 md:px-12 lg:px-16`

### Section rhythm
- Alternuj density: **dense → calm → dense** (ne všechny sekce stejné)
- Hero = calm (lots of negative space)
- Features = dense (kompaktní cards)
- Testimonials = calm (1-2 quotes, breathing room)
- CTA = dense (visual weight pro conversion)

## Motion — tiery (pohyb je výchozí stav webu, klid je výchozí stav nástroje)

Kolik se stránka hýbe, řídí **MOTION_TIER** (commitnutý ve webDNA.md,
defaulty per typ v 03-themes-and-dials.md):

| Tier | Co | Kde |
|---|---|---|
| **0 klidný** | žádné animace; jen okamžité hover/focus stavy | dashboard, aplikace (default) |
| **1 oživení** | scroll reveals, SplitText hero, countery, hover se substancí | podlaha KAŽDÉHO webu; volba pro dashboard |
| **2 vrstvená scéna** | scroll řídí děj — pinnuté scény, vrstvy s hloubkou | **Motion Site - Image jen po explicitní volbě; nikdy default** |
| **3 videoscroll** | generovaný film řízený rolováním | jen na výslovnou objednávku (kredity) |

Engine = **GSAP** (ScrollTrigger, ScrollSmoother, SplitText, CustomEase —
vše zdarma). Doktrína a slovník: `10-motion-web.md` (tier 1+2),
`11-motion-film.md` (tier 3). API pravda: `gsap/`.

### Pravidla platná napříč tiery

- **Signature ease z webDNA.md** — jedna vlastní easing křivka napříč
  stránkou. Default easy všude = AI tell.
- **`gsap.matchMedia()`** pro breakpointy + `prefers-reduced-motion`
  (reduced = plný obsah staticky, ne prázdná stránka).
- **Durations škála** (ne náhodná čísla): hover 150–200 ms · reveals
  400–700 ms · page transition 300–400 ms. Scrub scény nemají duration —
  řídí je scroll.
- **Choreografie, ne šablona:** stejný entrance na každé sekci není motion,
  je to razítko.

### Banned motion (všechny tiery)

- Text bez scrimu přes fotku/vrstvy; efekt bez nadpisu (viz Čitelnost níže)
- Scroll-jacking bez úniku (pin bez obsahu = vězení)
- Auto-playing video se zvukem; parallax na mobilech
- Bouncy spring na všem; particle efekty bez opory ve světě
- Marquee na sdělení (jen dekorace/opakování)

## Čitelnost — nesnížitelná (přebíjí každý efekt)

1. **Efekt bez sdělení je zakázaný.** Každá scéna/beat/sekce nese nadpis
   (h2/h3) nebo klíčovou větu.
2. **Text na obrazech vždy na podkladu** (scrim/plate) — kontrast 4,5:1
   body / 3:1 velký text proti nejsvětlejšímu i nejtmavšímu místu podkladu.
3. **Čitelné v klidu** — návštěvník může zastavit kdekoli; hero sdělení
   viditelné už při scroll 0.
4. **Text se nehýbe při čtení** — arrival max ~600 ms, pak klid.
5. **Reading order = DOM order.**

## Editoriální podlaha (výchozí stav pro web — nesnížitelné klientským vstupem)

- **Display font s charakterem, nikdy systémový** — nejbližší nainstalovaný
  font je selhání, ne fallback; self-host face podle světa
- **Škálový kontrast:** na stránce jeden prvek řádově větší než zbytek;
  sekce bez kontrastu měřítka nemá rytmus
- Míra řádku 65–75 znaků · display max 6rem · tracking −0,02 až −0,03 em
- **Elevace deklarovaná jednou** — border NEBO stín, nikdy oboje
- Sekce pod foldem: vertikální přítomnost (`min-height` blízko viewportu),
  arrival se staggerem ~90 ms, jeden vrchol na scroll
- **Primární CTA = nejsebevědomější prvek stránky**, ne textový odkaz

## Ikony (POVINNÉ pro web — rozstřelují text; kreativita vítaná)

Moderní ikonový systém patří do každého webu — text bez vizuálních kotev
je zeď. Ikony NEJSOU podezřelé; podezřelý je jen líný vzorec (níže).

- **Zdroj:** Lucide (v Next.js `lucide-react`, v single-file inline SVG
  s Lucide paths). Konzistentní stroke (1.5–2 px), barva z palety.
- **Důraz:** ikony jsou plnohodnotný stavební prvek stránky, ne dekorace
  na zbyt — u faktických sekcí (parametry, režimy, vrstvy, kroky) je
  strukturní pás s ikonami PRVNÍ volba vizuálu (viz Rytmus obrazu).
  Styl vždy moderní: linkové, jednotný stroke, akcentní barva světa —
  žádné emoji, žádné barevné ilustrační ikonky.
- **Základní použití:** odrážky (místo puntíku), kroky procesu, kontaktní
  řádky, FAQ markery, parametrové tabulky, štítky výhod.
- **Kreativní použití (klidně odvážně):** OBŘÍ outline ikona jako grafický
  motiv na pozadí sekce (nízká opacita, ořízlá hranou) · ikona v akcentním
  kruhu/tvaru jako vizuální kotva odstavce · DrawSVG dokreslení ikony při
  scrollu · ikona vetkaná do nadpisu · pás ikon jako dekorativní marquee ·
  různé velikosti v rytmu (jedna dominantní, ostatní malé).
- **Jediný skutečný zákaz — líný vzorec:** uniformní grid stejných kartiček
  „malá šedá ikona + nadpis + dva řádky" jako struktura stránky = kategoriální
  AI default. Chceš-li feature grid s ikonami, PŘETVOŘ ho: různé velikosti,
  asymetrie, jedna karta vybočuje, ikony velké a barevné. A žádné emoji
  místo ikon.

## Rytmus obrazu (POVINNÝ — proti textové zdi)

**Maximálně JEDNA čistě textová sekce na celou stránku.** Každá další
sekce nese vizuál: fotku (řetězenou ze světa webu), obrazový split 50/50,
full-bleed pás, vrstvenou scénu, výraznou grafiku (DrawSVG diagram, plán)
— NEBO moderní ikonový systém. Strukturní ikonový pás (položky s linkovými
ikonami jednotného stroke v akcentní barvě — filtry, režimy, parametry,
kroky) se počítá jako plnohodnotný vizuál: krásně rozbíjí strukturu
stránky a u faktických sekcí je to první volba. Samotná ikonka v odrážce
se NEPOČÍTÁ — vizuál musí nést plochu nebo rytmus celé sekce. Stránka
s 5+ sekcemi bez jediného obrázku mimo hero je vada, ne minimalismus.

## Typografická hra (proti „mega čisté" sterilitě)

Správná škála a čisté řádkování nestačí. Hra má DVĚ úrovně s různou
frekvencí:

**1) BARVA v nadpisech — průběžně.** Barevné klíčové slovo (plná akcentní
barva z palety, nebo brandový gradient text) používej napříč stránkou,
klidně ve většině nadpisů — to drží fonty živé, ne sterilní. Akcent žije
i v číslech a linkách.

**2) DEKORATIVNÍ tahy — STŘÍDAT, ne razítkovat.** Akcentové slovo smí mít
nadpis klidně ve většině sekcí, ale STEJNÝ tah maximálně na každém druhém
nadpisu — jeden tah mechanicky všude (např. kurzíva na každém klíčovém
slově) je průhledné razítko a zařízení přestane fungovat (reálný nález).
webDNA.md commitne 2–3 tahy světa a ty se po stránce střídají. Tahy:

- **Barevné slovo** — klíčové slovo nadpisu v akcentní barvě palety,
  NEBO **gradient text** (brandový gradient z palety světa — povolený
  a vítaný tah; zakázané zůstává jen purple→blue AI klišé a duha)
- **Kontrastní řez / rodina na slově** — kurzíva, tučné, jedno slovo
  v druhé rodině (grotesk nadpis + serif/italic slovo, nebo naopak;
  mono na číslech)
- **Outline slovo** — `-webkit-text-stroke` obrys bez výplně vedle plných slov
- **DrawSVG tah** — ručně kreslené podtržení/kroužek kolem slova
- **Přeškrtnutí + náhrada** — škrtnuté slovo a vedle správné (rétorický tah)

Pravidla hry: **max 1–2 tahy na nadpis** (zvýraznit všechno = nezvýraznit
nic) · čitelnost vždy vítězí (tah nikdy nesmí rozbít čtení nadpisu) ·
žádné poodskočení/rotace/baseline shift — text stojí rovně (viz zákaz
houpání) · akcentní barva musí žít i mimo CTA — v nadpisech, číslech,
linkách. Stránka, kde je barva jen na tlačítku, je šedá.

## Interaction

### Buttons
- **Primary CTA:** filled, brand color, font-semibold
- **Secondary:** outline nebo ghost, font-medium
- **Destructive:** red-500 fill, jen na delete actions
- **Disabled:** opacity-50, cursor-not-allowed, no hover

### Forms
- **Labels nad inputy** (ne placeholder-only — accessibility)
- **Focus ring:** 2px brand color, `ring-2 ring-offset-2`
- **Validation:** inline pod input (ne tooltip)
- **Submit button:** loading state s spinnerem

### Cards
- **Padding:** `p-6` minimum
- **Border:** subtle (`border border-slate-200 dark:border-slate-800`) NEBO shadow (`shadow-sm`), ne oba
- **Radius:** `rounded-lg` (8 px) nebo `rounded-xl` (12 px), konzistentně per page
- **Hover:** subtle elevation increase, ne color flash

## Responsive

### Breakpoints (Tailwind)
- **Mobile-first** vždy
- `sm:` 640 px — tablet portrait
- `md:` 768 px — tablet landscape
- `lg:` 1024 px — desktop small
- `xl:` 1280 px — desktop large
- `2xl:` 1536 px — wide screens

### Pravidla
- **Hero font-size:** `text-4xl md:text-6xl lg:text-7xl`
- **Section padding:** `py-16 md:py-24 lg:py-32`
- **Grid:** `grid-cols-1 md:grid-cols-2 lg:grid-cols-3` (default)
- **Container padding:** `px-6 md:px-12 lg:px-16`

## UX writing

### Pravidla v češtině
- **Vykání** (klient = user koncového produktu)
- **Konkrétní, ne abstraktní:** „Ušetříte 4 hodiny týdně" ne „Zvýšíte produktivitu"
- **Aktivní hlas:** „Stáhněte si přehled" ne „Přehled je možné stáhnout"
- **Stručné CTA:** „Začít zdarma" / „Stáhnout" / „Domluvit hovor"
  (ne „Klikněte sem pro zahájení vašeho..."v)

### Banned copy patterns (v češtině)
- „revoluce v X"
- „transformace vašeho byznysu"
- „posunout byznys na další úroveň"
- „inovativní řešení"
- „next-gen platforma"
- „seamless integrace"
- „powerful nástroj"
- „comprehensive solution"

### Tone podle context
- **B2B SaaS / dashboardy:** neutrální, technicky důvěryhodné
- **Landing page service biz:** přátelské, výsledkově orientované
- **Premium brand:** restrained, sofistikované, méně exclamace
- **E-commerce:** akční, jasné value prop
