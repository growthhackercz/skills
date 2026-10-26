# Tři režimy Ads Enginu + Autopilot smyčka

Jak `ad-strategist` pozná, **co** má klient udělat (1 reklama / kampaň / trvalý dohled), a jak reálně běží **Autopilot** — týdenní smyčka mezi `ad-analyst` (čte) a `ad-strategist` (rozhoduje), se 3 úrovněmi schvalování a kill-switchem. Čte to `ad-strategist` (rozpoznání režimu + brány) i `ad-analyst` (týdenní audit = motor Autopilotu).

> **Rozsah:** tenhle dokument definuje **logiku** smyčky (kdo co dělá, kdy se ptá, kdy zabíjí). Reálné **plánování** (týdenní spouštění jako opakovaný úkol v Command Center, cron, task lifecycle) = plánovací mašinérie Command Center, staví ji programátor při fleet deployi. Skill sám autopilota nerozjede na pozadí — popisuje, jak má běžet, a v každém běhu odpracuje jeden cyklus.

## Jak stratég pozná režim (ze zadání)
| Signál v zadání | Režim |
|---|---|
| „Udělej reklamu na X", „potřebuju banner / jeden vizuál" | **JEDNORÁZOVÝ** |
| „Naplánuj kampaň", „rozjeď mi reklamy na X", „chci víc variant / testovat úhly" | **KAMPAŇ** |
| „Hlídej mi reklamy", „ať se to samo optimalizuje", „starej se o účet" | **AUTOPILOT** |

Když je zadání nejednoznačné → **zeptej se** (jednorázovka × kampaň × trvalý dohled), neodhaduj nahoru. Vyšší režim = víc utraceného rozpočtu.

---

## Režim 1 — JEDNORÁZOVÝ
**Vstup:** jeden konkrétní požadavek (jedna reklama / vizuál / text).
**Co se stane:** zkrácený průchod (Krok 0 kontext → Krok 2 vybere 1 nosný úhel → Krok 3 formát → **Krok 4 route zkráceně** → Krok 5 zadá makerovi → Krok 6 plán). Bez rozsáhlé matice úhlů, bez A/B rozvětvení. (Krok 4 nevynechávej — Krok 6 potřebuje rozhodnutou route v `publishingTargets`.)
**Brána:** default **draft / PAUSED** — hotový výstup + dashboard, klient si spustí sám. Bez explicitní žádosti „rovnou spusť" se nepublikuje naživo.
**Výstup:** 1 reklama (copy + vizuál) + krátký dashboard.

## Režim 2 — KAMPAŇ
**Vstup:** „naplánuj / rozjeď kampaň".
**Co se stane:** plný průchod 7 kroků — signály (`ad-scout`, `ad-analyst`), matice úhlů (≥10 úhlů × awareness, `angle-os.md`), diverzita 5 os (persona × úhel × formát × herec × awareness), formátový mix (native + stealth), route × capability, zadání makerům (Anchor & Riff, ≥5 hook variant), `ad-plan.json`.
**Brána (klíčová):** publish je **vždy POZASTAVENÝ** (`draftOnly: true` / Meta `safeWriteStatus: PAUSED`). Klient dostane celou strategii + varianty ke schválení a **poslední slovo má on** — nic nejde naživo bez jeho kliknutí.
**Výstup:** `ad-strategy.md` + `ad-plan.json` + varianty (copy/vizuál) + naming `Persona_Angle_Format_Hook` (páteř učení).

