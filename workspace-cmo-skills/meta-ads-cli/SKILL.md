---
name: meta-ads-cli
description: Finální Meta Ads CLI publisher/audit krok. Použij jen pro read-only audit nebo PAUSED write z hotového ad-strategist plánu; nepoužívej jako orchestrátor celé kampaně.
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---

# Meta Ads CLI

Používej oficiální `meta ads` CLI dostupné jako `meta`.

## Kdy použít

- Ověření, že je Meta Ads integrace nastavená a vidí reklamní účet.
- Výpis kampaní, ad setů, reklam, kreativ a insights.
- Přímý Meta/Facebook/Instagram publishing krok z `ad-strategist`, pokud `ad-plan.json` obsahuje `publishingTargets[].backend: "meta_ads_cli"`.
- Bezpečné vytvoření kampaně/ad setu/creative/ad jako `PAUSED` po schválení uživatelem a po dodání hotového plánu, copy a assetů.
- Diagnostika chyb v Meta Marketing API bez přepisování vlastních curl skriptů.

Nepoužívej tento skill jako orchestrátor celé kampaně. Pokud úkol zní
„připrav/založ Meta reklamu/kampaň“ a neexistuje hotový `ad-plan.json`,
`ad-copy` a image/video manifest, nejdřív použij `ad-strategist` router a potom
`meta-ad-strategist`. Tento skill je jen read-only audit nebo finální Meta write
krok.

## Konfigurace

Vyžadované proměnné:

```text
META_ACCESS_TOKEN
META_AD_ACCOUNT_ID
META_PAGE_ID
```

`META_AD_ACCOUNT_ID` má mít tvar `act_...`. Pokud je uložené jen číslo, v příkazech ho normalizuj na `act_<id>`.

Wrapper `/usr/local/bin/meta` mapuje `META_ACCESS_TOKEN` na `ACCESS_TOKEN` a `META_AD_ACCOUNT_ID` na `AD_ACCOUNT_ID`, protože CLI očekává tyto názvy.
Pokud proměnné nejsou v process env, wrapper načte pouze `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` a `META_PAGE_ID` z `${OPENCLAW_HOME}/.env`.

## Bezpečnost

- Nikdy nevypisuj access token ani celé requesty s tokenem.
- `meta ads page list` může ve výstupu obsahovat `access_token`; nikdy neposílej raw výstup do chatu ani reportu.
- Bez explicitního potvrzení uživatele dělej jen read-only operace.
- Vytváření kampaní, ad setů, kreativ a reklam je povolené pouze jako `PAUSED`.
- Nikdy nespouštěj/nezapínej kampaně, neměň budgety a nemaž objekty bez samostatného explicitního potvrzení v chatu.
- Před každou write operací ukaž stručný review: účet, page, objective, budget, targeting, landing URL, copy a výsledný status.
- Pro write operace nepoužívej ručně skládaný Graph API `curl`, pokud stačí helper `scripts/meta_paused_create.py`.
- Nikdy nepoužívej `set -euo pipefail` v holém `exec` příkazu. OpenClaw exec může běžet přes `/bin/sh`; pokud potřebuješ `pipefail`, spusť skript přes `bash -lc 'set -euo pipefail; ...'`, nebo použij Python helper.
- Nepoužívej shell pipeline pro kritické write kroky. Kritický Meta write má být jeden `python3 .../meta_paused_create.py ...` příkaz s argumenty, ne inline heredoc/curl skript.

## Základní ověření

Nejdřív ověř CLI a účet:

```bash
meta --help
meta -o json ads adaccount list
```

Při ověření stránky výstup sanitizuj:

```bash
meta -o json ads page list | jq 'map(del(.access_token))'
```

Pokud si nejsi jistý syntaxí konkrétního příkazu, spusť nejdřív příslušný help:

```bash
meta ads --help
meta ads campaign --help
meta ads adset --help
meta ads creative --help
meta ads ad --help
meta ads insights --help
```

Preferuj JSON výstup:

```bash
meta -o json ads campaign list
```

## Doporučený postup

1. Ověř `meta --help` a dostupnost účtu.
2. Pro read-only audit načti kampaně/adsety/reklamy/insights přes `-o json`.
3. Shrň zjištění uživateli lidsky a přilož relevantní ID.
4. Pokud jde o kompletní kampaň, ověř, že vstup přišel z `ad-strategist` a obsahuje plán, copy a skutečné assety.
5. Pro vytvoření kampaně nejdřív připrav review a počkej na potvrzení.
6. Vše vytvářej jako `PAUSED` přes `scripts/meta_paused_create.py`.
7. Po write operaci ulož report do `/documents/{project-slug}/meta-ads/`.

## PAUSED create helper

Helper řeší aktuální povinné Meta API parametry a ukládá důkazy:

- image gate: ověří bitmapu, `ad-image-manifest.json`, `status: generated` a skutečný poměr stran před prvním Meta write requestem
- video gate: pokud je předán `--video-file`, ověří `ad-video-manifest.json`, `status: generated`, nahraje MP4 přes `/advideos`, počká na zpracování a vytvoří `video_data` creative; `--image-file` je v tom případě thumbnail image a je povinný
- campaign: `status=PAUSED`, `is_adset_budget_sharing_enabled=false`,
  `special_ad_categories=[]`
- ad set: `status=PAUSED`, `dsa_beneficiary`, `dsa_payor`,
  `targeting_automation.advantage_audience=0`
