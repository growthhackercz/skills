# Browser strategie — market-aware runtime 1.4

`browser` použij jen na veřejném webu firmy, když `web_fetch` vrátí prázdnou
kostru nebo stránka potřebuje JavaScript. Není to cesta k obcházení ochrany.

## Postup

1. Otevři přesnou veřejnou URL firmy.
2. Počkej nejvýše 10 sekund na běžné vykreslení.
3. Načti jen části potřebné pro brief: nabídka, reference, tým a kontakt.
4. Zavři stránku a zapiš URL, čas a výsledek do auditu.

## Okamžitý STOP zdroje

- captcha nebo „Verify you are human";
- login wall či paywall;
- druhé zobrazení „Just a moment…";
- HTTP 403/429 po jednom běžném opakování;
- požadavek na cookies, přihlášení nebo změnu identity;
- LinkedIn.

Po STOP zdroj označ jako blokovaný a pokračuj jiným povoleným zdrojem.
Nevkládej proxy, nestřídej IP, nepoužívej klientské cookies a nespouštěj
placený fallback. Apify je v této verzi vypnutý a jeho compatibility helper
vrací `metered_action_type_unavailable` bez provider callu.

Brief musí být pravdivě dokončitelný i bez browseru: použij CRM snapshot,
marketový registry source, statický veřejný web a zprávy; chybějící poznatek
označ jako neověřený.
