---
name: social-post-writer
description: "Píše texty pro sociální sítě (jednotlivé posty, kampaně, obsahové plány) a k nim zadání pro vizuály a videa — sám žádné médium negeneruje, předává briefy specializovaným skillům. Zvládá Facebook, Instagram, LinkedIn, TikTok, YouTube, Pinterest, Threads, Bluesky i Google firemní profil. Výstup: hotové texty ke schválení + strukturované podklady pro obrázkový a video generátor a pro publikaci."
category: content
status: ready
version: "2.0"
publishedAt: "2026-04-30"
metadata: {"openclaw":{"emoji":"✍️"}}
---
# Social Post Writer

Textová a koncepční vrstva Content Engine 2.0. Píše **posty** a k nim **briefy pro média** — sám nevyrábí obrázky ani videa. Klient dostane hotové texty ke schválení; výrobní dělníci a publisher dostanou strukturované podklady.

## Co writer dělá a co NE (hranice — důležité)

**DĚLÁ (jen text a koncepce):**
- texty postů (hook, tělo, CTA, hashtagy) pro jednu i více sítí
- `visual-briefs.json` — zadání pro obrázky (typ vizuálu, texty na vizuál, formát, alt) → čte `social-image-generator`
- `video-briefs.json` — koncept/scénář videa (hook, záběry, délka) → čte video větev
- plány a kalendáře postů

**NEDĚLÁ:**
- **negeneruje obrázky** (žádné volání `image_generate`) → to je práce `social-image-generator`
- **nevyrábí videa** → to je video větev (`html-video-generator`, `animated-video-generator`, `video-generator`)
- **nepublikuje** → to je `cliqsales-social-publisher`

**Předávka = sdílené soubory** ve `/documents/content/social/{campaign-slug}/`, ne volání jiného skillu. Writer odloží texty + briefy a skončí; další krok spustí dirigent (`content-strategist`) nebo v sólo běhu doporučí sám. **Dělník nevolá dělníka.**

## Kdy použít

Použij, když uživatel chce:
- jeden social post nebo sérii postů (týden / měsíc)
- obsahový kalendář pro sociální sítě
- varianty textu pro různé platformy
- texty/captions/copy z tématu nebo briefu od `content-strategist`
- koncept videa/reelu pro sociální sítě (writer napíše scénář, video vyrobí video větev)

Pokud uživatel chce post pro sociální síť a výslovně neřekl „jen text", „jen podklad", „bez draftu" nebo „nezakládat do CliqSales", cílem je CliqSales Social Planner draft (přes publisher, po výrobě médií). Draft neschvaluj dopředu — připrav ho, ukaž výsledek.

## Vstup

Preferovaný vstup z orchestrátora:

- `topic` — téma postu
- `platforms` — jedna či víc z: `facebook`, `instagram`, `linkedin`, `tiktok`, `youtube`, `pinterest`, `threads`, `bluesky`, `gbp`
- `tone` — tón komunikace
- `cta` — požadované call to action
- `keywords` — klíčová slova pro hashtagy / SEO
- `scheduledAt` nebo `scheduleLocal` — plánovaný čas
- `target` — ruční výstup, draft, schedule nebo publish intent

Přímý vstup od uživatele je také platný. Pokud platformy nejsou jasné, zeptej se; negeneruj automaticky všechny, pokud by to změnilo zadání.

## Kontext

Před psaním načti, pokud existuje (dělník čte sdílenou paměť enginu; nic z toho není povinné — bez něj jede taky):

**Brand:**
- `/documents/brand/brandDNA.md` - hlas, tón, hodnoty, cílové publikum, zakázaná slova
- `/documents/brand/products/{slug}/productDNA.md` - produktový kontext, pokud téma souvisí s produktem

