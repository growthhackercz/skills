---
name: content-strategist
description: "Strategist orchestrace pro social posty i blog články: rozhodne co se má vytvořit, kam to patří, připraví draft a publikuje jen na explicitní příkaz."
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-04-30"
---
# Content Strategist

Tento skill je orchestrátor. Sám nepíše finální texty, negeneruje obrázky ani nevolá publish API, pokud existuje specializovaný skill pro konkrétní krok.

## Co řeší

- rozpozná, jestli je zadání social post nebo blog článek
- vybere správnou produkční větev
- drží bezpečnostní pravidlo: default je vytvořený draft, publish jen na explicitní příkaz
- u social draft/publish flow hlídá, že post s `imagePrompt` má skutečný media asset, ne jen textový prompt

## Větve pipeline

### A) Social pipeline

1. `social-post-writer` - připraví social obsah (single nebo batch) bez publish API; pokud cílem je draft/schedule/publish a vznikne `imagePrompt`, vygeneruje skutečný obrázek přes `image_generate` a doplní `mediaFiles`.
2. `cliqsales-social-publisher` - nahraje `mediaFiles` do GHL Media a vytvoří social drafty v CliqSales/GHL Social Planneru; pokud dostane `imagePrompt` bez média, musí obraz nejdřív vygenerovat nebo položku označit jako failed.
3. publish/schedule až po explicitním potvrzení uživatele.

`social-post-writer` vždy vytváří ruční `social-posts.md` a API `social-posts.json`. Publisher dostává pouze `social-posts.json`.
Social média řeší přímo `cliqsales-social-publisher` přes `mediaFiles`, `mediaUrls` nebo upload. Prompt-only social draft není hotový draft, pokud je `mediaRequired: true`.

Pro social zadání typu „post na FB/IG/LinkedIn“ je cílový výstup CliqSales draft, pokud uživatel výslovně neřekne „jen text“, „jen podklad“, „bez draftu“, „nezakládat do CliqSales“ nebo podobně. Nečekej po `social-post-writer` na další potvrzení k draftu; rovnou pokračuj do `cliqsales-social-publisher`. Chybějící nebo uživatelem přeskočený brand znamená jen poznámku v reportu, ne `manual_review` režim.

### B) Blog pipeline

1. `article-writer` - vytvoří článek, metadata a image briefy.
2. `article-image-generator` - vygeneruje obrázky.
3. `wordpress-publisher assets` NEBO `cliqsales-blog-publisher assets` - uploaduje obrázky do cílového media systému a vytvoří target-specific `asset-manifest.json`.
4. `wordpress-publisher draft` NEBO `cliqsales-blog-publisher draft` - vytvoří blog draft v cílovém systému.
5. publish až po explicitním potvrzení uživatele.

## Routing pravidla

- Pokud uživatel chce „post na FB/IG/LI“, použij social pipeline.
- Pokud uživatel chce „článek/blog“, použij blog pipeline.
- Pokud není jasné, jestli jde o social nebo blog, nejdřív to ujasni.

## Draft/Publish pravidla (globální)

- Bez explicitního příkazu k publikaci se vytváří draft.
- „Publikuj“ musí být výslovné v aktuální konverzaci.
- Potvrzení má obsahovat konkrétní cíl (post/post_id/článek).
- Pokud potvrzení není jednoznačné, nepokračuj.

## Single vs Batch pravidla (social)

- Single: jeden social post = jeden draft request.
- Batch: více social postů najednou = sekvenční zpracování.
- Batch mód je `continue`: při chybě jedné položky pokračuj dál a vrať souhrnný report.

## Výstupní cesty

### Social

```text
/documents/brand/content/social/{campaign-slug}/
```

### Blog

```text
/documents/brand/content/blog/{slug}/
```

Nepřepisuj starší hotový běh bez výslovného pokynu.

## Doporučený chat průběh

Po přípravě social obsahu rovnou pokračuj do draft kroku. Neptej se „mám uložit draft“, pokud uživatel nepožádal jen o ruční/review podklad.

Po přípravě blog obsahu, pokud cílový systém není jasný:

```markdown
Obsah je připravený (blog) a čeká na draft krok.

Mám ho uložit jako draft do {target systému}?
```

Po draftu:

```markdown
Draft je připravený:
- Target: {cliqsales social|wordpress|cliqsales blog}
- ID: {post_id}
- Status: {draft}

Mám to publikovat / naplánovat?
```

## Failure handling

- Pokud selže tvorba obsahu, research nebo chybí brand/product kontext, nezahajuj publish větev.
- Social: pokud selže jedna položka v batchi, pokračuj v módu `continue` a reportuj položkový error.
- Blog: po `article-writer` zkontroluj `image-briefs.json`. Podpůrné obrázky mají být plánované po blocích 2-3 H2 sekcí, podporovat konkrétní text a nesmí být umístěné za poslední H2 nebo čistě po závěru/CTA. Článek s 5+ H2 sekcemi nesmí mít jen hero; vrať se do `article-writer` kroku a nepokračuj do generování obrázků.
- Blog: pokud selže hero image, zastav před publisher asset uploadem.
- Blog: pokud selže publisher asset/image krok, nevytvářej finální draft s rozbitými odkazy.
- WordPress: pokud REST neumožní zápis Yoast/RankMath meta polí, nepovažuj to za selhání draftu; reportuj omezení a ověř, že je nastavený aspoň standardní excerpt z `metaDescription`.
- WordPress: pokud draft po vytvoření obsahuje stejný nadpis v post title i v těle jako první `H1`, oprav flow přes `wordpress-publisher` bez `--keep-h1`; netvrď hotovo s duplicitním H1.
- CliqSales/GHL blog: pokud API vrátí validační chybu payloadu, uprav payload podle chybové zprávy; nehalucinuj příčinu.
- Pokud selže auth nebo API v publisheru, vrať přesnou chybu a nezkoušej publish.
- Pokud API vrátí 422, oprav payload podle chyby; neinterpretuj to jako token problém.
