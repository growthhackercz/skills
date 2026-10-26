---
name: cliqsales-ads-publisher
description: "Publisher Ads Enginu pro CliqSales/GoHighLevel Ad Manager — zakládá DRAFT reklamy pro Meta, LinkedIn a Google Ads; strict draft-only, real endpointy, publish endpointy blokované. Default backend pro plán z ad-strategist (backend: cliqsales-ads-publisher). Pro přímý Meta write použij meta-ads-publisher."
category: integrations
status: ready
version: "1.1"
publishedAt: "2026-05-08"
---
# CliqSales Ads — GHL publisher

Tento skill bere hotový reklamní plán, copy a asset manifesty a vytváří drafty v CliqSales/GoHighLevel Ad Manageru. Nepíše copy a negeneruje assety. **Publisher Ads Enginu** (rodina: `ad-strategist` → makery → **cliqsales-ads-publisher**).

Používej ho, když plán z `ad-strategist` určil `publishingTargets[].backend: "cliqsales-ads-publisher"` (legacy alias `"ghl_ad_manager"` přijmi taky). Pokud je backend `"meta-ads-publisher"` (legacy `"meta_ads_cli"`), nepřeváděj ho na GHL draft a předej práci skillu `meta-ads-publisher`.

## Bezpečnostní pravidla
- **🔒 Cesty — struktura `/documents/ads/` je FIXNÍ.** 1. úroveň (`campaigns/ · scout/ · sets/ · video/ · reports/ · pixel-capi-audits/ · ad-score/ · evergreen-ads.json`) je daná — **NIKDY tam nezakládej novou složku** (žádná složka se jménem kampaně/značky přímo pod `ads/`, jinak se v tom reporty ztratí). Nové kampaně/běhy/sady = vždy **PODsložka**. Čti i piš **jen** do `/documents/ads/campaigns/{campaign-slug}/`.

- Default a jediný normální režim je `draft`.
- Nikdy nevolej endpoint obsahující `/publish`.
- Nikdy neposílej `status: ACTIVE`, `ENABLED`, `PUBLISHED`, `LIVE`, `RUNNING` ani podobné hodnoty.
- Live publish musí být samostatný krok po explicitním schválení konkrétního draft ID uživatelem; tento skill ho sám neprovádí.
- Tokeny nepatří do chatu ani do CLI argumentů.

## Vstup

Primární vstup:

```text
/documents/ads/campaigns/{campaign-slug}/ad-drafts.json
```

Pokud chybí, sestav ho z:

- `ad-plan.json`
- `ad-copy.json`
- `ad-image-manifest.json`
- `ad-video-manifest.json`

## Konfigurace

Minimálně:

```text
GHL_API_KEY
GHL_LOCATION_ID
```

Volitelně:

```text
GHL_API_BASE_URL    # default https://services.leadconnectorhq.com
GHL_API_VERSION     # default 2023-02-21
GHL_LINKEDIN_AD_ACCOUNT_ID # optional fallback; jinak helper vezme LinkedIn account z integration endpointu
```

Token musí mít pro draft zápis `adPublishing.write`; pro read-only testy `adPublishing.readOnly`.

## Reference

- `references/ghl-ad-manager.md` - endpointy, scopes a payload kontrakt.

## CLI helper

```bash
python3 scripts/ad_publish.py validate --input /documents/ads/campaigns/{campaign-slug}/ad-drafts.json
python3 scripts/ad_publish.py test --platform facebook --platform google --platform linkedin
python3 scripts/ad_publish.py draft --input /documents/ads/campaigns/{campaign-slug}/ad-drafts.json --mode continue --confirm-draft yes
python3 scripts/ad_publish.py draft --input /documents/ads/campaigns/{campaign-slug}/ad-drafts.json --dry-run
```

## Workflow

1. Ověř, že plán obsahuje `backend: "ghl_ad_manager"` nebo že uživatel explicitně chce CliqSales/GHL Ad Manager draft.
2. Spusť `validate`.
3. Pokud nejsou ověřené integrace/ad accounts, spusť `test` pro cílové platformy.
4. Zkontroluj, že všechny assety v manifestech existují a mají URL nebo jsou uploadnuté podle GHL požadavků.
5. Spusť `draft` s `--confirm-draft yes` pouze pokud uživatel zadal draft intent.
6. Ulož výstup do `ad-publish-result.json`.
7. Vrať draft IDs nebo přesné chyby podle položek. Batch režim je `continue`.

