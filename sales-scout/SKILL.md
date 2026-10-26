---
name: sales-scout
description: "Připraví hluboký pre-sales brief na jeden konkrétní kontakt v určeném trhu přes jeho skutečné registry a veřejné zdroje; pro existující CRM kontakt může zmrazit přesný note/tag plán, chybějící kontakt zůstává jen k review."
category: sales
status: ready
version: "1.4"
publishedAt: "2026-09-02"
metadata: {"openclaw":{"requires":{"bins":["python3"]},"emoji":"🔎"}}
---

# Sales Scout

## ⚠️ Povinný postup (pro vykonávajícího agenta — čti jako první)

Tento skill **musí** projít kroky 0 → 0.5 → 1 → 2 → 3 → 4 → 5 → 6 → 7 **v pořadí**. Přeskakování kroků znamená nesplnění úkolu.

**Výzkum nemá STOP bod, ale musí běžet v konkrétním task flow.** Webhook je pouze vstupní transport: sám nezakládá důvěryhodnou task provenance ani neopravňuje CRM zápis. Před `--create-plan` musí existovat kladné ID tasku přiřazeného `cso`. Jeden úplný plán se schvaluje exact SHA v aktuální konverzaci; schválení tasku tento souhlas nenahrazuje.

Task pouze nepožaduj slovně: před research/action flow jej ověř nebo skutečně
vytvoř/reuse přes `mc-task-api/scripts/cc_task.py create-task` podle
`~/.openclaw/cs-skills/_lib/cso_task_flow.md`. Stabilní klíč je
`sales-scout:task:<contact-or-company>:<sourceEventId-or-inputHash>` a stejné
webhook opakování musí dostat stejné vrácené `task.id`.

- **Chybí identifikátor firmy** → skript skončí chybou (exit kód 3), nezeptá se.
- **Existuje úspěšně provedený brief mladší 60 dnů** (`delivery_state: succeeded`) → idempotentně vrátí původní plan/readback evidence a skončí. Pouze zmrazený nebo nejednoznačný plán se nesmí vydávat za hotovou CRM poznámku.
- **Kontakt v CliqSales CRM neexistuje** → žádná externí akce; helper atomicky uloží `/documents/sales/scout-review/<taskId>-brief.md` a task použije `sales-scout:brief-review`. Vytvoření kontaktu je deaktivovaná future capability.
- **Webhook nedodal produkt + máš víc Product DNA** → udělej **multi-product brief** pro top 1–3 fitující.

**Žádné improvizace.** Market/source policy načti přes
`python3 {baseDir}/scripts/market_context.py market-plan --market <MARKET>` a
výzkum veď podle `{baseDir}/references/research-zdroje.md`. Placené
Apify/LinkedIn/Google Places zdroje v této verzi vynech; compatibility helper
zůstává fail-closed. Pro CRM plán používej jen `scripts/ghl_scout_push.py` a
`~/.openclaw/cs-skills/_lib/sales-ghl-plan-workflow.md`; žádný ruční provider POST.

**Žádný vlastní inline Python** s `bs4`, `requests`, `selenium`, `playwright` — knihovny **NEJSOU** v prostředí dostupné. Používej `web_fetch`, `browser` a stdlib + helper skripty ze `scripts/`.

## Co tento skill dělá pro váš byznys

Obchodník nemá zvedat telefon naslepo. Dostane brief, ve kterém už **před prvním kontaktem** vidí, s kým mluví, jakou má firma velikost, zda není v insolvenci, jaké jsou nejnovější novinky a — co je nejdůležitější — **jaký z vašich produktů na firmu sedí**, jakým úhlem ji oslovit, jaký e-mail napsat a jaké otázky položit při hovoru.

Skill řeší tři typické nepříjemnosti pre-sales fáze:

