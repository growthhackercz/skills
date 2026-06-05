---
name: brand-dna
description: "Vytvoří kompletní report DNA značky včetně podstaty značky, zákazníka, příběhu, hlasu, vizuální identity, positioningu a komunikačních pilířů."
category: marketing
status: ready
version: "1.0"
publishedAt: "2026-04-25"
---
# DNA značky — Emoční a strategický profil značky

Uživatel přiloží podklady o značce (vyplněný dotazník, logo, existující materiály). Agent analyzuje vše a vytvoří Brand DNA Report.

---

## Vstup

Uživatel přiloží podklady o značce. Ideálně vyplněný dotazník Brand Designer™.

**Co agent potřebuje (alespoň základy):**
- Co firma dělá a komu pomáhá
- Kdo je ideální zákazník a co ho trápí
- Jakou transformaci přináší značka (před → po)
- Jaký pocit má vyvolávat
- Hodnoty a tón komunikace
- Vizuální preference (barvy, styl, inspirace)

**Volitelně (posílí výsledek):**
- Logo (agent z něj vyčte barvy jako základ palety)
- Existující web nebo materiály
- Příběh zakladatele
- Příklady, které uživatel obdivuje

Pokud uživatel nepřiloží žádné podklady, agent se zeptá na klíčové informace.

---

## Workflow

### Krok 1: Načti podklady
Analyzuj vše přiložené — dotazník, logo, weby, texty, screenshoty.

### Krok 2: Nabídni režim
Zeptej se uživatele:

> Mám tvé podklady. Jak chceš pokračovat?
> **1** — Kompletní zpráva o DNA značky (7 sekcí, jedna verze)
> **2** — 3 různé varianty Brand DNA ke srovnání

Pokud uživatel nespecifikuje, použij režim 1.

### Krok 3: Vytvoř zprávu
Napiš Brand DNA podle zvoleného režimu.

### Krok 4: Ulož
Ulož výstup jako: `/documents/brand/brandDNA.md`

---

## Role

Vystupuj jako zkušený stratég značkové zkušenosti. Tvůj úkol je zachytit emoční pravdu a energii značky — tak, aby každý, kdo s ní přijde do styku, okamžitě cítil, o co jde.

---

## Pravidla

- Popisuj jak má značku PŮSOBIT, ne jak má VYPADAT
- Používej smyslový jazyk a metafory
- Piš lidsky, přímo, bez korporátních frází
- Vyhni se klišé a prázdným výrazům
- Žádné dramatické konstrukce typu „Tohle není jen X — je to Y“
- Každá hodnota musí být konkrétní, není obecná
- Barvy vždy uvádej s HEX kódy
- Pokud je přiloženo logo — vycházej z jeho barev jako základ palety
- Pokud informace chybí — zapiš do sekce CHYBĚJÍCÍ INFORMACE, nevymýšlej si

---

## Formát zprávy (Režim 1 — kompletní)

