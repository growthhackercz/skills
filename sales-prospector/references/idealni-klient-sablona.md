# Ideální klient — šablona profilu + 6 doplňujících otázek

## Doplňující otázky (záložní postup v Kroku 0, když chybí Brand DNA / Product DNA)

Pokud Brand DNA nebo Product DNA chybí, polož uživateli těchto **6 otázek** v chatu. Bez jejich zodpovězení nepokračuj na Krok 1.

1. **Pro jaký produkt / službu lovíme?** (název + 1 věta popis problému, který řeší)
2. **B2B nebo B2C?** (případně oba)
3. **Geografie?** (CZ / SK / EU / svět)
4. **Velikost cílové firmy?** (mikro <10 zaměstnanců / SMB 10–250 / enterprise 250+ / N/A — irelevantní pro B2C)
5. **Branže / vertikála?** (volné, klidně víc — např. „e-shopy s kosmetikou, drogerie, lékárny")
6. **Klíčový problém, který produkt řeší?** (1 věta — formulace zákazníka, ne marketing copy)

## Šablona profilu ideálního klienta

Po Krok 0 vygeneruj profil v tomto formátu (uložit do `idealni-klient.md` až po STOP 1 schválení):

```markdown
# Ideální klient — [Název kampaně]

**Datum:** YYYY-MM-DD
**Produkt / služba:** [název]
**Segment:** B2B | B2C | mix

## Firmografika

- **Branže / vertikály:** [seznam, ideálně + CZ-NACE kódy pro B2B]
- **Velikost:** [např. „10–50 zaměstnanců" / „obrat 5–50M Kč" / „N/A"]
- **Geografie:** [CZ / SK / EU / svět + případně konkrétní regiony]
- **Právní forma:** [s.r.o. / a.s. / OSVČ / všechny]
- **Věk firmy:** [např. „založené 2018+" / „bez omezení"]

## Technografika / produktové signály

- **Co používá / prodává / vyrábí:** [konkrétní produkt, technologie, platforma]
- **Co je signál vhodnosti:** [např. „mají vlastní e-shop na Shoptetu", „prodávají bio produkty", „mají WooCommerce"]
- **Co je signál nevhodnosti:** [např. „používá SAP", „má jednotné přihlašování pro velké podniky", „používá jen bezplatnou verzi"]

## Signály zájmu

Pokud kandidát vykazuje jeden z těchto signálů, zvyšuje to jeho prioritu:

- [Expanze — nová pobočka, nový sklad, nový trh]
- [Investice — Series A/B, M&A]
- [Nábor — hledají specifickou roli (CMO, sales, ...)]
- [Změna majitele / nový management]
- [Veřejná zakázka vyhraná v posledních 6 měsících]
- [Nedávné zmínky v tisku]

## Disqualifiers (must NOT)

Tyto firmy do ICP NEpatří — vyřaď v Krok 5:

- [Insolvence / likvidace]
- [Přímá konkurence (jmenuj)]
- [Příliš malé — pod X zaměstnanců / obratu]
- [Příliš velké — nad Y zaměstnanců / obratu]
- [Specifické branže, kam neprodáváme (např. zbraně, hazard)]

## Hledací heuristika (pro agenta)

Zhuštěná verze ICP — co agent reálně použije v Krok 2 (plán vyhledávání) a Krok 5 (pre-filter):

```
Hledej firmy:
  CZ-NACE IN [4711, 4719, 4774]
  AND obrat 5–50M Kč (odhad z webu nebo veřejných údajů)
  AND region IN [Praha, Brno, Ostrava]
  AND právní forma = s.r.o.
  AND status = aktivní (ne v insolvenci)
  AND má vlastní web s e-mailem nebo telefonem

Zvýšená priorita (signály zájmu):
  + získali investici v posledních 12 měsících
  + otevřeli nový sklad nebo pobočku
  + hledají pozici související s [produktem]

Vyřaď:
  - v insolvenci nebo likvidaci
  - přímá konkurence: [list]
  - obrat <2M Kč nebo >200M Kč
```

## Notes

[Volné poznámky — kontext, specifika kampaně, co uživatel zdůraznil]
```

## Pravidla pro generaci profilu

1. **Buď konkrétní** — žádné „malé a střední firmy" bez upřesnění čísla.
2. **CZ-NACE kódy** — pro B2B v ČR vždy zkus uvést kódy (skill je má v `zdroje-vyhledavani.md`). Pokud nejsi jistý kódem, navrhni 2–3 nejbližší a nech uživatele zvolit v STOP 1.
3. **Disqualifiers musí být explicit** — bez nich pre-filter v Krok 5 selže.
4. **Hledací heuristika musí být strojově použitelná** — nepoužívej vágní pojmy („dynamické firmy", „inovativní"), používej měřitelné filtry.
5. **Sekce „Signály zájmu" je volitelná** — pokud uživatel nemá žádný konkrétní signál, nech sekci prázdnou. Není povinná.

## Příklad vyplněné šablony

```markdown
# Ideální klient — eko-kosmetika-eshopy

**Datum:** 2026-05-25
**Produkt / služba:** TermoTea — bezobalová zelená kosmetika (B2B distribuce)
**Segment:** B2B

## Firmografika

- **Branže / vertikály:** maloobchod kosmetikou (CZ-NACE 4775), e-shopy obecně (4791)
- **Velikost:** 5–50 zaměstnanců, obrat 5–50M Kč
- **Geografie:** ČR (primárně Praha, Brno, Ostrava, KV)
- **Právní forma:** s.r.o.
- **Věk firmy:** založené 2018+ (mladší = otevřenější novým dodavatelům)

## Technografika

- **Co používá:** Shoptet / WooCommerce / Shopify e-shop
- **Signál vhodnosti:** sortiment obsahuje bio / eko / vegan / bez testování na zvířatech
- **Signál nevhodnosti:** prodává jen jednu značku (exkluzivní distribuce)

## Signály zájmu

- Otevřeli novou kategorii v sortimentu
- Hledají kategori managera / nákupčího
- Nedávné zmínky v tisku o udržitelnosti

## Disqualifiers

- V insolvenci (check Justice.cz)
- Konkurenti: [Manufaktura, Yves Rocher CZ]
- Obrat <2M Kč (příliš malí)
- Obrat >200M Kč (mají vlastní privát značku)

## Hledací heuristika

Hledej firmy:
  CZ-NACE IN [4775, 4791]
  AND geografie = ČR
  AND právní forma = s.r.o.
  AND status = aktivní
  AND má vlastní web s e-mailem

Zvýšená priorita:
  + sortiment obsahuje „bio" / „eko" / „vegan" (zjisti vyhledáním na webu)
  + nedávné zmínky v tisku o udržitelnosti

Vyřaď:
  - insolvence (Justice.cz check)
  - Manufaktura, Yves Rocher CZ
```
