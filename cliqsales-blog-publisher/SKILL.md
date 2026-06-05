---
name: cliqsales-blog-publisher
description: "Publikujte hotový článek do CliqSales/GoHighLevel blogu přes Blog API jako draft, preview nebo po výslovném potvrzení publish. Umí použít asset manifest s veřejnými GHL media URL a vložit obrázky do rawHTML."
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-04-30"
---
# CliqSales Blog Publisher

Publikuje hotový obsah do CliqSales / GoHighLevel Blog API. Tento skill nepíše článek od nuly a negeneruje obrázky; pro tvorbu textu použij `article-writer`, pro obrázky `article-image-generator`, pro publishing tento skill.

## Workflow

1. **Ověř kontext** — Zkontroluj, že máš hotový článek jako HTML soubor, title, slug a informaci, jestli se tvoří draft nebo publish. Pokud chybí obsah nebo env konfigurace, zastav a řekni co chybí.
2. **Načti přístupy bezpečně** — Přístupy čti přes `scripts/ghl_publish.py --env-file {path}` nebo výchozí env lookup helperu. Neposílej tokeny v CLI argumentech.
3. **Otestuj GHL** — Před prvním publish během spusť `scripts/ghl_publish.py test`. Test ověřuje Blog API přes načtení blogů pro dané `locationId`; obecný location lookup není potřeba. Pokud test selže, nepokračuj.
4. **Připrav obsah** — Použij `article.html` a metadata. Výchozí chování odstraní metadata komentář i první `H1` z `rawHTML`, protože title se posílá samostatně.
5. **Volitelně vlož obrázky** — Pokud existuje `asset-manifest.json`, předej ho při `draft`, aby se do `rawHTML` vložily `img` bloky s GHL URL.
6. **Ověř slug** — Před vytvořením draftu ověř `urlSlug` přes `check-slug`. Primárně použij slug z `article-metadata.json`; pokud chybí, helper vytvoří URL slug z titulku včetně odstranění české diakritiky. Pokud je obsazený, navrhni alternativu.
7. **Načti blogy/autory/kategorie** — Blog je povinný (`blogId`). Autoři a kategorie jsou per-location endpointy.
8. **Vytvoř draft** — Výchozí akce je vždy `DRAFT`. Vrať `post_id`, `status`, `slug` a dostupné odkazy.
9. **Publikuj jen po potvrzení** — Přímý publish je povolený jen po explicitním potvrzení uživatele.
10. **Ověř výsledek** — Po draft/publish ověř, že API vrátilo `blogPost` objekt a že se zachoval title, slug a status.

## API pravidla (kritické)

- Base URL default: `https://services.leadconnectorhq.com`
- Headers: `Authorization`, `Version`, `Content-Type: application/json`
- `locationId` je u GET endpointů vždy query parametr, nikdy header.
- `authors` endpoint: `GET /blogs/authors?locationId=...&limit=...&offset=...` (bez `blogId`)
- `categories` endpoint: `GET /blogs/categories?locationId=...&limit=...&offset=...` (bez `blogId`)
- `posts list` endpoint: `GET /blogs/posts/all?locationId=...&blogId=...&limit=...&offset=...`; helper omezuje `limit` na API maximum 10
- `check slug` endpoint: `GET /blogs/posts/url-slug-exists?locationId=...&urlSlug=...`
- `create draft` endpoint: `POST /blogs/posts`

## Output Template

```markdown
# CliqSales draft připraven

- **Title:** {title}
- **Post ID:** {post_id}
- **Status:** {DRAFT|PUBLISHED|SCHEDULED}
- **Slug:** {urlSlug}
- **Blog ID:** {blog_id}
- **Public URL:** {link_or_empty}

## Poznámky
{co bylo automaticky zvoleno, co vyžaduje ruční kontrolu}
```

## Decision Criteria

| Condition | Threshold | Action |
|---|---:|---|
| Chybí `GHL_API_KEY` nebo `GHL_LOCATION_ID` | jakákoli chybějící hodnota | Zastav a požádej o doplnění nastavení integrace. |
| Uživatel neřekl publish | vždy | Vytvoř pouze `DRAFT`. |
| Uživatel chce publish | musí být výslovné potvrzení v aktuální konverzaci | Použij `publish --post-id ... --confirm-publish yes`. |
| Chybí `blogId` | vždy | Zastav a nejdřív načti blogy (`blogs`) nebo vyžádej `blogId`. |
| Slug je obsazený | `exists=true` | Navrhni alternativní slug a nepokračuj bez potvrzení. |
| API vrátí 401/403 | jakýkoli výskyt | Nepokračuj; vrať přesnou diagnostiku auth/scopes/location. |
| API vrátí 422 | jakýkoli výskyt | Uprav payload/query dle chybové hlášky, neinterpretuj to jako auth chybu. |

