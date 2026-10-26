#!/usr/bin/env python3
"""content-scout — provider adaptér (VYMĚNITELNÝ). v0.1 = ScrapeCreators.
Společné schéma položky: {platform,title,author,url,likes,views,comments,date,thumb}.
Swap providera = implementuj stejný povrch: search(platform, query, cap) -> list[item].
LinkedIn/YouTube = ověřené tvary; TikTok/Instagram = tolerantní normalizace + fail-open."""
import os, re, json, datetime, urllib.request, urllib.parse

BASE = "https://api.scrapecreators.com"
_last_credits = None

def _cc_variable(name):
    """Control Center proměnné (Nastavení -> Integrace) — store má přednost před env."""
    try:
        import sys as _sys
        _sys.path.insert(0, "/home/node/.openclaw/cs-skills/_lib")
        from cc_credentials import get_variable  # type: ignore
        return (get_variable(name) or "").strip()
    except Exception:
        return ""

def _key(): return _cc_variable("SCRAPECREATORS_API_KEY") or os.environ.get("SCRAPECREATORS_API_KEY", "")
def last_credits(): return _last_credits

def _get(path, params):
    global _last_credits
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"x-api-key": _key()})
    d = json.load(urllib.request.urlopen(req, timeout=45))
    if isinstance(d, dict) and "credits_remaining" in d:
        _last_credits = d["credits_remaining"]
    return d

def _to_int(*vals):
    for v in vals:
        if isinstance(v, (int, float)): return int(v)
        if isinstance(v, str):
            m = re.search(r"\d[\d.,]*", v)
            if m:
                try: n = float(m.group().rstrip(".,").replace(",", ""))
                except ValueError: continue
                if "M" in v.upper(): n *= 1e6
                elif "K" in v.upper(): n *= 1e3
                return int(n)
    return 0

def _walk(o):
    """yield all (key, value) primitives recursively"""
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)): yield from _walk(v)
            else: yield k, v
    elif isinstance(o, list):
        for v in o: yield from _walk(v)

def _find_img(o, *cdns):
    for _, v in _walk(o):
        if isinstance(v, str) and v.startswith("http") and any(c in v for c in cdns) \
           and re.search(r"\.(jpe?g|webp|png)", v.split("?")[0]):
            return v.split("?")[0]
    return ""

def _find_url(o, domain):
    for _, v in _walk(o):
        if isinstance(v, str) and domain in v and v.startswith("http"):
            return v.split("?")[0]
    return ""

def _find_metric(o, *needles):
    best = 0
    for k, v in _walk(o):
        if isinstance(k, str) and any(n in k.lower() for n in needles):
            best = max(best, _to_int(v))
    return best

def _find_text(o, *keys):
    for k, v in _walk(o):
        if isinstance(k, str) and k.lower() in keys and isinstance(v, str) and v.strip():
            return v.strip()
    return ""

# ---- per-platform (LinkedIn/YouTube ověřené) ----
def _li_title(p):
    t = (p.get("description") or "").replace("\n", " ").strip()
    if t: return t[:180]
    m = re.search(r"/posts/[^_/]+_([a-z0-9-]+)-activity", p.get("url", ""))  # text bývá v URL slugu
    if m:
        s = m.group(1).replace("-", " ").strip()
        return (s[:1].upper() + s[1:])[:180]
    return f"Příspěvek na LinkedInu od {(p.get('author') or {}).get('name','')}".strip()

def _linkedin(q, cap):
    out = []
    d = _get("/v1/linkedin/search/posts", {"query": q})
    for p in (d.get("posts") or [])[:cap]:
        thumb = p.get("image") or (p.get("images") or [None])[0] or _find_img(p, "licdn") or ""
        out.append({"platform": "linkedin", "title": _li_title(p),
            "author": (p.get("author") or {}).get("name", ""), "url": p.get("url", ""),
            "likes": p.get("likeCount", 0) or 0, "views": 0, "comments": p.get("commentCount", 0) or 0,
            "date": (p.get("datePublished") or "")[:10],
            "content": (p.get("description") or "").replace("\n", " ").strip(), "thumb": thumb})
    return out

