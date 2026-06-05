---
name: lead-magnet-generator
description: Vytvoří magnet na kontakty — sám doporučí 3–5 typů magnetu pro daný brand a produkt, pak vygeneruje názvy, osnovu, obsah, landing a děkovací stránku. Pro nemarketéry, kratší PDF 10–30 stran.
category: marketing
status: ready
version: 1.1
publishedAt: "2026-05-13"
metadata: {"openclaw":{"emoji":"🧲"}}
---

# Lead Magnet Generator

Vytváří magnet na kontakty — kratší PDF (1–30 stran), které dáváš zdarma výměnou za e-mail. Skill je navržený **pro zakladatele firem, ne pro marketéry**: nepoužívá marketingové žargony, sám se rozhodne, co je pro tvůj případ nejlepší podle informací o tvé značce a produktu.

**Co skill udělá za tebe:**
- Přečte tvůj brand a produkt z brandové knihovny
- Sám doporučí **3–5 nejlepších typů magnetu** se srozumitelným zdůvodněním proč právě tyto
- Po výběru typu vygeneruje 10 názvů a počká na výběr
- Po výběru názvu vyrobí osnovu a počká na schválení
- **Pak už pracuje sám** — vygeneruje kompletní obsah, landing page i děkovací stránku bez dalšího ptaní

**Workflow má 3 kroky, kde čekáme na tebe:**
1. ✋ výběr typu magnetu (Krok 2)
2. ✋ výběr názvu (Krok 3)
3. ✋ schválení osnovy (Krok 4)

Po schválení osnovy už nepřerušuj — zákazník dostane hotový obsah + landing + děkovačku v jednom běhu.

Po dokončení obsahu skill **sám aktivně nabídne** 4 možnosti finálního PDF a podle výběru spustí navazující skill:
- **HTML lead magnet generator** — designové PDF přes Playwright/Chromium s DESIGN.md tokeny
- **Image lead magnet generator** — prémiové AI A4 stránky přes OpenClaw `image_generate`
- **Oboje** — textovou i obrázkovou verzi pro A/B test (sekvenčně: nejdřív text, pak obrázková)
- **Zatím nic** — skončíme u obsahu, PDF si uděláš později

## Kdy použít

Použij tento skill když chceš:
- vytvořit "magnet na kontakty", "PDF zdarma", "freebie"
- získávat e-maily lidí, kteří se zajímají o tvé téma
- mít hodnotný materiál, který vede ke koupi tvého placeného produktu
- iterovat na obsahu už zvoleného magnetu

## Co potřebuješ připravené

Skill nejdřív hledá:

1. **Brand DNA** v `/documents/brand/brandDNA.md` — esence značky, hlas, USP
2. **Product DNA** v `/documents/brand/products/[nazev-produktu]/productDNA.md` — detail konkrétního placeného produktu, na který má magnet vést

**Když některý z těchto souborů chybí, skill se tě zeptá v jednoduchých otázkách a doplní je.** Není to test — můžeš odpovídat lidsky.

## Workflow

### Krok 0 (POVINNÝ): Načtení kontextu

Krok 0 má dvě fáze: **(0.1) detekce existujícího magnetu** a **(0.2) načtení brand+product DNA**.

#### 0.1 — Detekce existujícího magnetu

Než začneš tvořit cokoli nového, ověř, jestli na magnetu už někdo nepracoval. Podívej se do `/documents/lead-magnets/`:

- **Pokud uživatel zmínil konkrétní název** ("uprav magnet Money Reset Audit") → ověř, jestli existuje `/documents/lead-magnets/[odhadnutý-slug]/`
- **Pokud uživatel nezmínil název**, ale ve složce existují předchozí magnety → vypiš je krátce (slug + typ z `00-strategie.md`) a zeptej se, jestli má vzniknout nový, nebo pokračovat v některém existujícím

**Pokud existující složka existuje, polož jednu otázku:**

> *"Pro tenhle magnet už složka existuje (`[slug]`, typ: `[typ]`, název: `[název]`). Co chceš?"*
> 1. **Pokračovat** tam, kde jsi skončil (skill načte poslední dokončený krok a navrhne další)
> 2. **Přepsat obsah** — vrátit se k některému kroku a přepracovat (vyber krok 2/3/4/5/6/7)
> 3. **Začít nový** pod jiným slugem (zadáš nový název)
> 4. **Smazat starý** a začít znovu se stejným slugem (potvrzení)

