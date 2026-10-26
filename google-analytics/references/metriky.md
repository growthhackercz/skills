# Slovník metrik a dimenzí — čeština ↔ GA4 API

Používej v odpovědích české názvy; do API jdou anglické. Kompletní seznam: GA4 Data API dimensions & metrics explorer.

## Metriky

| Česky (do odpovědi) | GA4 API | Pozn. |
|---|---|---|
| Návštěvníci | `totalUsers` | unikátní lidé |
| Noví návštěvníci | `newUsers` | |
| Aktivní návštěvníci | `activeUsers` | default „users" v GA UI |
| Návštěvy | `sessions` | |
| Zobrazení stránek | `screenPageViews` | |
| Konverze | `conversions` | klíčové události |
| Míra zapojení | `engagementRate` | 0–1, ukazuj v % |
| Průměrná délka návštěvy | `averageSessionDuration` | sekundy → převeď na min:s |
| Tržby | `totalRevenue` | e-shopy |

## Dimenze

| Česky | GA4 API | Pozn. |
|---|---|---|
| Datum | `date` | YYYYMMDD |
| Stránka (cesta) | `pagePath` | |
| Titulek stránky | `pageTitle` | |
| Vstupní stránka | `landingPage` | |
| Zdroj návštěv (kanál) | `sessionDefaultChannelGroup` | Organic Search, Direct, Paid Social… |
| Zdroj / médium | `sessionSource` / `sessionMedium` | detailnější |
| Zařízení | `deviceCategory` | desktop / mobile / tablet |
| Země / město | `country` / `city` | |
| Obrazovka (realtime) | `unifiedScreenName` | jen runRealtimeReport |

## Překlad kanálů do češtiny

Organic Search = vyhledávače (neplacené) · Direct = přímá návštěva · Paid Search = placené vyhledávání · Paid Social = placené sociální sítě · Organic Social = sociální sítě (neplacené) · Email = e-mail · Referral = odkazy z jiných webů · Unassigned = nezařazené.

## Časté kombinace

- Čtenost blogu: metriky `screenPageViews,totalUsers` × dimenze `pagePath` + filtr `/blog`
- Trend návštěvnosti: `totalUsers,sessions` × `date`
- Výkon kanálů: `sessions,conversions` × `sessionDefaultChannelGroup`
- Mobil vs desktop: `sessions,engagementRate` × `deviceCategory`
