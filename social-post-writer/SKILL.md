---
name: social-post-writer
description: "Tvorba social postů a plánů bez publikace: připraví ruční MD výstup i API JSON pro FB/IG/LinkedIn a předá je do cliqsales-social-publisher."
category: content
status: ready
version: "1.0"
publishedAt: "2026-04-30"
---
# Social Post Writer

Tento skill slouží pro tvorbu a plánování social obsahu. Nepublikuje do API.

Vždy připrav dvě varianty stejného obsahu:

- `social-posts.md` pro ruční čtení, review, copy/paste a schválení
- `social-posts.json` pro API hand-off do `cliqsales-social-publisher`

## Kdy použít

Použij tento skill, když uživatel chce:

- jeden social post
- sérii postů na týden nebo měsíc
- obsahový kalendář pro FB/IG/LinkedIn
- varianty textu pro různé platformy
- texty/captions/copy z tématu nebo briefu od `content-strategist`

Pokud uživatel chce post pro FB/IG/LinkedIn a výslovně neřekl „jen text“, „jen podklad“, „bez draftu“ nebo „nezakládat do CliqSales“, cílem je CliqSales Social Planner draft. Po vytvoření obsahu předej `social-posts.json` do `cliqsales-social-publisher`; nečekej na další potvrzení k draftu.

## Vstup

Preferovaný vstup z orchestrátora:

- `topic` - téma postu
- `platforms` - `facebook`, `instagram`, `linkedin`
- `tone` - tón komunikace
- `cta` - požadované call to action
- `keywords` - klíčová slova pro hashtagy
- `scheduledAt` nebo `scheduleLocal` - plánovaný čas
- `target` - ruční výstup, draft, schedule nebo publish intent

Přímý vstup od uživatele je také platný. Pokud platformy nejsou jasné, zeptej se; negeneruj automaticky všechny platformy, pokud by to změnilo zadání.

## Kontext

Před psaním načti, pokud existuje:

- `/documents/brand/brandDNA.md` - hlas, tón, hodnoty, cílové publikum, zakázaná slova
- `/documents/brand/products/{slug}/productDNA.md` - produktový kontext, pokud téma souvisí s produktem
- research brief nebo trending výstup, pokud je součástí zadání
- `/documents/brand/content/content-log.md` - ověř, že se téma neopakuje příliš brzy

Pokud brand soubory neexistují, pokračuj bez nich, ale v `social-plan.md` poznamenej, že výstup je bez brand kontextu.
Pokud uživatel řekne, že máš brand přeskočit, také pokračuj do draftu a pouze poznamenej, že draft je bez brand kontextu. Chybějící nebo přeskočený brand nikdy sám o sobě nepřepíná výstup na ruční review.

## Výstupní složka

Ulož výstup do:

```text
/documents/brand/content/social/{campaign-slug}/
```

Povinné soubory:

```text
social-plan.md
social-posts.md
social-posts.json
```

`social-posts.md` a `social-posts.json` musí obsahovat stejný finální obsah. MD je pro člověka, JSON je pro API.

## Režimy práce

### Single

Jeden post pro jednu nebo více platforem.

### Batch

Více postů najednou. Každý post je samostatná položka v `social-posts.json` a samostatná sekce v `social-posts.md`.

## Writing workflow

1. Identifikuj téma, platformy, tón, CTA, klíčová slova a publish intent.
2. Vytvoř pro každou cílovou platformu samostatnou verzi textu.
3. Přidej 2-3 hook varianty, ale vyber jeden finální `hook`.
4. Přidej specifické CTA a hashtagy podle platformy.
5. Přidej doporučený formát a image prompt/media note.
6. Pokud cílem je `draft`, `schedule` nebo `publish` a post obsahuje `imagePrompt`, hned vygeneruj skutečný rastrový obrázek přes nativní `image_generate`.
7. Ulož obrázky do `/documents/brand/content/social/{campaign-slug}/images/`.
8. Ověř každý obrázek přes `test -s {path}` a `file {path}`.
9. Ulož ruční MD výstup.
10. Ulož publishable JSON se stejným textem v poli `summary` a s `mediaRequired: true` + `mediaFiles`, pokud byly obrázky vygenerované.

Platformové limity a doporučení ber z `references/platform-params.md`. Neber statistiky jako dogma; použij je jako copywriting heuristiku.

## social-posts.md format

```markdown
# Social Posts: {campaign}

Timezone: Europe/Prague
Mode: single_or_batch
Default publish intent: draft

## post-001 - {platform}

Topic: {topic}
Schedule: {scheduleLocal}
Status: draft

Hook:
{finální hook}

Text:
{finální text postu}

CTA:
{cta}

Hashtags:
{#tag1 #tag2}

Recommended format:
{carousel|single_image|video|reels|text}

Link placement:
{none|in_post|first_comment|bio|dm}

Media note:
{stručný nápad na vizuál}

Image prompt:
{detailní prompt pro image generator}
```

## social-posts.json schema

