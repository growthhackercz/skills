#!/usr/bin/env python3
"""content-scout — provider adaptér (VYMĚNITELNÝ). v2 = Apify (marketplace actory).
Volá Apify přes run-sync-get-dataset-items (synchronně, 1 HTTP call na platformu).
Společné schéma položky: {platform,title,author,url,likes,views,comments,date,thumb} (+ lang,duration,reposts,yt_short).
Actory ověřené pilotem (Free tier, 2026-07-08):
  tiktok = clockworks/tiktok-scraper · youtube = streamers/youtube-scraper · instagram = patient_discovery/instagram-search-reels
  linkedin = harvestapi/linkedin-post-search · x = danek/twitter-scraper
Swap providera = implementuj stejný povrch: search(platform, query, cap) -> (list[item], raw).
Pole jsou DEDIKOVANÁ per actor (žádný generický extractor — viz PLAN.md learning #1)."""
import os, re, json, datetime, urllib.request, urllib.parse, urllib.error

BASE = "https://api.apify.com/v2"
# actor slug ve tvaru pro API cestu: username~actor-name
ACTORS = {
    "tiktok":    "clockworks~tiktok-scraper",
    "youtube":   "streamers~youtube-scraper",
    "instagram": "patient_discovery~instagram-search-reels",
    "linkedin":  "harvestapi~linkedin-post-search",
    "x":         "danek~twitter-scraper",
}

def last_credits(): return None  # Apify nevrací per-call kredity; útratu vidíš v Apify dashboardu

def _cc_variable(name):
    """Control Center proměnné (Nastavení -> Integrace) — store má přednost před env."""
    try:
        import sys as _sys
        _sys.path.insert(0, "/home/node/.openclaw/cs-skills/_lib")
        from cc_credentials import get_variable  # type: ignore
        return (get_variable(name) or "").strip()
    except Exception:
        return ""

def _token(): return _cc_variable("APIFY_API_KEY") or os.environ.get("APIFY_API_KEY") or os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN", "")

