# Vlna end-to-end — dvě půlky stroje, setup a měření

## Princip

```
PŮLKA 1 (skill):     kandidáti → judge znění → exact plán dávky → ✋ SHA souhlas
                     (nic neodesílá ani nezapisuje do CRM)
PŮLKA 2 (platforma): odpověď → Conversation AI (kvalifikace + schůzka) → obchodník/majitel
MĚŘENÍ (tagy→cron):  odesláno → % odpovědí → % schůzek → Kč v pipeline (+ opt-out %)
```

Ruční GHL volání mimo helper je **zakázané**. Skill připraví kohortu a přes `--create-plan` zmrazí nejvýše 50 exact per-recipient message/tag dvojic. Tag závisí přes `dependsOnActionId` na úspěšném message readbacku. Sdílený helper vyžaduje exact SHA + `--confirm-execute yes` a před provider dispatch znovu zkontroluje kontakt a souhlas. Plán kanálu: vlny SMS-first (má-li snapshot telefon, jinak e-mail), připomínky cyklu e-mail-first. Změna exact payloadu vyžaduje nový plán, idempotency key a souhlas.

Vlna NEPRODÁVÁ. Pošle jednu krátkou osobní otázku (reply-first, Dean Jackson): plain text, žádné odkazy, žádný pitch. Cíl = odpověď.

## Otázky vln — vzory zde, ověření vítězové v Sales DNA §10 (učitelný artefakt)

| Segment | Vzor A | Vzor B |
|---|---|---|
| A | „Dobrý den [jméno], ještě řešíte [produkt/důvod]?" | „[jméno], dlouho jsme se neslyšeli — je [téma] stále aktuální?" |
| B | „Je [téma] pro vás ještě aktuální?" | „Před časem vás zajímalo [X] — platí to ještě?" |
| C | „Chodíte ještě k [X]? / Nedáme tomu novou várku?" | „Dlouho jsme se neviděli — máme pro vás termín tento týden." |

Po vyhodnocení vlny (14 dní) se vítězné znění navrhne k zápisu do Sales DNA §10 — Ověřené poznatky (po schválení) → příští vlny začínají od vítěze. To je měřená smyčka.

## Setup u klienta (jednorázově — klient NIC nestaví)

Potřebné automatizace v GHL pro ostrý provoz: ① zákazník odpověděl → tag `vlna-reply:<slug>` (u připomínek cyklu `cyklus-reply:<produkt>`) · ② „STOP/odhlásit" → DND · ③ Conversation AI agent (AI Studio) zapnutý na inboundu s kontextem. Odeslání smí provést výhradně exact schválený Sales GHL plán.

1. **Primární cesta: fleet GHL snapshot** — hotový balík ①–③ instalovaný do sub-účtu při onboardingu.
2. **Záloha: prompt pro GHL Workflow AI builder** — dosaď konkréta a vlož do AI builderu:

> Vytvoř workflow „Reaktivace — odpověď": Trigger = Customer Replied (SMS nebo e-mail). Podmínka = kontakt má tag začínající „vlna:". Akce = přidat tag „vlna-reply" + hodnota podle tagu vlny. Druhá větev: má-li kontakt tag začínající „cyklus:", přidat tag „cyklus-reply" + název produktu z tagu.
> Vytvoř workflow „Reaktivace — STOP": Trigger = příchozí zpráva obsahuje „STOP" nebo „odhlásit". Akce = zapnout DND.

3. **Ověření:** nejdřív zkontroluj existenci inbound reply/STOP automatizací bez seed odeslání. Seed test je samostatný exact message plán na vlastní kontakt a vyžaduje souhlas s jeho SHA; nikdy ho neposílej ručním provider voláním.

## Conversation AI — kontext a taxonomie odpovědí

Agent (GHL AI Studio) dostane: kdo byl osloven a proč (segment), jaká otázka odešla, který produkt, odkaz na kalendář. Chování:
- **zájem** → 1–2 kvalifikační otázky → nabídnout termín z kalendáře → notifikace obchodníkovi
- **negativní / „nezajímá"** → poděkovat, tag, u „nepište mi" → DND
- **nejasné / mimo scénář** → předat člověku (notifikace), AI nepokračuje

**GO/NO-GO čeština:** kvalita českých odpovědí agenta se hodnotí v prvním testu. NO-GO → **human-in-the-loop režim**: odpovědi padají majiteli/obchodníkovi s AI návrhem odpovědi k odkliku. Vlna funguje dál, jen pomaleji.

## Dávkování a ramp gate

- Jeden plán obsahuje nejvýše 50 kontaktů. Agent smí spustit execute jen v pracovní době podle Sales DNA §1; helper tento klientský kalendář sám nezná.
- Další offset vznikne **až po kontrole zdraví doručení** předchozí dávky. Agent vyhodnotí execution journal a dostupné bounce/complaint signály; chybovost > 5 % znamená STOP a předání majiteli. Producer sám asynchronní bounce nevidí a nesmí tvrdit opak.

## Měření a uzávěrka vlny

- Kohorta (denominátor) = `/documents/sales/vlny/<slug>.json`. Čitatele sbírá **cron stratéga** z tagů: `vlna-reply:<slug>` (odpovědi), schůzky, dealy v pipeline Reaktivace.
- Připomínky cyklu mají VLASTNÍ kohorty `/documents/sales/vlny/cyklus-<produkt>.json` a reply tag `cyklus-reply:<produkt>` — v auditu ani měření se nemíchají s vlnami. Metriky per produkt: připomínky → odpovědi → nové nákupy; závěry po čase = návrh úprav cyklů do Sales DNA §11.
- Soubor vlny v `/documents/sales/` je automaticky dohledatelný přes CC knowledge/LLM wiki — výsledky vidí celý tým.
- **Uzávěrka po 14 dnech:** trychtýř + vítězné znění A/B → návrh do Sales DNA §10 (zapíše se po schválení; do LLM wiki se soubor dostane synchronizací AI Data Centra).
