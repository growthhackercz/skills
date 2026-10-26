# Zdroje vyhledávání — market-aware runtime 1.4

Jediný machine source of truth pro dostupnost zdrojů je sdílený
`cs-skills/_lib/sales_market_policy.json`. Tento dokument vysvětluje, jak policy
použít; neopisuje paralelní ruční allowlist.

## Nejdřív určete market

Jeden běh zpracuje právě jeden ISO alpha-2 market. Jazyk výstupu je samostatný
`locale` a nemění registry ani normalizaci.

```bash
python3 {baseDir}/scripts/prospect_package.py market-plan \
  --market <CZ|SK|ES> \
  --locale <cs-CZ|sk-SK|es-ES|jiný-jazyk>
```

Použij jen source ID, roli a execution mode vrácené helperem. Neznámý market
končí `unsupported_market`; český ARES není fallback pro Slovensko, Španělsko
ani jinou zemi.

## Role zdrojů

- `registry_discovery` — najde firmy v oficiálním registru;
- `registry_verification` — ověří identitu, stav a registry ID;
- `registry_event` — doloží veřejnou obchodní událost, ale nemusí být úplnou
   firemní databází;
- `map_discovery` — najde lokální provozovny, není právním ověřením firmy;
- `web_discovery` — najde kandidátní weby přes platformní hledání;
- `public_contact` — veřejný firemní web s kontaktem;
- `public_signal` — aktuální zpráva, RSS nebo veřejná událost;
- `risk_verification` — insolvence, likvidace nebo jiné veřejné riziko;
- `vat_validation` — ověří už známé VAT ID, nikdy neslouží k discovery.

Jeden source run má jednu roli. Pokud stejný zdroj plní dvě role, zapiš dva
runy s konkrétními dotazy a časy.

## Trhy první verze

- `CZ / cz.v1` — ARES, Justice/ISIR, Hlídač státu, OSM/Overpass, veřejný web,
  RSS, platformní webové hledání a VIES validation;
- `SK / sk.v1` — Obchodný register SR, Obchodný vestník, OSM/Overpass,
  veřejný web, RSS, platformní webové hledání a VIES validation;
- `ES / es.v1` — veřejné BORME/BOE jako event/risk signal, OSM/Overpass,
  veřejný web, RSS, platformní hledání a VIES validation. Placené jednotlivé
  výpisy Registro Mercantil nejsou aktivní source 1.4.

Aktuální přesný seznam vždy vrať helperem; text výše je orientační mapa rolí.

## Povinná provenance

Každý `sourceRun` nese:

- kanonické `source` a `role`;
- konkrétní dotaz/filtr;
- `startedAt` a `verifiedAt` s timezone;
- stav `complete | partial | unavailable | blocked`;
- počet kandidátů;
- pouze sanitizovaný `errorCode`, nikdy raw response, HTML nebo credential.

Každý finální řádek nese skutečné `Source`, konkrétní `Source_URL` a
`VerifiedAt`. OSM, veřejný web ani web search nikdy neoznačuj jako Google Maps,
ARES nebo jiný registr.

## Degradace a STOP

- HTTP 403/429, login wall, CAPTCHA nebo paywall → konkrétní source ukončit a
  zapsat stav; neobcházet proxy/browser rotací.
- Nedostupný registry source → lze dokončit jen s nižší confidence, pokud market
  policy dovoluje jiné skutečné ověření; jinak běh zůstane rozpracovaný.
- Nedostupné platformní webové hledání → použít ostatní povolené zdroje; nikdy
  nevolat přímý Brave/Serper token.
- Apify, LinkedIn automatizace, Google Places a jiné placené zdroje nejsou v
  policy 1.4 aktivní. Fail-closed compatibility helper se nesmí obcházet.
- Kontakt bez veřejného e-mailu i telefonu není finální prospekt. Může zůstat v
  pracovní/review poznámce, ale ne v zapečetěném `prospects.csv`.

## Více zemí

Cross-market zadání rozděl na umbrella task a jeden child task/balík pro každý
market. Partial failure jedné země nesmí změnit source policy ani validitu
ostatních balíků. Sloučený manažerský přehled vzniká až z jednotlivých
validovaných výsledků.
