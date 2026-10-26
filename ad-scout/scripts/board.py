#!/usr/bin/env python3
"""Renderer: scout-report.json → Product Intelligence Board HTML.

Styl = golden template assets/board-template.html (masthead + velká čísla sekcí,
bez oddělovačů, 3 gradienty na pozadí, loga obchodů z favicon). Klientský výstup:
vykání, žádná vendor/zdroj/aktor jména (viz references/output-sanitization.md).

Sekce se **auto-číslují** podle toho, které mají data (žádné díry). Sekce, které
plní model (reviews.hooks / assortment / action_plan / signály), se zobrazí jen
když existují.

v0.1 — DRAFT.
"""
import html
import json
import sys

CSS = """
:root{--bg:224 86% 5%;--s1:226 36% 10.5%;--s2:228 31% 14%;--bd:226 26% 17%;
 --fg:210 32% 97%;--fgm:220 14% 80%;--fgd:221 11% 62%;--brand:203 100% 49%;--bl:205 100% 60%;--mint:178 85% 78%;
 --ind:208 100% 55%;--indd:214 92% 40%;--succ:152 60% 46%;--warn:37 92% 56%;--coral:350 86% 65%;
 --f:'Inter',system-ui,sans-serif;--m:'JetBrains Mono',monospace}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--f);background:hsl(var(--bg));color:hsl(var(--fg));-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;background:
 radial-gradient(900px 600px at 18% -8%,hsl(var(--ind)/.24),transparent 60%),
 radial-gradient(1100px 700px at 88% 4%,hsl(var(--brand)/.16),transparent 58%),
 radial-gradient(800px 800px at 60% 120%,hsl(var(--ind)/.13),transparent 55%)}
.wrap{position:relative;z-index:1;max-width:1340px;margin:0 auto;padding:40px 48px 70px}
.mono,.mchip{font-family:var(--m)}
.mchip{background:hsl(var(--s1));border:1px solid hsl(var(--bd));border-radius:7px;padding:3px 8px;color:hsl(var(--fgm));font-size:11px}
.phead{display:flex;align-items:flex-start;gap:16px;margin-bottom:34px}
.phead h1{font-size:36px;font-weight:800;letter-spacing:-.03em;line-height:1.05}
.phead h1 .theme{background:linear-gradient(90deg,#119CFF,#97F8F4);-webkit-background-clip:text;background-clip:text;color:transparent}
.phead .meta{display:flex;align-items:center;gap:9px;margin-top:12px;font-size:13.5px;color:hsl(var(--fgm));flex-wrap:wrap}
.phead .meta .src{font-family:var(--m);font-size:13px;color:hsl(var(--fgd))}.phead .meta .src b{color:hsl(var(--bl));font-weight:600}
.phead .right{margin-left:auto}
.pill{display:inline-flex;align-items:center;gap:7px;height:30px;padding:0 13px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid hsl(var(--succ)/.32);background:hsl(var(--succ)/.09);color:hsl(var(--succ));white-space:nowrap}
.pill .dt{width:7px;height:7px;border-radius:50%;background:currentColor}
.hero{display:grid;grid-template-columns:300px 1fr;gap:32px;align-items:center;margin-bottom:16px}
.pic{aspect-ratio:1;border-radius:20px;overflow:hidden;background:#fff;border:1px solid hsl(var(--bd));position:relative}
.pic img{width:100%;height:100%;object-fit:contain}
.pic .rt{position:absolute;top:13px;left:13px;background:hsl(152 60% 42%);color:#fff;font-weight:800;font-size:13px;padding:5px 12px;border-radius:9px}
.hi h1{font-size:29px;font-weight:800;letter-spacing:-.02em}.hi h1 span{color:hsl(var(--fgm));font-weight:600;font-size:17px}
.hi .cat{color:hsl(var(--fgm));font-size:14px;margin:11px 0 22px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}
.kpi{border-radius:14px;padding:15px 16px;background:linear-gradient(180deg,hsl(var(--s1)),hsl(var(--bg)/.4));border:1px solid hsl(var(--bd)/.85);position:relative;overflow:hidden}
.kpi::after{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:linear-gradient(90deg,transparent,var(--ac,hsl(var(--brand))),transparent)}
.kpi .l{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:hsl(210 22% 86%)}
.kpi .v{font-size:23px;font-weight:700;font-family:var(--m);margin-top:8px;color:var(--ac,hsl(var(--fg)))}.kpi .v small{font-size:12px;color:hsl(var(--fgm))}
.kpi .d{font-size:10.5px;color:hsl(var(--fgm));margin-top:5px}
.sec{margin-top:38px}.sechead{display:flex;align-items:baseline;gap:10px;margin-bottom:9px}
.secno{font-family:var(--m);font-size:36px;font-weight:700;color:hsl(var(--bl));line-height:1}
.sec h2{font-size:26px;font-weight:800;letter-spacing:-.025em}.sec .lead{font-size:14px;color:hsl(var(--fgm));margin-bottom:22px}
.card{border-radius:16px;background:linear-gradient(180deg,hsl(var(--s1)),hsl(var(--bg)/.35));border:1px solid hsl(var(--bd)/.85)}.lb{padding:8px 16px}
.row{display:grid;grid-template-columns:18px 30px 1fr 108px;align-items:center;gap:12px;padding:11px 6px;border-bottom:1px solid hsl(var(--bd)/.4)}.row:last-child{border-bottom:none}
.lg{width:30px;height:30px;border-radius:8px;background:#fff;display:grid;place-items:center;overflow:hidden;border:1px solid hsl(var(--bd)/.55)}.lg img{width:22px;height:22px;object-fit:contain}
.rk{font-family:var(--m);font-size:12px;font-weight:700;color:hsl(var(--fgd));text-align:center}
.st b{font-weight:600;font-size:14px;display:block}.ship{font-size:10.5px;color:hsl(var(--fgd));font-family:var(--m)}
.bar{height:6px;border-radius:3px;background:hsl(var(--s2));margin-top:6px;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,hsl(var(--ind)),hsl(var(--indd)))}
.price{font-family:var(--m);font-size:15px;font-weight:700;text-align:right}
.row.me{background:linear-gradient(90deg,hsl(38 92% 56%/.12),transparent);border-radius:9px}.row.me .st b{color:hsl(38 92% 68%)}.row.me .fill{background:linear-gradient(90deg,hsl(38 92% 56%),hsl(25 95% 52%))}
.row.cheap .fill{background:linear-gradient(90deg,hsl(152 60% 46%),hsl(168 72% 42%))}
.tag{font-family:var(--m);font-size:8.5px;font-weight:700;border-radius:5px;padding:1px 6px}.tag.me{background:hsl(38 92% 56%);color:#1a1204}.tag.cheap{background:hsl(152 60% 46%);color:#032019}
.duo{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.blk{border-radius:16px;background:linear-gradient(180deg,hsl(var(--s1)),hsl(var(--bg)/.35));border:1px solid hsl(var(--bd)/.85);padding:20px 22px}
.blk .h{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:hsl(var(--fgm));margin-bottom:14px}
.alert{display:flex;gap:12px;padding:12px 14px;border-radius:11px;background:hsl(var(--coral)/.08);border:1px solid hsl(var(--coral)/.3);margin-bottom:10px;font-size:13px;line-height:1.45}
.alert.win{background:hsl(152 60% 46%/.1);border-color:hsl(152 60% 46%/.32)}.alert b{color:hsl(var(--fg))}
.avail{display:flex;justify-content:space-between;font-size:13px;padding:8px 0;border-bottom:1px solid hsl(var(--bd)/.35)}.avail:last-child{border-bottom:none}
.avail .in{color:hsl(152 70% 62%);font-weight:600;font-size:11.5px}.avail .out{color:hsl(var(--coral));font-weight:600;font-size:11.5px}
.hookout{margin-top:14px;background:hsl(var(--brand)/.08);border:1px solid hsl(var(--brand)/.28);border-radius:11px;padding:12px 14px;font-size:12.5px;line-height:1.5;color:hsl(var(--bl))}.hookout b{color:hsl(var(--mint))}
.hooks{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:4px}
.hook{display:flex;gap:13px;padding:16px 18px;border-radius:14px;background:linear-gradient(180deg,hsl(var(--s1)),hsl(var(--bg)/.35));border:1px solid hsl(var(--bd)/.8)}
.hook .hno{font-family:var(--m);font-size:13px;font-weight:700;color:hsl(var(--bl));background:hsl(var(--bl)/.12);border:1px solid hsl(var(--bl)/.3);width:28px;height:28px;border-radius:8px;display:grid;place-items:center;flex:none}
.hook .ht{font-size:14px;font-weight:600;line-height:1.42}.hook .hpat{display:inline-block;font-family:var(--m);font-size:9px;text-transform:uppercase;color:hsl(var(--mint));background:hsl(var(--mint)/.1);border:1px solid hsl(var(--mint)/.25);border-radius:6px;padding:2px 8px;margin-top:9px}
.hook .hsrc{font-size:11.5px;color:hsl(var(--fgd));margin-top:9px;font-style:italic}.hook .hwhy{font-size:12px;color:hsl(var(--fgm));margin-top:6px;line-height:1.5}
.vchip{display:inline-flex;font-size:12.5px;background:hsl(var(--s2));border:1px solid hsl(var(--bd));border-radius:9px;padding:7px 12px;margin:4px 6px 4px 0}
.vchip.gap{color:hsl(38 92% 66%);border-color:hsl(38 92% 56%/.4);background:hsl(38 92% 56%/.08)}
.plan .pr{display:flex;gap:15px;margin-bottom:18px;line-height:1.62;font-size:14px}.plan .pr:last-child{margin-bottom:0}
.plan .ic{width:32px;height:32px;border-radius:9px;flex:none;display:grid;place-items:center}.plan .ic svg{width:17px;height:17px;fill:currentColor}
.plan b{color:hsl(var(--fg))}.plan .pr>div{color:hsl(var(--fgm))}
.rvi{font-size:13px;line-height:1.5;padding:8px 0 8px 18px;position:relative;color:hsl(var(--fgm));border-bottom:1px solid hsl(var(--bd)/.3)}.rvi:last-child{border-bottom:none}
.rvi::before{content:"";position:absolute;left:2px;top:14px;width:6px;height:6px;border-radius:50%}
.rvi.pl::before{background:hsl(152 70% 55%)}.rvi.mn::before{background:hsl(var(--coral))}
.subh{font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:hsl(var(--fgm));margin:26px 0 14px}
.foot{margin-top:40px;font-family:var(--m);font-size:10.5px;color:hsl(var(--fgm));line-height:1.6}
"""

