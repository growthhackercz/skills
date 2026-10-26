# CliqSales Closing System™ — index a cheat sheet

> Proprietární prodejní closing metodika CliqSales (interní slug složky: `cliqsales-closing-system`).

Univerzální prodejní metodika pro hodnocení a přípravu hovorů. **Jádro: Belfort + Hormozi**, doplněné o **vrstvu Human-Centric** (důvěra a identita pro high-ticket). Bez SPIN/Sandler/Challenger/Voss/Cialdini (ty se do rozhodovacího jádra nemíchají). Sdílená knihovna: čte ji `sales-mentor` (hodnocení hovoru), `sales-analytik` (klasifikační slovník) a `sales-assistant` (taktická příprava na jednání).

## ⚠️ Token disciplína — čti kapitolově, ne celé

Tenhle INDEX je jediný soubor, který se čte vždy. Zbytek čti **jen relevantní kapitolu** podle potřeby (viz Retrieval pravidla). Nikdy nenačítej celý KB do kontextu.

## Retrieval pravidla (pořadí načítání)

1. Urči **fáze hovoru** a **detekované námitky** (levně, z aktuálního `MeetingInsight` v1 / přepisu) — slovník je v `TAXONOMY.md`.
2. Načti **jen** kapitoly odpovídající tomu, co v hovoru je:
   - hodnotíš hovor → `SYSTEM_PROMPT.md` + `SCORING_ENGINE.md` (+ `COACHING_ENGINE.md` pro doporučení)
   - řešíš konkrétní námitku → sekci v `hormozi.md` / `belfort.md` dle typu
   - připravuješ hovor (assistant) → `hormozi.md` (CLOSER, Value Equation) + `belfort.md` (tonalita, looping)
   - **velká / high-ticket zakázka nebo `trust_*` námitka → `human-centric.md`** (důvěra před bolestí, Identity Shift)
3. `ethics.md` čti vždy, když produkuješ skóre nebo doporučení (penalizace manipulace je povinná).
4. Nikdy nepoužij jednu obecnou techniku bez kontextu hovoru.

## Cheat sheet (90 % případů vystačí s tímhle)

**Hormozi — CO musí zákazník uvěřit, aby se rozhodl:**
- **CLOSER:** Clarify (ujasni cíl a mezeru) · Label (pojmenuj bolest jeho slovy) · Overview past pain (náklad nečinnosti) · Sell the vacation (výsledek, ne proces) · Explain away concerns (okolnosti / jiní lidé / sebe­nedůvěra) · Reinforce (zpevni rozhodnutí po „ano").
- **Value Equation:** Hodnota = (Vysněný výsledek × Vnímaná pravděpodobnost) / (Časová prodleva × Úsilí a oběť). Zvyšuj čitatel, sniž jmenovatel.
- **Belief breaking:** najdi a přerámuj přesvědčení, které brání rozhodnutí (ne argumentuj proti faktu).

**Belfort — JAK vést hovor, aby jistota vznikla:**
- **Three Tens:** jistota v Produkt · Obchodníka · Firmu (logická + emocionální). Námitka = díra v jedné z těch tří.
- **Straight Line:** drž linii od otevření k uzávěru, kontroluj rozhovor, sbírej informace.
- **Looping (5 smyček):** zvyš jistotu Produkt → Obchodník → Firma → sniž práh akce (záruky) → zvyš práh bolesti (náklad nečinnosti).
- **Tonalita** (45 % vlivu): zvědavost, absolutní jistota, rozumný člověk, nedostatek, upřímnost, samozřejmost, „cítím vaši bolest", autorita, nadšení, deklarativní otázka.
- **Prahy:** práh akce je tvárný (sniž zárukami/malými kroky); práh bolesti — dost velká bolest = koupí u kohokoli.

**Human-Centric (vrstva pro high-ticket):**
- **Trust Equity:** u velkých zakázek vybuduj důvěru DŘÍV, než otevřeš nejhlubší bolest. Bolest bez důvěry = manipulace.
- **Identity Shift:** doveď zákazníka k tomu, aby se viděl jako „člověk, který investuje do špičkových řešení". Drží retenci a LTV, ne jen uzávěr.

**Sjednocení:** Hormozi = co potřebuje uvěřit. Belfort = jak hovor vést, aby to uvěřil. Human-Centric = u velkých zakázek nejdřív důvěra a identita. Agent žádného autora mechanicky nekopíruje.

**Který framework vede (podle velikosti dealu):**
- **Straight Line (Belfort) = operační systém** vždy — kontrola linie, tonalita, jistota, looping. Na něm běží ostatní.
- **CLOSER (Hormozi)** = struktura pro transakční / menší dealy (řádově do ~5 000 USD), rychlá replikovatelnost.
- **Human-Centric** = vrstva pro high-ticket / vztahové dealy (nad ~5 000 USD), kde nátlak selhává a rozhoduje důvěra a identita.
Hlavní rizika: CLOSER → tlak na pilu · Human-Centric → časová náročnost · Straight Line → manipulace (hlídá `ethics.md`).

## Povinná pravidla (přebíjejí vše ostatní)
- **Skóre nesmí být vysoké jen proto, že zákazník koupil.** Dobrý proces může vést k oprávněnému „ne"; slabý proces může omylem prodat.
- **Evidence-first:** každý závažný závěr má citaci / úsek hovoru.
- **Etika:** manipulace se penalizuje; jasné opakované „ne" se respektuje (`ethics.md`).

## Soubory
`SYSTEM_PROMPT.md` · `SCORING_ENGINE.md` · `COACHING_ENGINE.md` · `TAXONOMY.md` · `hormozi.md` · `belfort.md` · `human-centric.md` · `ethics.md` · `schemas/scorecard.schema.json`

Verze KB: viz soubor `VERSION` (jediný zdroj pravdy) · historie a pravidla bumpu v `CHANGELOG.md` · zdroj: Closing Agent KB (Belfort + Hormozi + vybrané body Human-Centric, veřejné metodiky).
