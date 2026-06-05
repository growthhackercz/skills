---
name: email-writer
description: "Pište e-maily týkající se prodeje, podpory, uvítání, newsletteru, sledování, spouštění, reaktivace a kampaní konverzačním stylem zaměřeným na konverzi."
category: content
status: ready
version: "1.0"
publishedAt: "2026-05-08"
---
# Email Writer

Uživatel zadá typ emailu a kontextu. Agent napíše hotový email, který zní jako osobní zpráva, ne jako marketing.

Tento skill muze fungovat samostatne, kdyz uzivatel chce jen text emailu nebo sekvence. Pokud uzivatel chce kampan, strategii, draft v GHL/SmartEmailingu nebo nahrani do platformy, vstupnim bodem ma byt `email-draft-orchestrator`, ktery si tento writer zavola jako copywritingovy krok.

---

## Vstup

Uživatel zadá co potřebuje. Minimální vstup: typ emailu + kontext.

Pokud uživatel nespecifikuje, agent se zeptá:
- **Typ emailu** — jaký (viz typy níže)
- **Cíl** — co má příjemce udělat po přečtení
- **Komu** — kdo je příjemce (nebo odvoď z brandDNA)
- **Kontext** — o čem email je, co mu předcházelo

Volitelně:
- Produkt/nabídka (jinak odvoď z productDNA)
- Tón (jinak odvoď z brandDNA)
- Délka (výchozí: krátký — 150-300 slov)
- Jméno odesílatele

---

## Typy emailů

### Jednotlivé emaily

| Typ | Kdy použít | Cíl |
|-----|-----------|-----|
| **Prodejní** | Představení nabídky, promo, spuštění | Klikněte na prodejní stránku / nákup |
| **Pečující** | Budování důvěry, edukace | Čtenář získá hodnotu, zůstane v kontaktu |
| **Zpravodaj** | Pravidelný obsah, novinky | Klikněte na článek, zapojení |
| **Navazující informace** | Po akci (webinář, stažení, konzultace) | Další krok v prodejní cestě |
| **Reaktivační** | Neaktivní kontakty | Znovu zapojit, klik |
| **Oznámení** | Událost, novinka, aktualizace | Informovat + akce |
| **Studený oslovení** | První kontakt, B2B | Odpověď / schůzka |

### Sekvence (série emailů)

| Typ | Počet emailů | Struktura |
|-----|-------------|-----------|
| **Uvítací** | 3-5 emailů | Seznámení → hodnota → hodnota → jemná nabídka → nabídka |
| **Promo** | 5-7 emailů | Upoutávka → edukace → příběh → nabídka → naléhavost → poslední šance → výsledky |
| **Pečující** | 5-7 emailů | Hodnota → hodnota → hodnota → jemná nabídka → hodnota → nabídka → hodnota |
| **Opuštěný košík** | 3 emaily | Připomínka → námitka → naléhavost/bonus |
| **Reaktivační** | 3 emaily | Chybíš nám → hodnota/novinka → poslední šance |

Při sekvenci napíše všechny emaily najednou s jasným označením pořadí a doporučeným časováním.

---

## Workflow

### Krok 1: Načti kontext
1. Načti `/documents/brand/brandDNA.md` — hlas značky, tón, poslatel
2. Pokud email souvisí s produktem → načti `/documents/brand/products/{slug}/productDNA.md`
3. Pokud existuje podklad z průzkumu nebo článek, na který email navazuje → načti ho

### Krok 2: Napiš email
Napiš kompletní email najednou. Výstup v. Markdown.

### Krok 3: Ulož
- Jednotlivý email: `/documents/brand/content/email/[slug].md`
- Sekvence: `/documents/brand/content/email/[nazev-sekvence]/[cislo]-[slug].md`

Pokud má email pokračovat do `email-draft-orchestrator`, ulož vedle Markdownu také platform-ready soubory:

- `email-001.html` - review-ready HTML email
- `email-001.txt` - plain-text fallback
- `email-manifest.json` - seznam emailů a metadata pro publishery

