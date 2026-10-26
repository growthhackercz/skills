#!/usr/bin/env python3
"""Datový provider pro ad-scout (Product Intelligence Board + Viral Ad Board).

Source-agnostický adaptér: skill mluví o obecných zdrojích (ceny/recenze/vyhledávání/
knihovna reklam), NE o konkrétních jménech. Konkrétní aktory jsou jen konfigurovatelné
defaulty (přepiš přes env), aby se název zdroje NIKDY nedostal do výstupu ani do
kódu skillu jako závislost. Klíč z APIFY_API_KEY (nikdy neloguje).

Vzor: run-sync-get-dataset-items (POST input → rovnou dataset items).

🛑 OCHRANA INFRASTRUKTURY: veškerý scraping běží na Apify (jejich IP + proxy
absorbují ToS/ban riziko) — NIKDY přímo z klientského serveru. Aktory dostávají
proxyConfiguration; browser fallback (mimo tenhle wrapper) veď taky přes proxy.

FALLBACK CHAINY (od v0.2): každý zdroj má pořadový seznam kandidátů (primary + fallbacky).
`run_chain` zkouší 1 → 2 → 3, vrátí PRVNÍ neprázdný výsledek a zaloguje, který vyhrál.
Fallback padá jen na error/prázdno (levné — za neúspěšný actor se skoro neplatí); odpad
(cizí jazyk / spam) řeší downstream filtr `_lang_ok`, ne přehazování actorů.

⚠️ KNIHOVNA REKLAM = APIFY TOKEN, NE Meta MCP/token. Na klientském serveru žádný Meta
MCP není a Meta Graph API token nemáme (a GHL napojení ho neposkytuje). Ad Library proto
scrapeme přes Apify actory (běží na APIFY_API_KEY, bez Meta účtu, bez loginu) — univerzální
pro celý fleet. Dotaz VŽDY frázově česky („bojové sporty"), NE holá zkratka („MMA" = 371k
globálního webnovel spamu); + countries=[CZ] drží výstup čistý.

Aktory (env → INTERNÍ, nejdou do klientského výstupu). Env přepíše slug pozice #0 v chainu;
fallbacky #1/#2 jsou defaulty v kódu:
  ADLIB (ads):   brilliant_gum/fb-ads-library → automation-lab/fb-ads-library → apify/facebook-ads-scraper
  SEARCH (SERP): apify/google-search-scraper
  Discovery organiky KEYWORD SEARCH (`content_search`, podle TÉMATU, ne hashtagu/watchlistu):
    YT: streamers/youtube-scraper (searchQueries)   TT: clockworks/tiktok-scraper → apidojo → free-tiktok
    IG: apify/instagram-scraper (native search) → hashtag explore → apify/instagram-api-scraper
    FB: scraper_one → powerai → scrapeforge         LI: harvestapi/linkedin-post-search
    META: seibs.co/meta-content-intel (FB+IG naráz)
  Komentáře k ORGANICE (Raw Diet, voice-of-customer) — vstup = URL postu, veřejné posty bez loginu:
    IG: apify/instagram-comment-scraper → apidojo → louisdeconinck
    FB: apify/facebook-comments-scraper → expected_knight → thedoor
    YT: streamers/youtube-comments-scraper → code-node-tools
    TT: clockworks/tiktok-comments-scraper
  Ceny/recenze (produktový board): cashmere_verdict/heureka-product-scraper, stealth_mode/heureka-reivews-scraper

v0.2 — fallback chainy + Apify ad-library na token + CZ/SK jazykový filtr; YT fix searchQueries.
"""
import datetime
import json
import os
import re
import sys
import unicodedata
import urllib.request
import urllib.parse
import urllib.error

API = "https://api.apify.com/v2"

# Stav běhu: kredit / měsíční limit Apify účtu vyčerpán (403 „usage hard limit") — NENÍ chyba skillu.
_STATE = {"apify_limit": False}
_LIMIT_MARKERS = ("usage hard limit", "monthly usage", "platform-feature-disabled",
                  "usage limit", "hard limit exceeded", "limit exceeded", "not enough", "insufficient")


def apify_limit_hit():
    """True = během fetche padl Apify účet na měsíční kredit/limit (ne technická chyba)."""
    return _STATE["apify_limit"]

PRICE_ACTOR = os.environ.get("AD_SCOUT_PRICE_ACTOR", "cashmere_verdict/heureka-product-scraper")
REVIEWS_ACTOR = os.environ.get("AD_SCOUT_REVIEWS_ACTOR", "stealth_mode/heureka-reivews-scraper")
SEARCH_ACTOR = os.environ.get("AD_SCOUT_SEARCH_ACTOR", "apify/google-search-scraper")
META_LISTEN_ACTOR = os.environ.get("AD_SCOUT_META_LISTEN_ACTOR", "seibs.co/meta-content-intel")


def _cc_variable(name):
    """Control Center proměnné (Nastavení -> Integrace) — store má přednost před env."""
    try:
        import sys as _sys
        _sys.path.insert(0, "/home/node/.openclaw/cs-skills/_lib")
        from cc_credentials import get_variable  # type: ignore
        return (get_variable(name) or "").strip()
    except Exception:
        return ""


def _token():
    return _cc_variable("APIFY_API_KEY") or os.environ.get("APIFY_API_KEY", "").strip() or None


def has_key():
    return _token() is not None