## Režim 3 — AUTOPILOT
**Vstup:** „hlídej a optimalizuj".
**Co to je:** kampaň, která **žije** — každý týden se sama vyhodnotí a navrhne/provede optimalizaci, v mantinelech, které klient jednou schválil. Není to „spusť a zapomeň" — je to řízená smyčka s brzdami.
**Aktivace:** při zapnutí ověř, že existuje pravidelný týdenní úkol (Command Center „Týdenní vyhodnocení reklam"); když chybí, založ ho přes Plánovač. **Název úkolu musí začínat přesně „Týdenní vyhodnocení reklam"** — Control Center hlídá deklarované pravidelné úkoly podle tohoto prefixu (kontrakt `ad-strategist:autopilot-setup` + watchdog) a jinak pojmenovaný úkol nepočítá. Nepředstírej, že smyčka běží na pozadí, dokud úkol reálně neexistuje.

### Týdenní cyklus (jeden běh)
```
1. SBĚR      →  ad-analyst (read-only): týdenní audit účtu
2. DIAGNÓZA  →  ad-strategist: audit → seznam akcí, roztříděný do úrovní 1/2/3
3. ÚROVEŇ 1  →  provede se automaticky (reverzibilní, nulový nový spend)
4. ÚROVEŇ 2  →  oznámení klientovi + okno na veto → jinak provést
5. ÚROVEŇ 3  →  makery vyrobí PAUSED → ad-plan.json (draftOnly) → tvrdá brána (klient klikne)
6. KILL-SWITCH check (při každém běhu; denní strop řeš platformním limitem) → STOP → read-only
7. COMPOUNDING → vítězné bloky zpět (evergreen-ads.json + Angle Leaderboard)
```

### Tři úrovně schvalování (mantinely autonomie)
| Úroveň | Kdy | Co smí | Jak se ptá |
|---|---|---|---|
| **1 — Autonomní** | reverzibilní, **nulový nový spend** | pauza jasného bleederu (CTR < 1 % + wasted spend), označení fatigue/frequency, příprava návrhů, refresh v rámci **už schváleného** úhlu | jen **log** (klient vidí, co se stalo) |
| **2 — Oznámit a pokračovat** (měkká brána) | dopad na peníze, ale **v rámci schváleného stropu** | realokace rozpočtu mezi existující ad sety pod stropem, spuštění nové varianty **už schváleného** úhlu | **oznámení + časové okno na veto**; bez veta se provede |
| **3 — Tvrdá brána** | mění mantinely | **nový úhel/persona**, navýšení rozpočtu **nad strop**, nová platforma, škálování vítěze, nová kampaň | **PAUSED/draft → čeká na explicit „ano"** klienta |

Default při zapnutí Autopilotu: pokud klient neurčí jinak, jede se **konzervativně** — Úroveň 1 automaticky, Úroveň 2 s oknem, vše ostatní Úroveň 3. Klient si mantinely (strop rozpočtu, délka veto okna, co smí být Ú2 vs Ú3) nastaví při schválení kampaně.

**Kdo mutace vykonává:** zásahy Ú1/Ú2 na **existujících** entitách (pauza, rozpočet pod stropem, aktivace už schválené varianty) provádí `ad-strategist` **skrze publishery** v rámci mantinelů; `ad-analyst` zůstává read-only. Pravidlo „nové kampaně/reklamy vznikají výhradně PAUSED" platí pro **tvorbu nových** entit — ne pro reverzibilní úpravy existujících v Autopilotu. **Ú1 = jen rotace/re-use UŽ vyrobených assetů** (nula nového ad-spendu i FAL kreditů); jakákoli nová produkce u makerů = Ú2+.

**Kde mantinely žijí:** sekce `autopilot` v `ad-plan.json` kampaně — `budgetCap` · `vetoWindowHours` · `killSwitch:{cpaOverrunPct, dailyHardCap}` · `levelOverrides`. Když klient nic nenastaví, platí konzervativní defaulty výše. **Bez uložených mantinelů** týdenní běh nemá odkud číst → jeď jen Ú1 a vyžádej si nastavení.

### Kill-switch (tvrdý stop celého autopilota, ne jedné reklamy)
Autopilot se **sám zastaví** do read-only a upozorní člověka, když:
- **CPA / náklad překročí strop** o nastavené % (utrácí a nekonvertuje),
- **tracking je rozbitý** (pixel/CAPI down, kolaps EMQ, chybí konverzní eventy) → čísla nedůvěryhodná, nelze podle nich optimalizovat,
- **platforma flagne účet** (policy / zamítnutí / omezení),
- **denní spend anomálie** nad hard cap,
- **klient řekne stop**.
Protože skill běží 1× týdně, **denní** strop nastav jako **platformní limit** (Meta campaign spending limit) už při tvorbě kampaně — týdenní audit denní přestřelení sám nezachytí včas. Po killu autopilot **nečeká na další akce** — jen reportuje a čeká na člověka. (Zdraví měření = důvod #2; audit trackingu dělá `ad-analyst` **před** každým škálovacím doporučením — viz `ad-analyst/references/audit-signals.md`.)

### Handoff `ad-analyst` ↔ `ad-strategist`
- **`ad-analyst` (čte, nerozhoduje):** týdenní audit → `summary.json` (v `/documents/ads/reports/{datum}-{mode}/`, schéma `ad-analyst/references/output-contract.md`) — winners/bleeders/fatigue/frequency/tracking + fixy vázané na peníze. **Nikdy sám nemění budget/kampaň.**
- **`ad-strategist` (rozhoduje, neprodukuje):** přečte audit → mapuje na tahy:
  - **frequency 5–7 / 30 dní** → ne „nová reklama", ale **posun awareness level** (`angle-os.md`),
  - **bleeder** → pauza (Ú1) + rozhodnutí recyklovat/zabít,
  - **fatigue** → **compounding 3 tahy** (Frankenstein · stejný úhel do nových formátů · stejný scénář na 3 nové tvůrce),
  - **winner** → škálování = **Úroveň 3** (tvrdá brána).
- Produkci dělají **makery** (PAUSED), publikaci **publishery** až po bráně. Stratég ani analytik nikdy nepublikují ani nemění účet sami.

---

## Co Autopilot NIKDY nedělá (guardraily)
- **Nezvyšuje rozpočet nad strop bez Úrovně 3.** Žádný nový spend bez brány.
- **Nespouští nový úhel/platformu automaticky** — vždy tvrdá brána.
- **Neobchází kill-switch** — při rozbitém trackingu se neškáluje „naslepo".
- **Nepublikuje ručním Graph API curl** — jen přes publishery/helpery.
- Klient má **poslední slovo** a může kdykoli autopilot vypnout.
