#!/usr/bin/env python3
"""Renderer: Search Ad Board → HTML — 6 stohovaných sekcí, každá končí AKCÍ.

Osa = klíčové slovo. Účel: takticko-ekonomická vrstva „jak levně vyhrát placený
Google Search" — kdo bidduje · hotová copy k naklonování (Search DNA) · mezera
v klíčových slovech · souboj landingů · semafor ceny · akční plán na 30 dní.

🛑 HRANICE: Viral Ad Board = CO konkurence říká (úhly). Search Ad Board = ZA CO
platí, kolik to stojí a jak ji přebít. Žádný rozbor sdělení — jen mechanika.

BRZDA (proti zahlcení SMB): max 5 inzerentů · 3 reklamy ke klonování · 10 slov
mezery · 3 kroky plánu. Žádné CPC na 2 desetinná místa jako fakt — vždy „odhad",
semafor místo čísel. Po přečtení má majitel vědět: co spustit · co opravit na
webu · kolik na to dát.

Klientský výstup: VŠE česky, vykání. Sanitizace rizikově vázaná — reklamní registr
Google (Ads Transparency) + kanál Google jmenovat SMÍME (veřejný registr); metodu
sběru ne. Renderer bere contract `search-report.json` (kostra = searchboard_build.py,
sémantika = model). CSS základ sdílený s adboard (_adboard_assets.py).

v0.1 — dle documents/projects/ad-scout-handoff/search-ad-board-plan.md.
"""
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _adboard_assets import DEMO_CSS, SVG_DEFS  # noqa: E402

