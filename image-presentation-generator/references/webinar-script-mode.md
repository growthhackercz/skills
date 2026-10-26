# Mód B — z webinářového skriptu

Pokud vstup pochází ze skillu `ultimate-webinar` (nebo uživatel dodá webinářový skript v Markdownu se slidy a speaker notes), neptej se na obsah od nuly — **rozparsuj skript** a namapuj ho na slide plán.

## 1. Parsuj skript

Z markdownu extrahuj:
- **Nadpisy slidů** — typicky `## SLIDE X — Nadpis`
- **Obsah slidů** — bullety, tabulky, citáty (často pod `**Na slidu:**`)
- **Speaker notes** — pod `**Poznámky pro speakera:**` → ulož do `slide-plan.json` pole `speaker_notes` (do obrázku NEJDOU; využijí se v PDF metadatech nebo doprovodném souboru)
- **Parametry** — délka, počet slidů, typ akce

## 2. Mapuj typ slidu → layout (z `slide-layouts.md`)

| Typ ve skriptu | Doporučený layout |
|----------------|-------------------|
| Title slide | `cover-cinematic` / `cover-typographic` |
| Cold open / Hook | `manifesto-statement` / `transition-word` / `cover-cinematic` |
| Kontrast (starý vs nový) | `before-after` / `myth-fact` / `versus-headtohead` |
| Tabulka / srovnání | `pros-cons-panels` / `two-column-text` |
| Case study / číslo | `big-stat` / `three-stat-cards` / `editorial-chart` |
| Stack (narůstající hodnota) | `numbered-steps-vertical` / `pyramid-hierarchy` |
| Proces / kroky | `numbered-steps-vertical` / `timeline-ribbon` / `circular-cycle` |
| Tajemství / sekce | `section-number-fullbleed` / `chapter-opener-photo` |
| Deprivace / dramatický bod | `manifesto-statement` na tmavém moodu, vysoký kontrast |
| Citát / reference | `pull-quote-spread` / `testimonial-portrait` |
| CTA / nabídka | `cta-gradient-panel` |
| Závěr | `endcap-product-context` / `contact-card` |

## 3. Zachovej strukturu

- Pořadí slidů ze skriptu drž 1:1.
- Zachovej fáze (1/2/3) a všechna tři tajemství (Brunson/Perfect Webinar struktura), pokud ve skriptu jsou.
- Aplikuj **variety engine** z `slide-layouts.md` — když po sobě jdou dva slidy stejného typu, vyber pro druhý alternativní layout ze stejné kategorie, ať se kompozice neopakuje.

## 4. Pokračuj normálním workflow

Po namapování pokračuj na Krok 1 (Style Directive z brand-board) → Krok 2 (potvrzení slide plánu, STOP) → dál standardně. Mód B jen nahrazuje „vymýšlení obsahu od nuly" parsováním skriptu.
