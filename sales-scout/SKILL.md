---
name: sales-scout
description: "Hluboký pre-sales brief na jeden konkrétní kontakt. Spouští se přes webhook (při příchodu nového leadu z CliqSales CRM) nebo manuálně z chatu. Z minima údajů (e-mail / jméno firmy / web) a definovaných produktů (Product DNA) dohledá web, ARES, LinkedIn (přes vestavěný prohlížeč), insolvenční rejstřík, veřejné zakázky a signály zájmu. Připraví 11-sekční brief s fit posouzením pro top 1–3 fitující produkty, doporučenými sales úhly, e-mailem, call openerem a kvalifikačními otázkami. Brief se uloží jako poznámka v CliqSales CRM (Rich Text). Plně autonomní — bez ptaní uživatele."
category: sales
status: ready
version: "1.0"
publishedAt: "2026-05-25"
metadata: {"openclaw":{"emoji":"🔎"}}
---

# Sales Scout

## ⚠️ Povinný postup (pro vykonávajícího agenta — čti jako první)

Tento skill **musí** projít kroky 0 → 0.5 → 1 → 2 → 3 → 4 → 5 → 6 → 7 **v pořadí**. Přeskakování kroků znamená nesplnění úkolu.

**Skill je plně autonomní — bez zastavení (žádné STOP body).** Spouští se přes webhook (uživatel není u rozhovoru) nebo manuálně. V obou případech projede vše bez ptaní:

- **Chybí identifikátor firmy** → skript skončí chybou (exit kód 3), nezeptá se.
- **Existuje brief mladší 60 dnů** → idempotentně vrátí původní (`note_id`) a skončí. Pro nový brief uživatel buď smaže audit záznam, nebo do promptu doplní `refresh=true`.
- **Kontakt v CliqSales CRM neexistuje** → skript ho vytvoří automaticky a připojí poznámku.
- **Webhook nedodal produkt + máš víc Product DNA** → udělej **multi-product brief** pro top 1–3 fitující.

**Žádné improvizace.** Pro výzkum používej **výhradně** zdroje uvedené v `{baseDir}/references/research-zdroje.md`. Pro LinkedIn používej nástroj `browser` (vestavěný Chromium), ne `web_fetch` — viz `{baseDir}/references/browser-strategie.md`. Pro vložení poznámky do CRM používej **jen** skript `scripts/ghl_scout_push.py`.

**Žádný vlastní inline Python** s `bs4`, `requests`, `selenium`, `playwright` — knihovny **NEJSOU** v prostředí dostupné. Používej `web_fetch`, `browser` a stdlib + helper skripty ze `scripts/`.

## Co tento skill dělá pro váš byznys

Obchodník nemá zvedat telefon naslepo. Dostane brief, ve kterém už **před prvním kontaktem** vidí, s kým mluví, jakou má firma velikost, zda není v insolvenci, jaké jsou nejnovější novinky a — co je nejdůležitější — **jaký z vašich produktů na firmu sedí**, jakým úhlem ji oslovit, jaký e-mail napsat a jaké otázky položit při hovoru.

Skill řeší tři typické nepříjemnosti pre-sales fáze:

1. **„Obchodník se ptá zákazníka na věci, které si mohl dohledat sám."** Skill projde web, ARES, LinkedIn a veřejné zdroje za pár desítek vteřin. Zákazník při prvním hovoru ví, že obchodník přišel připravený.
2. **„Lead přišel přes formulář a nikdo s ním nezačal pracovat 4 hodiny."** Skill se spouští automaticky z webhooku CliqSales CRM — než si obchodník otevře nový kontakt, brief už je v poznámce.
3. **„Máme 3 produkty a obchodník neví, který nabídnout."** Skill posoudí fit firmy pro každý váš produkt (A/B/C grade) a vybere top 1–3 nejvhodnější. Doporučí konkrétní úhel pro každý.

## Co vám skill dodá

**Jediný výstup:** poznámka v CliqSales CRM připojená ke kontaktu. Formát Rich Text (Bold, kurzíva, bullet listy, hyperlinky — viz `{baseDir}/references/ghl-html-konverze.md`).

