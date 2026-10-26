---
name: aiq-strategy-generator
description: Vytvoří kompletní CliqSales A.I.Q strategii kvízového funnelu podle Product DNA — lead magnet, kvíz, personalizovaný výsledek, prodejní stránku a e-maily. Provede uživatele výběrem varianty, názvu, vizuálu a textů ve čtyřech schvalovacích krocích a předá schválené podklady k realizaci.
category: sales
status: ready
version: "1.9"
publishedAt: "2026-10-02"
metadata: {"openclaw":{"emoji":"🎯"}}
---

# CliqSales A.I.Q Strategy Generator 1.9

Vytváří **kompletní strategii CliqSales A.I.Q funnelu** (lead magnet → kvíz → dynamický výsledek → personalizovaná prodejní stránka → e-mailový follow-up) a k ní **strojový kontrakt `funnel-spec.json` v0.5**, který mechanicky vykoná skill **`aiq-funnel-builder` 1.1.4**.

**Migrace:** Řada 1.5+ (aktuálně **1.9**) **plně nahrazuje** starší verzi 1.4.x (cesta přes GHL AI Studio s `02-pokyny-landing-kviz.md`). Pokud ve workspace existuje starší verze skillu, tato ji nahrazuje — obě verze nesmí běžet současně (stejný slug). Dříve nasazené funnely postavené přes AI Studio běží dál beze změny.

## Architektura: myšlení do specu, exekuce mechanická

```
aiq-strategy-generator 1.9  →  AIQ-strategie.md (zdroj pravdy) + funnel-spec.json
        │  (mozek strategie — všechna rozhodnutí)
        ▼
aiq-funnel-builder 1.1.4    →  Next.js app + schválený GHL plan/apply + Netlify deploy
        │  (deterministický plumbing — žádná interpretace)
        ▼
živý funnel: / (kvíz) · /vysledek · /magnet/[id] · /online/[id] · /doporuceni
```

Dělící čára NENÍ „lead magnet vs. prodejní stránka". Je to **deterministický plumbing** (GHL pole přes ID, skórování, /api/submit, e-mail plánování) vs. **kreativní prezentace** (texty, design). Všechno deterministické definuje tento skill deklarativně ve `funnel-spec.json` — builder to jen vykoná. Proto žádný name-matching polí, žádný slugifier, žádné hádání klíčů.

## Vstup: Product DNA je POVINNÁ (hard requirement)

**Bez `productDNA.md` skill NESMÍ pokračovat.** Prodejní stránka a e-maily se staví ze skutečné nabídky (komponenty, cena, garance, unikátní mechanismus, důkazy) — bez ní nedávají smysl. Žádný `[OVĚŘ S KLIENTEM]` fallback pro nabídkové sekce.

Pokud `/documents/brand/products/[slug]/productDNA.md` neexistuje:

> *„Pro tento funnel potřebuji Product DNA — z ní se staví nabídka, prodejní
> stránka i e-maily. Pro produkt `[název]` zatím neexistuje. Nejdřív ji s vámi
> připravím; potom plynule navážeme návrhem funnelu."*

**STOP. Nepokračuj bez productDNA.** Žádný URL ani manuální vstup jako náhrada.

`brandDNA.md` je doporučená (hlas + ideální klient) — pokud chybí, zeptej se na 2–3 klíčové body tónu, ale neblokuj.

## Co skill dodá (výstupní kontrakt 1.9)

Dokument + spec + mockup + meta ve folderu `/documents/lead-magnets/AIQ [Quiz title]/`:

| Soubor | Pro koho | Obsah |
|---|---|---|
| **`AIQ-strategie.md`** | klient (**ZDROJ PRAVDY**) | **JEDEN dokument = celý funnel po sekcích:** (1) jádro/pozicování + segmenty, (2) landing copy, (3) otázky kvízu, (4) lead magnet (struktura + proč + obsah), (5) **prodejní stránka (copy po blocích)**, (6) **e-maily (koncept větví + 2 vzorové plné maily ze 2 různých segmentů)**. L3 runtime části (personalizovaný hero/benefity/problémy/text mailů) označené `[personalizováno za běhu]` + vzor. |
| `funnel-spec.json` | **aiq-funnel-builder** | Strojový kontrakt (**držený v syncu s dokumentem**) dle `{baseDir}/references/funnel-spec-schema.md` — otázky + field_id/field_name, skórování, segmenty, `main_result`, `temperature_rules`, `cta_routes`, legacy metadata `magnet_structure`, vykreslovaný `magnet_middle`, `persona_fields` (32 pevných + pole použitá v `magnet_middle`), `score_areas` (volitelné), `benchmark` (volitelné), **`landing` (copy landing page)**, **`sales` (copy prodejky)**, `email_branches`, `urgency_source`, `ops`, `pilot_mode` |
| `mockup.png` | landing hero | Vizuál lead magnetu z Kroku 2.7 |
| `meta.json` | orchestrace | Metadata kvízu (product_slug, base_code, quiz_title, funnel_slug…) |