SEARCH_CSS = r"""
/* — Search Ad Board specifika (nad sdíleným DEMO_CSS) — */
.bidlist{display:flex;flex-direction:column}
.bidrow{display:grid;grid-template-columns:44px 56px minmax(220px,1.2fr) 1fr auto;gap:16px;align-items:center;
  padding:18px 22px;border-bottom:1px solid hsl(var(--border)/.5)}
.bidrow:last-child{border-bottom:none}
.bidrow.client{background:hsl(var(--brand)/.07);border-left:3px solid hsl(var(--brand))}
.bidrow .rk{font-family:var(--font-mono);font-size:20px;font-weight:700;color:hsl(var(--fg-dim))}
.bidrow .logo{width:44px;height:44px;border-radius:11px;background:hsl(var(--surface-2));display:grid;place-items:center;overflow:hidden}
.bidrow .logo img{width:26px;height:26px}
.bidrow .who .nm{font-size:16px;font-weight:700}
.bidrow .who .dm{font-family:var(--font-mono);font-size:11px;color:hsl(var(--fg-dim));margin-top:3px}
.bidrow .why1{font-size:13px;color:hsl(var(--fg-muted));line-height:1.5;max-width:560px}
.bidrow .facts{display:flex;flex-direction:column;gap:7px;align-items:flex-end;text-align:right}
.bidrow .facts .f{font-family:var(--font-mono);font-size:11px;color:hsl(var(--fg-muted));display:inline-flex;gap:6px;align-items:center}
.bidrow .facts .f b{color:hsl(var(--fg));font-size:12.5px}
.intbar{display:inline-flex;align-items:center;gap:8px;margin-top:8px}
.intbar .track{width:120px;height:6px;border-radius:3px;background:hsl(var(--surface-3));overflow:hidden}
.intbar .fill{height:100%;border-radius:3px;background:linear-gradient(90deg,hsl(var(--brand)),hsl(var(--mint)))}
.intbar .lb{font-family:var(--font-mono);font-size:10px;color:hsl(var(--fg-dim))}
.vbadge{display:inline-flex;align-items:center;gap:5px;font-family:var(--font-mono);font-size:9px;font-weight:700;
  letter-spacing:.07em;text-transform:uppercase;color:hsl(152 70% 62%);background:hsl(var(--success)/.13);
  border:1px solid hsl(var(--success)/.35);border-radius:6px;padding:3px 8px}
.cbadge{display:inline-flex;align-items:center;gap:5px;font-family:var(--font-mono);font-size:9px;font-weight:700;
  letter-spacing:.07em;text-transform:uppercase;color:hsl(var(--brand-light));background:hsl(var(--brand)/.13);
  border:1px solid hsl(var(--brand)/.35);border-radius:6px;padding:3px 8px}

/* akční lišta na konci každé sekce */
.actionbar{display:flex;gap:14px;align-items:flex-start;margin-top:18px;padding:17px 20px;border-radius:13px;
  border:1px solid hsl(var(--warning)/.35);background:linear-gradient(135deg,hsl(var(--warning)/.13),hsl(var(--warning)/.03))}
.actionbar .ic{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;flex:none;
  background:hsl(var(--warning)/.16);color:hsl(38 92% 62%)}
.actionbar .ic svg{width:17px;height:17px}
.actionbar .lb{font-family:var(--font-mono);font-size:9.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
  color:hsl(38 92% 62%);margin-bottom:5px}
.actionbar .tx{font-size:14.5px;font-weight:600;line-height:1.5}

/* mockup reklamy ve vyhledávání (světlá karta jako výsledek Googlu) */
.dnagrid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}
@media(max-width:1000px){.dnagrid{grid-template-columns:1fr}}
.gwrap{display:flex;flex-direction:column;gap:10px}
.gwrap .glabel{display:flex;align-items:center;gap:9px;font-family:var(--font-mono);font-size:10px;font-weight:700;
  letter-spacing:.13em;text-transform:uppercase;color:hsl(var(--fg-dim))}
.gwrap .glabel.klon{color:hsl(var(--brand-light))}
.gad{background:#fff;border-radius:13px;padding:18px 20px;box-shadow:0 14px 34px -18px rgba(0,0,0,.85)}
.gad .sp{font-size:11px;font-weight:700;color:#202124;margin-bottom:3px}
.gad .gurl{font-size:12px;color:#202124;display:flex;align-items:center;gap:6px;margin-bottom:5px}
.gad .gurl .fav{width:16px;height:16px;border-radius:50%;background:#f1f3f4;display:grid;place-items:center;overflow:hidden}
.gad .gurl .fav img{width:12px;height:12px}
.gad .gurl .du{color:#4d5156}
.gad .gh{font-size:17.5px;line-height:1.3;color:#1a0dab;font-weight:400;margin-bottom:5px}
.gad .gd{font-size:13px;line-height:1.5;color:#4d5156}
.gad .gsl{display:flex;flex-wrap:wrap;gap:7px;margin-top:11px}
.gad .gsl span{font-size:12px;color:#1a0dab;border:1px solid #dadce0;border-radius:999px;padding:4px 12px}
.gad.klon{outline:2px solid hsl(var(--brand)/.65);outline-offset:2px}
.gad .gnote{margin-top:11px;padding-top:10px;border-top:1px solid #ebedef;font-size:11.5px;color:#5f6368;font-style:italic}

/* tabulka mezery v klíčových slovech */
.kwtable{width:100%;border-collapse:collapse}
.kwtable th{font-family:var(--font-mono);font-size:9.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:hsl(var(--fg-dim));text-align:left;padding:13px 18px;border-bottom:1px solid hsl(var(--border)/.7)}
.kwtable td{padding:14px 18px;border-bottom:1px solid hsl(var(--border)/.45);font-size:13.5px;vertical-align:middle}
.kwtable tr:last-child td{border-bottom:none}
.kwtable .kw{font-family:var(--font-mono);font-size:13.5px;font-weight:600;color:hsl(var(--fg))}
.kwtable .num{font-family:var(--font-mono);color:hsl(var(--fg-muted))}
.kwtable .poz{font-size:12px;color:hsl(var(--fg-muted));line-height:1.45;max-width:380px}
.dot{display:inline-flex;align-items:center;gap:7px;font-family:var(--font-mono);font-size:12px;font-weight:700}
.dot::before{content:"";width:10px;height:10px;border-radius:50%;background:var(--dc,hsl(var(--success)))}
.dot.d0::before,.dot.d1::before,.dot.d2::before{background:hsl(152 65% 50%)}
.dot.d3::before,.dot.d4::before{background:hsl(38 92% 55%)}
.zam{display:inline-block;font-family:var(--font-mono);font-size:9.5px;color:hsl(var(--brand-light));
  background:hsl(var(--brand)/.11);border:1px solid hsl(var(--brand)/.25);border-radius:6px;padding:3px 8px}

/* souboj landingů */
.landtable{width:100%;border-collapse:collapse}
.landtable th{font-family:var(--font-mono);font-size:9.5px;font-weight:700;letter-spacing:.11em;text-transform:uppercase;
  color:hsl(var(--fg-dim));text-align:left;padding:13px 16px;border-bottom:1px solid hsl(var(--border)/.7)}
.landtable td{padding:15px 16px;border-bottom:1px solid hsl(var(--border)/.45);font-size:13px;line-height:1.5;vertical-align:top}
.landtable tr:last-child td{border-bottom:none}
.landtable .who{font-weight:700;font-size:13.5px;white-space:nowrap}
.landtable .who .dm{display:block;font-family:var(--font-mono);font-size:10px;color:hsl(var(--fg-dim));font-weight:400;margin-top:3px}
.landtable td.miss{color:hsl(38 92% 66%);font-weight:600;background:hsl(var(--warning)/.06)}
.yn{font-family:var(--font-mono);font-size:11.5px;font-weight:700}
.yn.ano{color:hsl(152 70% 60%)}.yn.ne{color:hsl(350 86% 68%)}
.pointa{display:flex;gap:13px;align-items:flex-start;padding:16px 20px;border-top:1px solid hsl(var(--border)/.5);
  font-size:14px;line-height:1.55}
.pointa b{color:hsl(var(--brand-light))}
.pointa .ic{width:30px;height:30px;border-radius:9px;background:hsl(var(--brand)/.13);color:hsl(var(--brand-light));
  display:grid;place-items:center;flex:none}
.pointa .ic svg{width:15px;height:15px}

/* semafor ceny */
.sema{display:flex;flex-direction:column}
.semarow{display:grid;grid-template-columns:230px 1fr;gap:18px;padding:19px 22px;border-bottom:1px solid hsl(var(--border)/.5);align-items:start}
.semarow:last-child{border-bottom:none}
@media(max-width:800px){.semarow{grid-template-columns:1fr}}
.semarow .head{display:flex;flex-direction:column;gap:5px}
.semarow .head .t{display:inline-flex;align-items:center;gap:9px;font-size:15px;font-weight:700}
.semarow .head .t::before{content:"";width:12px;height:12px;border-radius:50%;background:var(--sc);box-shadow:0 0 12px var(--sc)}
.semarow .head .s{font-size:11.5px;color:hsl(var(--fg-dim));line-height:1.45}
.semarow .kws{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.semarow .kws .k{font-family:var(--font-mono);font-size:12px;font-weight:600;border-radius:999px;padding:6px 14px;
  border:1px solid;color:hsl(var(--fg-muted))}
.semarow.grn .kws .k{color:hsl(152 70% 62%);border-color:hsl(var(--success)/.35);background:hsl(var(--success)/.08)}
.semarow.org .kws .k{color:hsl(38 92% 64%);border-color:hsl(var(--warning)/.32);background:hsl(var(--warning)/.07)}
.semarow.red .kws .k{color:hsl(350 86% 70%);border-color:hsl(var(--coral)/.32);background:hsl(var(--coral)/.07)}
.semarow .kws .none{font-size:12px;color:hsl(var(--fg-dim));font-style:italic}
.budgetbox{display:flex;gap:14px;align-items:center;margin:0 22px 20px;padding:16px 20px;border-radius:12px;
  border:1px solid hsl(var(--success)/.3);background:linear-gradient(135deg,hsl(var(--success)/.11),hsl(var(--success)/.02))}
.budgetbox .ic{width:34px;height:34px;border-radius:10px;background:hsl(var(--success)/.15);color:hsl(152 70% 58%);display:grid;place-items:center;flex:none}
.budgetbox .ic svg{width:17px;height:17px}
.budgetbox .tx{font-size:14.5px;line-height:1.5}
.budgetbox .tx b{color:hsl(152 70% 62%)}
.benchnote{margin:0 22px 18px;font-size:12px;color:hsl(var(--fg-dim));font-style:italic;line-height:1.5}

/* chips dotazů u bidderů */
.bq{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.bq span{font-family:var(--font-mono);font-size:10px;color:hsl(var(--fg-muted));background:hsl(var(--surface-2));border:1px solid hsl(var(--border));border-radius:6px;padding:2px 8px}

/* kreativa z registru uvnitř mockupu reklamy */
.gadimg{margin-top:12px}
.gadimg img{max-width:100%;max-height:180px;object-fit:contain;display:block;border:1px solid #ebedef;border-radius:9px;cursor:zoom-in}
.gadimg .cap{font-size:10.5px;color:#5f6368;margin-top:5px}

/* landing karty — screenshot + plný rozbor + proklik */
.lpgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;padding:20px 22px 8px}
@media(max-width:1000px){.lpgrid{grid-template-columns:1fr}}
.lpcard{border:1px solid hsl(var(--border)/.85);border-radius:14px;overflow:hidden;background:linear-gradient(180deg,hsl(var(--surface-1)),hsl(var(--bg)/.4));display:flex;flex-direction:column}
.lpcard .im{height:380px;overflow:hidden;background:hsl(var(--surface-2)/.5);cursor:zoom-in;position:relative}
.lpcard .im img{width:100%;object-fit:cover;object-position:top}
.lpcard .im::after{content:"";position:absolute;left:0;right:0;bottom:0;height:56px;background:linear-gradient(0deg,hsl(var(--surface-1)),transparent)}
.lpcard .im .b404{position:absolute;top:12px;right:12px;z-index:2;font-family:var(--font-mono);font-size:10px;font-weight:700;color:#fff;background:hsl(350 86% 55%);border-radius:6px;padding:4px 10px}
.lpcard .im .zoomhint{position:absolute;bottom:10px;right:12px;z-index:2;font-family:var(--font-mono);font-size:9.5px;color:hsl(var(--fg-muted))}
.lpcard .im .nofoto{display:grid;place-items:center;height:100%;color:hsl(var(--fg-dim));font-size:12.5px;padding:20px;text-align:center;line-height:1.6}
.lphead{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;padding:14px 16px 4px}
.lphead b{font-size:15px}
.lphead .dm{display:block;font-family:var(--font-mono);font-size:10.5px;color:hsl(var(--fg-dim));margin-top:3px}
.lplink{flex:none;display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;color:hsl(var(--brand-light));text-decoration:none;border:1px solid hsl(var(--brand)/.35);background:hsl(var(--brand)/.08);border-radius:999px;padding:6px 12px;white-space:nowrap}
.lplink:hover{border-color:hsl(var(--brand)/.6)}
.lbody{padding:10px 16px 6px;display:flex;flex-direction:column;gap:13px}
.lbsec .lbl{font-family:var(--font-mono);font-size:9.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:7px}
.lbsec ul{list-style:none;display:flex;flex-direction:column;gap:6px}
.lbsec li{position:relative;padding-left:16px;font-size:12.5px;line-height:1.5;color:hsl(var(--fg-muted))}
.lbsec li::before{content:"";position:absolute;left:0;top:7px;width:6px;height:6px;border-radius:50%}
.lbsec li b{color:hsl(var(--fg))}
.lbsec.s-strong .lbl{color:hsl(152 70% 60%)}.lbsec.s-strong li::before{background:hsl(152 70% 55%)}
.lbsec.s-weak .lbl{color:hsl(38 92% 62%)}.lbsec.s-weak li::before{background:hsl(38 92% 56%)}
.lbsec.s-insp .lbl{color:hsl(178 85% 66%)}.lbsec.s-insp li::before{background:hsl(178 85% 60%)}
.lmiss{margin:10px 14px 14px;padding:11px 13px;border-radius:10px;border:1px solid hsl(var(--warning)/.35);background:hsl(var(--warning)/.07);font-size:12.5px;line-height:1.55;color:hsl(38 92% 70%)}
.lmiss b{color:hsl(38 92% 62%);font-family:var(--font-mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;display:block;margin-bottom:4px}
.lbuild{margin:8px 22px 16px;padding:16px 20px;border-radius:13px;border:1px solid hsl(var(--success)/.35);background:linear-gradient(135deg,hsl(var(--success)/.1),hsl(var(--success)/.02))}
.lbuild .lbt{font-size:14px;font-weight:700;color:hsl(152 70% 62%);margin-bottom:10px}
.lbuild ul{list-style:none;display:grid;grid-template-columns:1fr 1fr;gap:8px 22px}
@media(max-width:900px){.lbuild ul{grid-template-columns:1fr}}
.lbuild li{position:relative;padding-left:22px;font-size:13px;line-height:1.55;color:hsl(var(--fg-muted))}
.lbuild li::before{content:"✓";position:absolute;left:0;color:hsl(152 70% 60%);font-weight:700}

/* verdikt — syntéza všech zdrojů */
.verdict{display:flex;gap:15px;align-items:flex-start;margin:2px 0 8px;padding:19px 22px;border-radius:14px;
  border:1px solid hsl(var(--mint,178 85% 60%)/.35);background:linear-gradient(135deg,hsl(178 85% 60%/.09),hsl(178 85% 60%/.02))}
.verdict .ic{width:36px;height:36px;border-radius:11px;background:hsl(178 85% 60%/.14);color:hsl(178 85% 70%);display:grid;place-items:center;flex:none}
.verdict .ic svg{width:18px;height:18px}
.verdict .lb{font-family:var(--font-mono);font-size:9.5px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:hsl(178 85% 70%);margin-bottom:6px}
.verdict .tx{font-size:14.5px;line-height:1.6}
.verdict .tx b{color:hsl(var(--fg))}

/* popup na zvětšení obrázku */
.vpop{position:fixed;inset:0;z-index:60;background:rgba(0,0,0,.84);display:none;place-items:center;padding:4vh 4vw}
.vpop.on{display:grid}
.vpop img{max-height:88vh;max-width:92vw;border-radius:12px;background:#fff}
.vpop .x{position:fixed;top:16px;right:24px;font-size:34px;line-height:1;color:#fff;cursor:pointer}

/* semafor — řádek obsahu (informační dotazy) */
.semarow.blu .kws .k{color:hsl(205 100% 72%);border-color:hsl(var(--brand)/.32);background:hsl(var(--brand)/.07)}

/* námět na advertorial */
.advcard{padding:32px 36px}
.advhead{display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap;margin-bottom:10px}
.advtype{flex:none;font-family:var(--font-mono);font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:hsl(var(--brand-light));background:hsl(var(--brand)/.12);border:1px solid hsl(var(--brand)/.35);border-radius:7px;padding:5px 11px;margin-top:5px}
.advtitle{font-size:21px;font-weight:800;letter-spacing:-.01em;line-height:1.3;flex:1;min-width:280px}
.advwhy{font-size:13px;color:hsl(var(--fg-muted));line-height:1.6;margin:8px 0 28px;max-width:860px}
.advbeats{display:grid;grid-template-columns:1fr 1fr;gap:0 64px;margin-bottom:26px}
@media(max-width:1000px){.advbeats{grid-template-columns:1fr}}
.advcol{display:flex;flex-direction:column}
.advbeat{display:flex;gap:19px;position:relative;padding-bottom:30px;font-size:13.5px;line-height:1.7;color:hsl(var(--fg-muted))}
.advbeat:last-child{padding-bottom:0}
.advbeat::before{content:"";position:absolute;left:16px;top:34px;bottom:-2px;width:2px;background:linear-gradient(180deg,hsl(var(--brand)/.45),hsl(var(--brand)/.12))}
.advbeat:last-child::before{display:none}
.advbeat .n{flex:none;width:33px;height:33px;border-radius:10px;border:1.5px solid var(--bc,hsl(var(--brand)));color:var(--bc,hsl(var(--brand-light)));background:hsl(var(--bg));box-shadow:0 0 14px -4px var(--bc,transparent);font-family:var(--font-mono);font-size:13px;font-weight:700;display:grid;place-items:center;position:relative;z-index:1}
.advbeat > div{padding-top:6px}
.advbeat b{color:hsl(var(--fg))}
.advads{padding:20px 0 6px;border-top:1px solid hsl(var(--border)/.5)}
.advadhead{font-family:var(--font-mono);font-size:9.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:hsl(var(--fg-dim));margin-bottom:14px}
.advadgrid{display:grid;grid-template-columns:1fr 1fr;gap:22px}
@media(max-width:1000px){.advadgrid{grid-template-columns:1fr}}
.advadwrap{display:flex;flex-direction:column;gap:9px}
.advadlbl{font-family:var(--font-mono);font-size:9px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:hsl(var(--brand-light))}
.advmeta{display:flex;flex-wrap:wrap;gap:34px;padding:22px 0 18px;border-top:1px solid hsl(var(--border)/.5)}
.advmeta .m{min-width:220px;flex:1}
.advmeta .ml{font-family:var(--font-mono);font-size:9.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:hsl(var(--fg-dim));margin-bottom:10px}
.advmeta .kws{display:flex;flex-wrap:wrap;gap:6px}
.advmeta .kws span{font-family:var(--font-mono);font-size:11px;color:hsl(152 70% 62%);background:hsl(var(--success)/.09);border:1px solid hsl(var(--success)/.3);border-radius:999px;padding:3px 10px}
.advmeta .mv{font-size:12.5px;color:hsl(var(--fg-muted));line-height:1.5}
.advfun{font-size:12px;color:hsl(var(--fg-dim));font-style:italic;line-height:1.6;margin-top:8px}
.advbtn{display:inline-flex;align-items:center;gap:9px;margin-top:20px;padding:12px 20px;border-radius:11px;border:1px solid hsl(var(--brand)/.5);background:hsl(var(--brand)/.13);color:hsl(var(--brand-light));font-size:13.5px;font-weight:700;cursor:pointer}
.advbtn:hover{background:hsl(var(--brand)/.2)}
.advnote{font-size:11.5px;color:hsl(var(--fg-dim));margin-top:7px}
.advhoff{position:absolute;left:-9999px;top:0;height:1px;width:1px;opacity:0}

/* akční plán — 3 kroky */
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
@media(max-width:1000px){.steps{grid-template-columns:1fr}}
.step{position:relative;border-radius:var(--radius);padding:22px;border:1px solid hsl(var(--border)/.85);
  background:linear-gradient(180deg,hsl(var(--surface-1)),hsl(var(--bg)/.4));overflow:hidden}
.step::after{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:linear-gradient(90deg,transparent,hsl(var(--brand)),transparent);opacity:.8}
.step .n{font-family:var(--font-mono);font-size:30px;font-weight:700;color:hsl(var(--brand-light));line-height:1;margin-bottom:12px}
.step .t{font-size:15.5px;font-weight:700;margin-bottom:9px;line-height:1.35}
.step .b{font-size:13px;color:hsl(var(--fg-muted));line-height:1.6}
.step .b b{color:hsl(var(--fg))}
"""