**Žádné soubory na disku.** Audit (kdy, na koho, který produkt, fit grade, ID poznámky v CRM) se zaznamenává jako jeden řádek v `/documents/sales/.scout-history.jsonl` (append-only, ~200 B / brief).

## Vstup — co skill potřebuje

**Webhook režim** dostane formátovaný text v promptu (formátování dělá webhook v Control Center / CliqSales workflow):

> *„Udělej Scout brief na nový kontakt: jméno=Marek Novák, email=marek@firma.cz, firma=Firma s.r.o., web=https://firma.cz, telefon=+420 777 123 456, contactId=abc123, product=bioptron-medall."*

**Manuální režim** přijme libovolnou kombinaci údajů v běžné větě:

- *„Scout brief na Bioptron Medall s.r.o. pro Bioptron"* (firma + produkt)
- *„Scout na Marka Nováka z Effect Clinic"* (osoba + firma, produkt si Scout vybere automaticky)
- *„Brief na info@firma.cz, nabízíme Bioptron"* (e-mail + produkt)
- *„Brief na kontakt z CRM abc123def456"* (přímo contactId)

**Minimální vstup:** alespoň jeden identifikátor firmy (e-mail, web, název firmy nebo `contactId`).

Postup extrakce údajů v `{baseDir}/references/prompt-parsing.md`. Postup identifikace produktu v `{baseDir}/references/product-context.md`.

## Jak skill pracuje — 8 kroků (všechny autonomní, žádné STOP)

### Krok 0 — Rozbalení vstupu

Vytáhne z prompt textu (regex + LLM uvažování):

- Jméno, příjmení (převést do 1. pádu pro LinkedIn lookup)
- Firma
- E-mail, telefon, web
- `contactId` (pokud webhook)
- **`product` slug** (pokud explicitně uveden)

Validace: musí být alespoň jeden identifikátor firmy. Pokud chybí všechno → skript vrátí chybu *„Promptu chybí identifikace firmy"* a skončí (exit 3).

### Krok 0.5 — Identifikace produktu (nový krok ve v0.2)

Načti `scripts/load_product_dnas.py` → vrátí list všech Product DNA z `/documents/brand/products/*/productDNA.md`.

Rozhodovací logika:

| Vstup z Krok 0 | Počet Product DNA | Akce |
|---|---|---|
| `product=X` v promptu | irelevantní | použij ten (`product_mode = "single"`) |
| Bez produktu | 0 | exit kód 4 + zpráva *„Žádný Product DNA v /documents/brand/products/. Vytvoř aspoň jeden přes product-dna-generator."* |
| Bez produktu | 1 | použij ten automaticky (`product_mode = "single"`) |
| Bez produktu | 2+ | **multi-product režim** (`product_mode = "multi"`): v Kroku 5 spočti fit pro každý produkt, vyber top 1–3 |

Detail v `{baseDir}/references/product-context.md`.

### Krok 1 — Kontrola opakovaného briefu (idempotence)

Načti `/documents/sales/.scout-history.jsonl` (pokud existuje). Hledej řádek se shodou na `contactId` (nebo na e-mailové doméně jako záloha) a `date` mladší než **60 dnů**.

**Pokud shoda existuje:**

- Vrať JSON `{success: true, cached: true, contactId: ..., note_id: ..., skip_reason: "brief mladší 60d"}`
- Skonči (exit 0).

**Pokud uživatel chce vynutit nový brief:**

- Manuální režim: v promptu řekne *„refresh"*, *„aktualizuj"* nebo *„nový brief"*
- Webhook režim: payload má `refresh=true`
- → Krok 1 se přeskočí a pokračuje se na Krok 2

### Krok 2 — Identifikace firmy

Pokud máme IČO → ARES lookup přímo (`scripts/ares_lookup.py --ico ...`).
Pokud máme jen název → ARES lookup podle názvu (`--nazev ...`), vyber nejlepší shodu (přesný match preferovaný, jinak první výsledek).
Pokud máme jen web → extrahuj doménu, dohledej v ARES přes obchodní jméno nebo přes web (některé záznamy mají `webovaStranka`).