> **Aktuální kontrakt:** dřív vznikaly tři samostatné dokumenty. Nově je
> **jeden čitelný dokument `AIQ-strategie.md`** zdrojem pravdy pro celý funnel
> včetně prodejní stránky a e-mailů. `landing-copy.md` už nevzniká; landing copy
> je součástí `funnel-spec.json` a oba výstupy se drží v synchronizaci.

**Co skill NEgeneruje:** `02-pokyny-landing-kviz.md`, tabulku field keys/slugů, formLabels mapping, pokyny pro AI agenta v platformě. Celá tahle vrstva zmizela — pole vytváří builder přes GHL API a dostává zpět `id`.

## Workflow

Kroky 0.0–2.7 jsou produkčně ověřené, Krok 3 má výstupní kontrakt + STOP bod 4, Krok 4 je handoff na builder.

### 🚫 Žádné perzistentní mezisoubory před Krok 2.6

Před schválením názvu v Kroku 2.6 NEUKLÁDEJ žádné intermediate soubory na disk — folder name (`AIQ [Quiz title]`) vzniká až tam. Intermediate state drž v paměti konverzace. Zakázané cesty: `/documents/aiq-strategies/*`, `/documents/lead-magnets/_wip-*`, `/tmp/aiq-*`. Od Kroku 2.6 dál je povolený `/documents/lead-magnets/AIQ [Quiz title]/koncepty/`.

### Krok 0.0 (POVINNÝ): Detekce existující práce

Skenuj `/documents/lead-magnets/AIQ */meta.json` a porovnej `product_slug`. Pokud existují předchozí kvízy, nabídni: (1) nový další kvíz — default, (2) přepsat konkrétní existující (stará verze se zazálohuje jako `AIQ-strategie.v[N].md`), (3) upravit jen sekci. Stará data v `/documents/aiq-strategies/` ignoruj.

Stejné zadání může přijet souběžně z chatu i úkolu. Nezakládej nový výstup ani
nový úkol, pokud už existuje rozpracovaná práce se stejným `funnel_slug`;
naváž na ni nebo uživateli ukaž existující výsledek. Nový funnel musí mít nový
slug, nikdy jen duplicitní složku se suffixem vytvořeným bez rozhodnutí uživatele.

### Krok 0.1 (POVINNÝ): Načtení kontextu

1. **`productDNA.md` — POVINNÁ** (viz hard requirement výše). Pokud uživatel nezmínil produkt a v knihovně je víc produktů, zeptej se který.
2. **`brandDNA.md`** — hlas, ideální klient (doporučená).
3. **Vizuální brand — `DESIGN.md`, Brand Book, Brand Kit** (`/documents/brand/`): vytáhni **paletu, typografii a fotostyl**. Barvy zapiš do `funnel-spec.design_tokens` (`primary` / `accent` / `gold` / `tertiary` / `bg` / `surface` / `text` / `text_soft` / `radius`) — **tečou do šablony runtime**, takže funnel dostane brand klienta, ne default. Fotostyl (mood z DESIGN.md) převeď do `visuals.hero_query` / `process_query` / `mood` (konkrétní EN scény pro fotky). Je-li v brandu víc kitů (landing / homepage / produkt), vyber ten **relevantní pro funnel/landing**. Chybí-li DESIGN.md, nech `design_tokens` neúplné — builder doplní **neutrální prémiový light theme, NIKDY CliqSales paletu** (brand pollution).
4. **Klasifikuj typ produktu** (digitální / fyzický / hybridní) — určuje podobu otázky o preferovaném řešení a `cta_routes`.

### Krok 1: Volitelná otázka na úhel

> *„Je něco konkrétního, co mám zdůraznit? Úhel, segment, typ magnetu?"*

Builder 1.0 podporuje pouze automatizovaný režim s kontaktem na konci
(`mode: "automatizovany_prodej"`, `contact_position: "end"`). Režim s kontaktem na začátku
zatím nenabízej ani negeneruj.

