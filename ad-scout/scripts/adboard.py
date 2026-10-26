#!/usr/bin/env python3
"""Renderer: Viral Ad Board → HTML — stohované sekce, plný kartový design.

Osa = klíčové slovo / téma. Účel: najít vítězné cizí kreativy a vytěžit z nich
přenositelné vzorce (hook · úhel · formát) ke klonování do klientových reklam.

Struktura (klientský board, VŠE česky — bez anglického žargonu pro SMB):
  hlavička (kicker + český H1 + podtitulek účelu)
  → přehled · mapa úhlů · syntéza „proč se inspirovat" + knihovna hooků
  1) PLACENÉ REKLAMY konkurence          (placená sociální kreativa · TOP 20)
  2) ORGANICKÝ OBSAH                      → Krátká videa (hooky/formáty) + Dlouhý obsah (úhly)
  3) ÚHLY VE VYHLEDÁVÁNÍ                  (jaké úhly konkurence jede v searchu — NE share of voice)
  4) JAZYK ZÁKAZNÍKA (Raw Diet)          (námitky/touhy/fráze z komentářů — bez jmen)

Renderer bere BOHATÝ machine contract (per-karta nm/orig/uhel/aw/why/thumb…), který
plní `scout.py`/model. CSS+SVG v `_adboard_assets.py`. **FB+IG → Meta.** Krátká/dlouhá
se klasifikuje z `format` nebo z délky+sítě. Sanitizace rizikově vázaná (obecný „zdroje").

v0.4 — stohované sekce + short/long split + Search→úhly + Jazyk zákazníka + český labeling.
"""
import html
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _adboard_assets import DEMO_CSS, SVG_DEFS  # noqa: E402

AD_SHOW, SHORT_SHOW, LONG_SHOW = 20, 20, 20  # embed pro analýzu (fetch ~20); board zobrazí COLLAPSE_AT + „načíst dalších"
COLLAPSE_AT = 10  # kolik karet v každé sekci vidět hned; zbytek za tlačítkem „Načíst dalších N"

# Viral DNA kondenzát (úroveň A) — 3 mini-karty v boardu (nejlepší Reklama · Organika · Longform)
DNA_CSS = """
.dnagrid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.dnacard{border-radius:15px;border:1px solid hsl(var(--bd)/.85);background:linear-gradient(180deg,hsl(var(--s1)),hsl(var(--bg)/.35));overflow:hidden;display:flex;flex-direction:column}
.dnacard .dthumb{position:relative;aspect-ratio:16/7;overflow:hidden;background:hsl(var(--s2))}
.dnacard .dthumb img{width:100%;height:100%;object-fit:cover;display:block;opacity:.92}
.dnacard .dtag{position:absolute;top:9px;left:9px;font-family:var(--m);font-size:9.5px;font-weight:700;letter-spacing:.07em;padding:3px 9px;border-radius:6px;background:rgba(0,0,0,.62);backdrop-filter:blur(4px)}
.dnacard .dbody{padding:14px 16px 16px;display:flex;flex-direction:column;gap:7px;flex:1}
.dnacard .dnm{font-weight:700;font-size:14px;line-height:1.3;color:hsl(var(--fg))}
.dnacard .dwho{font-size:11.5px;color:hsl(var(--fgd));font-family:var(--m)}
.dnacard .drow{font-size:12.5px;line-height:1.5;color:hsl(var(--fgm))}
.dnacard .drow b{color:hsl(var(--fg))}
.dnacard .dlink{margin-top:auto;padding-top:7px}
@media(max-width:880px){.dnagrid{grid-template-columns:1fr}}
"""


def e(x):
    return html.escape(str(x if x is not None else ""))


def fnum(n):
    try:
        return f"{int(n):,}".replace(",", " ")
    except Exception:
        return e(n)


def fmt_reach(x):
    try:
        x = int(x)
    except Exception:
        return e(x)
    return f"{round(x/1000)} tis." if x < 1_000_000 else f"{x/1_000_000:.1f} mil.".replace(".", ",")


def tier(s):
    s = s or 0
    return "s-hot" if s >= 75 else ("s-warm" if s >= 55 else "s-cool")


NETMETA = {"facebook": ("i-fb", "#0866FF", "Facebook"), "instagram": ("i-ig", "#E4405F", "Instagram"),
           "meta": ("i-fb", "#0866FF", "Meta"), "youtube": ("i-yt", "#FF0000", "YouTube"),
           "youtube-shorts": ("i-yt", "#FF0000", "YouTube Shorts"),
           "tiktok": ("i-tt", "#FF3B5C", "TikTok"), "linkedin": ("i-li", "#0A66C2", "LinkedIn"),
           "google": ("i-goo", "#4285F4", "Google")}


def _eff_net(v):
    """Efektivní síť pro badge/filtr: YouTube ve short bucketu = 'youtube-shorts' (oddělené od dlouhého YouTube)."""
    net = str(v.get("sit") or v.get("net") or "").lower()
    return "youtube-shorts" if (net == "youtube" and _fmt(v) == "short") else net
C_EYE, C_CLK, C_VAR = "hsl(203 100% 66%)", "hsl(38 92% 64%)", "hsl(221 92% 72%)"
C_HRT, C_CMT = "hsl(350 86% 68%)", "hsl(168 75% 58%)"

# Fáze povědomí česky (SMB nepochopí „solution-aware"). Angle OS žebřík → lidsky.
AW_CZ = {"unaware": "netuší problém", "problem-aware": "cítí problém",
         "solution-aware": "hledá řešení", "product-aware": "zvažuje produkt",
         "most-aware": "připraven koupit", "intent capture": "aktivně hledá",
         "vrsek": "vršek trychtýře", "stred": "střed trychtýře", "spodek": "spodek trychtýře"}

# 3 pásma trychtýře pro mapu útoku — hlavička sloupce: pozice + lidský popisek
FUNNEL_META = {"vrsek": ("Vršek trychtýře", "ještě neví — necítí problém, nehledá"),
               "stred": ("Střed trychtýře", "hledá řešení — porovnává možnosti"),
               "spodek": ("Spodek trychtýře", "vybírá a je připraven koupit")}


def aw_cz(aw):
    return AW_CZ.get(str(aw or "").strip().lower(), aw)


def _sites(v):
    return [str(x).lower() for x in (v if isinstance(v, list) else [v])]


def _meta_merge(sites):
    """FB + Instagram → jeden „meta". Ostatní kanály beze změny (dedup, pořadí zachováno)."""
    out = []
    for s in sites:
        s = "meta" if s in ("facebook", "instagram") else s
        if s not in out:
            out.append(s)
    return out


def _dur_sec(dur):
    if not dur:
        return None
    try:
        parts = [int(p) for p in str(dur).split(":")]
    except Exception:
        return None
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec


def _fmt(v):
    """Krátký vs dlouhý obsah. Explicitní `format`, jinak z sítě + délky.
    Short = hooky/formáty (reels, shorts, TikTok). Long = úhly/argumenty (YouTube dlouhé, podcast, LinkedIn)."""
    f = v.get("format")
    if f in ("short", "long"):
        return f
    net = str(v.get("sit") or v.get("net") or "").lower()
    if net in ("tiktok", "instagram"):
        return "short"
    if net == "linkedin":
        return "long"
    sec = _dur_sec(v.get("dur"))
    if sec is None:
        return "long" if net == "youtube" else "short"
    return "short" if sec <= 180 else "long"


def _badges(sites):
    return "".join(f'<span class="pb" style="background:{NETMETA[s][1]}"><svg fill="#fff"><use href="#{NETMETA[s][0]}"/></svg>{NETMETA[s][2]}</span>'
                   for s in sites if s in NETMETA)


def _why(lst):
    return "<ul class=\"why\">" + "".join(f"<li>{e(w)}</li>" for w in (lst or [])) + "</ul>" if lst else ""


def _plural_variant(n):
    n = int(n or 0)
    if n == 1:
        return "1 varianta"
    if 2 <= n <= 4:
        return f"{n} varianty"
    return f"{n} variant"


def _plural_inzerent(n):
    n = int(n or 0)
    if n == 1:
        return "inzerent"
    if 2 <= n <= 4:
        return "inzerenti"
    return "inzerentů"


def _src(t):
    return ("file://" + t) if str(t).startswith("/") else t


