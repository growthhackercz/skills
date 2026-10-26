#!/usr/bin/env python3
"""Build machine contractu pro Search Ad Board (deterministická kostra → model doplní sémantiku).

Search Ad Board = takticko-ekonomická vrstva „jak levně vyhrát placený Google Search".
🛑 HRANICE: Viral = CO říkají (úhly/sdělení) · Search = ZA CO platí, kolik to stojí a jak
je přebít. Tenhle build drží MECHANIKU (kdo/kde/kolik/jak dlouho), NE rozbor sdělení.

Deterministická část (tady):
  - dedup bidderů přes dotazy, intenzita = na kolika dotazech se inzerent objeví
  - hustota inzerentů/dotaz (sekce 1, 3, 5)
  - štítek „prověřeno trhem" ze stáří reklamy v registru (days >= PROVERENO_DNI)
  - kandidáti mezery: probe dotazy s 0–2 inzerenty + obohacení o volume/CPC z metrik
  - kostra cloneable_ads z reálné copy top bidderů (klon doplní model)

Sémantická část (MODEL — viz references/search-ad-board.md „Co plní MODEL"):
  proc_nebezpecny · klony reklam · kurátorovaná mezera · souboj landingů (WebFetch) ·
  semafor (3 signály: CPC odhad + oborový benchmark + hustota) · akční plán · podtitulek.

Vstup = normalizované položky z providera:
  serp:      [{query, paid:[{pos,title,desc,url,displayed,sitelinks}], organic, related}]
  portfolio: {domain: [{text, format, first_shown, last_shown, days, impressions, url}]}
  keywords:  [{kw, volume, cpc, competition, intent}]
  probes:    [{query, paid:[...]}]  (volitelné — ověření hustoty na model-generovaných slovech)

v0.1 — kostra dle documents/projects/ad-scout-handoff/search-ad-board-plan.md.
"""
import datetime
import re
import unicodedata
import urllib.parse

PROVERENO_DNI = 90     # reklama běžící 90+ dní = prověřená trhem (winner proxy)
GAP_MAX_BIDDERS = 4    # mezera = dotaz s 0–4 inzerenty (0–2 zelená · 3–4 oranžová střední); 5+ = velká konkurence, ven
MAX_BIDDERS = 5        # brzda: max 5 firem v sekci 1
MAX_GAP = 10           # brzda: max 10 slov v mezeře
MAX_CLONE = 3          # brzda: 3 hotové reklamy k naklonování


def _domain(url_or_disp):
    """Registrovaná doména z URL nebo displayedUrl (bez www, bez cesty)."""
    s = (url_or_disp or "").strip().lower()
    if not s:
        return None
    if "://" not in s:
        s = "http://" + s
    try:
        host = urllib.parse.urlparse(s).netloc.split(":")[0]
    except Exception:
        return None
    host = host[4:] if host.startswith("www.") else host
    return host or None