### Krok 2: 3 varianty dynamického lead magnetu ⭐ STOP 1

**🛑 Vyžaduje schválení. NEPOKRAČOVAT bez explicitní volby uživatele.**

Prezentuj **všechny 3 podporované varianty**. U každé povinně **CO TO JE / PROČ PRÁVĚ TENHLE / ZMĚNA U ČTENÁŘE / HOOK** — čtyři pole stačí k rozhodnutí. Zbytek doplň, kde to pomůže (co čekat, jak naváže, předběžný název, hodí se / radši ne), ne mechanicky u všech. NIKDY jen 1 variantu s „doporučuji X" — doporučeno = 1. položka seznamu, ne náhrada seznamu. Varianty:

1. 🎯 **Skóre / Osobní hodnocení** — main_result = skóre 0–100 + kategorie
2. 🩺 **Diagnostický audit** — main_result = N kritických oblastí + barevné kategorie
3. 📋 **Personalizovaný plán / Harmonogram** — main_result = harmonogram (X kroků / Y dní)
`calc` a `blueprint` v Builderu 1.0 nemají odpovídající render, proto je
nenabízej ani negeneruj. Každá podporovaná varianta má vlastní naplnění
`main_result`, `temperature_rules` a analytického `magnet_middle` — detail v
`{baseDir}/references/magnet-structure.md`. **Nic nesmí tvrdě záviset na skóre**
— skóre má jen část variant; univerzální větvení řeší `lead_temperature`.

### Krok 2.5 (POVINNÝ, bez ptaní): Technické identifikátory

1. **base_code** dle varianty: `score` / `audit` / `plan` (kolize → inkrement `score2`).
2. **Quiz title** — krátký interní popisek (max 40 znaků, diakritika OK), např. „Vzorový funnel".
3. **funnel_slug** — `aiq-` + ASCII kebab-case z Quiz title, max 40 znaků, např. `aiq-vzorovy-funnel`. Jde do `funnel-spec.json` a určuje Netlify site name + složku `/documents/sites/<funnel_slug>/`.

### Krok 2.5a (POVINNÝ): Jeden idempotentní CC task

Jakmile je známý `funnel_slug`, založ nebo převezmi právě jeden úkol. Stabilní
idempotency key je odvozený z `funnel_slug`, ne z času; souběžný druhý běh tak
převezme stejný úkol místo založení duplicity.

```bash
PRODUKT_SLUG="[produkt-slug]"
FUNNEL_SLUG="[funnel-slug]"

python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py create-task \
  --title "AIQ funnel — [název produktu]" \
  --description "Příprava schválené strategie kvízového funnelu a podkladů k realizaci." \
  --assigned-to cso \
  --priority medium \
  --status in_progress \
  --tag aiq --tag strategy --tag "$PRODUKT_SLUG" \
  --idempotency-key "cso:aiq-strategy:${FUNNEL_SLUG}"
```

Pokud odpověď obsahuje `reused: true`, pokračuj v tomto úkolu a nejdřív načti
jeho stav; nový nezakládej. Pokud uživatel explicitně pokračuje v existujícím
úkolu pro stejný funnel, použij jej. Pokud CC není dostupné, nezakládej náhradní
duplicitní práci; pokračuj v konverzaci a vytvoření stejného idempotentního úkolu
zopakuj před uložením výstupů.

### Povinný CC checkpoint pro STOP 2–4

STOP 1 probíhá ještě před vznikem stabilního `task_id` a zůstává pouze v
konverzaci. Jakmile Krok 2.5a vytvoří nebo převezme CC task, každý další STOP
(2, 3 a 4) musí být před ukončením tahu uložen jako explicitní rozhodovací
checkpoint. Nestačí položit otázku v závěrečné odpovědi: runtime by takový tah
správně uzavřel jako dokončený, zatímco business task by falešně zůstal v
`in_progress`.

Pro každý STOP připrav úplný checkpoint text v jazyce aktuální konverzace:
stručný kontext, všechny možnosti, jasně označené doporučení a přesnou otázku,
co má uživatel rozhodnout. Titul checkpointu musí být lokalizovaný a stabilní
pro daný krok, například `[STOP 2] Výběr názvu lead magnetu`, `[STOP 3] Výběr
vizuálu lead magnetu` a `[STOP 4] Schválení směru strategie`. Potom celý text
pošli přes stdin do retry-safe helperu; nevytvářej kvůli tomu persistentní
meziprodukt na disku:

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py request-review-checkpoint \
  --task-id <task_id> \
  --title "[lokalizovaný stabilní titul STOP bodu]" \
  --created-by cso \
  --content-file - <<'CHECKPOINT'
