---
name: google-analytics
description: "Odpovídá na otázky o návštěvnosti webu z Google Analytics (GA4): kolik lidí na webu, nejčtenější stránky a články, zdroje návštěv, konverze, dění právě teď. Dodává týdenní čísla pro obsahové reporty. Triggery: „návštěvnost", „kolik lidí bylo na webu", „nejčtenější články", „odkud chodí návštěvníci", „konverze z webu", „co se děje na webu teď", „Google Analytics"."
category: analytics
status: ready
version: "1.1"
publishedAt: "2026-07-06"
metadata: {"openclaw":{"requires":{"bins":["python3","openssl"]},"emoji":"📈"}}
---

# Google Analytics

Čte data z klientova Google Analytics 4 a odpovídá lidsky: krátká tabulka + 2–3 věty interpretace (co to znamená, co vyčnívá). Nikdy nesypat surová data bez vysvětlení. Komunikace s klientem vykáním, česky.

## Kdy použít

- Klient se ptá na návštěvnost, čtenost, zdroje návštěv, konverze, realtime dění.
- Content engine potřebuje čísla: páteční report, zlatý fond (top obsah), content-gap náměty.
- NEPOUŽÍVEJ pro Google Ads / Meta Ads výkon reklam — na to jsou reklamní skilly.

## Jak odpovídat (závazné)

1. Zavolej helper (níže), vyber správný subcommand podle otázky.
2. Ukaž malou tabulku (max ~10 řádků) + **interpretaci 2–3 větami**: trend vs minulé období, co vyčnívá, případně 1 doporučení.
3. Čísla zaokrouhluj lidsky („přes 800 návštěvníků", ne „823,0").
4. Metriky překládej: totalUsers = návštěvníci, sessions = návštěvy, screenPageViews = zobrazení stránek, conversions = konverze (slovník: `{baseDir}/references/metriky.md`).

## Helper

```bash
python3 {baseDir}/scripts/ga4_query.py <subcommand> [volby]
```

| Otázka klienta | Subcommand |
|---|---|
| „Kolik lidí bylo na webu?" / celkový přehled | `overview --days 7` (nebo 30) |
| „Nejčtenější stránky/články?" | `top-content --days 30 --limit 10` (jen blog: `--path-filter /blog`) |
| „Odkud chodí návštěvníci?" | `sources --days 30` |
| „Co nám vede ke konverzím?" | `conversions --days 30` |
| „Co se děje na webu právě teď?" | `realtime` |
| týdenní čísla pro report (JSON) | `weekly-summary` |
| cokoli na míru | `report --metrics ... --dimensions ... --start ... --end ...` |

`overview` vždy srovnává s předchozím stejně dlouhým obdobím — změnu v % vždy zmiň v interpretaci.

## Rozhraní pro content engine

- **Páteční report / content-performance:** `weekly-summary` → JSON (users/sessions/pageviews/conversions vs minulý týden + top 5 stránek + top 5 zdrojů). Do klientského reportu přelož lidsky: *„Vaše články tento týden přečetlo 840 lidí, 12 z nich poslalo poptávku."*
- **Zlatý fond (recyklace):** `top-content --days 90 --format json` → kandidáti na refresh.
- **Content-gap:** `conversions` vs `top-content` — stránky s vysokou čteností a nízkou konverzí = náměty na CTA/obsah.

## Nastavení (jednou, přes Nastavení → Integrace)

Klient (nebo Success Manager za něj) vloží:

- `GA_SERVICE_ACCOUNT_JSON` — celý obsah staženého JSON klíče service accountu
- `GA4_PROPERTY_ID` — číslo property (GA: Správce → Nastavení služby → ID služby)

Postup vytvoření klíče krok za krokem: `{baseDir}/references/setup-navod.md`. Service account e-mail musí být v GA přidaný jako **Čtenář** — to je nejčastější zádrhel.

## Failure handling

- Helper vypisuje česká vysvětlení sám (chybějící klíč → 4krokový návod; 403 → SA e-mail není Čtenář v GA; 404 → špatné Property ID; 429 → počkat). **Předej klientovi text helperu, nevymýšlej vlastní diagnózu.**
- Klient nemá GA4 (jen starý web bez měření) → vysvětli, že web potřebuje nasazené GA4 měření, a nabídni, že instrukce připraví technický kontakt.
- Nikdy nevkládej obsah klíče do chatu, logů ani reportů.

## Reference

- `{baseDir}/references/metriky.md` — slovník metrik a dimenzí (CZ ↔ GA4 API)
- `{baseDir}/references/setup-navod.md` — 4 kroky nastavení pro klienta / Success Managera
