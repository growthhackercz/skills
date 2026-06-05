---
name: cliqsales-social-publisher
description: "Publikace social postů do CliqSales/GoHighLevel Social Planner API. Default je draft, publish/schedule jen po explicitním příkazu. Podporuje single i batch režim s continue chováním."
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-04-30"
---
# CliqSales Social Publisher

Tento skill publikuje nebo plánuje social posty do GHL Social Planner API. Nepíše obsah od nuly.

## Vstup

Preferovaný vstup je výstup ze `social-post-writer`:

```text
/documents/brand/content/social/{campaign-slug}/social-posts.json
```

## Bezpečnostní pravidla

- Default je vždy draft.
- Publish/schedule pouze po explicitním příkazu v aktuální konverzaci.
- Nikdy nevypisuj token do chatu ani do diagnostiky.
- Pokud některá položka v batchi selže, mód je `continue`: pokračuj další položkou a vrať souhrn.
- Přístupy čti přes environment proměnné nebo přes helper `scripts/social_publish.py --env-file {path}`. Nepiš do skillu konkrétní lokální cestu k souboru s přístupy.
- Neposílej tokeny v CLI argumentech.

## Konfigurace

Minimální konfigurace přes `{ENV_VAR}`:

```text
GHL_API_KEY
GHL_LOCATION_ID
GHL_USER
```

Volitelné:

```text
GHL_API_VERSION     # default 2021-07-28
GHL_API_BASE_URL    # default https://services.leadconnectorhq.com
```

`GHL_USER` je jedno pole: GHL user ID nebo email. Email varianta vyžaduje token se scope pro `/users/`.

Pro každého klienta/sub-account musí být vlastní hodnoty `{GHL_API_KEY}`, `{GHL_LOCATION_ID}` a `{GHL_USER}`. Nepřenášej user ID mezi klienty.

Výchozí env lookup je řešen helperem stejně jako u ostatních publisherů. Pokud běh používá explicitní env soubor, předávej ho jen jako proměnný `{path}`:

```bash
python3 scripts/social_publish.py --env-file {path} test
```

## Ověřené endpointy

```text
GET  /social-media-posting/{LOCATION_ID}/accounts
POST /social-media-posting/{LOCATION_ID}/posts/list
POST /social-media-posting/{LOCATION_ID}/posts
PUT  /social-media-posting/{LOCATION_ID}/posts/{POST_ID}
GET  /social-media-posting/{LOCATION_ID}/categories
GET  /social-media-posting/{LOCATION_ID}/tags
POST /medias/upload-file
```

Diagnostický endpoint, nepoužívej v běžném flow:

```text
GET  /users/?locationId={LOCATION_ID}
```

## Workflow

1. Spusť `test` (accounts + posts/list; `/users/` se netestuje, protože token nemusí mít user scope).
2. Najdi account IDs přes `accounts`, nebo nech `batch-draft` automaticky namapovat `platform` na účet, pokud existuje právě jeden účet pro danou platformu.
3. Připrav payloady ze `social-posts.json`.
4. Pokud má položka `imagePrompt` a nemá `mediaFiles` ani `mediaUrls`, nejdřív vygeneruj skutečný rastrový obrázek přes nativní `image_generate`, ulož ho do `images/`, ověř `test -s` + `file` a doplň `mediaFiles`.
5. Pokud je `mediaRequired: true`, nevytvářej draft bez `mediaFiles` nebo `mediaUrls`.
6. Vytvoř draft(y) přes `batch-draft` nebo `draft`. Helper automaticky nahraje `mediaFiles` do GHL Media a vloží veřejné URL do payloadu jako `media`.
7. Pokud média doplňuješ až po vytvoření postu, použij `attach-media` a následně ověř `posts-list`, že `media[]` není prázdné.
8. Publish/schedule proveď jen při explicitním příkazu.

## CLI helper

Skript:

```text
scripts/social_publish.py
```

Hlavní příkazy:

```bash
python3 scripts/social_publish.py test
python3 scripts/social_publish.py accounts
python3 scripts/social_publish.py users
python3 scripts/social_publish.py draft --summary "..." --account-id ACC --schedule-local "2026-05-01 09:00"
python3 scripts/social_publish.py draft --summary "..." --account-id ACC --user owner@example.com
python3 scripts/social_publish.py draft --summary "..." --account-id ACC --media-file /documents/brand/content/social/campaign/images/post.png --media-required yes
python3 scripts/social_publish.py batch-draft --input /documents/brand/content/social/campaign/social-posts.json --mode continue
python3 scripts/social_publish.py batch-draft --input /documents/brand/content/social/campaign/social-posts.json --mode continue --account-map facebook:ACC_FB,instagram:ACC_IG
python3 scripts/social_publish.py upload-media --file /documents/brand/content/social/campaign/images/post.png
python3 scripts/social_publish.py attach-media --post-id POST_ID --file /documents/brand/content/social/campaign/images/post.png
python3 scripts/social_publish.py publish --post-id POST_ID --confirm-publish yes
```

## Batch contract (`continue`)

`batch-draft` zpracuje `posts[]` položky sekvenčně:

- úspěšné položky uloží jako `ok`
- neúspěšné položky uloží jako `failed`
- pokračuje dál i po chybě
- vrátí souhrn `total/ok/failed` + detail každé položky
- `userId` je pro GHL create post povinný, ale uživatel ho zadává jedním polem: item-level `user`, pak `--user`, pak `GHL_USER`
- pokud hodnota obsahuje `@`, helper ji bere jako email a zkusí ji převést přes `/users/`; pokud neobsahuje `@`, bere ji jako GHL user ID
- `/users/` endpoint neřeš v normálním flow, pokud token nemá user scope; nastav `GHL_USER` přímo na GHL user ID při klientském onboardingu
- `mediaFiles` helper před vytvořením draftu nahraje přes `/medias/upload-file` a použije vrácené veřejné URL v `media`
- `mediaRequired: true` bez `mediaFiles`/`mediaUrls` je chyba položky; v `continue` režimu položka selže a batch pokračuje dál
- `accountId`/`accountIds` mají přednost; jinak se použije `--account-id`, `--account-map`, nebo auto-map podle `platform`/`accountLabel`
- pokud auto-map najde více účtů pro stejnou platformu nebo label, položka bez explicitního mapování selže a batch pokračuje dál
- auto-map ignoruje účty označené jako `isExpired` nebo `deleted`

## Output Template

```markdown
# Social draft batch hotový

- Total: {n}
- OK: {ok_count}
- Failed: {failed_count}
- Mode: continue

## Detail
{per-item result s id, postId, status, error}
```

## Anti-patterns

- Nepublikuj bez explicitního příkazu.
- Nepředstírej úspěch při částečném selhání batch.
- Nepřepínej token při 422; oprav payload.
