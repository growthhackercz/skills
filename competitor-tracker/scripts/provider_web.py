#!/usr/bin/env python3
"""competitor-tracker — provider WEB (funnel spy + blog diff, stdlib, ~zdarma).

Funnel spy: normalizovaný snapshot homepage (title, H1, meta, ceny, CTA) -> diff jen
významných prvků (noise-engineering: kosmetika webu ≠ změna nabídky).
Blog diff: sitemap.xml -> nové URL od minula = content velocity + témata.
Načítání používá pouze bezpečný stdlib HTTP klient. JS-only nebo anti-bot web se
označí jako nedostupný; tento modul nemá skrytý Playwright ani placený fallback."""
import hashlib, html, html.parser, json, re, sys, urllib.parse, urllib.request, urllib.error

from net_guard import UnsafeURL, bezpecne_stahni, zkontroluj_url  # noqa: F401  (re-export pro tracker)

UA = {"User-Agent": "Mozilla/5.0 (compatible; CliqSalesTracker/1.0; +https://cliqsales.com)"}
PRICE_RE = re.compile(r"\d[\d\s.,]{1,12}\s*(?:Kč|CZK|€|EUR|USD|\$)|(?:Kč|€)\s*\d[\d\s.,]{1,10}", re.I)


class WebUnavailable(Exception):
    """Stránku se nepodařilo načíst. NENÍ to „beze změn" — volající to musí ohlásit."""


def _fetch(url, timeout=30):
    """Vrací text stránky. Vyhazuje WebUnavailable při výpadku, UnsafeURL při zakázané adrese.

    Dřív vracelo None a volající dělal `continue` — výpadek webu tak vypadal
    stejně jako klidný týden. Proto výjimka, ne None.
    """
    try:
        return bezpecne_stahni(url, timeout=timeout, hlavicky=UA)
    except UnsafeURL:
        raise
    except Exception as e:
        print(f"[web] {url}: {e}", file=sys.stderr)
        raise WebUnavailable(f"{url}: {e}") from e


_META_RE = re.compile(r"<meta\s+[^>]*?(?:property|name)\s*=\s*[\"']([^\"']+)[\"'][^>]*?content\s*=\s*[\"']([^\"']*)[\"']"
                      r"|<meta\s+[^>]*?content\s*=\s*[\"']([^\"']*)[\"'][^>]*?(?:property|name)\s*=\s*[\"']([^\"']+)[\"']", re.I)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


def page_card(url, timeout=15):
    """„Karta stránky" jako při sdílení na FB: {url, image, title} z og:image / og:title (fallback <title>).
    Zdarma, stdlib, jen hlavička stránky. Logo místo obrázku (typicky homepage) se nepovažuje za náhled.
    Vrací None, když stránka nejde načíst — volající kartu prostě nevykreslí (žádný prázdný rámeček)."""
    try:
        h = _fetch(url, timeout=timeout)
    except Exception:
        return None
    head = h[:120_000]
    meta = {}
    for m in _META_RE.finditer(head):
        k, v = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
        meta.setdefault(k.lower(), html.unescape(v or "").strip())
    img = meta.get("og:image") or meta.get("og:image:url") or meta.get("twitter:image") or ""
    if img and not img.startswith("http"):
        img = urllib.parse.urljoin(url, img)
    if img and (re.search(r"logo|favicon|\.svg(\?|$)", img, re.I)):
        img = ""   # logo není náhled stránky
    t = _TITLE_RE.search(head)
    title = meta.get("og:title") or (html.unescape(t.group(1)).strip() if t else "")
    return {"url": url, "image": img, "title": _norm(title)[:120]}


_FOOT = (  # měřicí skripty na webu = otisk „kde inzeruje" (ID účtů se veřejně dohledat nedají, platformy ano)
    ("meta_pixel", "Meta", r"fbq\(\s*['\"]init['\"]\s*,\s*['\"](\d{6,})"),
    ("google_ads", "Google Ads", r"(AW-\d{6,})"),
    ("linkedin", "LinkedIn", r"_linkedin_partner_id\s*=\s*['\"](\d+)"),
    ("sklik", "Sklik", r"(seznam_retargeting_id|rc\.retargetingId|c\.seznam\.cz/js/rc)"),
    ("tiktok", "TikTok", r"ttq\.load\(['\"]([A-Z0-9]{8,})"),
    ("gtm", "", r"(GTM-[A-Z0-9]{4,})"),
    ("ga4", "", r"(G-[A-Z0-9]{6,})"),
)


def ad_footprint(url, timeout=15):
    """Otisk inzerce z homepage: které reklamní platformy mají na webu měřicí skript.
    {"platforms": ["Meta", "Google Ads"], "ids": {meta_pixel: [...], google_ads: [...], gtm: [...]}}.
    Poctivě: pixel = inzeruje (nebo měří) na Metě; chybějící pixel ≠ neinzeruje (GTM může skrývat)."""
    try:
        h = _fetch(url, timeout=timeout)
    except Exception:
        return None
    ids, plats = {}, []
    for key, label, rx in _FOOT:
        found = sorted(set(re.findall(rx, h)))[:3]
        if found:
            ids[key] = found
            if label:
                plats.append(label)
    if not plats and ids.get("gtm"):
        plats.append("nelze určit (web měří přes správce značek Google)")
    return {"platforms": plats, "ids": ids, "checked": url}


