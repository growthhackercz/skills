# Judge gate — nezávislá kontrola kvality každé zprávy

Judge je kontrola kvality návrhu, **ne lidské schválení ani oprávnění k odeslání**. Každý návrh posuzuje druhý, nezávislý model; při chybě se návrh zablokuje. Přímé odesílání ze skillu je vypnuté.

## Nezávislost — jak judge spustit

Judge **NEVIDÍ tvoji úvahu ani kandidátní ranking**. Dostane pouze zprávy + surová fakta a verifikuje proti zdrojům. Celá sekvence (E1–E3) se posuzuje **v jednom vstupu, verdikt per e-mail**. Spusť subagenta s tímto vstupem:

```
Jsi kontrola kvality odchozí zákaznické komunikace. Nezávisle ověř navrženou
poprodejní sekvenci proti přiloženým faktům. Odpověz PŘESNĚ třemi řádky:
E1: APPROVE | REVISE: <konkrétní důvod> | BLOCK: <konkrétní důvod>
E2: APPROVE | REVISE: <konkrétní důvod> | BLOCK: <konkrétní důvod>
E3: APPROVE | REVISE: <konkrétní důvod> | BLOCK: <konkrétní důvod>

=== NAVRŽENÁ SEKVENCE ===
E1 (hned): <předmět + tělo> — poděkování + tipy, nesmí tvrdě prodávat
E2 (+7 dní; služby +2): <předmět + tělo + CTA odkaz a popisek> — hlavní nabídka
E3 (+14 dní; služby +7): <předmět + tělo + CTA> — dovření; přiměřený, žádný nátlak
(Pevná obálka — oslovení, podpis, patička s odhlášením — je schválená
majitelem při aktivaci a vkládá ji skript; judge posuzuje předměty, těla a CTA.
E-maily na sebe navazují — zkontroluj i, že se neopakují a nepůsobí jako spam.)

=== FAKTA (jediný zdroj pravdy) ===
1. Nákup zákazníka: <položky s názvy a datem, z purchase_sync>
2. Doporučený produkt: <záznam z catalog.json: název, cena, dostupnost, odkaz>
3. Co už zákazník má: <owned skupiny z upsell_recommend>
4. Mantinely: <salesDNA §11 doslova (mantinely + upgrade cesty) + relevantní
   řádky §1 (vykání, hlas)>
5. Kontakt: <jméno, oslovení; příznaky: čerstvá vratka/reklamace ano-ne>

=== RUBRIKA (všech 5 musí projít, jinak REVISE/BLOCK) ===
1. Produkt existuje v dodaném katalogovém snapshotu (2), cena je v mantinelech a není v (3). Skladovost uznej jen z explicitního trusted live vstupu; jinak ji netvrď ani neblokuj jako automaticky ověřenou.
2. Věta „proč" je pravdivá vůči (1) — žádné tvrzení, které z faktů neplyne.
3. Vhodnost páru: žádná citlivá/trapná kombinace (zdravotní, dětské, intimní
   kategorie), žádný necitlivý timing (čerstvá vratka/reklamace v (5)),
   žádná dražší/lepší varianta právě koupeného, pokud ji fakta (4) výslovně
   nepovolují jako upgrade cestu.
4. Jazyk a brand: správná čeština, vykání, jméno zákazníka správně, hlas dle
   mantinelů, žádné šablonovité AI fráze.
5. Compliance: možnost odhlášení přítomna (dle kanálu), žádné zavádějící
   claims (sleva/limitace, která ve faktech není).
```

## Verdikty a co s nimi

| Verdikt (per e-mail) | Akce |
|---|---|
| `APPROVE` | e-mail se plánuje (v režimu se schválením: do dávky pro majitele) |
| `REVISE: <důvod>` | JEDEN přepis daného e-mailu podle důvodu → znovu judge. Druhé REVISE = zacházej jako BLOCK. |
| `BLOCK: <důvod>` | zaloguj přes `ghl_offer_push.py --block --note "<důvod>"` a zastav celou sekvenci. Aggregate kontrakt vyžaduje schválený E1→E2→E3 řetěz; nesmí se tvářit kompletně, když některý krok chybí. |

- **Fail-closed:** judge neodpověděl, odpověděl mimo formát, subagent spadl → NEODESÍLAT, zalogovat jako BLOCK s poznámkou o chybě. Ticho je levnější než trapná zpráva pod klientovým brandem.
- **Blacklist párů:** stejný pár (koupené → doporučené) 2× BLOCK po sobě → přestaň ho navrhovat; zapiš do logu `pair_blacklist` a navrhni majiteli zápis do salesDNA §11, podsekce „Nikdy nenabízet“ — po schválení ho pak filtruje už skript.
- Každý verdikt se loguje do `upsell-log.jsonl` (pole `verdict`, `note`) — stratég v reportu vidí approve-rate a nejčastější důvody bloků.

## Kalibrace — kdy smí judge dostat volant

Judge lze kalibrovat porovnáním jeho verdiktů s rozhodnutími majitele nad návrhy:

- **shoda** = majitel schválil, judge dal APPROVE — nebo majitel zamítl a judge dal REVISE/BLOCK
- klíčová metrika = **false-APPROVE** (judge pustil, majitel zamítl) — to je jediná opravdu nebezpečná chyba

**Přepnutí na autonomii je podmíněné kalibrací: shoda ≥ 95 % na ≥ 20 dávkách.** Počet schválení sám o sobě nestačí. Nabídku na přepnutí formuluje stratég; rozhodnutí majitele se zapíše do salesDNA §1.
