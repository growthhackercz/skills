---
name: wordpress-publisher
description: "Publikujte hotový článek do WordPressu přes REST API jako draft, preview nebo po výslovném potvrzení publish. Umí použít asset manifest s WordPress media IDs/URLs pro vložení obrázků do Gutenberg obsahu."
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---
# WordPress Publisher

Publikuje hotový obsah do WordPressu. Tento skill nepíše článek od nuly a negeneruje obrázky; pro tvorbu textu použij `article-writer`, pro obrázky `article-image-generator`, pro publishing tento skill.

## Workflow

1. **Ověř kontext** — Zkontroluj, že máš hotový článek jako HTML/Markdown soubor, název, slug a instrukci, jestli má vzniknout draft, pending review nebo publish. Pokud chybí obsah nebo přístupové proměnné, zastav a řekni co chybí.
2. **Načti přístupy bezpečně** — Preferuj Control Center profil: `scripts/wp_publish.py --profile default ...`. Pokud uživatel pojmenuje jiný WP profil, použij jeho slug. Legacy env/env-file používej jen jako fallback. Nikdy nespouštěj `source`, `. env`, `set -a` ani shell expansion nad WP env souborem; application password může obsahovat mezery a shell ho rozbije nebo vyzradí.
3. **Ověř cílový web** — Před vytvořením draftu zkontroluj, že vybraný WP profil/doména odpovídá brandu, doméně nebo webu v zadání. Pokud zadání naznačuje jiný web než profil `default`, nepokračuj potichu; požádej o správný WP profil nebo výslovné potvrzení použití dostupného profilu.
4. **Otestuj WordPress** — Před prvním publikováním spusť test připojení přes `scripts/wp_publish.py --profile default test` nebo konkrétní pojmenovaný profil. Pokud test selže, nepokračuj.
5. **Připrav obsah** — Pokud vstup není Gutenberg HTML, převeď ho přes `scripts/wp_publish.py convert`. Výchozí chování helperu odstraní první `H1` z těla článku, protože WordPress post title se renderuje samostatně. Nepřidávej CSS, inline styly ani tracking skripty.
6. **Volitelně vlož obrázky** — Pokud existuje `asset-manifest.json`, použij ho při `convert` nebo `draft`, aby se vložily WordPress image bloky. Asset manifest musí obsahovat WP media IDs/URLs; lokální image manifest nejdřív zpracuj příkazem `assets`.
7. **Předej SEO metadata** — Pokud existuje `article-metadata.json`, předej ho přes `--metadata` nebo nech helper načíst sibling soubor. Helper použije `title`, `slug`, `metaDescription`, `primaryKeyword` a `secondaryKeywords` pro WP title/slug/excerpt/tagy. Yoast/RankMath meta zapisuj jen pokud je daný web vystavuje ve WordPress REST schema; jinak reportuj, že plugin SEO pole nejsou přes REST zapisovatelná a že byl nastaven standardní excerpt.
8. **Načti kategorie** — Pokud uživatel neurčil kategorii, načti dostupné kategorie a zvol nejbližší. Novou kategorii vytvářej jen pokud ji uživatel výslovně schválil.
9. **Vytvoř draft** — Výchozí akce je vždy `draft`. Vytvoř draft, vrať `post_id`, `preview_url`, `edit_url`, stav, kategorie, tagy a `seo` stav z helperu.
10. **Publikuj jen po potvrzení** — `publish` nebo změna existujícího postu je povolená pouze po explicitním potvrzení uživatele. Potvrzení musí být v aktuální konverzaci a musí pojmenovat post nebo `post_id`.
11. **Ověř výsledek** — Po draft/publish ověř, že WordPress vrátil URL a stav. Přes REST zkontroluj, že obsah neobsahuje duplicitní první `H1` a že obrázky odkazují na WP media IDs/URLs.

## Output Template

```markdown
# WordPress draft připraven

- **Title:** {title}
- **Post ID:** {post_id}
- **Status:** {draft|pending|publish}
- **Preview:** {preview_url}
- **Edit:** {edit_url}
- **Live URL:** {live_url_or_empty}
- **Categories:** {categories}
- **Tags:** {tags}
- **SEO:** {excerpt_set, plugin_meta_written nebo plugin_meta_note}

## Poznámky
{co bylo automaticky zvoleno, co vyžaduje ruční kontrolu}
```

## Decision Criteria