class _Extract(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.h1, self.ctas, self.meta = "", [], [], ""
        self._in, self._skip = None, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript"): self._skip += 1
        elif tag == "title": self._in = "title"
        elif tag == "h1": self._in = "h1"; self.h1.append("")
        elif tag in ("button",) or (tag == "a" and "btn" in (a.get("class") or "") + (a.get("id") or "")):
            self._in = "cta"; self.ctas.append("")
        elif tag == "meta" and a.get("name") == "description":
            self.meta = (a.get("content") or "")[:300]

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"): self._skip = max(0, self._skip - 1)
        elif tag in ("title", "h1", "button", "a"): self._in = None

    def handle_data(self, d):
        if self._skip: return
        if self._in == "title": self.title += d
        elif self._in == "h1" and self.h1: self.h1[-1] += d
        elif self._in == "cta" and self.ctas: self.ctas[-1] += d


def _norm(s): return re.sub(r"\s+", " ", (s or "")).strip()


def snapshot(url):
    """Normalizovaný snapshot stránky. Výpadek = WebUnavailable, ne None."""
    htm = _fetch(url)   # WebUnavailable / UnsafeURL propouštíme na volajícího
    p = _Extract()
    try: p.feed(htm)
    except Exception: pass
    text = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", htm, flags=re.S)
    prices = sorted(set(_norm(m) for m in PRICE_RE.findall(text)))[:25]
    snap = {"url": url, "title": _norm(p.title)[:200], "meta": _norm(p.meta),
            "h1": [_norm(h)[:200] for h in p.h1 if _norm(h)][:5],
            "ctas": sorted(set(_norm(c)[:60] for c in p.ctas if 2 < len(_norm(c)) < 60))[:12],
            "prices": prices}
    snap["hash"] = hashlib.sha1(json.dumps({k: snap[k] for k in ("title", "h1", "prices")},
                                           ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    return snap


def diff_web(prev, curr):
    """[(note)] — jen významné změny (title/H1/ceny); meta a CTA jsou podpůrné (šum)."""
    if not prev or not curr or prev.get("hash") == curr.get("hash"):
        return []
    notes = []
    if prev.get("title") != curr.get("title"):
        notes.append(f"titulek: „{prev.get('title', '')[:70]}“ → „{curr.get('title', '')[:70]}“")
    if prev.get("h1") != curr.get("h1"):
        notes.append(f"hlavní sdělení (H1): „{'; '.join(prev.get('h1', []))[:80]}“ → „{'; '.join(curr.get('h1', []))[:80]}“")
    op, np_ = set(prev.get("prices") or []), set(curr.get("prices") or [])
    if op != np_:
        add, rem = sorted(np_ - op)[:4], sorted(op - np_)[:4]
        notes.append("ceny: " + (("nové " + ", ".join(add)) if add else "")
                     + ((" · zmizely " + ", ".join(rem)) if rem else ""))
    return notes


# ---- blog / sitemap ----

def _fetch_volitelne(url):
    """Pro zdroje, jejichž nepřítomnost je legitimní (sitemapa nemusí existovat).

    Dostupnost webu jako takového hlídá snapshot homepage — když ta projde a
    sitemapa vrátí 404, je to opravdu „sitemapu nemá", ne výpadek.
    """
    try:
        return _fetch(url)
    except (WebUnavailable, UnsafeURL) as e:
        print(f"[web] sitemapa přeskočena — {e}", file=sys.stderr)
        return None


def sitemap_urls(domain, cap=400):
    """URL ze sitemap (vč. sitemap indexu, 1 úroveň). Prázdný list = sitemap není (OK)."""
    if not domain.startswith("http"): domain = "https://" + domain
    domain = domain.rstrip("/")
    urls = []
    for sm in (f"{domain}/sitemap.xml", f"{domain}/sitemap_index.xml"):
        x = _fetch_volitelne(sm)
        if not x: continue
        locs = [u for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", x) if u.lower().startswith(("http://", "https://"))]
        if "<sitemapindex" in x:
            # POZOR: adresy uvnitř sitemapy píše cizí web, tedy potenciální
            # útočník. Chodí přes _fetch → net_guard, takže vnitřní adresa
            # neprojde. Nikdy je nestahuj mimo guard.
            for sub in locs[:6]:
                xx = _fetch_volitelne(sub)
                if xx: urls += [u for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xx) if u.lower().startswith(("http://", "https://"))]
        else:
            urls += locs
        if urls: break
    return sorted(set(urls))[:cap]


BLOGISH = re.compile(r"/(blog|clanky|clanek|magazin|aktuality|novinky|news|poradna|pripadov|case-stud|reference|ebook|webinar|akademie)/", re.I)
JOBISH = re.compile(r"karier|career|job|volna-mista|nabor", re.I)
PRODUCTISH = re.compile(r"/(produkt|product|products|zbozi|item|eshop|shop|kategorie|category)/|[?&](variant|sku)=", re.I)


def categorize_new(prev_urls, curr_urls):
    """Nové URL ze sitemap rozdělené: blog/obsah · kariéra · ostatní stránky · bulk (sortiment).
    E-shopové produktové vlny (>30 nových productish URL) NEvypisujeme položkově — jen počet
    (produktová hlídka = separátní skill, rozhodnutí 2026-07-10)."""
    new = [u for u in curr_urls if u not in set(prev_urls or [])]
    jobs = [u for u in new if JOBISH.search(u)]
    blog = [u for u in new if BLOGISH.search(u) and u not in jobs]
    rest = [u for u in new if u not in jobs and u not in blog]
    products = [u for u in rest if PRODUCTISH.search(u)]
    pages = [u for u in rest if u not in products]
    if len(pages) > 30:  # sitemap výbuch (redesign/migrace) — položkově by to byl šum
        products, pages = products + pages, []
    return {"blog": blog[:10], "jobs": jobs[:5], "pages": pages[:8], "bulk": len(products)}
