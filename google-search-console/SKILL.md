---
name: google-search-console
description: "Odpovídá na otázky, jak vás lidé najdou ve vyhledávání (Google Search Console): na jaká slova se web zobrazuje, pozice, prokliky, imprese, CTR a sledování pozic klíčových slov. Doplněk k google-analytics (návštěvnost) — tento skill řeší SEO a vyhledávání. Triggery: „na jaká slova nás najdou", „pozice ve vyhledávání", „SEO výkon", „kolik prokliků z Googlu", „Search Console", „vyhledávací dotazy", „rank tracking"."
category: analytics
status: ready
version: "1.1"
publishedAt: "2026-07-06"
metadata: {"openclaw":{"requires":{"bins":["python3","openssl"]},"emoji":"🔎"}}
---

# Google Search Console

Čte data z klientovy Google Search Console a odpovídá lidsky: krátká tabulka + 2–3 věty interpretace. Ukazuje, **jak lidé web najdou ve vyhledávání** — dotazy, pozice, prokliky. Doplňuje `google-analytics` (ta řeší, co lidé dělají už na webu). Komunikace vykáním, česky.

## Kdy použít

- Klient se ptá na SEO: na jaká slova se zobrazuje, na jakých pozicích, kolik prokliků z Googlu, které stránky táhnou vyhledávání.
- `seo-strategist` potřebuje reálné pozice pro rank tracking a content-gap.
- NEPOUŽÍVEJ pro návštěvnost/čtenost/konverze na webu — na to je `google-analytics`.

## Jak odpovídat (závazné)

1. Zavolej helper, vyber subcommand podle otázky.
2. Tabulka (max ~15 řádků) + **interpretace 2–3 větami**: kde jsou příležitosti (vysoké imprese + nízké CTR = slabý titulek; pozice 5–15 = „na dosah top pětky, stačí doladit").
3. Metriky: imprese = kolikrát se web zobrazil ve výsledcích, prokliky = kolik lidí kliklo, CTR = míra prokliku, pozice = průměrné pořadí (nižší = lepší).
4. Pozor: GSC data mají 2–3denní zpoždění (helper s tím počítá), zmínit u „dnes/včera" dotazů.

## Helper

```bash
python3 {baseDir}/scripts/gsc_query.py <subcommand> [volby]
```

| Otázka klienta | Subcommand |
|---|---|
| „Na jaká slova nás lidé najdou?" | `queries --days 28 --limit 20` (jen blog: `--path /blog`) |
| „Které stránky táhnou z vyhledávání?" | `pages --days 28` |
| „Jak si vede konkrétní článek?" | `page-detail --url /blog/muj-clanek` |
| „Kde jsme na slovech X, Y?" | `rank-tracking --keywords "jak vybrat x,cena y"` |
| týdenní SEO čísla (JSON) | `weekly-summary` |

## Rozhraní pro content engine

- **seo-strategist (rank tracking):** `rank-tracking --keywords ... --format json` → zapiš pozice do sdíleného `seo-rankings.json`. Tohle konečně naplní tu dosud prázdnou schránku reálnými daty.
- **Content-gap:** `queries` s vysokými impresemi a nízkým CTR / pozicí 5–20 = témata, kde stačí vylepšit existující článek (rychlejší výhra než psát nový).
- **Páteční report:** `weekly-summary` → lidsky: *„Web se ve vyhledávání zobrazil 12 000×, kliklo 340 lidí. Nejvíc vás hledají na ‚jak vybrat X' — jste na 6. pozici, kousek od první stránky."*

## Nastavení (jednou, přes Nastavení → Integrace)

Používá **stejný service account jako google-analytics** — klient tedy nevkládá nový klíč, jen:

- `GA_SERVICE_ACCOUNT_JSON` — už vložený (sdílený s GA); pokud GA nemá, vloží celý JSON klíč
- `GSC_SITE_URL` — adresa webu v Search Console: `sc-domain:vasedomena.cz` (doménová property) nebo `https://vasedomena.cz/` (URL property, přesně i s lomítkem)

A jednou v Search Console přidat e-mail service accountu jako uživatele (Nastavení → Uživatelé a oprávnění). Postup: `{baseDir}/references/setup-navod.md`.

## Failure handling

- Helper vypisuje česká vysvětlení sám (403 → SA e-mail není uživatel v GSC; 404 → špatný GSC_SITE_URL, doménová vs URL property; 429 → počkat). Předej text helperu, nevymýšlej diagnózu.
- Nová property nebo nový web → data se načítají několik dní; helper vrátí „(žádná data)", vysvětli klientovi, že GSC potřebuje pár dní historie.
- Nikdy nevkládej obsah klíče do chatu, logů ani reportů.

## Reference

- `{baseDir}/references/setup-navod.md` — nastavení GSC pro klienta / Success Managera (navazuje na GA setup)
