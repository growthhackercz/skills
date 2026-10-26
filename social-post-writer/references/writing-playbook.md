# Writing Playbook — jak psát social posty 2026

Techniky psaní napříč sítěmi (per-síť čísla jsou v `platform-params.md`). Podklad: `RESEARCH-2026.md`. Heuristiky, ne dogma — [DOLOŽENO] = studie, [KONSENZUS] = praktici.

---

## 1. Struktura postu

Základní kostra (funguje na LinkedIn, FB, delší IG caption):

```
HOOK        1. řádek — zlomí scroll. Nejdůležitější prvek celého postu.
RE-HOOK     2. řádek — přidá zvědavost, slíbí payoff (co čtenář získá).
BODY        jádro — jedna myšlenka, krátké odstavce, konkrétno.
CTA         výzva — konkrétní akce (viz §5). Ne generická.
```

- [KONSENZUS] Welsh: **tělo piš první, hook až potom.** Anatomie „Trailer → Meat → CTA": trailer = vše nad zlomem „…more", meat = tělo, zakončení = výzva ke konverzaci nebo akci.
- [KONSENZUS] Acosta 6 kroků: **Hook → Re-hook → Lead (co se naučíš) → Body → Power-ending (2řádkové shrnutí) → CTA.** (Re-hook stojí na jednom zdroji — ber jako doporučení, ne zákon.)
- [DOLOŽENO] *„První řádek je důležitější než 95 % zbytku postu."* (Welsh) → na hook dej nejvíc práce.

### Karusel — 6 beatů (každý beat dělá copy job i visual job)

**Hook → Promise → Pull → Payoff → Ask.** Karusel se nevypráví jako seznam, ale jako příběh třemi kanály najednou (co říkáš · jak je to postavené · jak to vypadá):
- **Hook** (slide 1 / cover): zastav scroll. **Cover rule: 3 elementy · 2 barvy · 1 slovo výrazně větší** — vyznač klíčové slovo pro akcent (jde do `visual-briefs.json`).
- **Promise** (slide 2): potvrď hook — co čtenář získá, když doswipuje. Bez něj odejde u slidu 3.
- **Pull → Payoff** (slidy 3–N): jedna myšlenka/slide, **open loops** (naznač, dořeš na dalším slidu), eskalace, pattern interrupt — pozornost se získává **znovu každý slide**, ne jen jednou hookem.
- **Ask** (poslední slide): jedno konkrétní CTA.
- **Packaging:** text vypálený na slide **neopakuje** caption/titulek — doplňuje ho (jiná slova, ne kopie).

## 2. Hook — první řádek

Tři rysy silného hooku [KONSENZUS, Acosta]: (1) vyvolá **zvědavost**, (2) obsahuje **konkrétní číslo / nástroj / insight**, (3) slíbí **akční radu**.

**Climax-led, ne forced:** míř hook k **vrcholu obsahu**, ne k uměle šokující kontroverzi. Nejlepší otvírák je destilát nejsilnějšího momentu kusu, ne nalepená provokace.

Pravidla:
- **„Jak jsem" místo „Jak na"** — osobní zkušenost táhne víc než návod z třetí osoby.
- Hook ~6 slov, konkrétní, bez omáčky. Nevyzrazuj pointu (zvědavost = důvod číst dál).
- U IG do 125 zn., LinkedIn do ~210 zn. (viditelná část), TikTok/video do prvních 1–2 vteřin.

Archetypy (fill-in-the-blank, z katalogu 200+ šablon od top tvůrců — [KONSENZUS], bez výkonnostních dat):

| Archetyp | Vzor (CZ) |
|---|---|
| Transformace s výsledkem | „Jak jsem z [výchozí stav] udělal [výsledek] za [čas]." |
| Kontrariánský | „Proč [běžná rada] je špatně (a co dělat místo toho)." |
| Podmínkové varování | „Pokud [neděláte X], nečekejte [výsledek]." |
| Číslo / seznam | „3 věci, které [cílovka] dělá špatně u [téma]." |
| Otázka | „Co kdyby [žádoucí stav bez obvyklé překážky]?" |
| Výsledek napřed | „Z 0 na [výsledek] za [čas]. Takhle:" |

**Postup:** vygeneruj hooky v **typech** (kontrariánský · pattern interrupt · identity call-out · curiosity gap · stat shock) a **označ 2 nejlepší** pro daný kus — klient/dirigent vybere finální.

## 3. Typy postů (taxonomie)

Ne každý post je stejný. Vyber typ podle cíle kusu a drž jeho kostru:

| Typ | Kdy | Kostra |
|---|---|---|
| **Návod / how-to** | vzdělávat, saves | problém → kroky (číslované) → výsledek. Ideál pro carousel. |
| **Příběh** | budovat vztah, dwell | situace → zvrat/komplikace → poučení. Osobní detaily = anti-slop palivo. |
| **Kontrariánský** | dosah, diskuze | běžný názor → proč je špatný → co místo toho. Vyvolá komentáře. |
| **Case study / důkaz** | konverze | výchozí stav → co jsme udělali → **výsledek v číslech**. |
| **Social proof** | důvěra | cizí výsledek / citace zákazníka → co z toho plyne pro čtenáře. |
| **Promo / nabídka** | prodej | problém → řešení (produkt) → 1 jasné CTA. **Střídmě** — ne většina obsahu. |

