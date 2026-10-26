#!/usr/bin/env python3
"""competitor-tracker — digest board renderer (CliqSales navy, DM Sans, cyan->blue).
render(week, brands, out_html) — brands = list per-brand bloků z tracker.py:
  {slug, name, active, oldest, events: [event dicty z diff_engine], evergreens: [...]}
Čistý render, žádná logika. Poctivé labelování: délka běhu = proxy útraty."""
import html
import os
import tempfile
import urllib.parse


def _safe(u):
    """Jen http(s) odkazy do href — URL z cizích sitemap/reklam by jinak mohla nést javascript:."""
    u = str(u or "").strip()
    if any(ord(ch) < 32 for ch in u):
        return ""
    try:
        parsed = urllib.parse.urlsplit(u)
    except ValueError:
        return ""
    if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
        return ""
    if parsed.username is not None or parsed.password is not None:
        return ""
    return u

EV = {  # typ -> (štítek, barva, emoji-free ikona SVG path klíč)
    "BASELINE":     ("první snímek", "#38b6ff"),
    "NEW":          ("nová kreativa", "#2ee6c6"),
    "RERUN":        ("návrat winnera", "#ffd166"),
    "KILLED":       ("vypnuto", "#ff5d8f"),
    "KILLED_SHORT": ("krátké testy", "#8aa0c0"),
    "MILESTONE":    ("evergreen milník", "#b48bff"),
    "VELOCITY":     ("změna tempa", "#38b6ff"),
    "QUIET":        ("beze změn", "#8aa0c0"),
    "SOURCE_STALE": ("výpadek zdroje", "#8aa0c0"),
    "SOURCE_UNAVAILABLE": ("zdroj nedostupný", "#ff9f45"),
    "SOURCE_SKIPPED": ("zdroj přeskočen", "#ff9f45"),
    "REGISTRY":     ("úřední stopa", "#38b6ff"),
    "REGISTRY_CHANGE": ("změna v rejstříku", "#b48bff"),
    "ALERT":        ("zásadní událost", "#e24b4a"),
    "WAYBACK":      ("historie webu", "#38b6ff"),
    "WEB_CHANGE":   ("změna webu", "#2ee6c6"),
    "BLOG_NEW":     ("nový obsah", "#38b6ff"),
    "CONTENT_NEW":  ("nové stránky", "#38b6ff"),
    "JOBS_NEW":     ("nábor", "#b48bff"),
    "FILING":       ("listina ve sbírce", "#ffd166"),
    "NEWSLETTER":   ("newsletter", "#2ee6c6"),
    "NOTE":         ("poznámka", "#8aa0c0"),
    "YOUTUBE":      ("YouTube", "#ff5d8f"),
    "SOCIAL_NEW":   ("sociální sítě", "#b48bff"),
    "SOCIAL_BASELINE": ("první snímek · sítě", "#b48bff"),
    "REVIEWS":      ("recenze", "#ffd166"),
    "GOOGLE_ADS":   ("Google reklamy", "#38b6ff"),
    "LINKEDIN_ADS": ("LinkedIn reklamy", "#38b6ff"),
    "SERP_ADS":     ("brandová slova", "#e24b4a"),
}
NOTE_TYPES = ("KILLED_SHORT", "QUIET", "SOURCE_STALE", "SOURCE_UNAVAILABLE", "SOURCE_SKIPPED", "REGISTRY", "REGISTRY_CHANGE", "ALERT",
              "WAYBACK", "WEB_CHANGE", "BLOG_NEW", "CONTENT_NEW", "JOBS_NEW", "REVIEWS",
              "GOOGLE_ADS", "LINKEDIN_ADS", "SERP_ADS", "FILING", "NEWSLETTER", "NOTE", "YOUTUBE", "SOCIAL_NEW",
              "SOCIAL_BASELINE")
