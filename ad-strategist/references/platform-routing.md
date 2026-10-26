# Platforma × route × capability (skryté před klientem)

Stratég vybírá cestu podle **potřebné schopnosti**, ne podle read/write. Klient tuhle logiku nevidí — jen připojí účet a vidí stav.

## Rozhodovací strom

```
Klient připojený v CliqSales/GHL?
├─ NE  → nativní meta-ads-publisher (standalone) na vše, co má připojené
│         (žádné napojení → strategie + kreativa + draft/plán, NEpublikuje)
└─ ANO → Potřebuje TENHLE úkol Meta-only hloubku?
          (Advantage+ · lookalike · CBO/bid strategy · plný targeting · day-parting · dynamic creative · deep insights · CAPI)
          ├─ NE  → cliqsales-ads-publisher (GHL) = DEFAULT, klik, multi-platforma (Meta·Google·LinkedIn)
          └─ ANO → meta-ads-publisher (nativní write/read) — 1 Facebook login, bez tokenu, bez App Review
```

**Default = GHL (~80 % případů).** Nativní `meta-ads-publisher` jen na hloubku, kterou GHL neumí, nebo pro klienty bez GHL. **Google zatím přes GHL**; nativní Google později (F5).

## Publishery (poslední míle, viditelné v Control Center)

| Publisher | Route | Umí |
|---|---|---|
| **`cliqsales-ads-publisher`** | přes CliqSales/GHL | 1 skill, multi-platforma, standardní kampaně |
| **`meta-ads-publisher`** | nativní (oficiální Meta MCP) | Meta do hloubky — **i deep WRITE** (Advantage+, lookalike, CBO, plný targeting, dynamic creative), co GHL neumí |

- **Oficiální Meta MCP write je Metou posvěcený** (stavěný pro AI agenty) — NENÍ to third-party API flagging risk. Deep READ dělá `ad-analyst` přes tentýž MCP.
- Oba publishery **standalone** (nevyžadují CliqSales platformu). Credentials (env/OAuth) žijí mimo skill → připojený klient jede hned dál.

## Co předává stratég publisheru

`ad-plan.json` (objective · audience · budget · formát · kreativy · **route × capability**). U **KAMPANĚ POZASTAVENÝ ke schválení**, ne auto-publish.
