# Strategie pro nástroj `browser` — vestavěný Chromium

Sales Scout používá nástroj `browser` (headless Chromium, dostupný v prostředí openclaw) pro stránky, které `web_fetch` nepřečte správně. Tento dokument popisuje pravidla použití — kdy ano, kdy ne, jak detekovat ochranu proti robotům.

## Kdy `browser` použít

| Případ | Nástroj |
|---|---|
| LinkedIn (firma i osoba) | **vždy `browser`** |
| Statický web firmy (HTML pod 1500 znaků z `web_fetch` nebo prázdný `<body>`) | `browser` jako náhrada |
| Moderní SPA stránky (React / Next.js / Vue.js — poznáš podle prázdného `<body>` v `web_fetch`) | `browser` jako náhrada |
| Stránky za cookie bannerem, který blokuje obsah | `browser` (umí dismissnout) |
| Vše ostatní (statické HTML, JSON API, RSS) | `web_fetch` (rychlejší, levnější) |

## Pravidla pro LinkedIn

### 1. Pauza mezi navigacemi

**Mezi každou LinkedIn navigací pauza 5–10 vteřin** (random delay v tomto rozmezí). Tj. pokud děláš sekvenci „firma → osoba 1 → osoba 2", celkový čas je ~15–30 vteřin.

### 2. Max 3 LinkedIn page views per Scout brief

- 1× firma (`linkedin.com/company/[slug]`)
- 1× hlavní kontakt (`linkedin.com/in/[slug]`)
- 1× rezerva (pokud první pokus o osobu vrátí 404 nebo wrong profile)

**Pokud potřebuješ víc** — Scout brief tu firmu / osobu prostě nedostane. Lepší než vyvolat anti-bot a zablokovat IP na hodiny.

### 3. Hlavička User-Agent

`browser` nastavuje výchozí User-Agent automaticky. **Neměň ho** na něco vlastního — výchozí je realistický Chrome string. Vlastní User-Agent zvyšuje riziko detekce.

### 4. Cookie banner

LinkedIn nezobrazuje cookie banner pro anonymní návštěvy v EU (mimo přihlášené). Pokud se přesto zobrazí, **dismissni ho přes `browser` click** na tlačítko „Accept" / „Souhlasím" / „Reject all" — neignoruj, banner blokuje obsah.

### 5. Login wall

Pokud LinkedIn zobrazí prompt „Sign in to continue" nebo „Sign in to LinkedIn" → **STOP LinkedIn pro tento Scout běh**. Anonymní view je možný jen pro omezený počet pageviews per IP a den — pokud LinkedIn rozhodne, že už jsi překročil práh, blokne.

V briefu zápis: *„LinkedIn nedostupný (login wall). Zkus znovu za 2–4 hodiny."*

## Detekce ochran proti robotům

Po každé navigaci `browser` zkontroluj **text stránky** na tyto signály:

| Signál (text stránky obsahuje) | Co znamená | Akce |
|---|---|---|
| „Verify you're human" | Cloudflare / hCaptcha challenge | STOP zdroj, zápis „captcha" |
| „Just a moment..." | Cloudflare challenge (čekání na automatický pass) | Počkej max 10 vteřin a zkus znovu. Pokud druhý pokus zase „Just a moment...", STOP zdroj. |
| „Sign in to continue" | Login wall | STOP zdroj |
| „Sign in to LinkedIn" | LinkedIn login wall | STOP zdroj |
| „Page not found" / „404" | URL je špatný | Zkus alternativní URL (Brave Search), pokud nepomůže, vynechej |
| HTTP 999 | LinkedIn-specifický rate-limit | STOP LinkedIn pro tento Scout běh, zápis „LinkedIn rate-limit" |
| HTTP 403 / 429 | Generic rate-limit / blacklist | STOP zdroj, zápis „rate-limit" |

**„STOP zdroj"** neznamená skončit celý Scout brief — znamená přeskočit ten **jeden** zdroj a pokračovat s ostatními (ARES, web firmy, News). Brief se vyrobí s tím, co se podařilo získat. Chybějící sekce dostane poznámku *„nedostupné"*.

## Timeouty

