# Brand Board Prompt Template

Tato šablona se používá pro generování brand board obrázku přes `image_generate`. Nahraď placeholdery skutečnými hodnotami z brandDNA.md.

## Mapování: Brand DNA sekce → Placeholdery

Brand DNA report má 7 sekcí. Tady je odkud každý placeholder čerpá:

| Placeholder | Brand DNA sekce | Konkrétní pole | Příklad |
|---|---|---|---|
| `{{BRAND_NAME}}` | 1. Esence značky | Název | "Cliqsales" |
| `{{CATEGORY}}` | 1. Esence značky | Kategorie | "AI automatizace pro e-shopy" |
| `{{SLOGAN}}` | 1. Esence značky | Slogan | "Automatizace, která dává smysl" |
| `{{USP}}` | 1. Esence značky | Jedinečná výhoda (USP) | "Jediný nástroj co propojí AI s vaším e-shopem za 10 minut" |
| `{{EMOTIONAL_TONE}}` | 1. Esence značky | Emoční tón (3–5 pocitů) | "sebevědomá, inovativní, přístupná" |
| `{{TRANSFORMATION}}` | 1. Esence značky | Transformace PŘED → PO | "Z chaosu objednávek → klidný přehled" |
| `{{TARGET_AUDIENCE}}` | 2. Ideální zákazník | Kdo je, co hledá | "majitelé e-shopů 30–50 let, kteří chtějí škálovat" |
| `{{BRAND_VOICE}}` | 5. Hlas značky | Tón, rytmus, postoj | "přímý, energický, bez korporátního jazyka" |
| `{{PRIMARY_COLOR}}` | 6. Vizuální identita | Primární barva + HEX | "#1A3C5E deep navy" |
| `{{SECONDARY_COLOR}}` | 6. Vizuální identita | Sekundární barva + HEX | "#F4A261 warm amber" |
| `{{ACCENT_COLORS}}` | 6. Vizuální identita | Další barvy palety (volitelné) | "#E76F51 coral, #2A9D8F teal" |
| `{{HEADING_FONT}}` | 6. Vizuální identita | Typografie — heading font | "Montserrat Bold" |
| `{{BODY_FONT}}` | 6. Vizuální identita | Typografie — body font | "Inter Regular" |
| `{{VISUAL_STYLE}}` | 6. Vizuální identita | Vizuální styl — celkový směr | "minimalistický, technologický, čistý" |
| `{{PHOTO_STYLE}}` | 6. Vizuální identita | Styl fotografií — nálada, světlo | "přirozené světlo, teplé tóny, autentické momenty" |
| `{{TEXTURES}}` | 6. Vizuální identita | Textury a vzory | "jemné geometrické vzory, gradient overlays" |
| `{{ICON_STYLE}}` | 6. Vizuální identita | Ikonografie — styl ikon | "line icons, zaoblené rohy, 2px tloušťka" |
| `{{BRAND_SUMMARY}}` | 7. Shrnutí Brand DNA | Celkový pocit (odstavec) | "Značka co působí jako..." |

## Prompt šablona

Níže je kompletní prompt. Před použitím nahraď všechny `{{PLACEHOLDER}}` hodnoty. Pokud některý údaj v Brand DNA chybí, odstraň příslušný řádek nebo sekci.

---