**Mapování stavu složky → poslední dokončený krok:**

| Existují soubory | Poslední dokončený krok | Skill nabídne |
|------------------|-------------------------|---------------|
| Jen `00-strategie.md` | Krok 2 (typ + zdůvodnění) | Pokračovat na Krok 3 (názvy) |
| + `01-nazvy.md` | Krok 3 | Pokračovat na Krok 4 (osnova) |
| + `02-osnova.md` | Krok 4 | Pokračovat na Krok 5 (obsah) |
| + `03-obsah.md` | Krok 5 | Pokračovat na Krok 6 (landing) nebo rovnou handoff na PDF |
| + `04-landing.md` + `05-dekovacka.md` | Vše hotovo | Nabídnout handoff na PDF (HTML / Image / oboje) |

**Pokud nic neexistuje** → pokračuj rovnou na 0.2.

#### 0.2 — Načtení brandu a produktu

Skill přečte:

| Soubor | Cesta | Co z něj získá |
|--------|-------|---------------|
| Brand DNA | `/documents/brand/brandDNA.md` | hlas, slovník, kdo jsou klienti, jak velká je značka |
| Product DNA | `/documents/brand/products/[nazev-produktu]/productDNA.md` | cena, slib produktu, mechanismus, hlavní bolest |

**Pokud uživatel zmíní konkrétní produkt** ("magnet pro Money Reset", "magnet pro kurz X"), použij `[nazev-produktu]` jako jeho slug. Pokud nezmíní, zeptej se: *"Pro který tvůj placený produkt má magnet vést? (pomůže mi vybrat správný typ a tonalitu)"*

**Když některý soubor chybí**, skill ho doplní interaktivně. Detail v `{baseDir}/references/brand-context-loader.md`.

### Krok 1: Jedna lidská otázka

Polož uživateli **jednu volnou otázku** (ne checkbox kvíz):

> *"Co chceš, aby se po stažení tvého magnetu u čtenáře stalo? Stačí napsat 1–3 věty vlastními slovy. Pokud nevíš, napiš 'doporuč mi to' a já vyberu na základě tvého brandu a produktu."*

Z odpovědi (nebo z brand+product kontextu) skill **sám odhadne**:

- **Fázi rozhodování čtenáře** (poprvé slyší o problému / hledá řešení / vybírá / je blízko nákupu)
- **Co publikum o problému ví** (nikdy o tom neslyšeli / vědí že problém mají / znají typy řešení / znají tvůj produkt)
- **Velikost značky** (start / etablovaná / autorita) — ze brandDNA.md
- **Kolik času je čtenář ochotný strávit** (default 15 min, mění se podle ceny produktu a kategorie pain)
- **Hlavní bolest, kterou magnet řeší**

**NEPTEJ se na "funnel stage" ani "awareness level" ani "ICP" ani "TOFU" — jsou to marketingové pojmy, kterým mnoho zakladatelů nerozumí.** Místo toho odhadni z kontextu. Pokud je něco opravdu nejasné, zeptej se přirozeně: *"Tvoji čtenáři už ten problém znají, nebo o něm třeba ještě nepřemýšleli?"*

Detail logiky v `{baseDir}/references/selection-framework.md` sekce "Auto-detection".

### Krok 2: Doporučení 3–5 typů magnetu ⭐

**🛑 Vyžaduje schválení uživatele. Skill MUSÍ zastavit a vyčkat na user input — NEPOKRAČOVAT autonomně na Krok 3 dokud user explicitně nevybere variantu.**

**Klíčový krok — žádný obsah, dokud nemáš schválený typ.**

Skill vybere z katalogu 14 typů magnetů (`{baseDir}/references/lead-magnet-types.md`) **3–5 nejlepších** podle automatického vyhodnocení.

**Formát výstupu pro každou variantu (jednoduchý lidský jazyk, žádné anglicismy):**