`ad-publish-result.json` nese `skillVersion: "1.1"`. Výsledek z nižší verze
nekopíruj jako důkaz aktuálního stavu; znovu validuj současný vstup a použij
aktuální helper.

## ad-drafts.json schema

```json
{
  "campaignSlug": "free-kurz-strategie-ctverecek",
  "draftOnly": true,
  "publishingTarget": "ghl_ad_manager",
  "locationId": "optional-location-id",
  "drafts": [
    {
      "id": "fb-campaign-001",
      "platform": "facebook",
      "operation": "campaign",
      "draftOnly": true,
      "payload": {
        "name": "Free kurz Strategie Ctverecek",
        "status": "draft"
      }
    },
    {
      "id": "google-asset-group-001",
      "platform": "google",
      "operation": "campaign",
      "payload": {}
    }
  ]
}
```

`payload` musí odpovídat aktuálnímu GHL Ad Manager API. Helper umí endpoint routing a guardraily, ale neuhádne skryté API schema; při 422 oprav payload podle odpovědi GHL.

### LinkedIn payload

LinkedIn nepoužívá root `ads[]` jako finální GHL schema. Helper umí jednoduché root `ads[]` převést, ale před odesláním vždy vytvoří nested strukturu:

```json
{
  "platform": "linkedin",
  "operation": "full_campaign",
  "payload": {
    "name": "Draft - LinkedIn campaign group",
    "linkedInAdAccountId": "508241906",
    "organizationId": "urn:li:organization:...",
    "budget": {
      "amount": 1,
      "budgetType": "DAILY",
      "scheduleStartDate": "2026-05-01T00:00:00.000Z",
      "scheduleEndDate": "2026-05-31T00:00:00.000Z"
    },
    "objectiveType": "LEAD_GENERATION",
    "adCampaigns": [
      {
        "name": "Draft - LinkedIn campaign",
        "mediaType": "STANDARD_UPDATE",
        "locale": {"language": "en", "country": "US"},
        "unitCost": {"amount": 1},
        "audience": {
          "geo_locations": [
            {"name": "Czechia", "urn": "urn:li:geo:104508036", "facetUrn": "urn:li:adTargetingFacet:locations", "selectionType": "include"}
          ],
          "targetAudience": {"include": [], "exclude": []}
        },
        "ads": [
          {
            "name": "Draft - ad",
            "introductoryText": "Primary text",
            "headline": "Headline",
            "description": "Description",
            "destinationUrl": "https://example.com",
            "media": [
              {"type": "image", "src": "https://example.com/ad.png", "name": "ad.png", "fileSizeBytes": 123456}
            ]
          }
        ]
      }
    ]
  }
}
```

LinkedIn `mediaType` použij `STANDARD_UPDATE`, `SINGLE_VIDEO` nebo `CAROUSEL`. Root `budget` a `linkedInAdAccountId` jsou nutné pro viditelnost v Ad Manager dashboardu; helper je umí doplnit z aliasů nebo z integration endpointu. `media[].src` musí být veřejná URL nebo GHL media-manager URL; samotné `localPath` není pro GHL Ad Manager použitelné. Pokud GHL vrátí draft bez `adCampaigns[].ads[]` nebo se draft neobjeví v `/ad-publishing/campaigns`, helper to označí jako chybu, protože takový objekt v Ad Manageru neuvidíš.

## Output template

```markdown
Draft advertising batch hotový:
- Total: {n}
- OK: {ok}
- Failed: {failed}
- Result: `/documents/ads/campaigns/{campaign-slug}/ad-publish-result.json`

Detail:
{per-item id, platform, operation, endpoint, response id/error}
```

## Failure handling

- 401/403: auth/scope/integration problém; helper po první takové chybě ukončí batch a neposílá další write requesty.
- 422: payload/schema problém; oprav podle response.
- Chybějící asset: zastav danou položku, nepokračuj s placeholderem.
- Nejasný ad account nebo platform integration: vrať blocker a požaduj konkrétní account/integration.
