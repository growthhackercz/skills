#!/usr/bin/env python3
"""competitor-tracker — placené doplňkové zdroje (Apify) s FALLBACK CHAINY.

Každý zdroj = řetěz actorů (primár + záloha). Actor umře/přejmenuje se? -> zkusí se
další v řadě; bere se PRVNÍ použitelný výsledek. Řetěz je přepsatelný přes Control
Center proměnnou / env (COMP_<ZDROJ>_ACTORS = "actor1,actor2") — vyměníš actor na
fleetu BEZ nového image (stejný princip jako token přes _cc_variable).

Klíčové: rozlišujeme TŘI stavy, aby tracker nikdy nehlásil falešné ticho
(„konkurence zaspala") místo rozbitého scraperu:
  • OK      — zdroj vrátil použitelná data                    -> normální diff
  • PRÁZDNO — zdroj čistě odpověděl, ale nic (0 reklam apod.) -> žádná změna (legit)
  • STALE   — všechny actory selhaly NEBO vrátily neznámý       -> SourceError ->
              formát (možná změna scraperu)                     tracker: „zdroj
                                                                 dočasně nedostupný"

reviews  = Google Maps recenze (primár compass~crawler-google-places) — MĚSÍČNĚ.
google   = Google Ads Transparency (primár solidcode~ads-transparency-scraper) —
           AGREGÁT per značka (počty/longevita/formáty; bez copy). TÝDNĚ.
linkedin = LinkedIn Ad Library (primár ivanvs~linkedin-ad-library-scraper) — B2B:
           imprese po zemích. TÝDNĚ.
serp     = placené výsledky Googlu na BRANDOVÁ slova klienta (apify~google-search-
           scraper) — „kdo inzeruje na moje jméno". MĚSÍČNĚ, per watchlist.

Normalizéry jsou SCHÉMATOLERANTNÍ (zkoušejí víc názvů polí) — záloha vrátí data v
lehce jiném tvaru a stejně se přečtou; co přečíst nejde, spadne poctivě do STALE,
nikdy do tichého prázdna."""
import datetime, os, re, sys
import provider_ads  # sdílený _run_actor + token + SourceError

SourceError = provider_ads.SourceError

DEFAULT_CHAINS = {
    "reviews": ["compass~crawler-google-places", "beatanalytics~google-maps-reviews-scraper"],
    "google_ads": ["solidcode~ads-transparency-scraper", "s-r~google-ads-transparency"],
    "linkedin_ads": ["ivanvs~linkedin-ad-library-scraper", "unseenuser~LinkedIn-ads"],
    "youtube": ["streamers~youtube-scraper", "grow_media~youtube-channel-video-scraper"],
    "facebook": ["apify~facebook-posts-scraper", "curious_coder~facebook-post-scraper"],
    "instagram": ["apify~instagram-profile-scraper", "instagram-scraper~fast-instagram-post-scraper"],
    "linkedin_posts": ["harvestapi~linkedin-company-posts", "data-slayer~linkedin-company-posts-scraper"],
    "serp": ["apify~google-search-scraper"],
}

CHAIN_OVERRIDE_KEYS = {
    "reviews": "COMP_REVIEWS_ACTORS",
    "google_ads": "COMP_GOOGLE_ACTORS",
    "linkedin_ads": "COMP_LINKEDIN_ACTORS",
    "youtube": "COMP_YOUTUBE_ACTORS",
    "facebook": "COMP_FACEBOOK_ACTORS",
    "instagram": "COMP_INSTAGRAM_ACTORS",
    "linkedin_posts": "COMP_LINKEDIN_POSTS_ACTORS",
    "serp": "COMP_SERP_ACTORS",
}

_ACTOR_ID = re.compile(r"^[A-Za-z0-9_.-]+~[A-Za-z0-9_.-]+$")


def _chain(defaults, override_key):
    """Vyřeš řetěz actorů: CC proměnná / env (COMP_*_ACTORS = "a,b") vyhrává nad
    zabudovaným defaultem. Prázdné položky se zahazují, pořadí = priorita."""
    ov = provider_ads._cc_variable(override_key) or os.environ.get(override_key, "")
    ids = [x.strip() for x in ov.split(",") if x.strip()]
    invalid = [actor for actor in ids if not _ACTOR_ID.fullmatch(actor)]
    if invalid:
        raise SourceError(
            f"Neplatné ID Apify actoru v {override_key}: {', '.join(invalid)}. "
            "Použijte tvar vlastnik~nazev-actoru."
        )
    return ids or list(defaults)


