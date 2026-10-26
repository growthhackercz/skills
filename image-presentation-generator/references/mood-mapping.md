# Mood Mapping — feeling → visual cue

Přeneseno z `html-presentation-generator` (`animation-patterns.md`). Tam to řídilo animace; tady řídí **mood blok v GPT Image 2 promptu** — jaký pocit má slide vyvolat a jakými vizuálními prostředky.

Použij v Kroku 1 (sestavení Style Directive) a v Kroku 3 (per-slide prompt), abys vybral správný vizuální jazyk. Pocit odvoď z Brand DNA (esence, hlas) a z účelu prezentace.

| Feeling | Vizuální cues do promptu | Sedí k presetům |
|---------|--------------------------|-----------------|
| **Dramatic / Cinematic** | tmavá pozadí, spotlight/vignette, full-bleed fotky, velké měřítko, vysoký kontrast, hloubka | Bold Signal, Dark Botanical, Neon Cyber |
| **Techy / Futuristic** | neonový glow, grid/particle pozadí, mono akcenty, cyan/magenta/electric blue, čisté hrany | Neon Cyber, Terminal Green, Electric Studio |
| **Playful / Friendly** | zaoblené tvary, pastelové/jasné barvy, hravé badge, lehkost, mírná asymetrie | Split Pastel, Pastel Geometry |
| **Professional / Corporate** | navy/slate/charcoal, precizní mřížka, data-viz focus, střídmé akcenty, čisté karty | Electric Studio, Swiss Modern |
| **Calm / Minimal** | hodně whitespace, tlumená paleta, serif typografie, velkorysý padding, jeden klidný prvek | Dark Botanical, Paper & Ink |
| **Editorial / Magazine** | silná typo hierarchie, pull quotes, drop caps, grid-breaking layouty, serif headline + sans body | Vintage Editorial, Notebook Tabs, Paper & Ink |

## Jak mood zapsat do promptu

V sekci „MOOD" Style Directive uveď 3–5 adjektiv + jednu referenční estetiku. Příklad:

```
MOOD: confident, premium, cinematic, focused
REFERENCE AESTHETIC: Apple keynote × Linear product deck
VISUAL CUES: dark focused backgrounds, single dramatic focal element, deep contrast, generous negative space
```

Mood zůstává **konzistentní napříč celým deckem** (je součást Style Directive). Mění se jen kompozice (layout), ne nálada.
