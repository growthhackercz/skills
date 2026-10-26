#!/usr/bin/env python3
"""content-scout — entry (fetch + build).
  scout.py fetch  "<keyword>" [--mode long|short|both] [--provider scrapecreators] [--dry-run] [--slug S]
  scout.py build  "<keyword>" [--slug S] [--window 30] [--board hot-viral] [--out FILE]
File-first: surová data i board jdou do run-dir; do kontextu agenta jen destilát (brief.md).
Provider je vyměnitelný (viz provider.py). LinkedIn/YouTube ověřené; TikTok/IG tolerantní + fail-open."""
import sys, os, re, json, math, argparse, datetime

BASE_DEFAULT = next((p for p in ("/documents/content/research/runs",
                    os.path.expanduser("~/Documents/content-scout/runs")) if os.path.isdir(os.path.dirname(p)) or True), None)
CAPS = {"linkedin": 20, "youtube": 24, "tiktok": 15, "instagram": 8, "x": 20}
MODE_PLATFORMS = {"long": ["linkedin", "youtube", "x"], "short": ["tiktok", "instagram", "youtube"],
                  "both": ["linkedin", "youtube", "tiktok", "instagram", "x"]}
WEIGHT = {"x": 1.0, "linkedin": 1.0, "youtube": 1.0, "tiktok": 0.97, "instagram": 0.95,
          "reddit": 0.90, "hackernews": 0.85, "web": 0.80}

def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s.lower()).strip()
    return re.sub(r"[\s_]+", "-", s)[:50] or "topic"

def run_dir(slug):
    base = os.environ.get("SCOUT_RUNS", BASE_DEFAULT)
    d = os.path.join(base, slug, datetime.date.today().isoformat())
    os.makedirs(d, exist_ok=True)
    return d

def read_run(slug):
    """Pro build: dnešní běh, jinak nejnovější < 7 dní (cache — kredity se neplatí 2×), jinak dnešní prázdný."""
    base = os.path.join(os.environ.get("SCOUT_RUNS", BASE_DEFAULT), slug)
    today = os.path.join(base, datetime.date.today().isoformat())
    if os.path.exists(os.path.join(today, "items.json")): return today
    if os.path.isdir(base):
        for x in sorted(os.listdir(base), reverse=True):
            p = os.path.join(base, x)
            if os.path.exists(os.path.join(p, "items.json")):
                try:
                    if (datetime.date.today() - datetime.date.fromisoformat(x)).days <= 7: return p
                except Exception: pass
    os.makedirs(today, exist_ok=True); return today

# ---------------- FETCH ----------------
def cmd_fetch(a):
    prov = (a.provider or "apify").lower()
    provider = __import__("provider_scrapecreators" if prov in ("scrapecreators", "sc") else "provider")
    slug = a.slug or slugify(a.keyword)
    platforms = MODE_PLATFORMS[a.mode]
    if a.dry_run:
        n = sum(CAPS[p] for p in platforms)
        print(f"[dry-run] slug={slug} mode={a.mode} provider={prov} platformy={platforms}")
        print(f"[dry-run] capy: " + ", ".join(f"{p}≤{CAPS[p]}" for p in platforms))
        print(f"[dry-run] odhad ≈ do {n} výsledků · Apify pay-per-result ≈ ${0.002*n:.2f}–${0.004*n:.2f} · žádná útrata teď")
        return
    if prov in ("scrapecreators", "sc"):
        need, have = "SCRAPECREATORS_API_KEY", os.environ.get("SCRAPECREATORS_API_KEY")
    else:
        need = "APIFY_API_KEY"
        have = os.environ.get("APIFY_API_KEY") or os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN")
    if not have:
        print(f"VAROVÁNÍ: {need} není nastaven → fetch přeskočen. Použij fallback (web_search/x_search) přes SKILL.md.")
        return
    d = run_dir(slug); items = []
    for p in platforms:
        try:
            got, raw = provider.search(p, a.keyword, CAPS[p])
        except Exception as e:
            print(f"[{p}] chyba: {type(e).__name__}: {e}")
            continue
        if not got and raw is not None:  # fail-open: ulož raw, agent normalizuje
            json.dump(raw, open(os.path.join(d, f"raw_{p}.json"), "w"))
            print(f"[{p}] 0 položek — raw uloženo (raw_{p}.json), normalizuj ručně")
        else:
            print(f"[{p}] {len(got)} položek")
            items += got
    json.dump(items, open(os.path.join(d, "items.json"), "w"), ensure_ascii=False)
    cr = provider.last_credits()
    print(f"→ items.json ({len(items)} položek) · {d}")
    if cr is not None:
        print(f"kredity zbývá: {cr}" + ("  ⚠️ pod 100" if isinstance(cr, int) and cr < 100 else ""))

