#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""concept-seed.py — Web DNA generátor pro vibe-builder.

Přiřadí designový směr z katalogu deterministicky ze slugu projektu.
Smysl: model by jinak každý běh postavil svůj nejlíp hodnocený nápad
(= kategoriální default = fingerprint napříč fleetem). Web DNA přichází
zvenčí a je opakovatelná: stejný slug → stejný směr.

Použití:
    python3 concept-seed.py --slug muj-projekt [--purpose web|funnel]
      [--tier 0|1|2|3] [--reroll N] [--choose "jméno vyzyvatele"]

Výstup: přiřazený směr + 2 vyzyvatelé (JSON na stdout, lidský text na stderr).
Zero-dep, Python 3.8+.
"""
import argparse
import hashlib
import json
import re
import sys

# Katalog směrů. Každý je životaschopný sám o sobě: má tezi, paletovou
# strategii, typový charakter, kompoziční sklon, motion podpis a co odmítá.
# Směr je startovní bod art direction — NE hotový design. Rozviň ho pro
# konkrétní brand (viz 09-direction.md).
CATALOG = [
    {
        "name": "Editorial Broadsheet",
        "teze": "Stránka jako prémiový nedělní magazín — typografie je hlavní obraz.",
        "paleta": "Zdrženlivá: papírová bílá/ivory, inkoustová černá, 1 akcent",
        "typo": "výrazný serif display + čistý grotesk body",
        "kompozice": "off-grid editorial offsety, velké číslované kapitoly NE — místo nich running head",
        "motion": "line-mask reveals po řádcích (SplitText), pomalé, sebejisté",
        "odmita": "karty, bento gridy, ikonky u všeho",
    },
    {
        "name": "Swiss Poster",
        "teze": "Mřížka a měřítko dělají všechnu práci — jeden obraz, jeden titulek, ticho.",
        "paleta": "Commitnutá: jedna sytá barva nese plochu, černá + bílá",
        "typo": "grotesk v extrémním škálovém kontrastu (96px+ vs 14px)",
        "kompozice": "giant statement hero, asymetrie, hodně negativního prostoru",
        "motion": "velké skoky měřítka na scroll, marquee běhy",
        "odmita": "stíny, zaoblené rohy nad 8px, gradients",
    },
    {
        "name": "Dark Cinema",
        "teze": "Temný sál, světlo vede oko — stránka se odkrývá jako scény filmu.",
        "paleta": "Ponorná tmavá: uhlová/navy plocha, světlo jako nástroj hierarchie",
        "typo": "úzký display s charakterem + mono pro detaily",
        "kompozice": "image-as-canvas, pinnuté scény, tonální overlaye",
        "motion": "pomalé pinned scrub scény, světelné přechody, film grain jemně",
        "odmita": "bílé sekce uprostřed, veselé barvy, drobné karty",
    },
    {
        "name": "Soft Luxury",
        "teze": "Klid je luxus — kámen, len, vzduch; nic nekřičí, všechno sedí.",
        "paleta": "Zdrženlivá teplá: bone, sand, taupe, jeden hluboký akcent",
        "typo": "jemný serif display + humanistický sans, velkorysý leading",
        "kompozice": "mini hero, 50/50 editorial splits, hodně whitespace",
        "motion": "sotva znatelné fade-rise, dlouhé ease-out, žádné skoky",
        "odmita": "výprodejové CTA, husté gridy, ostré stíny",
    },
    {
        "name": "Blueprint / Technical",
        "teze": "Produkt jako inženýrský výkres — přesnost budí důvěru.",
        "paleta": "Commitnutá: rýsovací modř nebo tmavá + technická azurová, mřížka jako textura",
        "typo": "grotesk + mono čísla (tabular), kóty a popisky",
        "kompozice": "vertical rhythm lines, oversized metrics, diagramy",
        "motion": "DrawSVG kreslené linky, counter čísla, přesné krátké pohyby",
        "odmita": "lifestyle fotky, měkké stíny, dekorativní ilustrace",
    },
    {
        "name": "Organic Botanical",
        "teze": "Růst a materiál — stránka dýchá přírodou, ne šablonou eko-webu.",
        "paleta": "Plná: hluboká zeleň, hlína, krémová, květový akcent",
        "typo": "serif s oblými tahy + čistý sans, kurzíva jen v citacích",
        "kompozice": "diagonal staggered masonry, full-bleed makro fotky",
        "motion": "vrstvená scéna s hloubkou (parallax vrstev), organická stagger",
        "odmita": "neonové barvy, tvrdou mřížku, tech žargon",
    },
    {
        "name": "Museum Catalog",
        "teze": "Produkt jako exponát — číslovaný, datovaný, nasvícený, vzácný.",
        "paleta": "Zdrženlivá galerie: bílá stěna, černý text, mosazný akcent",
        "typo": "klasicistní serif display + drobný grotesk popisků",
        "kompozice": "centered statement, split testimonial quote wall, štítky exponátů",
        "motion": "pomalé Ken Burns na fotkách, opatrné reveals",
        "odmita": "urgency prvky, countdowny, výrazné CTA barvy",
    },
    {
        "name": "Kinetic Type",
        "teze": "Slova jsou herci — typografie se hýbe, obrazy jen asistují.",
        "paleta": "Commitnutá: 1 elektrizující akcent na neutrálu",
        "typo": "variabilní grotesk, váha a šířka jako výrazový prostředek",
        "kompozice": "text-dominant sekce, horizontální pinnuté běhy",
        "motion": "SplitText words/lines choreografie, marquee",
        "odmita": "stock fotky, ikonové gridy, dlouhé odstavce v pohybu",
    },
    {
        "name": "Warm Craft",
        "teze": "Ruční práce a poctivost — stránka jako dílna, ne showroom.",
        "paleta": "Plná teplá: okrová, cihlová, krémová, tmavě hnědá",
        "typo": "slab serif nebo výrazný humanist + upřímný body",
        "kompozice": "bottom-left text over image, materiálové textury na pozadí",
        "motion": "skromné reveals, hover se substancí (lift + stín)",
        "odmita": "korporátní glassmorphism, studené barvy, AI-hladké fotky",
    },
    {
        "name": "Monochrome Sculpt",
        "teze": "Jedna barva, deset valérů — hloubka vzniká světlem a vrstvením, ne paletou.",
        "paleta": "Ponorná monochromní: jedna hue v plné škále 50–950",
        "typo": "geometrický grotesk, tenké/tučné kontrasty",
        "kompozice": "3D cascading card deck, elevace jako jazyk",
        "motion": "clip-path reveals, jemné scale na scroll, stínové přechody",
        "odmita": "druhou hue kdekoli, barevné ikony, duhové grafy",
    },
    {
        "name": "Retro Print",
        "teze": "Tiskárna 1972 potkává dnešní web — rastr, přetisk, poctivý papír.",
        "paleta": "Plná retro: hořčicová, cihlová, petrolejová na off-white",
        "typo": "výrazný display s osobností + knižní body serif",
        "kompozice": "color-blocked diptychy, přetiskové vrstvy, samolepky střídmě",
        "motion": "skoky jako listování, rubber-band hover, žádný blur",
        "odmita": "gradients, glow, corporate fotky lidí u notebooků",
    },
    {
        "name": "Data Editorial",
        "teze": "Čísla vyprávějí příběh — stránka je reportáž s grafy, ne dashboard.",
        "paleta": "Zdrženlivá: novinová bílá/černá + 1 datová barva",
        "typo": "serif nadpisy jako headline + mono čísla",
        "kompozice": "oversized metrics strip, anotované grafy v textu",
        "motion": "counter čísla, grafy se kreslí při vjezdu (DrawSVG osy)",
        "odmita": "koláčové grafy, KPI karty v gridu, duhu v datech",
    },
    {
        "name": "Neon Noir",
        "teze": "Noční město — tma je plátno, jeden neon je podpis. Přesně jeden.",
        "paleta": "Ponorná tmavá + JEDEN neonový akcent (ne fialovo-modrý gradient)",
        "typo": "ostrý grotesk + mono, svítící jen akcentní prvky",
        "kompozice": "deep charcoal canvas, image-as-canvas s neonovým světlem",
        "motion": "glow pulzy na hover (střídmě), scrub scény s protisvětlem",
        "odmita": "purple-blue gradient (AI klišé!), glow na všem, particle déšť",
    },
    {
        "name": "Paper Collage",
        "teze": "Vystřihované vrstvy — stránka jako ručně lepený moodboard s řádem.",
        "paleta": "Plná: papírové tóny + 2 syté výstřižky",
        "typo": "kombinace serif výstřižků a psacího akcentu (střídmě!)",
        "kompozice": "diagonal staggered masonry, roztrhané okraje, vrstvení",
        "motion": "vrstvená scéna — výstřižky se skládají při scrollu",
        "odmita": "dokonalou symetrii, glassmorphism, 3D efekty",
    },
    {
        "name": "Cinematic Photo-led",
        "teze": "Fotografie je stránka — text jen titulkuje velké obrazy.",
        "paleta": "Zdrženlivá servisní: barvy vytahuje z fotek, UI neutrální",
        "typo": "tenký elegantní grotesk, malé kapitálky na popisky",
        "kompozice": "full-bleed image-as-canvas sekvence, mid editorial hero",
        "motion": "pomalé scale-in fotek, tonální crossfade mezi sekcemi",
        "odmita": "ilustrace, ikonky, text přes střed fotky bez scrimu",
    },
    {
        "name": "Bauhaus Playful",
        "teze": "Geometrie si hraje — kruh, čtverec, primární barva, přísný řád pod tím.",
        "paleta": "Plná primární: červená/modrá/žlutá na světlém podkladu",
        "typo": "geometrický grotesk, kruhové O jako motiv",
        "kompozice": "pristine gapless bento (jednou!), geometrické dělení stran",
        "motion": "tvary rotují a skládají se na scroll, pružné easing",
        "odmita": "fotografie jako hero, stíny, dekorativní serifiky",
    },
]

CANON = {
    "name": "Oborový standard",
    "teze": "Konvence provedená na plné řemeslo — bez ironie, bez pašovaných výstředností.",
    "pozn": "Tichý východ pro klienta. Nikdy nedoporučuj, nikdy neshazuj.",
}

# Chrome / skelet stránky — druhá osa kostky, rolovaná NEZÁVISLE na směru.
# Důvod: bez ní všechny weby konvergují na stejný skelet („malé logo vlevo
# + pill CTA vpravo + centrovaný hero text") a fingerprint je zpět, i když
# se světy liší. Roll je startovní bod jako směr — přebít ho smíš jen
# s pojmenovaným důvodem zapsaným ve webDNA.md.
HEADERS = [
    "logo vlevo + CTA vpravo (klasika — zaslouží si důvod, ne default)",
    "centrované logo, header bez CTA (CTA žije v hero) — u centrované hero kompozice logo klesá k nadpisu jako součást skupiny, nikdy nevisí přilepené u horního okraje",
    "logo vlevo + textová navigace 2–4 položky + CTA",
    "žádný header v hero — floating bar se objeví po prvním scrollu",
    "oversized wordmark jako součást hero kompozice",
    "spodní lišta: logo + CTA při dolní hraně, obraz běží od horní hrany",
]
# ⚠️ Hero text se NIKDY nezarovnává vpravo (čte se zleva; pravé zarovnání
# v hero je zákaz — brána to hlídá). Pravá strana patří médiu/dechu.
HERO_TEXT = [
    "centrovaný blok",
    "levý blok — pravá strana dýchá",
    "spodní třetina vlevo — obraz vede, text nastupuje dole",
    "rohové ukotvení vlevo dole — malý přesný blok, obří médium",
    "split — headline vlevo nahoře, sub + CTA dole",
]
CTA_SHAPES = [
    "pill (plný radius)",
    "ostrý obdélník (radius ≤ 4 px)",
    "textový link se šipkou a podtržením (žádný box)",
    "ghost outline (border, průhledná plocha)",
]

# ─── Motion podpis — třetí osa kostky ───────────────────────────────────
# Bez ní všechny weby konvergují na ease/DUR opsané z příkladu v dokumentaci
# (nejsilnější fleet fingerprint — pohyb je cítit, i když se hexy liší).
# Roll se zapisuje jako lib/motion.config.ts s lockem; brána lock ověřuje.

# Pojmenované CustomEase křivky (jméno → data). Build je registruje pod
# jménem "brand" — inline křivka z dokumentace je zakázaná.
# ⚠️ VŠECHNY křivky poolu jsou rodiny EASE-OUT (rychlý rozjezd, dlouhý
# dojezd). Podpis se roluje do `brandEase`, a ten nese PŘÍCHODY — pomalý
# rozjezd (ease-in, nápřah, symetrická in-out) je na příchodu zakázaný,
# protože zdrží přesně ten okamžik, kdy se uživatel dívá nejpozorněji
# (10-motion-web.md „Křivku vybírá situace"). Podpis mění CHARAKTER
# uvnitř rodiny, nikdy rodinu.
EASES = {
    "pero":     "M0,0 C0.16,0.84 0.28,1 1,1",     # rychlý nástup, dlouhý dojezd
    "vydech":   "M0,0 C0.19,1 0.22,1 1,1",        # měkký, vzdušný (expo-out)
    "svah":     "M0,0 C0.25,0.6 0.2,1 1,1",       # klasický ease-out s vahou
    "prak":     "M0,0 C0.1,0.9 0.2,1 1,1",        # vymrštění (bez nápřahu a přestřelu)
    "brzda":    "M0,0 C0.05,0.7 0.1,1 1,1",       # okamžitý start, sametová brzda
    "vlna":     "M0,0 C0.25,0.8 0.25,1 1,1",      # plavná, bez trhnutí
    "usazeni":  "M0,0 C0.22,0.61 0.36,1 1,1",     # věcné, bez dramat
    "dopad":    "M0,0 C0.08,0.82 0.5,1 1,1",      # rychlý start, pevné dosednutí
}

# Rodina pro POHYB PO OBRAZOVCE (prvek se přesouvá / mění tvar) — jedna
# pro všechny podpisy: charakter nese příchod, ne přesun. Marquee, progress
# a nekonečné smyčky jedou VŽDY `linear` (`ease: "none"`), nikdy brandEase.
EASE_INOUT = "M0,0 C0.77,0 0.175,1 1,1"

# Slovesa vjezdu textu — jiná TRANSFORMNÍ GRAMATIKA, ne jen jiná čísla.
# Pool per směr drží charakter směru (jako FONTY).
# ⚠️ ŽÁDNÉ houpání: rotateX a scaleSettle (overshoot kývání) jsou ZAKÁZANÉ —
# na textech vypadají lacině (reálný verdikt z produkce). Vjezdy jsou
# důstojné: posun, maska, wipe, blur, váha písma.
VERBS = ["rise", "clipUp", "wipe", "blurIn", "weight"]
VERB_POOLS = {
    "Editorial Broadsheet": ["rise", "clipUp", "blurIn"],
    "Swiss Poster": ["clipUp", "wipe", "rise"],
    "Dark Cinema": ["blurIn", "clipUp", "rise"],
    "Soft Luxury": ["rise", "blurIn", "clipUp"],
    "Blueprint / Technical": ["wipe", "clipUp", "rise"],
    "Organic Botanical": ["rise", "clipUp", "blurIn"],
    "Museum Catalog": ["clipUp", "rise", "blurIn"],
    "Kinetic Type": ["clipUp", "weight", "wipe"],
    "Warm Craft": ["rise", "blurIn", "clipUp"],
    "Monochrome Sculpt": ["clipUp", "blurIn", "wipe"],
    "Retro Print": ["clipUp", "wipe", "rise"],
    "Data Editorial": ["clipUp", "rise", "wipe"],
    "Neon Noir": ["blurIn", "wipe", "clipUp"],
    "Paper Collage": ["wipe", "blurIn", "rise"],
    "Cinematic Photo-led": ["blurIn", "rise", "clipUp"],
    "Bauhaus Playful": ["clipUp", "wipe", "rise"],
}
UNITS = ["words", "lines"]                   # dominantní jednotka splitu
# „chars" v poolu NENÍ — animace po písmenech je zakázaná (10-motion-web.md).
ORIGINS = ["start", "center", "edges", "random"]
TEMPI = [0.85, 1.0, 1.25]                     # násobič DUR škály
OVERSHOOTS = [0]  # houpání zakázané — přestřel na textu vypadá lacině
# ⚠️ ZÁKAZ: skew/velocity naklánění textu (text jedoucí „ze strany na
# stranu" podle rychlosti scrollu) působí neprofesionálně — osa je trvale
# vypnutá, stejně jako houpání (rotateX/scaleSettle). Text se NIKDY
# nehýbe do stran ani nenaklání.
DISTORTS = ["none"]
ACCENT_DELAYS = [0.08, 0.12, 0.16]

# Velké momenty — z poolu se rolují 2; zbytek zůstává v paletě jako
# volitelné autorské tahy (10-motion-web.md).
MOMENTS = [
    "pin-scéna (vrstvené jeviště)",
    "horizontální pinnutý běh",
    "Flip sdíleného slova hero → sekce",
    "slovní ruleta v nadpisu (wordSwap)",
    "kurzorový magnet na hero obrazu (desktop only, jen obraz, nikdy text)",
    "ScrambleText na metrikách (CZ-safe abeceda)",
    "nadpis jako maska pro obraz/video",
    "kapitolový snap velké scény",
    "klipový tab indikátor (zdvojený seznam, ořez podle aktivního tabu)",
    "scrub-light čtení (slova se rozsvěcují, jen opacity)",
    "rozklad na součástky — exploded view (JEN fyzický produkt, 07-images.md)",
]
# Moment nepoužitelný pro obor/typ projektu (rozklad bez fyzického produktu)
# nahraď dalším z palety a důvod zapiš do webDNA.md — stejný vzor jako
# přebití směru/chrome.

# Fontový zásobník per směr (Google Fonts s latin-ext — čeština!).
# Seed vybírá deterministicky → různí klienti = různé fonty, žádná konvergence
# na jeden „příkladový" font. PŘESKAKUJE SE, když klient má fonty v DESIGN.md
# (font = identita klienta).
FONTY = {
    "Editorial Broadsheet": ["Lora", "Spectral", "Source Serif 4"],
    "Swiss Poster": ["Archivo", "Inter Tight", "Familjen Grotesk"],
    "Dark Cinema": ["Sora", "Outfit", "Saira"],
    "Soft Luxury": ["EB Garamond", "Lora", "Gantari"],
    "Blueprint / Technical": ["IBM Plex Sans", "Chivo", "IBM Plex Mono"],
    "Organic Botanical": ["Literata", "Andada Pro", "Gantari"],
    "Museum Catalog": ["Marcellus", "EB Garamond", "Spectral"],
    "Kinetic Type": ["Anybody", "Archivo", "Unbounded"],
    "Warm Craft": ["Zilla Slab", "Bitter", "Josefin Sans"],
    "Monochrome Sculpt": ["Outfit", "Hanken Grotesk", "Geologica"],
    "Retro Print": ["Anton", "Bebas Neue", "Alfa Slab One"],
    "Data Editorial": ["Source Serif 4", "IBM Plex Serif", "Lora"],
    "Neon Noir": ["Saira", "Exo 2", "Chakra Petch"],
    "Paper Collage": ["Gabarito", "Bricolage Grotesque", "Familjen Grotesk"],
    "Cinematic Photo-led": ["Hanken Grotesk", "Figtree", "Albert Sans"],
    "Bauhaus Playful": ["Familjen Grotesk", "Archivo", "Gabarito"],
}


def pick(slug: str, purpose: str, reroll: int):
    seed = f"{slug.strip().lower()}|{purpose}|{reroll}"
    h = hashlib.sha256(seed.encode("utf-8")).digest()
    n = len(CATALOG)
    i0 = h[0] % n
    # vyzyvatelé: deterministická permutace zbytku katalogu — kolize
    # vyloučené konstrukcí (přiřazený směr není v kandidátech)
    rest = [i for i in range(n) if i != i0]
    rest.sort(key=lambda i: hashlib.sha256(seed.encode("utf-8") + bytes([i])).digest())
    return CATALOG[i0], CATALOG[rest[0]], CATALOG[rest[1]]


def resolve_choice(slug: str, purpose: str, reroll: int, requested: str,
                   assigned: dict, challengers: list):
    """Promění vybraného vyzyvatele na nový plný deterministický hod.

    Vyzyvatelé z prvního hodu jsou jen názvy/teze. Když si klient jednoho
    vybere, najdeme první následující hod, kde je tento směr assigned, aby
    font, chrome i motion vznikly ze stejného seedu jako zvolený směr.
    """
    allowed = {assigned["name"], *(item["name"] for item in challengers)}
    if requested not in allowed:
        names = ", ".join(sorted(allowed))
        raise ValueError(f"--choose musí být assigned nebo vyzyvatel z výchozího hodu: {names}")
    if requested == assigned["name"]:
        return reroll
    for candidate_roll in range(reroll + 1, reroll + 4097):
        candidate, _, _ = pick(slug, purpose, candidate_roll)
        if candidate["name"] == requested:
            return candidate_roll
    raise ValueError("vybraný směr se nepodařilo převést na plný hod v bezpečném limitu")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help="slug projektu/klienta")
    ap.add_argument("--purpose", default="web", choices=["web", "funnel", "dashboard", "app"])
    ap.add_argument("--tier", type=int, default=1, choices=[0, 1, 2, 3],
                    help="schválený motion tier marketingového webu (default 1)")
    ap.add_argument("--reroll", type=int, default=0, help="N-tý re-roll (0 = první hod)")
    ap.add_argument("--choose", help="přesné jméno assigned směru nebo vyzyvatele z výchozího hodu")
    a = ap.parse_args()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a.slug):
        ap.error("--slug musí být kebab-case (lowercase písmena, čísla a jednoduché pomlčky)")
    if a.reroll < 0:
        ap.error("--reroll musí být celé nezáporné číslo")

    # Dashboard a aplikace jsou nástroje, ne scénografie. Web DNA ani motion
    # podpis nedostávají — jinak by brána hlásila P1 (tier 0 nesmí mít
    # motion.config.ts) a agent by hnal do rozhraní webovou dramaturgii.
    if a.purpose in ("dashboard", "app"):
        print(
            "Web DNA je pro webové účely (web/funnel). Dashboard a aplikace směr "
            "ani motion podpis nedostávají — drží klidný tier 0 a brand klienta "
            "(viz 06-patterns.md a 16-aplikace.md).",
            file=sys.stderr,
        )
        print(json.dumps({
            "seed": f"{a.slug}|{a.purpose}|reroll={a.reroll}",
            "purpose": a.purpose,
            "tier": 0,
            "web_dna": None,
            "motion_signature": None,
            "webdna_zapis": {"concept_seed": "none", "tier": 0},
            "pozn": "Do webDNA.md zapiš `concept_seed: none` a `tier: 0`. "
                    "Bránu spouštěj bez --seed-slug a negeneruj lib/motion.config.ts.",
        }, ensure_ascii=False, indent=2))
        return 0

    assigned, ch1, ch2 = pick(a.slug, a.purpose, a.reroll)
    initial_reroll = a.reroll
    if a.choose:
        try:
            a.reroll = resolve_choice(a.slug, a.purpose, a.reroll, a.choose, assigned, [ch1, ch2])
        except ValueError as error:
            ap.error(str(error))
        assigned, ch1, ch2 = pick(a.slug, a.purpose, a.reroll)
    # deterministický výběr display fontu z poolu směru (přeskoč, má-li
    # klient fonty v DESIGN.md — identita klienta vítězí)
    pool = FONTY.get(assigned["name"], [])
    font = None
    if pool:
        fh = hashlib.sha256(f"{a.slug}|font|{a.reroll}".encode("utf-8")).digest()
        font = pool[fh[0] % len(pool)]
    # chrome/skelet: nezávislý roll, ať weby nesdílí stejnou kostru
    chash = hashlib.sha256(f"{a.slug}|chrome|{a.reroll}".encode("utf-8")).digest()
    chrome = {
        "header": HEADERS[chash[0] % len(HEADERS)],
        "hero_text": HERO_TEXT[chash[1] % len(HERO_TEXT)],
        "cta_shape": CTA_SHAPES[chash[2] % len(CTA_SHAPES)],
        "pozn": "Startovní bod jako směr — přebít jen s pojmenovaným důvodem ve webDNA.md (např. konflikt se směrem/oborem). Zapiš výsledný chrome do webDNA.md.",
    }
    # motion podpis: nezávislý roll → lib/motion.config.ts (lock hlídá brána)
    mhash = hashlib.sha256(f"{a.slug}|motion|{a.reroll}".encode("utf-8")).digest()
    lock = mhash.hex()[:12]
    ease_name = list(EASES)[mhash[1] % len(EASES)]
    verb_pool = VERB_POOLS.get(assigned["name"], VERBS[:3])
    tempo = TEMPI[mhash[3] % len(TEMPI)]
    m1 = MOMENTS[mhash[6] % len(MOMENTS)]
    m2_rest = [m for m in MOMENTS if m != m1]
    selected_moments = [m1, m2_rest[mhash[9] % len(m2_rest)]] if a.tier >= 2 else []
    signature = {
        "unit": UNITS[mhash[2] % len(UNITS)],
        "verb": verb_pool[mhash[0] % len(verb_pool)],
        "origin": ORIGINS[mhash[4] % len(ORIGINS)],
        "tempo": tempo,
        "ease_name": ease_name,
        "ease_curve": EASES[ease_name],
        "overshoot": OVERSHOOTS[mhash[5] % len(OVERSHOOTS)],
        "distort": DISTORTS[mhash[7] % len(DISTORTS)],
        "accent_delay": ACCENT_DELAYS[mhash[8] % len(ACCENT_DELAYS)],
        "moments": selected_moments,
        "lock": lock,
    }
    assigned_for_tier = dict(assigned)
    if a.tier <= 1:
        assigned_for_tier["kompozice"] = (
            assigned_for_tier["kompozice"]
            .replace("pinnuté scény", "filmové obrazové sekvence bez pinu")
            .replace("horizontální pinnuté běhy", "horizontální typografické pásy bez pinu")
        )
        assigned_for_tier["motion"] = (
            "žádný pohyb; prémiovost nese typografie, kompozice a fotografie"
            if a.tier == 0 else
            f"{signature['verb']} po {signature['unit']}, jemné reveal příchody; "
            "bez pinnuté nebo scrubované scény"
        )
    else:
        assigned_for_tier["motion_catalog"] = assigned["motion"]
    motion_config_ts = f"""// lib/motion.config.ts — VYGENEROVÁNO concept-seed.py, NEUPRAVUJ RUČNĚ