def _api_get(path, timeout=60):
    tok = _token()
    req = urllib.request.Request(f"{API}{path}", headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _api_post(path, payload, timeout=60):
    tok = _token()
    req = urllib.request.Request(f"{API}{path}", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _api_raw(path, timeout=120):
    tok = _token()
    req = urllib.request.Request(f"{API}{path}", headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def run_actor(actor, payload, timeout=180):
    """Spustí aktor synchronně, vrátí dataset items (list). Bez klíče → None."""
    tok = _token()
    if not tok:
        return None
    path = actor.replace("/", "~")
    url = f"{API}/acts/{path}/run-sync-get-dataset-items?token={urllib.parse.quote(tok)}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "ignore")[:400].lower()
        except Exception:
            pass
        if e.code in (402, 403) and any(m in body for m in _LIMIT_MARKERS):
            if not _STATE["apify_limit"]:  # hlas jen jednou, jasně že jde o KREDIT, ne o chybu skillu
                sys.stderr.write("[provider] 🛑 APIFY KREDIT / MĚSÍČNÍ LIMIT VYČERPÁN — NENÍ to chyba skillu "
                                 "(Apify účet překročil měsíční limit). Navyš plán / počkej na reset cyklu.\n")
            _STATE["apify_limit"] = True
        else:
            sys.stderr.write(f"[provider] {actor.split('/')[-1]}: HTTP {e.code}\n")  # nikdy nelogovat token
        return None
    except Exception as e:
        sys.stderr.write(f"[provider] {actor.split('/')[-1]}: {type(e).__name__}\n")
        return None


def run_chain(candidates, ctx, label=""):
    """Fallback chain: zkusí kandidáty (slug, builder) v pořadí; vrátí PRVNÍ neprázdný raw list.
    builder(ctx) → payload pro daný actor (každý actor má vlastní tvar vstupu). Loguje vítěze."""
    for i, (slug, build) in enumerate(candidates):
        if not slug:
            continue
        try:
            payload = build(ctx)
        except Exception:
            continue
        raw = run_actor(slug, payload)
        if raw:
            sys.stderr.write(f"[chain] {label}: #{i} {slug.split('/')[-1]} OK ({len(raw)})\n")
            return raw
        sys.stderr.write(f"[chain] {label}: #{i} {slug.split('/')[-1]} prázdno/chyba → další\n")
    sys.stderr.write(f"[chain] {label}: všechny actory selhaly/prázdné\n")
    return None


def _env0(var, default):
    """Env přepíše slug pozice #0 v chainu (zpětná kompatibilita), jinak default z kódu."""
    return os.environ.get(var, default)


# ---- obecné zdroje (source-agnostic) --------------------------------------

def price_offers(product, market="cz", cap=40, start_url=None):
    """Ceny + nabídky obchodů + dostupnost + varianty na produkt.

    Ověřeno naživo (2026-07-12): `searchKeywords` samo vrací PRÁZDNO i s proxy —
    hledací tok je nespolehlivý. Preferuj `start_url` (URL produktu na srovnávači,
    dohledej ho z výsledků vyhledávání), jinak fallback na browser tool (Chrome).
    proxyConfiguration je POVINNÉ (bez něj blokace)."""
    payload = {"maxItems": cap, "includeOffers": True, "includeSpecs": False,
               "proxyConfiguration": {"useApifyProxy": True}}
    if start_url:
        payload["startUrls"] = [{"url": start_url}]
    else:
        payload["searchKeywords"] = [product]
    return run_actor(PRICE_ACTOR, payload)


def price_reviews(product, market="cz", cap=30):
    """Recenze produktu (strukturované +/−). GDPR: bez jmen autorů."""
    return run_actor(REVIEWS_ACTOR, {"searchKeywords": [product], "max_items_per_url": cap})


def search_results(product, market="cz"):
    """Výsledky vyhledávání: organika + placené + AI přehled. OVĚŘENÝ tvar.

    Pozn. (2026-07-12): u CZ trhu **zakotvi dotaz česky** (přidej kategorii/„cena",
    např. „<produkt> vysavač cena") — čistě anglický název vrátí globální organiku
    (placené zůstanou CZ). Volající by měl anchor doplnit do `product`."""
    items = run_actor(SEARCH_ACTOR, {
        "queries": product, "resultsPerPage": 20, "maxPagesPerQuery": 1,
        "countryCode": market, "languageCode": "cs" if market == "cz" else "en",
        "mobileResults": False,
    })
    if not items:
        return None
    it = items[0]
    return {
        "organic": [{"pos": o.get("position"), "shop": o.get("websiteTitle") or o.get("title"),
                     "url": o.get("url")} for o in it.get("organicResults", [])],
        "paid": it.get("paidResults", []),
        "ai_overview": (it.get("aiOverview") or {}).get("content"),
        "related": [r.get("title") for r in it.get("relatedQueries", [])],
    }


# ---- Knihovna reklam: Apify na token (NE Meta MCP/token) -------------------

_A_PAGE = ("page_name", "pageName", "page", "advertiser", "advertiserName", "brandName", "author")
_A_TITLE = ("ad_creative_link_title", "adCreativeLinkTitle", "title", "headline", "linkTitle")
_A_TEXT = ("ad_creative_body", "adCreativeBody", "body", "text", "adText", "caption",
           "ad_creative_link_description", "linkDescription")
_A_URL = ("ad_snapshot_url", "adSnapshotUrl", "snapshotUrl", "adLibraryUrl", "url", "adUrl", "landingUrl", "linkUrl")
_A_START = ("ad_delivery_start_time", "adDeliveryStartTime", "startDate", "start_time",
            "deliveryStartTime", "startedRunningOn")
_A_DAYS = ("runningDays", "running_days", "days", "totalActiveDays", "activeDays", "daysRunning")
_A_REACH = ("reach", "eu_total_reach", "euTotalReach", "impressions", "totalReach", "audienceSize")
_A_CURR = ("currency", "curr")
_A_PLAT = ("publisher_platforms", "publisherPlatforms", "platforms", "plat")
_A_THUMB = ("thumbnailUrl", "imageUrl", "image_url", "thumbnail", "image", "originalImageUrl",
            "original_image_url", "snapshotImageUrl", "snapshot_image_url", "cover", "creativeImageUrl",
            "mediaUrl", "media_url", "previewImageUrl", "preview_image_url", "cardImageUrl",
            "card_image_url", "videoPreviewImageUrl", "video_preview_image_url", "displayUrl")

_IMG_RE = re.compile(r"https?://[^\s\"']+\.(?:jpg|jpeg|png|webp)(?:\?[^\s\"']*)?", re.I)
_IMG_HINT = ("scontent", "fbcdn", "cdninstagram")


def _find_image_url(obj, depth=0):
    """Heuristika: najde v reklamě obrázkovou URL, ať se pole jmenuje jakkoli (různí vendoři).
    Poslední záchrana, když `_A_THUMB` netrefí přesný klíč. Mělká rekurze."""
    if depth > 3:
        return None
    vals = obj.values() if isinstance(obj, dict) else (obj if isinstance(obj, list) else [])
    for v in vals:
        if isinstance(v, str):
            m = _IMG_RE.search(v)
            if m:
                return m.group(0)
            if v.startswith("http") and any(h in v for h in _IMG_HINT):
                return v
        elif isinstance(v, (dict, list)):
            u = _find_image_url(v, depth + 1)
            if u:
                return u
    return None

_PLAT_UP = {"facebook": "FACEBOOK", "instagram": "INSTAGRAM", "fb": "FACEBOOK", "ig": "INSTAGRAM"}


def _ad_days(item):
    """Dny běhu reklamy: přímé pole, jinak dopočet z data spuštění (epoch/ISO)."""
    for k in _A_DAYS:
        v = item.get(k)
        if isinstance(v, (int, float)) and v >= 0:
            return int(v)
    start = None
    for k in _A_START:
        v = item.get(k)
        if v:
            start = v
            break
    if not start:
        return None
    try:
        if isinstance(start, (int, float)) or str(start).isdigit():
            d0 = datetime.date.fromtimestamp(int(start))
        else:
            d0 = datetime.date.fromisoformat(str(start)[:10])
        return max((datetime.date.today() - d0).days, 0)
    except Exception:
        return None


def _adlib_url(query, country):
    """URL vyhledávání v Meta Ad Library (pro actory, co berou startUrls)."""
    q = urllib.parse.quote(query)
    return (f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
            f"&country={country}&q={q}&search_type=keyword_unordered&media_type=all")


def _first_url(v):
    """První http URL z pole/řetězce."""
    if isinstance(v, list):
        for x in v:
            if isinstance(x, str) and x.startswith("http"):
                return x
    elif isinstance(v, str) and v.startswith("http"):
        return v
    return None


def _ad_media_urls(item):
    """Náhled reklamní KREATIVY (ne logo inzerenta) + URL videa. Napříč tvary actorů:
    automation-lab (`imageUrls`/`videoPreviewUrls`/`videoUrls`) i oficiální apify (`snapshot.images[]`
    / `snapshot.videos[]`). Vrací (thumb=obrázek nebo poster videa, video_url)."""
    snap = item.get("snapshot") if isinstance(item.get("snapshot"), dict) else {}
    img = _first_url(item.get("imageUrls"))
    if not img:
        imgs = snap.get("images") if isinstance(snap.get("images"), list) else []
        if imgs and isinstance(imgs[0], dict):
            img = imgs[0].get("originalImageUrl") or imgs[0].get("resizedImageUrl")
    vprev = _first_url(item.get("videoPreviewUrls"))
    vurl = _first_url(item.get("videoUrls"))
    vids = snap.get("videos") if isinstance(snap.get("videos"), list) else []
    if vids and isinstance(vids[0], dict):
        vprev = vprev or vids[0].get("videoPreviewImageUrl")
        vurl = vurl or vids[0].get("videoSdUrl") or vids[0].get("videoHdUrl")
    return (img or vprev), vurl


def _norm_ad(item):
    """Sjednotí reklamu z libovolného Apify ad-library actoru (různí vendoři = různé klíče)
    na KANONICKÝ tvar s Meta-API názvy klíčů (`page_name`, `ad_creative_body`, …) — přesně ty,
    které downstream consumery (`_ads_for_build`, `_meta` v scout.py) už čtou. Bez page/copy → None."""
    if not isinstance(item, dict):
        return None
    page = _first(item, _A_PAGE)
    title = _first(item, _A_TITLE)
    text = _first(item, _A_TEXT)
    if not page or not (title or text):
        return None
    plats = _first(item, _A_PLAT) or []
    if isinstance(plats, str):
        plats = [plats]
    plat = [_PLAT_UP[p.lower()] for p in plats if isinstance(p, str) and p.lower() in _PLAT_UP]
    days = _ad_days(item)
    # ISO datum spuštění (dopočtené z dnů) — `_days_since` v scout ho parsuje zpět na dny
    start_iso = (datetime.date.today() - datetime.timedelta(days=days)).isoformat() if days is not None else None
    thumb, vurl = _ad_media_urls(item)  # náhled kreativy (obrázek / poster videa) + URL videa
    return {
        "page_name": str(page).strip(),
        "ad_creative_link_title": (str(title)[:200] if title else None),
        "ad_creative_body": (str(text)[:600] if text else ""),
        "reach": _first(item, _A_REACH, int),
        "ad_delivery_start_time": start_iso,
        "publisher_platforms": (plat or ["FACEBOOK"]),
        "ad_snapshot_url": _first(item, _A_URL),
        "thumbnail": thumb or _first(item, _A_THUMB),
        "video_url": vurl,
        "currency": _first(item, _A_CURR),
    }


def _ad_in_brilliant(c):
    return {"searchTerms": [c["q"]], "countries": [c["cc"]], "adActiveStatus": "active",
            "maxAds": c["cap"], "resolveSnapshotUrls": True}


def _ad_in_autolab(c):
    return {"searchQueries": [c["q"]], "country": c["cc"], "activeStatus": "active", "maxAds": c["cap"]}


def _ad_in_official(c):
    return {"startUrls": [{"url": _adlib_url(c["q"], c["cc"])}], "resultsLimit": c["cap"]}


AD_CHAIN = [
    # automation-lab = spolehlivý + vrací media (náhledy); brilliant_gum konzistentně 400 → až #1
    (_env0("AD_SCOUT_ADLIB_ACTOR", "automation-lab/facebook-ads-library"), _ad_in_autolab),
    ("brilliant_gum/facebook-ads-library-scraper", _ad_in_brilliant),
    ("apify/facebook-ads-scraper", _ad_in_official),
]

# povolené měny pro CZ trh (globální webnovel spam jede v USD)
_AD_CURR_OK = {"CZK", "EUR", None, ""}


def _is_concrete_ad(a):
    """Konkrétní reklama = reálná kreativa (headline/copy), NE dynamický produktový katalog
    ({{product.description}} placeholder) ani prázdná. Katalogy nás nezajímají — jen co reálně jede."""
    blob = ((a.get("ad_creative_link_title") or "") + " " + (a.get("ad_creative_body") or "")).strip()
    if "{{" in blob or "}}" in blob:
        return False
    return len(re.sub(r"\W+", "", blob)) >= 3


def ad_library(terms, country="CZ", cap=20):
    """Veřejná knihovna reklam přes Apify (token, bez Meta účtu/loginu). Fallback chain 3 actorů.
    `terms` = fráze („bojové sporty"), NE holá zkratka. Vrací top-`cap` normalizovaných KONKRÉTNÍCH
    reklam (dynamické katalogy vyloučeny; řazení/dedup/skóre řeší build). Měnový + jazykový filtr."""
    q = terms if isinstance(terms, str) else " ".join(t for t in (terms or []) if t)
    raw = run_chain(AD_CHAIN, {"q": q, "cc": (country or "CZ").upper(), "cap": cap}, "ads")
    if not raw:
        return None
    ads = [a for a in (_norm_ad(it) for it in raw) if a]
    ads = [a for a in ads if (str(a.get("currency") or "").upper() in _AD_CURR_OK)
           and _lang_ok((a.get("ad_creative_link_title") or "") + " " + (a.get("ad_creative_body") or ""))
           and _is_concrete_ad(a)]  # katalogy ven — jen konkrétní běžící reklamy
    return ads or None


# ---- Competitor Ad Board: Meta Ad Library per STRÁNKA (osa = značka) -------

def _adp_in_autolab(c):
    # automation-lab bere přímo pageUrls (URL FB stránky konkurenta) — bez page ID
    return {"pageUrls": [c["page_url"]], "country": c["cc"], "activeStatus": "active", "maxAds": c["cap"]}


def _adp_in_official(c):
    return {"startUrls": [{"url": c["page_url"]}], "resultsLimit": c["cap"], "activeStatus": "active"}


def _adp_in_azzouzana(c):
    return {"startUrl": c["page_url"], "maxAds": c["cap"], "extractDetails": False}


ADP_CHAIN = [
    (_env0("AD_SCOUT_ADPAGE_ACTOR", "automation-lab/facebook-ads-library"), _adp_in_autolab),
    ("apify/facebook-ads-scraper", _adp_in_official),
    ("azzouzana/meta-facebook-instagram-ads-library", _adp_in_azzouzana),
]


def page_ads(page_url, country="CZ", cap=100):
    """VŠECHNY aktivní reklamy KONKRÉTNÍ stránky (Competitor Ad Board, osa = značka).
    Vstup = URL FB stránky konkurenta (typicky nalezená zdarma na jeho webu). Bez jazykového
    filtru (jsou to reklamy té značky — SK/EN kusy jsou taky signál). Dynamické katalogy
    NEvyhazujeme — značí se `catalog:True` (jsou součást obrazu, ale neklonují se)."""
    if not page_url:
        return None
    raw = run_chain(ADP_CHAIN, {"page_url": page_url, "cc": (country or "CZ").upper(), "cap": cap}, "page-ads")
    if not raw:
        return None
    ads = []
    for it in raw:
        a = _norm_ad(it)
        if not a:
            continue
        a["catalog"] = not _is_concrete_ad(a)
        ads.append(a)
    return ads or None


# ---- Competitor Ad Board: Google Ads Transparency (vstup = doména) ----------

def _gt_in_sr(c):
    return {"domain": c["domain"], "region": c["cc"], "ads_count": min(c["cap"], 100), "detail": False}


def _gt_in_scrapesage(c):
    return {"domains": [c["domain"]], "region": c["cc"], "maxAdsPerSearch": c["cap"], "resultType": "ads"}


def _gt_in_solidcode(c):
    return {"searchQuery": c["domain"], "region": c["cc"], "maxResults": c["cap"]}


def _gt_in_lexis(c):
    url = (f"https://adstransparency.google.com/?region={urllib.parse.quote(c['cc'])}"
           f"&domain={urllib.parse.quote(c['domain'])}")
    return {"startUrls": [{"url": url}], "maxItems": c["cap"],
            "proxyConfiguration": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]}}


GT_CHAIN = [
    # s-r = domain-input, 100% úspěšnost, $0.01 start + $0.001/ad (ověřeno ve Store 2026-07-13)
    (_env0("AD_SCOUT_GT_ACTOR", "s-r/google-ads-transparency"), _gt_in_sr),
    ("scrapesage/google-ads-transparency-scraper", _gt_in_scrapesage),
    ("solidcode/ads-transparency-scraper", _gt_in_solidcode),
    # lexis-solutions: startUrls vstup, $0,0016/ad, impressions+targeting (ověřeno 2026-07-13)
    ("lexis-solutions/google-ads-scraper", _gt_in_lexis),
]

_G_ADVERT = ("advertiser_name", "advertiserName", "advertiser", "advertiserDisplayName", "brand")
_G_FORMAT = ("format", "adFormat", "creativeFormat", "creative_format", "type")
_G_TEXT = ("text", "title", "headline", "body", "description", "creativeText", "adText")
_G_URL = ("url", "adUrl", "creativeUrl", "creative_url", "transparencyUrl", "detailsUrl", "link")
_G_FIRST = ("first_shown", "firstShown", "firstShownDate", "first_shown_date", "startDate")
_G_LAST = ("last_shown", "lastShown", "lastShownDate", "last_shown_date", "lastSeen")
_G_IMG = ("image_url", "imageUrl", "image", "thumbnailUrl", "thumbnail", "previewUrl", "preview_url")
_G_VID = ("video_url", "videoUrl", "youtubeUrl", "youtube_url", "videoLink")


def _gt_days(item):
    """Dny běhu z first/last shown (Transparency nemá reach mimo politické)."""
    first = _first(item, _G_FIRST)
    if not first:
        return None
    try:
        d0 = datetime.date.fromisoformat(str(first)[:10])
        return max((datetime.date.today() - d0).days, 0)
    except Exception:
        return None


def _norm_gad(item):
    """Znormalizuje reklamu z libovolného Transparency actoru (různí vendoři = různé klíče).
    Vrací {advertiser, format, text, url, days, last_shown, thumb, video_url}; None = nepoužitelné."""
    if not isinstance(item, dict):
        return None
    fmt = str(_first(item, _G_FORMAT) or "").lower()
    text = _first(item, _G_TEXT)
    url = _first(item, _G_URL)
    thumb = _first(item, _G_IMG) or _find_image_url(item)
    if not (text or thumb or url):
        return None
    return {
        "advertiser": _first(item, _G_ADVERT),
        "format": (fmt if fmt in ("text", "image", "video") else ("video" if _first(item, _G_VID) else None)),
        "text": (str(text)[:300] if text else ""),
        "url": url,
        "days": _gt_days(item),
        "last_shown": _first(item, _G_LAST),
        "thumb": thumb,
        "video_url": _first(item, _G_VID),
    }


def filter_gt_advertisers(ads, brand=None, domain=None):
    """Disambiguace advertiserů z registru Googlu — domain lookup občas přimíchá CIZÍHO
    advertisera s podobným jménem (ověřeno naostro: „ronnie.cz" vrátilo Erasport (= reálný
    provozovatel Ronnie.cz) + „Ronnie Berg" (švédské autodíly)). Pravidla v pořadí:
    1) jeden advertiser → nech vše; 2) jméno značky/domény v názvu advertisera → nech ty;
    3) jinak vyber skupinu s nejvyšším podílem CZ/SK textů; remíza → největší skupina."""
    if not ads:
        return ads
    groups = {}
    for a in ads:
        groups.setdefault(a.get("advertiser") or "?", []).append(a)
    if len(groups) <= 1:
        return ads
    zn = re.sub(r"[^a-z0-9]", "", (brand or (domain or "").split(".")[0] or "").lower())
    named = [k for k in groups if zn and zn in re.sub(r"[^a-z0-9]", "", k.lower())]
    if named:
        keep = [a for k in named for a in groups[k]]
    else:
        def cz_ratio(items):
            txts = [i.get("text") or "" for i in items if i.get("text")]
            if not txts:
                return 0.0
            hits = sum(1 for t in txts if (_CZ_SK_WORD.search(t.lower()) or any(c in _CZ_STRONG for c in t)))
            return hits / len(txts)
        best = max(groups, key=lambda k: (cz_ratio(groups[k]), len(groups[k])))
        keep = groups[best]
    dropped = len(ads) - len(keep)
    if dropped:
        kept_names = sorted({a.get("advertiser") for a in keep})
        sys.stderr.write(f"[gads] disambiguace advertiserů: držím {kept_names} ({len(keep)}), "
                         f"{dropped} reklam cizích advertiserů vyřazeno\n")
    return keep


def transparency_ads(domain, region="CZ", cap=50, brand=None):
    """Reklamy advertisera PODLE DOMÉNY z veřejného registru transparentnosti Googlu
    (Search / YouTube / Display / Shopping). Fallback chain 3 actorů. Deep-link do registru
    si sestav zdarma: adstransparency.google.com/?domain=<doména>&region=<cc>.
    Pozn.: `ads_count` je pro actor jen orientační (vrací i ~100 při cap 50) — počítej s tím
    v odhadu. Výstup prochází disambiguací advertiserů (`filter_gt_advertisers`)."""
    if not domain:
        return None
    dom = re.sub(r"^https?://(www\.)?", "", domain.strip().lower()).split("/")[0]
    raw = run_chain(GT_CHAIN, {"domain": dom, "cc": (region or "CZ").upper(), "cap": cap}, "gads")
    if not raw:
        return None
    ads = [a for a in (_norm_gad(it) for it in raw) if a]
    ads = filter_gt_advertisers(ads, brand=brand, domain=dom)
    return ads or None


# ---- Competitor Ad Board: landing fetch + pixel-detekce (router ZDARMA) -----

_PIXELS = {
    "meta": r"connect\.facebook\.net|fbq\(",
    "tiktok": r"analytics\.tiktok\.com|ttq\.",
    "linkedin": r"snap\.licdn\.com|_linkedin_partner_id",
    "google-ads": r"googleadservices|gtag\(|googletagmanager\.com/gtag",
    "gtm": r"googletagmanager\.com/gtm",
    "sklik": r"c\.imedia\.cz|sklikApi|rc\.seznam",
    "hotjar": r"hotjar",
    "heureka": r"heureka",
}
_SOCIAL = {
    "facebook": r"(?:https?:)?//(?:www\.|cs-cz\.)?facebook\.com/([A-Za-z0-9.\-_]{3,60})",
    "instagram": r"(?:https?:)?//(?:www\.)?instagram\.com/([A-Za-z0-9._]{3,40})",
    "tiktok": r"(?:https?:)?//(?:www\.)?tiktok\.com/@([A-Za-z0-9._]{2,40})",
}
_SOCIAL_JUNK = {"sharer", "share.php", "plugins", "tr", "policy", "policies", "legal", "help", "dialog", "login"}


def landing_pixels(domain, timeout=25):
    """Stáhne homepage konkurenta (prostý fetch — landing je veřejná vizitka, ne DB extrakce)
    a vrátí {pixels:[…], social:{net:url}, title}. Pixel-detekce = ROUTER ZDARMA: podle pixelů
    se zapínají jen relevantní placené moduly (TikTok/LinkedIn až když tam pixel je).
    Bonus: odkaz na FB stránku z patičky = vstup pro page_ads (bez hledání page ID)."""
    dom = re.sub(r"^https?://(www\.)?", "", (domain or "").strip().lower()).split("/")[0]
    if not dom:
        return None
    html_txt = ""
    for u in (f"https://www.{dom}/", f"https://{dom}/"):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125 Safari/537.36"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                html_txt = r.read().decode("utf-8", "ignore")
            break
        except Exception:
            continue
    if not html_txt:
        return None
    pixels = [k for k, p in _PIXELS.items() if re.search(p, html_txt, re.I)]
    social = {}
    from collections import Counter
    for net, pat in _SOCIAL.items():
        hits = [m for m in re.findall(pat, html_txt) if m.lower() not in _SOCIAL_JUNK]
        if hits:
            handle = Counter(hits).most_common(1)[0][0]
            base = {"facebook": "https://www.facebook.com/", "instagram": "https://www.instagram.com/",
                    "tiktok": "https://www.tiktok.com/@"}[net]
            social[net] = base + handle
    m = re.search(r"<title[^>]*>(.*?)</title>", html_txt, re.S | re.I)
    return {"pixels": pixels, "social": social, "title": (m.group(1).strip()[:120] if m else None)}


_LP_HINT = re.compile(r"/(lp|go|akce|kampan|promo|sale|black|sleva|vyprodej|soutez|landing)[/\-]", re.I)


def sitemap_lps(domain, cap=30, timeout=20):
    """Sitemap.xml → skryté landing pages (/lp/ /go/ /akce/…) = kampaně mimo reklamní registry.
    Prostý fetch (veřejný soubor), zdarma. Vrací max `cap` URL."""
    dom = re.sub(r"^https?://(www\.)?", "", (domain or "").strip().lower()).split("/")[0]
    urls = []
    for sm in (f"https://www.{dom}/sitemap.xml", f"https://{dom}/sitemap.xml"):
        try:
            req = urllib.request.Request(sm, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                xml = r.read().decode("utf-8", "ignore")
            urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
            break
        except Exception:
            continue
    if not urls:
        return None
    hits = [u for u in urls if _LP_HINT.search(u)]
    return hits[:cap] or None


# ---- Raw Diet: komentáře pod virálem (voice-of-customer) -------------------

# Kandidátní pole textu/lajků napříč aktory (různí vendoři = různá jména).
_C_TEXT = ("text", "comment", "commentText", "message", "content")
_C_LIKES = ("likes", "likesCount", "voteCount", "diggCount", "likeCount")


def _norm_comment(item, net):
    """Znormalizuje syrový komentář z libovolného aktoru na {text, likes, net}.
    🛑 GDPR: jméno/handle/ID autora NIKDY nepřenášíme — strháváme je už tady, na
    hranici providera, ať se osobní údaj vůbec nedostane dál do skillu ani do wiki."""
    if not isinstance(item, dict):
        return None
    text = next((str(item[k]).strip() for k in _C_TEXT if item.get(k)), "")
    if not text:
        return None
    likes = next((item[k] for k in _C_LIKES if isinstance(item.get(k), (int, float))), 0)
    return {"text": text[:400], "likes": int(likes or 0), "net": net}


# Comment chainy — vstup = URL postů (veřejné posty, bez loginu; Apify jede přes residential proxy).
def _cm_ig_official(c):
    return {"directUrls": c["urls"], "resultsLimit": c["cap"], "includeNestedComments": False}


def _cm_ig_apidojo(c):
    return {"startUrls": [{"url": u} for u in c["urls"]], "maxItems": c["cap"], "fetchReplies": False}


def _cm_ig_louis(c):
    return {"urls": c["urls"], "maxComments": c["cap"]}


def _cm_fb_official(c):
    return {"startUrls": [{"url": u} for u in c["urls"]], "resultsLimit": c["cap"], "includeNestedComments": False}


def _cm_fb_knight(c):
    return {"postUrls": c["urls"], "maxComments": c["cap"], "includeNestedComments": False}


def _cm_fb_thedoor(c):
    return {"postUrls": c["urls"], "targetComments": c["cap"], "includeReplies": False}


def _cm_yt_streamers(c):
    return {"startUrls": [{"url": u} for u in c["urls"]], "maxComments": c["cap"], "sortCommentsBy": "top"}


def _cm_yt_codenode(c):
    return {"inputType": "video", "videoUrls": c["urls"], "maxCommentsPerVideo": c["cap"], "commentSortBy": "top"}


def _cm_tt_clockworks(c):
    return {"postURLs": c["urls"], "commentsPerPost": c["cap"], "maxRepliesPerComment": 0}


def _cm_tt_apidojo(c):
    return {"startUrls": [{"url": u} for u in c["urls"]], "maxItems": c["cap"], "includeReplies": False}


def _cm_tt_scrapeforge(c):
    return {"postURLs": c["urls"], "commentsPerPost": c["cap"], "maxRepliesPerComment": 0}


COMMENT_CHAINS = {
    "instagram": [
        (_env0("AD_SCOUT_IG_COMMENTS_ACTOR", "apify/instagram-comment-scraper"), _cm_ig_official),
        ("apidojo/instagram-comments-scraper-api", _cm_ig_apidojo),
        ("louisdeconinck/instagram-comments-scraper", _cm_ig_louis),
    ],
    "facebook": [
        (_env0("AD_SCOUT_FB_COMMENTS_ACTOR", "apify/facebook-comments-scraper"), _cm_fb_official),
        ("expected_knight/facebook-comments-pay-per-comment", _cm_fb_knight),
        ("thedoor/facebook-comment-scraper", _cm_fb_thedoor),
    ],
    "youtube": [
        (_env0("AD_SCOUT_YT_COMMENTS_ACTOR", "streamers/youtube-comments-scraper"), _cm_yt_streamers),
        ("code-node-tools/youtube-comments-scraper", _cm_yt_codenode),
    ],
    "tiktok": [
        (_env0("AD_SCOUT_TT_COMMENTS_ACTOR", "clockworks/tiktok-comments-scraper"), _cm_tt_clockworks),
        ("apidojo/tiktok-comments-scraper", _cm_tt_apidojo),
        ("scrapeforge/tiktok-comments-extractor", _cm_tt_scrapeforge),
    ],
}
_NET_ALIAS = {"yt": "youtube", "tt": "tiktok", "ig": "instagram", "fb": "facebook"}


def content_comments(urls, net, cap=120):
    """Stáhne komentáře pod ORGANICKÝM virálem (Raw Diet = jazyk zákazníka) k top kusům.
    Vstup = URL postů; fallback chain per síť (když primární actor vrátí prázdno / rate-limit).
    Vrací list `{text, likes, net}` BEZ autorů (GDPR). Destilaci na námitky/touhy dělá MODEL."""
    if not urls:
        return None
    if isinstance(urls, str):
        urls = [urls]
    urls = list(urls)
    net = _NET_ALIAS.get((net or "").lower(), (net or "").lower())
    chain = COMMENT_CHAINS.get(net)
    if not chain:
        return None
    raw = run_chain(chain, {"urls": urls, "cap": cap}, f"comments:{net}")
    if not raw:
        return None
    out = [c for c in (_norm_comment(it, net) for it in raw) if c]
    return out or None


# ---- Viral DNA Card: donor fetch podle URL (jeden kus — reklama nebo obsah) ---------
# Donor = JEDEN vítězný kus (URL videa/postu/reklamy) → meta + náhled + (volitelně)
# přepis + video. Chainy per síť, ≥2 fallbacky (ověřeno v Apify Store 2026-07-13).
# TikTok #0 umí v JEDNOM běhu meta + cover + video download + transkripci (add-on).

_DONOR_NET_RE = [
    (re.compile(r"facebook\.com/ads/library", re.I), "adlib"),
    (re.compile(r"tiktok\.com", re.I), "tiktok"),
    (re.compile(r"youtube\.com|youtu\.be", re.I), "youtube"),
    (re.compile(r"instagram\.com", re.I), "instagram"),
    (re.compile(r"facebook\.com|fb\.watch", re.I), "facebook"),
]


def donor_net(url):
    """Síť donora z URL (adlib = Meta Ad Library deep-link, jinak organika)."""
    for rx, net in _DONOR_NET_RE:
        if rx.search(url or ""):
            return net
    return None


def _dn_tt_clockworks(c):
    p = {"postURLs": c["urls"], "shouldDownloadCovers": True}
    if c.get("video"):
        p["shouldDownloadVideos"] = True                 # add-on (~$0,001/video)
    if c.get("transcript"):                              # add-on (~$0,04/započatá min)
        p["downloadSubtitlesOptions"] = "DOWNLOAD_AND_TRANSCRIBE_VIDEOS_WITHOUT_SUBTITLES"
    return p


def _dn_tt_apidojo(c):
    return {"startUrls": c["urls"], "maxItems": len(c["urls"])}


def _dn_tt_free(c):
    return {"postURLs": c["urls"]}


def _dn_yt_streamers(c):
    # startUrls mode chce maxResults>0, jinak NO_RESULTS (ověřeno 2026-07-12)
    p = {"startUrls": [{"url": u} for u in c["urls"]], "maxResults": max(len(c["urls"]), 1)}
    if c.get("transcript"):
        p.update({"downloadSubtitles": True, "subtitlesLanguage": "any",
                  "subtitlesFormat": "plaintext", "preferAutoGeneratedSubtitles": True})
    return p


def _dn_yt_starvibe(c):
    return {"youtube_url": c["urls"][0], "include_transcript_text": bool(c.get("transcript"))}


def _dn_yt_beyondops(c):
    return {"videoUrls": c["urls"]}


def _dn_ig_official(c):
    return {"directUrls": c["urls"], "resultsType": "posts", "resultsLimit": len(c["urls"])}


def _dn_ig_api(c):
    return {"directUrls": c["urls"], "resultsLimit": len(c["urls"])}


def _dn_fb_official(c):
    return {"startUrls": [{"url": u} for u in c["urls"]], "resultsLimit": len(c["urls"])}


def _dn_fb_xtracto(c):
    return {"posts": c["urls"]}


def _dn_al_autolab(c):
    return {"adsLibraryUrls": c["urls"], "maxAds": 3}


def _dn_al_official(c):
    return {"startUrls": [{"url": u} for u in c["urls"]], "resultsLimit": 3}


def _dn_al_azzouzana(c):
    return {"startUrl": c["urls"][0], "maxAds": 3, "extractDetails": True}


DONOR_CHAINS = {
    "tiktok": [
        (_env0("AD_SCOUT_TT_DONOR_ACTOR", "clockworks/tiktok-scraper"), _dn_tt_clockworks),
        ("apidojo/tiktok-scraper", _dn_tt_apidojo),
        ("clockworks/free-tiktok-scraper", _dn_tt_free),
    ],
    "youtube": [
        (_env0("AD_SCOUT_YT_DONOR_ACTOR", "streamers/youtube-scraper"), _dn_yt_streamers),
        ("starvibe/youtube-video-transcript", _dn_yt_starvibe),
        ("beyondops/youtube-metadata-scraper-pro-v2", _dn_yt_beyondops),
    ],
    "instagram": [
        (_env0("AD_SCOUT_IG_DONOR_ACTOR", "apify/instagram-scraper"), _dn_ig_official),
        ("apify/instagram-api-scraper", _dn_ig_api),
    ],
    "facebook": [
        (_env0("AD_SCOUT_FB_DONOR_ACTOR", "apify/facebook-posts-scraper"), _dn_fb_official),
        ("xtracto/facebook-post-detail", _dn_fb_xtracto),
    ],
    "adlib": [
        (_env0("AD_SCOUT_ADLIB_DONOR_ACTOR", "automation-lab/facebook-ads-library"), _dn_al_autolab),
        ("apify/facebook-ads-scraper", _dn_al_official),
        ("azzouzana/meta-facebook-instagram-ads-library", _dn_al_azzouzana),
    ],
}

# Dedikovaný přepis (fallback, když ho donor fetch nevrátil). YouTube: titulky zdarma
# v #0 donor chainu; tohle jsou záložní specialisti. TikTok přepis řeší donor chain #0.
TRANSCRIPT_CHAINS = {
    "youtube": [
        (_env0("AD_SCOUT_YT_TRANSCRIPT_ACTOR", "pintostudio/youtube-transcript-scraper"),
         lambda c: {"videoUrl": c["urls"][0], "targetLanguage": "en"}),
        ("karamelo/youtube-transcripts", lambda c: {"urls": c["urls"], "outputFormat": "json"}),
    ],
}

_D_SHARES = ("shareCount", "sharesCount", "shares", "repostCount", "resharesCount")
_D_DESC = ("text", "description", "caption", "postText", "content", "desc")


def _donor_transcript_text(item):
    """Vytáhne přepis z libovolného tvaru (různí vendoři: string / list segmentů / subtitles)."""
    for k in ("transcript", "transcript_text", "transcription", "subtitles_text", "captions_text"):
        v = item.get(k)
        if isinstance(v, str) and len(v.strip()) > 40:
            return v.strip()
        if isinstance(v, list) and v:  # segmenty [{text,...}]
            parts = [str(s.get("text") or s.get("line") or "").strip() for s in v if isinstance(s, dict)]
            joined = " ".join(x for x in parts if x)
            if len(joined) > 40:
                return joined
    subs = item.get("subtitles")
    if isinstance(subs, list):
        for s in subs:
            if isinstance(s, dict):
                for k in ("plaintext", "text", "srt", "content"):
                    v = s.get(k)
                    if isinstance(v, str) and len(v.strip()) > 40:
                        return v.strip()
    vm = item.get("videoMeta") if isinstance(item.get("videoMeta"), dict) else {}
    for k in ("subtitles", "transcript"):
        v = vm.get(k)
        if isinstance(v, str) and len(v.strip()) > 40:
            return v.strip()
    return None


def _fetch_subtitle_link(item):
    """TikTok (ASR) titulky chodí jako `videoMeta.subtitleLinks[].downloadLink` (VTT v KV
    store providera, žije s ?token — stejně jako covery). Stáhne první funkční a očistí
    na souvislý text (bez časování). Ověřeno naostro 2026-07-13."""
    vm = item.get("videoMeta") if isinstance(item.get("videoMeta"), dict) else {}
    links = vm.get("subtitleLinks") or item.get("subtitleLinks") or []
    for l in links:
        url = l.get("downloadLink") if isinstance(l, dict) else None
        if not url:
            continue
        if "api.apify.com" in url and "token=" not in url:
            tok = _token()
            if tok:
                url += ("&" if "?" in url else "?") + "token=" + urllib.parse.quote(tok)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read().decode("utf-8", "ignore")
        except Exception:
            continue
        lines = []
        for ln in raw.splitlines():
            s = ln.strip()
            if not s or s.startswith(("WEBVTT", "NOTE", "STYLE")) or "-->" in s or s.isdigit():
                continue
            lines.append(s)
        text = " ".join(lines)
        if len(text) > 40:
            return text
    return None


def _norm_donor(item, net):
    """Znormalizuje donora (1 kus) na jednotný tvar pro dnacard_build. Nese i syrové
    pole `_raw` (build ho uloží do donor-raw.json pro pozdější doladění tvarů)."""
    base = _norm_search(item, net) or {}
    vm = item.get("videoMeta") if isinstance(item.get("videoMeta"), dict) else {}
    am = item.get("authorMeta") if isinstance(item.get("authorMeta"), dict) else {}
    video_url = (_first_url(item.get("mediaUrls")) or vm.get("downloadAddr")
                 or _first_url(item.get("videoUrl")) or _first_url(item.get("videoUrls")))
    desc = _first(item, _D_DESC)
    return {
        "sit": net, "nm": base.get("nm") or "", "kdo": base.get("kdo"),
        "url": base.get("url"), "zhlednuti": base.get("zhlednuti"), "likes": base.get("likes"),
        "cmts": base.get("cmts"), "shares": _first(item, _D_SHARES, int),
        "thumb": base.get("thumb"), "dur": base.get("dur"),
        "popis": (str(desc)[:2000] if desc else None),
        "video_url": video_url,
        "transcript": _donor_transcript_text(item) or _fetch_subtitle_link(item),
        "sledujicich": am.get("fans") or am.get("followers") or item.get("numberOfSubscribers"),
        "_raw": item,
    }


def donor_meta(url, want_video=False, want_transcript=False):
    """Stáhne meta JEDNOHO donora podle URL (Viral DNA Card). Vrací normalizovaný tvar;
    u reklamy (Ad Library deep-link) vrací {sit:'adlib', ad:<kanonická reklama>}.
    Vše přes Apify (proxy IP), nikdy z klientského serveru."""
    net = donor_net(url)
    chain = DONOR_CHAINS.get(net or "")
    if not chain:
        sys.stderr.write(f"[donor] neznámá síť pro URL: {url[:80]}\n")
        return None
    raw = run_chain(chain, {"urls": [url], "video": want_video, "transcript": want_transcript},
                    f"donor:{net}")
    if not raw:
        return None
    if net == "adlib":
        ads = [a for a in (_norm_ad(it) for it in raw) if a]
        return {"sit": "adlib", "ad": (ads[0] if ads else None), "_raw": raw[0]}
    return _norm_donor(raw[0], net)


def donor_transcript(url):
    """Záložní přepis donora (když ho donor_meta nevrátil). Jen sítě s chainem (YouTube)."""
    net = donor_net(url)
    chain = TRANSCRIPT_CHAINS.get(net or "")
    if not chain:
        return None
    raw = run_chain(chain, {"urls": [url]}, f"transcript:{net}")
    if not raw:
        return None
    for it in raw:
        if not isinstance(it, dict):
            continue
        t = _donor_transcript_text(it)
        if t:
            return t
        data = it.get("data")  # pintostudio: {data:[{text,start,dur}]}
        if isinstance(data, list):
            joined = " ".join(str(s.get("text") or "").strip() for s in data if isinstance(s, dict))
            if len(joined) > 40:
                return joined
    return None


# ---- Discovery organiky: KEYWORD SEARCH (podle tématu, ne hashtagu/watchlistu) -------

# Kandidátní pole napříč aktory (různí vendoři = různá jména).
_S_TEXT = ("title", "caption", "text", "content", "postText", "description", "nm")
_S_WHO = ("ownerUsername", "authorName", "author", "username", "channelName", "ownerFullName", "authorFullName", "pageName")
_S_URL = ("url", "postUrl", "webVideoUrl", "videoUrl", "videoLink", "permalink", "link", "postLink")
_S_VIEWS = ("playCount", "videoViewCount", "viewCount", "views", "viewsCount")
_S_LIKES = ("likesCount", "diggCount", "likes", "reactionsCount", "numLikes", "likeCount", "reactions")
_S_CMTS = ("commentsCount", "commentCount", "comments", "numComments")
_S_THUMB = ("displayUrl", "coverUrl", "thumbnailUrl", "thumbnail", "cover", "imageUrl")


def _first(item, keys, cast=None):
    for k in keys:
        v = item.get(k)
        if v not in (None, "", 0, []):
            if cast:
                try:
                    return cast(v)
                except Exception:
                    continue
            return v
    return None


def _norm_search(item, net):
    """Znormalizuje syrový výsledek keyword search z libovolného aktoru na tvar `viralni`
    kontraktu. `nm` je surový titulek/caption — MODEL ho pak přeloží/shrne (max 3 řádky).
    Ošetřuje i ZANOŘENÁ pole (TikTok clockworks: videoMeta.coverUrl / authorMeta.name)."""
    if not isinstance(item, dict):
        return None
    url = _first(item, _S_URL)
    text = _first(item, _S_TEXT)
    if not (url or text):
        return None
    vm = item.get("videoMeta") if isinstance(item.get("videoMeta"), dict) else {}
    am = item.get("authorMeta") if isinstance(item.get("authorMeta"), dict) else {}
    thumb = _first(item, _S_THUMB) or vm.get("coverUrl") or vm.get("originalCoverUrl")
    who = _first(item, _S_WHO) or am.get("nickName") or am.get("name")
    if isinstance(who, dict):  # někteří actoři (FB) vrací autora jako objekt {id,name,profileUrl}
        who = who.get("name") or who.get("username") or who.get("fullName") or who.get("nickName")
    if who and not str(who).startswith("@"):
        who = "@" + str(who)
    dur = item.get("dur") or item.get("duration") or vm.get("duration")
    return {
        "sit": net, "nm": (str(text)[:200] if text else ""), "kdo": who, "url": url,
        "zhlednuti": _first(item, _S_VIEWS, int), "likes": _first(item, _S_LIKES, int),
        "cmts": _first(item, _S_CMTS, int), "thumb": thumb,
        "dur": (str(dur) if dur else None), "geo": None,
    }


# ---- Search Ad Board: placený SERP + keyword metriky (portfolio → transparency_ads výše) ----
# Zdroje ověřeny v Apify Store 2026-07-13 (fetch-actor-details): ceny + input schémata + CZ podpora.
#   SERP paid:     apify/google-search-scraper + add-on focusOnPaidAds (~$0,0075/dotaz s add-onem)
#   Portfolio inzerenta: sdílené `transparency_ads` (GT_CHAIN: s-r → scrapesage → solidcode → lexis)
#   Keyword metriky: s-r/google-keywords (ISO country, CZ OK; $0,002/kw)
#                  → fallback burbn/semrush-keyword-magic-tool ($0,005 start + $0,006/kw)
#   ⚠️ smacient/google-keyword-planner-mcp ZAMÍTNUT — `locations` enum NEMÁ Českou republiku.

_SERP_BATCH = 4  # dotazů na jeden actor run (run-sync limit ~300 s; paid add-on dělá až 3 retry/dotaz)

# ⚠️ Ověřeno naostro (2026-07-13, „kreatin" CZ): s focusOnPaidAds vrací actor JEN paid blok
# (organicResults/relatedQueries PRÁZDNÉ) a občas SLEPÍ víc reklam do jednoho záznamu
# (displayedUrl = víc URL za sebou). Slepence řeší _split_glued; související dotazy ber
# ze search_results (normální levný běh). 0 paid po 3 retry = validní signál (hustota 0).
_DOM_RE = re.compile(r"(?:https?://)?(?:www\.)?([a-z0-9][a-z0-9.-]*\.[a-z]{2,})", re.I)
_TITLE_SPLIT = re.compile(r"(?<=[a-záčďéěíňóřšťúůýž0-9%.!)])(?=[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ])")


def _paid_norm(p, pos_fallback):
    """Znormalizuje jeden placený výsledek SERPu. Sitelinky POTVRZENY testovacím během
    (P1 z plánu): `siteLinks: [{title, url, description?}]`."""
    if not isinstance(p, dict):
        return None
    title = p.get("title") or ""
    url = p.get("url") or ""
    if not (title or url):
        return None
    links = []
    for sl in (p.get("siteLinks") or []):
        t = (sl.get("title") or "").strip() if isinstance(sl, dict) else str(sl).strip()
        if t and t not in links:
            links.append(t[:60])
    return {
        "pos": p.get("adPosition") or p.get("position") or pos_fallback,
        "title": str(title)[:200],
        "desc": str(p.get("description") or "")[:400],
        "url": url,
        "displayed": p.get("displayedUrl") or p.get("displayed_url") or "",
        "sitelinks": links,
    }


def _split_glued(p, pos_fallback):
    """Actor občas slepí VÍC reklam do jednoho záznamu (displayedUrl obsahuje víc URL).
    Rozdělí per doména; titulky zkusí rozseknout na hranici malé→VELKÉ písmeno (jen když
    počet segmentů sedí na počet domén — jinak blob nechá modelu k vyčištění, flag `blob`)."""
    base = _paid_norm(p, pos_fallback)
    if not base:
        return []
    doms = []
    for m in _DOM_RE.finditer(base["displayed"] or ""):
        d = m.group(1).lower()
        if d not in doms:
            doms.append(d)
    if len(doms) <= 1:
        return [base]
    parts = _TITLE_SPLIT.split(base["title"] or "")
    if len(parts) != len(doms):
        parts = [base["title"]] + [""] * (len(doms) - 1)
    out = []
    for i, d in enumerate(doms):
        out.append({
            "pos": base["pos"], "title": (parts[i] or base["title"] or "")[:200],
            "desc": base["desc"] if i == 0 else "",
            "url": base["url"] if i == 0 else None,
            "displayed": d, "sitelinks": base["sitelinks"] if i == 0 else [],
            "blob": True,  # slepenec — copy vyčistí model (sekce 2)
        })
    return out


def search_ads(queries, market="cz"):
    """Placený blok Google Search na dotaz(y): kdo bidduje + copy + pozice + sitelinky.
    Páteř Search Ad Boardu (sekce 1, 2, 3, 5 — hustota inzerentů/dotaz). Add-on
    `focusOnPaidAds` = ad-specializovaná proxy s retry, účtuje se per stránka i bez nálezu.
    `queries` = string nebo list; dotazy se dávkují po _SERP_BATCH na jeden běh."""
    if isinstance(queries, str):
        queries = [queries]
    queries = [q.strip() for q in (queries or []) if q and q.strip()]
    if not queries:
        return None
    out = []
    for i in range(0, len(queries), _SERP_BATCH):
        batch = queries[i:i + _SERP_BATCH]
        items = run_actor(SEARCH_ACTOR, {
            "queries": "\n".join(batch), "resultsPerPage": 10, "maxPagesPerQuery": 1,
            "countryCode": market, "searchLanguage": "cs" if market == "cz" else "",
            "languageCode": "cs" if market == "cz" else "en",
            "focusOnPaidAds": True, "mobileResults": False,
        }, timeout=300)
        if not items:
            # fallback SERP: jediný actor s paid add-onem je apify/google-search-scraper —
            # záskok umí jen organiku (degradace, ne výpadek); placený blok označíme nedostupný
            sys.stderr.write(f"[chain] serp: {SEARCH_ACTOR} prázdno/chyba → {SERP_FALLBACK_ACTOR} (jen organika)\n")
            for q in batch:
                rows = run_actor(SERP_FALLBACK_ACTOR, {
                    "query": q, "maxItems": 10, "country": market,
                    "language": "cs" if market == "cz" else "en",
                    "domain": "google.cz" if market == "cz" else "google.com",
                }, timeout=180) or []
                out.append({"query": q, "paid": [], "related": [], "_paid_unavailable": True,
                            "organic": [{"pos": r.get("position"), "title": r.get("title"),
                                         "url": r.get("url")} for r in rows[:10]]})
            continue
        for it in (items or []):
            q = ((it.get("searchQuery") or {}).get("term") if isinstance(it.get("searchQuery"), dict)
                 else it.get("searchQuery")) or ""
            paid = []
            for j, p in enumerate(it.get("paidResults") or []):
                paid += _split_glued(p, j + 1)
            out.append({
                "query": str(q).strip(),
                "paid": paid,
                # s focusOnPaidAds bývá organika/related PRÁZDNÁ → related ber ze search_results
                "organic": [{"pos": o.get("position"), "title": o.get("title"), "url": o.get("url")}
                            for o in (it.get("organicResults") or [])[:10]],
                "related": [r.get("title") for r in (it.get("relatedQueries") or []) if r.get("title")],
            })
    return out or None


# Portfolio inzerenta z reklamního registru = SDÍLENÉ `transparency_ads` (GT_CHAIN výše,
# Competitor Ad Board). Search board ho volá per doména top bidderů — žádná duplikace.
def advertiser_ads(domain, market="CZ", cap=30):
    """Alias pro Search Ad Board: portfolio inzerenta podle domény z veřejného registru
    (Google Ads Transparency). Winner proxy = stáří reklamy (`days`); 90+ dní = „prověřeno
    trhem". Deleguje na sdílené transparency_ads (fallback chain 4 actorů)."""
    return transparency_ads(domain, market, cap)


# Keyword metriky (objem/CPC/konkurence) — podklad mezery v klíčových slovech + semaforu ceny.
_KW_KW = ("keyword", "kw", "term", "query")
_KW_VOL = ("volume", "search_volume", "searchVolume", "avg_monthly_searches", "avgMonthlySearches", "monthly_volume")
_KW_CPC = ("cpc", "cpc_usd", "cpcUsd", "avg_cpc", "avgCpc", "cost_per_click", "high_cpc", "cpc_high")
_KW_COMP = ("competition", "paid_difficulty", "paidDifficulty", "paid_competition", "competition_level",
            "competition_index", "competitionIndex")
_KW_INTENT = ("intent", "search_intent", "searchIntent")


def _norm_kw(item):
    if not isinstance(item, dict):
        return None
    kw = _first(item, _KW_KW)
    if not kw:
        return None
    comp = _first(item, _KW_COMP)
    intent = _first(item, _KW_INTENT)
    return {"kw": str(kw).strip().lower()[:80], "volume": _first(item, _KW_VOL, int),
            "cpc": _first(item, _KW_CPC, float),
            "competition": (str(comp)[:20] if comp is not None else None),
            "intent": (str(intent)[:30].lower() if intent else None)}


def _kw_in_sr(c):
    return {"keyword": c["seed"], "country": c["cc"].lower(), "language": c["lang"],
            "limit": c["cap"], "min_volume": 0}


def _kw_in_semrush(c):
    return {"keyword": c["seed"], "country": c["cc"].lower(), "language": c["lang"], "maxResults": c["cap"]}


KEYWORD_CHAIN = [
    (_env0("AD_SCOUT_KEYWORD_ACTOR", "s-r/google-keywords"), _kw_in_sr),
    ("burbn/semrush-keyword-magic-tool", _kw_in_semrush),
]


def keyword_metrics(seed, market="cz", cap=60):
    """Rozšíří seed slovo na varianty s objemem hledání, odhadem CPC a konkurencí.
    ⚠️ CPC je ODHAD s nejasnou měnou (u CZ vypadá jako Kč, ověřeno „kreatin"≈24; garantované
    to není) — na boardu VŽDY jen semafor levné/střední/drahé, nikdy „přesné" CPC na 2
    desetinná místa. `competition` = index 0–1 (1 = plno). Hustotu ověřuje search_ads (probe)."""
    if not seed:
        return None
    lang = "cs" if (market or "").lower() == "cz" else "en"
    raw = run_chain(KEYWORD_CHAIN,
                    {"seed": seed, "cc": (market or "cz"), "lang": lang, "cap": cap},
                    "keywords")
    if not raw:
        return None
    seen, out = set(), []
    for it in raw:
        k = _norm_kw(it)
        if not k or k["kw"] in seen:
            continue
        seen.add(k["kw"])
        out.append(k)
    return out or None


# Cílený dohled objemů pro KONKRÉTNÍ slova (bulk) — expanzní actory long-tail z mezery
# často neznají; tenhle bere seznam slov a vrátí volume/CPC/konkurenci per slovo.
SERP_FALLBACK_ACTOR = _env0("AD_SCOUT_SERP_FALLBACK_ACTOR", "igolaizola/google-search-scraper-ppe")
KW_VOLUME_ACTOR = _env0("AD_SCOUT_KWVOL_ACTOR", "iskander/google-keyword-search-volume-api")
_KWVOL_LOC = {"cz": "Czechia", "sk": "Slovakia", "pl": "Poland", "de": "Germany",
              "at": "Austria", "us": "United States", "gb": "United Kingdom", "es": "Spain"}


SCREENSHOT_ACTOR = _env0("AD_SCOUT_SCREENSHOT_ACTOR", "apify/screenshot-url")


def page_screenshot(url, out_path, market="cz", width=1280, height=2200, timeout=180):
    """Screenshot stránky reálným prohlížečem přes Apify + REZIDENTNÍ proxy daného trhu —
    fallback pro landingy, které blokují roboty (ověřeno na Alze: Playwright headless
    i headful = 403, rezidentní proxy = 200). Browser tool na serveru je PRVNÍ volba
    (zdarma); tohle je záskok ~$0,02–0,05/snímek. Vrací cestu k PNG, nebo None."""
    import time
    try:
        run = _api_post(f"/acts/{SCREENSHOT_ACTOR.replace('/', '~')}/runs", {
            "urls": [{"url": url}], "waitUntil": "networkidle2", "delay": 6000,
            "viewportWidth": width, "viewportHeight": height, "fullPage": False,
            "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"],
                      "apifyProxyCountry": (market or "cz").upper()},
        })["data"]
        rid = run["id"]
        deadline = time.time() + timeout
        st = None
        while time.time() < deadline:
            time.sleep(5)
            st = _api_get(f"/actor-runs/{rid}")["data"]
            if st["status"] not in ("RUNNING", "READY"):
                break
        if not st or st.get("status") != "SUCCEEDED":
            return None
        kvs = st["defaultKeyValueStoreId"]
        keys = _api_get(f"/key-value-stores/{kvs}/keys")["data"]["items"]
        shot = next((k["key"] for k in keys if k["key"].startswith("screenshot")), None)
        if not shot:
            return None
        data = _api_raw(f"/key-value-stores/{kvs}/records/{shot}")
        if not data or len(data) < 5000:
            return None
        with open(out_path, "wb") as f:
            f.write(data)
        return out_path
    except Exception as ex:
        sys.stderr.write(f"[provider] page_screenshot: {str(ex)[:120]}\n")
        return None


