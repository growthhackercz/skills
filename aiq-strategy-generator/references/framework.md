# AIQ Framework — metodologie + pravidla generace

Spojuje dva frameworky:
1. **CliqSales A.I.Q** — 3 pilíře ultrapersonalizace (lead → prodej → follow-up)
2. **Metoda hodnotící karty** — ověřený framework (hook na landing, dotazník s 5 otázkami ano/ne + otevřené kvalifikační, dynamická výsledková stránka)

Detail per varianta lead magnetu v `dynamic-lead-magnet-types.md`.

---

## Tři pilíře CliqSales A.I.Q

1. **Ultrapersonalizovaný proces pro získání kontaktů** — dynamický lead magnet (self-assessment dotazník) přizpůsobený každému návštěvníkovi. Z odpovědí vzniká 360° profil.
2. **Ultrapersonalizované prodejní materiály** — adaptivní prodejní stránka + prezentace, která zná každého klienta v reálném čase.
3. **Ultrapersonalizovaný follow-up** — adaptivní sekvence e-mailů/SMS/WhatsApp + personalizovaný „vize budoucnosti" dokument per kontakt.

**Klíčový princip:** segmenty v dokumentu jsou **jen příklad**. Engine personalizuje per individuální kontakt. Vždy v dokumentu připomenout.

---

## 8 personalizovaných prvků, které musí dotazník vytěžit

Z odpovědí musíme generovat per kontakt:

| # | Prvek | Z které části dotazníku |
|---|-------|--------------------------|
| 1 | Nadpis | Otázka o současné situaci + otázka o cíli |
| 2 | Podnadpis | Otázka o situaci + 5 otázek ano/ne |
| 3 | Top 3 benefity | Otázka o cíli — priority |
| 4 | Top 3 problémy | 5 otázek ano/ne + otázka o překážce |
| 5 | Vize bez řešení | Otázka o překážce + neúspěšné doporučené postupy |
| 6 | Vize s řešením | Otázka o cíli + úspěšné doporučené postupy |
| 7 | Top 3 námitky | Otázka o překážce + závěrečný otevřený box |
| 8 | 5 důvodů, proč se rozhodnout | Otázka o preferovaném řešení + kombinace všech |

Každá otázka v dotazníku musí přispívat alespoň k jednomu prvku. Jinak je nadbytečná.

---

## SEKCE 1: Cílová skupina a segmentace

### Co tahnout z kontextu (Brand DNA / manuál / URL)

| Co potřebuju | Z Brand DNA | Z manuálu / URL |
|--------------|-------------|------------------|
| Demografie ideálního klienta | `## 2. IDEÁLNÍ ZÁKAZNÍK` → „Kdo je" | Z textu o cílovce, koho oslovují |
| Bolesti / frustrace | `## 2.` → „Co ho trápí" | Z benefitů produktu (problém, který řeší) |
| Co publikum hledá | `## 2.` → „Co hledá" | Z popisu produktu, nadpisu |
| Typické výroky / jazyk | `## 2.` → „Typické výroky" | Z testimoniálů, často kladených otázek |
| Hlas + slovník | `## 5. HLAS ZNAČKY` | Z tonality produktové stránky |

Pokud chybí → `[OVĚŘ S KLIENTEM: …]`.

### 3 ilustrativní segmenty

**Psychografické, ne demografické.** „Muži 40+" je špatně. Dobré osy:

- **Fáze problému:** „Teprve tuší" / „Aktivně hledá" / „Porovnává nabídky"
- **Velikost kontextu:** „Solo" / „Tým 2–10" / „Větší firma"
- **Hlavní motivace:** „Ušetřit čas" / „Růst" / „Krizově zachránit"
- **Zkušenost s tématem:** „Nikdy" / „Zkoušel a nezafungovalo" / „Mám něco, chci lepší"

Pro každý segment: charakteristiky / specifické potřeby / komunikační styl / preferované řešení.

Vždy připomenout: **segmenty jsou jen příklad** — engine personalizuje per kontakt.

---

## SEKCE 2: Dynamický lead magnet

Detail per varianta v `dynamic-lead-magnet-types.md`. V dokumentu uveď:

- **Vybraná varianta** (1 z 5) — 1 věta proč
- **Název** — **schválený uživatelem v Krok 2.6** (viz pravidla níže). Toto je hlavní marketingový název pro landing page hook (plné znění).
- **Quiz short name** (= zkrácená verze schváleného názvu pro Field name prefix) — esence v 2–4 slovech bez otazníku. Detail níže.
- **Typ hooku** (Frustrace / Připravenost / Výsledek / Náklady / Vize) + příklad nadpisu
- **Hlavní slib** — co klient dostane za X minut
- **Primární bolest** — kterou bolest řešíme (z kontextu)
- **3 měřitelné oblasti** (benefit-oriented — viz Sekce 4 pravidla)
- **Dynamický výstup** — co konkrétně klient po vyplnění uvidí (skóre / audit / plán / čísla / strategický plán)
- **Komunikační úhel + shrnutí**

### Quiz title = zkrácená esence hooku

**Quiz short name** musí být:
- **Esence schváleného názvu / hooku** (ne brand name, ne typ varianty)
- 2–4 slova, max ~25 znaků
- S diakritikou OK (jen ve Field name UI), ASCII slug pro Field key
- **Sémanticky propojený s landing page hookem** — když uživatel vidí Field name v Contact Details (`AIQ - [Quiz short name] - …`), musí okamžitě poznat, ze kterého kvízu data jsou

✅ **Silné příklady:**
| Schválený název (z Krok 2.6) | Quiz short name | Quiz slug (ASCII) |
|---|---|---|
| „Pořád utíráte prach a pořád ho máte zpátky?" | `Domácí prach test` | `domaci_prach_test` |
| „Jste připraveni na 30 dní bez bolesti zad?" | `30 dní bez bolesti` | `30_dni_bez_bolesti` |
| „Kolik vás stojí pomalá odezva na leady?" | `Cena pomalých leadů` | `cena_pomalych_leadu` |

❌ **Slabé (anti-pattern):**
- `[Brand] Skóre` (jen brand + typ varianty — žádný hook)
- `[Produkt] Test` (brand bez benefitu)
- `[Služba] Audit` (interní název)

**Pravidlo:** Quiz short name převzít hlavní **benefit nebo hook keyword** z názvu (Krok 2.6), ne brand. Brand identifikuje folder, hook identifikuje kvíz.

### Pracovní (předběžný) název v Krok 2 — pravidla

