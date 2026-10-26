# Týdenní report — šablona (anti-reporter pravidla)

Report VŽDY začíná vykonanými čísly (co tým reálně udělal), nikdy plánem. Piš vykáním, stručně, bez žargonu. Návrhy formuluj tak, aby se daly schválit jedním slovem.

---

```markdown
# Prodejní týden <od–do>

## Co se vykonalo
- Osloveno: <N> kontaktů · odpovědí: <N> · schůzek domluveno: <N> · proběhlo: <N>
- Nové obchody: <N> (<Kč>) · vyhráno: <N> (<Kč>) · prohráno: <N> (důvody: <top 2>)
- Úkoly týmu: <N> zadaných, <N> dokončených (přípravy na jednání, follow-upy, briefy)

## Kde jsme vůči cíli
- Měsíční cíl: <Kč> → aktuálně <X %> (<Kč>)
- Forecast do konce měsíce: <Kč> (hodnota × pravděpodobnost per fáze, per pipeline)
- <1 věta: co forecast táhne nahoru/dolů>

## Co si zaslouží pozornost
- <max 3 body: trčící dealy, výpadek SLA, výrazná událost>

## Návrhy ke schválení
1. **Reaktivační vlna:** <segment, počet kontaktů, navrhovaný úhel> — po odsouhlasení připravím kohortu a exact plán; provedení vyžaduje samostatný souhlas s jeho SHA.
2. **Prospecting kampaň:** <market, produkt, ICP, cílový počet> — po odsouhlasení založím jeden CSO Prospector task; ten před sběrem ukáže ICP a source plán ke schválení.
3. **<další návrh>** — odpovězte „ano/ne".

⏳ Čeká z minula: <návrhy bez odpovědi — pokud 2+ týdny, výslovně upozorni, že engine v této části stojí>
```

---

Zásady:
- Čísla ber z denních souhrnů a snapshotu (skript), ne z paměti.
- Řádek „Úkoly týmu": zadané spočítej z dispatch-logu (`.strategist-state/dispatch-log.md`), stavy ověř přes `GET /api/tasks?assigned_to=cso` (done / v review / failed za týden). Failed jmenovitě do „Co si zaslouží pozornost".
- Zlepšení v procentech per vlna uvádět jen orientačně (malé vzorky) — trend, ne věda.
- Žádný návrh ≠ žádná sekce — sekci Návrhy vynech, když není co schvalovat.
