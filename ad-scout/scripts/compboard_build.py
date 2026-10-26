#!/usr/bin/env python3
"""Build machine contractu pro Competitor Ad Board (osa = ZNAČKA, vstup = doména konkurenta).

Deterministická část (winner skóre, seskupení variant, stat row, kostra kontraktu) žije tady;
renderer `adboard.render_competitor` jen vykresluje. Sémantiku (překlady, úhly, fáze povědomí,
typ kampaně výkonová/image/nábor, „proč" odrážky, mapa útoku, útočný plán) plní MODEL —
stejný vzor jako Viral Ad Board (`adboard_build.py`).

Winner scoring (plán §3): PRIMÁRNĚ dosah EU × počet variant (varianty = nejspolehlivější
signál — 5+ verzí téhož konceptu = interní data konkurenta prosakují ven), dny běhu jen
SEKUNDÁRNĚ (brandové/náborové kampaně běží dlouho bez ohledu na výkon → labelovat zvlášť,
neklonovat jako výkonové).

Vstup = normalizované položky z providera:
  meta_ads:   [{page_name, ad_creative_body, ad_creative_link_title, reach,
                ad_delivery_start_time, publisher_platforms, ad_snapshot_url,
                thumbnail, video_url, catalog}]
  google_ads: [{advertiser, format, text, url, days, last_shown, thumb, video_url}]
  landing:    {pixels:[…], social:{net:url}, title}
  serp:       výstup provider.search_results (organic/paid/ai_overview)
  sitemap:    [url, …]

Výstup = competitor-contract.json (schéma: references/competitor-ad-board.md).
v0.1 — MVP: stat row + 01 Vítězové + 02 Mapa útoku (kostru plní model) + 09 Útočný plán (model).
"""
import datetime
import math
import os
import re
import urllib.parse

from adboard_build import dl_thumb, hook_of, detect_angle, slugify, is_cz_text  # sdílené helpery

WINNERS_CAP = 10          # TOP N karet v sekci 01 (donor banka)
GOOGLE_SHOW = 30          # pool ukázek z registru Googlu v kontraktu — schválně větší: registr vrací
                          # reklamy per INZERENT (všechny trhy), model vision-filtrem zahraniční označí
                          # `mimo_trh` a mřížka musí i po filtru ukázat ≥12 domácích kusů

# Náborové kampaně poznáme deterministicky (brand/image označí model).
_HIRING = re.compile(r"\b(nábor|kariér|hledáme|přidej se|join (our|the) team|hiring|"
                     r"pracuj u nás|volná pozice|staň se součástí)\b", re.I)


def score_comp(reach, variants, days):
    """Winner skóre: dosah EU (55) × varianty (30) primárně, dny běhu sekundárně (15)."""
    return round(55 * min(math.log10(max(reach or 0, 10)) / 6, 1)
                 + 30 * min(variants or 1, 8) / 8
                 + 15 * min(days or 0, 180) / 180)


def _days_since(start):
    if not start:
        return None
    try:
        d0 = datetime.date.fromisoformat(str(start)[:10])
        return max((datetime.date.today() - d0).days, 0)
    except Exception:
        return None


def _concept_key(ad):
    """Klíč kreativního konceptu: stejná/velmi podobná copy = varianty JEDNOHO konceptu.
    (U competitor boardu jsou všechny reklamy téže stránky → varianty se počítají per koncept,
    ne per inzerent jako u Viral boardu.)"""
    blob = ((ad.get("ad_creative_body") or "") + " " + (ad.get("ad_creative_link_title") or "")).strip().lower()
    blob = re.sub(r"\s+", " ", blob)
    return blob[:80] or ("__thumb__" + str(ad.get("thumbnail") or id(ad)))


def _ad_sites(plat):
    nets = []
    for p in (plat if isinstance(plat, list) else [plat] if plat else []):
        n = {"FACEBOOK": "facebook", "INSTAGRAM": "instagram"}.get(str(p).upper())
        if n and n not in nets:
            nets.append(n)
    return nets or ["facebook"]