Z ARES vytáhni: IČO, sídlo, právní formu, datum vzniku, status (aktivní / v likvidaci), statutární zástupce, předmět činnosti.

### Krok 3 — Paralelní výzkum

Spusť souběžně všechny tyto zdroje (nečekej na jeden, který se rozjíždí pomalu):

- **A) Web firmy** — `web_fetch` na `/`, `/o-nas`, `/produkty`, `/sluzby`, `/cenik`, `/blog`, `/kontakt`. Pokud `<body>` pod 1500 znaků nebo prázdný → náhradně `browser`.
- **B) LinkedIn firmy** — `browser` na `linkedin.com/company/[slug]` (slug odhadem z názvu firmy nebo přes Brave Search).
- **C) LinkedIn osoby** — `browser` na `linkedin.com/in/[slug]` (slug z jména) nebo přes Brave Search `site:linkedin.com/in "Jméno" "firma"`.
- **D) Justice.cz / ISIR** — kontrola insolvenčního řízení podle IČO.
- **E) Hlídač státu** — veřejné zakázky podle IČO (posledních 12 měsíců).
- **F) News a signály zájmu** — RSS kanály (Lupa, CzechCrunch, E15) + Brave Search na `"[Firma]" 2026`.

Pravidla anti-bot v `{baseDir}/references/browser-strategie.md`. Pravidla výběru zdrojů v `{baseDir}/references/research-zdroje.md`.

### Krok 4 — Strukturování briefu (společné sekce)

Naplň společné sekce briefu podle `{baseDir}/references/brief-sablona.md`:

- Sekce 1 — Základní údaje
- Sekce 3 — Relevantní signály z veřejných podkladů
- Sekce 4 — Pravděpodobné potřeby
- Sekce 5 — Rizika a námitky

### Krok 5 — Fit posouzení + per-produkt sekce

Pro každý produkt v scope (single nebo multi):

