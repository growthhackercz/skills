# RESEARCH 2026 — Organické social posty (podklad pro upgrade skillu `social-post-writer`)

> **Zdroj:** konsolidace zastaveného deep-research workflow (`wf_6e12385f-580`, 07/2026). ~65 subagentů: Web Searcher (6 oblastí) → Source Extractor (fetch + extrakce claimů) → Adversarial Claim Verifier (3 hlasy/claim, snaha vyvrátit). Workflow se zastavil před finální syntézou; tento report skládá dohromady 162 extrahovaných claimů a 28 adverzárních verdiktů.
>
> **Klasifikace u každého tvrzení:**
> **[DOLOŽENO]** = studie / oficiální zdroj přímo v datech (a u sporných čísel prošlo adverzárním ověřením).
> **[KONSENZUS]** = shoda praktiků / více blogů, ale bez tvrdé studie.
> **[SPORNÉ/MÝTUS]** = protichůdné zdroje nebo nepodloženo.
>
> **Metodická poznámka:** Většina „benchmarků" (Buffer, Metricool, Socialinsider, Ordinal) jsou **first-party vendor studie** na jejich vlastních datech = selection bias. Verifikátoři je potvrdili jako věrně citované, ale absolutní čísla jsou vždy metodicky závislá (per-reach vs. per-follower vs. per-impression) a nesmí se míchat mezi studiemi. Kde to hraje roli, je to u tvrzení uvedeno.

---

## Oblast 1 — Algoritmické změny 2025–2026 per síť

### 1A. VERDIKT NA DVA OVĚŘOVANÉ MÝTY (klíčové)

#### MÝTUS A: „Meta omezila link posty na 2/měsíc pro neověřené účty"
**VERDIKT: [SPORNÉ/MÝTUS] — jak je to formulováno v naší současné referenci, je to NEPŘESNÉ. Realita = OMEZENÝ TEST vázaný na placené Meta Verified, ne plošná policy, a časové okno „za měsíc" žádný primární zdroj nepotvrzuje.**

Co data skutečně ukazují:
- **[DOLOŽENO]** Meta v prosinci 2025 spustila **omezený TEST** (ne policy), který limituje počet **link postů** u účtů v professional mode a u Facebook Pages, pokud nemají **Meta Verified**. Poprvé zachyceno uživateli (mj. Matt Navarra) v týdnu před 17. 12. 2025, poté potvrzeno mluvčím Mety. *(TechCrunch, 17. 12. 2025; Source Extractor af7585577088a6c71)*
- **[DOLOŽENO]** Meta doslova: *„This is a limited test to understand whether the ability to publish an increased volume of posts with links adds additional value for Meta Verified subscribers."* *(TechCrunch 12/2025)*
- **[DOLOŽENO]** Číslo **2** v testu potvrzeno, ALE primární zdroj (TechCrunch) **neuvádí časové okno** (per měsíc/týden/den). Tvrzení „2 ZA MĚSÍC" pochází až z pozdější interpretace (Social Media Examiner / Mari Smith, 02/2026), která to sama označuje jako **test**, ne doloženou policy, a cituje pozorování expertky, ne oznámení Mety. *(Source Extractor adea50497e2738293)*
- **[DOLOŽENO]** **Publisheři jsou z testu výslovně vyňati.** *(TechCrunch 12/2025)*
- **[DOLOŽENO]** **Odkazy v komentářích test NEomezuje** — potvrzeno Metou. Taktika „link v prvním komentáři" na FB tedy zůstává v platnosti. *(TechCrunch 12/2025; SM Examiner 02/2026)*
- **[DOLOŽENO]** Meta Verified: od **14,99 USD/měsíc** (profily), vyšší tarify 50 / 150 / 500 USD/měsíc. *(TechCrunch, SM Examiner)*
- **Kontext (proč Meta linky marginalizuje):** **[DOLOŽENO]** Podle Mety pochází **>98 % zobrazení** ve FB feedu v USA z postů **bez odkazů**; link posty = jen ~1,9 % zobrazení (Facebook Widely Viewed Content Report). *(af7585577088a6c71, adea50497e2738293)*
- **Predikce (ne fakt):** **[SPORNÉ]** Mari Smith: neplatící uživatelé „pravděpodobně" nebudou blokováni, ale dostanou prakticky nulový dosah linků — „probably", tj. pravděpodobnostní formulace i od zastánce tvrzení. *(adea50497e2738293)*

→ **Doporučená formulace do skillu:** „Facebook (12/2025+): Meta TESTUJE omezení link postů (číslo 2) u professional/Page účtů bez Meta Verified. Není to plošná policy, časové okno není oficiálně potvrzené, publisheři vyňati, linky v komentářích bez omezení. Bezpečné pravidlo: link nedávat do těla FB postu, ale do prvního komentáře — nezávisle na tomto testu má link post na FB tak jako tak <2 % zobrazení."

#### MÝTUS B: „Instagram tvrdý limit 5 hashtagů od 12/2025"
**VERDIKT: [DOLOŽENO] — v JÁDRU PRAVDA. Je to reálná, platformou vynucovaná změna (ne jen Mosseriho doporučení 3–5), s jedinou nuancí: v 12/2025 byla oznámena a nasazovala se postupně (gradual rollout), ne okamžitě u všech účtů naráz.**

- **[DOLOŽENO]** Instagram v **prosinci 2025** oficiálně oznámil snížení maxima hashtagů v caption (post i Reel) z 30 na **5** jako **produktovou změnu / hard cap**, ne doporučení. *(Social Media Today, 18. 12. 2025; Adam Mosseri @mosseri primární oznámení; Source Extractor aa5b2249527205dac + ab734df444c7ffe57)*
- **[DOLOŽENO]** Doslovné znění (Meta e-mail relayovaný agenturou @yoursocialteam s creditem @mosseri): *„Starting this week, you'll be able to add up to 5 hashtags in the caption of a Reel or post (vs. the previous 30.)"* + *„Rolling out globally starting today, over the coming weeks."* → potvrzuje **cap i postupné nasazení**. *(ab734df444c7ffe57)*
- **[DOLOŽENO]** Oficiální zdůvodnění Instagramu: *„using fewer (up to 5) more targeted hashtags, rather than many generic ones, can improve both your content's performance and people's experience."* *(aa5b2249527205dac)*
- **[DOLOŽENO]** Limitu předcházel ~rok testování; v posledním experimentu byla část uživatelů omezena dokonce jen na **3** hashtagy — Instagram zvažoval přísnější limit, finálně zvolil 5. *(aa5b2249527205dac)*
- **[DOLOŽENO]** Mosseri opakovaně (02/2025 i 05/2025): hashtagy **nezvyšují reach ani viditelnost**; hodnota je jen v kategorizaci/propojení obsahu, ne v discovery. *(aa5b2249527205dac)*
- **Nuance zdroje:** primární oznámení běželo přes Mosseriho účet; agenturní repost byl secondhand. Ale samotný fakt (5 cap, 12/2025, gradual) je potvrzen víc zdroji včetně Social Media Today. *(ab734df444c7ffe57)*

