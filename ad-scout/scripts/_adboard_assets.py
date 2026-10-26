# -*- coding: utf-8 -*-
# CSS + SVG ikony převzaté 1:1 z golden dema (ad-board-ai-agenti-cz.html).
DEMO_CSS = r""":root{
  --bg:224 86% 5%;--rail:225 66% 7%;--surface-1:226 36% 10.5%;--surface-2:228 31% 14%;--surface-3:230 28% 18.5%;
  --border:226 26% 17%;--border-soft:224 24% 27%;
  --fg:210 32% 97%;--fg-muted:220 14% 80%;--fg-dim:221 11% 62%;
  --brand:203 100% 49%;--brand-deep:212 100% 33%;--brand-light:205 100% 60%;--mint:178 85% 78%;
  --indigo:208 100% 55%;--indigo-deep:214 92% 40%;--success:152 60% 46%;--warning:37 92% 56%;--coral:350 86% 65%;
  --radius:16px;--radius-sm:11px;--font-sans:'Inter',system-ui,sans-serif;--font-mono:'JetBrains Mono',monospace;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--font-sans);background:hsl(var(--bg));color:hsl(var(--fg));-webkit-font-smoothing:antialiased;font-feature-settings:'cv11','ss01'}
body::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;background:
  radial-gradient(900px 600px at 18% -8%,hsl(var(--indigo)/.16),transparent 60%),
  radial-gradient(1100px 700px at 88% 4%,hsl(var(--brand)/.10),transparent 58%),
  radial-gradient(800px 800px at 60% 120%,hsl(var(--indigo)/.08),transparent 55%)}
.wrap{position:relative;z-index:1;max-width:1880px;margin:0 auto;padding:34px 42px 60px}
.mono{font-family:var(--font-mono)}

.phead{display:flex;align-items:flex-start;gap:16px;margin-bottom:24px}
.phead h1{font-size:36px;font-weight:800;letter-spacing:-.03em;line-height:1.05}
.phead h1 .theme{background:linear-gradient(90deg,#119CFF,#97F8F4);-webkit-background-clip:text;background-clip:text;color:transparent}
.phead .meta{display:flex;align-items:center;gap:10px;margin-top:11px;font-size:13.5px;color:hsl(var(--fg-muted));flex-wrap:wrap}
.phead .meta .mchip{font-family:var(--font-mono);background:hsl(var(--surface-1));border:1px solid hsl(var(--border));border-radius:7px;padding:3px 8px;color:hsl(var(--fg-muted));font-size:11px}
.phead .right{margin-left:auto}
.pill{display:inline-flex;align-items:center;gap:7px;height:30px;padding:0 13px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid hsl(var(--border));background:hsl(var(--surface-1));color:hsl(var(--fg-muted))}
.pill.ok{color:hsl(var(--success));border-color:hsl(var(--success)/.32);background:hsl(var(--success)/.09)}

.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:18px}
.stat{position:relative;border-radius:var(--radius);padding:18px;overflow:hidden;background:linear-gradient(180deg,hsl(var(--surface-1)),hsl(var(--bg)/.4));border:1px solid hsl(var(--border)/.85);box-shadow:0 1px 0 rgba(255,255,255,.04) inset,0 12px 30px -18px rgba(0,0,0,.8)}
.stat::after{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:linear-gradient(90deg,transparent,var(--accent,hsl(var(--brand))),transparent);opacity:.85}
.stat .top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.stat .lbl{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:hsl(210 22% 86%)}
.stat .ic{width:32px;height:32px;border-radius:9px;display:grid;place-items:center;background:var(--accent-bg,hsl(var(--brand)/.12));color:var(--accent,hsl(var(--brand)))}
.stat .ic svg{width:17px;height:17px}
.stat .val{font-size:34px;font-weight:700;letter-spacing:-.02em;font-family:var(--font-mono);line-height:1;color:var(--accent,hsl(var(--fg)))}
.stat .val small{font-size:16px;color:hsl(var(--fg-muted));font-weight:600}
.stat .delta{font-size:11.5px;color:hsl(var(--fg-muted));margin-top:9px}
.stat .delta b{color:hsl(var(--success));font-weight:600}

.card{border-radius:var(--radius);background:linear-gradient(180deg,hsl(var(--surface-1)),hsl(var(--bg)/.35));border:1px solid hsl(var(--border)/.85);box-shadow:0 1px 0 rgba(255,255,255,.04) inset,0 18px 40px -26px rgba(0,0,0,.9)}
.card .chead{display:flex;align-items:center;gap:10px;padding:16px 18px;border-bottom:1px solid hsl(var(--border)/.55)}
.card .chead h3{font-size:14px;font-weight:600;letter-spacing:-.01em}
.card .chead .sub{margin-left:auto;font-size:11px;font-family:var(--font-mono);color:hsl(var(--fg-muted));letter-spacing:.04em}

.gapbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:14px 18px}
.gap{display:inline-flex;align-items:center;gap:9px;height:31px;padding:0 14px;border-radius:999px;font-size:12px;font-weight:600}
.gap.red{color:hsl(350 90% 76%);border:1px solid hsl(var(--coral)/.28);background:linear-gradient(135deg,hsl(var(--coral)/.16),hsl(var(--coral)/.04))}
.gap.yel{color:hsl(38 92% 66%);border:1px solid hsl(var(--warning)/.28);background:linear-gradient(135deg,hsl(var(--warning)/.15),hsl(var(--warning)/.04))}
.gap.grn{color:hsl(152 70% 60%);border:1px solid hsl(var(--success)/.3);background:linear-gradient(135deg,hsl(var(--success)/.16),hsl(var(--success)/.05))}
.gap .n{font-family:var(--font-mono);font-size:10px;font-weight:700;background:hsl(var(--bg)/.55);border-radius:6px;padding:2px 7px}

.duo{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:stretch;margin-top:20px}
.duo>.card{display:flex;flex-direction:column;height:100%;border:1px solid hsl(220 26% 20%);background:hsl(226 32% 12.5%)}
.duo>.card>.chead{padding:26px 38px 26px 32px;border-bottom:1px solid hsl(213 30% 22%/.6)}
.duo .synth .bd{flex:1;padding:34px 76px 22px 34px}
.duo .synth .bd .row{position:relative;display:flex;gap:16px;margin-bottom:36px;font-size:13.5px}
.duo .synth .bd .row:last-child{margin-bottom:8px}
.duo .synth .bd .row:not(:last-child)::before{content:"";position:absolute;left:15px;top:36px;bottom:-36px;width:2px;background:linear-gradient(180deg,hsl(var(--brand)/.5),hsl(var(--border-soft)/.5));z-index:0}
.duo .synth .bd .row .ic{position:relative;z-index:1;width:32px;height:32px;border-radius:9px;display:grid;place-items:center;flex:none}
.duo .synth .bd .row .ic svg{width:17px;height:17px}
.duo .synth .bd .row div{line-height:1.62}
.duo .synth .bd .row b{color:hsl(var(--fg));font-weight:600}
.duo .synth .foot{padding:18px 34px;border-top:1px solid hsl(213 30% 22%/.5)}
.duo .synth .foot .note{font-family:var(--font-mono);font-size:10px;color:hsl(var(--fg-dim))}

.hookgrid{flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:12px 34px 18px}
.hk{position:relative;display:flex;gap:14px;padding:15px 0;border-bottom:1px solid hsl(var(--border)/.45)}
.hk:last-child{border-bottom:none}
.hk:not(:last-child)::before{content:"";position:absolute;left:14px;top:33px;bottom:-15px;width:2px;background:linear-gradient(180deg,hsl(var(--brand)/.5),hsl(var(--border-soft)/.5));z-index:0}
.hk .no{position:relative;z-index:1;font-family:var(--font-mono);font-size:11.5px;font-weight:700;border:1px solid;border-radius:8px;min-width:29px;height:29px;display:grid;place-items:center;flex:none;margin-top:2px;background:hsl(226 32% 12.5%) !important}
.hk .b{min-width:0}
.hk .t{font-size:14.5px;font-weight:700;line-height:1.35}
.hk .horig{font-size:10.5px;color:hsl(var(--fg-dim));font-style:italic;margin-top:3px}
.hk .pat{display:inline-block;font-family:var(--font-mono);font-size:9px;border:1px solid;border-radius:6px;padding:2px 8px;margin:7px 6px 0 0}
.hk .why2{font-size:12px;color:hsl(var(--fg-muted));margin-top:6px;line-height:1.5}
.hk .srcline{font-family:var(--font-mono);font-size:10px;color:hsl(var(--fg-muted));margin-top:6px}
.hk .srcline b{color:hsl(var(--fg-muted));font-weight:600}

.sectionhead{margin:66px 0 20px}
.sectionhead .shrow{display:flex;align-items:baseline;gap:14px}
.sectionhead .secno{font-family:var(--font-mono);font-size:42px;font-weight:700;color:hsl(var(--brand-light));line-height:1}
.sectionhead h2{font-size:30px;font-weight:800;letter-spacing:-.03em;line-height:1.05}
.sectionhead p{font-size:14.5px;color:hsl(var(--fg-muted));margin-top:10px;max-width:1000px}

.tabs{display:flex;gap:10px;margin:26px 0 20px;border-bottom:1px solid hsl(var(--border)/.7);padding-bottom:0}
.tab{display:inline-flex;align-items:center;gap:10px;font-family:var(--font-sans);font-size:15px;font-weight:700;padding:14px 22px;border:none;background:none;color:hsl(var(--fg-dim));cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-1px;transition:.15s}
.tab svg{width:18px;height:18px}
.tab .tc{font-family:var(--font-mono);font-size:12px;font-weight:700;background:hsl(var(--surface-2));color:hsl(var(--fg-muted));border-radius:7px;padding:2px 9px}
.tab:hover{color:hsl(var(--fg-muted))}
.tab.on{color:hsl(var(--fg));border-bottom-color:hsl(var(--brand))}
.tab.on .tc{background:hsl(var(--brand)/.18);color:hsl(var(--brand-light))}

.tabnote{font-size:13px;color:hsl(var(--fg-muted));margin:2px 0 16px;display:flex;align-items:center;gap:8px}
.netbar{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:20px}
.nf{display:inline-flex;align-items:center;gap:8px;font-size:12.5px;font-weight:600;padding:8px 14px;border-radius:999px;border:1px solid hsl(var(--border));background:hsl(var(--surface-1));color:hsl(var(--fg-muted));cursor:pointer;transition:.14s}
.nf svg{width:15px;height:15px}
.nf:hover{border-color:hsl(var(--border-soft));color:hsl(var(--fg))}
.nf.on{background:hsl(var(--brand)/.14);border-color:hsl(var(--brand)/.5);color:hsl(var(--brand-light))}
.nf.ghost{opacity:.42;cursor:not-allowed;color:hsl(var(--fg-dim))}
.nf.ghost em{font-style:normal;font-family:var(--font-mono);font-size:9px;letter-spacing:.08em;text-transform:uppercase;background:hsl(var(--surface-2));border-radius:5px;padding:1px 6px}

.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}
@media(max-width:1300px){.grid{grid-template-columns:repeat(4,1fr)}}
@media(max-width:1040px){.grid{grid-template-columns:repeat(3,1fr)}.stats{grid-template-columns:repeat(2,1fr)}.duo{grid-template-columns:1fr}}
@media(max-width:760px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:520px){.grid{grid-template-columns:1fr}.stats{grid-template-columns:1fr}}

.ocard{position:relative;border-radius:13px;overflow:hidden;border:1px solid hsl(215 40% 26%);display:flex;flex-direction:column;transition:.15s;cursor:pointer;text-decoration:none;color:inherit;
  background:radial-gradient(420px 300px at 0% 0%,hsl(210 90% 34%/.22),transparent 62%),linear-gradient(158deg,hsl(220 46% 19%),hsl(226 44% 11%) 55%,hsl(225 50% 8%));
  box-shadow:0 1px 0 rgba(255,255,255,.07) inset,0 20px 44px -22px rgba(0,0,0,.95)}
.ocard[data-net~="youtube"],.ocard[data-net~="tiktok"]{background:radial-gradient(420px 300px at 0% 0%,hsl(168 70% 34%/.2),transparent 62%),linear-gradient(158deg,hsl(210 40% 18%),hsl(224 42% 11%) 55%,hsl(225 50% 8%))}
.ocard::after{content:"";position:absolute;left:0;right:0;top:0;height:2px;z-index:4;opacity:.9;background:linear-gradient(90deg,transparent,hsl(var(--indigo)),transparent)}
.ocard[data-net~="youtube"]::after,.ocard[data-net~="tiktok"]::after{background:linear-gradient(90deg,transparent,hsl(168 80% 55%),transparent)}
.ocard:hover{transform:translateY(-3px);border-color:hsl(var(--brand)/.5);box-shadow:0 16px 40px -18px hsl(var(--brand)/.5)}
.thumb{position:relative;aspect-ratio:4/5;overflow:hidden;display:flex;align-items:center;justify-content:center;background:hsl(var(--surface-2))}
.thumb img.real,.thumb video.real{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}
.thumb video.real{background:#000;cursor:pointer}
.mbadge{position:absolute;top:8px;right:8px;z-index:3;display:inline-flex;align-items:center;gap:5px;font-family:var(--font-mono);font-size:9px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;background:hsl(var(--bg)/.82);color:hsl(var(--fg-muted));border-radius:5px;padding:3px 7px;backdrop-filter:blur(3px)}
.mbadge svg{width:10px;height:10px}
.mbadge.vid{background:hsl(var(--coral)/.92);color:#fff}
.playov{position:absolute;inset:0;z-index:2;display:grid;place-items:center;pointer-events:none}
.playov svg{width:48px;height:48px;fill:#fff;opacity:.94;filter:drop-shadow(0 4px 16px rgba(0,0,0,.7))}
.vpop{display:none;position:fixed;inset:0;z-index:100;background:rgba(1,7,26,.88);backdrop-filter:blur(6px);align-items:center;justify-content:center;padding:20px}
.vpop.on{display:flex}
.vpop-inner{position:relative;height:min(88vh,820px);aspect-ratio:9/16;max-width:94vw;border-radius:16px;overflow:hidden;background:#000;box-shadow:0 30px 90px -20px rgba(0,0,0,.95)}
.vpop-inner video{width:100%;height:100%;object-fit:contain;background:#000;display:block}
.vpop-inner.img{aspect-ratio:auto;height:auto;width:auto;max-height:none;max-width:none;background:transparent;box-shadow:none;overflow:visible}
.vpop-x{position:absolute;top:10px;right:10px;z-index:2;width:36px;height:36px;border-radius:50%;border:none;background:rgba(0,0,0,.55);color:#fff;font-size:19px;line-height:1;cursor:pointer;display:grid;place-items:center;backdrop-filter:blur(4px)}
.vpop-x:hover{background:rgba(0,0,0,.85)}
.thumb .shade{position:absolute;inset:0;z-index:1;background:linear-gradient(180deg,rgba(1,7,26,.62),transparent 36%,transparent 58%,rgba(1,7,26,.72))}
.thumb .pico{position:relative;z-index:1;opacity:.55}
.thumb .noimg{position:absolute;inset:0;z-index:1;display:grid;place-items:center;color:hsl(var(--fg-muted));background:radial-gradient(130% 120% at 50% -10%,hsl(var(--surface-3)),hsl(var(--surface-1)) 55%,hsl(var(--bg)))}
.thumb .noimg svg{opacity:.6;filter:drop-shadow(0 4px 14px rgba(0,0,0,.4))}
.score{position:absolute;top:8px;left:8px;z-index:2;display:inline-flex;align-items:center;gap:5px;font-family:var(--font-mono);font-size:11.5px;font-weight:700;color:#fff;border-radius:6px;padding:3px 9px;box-shadow:0 3px 12px rgba(0,0,0,.45)}
.score svg{margin-top:-1px}
.score.s-hot{background:linear-gradient(135deg,hsl(350 86% 58%),hsl(25 95% 53%))}
.score.s-warm{background:linear-gradient(135deg,hsl(37 92% 48%),hsl(25 95% 46%));color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.45)}
.score.s-cool{background:linear-gradient(135deg,hsl(var(--brand)),hsl(var(--indigo-deep)))}
.rank{position:absolute;bottom:8px;left:8px;z-index:2;font-family:var(--font-mono);font-size:9px;font-weight:700;background:hsl(var(--bg)/.8);backdrop-filter:blur(3px);color:hsl(var(--fg));border-radius:4px;padding:2px 7px}
.dur{position:absolute;bottom:8px;right:8px;z-index:2;font-family:var(--font-mono);font-size:8.5px;background:hsl(var(--bg)/.8);color:#fff;border-radius:4px;padding:2px 6px}
.geo{position:absolute;top:8px;right:8px;z-index:2;font-family:var(--font-mono);font-size:8.5px;font-weight:700;letter-spacing:.06em;background:hsl(38 92% 48%/.95);color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.45);border-radius:4px;padding:2px 7px}
.ocard .body{padding:14px 15px;display:flex;flex-direction:column;gap:9px;flex:1}
.ocard .nm{font-size:14.5px;font-weight:700;line-height:1.34;min-height:auto;color:hsl(var(--fg));transition:color .14s}
.ocard:hover .nm{color:hsl(var(--fg))}
.ocard .orig{font-size:11px;color:hsl(var(--fg-dim));font-style:italic;margin-top:-3px;line-height:1.35}
.pbs{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.pb{display:inline-flex;align-items:center;gap:6px;font-size:10.5px;font-weight:700;color:#fff;padding:4px 10px;border-radius:7px;box-shadow:0 3px 10px rgba(0,0,0,.3)}
.pb svg{width:12px;height:12px}
.pbs .who{font-size:11.5px;color:hsl(var(--fg-muted));font-weight:600}
.mline{display:flex;gap:12px;font-family:var(--font-mono);font-size:10px;flex-wrap:wrap}
.mline span{display:inline-flex;align-items:center;gap:5px}
.mline svg{width:12px;height:12px}
.chiprow{display:flex;gap:6px;flex-wrap:wrap}
.skill{font-family:var(--font-mono);font-size:9px;color:hsl(var(--brand-light));background:hsl(var(--brand)/.1);border:1px solid hsl(var(--brand)/.22);border-radius:6px;padding:3px 7px}
.skill.aw{color:hsl(var(--fg-muted));background:hsl(var(--surface-2));border-color:hsl(var(--border))}
.skill.free{color:hsl(var(--success));background:linear-gradient(135deg,hsl(var(--success)/.24),hsl(var(--success)/.07));border-color:hsl(var(--success)/.4)}
.why{list-style:none;padding:2px 0}
.why li{position:relative;padding-left:14px;margin:4px 0;font-size:11.5px;line-height:1.5;color:hsl(var(--fg-muted))}
.why li:before{content:"›";position:absolute;left:0;font-weight:800}
.why li:nth-child(1):before{color:hsl(203 100% 62%)}
.why li:nth-child(2):before{color:hsl(38 92% 60%)}
.why li:nth-child(3):before{color:hsl(168 75% 55%)}
.acts{display:flex;gap:6px;margin-top:auto;padding-top:10px;border-top:1px solid hsl(var(--border)/.55)}
.acts .alink{flex:1;display:flex;align-items:center;justify-content:center;gap:6px;font-size:11px;font-weight:600;padding:9px 4px;border-radius:8px;border:1px solid hsl(var(--border));background:hsl(var(--surface-2));color:hsl(var(--fg-muted));transition:.14s;text-decoration:none;cursor:pointer}
.ocard:hover .acts .alink{color:hsl(var(--brand-light));border-color:hsl(var(--brand)/.45);background:hsl(var(--brand)/.08)}
.pagefoot{margin-top:30px;font-family:var(--font-mono);font-size:10.5px;color:hsl(var(--fg-muted));letter-spacing:.03em}

.kicker{font-family:var(--font-mono);font-size:12px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:hsl(var(--brand-light));margin-bottom:9px;display:block}
.subtitle{font-size:15.5px;color:hsl(var(--fg-muted));margin-top:13px;max-width:940px;line-height:1.55}
.subhead{display:flex;align-items:center;gap:12px;margin:30px 0 16px;font-size:17px;font-weight:700;letter-spacing:-.01em}
.subhead .tag{font-family:var(--font-mono);font-size:10px;font-weight:600;color:hsl(var(--fg-dim));background:hsl(var(--surface-2));border:1px solid hsl(var(--border));border-radius:6px;padding:3px 8px;text-transform:uppercase;letter-spacing:.06em}
.subhead .cnt{margin-left:auto;font-family:var(--font-mono);font-size:12px;color:hsl(var(--fg-muted))}
/* dlouhý obsah = 16:9 landscape, ale 5 sloupců jako placené (dědí .grid) */
.gwide .thumb{aspect-ratio:16/9}
/* kolaps: zobraz prvních 10, zbytek za tlačítkem „Načíst dalších N" */
.grid.collapsed>.ocard:nth-child(n+11){display:none}
.ocard.nf-hide{display:none}
.loadmore{display:block;margin:24px auto 0;padding:13px 34px;border-radius:11px;border:none;background:linear-gradient(135deg,hsl(var(--brand)),hsl(178 85% 66%));color:#01071A;font-family:var(--font-sans);font-size:14px;font-weight:700;letter-spacing:.01em;cursor:pointer;transition:.15s;box-shadow:0 6px 22px -8px hsl(var(--brand)/.75)}
.loadmore:hover{filter:brightness(1.08);box-shadow:0 9px 28px -8px hsl(var(--brand)/.95);transform:translateY(-1px)}
/* sekce 03 — úhly ve vyhledávání (bohatší: úhel + počet + insight + příklady) */
.ublock{padding:20px 22px;border-bottom:1px solid hsl(var(--border)/.5)}
.ublock:last-child{border-bottom:none}
.ubhead{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:13px}
.ubhead .u{font-size:17px;font-weight:700;color:hsl(var(--brand-light))}
.ubhead .cnt{font-family:var(--font-mono);font-size:10.5px;font-weight:700;color:hsl(var(--fg-muted));background:hsl(var(--brand)/.12);border:1px solid hsl(var(--brand)/.25);border-radius:999px;padding:3px 10px}
.ubhead .ins{margin-left:auto;font-size:12.5px;color:hsl(var(--fg-muted));font-style:italic;max-width:60%}
.uex{display:flex;flex-direction:column;gap:9px}
.uexr{display:flex;align-items:baseline;gap:11px;font-size:13.5px}
.uexr::before{content:"›";color:hsl(var(--brand-light));font-weight:800;flex:none}
.uexr .q{color:hsl(var(--fg));font-style:italic;line-height:1.4}
.uexr .b{margin-left:auto;font-family:var(--font-mono);font-size:11px;color:hsl(var(--fg-dim));white-space:nowrap}
/* sekce 04 — jazyk zákazníka (vizuální: fráze jako pilulky + barevné panely) */
.fraze{display:flex;flex-wrap:wrap;gap:10px;padding:22px 24px 20px;border-bottom:1px solid hsl(var(--border)/.5)}
.fraze .fl,.trig .fl{font-family:var(--font-mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:hsl(var(--fg-dim));width:100%;margin-bottom:2px}
.trig{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:16px 24px;border-bottom:1px solid hsl(var(--border)/.5)}
.ttag{font-family:var(--font-mono);font-size:11px;font-weight:700;color:hsl(var(--warning));background:hsl(var(--warning)/.12);border:1px solid hsl(var(--warning)/.3);border-radius:999px;padding:6px 13px}
.dietrow+.dietrow{border-top:1px solid hsl(var(--border)/.5)}
.fpill{font-size:14.5px;font-weight:600;color:hsl(var(--fg));background:linear-gradient(135deg,hsl(var(--brand)/.17),hsl(var(--brand)/.05));border:1px solid hsl(var(--brand)/.3);border-radius:999px;padding:9px 17px}
.fpill:before{content:"„";color:hsl(var(--brand-light));margin-right:3px}
.fpill:after{content:"“";color:hsl(var(--brand-light));margin-left:3px}
.dietrow{display:grid;grid-template-columns:1fr 1fr}
.dcol{padding:22px 26px}
.dcol.nam{border-right:1px solid hsl(var(--border)/.5)}
.dcol h4{display:flex;align-items:center;gap:11px;font-size:13px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;margin-bottom:16px}
.dcol h4 .ic{width:28px;height:28px;border-radius:8px;display:grid;place-items:center;flex:none}
.dcol h4 .ic svg{width:15px;height:15px}
.dcol h4 .cnt{margin-left:auto;font-family:var(--font-mono);font-size:11px;color:hsl(var(--fg-dim))}
.dcol ul{list-style:none}
.dcol li{position:relative;padding-left:18px;margin:15px 0;font-size:13.5px;line-height:1.45}
.dcol li:before{content:"";position:absolute;left:0;top:7px;width:7px;height:7px;border-radius:2px;background:var(--dot,hsl(var(--brand)))}
.dcol li .q{display:block;font-style:italic;font-weight:600;color:hsl(var(--fg))}
.dcol li .expl{display:block;margin-top:4px;font-size:12px;line-height:1.5;color:hsl(var(--fg-dim));font-weight:400;font-style:normal}
@media(max-width:900px){.dietrow{grid-template-columns:1fr}.dcol.nam{border-right:none;border-bottom:1px solid hsl(var(--border)/.5)}.ubhead .ins{max-width:100%;margin-left:0}}
"""

