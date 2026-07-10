---
name: ad-writer
description: "Píše platformově specifické reklamní texty pro Meta, LinkedIn a Google Ads včetně RSA headlines, social primary textu, CTA, carousel karet a publisher JSON hand-offu."
category: content
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---
# Ad Writer

Tento skill píše finální reklamní copy a strukturovaný JSON pro další kroky. Nepublikuje a negeneruje assety.

## Kdy použít

Použij při tvorbě textu pro placené reklamy, ad variants, carousel card copy, Meta/LinkedIn primary text, Google responsive search ads, Performance Max text assets nebo publisher hand-off.

## Vstup

Preferovaný vstup je `ad-plan.json` od `meta-ad-strategist` nebo
`cliqsales-ad-strategist`; starší tasky mohou přijít přes `ad-strategist`
router:

```text
/documents/brand/ads/{campaign-slug}/ad-plan.json
```

Načti také dostupné brand/product podklady. Pokud chybí brand/product podklady a `ad-plan.json` nemá `brandContextConfirmedWithoutDocs: true`, nevymýšlej brand voice a vrať se na `ad-strategist` pro potvrzení `missing_needs_confirmation`. Pokud potvrzení existuje, piš copy jen z dodaného zadání, landing page a dostupných veřejných informací a označ to v `ad-copy.md`. Pokud chybí landing URL pro draft, copy můžeš připravit, ale publisher readiness označ jako `blocked_missing_landing_url`.

## Reference

- `references/platform-copy-rules.md` - limity, struktury a quality rules.

## Workflow

1. Ověř jazyk kampaně podle zadání; české zadání znamená české reklamy.
2. Vytvoř message map: awareness level, pain, promise, proof, CTA, objections.
3. Pro každou platformu napiš samostatné varianty, ne jednu generickou verzi.
4. Pro carousel napiš copy pro každou kartu: headline, body, visual cue, card CTA/link.
5. Pro Google Search vytvoř responsive search ad: 8-15 headlines, 2-5 descriptions, path1/path2 a keyword themes.
6. Ulož `ad-copy.md` pro člověka a `ad-copy.json` pro další skilly.
7. Pokud je potřeba obrázek/video, doplň `imageBriefs` a `videoBriefs` v JSONu pro hand-off.

## Výstupní složka

```text
/documents/brand/ads/{campaign-slug}/
```

Povinné soubory:

```text
ad-copy.md
ad-copy.json
```

## ad-copy.json schema

```json
{
  "campaignSlug": "free-kurz-strategie-ctverecek",
  "language": "cs",
  "draftOnly": true,
  "platforms": ["meta"],
  "ads": [
    {
      "id": "meta-carousel-001",
      "platform": "meta",
      "format": "carousel",
      "objective": "lead_generation",
      "primaryText": "Finální text reklamy.",
      "headline": "Finální headline",
      "description": "Volitelný popis",
      "cta": "Sign Up",
      "landingUrl": "https://example.com",
      "cards": [
        {
          "id": "card-01",
          "headline": "Krok 1",
          "body": "Co má karta říct.",
          "visualCue": "Co má být na obrázku.",
          "cta": "Zjistit více",
          "landingUrl": "https://example.com"
        }
      ],
      "imageBriefIds": ["img-card-01"],
      "videoBriefIds": ["vid-001"],
      "publisherReady": true
    }
  ],
  "imageBriefs": [],
  "videoBriefs": []
}
```

## Quality rules

- Každá reklama má jednu hlavní myšlenku.
- Nepoužívej generický AI jazyk typu „v dnešním digitálním světě“, „posuňte podnikání na další úroveň“, „revoluční řešení“.
- Claims musí být konkrétní a obhajitelné. U regulovaných oborů nepoužívej záruky výsledků, zdravotní/finanční sliby ani zavádějící urgency.
- CTA musí říkat, co se stane po kliknutí.
- Platformové limity ber z reference a nepřekroč je, pokud nejde o interní working copy.

## Output do chatu

```markdown
Copy je připravená:
- Manual: `/documents/brand/ads/{campaign-slug}/ad-copy.md`
- JSON: `/documents/brand/ads/{campaign-slug}/ad-copy.json`
- Platformy: {platforms}
- Další krok: `ad-image-creator`, `ad-video-creator` nebo `ad-publisher`
```

Pokud jde o orchestrátor workflow, nevracej toto jako finální výsledek; je to mezikrok.