HEAD = ('<!doctype html><html lang="cs"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800'
        '&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet"><style>{css}</style></head><body><div class="wrap">')


def e(x):
    return html.escape(str(x if x is not None else ""))


def _fmt(n):
    try:
        return f"{int(round(float(n))):,}".replace(",", " ")
    except Exception:
        return e(n)


def render(report, out_path):
    p = report.get("product") or {}
    kpi = report.get("kpi") or {}
    cl = report.get("client") or {}
    q = (report.get("trigger") or {}).get("query", "")
    market = report.get("market", "cz").upper()
    parts = [HEAD.format(title=f'Product Intelligence Board — „{e(q)}"', css=CSS)]

    parts.append(
        f'<div class="phead"><div><h1>Product Intelligence Board '
        f'<span class="theme">— „{e(q)}"</span></h1>'
        f'<div class="meta"><span class="mchip">ad-scout</span> <span>trh {e(market)}</span> · '
        f'<span class="mono">{e(report.get("generated_at"))}</span> · '
        f'<span class="src">z <b>veřejně dostupných</b> tržních dat</span></div></div>'
        f'<div class="right"><span class="pill"><span class="dt"></span>REÁLNÁ DATA</span></div></div>')

    img = p.get("image_url") or "assets/venum-4.jpg"
    rating = p.get("rating_pct")
    rt = f'<span class="rt">★ {e(rating)} %</span>' if rating else ""
    parts.append(
        f'<div class="hero"><div class="pic"><img src="{e(img)}" alt="">{rt}</div>'
        f'<div class="hi"><h1>{e(p.get("name") or q)} <span>{e(p.get("category",""))}</span></h1>'
        f'<div class="cat">klient: <b style="color:hsl(var(--fg))">{e((cl.get("name") or cl.get("domain") or "—"))}</b>'
        f' · {e(p.get("reviews_count",""))} recenzí · {e(p.get("shops_count",""))} obchodů na trhu</div>{_kpis(kpi)}</div></div>')

    # auto-číslované sekce (jen ty, co mají data)
    n = 1
    for fn in (_price_map, _signals, _reviews, _assortment, _search, _meta):
        s = fn(report)
        if s:
            parts.append(_section(f"{n:02d}", *s))
            n += 1
    plan = _plan(report)
    if plan:
        parts.append(_section("→", *plan))

    parts.append(f'<div class="foot">CliqSales · Ad Scout · Product Intelligence Board · '
                 f'spuštěno názvem produktu · REÁLNÁ DATA z veřejných tržních zdrojů — ceny, dostupnost, '
                 f'recenze a varianty · výsledky vyhledávání (organika + placené) · veřejná knihovna reklam · '
                 f'denní aktualizace · {e(report.get("generated_at"))}</div></div></body></html>')
    with open(out_path, "w") as f:
        f.write("".join(x for x in parts if x))
    return out_path


