---
name: ad-generator-gpt-image-2
description: "Samostatný šablonový generátor statických reklam z Brand DNA a Product DNA pomocí nativního image_generate / GPT Image 2; použij pro produktové, brandové a Meta/social ad vizuály mimo ad-strategist pipeline."
category: creative
status: ready
version: "1.0"
publishedAt: "2026-05-02"
---

# Generátor statických reklam - GPT Image 2

Generuj produkčně použitelné statické reklamní obrázky pro značku nebo produkt tak, že převedeš Brand DNA a Product DNA do vyplněných reklamních šablon a finální obrázky vygeneruješ přes nativní `image_generate` / GPT Image 2.

Toto je Control Center adaptace původního workflow Static Ad Generator. Původní flow používalo `~/brands`, FAL, `FAL_KEY` a `generate_ads.py`; tato verze používá sdílený brand kit v `/documents` a nativní image tool.

## Vztah k `ad-image-creator`

Tento skill nech jako samostatný šablonový generátor: pracuje s Brand DNA/Product DNA a sadou 40 template promptů. Nepoužívej ho jako náhradu za `ad-image-creator` v workflow `ad-strategist -> ad-writer -> ad-image-creator -> ad-publisher`, protože ten očekává konkrétní briefy a manifest pro publisher.

`ad-image-creator` je naopak pipeline krok pro předem naplánované reklamní formáty a vytváří `/documents/brand/ads/{campaign-slug}/ad-image-manifest.json`.

## Postup

1. **Ujasni zadání** - Zjisti, zda uživatel chce brand-level reklamy, produktové reklamy, nebo jen konkrétní čísla šablon. Pokud je zadání vágní, polož jednu krátkou upřesňující otázku; pokud je použitelné, pokračuj.
2. **Načti Brand DNA** - Přečti `/documents/brand/brandDNA.md`. Pokud soubor chybí nebo je prázdný, reklamy zatím negeneruj; vyžádej si URL značky nebo brand podklady, aby je mohl nejdřív doplnit `brand-dna`.
3. **Načti Product DNA** - Pro reklamy na konkrétní produkt/službu přečti `/documents/brand/products/{product-slug}/productDNA.md`. Pokud produkt není jasný, vypiš dostupné složky v `/documents/brand/products/` a zeptej se, který produkt použít.
4. **Nejdřív doplň chybějící DNA** - Pokud pro produktovou reklamu chybí Product DNA, vyžádej si produktovou URL nebo produktové podklady a nejdřív vytvoř/doplň Product DNA přes `product-dna`; teprve potom generuj reklamy.
5. **Vyber šablony** - Pokud uživatel nespecifikuje čísla šablon, použij všech 40 šablon z `references/template-prompts.md`. Pokud čísla zadá, použij jen tyto šablony.
6. **Nastav parametry běhu** - Default je `variations=1`, `quality=high` a `output_format=png`. Uživatel může změnit šablony, počet variant nebo kvalitu, ale pro standardní běh nevyžaduj další vstupy.
7. **Ukaž plán běhu** - Před generováním ukaž zdroje DNA, vybrané šablony, počet variant, kvalitu, očekávaný počet obrázků a výstupní složku v aktuální session nebo task kontextu.
8. **Vytvoř finální prompty** - Pro každou vybranou šablonu nahraď placeholdery konkrétními informacemi z Brand DNA, Product DNA a dostupných brand/product assetů. Technický jazyk promptů ponech v angličtině; viditelný reklamní text napiš jazykem kampaně.
9. **Generuj přes native image** - Použij nativní `image_generate` / GPT Image 2. Nepoužívej FAL, `.env`, `FAL_KEY`, OpenRouter wrapper skripty, ImageMagick/ImageMagic (`magick`, `convert`) ani ručně volané HTTP endpointy jako runtime cestu.
10. **Ulož výstupy** - Každý běh ulož pod `/documents/ads/{brand-or-product}/{run-id}/`. Ke každé šabloně ulož obrázek, finální prompt a záznam v manifestu.
11. **Vrať výsledek** - V aktuálním chatu/session vrať stručné shrnutí s odkazy/cestami k výstupní složce, `manifest.json`, `prompts.json` a případně `gallery.html`. Pokud existuje jakýkoli task context, zároveň zaregistruj trvalé výstupy jako deliverable(s).

## Kontext Spuštění

Tento skill může běžet z přímého chatu nebo z Control Center tasku.

