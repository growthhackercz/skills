# Šablona briefu — 11 sekcí

Sales Scout vyplňuje tuto šablonu a vloží ji jako poznámku ke kontaktu v CliqSales CRM. Formát je Markdown, helper `ghl_scout_push.py` ho konvertuje na GHL Rich Text HTML před vložením (viz `ghl-html-konverze.md`).

## Důležitá omezení

- **Žádné tabulky** — GHL Rich Text v poznámkách nepodporuje, převedly by se na ošklivý text. Vše jako bullet listy nebo bold-prefix bullety (`**Klíč:** hodnota`).
- **Žádné code blocky** — totéž.
- **Headings jen H2** (`## Nadpis`) — H3 a hlubší se v GHL HTML konvertují na bold (Rich Text headings nepodporuje), proto je nepoužíváme nadbytečně. Výjimka: multi-product brief má v sekci 2 a 6–10 H2 subsekce (`## Pro [produkt-name]`).
- **Emoji prefix u nadpisů** jako vizuální kotvy — 📋 🎯 🚀 💡 ⚠️ 🎬 ✉️ 📞 ❓ 🗂️.

## Hlavička

**Single-product:**

```markdown
🔎 **Sales Scout brief** — [YYYY-MM-DD] · Fit [A/B/C] pro [Název produktu] · [webhook | manuální]
```

**Multi-product** (víc produktů z fit posouzení, max 3):

```markdown
🔎 **Sales Scout brief** — [YYYY-MM-DD] · Fit A: [Produkt 1], Fit B: [Produkt 2] · [webhook | manuální]
```

**Pravidla pro hlavičku:**

- **NEUVÁDĚJ název firmy v hlavičce** — poznámka je připnutá ke kontaktu, firma je vidět nad ní. Duplikace = šum.
- **Vždy uveď datum** (YYYY-MM-DD, lokální formát stačí).
- **Vždy uveď fit grade** — obchodník skenuje notes v CRM, na první pohled má vidět *„aha, A fit pro Bioptron, koukni se na to"*.
- **Vždy uveď režim** (`webhook` / `manuální` / `manuální refresh` pokud `refresh=true`).
- **Bez verze skillu v hlavičce** — verze patří do zápatí (audit).

## Sekce 1 — 📋 Základní údaje (společná)

```markdown
## 📋 Základní údaje

- **Firma:** [Název firmy]
- **IČO:** [12345678]
- **Lokalita:** [Adresa, město]
- **Web:** [https://firma.cz](https://firma.cz)
- **E-mail:** [info@firma.cz](mailto:info@firma.cz)
- **Telefon:** [+420 ...]
- **Kontakt:** [Jméno Příjmení] — [pozice z webu / LinkedIn]
- **LinkedIn osoby:** [URL nebo „nenalezeno"]
- **Zdroj výzkumu:** web ✓ | ARES ✓ | LinkedIn ✓/nedostupný | Justice ✓ | News ✓
```

## Sekce 2 — 🎯 Shrnutí fitu (per produkt)

**Single-product režim:**

```markdown
## 🎯 Shrnutí fitu pro [Název produktu]

**Fit: A / velmi dobrý** (alternativy: **B / dobrý** | **C / okrajový**)

Effect Clinic je vhodný lead pro Bioptron, protože kombinuje estetickou medicínu, laserové zákroky a kosmetická ošetření. Bioptron zde dává smysl primárně jako doplňková regenerační procedura po estetických zákrocích.

**Nejsilnější vstupní argument:** rozšíření klientské péče po zákroku, neinvazivní procedura s nízkou provozní náročností.
```

**Multi-product režim** — tři H2 subsekce, jedna za druhou:

```markdown
## 🎯 Shrnutí fitu pro Bioptron MedAll

**Fit: A / velmi dobrý**

Effect Clinic kombinuje laser, estetickou chirurgii a kosmetickou péči — Bioptron jako doplňková regenerační procedura po zákrocích.

## 🎯 Shrnutí fitu pro AI Akcelerátor

**Fit: B / dobrý**

Klinika má 7 zaměstnanců a roste, mohla by mít užitek z AI nástroje pro koordinaci klientů a follow-up. Není to však primární prioritou estetického centra.

## 🎯 Shrnutí fitu pro Live100 vitamíny

**Fit: C / okrajový**

Klinika má vlastní doplňky stravy pro klientelu, ale jako re-seller live100 by nepřinesl významnou hodnotu.
```

