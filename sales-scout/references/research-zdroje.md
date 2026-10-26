# Zdroje Sales Scouta — market-aware runtime 1.4

Scout používá stejný machine source of truth jako Prospector:
`cs-skills/_lib/sales_market_policy.json`. Přesný market plán načti:

```bash
python3 {baseDir}/scripts/market_context.py market-plan --market <CZ|SK|ES>
```

Neznámý market končí `unsupported_market`. ARES je pouze source `cz.v1`; pro
SK/ES ani jako fallback neplatí.

## Pořadí důkazů

1. **Exact CRM snapshot** — identita cílového kontaktu, pipeline a interní
   kontext; nikdy discovery ani zápis.
2. **Registry verification marketu** — právní identita, registry ID, sídlo,
   forma a stav pouze v rozsahu skutečné odpovědi.
3. **Veřejný web firmy** — nabídka, segmenty, reference, tým a kontakt.
4. **Registry event / risk verification** — obchodní události, insolvence nebo
   jiné marketové veřejné riziko.
5. **Veřejné RSS a platformní webové hledání** — čerstvé obchodní signály.

VIES validuje pouze již známé EU VAT ID; nehledá firmy. OSM/Overpass může
doložit provozovnu, ale není právním ověřením subjektu.

Při rozporu má přednost exact CRM identita pro cílový kontakt a čerstvější
autoritativní veřejný zdroj pro firemní fakt. Rozpor popiš; neslučuj firmy nebo
osoby odhadem.

## Provenance

U každého podstatného tvrzení drž:

- kanonické source ID a roli z policy;
- konkrétní veřejnou URL;
- čas ověření s timezone;
- `verified | hypothesis | unavailable | conflicting`;
- která věta briefu z důkazu vychází.

Pro Prospector vstup zachovej původní source provenance a při Scout revalidaci
přidej nový čas/URL; nepřepisuj historický důkaz novým názvem.

## Veřejný web a browser

- začni `web_fetch` na konkrétní URL;
- browser použij jen pro prázdný JavaScriptový shell stejného firemního webu;
- 403/429, login wall, CAPTCHA nebo paywall source okamžitě ukončí;
- nestřídej proxy, identity ani klientské cookies;
- prázdný výsledek není důkaz, že informace neexistuje.

## Vypnuté zdroje

LinkedIn automatizace, Apify, Google Places a přímé provider credentials nejsou
v policy 1.4 aktivní. Nepoužívej browser, `web_fetch`, cookies ani vlastní HTTP
call k jejich obcházení. Compatibility helper vrací
`metered_action_type_unavailable`, nenačte token a neutratí kredit.
