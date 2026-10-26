# Směr — Web DNA, jeden commitnutý koncept, webDNA.md

Načti ve fázi konceptu (před generováním čehokoli). Po commitu světa se k tomuto
souboru už nevracíš — rozhodnutí žijí ve `webDNA.md`.

## Proč tenhle mechanismus existuje

Model postavený před volný brief vybere svůj nejlíp hodnocený nápad — a ten je
u každého běhu stejný. Výsledek na fleetu: stovky klientů, jeden „prémiový"
vzhled. Bezpečné provedení je v bezobslužné práci to známé riziko, ne jistota.

Dvě mechanické pojistky:

1. **Web DNA generátor (`scripts/concept-seed.py`)** — směr přiřazuje externí seed
   odvozený z klientského slugu, ne tvoje preference. Deterministický:
   stejný klient = stejný směr (opakovatelnost), jiný klient = jiný směr
   (žádný fingerprint).
2. **Jeden commitnutý koncept, ne menu.** Nabídka tří vyvážených kandidátů
   svádí klienta k nejbezpečnější kartě. Prezentuje se JEDEN směr naplno +
   pojmenované alternativy + tichý „klasický" východ.

## Krok 1: Vygeneruj Web DNA

```bash
python3 {baseDir}/scripts/concept-seed.py --slug <projekt-slug> --purpose web
```

Vrátí: přiřazený směr (z katalogu ve skriptu) + 2 vyzyvatele + **chrome roll**
(header varianta, umístění hero textu, tvar CTA). Chrome je samostatná osa
kostky: směr chrání před stejností světů, chrome před stejností SKELETU —
bez něj každý web skončí jako „malé logo vlevo + pill CTA vpravo + centrovaný
hero" (reálný nález z prvních dem). Chrome roll platí stejně jako směr:
přebít ho smíš jen s pojmenovaným důvodem zapsaným ve webDNA.md; kanonické
příklady v dokumentaci jsou zdroj ENGINU, nikdy zdrojem hlavičky/skeletu.
**Zákon soudržnosti kompozice:** u centrovaného hero tvoří logo → tag →
h1 → sub JEDEN vertikálně centrovaný blok — logo klesá k obsahu (nebo je
přímo součástí hero), NIKDY nevisí samo přilepené u horního okraje, zatímco
text sedí ve středu. Roztržená kompozice = rozpadlý hero.
Skript se NIKDY nepřeskakuje u nového webu — psát kód před jeho během je
porušení kontraktu. Výjimky, kdy se Web DNA NEgeneruje:

- Klient dal `direction` referenci (screenshot/URL) — explicitní vůle přebíjí Web DNA.
- Klient si výslovně vyžádal konkrétní směr („chci to minimalistické a světlé").
- Iterace existujícího projektu (svět už je commitnutý ve `webDNA.md`).

Vlastní re-roll smíš jen z pojmenovaného věcného důvodu (směr neunese
produktová fakta nebo účel stránky) — „nelíbí se mi" důvod není. Klient smí
re-roll kdykoli; po dvou re-rollech se zeptej, jaká kvalita chybí.

**Web DNA přiřazuje formu, ne tón.** U vážných oborů (pohřebnictví,
zdravotnictví, právo, krizové služby) směr nejdřív přelož do vážné polohy —
včetně FONTU: display s výraznou osobností (Unbounded, Anton, Alfa Slab…)
vážný obor neunese — vezmi nejcivilnější řez z poolu, nebo přebij na
civilní grotesk (Archivo / Hanken Grotesk / Inter Tight) s důvodem ve
webDNA.md. Hravý font na zdravotnickém produktu = ztráta důvěry —
např. „Bauhaus Playful" → geometrická přísnost bez hravosti. Když směr
vážnou polohu neunese, je to přesně legitimní věcný re-roll: pojmenuj to
(„playful forma neunese pietní službu") a hoď znovu.

## Krok 2: Rozviň přiřazený směr do konceptu

Koncept = konkrétní procházka stránkou, ne teze. Vyprávěj, co návštěvník
VIDÍ: co je v prvním viewportu a v jakém měřítku, co se stane při rolování,
jak sekce navazují, kde je hlavní akce. Pokud koncept přečtený nahlas zní
jako nálada („moderní, čistý, prémiový"), není hotový — chybí mu rozhodnutí.

**Test paměti:** kdyby návštěvník odešel po prvním viewportu, co popíše
kamarádovi za hodinu? Když je poctivá odpověď „takový hezký web", koncept
nemá tezi.

## Krok 3: Sparring (nikdy sebe-review)

Než koncept ukážeš klientovi, nech ho napadnout čerstvým subagentem.
Podle běhového prostředí: v OpenClawu `sessions_spawn` a výsledek vyzvedni
přes `sessions_yield`; v Claude Code nativní `Agent`. 🛑 Nikdy nevolej
`/api/spawn` napřímo. Když ani jedna cesta není dostupná, sparring **vynech
a napiš to** — nikdy si koncept nekritizuj sám, sebe-review nic nenajde.
Subagent dostane: koncept + brand kontext +
účel stránky. NIKDY nedostane tvoje zdůvodnění ani informaci, že jsi autor.

Zadání pro subagenta: (a) napadni koncept — je teze čitelná? unese produktová
fakta? je první viewport sdělení, nebo dekorace? (b) navrhni jeden divoký
úhel, který autor nezvážil. Co přežije, zapracuj. Sparring je kritika
strategie — subagent nikdy nepíše copy, kód ani designová rozhodnutí.

## Krok 4: Prezentuj klientovi — jeden směr naplno

Struktura prezentace:

1. **Přiřazený směr, plně commitnutý** — jméno, teze, procházka stránkou,
   paleta (přesné hexy), typo pár, podpisová interakce, poctivé riziko.
2. **Alternativy (max 2, jen jménem + jednou větou)** — vyzyvatelé z Web DNA.
   Nikdy je nerozváděj do stejné hloubky, jinak vyrábíš menu.
3. **Tichý klasický východ** — jedna věta: „Kdybyste chtěli konzervativní
   řešení podle standardu oboru, jde to taky." Nikdy ho nedoporučuj, nikdy
   neshazuj. Když ho klient vezme, proveď konvenci na plné řemeslo, bez ironie.
4. **(Web) nabídka videoscrollu** — jedna věta s cenou, viz SKILL.md.

→ **STOP. Čekej na volbu klienta.**

## Krok 5: Commit světa → webDNA.md

Po volbě zapiš do `<slug>/webDNA.md` — je to kontrakt pro celý build a přežije
kompaktaci kontextu (chat ne):

```markdown
---
skillVersion: "1.3.4"
---

# webDNA — <projekt>
## Teze
<jedna věta: jaká myšlenka stránku vlastní + jaké oborové klišé odmítá>
## Směr
<jméno směru z Web DNA / z reference> · identity_source: brand | experiment(<citace souhlasu>)
## Paleta
<role: přesné hexy + strategie: Zdrženlivá / Commitnutá / Plná / Ponorná>
## Typografie
display: <font + proč> · body: <font> · škála: <hodnoty>
## Motion
concept_seed: <slug ze concept-seed.py, u dashboardu a aplikace `none`>
tier: <0-3>
signature ease: <CustomEase data> · podpisový moment: <co>
## Kompozice
hero: <archetyp> · hero_mode: scene | classic-image | classic-video
· anchors per sekce: <seznam> · rytmus: <dense/calm mapa>
## Chrome (z rollu concept-seed, přebití jen s důvodem)
header: <varianta z rollu> · hero text: <placement z rollu> · CTA tvar: <z rollu>
· beat placement vzor (videoscroll): <např. „L → velký centrální → P → finále centr">
## Assety
role referencí: <soubor → direction/identity/asset/content> · řetěz: <pořadí>
## Sitemap (multipage)
<stránka → účel → anchors>
## Zákazy pro tento svět
<2-4 věci, které tento svět nikdy neudělá>
```

Pravidla po commitu:

- **Build čte webDNA.md, nerozhoduje znovu.** Tichá revize palety/typa/teze
  v půlce buildu je porušení kontraktu.
- Brány smí zabít vadu (kontrast, chybějící stav, klišé), **nikdy rozhodnutí**
  zapsané ve webDNA.md. Když brána opakovaně padá na světě samotném (2×),
  vrať se ke klientovi — neřeď svět potichu.
- Každý brand má vlastní svět. Nikdy nereskinuj stránku postavenou dřív
  v této session (stejná kostra + nové barvy = dva průměrné weby místo
  jednoho dobrého).

## Barevná strategie (rozhodni před výběrem barev)

- **Zdrženlivá** — neutrály + 1 akcent. Default pro Operate/Read účely.
- **Commitnutá** — jedna sytá barva nese 30–60 % plochy.
- **Plná paleta** — 3–4 pojmenované role.
- **Ponorná** — plocha JE barva.

Persuade/Experience stránky mají povolení k odvážnějším strategiím — ber je,
když to brief dovolí. Barva commituje v měřítku stránky (pole vlastnící celé
regiony), ne jako akcenty rozsypané po neutrálu. Světlý/tmavý režim není
kategorie defaultu: napiš jednu větu fyzické scény (kdo, kde, při jakém
světle stránku používá) a nech ji rozhodnout.
