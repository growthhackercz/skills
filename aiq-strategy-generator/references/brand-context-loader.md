# Načtení kontextu — 3-way input

Product DNA **není povinná**. Skill přijímá tři zdroje produktového kontextu (v pořadí preference):

1. **Product DNA** — `/documents/brand/products/[slug]/productDNA.md` (preferováno, nejvíc dat)
2. **URL produktové stránky** — skill přečte stránku přes `web_fetch`
3. **Manuální popis** — uživatel nalepí text/info o produktu

Brand DNA (`/documents/brand/brandDNA.md`) je stále silně doporučená pro hlas + ideálního klienta, ale pokud chybí, lze ji nahradit zkrácenou variantou nebo extrahovat z URL.

---

## Workflow auto-detekce

### Co skill udělá v Krok 0.2

```
1. Zkontroluj /documents/brand/brandDNA.md → načti pokud existuje
2. Zkontroluj /documents/brand/DESIGN.md → POVINNÉ pro generaci
   02-pokyny-landing-kviz.md (design tokeny: barvy, fonty, gradient, radius)

   🔴 FORCE-LOAD pravidlo (1.3.2+): PŘED generací 02-pokyny VŽDY
   proveď Read na /documents/brand/DESIGN.md. NIKDY nepředpokládej
   bez aktivního čtení, že DESIGN.md chybí. Mnoho klientů ho má, ale
   agent ho nenačte → VIZUÁL sekce chybí → landing v AI Studiu
   vypadá jako builder default.

   • Pokud existuje → extrahuj konkrétní HEX hodnoty, font names, radius,
     gradient stack — vlož do 02-dokumentu jako KONKRÉTNÍ hodnoty
     (VŽDY proveď, NIKDY neskipuj)
   • Pokud opravdu chybí (Read vrátí „file not found") → **VIZUÁL sekce
     v `02-pokyny-landing-kviz.md` se ÚPLNĚ VYNECHÁ** (žádný flag,
     žádný placeholder, žádná poznámka). Vygeneruj jen texty (Nadpis,
     Podnadpis, Tři oblasti, Autorita, CTA) bez design tokenů. Klient si
     DESIGN.md doplní později manuálně pokud bude potřebovat brand styling.
     **ŽÁDNÁ default CliqSales paleta jako fallback** (= brand pollution).
3. Zkontroluj /documents/brand/logo.png → URL nebo public CDN link pro vložení
   do 02-dokumentu (agent v platformě nemá lokální přístup)
4. Identifikuj produktový vstup:
   a) Uživatel zmínil slug existující v /documents/brand/products/ → načti productDNA.md
   b) Uživatel poslal URL → web_fetch + extrakce
   c) Uživatel nalepil text/info → použij přímo
   d) Nic nezmínil + existuje 1 produkt v knihovně → použij ho (oznam)
   e) Nic nezmínil + existuje víc produktů → zeptej se který, nabídni URL/manuál
   f) Nic nezmínil + žádný produkt v knihovně → polož otázku (viz níže)
5. Validuj, že máš minimum dat pro generaci strategie
6. Kde data chybí → poznač pro `[OVĚŘ S KLIENTEM: …]` placeholder v dokumentu
```

**Klíčový rozdíl mezi 01-strategie.md a 02-pokyny-landing-kviz.md:**
- `01-strategie.md` = strategický dokument pro klienta (interní, lidsky čitelný), nevyžaduje design tokeny
- `02-pokyny-landing-kviz.md` = pokyny pro AI agenta v platformě, který **nemá přístup k brand library** → potřebuje konkrétní HEX, fonty a logo URL **vepsané přímo do dokumentu**

### Otázka při žádném vstupu (případ f)