def _thumb(t, sym):
    if t:
        return f'<img class="real" src="{e(_src(t))}" alt=""><span class="shade"></span>'
    return f'<div class="noimg"><svg width="56" height="56" fill="currentColor"><use href="#{sym}"/></svg></div>'


def _ad_media(r, sym):
    """Jasně video vs obrázek. Náhled + štítek; u videa play-overlay. Přehrávání řeší
    popup (lightbox) v 9:16 — klik obsluhuje `_ad_card` (openVid), ať vertikální video
    nesedí zdeformované do 4:5 karty."""
    media = str(r.get("media") or "").lower()
    is_video = media == "video" or bool(r.get("video_url"))
    ic, lab = ("i-play", "Video") if is_video else ("i-img", "Obrázek")
    badge = f'<span class="mbadge{" vid" if is_video else ""}"><svg fill="currentColor"><use href="#{ic}"/></svg>{lab}</span>'
    inner = _thumb(r.get("thumb"), sym)
    if is_video:
        inner += '<span class="playov"><svg viewBox="0 0 24 24"><use href="#i-play"/></svg></span>'
    return inner + badge


def _ad_card(r):
    sites = _meta_merge(_sites(r.get("site")))
    prim = sites[0] if sites else "meta"
    chips = f'<span class="skill">úhel: {e(r.get("uhel"))}</span>' + (f'<span class="skill aw">{e(aw_cz(r["aw"]))}</span>' if r.get("aw") else "")
    m = (f'<span style="color:{C_EYE}"><svg fill="currentColor"><use href="#i-eye"/></svg>{fmt_reach(r.get("dosah_eu"))} EU</span>'
         f'<span style="color:{C_CLK}"><svg fill="currentColor"><use href="#i-clk"/></svg>{e(r.get("dni"))} dní</span>')
    if (r.get("varianty") or 0) > 1:
        m += f'<span style="color:{C_VAR}">⧉ {_plural_variant(r["varianty"])}</span>'
    orig = f'<div class="orig">„{e(r["orig"])}“</div>' if r.get("orig") else ""
    vurl, url, th = r.get("video_url"), r.get("url"), r.get("thumb")
    if vurl:  # video → přehrání v popupu
        click = f" onclick=\"openVid('{e(vurl)}')\" style=\"cursor:pointer\""
    elif th:  # obrázek → zvětšení v popupu (konzistentní s videem)
        click = f" onclick=\"openImg('{e(_src(th))}')\" style=\"cursor:pointer\""
    elif url:  # bez média → odkaz do knihovny reklam
        click = f" onclick=\"window.open('{e(url)}','_blank')\" style=\"cursor:pointer\""
    else:
        click = ""
    return (f'<div class="ocard" data-net="{" ".join(sites)}">'
            f'<div class="thumb"{click}>{_ad_media(r, NETMETA[prim][0])}'
            f'<span class="score {tier(r.get("score"))}"><svg width="11" height="11" fill="currentColor"><use href="#i-fire"/></svg><b>{e(r.get("score"))}</b></span>'
            f'<span class="rank">#{e(r.get("poradi"))}</span>'
            + ('<span class="geo">GLOBÁL</span>' if r.get("geo") == "global" else "")
            + f'<span class="dur">{e(r.get("dni"))} dní</span></div>'
            f'<div class="body"><div class="nm">{e(r.get("nm"))}</div>{orig}'
            f'<div class="pbs">{_badges(sites)}<span class="who">{e(r.get("inzerent"))}</span></div>'
            f'<div class="mline">{m}</div><div class="chiprow">{chips}</div>{_why(r.get("why"))}'
            f'<div class="acts"><a class="alink" href="{e(r.get("url"))}" target="_blank" rel="noopener">Zobrazit reklamu ↗</a></div></div></div>')


def _viral_card(v):
    net = _eff_net(v) or "youtube"  # YouTube Shorts oddělené od dlouhého YouTube (badge + filtr)
    ic, col, lab = NETMETA.get(net, ("i-yt", "#FF0000", net.title()))
    free = " free" if "VOLNÝ" in (v.get("uhel") or "") else ""
    m = (f'<span style="color:{C_EYE}"><svg fill="currentColor"><use href="#i-eye"/></svg>{fnum(v.get("zhlednuti"))}</span>'
         f'<span style="color:{C_HRT}"><svg fill="currentColor"><use href="#i-heart"/></svg>{fnum(v.get("likes"))}</span>')
    if v.get("cmts"):
        m += f'<span style="color:{C_CMT}"><svg fill="currentColor"><use href="#i-cmt"/></svg>{fnum(v["cmts"])}</span>'
    geo = '<span class="geo">GLOBÁL</span>' if v.get("geo") == "global" else ""
    dur = f'<span class="dur">{e(v["dur"])}</span>' if v.get("dur") else ""
    labels = {"youtube": "Přehrát na YouTube", "youtube-shorts": "Přehrát na YouTube", "tiktok": "Otevřít na TikToku",
              "instagram": "Otevřít na Instagramu", "facebook": "Otevřít na Facebooku"}
    label = labels.get(net, "Otevřít obsah")
    is_video = bool(v.get("dur")) or net in ("tiktok", "youtube", "youtube-shorts")  # IG/FB posty (bez dur) = obrázek, bez play
    playov = '<span class="playov"><svg viewBox="0 0 24 24"><use href="#i-play"/></svg></span>' if is_video else ""
    orig = f'<div class="orig">„{e(v["orig"])}“</div>' if v.get("orig") else ""  # anglický originál pod českým titulkem
    return (f'<a class="ocard" data-net="{e(net)}" data-geo="{e(v.get("geo", "cz"))}" href="{e(v.get("url"))}" target="_blank" rel="noopener">'
            f'<div class="thumb">{_thumb(v.get("thumb"), ic)}{playov}'
            f'<span class="score {tier(v.get("score"))}"><svg width="11" height="11" fill="currentColor"><use href="#i-fire"/></svg><b>{e(v.get("score"))}</b></span>'
            f'<span class="rank">#{e(v.get("poradi"))}</span>{geo}{dur}</div>'
            f'<div class="body"><div class="nm">{e(v.get("nm"))}</div>{orig}'
            f'<div class="pbs"><span class="pb" style="background:{col}"><svg fill="#fff"><use href="#{ic}"/></svg>{lab}</span><span class="who">{e(v.get("kdo"))}</span></div>'
            f'<div class="mline">{m}</div><div class="chiprow"><span class="skill{free}">úhel: {e(v.get("uhel"))}</span></div>{_why(v.get("why"))}'
            f'<div class="acts"><span class="alink">{label} ↗</span></div></div></a>')


def _net_counts(items):
    c = {}
    for v in items:
        n = _eff_net(v)  # YouTube Shorts počítáme odděleně od dlouhého YouTube
        if n:
            c[n] = c.get(n, 0) + 1
    return c


def _netbar(gid, counts, order):
    b = [f'<span class="nf on" onclick="net(event,\'{gid}\',\'all\')">Všechny sítě</span>']
    for n in order:
        if counts.get(n):
            ic, col, lab = NETMETA[n]
            b.append(f'<span class="nf" onclick="net(event,\'{gid}\',\'{n}\')"><svg fill="{col}"><use href="#{ic}"/></svg>{lab} · {counts[n]}</span>')
    return "".join(b)


def _stat(lbl, val, delta, acc, ic):
    accf = acc if acc.startswith("var(") else f"hsl({acc})"
    accbg = "hsl(var(--brand)/.12)" if acc.startswith("var(") else f"hsl({acc}/.12)"
    return (f'<div class="stat" style="--accent:{accf};--accent-bg:{accbg}"><div class="top"><span class="lbl">{e(lbl)}</span>'
            f'<span class="ic"><svg fill="currentColor"><use href="#{ic}"/></svg></span></div>'
            f'<div class="val">{e(val)}</div><div class="delta">{delta}</div></div>')


def _sectionhead(no, h2, lead):
    return (f'<div class="sectionhead"><div class="shrow"><span class="secno">{e(no)}</span>'
            f'<h2>{e(h2)}</h2></div><p>{lead}</p></div>')