def e(x):
    return html.escape(str(x if x is not None else ""))


def fnum(n):
    try:
        return f"{int(n):,}".replace(",", " ")
    except Exception:
        return e(n)


def _fav(dom):
    return f"https://www.google.com/s2/favicons?domain={e(dom)}&sz=64" if dom else None


def _stat(lbl, val, delta, acc, ic):
    accf = acc if acc.startswith("var(") else f"hsl({acc})"
    accbg = "hsl(var(--brand)/.12)" if acc.startswith("var(") else f"hsl({acc}/.12)"
    return (f'<div class="stat" style="--accent:{accf};--accent-bg:{accbg}"><div class="top"><span class="lbl">{e(lbl)}</span>'
            f'<span class="ic"><svg fill="currentColor"><use href="#{ic}"/></svg></span></div>'
            f'<div class="val">{val}</div><div class="delta">{e(delta)}</div></div>')


def _sectionhead(no, h2, lead):
    return (f'<div class="sectionhead"><div class="shrow"><span class="secno">{no:02d}</span>'
            f'<h2>{e(h2)}</h2></div><p>{e(lead)}</p></div>')


def _action(text):
    if not text:
        return ""
    return ('<div class="actionbar"><span class="ic"><svg fill="currentColor"><use href="#i-bolt"/></svg></span>'
            f'<div><div class="lb">Co udělat</div><div class="tx">{e(text)}</div></div></div>')


