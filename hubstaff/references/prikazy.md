# Katalog CLI příkazů skillu `hubstaff`

Kompletní seznam toho, co skill umí. Pro každý příkaz najdeš syntax, parametry, příklady a zkrácenou ukázku výstupu. Pro popis polí v odpovědích koukni do `endpointy/<resource>.md`.

**Obecná syntaxe:**

```
python3 {baseDir}/scripts/hubstaff.py <command> [--org ID] [filtry] [--format json|csv|table] [--max-pages N] [--columns ...] [--limit N]
```

**Společné parametry pro všechny příkazy (kromě `auth-check`):**

| Parametr | Výchozí | Popis |
|---|---|---|
| `--format {json,csv,table}` | `json` | Formát výstupu. `json` pro další zpracování, `csv` pro export, `table` pro výpis do chatu klientovi. |
| `--max-pages N` | `50` | Limit stránek při paginaci. Pojistka proti rate-limitu. Při překročení skill skončí chybou. |
| `--columns sloupec1,sloupec2,…` | (všechny) | Pro `csv` / `table` omezí vypsané sloupce. Tečka v názvu (`time_slot.start`) zobrazí vnořené pole. |
| `--limit N` | (vše) | Klient-side omezení počtu vrácených záznamů (po stažení a paginaci). |

**Specifické pro endpointy s časovým oknem:**

| Parametr | Povinný | Popis |
|---|---|---|
| `--from YYYY-MM-DD` | ano | Začátek období (lze i plný ISO 8601). |
| `--to YYYY-MM-DD` | ano | Konec období. |
| `--member ID` | ne | Filtr na člena (lze opakovat). |
| `--project ID` | ne | Filtr na projekt (lze opakovat). |

---

## `auth-check` — ověření PAT

Rychlá kontrola, že `HUBSTAFF_PAT` funguje a token má přístup k aspoň jedné organizaci.

```bash
python3 hubstaff.py auth-check
```

Výstup:
```
Přihlášen jako jan.novak@firma.cz (Jan Novák). Výchozí organizace ID: 123456.
```

---

## `me` — identita vlastníka tokenu

```bash
python3 hubstaff.py me --format json
```

Vrátí podrobnosti o uživateli, kterému patří PAT (id, jméno, email, timezone, role).

---

## `orgs` — výpis organizací

```bash
python3 hubstaff.py orgs --format table --columns id,name,status
```

Typicky vrací 1 organizaci. Pokud máte přístup k víc, tady je uvidíte.

---

## `members` — členové organizace

```bash
python3 hubstaff.py members --format table --columns id,name,email,status,role
```

S `--org ID` explicitně cílí na konkrétní organizaci (jinak první přístupná).

Detail polí: `endpointy/members.md`.

---

## `projects` — projekty organizace

```bash
python3 hubstaff.py projects --format table --columns id,name,status,budget.type,budget.budget
```

Vrací i informace o rozpočtech (`budget.type` = `hours` nebo `money`, `budget.budget` = naplánovaná hodnota).

Detail polí: `endpointy/projects.md`.

---

## `clients` — klienti organizace

Externí subjekty (firmy / osoby), pro které organizace pracuje. Projekty se k nim navazují přes `client_id`.

```bash
python3 hubstaff.py clients --format table --columns id,name,status,billing_email
```

Detail polí: `endpointy/clients.md`.

---

## `teams` — týmy organizace