# ikona per typ události (stroke, lucide-like) — vizuální orientace v digestu
TICON = {
    "BLOG_NEW": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M9 13h6 M9 17h6",
    "CONTENT_NEW": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6",
    "JOBS_NEW": "M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16",
    "GOOGLE_ADS": "m3 11 18-5v12L3 14z M11.6 16.8a3 3 0 1 1-5.8-1.6",
    "LINKEDIN_ADS": "m3 11 18-5v12L3 14z M11.6 16.8a3 3 0 1 1-5.8-1.6",
    "YOUTUBE": "M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z M10 9v6l5-3z",
    "SOCIAL_NEW": "M17 2a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5z M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M17.5 6.5h.01",
    "SOCIAL_BASELINE": "M17 2a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5z M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
    "REVIEWS": "M12 2 15 8.3l6.9.6-5.2 4.6 1.6 6.5L12 17.8 5.7 22l1.6-6.5L2.1 8.9l6.9-.6z",
    "NEW": "M12 3l1.8 4.7L18.5 9l-4.7 1.3L12 15l-1.3-4.7L6 9l4.7-1.3z",
    "RERUN": "M3 12a9 9 0 1 0 9-9 M3 3v5h5",
    "KILLED": "M18.4 6.6a9 9 0 1 1-12.8 0 M12 2v10",
    "MILESTONE": "M12 2c1.2 3 4 4.2 4 8a4 4 0 0 1-8 0c0-1.3.6-2.2 1.2-2.8",
    "BASELINE": "M4 4h16v16H4z M4 10h16 M10 4v16",
    "WEB_CHANGE": "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M2 12h20 M12 2a15 15 0 0 1 0 20 M12 2a15 15 0 0 0 0 20",
    "WAYBACK": "M3 12a9 9 0 1 0 9-9 M3 3v5h5 M12 7v5l3 2",
    "SOURCE_UNAVAILABLE": "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M12 8v5 M12 16h.01",
    "SOURCE_STALE": "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M12 8v5 M12 16h.01",
    "SOURCE_SKIPPED": "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M12 8v5 M12 16h.01",
    "ALERT": "M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z M12 9v4 M12 17h.01",
    "REGISTRY": "M3 21h18 M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16 M9 8h.01 M15 8h.01 M9 12h.01 M15 12h.01",
    "REGISTRY_CHANGE": "M3 21h18 M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16 M9 8h.01 M15 8h.01",
    "FILING": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6",
    "NEWSLETTER": "M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z m1 1 7 6 7-6",
    "SERP_ADS": "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14z M21 21l-4.3-4.3",
    "VELOCITY": "m22 7-8.5 8.5-5-5L2 17 M16 7h6v6",
}
_LINK = ('<svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.2" '
         'stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6"/><path d="M10 14 21 3"/>'
         '<path d="M18 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5"/></svg>')
ACCENTS = ("#38b6ff", "#ffb454", "#2ee6c6", "#b48bff", "#ffd166", "#ff9f45")
ICON = {
    "flame": '<path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67z"/>',
    "paw": '<path d="M12 12.5c-2.9 0-5.5 2.6-5.5 5.2 0 1.6 1.2 2.8 2.9 2.8 1 0 1.7-.4 2.6-.4s1.6.4 2.6.4c1.7 0 2.9-1.2 2.9-2.8 0-2.6-2.6-5.2-5.5-5.2zM6 8.5a2.2 2.5 0 100 5 2.2 2.5 0 000-5zm12 0a2.2 2.5 0 100 5 2.2 2.5 0 000-5zM9 3.5a2.2 2.7 0 100 5.4 2.2 2.7 0 000-5.4zm6 0a2.2 2.7 0 100 5.4 2.2 2.7 0 000-5.4z"/>',
    "bolt": '<path d="M13 2L3 14h7v8l10-12h-7z"/>',
}


def _svg(k, sz=14, col="#fff", op=1.0):
    return f'<svg viewBox="0 0 24 24" width="{sz}" height="{sz}" fill="{col}" style="opacity:{op};flex:none">{ICON.get(k, "")}</svg>'


def _e(s): return html.escape(str(s or ""))