def configured_chain(source):
    """Return the exact configured fallback chain for planning and execution."""
    if source not in DEFAULT_CHAINS:
        raise SourceError(f"Neznámý placený zdroj: {source}.")
    return _chain(DEFAULT_CHAINS[source], CHAIN_OVERRIDE_KEYS[source])


def _g(d, *keys, default=None):
    """První neprázdná hodnota z kandidátních klíčů (schéma-tolerance napříč actory)."""
    if isinstance(d, dict):
        for k in keys:
            v = d.get(k)
            if v not in (None, ""):
                return v
    return default


def _run_chain(chain, input_of, normalize_of, usable_of, cap, timeout=300):
    """Zkusí actory v pořadí. Vrací normalizovaný objekt (OK i legit PRÁZDNO).

    ⚠️ ZÁLOHA SE VOLÁ JEN PŘI SELHÁNÍ, NE PŘI PRÁZDNÉ ODPOVĚDI.

    Dřív tu byla jen podmínka `usable_of`, což je test „přišla nějaká data".
    Jenže konkurent, který zrovna neinzeruje, je **běžný stav** — a prázdná
    odpověď primáru tak spouštěla celý zbytek řetězu. Dva důsledky, oba špatné:

      1. u každého klidného konkurenta se každý týden platily oba actory,
      2. když pak záloha spadla, `raise` přebil čistou odpověď primáru
         a zdroj se hlásil jako nedostupný, přestože primár odpověděl v pořádku.

    Proto se rozlišuje ODPOVĚDĚL (actor doběhl a data šla přečíst) od
    POUŽITELNÝ (jsou v nich nějaké položky). Řetěz končí u prvního, který
    **odpověděl** — ať už něco našel, nebo poctivě nic.

    Konce:
      • actor odpověděl (i prázdnem)               -> vrať jeho objekt
      • některý vrátil syrová data, ale nečitelná  -> STALE (změna schématu)
      • všichni spadli na chybě                    -> STALE (poslední chyba)
    """
    raised = None
    saw_raw = False
    for actor in chain:
        try:
            raw = provider_ads._run_actor(actor, input_of(actor), cap, timeout)
        except SourceError as e:
            raised = e
            print(f"[extras] {actor} selhal, zkouším další v řetězu: {e}", file=sys.stderr)
            continue

        try:
            obj = normalize_of(actor, raw)
        except Exception as exc:
            saw_raw = True
            print(f"[extras] {actor} normalizace selhala, zkouším další v řetězu: {exc}", file=sys.stderr)
            continue

        if usable_of(obj):
            return obj                      # data → hotovo

        if not raw:
            return obj                      # actor doběhl a čistě nic nenašel → legit ticho,
                                            # zálohu NEVOLÁME (šetří kredity i falešné STALE)

        # Actor něco vrátil, ale normalizér z toho nic nedostal → nejspíš se
        # změnilo schéma. Tady zálohu zkusit chceme, ta může umět jiný tvar.
        saw_raw = True
        print(f"[extras] {actor} vrátil data v neznámém tvaru, zkouším další v řetězu",
              file=sys.stderr)

    if saw_raw:
        raise SourceError("Zdroj odpověděl v neočekávaném formátu (možná změna scraperu) — "
                          "ponechávám poslední známý stav.")
    if raised is not None:
        raise raised
    raise SourceError("Žádný actor v řetězu neodpověděl.")


# ================================ recenze (Raw Diet) ================================

def _reviews_from(items):
    out = []
    for r in items or []:
        if not isinstance(r, dict):
            continue
        stars = _g(r, "stars", "rating", "reviewRating", "score", "starRating")
        date = str(_g(r, "publishedAtDate", "publishAt", "publishedAt", "date",
                      "reviewDate", "publishedAtText", default=""))[:10]
        text = (_g(r, "text", "textTranslated", "reviewText", "snippet", "review", default="") or "").strip()[:400]
        out.append({"stars": stars, "date": date, "text": text})
    return out