U starších výstupů bez HTML stačí uložit Markdown; `email-draft-orchestrator` umí HTML/TXT doplnit.

---

## Výstupní formát

```markdown
# [TYP]: [Krátký popis]

**Předmět:** [předmět emailu]
**Náhled textu:** [40-90 znaků — text viditelný v doručené poště za předmětem]
**Odesílatel:** [jméno z brandDNA]
**Cíl:** [co má příjemce udělat]
**Hlavní spouštěč:** [který psychologický spouštěč email používá]

---

[Tělo emailu — čistý text, žádné HTML, žádné formátování kromě odřádkování]

[CTA]

[Podpis]

---

**Poznámky pro nasazení:**
- Personalizace: [kde vložit {first_name} nebo jiné proměnné]
- Časování: [kdy odeslat — den, čas, nebo rozestup od předchozího emailu]
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

HTML ma byt jednoduche a email-safe: inline odkazy, kratke odstavce, zadne skripty, zadne externi CSS. Pokud nejsou `From email` nebo `Reply to` zname, nehalucinuj je; publisher je muze doplnit z env.

---

## Principy psaní emailů

### Předmět

Předmět rozhoduje jestli email vůbec někdo otevře. Pravidla:

- Max 50 znaků (ideálně 30-40)
- Vyvolává zvědavost — čtenář MUSÍ otevřít aby zjistil víc
- Nesmí znít marketingově — žádné "SLEVA", "Exkluzivní nabídka", "Nenechte si ujít"
- Osobní a konverzační — jako by psal kamarád
- Narušení očekávání — něco neočekávaného

Dobré předměty:
- "udělal jsem chybu"
- "tohle jsem nečekal"
- "rychlá otázka"
- "přestal jsem s tím"
- "3 věci, které bych udělala jinak"
- "špatná zpráva"
- "měl jsi pravdu"
- "nečti tohle (pokud...)"

Špatné předměty:
- "Exkluzivní nabídka jen pro vás!"
- "5 tipů jak zlepšit váš marketing"
- "Newsletter #47 — březen 2026"
- "Nový článek na blogu"
- "Nenechte si ujít naši akci!"

Ke každému emailu dodej 3 varianty předmětů — hlavní + 2 alternativy pro A/B test.

### Náhled textu

40–90 znaků. Doplňuje předmět — nepopisuje ho, rozšiřuje zvědavost. Nikdy neopakuj předmět.

- Předmět: "udělal jsem chybu" → Náhled: "a stálo mě to 3 měsíce práce"
- Předmět: "rychlá otázka" → Náhled: "zabere ti to 10 sekund"

### Úvodní věta

První věta rozhoduje jestli čtenář dočte zbytek. Pravidla:

- Okamžitě zaujmi — žádné "Doufám, že se máte dobře"
- Buď konkrétní, ne obecný
- Vytvořit okamžité spojení — čtenář se musí poznat
- Vyprávěj — začni uprostřed příběhu

Dobré úvody:
- "Včera jsem dostal email, který mě zastavil uprostřed oběda."
- "Řeknu ti něco, co většina lidí v mém oboru nepřizná."
- "Znáš ten pocit, když víš, že děláš něco špatně — ale nevíš co?"
- "Před 6 měsíci jsem měl zavřel firmu."
- "Tohle mi řekl klient minulý týden a od té doby na to myslím."

Špatné úvody:
- "Doufám, že se máte skvěle!"
- "V dnešním emailu se podíváme na..."
- "Rádi bychom vám představili..."
- "Jak jistě víte, umělá inteligence mění svět..."

### Tělo emailu

- **Krátké odstavce** — max 2-3 řádky, pak prázdný řádek
- **Střídej délku vět** — krátká. Pak delší, která rozvine myšlenku. Pak zase krátká.
- **Jedna myšlenka na odstavec** — nikdy nemíchej víc témat
- **Jeden hlavní psychologický spouštěč na email** (viz sekce níže)
- **Max 150-300 slov** — email není článek. Pokud potřebuješ víc slov, rozděl na 2 emaily.
- **Žádné formátování** — žádné tučné, kurzíva, podtržení, odrážky. Čistý text jako osobní zpráva. Výjimka: odkaz na žádost k akci může být na vlastním řádku.

### CTA

- Jeden email = jedna CTA. NIKDY víc.
- Výzva je přirozená součást textu, není oddělené tlačítko
- Formuluj jako osobní doporučení, ne jako marketing

dobré výzvy:
- "Tady se můžeš podívat, jak to funguje: [odkaz]"
- "Jestli tě to zaujalo, mrkni sem: [odkaz]"
- "Odpověz mi na tento email — zajímá mě tvůj názor."
- "Zaregistruj se tady, trvá do 30 sekund: [odkaz]"

Špatné výzvy:
- "KLIKNĚTE ZDE PRO VÍCE INFORMACÍ"
- "Neváhejte a dodejte naši nabídku ještě dnes!"
- "Zaregistrujte se nyní a získejte exkluzivní přístup!"

### Podpis

Krátký, osobní. Jméno + případně role/firma. Žádné "S pozdravem" nebo "S přátelským pozdravem".

Formát:
```
[Jméno]