def _atomic_write(out_html, content):
    directory = os.path.dirname(out_html) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{os.path.basename(out_html)}.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, out_html)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def top_creatives(ads, n=8):
    """Pás náhledů pro kartu značky: aktivní kreativy s náhledem, nejdéle běžící první, 1 na creative_hash."""
    seen, out = set(), []
    for a in sorted((x for x in ads or [] if x.get("creative_url") and x.get("is_active", True)),
                    key=lambda x: -(x.get("days_running") if isinstance(x.get("days_running"), int) else -1)):
        h = a.get("creative_hash") or a.get("ad_archive_id")
        if h in seen:
            continue
        seen.add(h)
        out.append({"creative_url": a["creative_url"], "ad_library_url": a.get("ad_library_url", ""),
                    "hook": a.get("hook", ""), "days": a.get("days_running", "")})
        if len(out) >= n:
            break
    return out


def _tag(typ, label, color):
    p = TICON.get(typ)
    ico = (f'<svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" '
           f'stroke-linecap="round" stroke-linejoin="round"><path d="{p}"/></svg>') if p else ""
    return f'<span class="tag" style="--c:{color}">{ico}{_e(label)}</span>'


def _chip(url, label):
    if not _safe(url):
        return ""
    return f'<a class="lnk" href="{_e(url)}" target="_blank" rel="noopener noreferrer">{_LINK}{_e(label)}</a>'


def _links_html(ev):
    """Klikací chipy z polí, která event už nese: links[] · ad_archive_id (Ad Library) · destination.
    Žádné mrtvé odkazy: co chybí, se prostě nevykreslí."""
    typ, out = ev.get("type", ""), []
    labels = {"REVIEWS": "otevřít recenze", "GOOGLE_ADS": "knihovna reklam Google", "WEB_CHANGE": "otevřít stránku",
              "REGISTRY": "detail v rejstříku", "REGISTRY_CHANGE": "detail v rejstříku", "ALERT": "detail v rejstříku",
              "FILING": "sbírka listin", "YOUTUBE": "přehrát na YouTube", "SERP_ADS": "zobrazit výsledky",
              "WAYBACK": "archiv webu", "LINKEDIN_ADS": "knihovna reklam LinkedIn"}
    for i, u in enumerate([x for x in (ev.get("links") or []) if x]):
        if typ == "SOCIAL_NEW":
            lab = f"příspěvek {i + 1}"
        elif typ == "SOCIAL_BASELINE":
            lab = ("Facebook", "Instagram", "LinkedIn")[i] if i < 3 else "profil"
            for k, v in (("facebook.com", "Facebook"), ("instagram.com", "Instagram"), ("linkedin.com", "LinkedIn")):
                if k in u: lab = v
        elif typ in labels:
            lab = labels[typ]
        else:  # blog / kariéra / nové stránky -> poslední segment cesty
            lab = (u.rstrip("/").split("/")[-1] or u)[:42]
        out.append(_chip(u, lab))
    aid = ev.get("ad_archive_id")
    if aid and typ in ("NEW", "KILLED", "MILESTONE", "RERUN"):
        out.append(_chip(f"https://www.facebook.com/ads/library/?id={aid}", "otevřít v knihovně reklam Meta"))
    if ev.get("destination"):
        out.append(_chip(ev["destination"], "cílová stránka"))
    return f'<div class="links">{"".join(out)}</div>' if out else ""


def _thumb_html(ev):
    """Náhled kreativy (creative_url u nových/vypnutých/vrácených kreativ) + karty stránek (cards[]:
    og:image + titulek, jako při sdílení na FB) u nového obsahu / stránek / cílových stránek."""
    out = []
    u = ev.get("creative_url")
    if u and ev.get("type") in ("NEW", "KILLED", "RERUN"):
        href = f'https://www.facebook.com/ads/library/?id={ev["ad_archive_id"]}' if ev.get("ad_archive_id") else u
        if not _safe(href) or not _safe(u):
            return ""
        out.append(f'<a class="thumb" href="{_e(href)}" target="_blank" rel="noopener noreferrer">'
                   f'<img src="{_e(u)}" loading="lazy" referrerpolicy="no-referrer" alt="náhled kreativy"><span class="lk">{_LINK}</span></a>')
    for c in (ev.get("cards") or [])[:3]:
        if not c.get("image") or not _safe(c.get("url") or c["image"]) or not _safe(c["image"]):
            continue   # bez og:image žádný prázdný rámeček — titulek je v odkazu
        out.append(f'<a class="thumb pc" href="{_e(c.get("url") or c["image"])}" target="_blank" rel="noopener noreferrer" '
                   f'title="{_e(c.get("title", ""))}"><img src="{_e(c["image"])}" loading="lazy" referrerpolicy="no-referrer" alt=""><span class="lk">{_LINK}</span>'
                   f'<span class="pct">{_e(str(c.get("title", ""))[:48])}</span></a>')
    return "".join(out)