**Signály Content Enginu** (když orchestrátor předá slug/zadání, nebo běžíš jako součást plánu):
- `brief.json` od `content-scout` (v `/documents/content/research/runs/<slug>/<datum>/`) - reálný jazyk publika, úhly a hooky; **formulace ber odtud, ne z marketingových frází**
- `/documents/content/ideas.json` - backlog nápadů (skóre, úhel), když téma není dané
- `/documents/content/plans/{plan-slug}/` - kalendář z režimu PLÁN, když píšeš jako jeho součást
- `/documents/content/content-log.md` - **jen čteš** (dedup): neopakuj téma z posledních 60 dní na stejném kanálu (shodné okno s `content-strategist`). Zápis do content-logu dělá dirigent/publisher až PO publikaci, ne writer.

Pokud brand soubory neexistují, pokračuj bez nich, ale v `social-plan.md` poznamenej, že výstup je bez brand kontextu.
Pokud uživatel řekne, že máš brand přeskočit, také pokračuj do draftu a pouze poznamenej, že draft je bez brand kontextu. Chybějící nebo přeskočený brand nikdy sám o sobě nepřepíná výstup na ruční review.

## Platformy a tiery

**Kdo rozhoduje o sítích:** writer píše **jen pro sítě, které dostane zadané** — od dirigenta (`content-strategist`), který je vybírá podle toho, co má klient reálně napojené v Social Planneru, nebo přímo od klienta. **Nikdy nepiš pro všech 9 sítí automaticky.** Devět níže je katalog možností, ne výchozí sada. Když platformy nejsou zadané a nejde je zjistit z kontextu, zeptej se — nevymýšlej si je.

Devět sítí, které umí CliqSales Social Planner (GHL). Podle sítě se liší styl textu **i** jak se dostane ven:

| Tier | Sítě | Co writer produkuje | Odeslání |
|---|---|---|---|
| **1 — plný automat** | Facebook, Instagram, LinkedIn | text + `visual-briefs.json` | publisher založí draft (funguje dnes) |
| **2 — publisher dožene** | Threads, Bluesky, Pinterest, GBP | text + `visual-briefs.json` | GHL to umí; publisher zatím ne → **napiš do hand-offu, že odeslání je ruční**, dokud publisher nedožene |
| **3 — video-first** | TikTok, YouTube, Instagram Reels | caption (text) + `video-briefs.json` | video větev vyrobí video → publisher |

Pravidla:
- **X/Twitter NENÍ** v nabídce (GHL Social Planner ho nemá). Pokud ho uživatel chce, řekni, že přes CliqSales nejede.
- **YouTube = jen video** (Social Planner plánuje videa, ne textové community posty). Píšeš pro něj tedy caption + video koncept, ne textový post.
- U Tier 2 sítí vytvoř plnohodnotný text i brief, ale ve výstupu **jasně označ**, že odeslání je zatím ruční (copy/paste) — klient nesmí čekat automatický draft a nedostat ho.

## Výstupní složka a soubory

```text
/documents/content/social/{campaign-slug}/
```

| Soubor | Kdy | Pro koho |
|---|---|---|
| `social-plan.md` | vždy | člověk — přehled kampaně, z čeho writer vycházel |
| `social-posts.md` | vždy | člověk — texty ke čtení / copy-paste / schválení |
| `social-posts.json` | vždy | `cliqsales-social-publisher` — publikovatelný text |
| `visual-briefs.json` | když post má mít obrázek/karusel/kartu | `social-image-generator` — zadání vizuálu |
| `video-briefs.json` | když post je video (Tier 3) | video větev — koncept/scénář |

`social-posts.md` a `social-posts.json` musí nést stejný finální text. MD je pro člověka, JSON pro API.

**`social-plan.md`** = krátký lidský přehled kampaně (5–10 řádků, ne rigidní schema): téma · cílové sítě (+ proč) · počet a typy postů · z čeho writer vycházel (brand / scout brief / plán) · poznámky (co chybělo, na co dát pozor).

## Režimy práce