→ **Doporučená formulace do skillu:** „Instagram (12/2025+): TVRDÝ limit max. 5 hashtagů v caption (post i Reel), platformově vynucený, nasazováno postupně. Používej ≤5 úzce cílených, nikdy generické (#reels, #explore, #fyp) — ty podle Mety mohou výkonu spíš uškodit. Hashtagy nezvyšují reach, jen pomáhají zařazení."

---

### 1B. LinkedIn — externí odkazy: penalizace, link v prvním komentáři, osobní vs. firemní

Tohle byla **nejsilněji rozporovaná oblast celého výzkumu** (8 adverzárních hlasů, split verdikty). Shrnutí:

**Základní studie (Ordinal / „Ordinal Data Lab", autor Jeffrey Zhao):**
- **[DOLOŽENO, ale vendor + živá URL padá]** Na vzorku **900 000+ LinkedIn postů (2/2023 – 2/2026)** měly posty s externím odkazem v průměru **−26,5 % reach** vs. posty bez odkazu; penalizace rostla z **5 % (2023) → 42 % (2025, 95% CI 35–48 %) → 38 % 2026 YTD**; statisticky signifikantní každý rok (Mann-Whitney U, **p < 0,001**); negativní ve **34 z 37 měsíců**. *(Source Extractor abddc6b8a1ae78d25)*
  - **Ověření:** Verifikátoři potvrdili každé číslo **verbatim přes Wayback snapshot 2026-03-29** (živá URL `tryordinal.com/blog/linkedin-link-penalty-study` nyní vrací 404 — **v reportu vždy citovat archivní URL**). *(verdikty aaae5b, a85038, a43699, a83aac)*
  - **Výhrada:** vendor studie na datech z **vlastního plánovacího nástroje Ordinal** (selection bias k firemním stránkám / employee-advocacy), observační, ne peer-reviewed.

**Link v prvním komentáři — funguje, nebo je „patched"? → SPORNÉ (dataset vs. dataset):**
- **[DOLOŽENO — ale jen jako směrový signál]** Podle Ordinal dat od **11/2024 do 2/2026** měly link-in-comments posty reach skóre **nad no-link baseline 100 téměř každý měsíc** (rozsah 88,2–594,9; 2/2026 = 301,7; 11 z 12 sledovaných měsíců nad baseline). Autoři to sami kvůli selection bias označují za *„a signal to test and monitor, not a guaranteed playbook."* *(abddc6b8a1ae78d25; verifikátoři a85038, a43699, a83aac potvrdili verbatim)*
- **[SPORNÉ]** PROTI tomu tvrdí několik 2026 agenturních blogů, že workaround „link v prvním komentáři" byl **na začátku 2026 patchnut** přes detekci „bridge behavior" (algoritmus penalizuje link v komentáři autora stejně jako v těle):
  - dataslayer.ai (02/2026): externí link v postu ≈ **−60 % reach** a NOVĚ penalizován i link v prvním komentáři. *(Web Searcher a7aa52ad94fc80546)*
  - digitalapplied.com, SocialPilot (06/2026): „first-comment workaround patched in early 2026". *(verdikty a83aac, a43699)*
  - van der Blom (secondhand): komentáře s externím linkem suppressed **až −80 %** viditelnosti. *(verdikt a01c0200)*
  - **ALE:** tyto zdroje **neuvádějí dataset**, zatímco Ordinalova vlastní 1–2/2026 měření (271,3; 301,7 nad baseline) ukazují opak. → **Epistemický status: link v prvním komentáři je směrový signál, ne doložený playbook. Testovat per účet.**

**Osobní profil vs. firemní stránka — a „penalizace linků" celkově → SPORNÉ:**
- **[SPORNÉ/MÝTUS]** Ordinal claim „company pages reach ratio 0,95 (−5 %) / osobní profily 1,01 (imunní, bez měřitelné ztráty)" **NEPROŠEL** adverzárně: (a) konkrétní čísla 0,95/1,01 nejsou v žádném indexovaném úryvku a jsou **matematicky neslučitelná** s agregátní penalizací −26,5 % téže studie (Simpson's paradox / composition effect); (b) contradicted větším nezávislým datasetem. *(refutováno: a01c0200, a08dfb, ad349d, a6cf75)*
- **Protichůdné velké datasety (osobní profily):**
  - **[DOLOŽENO]** van der Blom, **Algorithm Insights 2026 (1,3M postů, převážně osobní profily):** jeden externí link v těle = **−18,8 % medián reach**. *(verdikty a01c0200, a08dfb)*
  - **[DOLOŽENO]** AuthoredUp (**3M+**, resp. 621 833 postů, převážně osobní tvůrci, 03/2025–02/2026): posty s 1 linkem mají **nejnižší reach**; off-platform posty nižší initial distribution; 4+ linků má 3–5× vyšší medián reach než 1 link. *(verdikt ad349d)*
  - **[DOLOŽENO]** Metricool 2026: firemní stránky s linky **+51 % impresí**, osobní profily **−27 %** (opačný směr než Ordinal!). *(verdikt aa28b9d)*
- **Oficiální stanovisko LinkedIn (protistrana):**
  - **[DOLOŽENO]** LinkedIn Sr. Director of Product Management **Rishi Jobanputra** (cca 08/2025, via Matt Barker): pouhé přidání linku reach **NEsnižuje** — rozhoduje **záměr (intent)**, ne link. Post, jehož jediný účel je odvést na link bez vlastní hodnoty, ztratí reach; hodnotný link post penalizován není. *(Source Extractor ab03bfdeefb62cac9; Web Searcher a12adac4b82de7a45)*
  - Praktické pravidlo z komentářů: *„the link should extend the value, not carry it."* *(ab03bfdeefb62cac9)*

→ **Syntéza pro skill (LinkedIn linky):** Sítě se neshodují na velikosti ani mechanismu penalizace, ale **shodují se na směru: link v těle LinkedIn postu snižuje reach** (odhady −18,8 % až −60 %; oficiálně popřeno, ale všechna praktická data to potvrzují). **Bezpečné pravidlo:** hodnotu nést v textu postu, link buď (a) do prvního komentáře (funguje jako směrový signál, ne jistota — testovat), nebo (b) vynechat u awareness postů. Vyhnout se „naked link" postu bez vlastní hodnoty.

---

### 1C. LinkedIn — algoritmus, formáty, dwell time (2026)

- **[KONSENZUS — praktik]** **Dwell time (doba zdržení na postu) = signál č. 1** pro LinkedIn algoritmus 2026; kdo nepoužívá carousely / infografiky / vizuály, je „prakticky neviditelný". *(Justin Welsh, LinkedIn Guide 2026, a3b4d4153fbe15127; potvrzeno i blogem a03768b7e6f23e407: „post čtený 30 s překoná post s 50 rychlými liky")*
- **[DOLOŽENO — Buffer 52M+ postů, 03/2026]** Pořadí formátů na LinkedIn podle mediánového ER (metodika Buffer = engagements/reach): **carousel/dokument 21,77 %** > video 7,35 % > image 6,52 % > **link 3,81 %** > **text 3,18 %**. Carousel ≈ 3× video. Link a text = nejslabší. *(Source Extractor a250120b47d13e0a5; verifikátoři ad65c, a30715, ad4bd potvrdili verbatim)*
  - **Výhrada:** 21,77 % je Buffer-metodika (dělí reachem, započítává kliky vč. carousel slide-clicks) → vs. per-impression benchmarky (Socialinsider dokumenty ~7,0 %, Oktopost B2B medián 5,72 %) je to mnohem výš. **Pořadí formátů ale všechny studie potvrzují.** Nikdy nemíchat absolutní čísla mezi studiemi.
- **[KONSENZUS — blog]** LinkedIn dokument/PDF carousel = **nejvýkonnější formát 6,6 % ER** (596 % vs. text, 303 % vs. single image, 278 % vs. video). *(a03768b7e6f23e407 — pozn.: jiná metodika, jiný absolutní údaj než Buffer, ale stejný směr)*
- **[KONSENZUS — blog]** Nový LinkedIn post algoritmus nejdřív testuje na **2–5 % sítě** autora; jen **5 %** postů, které v první hodině podvýkonují, se později vzpamatuje. *(a03768b7e6f23e407)*
- **[KONSENZUS — blog]** Hashtagy na LinkedIn: jen **1–2 vysoce relevantní inline** v textu, ne naskládané na konci. *(a03768b7e6f23e407)* — pozn.: naše současná reference říká „přesně 3 (oficiální doporučení LinkedIn)"; praktici 2026 doporučují spíš 1–2. Obojí je „doporučení", ne hard limit.
- **[DOLOŽENO — Metricool 2026]** LinkedIn: klasické metriky (liky, komentáře, shares) meziročně **klesají**, ale celkový engagement **+14 %** díky „invisible interactions" (kliky, swipy carouselu, video views, link taps). → mění to, jaké CTA má smysl (swipe/dwell-oriented, ne jen „komentuj X"). *(Web Searcher a7aa52ad94fc80546)*

