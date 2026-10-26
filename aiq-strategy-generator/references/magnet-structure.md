# Struktura lead magnetu — pevná kostra + dynamický analytický střed

Magnet (`/magnet/[contactId]`) je **plný personalizovaný dokument**, na který vede
odkaz z E0 e-mailu. NEPRODÁVÁ — ⅔ obsahu je poctivá analýza a hodnota, ⅓ je most
na personalizovanou prodejní stránku `/r/[contactId]`. Prodej je práce prodejní
stránky, ne magnetu.

## Aktuální struktura Builderu 1.0

> ⚡ **AIQ Engine (aktuální mag2 runtime — čti první):** magnet 2.0 má **PEVNOU KOSTRU**
> (fáze 1 skóre/oblasti → fáze 2 rizika/vyčíslení/„pod lupou" → fáze 4 Shrnutí „kde jste
> ↔ kam chcete" → fáze 5 řešení/předpis/urgence/CTA) a **jediný flexibilní kus je STŘED
> (fáze 3) = `magnet_middle`** (3 bloky, `text`/`cards`/`steps`). To je jádro AIQ Enginu —
> personalizační motor, co dělá každý magnet unikátní při stejném oblouku. **Nová pole:**
> `souhrn_ted`/`souhrn_chci`/`pointa` (fáze 4) + `nalehavost` (fáze 5). Kontrakt +
> doporučená skladba: `funnel-spec-schema.md` → `magnet_middle[]`.
> `magnet_structure` zůstává jen jako legacy metadata; Builder 1.0 podle něj
> neskládá pořadí stránky.

**5fázový psychologický oblouk (AIQ Engine):**
1. **Úvod** — jméno + skóre + oblasti/pásma (kdo jsem, kde stojím). Deterministické.
2. **Diagnóza** — 2.1 klíčová rizika · 2.2 vyčíslení v Kč (volitelné, doporučené) ·
   2.3 klíčové odpovědi „pod lupou" (technika Zrcadlo — jeho slova zpátky).
3. **STŘED (`magnet_middle`)** — flexibilní analytická část; AI navrhne typicky
   situaci → prostor/souvislosti → rizika. Tady žije unikátnost funnelu.
4. **Shrnutí** — „kde jste teď ↔ kam chcete" (z jeho cílů) + silná **pointa** (napětí+naděje).
5. **Co s tím** — mechanismus řešení → předpis (produkt navázaný na jeho problémy) →
   **urgence** (proč teď, z Product DNA) → jediné CTA. Bez hard-sellu, zvědavost → klik na /r/.

Pevné fáze strategie nepřeskládává. Pro každý nový funnel navrhne **3 kvalitní
analytické bloky** v `funnel-spec.magnet_middle` (výjimečně až 5). Každý blok
musí nést novou informaci; žádná vata, obecný checklist ani prodejní CTA. Bloky
jsou součástí strategie ve STOP 4, bez samostatného STOPu.

**Kontrakt bloku `magnet_middle[]`:**

```jsonc
{
  "block": 1,                    // volitelné pořadí; rozhoduje pořadí v poli
  "key": "rozbor",              // stabilní id sekce
  "subtitle": "Souvislosti",    // krátký eyebrow
  "title": "Co vaše odpovědi říkají o vašem zálohování",  // nadpis, který lead uvidí
  "render": "text",             // text | cards | steps
  "persona_field": "magnet_rozbor",   // musí být i v persona_fields[]
  "instruction": "2–3 odstavce: co říká KOMBINACE odpovědí…"
}
```

**Paleta render typů dynamického středu:**

| `render` | Typ | Popis | LLM? |
|---|---|---|---|
| `text` | LLM | Nadpis + odstavce (rozbor, co děláte dobře, rezervy…) | ano |
| `cards` | LLM | 2–3 analytické karty; `**Nadpis** popis`, oddělené prázdným řádkem | ano |
| `steps` | LLM | Očíslované analytické body, ne akční checklist ani CTA | ano |

⚠️ **`reviews` — placeholder flag.** Recenze ber z productDNA (reálné). Když je klient
nemá, vlož **ukázkové** a v `AIQ-strategie.md` to **výslovně označ** jako dočasné:
„Recenze jsme zatím doplnili jako ukázku — nahraďte je svými reálnými, nebo řekněte,
ať je smažeme." Nikdy nevydávej vymyšlenou recenzi za pravou. Jen křestní jméno +
kontext (město), žádné příjmení ani fotka.

Pole může znovu použít `magnet_rozbor` nebo `magnet_rizika`; nové pole, například
`magnet_prostor`, musí být přidané do `persona_fields[]`. Jedno pole nepoužívej
ve více blocích, jinak se stejný obsah zobrazí opakovaně.

**Doporučený střed:** rozbor (`text`) → prostor (`cards`, volitelné) → rizika
(`text`). CTA, předpis, shrnutí a urgence patří do pevné kostry.

## Naplnění per varianta

Strategy skill vybírá variantu v Kroku 2 — a pro ni definuje `main_result`,
`temperature_rules` a konkrétní podobu jednotlivých sekcí (odkazujeme je přes
`key`/`render`, ne přes číslo bloku). **Nic nesmí tvrdě záviset na
skóre** — skóre má jen část variant.

### Mechanismus uvědomění per varianta (řídí znění otázek)

Varianta neurčuje jen výstup, ale hlavně **jak si člověk sám uvědomí, že produkt
potřebuje** — a to se rodí **během vyplňování**, ne ve výsledku. Mechanismus zvol
dřív, než napíšeš první otázku. Detail a vzory: `copy-recipes.md` → „Otázky kvízu".

| Varianta | Vedoucí mechanismus | Otázky mají znít |
|---|---|---|
| `score` | selhání proti normě | „děláte / víte X?" — normy musí projít **testem pravosti** |
| `audit` | selhání proti normě + odkrytí slepého místa | totéž + options s poctivým „nevím / nenapadlo mě" |
| `plan` | mezera ve zralosti | „v jaké fázi jste?" — fáze, ne pass/fail |

**Blok kvalifikace (Velká čtyřka) je povinný u VŠECH variant** — každý magnet vede
k produktu. **Teplota se u nových funnelů bere z něj (`urgency_budget`), ne ze
skóre** — skóre a nákupní záměr jsou různé osy. **Skóre měří VELIKOST mezery /
potřeby jedním směrem: vyšší skóre = větší potřeba = teplejší zacházení. Kdo je bez
mezery, skóruje NÍZKO — a to je správně** (není to horký lead, i kdyby byl spokojený).
Nikdy neobracet na „jak dobře na tom jste", kde vysoké = spokojený = nekupuje.
Výjimka `score` viz níže.

### Teplota: `temperature_rules.source`

Kompletní tabulka tří zdrojů (`urgency_budget` / `critical_areas` / `score`) i důvod,
proč `number_urgency` kód **záměrně nemá**, jsou v `funnel-spec-schema.md` →
`temperature_rules`. Pro magnet platí: **default `urgency_budget`** z otázky nesoucí
signál rozpočtu; skóre teplotu neurčuje (měří spokojenost, ne nákupní záměr).

⚠️ **`urgency_budget` bez `question` spadne na práh skóre a zaloguje varování.**
Klíče `hot[]` / `warm[]` musí obsahovat **přesné hodnoty** z `options` dané otázky
(znak po znaku — překlep = lead spadne do cold).

### Která otázka nese co (mapování na spec)

Aby si builder ani strategie nemusely hádat:

| Spec pole | Bere z otázky | Typ |
|---|---|---|
| `temperature_rules.question` (urgency_budget) | **preferované řešení** (Velká čtyřka #4) | single |
| `mechanisms.by_pain` klíče | **co chcete zlepšit** — bolestivá otázka z bloku uvědomění/kvalifikace | multi |
| `cta_routes` klíče | **preferované řešení** (Velká čtyřka #4) — stejná jako teplota | single |
| `segments[].trigger` | **současná situace** (Velká čtyřka #1) | single |

`by_pain` a `temperature` tedy čtou **různé** otázky: bolest (co chce zlepšit) vs.
rozpočet (jaké řešení). Nepleť je.

### 🎯 Skóre (`variant: "score"`)

- `main_result`: `{ "type": "score", "label": "…", "unit": "/100" }` — skóre 0–100 + kategorie + gauge vizualizace
- ⚠️ **Orientace osy:** vyšší skóre = větší POTŘEBA (viz SKILL.md pravidlo skóre). Zakázaná jména os: jistota / pokrytí / připravenost / zralost / zdraví. `label` odpovídá na otázku z názvu magnetu. Test person: persona s největším problémem → nejvyšší pásmo.
- `temperature_rules`: **`source: "urgency_budget"`** (default) + `question` a `hot[]`/`warm[]` z otázky na preferované řešení. `source: "score"` jen tehdy, když skóre prokazatelně měří naléhavost, ne spokojenost (existující specy se `score` zůstávají funkční).
- `text` sekce (rozbor): rozbor per skórovací oblast (co která odpověď ubrala/přidala)
- `text` sekce (rizika): oblasti s nejnižším příspěvkem ke skóre

### 🩺 Audit (`variant: "audit"`)

- `main_result`: skóre NEBO počet kritických oblastí + barevné kategorie
  (`{ "type": "audit_areas" }`)
- ⚠️ **Orientace:** hlavní výstup = **počet kritických oblastí** (víc = hůř = tepleji); červená = kritická = horní konec. Zákaz „skóre zdraví" / známek A–F / „vše zelené" jako hlavního výsledku — grade obrací osu (zdravý = nekupuje).
- `temperature_rules`: **`source: "urgency_budget"`** (default) nebo `"critical_areas"` (hot = N+ kritických oblastí). `score` jen jako výjimka jako u varianty score.
- `text` sekce (rozbor): rozbor per auditovaná oblast (např. čtyři samostatně hodnocené oblasti)
- `text` sekce (rizika): kritické oblasti s dopady

### 📋 Plán / Harmonogram (`variant: "plan"`)

- `main_result`: `{ "type": "plan" }` — personalizovaný harmonogram (X kroků / Y dní)
- ⚠️ **Orientace:** fázi jen REPORTUJ („jste ve fázi 2 z 5"). Boduje-li se, boduj **mezeru do cílové fáze** (nižší fáze = víc bodů), ne dosaženou zralost. Skórovací otázky se NEPTAJÍ na sympatie k režimu/přístupu produktu (kontaminace osy záměrem).
- `temperature_rules`: `source: "urgency_budget"` + **`question` a `hot[]` / `warm[]`**
  — z otázky o preferovaném řešení, NE ze skóre. Bez těch klíčů to spadne na skóre.
- `text` sekce (rozbor): proč zrovna tyhle kroky v tomhle pořadí (z jeho odpovědí)
- `steps` sekce (akce): první týden plánu = kroky zdarma, bez produktu

## Routy (kontext pro strategii)

- `/vysledek?c=<id>` — okamžité shrnutí po kvízu: **plná deterministická
  diagnóza za 0 s** (main_result + segment + předpis-teaser z pravidel specu, bez
  LLM) + progresivní „analýza se dokresluje" (sync režim) + přímá výzva k akci na /r/.
- `/magnet/[contactId]` — plný magnet s pevnou kostrou a `magnet_middle`, SSR z
  GHL polí, print-friendly. Odkaz v E0 e-mailu.
- Žádná runtime PDF generace. Žádné per-kontakt obrázky — všechny obrázky jsou
  statické per funnel.

## Pravidla obsahu (závazná)

1. **⅔:⅓ poměr** — analytické sekce (`main_result`, `text`, `cards`, `steps`)
   nesou hodnotu samy o sobě; kdyby si lead nikdy nic nekoupil, analýza mu pořád pomohla.
2. **Benchmark bez podkladů = vynechat sekci**, ne vymýšlet čísla.
3. **Dynamický střed je analytický**, bez CTA a bez akčního checklistu.
4. **Citace vlastních slov leada** jen po sanitizaci (bez URL, délkový limit).
5. **Vykání, žádné zdravotní sliby, žádné anglicismy.**