def _youtube(q, cap):
    out = []
    d = _get("/v1/youtube/search", {"query": q})
    vids = [(v, False) for v in (d.get("videos") or [])] + [(v, True) for v in (d.get("shorts") or [])]  # YouTube sám dělí videa/Shorts
    for v, is_short in vids[:cap]:
        ch = v.get("channel") or {}
        dur = _to_int(v.get("lengthSeconds")) or (int((v.get("durationMs") or 0) / 1000) if v.get("durationMs") else 0)
        out.append({"platform": "youtube", "title": (v.get("title") or "")[:180],
            "author": (ch.get("title") if isinstance(ch, dict) else ch) or "",
            "url": v.get("url") or ("https://www.youtube.com/watch?v=" + (v.get("id") or "")),
            "likes": _to_int(v.get("likeCountInt"), v.get("likeCount")),
            "views": _to_int(v.get("viewCountInt"), v.get("viewCount")),
            "comments": _to_int(v.get("commentCountInt")),
            "date": (v.get("publishedTime") or v.get("publishDate") or ""),
            "content": (v.get("description") or v.get("title") or "")[:400], "thumb": v.get("thumbnail") or "",
            "yt_short": is_short, "duration": dur})  # yt_short = ze Shorts pole; duration s (hranice 180s)
    return out

def _tolerant(platform, domain, cdn, data, cap):
    """TikTok/IG: response shapes drift — normalizuj tolerantně, fail-open na raw."""
    lists = [v for _, v in [("", data)] ]  # seed
    candidates = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], (dict,)):
                candidates.append(v)
    elif isinstance(data, list):
        candidates.append(data)
    items = max(candidates, key=len) if candidates else []
    out = []
    for it in items[:cap]:
        url = _find_url(it, domain)
        if not url: continue
        out.append({"platform": platform, "title": _find_text(it, "desc", "title", "caption", "text")[:180],
            "author": _find_text(it, "unique_id", "handle", "username", "nickname", "author"),
            "url": url, "likes": _find_metric(it, "digg", "like"),
            "views": _find_metric(it, "play", "view"), "comments": _find_metric(it, "comment"),
            "date": "", "content": _find_text(it, "desc", "caption", "text", "content", "title")[:400],
            "thumb": _find_img(it, cdn)})
    return out

def _tiktok(q, cap):
    d = _get("/v1/tiktok/search/keyword", {"query": q, "sort_by": "relevance"})
    out = []
    for row in (d.get("search_item_list") or [])[:cap]:
        a = row.get("aweme_info") or row
        st = a.get("statistics") or {}; vid = a.get("video") or {}
        cover = ((vid.get("cover") or {}).get("url_list") or [""])[0] or ((vid.get("origin_cover") or {}).get("url_list") or [""])[0]
        play = ((vid.get("play_addr") or {}).get("url_list") or [""])[0]
        date = ""
        try: date = datetime.datetime.utcfromtimestamp(int(a.get("create_time"))).date().isoformat()
        except Exception: pass
        desc = (a.get("desc") or "").replace("\n", " ").strip()
        out.append({"platform": "tiktok", "title": desc[:180], "content": desc,
            "author": (a.get("author") or {}).get("unique_id", ""),
            "url": (a.get("share_url") or "").split("?")[0],
            "likes": st.get("digg_count", 0) or 0, "views": st.get("play_count", 0) or 0,
            "comments": st.get("comment_count", 0) or 0, "date": date,
            "thumb": cover, "video": play})
    return out, d

def _instagram(q, cap):
    d = _get("/v2/instagram/reels/search", {"query": q})
    out = []
    for r in (d.get("reels") or [])[:cap]:
        cap_txt = (r.get("caption") or "").replace("\n", " ").strip()
        out.append({"platform": "instagram", "title": cap_txt[:180], "content": cap_txt,
            "author": (r.get("owner") or {}).get("username", ""),
            "url": (r.get("url") or "").split("?")[0],
            "likes": max(0, r.get("like_count", 0) or 0),
            "views": max(0, r.get("video_view_count") or r.get("video_play_count") or 0),
            "comments": max(0, r.get("comment_count", 0) or 0), "date": (r.get("taken_at") or "")[:10],
            "thumb": r.get("thumbnail_src") or r.get("display_url") or "", "video": r.get("video_url") or ""})
    return out, d

# ---- veřejné rozhraní ----
def search(platform, query, cap):
    """Vrátí (items, raw). raw se uloží při 0 položkách (fail-open)."""
    if platform == "linkedin": return _linkedin(query, cap), None
    if platform == "youtube":  return _youtube(query, cap), None
    if platform == "tiktok":   return _tiktok(query, cap)
    if platform == "instagram":return _instagram(query, cap)
    raise ValueError(f"unknown platform {platform}")