1. **„Obchodník se ptá zákazníka na věci, které si mohl dohledat sám."** Skill projde veřejný web a registry povolené pro konkrétní market a doloží zdroje. Zákazník při prvním hovoru ví, že obchodník přišel připravený.
2. **„Lead přišel přes formulář a nikdo s ním nezačal pracovat 4 hodiny."** Skill může automaticky připravit brief a exact CRM plán; obchodník jasně vidí, zda plán čeká na souhlas, nebo byl prokazatelně proveden.
3. **„Máme 3 produkty a obchodník neví, který nabídnout."** Skill posoudí fit firmy pro každý váš produkt (A/B/C grade) a vybere top 1–3 nejvhodnější. Doporučí konkrétní úhel pro každý.

## Co vám skill dodá

**Výstup:** Rich Text brief a zmrazený plán poznámky; volitelně závislý aditivní tag. Poznámka v CRM existuje až po `status: complete` a úspěšném readbacku.

**Žádné trvalé brief soubory na disku.** Audit zaznamenává plan action ID, `planSha256` a `delivery_state` do `/documents/sales/.scout-history.jsonl`; zmrazený plán se nesmí zaměnit za provider readback.

## Vstup — co skill potřebuje

**Webhook režim** dostane formátovaný text v promptu (formátování dělá webhook v Control Center / CliqSales workflow):

> *„Udělej Scout brief na nový kontakt: market=SK, jméno=Marek Novák, email=marek@firma.sk, firma=Firma s.r.o., web=https://firma.sk, telefon=+421 901 234 567, contactId=abc123, product=produkt-a."*

**Manuální režim** přijme libovolnou kombinaci údajů v běžné větě:

- *„Scout brief na Firma Alfa s.r.o. pro Produkt A"* (firma + produkt)
- *„Scout na Marka Nováka z Firma Alfa"* (osoba + firma, produkt si Scout vybere automaticky)
- *„Brief na info@firma.cz, nabízíme Produkt A"* (e-mail + produkt)
- *„Brief na kontakt z CRM abc123def456"* (přímo contactId)

**Minimální vstup:** alespoň jeden identifikátor firmy (e-mail, web, název
firmy, registry ID nebo `contactId`). Market převezmi z validovaného
Prospector řádku nebo explicitního vstupu. Pouze kvůli kompatibilitě starého
CZ webhooku platí: chybějící market = `CZ` a v briefu jej označ jako
`legacy_default`; jiný trh se z TLD ani telefonu neodhaduje.

Postup extrakce údajů v `{baseDir}/references/prompt-parsing.md`. Postup identifikace produktu v `{baseDir}/references/product-context.md`.

## Jak skill pracuje — 8 kroků (research a plán autonomní; execution schvaluje uživatel)

### Krok 0 — Rozbalení vstupu

Vytáhne z prompt textu (regex + LLM uvažování):

- Jméno, příjmení (převést do 1. pádu pouze pro brief)
- Firma
- E-mail, telefon, web
- `market`, `registry_id_type`, `registry_id` a původní source provenance
- `contactId` (pokud webhook)
- **`product` slug** (pokud explicitně uveden)

Validace: spusť `market_context.py market-plan` s explicitním nebo legacy CZ
marketem. Neznámý market nebo chybějící identifikátor firmy znamená exit 3;
český ARES není fallback.

### Krok 0.5 — Identifikace produktu

Načti `scripts/load_product_dnas.py` → vrátí list všech Product DNA z `/documents/brand/products/*/productDNA.md`.

Rozhodovací logika:

| Vstup z Krok 0 | Počet Product DNA | Akce |
|---|---|---|
| `product=X` v promptu | irelevantní | použij ten (`product_mode = "single"`) |
| Bez produktu | 0 | exit kód 4 + zpráva *„Žádný Product DNA v /documents/brand/products/. Vytvoř aspoň jeden přes product-dna."* |
| Bez produktu | 1 | použij ten automaticky (`product_mode = "single"`) |
| Bez produktu | 2+ | **multi-product režim** (`product_mode = "multi"`): v Kroku 5 spočti fit pro každý produkt, vyber top 1–3 |

Detail v `{baseDir}/references/product-context.md`.

### Krok 1 — Kontrola opakovaného briefu (idempotence)