def keyword_volumes(kws, market="cz"):
    """Objem/CPC/konkurence pro ZADANÁ slova (bulk actor; fallback = expanzní chain
    se slovem jako seedem). Vrací {kw: {volume, cpc, competition}}."""
    kws = [str(k).strip() for k in (kws or []) if k and str(k).strip()][:50]
    if not kws:
        return {}
    lang = "cs" if (market or "").lower() == "cz" else "en"
    out = {}
    items = run_actor(KW_VOLUME_ACTOR, {
        "keywords": kws, "location_name": _KWVOL_LOC.get((market or "cz").lower(), "Czechia"),
        "language_code": lang,
    }, timeout=300)
    for it in items or []:
        k = _norm_kw(it)
        if k:
            # bulk actor vrací CPC v USD → hrubý převod na Kč (board ukazuje jen odhady)
            if k.get("cpc") and k["cpc"] < 10 and (market or "").lower() == "cz":
                k["cpc"] = round(k["cpc"] * 23.5, 1)
            out[k["kw"]] = k
    missing = [k for k in kws if k.lower() not in out]
    if missing:
        sys.stderr.write(f"[chain] kw-volumes: bulk nedodal {len(missing)} slov → expanzní fallback\n")
    for k in missing[:10]:
        rows = run_chain(KEYWORD_CHAIN, {"seed": k, "cc": (market or "cz"), "lang": lang, "cap": 5},
                         f"kwvol:{k[:24]}") or []
        for it in rows:
            n = _norm_kw(it)
            if n and n["kw"] == k.lower():
                out[k.lower()] = n
                break
    return out


