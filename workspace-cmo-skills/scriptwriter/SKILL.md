---
name: scriptwriter
description: Napište skripty videoreklam s úplnými poznámkami k produkci. Vytváří rozdělení scén po scéně včetně dialogů, návrhů B-roll, textu na obrazovce, směru kamery a načasování. Výstupy jednotlivých souborů skriptů plus kombinovaný přehled ke schválení.
category: creative
status: ready
version: "1.0"
publishedAt: "2026-04-25"
---

# Scénář

Napište scénáře videoreklam připravené pro produkci pro social/Meta kampaně.

## Výstupní struktura

### Jednotlivé soubory skriptů (pro produkci)
```
/documents/{project-slug}/creative/scripts/
├── 01-{script-name}.md
├── 02-{script-name}.md
└── ...
```

### Kombinovaný přehled (pro schválení)
```
├── scripts-overview.md    # All scripts in one doc
```

## Šablona skriptu

Každý soubor skriptu má tuto strukturu:

```markdown
# {Brand} Video Ad Script: {Title}

**Duration:** {X} seconds  
**Format:** {Talking head / Screen recording / Animation / Mixed}  
**Aspect Ratio:** {9:16 / 1:1 / 16:9}  
**Funnel Stage:** {TOFU / MOFU / BOFU}  
**Landing Page:** {URL}

---

## 📋 Overview

| Element | Details |
|---------|---------|
| **Hook** | {One-line hook strategy} |
| **Emotion** | {Emotional journey: X → Y → Z} |
| **CTA** | {Call to action} |
| **Tone** | {Voice/energy description} |

---

## 🎬 SCENE 1: HOOK (0:00 - 0:03)

### Shot
- **Type:** {Shot type}
- **Setting:** {Location/background}
- **Energy:** {Mood/energy level}

### Dialogue
> "{Exact words}"

### On-Screen Text
```
{Text, který se objeví na obrazovce}
```

### B-Roll Options
1. {Option 1}
2. {Option 2}

### Direction
- {Camera/performance direction}
- {Timing notes}

---

[Continue for each scene...]

---

## 📝 FULL SCRIPT (Clean Copy)

{Complete script without formatting for teleprompter}

**Word count:** {N} words  
**Reading time:** ~{N} seconds

---

## 🎨 THUMBNAIL CONCEPT

{2-3 thumbnail options with descriptions}

---

## 🎥 PRODUCTION NOTES

{Equipment, recording tips, editing notes}

---

## 📊 VARIATIONS TO TEST

| Element | A | B |
|---------|---|---|
| {Element} | {Version A} | {Version B} |

---

## ✅ PRE-PUBLISH CHECKLIST

- [ ] Audio is clear
- [ ] Captions added
- [ ] End card holds 2+ seconds
- [ ] Landing page works
- [ ] Link in description/comments
```

## Struktura skriptu podle trvání

### 15sekundový skript (Stories/Reels)
```
[0-2s]  HOOK - Pattern interrupt
[2-8s]  VALUE - One key insight
[8-13s] CTA - Clear next step
[13-15s] END CARD
```

### 25–30 sekundový scénář (standardní)
```
[0-3s]   HOOK - Pattern interrupt
[3-10s]  PROBLEM - Agitate pain point
[10-20s] SOLUTION - Present offer
[20-27s] PROOF + CTA - Social proof + action
[27-30s] END CARD
```

### 45–60 sekundový scénář (dlouhý formát)
```
[0-5s]   HOOK - Strong opening
[5-15s]  PROBLEM - Deep agitation
[15-30s] SOLUTION - Explain transformation
[30-45s] PROOF - Testimonials/results
[45-55s] CTA - Clear call to action
[55-60s] END CARD
```

## Hákové vzorce

### Přerušení vzoru
> "Pokud se stále chováte [špatně], jste [následek]."

### Mezera zvědavosti
> "Já [dosáhl jsem výsledku] a tady je to, co vám nikdo neřekne..."

### Kontroverzní záběr
> "Přestaňte [běžná rada]. Zde je to, co skutečně funguje."

### Identity Call-out
> "Toto je pro [konkrétní osobu], která [konkrétní situace]..."

### Háček na otázky
> "Proč dělat [překvapivou věc], když můžete [lepší alternativu]?"

### Vedení výsledku
> "[Společnost] přešla z [před] do [po]. Zde je návod."

## Pokyny pro text na obrazovce

1. **Keep it short** – maximálně 3–5 slov na textový prvek
2. **Posílit, neopakovat** — Přidat do dialogu, neduplikovat
3. **Používejte hierarchii** — Důležitá slova větší/bolder
4. **Načasovat to správně** — Objevte se s dialogem, ne dříve
5. **Konzistentní umístění** — Stejná oblast v celém videu