SVG_DEFS = r"""<svg style="display:none" xmlns="http://www.w3.org/2000/svg"><symbol id="i-fire" viewBox="0 0 24 24"><path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67z"/></symbol><symbol id="i-eye" viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zm0 12a4.5 4.5 0 110-9 4.5 4.5 0 010 9zm0-7a2.5 2.5 0 100 5 2.5 2.5 0 000-5z"/></symbol><symbol id="i-heart" viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></symbol><symbol id="i-cmt" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></symbol><symbol id="i-clk" viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></symbol><symbol id="i-tgt" viewBox="0 0 24 24"><path d="M12 2a10 10 0 100 20 10 10 0 000-20zm0 18a8 8 0 110-16 8 8 0 010 16zm0-13a5 5 0 100 10 5 5 0 000-10zm0 8a3 3 0 110-6 3 3 0 010 6zm0-4.5a1.5 1.5 0 100 3 1.5 1.5 0 000-3z"/></symbol><symbol id="i-fb" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></symbol><symbol id="i-ig" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></symbol><symbol id="i-yt" viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12z"/></symbol><symbol id="i-tt" viewBox="0 0 24 24"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></symbol><symbol id="i-li" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z"/></symbol><symbol id="i-goo" viewBox="0 0 24 24"><path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/></symbol><symbol id="i-lay" viewBox="0 0 24 24"><path d="M4 4h7v7H4V4zm9 0h7v4h-7V4zm0 6h7v10h-7V10zM4 13h7v7H4v-7z"/></symbol><symbol id="i-bolt" viewBox="0 0 24 24"><path d="M11 21h-1l1-7H7.5c-.58 0-.57-.32-.38-.66.19-.34.05-.08.07-.12C8.48 10.94 10.42 7.54 13 3h1l-1 7h3.5c.49 0 .56.33.47.51l-.07.15C12.96 17.55 11 21 11 21z"/></symbol><symbol id="i-play" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></symbol><symbol id="i-img" viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></symbol></svg>"""
