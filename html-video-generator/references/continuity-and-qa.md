# Continuity & QA — proof, carryover, surgical edity

Produkční vrstva, kterou HyperFrames neřeší. Destilát z `saranambiar/hyperframes-video-agent-skills` (Apache-2.0) + naše ověřené.

## Proof-before-done (povinná brána)

**Nikdy „hotovo" bez:** `probe_media.py` (ffprobe metadata) + proof framy na přesných časech + contact sheet — **z renderovaného MP4, NE z prohlížeče.** `render.sh` to dělá automaticky do `qa/proof/`.

Kdy proof: hranice scén (−0.05s, +0.05s, mid-transition, first-settled), změněné timestampy, framy s captions, konec. **Projdi VŠECHNY** (Read). Gates nechytí: neviditelný text, flash, mrtvou scénu, špatnou barvu.

```bash
python3 scripts/extract_proof_frames.py final.mp4 --time hook=0.5 --time reveal=4.0 --time cta=12.0 \
  -o qa/proof --contact-sheet qa/proof/sheet.jpg
```

## ⚠️ Carryover-frame audit (#1 tichý regres)

Pozdější scéna často obsahuje **REKONSTRUOVANOU KOPII** finálního framu předchozí scény (pro plynulý přechod). Když změníš prvek tam, kde se poprvé objeví, **jeho kopie v další scéně zůstane stará** → finál ukáže nový label ve scéně A a starý v prvním framu scény B.

**Při KAŽDÉ změně prvku prohledej:** aktuální scéna → další scéna → každá scéna se stejným titulkem → inline SVG text → osy grafů → hlavičky tabulek → CTA copy → theme barvy. Pak proof na hranici obou scén.

## Surgical-change kontrakt (chraň schválenou práci)

Hodně iterací se promrhá tím, že agent „vylepšuje" už schválené. Před editem vyplň `templates/change-request.md`:
- **Change** — co přesně se mění.
- **Preserve** — co se NESMÍ dotknout (downstream starty, music timing, caption timing, schválený styl, sousední scény).
- **Implementation rule** — najdi nejmenší source artefakt vlastnící změnu; re-renderuj JEN dotčené scény.
- **Proof** — framy na přesných časech (before/after).

5 zákazů: neredesignuj · nesyncuj znovu (pokud to změna nevyžaduje) · neregeneruj nedotčené scény · nepatchuj starý final MP4 když existuje source · vždy zkontroluj carryover.

**Stop podmínky (ptej se, nehádej):** konflikt se zamčenou scénou · chybí source asset · implikuje neschválenou změnu scénáře · nejednoznačný recolor loga.

## Theme-color brána (brand fidelity = claim „API místo shell")

```bash
python3 scripts/scan_theme_colors.py documents/videos/<slug> --allow "#01071A" --allow "#119CFF" --allow "#97F8F4" ...
```
Grepne hex/rgb/hsl mimo povolenou paletu (z frame.md), **exit 1** při nálezu → CI brána. Vyluč loga/produktové footage/reference z recoloringu.

## Smallest timing intervention (audio sync ladder)

Viz `assembly.md`. Pořadí: whole-scene `setpts` → segment map → **hold frame** (ticho/pauza, ne global slowdown) → audio `atempo`. Nikdy nepřetimuj celé video kvůli jedné pauze.
