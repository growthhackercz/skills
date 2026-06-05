---
name: meta-ad-strategist
description: "Meta-native reklamní stratég pro Facebook/Instagram kampaně; použij ho pro direct Meta plánování, reporting-informed strategii a PAUSED write plán přes meta_ads_cli."
category: marketing
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---

# Meta Ad Strategist

Tento skill tvoří Meta-native reklamní strategii pro Facebook a Instagram.
Výstupem je plán a publisher hand-off pro `meta_ads_cli`; samotné copy, assety
a write krok řeší specializované sdílené skilly.

## Kdy použít

Použij ho, když zadání žádá Meta/Facebook/Instagram reklamu přes direct Meta
integraci, Meta CLI, native placementy nebo PAUSED vytvoření kampaně/ad setu/ad.
Pro CliqSales/GHL drafty, Google, LinkedIn nebo CRM-heavy multi-platform workflow
použij `cliqsales-ad-strategist`.

Bez `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` a `META_PAGE_ID` neslibuj direct
write ani deep Meta reporting. Pokud uživatel chce jen draft a GHL je dostupné,
přesměruj workflow na `cliqsales-ad-strategist`; jinak vrať přesný blocker.

## Workflow

1. Ověř dostatek kontextu: offer, cíl kampaně, landing URL, cílová země/jazyk,
   Meta placement intent, draft/write intent a požadovaný počet reklam.
2. Ověř direct Meta capability bez vypsání tokenů: `META_ACCESS_TOKEN`,
   `META_AD_ACCOUNT_ID`, `META_PAGE_ID`. Pokud chybí, vrať blocker nebo route na
   `cliqsales-ad-strategist` podle zadání.
3. Načti relevantní brand/product podklady. Pokud chybí nebo patří jiné značce,
   nastav `brandContextStatus: "missing_needs_confirmation"`; bez explicitního
   souhlasu nepokračuj do produkce assetů ani publisheru. Po souhlasu ulož
   `brand-input-note.md` a nastav `brandContextConfirmedWithoutDocs: true`.
4. Pokud jde o existující účet nebo optimalizační brief, použij
   `meta-ads-reporting` jako intelligence modul pro winners, bleeders, fatigue,
   budget efficiency nebo weekly brief. Reporting je read-only.
5. Pokud reporting nebo brief naznačuje slabý tracking signál, missing events,
   nízké EMQ, pixel/CAPI problém nebo double-counting, použij
   `meta-pixel-capi-audit` před škálovacím doporučením.
6. Urči objective, audience, placementy a formát. Video přidej jen při explicitní
   žádosti, Reels/Stories intentu, demo/UGC potřebě nebo když je pohyb jasně
   důležitý pro offer.
7. Nastav počty: default `copyVariantCount: 3`, `imageVariantCount: 2`,
   `publishableAdCount: 1`. Copy varianty nejsou vytvořené reklamy; vytvořená
   reklama znamená existující Meta `ad_id`.
8. Ulož `ad-strategy.md`, `ad-plan.json`, `ad-image-briefs.json` a případně
   `ad-video-briefs.json` do `/documents/brand/ads/{campaign-slug}/`.
9. Před copy a assety načti `ad-writer`, `ad-image-creator` a podle potřeby
   `ad-video-creator`. Pro produkční video nepoužívej 5s test default; nastav
   `qualityTier: "pro"` a platformově vhodnou délku. Smoke test smí mít 3-5 s
   a `qualityTier: "standard"` jen při explicitním technickém testu.
10. Před Meta write ověř, že `ad-image-manifest.json` existuje, vybraný asset má
   `status: "generated"` a publisher dostane image manifest, image ID a očekávaný
   poměr stran. U video creative vyžaduj také `ad-video-manifest.json` a
   thumbnail z image manifestu.
11. Pro direct write předej práci do `meta-ads-cli`. Bez potvrzení uživatele
   nevytvářej nic; po potvrzení vytvářej pouze `PAUSED` objekty přes helper
   `meta_paused_create.py`.