def _grid(gid, cards, n, extra=""):
    """Mřížka karet: prvních COLLAPSE_AT vidět hned, zbytek schovaný za tlačítkem
    „Načíst dalších N" (JS odkryje, bez re-fetche — data už jsou v HTML)."""
    html_out = f'<div class="grid collapsed{extra}" id="{gid}">{cards}</div>'
    if n > COLLAPSE_AT:
        html_out += (f'<button class="loadmore" data-grid="{gid}" onclick="more(this)">'
                     f'Načíst dalších {n - COLLAPSE_AT} ↓</button>')
    return html_out


def render(rep, out_path):
    m = rep.get("meta", {})
    pok = rep.get("pokryti", {})
    tema = m.get("tema", "")
    trh = (m.get("trh") or "cz").upper()

    ads = (rep.get("reklamy") or [])[:AD_SHOW]
    viral = rep.get("viralni") or []
    short = [v for v in viral if _fmt(v) == "short"][:SHORT_SHOW]
    longf = [v for v in viral if _fmt(v) == "long"][:LONG_SHOW]

    podtitulek = m.get("podtitulek") or (
        f'Vítězné reklamy konkurence a nejsledovanější organický obsah na téma „{tema}" — '
        'hotové vzorce (hook, úhel, formát), které převezmete do vlastních kampaní.')

    p = ['<!doctype html><html lang="cs"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>Viral Ad Board — „{e(tema)}"</title>'
         '<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800'
         '&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">'
         f'<style>{DEMO_CSS}{DNA_CSS}</style></head><body>{SVG_DEFS}<div class="wrap">']

    # hlavička
    p.append(
        f'<div class="phead"><div>'
        f'<h1>Viral Ad Board <span class="theme">— „{e(tema)}"</span></h1>'
        f'<div class="meta"><span class="mchip">ad-scout</span><span>trh {e(trh)}</span> · '
        f'<span class="mono">{e(m.get("sken"))}</span> · <span>z veřejně dostupných reklamních a organických dat</span></div>'
        f'<p class="subtitle">{e(podtitulek)}</p></div>'
        f'<div class="right"><span class="pill ok">REÁLNÁ DATA</span></div></div>')

    # přehled — ODVOZENÉ signály (ne fetch cap): nasycení · nejvirálnější · ověřené · díra
    all_ads = rep.get("reklamy") or []
    all_viral = rep.get("viralni") or []
    volno = len((rep.get("mapa_uhlu") or {}).get("volno", []))
    inzerentu = pok.get("inzerentu") or len({r.get("inzerent") for r in all_ads})
    max_days = max((r.get("dni") or 0 for r in all_ads), default=0)
    max_views = max((v.get("zhlednuti") or 0 for v in all_viral), default=0)
    p.append('<div class="stats">'
             + _stat("Inzerentů na téma", inzerentu, "značek jede reklamy — nasycení trhu", "var(--brand)", "i-lay")
             + _stat("Nejvirálnější", fmt_reach(max_views), "zhlédnutí — nejsledovanější kus", "350 86% 65%", "i-fire")
             + _stat("Nejdéle běžící", max_days, "dní běhu — ověřený vítěz", "168 72% 48%", "i-clk")
             + _stat("Volné úhly", volno, "kde má konkurence mezeru = vaše příležitost", "205 100% 62%", "i-tgt")
             + '</div>')

    # Číslované sekce — číslo se inkrementuje jen pro sekce, co reálně vzniknou (01 od mapy úhlů)
    _n = [0]

    def secno():
        _n[0] += 1
        return f"{_n[0]:02d}"

    # 01) MAPA ÚHLŮ
    am = _angle_map(rep)
    if am:
        p.append(_sectionhead(secno(), "Mapa úhlů",
                              "Které úhly už konkurence přeplnila (🔴 plno) a kde máte volný prostor se odlišit (🟢 volno)."))
        p.append(am)

    # 02) PROČ SE TÍM INSPIROVAT
    syn = _synthesis(rep)
    if syn:
        p.append(_sectionhead(secno(), "Klíčové poznatky",
                              "Shrnutí signálů z reklam a organiky + knihovna nejsilnějších úvodních hooků, které převezmete do vlastní kampaně."))
        p.append(syn)

    # 02b) VIRAL DNA kondenzát (úroveň A) — TOP 1 z každého světa; sekce jen když ji model vyplnil
    dk = _dna_top3(rep)
    if dk:
        p.append(_sectionhead(secno(), "Viral DNA — nejlepší kus z každého světa",
                              "Tři nejsilnější donoři rozklíčovaní na přenositelnou DNA: hook · úhel · proč vyhrál · jak se inspirovat. To hlavní rovnou tady, bez klikání."))
        p.append(dk)

    # 03) PLACENÉ REKLAMY (sekci vynech, když žádné reklamy — např. spamem zaplavená knihovna)
    if ads:
        adc = {}
        for r in ads:
            for s in _meta_merge(_sites(r.get("site"))):
                adc[s] = adc.get(s, 0) + 1
        p.append(_sectionhead(secno(),
                              "Placené reklamy konkurence",
                              "Co konkurence platí za pozornost. Klonovatelná kreativa — hodnocení = dosah v EU × délka běhu × počet variant."))
        p.append(f'<div class="netbar" id="netbar-ad">{_netbar("ad", adc, ["meta", "tiktok", "youtube"])}</div>')
        p.append(_grid("grid-ad", "".join(_ad_card(r) for r in ads), len(ads)))

    # 04) ORGANICKÝ OBSAH — krátká / dlouhá
    p.append(_sectionhead(secno(),
                          "Co lidé sami sledují a sdílejí",
                          "Organika bez rozpočtu — nejsilnější signál, co publikum opravdu baví. Hodnocení = zhlédnutí × zapojení."))
    if short:
        p.append('<div class="subhead">Krátký obsah <span class="tag">hooky · formáty</span>'
                 f'<span class="cnt">{len(short)} kusů · TikTok, YouTube Shorts, reels</span></div>')
        p.append(f'<div class="netbar" id="netbar-short">{_netbar("short", _net_counts(short), ["tiktok", "youtube-shorts", "instagram", "facebook"])}</div>')
        p.append(_grid("grid-short", "".join(_viral_card(v) for v in short), len(short)))
    if longf:
        p.append('<div class="subhead">Dlouhý obsah <span class="tag">úhly · argumenty</span>'
                 f'<span class="cnt">{len(longf)} kusů · YouTube, podcasty, LinkedIn</span></div>')
        p.append(f'<div class="netbar" id="netbar-long">{_netbar("long", _net_counts(longf), ["youtube", "linkedin", "tiktok", "instagram"])}</div>')
        p.append(_grid("grid-long", "".join(_viral_card(v) for v in longf), len(longf), " gwide"))

    # 05) ÚHLY VE VYHLEDÁVÁNÍ
    sa = _search_angles(rep)
    if sa:
        p.append(_sectionhead(secno(),
                              "Jaké úhly konkurence komunikuje ve vyhledávání",
                              "Ne kdo víc utrácí — ale jakými sliby konkurence oslovuje lidi, kteří produkt aktivně hledají. Další zdroj úhlů do vaší reklamy."))
        p.append(sa)

    # 06) JAZYK ZÁKAZNÍKA
    diet = _diet(rep)
    if diet:
        p.append(_sectionhead(secno(),
                              "Jak o tématu mluví sami potenciální zákazníci",
                              "Doslovné výrazy z komentářů pod nejsledovanějším obsahem — jejich námitky, touhy, frustrace, otázky i emoční triggery. Piště reklamu přesně jejich jazykem, ne svým."))
        p.append(diet)

    p.append(f'<div class="pagefoot">CliqSales · Ad Scout · Viral Ad Board · spuštěno klíčovým slovem / tématem · '
             f'reálná data z veřejně dostupných zdrojů · {e(pok.get("reklamy_relevantni", len(rep.get("reklamy") or [])))} reklam + '
             f'{e(len(viral))} organických kusů · {e(m.get("sken"))}</div>')
    p.append('</div>'
             '<div id="vpop" class="vpop" onclick="closeVid(event)"><div class="vpop-inner" onclick="event.stopPropagation()">'
             '<button class="vpop-x" onclick="closeVid(event)" aria-label="Zavřít">✕</button>'
             '<video id="vpopv" controls playsinline></video>'
             '<img id="vpopi" alt="" style="display:none;max-height:84vh;max-width:90vw;width:auto;height:auto;object-fit:contain;border-radius:12px">'
             '</div></div>'
             '<script>'
             'function net(e,g,n){document.querySelectorAll("#netbar-"+g+" .nf").forEach(function(b){b.classList.remove("on")});e.currentTarget.classList.add("on");'
             'document.querySelectorAll("#grid-"+g+" .ocard").forEach(function(c){var m=(n=="all"||((" "+c.dataset.net+" ").indexOf(" "+n+" ")>=0));c.classList.toggle("nf-hide",!m)})}'
             'function more(b){var g=document.getElementById(b.dataset.grid);g.classList.remove("collapsed");b.remove()}'
             'function openVid(u){var m=document.getElementById("vpop"),v=document.getElementById("vpopv"),i=document.getElementById("vpopi");i.style.display="none";v.style.display="";v.parentNode.classList.remove("img");v.src=u;m.classList.add("on");v.play().catch(function(){})}'
             'function openImg(u){var m=document.getElementById("vpop"),v=document.getElementById("vpopv"),i=document.getElementById("vpopi");v.pause&&v.pause();v.style.display="none";i.parentNode.classList.add("img");i.src=u;i.style.display="";m.classList.add("on")}'
             'function closeVid(e){var m=document.getElementById("vpop"),v=document.getElementById("vpopv"),i=document.getElementById("vpopi");v.pause();v.removeAttribute("src");v.load();i.removeAttribute("src");m.classList.remove("on")}'
             'document.addEventListener("keydown",function(e){if(e.key==="Escape")closeVid()});'
             '</script></body></html>')

    with open(out_path, "w") as f:
        f.write("".join(x for x in p if x))
    return out_path


