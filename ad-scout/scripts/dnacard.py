#!/usr/bin/env python3
"""Renderer: Viral DNA Card™ → HTML (hloubkový rozbor jedné virální předlohy).

Karta = klon-šablona pro tvorbu vlastní kreativy (Ad DNA Method™ — krok Dekóduj
→ vstup do Neural Clone). Funguje pro reklamu i organický obsah.
Design 1:1 z dema `documents/ads/scout/dna-deep-dive-demo/dna-card.html`.

Sekce: hero (náhled + trakce + snímky + proč předloha) → 01 Vizuální DNA →
02 Textová & strukturní DNA (+ vrstva přepis) → 03 Reakce publika → Jak tuhle
DNA naklonovat. Renderer vykresluje jen vyplněné sekce (prázdné přeskočí).

Pravidla: čeština (vykání), žádná jména zdrojových aktorů/metod sběru,
cizí kreativa se NEREHOSTUJE (jen náhled k rozboru + odkaz na originál),
komentáře bez jmen (GDPR — strhává už provider). Slovo „donor" je jen interní
klíč schématu — v renderovaném textu VŽDY „předloha".

v0.1 — render dna-card.json (schéma v references/viral-dna-card.md).
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _adboard_assets import SVG_DEFS  # sdílené ikony — stejné jako na boardech

CSS = """
:root{--bg:224 86% 5%;--s1:226 36% 10.5%;--s2:228 31% 14%;--bd:226 26% 17%;
 --fg:210 32% 97%;--fgm:220 14% 80%;--fgd:221 11% 62%;--brand:203 100% 49%;--bl:205 100% 60%;--mint:178 85% 78%;
 --ind:208 100% 55%;--succ:152 60% 46%;--warn:37 92% 56%;--coral:350 86% 65%;--f:'Inter',system-ui,sans-serif;--m:'JetBrains Mono',monospace}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--f);background:hsl(var(--bg));color:hsl(var(--fg));-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;background:
 radial-gradient(900px 600px at 18% -8%,hsl(var(--ind)/.24),transparent 60%),
 radial-gradient(1100px 700px at 88% 4%,hsl(var(--brand)/.16),transparent 58%),
 radial-gradient(800px 800px at 60% 120%,hsl(var(--ind)/.13),transparent 55%)}
