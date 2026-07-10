---
name: meta-ads-reporting
description: "Read-only Meta Ads reporting a intelligence; použij ho pro overview, winners, bleeders, fatigue, budget efficiency, weekly brief a dashboard bez změn kampaní."
category: analytics
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---

# Meta Ads Reporting

Tento skill čte výkon Meta Ads účtu a vyrábí reporty nebo doporučení. Nikdy
nemění kampaně, budgety, statusy, ad sety ani kreativy.

## Kdy použít

Použij ho pro existující Meta Ads účet, když uživatel chce overview, denní
kontrolu, winners, bleeders, creative fatigue, budget efficiency, read-only
budget recommendations, weekly brief, dashboard nebo anomaly detection.

Používej official `meta` CLI dostupné jako `meta`. Nepoužívej `social-cli`.

Podporované modes:

- `daily-check`
- `overview`
- `winners`
- `bleeders`
- `creative-fatigue`
- `budget-efficiency`
- `budget-recommendations`
- `weekly-brief`
- `dashboard`
- `anomaly-detection`

## Workflow

1. Ověř dostatek kontextu: klient/projekt slug, časové období, report mode a
   zda jde o read-only reporting existujícího účtu.
2. Ověř Meta capability bez vypsání tokenů: `META_ACCESS_TOKEN`,
   `META_AD_ACCOUNT_ID`, `META_PAGE_ID`; při chybě vrať blocker.
3. Spusť helper pro suchý plán reportu:
   `python3 scripts/meta_report.py dry-run --client {client} --mode {mode}`.
4. Přečti relevantní data přes `meta -o json ads ...` a ukládej raw výstupy do
   `raw/`. Výstupy se stránkovými tokeny nebo access tokeny vždy sanitizuj.
5. Vyhodnoť mode podle `references/report-types.md` a thresholds podle
   `references/thresholds.md`.
6. Vyrenderuj report z raw JSON dat:
   `python3 scripts/meta_report.py render --client {client} --mode {mode} --raw-dir {report-dir}/raw --output-dir {report-dir}`.
7. Helper vytvoří `summary.json` s metrikami, detekovanými signály,
   doporučeními a explicitním `readOnly: true`.
8. Helper vytvoří lidský `report.md`. Pro `dashboard` navíc vytvoří
   `dashboard.html`.
9. Doporučení formuluj jako návrhy pro člověka; nespouštěj žádné write příkazy.
10. Pokud data nestačí pro závěr, označ `insufficient_data` a popiš, která pole
   nebo časové období chybí.

## Output Template

Výstupy ukládej přesně sem:

```text
/documents/{client}/meta-ads/reports/{YYYY-MM-DD}-{report-type}/
├── raw/
├── summary.json
├── report.md
└── dashboard.html  # jen mode dashboard
```

`summary.json` minimálně:

```json
{
  "client": "client-slug",
  "reportType": "winners",
  "date": "YYYY-MM-DD",
  "readOnly": true,
  "accountId": "act_...",
  "period": {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"},
  "signals": [],
  "recommendations": [],
  "thresholds": {},
  "dataQuality": {"status": "ok", "notes": []}
}
```

## Decision Criteria

| Podmínka | Prah | Akce |
|---|---:|---|
| Bleeder CTR | < 1.0% | označit jako bleeder candidate |
| High frequency | > 3.5 | označit frequency risk |
| Fatigue CTR drop | > 20% | označit creative fatigue |
| CPC spike | > 30% | označit CPC anomaly |
| CPM spike | > 25% | označit CPM anomaly |
| Daily spend noise | < 50 currency units | nesignalizovat jako silnou anomálii bez další evidence |

## Anti-patterns

| Nedělej | Proč | Místo toho |
|---|---|---|
| Neměň budget, status ani kampaně | reporting je read-only | vrať doporučení pro člověka |
| Nepoužívej `social-cli` | není náš runtime standard | použij official `meta` CLI |
| Neposílej raw page output s tokeny do chatu | může obsahovat citlivé hodnoty | sanitizuj raw a reportuj jen potřebné ID |
| Neber threshold jako absolutní pravdu bez kontextu | malé spendy jsou šum | uveď confidence a spend context |
| Nedávej dashboard bez `summary.json` | HTML bez datového kontraktu je obtížně auditovatelné | nejdřív `summary.json`, potom HTML |

## Integration

**Uses:**
- `meta` CLI - read-only Meta Ads data.
- `scripts/meta_report.py` - validate/dry-run kontrakt pro report modes.
- `references/report-types.md` - mode-specific data needs.
- `references/thresholds.md` - výchozí prahy.
- `references/output-contract.md` - přesný výstupní layout.

**Used by:**
- `ad-strategist` router pro reporting dotazy.
- `meta-ad-strategist` jako intelligence modul před tvorbou nové Meta strategie.

## Quality Checklist

- [ ] Report neobsahuje write operaci ani live změnu.
- [ ] Výstupní adresář odpovídá `/documents/{client}/meta-ads/reports/...`.
- [ ] `summary.json` má `readOnly: true`.
- [ ] Raw data jsou uložená v `raw/` a citlivé hodnoty nejsou v chatu.
- [ ] Mode odpovídá jednomu z podporovaných report types.
- [ ] Doporučení jsou jasně označená jako read-only recommendations.