**V Krok 2 (výběr varianty) skill prezentuje u každé varianty 1 PŘEDBĚŽNÝ (pracovní) název** jako preview marketingového tónu. Uživatel díky tomu hned vidí, jak by konkrétně mohla varianta znít, a snadno se rozhodne o typu kvízu.

**Pravidla pro pracovní název:**

1. **1 návrh per varianta** (5 variant = 5 pracovních názvů v Krok 2 výstupu)
2. **Prochází VŠEMI 4 povinnými kritérii** (stejně jako finální názvy v Krok 2.6):
   - Konkrétní výsledek (kvantifikovaný)
   - Specifické číslo / čas
   - Emoční náboj (frustrace NEBO curiosity gap)
   - **USP / mechanism keyword z Product DNA** = unikátní mechanismus / technologie / metodika produktu (např. pro wellness produkt specifická terapeutická technologie; pro B2B SaaS konkrétní AI funkce; pro online kurz unikátní metodika; pro e-commerce patentovaná surovina / složení)
3. **Hook formula odpovídá variantě:**
   - Skóre → typ Frustrace default (pro produkty s opakovanou bolestí) / Připravenost
   - Audit → Frustrace / Náklady
   - Plán → Výsledek / Připravenost
   - Kalkulačka → Náklady / Příležitost
   - Strategický plán → Vize
4. **Označení jako PŘEDBĚŽNÝ** — výstup MUSÍ jasně říct, že to je pracovní preview, nikoli finální volba:
   ```
   📝 PŘEDBĚŽNÝ NÁZEV (finální vybereme v Krok 2.6)
      „[pracovní název]"
      POZOR: toto je jen preview, abys viděl, jaký marketing
      tón tahle varianta nese. V dalším kroku vybereme z 10
      finálních.
   ```