- **Přímý chat bez navázaného tasku:** pokud je potřeba upřesnění, ptej se krátce ve stejném chatu a finální výsledek vrať tam.
- **Chat s navázaným taskem nebo chat vzniklý z tasku:** ber práci jako taskovou. Pořád se můžeš ptát a odpovídat v chatu, ale vygenerované výstupy musí být zároveň zaregistrované jako task deliverable(s).
- **Control Center task:** aktivní agent session je pořád správné místo pro stručné upřesňující otázky. Pokud je dostupné Control Center API, zrcadli blokující otázky i do task threadu.
- **Nečekej kvůli volitelným detailům:** pokud chybí jen šablony, počet variant, kvalita, formát nebo subset poměrů stran, použij defaulty a pokračuj.
- **Blokující chybějící vstupy:** pokud chybí Brand DNA, Product DNA, volba produktu, produktová URL nebo povinné zdrojové podklady a reklamu nejde poctivě vygenerovat, negeneruj. Vyžádej si přesné chybějící vstupy a pokud je dostupné Control Center API, přepni task do `blocked` s metadata jako `waiting_on: "client"` a `blocked_reason: "missing_ad_inputs"`.
- **Pokračování po zpětné vazbě:** když uživatel odpoví v agent chatu, doplní chybějící soubory nebo znovu probudí task s chybějící informací, pokračuj v existujícím tasku. Pokud byl task `blocked` a API je dostupné, před pokračováním ho přepni zpět do `in_progress`.
- **Dokončení navázaného tasku:** ulož trvalé výstupy pod `/documents`, vytvoř deliverable(s) pro vygenerované soubory a manifest, stejné cesty vrať v chatu/session, potom task přesuň do `review` a ověř status. Nepřesouvej task do `review` bez deliverables.

## Výstupní Šablona

Před generováním pošli tento plán v aktuální session nebo task kontextu:

```markdown
# Plán generování reklam

- **Zdroj Brand DNA:** `/documents/brand/brandDNA.md`
- **Zdroj Product DNA:** `/documents/brand/products/{product-slug}/productDNA.md` nebo `brand-level`
- **Šablony:** {all-40 nebo seznam čísel šablon}
- **Varianty:** {variations} na šablonu
- **Kvalita:** {quality}
- **Formát:** PNG
- **Očekávaný počet obrázků:** {template-count * variations}
- **Výstup:** `/documents/ads/{brand-or-product}/{run-id}/`
```

Použij tuto výstupní strukturu:

```text
/documents/ads/{brand-or-product}/{run-id}/
├── prompts.json
├── manifest.json
├── gallery.html
└── outputs/
    ├── 01-headline/
    │   ├── prompt.txt
    │   └── v1.png
    └── 02-offer-promotion/
        ├── prompt.txt
        └── v1.png
```

`manifest.json` udržuj v této struktuře:

```json
{
  "skill": "ad-generator-gpt-image-2",
  "brandDnaPath": "/documents/brand/brandDNA.md",
  "productDnaPath": "/documents/brand/products/{product-slug}/productDNA.md",
  "quality": "high",
  "variations": 1,
  "generatedAt": "YYYY-MM-DDTHH:mm:ssZ",
  "outputs": [
    {
      "templateNumber": 1,
      "templateName": "Headline",
      "aspectRatio": "4:5",
      "promptPath": "/documents/ads/{brand-or-product}/{run-id}/outputs/01-headline/prompt.txt",
      "imagePath": "/documents/ads/{brand-or-product}/{run-id}/outputs/01-headline/v1.png"
    }
  ]
}
```

Závěrečná odpověď:

```markdown
Hotové statické reklamy jsou uložené tady:

- **Výstupní složka:** `/documents/ads/{brand-or-product}/{run-id}/`
- **Manifest:** `/documents/ads/{brand-or-product}/{run-id}/manifest.json`
- **Prompty:** `/documents/ads/{brand-or-product}/{run-id}/prompts.json`
- **Galerie:** `/documents/ads/{brand-or-product}/{run-id}/gallery.html`

Vygenerováno: {count} obrázků z {template-count} šablon.
```

## Rozhodovací Pravidla

| Podmínka | Práh | Akce |
|----------|------|------|
| Brand DNA chybí | `/documents/brand/brandDNA.md` neexistuje nebo je prázdný | Zastav běh a vyžádej URL/podklady pro `brand-dna` |
| Product DNA chybí | Produktová reklama bez `/documents/brand/products/{product-slug}/productDNA.md` | Zastav běh a vyžádej produktovou URL/podklady pro `product-dna` |
| Šablony nejsou specifikované | Nejsou zadaná čísla šablon | Použij všech 40 šablon |
| Varianty nejsou specifikované | Není zadaná hodnota | Použij `1` variantu na šablonu |
| Kvalita není specifikovaná | Není zadaná hodnota | Použij `high` |
| Počet obrázků je vyšší než 40 | `template-count * variations > 40` | Uveď počet a upozorni, že běh může trvat déle; nepřepisuj defaulty bez pokynu |
| Přesný vzhled produktu je důležitý | Záleží na obalu/vizuální přesnosti produktu | Použij dostupné produktové reference; pokud chybí, uveď toto omezení ve výsledku |

## Mapování Poměrů Stran

| Poměr | Velikost obrázku |
|-------|------------------|
| `1:1` | `2048x2048` |
| `4:5` | `1664x2080` |
| `9:16` | `1440x2560` |
| `16:9` | `2560x1440` |
| `4:3` | `2240x1680` |
| `3:4` | `1680x2240` |

