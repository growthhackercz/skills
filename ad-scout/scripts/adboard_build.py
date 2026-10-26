#!/usr/bin/env python3
"""Build bohatého contractu pro Viral Ad Board (analýza → contract).

Deterministická část (skóre, výběr, CZ→globál, thumbnaily, sestavení contractu)
žije tady; renderer `adboard.py` ho jen vykresluje. **Sémantické části** (detekce
úhlu, PŘEKLAD cizí copy, awareness, „proč" odrážky, syntéza, hooky, mapa úhlů)
plní MODEL za běhu — jako u produktového boardu recenze→náměty. Taxonomie úhlů je
**pluggable per téma** (viz `references/viral-ad-board.md`), ne natvrdo.

Vstup = normalizované položky z providera:
  ads:    [{page, text, title, reach, days, plat:[FACEBOOK/INSTAGRAM], url, thumb}]
  viral:  [{net:youtube|tiktok, title/text, who, views, likes, cmts, url, dur, thumb, cz:bool}]
  search: [{brand, head, desc, url, queries, total}]

Výstup = rich contract (schéma v references/viral-ad-board.md).
v0.1 — deterministická kostra; sémantiku (nm/orig/uhel/aw/why/synteza/hooky/mapa) doplní model.
"""
import math
import os
import re
import statistics
import subprocess
import unicodedata

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125 Safari/537.36"


def _cc_token():
    """APIFY_API_KEY — Control Center store (Nastavení -> Integrace) má přednost před env."""
    try:
        import sys as _sys
        _sys.path.insert(0, "/home/node/.openclaw/cs-skills/_lib")
        from cc_credentials import get_variable  # type: ignore
        tok = (get_variable("APIFY_API_KEY") or "").strip()
        if tok:
            return tok
    except Exception:
        pass
    return os.environ.get("APIFY_API_KEY", "").strip()

# Startovní taxonomie úhlů (PŘÍKLAD — model ji nahradí/rozšíří per téma; viz reference).
DEFAULT_ANGLE_RULES = [
    (r"busywork|productiv|produktiv|čas|efektiv|rutin", "produktivita / úspora času"),
    (r"support|inbox|ticket|recep|hovor|účet|asisten", "AI zaměstnanec na roli"),
    (r"build|postav|no ?code|describe|workflow", "postav si to sám (bez kódu)"),
    (r"kurz|webinář|konferenc|use case|rozdíl|edukac", "edukace / adopce"),
    (r"nahrad|berou práci|převezm|končí|fomo", "FOMO / náhrada práce"),
]


def slugify(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:26]


_CZ_STRONG_RE = re.compile(r"[ěřůĚŘŮľĺŕôäĽĹŔÔÄ]")  # ř/ě/ů (unikátně CZ) + SK znaky; NE sdílené í/é/á
_CZ_WORD_RE = re.compile(r"\b(že|není|jsem|jsou|jaký|jaké|slyšel|nebo|při|před|více|proč|"
                         r"som|si|ako|aby|prečo|viac|máš|váš|naše|český|česk)\b", re.I)


def is_cz_text(t):
    """STRIKTNÍ detekce češtiny/slovenštiny — NE loose í/é/á (ty mají i španělština/francouzština/
    srbština → dřív plnily 'lokální kvótu' cizím obsahem). Vyžaduje ř/ě/ů / SK znak / CZ-SK slovo."""
    return bool(_CZ_STRONG_RE.search(t or "") or _CZ_WORD_RE.search((t or "").lower()))


def _dur_sec(dur):
    if not dur:
        return None
    try:
        parts = [int(p) for p in str(dur).split(":")]
    except Exception:
        return None
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec


def content_format(net, dur):
    """Krátký vs dlouhý obsah. Short = háčky/formáty (reels, shorts, TikTok);
    long = úhly/argumenty (YouTube dlouhé, podcast, LinkedIn). Práh 180 s."""
    net = (net or "").lower()
    if net in ("tiktok", "instagram"):
        return "short"
    if net == "linkedin":
        return "long"
    sec = _dur_sec(dur)
    if sec is None:
        return "long" if net == "youtube" else "short"
    return "short" if sec <= 180 else "long"


def hook_of(text):
    t = re.sub(r"[\U0001F300-\U0001FAFF☀-➿⬀-⯿️]", "", text or "").strip()
    m = re.split(r"(?<=[.!?])\s+", t)
    return (m[0] if m else t)[:100].strip()


