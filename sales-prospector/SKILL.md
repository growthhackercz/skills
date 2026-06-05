---
name: sales-prospector
description: "Najde 10–100 nových obchodních kontaktů denně přesně podle vašeho ideálního klienta. Hledá ve veřejných českých zdrojích (ARES, Mapy Google, Justice.cz, oborové katalogy, zpravodajské kanály) bezpečně k ochraně proti robotům, bez LinkedIn. Automaticky vyřazuje firmy, které už máte v CRM nebo kterým jste se nedávno věnovali. Výstup: seznam prospektů ve složce /documents/sales/prospects/ a volitelné vložení do CliqSales CRM."
category: sales
status: ready
version: "1.0"
publishedAt: "2026-05-25"
metadata: {"openclaw":{"emoji":"🎯"}}
---

# Sales Prospector

## ⚠️ Povinný postup (pro vykonávajícího agenta — čti jako první)

Tento skill **musí** projít kroky 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 **v pořadí**. Přeskakování kroků nebo zastavovacích bodů (✋ STOP 1 / STOP 2 / STOP 3) znamená nesplnění úkolu — výstup nebude konzistentní, ošetření duplicit selže a uživatel ztratí kontrolu nad tím, jaké firmy se v jeho jménu osloví.

**Když uživatel chce „rychlý běh", zkracuj OBSAH (méně otázek, kratší profil), NE STRUKTURU.** Pořád potvrď profil ideálního klienta v Kroku 1 a plán vyhledávání v Kroku 2. „Rychle" znamená 30 vteřin každá zastávka, ne přeskočení.

**Žádné improvizace na vlastní pěst.** Pokud chybí podklad (Brand DNA, Product DNA, přístupové údaje k integraci), použij dokumentovaný náhradní postup z Kroku 0 nebo skill zastav s lidskou zprávou *„chybí X, doplň a spusť znovu"*. Nevymýšlej alternativní postup mimo skill.

**Vždy používej helper skripty ze složky `scripts/`** (`dedup_check.py`, `ghl_contact_upsert.py`) — neopisuj jejich logiku do inline kódu. Pro HTTP používej nástroj `web_fetch`. Pro vyhledávání zdroje uvedené v `references/zdroje-vyhledavani.md`.

## Co tento skill dělá pro váš byznys

Najde vám každý den novou várku **kvalitních obchodních kontaktů** — firem, které přesně odpovídají tomu, jak jste si definovali ideálního klienta. Není to masivní stahování e-mailů, je to pečlivý výběr.

Skill ošetřuje tři běžné nepříjemnosti, které trápí každý prodejní tým:

1. **„Pořád dokola hledáme ručně."** Skill prohledá ARES, Mapy Google, oborové katalogy a zpravodajské kanály za vás — denně, bez únavy.
2. **„Vrátí nám firmy, které už dávno známe."** Skill si pamatuje, koho jste minulé měsíce dostali, a kdo už ve vašem CRM je. Stejnou firmu nebudete oslovovat dvakrát.
3. **„Obchodník dostane seznam, ale neví, čím začít rozhovor."** Skill pro každou firmu připraví jednu až dvě věty „proč právě oni" — konkrétní hák do prvního oslovení.

**Cílový denní objem:** výchozí 30 prospektů, podle potřeby 10 až 100.

## Co vám skill dodá

Ve složce `/documents/sales/prospects/[YYYY-MM-DD]-[nazev-kampane]/`:

| Soubor | K čemu slouží |
|---|---|
| `prospects.csv` | Tabulka prospektů (sloupce: `Company`, `Name`, `Email`, `Phone`, `Web`, `Tags`, `Source`, `Uvodni_veta`, `Source_URL`, `Signal_zajmu`). **Do CliqSales CRM v Kroku 8 se posílají jen standardní pole** (jméno, firma, e-mail, telefon, web) + jediný tag `sales prospector`. Ostatní sloupce slouží pro lidský přehled v `prospects-review.md` a pro auditní stopu. |
| `prospects-review.md` | Lidsky čitelný přehled — můžete ho otevřít a procházet v editoru, řazeno podle relevance, s odůvodněním u každého řádku |
| `idealni-klient.md` | Schválený profil ideálního klienta — abyste se za týden mohli podívat, podle čeho jste prospekty hledali |
| `plan-vyhledavani.md` | Schválený seznam zdrojů, parametrů a denního cíle — pro zpětnou kontrolu a opakovatelnost |
| `meta.json` | Strojové metadata (kampaň, datum, počet kandidátů, kolik bylo vyřazeno a proč, zda došlo k vložení do CRM) |