| Condition | Threshold | Action |
|---|---:|---|
| Chybí WordPress profil nebo jeho application password | jakákoli chybějící hodnota | Zastav a požádej o doplnění WordPress profilu v Integracích. |
| WP profil/doména neodpovídá brandu nebo webu v zadání | jakýkoli mismatch nebo nejistota | Nevytvářej draft; požádej o správný profil nebo výslovné potvrzení cílového webu. |
| Uživatel neřekl publish | vždy | Vytvoř pouze `draft`, i když env říká jiný status. |
| Uživatel chce publish | musí být výslovné potvrzení v aktuální konverzaci | Použij `--status publish` nebo `publish --post-id`. |
| Článek nemá title | 0 znaků | Nepublikuj; vyžádej title nebo ho odvoď z H1 a ukaž ho před vytvořením draftu. |
| Tělo postu obsahuje stejný H1 jako WP title | jakýkoli výskyt | Odstraň první H1 z contentu; WordPress title ho nahradí. `--keep-h1` použij jen na výslovný požadavek. |
| Asset manifest obsahuje lokální cesty bez WP URL/ID | jakýkoli výskyt | Nejdřív spusť upload assetů; nevkládej nepublikovatelné lokální cesty do WordPressu. |
| WordPress vrátí 401/403 | jakýkoli výskyt | Nepokračuj; přístupy nebo role jsou špatně. |
| SEO plugin meta nejsou ve WP REST schema | žádné writable Yoast/RankMath keys | Nastav title, slug, excerpt a tagy; reportuj omezení místo tvrzení, že Yoast SEO je vyplněné. |

## Anti-patterns

| Don't | Why | Instead |
|---|---|---|
| Nepředávej application password v CLI argumentu. | Ukáže se v shell historii a proc listu. | Použij `--profile`; helper vyřeší secret přes Control Center credential store. |
| Nesourcuj WP env soubor (`source`, `. env`, `set -a`). | WP application password běžně obsahuje mezery; shell ho rozbije a může ho vypsat. | Spouštěj helper s `--profile`, případně s `--env-file`; helper parsuje vstupy bezpečně. |
| Nepoužívej `default` profil, když task zmiňuje jiný web/brand. | Draft může vzniknout na špatném klientském webu. | Nejprve ověř profil/doménu nebo požádej o potvrzení. |
| Nepublikuj rovnou `publish` bez schválení. | Může jít o nezkontrolovaný obsah na klientském webu. | Nejprve draft + preview URL. |
| Nevytvářej nové kategorie automaticky. | Rozbije taxonomii webu. | Použij existující kategorii nebo požádej o schválení. |
| Nepiš credentials do reportu. | Leak secretů. | Reportuj jen URL, post ID, status a redaktované diagnostiky. |
| Nepoužívej tento skill pro psaní článku. | Publishing skill neřeší kreativní kvalitu. | Nejdřív `article-writer`, pak `wordpress-publisher`. |
| Nevkládej `/documents/...` image paths do článku. | WordPress je neumí veřejně servírovat. | Použij `asset-manifest.json` s `wpMediaId` a `wpUrl`. |
| Netvrď „SEO hotovo“, když je nastavený jen excerpt. | Yoast/RankMath pole nemusí být zapisovatelná přes REST. | Reportuj přesný `seo` stav vrácený helperem. |

## Integration

**Uses:**
- `article-writer` — review-ready HTML, metadata a image briefy.
- `article-image-generator` — lokální image manifest.
- `wordpress-publisher assets` — asset manifest s WP media IDs/URLs.
- `scripts/wp_publish.py` — bezpečný WordPress REST API helper bez credentials v CLI argumentech.
- WordPress REST API `/wp-json/wp/v2/*` — posts, categories, tags a users/me.

**Used by:**
- `article-writer` — předává hotové HTML k vytvoření draftu.
- CMO workflow — finální publikace článků a blogových výstupů.

## Credential Lookup

Preferovaná cesta je Control Center WordPress profil:

```bash
python3 /home/node/.openclaw/cs-skills/wordpress-publisher/scripts/wp_publish.py --profile default test
```

Helper čte public profil z `/home/node/.openclaw/control-center-credentials.json`
a application password z `/home/node/.openclaw/control-center-secrets.json`.
Secret nikdy neposílej v argumentu ani ho nevypisuj.

