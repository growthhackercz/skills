#!/usr/bin/env python3
"""ad-scout — validovaný wrapper pro Product Intelligence Board + Viral Ad Board.

Žádný přímý shell v skillu — vše přes tenhle wrapper.

  # Product Intelligence Board (osa = produkt)
  fetch "<produkt>" --market cz [--client-domain d] [--dry-run] [--refresh]
  build "<produkt>" [--board]

  # Viral Ad Board (osa = téma / klíčové slovo)
  viral-fetch "<téma>" --market cz [--b2b] [--since '18 months'] [--dry-run] [--refresh]
  viral-render "<téma>"

  # Search Ad Board (osa = klíčové slovo; taktika placeného Google Search)
  search-fetch "<slovo>" --market cz [--client-domain d] [--keywords "a;b"] [--dry-run] [--refresh]
  search-probe "<slovo>" --queries "a;b;c" [--dry-run]     # ověření hustoty na model-generovaných slovech
  search-render "<slovo>"

fetch/build  = Product board: Heureka + Google SERP + Meta → scout-report.json (--board = HTML).
viral-fetch  = Viral board: knihovna reklam + organika (content_search keyword napříč sítěmi) +
               vyhledávání → adboard_build.build → rich-contract.json (KOSTRA). Pak STOP:
               MODEL doplní sémantiku (překlad nm/orig, úhel, awareness, why, mapa úhlů, syntéza,
               hooky, search_uhly, jazyk_zakaznika). Detaily: references/viral-ad-board.md.
viral-render = vyrenderuje (modelem doplněný) rich-contract.json → viral-ad-board.html.

Kredity = klientské peníze → VŽDY nejdřív --dry-run. Denní cache (fetch 1×/den/téma).
v0.1 — DRAFT, chce 1 validační běh (Google SERP + IG/FB komenty ověřeny; ostatní tvar potvrdit).
"""
import argparse
import datetime
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import provider  # noqa: E402
import adboard_build  # noqa: E402
import dnacard_build  # noqa: E402
import searchboard_build  # noqa: E402

RUNS_BASE = os.environ.get("AD_SCOUT_RUNS", "/documents/ads/scout/products")
RUNS_KW = os.environ.get("AD_SCOUT_RUNS_KW", "/documents/ads/scout/keywords")

# Capy (drží náklad při zemi) + odhad ceny za výpis (USD).
CAPS = {"heureka_offers": 40, "heureka_reviews": 30, "serp": 20, "meta": 30}
EST_COST = {"heureka": 0.03, "serp": 0.003, "meta": 0.02}  # ~$0,05 celkem
# Viral board: embed ~20/sekce pro analýzu (board zobrazí 10 + „načíst dalších"); organika per síť.
# Fetch s REZERVOU, aby po filtraci/dedupu zbylo top ~20 k zobrazení (jinak sekce nikdy nemá 20).
# Zobrazení řídí AD_SHOW/SHORT_SHOW/LONG_SHOW=20 v adboard.py; tohle je jen fetch headroom.
VCAPS = {"ads": 40, "per_platform": 30, "serp": 1}
VEST = {"adlib": 0.05, "organic": 0.55, "serp": 0.005, "comments": 0.2}  # ~$0,8/board (ads levné, organika CZ+EN, komenty bez YT)
CMT_POSTS_PER_NET = 2   # kolik top organických postů/síť mine na komentáře (bounded — kredity)
CMT_CAP = 40            # max komentářů/post
AD_MIN = 20             # cíl TOP 20 konkrétních reklam; když v CZ míň, doplň ze zahraničí (globální)
AD_VIDEO_MIN = 3        # min. videoreklam; když CZ konkurence video nejede (= díra), dotáhni zahraniční video
AD_FOREIGN = ["SK", "DE", "AT", "PL", "US", "GB"]  # sousední + velké trhy (podobné značky/termín, video inspirace)


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:50] or "produkt"


def today():
    return datetime.date.today().isoformat()


def run_dir(product, date=None):
    d = os.path.join(RUNS_BASE, slugify(product), date or today())
    os.makedirs(d, exist_ok=True)
    return d


def latest_today(product):
    d = os.path.join(RUNS_BASE, slugify(product), today())
    return d if os.path.isfile(os.path.join(d, "raw.json")) else None


# ---- fetch -----------------------------------------------------------------

def cmd_fetch(a):
    if a.dry_run:
        total = sum(EST_COST.values())
        print("DRY-RUN — 0 útraty. Odhad ostrého běhu:")
        print(f"  Heureka nabídky+recenze  ~${EST_COST['heureka']:.3f}  (cap {CAPS['heureka_offers']}/{CAPS['heureka_reviews']})")
        print(f"  Google SERP (CZ)         ~${EST_COST['serp']:.3f}  (cap {CAPS['serp']})")
        print(f"  Meta Ad Library          ~${EST_COST['meta']:.3f}  (cap {CAPS['meta']})")
        print(f"  ── celkem                ~${total:.2f} za jeden výpis")
        print("STOP — potvrď, než pustíš ostrý fetch (bez --dry-run).")
        return

    if not a.refresh and latest_today(a.product):
        print(f"Cache: dnešní běh existuje ({latest_today(a.product)}). Použij build, nebo --refresh.")
        return

    if not provider.has_key():
        print("Bez APIFY_API_KEY — placené zdroje přeskočeny. Doplň volné zdroje do agent_items.json (viz SKILL Krok 4).")
        rd = run_dir(a.product)
        _save(rd, "raw.json", {"product": a.product, "market": a.market,
                               "client_domain": a.client_domain, "sources": [], "no_key": True})
        return

    raw = {"product": a.product, "market": a.market, "client_domain": a.client_domain,
           "fetched_at": today(), "sources": []}
    print("Fetch: ceny + nabídky…")
    raw["prices"] = provider.price_offers(a.product, a.market, CAPS["heureka_offers"])
    if raw["prices"]:
        raw["sources"].append("market-prices")
    print("Fetch: recenze…")
    raw["reviews_raw"] = provider.price_reviews(a.product, a.market, CAPS["heureka_reviews"])
    if raw["reviews_raw"]:
        raw["sources"].append("market-reviews")
    print("Fetch: výsledky vyhledávání…")
    raw["search"] = provider.search_results(a.product, a.market)
    if raw["search"]:
        raw["sources"].append("search")
    print("Fetch: knihovna reklam…")
    raw["adlib"] = provider.ad_library(a.product, a.market.upper())
    if raw["adlib"]:
        raw["sources"].append("ad-library")

    rd = run_dir(a.product)
    _save(rd, "raw.json", raw)
    print(f"Hotovo → {rd}/raw.json  (zdroje: {', '.join(raw['sources']) or 'žádné'})")


# ---- build -----------------------------------------------------------------

