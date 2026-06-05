---
name: aiq-strategy-generator
description: Vytvoří kompletní CliqSales A.I.Q strategii — vstupem je Product DNA, manuální popis produktu, nebo URL stránky. Nabídne 4–5 variant dynamického lead magnetu (skóre / audit / plán / kalkulačka / strategický plán), po výběru vygeneruje strategii (segmentace, dotazník, landing, nabídka, follow-up) + samostatné platformově neutrální pokyny pro AI agenta na vytvoření landing page, vlastních polí, kvízu a thank you page. Podporuje více kvízů per produkt.
category: sales
status: ready
version: "1.4"
publishedAt: "2026-05-20"
metadata: {"openclaw":{"emoji":"🎯"}}
---

# CliqSales A.I.Q Strategy Generator

Vytváří **kompletní strategický dokument CliqSales A.I.Q implementace** — podle čeho se staví dynamický funnel (lead magnet → dotazník → landing → nabídka → follow-up). Slouží konzultantovi/majiteli firmy pro prezentaci strategie klientovi nebo internímu týmu.

**Vstup je flexibilní:**

1. **Product DNA** (preferováno) — z `/documents/brand/products/[slug]/productDNA.md`
2. **Manuální popis** — uživatel nalepí informace o produktu
3. **URL produktové stránky** — skill přečte stránku přes `web_fetch` a vytáhne kontext

**Brand DNA** je doporučená (hlas + ideální klient), ale pokud chybí, skill se zeptá nebo dohledá z URL.

**Klíčový princip:** dynamický lead magnet **není statické PDF** (checklist, ebook…). Je to **self-assessment dotazník s dynamickým výstupem per kontakt** — postavené na osvědčené metodě hodnotící karty. Detail v `{baseDir}/references/dynamic-lead-magnet-types.md`.

## Co skill dodá

**Dva soubory** ve folderu `/documents/lead-magnets/AIQ [Quiz title]/`:

### 📄 `01-strategie.md` — strategie pro klienta