def _plural(n, one, few, many):
    n = int(n or 0)
    return one if n == 1 else (few if 2 <= n <= 4 else many)


# ---- 01 bidders -------------------------------------------------------------

def _bidders(rep):
    bs = rep.get("bidders") or []
    if not bs:
        return "", ""
    total_q = max((b.get("intenzita") or 0 for b in bs), default=1)
    total_q = max(total_q, rep.get("pokryti", {}).get("dotazu") or 1)
    rows = ""
    for i, b in enumerate(bs, 1):
        it = b.get("intenzita") or 0
        reg = b.get("registr") or {}
        badges = ""
        if b.get("provereno"):
            badges += '<span class="vbadge">✓ prověřeno trhem</span>'
        if b.get("is_client"):
            badges += '<span class="cbadge">vy</span>'
        why = b.get("proc_nebezpecny") or ""
        # počet dotazů = SJEDNOCENÍ všech snímků (blok se střídá) — žádný denominátor z jednoho běhu
        n_q = len(b.get("dotazy") or []) or it
        facts = (f'<span class="f">nejlepší pozice <b>#{e(b.get("nejlepsi_pozice") or "–")}</b></span>'
                 f'<span class="f">zachycen na <b>{n_q} {_plural(n_q, "dotazu", "dotazech", "dotazech")}</b></span>')
        if reg.get("nejstarsi_dni"):
            facts += f'<span class="f">nejstarší reklama <b>{fnum(reg["nejstarsi_dni"])} dní</b></span>'
        if reg.get("reklam"):
            nr = reg["reklam"]
            pre = "~" if reg.get("odhad") else ""
            facts += (f'<span class="f">v registru <b>{pre}{fnum(nr)} '
                      f'{_plural(nr, "reklama", "reklamy", "reklam")}</b></span>')
        # na kterých dotazech se objevil (chips místo abstraktní „intenzity")
        qs = "".join(f"<span>{e(q)}</span>" for q in (b.get("dotazy") or [])[:4])
        qs_h = f'<div class="bq">{qs}</div>' if qs else ""
        logo = _fav(b.get("domain"))
        logo_img = f'<img src="{e(logo)}" alt="">' if logo else ""
        rows += (f'<div class="bidrow{" client" if b.get("is_client") else ""}">'
                 f'<span class="rk">{i}</span>'
                 f'<span class="logo">{logo_img}</span>'
                 f'<div class="who"><div class="nm">{e(b.get("nazev"))} {badges}</div>'
                 f'<div class="dm">{e(b.get("domain"))}</div>{qs_h}</div>'
                 f'<div class="why1">{e(why)}</div>'
                 f'<div class="facts">{facts}</div></div>')
    card = f'<div class="card"><div class="bidlist">{rows}</div></div>'
    top3 = ", ".join(b.get("nazev") or b.get("domain") or "" for b in bs[:3] if not b.get("is_client"))
    default_act = (f"Tito {_plural(min(3, len(bs)), 'inzerent vám bere', 'inzerenti vám berou', 'inzerenti vám berou')} "
                   f"poptávky: {top3}. Sledujte je — zbytek můžete ignorovat.")
    return card, default_act