### 1D. Číslo „561 % vyšší reach osobní profil vs. firemní stránka"
**VERDIKT: [SPORNÉ] — v nasbíraných datech NEDOLOŽENO jako nezávislý benchmark.** Stopa vede k jediné vendor analýze (**GaggleAMP**, re-citováno Refine Labs) = horní vendor odhad, ne nezávislé měření. Konzervativnější data: Sprout Q1 2026 ~**4,7 % osobní profil vs. 1–2 % firemní** (tj. řádově ~3–5×, ne 5,6×). **Směr (osobní >> firemní) platí, konkrétní číslo 561 % ne.** *(Web Searcher aafc89390169c87f5)*

### 1E. X/Twitter — algoritmus (open-source kód)
- **[DOLOŽENO — zveřejněný zdroj. kód X + Buffer]** Externí linky v hlavním postu: **−30 až −50 % reach**; u free účtů od **03/2025 nulový medián engagementu** link postů. Řešení: link do reply. *(Source Extractor ac05ea7b06cf31f37; Web Searcher a516abd2cc19cfc13)*
- **[DOLOŽENO — open-source kód]** Váhy ranking signálů: reply s odpovědí autora **+75**, reply **+13,5**, bookmark **+10**, retweet **+1,0**, like **+0,5**. → **konverzace (reply chain) je ~150× silnější než like**; retweet 20×, bookmark 10×. *(ac05ea7b06cf31f37)*
- **[DOLOŽENO]** Hashtagy na X: **1–2 relevantní = +21 % engagement**, ale **více hashtagů penalizováno −40 %** (spam signál). → tvrzení „X posty úplně bez hashtagů" je nepřesné; 1–2 pomáhají. *(ac05ea7b06cf31f37; a2b54ea6e8828c0ba potvrzuje 1–3)*
- **[DOLOŽENO/KONSENZUS]** **Long-form > thread:** od 03/2026 algoritmus X zvýhodňuje **jeden long-form post** (Premium až 25 000 znaků, dwell time 2+ min = signál +10) před multi-tweet threadem. *(ac05ea7b06cf31f37; a516abd2cc19cfc13)*
- **[DOLOŽENO]** Krátké tweety **71–100 znaků = +17 % engagement** vs. delší. *(ac05ea7b06cf31f37)*
- **[DOLOŽENO]** Premium boost: **4× in-network, 2× out-of-network viditelnost (~10× reach/post)**; TweepCred práh **0,65** — pod ním se distribuují jen 3 tweety účtu. *(ac05ea7b06cf31f37)*
- **[DOLOŽENO]** Prvních **30 min** rozhoduje (10+ interakcí spouští amplifikaci). *(a516abd2cc19cfc13)*

---

## Oblast 2 — Struktury postů a hooků 2026 (data + systémy tvůrců)

### 2A. LinkedIn anatomie postu (Justin Welsh — nejcitovanější praktik)
- **[KONSENZUS — primární praktik]** **Anatomie: Trailer → Meat → CTA/CTC + vizuál.** *(a3b4d4153fbe15127, afdc6baea5def922c)*
  - **Trailer** = vše nad zlomem „…more". První řádek láme scroll pattern, druhý staví tenzi, **poslední řádek před „see more" (hook line) slibuje payoff** worth clicking.
  - **Meat** = tělo. Welsh ho píše **jako první, hook až potom.**
  - Zakončení: **CTC (call to conversation** — výzva ke komentáři) NEBO **CTA** (newsletter/produkt).