# ---- Jazykový allow-list (CZ/SK) — síto proti globálnímu/cizojazyčnému šumu -----
# Primární obrana je keyword-search actor (ne generický hashtag explore); tohle je best-effort síto.
_CZ_STRONG = set("ěřůýĚŘŮÝ")                   # ř/ě/ů/ý = prakticky unikátní pro češtinu/slovenštinu
_SK_STRONG = set("ľĺŕôäĽĹŔÔÄ")                 # slovenské znaky
_FOREIGN_CHAR = set("çãõñćđğıøåßşțàèìòùâêîûüö¿¡")  # znaky mimo CZ/SK/EN (špan./katalán/portug./turec./něm. …)
# Cizí (ne CZ/SK/EN) slova. Držíme jen CZ/SK + angličtinu; ostatní jazyky (španělština…) ven.
_FOREIGN_WORD = ("için", "você", "voce", "não", "nao", "lloguer", "generalitat", "convocat",
                 "ajuda", "možda", "nešto", "ovaj", " jer ", "hvala", "hola", " com o ",
                 "qué", "creatina", " está ", "cómo", " es la ", " una ", "señor", " años",
                 " che ", " della ", " sono ", " avec ", " pour ", " être", " vous ", " für ",
                 " yang ", " tinggi ", " kamu ", " jgn", "ciri-ciri", " wajib ", " dulu ", " tidak ",  # indonéština
                 " wir ", " müssen", " machen", " nicht ", " und ", " ich ", " ist ", " das ", " sehr ",  # němčina
                 " hasta ", "cambia", " voz ", " cómo ", " para ti")  # španělština (další)
