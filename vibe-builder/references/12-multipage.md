# Multipage — jeden svět, N stránek

Načti, když sitemap > 1 stránka. Web pattern (sekce, landing anatomie) je
v 06-patterns.md — tento soubor řeší, jak z jedné stránky udělat celý web,
aniž vznikne chaos (každá stránka jiný svět) nebo nuda (všechny stránky
stejná šablona).

## Princip: svět konstantní, choreografie per stránka

- **Jednou pro celý web:** Web DNA, koncept, `webDNA.md` (paleta, typo,
  signature ease, motion tier), nav, footer, CTA styl. Stránky jsou
  kapitoly téhož světa.
- **Per stránka:** sada composition anchors (nikdy kopie homepage), hero
  archetyp (Giant smí jen homepage; podstránky Mini/Mid), rytmus sekcí,
  vlastní obrázkové sloty (z téhož řetězu světa).

## Postup

1. **Sitemap v briefu.** Zjisti mapu (3–7 stránek) a účel každé:
   Persuade (přesvědčit) / Read (přečíst) / Operate (udělat úkon).
   Zapiš do `webDNA.md` sekce Sitemap: stránka → účel → anchors.
2. **Homepage first.** Postav, projeď brány, screenshot, klient schválí
   → homepage se stává vzorem: definuje sdílené komponenty a motion jazyk.
   → STOP před stavbou zbytku.
3. **Podstránky po jedné** (nikdy všechny naráz — malé kroky s bránou mezi
   nimi drží kvalitu). Každá čte `webDNA.md` + sdílené komponenty; layout
   navrhuje vlastní. Po každé stránce brány + screenshot.
4. **Křížová kontrola na konci:** nav odkazy vedou na existující routy,
   aktivní stav nav odpovídá stránce, žádná stránka nesdílí identickou
   kostru anchors s jinou.

## Next.js struktura

```
app/
  layout.tsx        ← nav + footer + fonty (jednou)
  template.tsx      ← jemný page-transition fade (respektuje reduced-motion)
  page.tsx          ← homepage
  <route>/page.tsx  ← podstránky (sluzby/, o-nas/, kontakt/, ...)
components/
  sections/         ← sdílená knihovna sekcí (Hero, CTA, Footer, ...)
  motion/           ← scény, reveals (per komponenta, useGSAP se scope)
lib/motion.ts       ← brandEase + DUR škála (z webDNA.md)
```

- `output: 'export'` generuje všechny routy staticky → netlify-publisher
  beze změny. (Funnel s formuláři zůstává statický, kontakt bere serverová funkce —
  viz 15-lead-magnet-pages.md a 16-aplikace.md.)
- České routy: kebab-case bez diakritiky (`/o-nas`, `/sluzby`, `/kontakt`).
- Metadata per stránka: `title` šablona `%s — <Brand>`, description z copy
  stránky, OG image z hero slotu stránky.
- 404: vlastní `not-found.tsx` ve světě brandu (drobný second-read moment
  je tu vítaný).

## Motion napříč stránkami

- Reveals žijí per komponenta (`useGSAP` + scope) → fungují na každé
  stránce automaticky, žádná globální orchestrace.
- Vrstvená scéna (tier 2) je typicky JEN na homepage; podstránky drží
  tier 1 slovník + max 1 menší pinnutý moment tam, kde to účel unese
  (Persuade ano, Read/Operate ne).
- `template.tsx` přechod: fade/rise 300–400 ms s brandEase; pod
  reduced-motion žádný přechod.

## Nav a footer

- Nav: skutečné odkazy (`next/link`), aktivní stav (`usePathname`),
  mobilní menu plnohodnotné (ne schované odkazy). Nav nese logo (identita)
  a 1 primární CTA — nejsebevědomější prvek chrome.
- Footer: reálné kontakty a sociální odkazy z briefu; chybí-li, vynech —
  nikdy placeholder `#`.
