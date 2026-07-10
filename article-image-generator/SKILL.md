---
name: article-image-generator
description: "Obstará článkové obrázky: u každého sám rozhodne, jestli sáhnout po reálné fotce (Pexels, nebo web fallback), nebo generovat v brand stylu přes image_generate. Funguje z image briefů, ale i sólo — briefy si odvodí přímo z článku. Vždy přidá OG kartu pro sdílení (titulek na brand pozadí). Uloží soubory pod /documents a vytvoří image-manifest.json pro publisher assets krok."
category: creative
status: ready
version: "2.1"
metadata: {"openclaw":{"requires":{"bins":["python3"]},"optionalEnv":["PEXELS_API_KEY"],"emoji":"🖼️"}}
---
# Article Image Generator

Mezikrok mezi článkem a publishingem. Bere `image-briefs.json` a pro každý brief **sám rozhodne zdroj obrázku** — reálná fotka z **Pexels**, nebo generování přes nativní **`image_generate`** (GPT Image 2). Ukládá obrázky a vytváří manifest.

Nepoužívej shell wrapper ani ručně volané OpenRouter/OpenAI HTTP endpointy pro generování. Runtime default/fallback řeší nativní `image_generate`. Pexels se volá výhradně přes `{baseDir}/scripts/pexels.py`.

> **Jen pro články.** Tady dává reálná stock fotka smysl (hero, ilustrační inline). Pro social/reklamu/brand vizuály se stock nepoužívá — tam vyhrává generování v brandu (řeší jiné skilly).

## Vstup — degradační žebřík (skill je plně funkční i sólo)

1. **`/documents/content/blog/{slug}/image-briefs.json`** od article-writera — primární cesta (orchestrace). *(Přechodné období: když na nové cestě nic není, podívej se i na starou `/documents/brand/content/blog/{slug}/` a pracuj tam, kde článek reálně leží — výstupy pak drž ve stejné složce jako briefs.)*
2. **Briefs chybí, ale existuje text článku** (soubor ve složce slugu, nebo text od klienta): **odvoď briefy sám** — hero (16:9) + 1 inline obrázek na každé 2–3 H2 sekce (námět z obsahu sekce, `alt` z kontextu) + OG karta (viz níže). Ulož je jako `image-briefs.json` (stejné schéma) a pokračuj normálně.
3. **Je jen titulek/téma** („doplňte obrázky k článku o výběru kávy"): vyrob aspoň hero + OG kartu z titulku a řekni, že inline obrázky doplníš, až bude text.

Volitelně: cílová složka (výchozí `/documents/content/blog/{slug}/images`), počet obrázků nebo subset `brief.id`, požadavek na regeneraci konkrétního obrázku.

## OG karta — povinný asset každého článku

Ke KAŽDÉMU článku vytvoř navíc **OG obrázek pro sdílení** (`og.png`, 1200×630): titulek článku na brand pozadí. Vždy generovaný (nikdy stock), vždy s brand stylem a pravidly pro text dle `{baseDir}/references/brand-style.md`. Pokud briefs OG neobsahují, přidej ho sám. V manifestu `placement: "og"` — publisher ho použije jako og:image.

## Zdroj obrázku — rozhodni per brief (Pexels vs. generování)

**Máš plnou svobodu rozhodnout u KAŽDÉHO obrázku zvlášť.** Neřiď se pevným štítkem — posuď záměr briefu a rozhodni, co dá lepší výsledek:

**Nakloň se k Pexels (reálná fotka), když:**
- jde o reálnou situaci / člověka / místo (tým u stolu, ruce na klávesnici, kancelář, město, příroda, jídlo)
- autenticita a lidskost zvyšují důvěru čtenáře
- námět je běžný → kvalitní fotka existuje
- na přesné brand paletě u toho obrázku nezáleží

**Nakloň se ke generování (`image_generate`), když:**
- obrázek musí sednout přesně do brandu (barvy, styl, nálada) — typicky hero
- je to specifický/neobvyklý koncept, který stock nemá („AI agent řídí marketingový tým")
- obsahuje text, graf, diagram, infografiku, schéma
- jde o konkrétní produkt nebo abstraktní/futuristický vizuál
- chceš unikátnost (ne fotku, co má každý)

**Klíč — nejdřív se podívej, pak rozhodni.** U foto-námětů si Pexels **prohledej a posuď reálné výsledky** (viz Workflow). Silná trefa → vezmi ji. Slabé, generické nebo mimo téma → generuj. Rozhoduješ podle toho, co reálně vidíš, ne naslepo.

**Když váháš:** hero (musí táhnout a být v brandu) → spíš generuj · ilustrační inline fotky u textu → spíš Pexels. Když nesedí ani čistá fotka, ani čistě brandový vizuál, generuj fotorealistický námět s brand stylem — nekombinuj stock a generování do jednoho obrázku.

**Fallback řetěz (jen u foto-námětů), v tomhle pořadí:**
1. **Pexels API** (přes `pexels.py`) — první volba, strukturované a licenčně čisté.
2. **`web_search`** — když chybí `PEXELS_API_KEY` nebo Pexels nic nevrátí, zkus najít reálnou fotku přes nativní `web_search`. **Jen volné komerční zdroje** (Pexels, Unsplash, Pixabay, Wikimedia Commons); u nejasné licence fotku neber.
3. **`image_generate`** — když ani web nedá použitelnou a licenčně čistou fotku, vygeneruj.

Řetěz se týká jen foto-námětů; branded/koncept/grafika jdou rovnou na generování. Nic se nerozbije — vždy skončíš u nějakého obrázku.

## Workflow

1. Načti `image-briefs.json`.
2. Zkontroluj, že každý brief má `id`, `filename`, `prompt`, `aspectRatio` a `alt`.
3. Ukaž krátký plán: počet obrázků, cílovou složku, poměry stran a **u každého tvůj předběžný zdroj** (Pexels / generovat) s jednořádkovým proč.
4. **Pro každý brief zvol zdroj** dle rámce výše:

   **A) Pexels cesta** (foto-námět):
   1. Odvoď 2–4slovný anglický search dotaz z briefu (subjekt scény, ne celý prompt).
   2. Podívej se na kandidáty:
      ```bash
      python3 {baseDir}/scripts/pexels.py search "<dotaz>" --orientation <landscape|portrait|square> --per-page 6 --min-width 1400
      ```
   3. **Posuď výsledky** (JSON: `preview`, rozměry, `alt`). Sedí námět, kvalita, kompozice, dost velké?
      - **Ano** → stáhni vybraný:
        ```bash
        python3 {baseDir}/scripts/pexels.py download "<download_url>" "/documents/content/blog/{slug}/images/{filename}"
        ```
        Do manifestu ulož `source: "pexels"` + `photographer` a `pexels_url` (atribuce, i když ji Pexels nevyžaduje).
      - **Ne / prázdné / `no_key`** → přejdi na web fallback (A2).

   **A2) Web fallback** (foto-námět, když Pexels selhal nebo chybí klíč):
   1. `web_search` na reálnou fotku k námětu. **Jen volné komerční zdroje** — do dotazu přidej cíl (např. `site:pexels.com` / `site:unsplash.com` / `site:pixabay.com` / „free stock photo").
   2. Posuď výsledek a **ověř licenci** (volné komerční). Nejasná licence → nepoužívej, jdi na generování (B).
   3. Stáhni čistou fotku do cílové cesty (`web_fetch`/`curl` na přímou image URL). Do manifestu `source: "web"` + `source_url` a `license`.
   - Nic použitelného/licenčně čistého → generuj (B).

   **B) Generování** (branded / koncept / grafika / fallback z A i A2):
   - Zavolej nativní `image_generate` s promptem z briefu. Do manifestu `source: "generated"`.