def _angle_map(rep):
    mp = rep.get("mapa_uhlu") or {}
    if not (mp.get("plno") or mp.get("sporne") or mp.get("volno")):
        return ""
    chips = ""
    for u in mp.get("plno", []):
        chips += f'<span class="gap red">{e(u.get("uhel") if isinstance(u, dict) else u)} <span class="n">{e(u.get("pocet") if isinstance(u, dict) else "9+")}</span></span>'
    for u in mp.get("sporne", []):
        chips += f'<span class="gap yel">{e(u.get("uhel") if isinstance(u, dict) else u)} <span class="n">{e(u.get("pocet") if isinstance(u, dict) else "")}</span></span>'
    for u in mp.get("volno", []):
        chips += f'<span class="gap grn">{e(u.get("uhel") if isinstance(u, dict) else u)} <span class="n">VOLNÝ</span></span>'
    return f'<div class="gapbar" style="padding:2px 0 0">{chips}</div>'


def _synthesis(rep):
    syn = rep.get("synteza") or []
    hooky = rep.get("hooky") or []
    if not (syn or hooky):
        return ""
    rows = ""
    for s in syn:
        col = s.get("color", "hsl(203 100% 62%)")
        rows += (f'<div class="row"><span class="ic" style="background:{col.replace(")", "/.12)")};color:{col}">'
                 f'<svg fill="currentColor"><use href="#{e(s.get("icon", "i-eye"))}"/></svg></span><div>{s.get("html", "")}</div></div>')
    left = ('<div class="card synth"><div class="chead"><h3>Co si z toho vzít</h3>'
            f'<span class="sub">DOPORUČENÍ</span></div><div class="bd">{rows}</div>'
            '<div class="foot"><span class="note">Kombinace dvou signálů: placené reklamy (za co trh platí) × organika (co publikum skutečně sleduje a sdílí)</span></div></div>')
    hk = ""
    for i, h in enumerate(hooky, 1):
        col = h.get("color", "hsl(203 100% 60%)")
        orig = f'<div class="horig">„{e(h["orig"])}“</div>' if h.get("orig") else ""
        hk += (f'<div class="hk"><span class="no" style="color:{col};background:{col.replace(")", "/.12)")};border-color:{col.replace(")", "/.35)")}">{i}</span><div class="b">'
               f'<div class="t">„{e(h.get("cz"))}“</div>{orig}'
               f'<span class="pat" style="color:{col};background:{col.replace(")", "/.1)")};border-color:{col.replace(")", "/.3)")}">vzorec: {e(h.get("vzorec"))}</span>'
               f'<div class="why2">{e(h.get("why"))}</div><div class="srcline"><b>{e(h.get("kdo"))}</b> · {e(h.get("val"))}</div></div></div>')
    right = f'<div class="card"><div class="chead"><h3>Knihovna hooků — co zastavuje palec</h3><span class="sub">ÚVODNÍ HOOKY</span></div><div class="hookgrid">{hk}</div></div>'
    return f'<div class="duo">{left}{right}</div>'


def _dna_top3(rep):
    """Viral DNA kondenzát (úroveň A): 3 mini-karty — nejlepší Reklama · Organika · Longform.
    Vykreslí jen kbelíky, které MODEL vyplnil (hook/proc); prázdný kondenzát = žádná sekce
    (staré kontrakty bez `dna_kondenzat` fungují beze změny)."""
    dk = rep.get("dna_kondenzat") or {}
    meta = [("reklama", "NEJLEPŠÍ REKLAMA", "hsl(205 100% 62%)"),
            ("organika", "NEJLEPŠÍ KRÁTKÝ VIRÁL", "hsl(350 86% 68%)"),
            ("longform", "NEJLEPŠÍ DLOUHÝ OBSAH", "hsl(178 70% 62%)")]
    cards = ""
    for key, tag, col in meta:
        b = dk.get(key)
        if not b or not (b.get("proc") or b.get("hook")):
            continue
        th = f'<img src="{e(_src(b["thumb"]))}" alt="">' if b.get("thumb") else ""
        rows = ""
        if b.get("hook"):
            rows += f'<div class="drow"><b>Hook:</b> „{e(b["hook"])}“</div>'
        if b.get("uhel"):
            rows += f'<div class="drow"><b>Úhel:</b> {e(b["uhel"])}</div>'
        if b.get("proc"):
            rows += f'<div class="drow"><b>Proč vyhrál:</b> {e(b["proc"])}</div>'
        if b.get("inspirace"):
            rows += f'<div class="drow"><b>Jak se inspirovat:</b> {e(b["inspirace"])}</div>'
        who = " · ".join(str(x) for x in (b.get("kdo"), b.get("val")) if x)
        if b.get("dna_url"):
            link = (f'<div class="dlink"><a class="alink" href="{e(_src(b["dna_url"]))}" '
                    'target="_blank" rel="noopener">🧬 Celý rozbor DNA →</a></div>')
        elif b.get("url"):
            link = (f'<div class="dlink"><a class="alink" href="{e(b["url"])}" '
                    'target="_blank" rel="noopener">Zobrazit originál ↗</a></div>')
        else:
            link = ""
        cards += (f'<div class="dnacard"><div class="dthumb">{th}'
                  f'<span class="dtag" style="color:{col}">{tag}</span></div>'
                  f'<div class="dbody"><div class="dnm">{e(b.get("nm"))}</div>'
                  f'<div class="dwho">{e(who)}</div>{rows}{link}</div></div>')
    return f'<div class="dnagrid">{cards}</div>' if cards else ""


def _search_angles(rep):
    """Úhly ve vyhledávání (NE share of voice). Bohatší blok per úhel: počet inzerentů,
    insight, příklady headline + kdo. Z `search_uhly` nebo odvozeno ze `search`."""
    items = rep.get("search_uhly")
    if not items:
        groups = {}
        for g in rep.get("search") or []:
            u = g.get("uhel") or "obecný úhel"
            grp = groups.setdefault(u, {"uhel": u, "priklady": [], "brands": set()})
            if g.get("head"):
                grp["priklady"].append({"head": g.get("head"), "kdo": g.get("brand")})
            if g.get("brand"):
                grp["brands"].add(g.get("brand"))
        items = [{"uhel": v["uhel"], "pocet": len(v["brands"]), "priklady": v["priklady"]}
                 for v in groups.values()]
    if not items:
        return ""
    blocks = ""
    for it in items:
        pocet = it.get("pocet")
        cnt = f'<span class="cnt">{e(pocet)} {_plural_inzerent(pocet)}</span>' if pocet else ""
        ins = f'<span class="ins">{e(it.get("insight"))}</span>' if it.get("insight") else ""
        ex = ""
        for pr in (it.get("priklady") or [])[:4]:
            b = f'<span class="b">{e(pr.get("kdo"))}</span>' if pr.get("kdo") else ""
            ex += f'<div class="uexr"><span class="q">{e(pr.get("head"))}</span>{b}</div>'
        blocks += (f'<div class="ublock"><div class="ubhead"><span class="u">{e(it.get("uhel"))}</span>'
                   f'{cnt}{ins}</div><div class="uex">{ex}</div></div>')
    return (f'<div class="card"><div class="chead"><h3>Komunikační úhly, které konkurence kupuje ve vyhledávání</h3>'
            f'<span class="sub">ÚHLY, NE POŘADÍ</span></div>{blocks}</div>')


