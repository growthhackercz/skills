# Meta Ads Reporting Output Contract

Výstupy patří pod:

```text
/documents/{client}/meta-ads/reports/{YYYY-MM-DD}-{report-type}/
├── raw/
├── summary.json
├── report.md
└── dashboard.html
```

`dashboard.html` existuje jen pro `dashboard` mode.

`summary.json` musí obsahovat:

- `client`
- `reportType`
- `date`
- `readOnly: true`
- `accountId`
- `period`
- `signals`
- `recommendations`
- `thresholds`
- `dataQuality`

`report.md` musí shrnout:

- account a období
- hlavní metriky
- winners
- bleeders / risks
- fatigue nebo anomaly signály
- read-only recommendations
- limity dat