def _norm_reviews(actor, raw):
    if not raw:
        return None
    today = datetime.date.today().isoformat()
    first = raw[0] if isinstance(raw[0], dict) else {}
    # (A) tvar „místo s vnořenými recenzemi" (compass~crawler-google-places)
    if isinstance(first, dict) and ("reviews" in first or "totalScore" in first or "reviewsCount" in first):
        revs = _reviews_from(first.get("reviews") or [])
        return {"place": _g(first, "title", "name", default=""),
                "rating": _g(first, "totalScore", "rating", "averageRating"),
                "count": _g(first, "reviewsCount", "reviewCount", "count"),
                "maps_url": _g(first, "url", "placeUrl", "mapsUrl", default=""),
                "place_id": _g(first, "placeId", "place_id", default=""),
                "website": _g(first, "website", default=""),
                "reviews": revs, "fetched": today}
    # (B) plochý seznam recenzí (name-based zálohy) — agregáty dopočítáme
    revs = _reviews_from(raw)
    if not any(r["stars"] is not None or r["text"] for r in revs):
        return None  # syrová data bez čitelné recenze -> _run_chain to vyhodnotí jako STALE
    nums = [float(r["stars"]) for r in revs if isinstance(r["stars"], (int, float))]
    return {"place": "", "rating": round(sum(nums) / len(nums), 1) if nums else None,
            "count": len(revs), "reviews": revs, "fetched": today}


def _dom(u):
    """Doména bez schématu/www (pro shodu webu značky s webem místa na Mapách)."""
    return re.sub(r"^https?://(www\.)?", "", str(u or "").strip().lower()).split("/")[0]


def _pick_places(raw, brand_name, web):
    """Z kandidátů na Mapách vybere to správné místo — NE slepě první výsledek.
    Obecné jméno („AMC") jinak trefí cizí byznys (autobazar místo nádobí). Skóre:
    +3 web místa == web značky · −2 jiný web než značka · +2 jméno značky v názvu.
    Bere se jen skóre ≥ 2; místo bez hodnocení se zahazuje. Vrací [nejlepší] nebo [] (legit prázdno); plochý
    seznam recenzí (tvar B) propouští beze změny."""
    if not isinstance(raw, list) or not raw or not isinstance(raw[0], dict):
        return raw
    if not any(("totalScore" in p or "reviewsCount" in p or "title" in p) for p in raw if isinstance(p, dict)):
        return raw  # tvar B (ploché recenze) — nic nevybíráme
    bd, bn = _dom(web), (brand_name or "").strip().lower()
    best, best_s = None, -1
    for p in raw:
        if not isinstance(p, dict):
            continue
        rating, cnt = _g(p, "totalScore", "rating", "averageRating"), _g(p, "reviewsCount", "reviewCount", "count")
        if rating in (None, "", 0) or not cnt:
            continue  # bez hodnocení = nepoužitelné (žádné „None★")
        s = 0
        pw = _dom(_g(p, "website", default=""))
        if bd and pw == bd: s += 3
        elif bd and pw and pw != bd: s -= 2   # jiný web než značka = cizí byznys se stejným slovem v názvu
        if bn and bn in str(_g(p, "title", "name", default="")).lower(): s += 2
        if s > best_s:
            best, best_s = p, s
    return [best] if best and best_s >= 2 else []   # bez shody webu/jména = raději nic


def _in_reviews(brand_name, location, cap_reviews, place=None):
    def _inp(actor):
        if actor.startswith("compass~crawler-google-places"):
            base = {"maxReviews": cap_reviews, "reviewsSort": "newest", "language": "cs",
                    "scrapeReviewsPersonalData": False}
            if place:   # potvrzené místo (URL z Map nebo placeId) -> žádné hádání
                return {**base, **({"startUrls": [{"url": place}]} if str(place).startswith("http")
                                    else {"placeIds": [place]})}
            return {**base, "searchStringsArray": [brand_name], "locationQuery": location,
                    "maxCrawledPlacesPerSearch": 3}   # 3 kandidáti -> _pick_places vybere správný
        # obecná name-based záloha (beatanalytics apod.)
        return {"searchQueries": [brand_name], "searchStringsArray": [brand_name],
                "maxPlacesPerSearch": 1, "maxReviewsPerPlace": cap_reviews, "maxReviews": cap_reviews,
                "language": "cs", "country": (location[:2] or "CZ").upper(), "reviewsSort": "newest"}
    return _inp