_CZ_SK_WORD = re.compile(
    r"\b(že|který|která|které|jsou|více|při|před|vás|naše|když|jsem|bude|máte|jaký|jaké|"
    r"slyšel|nebo|kolik|není|dej|mýtus|není|český|česká|české|proč|něco|můžeš|vám|takže|prostě|opravdu|"
    r"som|si|ťa|prečo|viac|ako|aby|väčš|najlepš|ďakujem)\b", re.I)
# angličtina — časté funkční/tématické slovo (pozitivní brána proti jiným latinkovým jazykům)
_EN_WORD = re.compile(
    r"\b(the|is|are|was|a|an|to|of|and|or|for|you|your|what|how|why|this|that|does|do|"
    r"with|it|on|in|my|me|we|he|she|when|if|not|no|but|creatine|take|taking|best|good|bad|"
    r"need|know|before|after|women|men|day|days|body|muscle|kidney|kidneys|about|why)\b", re.I)


def _lang_ok(text):
    """Best-effort: nech česky/slovensky, zahoď zjevně cizojazyčné (srbština, katalánština,
    portugalština, turečtina…). Není 100 % — hlavní obrana je keyword-search actor, tohle je síto."""
    t = text or ""
    if not t.strip():
        return True                                  # bez textu nerozhoduj
    low = t.lower()
    if re.search(r"[Ѐ-ӿ]", t):             # cyrilice (srbština/ruština)
        return False
    if any(c in _FOREIGN_CHAR for c in t):
        return False
    if any(w in low for w in _FOREIGN_WORD):
        return False
    if any(c in _CZ_STRONG or c in _SK_STRONG for c in t):
        return True
    if _CZ_SK_WORD.search(low):
        return True
    # POZITIVNÍ anglická brána: delší text bez CZ/SK signálu MUSÍ mít anglické slovo, jinak je to
    # jiný latinkový jazyk (španělština/francouzština/srbochorvatština…) → ven. Krátké tituly (např.
    # „Cope") nechává projít (benefit of the doubt).
    if len(low) > 18 and not _EN_WORD.search(low):
        return False
    return True