```
Vygeneruj prémiovou vertikální moodboard koláž v poměru stran 2:3, která představí kompletní systém vizuální identity značky {{BRAND_NAME}} ({{CATEGORY}}) v rozvržení ve stylu Behance.

ZNAČKA:
Název: {{BRAND_NAME}}
Kategorie: {{CATEGORY}}
Slogan: {{SLOGAN}}
USP: {{USP}}
Emoční tón: {{EMOTIONAL_TONE}}
Transformace: {{TRANSFORMATION}}
Cílová skupina: {{TARGET_AUDIENCE}}
Hlas značky: {{BRAND_VOICE}}
Celkový pocit: {{BRAND_SUMMARY}}

VIZUÁLNÍ SYSTÉM (ze sekce Vizuální identita Brand DNA):
Vizuální styl: {{VISUAL_STYLE}}
Styl fotografií: {{PHOTO_STYLE}}
Textury a vzory: {{TEXTURES}}
Ikonografie: {{ICON_STYLE}}

PRVKY MOODBOARDU:
- Logo značky s velkým množstvím negativního prostoru (použij přesně přiložené logo, žádné vlastní logo/wordmark)
- Název značky "{{BRAND_NAME}}" + slogan "{{SLOGAN}}" nahoře
- 2 styly písma zobrazené pomocí realistických brandových frází v češtině — nadpisový font {{HEADING_FONT}}, textový font {{BODY_FONT}}. Fráze musí odpovídat esenci a tónu značky. Nepoužívej klišé jako „odemkni", „uvolni", „obejmi".
- Barevné vzorky s HEX kódy: {{PRIMARY_COLOR}}, {{SECONDARY_COLOR}}, {{ACCENT_COLORS}}
- 2–3 textury nebo abstraktní pozadí: {{TEXTURES}}
- 3–4 brandové fotografie ve stylu: {{PHOTO_STYLE}} — relevantní pro obor {{CATEGORY}}. Vyprávěcí, autentické, ne stockové.
- 3–5 grafických akcentů — ikony ve stylu {{ICON_STYLE}}, geometrické tvary a motivy odpovídající emočnímu tónu: {{EMOTIONAL_TONE}}
- 2–3 realistické mockupy (web, sociální sítě, vizitky) s aplikovanou vizuální identitou ve stylu {{VISUAL_STYLE}}

STRUKTURA LAYOUTU:
Horní třetina: název značky / logo, ukázky písma, barevné vzorky, textury, fotografie — plynulé, editoriální, vrstvené jako rozvržení v magazínu.
Spodní dvě třetiny: realistické mockupy aplikující vizuální systém značky na světlém / tmavém / barevném pozadí. Značka v praxi — hlavní pointa celého boardu.

DESIGNOVÉ PRINCIPY:
- Vertikální canvas přes celou plochu bez okrajů
- Vrstvené a pohlcující rozvržení, ne krabicové ani příliš rigidně gridové
- Moderní hloubka (jemné gradienty, překryvy) — bez zastaralých efektů (zkosení, těžké stíny)
- Bez popisek, titulků nebo názvů sekcí — čistý vizuál
- Čistá spodní hrana, nic nesmí být uříznuté
- Prémiová, soudržná kvalita připravená pro klienta
- Poměr stran 2:3

REFERENČNÍ OBRÁZKY:
Pokud jsou přiloženy referenční obrázky z /documents/brand/images/, použij je jako vizuální inspiraci — zachyť jejich náladu, barevnost a styl ve výsledném brand boardu. Nemusíš je kopírovat doslovně, ale výsledek by měl rezonovat se stejnou vizuální energií.

Veškerý text na moodboardu v češtině.
```

---

## Iterační doplňky

Pokud uživatel chce úpravy, přidej na konec promptu dodatečnou instrukci. Příklady:

| Feedback uživatele | Doplněk do promptu |
|---|---|
| "Tmavší paleta" | `Celkový vizuál by měl být tmavší — použij tmavé pozadí a světlé akcenty. Dark mode estetika.` |
| "Více minimalistické" | `Redukuj počet prvků na minimum. Více negativního prostoru. Méně textur, méně fotografií. Čistý, vzdušný design.` |
| "Jiný styl fotek" | `Fotografie by měly být [styl dle feedbacku] — např. lifestyle, flat lay, dokumentární, abstraktní.` |
| "Luxusnější pocit" | `Přidej zlaté nebo měděné akcenty. Elegantní serifová typografie. Mramorové nebo hedvábné textury. Prémiový, high-end dojem.` |
| "Hravější, mladší" | `Jasnější barvy, zaoblené tvary, neformální typografie. Energický a přístupný vizuální jazyk pro mladší publikum.` |
| "Jiné fonty" | `Změň typografii — nadpisový font: [nový font], textový font: [nový font]. Zachovej zbytek vizuálního systému.` |
| "Změň ikony" | `Ikony by měly být ve stylu [nový styl] místo {{ICON_STYLE}}.` |
