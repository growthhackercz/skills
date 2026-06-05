# GoHighLevel Ad Manager Reference

Zdroj: HighLevel API 2.0 Ad Manager docs a Scopes page. Ad Manager endpointy používají `Version: 2023-02-21`.

## Auth

- Bearer token.
- Použij Access Token typu Sub-Account nebo Private Integration Token Sub-Account podle endpointu.
- Potřebné scopes:
  - `adPublishing.readOnly` pro integrace, ad accounts, reporting a lookup.
  - `adPublishing.write` pro upsert/draft, assets a publish endpoints.

## Draft/upsert endpoints

Tyto endpointy helper může použít:

```text
PUT  /ad-publishing/facebook/campaigns
PUT  /ad-publishing/facebook/adsets
PUT  /ad-publishing/facebook/ads-v2
PUT  /ad-publishing/linkedin/ads
POST /ad-publishing/google/assets
PUT  /ad-publishing/google/ads
```

Read-only probe endpointy:

```text
GET /ad-publishing/facebook/integration
GET /ad-publishing/facebook/ad-accounts
GET /ad-publishing/google/integration
GET /ad-publishing/google/ad-accounts
GET /ad-publishing/linkedin/integration
GET /ad-publishing/linkedin/ad-accounts
GET /ad-publishing/campaigns
```

## Blocked live endpoints

Nikdy je nevolej v draft workflow:

```text
POST /ad-publishing/facebook/campaigns/:campaignId/publish
POST /ad-publishing/google/ads/:adId/publish
POST /ad-publishing/linkedin/ads/:adId/publish
```

## Operation map

| Platform | Operation | Method | Endpoint |
| --- | --- | --- | --- |
| facebook/meta | campaign | PUT | `/ad-publishing/facebook/campaigns` |
| facebook/meta | adset | PUT | `/ad-publishing/facebook/adsets` |
| facebook/meta | ad | PUT | `/ad-publishing/facebook/ads-v2` |
| linkedin | campaign_group/full_campaign/ad | PUT | `/ad-publishing/linkedin/ads` |
| google | assets | POST | `/ad-publishing/google/assets` |
| google | campaign/full_campaign/ad | PUT | `/ad-publishing/google/ads` |

## Payload rules

- `draftOnly` musí být `true` nebo neuvedené s top-level `draftOnly: true`.
- `operation` nesmí být `publish`.
- `endpoint` nesmí obsahovat `/publish`.
- `payload.locationId` se může doplnit z `GHL_LOCATION_ID`, pokud chybí.
- Stavové hodnoty jako `ACTIVE`, `ENABLED`, `PUBLISHED`, `LIVE`, `RUNNING` jsou v draft workflow zakázané.
- `PAUSED`, `DISABLED`, `DRAFT`, `draft` jsou povolené draft-safe hodnoty, pokud je GHL schema vyžaduje.

## LinkedIn schema notes

`PUT /ad-publishing/linkedin/ads` vytváří campaign group včetně nested campaigns a ads. API může přijmout i příliš plochý payload a vrátit 200, ale výsledek pak nemusí být v Ad Manager dashboard listu. Proto helper považuje LinkedIn response bez root `budget`, bez `linkedInAdAccountId`, bez `adCampaigns[].ads[]`, nebo bez dohledatelnosti přes `GET /ad-publishing/campaigns` za chybu.

Minimální ověřený nested tvar:

```json
{
  "locationId": "CN13B3u9zZu6pipOwDZs",
  "linkedInAdAccountId": "508241906",
  "organizationId": "urn:li:organization:69669752",
  "budget": {
    "amount": 1,
    "budgetType": "DAILY",
    "scheduleStartDate": "2026-05-01T00:00:00.000Z",
    "scheduleEndDate": "2026-05-31T00:00:00.000Z"
  },
  "name": "Draft - campaign group",
  "publishingStatus": "DRAFT",
  "objectiveType": "LEAD_GENERATION",
  "adBudgetOptimization": "MAXIMUM_DELIVERY",
  "adCampaigns": [
    {
      "name": "Draft - campaign",
      "publishingStatus": "DRAFT",
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
```

LinkedIn enumy ověřené proti GHL:

- `mediaType`: `STANDARD_UPDATE`, `SINGLE_VIDEO`, `CAROUSEL`.
- `objectiveType`: `LEAD_GENERATION` je bezpečný default pro lead/trial/signup kampaně. Pro návštěvy webu použij `WEBSITE_VISIT`.
- `linkedInAdAccountId` a root `budget` jsou nutné pro to, aby se draft objevil v dashboard listu. `adAccountId` je jen helper alias a před odesláním se převede.
- Pro copy použij `introductoryText` a `destinationUrl`; `introText` a `landingUrl` jsou jen helper aliasy.
- Pro media použij `src`. `localPath` je pouze interní stopa k assetu a musí být před publish hand-offem nahrazená veřejnou nebo GHL media-manager URL.

## Test discipline

- Syntax test nestačí.
- `validate` ověří schema a guardraily bez sítě.
- `test` provede read-only probe reálných integrací/ad accounts.
- `draft --dry-run` ukáže přesné requesty bez zápisu.
- `draft --confirm-draft yes` provede reálné write requesty pouze na upsert/draft endpointy.