| Operace | Timeout | Co dělat při překročení |
|---|---|---|
| `browser` navigate | 20 vteřin | Skip stránku, zápis „navigation timeout" |
| `browser` načtení obsahu (po navigaci) | 5 vteřin (čekání na DOM ready) | Pokud žádný viditelný text, zkus jeden retry |
| `web_fetch` | 15 vteřin (default) | Skip stránku, zápis „fetch timeout" |
| Brave Search lookup | 10 vteřin | Přeskoč, použij ruční odhad slug |

## Co `browser` extrahuje

Pro každou LinkedIn page Scout extrahuje:

### Firma (`linkedin.com/company/[slug]`)

- Hlavní nadpis (název firmy podle LinkedIn)
- Popis (`<p>` pod nadpisem)
- Detail karta: počet zaměstnanců, sektor, headquarter, founded, web
- (Volitelně) první 3 recent posts (titulek + datum)

### Osoba (`linkedin.com/in/[slug]`)

- Jméno + headline (typicky „Pozice @ Firma")
- About sekce (první 200 znaků)
- Aktuální pozice (firma + role)
- Předchozí 2–3 pozice (firma + role + období)
- Vzdělání (poslední 1–2 školy)

**Extrakce přes `browser` snapshot + selektorové dotazy**, ne přes `browser eval` s vlastním JavaScriptem (eval zvyšuje riziko detekce a je obtížnější udržovat).

## Šetrné chování — co NEDĚLAT

- ❌ **Žádný scraping smyček** — single navigate + single extract per stránka. Nikdy ne for-loop přes víc LinkedIn URL bez pauzy.
- ❌ **Žádné scrollování** pro lazy-loaded contenty — co je vidět v prvním DOM ready, to si vezmeme. Nic víc.
- ❌ **Žádné klikání na „See more" / „Show all"** — agreguje další pageviews, riziko detekce.
- ❌ **Žádný headless False mode** s vlastním Chrome — používáme výhradně vestavěný `openclaw-chromium` s výchozími parametry.
- ❌ **Žádný proxy rotation** — jedna IP, jedna identita. Anonymní LinkedIn view je legitimní použití, proxy rotation by bylo aktivní obcházení.

## Když `browser` neexistuje / je vypnutý

Pokud `browser` tool není v prostředí dostupný (`tools.browser.enabled = false` v openclaw.json):
- Pro LinkedIn → sekce „Kontakt — pozice" v briefu zůstane prázdná s poznámkou *„`browser` tool není dostupný, LinkedIn data nelze získat."*
- Pro SPA stránky firmy → náhradně přes `web_fetch` i s vědomím, že obsah bude omezený, + poznámka v briefu *„Web firmy je SPA, podrobnosti omezené."*
- Brief se vyrobí i bez `browser` — postaven na ARES, statickém webu, News a Justice.cz.

## Příklady použití (high-level)

### Krok 3 — LinkedIn firma

```
1. Najdi LinkedIn URL firmy:
   - guess slug: "Bioptron Medall s.r.o." → "bioptron-medall"
   - test URL: https://www.linkedin.com/company/bioptron-medall
   - pokud guess nesedí, Brave Search: site:linkedin.com/company "Bioptron Medall"
2. Pauza 5–10 vteřin
3. browser navigate na ověřený URL
4. Kontrola textu stránky na anti-bot signály → pokud najdeš, STOP LinkedIn
5. Extrahuj: nadpis, popis, počet zaměstnanců, sektor, lokace, web
6. Zapiš do briefu
```

### Krok 3 — LinkedIn osoba

```
1. Pauza 5–10 vteřin (od poslední LinkedIn navigace)
2. Najdi LinkedIn URL osoby:
   - guess slug: "Marek Novák" → "marek-novak" (bez diakritiky)
   - test URL: https://www.linkedin.com/in/marek-novak
   - pokud guess nesedí (404 nebo nesouvisející osoba), Brave Search: site:linkedin.com/in "Marek Novák" "Bioptron"
3. browser navigate na ověřený URL
4. Kontrola anti-bot
5. Extrahuj: jméno, headline, aktuální pozice, 2 předchozí role, vzdělání
6. Zapiš do briefu
```