> *„Aby AIQ strategie dávala smysl, potřebuju vědět, na jaký konkrétní produkt má funnel cílit. Tři možnosti:*
> 1. *Použít Product DNA — pokud nemáš, pusť skill `product-dna` a vrať se*
> 2. *Pošli mi URL produktové stránky a já si data vytáhnu sám*
> 3. *Napiš mi rovnou základní info o produktu (název, co dělá, pro koho, cena, transformace)*
>
> *Co zvolíš?"*

---

## Zdroj 1 — Product DNA (preferováno)

Markdown soubor bez YAML frontmatteru. Skill čte sekce přímým parsováním.

### Identifikace produktu

- Uživatel zmínil produkt v zadání → použij slug (kebab-case)
- Nezmínil + jeden subfolder v `/documents/brand/products/` → použij ho
- Nezmínil + více subfolderů → zeptej se: *„Vidím produkty: [seznam slugů]. Pro který má strategie vést?"*

### Co skill vytahuje

| Sekce v Product DNA | Použití |
|----------------------|---------|
| `## 1. ESENCE PRODUKTU` — Název | Header strategie + sekce 5.2 |
| `## 1.` — Kategorie | Doporučení varianty lead magnetu (kurz → Plan, SaaS → Calculator, …) |
| `## 1.` — USP | Sekce 2 + sekce 5.2 neuroconversion |
| `## 1.` — Transformace PŘED → PO | Sekce 2 + sekce 3 (Q2 odpovědi) + sekce 6 Den 3 |
| `## 3. HLAVNÍ BENEFITY` | Sekce 3 Q2 odpovědi + sekce 5.2 3D benefity |
| `## 3.` — Mechanismus per benefit | Sekce 5.2 unikátní metodika |
| `## 4. CO PŘESNĚ KLIENT DOSTANE` | Sekce 5.2 komponenty |
| `## 5. CENOVÁ STRUKTURA` | Výběr varianty + sekce 5.2 cena + Q4 odpovědí |
| `## 6. NEJČASTĚJŠÍ NÁMITKY` | Sekce 3 Q3 odpovědi + sekce 6 Den 4 |
| `## 7. SOCIÁLNÍ DŮKAZ` | Sekce 4 credibility + sekce 5.2 důkazy |
| `## 8. PRODEJNÍ SPOUŠTĚČE` | Sekce 5.2 bonusy/garance/urgence |

---

## Zdroj 2 — URL (web_fetch)

Když uživatel pošle URL (`https://…`):

1. Zavolej `web_fetch` na URL
2. Z výsledku extrahuj minimální kontext (viz níže)
3. Pokud URL vede na 404 / nedostupnou stránku → oznam uživateli, požádej o alternativu
4. Pokud stránka je krátká / nedává smysl → polož doplňující otázky (zkrácený manuální)

### Co extrahovat z URL (minimální set)

