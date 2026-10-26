"""product_dna.py — významová čtečka současné i obohacené Product DNA.

Řeší audit P1-11: parser hledal H2/H3 nadpisy „ideální klient", „hodnotová
propozice", „pozicování". Kanonická i obohacená Product DNA mají tyhle
informace pod jinými názvy, takže Scout dostával tři prázdná pole a mlčky
skóroval bez nich.

Zásady:
  1. Sekce se hledá podle SADY synonym, ne podle jednoho přesného nadpisu.
  2. Úroveň nadpisu ani číslování nerozhoduje (`## 3. Ideální zákazník` sedí).
  3. Neúplný parse je VIDITELNÝ — vrací se seznam nenalezených sekcí, aby
     volající mohl varovat místo tichého pokračování.
  4. Bohatší obsah není vydáván za nový schema kontrakt; rozhoduje význam.

Tento soubor je runtime-local součást skillu; upravuj jej společně s jeho callery a testy.
"""

import re

# Synonyma sekcí. Klíč = pole ve výstupu, hodnota = varianty nadpisu.
# Porovnává se bez diakritiky, bez čísel a bez interpunkce, na začátek řádku.
SECTIONS = {
    "ideal_customer": [
        "idealni klient", "idealni zakaznik", "ideal customer", "ideal client",
        "cilova skupina", "cilovka", "pro koho to je", "komu to prodavame",
        "persona", "avatar", "kdo je zakaznik", "target audience", "icp",
    ],
    "value_proposition": [
        "hodnotova propozice", "value proposition", "co resi", "co produkt resi",
        "hlavni slib", "slib", "promise", "prinos", "benefit", "vysledek",
        "hlavni benefity", "transformace", "co zakaznik ziska", "core offer", "nabidka",
    ],
    "positioning": [
        "pozicovani", "positioning", "jak se lisime", "odlisenost",
        "unikatni mechanismus", "unique mechanism", "konkurence",
        "proc my", "diferenciace", "kategorie", "esence produktu",
    ],
    "objections": [
        "namitky", "objections", "obavy", "prekazky", "co brani nakupu",
        "casté namitky", "caste namitky", "objection handling", "rizika",
    ],
    "pricing": [
        "cena", "cenik", "pricing", "price", "kotva", "cenova kotva",
        "cenova struktura", "investice", "kolik to stoji",
    ],
    "proof": [
        "dukazy", "dukaz", "proof", "reference", "case study", "pripadova studie",
        "vysledky klientu", "testimonials", "social proof",
    ],
}

_DIA = str.maketrans("áäčďéěíľĺňóôöřšťúůüýžÁÄČĎÉĚÍĽĹŇÓÔÖŘŠŤÚŮÜÝŽ",
                     "aacdeeillnooorstuuuyzAACDEEILLNOOORSTUUUYZ")


def _norm(s):
    """Normalizace nadpisu: bez diakritiky, čísel, interpunkce, malá písmena."""
    t = str(s).translate(_DIA).lower()
    t = re.sub(r"[*_`#>]", " ", t)          # markdown ozdoby
    t = re.sub(r"^\s*\d+[.)]?\s*", " ", t)  # číslování „3." / „3)"
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split()).strip()


def _headings(md):
    """Vrátí [(pozice_začátku_obsahu, úroveň, normalizovaný_nadpis, pozice_nadpisu)]."""
    out = []
    for m in re.finditer(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", md, flags=re.M):
        out.append((m.end() + 1, len(m.group(1)), _norm(m.group(2)), m.start()))
    # Podpora podtrženého stylu „Nadpis\n======"
    for m in re.finditer(r"^(.+)\n(=+|-{3,})[ \t]*$", md, flags=re.M):
        lvl = 1 if m.group(2).startswith("=") else 2
        out.append((m.end() + 1, lvl, _norm(m.group(1)), m.start()))
    return sorted(out, key=lambda x: x[3])


def _match(norm_heading, variants):
    """Nadpis sedí, když se rovná variantě, nebo ji obsahuje jako celé slovo."""
    for v in variants:
        if norm_heading == v:
            return True
        if re.search(rf"(^|\s){re.escape(v)}(\s|$)", norm_heading):
            return True
    return False


def extract_section(md, variants, limit=2000):
    """Vytáhne obsah sekce, jejíž nadpis sedí na některou variantu.

    Sekce končí prvním dalším nadpisem stejné nebo vyšší úrovně.
    """
    hs = _headings(md)
    for i, (start, lvl, norm, _hpos) in enumerate(hs):
        if not _match(norm, variants):
            continue
        end = len(md)
        for start2, lvl2, _n2, hpos2 in hs[i + 1:]:
            if lvl2 <= lvl:
                end = hpos2
                break
        body = md[start:end].strip()
        if body:
            return body[:limit]
    return None


def extract_name(md, fallback=""):
    m = re.search(r"^#[ \t]+(.+?)[ \t]*$", md, flags=re.M)
    if m:
        return re.sub(r"\s*[—–-]\s*product\s*dna\s*$", "", m.group(1).strip(), flags=re.I)
    return fallback


def parse(md, slug="", path=""):
    """Rozparsuje Product DNA. Vrací dict + `missing` se nenalezenými sekcemi.

    `missing` NIKDY nezamlčuj — audit P1-11 vytýká právě to, že prázdná
    klíčová pole projdou bez varování a Scout pak skóruje naslepo.
    """
    md = str(md or "")
    out = {
        "slug": slug,
        "name": extract_name(md, slug),
        "path": str(path),
        "raw_md_chars": len(md),
    }
    limits = {"ideal_customer": 1500, "value_proposition": 1000,
              "positioning": 800, "objections": 800,
              "pricing": 600, "proof": 800}
    missing = []
    for key, variants in SECTIONS.items():
        val = extract_section(md, variants, limits.get(key, 1000))
        out[key] = val or ""
        if not val:
            missing.append(key)
    out["missing"] = missing
    # Klíčová trojice pro fit scoring — bez ní nemá smysl skórovat.
    out["usable_for_scoring"] = not ({"ideal_customer", "value_proposition"} & set(missing))
    return out


def warn_lines(parsed):
    """Řádky varování pro stderr. Prázdný seznam = vše nalezeno."""
    miss = parsed.get("missing") or []
    if not miss:
        return []
    label = {"ideal_customer": "ideální zákazník", "value_proposition": "hodnotová propozice",
             "positioning": "pozicování", "objections": "námitky",
             "pricing": "cena / kotva", "proof": "důkazy"}
    lines = [f"POZOR: v Product DNA '{parsed.get('slug') or parsed.get('name')}' "
             f"chybí sekce: {', '.join(label.get(m, m) for m in miss)}"]
    if not parsed.get("usable_for_scoring"):
        lines.append("       Bez ideálního zákazníka a hodnotové propozice nelze "
                     "spolehlivě určit fit — doplňte Product DNA, nebo skóre neberte vážně.")
    return lines
