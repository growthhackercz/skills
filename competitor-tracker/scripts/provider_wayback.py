#!/usr/bin/env python3
"""competitor-tracker — provider WAYBACK (archive.org CDX, zdarma, bez klíče).

Cold-start hodnota při baseline: „takhle se web/nabídka konkurenta vyvíjely poslední rok
zpátky" — okamžitá historie bez čekání na akumulaci vlastních snímků.
Ověřeno živě 2026-07-10 (notino.cz: 40+ snímků)."""
import datetime, json, sys, urllib.parse, urllib.request

CDX = "https://web.archive.org/cdx/search/cdx"


def history(domain, years=1, timeout=45):
    """Přehled archivu webu: počet snímků, rozsah, ~kvartální odkazy. None při nedostupnosti."""
    domain = (domain or "").replace("https://", "").replace("http://", "").strip("/")
    if not domain:
        return None
    frm = (datetime.date.today() - datetime.timedelta(days=365 * years)).strftime("%Y%m%d")
    rows = None
    # archive.org umí házet 503 (rate limit) — zkus i variantu bez www; při neúspěchu
    # fail-open na None (wayback.json nevznikne -> příští obchůzka to zkusí sama znovu)
    for cand in dict.fromkeys((domain, domain.removeprefix("www."))):
        q = urllib.parse.urlencode({"url": cand, "output": "json", "fl": "timestamp,original",
                                    "filter": "statuscode:200", "collapse": "timestamp:6",
                                    "from": frm, "limit": "60"})
        try:
            rows = json.load(urllib.request.urlopen(f"{CDX}?{q}", timeout=timeout))[1:]
            domain = cand
            break
        except Exception as e:
            print(f"[wayback] {cand}: {e}", file=sys.stderr)
    if rows is None:
        return None
    if not rows:
        return {"domain": domain, "snapshots": 0, "quarterly": []}
    quarterly = rows[:: max(1, len(rows) // 8)][:8]
    return {"domain": domain, "snapshots": len(rows),
            "first": rows[0][0][:8], "last": rows[-1][0][:8],
            "quarterly": [{"date": f"{t[:4]}-{t[4:6]}-{t[6:8]}",
                           "url": f"https://web.archive.org/web/{t}/{o}"} for t, o in quarterly]}