def _diet(rep):
    """Jazyk zákazníka (Raw Diet) — vizuální: doslovné fráze (pilulky) + emoční triggery (tagy)
    + 4 barevné panely: Námitky · Touhy · Frustrace ze současných řešení · Otázky, které si kladou."""
    jz = rep.get("jazyk_zakaznika") or {}
    nam = jz.get("namitky") or []
    tou = jz.get("touhy") or []
    fra = jz.get("fraze") or []
    fru = jz.get("frustrace") or []
    otz = jz.get("otazky") or []
    trg = jz.get("triggery") or []
    if not (nam or tou or fra or fru or otz or trg):
        return ""
    zc = jz.get("zdroj_pocet") or {}
    total = int(sum(v for v in zc.values() if isinstance(v, (int, float))))
    note = f"z {fnum(total)} komentářů · bez jmen (GDPR)" if total else "z komentářů pod TOP obsahem · bez jmen (GDPR)"

    fraze_html = ""
    if fra:
        pills = "".join(f'<span class="fpill">{e(x)}</span>' for x in fra)
        fraze_html = f'<div class="fraze"><span class="fl">Doslovné výrazy, které používají</span>{pills}</div>'
    trig_html = ""
    if trg:
        tags = "".join(f'<span class="ttag">{e(x)}</span>' for x in trg)
        trig_html = f'<div class="trig"><span class="fl">Emoční triggery</span>{tags}</div>'

    def panel(cls, icon, icbg, iccol, title, items, dot):
        items = items[:5]
        lis = ""
        for it in items:
            if isinstance(it, dict):
                q = it.get("q") or it.get("vyraz") or it.get("citace") or ""
                ex = it.get("e") or it.get("vyznam") or it.get("vysvetleni") or ""
            else:
                q, ex = it, ""
            # citace zákazníka = v uvozovkách + kurzívou (patrné, že je to reálné tvrzení návštěvníka)
            body = f'<span class="q">„{e(q)}“</span>' + (f'<span class="expl">{e(ex)}</span>' if ex else "")
            lis += f'<li style="--dot:{dot}">{body}</li>'
        return (f'<div class="dcol {cls}"><h4><span class="ic" style="background:{icbg};color:{iccol}">'
                f'<svg fill="currentColor"><use href="#{icon}"/></svg></span>{title}'
                f'<span class="cnt">{len(items)}×</span></h4><ul>{lis}</ul></div>')
    row1 = ""
    if nam or tou:
        nam_p = panel("nam", "i-bolt", "hsl(350 86% 62% / .14)", "hsl(350 86% 68%)", "Námitky a obavy", nam, "hsl(350 86% 62%)")
        tou_p = panel("tou", "i-heart", "hsl(168 72% 50% / .14)", "hsl(168 72% 58%)", "Touhy a přání", tou, "hsl(168 72% 50%)")
        row1 = f'<div class="dietrow">{nam_p}{tou_p}</div>'
    row2 = ""
    if fru or otz:
        fru_p = panel("nam", "i-fire", "hsl(37 92% 54% / .14)", "hsl(37 92% 62%)", "Frustrace se současnými řešeními", fru, "hsl(37 92% 54%)")
        otz_p = panel("tou", "i-cmt", "hsl(203 100% 60% / .14)", "hsl(203 100% 66%)", "Otázky, které si kladou", otz, "hsl(203 100% 60%)")
        row2 = f'<div class="dietrow">{fru_p}{otz_p}</div>'
    return (f'<div class="card"><div class="chead"><h3>Jazyk zákazníka — jejich slova, ne vaše</h3>'
            f'<span class="sub">{e(note)}</span></div>{fraze_html}{trig_html}{row1}{row2}</div>')


# ============================================================================
# COMPETITOR AD BOARD (kind=competitor) — osa = ZNAČKA (vstup = doména konkurenta)
# MVP: stat row + 01 Jejich vítězové (donor banka) + 02 Mapa úhlů (kde zaútočit)
#      + 03 Útočný plán — 3 tahy (handoff na AI Marketéra).
# Stejný design language (CSS/SVG z _adboard_assets), kontrakt z compboard_build.py.
# ============================================================================

