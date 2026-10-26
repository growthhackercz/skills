#!/usr/bin/env python3
"""competitor-tracker — diff engine (snapshot -> snapshot => eventy) + noise-engineering.

Eventy (viz references/data-contracts.md):
  BASELINE   první snímek značky (žádný NEW/KILLED spam; zrekonstruuje evergreeny z days_running)
  NEW        nová kreativa (podle creative_hash, ne ad_id — placementy šumí)
  KILLED     kreativa zmizela A běžela >= KILL_MIN_DAYS (kratší = testovací šum, jen agregát)
  RERUN      nová kreativa, jejíž hash je v archivu killnutých => prokázaný winner (nejsilnější signál)
  MILESTONE  aktivní kreativa překročila 30/60/90 dní (každý práh hlásíme jen JEDNOU)
  VELOCITY   počet nových kreativ >= 2x nebo <= 0.5x mediánu posledních běhů (min. absolutní rozdíl)
  QUIET      žádný event => legitimní výstup „nic podstatného"

Noise pravidla: identita = creative_hash · killed < 7 dní jen souhrnně · milestone dedup
přes profile.milestones_reported · velocity až od 3. běhu."""
import datetime, statistics

KILL_MIN_DAYS = 7
ARCHIVE_MAX_DAYS = 365   # návrat po roce už není „prokázaný winner" — archiv se ořezává
ARCHIVE_MAX_ITEMS = 400
MILESTONES = (30, 60, 90)
VELOCITY_MIN_RUNS = 2   # tolik předchozích běhů potřebuje mediánová základna
VELOCITY_MIN_ABS = 3    # min. absolutní rozdíl nových kreativ, aby VELOCITY nebyl šum


def dedupe(ads):
    """Placementy téže kreativy -> 1 logický záznam + variants count. Drží nejdéle běžící."""
    by = {}
    for a in ads:
        h = a.get("creative_hash") or ("id:" + str(a.get("ad_archive_id")))
        cur = by.get(h)
        d = a.get("days_running") if isinstance(a.get("days_running"), int) else -1
        dc = cur.get("days_running") if cur and isinstance(cur.get("days_running"), int) else -1
        if cur is None or d > dc:
            a = dict(a); a["variants"] = (cur.get("variants", 1) + 1) if cur else 1
            by[h] = a
        else:
            cur["variants"] = cur.get("variants", 1) + 1
    return by  # {hash: ad}


def _ev(brand, date, typ, ad=None, **extra):
    e = {"date": date, "brand": brand, "type": typ}
    if ad:
        e.update({"ad_archive_id": ad.get("ad_archive_id", ""), "hook": ad.get("hook", "")[:160],
                  "days": ad.get("days_running", ""), "cta": ad.get("cta", ""),
                  "destination": ad.get("destination", ""), "eu_reach": ad.get("eu_reach", ""),
                  "creative_url": ad.get("creative_url", "")})
    e.update(extra)
    return e


