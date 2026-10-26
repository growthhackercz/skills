# Brand styl pro generované obrázky (sdílený postup)

Jednotný recept, jak z brand podkladů klienta vyrobit **styl do generovacího promptu**. Cíl: fleet negeneruje brand v sedmi odstínech, a social vizuály vypadají **profesionálně jako design systém**, ne „average".

## 1) Načti brand podklady (co existuje)

| Soubor | Co si vzít |
|---|---|
| `/documents/brand/DESIGN.md` | HEX barvy (primární/sekundární/akcent/pozadí), fonty, gradient, radius |
| `/documents/brand/brandDNA.md` | nálada/tonalita (prémiová · hravá · technická…), slovník |
| `/documents/brand/brand-board.png` | vizuální reference designového jazyka |
| `/documents/brand/brand-kit/23-inspirace-pro-instagram.png` | **jak vypadá náš social feed** (primární social reference) |

Nic z toho → generuj neutrálně kvalitně a v manifestu `"brandStyle": "none"`.

## 2) ⭐ Few-shot reference (nejsilnější zámek stylu)

**Textový popis stylu nestačí.** Nakrmit generátor **2–4 skutečnými brand vizuály** zamkne styl (paletu, typografii, layout logiku) mnohem silněji.

- Vyber **2–4 reference:** `brand-board.png` + `brand-kit/23-inspirace-pro-instagram.png` + 1–2 reálné povedené posty klienta (z `/documents/content/social/**/images/` nebo brand knihovny).
- Předhoď je do `image_generate` jako **obrázkové reference** (GPT Image 2 image input / edit mód).
- Prompt zarámuj: *„Use these as STYLE references — derive palette, typography, and layout logic. Do NOT copy them; generate a NEW visual in the same design language."*
- **Guardrail (závazný):** reference = **odvození designového jazyka, NE předloha ke kopírování.** (Stejné pravidlo má `brand-image-generator`.) Různost obsahu ano, jednotný systém taky — viz grid střídání v SKILL.md.
- **Produkt nebo osoba na vizuálu → few-shot POVINNÝ (výjimka z „nekopíruj").** Reálný produkt (packshot z brand knihovny) předhoď jako `image` referenci a drž ho **věrně** — tím máš **správné logo/label** a konzistentní produkt napříč slidy. Bez toho GPT vymyslí špatné logo a mění produkt slide od slidu. Totéž osoba/founder (zamčená tvář). *(Reálný produkt > jakýkoli textový popis.)*

## 3) Barvy — 3 role, ne paleta

Z DESIGN.md odvoď **tři barvy s pevnými rolemi** (víc barev = amatérské „popping"):

| Role | CliqSales default | Použití |
|---|---|---|
| **Background** | navy `#01071A` | dominantní plocha |
| **Primary/text** | bílá | hlavní text, klid |
| **Accent** | modrá / cyan | 1 klíčové slovo, prvek, CTA |

- Poměr **60 / 30 / 10** (dominantní / sekundární / akcent).
- **Nikdy víc než 3 barvy** — i pod fotkou drž 3 (foto se podřídí paletě).

## 4) Typografie — mix 2 fontů, editorial (NE obří placka)

- **Mix DVOU kontrastních fontů i v nadpisu** — výrazný serif/display pro jedno slovo + **elegantní kurzíva nebo clean sans** pro druhé. To dělá titulek **hravý a editoriální**, ne sterilní. *(Ověřeno testem: jeden font přes celou šířku = placka; serif + kurzíva = prémiový magazín.)*
- **Střední škála, NE obří.** Typografie výrazná, ale **integrovaná do vizuálu** s prostorem kolem — nikdy jedno slovo přes celý slide. Cíl je **silný vizuál + silná (ne přebujelá) typografie** současně.
- **Body font čistý** (druhá role); když má osobnost, je to špatně.
- Font popiš slovy („high-contrast serif + italic script"), nezadávej název fontu (modely ho neznají).

## 5) Slož STYL BLOK (na konec promptu, když nejedeš few-shot)

```
Brand style: background {HEX pozadí} (dominant 60%), {HEX text} text (30%),
{HEX akcent} accent (10%, one key word only). Two type roles: bold display
headline with ONE word enlarged in accent color, clean body. Mood: {2–4 slova
z brandDNA}. Consistent, professional design-system look.
```

## 6) Text na obrázku (karty, citáty, statistiky, slidy)

- `image_generate` (GPT Image 2 text umí) — text v promptu PŘESNĚ v uvozovkách, česky s diakritikou + „exactly as written, correct Czech diacritics".
- Titulek max ~8 slov. **Vyznač 1 klíčové slovo** pro akcentní barvu a větší velikost.
- Zkontroluj výsledek — překlep = regeneruj (1 retry, pak zjednoduš text).

## 7) Kdy je brand styl POVINNÝ

| Použití | Brand styl |
|---|---|
| karusel, karta, single vizuál, story cover — cokoli social | **povinný** (few-shot + styl blok) |
| ilustrační inline foto (lidé, situace) | paleta volněji — autenticita > filtr |