# ---------------- SCORING ----------------
def vraw(it):
    L = lambda x: math.log1p(max(0, x or 0)); v, lk, c = L(it.get("views")), L(it.get("likes")), L(it.get("comments")); p = it["platform"]
    if p in ("reddit", "hackernews", "linkedin"): return 0.60 * lk + 0.40 * c
    if p == "youtube": return 0.45 * v + 0.42 * lk + 0.13 * c
    if p in ("tiktok", "instagram"): return 0.45 * v + 0.37 * lk + 0.18 * c
    if p == "x": return 0.40 * v + 0.40 * lk + 0.10 * L(it.get("reposts", 0)) + 0.10 * c
    return 0.5 * lk + 0.3 * c + 0.2 * v

def parse_date(s):
    """ISO nebo relativní datum EN i CZ ('2 weeks ago', 'před rokem', 'a month ago') → date.
    None když nelze (pak NEmazat). Zobrazení je vždy čisté YYYY-MM-DD (viz build)."""
    if not s: return None
    s = str(s).strip().lower()
    m = re.match(r"(\d{4}-\d\d-\d\d)", s)
    if m:
        try: return datetime.date.fromisoformat(m.group(1))
        except Exception: return None
    T = datetime.date.today()
    if "yesterday" in s or "včera" in s: return T - datetime.timedelta(days=1)
    if any(w in s for w in ("today", "dnes", "hour", "hodin", "minut", "sec", "vteř", "právě", "just now")):
        return T
    units = [("week", 7), ("týd", 7), ("month", 30), ("měs", 30), ("year", 365), ("rok", 365),
             ("roc", 365), ("let", 365), ("day", 1), ("den", 1), ("dne", 1), ("dny", 1), ("dní", 1), ("dnem", 1)]
    m = re.search(r"(\d+)", s); n = int(m.group(1)) if m else 1  # 'před týdnem' / 'a week ago' = 1
    for k, d in units:
        if k in s: return T - datetime.timedelta(days=n * d)
    return None

_CZM = ["", "ledna", "února", "března", "dubna", "května", "června", "července", "srpna", "září", "října", "listopadu", "prosince"]
def cz_date(iso):
    d = parse_date(iso)
    return f"{d.day}. {_CZM[d.month]} {d.year}" if d else ""

def freshness(it, today):
    dt = parse_date(it.get("date", ""))
    if not dt: return 1.0
    dd = (today - dt).days
    if dd <= 7: return 1.15
    if dd <= 14: return 1.05
    return 0.92

