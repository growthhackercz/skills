---
name: meta-pixel-capi-audit
description: "Read-only audit Meta Pixelu, Conversions API, deduplikace a Event Match Quality; použij ho pro kontrolu tracking signálu bez odesílání test eventů nebo změn konfigurace."
category: analytics
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---

# Meta Pixel CAPI Audit

Tento skill audituje Meta Pixel + Conversions API signál. Je read-only: sbírá
důkazy, kontroluje konfiguraci, odhaduje EMQ a vrací prioritizovaný fix list,
ale sám neposílá CAPI test eventy ani nemění web, GHL, Shopify, WordPress nebo
Meta nastavení.

## Kdy použít

Použij ho, když uživatel řeší Meta Pixel, Conversions API, Event Match Quality,
deduplikaci přes `event_id`, missing `fbp/fbc`, iOS signal loss, Events Manager
diagnostiku nebo otázku „proč Meta nevidí konverze“.

Nepoužívej `social-cli`. Pokud je potřeba Meta účet nebo pixel list, používej
official `meta` CLI, případně ruční read-only evidence z Events Manageru.

## Workflow

1. Ověř dostatek kontextu: web/platforma, pixel ID, ad account ID, hlavní eventy
   (`Lead`, `Purchase`, `CompleteRegistration`), tracking stack a dostupné
   Events Manager důkazy.
2. Ověř Meta capability bez vypsání tokenů: `META_ACCESS_TOKEN`,
   `META_AD_ACCOUNT_ID`, případně pixel ID z briefu nebo dokumentů.
3. Načti `references/audit-checklist.md` a vytvoř evidence JSON s tím, co je
   skutečně doložené. Nezapisuj raw PII; jen názvy matching fields.
4. Spusť dry-run nebo audit helper:
   `python3 scripts/pixel_capi_audit.py audit --client {client} --input evidence.json`.
5. Zkontroluj pass/fail pro browser pixel, server CAPI, dedup `event_id`,
   advanced matching, `fbp/fbc`, test events a platform-specific gotchas.
6. Odhadni EMQ podle dostupných matching fields. Purchase target je `9.3+`,
   Lead target je `8.0+`; vždy uveď, že jde o odhad a skutečné EMQ se ověřuje v
   Events Manageru.
7. Ulož `summary.json` a `report.md` do
   `/documents/{client}/meta-ads/pixel-capi-audits/{YYYY-MM-DD}/`.
8. Fix list seřaď podle dopadu na signál: email/phone, dedup event_id, fbp/fbc,
   IP/UA, geo fields, platform-specific server wiring.

## Output Template

```text
/documents/{client}/meta-ads/pixel-capi-audits/{YYYY-MM-DD}/
├── summary.json
└── report.md
```

`summary.json` minimálně:

```json
{
  "client": "client-slug",
  "date": "YYYY-MM-DD",
  "readOnly": true,
  "pixelId": "123456789",
  "platform": "nextjs",
  "events": [],
  "findings": [],
  "recommendations": [],
  "dataQuality": {"status": "ok", "notes": []}
}
```

## Decision Criteria

| Podmínka | Prah | Akce |
|---|---:|---|
| Lead EMQ estimate | < 8.0 | prioritizovat matching fields a fbp/fbc |
| Purchase EMQ estimate | < 9.3 | prioritizovat email+phone+dedup+fbp/fbc |
| Browser pixel a CAPI běží bez shared `event_id` | jakýkoli core event | označit double-counting risk |
| CAPI chybí pro hlavní conversion event | Lead/Purchase absent | označit signal loss risk |
| Evidence obsahuje raw PII | jakýkoli email/phone/name value | zastavit a požádat o sanitized evidence |
| Chybí Events Manager důkaz | žádný test/diagnostic export | označit `insufficient_data`, ne tvrdit hotovo |

## Anti-patterns

| Nedělej | Proč | Místo toho |
|---|---|---|
| Neposílej test eventy bez explicitního povolení | i test traffic je runtime zásah | vrať read-only audit a návod pro ruční test |
| Nezapisuj emaily/telefony do evidence | PII nesmí skončit v repo ani reportech | používej jen matching field names |
| Netvrď skutečné EMQ z odhadu | API/evidence nemusí vracet aktuální Events Manager skóre | označ `estimatedEmq` |
| Neslibuj CAPI přes GHL bez ověření nastavení | GHL může mít vlastní nativní flow | audituj jako platform evidence |
| Nepoužívej `social-cli` | není náš runtime standard | drž official `meta` CLI a read-only helper |

## Integration

**Uses:**
- `scripts/pixel_capi_audit.py` - validate/dry-run/audit nad sanitized evidence.
- `references/audit-checklist.md` - evidence schema a platform checks.
- `meta-ads-reporting` - výkonový kontext, pokud reporting ukazuje signal loss.

**Used by:**
- `ad-strategist` router pro Pixel/CAPI a tracking dotazy.
- `meta-ad-strategist` před škálováním kampaní, pokud tracking signál vypadá slabě.

## Quality Checklist

- [ ] Audit je read-only a neposlal žádný event.
- [ ] Report neobsahuje raw PII ani tokeny.
- [ ] Každý core event má browser/CAPI/dedup status.
- [ ] EMQ je označené jako estimate.
- [ ] Fix list je prioritizovaný podle dopadu na signál.
- [ ] Chybějící důkazy jsou označené jako `insufficient_data`.
