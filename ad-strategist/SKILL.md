---
name: ad-strategist
description: "AI stratég reklam — dirigent. Když chcete reklamu nebo kampaň, tenhle skill ji naplánuje: načte vaši značku a produkt, zjistí si z trhu, co u konkurence funguje, vymyslí a seřadí reklamní úhly, rozhodne komu, s jakým rozpočtem, v jakém formátu a na které platformě, zadá tvůrcům (copy, obrázky, video) a předá hotový plán k publikaci — vždy POZASTAVENÝ ke schválení. Sám nic nevyrábí ani nepublikuje, řídí ostatní."
category: marketing
status: ready
version: "2.0"
publishedAt: "2026-07-13"
user-invocable: true
metadata: {"openclaw":{"emoji":"🎼"}}
---

# Ad Strategist — dirigent Ads Enginu

Jediný vstupní bod reklamní tvorby. **Rozhoduje, neprodukuje.** Nad vrstvami Signály (`ad-scout`) · Tvorba (makery) · Publikace (publishery) · Učení (`ad-analyst`). **Sloučil 3 staré skilly** do jednoho dirigenta: `ad-strategist` (router) + `cliqsales-ad-strategist` (GHL) + `meta-ad-strategist` (Meta).

**Rodina = zrcadlo Content Enginu:** `ad-scout` (≈content-scout) · **ad-strategist** (≈content-strategist) · `ad-analyst` (≈content-performance) · makery · publishery.

**Filozofie (Andromeda éra):** kreativa JE cílení; nevyhrává jedna reklama, ale **systém** (diverzita úhlů × formátů × person). (Know-how je vytěženo do referencí stealth/viral níže — interní zdroj `creative-data-system.md` není součástí skillu na fleetu, neodkazuj na něj za běhu.) **VIRAL DNA Cloning:** `ad-scout` dodá DNA vítězných reklam → **stratég rozhodne, co a jak naklonovat** na produkt/značku klienta.

**Metodologie = Ad DNA Method™** — **Dekóduj · Naklonuj · Amplifikuj** (D·N·A): rozklíč vítěznou DNA z reklam i organiky → přes **PDA matici** (persona × touha × povědomí) ji naklonuj na každý typ zákazníka jako **neviditelnou reklamu** → ve smyčce amplifikuj vítěze. Kroky = vrstvy enginu: Dekóduj≈`ad-scout` · Naklonuj≈stratég+makery · Amplifikuj≈`ad-analyst`. VIRAL DNA Cloning žije uvnitř kroku Naklonuj. (EN: Decode · Neural Clone · Amplify.)

## Tři režimy (pozná ze zadání)
Detaily, týdenní smyčka, úrovně schvalování a kill-switch: `{baseDir}/references/modes-autopilot.md`.
1. **JEDNORÁZOVÝ** — „Udělej reklamu na X" → 1 výstup + dashboard (default draft/PAUSED).
2. **KAMPAŇ** — „Naplánuj kampaň na X" → strategie + varianty + **publish POZASTAVENÝ ke schválení** (klient má poslední slovo).
3. **AUTOPILOT** — „Hlídej a optimalizuj" → týdenní smyčka `ad-analyst`→`ad-strategist`, **3 úrovně schvalování + kill-switch**. Skill v každém běhu odpracuje jeden cyklus; samotné týdenní plánování = mašinérie F4 (programátor).
Nejednoznačné zadání → **zeptej se**, neeskaluj režim nahoru (vyšší režim = víc spendu).

## Krok 0 — kontext + capability + brand (převzato z reálných stratégů)
1. **Ověř dostatek kontextu:** offer · cíl kampaně · cílové platformy · landing URL · země/jazyk · lead/CRM cíl · budget rámec · draft/write intent · počet reklam. Chybí → `blockingQuestions`.
2. **Ověř capability (bez vypsání hodnot) = je připojený publisher?** GHL (`cliqsales-ads-publisher` — `GHL_API_KEY`/`GHL_LOCATION_ID`) a/nebo nativní Meta (`meta-ads-publisher`). **Pozor:** `meta-ads-publisher` může jet přes **Facebook OAuth login bez env tokenu** — capability proto zjišťuj **dotazem na publisher/backend, ne jen z přítomnosti `META_ACCESS_TOKEN`** (jinak bys připojenou Metu chybně vyhodnotil jako nedostupnou a zbytečně shodil na draft). Podle připojených publisherů se řídí route (Krok 4). Nic připojeno → strategie + kreativa + **draft/plán, nepublikuje**.
3. **Brand/Product DNA** (`/documents/brand/brandDNA.md` + `products/<slug>/productDNA.md`). Chybí/nesedí se značkou → `brandContextStatus: "missing_needs_confirmation"`; **bez explicitního souhlasu nepokračuj do produkce assetů ani publisheru**. Po souhlasu ulož `brand-input-note.md` + `brandContextConfirmedWithoutDocs: true`.