5. Ulož rastrový soubor pod `/documents/content/blog/{slug}/images/{filename}`.
6. Ověř, že každý soubor existuje a není prázdný.
7. Vytvoř `/documents/content/blog/{slug}/image-manifest.json`.

## image-manifest.json

```json
{
  "articleSlug": "{slug}",
  "sourceBriefs": "/documents/content/blog/{slug}/image-briefs.json",
  "generatedAt": "YYYY-MM-DDTHH:mm:ssZ",
  "images": [
    {
      "id": "hero",
      "placement": "hero",
      "localPath": "/documents/content/blog/{slug}/images/hero.png",
      "filename": "hero.png",
      "aspectRatio": "16:9",
      "alt": "Alt text",
      "source": "generated",
      "prompt": "Prompt actually used (jen u source=generated)",
      "photographer": "Jméno autora (jen u source=pexels)",
      "pexels_url": "https://www.pexels.com/photo/... (jen u source=pexels)",
      "status": "ok"
    }
  ]
}
```

`source` je `"pexels"`, `"web"` nebo `"generated"`. U Pexels/web vynech `prompt` a doplň atribuci (`photographer`+`pexels_url`, u webu `source_url`+`license`); u generování vynech atribuci.

## Prompt pravidla (pro generování)

- **Brand styl je povinný pro hero, OG kartu a branded/koncept námaty:** slož styl blok přesně podle `{baseDir}/references/brand-style.md` (HEX barvy z DESIGN.md + nálada z brandDNA). Bez brand podkladů generuj neutrálně a do manifestu přidej `"brandStyle": "none"`. Ilustrační inline fotorealismus brand blok nepotřebuje.
- Prompt piš anglicky, pokud uživatel nechce jinak.
- Popiš subjekt, scénu, styl, kompozici, světlo, náladu a účel.
- Bez textu → přidej `NO text, NO logos, NO watermarks`. S textem (OG karta) → text přesně v uvozovkách, česky s diakritikou, pravidla v `references/brand-style.md`; překlep = 1 regenerace, pak text zjednoduš.
- Provider-neutral prompt (neoptimalizuj zvlášť pro Gemini/GPT Image 2, pokud uživatel nechce).

## Pexels pravidla

- Volej jen `{baseDir}/scripts/pexels.py` (žádný ruční `curl` na Pexels — klíč out of logs).
- Dotaz krátký a anglicky (2–4 slova), orientace dle `aspectRatio` briefu, `--min-width` ať fotka není malá.
- Nikdy neber první výsledek naslepo — posuď `preview` a rozměry.
- Licence Pexels = volné komerční, bez povinné atribuce; autora přesto ulož do manifestu.

## Výstup do chatu

```markdown
# Obrázky hotové

- **Manifest:** `/documents/content/blog/{slug}/image-manifest.json`
- **Složka:** `/documents/content/blog/{slug}/images/`
- **Počet:** {count} ({p} z Pexels, {g} generováno)

Další krok: cílový publisher `assets` příkaz (`wordpress-publisher` nebo `cliqsales-blog-publisher`).
```

## Failure handling

- `image_generate` selže → nehlaš úspěch; do manifestu jen úspěšné, vrať přesnou chybu. Selže hero → zastav pipeline.
- Pexels `no_key` / `request_failed` / nula výsledků → **není chyba**, jen postup po fallback řetězu: web_search → generování.
- `web_search` nic licenčně čistého → generuj. Při jakékoli nejistotě o licenci vždy raději generuj.
- `pexels.py download` selže → zkus jiného kandidáta, pak web fallback, pak generuj.