[úplný lokalizovaný text checkpointu — ne souhrn]
CHECKPOINT
```

Teprve po potvrzeném úspěchu helperu vrať uživateli stejný rozhodovací obsah a
zastav se. Helper vytvoří nebo znovu použije exact textový deliverable a vystaví
task v `review`. Při pokračování ve stejném tasku jej nepřepínej zpět do
`in_progress`: tento přechod by mohl vyvolat duplicitní wake. Pokračuj v
aktuálním tahu a při dalším STOPu použij nový stabilní titul checkpointu.

Pokud helper selže nebo najde stejný titul s jiným obsahem, dál nepokračuj,
nevytvářej náhradní task ani druhý checkpoint a oznam technický blocker. Nikdy
neodvozuj čekání z otazníku či formulace textu a nepoužívej runtime
`sessions_yield` jako náhradu za tento business-review checkpoint.

### Krok 2.6: Výběr názvu lead magnetu ⭐ STOP 2

**🛑 Vyžaduje schválení. NEPOKRAČOVAT bez explicitního výběru názvu.**

Vygeneruj **8–12 silných marketingových názvů** pokrývajících různé úhly (výsledkový / zvědavostní / bolestní / autoritní / urgentní — ne nutně všechny rovnoměrně). První = „Doporučeno" + 1 věta zdůvodnění. Vodítka: specifičnost (čísla + časový rámec), délka ~25–60 znaků, hlas dle brandDNA. **USP z productDNA použij jako filtr kvality nad celým seznamem, ne jako povinnost v každém názvu** — projdi návrhy a slabé (ty, co může tvrdit libovolná konkurence) vyřaď nebo přepiš; aspoň polovina seznamu ať USP nese.

Po výběru: `folder_name = "AIQ " + Quiz_title` (z Kroku 2.5 — NIKDY ze schváleného marketingového názvu). Kolize folderu → zeptej se (přepsat / jiný název / suffix).

**Co je schválený název a co je H1 (ať se to neplete):** schválený marketingový název = **titul magnetu** — jde na mockup a na výsledkovou stránku, drží se doslovně. **H1 landing hero se NEROVNÁ tomu názvu** — píše se až v Kroku 3 podle hook pravidel (copy-recipes, „Hero ve 3 variantách") a smí znít jinak, ale musí s názvem **ladit** (stejný slib, stejný tón). Titul magnetu je pevný, hero je kreativní jeho převyprávění.

### Krok 2.7: Vizuální mockup lead magnetu ⭐ STOP 3

**🛑 Vyžaduje schválení (nebo explicitní „přeskoč mockup"). NIKDY neskipovat tiše.**

**🛑 COST STOP před prvním generováním.** Mockup může čerpat placené kredity.
Nejdřív uživateli sděl:

- kolik generátorových volání plánuješ pro grid a finální render,
- jakého providera/model použiješ a jaký je maximální počet variant (16),
- odhad maximální ceny, pokud ho lze spolehlivě určit; jinak výslovně řekni,
  že přesnou cenu předem neznáš,
- že při selhání nepoběží neomezené retry.

Čekej na explicitní souhlas s placenou operací. Schválení varianty magnetu ani
názvu není souhlas s čerpáním kreditů.

Po souhlasu: sanity check brand assetů → grid 4×4 = nejvýše 16 layoutů, 3:4
vertikál, headline = schválený název z Kroku 2.6 → STOP na výběr → jeden finální
render 1500×2000 px → ulož `mockup.png` do AIQ folderu. Primary
`image_generate`, placený fallback OpenRouter/FAL jen po stejném explicitním
souhlasu. Chybí-li povinné brand assety → flag `[MOCKUP TBD]`, oznam a
pokračuj. API klíče nikdy do logu/promptu.

**Pokud magnet slibuje „tři měřené oblasti"** (score/audit), urči je **teď** — jdou do dílčích skóre na mockupu i do landing textu (Krok 3). Musí sedět obrázek i text; detail v `{baseDir}/references/copy-recipes.md` („Otázky kvízu").

**🖼️ ZOBRAZENÍ GRIDU UŽIVATELI (závazné):**

1. Grid IHNED po vygenerování **zkopíruj do `/documents/lead-magnets/AIQ [Quiz title]/mockup-grid.png`** a v chatu odkaž VÝHRADNĚ touto plnou `/documents/…` cestou — jen tak Control Center zobrazí náhled. **NIKDY neposílej interní název souboru generátoru** (`ig_….png` apod.) — ten se uživateli nezobrazí a výběr se zasekne.
2. **Souběžně s odkazem VŽDY pošli i stručný textový přehled všech 16 variant** (1 řádek na variantu: co zobrazuje, jaký má feel) + svoje top 3 doporučení s důvodem. Uživatel tak vybere i v případě, že se mu náhled nezobrazí — na nic se nemusí doptávat.
3. **Interní identifikátory (`Quiz title`, `base_code`, `funnel_slug`) uživateli NEUKAZUJ** — rozhoduje se o vizuálu a názvu, ne o slugách. Technické hodnoty patří do funnel-spec/meta.json, ne do konverzace.

### Krok 3: Strategie — STOP 4 (klíčové body do chatu) → generace celku (JEDNOU)

**Dvě fáze, jen JEDNA stopka:** klíčové body do chatu ke schválení →
teprve pak plný dokument. Strategie se **NEgeneruje dvakrát.**

**Fáze A — STOP 4: klíčové body DO CHATU (NE soubor, NE plný dokument).** Vypiš jen SMĚR/kostru,
po povrchu, ať se klient nezamotá:
- jádro / pozicování + segmenty
- zvolený **úhel** + koncept **hero slibu** + tón (+ 1 alternativa)
- otázky = zvolený **mechanismus uvědomění** + proč (ne plné znění všech otázek)
- pevný oblouk magnetu + 3 analytické bloky AIQ Engine středu
- rámování nabídky + kadence e-mailů (větve dle teploty)

⚠️ Body musí být dost **KONKRÉTNÍ na to, co řídí copy** (úhel, tón, hero koncept, rámování nabídky) —
jinak vygenerovaný detail klienta překvapí. Uzavři: *„Sedí tenhle směr? Schvalte, nebo řekněte, co
změnit — pak vygeneruju kompletní strategii."*

**🛑 STOP bod 4 — jediné schválení.** NEPOKRAČUJ bez explicitního schválení směru.

**Fáze B — PO schválení: vygeneruj CELÝ `AIQ-strategie.md` + `funnel-spec.json` (JEDNOU, žádný další
STOP).** `AIQ-strategie.md` = **zdroj pravdy**, 6 sekcí:

1. **Jádro / pozicování** — cílovka, segmenty, nabídka (komponenty / cena / garance), zvolený úhel + proč.
2. **Landing page** — copy: hero + podnadpis + 3 měřené oblasti + kredibilita + CTA + mikrocopy kvízu.
   → do `funnel-spec.json` `landing.*` (builder ji čte **ze specu**; **`landing-copy.md` už NEgeneruj**).
3. **Otázky kvízu** — plné znění: zvolený **mechanismus uvědomění** + proč; blok uvědomění; blok
   kvalifikace (Velká čtyřka) + otevřený box. **U každé normy zdroj** („productDNA: …" / „běžná praxe: …").
4. **Lead magnet** — pevný psychologický oblouk Builderu 1.0 + **PROČ tam je** + AIQ Engine
   flexibilní analytický STŘED (`magnet_middle`: 3 bloky, max 5, +
   `souhrn_ted`/`souhrn_chci`/`pointa`/`nalehavost`).
   Kontrakt: `{baseDir}/references/magnet-structure.md` + `funnel-spec-schema.md` → `magnet_middle[]`.
5. **Prodejní stránka** — copy PO BLOCÍCH dle `{baseDir}/references/sales-page-blueprint.md` → „Copy per
   sekci" (hero = **TRANSFORMACE**, ne formule; nabídka, bonusy + hodnoty, garance, FAQ, den, stroj času…).
   → do `funnel-spec.json` `sales.*`. U personalizovaných bloků (hero H1/podnadpis, zrcadlo, benefity,
   námitky) značka `[personalizováno za běhu]` + vzor — L3 dopisuje runtime `personalize.ts`.
6. **E-maily** — koncept větví (hot/warm: den + cíl + tón) → `email_branches` + `urgency_source`.
   **+ 2 VZOROVÉ PLNÉ e-maily ze 2 úplně jiných segmentů** (aby si klient představil reálný mail;
   runtime pak personalizuje per lead v tomto duchu).

+ **Text souhlasu** (`consent_text`) — odpovídá tomu, na co se kvíz OPRAVDU ptá.

**Po vygenerování ulož** `AIQ-strategie.md` + `funnel-spec.json` + `meta.json`. Vnitřní kontrolní seznam
(níže) je tvoje QA, ne další STOP.

**Pozdější změny (on-demand):** klient řekne „změň prodejku / e-maily / …" → přepiš **JEN dotčenou sekci**
dokumentu, `AIQ-strategie.md` zůstává konzistentní, **re-sync** `funnel-spec.json`. Strategie se nerozjede
od detailu; **nepřegeneruj od nuly** — jen jádro (nabídka/segment/pozicování) kaskáduje do všech sekcí.

**Pravidla generace `funnel-spec.json`** — kompletní schéma, kontrakt i příklady jsou v `{baseDir}/references/funnel-spec-schema.md`. Tady jen to, co řídí orchestraci a co se nejčastěji plete:

- **`brand` (POVINNÝ, kompletní)** — `name` / `cta_url` / `privacy_email` / `email_footer` z productDNA/brandDNA. Cokoli chybí → dotaz ve STOP 4. **Builder bez kompletního `brand` odmítne stavět.**
- **Všechny klientské texty** (landing, prodejní stránka, e-maily, otázky) generuj VÝHRADNĚ podle `{baseDir}/references/copy-recipes.md` — 10 úhlů + výběrová logika, landing 5 bloků, mechanismy uvědomění, testy otázek, „Jak psát". Hero mluví k dilematu cílovky, ne výčet vlastností. Ve STOP 4 předlož zvolený úhel + proč + 1 alternativu.
- **Skóre (jen když ho magnet má) měří JEDNU osu = MÍRU POTŘEBY / problému, a směr je PEVNÝ: vyšší skóre = větší potřeba = teplejší zacházení.** Není to stylistika — runtime fallback teploty (`hot_min`/`warm_min`) čte vysoké skóre natvrdo jako hot; obrácená osa je nekompatibilní s kódem.
  - **Osu pojmenuj po mezeře / zátěži / ceně / riziku současného stavu** („nakolik potřebujete X", „skóre rizika…"), **NIKDY po stavu či kompetenci zákazníka** — „jistota", „pokrytí", „zralost", „připravenost", „zdraví", „přehled" osu OBRACEJÍ (100 = spokojený = nekupuje). Test jde o potřebnost produktu, ne o vysvědčení zákazníka.
  - **Body dostává odpověď signalizující POTŘEBU**, ne sympatie k řešení. Otázky „dává vám smysl [náš přístup]?" do skóre NEPATŘÍ (záměr → teplota, vhodnost → kvalifikace/cta_routes). Míchat „nepotřebuju" s „chci koupit" do jednoho čísla = skóre bez významu.
  - **`main_result.label` odpovídá na otázku z `lead_magnet_name`** (slíbil-li magnet „má to pro vás smysl?", skóre odpovídá přesně na to, ne na „jak jistí si jste"). Labely pásem z pohledu zákazníka, ne CRM žargon („silný adept" patří do `category`, ne na obrazovku).
  - **Test person (POVINNÉ QA před STOP 4):** projdi skórováním (a) personu s NEJVĚTŠÍM problémem a (b) spokojenou personu. (a) MUSÍ skončit v nejvyšším pásmu s nejaktivnější `action`, (b) v nejnižším. Jinak je osa obrácená nebo kontaminovaná záměrem — oprav před předložením.
  - **Kvalifikace NIKDY nevychází ze skóre** — horký lead z bloku kvalifikace (otázka na preferované řešení = signál rozpočtu). Skóre je jedna deterministická vrstva, ne páteř; **hloubkovou analýzu dělá VŽDY AI** (nikdy 3 předpřipravené „poznatky" na pásmo). Per-typ orientace osy (`score`/`audit`/`plan`) v `{baseDir}/references/magnet-structure.md`.
- **`role` u KAŽDÉ otázky (POVINNÉ)** — řídí „problémové zrcadlo" na magnetu (TOP 5 verbatim odpovědí odhalujících REÁLNÝ PROBLÉM, hned pod skóre = technika Zrcadlo). Hodnoty: `diagnostic` (odhaluje mezeru/riziko, nese i skóre), `problem` (přání / co zlepšit), `objection` (co brzdí — cena/čas), `routing` (další krok = otázka pro `cta_routes`), `qualifying`, `open` (textarea). **Do zrcadla jdou jen `diagnostic`/`problem`**; `objection`/`routing`/`qualifying`/`open` se vyřadí (jinak „Cena" nebo „Chci nabídku" vyskočí jako problém klienta). Kontrakt + tabulka ve `funnel-spec-schema.md`.
- **`magnet_structure`** — legacy/backward-compatible metadata; Builder 1.0 podle něj neskládá pořadí celé stránky. Nový dynamický obsah patří do `magnet_middle`. **Magnet NEPRODÁVÁ** — prodej je práce prodejní stránky.
- **`magnet_middle` (AIQ Engine — POVINNÝ pro nové funnely)** — 3 analytické bloky (max 5) flexibilního STŘEDU: `text`/`cards`/`steps` + `subtitle` (eyebrow) + `title` (H2) + `persona_field` + volitelná `instruction`. Karty jsou volitelné; nedávej sem akční checklist ani prodejní CTA. Bloky mohou znovu použít `magnet_rozbor`/`magnet_rizika`; pro nový blok přidej nové pole (např. `magnet_prostor`). `persona_fields[]` musí obsahovat všech 32 pevných polí a každé `persona_field` z `magnet_middle`. `souhrn_chci` vyžaduje v kvízu výběrovou otázku „co chcete zlepšit"; `nalehavost` z Product DNA BEZ Kč (částku doplní šablona). Kontrakt: `funnel-spec-schema.md` → `magnet_middle[]`. Chybí-li → builder spadne na pevný střed (starší funnely OK).
- **Teplota** — `temperature_rules.source` default `urgency_budget` z otázky na preferované řešení (tabulka zdrojů + kontrakt ve `funnel-spec-schema.md`; per-varianta v `magnet-structure.md`).
- **GHL pole se NEVYTVÁŘEJÍ ručně a nenavrhují se field keys** — builder je vytvoří přes API a zapíše `id`. Spec nese `field_id` (existující pole) NEBO `field_name` (k vytvoření), nikdy obojí null.
- **`mechanisms` (POVINNÝ)**, **prodejní stránka** (`sales-page-blueprint.md`), **e-maily** (`email-branches.md`), **`visuals`**, **`urgency_source`** (default `none`, fake urgence zakázaná), **`pilot_mode`** (default `false`), **`design_tokens`** — schéma a pravidla každého v `funnel-spec-schema.md`. `mechanisms` je povinný — bez něj sekce 4 prodejní stránky zmizí.

**Kontrola na konci generace — obsahové QA (tvoje, ne další STOP):**

Jen to, co odchytí lidský úsudek, ne parser (strukturní JSON kontrolu drží checklist ve `funnel-spec-schema.md`):

- ✅ Vykání ve všech klientských textech; žádné anglicismy (mimo „CliqSales A.I.Q")
- ✅ Žádné léčebné / zdravotní sliby („podpora prostředí", ne „vyléčí alergie"); zdravotně zabarvené otázky → `consent` povinný
- ✅ Ceny / garance / čísla VÝHRADNĚ z productDNA — nic vymyšleného
- ✅ **Blok uvědomění** má zvolený mechanismus a odpovídá mu formát otázek; **normy prošly testem pravosti** (dá se napsat zdroj? řekne si čtenář „to bych vědět měl"? je to norma pro NĚJ?); závěr = otevřený box
- ✅ **Blok kvalifikace (Velká čtyřka)** kompletní; otázka na preferované řešení nese signál rozpočtu
- ✅ **Otázky prošly testy** — uvědomění: situační + uvědomění; všechny: slovník cílovky
- ✅ **Každá otázka má `role`** — problémové = `diagnostic`/`problem`; „co vás odrazuje" = `objection`; otázka na další krok = `routing`; textarea = `open`. (Bez toho by námitka/routing prosákly do problémového zrcadla na magnetu.)
- ✅ **Skladba ~5 ANO/NE + ~5 výběrových** (automatizovaný prodej) — bohaté výběrové plní TOP-5 zrcadlo, diagnostická ANO/NE krmí AI rozbor; každá ANO/NE jiná páka. Extra diagnostická ANO/NE = `role: diagnostic` **bez `score`** (skóre saturuje). Každá otázka = vlastní GHL pole. Detail v `copy-recipes.md` → „Struktura kvízu".
- ✅ **Skóre měří míru POTŘEBY jedním směrem (vyšší = větší potřeba); „test person" prošel** — persona s největším problémem padne do nejvyššího pásma s nejaktivnější akcí, spokojená do nejnižšího; osa pojmenovaná po potřebě/riziku, ne po stavu zákazníka; kvalifikace nevychází ze skóre
- ✅ **Landing má všech 5 bloků** (hook, podnadpis s počtem otázek, tři měřené oblasti, kredibilita, CTA se třemi sliby)
- ✅ Zvolený komunikační úhel + 1 alternativa připravené pro STOP 4

Před uložením projdi i **strukturní checklist v `{baseDir}/references/funnel-spec-schema.md`** (validní JSON, pole, palety, čárky v options, brand, urgency, magnet_structure).

### Krok 4: Uložení + handoff na aiq-funnel-builder

Ulož do `/documents/lead-magnets/AIQ [Quiz title]/`: `AIQ-strategie.md`, `funnel-spec.json`, `mockup.png`, `meta.json` s klíči: `product_slug`, `base_code`, `quiz_title`, `funnel_slug`, `spec_version` (= `"0.5"`), `skillVersion` (= `"1.9"`), `created` (ISO datum), `approved_name` (schválený marketingový název). Artefakt s nižším `skillVersion` nikdy slepě nekopíruj do nového výstupu; nejdřív ho převeď podle aktuálního kontraktu a znovu validuj.

**CC deliverables + review:**

```bash
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py create-deliverable \
  --task-id <task_id> --title "AIQ strategie — [produkt] — [Quiz title]" --type report \
  --content-file "/documents/lead-magnets/AIQ [Quiz title]/AIQ-strategie.md" \
  --file-path "/documents/lead-magnets/AIQ [Quiz title]/AIQ-strategie.md" --created-by cso