# Junk filtr organiky — bazar/inzeráty a zpravodajské weby NEJSOU obsah ke klonování.
# Podcasty, brandové posty a tvůrčí obsah projdou (necílíme na styl, jen na zjevný odpad).
_JUNK_MARKET = re.compile(r"\b(prodáv|prodám|prodej|koupím|sháním|"
                          r"cena dohodou|bazar|inzerát|zn\.:|odvoz)", re.I)  # stem match (bez trailing \b kvůli diakritice)
_JUNK_NEWS = re.compile(r"(deník|denik\.cz|zpráv|zprav|sport\.cz|idnes|novinky\.cz|"
                        r"seznamzpr|blesk\.cz|aktuálně|aktualne\.cz|irozhlas|denik\.cz|\.denik\.)", re.I)


def _is_content_junk(text, who="", url=""):
    """True = bazar/inzerát nebo zpravodajský článek → ne obsah ke klonování. Konzervativní."""
    if _JUNK_MARKET.search(text or ""):
        return True
    if _JUNK_NEWS.search(f"{who or ''} {url or ''}"):  # autor = zpravodajský web / odkaz na článek
        return True
    return False


_HASH_STOP = {"a", "na", "pro", "o", "v", "z", "s", "do", "i", "the", "and", "for", "of"}