def _kpis(kpi):
    if not kpi:
        return ""
    c = []
    if kpi.get("lowest_price") is not None:
        c.append(f'<div class="kpi" style="--ac:hsl(152 60% 52%)"><div class="l">Nejnižší</div>'
                 f'<div class="v">{_fmt(kpi["lowest_price"])}<small> Kč</small></div><div class="d">{e(kpi.get("lowest_shop",""))}</div></div>')
    if kpi.get("your_landed") is not None:
        c.append(f'<div class="kpi" style="--ac:hsl(38 92% 60%)"><div class="l">Vaše cena</div>'
                 f'<div class="v">{_fmt(kpi["your_landed"])}<small> Kč</small></div>'
                 f'<div class="d">index {e(kpi.get("price_index_pct","–"))} % mediánu</div></div>')
    if kpi.get("rank"):
        c.append(f'<div class="kpi" style="--ac:hsl(var(--brand))"><div class="l">Pozice</div>'
                 f'<div class="v">{e(kpi["rank"])}.<small>/{e(kpi.get("rank_of",""))}</small></div><div class="d">v ceně s dopravou</div></div>')
    if kpi.get("reviews_count") is not None:
        c.append(f'<div class="kpi" style="--ac:hsl(var(--succ))"><div class="l">Hodnocení</div>'
                 f'<div class="v">{e(kpi.get("rating_pct","–"))} %</div><div class="d">{e(kpi["reviews_count"])} recenzí</div></div>')
    return f'<div class="kpis">{"".join(c)}</div>' if c else ""


