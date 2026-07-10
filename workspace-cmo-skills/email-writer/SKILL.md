---
name: email-writer
description: "Píše krátké, úderné e-maily s jediným cílem: klik. Prodejní, pečující, newsletter, follow-up, reaktivační i kampaňové — konverzační styl, maximální curiosity gap, oslovení a tón z brand DNA."
category: content
status: ready
version: "2.0"
publishedAt: "2026-07-08"
---
# Email Writer

Uživatel zadá typ e-mailu a kontext. Agent napíše hotový e-mail, který zní jako osobní zpráva (ne jako marketing) a jehož jediným úkolem je **dostat čtenáře na klik**.

Skill funguje samostatně (jen text e-mailu nebo sekvence) i jako copywriting krok, který si zavolá `email-draft-orchestrator` (kampaně, strategie, draft v GHL/SmartEmailingu). Content Strategist volá tento writer napřímo.

---

## Cíl e-mailu: KLIK (nejdůležitější pravidlo)

E-mail neprodává. Má jediný úkol: **dostat čtenáře na klik.** Prodává až stránka za odkazem. Každé rozhodnutí (předmět, délka, formát, CTA) slouží tomuhle jednomu cíli.

**Curiosity gap na maximum, ale z reálného obsahu.** Otevři smyčku, kterou jde zavřít jedině klikem. Napětí ber z **nejsilnějšího skutečného prvku** e-mailu (překvapivé číslo, ostrý kontrast, konkrétní věta z příběhu, nečekané zjištění), ne z vymyšlené dramatické šablony. Otevření musí být poctivé a klik musí pointu doručit; žádný bait-and-switch.
- Předmět nakousne, náhled rozšíří, tělo vygraduje napětí. Pointa je až za odkazem.
- Nikdy neprozraď odpověď v e-mailu. Kdyby ji čtenář znal, neklikne.

**Krátké a úderné.** Default **50–150 slov**. Jde-li to říct kratší, řekni to kratší. Žádný warm-up, žádná vata, rovnou do napětí.

**Vzdušné a přehledné (mobil first).**
- Jedna myšlenka = jeden řádek nebo krátký odstavec (1–2 řádky), pak prázdný řádek.
- Hodně bílého místa. Čte se to palcem při skrolování.
- Věty krátké. Občas jednoslovný odstavec pro důraz.
- Klíčová věta a CTA na samostatném řádku, ať „vydechnou".

**Oslovení a tón z brand DNA.** Ty/vy, formálnost i energii **přebírej z `brandDNA.md` klienta** (řada B2B značek vyká, neformální B2C tyká). Vzorové e-maily v tomto skillu ilustrují STYL, ne oslovení.

---

## Vstup

Uživatel zadá co potřebuje. Minimální vstup: typ e-mailu + kontext.

Pokud uživatel nespecifikuje, agent se zeptá:
- **Typ e-mailu** — jaký (viz typy níže)
- **Cíl** — kam má klik vést (jaká stránka nebo akce)
- **Komu** — kdo je příjemce (nebo odvoď z brandDNA)
- **Kontext** — o čem e-mail je, co mu předcházelo, na co odkazuje

Volitelně:
- Produkt/nabídka (jinak odvoď z productDNA)
- Tón + oslovení ty/vy (jinak odvoď z brandDNA)
- Délka (výchozí: 50–150 slov)
- Jméno odesílatele

---

## Typy e-mailů

### Jednotlivé e-maily

| Typ | Kdy použít | Cíl (klik) |
|-----|-----------|-----|
| **Prodejní** | Představení nabídky, promo, spuštění | Klik na prodejní stránku / nákup |
| **Pečující** | Budování důvěry, edukace | Klik na hodnotu, zůstat v kontaktu |
| **Zpravodaj** | Pravidelný obsah, novinky | Klik na článek |
| **Navazující informace** | Po akci (webinář, stažení, konzultace) | Klik na další krok v cestě |
| **Reaktivační** | Neaktivní kontakty | Znovu zapojit, klik |
| **Oznámení** | Událost, novinka, aktualizace | Informovat + klik na akci |
| **Studené oslovení** | První kontakt, B2B | Odpověď / schůzka |