- **[DOLOŽENO — číslo platformy]** LinkedIn: limit **3 000 znaků**, ale nad zlomem se zobrazuje jen **~210 znaků**. Při prázdném řádku mezi větami se před „see more" vejdou jen ~2 napsané řádky. Úkol těch ~210 znaků = výhradně získat klik na „…more". *(a3b4d4153fbe15127, a33a0e867c0bc6b26)*
- **[KONSENZUS]** Formátovací čísla Welsh: věty **~5 slov** (vs. průměr 10), odstavce **~7 slov** (jedna věta + vzduch), hooky **~6 slov**; bloky po **3 krátkých řádcích** oddělené prázdnými řádky. *(afdc6baea5def922c, a33a0e867c0bc6b26)*
- **[KONSENZUS]** *„The first line is more important than 95 % of the rest of the post."* *(a33a0e867c0bc6b26)*
- **[KONSENZUS]** Nejvýkonnější vizuální formáty LinkedIn 2026 dle Welshe: **PDF carousely** (vzdělávací obsah), **infografiky** (komplexní data), **vizuály 4:5** (stop scroll). *(a3b4d4153fbe15127)*
- **[KONSENZUS]** Welshova viral formule (3-step template): *„The {RelatableEnemy} is {Negativity}" / „The {Hero} is {StrongPositiveStatement}" / „And I {Gasoline}. {TeaserQuestion}?"* *(a33a0e867c0bc6b26)*
- **Systém recyklace „Play the Hits":** z každého úspěšného postu 5 variací, po jedné měsíčně na dalších 5 měsíců; cíl portfolio **90 „hitů"** → 25 % ročního obsahu pokryto repurposingem. *(a3b4d4153fbe15127)*
- **Případovka:** Welshův viral post = 4,766M impresí, 50 583 engagementů, 1 444 komentářů, 1 589 shares. *(a33a0e867c0bc6b26)*

### 2B. Lara Acosta (top LinkedIn creator 2025/26)
- **[KONSENZUS]** 6-krokový framework: **Hook → Re-hook (přidá curiosity) → Lead (co se čtenář naučí) → Body → Power-ending (2řádkové shrnutí) → CTA/CTE.** Jediný nalezený zdroj, který explicitně popisuje **„re-hook"** z požadované anatomie. *(magicpost.in, afdc6baea5def922c)*
- **[KONSENZUS]** Pravidlo **„How I" místo „How to"** v hooku; teze „content = 20 % psaní, 80 % psychologie". *(afdc6baea5def922c)*
- **[KONSENZUS]** Tři rysy jejích hooků: (1) vyvolat zvědavost, (2) konkrétní čísla/nástroje/insighty, (3) příslib akčních rad. *(Source Extractor afc75e3bd11225b02)*
- **[KONSENZUS]** Formátování: jednoduchý jazyk, krátké věty, **každý řádek musí obstát samostatně**, vysoká skenovatelnost, šipky vedoucí oko. *(afc75e3bd11225b02)*
- **[KONSENZUS]** Nejčastější formát = simple image post (~46 % obsahu), postuje denně, nejlepší den **úterý**, 200k+ followerů. *(afc75e3bd11225b02)*
- **[SPORNÉ]** „Dobrý hook ovlivní až 80 % úspěchu postu" — číslo bez citované studie, copywriterské lore. *(afc75e3bd11225b02)*
- **⚠️ Rozpor v datech:** anotace zadání tvrdila, že tento zdroj popisuje samostatný **re-hook framework**; Source Extractor afc75e3bd11225b02 explicitně uvádí, že tenhle konkrétní článek re-hook **vůbec nezmiňuje** (re-hook je doložen jen z magicpost.in výše). Re-hook tedy stojí na jednom zdroji.

### 2C. Nicolas Cole / Dickie Bush (Ship 30 for 30) — jmenováni v zadání
- **[KONSENZUS — primární autoři]** **Hook-Story-Offer** framework pro strukturu krátkých postů; dále curiosity gap, **„1 Chip Rule"**, formát **Atomic Essay (~250 slov)**. Beginner-level, od autorů samotných, bez studie. *(Web Searcher afdc6baea5def922c)*

### 2D. Alex Hormozi — jmenován v zadání
- **[KONSENZUS — v datech jen mělce]** V search výsledcích doložen Hormozi **„Hook–Retain–Reward"** model a kategorie hooků (past / recent past / present / in-the-moment). **NEBYLO ale hlouběji fetchnuto do strukturovaných claimů** — workflow zachytilo jen názvy zdrojů (YouTube, skool.com, LinkedIn „My $4,000,000 content strategy for 2025"). *(allpages — search snippets)*
- **(V nasbíraných datech nedoloženo:** konkrétní číselná pravidla Hormoziho hook systému, plný rozpad Hook-Retain-Reward. **Bude potřeba doplnit rešerši.)**