## Output Template

`ad-plan.json` musí obsahovat minimálně:

```json
{
  "campaignSlug": "campaign-slug",
  "offer": "Offer name",
  "language": "cs",
  "platforms": ["meta"],
  "objective": "lead_generation",
  "draftOnly": true,
  "copyVariantCount": 3,
  "imageVariantCount": 2,
  "publishableAdCount": 1,
  "publishingTargets": [
    {
      "platform": "meta",
      "backend": "meta_ads_cli",
      "safeWriteStatus": "PAUSED",
      "reason": "Meta direct integrace je dostupná a uživatel nechce GHL draft."
    }
  ],
  "brandContextStatus": "missing_confirmed",
  "brandContextConfirmedWithoutDocs": true,
  "formatMix": [
    {
      "platform": "meta",
      "format": "single_image",
      "reason": "První publishable ad má jasný hook a validní image hand-off."
    }
  ],
  "blockingQuestions": []
}
```

## Decision Criteria

| Podmínka | Prah | Akce |
|---|---:|---|
| Direct Meta vars chybí | chybí aspoň 1 z 3 | blocker nebo route na `cliqsales-ad-strategist` |
| Uživatel chce draft přes Meta direct | explicitní draft/write intent | plánuj `PAUSED`, ne GHL draft |
| Počet reklam není zadaný | žádný počet | `publishableAdCount: 1` |
| Uživatel chce 3 reklamy / A/B/C | explicitní počet | samostatné publishable `ads[]`, ne jen copy varianty |
| Video není výslovně potřeba | žádný Reels/Stories/video/demo intent | nezařazuj video automaticky |
| Existující účet má výkonová data | reporting/optimization brief | použij `meta-ads-reporting` před plánem |
| Tracking signal je nejistý | missing events / EMQ / dedup / pixel warning | použij `meta-pixel-capi-audit` |

## Anti-patterns

| Nedělej | Proč | Místo toho |
|---|---|---|
| Nevydávej copy varianty za created ads | Meta ad existuje až po `ad_id` | drž `publishableAdCount` odděleně |
| Neposílej do publisheru placeholder asset | write by vytvořil nekvalitní nebo vadnou reklamu | vyžaduj validní manifesty |
| Nesnižuj video tiše na obrázek | uživatel požadoval video asset | označ blocker nebo explicitní fallback |
| Nepoužívej ruční Graph API curl pro write | vyšší riziko token leaků a neúplných guardrailů | použij `meta-ads-cli` helper |
| Nepoužívej `social-cli` | není náš oficiální runtime | používej official `meta` CLI a naše helpery |

## Integration

**Uses:**
- `meta-ads-reporting` - read-only intelligence pro existující účty.
- `meta-pixel-capi-audit` - read-only audit tracking signálu před scale rozhodnutím.
- `ad-writer` - finální reklamní copy a JSON hand-off.
- `ad-image-creator` - bitmapové assety a `ad-image-manifest.json`.
- `ad-video-creator` - MP4 assety a `ad-video-manifest.json`, pokud je video součástí mixu.
- `meta-ads-cli` - finální read-only audit nebo potvrzený `PAUSED` write.

**Used by:**
- `ad-strategist` router pro Meta direct zadání.

## Quality Checklist

- [ ] `publishingTargets[].backend` je `meta_ads_cli`.
- [ ] Direct write je popsaný pouze jako `PAUSED`.
- [ ] Chybějící Meta integrace je blocker nebo vědomý route na GHL draft.
- [ ] `copyVariantCount`, `imageVariantCount` a `publishableAdCount` nejsou zaměněné.
- [ ] Image/video manifest requirement je explicitní před write krokem.
- [ ] Video decision obsahuje produkční vs smoke defaulty a `qualityTier`.
- [ ] Reporting doporučení jsou read-only a neslibují změnu kampaní.
- [ ] Slabý tracking signal je route na `meta-pixel-capi-audit`, ne domněnka.
