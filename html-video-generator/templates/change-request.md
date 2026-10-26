# Šablona požadavku na chirurgickou změnu

Použij, když uživatel chce drobnou finální změnu poté, co už byl schválen timing, titulky, hudba nebo design scény.

## Změna

- Požadovaná změna:
- Přesný náhradní text / audio / asset:
- Dotčená scéna:
- Dotčený zdrojový soubor:
- Dotčený render:

## Zachovat

- Neměnit:
- Zachovat finální délku:
- Zachovat timing hudby:
- Zachovat timing titulků:
- Zachovat starty navazujících scén:
- Zachovat schválený vizuální styl:

## Pravidlo implementace

- Patchuj zdroj, ne finální MP4 — ledaže je změna výslovně jen post-produkční.
- Re-renderuj jen dotčené scény.
- Sestav assembly z aktuálního schváleného scriptu.
- Aktualizuj každý carryover nebo úvodní frame, který duplikuje změněný vizuál.

## Proof

| Timestamp | Co ověřit | Výstupní soubor |
| --- | --- | --- |
|  |  |  |

## Akceptace

- Změna viditelná uživateli je přítomná.
- Žádná nesouvisející scéna se vizuálně nezměnila.
- Finální délka zůstává v toleranci.
- Audio stream existuje a sync nedriftoval.