## Sekce 3 — 🚀 Relevantní signály z veřejných podkladů (společná)

```markdown
## 🚀 Relevantní signály z veřejných podkladů

- Centrum funguje od roku 2009.
- Nabízí laserové zákroky: epilace, korekce červených žilek, IPL omlazení pleti, odstranění pigmentací.
- Nabízí estetickou chirurgii: korekce víček, výplňové materiály, liposukce.
- Profil uvádí radiofrekvenci, OxyGeneo+, HIFU, mezoterapii.
- Cenová hladina ukazuje, že klientela je zvyklá platit za prémiovější estetickou péči.
- (Pokud dostupné z news / Hlídače státu) **Signál zájmu:** v dubnu 2026 získali …
```

## Sekce 4 — 💡 Pravděpodobné potřeby (společná)

```markdown
## 💡 Pravděpodobné potřeby

1. **Zvýšit hodnotu návštěvy klienta** — přidat doplňkovou proceduru k estetickým výkonům.
2. **Zlepšit následnou péči po zákroku** — nabídnout klientům klidnou, neinvazivní podporu regenerace.
3. **Odlišit se od konkurence** — nabídnout proceduru navázanou na švýcarský zdravotnický přístroj.
4. **Vytvořit nový důvod k opakované návštěvě** — série krátkých světelných procedur po ošetření.
```

## Sekce 5 — ⚠️ Rizika a námitky (společná)

```markdown
## ⚠️ Rizika a námitky

- **Mají vlastní laserové a přístrojové technologie.** Pozice musí být doplněk, ne konkurence laseru.
- **Zdravotní tvrzení musí být opatrná.** Nepoužívat sliby typu „vyléčí"; raději „podpora regenerace", „zklidnění".
- **Rozhodovací osoba může být vytížená.** První kontakt musí být krátký a konkrétní.
- **Insolvence:** [žádné aktivní řízení (Justice.cz, ověřeno [DD.MM.YYYY])] / [⚠️ Aktivní insolvenční řízení od [datum], spis. zn. [číslo] — **NEOSLOVOVAT**.]
- **Soudní spory:** [žádné | popis]
```

## Sekce 6 — 🎯 Doporučený sales úhel (per produkt)

```markdown
## 🎯 Doporučený sales úhel pro [Název produktu]

**Primární úhel:** „[Produkt] jako doplňková procedura po estetických a laserových ošetřeních — pro klienty, kteří řeší zklidnění, regeneraci pleti, jizvy nebo pooperační komfort."

**Sekundární úhel:** „Krátká procedura 5–10 minut, kterou lze zařadit jako premium add-on bez složitého provozu."

**Čemu se vyhnout:**
- Netvrdit, že [Produkt] nahradí jejich laserové procedury.
- Netlačit na okamžitý nákup.
- Neotevírat komunikaci obecnou prezentací výrobce.
```

## Sekce 7 — 🎬 Next-best-action (per produkt)

```markdown
## 🎬 Next-best-action pro [Název produktu]

- **Priorita:** A (alternativy: B / C)
- **Doporučený další krok v CRM:** Call / kvalifikační hovor
- **Cíl hovoru:** zjistit, kdo rozhoduje o nákupu přístrojů a zda mají zájem o doplnění procedury pro regeneraci po zákrocích.
- **Optimální čas oslovení:** [např. „v týdnu do 5 pracovních dnů — signál zájmu z 04/2026 je čerstvý"]
```

## Sekce 8 — ✉️ E-mail / první oslovení (per produkt)