Kontrariánský a příběh nejlíp plní nejsilnější hack 2026: **vyvolat komentáře** (viz §5).

## 4. Formátování (skenovatelnost)

[KONSENZUS, Welsh] — hlavně LinkedIn, přiměřeně FB/delší IG:
- **Věty ~5 slov** (proti průměru 10), **odstavce ~7 slov** = jedna věta + prázdný řádek („vzduch").
- **Bloky po ~3 krátkých řádcích**, oddělené **prázdnými řádky**.
- **Každý řádek obstojí sám** — čtenář skenuje, ne čte souvisle. Šipky/čísla vedou oko.
- **Mix délek vět (burstiness)** — střídej krátké a delší. Monotónní rytmus = AI tell (viz §6).
- Bez markdown (`**`, `#`) v těle postu — sítě ho nerenderují, vypadá jako slop.

## 5. CTA a engagement mechaniky

Pořadí podle doloženého dopadu:
1. [DOLOŽENO] **Piš post tak, aby vyvolal komentáře** — odpovídání na komentáře je nejsilnější reach hack 2026 (LinkedIn +30 %, IG +21 %, Threads +42 %). Otázka na konci, kontrariánský názor, „souhlasíte?".
2. [DOLOŽENO, IG] **Share-CTA a save-CTA nad „komentuj":** „pošli to někomu, kdo…", „ulož si na později". Shares/sends přes DM = nejvýš vážený IG signál 2026.
3. [KONSENZUS] **DM-keyword místo „link in bio":** „napiš AI do komentáře, pošlu ti [lead magnet]" — reply rate 50–60 %, konverze 3–5× vs. link in bio. Nejsilnější u SMB účtů.
4. [DOLOŽENO] **Otázka v caption = +37 % komentářů.** Levné a účinné.
5. **Link:** FB/LinkedIn do 1. komentáře (ne do těla), nebo vynech u awareness postů (viz `platform-params.md`).

Vždy **jedno** CTA na post. Konkrétní, ne „klikněte sem" / „sledujte nás".

## 6. Anti-AI-slop (aby text nezněl generovaně)

[DOLOŽENO] AI je na LinkedIn většina (~54 % dlouhých postů) a AI-post má **−45 % engagement**. Lidsky znějící text = měřitelná výhoda, ne kosmetika.

### Zakázané konstrukce (nejsilnější telly)
- **„Není to X, je to Y"** a **„nejen X, ale i Y"** — nejsilnější AI tell 2026. Nikdy.
- **Trojice** (tři přídavná jména / tři fráze za sebou) nadužívané — „rychlé, chytré a efektivní".
- **Mechanické přechody:** „Za prvé a především", „Kromě toho", „A v neposlední řadě", „Souhrnem".
- **Generický closer:** „Co myslíte? Napište do komentářů!", „Souhlasíte? Dejte vědět!" → nahraď konkrétní osobní výzvou.
- **Předvídatelná šablona** (úvod → 3 body → závěr). Variuj strukturu mezi posty; dokonalá symetrie odstavců = tell.

### Zakázaný slovník
- **Česky (AI klišé):** „v dnešní digitální/uspěchané době", „posuňte to na další úroveň", „pojďme se ponořit", „ne náhodou", „doslova", „klíčový/zásadní" (nadužité), „revoluční", „inovativní řešení", „svět [čehokoli]", „nebojte se", „a to je přesně důvod, proč".
- **Anglicky (pro EN posty):** delve, unlock, skyrocket, game-changer, dive deep, unveil, furthermore, moreover, testament, landscape, groundbreaking, cutting-edge, elevate, harness, seamless + filler just/very/really/actually/basically.
- Jedno slovo nevadí; **kumulace** je tell.

### Em-dash a interpunkce
- **Em-dash (—) jen výjimečně.** Nadužívání je silný formátovací tell (a v rozporu s CliqSales stylem). Většinou stačí čárka, dvojtečka, závorka nebo tečka a kratší věta.
- Bez dekorativních emoji jako odrážek/oddělovačů; bez mechanického **tučnění** klíčových slov v těle postu.

### Pozitivní pravidla (čím to nahradit)
- Piš, jak mluvíš. Krátké věty, aktivní rod, **mix délek** (burstiness).
- **Konkrétní osobní detail** (číslo, jméno nástroje, reálná situace) — AI píše obecně, člověk konkrétně.
- Klidně poruš formátovací pravidlo, kde to dává smysl — přirozený tok > dokonalá symetrie.

### Pojistka (nehalucinovat detekci)
[DOLOŽENO] Žádný jednotlivý znak není důkaz — jsou to **potenciální signály**, vyskytují se i v lidských textech. Běžní čtenáři poznají AI text na úrovni náhody; spolehlivě jen power-useři a hlavně **B2B/LinkedIn** publikum. Cíl je **znít lidsky**, ne paranoidně mazat každou pomlčku. Burstiness + osobní konkrétno vyřeší většinu.

---

## Zdroje
Justin Welsh (LinkedIn 2026), Lara Acosta, Nicolas Cole / Ship 30, Kleo hook katalog (200+ šablon), Wikipedia „Signs of AI writing" (WikiProject AI Cleanup), Buffer / Hootsuite / Metricool 2026, Originality.ai. Detail + klasifikace v interním podkladu `RESEARCH-2026.md` (dev-lab, není součástí fleet distribuce).