Pokud je nastaveno více WordPress webů, každý web má vlastní profil v
Integracích. Použij `--profile default`, pokud task neurčuje konkrétní web;
pokud uživatel nebo task pojmenuje jiný profil, použij jeho slug, například
`--profile magazin`.

## Legacy Env Fallback

Výchozí env soubor, pokud není předán `--env-file`:

```text
/home/node/.openclaw/secrets/wordpress.env
/home/node/.openclaw/secrets/wp.env
/home/node/.openclaw/.env
```

Absence `secrets/wordpress.env` sama o sobě neznamená chybějící integraci.
Pokud nemáš konkrétní env soubor ověřený, nepředávej `--env-file` a použij
`--profile default` nebo výchozí lookup helperu.

Minimální konfigurace:

```env
WP_SITE_URL=https://example.com
WP_USERNAME=wp-user
WP_APPLICATION_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

## Examples

Test připojení:

```bash
python3 /home/node/.openclaw/cs-skills/wordpress-publisher/scripts/wp_publish.py --profile default test
```

Upload obrázků z image manifestu do WordPress Media Library:

```bash
python3 /home/node/.openclaw/cs-skills/wordpress-publisher/scripts/wp_publish.py --profile default assets \
  --image-manifest /documents/brand/content/blog/nazev-clanku/image-manifest.json \
  --output /documents/brand/content/blog/nazev-clanku/asset-manifest.json
```

Převod HTML do Gutenbergu a vložení obrázků z asset manifestu:

```bash
python3 /home/node/.openclaw/cs-skills/wordpress-publisher/scripts/wp_publish.py convert \
  --input /documents/brand/content/blog/nazev-clanku/article.html \
  --asset-manifest /documents/brand/content/blog/nazev-clanku/asset-manifest.json \
  --output /documents/brand/content/blog/nazev-clanku/article-gutenberg.html
```

Vytvoření draftu z hotového HTML:

```bash
python3 /home/node/.openclaw/cs-skills/wordpress-publisher/scripts/wp_publish.py --profile default draft \
  --input /documents/brand/content/blog/clanek.html \
  --title "Název článku" \
  --slug "nazev-clanku" \
  --category "Blog" \
  --tag "seo"
```

Vytvoření draftu rovnou s asset manifestem:

```bash
python3 /home/node/.openclaw/cs-skills/wordpress-publisher/scripts/wp_publish.py --profile default draft \
  --input /documents/brand/content/blog/nazev-clanku/article.html \
  --metadata /documents/brand/content/blog/nazev-clanku/article-metadata.json \
  --asset-manifest /documents/brand/content/blog/nazev-clanku/asset-manifest.json \
  --title "Název článku" \
  --slug "nazev-clanku"
```

Publikace existujícího draftu po potvrzení:

```bash
python3 /home/node/.openclaw/cs-skills/wordpress-publisher/scripts/wp_publish.py --profile default publish \
  --post-id 123 \
  --confirm-publish yes
```

## Quality Checklist

- [ ] Přístupy byly načteny přes Control Center profil nebo legacy env fallback, ne z chatu ani CLI argumentů.
- [ ] Vybraný WP profil/doména odpovídá cílovému brandu/webu, nebo je v reportu uvedené explicitní potvrzení operátora.
- [ ] WP env soubor nebyl nikdy sourcován shellem; helper běžel s `--profile`, `--env-file` nebo výchozím lookupem.
- [ ] Výchozí stav je `draft`, pokud uživatel výslovně nepotvrdil publish.
- [ ] Článek má title, slug a obsah.
- [ ] Tělo WordPress postu neobsahuje duplicitní první `H1`; post title je WP title.
- [ ] `article-metadata.json` bylo použito pro title/slug/excerpt/tags nebo bylo jasně řečeno, proč chybí.
- [ ] SEO stav z helperu je reportovaný přesně; Yoast/RankMath se netvrdí jako nastavený, pokud REST schema nedovolilo zápis.
- [ ] Pokud se vkládají obrázky, asset manifest obsahuje `wpMediaId` a `wpUrl`, ne jen lokální cesty.
- [ ] Kategorie a tagy byly zvoleny z existujících hodnot nebo výslovně schváleny.
- [ ] Výstup neobsahuje `WP_APPLICATION_PASSWORD`, Authorization header ani jiné secrety.
- [ ] Uživatel dostal `post_id`, `preview_url` a `edit_url`.