### Sekvence (série e-mailů)

| Typ | Počet e-mailů | Struktura |
|-----|-------------|-----------|
| **Uvítací** | 3–5 e-mailů | Seznámení → hodnota → hodnota → jemná nabídka → nabídka |
| **Promo** | 5–7 e-mailů | Upoutávka → edukace → příběh → nabídka → naléhavost → poslední šance → výsledky |
| **Pečující** | 5–7 e-mailů | Hodnota → hodnota → hodnota → jemná nabídka → hodnota → nabídka → hodnota |
| **Opuštěný košík** | 3 e-maily | Připomínka → námitka → naléhavost/bonus |
| **Reaktivační** | 3 e-maily | Chybíš nám → hodnota/novinka → poslední šance |

Při sekvenci napiš všechny e-maily najednou s jasným označením pořadí a doporučeným časováním.

---

## Workflow

### Krok 1: Načti kontext
1. `/documents/brand/brandDNA.md` — hlas, tón, **oslovení (ty/vy)**, odesílatel
2. Souvisí-li s produktem → `/documents/brand/products/{slug}/productDNA.md`
3. Existuje-li podklad z průzkumu nebo obsah/článek, na který e-mail odkazuje → načti ho (z něj bereš **reálný hook** do předmětu i těla)

### Krok 2: Napiš e-mail
Napiš kompletní e-mail najednou. Výstup v Markdownu.

### Krok 3: Ulož
- Jednotlivý e-mail: `/documents/content/email/{slug}.md`
- Sekvence: `/documents/content/email/{nazev-sekvence}/{cislo}-{slug}.md`

Nové výstupy piš do `/documents/content/email/` (sjednocené s Content Engine). Starší flow ukládal do `/documents/brand/content/email/` — ten zůstává čitelný jako fallback.

Pokud e-mail pokračuje do `email-draft-orchestrator`, ulož vedle Markdownu i platform-ready soubory: `email-001.html`, `email-001.txt`, `email-manifest.json`. U starších výstupů bez HTML stačí Markdown; orchestrator HTML/TXT doplní.

---

## Výstupní formát

```markdown
# [TYP]: [Krátký popis]

**Předmět:** [hlavní předmět]
**Varianty předmětu:** [2–4 alternativy různých archetypů pro A/B]
**Náhled textu:** [40–90 znaků — text za předmětem v doručené poště]
**Odesílatel:** [jméno z brandDNA]
**Cíl (klik):** [kam má klik vést]
**Hlavní spouštěč:** [který psychologický spouštěč e-mail používá]

---

[Tělo e-mailu — čistý text, žádné HTML, jen odřádkování a vzdušné odstavce]

[CTA]

[Podpis]

---

**Poznámky pro nasazení:**
- Personalizace: [kde vložit {first_name} nebo jiné proměnné]
- Časování: [kdy odeslat — den, čas, nebo rozestup od předchozího e-mailu]
- Příjemci: [komu poslat — celý seznam / segment / automaticky po události]
```

## HTML handoff format

Při generování pro GHL nebo SmartEmailing vytvoř HTML s metadatovým komentářem:

```html
<!--
EMAIL METADATA
Campaign: {campaign-slug}
Id: email-001
Name: {nazev emailu}
Subject: {predmet}
Preview text: {nahled textu}
From name: {odesilatel}
From email: {from_email pokud je znamy}
Reply to: {reply_to pokud je znamy}
Audience: {segment nebo poznamka}
Status: draft
-->
<!doctype html>
<html>
<body>
  <p>...</p>
</body>
</html>
```

HTML jednoduché a email-safe: inline odkazy, krátké odstavce, žádné skripty, žádné externí CSS. Pokud `From email` / `Reply to` neznáš, nehalucinuj je; publisher je doplní z env.

---

## Principy psaní e-mailů

### Předmět (rozhoduje o otevření — extrémně důležité)