def reviews(brand_name, location="Czechia", cap_reviews=40, place=None, web=None):
    """dict|None. None = legit prázdno; SourceError = STALE (výpadek zdroje).
    place = potvrzené místo (URL/placeId z `find-place`); bez něj se vybírá podle webu a jména."""
    chain = configured_chain("reviews")
    norm = (lambda actor, raw: _norm_reviews(actor, raw if place else _pick_places(raw, brand_name, web)))
    return _run_chain(chain, _in_reviews(brand_name, location, cap_reviews, place), norm,
                      lambda o: bool(o and (o.get("place") or o.get("count") or o.get("reviews"))),
                      cap=3)


def search_places(brand_name, location="Czechia", web="", n=3):
    """Kandidáti míst na Mapách pro POTVRZENÍ uživatelem při nastavení (jako find-ico u rejstříku).
    Vrací [{title, address, category, rating, count, website, url, placeId, shoda}] seřazené od nejlepšího."""
    chain = configured_chain("reviews")[:1]
    inp = {"searchStringsArray": [brand_name], "locationQuery": location, "maxCrawledPlacesPerSearch": n,
           "maxReviews": 0, "language": "cs"}
    raw = provider_ads._run_actor(chain[0], inp, n, 300) or []
    bd, bn, out = _dom(web), (brand_name or "").strip().lower(), []
    for p in raw:
        if not isinstance(p, dict):
            continue
        s = 0
        pw = _dom(_g(p, "website", default=""))
        if bd and pw == bd: s += 3
        elif bd and pw and pw != bd: s -= 2
        if bn and bn in str(_g(p, "title", "name", default="")).lower(): s += 2
        if _g(p, "totalScore", "rating") and _g(p, "reviewsCount", "reviewCount"): s += 1
        out.append({"title": _g(p, "title", "name", default=""), "address": _g(p, "address", default=""),
                    "category": _g(p, "categoryName", "category", default=""),
                    "rating": _g(p, "totalScore", "rating"), "count": _g(p, "reviewsCount", "reviewCount"),
                    "website": _g(p, "website", default=""), "url": _g(p, "url", "placeUrl", default=""),
                    "placeId": _g(p, "placeId", "place_id", default=""), "shoda": s})
    return sorted(out, key=lambda c: -c["shoda"])


def diff_reviews(prev, curr):
    """[(note)] — posun ratingu/počtu + čerstvé negativní recenze (doslovně = úhly pro nás)."""
    if not curr:
        return []
    notes = []
    # předchozí snímek bez hodnocení (špatně trefené místo) = žádná základna -> založit znovu, ne „None→4,4"
    if prev and prev.get("rating") is not None:
        dc = (curr.get("count") or 0) - (prev.get("count") or 0)
        dr = round((curr.get("rating") or 0) - (prev.get("rating") or 0), 1)
        if dc or dr:
            notes.append(f"recenze: {curr.get('rating')}★ ({'+' if dr > 0 else ''}{dr or '±0'}), "
                         f"{curr.get('count')} celkem ({'+' if dc >= 0 else ''}{dc} za měsíc)")
    else:
        notes.append(f"recenze založeny: {curr.get('place', '')} — {curr.get('rating')}★, {curr.get('count')} recenzí")
    if curr.get("rating") is None:
        return []   # místo bez hodnocení = nic nehlásit (žádné „None★")
    lows = [r for r in curr.get("reviews", []) if isinstance(r.get("stars"), (int, float))
            and r["stars"] <= 2 and len((r.get("text") or "").strip()) >= 25]
    for r in lows[:2]:
        notes.append(f"stížnost ({r['stars']}★): „{r['text'][:140]}“. Možný podnět pro Vaši reklamu.")
    return notes


# ========================= Google Ads Transparency (agregát) =========================

def _norm_google(actor, raw):
    today = datetime.date.today()
    creatives = []
    for x in raw or []:
        if not isinstance(x, dict):
            continue
        cid = _g(x, "creativeId", "creative_id", "id", "adId", default="")
        last = str(_g(x, "lastShown", "last_shown", "lastShownDate", "endDate", "end_date", default=""))[:10]
        first = str(_g(x, "firstShown", "first_shown", "startDate", "start_date", default=""))[:10]
        if not (cid or last or first):
            continue  # neparsovatelný řádek — nezapočítávej (jinak by 10× šum = „použitelné")
        days = _g(x, "approxDaysShown", "daysShown", "days", default="")
        fmt = _g(x, "adFormat", "format", "creativeType", "type", default="")
        try:
            fresh = (today - datetime.date.fromisoformat(last)).days <= 7
        except (ValueError, TypeError):
            fresh = False
        creatives.append({"id": cid, "format": fmt, "days": days, "first": first, "last": last, "active": fresh})
    act = [c for c in creatives if c["active"]]
    fm = {}
    for c in act:
        fm[c["format"]] = fm.get(c["format"], 0) + 1
    return {"fetched": today.isoformat(), "total_seen": len(creatives), "active": len(act), "formats": fm,
            "oldest_days": max((c["days"] for c in act if isinstance(c["days"], int)), default=0),
            "creatives": creatives[:200]}