```
═══════════════════════════════════════════════════════════
VARIANTA 1 (Doporučeno) — [TYP]
"[Provizorní pracovní název]"
═══════════════════════════════════════════════════════════

📌 CO TO JE
   1 věta, co je to za formát (ne jak se jmenuje, ale co fyzicky čtenář dostane)

🎯 PROČ PRÁVĚ TENHLE PRO TEBE
   3–4 věty proč to sedí přesně na tvůj brand+produkt+publikum.
   Žádný marketing žargon. Mluv jako kdybys to vysvětloval kamarádovi.

📊 CO OD NĚHO ČEKAT
   • Kolik lidí dá e-mail: X–Y ze 100 návštěvníků landing page
   • Jak dlouho čte: X minut
   • Kolik práce dá implementace pro čtenáře: malá / střední / velká
   • Síla bridge na tvůj placený produkt: slabá / střední / silná

👤 ZMĚNA U ČTENÁŘE
   • Před stažením: [konkrétně, lidsky]
   • Po stažení: [konkrétně, lidsky]
   • Klíčový aha moment: [co si uvědomí]

🌉 JAK NAVÁŽE NA TVŮJ PRODUKT
   • [Popis přemostění lidsky — ne "CTA", ne "bridge"]
   • Kdy je nejlepší čas pozvat ho ke koupi: [v PDF / na děkovací stránce / e-mail #1 / e-mail #3]

📏 ROZSAH
   • [N] stran, asi [T] minut čtení
   • Co tam bude: [stručně]
   • Orientace: na výšku (portrait) / na šířku (landscape)
     Důvod: [1 věta proč pro tento typ — viz orientation.md]

✅ HODÍ SE KDYŽ
   [Konkrétní signály z brandu/produktu/publika, kdy je tahle varianta optimální]

⚠️  RADŠI NE, KDYŽ
   [Edge case kontra]
```

**Pravidla pro 3–5 variant:**

1. **První varianta = "Doporučeno"** + 1 věta extra zdůvodnění proč oproti ostatním
2. **Mix kategorií** — neukazuj 3× to samé, dej různé typy (např. 1 rychlý + 1 střední + 1 hlubší)
3. **Mix doby čtení** — alespoň 1 rychlý (≤10 min) + 1 střední (15–30 min)
4. **Lidský jazyk** — místo "Funnel stage: TOFU, Awareness: problem-aware" napiš "Pro lidi, kteří už ten problém řeší, ale ještě hledají, jak na to"

Po prezentaci variant **STOP — vyčkej na user input.** Polož otázku:

> *"Která varianta tě oslovuje? (Můžeš si i vybrat kombinaci dvou — třeba rychlý magnet jako primární + delší jako bonus později v e-mailové sekvenci.)"*

