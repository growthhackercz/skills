#!/usr/bin/env python3
"""competitor-tracker — provider Meta Ad Library (Apify, VYMĚNITELNÝ).
Actor: curious_coder~facebook-ads-library-scraper přes run-sync-get-dataset-items
(synchronně, 1 HTTP call na značku). Bez externích závislostí (stdlib urllib).

Normalizovaná reklama (společné schéma pro diff_engine + board):
  {advertiser, hook, full_copy, cta, offer, destination, days_running, started,
   ad_archive_id, is_active, creative_hash}

creative_hash = stabilní identita KREATIVY (ne placementu) — ad_archive_id se mění
per placement/duplikace, hash textu ne. Diff jede přes hash (noise-engineering #1).
Swap providera = implementuj stejný povrch: pull(brand_query, country, cap) -> list[ad]."""
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ACTOR = "curious_coder~facebook-ads-library-scraper"       # vyžaduje count >= 10
ACTOR_FALLBACK = "apify~facebook-ads-scraper"              # bohatší schéma (reachEstimate/spend)
MIN_CAP = 10                                               # pilot 2026-07-10: curious_coder odmítá < 10
BASE = "https://api.apify.com/v2"
MAX_PROVIDER_BYTES = 25_000_000


def _cc_variable(name):
    """Control Center proměnné (Nastavení -> Integrace) — store má přednost před env."""
    try:
        sys.path.insert(0, "/home/node/.openclaw/cs-skills/_lib")
        from cc_credentials import get_variable  # type: ignore
        return (get_variable(name) or "").strip()
    except Exception:
        return ""