python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py create-deliverable \
  --task-id <task_id> --title "Funnel spec — [Quiz title]" --type report \
  --content-file "/documents/lead-magnets/AIQ [Quiz title]/funnel-spec.json" \
  --file-path "/documents/lead-magnets/AIQ [Quiz title]/funnel-spec.json" --created-by cso

python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py update-task <task_id> --status review
```

Task NIKDY nepřesouvej do `done` přímo (quality review dělá nadřazený agent).

**Závěrečná zpráva klientovi** (bez názvů skillů, interních formátů a technických
cest; dokumenty jsou dostupné jako výstupy úkolu):

```
═══════════════════════════════════════════════════════════
✅ Strategie pro [produkt] — „[Schválený název]" je připravená ke kontrole.

V příloze úkolu #[task_id] najdete:
• kompletní strategii od kvízu po prodejní stránku a e-maily,
• schválený vizuál,
• podklady připravené pro realizaci.

Další krok: projděte strategii. Po vašem schválení připravím funkční funnel
a před spuštěním ještě přesně shrnu zásahy, provoz a případné placené náklady.
═══════════════════════════════════════════════════════════
```

## Reference

- `{baseDir}/references/funnel-spec-schema.md` — anotovaná struktura funnel-spec.json v0.5 (všechny klíče + ilustrativní příklady)
- `{baseDir}/references/magnet-structure.md` — pevná kostra + dynamický analytický střed magnetu a naplnění podporovaných variant
- `{baseDir}/references/sales-page-blueprint.md` — 8 sekcí prodejní stránky diagnóza→předpis, adaptivita dle teploty, cta_routes, fallback /doporuceni
- `{baseDir}/references/copy-recipes.md` — knihovna 10 komunikačních úhlů + výběrová logika a prezentace úhlu ve STOP 4 (hook na dilema, zákaz výčtu vlastností)
- `{baseDir}/references/email-branches.md` — 3 e-mailové větve, obálka + lint pravidla, urgency_source, zákaz fake urgence

## Důležitá pravidla (rychlý souhrn — detaily v těle + referencích)

Jen orchestrační brány, které nesmíš minout. Vše ostatní drží Krok 3 + reference
+ oba checklisty — tady se nerestatuje, ať nevzniká druhá pravda.

1. **Product DNA povinná** — bez ní STOP a poslat uživatele na skill product-dna (žádný fallback pro nabídkové sekce).
2. **4 STOP body:** varianta (Krok 2) · název (Krok 2.6) · mockup (Krok 2.7) · celá strategie v jedné dávce (Krok 3). Nikdy přes STOP autonomně.
3. **GHL pole nevytváříme ani nehádáme** — builder je vytvoří přes API a zapíše `id`; spec nese `field_id` (existující) nebo `field_name` (k vytvoření).
4. **`brand` blok povinný a kompletní** — bez něj builder odmítne stavět.