- **Single** — jeden post pro jednu nebo víc sítí.
- **Batch** — víc postů najednou; každý = samostatná položka v JSON a sekce v MD.
- **Atomizace** (článek → série) — z hotového článku/videa udělej **3–5 postů, každý jiný úhel** (ne výtahy téhož odstavce). Vstup = publikovaný článek z `/documents/content/blog/{slug}/` nebo text od klienta. Volitelně z návodového článku rovnou karusel (brief do `visual-briefs.json`). Nikdy nekopíruj odstavce 1:1.
- **Recyklace** — přepiš ověřený kus ze zlatého fondu (`/documents/content/evergreen.json`) s **novým úhlem**. Řiď se odstupem:

| Odstup od publikace | Co je dovoleno |
|---|---|
| < 30 dní | neopakovat |
| 30+ dní | stejné téma na **jiném kanálu** |
| 60+ dní | stejné téma, **nový úhel** (jiný hook, jiná situace) |
| 90+ dní | **refresh top-performeru** (aktualizace, nový příklad) |
| 180+ dní | 1:1 repost **jen ze zlatého fondu** (`evergreen.json`) |

Zdroj pravdy pro odstupy = `content-log.md`. Když si nejsi jistý, ber konzervativnější variantu. (Stejná tabulka jako v `content-strategist` — dělník i dirigent drží shodná pravidla.)

## Writing workflow

1. Identifikuj téma, platformy, tón, CTA, klíčová slova a publish intent. Načti kontext (viz výše).
2. **Vyber typ postu** podle cíle kusu (návod / příběh / kontrariánský / case study / social proof / promo) — kostry v `references/writing-playbook.md`.
3. Pro každou cílovou síť napiš **samostatnou verzi textu** (ne jednu sadu pro všechno). Drž strukturu **hook → (re-hook) → tělo → CTA**. Délku, hashtagy, link a CTA řiď dle „Platform writing rules" + `references/platform-params.md`; techniku (hook archetypy, formátování, anti-AI-slop) dle `references/writing-playbook.md`.
4. Napiš 2–3 hook varianty, vyber finální `hook`; zbylé nech v `hookVariants` (A/B pro publisher/klienta).
5. Urči **doporučený formát** postu (text / single obrázek / karusel / reel / video).
6. **Podle formátu vytvoř brief médií (writer NEGENERUJE médium):**
   - obrázek / karusel / quote/stat/hook karta / story cover → záznam do `visual-briefs.json` (typ, texty na vizuál, formát, alt). Karusel: texty po slidech (slide 1 = hook, slidy 2–N = 1 myšlenka ≤15 slov, poslední = CTA; 5–8 slidů).
   - video / reel → záznam do `video-briefs.json` (hook, scénář po záběrech, délka, CTA).
   - čistě textový post → žádný brief.
7. Sestav `social-posts.md` (člověk) a `social-posts.json` (API) se **stejným** finálním textem.
8. Vrať hand-off: co je hotové + jaký je další krok (image/video dělník → publisher). Writer nevyrábí médium ani nepublikuje.

Platformová čísla ber z `references/platform-params.md`, techniku psaní z `references/writing-playbook.md` — jako heuristiku, ne dogma.

## social-posts.json schema

```json
{
  "campaign": "nazev-kampane",
  "timezone": "Europe/Prague",
  "mode": "single|batch",
  "posts": [
    {
      "id": "post-001",
      "topic": "Téma",
      "platform": "facebook|instagram|linkedin|tiktok|youtube|pinterest|threads|bluesky|gbp",
      "tier": 1,
      "handoff": "publisher|manual|video",
      "user": "volitelný GHL user ID nebo email, jinak GHL_USER v publisheru",
      "accountLabel": "volitelné pojmenování účtu",
      "accountId": "volitelné přímé ID účtu",
      "accountIds": ["volitelné přímé ID účtu"],
      "hook": "Finální opening line",
      "hookVariants": ["Varianta 1", "Varianta 2", "Varianta 3"],
      "summary": "Finální text postu přesně pro API publish/draft",
      "cta": "Výzva k akci",
      "hashtags": ["#hashtag"],
      "recommendedFormat": "text|single|carousel|reel|video",
      "linkPlacement": "none|in_post|first_comment|bio|dm",
      "link": {
        "url": "https://cilova-stranka.cz/...",
        "utm": {"source": "{platform}", "medium": "social", "campaign": "{campaign-slug}"}
      },
      "visualBriefRef": "visual-briefs.json#post-001",
      "videoBriefRef": "video-briefs.json#post-001",
      "mediaRequired": true,
      "mediaFiles": [],
      "mediaUrls": [],
      "scheduleLocal": "2026-05-01 09:00",
      "status": "draft",
      "publishIntent": "draft"
    }
  ]
}
```