def token():
    return (_cc_variable("APIFY_API_KEY") or os.environ.get("APIFY_API_KEY")
            or os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN", "")).strip()


def actor_chain():
    return [ACTOR, ACTOR_FALLBACK]


def normalize_facebook_page(value):
    """Return a safe Facebook page URL and optional numeric page ID."""
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("Facebooková stránka nesmí být prázdná.")
    if raw.isdigit():
        return f"https://www.facebook.com/{raw}", raw
    if "://" not in raw:
        if not re.fullmatch(r"[A-Za-z0-9._-]{2,100}", raw.lstrip("@")):
            raise ValueError("Neplatný Facebook handle nebo page ID.")
        return f"https://www.facebook.com/{raw.lstrip('@')}", ""
    try:
        parsed = urllib.parse.urlsplit(raw)
    except ValueError:
        raise ValueError("Neplatná URL Facebook stránky.") from None
    host = (parsed.hostname or "").lower()
    if (parsed.scheme.lower() not in ("http", "https") or parsed.username is not None
            or parsed.password is not None or not (host == "facebook.com" or host.endswith(".facebook.com"))):
        raise ValueError("Je povolená jen veřejná http(s) URL na facebook.com.")
    page_id = parsed.path.strip("/").split("/")[-1]
    return raw, page_id if page_id.isdigit() else ""


def monthly_usage_usd(timeout=20):
    """Reálná měsíční útrata na Apify (USD) — podklad pro bezpečnostní práh skillu
    (watchlist caps.apify_monthly_usd). Čte oficiální endpoint /v2/users/me/limits.
    Vrací {"used": float|None, "apify_max": float|None} nebo None (bez klíče / výpadek).
    Token jde výhradně v hlavičce — nikdy do URL ani do logu."""
    t = token()
    if not t:
        return None
    try:
        req = urllib.request.Request(f"{BASE}/users/me/limits",
                                     headers={"Authorization": "Bearer " + t})
        d = (json.load(urllib.request.urlopen(req, timeout=timeout)) or {}).get("data") or {}
        cur, lim = d.get("current") or {}, d.get("limits") or {}
        used = cur.get("monthlyUsageUsd")
        mx = lim.get("maxMonthlyUsageUsd")
        used_value = float(used) if used is not None else None
        max_value = float(mx) if mx is not None else None
        if used_value is None or not math.isfinite(used_value) or used_value < 0:
            return None
        if max_value is not None and (not math.isfinite(max_value) or max_value < 0):
            max_value = None
        return {"used": used_value, "apify_max": max_value}
    except Exception as e:
        print(f"[provider] útrata Apify nedostupná: {e}", file=sys.stderr)
        return None


def build_input(query, country, cap, status="active"):
    """query = název stránky/značky pro keyword search NEBO celá Ad Library URL."""
    if str(query).lower().startswith(("http://", "https://")):
        url, _ = normalize_facebook_page(query)
    else:
        q = urllib.parse.quote_plus(query)
        url = ("https://www.facebook.com/ads/library/"
               f"?active_status={status}&ad_type=all&country={country}"
               f"&q={q}&search_type=keyword_unordered&media_type=all")
    return {"urls": [{"url": url}], "count": cap,
            "scrapePageAds.activeStatus": status,
            "scrapePageAds.countryCode": country,
            "scrapePageAds.sortBy": "impressions_desc",
            "scrapeAdDetails": False}


class SourceError(RuntimeError):
    """Selhání zdroje — klientská (česká) zpráva v args[0], technický detail jde na stderr."""


def _run_actor(actor, inp, cap, timeout):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+~[A-Za-z0-9_.-]+", str(actor or "")):
        raise SourceError(f"Neplatné ID Apify actoru: {actor!r}.")
    access_token = token()
    if not access_token:
        raise SourceError("Chybí APIFY_API_KEY; placený zdroj nespouštím.")
    # token v hlavičce, NE v URL (nesmí prosakovat do access logů / tracebacků)
    actor_path = urllib.parse.quote(actor, safe="~")
    # `limit` bounds the returned page only. `maxItems` is the Apify billing
    # guard for pay-per-result actors, so both must follow the validated cap.
    url = f"{BASE}/acts/{actor_path}/run-sync-get-dataset-items?" + urllib.parse.urlencode({
        "limit": cap,
        "maxItems": cap,
    })
    req = urllib.request.Request(url, data=json.dumps(inp).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + access_token}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw_body = response.read(MAX_PROVIDER_BYTES + 1)
        if len(raw_body) > MAX_PROVIDER_BYTES:
            raise SourceError("Zdroj vrátil příliš velkou odpověď; data z bezpečnostních důvodů nezpracovávám.")
        d = json.loads(raw_body)
    except urllib.error.HTTPError as e:
        body = ""
        try: body = e.read().decode("utf-8", "ignore")[:300]
        except Exception: pass
        print(f"[provider] {actor} HTTP {e.code}: {body}", file=sys.stderr)
        raise SourceError(f"Zdroj reklam tento týden nevrátil data (HTTP {e.code}).")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"[provider] {actor} síťová chyba: {e}", file=sys.stderr)
        raise SourceError("Zdroj reklam je momentálně nedostupný (síťová chyba).")
    except json.JSONDecodeError as e:
        print(f"[provider] {actor} vrátil neplatný JSON: {e}", file=sys.stderr)
        raise SourceError("Zdroj reklam vrátil nečitelnou odpověď.")
    if isinstance(d, dict):
        d = d.get("items") or []
    items = d if isinstance(d, list) else []
    # fallback actor (apify~facebook-ads-scraper) balí reklamy do obálky {inputUrl, results:[...], totalCount}
    # -> rozbal; prázdné results = legit „neinzeruje", NE jedna falešná kreativa z obálky
    if items and all(isinstance(x, dict) and "results" in x and not x.get("snapshot") for x in items):
        items = [r for x in items for r in (x.get("results") or []) if isinstance(r, dict)]
    # actor umí vrátit chybu jako datasetovou položku — to je selhání, ne výsledek
    if items and isinstance(items[0], dict) and "error" in items[0] and len(items[0]) <= 3 \
            and not items[0].get("ad_archive_id") and not items[0].get("adArchiveID"):
        print(f"[provider] {actor} error item: {str(items[0])[:200]}", file=sys.stderr)
        raise SourceError("Zdroj reklam vrátil chybu místo dat.")
    return items


