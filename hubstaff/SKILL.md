---
name: hubstaff
description: Read-only wrapper nad Hubstaff API pro čtení času, aktivity, projektů, směn, členů a souvisejících reportovacích dat. Vrací JSON, CSV nebo tabulky; interpretaci a automatizaci dělá agent nebo nadřazený skill.
category: integrations
status: ready
version: "1.0"
publishedAt: "2026-05-20"
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":["HUBSTAFF_PAT"]},"primaryEnv":"HUBSTAFF_PAT","emoji":"⏱️"}}
---

# Hubstaff — wrapper API

Tenký integrační skill — dává agentovi přímý přístup k Hubstaff API v2. Sám nic neinterpretuje, neukládá zprávy, neplánuje běhy. Vrací data, ze kterých si orchestrující skill nebo agent poskládá, co potřebuje (týdenní přehled, upozornění na nízkou aktivitu, fakturaci dle hodin, BI export, ad-hoc dotaz).

## Kdy tenhle skill použít

Pokaždé, když potřebuješ z Hubstaffu **přečíst** cokoli — kolik hodin tým odpracoval, jaká byla aktivita, kdo měl naplánovanou směnu, jaké projekty jedou, top aplikace/URL člena, přestávky. Není to skill na výpočty ani na rozhodnutí — je to skill na získání dat.

## Kdy tenhle skill NEpoužívat

- Když máš data jen formátovat / spočítat / interpretovat — to si dělej sám nad získanými daty.
- Když chceš pravidelnou zprávu (denně, týdně) — naplánuj přes OpenClaw cron na úrovni orchestrujícího skillu, nikoli tady.
- Když chceš detekci odchylek (nízká aktivita, zameškaná směna, přepalování rozpočtu) — `hubstaff` ti vrátí surová data, pravidla aplikuje orchestrace.
- Když chceš v Hubstaffu cokoli **měnit** — verze 1.0 je čistě read-only.

## Workflow

1. **Pre-flight** (jen při prvním volání v session): pokud chybí proměnná `HUBSTAFF_PAT` v prostředí, zobraz uživateli návod z `{baseDir}/references/nastaveni-pat.md` a skonči. Jinak rychlé ověření: `python3 {baseDir}/scripts/hubstaff.py auth-check` (cachuje token, příště je instant).
2. **Vyber příkaz** podle toho, co potřebuješ. Kompletní katalog příkazů včetně parametrů a příkladů je v `{baseDir}/references/prikazy.md`.
3. **Pokud potřebuješ vědět, co znamenají jednotlivá pole** v odpovědi (např. jak se počítá `activity_percent`, co je `time_slot`, jak se liší `tracked` vs. `manual`) → načti odpovídající soubor v `{baseDir}/references/endpointy/`.
4. **Zavolej příkaz** přes shell:
   ```
   python3 {baseDir}/scripts/hubstaff.py <command> [options]
   ```
   Výchozí výstup je JSON (vhodný pro další zpracování). Pro výpis do chatu uživateli použij `--format table` (česká tabulka). Pro export do souboru použij `--format csv`.
5. **Vrať data** uživateli nebo nadřazenému skillu/agentovi. Žádné domýšlení čísel, žádné interpretace nad rámec toho, co uživatel chtěl.

## Příklady volání

```bash
# Ověření tokenu a výpis organizací
python3 {baseDir}/scripts/hubstaff.py auth-check
python3 {baseDir}/scripts/hubstaff.py orgs --format table

# Členové týmu jako tabulka do chatu
python3 {baseDir}/scripts/hubstaff.py members --format table --columns id,name,email,status

# Klienti, týmy, úkoly konkrétního projektu
python3 {baseDir}/scripts/hubstaff.py clients --format table
python3 {baseDir}/scripts/hubstaff.py teams --format table
python3 {baseDir}/scripts/hubstaff.py tasks --project 4567 --format table

# Souhrnné časové záznamy (vč. ručně přidaných hodin) za týden
python3 {baseDir}/scripts/hubstaff.py time-entries --from 2026-05-11 --to 2026-05-17 --format csv

# Žádosti o volno za měsíc (kdo má dovolenou v daném okně)
python3 {baseDir}/scripts/hubstaff.py time-offs --from 2026-05-01 --to 2026-05-31 --format table

# Aktivita celého týmu za minulý týden, CSV pro další zpracování
python3 {baseDir}/scripts/hubstaff.py activities --from 2026-05-11 --to 2026-05-17 --format csv

# Aktivita konkrétního člena za 14 dní v JSON
python3 {baseDir}/scripts/hubstaff.py activities --member 12345 --from 2026-05-05 --to 2026-05-19

# Pro detekci zameškaných směn si stáhni obě věci a porovnej v orchestraci:
python3 {baseDir}/scripts/hubstaff.py shifts --from 2026-05-11 --to 2026-05-17
python3 {baseDir}/scripts/hubstaff.py activities --from 2026-05-11 --to 2026-05-17

# Top aplikace člena za měsíc, jen 10 záznamů
python3 {baseDir}/scripts/hubstaff.py apps --member 12345 --from 2026-04-19 --to 2026-05-19 --limit 10
```

## Reference

- `{baseDir}/references/nastaveni-pat.md` — jak v Hubstaffu vytvořit Personal Access Token a kam ho nastavit do prostředí
- `{baseDir}/references/prehled-api.md` — high-level vysvětlení, co Hubstaff API v2 nabízí, jak fungují období, stránkování, oprávnění a limity
- `{baseDir}/references/prikazy.md` — kompletní katalog CLI příkazů: syntax, parametry, příklady, ukázky výstupu
- `{baseDir}/references/endpointy/` — popis jednotlivých resources (členové, projekty, aktivity, snímky, aplikace, URL, směny, přestávky): co znamenají pole, jak je interpretovat, na co si dát pozor

## Důležité poznámky

- **Read-only.** Skill neumí v Hubstaffu nic měnit. Pokud potřebuješ zápis (přidat člena, založit projekt), je to mimo rozsah verze 1.0.
- **Snímky obrazovky** (`screenshots` příkaz) vrací jen metadata (čas, ID, URL na obrázek v Hubstaffu) — žádné stahování obrázků na disk. Pokud uživatel chce konkrétní snímek vidět, dej mu odkaz na hubstaff.com.
- **Rate-limit:** Hubstaff povoluje 1000 požadavků/hod na aplikaci. Klient automaticky čeká při HTTP 429. U dotazů přes dlouhá období (např. roční aktivity) může běh trvat několik minut — preferuj kratší okna a agregaci v orchestraci.
- **Token cache:** access token se cachuje v `~/.openclaw/cache/hubstaff/token.json` (per workspace). Pokud klient mění PAT, smaž soubor — klient si po restartu vyžádá nový.
- **Vykání ve výstupech pro uživatele.** Pokud renderuješ data do chatu, mluv s klientem vykáním. Skill samotný (helpy v CLI) je v tykání-neutrální formě.