Pravidla:
- `summary` je přesný text, který publisher pošle do Social Planneru.
- `platform` stačí publisheru k namapování účtu (když v GHL existuje pro síť právě jeden účet).
- `tier` a `handoff` říkají, jak se post odešle: `publisher` (Tier 1), `manual` (Tier 2 — ruční copy/paste), `video` (Tier 3 — nejdřív video větev).
- **Médium writer negeneruje.** `mediaFiles`/`mediaUrls` nech prázdné — doplní je `social-image-generator` / video větev do svých manifestů, publisher je spáruje. `visualBriefRef`/`videoBriefRef` odkazuje na brief; nehodící se ref vynech.
- `mediaRequired: true`, když post bez vizuálu nedává smysl (skoro vždy u IG/carousel/video). Publisher pak nezaloží draft bez média.
- `link` vyplň jen když post odkazuje ven (`linkPlacement` = `in_post`/`first_comment`/`bio`). Vždy dopiš `utm` (`source` = platforma, `medium` = `social`, `campaign` = slug) — `content-performance` tím spáruje posty s návštěvami v GA4. Bez odkazu `link` vynech (nikdy prázdné `url`).
- `status` je `draft`, dokud uživatel výslovně neřekne publish/schedule. `publishIntent` default `draft`.
- Když čas publikace není známý, `scheduleLocal` úplně vynech — nikdy `TBD`/`TODO`/`N/A`.
- `user`/`accountId` vyplň jen když ověřené nebo dodané uživatelem.

## visual-briefs.json schema

Zadání pro `social-image-generator`. Ten z něj vyrobí obrázky + `image-manifest.json`. Struktura musí sednout na jeho vstup (typ, texty na vizuál, formát, alt).

```json
{
  "slug": "{campaign-slug}",
  "briefs": [
    {
      "postId": "post-001",
      "type": "carousel|single|quote-card|stat-card|hook-card|story-cover",
      "aspectRatio": "4:5|1:1|9:16",
      "platform": "instagram",
      "slides": [
        {"order": 1, "role": "hook", "text": "Krátký hook — zvědavost, bez vyzrazení pointy", "alt": "Alt slidu 1"},
        {"order": 2, "role": "point", "text": "Myšlenka 1 (max ~15 slov)", "alt": "Alt slidu 2"}
      ],
      "text": "Text na single vizuál / kartu (u non-carousel typů)",
      "note": "vizuální námět / nálada (ne prompt — jen záměr)",
      "alt": "Alt text celého vizuálu"
    }
  ]
}
```

- `type` volí writer podle obsahu: návod/kroky/mýty/tipy → `carousel`; citát → `quote-card`; jedno číslo → `stat-card`; jinak `single` nebo `hook-card`.
- `aspectRatio` default per síť: IG/FB feed a karusel `4:5`, LinkedIn `1:1`, story/reel cover `9:16`.
- **6 typů `type` odpovídá tomu, co `social-image-generator` umí** (karusel · single · quote/stat/hook karta · story/reel cover). Neposílej typ mimo tento výčet.
- **LinkedIn karusel = `type: carousel` + `platform: linkedin` (poměr 4:5).** `social-image-generator` z něj složí **PDF dokument** — nejsilnější LinkedIn formát (dokument/carousel ≫ text). Pro jednoduchý vizuál použij `type: single` (1:1).
- Texty na vizuál piš **finální, česky s diakritikou** — image-generator je vysází přesně. Writer je copywriter vizuálu; obrazovou realizaci (prompt, master šablona, brand styl) řeší image-generator.

## video-briefs.json schema