⚠️ **NEPOKRAČOVAT na Krok 3 bez explicitní volby uživatele** (číslo varianty, název, nebo přirozená volba typu „chci taháček"). Pokud user napíše něco nesouvisejícího, znovu ho slušně přesměruj na výběr.

**Po výběru typu ulož `00-strategie.md`** — jediný soubor, ze kterého downstream skilly (`html-lead-magnet-generator`, `image-lead-magnet-generator`) čtou strukturovaný kontext. Použij YAML frontmatter + markdown zdůvodnění:

```markdown
---
typ: audit                          # one of: checklist, cheat-sheet, sablona, knihovna-prikladu, mini-pruvodce, workbook, audit, quick-start, srovnani, kalkulacka, pripadova-studie, seznam-zdroju, scripty, mini-kurz
orientace: portrait                 # portrait | landscape (z 📏 ROZSAH dané varianty)
delka_stran: 12                     # odhad
delka_minut: 18                     # odhad doby čtení
publikum_faze: solution-aware       # unaware | problem-aware | solution-aware | product-aware | most-aware
brand_slug: prima-finance           # z brandDNA.md (jen pro logging)
produkt_slug: money-reset           # z cesty /documents/brand/products/[slug]/
verze: 1                            # bumpne se při edit-existing flow
---

# Strategie magnetu

## Vybraný typ
[typ + 1 věta proč právě tenhle]

## Zdůvodnění
[3-5 vět z 🎯 PROČ PRÁVĚ TENHLE PRO TEBE dané varianty]

## Klíčová pravidla pro další kroky
- [3-5 bodů z varianty: zaměření, tón, formát, klíčový aha moment]
```

**Slug magnetu** zatím necháváš prázdný — vznikne až po Krok 3 (výběr názvu) a uloží se do nového řádku `slug:` v frontmatteru.

### Krok 3: 10 názvů

**🛑 Vyžaduje schválení uživatele. Skill MUSÍ zastavit a vyčkat na user input — NEPOKRAČOVAT autonomně na Krok 4 dokud user explicitně nevybere název.**

Až po výběru typu vygeneruj **10 názvů** podle pravidel v `{baseDir}/references/prompts.md` sekce "Názvy".

**Klíčová pravidla:**
- **Specifičnost vyhrává:** "5 e-mailů, které prodaly milion korun" je silnější než "Jak psát e-maily" (Hormozi: 1 problém, ne kategorie)
- **Co + jak rychle:** každý název musí dát čtenáři odpověď "co to vyřeší" a "jak rychle"
- **Čísla 3, 5, 7 + časový rámec** (5 min / 7 dní / 30 dní)
- **Hlas přesně podle brandDNA.md**
- **Bez názvu mechanismu** v titulu (mechanismus odhalíš uvnitř)
- Format-specific struktury (checklist a workbook mají jiné vzorce — viz `prompts.md`)

Výstup: 10 názvů od nejsilnějšího po nejméně silný + 1–2 věty proč funguje. **STOP — vyčkej na user input.**

⚠️ **NEPOKRAČOVAT na Krok 4 bez explicitní volby názvu** (číslo, citace názvu, nebo úprava jednoho z nich).

**Po výběru názvu:**

1. Odvod **slug magnetu** = kebab-case schváleného názvu, max 50 znaků, bez diakritiky, bez závorek/uvozovek. Příklad: `"5 e-mailů, které prodaly milion korun"` → `5-emailu-ktere-prodaly-milion-korun`.
2. **Ověř kolizi** — pokud `/documents/lead-magnets/[slug]/` už existuje a nepatří k tomuto runu (z 0.1 by to bylo zachycené), zeptej se uživatele, jestli má skill přidat suffix (`-v2`) nebo přepsat.
3. **Vytvoř složku** `/documents/lead-magnets/[slug]/` a přesuň/dopiš `00-strategie.md` (přidej do frontmatteru pole `slug: [slug]` a `nazev: "[finální název]"`).
4. Ulož 10 názvů + zdůvodnění do `01-nazvy.md` (vítězný název je první + flag `<!-- vybráno -->`).

### Krok 4: Osnova

**🛑 Poslední krok, kde čekáme na tebe — vyžaduje schválení osnovy. Po schválení už pracuje autonomně až do konce (Kroky 5 → 6 → 7 v jedné dávce, bez přerušení).**

Vytvoř osnovu **podle zvoleného typu** — každý typ má jinou strukturu (checklist je úplně jinak než workbook).

Detail per typ v `{baseDir}/references/lead-magnet-types.md` sekce "Struktura".

Stručně:

| Typ | Co má osnova obsahovat |
|-----|------------------------|
| Checklist | 1–3 stránky × seznam akcí (max 25 položek) + úvod + tip |
| Cheat sheet (taháček) | 1–2 stránky × hlavní pravidla/vzorce + 1 příklad |
| Šablona | Úvod + samotná šablona + návod jak vyplnit + příklad |
| Knihovna příkladů | Úvod + 5–15 hotových příkladů s vysvětlením |
| Mini-průvodce | Úvod + 3–5 kapitol + závěr s pozváním ke koupi |
| Workbook | Úvod + N kapitol s cvičeními k vyplnění + reflexe + závěr |
| Audit / Sebehodnocení | Úvod + diagnostické otázky + výsledek + výklad + co dál |
| Quick-start průvodce | Den 1 / Den 2 / … + závěr |
| Srovnání A vs. B | Vysvětlení + tabulka + výklad + co volit |
| Kalkulačka | Vstupní pole + vzorec + příklad + výklad |
| Případová studie | Předtím → akce → potom + lekce |
| Seznam zdrojů | Kategorie + 5–15 zdrojů per kategorie + tip |
| Scripty / hotové věty | Situace + script + varianty + tip kdy nepoužít |
| Mini-kurz | Lekce 1–N (každá ≤5 stran) + závěr |

**Výstup:** prostý očíslovaný seznam stránek. **STOP — vyčkej na schválení osnovy.**

⚠️ **NEPOKRAČOVAT na Krok 5 bez explicitního schválení osnovy** ("OK", "jdeme dál", "souhlasím", úprava dílčí položky a re-schválení).

✅ **Po schválení osnovy už skill pracuje sám.** Kroky 5, 6 a 7 se vykonají v jedné autonomní dávce — žádné další STOP, žádné ptání na schválení mezi sekcemi/kapitolami/landingu/děkovačky. Až na konci skill ohlásí kompletní výsledek + handoff prompt na PDF.

### Krok 5: Obsah (autonomní)

Po schválení osnovy generuj **kompletní obsah najednou** — všechny sekce/kapitoly bez přerušování.

**Univerzální pravidla:**
- Jeden konkrétní problém, kompletní řešení
- Akční tipy do 5 minut implementace
- Konkrétní > obecné (čísla, jména, příběhy, ne fluffy fráze)
- Žádné AI klišé ("v dnešní rychlé době", "pojďme se ponořit")
- Hlas přesně podle brandDNA.md
- Závěrečná sekce = lidský příběh (něco se mi/klientovi stalo → uvědomil jsem si X → tady to máš) + pozvání ke koupi placeného produktu

**Pro krátké formáty** (checklist, taháček, šablona, audit ≤7 stran):
- Žádné doplňující prvky (žádné citáty, žádné mýty vs. fakta)
- Hustá užitečnost — každý řádek je užitečný
- Závěrečná stránka = krátké přemostění na placený produkt (1 odstavec)

**Pro středně dlouhé** (audit, quick-start, případová studie 5–15 stran):
- 1 citát autora per kapitola (volitelný)
- 1 box "častá chyba" per kapitola
- Závěr = lidský příběh + pozvání ke koupi

**Pro dlouhé** (mini-průvodce, workbook, mini-kurz 10–30 stran):
- Plná struktura kapitol (úvod s překvapivým faktem, 3–5 podbodů s aha momenty, citát, mýty vs. fakta, šablona, plynulý přechod)
- Závěrečná kapitola = silný příběh + nabídka

Detail per typ v `{baseDir}/references/prompts.md` sekce "Obsah".

**NEZASTAVUJ se mezi sekcemi.** Vygeneruj všechny sekce/kapitoly v jednom průchodu, ulož do `03-obsah.md`, pak rovnou pokračuj na Krok 6.

### Krok 6: Landing page (autonomní)

Struktura:

1. **10 variant nadpisu** (3 výsledkové, 3 zvědavostní, 2 zaměřené na bolest, 2 na autoritu/sociální důkaz)
2. **Podnadpis** — rozšiřuje vítězný nadpis
3. **Tlačítko k akci** — co bude napsáno na hlavním tlačítku
4. **5–7 odrážek hlavních benefitů** — každá ukazuje co získá / proč to bude fungovat / jak rychle / jak málo úsilí
5. **3–5 sociálních důkazů** — `[VYPLŇ REÁLNÝM TESTIMONIALEM]` pokud nemá
6. **Krátké budování důvěry v autora** — z brandDNA.md (čísla, výsledky, klienti)
7. **Doporučení kolik polí ve formuláři:** vždy doporuč **jen e-mail** (max e-mail + jméno). Každé další pole snižuje počet zájemců o 5–10%.

Ulož do `04-landing.md` a rovnou pokračuj na Krok 7. **Nezastavuj se.**

### Krok 7: Děkovací stránka (autonomní)

Pevný nadpis: **"Gratuluji Vám ke stažení PDF, co teď dále?"**
Pevný podnadpis: **"Již za malou chvíli vám dorazí odkaz ke stažení PDF do vašeho e-mailu. Ale to není vše…"**

Doplň **jeden přemosťovací odstavec** (4–7 vět), který:

1. Vyvolá zvědavost
2. Přejde na lidský příběh (něco se stalo → uvědomil jsem si X → teď to chci dát i tobě)
3. Naváže na placený produkt z `productDNA.md`
4. Slíbí, co bude na zbytku stránky následovat

Ulož do `05-dekovacka.md` a pokračuj na finální handoff (níže).

## Output

```
/documents/lead-magnets/[slug]/
├── 00-strategie.md        # YAML frontmatter (typ, orientace, slug, délka, fáze publika...) + markdown zdůvodnění (Krok 2 + 3)
├── 01-nazvy.md            # 10 názvů, vítězný označený `<!-- vybráno -->` (Krok 3)
├── 02-osnova.md           # osnova (Krok 4)
├── 03-obsah.md            # kompletní obsah (Krok 5)
├── 04-landing.md          # landing page (Krok 6)
└── 05-dekovacka.md        # děkovací stránka (Krok 7)
```

`[slug]` = kebab-case schváleného názvu, max 50 znaků, bez diakritiky.

**Strukturovaný `00-strategie.md`** je jediný kontextový dokument, ze kterého downstream skilly (`html-lead-magnet-generator`, `image-lead-magnet-generator`) čtou — typ magnetu, orientaci, slug produktu, fázi publika. Bez něj by musely tyhle informace dohadovat z volného textu.

Po dokončení vypiš:
1. Cestu ke složce
2. Vybraný typ + lidsky proč
3. **Handoff prompt (POVINNÝ)** — aktivně se zeptej, jak má vzniknout finální PDF:

```
═══════════════════════════════════════════════════════════
✅ Obsah magnetu je hotový.
   Soubor: /documents/lead-magnets/[slug]/03-obsah.md

Jak chceš vyrobit finální PDF?

  1️⃣  TEXTOVÉ PDF (HTML → PDF)
      • Designové PDF přes Playwright/Chromium
      • Použije DESIGN.md tokeny (barvy, fonty, ikony)
      • Rychlé (sekundy), zdarma, žádné AI
      • Vhodné pro: checklist, cheat sheet, workbook, mini-průvodce
      → Spustí: html-lead-magnet-generator

  2️⃣  OBRÁZKOVÉ PDF (AI generované A4 stránky)
      • Prémiové vizuály přes OpenClaw image_generate
      • Brand library (brand-board, 08-inspirace) jako reference
      • Pomalejší (~30 s/stránka), kvalitní design
      • Vhodné pro: případová studie, mini-průvodce s vizuálem, brand magnet
      → Spustí: image-lead-magnet-generator

  3️⃣  OBOJÍ (textové primární + obrázkové bonus)
      • Vytvoří se obě verze pro A/B test landing page
      • Doporučeno když nevíš, co bude lépe konvertovat

  4️⃣  ZATÍM NIC — chci jen obsah
      • Skončíme tady, PDF si udělám později
═══════════════════════════════════════════════════════════

Která varianta? (1 / 2 / 3 / 4)
```

**Po výběru:**
- **1** → invokuj `html-lead-magnet-generator` se složkou magnetu jako kontextem
- **2** → invokuj `image-lead-magnet-generator` se složkou magnetu jako kontextem
- **3** → spusť `html-lead-magnet-generator` první, po dokončení automaticky `image-lead-magnet-generator`
- **4** → poděkuj a ukonči

Pokud uživatel řekne přirozeně ("chci textový", "udělej obrázkový", "obojí"), interpretuj jako 1/2/3.

## Reference

- `{baseDir}/references/lead-magnet-types.md` — katalog 14 typů s detaily kdy který
- `{baseDir}/references/selection-framework.md` — jak skill sám vybere 3–5 typů (auto-detect)
- `{baseDir}/references/prompts.md` — detailní prompty pro každý krok a každý typ
- `{baseDir}/references/frameworks.md` — interní frameworky (Hormozi, Brunson, Haines, Schwartz) — jak je aplikovat, ale bez jejich pojmenování v komunikaci s uživatelem
- `{baseDir}/references/brand-context-loader.md` — jak načíst brand DNA a product DNA
- `{baseDir}/references/example-output.md` — ukázka kompletního workflow s 3 typy