def _price_map(r):
    pm = r.get("price_map") or []
    if not pm:
        return None
    mx = max(x["landed"] for x in pm) or 1
    rows = []
    for i, o in enumerate(pm, 1):
        cls = "row" + (" cheap" if o.get("is_min") else "") + (" me" if o.get("is_client") else "")
        logo = f'<div class="lg"><img src="{e(o["logo"])}" alt=""></div>' if o.get("logo") else '<div class="lg"></div>'
        tag = ' <span class="tag cheap">MIN</span>' if o.get("is_min") else (' <span class="tag me">VY</span>' if o.get("is_client") else "")
        ship = f'doprava {_fmt(o["shipping"]) + " Kč" if o.get("shipping") else "zdarma"} → celkem {_fmt(o["landed"])} Kč'
        if o.get("note"):
            ship += f' · {e(o["note"])}'
        w = int(o["landed"] / mx * 100)
        rows.append(f'<div class="{cls}"><div class="rk">{i}</div>{logo}<div class="st"><b>{e(o["shop"])}</b>'
                    f'<span class="ship">{ship}</span><div class="bar"><div class="fill" style="width:{w}%"></div></div></div>'
                    f'<div class="price">{_fmt(o["price"])}{tag}</div></div>')
    return ("Cenová mapa",
            "Kdo prodává stejný produkt a za kolik — <b style=\"color:hsl(var(--fg))\">cena včetně dopravy</b>, protože samotná cena bez dopravy je zavádějící.",
            f'<div class="card shops"><div class="lb">{"".join(rows)}</div></div>')