```json
{
  "campaign": "nazev-kampane",
  "timezone": "Europe/Prague",
  "mode": "single_or_batch",
  "posts": [
    {
      "id": "post-001",
      "topic": "Téma",
      "platform": "facebook|instagram|linkedin",
      "user": "volitelný GHL user ID nebo email, pokud se nepoužije GHL_USER v publisheru",
      "accountLabel": "volitelné pojmenování účtu",
      "accountId": "volitelné přímé ID účtu",
      "accountIds": ["volitelné přímé ID účtu"],
      "hook": "Finální opening line",
      "hookVariants": ["Varianta 1", "Varianta 2", "Varianta 3"],
      "summary": "Finální text postu přesně pro API publish/draft",
      "cta": "Výzva k akci",
      "hashtags": ["#hashtag"],
      "recommendedFormat": "carousel|single_image|video|reels|text",
      "linkPlacement": "none|in_post|first_comment|bio|dm",
      "mediaNote": "Co má být za vizuál",
      "imagePrompt": "Prompt pro image generator",
      "imageSize": "1080x1080",
      "mediaRequired": true,
      "mediaFiles": ["/documents/brand/content/social/campaign/images/post-001.png"],
      "mediaUrls": ["volitelné veřejné URL po uploadu"],
      "scheduleLocal": "2026-05-01 09:00",
      "timezone": "Europe/Prague",
      "status": "draft",
      "publishIntent": "draft"
    }
  ]
}
```

Pravidla:

- `summary` je přesný text, který má publisher poslat do GHL Social Planneru.
- Pokud existuje `imagePrompt` a cílem je draft/schedule/publish, nevytvářej pouze prompt-only výstup. Nastav `mediaRequired: true`, zavolej `image_generate`, ulož soubor a vyplň `mediaFiles`.
- Prompt-only výstup je povolený jen pro čistě ruční/review podklad bez publisheru.
- `status` je vždy `draft`, pokud uživatel výslovně neřekl publish/schedule.
- `publishIntent` je výchozí `draft`.
- Nepoužívej `publishIntent: "manual_review"`, pokud uživatel výslovně nepožádal jen o ruční/review podklad bez CliqSales draftu.
- Pokud není známý čas publikace, pole `scheduleLocal` úplně vynech. Nikdy do něj nepiš `TBD`, `TODO`, `N/A` ani podobný placeholder.
- `timezone` default `Europe/Prague`, pokud není zadaná klientská zóna.
- `platform` stačí pro jednoduchý hand-off: `cliqsales-social-publisher` si účet namapuje automaticky, pokud v GHL existuje právě jeden účet pro danou platformu.
- `user` vyplňuj jen pokud je ověřené nebo dodané uživatelem; jinak publisher použije `GHL_USER`.
- `accountId`/`accountIds` vyplňuj jen když jsou ověřené z publisheru nebo je dodal uživatel. Pokud je účtů pro platformu víc, publisher si musí vyžádat `--account-map`.
- `imagePrompt` je zdrojový brief pro `image_generate`; pokud je nastavený publisher cíl, musí k němu existovat `mediaFiles` nebo explicitní poznámka proč generování selhalo.

## Platform writing rules

### LinkedIn

- silný profesionální point v prvních 210 znacích
- strukturovaný text s krátkými odstavci
- přesně 3 hashtagy
- CTA míří na komentář nebo zkušenost
- doporuč carousel/dokument, pokud téma snese strukturované slidy

### Instagram

- hook musí být viditelný v prvních 125 znacích
- vizuální, stručnější, energický text
- 3-5 hashtagů, nikdy víc než 5
- CTA může být save/share/DM
- doporuč carousel, reels nebo single image podle tématu

### Facebook

- konverzační tón, otázka nebo mini příběh
- 1-2 hashtagy max
- pokud je potřeba link, preferuj `first_comment`
- CTA míří na komentář, sdílení nebo reakci

## Copy rules

- Žádný generický AI slang: nepoužívej "v dnešním digitálním světě", "zůstaňte v obraze", "posuňte to na další úroveň".
- Každý post musí mít jednu jasnou myšlenku.
- Piš jazykem uživatele. Pokud zadání je česky, posty jsou česky.
- Respektuj brand voice z `brandDNA.md`.
- CTA musí být konkrétní, ne "klikněte sem".
- Hashtagy mají odpovídat platformě, ne být jedna sada pro všechno.

## Hand-off do publisheru

Po vytvoření souborů vrať:

```markdown
# Social obsah připraven

- Plan: `/documents/brand/content/social/{campaign-slug}/social-plan.md`
- Manual: `/documents/brand/content/social/{campaign-slug}/social-posts.md`
- API JSON: `/documents/brand/content/social/{campaign-slug}/social-posts.json`
- Mode: {single|batch}
- Default publish intent: draft

Další krok: `cliqsales-social-publisher` nad `social-posts.json`.
```

Pokud cílem byl CliqSales draft, tento hand-off není finální odpověď. Finální odpověď vrať až po běhu `cliqsales-social-publisher` a uveď vytvořené draft ID nebo přesnou chybu.

## Anti-patterns

- Nepovažuj „bez brandu“ za důvod skončit pouze u review výstupu.
- Neptej se na potvrzení draftu, pokud uživatel zadal social post a nezakázal CliqSales draft.
- Nepiš `scheduleLocal: "TBD"` ani jiné placeholder datum.
- Nepiš, že je obsah publikovaný, když nebyl volán publisher.
- Nepřidávej neověřené account IDs.
- Nepředstírej API validaci; writer API nevolá.
- Nevyráběj jen Markdown bez JSONu, pokud má obsah pokračovat do publisheru.
- Nezakládej Social Planner draft bez očekávaného obrázku, pokud JSON obsahuje `mediaRequired: true`.