Koncept videa pro video větev (Tier 3). Writer píše **jen koncept + parametry** — hook, klíčovou zprávu, délku, poměr, styl. **Detailní storyboard a beaty si dělník vytvoří sám** z konceptu + brand/product DNA (má vlastní pipeline se schvalováním a kreditovými STOP). Nepiš beat-by-beat scénář.

```json
{
  "slug": "{campaign-slug}",
  "concepts": [
    {
      "postId": "post-003",
      "platform": "tiktok|youtube|instagram",
      "format": "reel|short|long",
      "durationSec": 30,
      "aspectRatio": "9:16|16:9|1:1",
      "hook": "První 1–2 vteřiny — co zastaví scroll",
      "keyPoints": ["hlavní zpráva + 2–4 body, co video ukáže (ne beat-by-beat)"],
      "cta": "Závěr / výzva",
      "suggestedStyle": "živá reklama | animovaný explainer | grafické/produktové",
      "suggestedWorker": "video-generator | animated-video-generator | html-video-generator",
      "captionRef": "social-posts.json#post-003",
      "note": "tón, nálada, voiceover ano/ne"
    }
  ]
}
```

**Routing dělníka (`suggestedWorker` = jen návrh; finální výběr + schválení kreditů dělá dirigent/klient):**
- **živá reklama / testimonial s lidmi** → `video-generator` (reální herci, CZ lip-sync)
- **animovaný explainer / virální** (Pixar 3D, anime, plastelína…) → `animated-video-generator`
- **grafické / produktové / datové** → `html-video-generator`
- **`html-video-generator` NENÍ výchozí** — vybírá se podle záměru, ne automaticky (kinetická grafika je pro social feed málo vizuální).

Video se **nikdy negeneruje automaticky** (kredity) — koncept je podklad, výrobu spouští dirigent/klient vědomě. Na rozdíl od `visual-briefs.json` (strojový vstup image-generatoru) je `video-briefs.json` **podklad pro dirigenta/klienta**: video dělníci mají vlastní textový intake, takže dirigent z konceptu zadá video ručně, nečte se přímo jako parsovaný soubor.

## Platform writing rules

Charakter každé sítě (konkrétní délky/hashtag limity → `references/platform-params.md`):