Ještě před research spusť `python3 {baseDir}/scripts/ghl_scout_push.py --check-cache --contact-id <id> --history-path /documents/sales/.scout-history.jsonl` (bez ID použij `--email`). Helper načte historii a u `plan_frozen` zkontroluje kanonický execution journal podle `planSha256`. Teprve note akce se stavem `succeeded`, provider receipt a readbackem povýší novým auditním řádkem na cache hit. Chybějící, neprovedený nebo `outcome_unknown` plán není hotový brief. Historické neprázdné `ghl_note_id` zůstává kompatibilní.

**Pokud shoda existuje:**

- Vrať JSON `{success: true, cached: true, contactId: ..., plan_action_ids: [...], skip_reason: "úspěšný brief mladší 60d"}`
- Skonči (exit 0).

**Pokud uživatel chce vynutit nový brief:**

- Manuální režim: v promptu řekne *„refresh"*, *„aktualizuj"* nebo *„nový brief"*
- Webhook režim: payload má `refresh=true`
- → Krok 1 se přeskočí a pokračuje se na Krok 2

### Krok 2 — Identifikace firmy

Použij registry ID/source provenance z Prospector řádku, pokud existují. Pokud
market policy nabízí `registry_verification`, znovu je přes tuto roli ověř.
Pokud ji nenabízí, event/VAT/web důkaz za plný registry výpis nevydávej. Bez
Prospector vstupu hledej firmu pouze zdroji/rolemi vrácenými `market-plan`.
`scripts/ares_lookup.py` je platný jen pro `market=CZ`; pro SK nebo ES jej
nikdy nespouštěj.

Z registry zdroje ber jen skutečně vrácené identifikační údaje, sídlo, právní
formu, datum vzniku a stav. Chybějící pole dober z veřejného firemního webu,
ne z LinkedInu ani z odhadu. Rozpor zdrojů viditelně popiš.

### Krok 3 — Paralelní výzkum

Spusť souběžně jen relevantní role vrácené market policy:

- veřejný web firmy pro nabídku, reference, tým a kontakt;
- registry verification/event a risk verification pro daný market;
- veřejné RSS a platformní webové hledání pro čerstvé signály;
- rozhodovače pouze z veřejného webu firmy.

Browser smí následovat jen po prázdném JavaScriptovém shellu na firemním webu,
ne po 403/429. Každé podstatné tvrzení nese source URL a čas ověření.

**Apify/Places/direct-provider útrata v této verzi musí být přesně 0.**
Compatibility helper končí `metered_action_type_unavailable`; přímý token nebo
provider call je zakázán.

Pravidla anti-bot v `{baseDir}/references/browser-strategie.md`. Pravidla výběru zdrojů v `{baseDir}/references/research-zdroje.md`.

### Krok 4 — Strukturování briefu (společné sekce)

Naplň společné sekce briefu podle `{baseDir}/references/brief-sablona.md`:

- Sekce 1 — Základní údaje
- Sekce 3 — Relevantní signály z veřejných podkladů (na konec sekce patří blok **„Na koho jít"** — rozhodovači z kroku C2: jméno, pozice, doba ve firmě; jen pokud C2 běžel)
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

### Krok 6 — Auditní log (zapisuje výhradně helper)

Auditní řádek do `/documents/sales/.scout-history.jsonl` zapisuje **jen `ghl_scout_push.py`** v Kroku 7. Zapisuje action ID, cestu plan artefaktu, `planSha256` a `delivery_state`; pouze `succeeded` (nebo historický neprázdný `ghl_note_id`) je hotová CRM poznámka. Předej `--product-mode`, `--products`, `--fit-grades`, `--mode`, `--task-id` / `--source-run-id`, stabilní `--idempotency-key` a kanonický `--plan-artifact`.

### Krok 7 — Vytvoření a potvrzení CRM plánu

Spusť `python3 {baseDir}/scripts/ghl_scout_push.py`:

**Webhook režim (máme contactId):**
```bash
python3 ghl_scout_push.py --market SK --contact-id abc123 --note-body-file /tmp/brief.md \
    --idempotency-key "sales-scout:brief:123:abc123" \
    --plan-artifact /documents/sales/ghl-plans/scout/123-brief.json \
    --create-plan --task-id 123
```

**Manuální režim (exact lookup; nenalezený kontakt zůstane file/review-only):**

Exact e-mail/telefon pro mutation target se neodvozuje ze singular duplicate
endpointu. Shared helper projde bounded PIT-compatible contact search, vyžaduje
stabilní total, unikátní ID a právě jednu lokálně exact shodu. Více shod,
neúplnost nebo limit 10 000 znamená STOP a požadavek na explicitní `contactId`.
```bash
python3 ghl_scout_push.py --market SK --email marek@firma.sk --first-name Marek --last-name Novák \
    --company "Firma Alfa" --note-body-file /tmp/brief.md \
    --idempotency-key "sales-scout:brief:123:marek-firma" \
    --plan-artifact /documents/sales/ghl-plans/scout/123-brief.json \
    --create-plan --task-id 123
```

Helper sám:

1. `--create-plan` vyžaduje kladné `--task-id`; bez task provenance helper plán nevytvoří.
2. Přes named tenantní read helper najde právě jeden kontakt podle `contactId`, e-mailu nebo telefonu. Secret načte strict resolver a nikdy jej nevypíše.
3. Pokud kontakt prokazatelně neexistuje, vrátí `fileReviewOnly: true`, uloží review brief a nevytvoří žádný plán. Task nastav na `sales-scout:brief-review`.
4. Pokud kontakt existuje, konvertuje MD → bezpečné GHL HTML a zmrazí `sales.ghl.note.create.v1` a `sales.ghl.tags.add.v1`.
5. Tag vždy závisí na note action ID stejného plánu; externí dependency se nepřijímá.
6. Tag je aditivní delta `sales scout`; nikdy nenahrazuje celé pole tagů.
7. U existujícího kontaktu vrátí `complete: true`, note/tag action ID a `planSha256`; u nenalezeného kontaktu plán nevytváří.

Stejný plán po chybě neopakuj. U `outcome_unknown` ručně ověř GHL; oprava znamená nový plán a nový souhlas.

Ukaž celý souhrn a exact SHA. Po explicitním souhlasu v aktuální konverzaci proveď plán podle `~/.openclaw/cs-skills/_lib/sales-ghl-plan-workflow.md`. Nenalezený kontakt nemá action flow.

V task flow nastav metadata `contract: "sales-scout:brief-actions-v1-4"` a
`contractParams: {}`. Varianta používá built-in `{taskId}` a ověří
`/documents/sales/ghl-plans/scout/{taskId}-brief.json`; do review přejdi až
po `complete: true`. Webhook bez existujícího CSO tasku tento kontrakt ani
plán nevytváří. Nesuffixovaný `brief-actions` zůstává pouze pro již bindované
tasky 1.3 a nikdy se nepřepisuje.

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
| Pustit `web_fetch` nebo `browser` na LinkedIn | `web_fetch` vrátí prázdnou kostru; browser = captcha/login wall a riziko blokace IP. | LinkedIn v této verzi vynech. Apify helper je fail-closed do zavedení typed metered action. |
| Obejít `metered_action_type_unavailable` přímým Apify POSTem/tokenem | Obchází CC rozpočtovou hranici a může utratit kredit bez souhlasu. | Zdroj vynech a vykazuj útratu 0 $. |
| Pokračovat po detekci captcha / login wall (web firmy) | Další pokusy = blokace IP. | Zdroj ukonči a pracuj jen s ostatními bezplatnými podklady. |
| **Považovat autonomní research za souhlas se CRM zápisem** | Obejde lidské schválení konkrétního payloadu. | Research/plán může být autonomní; execute až po souhlasu s exact SHA. |
| **Vytvořit dynamický tag** (s datem, fit gradem, produktem) | Tisíce unikátních tagů v CliqSales = nepřehled. | Jediný tag `sales scout` (lowercase, s mezerou). Vše ostatní zůstává v textu poznámky. |
| **Ukládat brief jako MD soubor** do `/documents/sales/scout-briefs/...` | Tisíce souborů zaplaví disk při velkém objemu webhooků. | Brief jen do CRM. Audit jako 1 řádek v `/documents/sales/.scout-history.jsonl`. |
| **Použít headings (H1–H6), tabulky, code blocks** v brief textu | GHL Rich Text v poznámkách je nepodporuje — v UI se zobrazí jako plain text. | Jen bold, kurzíva, bullet/numbered listy, hyperlinky. Pravidla v `ghl-html-konverze.md`. |
| Volat `ghl_scout_push.py` **bez konverze MD → HTML** | Poznámka se uloží jako raw Markdown text — v UI uvidíš `**bold**` doslovně. | Helper sám konvertuje. Pošli mu MD body, on udělá zbytek. |
| **Považovat `plan_frozen` za hotový brief** | Připravený plán není CRM poznámka. | Cache jen řádek `delivery_state: succeeded` podložený execution readbackem. |
| Volat GHL ručně mimo helper | Obejde exact SHA, journal a zákaz opakování. | Reads i writes pouze přes `sales_ghl_plan.py`; write až po souhlasu s plánem. |
| Použít `web_fetch` na SPA stránce firmy (React / Next / Vue) | Vrátí prázdný `<body>` — sekce „Co dělají" v briefu zůstane prázdná. | Pokud HTML pod 1500 znaků → náhradně `browser`. |
| Zpracovávat víc kontaktů paralelně (batch mode) | Tento skill je pro **jeden kontakt**. Batch by zaplavil registry, webové zdroje a GHL reads. | Prospector výběr zpracuj jako jednotlivé bounded Scout tasky. |

## Návaznost na další skilly

**Vstup z:**
- Webhook z CliqSales CRM při příchodu nového kontaktu (primární trigger v produkci)
- `sales-prospector` — předává normalizovaný market, registry ID a provenance z
  vybraného řádku `prospects.csv`
- Manuální spuštění z chatu obchodníka / manažera

**Předává výstup do:**
- `aiq-strategy-generator` — Scout brief je vstup pro stavbu personalizované prodejní cesty
- `sales-analytik` — smí spojovat brief s výsledkem až po existenci explicitního
  CRM admission/link; samotný file-only kandidát není konverzní evidence

## Doplňkové soubory (reference)

- `{baseDir}/references/research-zdroje.md` — aktivní zdroje, provenance a STOP podmínky
- `{baseDir}/references/brief-sablona.md` — struktura 11 sekcí + vyplněný příklad (single i multi-product)
- `{baseDir}/references/prompt-parsing.md` — pravidla extrakce údajů z prompt textu (regex + LLM)
- `{baseDir}/references/browser-strategie.md` — pravidla pro `browser` tool (pauzy proti robotům, detekce captcha, časové limity)
- `{baseDir}/references/product-context.md` — jak Scout načte a použije Product DNA, multi-product logika
- `{baseDir}/references/ghl-html-konverze.md` — pravidla konverze Markdown → GHL Rich Text HTML

## Bezpečnost a citlivá data

- **Přístupové údaje k CliqSales:** načítá pouze sdílený strict resolver ze store; secret se nikdy nevypisuje ani neukládá do plánu.
- **LinkedIn/Apify:** v této verzi vypnuto. Compatibility helper nenachází token a truthful odmítne placený běh.
- **GDPR:** skill pracuje s veřejně dostupnými údaji a exact bounded CRM lookupem. Nejasný lookup zastaví všechny navazující akce.
- **Idempotence:** každá plan action má stabilní business key a payload SHA. Ztracená write odpověď znamená `outcome_unknown` a nikdy se automaticky neopakuje.
- **Ochrana proti robotům:** browser jen na weby firem, okamžitý stop při captcha; žádný placený fallback.