def detect_angle(text, rules=None):
    t = (text or "").lower()
    for pat, lab in (rules or DEFAULT_ANGLE_RULES):
        if re.search(pat, t):
            return lab
    return "obecný úhel"


def score_ad(reach, days, variants):
    return round(55 * min(math.log10(max(reach or 0, 10)) / 6, 1)
                 + 35 * min(days or 0, 150) / 150
                 + 10 * min(variants or 0, 8) / 8)


def score_org(views, likes, cmts=0):
    """Dosah (log, strop ~30 mil.) + zapojení (ER do 8 %) + diskuse (komentáře/10k zhl.).
    Dosah je hlavní faktor (70 %) — miliony zhlédnutí musí táhnout; zapojení a diskuse
    jen dolaďují pořadí. Stropy schválně vysoko — virální vítězové se musí rozlišit,
    ne slít na maximu (první verze saturovala na 88 už od ~316k zhlédnutí a ER 2,5 %)."""
    v = 70 * min(math.log10(max(views or 1, 1)) / 7.5, 1)
    er = (likes or 0) / max(views or 1, 1) * 100
    z = 20 * min(er / 8, 1)
    cr = (cmts or 0) / max(views or 1, 1) * 10000
    d = 10 * min(cr / 20, 1)
    return round(v + z + d)


def tier(s):
    s = s or 0
    return "s-hot" if s >= 75 else ("s-warm" if s >= 55 else "s-cool")


PLAT_NET = {"FACEBOOK": "facebook", "INSTAGRAM": "instagram"}


def _ad_sites(plat):
    if isinstance(plat, str):
        plat = [plat]
    nets = [PLAT_NET[p] for p in (plat or []) if p in PLAT_NET]
    return nets or ["facebook"]


def dl_thumb(url, path):
    """Stáhne náhled do path (jen přes provider/proxy IP — ne z klientského serveru).
    Vrací absolutní cestu nebo None. Kredity/ToS: obrázek je jen k rozboru, ne rehost."""
    if os.path.exists(path) and os.path.getsize(path) > 4000:
        return path
    if not url:
        return None
    if "api.apify.com" in url and "token=" not in url:  # KV-store covery (TikTok) chtějí token
        tok = _cc_token()
        if tok:
            url = url + ("&" if "?" in url else "?") + "token=" + tok
    try:
        subprocess.run(["curl", "-s", "-A", UA, "-o", path, "--max-time", "22", url], capture_output=True)
    except Exception:
        return None
    return path if (os.path.exists(path) and os.path.getsize(path) > 4000) else None


def _dna_kondenzat(reklamy, viralni):
    """Viral DNA kondenzát (úroveň A, spec references/viral-dna-card.md): 1 nejlepší kus
    z každého světa (Reklama · Organika-short · Longform) → mini-karta přímo v boardu,
    předpočítaná při buildu (žádný proklik, skoro zadarmo — jede na už staženém textu).
    Build vybere kandidáty deterministicky; sémantiku (hook · proc · inspirace, max ~5
    řádků/kus) doplní MODEL. Renderer sekci ukáže, až když je vyplněná."""
    def bucket(item, typ):
        if not item:
            return None
        if typ == "reklama":
            val = " · ".join(x for x in (
                f"{item['dni']} dní běhu" if item.get("dni") else None,
                f"{item['varianty']} variant" if (item.get("varianty") or 0) > 1 else None) if x)
        else:
            val = " · ".join(x for x in (
                (f"{item['zhlednuti']:,}".replace(",", " ") + " zhlédnutí") if item.get("zhlednuti") else None,
                item.get("sit")) if x)
        return {"typ": typ, "ref": item.get("poradi"), "nm": item.get("nm"),
                "kdo": item.get("inzerent") or item.get("kdo"), "url": item.get("url"),
                "thumb": item.get("thumb"), "uhel": item.get("uhel"), "val": val,
                # ↓ plní MODEL (kondenzát držet krátký!); dna_url = odkaz na standalone kartu (volitelně)
                "hook": None, "proc": None, "inspirace": None, "dna_url": None}

    def top(xs):
        return max(xs, key=lambda x: x.get("score") or 0) if xs else None

    shorts = [v for v in viralni if v.get("format") == "short"]
    longs = [v for v in viralni if v.get("format") == "long"]
    return {"reklama": bucket(reklamy[0] if reklamy else None, "reklama"),
            "organika": bucket(top(shorts), "organika"),
            "longform": bucket(top(longs), "longform")}


