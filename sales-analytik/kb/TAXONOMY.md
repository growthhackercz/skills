# TAXONOMY — fáze hovoru, námitky, signály, chyby

Sdílený slovník. Mentor jím segmentuje a klasifikuje, analytik jím agreguje napříč hovory. Používej tyhle přesné klíče (ne synonyma), ať jsou data porovnatelná.

## Fáze hovoru (15)

Stejné pravidlo: klíč do dat, **český název do výstupů**.

| Klíč | Česky | Klíč | Česky |
|---|---|---|---|
| `opening` | otevření | `certainty_building` | budování jistoty |
| `rapport` | navázání vztahu | `price_delivery` | sdělení ceny |
| `agenda` | agenda hovoru | `objection_handling` | práce s námitkami |
| `discovery` | discovery a diagnostika | `close` | closing |
| `pain_and_consequence` | bolest a její dopad | `follow_up_commitment` | domluvený další krok |
| `qualification` | kvalifikace | `post_call` | po hovoru |
| `future_state` | vize budoucího stavu | | |
| `transition` | přechod k řešení | | |
| `presentation` | prezentace řešení | | |

U každé fáze urči: proběhla / chybí · kvalita přechodu · předčasné uzavírání · zbytečné vracení · ztráta kontroly nad linií.

## Typy námitek (21)

⚠️ **Klíč vlevo je JEN technický identifikátor do dat** (aby šly hovory porovnávat napříč obdobími). **V každém textu, který uvidí klient nebo obchodník — karta, detailní rozbor, report — používej VÝHRADNĚ český název vpravo.** Anglický klíč se do výstupu nikdy nepíše.

| Klíč (data) | Česky (do výstupů) | Klíč (data) | Česky (do výstupů) |
|---|---|---|---|
| `price` | cena | `comparison` | srovnává s konkurencí |
| `affordability` | nemáme rozpočet | `risk` | obava z rizika |
| `timing` | teď se to nehodí | `implementation` | obava z nasazení |
| `urgency` | není to priorita | `effort` | bude s tím moc práce |
| `trust_product` | nedůvěra v produkt | `past_failure` | špatná zkušenost z minula |
| `trust_company` | nedůvěra ve firmu | `need_to_think` | rozmyslím si to |
| `trust_salesperson` | nedůvěra v obchodníka | `information_request` | žádost o informace |
| `self_doubt` | „my to nezvládneme" | `polite_rejection` | zdvořilé odmítnutí |
| `fit` | nesedí to na nás | `hidden_objection` | skrytá námitka |
| `authority` | rozhoduje někdo jiný | `not_qualified` | není to náš zákazník |
| `partner_or_team` | musí to probrat s dalšími | | |

**Rozliš vždy:** skutečná námitka vs. podmínka vs. otázka vs. žádost o informaci vs. vyhýbavá odpověď vs. zdvořilé odmítnutí vs. nevhodnost nabídky. „Rozmyslím si to" je nejčastěji `hidden_objection` — najdi, co je pod tím (obvykle díra v jedné z Three Tens).

## Buying signals (kupní signály)
Otázky na implementaci / termíny / „jak by to u nás fungovalo" · přechod z „jestli" na „jak" · řeší detail místo principu · ptá se na reference/záruky · sám dopočítává návratnost · zapojuje partnera/tým do rozhodnutí. Signál = pobídka k transition/close, ne k další prezentaci.

## Failure patterns (opakující se chyby obchodníka)
- `premature_pitch` — nabídka před dokončenou discovery
- `feature_dumping` — výčet funkcí místo výsledku (porušení „sell the vacation")
- `pain_named_by_rep` — obchodník pojmenuje dopad za zákazníka (zákazník si ho neuvěří)
- `logical_objection_fight` — argumentace proti námitce místo loopingu/reframe
- `no_next_step` — hovor končí bez konkrétního dalšího kroku s termínem
- `price_before_value` — cena dřív, než je postavená hodnota
- `line_lost` — zákazník převzal kontrolu, obchodník reaktivně následuje
- `wrong_objection_treated` — řeší povrchovou námitku, ne skutečnou
- `happy_ears` — slyší souhlas, který nezazněl; přeskočí qualification
- `manipulation` — viz `ethics.md` (penalizuje se tvrdě)

## Typy znalostí (pro záznamy v KB)
`principle` · `framework` · `heuristic` · `signal` · `failure_pattern` · `objection_pattern` · `coaching_rule` · `scoring_rule` · `ethical_constraint` · `example`