_EMOJI = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF←-⇿⬀-⯿️‍•]")
_CTA = re.compile(r"^(comment\b|follow\b|link in bio|link below|link on|dm\b|save this|bookmark|wait for it|part\s*\d|drop a\b|i'?ll send|i will send|tag a|like and|smash)", re.I)
def title_from_content(text):
    """Titulek tam, kde platforma nemá nativní (TikTok/IG/X popisky): bez emoji, přeskoč úvodní CTA/teaser,
    vezmi první SMYSLUPLNOU větu, řez na hranici slova. (Agentův titles.json má stejně přednost — tohle je fallback.)"""
    t = _EMOJI.sub("", text or "")
    t = re.sub(r"\s+", " ", t).strip(" ·—–-|:")
    sents = [x.strip(" ·—–-|:\"'“”") for x in re.split(r"(?<=[.!?…])\s+|\n+", t) if x.strip()]
    pick = ""
    for x in sents:
        if _CTA.search(x): continue                              # „Comment Video…", „Follow for…", „PART 1…"
        if x.endswith(("…", "...")) and len(x) < 45: continue     # úvodní teaser („I didn't think I'd ever say this…")
        if len(x) < 12: continue
        pick = x; break
    s = pick or (sents[0] if sents else t)
    if len(s) > 90:  # ořízni na hranici slova (ne uprostřed) + …
        s = s[:90].rsplit(" ", 1)[0].rstrip(" ,;:·—–-") + "…"
    return s

def content_bullets(text):
    """FALLBACK bullety z obsahu (v ostrém provozu je agent nahradí '3 highlighty PROČ je to virální')."""
    t = re.sub(r"[ \t]+", " ", text or "").strip()
    out = []
    for s in re.split(r"(?<=[.!?…])\s+|\n+|\s+[•·▪\-–—]\s+", t):
        s = s.strip(" •·▪-–—\t\"'“”")
        if len(s) >= 18:
            out.append(s[:95] + ("…" if len(s) > 95 else ""))
        if len(out) == 3: break
    return out

def is_czech(s):
    s = (s or "").lower()
    # jen Česko-specifické znaky — á/í/é/ú/ó sdílí španělština/francouzština → jinak „ES = CZ" false-positive
    return bool(re.search(r"[ěščřžůňťďý]", s)) or bool(re.search(r"\b(pro|které|který|jak|proč|nemovitost|makléř|vás|naše|náš|jsem|není|prostě|příspěvek|firmy|podnikání)\b", s))

def score_pool(items, today):
    """Skóruje a řadí V RÁMCI POOLU (per-geo normalizace → lokální se neutopí pod globálem)."""
    if not items: return []
    mx = max((vraw(i) for i in items), default=1) or 1
    for it in items:
        it["_v"] = 100 * vraw(it) / mx
        it["heat"] = round(it["_v"])
        it["_score"] = it["_v"] * freshness(it, today) * WEIGHT.get(it["platform"], 0.7)
    return sorted(items, key=lambda i: i["_score"], reverse=True)

def download_thumbs(items, assets):
    """Stáhne náhledy lokálně (cdn hotlink ochrana → jinak se nevykreslí). Best-effort, tiché."""
    import urllib.request, hashlib
    os.makedirs(assets, exist_ok=True)
    UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
    ok = 0
    for it in items:
        u = it.get("thumb") or ""
        if not u or u.startswith("assets/"): continue
        h = hashlib.md5(u.encode()).hexdigest()[:14] + ".jpg"
        dst = os.path.join(assets, h)
        if not os.path.exists(dst) or os.path.getsize(dst) < 800:
            try:
                data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=12).read()
                if len(data) < 800: continue
                open(dst, "wb").write(data)
            except Exception:
                continue
        it["thumb"] = "assets/" + h; ok += 1
    return ok

