---
name: cliqsales-ad-strategist
description: "CliqSales/GHL reklamní stratég pro Ad Manager drafty; použij ho pro GHL, Google, LinkedIn, CRM/follow-up aware workflow a multi-platform drafty."
category: marketing
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---

# CliqSales Ad Strategist

Tento skill tvoří strategii pro reklamní drafty v CliqSales/GoHighLevel Ad
Manageru. Je silný tam, kde reklama navazuje na CRM, lead routing, pipeline,
follow-up a multi-platform drafty.

## Kdy použít

Použij ho, když uživatel chce CliqSales, GoHighLevel, GHL, Ad Manager draft,
Google Ads, LinkedIn Ads, CRM-aware plán, lead routing nebo multi-platform
draft. Pro direct Meta PAUSED write použij `meta-ad-strategist`.

GHL-only režim nemá garantovaná deep Meta data jako fatigue, winners, bleeders,
pixel/CAPI diagnostiku nebo raw Meta insights, pokud je GHL API neposkytuje.
Takové dotazy směruj na `meta-ads-reporting`, pokud existuje direct Meta
integrace.

## Workflow

1. Ověř dostatek kontextu: offer, cílové platformy, landing URL, lead/CRM cíl,
   follow-up potřeby, budget rámec a draft intent.
2. Ověř GHL capability bez vypsání tokenů: `GHL_API_KEY`, `GHL_LOCATION_ID` a
   podle potřeby `GHL_USER`. Pokud chybí, ulož strategii a vrať přesný
   integration blocker.
3. Načti brand/product podklady. Pokud chybí nebo nesedí se značkou, nastav
   `brandContextStatus: "missing_needs_confirmation"`; bez explicitního souhlasu
   nepokračuj do produkce assetů ani draft publisheru. Po souhlasu ulož
   `brand-input-note.md` a nastav `brandContextConfirmedWithoutDocs: true`.
4. Rozděl platformy podle GHL možností: Facebook/Meta přes GHL draft, Google
   přes GHL draft, LinkedIn přes GHL draft. Pokud jedna kampaň obsahuje direct
   Meta a GHL platformy, vrať split plan a Meta část předej `meta-ad-strategist`.
5. Navrhni CRM/follow-up aware plán: lead stage, pipeline, routing, owner,
   follow-up sekvence, UTM a měření, které jsou potřebné pro draft readiness.
6. Nastav `draftOnly: true` a `publishingTargets[].backend: "ghl_ad_manager"`.
   Nikdy neplánuj live publish v tomto skillu.
7. Ulož `ad-strategy.md`, `ad-plan.json`, `ad-image-briefs.json`,
   `ad-video-briefs.json` podle formátu a `ad-drafts.json` do
   `/documents/brand/ads/{campaign-slug}/`.
8. Před copy a assety načti `ad-writer`, `ad-image-creator` a podle potřeby
   `ad-video-creator`.
9. Před publisherem ověř, že assety mají veřejnou URL nebo jsou uploadnuté do
   GHL media manageru. Samotný `localPath` není pro GHL Ad Manager draft
   použitelný.
10. Předej hotové `ad-drafts.json` do `ad-publisher`, který provede validaci a
   draft-only create přes GHL endpointy.

## Output Template

`ad-plan.json` musí obsahovat minimálně:

```json
{
  "campaignSlug": "campaign-slug",
  "offer": "Offer name",
  "language": "cs",
  "platforms": ["facebook", "google", "linkedin"],
  "objective": "lead_generation",
  "draftOnly": true,
  "publishingTargets": [
    {
      "platform": "facebook",
      "backend": "ghl_ad_manager",
      "mode": "draft",
      "reason": "Uživatel chce CliqSales/GHL Ad Manager draft."
    }
  ],
  "crmFollowUp": {
    "pipelineStage": "new_lead",
    "owner": "marketing",
    "followUpRequired": true
  },
  "blockingQuestions": []
}
```

`ad-drafts.json` musí používat `draftOnly: true` a položky pro `ad-publisher`.

## Decision Criteria

| Podmínka | Prah | Akce |
|---|---:|---|
| Chybí `GHL_API_KEY` nebo `GHL_LOCATION_ID` | chybí aspoň 1 | blocker `missing_ghl_integration` |
| Platforma je Google nebo LinkedIn | jakýkoli direct request | GHL draft přes `ghl_ad_manager` |
| Uživatel chce CRM/follow-up | explicitní nebo implied lead routing | zahrnout CRM/follow-up plán |
| Asset má jen `localPath` | žádná public/media URL | blocker před `ad-publisher` |
| Uživatel chce live publish | jakýkoli live intent | vytvořit draft a žádat separátní schválení |
| Uživatel chce deep Meta fatigue/winners | GHL-only data | route na `meta-ads-reporting` nebo označit limit |

## Anti-patterns

| Nedělej | Proč | Místo toho |
|---|---|---|
| Nevytvářej live kampaně | tento workflow je draft-only | vždy `draftOnly: true` |
| Nepřeváděj direct Meta PAUSED write na GHL bez důvodu | jiný backend a jiné důkazy | split plan nebo `meta-ad-strategist` |
| Neposílej do GHL jen lokální asset path | draft nemusí být viditelný v Ad Manageru | použij public URL nebo GHL media URL |
| Neslibuj Meta pixel/fatigue data z GHL | GHL API je nemusí poskytovat | použij direct Meta reporting |
| Nekombinuj Google/LinkedIn schema do Meta helperu | publisher boundary by se rozbil | drž `ghl_ad_manager` pro tyto platformy |

## Integration

**Uses:**
- `ad-writer` - copy a publisher JSON podklady.
- `ad-image-creator` - bitmapové assety a manifest.
- `ad-video-creator` - video assety, pokud je formát vyžaduje.
- `ad-publisher` - validace a vytvoření CliqSales/GHL draftů.
- `meta-ad-strategist` - jen pro split, pokud část kampaně má jít direct Meta.

**Used by:**
- `ad-strategist` router pro GHL/CliqSales, Google, LinkedIn a CRM-aware zadání.

## Quality Checklist

- [ ] `publishingTargets[].backend` je `ghl_ad_manager`.
- [ ] Všechny publisher položky jsou draft-only.
- [ ] Google a LinkedIn nejdou přes direct Meta helper.
- [ ] CRM/follow-up dopady jsou zachycené, pokud jsou v zadání relevantní.
- [ ] Assety mají public URL nebo GHL media URL před publisherem.
- [ ] GHL-only reporting limity jsou jasně uvedené.