def _run(actor, inp, timeout=180):
    """Spustí Apify actor synchronně a vrátí položky datasetu (list) v jednom HTTP callu."""
    url = f"{BASE}/acts/{actor}/run-sync-get-dataset-items?token=" + urllib.parse.quote(_token())
    req = urllib.request.Request(url, data=json.dumps(inp).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        d = json.load(urllib.request.urlopen(req, timeout=timeout))
    except urllib.error.HTTPError as e:
        try: body = e.read().decode("utf-8", "ignore")[:200]
        except Exception: body = ""
        raise RuntimeError(f"Apify {actor} HTTP {e.code}: {body}")
    if isinstance(d, list): return d
    if isinstance(d, dict): return d.get("items") or []
    return []

def _i(*vals):
    """Tolerantní int (unpackuje '1.2M', '6 473', 26000, '26,000'). bool ignoruje."""
    for v in vals:
        if isinstance(v, bool): continue
        if isinstance(v, (int, float)): return int(v)
        if isinstance(v, str):
            m = re.search(r"\d[\d.,]*", v)
            if m:
                try: return int(float(m.group().rstrip(".,").replace(",", "")))
                except ValueError: continue
    return 0

def _dur(s):
    """'00:18:47' -> 1127 s; int/float -> int; jinak 0 (hranice 180 s pro short)."""
    if isinstance(s, (int, float)): return int(s)
    if isinstance(s, str) and ":" in s:
        p = [int(x) for x in s.split(":") if x.strip().isdigit()]
        if len(p) == 3: return p[0]*3600 + p[1]*60 + p[2]
        if len(p) == 2: return p[0]*60 + p[1]
    return 0

def _twdate(s):
    """Twitter formát 'Thu Jul 02 08:42:24 +0000 2026' -> '2026-07-02' (jinak '')."""
    try: return datetime.datetime.strptime(str(s), "%a %b %d %H:%M:%S %z %Y").date().isoformat()
    except Exception: return ""

# ---- per-platform (pole ověřená pilotem 2026-07-08) ----
def _tiktok(q, cap):
    d = _run(ACTORS["tiktok"], {"searchQueries": [q], "searchSection": "/video", "resultsPerPage": cap})
    out = []
    for it in d[:cap]:
        if it.get("isAd"): continue  # reklamy sem NEpatří (→ ad-scout)
        vm = it.get("videoMeta") or {}
        desc = (it.get("text") or "").replace("\n", " ").strip()
        out.append({"platform": "tiktok", "title": desc[:180], "content": desc,
            "author": (it.get("authorMeta") or {}).get("name", ""),
            "url": (it.get("webVideoUrl") or "").split("?")[0],
            "likes": _i(it.get("diggCount")), "views": _i(it.get("playCount")), "comments": _i(it.get("commentCount")),
            "date": (str(it.get("createTimeISO") or ""))[:10],
            "thumb": vm.get("coverUrl") or vm.get("originalCoverUrl") or "",
            "lang": it.get("textLanguage") or "", "duration": _dur(vm.get("duration"))})
    return out, d

def _youtube(q, cap):
    shorts = max(3, cap // 3)
    d = _run(ACTORS["youtube"], {"searchQueries": [q], "maxResults": cap, "maxResultsShorts": shorts})
    out = []
    for v in d[:cap + shorts]:
        out.append({"platform": "youtube", "title": (v.get("title") or "")[:180],
            "author": v.get("channelName") or "", "url": v.get("url") or "",
            "likes": _i(v.get("likes")), "views": _i(v.get("viewCount")), "comments": _i(v.get("commentsCount")),
            "date": v.get("date") or "", "content": (v.get("text") or v.get("title") or "")[:400],
            "thumb": v.get("thumbnailUrl") or "", "yt_short": (v.get("type") == "shorts"),
            "duration": _dur(v.get("duration"))})
    return out, None

def _instagram(q, cap):
    pages = max(1, -(-cap // 10))  # ~10–12 reels na stránku
    d = _run(ACTORS["instagram"], {"query": q, "maxPages": pages})
    out = []
    for r in d[:cap]:
        cap_txt = ((r.get("caption") or {}).get("text") or "").replace("\n", " ").strip()
        code = r.get("code") or ""
        out.append({"platform": "instagram", "title": cap_txt[:180], "content": cap_txt,
            "author": (r.get("user") or {}).get("username", ""),
            "url": (f"https://www.instagram.com/reel/{code}/" if code else ""),
            "likes": max(0, _i(r.get("like_count"))),
            "views": _i(r.get("ig_play_count"), r.get("play_count")),
            "comments": max(0, _i(r.get("comment_count"))),
            "date": (str(r.get("taken_at_date") or ""))[:10],
            "thumb": r.get("thumbnail_url") or "", "duration": _i(r.get("video_duration"))})
    return out, d

def _linkedin(q, cap):
    d = _run(ACTORS["linkedin"], {"searchQueries": [q], "maxPosts": cap, "sortBy": "relevance"})
    out = []
    for p in d[:cap]:
        eng = p.get("engagement") or {}
        content = (p.get("content") or "").replace("\n", " ").strip()
        imgs = p.get("postImages") or []
        thumb = (imgs[0].get("url") if imgs and isinstance(imgs[0], dict) else "") \
                or (p.get("postVideo") or {}).get("thumbnailUrl", "") \
                or ((p.get("article") or {}).get("image") or {}).get("url", "") \
                or ((p.get("author") or {}).get("avatar") or {}).get("url", "")
        out.append({"platform": "linkedin", "title": content[:180], "content": content,
            "author": (p.get("author") or {}).get("name", ""), "url": p.get("linkedinUrl") or "",
            "likes": _i(eng.get("likes")), "views": 0, "comments": _i(eng.get("comments")),
            "date": ((p.get("postedAt") or {}).get("date") or "")[:10], "thumb": thumb or ""})
    return out, None

def _x_thumb(media):
    """danek media = dict {photo|video: dict|list}; vrať první obrázkovou URL (odolné vůči list i dict)."""
    if not isinstance(media, dict): return ""
    for key in ("photo", "video"):
        m = media.get(key)
        if isinstance(m, list): m = m[0] if m else None
        if isinstance(m, dict):
            u = m.get("media_url_https") or m.get("media_url") or ""
            if u: return u
    return ""

def _x(q, cap):
    d = _run(ACTORS["x"], {"query": q, "search_type": "Top", "max_posts": cap})
    out = []
    for t in d[:cap]:
        try:
            if not isinstance(t, dict) or not t.get("text"): continue  # přeskoč servisní/prázdné položky
            ui = t.get("user_info") if isinstance(t.get("user_info"), dict) else {}
            sn = t.get("screen_name") or ui.get("screen_name") or ""
            tid = t.get("tweet_id") or ""
            txt = (t.get("text") or "").replace("\n", " ").strip()
            out.append({"platform": "x", "title": txt[:180], "content": txt,
                "author": ui.get("name") or sn,
                "url": (f"https://x.com/{sn}/status/{tid}" if sn and tid else ""),
                "likes": _i(t.get("favorites")), "views": _i(t.get("views")), "comments": _i(t.get("replies")),
                "reposts": _i(t.get("retweets")), "date": _twdate(t.get("created_at")),
                "thumb": _x_thumb(t.get("media")), "lang": t.get("lang") or ""})
        except Exception:
            continue  # jeden divný tweet nezabije celou platformu (fail-open per item)
    return out, d

# ---- veřejné rozhraní ----
def search(platform, query, cap):
    """Vrátí (items, raw). raw se uloží při 0 položkách (fail-open — agent normalizuje ručně)."""
    if platform == "linkedin":  return _linkedin(query, cap)
    if platform == "youtube":   return _youtube(query, cap)
    if platform == "tiktok":    return _tiktok(query, cap)
    if platform == "instagram": return _instagram(query, cap)
    if platform == "x":         return _x(query, cap)
    raise ValueError(f"unknown platform {platform}")