def _event_row(ev):
    typ = ev.get("type", "")
    label, color = EV.get(typ, (typ.lower(), "#8aa0c0"))
    if typ == "MILESTONE":
        label = f'{ev.get("milestone", "?")}+ dní'
    bits = []
    hook = ev.get("hook")
    if hook: bits.append(f'<span class="hk">„{_e(hook)}"</span>')
    if isinstance(ev.get("eu_reach"), int) and ev["eu_reach"] > 0:
        bits.append(f'dosah v EU ~{ev["eu_reach"]:,} lidí'.replace(",", " "))
    if typ == "BASELINE":
        bits.append(f'{ev.get("count", 0)} aktivních kreativ, nejstarší {ev.get("oldest_days", 0)} dní')
        if ev.get("note"): bits.append(_e(ev["note"]))
    if typ == "RERUN":
        bits.append(f'dřív běžela {_e(ev.get("prev_run_days"))} dní — vrátili ji = prokázaný winner')
    if typ == "KILLED" and isinstance(ev.get("days"), int):
        bits.append(f'po {ev["days"]} dnech')
    if typ == "MILESTONE" and isinstance(ev.get("days"), int):
        bits.append(f'běží {ev["days"]} dní — evergreen kandidát')
    if typ == "VELOCITY":
        bits.append(f'{_e(ev.get("note"))} ({ev.get("new")} nových vs. obvyklých ~{ev.get("base")})')
    if typ in NOTE_TYPES:
        bits.append(_e(ev.get("note")))
    return (f'<div class="ev">{_tag(typ, label, color)}{_thumb_html(ev)}'
            f'<div class="txt">{" · ".join(b for b in bits if b)}{_links_html(ev)}</div></div>')


def _brand_card(b, idx=0):
    evs = [e for e in b.get("events", []) if e.get("type") != "QUIET"] or b.get("events", [])
    rows = "\n".join(_event_row(e) for e in evs[:10])
    more = f'<div class="more">+ {len(evs) - 10} dalších eventů</div>' if len(evs) > 10 else ""
    ev_chips = "".join(
        f'<span class="chip">{_svg("flame", 11, "#ffd166")} {_e(str(x.get("hook", ""))[:60])}'
        f'<b>{x.get("days", "")} d</b></span>'
        for x in (b.get("evergreens") or [])[:3])
    # accent per značka (vizuální oddělení sekcí); zásadní událost = červená
    acc = "#e24b4a" if any(e.get("type") == "ALERT" for e in evs) else ACCENTS[idx % len(ACCENTS)]
    init = (str(b.get("name") or "?").strip()[:1] or "?").upper()
    fb_page_url = _safe(b.get("fb_page_url"))
    # pás náhledů aktivních kreativ (nejdéle běžící první = winnery) — klik = Ad Library
    strip = ""
    tc = [c for c in (b.get("top_creatives") or []) if _safe(c.get("creative_url")) and _safe(c.get("ad_library_url") or c.get("creative_url"))][:8]
    if tc:
        cards = "".join(
            f'<a class="cr" href="{_e(c.get("ad_library_url") or c["creative_url"])}" target="_blank" rel="noopener noreferrer" '
            f'title="{_e(str(c.get("hook", ""))[:140])}"><img src="{_e(c["creative_url"])}" loading="lazy" referrerpolicy="no-referrer" alt=""><span class="lk">{_LINK}</span>'
            f'<span class="crd">{c.get("days", "?")} d</span></a>' for c in tc)
        strip = f'<div class="strip"><div class="strip-l">Aktivní kreativy · nejdéle běžící</div><div class="crs">{cards}</div></div>'
    dc = [c for c in (b.get("dest_cards") or []) if _safe(c.get("image")) and _safe(c.get("url") or c.get("image"))][:4]
    if dc:   # kam posílají reklamy — cílové stránky jako karty (og:image + titulek), klik = stránka
        pcs = "".join(
            f'<a class="thumb pc" href="{_e(c.get("url") or c["image"])}" target="_blank" rel="noopener noreferrer" '
            f'title="{_e(c.get("title", ""))}"><img src="{_e(c["image"])}" loading="lazy" referrerpolicy="no-referrer" alt=""><span class="lk">{_LINK}</span>'
            f'<span class="pct">{_e(str(c.get("title", ""))[:48])}</span></a>' for c in dc)
        strip += f'<div class="strip"><div class="strip-l">Kam posílají reklamy · cílové stránky</div><div class="crs">{pcs}</div></div>'
    return f'''<section class="brand" style="--a:{acc}">
  <header><div class="bhead"><span class="binit">{_e(init)}</span><div><div class="bname">{_e(b["name"])}</div>
    <div class="bstats">{b.get("active", 0)} aktivních kreativ · nejstarší {b.get("oldest", 0)} dní{(" · inzeruje na: " + _e(", ".join(b["footprint"]))) if b.get("footprint") else ""}{(' · <a class="pl" href="' + _e(fb_page_url) + '" target="_blank" rel="noopener noreferrer">FB stránka</a>') if fb_page_url else ""}</div></div></div></header>
  {strip}
  {f'<div class="evers">{ev_chips}</div>' if ev_chips else ""}
  <div class="evs">{rows}{more}</div>
</section>'''