- ad: `status=PAUSED`
- evidence files: `00-created-ids.json`, `00-image-validation.json`, volitelně `00-video-validation.json`, a verifikační soubory až po `11-verification-summary.json`

Příklad:

```bash
python3 ~/.openclaw/workspaces/cmo/skills/meta-ads-cli/scripts/meta_paused_create.py \
  --out-dir /documents/project/meta-ads/meta \
  --image-file /documents/project/creative/images/ad.jpg \
  --image-manifest /documents/project/ad-image-manifest.json \
  --image-id img-01 \
  --expected-aspect-ratio 1:1 \
  --campaign-name "TEST PAUSED Brand Campaign" \
  --adset-name "TEST PAUSED Brand Ad Set CZ 30-55" \
  --creative-name "TEST PAUSED Brand Creative" \
  --ad-name "TEST PAUSED Brand Ad" \
  --landing-url "https://example.com/" \
  --primary-text "Primary ad text" \
  --headline "Headline" \
  --description "Short description" \
  --daily-budget 10000 \
  --age-min 30 \
  --age-max 55 \
  --countries CZ \
  --dsa-beneficiary "Brand Name" \
  --dsa-payor "Brand Name"
```

Video příklad:

```bash
python3 ~/.openclaw/workspaces/cmo/skills/meta-ads-cli/scripts/meta_paused_create.py \
  --out-dir /documents/project/meta-ads/meta-video \
  --image-file /documents/project/images/video-thumbnail.png \
  --image-manifest /documents/project/ad-image-manifest.json \
  --image-id img-video-thumb \
  --expected-aspect-ratio 9:16 \
  --video-file /documents/project/videos/vid-001.mp4 \
  --video-manifest /documents/project/ad-video-manifest.json \
  --video-id vid-001 \
  --campaign-name "TEST PAUSED Brand Video Campaign" \
  --adset-name "TEST PAUSED Brand Video Ad Set CZ 30-55" \
  --creative-name "TEST PAUSED Brand Video Creative" \
  --ad-name "TEST PAUSED Brand Video Ad" \
  --landing-url "https://example.com/" \
  --primary-text "Primary ad text" \
  --headline "Headline" \
  --daily-budget 10000 \
  --age-min 30 \
  --age-max 55 \
  --countries CZ \
  --dsa-beneficiary "Brand Name" \
  --dsa-payor "Brand Name"
```

Helper čte `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` a `META_PAGE_ID` z process
env nebo `${OPENCLAW_HOME}/.env`, tokeny nevypisuje a odmítne jiný status než
`PAUSED`.

## Vstup z reklamního orchestrátoru

Pokud tě volá `meta-ad-strategist` nebo starší task přes `ad-strategist` router,
načti primárně:

```text
/documents/brand/ads/{campaign-slug}/ad-plan.json
/documents/brand/ads/{campaign-slug}/ad-copy.json
/documents/brand/ads/{campaign-slug}/ad-image-manifest.json
/documents/brand/ads/{campaign-slug}/ad-video-manifest.json
```

Před write akcí ověř, že:

- `ad-plan.json` obsahuje pro Meta `backend: "meta_ads_cli"`,
- existuje landing URL a campaign objective,
- rozpočet a targeting jsou buď zadané, nebo se na ně doptáš před vytvořením ad setu/ad,
- assety nejsou placeholdery a mají použitelnou lokální cestu nebo veřejnou URL,
- `ad-image-manifest.json` existuje, vybraný obrázek má `status: "generated"` a helper dostane `--image-manifest`, `--image-id` a `--expected-aspect-ratio`,
- pokud je formát video, `ad-video-manifest.json` existuje, vybrané video má `status: "generated"` a helper dostane `--video-file`, `--video-manifest` a `--video-id`; thumbnail pořád jde přes image gate,
- uživatel v aktuálním vlákně potvrdil vytvoření `PAUSED` objektů.
- write krok použije `scripts/meta_paused_create.py`; ruční Graph API payload je fallback jen pokud helper neumí konkrétní objekt a musíš uložit přesný důvod.

Pokud rozpočet chybí, můžeš připravit plán a review, ale nevytvářej ad set ani ad. Campaign shell jako `PAUSED` vytvářej jen pokud to uživatel výslovně potvrdil jako technický smoke/test.

## Více reklam

Defaultně vytvoř jeden finální Meta ad. Pokud `ad-plan.json` obsahuje `publishableAdCount > 1`, musí mít každý publikovatelný záznam vlastní copy, asset a review řádek.

Současný helper vytváří jeden PAUSED ad set a jeden PAUSED ad na jeden běh. Pro bezpečný A/B test tedy:

- buď spusť helper opakovaně s jasně odlišenými názvy a samostatným evidence adresářem pro každý ad, pokud uživatel schválil tento zjednodušený režim,
- nebo zastav write krok a vrať blocker `batch_shared_adset_not_supported`, pokud je požadovaný jeden sdílený ad set s více ads.

Nikdy nevydávej copy varianty za vytvořené reklamy. Vytvořená reklama znamená existující Meta `ad_id` ve výstupu helperu.

## Výstupy

Pro reporty používej:

```text
/documents/{project-slug}/meta-ads/
```

Minimální report po akci:

```markdown
# Meta Ads Report

## Account
- Ad account:
- Page:

## Actions
- ...

## Created / Checked IDs
- ...

## Risks / Next Step
- ...
```