// signature_lock: {lock}
import gsap from "gsap";
import {{ CustomEase }} from "gsap/CustomEase";
gsap.registerPlugin(CustomEase);

// brandEase = PŘÍCHOD a ODCHOD (rodina ease-out). brandEaseInOut = pohyb
// po obrazovce. Konstantní pohyb (marquee, progress, smyčka) = ease: "none".
export const brandEase = CustomEase.create("brand", "{signature['ease_curve']}"); // {ease_name}
export const brandEaseInOut = CustomEase.create("brandInOut", "{EASE_INOUT}");
export const DUR = {{ fast: {round(0.35 * tempo, 2)}, base: {round(0.7 * tempo, 2)}, slow: {round(1.1 * tempo, 2)} }};
export const SIGNATURE = {{
  unit: "{signature['unit']}",
  verb: "{signature['verb']}",
  origin: "{signature['origin']}",
  tempo: {tempo},
  ease: "brand",
  overshoot: {signature['overshoot']},
  distort: "{signature['distort']}",
  accentDelay: {signature['accent_delay']},
  maxChars: 60,
  lock: "{lock}",
}} as const;
"""
    out = {
        "seed": f"{a.slug}|{a.purpose}|reroll={a.reroll}",
        "tier": a.tier,
        "selection": {
            "requested": a.choose or assigned["name"],
            "initial_reroll": initial_reroll,
            "resolved_reroll": a.reroll,
        },
        "assigned": assigned_for_tier,
        "display_font": font,
        "font_pool": pool,
        "font_pozn": "Platí jen bez klientských fontů v DESIGN.md. Ověř latin-ext subset (čeština); bez něj vezmi další z poolu. Line-height display ≥ 1.15.",
        "chrome": chrome,
        "motion_signature": signature if a.tier >= 1 else None,
        "motion_config_ts": motion_config_ts if a.tier >= 1 else None,
        "motion_pozn": (
            "Tier 0: neinstaluj GSAP a nevytvářej motion.config.ts ani text-motion.ts; do webDNA.md zapiš tier: 0."
            if a.tier == 0 else
            f"Tier {a.tier}: zapiš motion_config_ts DOSLOVA jako <slug>/src/lib/motion.config.ts — brána ověřuje lock (--seed-slug). Podpis do webDNA.md ## Motion. Sloveso/jednotku smíš přebít jen s pojmenovaným důvodem ve webDNA.md; lock v souboru zůstává. Velké tier-2 momenty jsou prázdné pro tier 1."
        ),
        "challengers": [
            {"name": ch1["name"], "teze": ch1["teze"]},
            {"name": ch2["name"], "teze": ch2["teze"]},
        ],
        "canon_exit": CANON,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    motion_summary = (
        "žádný (tier 0)"
        if a.tier == 0 else
        f"{signature['verb']}/{signature['unit']} · ease „{ease_name}“ · tempo {tempo} · origin {signature['origin']}"
    )
    moments_summary = " + ".join(signature["moments"]) if signature["moments"] else f"žádné (tier {a.tier})"
    print(f"\n→ Přiřazený směr: {assigned['name']} — {assigned['teze']}\n"
          f"  Chrome: {chrome['header']} · hero text: {chrome['hero_text']} · CTA: {chrome['cta_shape']}\n"
          f"  Motion podpis: {motion_summary}\n"
          f"  Tier: {a.tier} · velké momenty: {moments_summary}\n"
          f"  Vyzyvatelé: {ch1['name']} · {ch2['name']}\n"
          f"  Rozviň podle 09-direction.md, pak sparring, pak 1 commitnutý koncept klientovi.\n"
          f"  ⚠️ Web DNA přiřazuje FORMU, ne TÓN: u vážných oborů (pohřebnictví,\n"
          f"  zdravotnictví, právo, finance seniorům…) přelož směr do vážné polohy;\n"
          f"  když to nejde, re-rolluj s pojmenovaným věcným důvodem (09-direction.md).",
          file=sys.stderr)


if __name__ == "__main__":
    main()