def diff(brand, date, prev_ads, curr_ads, profile):
    """(events, profile) — prev_ads=None => BASELINE. profile je mutovaný agregát značky."""
    curr = dedupe(curr_ads)
    events = []
    profile.setdefault("milestones_reported", {})
    profile.setdefault("velocity_history", [])
    profile.setdefault("killed_archive", {})   # hash -> {hook, days, date}

    if prev_ads is None:
        evers = sorted((a for a in curr.values() if isinstance(a.get("days_running"), int)
                        and a["days_running"] >= MILESTONES[0]),
                       key=lambda a: -a["days_running"])
        for a in evers:
            hit = max(m for m in MILESTONES if a["days_running"] >= m)
            profile["milestones_reported"][a["creative_hash"]] = [m for m in MILESTONES if m <= hit]
        viability = ("" if curr else
                     "Značka aktuálně neinzeruje v knihovně reklam — hlídka poběží hlavně po úřední "
                     "stopě, webu a recenzích; reklamní eventy budou vzácné (to je poctivá informace, ne chyba).")
        events.append(_ev(brand, date, "BASELINE", count=len(curr),
                          evergreens=[{"hook": a["hook"][:120], "days": a["days_running"],
                                       "eu_reach": a.get("eu_reach", "")} for a in evers[:5]],
                          oldest_days=(evers[0]["days_running"] if evers else 0),
                          eu_reach_total=sum(a["eu_reach"] for a in curr.values()
                                             if isinstance(a.get("eu_reach"), int)),
                          **({"note": viability} if viability else {})))
    else:
        prev = dedupe(prev_ads)
        new_h = [h for h in curr if h not in prev]
        gone_h = [h for h in prev if h not in curr]

        for h in new_h:
            a = curr[h]
            if h in profile["killed_archive"]:
                old = profile["killed_archive"][h]
                events.append(_ev(brand, date, "RERUN", a,
                                  prev_run_days=old.get("days", ""), killed_on=old.get("date", "")))
            else:
                events.append(_ev(brand, date, "NEW", a))

        short_kills = 0
        for h in gone_h:
            a = prev[h]
            d = a.get("days_running") if isinstance(a.get("days_running"), int) else 0
            profile["killed_archive"][h] = {"hook": a.get("hook", "")[:120], "days": d, "date": date}
            if d >= KILL_MIN_DAYS:
                events.append(_ev(brand, date, "KILLED", a))
            else:
                short_kills += 1
        if short_kills:
            events.append(_ev(brand, date, "KILLED_SHORT", count=short_kills,
                              note=f"{short_kills} kreativ zmizelo do {KILL_MIN_DAYS} dní (testovací šum, souhrnně)"))

        for h, a in curr.items():
            d = a.get("days_running")
            if not isinstance(d, int): continue
            done = profile["milestones_reported"].get(h, [])
            for m in MILESTONES:
                if d >= m and m not in done:
                    events.append(_ev(brand, date, "MILESTONE", a, milestone=m))
                    done = sorted(set(done) | {m})
            if done: profile["milestones_reported"][h] = done

        n_new = len(new_h)
        hist = [v["new_count"] for v in profile["velocity_history"]]
        if len(hist) >= VELOCITY_MIN_RUNS:
            base = statistics.median(hist[-4:])
            if abs(n_new - base) >= VELOCITY_MIN_ABS and base >= 0:
                if base > 0 and n_new >= 2 * base:
                    events.append(_ev(brand, date, "VELOCITY", direction="up", new=n_new, base=base,
                                      note="výrazně zrychlili testování kreativ"))
                elif n_new <= base / 2:
                    events.append(_ev(brand, date, "VELOCITY", direction="down", new=n_new, base=base,
                                      note="výrazně zpomalili — možná šetří, nebo přesouvají rozpočet"))
        profile["velocity_history"] = (profile["velocity_history"] + [{"date": date, "new_count": n_new}])[-12:]

    # Pruning — profil má přežít roky týdenních běhů, ne bobtnat donekonečna
    try:
        cutoff = (datetime.date.fromisoformat(date) - datetime.timedelta(days=ARCHIVE_MAX_DAYS)).isoformat()
    except ValueError:
        cutoff = ""
    ka = profile["killed_archive"]
    if len(ka) > ARCHIVE_MAX_ITEMS or any(v.get("date", "") < cutoff for v in ka.values()):
        kept = sorted(ka.items(), key=lambda kv: kv[1].get("date", ""), reverse=True)[:ARCHIVE_MAX_ITEMS]
        profile["killed_archive"] = {h: v for h, v in kept if v.get("date", "") >= cutoff}
    live = set(curr) | set(profile["killed_archive"])
    profile["milestones_reported"] = {h: m for h, m in profile["milestones_reported"].items() if h in live}

    if not [e for e in events if e["type"] not in ("KILLED_SHORT",)]:
        events.append(_ev(brand, date, "QUIET", note="beze změn — to je taky informace"))

    # agregát pro profil / wiki / status
    active = list(curr.values())
    evers = sorted((a for a in active if isinstance(a.get("days_running"), int)
                    and a["days_running"] >= MILESTONES[0]), key=lambda a: -a["days_running"])
    profile.update({
        "updated": date, "active_creatives": len(active),
        "active_placements": sum(a.get("variants", 1) for a in active),
        "oldest_days": (max((a["days_running"] for a in active
                             if isinstance(a.get("days_running"), int)), default=0)),
        "evergreens": [{"hook": a["hook"][:120], "days": a["days_running"], "cta": a.get("cta", ""),
                        "eu_reach": a.get("eu_reach", "")} for a in evers[:8]],
        "top_hooks": [a["hook"][:140] for a in sorted(
            active, key=lambda x: -(x.get("days_running") if isinstance(x.get("days_running"), int) else 0))[:8]
            if a.get("hook")],
        "eu_reach_total": sum(a["eu_reach"] for a in active if isinstance(a.get("eu_reach"), int)),
        "top_by_reach": [{"hook": a["hook"][:120], "eu_reach": a["eu_reach"], "days": a.get("days_running", "")}
                         for a in sorted((x for x in active if isinstance(x.get("eu_reach"), int)),
                                         key=lambda x: -x["eu_reach"])[:5]],
    })
    return events, profile
