---
name: content-performance
description: "Týdenní vyhodnocení obsahu: stáhne engagement ze Social Planneru a čtenost, konverze a pozice z Google Analytics a Search Console, sestaví týdenní report v lidské řeči, plní zlatý fond ověřených témat a přeskóruje zásobník nápadů. Engine se díky němu každý týden zpřesňuje."
category: integrations
status: ready
version: "2.0"
publishedAt: "2026-07-06"
metadata: {"openclaw":{"emoji":"📈"}}
---

# Content Performance

Učící vrstva obsahového enginu. Jednou týdně (pravidelný úkol) nebo na vyžádání („jak se dařilo obsahu?") vyhodnotí, co fungovalo, a promítne to zpět do rozhodování: **zlatý fond**, **přeskórování backlogu**, **doporučení pro další plán**. Sám nic nepublikuje ani nemaže.

Klientovi nikdy nevykládej architekturu — dostává jen srozumitelný týdenní report s čísly a doporučeními.

## Kdy běží

- **Pravidelně: 1× týdně** (viditelný pravidelný úkol v Control Center: „Týdenní vyhodnocení obsahu"). Konkrétní den nevynucuj — naplánuj týden od aktivace; když klient řekne „posílejte mi to v pondělí", jen přeplánuj úkol.
- **Na vyžádání:** „jak se dařilo obsahu?", „co tento týden fungovalo?", „vyhodnoť obsah za měsíc" (uprav okno).

## 1 · Sběr dat (posledních 7 dní + srovnání s předchozím týdnem)

| Zdroj | Co bereš | Když chybí |
|---|---|---|
| **Social Planner (CliqSales/GHL)** | publikované posty + engagement (reakce, komentáře, sdílení, dosah je-li k dispozici) | přeskoč sekci social, poznamenej |
| **google-analytics** (GA4) | čtenost článků, organická návštěvnost, konverze/poptávky z obsahu | přeskoč web čísla, poznamenej |
| **google-search-console** | dotazy, pozice, imprese, CTR per stránka | přeskoč SEO sekci, poznamenej |
| `/documents/content/content-log.md` | co a kdy vyšlo (párování výkonů na témata) | bez logu jen surová čísla + upozornění |

Vždy pracuj s tím, co je — chybějící zdroj nikdy neblokuje report.

## 2 · Vyhodnocení

1. **Spáruj čísla s tématy** přes `content-log.md` (datum + kanál + téma + odkaz).
2. **Označ top a flop:** top = výrazně nad mediánem týdne (např. 2× medián engagementu / čtenosti), flop = výrazně pod. Malé vzorky (1–2 kusy) nehodnoť jako trend.
3. **Zlatý fond** — top-performer zapiš/aktualizuj v `/documents/content/evergreen.json`:

```json
{
  "items": [
    {
      "topic": "Kolik stojí AI agent pro malou firmu",
      "channel": "blog",
      "url": "https://…",
      "publishedAt": "2026-07-01",
      "metrics": {"readers7d": 412, "engagement": 56, "leads": 4},
      "whyItWorked": "konkrétní čísla v titulku + otázka, kterou zákazníci reálně pokládají",
      "lastRecycledAt": null
    }
  ],
  "lastUpdated": "YYYY-MM-DD"
}
```

`whyItWorked` je povinné — bez příčiny je zlatý fond jen seznam odkazů.

4. **Přeskóruj backlog** (`/documents/content/ideas.json`): nápadům podobným top tématům zvyš skóre, podobným flopům sniž. Ke změně přidej poznámku proč (auditní stopa).
5. **SEO rychlé výhry (striking-distance):** z GSC vyber dotazy na pozicích **8–25** s nadprůměrnými impresemi a nízkým CTR → doporučení „vylepšit existující stránku" (předává se `seo-strategist`u, klientovi jen lidsky: „malou úpravou stránky X můžete rychle získat návštěvnost").

## 3 · Týdenní report (výstup pro klienta)

Ulož do `/documents/content/reports/YYYY-WW.md` a pošli zprávou. Formát — krátký, lidský, vykání:

> **Obsah tento týden** 📊
>
> - **840 čtenářů na blogu** (+12 % oproti minulému týdnu)
> - Nejlepší kus: *„[téma]"* — 56 interakcí, 4 poptávky
> - Publikováno: 3 posty, 1 článek, 1 newsletter
>
> **Co z toho plyne:** [1–2 věty — např. „Témata s konkrétními čísly v titulku fungují nejlépe — příští týden jich zařadíme víc."]
>
> **Rychlá výhra:** stránka *[X]* je na 9. pozici na dotaz *„[dotaz]"* — drobná úprava ji může dostat do top 5. Mám to připravit?

Pravidla reportu:
- Maximálně ~10 řádků. Žádné tabulky metrik, žádná skóre, žádné názvy skillů.
- Vždy aspoň jedno **doporučení s nabídkou akce** („Mám to připravit?").
- Když je dat málo (první týdny), řekni to na rovinu: „Zatím sbíráme data, první trendy uvidíme za 2–3 týdny." Nevymýšlej si čísla.

## 4 · Zpětná vazba do enginu

Po každém běhu platí: `evergreen.json` aktualizovaný, `ideas.json` přeskórovaný, report uložený. `content-strategist` (režimy PLÁN i AUTOPILOT) z těchto souborů čte automaticky — žádné další předávání není potřeba.

## 5 · Wiki (AI Data Center) — když je k dispozici

Všechny kroky s elegantním fallbackem: když wiki nebo typ karty „Obsah" na instanci ještě neexistuje, přeskoč je BEZ chyby a klientovi nic nehlas.

1. **Souhrn:** týdenní report předej i jako task výstup — Wiki Manager z něj vytvoří Souhrn „Obsah — týden N" (a Daily Pulse z něj může citovat).
2. **Výkonové claims:** na karty Obsah dotčených kusů přidej týdenní výkon (čtenáři · engagement · poptávky) — **max 1 zápis na kus a týden** (Historie karty musí zůstat čitelná).
3. **Zlatý fond:** nové položky `evergreen.json` označ na příslušné kartě Obsah jako ⭐ — wiki je zrcadlo, provozní pravda zůstává v souboru.
4. **Zmínky obsahu:** vytáhni z wiki zmínky publikovaných kusů v hovorech/e-mailech za posledních 7 dní → do reportu přidej řádek: *„Obsah zazněl v N obchodních konverzacích."* — nejsilnější důkaz dopadu obsahu.

## Data

```text
/documents/content/evergreen.json       # zlatý fond (zapisuje TENTO skill)
/documents/content/ideas.json           # backlog — přeskórování
/documents/content/reports/YYYY-WW.md   # týdenní reporty
/documents/content/content-log.md       # čtení: párování výkonů na témata
```

## Failure handling

- Jediný dostupný zdroj = Social Planner → report jen ze social čísel + věta „Až připojíme webovou analytiku, uvidíte i čtenost a poptávky."
- Žádná publikace v okně → krátká zpráva „Tento týden nic nevyšlo" + nabídka naplánovat obsah (odkaz na režim PLÁN).
- GA4/GSC vrací chybu autorizace → přesná chyba do reportu pro Pavla/tým, klientovi jen „webová čísla tento týden nemáme k dispozici". Nikdy netipuj příčinu.
- Nekonzistence log vs. realita (post v Planneru, který není v logu) → doplň log zpětně a poznamenej to.