def cmd_build(a):
    rd = latest_today(a.product) or run_dir(a.product)
    raw_path = os.path.join(rd, "raw.json")
    if not os.path.isfile(raw_path):
        print("Nejdřív fetch (nebo doplň agent_items.json). Chybí raw.json.")
        return
    raw = json.load(open(raw_path))

    report = {
        "board": "product-intelligence",
        "generated_at": today(),
        "market": raw.get("market", "cz"),
        "trigger": {"type": "product_name", "query": a.product},
        "client": {"domain": raw.get("client_domain")},
        "sources": raw.get("sources", []),
        "caveats": ["meta=inzerent-level", "denní snímek, ne real-time"],
    }
    report["price_map"] = _price_map(raw)
    report["kpi"] = _kpi(report["price_map"])
    report["signals"] = {"price_drops": _price_drops(a.product, report["price_map"]),
                         "low_30d": _low30(raw, report["price_map"]),
                         "stock": _stock(raw)}
    report["search"] = _search(raw)
    report["meta_ads"] = _meta(raw)
    # reviews.hooks / assortment.gaps / action_plan = doplní MODEL (SKILL Krok 6).
    report.setdefault("reviews", {"praise": _rev(raw, "pos"), "criticism": _rev(raw, "neg"), "hooks": [],
                                  "_todo": "náměty vyrobí model z recenzí (SKILL Krok 6)"})
    report.setdefault("assortment", {"have": [], "gaps": [],
                                     "_todo": "díry v sortimentu doplní model"})
    report.setdefault("action_plan", [])

    _save(rd, "scout-report.json", report)
    print(f"Machine contract → {rd}/scout-report.json")

    if a.board:
        try:
            import board
            out = board.render(report, os.path.join(rd, "product-intelligence-board.html"))
            print(f"Board → {out}")
        except Exception as e:
            print(f"[board] render selhal: {type(e).__name__}: {e}")


def _num(x):
    try:
        return float(re.sub(r"[^\d.]", "", str(x)))
    except Exception:
        return None


def _price_map(raw):
    """Normalizuj Heureka nabídky do žebříčku podle landed (cena+doprava).
    Tvar Heureka aktoru POTVRDIT — tady defenzivní parsování běžných klíčů."""
    offers = []
    h = raw.get("prices") or []
    if isinstance(h, dict):
        h = h.get("offers") or h.get("shops") or []
    client = (raw.get("client_domain") or "").lower()
    for o in (h or [])[:CAPS["heureka_offers"]]:
        shop = o.get("shop") or o.get("shopName") or o.get("seller")
        dom = (o.get("domain") or o.get("url") or "").lower()
        price = _num(o.get("price") or o.get("priceWithVat"))
        ship = _num(o.get("shipping") or o.get("delivery") or 0) or 0
        if not shop or price is None:
            continue
        offers.append({
            "shop": shop, "domain": dom, "price": price, "shipping": ship,
            "landed": price + ship, "note": o.get("note", ""),
            "availability": o.get("availability") or o.get("stock") or "",
            "is_client": bool(client and client in dom),
            "logo": f"https://www.google.com/s2/favicons?domain={dom}&sz=64" if dom else None,
        })
    offers.sort(key=lambda x: x["landed"])
    if offers:
        offers[0]["is_min"] = True
    return offers