### Styly textu
```
EMPHASIS: All caps, bold
"Quote style": In quotation marks
Stat/number: Large, accent color
CTA: Arrow or emoji pointing (👇 ➡️)
```

## Kategorie B-Roll

### Záznamy obrazovky
- Rozhraní nástrojů (ChatGPT, Make atd.)
- Workflow běžící automatizace
- Výsledky/dashboards
- Náhled kurzu/product

### Variace mluvící hlavy
- Různé úhly (rovný, 3/4)
- Různé rámy (těsné, střední, široké)
- Gesta a reakce

### Stock/Generic
- Osoba pracující na notebooku
- Týmová spolupráce
- Frustrace → momenty úspěchu
- Abstraktní technické vizuály

### Specifické pro značku
- Snímky obrazovky produktu
- Ohlasy zákazníků (klipy)
- V zákulisí
- Záznam události

## Emocionální oblouky

### TOFU (uvědomění)
```
Frustration → Curiosity → Hope
"I'm stuck" → "Wait, what?" → "I could do this"
```

### MOFU (zvážení)
```
Skepticism → Understanding → Confidence
"Does this work?" → "This makes sense" → "I need this"
```

### BOFU (rozhodnutí)
```
Hesitation → Trust → Urgency
"Is it worth it?" → "Others got results" → "I should act now"
```

## Pokyny pro stimulaci

| Doba trvání | Slova | Tempo |
|----------|-------|------|
| 15s | 35-45 | Rychlý, úderný |
| 30. léta | 65-80 | Konverzační |
| 45 let | 100-120 | Místnost k dýchání |
| 60. léta | 140-160 | Tempo vyprávění |

**Pravidlo:** 2,5–3 slova za sekundu pro přirozené předávání.

## Workflow

### 1. Přijměte stručnou zprávu
Od `/campaign_planner` nebo přímého požadavku:
- Koncept reklamy a fáze trychtýře
- Cílová doba trvání
- Klíčové body messagingu
- Vstupní stránka
- Pokyny pro hlas značky

### 2. Napište scénář
- Začněte háčkem (nejdůležitější)
- Vybudujte emocionální oblouk
- Časový limit pro každou sekci
- Přidejte návrhy B-roll
- Zahrnout text na obrazovce

### 3. Recenze & polština
- Čtěte nahlas kvůli načasování
- Zkontrolujte počet slov vs trvání
- Ujistěte se, že CTA je prázdné
– Ověřte zarovnání vstupní stránky

### 4. Přidejte výrobní poznámky
- Koncepty miniatur
- Varianty testu A/B
- Návrhy na vybavení
- Úprava poznámek

### 5. Doručte
- Uložit individuální soubor skriptu
- Přidat do přehledového dokumentu
- Odeslat ke schválení

## Konvence pojmenovávání souborů

```
{NN}-{slug}.md

01-free-crash-course.md
02-ai-readiness-quiz.md
03-ai-operator-course.md
04-team-training-case-study.md
```

## Přehled Struktura dokumentu

```markdown
# {Brand} Campaign Scripts Overview

**Campaign:** {Name}
**Total Scripts:** {N}
**Date:** {YYYY-MM-DD}

---

## Summary

| # | Script | Duration | Funnel | Status |
|---|--------|----------|--------|--------|
| 1 | Free Crash Course | 30s | TOFU | ✅ Ready |
| 2 | AI Readiness Quiz | 25s | TOFU | ✅ Ready |
| 3 | AI Operator Course | 35s | MOFU | ✅ Ready |
| 4 | Team Training | 40s | BOFU | ✅ Ready |

---

## Script 1: Free Crash Course

[Full script content]

---

## Script 2: AI Readiness Quiz

[Full script content]

---

[Continue for all scripts...]
```

## Integrace

Pracuje s:
- `/campaign_planner` — Poskytuje kreativní slipy
- `/creative_director` — Orchestruje kompletní tvorbu aktiv
- `/ad_designer` – Vytváří doprovodné grafické reklamy
- `/page_designer` – Vytváří vstupní stránky, na které odkazují skripty

## Quality Checklist

Před doručením jakéhokoli skriptu:

- [ ] Hook upoutá pozornost během prvních 3 sekund
- [ ] Emocionální oblouk je jasný
- [ ] Dialog zní přirozeně (čti nahlas)
- [ ] Počet slov odpovídá trvání
- [ ] CTA je konkrétní a jasné
- [ ] Text na obrazovce zesiluje (nikoli duplikáty)
- [ ] Návrhy B-roll jsou použitelné
- [ ] Včetně konceptů miniatur
- [ ] Poskytnuty varianty A/B