# ---- 02 Search DNA (klonování) ----------------------------------------------

def _gad(inz, dom, head, desc, sitelinks, note=None, klon=False):
    fav = _fav(dom)
    fav_img = f'<img src="{e(fav)}" alt="">' if fav else ""
    sl = "".join(f"<span>{e(s)}</span>" for s in (sitelinks or [])[:6])
    sl = f'<div class="gsl">{sl}</div>' if sl else ""
    note_h = f'<div class="gnote">{e(note)}</div>' if note else ""
    desc_h = f'<div class="gd">{e(desc)}</div>' if desc else ""
    return (f'<div class="gad{" klon" if klon else ""}">'
            f'<div class="sp">Sponzorováno</div>'
            f'<div class="gurl"><span class="fav">{fav_img}</span>'
            f'<span class="du">{e(dom or "")}</span></div>'
            f'<div class="gh">{e(head or "")}</div>'
            f'{desc_h}{sl}{note_h}</div>')


def _clones(rep):
    items = [c for c in (rep.get("cloneable_ads") or []) if (c.get("vzor") or {}).get("head")]
    if not items:
        return "", ""
    out = ""
    for c in items:
        v = c.get("vzor") or {}
        k = c.get("klon") or {}
        # dni = stáří nejstarší reklamy INZERENTA v registru (důkaz vytrvalosti),
        # ne téhle konkrétní reklamy ze SERPu — popisek to musí říkat poctivě
        vdays = f' · inzeruje nepřetržitě {fnum(v["dni"])} dní' if v.get("dni") else ""
        vbadge = " · ✓ prověřeno trhem" if v.get("provereno") else ""
        vlabel = f'VZOR — {e(v.get("inzerent") or v.get("domain"))}{vdays}{vbadge}'
        klabel = "VÁŠ KLON — připraveno k nasazení"
        # vzor = VŽDY jednotný mockup; text z živého SERPu, nebo přepis reálné kreativy
        # z registru (model — vision); poznámka pod čarou říká zdroj / co konkurent neukazuje
        vg = _gad(v.get("inzerent"), v.get("domain"), v.get("head"), v.get("desc"),
                  v.get("sitelinks"), note=v.get("pozn"))
        klient = (rep.get("meta") or {}).get("klient") or {}
        if k.get("head"):  # klon doplněný modelem → pár vzor|klon
            kg = _gad(klient.get("nazev"), klient.get("domain"), k.get("head"), k.get("desc"),
                      k.get("sitelinks"), note=k.get("pozn"), klon=True)
            out += (f'<div class="dnagrid"><div class="gwrap"><span class="glabel">{vlabel}</span>{vg}</div>'
                    f'<div class="gwrap"><span class="glabel klon">{klabel}</span>{kg}</div></div>')
        else:  # bez klonu → jen vzor (žádný prázdný sloupec s labelem)
            out += (f'<div class="dnagrid"><div class="gwrap"><span class="glabel">{vlabel}</span>{vg}</div>'
                    f'<div class="gwrap"></div></div>')
    n = len([c for c in items if (c.get("klon") or {}).get("head")])
    act = (f"Zkopírujte {_plural(n, 'tuto reklamu', f'tyto {n} reklamy', f'těchto {n} reklam')} "
           f"do svého účtu Google Ads. Texty jsou hotové — jen zkontrolujte, že ceny a nabídka sedí.")
    return out, act


# ---- 03 mezera v klíčových slovech -------------------------------------------

_ZAMER_CZ = {"transactional": "nákupní", "commercial": "srovnávací", "informational": "informační",
             "navigational": "značkový"}


def _gap(rep):
    gap = rep.get("keyword_gap") or []
    if not gap:
        return "", ""
    rows = ""
    for g in gap:
        vol = f"~{fnum(g['volume'])}/měs" if g.get("volume") else '<span style="color:hsl(var(--fg-dim))">long-tail</span>'
        zam_raw = str(g.get("zamer") or "").lower()
        zam = f'<span class="zam">{e(_ZAMER_CZ.get(zam_raw, g["zamer"]))}</span>' if g.get("zamer") else ""
        cpc = f"~{round(float(g['cpc_odhad']))} Kč" if g.get("cpc_odhad") else "–"
        n = int(g.get("inzerentu") or 0)
        uroven = "volno" if n <= 2 else "střední"   # 0–2 zelená · 3–4 oranžová
        rows += (f'<tr><td class="kw">{e(g.get("kw"))}</td><td>{zam}</td>'
                 f'<td class="num">{vol}</td><td class="num">{e(cpc)}</td>'
                 f'<td><span class="dot d{min(n, 4)}">{n} {_plural(n, "inzerent", "inzerenti", "inzerentů")} · {uroven}</span></td>'
                 f'<td class="poz">{e(g.get("pozn") or "")}</td></tr>')
    n_volno = sum(1 for g in gap if int(g.get("inzerentu") or 0) <= 2)
    card = ('<div class="card"><table class="kwtable"><thead><tr>'
            '<th>Klíčové slovo</th><th>Záměr</th><th>Hledanost (odhad)</th><th>Cena za klik (odhad)</th>'
            '<th>Konkurence v placeném bloku</th><th>Proč to slovo</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>')
    act = (f"Začněte {n_volno} slovy s 0–2 inzerenty (🟢 volno) v přesné shodě — kliky za zlomek ceny obecných slov. "
           "Slova se 3–4 inzerenty (🟡 střední) přidejte hned potom, pořád jsou levnější než hlava trhu.")
    return card, act