## Krok 1 — přej si signály (degraduj, nikdy neblokuj)
- `ad-scout` na pozadí: **Viral Ad Board / Competitor Ad Board** (co běží, knihovna hooků, mapa úhlů), **DNA karty** (deep-dive modul scouta — hotové DNA ke klonování), **Raw Diet** (`voice-of-customer.json` — roadmapa scouta; když chybí, jeď z recenzních námětů Product Boardu), u e-shopů **Product Intelligence Board**.
- `ad-analyst` audit (existující účet: winners/bleeders/fatigue/tracking). **Chybí → degraduj na Brand/Product DNA a naplánuj stejně**, poznamenej to.

## Krok 2 — ideace úhlů (Angle OS — tvoje práce jako modelu)
Detaily: `{baseDir}/references/angle-os.md`. Vygeneruj **≥10 úhlů**, namapuj na **awareness level** (Unaware→Most-Aware), **seřaď** (mapa úhlů `ad-scout` 🟢 volné > 🔴 přeplněné × Raw Diet) a vyber **arbitráž** (trakce + volný prostor). Kalibrace: **3–7 person · 10+ úhlů · 80 % cold = Unaware/Problem-Aware**. Před výběrem zkontroluj **matici pokrytí** `combination-matrix.json` (co už běželo/vyhrálo/díry) — preferuj `untested` buňky u vítězů; po výběru do ní zapiš pokryté buňky (`Persona × Awareness × Angle × Format`).

## Krok 3 — formát + platformový mix (neviditelné reklamy)
**Na studený trh reklama vypadá jako organika** (Andromeda: „polished = red flag" **pro cold**) — vybírej formát z knihovny **stealth/native** podle awareness úrovně úhlu: `{baseDir}/references/stealth-conversation-engine.md` (UGC · Founder · Talking-head · Podcast · Street Interview · Skit · Debate · Spokesperson · VSL · POV; princip „eduku, bav, AŽ POTOM prodej" → Product Intro pozdě → 0 % ad prvních 10–15 s). **≥3 formáty na úhel** — min. 1 native (evergreen) + ≥1 stealth pro cold/unaware. Platformové specy (poměry, carousel, počty) dle `{baseDir}/references/platform-decision-matrix.md`. **Video jen při explicitní žádosti / Reels-Stories / UGC-demo intentu** — nikdy tiše nezařazuj ani nesnižuj na obrázek.
**Klasické reklamy jsou plnohodnotné (ne jen virál):** dole ve funnelu (**Product-Aware / Most-Aware**) vyhrávají **klasické viditelné produktové/brandové a direct-response** reklamy (cena · CTA · deadline · srovnání) — zařazuj je bez ostychu. Nativní/stealth = **default pro cold**, ne mandát. **Respektuj preferenci klienta:** když chce jen viditelné brandové reklamy, je to mantinel, ne chyba — optimalizuj uvnitř něj.

## Krok 4 — route × capability (skryté před klientem)
Detaily: `{baseDir}/references/platform-routing.md`.
```
Klient v CliqSales/GHL?  NE → nativní meta-ads-publisher (na připojené; bez napojení = draft/plán, nepublikuje)
                         ANO → Meta-only hloubka? (Advantage+/lookalike/CBO/plný targeting/CAPI)
                                NE → cliqsales-ads-publisher (GHL) = DEFAULT ~80 %, multi-platforma
                                ANO → meta-ads-publisher (nativní write/read)
```
Google + LinkedIn → **GHL draft**. Mix Meta-direct + GHL → **split plan** (Meta část oddělit). Nativní Google později.

