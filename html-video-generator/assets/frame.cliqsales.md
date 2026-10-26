# FRAME.md — CliqSales (motion design system pro video)

> Obdoba `DESIGN.md`, ale přepsaná pro video frame: pacing, scale, dwell, motion, kompozice. Default **16:9**; pro **9:16 / 1:1** přepočítej kompozici (vertikální stack, hero zabírá víc výšky), ne crop.
> Zdroj brandu: `documents/brand/brandDNA.md` + `DESIGN.md`. Klientský text = vykání.

## Overview

Moderní, high-tech, **prémiový dark-mode**. Sebevědomé, energické, „bez omáčky". Tmavé navy plátno, cyan→mint glow jako jediný signature akcent, velká tučná Manrope typografie. Pocit „tady to někdo umí a doručí". CliqSales prodává **AI tým, ne nástroj** — vizuál má působit jako živý systém, ne statická prezentace.

## Colors

| Role | HEX | Použití ve videu |
|---|---|---|
| Pozadí (base) | `#01071A` | hlavní plátno všech scén, dark-mode základ |
| Pozadí (panel) | `#0A1228` / `#0F1A33` | karty, dashboard panely, hloubkové vrstvy |
| Ink (primární text) | `#FFFFFF` | headliny, čísla |
| Ink (sekundární) | `#A5A5A5` | body text, popisky (NE off-bílá) |
| **Akcent — Cyan** | `#119CFF` | CTA, klíčová zvýraznění, glow, aktivní stavy |
| **Akcent — Mint** | `#97F8F4` | druhý konec gradientu, jemné highlighty |
| Signature gradient | `linear-gradient(165deg, #119CFF, #97F8F4)` | hero akcenty, CTA buttony, glow okraje |
| Success | `#4ADE80` | pozitivní metriky (růst, „aktivní") |

⚠️ Žádné full-screen lineární gradienty na tmavé (H.264 banding) — radial glow + lokální akcenty.

## Typography

- **Headliny:** **Manrope** 700–900, letter-spacing −2.4 až −3px. Hero ve videu **96–130px** (větší než web, frame se má vyplnit).
- **Subheady / h3:** **DM Sans** 500–700.
- **Eyebrows (uppercase):** **Nunito Sans** bold, letter-spacing +6 až +9px, 24–30px.
- **Čísla / metriky:** Manrope 800, `font-variant-numeric: tabular-nums`.
- Radius: **12px** (panely), 999px (pilulky/CTA).
- Fallback když fonty nejsou jako .woff2: Inter (a varuj).

## Motion (klíč k „není to slide")

- **Kontinuální kamera v KAŽDÉ scéně** — celou dobu běží znatelný pohyb (parallax, push-in, pan, 3D drift), ne „najede a stojí". Statický frame = mrtvý frame.
- **Easing podpis:** `expo.out` / `power4.out` (sebevědomé, rychlý start), overshoot `back.out(1.2–1.6)` na akcentech. Dreamy přechody `sine.inOut`.
- **Timing:** energický, ale prémiový. Hero entrance 0.5–0.8s, holdy krátké, mezi-scénové přechody 0.3–0.6s.
- **Depth:** vždy 3+ vrstvy (glow pozadí, hloubkové panely, foreground). 3D kde to dává smysl (floating UI, device, parallax).
- **Hero beaty:** 1–3× za video catalog VFX (3D showcase / portal / glass) nebo html-in-canvas.
- **Transitions:** shader/zoom-through na hero reveal, blur crossfade na spojovací scény. Žádné jump cuty.

## Frame composition

- **Vyplň frame** — hero text 60–80% šířky. Žádný malý web-sized prvek uprostřed prázdna.
- **Safe area 120 px** — obsah (text, karty, fotky) nikdy nelepit na okraje framu; velké prvky uvnitř safe area, okolo dýchající white space. Nataženo ke krajům = stísněné, amatérské.
- **Dark plátno s glow** — radial cyan glow jako atmosféra, nikdy plochá čerň.
- **Kotvi k hraně / split frame** — dashboard vlevo, text vpravo; ne centrovaný stack.
- Hloubka přes vrstvení panelů + stíny + blur near/far.

## Voice & content

- Tón: sebevědomý, praktický, energický, lidský. Krátké úderné věty + tvrdá čísla.
- Klíčová slova: AI tým, AI agent, „pracuje za vás", 24/7, na klíč, AI Marketér/Obchodník/Provozní Manažer.
- Struktura: **hook → story → proof → CTA**.

## Do's and Don'ts

**Do:** dark navy vždy · cyan→mint gradient jako jediný signature akcent · Manrope dominantně · vyplnit frame · kontinuální pohyb · generické role agentů (AI Marketér, ne Marc) · vykání.

**Don't:** ❌ světlé pozadí (logo je bílé, zanikne) · ❌ statický „slide" layout · ❌ slova „platforma / nástroj / SaaS / druhý mozek" · ❌ konkrétní jména agentů (Steve, Marc) · ❌ cizí fonty · ❌ akcent jinou barvou než cyan/mint.
