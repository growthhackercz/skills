# Output contract — co analytik strojově produkuje

Přesný tvar výstupů `ad-analyst`. Strojové soubory čte `ad-strategist` (fáze DIAGNÓZA Autopilot smyčky — `ad-strategist/references/modes-autopilot.md`). **Vše `readOnly: true`** — analytik nic nemění. Převzato z reálného `meta-ads-reporting` + `meta-pixel-capi-audit`.

## A · Live audit / reporting (`meta_report.py`)
Helper **nevolá Meta** — agent nasbírá raw read-only JSON přes `meta` CLI (`meta -o json ads …`) do `raw/`, helper z toho **deterministicky** vyrenderuje report. Před sběrem vždy `dry-run` (vypíše plán příkazů, nic neutratí).

**Report modes** (helper `--mode`): `daily-check` · `overview` · `winners` · `bleeders` · `creative-fatigue` · `budget-efficiency` · `budget-recommendations` · `weekly-brief` · `dashboard` · `anomaly-detection`. Autopilot týdenní běh = `weekly-brief` (+ `creative-fatigue` / `bleeders` na signály).

**Co helper reálně dělá (nepřeceňuj):**
- Mode ovlivňuje **label + plán příkazů + dashboard**, ne (zatím) odlišnou analytickou logiku — signály (winners/bleeders/frequency) počítá stejně napříč mody. Budget/anomaly/weekly hloubku **dopisuje agent** nad `summary.json`.
- `report.md` a `dashboard.html` z helperu jsou **anglický strojový mezikrok**. **Klientský report píše agent** česky (vykání) ze `summary.json` — helper výstup klientovi nepředávej doslova.
- **Winners = top-5 podle CTR, spend-gated** (reklama pod prahem denního spendu se mezi vítěze nedostane — šum vyfiltrován v kódu). **CPA:** `metrics.blendedCostPerResult` + `metrics.totalResults` počítá helper. **ROAS** helper nepočítá — dopočítej z `purchase_roas`/`action_values` na řádcích.
- **Fatigue / CPC / CPM spike** vystřelí jen když raw JSON obsahuje **předchozí období** (`previous_ctr`/`previous_cpc`/`previous_cpm`). Pro „creative-fatigue (30d+7d)" musí agent sesbírat **dvě období** a předchozí hodnoty do raw doplnit — z jednoho snímku fatigue nevznikne.

**Výstupní cesta:** `/documents/ads/reports/{YYYY-MM-DD}-{mode}/`
```text
├── raw/            # raw meta CLI JSON (tokeny/page tokeny sanitizované)
├── summary.json    # strojový kontrakt (čte ad-strategist)
├── report.md       # lidský report (klientovi, vykání)
└── dashboard.html  # jen mode dashboard
```

`summary.json` (min. pole): `client` · `reportType` · `date` · **`readOnly: true`** · `accountId` · `period` · `metrics` · `signals[]` · `recommendations[]` (každé `readOnly: true`) · `thresholds` · `dataQuality{status, notes}`. Když chybí data → `dataQuality.status: "insufficient_data"` (netvrď výkon z ničeho).

Prahy v `thresholds` = default heuristiky (viz `audit-signals.md`), ne auto-rozhodnutí.

## B · Tracking audit — Pixel/CAPI (`pixel_capi_audit.py`)
Read-only audit ze **sanitizované** evidence (jen názvy matching polí, **NIKDY raw email/telefon/IP/token** — helper na PII tvrdě spadne). Před auditem `dry-run`.

**Výstupní cesta:** `/documents/ads/pixel-capi-audits/{YYYY-MM-DD}/`
```text
├── summary.json
└── report.md
```

`summary.json` (min.): `client` · `date` · **`readOnly: true`** · `pixelId` · `platform` · `events[]` (per event: browserPixel/serverCapi/eventIdDedup/matchingFields/**estimatedEmq**/targetEmq) · `findings[]` (severity critical/warning/info + code) · `recommendations[]` · `dataQuality`.

**EMQ cíle** (odhad, ověřit v Events Manageru): Purchase **9,3+** výborně / 8,0–9,2 dobře / <8,0 opravit · Lead **8,0+** výborně / 6,5–7,9 dobře / <6,5 opravit. Vždy značit `estimatedEmq` (ne skutečné skóre). (Skript používá **jediný target** = horní hranice: Purchase 9,3 / Lead 8,0 / ostatní eventy 7,0; pod ním `low_estimated_emq`. Pásma výborně/dobře/opravit jsou pro **tvůj výklad**, ne kód — odhad z vah bývá konzervativní, ber `low_estimated_emq` jako podnět zlepšit matching, ne jako selhání.)

## C · Learning výstupy (zpět do enginu)
- `evergreen-ads.json` — zlatý fond vítězných bloků. **Cesta:** `/documents/ads/evergreen-ads.json` (píše analytik, čte `ad-strategist` compounding).
- **Pre-launch skóre:** `/documents/ads/ad-score/{slug}.json`.
- Angle Leaderboard — řazení podle úhlu, ne podle „Amount Spent".
- Wiki karty „Kampaň" přes `WikiManager` (spend/ROAS/CTR/frequency křivka), když je wiki k dispozici — elegantní fallback bez chyby, když typ karty neexistuje.

## Pravidla kontraktu
- **Read-only všude** — `readOnly: true` v každém `summary.json`; žádná write operace, žádná auto-změna budgetu.
- **Sanitizace** — raw výstupy s tokeny/page tokeny nikdy do chatu; PII nikdy do evidence.
- **Degradace** — chybí nativní Meta → GHL reporting → poznamenej limit (GHL nedá Meta fatigue/pixel/EMQ data). Nikdy neslibuj data, co zdroj nedává.
- **Klientovi** jen `report.md` / dashboard (lidsky, vykání, žádná architektura ani vendor jména); `summary.json` je strojový.