def _own_winner_card(w, i):
    """Vlastní výherce klienta (z compounding smyčky ad-analyst → own-winners.json).
    Je to klientova VLASTNÍ kreativa → `vlastni:True`, VYJMUTA ze sanitizace i z
    konkurenčního rankingu. Drží se stejného tvaru karty jako konkurenti."""
    return {
        "poradi": i + 1, "vlastni": True,
        "inzerent": w.get("inzerent") or w.get("brand") or "Vy",
        "site": w.get("site") or ["facebook"], "score": w.get("score"),
        "dosah_eu": w.get("dosah_eu") or w.get("reach"), "dni": w.get("dni") or w.get("days"),
        "url": w.get("url"), "nm": w.get("nm") or w.get("title"), "orig": w.get("orig"),
        "uhel": w.get("uhel"), "aw": w.get("aw"), "why": w.get("why"), "thumb": w.get("thumb"),
    }


def build(fetched, tema, trh="cz", angle_rules=None, curated=None, assets_dir=None,
          own_winners=None, cap_ads=20, cap_viral=45):  # cap_viral 45 = až 20 krátkých + 20 dlouhých v boardu
    """Sestaví rich contract. Sémantiku (nm/orig/aw/why/synteza/hooky/mapa) nechává na modelu —
    předvyplní `nm`/`uhel`/`why` deterministicky, model je přepíše (překlad, kurátorování).

    `own_winners` = volitelný vstup z compounding smyčky (`ad-analyst` → `own-winners.json`):
    vítězné reklamy KLIENTA. Jdou do samostatného klíče `vlastni_vyherci` (ne mezi konkurenty),
    jsou vyjmuty ze sanitizace a jejich úhly/hooky tečou do wiki vrstvy Koncepty."""
    curated = curated or {}
    ads_in = fetched.get("ads") or []
    viral_in = fetched.get("viral") or []
    search_in = fetched.get("search") or []

    # --- REKLAMY: dedup per (inzerent, text), varianty, skóre, výběr (max 3/inzerent) ---
    groups, pagecount = {}, {}
    for r in ads_in:
        pagecount[r["page"]] = pagecount.get(r["page"], 0) + 1
        k = (r["page"], (r.get("text") or "")[:60])
        if k not in groups or (r.get("reach") or 0) > (groups[k].get("reach") or 0):
            groups[k] = r
    uniq = list(groups.values())
    for r in uniq:
        r["variants"] = pagecount[r["page"]]
        r["score"] = score_ad(r.get("reach"), r.get("days"), r["variants"])
    uniq.sort(key=lambda r: -r["score"])
    ads_sel, pc = [], {}
    for r in uniq:
        if pc.get(r["page"], 0) >= 3:
            continue
        pc[r["page"]] = pc.get(r["page"], 0) + 1
        ads_sel.append(r)
        if len(ads_sel) >= cap_ads:
            break

    reklamy = []
    for i, r in enumerate(ads_sel):
        cur = curated.get(r["page"], {})
        ang = cur.get("uhel") or detect_angle((r.get("text") or "") + " " + (r.get("title") or ""), angle_rules)
        title = cur.get("title") or hook_of(r.get("text") or "") or hook_of(r.get("title") or "")
        thumb = None
        if assets_dir and r.get("thumb"):
            thumb = dl_thumb(r["thumb"], os.path.join(assets_dir, f"ad-{slugify(r['page'])}-{i}.jpg"))
        reklamy.append({
            "poradi": i + 1, "inzerent": r["page"].strip(), "site": _ad_sites(r.get("plat")),
            "score": r["score"], "dosah_eu": r.get("reach"), "dni": r.get("days"), "varianty": r["variants"],
            "url": r.get("url"), "nm": cur.get("tr") or title, "orig": (title if cur.get("tr") else None),
            "uhel": ang, "aw": cur.get("aw"), "why": cur.get("vzit"), "thumb": thumb,
            "video_url": r.get("video_url"),  # video reklamy → play popup na kartě (poster = thumb)
            "geo": r.get("geo"),  # 'global' = zahraniční doplněk (badge na kartě), jinak CZ
            "video_inspo": r.get("video_inspo"),  # zahraniční video kvůli chybějícímu CZ videu
            "_text": r.get("text"),  # syrový text pro model (překlad/úhel/why); do klientského výstupu NEJDE
        })

    # --- VIRÁL: CZ priorita → globál, skóre ---
    vitems = []
    for v in viral_in:
        cz = v.get("cz")
        if cz is None:
            cz = is_cz_text(v.get("title") or v.get("text"))
        vitems.append({**v, "geo": "cz" if cz else "global",
                       "score": score_org(v.get("views"), v.get("likes"), v.get("cmts"))})
    # Lokální PŘEDNOST + KVÓTA: CZ napřed (řadí sort), zaruč aspoň LOCAL_QUOTA českých kusů v boardu
    # i s nižším dosahem (jinak je globální angličtina s miliony zhlédnutí přebije a lokální zmizí).
    LOCAL_QUOTA = 3
    vitems.sort(key=lambda x: (x["geo"] != "cz", -x["score"]))
    cz_items = [v for v in vitems if v["geo"] == "cz"]
    quota = cz_items[:LOCAL_QUOTA]                       # rezervované lokální sloty
    rest = [v for v in vitems if id(v) not in {id(q) for q in quota}][:max(cap_viral - len(quota), 0)]
    vitems = quota + rest
    viralni = []
    for i, v in enumerate(vitems):
        thumb = None
        if assets_dir and v.get("thumb"):
            thumb = dl_thumb(v["thumb"], os.path.join(assets_dir, f"vir-{v.get('net')}-{i}.jpg"))
        title = v.get("title") or hook_of(v.get("text"))
        viralni.append({
            "poradi": i + 1, "sit": v.get("net"), "kdo": v.get("who"), "score": v["score"],
            "zhlednuti": v.get("views"), "likes": v.get("likes"), "cmts": v.get("cmts"), "url": v.get("url"),
            "nm": title, "uhel": detect_angle(title, angle_rules), "why": None, "thumb": thumb,
            "dur": v.get("dur"), "geo": v["geo"], "format": content_format(v.get("net"), v.get("dur")),
        })

    # --- SEARCH: share of voice ---
    search = []
    for i, g in enumerate(search_in):
        sov, tot = g.get("queries", 0), g.get("total", 0)
        stav = "silná pozice" if sov >= tot * 0.5 else ("okrajová" if sov == 1 else "střední")
        search.append({
            "poradi": i + 1, "brand": g.get("brand"), "head": g.get("head"), "url": g.get("url"),
            "score": g.get("score"), "sov": sov, "total": tot,
            "stav": stav, "uhel": detect_angle((g.get("desc") or "") + " " + (g.get("head") or ""), angle_rules),
            "aw": "intent capture", "why": None,
        })

    # --- VLASTNÍ VÝHERCI (compounding, volitelný) ---
    vlastni = [_own_winner_card(w, i) for i, w in enumerate(own_winners or [])]

    n_cz = sum(1 for v in viralni if v["geo"] == "cz")
    n_short = sum(1 for v in viralni if v.get("format") == "short")
    med = int(statistics.median([r.get("days") for r in ads_sel if r.get("days")])) if ads_sel else 0
    return {
        "meta": {"skill": "ad-scout", "vystup": "viral-ad-board", "tema": tema, "trh": trh},
        "pokryti": {"reklamy_relevantni": len(ads_in), "inzerentu": len({r["page"] for r in ads_in}),
                    "search": len(search), "viralni_kusu": len(viralni), "viral_cz": n_cz,
                    "viral_global": len(viralni) - n_cz, "median_behu": med,
                    "short": n_short, "long": len(viralni) - n_short, "vlastni_vyherci": len(vlastni),
                    # video signál: kolik CZ videoreklam (0 = největší díra) + kolik zahraniční video inspirace
                    "cz_video": sum(1 for r in reklamy if r.get("video_url") and r.get("geo") != "global"),
                    "video_inspo": sum(1 for r in reklamy if r.get("video_inspo"))},
        "reklamy": reklamy, "search": search, "viralni": viralni, "vlastni_vyherci": vlastni,
        # Viral DNA kondenzát (úroveň A) — TOP-1 z každého světa; hook/proc/inspirace doplní model
        "dna_kondenzat": _dna_kondenzat(reklamy, viralni),
        # Sémantiku DOPLNÍ MODEL (viz reference): nm/orig(překlad) · aw · why · synteza · hooky · mapa_uhlu ·
        # search_uhly (úhly ve vyhledávání) · jazyk_zakaznika (Raw Diet z komentářů) · meta.podtitulek.
        "jazyk_zakaznika": {"namitky": [], "touhy": [], "fraze": [], "zdroj_pocet": {}},
    }