# ---------------- BUILD ----------------
def cmd_build(a):
    slug = a.slug or slugify(a.keyword)
    d = read_run(slug); today = datetime.date.today()
    items = []
    for f in ("items.json", "agent_items.json"):
        p = os.path.join(d, f)
        if os.path.exists(p):
            try: items += json.load(open(p))
            except Exception: pass
    if not items:
        print(f"Žádná data v {d}. Nejdřív `fetch` nebo dodej agent_items.json (fallback)."); return

    must = [t.strip().lower() for t in (getattr(a, "must", "") or "").split(",") if t.strip()]
    LANGS = set(t.strip().lower()[:2] for t in (getattr(a, "langs", "") or "cs,en").split(",") if t.strip())  # allowlist jazyků (známý cizí lang = šum, zahodit)
    def relevant(it):
        if not must: return True
        blob = ((it.get("title") or "") + " " + (it.get("content") or "")).lower()
        return any(t in blob for t in must)

    def window_filter(win):
        cd = today - datetime.timedelta(days=win); seen, out = set(), []
        for it in items:
            u = (it.get("url") or "").split("?")[0]
            if not u or u in seen: continue
            seen.add(u); it.setdefault("date", ""); it.setdefault("platform", "web")
            if not relevant(it): continue
            lg = (it.get("lang") or "").lower()[:2]
            if lg and LANGS and lg not in LANGS: continue  # zahoď známý cizí jazyk (šum: es/ha/ar…)
            dt = parse_date(it.get("date", ""))
            if dt and dt < cd: continue  # smaž jen PROKAZATELNĚ staré; neznámé datum = nech
            it = dict(it); it["date"] = dt.isoformat() if dt else ""  # čisté YYYY-MM-DD (bez času)
            out.append(it)
        return out

    # adaptivní okno: tenká nika → rozšiř, ať brief není prázdný (a řekni to)
    MIN = 8; eff = a.window
    for win in [a.window] + [w for w in (90, 180, 365) if w > a.window]:  # 30 → 90 → 180 → 365
        uniq = window_filter(win); eff = win
        if len(uniq) >= MIN: break
    widened = eff != a.window
    cutoff_date = today - datetime.timedelta(days=eff); cutoff = cutoff_date.isoformat()
    BULL = {}
    bp = os.path.join(d, "bullets.json")  # agentovy 'proč virální' highlighty (url -> [3])
    if os.path.exists(bp):
        try: BULL = json.load(open(bp))
        except Exception: pass
    TIT = {}
    tp = os.path.join(d, "titles.json")  # agentovy ČISTÉ titulky pro posty bez nativního titulku (url -> "titulek")
    if os.path.exists(tp):
        try: TIT = json.load(open(tp))
        except Exception: pass

    NATIVE_TITLE = ("youtube", "hackernews", "web")  # tyhle mají vlastní titulek; ostatní jen text → titulek VYROB z obsahu
    def enrich(it):
        content = (it.get("content") or "").strip() or (it.get("title") or "")
        if it["platform"] not in NATIVE_TITLE or not (it.get("title") or "").strip():
            it["title"] = (TIT.get(it["url"])                              # 1) agentův čistý titulek (ideál — reels/TikTok/IG nemají nativní)
                           or title_from_content(content)                 # 2) fallback: vyrob z obsahu (bez emoji, hranice slova)
                           or f"Příspěvek od {it.get('author','')}".strip().rstrip(" ·")
                           or f"{it['platform'].capitalize()} příspěvek")
        it["geo"] = "cs" if ((it.get("lang") or "").lower().startswith("cs")  # nativní jazyk z Apify (TikTok/X), fallback heuristika z obsahu
                             or is_czech((it.get("content") or "") + " " + it.get("author", ""))) else "global"
        p = it["platform"]  # 📚 Články & dlouhá videa (long) vs 📱 Social & krátká videa (short)
        if p in ("tiktok", "instagram"): it["format"] = "short"          # feed-native = vždy social
        elif p == "youtube": it["format"] = "short" if (it.get("yt_short") or 0 < (it.get("duration") or 0) <= 180) else "long"  # Shorts / ≤3 min
        else: it["format"] = "long"                                       # LinkedIn/web/HN/Reddit/X thready = hloubka
        it["likes"] = max(0, it.get("likes", 0) or 0)  # IG občas vrací -1 (skryté)
        it["bullets"] = (BULL.get(it["url"]) or content_bullets(content))[:3]
        it["date_disp"] = cz_date(it.get("date", ""))

    local = score_pool(uniq, today)
    topped = 0; thin = len(local) < 10
    gslug = getattr(a, "global_slug", "")
    if len(local) < 30 and gslug:  # doplň do TOP 30 z globálu (a když <10 lokálních, je to i thin-niche fallback)
        gd = read_run(gslug); gitems = []
        for f in ("items.json", "agent_items.json"):
            gp = os.path.join(gd, f)
            if os.path.exists(gp):
                try: gitems += json.load(open(gp))
                except Exception: pass
        lurls = {i["url"].split("?")[0] for i in local}; seen = set(); gclean = []
        gcut = today - datetime.timedelta(days=365)
        for it in gitems:
            u = (it.get("url") or "").split("?")[0]
            if not u or u in seen or u in lurls: continue
            seen.add(u); it.setdefault("date", ""); it.setdefault("platform", "web")
            if not relevant(it): continue
            lg = (it.get("lang") or "").lower()[:2]
            if lg and LANGS and lg not in LANGS: continue
            dt = parse_date(it.get("date", ""))
            if dt and dt < gcut: continue
            it = dict(it); it["date"] = dt.isoformat() if dt else ""; gclean.append(it)
        fill = score_pool(gclean, today)[:max(0, 30 - len(local))]
        for it in fill: it["_fill"] = True
        uniq = local + fill; topped = len(fill)
    else:
        uniq = local
    for it in uniq:
        enrich(it)
    # jazyk-based pořadí + skóre: nejdřív 🇨🇿 lokální (heat relativně k CZ poolu), pak 🌍 globální
    cs = score_pool([i for i in uniq if i.get("geo") == "cs"], today)
    gl = score_pool([i for i in uniq if i.get("geo") != "cs"], today)
    uniq = (cs + gl)[:30]
    thin = len(cs) < 10
    topped = sum(1 for i in uniq if i.get("geo") != "cs")

    from collections import Counter
    counts = dict(Counter(i["platform"] for i in uniq))
    viral_top = [{"rank": n+1, "platform": it["platform"], "format": it.get("format", "long"), "geo": it.get("geo", ""),
                  "title": it["title"][:140], "url": it["url"], "author": it.get("author", ""),
                  "likes": it.get("likes", 0), "views": it.get("views", 0), "heat": it["heat"],
                  "date": it.get("date", "")} for n, it in enumerate(uniq[:20])]
    brief = {"keyword": a.keyword, "slug": slug, "generated": today.isoformat(),
             "window_days": eff, "requested_window": a.window, "widened": widened,
             "cutoff": cutoff, "counts_by_platform": counts, "total_items": len(uniq),
             "viral_top": viral_top,
             "note_for_agent": "Naklastruj raw_items do TÉMAT (Trend Board), doplň 🌲 evergreen (otázky/bolesti/sezóna) a doporučené úhly/hooky. viral_top je hotová data-strana.",
             "raw_items": uniq}
    json.dump(brief, open(os.path.join(d, "brief.json"), "w"), ensure_ascii=False, indent=1)

    warn = f"  ⚠️ za {a.window} dní bylo málo dat → okno rozšířeno na {eff} dní (tenká nika)" if widened else ""
    if topped:
        warn += (f"  🌍 málo lokálních (CZ) záznamů i za {eff} dní → doplněno {topped}× z globálního trhu (předstih)"
                 if thin else f"  🌍 doplněno {topped}× z globálního trhu do TOP 30")
    nlong = sum(1 for i in uniq if i.get("format") == "long"); nshort = len(uniq) - nlong
    ncs = sum(1 for i in uniq if i.get("geo") == "cs")
    lines = [f"# Content Scout brief — {a.keyword}", "",
             f"Okno: {cutoff} → {today} ({eff} dní) · položek: {len(uniq)} · zdroje: " +
             ", ".join(f"{k} {v}" for k, v in counts.items()) + warn, "",
             f"Formát: 📚 Články & dlouhá videa {nlong} · 📱 Social & krátká videa {nshort}  |  Geo: 🇨🇿 {ncs} / 🌍 {len(uniq)-ncs}", "",
             "## 🔥 Virály (příspěvky, co odskočily — hotová data-strana)", "",
             "| # | 🔥 | Síť | ❤ | 👁 | Příspěvek |", "|---|---|---|---|---|---|"]
    for it in uniq[:12]:
        vv = f'{it.get("views",0):,}'.replace(",", " ") if it.get("views") else "—"
        lines.append(f'| {uniq.index(it)+1} | {it["heat"]} | {it["platform"]} | {it.get("likes",0):,} | {vv} | [{it["title"][:56]}]({it["url"]}) |'.replace(",", " ", 2))
    lines += ["", "## 📈 Trendy (TÉMATA) — DOPLNÍ AGENT clusteringem raw_items",
              "## 🌲 Evergreen (otázky · bolesti · sezóna) — DOPLNÍ AGENT",
              "## Doporučené úhly / hooky — DOPLNÍ AGENT", ""]
    open(os.path.join(d, "brief.md"), "w", encoding="utf-8").write("\n".join(lines))
    print(f"→ brief.json + brief.md · {d}")
    print("\n".join(lines[:18]))

    if a.board:
        import board
        if "trend" in a.board:  # ---- Trend Board: TOP 10 TÉMAT z agentova themes.json ----
            out = a.out or os.path.join(d, "board-trend.html")
            themes = []
            tp = os.path.join(d, "themes.json")  # agent clusteruje raw_items → témata (viz SKILL.md Krok 5)
            if os.path.exists(tp):
                try: themes = json.load(open(tp))
                except Exception: pass
            if not themes:
                print("⚠️ Trend Board: chybí themes.json — agent musí nejdřív naklastrovat témata (SKILL.md Krok 5). Board nevygenerován.")
            else:
                sub_t = f"📅 Data z posledních {eff} dní · 🇨🇿 lokální + 🌍 globální doplněk · Trend Score = síla trendu 0–100"
                if widened: sub_t += f" · ⚠️ za {a.window} dní málo dat → rozšířeno na {eff} dní (tenká nika)"
                n = board.render_trend(a.keyword, themes, out, subtitle=sub_t)
                print(f"→ Trend Board ({n} témat): {out}")
        else:  # ---- Viral Board: TOP 30 KUSŮ ----
            out = a.out or os.path.join(d, "board-viral.html")
            sub = f"TOP 30 · okno {cutoff} → {today} ({eff} dní) · Trend Score = viralita 0–100"
            if widened: sub += f" · ⚠️ za {a.window} dní skoro nic — nejlepší za {eff} dní (tenká nika)"
            if topped: sub += f" · 🌍 doplněno {topped}× globálním trhem (málo lokálních záznamů)"
            got = download_thumbs(uniq, os.path.join(os.path.dirname(out), "assets"))  # náhledy lokálně, ať se vykreslí
            print(f"náhledy staženo lokálně: {got}")
            n = board.render(a.keyword, uniq, out, kind="Viral", subtitle=sub)
            print(f"→ Viral Board ({n} karet): {out}")

# ---------------- CLI ----------------
def main():
    ap = argparse.ArgumentParser(prog="scout.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch"); f.add_argument("keyword")
    f.add_argument("--mode", choices=["long", "short", "both"], default="both")
    f.add_argument("--provider", default="apify"); f.add_argument("--dry-run", action="store_true")
    f.add_argument("--slug", default="")
    b = sub.add_parser("build"); b.add_argument("keyword"); b.add_argument("--slug", default="")
    b.add_argument("--window", type=int, default=30); b.add_argument("--board", default=""); b.add_argument("--out", default="")
    b.add_argument("--global", dest="global_slug", default="", help="slug globálního běhu na doplnění, když <10 lokálních")
    b.add_argument("--must-contain", dest="must", default="", help="čárkou oddělené tokeny; položka musí aspoň jeden obsahovat (relevance filtr)")
    b.add_argument("--langs", default="cs,en", help="allowlist jazyků (známý lang mimo seznam se zahodí jako šum); default cs,en · ES trh: es,en")
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    (cmd_fetch if a.cmd == "fetch" else cmd_build)(a)

if __name__ == "__main__":
    main()
