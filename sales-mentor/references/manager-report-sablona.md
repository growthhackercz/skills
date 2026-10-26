# Report manažerovi — denní a týdenní

**Tenhle report = přehled VÝKONU LIDÍ** (kdo je silný/slabý, koho koučovat), ne byznys/playbook. Je to jen mentorovy scorecardy sečtené za tým — stejná data, jiný čtenář. **Byznys/playbook učení (opakující se námitky, funnel) dělá `sales-analytik`**, ne mentor. Manažer dostává oba reporty, ale jsou to jiné věci: mentor = tabulka výkonu lidí, analytik = co změnit v metodě. Žádné zdvojení.

Podklad vyrábí `mentor_report.py`; model z něj složí finální zprávu. Čte **jen scorecardy** (ne přepisy). Podklad dodává: čísla, trend vs. minulé období, nejslabší kategorii, časté příčiny, obchodníky s průměrem a trendem. Silné stránky a osobní focus doplní model ze scorecardů.

## Denní přehled (mentor-daily)
Krátký, akční. Manažer ho přečte za minutu.
1. **Čísla dne:** kolik hovorů ohodnoceno · průměrné skóre · trend vs. včera.
2. **Nejslabší kategorie týmu** dnes (kam mířit koučink).
3. **Kdo potřebuje pozornost:** obchodník s nejnižším průměrem nebo největším propadem, jednou větou proč.
4. **Červená vlajka** (jen když je): detekovaná manipulace nebo skóre pod 40.

## Týdenní shrnutí (mentor-weekly)
**Manažerovi:**
1. Čísla týdne + trend vs. minulý týden.
2. **Tabulka obchodníků:** průměr, počet hovorů, trend, nejslabší kategorie.
3. Kdo roste a kdo klesá + doporučený zásah (konkrétní dovednost k procvičení per obchodník).
4. Systémový vzorec, pokud stejná díra padá napříč týmem: označ ho v souhrnu jako podnět pro `sales-analytik` (ten ho zachytí přes scorecardy, mentor sám playbook neřeší).

**Každému obchodníkovi (osobní):**
- jeho průměr + trend · jedna silná stránka týdne · **jedna dovednost na příští týden** + cvičení.

## Zásady
- Vykání. Konkrétní čísla, ne obecné fráze.
- Manažerovi = agregát a řízení; obchodníkovi = osobní rozvoj. Nemíchat.
- Reporty se do CRM nezapisují; mentor neposouvá dealy, jen hodnotí a reportuje. Doručení reportu = deliverable úlohy + e-mail příjemcům z §1. (Per-call pointer-poznámka na kontakt je jiná věc, řeší ji krok 6 v SKILL.)
- Batch je odpojený od per-call: report čte hotové scorecardy, nehodnotí znovu.