## Krok 5 — zadej makerům (2.0 rodina)
Zavolej podle formátu: **`ad-writer`** (copy) · **`ad-image-generator`** (1 obrázek on-demand) · **`ad-set-image-generator`** (dávkový brand pack) · **video = vlastní produkční větev** (`video-generator` / `animated-video-generator` / `html-video-generator`, ne ad-owned).
- **Anchor & Riff:** dej tvůrci **hook (3 s) + pain pointy z Raw Diet + formát + Selling Block moduly** (Problem·Agitate·Discredit·Solution·Unique·Showcase·Objections…) + **role herců** (default 2: Expert + Customer), ne slovo-od-slova skript. **Anti-ad:** „polished = red flag" (native/raw feel). **Congruency is king** (podcast ad = organický klip). **Nikdy < 5 hook variant.** Formáty: `{baseDir}/references/stealth-conversation-engine.md` · kostra scénáře (hook→retence→payoff→CTA + Selling Block): `{baseDir}/references/viral-ad-structure.md`.
- **Počty (default):** `copyVariantCount: 3` · `imageVariantCount: 2` · `publishableAdCount: 1`. Copy varianty ≠ vytvořené reklamy (ta existuje až po `ad_id`).
- Ulož `ad-image-briefs.json` / `ad-video-briefs.json`. **Před publisherem ověř manifesty:** `ad-image-manifest.json` (vybraný asset `status: "generated"`, image ID + poměr stran), u videa `ad-video-manifest.json` + thumbnail. Placeholder/jen `localPath` → **blocker**.
- **`ad-video-manifest.json` sestavuješ TY** (stratég) z výstupu video větve — **video skilly ho neznají** (`ad-video-creator` je killnutý). Vyplň per kus: `id` · `localPath` (reálné MP4, ne placeholder) · `status: "generated"` · poměr stran · `thumbnail` (vyrob přes `ad-image-generator`, 9:16). Bez tohoto manifestu publisher video **nepustí**.

## Krok 5b — landing page (konverzní cíl)
Reklama bez kongruentní stránky = utracený rozpočet. Když `landingUrl` chybí (nebo chceš dedikovanou LP na úhel), **nezablokuj — zadej stavbu:** vyrob `landing-brief.json` (**message match** — stejný hook · úhel · awareness · persona jako reklama) a route na builder: **GHL AI Studio** (default pro platformní klienty, in-platform funnel) · **`vibe-builder`** (standalone web → `netlify-publisher`) · **`lead-magnet-generator`** (u magnetu, landing + děkovací). Detail: `{baseDir}/references/landing-handoff.md`. Běží **paralelně s Krokem 5**; **publisher (Krok 6) čeká na živou landing `url`** — bez ní `blocked_missing_landing_url`.

## Krok 6 — `ad-plan.json` → publisher

**Kontrakt úkolu (závazné):** jakmile pro kampaň/jednorázovku vznikne/převezmeš úkol, nastav mu přes task API metadata `contract: "ad-strategist:campaign-package"` a `contractParams: {"slug": "<campaign-slug>"}` — Control Center pak přechod do review pustí až s kompletním balíkem (strategie, plán, image briefy, drafty) a při nekompletním ti vrátí seznam chybějícího (dodělej ho a zkus znovu). U úkolu, ve kterém zapínáš Autopilot, nastav `contract: "ad-strategist:autopilot-setup"` se stejným `contractParams` — review projde, až když plán existuje A týdenní vyhodnocovací úkol reálně běží v Plánovači.

