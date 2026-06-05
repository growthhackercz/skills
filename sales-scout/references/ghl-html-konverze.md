# Konverze Markdown → GHL Rich Text HTML

Sales Scout brief je psán v Markdownu (lidsky čitelný, snadno se kontroluje). Helper `ghl_scout_push.py` ho před vložením do CliqSales CRM konvertuje na **GHL Rich Text HTML** — omezenou podmnožinu HTML, kterou CliqSales notes editor podporuje.

## Co GHL Rich Text podporuje

Podle oficiální dokumentace ([help.gohighlevel.com](https://help.gohighlevel.com/support/solutions/articles/155000006459)) editor poznámek podporuje:

| Prvek | HTML element | Markdown vstup |
|---|---|---|
| Bold | `<strong>` | `**text**` |
| Kurzíva | `<em>` | `*text*` |
| Podtržení | `<u>` | (Markdown nemá, lze přes HTML pass-through) |
| Přeškrtnutí | `<s>` | `~~text~~` |
| Odrážkový seznam | `<ul><li>` | `- text` |
| Číslovaný seznam | `<ol><li>` | `1. text` |
| Odkaz | `<a href="...">` | `[text](url)` |
| Odstavec | `<p>` | dvojitý nový řádek |

## Co GHL Rich Text **NE**podporuje

Tyto Markdown prvky musíme **převést** na něco jiného:

| Prvek | Markdown vstup | Co s tím udělá konvertor |
|---|---|---|
| Nadpis H2 | `## Nadpis` | `<p><strong>Nadpis</strong></p>` (bold odstavec) |
| Nadpis H3 | `### Nadpis` | `<p><strong><em>Nadpis</em></strong></p>` (bold + kurzíva odstavec) |
| Nadpis H4+ | `#### Nadpis` | totéž jako H3 |
| Tabulka | `\| col1 \| col2 \|` | převést na bullet list s bold-prefixem: `<ul><li><strong>col1:</strong> col2</li></ul>` |
| Inline code | `` `code` `` | `<em>code</em>` (kurzíva jako náhrada) |
| Code block | ` ```code block``` ` | `<blockquote>code block</blockquote>` (blockquote jako vizuální oddělení) |
| Obrázek | `![alt](url)` | převést na odkaz: `<a href="url">[obrázek: alt]</a>` |
| Horizontální čára | `---` | `<p>— — —</p>` (vizuální oddělení textem) |

## Co si v briefu **nepoužíváme** (proto, abychom konvertor nezatěžovali)

- Tabulky — místo nich bullety s bold-prefixem (`**Klíč:** hodnota`)
- Code blocky — brief je text, ne kód
- Obrázky — brief je text, screenshoty se neukládají
- Nadpisy H3+ — všechno se vleze do H2 + bold uvnitř

Důsledek: konvertor je jednoduchý a robustní.

## Příklad konverze

### Vstup (Markdown brief)

```markdown
🔎 **SCOUT BRIEF** — Effect Clinic, 2026-05-25, webhook

## 📋 Základní údaje

- **Firma:** Effect Clinic
- **IČO:** 12345678
- **Web:** [https://effectclinic.cz](https://effectclinic.cz)

## 🎯 Shrnutí fitu pro Bioptron MedAll

**Fit: A / velmi dobrý**

Effect Clinic je vhodný lead, protože kombinuje *estetickou medicínu* a laserové zákroky.
```

### Výstup (GHL Rich Text HTML)

```html
<p>🔎 <strong>SCOUT BRIEF</strong> — Effect Clinic, 2026-05-25, webhook</p>

<p><strong>📋 Základní údaje</strong></p>

<ul>
  <li><strong>Firma:</strong> Effect Clinic</li>
  <li><strong>IČO:</strong> 12345678</li>
  <li><strong>Web:</strong> <a href="https://effectclinic.cz">https://effectclinic.cz</a></li>
</ul>

<p><strong>🎯 Shrnutí fitu pro Bioptron MedAll</strong></p>

<p><strong>Fit: A / velmi dobrý</strong></p>

<p>Effect Clinic je vhodný lead, protože kombinuje <em>estetickou medicínu</em> a laserové zákroky.</p>
```

### Jak to vypadá v CliqSales UI

> 🔎 **SCOUT BRIEF** — Effect Clinic, 2026-05-25, webhook
>
> **📋 Základní údaje**
>
> - **Firma:** Effect Clinic
> - **IČO:** 12345678
> - **Web:** [https://effectclinic.cz](https://effectclinic.cz)
>
> **🎯 Shrnutí fitu pro Bioptron MedAll**
>
> **Fit: A / velmi dobrý**
>
> Effect Clinic je vhodný lead, protože kombinuje *estetickou medicínu* a laserové zákroky.

Tj. **strukturované, formátované, klikatelné odkazy** — ne raw Markdown text s `**` znaky.

## Implementace v `ghl_scout_push.py`

Helper má funkci `md_to_ghl_html(markdown_text: str) -> str` postavenou na regulárních výrazech (lehký konvertor, žádné externí knihovny). Pravidla aplikuje v tomto pořadí:

1. **Code blocks** (` ```...``` `) → `<blockquote>...</blockquote>` (jako první, aby se uvnitř nezpracovaly další prvky)
2. **Tabulky** (`| col1 | col2 |\n|---|---|\n| val1 | val2 |`) → bullet list s bold-prefixem (každý řádek = jeden bullet, sloupce přes `**Header:** value`)
3. **Headings** (`## Nadpis`) → `<p><strong>Nadpis</strong></p>` (H2 i hlubší — všechny dostanou stejný bold odstavec, H3+ navíc kurzívu)
4. **Bullet listy** (řádky začínající `- `) → `<ul><li>...</li></ul>` (skupiny sousedních bulletů do jednoho `<ul>`)
5. **Číslované listy** (řádky začínající `1. `, `2. `, …) → `<ol><li>...</li></ol>`
6. **Inline code** (`` `code` ``) → `<em>code</em>`
7. **Bold** (`**text**`) → `<strong>text</strong>`
8. **Kurzíva** (`*text*`) → `<em>text</em>` (pozor na konflikt s bullety — proto až po krokech 4 a 5)
9. **Přeškrtnutí** (`~~text~~`) → `<s>text</s>`
10. **Odkazy** (`[text](url)`) → `<a href="url">text</a>`
11. **Obrázky** (`![alt](url)`) → `<a href="url">[obrázek: alt]</a>`
12. **Horizontální čára** (`---` na samostatném řádku) → `<p>— — —</p>`
13. **Odstavce** (zbylý text oddělený prázdným řádkem) → obalit `<p>...</p>`

**Žádné nested headings ani složité kombinace.** Pokud brief obsahuje něco nečekaného, konvertor zachová původní text (graceful degradation — uživatel uvidí raw text místo formátování, ale brief je čitelný).

## Debug / preview

Helper má CLI flag `--preview-html` — místo POST na GHL vypíše konvertovaný HTML do stderr. Užitečné pro debugging:

```bash
python3 ghl_scout_push.py --contact-id abc123 --note-body-file brief.md --preview-html
```

Výstup do stderr:
```html
<!-- GHL Rich Text preview -->
<p>🔎 <strong>SCOUT BRIEF</strong> — ...</p>
...
```

A `result.json` na stdout: `{"preview": true, "html_length": 2450, "html_md5": "..."}`. Žádný POST se neprovede.

## Pokud GHL HTML render selže (vizuální problém v UI)

V budoucnu (verze 0.3+) můžeme přidat unit test `tests/test_md_to_html.py`, který volá `md_to_ghl_html()` na sadu vzorových briefů a porovná HTML output s očekávaným.

Pro v0.2 spoléháme na ruční ověření — Pavel po prvním reálném testu (Bioptron) zkontroluje, jak poznámka vypadá v CliqSales UI, a pokud něco vypadá špatně, opravíme konvertor v další iteraci (v0.3).