def build(fetched, konkurent, trh="cz", klient=None, angle_rules=None, assets_dir=None):
    """Sestaví kostru competitor-contractu. `konkurent` = {znacka?, domena}; `klient` volitelně
    {znacka?, domena?} (kontext pro model — proti komu se útočí). Sémantiku doplní MODEL."""
    meta_in = [a for a in (fetched.get("meta_ads") or [])]
    google_in = [a for a in (fetched.get("google_ads") or [])]
    landing = fetched.get("landing") or {}
    serp = fetched.get("serp") or {}
    sitemap = fetched.get("sitemap") or []
    domena = (konkurent or {}).get("domena") or ""
    znacka = (konkurent or {}).get("znacka") or (landing.get("title") or domena).split("|")[0].strip()

    # --- koncepty: seskup varianty téže copy, reprezentant = nejvyšší dosah ---
    concepts = {}
    for a in meta_in:
        k = _concept_key(a)
        c = concepts.setdefault(k, {"ads": [], "variants": 0})
        c["ads"].append(a)
        c["variants"] += 1
    reps = []
    for c in concepts.values():
        rep = max(c["ads"], key=lambda x: (x.get("reach") or 0))
        rep = dict(rep)
        rep["variants"] = c["variants"]
        rep["days"] = _days_since(rep.get("ad_delivery_start_time"))
        rep["score"] = score_comp(rep.get("reach"), rep["variants"], rep.get("days"))
        reps.append(rep)
    # katalogy ven z vítězů (nejsou klonovatelné), ale zůstávají ve statistice
    winners_pool = [r for r in reps if not r.get("catalog")]
    winners_pool.sort(key=lambda r: -r["score"])

    vitezove = []
    for i, r in enumerate(winners_pool[:WINNERS_CAP]):
        blob = (r.get("ad_creative_link_title") or "") + " " + (r.get("ad_creative_body") or "")
        typ = "nabor" if _HIRING.search(blob) else None  # image/brand označí model
        thumb = None
        if assets_dir and r.get("thumbnail"):
            thumb = dl_thumb(r["thumbnail"], os.path.join(assets_dir, f"win-{slugify(znacka)}-{i}.jpg"))
        vitezove.append({
            "poradi": i + 1,
            "nm": r.get("ad_creative_link_title") or hook_of(r.get("ad_creative_body") or ""),
            "orig": None,                      # model: překlad → nm česky, originál sem
            "uhel": detect_angle(blob, angle_rules),
            "aw": None,                        # model: fáze povědomí
            "typ": typ,                        # None=výkonová (default) | "image" | "nabor" — model potvrdí
            "score": r["score"], "dosah_eu": r.get("reach"), "dni": r.get("days"),
            "varianty": r["variants"], "site": _ad_sites(r.get("publisher_platforms")),
            "url": r.get("ad_snapshot_url"), "thumb": thumb, "video_url": r.get("video_url"),
            "why": None,                       # model: 3× proč vyhrává
            "klon": None,                      # model: jak naklonovat na produkt klienta
            "_text": r.get("ad_creative_body"),  # syrová copy pro model — do výstupu NEJDE
        })

    # --- Google registr: ukázky pro úhly + formátový mix ---
    google_reklamy, fmt_mix = [], {}
    for g in google_in:
        fmt = g.get("format") or "text"
        fmt_mix[fmt] = fmt_mix.get(fmt, 0) + 1
    # ukázky: napřed kreativy s PŘÍMÝM obrázkem (simgad/gstatic — jde vložit jako <img>),
    # JS preview (`/ads/preview/content.js`) až jako poslední — v <img> nefunguje a Playwright
    # render vrací prázdno; pak s copy, pak dle dnů běhu
    def _gkey(x):
        js = "/ads/preview/content.js" in (x.get("thumb") or "")
        return (js, not (x.get("text") or "").strip(), -(x.get("days") or 0))
    for g in sorted(google_in, key=_gkey)[:GOOGLE_SHOW]:
        txt = (g.get("text") or "").strip()
        item = {
            "nm": hook_of(txt) or None, "format": g.get("format"),
            "dni": g.get("days"), "url": g.get("url"), "thumb": g.get("thumb"),
        }
        # předznačení cizího trhu: registr vrací reklamy per INZERENT (všechny jeho trhy);
        # neprázdný text mimo jazyk trhu → mimo_trh (model pak vision-kontrolou potvrdí/doplní
        # i kusy bez textu — doména je vidět jen ve screenshotu kreativy)
        if txt and not is_cz_text(txt):
            item["mimo_trh"] = True
        google_reklamy.append(item)

    # --- stat row ---
    days_all = [r.get("days") for r in reps if r.get("days") is not None] + \
               [g.get("days") for g in google_in if g.get("days") is not None]
    new30 = sum(1 for r in reps if (r.get("days") is not None and r["days"] <= 30)) + \
            sum(1 for g in google_in if (g.get("days") is not None and g["days"] <= 30))
    stat = {
        "aktivnich_reklam": len(meta_in) + len(google_in),
        "meta_reklam": len(meta_in), "google_reklam": len(google_in),
        "konceptu": len(reps), "katalogovych": sum(1 for r in reps if r.get("catalog")),
        "nejdele_bezici_dni": max(days_all, default=0),
        "top_dosah_eu": max((r.get("reach") or 0 for r in meta_in), default=0),
        "nove_30d": new30,
        "uhly_volne": None,  # doplní model z mapy útoku
        # reálné počty z registrů — doplní AGENT přes browser tool (NE Apify, NE scraping):
        # otevře registry.meta_adlib („~N výsledků") a registry.google („přibližně N reklam")
        # a přečte první číslo na stránce. Vzorek z Apify zůstává levný, tohle jsou 2 page loady.
        "registr_total": None,  # {"meta": N, "google": N}
    }

    dom = re.sub(r"^https?://(www\.)?", "", domena.lower()).split("/")[0]
    registry = {
        "google": f"https://adstransparency.google.com/?region={trh.upper()}&domain={dom}",
        "meta": (landing.get("social", {}) or {}).get("facebook"),  # page → knihovna přes kartu reklamy
        "meta_adlib": ("https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
                       f"&country={trh.upper()}&q={urllib.parse.quote(znacka)}&search_type=page&media_type=all"),
    }

    return {
        "meta": {"skill": "ad-scout", "vystup": "competitor-ad-board", "trh": trh,
                 "konkurent": {"znacka": znacka, "domena": dom},
                 "klient": (klient or {})},
        "stat": stat,
        "kanaly": {"pixely": landing.get("pixels") or [], "site": landing.get("social") or {},
                   "registry": registry},
        "vitezove": vitezove,
        "google_reklamy": google_reklamy,
        "google_mix": fmt_mix,
        "landing_pages": sitemap,
        "serp": {"organic": (serp.get("organic") or [])[:8], "paid": serp.get("paid") or [],
                 "ai_overview": bool(serp.get("ai_overview"))},
        # ↓↓↓ sémantika — DOPLNÍ MODEL (viz references/competitor-ad-board.md „Co plní MODEL")
        "mapa_utoku": {"faze": [], "radky": [], "prilezitosti": []},
        "utocny_plan": [],
        "pokryti": {"meta": len(meta_in), "google": len(google_in), "koncepty": len(reps),
                    "vitezove": len(vitezove), "landing_pages": len(sitemap)},
    }
