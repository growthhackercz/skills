# Motion pro web — tier 1 (oživení) + tier 2 (vrstvená scéna)

Načti pro každý web/landing/funnel. API pravda ke GSAP je ve `gsap/`
(react, scrolltrigger, plugins, core, timeline, performance) — tam sahej,
když píšeš kód. Tento soubor je doktrína: co, kdy a proč.

## Stack a setup

```bash
npm install --legacy-peer-deps --save-exact gsap@3.15.0 @gsap/react@2.1.2
chmod +x node_modules/next/dist/bin/next 2>/dev/null || true
```

GSAP je od akvizice Webflow **100 % zdarma včetně všech pluginů**
(ScrollTrigger, ScrollSmoother, SplitText, Flip, DrawSVG, Observer,
CustomEase, MotionPath) — vše z veřejného `gsap` npm balíku, žádný token.

Vzory, které platí VŽDY (detail `gsap/react.md`):

- `useGSAP(() => {...}, { scope: containerRef })` — nikdy holý `useEffect`,
  nikdy selektor bez scope
- `contextSafe` pro handlery vytvořené po prvním běhu
- GSAP jen na klientu (`"use client"` komponenty) — nikdy při SSR
- **Zákon pořadí:** pinnuté scény vytvářej PŘED ambientními triggery —
  ScrollTrigger refreshuje v pořadí vytvoření; obráceně = efekty střílejí
  o tisíce pixelů dřív, tiše
- Smooth scroll = **ScrollSmoother** (nativní integrace, žádné ruční drátování)

## Dva rozpočty pohybu (rozhoduj se podle nich, ne podle chuti)

Na jedné stránce žijí dvě různé věci a **každá má jiný rozpočet pohybu**.
Než napíšeš jakoukoli animaci, zařaď prvek do jednoho z těch dvou světů —
pravidla se pak neberou ze stejné tabulky.

**Scénografie** = hero, sekční nadpisy, obrazy, vrstvené scény, filmy,
velké momenty. Návštěvník je uvidí **jednou nebo dvakrát v životě**. Tady
platí celá naše ambice: bohatý nástup, velké momenty, narativní tempo.
Trvání smí být delší (400–800 ms), protože se pohyb podílí na sdělení.

**Rozhraní** = navigace, mobilní menu, dropdown, jazykový přepínač, FAQ
akordeon, formulářová pole a jejich validace, modal, cookie lišta,
tlačítka, taby, filtry. Tyhle prvky uživatel **použije opakovaně během
jedné návštěvy** a čeká od nich odezvu, ne představení. Tady platí
rozpočet rozhraní: **pod 300 ms, `ease-out`, žádná dekorace navíc.**

Rozhodovací pravidlo: **čím častěji prvek uživatel uvidí nebo použije,
tím kratší a nenápadnější animace.** Prvek ovládaný klávesou (odeslání
formuláře Enterem, zavření modalu Escapem, ⌘K vyhledávání) se
**neanimuje vůbec** — u opakované akce dělá animace zpoždění a rozpojuje
ji od uživatelova záměru.

Tohle rozdělení **nezeslabuje ambici stránky**. Naopak: pohybový rozpočet
se přesouvá tam, kde má dopad, a nepálí se na tom, co člověk odklikne
pětkrát za minutu.

⚠️ Stejná logika řídí i **dashboardy a klientské portály** (tier 0/1
v 03-themes-and-dials.md) — to jsou plochy, které uživatel otevírá denně,
tam je nulová až minimální animace správná odpověď, ne kompromis.

## Motion podpis světa — lib/motion.config.ts (povinné, generované)

Default easing všude je AI tell: každý AI web se hýbe stejně. A příkladová
křivka opsaná z dokumentace je stejný fingerprint jako default. Proto motion
podpis (ease z poolu 8 pojmenovaných křivek, tempo, sloveso vjezdu, jednotka
splitu, stagger origin, 2 velké momenty) **roluje concept-seed.py** a vydá
hotový obsah `lib/motion.config.ts` — ten zapíšeš DOSLOVA (obsahuje lock,
který brána ověřuje přes `--seed-slug`). NIKDY nepiš vlastní inline křivku
ani vlastní DUR — build importuje `brandEase`, `brandEaseInOut`, `DUR`
a `SIGNATURE` z `./motion.config`. Přebít sloveso/jednotku smíš jen s pojmenovaným
důvodem ve webDNA.md; lock v souboru vždy zůstává.

### Křivku vybírá situace, podpis vybírá charakter

Zámek na `brandEase` řeší, aby se všechny naše stránky nehýbaly stejně.
Neřeší, že **různé druhy pohybu chtějí různou rodinu křivky**. Podpis
proto určuje, JAK křivka vypadá uvnitř své rodiny — rodinu určuje situace:

| Situace | Rodina | Poznámka |
|---|---|---|
| Prvek přijíždí nebo odjíždí | **ease-out** | rychlý rozjezd = okamžitá odezva |
| Prvek se přesouvá / mění tvar na obrazovce | **ease-in-out** | přirozený rozjezd i dojezd |
| Hover, změna barvy, stín | **ease** | krátké a nenápadné |
| Konstantní pohyb (marquee, progress, smyčka) | **linear** (`ease: "none"`) | jediná správná volba |
| Výchozí, když si nejsi jistý | **ease-out** | |

`motion.config.ts` proto vydává `brandEase` (příchod/odchod, rodina
ease-out) i `brandEaseInOut` (pohyb po obrazovce) — ber je podle tabulky,
nevymýšlej třetí.

**🛑 `ease-in` na příchodu je zakázaný.** Začíná pomalu, tedy zdrží přesně
ten okamžik, kdy se uživatel dívá nejpozorněji. `ease-out` na 200 ms
působí rychleji než `ease-in` na stejných 200 ms — vnímaná rychlost je
funkce tvaru křivky, ne jen trvání. Totéž platí pro každou křivku
z podpisu, která by měla pomalý rozjezd: v příchodové roli se nepoužije.

**Vestavěné CSS easingy jsou příliš slabé** na cokoli záměrného. Když
`motion.config.ts` z jakéhokoli důvodu nedodá křivku (fallback, chrome
prvek psaný v čistém CSS mimo GSAP), použij tyhle a žádné jiné:

```css
--ease-out:    cubic-bezier(0.23, 1, 0.32, 1);    /* příchod / odchod */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);   /* pohyb po obrazovce */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);    /* šuplík / panel zdola */
```

**Výjimka ze zámku podpisu:** marquee, progress bar a jakákoli nekonečná
smyčka jedou VŽDY `linear` (`ease: "none"`), bez ohledu na `brandEase`.
Brandová křivka na konstantním pohybu způsobí viditelné pulzování na
každém opakování.

## Reduced-motion + breakpointy — jeden mechanismus

`gsap.matchMedia()` s conditions — automatický revert při změně, žádný
ruční úklid (detail `gsap/core.md`):

```ts
const mm = gsap.matchMedia();
mm.add({
  isDesktop: "(min-width: 800px)",
  isMobile: "(max-width: 799px)",
  reduceMotion: "(prefers-reduced-motion: reduce)",
}, (ctx) => {
  const { reduceMotion } = ctx.conditions!;
  if (reduceMotion) return; // žádný posun ani scrub — krátká prolnutí řeš v CSS (viz níž)
  // ... animace
});
```

`prefers-reduced-motion` = **plný obsah, méně pohybu — ne nula animací.**
Nevolnost spouští POHYB a změna pozice, ne prolnutí. Proto:

- **Pryč jde:** posun, parallax, pinnuté a scrubované scény, kurzorové
  efekty, Ken Burns, marquee, smyčky, škálování velkých ploch, splity textu.
- **Zůstává:** krátké prolnutí opacity (~200 ms) tam, kde pomáhá pochopit,
  že se něco změnilo · barevné přechody · zpětná vazba stisku
  (`scale(0.97)` je 3% změna na 160 ms, ta nikoho nerozhoupe).

Výchozí stav každého animovaného prvku musí být čitelný — animuj `.from()`
do viditelného, nikdy neschovávej obsah přes CSS `opacity: 0` bez JS
fallbacku. Když skript selže, stránka musí být kompletní.

**Obsluž i sousední preference**, pokud stránka používá průhledné
a prosklené plochy:

```css
@media (prefers-reduced-transparency: reduce) {
  .glass { background: var(--surface-solid); backdrop-filter: none; }
}
@media (prefers-contrast: more) {
  .glass { background: var(--surface-solid); border: 1px solid var(--border-strong); }
}
```

## ČITELNOST — nesnížitelná (přebíjí každý efekt)

Motion stránky nejčastěji umírají na to, že efekt sežere sdělení. Pravidla:

1. **Efekt bez sdělení je zakázaný.** Každá scéna/beat/sekce nese nadpis
   (h2/h3) nebo klíčovou větu. „Jen hezký pohyb" neexistuje — když scéna
   nemá co říct, nemá na stránce co dělat.
2. **Text na obrazech vždy na podkladu.** Scrim (radiální/lineární gradient
   pod textem) nebo plate — kontrast 4,5:1 body / 3:1 velký text, měřeno
   proti nejsvětlejšímu I nejtmavšímu místu podkladu. Bílá, ne krémová
   (krémová na světlém podkladu vypadá špinavě).
   **Scrim NIKDY nekončí hranou elementu** — dělá se jako přesahující
   pseudo-element (`inset: -55% -45%`, `z-index: -1`) a gradient dojede
   do PLNÉ průhlednosti nejpozději na ~75 % plochy. Viditelný obdélník
   nebo ovál kolem textu = vada (reálný incident); okraje se musí úplně
   jemně ztratit. Nikdy nedávej gradient větší než element (ellipse 135 %
   apod.) — na hraně boxu se tvrdě usekne.