def _kpi(pm):
    if not pm:
        return {}
    landeds = sorted(x["landed"] for x in pm)
    med = landeds[len(landeds) // 2]
    client = next((x for x in pm if x.get("is_client")), None)
    kpi = {"lowest_price": min(x["price"] for x in pm),
           "lowest_shop": pm[0]["shop"], "rank_of": len(pm)}
    if client:
        kpi["your_landed"] = client["landed"]
        kpi["price_index_pct"] = round(client["landed"] / med * 100) if med else None
        kpi["rank"] = pm.index(client) + 1
    return kpi


def _history_report(product):
    """Nejnovější PŘEDCHOZÍ (ne dnešní) scout-report.json pro produkt = podklad cenopádu."""
    base = os.path.join(RUNS_BASE, slugify(product))
    if not os.path.isdir(base):
        return None
    days = sorted(d for d in os.listdir(base) if d < today())
    for d in reversed(days):
        p = os.path.join(base, d, "scout-report.json")
        if os.path.isfile(p):
            try:
                return json.load(open(p))
            except Exception:
                pass
    return None


def _price_drops(product, pm):
    """Derived $0 — kdo dnes zlevnil proti poslednímu předchozímu snímku."""
    prev = _history_report(product)
    if not prev:
        return []
    old = {o.get("shop"): o.get("landed") for o in prev.get("price_map", []) if o.get("landed")}
    drops = []
    for o in pm:
        was = old.get(o["shop"])
        if was and o["landed"] < was:
            pct = round((o["landed"] - was) / was * 100)
            drops.append({"shop": o["shop"], "pct": pct, "landed": o["landed"],
                          "delta": round(o["landed"] - was)})
    return sorted(drops, key=lambda x: x["pct"])


def _low30(raw, pm):
    """Nejnižší cena za 30 dní ze zdroje (srovnávač/e-shop ji často uvádí) —
    reálný cenopád-proxy dostupný UŽ NA PRVNÍM běhu (nezávisí na naší historii).
    Bere nejnižší z per-obchodních 30denních minim; current_low = dnešní tržní minimum."""
    offers = raw.get("prices") or []
    if isinstance(offers, dict):
        offers = offers.get("offers") or []
    lows = []
    for o in offers:
        v = _num(o.get("price_low_30d") or o.get("lowest_30d") or o.get("min_price_30d"))
        if v:
            lows.append((v, o.get("shop") or o.get("shopName")))
    if not lows:
        return {}
    lo = min(lows)
    cur = min((x["landed"] for x in pm), default=None) if pm else None
    return {"market_low_30d": lo[0], "shop": lo[1], "current_low": cur}


def _stock(raw):
    """Out-of-stock trigger (nejakčnější) + přehled dostupnosti z nabídek."""
    offers = raw.get("prices") or []
    if isinstance(offers, dict):
        offers = offers.get("offers") or []
    out, avail = [], []
    for o in offers:
        a = str(o.get("availability") or o.get("stock") or "").lower()
        shop = o.get("shop") or o.get("shopName")
        if not shop:
            continue
        if any(k in a for k in ("vyprod", "není skladem", "out of stock", "nedostup")):
            out.append({"shop": shop})
        elif a:
            avail.append({"shop": shop, "status": a})
    return {"out_of_stock": out, "availability": avail}


def _rev(raw, sign):
    """Surové +/− z recenzí (model je zpracuje na náměty). GDPR: bez jmen autorů."""
    rr = raw.get("reviews_raw") or []
    key = "pros" if sign == "pos" else "cons"
    out = []
    for r in (rr if isinstance(rr, list) else []):
        for item in (r.get(key) or []):
            if item and item not in out:
                out.append(item)
    return out[:6]


def _search(raw):
    s = raw.get("search") or {}
    paid_names = []
    for p in s.get("paid", []):
        for sl in (p.get("siteLinks") or []):
            t = (sl.get("title") or "").split("http")[0].strip()
            if t and t not in paid_names and len(t) < 40:
                paid_names.append(t)
    return {"organic": s.get("organic", []), "paid": paid_names[:6],
            "ai_overview": bool(s.get("ai_overview"))}


def _meta(raw):
    ads = raw.get("adlib") or []
    by = {}
    for ad in ads:
        name = ad.get("page_name") or ad.get("advertiser")
        if not name:
            continue
        by.setdefault(name, {"advertiser": name, "ads_count": 0, "starts": []})
        by[name]["ads_count"] += 1
        t = ad.get("ad_delivery_start_time")
        if t:
            by[name]["starts"].append(t)
    return sorted(by.values(), key=lambda x: -x["ads_count"])


# ---- Viral Ad Board (osa = téma) -------------------------------------------

def run_dir_kw(tema, date=None):
    d = os.path.join(RUNS_KW, slugify(tema), date or today())
    os.makedirs(d, exist_ok=True)
    return d


def latest_today_kw(tema):
    d = os.path.join(RUNS_KW, slugify(tema), today())
    return d if os.path.isfile(os.path.join(d, "rich-contract.json")) else None


def _days_since(start):
    if not start:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%d.%m.%Y"):
        try:
            d = datetime.datetime.strptime(str(start)[:19], fmt).date()
            return (datetime.date.today() - d).days
        except Exception:
            continue
    return None


def _ads_for_build(adlib):
    """Knihovna reklam (Ad Library) → tvar pro adboard_build.build. Tvar aktoru POTVRDIT —
    defenzivní parsování běžných klíčů (page/text/reach/start/plat/url/thumb)."""
    out = []
    for ad in (adlib or []):
        page = ad.get("page_name") or ad.get("advertiser") or ad.get("pageName")
        if not page:
            continue
        img = ad.get("thumbnail") or ad.get("imageUrl") or ad.get("video_preview_image_url")
        if not img:
            imgs = ad.get("images") or []
            first = imgs[0] if isinstance(imgs, list) and imgs else None
            img = first.get("original_image_url") if isinstance(first, dict) else first
        out.append({
            "page": page,
            "text": ad.get("ad_creative_body") or ad.get("text") or ad.get("body") or ad.get("adText") or "",
            "title": ad.get("ad_creative_link_title") or ad.get("title"),
            "reach": _num(ad.get("eu_total_reach") or ad.get("reach") or ad.get("euReach")),
            "days": _days_since(ad.get("ad_delivery_start_time") or ad.get("startDate") or ad.get("start_date")),
            "plat": ad.get("publisher_platforms") or ad.get("platforms") or ["FACEBOOK"],
            "url": ad.get("ad_snapshot_url") or ad.get("url") or ad.get("snapshotUrl"),
            "thumb": img,
            "video_url": ad.get("video_url"),  # video reklamy → play popup (poster = thumb)
            "geo": ad.get("_geo"),  # 'global' pro zahraniční doplněk, jinak None (CZ)
            "video_inspo": ad.get("_video_inspo"),  # zahraniční video dotažené kvůli chybějícímu CZ videu
        })
    return out


def _viral_for_build(items):
    """content_search výstup → tvar pro adboard_build.build (viral)."""
    out = []
    for x in (items or []):
        geo = x.get("geo")
        out.append({
            "net": x.get("sit"), "title": x.get("nm"), "who": x.get("kdo"),
            "views": x.get("zhlednuti"), "likes": x.get("likes"), "cmts": x.get("cmts"),
            "url": x.get("url"), "thumb": x.get("thumb"), "dur": x.get("dur"),
            "cz": (geo == "cz") if geo else None,  # None → build rozhodne z jazyka titulku
        })
    return out


def _search_for_build(search):
    """search_results (Google) → tvar pro adboard_build.build (search = placené inzeráty)."""
    paid = (search or {}).get("paid") or []
    out = []
    for p in paid:
        if isinstance(p, str):
            out.append({"brand": p, "head": p, "desc": "", "url": None, "queries": 1, "total": len(paid)})
        elif isinstance(p, dict):
            out.append({"brand": p.get("displayedLink") or p.get("title"), "head": p.get("title"),
                        "desc": p.get("description") or p.get("snippet") or "", "url": p.get("url"),
                        "queries": 1, "total": len(paid)})
    return out


def _fetch_comments(viralni, rd, posts_per_net=CMT_POSTS_PER_NET, cap=CMT_CAP):
    """Raw komenty pod TOP organikou (voice-of-customer) → comments.json; model z nich destiluje
    jazyk_zakaznika. Vstup = URL postů (veřejné, bez loginu, přes Apify proxy). Bounded per síť."""
    by_net = {}
    for v in (viralni or []):
        net = (v.get("sit") or "").lower()
        # YouTube komenty vynechány — actory konzistentně padají (403/400) a drahý Actor-Start fee = plýtvání.
        if net in ("instagram", "facebook", "tiktok") and v.get("url"):
            by_net.setdefault(net, []).append(v["url"])
    out = {}
    for net, urls in by_net.items():
        got = provider.content_comments(urls[:posts_per_net], net, cap=cap)
        print(f"  komenty {net}: {len(got or [])}")
        if got:
            out[net] = got
    _save(rd, "comments.json", out)
    return sum(len(v) for v in out.values())


def cmd_viral_fetch(a):
    platforms = ["tiktok", "youtube", "instagram", "facebook"] + (["linkedin"] if a.b2b else [])
    if a.dry_run:
        cmt = 0 if a.no_comments else VEST["comments"]
        total = VEST["adlib"] + VEST["organic"] + VEST["serp"] + cmt
        print("DRY-RUN — 0 útraty. Odhad ostrého běhu Viral Ad Boardu:")
        print(f"  Knihovna reklam              ~${VEST['adlib']:.3f}  (cap {VCAPS['ads']}, přes Apify token)")
        print(f"  Organika keyword × {len(platforms)} sítí   ~${VEST['organic']:.3f}  ({', '.join(platforms)}, cap {VCAPS['per_platform']}/síť)")
        print(f"  Vyhledávání (úhly)           ~${VEST['serp']:.3f}")
        print(f"  Komentáře (jazyk zákazníka)  ~${cmt:.3f}  ({'přeskočeno --no-comments' if a.no_comments else f'{CMT_POSTS_PER_NET} posty/síť × {CMT_CAP}'})")
        print(f"  ── celkem                    ~${total:.2f} za jedno téma")
        print("STOP — potvrď, než pustíš ostrý viral-fetch (bez --dry-run).")
        return
    if not a.refresh and latest_today_kw(a.tema):
        print(f"Cache: dnešní běh existuje ({latest_today_kw(a.tema)}). Uprav rich-contract.json + viral-render, nebo --refresh.")
        return
    if not provider.has_key():
        print("Bez APIFY_API_KEY — placené zdroje přeskočeny. Doplň organiku/reklamy ručně do rich-contract.json (viz SKILL Krok 4).")
        return
    rd = run_dir_kw(a.tema)
    print("Fetch: knihovna reklam (jen konkrétní, katalogy vyloučeny)…")
    adlib = provider.ad_library(a.tema, a.market.upper(), VCAPS["ads"]) or []
    seen = {r.get("page_name") for r in adlib}
    # 1) CZ→zahraničí: když v CZ málo konkrétních reklam, doplň ze sousedních trhů na aspoň TOP 10
    if len(adlib) < AD_MIN:
        for cc in AD_FOREIGN:
            if len(adlib) >= AD_MIN:
                break
            print(f"  jen {len(adlib)} konkrétních CZ reklam → doplňuji z {cc}…")
            for m in (provider.ad_library(a.tema, cc, VCAPS["ads"]) or []):
                if m.get("page_name") in seen:
                    continue
                m["_geo"] = "global"
                adlib.append(m); seen.add(m.get("page_name"))
                if len(adlib) >= VCAPS["ads"]:
                    break
    # 2) VIDEO díra = největší příležitost: když CZ konkurence nejede VIDEO, dotáhni
    #    nejúspěšnější zahraniční VIDEOreklamy jako inspiraci (video má obří dopad)
    cz_video = sum(1 for r in adlib if r.get("video_url") and r.get("_geo") != "global")
    if cz_video < AD_VIDEO_MIN:
        print(f"  CZ videoreklam jen {cz_video} → dotahuji zahraniční video inspiraci…")
        got_v = 0
        for cc in AD_FOREIGN:
            if got_v >= AD_VIDEO_MIN:
                break
            for m in (provider.ad_library(a.tema, cc, VCAPS["ads"]) or []):
                if not m.get("video_url") or m.get("page_name") in seen:
                    continue
                m["_geo"] = "global"; m["_video_inspo"] = True
                adlib.append(m); seen.add(m.get("page_name")); got_v += 1
                if got_v >= AD_VIDEO_MIN:
                    break
    print("Fetch: organika (keyword search napříč sítěmi)…")
    viral = []
    for net in platforms:
        # LOKÁLNÍ obsah má PŘEDNOST: český dotaz s geo-cílením na trh (proxyCountryCode)
        got = provider.content_search(a.tema, net, since=a.since, cap=VCAPS["per_platform"], market=a.market) or []
        # EN jen jako DOPLNĚK, když je lokálního obsahu málo (hodně se odfiltruje jako cizojazyčný šum).
        # EN dotaz jede GLOBÁLNĚ (market=None); český obsah zůstává první (build řadí geo != cz).
        if a.en and len(got) < VCAPS["per_platform"]:
            seen = {x.get("url") for x in got}
            for x in (provider.content_search(a.en, net, since=a.since, cap=VCAPS["per_platform"], market=None) or []):
                if x.get("url") in seen:
                    continue
                got.append(x); seen.add(x.get("url"))
                if len(got) >= VCAPS["per_platform"]:
                    break
        got = got[:VCAPS["per_platform"]]
        print(f"  {net}: {len(got)}{' (+EN)' if a.en else ''}")
        viral += got
    print("Fetch: vyhledávání (úhly)…")
    search = provider.search_results(a.tema, a.market)
    if provider.apify_limit_hit():
        print("\n🛑 APIFY KREDIT / MĚSÍČNÍ LIMIT VYČERPÁN — TOHLE NENÍ TECHNICKÁ CHYBA SKILLU.")
        print("   Apify účet překročil měsíční limit útraty (HTTP 403 „usage hard limit“).")
        print("   Řešení: • navyš Apify plán (odstraní strop), nebo • počkej na reset měsíčního cyklu.")
        if not adlib and not viral:
            print("   Nestáhla se žádná data → board se negeneruje. Doplň kredit a spusť znovu.")
            return
        print("   (Část dat se stáhla ještě před limitem — pokračuji s tím, co je.)")
    fetched = {"ads": _ads_for_build(adlib), "viral": _viral_for_build(viral),
               "search": _search_for_build(search)}
    _save(rd, "fetched.json", fetched)
    own = None
    ow_path = os.path.join(rd, "own-winners.json")
    if os.path.isfile(ow_path):
        try:
            own = json.load(open(ow_path))
        except Exception:
            own = None
    contract = adboard_build.build(fetched, a.tema, a.market, own_winners=own, assets_dir=rd)
    contract["meta"]["sken"] = today()
    if not a.no_comments:
        print("Fetch: komentáře pod top organikou (jazyk zákazníka)…")
        ncom = _fetch_comments(contract.get("viralni"), rd)
        print(f"  → comments.json ({ncom} komentářů)")
    _save(rd, "rich-contract.json", contract)
    pk = contract.get("pokryti", {})
    print(f"KOSTRA → {rd}/rich-contract.json  (reklam {pk.get('reklamy_relevantni', 0)}, "
          f"organika {pk.get('viralni_kusu', 0)}: {pk.get('short', 0)} krátký / {pk.get('long', 0)} dlouhý)")
    print("STOP — TEĎ DOPLNÍ MODEL (viz references/viral-ad-board.md „Co plní MODEL“):")
    print("  • překlad nm/orig · úhel · fáze povědomí · 3× why · mapa_uhlu · synteza · hooky")
    print("  • search_uhly (úhly ve vyhledávání) · jazyk_zakaznika — DESTILUJ z comments.json (námitky/touhy/fráze)")
    print(f'  Pak: viral-render "{a.tema}"')


def cmd_viral_render(a):
    rd = latest_today_kw(a.tema) or os.path.join(RUNS_KW, slugify(a.tema), today())
    cpath = os.path.join(rd, "rich-contract.json")
    if not os.path.isfile(cpath):
        print("Chybí rich-contract.json — nejdřív viral-fetch.")
        return
    contract = json.load(open(cpath))
    try:
        import adboard
        out = adboard.render(contract, os.path.join(rd, "viral-ad-board.html"))
        print(f"Viral Ad Board → {out}")
    except Exception as e:
        print(f"[adboard] render selhal: {type(e).__name__}: {e}")


# ---- Search Ad Board (osa = klíčové slovo; taktika placeného Google Search) ----
# 🛑 HRANICE: Viral = CO konkurence říká (úhly) · Search = ZA CO platí, kolik a jak ji přebít.

# Capy + odhad ceny (USD; ceny actorů ověřeny v Apify Store 2026-07-13)
SCAPS = {"serp_queries": 8,      # hlavní slovo + související dotazy (jeden SERP běh s paid add-onem)
         "probe_queries": 12,    # max ověřovacích dotazů na search-probe
         "portfolio_top": 3,     # kolika top bidderům stáhnout portfolio z registru
         "portfolio_ads": 30,    # max reklam/inzerent z registru
         "kw_metrics": 60}       # max keyword variant s metrikami
SEST = {"serp_q": 0.0095,        # SERP stránka $0,0025 + paid add-on $0,005 + AIO/start rezerva
        "tp_start": 0.01, "tp_ad": 0.001,   # registr reklam (Transparency)
        "kw": 0.002}             # keyword metrika za slovo


def latest_today_search(tema):
    d = os.path.join(RUNS_KW, slugify(tema), today())
    return d if os.path.isfile(os.path.join(d, "search-report.json")) else None


def _search_cost(n_queries, portfolio_top=SCAPS["portfolio_top"], kw=SCAPS["kw_metrics"]):
    serp = n_queries * SEST["serp_q"]
    tp = portfolio_top * (SEST["tp_start"] + SCAPS["portfolio_ads"] * SEST["tp_ad"])
    kwc = kw * SEST["kw"]
    return serp, tp, kwc


def _rebuild_search_contract(rd, tema, market, client_domain=None, client_name=None):
    """(Re)build kostry z fetched.json + probes.json. Zachová sémantiku, kterou už model
    doplnil do search-report.json (klony, landing, plán…), pokud existuje."""
    fetched = json.load(open(os.path.join(rd, "fetched.json")))
    probes = []
    ppath = os.path.join(rd, "probes.json")
    if os.path.isfile(ppath):
        try:
            probes = json.load(open(ppath))
        except Exception:
            probes = []
    contract = searchboard_build.build(fetched, tema, market, client_domain=client_domain,
                                       client_name=client_name, probes=probes)
    # merge: modelem doplněná sémantika z předchozí verze kontraktu přežije rebuild
    old_path = os.path.join(rd, "search-report.json")
    if os.path.isfile(old_path):
        try:
            old = json.load(open(old_path))
            for key in ("cloneable_ads", "landing_gaps", "landing_pointa", "budget_semafor",
                        "action_plan", "akce"):
                if old.get(key):
                    contract[key] = old[key]
            if (old.get("meta") or {}).get("podtitulek"):
                contract["meta"]["podtitulek"] = old["meta"]["podtitulek"]
            # ruční poznámky u bidderů/mezery (proc_nebezpecny, zamer, pozn) — merge podle klíče
            old_bid = {b.get("domain"): b for b in old.get("bidders") or []}
            for b in contract.get("bidders") or []:
                ob = old_bid.get(b.get("domain"))
                if ob and ob.get("proc_nebezpecny"):
                    b["proc_nebezpecny"] = ob["proc_nebezpecny"]
            old_gap = {g.get("kw"): g for g in old.get("keyword_gap") or []}
            for g in contract.get("keyword_gap") or []:
                og = old_gap.get(g.get("kw"))
                if og:
                    g["zamer"] = og.get("zamer") or g.get("zamer")
                    g["pozn"] = og.get("pozn") or g.get("pozn")
                    g["semafor"] = og.get("semafor") or g.get("semafor")
        except Exception:
            pass
    _save(rd, "search-report.json", contract)
    return contract


def cmd_search_fetch(a):
    extra = [k.strip() for k in (a.keywords or "").replace(",", ";").split(";") if k.strip()]
    n_serp = min(1 + len(extra) + 5, SCAPS["serp_queries"])  # slovo + extra + ~5 souvisejících
    if a.dry_run:
        serp, tp, kwc = _search_cost(n_serp)
        total = serp + tp + kwc
        print("DRY-RUN — 0 útraty. Odhad ostrého běhu Search Ad Boardu:")
        print(f"  Placený blok vyhledávání     ~${serp:.3f}  ({n_serp} dotazů vč. souvisejících, paid add-on)")
        print(f"  Registr reklam (portfolia)   ~${tp:.3f}  (top {SCAPS['portfolio_top']} inzerenti × {SCAPS['portfolio_ads']} reklam)")
        print(f"  Keyword metriky (objem/CPC)  ~${kwc:.3f}  (cap {SCAPS['kw_metrics']} slov)")
        print(f"  ── celkem                    ~${total:.2f} za jedno slovo (+ probe ~${SCAPS['probe_queries'] * SEST['serp_q']:.2f} volitelně)")
        print("STOP — potvrď, než pustíš ostrý search-fetch (bez --dry-run).")
        return
    if not a.refresh and latest_today_search(a.tema):
        print(f"Cache: dnešní běh existuje ({latest_today_search(a.tema)}). Uprav search-report.json + search-render, nebo --refresh.")
        return
    if not provider.has_key():
        print("Bez APIFY_API_KEY — placené zdroje přeskočeny. Search Ad Board bez živého SERPu nedává smysl — doplň klíč.")
        return
    rd = run_dir_kw(a.tema)

    # 1) související dotazy z NORMÁLNÍHO (levného) běhu — paid add-on je nevrací
    #    (ověřeno naostro: focusOnPaidAds → organika/related prázdné)
    print("Fetch: související dotazy + organika (hlavní slovo)…")
    base = provider.search_results(a.tema, a.market) or {}
    queries = [a.tema] + extra
    seen_q = {q.strip().lower() for q in queries}
    for q in (base.get("related") or []):
        ql = (q or "").strip().lower()
        if ql and ql not in seen_q and len(queries) < SCAPS["serp_queries"]:
            queries.append(q)
            seen_q.add(ql)
    # 2) placený blok pro všechny dotazy (kdo bidduje + copy + hustota)
    print(f"Fetch: placený blok vyhledávání ({len(queries)} dotazů)…")
    serp = provider.search_ads(queries, a.market) or []

    # 3) top bidders → portfolio z veřejného registru reklam (kdo je „prověřený trhem")
    bidders = searchboard_build._collect_bidders(serp, a.client_domain)
    top = [b["domain"] for b in bidders if not b["is_client"]][:SCAPS["portfolio_top"]]
    portfolio = {}
    for dom in top:
        print(f"Fetch: registr reklam — {dom}…")
        ads = provider.advertiser_ads(dom, a.market.upper(), SCAPS["portfolio_ads"])
        if ads:
            portfolio[dom] = ads
    # 4) keyword metriky (objem/CPC) — podklad mezery + semaforu
    keywords = None
    if not a.no_metrics:
        print("Fetch: keyword metriky (objem/CPC odhad)…")
        keywords = provider.keyword_metrics(a.tema, a.market, SCAPS["kw_metrics"])
    if provider.apify_limit_hit():
        print("\n🛑 APIFY KREDIT / MĚSÍČNÍ LIMIT VYČERPÁN — není to chyba skillu (viz viral-fetch).")
        if not serp:
            print("   Nestáhl se žádný SERP → board se negeneruje. Doplň kredit a spusť znovu.")
            return
    fetched = {"serp": serp, "portfolio": portfolio, "keywords": keywords or [],
               "main_organic": base.get("organic") or [], "main_ai_overview": base.get("ai_overview")}
    _save(rd, "fetched.json", fetched)
    contract = _rebuild_search_contract(rd, a.tema, a.market, a.client_domain, a.client_name)
    # 5) dohled hledanosti: slova mezery, která expanzní actor nezná → bulk objemy per slovo
    #    (bez toho má půlka mezery „–“ a tabulka vypadá hůř než SEO nástroj)
    missing = [g["kw"] for g in contract.get("keyword_gap") or [] if not g.get("volume")]
    if missing:
        print(f"Fetch: dohled objemů pro {len(missing)} slov mezery (bulk)…")
        vols = provider.keyword_volumes(missing, a.market) or {}
        if vols:
            fetched["keywords"] = (fetched.get("keywords") or []) + list(vols.values())
            _save(rd, "fetched.json", fetched)
            contract = _rebuild_search_contract(rd, a.tema, a.market, a.client_domain, a.client_name)
    pk = contract.get("pokryti", {})
    print(f"KOSTRA → {rd}/search-report.json  (dotazů {pk.get('dotazu')}, inzerentů {pk.get('inzerentu')}, "
          f"portfolia {pk.get('portfolio_inzerentu')}, metrik {pk.get('kw_metrik')})")
    print("STOP — TEĎ DOPLNÍ MODEL (viz references/search-ad-board.md „Co plní MODEL“):")
    print("  • proc_nebezpecny (top 3) · klony reklam (sekce 2) · mezera: vygeneruj kandidáty →")
    print(f'    search-probe "{a.tema}" --queries "slovo1;slovo2;…"  (ověří hustotu v živém SERPu)')
    print("  • landing_gaps (WebFetch stránek top 3) · budget_semafor + benchmark · action_plan (3 kroky)")
    print(f'  Pak: search-render "{a.tema}"')


def cmd_search_probe(a):
    queries = [q.strip() for q in (a.queries or "").replace(",", ";").split(";") if q.strip()]
    queries = queries[:SCAPS["probe_queries"]]
    if not queries:
        print("Zadej --queries \"slovo1;slovo2;…\" (kandidáti mezery vygenerovaní modelem).")
        return
    if a.dry_run:
        print(f"DRY-RUN — 0 útraty. Probe {len(queries)} dotazů ≈ ${len(queries) * SEST['serp_q']:.2f}.")
        print("STOP — potvrď, než pustíš ostrý search-probe (bez --dry-run).")
        return
    rd = latest_today_search(a.tema)
    if not rd:
        print("Chybí dnešní search-fetch běh — nejdřív search-fetch.")
        return
    if not provider.has_key():
        print("Bez APIFY_API_KEY nelze ověřit hustotu.")
        return
    print(f"Probe: {len(queries)} dotazů (hustota inzerentů v živém SERPu)…")
    got = provider.search_ads(queries, a.market) or []
    ppath = os.path.join(rd, "probes.json")
    probes = []
    if os.path.isfile(ppath):
        try:
            probes = json.load(open(ppath))
        except Exception:
            probes = []
    seen = {p.get("query", "").strip().lower() for p in probes}
    probes += [g for g in got if g.get("query", "").strip().lower() not in seen]
    _save(rd, "probes.json", probes)
    # rebuild kostry (mezera se přepočítá z probe hustoty; sémantika modelu přežije)
    raw = json.load(open(os.path.join(rd, "search-report.json")))
    meta = raw.get("meta") or {}
    contract = _rebuild_search_contract(rd, a.tema, a.market,
                                        (meta.get("klient") or {}).get("domain"),
                                        (meta.get("klient") or {}).get("nazev"))
    gap = contract.get("keyword_gap") or []
    print(f"Probes → {ppath} ({len(probes)} dotazů). Mezera teď: {len(gap)} slov s 0–2 inzerenty.")
    for g in gap:
        print(f"  🟢 {g['kw']}  ({g['inzerentu']} inz.{', ~' + str(g['volume']) + '/měs' if g.get('volume') else ''})")


def cmd_search_render(a):
    rd = latest_today_search(a.tema) or os.path.join(RUNS_KW, slugify(a.tema), today())
    cpath = os.path.join(rd, "search-report.json")
    if not os.path.isfile(cpath):
        print("Chybí search-report.json — nejdřív search-fetch.")
        return
    contract = json.load(open(cpath))
    try:
        import searchboard
        out = searchboard.render(contract, os.path.join(rd, "search-ad-board.html"))
        print(f"Search Ad Board → {out}")
    except Exception as e:
        print(f"[searchboard] render selhal: {type(e).__name__}: {e}")


# ---- Competitor Ad Board (osa = ZNAČKA, vstup = doména konkurenta) ----------

RUNS_COMP = os.environ.get("AD_SCOUT_RUNS_COMP", "/documents/ads/scout/competitors")
# Capy + odhad (USD): Meta per-page ~$0.005 start + $0.0005/ad; Google Transparency
# ~$0.01 start + $0.001/ad; landing + pixel-router + sitemap ZDARMA; SERP ~$0.003.
CCAPS = {"meta": 100, "google": 50}
CEST = {"meta": 0.055, "google": 0.06, "serp": 0.003}  # ~$0.12 / konkurent (základní běh)


def run_dir_comp(domena, date=None):
    d = os.path.join(RUNS_COMP, slugify(domena), date or today())
    os.makedirs(d, exist_ok=True)
    return d


def latest_today_comp(domena):
    d = os.path.join(RUNS_COMP, slugify(domena), today())
    return d if os.path.isfile(os.path.join(d, "raw.json")) else None


def _norm_brand(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _filter_brand_pages(ads, brand, domena):
    """Nech jen reklamy STRÁNKY konkurenta — actory občas přibalí cizí stránky (affiliate/
    influencer reklamy zmiňující značku, např. slevové kódy). Match: normalizovaná značka ⊆
    page_name nebo obráceně; fallback = dominantní stránka v datech."""
    if not ads:
        return ads
    zn = _norm_brand(brand) or _norm_brand((domena or "").split(".")[0])
    keep = [a for a in ads if zn and (zn in _norm_brand(a.get("page_name")) or _norm_brand(a.get("page_name")) in zn)]
    if len(keep) >= max(3, len(ads) // 2):
        dropped = len(ads) - len(keep)
        if dropped:
            print(f"  filtr stránky: {dropped} reklam cizích stránek vyřazeno (affiliate/šum)")
        return keep
    # fallback: dominantní stránka
    cnt = {}
    for a in ads:
        cnt[a.get("page_name")] = cnt.get(a.get("page_name"), 0) + 1
    dom_page = max(cnt, key=cnt.get)
    keep = [a for a in ads if a.get("page_name") == dom_page]
    if len(keep) < len(ads):
        print(f"  filtr stránky: držím dominantní stránku „{dom_page}“ ({len(keep)}/{len(ads)})")
    return keep


def _find_fb_page(domena, znacka, market):
    """FB stránka konkurenta: 1) zdarma z jeho webu (landing_pixels → social.facebook),
    2) fallback z výsledků vyhledávání („<značka> facebook")."""
    lp = provider.landing_pixels(domena)
    fb = (lp or {}).get("social", {}).get("facebook")
    if fb:
        return fb, lp
    s = provider.search_results(f"{znacka or domena} facebook", market)
    for o in (s or {}).get("organic", []):
        u = o.get("url") or ""
        if "facebook.com/" in u and "/ads/" not in u:
            return u.split("?")[0], lp
    return None, lp


def cmd_comp_fetch(a):
    if a.dry_run:
        total = sum(CEST.values())
        print("DRY-RUN — 0 útraty. Odhad ostrého běhu Competitor Ad Boardu (základní):")
        print(f"  Knihovna reklam Meta (per stránka)  ~${CEST['meta']:.3f}  (cap {CCAPS['meta']} reklam)")
        print(f"  Registr transparentnosti Google     ~${CEST['google']:.3f}  (cap {CCAPS['google']}, vstup = doména)")
        print(f"  Vyhledávání (kontext)               ~${CEST['serp']:.3f}")
        print("  Landing + pixel-router + sitemap    zdarma")
        print(f"  ── celkem                           ~${total:.2f} za jednoho konkurenta")
        print("STOP — potvrď, než pustíš ostrý comp-fetch (bez --dry-run).")
        return
    if not a.refresh and latest_today_comp(a.domena):
        print(f"Cache: dnešní běh existuje ({latest_today_comp(a.domena)}). Uprav contract + comp-render, nebo --refresh.")
        return
    if not provider.has_key():
        print("Bez APIFY_API_KEY — placené zdroje přeskočeny. Jedou jen volné (landing/pixely/sitemap/registry deep-linky).")

    rd = run_dir_comp(a.domena)
    print("Krok 0 (zdarma): landing + pixel-router + FB stránka…")
    fb_page, landing = _find_fb_page(a.domena, a.brand, a.market)
    print(f"  pixely: {', '.join((landing or {}).get('pixels') or []) or 'nenalezeny'}")
    print(f"  FB stránka: {fb_page or 'nenalezena (Meta modul pojede přes hledání značky)'}")
    print("Krok 0 (zdarma): sitemap → skryté landing pages…")
    sitemap = provider.sitemap_lps(a.domena) or []
    print(f"  kampaňové LP: {len(sitemap)}")

    meta_ads = None
    if provider.has_key():
        print(f"Fetch: knihovna reklam Meta (stránka konkurenta, cap {CCAPS['meta']})…")
        if fb_page:
            meta_ads = provider.page_ads(fb_page, a.market.upper(), CCAPS["meta"])
        if not meta_ads and (a.brand or a.domena):
            # fallback: hledání značky jménem + filtr na stránku konkurenta
            print("  page-ads prázdno → fallback hledání značky v knihovně…")
            zn = (a.brand or a.domena.split(".")[0])
            found = provider.ad_library(zn, a.market.upper(), CCAPS["meta"]) or []
            znl = zn.lower().replace(" ", "")
            meta_ads = [m for m in found if znl in (m.get("page_name") or "").lower().replace(" ", "")] or None
        meta_ads = _filter_brand_pages(meta_ads, a.brand, a.domena)
        print(f"  reklam Meta: {len(meta_ads or [])}")
        print(f"Fetch: registr transparentnosti Google (doména, cap {CCAPS['google']})…")
        google_ads = provider.transparency_ads(a.domena, a.market.upper(), CCAPS["google"], brand=a.brand)
        print(f"  reklam Google/YouTube: {len(google_ads or [])}")
        print("Fetch: vyhledávání (kontext)…")
        serp = provider.search_results(a.brand or a.domena, a.market)
    else:
        google_ads, serp = None, None

    if provider.apify_limit_hit():
        print("\n🛑 APIFY KREDIT / MĚSÍČNÍ LIMIT VYČERPÁN — není to chyba skillu (viz viral-fetch hláška).")

    raw = {"konkurent": {"znacka": a.brand, "domena": a.domena}, "market": a.market,
           "fetched_at": today(), "fb_page": fb_page,
           "landing": landing, "sitemap": sitemap,
           "meta_ads": meta_ads, "google_ads": google_ads, "serp": serp,
           "klient": {"domena": a.client_domain} if a.client_domain else {}}
    _save(rd, "raw.json", raw)

    import compboard_build
    contract = compboard_build.build(
        {"meta_ads": meta_ads or [], "google_ads": google_ads or [], "landing": landing or {},
         "serp": serp or {}, "sitemap": sitemap},
        {"znacka": a.brand, "domena": a.domena}, a.market,
        klient=raw["klient"], assets_dir=rd)
    contract["meta"]["sken"] = today()
    _save(rd, "competitor-contract.json", contract)
    st = contract["stat"]
    print(f"KOSTRA → {rd}/competitor-contract.json  (Meta {st['meta_reklam']}, Google {st['google_reklam']}, "
          f"konceptů {st['konceptu']}, vítězů {len(contract['vitezove'])})")
    print("STOP — TEĎ DOPLNÍ MODEL (viz references/competitor-ad-board.md „Co plní MODEL“):")
    print("  • vitezove: nm česky + orig · uhel · aw · typ (výkonová/image/nábor) · 3× why · klon")
    print("  • mapa_utoku (úhly × fáze, počty, prilezitosti) · utocny_plan (3 tahy s handoff textem)")
    print("  • stat.uhly_volne · meta.podtitulek (volitelně)")
    print(f'  Pak: comp-render "{a.domena}"')


def cmd_comp_build(a):
    """Přestaví competitor-contract.json z cache (raw.json) BEZ re-fetche (0 kreditů).
    Použij po úpravě filtrů/buildu — thumbnaily se berou z cache."""
    rd = latest_today_comp(a.domena)
    if not rd:
        print("Chybí dnešní raw.json — nejdřív comp-fetch.")
        return
    raw = json.load(open(os.path.join(rd, "raw.json")))
    meta_ads = _filter_brand_pages(raw.get("meta_ads"), a.brand or (raw.get("konkurent") or {}).get("znacka"),
                                   a.domena)
    import compboard_build
    contract = compboard_build.build(
        {"meta_ads": meta_ads or [],
         "google_ads": provider.filter_gt_advertisers(raw.get("google_ads") or [],
                                                      brand=a.brand or (raw.get("konkurent") or {}).get("znacka"),
                                                      domain=a.domena),
         "landing": raw.get("landing") or {}, "serp": raw.get("serp") or {},
         "sitemap": raw.get("sitemap") or []},
        raw.get("konkurent") or {"domena": a.domena}, raw.get("market", "cz"),
        klient=raw.get("klient") or {}, assets_dir=rd)
    contract["meta"]["sken"] = today()
    _save(rd, "competitor-contract.json", contract)
    st = contract["stat"]
    print(f"KOSTRA (rebuild z cache) → {rd}/competitor-contract.json  "
          f"(Meta {st['meta_reklam']}, Google {st['google_reklam']}, konceptů {st['konceptu']}, vítězů {len(contract['vitezove'])})")


def cmd_comp_render(a):
    rd = latest_today_comp(a.domena) or os.path.join(RUNS_COMP, slugify(a.domena), today())
    cpath = os.path.join(rd, "competitor-contract.json")
    if not os.path.isfile(cpath):
        print("Chybí competitor-contract.json — nejdřív comp-fetch.")
        return
    contract = json.load(open(cpath))
    try:
        import adboard
        out = adboard.render_competitor(contract, os.path.join(rd, "competitor-ad-board.html"))
        print(f"Competitor Ad Board → {out}")
    except Exception as e:
        print(f"[adboard] render selhal: {type(e).__name__}: {e}")


# ---- Viral DNA Card™ (osa = JEDEN donor: URL reklamy nebo obsahu) -----------
# Hloubkový rozbor jednoho vítěze → klon-šablona pro makery (Ad DNA Method™,
# krok Dekóduj-hloubka). Standalone režim (B): URL → karta. Kondenzát (A) se
# předpočítává v adboard_build (dna_kondenzat). Spec: references/viral-dna-card.md.

RUNS_DNA = os.environ.get("AD_SCOUT_RUNS_DNA", "/documents/ads/scout/dna")
DNA_CMT_CAP = 60   # max komentářů donora (Raw Diet karty; levné — jen text)
# odhady (USD, BRONZE tier — ceny actorů ověřeny v Apify Store 2026-07-13)
DNAEST = {"donor": 0.010, "video": 0.010, "tr_min": 0.045, "comments": DNA_CMT_CAP * 0.00125}


def dna_slug(url):
    """Stabilní slug donora z URL: síť + ID kusu (tiktok-755663…, youtube-IbLIyA6AlS4)."""
    net = provider.donor_net(url) or "donor"
    m = (re.search(r"/(?:video|photo)/(\d+)", url) or re.search(r"[?&]v=([\w-]{6,})", url)
         or re.search(r"youtu\.be/([\w-]{6,})", url) or re.search(r"/shorts/([\w-]{6,})", url)
         or re.search(r"/(?:reel|reels|p)/([\w-]{5,})", url) or re.search(r"[?&]id=(\d+)", url))
    tail = m.group(1) if m else slugify(url.split("://")[-1])[-24:]
    return f"{net}-{tail}"[:50]


def run_dir_dna(url, date=None):
    d = os.path.join(RUNS_DNA, dna_slug(url), date or today())
    os.makedirs(d, exist_ok=True)
    return d


def latest_today_dna(url):
    d = os.path.join(RUNS_DNA, dna_slug(url), today())
    return d if os.path.isfile(os.path.join(d, "dna-card.json")) else None


def cmd_dna_fetch(a):
    net = provider.donor_net(a.url)
    if not net:
        print("Neznámá síť — podporované URL: TikTok, YouTube, Instagram, Facebook, Meta Ad Library.")
        return
    is_short_net = net in ("tiktok", "instagram")
    want_frames = is_short_net and not a.no_frames          # krátké = framy + vision (spec §6)
    want_tr = not a.no_transcript and net in ("tiktok", "youtube")
    if a.dry_run:
        rows = [("Meta donora (1 kus)", DNAEST["donor"])]
        if want_frames:
            rows.append(("Video ke snímkům (framy = ffmpeg zdarma)", DNAEST["video"]))
        if want_tr:
            rows.append(("Přepis (YouTube titulky ~zdarma / krátké video ~$0,045 za započatou min)",
                         0.005 if net == "youtube" else DNAEST["tr_min"] * 2))
        if not a.no_comments and net != "adlib":
            rows.append((f"Komentáře publika (cap {DNA_CMT_CAP})", DNAEST["comments"]))
        total = sum(c for _, c in rows)
        print(f"DRY-RUN — 0 útraty. Odhad ostrého běhu Viral DNA Card ({net}):")
        for lbl, c in rows:
            print(f"  {lbl:<62} ~${c:.3f}")
        print(f"  ── celkem                                                      ~${total:.2f} za jednu kartu")
        print("STOP — potvrď, než pustíš ostrý dna-fetch (bez --dry-run).")
        return
    if not a.refresh and latest_today_dna(a.url):
        print(f"Cache: dnešní běh existuje ({latest_today_dna(a.url)}). Uprav dna-card.json + dna-render, nebo --refresh.")
        return
    if not provider.has_key():
        print("Bez APIFY_API_KEY nelze donora stáhnout (scraping jede výhradně přes proxy providera).")
        return
    rd = run_dir_dna(a.url)
    print(f"Fetch: meta donora ({net})…")
    donor = provider.donor_meta(a.url, want_video=want_frames, want_transcript=want_tr)
    if not donor or (net == "adlib" and not donor.get("ad")):
        if provider.apify_limit_hit():
            print("🛑 APIFY KREDIT / MĚSÍČNÍ LIMIT VYČERPÁN — není to chyba skillu (viz viral-fetch hláška).")
        else:
            print("Donora se nepodařilo stáhnout (všechny actory prázdné). Zkontroluj URL, případně --refresh později.")
        return
    _save(rd, "donor-raw.json", donor.pop("_raw", None) or {})

    # framy (krátký formát): video přes provider/proxy → lokální ffmpeg (zdarma)
    frames = []
    if want_frames and donor.get("video_url"):
        print("Fetch: video pro snímky (jen k rozboru, nerehostuje se)…")
        vp = adboard_build.dl_thumb(donor["video_url"], os.path.join(rd, "video.mp4"))
        if vp:
            frames = dnacard_build.extract_frames(vp, os.path.join(rd, "frames"))
            print(f"  framů: {len(frames)}")
        else:
            print("  video se nepodařilo stáhnout → vizuální DNA jen z náhledu")

    # přepis: donor fetch ho často nese (YT titulky / TikTok transkripce); fallback specialista
    tr = donor.get("transcript")
    if want_tr and not tr and net == "youtube":
        print("Fetch: přepis (záložní zdroj)…")
        tr = provider.donor_transcript(a.url)
    print(f"  přepis: {'ano (' + str(len(tr)) + ' znaků)' if tr else 'není k dispozici'}")

    # komentáře (Raw Diet karty) — bez jmen (GDPR, strhává provider)
    comments = None
    if not a.no_comments and net != "adlib":
        print("Fetch: komentáře publika…")
        comments = provider.content_comments([a.url], net, cap=DNA_CMT_CAP)
        print(f"  komentářů: {len(comments or [])}")
        _save(rd, "comments.json", comments or [])

    contract = dnacard_build.build(donor, tema=a.tema, trh=a.market, comments=comments,
                                   transcript=tr, frames_paths=frames, run_dir=rd)
    if net == "adlib":
        contract["publikum"]["poznamka"] = ("Veřejná knihovna reklam komentáře neposkytuje — "
                                            "jazyk publika čerpejte z organiky na stejné téma.")
    elif not comments:
        contract["publikum"]["poznamka"] = ("Komentáře se nepodařilo stáhnout (nebo jich donor má málo) — "
                                            "vrstva se doplní při dalším běhu.")
    _save(rd, "dna-card.json", contract)
    d = contract["donor"]
    print(f"KOSTRA → {rd}/dna-card.json  (typ {d.get('typ')}, formát {d.get('format')}, "
          f"přepis {contract['prepis']['stav']}, komentářů {contract['publikum']['zdroj_pocet']}, framů {len(frames)})")
    print("STOP — TEĎ DOPLNÍ MODEL (viz references/viral-dna-card.md „Co plní MODEL“):")
    print("  • donor.nm česky + orig · proc_donor · vizualni_dna (VISION: prohlédni thumb + frames!)")
    print("  • textova_dna (hook·úhel+povědomí·formát·nabídka) + kostra (z přepisu, jinak odhad)")
    print("  • prepis.hook_3s · publikum (destilát z _surovina.komentare, česky) · klon (V/H/U/F)")
    print(f'  Pak: dna-render "{a.url}"')


def cmd_dna_render(a):
    rd = latest_today_dna(a.url)
    if not rd:  # fallback: poslední existující běh (karta se needituje jen v den fetche)
        base = os.path.join(RUNS_DNA, dna_slug(a.url))
        days = sorted(os.listdir(base))[::-1] if os.path.isdir(base) else []
        rd = next((os.path.join(base, d) for d in days
                   if os.path.isfile(os.path.join(base, d, "dna-card.json"))), None)
    if not rd:
        print("Chybí dna-card.json — nejdřív dna-fetch.")
        return
    card = json.load(open(os.path.join(rd, "dna-card.json")))
    try:
        import dnacard
        out = dnacard.render(card, os.path.join(rd, "viral-dna-card.html"))
        print(f"Viral DNA Card → {out}")
    except Exception as e:
        print(f"[dnacard] render selhal: {type(e).__name__}: {e}")


def _save(d, name, obj):
    with open(os.path.join(d, name), "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser(prog="ad-scout")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("product")
    f.add_argument("--market", default="cz")
    f.add_argument("--client-domain", default=None)
    f.add_argument("--dry-run", action="store_true")
    f.add_argument("--refresh", action="store_true")
    f.set_defaults(func=cmd_fetch)
    b = sub.add_parser("build")
    b.add_argument("product")
    b.add_argument("--board", action="store_true")
    b.set_defaults(func=cmd_build)
    vf = sub.add_parser("viral-fetch")
    vf.add_argument("tema")
    vf.add_argument("--market", default="cz")
    vf.add_argument("--b2b", action="store_true", help="přidá LinkedIn (dlouhý obsah, B2B úhly)")
    vf.add_argument("--since", default=None, help="volitelná pojistka stáří (např. '18 months'); default bez limitu")
    vf.add_argument("--en", default=None, help="anglický překlad tématu — doplní organiku, když je českých výsledků málo (např. --en creatine)")
    vf.add_argument("--dry-run", action="store_true")
    vf.add_argument("--refresh", action="store_true")
    vf.add_argument("--no-comments", action="store_true", help="přeskoč sběr komentářů (jazyk zákazníka) — ušetří kredity")
    vf.set_defaults(func=cmd_viral_fetch)
    vr = sub.add_parser("viral-render")
    vr.add_argument("tema")
    vr.set_defaults(func=cmd_viral_render)
    sf = sub.add_parser("search-fetch")
    sf.add_argument("tema")
    sf.add_argument("--market", default="cz")
    sf.add_argument("--client-domain", default=None)
    sf.add_argument("--client-name", default=None)
    sf.add_argument("--keywords", default=None, help="extra dotazy k hlavnímu slovu (a;b;c)")
    sf.add_argument("--no-metrics", action="store_true", help="přeskoč keyword metriky (ušetří kredity)")
    sf.add_argument("--dry-run", action="store_true")
    sf.add_argument("--refresh", action="store_true")
    sf.set_defaults(func=cmd_search_fetch)
    sp = sub.add_parser("search-probe")
    sp.add_argument("tema")
    sp.add_argument("--queries", default=None, help="kandidáti mezery od modelu (a;b;c), ověří hustotu")
    sp.add_argument("--market", default="cz")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_search_probe)
    sr = sub.add_parser("search-render")
    sr.add_argument("tema")
    sr.set_defaults(func=cmd_search_render)
    cf = sub.add_parser("comp-fetch")
    cf.add_argument("domena", help="doména konkurenta (např. gymbeam.cz)")
    cf.add_argument("--brand", default=None, help="jméno značky konkurenta (jinak z titulku webu)")
    cf.add_argument("--market", default="cz")
    cf.add_argument("--client-domain", default=None, help="doména klienta (kontext útoku)")
    cf.add_argument("--dry-run", action="store_true")
    cf.add_argument("--refresh", action="store_true")
    cf.set_defaults(func=cmd_comp_fetch)
    cb = sub.add_parser("comp-build")
    cb.add_argument("domena")
    cb.add_argument("--brand", default=None)
    cb.set_defaults(func=cmd_comp_build)
    cr = sub.add_parser("comp-render")
    cr.add_argument("domena")
    cr.set_defaults(func=cmd_comp_render)
    df = sub.add_parser("dna-fetch")
    df.add_argument("url", help="URL donora (TikTok/YouTube/IG/FB post, nebo Meta Ad Library deep-link)")
    df.add_argument("--tema", default=None, help="téma/kampaň, ke které donor patří (do hlavičky karty)")
    df.add_argument("--market", default="cz")
    df.add_argument("--no-comments", action="store_true", help="přeskoč komentáře (Raw Diet vrstva)")
    df.add_argument("--no-transcript", action="store_true", help="přeskoč přepis (ušetří u krátkých videí)")
    df.add_argument("--no-frames", action="store_true", help="přeskoč video framy (vizuální DNA jen z náhledu)")
    df.add_argument("--dry-run", action="store_true")
    df.add_argument("--refresh", action="store_true")
    df.set_defaults(func=cmd_dna_fetch)
    dr = sub.add_parser("dna-render")
    dr.add_argument("url", help="URL donora (stejná jako u dna-fetch)")
    dr.set_defaults(func=cmd_dna_render)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