| Pole | Kde to obvykle je na stránce |
|------|-------------------------------|
| **Název produktu** | H1, title tag, hero section |
| **Jednou větou co dělá** | Subheading pod hlavním H1, hero text |
| **Hlavní benefit / transformace** | „Get X" / „Bez Y" hero copy |
| **Cílová skupina** | „For [koho]" sekce, FAQ, testimoniály |
| **Cena (pokud uvedená)** | Pricing sekce / „Investice" sekce |
| **Pojmenovaný framework / mechanismus** | Sekce „Jak to funguje" / „Náš proces" |
| **Sociální důkazy** | Testimoniály, čísla („1 750+ klientů"), loga |
| **Garance** | „Money-back guarantee" / „garance vrácení" |
| **Urgence** | „Limitovaná místa", „cena platí do…" |
| **Bonusy** | Pricing sekce, „Co dostanete navíc" |

### Pokud URL je hlavní homepage (ne produktová)

- Hledej odkaz na konkrétní produkt v menu / hero CTA
- Zeptej se uživatele: *„Tahle URL vede na celkovou homepage. Pošli mi prosím přímý odkaz na produkt, nebo mi napiš, který z produktů [seznam z menu] tě zajímá."*

### Bezpečnost

- `web_fetch` neposílá API klíče
- Stáhne obsah, parsuj přímo z textu / markdownu
- Ignoruj inline scripty a CSS, soustřeď se na text a strukturu

---

## Zdroj 3 — Manuální popis

Uživatel nalepí text. Skill parsuje volně, hledá minimum 5–7 polí:

- Název produktu
- Co dělá (1 věta)
- Pro koho
- Cena
- Transformace (z → na)
- Hlavní benefit / mechanismus (pokud zmíněno)
- Sociální důkaz (pokud zmíněno)

Pokud manuální vstup je krátký / mlhavý → polož 1 doplňující otázku:

> *„OK, mám: [shrnutí]. Doplňující otázka — [konkrétní chybějící údaj, který nejvíc chybí]?"*

**Max 1 doplňující otázka.** Pokud uživatel napsal „mám jen tohle, zbytek vyplň `[OVĚŘ]`" → respektuj a pokračuj.

---

## Pokud chybí Brand DNA

Brand DNA je silně doporučená (hlas + ideální klient + příběh zakladatele), ale chybí-li:

### Možnost A: nasměrovat na brand-dna skill

> *„Pro úplnou AIQ strategii by se hodil i Brand DNA report (hlas značky, ideální klient). Pusť skill `brand-dna` a vrať se. Bez něj pokračovat můžeme, ale strategie nebude tak personalizovaná na váš hlas."*

### Možnost B: zkrácená varianta (1 dávka otázek)

> *„OK, zkráceně. Řekni mi v jedné zprávě:*
> 1. *Kdo jsi a co děláš (1 věta)*
> 2. *Komu pomáháš (popis ideálního klienta)*
> 3. *Co tě dělá jiným než konkurence*
> 4. *Tonalita značky (formálně / neformálně / odborně / přátelsky / drsně…)*
> 5. *Jak velká je značka (začátek / etablovaná / autorita)"*

Z odpovědí vytvoř zjednodušený `brandDNA.md` v `/documents/brand/` — bude to jednou pro vždy a další skilly z něj budou těžit.

### Možnost C: vytáhnout z URL

Pokud uživatel poslal URL produktové stránky, často je tam i info o autorovi/firmě. Zkus extrahovat:

- Jméno zakladatele / firmy
- Příběh zakladatele („Náš příběh" / „O nás")
- Bio + autorita / credibility
- Tonalita z copy stránky

Co se nepodaří dohledat → `[OVĚŘ S KLIENTEM: …]`.

---

## Audit trail (`00-kontext.md`)

Po načtení vytvoř krátký audit soubor:

```markdown
# AIQ strategie — kontext generace

**Datum generace:** [YYYY-MM-DD HH:MM]
**Produkt:** [název / slug]
**Vybraná varianta lead magnetu:** [Scorecard / Audit / Plan / Calculator / Blueprint] — důvod: [1 věta]

## Zdroj produktového kontextu

- Typ vstupu: [Product DNA / URL / manuální]
- Cesta / URL / hash manuálu: […]
- Datum / verze: […]

## Zdroj brand kontextu

- Typ vstupu: [Brand DNA / zkrácená varianta / z URL / žádný]
- Cesta: […]

## Optional úhel od uživatele (Krok 1)

[text z Krok 1, nebo „bez specifického úhlu"]

## Chybějící data označená `[OVĚŘ S KLIENTEM]`

- [seznam míst v dokumentu s placeholdery]
```

Klient tento soubor nedostává — slouží pro debug a iteraci.

---

## Důležité

- **Žádný YAML frontmatter** v Brand/Product DNA reportech — jsou to čisté markdown soubory, parsuj sekce přímo
- **Strukturovaná data si skill ukládá do `/documents/lead-magnets/AIQ [Quiz title]/`** — ne do brand/product DNA
- **Kde chybí data → `[OVĚŘ S KLIENTEM: konkrétní otázka]`** — nikdy nevymýšlej spekulace