Logická seskupení členů (např. „Vývoj", „Obchod", „Podpora").

```bash
python3 hubstaff.py teams --format table --columns id,name,status,members
```

Detail polí: `endpointy/teams.md`.

---

## `tasks` — úkoly organizace

Úkoly pod projekty (drobnější jednotky práce). Bez filtru vrací všechny úkoly organizace — pro velké klienty raději filtrujte na projekt.

```bash
# Všechny úkoly konkrétního projektu
python3 hubstaff.py tasks --project 4567 --format table --columns id,summary,status,due_at,assignees
```

Detail polí: `endpointy/tasks.md`.

---

## `activities` — aktivita v 10-min blocích

Klíčový endpoint pro monitorování. Vrací jednotlivé 10minutové bloky se zaznamenanou aktivitou (procenta klávesnice + myš), přiřazením k projektu / úkolu a délkou sledovaného času v bloku.

```bash
# Celý tým za týden, tabulka do chatu
python3 hubstaff.py activities --from 2026-05-11 --to 2026-05-17 \
    --format table --columns time_slot.start,user_id,project_id,activity,tracked

# Jeden člen za 14 dní jako JSON pro další zpracování
python3 hubstaff.py activities --member 12345 --from 2026-05-05 --to 2026-05-19

# CSV export pro Excel / BI
python3 hubstaff.py activities --from 2026-05-01 --to 2026-05-31 --format csv > /tmp/aktivity-kveten.csv
```

Detail polí (vč. vysvětlení `activity` v procentech): `endpointy/activities.md`.

**Pozor:** roční aktivity celého týmu mohou narazit na rate-limit (1000 req/h). Pro dlouhá období preferujte stažení v dávkách po měsících.

---

## `screenshots` — metadata snímků obrazovky

Vrací **pouze metadata** (kdy snímek vznikl, ID, URL na obrázek v Hubstaffu). Skill obrázky **nestahuje** — pokud klient chce snímek vidět, dejte mu link.

```bash
python3 hubstaff.py screenshots --from 2026-05-18 --to 2026-05-18 \
    --member 12345 --format table --columns id,time_slot,url
```

Detail polí: `endpointy/screenshots.md`.

---

## `apps` — top aplikace

Které aplikace člen používal a kolik času v nich. Vyžaduje plán Hubstaffu, který má app tracking zapnutý.

```bash
python3 hubstaff.py apps --from 2026-05-11 --to 2026-05-17 \
    --member 12345 --limit 10 --format table
```

Detail polí: `endpointy/applications.md`.

---

## `urls` — top URL

Které weby člen navštívil. Stejná omezení jako `apps`.

```bash
python3 hubstaff.py urls --from 2026-05-11 --to 2026-05-17 \
    --member 12345 --limit 10 --format table
```

Detail polí: `endpointy/urls.md`.

---

## `shifts` — plánované směny

Naplánované směny pro členy (rozvrh). Vhodné porovnat s `activities` pro detekci zameškaných / opožděných směn.

```bash
python3 hubstaff.py shifts --from 2026-05-11 --to 2026-05-17 \
    --format table --columns id,user_id,starts_at,ends_at,job_site_id
```

Detail polí: `endpointy/shifts.md`.

---

## `breaks` — přestávky

Kdy si členové dávali přestávky a jak dlouhé. Vrací endpoint `work_breaks` Hubstaffu.

```bash
python3 hubstaff.py breaks --from 2026-05-11 --to 2026-05-17 \
    --format table --columns id,user_id,starts_at,ends_at,duration
```

Detail polí: `endpointy/work-breaks.md`.

---

## `time-entries` — souhrnné časové záznamy

Klasické „od–do" úseky práce, **vč. ručně přidaných hodin** (`manual: true`). Pro „kolik kdo skutečně vykázal" preferujte tento endpoint před `activities` (které neukazují ruční hodiny).

```bash
# Souhrnné záznamy týmu za týden, CSV
python3 hubstaff.py time-entries --from 2026-05-11 --to 2026-05-17 --format csv

# Jen jeden člen, vč. poznámek
python3 hubstaff.py time-entries --member 12345 --from 2026-05-11 --to 2026-05-17 \
    --format table --columns starts_at,ends_at,tracked,project_id,manual,note
```

Detail polí (rozdíl proti `activities`): `endpointy/time-entries.md`.

---

## `time-offs` — žádosti o volno

Dovolená, nemoc, osobní volno, neplacené volno — s typem politiky a stavem schválení.

```bash
# Kdo má v daný měsíc volno
python3 hubstaff.py time-offs --from 2026-05-01 --to 2026-05-31 \
    --format table --columns user_id,policy_name,start_date,end_date,status
```

Detail polí: `endpointy/time-offs.md`.

---

## Vzorové úlohy a doporučená kombinace příkazů

Tyto úlohy obvykle řeší orchestrující skill, ale dobré vědět, co se k čemu hodí:

**„Kolik hodin tým odpracoval včera?"**
```bash
python3 hubstaff.py activities --from 2026-05-18 --to 2026-05-18 --format json
```
Orchestrace agreguje `tracked` přes všechny záznamy.

**„Kdo měl včera nízkou aktivitu (pod 30 %)?"**
```bash
python3 hubstaff.py activities --from 2026-05-18 --to 2026-05-18 --format json
python3 hubstaff.py members --format json
```
Orchestrace spočítá průměr `activity` per `user_id`, propojí se jmény z `members`, vyfiltruje pod 30 %.

**„Kdo zaspal naplánovanou směnu minulý týden?"**
```bash
python3 hubstaff.py shifts --from 2026-05-11 --to 2026-05-17 --format json
python3 hubstaff.py activities --from 2026-05-11 --to 2026-05-17 --format json
```
Orchestrace pro každou směnu zkontroluje, jestli v jejím časovém okně existuje aspoň jedna aktivita stejného člena.

**„Které projekty přepalují rozpočet?"**
```bash
python3 hubstaff.py projects --format json
python3 hubstaff.py time-entries --from 2026-01-01 --to 2026-05-19 --format json
```
Orchestrace agreguje `tracked` per `project_id` (z `time-entries`, vč. ručních hodin) a porovná s `budget.budget`.

**„Kdo má v daný týden volno?"**
```bash
python3 hubstaff.py time-offs --from 2026-05-11 --to 2026-05-17 --format json
```
Filtr `status: approved` v orchestraci. Hodí se před vystavením upozornění typu „nízká aktivita" — pokud má člen schválené volno, není to anomálie.

**„Co dělal Honza minulý týden?"**

Nejdřív najdi ID:
```bash
python3 hubstaff.py members --format table --columns id,name,email
```
Pak:
```bash
python3 hubstaff.py activities --member 12345 --from 2026-05-11 --to 2026-05-17 --format table
python3 hubstaff.py apps --member 12345 --from 2026-05-11 --to 2026-05-17 --limit 10
python3 hubstaff.py urls --member 12345 --from 2026-05-11 --to 2026-05-17 --limit 10
```