def _in_google(query, region):
    def _inp(actor):
        if actor.startswith("solidcode~"):
            return {"searchQuery": query, "region": region, "maxResults": 50}
        if actor.startswith("s-r~") or "google-ads-transparency" in actor:
            # s-r bere doménu/hledaný výraz; ads_count místo maxResults
            return {"domain": query, "search": query, "region": region, "ads_count": 50}
        return {"searchQuery": query, "queries": [query], "region": region, "maxResults": 50, "maxItems": 50}
    return _inp


def google_ads(query, region="CZ", cap=50):
    """dict (i pro legit prázdno). SourceError = STALE."""
    chain = configured_chain("google_ads")
    return _run_chain(chain, _in_google(query, region), _norm_google,
                      lambda o: bool(o and o.get("total_seen")), cap)


def diff_google(prev, curr):
    if not curr:
        return []
    if not prev:
        return ([f"Google reklamy: {curr['active']} aktivních "
                 f"({', '.join(f'{v}× {k}' for k, v in curr['formats'].items()) or 'bez formátů'}), "
                 f"nejdéle {curr['oldest_days']} dní"] if curr["active"] else [])
    d = curr["active"] - prev.get("active", 0)
    if abs(d) >= 3 or (prev.get("active", 0) == 0) != (curr["active"] == 0):
        return [f"Google reklamy: {curr['active']} aktivních ({'+' if d >= 0 else ''}{d} oproti minule)"]
    return []


# ============================ LinkedIn Ad Library (B2B) ============================

def _norm_linkedin(actor, raw):
    today = datetime.date.today().isoformat()
    ads, imp_total, countries = [], 0, {}
    parsed = 0
    for x in raw or []:
        if not isinstance(x, dict):
            continue
        per = x.get("period") or {}
        start = _g(per, "start", default=_g(x, "startDate", "start", default=""))
        end = _g(per, "end", default=_g(x, "endDate", "end", default=""))
        title = (_g(x, "title", "headline", "adTitle", default="") or "")[:120]
        body = (_g(x, "body", "adBody", "description", "text", default="") or "")[:200]
        imp = ((x.get("totalImpressionParsed") or {}).get("estimatedMin")
               or _g(x, "impressionsMin", "estimatedMin", default=0) or 0)
        if not (title or body or start or end or imp):
            continue  # neparsovatelný řádek
        parsed += 1
        imp_total += imp
        for c in x.get("impressions") or []:
            if isinstance(c, dict):
                countries[c.get("country", "?")] = countries.get(c.get("country", "?"), 0) + (c.get("estimatedMin") or 0)
        ads.append({"title": title, "body": body, "start": start, "end": end,
                    "imp_min": imp, "active": bool(end) and str(end)[:10] >= today[:10]})
    top_c = sorted(countries.items(), key=lambda kv: -kv[1])[:3]
    return {"fetched": today, "count": parsed, "active": sum(1 for a in ads if a["active"]),
            "impressions_min": imp_total, "top_countries": top_c, "ads": ads}


def _in_linkedin(name):
    url = "https://www.linkedin.com/ad-library/search?keyword=" + name.replace(" ", "%20")
    def _inp(actor):
        if actor.startswith("ivanvs~"):
            return {"urls": [{"url": url}], "maxRecords": 25}
        if actor.startswith("unseenuser~"):
            return {"keywords": [name], "maxResults": 25}
        # memo23 / obecná name-based záloha
        return {"keywords": [name], "companies": [name], "maxItems": 25, "urls": [{"url": url}]}
    return _inp


def linkedin_ads(name, cap=25):
    """dict (i pro legit prázdno). SourceError = STALE."""
    chain = configured_chain("linkedin_ads")
    return _run_chain(chain, _in_linkedin(name), _norm_linkedin,
                      lambda o: bool(o and o.get("count")), cap)