COMP_CSS = r"""
.typb{font-family:var(--font-mono);font-size:8.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;border-radius:6px;padding:3px 8px;border:1px solid}
.typb.vyk{color:hsl(152 70% 60%);background:hsl(var(--success)/.12);border-color:hsl(var(--success)/.35)}
.typb.img{color:hsl(38 92% 66%);background:hsl(var(--warning)/.12);border-color:hsl(var(--warning)/.35)}
.typb.nab{color:hsl(var(--fg-dim));background:hsl(var(--surface-2));border-color:hsl(var(--border))}
.klon{font-size:11.5px;line-height:1.5;color:hsl(var(--mint));background:hsl(178 85% 60%/.07);border:1px dashed hsl(178 85% 60%/.3);border-radius:8px;padding:8px 10px}
.klon b{color:hsl(var(--fg));font-weight:600}
.chips-kanaly{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:-6px 0 22px}
.kchip{display:inline-flex;align-items:center;gap:7px;font-size:12px;font-weight:600;padding:7px 13px;border-radius:999px;border:1px solid hsl(var(--border));background:hsl(var(--surface-1));color:hsl(var(--fg-muted))}
.kchip svg{width:14px;height:14px}
.kchip a{display:inline-flex;align-items:center;gap:7px;color:hsl(var(--brand-light));text-decoration:none}
.matrix{width:100%;border-collapse:separate;border-spacing:6px;table-layout:fixed}
.matrix th{font-family:var(--font-mono);font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:hsl(var(--fg-muted));padding:6px 8px;text-align:center}
.matrix th.rowh{text-align:left;width:220px}
.matrix td{border-radius:9px;text-align:center;padding:13px 6px;font-family:var(--font-mono);font-size:13px;font-weight:700}
.matrix td .st{display:block;font-size:8.5px;letter-spacing:.08em;font-weight:700;margin-top:3px;text-transform:uppercase;opacity:.85}
.matrix td.full{background:linear-gradient(135deg,hsl(var(--coral)/.2),hsl(var(--coral)/.07));color:hsl(350 90% 76%);border:1px solid hsl(var(--coral)/.3)}
.matrix td.weak{background:linear-gradient(135deg,hsl(var(--warning)/.17),hsl(var(--warning)/.05));color:hsl(38 92% 66%);border:1px solid hsl(var(--warning)/.3)}
.matrix td.open{background:linear-gradient(135deg,hsl(var(--success)/.18),hsl(var(--success)/.05));color:hsl(152 70% 62%);border:1px solid hsl(var(--success)/.35)}
.matrix td.na{background:hsl(var(--surface-2)/.25);color:hsl(var(--fg-dim)/.6);border:1px solid hsl(var(--border)/.25);font-weight:400}
.matrix th .fdesc{display:block;font-size:9px;font-weight:400;letter-spacing:.02em;text-transform:none;color:hsl(var(--fg-dim));margin-top:3px}
.matrix td.rowl{background:none;border:none;text-align:left;font-family:var(--font-sans);font-size:13.5px;font-weight:600;color:hsl(var(--fg));padding:6px 8px}
.oppo{display:grid;grid-template-columns:1fr 1fr;gap:20px;padding:24px 26px 28px;border-top:1px solid hsl(var(--border)/.5)}
.oppo .op{border:1px solid hsl(var(--border)/.85);border-radius:14px;background:linear-gradient(180deg,hsl(var(--surface-1)),hsl(var(--bg)/.4));padding:22px 24px;font-size:13px;line-height:1.65;display:flex;flex-direction:column}
.oppo .op .ohead{display:flex;align-items:center;gap:12px;margin-bottom:13px}
.oppo .op .tag{flex:none;font-family:var(--font-mono);font-size:9.5px;font-weight:700;color:hsl(152 70% 60%);background:hsl(var(--success)/.13);border:1px solid hsl(var(--success)/.35);border-radius:6px;padding:4px 10px;letter-spacing:.05em}
.oppo .op b{color:hsl(var(--fg));font-size:14px}
.oppo .op .proc{color:hsl(var(--fg-muted));flex:1}
.oppo .op .pk{margin-top:14px;padding-top:14px;border-top:1px dashed hsl(var(--border)/.6);color:hsl(var(--mint,178 85% 78%))}
.oppo .op .pk b{color:hsl(178 85% 78%);font-size:12px;text-transform:uppercase;letter-spacing:.05em}
@media(max-width:880px){.oppo{grid-template-columns:1fr}}
.plan{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
@media(max-width:1040px){.plan{grid-template-columns:1fr}}
.pcard{position:relative;border-radius:var(--radius);padding:24px 24px 20px;background:linear-gradient(180deg,hsl(var(--surface-1)),hsl(var(--bg)/.4));border:1px solid hsl(var(--border)/.85);box-shadow:0 1px 0 rgba(255,255,255,.04) inset,0 18px 40px -26px rgba(0,0,0,.9);display:flex;flex-direction:column;gap:12px}
.pcard::after{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:linear-gradient(90deg,transparent,var(--pc,hsl(var(--brand))),transparent);opacity:.9}
.pcard .pno{font-family:var(--font-mono);font-size:34px;font-weight:700;color:var(--pc,hsl(var(--brand-light)));line-height:1}
.pcard .ptah{font-family:var(--font-mono);font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--pc,hsl(var(--brand-light)))}
.pcard h3{font-size:18px;font-weight:800;letter-spacing:-.01em;line-height:1.25}
.pcard p{font-size:13px;line-height:1.6;color:hsl(var(--fg-muted));flex:1}
.pcard .zdroj{font-family:var(--font-mono);font-size:10px;color:hsl(var(--fg-dim))}
.pcard .hbtn{display:flex;align-items:center;justify-content:center;gap:8px;padding:12px;border:none;border-radius:10px;background:linear-gradient(135deg,hsl(var(--brand)),hsl(178 85% 66%));color:#01071A;font-family:var(--font-sans);font-size:13.5px;font-weight:700;cursor:pointer;transition:.15s;box-shadow:0 6px 20px -8px hsl(var(--brand)/.7)}
.pcard .hbtn:hover{filter:brightness(1.08);transform:translateY(-1px)}
.pcard .hnote{font-size:10.5px;color:hsl(var(--fg-dim));text-align:center}
.hoff{position:absolute;left:-9999px;top:0;height:1px;width:1px;opacity:0}
.ggrid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.gcard{border:1px solid hsl(var(--border)/.85);border-radius:12px;background:linear-gradient(180deg,hsl(var(--surface-1)),hsl(var(--bg)/.4));overflow:hidden}
.gth{height:170px;background:hsl(var(--surface-2)/.6);display:grid;place-items:center;cursor:zoom-in;padding:10px;overflow:hidden}
.gth img{max-width:100%;max-height:150px;object-fit:contain;display:block;border-radius:6px}
.gth-empty{color:hsl(var(--fg-dim));font-size:11.5px;cursor:default}
.gmeta{display:flex;align-items:center;gap:9px;padding:10px 13px 6px}
.gmeta .fmt{font-family:var(--font-mono);font-size:9px;font-weight:700;text-transform:uppercase;color:hsl(var(--fg-muted));background:hsl(var(--surface-2));border:1px solid hsl(var(--border));border-radius:5px;padding:2px 7px}
.gdni{margin-left:auto;font-family:var(--font-mono);font-size:10px;font-weight:700;color:hsl(38 92% 64%);background:hsl(38 92% 56%/.13);border:1px solid hsl(38 92% 56%/.4);border-radius:6px;padding:3px 9px;white-space:nowrap}
.gnm{padding:0 13px 12px;font-size:12.5px;line-height:1.45;color:hsl(var(--fg))}
.gexp{margin-top:16px;font-size:13px;line-height:1.55;color:hsl(var(--fg-muted));background:hsl(178 85% 60%/.06);border:1px dashed hsl(178 85% 60%/.3);border-radius:11px;padding:13px 16px}
.gexp b{color:hsl(var(--fg))}
@media(max-width:1040px){.ggrid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:520px){.ggrid{grid-template-columns:1fr}}
"""

_TYP_BADGE = {None: ("vyk", "Výkonová — klonovat"), "vykonova": ("vyk", "Výkonová — klonovat"),
              "image": ("img", "Image kampaň — neklonovat jako výkonovou"),
              "nabor": ("nab", "Nábor — neklonovat")}


def _comp_card(r):
    sites = _meta_merge(_sites(r.get("site")))
    prim = sites[0] if sites else "meta"
    tcls, tlab = _TYP_BADGE.get(r.get("typ"), _TYP_BADGE[None])
    chips = f'<span class="typb {tcls}">{e(tlab)}</span><span class="skill">úhel: {e(r.get("uhel"))}</span>' \
            + (f'<span class="skill aw">{e(aw_cz(r["aw"]))}</span>' if r.get("aw") else "")
    m = ""
    if r.get("dosah_eu"):
        m += f'<span style="color:{C_EYE}"><svg fill="currentColor"><use href="#i-eye"/></svg>{fmt_reach(r["dosah_eu"])} EU</span>'
    if r.get("dni") is not None:
        m += f'<span style="color:{C_CLK}"><svg fill="currentColor"><use href="#i-clk"/></svg>běží {e(r["dni"])} dní</span>'
    if (r.get("varianty") or 0) > 1:
        m += f'<span style="color:{C_VAR}">⧉ {_plural_variant(r["varianty"])}</span>'
    orig = f'<div class="orig">„{e(r["orig"])}“</div>' if r.get("orig") else ""
    klon = f'<div class="klon"><b>Naklonovat na váš produkt:</b> {e(r["klon"])}</div>' if r.get("klon") else ""
    vurl, url, th = r.get("video_url"), r.get("url"), r.get("thumb")
    if vurl:
        click = f" onclick=\"openVid('{e(vurl)}')\" style=\"cursor:pointer\""
    elif th:
        click = f" onclick=\"openImg('{e(_src(th))}')\" style=\"cursor:pointer\""
    elif url:
        click = f" onclick=\"window.open('{e(url)}','_blank')\" style=\"cursor:pointer\""
    else:
        click = ""
    dni_b = f'<span class="dur">{e(r["dni"])} dní</span>' if r.get("dni") is not None else ""
    return (f'<div class="ocard" data-net="{" ".join(sites)}">'
            f'<div class="thumb"{click}>{_ad_media(r, NETMETA.get(prim, NETMETA["meta"])[0])}'
            f'<span class="score {tier(r.get("score"))}"><svg width="11" height="11" fill="currentColor"><use href="#i-fire"/></svg><b>{e(r.get("score"))}</b></span>'
            f'<span class="rank">#{e(r.get("poradi"))}</span>{dni_b}</div>'
            f'<div class="body"><div class="nm">{e(r.get("nm"))}</div>{orig}'
            f'<div class="pbs">{_badges(sites)}</div>'
            f'<div class="mline">{m}</div><div class="chiprow">{chips}</div>{_why(r.get("why"))}{klon}'
            f'<div class="acts"><a class="alink" href="{e(r.get("url"))}" target="_blank" rel="noopener">Otevřít v knihovně reklam ↗</a></div></div></div>')


def _stav_cls(n):
    n = int(n or 0)
    return ("open", "volno") if n == 0 else (("weak", "slabší") if n <= 2 else ("full", "plno"))


