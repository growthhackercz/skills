# Anti-slop — pravidla lidského textu

Závazný průchod po dopsání článku, PŘED self-auditem. AI text se pozná podle vzorců níže — každý výskyt najdi a přepiš. Cíl: čtenář neřeší, kdo článek napsal, ale co se z něj dozvěděl.

## 1) Zakázaný slovník (najdi a nahraď)

| Klišé | Čím nahradit |
|---|---|
| „v dnešní (digitální / uspěchané / moderní) době" | konkrétní kontext, nebo smazat — věta bez toho funguje |
| „pojďme se podívat / pojďme se ponořit" | rovnou k věci, bez ohlašování |
| „je důležité si uvědomit / zmínit / poznamenat" | řekni fakt rovnou, bez předehry |
| „v neposlední řadě" | „a" — nebo přeskládej pořadí |
| „ať už jste X, nebo Y" | vyber JEDNO publikum — článek má segment, ne všechny |
| „nejen X, ale i Y" (víc než 1× v článku) | přeformulovat — jde o nadužívaný vzorec |
| „klíčový / zásadní / esenciální" (víc než 2× v článku) | konkrétní důvod, PROČ na tom záleží |
| „revoluční / přelomový / game-changer" | co přesně se změní, v číslech |
| „posunout na další úroveň" | měřitelný výsledek |
| „rychle a efektivně", „snadno a jednoduše" (prázdné dvojice) | jedno slovo — nebo konkrét, jak rychle |
| „v tomto článku se dozvíte / zjistíte" | řeší answer-first úvod — odpověz rovnou |
| „stojí za zmínku", „není žádným tajemstvím", „jak jsme si už řekli" | smazat — vata |
| „Závěrem / Na závěr / Shrnutí" jako nadpis | zakázané (viz workflow) — závěr nese další krok |

## 2) Rytmus a stavba

- **Střídej délky vět.** Po dlouhém souvětí krátká věta. Tři věty podobné délky za sebou = přepiš jednu.
- **Odstavce různě dlouhé** (1–4 věty). Uniformní bloky stejné výšky jsou strojový vzorec.
- **Max jedna trojice-výčet („X, Y a Z") na sekci.** AI dává trojici do každého odstavce — člověk ne.
- **Odrážky jen tam, kde je chce playbook typu.** Souvislý text nenahrazuj seznamem; seznam není odstavec.
- **Ne každá H2 otázka.** Otázkové nadpisy jen tam, kde odpovídají reálným dotazům; jinak tvrzení.

## 3) Typografické tely

- **Dlouhá pomlčka „—" střídmě**: orientačně max 1 na 300 slov. Většinou stačí čárka, dvojtečka, závorka nebo tečka a kratší věta.
- **Žádné emoji v článku**, pokud je brand hlas výslovně nechce.
- **Tučné jen pro klíčová tvrzení** — ne v každém odstavci, jinak nezvýrazňuje nic.

## 4) Konkrétnost povinná

- Každé obecné tvrzení doprovoď konkrétem: číslo, situace, nástroj, příklad z oboru klienta. **Obecná věta bez konkrétu = škrtni, nebo doplň konkrét.**
- Zákaz „mnoho firem", „většina lidí", „studie ukazují" bez zdroje — buď číslo se jmenovaným zdrojem, nebo konkrétní situace („e-shop s 500 objednávkami měsíčně…").
- Prázdná superlativa („nejlepší řešení na trhu") nahraď ověřitelným tvrzením.

## 5) Test čtení nahlas

- Projdi si úvod a závěr, jako bys je říkal zákazníkovi do očí. Věta, kterou bys nahlas nikdy neřekl, se přepisuje mluvenou formulací.
- Slovník ber z brandDNA a z reálného jazyka publika (research brief od content-scout) — ne z marketingové češtiny.

## Průchod (pořadí)

1. Najdi a nahraď zakázaný slovník (sekce 1).
2. Zkontroluj rytmus: délky vět, odstavce, trojice, odrážky (sekce 2).
3. Pomlčky, emoji, tučné (sekce 3).
4. Obecná tvrzení → konkréty (sekce 4).
5. Úvod a závěr nahlas (sekce 5).

Teprve potom self-audit ze SKILL.md.

> Pozn. pro fleet build: tento soubor je kanonický pro celou content rodinu — při buildu image kopírovat stejnou verzi i do `social-post-writer/references/` (stejný vzor jako `brand-style.md`).