```markdown
## ✉️ E-mail / první oslovení pro [Název produktu]

**Předmět:** Doplňková světelná procedura po estetických ošetřeních

**Tělo:**

Dobrý den,

narazil jsem na Effect Clinic a zaujalo mě, že kombinujete laserové zákroky, estetickou péči a plastickou chirurgii. Právě u takových pracovišť často dává smysl doplňková světelná procedura pro klienty, kteří řeší zklidnění a regeneraci po ošetření.

Zastupujem [Vaši firmu] a rád bych vám krátce ukázal Bioptron MedAll — švýcarský zdravotnický přístroj pro světelnou terapii, který se dá zařadit jako doplněk k péči po zákrocích nebo jako samostatná prémiová procedura.

Mělo by smysl domluvit si 10 minut a ověřit, jestli by to zapadalo do vaší nabídky?

S pozdravem
[Jméno obchodníka / Firma]
```

## Sekce 9 — 📞 Call opener (per produkt)

```markdown
## 📞 Call opener pro [Název produktu]

Dobrý den, volám kvůli Effect Clinic — viděl jsem, že nabízíte laserové a estetické zákroky včetně péče o pleť, pigmentace a jizvy. Nechci nabízet další „konkurenční laser", spíš doplňkovou světelnou proceduru Bioptron, která může rozšířit následnou péči po ošetření. Kdo u vás řeší nové přístroje nebo doplňkové procedury?
```

## Sekce 10 — ❓ Kvalifikační otázky (per produkt)

```markdown
## ❓ Kvalifikační otázky pro [Název produktu]

1. Nabízíte klientům po zákrocích nějakou následnou regenerační nebo zklidňující péči?
2. Máte procedury, kde by dávalo smysl přidat krátký 5–10minutový doplněk?
3. Kdo u vás rozhoduje o nákupu nových přístrojů?
4. Zajímá vás spíš přístroj pro použití v provozovně, nebo i možnost doporučení klientům domů?
5. Jak hodnotíte nové procedury — podle návratnosti, poptávky klientů, odbornosti, nebo jednoduchosti obsluhy?
```

## Sekce 11 — 🗂️ Doporučený další krok v CRM (společná)

```markdown
## 🗂️ Doporučený další krok v CRM

- **Top priorita produktu:** [Název produktu s nejvyšším fit] (fit A)
- **Stage:** kvalifikovat — první kontakt (nebo „nabídnout demo" / „odložit" podle fit grade)
- **Úkol:** Zavolat [Jméno Příjmení] (telefon [+420 ...]) a ověřit zájem o doplnění procedury / produktu.
- **Termín úkolu:** do 5 pracovních dnů (pro fit A) | do 14 dnů (pro fit B) | nesledovat aktivně (pro fit C)
```

**Tagy se NESLOVAJÍ v briefu** — helper `ghl_scout_push.py` přidá jediný tag `sales scout` (lowercase, s mezerou). Žádné per-produkt, per-lokalita, per-fit, per-datum tagy.

## Zápatí

```markdown
---

Vytvořeno: Sales Scout v1.0, [YYYY-MM-DD HH:MM UTC] | Režim: [webhook | manuální]
Audit: /documents/sales/.scout-history.jsonl (řádek s [contactId])
```

## Pravidla psaní obsahu

1. **Buď konkrétní.** Žádné „inovativní řešení", „dynamická firma" — používej měřitelné a ověřené údaje s odkazem na zdroj.
2. **Uváděj zdroj** každé výrazné věty: *„(Lupa.cz, 2026-04-15)"*, *„(z webu)"*, *„(ARES)"*, *„(LinkedIn)"*.
3. **Nevymýšlej.** Pokud informaci nemáš, napiš *„nezjištěno"* nebo sekci vynechej. **Žádné halucinace.**
4. **Pište česky.** Vykání ke koncovému uživateli (obchodník, který brief čte). Tykání se v briefu neobjevuje nikde — ani v call openeru, ani v e-mailu (oba jsou v obchodním tónu).
5. **Brief má být přehledný do 60 vteřin** — bullet pointy, krátké věty, emoji jako vizuální kotvy.

## Vyplněný příklad — single-product brief

(Viz Effect Clinic vzor v `/Users/pavelhrdlicka/Downloads/effect-clinic-sales-scout.md` jako referenční ukázka — formátování a hloubka obsahu, ke kterému Sales Scout cílí.)