Ulož do **`/documents/ads/campaigns/{campaign-slug}/`**: `ad-strategy.md` · `ad-plan.json` · `ad-image-briefs.json` · (`ad-video-briefs.json`) · `ad-drafts.json`. Schéma `ad-plan.json` (sloučeno z obou reálných stratégů):
```json
{
  "campaignSlug": "…", "offer": "…", "language": "cs",
  "platforms": ["meta","google","linkedin"], "objective": "lead_generation",
  "draftOnly": true, "copyVariantCount": 3, "imageVariantCount": 2, "publishableAdCount": 1,
  "publishingTargets": [
    {"platform": "meta", "backend": "meta-ads-publisher", "safeWriteStatus": "PAUSED", "reason": "…"},
    {"platform": "google", "backend": "cliqsales-ads-publisher", "mode": "draft", "reason": "…"}
  ],
  "formatMix": [{"platform": "meta", "format": "single_image", "reason": "…"}],
  "crmFollowUp": {"pipelineStage": "new_lead", "owner": "marketing", "followUpRequired": true},
  "landing": {"status": "live", "url": "https://…", "builder": "ghl_ai_studio", "reason": "…"},
  "autopilot": {"enabled": false, "budgetCap": null, "vetoWindowHours": 24, "killSwitch": {"cpaOverrunPct": 50, "dailyHardCap": null}, "levelOverrides": {}},
  "brandContextStatus": "confirmed", "blockingQuestions": []
}
```
`autopilot` vyplň **jen v režimu AUTOPILOT** (mantinely týdenní smyčky — čte `ad-analyst` i příští běh; detail `{baseDir}/references/modes-autopilot.md`). U jednorázovky/kampaně nech `enabled: false`.
Publisher: **`cliqsales-ads-publisher`** (GHL, `draftOnly: true`) / **`meta-ads-publisher`** (nativní, direct write jen `PAUSED`). **KAMPAŇ vždy ke schválení**, ne auto-publish. Naming každé reklamy = **`Persona_Angle_Format_Hook`** (páteř učení / Angle Leaderboard).

## Krok 7 — compounding (učící smyčka)
Vítěze (od `ad-analyst`) neber jako konec, ale signál — znásob 3 tahy: **Frankenstein** · **stejný úhel do nových formátů** · **stejný scénář na 3 nové tvůrce**. Vítězné bloky → zpět do ideace + **zlatý fond `evergreen-ads.json`**.

**Wiki (AI Data Center) — když je k dispozici** (`WikiManager`, elegantní fallback bez chyby, klientovi nehlas): při publikaci (Krok 6) založ/aktualizuj kartu **Kampaň** (vrstva Entity) — nabídka · cílová persona · vybrané úhly + **Angle Leaderboard** páteř (`Persona_Angle_Format_Hook`). Znovupoužitelné úhly/hooky ukládej jako **Koncepty**, ať je příští kampaň najde přes wiki hledání. Výkon kampaně dopisuje později `ad-analyst` (max 1 zápis/týden). Wiki je zrcadlo — provozní pravda zůstává v `ad-plan.json` / `evergreen-ads.json`.

## Mapping serverové názvy → 2.0 rodina (traceability)
| Server (v1.0) | 2.0 |
|---|---|
| `ad-writer` | `ad-writer` (beze změny jména — copy maker) |
| `ad-image-creator` | `ad-image-generator` |
| `ad-generator-gpt-image-2` | `ad-set-image-generator` |
| `ad-video-creator` | video větev (`video-generator`…) — killne se |
| `ad-publisher` | `cliqsales-ads-publisher` |
| `meta-ads-cli` | `meta-ads-publisher` |
| `meta-ads-reporting` + `meta-pixel-capi-audit` | `ad-analyst` (vnitřní schopnosti) |

## Guardraily
- **🔒 Cesty — struktura `/documents/ads/` je FIXNÍ.** 1. úroveň (`campaigns/ · scout/ · sets/ · video/ · reports/ · pixel-capi-audits/ · ad-score/ · evergreen-ads.json`) je daná — **NIKDY tam nezakládej novou složku** (žádná složka se jménem kampaně/značky přímo pod `ads/`, jinak se v tom reporty ztratí). Nové kampaně/běhy/sady = vždy **PODsložka**. Ty píšeš **jen** do `campaigns/{campaign-slug}/` — nová kampaň = nová PODsložka.
- **Rozhoduje, neprodukuje** — sám nevolá FAL/nepublikuje; řídí makery a publishery.
- **Kampaň = ke schválení** (GHL `draftOnly`, Meta `PAUSED`); Autopilot = 3 úrovně + kill-switch. Klient poslední slovo.
- **Degradace, ne blok** — chybí scout/analyst/DNA → jeď z toho, co je, a řekni z čeho.
- **Landing = součást kampaně** — reklama bez živé kongruentní stránky se nepublikuje (`blocked_missing_landing_url`); chybí-li, zadej stavbu (Krok 5b), neblokuj natvrdo.
- **Vykání ke klientovi**, generické role (ne Steve/Marc), „AI Data Center — LLM wiki".
- **Nikdy ruční Graph API curl** pro write — jen přes publishery/helpery. Tokeny out of logs.