def _hashtags(query, n=3):
    """Téma → hashtagy pro IG explore fallback (bez diakritiky, bez stopslov)."""
    w = unicodedata.normalize("NFKD", query or "").encode("ascii", "ignore").decode().lower()
    words = [x for x in re.split(r"[^a-z0-9]+", w) if len(x) > 2 and x not in _HASH_STOP]
    tags = []
    for x in words:
        if x not in tags:
            tags.append(x)
    joined = "".join(words)
    if len(words) > 1 and joined not in tags:
        tags.append(joined)
    return tags[:n] or ([joined] if joined else [])


# Search chainy per síť. builder(ctx) — ctx: {q, cap, since}. Každý actor má vlastní tvar vstupu.
def _se_yt_streamers(c):
    # FIX: streamers/youtube-scraper bere `searchQueries` (pole), NE `searchKeywords`.
    # `maxResultsShorts` = dedikovaně i YouTube Shorts. Fixně 15 (ne plný cap) — jinak stahuje 2× cap (drahé).
    p = {"searchQueries": [c["q"]], "maxResults": c["cap"], "maxResultsShorts": 15, "sortingOrder": "relevance"}
    if c.get("since"):
        p["dateFilter"] = c["since"]
    return p


def _se_tt_clockworks(c):
    p = {"searchQueries": [c["q"]], "resultsPerPage": c["cap"]}
    if c.get("cc"):  # CZ-region: servíruj jako z dané země (jinak globálně nejpopulárnější = cizí jazyk)
        p["proxyCountryCode"] = c["cc"]
    if c.get("since"):
        p["oldestPostDateUnified"] = c["since"]
    return p