1. Cílová skupina + 3 ilustrativní segmenty
2. **Dynamický lead magnet** — vybraná varianta z 5 (skóre / audit / plán / kalkulačka / strategický plán) + **silný marketingový název schválený uživatelem v Krok 2.6** (10 návrhů ke schválení, 2 per kategorie: výsledkový / zvědavostní / bolestní / autoritní / urgentní), s slibem, typem hooku, dynamickým výstupem
3. **A.I.Q dotazník** — 10–15 otázek (default) nebo až 35 (režim „pro osobní setkání"); struktura: kontakt + **5 otázek ano/ne** (doporučené postupy) + 5–10 otevřených kvalifikačních (nebo až 30)
4. **Lead magnet landing page** — strukturální plán (hook + podnadpis + 3 měřitelné oblasti + autorita + výzva k akci), cíl konverze 20–40 %
5. **Nabídka** — postaveno na Product DNA / vstupu (USP, benefity s mechanismy, důkazy, garance, urgence, bonusy)
6. **5denní adaptivní follow-up sekvence** — 6 e-mailů, multikanálově

### 🤖 `02-pokyny-landing-kviz.md` — platformově neutrální pokyny pro AI agenta

Použij v GoHighLevel AI Studio, ScoreApp, Webflow, Typeform, n8n, Make. Obsahuje:

1. **Tabulka vlastních polí — 3 vrstvy identifikace per pole:**
   - **Field name** (lidský, plná otázka): `AIQ - [Quiz short name] - [CELÝ TEXT OTÁZKY]`
   - **Field key** (slug pro API + template tagy): `aiq_[quiz_slug]_[max 3 slova]`
   - **Question text** (v kvízu) = Field name po prefixu

   Příklad: Field name `AIQ - Dýcháte čistý vzduch - Vnímáte v některých místnostech zhoršený vzduch nebo pachy?` + Field key `aiq_dychate_cisty_vzduch_zhorseny_vzduch_pachy`. Pole spadnou do default folderu „Additional Info" (GHL API nepodporuje custom folder při tvorbě). **Field key se posílá explicit v POST /customFields API request (1.3.2+)** — ne přes UI auto-slug, který by ho destruktivně komolil.
2. **KROK 1** — Landing page (prompt pro AI agenta)
3. **KROK 2** — Vlastní pole (striktní pre-creation podle tabulky, PŘED kvízem)
4. **KROK 3** — Kvíz (mapuje 1:1 na pole z KROK 2)
5. **KROK 4** — Thank you page (rychlé vyhodnocení + „připravujeme analýzu, do 5 minut na e-mail")
6. Validační checklist

**Neobsahuje** e-mailové sekvence ani CRM-specific zmínky — je opravdu jen o landing + kvízu + thank you.

### Více kvízů pro jeden produkt

Skill podporuje **více lead magnetů per produkt** (např. nejdřív Skóre, pak Audit). Každý kvíz dostane **vlastní top-level folder** v `/documents/lead-magnets/` pojmenovaný podle schváleného marketingového názvu (`AIQ Spánkové skóre/`, `AIQ Audit prodejní cesty/`) a vlastní namespace ve vlastních polích (`aiq_spankove_skore_*` vs. `aiq_prodejni_audit_*`). Vazbu na produkt drží `meta.json.product_slug`, ne folder hierarchie.

## Workflow

### 🚫 KRITICKÉ: Žádné perzistentní checkpointy před Krok 2.6

**Před schválením názvu lead magnetu v Krok 2.6 NEUKLÁDEJ žádné intermediate soubory na disk.** Intermediate state (Krok 0 kontext, Krok 2 varianty, Krok 2.5 base_code, Krok 2.6 návrhy názvů) drž **pouze v conversation memory**, ne jako persistované soubory.

**Důvod:** Folder name (`AIQ [Quiz title]`) vzniká až v Krok 2.6. Před ním nevíme, kam by checkpointy patřily. Ukládat je do `/documents/aiq-strategies/[produkt-slug]/` (stará cesta) je ZAKÁZÁNO — to je STARÁ ARCHITEKTURA, žádný nový obsah tam nepatří.

**⛔ ZAKÁZANÉ checkpoint cesty (žádné z těchto neukládej):**
- `/documents/aiq-strategies/[cokoli]/` — stará cesta, neexistuje pro novou architekturu
- `/documents/lead-magnets/_wip-*/` — wip staging není součástí specu
- `/tmp/aiq-*/` — neperzistujeme nikam

**✅ POVOLENÉ od Krok 2.6 dál:** `/documents/lead-magnets/AIQ [Quiz title]/checkpoints/` — uvnitř finálního folderu. Sem můžeš ukládat audit trail po schválení názvu, např.:
```
/documents/lead-magnets/AIQ Spánkové skóre/
├── 01-strategie.md                 # finální (Krok 3)
├── 02-pokyny-landing-kviz.md       # finální (Krok 3)
├── mockup.png                      # finální (Krok 2.7)
├── meta.json                       # finální (Krok 4)
└── checkpoints/                    # volitelné, po Krok 2.6
    ├── 03-nazvy-vybrane.md         # 10 návrhů + vybraný (audit)
    ├── 04-mockup-grid-source.txt   # poznámka k mockup grid
    └── ...
```

Pokud session crashne před Krok 2.6, intermediate state se ztratí — uživatel skill spustí znovu od Krok 0. To je akceptovatelný trade-off za čistou architekturu.

### Krok 0.0 (POVINNÝ): Založit NOVÝ CC task pro toto zadání

**🔴 Než cokoli jiného uděláš, založ NOVÝ task v Control Center.** Každé nové zadání = nový task. **NIKDY nerecykluj task ID z předchozí session ani z paměti.** Bez tasku neprochází strategie standardním lifecycle (deliverable + quality review).

**⛔ ZAKÁZÁNO:**
- Použít `update-task` na existující task #X, který byl založen pro jiný produkt nebo jiný kvíz
- Recyklovat task ID z předchozího běhu v session paměti
- Pokračovat v existujícím tasku jen proto, že už něco rozdělaného existuje
- **Pokračovat v CC-linked tasku** (zpráva od CC obsahuje `this operator reply is linked to task #X`), pokud zadání mluví o nové strategii / jiném produktu / jiné variantě. CC link je jen kontextový marker, ne příkaz pokračovat.

**🚨 SCÉNÁŘ: CC operator reply is linked to task #X**

CC automaticky linkuje operator zprávy na otevřený task v dané session. Agent dostane ve zprávě patičku typu:

```
Control Center task context: this operator reply is linked to task #86
"AIQ strategie — [název produktu]". Continue the work on this task.
```

**Tohle ALMOST VŽDY znamená VYTVOŘ NOVÝ TASK**, ne pokračovat. Aplikuj tento rozhodovací strom:

| Signál v aktuální zprávě uživatele | Akce |
|---|---|
| „nová", „udělej novou", „další AIQ", „start", „začni" | **NOVÝ TASK** — ignoruj linkaný |
| Jiný název produktu než v linkaném tasku (např. produkt A v aktuální zprávě vs. produkt B v linkaném tasku) | **NOVÝ TASK** — produkt se změnil |
| Žádost o jinou variantu lead magnetu pro stejný produkt | **NOVÝ TASK** — jiný kvíz |
| „pokračuj", „dodělej", „uprav v tasku" + stejný produkt + stejná varianta | Update existujícího tasku (jediná legitimní výjimka) |
| Uživatel explicitně řekne „pokračuj v #86" / „uprav #86" | Update existujícího tasku |

**Pokud máš jakoukoli pochybnost, vytvoř NOVÝ task.** Uživatel může task v review/in_progress kdykoli zrušit; smíchaný task (s deliverables z 2 různých produktů) je horší než duplicitní task.

**✅ POVINNÉ:**
- Vždy volat `create-task` s **unikátním idempotency key**, který obsahuje aktuální slug produktu + (pokud už víš) variant code + timestamp do sekund
- Pokud `create-task` vrátí `reused: true` → ZASTAV a slušně upozorni uživatele („Pro tento produkt už existuje task #X v review/in_progress. Chceš pokračovat v něm nebo založit nový?"). Pak respektuj rozhodnutí.

**Použij helper `cc_task.py`:**

```bash
# Aktuální produkt slug (z Krok 0.2) — nahraď [produkt-slug] před voláním
PRODUKT_SLUG="[produkt-slug]"   # např. vlajkovy-produkt, online-kurz, sluzba-x
TS=$(date +%Y%m%d%H%M%S)        # vždy aktuální čas do sekund

python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py create-task \
  --title "AIQ strategie — [název produktu] — [Quiz title z Krok 2.5, pokud znáš; jinak doplníš v update-task po Krok 2.6]" \
  --description-file /tmp/aiq-task-desc.md \
  --assigned-to cso \
  --priority medium \
  --status in_progress \
  --tag aiq \
  --tag strategy \
  --tag "$PRODUKT_SLUG" \
  --idempotency-key "cso:aiq-strategy:${PRODUKT_SLUG}:${TS}"
```

**Pravidla pro idempotency key (KRITICKÉ):**

- Vzorec: `cso:aiq-strategy:[produkt-slug]:[timestamp YYYYMMDDHHMMSS]`
- Příklad: `cso:aiq-strategy:[produkt-slug]:20260513170422`
- **Nikdy nepoužívej fixní string** (bez produkt slugu) — vedlo by ke kolizím napříč produkty
- **Timestamp do sekund**, ne do minut — vyhneš se kolizi při dvou rychlých spuštěních
- Produkt slug musí odpovídat aktuálnímu produktu z Krok 0.2 — **NIKDY ne recyklovaný slug z dřívější session**

**Popis tasku** (`/tmp/aiq-task-desc.md`) — krátký, max 5–8 řádků:

```
Tvorba kompletní CliqSales A.I.Q strategie.

Vstup: [Product DNA / URL / manuální popis — co je k dispozici]
Produkt: [název produktu] (slug: [produkt-slug])
Režim: [bude upřesněn v Krok 1]
Vybraná varianta: [bude upřesněna v Krok 2]
Quiz slug: [bude upřesněn v Krok 2.5]
Quiz title: [bude upřesněn v Krok 2.5]

Deliverables (po Krok 4):
  - /documents/lead-magnets/AIQ [Quiz title]/01-strategie.md
  - /documents/lead-magnets/AIQ [Quiz title]/02-pokyny-landing-kviz.md
```

**Co dělat s task ID:** Ulož si vrácené `task.id` z odpovědi do paměti **aktuálního zadání** (ne napříč session). Budeš ho potřebovat v Krok 4 (create-deliverable + update-task na `review`). Po Krok 4 task ID „zahoď" — nepoužívej ho pro další spuštění, i kdyby šlo o stejný produkt.

**Po Krok 2.5 (znáš quiz slug)** a po Krok 2.6 (znáš schválený název):

```bash
# Doplň title a description o quiz title + vybraný název lead magnetu
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py update-task <task_id> \
  --title "AIQ strategie — [název produktu] — [Quiz title] — \"[Schválený název lead magnetu]\""
```

**Pokud helper selže** (např. CC nedostupné) — pokračuj v práci, ale na konci v Krok 4 zopakuj pokus o create-task se stejným idempotency key. Neblokuj generaci strategie kvůli CC výpadku.

### Krok 0.1 (POVINNÝ): Detekce existující strategie pro daný produkt

Skenuj `/documents/lead-magnets/` — folder name pattern `AIQ [Quiz title]`. Pro každý folder čti `meta.json` a porovnej `product_slug` proti aktuálnímu produktu z Krok 0.2.

```bash
# Pseudokód detekce — match podle product_slug v meta.json
for d in /documents/lead-magnets/AIQ\ */; do
  if [ -f "$d/meta.json" ] && [ "$(jq -r .product_slug "$d/meta.json")" = "[aktuální produkt-slug]" ]; then
    echo "$d (vytvořeno $(jq -r .created_at "$d/meta.json"), varianta: $(jq -r .variant_name "$d/meta.json"))"
  fi
done
```

Pokud existují předchozí AIQ kvízy pro tento produkt:

> *„Pro produkt `[produkt]` už existuje [N] AIQ kvíz(ů):"*
> - `AIQ [Quiz title kvízu A]` — varianta `[Skóre]`, vytvořeno `[datum]`
> - `AIQ [Quiz title kvízu B]` — varianta `[Audit]`, vytvořeno `[datum]`
>
> *„Co chceš?"*
> 1. **Vytvořit nový další kvíz** — vznikne nový folder `AIQ [nový Quiz title]` (default)
> 2. **Přepsat konkrétní existující** — vyber název ze seznamu, starou verzi zazálohuji jako `01-strategie.v[N].md` uvnitř téhož folderu
> 3. **Upravit jen některou sekci** — vyber kvíz + sekci 1–6

**Žádná migrace ze staré cesty.** Stará data v `/documents/aiq-strategies/` zůstávají nedotčená — skill je ignoruje. Pokud klient potřebuje migrovat, dělá to ručně.

### Krok 0.2 (POVINNÝ): Načtení kontextu (3-way vstup)

Detail v `{baseDir}/references/brand-context-loader.md`.

**Auto-detekce vstupu:**

| Co uživatel poskytl | Co skill udělá |
|---------------------|----------------|
| Zmínil slug produktu (existuje v `/documents/brand/products/`) | Načti `productDNA.md` |
| Poslal URL produktové stránky | Zavolej `web_fetch`, extrahuj produktový kontext |
| Nalepil text / popis / informace | Použij text jako manuální vstup |
| Nic nezmínil → existuje 1 produkt v brand knihovně | Použij ho a oznam |
| Nic nezmínil → existuje víc produktů | Zeptej se který, nabídni URL/manuální |
| Nic nezmínil → žádný produkt | Polož otázku se 3 možnostmi (Product DNA / URL / manuál) |

Vždy načti i `brandDNA.md` (pokud existuje). Pokud chybí, zkrácená varianta nebo z URL.

**Klasifikuj typ produktu** (povinný krok — určí podobu otázky o preferovaném řešení):

| Typ produktu | Signály |
|--------------|---------|
| **Digitální / informační / služba / kurz** | Online kurz, koučink, konzultace, SaaS, agentura, mentoring, e-book, video kurz |
| **Fyzický produkt** | Zařízení, přípravek, doplněk, gadget, e-commerce produkt, hmotná věc |
| **Hybridní** | Fyzický produkt + povinné zaškolení / instalace / servis (např. čistička s instalací, B2B nástroj s onboardingem) |

Z Product DNA `## 1. Kategorie` typicky vidíš přímo. Z URL/popisu odvodíš: pokud produkt má hmotnou variantu k doručení = fyzický; pokud nutně potřebuje doprovodnou službu = hybridní; jinak digitální. Pokud nejasné → polož 1 otázku.

Cokoli skill nedohledá → označí v dokumentu `[OVĚŘ S KLIENTEM: …]`.

### Krok 1: Volitelná otázka na úhel + režim

> *„Mám všechno, co potřebuju. Předtím poslední věc:*
>
> *1. Je něco, na čem ti záleží, abych zdůraznil? Konkrétní úhel, klíčový segment, typ lead magnetu, který už máš v hlavě?*
> *2. Má lead magnet vést k automatizovanému prodeji (kratší dotazník 10–15 otázek), nebo k osobnímu setkání / konzultaci (delší kvalifikační dotazník až 35 otázek)?*
>
> *Pokud nevíš, napiš 'jdeme' a vyberu sám podle ceny a typu produktu."*

**Auto-doporučení režimu** podle ceny produktu:
- Cena < 50 000 Kč → automatizovaný prodej (default)
- Cena 50 000 – 200 000 Kč → záleží na typu (kurz/program = automat; consulting = osobní setkání)
- Cena > 200 000 Kč → osobní setkání (default)

Pokud uživatel nereaguje na otázku 2, skill aplikuje auto-doporučení a oznámí.

### Krok 2: 4–5 variant dynamického lead magnetu ⭐

**🛑 Vyžaduje schválení uživatele. Skill MUSÍ zastavit a vyčkat na user input — NEPOKRAČOVAT autonomně na Krok 3 dokud user explicitně nevybere variantu.**

**🚨 KRITICKÉ — anti-shortcut pravidlo:**

Skill MUSÍ prezentovat **minimálně 4 varianty** v plném formátu (CO TO JE / PROČ / CO ČEKAT / ZMĚNA / JAK NAVÁŽE / HOOK / PŘEDBĚŽNÝ NÁZEV / HODÍ SE / RADŠI NE). **NIKDY neprezentuj pouze 1 variantu s „doporučuji začít s X"** — i když je jedna jasně nejvhodnější. „Doporučeno" = 1. položka v seznamu, NIKDY náhrada za seznam. Uživatel musí vidět spectrum, aby věděl, čemu se vyhýbá a proč.

**Jak poznáš porušení:**
- ❌ Výstup obsahuje pouze 1 blok `VARIANTA 1 ...` a žádné další
- ❌ Výstup řekne „doporučuju začít s [X]" bez prezentace ostatních variant
- ❌ Výstup zkrátí formát na 1–2 řádky per varianta („Skóre — klasické hodnocení, doporučuju") místo plného 9-sekčního bloku

Pokud se chystáš generovat shortcut, ZASTAV a vrať se k plnému formátu pro 4–5 variant.

Vyber **4–5 variant** ze 5 dostupných typů (detail v `{baseDir}/references/dynamic-lead-magnet-types.md`):

1. **🎯 Skóre / Osobní hodnocení** (klasický scorecard)
2. **🩺 Diagnostický audit**
3. **📋 Personalizovaný plán / Harmonogram**
4. **📊 Kalkulačka přínosů**
5. **🎨 Strategický plán na míru**

**Pravidla výběru:**

- **Vždy prezentuj 4 nebo 5 variant.** Variantu vynech jen pokud je matematicky nemožná pro daný produkt (např. Kalkulačka pro lifestyle koučink bez kvantifikovatelných metrik). „Méně vhodná" ≠ „vynechat".
- **První varianta = „Doporučeno"** + 1 věta extra zdůvodnění. Doporučeno = pořadí v seznamu, ne náhrada za seznam.
- Pořadí: od nejlépe sedící po nejméně sedící
- **Zohlední režim z Krok 1** — pokud režim „osobní setkání", upřednostni varianty s delším kvalifikačním dotazníkem (Audit, Strategický plán)

**Formát výstupu per varianta** (lidský jazyk, žádné anglicismy):

```
═══════════════════════════════════════════════════════════
VARIANTA 1 (Doporučeno) — 🎯 SKÓRE / OSOBNÍ HODNOCENÍ
═══════════════════════════════════════════════════════════

📌 CO TO JE
   1–2 věty, co fyzicky klient dostane (kolik otázek, jaký výstup)

🎯 PROČ PRÁVĚ TENHLE PRO TEBE
   3–4 věty proč to sedí přesně na brand+produkt+publikum.

📊 CO OD NĚHO ČEKAT
   • Konverze landing → vyplněný dotazník: X–Y%
   • Doba vyplnění: X minut
   • Kvalita kontaktů: nízká / střední / vysoká
   • Síla přemostění na placený produkt: slabá / střední / silná

👤 ZMĚNA U ČTENÁŘE
   • Před: [konkrétně lidsky]
   • Po (dynamický výstup): [co konkrétně dostane]
   • Klíčový aha moment: [co si uvědomí]

🌉 JAK NAVÁŽE NA TVŮJ PRODUKT
   • [Popis přemostění — kvalifikační otázka o preferovaném řešení
     prozradí rozpočet, dynamický další krok]
   • Kdy je nejlepší pozvat ke koupi: [na výsledkové stránce /
     e-mail #1 / e-mail #3]

🎣 HOOK (pro landing page)
   Typ: [Frustrace / Připravenost / Výsledek / Náklady / Vize]
     (krátký popis funkce v závorce — viz framework.md sekce 4)
   Příklad nadpisu: „[konkrétní vzor pro tento brand]"

📝 PŘEDBĚŽNÝ NÁZEV (finální vybereme v Krok 2.6)
   „[Pracovní název — 1 návrh splňující 3 povinná kritéria:
     konkrétní výsledek + číslo/čas + emoční náboj]"
   POZOR: toto je jen preview, abys viděl, jaký marketing tón
   tahle varianta nese. V dalším kroku vybereme z 10 finálních.

✅ HODÍ SE KDYŽ
   [Konkrétní signály z brandu/produktu/publika]

⚠️ RADŠI NE, KDYŽ
   [Edge case kontra]
```

Po prezentaci variant **STOP — vyčkej na user input.**

> *„Která varianta tě oslovuje? (Stačí číslo nebo název. Můžeš si i vyžádat úpravy — třeba 'skóre, ale s kratším dotazníkem'.)*
>
> *Předběžné názvy u variant slouží jako preview marketing tónu — finální název vybereme společně v dalším kroku z 10 vyladěných možností."*

⚠️ **NEPOKRAČOVAT na Krok 3 bez explicitní volby** (číslo, název varianty, nebo přirozená volba). Pokud uživatel napíše něco nesouvisejícího, slušně přesměruj na výběr.

### Krok 2.5 (POVINNÝ): Auto-generace technických identifikátorů (base_code + quiz_title)

**Bez ptaní uživatele.** Skill rozhodne autonomně. Folder name (`AIQ [Quiz title]`) se generuje až v Krok 2.6 — tady jen technické slugy.

1. **Mapování vybrané varianty → base code** (pro idempotency CC tasku):

   | Varianta | Base code |
   |---|---|
   | Skóre / Osobní hodnocení | `score` |
   | Diagnostický audit | `audit` |
   | Personalizovaný plán / Harmonogram | `plan` |
   | Kalkulačka přínosů | `calc` |
   | Strategický plán na míru | `blueprint` |

2. **Detekce kolize base_code** (jen pro idempotency key + meta.json — NE pro folder strukturu):
   - Skenuj všechny `meta.json` v `/documents/lead-magnets/AIQ */` pro aktuální `product_slug`
   - Pokud žádný existující kvíz nemá tento `base_code` → použij ho přímo
   - Pokud existuje → inkrementuj (`score` → `score2` → `score3`)

3. **Quiz title** (popisek pro UI skupiny polí) — vymysli sám podle primárního benefitu / bolesti z Product DNA. Příklady napříč doménami: wellness produkt + varianta Skóre + bolest „nekvalitní spánek" → `Skóre kvality spánku`; B2B SaaS + Audit + „pomalé follow-upy" → `Audit prodejní cesty`; online kurz + Plán + „chybí čas" → `Plán prvního milionu`. Max 40 znaků, s diakritikou OK.

Detail v `{baseDir}/references/quiz-implementation.md`.

### Krok 2.6: Výběr názvu lead magnetu ⭐ STOP

**🛑 Vyžaduje schválení uživatele. NEPOKRAČOVAT na Krok 3 dokud user explicitně nevybere název.**

Název je **nejdůležitější CR páka** dynamického lead magnetu. Skill generuje **přesně 10 silných marketingových názvů** a počká.

**Pravidla generace** (detail v `{baseDir}/references/framework.md` sekce „Tvorba názvu lead magnetu"):

- 1. = „Doporučeno" + 1 věta zdůvodnění
- **10 návrhů s povinným mixem 5 kategorií, 2 návrhy per kategorie:** výsledkový / zvědavostní / bolestní / autoritní / urgentní
- Specifičnost (čísla 3 / 5 / 7 / 10 + časový rámec)
- Délka 25–60 znaků
- Hlas přesně podle Brand DNA
- Klíčová slova per varianta (Skóre → „test"/„skóre", Audit → „audit"/„diagnostika", Plán → „plán"/„harmonogram"/„90 dní", Kalk → „kalkulačka"/„kolik vás stojí", Strategie → „strategický plán"/„blueprint")
- Bez názvu mechanismu v titulu

**Formát výstupu:**

```
═══════════════════════════════════════════════════════════
NÁZEV LEAD MAGNETU — vyber 1 z 10 návrhů
═══════════════════════════════════════════════════════════

VÝSLEDKOVÉ
 1. 🎯 [DOPORUČENO] „[název 1]"
    Proč: [1 věta zdůvodnění]
 2. „[název 2]"

ZVĚDAVOSTNÍ
 3. „[název 3]"
 4. „[název 4]"

BOLESTNÍ
 5. „[název 5]"
 6. „[název 6]"

AUTORITNÍ
 7. „[název 7]"
 8. „[název 8]"

URGENTNÍ / CENOVÉ
 9. „[název 9]"
10. „[název 10]"
```

> *„Který název tě oslovuje? Můžeš vybrat číslo, citovat název, nebo navrhnout úpravu (např. 'jednička, ale '30 dní' místo '7 dní')."*

⚠️ **NEPOKRAČOVAT na Krok 3 bez explicitního výběru názvu.** Pokud uživatel upraví, akceptuj a použij upravenou verzi.

Po výběru ulož schválený název do paměti session — použij ho v Krok 3 jako vstup do `01-strategie.md` (sekce 2.1) a `02-pokyny-landing-kviz.md` (header + KROK 1 prompt + KROK 4 prompt).

**Generace folder name z Quiz title (z Krok 2.5):**

```
folder_name = "AIQ " + sanitize(quiz_title)
```

**🔑 KLÍČOVÉ:** Folder se odvozuje z **Quiz title** (krátký interní popisek z Krok 2.5, max 40 znaků, např. „Audit domácího vzduchu", „Skóre kvality spánku"), **NIKDY ne ze schváleného lead magnet name** (= dlouhý marketingový hook z Krok 2.6, např. „Alergie, prach nebo únava? Zjistěte, co může zhoršovat vzduch doma").

**Důvod:** Schválený lead magnet name je marketing hook pro landing page (často dlouhý, s otazníky, čárkami, dvojtečkami). Quiz title je interní strukturní popisek vhodný pro filesystem path — krátký, jednoznačný, bez special chars.

**Sanitize pravidla** (minimální — zachovat čitelnost):
- Nahraď `/` a `\` za ` ` (jediné znaky, které filesystem nezvládne)
- Trim leading/trailing whitespace
- Zachovej diakritiku, mezery — `/documents/` je linux ext4 docker volume, UTF-8 OK

Příklady:
- Quiz title „Skóre kvality spánku" → folder `AIQ Skóre kvality spánku`
- Quiz title „Audit prodejní cesty" → folder `AIQ Audit prodejní cesty`
- Quiz title „Plán prvního milionu" → folder `AIQ Plán prvního milionu`
- Quiz title „Audit domácího vzduchu" → folder `AIQ Audit domácího vzduchu`

**Schválený lead magnet name** (= dlouhý marketing hook) žije v meta.json a v `01-strategie.md` jako H1 / hook — NE v cestě.

**Detekce kolize folderu** (pokud existuje `/documents/lead-magnets/[folder_name]/`):

> *„Folder `AIQ [Quiz title]` už existuje (vytvořen `[datum]`). Co chceš?"*
> 1. **Přepsat** — vygeneruji znovu, starou verzi zazálohuji jako `01-strategie.v[N].md` uvnitř téhož folderu
> 2. **Zvolit jiný název z 10** — vrať se na výběr 1–10
> 3. **Přidat suffix** — folder bude `AIQ [Quiz title] (2)` (nebo (3), pokud (2) existuje)

Žádné automatické inkrementování bez ptaní — chceme jednoznačnou volbu od uživatele.

### Krok 2.7: Prémiový vizuální mockup lead magnetu ⭐ STOP

**🛑 Vyžaduje schválení uživatele. NEPOKRAČOVAT na Krok 3 dokud user explicitně nevybere mockup (nebo neřekne „přeskoč mockup").**

**🚨 KRITICKÉ — anti-skip pravidlo Krok 2.7:**

Skill MUSÍ Krok 2.7 PROVÉST — i když brand assety chybí. „Provést" znamená jedno ze dvou:

**A) Vygenerovat mockup grid** (full reference set nebo fallback path přes openrouter/FAL — viz sekce C níže). Po doručení gridu STOP a vyčkat na user selection.

**B) Označit jako blocker** — pokud sanity check ukáže, že chybí povinné brand assety (`brand-board.png` NEBO `brandDNA.md` NEBO `logo.*`), ulož:
- `mockup_status: "tbd_missing_brand"` do `meta.json` (vytvoří se v Krok 4, drž si to v paměti)
- flag `[MOCKUP TBD — chybí: brand-board.png / brandDNA.md / logo]` do `01-strategie.md` sekce 4.5 (vytvoří se v Krok 3)
- flag `[MOCKUP TBD]` + instrukci pro klienta do `02-pokyny-landing-kviz.md` HERO MOCKUP sekce
- **Oznam uživateli**, co konkrétně chybí, a pokračuj na Krok 3 bez mockupu.

**🚫 NIKDY neskipuj Krok 2.7 ticho.** Přeskočení = porušení workflow.

**Jak poznáš porušení (před přechodem na Krok 3 zkontroluj):**
- ❌ Přeskočil jsi z Krok 2.6 (název) rovnou na Krok 3 (strategie) **bez STOP bodu** pro výběr mockupu
- ❌ Ve výstupu `02-pokyny-landing-kviz.md` **chybí sekce HERO MOCKUP** úplně
- ❌ V `01-strategie.md` **chybí sekce 4.5 Vizuál lead magnetu**
- ❌ V `meta.json` **chybí pole `mockup_path` a `mockup_status`**

Pokud kterékoli z výše uvedeného platí → ZASTAV, vrať se ke Krok 2.7, dokonči ho (cesta A nebo B). Bez Krok 2.7 nelze pokračovat na Krok 3.

Mockup lead magnetu na landing page je primární CR booster (+20–50 % konverze vs. text-only landing). Po schválení názvu z Krok 2.6 skill vygeneruje **grid 4×4 = 16 layoutů** prémiového vizuálního náhledu lead magnetu v **3:4 vertikálním formátu** a počká, až uživatel vybere finální variantu.

Detail prompt template, fallback a reference hierarchie v `{baseDir}/references/mockup-recipes.md`.

**A. Sanity check brand assets** (před voláním image_generate):

| Co existuje v `/documents/brand/` | Kvalita | Akce |
|---|---|---|
| `brand-kit/20-magnet-na-kontakty.png` + `brand-board.png` + `brandDNA.md` + `logo.*` | **Nejvyšší** | Full reference set, pokračuj |
| Chybí `brand-kit/20-magnet-na-kontakty.png`, ostatní OK | **Střední** | Fallback prompt bez primary reference, pokračuj |
| Chybí `brand-board.png` NEBO `brandDNA.md` NEBO logo | **Skip Krok 2.7** | Flag `[MOCKUP TBD — chybí Brand DNA / Brand Board / logo]` v `01-strategie.md` sekci 4.5, pokračuj na Krok 3 bez mockupu |

**B. Sestavení promptu** (per varianta):

Skill sestaví prompt podle template v `{baseDir}/references/mockup-recipes.md` — sekce „Mockup matrix per varianta" + „Prompt template". Per varianta:

| Varianta | Co mockup zobrazuje |
|---|---|
| 🎯 Skóre | Dashboard náhled — 0–100% gauge + 3 sub-kategorie + insights + CTA |
| 🩺 Audit | A4 PDF report — cover + sample inside page s 5 sekcemi |
| 📋 Plán | Kalendář / habit tracker — 7/14/30 dní × denní akce |
| 📊 Kalkulačka | Result dashboard — Kč úspora + breakdown + before/after |
| 🎨 Strategie | A4 blueprint — cover + 3-pillar diagram + roadmap timeline |

**Headline ve všech 16 mockupech v gridu = schválený název z Krok 2.6.** USP keyword z Product DNA sekce 1 musí být v mockupu obsažen.

**C. Volání `image_generate` — primary + fallback path:**

```
PRIMARY: nativní image_generate (GPT image 2)
  - prompt: [sestavený text z mockup-recipes.md template]
  - reference_images: [brand assets podle sanity check]
  - format: 3:4 vertikál (např. 1200×1600 px)
  - grid mode: 4×4 = 16 mockupů s čísly 1–16
  - output: /documents/brand/visuals/grid-aiq-[base_code]-[YYYYMMDD].png

FALLBACK 1: openrouter API (pokud image_generate selže)
  - env: OPENROUTER_API_KEY
  - model: gpt-image-2 nebo dalle-3
  - reference images: base64 inline

FALLBACK 2: FAL API (pokud openrouter selže)
  - env: FAL_KEY
  - model: flux-pro nebo gpt-image-2
  - reference images: upload first, pak URL

FALLBACK 3: Všechny selhaly → flag [MOCKUP TBD — image gen nedostupný],
            pokračuj na Krok 3 bez mockupu
```

**Bezpečnost:** OPENROUTER_API_KEY a FAL_KEY nikdy do logu / promptu / paměti agenta — vždy přes env var v scriptu.

**D. Anti-AI-slop pre-check** (před prezentací gridu uživateli):

Skill projde výstup checklistem v `{baseDir}/references/mockup-recipes.md` sekce „Anti-AI-slop checklist". Pokud cokoli selhává (lorem ipsum, brand name v hlavičce místo USP, nečitelná čísla, generický AI feel) → automaticky regeneruj se silnějšími anti-pattern instrukcemi v promptu. Cap auto-regenerace na 2 pokusy, pak požádat uživatele o explicit feedback.

**E. Prezentace gridu + STOP:**

```
═══════════════════════════════════════════════════════════
VIZUÁLNÍ MOCKUP LEAD MAGNETU — 16 variant ke schválení
═══════════════════════════════════════════════════════════

📄 Grid uložen: /documents/brand/visuals/grid-aiq-[base_code]-[YYYYMMDD].png
   Format: 3:4 vertikál · 16 layoutů (4×4 grid, číslované 1–16)
   Varianta: [SKÓRE / AUDIT / PLÁN / KALKULAČKA / STRATEGIE]
   Headline: „[schválený název z Krok 2.6]"

Brand reference použitá:
   [✅ brand-kit/20-magnet-na-kontakty.png — primary vzor]
   [✅ brand-board.png — moodboard]
   [✅ brandDNA.md sekce 6 — paleta + typografie]
   [✅ logo.png — přesné logo]
```

> *„Tady je grid 16 mockup variant. Vyber 1 (nebo více), kterou chceš použít jako finální mockup na landing. Můžeš taky napsat „regeneruj [s úpravou]" pokud žádný nesedí — např. „regeneruj minimalističtější" nebo „regeneruj víc dashboard-like"."*

⚠️ **NEPOKRAČOVAT na Krok 3 bez explicitního výběru** (číslo 1–16, „regeneruj X", nebo „přeskoč mockup, pokračuj bez něj").

**F. Finální render** (po user selection):

```
1. Sestav prompt pro full-size single mockup (1500×2000 px, 3:4 vertikál)
2. Vlož grid PNG jako referenci + řekni „vygeneruj plnou verzi mockupu #N z přiloženého gridu"
3. Volej image_generate (primary) nebo fallback
4. Ulož:
   - /documents/brand/visuals/aiq-[base_code]-[YYYYMMDD].png (originál)
   - /documents/lead-magnets/AIQ [Quiz title]/mockup.png (copy do AIQ folderu)
5. Propiš do meta.json (vytvoří se v Krok 4):
   - "mockup_path": "/documents/lead-magnets/AIQ [Quiz title]/mockup.png"
   - "mockup_layout_number": 7
   - "mockup_grid_source": "/documents/brand/visuals/grid-aiq-..."
```

**G. Regenerace** (pokud uživatel řekne „regeneruj [úprava]"):

Skill modifikuje prompt podle úpravy (např. „minimalističtější" → přidá „prioritizuj whitespace, méně density") a zavolá `image_generate` znovu pro nový grid. **Žádný cap na regeneraci** — klient platí svůj API klíč a rozhoduje sám. Před každou regenerací krátká hláška „Generuju další grid (image_generate volání #N)".

**H. Verzování mockupů** (při přegenerování stávajícího kvízu):

Před overwrite `mockup.png` → starý přesun na `mockup.v[N].png` (kde N je další volný index) ve stejném AIQ folderu.

### Krok 3: Autonomní generace celé strategie + pokynů pro AI agenta

**🛑 Po výběru názvu i mockupu žádné další STOP body. Skill jede do konce.**

**🚨 KRITICKÉ — anti-skip Design tokens v `02-pokyny-landing-kviz.md`:**

Před generací `02-pokyny-landing-kviz.md` MUSÍŠ načíst `/documents/brand/DESIGN.md` a propsat **konkrétní HEX hodnoty, font names, gradient stack, radius, layout** do VIZUÁL sekce promptu pro AI agenta. NE placeholdery `[#primary]`, NE odkazy „použij z DESIGN.md".

**Pokud DESIGN.md existuje:**
- Vlož KONKRÉTNÍ tokens (HEX, font names, gradient) jako finální copy-paste-ready hodnoty pro AI agenta v platformě

**Pokud DESIGN.md NEEXISTUJE (chybí v `/documents/brand/`):**
- ❌ **NIKDY nepouživej default CliqSales paletu** jako fallback — to by byla brand pollution (klient by dostal stránku s CliqSales-feel místo svého)
- ✅ **VIZUÁL sekce v `02-pokyny-landing-kviz.md` se ÚPLNĚ VYNECHÁ** (žádný flag, žádný placeholder, žádná poznámka v `01-strategie.md`)
- ✅ Vygeneruj jen texty (Nadpis, Podnadpis, Tři oblasti, Autorita, CTA) bez design tokenů
- ✅ Pokračuj na Krok 3 bez blocking — klient si DESIGN.md doplní později manuálně pokud bude chtít brand styling

**Jak poznáš porušení (před handoffem v Krok 4 zkontroluj):**
- ❌ `02-pokyny-landing-kviz.md` má VIZUÁL sekci s placeholdery `[#primary]`, `[Display font]` místo konkrétních hodnot
- ❌ Použita CliqSales default paleta bez explicit DESIGN.md klienta
- ❌ Flag `[DESIGN TOKENS TBD]` v dokumentu (v 1.2.7+ úplně vynechej VIZUÁL sekci, žádný TBD flag)
- ❌ **`02-pokyny-landing-kviz.md` NEMÁ VIZUÁL sekci, i když `/documents/brand/DESIGN.md` EXISTUJE** — to znamená, že agent nenačetl DESIGN.md (1.3.2 force-load porušení). VŽDY proveď `ls /documents/brand/DESIGN.md` před generací; pokud existuje, propsat tokeny POVINNÉ.

Pokud kterékoli z výše uvedeného platí → ZASTAV, načti DESIGN.md (pokud existuje, propsat konkrétní hodnoty; pokud ne, smazat VIZUÁL sekci úplně), znovu vygeneruj.

**🚨 KRITICKÉ — anti-skip pro `02-pokyny-landing-kviz.md` obsah:**

`02-pokyny-landing-kviz.md` MUSÍ být kompletní exekuční dokument pro AI agenta v platformě (GHL AI Studio / ScoreApp / Webflow). Agent v platformě **nemá kontext** — všechno musí být v souboru hotové, copy-paste-ready.

**Minimální délka:** ≥ 200 řádků (typicky 250–400). Pokud < 200 → agent zkrátil template místo vyplnění → ZASTAV a regeneruj.

**Povinné sekce s jejich minimálním obsahem (před handoffem zkontroluj):**

| Sekce | Co MUSÍ obsahovat | Detektor porušení |
|---|---|---|
| **Projekt** | Lead magnet, Produkt, Quiz title, Quiz short name, Quiz slug, Varianta, Režim | < 7 řádků = chybí |
| **KROK 1 — Landing page** | Nadpis (full hook) · Podnadpis · **Tři měřitelné oblasti** (active sloveso + číslo) · **Autorita** (kdo, čísla, social proof) · CTA (full text) · **VIZUÁL design tokens** (HEX + fonts + radius — pokud DESIGN.md existuje) · **HERO MOCKUP pokyny** (cesta + umístění + format) | Chybí Tři oblasti / Autorita / VIZUÁL = porušení |
| **KROK 2 — Custom pole** (1.3.13 IMPERATIV) | **Imperativ „POVINNĚ TEĎ vytvoř, NEPTEJ SE"** + 5-krokový postup (zkontroluj → vytvoř chybějící → použij existující → oznam → pokračuj) + **seznam Field names** + explicit zákaz ptaní uživatele + explicit „pokračuj rovnou na KROK 3 bez čekání". NIKDY nedávej agentovi fieldKey, dataType, options, API endpoint URL — agent si vyřídí interně. | Chybí imperativ „POVINNĚ TEĎ" / chybí zákaz ptaní / chybí check-or-create logika / dáno víc než seznam field names + imperativ = porušení 1.3.13 |
| **KROK 3 — Kvíz / dotazník** (1.3.15) | **UX pravidla** (progress · selected · required markers, BEZ konkrétní ms hodnoty transition) · Pořadí kontaktu (krátký na konec / dlouhý na začátek) · **Seznam otázek** + typy odpovědí (ano/ne · 1 z víc · víc současně · textarea) · Skórování pro Skóre/Audit · **KRITICKÉ Mapping do CRM** (3 pravidla: keys BEZ `contact.` prefixu / formLabels s plným field name vč. `AIQ - [QSN] - ` prefixu / array-to-CSV). | Chybí UX patterns / seznam otázek / chybí kterékoli ze 3 mapping pravidel = porušení 1.3.15 |
| **KROK 4 — Thank you page** | Rychlé vyhodnocení (skóre / hlavní oblast / další krok) · **Segmenty** s personalizovaným textem · Dynamický další krok podle odpovědí · **VIZUÁL design tokens** (pokud DESIGN.md existuje) | Chybí segmenty / personalizace = porušení |

Pokud kterékoli sekce nesplňuje minimum → ZASTAV, regeneruj `02-pokyny-landing-kviz.md` kompletně podle template v `{baseDir}/references/quiz-implementation.md`.

**(1.3.15 SIMPLIFICATION):** Detector pro field key algoritmus odstraněn. Agent v GHL AI Studio si keys generuje sám podle interního GHL slugifieru — my je v skill nediktujeme. Match Quiz.tsx ↔ CRM probíhá přes `formLabels` mapping (viz FORM-POST-PAYLOAD detector níže), ne přes shodu klíče.

**🚨 ANTI-LAYOUT-INSTRUCTION detector (1.3.11+):**

Před handoffem v Krok 4 zkontroluj, že `02-pokyny-landing-kviz.md` **NEOBSAHUJE explicit layout instrukce** (px rozměry, CSS utility, container/grid pokyny). Layout je výhradně v rukou AI agenta v platformě — my dáváme jen brand identity (barvy, fonty, radius).

**Zakázané fráze v dokumentu** (= layout micromanagement, který agent neumí dodržet):

- ❌ „Max šířka stránky" / „max-width" / „max content width"
- ❌ „hero padding" / „section padding" / „vertikální mezery" s konkrétní hodnotou
- ❌ „container", „grid", „flex" jako CSS pokyny s rozměry
- ❌ Konkrétní px rozměry stránky: „1180 px", „1200 px", „1240 px", „1440 px"
- ❌ Tailwind utility classes: „rounded-2xl", „shadow-lg", „py-12", „gap-8"
- ❌ „section gap" / „vertical rhythm" / „grid proporce"

**Povolené** (= obsahové + brand identity pokyny):

- ✅ Konkrétní HEX barvy z DESIGN.md
- ✅ Font names + váhy + velikosti pro typografii (display/heading/body)
- ✅ Radius v px (single brand token, např. `8px`)
- ✅ Gradient direction + stops
- ✅ Obsahové pokyny: „Nadpis (max 14 slov)", „3 oblasti — ikona + věta", „CTA tlačítko: <text>"
- ✅ Pozice základních prvků: „logo vlevo nahoře", „hero mockup vedle textu na desktop / pod textem na mobile"

**Jak poznáš porušení:**
- ❌ Dokument obsahuje řádek „Max šířka stránky: 1180–1240 px" → porušení
- ❌ Dokument obsahuje řádek „Padding hero: 96px top, 64px bottom" → porušení
- ❌ Dokument říká „Container: 1200 px, gap 80 px mezi sekcemi" → porušení

**Důvod:** 1.3.10 výstup (test Therapy Air iOn 25.5.2026) měl layout instrukce vrácené do dokumentu i přes jejich odstranění v 1.3.9. AI agent v GHL AI Studio layout sice „dodrží", ale výsledek vypadá jako builder default — protože platforma má vlastní container/grid engine a naše px hodnoty se buď ignorují, nebo kolidují. Layout je výhradně agentova práce.

Pokud detekuješ zakázanou frázi → smaž celou větu/řádek, regeneruj VIZUÁL + KROK 1/KROK 4 sekce **bez layout instrukcí**.

**🚨 FORM-POST-PAYLOAD detector (1.3.15 — KLÍČOVÝ pro mapping):**

Před handoffem v Krok 4 zkontroluj, že KROK 3 v `02-pokyny-landing-kviz.md` obsahuje **explicit pokyny pro Quiz.tsx form post payload** se 3 povinnými pravidly. Bez nich AIQ pole skončí v Unmapped Fields a data nepřitečou do CRM contact:

- ❌ Pokud KROK 3 nemá sekci „KRITICKÉ — Mapping do CRM (form post payload)" → porušení
- ❌ Pokud field keys v Quiz.tsx form data obsahují **`contact.` prefix** (např. `"contact.aiq__X": "Ano"`) → porušení (= GHL parser tečku eskapuje na `__DOT__`, audit log zobrazí „Contact D O T A I Q...", admin UI cosmeticky rozbité)
- ❌ Pokud chybí pokyn vložit do payloadu **`formLabels` objekt** s mapováním `field_key → PLNÝ field name v CRM` (= `"AIQ - [Quiz short name] - " + question_text`, NE jen samotný question text) → porušení
- ❌ Pokud chybí pokyn převést multi-select **array hodnoty na CSV string** PŘED odesláním → porušení
- ✅ KROK 3 obsahuje 3 pravidla: (1) keys BEZ `contact.` prefixu, (2) formLabels s plným field name vč. prefixu `AIQ - [Quiz short name] - `, (3) array-to-CSV reduce + příklad payload struktury

**Důvod:** Série testů Therapy Air iOn 25.–26.5.2026 ukázala 2 nezávislé bugy:

1. **`contact.` prefix v keys:** Quiz.tsx z 1.3.12+ posílal `"contact.aiq__X": "Ano"`. GHL form post parser tečku v `contact.` eskapuje na `__DOT__` (= konflikt s template tag syntax `{{contact.X}}`) → v Form submission details / Contact Details view se zobrazí jako „Contact D O T A I Q -..." (cosmetic, ale rušivé pro klienta). Fix: posílat keys BEZ prefixu — `"aiq__X": "Ano"`.

2. **formLabels jen s question textem:** 1.3.14 instruoval `formLabels[fieldKey] = q.question` (= jen otázka). GHL ale matchuje field_key → CRM custom field tím, že **`formLabels[fieldKey]` MUSÍ PŘESNĚ odpovídat plnému field name v CRM** (= včetně prefixu `AIQ - [Quiz short name] - `). Bez prefixu mismatch → unmapped. Fix: `formLabels[fieldKey] = "AIQ - " + quizShortName + " - " + q.question`.

Pokud KROK 3 neobsahuje všechna 3 pravidla → regeneruj podle template v `references/quiz-implementation.md` (sekce „🚨 KRITICKÉ — Mapping do CRM").

**🚨 ANTI-PASSIVE-AGENT detector v KROK 2 (1.3.13+):**

Před handoffem v Krok 4 zkontroluj, že KROK 2 v `02-pokyny-landing-kviz.md` obsahuje **explicit imperativ pro tvorbu polí** + zákaz ptaní uživatele:

- ❌ Pokud KROK 2 obsahuje formulaci „Field key … si GHL vyřídí samo" / „interní technické nastavení polí si platformní agent vyřídí sám" **bez explicitního „POVINNĚ TEĎ vytvoř"** → porušení (= agent se zeptá uživatele místo jednání, jak ukázal test Therapy Air iOn 25.5.2026)
- ❌ Pokud KROK 2 nemá explicit `NEPTEJ SE uživatele "Mám pole vytvořit?"` + `POKRAČUJ rovnou na KROK 3 bez čekání` → porušení
- ❌ Pokud KROK 2 nemá **check-or-create logiku** (existující pole použij as-is, chybějící vytvoř, neduplikuj) → porušení
- ❌ Pokud KROK 2 nemá explicitní `Pole MUSÍ vzniknout PŘED KROK 3` (= jinak Quiz.tsx posílá data do neexistujících polí = unmapped) → porušení
- ✅ KROK 2 má 5-krokový postup „zkontroluj → vytvoř chybějící → použij existující → oznam jednou zprávou → pokračuj rovnou" + explicit zákaz ptaní + zákaz čekání na user input

**Důvod:** Test Therapy Air iOn 25.5.2026 ukázal, že 1.3.8 ULTRA-SIMPLIFIED formulace „GHL si vyřídí samo" agentovi dala povolení **se ptát uživatele místo jednat**. Agent v AI Studio zapsal field keys do Quiz.tsx (KROK 3), ale pole v CRM fyzicky nevytvořil — pak se zeptal uživatele *„Mám pole přes API vytvořit, nebo už je máš v GoHighLevel připravené?"*. Quiz.tsx by tak posílal data do neexistujících polí = data ztracená. 1.3.13 explicit imperativ tuhle past odstraňuje — agent JEDNÁ, neptá se.

Pokud KROK 2 nemá imperativ + zákaz ptaní + check-or-create logiku → regeneruj podle template v `references/quiz-implementation.md` (sekce „KROK 2 — Custom pole (POVINNĚ TEĎ vytvoř, NEPTEJ SE)").

**(1.3.15 SIMPLIFICATION):** ANTI-OVER-ENGINEERING detector odstraněn — pravidla zahrnuta v FORM-POST-PAYLOAD detector výše (KROK 3 obsahuje POUZE 3 mapping pravidla + seznam otázek + UX + skórování, žádné API endpointy, žádný fieldKey/dataType v KROK 2 — agent vyřídí interně).

Vygeneruj **dva soubory**:

1. **`01-strategie.md`** — strategický dokument pro klienta (segmentace, lead magnet, dotazník, landing, nabídka, follow-up). Template v `{baseDir}/references/output-template.md`, pravidla v `{baseDir}/references/framework.md`. Texty v 01 jsou OK duplikovat s 02 (01 je komplexní strategický pohled, používá se i jinde — sales meetingy, prezentace, postavení strategie).
2. **`02-pokyny-landing-kviz.md`** — **platformově neutrální** pokyny pro AI agenta (v GoHighLevel AI Studio / ScoreApp / Webflow / Typeform / kdekoli). Struktura (1.3.8 ULTRA-SIMPLIFIED): Projekt · KROK 1 Landing · KROK 2 **Custom pole (jen seznam field names)** · KROK 3 **Kvíz (jen seznam otázek + UX)** · KROK 4 Thank you. **Žádné e-mailové sekvence, žádné API instrukce, žádné webhook prefix code.** Template + pravidla naming convention v `{baseDir}/references/quiz-implementation.md`.

   **🔑 KRITICKÁ PRAVIDLA pro `02-pokyny-landing-kviz.md`:**

   - **TYKÁNÍ povinné** — pokyny jdou pro AI agenta v platformě (GHL AI Studio, ScoreApp, Webflow, Typeform), ne pro lidského klienta. Vykání by znělo divně. Druhá osoba jednotného čísla: „vytvoř", „vlož", „nastav", „použij", „přepiš".
   - **Hotové texty, žádné placeholdery k vymýšlení.** Každá sekce landing page / thank you page / kvízu obsahuje **finální copy** — agent v platformě je copy-paste-ready vloží. Žádné `[OVĚŘ S KLIENTEM]`, žádné `[konkrétní hook z 01-strategie.md]`, žádné formuly typu „použij active sloveso + číslo". To je Tvoje (Alex) práce v Krok 3 — vyplnit konkrétní texty z brand kontextu + schváleného názvu. Agent v platformě nemá context, takže texty MUSÍ být kompletní.
   - **Žádná duplikace otázek** — otázky kvízu existují JEN jednou: v Tabulce vlastních polí (s `Možnosti` sloupcem). Sekce KROK 3 — Kvíz neopakuje texty otázek, jen odkazuje: „použij Question text + Možnosti z Tabulky vlastních polí, zachovej pořadí".
   - **Single source of truth** = Tabulka vlastních polí. Field name, Field key, Question text, Typ, Možnosti — vše v jedné tabulce.

**Obě soubory ukládej do folderu `/documents/lead-magnets/AIQ [Quiz title]/`** (folder name vznikl v Krok 2.6 sanitizací **Quiz title** z Krok 2.5 — NE schváleného lead magnet name).

**Klíčové principy napříč dokumentem:**

1. **Sekce 2 (lead magnet)** — varianta + název + typ hooku + 3 měřitelné oblasti („změříme a zlepšíme A, B, C")
2. **Sekce 3 (dotazník)** — struktura podle režimu:
   - **5 otázek ano/ne** — doporučené postupy (generují skóre 0–100 %)
   - **Otevřené kvalifikační otázky** — počet podle režimu:
     - Režim „automatizovaný prodej": **5–10 otázek**, celkem dotazník 10–15
     - Režim „pro osobní setkání": **až 30 otevřených otázek**, celkem dotazník až 35
   - Závěrečná otázka vždy: **otevřený box** „Je něco dalšího, co bychom měli vědět?"
   - **Pořadí kontaktu (kritické pro konverzi):**
     - Krátký kvíz (default 10–15): kontakt **na KONEC** — e-mail gate na konci kvízu konvertuje **40 %+** vs. 5 % na začátku (Interact 2026)
     - Dlouhý kvíz (osobní setkání 35): kontakt **na ZAČÁTEK** — filtr serióznosti
3. **Sekce 4 (landing page)** — 5 sekcí:
   - Hook (Frustrace / Připravenost / Výsledek / Náklady / Vize — podle varianty)
   - Podnadpis („Odpovězte na X otázek a zjistíte…")
   - 3 měřitelné oblasti („změříme a zlepšíme A, B, C")
   - Autorita (kdo vytvořil, výzkum, statistiky)
   - Výzva k akci („Spustit dotazník — X minut, zdarma, okamžitá doporučení")
   - **Cíl konverze 20–40 %** explicitně v dokumentu
4. **Sekce 5 (nabídka)** — Stránka s dynamickými výsledky + nabídka:
   - **Hlavní výsledek** (skóre % / kategorie / čas / čísla / strategické shrnutí podle varianty)
   - **3 klíčové poznatky** per profil
   - **Dynamický další krok** podle odpovědi na otázku o preferovaném řešení (rozpočtový signál). **Otázka má 3 verze podle typu produktu** — digitální (kniha/online/1:1/služba), fyzický (vstupní/standard/premium/kompletní set), hybridní (jen produkt/+ onboarding/+ servis/na klíč). Detail v `references/framework.md`.
5. **Sekce 6 (follow-up)** — 6 e-mailů standardně, Den 3 obsahuje personalizovaný dokument vizualizovaný z dynamického výstupu

### Kontrola na konci generace

- ✅ Všechny otázky dotazníku vykáním
- ✅ Žádné anglicismy v hlavním textu (mimo „CliqSales A.I.Q")
- ✅ **Prvních 5 otázek po kontaktu = ano/ne doporučené postupy**
- ✅ Otevřené kvalifikační otázky následují (5–10 default, až 30 v režimu osobního setkání)
- ✅ Žádné spekulace — chybějící označit `[OVĚŘ S KLIENTEM]`
- ✅ Konec dokumentu **neobsahuje** „implementační kroky" ani „očekávané výsledky"
- ✅ Připomenutí, že AIQ engine personalizuje per kontakt (segmenty jsou jen příklad)
- ✅ Vybraná varianta + režim konzistentně promítnuté do sekcí 2, 3, 4, 5

### Krok 4: Uložení + handoff

Ulož vše do folderu `/documents/lead-magnets/AIQ [Quiz title]/` z Krok 2.6:

```
/documents/lead-magnets/
└── AIQ [Quiz title]/    # např. AIQ Spánkové skóre/, AIQ Audit prodejní cesty/
    ├── 01-strategie.md                    # strategický dokument pro klienta
    ├── 02-pokyny-landing-kviz.md          # platformově neutrální pokyny pro AI agenta
    └── meta.json                          # full metadata kvízu
```

**`meta.json`** struktura:
```json
{
  "lead_magnet_name": "[schválený plný název z Krok 2.6 — marketing hook pro landing H1]",
  "folder_name": "AIQ Skóre kvality spánku",
  "quiz_title": "Skóre kvality spánku",
  "quiz_short_name": "Spánkové skóre",
  "quiz_slug_ascii": "spankove_skore",
  "base_code": "score",
  "variant_name": "Skóre / Osobní hodnocení",
  "mode": "automatizovaný prodej",
  "product_slug": "[slug-tveho-produktu]",
  "product_type": "fyzický",
  "mockup_path": "/documents/lead-magnets/AIQ [Quiz title]/mockup.png",
  "mockup_layout_number": 7,
  "mockup_grid_source": "/documents/brand/visuals/grid-aiq-score-20260517.png",
  "mockup_status": "generated | tbd_missing_brand | tbd_imagegen_failed",
  "created_at": "2026-05-17T..."
}
```

**Uzavři CC task** (task ID jsi uložil z Krok 0.0) — **dva deliverables**:

```bash
# 1. Strategický dokument
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py create-deliverable \
  --task-id <task_id_z_krok_0> \
  --title "AIQ strategie — [produkt] — [Quiz title]" \
  --type report \
  --content-file "/documents/lead-magnets/AIQ [Quiz title]/01-strategie.md" \
  --file-path "/documents/lead-magnets/AIQ [Quiz title]/01-strategie.md" \
  --created-by cso

# 2. Pokyny pro AI agenta (samostatný deliverable — klient ho pošle do AI Studia)
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py create-deliverable \
  --task-id <task_id_z_krok_0> \
  --title "Pokyny pro AI agenta — [Quiz title]" \
  --type report \
  --content-file "/documents/lead-magnets/AIQ [Quiz title]/02-pokyny-landing-kviz.md" \
  --file-path "/documents/lead-magnets/AIQ [Quiz title]/02-pokyny-landing-kviz.md" \
  --created-by cso

# 3. Posuň task do review
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py update-task <task_id_z_krok_0> \
  --status review

# 4. Ověř
python3 /home/node/.openclaw/cs-skills/mc-task-api/scripts/cc_task.py get-task <task_id_z_krok_0>
```

**NEPŘESOUVEJ task do `done` přímo** — to vyžaduje quality review nadřazeného agenta (CEO). API vrátí 403, pokud bys to zkusil.

**🚫 KRITICKÉ — formátování cest v handoff výstupu:**

Cesty v handoff PIŠ JAKO PLAIN TEXT, NIKDY ne v markdown code span (`…` ani ``…``).

**Důvod:** Folder name + soubory v cestě mohou obsahovat speciální znaky (mezery, diakritiku, vícero slov). Při zabalení do markdown code spanu (` `path` ` nebo `` ``path`` ``) chat renderer občas zlomí formátování — viditelný backtick uprostřed cesty, dvojité backticky, poškozené segmenty.

✅ **Správně (plain text):**
```
📄 Dva soubory v: /documents/lead-magnets/AIQ Skóre kvality spánku/
   ├── 01-strategie.md
   ├── 02-pokyny-landing-kviz.md
   ├── meta.json
   └── mockup.png
```

❌ **Špatně (code span — zlomí renderer):**
```
📄 Dva soubory v: `/documents/lead-magnets/AIQ Skóre kvality spánku/`
```

❌ **Špatně (dvojité backticky):**
```
📄 Dva soubory v: ``/documents/lead-magnets/AIQ Skóre kvality spánku/``
```

Stejné pravidlo pro všechny soubory v deliverables seznamu — `01-strategie.md`, `02-pokyny-landing-kviz.md`, `meta.json`, `mockup.png` piš jako plain text odsazený 3 mezerami pod root cestou.

Vypiš handoff:

```
═══════════════════════════════════════════════════════════
✅ AIQ kvíz pro [produkt] — „[Schválený název]" je hotový.

📄 Výstupy v: /documents/lead-magnets/AIQ [Quiz title]/
   ├── 01-strategie.md            ← strategie pro klienta
   ├── 02-pokyny-landing-kviz.md  ← copy-paste do AI Studia
   ├── meta.json                  ← metadata kvízu (orchestrace)
   └── mockup.png                 ← vizuál pro landing hero (pokud Krok 2.7)

Lead magnet: [VARIANTA] — „[NÁZEV]"
   Typ hooku: [Frustrace / Připravenost / Výsledek / Náklady / Vize]
   Konverze cíl: 20–40 %
Dotazník: [N] otázek (kontakt + 5 ano/ne + [N] otevřených)
   Režim: [automatizovaný prodej / pro osobní setkání]
Base code: [score / audit / score2 / ...]  (technický slug pro field key + idempotency)
Skupina v platformě: AIQ — [Produkt] — [Quiz title]
Field name pattern: AIQ - [Quiz short name] - [Plný text otázky]
   (např. „AIQ - Spánkové skóre - Jak dlouho usínáte večer?")

CC tasky: #[task_id] → status review (2 deliverables, čeká na quality review)

Co teď?
  1️⃣  Otevřít 01-strategie.md a projít s klientem
  2️⃣  Poslat 02-pokyny-landing-kviz.md AI agentovi v platformě
      (GoHighLevel AI Studio, ScoreApp, Webflow, Typeform, ...)
  3️⃣  Pro stejný produkt další lead magnet? Spusť skill znovu —
      založí nový folder „AIQ [další Quiz title]/" vedle aktuálního
═══════════════════════════════════════════════════════════
```

## Output

```
/documents/lead-magnets/
├── AIQ [Quiz title kvízu A]/         # např. AIQ Spánkové skóre/
│   ├── 01-strategie.md                    # strategický dokument pro klienta
│   ├── 02-pokyny-landing-kviz.md          # platformově neutrální pokyny pro AI agenta
│   └── meta.json                          # quiz metadata (incl. product_slug)
└── AIQ [Quiz title kvízu B]/         # např. AIQ Audit prodejní cesty/
    ├── 01-strategie.md
    ├── 02-pokyny-landing-kviz.md
    └── meta.json
```

Jeden produkt = více kvízů. Každý kvíz má **vlastní top-level folder** pojmenovaný podle schváleného lead magnet názvu. Vazbu kvízu na produkt drží `meta.json.product_slug` (folder hierarchie už produkt neviditelně neukrývá).

## Reference

- `{baseDir}/references/dynamic-lead-magnet-types.md` — **5 variant** dynamického lead magnetu (detail + kdy kterou)
- `{baseDir}/references/framework.md` — metoda hodnotící karty, kvalifikační otázky, dynamické výsledky, integrace s AIQ
- `{baseDir}/references/output-template.md` — markdown template strategického dokumentu (`01-strategie.md`)
- `{baseDir}/references/quiz-implementation.md` — naming convention vlastních polí + template pokynů pro AI agenta (`02-pokyny-landing-kviz.md`)
- `{baseDir}/references/brand-context-loader.md` — 3-way vstup (Product DNA / manuální / URL)
- `{baseDir}/references/mockup-recipes.md` — prémiový mockup lead magnetu (Krok 2.7): reference hierarchie, per-varianta prompt template, 3:4 vertikál grid 4×4, anti-AI-slop checklist, primary + fallback image_generate

## Důležitá pravidla

1. **Každé nové zadání = nový CC task** (Krok 0.0). Bez tasku neprocházejí výstupy standardním lifecycle (deliverable + quality review). Task se posune do `review` v Krok 4 po vytvoření **2 deliverables** (strategie + pokyny pro AI agenta), do `done` pouze nadřazený agent přes quality review.
2. **Folder name = `AIQ [Quiz title]`** (top-level v `/documents/lead-magnets/`). Žádné product-slug ani quiz-slug subfoldery. Vazbu na produkt drží `meta.json.product_slug`. Base_code (`score`/`audit`/...) je technický identifikátor pro field key prefix + idempotency CC tasku, **ne pro folder strukturu** (Krok 2.5).
3. **Dva výstupní soubory.** `01-strategie.md` = strategie pro klienta (s e-maily). `02-pokyny-landing-kviz.md` = **platformově neutrální** pokyny pro AI agenta (jen landing + pole + kvíz + thank you, ŽÁDNÉ e-maily, ŽÁDNÉ CRM-specific zmínky).
4. **Naming convention vlastních polí — 3 vrstvy identifikace:**

   - **Field name** (Contact Details + webhook key): `AIQ - [Quiz short name] - [CELÝ TEXT OTÁZKY]`
     - S diakritikou, plné znění otázky 1:1 (= question text v kvízu)
     - Bez stropu znaků (GHL nemá rigid limit)
     - Příklad: `AIQ - Dýcháte čistý vzduch - Vnímáte v některých místnostech zhoršený vzduch, prach nebo pachy?`

   - **Field key (slug)** (GHL template tagy + REST API filter): `aiq_[quiz_slug]_[max 3 slova z otázky]`
     - ASCII snake_case, bez diakritiky
     - **Vždy obsahuje quiz_slug** (filtrovatelné napříč všemi poli kvízu)
     - **Max 3 slova** v otázkové části (sémantická esence, ne celá otázka)
     - Příklad: `aiq_dychate_cisty_vzduch_zhorseny_vzduch_pachy`

   - **Question text** (v kvízu pro návštěvníka) = Field name po prefixu `AIQ - [Quiz short name] - ` (identické s plnou otázkou)

   **Quiz short name** (lidsky, ve Field name): krátká esence schváleného názvu lead magnetu z Krok 2.6 (max ~25 znaků, s diakritikou OK). **Quiz slug** (ASCII, ve Field key): odvozen z Quiz short name přes transliteraci → lowercase + snake_case.

   **Důvod 3 vrstev:** Field name nese plný kontext pro model v automatizaci (n8n/Make), Field key je čitelný v template tagách `{{contact.X}}` a filtrovatelný přes API, Question text v kvízu zachovává plné lidské znění pro návštěvníka.

   **Folder strategy:** GHL API neumí specifikovat folder při tvorbě pole → pole spadnou do default „Additional Info" → veškerá identifikace kvízu je vmáčknutá do field name a field key, ne do folderu.

   Pole se vytváří v platformě **PO kvízu** (KROK 3 v pokynech, 1.3.2+) přes API. **Field key se posílá explicit v POST /customFields request body** (`name` + `fieldKey` + `dataType` + `options`), ne přes UI s destruktivním auto-slugem. Detail v `references/quiz-implementation.md` KROK 3.
5. **USP keyword v každém názvu lead magnetu = POVINNÉ.** Každý pracovní i finální název (Krok 2 + Krok 2.6) musí obsahovat hlavní USP / mechanismus / diferenciátor z Product DNA `## 1. ESENCE`. USP = unikátní mechanismus / technologie / metodika, kterou produkt řeší problém — bez ní je název generický a může se týkat libovolného konkurenčního řešení. Příklady napříč doménami: specifická terapeutická technologie (wellness), konkrétní AI funkce (B2B SaaS), unikátní metodika (kurz / konzultace), patentovaná surovina (e-commerce). Test: pokud z názvu odstraníš USP keyword, mělo by zbýt něco, co se může týkat libovolného konkurenčního řešení → název je slabý. Pravidlo platí jako 4. povinné kritérium vedle: konkrétní výsledek + číslo/čas + emoční náboj. Detail v `references/framework.md` Krok 2.6.
6. **Dynamický lead magnet ≠ statické PDF.** Tento skill nedělá checklist ani ebook — dělá self-assessment dotazník s dynamickým výstupem per kontakt.
7. **Pořadí kontaktního formuláře:**
   - **Krátký kvíz (10–15 otázek, default):** kontakt jako POSLEDNÍ krok před thank you. Konverze e-mail gate na konci = **40 %+** vs. 5 % na začátku (Interact 2026).
   - **Dlouhý kvíz (až 35 otázek, pro osobní setkání):** kontakt na ZAČÁTEK jako filtr serióznosti.
   Detail v `references/framework.md` sekce 3.
8. **Prvních 5 otázek ze 13–15 = vždy ano/ne** (doporučené postupy), generují skóre. Pak otevřené kvalifikační. Pak kontakt (u krátkého).
9. **Limit otázek:** 10–15 default / až 35 v režimu „pro osobní setkání".
10. **Závěrečná otázka vždy otevřený box** („Je něco dalšího, co bychom měli vědět?") — kvalifikační zlato.
11. **Otázka o preferovaném řešení musí dávat klientovi smysl podle typu produktu.** Pro fyzický produkt nikdy nenabízej „1:1 koučink"; pro online kurz nikdy „vstupní balíček". Tři verze otázky (digitální / fyzický / hybridní) — detail v `references/framework.md`.
12. **Thank you page má pevný klíčový text:** „⏳ Připravujeme na pozadí vaši pokročilou analýzu — postavenou přesně na vašich odpovědích. Váš personalizovaný [název magnetu] vám pošleme do 5 minut do e-mailu." MUSÍ být viditelný hned po načtení stránky (nad fold).
13. **Vykání v dotazníku** — povinné.
14. **Žádné anglicismy** v hlavním textu (kromě „CliqSales A.I.Q", „funnel", „hook"). „CTA" → „výzva k akci", „insights" → „klíčové poznatky", „best practice" → „doporučený postup", „next step" → „další krok".
15. **Žádné spekulace** — kde chybí data, `[OVĚŘ S KLIENTEM]`.
16. **AIQ engine personalizuje per kontakt** — vždy v dokumentu připomenout, že segmenty jsou jen ilustrativní.
17. **Konec dokumentu = závěr strategie**, žádné „příští kroky".