_CSS = """
*{box-sizing:border-box;margin:0}
html{background:#070d1c}
body{background:radial-gradient(1100px 620px at 6% -8%,rgba(46,230,198,.12),transparent 58%),radial-gradient(1050px 760px at 102% 2%,rgba(58,123,255,.16),transparent 56%),linear-gradient(180deg,#0a1122,#070d1c);background-attachment:fixed;color:#eaf1ff;font:15px/1.5 'DM Sans',-apple-system,'Segoe UI',Roboto,sans-serif;padding:34px 30px;max-width:1080px;margin:0 auto}
.kicker{display:inline-flex;align-items:center;gap:8px;font-size:12px;font-weight:700;letter-spacing:0;text-transform:uppercase;color:#2ee6c6;background:linear-gradient(135deg,#2ee6c633,#3a7bff22);border:1px solid #2ee6c633;padding:7px 14px;border-radius:30px}
h1{font-size:30px;font-weight:800;letter-spacing:0;margin:14px 0 4px}
h1 .grad{background:linear-gradient(135deg,#2ee6c6,#38b6ff 55%,#3a7bff);-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{color:#8aa0c0;margin:4px 0 20px}
.mrow{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 26px}
@media(max-width:720px){.mrow{grid-template-columns:repeat(2,1fr)}}
.m{background:#121a30;border:1px solid #1e2c4a;border-radius:14px;padding:14px 16px}
.m .v{font-size:26px;font-weight:800} .m .l{font-size:12px;color:#8aa0c0}
.quiet{background:#121a30;border:1px dashed #2e3f63;border-radius:14px;padding:18px;color:#aabbd8;margin-bottom:22px}
.brand{position:relative;background:linear-gradient(180deg,#131c33,#101627);border:1px solid #22304f;border-top:3px solid var(--a,#38b6ff);border-radius:16px;padding:20px 22px;margin:0 0 24px;box-shadow:0 22px 60px rgba(0,0,0,.4)}
.brand header{margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid #1e2c4a}
.bhead{display:flex;align-items:center;gap:13px}
.binit{flex:none;width:42px;height:42px;border-radius:12px;display:grid;place-items:center;font-weight:800;font-size:18px;color:#06101f;background:linear-gradient(140deg,var(--a,#38b6ff),#ffffff55)}
.bname{font-size:20px;font-weight:800;letter-spacing:0} .bstats{font-size:12.5px;color:#8aa0c0;margin-top:2px}
.links{margin-top:7px;display:flex;flex-wrap:wrap;gap:6px}
.lnk{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;font-weight:600;color:#7fd4ff;text-decoration:none;background:#0e1730;border:1px solid #24406a;border-radius:10px;padding:3px 9px}
.lnk:hover{border-color:#3a7bff;color:#aee0ff}
.thumb{position:relative;flex:none;display:block;width:80px;height:80px;border-radius:12px;overflow:hidden;border:1px solid #24406a;line-height:0}
.thumb img{width:100%;height:100%;object-fit:cover;display:block} .thumb:hover{border-color:#3a7bff}
.thumb.pc{position:relative;width:150px;height:84px}
.pct{position:absolute;left:0;right:0;bottom:0;font-size:10px;font-weight:700;line-height:1.2;color:#fff;background:linear-gradient(0deg,rgba(1,7,20,.85),rgba(1,7,20,0));padding:10px 6px 5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lk{position:absolute;top:6px;right:6px;width:22px;height:22px;border-radius:50%;background:rgba(1,7,20,.72);border:1px solid rgba(255,255,255,.18);display:grid;place-items:center;color:#fff;line-height:0;pointer-events:none}
.cr:hover .lk,.thumb:hover .lk{background:#119CFF}
.pl{color:#7fd4ff;text-decoration:none;border-bottom:1px dotted #3a7bff} .pl:hover{color:#aee0ff}
.strip{margin:0 0 12px} .strip-l{font-size:10.5px;font-weight:800;letter-spacing:0;text-transform:uppercase;color:#8aa0c0;margin-bottom:7px}
.crs{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px}
.cr{position:relative;flex:none;width:112px;height:112px;border-radius:12px;overflow:hidden;border:1px solid #24406a;background:#0e1730;line-height:0}
.cr img{width:100%;height:100%;object-fit:cover;display:block} .cr:hover{border-color:var(--a,#38b6ff)}
.crd{position:absolute;left:6px;bottom:6px;font-size:10.5px;font-weight:800;line-height:1;color:#fff;background:rgba(1,7,20,.72);border-radius:8px;padding:4px 6px}
.evers{margin:0 0 10px} .chip{display:inline-flex;align-items:center;gap:6px;background:#0e1730;border:1px solid #263354;border-radius:16px;padding:4px 10px;margin:0 6px 6px 0;font-size:12px;color:#cfe0ff}
.chip b{color:#ffd166;font-weight:800}
.ev{display:flex;gap:11px;align-items:flex-start;padding:11px 0;border-top:1px solid #1a2440}
.ev:first-child{border-top:0}
.tag{flex:none;display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:800;letter-spacing:0;text-transform:uppercase;color:var(--c);border:1px solid color-mix(in srgb,var(--c) 45%,transparent);background:color-mix(in srgb,var(--c) 12%,transparent);border-radius:12px;padding:4px 9px;margin-top:1px;white-space:nowrap}
.txt{font-size:13.5px;color:#c6d4ee} .hk{color:#eaf1ff;font-weight:600}
.more{font-size:12px;color:#8aa0c0;padding-top:8px}
footer{margin-top:26px;color:#6f83a6;font-size:12px;border-top:1px solid #1a2440;padding-top:14px}
@media(max-width:560px){
 body{padding:26px 14px}
 .brand{padding:18px 16px}
 .bhead{align-items:flex-start}
 .bhead>div:last-child{min-width:0}
 .bname,.bstats,.txt{overflow-wrap:anywhere}
 .ev{display:grid;grid-template-columns:minmax(0,1fr);gap:8px}
 .ev>.tag{width:max-content;max-width:100%;white-space:normal}
 .ev>.thumb{width:min(100%,220px);height:auto;aspect-ratio:1}
 .ev>.thumb.pc{aspect-ratio:16/9}
 .links{max-width:100%}
 .lnk{max-width:100%;white-space:normal;overflow-wrap:anywhere}
 .chip{max-width:100%;white-space:normal}
}
"""