Plus tabulka prospektů přímo v chatu pro rychlé prolétnutí, než si soubory otevřete.

## Jak skill pracuje — 8 kroků se 3 zastávkami na schválení

Skill nikdy nepokračuje bez vašeho výslovného „pokračuj" v zastávkách (✋ STOP).

### Krok 0 — Příprava (tiše)

**🛑 NEZAČÍNEJ sběrem dat.** Pokud uživatel řekne *„najdi mi 20 prospektů pro X"*, **NEROZJÍŽDĚJ rovnou** `web_fetch` na vyhledávače ani vlastní Python skripty. Musíš nejdřív projít Krokem 0 → 1 → STOP 1 → 2 → STOP 2. Až po STOPu 2 spustíš Krok 3 (sběr).

1. Skill načte vaši značku z `/documents/brand/brand-kit/brandDNA.md` a produkt z `/documents/brand/products/[slug]/productDNA.md`.
2. Pokud něco z toho chybí, položí vám **6 doplňujících otázek** (viz `{baseDir}/references/idealni-klient-sablona.md`).
3. Zeptá se na **název kampaně** (krátký, např. „eko-kosmetika-eshopy"). Když ho nedáte, navrhne ho podle vstupu.

V tomto kroku skill **nic neukládá na disk** — všechno drží jen v paměti rozhovoru. Cílová složka vznikne až v Kroku 7.

### Krok 1 — Definice ideálního klienta

Z údajů o značce, produktu a vašich odpovědí skill sestaví **profil ideálního klienta** podle šablony v `{baseDir}/references/idealni-klient-sablona.md`:

- **Firmografika** — obor (CZ-NACE pro B2B), velikost, region, právní forma, věk firmy
- **Produktové signály** — jakou technologii nebo platformu firma používá; co prodává; co vyrábí
- **Signály zájmu** — co naznačuje, že je firma „zralá k oslovení" (expanze, nová investice, nábor, nový majitel)
- **Vyřazovací kritéria** — kdo do profilu **nepatří** (insolvence, konkurence, příliš malí, příliš velcí)
- **Vyhledávací předpis** — zhuštěné pravidlo, podle kterého skill bude hledat (např. „firmy s CZ-NACE 4711, obrat 5–50 mil. Kč, Praha nebo Brno, aktivní, ne v insolvenci")

**✋ STOP 1** — skill vypíše profil v chatu a zeptá se: *„Souhlasíš s tímto profilem? (ano / uprav X / vygeneruj jinak)"*. Bez výslovného souhlasu nepokračuje.

### Krok 2 — Plán vyhledávání a strategie ošetření duplicit

Skill navrhne **2–3 zdroje** ze seznamu v `{baseDir}/references/zdroje-vyhledavani.md` (vybere ty, které nejlíp odpovídají profilu z Kroku 1). Pro každý uvede:

- Konkrétní dotaz nebo filtr (např. *„ARES: CZ-NACE = 4711, kraj = Praha, obrat 5–50 mil., aktivní"*)
- Odhad počtu kandidátů
- Denní limit, který je u tohoto zdroje bezpečný

Navrhne **denní cíl** (výchozí 30 prospektů, rozsah 10–100) a vyčíslí odhad doby běhu a nákladů (pokud používáme placené vyhledávání jako Brave Search).

Pak skill ukáže **strategii ošetření duplicit** — výchozí nastavení v souladu s `{baseDir}/references/dedup-strategie.md`:

| Pravidlo | Výchozí hodnota |
|---|---|
| **Karanténa mezi kampaněmi** | 180 dní — kontakt už dodaný v jiné kampani se nepoužije znovu dříve než za půl roku |
| **Karanténa po kontaktu v CRM** | 180 dní — pokud firmu v CRM někdo oslovil v posledních 180 dnech, vyřadí se |
| **Příznak DND (Do Not Disturb — nerušit)** | aktivní, tvrdě vyřadí — respektujeme nativní „nerušit" v CliqSales |
| **Černá listina** | aktivní, čte se z `/documents/sales/blacklist.csv` |
| **Příznak [PROBĚHL DLOUHO]** | u kontaktů s aktivitou v CRM starší než 180 dní — ponechá je v seznamu, ale označí v přehledu — obchodník sám rozhodne |

**✋ STOP 2** — skill vypíše plán a strategii duplicit, zeptá se: *„Souhlasíš s plánem a strategií duplicit? Můžu spustit vyhledávání? (ano / uprav zdroje / uprav počet / uprav karantény)"*. Bez souhlasu nepokračuje.

### Krok 3 — Sběr surových údajů

Skill paralelně dotáže schválené zdroje. **Respektuje denní limity** u každého zdroje (viz `{baseDir}/references/zdroje-vyhledavani.md`).

Průběžně hlásí v chatu po každých 10 nasbíraných firmách: `🔎 Krok 3: nasbíráno 20 / 30 (ARES: 12, Mapy Google: 8)`.

Seznam drží v paměti rozhovoru. Na disk neukládá.

### Krok 4 — Doplnění informací

U každé firmy se skill pokusí dohledat:

- Funkční webovou stránku
- Kontaktní e-mail (jen z `/kontakt`, `/contact`, patičky — žádné stahování e-mailů z neveřejných zdrojů)
- Telefon
- Jméno klíčové osoby (jen pokud je veřejně na webu — „O nás", „Tým", „Vedení")
- Odhad počtu zaměstnanců
- Konkrétní popis oboru (ne jen kód)
- Stručný popis firmy jednou větou
- **Signál zájmu** (volitelně, ze zpravodajských kanálů): např. *„získali investici Series A v dubnu 2026"*, *„otevírají nový sklad v Brně"*, *„hledají marketingového ředitele"*

Pokud se nepodaří najít ani e-mail, ani telefon, firmu si skill nechá, ale označí ji `kvalita_kontaktu: nízká`.

**Hybridní načítání stránek — kdy `web_fetch`, kdy nativní Chromium:**

Výchozí nástroj je `web_fetch` — rychlý, levný, postačí pro **~90 % českých firemních webů** (statické HTML).

**Fallback na nativní headless Chromium** spusť, pokud `web_fetch` vrátí:

- HTML s méně než 1500 znaků viditelného textu (po readability extrakci), **NEBO**
- prázdný `<body>` obsahující pouze `<div id="root">`, `<div id="__next">` nebo `<div id="app">` — typické známky moderní jednorázovkové aplikace (React, Next.js, Vue, Nuxt), kde se obsah načítá až JavaScriptem, **NEBO**
- HTTP 403 / 429 ze serveru (statické stahování zablokováno)

V tom případě volej nativní browser (`/usr/local/bin/openclaw-chromium`, headless, schema `navigate` + `extract`), navigate na stejnou URL, počkej 3 vteřiny na vykreslení JavaScriptu, extrahuj text.

**Pokud i browser dostane CAPTCHA / přihlašovací zeď**, NEPROBÍHEJ obcházet — označ kontakt `kvalita_kontaktu: nízká` a pokračuj. Antipatterns sekce dole popisuje, kde browser **nepoužívat**.

### Krok 5 — Vyřazení nevyhovujících (pět vrstev)

Skill aplikuje pravidla v tomto pořadí. U každé vyřazené firmy si pamatuje **důvod** — uvidíte to v `prospects-review.md`.

1. **Povinná kritéria z profilu ideálního klienta** — vyřadí ty, kteří nesplňují (např. mimo region, mimo velikostní rozmezí, bez kontaktu).
2. **Vyřazovací kritéria z profilu** — insolvence (ověří se v Justice.cz / ISIR), konkurence, jiné disqualifikátory.
3. **Černá listina** (`/documents/sales/blacklist.csv`) — pokud existuje, vyřadí podle e-mailu, telefonu, domény, IČO nebo vzoru názvu firmy.
4. **Karanténa z předchozích kampaní** (`/documents/sales/.dedup-history.jsonl`) — pokud firma už byla v jakékoli kampani v posledních 180 dnech, vyřadí.
5. **Kontrola v CliqSales CRM** — u každého zbývajícího kandidáta zavolá `GET /contacts/search?email=...` a vyhodnotí:
   - **Příznak DND zapnutý** → tvrdě vyřadit (respektujeme nerušit)
   - **Aktivita v posledních 180 dnech** → vyřadit (někdo už oslovil)
   - **Aktivita starší než 180 dnů** → ponechat + označit `[PROBĚHL DLOUHO]` se zmínkou poslední aktivity a fáze v pipeline

Skill vypíše souhrn v chatu: *„Ze 47 nasbíraných firem odfiltrováno 22: bez kontaktu (5), insolvence (3), černá listina (2), karanténa kampaně (8), nedávno v CRM (3), DND (1). Zbývá 25 prospektů. + 3 firmy označeny [PROBĚHL DLOUHO] — vidíte je v přehledu."*

### Krok 6 — Příprava úvodních vět pro oslovení

Pro každého zbývajícího prospekta skill napíše **jednu až dvě věty**, kterými může obchodník začít první oslovení. Vychází z:

1. Signálu zájmu (pokud máme): *„Právě jste otevřeli druhou pobočku v Brně — náš [produkt] vám usnadní [problém]."*
2. Konkrétního detailu z webu: *„Vidím na vašem webu sekci o udržitelnosti — náš [produkt] je 100% recyklovatelný."*
3. Souladu s oborem: *„Specializujete se na [obor X], což je přesně náš nejúspěšnější segment."*

### Krok 7 — Vypsání a uložení

1. Skill vytvoří složku `/documents/sales/prospects/[YYYY-MM-DD]-[nazev-kampane]/` a uloží do ní pět souborů (viz „Co vám skill dodá" výše).
2. **Připíše** všechny vydané prospekty (včetně těch s příznakem [PROBĚHL DLOUHO]) do `/documents/sales/.dedup-history.jsonl` — to je živá paměť, která brání budoucímu opakovanému dodání.
3. V chatu vypíše **tabulku prvních 20 prospektů** (Firma / Web / Kontakt / Úvodní věta). Celý seznam najdete v `prospects-review.md`.
4. Zobrazí absolutní cestu ke složce: `/documents/sales/prospects/2026-05-25-eko-kosmetika-eshopy/`.

### Krok 8 — Volitelné vložení do CliqSales CRM

Skill se zeptá: *„Chceš tyto leady nahrát do CliqSales CRM?"*

Možnosti odpovědi:
- **„ne, jen soubory"** → konec. Do `meta.json` se zapíše `ghl_pushed: false`.
- **„vyber které"** → uživatel označí podmnožinu (čísla řádků nebo „jen úroveň A"). Pokračuje s vybranou podmnožinou.
- **„ano, všechny"** → pokračuje se všemi.

Pak skill:

1. Spustí **zkušební režim**: `python3 {baseDir}/scripts/ghl_contact_upsert.py --csv [cesta] --dry-run`
2. Skript načte přístupové údaje k CliqSales přes sdílenou knihovnu `cc_credentials.ghl_credentials()`. Pokud chybí, vypíše: *„CliqSales (GoHighLevel) integrace není nastavená. Jdi do Control Center → Nastavení → Integrace → CliqSales (GoHighLevel), vyplň Private Integration Token a Location ID."* → Krok 8 končí.
3. V chatu se objeví výsledek zkušebního průchodu: *„Vytvořím 19 nových kontaktů, upravím 7 existujících (shoda podle e-mailu). 2 mají v CliqSales aktivní DND — upozorňuji, kampaně na ně nepoběží. Aplikuji tag: `sales prospector`."*
4. **✋ STOP 3** — *„Můžu vložit do CRM doopravdy? (ano / ne)"*
5. Pokud „ano" → spustí skript bez `--dry-run`. Vrátí souhrn `{created, updated, failed, errors}`.
6. Aktualizuje `meta.json` o `ghl_pushed: true, ghl_summary: {...}`.
7. Závěrečné hlášení v chatu: *„Vloženo 19 kontaktů do CliqSales CRM s tagem `sales prospector`. 7 bylo upraveno (e-mail už existoval). 0 selhalo. Detaily v `meta.json`."*

**Pravidla pro tagy a vlastní pole (politika v1.0):**

- **Jediný tag:** `sales prospector` (lowercase, s mezerou). Žádné kampaňové tagy (`prospector-bioptron-brno-...`), žádné zdrojové tagy (`prospector-source-firmy.cz`), žádná klíčová slova (`bioptron`, `brno`, `b2b`). Tag drží CRM přehledný a kontakt lze filtrovat jediným kliknutím.
- **Žádné vlastní pole (custom fields).** Hook, signál zájmu, zdroj a URL zdroje žijí jen v souborech `/documents/sales/prospects/[...]/prospects-review.md` (lidský audit). Pokud obchodník potřebuje k danému kontaktu úvodní větu, otevře přehled v souboru, ne v CRM.
- **Kampaň** se do CRM nepropisuje. Žije jako název složky `/documents/sales/prospects/[YYYY-MM-DD]-[kampaň-slug]/` a v `meta.json`. Pro zpětné dohledání „odkud kontakt přišel" otevřeš historii v `.dedup-history.jsonl` nebo `meta.json` kampaně.
- **CSV sloupec `Tags`** v `prospects.csv` se **ignoruje** — drž ho prázdný. Helper skript ho nečte.

## Návaznost na další skilly

**Skill volá:**
- `brand-dna-generator` — v Kroku 0 jako náhrada, pokud chybí Brand DNA (informativně, neblokuje)
- `product-dna-generator` — totéž pro Product DNA

**Skill předává výstup:**
- `sales-scout` — vezme `prospects.csv` a u každého kontaktu udělá hlubší kvalifikaci
- `aiq-strategy-generator` — postaví personalizovanou prodejní cestu pro nejlepší prospekty
- `sales-mentor` — sleduje konverzi prospektů přes čas, vrací zpětnou vazbu

## Doplňkové soubory (reference)

- `{baseDir}/references/zdroje-vyhledavani.md` — detail u každého zdroje (API, dotazy, denní limity, poznámky k ochraně proti robotům)
- `{baseDir}/references/idealni-klient-sablona.md` — šablona profilu + 6 doplňujících otázek (záložní postup, když chybí Brand DNA / Product DNA)
- `{baseDir}/references/ghl-upsert-mapping.md` — mapování sloupců CSV na pole v CliqSales (GoHighLevel)
- `{baseDir}/references/dedup-strategie.md` — pětivrstvá ochrana proti opakovanému dodávání kontaktů (formát historie, formát černé listiny, hraniční případy)

## Antipatterns — co NEDĚLAT

Tyto chyby se opakovaně objevují u agentů, kteří skill používají nesprávně. Vyhni se jim — každá z nich poškozuje výstup nebo dlouhodobou použitelnost zdrojů.

| Antipattern | Proč je špatný | Co dělat místo toho |
|---|---|---|
| Pustit hned `web_fetch` na DuckDuckGo / Bing / Google search bez Kroku 1 a 2 | Bez schválené definice ideálního klienta sbíráš náhodné firmy, ne kvalifikované prospekty. Bez schváleného plánu vyhledávání nerespektuješ denní limity zdrojů. | Projdi nejdřív Krok 0 → 1 → ✋ STOP 1 → 2 → ✋ STOP 2. Až po souhlasu uživatele spusť Krok 3. |
| Psát vlastní inline Python skript s `bs4` (BeautifulSoup), `requests`, `selenium` | Tyto knihovny **NEJSOU** v prostředí openclaw nainstalované. Skript spadne při importu (`ModuleNotFoundError`). | Volej helper skripty ze složky `scripts/`. Pro HTTP používej nástroj `web_fetch`. Pro parsing HTML stačí stdlib `html.parser` + regulární výrazy. |
| Pokračovat po HTTP 202 / 429 / 403 ze stejného zdroje | Ochrana proti robotům se aktivuje — další dotazy začnou vracet captcha a zablokují IP adresu pro budoucí použití. | Zastav konkrétní zdroj, pokračuj s ostatními. Žádné opakované pokusy na ten samý zdroj. |
| Přeskočit Krok 5 (pětivrstvé ošetření duplicit) | Stejné firmy půjdou znovu — i ty, které máš v CRM, na černé listině, nebo s aktivním DND. Obchodník dostane duplikáty, kontakty dostávají opakované oslovení (riziko stížnosti). | Po Kroku 4 vždy spusť `scripts/dedup_check.py` s parametry podle `dedup-strategie.md`. |
| Přímé stahování z Google search | Google rozezná opakované dotazy po několika voláních → captcha → zablokuje IP pro hodiny až dny. | Pro webové vyhledávání použij Brave Search API nebo Serper.dev (přístupové údaje jsou v `cc_credentials`). |
| Sbírat e-maily ze zdrojů, které vyžadují přihlášení, nebo ze SPF/MX záznamů | GDPR riziko — kontakt není veřejně dostupný, vystavujete klienta riziku stížnosti nebo pokuty. | Sbírej jen z veřejných stránek (`/kontakt`, `/contact`, ARES, oborové katalogy s otevřeným přístupem). |
| Vyrobit výstupní soubory bez Kroku 7 (uložení + zápis do historie) | Při příštím běhu se stejné firmy vyfasují znovu — paměť pro ošetření duplicit nezachytí, co už bylo dodáno. | Po Kroku 6 vždy spusť Krok 7: ulož 5 souborů + připiš do `/documents/sales/.dedup-history.jsonl`. |
| Sběr 50+ kontaktů z Firmy.cz za pár vteřin | Firmy.cz má středně přísnou ochranu proti robotům — denní limit je ~30 dotazů. Větší objem aktivuje blokaci. | Použij Firmy.cz jen jako doplněk (max 30 dotazů denně), primární zdroje jsou ARES a Google Maps Places API. |
| Volat nativní Chromium na Google Search / Bing / DuckDuckGo, aby se „obešla CAPTCHA" | Tyto vyhledávače poznají headless Chromium podle podpisu (Playwright, chybějící skutečný fingerprint prohlížeče) → CAPTCHA → zablokování IP adresy. Browser zde nepomáhá, jen zhorší situaci. | Pro webové vyhledávání používej Brave Search API nebo Serper.dev — přístupové klíče řeší `cc_credentials`. Detail v `zdroje-vyhledavani.md`. |
| Volat nativní Chromium na LinkedIn (firma, osoba, vyhledávání) | LinkedIn je v Sales Prospectoru **explicitně vyřazen**. I s browserem hrozí (a) zablokování LinkedIn účtu klienta, pokud skript používá jeho session cookies, (b) porušení podmínek LinkedIn. | Pro práci s LinkedIn daty použij samostatný skill `linkedin-prospector` (až bude vydán). |
| Po HTTP 403 od CliqSales API rovnou pokračovat „náhradním postupem" (vlastní inline Python, ruční volání API) | Cloudflare 403 Error 1010 znamená, že podpis klienta je blokovaný — vlastní improvizace problém **neobejde**, jen poškodí audit deduplikace a vyprodukuje výstup, který nikdy nedoputuje do CRM. | Zastav skill, oznam uživateli: *„CliqSales API blokována Cloudflare 1010 — potřeba aktualizovat User-Agent v helper skriptu."* Skript po opravě spusť znovu. |

## Bezpečnost a citlivá data

- **Přístupové údaje k CliqSales:** skill je čte výhradně přes sdílenou knihovnu `cc_credentials.ghl_credentials()` (umístění: `~/.openclaw/cs-skills/_lib/`). Nikdy se neukládají do logů, do chatu ani do souborů. V logu se ukazuje jen otisk (`f3e1a2…(len=64)`).
- **Ochrana proti robotům:** skill dodržuje denní limity u každého zdroje (viz `zdroje-vyhledavani.md`). Při HTTP 429 / 403 zastaví konkrétní zdroj a pokračuje s ostatními — nikdy se nesnaží obejít kontrolu.
- **LinkedIn:** tento skill **nepodporuje**. Pro práci s LinkedIn daty existuje samostatný skill `linkedin-prospector` (k vydání později).
- **GDPR:** skill pracuje **výhradně s veřejně dostupnými údaji** (ARES, veřejné kontaktní stránky firem, oborové katalogy). Nestahuje e-maily ze SPF/MX záznamů ani z databází třetích stran. Firmy bez veřejně zveřejněného kontaktu se neukládají, jen se označí.
- **Idempotentní vkládání:** v Kroku 8 se používá `POST /contacts/upsert` — pokud kontakt s daným e-mailem už v CRM existuje, upraví se, nevznikne duplikát.