def pull(query, country="CZ", cap=50, status="active", timeout=600):
    """Spustí actor synchronně, vrátí RAW list reklam. Primár = levný curious_coder
    (min. cap 10), při selhání auto-fallback na oficiální apify~facebook-ads-scraper
    (degradace per zdroj — run nikdy nespadne kvůli jednomu aktoru)."""
    cap = max(cap, MIN_CAP)
    u = build_input(query, country, cap, status)
    try:
        return _run_actor(ACTOR, u, cap, timeout)
    except RuntimeError as e:
        print(f"[provider] primár selhal -> fallback {ACTOR_FALLBACK}", file=sys.stderr)
        # input schéma fallbacku OVĚŘENO živě 2026-07-10 (startUrls+resultsLimit; activeStatus je v jeho schématu)
        return _run_actor(ACTOR_FALLBACK, {"startUrls": u["urls"], "resultsLimit": cap,
                                           "activeStatus": status}, cap, timeout)


# ---- normalizace (pole ověřená ze scale-ads pilotu; actor schéma může driftovat) ----

def _snap(ad): return ad.get("snapshot") or {}


def _clean_tpl(s):
    """Odstraní prosáklé šablonové proměnné dynamických reklam ({{product.brand}} apod.) z textu."""
    return re.sub(r"\s+", " ", re.sub(r"\{\{[^}]*\}\}", "", s or "")).strip()


def _creative_url(s):
    """Náhled kreativy (obrázek / náhled videa) ze snapshotu — thumbnail v reportu.
    Schéma-tolerantní (curious_coder i oficiální actor); karusel = první karta."""
    def pick(d):
        if not isinstance(d, dict):
            return ""
        return (d.get("original_image_url") or d.get("resized_image_url") or d.get("originalImageUrl")
                or d.get("resizedImageUrl") or d.get("video_preview_image_url") or d.get("videoPreviewImageUrl")
                or d.get("image_url") or d.get("imageUrl") or "")
    for coll in (s.get("images"), s.get("videos"), s.get("cards")):
        for it in (coll or []):
            u = pick(it)
            if u:
                return u
    return pick(s)


def _body_text(ad):
    s = _snap(ad); b = s.get("body")
    t = b.get("text") if isinstance(b, dict) else (b if isinstance(b, str) else None)
    if not t:
        for c in s.get("cards") or []:
            cb = c.get("body")
            if isinstance(cb, dict): cb = cb.get("text")
            if cb: t = cb; break
    return (t or "").strip()


def _hook(body):
    for line in (body or "").splitlines():
        s = line.strip()
        if len(s) >= 3: return s[:200]
    return (body or "")[:200]


def _offer(ad):
    s = _snap(ad)
    for k in ("title", "link_description", "caption", "linkDescription"):
        v = s.get(k)
        if isinstance(v, dict): v = v.get("text")
        if v and str(v).strip(): return str(v).strip()[:160]
    for c in s.get("cards") or []:
        for k in ("title", "link_description"):
            v = c.get(k)
            if v and str(v).strip(): return str(v).strip()[:160]
    return ""


def _eu_reach(ad):
    """EU dosah z DSA transparentnosti (Meta ho v EU per reklama ukazuje!).
    Actor schéma driftuje -> zkus víc cest (curious_coder snake_case i oficiální camelCase),
    fail-open na ''. Vrací int (dolní mez rozsahu)."""
    cands = [ad.get("eu_total_reach"), ad.get("euTotalReach"), ad.get("reachEstimate"),
             (ad.get("aaa_info") or {}).get("eu_total_reach") if isinstance(ad.get("aaa_info"), dict) else None,
             (ad.get("aaaInfo") or {}).get("euTotalReach") if isinstance(ad.get("aaaInfo"), dict) else None,
             (_snap(ad).get("eu_total_reach")),
             (ad.get("impressions_with_index") or {}).get("impressions_text") if isinstance(ad.get("impressions_with_index"), dict) else None,
             (ad.get("impressionsWithIndex") or {}).get("impressionsText") if isinstance(ad.get("impressionsWithIndex"), dict) else None,
             ad.get("reach_estimate")]
    for v in cands:
        if v in (None, "", 0): continue
        if isinstance(v, (int, float)): return int(v)
        # textové hodnoty umí být „12K", „1.88M", „10K-15K" (bereme dolní mez rozsahu)
        m = re.search(r"([\d][\d\s.,]*)\s*([KkMm])?", str(v))
        if m:
            mult = {"k": 1_000, "m": 1_000_000}.get((m.group(2) or "").lower(), 1)
            try: return int(float(m.group(1).replace(" ", "").replace(",", "").rstrip(".")) * mult)
            except ValueError: continue
    return ""