def _fmt_reach(v):
    return f"~{v:,} lidí v EU".replace(",", " ") if isinstance(v, int) and v > 0 else ""


def _overview_card(b):
    reg = b.get("registry") or {}
    ev_chips = "".join(
        f'<span class="chip">{_svg("flame", 11, "#ffd166")} {_e(str(x.get("hook", ""))[:64])}'
        f'<b>{x.get("days", "")} d</b></span>'
        for x in (b.get("evergreens") or [])[:4])
    reach_rows = "".join(
        f'<div class="ev"><span class="tag" style="--c:#2ee6c6">dosah</span>'
        f'<div class="txt"><span class="hk">„{_e(str(t.get("hook", ""))[:80])}"</span> · '
        f'{_fmt_reach(t.get("eu_reach"))} ({t.get("days", "")} d)</div></div>'
        for t in (b.get("top_by_reach") or [])[:3])
    reg_bits = []
    if reg.get("executives"): reg_bits.append("vedení: " + ", ".join(reg["executives"][:3]))
    if reg.get("owners"): reg_bits.append("vlastníci: " + ", ".join(reg["owners"][:2]))
    if reg.get("flag_insolvence"): reg_bits.append("⚠ zmínka o insolvenci")
    if reg.get("flag_likvidace"): reg_bits.append("⚠ likvidace/zánik")
    reg_row = (f'<div class="ev"><span class="tag" style="--c:#38b6ff">rejstřík</span>'
               f'<div class="txt">{_e(" · ".join(reg_bits))}</div></div>') if reg_bits else ""
    quietnote = ('<div class="ev"><span class="tag" style="--c:#8aa0c0">bez reklam</span>'
                 '<div class="txt">Značka aktuálně neinzeruje — hlídka jede po rejstříku a webu.</div></div>'
                 if not b.get("active") else "")
    reach_total = _fmt_reach(b.get("eu_reach_total"))
    return f'''<section class="brand">
  <header><div class="bname">{_e(b["name"])}</div>
    <div class="bstats">{b.get("active", 0)} aktivních kreativ · nejstarší {b.get("oldest", 0)} dní{(" · celkem " + reach_total) if reach_total else ""} · stav k {_e(b.get("updated", "?"))}</div></header>
  {f'<div class="evers">{ev_chips}</div>' if ev_chips else ""}
  <div class="evs">{reg_row}{reach_rows}{quietnote}</div>
</section>'''