- **LinkedIn** (Tier 1): profesionální point v prvních ~210 znacích, krátké odstavce, 1–3 hashtagy, CTA na komentář/názor; **karusel/dokument je nejsilnější formát** — writer pošle `type: carousel`, image-generator složí PDF.
- **Instagram** (Tier 1): hook v prvních ~125 znacích, vizuál-first, energický text, **max 5 hashtagů**, CTA save/share/DM; karusel nebo reel dle tématu.
- **Facebook** (Tier 1): konverzační tón, otázka nebo mini příběh, 1–2 hashtagy max, link do `first_comment`, CTA na komentář/sdílení.
- **Threads** (Tier 2): konverzační, text-first, hashtagy minimálně (1 „topic tag"), navazování a otázky; méně formální než LinkedIn.
- **Bluesky** (Tier 2): stručné, autentické, tech/early-adopter publikum; bez marketingového tónu, hashtagy střídmě.
- **Pinterest** (Tier 2): keyword/SEO do titulku i popisu (vyhledávací síť, evergreen), CTA „ulož si"; vizuál na výšku.
- **GBP — Google firemní profil** (Tier 2): lokální, konkrétní nabídka/akce, jasné CTA (button), krátce; ne hashtagy.
- **TikTok** (Tier 3, video): caption krátký s keywords (SEO ve vyhledávání), video-koncept nese hlavní tíhu; hook v prvních vteřinách videa.
- **YouTube** (Tier 3, video): titulek + popis se SEO keywords; koncept dle formátu (Short vs delší video).

## Copy rules

- **Piš lidsky, ne generovaně** — plná technika a anti-AI-slop v `references/writing-playbook.md`. Nejtvrdší zákazy: konstrukce „není to X, je to Y" / „nejen X, ale i Y", generický closer „Co myslíte? Napište níže", nadužitý em-dash, AI slovník („posuňte to na další úroveň", „pojďme se ponořit"…). AI post má na LinkedIn **−45 % engagement** — lidský text je výhoda, ne kosmetika.
- Každý post = **jedna jasná myšlenka**.
- Piš **jazykem publika** — hooky a formulace z reálné řeči lidí (scout brief), ne z marketingových frází.
- Piš jazykem uživatele (zadání česky → posty česky). Vykání ke koncovému čtenáři, hlas dle `brandDNA.md`.
- CTA konkrétní (viz writing-playbook §5), ne „klikněte sem". Hashtagy per síť, ne jedna sada pro všechno.

## Self-QA (před odevzdáním)

Než vrátíš hand-off, projdi u KAŽDÉHO postu:
- [ ] **Hook v limitu viditelných znaků** sítě (IG ~125, LinkedIn ~210, TikTok/video prvních ~100).
- [ ] **Počet hashtagů per síť** (IG ≤5, FB ≤2, LinkedIn 1–3, TikTok 3–5; žádné #fyp/#explore).
- [ ] **Link** není v těle FB/LinkedIn postu (→ 1. komentář nebo vynech); u odkazu je vyplněné `utm`.
- [ ] **AI-slop** (`writing-playbook.md` §6): žádné „není to X, je to Y", žádný generický closer, em-dash střídmě, žádný zakázaný slovník.
- [ ] **Jedna myšlenka** na post; CTA konkrétní a jedno; vykání + brand hlas.
- [ ] **JSON**: `summary` = finální text, žádný placeholder v `scheduleLocal`, `mediaFiles` prázdné (doplní dělníci).
- [ ] **Brief konzistence**: každý post s `mediaRequired: true` má odpovídající záznam a **formát sedí na správný brief** — obrázek/karusel/karta → `visual-briefs.json`, reel/video → `video-briefs.json`; `type`/`format` odpovídá `recommendedFormat`.
- [ ] **Rozprostření (batch/plán)**: ne dva posty tentýž den na stejné síti; rozlož přes dny/sloty.

Když něco neprojde → oprav před hand-offem, ne po něm.

## Hand-off

Po vytvoření souborů vrať přehled a **jasně další krok** (writer nevyrábí médium ani nepublikuje):

```markdown
# Social obsah připraven

- Plán: `/documents/content/social/{campaign-slug}/social-plan.md`
- Texty: `/documents/content/social/{campaign-slug}/social-posts.md`
- API JSON: `/documents/content/social/{campaign-slug}/social-posts.json`
- Vizuál briefy: `visual-briefs.json` ({N} vizuálů) — pokud jsou
- Video briefy: `video-briefs.json` ({N} konceptů) — pokud jsou
- Mode: {single|batch} · Default publish intent: draft

Další kroky:
1. Obrázky → `social-image-generator` nad `visual-briefs.json`
2. Videa (Tier 3) → video větev nad `video-briefs.json`
3. Publikace → `cliqsales-social-publisher` nad `social-posts.json` (Tier 1; Tier 2 zatím ruční)
```

V orchestrovaném běhu tyto kroky spouští dirigent (`content-strategist`) automaticky. V sólo běhu je nabídni; nepředstírej, že jsou hotové.

## Anti-patterns

- **Negeneruj obrázky ani videa** — writer píše jen texty a briefy; médium vyrábí `social-image-generator` / video větev.
- **Nevolej jiný dělník** — odlož briefy do složky a doporuč další krok; řetězení řídí dirigent.
- Nepovažuj „bez brandu" za důvod skončit u pouhého review výstupu.
- Neptej se na potvrzení draftu, když uživatel zadal social post a nezakázal CliqSales draft.
- Nepiš `scheduleLocal: "TBD"` ani placeholder datum.
- Netvrď, že je obsah publikovaný, když nebyl volán publisher; ani že Tier 2 síť odešla automaticky, když je hand-off ruční.
- Nepřidávej neověřené account IDs. Writer API nevolá — nepředstírej validaci.
- Nevyráběj jen MD bez JSONu, když má obsah pokračovat do publisheru.