def _attack_matrix(rep):
    mu = rep.get("mapa_utoku") or {}
    faze, radky = mu.get("faze") or [], mu.get("radky") or []
    if not (faze and radky):
        return ""
    def _fhead(f):
        if f in FUNNEL_META:
            t, d = FUNNEL_META[f]
            return f'<th>{e(t)}<span class="fdesc">{e(d)}</span></th>'
        return f"<th>{e(aw_cz(f))}</th>"
    head = '<tr><th class="rowh">Úhel</th>' + "".join(_fhead(f) for f in faze) + "</tr>"
    rows = ""
    for r in radky:
        rel = r.get("relevantni")  # fáze, kde úhel dává smysl (model); bez pole = všechny
        bunky = (r.get("bunky") or [0] * len(faze))[:len(faze)]
        cells = ""
        for i, n in enumerate(bunky):
            # nerelevantní kombinace (sleva × cítí problém apod.) bez reklam → šedé „—",
            # nepočítá se jako volno; buňka S reklamami se ukazuje vždy (důkaz z registru)
            if rel and faze[i] not in rel and not n:
                cells += '<td class="na">—</td>'
            else:
                cls, lab = _stav_cls(n)
                cells += f'<td class="{cls}">{int(n or 0)}<span class="st">{lab}</span></td>'
        rows += f'<tr><td class="rowl">{e(r.get("uhel"))}</td>{cells}</tr>'
    opps = ""
    for o in (mu.get("prilezitosti") or []):
        pk = (f'<div class="pk"><b>→ Udělejte:</b> {e(o["pokyn"])}</div>') if o.get("pokyn") else ""
        opps += (f'<div class="op"><div class="ohead"><span class="tag">🟢 VOLNO</span>'
                 f'<b>{e(o.get("uhel"))} × {e(aw_cz(o.get("faze")))}</b></div>'
                 f'<div class="proc">{e(o.get("proc"))}</div>{pk}</div>')
    opps_html = f'<div class="oppo">{opps}</div>' if opps else ""
    return (f'<div class="card"><div class="chead"><h3>Obsazené a volné úhly konkurenta</h3>'
            f'<span class="sub">🔴 PLNO · 🟡 SLABŠÍ · 🟢 VOLNO = PŘÍLEŽITOST · — kombinace pro úhel nedává smysl</span></div>'
            f'<div style="padding:16px 18px"><table class="matrix">{head}{rows}</table></div>{opps_html}</div>')


_PLAN_COLORS = ["hsl(203 100% 60%)", "hsl(152 60% 52%)", "hsl(350 86% 65%)"]


def _attack_plan(rep):
    plan = rep.get("utocny_plan") or []
    if not plan:
        return ""
    cards = ""
    for i, t in enumerate(plan[:3]):
        col = _PLAN_COLORS[i % 3]
        hoff = ""
        if t.get("handoff"):
            hoff = (f'<textarea class="hoff" id="hoff-{i}" readonly>{e(t["handoff"])}</textarea>'
                    f'<button class="hbtn" onclick="copyHoff({i},this)"><svg width="15" height="15" fill="currentColor"><use href="#i-cmt"/></svg>Zadat AI Marketérovi</button>'
                    '<div class="hnote">Zkopíruje hotové zadání — vložte ho AI Marketérovi do chatu.</div>')
        zdroj = f'<div class="zdroj">{e(t.get("zdroj"))}</div>' if t.get("zdroj") else ""
        cards += (f'<div class="pcard" style="--pc:{col}"><div class="pno">{i + 1}</div>'
                  f'<div class="ptah">{e(t.get("tah"))}</div><h3>{e(t.get("titulek"))}</h3>'
                  f'<p>{e(t.get("popis"))}</p>{zdroj}{hoff}</div>')
    return f'<div class="plan">{cards}</div>'


def _google_block(rep):
    """Google reklamy VIZUÁLNĚ: registr nedává copy, ale dává archivní náhled kreativy
    (googlesyndication simgad) — ukazujeme mřížku reálných kreativ + délku běhu
    (nejsilnější signál: co běží roky, to vydělává). Klik → zvětšení v popupu.
    Mřížka ukazuje JEN domácí trh (`mimo_trh` kusy filtruje) — zahraniční kampaně
    patří do analytické poznámky `google_expanze`, ne mezi kreativy ke klonování."""
    gads = [g for g in (rep.get("google_reklamy") or [])
            if (g.get("thumb") or g.get("nm")) and not g.get("mimo_trh")]
    if not gads:
        return ""
    gads = sorted(gads, key=lambda g: -int(g.get("dni") or 0))

    def _img_ok(t):
        # JS preview registru nejde vložit jako <img> (vrací skript) — bez náhledu
        return t and "/ads/preview/content.js" not in t
    fmt_cz = {"text": "textová", "image": "obrázek", "video": "video"}
    cards = ""
    for g in gads:
        th = g.get("thumb")
        img = (f'<div class="gth" onclick="openImg(\'{e(th)}\')"><img src="{e(th)}" loading="lazy" alt=""></div>'
               if _img_ok(th) else '<div class="gth gth-empty">náhled jen v registru</div>')
        fmt = f'<span class="fmt">{e(fmt_cz.get(g.get("format"), g.get("format") or ""))}</span>'
        dni = f'<span class="gdni">běží {e(g["dni"])} dní</span>' if g.get("dni") else ""
        txt = f'<div class="gnm">{e(g["nm"])}</div>' if g.get("nm") else ""
        cards += f'<div class="gcard">{img}<div class="gmeta">{fmt}{dni}</div>{txt}</div>'
    exp = ""
    if rep.get("google_expanze"):
        exp = (f'<div class="gexp"><b>🌍 Zahraniční expanze (z registru):</b> '
               f'{e(rep["google_expanze"])}</div>')
    return f'<div class="ggrid">{cards}</div>{exp}'