def render_overview(brands, out_html, generated=""):
    """Jednorázový SITUAČNÍ board — „jak si konkurence stojí teď" (z paměti, žádný scrape)."""
    n_active = sum(b.get("active", 0) for b in brands)
    n_ever = sum(len(b.get("evergreens") or []) for b in brands)
    reach = sum(b.get("eu_reach_total", 0) for b in brands if isinstance(b.get("eu_reach_total"), int))
    cards = "\n".join(_overview_card(b) for b in brands)
    doc = f'''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="referrer" content="no-referrer">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Konkurence — aktuální situace</title><style>{_CSS}</style></head><body>
<span class="kicker">{_svg("paw", 13, "#2ee6c6")} Stopař konkurence · aktuální situace</span>
<h1>Jak si konkurence stojí <span class="grad">právě teď</span></h1>
<p class="sub">Přehled z posledních snímků — pro změny v čase slouží týdenní digest. {_e(generated)}</p>
<div class="mrow">
  <div class="m"><div class="v">{len(brands)}</div><div class="l">sledovaných značek</div></div>
  <div class="m"><div class="v" style="color:#2ee6c6">{n_active}</div><div class="l">aktivních kreativ</div></div>
  <div class="m"><div class="v" style="color:#ffd166">{n_ever}</div><div class="l">evergreenů (30+ dní)</div></div>
  <div class="m"><div class="v" style="color:#38b6ff">{f"{reach:,}".replace(",", " ")}</div><div class="l">součet dosahu v EU</div></div>
</div>
{cards}
<footer>Zdroj: veřejná knihovna reklam Meta (DSA) + obchodní rejstřík + webový archiv. Dosah v EU je
reálné číslo z transparentnosti dle nařízení EU; přesnou útratu knihovna neukazuje.</footer>
</body></html>'''
    _atomic_write(out_html, doc)
    return out_html