def diff_linkedin(prev, curr):
    if not curr:
        return []
    if not prev:
        # mezeruj JEN číslo (ne celou větu) — jinak .replace sežere i větné čárky
        _n = lambda v: format(int(v or 0), ",").replace(",", " ")  # noqa: E731
        return ([f"LinkedIn reklamy: {curr['active']} aktivních, zobrazení nejméně {_n(curr['impressions_min'])}"
                 + (f" (top: {', '.join(f'{c} {_n(v)}' for c, v in curr['top_countries'])})"
                    if curr["top_countries"] else "")] if curr["count"] else [])
    d = curr["active"] - prev.get("active", 0)
    if abs(d) >= 2 or (prev.get("active", 0) == 0) != (curr["active"] == 0):
        return [f"LinkedIn reklamy: {curr['active']} aktivních ({'+' if d >= 0 else ''}{d} oproti minule)"]
    return []


# ===================== YouTube kanál konkurenta (organika) =====================

def _norm_youtube(actor, raw):
    out = []
    for x in raw or []:
        if not isinstance(x, dict):
            continue
        url = _g(x, "url", "videoUrl", "link", default="")
        title = (_g(x, "title", "videoTitle", "name", default="") or "")[:120]
        if not title:
            continue  # bez titulku = neparsovatelný řádek
        vid = _g(x, "id", "videoId", default="")
        if not vid and url:
            vid = (url.split("v=")[-1] if "v=" in url else url.rstrip("/").rsplit("/", 1)[-1])[:20]
        views = _g(x, "viewCount", "views", "numberOfViews", "viewCountInt", default=0) or 0
        if isinstance(views, str):
            m = re.search(r"[\d\s.,]+", views)
            views = int(re.sub(r"[^\d]", "", m.group()) or 0) if m else 0
        date = str(_g(x, "date", "publishedAt", "uploadDate", "publishedTimeText", default=""))[:10]
        out.append({"id": vid or (title[:20]), "title": title, "views": views, "date": date, "url": url})
    return out


def _in_youtube(channel_url, cap):
    """Vstupy ověřené proti aktuálním schématům actorů (2026-07-29).

    Dvě chyby, které tu byly a obě tiše rozbíjely YouTube vrstvu:
      • `sortingOrder` u streamers~ je řazení pro VYHLEDÁVÁNÍ. Pro kanál slouží
        `sortVideosBy` — se špatným polem se řadilo podle výchozího pořadí a
        nová videa mohla vypadnout mimo `maxResults`.
      • `videoType: "all"` u grow_media~ NENÍ povolená hodnota (jen `long`|`short`),
        takže záloha padala pokaždé. V kombinaci se starým chováním řetězu se
        pak kanál bez nových videí hlásil jako nedostupný zdroj každý týden.
    """
    def _inp(actor):
        if actor.startswith("streamers~"):
            return {"startUrls": [{"url": channel_url}], "maxResults": cap, "maxResultsShorts": 3,
                    "sortVideosBy": "newest"}
        # grow_media / obecná channel-URL záloha
        return {"channelUrls": [channel_url], "maxResults": cap + 3,
                "videoType": "long", "sortOrder": "latest"}
    return _inp


def youtube_channel(channel_url, cap=8):
    """list (i prázdný = legit). SourceError = STALE."""
    chain = configured_chain("youtube")
    obj = _run_chain(chain, _in_youtube(channel_url, cap), _norm_youtube,
                     lambda o: bool(o), cap + 3)
    return obj or []   # prázdný kanál = legit; _run_chain už kvůli tomu nevolá zálohu


def diff_youtube(prev_ids, videos):
    new = [v for v in videos if v["id"] not in set(prev_ids or [])]
    if not new:
        return []
    top = max(new, key=lambda v: v["views"] or 0)
    note = f"{len(new)} nových videí na YouTube — nejsledovanější: „{top['title']}“"
    if top.get("views"):
        note += f" ({top['views']:,} zhlédnutí)".replace(",", " ")
    return [(note, [v["url"] for v in new[:3]])]


# ================= Sociální sítě konkurenta (organika PER PROFIL) =================
# FB / IG / LinkedIn: nové příspěvky + engagement z KONKRÉTNÍHO profilu konkurenta (per-profile,
# ne keyword jako content-scout). Stejný chain vzor jako YouTube: primár + záloha, override přes
# COMP_FACEBOOK_ACTORS / COMP_INSTAGRAM_ACTORS / COMP_LINKEDIN_POSTS_ACTORS. Normalizace = dedikovaná
# pole per actor (nikdy generický extractor); None = neznámý tvar (zkusí se záloha), [] = legit prázdno.
# Všechny tři zdroje jsou placené; cenu ověř před během v aktuálním Apify účtu.

