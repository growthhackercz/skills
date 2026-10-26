#!/usr/bin/env python3
"""content-scout — board renderer (čistý render z předskórovaných položek).
Volá se z scout.py: render(topic, items, out_html, kind). Položka musí mít:
platform,title,author,url,likes,views,comments,date,thumb,heat,bullets(list),score."""
import html
from collections import Counter

PLAT = {
 "x":("X / Twitter","#1d9bf0","x"), "linkedin":("LinkedIn","#0a66c2","linkedin"),
 "youtube":("YouTube","#ff0000","youtube"), "reddit":("Reddit","#ff4500","reddit"),
 "hackernews":("Hacker News","#ff6600","hn"), "tiktok":("TikTok","#ff0050","tiktok"),
 "instagram":("Instagram","#e1306c","instagram"), "web":("Web","#7c8aa0","web"),
}
ICON = {
 "x":'<path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>',
 "linkedin":'<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z"/>',
 "youtube":'<path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12z"/>',
 "reddit":'<path d="M24 11.779c0-1.459-1.192-2.645-2.657-2.645-.715 0-1.363.286-1.84.746-1.81-1.191-4.259-1.949-6.971-2.046l1.483-4.669 4.016.941-.006.058c0 1.193.975 2.163 2.174 2.163 1.198 0 2.172-.97 2.172-2.163s-.975-2.164-2.172-2.164c-.92 0-1.704.574-2.021 1.379l-4.329-1.015a.379.379 0 0 0-.450.270l-1.654 5.207c-2.758.075-5.25.833-7.077 2.034a2.642 2.642 0 0 0-1.838-.742C1.192 9.134 0 10.32 0 11.779c0 .982.542 1.835 1.34 2.291a4.61 4.61 0 0 0-.052.7c0 3.547 4.234 6.428 9.428 6.428s9.428-2.881 9.428-6.428c0-.238-.02-.473-.054-.703.792-.458 1.332-1.309 1.332-2.288zM6.769 13.703c0-.659.534-1.193 1.193-1.193s1.193.534 1.193 1.193-.534 1.193-1.193 1.193-1.193-.534-1.193-1.193zm6.703 4.041c-.835.835-2.432.9-2.901.9s-2.067-.064-2.9-.9a.31.31 0 0 1 0-.438.31.31 0 0 1 .438 0c.526.526 1.652.713 2.463.713.81 0 1.937-.187 2.463-.713a.31.31 0 0 1 .438 0 .31.31 0 0 1-.001.438zm-.235-2.848c-.659 0-1.193-.534-1.193-1.193s.534-1.193 1.193-1.193 1.193.534 1.193 1.193-.534 1.193-1.193 1.193z"/>',
 "hn":'<path d="M0 24V0h24v24H0zM6.951 5.896l4.112 7.708v5.064h1.583v-4.972l4.148-7.799h-1.749l-2.457 4.875c-.372.745-.688 1.434-.688 1.434s-.297-.708-.651-1.434L8.831 5.896z"/>',
 "tiktok":'<path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>',
 "instagram":'<path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>',
 "web":'<path d="M12 0a12 12 0 100 24 12 12 0 000-24zm0 2c1.6 0 3 3.5 3 10s-1.4 10-3 10-3-3.5-3-10 1.4-10 3-10zM4 12a8 8 0 0116 0H4z"/>',
 "flame":'<path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67z"/>',
 "heart":'<path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>',
 "eye":'<path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zm0 12a4.5 4.5 0 110-9 4.5 4.5 0 010 9zm0-7a2.5 2.5 0 100 5 2.5 2.5 0 000-5z"/>',
 "comment":'<path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>',
 "article":'<path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>',
 "mobile":'<path d="M17 1.01L7 1c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-1.99-2-1.99zM17 19H7V5h10v14z"/>',
 "scout":'<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10c0-2.76-1.12-5.26-2.93-7.07l-1.42 1.42A7.94 7.94 0 0120 12a8 8 0 11-8-8V2zm0 4a6 6 0 00-6 6 6 6 0 006 6 6 6 0 006-6h-2a4 4 0 01-4 4 4 4 0 01-4-4 4 4 0 014-4V6zm0 4a2 2 0 00-2 2 2 2 0 002 2 2 2 0 002-2 2 2 0 00-2-2z"/>',
 "bolt":'<path d="M13 2L3 14h7v8l10-12h-7z"/>',
 "trendup":'<path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/>',
 "edit":'<path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 000-1.41l-2.34-2.34a1 1 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>',
 "bulb":'<path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z"/>',
}
def _svg(k, sz, col, op=1.0):
    return f'<svg viewBox="0 0 24 24" width="{sz}" height="{sz}" fill="{col}" style="opacity:{op}">{ICON.get(k,"")}</svg>'