def render(week, brands, out_html, generated="", complete=None):
    n_new = sum(1 for b in brands for e in b.get("events", []) if e["type"] == "NEW")
    n_rerun = sum(1 for b in brands for e in b.get("events", []) if e["type"] == "RERUN")
    n_kill = sum(1 for b in brands for e in b.get("events", []) if e["type"] == "KILLED")
    n_mile = sum(1 for b in brands for e in b.get("events", []) if e["type"] == "MILESTONE")
    # Výpadek zdroje NENÍ tichý týden — tichá degradace je horší než hlášená chyba.
    incomplete_types = {"SOURCE_STALE", "SOURCE_UNAVAILABLE", "SOURCE_SKIPPED"}
    incomplete = [b for b in brands
                  if any(e.get("type") in incomplete_types for e in b.get("events", []))]
    allev = [e for b in brands for e in b.get("events", [])]
    # Ticho se odvozuje ze všech typů událostí, ne jen z reklam. Změna webu,
    # vedení, recenzí nebo sociálních sítí je pořád reálná změna.
    activity = [
        e for e in allev
        if e.get("type") not in ({"QUIET", "BASELINE", "SOCIAL_BASELINE"} | incomplete_types)
    ]
    # První obchůzka (základna) NENÍ tichý týden — jen ještě není s čím porovnávat.
    first_run = not activity and any(e.get("type") in ("BASELINE", "SOCIAL_BASELINE") for e in allev)
    if complete is None:
        complete = not incomplete
    quiet = not activity and complete and not first_run
    cards = "\n".join(_brand_card(b, i) for i, b in enumerate(brands))
    if not complete:
        jmena = ", ".join(dict.fromkeys(b.get("name", "?") for b in incomplete)) or "sledované zdroje"
        quiet_note = ('<div class="quiet" style="border-color:rgba(255,197,84,.4)">'
                      f'<b>Obchůzka není úplná.</b> Dotčené značky: <b>{_e(jmena)}</b>. '
                      'Výsledky z dostupných zdrojů zůstávají platné, ale '
                      '<b>nelze tvrdit, že se u konkurence nic nezměnilo.</b></div>')
    elif first_run:
        n_act = sum(b.get("active", 0) for b in brands)
        n_posts = sum(e.get("count", 0) for e in allev if e["type"] == "SOCIAL_BASELINE")
        quiet_note = ('<div class="quiet" style="border-color:rgba(46,230,198,.35)">'
                      f'🧭 <b>První obchůzka: základna pro příští porovnání.</b> Uložil jsem {n_act} kreativ'
                      + (f', {n_posts} příspěvků ze sociálních sítí' if n_posts else '')
                      + ', recenze, rejstřík a stav webu. Od příště hlásím <b>jen změny</b>: nové kreativy, '
                        'nové příspěvky, pohyby cen a úřední události.</div>')
    elif quiet:
        quiet_note = ('<div class="quiet">Tichý týden — u sledované konkurence se nic podstatného nezměnilo. '
                      'To je taky informace: nikdo neškáluje nic nového.</div>')
    else:
        quiet_note = ""
    doc = f'''<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta name="referrer" content="no-referrer">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stopař konkurence — týden {_e(week)}</title><style>{_CSS}</style></head><body>
<span class="kicker">{_svg("paw", 13, "#2ee6c6")} Stopař konkurence · týdenní digest</span>
<h1>Co se změnilo u konkurence — <span class="grad">týden {_e(week)}</span></h1>
<p class="sub">Jen změny, žádný šum. {_e(generated)}</p>
<div class="mrow">
  <div class="m"><div class="v" style="color:#2ee6c6">{n_new}</div><div class="l">nové kreativy</div></div>
  <div class="m"><div class="v" style="color:#ffd166">{n_rerun}</div><div class="l">návraty winnerů</div></div>
  <div class="m"><div class="v" style="color:#ff5d8f">{n_kill}</div><div class="l">vypnuté (7+ dní)</div></div>
  <div class="m"><div class="v" style="color:#b48bff">{n_mile}</div><div class="l">evergreen milníky</div></div>
</div>
{quiet_note}
{cards}
<footer>Zdroj: veřejná knihovna reklam Meta (transparentnost dle nařízení EU). Délka běhu = ukazatel
toho, za co inzerent dál platí. Dosah v EU je reálné číslo z DSA transparentnosti (rozsah, jen reklamy
zobrazované v EU); přesnou útratu knihovna neukazuje.</footer>
</body></html>'''
    _atomic_write(out_html, doc)
    return out_html
