---
name: content-ideation
description: "Zásobník nápadů na obsah: překládá reálné signály trhu (trendy, otázky zákazníků, pozice v Googlu) na konkrétní obsahové nápady s doloženým skóre a spravuje backlog. Použijte na „dejte mi nápady, o čem psát", při týdenním plánování obsahu nebo když je potřeba zaplnit mezeru v obsahu."
status: ready
version: "2.0"
publishedAt: "2026-07-07"
category: content
metadata: {"openclaw":{"emoji":"💡"}}
---

# Content Ideation

<!-- v2 REWORK (2026-07-07): překladač TRH→BYZNYS + správce zásobníku. Vymýšlení „z hlavy" nahrazeno
     vstupní kaskádou reálných signálů; skóre s doloženým zdrojem; TTL; stopa původu; cesty /documents/content/.
     Verze 2.0 (generace 2, sjednoceno 2026-07-07). -->

Dělník vrstvy Rozhodování. V řetězu enginu: **scout NAJDE → ideation VYMYSLÍ A SEŘADÍ → strategist VYBERE → writeři VYROBÍ.**

Tvoje práce je **průnik: co trh říká × co firma prodává × jaký formát to unese**. NEopakuješ clustering scouta (ten už témata má), NEvymýšlíš z imaginace (bez podkladu jen jako poctivě označený poslední stupeň) a NErozhoduješ, co se publikuje (to je strategist/klient).

## Vstupní kaskáda (degradační žebřík — NIKDY neblokuj)

Vezmi nejvyšší dostupný stupeň; vždy klientovi řekni, z čeho vycházíš:

1. **Čerstvé tržní signály** — `/documents/content/research/runs/<slug>/<datum>/brief.json` od content-scoutu, **max 7 dní starý** (0 kreditů navíc, jen čtení). Témata, virály, úhly, hooky, otázky.
2. **Vlastní zákazníci a web** — wiki / AI Data Center: otázky zákazníků z hovorů a e-mailů + content-gap položky („ptají se, nemáme obsah") · `/documents/content/seo-keywords.json` (clustery, striking-distance příležitosti od seo-strategista).
3. **Brand + Product DNA** — `/documents/brand/brandDNA.md` + `/documents/brand/products/*/productDNA.md`. Nápady z tohoto stupně **poctivě označ**: *„zatím bez tržních signálů — až připojíme trendy, zpřesní se"*.

Vždy navíc: `/documents/content/content-log.md` (co už vyšlo — žádné opakování do 60 dní) a stávající backlog `/documents/content/ideas.json` (dedup i vůči navrženým/odmítnutým).

## Generování: průnik signál × produkt × formát

Z každého silného signálu vyrob konkrétní nápad NAPOJENÝ na byznys klienta:

> signál „lidé řeší domácí espresso" × produkt „prodáváme zrnkovou kávu" × formát → **„Průvodce: espresso doma ze zrnkové do 5 000 Kč"** (článek-návod) + série 3 postů + newsletter

Ověřené vzory (použij, když sedí na signál): vyřešený problém zákazníka · opakovaná otázka publika · contrarian pohled na běžnou radu v oboru · reálná data/čísla klienta (vždy, když existují — jsou ze své podstaty unikátní) · „co bych si přál vědět, když jsem začínal" · srovnání X vs Y · chyby a selhání · zákulisí procesu.

**Hook je důležitější než téma.** Každý nápad má napsaný první řádek, který zastaví scroll — bez hooku není co prezentovat. Cíl: 10+ surových nápadů → obodovat → prezentovat max 5.

## Skóre s dokladem (žádná vymyšlená čísla)

5 dimenzí, každá 1–5 **s uvedeným zdrojem**. Průměr = skóre nápadu.

| Dimenze | Doklad (odkud se bere) |
|---|---|
| **Poptávka** | scout: engagement/počet kusů k tématu · GSC: imprese dotazů · wiki: kolik zákazníků se ptalo |
| **Byznys** | vazba na konkrétní produkt/službu z DNA (co z toho firma má) |
| **Mezera** | content-log (nepsali jsme o tom?) + wiki content-gap (chybí odpověď?) |
| **SEO příležitost** | seo-keywords.json: cluster, striking-distance (pozice 8–25) |
| **Úhel/hook** | jediná subjektivní dimenze — síla úhlu a hooku (přiznaně úsudek) |

Bez dokladu pro dimenzi → skóruj střed (3) a napiš „bez dat". Nafouknuté skóre je zakázané — 2 v jedné dimenzi je v pořádku, když jsou ostatní silné.

**Prahy:** 4.0+ = do plánu do 7 dnů · 3.0–3.9 = do 2–4 týdnů · 2.0–2.9 = zaparkovat (chce lepší úhel) · pod 2.0 = zabít.

## Backlog `/documents/content/ideas.json`

```json
{
  "ideas": [
    {
      "id": "espresso-doma-pruvodce",
      "title": "Espresso doma ze zrnkové do 5 000 Kč",
      "hook": "Nepotřebujete kávovar za třicet tisíc. Potřebujete tři věci a jedna stojí stovku.",
      "angle": "cenová bariéra je hlavní otázka signálu — rozbij ji konkrétním setupem",
      "formatPlan": {"clanek": "návod", "posty": 3, "newsletter": true, "video": "koncept"},
      "source": {"type": "scout", "ref": "runs/kava/2026-07-06", "quote": "23 příspěvků · 4 sítě · roste"},
      "productLink": "zrnková káva (productDNA)",
      "score": 4.4,
      "scoring": {"poptavka": {"v": 5, "doklad": "23 kusů/4 sítě, roste"}, "byznys": {"v": 5, "doklad": "přímo prodávaný produkt"}, "mezera": {"v": 4, "doklad": "v logu nic za 60 dní"}, "seo": {"v": 4, "doklad": "cluster espresso, pozice 14"}, "uhel": {"v": 4, "doklad": "úsudek"}},
      "ttl": "2026-07-27",
      "evergreen": false,
      "status": "idea",
      "offeredCount": 0,
      "addedDate": "2026-07-07"
    }
  ],
  "lastRun": "2026-07-07"
}
```

**Životnost a hygiena:**
- Nápad z trendu → `ttl` ~21 dní (po vypršení mrtvý — smaž nebo obnov jen s novým signálem). Evergreen (`evergreen: true`) TTL nemá.
- `status`: `idea` → `nabidnuto` → `planned` → `published` (pak řádek patří content-logu) · `odmitnuto`.
- **2× odmítnutý nápad přestaň nabízet** (`offeredCount` + status) — klientovo „ne" je taky data.
- Týdenní přeskórování backlogu dělá `content-performance` (boost témat podobných vítězům) — nesahej mu do toho, jen čti výsledek.

## Výstup

**Sólo běh** („dejte mi nápady, o čem psát") — klientovi vykáním, žádná skóre, žádné názvy skillů:

> Mám pro Vás 5 témat. U každého říkám proč:
> 1. **Espresso doma do 5 000 Kč** — na cenu setupu se ptá nejvíc lidí kolem tématu a přímo prodáváte zrnkovou. *(návod + 3 posty)*
> 2. …
> Odpovězte číslem a připravím draft. Nebo řekněte „naplánuj to" a rozložím je do kalendáře.

Interně vždy: aktualizovaný `ideas.json` + krátká poznámka, ze kterého stupně kaskády nápady vzešly.

**V orchestraci** (volá strategist v PLÁNu / autopilot fallback): vrať jen obodovaný seznam z `ideas.json` — prezentaci klientovi dělá strategist.

## Pravidla

- Nikdy nenavrhuj témata mimo obor a produkty klienta (DNA je kotva).
- Když existují reálná data klienta (výsledky, čísla, case), nápad na nich postavený má přednost.
- Nenavrhuj, co píšou všichni — hodnota je v úhlu, který má doklad.
- Max 5 nápadů v prezentaci (přehlcení zabíjí akci); zbytek žije v backlogu.
- Evergreen > reaktivní, pokud trend není masivní (a masivnost dokládá scout, ne pocit).
- Když klient mimochodem zmíní něco zajímavého („zrovna jsme vyřešili X"), okamžitě to zapiš jako nápad se `source.type: "klient"`.

## Failure handling

- Chybí scout brief → stupeň 2; chybí wiki/GSC → stupeň 3 s poctivým označením. **Nikdy neodpovídej „nemám data".**
- Poškozený/chybějící `ideas.json` → založ nový dle schématu, pokračuj (starý neopravuj slepě, přejmenuj na `.bak`).
- Konflikt s content-logem (téma < 60 dní) → nápad nevyhazuj, přegeneruj úhel, nebo označ `ttl` na po-lhůtě.

## Integrace (kontrakt = soubory, ne volání)

**Čte:** scout `brief.json` · wiki (otázky, content-gap) · `seo-keywords.json` · `content-log.md` · brand/product DNA · `evergreen.json` (zlatý fond — inspirace pro nové úhly).
**Píše:** `ideas.json` (jediný vlastník zápisu nových nápadů).
**Kdo ho čte:** `content-strategist` (PLÁN krok signálů, pondělní nabídka, AUTOPILOT fallback stupeň 3) · `content-performance` (týdenní přeskórování) · wiki content-gap tam přidává schválená témata.