def _epoch(v):
    """Epoch sekundy z int NEBO ISO stringu ('2026-01-05T08:00:00.000Z' — oficiální actor)."""
    if isinstance(v, (int, float)) and v: return int(v)
    if isinstance(v, str) and v:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", v)
        if m:
            import calendar
            return calendar.timegm((int(m.group(1)), int(m.group(2)), int(m.group(3)), 0, 0, 0))
        try: return int(float(v)) or None
        except ValueError: return None
    return None


def _days(ad, now=None):
    now = now or int(time.time())
    start = _epoch(ad.get("start_date") or ad.get("startDate") or ad.get("startDateFormatted"))
    end = _epoch(ad.get("end_date") or ad.get("endDate") or ad.get("endDateFormatted"))
    if not start: return None, ""
    return max(0, ((end or now) - start) // 86400), time.strftime("%Y-%m-%d", time.gmtime(start))


def _norm_ws(s): return re.sub(r"\s+", " ", (s or "").lower()).strip()


def creative_hash(body, offer, cta, dest, ad_id):
    """Identita kreativy. Prázdná kreativa (image-only bez copy) -> fallback na ad_id
    (žádné falešné slučování všech bez-textových reklam do jedné)."""
    key = "|".join(_norm_ws(x) for x in (body[:400], offer, cta, dest))
    if not key.strip("|"):
        return "id:" + str(ad_id)
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def normalize(ad, now=None):
    s = _snap(ad); body = _body_text(ad)
    days, started = _days(ad, now)
    dest = s.get("link_url") or s.get("linkUrl") \
        or next((c.get("link_url") or c.get("linkUrl") for c in s.get("cards") or []
                 if c.get("link_url") or c.get("linkUrl")), "")
    cta = (s.get("cta_text") or s.get("ctaText") or "").strip()
    off = _offer(ad)
    aid = ad.get("ad_archive_id") or ad.get("adArchiveID") or ad.get("adArchiveId") or ""
    active = ad.get("is_active") if ad.get("is_active") is not None else ad.get("isActive")
    return {"advertiser": s.get("page_name") or s.get("pageName") or ad.get("page_name") or ad.get("pageName") or "",
            "hook": _hook(_clean_tpl(body)), "full_copy": _clean_tpl(body)[:600], "cta": cta, "offer": off,
            "destination": dest or "", "days_running": days if days is not None else "",
            "started": started, "ad_archive_id": aid, "eu_reach": _eu_reach(ad),
            "is_active": bool(active) if active is not None
            else (ad.get("end_date") in (None, "", 0)),
            "creative_url": _creative_url(s),
            "ad_library_url": f"https://www.facebook.com/ads/library/?id={aid}" if aid else "",
            "creative_hash": creative_hash(body, off, cta, dest, aid)}


def _audience(ad):
    """Cílení z EU transparentnosti (aaa_info) — jen když je detail scrapnutý."""
    aaa = ad.get("aaa_info") or {}
    if not isinstance(aaa, dict) or not aaa:
        return None
    age = aaa.get("age_audience") or {}
    locs = [l.get("name") for l in aaa.get("location_audience") or [] if isinstance(l, dict) and not l.get("excluded")]
    out = {"gender": aaa.get("gender_audience") or "", "age_min": age.get("min"), "age_max": age.get("max"),
           "locations": locs[:5]}
    return out if any(v for v in out.values()) else None


def enrich_details(query, country="CZ", deep=10, timeout=420):
    """Detail scrape TOP-N reklam značky (EU dosah + cílení žijí JEN na detailu — pilot
    2026-07-10; permalink ?id= actor neumí, funguje search dotaz s scrapeAdDetails=True
    řazený podle impresí). Vrací {ad_archive_id: {eu_reach, audience}}. 1 actor call."""
    n = max(int(deep), MIN_CAP)
    inp = build_input(query, country, n)
    inp["scrapeAdDetails"] = True
    try:
        items = _run_actor(ACTOR, inp, n, timeout)
    except RuntimeError as e:
        print(f"[provider] enrich selhal ({e}) -> výstup pokračuje bez EU dosahu", file=sys.stderr)
        raise SourceError("Detail reklam s dosahem v EU se nepodařilo načíst.") from e
    out = {}
    for ad in items:
        aid = str(ad.get("ad_archive_id") or ad.get("adArchiveID") or ad.get("adArchiveId") or "")
        if not aid:
            continue
        out[aid] = {"eu_reach": _eu_reach(ad), "audience": _audience(ad)}
    return out


# ---- brand filter (keyword search je fuzzy — přitáhne cizí inzerenty) ----
_STOP = {"the", "a", "an", "official", "my", "get", "shop", "store"}


def brand_token(name):
    toks = [t for t in re.split(r"[^a-z0-9]+", (name or "").lower()) if t]
    for t in toks:
        if t not in _STOP and len(t) >= 3: return t
    return toks[0] if toks else ""


def find_page(name, web="", country="CZ", cap=50, timeout=600):
    """Dohledá facebookovou stránku konkurenta v knihovně reklam: hledání podle jména ->
    seskupení podle page_id -> skóre = kolik reklam vede na doménu jeho webu (+ shoda jména).
    Vrací kandidáty od nejlepšího: [{page_id, page_name, page_url, ads, to_domain, likes, shoda}].
    Bez kandidáta s reklamou na web = nic neinzeruje / jiný trh — řekne se to, nehádá se."""
    dom = re.sub(r"^https?://(www\.)?", "", (web or "").lower()).split("/")[0]
    tok = brand_token(name)
    raw = pull(name, country=country, cap=cap, timeout=timeout)
    pages = {}
    for ad in raw:
        s = _snap(ad)
        pid = str(ad.get("page_id") or s.get("page_id") or "")
        if not re.fullmatch(r"\d{3,30}", pid):
            continue
        p = pages.setdefault(pid, {"page_id": pid, "page_name": s.get("page_name") or ad.get("page_name") or "",
                                   "page_url": s.get("page_profile_uri") or "", "ads": 0, "to_domain": 0,
                                   "likes": s.get("page_like_count") or ""})
        p["ads"] += 1
        dest = s.get("link_url") or s.get("linkUrl") or ""
        ddom = re.sub(r"^https?://(www\.)?", "", dest.lower()).split("/")[0]
        if dom and ddom and (ddom == dom or ddom.endswith("." + dom) or dom.endswith("." + ddom)):
            p["to_domain"] += 1
    out = list(pages.values())
    for p in out:
        p["shoda"] = p["to_domain"] * 3 + (2 if tok and tok in p["page_name"].lower() else 0)
        if p["page_id"]:
            # Do not trust an actor-supplied profile URL; the numeric page ID
            # gives us a canonical Facebook destination.
            p["page_url"] = f"https://www.facebook.com/{p['page_id']}"
    return sorted(out, key=lambda p: (-p["shoda"], -p["ads"]))


def filter_to_brand(rows, name):
    """(kept, dropped) — nech JEN reklamy inzerenta značky. Žádný fallback „když je shod málo,
    nech všechno": u obecného jména (ZWILLING = německy „dvojče") tak 12 cizích reklam
    hrálo roli konkurenta. Nula shod = poctivé prázdno + volající to ohlásí (ověřit název stránky)."""
    tok = brand_token(name)
    if not tok: return rows, 0
    kept = [r for r in rows if tok in (r.get("advertiser") or "").lower()]
    return kept, len(rows) - len(kept)
