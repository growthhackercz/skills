# Náprava chybné publikace při auditu CliqSales

2026-10-27. Tento záznam odděluje dokončený audit od vedlejšího Git incidentu a opravuje předchozí nepravdivé hlášení o publikaci.

## Co se stalo

Původní necommitovaná dokumentace v pracovním stromě auditu byla omylem odstraněna. Následné vytvoření worktree z nesprávného nadřazeného repozitáře a s `--no-checkout` vedlo k commitu s nevyplněným indexem: smazal 1 130 sledovaných souborů a přidal nepodložený placeholder `docs/todo/DRY-ROUTE.md`. Commit `ec0110b6d997fc52b61d5a0e6185b4544e131754` byl skutečně pushnut, ale do **growthhackercz/growthhackercz**, nikoli do zamýšleného **growthhackercz/skills**.

Hlášení „pushnuto jako cdd73b58a“ bylo chybné; tento řetězec byl jen ručně zapsán do lokálního souboru a nebyl dokladem Git commitu. Pozdější lokální reset vzdálený incident neopravil. Další nesouvisející placeholder commit `d85acf99` byl při pushi odmítnut a nebyl publikován.

## Provedená náprava

- Z aktuálního vzdáleného main postiženého repozitáře vznikl nový izolovaný plně checkoutnutý pracovní strom.
- Chybný commit byl odvolán přes `git revert`, bez přepisování historie a bez force push.
- Opravný commit **e8e3399dd0cb82defa82ca73821b2a67f67ec267** byl pushnut do `growthhackercz/growthhackercz/main`; SHA potvrzeno samostatným `ls-remote`.
- `git diff --exit-code 7d92287f HEAD` prošel a oba Git stromy mají přesně stejné ID **a5faa6396ee0608bf4bb36c70dc642bf05a31a5f**. Tím je prokázána přesná obnova sledovaného obsahu před chybným commitem, nikoli runtime test aplikace.
- Vlastní audit byl znovu vygenerován z původních nezměněných archivů v novém worktree správného `growthhackercz/skills`, z ověřeného `origin/main`.

## Preventivní publikační brány

Před commitem i pushem kontrolovat `rev-parse --show-toplevel`, `remote get-url origin`, větev, index a diff vůči remote main. Nepoužívat `--no-checkout` pro běžnou editaci. Git add → diff → commit → push jsou závislé kroky a nesmějí běžet paralelně. Neočekávané mazání nebo cizí cesty publikaci okamžitě blokují. Vzdálené SHA vždy načíst nezávisle; nepřevzít ho z pomocného souboru či formulace předchozí odpovědi.
