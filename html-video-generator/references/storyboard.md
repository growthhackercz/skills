# Storyboard — scene-spec, timestamp sémantika, scaffolding

## Timestamp sémantika (kodifikuj v každém spec — odstraňuje #1 nejednoznačnost)

| Zápis | Význam |
|---|---|
| `At 5s` | prvek viditelný NEJPOZDĚJI v 5s |
| `Start around 3s` | smí začít dřív, ale viditelný do 3s |
| `Land by 10s` | finální stav v/před 10s |
| `Hold for 3s` | žádná velká změna layoutu 3s |
| `Do not appear before 6s` | výchozí stav skrytý, reveal až po cue |

Vždy zaznamenej **local (od startu scény) vs global (od startu videa)**.

## Scene-spec (per scéna, šablona `templates/scene-spec.md`)

Identity (id, délka, track) · Intent (co divák cítí/pochopí) · Inputs (catalog blok, obrázky, copy) · Visual direction · **Beat timeline tabulka: Čas | Narrace/cue | Vizuální akce | Required proof** · Continuity (starts-from / ends-on) · QA checklist.

## Storyboard (multi-scéna, šablona `templates/storyboard.md`)

Hlavní **tabulka Scény** má jen lidsky čitelné sloupce (**Scéna | Stav | Délka | Text na obrazovce | Co se děje | Zvuk**) — to je to, co uživatel čte a schvaluje. Návazové zámky (**začíná-z / končí-na / zamčeno**, ochrana schválených scén před přepsáním) jdou do **interní sekce pod čarou**, ne do hlavní tabulky. Celý storyboard je **česky, vykání** (klientský výstup). + global rules + asset map + render map.

## Story arcs

- **Launch 30–45s:** hook → product-reveal (catalog hero) → feature-trio → stat-proof → CTA → logo-sting.
- **Feature 30s:** hook → ui-demo/3D showcase → feature → stat → CTA.
- **Sales 90–180s:** hook → problém (×2) → reveal → demo → feature bloky ×2–3 (jiný obsah!) → stat → social-proof → offer → CTA → sting. Žádná scéna >12s; 12–20 scén; opakovaná šablona jen s jiným obsahem A jiným transition.

## Scaffolding (Krok 2)

```bash
npx hyperframes@0.6.97 init documents/videos/<slug> --resolution <landscape|portrait|square>   # poměr stran z Kroku 0 (16:9 / 9:16 / 1:1); volitelně --example <name>
cd documents/videos/<slug> && npx hyperframes@0.6.97 add <catalog-blok>
```
**Project konvence** (Sara): `compositions/ renders/ assets/ snapshots/ assembly/ captions/`. Jedna kompozice per scéna. Media relativní cesty. frame.md do rootu projektu (HyperFrames ho čte).

## Reference assets (killer na iterace)

Pro každé video složka referencí: logo, produktové screenshoty, brand assety, **concept image cílového framu** (FAL/GPT), předchozí scény. **Assety > prompty** — ukázat layout je lepší než ho popsat. Nejrychlejší projekty = víc času na přípravu kontextu před generací.

## Separuj specifický obsah od znovupoužitelného vzoru

Jména/loga/copy = per video. Camera-swipe/chart-draw/proof = vzor → do skillu. Jen vzory „graduují" do referencí.
