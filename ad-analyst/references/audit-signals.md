# Live audit — signály, prahy, zdraví měření

Read-only audit běžícího účtu. **Prahy jsou heuristiky pro první signál, ne automatické rozhodnutí.** Nikdy neměň budget/kampaň automaticky. Převzato z reálného `meta-ads-reporting` + `meta-pixel-capi-audit`.

## Nejdřív: typ výsledku
Detekuj **lead vs purchase** (jinak se CPA/ROAS čte špatně). Podle toho volíš metriky a prahy.

## Signály, co reálně řídí verdikt (zbytek je kontext)
- **Spend** — Meta tlačí rozpočet do reklamy = funguje (algoritmus jí věří).
- **CPA / ROAS** — děláš na tom peníze? Hlavní verdikt.
- **Frequency 5–7 / 30 dní** = vyčerpaný bottom-funnel pool = **čas posunout awareness level** (signál pro `ad-strategist`, ne „udělej novou reklamu").

## Prahy (default heuristiky)
| Signál | Práh | Poznámka |
|---|---:|---|
| Bleeder CTR | < 1,0 % | kontroluj zároveň spend a objective |
| High frequency | > 3,5 | u malého publika může být normální, ale fatigue risk |
| Fatigue CTR drop | > 20 % | porovnávej proti předchozímu období stejné délky |
| CPC spike | > 30 % | vyžaduje spend nad noise threshold |
| CPM spike | > 25 % | kontroluj sezónnost + audience změny |
| Daily spend noise | < 50 měny | pod tím netvrď silnou anomálii |

Doporučení k budgetům **zůstávají read-only**. Nikdy neměň budget automaticky.

## Zdraví měření (tracking audit — před škálováním)
Když reporting naznačí slabý signál, **audit PŘED škálovacím doporučením** (ne domněnka):
- **Missing events** (chybí klíčové konverzní eventy)
- **Nízké EMQ** (Event Match Quality — slabá kvalita párování)
- **Dedup / double-counting** (pixel + CAPI počítají dvakrát)
- **Pixel / CAPI problém** (nekonzistence serverového a browser trackingu)
→ Bez zdravého trackingu jsou výkonová čísla nespolehlivá → nejdřív spravit měření, pak škálovat.

## Kaskáda zdrojů
1. **Nativní Meta** (`meta` CLI → `meta_report.py`): winners/bleeders/frequency/fatigue (fatigue vyžaduje dvě období, viz output-contract). Kde runtime nabízí navíc (opportunity score, auction/ranking benchmarks), přiber jako kontext.
2. **GHL reporting** (Google/LinkedIn) — když není direct Meta.
→ **Degradace:** GHL nedá Meta fatigue/pixel data — poznamenej limit, neslibuj, co zdroj nedává.

## Fixy = vázané na peníze
Každé doporučení spoj s dopadem na peníze (wasted spend X/den · fatigue → posun awareness · missing event → ztracené konverze). Ne obecné „optimalizuj".