### 2E. Katalog hook formulí (surovina pro skill)
- **[KONSENZUS — bez výkonnostních dat]** Kleo: **203 fill-in-the-blank hook šablon** s reálnými příklady od 60+ jmenovaných tvůrců (Welsh, Acosta, Cole, Bush, Dan Koe, Jasmin Alić, Matt Barker, Katelyn Bourgoin, Alex & Leila Hormozi…). Archetypy: transformace s výsledkem („How I turned my [asset] into [valuable asset] [results]"), kontrariánský hook („Why great [professionals] must be [counterintuitive quality]"), podmínkové varování („If you don't [action], don't expect [outcome]"). Samostatná sekce **14 carousel hook šablon**. Žádná číselná pravidla, žádná studie → klasifikovat jako konsenzus praktiků. *(Source Extractor a6302a6216d1e2995; afdc6baea5def922c)*

### 2F. Nejsilnější doložený strukturní princip napříč sítěmi
- **[DOLOŽENO — Buffer, ~2M postů, 03/2026]** Nejsilnější signál engagementu **není formát ani timing, ale odpovídání na komentáře** (viz Oblast 5). Buffer doslova: *„The strongest signal in this entire dataset wasn't a format trick, a timing hack, or an algorithm exploit. It was replies."* → strukturní důsledek: **post psát tak, aby vyvolal komentáře, a pak na ně odpovídat.** *(a250120b47d13e0a5; verifikátoři a2a11a, a48b3e, a10b1ae potvrdili verbatim)*

---

## Oblast 3 — Carousel playbook

### 3A. Instagram carousel
- **[DOLOŽENO — Buffer 4M+ IG postů]** Carousely generují **~109 % vyšší engagement na zasaženého uživatele než Reels** (ER podle reach: **carousel 6,90 % > single image 4,44 % > Reels 3,31 %**), ale Reels mají **~1,36× vyšší reach (+36 %)** než carousely. → **Reels vyhrávají reach, carousely vyhrávají engagement/saves.** *(Source Extractor a250120b47d13e0a5; verifikátoři a0777e, a7cad9, a1f908 potvrdili verbatim)*
  - **Výhrada:** reach data (1,36×) z okna posty přes Buffer 1/2022–10/2024; Socialinsider jinou metodikou hlásí reach gap **>2×**. Směr stejný, magnituda metodika-závislá.
- **[DOLOŽENO — Metricool 2026, 24,3M postů]** Carousely = **9× více saves** než single-image posty. *(Source Extractor a03b1ee0bb3147558; verifikátoři aaee7d, ad8e93, adaefcc potvrdili verbatim)*
- **[DOLOŽENO — Metricool 2026]** Objem publikovaného obsahu 2026: **+12 % single image, +24 % carousely, +35 % Reels** (Reels nejrychleji rostou, ale carousely drží save-korunu). *(a03b1ee0bb3147558)*
- **[DOLOŽENO — Metricool/HypeAuditor]** **Reels vyhrávají reach u účtů pod ~50k followers, carousely u největších účtů** (>1M) — reach výhoda Reels se u velkých účtů obrací. Pro SMB (cílovka skillu) tedy Reels na reach, carousel na saves/hloubku. *(Web Searcher aafc89390169c87f5; verdikt a0777e)*
- **[KONSENZUS — blog]** Počet slidů IG carouselu: optimum **8–10 slidů**, engagement klesá po slidu ~3 a znovu stoupá u delších carouselů (dočtení). *(allpages — fetched content)*
- **[KONSENZUS — Welsh]** Poměr **4:5** (1080×1350) pro feed vizuály/carousely — „easy to consume, stop the scroll". *(a3b4d4153fbe15127)* — pozn.: 4:5 vs. 1:1 se v datech neřeší přímým srovnáním; konsenzus je 4:5 (zabírá víc plochy feedu).

### 3B. LinkedIn dokument / PDF carousel
- **[DOLOŽENO — Buffer]** Nejvýkonnější formát na LinkedIn (viz 1C): **carousel/dokument 21,77 % ER**, ~3× video. *(a250120b47d13e0a5)*
- **[KONSENZUS — blog]** Optimální délka LinkedIn dokument/PDF carouselu: **5–10 slidů; engagement klesá po 10. slidu.** *(a03768b7e6f23e407)*
- **[KONSENZUS — blog]** **První slide = headline/hook („subject line, ne cover page")** — bez něj nikdo neswipuje; poslední slide = jasné CTA; konzistentní branding. Sweet spot **6–10 slidů** (5–8 pro rychlé tipy, 8–15 pro hloubku). *(morphica.studio, afdc6baea5def922c)*

→ **Konsolidované carousel pravidlo:** 1. slide je hook (nikdy „cover"), 6–10 slidů (LinkedIn ostře řezat po 10), poměr 4:5, poslední slide CTA. IG carousel = save-mašina, Reels = reach-mašina.

---

## Oblast 4 — Nové platformy (X, TikTok, Threads, YouTube Community)

### 4A. X / Twitter (viz i 1E pro algoritmus)
- **[DOLOŽENO/KONSENZUS]** Délka: technický limit **280 znaků** (free) / **25 000** (Premium); optimum **70–100 znaků** (17 % vyšší engagement na 71–100 zn.). *(a2b54ea6e8828c0ba, ac05ea7b06cf31f37)*
- **[KONSENZUS]** Thready fungují nejlíp **4–8 tweetů**; ALE od 03/2026 single long-form post distribučně > thread. *(a2b54ea6e8828c0ba, ac05ea7b06cf31f37)*
- **[DOLOŽENO]** Hashtagy: **1–3 relevantní** (1–2 = +21 %, více = −40 %). Ne nula. *(a2b54ea6e8828c0ba, ac05ea7b06cf31f37)*
- **[KONSENZUS]** Nativní obrázky/videa **+40 % engagement**; externí linky do reply, ne do těla. *(a2b54ea6e8828c0ba)*
- **[KONSENZUS]** Frekvence: B2B ≥2/den, B2C ≥3/den, enterprise ≥4/den; nejlepší časy všední dny 9–12 h, **středa = peak**. *(a2b54ea6e8828c0ba)*

### 4B. TikTok caption
- **[KONSENZUS]** Sweet spot **150–300 znaků**; viditelných jen prvních **~100 znaků** před „…more" → klíčové sdělení do prvních ~100 zn. *(Source Extractor a3be4c7aeda946980; Web Searcher a516abd2cc19cfc13)*
- **[KONSENZUS]** Primární SEO keyword do **prvních 50 znaků**. *(a516abd2cc19cfc13)*
- **[KONSENZUS]** **3–5 cílených hashtagů** (1 broad + 1 mid-tier + 1–2 specifické); **>5–6 = spam signál**; **NEpoužívat #fyp / #foryou** (saturované). *(a3be4c7aeda946980, a516abd2cc19cfc13)*
- **⚠️ ROZPOR V DATECH na hard limit caption:** monolit.sh uvádí limit **4 000 znaků** *(a516abd2cc19cfc13)*, ale a3be4c7aeda946980 uvádí **2 200 znaků**. → **Nutno ověřit proti oficiální dokumentaci TikToku** (pravděpodobně 2 200 pro caption historicky, 4 000 po rozšíření — v datech nerozřešeno). Pro pravidlo skillu je stejně relevantní jen sweet spot 150–300.
- **[SPORNÉ]** ER podle délky (pod 100 zn. 4,1 %; 150–300 zn. 5,3 %; 300–600 zn. 4,8 %; 600+ zn. 3,6 %; „150–300 = +18–27 % reach") — **čísla vendor blogu bez citované studie/vzorku/metodiky**, nelze nezávisle ověřit. *(a3be4c7aeda946980)*

### 4C. Threads
- **[DOLOŽENO — limit]** **500 znaků** na post (text attachment až 10 000), video do **5 minut**. *(a6a6450332070ccc4, a5cd0104a9431a278)*
- **[KONSENZUS]** Algoritmus 2026 prioritizuje **kvalitu konverzace** — repliky a repliky-na-repliky váženy vysoko, počet followerů méně důležitý než hloubka engagementu (rozdíl vs. broadcast X). For You feed je **AI-ranked** (ne čistě chronologický). *(a6a6450332070ccc4; pozn.: a5cd0104 tvrdil chronologický feed — **to je nepřesné/zastaralé**, default For You je algoritmický)*
- **[KONSENZUS]** Posty postavené na **otázce = 5–10× více replik** než oznamovací posty. *(a6a6450332070ccc4)*
- **[KONSENZUS]** Nejlíp fungují krátké konverzační posty **1–2 řádky, 3–5× týdně**, s pákou existujícího IG publika. *(a516abd2cc19cfc13)*
- **[KONSENZUS]** Doporučená kadence: 3 vlastní posty/den + 2 repliky pod každým + 5 community engagementů/den. *(a6a6450332070ccc4)*
- **[DOLOŽENO — kontext]** Threads ~**400M MAU / 115,1M DAU** (konec 2025). *(a6a6450332070ccc4)*

### 4D. YouTube Community
- **[DOLOŽENO — limity]** Text post max **2 000 znaků**; poll **2–5 možností**; min. **500 subscriberů** (dřívější požadavek 30 dní stáří kanálu **zrušen**). *(Source Extractor a5f8a69fef1819324)*
- **[KONSENZUS]** **Ankety (polls) = nejvyšší engagement** ze všech typů Community postů, překonávají textové posty **3–5×** na hlasech/komentářích. *(a5f8a69fef1819324, a516abd2cc19cfc13)*
- **[KONSENZUS]** Frekvence **2–4 posty/týden** (škáluje s velikostí: <10k = 2–3/týden, 10–100k = 3–4/týden, 100k+ = 4–7/týden); >3/týden zvedá engagement na dalším videu o ~20 %. Poll ~24 h před vydáním videa zvedá dosah premiéry. *(a5f8a69fef1819324, a516abd2cc19cfc13)*

---

## Oblast 5 — CTA & engagement mechaniky 2026

### 5A. Odpovídání na komentáře = nejsilnější doložená mechanika
- **[DOLOŽENO — Buffer ~2M postů, 03/2026]** Účty, které odpovídají na komentáře, měly: **Threads +42 %, LinkedIn +30 %, Instagram +21 %, Facebook +9,5 %, X +8 %** engagement (+Bluesky +5 %). Metodika: fixed-effects regrese (každý účet vs. sám sobě v čase, kontrola velikosti/lokality/niche). **Výhrada: korelace, ne prokázaná kauzalita** (Buffer to sám přiznává). *(a250120b47d13e0a5; verifikátoři a2a11a, a48b3e, a10b1ae, a7cad9 — všichni potvrdili verbatim, nerefutováno)*
  → **CTA pravidlo:** vyvolej komentáře a pak na ně odpovídej. „Reply-to-your-commenters" je nejlevnější reach hack 2026.

### 5B. Save/share vs. comment CTA
- **[DOLOŽENO — Hootsuite, oficiální hierarchie signálů IG 2026]** **Shares/sends přes DM = nejvýše vážený signál** (hlavně Reels), pak **saves a watch time nad liky**. Post s otázkou v caption **+37 % komentářů**; explicitní CTA **+20–30 % engagement**. *(Web Searcher a7aa52ad94fc80546)*
  → **Preferuj share-CTA („pošli to někomu, kdo…")** a save-CTA („ulož si to na později") nad prostým „komentuj". Otázka v caption je levný +37 % komentářů.

### 5C. DM-keyword automatizace (ManyChat „napiš X")
- **[KONSENZUS — vendor benchmarky, ne studie]**
  - Open rate automatických DM engaged publiku: **80–90 %**. *(ac5973c42c2dec0c9)*
  - Reply rate comment-to-DM („napiš do komentáře X, pošlu ti Y"): **50–60 %**. *(ac5973c42c2dec0c9)*
  - Odpověď **do 60 s = 21× vyšší konverze** než 30+ min zpoždění (cit. Napolify 01/2026). *(ac5973c42c2dec0c9; creatorflow.so)*
  - Click-to-sale konverze DM: **7–20 %** dle velikosti publika (micro-influenceři 10–100k: **15–20 %**; 500k+: 7–12 %). *(ac5973c42c2dec0c9, creatorflow.so)*
  - E-mail capture v DM konverzuje **40–80 %** vs. externí formulář. *(creatorflow.so)*
  - **DM konverze 3–5× vyšší než „link in bio".** *(creatorflow.so)*
- **[KONSENZUS]** **Link v biu má CTR jen ~5 %** (Sprout Social); DM ho překonává díky přímému doručení. *(ac5973c42c2dec0c9)*
  → **CTA pravidlo:** DM-keyword („napiš AI do komentáře") > link in bio > link v postu. Micro-účty (SMB cílovka) mají nejvyšší konverze.

### 5D. LinkedIn repost mechanika
- **[DOLOŽENO — MagicPost korpus 1,2M+ originálů vs. 13,8k repostů, 07/2026]** Medián: **originál 28 liků / 6 komentářů**, **repost s komentářem 8 liků / 0 komentářů**, **holý one-click repost 2 liky / 0 komentářů** (~14× méně než originál). *(Source Extractor acf2b0f7aee917a50, a7aa52ad94fc80546)*
  - Vlastní komentář ~**4× zvedne** holý repost, ale i tak repost vydělá **<⅓** toho co originál.
  - **Minimum při repostu: alespoň 2 věty vlastního komentáře.** „Great post, worth a read" = penalizace repostu bez benefitu.
  - Reshare vlastního silného postu: počkat **24–48 h** po publikaci (až se křivka zploští), jednou.
  - Výhrada: jen MagicPost data, žádná externí studie/oficiální LinkedIn zdroj.
  → **CTA pravidlo:** repost jen s ≥2 větami vlastní myšlenky; jinak nemá cenu. Radši napsat originál.

### 5E. Comment-to-unlock / urgency / personalizace
- **(V nasbíraných datech nedoloženo:** konkrétní čísla pro „comment-to-unlock" mechaniku ani pro urgency/personalizaci CTA. Fráze „comment-to-unlock" se v žádné fetchnuté stránce nevyskytuje — byla jen v zadání. Nejblíž je comment-to-DM automatizace v 5C. **Bude potřeba doplnit rešerši**, pokud to má být samostatné pravidlo.)

---

## Oblast 6 — Anti-AI-slop (jak se pozná AI post 2026 + pravidla pro lidský text)

### 6A. Proč to je konkurenční výhoda (tvrdá čísla)
- **[DOLOŽENO — Originality.ai, 8 795 postů, k 10/2024]** ~**54 % dlouhých (100+ slov) LinkedIn postů je odhadem AI-generovaných** — AI je na LinkedIn většinová norma → lidsky znějící text = diferenciátor. Follow-up (3 368 postů, 2025) potvrdil **53,7 %** i v 2025. *(Source Extractor a87a3b48b24bd4724; verifikátor a1c83e potvrdil verbatim, medium confidence)*
  - **Výhrada:** vendor detekční firma, vlastní detektor s prahem ≥0,5, EN long-form vzorek, detektory mají false-positive problém u „vypiplaného" profesionálního psaní → **klasifikovat jako odhad, ne tvrdý fakt.**
- **[DOLOŽENO]** Pravděpodobně-AI post měl **−45 % engagement** vs. pravděpodobně-lidský (analýza 2 726 postů). *(a87a3b48b24bd4724)*
- **[DOLOŽENO]** Po ChatGPT (konec 2022): +189 % používání AI v LinkedIn postech, +107 % délka AI long-form postů. → **delší ≠ lepší; AI-bloat je rozpoznatelný.** *(a87a3b48b24bd4724)*

### 6B. Detekční vzory (co AI post prozrazuje) — kanonický katalog
Nejtvrději doložený zdroj = **Wikipedia „Signs of AI writing" (WikiProject AI Cleanup)**, katalog z tisíců reálných příkladů. *(Source Extractor aa52b80be6480d772)*

- **[DOLOŽENO]** **Negativní paralelismus:** *„not just X, but also Y"* a **„it's not X, it's Y"** = explicitně dokumentovaný AI tell. **→ potvrzuje podezření ze zadání.** *(aa52b80be6480d772)* Forbes (03/2025) totéž: *„It's not about working harder, it's about working smarter"* = prázdná AI fráze. *(af907f1095541f00c)*
- **[DOLOŽENO]** **Rule of three** (tři přídavná jména / tři krátké fráze za sebou) nadužívané = AI tell. *(aa52b80be6480d772)*
- **[DOLOŽENO]** **Em-dash (—) nadužívání** k oddělování vět = jeden z nejsilnějších formátovacích tellů. *(aa52b80be6480d772, a5550dfc81cffc906)* — pozn.: mírně kontrariánsky, em-dash používají i lidé → viz 6D false positives.
- **[DOLOŽENO]** Další formátovací telly: mechanické **tučnění klíčových slov**, **dekorativní emoji jako odrážky/oddělovače**, **Title Case v nadpisech**, **„chytré" oblé uvozovky/apostrofy** místo rovných. *(aa52b80be6480d772)*
- **[DOLOŽENO]** **Mechanické přechodové fráze:** „First and foremost", „In addition to this", „Furthermore", „Moreover", „Last but not least" = jasný signál AI. *(af907f1095541f00c, a5550dfc81cffc906)*
- **[DOLOŽENO]** **AI slovník (mění se s generací modelu):** GPT-4 éra: *delve, tapestry, testament, intricate, pivotal, landscape*; GPT-4o: *enhance, showcasing, highlighting, fostering, align with*; GPT-5+: *emphasizing, enhance, highlighting, showcasing*. Jedno slovo nic, **kumulace = nejsilnější tell.** *(aa52b80be6480d772)*
- **[DOLOŽENO — Ramonov blacklist, 50+ slov]** Přímo použitelný zákazový seznam: *delve, embark, game-changer, unlock, skyrocket, revolutionize, dive deep, unveil, pivotal, furthermore, moreover, testament, landscape, ever-evolving, illuminate, harness, groundbreaking, cutting-edge, remarkable…* + filler *just, very, really, literally, actually, basically*. *(Source Extractor a5550dfc81cffc906)*
- **[DOLOŽENO — Forbes/LinkedIn]** **Předvídatelná šablona** (úvod → 3 body → závěr; nebo problém → řešení → CTA) = AI formule. **Dokonalá symetrie odstavců** = AI tell; lidský text má přirozený tok a nedokonalosti. *(af907f1095541f00c)*
- **[DOLOŽENO]** **Generický engagement-bait závěr:** *„What do you think? Drop your thoughts below!"*, *„Do you agree? Let me know in the comments!"* = standardní AI closer. *(af907f1095541f00c)*

### 6C. Pozitivní pravidla pro lidský text
- **[DOLOŽENO/KONSENZUS]** Krátké, jednoduché věty, aktivní rod; **mix délek vět (burstiness)**; psát konverzačně („write like you talk"); sdílet konkrétní osobní zkušenosti/detaily; **porušovat formátovací pravidla, kde to dává smysl.** *(af907f1095541f00c, a5550dfc81cffc906, a7c4fc8450dc92542)*
- **[DOLOŽENO — Ramonov, social-specific]** U social obsahu navíc **zakázat hashtagy, markdown, hvězdičky, přemíru emoji.** *(a5550dfc81cffc906)*
- **[KONSENZUS — Forbes LinkedIn]** Čtenáři poznají AI podle: okaté přechody, buzzwordy bez konkréta, podezřele dokonalá symetrie, generický engagement bait, **absence osobních detailů**. *(a7c4fc8450dc92542)*

### 6D. Důležitá pojistka proti přehnaným zákazům (nehalucinovat detekci)
- **[DOLOŽENO]** **Žádný jednotlivý znak není důkaz.** Wikipedia i kontrariánské zdroje varují: tyto prvky jsou jen **potenciální signály**, vyskytují se i v lidských textech (editorialy, blogy), a lidské psaní se vlivem LLM AI-stylu přibližuje → **heuristiky, ne binární detektor.** *(aa52b80be6480d772, robotsatemyhomework substack)*
- **[DOLOŽENO — studie 2025]** Běžní čtenáři rozpoznají AI text **na úrovni náhody**; jen **intenzivní uživatelé LLM** poznají AI v ~**90 %**. Detekční nástroje mají netriviální chybovost. → „čtenáři poznají AI post" platí hlavně pro power-usery a specificky pro **LinkedIn/B2B** publikum, ne pro průměrné IG/FB publikum. *(aa52b80be6480d772)*
- **[KONSENZUS]** Em-dash je nejčastější false positive (používají ho i lidé) → nezakazovat úplně, jen omezit nadužívání. *(robotsatemyhomework; shoduje se s naší CLAUDE.md poznámkou)*

---

## TOP 20 akčních pravidel pro AI copywritera 2026

Seřazeno podle dopadu (nejsilnější doložený efekt nahoře). Formulováno jako přímé instrukce.

1. **Odpovídej na komentáře — nejsilnější doložený reach hack.** Piš post tak, aby vyvolal komentáře, a pak na ně reaguj. Doložený lift: LinkedIn +30 %, IG +21 %, Threads +42 %, FB +9,5 %, X +8 %. *(Buffer ~2M postů 2026)*
2. **LinkedIn hook do 210 znaků.** Nad zlomem „…more" se zobrazí jen ~210 znaků; první řádek láme scroll, poslední řádek před „see more" slibuje payoff. Jediný úkol téhle části = klik na „…more". *(Welsh 2026)*
3. **LinkedIn: piš carousel/dokument, ne čistý text.** Pořadí ER: carousel 21,77 % ≫ video 7,35 % > image 6,52 % > link 3,81 % > text 3,18 %. Text a link jsou nejslabší. *(Buffer 52M 2026)*
4. **Instagram: max 5 hashtagů (hard limit 12/2025), úzce cílených, žádné generické** (#fyp/#explore mohou uškodit). *(Mosseri/IG 12/2025 — DOLOŽENO)*
5. **Facebook: link NEDÁVEJ do těla postu — dej ho do prvního komentáře.** Link posty mají <2 % zobrazení feedu; Meta navíc testuje limit link postů u neověřených professional/Page účtů. Komentáře limit neomezuje. *(Meta/TechCrunch 12/2025)*
6. **LinkedIn/X: hodnotu nes v textu postu, link jen „rozšiřuje", nikdy nenese.** Link v těle snižuje reach (−18,8 až −60 %). Buď do 1. komentáře, nebo vynech u awareness postů. *(van der Blom, Ordinal, Metricool 2026)*
7. **Použij DM-keyword CTA místo „link in bio".** „Napiš X do komentáře, pošlu ti Y": reply rate 50–60 %, DM open 80–90 %, konverze 3–5× vs. link in bio (CTR ~5 %). *(vendor benchmarky 2026)*
8. **Instagram: preferuj share-CTA a save-CTA nad „komentuj".** Shares/sends přes DM = nejvýše vážený IG signál 2026; saves > liky. Otázka v caption = +37 % komentářů levně. *(Hootsuite 2026)*
9. **X: piš 71–100 znaků; jeden long-form post > thread; 1–2 hashtagy (ne víc).** 71–100 zn. = +17 % engagement; >2 hashtagy = −40 %; od 03/2026 long-form distribučně poráží thready. *(open-source kód X 2026)*
10. **Carousel: první slide je HOOK, ne cover.** Bez hook slidu nikdo neswipuje. IG i LinkedIn. *(morphica, Welsh 2026)*
11. **Carousel délka: 6–10 slidů; na LinkedIn ostře řež po 10 (pak engagement padá).** *(blog 2026)*
12. **Zakázaný slovník + em-dash pod kontrolou.** Nikdy: delve, unlock, skyrocket, game-changer, dive deep, furthermore, moreover, testament, landscape, groundbreaking, cutting-edge + „First and foremost / Last but not least". Em-dash jen výjimečně. *(Wikipedia AI Cleanup + Ramonov)*
13. **Nikdy „it's not X, it's Y" ani „not just X, but also Y".** Nejsilnější AI tell 2026. Stejně tak rule-of-three nadužívání. *(Wikipedia AI Cleanup, Forbes)*
14. **Nepiš šablonu (úvod → 3 body → závěr). Variuj strukturu mezi posty.** Dokonalá symetrie odstavců = AI tell; lidský text má nedokonalý tok. *(Forbes 2025)*
15. **Vyhýbej se generickému closeru „What do you think? Drop your thoughts below."** Místo toho konkrétní, osobní, konverzační výzva. *(Forbes 2025)*
16. **LinkedIn formátování: věty ~5 slov, odstavce ~7 slov (1 věta + vzduch), bloky po 3 řádcích s prázdnými řádky mezi.** *(Welsh 2026)*
17. **Použij re-hook (2. řádek přidá curiosity po hooku).** Struktura Hook → Re-hook → Lead → Body → Power-ending → CTA. *(Lara Acosta — pozn.: 1 zdroj)*
18. **TikTok: klíčové sdělení + SEO keyword do prvních ~100 znaků; caption 150–300 znaků; 3–5 hashtagů, ne #fyp/#foryou.** *(blogy 2026)*
19. **Threads/YT Community: postav post na OTÁZCE.** Threads: otázka = 5–10× víc replik. YT Community: poll = nejvyšší engagement, 3–5× nad text. *(blogy 2026)*
20. **LinkedIn repost jen s ≥2 větami vlastní myšlenky.** Holý one-click repost = 2 liky (~14× méně než originál); komentář ho 4× zvedne, ale i tak <⅓ originálu. Radši napiš originál. *(MagicPost 1,2M postů 2026)*

---

## Klíčové mezery v datech (kde doplnit rešerši)

1. **Alex Hormozi Hook-Retain-Reward** — jen search snippety, žádná hloubková extrakce číselných pravidel. *(Oblast 2D)*
2. **Comment-to-unlock mechanika** — v datech vůbec (fráze jen v zadání); jen příbuzná comment-to-DM. *(Oblast 5E)*
3. **Urgency / personalizace CTA čísla** — nedoloženo. *(Oblast 5E)*
4. **TikTok hard limit caption** — rozpor 2 200 vs. 4 000 znaků, nerozřešeno; ověřit oficiální dokumentaci. *(Oblast 4B)*
5. **IG carousel 4:5 vs. 1:1 přímé srovnání výkonu** — konsenzus 4:5, ale bez head-to-head dat. *(Oblast 3A)*
6. **Re-hook framework** — stojí na jediném zdroji (magicpost.in); anotace zadání byla nepřesná (Acosta článek re-hook nezmiňuje). *(Oblast 2B)*
7. **Nicolas Cole / Ship 30** — jen high-level (Hook-Story-Offer, Atomic Essay ~250 slov), žádná číselná pravidla. *(Oblast 2C)*
8. **Brunson (Perfect Webinar / Epiphany Bridge)** — v datech nedoloženo pro social posty (patří spíš do webinar skillu).