def _fmt(n): return f"{n:,}".replace(",", " ")
def _clip(s, n=78):  # titulek nikdy neuseknout uprostřed slova; zkrať čistě na ~3 řádky
    s = (s or "").strip()
    if len(s) <= n: return s
    return s[:n].rsplit(" ", 1)[0].rstrip(" ,;:·—–-") + "…"

def _card(rank, it):
    name, color, ik = PLAT.get(it["platform"], ("?", "#555", "web"))
    h = it.get("heat", 0); tier = "hot" if h >= 80 else "warm" if h >= 50 else "cool"
    flag = "🇨🇿" if it.get("geo") == "cs" else "🌍"
    th = html.escape(it.get("thumb") or "")
    orient = "portrait" if it.get("platform") in ("tiktok", "instagram") else "landscape"  # grid vždy 16:9; portrét vsazen dovnitř rámu
    bg = f'<img class="bg" src="{th}" referrerpolicy="no-referrer" aria-hidden="true">' if th and orient == "portrait" else ""
    img = f'{bg}<img class="ph" src="{th}" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display=\'none\'">' if th else ""
    big = "" if th else f'<span class="big">{_svg(ik,46,"#fff",0.5)}</span>'  # centrální ikona jen když NENÍ náhled
    dd = it.get("date_disp") or it.get("date") or ""
    date = f' · {html.escape(dd)}' if dd else ""
    m = f'{_svg("heart",12,"#ff5d8f")} {_fmt(it.get("likes",0))}'  # engagement ikony barevné dle brand jazyka
    if it.get("views"): m += f' &nbsp;·&nbsp; {_svg("eye",12,"#38b6ff")} {_fmt(it["views"])}'
    if it.get("comments"): m += f' &nbsp;·&nbsp; {_svg("comment",12,"#2ee6c6")} {_fmt(it["comments"])}'
    bl = "".join(f"<li>{html.escape(b)}</li>" for b in it.get("bullets", [])[:3])
    fmt = it.get("format", "long")
    flabel = (_svg("mobile", 12, "currentColor") + " Social & krátká videa") if fmt == "short" else (_svg("article", 12, "currentColor") + " Články & dlouhá videa")
    return f'''<a class="card" data-format="{fmt}" data-platform="{it["platform"]}" href="{html.escape(it["url"])}" target="_blank">
  <div class="thumb {orient}" style="--c:{color}">{img}{big}<span class="score {tier}">{_svg("flame",12,"currentColor")} {h}</span>
    <div class="overlay"><span class="fmt f-{fmt}">{flabel}</span></div></div>
  <div class="body"><div class="title">{html.escape(_clip(it["title"]))}</div>
    <div class="badge" style="background:{color}">{_svg(ik,12,"#fff")}<span>{flag} {name}{date}</span></div><div class="meta">{html.escape(it.get("author",""))}</div>
    <div class="metrics">{m}</div><ul class="why">{bl}</ul></div><div class="rank">#{rank}</div></a>'''

def render(topic, items, out_html, kind="Viral", subtitle=""):
    top = items[:30]
    cnt = Counter(i["platform"] for i in top)
    chips = " ".join(f'<span class="chip" style="background:{PLAT[p][1] if p in PLAT else "#3a5cff"}" onclick="pf(event,\'{p}\')">{_svg(PLAT[p][2] if p in PLAT else "web",12,"#fff")} {PLAT[p][0] if p in PLAT else p}: {n}</span>' for p, n in cnt.most_common())
    cards = "\n".join(_card(i+1, it) for i, it in enumerate(top))
    doc = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TOP {len(top)} příspěvků — {html.escape(topic)}</title><style>
