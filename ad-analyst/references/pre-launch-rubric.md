# Pre-launch rubrika (ad-score) — 0–100 před spuštěním

Ohodnoť reklamu/draft/scénář/copy **PŘED** spuštěním. Nefetchuje data. Cíl: chytit slabou reklamu dřív, než spálí rozpočet + dát **hotové lepší verze**, ne obecné rady.

## 6 vážených dimenzí (součet 100)

| Dim | Váha | Co hodnotíš | Silné = |
|---|---:|---|---|
| **Hook** | 25 | první 3 s / první frame / headline | pattern interrupt · obraz bolesti · otázka · kontrast; zastaví scroll bez „reklamního" tónu |
| **Copy** | 20 | tělo, tok, jazyk zákazníka | mluví jazykem cílového zákazníka (dle Brand DNA / voice-of-customer klienta); jedna myšlenka; žádný ad-speak |
| **CTA** | 15 | výzva k akci | jasná, jedna, nízká bariéra |
| **Offer** | 15 | nabídka / důvod teď | konkrétní hodnota, důvod jednat |
| **Emotional** | 15 | emoční tah | zrcadlí pocit (bolest/touhu), ne feature list |
| **Visual** | 10 | vizuál / formát | native/raw feel (ne „polished = red flag"); congruency formátu; čitelnost na mobilu |

## Kalibrace (tvrdá, ne inflace)
- **90–100** = připraveno ke spuštění, silné napříč dimenzemi.
- **70–89** = spustitelné po drobných fixech.
- **50–69** = přepiš klíčové dimenze před spuštěním.
- **< 50** = nespouštět; zásadní přepracování.
- Buď přísný — většina draftů má slabý **Hook** (nejvyšší váha). Nedávej 8/10 z lenosti.

## Výstup per dimenze
Skóre + **1 věta proč** + **konkrétní přepsaná verze** (ne „zlepši hook", ale hotový lepší hook). Na konci: celkové skóre, top 3 fixy podle dopadu, verdikt (spustit / fix / přepsat).

## Anti-ad kontrola (přes všechny dimenze)
- „Polished = red flag 2026" — naleštěné = vypadá jako reklama = scroll. Chceš native/raw.
- **Congruency:** formát + střih + zákazník musí sedět (podcast ad = organický klip). Detaily formátů: `ad-strategist` → `stealth-conversation-engine.md`.
- **Hook v prvních 3 s** rozhoduje o všem ostatním.

## Strojový výstup
`ad-score/<slug>.json`: `{overall, dims:{hook,copy,cta,offer,emotional,visual}, fixes:[…], verdict}` → čte `ad-strategist`.