def _se_tt_apidojo(c):
    p = {"keywords": [c["q"]], "maxItems": c["cap"], "includeSearchKeywords": True}
    if c.get("cc"):
        p["location"] = c["cc"]  # geo-cílení i na fallbacku
    return p


def _se_tt_free(c):
    p = {"searchQueries": [c["q"]], "resultsPerPage": c["cap"]}
    if c.get("cc"):
        p["proxyCountryCode"] = c["cc"]
    return p


# YouTube search fallbacky (keyword search actory)
def _se_yt_thedoor(c):
    return {"queries": [c["q"]], "maxResults": c["cap"]}


def _se_yt_khadin(c):
    p = {"searchQueries": [c["q"]], "maxResultsPerQuery": c["cap"], "includeShorts": True}
    if c.get("cc"):
        p["country"] = c["cc"]
    return p


# LinkedIn search fallbacky
def _se_li_datadoping(c):
    return {"keywords": [c["q"]], "max_posts": c["cap"], "sort_by": "relevance"}


def _se_li_lofo(c):
    p = {"keywords": [c["q"]], "maxPostsPerKeyword": c["cap"]}
    if c.get("cc"):
        p["country"] = c["cc"]
    return p


def _se_ig_search(c):
    # apify/instagram-scraper: nativní `search` (ne ruční hashtag explore) → čistší než #tag garbage
    return {"search": c["q"], "searchType": "hashtag", "resultsType": "posts", "resultsLimit": c["cap"]}


def _se_ig_explore(c):
    tags = _hashtags(c["q"])
    return {"directUrls": [f"https://www.instagram.com/explore/tags/{t}/" for t in tags],
            "resultsType": "posts", "resultsLimit": c["cap"]}


def _se_ig_api(c):
    return {"search": c["q"], "searchType": "hashtag", "resultsType": "posts", "resultsLimit": c["cap"]}


def _se_fb_scraperone(c):
    p = {"query": c["q"], "resultsCount": c["cap"]}
    if c.get("since"):
        p["startDate"] = c["since"]
    return p


def _se_fb_powerai(c):
    p = {"query": c["q"], "maxResults": c["cap"]}
    if c.get("since"):
        p["start_date"] = c["since"]
    return p


def _se_fb_scrapeforge(c):
    p = {"query": c["q"], "max_results": c["cap"], "search_type": "posts"}
    if c.get("since"):
        p["start_date"] = c["since"]
    return p


def _se_li_harvest(c):
    p = {"searchQueries": [c["q"]], "maxPosts": c["cap"], "sortBy": "relevance", "scrapeReactions": True}
    if c.get("since"):
        p["postedLimitDate"] = c["since"]
    return p


def _se_meta_listen(c):
    return {"mode": "search", "keywords": [c["q"]], "platforms": ["facebook", "instagram"],
            "max_results_per_platform": c["cap"]}


SEARCH_CHAINS = {
    "youtube": [
        (_env0("AD_SCOUT_YT_SEARCH_ACTOR", "streamers/youtube-scraper"), _se_yt_streamers),
        ("thedoor/youtube-video-search", _se_yt_thedoor),
        ("khadinakbar/youtube-search-scraper", _se_yt_khadin),
    ],
    "tiktok": [
        (_env0("AD_SCOUT_TT_SEARCH_ACTOR", "clockworks/tiktok-scraper"), _se_tt_clockworks),
        ("apidojo/tiktok-scraper", _se_tt_apidojo),
        ("clockworks/free-tiktok-scraper", _se_tt_free),
    ],
    "instagram": [
        # hashtag-explore PRIMÁRNĚ (vrací reálné posty; native `search` vrací jen ~1 → blokoval fallback).
        # Jazykový filtr `_lang_ok` dočistí němčinu (#kreatin je německy dominantní).
        (_env0("AD_SCOUT_IG_SEARCH_ACTOR", "apify/instagram-scraper"), _se_ig_explore),
        ("apify/instagram-scraper", _se_ig_search),
        ("apify/instagram-api-scraper", _se_ig_api),
    ],
    "facebook": [
        (_env0("AD_SCOUT_FB_SEARCH_ACTOR", "scraper_one/facebook-posts-search"), _se_fb_scraperone),
        ("powerai/facebook-post-search-scraper", _se_fb_powerai),
        ("scrapeforge/facebook-search-posts", _se_fb_scrapeforge),
    ],
    "linkedin": [
        (_env0("AD_SCOUT_LI_SEARCH_ACTOR", "harvestapi/linkedin-post-search"), _se_li_harvest),
        ("datadoping/linkedin-posts-search-scraper", _se_li_datadoping),
        ("lofomachines/linkedin-post-search-scraper", _se_li_lofo),
    ],
    "meta": [(META_LISTEN_ACTOR, _se_meta_listen)],
}


def content_search(query, net, since=None, cap=30, market=None):
    """Najde organiku na téma přes KEYWORD SEARCH (ne hashtag, ne watchlist) — obsah neuteče,
    i když nikdo nedal hashtag. net: youtube/tiktok/instagram/facebook/linkedin/meta(FB+IG naráz).

    `market` (např. „cz") = geo-cílení: LOKÁLNÍ obsah má PŘEDNOST (TikTok `proxyCountryCode` servíruje
    jako z dané země, jinak vrací globálně nejpopulárnější = cizí jazyk). EN doplněk se volá BEZ marketu
    (globálně). Fallback chain per síť; výstup filtruje `_lang_ok` (CZ/SK/EN). `since` = volitelná pojistka."""
    if not query:
        return None
    net = _NET_ALIAS.get((net or "").lower(), (net or "").lower())
    chain = SEARCH_CHAINS.get(net)
    if not chain:
        return None
    cc = ((market or "").upper() or None)
    raw = run_chain(chain, {"q": query, "cap": cap, "since": since, "cc": cc}, f"search:{net}")
    if not raw:
        return None
    out = []
    for it in raw:
        c = _norm_search(it, net if net != "meta" else "facebook")
        if not c:
            continue
        if net == "meta":  # u meta aktoru vezmi síť z položky, když ji nese
            c["sit"] = str(it.get("platform") or it.get("net") or "facebook").lower()
        if not _lang_ok(c.get("nm")):  # zahoď cizojazyčný šum
            continue
        if _is_content_junk(c.get("nm"), c.get("kdo"), c.get("url")):  # bazar/zprávy ven
            continue
        out.append(c)
    return out or None
