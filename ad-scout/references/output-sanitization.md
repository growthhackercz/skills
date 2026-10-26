# Sanitizace výstupu — kdy nejmenovat zdroj (rizikově vázané)

**Princip (2026-07-12, Pavlova korekce):** Sanitizace (skrýt zdroj/metodu) je **POVINNÁ jen tam, kde bychom porušovali podmínky služby nebo riskovali právní problém.** Ne plošně. Kde je zdroj veřejný a nic neporušujeme, jmenovat SMÍME.

## 🛑 MUSÍ skrýt (reálné ToS / právní riziko)
- **Srovnávače / agregátory — Heureka, Zboží.cz.** Jejich databáze je chráněná (zvláštní právo pořizovatele, sui generis) + ToS zakazují automatický sběr. **NIKDY nejmenovat, nikdy neprozradit, že z nich bereme data / extrahujeme jejich databázi.** Týká se Product Intelligence Boardu (ceny/nabídky).
- V klientském výstupu vždy nahraď obecným: „z veřejně dostupných tržních dat" / „veřejná knihovna reklam" / „srovnávač cen" (obecně, bez názvu).

## ✅ SMÍME jmenovat (veřejné, žádná povinnost skrývat)
- **Reklamní registry — Meta Ad Library, Google Ads Transparency.** Veřejné transparency nástroje, platformy je **samy zveřejňují** (i oficiální API). Nic neporušujeme → jmenovat je OK. (Pro čistotu můžeš být i obecný, ale není to nutnost.)
- **Kanály — Facebook, Instagram, Google, YouTube, TikTok, e-shopy.** Vždy OK (popisují, kde konkurence inzeruje / kde je produkt).

## 🧹 Radši vynechat kvůli ČISTOTĚ (ne kvůli právu)
- „scraping" / „scrapujeme", „snapshot", „SERP", „DPA", **Apify**, jména aktorů — nejsou právní problém, ale zní technicky / neprofesionálně a prozrazují metodu. Do klientského textu je nedávej; interní reference (`data-sources.md`) je klidně používá.

## Praktický default rendereru
Renderer (`board.py` / `adboard.py`) drží **obecný „zdroj"** (masthead/patička) — bezpečný default (pokryje i Heureku) a čte se čistě; kanály nech u obsahu (badge/sekce). U ad boardů (Meta/Google) můžeš být konkrétnější, když to dává smysl — není zakázané.

## Kde to hlídat (rychlá tabulka)
| Zdroj ve výstupu | Pravidlo |
|---|---|
| Heureka / Zboží / srovnávač | 🛑 nikdy jménem → „veřejně dostupná tržní data / srovnávač cen" |
| Meta Ad Library / Google Ads Transparency | ✅ smíš jmenovat (default ale obecný „veřejná knihovna reklam") |
| Facebook / Instagram / Google / YouTube / TikTok | ✅ OK (kanál u obsahu) |
| Apify / aktory / „scraping" / „snapshot" | 🧹 vynech (čistota, ne právo) |

Reference čistého výstupu: `assets/board-template.html`.