def render_competitor(rep, out_path):
    # thumbnaily vedle HTML → relativní cesty (board je přenositelný: ZIP/mail/jiný počítač)
    out_dir = os.path.dirname(os.path.abspath(out_path))
    for v in (rep.get("vitezove") or []):
        t = v.get("thumb")
        if t and os.path.dirname(os.path.abspath(t)) == out_dir:
            v["thumb"] = os.path.basename(t)
    m = rep.get("meta", {})
    kon = m.get("konkurent") or {}
    znacka = kon.get("znacka") or kon.get("domena") or ""
    trh = (m.get("trh") or "cz").upper()
    stat = rep.get("stat") or {}
    kanaly = rep.get("kanaly") or {}
    vit = rep.get("vitezove") or []

    podtitulek = m.get("podtitulek") or (
        f'Co značka {znacka} právě platí v reklamách — jejich ověření vítězové ke klonování, '
        'úhly, které přeplnili, a volná místa, kde na ně zaútočíte.')

    p = ['<!doctype html><html lang="cs"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>Competitor Ad Board — {e(znacka)}</title>'
         '<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800'
         '&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">'
         f'<style>{DEMO_CSS}{COMP_CSS}</style></head><body>{SVG_DEFS}<div class="wrap">']

    # hlavička
    p.append(
        f'<div class="phead"><div>'
        f'<h1>Competitor Ad Board <span class="theme">— {e(znacka)}</span></h1>'
        f'<div class="meta"><span class="mchip">ad-scout</span><span>trh {e(trh)}</span> · '
        f'<span class="mono">{e(m.get("sken"))}</span> · <span>z veřejných reklamních registrů (EU transparentnost)</span></div>'
        f'<p class="subtitle">{e(podtitulek)}</p></div>'
        f'<div class="right"><span class="pill ok">REÁLNÁ DATA</span></div></div>')

    # stat row (5): Meta a Google zvlášť — reálné počty z registrů (browser tool), vzorek jako dovětek
    rt = stat.get("registr_total") or {}
    if rt.get("meta"):
        meta_val = f'~{fnum(rt["meta"])}'
        meta_delta = f'aktivních v knihovně reklam Meta · analyzovaný vzorek: {stat.get("meta_reklam", 0)}'
    else:
        meta_val = stat.get("meta_reklam", 0)
        meta_delta = "aktivních reklam ve vzorku z knihovny Meta"
    if rt.get("google"):
        goo_val = f'~{fnum(rt["google"])}'
        goo_delta = f'aktivních v registru Google · analyzovaný vzorek: {stat.get("google_reklam", 0)}'
    else:
        goo_val = stat.get("google_reklam", 0)
        goo_delta = "aktivních reklam ve vzorku z registru Google"
    # volné úhly deterministicky: s `relevantni` = zelené buňky (relevantní a prázdné),
    # bez něj = řádky mapy bez jediné reklamy; fallback model hodnota
    mu_ = rep.get("mapa_utoku") or {}
    radky_mu, faze_mu = mu_.get("radky") or [], mu_.get("faze") or []
    if radky_mu and any(r.get("relevantni") for r in radky_mu):
        volne = 0
        for r in radky_mu:
            rel = r.get("relevantni")
            bunky = (r.get("bunky") or [0] * len(faze_mu))[:len(faze_mu)]
            volne += sum(1 for i, n in enumerate(bunky)
                         if not n and (not rel or faze_mu[i] in rel))
    elif radky_mu:
        volne = sum(1 for r in radky_mu if not any(r.get("bunky") or []))
    else:
        volne = stat.get("uhly_volne")
    p.append('<div class="stats" style="grid-template-columns:repeat(5,1fr)">'
             + _stat("Reklamy Meta", meta_val, meta_delta, "217 100% 65%", "i-fb")
             + _stat("Reklamy Google", goo_val, goo_delta, "45 96% 55%", "i-goo")
             + _stat("Nejdéle běžící", f'{stat.get("nejdele_bezici_dni", 0)}', "dní běhu — za co platí nejdéle", "168 72% 48%", "i-clk")
             + _stat("Volné úhly", ("—" if volne is None else volne), "kde konkurent mlčí = kudy zaútočit", "152 60% 46%", "i-tgt")
             + _stat("Nových za 30 dní", stat.get("nove_30d", 0), "čerstvě nasazené reklamy — co právě testuje", "205 100% 62%", "i-bolt")
             + '</div>')

    # kanály — právě DVA proklikové chipy do veřejných registrů (Meta knihovna + Google registr)
    reg = kanaly.get("registry") or {}
    meta_url = reg.get("meta_adlib") or (
        "https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
        f"&country={trh}&q={urllib.parse.quote(znacka)}&search_type=page&media_type=all")
    def _kchip(url, ic, lab, col):
        # barevně rozlišené per síť (Meta modrá / Google žlutá), ať jdou od sebe na první pohled
        return (f'<span class="kchip" style="border-color:{col}40">'
                f'<a href="{e(url)}" target="_blank" rel="noopener" style="color:{col}">'
                f'<svg fill="currentColor"><use href="#{ic}"/></svg>{lab} ↗</a></span>')

    chips = ""
    if stat.get("meta_reklam") or reg.get("meta") or reg.get("meta_adlib"):
        chips += _kchip(meta_url, "i-fb", "Facebook / Instagram", "#4A8CFF")
    if reg.get("google"):
        chips += _kchip(reg["google"], "i-goo", "Google / YouTube", "#FBBC05")
    if chips:
        p.append(f'<div class="chips-kanaly"><span style="font-family:var(--font-mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:hsl(var(--fg-dim))">Reklamní kanály značky</span>{chips}</div>')

    _n = [0]

    def secno():
        _n[0] += 1
        return f"{_n[0]:02d}"

    # 01) JEJICH VÍTĚZOVÉ
    if vit:
        p.append(_sectionhead(secno(), "Jejich vítězové — za tyhle platí nejdéle",
                              "Ověřené reklamy konkurenta seřazené podle dosahu v EU × počtu variant (dny běhu jako druhotný důkaz). "
                              "Vezměte si kostru, ne značku — každá karta říká, jak ji naklonovat na váš produkt."))
        p.append(_grid("grid-win", "".join(_comp_card(r) for r in vit), len(vit)))

    # GOOGLE REKLAMY — vizuální mřížka kreativ z registru
    gb = _google_block(rep)
    if gb:
        gmix = rep.get("google_mix") or {}
        mix_cz = {"text": "textová", "image": "obrázková", "video": "video"}
        mix_txt = " · ".join(f"{v}× {mix_cz.get(k, k)}" for k, v in sorted(gmix.items(), key=lambda x: -x[1]))
        n_mix = sum(gmix.values())
        g_tot = (stat.get("registr_total") or {}).get("google")
        plny = (f"kompletní výpis (~{fnum(g_tot)} reklam v registru) otevřete tlačítkem „Google / YouTube ↗“ nahoře."
                if g_tot else "kompletní výpis je rozsáhlejší, otevřete ho tlačítkem „Google / YouTube ↗“ nahoře.")
        vzorek = (f" Analyzovaný vzorek: {n_mix} nejdéle běžících kreativ ({e(mix_txt)}) — {plny}") if n_mix else ""
        p.append(_sectionhead(secno(), "Stejná značka ve vyhledávání a na YouTube",
                              "Reálné kreativy z veřejného registru Google seřazené podle délky běhu — "
                              f"co běží roky, to vydělává. Klik na kreativu = zvětšení.{vzorek}"))
        p.append(gb)

    # 02) MAPA ÚHLŮ — KDE ZAÚTOČIT
    am = _attack_matrix(rep)
    if am:
        p.append(_sectionhead(secno(), "Mapa úhlů — kde je díra",
                              "Které úhly a pásma trychtýře konkurent obsadil (🔴), kde je slabší (🟡) a kde mlčí (🟢). "
                              "Neporazíte ho tam, kde je silný — obejdete ho tam, kde chybí."))
        p.append(am)

    # 03) ÚTOČNÝ PLÁN — 3 TAHY
    ap = _attack_plan(rep)
    if ap:
        p.append(_sectionhead(secno(), "Útočný plán — 3 tahy",
                              "Syntéza celého boardu do tří konkrétních tahů. Každý tah má hotové zadání pro vašeho AI Marketéra — nic nevymýšlíte."))
        p.append(ap)

    pk = rep.get("pokryti") or {}
    p.append(f'<div class="pagefoot">CliqSales · Ad Scout · Competitor Ad Board · spuštěno doménou konkurenta · '
             f'reálná data z veřejných reklamních registrů · {e(pk.get("meta", 0))} reklam Facebook/Instagram + '
             f'{e(pk.get("google", 0))} Google/YouTube · {e(m.get("sken"))}</div>')
    p.append('</div>'
             '<div id="vpop" class="vpop" onclick="closeVid(event)"><div class="vpop-inner" onclick="event.stopPropagation()">'
             '<button class="vpop-x" onclick="closeVid(event)" aria-label="Zavřít">✕</button>'
             '<video id="vpopv" controls playsinline></video>'
             '<img id="vpopi" alt="" style="display:none;max-height:84vh;max-width:90vw;width:auto;height:auto;object-fit:contain;border-radius:12px">'
             '</div></div>'
             '<script>'
             'function more(b){var g=document.getElementById(b.dataset.grid);g.classList.remove("collapsed");b.remove()}'
             'function openVid(u){var m=document.getElementById("vpop"),v=document.getElementById("vpopv"),i=document.getElementById("vpopi");i.style.display="none";v.style.display="";v.parentNode.classList.remove("img");v.src=u;m.classList.add("on");v.play().catch(function(){})}'
             'function openImg(u){var m=document.getElementById("vpop"),v=document.getElementById("vpopv"),i=document.getElementById("vpopi");v.pause&&v.pause();v.style.display="none";i.parentNode.classList.add("img");i.src=u;i.style.display="";m.classList.add("on")}'
             'function closeVid(e){var m=document.getElementById("vpop"),v=document.getElementById("vpopv"),i=document.getElementById("vpopi");v.pause();v.removeAttribute("src");v.load();i.removeAttribute("src");m.classList.remove("on")}'
             'function copyHoff(i,btn){var t=document.getElementById("hoff-"+i);var done=function(){var o=btn.innerHTML;btn.innerHTML="✓ Zkopírováno — vložte AI Marketérovi";setTimeout(function(){btn.innerHTML=o},2600)};'
             'if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t.value).then(done)}else{t.style.position="static";t.select();document.execCommand("copy");t.style.position="absolute";done()}}'
             'document.addEventListener("keydown",function(e){if(e.key==="Escape")closeVid()});'
             '</script></body></html>')

    with open(out_path, "w") as f:
        f.write("".join(x for x in p if x))
    return out_path


if __name__ == "__main__":
    rep = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else "viral-ad-board.html"
    if (rep.get("meta") or {}).get("vystup") == "competitor-ad-board":
        print(render_competitor(rep, out if out != "viral-ad-board.html" else "competitor-ad-board.html"))
    else:
        print(render(rep, out))