5. **Anti-pattern:** stejný checklist jako pro finální názvy v Krok 2.6 (žádná obecná otázka, žádné „lepší/efektivnější", > 60 znaků, korporátní žargon)

6. **Brand name vs. USP / mechanism — preferuj mechanism, ne brand** (stejné pravidlo jako Krok 2.6 pravidlo 8):

   AIQ lead magnet je primárně **top-of-funnel cold akvizice** — návštěvník brand v této fázi typicky nezná. Pracovní název musí prodávat užitek/mechanism (USP), ne brand.

   ⚠️ V pracovním názvu **by neměl být specifický oficiální obchodní název produktu / služby** (např. „Bioptron", „Aqueena Pro", „CliqSales AI Team"). USP keyword z Product DNA (mechanism / technologie / metodika) ano, brand name raději ne.

   **Test substituce:** Zaměň brand v návrhu za `[produkt]`. Pokud věta zní hloupě nebo vyžaduje brand pro pochopení („co získáte s čistou vodou z [produkt]") → přepiš na variantu s mechanismem („co získáte s **domácí filtrací**").

   ✅ Preferuj (mechanism): „Spočítejte si, kolik vás doma stojí balená voda — a co vrátí domácí filtrace"
   ⚠️ Raději ne (brand): „Spočítejte si, kolik vás doma stojí balená voda — a co získáte s Aqueena Pro"

   **Výjimka:** kvíz určený výhradně pro warm/retargeting publikum může brand obsahovat. Pro default AIQ skill (cold akvizice) preferuj mechanism. Detail v Krok 2.6 pravidlo 8.

### Tvorba finálního názvu lead magnetu (Krok 2.6) — pravidla

**Skill v Krok 2.6 vygeneruje přesně 10 silných marketingových názvů** a počká na uživatelovu volbu. Název je **nejdůležitější CR páka** lead magnetu, proto vlastní STOP bod. **10 návrhů zaručuje široký výběr** napříč kategoriemi a tonalitami.

**Pracovní název z Krok 2 patří mezi 10 návrhů** (typicky jako 1. = doporučený), ale zbylých 9 musí pokrýt mix 5 kategorií + různé úhly. Uživatel může pracovní název z Krok 2 přímo vybrat („vezmu pracovní"), zvolit jiný z 10, nebo navrhnout úpravu.

#### Pravidla pro generaci názvů

**🔴 4 povinná kritéria + 1 podmíněné — každý z 10 návrhů musí splňovat všechna 4 současně:**

1. **Konkrétní výsledek se SMYSLOVÝM OBRAZEM** — co konkrétně klient zažije / uvidí / pocítí. Ne abstraktní benefity jako „úleva", „klid", „regenerace", „smysl", „pohoda", „harmonie" — ty jsou popisné, ne pull.
   - ✅ „vstávat ráno bez bolesti zad"
   - ✅ „spát celou noc bez probouzení"
   - ✅ „chodit dva dny v kuse bez tabletky"
   - ❌ „pro větší úlevu a klid" / „pro bolest, hojení a regeneraci"
2. **Specifické číslo nebo čas** — `5 chyb`, `7 návyků`, `4 minuty`, `30 dní`, `90 dní`, `prvních 100`. Bez čísel = slabý název.
3. **Emoční náboj** — alespoň jeden z:
   - **Pojmenovaná opakovaná bolest s detaily** („5 let bolesti zad", „každé ráno ztuhlost", „po hodině chůze bolest kolen")
   - **Counter-intuitive / paradox kontrast** („Léky, masti, rehabilitace — a stejně to bolí")
   - **Specifický cost kontrast** („Než zaplatíte další rehabilitaci za 8 000 Kč…")
   - **Curiosity gap s konkrétním slibem** („Tady jsou 3 důvody, proč…")
   - ❌ Anti-pattern: „úleva", „klid", „smysl", „pohoda", „pomoci" jako jediný emoční pull → zamítnout
4. **Konzistence s vybranou variantou — klíčová slova jen z té varianty:**

   | Vybraná varianta | Povolená klíčová slova v názvu |
   |---|---|
   | Skóre | „test", „skóre", „zjistěte za X min", „otestujte" |
   | Audit | „audit", „diagnostika", „analýza" |
   | Plán / Harmonogram | „plán", „harmonogram", „N denní" |
   | Kalkulačka | „spočítejte", „kolik vás stojí", „kalkulačka" |
   | Strategický plán na míru | „strategie", „strategický plán", „plán na míru", „blueprint" |

   **Zákaz mixu:** v návrhu pro Strategický plán nepoužívej „spočítejte" (Kalkulačka) ani „test za 4 min" (Skóre). Mix klíčových slov → ZAHOĎ návrh.

**5. USP / mechanism keyword — DOPORUČENÉ, ne povinné v každém:**
   - Z Product DNA `## 1. ESENCE PRODUKTU` → USP fráze = hlavní mechanismus / metodika / technologie produktu (např. v doméně wellness specifická terapeutická technologie; v B2B SaaS konkrétní AI funkce; v online vzdělávání unikátní metodika; v high-ticket konzultaci pojmenovaný framework)
   - **Doporučení:** 6–8 z 10 návrhů obsahuje USP keyword (silně směřuje k prodeji, návštěvník hned ví, co produkt dělá)
   - **2–4 návrhy mohou USP vynechat**, pokud jsou silný **clickbait s emotional pull**, který i bez USP **jasně směřuje k prodeji** (např. „5 let bolesti zad? Tady je váš plán." — bez USP, ale stále jasně směřuje k řešení)
   - **Test:** Když USP keyword chybí, musí být v názvu silný emocionální nebo curiosity hook, který sám o sobě stačí na klik. Jinak je název generický → zahoď.

**Pokud návrh nesplňuje 1+2+3+4 (=4 povinná kritéria) → ZAHOĎ a zkus jiný.** Lepší 10 vyladěných než 10 vlažných.

#### Další pravidla

1. **První varianta = „Doporučeno"** + 1 věta zdůvodnění, proč je nejsilnější pro tento brand+produkt+publikum
2. **10 názvů s povinným mixem 5 kategorií** (2 návrhy per kategorie) — **každá kategorie má specifickou tonalitu**:
   - **Výsledkový (2×) — SMYSLOVÝ obraz výsledku, ne abstraktní benefit:**
     - ✅ „Vstávat ráno bez bolesti zad — váš plán [USP] pro celou rodinu" (wellness)
     - ✅ „Otevřít pondělí 10 nových leadů — váš 30denní plán [USP]" (B2B SaaS)
     - ❌ „30denní strategie pro úlevu a klid" (úleva a klid = abstraktní)
   - **Zvědavostní (2×) — KONKRÉTNÍ slib v otázce, ne generic curiosity:**
     - ✅ „Které 3 chyby brzdí váš obrat? Audit prodejního procesu odhaluje za 4 min"
     - ❌ „Dává vám [vaše řešení] smysl?" (generic, žádný slib)
   - **Bolestní (2×) — POJMENOVANÁ opakovaná bolest s detaily, ne generic „bolest":**
     - ✅ „5 let stagnujícího obratu, žádné řešení? Plán [USP] na míru vaší firmě"
     - ❌ „Pořád to nejde? Vytvořte si plán" (bolest bez specifika)
   - **Autoritní (2×) — KONKRÉTNÍ číslo / autor / výzkum, ne generic „3 kroky":**
     - ✅ „Strategie [USP] podle ověřené metodiky — 7 týdnů, 1 200+ klientů"
     - ❌ „Strategie ve 3 krocích" (bez konkrétna)
   - **Urgentní/cenový (2×) — COUNTER-INTUITIVE / PARADOX kontrast:**
     - ✅ „Marketing, ads, kampaně — a leady pořád nepřibývají. Plán [USP] na 30 dní."
     - ✅ „Než zaplatíte další konzultaci za 8 000 Kč: spočítejte [USP plán]"
     - ❌ „Kolik vás stojí status quo" (vágní)
3. **Délka 25–60 znaků** — kratší skóruje lépe na mobilu. Sweet spot **4–7 slov**.
4. **Hlas přesně podle Brand DNA** (`## 5. HLAS ZNAČKY` — slova, která definují / slova, kterým se značka vyhýbá)
5. **Per varianta** lead magnetu musí název odrážet typ:

   | Varianta | Klíčová slova v názvu |
   |---|---|
   | Skóre / Osobní hodnocení | „test", „skóre", „hodnocení", „audit X postupů" |
   | Diagnostický audit | „audit", „diagnostika", „analýza" |
   | Personalizovaný plán / Harmonogram | „plán", „harmonogram", „roadmap", „90 dní" |
   | Kalkulačka přínosů | „kalkulačka", „kolik vás stojí", „spočítejte si" |
   | Strategický plán | „strategický plán", „blueprint", „plán na míru" |

6. **Mechanismus / USP v titulu — pravidlo „když je to differentiator, patří tam":**
   - **PATŘÍ do titulu**, pokud je to **brand differentiator / USP** z Product DNA `## 1. ESENCE` — unikátní mechanismus / technologie / metodika, kterou produkt řeší problém (např. specifická terapeutická technologie ve wellness, konkrétní AI funkce v B2B SaaS, pojmenovaný framework v konzultaci). V tomto případě je USP keyword **povinný** (viz 4. kritérium výše).
   - **NEPATŘÍ do titulu**, pokud je to jen technický mechanismus bez prodejní hodnoty (např. „algoritmus K-means" v marketing tool, „LLM agent stack" v B2B SaaS pro nemarketéry).
   - **Rozlišovací test:** Pokud bez tohoto slova název ztrácí smysl pro cílovku (návštěvník neví, k čemu jde) nebo se může týkat libovolného konkurenčního řešení → je to USP/differentiator → **patří do titulu**.
7. **Žádné anglicismy** (kromě zavedených, které brand používá)

8. **Brand name vs. USP / mechanism — preferuj mechanism, ne brand:**

   **Kontext:** AIQ lead magnet je primárně **top-of-funnel cold akvizice**. Návštěvník v této fázi typicky brand nezná — landing page kvízu je často prvním kontaktem. Hook tedy potřebuje prodávat **užitek / mechanism (USP)**, ne brand, protože:

   - Cold publikum brand nemá kontext → CTR drop u hooku závislého na brand awareness
   - Hook s mechanismem („domácí světelná terapie", „AI prodejní automatizace") osloví i lidi hledající *řešení*, kteří o brandu nikdy neslyšeli
   - Brand žije na landingu jako autorita („Vytvořeno [brand], 1 200+ klientů"), ne v hooku magnetu

   **Pravidlo:** V pracovním názvu (Krok 2) i v 10 finálních návrzích (Krok 2.6) by **neměl být specifický oficiální obchodní název produktu / služby** (např. „Bioptron", „Aqueena Pro", „CliqSales AI Team"). USP keyword z Product DNA (mechanism / metodika / technologie) ano, brand name raději ne.

   ✅ Preferuj (mechanism): „Test vhodnosti světelné terapie: zjistěte za 4 minuty, jestli vám sedí"
   ⚠️ Raději ne (brand v hooku): „Test vhodnosti světelné terapie: jestli Bioptron dává smysl právě pro vás"

   **Test:** Zaměň brand v návrhu za placeholder `[produkt]`. Pokud věta zní hloupě nebo vyžaduje brand pro pochopení („jestli [produkt] dává smysl") → název je závislý na brand awareness → přepiš na variantu s mechanismem.

   **Výjimka:** Kvíz určený výhradně pro **warm publikum / retargeting** (existující zákazníci, návštěvníci brand stránek) může brand v názvu obsahovat — brand awareness existuje. Pro **default AIQ skill (cold akvizice)** preferuj mechanism.

#### Anti-pattern checklist — automaticky zamítnout název pokud

- ❌ Je to **obecná otázka bez konkrétního výsledku** („Dýcháte čistý vzduch?" / „Máte úspěšný marketing?")
- ❌ Obsahuje slovo **„lepší / efektivnější / kvalitnější / vyšší úroveň"** bez čísel
- ❌ Délka **> 60 znaků** (rozpadne se na mobilu)
- ❌ **Bez emočního ani curiosity hooku** (popisné konstatování typu „Skóre vaší marketingové strategie")
- ❌ Obsahuje **korporátní žargon** („synergie", „optimalizace", „transformace", „synergický")
- ❌ Slibuje **vágně** („zlepšete váš X", „získejte vhled do Y", „pomoci právě vám", „pro pohodu")
- ❌ **Bez čísla, času ani konkrétní položky** — pouze stav („Jste profík v Y?")
- ❌ **Pouze abstraktní benefity** jako emoční pull („úleva", „klid", „regenerace", „smysl", „pohoda", „harmonie") bez smyslového obrazu — to nejsou pulls, jsou to popisy
- ❌ **MIX klíčových slov z více variant** — např. „spočítejte plán" v návrhu pro Strategický plán (mix Kalkulačka + Plán) → ZAHOĎ
- ❌ **Bez USP a zároveň bez silného clickbait emotional pull** — pokud nemá USP keyword, MUSÍ mít silný emoční hook, který sám o sobě stačí na klik
- ⚠️ **Obsahuje oficiální brand name** (např. „Bioptron", „Aqueena Pro") — raději přepiš na USP/mechanism (viz pravidlo 8 výše). Brand patří na landing page jako autorita, ne do top-funnel hooku. Výjimka jen pro warm/retargeting kvízy.

Před prezentací 10 návrhů uživateli **provětej každý návrh přes anti-pattern checklist**. Kdo neprojde → zahoď a vygeneruj náhradu.

#### Formát výstupu — 10 návrhů, seskupené po 2 per kategorie

```
═══════════════════════════════════════════════════════════
NÁZEV LEAD MAGNETU — vyber 1 z 10 návrhů
═══════════════════════════════════════════════════════════

VÝSLEDKOVÉ (zaměřeno na konkrétní dosažitelný cíl)
 1. 🎯 [DOPORUČENO] „[název 1]"
    Proč: [1 věta zdůvodnění, proč je tahle nejsilnější pro brand+produkt]
 2. „[název 2]"

ZVĚDAVOSTNÍ (otevírá smyčku, vyvolává touhu zjistit)
 3. „[název 3]"
 4. „[název 4]"

BOLESTNÍ (pojmenovává frustraci, kterou cílovka prožívá)
 5. „[název 5]"
 6. „[název 6]"

AUTORITNÍ (opírá se o expertízu, výzkum, počty klientů)
 7. „[název 7]"
 8. „[název 8]"

URGENTNÍ / CENOVÉ (kvantifikuje cenu zbytečnosti / nečinnosti)
 9. „[název 9]"
10. „[název 10]"
```

Po prezentaci **STOP — vyčkej na uživatele:**

> *„Který název tě oslovuje? Můžeš vybrat číslo, citovat jeden z nich, nebo navrhnout úpravu existujícího (např. 'jednička, ale '30 dní' místo '7 dní')."*

⚠️ **NEPOKRAČOVAT na Krok 3 bez explicitního výběru názvu.**

#### Příklady silných názvů per varianta (rotace 5 domén)

Každá varianta dostane 1 příklad z odlišné domény, aby AI při generaci nevybírala vždy z jednoho slovníku. Při tvorbě 10 návrhů v Krok 2.6 přizpůsob slovník konkrétní doméně z Product DNA — tyto příklady jsou jen šablona patternu.

**Skóre / Osobní hodnocení (doména: wellness — fyzický produkt řešící chronickou bolest):**
- 🎯 „Test 10 návyků pro bezbolestné dny doma s [USP]"
- „Jste připraveni na 30 dní bez bolesti zad?"
- „Skóre vaší domácí regenerace"
- „90vteřinový audit vaší léčby"
- „5 návyků, které měníte na bolest. Otestujte se."

**Diagnostický audit (doména: B2B SaaS / služba):**
- 🎯 „Audit prodejního procesu: kde tečou peníze v roce 2026"
- „Diagnostika 18 oblastí vaší prodejní cesty"
- „Proč nerostete v obratu, přestože investujete do marketingu"

**Plán / Harmonogram (doména: online kurz / mentoring):**
- 🎯 „Váš 90denní plán k prvnímu milionu"
- „30 dní k vyšší konverzi: plán krok za krokem"
- „Harmonogram 12 týdnů, jak nastartovat [konkrétní cíl studenta]"

**Kalkulačka přínosů (doména: e-commerce / fyzické zboží):**
- 🎯 „Kalkulačka úspor: kolik vám ročně vrátí přechod na [USP] suroviny"
- „Spočítejte si návratnost [produktu] za 12 měsíců provozu"
- „Kolik vás ročně stojí ruční variantní řešení místo [USP]"

**Strategický plán (doména: high-ticket konzultace / agentura):**
- 🎯 „Váš strategický plán škálování z 10M na 100M"
- „Blueprint [USP framework] transformace pro vaši firmu"
- „Personalizovaný plán enterprise růstu na 3 roky"

---

## SEKCE 3: A.I.Q dotazník — struktura

### Pořadí kontaktu — záleží na režimu kvízu

**🔑 Klíčové pro konverzi:** Pořadí kontaktního formuláře vs. obsahových otázek **dramaticky ovlivní completion rate**. Pravidlo:

| Režim | Kontakt | Konverze e-mail gate | Logika |
|---|---|---|---|
| **Krátký kvíz** (default, 10–15 otázek) | **NA KONEC** (poslední krok před thank you page) | **40 %+** | Po 90 s investice do otázek je člověk zvědavý na výsledek a dá e-mail výměnou za personalizovanou analýzu |
| **Dlouhý kvíz** (osobní setkání, až 35 otázek) | **NA ZAČÁTEK** (první krok) | 10–20 % | Dlouhý kvíz je sám filtr serióznosti — kontakt na začátku odsejne casual visitors, zbydou jen kvalifikovaní |

**Zdroj:** Interact Quiz Conversion Rate Report 2026 — email gate na konci kvízu konvertuje cca **8× lépe** než na začátku (40 % vs. 5 %).

### Kontaktní obrazovka (pole)

Bez ohledu na pořadí obsahuje vždy:

- **Jméno** (povinné, system field `first_name`)
- **E-mail** (povinné, system field `email`)
- **Telefon**:
  - U krátkého kvízu: **volitelné** (neztrácet konverzi)
  - U dlouhého kvízu pro osobní setkání: **povinné** (potřebujeme volat kvalifikovaného leada)

#### Krátký kvíz — kontakt na KONEC

Po poslední obsahové otázce zobraz kontaktní obrazovku s nadpisem:

> *„Skvěle, jste hotoví! Kam máme poslat vaši personalizovanou analýzu?"*
> *„Výsledky vám dorazí do 5 minut do e-mailu."*

Tlačítko: **„Získat moji analýzu"**

#### Dlouhý kvíz — kontakt na ZAČÁTEK

První obrazovka před prvními obsahovými otázkami:

> *„Než začneme, kam vám pošleme vaši personalizovanou strategickou analýzu?"*

Tlačítko: **„Pokračovat na analýzu (X minut)"**

### Část 2 — 5 otázek ano/ne (doporučené postupy) — POVINNÉ

**Vždy přesně 5 otázek ano/ne** o tom, jestli klient dělá 5 nejdůležitějších doporučených postupů ve své oblasti (každé „ano" = 20 % skóre, max 100 %).

**Pravidla pro výběr 5 doporučených postupů:**

- Z Product DNA `## 3. HLAVNÍ BENEFITY` → každý benefit má „Mechanismus" pole → odvod doporučený postup
- Z URL / manuálu → odvod z toho, co produkt dělá / od čeho odrazuje
- Doporučené postupy musí být **konkrétní akce**, ne stavy („Zkoumáte týdně metriky?" ne „Jste úspěšní?")
- **Druhá osoba množná, vykání:** „Měříte X?" / „Sledujete Y?" / „Děláte Z pravidelně?"

**Formát výstupu per otázka:**

```
Otázka N: Děláte/sledujete/máte [konkrétní doporučený postup]?
   Odpovědi: Ano / Ne
   Účel: měření, zda klient aplikuje doporučený postup [N]
   Personalizace: → top 3 problémy (pokud ne), vize s řešením (pokud ano), skóre
```

### Část 3 — Otevřené kvalifikační otázky — POVINNÉ

**Počet podle režimu:**

| Režim | Počet otevřených otázek | Celkem dotazník |
|-------|--------------------------|-----------------|
| **Automatizovaný prodej (default)** | 5–10 | 10–15 |
| **Pro osobní setkání** | až 30 | až 35 |

**Klíčové kvalifikační otázky (vždy zachytit, bez ohledu na režim):**

1. **Současná situace** — kde teď klient je v dané oblasti
   - Default režim: radio (4–5 možností)
   - Pro osobní setkání: otevřená („Popište 2–3 větami, kde teď jste s [oblast]…")
   - Personalizace: → segment, nadpis, podnadpis
   - Účel: segmentace + kvalifikace velikosti

2. **Cíl v 90 dnech** — co je pro klienta nejdůležitější dosáhnout
   - Default režim: radio nebo multiselect (max 2)
   - Pro osobní setkání: otevřená („Jakého hlavního cíle chcete dosáhnout v dalších 90 dnech?")
   - Personalizace: → top 3 benefity, vize s řešením
   - Účel: hlavní motivace

3. **Překážka** — co klientovi brání, nebo co zkusil a nezafungovalo
   - Default režim: radio nebo multiselect (max 3)
   - Pro osobní setkání: otevřená („Co konkrétně vás zatím brzdí? Co jste zkusili?")
   - Personalizace: → top 3 problémy, top 3 námitky
   - Účel: předjímání námitek

4. **Preferované řešení / rozpočet** — co by klientovi vyhovovalo nejvíce ⭐
   - Vždy radio (4 možnosti, v pořadí od nejlevnější po nejdražší)
   - **Obsah možností závisí na typu produktu** (skill detekuje z Product DNA `## 1. Kategorie` nebo z URL/popisu):

   **a) Digitální / informační / služby / kurzy (default):**
     - a) Kniha, článek, video kurz (do 5 000 Kč)
     - b) Online program / kurz (5 000 – 30 000 Kč)
     - c) 1:1 koučink / mentoring (30 000 – 100 000 Kč)
     - d) Služba na klíč / agentura / enterprise (100 000 Kč+)

   **b) Fyzický produkt / e-commerce / zařízení:**
     - a) Vstupní balíček / základní varianta (cena z `## 5.` nejnižší tier)
     - b) Standardní balíček (střední tier)
     - c) Premium balíček (vyšší tier)
     - d) Kompletní set / luxury / B2B množstevní balíček (nejvyšší tier)
     - Pokud Product DNA neobsahuje 4 cenové úrovně, použij 4 rozpětí Kč okolo střední ceny (např. ±30 %, ±60 %, ±100 %)

   **c) Hybridní (fyzický produkt + služba):**
     - a) Jen produkt — bez další podpory
     - b) Produkt + onboarding (instalace, zaškolení)
     - c) Produkt + osobní servis / mentoring
     - d) Kompletní řešení na klíč

   - Účel: **prozradí rozpočet**, určuje dynamický další krok
   - Personalizace: → 5 důvodů, dynamická výzva k akci
   - **Pravidlo:** otázka MUSÍ dávat klientovi smysl. Nikdy nenabízej „1:1 koučink" u fyzického produktu ani „vstupní balíček" u online kurzu.

5. **Závěrečná otevřená otázka** — vždy poslední otázka v dotazníku
   - Otevřené textové pole (max 500 znaků v default, max 2000 v režimu pro osobní setkání)
   - Žádné možnosti — prázdný box
   - Doslovné znění: „Je něco dalšího, co bychom měli vědět?"
   - Personalizace: → custom personalizace, citace vlastním jazykem
   - Účel: nečekané informace o rozpočtu / urgenci / kontextu — **kvalifikační zlato**

### Další kvalifikační otázky v režimu pro osobní setkání

Pokud režim „pro osobní setkání" (až 30 otevřených otázek), doplň dalších 15–25 hlubokých otázek z následujících oblastí:

- **Byznys kontext** — obrat, velikost týmu, fáze růstu, hlavní trh
- **Historie** — co všechno už zkusili, co fungovalo/nefungovalo, jak dlouho problém řeší
- **Vize** — kde se vidí za 1–3 roky, co je důvodem řešit to teď
- **Rozhodovací proces** — kdo rozhoduje, jak rychle, jaký je rozpočet, jaká kritéria
- **Tým a nástroje** — koho mají, co používají, co chybí
- **Aktuální výsledky** — konkrétní čísla (s privacy disclaimerem)
- **Obavy a rizika** — co by mohlo pokazit projekt, jaké mají obavy z investice
- **Motivace** — proč právě teď, co se změnilo
- **Předchozí dodavatelé** — s kým spolupracovali, jak to dopadlo

Všechny otevřené (textové pole), žádné radio. Cílem je předpříprava na konzultační hovor.

### Mapování odpovědí → 8 personalizovaných prvků (tabulka v dokumentu)

Tuto tabulku vždy zařaď na konec sekce 3:

| Personalizovaný prvek | Z které otázky |
|------------------------|-----------------|
| Nadpis | Současná situace + cíl |
| Podnadpis | Současná situace + 5 otázek ano/ne |
| Top 3 benefity | Cíl (priority) |
| Top 3 problémy | 5 otázek ano/ne (kde „ne") + překážka |
| Vize bez řešení | Překážka + neúspěšné doporučené postupy |
| Vize s řešením | Cíl + úspěšné doporučené postupy |
| Top 3 námitky | Překážka + závěrečný otevřený box |
| 5 důvodů | Preferované řešení + kombinace všech |
| **Dynamický další krok** | **Preferované řešení (rozpočtový signál)** |

### Úvodní text dotazníku

Povinné 2–3 věty na první stránce:

1. **Pozvání a motivace** — pozvi k vyplnění, naznače přínos personalizované analýzy
2. **Oznámení o výsledcích** — explicitně, že personalizovaná analýza dorazí na e-mail **do 5 minut** po odeslání

Vzor (přizpůs hlasu z brandu):

> *„Vítejte. Tento dotazník vám pomůže získat personalizovanou analýzu vaší situace — [konkrétní výstup podle varianty]. Vyplnění trvá X minut. Po odeslání vám do 5 minut dorazí kompletní vyhodnocení i s konkrétními doporučeními do e-mailu."*

Vykání. Žádné anglicismy.

---

## SEKCE 4: Lead magnet landing page — struktura

### Struktura LP (vždy 5 sekcí)

**A. HOOK** (top stránky) — **KRITICKÉ PRO KONVERZI**. Hook musí během 3 sekund vzbudit u čtenáře pocit „to je o mně" — buď aktivní touhu řešení, nebo skrytou touhu, kterou hook „probudí". Pět typů formulí + příklady níže:

**Pět typů hooků (česky, jednoslovně, pro výstupy k uživateli):**

| Typ | Co dělá |
|---|---|
| **Frustrace** | oslovuje opakovanou bolest, kterou cílovka prožívá |
| **Připravenost** | ptá se na ochotu k akci („Jste připraveni…?") |
| **Výsledek** | slibuje konkrétní změnu („Získejte X za Y dní") |
| **Náklady** | ukazuje cenu nečinnosti / status quo („Kolik vás stojí…") |
| **Vize** | maluje atraktivní budoucnost („Získejte plán pro X") |

Interní pojmenování (anglicky) v pravidlech níže slouží jen jako reference pro agenta; **ve výstupech k uživateli vždy jen české jednoslovné typy + krátký popis funkce v závorce**.

#### Hook Frustrace (interně Frustration) — formula

```
„Frustruje vás, že [konkrétní nedosažený výsledek],
přestože [konkrétní úsilí, které věnujete]?"
```

✅ **Silné příklady:**
- „Pořád utíráte prach a pořád ho máte zpátky? Otestujte, kde je skutečný zdroj."
- „Spánek vás místo regenerace unavuje, i když chodíte spát včas?"
- „Investujete do marketingu, ale nové zakázky pořád nepřibývají?"

❌ **Slabé příklady (anti-patterns):**
- „Dýcháte čistý vzduch?" (chybí frustrace + úsilí, jen otázka)
- „Trápí vás vzduch doma?" (vágní, žádné konkrétno)
- „Máte problém s prachem?" (jen problém bez kontextu úsilí)

#### Hook Připravenost (interně Readiness) — formula

```
„Jste připraveni na [konkrétní výsledek] za [konkrétní čas]?"
```

✅ **Silné příklady:**
- „Jste připraveni získat prvních 10 zákazníků za 30 dní díky [USP]?"
- „Jste připraveni na 90 dní bez bolesti zad?"
- „Jste připraveni na první milion na účtu do konce roku?"

❌ **Slabé příklady:**
- „Jste připraveni růst?" (žádný výsledek ani čas)
- „Jste připraveni na lepší výsledky?" (vágní)
- „Připraveni na změnu?" (bez specifika)

#### Hook Výsledek (interně Outcome, variace Připravenosti) — formula

```
„Získejte [konkrétní výsledek] za [konkrétní čas] —
i když [obtíže / pochybnost]"
```

✅ **Silné příklady:**
- „Získejte svůj 90denní plán prvního milionu — i když dosud nemáte produkt"
- „Vyrobte si dnes večer první [USP výstup] — i když dosud neumíte [obvyklý předpoklad]"

❌ **Slabé:** „Získejte výsledky" (žádné konkrétno).

#### Hook Náklady (interně Cost) — formula

```
„Kolik vás stojí [status quo], dokud [konkrétní bolest] pokračuje?"
```

✅ **Silné:**
- „Kolik vás stojí pomalá odezva na leady — každý den, který je necháte vychladnout?"
- „Kolik vás ročně stojí ruční follow-up místo automatizace?"

❌ **Slabé:** „Spočítejte si úspory" (jednorozměrné).

#### Hook Vize (interně Vision) — formula

```
„Získejte svůj vlastní plán pro [konkrétní transformace] —
postavený na [konkrétní vlastnost vaší situace]"
```

✅ **Silné:**
- „Získejte svůj vlastní plán nasazení [USP] ve firmě — postavený na vaší konkrétní velikosti týmu a obratu"

❌ **Slabé:** „Vlastní strategie" (bez transformace ani specifika).

#### Mapování varianta → typ hooku (default volba)

| Varianta lead magnetu | Default typ hooku | Alternativní typ |
|---|---|---|
| Skóre / Osobní hodnocení | **Frustrace** (pro opakovanou bolest) | Připravenost |
| Diagnostický audit | **Frustrace** | Náklady |
| Personalizovaný plán | **Připravenost** / Výsledek | Vize |
| Kalkulačka přínosů | **Náklady** | Frustrace |
| Strategický plán | **Vize** | Připravenost |

**Důležité:** Pokud Product DNA / Brand DNA naznačuje opakovanou frustraci publika (např. fyzický produkt řešící chronickou bolest), upřednostni **typ Frustrace**, i když varianta defaultně doporučuje Připravenost. Frustrace konvertuje výrazně lépe u skryté touhy (Scorecard Marketing data: skrytá touha — kterou hook „probudí" — konvertuje líp než aktivní vědomá touha).

**B. PODNADPIS** (pod hookem) — formula

```
„Zjistěte za [X] minut, [konkrétní insight] a [konkrétní akce]
pro [konkrétní výsledek za konkrétní čas]"
```

✅ **Silné příklady:**
- „Zjistěte za 4 minuty, kolik prachu, pylu a alergenů máte doma — a co konkrétně udělat, abyste je snížili o 80 % během 30 dní."
- „Zjistěte za 3 minuty, kde přesně vaše marketingové úsilí ztrácí peníze — a co konkrétně přestat dělat, abyste neztratili dalších 200 000 Kč ročně."

❌ **Slabé (anti-pattern):**
- „Odpovězte na 13 otázek a zjistíte své skóre." (vágní benefit „skóre")
- „Získejte personalizovaná doporučení." (žádný konkrétní výsledek)
- „Otestujte se a získejte plán." (žádné číslo / čas)

**Klíč:** podnadpis musí **kvantifikovat výsledek** (% / Kč / dny) + **konkrétní akci**, ne jen oznámit „dostanete doporučení".

**C. 3 MĚŘITELNÉ OBLASTI** (hodnotová nabídka) — **musí být benefit-oriented**, ne abstraktní kategorie:

```
„Pomocí tohoto [skóre / auditu / plánu / kalkulačky /
strategického plánu] zjistíte:
• [Aktivní sloveso] + [konkrétní výsledek 1]
• [Aktivní sloveso] + [konkrétní výsledek 2]
• [Aktivní sloveso] + [konkrétní výsledek 3 + benefit pro Kč/čas/zdraví]"
```

✅ **Silné příklady (doména wellness — fyzický produkt):**
- „Změříme, kolik konkrétně máte doma [měřitelná veličina — prach / hluk / pyl] (a kde jsou skryté zdroje, které pravděpodobně neznáte)"
- „Zjistíme, jak [oblast] ovlivňuje [zdraví / spánek / výkon] vaší rodiny — a které riziko je u vás největší"
- „Najdeme, kterou variantu [produktu] potřebujete — a kterou ne (ušetříte 5–25 000 Kč za špatnou volbu)"

✅ **Silné příklady (doména B2B SaaS / služba):**
- „Spočítáme, kolik vás ročně stojí ruční follow-up a opožděné odpovědi na leady"
- „Zjistíme, které 3 prodejní úkoly můžete dnes večer předat [USP nástroji] (a které ne)"
- „Najdeme, jaký rozpočet vám vrátí [USP] za 90 dní — a kdy zacházet do investice 600 000 Kč nemá smysl"

✅ **Silné příklady (doména online kurz / mentoring):**
- „Spočítáme, kolik vám aktuální mezery v dovednostech stojí v ušlém obratu měsíčně"
- „Zjistíme, které 3 lekce máte odbavit jako první (a které přeskočit pro váš profil)"
- „Najdeme, za jak dlouho dosáhnete [konkrétní milestone] při vašem aktuálním tempu — a co změnit, aby to bylo o 50 % rychlejší"

❌ **Slabé (anti-pattern — vágní kategorie bez benefitu):**
- „Zdroje [problému]" — abstraktní kategorie, žádný benefit
- „Citlivost [kontextu]" — korporátní term
- „Připravenost na řešení" — bez konkrétna

**Pravidlo:** Každá ze 3 oblastí musí začínat **aktivním slovesem v 1. osobě množné** („Změříme / Zjistíme / Spočítáme / Najdeme / Porovnáme / Ukážeme") + **konkrétní výsledek s číslem / Kč / názvem položky**.

**D. AUTORITA** (důvěryhodnost autora):

- **Kdo to vytvořil:** jméno + bio (z Brand DNA `## 3. PŘÍBĚH ZAKLADATELE` nebo z URL)
- **Background:** co dělal/dělá (počet klientů, výsledky, knihy, podcasty)
- **Výzkum:** statistiky („85 % firem v X selhává na Y", „Studie [zdroj] ukázala…")
- **Sociální důkaz:** počet stažení / klientů / hodnocení (pokud máme)

**E. VÝZVA K AKCI** — formula se **social proof signálem**:

```
„Spustit [název nástroje] — [X minut], zdarma,
[okamžitý benefit]. Již [N] [klientů/domácností/firem]
zjistilo své [score / audit / plán]."
```

✅ **Silné příklady:**
- „Spustit test vzduchu doma — 4 minuty, zdarma, personalizovaná doporučení do 5 minut na e-mail. Již 1 247 domácností zjistilo své skóre."
- „Spustit audit prodejního procesu — 6 minut, zdarma, kompletní report do 10 minut. Již 312 firem zjistilo, kde tečou peníze."

❌ **Slabé:**
- „Spustit kvíz" (jen tlačítko, žádný benefit)
- „Začít" (žádný kontext)

**Klíč:** kombinace **rychlost + zdarma + okamžitý výsledek + social proof číslo** (kolik už test/audit vyplnilo).

**Pokud klient nemá reálné číslo pro social proof** → v dokumentu označ `[OVĚŘ S KLIENTEM: počet vyplněných testů / domácností / firem pro social proof v CTA]`. Bez ověřeného čísla nepoužívat fiktivní čísla — narušilo by to důvěru.

### Cíl konverze

**Landing → vyplněný dotazník: 20–40 %**

Pokud při testování je nižší → hook a hodnotová nabídka nejsou dost silné.

### Psychologické triggery

- **Urgence:** časový limit pro bonus / sezónní okno (jen pokud reálné)
- **Sociální důkaz:** počet uživatelů, hodnocení
- **Autorita:** ze sekce autority
- **Vzácnost:** „personalizovaná × všeobecné PDF" — proč naše je jiné
- **Reciprocita:** „Dáte mi X minut, dám vám personalizovanou analýzu"

### Přemostění do prodeje

- Strategický přechod: dotazník → výsledková stránka → personalizovaný e-mail → prodejní stránka
- Kvalifikace: otázka o preferovaném řešení rozdělí klienty do 4 rozpočtových kategorií → každá dostane jinou prodejní komunikaci
- Personalizace: výsledek magnetu je prodejní háček (klient se vidí v analýze → důvěra)

---

## SEKCE 5: Nabídka + stránka s dynamickými výsledky

### Část A — Stránka s dynamickými výsledky

Co klient uvidí **hned po vyplnění** dotazníku (před e-mailem):

```
1. HLAVNÍ VÝSLEDEK
   - Skóre: ukazatel 0–100 % + kategorie („Středně připravený")
   - Audit: kategorie skóre + celkový dojem
   - Plán: náhled časové osy („Váš 90denní plán je připraven")
   - Kalkulačka: hlavní číslo („Současný stav vás stojí 850 000 Kč/rok")
   - Strategický plán: strategické shrnutí („3 příležitosti pro váš růst")

2. 3 KLÍČOVÉ POZNATKY
   Konkrétně podle odpovědí — co dělají dobře / co schází

3. DYNAMICKÝ DALŠÍ KROK (podle preferovaného řešení)
   - „Kniha" → Stáhněte si bezplatnou knihu, odkaz na produktovou stránku
   - „Online" → Pozvánka na webinář / registrace do kurzu
   - „1:1" → Rezervovat 1:1 strategickou konzultaci
   - „Služba na klíč" → Strategický call s nejvyšším konzultantem

4. KONTAKT + SOCIÁLNÍ SÍTĚ + WEB
   Patička s odkazy
```

### Část B — Struktura nabídky (mapování Product DNA / vstup → struktura)

| Položka v nabídce | Zdroj (Product DNA) | Fallback (manuál / URL) |
|--------------------|----------------------|---------------------------|
| Pozicování (hlavní myšlenka + unikátní mechanismus) | `## 1.` USP + transformace | Nadpis + popis z URL |
| Název nabídky | `## 1.` Název | Z URL nebo manuálu |
| Komponenty | `## 4. CO PŘESNĚ KLIENT DOSTANE` | Z popisu produktu |
| 3D benefity (top 3) | `## 3. HLAVNÍ BENEFITY` | Z benefitů na URL |
| Unikátní mechanismus | `## 3.` „Mechanismus" pole | Pojmenovaný framework z URL / `[OVĚŘ]` |
| Důkazy | `## 7. SOCIÁLNÍ DŮKAZ` | Testimoniály z URL |
| Bonusy + hodnoty | `## 8. SPOUŠTĚČE` → bonusy | `[OVĚŘ S KLIENTEM]` |
| Garance | `## 8.` → garance | Z URL nebo `[OVĚŘ]` |
| Urgence | `## 8.` → urgence | `[OVĚŘ S KLIENTEM]` |
| Cena | `## 5. CENOVÁ STRUKTURA` | Z URL nebo `[OVĚŘ]` |

### Personalizace per segment (5.2)

Pro každý ze 3 ilustrativních segmentů:
- Hlavní zaměření (který benefit cílíme)
- Klíčové benefity (2–3 z top 3)
- Adaptivní nadpis („Pro [segment] = [konkrétní výsledek z otázky o cíli] za [časový rámec]")

**Vždy připomenout:** AIQ engine generuje personalizaci per kontakt, ne pro 3 segmenty.

---

## SEKCE 6: 5denní adaptivní follow-up sekvence

### Struktura 6 e-mailů

| Den | Účel | Hlavní zpráva | Výzva k akci |
|-----|------|----------------|----------------|
| **Den 1** | Doručení výsledků + autorita | Děkuji, tady je vaše [skóre / audit / plán / kalkulačka / strategický plán]. Krátký autor bio. | Na prodejní stránku — varianta podle preferovaného řešení |
| **Den 2** | Představení nabídky + hodnota | Detailní představení produktu, top 3 benefity z otázky o cíli | Na prodejní stránku |
| **Den 3** | Vize budoucnosti + emoce | Kontrastní vize „bez/s řešením". **Personalizovaný PDF dokument** s vizí (per klient). | Odkaz na stažení personalizovaného „Vize 12 měsíců napřed" PDF |
| **Den 4** | Garance + logické argumenty | Předjímání top 3 námitek z otázky o překážce + garance + důkazy | Na prodejní stránku |
| **Den 5 ráno** | Urgence + sleva / bonus | Slevový voucher per rozpočtová kategorie; časový limit | Na prodejní stránku s voucherem |
| **Den 5 večer** | Finální výzva | Krátký emocionální, připomenutí klíčové bolesti | Na prodejní stránku |

### Multikanálový přístup

- **E-mail:** primární kanál, všech 6 zpráv
- **SMS:** Den 1 (krátké „výsledky dorazily"), Den 5 ráno + večer (urgence)
- **Retargeting (reklamy):** vizuálně jiné kreativy per segment
- **WhatsApp / Messenger** (pokud relevant): osobnější ton, Den 3 lidský příběh

### Vzorové předměty e-mailů

- Den 1: „[Jméno], váš [skóre / audit / plán] je tady"
- Den 2: „[Konkrétní benefit z otázky o cíli] — jak na to"
- Den 3: „Jak to bude vypadat za rok?"
- Den 4: „Vím, co vás brzdí — a tady je důvod, proč to není problém"
- Den 5 ráno: „[Jméno], poslední den s bonusem"
- Den 5 večer: „Za 6 hodin to končí"

---

## Globální pravidla

1. **Vykání všude** v dotazníku, na landing page, v e-mailech
2. **Žádné anglicismy** (kromě „funnel", „hook") — místo „CTA" → „výzva k akci", „insights" → „klíčové poznatky", „best practice" → „doporučený postup", „next step" → „další krok", „done-for-you" → „služba na klíč"
3. **Žádné spekulace** — chybějící data `[OVĚŘ S KLIENTEM: …]`
4. **Hlas podle Brand DNA `## 5. HLAS ZNAČKY`** (pokud existuje); jinak `[OVĚŘ S KLIENTEM: tonalitu]`
5. **Konec dokumentu = závěr strategie** — žádné „implementační kroky" ani „očekávané výsledky"
6. **Segmenty jsou ilustrativní** — vždy připomenout (engine personalizuje per kontakt)
7. **Prvních 5 otázek = ano/ne doporučené postupy**, pak otevřené kvalifikační
8. **Limit otázek:** 10–15 default / až 35 v režimu pro osobní setkání
9. **Závěrečná otázka vždy:** otevřený box „Je něco dalšího, co bychom měli vědět?"
10. **Cíl konverze landing → dotazník 20–40 %** — explicitně uvést v dokumentu