# ---- 04 souboj landingů -------------------------------------------------------

def _yn(v):
    if v is None or v == "":
        return "–"
    s = str(v).strip().lower()
    if s in ("ano", "true", "yes", "1"):
        return '<span class="yn ano">ANO</span>'
    if s in ("ne", "false", "no", "0"):
        return '<span class="yn ne">NE</span>'
    return e(v)


def _lbullets(items, label, cls):
    if not items:
        return ""
    # položka smí být string (odrážka) nebo {co} — pro zpětnou kompatibilitu s daty
    lis = "".join(f"<li>{it.get('co') if isinstance(it, dict) else it}</li>" for it in items)
    return f'<div class="lbsec {cls}"><div class="lbl">{label}</div><ul>{lis}</ul></div>'


def _landing(rep):
    lg = [x for x in (rep.get("landing_gaps") or [])
          if x.get("silne") or x.get("slabe") or x.get("chybi")]
    if not lg:
        return "", ""
    # karta per landing: velký screenshot (klik = celá stránka) + proklik + strukturovaný rozbor
    # (✓ Silné · ⚠ Slabé → doplňte · → Čím se inspirovat) — nejsilnější sekce boardu
    cards = ""
    for x in lg:
        sc = x.get("screenshot")
        b404 = ('<span class="b404">reklama → 404 / vyhledávání</span>'
                if "404" in (str(x.get("chybi") or "") + " ".join(x.get("slabe") or [])) else "")
        if sc:
            im = (f'<div class="im" onclick="openImg(\'{e(sc)}\')"><img src="{e(sc)}" loading="lazy" alt="">{b404}'
                  '<span class="zoomhint">klik = celá stránka</span></div>')
        else:
            im = (f'<div class="im"><span class="nofoto">náhled nedostupný — stránka blokuje roboty;<br>'
                  f'hodnoceno z textu reklamy</span>{b404}</div>')
        link = (f'<a class="lplink" href="{e(x["url_full"])}" target="_blank" rel="noopener">Otevřít stránku ↗</a>'
                if x.get("url_full") else "")
        body = (_lbullets(x.get("silne"), "✓ Silné", "s-strong")
                + _lbullets(x.get("slabe"), "⚠ Slabé", "s-weak")
                + _lbullets(x.get("vas_tah") or x.get("inspirace"), "→ Akční kroky pro nás", "s-insp"))
        if not body:  # fallback na starý plochý formát
            body = f'<div class="lmiss"><b>Co mu chybí</b>{e(x.get("chybi") or "–")}</div>'
        cards += (f'<div class="lpcard">{im}<div class="lphead"><div><b>{e(x.get("nazev") or x.get("domain"))}</b>'
                  f'<span class="dm">{e(x.get("url") or x.get("domain") or "")}</span></div>{link}</div>'
                  f'<div class="lbody">{body}</div></div>')
    # checklist „co postavit vy" — z děr konkurence rovnou stavební plán (plní model)
    stavba = ""
    if rep.get("landing_stavba"):
        lis = "".join(f"<li>{e(s)}</li>" for s in rep["landing_stavba"])
        stavba = (f'<div class="lbuild"><div class="lbt">Vaše stránka — kterou nemá nikdo z konkurence</div>'
                  f'<ul>{lis}</ul></div>')
    pointa = rep.get("landing_pointa")
    pointa_h = (f'<div class="pointa"><span class="ic"><svg fill="currentColor"><use href="#i-tgt"/></svg></span>'
                f'<div>{pointa}</div></div>') if pointa else ""
    card = f'<div class="card"><div class="lpgrid">{cards}</div>{stavba}{pointa_h}</div>'
    act = ("Doplňte na svou stránku to, co konkurenci chybí — a uveďte cenu. "
           "Kdo cenu skrývá, ztrácí kliknutí lidí připravených koupit.")
    return card, act


# ---- námět na advertorial (mezistupeň reklama → nabídka) ----------------------

def _advertorial(rep):
    """Hotový námět na advertorial dle principů skillu article-writer (typ prodejní
    článek): podtyp podle publika + kostra (beats) + kongruence s reklamou + cílová
    slova + kopírovatelné zadání pro AI Marketéra. Board mezeru NAJDE, article-writer
    stránku VYROBÍ — sekce je most mezi nimi."""
    a = rep.get("advertorial_namet") or {}
    if not (a.get("titulek") and a.get("osnova")):
        return "", ""
    _BC = ["hsl(205 100% 62%)", "hsl(350 86% 65%)", "hsl(221 92% 68%)",
           "hsl(38 92% 58%)", "hsl(168 75% 55%)"]

    def _beat(i, b):
        return (f'<div class="advbeat" style="--bc:{_BC[(i - 1) % len(_BC)]}">'
                f'<span class="n">{i}</span><div>{b}</div></div>')

    osn = a["osnova"]
    half = (len(osn) + 1) // 2
    col1 = "".join(_beat(i, b) for i, b in enumerate(osn[:half], 1))
    col2 = "".join(_beat(i, b) for i, b in enumerate(osn[half:], half + 1))
    beats = f'<div class="advcol">{col1}</div><div class="advcol">{col2}</div>'
    kws = "".join(f"<span>{e(k)}</span>" for k in (a.get("cilova_slova") or [])[:10])
    metas = ""
    if kws:
        metas += f'<div class="m"><div class="ml">Cílová slova (z mezery)</div><div class="kws">{kws}</div></div>'
    if a.get("kongruence"):
        metas += f'<div class="m"><div class="ml">Kongruence s reklamou</div><div class="mv">{e(a["kongruence"])}</div></div>'
    if a.get("cta"):
        metas += f'<div class="m"><div class="ml">Výzvy k akci</div><div class="mv">{e(a["cta"])}</div></div>'
    btn = ""
    if a.get("handoff"):
        btn = (f'<textarea class="advhoff" id="advhoff">{e(a["handoff"])}</textarea>'
               '<button class="advbtn" onclick="copyAdv(this)">'
               '<svg width="15" height="15" fill="currentColor"><use href="#i-cmt"/></svg>Zadat AI Marketérovi</button>'
               '<div class="advnote">Zkopíruje hotové zadání — vložte ho AI Marketérovi do chatu, článek napíše za vás.</div>')
    why = f'<div class="advwhy">{e(a.get("proc_podtyp") or "")}</div>' if a.get("proc_podtyp") else ""
    # 2 mockupy reklam, které na článek povedou (vstup funnelu: reklama → článek → nabídka)
    ads_h = ""
    reklamy = (a.get("reklamy") or [])[:2]
    if reklamy:
        gads = "".join(
            f'<div class="advadwrap"><span class="advadlbl">Reklama {i} → článek</span>'
            + _gad(None, r.get("domain"), r.get("head"), r.get("desc"), r.get("sitelinks")) + '</div>'
            for i, r in enumerate(reklamy, 1))
        ads_h = ('<div class="advads"><div class="advadhead">Reklamy, které na článek povedou</div>'
                 f'<div class="advadgrid">{gads}</div></div>')
    fun = ('<div class="advfun">Proč mezistupeň: reklama → prodejní článek → nabídka dává o 30–50 % víc poptávek '
           'na kliknutí a výrazně nižší cenu poptávky než proklik rovnou na nabídku.</div>')
    card = (f'<div class="card advcard"><div class="advhead">'
            f'<span class="advtype">{e(a.get("podtyp") or "prodejní článek")}</span>'
            f'<div class="advtitle">„{e(a["titulek"])}"</div></div>{why}'
            f'<div class="advbeats">{beats}</div>{ads_h}'
            f'<div class="advmeta">{metas}</div>{fun}{btn}</div>')
    act = "Nepište článek ručně — tlačítko výše zkopíruje hotové zadání pro AI Marketéra. Po publikaci na něj veďte zelená slova."
    return card, act