Předmět má **jediný úkol: otevření.** Je to první curiosity gap a **nesmí jít uhodnout ze sebe sama** — kdyby čtenář znal z předmětu pointu, neotevře (a neklikne).

**Zdroj předmětu = obsah e-mailu, ne šablona.** Vytáhni **nejsilnější reálný prvek** (překvapivé číslo, ostrý kontrast, konkrétní věta z příběhu, nečekané zjištění) a z něj postav předmět. Když e-mail odkazuje na obsah, který **už má silný titulek** (článek v newsletteru, landing page), **pracuj s tím titulkem** — zauzluj ho do zvědavosti, nevymýšlej vedle náhodnou clickbait větu.

Pravidla:
- **Max 50 znaků** (ideál 30–40). Mobil ukáže ~30–40 → **hook nacpi na začátek**.
- **Malá písmena = osobní** (ne „broadcast"). Vědomá taktika.
- **Nesmí znít marketingově** (žádné „SLEVA", „Exkluzivní nabídka", „Nenechte si ujít").
- **Ke každému e-mailu dodej 3–5 variant předmětu**, a to **různých archetypů** — ať A/B testuje odlišné úhly, ne obměny jedné věty.

Archetypy (jen styling; obsah vždy z reálného hooku):
konkrétní číslo/výsledek · ostrý kontrast (před/po) · přímá otázka · nečekané zjištění · otevřená smyčka · pattern-interrupt.

Špatné předměty (nikdy): „Exkluzivní nabídka jen pro vás!", „5 tipů jak zlepšit marketing", „Newsletter #47 — březen 2026", „Nový článek na blogu", „Nenechte si ujít naši akci!".

### Náhledový text

40–90 znaků. Doplňuje předmět — nepopisuje ho, rozšiřuje zvědavost. Nikdy neopakuj předmět.
- Předmět: „stálo mě to 3 měsíce" → Náhled: „a nemuselo, kdybych věděl tohle"
- Předmět: „rychlá otázka" → Náhled: „zabere vám to 10 sekund"

### Úvodní věta

První věta rozhoduje, jestli čtenář dočte. Pravidla:
- Okamžitě zaujmi — žádné „Doufám, že se máte dobře".
- Buď konkrétní, ne obecný.
- Vytvoř okamžité spojení — čtenář se musí poznat.
- Vyprávěj — začni uprostřed příběhu.

Dobré úvody:
- „Včera mi přišel e-mail, který mě zastavil uprostřed oběda."
- „Řeknu vám něco, co většina lidí v mém oboru nepřizná."
- „Znáte ten pocit, když víte, že děláte něco špatně, ale nevíte co?"

Špatné úvody: „Doufám, že se máte skvěle!", „V dnešním e-mailu se podíváme na…", „Rádi bychom vám představili…", „Jak jistě víte, umělá inteligence mění svět…".

### Tělo e-mailu

- **Krátké odstavce** — max 2–3 řádky, pak prázdný řádek. Vzdušné, mobil-first.
- **Střídej délku vět.** Krátká. Pak delší, která myšlenku rozvine. Pak zase krátká.
- **Jedna myšlenka na odstavec.**
- **Jeden hlavní psychologický spouštěč** na e-mail.
- **50–150 slov** default. E-mail není článek; potřebuješ-li víc, rozděl na 2.
- **Bez formátování** (žádné tučné, kurzíva, odrážky). Čistý text jako osobní zpráva. Výjimka: odkaz CTA na vlastním řádku.
- **Neprozrazuj pointu** — ta patří za odkaz.

### CTA

- **Jeden e-mail = jedna CTA. NIKDY víc.**
- CTA = jediné místo, kde se smyčka zavře.
- Výzva je přirozená součást textu, ne oddělené tlačítko.
- Formuluj jako osobní tip („tady zjistíte zbytek"), ne jako marketing („kupte").

Dobré výzvy:
- „Tady se můžete podívat, jak to funguje: [odkaz]"
- „Jestli vás to zaujalo, mrkněte sem: [odkaz]"
- „Odpovězte mi na tento e-mail — zajímá mě váš názor."

Špatné výzvy: „KLIKNĚTE ZDE PRO VÍCE INFORMACÍ", „Neváhejte a využijte naši nabídku ještě dnes!".

### Podpis

Krátký, osobní. Jméno + případně role/firma. Žádné „S pozdravem".

```
[Jméno]

P.S. [volitelný postscript — často nejčtenější část e-mailu]
```

P.S. použij strategicky — shrň hlavní přínos, přidej naléhavost, nebo zopakuj odkaz. Ne v každém e-mailu.

---

## Psychologické spouštěče

V každém e-mailu použij JEDEN hlavní spouštěč. Nech ho působit přirozeně, žádná manipulace.

| Spouštěč | Jak funguje | Kdy použít |
|---------|------------|-----------|
| **Zvědavost** | Otevři smyčku, zavři ji až za klikem | Úvod, předmět |
| **Sociální důkaz** | Příběh/výsledek jiného zákazníka | Pečující, prodejní |
| **Reciprocita** | Dej hodnotu zdarma, pak požádej | Newsletter, pečující |
| **Nedostatek** | Omezený čas/místa (jen pokud je reálný) | Spouštěcí, promo |
| **Autorita** | Data, studie, citát experta | Edukační, pečující |
| **Příběh** | Osobní příběh s poučením | Uvítací, pečující |
| **Ztotožnění** | Čtenář se pozná v problému | Úvod, pečující |
| **Kontrast** | Před/po, staré vs. nové | Prodejní, případová studie |
| **Mezera zvědavosti** | Naznač odpověď, dodej ji za klikem | Newsletter, promo |
| **Strach ze ztráty** | Co ztrácíte, když nejednáte | Navazující, opuštěný košík |

---

## Pravidla pro sekvenci

- **Každý e-mail stojí sám** — čtenář nemusel číst předchozí.
- **Narůstající intenzita** — od hodnoty k nabídce, ne naopak.
- **Max 1 prodejní e-mail na 3 hodnotové** — poměr 3:1.
- **Variabilní délka** — střídej kratší (50–80 slov) a delší (do 150).
- **Variabilní formát** — střídej příběh, tip, otázku, data, osobní sdělení.
- **Konzistentní hlas** — celá sekvence zní jako jeden člověk.
- **Časování** — navrhni konkrétní rozestupy (den 0, 1, 3, 5…).

---

## Anti-slop (jazyk — povinné)

E-mail nesmí znít jako od AI. Před odesláním projdi:
- **Pomlčka „—" střídmě** (řádově 1 na e-mail). Přemíra je typický AI tell — většinou stačí čárka, dvojtečka, závorka nebo tečka.
- **Žádná CZ AI klišé:** „v dnešní digitální/uspěchané době", „posuňte to na další úroveň", „nejen…, ale i", „v neposlední řadě", „změna hry".
- **Ne trojice do foroty** — max jeden výčet „X, Y a Z" na e-mail.
- **Konkrétnost > obecnost** — číslo, jméno, situace místo frází.
- **Test nahlas** — přečti e-mail nahlas; kde se zadrhneš nebo to zní jako leták, přepiš.

---

## Zakázané vzory

NIKDY nepoužívej:
- „Doufám, že se máte dobře / skvěle"
- „Rádi bychom vám oznámili…" / „V dnešním e-mailu se podíváme na…" / „Jak jistě víte…"
- „Nenechte si ujít tuto jedinečnou příležitost"
- „Exkluzivní / limitovaná / poslední šance" (pokud to není pravda)
- „Klikněte zde" jako text výzvy
- Více než 1 CTA v e-mailu
- HTML formátování (tučné, kurzíva, barvy, tlačítka) — piš čistý text
- Emotikony v předmětu (pokud to není hlas značky)
- Předmět delší než 50 znaků
- E-mail delší než 300 slov (výjimka: příběhový/uvítací max 500); default 50–150
- **Prozrazení pointy přímo v e-mailu** — zabíjí klik, pointa patří za odkaz