## Zakázané Vzory

| Nedělej | Proč | Místo toho |
|---------|------|------------|
| Nevytvářej `~/brands/...` | Vznikl by paralelní brand store mimo Control Center brand kit | Čti a zapisuj jen pod `/documents` |
| Nepoužívej FAL, `FAL_KEY`, původní `generate_ads.py` ani ImageMagick/ImageMagic (`magick`, `convert`) jako runtime cestu | Deployment musí používat native image konfiguraci a obrázky má tvořit model, ne lokální image CLI | Použij `image_generate` |
| Nevymýšlej Brand DNA ani Product DNA | Reklamy by nebyly opřené o schválený brand/product kontext | Zastav se a vyžádej URL/podklady |
| Negeneruj bez viditelného plánu | Uživatel by neviděl rozsah, dopad na čas/cenu ani výstupní lokaci | Nejdřív ukaž plán běhu v aktuální session nebo task kontextu |
| Nepřepisuj staré běhy | Ztratil by se audit a porovnání variant | Vždy vytvoř nový `{run-id}` |
| Nepřekládej technické identifikátory a cesty | Rozbil by se runtime kontrakt | Překládej jen uživatelský text a popisy |

## Integrace

**Používá:**

- `brand-dna` - vytvoření nebo doplnění `/documents/brand/brandDNA.md`, pokud brand kit chybí.
- `product-dna` - vytvoření nebo doplnění `/documents/brand/products/{product-slug}/productDNA.md`, pokud produktový kontext chybí.
- `image_generate` - nativní OpenClaw image generation přes nakonfigurovaný GPT Image 2/default fallback.
- `/documents` - jediný agent-facing filesystem root pro vstupy a výstupy.

**Používají:**

- `cmo` - kampaně, produktové reklamy, Meta/social kreativy a kreativní testy.
- `copywriting` - může dodat varianty headline, offeru, CTA, proof copy a review copy pro šablony.
- `scriptwriter` - může převést vítězné statické koncepty do video scénářů.

## Kontrolní Seznam Kvality

- [ ] Brand DNA bylo načteno z `/documents/brand/brandDNA.md`.
- [ ] U produktových reklam bylo načteno správné Product DNA.
- [ ] Pokud potřebné DNA chybělo, generování se zastavilo a vyžádalo URL/podklady.
- [ ] Plán běhu byl ukázán před generováním.
- [ ] Pokud šlo o Control Center task, trvalé výstupy byly zaregistrované jako deliverables před review.
- [ ] Šablony byly vybrané z `references/template-prompts.md`.
- [ ] Každý prompt obsahuje konkrétní brand/product informace, ne placeholdery.
- [ ] Výstupy jsou uložené pod `/documents/ads/{brand-or-product}/{run-id}/`.
- [ ] `manifest.json` a `prompts.json` odpovídají skutečně vytvořeným souborům.
- [ ] Nebyl použit FAL, `.env`, `FAL_KEY`, původní HTTP wrapper ani ImageMagick/ImageMagic (`magick`, `convert`).

## Datové Soubory

- `references/template-prompts.md` - původních 40 šablon pro statické reklamy. Načti ho až při výběru nebo generování šablon.
- `/documents/brand/brandDNA.md` - povinný brand zdroj.
- `/documents/brand/products/{product-slug}/productDNA.md` - povinný zdroj pro produktové reklamy.
- `/documents/ads/{brand-or-product}/{run-id}/` - výstupní složka každého běhu.

## Výchozí Nastavení Šablon

Defaultní běh bez dalších instrukcí:

```text
templates: 1-40
variations: 1
quality: high
output_format: png
```

Uživatel může říct například:

- „Vygeneruj jen šablony 1, 7, 13 a 15.“
- „Dej tři varianty každé šablony.“
- „Použij medium kvalitu pro rychlý test.“
- „Vygeneruj jen 9:16 šablony pro Stories.“

## Technické Poznámky

- Produktové obrázky jsou důležité, když záleží na vzhledu produktu. Přední, zadní, šikmé a lifestyle reference zlepšují věrnost produktu.
- Šablonové prompty mohou říkat "attached images"; mapuj to na dostupné chat přílohy nebo image soubory pod `/documents`.
- Použij image editing/reference-image generation, když prompt závisí na přesném obalu produktu nebo existující vizuální referenci. Použij standardní text-to-image, když je šablona lifestyle, editorial, diagrammatic nebo UGC-style bez potřeby přesného renderu produktu.
- Poměry stran jsou důležité pro reklamní umístění: `1:1` pro feed, `4:5` pro feed s větší plochou a `9:16` pro Stories/Reels.
- `high` kvalita je default pro produkční výstup; `medium` je vhodné pro rychlejší testy; `low` jen pro hrubé náhledy layoutu.
- Copy vytvořené při přípravě promptů má být zpřesněné skutečným jazykem zákazníků, pokud jsou v brand/product kontextu dostupné recenze, zákaznické reference nebo důkazní body.
