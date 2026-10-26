# FIO API — Rate limit

## Pravidlo

> **Jeden API token smí volat FIO API maximálně 1× za 30 sekund.**

Při porušení limitu FIO vrací **HTTP 409 Conflict**. Není to chyba klienta ani serveru — je to záměrné omezení.

## Co počítá jako „1 volání"

Každý HTTP request na `fioapi.fio.cz` se počítá, ať voláš:

- `/periods/`
- `/last/`
- `/by-id/`
- `/lastStatement/`
- `/set-last-date/`
- `/set-last-id/`

Limit je **per token**, ne per endpoint. Tj. pokud zavoláš `/set-last-date/` a hned `/last/`, druhý request dostane 409.

## Retry strategie (implementováno v `fio_get.py`)

Helper `scripts/fio_get.py` automaticky řeší HTTP 409 takto:

```
1. pokus → request hned
2. pokus → po 30 s
3. pokus → po 60 s
4. pokus → po 120 s
```

Celkem až **3 retry**, kumulativně až ~3.5 minuty čekání. Pokud se ani po 4 pokusech nepovede, helper vyhodí `RuntimeError`.

## Praktické důsledky pro agenta

### Pomalé operace

- 1 request = ~okamžitě (response time obvykle 1–5 s).
- 5 sekvenčních requestů = **2+ minuty** reálného času.
- Plánuj pipeline tak, abys minimalizoval počet volání.

### Jak omezit počet volání

**❌ Špatně (5 volání = 2 minuty):**
```
1. /set-last-date/  (reset zarážky)
2. /last/           (stáhnout od zarážky)
3. /set-last-date/  (znovu reset)
4. /last/
5. /lastStatement/  (kontrola)
```

**✅ Lépe (1 volání = několik sekund):**
```
1. /periods/{datum-od}/{datum-do}/  (stáhne všechno najednou)
```

### Velká období

Pro období > 1 rok zvaž **rozdělení na čtvrtletí**:
- 4× `/periods/` (~2 minuty reálného času).
- Menší response per request (robustnější na timeout / paměť).
- Snazší debug pokud něco selže.

### Paralelizace

**Nelze!** Stejný token nemůže běžet paralelně. Pokud bys spustil 2 requesty současně, druhý dostane 409.

Pokud má klient víc účtů, **každý má vlastní token** → ty lze volat paralelně (ale to není v MVP scope tohoto skillu).

## Co dělat při častém 409

Pokud agent dostává 409 i po retry:

1. Zkontroluj, jestli neběží **jiný proces** se stejným tokenem (cron job, jiný openclaw skill, klient v IB).
2. Zkontroluj, jestli v jedné session nevoláš `fio_get.py` opakovaně bez čekání.
3. Pokud běží watcher / cron — uprav interval na **≥ 1 minuta** (s rezervou).

## HTTP 429 vs 409

FIO **nepoužívá** standardní HTTP 429 Too Many Requests. Používá **409 Conflict**, což je nestandardní, ale je to fakt. `fio_get.py` to ošetřuje správně.