*{{box-sizing:border-box;margin:0}} body{{background:radial-gradient(1100px 620px at 6% -8%,rgba(46,230,198,.12),transparent 58%),radial-gradient(1050px 760px at 102% 2%,rgba(58,123,255,.16),transparent 56%),radial-gradient(1200px 900px at 55% 122%,rgba(56,182,255,.11),transparent 60%),linear-gradient(180deg,#0a1122,#070d1c);background-attachment:fixed;color:#eaf1ff;font:15px/1.45 'DM Sans',-apple-system,Segoe UI,Roboto,sans-serif;padding:34px 30px}}
.kicker{{display:inline-flex;align-items:center;gap:8px;font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#2ee6c6;background:linear-gradient(135deg,#2ee6c633,#3a7bff22);border:1px solid #2ee6c633;padding:7px 14px;border-radius:30px}} .kicker svg{{filter:drop-shadow(0 0 6px #2ee6c6aa)}}
h1{{font-size:30px;font-weight:800;letter-spacing:-.5px;margin:14px 0 4px}} h1 .grad{{background:linear-gradient(135deg,#2ee6c6,#38b6ff 55%,#3a7bff);-webkit-background-clip:text;background-clip:text;color:transparent}} .sub{{color:#8aa0c0;margin:4px 0}}
.chips{{margin:14px 0 10px}} .chip{{display:inline-flex;align-items:center;gap:6px;border:0;border-radius:16px;padding:5px 11px;margin:3px;font-size:11.5px;color:#fff;font-weight:800;cursor:pointer;transition:.15s;box-shadow:0 3px 10px #0005}} .chip svg{{fill:#fff}} .chip:hover{{transform:translateY(-2px)}} .chip.on{{box-shadow:0 0 0 2px #fff,0 6px 16px #0007;transform:translateY(-1px)}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}}
@media(max-width:1100px){{.grid{{grid-template-columns:repeat(2,1fr)}}}} @media(max-width:620px){{.grid{{grid-template-columns:1fr}}}}
.card{{position:relative;background:#121a30;border:1px solid #1e2c4a;border-radius:14px;overflow:hidden;text-decoration:none;color:inherit;display:flex;flex-direction:column;transition:.15s}}
.card:hover{{transform:translateY(-3px);border-color:#3a5cff;box-shadow:0 10px 30px #0006}}
.thumb{{position:relative;aspect-ratio:16/9;background:linear-gradient(135deg,var(--c),#0b1020);display:flex;align-items:center;justify-content:center;overflow:hidden}}
.thumb .ph{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.thumb .bg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:blur(20px) brightness(.55);transform:scale(1.15)}}
.thumb.portrait .ph{{object-fit:contain;z-index:1}}
.overlay{{position:absolute;left:8px;right:8px;bottom:8px;z-index:3;display:flex;flex-direction:column;gap:5px;align-items:flex-start}}
.overlay .badge,.overlay .fmt{{box-shadow:0 2px 10px #000a;max-width:100%}}
.overlay .fmt{{background:#0e1730dd;backdrop-filter:blur(6px)}}
.overlay .badge span{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.body{{padding:16px 16px 18px;display:flex;flex-direction:column;gap:8px}}
.badge{{display:inline-flex;align-items:center;gap:5px;font-size:10.5px;font-weight:700;color:#fff;padding:3px 8px;border-radius:6px;align-self:flex-start}}
.title{{font-weight:800;font-size:18px;line-height:1.28;letter-spacing:-.3px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.meta{{color:#8aa0c0;font-size:12px}} .metrics{{font-size:12.5px;color:#cfe0ff;font-weight:600}} .metrics svg{{vertical-align:-2px}}
.why{{list-style:none;font-size:11.5px;line-height:1.45;color:#b9c8e6;background:#0e1730;border-left:3px solid var(--c,#3a5cff);padding:7px 9px 7px 22px;border-radius:0 7px 7px 0}}
.why li{{position:relative;margin:1px 0}} .why li:before{{content:"›";position:absolute;left:-12px;color:var(--c);font-weight:800}}
.score{{position:absolute;top:8px;left:8px;z-index:3;display:inline-flex;align-items:center;gap:4px;font-size:12.5px;font-weight:800;color:#fff;padding:3px 8px;border-radius:8px;box-shadow:0 2px 8px #0007}} .score svg{{margin-top:-1px}}
.score.hot{{background:linear-gradient(135deg,#ff7a18,#ff2052)}} .score.warm{{background:linear-gradient(135deg,#ffab18,#ff6a00)}} .score.cool{{background:linear-gradient(135deg,#38b6ff,#2f6bff)}}
.rank{{position:absolute;top:8px;right:8px;z-index:3;background:#000a;backdrop-filter:blur(4px);border-radius:8px;padding:3px 9px;font-weight:800;font-size:13px}}
.foot{{color:#5d6f8e;margin-top:28px;font-size:12px}}
.filters{{margin:0 0 34px}} .filters button{{display:inline-flex;align-items:center;gap:5px;background:#16203a;border:1px solid #243a5e;color:#cfe0ff;border-radius:16px;padding:5px 12px;margin-right:7px;font-size:11.5px;cursor:pointer;font-weight:700;transition:.15s}} .filters button:hover{{border-color:#38b6ff;transform:translateY(-1px)}} .filters button.on{{background:linear-gradient(135deg,#2ee6c6,#3a7bff);border-color:transparent;color:#04101f}}
.fmt{{display:inline-flex;align-items:center;gap:5px;align-self:flex-start;font-size:10.5px;font-weight:700;padding:2px 9px;border-radius:20px;background:#0e1730;border:1px solid #243a5e}} .fmt.f-short{{color:#ff9ec4}} .fmt.f-long{{color:#8fd0ff}}
</style></head><body>
<span class="kicker">{_svg("scout",15,"#2ee6c6")} Content Scout · {html.escape(kind)} Board</span>
<h1>TOP {len(top)} příspěvků — <span class="grad">{html.escape(topic)}</span></h1>
<div class="sub">{html.escape(subtitle)}</div><div class="chips">{chips}</div>
<div class="filters"><button class="on" onclick="ff(event,'all')">Vše</button><button onclick="ff(event,'long')">{_svg("article",12,"currentColor")} Články &amp; dlouhá videa</button><button onclick="ff(event,'short')">{_svg("mobile",12,"currentColor")} Social &amp; krátká videa</button></div>
<div class="grid">{cards}</div>
<div class="foot">CliqSales · Content Scout</div>
<script>
var flt={{fmt:'all',plat:'all'}};
function applyF(){{document.querySelectorAll('.card').forEach(function(c){{var okF=flt.fmt=='all'||c.dataset.format==flt.fmt;var okP=flt.plat=='all'||c.dataset.platform==flt.plat;c.style.display=(okF&&okP)?'':'none';}});}}
function ff(e,m){{flt.fmt=m;document.querySelectorAll('.filters button').forEach(function(b){{b.classList.remove('on');}});e.currentTarget.classList.add('on');applyF();}}
function pf(e,p){{flt.plat=(flt.plat==p?'all':p);document.querySelectorAll('.chip').forEach(function(c){{c.classList.remove('on');}});if(flt.plat!='all')e.currentTarget.classList.add('on');applyF();}}
</script>
</body></html>'''
    open(out_html, "w", encoding="utf-8").write(doc)
    return len(top)


# ============ TREND BOARD (render_trend) — TOP 10 rostoucích TÉMAT ============
_COOL = ["#2ee6c6","#27d8ce","#38b6ff","#33bdf2","#3aa8ff","#3a95ff","#3a83f5","#4a6fe8","#5a6cd8","#6b78c4"]
_IDEA = {"reel":("mobile","Reel"),"short":("mobile","Reel"),"article":("article","Článek"),"clanek":("article","Článek"),"blog":("article","Blog"),"youtube":("youtube","YouTube"),"video":("youtube","Video"),"newsletter":("article","Newsletter"),"post":("mobile","Post")}
def _u(k): return f'<svg><use href="#{k}"/></svg>'
def _prisp(n): return "příspěvek" if n == 1 else "příspěvky" if 2 <= n <= 4 else "příspěvků"  # česká shoda
def _spark(mom):  # sparkline odvozený z momenta (vyšší = strmější růst)
    endY = max(2, 31 - round(mom * 0.16)); xs = [0,35,70,105,140,175,210]
    ys = [round(30 - (30-endY)*((i/6)**1.6)) for i in range(7)]
    stroke = "#2ee6c6" if mom >= 90 else "#38b6ff" if mom >= 55 else "#8ea3c8"
    pts = " ".join(f"{x},{y}" for x, y in zip(xs, ys))
    area = f"M0 {ys[0]} " + " ".join(f"L{x} {y}" for x, y in zip(xs[1:], ys[1:])) + " L210 34 L0 34Z"
    return f'<svg class="spark" viewBox="0 0 210 34"><path d="{area}" fill="url(#g1)"/><polyline points="{pts}" fill="none" stroke="{stroke}" stroke-width="2.4" stroke-linecap="round"/><circle cx="210" cy="{ys[-1]}" r="3.2" fill="{stroke}"/></svg>'
def _timeline(mom):  # tečky v čase; vyšší momentum = víc čerstvých (mint) tečet vpravo
    fresh = 100 - min(62, mom * 0.42)
    h = '<div class="track"><div class="base"></div><div class="trail" style="left:10%;width:84%"></div>'
    for x, sz in [(14,8),(36,10),(58,12),(78,14),(93,17)]:
        h += f'<span class="{"dot mint" if x >= fresh else "dot"}" style="left:{x}%;width:{sz}px;height:{sz}px"></span>'
    return h + '</div><div class="axis"><span>před 30 dny</span><span>21</span><span>14</span><span>7</span><span>dnes</span></div>'

_TREND_CSS = ''':root{--line:#1e2c4a;--tx:#eaf1ff;--mut:#8ea3c8;--dim:#5f7398;--mint:#2ee6c6;--cyan:#38b6ff;--blue:#3a7bff;
--g:linear-gradient(135deg,#2ee6c6,#38b6ff 55%,#3a7bff);--gsoft:linear-gradient(135deg,#2ee6c633,#3a7bff22);
--linkedin:#3b95e8;--youtube:#ff3b3b;--tiktok:#ff2d74;--instagram:#e754a0;--x:#4bb0f5;--reddit:#ff6a33;--web:#9bb0cf;}
*{box-sizing:border-box;margin:0}
body{background:radial-gradient(1100px 620px at 6% -8%,rgba(46,230,198,.12),transparent 58%),radial-gradient(1050px 760px at 102% 2%,rgba(58,123,255,.16),transparent 56%),radial-gradient(1200px 900px at 55% 122%,rgba(56,182,255,.11),transparent 60%),linear-gradient(180deg,#0a1122,#070d1c);background-attachment:fixed;color:var(--tx);font:15px/1.5 \'DM Sans\',-apple-system,Segoe UI,Roboto,sans-serif;padding:34px 30px 90px;-webkit-font-smoothing:antialiased}
.wrap{max-width:1200px;margin:0 auto} .ic{width:1em;height:1em;fill:currentColor;vertical-align:-.12em}
.kicker{display:inline-flex;align-items:center;gap:8px;font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--mint);background:var(--gsoft);border:1px solid #2ee6c633;padding:7px 14px;border-radius:30px}
.ki{width:15px;height:15px;fill:var(--mint);filter:drop-shadow(0 0 6px #2ee6c6aa)}
h1{font-size:34px;font-weight:800;letter-spacing:-.5px;margin:14px 0 4px;line-height:1.1} h1 .grad{background:var(--g);-webkit-background-clip:text;background-clip:text;color:transparent}
.lede{color:var(--mut);max-width:740px;font-size:15.5px}
.tmeta{color:var(--mut);font-size:13.5px;font-weight:600;margin:7px 0 0}
.layer{display:inline-flex;align-items:center;gap:9px;color:var(--dim);font-size:12.5px;font-weight:700;margin:24px 0 13px;text-transform:uppercase;letter-spacing:.1em}
.layer b{color:#04101f;background:var(--g);padding:3px 9px;border-radius:7px;letter-spacing:0} .hint{color:var(--dim);font-weight:600;text-transform:none;letter-spacing:0;font-size:12px}
.mapwrap{padding:0}
.field{display:grid;grid-template-columns:repeat(6,1fr);grid-template-rows:146px 146px 116px 116px 100px;gap:16px}
.tile{border-radius:16px;padding:16px 18px;position:relative;overflow:hidden;border:1px solid #ffffff2b;cursor:pointer;display:flex;flex-direction:column;justify-content:space-between;transition:.2s;box-shadow:0 12px 30px #00000066}
.tile:hover{transform:translateY(-3px);box-shadow:0 20px 50px #0009,0 0 0 1px var(--c);border-color:#ffffff40}
.tile .glow{position:absolute;inset:0;background:linear-gradient(140deg,#0b1830,#080f1e)}
.tile .glow::after{content:"";position:absolute;inset:0;background:radial-gradient(175% 165% at 100% 12%,var(--c),transparent 62%);opacity:1}
.tile>*{position:relative;z-index:1}
.tile .tnum{font-size:40px;font-weight:800;color:var(--c);line-height:.9;letter-spacing:-1px} .tile .tnum small{display:none}
.tile .bt{font-weight:800;letter-spacing:-.2px;line-height:1.12;color:#fff;text-shadow:0 1px 8px #0007}
.tile .arw{align-self:flex-start;display:inline-flex;align-items:center;gap:5px;font-weight:800;background:#04101fcc;color:#eafcff;padding:3px 9px;border-radius:20px;font-size:12px;backdrop-filter:blur(4px)}
.tile.xl{grid-column:span 3;grid-row:span 2}.tile.xl .bt{font-size:25px;max-width:86%}
.tile.xl .tnum{font-size:64px}.tile.xl .tnum small{display:block;font-size:11px;font-weight:800;letter-spacing:.14em;opacity:.72;text-shadow:none;margin-top:4px}
.tile.wide{grid-column:span 3}.tile.wide .bt{font-size:17px}.tile.wide .tnum{font-size:44px}
.tile.md{grid-column:span 2}.tile.md .bt{font-size:14.5px}
.mlegend{grid-column:span 4;border-radius:16px;border:1px dashed #26365a;background:#0b1526;display:flex;align-items:center;gap:18px;padding:0 22px;color:var(--dim);font-size:12.5px;flex-wrap:wrap}
.mlegend .scale{display:flex;height:10px;width:160px;border-radius:5px;overflow:hidden}.mlegend .scale i{flex:1} .mlegend b{color:var(--tx)}
.tcard{background:linear-gradient(180deg,#0e1a33,#0a1020);border:1px solid var(--line);border-left:4px solid var(--c);border-radius:18px;overflow:hidden;box-shadow:0 16px 44px #00000066}
.tcard+.tcard{margin-top:22px}
.tcard.flash{animation:fl 1.5s ease}@keyframes fl{0%,100%{box-shadow:0 14px 40px #0004}25%{box-shadow:0 0 0 2px var(--c),0 14px 40px #0004}}
.head{display:grid;grid-template-columns:auto 1fr 240px;gap:10px;align-items:start;padding:22px 22px;position:relative}
.head::after{content:"";position:absolute;inset:0;background:radial-gradient(80% 140% at -2% 0%,var(--c),transparent 42%);opacity:.09;pointer-events:none}
.rk{text-align:left;line-height:1;position:relative;z-index:1;padding-top:0}
.rk .n{font-size:40px;font-weight:800;line-height:.82;background:var(--g);-webkit-background-clip:text;background-clip:text;color:transparent}
.rk small{display:block;font-size:9.5px;letter-spacing:.16em;color:var(--dim);font-weight:700;margin-top:2px}
.main{position:relative;z-index:1}
.tt{font-size:28px;font-weight:800;letter-spacing:-.3px;line-height:1.05;margin-bottom:2px;display:flex;align-items:center;gap:9px;flex-wrap:wrap}
.tt .rocket{font-size:11px;font-weight:800;color:#04101f;background:linear-gradient(135deg,#2ee6c6,#38b6ff);padding:2px 8px;border-radius:20px}
.why{color:var(--mut);font-size:12.5px;margin-bottom:0;line-height:1.3}
.dist{display:flex;align-items:center;gap:9px;flex-wrap:wrap;font-size:12.5px;margin-left:-47px;margin-top:22px}
.pd{display:inline-flex;align-items:center;gap:7px;font-weight:800;background:var(--pc);color:#fff;border:1px solid #ffffff33;border-radius:9px;padding:4px 11px;font-size:12.5px;box-shadow:0 2px 8px #00000040}.pd svg{width:14px;height:14px;fill:#fff}
.dtot{color:var(--mut);font-weight:600}
.right{display:flex;flex-direction:column;align-items:flex-end;gap:9px;justify-self:end;position:relative;z-index:1}
.ts{display:flex;flex-direction:column;align-items:flex-end;line-height:1}
.tsnum{font-size:38px;font-weight:800;color:var(--c);letter-spacing:-1px}
.tslab{font-size:9px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--dim);margin-top:3px}
.up{display:inline-flex;align-items:center;gap:5px;font-weight:800;font-size:13px;color:var(--mint);background:#2ee6c61a;border:1px solid #2ee6c640;padding:3px 10px;border-radius:20px;white-space:nowrap}
.up.b{color:var(--cyan);background:#38b6ff1a;border-color:#38b6ff40}.up.d{color:var(--mut);background:#8ea3c81a;border-color:#8ea3c840}
.spark{width:210px;height:34px;display:block}
.body{padding:4px 22px 22px;margin:0 4px;border-top:1px solid #ffffff0d}
.dlabel{display:flex;align-items:center;gap:9px;font-size:11.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#cddaf2;margin:17px 0 10px}
.di{width:26px;height:26px;border-radius:8px;background:linear-gradient(140deg,var(--c),#10233f);display:inline-grid;place-items:center;flex:none;box-shadow:0 0 12px -5px var(--c)} .di svg{width:14px;height:14px;fill:#fff}
.strong{list-style:none;display:grid;gap:7px} .strong li{position:relative;padding-left:20px;font-size:13.5px;color:#cfdef7} .strong li:before{content:"";position:absolute;left:2px;top:7px;width:7px;height:7px;border-radius:50%;background:var(--c)}
.track{position:relative;height:36px;margin-top:2px}
.track .base{position:absolute;left:0;right:0;top:50%;height:2px;background:#17244190;border-radius:2px}
.track .trail{position:absolute;top:50%;height:3px;transform:translateY(-50%);border-radius:3px;background:linear-gradient(90deg,#2ee6c600,#2ee6c6,#38b6ff);box-shadow:0 0 12px #38b6ff55}
.dot{position:absolute;top:50%;transform:translate(-50%,-50%);border-radius:50%;background:radial-gradient(circle at 35% 30%,#bff3ff,#38b6ff);box-shadow:0 0 10px #38b6ff77}
.dot.mint{background:radial-gradient(circle at 35% 30%,#d6fff4,#2ee6c6);box-shadow:0 0 10px #2ee6c688}
.axis{display:flex;justify-content:space-between;color:var(--dim);font-size:10.5px;margin-top:2px}
.ideas{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.idea{background:#0d1730;border:1px solid var(--line);border-radius:12px;padding:13px 14px}
.idea .fmt{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:800;color:#fff;background:linear-gradient(135deg,#173654,#0f2036);border:1px solid #2ee6c633;padding:4px 11px;border-radius:20px;margin-bottom:9px} .idea .fmt svg{width:12px;height:12px;fill:#fff}
.idea .it{font-size:13px;font-weight:700;line-height:1.3;color:#e7f0ff}
.angle{display:flex;align-items:center;gap:12px;background:var(--gsoft);border:1px solid #2ee6c633;border-radius:12px;padding:13px 16px;margin-top:16px}
.angle b{color:var(--mint)}.angle .txt{font-size:13.5px;font-weight:600}.angle .di{background:none;box-shadow:none;width:auto;height:auto}.angle .di svg{width:20px;height:20px}
.geo{display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:800;color:#bcd;background:#0e1d3a;border:1px solid var(--line);padding:3px 9px;border-radius:20px}
.geotop{margin-bottom:9px}
.pieces2{display:grid;gap:8px}
.pc2{display:flex;align-items:center;gap:10px;background:#0d1730;border:1px solid var(--line);border-radius:10px;padding:8px 11px;text-decoration:none;color:inherit;transition:.15s}
.pc2:hover{border-color:var(--c);transform:translateX(3px)}
.pcp{width:26px;height:26px;border-radius:7px;display:grid;place-items:center;flex:none}.pcp svg{width:14px;height:14px;fill:#fff}
.pctx{display:flex;flex-direction:column;gap:2px;min-width:0}
.pctt{font-size:12.5px;font-weight:700;color:#e7f0ff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pcm{font-size:11px;color:var(--dim);font-weight:600;display:inline-flex;align-items:center}.pcm svg{vertical-align:-1px}
#c1{border-left-width:5px} #c10 .rk .n{font-size:30px}
.foot{color:var(--dim);margin-top:44px;font-size:12.5px;text-align:center;border-top:1px solid var(--line);padding-top:20px} .foot b{background:var(--g);-webkit-background-clip:text;background-clip:text;color:transparent}
@media(max-width:900px){.field{grid-template-columns:repeat(2,1fr)}.tile.xl,.tile.wide,.tile.md,.mlegend{grid-column:span 2;grid-row:span 1}.head{grid-template-columns:60px 1fr}.right{display:none}.ideas{grid-template-columns:1fr}}'''

def render_trend(topic, themes, out_html, subtitle=""):
    T = sorted(themes, key=lambda t: t.get("score", 0), reverse=True)[:10]
    n = len(T)
    sprite = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
              '<linearGradient id="g1" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#2ee6c6" stop-opacity=".4"/><stop offset="1" stop-color="#2ee6c6" stop-opacity="0"/></linearGradient>'
              + "".join(f'<symbol id="{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICON.items()) + '</defs></svg>')
    tiles = []
    for i, t in enumerate(T):
        c = _COOL[min(i, len(_COOL)-1)]; cls = "xl" if i == 0 else "wide" if i < 3 else "md"
        arw = ("🚀 " if t.get("rocket") else "▲ ") + f'+{t.get("momentum",0)} %'
        num = f'{t.get("score",0)}<small>TREND SCORE</small>' if i == 0 else f'{t.get("score",0)}'
        tiles.append(f'<div class="tile {cls}" data-go="c{i+1}" style="--c:{c}"><div class="glow"></div><div class="tnum">{num}</div><div class="bt">{html.escape(t.get("name",""))}</div><div class="arw">{arw}</div></div>')
    legend = '<div class="mlegend"><span><b>Trend Score</b> = síla trendu</span><div class="scale"><i style="background:#6b78c4"></i><i style="background:#4a6fe8"></i><i style="background:#3a83f5"></i><i style="background:#38b6ff"></i><i style="background:#27d8ce"></i><i style="background:#2ee6c6"></i></div><span>méně žhavé → nejžhavější</span><span>· velikost dlaždice = skóre</span></div>'
    cards = []
    for i, t in enumerate(T):
        c = _COOL[min(i, len(_COOL)-1)]; mom = t.get("momentum", 0)
        upcls = "" if mom >= 90 else " b" if mom >= 55 else " d"
        up = ("🚀 " if t.get("rocket") else "▲ ") + f"+{mom} %"
        rocket = '<span class="rocket">🚀 předstih</span>' if t.get("rocket") else ""
        plats = t.get("platforms", {}); total = sum(plats.values())
        pds = "".join(f'<span class="pd" style="--pc:var(--{p})">{_u(p)}{cnt}</span>' for p, cnt in plats.items())
        why = "".join(f"<li>{html.escape(w)}</li>" for w in t.get("why", [])[:3])
        ideas = ""
        for idea in t.get("ideas", [])[:3]:
            ik, lab = _IDEA.get((idea.get("fmt") or "reel").lower(), ("mobile", "Reel"))
            ideas += f'<div class="idea"><span class="fmt">{_u(ik)}{lab}</span><div class="it">{html.escape(idea.get("text",""))}</div></div>'
        g = t.get("geo", "")  # geo štítek tématu
        geo_badge = ('<span class="geo">🇨🇿🌍 lokální + globální</span>' if g == "mix"
                     else '<span class="geo">🌍 globální · předstih</span>' if g == "global"
                     else '<span class="geo">🇨🇿 lokální</span>' if g == "cs" else "")
        pieces_html = ""  # konkrétní příspěvky, co trend táhnou (top 2–3, propojka na Viral Board)
        for pc in t.get("pieces", [])[:3]:
            pcol = PLAT.get(pc.get("platform"), ("", "#3a5cff", "web"))[1]
            flag = "🇨🇿" if pc.get("geo") == "cs" else "🌍"
            eng = f'{_svg("heart",11,"#ff5d8f")} {_fmt(pc.get("likes",0))}'
            if pc.get("views"): eng += f' &nbsp;·&nbsp; {_svg("eye",11,"#38b6ff")} {_fmt(pc["views"])}'
            pieces_html += f'<a class="pc2" href="{html.escape(pc.get("url","#"))}" target="_blank"><span class="pcp" style="background:{pcol}">{_u(pc.get("platform","web"))}</span><span class="pctx"><span class="pctt">{flag} {html.escape(pc.get("title",""))}</span><span class="pcm">{eng}</span></span></a>'
        pieces_block = f'<div class="dlabel"><span class="di">{_u("flame")}</span>Příspěvky, které trend táhnou</div><div class="pieces2">{pieces_html}</div>' if pieces_html else ""
        cards.append(f'''<div class="tcard{" flash" if i==0 else ""}" id="c{i+1}" style="--c:{c}">
  <div class="head"><div class="rk"><span class="n">{i+1}.</span><small>TÉMA</small></div>
    <div class="main"><div class="tt">{html.escape(t.get("name",""))}{rocket}</div><div class="why">{html.escape(t.get("desc",""))}</div>
      <div class="dist">{pds}<span class="dtot">· {total} {_prisp(total)}</span>{geo_badge}</div></div>
    <div class="right"><div class="ts"><span class="tsnum">{t.get("score",0)}</span><span class="tslab">Trend Score</span></div><span class="up{upcls}">{up}</span>{_spark(mom)}</div></div>
  <div class="body">
    <div class="dlabel"><span class="di">{_u("bolt")}</span>Proč je trend silný</div><ul class="strong">{why}</ul>
    <div class="dlabel"><span class="di">{_u("trendup")}</span>Akcelerace v čase</div>{_timeline(mom)}
    {pieces_block}
    <div class="dlabel"><span class="di">{_u("edit")}</span>Ukázky, jak může obsah vypadat</div><div class="ideas">{ideas}</div>
    <div class="angle"><span class="di">{_u("bulb")}</span><span class="txt"><b>Hlavní úhel:</b> {html.escape(t.get("angle",""))}</span></div>
  </div></div>''')
    lede = "Mapa celého pole trendů (velikost i barva = Trend Score) → žebříček s kartou pro každé téma: proč je silné, akcelerace v čase a ukázky obsahu."
    tmeta = f'<p class="tmeta">{html.escape(subtitle)}</p>' if subtitle else ""
    doc = ('<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>TOP {n} trendů — {html.escape(topic)}</title><style>' + _TREND_CSS + '</style></head><body><div class="wrap">'
        + sprite
        + '<span class="kicker"><svg class="ki"><use href="#scout"/></svg> Content Scout · Trend Board</span>'
        + f'<h1>TOP {n} trendů — <span class="grad">{html.escape(topic)}</span></h1>'
        + tmeta
        + f'<p class="lede">{lede}</p>'
        + '<div class="layer"><b>MAPA</b> Trendové pole <span class="hint">— velikost i barva = Trend Score · klik skočí na kartu</span></div>'
        + '<div class="mapwrap"><div class="field">' + "".join(tiles) + legend + '</div></div>'
        + f'<div class="layer" style="margin-top:30px"><b>ŽEBŘÍČEK</b> TOP {n} trendů</div>'
        + "\n".join(cards)
        + '<div class="foot">CliqSales · <b>Content Scout</b> · Trend Board</div>'
        + '<script>document.querySelectorAll(".tile[data-go]").forEach(function(t){t.addEventListener("click",function(){var r=document.getElementById(t.dataset.go);if(!r)return;r.scrollIntoView({behavior:"smooth",block:"center"});r.classList.remove("flash");void r.offsetWidth;r.classList.add("flash");});});</script>'
        + '</div></body></html>')
    open(out_html, "w", encoding="utf-8").write(doc)
    return n