def _signals(r):
    sig = r.get("signals") or {}
    drops = sig.get("price_drops") or []
    low = sig.get("low_30d") or {}
    stock = sig.get("stock") or {}
    outs = stock.get("out_of_stock") or []
    avail = stock.get("availability") or []
    if not (drops or outs or avail or low.get("market_low_30d")):
        return None
    left = '<div class="blk"><div class="h">Cenopád — pohyb cen</div>'
    for d in drops:
        left += f'<div class="alert"><div><b>{e(d.get("shop"))} {e(d.get("pct"))} %</b> na {_fmt(d.get("landed"))} Kč ({_fmt(d.get("delta"))} Kč).</div></div>'
    if low.get("market_low_30d"):
        cur = low.get("current_low")
        trend = ("pod 30denním minimem → tlak dolů" if (cur and cur < low["market_low_30d"])
                 else "nad 30denním minimem" if cur else "")
        extra = f' · dnes trh na <b>{_fmt(cur)} Kč</b> ({trend})' if cur else ''
        left += (f'<div class="alert win"><div>Nejnižší cena za <b>30 dní</b>: {_fmt(low["market_low_30d"])} Kč'
                 f'{extra}.</div></div>')
    if not drops and not low.get("market_low_30d"):
        left += '<div style="font-size:13px;color:hsl(var(--fgm))">První snímek — denní cenopád se začne hlídat od zítřka (diff proti dnešku).</div>'
    left += "</div>"
    right = '<div class="blk"><div class="h">Dostupnost — kde je díra</div>'
    if outs:
        for o in outs:
            right += f'<div class="alert win"><div><b>{e(o.get("shop"))} vyprodáno.</b> Vy skladem → zvedněte bid, berte jeho objednávky.</div></div>'
    for a in avail[:5]:
        st = str(a.get("status", "")).lower()
        cls = "in" if ("sklad" in st or not st) else "out"
        right += f'<div class="avail"><span>{e(a.get("shop"))}</span><span class="{cls}">● {e(a.get("status") or "Skladem")}</span></div>'
    right += "</div>"
    return ("Živé signály — cenopád & dostupnost",
            "Co se na trhu změnilo za posledních pár dní — kdo zlevnil a komu došlo zboží. Na tyhle změny reagujete okamžitě.",
            f'<div class="duo">{left}{right}</div>')


def _reviews(r):
    rv = r.get("reviews") or {}
    hooks = rv.get("hooks") or []
    if not (rv.get("praise") or rv.get("criticism") or hooks):
        return None
    body = '<div class="duo">'
    if rv.get("praise"):
        body += '<div class="blk"><div class="h" style="color:hsl(152 70% 62%)">✓ Co zákazníci chválí</div>'
        body += "".join(f'<div class="rvi pl">{e(p)}</div>' for p in rv["praise"])
        body += "</div>"
    if rv.get("criticism"):
        body += '<div class="blk"><div class="h" style="color:hsl(var(--coral))">✗ Na co si stěžují</div>'
        body += "".join(f'<div class="rvi mn">{e(c)}</div>' for c in rv["criticism"])
        body += "</div>"
    body += "</div>"
    if hooks:
        n = len(hooks)
        adj = "hotový" if n == 1 else ("hotové" if n < 5 else "hotových")
        noun = "námět do reklamy" if n == 1 else ("náměty do reklamy" if n < 5 else "námětů do reklamy")
        body += f'<div class="subh">{n} {adj} {noun} — každý postavený na tom, co zákazníci sami napsali</div>'
        body += '<div class="hooks">'
        for i, h in enumerate(hooks, 1):
            body += (f'<div class="hook"><div class="hno">{i}</div><div><div class="ht">{e(h.get("headline",""))}</div>'
                     f'<span class="hpat">{e(h.get("mechanism",""))}</span>'
                     f'<div class="hsrc">{e(h.get("source",""))}</div>'
                     f'<div class="hwhy">{e(h.get("why",""))}</div></div></div>')
        body += "</div>"
    if rv.get("caution"):
        body += f'<div class="hookout"><b style="color:hsl(var(--coral))">Pozor:</b> {e(rv["caution"])}</div>'
    return ("Recenze → náměty do reklam",
            "Co zákazníci chválí a na co si stěžují — hotový námět na reklamu.", body)


def _assortment(r):
    a = r.get("assortment") or {}
    if not (a.get("have") or a.get("gaps")):
        return None
    chips = "".join(f'<span class="vchip">{e(v)} ✓</span>' for v in a.get("have", []))
    chips += "".join(f'<span class="vchip gap">{e(g.get("variant", g) if isinstance(g, dict) else g)} ✗ nemáte</span>' for g in a.get("gaps", []))
    return ("Sortiment — kde máte mezeru",
            "Které varianty konkurence prodává a vy nemáte v katalogu (doložená poptávka).",
            f'<div class="blk">{chips}</div>')


