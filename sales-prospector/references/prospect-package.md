# Prospect package 1.4

Tento kontrakt převádí výsledky jednoho market běhu do jednoho ověřitelného
balíku. `meta.json` je jediný machine source of truth; `prospects.csv` vždy
generuje helper, ne model ručně.

## Jedna kampaň = jeden market

`market` je ISO alpha-2 (`CZ`, `SK`, `ES`) a je nezávislý na jazyku výstupu
`locale`. Více zemí rozděl na samostatné tasky/složky. Výsledky lze sloučit až
po úspěšné validaci jednotlivých balíků.

Nejdřív načti aktuální policy:

```bash
python3 {baseDir}/scripts/prospect_package.py market-plan --market SK --locale cs-CZ
```

Výstup určuje přesný `adapter`, povolená source ID, role a execution mode.
Neznámý market končí `unsupported_market`; nepoužívej ARES jako fallback.

## Normalizace kandidátů

Surový JSON je pole objektů. Povinné jsou firma, skutečný source, konkrétní
`source_url`, čas ověření, confidence a veřejný e-mail nebo telefon. Registry ID
je volitelné, ale typ a hodnota musí být společně.

```json
[
  {
    "market": "SK",
    "company": "Firma s.r.o.",
    "registry_id_type": "ico",
    "registry_id": "12345678",
    "web": "https://firma.example",
    "email": "info@firma.example",
    "phone": "0901 234 567",
    "source": "sk_business_register",
    "source_url": "https://www.orsr.sk/",
    "verified_at": "2026-09-02T10:15:00Z",
    "confidence": "high",
    "contact_id": "",
    "intro_line": "Firma expanduje do dalšího regionu.",
    "interest_signal": "Nová pobočka"
  }
]
```

```bash
python3 {baseDir}/scripts/prospect_package.py normalize \
  --market SK \
  --input /tmp/raw-candidates.json \
  --output /tmp/final-candidates.json
```

Helper normalizuje marketový telefon do E.164, doménu, e-mail a registry ID.
Řádek bez veřejného e-mailu i telefonu do finálního CSV nepustí.

## Draft metadat

Po deduplikaci připrav přesně tento tvar. `sourceRuns` popisuje skutečně
provedené běhy; fallback musí mít vlastní source ID. `errorCode` je jen
sanitizovaný kód, nikdy raw response nebo credential.

```json
{
  "taskId": 123,
  "taskContract": "sales-prospector:prospect-package-v1-4",
  "campaign": "2026-09-02-sk-b2b-saas",
  "market": "SK",
  "locale": "cs-CZ",
  "marketAdapter": "sk.v1",
  "createdAt": "2026-09-02T10:20:00Z",
  "sourceRuns": [
    {
      "source": "sk_business_register",
      "role": "registry_discovery",
      "status": "complete",
      "query": "software Bratislava",
      "sourceUrl": "https://www.orsr.sk/",
      "startedAt": "2026-09-02T10:00:00Z",
      "verifiedAt": "2026-09-02T10:15:00Z",
      "candidateCount": 42,
      "errorCode": null
    }
  ],
  "funnel": {
    "rawCandidates": 42,
    "withPublicContact": 31,
    "afterProfileFilter": 24,
    "afterLocalDedup": 20,
    "afterCrmDedup": 18,
    "final": 18
  },
  "crmDedup": {
    "status": "complete",
    "observedAt": "2026-09-02T10:19:00Z",
    "checked": 20,
    "unknown": 0
  }
}
```

Funnel musí být monotónní. `crmDedup.status` musí být `complete`, počet
`unknown` nula a `checked` se musí přesně rovnat `afterLocalDedup`.

## Contract se volí jednou

Task binding je neměnný. Nejdřív se uživatele zeptej, zda chce jen soubory,
nebo také tag plán pro exact existující CRM kontakty. Potom draft zapečeť:

- jen soubory → `sales-prospector:prospect-package-v1-4`;
- tag plán → `sales-prospector:prospect-actions-v1-4`.

Nikdy nejdřív nenastavuj první contract a potom jej nepřepínej druhým.

## Seal a validace

```bash
python3 {baseDir}/scripts/prospect_package.py seal \
  --draft /tmp/prospect-meta-123.json \
  --candidates /tmp/final-candidates.json \
  --csv /documents/sales/prospects/2026-09-02-sk-b2b-saas/prospects.csv \
  --meta /documents/sales/prospects/2026-09-02-sk-b2b-saas/meta.json
```

Helper vytvoří kanonické CSV, spočítá SHA-256 přes jeho přesné byty, sestaví
`cliqsales.sales_prospect_package.v1` a ještě před publikací oba soubory
provider-free ověří. Pád mezi dvěma atomickými replace může vytvořit jen
neshodný pár, který CC checkpoint odmítne; nikdy falešný PASS.

Pro ruční opakovanou kontrolu:

```bash
python3 {baseDir}/scripts/prospect_package.py validate \
  --meta /documents/sales/prospects/2026-09-02-sk-b2b-saas/meta.json \
  --csv /documents/sales/prospects/2026-09-02-sk-b2b-saas/prospects.csv \
  --task-id 123 \
  --campaign 2026-09-02-sk-b2b-saas \
  --task-contract sales-prospector:prospect-package-v1-4
```

Task přesuň do review až po `ok: true`. CC stejný balík ověří nezávisle; model
nemůže checkpoint přeskočit. Nulový výsledek je platný, pokud CSV obsahuje
kanonickou hlavičku, funnel končí nulou a CRM dedup je complete.
