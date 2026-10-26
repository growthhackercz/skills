# AIQ landing/prodejní stránka — obrázky (zdroj, pořadí, generování, hosting)

Ke stránce patří **dvě samostatné sady**: **produktový carousel** (věrný produkt, artefakt produktové složky) a **lifestyle sada** (vysněný výsledek, per‑stránka). Prodejka NESMÍ recyklovat obrázky z landingu ani viset na cross‑origin URL — vše je **self‑hosted** ve funnel `public/img/`.

## ⛓️ Pořadí a zdroj (POVINNÉ — čti první)

**Carousel se dělá PŘED landing/prodejní stránkou a jen když ještě neexistuje.**

1. **Nejdřív ověř produktovou složku:** `/documents/brand/products/<slug>/carousel/`.
   - **Carousel už existuje** (`01-hero.jpg … 06-*.jpg` + `carousel-manifest.json`) → **NEGENERUJ ho znovu.** Použij ten stávající.
   - **Carousel chybí** → vygeneruj ho přes `product-image-generator` **do produktové složky** (ne ad‑hoc „do stránky") a **teprve pak** stavěj LP.
2. **Carousel je artefakt PRODUKTU, ne stránky.** Žije v produktové složce, je znovupoužitelný napříč landing / prodejkou / e‑shopem. Landing/prodejka ho jen **spotřebuje** (zkopíruje `carousel/*.jpg` → funnel `public/img/`), **nikdy ho negeneruje uvnitř sebe**.
3. **Lifestyle sada je naopak per‑stránka** (vysněný výsledek konkrétní LP) — generuje ji `brand-image-generator` a hostuje se rovnou do funnel `public/img/`.

Závazné pořadí: **(1) carousel v produktové složce hotový → (2) lifestyle sada → (3) build LP z obojího.**

## 📐 Formáty + text podle slotu (POVINNÉ)

**🔤 Text patří JEN na produktový carousel.** Carousel karty nesou baked-in text (nabídka, recenze, callouty — Russell/DTC styl). **Všechny ostatní obrázky (lifestyle, komponenty, nabídky, bonusy) jsou ČISTÉ — bez jakéhokoli textu/nadpisů/log v obrázku.** Popisky a nadpisy k nim dodá až **render (HTML/CSS)** — je to editovatelné, matchuje design system a drží čistou fotku.

**Poměry stran podle toho, kam obrázek jde:**
| Slot | Poměr | Proč |
|---|---|---|
| **Produktový carousel** (s textem) | **4:3** (nebo 1:1 dle product-image-generator) | pruh dlaždic |
| **Lifestyle** (pozadí sekcí, atmosféra) | **4:3 landscape** | full-width sekce, důraz na střed, negativní prostor na overlay |
| **Komponenty / vlastnosti / detaily** | **1:1 čtverec** | jdou do **dvousloupcového** layoutu |
| **Nabídky / value bloky** | **1:1 čtverec** | dvousloupcový layout |
| **Bonusy** | **1:1 čtverec** | dvousloupcový layout (karty vedle sebe) |

Pravidlo: **cokoli, co se na stránce zobrazuje ve 2 sloupcích, generuj 1:1 čtverec**; co je full-width pozadí, generuj 4:3.

## A) Produktový carousel — `product-image-generator` → produktová složka
- **Zdroj věrnosti:** reálná fotka produktu z `/documents/brand/products/<slug>/images/` (bez ní STOP a vyžádej ji). Fotku předávej jako **referenci** (viz Engine) — produkt drží 1:1, žádné vymyšlené logo / tvar / tagline.
- **6 obrázků nesoucích text** (produktový příběh: `01` hero produkt → nabídka → recenze → detail → před/po → lifestyle). **Snímek `01` = HERO** prodejky.
- **Výstup:** `/documents/brand/products/<slug>/carousel/` (`01-hero.jpg … 06-lifestyle.jpg` + `carousel-manifest.json`).
- **Do funnelu:** zkopíruj `carousel/*.jpg` → `public/img/` (např. `sp-c1.jpg … sp-c6.jpg`). Odkazuj relativně `/img/...`.

## B) Lifestyle sada — principy z `product-image-generator`, ale VŽDY BEZ TEXTU
Lifestyle jsou **separátní kategorie** od carouselu: **NIKDY na nich není text** (žádné nadpisy/popisky/callouty). Kvalitu a věrnost řeš principy z `product-image-generator` (`carousel-types.md` → `{BRAND_CONTEXT}` fidelity klauzule), jen bez baked-in textu.

**Sada = 6 produktových lifestyle (emoční sekce) + 3 lifestyle bez produktu (neutrální atmosféra/reference).** Všechny **4:3 horizontální** (pozadí sekcí), čisté, negativní prostor na text overlay (text dodá render).

**6 produktových lifestyle = PRODUKT V AKCI, každý z JINÉHO úhlu a vzdálenosti** (zblízka / střed / celek), různé situace a lidé — variéta, ať se neopakuje, ALE drží brand linii dle Brand DNA klienta.

**🚫 ANTI-REPETICE (klíčová past — model se sám opakuje):** GPT Image 2 defaultně generuje pořád stejného člověka (žena ~40, hnědé vlasy, **světle modrá košile**) ve stále stejné scéně. To je špatně. **V KAŽDÉM promptu explicitně předepiš JINOU konkrétní osobu a JINÉ prostředí** napříč těmito osami:
- **Osoba:** věk (dítě / 20s / 30s / 40s / 50s / senior), pohlaví, barva a délka vlasů, **barva a typ oblečení** (NIKDY 2× světle modrá košile), etnicita, sólo / pár / rodina.
- **Scéna/prostředí cílovky (dle produktu a Brand DNA):** styl prostředí, barvy, denní doba a světlo (ráno / poledne / zlaté večerní), roční období — dle scény relevantní pro TENHLE produkt.
- **Rám:** detail / polocelek / celek + úhel (zepředu / tři-čtvrteční / z boku).
Po vygenerování zkontroluj sadu jako CELEK — pokud dva obrázky působí „stejně", přegeneruj s explicitně jinou osobou/prostředím.

**🔒 PRODUKTOVÁ VĚRNOST ZAKOTVENÁ V PROMPTU (nejdůležitější pravidlo):** reálnou fotku produktu předej jako referenci (`references`/`images`) A do promptu dej explicitní kotvu:
> „Use the attached photo as the EXACT faithful reference — identical shape, proportions, colours and details; the front markings (wordmark + logo) must stay crisp, correctly placed and fully legible exactly as in the reference — **never detach, warp, duplicate, relocate or garble the logo or wordmark**, and do not invent a different product."
- Důvod: bez tvrdé kotvy se často **odlepí/zkomolí logo** (logo produktu). Po vygenerování **vizuálně zkontroluj věrnost loga** u každého; když se odlepilo → přegeneruj.

**3 lifestyle bez produktu** — neutrální atmosféra a reference (autentičnost), velká variabilita prostředí/lidí/světla.

- **Ukládej do funnel `public/img/`:** `sp-lifep1..6` (produktové), `sp-life1..3` (bez produktu).

### 🎬 Pořadí — produktové lifestyle jdou na EMOČNÍ sekce (pozadí)
Produkt v akci prodává emoci. Proto 6 produktových lifestyle pozadí patří přesně na 6 emočních sekcí stránky (v tomto pořadí):

| Emoční sekce | Obrázek |
|---|---|
| **HERO** | `sp-lifep1` (hero **pozadí**, produkt v akci) |
| **Social proof #2** (testimonial) | `sp-lifep2` |
| **Váš den — předtím/potom** | `sp-lifep3` |
| **Case study** (social proof #3) | `sp-lifep4` |
| **Stroj času** | `sp-lifep5` |
| **Osobní emotivní CTA** | `sp-lifep6` |

- Každá z těchto sekcí = foto-band (produktové lifestyle pozadí + tmavý/tint overlay + bílý text z renderu).
- **Datové/racionální sekce** (autoritní pás, komponenty, srovnání, proof čísla) produktové lifestyle pozadí NEmají — tam jdou čisté komponenty/čísla, případně neutrální `sp-life1..3`.
- **Hero = dvě vrstvy, ne jeden soubor** (sjednocení názvů, ať není rozpor): **pozadí** hero sekce = `sp-lifep1.jpg` (lifestyle, produkt v akci); **plovoucí produktová karta** nad ním = `sp-hero.jpg` (samostatný produktový vizuál, pokud existuje). Render je bere z různých tříd (`.sp-hero-photo` → `sp-lifep1.jpg`, `.sp-hero-mock` → `sp-hero.jpg`), takže to nejsou synonyma.

## Engine — VŽDY nativní tool `image_generate` (GPT image 2, OpenClaw)
Obrázky se generují **výhradně nativním toolem `image_generate`** (GPT image 2, default backend OpenClaw — žádný API klíč navíc, billing přes Control Center). **🚫 NIKDY Freepik/Magnific ani jiný externí generátor** — nativní tool je jediná sankcionovaná cesta pro skilly i fleet (validovaný wrapper, „API místo shell", dostupný každému klientovi; Freepik/Magnific klienti nemají). To platí ve VŠECH skillech.

**Reference produktu (věrnost):** reálné fotky produktu předávej **parametrem `images`** (pole cest, max 3) — NE jako flag. Cesty jsou **runtime** `/home/node/documents/...` (ne `/documents/...`). Pořadí: `[fotka produktu, (po pilotu) schválený hero jako style anchor, brand-board]`. Hero drží jen styl/světlo, ne lidi (na scénických kartách chceš různé lidi).

**Parametry volání:**
- `prompt` — celý prompt (scéna anglicky, viditelný text česky se správnou diakritikou).
- `images` — reference (produkt / schválený hero / brand-board), runtime cesty.
- `size` — lifestyle horizontální → `1536x1024` (landscape, pak volitelně ořez na 4:3); portrét `1024x1536`; carousel dle typu (často `1024x1024`).
- `quality` — `high` (prémiový výstup; draft `medium`).
- `outputFormat` — `jpeg` (rovnou JPG, menší, rychlé LCP; když vznikne PNG → převeď `sips -s format jpeg` / Pillow).
- `filename` — cíl `/home/node/documents/...` (carousel do produktové složky, lifestyle do funnel `public/img/`).

**Kredity / STOP:** billing jde přes Control Center. Nejdřív **piloty** (1 produkt + 1 lifestyle) ke schválení stylu a věrnosti, pak zbytek sady. Před prvním placeným voláním i před generováním zbytku sady uveď plánovaný počet obrázků a dostupný odhad ceny a čekej na explicitní souhlas uživatele.

## Hosting — self‑hosted `public/img/`
- Nahraj vygenerované JPG do `/documents/sites/<funnel>/public/img/` (carousel `sp-c1.jpg …`, lifestyle `sp-life1.jpg …`, hero `sp-hero.jpg`).
- V renderu referencuj **relativně** `/img/<name>.jpg` (Next servíruje z public). **NIKDY cross‑origin** (WAF/proxy může non-browser požadavek odmítnout nebo vrátit jiný status a obrázky pak zmizí; landing obrázky NErecyklovat).
- `sales.hero_image` (string `/img/…`) + `sales.carousel` `[{img:"/img/…",title,desc}]` + lifestyle pole ve funnel‑specu. Render má `safeImg()` — každou ne‑`/img/` cestu přepíše na `/img/` fallback → obrázky jsou vždy vidět.

## Jak obrázky používat na stránce (vizuální rytmus)
- **Max 2 textové sekce za sebou → pak vizuál** (lifestyle foto na pozadí sekce s overlay, carousel, graf, ikonová mřížka).
- **Hero** = lifestyle `sp-lifep1.jpg` jako podklad (`hero-media` pattern) + overlay + plovoucí produktová karta `sp-hero.jpg` (pokud existuje; jinak carousel `01`).
- **Pozadí sekcí** = lifestyle 4:3 s tmavým/tint overlay (text čitelný), střed obrázku nese motiv.
- **Bonusy + komponenty nabídky** = každá položka s vlastní fotkou/ikonou.
- Detaily pravidel: `aiq-strategy-generator/references/sales-page-blueprint.md` → sekce „🎨 VIZUÁLNÍ HUSTOTA + OBRÁZKY".