def _search(r):
    s = r.get("search") or {}
    if not (s.get("organic") or s.get("paid")):
        return None
    org = "".join(f'<div class="avail"><span><b class="mono">{e(o.get("pos"))}.</b>&nbsp; {e(o.get("shop"))}'
                  f'{" · VY" if o.get("is_client") else ""}</span></div>' for o in s.get("organic", [])[:9])
    paid = "".join(f'<span class="vchip">{e(x)}</span>' for x in s.get("paid", []))
    ai = '<div class="hookout" style="margin-top:12px">Nad výsledky běží <b>AI přehled</b> produktu — nová plocha, kde se rozhoduje o prokliku.</div>' if s.get("ai_overview") else ""
    return ("Google — kdo se zobrazí na produkt",
            "Když zákazník vygooglí produkt, tohle mu vyskočí — tady se bojuje o proklik.",
            f'<div class="duo"><div class="blk"><div class="h">Organické výsledky — zdarma</div>{org}</div>'
            f'<div class="blk"><div class="h">Placené — kdo bidují</div>{paid}{ai}</div></div>')


def _meta(r):
    m = r.get("meta_ads") or []
    note_txt = r.get("meta_note")
    if not (m or note_txt):
        return None
    body = ""
    if m:
        rows = []
        for i, a in enumerate(m, 1):
            mon = f' · ~{a["months"]} měsíců' if a.get("months") else ""
            rows.append(f'<div class="row" style="grid-template-columns:18px 1fr 60px"><div class="rk">{i}</div>'
                        f'<div class="st"><b>{e(a.get("advertiser"))}</b><span class="ship">{e(a.get("note",""))}{mon}</span></div>'
                        f'<div class="price">{e(a.get("ads_count"))}</div></div>')
        body += f'<div class="card"><div class="lb">{"".join(rows)}</div></div>'
    if note_txt:
        body += f'<div class="alert" style="margin-top:14px"><div>{e(note_txt)}</div></div>'
    body += ('<div style="font-size:10.5px;color:hsl(var(--fgd));font-family:var(--m);margin-top:10px">'
             'Pozn.: data na úrovni inzerenta, ne přesného produktu.</div>')
    return ("Reklamní aktivita konkurence (Facebook · Instagram)",
            "Kdo jede reklamy a jak dlouho — doba běhu = signál výkonu. Číslo vpravo = reklam v knihovně.", body)


PLAN_ICONS = [
    ("38 92% 62%", '<path d="M12 2a10 10 0 100 20 10 10 0 000-20zm0 18a8 8 0 110-16 8 8 0 010 16zm0-13a5 5 0 100 10 5 5 0 000-10z"/>'),
    ("350 86% 65%", '<path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/>'),
    ("152 70% 60%", '<path d="M9 16.17L4.83 12l-1.42 1.42L9 19 21 7l-1.41-1.42z"/>'),
    ("214 92% 64%", '<path d="M13 3h-2v10h2V3zm4.83 2.17l-1.42 1.42A6.98 6.98 0 0119 12a7 7 0 11-14 0c0-2.06.9-3.9 2.32-5.17L5.9 5.41A8.96 8.96 0 003 12a9 9 0 1018 0c0-2.74-1.23-5.19-3.17-6.83z"/>'),
]


def _plan(r):
    ap = r.get("action_plan") or []
    if not ap:
        return None
    rows = ""
    for i, x in enumerate(ap):
        c, path = PLAN_ICONS[i % len(PLAN_ICONS)]
        rows += (f'<div class="pr"><span class="ic" style="background:hsl({c}/.14);color:hsl({c})">'
                 f'<svg viewBox="0 0 24 24">{path}</svg></span>'
                 f'<div><b>{e(x.get("title"))}</b> {e(x.get("body"))}</div></div>')
    return ("Co s tím — akční plán", "", f'<div class="blk plan">{rows}</div>')


def _section(no, title, lead, body):
    lead_html = f'<div class="lead">{lead}</div>' if lead else ""
    return (f'<div class="sec"><div class="sechead"><span class="secno">{e(no)}</span>'
            f'<h2>{e(title)}</h2></div>{lead_html}{body}</div>')


if __name__ == "__main__":
    rep = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else "board.html"
    print(render(rep, out))