def _post(pid, url, text, date, likes=0, comments=0, shares=0, views=0):
    t = " ".join(str(text or "").split())
    def _i(v):
        try: return int(v or 0)
        except (TypeError, ValueError): return 0
    return {"id": str(pid or url or ""), "url": url or "", "text": t[:280], "date": str(date or ""),
            "likes": _i(likes), "comments": _i(comments), "shares": _i(shares), "views": _i(views)}


def _in_facebook(page_url, cap):
    def f(actor):
        if actor.startswith("apify~facebook-posts-scraper"):
            return {"startUrls": [{"url": page_url}], "resultsLimit": cap}
        return {"urls": [page_url], "count": cap}                 # curious_coder~facebook-post-scraper
    return f


def _norm_facebook(actor, raw):
    if not isinstance(raw, list): return None
    out = []
    for p in raw:
        if not isinstance(p, dict): continue
        pid, url = _g(p, "postId", "post_id", "id"), _g(p, "url", "postUrl", "post_url")
        if not (pid or url): continue
        out.append(_post(pid, url, _g(p, "text", "message", "caption", default=""),
                         _g(p, "time", "timestamp", "date", "publishedAt", default=""),
                         _g(p, "likes", "likesCount", "reactions_count", "reactionsCount", default=0),
                         _g(p, "comments", "commentsCount", "comments_count", default=0),
                         _g(p, "shares", "sharesCount", "shares_count", default=0),
                         _g(p, "viewsCount", "views", "play_count", default=0)))
    if not out and raw: return None      # data přišla, ale v neznámém tvaru -> záloha
    return out


def _in_instagram(handle, cap):
    h = str(handle).rstrip("/").split("/")[-1].lstrip("@")   # přijme handle i celou URL
    def f(actor):
        if actor.startswith("apify~instagram-profile-scraper"):
            return {"usernames": [h]}
        return {"instagramUsernames": [h], "postsPerProfile": cap}   # instagram-scraper~fast-instagram-post-scraper
    return f


def _norm_instagram(actor, raw):
    if not isinstance(raw, list): return None
    items, recognized = [], False
    for it in raw:
        if not isinstance(it, dict): continue
        if isinstance(it.get("latestPosts"), list):     # oficiální actor: profil + poslední posty
            recognized = True; items.extend(it["latestPosts"])
        else:
            items.append(it)                              # záložní actor: přímo posty
    out = []
    for p in items:
        if not isinstance(p, dict): continue
        code = _g(p, "shortCode", "shortcode", "code")
        pid = _g(p, "id", "pk") or code
        url = _g(p, "url") or (f"https://www.instagram.com/p/{code}/" if code else "")
        if not (pid or url): continue
        cap_ = p.get("caption")
        text = cap_.get("text", "") if isinstance(cap_, dict) else (cap_ or "")
        out.append(_post(pid, url, text, _g(p, "timestamp", "taken_at", "takenAt", default=""),
                         _g(p, "likesCount", "like_count", "likes", default=0),
                         _g(p, "commentsCount", "comment_count", "comments", default=0), 0,
                         _g(p, "videoViewCount", "play_count", "video_view_count", default=0)))
    if not out and raw and not recognized: return None
    return out


def _in_linkedin_posts(company_url, cap):
    def f(actor):
        if actor.startswith("harvestapi~"):
            return {"targetUrls": [company_url], "maxPosts": cap, "includeReposts": False}
        return {"companyUrls": [company_url], "maxPosts": cap}    # data-slayer~linkedin-company-posts-scraper
    return f


def _norm_linkedin_posts(actor, raw):
    if not isinstance(raw, list): return None
    out = []
    for p in raw:
        if not isinstance(p, dict): continue
        pid, url = _g(p, "id", "urn", "postUrn"), _g(p, "linkedinUrl", "url", "postUrl")
        if not (pid or url): continue
        eng = p.get("engagement") if isinstance(p.get("engagement"), dict) else {}
        posted = p.get("postedAt")
        date = posted.get("date") if isinstance(posted, dict) else _g(p, "postedAt", "date", "publishedAt", default="")
        out.append(_post(pid, url, _g(p, "content", "text", default=""), date,
                         _g(eng, "likes", "reactions", default=0) or _g(p, "likes", "reactionsCount", default=0),
                         _g(eng, "comments", default=0) or _g(p, "comments", "commentsCount", default=0),
                         _g(eng, "shares", "reposts", default=0) or _g(p, "shares", "repostsCount", default=0)))
    if not out and raw: return None
    return out