# ---- 05 semafor ceny ----------------------------------------------------------

def _sema(rep):
    bs = rep.get("budget_semafor") or {}
    z, o, r = bs.get("zelena") or [], bs.get("oranzova") or [], bs.get("cervena") or []
    obsah = bs.get("obsah") or []
    taken = {k.strip().lower() for k in o + r + obsah}
    z = [k for k in z if k.strip().lower() not in taken]  # ostatní kategorie přebíjí auto-zelenou
    if not (z or o or r or obsah):
        return "", ""

    def row(cls, color, title, sub, kws):
        chips = "".join(f'<span class="k">{e(k)}</span>' for k in kws[:12]) or '<span class="none">— žádná —</span>'
        return (f'<div class="semarow {cls}" style="--sc:{color}"><div class="head">'
                f'<span class="t">{e(title)}</span><span class="s">{e(sub)}</span></div>'
                f'<div class="kws">{chips}</div></div>')

    body = (row("grn", "hsl(152 65% 50%)", "Zelená — začněte tady (0–2 inzerenti)",
                "Nákupní záměr, skoro nikdo neinzeruje, nízká cena za klik. Prvních 90 dní jen tato.", z)
            + row("org", "hsl(38 92% 55%)", "Oranžová — střední konkurence (3–4 inzerenti)",
                  "Ještě se vyplatí, jen dráž než zelená. Přidejte hned po zelených, až prokážou poptávky.", o)
            + row("red", "hsl(350 86% 60%)", "Červená — velká konkurence (5+ inzerentů)",
                  "Nejdražší klik a plný blok — patří sem i hlavní slovo oboru. Se silnou nabídkou tu jít můžete, ale opatrně, ať nespálíte rozpočet.", r)
            + row("blu", "hsl(205 100% 62%)", "Obsah, ne reklamy",
                  "Informační dotazy (účinky, dávkování, obavy). Neplaťte za klik — natočte video / napište článek a sbírejte důvěru zdarma.", obsah))
    pr = bs.get("priklad") or {}
    budget = ""
    if pr.get("rozpocet_kc") and pr.get("kliku_odhad"):
        pozn = f" {pr['pozn']}" if pr.get("pozn") else ""
        budget = ('<div class="budgetbox"><span class="ic"><svg fill="currentColor"><use href="#i-bolt"/></svg></span>'
                  f'<div class="tx">S rozpočtem <b>{fnum(pr["rozpocet_kc"])} Kč/měs</b> získáte na zelených slovech '
                  f'odhadem <b>~{e(pr["kliku_odhad"])} kliknutí</b>.{e(pozn)} Vše jsou odhady — přesné ceny ukáže až první týden kampaně.</div></div>')
    bench = f'<div class="benchnote">{e(bs["benchmark_pozn"])}</div>' if bs.get("benchmark_pozn") else ""
    card = f'<div class="card"><div class="sema">{body}</div>{budget}{bench}</div>'
    act = ("Prvních 90 dní jeďte zelená slova, oranžová přidejte hned po nich. Na červená (velká konkurence, "
           "vč. hlavního slova) jděte jen se silnou nabídkou a malým denním stropem — ať nespálíte rozpočet.")
    return card, act


# ---- 06 akční plán -------------------------------------------------------------

def _plan(rep):
    plan = rep.get("action_plan") or []
    if not plan:
        return ""
    out = ""
    for i, s in enumerate(plan[:3], 1):
        if isinstance(s, str):
            title, body = f"Krok {i}", s
        else:
            title, body = s.get("title") or f"Krok {i}", s.get("body") or ""
        out += f'<div class="step"><div class="n">{i}</div><div class="t">{e(title)}</div><div class="b">{body}</div></div>'
    return f'<div class="steps">{out}</div>'


# ---- render -------------------------------------------------------------------