.wrap{position:relative;z-index:1;max-width:1180px;margin:0 auto;padding:40px 48px 70px}
.mono,.mchip{font-family:var(--m)}
.mchip{background:hsl(var(--s1));border:1px solid hsl(var(--bd));border-radius:7px;padding:3px 8px;color:hsl(var(--fgm));font-size:11px}
.phead{display:flex;align-items:flex-start;gap:16px;margin-bottom:30px}
.phead h1{font-size:34px;font-weight:800;letter-spacing:-.03em;line-height:1.05}
.phead h1 .theme{background:linear-gradient(90deg,#119CFF,#97F8F4);-webkit-background-clip:text;background-clip:text;color:transparent}
.phead .orig{color:hsl(var(--fgd));font-style:italic;font-size:14px;margin-top:7px}
.phead .subtitle{margin-top:11px;font-size:14px;color:hsl(var(--fgm));max-width:760px;line-height:1.55}
.phead .meta{display:flex;align-items:center;gap:9px;margin-top:12px;font-size:13.5px;color:hsl(var(--fgm));flex-wrap:wrap}
.phead .right{margin-left:auto}
.pill{display:inline-flex;align-items:center;gap:7px;height:30px;padding:0 13px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid hsl(var(--warn)/.32);background:hsl(var(--warn)/.09);color:hsl(var(--warn));white-space:nowrap}
.hero{display:grid;grid-template-columns:380px 1fr;gap:30px;align-items:start;margin-bottom:14px}
.pic{border-radius:16px;overflow:hidden;border:1px solid hsl(var(--bd));box-shadow:0 24px 60px -26px rgba(0,0,0,.9);position:relative}
.pic img{width:100%;display:block}
.pic video{width:100%;display:block;background:#000}
.fsbtn{position:absolute;top:10px;right:10px;width:34px;height:34px;border-radius:9px;background:rgba(0,0,0,.55);backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,.28);color:#fff;font-size:16px;line-height:1;cursor:pointer;display:grid;place-items:center;transition:background .15s}
.fsbtn:hover{background:hsl(var(--brand)/.85)}
.piccap{margin-top:9px;font-family:var(--m);font-size:11px;color:hsl(var(--mint))}
.pic .plabel{position:absolute;bottom:0;left:0;right:0;background:linear-gradient(0deg,rgba(0,0,0,.85),transparent);padding:22px 14px 10px;font-family:var(--m);font-size:11px;color:hsl(var(--mint))}
.chrow{display:flex;align-items:center;gap:12px;margin:2px 0 14px;flex-wrap:wrap}
.chrow .ch{color:hsl(var(--fgm));font-size:13.5px}
.chrow .ch a{color:inherit;text-decoration:none;border-bottom:1px dashed hsl(var(--fgd)/.55)}
.chrow .ch a:hover{color:hsl(var(--bl));border-bottom-color:hsl(var(--bl)/.6)}
.openbtn{margin-left:auto;display:inline-flex;align-items:center;gap:8px;height:32px;padding:0 14px;border-radius:999px;border:1px solid hsl(var(--bd));background:hsl(var(--s2));color:hsl(var(--fg));font-size:12.5px;font-weight:600;text-decoration:none;white-space:nowrap}
.openbtn svg{width:14px;height:14px;fill:currentColor}
.openbtn:hover{border-color:hsl(var(--brand)/.55);color:hsl(var(--bl))}
.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.stat{position:relative;border-radius:13px;padding:14px 15px;overflow:hidden;background:linear-gradient(180deg,hsl(var(--s1)),hsl(var(--bg)/.4));border:1px solid hsl(var(--bd)/.85);box-shadow:0 1px 0 rgba(255,255,255,.04) inset,0 12px 30px -18px rgba(0,0,0,.8)}
.stat::after{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:linear-gradient(90deg,transparent,var(--accent,hsl(var(--brand))),transparent);opacity:.85}
.stat .top{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.stat .lbl{font-size:10.5px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;color:hsl(210 22% 86%)}
.stat .ic{width:26px;height:26px;border-radius:8px;display:grid;place-items:center;background:var(--accent-bg,hsl(var(--brand)/.12));color:var(--accent,hsl(var(--brand)))}
.stat .ic svg{width:14px;height:14px}
.stat .val{font-size:25px;font-weight:700;letter-spacing:-.02em;font-family:var(--m);line-height:1;color:var(--accent,hsl(var(--fg)))}
.stat .val small{font-size:13px;color:hsl(var(--fgm));font-weight:600}
.stat .delta{font-size:11px;color:hsl(var(--fgd));margin-top:8px}
.frames{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-top:14px}
.frames img{width:100%;aspect-ratio:9/13;object-fit:cover;border-radius:9px;border:1px solid hsl(var(--bd));display:block}
.frames .flabel{grid-column:1/-1;font-family:var(--m);font-size:10.5px;color:hsl(var(--fgd));margin-top:2px}
.sec{margin-top:34px}.sechead{display:flex;align-items:baseline;gap:10px;margin-bottom:9px}
.secno{font-family:var(--m);font-size:30px;font-weight:700;color:hsl(var(--bl));line-height:1}
.sec h3{font-size:23px;font-weight:800;letter-spacing:-.02em}
.sec .lead{font-size:13.5px;color:hsl(var(--fgm));margin-bottom:18px}
.blk{border-radius:16px;background:linear-gradient(180deg,hsl(var(--s1)),hsl(var(--bg)/.35));border:1px solid hsl(var(--bd)/.85);padding:20px 22px}
.duo{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.dna{display:flex;gap:13px;padding:13px 0;border-bottom:1px solid hsl(var(--bd)/.4);font-size:13.5px;line-height:1.5}
.dna:last-child{border-bottom:none}
.dna .k{flex:none;width:150px;font-weight:700;color:hsl(var(--fg))}
.dna .vv{color:hsl(var(--fgm))}.dna .vv b{color:hsl(var(--fg))}
.chip{display:inline-block;font-family:var(--m);font-size:9px;letter-spacing:.04em;text-transform:uppercase;color:hsl(var(--mint));background:hsl(var(--mint)/.1);border:1px solid hsl(var(--mint)/.25);border-radius:6px;padding:2px 8px;margin:0 4px 4px 0}
.layer{border:1px dashed hsl(var(--bd));border-radius:12px;padding:14px 16px;font-size:13px;color:hsl(var(--fgd));line-height:1.55;background:hsl(var(--s1)/.4)}
.layer b{color:hsl(var(--fgm))}
.dietrow{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
.dcol{border-radius:13px;border:1px solid hsl(var(--bd)/.8);background:hsl(var(--s1)/.55);padding:15px 16px}
.dcol h4{font-size:13px;font-weight:700;margin-bottom:9px;display:flex;align-items:center;gap:8px}
.dcol h4 .dot{width:9px;height:9px;border-radius:99px;flex:none}
.dcol ul{list-style:none}
.dcol li{padding:7px 0;border-bottom:1px solid hsl(var(--bd)/.35);font-size:12.5px;line-height:1.5}
.dcol li:last-child{border-bottom:none}
.dcol .q{font-style:italic;color:hsl(var(--fg))}
.dcol .expl{display:block;color:hsl(var(--fgd));font-size:11.5px;margin-top:2px}
.fraze{margin-top:14px}.fraze .fl{display:block;font-family:var(--m);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:hsl(var(--fgd));margin-bottom:8px}
.fpill{display:inline-block;font-size:12px;font-style:italic;color:hsl(var(--fg));background:hsl(var(--s2));border:1px solid hsl(var(--bd));border-radius:999px;padding:4px 12px;margin:0 6px 6px 0}
.ttag{display:inline-block;font-family:var(--m);font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:hsl(var(--warn));background:hsl(var(--warn)/.09);border:1px solid hsl(var(--warn)/.3);border-radius:6px;padding:3px 9px;margin:0 6px 6px 0}
.clone{border-radius:16px;background:hsl(226 32% 12.5%);border:1px solid hsl(220 26% 20%);padding:24px 26px}
.clone .r{display:flex;gap:14px;margin-bottom:16px;font-size:14px;line-height:1.6}.clone .r:last-child{margin-bottom:0}
.clone .ic{width:30px;height:30px;border-radius:9px;flex:none;display:grid;place-items:center;font-family:var(--m);font-weight:700;font-size:12px}
.clone b{color:hsl(var(--fg))}.clone .r>div{color:hsl(var(--fgm))}
.alink{color:hsl(var(--bl));text-decoration:none;font-size:13px;font-weight:600}
.foot{margin-top:38px;font-family:var(--m);font-size:10.5px;color:hsl(var(--fgm));line-height:1.6}
@media(max-width:880px){.hero{grid-template-columns:1fr}.duo{grid-template-columns:1fr}.dietrow{grid-template-columns:1fr}.frames{grid-template-columns:repeat(3,1fr)}}
"""

NET_CZ = {"youtube": "YouTube", "youtube-shorts": "YouTube Shorts", "tiktok": "TikTok",
          "instagram": "Instagram", "facebook": "Facebook", "meta": "Meta (Facebook/Instagram)",
          "linkedin": "LinkedIn", "adlib": "veřejná knihovna reklam"}
TYP_CZ = {"organika": "organický obsah", "reklama": "placená reklama"}
FMT_CZ = {"short": "krátké video", "long": "dlouhý obsah", "static": "statická reklama",
          "video": "videoreklama"}
# ikona zdrojové sítě pro tlačítko „Otevřít příspěvek/reklamu"
NET_IC = {"tiktok": "i-tt", "youtube": "i-yt", "youtube-shorts": "i-yt", "instagram": "i-ig",
          "facebook": "i-fb", "meta": "i-fb", "adlib": "i-fb", "linkedin": "i-li"}
# klon ikony: písmeno → barva (V vizuál · H hook · U úhel · F formát/nabídka)
KLON_IC = {"V": ("hsl(var(--coral)/.16)", "hsl(var(--coral))"),
           "H": ("hsl(var(--brand)/.16)", "hsl(var(--bl))"),
           "U": ("hsl(38 92% 56%/.16)", "hsl(38 92% 62%)"),
           "Ú": ("hsl(38 92% 56%/.16)", "hsl(38 92% 62%)"),
           "F": ("hsl(152 60% 46%/.16)", "hsl(152 70% 60%)")}


def e(x):
    return html.escape(str(x if x is not None else ""))


def fnum(n):
    try:
        return f"{int(n):,}".replace(",", " ")
    except Exception:
        return e(n)


def fnum_c(n):
    """Kompakt do velkých dlaždic: 1400000 → „1,4 mil.", 35700 → „35,7 tis."."""
    try:
        v = float(n)
    except Exception:
        return e(n)
    if v >= 1_000_000:
        s = f"{v / 1_000_000:.1f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{s}&nbsp;<small>mil.</small>"
    if v >= 10_000:
        s = f"{v / 1_000:.1f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{s}&nbsp;<small>tis.</small>"
    return fnum(n)


def _dur_h(dur):
    """Délka lidsky: '72' → '1:12', '00:05:26' → '5:26'."""
    if not dur:
        return None
    s = str(dur)
    if ":" in s:
        return s.lstrip("0:") if len(s.lstrip("0:")) >= 3 else s
    try:
        sec = int(float(s))
        return f"{sec // 60}:{sec % 60:02d}"
    except Exception:
        return s


def _src(t):
    return ("file://" + t) if str(t).startswith("/") else t


def _kanal_url(d):
    """URL profilu/kanálu autora — z `kanal_url`, jinak dovodí z URL kusu (kde to jde)."""
    if d.get("kanal_url"):
        return d["kanal_url"]
    u = str(d.get("url") or "")
    m = re.match(r"(https://www\.tiktok\.com/@[^/?#]+)/", u)
    if m:
        return m.group(1)
    m = re.match(r"(https://www\.youtube\.com/@[^/?#]+)", u)
    if m:
        return m.group(1)
    return None


def _stat(lbl, val, delta, acc, ic):
    """Dlaždice metriky — stejný vzor jako stat row na boardech (barva + ikona + popisek)."""
    accf = acc if acc.startswith("var(") else f"hsl({acc})"
    accbg = "hsl(var(--brand)/.12)" if acc.startswith("var(") else f"hsl({acc}/.12)"
    return (f'<div class="stat" style="--accent:{accf};--accent-bg:{accbg}"><div class="top"><span class="lbl">{e(lbl)}</span>'
            f'<span class="ic"><svg fill="currentColor"><use href="#{ic}"/></svg></span></div>'
            f'<div class="val">{val}</div><div class="delta">{e(delta)}</div></div>')


def _stats(d):
    out = []
    if d.get("zhlednuti"):
        out.append(_stat("Zhlédnutí", fnum_c(d["zhlednuti"]), "celkový dosah kusu", "var(--brand)", "i-eye"))
    if d.get("likes"):
        out.append(_stat("Lajků", fnum_c(d["likes"]), "pozitivní odezva publika", "350 86% 65%", "i-heart"))
    if d.get("cmts"):
        out.append(_stat("Komentářů", fnum_c(d["cmts"]), "vstupů do diskuse", "168 72% 48%", "i-cmt"))
    if d.get("shares"):
        out.append(_stat("Sdílení", fnum_c(d["shares"]), "posílají dál — nejsilnější signál", "37 92% 56%", "i-fire"))
    if d.get("engagement_pct"):
        out.append(_stat("Zapojení", f'{str(d["engagement_pct"]).replace(".", ",")}&nbsp;<small>%</small>',
                         "interakce vůči zhlédnutím", "152 60% 46%", "i-bolt"))
    if d.get("dosah_eu"):
        out.append(_stat("Dosah EU", fnum_c(d["dosah_eu"]), "unikátních uživatelů v EU", "var(--brand)", "i-eye"))
    if d.get("dni"):
        out.append(_stat("Dní běhu", fnum(d["dni"]), "běží beze změny — ověřený vítěz", "168 72% 48%", "i-clk"))
    if d.get("varianty"):
        out.append(_stat("Variant", fnum(d["varianty"]), "kolik verzí inzerent testuje", "205 100% 62%", "i-lay"))
    dh = _dur_h(d.get("dur"))
    if dh:
        out.append(_stat("Délka", e(dh), "stopáž kusu", "205 100% 62%", "i-clk"))
    return "".join(out)


def _rows(radky):
    out = ""
    for r in radky or []:
        out += (f'<div class="dna"><div class="k">{e(r.get("k"))}</div>'
                f'<div class="vv">{r.get("v") or ""}</div></div>')  # v = model HTML (smí <b>)
    return out


def _panel(title, items, dot):
    if not items:
        return ""
    lis = ""
    for it in items[:5]:
        if isinstance(it, dict):
            q, ex = it.get("q") or "", it.get("e") or ""
        else:
            q, ex = it, ""
        lis += (f'<li><span class="q">„{e(q)}“</span>'
                + (f'<span class="expl">{e(ex)}</span>' if ex else "") + "</li>")
    return (f'<div class="dcol"><h4><span class="dot" style="background:{dot}"></span>{e(title)}'
            f'</h4><ul>{lis}</ul></div>')


def render(card, out_path):
    m = card.get("meta", {})
    d = card.get("donor", {})
    tema = m.get("tema")
    net_cz = NET_CZ.get(str(d.get("sit") or "").lower(), d.get("sit") or "")
    typ_cz = TYP_CZ.get(d.get("typ"), d.get("typ") or "")
    fmt_cz = FMT_CZ.get(d.get("format"), d.get("format") or "")

    p = ['<!doctype html><html lang="cs"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>Viral DNA Card™ — „{e(d.get("nm") or tema or "")}"</title>'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800'
         '&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">'
         f'<style>{CSS}</style></head><body>{SVG_DEFS}<div class="wrap">']

    # nadpis = název kusu (česky, gradient); anglický originál kurzívou pod ním
    theme = d.get("nm") or tema or typ_cz
    orig_h = f'<div class="orig">„{e(d["orig"])}“</div>' if d.get("orig") else ""
    tema_h = f'<span>téma: „{e(tema)}"</span> · ' if tema else ""
    sub = m.get("podtitulek") or (
        "Hloubkový rozbor jednoho virálního kusu — co přesně na něm funguje (vizuál, text, "
        "reakce publika) a hotový recept, jak stejný vzorec přenést do vlastní reklamy.")
    p.append(
        f'<div class="phead"><div><h1>Viral DNA Card™ <span class="theme">— „{e(theme)}"</span></h1>{orig_h}'
        f'<div class="meta"><span class="mchip">ad-scout · rozbor virální předlohy</span>'
        f'{tema_h}<span>zdroj: {e(net_cz)} ({e(typ_cz)})</span> · <span class="mono">{e(m.get("sken"))}</span></div>'
        f'<p class="subtitle">{e(sub)}</p></div></div>')

    # hero: vlevo náhled (inline přehrávač, když máme video), vpravo metriky + klíčové snímky + proč
    thumb = d.get("thumb")
    vsrc = _src(d["video"]) if d.get("video") else None
    pic = ""
    if vsrc:
        ratio = "9/16" if d.get("format") == "short" else "16/9"
        poster = f' poster="{e(_src(thumb))}"' if thumb else ""
        pic = (f'<div><div class="pic"><video id="dnavid" src="{e(vsrc)}"{poster} controls playsinline '
               f'preload="metadata" style="aspect-ratio:{ratio};object-fit:cover"></video>'
               '<button class="fsbtn" onclick="fs()" title="Celá obrazovka">⛶</button></div>'
               '<div class="piccap">▲ reálný kus — přehrajte si ho přímo tady, ⛶ = celá obrazovka</div></div>')
    elif thumb:
        pic = (f'<div class="pic"><img src="{e(_src(thumb))}" alt="náhled předlohy">'
               '<div class="plabel">▲ reálný náhled — vstup do analýzy vizuální DNA</div></div>')
    # řádek kanálu: proklikový profil autora + tlačítko „Otevřít příspěvek/reklamu" na zdroji
    kanal = _kanal_url(d)
    kdo_h = (f'<a href="{e(kanal)}" target="_blank" rel="noopener">{e(d.get("kdo"))}</a>'
             if kanal and d.get("kdo") else e(d.get("kdo") or ""))
    ch_h = " · ".join(x for x in (kdo_h, e(fmt_cz), e(net_cz)) if x)
    btn = ""
    if d.get("url"):
        lab = "Otevřít reklamu" if d.get("typ") == "reklama" else "Otevřít příspěvek"
        ic = NET_IC.get(str(d.get("sit") or "").lower())
        ic_h = f'<svg><use href="#{ic}"/></svg>' if ic else ""
        btn = (f'<a class="openbtn" href="{e(d["url"])}" target="_blank" rel="noopener">'
               f'{ic_h}{lab} ↗</a>')
    vd = card.get("vizualni_dna") or {}
    frames = [f for f in (vd.get("frames") or []) if f]
    fr_h = ""
    if frames:
        imgs = "".join(f'<img src="{e(_src(f))}" alt="">' for f in frames[:6])
        fr_h = (f'<div class="frames">{imgs}<span class="flabel">▲ klíčové snímky průběhu videa '
                '— podklad rozboru tempa a vizuálních vzorců</span></div>')
    proc = (f'<div style="font-size:12.5px;color:hsl(var(--fgd));margin-top:14px;line-height:1.5">'
            f'<b style="color:hsl(var(--fgm))">Proč tato předloha:</b> {e(d["proc_donor"])}</div>') if d.get("proc_donor") else ""
    p.append(f'<div class="hero">{pic}<div class="hi">'
             f'<div class="chrow"><span class="ch">{ch_h}</span>{btn}</div>'
             f'<div class="stats">{_stats(d)}</div>{fr_h}{proc}</div></div>')

    n = [0]

    def secno():
        n[0] += 1
        return f"{n[0]:02d}"

    # 01 vizuální DNA
    if vd.get("radky"):
        chips = "".join(f'<span class="chip">vzorec: {e(v)}</span>' for v in vd.get("vzorce") or [])
        p.append(f'<div class="sec"><div class="sechead"><span class="secno">{secno()}</span>'
                 '<h3>Vizuální DNA — co diváka zastaví</h3></div>'
                 '<div class="lead">Rozbor prvního snímku a vizuálních vzorců: co přesně na náhledu zastaví pozornost a proč.</div>'
                 f'<div class="blk">{_rows(vd["radky"])}'
                 + (f'<div style="margin-top:12px">{chips}</div>' if chips else "") + "</div></div>")

    # 02 textová & strukturní DNA
    td = card.get("textova_dna") or {}
    pr = card.get("prepis") or {}
    if td.get("radky") or td.get("kostra"):
        left = f'<div class="blk">{_rows(td.get("radky"))}</div>'
        kost = ""
        if td.get("kostra"):
            kost = (f'<div class="dna" style="border-bottom:1px solid hsl(var(--bd)/.4)">'
                    f'<div class="k">Kostra ({e(td.get("kostra_zdroj") or "odhad")})</div>'
                    f'<div class="vv">{td["kostra"]}</div></div>')
        if pr.get("stav") == "ok":
            hook = f'<b>Mluvený hook (první ~3 s):</b> „{e(pr["hook_3s"])}“<br>' if pr.get("hook_3s") else ""
            note = e(pr.get("poznamka") or "Celý přepis je uložen u karty — kostra výše z něj vychází.")
            layer = f'<div class="layer" style="margin-top:14px"><b>▸ Vrstva PŘEPIS</b> — k dispozici. {hook}<i>{note}</i></div>'
        else:
            note = e(pr.get("poznamka") or "Přepis nebyl u tohoto kusu dostupný — kostra je odhad z titulku a popisu.")
            layer = f'<div class="layer" style="margin-top:14px"><b>▸ Vrstva PŘEPIS</b> — <i>{note}</i></div>'
        p.append(f'<div class="sec"><div class="sechead"><span class="secno">{secno()}</span>'
                 '<h3>Textová DNA — jak je sdělení postavené</h3></div>'
                 '<div class="lead">Hook, úhel, formát a nabídka + kostra příběhu — z reálného titulku, popisu a přepisu.</div>'
                 f'<div class="duo">{left}<div class="blk">{kost}{layer}</div></div></div>')

    # 03 reakce publika (Raw Diet)
    pub = card.get("publikum") or {}
    if pub.get("namitky") or pub.get("touhy") or pub.get("fraze"):
        zdroj = pub.get("zdroj_pocet")
        lead = ("Komentáře pod předlohou = publikum vlastními slovy — námitky, touhy a jazyk, "
                "který můžete převzít do vlastního textu."
                + (f" Z {fnum(zdroj)} komentářů, bez jmen autorů." if zdroj else " Bez jmen autorů."))
        fr = ""
        if pub.get("fraze"):
            pills = "".join(f'<span class="fpill">{e(x)}</span>' for x in pub["fraze"])
            fr = f'<div class="fraze"><span class="fl">Doslovné výrazy publika</span>{pills}</div>'
        tg = ""
        if pub.get("triggery"):
            tags = "".join(f'<span class="ttag">{e(x)}</span>' for x in pub["triggery"])
            tg = f'<div class="fraze"><span class="fl">Emoční spouštěče</span>{tags}</div>'
        row = ""
        if pub.get("namitky") or pub.get("touhy"):
            row = ('<div class="dietrow">'
                   + _panel("Námitky a obavy", pub.get("namitky"), "hsl(350 86% 62%)")
                   + _panel("Touhy a přání", pub.get("touhy"), "hsl(168 72% 50%)")
                   + "</div>")
        note = f'<div class="layer" style="margin-top:14px"><i>{e(pub["poznamka"])}</i></div>' if pub.get("poznamka") else ""
        p.append(f'<div class="sec"><div class="sechead"><span class="secno">{secno()}</span>'
                 f'<h3>Reakce publika — jak o tom lidé mluví</h3></div><div class="lead">{lead}</div>'
                 f'<div class="blk">{fr}{tg}{row}{note}</div></div>')
    elif pub.get("poznamka"):
        p.append(f'<div class="sec"><div class="sechead"><span class="secno">{secno()}</span>'
                 '<h3>Reakce publika — jak o tom lidé mluví</h3></div>'
                 f'<div class="layer"><b>▸ Vrstva KOMENTÁŘE</b> — <i>{e(pub["poznamka"])}</i></div></div>')

    # → klon
    klon = card.get("klon") or []
    if klon:
        rows = ""
        for k in klon:
            typ = str(k.get("typ") or "V")[:1].upper()
            bg, col = KLON_IC.get(typ, KLON_IC["V"])
            rows += (f'<div class="r"><span class="ic" style="background:{bg};color:{col}">{e(typ)}</span>'
                     f'<div><b>{e(k.get("nazev"))}:</b> {k.get("text") or ""}</div></div>')
        p.append('<div class="sec"><div class="sechead"><span class="secno">→</span>'
                 '<h3>Jak tuto DNA přenést do vlastní reklamy</h3></div>'
                 '<div class="lead">Recept pro tvorbu — vizuál, hook, úhel a formát přeložené na váš produkt. '
                 'Rovnou z něj vychází zadání pro tvůrce kreativy.</div>'
                 f'<div class="clone">{rows}</div></div>')

    p.append(f'<div class="foot">CliqSales · Ad Scout · Viral DNA Card™ · interní podklad pro tvorbu vlastní kreativy '
             f'(krok Dekóduj → Naklonuj) · cizí obsah pouze analyzujeme, nekopírujeme a nešíříme · '
             f'reálná data z veřejně dostupných zdrojů · komentáře bez jmen autorů · {e(m.get("sken"))}</div>')
    p.append(
        "</div><script>"
        "function fs(){var v=document.getElementById('dnavid');if(!v)return;"
        "if(v.requestFullscreen)v.requestFullscreen();"
        "else if(v.webkitRequestFullscreen)v.webkitRequestFullscreen();"
        "else if(v.webkitEnterFullscreen)v.webkitEnterFullscreen()}"
        "</script></body></html>")

    with open(out_path, "w") as f:
        f.write("".join(x for x in p if x))
    return out_path


if __name__ == "__main__":
    card = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else "viral-dna-card.html"
    print(render(card, out))