def facebook_posts(page_url, cap=10):
    """Příspěvky FB stránky konkurenta. list (i prázdný = legit). SourceError = STALE."""
    chain = configured_chain("facebook")
    return _run_chain(chain, _in_facebook(page_url, cap), _norm_facebook, lambda o: bool(o), cap + 3) or []


def instagram_posts(handle, cap=8):
    """Poslední posty IG profilu konkurenta. list (i prázdný = legit). SourceError = STALE."""
    chain = configured_chain("instagram")
    return _run_chain(chain, _in_instagram(handle, cap), _norm_instagram, lambda o: bool(o), cap + 3) or []


def linkedin_posts(company_url, cap=10):
    """Příspěvky LinkedIn company page konkurenta. list (i prázdný = legit). SourceError = STALE."""
    chain = configured_chain("linkedin_posts")
    return _run_chain(chain, _in_linkedin_posts(company_url, cap), _norm_linkedin_posts,
                      lambda o: bool(o), cap + 3) or []


def diff_social(prev_ids, posts, label):
    """Nové příspěvky od minulého snímku (podle id). Vrací [(note, links)] nebo []."""
    new = [p for p in posts if p["id"] not in set(prev_ids or [])]
    if not new:
        return []
    top = max(new, key=lambda p: (p["likes"] or 0) + (p["comments"] or 0))
    snip = (top["text"] or "").strip()
    snip = (snip[:70] + "…") if len(snip) > 70 else snip
    note = f"{len(new)} nových příspěvků na {label}"
    if snip:
        note += f" — nejvíc reakcí: „{snip}“"
    r = (top["likes"] or 0) + (top["comments"] or 0)
    if r:
        note += f" ({r:,} reakcí)".replace(",", " ")
    return [(note, [p["url"] for p in new[:3] if p["url"]])]


# ================= SERP brand-guard (kdo inzeruje na klientova slova) =================
# Oficiální apify~google-search-scraper = stabilní; 0 reklam je LEGIT odpověď (ne STALE),
# takže tenhle zdroj neprochází „neznámý formát = stale" logikou. Řetěz je přesto
# přepsatelný (COMP_SERP_ACTORS) pro případ výměny na fleetu.

def serp_paid(keyword, country="cz", lang="cs"):
    """list reklam (i prázdný = legit: nikdo neinzeruje). SourceError = STALE."""
    chain = configured_chain("serp")
    raised = None
    for actor in chain:
        inp = ({"queries": keyword, "countryCode": country, "languageCode": lang,
                "maxPagesPerQuery": 1, "focusOnPaidAds": True} if actor.startswith("apify~google-search-scraper")
               else {"queries": [keyword], "query": keyword, "countryCode": country, "languageCode": lang,
                     "maxPagesPerQuery": 1})
        try:
            it = provider_ads._run_actor(actor, inp, 2, 300)
        except SourceError as e:
            raised = e
            continue
        ads = []
        for page in it or []:
            for a in (page.get("paidResults") or page.get("ads") or []):
                dom = ""
                for cand in (_g(a, "displayedUrl", "displayed_link", default=""), _g(a, "url", "link", default="")):
                    d = re.sub(r"^https?://(www\.)?", "", cand).split("https")[0].split("/")[0].strip()
                    if d and "google." not in d:
                        dom = d
                        break
                if dom:
                    ads.append({"title": (_g(a, "title", "adTitle", default="") or "")[:90], "domain": dom})
        return ads
    if raised is not None:
        raise raised
    return []


def diff_serp(keyword, own_domain, ads):
    own = re.sub(r"^https?://(www\.)?", "", own_domain or "").split("/")[0]
    foreign = [a for a in ads if a["domain"] and own and own not in a["domain"]]
    if not foreign:
        return []
    who = ", ".join(sorted({a["domain"] for a in foreign})[:4])
    return [f"Na váš brandový dotaz „{keyword}“ inzeruje: {who} — zvažte obrannou Search kampaň."]
