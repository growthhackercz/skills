# Kinetická typografie — anti-„prezentace" zbraň

**Princip č. 1:** statický text na pozadí = vypadá to jako PowerPoint. **Pohyblivá (kinetická) typografie je hlavní věc, co video odliší od prezentace.** Proto **kinetiku používej hodně** — na každý headline a klíčové slovo, ne výjimečně.

Bereme z **oficiální HyperFrames catalog knihovny** (text/caption komponenty), ne vymýšlíme od nuly:

```bash
npx hyperframes add caption-kinetic-slam caption-editorial-emphasis morph-text shimmer-sweep
```

## Kurátorovaná sada (používej tyhle) ⭐

- **`caption-kinetic-slam`** — full-screen jedno slovo, **střídavé směry náletu**. Na úderná slova / pointy („Hotovo.", „Vyprodáno.", „Letí!"). **Používej hodně** — největší rozdíl oproti slideu.
- **`caption-editorial-emphasis`** — dvou-fontový systém s **dramatickým kontrastem velikostí** na emphasis slova (malé „normální" + obří „klíčové"). Editorial, prémiové, magazínové.
- **`morph-text`** — gooey morph mezi slovy (SVG threshold + blur). Plynulé střídání slov v jednom místě.
- **`shimmer-sweep`** — světelný sweep přes text (CSS gradient mask). Na AI/premium akcenty a reveal.
- doplňkově: `caption-clip-wipe` (per-word clip reveal), `caption-gradient-fill` (gradient + elastic bounce), `caption-particle-burst` (klíčové slovo → částice), `caption-weight-shift` (font-weight přechod), `texture-mask-text` (textura skrz písmena).

## Recepty (i bez catalog bloku — kódovaně v GSAP)

- **Per-word reveal:** rozsekej headline na `.w` spany, stagger 0.08–0.1 s, vstup velocity-slide + `filter:blur(10→0)` + `power4.out`. (Žádný plochý fade celého řádku.)
- **Editorial emphasis:** klíčové slovo **1.5–2× větší** + gradient clip (cyan→modrá) + zbytek menší/lehčí. Kontrast nese pozornost.
- **Kinetic slam:** úderné slovo přiletí celé přes frame z jiného směru než předchozí (L→R, pak shora…), tvrdý dojezd `back.out(1.6)` + uniformní squash na dopadu (NE non-uniformní = neroztahuj písmo).
- **Gradient akcent:** akcentní část headline `-webkit-background-clip:text` v brand gradientu (clip MUSÍ být na animovaném elementu, jinak zmizí).
- **Shimmer:** přejezd světelného highlightu přes „AI" / klíčové slovo po naskočení.

## Pravidla

- **Každý headline = kinetický**, ne statický. Klíčové slovo zvýrazni (velikost/gradient/slam).
- **Jemnost vs síla:** dynamika ANO, ale ne agresivní rotace/overshoot (viz `production-recipes.md` §4) — drž `back.out(1.4–1.8)`, tuhé písmo.
- **Pozor na dětinskost** — silná kinetika ≠ poskakující bublinkové fonty. Prémiové, ostré, sebevědomé.
- Brand fonty (Manrope/Inter), brand gradient na akcenty.