3. **Čitelné v klidu.** Návštěvník může zastavit kdekoli — text musí jít
   přečíst při zastaveném scrollu, ne jen v letu. Hero sdělení viditelné
   už při scroll 0 (žádné „skrolujte, ono to přijde").
4. **Text se nehýbe při čtení.** Arrival max ~600 ms, pak klid. Žádný text
   trvale v pohybu (marquee jen na dekorativní/opakující se obsah, nikdy
   na sdělení).
5. **Reading order = DOM order.** Vizuální choreografie nesmí přeházet
   logické pořadí čtení (screen readery, tabování).

## DOM kontrakt (povinný — brána na něm stojí)

Vygenerovaný kód deklaruje strukturu, aby ji brána mohla kontrolovat bez
hádání:

- **Každá `<section>` nese `data-anchor="<jméno-anchoru>"`** (z 02-composition,
  dle webDNA.md outline) — brána hlídá variety (3× stejný za sebou = P1)
- **Každé textové sdělení nad scénou/filmem = beat**: element s
  `className` obsahujícím `beat` NEBO atributem `data-beat` — a **musí
  obsahovat nadpis** (h2–h6). Brána: beat bez nadpisu = P1.
- Jiné pojmenování = kontrakt porušen a kontroly tiše nefungují. Proto je
  kontrakt POVINNÝ, ne konvence.

## TIER 1 — oživení (podlaha každého webu)

### Text v pohybu (POVINNÁ vrstva — texty nesmí jen „nafádovat")

Blokový fade-up celých odstavců NENÍ textová animace — je to přesun
kontejneru. Vrstvu implementuje **engine `lib/text-motion.ts`** — zkopíruj
šablonu `{baseDir}/references/text-motion.template.ts` do
`<slug>/src/lib/text-motion.ts`. Engine drží mechaniku (split, mask,
cleanup, aria, reduced-motion, výkon); VZHLED bere ze `SIGNATURE`
v motion.config.ts — dvě stránky se stejným enginem se hýbou jinak,
protože mají jiný podpis. Nepiš SplitText choreografie od nuly; volej
helpery a dolaď parametry.

🛑 **Runtime marker `data-motion-ready`.** Engine ho nastavuje na animovaný
prvek (`dataset.motionReady = "1"`) až v okamžiku, kdy se choreografie
opravdu rozběhla — a při `prefers-reduced-motion` hned, protože finální stav
je dosažený bez tweenu. Obě brány na něm stojí: `design-gate.js` ověří, že ho
zapisuje **jen** kanonický `lib/text-motion.ts`, `visual-gate.mjs` ho čte
v prohlížeči jako důkaz, že motion vrstva žije. Proto:

- **nikdy** ho nepiš do markupu (potvrzoval by pohyb, který neběží),
- **nikdy** ho nenastavuj z komponenty ani jiného souboru,
- když engine upravuješ, marker musí zůstat — bez něj brána projekt zablokuje.

**DOM kontrakt vrstvy (brána na něm stojí):** každý animovaný nadpis nese
`data-motion="words|lines|scrub"` — h1 bez `data-motion` je P1.
**`chars` je zakázaná hodnota** (viz zákaz animace po písmenech níže).
Split bez staggeru je P1 (přítomnost tokenu není choreografie).

- **🛑 ZÁKAZ animace po písmenech.** `data-motion="chars"` ani `heroChars()`
  se nepoužívají — nikde, ani v hero. Platí i pro varianty typu
  „po slabikách“ a „typewriter“. Tři důvody, každý sám o sobě stačí:
  1. **Text, který uživatel čte, se nesmí hýbat kvůli stylu.** Nadpis je
     obsah, ne dekorace. Rozsypaná písmena skládající se během čtení jsou
     přesně tenhle přestupek.
  2. **Česká diakritika se láme** — háčky a čárky u samostatně animovaných
     glyfů poskakují a ořezávají se o mask wrappery.
  3. **Během náběhu je text nečitelný** a per-znakový stagger na dlouhém
     českém nadpisu blokuje čitelnost násobně déle než per-slovní.

  **Jediná výjimka: číslice.** U čísla nese změna jednotlivé číslice
  informaci (hodnota se mění), u slova ne. Číselníky proto dál dělej
  přes `countUp()` s `tabular-nums` — per-číslicový přechod je tam
  správně, ne v rozporu s tímhle zákazem.
- **Hero h1: `words` nebo `linesMask()`** — nadpis nastupuje po slovech nebo
  po řádcích, podle podpisu světa (sloveso × jednotka × origin × ease).
  **ZÁKAZ houpání**: žádné rotace (rotateX/Y/Z), žádný overshoot bounce,
  žádné kývání — vjezdy textu jsou důstojné (posun, maska, wipe, blur, váha).
- **KAŽDÝ sekční h2: `linesMask()`** — mask reveal řádků je „drahý" pocit;
  standard, ne bonus.
- **Zvýrazněné slovo: mikro-timing** — engine řeší přes `accent` selektor
  (`SIGNATURE.accentDelay`); autorský detail zdarma.
- **1 scrub-textový moment na stránku: `scrubText()`** — slova se
  rozsvěcují rolováním. TVRDÁ MEZ: mění se JEN opacity/barva, nikdy
  pozice, a plný stav nastane do ~60 % scroll rozsahu (světlo nesmí
  honit čtenáře).
- **Countery: `countUp()`** u všech velkých čísel (tabular-nums povinné).
- Odstavce: fade-per-paragraph se staggerem (ne celý blok najednou).

**📱 Mobil: vrstva je POVINNÁ i na mobilu** — words/lines jsou čistý
transform + opacity a jedou i na středním Androidu. Mobil ztrácí HLOUBKU
(parallax, pin scény, kurzorové efekty, distort), nikdy ŘEČ (textovou
choreografii). Helpery volané jen v `isDesktop` větvi = vrstva na mobilu
chybí = stejná statická stránka, jakou řešíme.

⚠️ Výklad čitelnosti: pravidlo „text se nehýbe při čtení" znamená
**po dojezdu klid** — NE „text neanimuj". Příchod textu má být bohatě
choreografovaný; zakázaný je jen trvalý pohyb během čtení. České háčky:
mask wrappery potřebují padding (engine řeší) a line-height ≥ 1.15.

### Zbytek slovníku

- **Section reveal:** `gsap.from(el, { y: 26, opacity: 0, duration: DUR.base,
  ease: brandEase, stagger: 0.06, overwrite: "auto",
  scrollTrigger: { trigger: el, start: "top 82%", once: true } })`
  — pro ne-textové prvky (karty, obrázky, ikony)
- **Hover se substancí:** lift + stín, 150–200 ms — na kartách a CTA,
  VŽDY uvnitř `@media (hover: hover) and (pointer: fine)` (viz Stavy
  ovládacích prvků)
- **Stisk:** `scale(0.97)` na `:active`, 160 ms — na každém tlačítku a odkazu
  ve tvaru tlačítka
- **DrawSVG akcent:** kreslené podtržení/divider tam, kde to svět unese

**Rozpočet trvání pro rozhraní** (scénografie má vlastní, delší — viz Dva
rozpočty pohybu):

| Prvek | Trvání |
|---|---|
| Stisk tlačítka | 100–160 ms |
| Tooltip, malý popover | 125–200 ms |
| Dropdown, select, jazykový přepínač | 150–250 ms |
| Modal, drawer, mobilní menu | 200–500 ms |
| Akordeon (FAQ) | 200–250 ms |
| Scénografie (hero, sekční nadpis, beat) | 400–800 ms (arrival TEXTU drží strop ~600 ms — viz Čitelnost, pravidlo 4) |

**Prvek rozhraní nesmí překročit 300 ms bez pojmenovaného důvodu.**
180ms dropdown působí svižněji než 400ms — a rychlejší spinner dělá dojem
rychlejšího načtení, i když se skutečná doba nezmění.

**Stagger 40–80 ms mezi položkami, a součet je strop.** Stagger × počet
položek nesmí přesáhnout ~400 ms — u osmi karet s 90ms krokem dosedá
poslední karta o 0,7 s později než první, tedy dávno poté, co kolem ní
čtenář prorolloval. Když je položek víc, nezvyšuj celkový čas: použij
`ScrollTrigger.batch` a nech nastupovat jen to, co je právě ve výřezu.
Stagger je dekorace — nikdy nesmí blokovat interakci (odkaz v poslední
kartě musí jít kliknout, i když ještě nedojel).

**Ambice: MotionSite základ NENÍ „reveals všude a dost".** Povinné minimum
na web/landing: **≥ 3 RŮZNÉ motion mechanismy nad rámec reveals** — z toho
**2 velké momenty přiděluje motion podpis** (SIGNATURE roll v concept-seed;
jsou to commitnutá rozhodnutí, ne inspirace). Paleta velkých momentů:

- pin+scrub **vrstvená scéna** · **horizontální pinnutý běh**
- **Flip sdíleného slova**: slovo z hero doletí do sekčního nadpisu
  (`Flip.fit/from` na ScrollTriggeru) — Lusion-grade moment zdarma
- **slovní ruleta** v nadpisu (`wordSwap()` — 2–4 varianty benefitu)
- **kurzorový magnet/odpud na hero obrazu** (quickTo, desktop, jen na obraze
  nebo dekoraci — **nikdy na písmenech nadpisu**; per-znakový efekt je
  zakázaný i v hoveru, viz zákaz animace po písmenech)
- **ScrambleText na metrikách** — jen na **číslech**, ne na slovech (u číslic
  nese změna znaku informaci, viz výjimka v zákazu animace po písmenech);
  CZ-safe abeceda bez diakritiky ve scramble fázi, doběh spolu s countUp
- **nadpis jako maska pro obraz/video** (`background-clip: text` s médiem,
  ne s gradientem; `mix-blend-mode: difference` varianta)
- **kapitolový snap** velké scény (`ScrollTrigger.snap` na beaty)
- **scrub-light čtení** (`scrubText()` — slova se rozsvěcují)
- **rozklad na součástky** (exploded view, JEN fyzický produkt — vrstvy
  a pravidla v 07-images.md; každá součástka = benefit beat)
- **klipový tab indikátor** — zdvoj seznam tabů, kopii nastyluj jako
  aktivní stav (jiné pozadí, jiná barva textu) a ořízni ji klipem tak, aby
  byl vidět jen aktivní tab; při přepnutí animuj `clip-path`. Text i pozadí
  se přebarví dokonale synchronně, protože jde o jeden odhalovaný prvek,
  ne o dvě nezávisle časované barvy — čistě timingem tohohle nikdy nedosáhneš.
- **před/po posuvník** — dva obrazy přes sebe, horní ořízlý
  `clip-path: inset(0 50% 0 0)`, pravý inset řízený tažením. Žádné DOM
  prvky navíc, hardwarově akcelerované. (Sedí na naše před/po sekce.)
- **odhalení druhé vrstvy klipem** — stejnou technikou lze odhalit jiný
  barevný režim, druhou verzi sekce nebo „rentgen“ produktu.
- **maskování prolnutí blurem** — když crossfade dvou stavů drhne a žádný
  easing ani trvání to nespraví, přidej během přechodu `filter: blur(2px)`.
  Bez blur oko vidí dva objekty přes sebe; blur je slepí v jeden vjem
  proměny. Drž pod 20 px. (Použitelné na Flip sdíleného slova a výměny obrazů.)

**Subtilní reveal vrstva je POVINNÝ ZÁKLAD každé stránky.** Fotky,
odstavce, ikonové položky, metriky i CTA nastupují jemně (fade + rise
~24 px se stagger, brand ease, `ScrollTrigger.batch`) — nic se neobjeví
skokem. Jednou nastoupí a STOJÍ. Reálný nález: doktrína dřív tlačila jen
na velké momenty a stránky končily bez jemného základu — působily staticky.

Velké momenty stavíš NAD tuhle vrstvu, ne místo ní: stránka jedoucí JEN
na fade-reveals je pod úrovní produktu, ale stránka BEZ nich je vada.
Klidná sekce (jen reveal, bez velkého momentu) je nádech v rytmu — na
stránce jich smí být víc, ale aspoň 2–3 sekce nesou autorský pohybový
nápad z motion podpisu světa. Blur, mask, clip-path patří do palety,
pokud drží 60 fps a čitelnost.

**Výkonové meze enginu (drží helper, ne dobrá vůle):** words max
~60 glyfů (nad to auto-degradace na words) · `will-change` jen po dobu
tweenu · měř p95 rAF delta.

### Stavy ovládacích prvků — nejlevnější prémiový detail, co existuje

Tlačítko bez stavu stisku působí, jako by rozhraní neposlouchalo. Tohle je
podlaha, ne bonus — platí na každé tlačítko, CTA, kartu s odkazem, taby
i položky filtru.

```css
.button {
  transition: transform 160ms var(--ease-out);
}
.button:active {
  transform: scale(0.97);   /* rozsah 0,95–0,98, nikdy míň */
}

/* Hover se dotýká JEN zařízení, kde hover reálně existuje */
@media (hover: hover) and (pointer: fine) {
  .button:hover { transform: translateY(-2px); box-shadow: …; }
}
```

- **`:active` gating nepotřebuje** — stisk je na dotyku reálný. Gating
  potřebuje `:hover`: dotykové zařízení hover spustí při tapnutí a prvek
  pak zůstane „zvednutý“ — vypadá to jako zaseknuté rozhraní.
- **`scale()` škáluje i potomky** (text, ikonu) — proto stisk čte jako
  fyzické zamáčknutí. To je záměr, ne vada.

**🛑 Nikdy neanimuj z `transform: scale(0)`.** Nic ve skutečném světě
nevzniká z ničeho. Startuj z `scale(0.9)`–`scale(0.97)` v kombinaci
s `opacity: 0`. Platí pro každý příchod: dropdown, modal, kartu, toast.

**Rozbalovací prvky vyjíždějí ze svého spouštěče, ne ze středu.**
Dropdown, jazykový přepínač, popover, tooltip — nastav `transform-origin`
tam, kde je tlačítko, které je otevřelo. Výchozí `center` je pro ně
špatně. **Modal je výjimka** — není ukotvený k žádnému spouštěči,
zůstává centrovaný.

**Odchod je rychlejší než příchod, a jde stejnou cestou, kterou přišel.**
Panel, který přijel zprava, odjíždí doprava, ne dolů. Trvání: pomalu tam,
kde se uživatel rozhoduje, svižně tam, kde odpovídá systém — např.
„podrž pro potvrzení“ plní 2 s `linear`, ale po puštění se vrací
200 ms `ease-out`. Stejné trvání příchodu i odchodu je vada.

**Vstupní animaci prvku, který nepotřebuje GSAP, dělej v CSS** přes
`@starting-style` — netahej kvůli mobilnímu menu celý animační runtime:

```css
.menu {
  opacity: 1; transform: translateY(0);
  transition: opacity 220ms var(--ease-out), transform 220ms var(--ease-out);
  @starting-style { opacity: 0; transform: translateY(-8px); }
}
```

### Přerušitelnost — uživatel scrolluje uprostřed náběhu

Návštěvník nečeká, až animace dojede. Scrolluje dál, vrací se nahoru,
klikne v půlce nástupu. Doktrína to musí ustát:

- **Reveal se přehraje JEDNOU.** `scrollTrigger: { once: true }` (nebo
  `toggleActions: "play none none none"`). Nikdy `"play reverse play reverse"` —
  stránka, která při každém projetí sekce znovu bliká, bojuje se svým
  čtenářem. Jednou nastoupí a STOJÍ.
- **`overwrite: "auto"` na každém tweenu, který může být spuštěn znovu**
  (hover, stavové přepnutí, opakovaný trigger). Bez toho se tweeny
  skládají přes sebe a prvek skáče. GSAP tween přerušený s `overwrite`
  pokračuje z aktuální pozice — nikdy nerestartuj běžící náběh od nuly.
- **Nová animace vždy startuje z AKTUÁLNÍ hodnoty na obrazovce**, ne
  z cílové nebo výchozí. Startovat z logické hodnoty znamená viditelný
  skok v místě přerušení.
- **Kurzorové a ukazovátkové efekty jedou přes `gsap.quickTo`**, nikdy
  přímým zápisem pozice myši do transformu. Přímé navázání na kurzor
  působí uměle, protože nemá setrvačnost; `quickTo` interpoluje a dodá
  pocit hmoty. (Totéž dělá `scrub: 0.9` u pinnutých scén.)
- **Scrubuje jen obraz, ne text** (viz 11-motion-film.md): scroll řídí
  film nebo scénu, textové beaty se přepínají prahy a tween mezi stavy
  běží na ČASE. Text navázaný přímo na scrub se při každém pohybu kolečka
  rozpadá a skládá a nejde přečíst. (Jediná výjimka je `scrubText()` —
  rozsvěcení slov mění POUZE opacity/barvu, nikdy pozici.)

## Klasický hero a klidný web (klientská volba, ne fallback)

Klient smí chtít „normální stránku" — a výsledek musí být stejně prémiový,
jen jinými prostředky (typografie, kompozice, fotografie).

**`hero_mode: classic-image`** — velká lifestyle fotka jako hero (07: scéna
s produktem/životem, NIKDY packshot). Kompozice a placement textu z chrome
rollu — **hero text se NIKDY nezarovnává vpravo** (platí pro každý hero;
pravá strana patří médiu a dechu, brána to blokuje). Text se narodí kineticky (`words` / `linesMask()`), pokud je tier ≥ 1; jemný
Ken Burns na fotce (scale 1.0 → 1.04, 14 s, jednou) je volitelný a nepočítá
se jako „animace", kterou klient odmítl.

**`hero_mode: classic-video`** — smyčkové video na pozadí, klasika (žádný
scrub!): `<video autoPlay muted loop playsInline poster>`, WebM + MP4,
≤ ~5 MB, 10–20 s smyčka bez viditelného střihu, scrim pod textem.
- Zdroj: klientovo video (zdarma, hned) NEBO 1 generovaný klip — za
  kredity, STOP s cenou před generací (stejná brzda jako videoscroll).
- `prefers-reduced-motion` → poster místo videa. Mobil → poster nebo
  lehčí varianta (mobilní data; video nikdy nesmí blokovat LCP).
- TSX recept v 06-patterns.md („Classic Video Hero").

**Klidný web (tier 1)**: reveals + narození textů, žádné pin scény, žádný
scrub. **Statický web (tier 0)**: nic se nehýbe — brána s `--dna` textová
pravidla vypne; hlídej o to přísněji editoriální podlahu (01). Hero režim
řídí jen hero — tělo stránky drží svůj tier z webDNA.md.

## TIER 2 — vrstvená scéna (= Motion Site - Image, první úroveň rodiny; NENÍ default webu)

Scroll řídí děj: obraz složený z vrstev (PNG s průhlednými okraji,
generované řetězeně — viz 07-images.md), sticky jeviště, choreografie psaná
obálkami. Stavíme na ScrollTriggeru (pin + scrub), ne na vlastním rAF.

### Kostra

```tsx
// Scéna: pinnutý stage, vrstvy jako absolutní <img>, scrub timeline
useGSAP(() => {
  const tl = gsap.timeline({
    scrollTrigger: { trigger: stageRef.current, start: "top top",
      end: "+=280%", pin: true, scrub: 0.9 }, // scrub 0.9 ≈ lerp „máslo"
  });
  tl.to(".layer-back",  { yPercent: -8,  scale: 1.06 }, 0)
    .to(".layer-mid",   { yPercent: -18 }, 0)
    .to(".layer-front", { yPercent: -34 }, 0)
    .fromTo(".beat-1",  { autoAlpha: 0, y: 40 }, { autoAlpha: 1, y: 0 }, 0.12)
    .to(".beat-1",      { autoAlpha: 0, y: -30 }, 0.34); // beat má enter/peak/exit
}, { scope: stageRef });
```

### Choreografická pravidla

- **Scéna = obálka enter/peak/exit.** Každý prvek má kdy přijde, kdy vrcholí,
  kdy odejde — pozice v timeline (0–1 progressu scény). Beat (textové
  sdělení) musí mít peak ≥ 12 % progressu, aby šel přečíst; finale beat
  nefaduje (zůstává).
- **Hloubka = rychlost.** Zadní vrstvy se hýbou málo, přední hodně
  (poměr cca 1 : 2 : 4). Plus jemný scale zadní vrstvy pro pocit jízdy.
- **Protiškálování:** prvek uvnitř zoomujícího rodiče, který má zůstat
  opticky stabilní (UI, karty), škáluj inverzně (`scale: 1/parentScale`).
- **Parallax na kurzor** (desktop only, přes matchMedia): posuvy řádu
  jednotek px na pozadí, do ~20 px na popředí. `quickTo` pro plynulost.
- **Okraje vrstev:** pohyb nesmí odhalit šev — vrstvy generuj s přesahem
  (bleed ≥ 6 % na stranách, které se hýbou).
- **Dvě až tři pinnuté/scrubované scény na stránku jsou standard MotionSite
  základu** — hero scéna + minimálně jeden další velký moment v těle
  (horizontální běh, druhá scéna, scrub odhalení). Mezi nimi klidné sekce
  jako nádechy — rytmus, ne opatrnost.
- Za scénou stránka nesmí „zplihnout": sekce drží editoriální podlahu
  (01-foundation.md) A vlastní pohybové nápady — parallax na obrázcích,
  DrawSVG akcenty, marquee běhy. Odvaha se měří dole, ne jen v hero.
- **⚠️ ZÁKAZ pohybu textu do stran:** žádný skew/velocity efekt na písmu
  (text naklánějící se „ze strany na stranu" podle rychlosti scrollu),
  žádné houpání (rotateX, overshoot kývání). Text nastupuje (rise, mask,
  wipe, blur), ale jakmile stojí, UŽ SE NEHÝBE — profesionální kinetika
  je v nástupu, ne v neustálém vlnění.

### Výkon

- Animuj jen `transform` a `opacity` (`autoAlpha`); `will-change` jen na
  pohyblivých vrstvách; žádné layout-thrashing čtení v ticku
- Vrstvy: WebP/PNG, largest ≤ 350 kB, celkem scéna ≤ 2,5 MB
- Měř p95/max rAF delta, ne průměr FPS — cíl max < 50 ms
  (detail `gsap/performance.md`)
- **CSS proměnná na rodiči NIKDY neřídí transform potomků.** Změna
  proměnné na kontejneru přepočítá styly VŠEM potomkům — u seznamu
  s dvaceti kartami je to lavina přepočtů v každém snímku. Zapisuj
  `transform` přímo na ten prvek, který se hýbe.
  ```js
  el.parentNode.style.setProperty('--shift', `${d}px`); // ❌ recalc všem dětem
  el.style.transform = `translateY(${d}px)`;            // ✅ jen tenhle prvek
  ```
- **CSS a WAAPI běží mimo hlavní vlákno, `requestAnimationFrame` ne.**
  Zatímco se stránka načítá, parsuje skripty a dekóduje obrázky, JS
  animace zahazuje snímky — CSS animace jede dál hladce. Praktický důsledek
  pro hero: **nástup hero prvků nepouštěj do dokončení kritického načtení**
  (počkej na `fonts.ready` a dekódovaný hero obraz), nebo ho napiš jako
  čisté CSS / WAAPI. Trhaný hero je nejdražší vada na stránce — je první,
  co člověk uvidí.
  ```js
  el.animate([{ clipPath: 'inset(0 0 100% 0)' }, { clipPath: 'inset(0 0 0 0)' }],
    { duration: 600, fill: 'forwards', easing: 'cubic-bezier(0.77, 0, 0.175, 1)' });
  ```
- **`clip-path` je výjimka potvrzená měřením** — je hardwarově akcelerovaný
  a levnější než animace `height`; maskové odhalení tedy dělej klipem, ne
  výškou. (`height` toleruj jedině u akordeonu, kde transformní ekvivalent
  neexistuje.)
- **`filter: blur()` je paint operace, ne kompozice.** Používej ho účelně,
  drž pod **20 px** a počítej s tím, že v Safari je výrazně dražší než
  v Chromu. Blur na velké ploše během scrubu je jistá cesta k propadu fps.

## QA pohybu — čtyři kontroly, které nic nestojí

Měření fps říká, jestli animace běží. Neříká, jestli je dobrá. Než
stránku odevzdáš, projdi tohle:

1. **Zpomal ji.** Přehraj klíčové animace na 2–5× delší trvání (dočasně
   zvyš `duration`, nebo sniž rychlost v panelu Animations v DevTools).
   Ptej se: prolínají se barvy čistě, nebo jsou chvíli vidět dva stavy přes
   sebe? Nekončí křivka trhnutím? Je `transform-origin` tam, kde má být?
   Běží opacity a transform synchronně, nebo se rozjíždějí?
2. **Projdi ji po snímcích** (Chrome DevTools → Animations). Odhalí
   rozjetí souběžných vlastností, které při plné rychlosti nevidíš.
3. **Otevři to na reálném telefonu**, ne jen v responzivním režimu
   prohlížeče — dotykové chování, výkon a falešný hover se v emulaci
   nechovají stejně.
4. **Podívej se na to znovu druhý den.** Vady, které jsou během stavby
   neviditelné (protože jsi na ně zvyklý), druhý den vyskočí okamžitě.
   Tohle je nejlevnější kontrola kvality, jakou máme.

Když si po těchhle čtyřech krocích nejsi jistý, jestli animace stránce
pomáhá: **smaž ji.** Nejistota u pohybu je skoro vždy signál, že prvek
pohyb nepotřebuje.

## Anti-slop pro motion (doplněk k 04-anti-slop.md)

- ❌ Stejný fade-up entrance na všech sekcích (šablona, ne choreografie)
- ❌ Scroll-jacking bez úniku (uvězněný scroll; pin s dlouhým `end` bez
  obsahu je vězení)
- ❌ Text bez scrimu přes fotku/vrstvy
- ❌ Efekt bez nadpisu (viz Čitelnost — pravidlo 1)
- ❌ Parallax/pin/kurzorové efekty na mobilech (vypni přes matchMedia) —
  ale POZOR: „klidnější verze" znamená míň HLOUBKY, ne mrtvé texty; vrstva
  Text v pohybu na mobilu zůstává celá (viz výše)
- ❌ Bouncy spring na všem; particle efekty bez důvodu ve světě
- ❌ Marquee se sdělením (marquee jen dekorace/opakování)
- ❌ Motion na dashboardu (tier 0/1 max — viz 03-themes-and-dials.md)
- ❌ `ease-in` na příchodu čehokoli (líný rozjezd v okamžiku, kdy se
  uživatel dívá nejpozorněji)
- ❌ `transition: all` — vždy vyjmenuj konkrétní vlastnosti; `all` animuje
  i to, co nemá, a mimo GPU
- ❌ `scale(0)` jako výchozí stav příchodu (prvek vzniká z ničeho)
- ❌ `:hover` pohyb bez `@media (hover: hover) and (pointer: fine)` —
  na dotyku zůstane prvek zaseknutý ve zvednutém stavu
- ❌ `transform-origin: center` na dropdownu nebo popoveru ukotveném
  ke spouštěči (modal je výjimka)
- ❌ Reveal, který se přehrává znovu při každém projetí sekce
  (`toggleActions` s `reverse`)
- ❌ Stejné trvání příchodu i odchodu u modalu, menu nebo lišty
  (odchod má být svižnější)
- ❌ Prvek, který odjíždí jinou stranou, než kterou přijel
- ❌ Animace na akci spouštěné klávesou (Enter, Esc, ⌘K)
- ❌ Animace na prvku, u kterého neumíš pojmenovat účel jedním slovem
  (zpětná vazba · prostorová souvislost · indikace stavu · zabránění
  skoku · vysvětlení). „Vypadá to hezky“ účel není.