P.S. [volitelný postscript — často nejčtenější část emailu]
```

P.S. použij strategicky — shrň hlavní přínos, přidej naléhavost, nebo zmíň bonus. Ne v každém emailu.

---

## Psychologické spouštěče

V každém emailu použij JEDEN hlavní spouštěč. Nech ho působit přirozeně — žádná manipulace.

| Spouštěč | Jak funguje | Kdy použít |
|---------|------------|-----------|
| **Zvědavost** | Otevři smyčku, zavři ji až za k akci | Úvod, předmět |
| **Sociální důkaz** | Příběh/výsledek jiného zákazníka | Pečující, prodejní |
| **Reciprocita** | Dej hodnotu zdarma, pak požádej | Newsletter, pečující |
| **Nedostatek** | Omezený čas/místa (jen pokud je reálný) | Spouštěcí, promo |
| **Autorita** | Data, studie, citát experta | Edukační, pečující |
| **Příběh** | Osobní příběh s poučením | Uvítací, pečující |
| **Ztotožnění** | Čtenář se pozná v problému | Úvod, pečující |
| **Kontrast** | Před/po, staré vs. nové | Prodejní, případová studie |
| **Mezera zvědavosti** | Naznač odpověď, dodej ji za klikem | Newsletter, promo |
| **Strach ze ztráty** | Co ztrácíš když neřeš | Následný, opuštěný košík |

---

## Pravidla pro sekvenci

Při psaní záznamu dodržuj:

- **Každý email stojí sám** — čtenář nemusel číst předchozí
- **Narůstající intenzita** — od hodnoty k nabídce, ne naopak
- **Max 1 prodejní email na 3 hodnotové** — poměr 3:1
- **Variabilní délka** — střídej kratší (100 slov) a delší (300 slov) emaily
- **Variabilní formát** — střídej příběh, tip, otázka, data, osobní sdělení
- **Konzistentní hlas** — celá sekvence zní jako jeden člověk
- **Časování** — navrhni konkrétní rozestupy mezi emaily (den 0, den 1, den 3, den 5...)

---

## Zakázané vzory

NIKDY nepoužívej:
- "Doufám, že se máte dobře / skvěle"
- "Rádi bychom vám oznámili..."
- "V dnešním emailu se podíváme na..."
- "Jak jistě víte..."
- "Nenechte si tuto jedinečnou příležitost"
- "Exkluzivní / limitovaná / poslední šance" (pokud to není pravda)
- "Klikněte zde" jako textové výzvy
- Více než 1 CTA v emailu
- HTML formátování (tučné, kurzíva, barvy, tlačítka) — piš čistý text
- Emotikony v předmětu (pokud to není hlas značky)
- Předmět delší než 50 znaků
- Email delší než 400 slov (výjimka: spouštěcí/příběhový email max 500)