1. Spočítej **fit grade A/B/C** porovnáním firmografika firmy (sektor, velikost, region, segment) s **ideálním klientem** v Product DNA (`/documents/brand/products/[slug]/productDNA.md` sekce „Ideální klient").
2. Vygeneruj per-produkt sekce:
   - Sekce 2 — Shrnutí fitu (grade + 2–3 věty důvodu)
   - Sekce 6 — Doporučený sales úhel (primární / sekundární / čemu se vyhnout)
   - Sekce 7 — Next-best-action (priorita + krok v CRM + cíl hovoru)
   - Sekce 8 — E-mail / první oslovení
   - Sekce 9 — Call opener
   - Sekce 10 — Kvalifikační otázky

**V multi-product režimu:**

- Spočítej fit pro **všechny** produkty
- Vyber top 1–3 s nejlepším fitem (A > B; pokud žádný A, B > C; pokud všechno C, vrať top 1)
- Per-produkt sekce 2 + 6–10 budou jako H2 subsekce (`## Pro [produkt-name]`) uvnitř jedné poznámky

### Krok 6 — Zápis do auditního logu

Připiš řádek do `/documents/sales/.scout-history.jsonl`:

```json
{"date":"2026-05-25T11:24:00Z","contactId":"abc123","firma":"Effect Clinic","ico":"12345678","mode":"webhook","product_mode":"single","products":["bioptron-medall"],"fit_grades":{"bioptron-medall":"A"},"ghl_note_id":null}
```

Po Kroku 7 (úspěch) se v posledním poli `ghl_note_id` aktualizuje. **Žádný MD soubor.**

### Krok 7 — Vložení do CliqSales CRM

Spusť `python3 {baseDir}/scripts/ghl_scout_push.py`:

**Webhook režim (máme contactId):**
```bash
python3 ghl_scout_push.py --contact-id abc123 --note-body-file /tmp/brief.md
```

**Manuální režim (musíme najít/vytvořit kontakt):**
```bash
python3 ghl_scout_push.py --email marek@firma.cz --first-name Marek --last-name Novák \
    --company "Effect Clinic" --note-body-file /tmp/brief.md
```

Helper sám:

1. **Najde existující kontakt** (podle e-mailu nebo telefonu)
2. **Pokud kontakt neexistuje** → automaticky ho vytvoří (default `--create-if-missing`)
3. **Konvertuje MD → GHL HTML** (Rich Text — pravidla v `{baseDir}/references/ghl-html-konverze.md`)
4. **Vloží poznámku** přes `POST /contacts/{contactId}/notes`
5. **Přidá tag `sales scout`** (jediný, lowercase, idempotent — GHL POST tagů se duplicitou neresetuje)
6. **Aktualizuje `ghl_note_id`** ve `.scout-history.jsonl`

Helper vrátí JSON `{success, contactId, noteId, action, mode}`. Pokud selže → exit kód 4 + chybová zpráva. Žádné ptaní uživatele v žádné fázi.

## Brief — 11 sekcí

Struktura podle `{baseDir}/references/brief-sablona.md`. Stručný přehled (společné × per produkt):

| # | Sekce | Společná / per produkt |
|---|---|---|
| 1 | 📋 Základní údaje (firma, lokalita, web, e-mail, telefon, zdroj) | společná |
| 2 | 🎯 **Shrnutí fitu — grade A/B/C + 2–3 věty důvodu** | **per produkt** |
| 3 | 🚀 Relevantní signály z veřejných podkladů | společná |
| 4 | 💡 Pravděpodobné potřeby (3–5 bodů) | společná |
| 5 | ⚠️ Rizika a námitky (insolvence, soudní spory, negativní press) | společná |
| 6 | 🎯 **Doporučený sales úhel: Primární / Sekundární / Čemu se vyhnout** | **per produkt** |
| 7 | 🎬 **Next-best-action: Priorita + Další krok + Cíl hovoru** | **per produkt** |
| 8 | ✉️ **E-mail / první oslovení** (předmět + tělo) | **per produkt** |
| 9 | 📞 **Call opener** (celá úvodní část hovoru) | **per produkt** |
| 10 | ❓ **Kvalifikační otázky** (5 konkrétních pro hovor) | **per produkt** |
| 11 | 🗂️ Doporučený další krok v CRM (priorita + úkol) | společná (vychází z top fit produktu) |

V multi-product režimu se sekce 2 a 6–10 opakují jako H2 subsekce (`## Pro [produkt-name]`) uvnitř jedné poznámky.

**V briefu jsou jen sekce nadpisem (`## Nadpis`) a bullet listy — žádné tabulky, žádné code blocky, žádné nadpisy H3/H4.** Důvod: GHL Rich Text v poznámkách tyto prvky nepodporuje, brief by v UI vypadal špatně.

## Antipatterns — co NEDĚLAT

| Antipattern | Proč je špatný | Co dělat místo toho |
|---|---|---|
| Pustit `web_fetch` na LinkedIn | LinkedIn loaduje obsah přes JavaScript — `web_fetch` vrátí prázdnou kostru bez dat. | Pro LinkedIn vždy `browser` tool. |
| Více než 3 LinkedIn page views per brief | LinkedIn anti-bot se aktivuje — captcha → blokace IP na hodiny. | Max 3 LinkedIn page views per Scout brief (firma + 1 osoba + 1 záloha). |
| Pokračovat po detekci captcha / login wall | Další pokusy = blokace IP. | Detekuj „Verify you're human", „Sign in to continue", „Just a moment…" — STOP konkrétního zdroje, pokračuj s ostatními. |
| **Zeptat se uživatele na cokoli** (v jakémkoli kroku) | Skill je autonomní — webhook nemá uživatele u rozhovoru. Ptaní rozbije autonomii. | Pro neznámé situace použij **rozumný výchozí stav** podle Kroku 0.5 / 1 / 7. Pokud vstup chybí kriticky → exit s chybou (ne otázka). |
| **Vytvořit dynamický tag** (s datem, fit gradem, produktem) | Tisíce unikátních tagů v CliqSales = nepřehled. | Jediný tag `sales scout` (lowercase, s mezerou). Vše ostatní zůstává v textu poznámky. |
| **Ukládat brief jako MD soubor** do `/documents/sales/scout-briefs/...` | Tisíce souborů zaplaví disk při velkém objemu webhooků. | Brief jen do CRM. Audit jako 1 řádek v `/documents/sales/.scout-history.jsonl`. |
| **Použít headings (H1–H6), tabulky, code blocks** v brief textu | GHL Rich Text v poznámkách je nepodporuje — v UI se zobrazí jako plain text. | Jen bold, kurzíva, bullet/numbered listy, hyperlinky. Pravidla v `ghl-html-konverze.md`. |
| Volat `ghl_scout_push.py` **bez konverze MD → HTML** | Poznámka se uloží jako raw Markdown text — v UI uvidíš `**bold**` doslovně. | Helper sám konvertuje. Pošli mu MD body, on udělá zbytek. |
| **Přeskočit Krok 1** (kontrola opakovaného briefu) | Stejný brief se přepíše v CRM, audit log dostane duplicitní záznamy. | Vždy grep `.scout-history.jsonl` podle `contactId`. Při shodě mladší 60d → idempotentně skonči. |
| Použít `web_fetch` na SPA stránce firmy (React / Next / Vue) | Vrátí prázdný `<body>` — sekce „Co dělají" v briefu zůstane prázdná. | Pokud HTML pod 1500 znaků → náhradně `browser`. |
| Zpracovávat víc kontaktů paralelně (batch mode) | Tento skill je pro **jeden kontakt**. Batch by zaplavil GHL API a LinkedIn anti-bot. | Pro batch (Sales Prospector výstup → 30 briefů) spusť skill 30× sekvenčně s pauzou 30 vteřin mezi běhy. |

## Návaznost na další skilly

**Vstup z:**
- Webhook z CliqSales CRM při příchodu nového kontaktu (primární trigger v produkci)
- `sales-prospector` — pro každý řádek `prospects.csv` můžeš spustit Scout brief manuálně
- Manuální spuštění z chatu obchodníka / manažera

**Předává výstup do:**
- `aiq-strategy-generator` — Scout brief je vstup pro stavbu personalizované prodejní cesty
- `sales-mentor` — analyzuje, které briefy vedly k uzavřeným obchodům

## Doplňkové soubory (reference)

- `{baseDir}/references/research-zdroje.md` — detail u každého zdroje, kdy `web_fetch` a kdy `browser`, denní limity
- `{baseDir}/references/brief-sablona.md` — struktura 11 sekcí + vyplněný příklad (single i multi-product)
- `{baseDir}/references/prompt-parsing.md` — pravidla extrakce údajů z prompt textu (regex + LLM)
- `{baseDir}/references/browser-strategie.md` — pravidla pro `browser` tool (pauzy proti robotům, detekce captcha, časové limity)
- `{baseDir}/references/product-context.md` — jak Scout načte a použije Product DNA, multi-product logika
- `{baseDir}/references/ghl-html-konverze.md` — pravidla konverze Markdown → GHL Rich Text HTML

## Bezpečnost a citlivá data

- **Přístupové údaje k CliqSales:** skill je čte výhradně přes sdílenou knihovnu `cc_credentials.ghl_credentials()` (umístění: `~/.openclaw/cs-skills/_lib/`). Nikdy se neukládají do logů, do chatu ani do souborů.
- **LinkedIn:** skill **nepoužívá** přihlášení do LinkedIn účtu. Pracuje výhradně s **veřejně dostupnými stránkami** (anonymní návštěva přes browser).
- **GDPR:** skill pracuje **výhradně s veřejně dostupnými údaji** (firemní web, ARES, Justice.cz, veřejné LinkedIn pages). Nestahuje e-maily ze SPF/MX záznamů ani z databází třetích stran.
- **Idempotence:** Krok 1 zabraňuje opakovanému dodávání stejného briefu. Krok 7 (vložení do CRM) je idempotentní (helper detekuje duplicitní obsah).
- **Ochrana proti robotům:** pauzy 5–10 vteřin mezi LinkedIn navigacemi, max 3 LinkedIn page views per brief, okamžitý stop při detekci captcha. Detail v `browser-strategie.md`.
