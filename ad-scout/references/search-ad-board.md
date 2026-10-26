# Search Ad Board — spec (v1)

**Kdo platí za vaše zákazníky ve vyhledávání** na klíčové slovo → jejich reklamy k převzetí, slova, kde nakoupíte kliknutí levně, a plán na prvních 30 dní. Osa = **klíčové slovo s nákupním záměrem** („kreatin", „boxerské rukavice"), klient = zadavatel (jeho doména kvůli „jste/nejste v placeném bloku"). Rodina: Viral board = kreativa na téma, Competitor board = jedna značka, **Search board = aukce ve vyhledávání**.

## Sekce boardu (renderer `scripts/searchboard.py`)

1. **Kdo přihazuje** (bidders) — inzerenti z živého placeného bloku × ověření v registru Google (počet reklam + nejstarší běh); u top 3 `proc_nebezpecny`.
2. **Reklamy k převzetí** (cloneable_ads) — reálný inzerát (head/desc/sitelinky/dny běhu) + **klon přeložený na klienta** vedle.
3. **Mezera ve slovech** (keyword_gap) — slova s objemem/CPC, kde v placeném bloku nikdo není; semafor + poznámka.
4. **Landing stránky konkurence** (landing_gaps) — slib · cena viditelná? · výzva k akci · důvěryhodnost · **co chybí** + `landing_pointa`.
5. **Námět na advertorial** (advertorial_namet) — hotový návrh prodejního článku, na který povedou reklamy ze zelených slov; s kopírovatelným zadáním pro AI Marketéra.
6. **Semafor rozpočtu** (budget_semafor) — zelená (začněte) / oranžová (později) / červená (zatím ne) + obsah (informační dotazy) + příklad rozpočtu.
7. **Akční plán** (action_plan) — přesně 3 kroky s časováním.

## Workflow

```bash
# 1) VŽDY dry-run (odhad + STOP)
python3 {baseDir}/scripts/scout.py search-fetch "<slovo>" --market cz --client-domain <klient.cz> --dry-run
# 2) ostrý fetch (denní cache per slovo; --keywords "a;b" přidá vlastní dotazy)
python3 {baseDir}/scripts/scout.py search-fetch "<slovo>" --market cz --client-domain <klient.cz>
# 3) MODEL doplní sémantiku do search-report.json (viz níže)
# 4) render
python3 {baseDir}/scripts/scout.py search-render "<slovo>"
```

Run-dir: `/documents/ads/scout/keywords/<slug>/<datum>/` — `fetched.json` · `probes.json` · `search-report.json` (contract) · `search-ad-board.html`. Rebuild kostry z cache za 0 kreditů: `_rebuild` běží při `search-render` — **sémantiku modelu zachovává** (merge podle domain/kw).

**Zdroje + cena (~$0,15–0,25/slovo):** živý SERP s paid add-onem (`apify/google-search-scraper`, slovo + související dotazy + probe pokrytí) · **registr Google per inzerent** (portfolio top bidderů — ověření, jak dlouho a čím platí) · **keyword metriky** (objem/CPC/konkurence, chain `s-r/google-keywords` → fallbacky). Fallback chainy a env overrides: `references/data-sources.md`.

## Deterministika navíc (v1.1 — po kritice 2026-07-13)

- **Semafor + mezera = klasifikace podle POČTU inzerentů** (`_semafor`, `GAP_MAX_BIDDERS=4`): **0–2 = zelená** (mezera, levný vstup) · **3–4 = oranžová** (střední konkurence — pořád se vyplatí, jen dráž) · **5+ = červená** (velký nátlak; nátlak začíná u 5, NE u 3) · informační dotazy = **obsah** (video/článek, ne PPC). Nákupní long-tail (gap) klasifikuj podle jeho počtu; obecné head dotazy nikdy zelená (jeden snímek podceňuje nasycenou hlavu → min. oranžová). **Hlavní slovo oboru (`tema`) = VŽDY červená** (nejvíc kontestované, nejdražší klik — patří tam, i když ho jeden snímek podcenil). Červená NEZAKAZUJE inzerci — varuje „velká konkurence, se silnou nabídkou opatrně, ať nespálíte rozpočet". **Mezera (tabulka sekce 03) ukazuje zelená I oranžová slova** (0–4) s barevnou tečkou (🟢 volno / 🟡 střední) — bohatší krajina; 5+ jen v semaforu. Model smí přeřadit, ne vymýšlet. Stará chyba: zelená z probe dotazů → „kreatin" v „nakupujte hned"; a 3 inzerenti ≠ červená.
- **Dohled hledanosti:** slova mezery bez objemu → `provider.keyword_volumes` (bulk actor per slovo; fetch to dělá automaticky, krok 5). CPC bulk actoru je v USD → provider převádí na Kč.
- **Vizuály:** bidders nesou `nahledy` (≤3 archivní kreativy z registru, klik = zvětšení) a vzor klonu `thumb` — vyplní bílé místo, když SERP nedá popis. **Kreativy MUSÍ být k tématu** — build filtruje textem (`_tema_creatives`, k→c varianta), ale texty jsou v datech často prázdné (copy je jen UVNITŘ screenshotu) → **model kreativy z portfolia PROHLÉDNE OČIMA a tematické doplní ručně** (reálný případ: Dr. Max = taška na pleny jako „nejstarší reklama", Nutrendův kreatin našla až vision kontrola). Radši žádná kreativa než nesouvisející; mrtvá URL → `onerror` blok skryje. Popisek stáří VŽDY „inzeruje nepřetržitě X dní" (stáří nejstarší reklamy inzerenta), ne „běží X dní" (nevíme, jak dlouho běží ta konkrétní). Tabulka mezery ukazuje CPC (Kč) + záměr česky; bez objemu → „long-tail", ne „–".
- **`verdikt`** (model, 2–4 věty, smí <b>): syntéza VŠECH zdrojů (SERP × registr × metriky × landingy) — věta, kterou SEO nástroj neposkládá. Renderer ji dává hned pod stat row.
- **Landing sekce = karty se STRUKTUROVANÝM rozborem (nejsilnější sekce boardu):** velký screenshot (browser tool, viewport 1280×2200 → `lp-<název>.png` vedle HTML, `landing_gaps[].screenshot` relativní; klik = celá stránka) + **`url_full`** (proklik „Otevřít stránku ↗" — povinné) + tři odrážkové bloky: **`silne`** (✓ co JEJICH stránka dělá dobře), **`slabe`** (⚠ JEJICH slabiny — holé konstatování, ne rada konkurentovi) a **`vas_tah`** (renderer label „→ Inspirace pro nás" — NAŠE strana: co z toho doplníme/uděláme u klienta — formuluj z pohledu klienta „postavte X", „vyhraňte se", „který jim chybí"). Tři barvy (zelená/oranžová/mint) drží jasnou hranici jejich vs. naše. Každý 2–3 odrážky, smí `<b>`. Sytit z reálné návštěvy stránky (browser tool). Starý plochý `chybi` je jen fallback. Anti-bot stěna (Playwright headless i headful = 403)? → **`provider.page_screenshot(url, out, market)`** — Apify `apify/screenshot-url` s REZIDENTNÍ proxy trhu (~$0,02–0,05/snímek; ověřeno: Alza 403 → přes rezidentní CZ proxy 200 a plný snímek). Browser tool na serveru je první volba (zdarma), actor je záskok. Když selže i ten → screenshot null (renderer přizná „náhled nedostupný"); „404" v `chybi` → červený badge. **`landing_stavba`** (model, 3–5 odrážek): checklist „Co postavit vy" složený z děr konkurence — proveditelné pokyny, ne fráze. **Poslední odrážka = VŽDY handoff na výrobu: doporučená stránka je ADVERTORIAL (prodejní článek) a v systému na něj existuje skill `article-writer` (typ `prodejni-clanek`, vč. listicle advertorialu)** — klientovi piš „zadejte AI Marketérovi", interně směruj na article-writer. Stejně tak `action_plan` krok se stránkou. Search board mezeru NAJDE, article-writer stránku VYROBÍ — nikdy nenavrhuj ruční psaní.

## Co plní MODEL (sémantika — po `search-fetch`, před `search-render`)

- **`bidders[].proc_nebezpecny`** (top 3–5) — čím je hráč nebezpečný a jak se mu vyhnout (1–2 věty, z dat: počet reklam, roky běhu, typ hráče).
- **`cloneable_ads[].vzor` — VŽDY jednotný mockup, nikdy obrázek kreativy v sekci 02.** Text ze živého SERPu; když SERP dá jen hlavičku, **PŘEPIŠ text z reálné kreativy v registru (vision — text je uvnitř screenshotu)** do `head`/`desc` a do `vzor.pozn` napiš zdroj („Přepis reálné reklamy z veřejného registru…"). Když text není nikde, nech jen hlavičku a do `pozn` dej insight („Víc konkurent neukazuje — prodává jen důvěru značky…"). Vymýšlet text je zakázané.
- **`cloneable_ads[].klon`** — head (≤30 znaků smysluplně), desc, 2 sitelinky, `pozn` (co ze vzoru převzít a co NE) — **přeložené na produkt/značku KLIENTA**, žádné kopírování konkurenta doslova.
- **`keyword_gap[].zamer` + `pozn`** — nákupní vs. srovnávací záměr; poznámka proč slovo stojí za nákup.
- **`landing_gaps`** — **BROWSER TOOLEM otevři landing top 3 bidderů** (z reklam/SERP) a vyplň slib · cena_viditelna · cta · trust · **chybi**; + `landing_pointa` (jedna věta: co nemá nikdo = kudy na to). Anti-bot stěna (Alza…)? Vyplň z textu reklamy a poznač, ověření nešlo.
- **`budget_semafor.benchmark_pozn` + `priklad`** ({rozpocet_kc, kliku_odhad, pozn}) — odhady VŽDY rámuj jako odhady.
- **`advertorial_namet`** — samostatná sekce s NÁMĚTEM na advertorial. **Nejdřív si načti principy ze skillu `article-writer`** (jeho soubor `article-types.md` v references, sekce „Prodejní článek / advertorial" — je to JINÝ skill, ne ad-scout): vyber **podtyp podle publika** (příběhový · PAS · listicle · expertní · srovnávací) a drž univerzální pravidla (70/30, produkt až po 40–60 %, unikátní mechanismus, měkká + tvrdá CTA, kongruence titulku s reklamou, délka podle námitek). Pole: `{podtyp, proc_podtyp, titulek, osnova:[beats dle podtypu — smí <b>], cilova_slova:[z mezery], kongruence, cta, handoff, reklamy:[2× {domain, head, desc, sitelinks}]}`. **`reklamy` = 2 mockupy search reklam KLIENTA, které na článek povedou** (vstup funnelu reklama→článek→nabídka) — head zrcadlí gap slovo, cíl = článek, ne produkt; renderer je vykreslí jako Google mockupy pod osnovou. **Osnovu syt daty z boardu i rodiny** (mýty z Viral/DNA boardu, jazyk reklam konkurence, díry z landing sekce). `handoff` = kompletní samostatné zadání pro AI Marketéra (renderer dává tlačítko „Zadat AI Marketérovi" — kopíruje do schránky).
- **`action_plan`** — přesně 3 kroky `{title, body}` s časováním (týden 1 / týden 2–4 / den 30+), proveditelné bez další otázky.
- Volitelně `meta.podtitulek`. **Vykání, česky, žádné anglicismy na ploše** (CPC/SERP vysvětli nebo přelož).

## Pravidla poctivosti

- **🌍 GEO: operátor může sedět MIMO trh** (reálný případ: analýza CZ trhu ze Španělska). Nikdy nespoléhej na lokální prohlížeč/IP pro tržní data: SERP a metriky VŽDY přes actor s country parametrem, landing snímky přes `provider.page_screenshot` (rezidentní proxy trhu), registry jen přes URL s country/region parametrem. Lokální browser je OK jen pro čtení registrů s explicitním geo v URL.
- **🛑 DRUHÝ SNÍMEK MEZERY JE POVINNÝ.** Placený blok se střídá a jeden snímek LŽE (reálný případ: první sonda ukázala 10 slov s 0 inzerenty; druhý snímek — „creapure 500g" 6 inzerentů, „s příchutí" 5, „gummies" 4). Před finalizací PŘEMĚŘ všechna slova mezery druhým během `search-probe`; hustota = SJEDNOCENÍ snímků; slova s 3+ inzerenty z mezery VYHOĎ (→ červená semaforu); do `pozn` piš „střídavě X a Y", ne „nikdo". Biddery objevené až druhým snímkem DOPLŇ do sekce 01 (+ ověř jejich registr přes `advertiser_ads`).

- **Počty rámuj jako vzorek** — SERP snímek je momentka pár dotazů, registr je capnutý fetch; reálný trh je větší.
- **`provereno`** u biddera = potvrzen v registru Google; SERP-only hráče označ (mohou být nárazoví).
- Odhady CPC/kliků = plánovačová čísla, ne slib („přesné ceny ukáže až první týden kampaně" nechává renderer).
- **Nikdy nerehostuj cizí kreativu**; texty reklam = veřejný placený blok (citace k rozboru OK). Registr Google jmenovat SMÍŠ, srovnávače NIKDY, Apify/metodu vynech.
- `<title>` stránky = přesně hlavní nadpis (`Search Ad Board — „<slovo>"`).