```markdown
# BRAND DNA: [Název značky]

---

## 1. ESENCE ZNAČKY

- **Název:** [název firmy/značky]
- **Kategorie:** [oblast ve které značka působí]
- **Slogan:** [max několik slov — úderné heslo zachycující postoj/filozofii. Ne popis služby, ale emoční zkratka.]
- **Jedinečná výhoda (USP):** [Jedna věta: „Proč jít k nám a ne ke konkurenci?" Struktura: [Co děláme jinak] + [Jak] + [Výsledek]. Konkrétní, žádné prázdné superlativy.]
- **Transformace PŘED → PO:**
  - Vnější změna: [co se změní v životě/byznysu zákazníka]
  - Vnitřní změna: [jak se zákazník cítí po transformaci]
- **Emoční tón:** [3-5 specifických pocitů — ne obecné jako „profesionální"]

---

## 2. IDEÁLNÍ ZÁKAZNÍK

- **Kdo je:** [pozice, situace, životní fáze]
- **Co hledá:** [jakou změnu chce]
- **Co ho trápí:** [hlavní bolest/frustrace]
- **Jak se má cítit při kontaktu se značkou:** [konkrétní pocity]

---

## 3. PŘÍBĚH ZAKLADATELE

- **Jaká část cesty formuje energii značky:** [osobní zkušenost, která dala značce vzniknout]
- **Jaký typ energie to aktivuje:** [co z tohoto příběhu prostupuje do značky]

---

## 4. POCIT ZE ZNAČKY NAPŘÍČ KANÁLY

Popisuj tempo, atmosféru, rytmus — ne design.

- **Web:** [jaký pocit má návštěvník při procházení webu]
- **Sociální sítě:** [jakou roli hraje značka v feedu — připomínka, inspirace, energizér...]
- **E-maily:** [tón, tempo, jaký pocit má čtenář po přečtení]
- **Videa:** [nálada, tempo, styl komunikace]
- **Živé akce:** [jakou atmosféru vytváříme v osobním kontaktu]

---

## 5. HLAS ZNAČKY

- **Tón:** [jak značka zní — klidně, sebevědomě, hřejivě...]
- **Rytmus:** [krátké věty / delší plynulé / mix]
- **Postoj:** [jak se značka staví ke světu — průvodce, mentor, parťák, expert...]
- **Slova, která značku definují:** [5-10 slov, která se přirozeně objevují v komunikaci]
- **Slova, kterým se značka vyhýbá:** [slova, která nezapadají do tónu]
- **Ukázkové věty:** [2-3 věty, jak by značka promluvila přímo k zákazníkovi]

---

## 6. VIZUÁLNÍ IDENTITA

### Barevná paleta

**Primární barvy:**
| Barva | HEX | Použití |
|-------|-----|---------|
| [název] | #XXXXXX | [kde se používá — hlavní, pozadí, akcenty...] |
| [název] | #XXXXXX | [...] |

**Sekundární barvy:**
| Barva | HEX | Použití |
|-------|-----|---------|
| [název] | #XXXXXX | [...] |
| [název] | #XXXXXX | [...] |

### Typografie
- **Nadpisy:** [doporučený font + Google Fonts alternativa]
- **Tělo textu:** [doporučený font + Google Fonts alternativa]
- **Styl:** [jak typografie podporuje pocit značky]

### Vizuální styl
- **Celkový směr:** [minimalistický / luxusní / organický / moderní / ...]
- **Styl fotografií:** [nálada, světlo, kompozice]
- **Textury a vzory:** [pokud jsou relevantní]
- **Ikonografie:** [styl ikon — liniové, vyplněné, ruční kresba...]

---

## 7. SHRNUTÍ BRAND DNA

[Jeden odstavec zachycující celkový pocit ze značky. Esence toho, čím značka je, jak působí a co v lidech vyvolává.]

---

## CHYBĚJÍCÍ INFORMACE

[Co v podkladech chybělo a co by Brand DNA posílilo. Pokud nechybí nic: „Podklady byly kompletní."]
```

---

## Formát 3 variací (Režim 2)

Pro každou variantu napiš jeden souvislý odstavec obsahující:
- Název značky
- DNA značky (3-6 slov zachycujících esenci)
- Polohování
- Tón hlasu
- Vizuální směr (nálada, textury, styl fotek, doporučené barvy s HEX kódy, fonty)
- Ideální publikum
- Obsahové pilíře (3-5 témat s vysvětlením)
- Hlavní nabídky
- Ukázkové slogany (3-5)

Varianty by měly mít v přístupu — jen v detailech. Každá varianta nabízí jiný směr, jinou energii, jiný úhel pohledu na značku.

Pokud je přiloženo logo, všechny 3 varianty musí vycházet z barev loga.

---

## Iterace

Po prvním výstupu uživatel může požádat o úpravy:
- "Změň tón na odvážnější."
- "Víc zdůrazni transformaci."
- "Navrhni tmavší paletu."
- „Slogan je moc obecný — chci něco úsečnějšího.“
- „Přidej hodnotu o komunitě.“

Při úpravě jedné sekce NIKDY neměň ostatní sekce.

---

## Jak se Brand DNA používá dál

Značka DNA je základ celého marketingového ekosystému. Všechny ostatní dovednosti z ní čerpají:
- **Copywriting** — tón, hlas, hodnoty, emoční naladění
- **Články a emaily** — styl komunikace, ukázkové věty
- **Vizuály** — barevná paleta, styl fotografií, typografie
- **DNA produktu** — konzistence tónu mezi značkou a produktem
- **Sociální sítě** — pocit značky napříč kanály

DNA značky = KDO jste (hodnoty, tóny, emoce, vizuální identita).
Produkt DNA = CO prodáváte (benefity, cena, námitky, důkazy).

Značka DNA je jedna pro celou firmu. Produkt DNA se vytváří pro každý produkt zvlášť.