def _slug(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def _name_from_domain(dom):
    """bjp-store.cz → Bjp-store (fallback jméno, model ho zpřesní)."""
    base = (dom or "").split(".")[0]
    return base.capitalize() if base else dom


def _collect_bidders(serp, client_domain=None):
    """Dedup inzerentů napříč dotazy + intenzita + reálná copy + sitelinky."""
    client = (client_domain or "").lower()
    by = {}
    for row in serp or []:
        q = row.get("query") or ""
        for p in row.get("paid") or []:
            dom = _domain(p.get("displayed") or p.get("url"))
            if not dom:
                continue
            b = by.setdefault(dom, {"domain": dom, "queries": [], "positions": [],
                                    "ads": [], "sitelinks": []})
            if q and q not in b["queries"]:
                b["queries"].append(q)
            if isinstance(p.get("pos"), (int, float)):
                b["positions"].append(int(p["pos"]))
            if p.get("title") and len(b["ads"]) < 4:
                b["ads"].append({"head": p["title"], "desc": p.get("desc") or "",
                                 "query": q, "pos": p.get("pos"), "url": p.get("url")})
            for sl in p.get("sitelinks") or []:
                if sl not in b["sitelinks"]:
                    b["sitelinks"].append(sl)
    out = []
    for b in by.values():
        pos = b["positions"]
        out.append({
            "domain": b["domain"],
            "nazev": _name_from_domain(b["domain"]),
            "intenzita": len(b["queries"]),
            "dotazy": b["queries"],
            "nejlepsi_pozice": min(pos) if pos else None,
            "prumerna_pozice": round(sum(pos) / len(pos), 1) if pos else None,
            "ukazky": b["ads"],
            "sitelinks": b["sitelinks"][:8],
            "is_client": bool(client and client in b["domain"]),
        })
    out.sort(key=lambda x: (-x["intenzita"], x["nejlepsi_pozice"] or 99))
    return out


def _img_thumb(t):
    # JS preview registru (`/ads/preview/content.js`) nejde vložit jako <img> — jen přímé obrázky
    return bool(t) and "/ads/preview/content.js" not in t


def _norm_txt(s):
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _tema_creatives(ads, tema):
    """Kreativy z registru RELEVANTNÍ k tématu (text obsahuje téma; k→c varianta pro
    CZ/EN pravopis, např. kreatin/creatine). Velcí inzerenti (Alza, Dr. Max) mají v registru
    stovky reklam na cokoli — bez filtru board ukáže tašku na pleny místo kreatinu.
    Radši ŽÁDNÁ kreativa než nesouvisející."""
    t = _norm_txt(tema).strip()
    stems = {s for s in (t, ("c" + t[1:]) if t.startswith("k") else None) if s}
    vis = [a for a in ads or [] if _img_thumb(a.get("thumb"))
           and any(s in _norm_txt(a.get("text")) for s in stems)]
    vis.sort(key=lambda a: -(a.get("days") or 0))
    return [a["thumb"] for a in vis[:3]]


def _enrich_portfolio(bidders, portfolio, tema=None):
    """Doplní bidderům data z reklamního registru: max stáří, počet reklam, prověřeno
    + `nahledy` (až 3 archivní kreativy K TÉMATU — vizuál na board zadarmo)."""
    for b in bidders:
        ads = (portfolio or {}).get(b["domain"]) or []
        days = [a.get("days") for a in ads if isinstance(a.get("days"), int)]
        b["registr"] = {
            "reklam": len(ads),
            "nejstarsi_dni": max(days) if days else None,
            "formaty": sorted({a.get("format") for a in ads if a.get("format")}),
        }
        b["provereno"] = bool(days and max(days) >= PROVERENO_DNI)
        b["nahledy"] = _tema_creatives(ads, tema) if tema else []
    return bidders


_INFO_PAT = re.compile(r"účink|škodliv|dávkov|davkov|\bjak\b|co je|proč|proc\b|recenz|zkušenost|vedlejší|mýt|myt(?:us|y)", re.I)


def _semafor(gap, density, tema=None):
    """Semafor rozpočtu DETERMINISTICKY (data, ne dojem). Klasifikace podle POČTU inzerentů:
    0–2 = zelená (mezera, levný vstup) · 3–4 = oranžová (střední konkurence) · 5+ = červená
    (velká konkurence — nátlak začíná u 5, ne u 3) · informační dotazy = obsah (video/článek, ne PPC).
    Nákupní long-tail (gap) klasifikuj podle jeho počtu; obecné head dotazy (density) nikdy zelená —
    jeden snímek podceňuje nasycenou hlavu (min. oranžová). **Hlavní slovo oboru (`tema`) = VŽDY červená**
    (nejvíc kontestované, nejdražší klik — patří tam, i když ho jeden snímek podcenil). Model smí přeřadit."""
    zelena, oranzova, cervena, obsah = [], [], [], []
    gset = set()
    head = (tema or "").strip().lower()
    for g in gap:
        kw, n = g["kw"], (g.get("inzerentu") or 0)
        gset.add(kw.strip().lower())
        if _INFO_PAT.search(kw):
            obsah.append(kw)
        elif n <= 2:
            zelena.append(kw)
        elif n <= 4:
            oranzova.append(kw)
        else:
            cervena.append(kw)
    for d in density or []:
        q = (d.get("query") or "").strip()
        n = d.get("inzerentu") or 0
        if not q or q.lower() in gset:
            continue
        if _INFO_PAT.search(q):
            obsah.append(q)
        elif head and q.lower() == head:
            cervena.append(q)          # hlavní slovo oboru = vždy velká konkurence
        elif n >= 5:
            cervena.append(q)
        else:
            oranzova.append(q)         # ostatní head dotaz nikdy zelená (viz docstring)
    # hlavní slovo musí být na boardu vždy (i když ho density nezachytil)
    if head and head not in {x.strip().lower() for x in cervena + oranzova + zelena + obsah}:
        cervena.insert(0, tema)
    return {"zelena": zelena, "obsah": obsah, "oranzova": oranzova, "cervena": cervena}


def _density(serp):
    """Hustota: dotaz → počet unikátních inzerentů v placeném bloku.
    ⚠️ Reklamy se v SERPu STŘÍDAJÍ (ověřeno naostro: stejný dotaz, hodina rozdíl, jiní
    inzerenti) → víc snímků téhož dotazu se SJEDNOCUJE (union inzerentů), ne přepisuje."""
    by_q = {}
    order = []
    for row in serp or []:
        q = (row.get("query") or "").strip()
        if not q:
            continue
        doms = {_domain(p.get("displayed") or p.get("url")) for p in row.get("paid") or []}
        doms.discard(None)
        if q not in by_q:
            by_q[q] = set()
            order.append(q)
        by_q[q] |= doms
    return [{"query": q, "inzerentu": len(by_q[q]), "inzerenti": sorted(by_q[q])}
            for q in order]


def _kw_index(keywords):
    return {k["kw"]: k for k in (keywords or []) if k.get("kw")}


def _gap_candidates(probes, keywords, main_density):
    """Mezera = probe dotazy s 0–GAP_MAX_BIDDERS inzerenty, obohacené o volume/CPC.
    Jen OVĚŘENÁ hustota (reálný SERP), žádné odhady. Model pak kurátoruje (zamer/pozn)."""
    kwi = _kw_index(keywords)
    cands = []
    seen = set()
    for row in _density(probes) + [d for d in main_density if d["inzerentu"] <= GAP_MAX_BIDDERS]:
        q = (row.get("query") or "").strip().lower()
        if not q or q in seen or row["inzerentu"] > GAP_MAX_BIDDERS:
            continue
        seen.add(q)
        met = kwi.get(q) or {}
        cands.append({
            "kw": q,
            "inzerentu": row["inzerentu"],
            "inzerenti": row.get("inzerenti") or [],
            "volume": met.get("volume"),
            "cpc_odhad": met.get("cpc"),
            "konkurence": met.get("competition"),
            "zamer": met.get("intent"),      # model přepíše česky (nákupní/informační…)
            "semafor": "zelena",             # ověřená mezera = zelená (model může přeřadit)
            "pozn": None,                    # model: proč to slovo / jak ho použít
        })
    cands.sort(key=lambda x: (x["inzerentu"], -(x["volume"] or 0)))
    return cands[:MAX_GAP]


def _clone_skeleton(bidders):
    """Kostra sekce 2: reálné reklamy top bidderů (vzor) — klon doplní MODEL.
    Mechanika, ne rozbor úhlů (to je Viral)."""
    out = []
    for b in bidders[:MAX_CLONE]:
        if not b.get("ukazky"):
            continue
        best = b["ukazky"][0]
        out.append({
            "vzor": {
                "inzerent": b["nazev"], "domain": b["domain"],
                "head": best.get("head"), "desc": best.get("desc"),
                "sitelinks": b.get("sitelinks") or [],
                "dni": (b.get("registr") or {}).get("nejstarsi_dni"),
                "provereno": b.get("provereno", False),
                "query": best.get("query"),
                # vizuál: archivní kreativa z registru — vyplní bílé místo, když SERP nedá desc
                "thumb": (b.get("nahledy") or [None])[0],
            },
            # MODEL: naklonovaná kostra vítěze s dosazenou nabídkou klienta
            "klon": {"head": None, "desc": None, "sitelinks": [], "pozn": None},
        })
    return out


def build(fetched, tema, trh="cz", client_domain=None, client_name=None, probes=None):
    serp = fetched.get("serp") or []
    portfolio = fetched.get("portfolio") or {}
    keywords = fetched.get("keywords") or []
    probes = probes or fetched.get("probes") or []

    bidders = _enrich_portfolio(_collect_bidders(serp, client_domain), portfolio, tema)
    density = _density(serp)
    gap = _gap_candidates(probes, keywords, density)

    n_paid = sum(len(r.get("paid") or []) for r in serp)
    n_queries = len({(r.get("query") or "").strip().lower() for r in serp if r.get("query")})
    n_probes = len({(r.get("query") or "").strip().lower() for r in probes if r.get("query")})
    max_days = max((b["registr"]["nejstarsi_dni"] or 0 for b in bidders if b.get("registr")), default=0)
    return {
        "meta": {"skill": "ad-scout", "vystup": "search-ad-board", "tema": tema, "trh": trh,
                 "sken": datetime.date.today().isoformat(),
                 "klient": {"domain": client_domain, "nazev": client_name},
                 "podtitulek": None},  # MODEL (volitelně; jinak default rendereru)
        "pokryti": {"dotazu": n_queries, "probe_dotazu": n_probes,
                    "inzerentu": len(bidders), "placenych_reklam": n_paid,
                    "portfolio_inzerentu": len(portfolio), "kw_metrik": len(keywords),
                    "mezera_slov": len(gap), "nejdelsi_beh_dni": max_days},
        # 01 Kdo vám kupuje zákazníky — max 5, model doplní `proc_nebezpecny` (1 věta) top 3
        "bidders": [dict(b, proc_nebezpecny=None) for b in bidders[:MAX_BIDDERS]],
        # 02 Search DNA — hotové reklamy k naklonování (mechanika: struktura/čísla/rozšíření)
        "cloneable_ads": _clone_skeleton(bidders),
        # 03 Mezera v klíčových slovech (ověřená hustota z živého SERPu)
        "keyword_gap": gap,
        # hustota na hlavních dotazech (podklad semaforu + kontext pro model)
        "hustota": density,
        # 04 Souboj landingů — CELÉ plní MODEL (WebFetch landingů top 3 bidderů)
        "landing_gaps": [{"domain": b["domain"], "nazev": b["nazev"], "url": None,
                          "slib": None, "cena_viditelna": None, "cta": None,
                          "trust": None, "chybi": None} for b in bidders[:3]],
        "landing_pointa": None,  # MODEL: čím je klient přebije (1–2 věty)
        # 05 Semafor ceny — DETERMINISTICKY (model dolaďuje, nepřepisuje logiku):
        # zelená = slova z mezery (nákupní long-tail) · obsah = informační dotazy (patří
        # obsahu, ne PPC) · červená = plný blok (3+ inzerentů) · oranžová = zbytek hlavních
        # dotazů (obecná slova — snímek 0 inzerentů ≠ levná aukce, obecné je vždy dražší)
        "budget_semafor": dict(_semafor(gap, density, tema),
                               benchmark_pozn=None,  # MODEL: oborové CPC rozpětí (vždy „odhad")
                               priklad={"rozpocet_kc": None, "kliku_odhad": None, "pozn": None}),
        # 06 Akční plán na 30 dní — MODEL (přesně 3 kroky)
        "action_plan": [],
        # surová keyword metrika pro model (do klientského výstupu NEJDE — brzda: žádné
        # výpisy 30+ slov s objemy; board ukazuje max 10 slov mezery)
        "_keywords_raw": keywords[:80],
        "_todo": ("MODEL doplní: proc_nebezpecny (top 3) · klony reklam · zamer/pozn mezery · "
                  "landing_gaps přes WebFetch · semafor + benchmark + priklad · action_plan (3 kroky) · "
                  "podtitulek. Viz references/search-ad-board.md."),
    }
