---
name: ad-strategist
description: "Router a compatibility shim pro placené reklamy; použij ho, když starší zadání říká ad-strategist nebo není jasné, zda má jít workflow přes Meta direct, CliqSales/GHL nebo Meta reporting."
category: marketing
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---

# Ad Strategist

Tento skill už netvoří vlastní reklamní strategii. Slouží jako vstupní router,
který rychle rozhodne, který specializovaný skill má agent načíst dál, aby se
nemíchal Meta direct publisher, CliqSales/GHL draft workflow a reporting.

## Kdy použít

Použij tento skill pro kompatibilitu se staršími tasky typu „použij
ad-strategist“ nebo když brief žádá reklamu/kampaň, ale není jasné, zda má jít
o direct Meta, GHL/CliqSales draft, Google/LinkedIn draft nebo reporting.

Nepoužívej ho jako třetí orchestrátor. Po routing rozhodnutí pokračuj ve
specializovaném skillu a dlouhé strategické kontrakty ber z něj.

## Workflow

1. Ověř, jestli brief stačí k rozhodnutí: cílová platforma, publisher intent,
   reporting vs nová kampaň, draft/write intent a případně CRM/follow-up.
2. Pokud uživatel explicitně chce Meta direct, Meta CLI, Facebook/Instagram
   native nebo `publishingTargets[].backend: "meta_ads_cli"`, načti
   `meta-ad-strategist`.
3. Pokud uživatel explicitně chce CliqSales, GoHighLevel, GHL, Ad Manager,
   Google Ads, LinkedIn Ads, CRM/follow-up aware plán nebo multi-platform draft,
   načti `cliqsales-ad-strategist`.
4. Pokud zadání řeší existující Meta účet, výkon, winners, bleeders, fatigue,
   rozpočtová doporučení nebo dashboard, načti `meta-ads-reporting`.
5. Pokud zadání řeší Meta Pixel, CAPI, Event Match Quality, deduplikaci eventů,
   `fbp/fbc`, tracking diagnostiku nebo Events Manager, načti
   `meta-pixel-capi-audit`.
6. Pokud není backend jasný, udělej capability check bez zápisu: jsou dostupné
   `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID`, `META_PAGE_ID`; jsou dostupné
   `GHL_API_KEY`, `GHL_LOCATION_ID`. Tokeny nevypisuj.
7. Pokud brief říká jen Meta/Facebook/Instagram a Meta direct integrace je
   dostupná, zvol `meta-ad-strategist`. Pokud Meta direct chybí a GHL je
   dostupné, zvol `cliqsales-ad-strategist` jako draft fallback a jasně uveď
   důvod.
8. Pokud nejde bezpečně rozhodnout, polož jednu krátkou otázku v task threadu:
   „Chceš direct Meta PAUSED write, nebo CliqSales/GHL draft?“
9. Do chatu nebo pracovního souboru zapiš routing výsledek a pak pokračuj
   načtením vybraného skillu.

## Output Template

```markdown
Routing reklamního workflow:
- Vybraný skill: `{meta-ad-strategist | cliqsales-ad-strategist | meta-ads-reporting | meta-pixel-capi-audit}`
- Důvod: {platforma / backend / reporting intent / tracking intent / capability check}
- Další krok: načíst `skills/{selected-skill}/SKILL.md` a pokračovat podle něj
```

Pokud routing není možný:

```markdown
Potřebuji upřesnit routing:
- Možnosti: direct Meta PAUSED write, CliqSales/GHL draft, Meta reporting
- Otázka: Chceš direct Meta PAUSED write, nebo CliqSales/GHL draft?
```

## Decision Criteria

| Podmínka | Prah | Akce |
|---|---:|---|
| Brief říká Meta direct / Meta CLI / FB+IG native | explicitní zmínka | `meta-ad-strategist` |
| Brief říká CliqSales / GHL / Ad Manager / CRM / follow-up | explicitní zmínka | `cliqsales-ad-strategist` |
| Brief říká Google nebo LinkedIn | jakákoli primární platforma | `cliqsales-ad-strategist` |
| Brief je reporting existujícího Meta účtu | performance / winners / bleeders / fatigue / dashboard | `meta-ads-reporting` |
| Brief řeší Pixel/CAPI/tracking/EMQ | pixel, CAPI, event_id, fbp/fbc nebo Events Manager | `meta-pixel-capi-audit` |
| Platforma je Meta a Meta vars chybí, GHL vars existují | 0 Meta direct capability | GHL draft fallback přes `cliqsales-ad-strategist` |
| Není jasný publisher ani platforma | žádný bezpečný default | jedna krátká otázka |

## Anti-patterns

| Nedělej | Proč | Místo toho |
|---|---|---|
| Netvoř zde vlastní strategii kampaně | vznikl by třetí orchestrátor | předej do specializovaného strategist skillu |
| Nekopíruj sem dlouhá PAUSED/GHL pravidla | duplikace source of truth | odkaž na `meta-ad-strategist` nebo `cliqsales-ad-strategist` |
| Nevolej přímo `meta-ads-cli` bez plánu | publisher nemá hádat strategii | nejdřív `meta-ad-strategist` |
| Nevolej přímo `ad-publisher` bez backend rozhodnutí | GHL draft schema se nesmí míchat s Meta direct | nejdřív `cliqsales-ad-strategist` |
| Neslibuj deep Meta reporting přes GHL-only data | GHL nemusí vracet pixel/fatigue/winners data | použij `meta-ads-reporting` nebo označ limit |

## Integration

**Uses:**
- `meta-ad-strategist` - Meta-native strategie a PAUSED direct write plán.
- `cliqsales-ad-strategist` - CliqSales/GHL draft strategie pro GHL, Google,
  LinkedIn a CRM-aware kampaně.
- `meta-ads-reporting` - read-only Meta reporting a intelligence.
- `meta-pixel-capi-audit` - read-only Pixel/CAPI, dedup a EMQ audit.

**Used by:**
- CMO workspace a starší tasky, které pořád říkají `ad-strategist`.

## Quality Checklist

- [ ] Routing výsledek ukazuje právě jeden další specializovaný skill.
- [ ] Brief s reporting intentem nejde do publisher workflow.
- [ ] Meta direct a GHL draft nejsou v jedné větě vydávány za totéž.
- [ ] Pokud chybí backend rozhodnutí, padla jen jedna krátká otázka.
- [ ] Router neobsahuje vlastní dlouhou strategickou/publisher implementaci.
