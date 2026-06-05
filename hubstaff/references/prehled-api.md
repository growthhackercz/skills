# Přehled Hubstaff API v2

Tento dokument vysvětluje, **co Hubstaff API umí**, jak je strukturované a na co si dát pozor. Slouží agentovi jako orientační mapa — pro konkrétní příkazy a parametry koukni do `prikazy.md`, pro detail jednotlivých polí v odpovědích do `endpointy/`.

## Architektura ve zkratce

Hubstaff API v2 je REST. Adresa: `https://api.hubstaff.com/v2/`. Vrací výhradně JSON. Vyžaduje HTTPS.

Každý požadavek nese hlavičku `Authorization: Bearer <access_token>`. Access token získá klient výměnou Personal Access Tokenu (PAT) na endpointu `https://account.hubstaff.com/access_tokens`. Tahle výměna probíhá automaticky uvnitř skillu — vy se staráte jen o PAT (viz `nastaveni-pat.md`).

## Hlavní zdroje dat (resources)

Hubstaff modeluje práci kolem těchto entit:

| Resource | Co reprezentuje |
|---|---|
| **Organization** | Firma / účet. Většina klientů má jednu organizaci. |
| **Member** | Zaměstnanec / spolupracovník v organizaci. |
| **Client** | Externí subjekt, pro kterého se dělá práce (CRM-like entita). Projekty se k němu navazují. |
| **Team** | Logické seskupení členů (např. „Vývoj", „Obchod"). |
| **Project** | Projekt s rozpočtem, ke kterému jsou přiřazeni členové a (volitelně) klient. |
| **Task** | Konkrétní úkol pod projektem. |
| **Activity** | 10minutový blok sledovaného času s aktivitou v procentech (klávesnice + myš). Toto je nejjemnější granulace dat. |
| **Screenshot** | Snímek obrazovky pořízený automaticky během sledovaného času (0–3 snímky každých 10 min). |
| **Application** | Aplikace, ve které člen pracoval (název + čas). |
| **URL** | Webová stránka, kterou člen navštívil během sledovaného času. |
| **Shift** | Naplánovaná směna (rozvrh). |
| **Work break** | Přestávka (start, konec, důvod). |
| **Time entry** | Souhrnný úsek práce (od–do, projekt, úkol, poznámka, manuálně přidané vs. tracked). Pro „kolik kdo skutečně vykázal" preferujte před `activities`. |
| **Time off** | Žádost o volno (dovolená, nemoc, osobní volno) — s typem politiky a stavem schválení. |

## Časové okno

Velká část endpointů (activities, screenshots, apps, urls, shifts, breaks) vyžaduje **začátek a konec** období. Hubstaff očekává **ISO 8601 timestamp v UTC** (např. `2026-05-19T00:00:00Z`).

Skill přijímá zkrácený formát `YYYY-MM-DD` a doplňuje si časy automaticky:
- `--from 2026-05-19` → `2026-05-19T00:00:00Z`
- `--to 2026-05-19` → `2026-05-19T23:59:59Z` (jednodenní okno pokrývá celý den)

**Pozor na časové zóny.** Hubstaff ukládá vše v UTC. Pokud váš tým pracuje v české zóně, půlnoc UTC ≠ půlnoc Praha (rozdíl 1–2 hodiny). Pro „pondělí v Praze" je přesnější okno např. `2026-05-19T22:00:00Z` až `2026-05-20T22:00:00Z` (létní čas). Orchestrující skill nad `hubstaff` by měl zónu řešit explicitně, pokud na ní záleží.

## Stránkování

Hubstaff stránkuje výsledky. Klient skillu **automaticky sbírá všechny stránky** a vrátí jeden konsolidovaný seznam. Limit je 50 stránek (přepsatelný přes `--max-pages N`). Pokud narazíte na limit, zužte časové okno nebo filtry (`--member`, `--project`).

Při paginaci se používá kurzor `next_page_start_id` — to se děje uvnitř, nemusíte se tím zabývat.

## Filtry

Většina endpointů s časovým oknem přijímá:
- `--member 12345` — omezí na konkrétního člena (lze opakovat: `--member 1 --member 2`)
- `--project 678` — omezí na konkrétní projekt (lze opakovat)

Členové a projekty se zadávají **přes ID**, ne přes jméno. ID získáte z `hubstaff members` a `hubstaff projects`.

## Oprávnění

Token vidí jen data, na která má sám člen (vlastník PAT) v Hubstaffu právo. Praktický dopad:

- **Majitel / Manažer** vidí všechny členy, projekty, aktivity celé organizace.
- **Běžný User** vidí typicky jen svá data.
- Některé endpointy (top apps, top urls) vyžadují plán **Hubstaff Premium** nebo vyšší — pokud máte starší plán, dostanete prázdný výsledek nebo HTTP 403.

## Rate-limit

Hubstaff povoluje **1000 požadavků za hodinu** na jednu aplikaci (= na jeden PAT). Klient skillu při HTTP 429 automaticky čeká a opakuje (exponenciální backoff). Pokud děláte hodně dotazů (např. roční aktivity celého týmu), buďte trpěliví — může to trvat několik minut.

Tipy, jak nepřekročit limit:
- Stáhněte si data za delší okno **jednou** (jako CSV / JSON do souboru) a dotazujte se na uložený výstup, ne na API znovu a znovu.
- Filtrujte na úrovni API (`--member`, `--project`), nikoli klient-side.
- Pro pravidelné běhy (cron) plánujte přes orchestrující skill, ne přes opakované volání `hubstaff`.

## Co API NEUMÍ (verze 1.0 skillu)

- **Změnu dat** — skill je striktně read-only. Přidávat členy, zakládat projekty, upravovat time entries → mimo rozsah.
- **Stahování snímků obrazovky** — vrací jen metadata (čas, URL na obrázek). Pokud chcete snímek vidět, otevřete odkaz v Hubstaffu.
- **Webhooks** — pro real-time eventy (nová time entry, opožděný start) Hubstaff podporuje webhooks, ale skill je nenastavuje. Pro pravidelný polling stačí cron na orchestrujícím skillu.
- **Výplaty (payroll)** — endpoint pro výplaty existuje, ale do verze 1.0 ho nezabaluje. Bude v samostatném `hubstaff-payroll` skillu, pokud bude poptávka.

## Když něco selže

| Chybová hláška | Co to znamená | Co dělat |
|---|---|---|
| `Chybí HUBSTAFF_PAT v prostředí.` | Token nebyl nastaven. | Postupujte podle `nastaveni-pat.md`. |
| `Výměna tokenu selhala (HTTP 401)` | PAT je neplatný / zneplatněný. | Vygenerujte v Hubstaffu nový token a aktualizujte `HUBSTAFF_PAT`. |
| `HTTP 403 při …` | Token nemá oprávnění na daný endpoint nebo plán Hubstaffu nepokrývá funkci. | Použijte token majitele / upgradujte plán Hubstaffu. |
| `Překročen limit 50 stránek.` | Dotaz vrátil moc dat. | Zužte časové okno nebo přidejte filtr `--member` / `--project`, případně zvyšte `--max-pages`. |
| `Hubstaff API nedostupné po N pokusech` | Síť nebo Hubstaff má výpadek. | Zkuste znovu za pár minut. Pokud výpadek trvá, zkontrolujte <https://status.hubstaff.com>. |