## Anti-patterns

| Don't | Why | Instead |
|---|---|---|
| Neposílej token v CLI argumentu. | Token unikne do historie/proc listu. | Použij env/`--env-file`. |
| Nevypisuj ani částečné tokeny do chatu. | Prefix/suffix tokenu je zbytečný fingerprint secretu. | Reportuj jen, že token je přítomný a jestli formát vypadá správně. |
| Nepublikuj rovnou `PUBLISHED` bez schválení. | Může odejít nezkontrolovaný obsah. | Nejprve draft. |
| Neposílej `metaTitle`/`metaDescription` do `POST /blogs/posts`. | Endpoint vrací 422 pro nepovolená pole. | Použij `title` a `description`. |
| Neposílej `blogId` u `/blogs/authors` a `/blogs/categories`. | Vrací 422. | Použij jen `locationId`, `limit`, `offset`. |
| Nevkládej lokální cesty obrázků do `rawHTML`. | Nejsou veřejně dostupné. | Použij asset manifest s `ghlUrl`. |
| Nepiš credentials do reportu. | Leak secretů. | Reportuj jen ID/status/slug/URL. |

## Integration

**Uses:**
- `article-writer` — vstupní HTML článku a metadata.
- `article-image-generator` — lokální image manifest.
- `cliqsales-blog-publisher assets` — asset manifest s GHL URL.
- `scripts/ghl_publish.py` — bezpečný GHL Blog API helper.

**Used by:**
- `content-strategist` — finální krok pro target `cliqsales`.

## Data Files

Výchozí env soubor, pokud není předán `--env-file`:

```text
/home/node/.openclaw/secrets/cliqsales.env
/home/node/.openclaw/secrets/ghl.env
/home/node/.openclaw/.env
```

Minimální konfigurace:

```env
GHL_API_KEY=pit-xxxxxxxx
GHL_LOCATION_ID=KJ9snzElAUhcNPzZ4b76
GHL_API_VERSION=2021-07-28
GHL_API_BASE_URL=https://services.leadconnectorhq.com
GHL_DEFAULT_STATUS=DRAFT
```

## Examples

Test připojení:

```bash
python3 /home/node/.openclaw/cs-skills/cliqsales-blog-publisher/scripts/ghl_publish.py test
```

Načtení blogů:

```bash
python3 /home/node/.openclaw/cs-skills/cliqsales-blog-publisher/scripts/ghl_publish.py blogs
```

Upload obrázků z image manifestu do GHL Media:

```bash
python3 /home/node/.openclaw/cs-skills/cliqsales-blog-publisher/scripts/ghl_publish.py assets \
  --image-manifest /documents/brand/content/blog/nazev-clanku/image-manifest.json \
  --output /documents/brand/content/blog/nazev-clanku/asset-manifest.json
```

Vytvoření draftu z hotového HTML:

```bash
python3 /home/node/.openclaw/cs-skills/cliqsales-blog-publisher/scripts/ghl_publish.py draft \
  --input /documents/brand/content/blog/nazev-clanku/article.html \
  --metadata /documents/brand/content/blog/nazev-clanku/article-metadata.json \
  --asset-manifest /documents/brand/content/blog/nazev-clanku/asset-manifest.json \
  --blog-id BLOG_ID \
  --status DRAFT
```

Publikace existujícího draftu po potvrzení:

```bash
python3 /home/node/.openclaw/cs-skills/cliqsales-blog-publisher/scripts/ghl_publish.py publish \
  --post-id POST_ID \
  --confirm-publish yes
```

## Quality Checklist

- [ ] Přístupy byly načteny z env/secret file.
- [ ] Výchozí status byl `DRAFT`, pokud nebyl explicitně potvrzen publish.
- [ ] Článek má title, slug, rawHTML a `blogId`.
- [ ] Slug byl ověřen před vytvořením draftu.
- [ ] Pokud se vkládají obrázky, manifest obsahuje veřejné `ghlUrl`.
- [ ] Výstup neobsahuje tokeny ani auth hlavičky.
- [ ] Uživatel dostal minimálně `post_id`, `status`, `urlSlug`.
