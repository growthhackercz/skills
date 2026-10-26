# Angle OS — awareness žebřík + ideace a řazení úhlů

Jádro stratéga. Úhel = *co* říkáš (ne formát = *jak*, ne persona = *komu*). Ideace úhlů je práce modelu.

## Awareness žebřík (Eugene Schwartz) — hlavní páka škálování

Každý úhel patří na jednu úroveň podle toho, kde je zákazník:

| Úroveň | Zákazník | Úhel mluví o… |
|---|---|---|
| **Unaware** | netuší, že má problém | příběh / obraz světa / provokace („takhle to dneska chodí") |
| **Problem-Aware** | cítí bolest, nezná řešení | **bolest a její cena** („topíte se v rutině") |
| **Solution-Aware** | zná typ řešení, ne váš produkt | proč tenhle typ řešení (AI tým) funguje |
| **Product-Aware** | zná vás, váhá | důkaz · srovnání · námitky · nabídka |
| **Most-Aware** | připraven koupit | cena · deadline · bonus · CTA |

**„90% unlock":** většina brandů zasekne publikum na bottom-funnel (Product/Most-Aware) a vyčerpá ho (frequency 5–7 → pool je mrtvý). **Posun O ÚROVEŇ VÝŠ = nový hladový trh**, ne nová reklama. Proto: **80 % cold trafficu cílit na Unaware / Problem-Aware.**

## Ideace — jak vygenerovat ≥10 úhlů

Zdroje surovin (v tomhle pořadí):
1. **Raw Diet** (`voice-of-customer.json`) — doslovné bolesti/námitky/touhy zákazníka → nejsilnější úhly (jeho slovy).
2. **Mapa úhlů z `ad-scout`** — 🟢 volné úhly (nikdo nejede) = arbitráž · 🔴 přeplněné = ověřené, ale nabité.
3. **DNA karty** — úhly vítězných reklam konkurence k naklonování.
4. **Product DNA** — mechanismus, odlišovač, nabídka.

Pro každý úhel zapiš: `název · awareness level · z čeho vychází (Raw Diet/DNA/gap) · komu (persona) · 1 větou pointa`.

## Řazení a výběr

Skóruj úhel dvěma osami a hledej **arbitráž** (průnik):
- **Trakce** — má organickou/reklamní trakci (z boardu / DNA karet)?
- **Prostor** — jak je přeplněný (🟢 volný > 🔮 sporný > 🔴 crowded)?

**Nejsilnější doporučení = úhel s trakcí, který nikdo neinzeruje** (ověřený + prázdný prostor). Vyber mix napříč awareness úrovněmi (ne jen bottom-funnel).

## Diverzita = 5 os (kalibrace)

Pravá diverzita = **nová kreativa** (nový entity ID = čerstvé učení pro Andromedu), ne tweaky téhož.

| Osa | Kalibrace |
|---|---|
| **Persona** | 3–7 na produkt |
| **Angle** | 10+ testovaných úhlů |
| **Format** | ≥3 formáty na úhel |
| **Actor** | tvůrce = plná proměnná, ne detail |
| **Awareness** | 80 % cold = Unaware/Problem-Aware |

## Naming (páteř učení)

Každá reklama tagovaná **`Persona_Angle_Format_Hook`** — bez toho nejde srovnat, co vyhrálo a PROČ. Uvnitř karty kampaně z toho vzniká **Angle Leaderboard** (řazení podle psychologického triggeru, NE podle „Amount Spent").

## PDA matice — matice pokrytí (co jsme zkusili × co vyhrálo × díry)

Srdce kroku **Naklonuj** metody **Ad DNA Method™**. Klientský/marketingový název = **PDA matice** (**P**ersona × touha/**D**esire × povědomí o produktu/**A**wareness) — čisté 3 osy, rýmuje se s „DNA". Interně ji drž jako **žijící matici** `combination-matrix.json` (`/documents/ads/campaigns/{campaign-slug}/`) se **4. výkonovou osou Formát** (jak se doručí) a „touhu/Desire" vyjádři jako **úhel**. Pro každou buňku **Persona × Awareness × Angle × Format** stav: `untested` (díra) · `testing` (běží) · `winner` (vyhrálo) · `killed` (propadlo).

**Kdo ji drží:**
- **`ad-strategist` (ideace):** před spuštěním zapíše, které buňky kampaň pokrývá; při výběru úhlů preferuje **`untested` díry sousedící s `winner` buňkami** (rozšiř vítěze o novou personu/awareness/formát) před opakováním obsazených.
- **`ad-analyst` (learning):** po auditu překlopí buňky na `winner`/`killed` podle Angle Leaderboardu; díry (co nikdo nezkusil) hlásí zpět stratégovi jako **další tah**.

**Schéma (řídce — jen dotčené buňky, ne plný kartézský součin):**
```json
{
  "campaignSlug": "…",
  "axes": {"persona": ["…"], "awareness": ["unaware","problem_aware","…"], "angle": ["…"], "format": ["ugc","…"]},
  "cells": [
    {"persona": "…", "awareness": "problem_aware", "angle": "…", "format": "ugc", "status": "winner", "adName": "Persona_Angle_Format_Hook", "note": "…"}
  ]
}
```
**Proč řídce:** plný grid person×awareness×úhlů×formátů = stovky buněk. Sleduj jen buňky, které jsi zkusil nebo cíleně chceš zkusit. Cíl matice = odpovědět „**co jsme ještě nezkusili a mělo by fungovat**" (arbitráž), ne vyplnit vše.