def render(rep, out_path):
    m = rep.get("meta") or {}
    pok = rep.get("pokryti") or {}
    akce = rep.get("akce") or {}
    tema = m.get("tema", "")
    trh = (m.get("trh") or "cz").upper()

    podtitulek = m.get("podtitulek") or (
        f'Kdo platí za vaše zákazníky ve vyhledávání na téma „{tema}" — jejich reklamy k převzetí, '
        'slova, kde nakoupíte kliknutí levně, a plán na prvních 30 dní.')

    p = ['<!doctype html><html lang="cs"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>Search Ad Board — „{e(tema)}"</title>'
         '<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800'
         '&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">'
         f'<style>{DEMO_CSS}{SEARCH_CSS}</style></head><body>{SVG_DEFS}<div class="wrap">']

    # hlavička
    p.append(
        f'<div class="phead"><div>'
        f'<h1>Search Ad Board <span class="theme">— „{e(tema)}"</span></h1>'
        f'<div class="meta"><span class="mchip">ad-scout</span><span>trh {e(trh)}</span> · '
        f'<span class="mono">{e(m.get("sken"))}</span> · '
        f'<span>z živého vyhledávání Google a veřejného registru reklam</span></div>'
        f'<p class="subtitle">{e(podtitulek)}</p></div>'
        f'<div class="right"><span class="pill ok">REÁLNÁ DATA</span></div></div>')

    # přehled — 4 staty
    n_gap = len(rep.get("keyword_gap") or [])
    p.append('<div class="stats">'
             + _stat("Inzerentů na vašich slovech", e(pok.get("inzerentu") or 0),
                     "firem platí za stejné zákazníky", "var(--brand)", "i-goo")
             + _stat("Nejdéle běžící reklama", f'{fnum(pok.get("nejdelsi_beh_dni") or 0)}<small> dní</small>',
                     "co dlouho běží, to vydělává — prověřeno trhem", "168 72% 48%", "i-clk")
             + _stat("Volných slov", e(n_gap),
                     "dotazy s 0–2 inzerenty = kliknutí za zlomek ceny", "152 65% 50%", "i-tgt")
             + _stat("Prozkoumaných dotazů", e((pok.get("dotazu") or 0) + (pok.get("probe_dotazu") or 0)),
                     "živý snímek placeného vyhledávání", "205 100% 62%", "i-eye")
             + '</div>')

    # verdikt — syntéza všech zdrojů dohromady (SERP × registr × metriky × landingy);
    # přesně tohle SEO nástroj neposkládá — plní MODEL
    if rep.get("verdikt"):
        p.append('<div class="verdict"><span class="ic"><svg fill="currentColor"><use href="#i-tgt"/></svg></span>'
                 f'<div><div class="lb">Verdikt — co z toho všeho plyne</div><div class="tx">{rep["verdikt"]}</div></div></div>')

    _n = [0]

    def secno():
        _n[0] += 1
        return _n[0]

    # 01 kdo vám kupuje zákazníky
    card, dact = _bidders(rep)
    if card:
        p.append(_sectionhead(secno(), "Kdo vám kupuje zákazníky",
                              "Firmy, které platí za stejná vyhledávání jako vy — seřazené podle toho, na kolika vašich dotazech se objevují."))
        p.append(card)
        p.append(_action(akce.get("bidders") or dact))

    # 02 hotové reklamy k naklonování
    card, dact = _clones(rep)
    if card:
        p.append(_sectionhead(secno(), "Jejich hotové reklamy k naklonování",
                              "Reklamy, které konkurenci prokazatelně fungují (dlouhý běh = trh je ověřil). Vlevo vzor, vpravo verze připravená pro vás."))
        p.append(card)
        p.append(_action(akce.get("clone") or dact))

    # 03 mezera v klíčových slovech
    card, dact = _gap(rep)
    if card:
        p.append(_sectionhead(secno(), "Mezera v klíčových slovech — kde nakoupíte levně",
                              "Slova s nákupním záměrem a malou konkurencí. 🟢 0–2 inzerenti = volno · 🟡 3–4 = střední. "
                              "Ověřeno ve DVOU živých snímcích (blok se střídá), ne odhadem."))
        p.append(card)
        p.append(_action(akce.get("gap") or dact))

    # 04 souboj landingů
    card, dact = _landing(rep)
    if card:
        p.append(_sectionhead(secno(), "Souboj stránek: co slibují — a čím je přebijete",
                              "Kam konkurence posílá kliknutí a co tam slibuje — reálné snímky stránek, klik = celá stránka. "
                              "U každého vidíte, co dělá dobře, kde má slabinu a jaké kroky z toho vytěžíte pro sebe."))
        p.append(card)
        p.append(_action(akce.get("landing") or dact))

    # 05 námět na advertorial (most: board najde mezeru → article-writer napíše stránku)
    card, dact = _advertorial(rep)
    if card:
        p.append(_sectionhead(secno(), "Námět na advertorial — mezistupeň mezi reklamou a nákupem",
                              "Hotový návrh prodejního článku, na který povedete reklamy ze zelených slov. "
                              "Postavený na dírách konkurence z předchozích sekcí — stačí zadat AI Marketérovi."))
        p.append(card)
        p.append(_action(akce.get("advertorial") or dact))

    # 06 semafor ceny
    card, dact = _sema(rep)
    if card:
        p.append(_sectionhead(secno(), "Kolik to bude stát — semafor",
                              "Žádné tabulky cen na halíř. Tři barvy: kde nakupovat hned, kde počkat a kam zatím nesahat. Vše jsou odhady."))
        p.append(card)
        p.append(_action(akce.get("semafor") or dact))

    # 06 akční plán
    plan = _plan(rep)
    if plan:
        p.append(_sectionhead(secno(), "Akční plán na 30 dní",
                              "Tři kroky. Víc ne. Když je uděláte, víte za měsíc přesně, kolik vás stojí jedna poptávka z vyhledávání."))
        p.append(plan)

    p.append(f'<div class="pagefoot">CliqSales · Ad Scout · Search Ad Board · spuštěno klíčovým slovem · '
             f'reálná data z vyhledávání Google a veřejného registru reklam · '
             f'{e(pok.get("dotazu", 0))} dotazů + {e(pok.get("probe_dotazu", 0))} ověřovacích · {e(m.get("sken"))}</div>')
    p.append(
        '</div><div class="vpop" id="vpop" onclick="closeImg()"><span class="x">×</span>'
        '<img id="vpopi" alt=""></div>'
        "<script>"
        "function openImg(s){var p=document.getElementById('vpop');"
        "document.getElementById('vpopi').src=s;p.classList.add('on')}"
        "function closeImg(){var p=document.getElementById('vpop');"
        "p.classList.remove('on');document.getElementById('vpopi').removeAttribute('src')}"
        "document.addEventListener('keydown',function(e){if(e.key==='Escape')closeImg()});"
        "function copyAdv(btn){var t=document.getElementById('advhoff');if(!t)return;"
        "navigator.clipboard.writeText(t.value).then(function(){var o=btn.innerHTML;"
        "btn.innerHTML='✓ Zkopírováno — vložte AI Marketérovi';setTimeout(function(){btn.innerHTML=o},2500)})}"
        "</script></body></html>")

    with open(out_path, "w") as f:
        f.write("".join(x for x in p if x))
    return out_path


if __name__ == "__main__":
    rep = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else "search-ad-board.html"
    print(render(rep, out))
