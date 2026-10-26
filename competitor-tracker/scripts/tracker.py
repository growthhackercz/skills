#!/usr/bin/env python3
"""competitor-tracker („Stopař konkurence") — validovaný orchestrátor (žádný přímý shell).

Příkazy:
  init        založí /documents/competitors/ strukturu + prázdný watchlist
  add-brand   přidá značku do watchlistu (idempotentní podle slugu)
  patrol      obchůzka: fetch (Apify) -> snapshot -> diff -> eventy -> profil -> digest board
              --dry-run = nevolá placené actory, jen účetní stav + plán; --fixture-dir = test bez kreditů
  status      kompaktní JSON pro agenta (watchlist, agregáty, poslední eventy) — režim DOTAZ

Datové kontrakty: references/data-contracts.md. Vše stdlib, bez závislostí."""
import argparse
import contextlib
import datetime
import fcntl
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import provider_ads, provider_registry, provider_wayback, provider_web, provider_extras  # noqa: E402
import diff_engine, board  # noqa: E402

DEFAULT_ROOT = "/documents/competitors"
DEFAULT_APIFY_MONTHLY_USD = 5.0
MIN_ADS_PER_BRAND = 10
MAX_ADS_PER_BRAND = 100
MAX_DEEP_CREATIVES = 25


class StateCorruptError(RuntimeError):
    """Durable tracker state is unreadable and must not be reset implicitly."""


class PatrolAlreadyRunning(RuntimeError):
    """Another process owns the patrol lock for the same data root."""


def _read_events(path, since=None):
    """Čte events.jsonl odolně: poškozený řádek (přerušený zápis při pádu) přeskočí,
    místo aby shodil battlecard, report i status."""
    out, bad = [], 0
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    bad += 1
                    continue
                if since and e.get("date", "") < since:
                    continue
                out.append(e)
    except FileNotFoundError:
        return []
    if bad:
        print(f"[tracker] pozor: {bad} poškozených řádků v events.jsonl přeskočeno", file=sys.stderr)
    return out

def slugify(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:50] or "znacka"


def _single_line(value, label, maximum=160):
    text = " ".join(str(value or "").split()).strip()
    if not text:
        raise ValueError(f"{label} nesmí být prázdný.")
    return text[:maximum]


def _p(root, *parts): return os.path.join(root, *parts)


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        raise StateCorruptError(
            f"Soubor stavu je poškozený: {path} (řádek {exc.lineno}, sloupec {exc.colno}). "
            "Nezakládám novou základnu; obnovte soubor ze zálohy nebo ho opravte."
        ) from exc


def _save(path, data):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{os.path.basename(path)}.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def _save_text(path, content):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{os.path.basename(path)}.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def _append_jsonl(path, items):
    rows = [json.dumps(item, ensure_ascii=False) + "\n" for item in items]
    if not rows:
        return
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    payload = "".join(rows).encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        written = os.write(fd, payload)
        if written != len(payload):
            raise OSError(f"Neúplný zápis event logu ({written}/{len(payload)} bajtů).")
        os.fsync(fd)
    finally:
        os.close(fd)


def _positive_budget(value, label="Měsíční rozpočtový práh Apify"):
    try:
        budget = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} musí být kladné číslo v USD.") from None
    if not math.isfinite(budget) or budget <= 0:
        raise ValueError(f"{label} musí být větší než 0 USD.")
    return budget


def _bounded_int(value, minimum, maximum, label):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} musí být celé číslo {minimum}–{maximum}.") from None
    if number < minimum or number > maximum:
        raise ValueError(f"{label} musí být v rozsahu {minimum}–{maximum}.")
    return number


def _country_code(value):
    code = str(value or "").strip().upper()
    if not re.fullmatch(r"[A-Z]{2}", code):
        raise ValueError("Trh musí být dvoupísmenný kód země, například CZ, SK, ES nebo GB.")
    return code


def _validate_fixture_root(root):
    production_root = os.path.realpath(root)
    if production_root == "/documents" or production_root.startswith("/documents/"):
        raise ValueError("Fixture režim je povolený jen nad testovacím kořenem mimo /documents.")


def _require_paid_confirmation(args):
    if not getattr(args, "confirm_paid", False):
        sys.exit(
            "Tento příkaz může čerpat placené kredity Apify. Po výslovném souhlasu klienta "
            "ho spusťte znovu s --confirm-paid."
        )


def _paid_budget_guard(watchlist):
    """Return a fail-closed snapshot of credential and current monthly usage."""
    try:
        budget = _positive_budget(
            (watchlist.get("caps") or {}).get("apify_monthly_usd", DEFAULT_APIFY_MONTHLY_USD)
        )
    except ValueError as exc:
        return {
            "ok": False,
            "code": "invalid_budget",
            "reason": str(exc),
            "has_key": bool(provider_ads.token()),
            "budget": {
                "limit_usd": None,
                "effective_limit_usd": None,
                "provider_limit_usd": None,
                "used_usd": None,
                "stav": "neplatné nastavení",
                "guarantee": "Předběžná pojistka; tvrdý účetní limit nastavte také přímo v Apify.",
            },
        }

    budget_state = {
        "limit_usd": budget,
        "effective_limit_usd": budget,
        "provider_limit_usd": None,
        "used_usd": None,
        "stav": "neověřeno",
        "guarantee": "Předběžná pojistka podle aktuální útraty; tvrdý účetní limit nastavte také přímo v Apify.",
    }
    has_key = bool(provider_ads.token())
    if not has_key:
        budget_state["stav"] = "bez klíče"
        return {
            "ok": False,
            "code": "missing_credential",
            "reason": "chybí APIFY_API_KEY v Control Center → Nastavení → Integrace",
            "has_key": False,
            "budget": budget_state,
        }

    usage = provider_ads.monthly_usage_usd()
    if not usage or usage.get("used") is None:
        budget_state["stav"] = "ověření selhalo"
        return {
            "ok": False,
            "code": "usage_unavailable",
            "reason": "aktuální útratu Apify se nepodařilo ověřit",
            "has_key": True,
            "budget": budget_state,
        }

    used = float(usage["used"])
    provider_limit = usage.get("apify_max")
    if isinstance(provider_limit, (int, float)) and math.isfinite(provider_limit) and provider_limit > 0:
        budget_state["provider_limit_usd"] = round(float(provider_limit), 2)
        budget_state["effective_limit_usd"] = min(budget, float(provider_limit))
    effective_limit = float(budget_state["effective_limit_usd"])
    budget_state["used_usd"] = round(used, 2)
    if used >= effective_limit:
        budget_state["stav"] = "vyčerpáno"
        return {
            "ok": False,
            "code": "budget_exhausted",
            "reason": (
                f"měsíční útrata Apify {used:.2f} USD dosáhla bezpečnostního prahu "
                f"{effective_limit:.2f} USD"
            ),
            "has_key": True,
            "budget": budget_state,
        }

    budget_state["stav"] = "nad 80 %" if used >= 0.8 * effective_limit else "v pořádku"
    return {
        "ok": True,
        "code": "",
        "reason": "",
        "has_key": True,
        "budget": budget_state,
    }


def _require_paid_budget(watchlist):
    guard = _paid_budget_guard(watchlist)
    if not guard["ok"]:
        sys.exit(f"Placený zdroj nespouštím: {guard['reason']}.")
    return guard


@contextlib.contextmanager
def _patrol_lock(root):
    """Serialize patrols sharing one durable data root."""
    os.makedirs(root, exist_ok=True)
    lock_path = _p(root, ".patrol.lock")
    with open(lock_path, "a+", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise PatrolAlreadyRunning(
                "Pro tento seznam už jedna obchůzka běží. Druhou nespouštím, aby se "
                "neduplikovala útrata ani výstupy."
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _watchlist(root):
    p = _p(root, "watchlist.json")
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise StateCorruptError(
            "watchlist.json existuje, ale není validní JSON. Nezakládám nový seznam; "
            "opravte soubor nebo ho obnovte ze zálohy."
        ) from exc
    if not isinstance(data, dict) or not isinstance(data.get("brands"), list):
        raise StateCorruptError(
            "watchlist.json nemá platnou strukturu (chybí pole brands). "
            "Nezakládám nový seznam; opravte soubor nebo ho obnovte ze zálohy."
        )
    if "keywords" in data and not isinstance(data.get("keywords"), list):
        raise StateCorruptError("watchlist.json má neplatné pole keywords; očekávám seznam.")
    if "caps" in data and not isinstance(data.get("caps"), dict):
        raise StateCorruptError("watchlist.json má neplatné pole caps; očekávám objekt.")
    return data


def _today(): return datetime.date.today().isoformat()


def _week(): return "{}-W{:02d}".format(*datetime.date.today().isocalendar()[:2])


# ---------- init / add-brand ----------

def cmd_init(a):
    wl = _watchlist(a.root)
    if wl is not None:
        print(json.dumps({"ok": True, "note": "watchlist už existuje", "brands": len(wl["brands"])}, ensure_ascii=False)); return
    try:
        budget = _positive_budget(a.apify_monthly_usd)
        cap = _bounded_int(a.cap, MIN_ADS_PER_BRAND, MAX_ADS_PER_BRAND, "Limit reklam na značku")
        country = _country_code(a.country)
    except ValueError as exc:
        sys.exit(str(exc))
    for d in ("history", "digest", "profiles"):
        os.makedirs(_p(a.root, d), exist_ok=True)
    _save(_p(a.root, "watchlist.json"),
          {"version": 1, "created": _today(), "country": country,
           "caps": {"ads_per_brand": cap, "apify_monthly_usd": budget},
           "brands": [], "keywords": []})
    print(json.dumps({"ok": True, "root": a.root, "country": country}, ensure_ascii=False))


def cmd_set_budget(a):
    """Změní měsíční bezpečnostní práh Apify (USD) bez re-initu."""
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    try:
        budget = _positive_budget(a.usd)
    except ValueError as exc:
        sys.exit(str(exc))
    wl.setdefault("caps", {})["apify_monthly_usd"] = budget
    _save(_p(a.root, "watchlist.json"), wl)
    print(json.dumps({"ok": True, "apify_monthly_usd": budget}, ensure_ascii=False))


_CARD_CACHE = {}


def _human_err(e):
    """Chybu zdroje přeložit klientovi (ne „HTTP Error 410: Gone")."""
    t = str(e)
    m = re.search(r"HTTP Error (\d{3})", t)
    code = int(m.group(1)) if m else None
    if code in (404, 410): return f"stránka neexistuje nebo byla přesunuta (kód {code})."
    if code in (401, 403): return f"web přístup odmítl, pravděpodobně ochrana proti robotům (kód {code})."
    if code and code >= 500: return f"web má výpadek na své straně (kód {code})."
    if "timed out" in t.lower() or "timeout" in t.lower(): return "web neodpověděl včas."
    return "zdroj se nepodařilo načíst (" + t[:80] + ")."


def _page_cards(urls, n=3):
    """Karty stránek (og:image + titulek) k prvním n odkazům události; cache per URL v rámci běhu.
    Zdarma (jen hlavička stránky). Stránka bez načtení = žádná karta, event zůstává."""
    out = []
    for u in [x for x in (urls or []) if str(x).startswith("http")][:n]:
        if u not in _CARD_CACHE:
            try:
                _CARD_CACHE[u] = provider_web.page_card(u)
            except Exception:
                _CARD_CACHE[u] = None
        if _CARD_CACHE[u]:
            out.append(_CARD_CACHE[u])
    return out


def _dest_cards(ads, n=4):
    """Cílové stránky reklam (nejdéle běžící první, 1 na URL, bez šablonových {{…}} URL) jako karty stránek."""
    seen, dests = set(), []
    for a in sorted(ads, key=lambda x: -(x.get("days_running") if isinstance(x.get("days_running"), int) else -1)):
        u = (a.get("destination") or "").split("?")[0].rstrip("/")
        if not u.startswith("http") or "{{" in u or u in seen:
            continue
        seen.add(u); dests.append(u)
        if len(dests) >= n * 2:
            break
    return [c for c in _page_cards(dests, n=n * 2) if c.get("image")][:n]


def cmd_find_place(a):
    """Kandidáti místa na Google Mapách pro recenze — uživatel POTVRDÍ správné (jako find-ico).
    Obecné jméno („AMC") jinak trefí cizí byznys. Jde o jedno placené Apify volání."""
    _require_paid_confirmation(a)
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    _require_paid_budget(wl)
    try:
        a.n = _bounded_int(a.n, 1, 10, "Počet kandidátů míst")
    except ValueError as exc:
        sys.exit(str(exc))
    b = next((x for x in wl["brands"] if x["slug"] == a.brand), None)
    if not b: sys.exit(f"Značka „{a.brand}“ není ve watchlistu.")
    loc = {"CZ": "Czechia", "SK": "Slovakia", "ES": "Spain"}.get(wl.get("country", "CZ"), "Czechia")
    try:
        cands = provider_extras.search_places(b["name"], location=loc, web=b.get("web", ""), n=a.n)
    except Exception as e:
        sys.exit(f"Mapy nedostupné: {e}")
    print(json.dumps({"brand": a.brand, "kandidati": cands,
                      "dalsi_krok": "potvrďte správné místo: tracker.py set-place --brand <slug> --place <url|placeId>"},
                     ensure_ascii=False, indent=1))


def cmd_set_place(a):
    """Uloží potvrzené místo na Mapách ke značce (URL nebo placeId) -> recenze se čtou z něj, ne z hádání."""
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    b = next((x for x in wl["brands"] if x["slug"] == a.brand), None)
    if not b: sys.exit(f"Značka „{a.brand}“ není ve watchlistu.")
    b["maps_place"] = (a.place or "").strip()
    _save(_p(a.root, "watchlist.json"), wl)
    print(json.dumps({"ok": True, "slug": a.brand, "maps_place": b["maps_place"]}, ensure_ascii=False))


def cmd_add_brand(a):
    wl = _watchlist(a.root)
    if wl is None:
        sys.exit("Nejdřív spusť: tracker.py init")
    try:
        name = _single_line(a.name, "Název značky")
    except ValueError as exc:
        sys.exit(str(exc))
    slug = slugify(name)
    if any(b["slug"] == slug for b in wl["brands"]):
        print(json.dumps({"ok": True, "note": "značka už ve watchlistu", "slug": slug}, ensure_ascii=False)); return
    if len(wl["brands"]) >= 10:
        sys.exit("Watchlist má max 10 značek (nákladový cap). Nejdřív nějakou odeber.")
    try:
        country = _country_code(wl.get("country", "CZ"))
    except ValueError as exc:
        sys.exit(str(exc))
    ico = re.sub(r"\s+", "", str(a.ico or ""))
    if ico and country == "CZ" and not re.fullmatch(r"\d{8}", ico):
        sys.exit("České IČO musí mít přesně 8 číslic.")
    rec = {"slug": slug, "name": name,
           "ad_library": " ".join(str(a.query or name).split()), "web": (a.web or "").strip(),
           "ico": ico, "youtube": (a.youtube or "").strip(),
           "facebook": (a.facebook or "").strip(), "instagram": (a.instagram or "").strip(),
           "linkedin": (a.linkedin or "").strip(), "maps_place": (a.maps or "").strip(),
           "fb_page_id": "", "fb_page_url": "", "footprint": None,
           "watch_urls": [], "note": a.note or ""}
    out = {"ok": True, "slug": slug}
    if rec["web"]:   # otisk „kde inzeruje" z měřicích skriptů webu (zdarma)
        rec["footprint"] = provider_web.ad_footprint(rec["web"])
        out["inzeruje_na"] = (rec["footprint"] or {}).get("platforms", [])
    if getattr(a, "find_page", False) and not getattr(a, "no_find_page", False):
        _require_paid_confirmation(a)
        _require_paid_budget(wl)
        out.update(_resolve_page(rec, country))   # správná FB stránka podle cílové domény reklam
    wl["brands"].append(rec)
    _save(_p(a.root, "watchlist.json"), wl)
    out["brands"] = len(wl["brands"])
    print(json.dumps(out, ensure_ascii=False, indent=1))


def _resolve_page(rec, country):
    """Najde stránku konkurenta v knihovně reklam (find_page). Jednoznačná shoda (reklamy vedou na jeho web)
    -> uloží se sama; jinak vrátí kandidáty a uživatel potvrdí přes set-page. Jedno placené hledání."""
    try:
        cands = provider_ads.find_page(rec["name"], rec.get("web", ""), country=country)
    except Exception as e:
        return {"stranka": f"dohledání selhalo: {e}"}
    if not cands:
        return {"stranka": "v knihovně reklam nic pod tímto jménem — buď neinzeruje, nebo jiný název stránky"}
    best = cands[0]
    clear = best["to_domain"] > 0 and (len(cands) == 1 or best["shoda"] > cands[1]["shoda"])
    if clear:
        rec["fb_page_id"], rec["fb_page_url"] = best["page_id"], best["page_url"]
        return {"stranka": f"{best['page_name']} ({best['page_url']}) — {best['to_domain']} reklam vede na jeho web, uloženo"}
    return {"stranka": "nejednoznačné — potvrďte: tracker.py set-page --brand <slug> --page <URL stránky>",
            "kandidati": cands[:5]}


def cmd_find_page(a):
    _require_paid_confirmation(a)
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    _require_paid_budget(wl)
    b = next((x for x in wl["brands"] if x["slug"] == a.brand), None)
    if not b: sys.exit(f"Značka „{a.brand}“ není ve watchlistu.")
    if b.get("web") and not b.get("footprint"):
        b["footprint"] = provider_web.ad_footprint(b["web"])
    res = _resolve_page(b, wl.get("country", "CZ"))
    _save(_p(a.root, "watchlist.json"), wl)
    print(json.dumps({"brand": a.brand, "inzeruje_na": (b.get("footprint") or {}).get("platforms", []), **res},
                     ensure_ascii=False, indent=1))


def cmd_set_page(a):
    """Uloží potvrzenou FB stránku (URL nebo page_id) -> knihovna reklam se ptá na ni, ne na slovo."""
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    b = next((x for x in wl["brands"] if x["slug"] == a.brand), None)
    if not b: sys.exit(f"Značka „{a.brand}“ není ve watchlistu.")
    try:
        page_url, page_id = provider_ads.normalize_facebook_page(a.page)
    except ValueError as exc:
        sys.exit(str(exc))
    b["fb_page_url"] = page_url
    b["fb_page_id"] = page_id or b.get("fb_page_id", "")
    _save(_p(a.root, "watchlist.json"), wl)
    print(json.dumps({"ok": True, "slug": a.brand, "fb_page_url": b["fb_page_url"]}, ensure_ascii=False))


# ---------- patrol ----------

def _latest_snapshot(root, slug, before=None):
    d = _p(root, "history", slug)
    try:
        snaps = sorted(f for f in os.listdir(d) if f.startswith("ads-") and f.endswith(".json"))
    except FileNotFoundError:
        return None, None
    if before:
        snaps = [s for s in snaps if s < f"ads-{before}.json"]
    if not snaps: return None, None
    path = _p(d, snaps[-1])
    return _load(path, None), snaps[-1][4:-5]


def _q(s):
    """České uvozovky + neutralizace markdown syntaxe (hook z cizí reklamy jde do firemní wiki)."""
    s = str(s or "").replace("`", "ʼ").replace("[", "(").replace("]", ")").replace("#", "＃")
    return "„" + s + "“"


def _reach_note(v):
    return f" · dosah v EU ~{v:,} lidí".replace(",", " ") if isinstance(v, int) and v > 0 else ""


def _write_profile_md(root, brand, profile, events):
    """Wiki-ingestible profil značky (štítek: konkurence). Agregát, ne eventový šum."""
    lines = [f"# {brand['name']} — profil konkurenta", "",
             f"Štítky: `konkurence` · sledováno Stopařem konkurence · aktualizováno {profile.get('updated', '')}", "",
             f"- **Aktivní kreativy:** {profile.get('active_creatives', 0)} "
             f"({profile.get('active_placements', 0)} placementů)",
             f"- **Nejdéle běžící reklama:** {profile.get('oldest_days', 0)} dní"]
    if profile.get("eu_reach_total"):
        lines.append(f"- **Součet dosahu v EU (aktivní reklamy):** ~{profile['eu_reach_total']:,} lidí".replace(",", " "))
    lines += [f"- **Web:** {brand.get('web') or '—'}", ""]
    if profile.get("evergreens"):
        lines += ["## Evergreeny (30+ dní — za tohle dál platí)", ""]
        lines += [f"- {_q(e['hook'])} — {e['days']} dní{_reach_note(e.get('eu_reach'))}"
                  for e in profile["evergreens"][:6]] + [""]
    if profile.get("top_by_reach"):
        lines += ["## Největší dosah v EU", ""]
        lines += [f"- {_q(t['hook'])} — ~{t['eu_reach']:,} lidí".replace(",", " ") + f" ({t['days']} dní)"
                  for t in profile["top_by_reach"][:5]] + [""]
    if profile.get("top_hooks"):
        lines += ["## Aktuální hooky", ""] + [f"- {_q(h)}" for h in profile["top_hooks"][:6]] + [""]
    recent = [e for e in events if e["type"] in ("NEW", "RERUN", "KILLED", "VELOCITY", "MILESTONE")][:6]
    if recent:
        lines += ["## Poslední změny", ""]
        lines += [f"- {e['date']} · {e['type']}: {_q(e.get('hook') or e.get('note', ''))}" for e in recent] + [""]
    lines += ["---", "*Délka běhu = ukazatel, za co inzerent dál platí. Dosah v EU = reálné číslo "
              "z DSA transparentnosti; přesnou útratu knihovna reklam neukazuje.*"]
    path = _p(root, "profiles", f"{brand['slug']}.md")
    _save_text(path, "\n".join(lines))
    return path


def _is_due(snapshot, days, label):
    if not snapshot:
        return True
    fetched = str(snapshot.get("fetched") or "").strip()
    if not fetched:
        return True
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(fetched)).days >= days
    except ValueError as exc:
        raise StateCorruptError(f"Neplatné datum 'fetched' ve stavu {label}: {fetched!r}.") from exc


def _paid_call_plan(root, brands, deep, watchlist, today=None, force=False):
    """Conservative actor-call envelope; no provider request is made here."""
    totals = {}
    today = today or _today()
    planned_brands = 0

    def add(source, minimum=1, maximum=1):
        row = totals.setdefault(source, {"source": source, "minimum": 0, "maximum": 0})
        row["minimum"] += minimum
        row["maximum"] += maximum

    for brand in brands:
        if not force and os.path.exists(_p(root, "history", brand["slug"], f"ads-{today}.json")):
            continue
        planned_brands += 1
        add("Meta Ad Library", maximum=len(provider_ads.actor_chain()))
        if deep:
            add("Meta detail", minimum=0, maximum=1)
        add("Google Ads Transparency", maximum=len(provider_extras.configured_chain("google_ads")))
        add("LinkedIn Ad Library", maximum=len(provider_extras.configured_chain("linkedin_ads")))
        if brand.get("youtube"):
            add("YouTube", maximum=len(provider_extras.configured_chain("youtube")))
        if brand.get("facebook"):
            add("Facebook příspěvky", maximum=len(provider_extras.configured_chain("facebook")))
        if brand.get("instagram"):
            add("Instagram příspěvky", maximum=len(provider_extras.configured_chain("instagram")))
        if brand.get("linkedin"):
            add("LinkedIn příspěvky", maximum=len(provider_extras.configured_chain("linkedin_posts")))
        reviews = _load(_p(root, "history", brand["slug"], "reviews.json"), None)
        if brand.get("maps_place") and _is_due(reviews, 28, f"recenzí značky {brand['slug']}"):
            add("Google Maps recenze", maximum=len(provider_extras.configured_chain("reviews")))

    serp = _load(_p(root, "serp.json"), None)
    if planned_brands and watchlist.get("keywords") and _is_due(serp, 28, "SERP"):
        chain_len = len(provider_extras.configured_chain("serp"))
        for _ in watchlist["keywords"][:5]:
            add("Google SERP", maximum=chain_len)

    rows = list(totals.values())
    return {
        "minimum": sum(row["minimum"] for row in rows),
        "maximum": sum(row["maximum"] for row in rows),
        "sources": rows,
        "note": "Počty jsou jen pro patrol; setup lookupy find-page/find-place nejsou zahrnuté. "
                "Maximum počítá nakonfigurované zálohy a cena actorů se může měnit.",
    }


def cmd_patrol(a):
    try:
        with _patrol_lock(a.root):
            return _cmd_patrol_locked(a)
    except PatrolAlreadyRunning as exc:
        sys.exit(str(exc))


def _cmd_patrol_locked(a):
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    brands = [b for b in wl["brands"] if not a.brand or b["slug"] == a.brand]
    if not brands: sys.exit("Watchlist je prázdný (tracker.py add-brand) nebo slug nesedí.")
    if a.fixture_dir:
        try:
            _validate_fixture_root(a.root)
        except ValueError as exc:
            sys.exit(str(exc))
    try:
        cap = _bounded_int(
            a.cap or wl.get("caps", {}).get("ads_per_brand", 50),
            MIN_ADS_PER_BRAND,
            MAX_ADS_PER_BRAND,
            "Limit reklam na značku",
        )
        deep = int(a.deep)
        if deep != 0:
            deep = _bounded_int(deep, provider_ads.MIN_CAP, MAX_DEEP_CREATIVES, "Počet detailů kreativ")
    except (TypeError, ValueError) as exc:
        sys.exit(str(exc))
    try:
        country = _country_code(a.country or wl.get("country", "CZ"))
    except ValueError as exc:
        sys.exit(str(exc))
    today, week = _today(), _week()
    digest_dir = _p(a.root, "digest", week)
    summary_path = _p(digest_dir, "summary.json")
    existing_summary = _load(summary_path, None)

    # A repeated scheduled/manual invocation on the same day must not spend,
    # rebuild, or overwrite the earlier board with an empty "quiet" result.
    if (not a.dry_run and not a.force and existing_summary
            and existing_summary.get("generated") == today):
        selected = {brand["slug"] for brand in brands}
        cached_brands = [
            brand for brand in existing_summary.get("brands", [])
            if brand.get("slug") in selected
        ]
        if len(cached_brands) == len(brands):
            print(json.dumps({
                "ok": True,
                "cached": True,
                "board": existing_summary.get("board") or _p(digest_dir, "index.html"),
                "summary": summary_path,
                "quiet": bool(existing_summary.get("quiet")),
                "complete": bool(existing_summary.get("complete")),
                "sources_unavailable": existing_summary.get("sources_unavailable") or [],
                "events_total": existing_summary.get("events_total", 0),
            }, ensure_ascii=False))
            return

    # This is a fail-closed pre-run guard against the provider account's current
    # monthly usage, not a transactional billing limit. Apify remains the source
    # of truth for an absolute account cap and actor prices.
    if a.fixture_dir:
        budget = _positive_budget(
            (wl.get("caps") or {}).get("apify_monthly_usd", DEFAULT_APIFY_MONTHLY_USD)
        )
        guard = {
            "ok": True,
            "code": "",
            "reason": "",
            "has_key": False,
            "budget": {
                "limit_usd": budget,
                "effective_limit_usd": budget,
                "provider_limit_usd": None,
                "used_usd": None,
                "stav": "fixture",
                "guarantee": "Fixture režim nevolá provider.",
            },
        }
    else:
        guard = _paid_budget_guard(wl)

    has_apify_key = bool(guard["has_key"])
    paid_ok = bool(guard["ok"])
    budget_allows_paid = paid_ok
    paid_skip_code = str(guard["code"] or "")
    paid_skip_reason = str(guard["reason"] or "")
    rozpocet = guard["budget"]

    if paid_ok and rozpocet.get("stav") == "nad 80 %":
        print(
            f"[rozpočet] Pozor: Apify tento měsíc {rozpocet['used_usd']:.2f} z "
            f"{rozpocet['effective_limit_usd']:.2f} USD (>80 %).",
            file=sys.stderr,
        )

    if paid_ok and not a.dry_run and not a.fixture_dir and not getattr(a, "confirm_paid", False):
        paid_ok = False
        paid_skip_code = "approval_required"
        paid_skip_reason = "chybí potvrzení placeného běhu (--confirm-paid)"
        rozpocet["stav"] = "čeká na potvrzení"

    try:
        call_plan = ({
            "minimum": 0,
            "maximum": 0,
            "sources": [],
            "note": "Fixture režim nevolá Apify actory.",
        } if a.fixture_dir else _paid_call_plan(a.root, brands, deep, wl, today=today, force=a.force))
    except provider_ads.SourceError as exc:
        call_plan = {
            "minimum": 0,
            "maximum": 0,
            "sources": [],
            "error": str(exc),
            "note": "Plán placených zdrojů je neplatný; žádný actor se nespustí.",
        }
        budget_allows_paid = False
        if paid_ok:
            paid_ok = False
            paid_skip_code = "invalid_provider_config"
            paid_skip_reason = str(exc)
            rozpocet["stav"] = "neplatné nastavení zdroje"
    call_plan["will_execute"] = bool(not a.dry_run and not a.fixture_dir and paid_ok)
    call_plan["would_execute_after_confirmation"] = bool(not a.fixture_dir and budget_allows_paid)

    if paid_skip_reason:
        print(
            f"[rozpočet] {paid_skip_reason} — všechny placené zdroje vynechávám; "
            "rejstřík a veřejný web pokračují.",
            file=sys.stderr,
        )

    if a.dry_run:
        plan = [{"brand": b["name"], "dotaz": b.get("fb_page_url") or b["ad_library"],
                 "rezim": "stránka (jen její reklamy)" if b.get("fb_page_url") else "slovo + filtr inzerenta",
                 "country": country, "cap": cap,
                 "posledni_snimek": _latest_snapshot(a.root, b["slug"])[1] or "žádný (baseline)"} for b in brands]
        print(json.dumps({"dry_run": True, "actor": provider_ads.ACTOR,
                          "apify_actor_calls": call_plan,
                          "deep_reach": f"top {deep} kreativ/značku (EU dosah + cílení)" if deep else "vypnuto",
                          "rozpocet": rozpocet,
                          "plan": plan,
                          "klic_nalezen": has_apify_key,
                          "paid_skip_code": paid_skip_code or None,
                          "paid_skip_reason": paid_skip_reason or None}, ensure_ascii=False, indent=1))
        return

    # Režim bez ověřeného placeného přístupu: placené zdroje se vynechají, ale úřední
    # stopa (rejstřík, zdarma) a Wayback jedou dál — tracker má hodnotu i bez klíče.
    ads_enabled = bool(a.fixture_dir) or paid_ok
    if not ads_enabled:
        print(f"[patrol] Placené zdroje vypnuté: {paid_skip_reason}.", file=sys.stderr)

    os.makedirs(digest_dir, exist_ok=True)
    summary, all_events = {
        "week": week,
        "generated": today,
        "brands": [],
        "quiet": True,
        "paid_sources": {
            "enabled": bool(not a.fixture_dir and paid_ok),
            "fixture": bool(a.fixture_dir),
            "skip_code": paid_skip_code or None,
            "skip_reason": paid_skip_reason or None,
            "budget": rozpocet,
            "actor_calls": call_plan,
        },
    }, []

    def _append_events(evs):
        _append_jsonl(_p(a.root, "events.jsonl"), evs)

    def _registry_wayback(b):
        """Úřední stopa (rejstřík per trh, zdarma) + Wayback cold-start. Nezávislé na Apify."""
        evs, slug = [], b["slug"]

        def _vypadek(zdroj, detail):
            """Zdroj se nedíval. Bez tohohle by výpadek ARESu vypadal jako
            „u konkurence se nic úředního nestalo" — a insolvence je ALERT."""
            evs.append({"date": today, "brand": slug, "type": "SOURCE_UNAVAILABLE",
                        "note": f"{zdroj}: {detail} Tenhle zdroj tento týden nekontroluji — "
                                f"„nic nového“ se ho netýká.", "severity": "info"})
            print(f"[{zdroj}] {slug}: VÝPADEK — {detail}", file=sys.stderr)

        if b.get("ico") and country in provider_registry.SUPPORTED:   # nepodporovaný trh = tiché vynechání (viz SKILL)
            cur = provider_registry.fetch(b["ico"], country)
            if not cur:
                _vypadek("Obchodní rejstřík", "zdroj neodpověděl.")
            if cur:
                rpath = _p(a.root, "history", slug, "registry.json")
                prev = _load(rpath, None)
                if prev:
                    for typ, note, sev in provider_registry.diff(prev, cur):
                        evs.append({"date": today, "brand": slug, "type": typ, "note": note, "severity": sev})
                else:
                    evs.append({"date": today, "brand": slug, "type": "REGISTRY",
                                "note": f"Úřední stopa založena: {cur['name']} (IČO {cur['ico']}), "
                                        f"od {cur.get('established', '?')}, vedení: "
                                        f"{', '.join(cur.get('executives', [])[:4]) or '—'}. Hlídám změny.",
                                "links": ([f"https://ares.gov.cz/ekonomicke-subjekty?ico={cur['ico']}"]
                                          if cur.get("ico") else [])})
                _save(rpath, cur)
        if b.get("ico") and country == "CZ":
            try:  # Sbírka listin (justice.cz, zdarma) — závěrky mohou obsahovat údaje o hospodaření
                fl = provider_registry.filings(b["ico"])
                if fl is None:
                    _vypadek("Sbírka listin", "zdroj neodpověděl nebo subjekt nebyl dohledán.")
                else:
                    fpath = _p(a.root, "history", slug, "filings.json")
                    prev_ids = [f["id"] for f in _load(fpath, {"filings": []})["filings"]]
                    for note, valuable in provider_registry.diff_filings(prev_ids, fl):
                        if prev_ids:  # první běh = baseline, bez spamu 55 listin
                            evs.append({"date": today, "brand": slug, "type": "FILING", "note": note,
                                        "severity": "info" if not valuable else "alert"})
                    _save(fpath, {"filings": fl, "fetched": today})
            except StateCorruptError:
                raise
            except Exception as e:
                _vypadek("Sbírka listin", f"{e}.")
        wpath = _p(a.root, "history", slug, "wayback.json")
        if b.get("web") and not os.path.exists(wpath):
            h = provider_wayback.history(b["web"])
            if h is None:
                _vypadek("Webový archiv", "historii webu se nepodařilo načíst.")
            else:
                _save(wpath, h)
                if h.get("snapshots"):
                    evs.append({"date": today, "brand": slug, "type": "WAYBACK",
                                "note": f"Historie webu: {h['snapshots']} archivních snímků "
                                        f"od {str(h.get('first', ''))[:4]} — vývoj nabídky k porovnání.",
                                "links": [q["url"] for q in h.get("quarterly", [])[:3]]})
        return evs

    def _ev(slug, typ, note, **extra):
        return {"date": today, "brand": slug, "type": typ, "note": note, **extra}

    def _extra_sources(b, run_paid, run_web):
        """F2–F4 zdroje: web+blog (zdarma) · Google/LinkedIn ads (týdně) · recenze (měsíčně).

        Každý zdroj má fallback chain (provider_extras). Když padne CELÝ řetěz, NEML­ČÍME:
        zapíšeme SOURCE_UNAVAILABLE event. Jinak by rozbitý scraper vypadal v reportu
        stejně jako klidný týden — a klient by četl „konkurence nic nedělá", zatímco
        jsme se ve skutečnosti nedívali. Tichý týden smí být jen ověřené ticho."""
        evs, slug = [], b["slug"]
        hist = lambda name: _p(a.root, "history", slug, name)  # noqa: E731

        def _unavailable(zdroj, e):
            evs.append(_ev(slug, "SOURCE_UNAVAILABLE",
                           f"{zdroj}: {_human_err(e)} Tento zdroj tento týden nekontroluji, "
                           f"„nic nového“ se ho netýká.", severity="info"))
            print(f"[{zdroj}] {slug}: VÝPADEK — {e}", file=sys.stderr)
        if run_web:
            try:
                # homepage + SLEDOVANÉ STRÁNKY (max 10/značku — ceník, kategorie, klíčové landing)
                pages = ([b["web"]] if b.get("web") else []) + (b.get("watch_urls") or [])[:10]
                for i, url in enumerate(dict.fromkeys(pages)):
                    key = "web.json" if i == 0 else f"web-{hashlib.sha1(url.encode()).hexdigest()[:8]}.json"
                    where = "Web" if i == 0 else f"Stránka {url.split('//')[-1][:60]}"
                    try:
                        cur = provider_web.snapshot(url)
                    except provider_web.UnsafeURL as e:
                        # Do watchlistu se dostala adresa, která dnes neprojde kontrolou
                        # (např. doména začala mířit dovnitř). Nestahovat, ale nahlásit.
                        _unavailable(where, e)
                        continue
                    except provider_web.WebUnavailable as e:
                        # Tohle je ta díra, kvůli které report psal „beze změn",
                        # zatímco web byl celý týden nedostupný.
                        _unavailable(where, e)
                        continue
                    if not cur: continue
                    for n in provider_web.diff_web(_load(hist(key), None), cur):
                        evs.append(_ev(slug, "WEB_CHANGE", f"{where}: {n}",
                                       links=([where] if str(where).startswith("http") else []),
                                       cards=_page_cards([where], n=1)))
                    _save(hist(key), cur)
                if b.get("web"):
                    urls = provider_web.sitemap_urls(b["web"])
                    if urls:
                        prev_urls = _load(hist("blog-urls.json"), None)
                        if prev_urls is not None:
                            c = provider_web.categorize_new(prev_urls, urls)
                            def _sl(us): return ", ".join(u.rstrip("/").rsplit("/", 1)[-1][:40] for u in us[:3])
                            if c["blog"]:
                                evs.append(_ev(slug, "BLOG_NEW",
                                               f"{len(c['blog'])} nového obsahu (např. {_sl(c['blog'])})", links=c["blog"][:5],
                                               cards=_page_cards(c["blog"])))
                            if c["pages"]:
                                evs.append(_ev(slug, "CONTENT_NEW",
                                               f"{len(c['pages'])} nových stránek na webu (např. {_sl(c['pages'])})", links=c["pages"][:5],
                                               cards=_page_cards(c["pages"])))
                            if c["jobs"]:
                                evs.append(_ev(slug, "JOBS_NEW",
                                               f"{len(c['jobs'])} nových kariérních stránek — náborový signál", links=c["jobs"],
                                               cards=_page_cards(c["jobs"], n=2)))
                            if c["bulk"] >= 30:
                                evs.append(_ev(slug, "CONTENT_NEW",
                                               f"~{c['bulk']} nových produktových/katalogových URL — hýbou sortimentem "
                                               f"(detailní produktová hlídka je mimo záběr trackeru)"))
                        _save(hist("blog-urls.json"), urls)
            except StateCorruptError:
                raise
            except Exception as e:
                _unavailable("Web", e)
        if run_paid:
            try:  # Google Ads Transparency — agregát
                cur = provider_extras.google_ads(b.get("web") or b["ad_library"], region=country)
                for n in provider_extras.diff_google(_load(hist("google.json"), None), cur):
                    _gd = re.sub(r"^https?://(www\.)?", "", b.get("web") or "").split("/")[0]
                    evs.append(_ev(slug, "GOOGLE_ADS", n, links=(
                        [f"https://adstransparency.google.com/?region={country}&domain={_gd}"] if _gd else [])))
                if cur: _save(hist("google.json"), cur)
            except provider_ads.SourceError as e:
                _unavailable("Google reklamy", e)
            except StateCorruptError:
                raise
            except Exception as e:
                _unavailable("Google reklamy", e)
            try:  # LinkedIn Ad Library — B2B
                cur = provider_extras.linkedin_ads(b["name"])
                for n in provider_extras.diff_linkedin(_load(hist("linkedin.json"), None), cur):
                    evs.append(_ev(slug, "LINKEDIN_ADS", n, links=[
                        "https://www.linkedin.com/ad-library/search?companyName=" + b["name"].replace(" ", "%20")]))
                if cur: _save(hist("linkedin.json"), cur)
            except provider_ads.SourceError as e:
                _unavailable("LinkedIn reklamy", e)
            except StateCorruptError:
                raise
            except Exception as e:
                _unavailable("LinkedIn reklamy", e)
            if b.get("youtube"):
                try:  # YouTube kanál — organika bez ToS problému
                    vids = provider_extras.youtube_channel(b["youtube"])
                    ypath = hist("youtube.json")
                    prev_y = _load(ypath, None)
                    if prev_y is not None:
                        for note, links in provider_extras.diff_youtube(prev_y.get("ids", []), vids):
                            evs.append(_ev(slug, "YOUTUBE", note, links=links))
                    if vids:
                        _save(ypath, {"ids": [v["id"] for v in vids], "videos": vids,
                                      "fetched": today})
                except provider_ads.SourceError as e:
                    _unavailable("YouTube", e)
                except StateCorruptError:
                    raise
                except Exception as e:
                    _unavailable("YouTube", e)
            _social_base = []   # (síť, počet, URL profilu) na prvním snímku -> jeden souhrnný event
            _prof = {"facebook": "https://www.facebook.com/{}", "instagram": "https://www.instagram.com/{}/",
                     "linkedin": "https://www.linkedin.com/company/{}/"}
            for _net, _fn, _lbl in (("facebook", provider_extras.facebook_posts, "Facebook"),
                                    ("instagram", provider_extras.instagram_posts, "Instagram"),
                                    ("linkedin", provider_extras.linkedin_posts, "LinkedIn")):
                if not b.get(_net):
                    continue
                try:  # sociální sítě — organika z profilu konkurenta (per-profile, stejný vzor jako YouTube)
                    posts = _fn(b[_net])
                    spath = hist(f"social-{_net}.json")
                    prev_s = _load(spath, None)
                    if prev_s is not None:
                        for note, links in provider_extras.diff_social(prev_s.get("ids", []), posts, _lbl):
                            evs.append(_ev(slug, "SOCIAL_NEW", note, links=links))
                    elif posts:  # první běh = baseline: bez diffu, ale řekneme, co se sbírá
                        h = str(b[_net]).strip()
                        url = h if h.startswith("http") else _prof[_net].format(h.rstrip("/").split("/")[-1].lstrip("@"))
                        _social_base.append((_lbl, len(posts), url))
                    if posts:
                        _save(spath, {"ids": [p["id"] for p in posts], "posts": posts, "fetched": today})
                except provider_ads.SourceError as e:
                    _unavailable(f"{_lbl} příspěvky", e)
                except StateCorruptError:
                    raise
                except Exception as e:
                    _unavailable(f"{_lbl} příspěvky", e)
            if _social_base:
                _parts = " · ".join(f"{l} {n}" for l, n, _ in _social_base)
                evs.append(_ev(slug, "SOCIAL_BASELINE",
                               f"První snímek sítí: {_parts} příspěvků — od příště hlásím jen nové.",
                               links=[u for _, _, u in _social_base], count=sum(n for _, n, _ in _social_base)))
            if b.get("maps_place"):
                try:  # recenze — MĚSÍČNĚ, jen z klientem potvrzeného místa
                    prevr = _load(hist("reviews.json"), None)
                    stale = _is_due(prevr, 28, f"recenzí značky {slug}")
                    if stale:
                        loc = {"CZ": "Czechia", "SK": "Slovakia", "ES": "Spain"}.get(country, "Czechia")
                        cur = provider_extras.reviews(b["name"], location=loc,
                                                      place=b["maps_place"], web=b.get("web"))
                        _rl = [cur["maps_url"]] if cur and cur.get("maps_url") else []
                        for n in provider_extras.diff_reviews(prevr, cur):
                            evs.append(_ev(slug, "REVIEWS", n, links=_rl))
                        if cur: _save(hist("reviews.json"), cur)
                except provider_ads.SourceError as e:
                    _unavailable("Recenze", e)
                except StateCorruptError:
                    raise
                except Exception as e:
                    _unavailable("Recenze", e)
        return evs

    def _brand_entry(b, profile, events, dropped=0, prev_date=None, note="", ads=None):
        return {"slug": b["slug"], "name": b["name"], "active": profile.get("active_creatives", 0),
                "oldest": profile.get("oldest_days", 0), "dropped": dropped,
                "events": events, "evergreens": profile.get("evergreens", [])[:3],
                "top_creatives": board.top_creatives(ads or []),   # pás náhledů v kartě (i při baseline)
                "dest_cards": [] if a.fixture_dir else _dest_cards(ads or []),   # kam posílají reklamy (karty stránek)
                "footprint": (b.get("footprint") or {}).get("platforms", []), "fb_page_url": b.get("fb_page_url", ""),
                "prev_snapshot": prev_date or "baseline", "note": note}

    fresh_patrol = False
    for b in brands:
        slug = b["slug"]
        profile = _load(_p(a.root, "history", slug, "profile.json"), {"brand": b["name"], "slug": slug})
        snap_path = _p(a.root, "history", slug, f"ads-{today}.json")
        forced_rerun = os.path.exists(snap_path) and a.force

        # Úřední stopa + Wayback — zdarma, běží VŽDY (i bez Apify klíče, i při výpadku ads zdroje)
        same_day = os.path.exists(snap_path) and not a.force
        reg_events = [] if a.fixture_dir else _registry_wayback(b)
        # F2–F4 zdroje: web/blog zdarma, Google/LinkedIn/recenze jen s klíčem; same-day neplatí dvakrát
        if not a.fixture_dir and not same_day:
            reg_events += _extra_sources(b, run_paid=paid_ok, run_web=True)
        if reg_events:
            _append_events(reg_events); all_events.extend(reg_events)
            summary["quiet"] = False

        # Dnešní kompletní snímek má přednost i v případě, že se klíč nebo rozpočet
        # mezitím změnil. Nevoláme znovu a nepředstíráme nový neúplný běh.
        if same_day:
            cached_entry = next(
                (entry for entry in (existing_summary or {}).get("brands", []) if entry.get("slug") == slug),
                None,
            )
            if cached_entry:
                summary["brands"].append(cached_entry)
                cached_events = cached_entry.get("events") or []
                all_events.extend(cached_events)
                if any(event.get("type") != "QUIET" for event in cached_events):
                    summary["quiet"] = False
            else:
                stale = _ev(
                    slug,
                    "SOURCE_STALE",
                    "Dnešní snímek existuje, ale chybí k němu uložený souhrn. "
                    "Ponechávám soubory beze změny; použijte --force až po kontrole.",
                )
                all_events.append(stale)
                summary["quiet"] = False
                summary["brands"].append(_brand_entry(b, profile, reg_events + [stale]))
            print(f"[patrol] {b['name']}: přeskočeno (dnes už proběhlo)", file=sys.stderr)
            continue

        fresh_patrol = True

        # Bez ověřeného placeného přístupu jedou dál jen bezplatné zdroje. Stav
        # musí být viditelný v JSON i HTML a celý běh nesmí být označen za úplný.
        if not ads_enabled:
            skipped = _ev(
                slug,
                "SOURCE_SKIPPED",
                f"Placené zdroje přeskočeny: {paid_skip_reason}.",
                severity="info",
                reason_code=paid_skip_code,
            )
            _append_events([skipped])
            all_events.append(skipped)
            summary["quiet"] = False
            summary["brands"].append(_brand_entry(
                b, profile, reg_events + [skipped], note=paid_skip_reason,
            ))
            continue

        # Idempotence (same-day): dnešní snímek už existuje -> nediffuj znovu (duplicitní eventy,
        # rozbitá velocity základna). --force přepíše snapshot, ale eventy stejně neduplikuje.
        prev_snap, prev_date = _latest_snapshot(a.root, slug, before=today)

        # Per-značka error handling: jeden padlý zdroj NIKDY neshodí celý týdenní běh.
        try:
            if a.fixture_dir:
                raw = _load(_p(a.fixture_dir, f"{slug}.json"), [])
            else:
                # stránka (čisté, jen její reklamy) má přednost před slovem (šum cizích inzerentů)
                raw = provider_ads.pull(b.get("fb_page_url") or b["ad_library"], country=country, cap=cap)
            ads = [provider_ads.normalize(x) for x in raw]
            ads, dropped = (ads, 0) if b.get("fb_page_url") else provider_ads.filter_to_brand(ads, b["name"])
        except StateCorruptError:
            raise
        except Exception as e:
            ev = [{"date": today, "brand": slug, "type": "SOURCE_STALE", "note": str(e)
                   + " Ponechávám poslední známý stav."}]
            _append_events(ev); all_events.extend(ev)
            summary["source_stale"] = True
            summary["brands"].append(_brand_entry(b, profile, reg_events + ev, prev_date=prev_date, note=str(e)))
            print(f"[patrol] {b['name']}: VÝPADEK ZDROJE — {e}", file=sys.stderr)
            continue

        # Knihovna něco vrátila, ale nic od potvrzeného inzerenta. Takový výsledek
        # není ověřené prázdno: neukládat falešnou baseline a nehlásit ticho.
        no_match = (not ads) and dropped > 0
        if no_match:
            ev = [_ev(
                slug,
                "SOURCE_STALE",
                f"Knihovna vrátila {dropped} reklam jiných inzerentů a žádnou potvrzenou shodu pro "
                f"„{b['name']}“. Nezakládám prázdný snímek; ověřte stránku přes find-page --confirm-paid "
                "a uložte ji přes set-page.",
            )]
            _append_events(ev)
            all_events.extend(ev)
            summary["source_stale"] = True
            summary["quiet"] = False
            summary["brands"].append(_brand_entry(b, profile, reg_events + ev, dropped, prev_date))
            continue

        # Guard proti falešné vlně KILLED->RERUN: prázdný/zkolabovaný výsledek u značky,
        # co minule měla kreativy, je skoro jistě výpadek zdroje, ne reálné vypnutí všeho.
        prev_ads_g = prev_snap["ads"] if prev_snap else None
        if prev_ads_g is not None:
            n_prev = len(diff_engine.dedupe(prev_ads_g)); n_curr = len(diff_engine.dedupe(ads))
            # n_prev == 0: značka neinzerovala ani minule -> 0 dnes je normální, ne výpadek.
            # no_match s neprázdnou minulostí = drift dotazu -> držíme poslední stav (žádná vlna KILLED).
            if n_prev > 0 and (n_curr == 0 or (n_prev >= 5 and n_curr < 0.2 * n_prev)):
                ev = [{"date": today, "brand": slug, "type": "SOURCE_STALE",
                       "note": f"Zdroj vrátil {n_curr} kreativ (minule {n_prev}) — vypadá to na výpadek, "
                               f"ne na reálné vypnutí. Ponechávám poslední známý stav, ověřím příště."}]
                _append_events(ev); all_events.extend(ev)
                summary["source_stale"] = True
                summary["brands"].append(_brand_entry(b, profile, reg_events + ev, dropped, prev_date))
                print(f"[patrol] {b['name']}: KOLAPS VÝSLEDKŮ ({n_curr} vs {n_prev}) — přeskakuji diff", file=sys.stderr)
                continue

        # Deep enrich: EU dosah + cílení žijí jen na DETAILU reklamy (pilot 2026-07-10).
        # Druhý call: týž dotaz s detaily, řazený dle impresí -> top-N „money ads" značky.
        if deep and ads and not a.fixture_dir:
            try:
                det = provider_ads.enrich_details(
                    b.get("fb_page_url") or b["ad_library"], country=country, deep=deep,
                )
            except provider_ads.SourceError as exc:
                detail_event = _ev(
                    slug,
                    "SOURCE_UNAVAILABLE",
                    f"Detail reklam: {exc} Seznam kreativ zůstává dostupný, ale dosah a cílení nejsou ověřené.",
                    severity="info",
                )
                _append_events([detail_event])
                all_events.append(detail_event)
                reg_events.append(detail_event)
                summary["quiet"] = False
                det = {}
            except Exception as exc:
                detail_event = _ev(
                    slug,
                    "SOURCE_UNAVAILABLE",
                    f"Detail reklam: {_human_err(exc)} Seznam kreativ zůstává dostupný, "
                    "ale dosah a cílení nejsou ověřené.",
                    severity="info",
                )
                _append_events([detail_event])
                all_events.append(detail_event)
                reg_events.append(detail_event)
                summary["quiet"] = False
                det = {}
            for x in ads:
                d = det.get(str(x["ad_archive_id"]))
                if d:
                    if isinstance(d.get("eu_reach"), int): x["eu_reach"] = d["eu_reach"]
                    if d.get("audience"): x["audience"] = d["audience"]

        _save(snap_path,
              {"date": today, "brand": b["name"], "count": len(ads), "dropped_other_advertisers": dropped, "ads": ads})

        pre_velocity = list(profile.get("velocity_history", []))
        events, profile = diff_engine.diff(slug, today, prev_ads_g, ads, profile)
        if not a.fixture_dir:   # karta cílové stránky reklamy (og:image + titulek) u nových/vrácených kreativ
            for e in events:
                if e["type"] in ("NEW", "RERUN") and e.get("destination"):
                    e["cards"] = _page_cards([e["destination"]], n=1)
        if forced_rerun:
            # --force: nový snímek ano, ale žádné duplicitní eventy v logu ani dvojí velocity záznam
            profile["velocity_history"] = pre_velocity
        else:
            _append_events(events)
        _save(_p(a.root, "history", slug, "profile.json"), profile)
        md = _write_profile_md(a.root, b, profile, events)

        real = [e for e in events if e["type"] not in ("QUIET", "KILLED_SHORT")]
        if real: summary["quiet"] = False
        all_events.extend(events)
        entry = _brand_entry(b, profile, reg_events + events, dropped, prev_date, ads=ads)
        entry["profile_md"] = md
        summary["brands"].append(entry)
        print(f"[patrol] {b['name']}: {len(ads)} kreativ · {len(real)} eventů "
              f"(vs. {prev_date or 'baseline'})", file=sys.stderr)

    # SERP brand-guard (MĚSÍČNĚ, watchlist-level): kdo inzeruje na klientova brandová slova
    serp_events = []
    if fresh_patrol and not a.fixture_dir and paid_ok and wl.get("keywords"):
        sm = _load(_p(a.root, "serp.json"), {"fetched": "2000-01-01", "results": {}})
        if _is_due(sm, 28, "SERP"):
            for kw in wl["keywords"][:5]:
                try:
                    hits = provider_extras.serp_paid(kw, country=country.lower())
                    sm["results"][kw] = hits
                    for n in provider_extras.diff_serp(kw, wl.get("own_web", ""), hits):
                        serp_events.append({"date": today, "brand": "brandova-slova", "type": "SERP_ADS", "note": n,
                                            "links": ["https://www.google.com/search?q=" + str(kw).replace(" ", "+")]})
                except provider_ads.SourceError as e:
                    serp_events.append({"date": today, "brand": "brandova-slova", "type": "SOURCE_UNAVAILABLE",
                                        "note": f"Hlídka brandového slova „{kw}“: {e} "
                                                f"Tenhle zdroj tento měsíc nekontroluji.", "severity": "info"})
                    print(f"[serp] {kw}: VÝPADEK — {e}", file=sys.stderr)
                except Exception as e:
                    serp_events.append({"date": today, "brand": "brandova-slova", "type": "SOURCE_UNAVAILABLE",
                                        "note": f"Hlídka brandového slova „{kw}“: {_human_err(e)} "
                                                f"Tenhle zdroj tento měsíc nekontroluji.", "severity": "info"})
                    print(f"[serp] {kw}: VÝPADEK — {e}", file=sys.stderr)
            sm["fetched"] = today
            _save(_p(a.root, "serp.json"), sm)
    if serp_events:
        _append_jsonl(_p(a.root, "events.jsonl"), serp_events)
        all_events.extend(serp_events); summary["quiet"] = False
        summary["brands"].append({"slug": "brandova-slova", "name": "Vaše brandová slova (SERP)",
                                  "active": 0, "oldest": 0, "events": serp_events, "evergreens": []})

    # Nedostupné zdroje: ticho SMÍ znamenat „konkurence nic nedělá" jen tehdy, když se
    # všechny zdroje opravdu dívaly. Jinak agent musí přiznat neúplnou obchůzku.
    coverage_events = {"SOURCE_UNAVAILABLE", "SOURCE_STALE", "SOURCE_SKIPPED"}
    unavailable = [e for e in all_events if e["type"] in coverage_events]
    summary["sources_unavailable"] = list(dict.fromkeys([
        (e["note"].split(":")[0] if e["type"] in ("SOURCE_UNAVAILABLE", "SOURCE_SKIPPED")
         else f"knihovna reklam Meta ({e.get('brand', '')})")
        for e in unavailable
    ]))
    summary["complete"] = not unavailable

    n_un = len(summary["sources_unavailable"])
    un_txt = ("" if not n_un else
              f" · {n_un} část neověřena" if n_un == 1 else
              f" · {n_un} části neověřeny" if n_un < 5 else
              f" · {n_un} částí neověřeno")
    out_html = board.render(
        week,
        summary["brands"],
        _p(digest_dir, "index.html"),
        generated=f"Snímek {today} · {len(brands)} značek · zdroj Meta Ad Library" + un_txt,
        complete=summary["complete"],
    )
    summary["board"] = out_html
    summary["events_total"] = len([
        e for e in all_events if e["type"] not in ({"QUIET"} | coverage_events)
    ])
    _save(_p(digest_dir, "summary.json"), summary)
    print(json.dumps({"ok": True, "board": out_html,
                      "summary": _p(digest_dir, "summary.json"),
                      "quiet": summary["quiet"],
                      "complete": summary["complete"],
                      "sources_unavailable": summary["sources_unavailable"],
                      "events_total": summary["events_total"]},
                     ensure_ascii=False))


def cmd_add_url(a):
    """Sledovaná stránka konkurenta (ceník, kategorie, landing) — max 10/značku.
    Limit je záměrně nízký: přidání je práce, klient si sám vybere, co ho opravdu zajímá."""
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    b = next((x for x in wl["brands"] if x["slug"] == a.brand), None)
    if not b: sys.exit(f"Značka '{a.brand}' není ve watchlistu.")
    urls = b.setdefault("watch_urls", [])
    # Validace hned při zadání — klient dostane chybu teď, ne až za týden
    # při obchůzce. Zároveň se do watchlistu nedostane vnitřní adresa.
    try:
        u = provider_web.zkontroluj_url(a.url)
    except provider_web.UnsafeURL as e:
        sys.exit(f"Adresu nelze sledovat: {e}")
    if u in urls:
        print(json.dumps({"ok": True, "note": "URL už sledujeme", "count": len(urls)}, ensure_ascii=False)); return
    if len(urls) >= 10:
        sys.exit("Max 10 sledovaných stránek na značku. Nejdřív nějakou odeberte (edit watchlist.json).")
    urls.append(u)
    _save(_p(a.root, "watchlist.json"), wl)
    print(json.dumps({"ok": True, "brand": a.brand, "watch_urls": urls}, ensure_ascii=False))


LOGGABLE = {"NEWSLETTER", "NOTE"}


def cmd_log_event(a):
    """Ručně/agentně pozorovaný signál do event streamu (např. newsletter z CC schránky).
    Validované typy, aby log zůstal konzistentní pro digest/CEO report."""
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    if a.type not in LOGGABLE:
        sys.exit(f"Typ musí být jeden z: {', '.join(sorted(LOGGABLE))}")
    if not any(x["slug"] == a.brand for x in wl["brands"]):
        sys.exit(f"Značka '{a.brand}' není ve watchlistu.")
    e = {"date": _today(), "brand": a.brand, "type": a.type, "note": a.note.strip()[:300]}
    _append_jsonl(_p(a.root, "events.jsonl"), [e])
    print(json.dumps({"ok": True, "event": e}, ensure_ascii=False))


# ---------- add-keyword / battlecard / ceo-report ----------

def cmd_add_keyword(a):
    """Brandová slova klienta pro SERP hlídku (kdo inzeruje na jeho jméno)."""
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    if a.own_web: wl["own_web"] = a.own_web.strip()
    if a.term and a.term.strip() not in wl.setdefault("keywords", []):
        if len(wl["keywords"]) >= 5: sys.exit("Max 5 brandových slov (nákladový cap).")
        wl["keywords"].append(a.term.strip())
    _save(_p(a.root, "watchlist.json"), wl)
    print(json.dumps({"ok": True, "keywords": wl["keywords"], "own_web": wl.get("own_web", "")}, ensure_ascii=False))


def cmd_battlecard(a):
    """Battlecard pro Obchodníka — fakta + slabiny z recenzí + poslední pohyby konkurenta."""
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    b = next((x for x in wl["brands"] if x["slug"] == a.brand), None)
    if not b: sys.exit(f"Značka '{a.brand}' není ve watchlistu.")
    h = lambda n: _load(_p(a.root, "history", a.brand, n), {})  # noqa: E731
    prof, reg, rev = h("profile.json"), h("registry.json"), h("reviews.json")
    try:
        evs = _read_events(_p(a.root, "events.jsonl"))
        evs = [e for e in evs if e.get("brand") == a.brand
               and e["type"] in ("ALERT", "RERUN", "NEW", "KILLED", "REGISTRY_CHANGE", "WEB_CHANGE", "REVIEWS")][-6:]
    except FileNotFoundError:
        evs = []
    L = [f"# Battlecard — {b['name']}", "",
         f"Štítky: `konkurence` `battlecard` · pro AI Obchodníka · aktualizováno {_today()}", "",
         "## Fakta (obchodní rejstřík)"]
    if reg:
        L += [f"- Vedení: {', '.join(reg.get('executives', [])[:4]) or '—'}",
              f"- Vlastníci: {', '.join(reg.get('owners', [])[:3]) or '—'}",
              f"- Od {reg.get('established', '?')} · kapitál {reg.get('capital', '?')}"
              + (" · ⚠ INSOLVENCE hint" if reg.get("flag_insolvence") else "")
              + (" · ⚠ likvidace" if reg.get("flag_likvidace") else "")]
    else:
        L += ["- (rejstřík nesledován — doplňte IČO)"]
    # POZOR: mezerování čísla dělej jen NAD číslem, ne nad celou větou — .replace(",", " ")
    # přes celý řetězec sežere i větné čárky („aktivních, imprese" -> „aktivních  imprese").
    L += ["", "## Reklamní přítomnost",
          f"- Meta: {prof.get('active_creatives', 0)} aktivních kreativ, nejdéle {prof.get('oldest_days', 0)} dní"
          + (f", dosah v EU ~{format(prof['eu_reach_total'], ',').replace(',', ' ')} lidí"
             if prof.get("eu_reach_total") else "")]
    L += [f"- Hlavní sdělení: {_q(hk)}" for hk in (prof.get("top_hooks") or [])[:3]]
    L += ["", "## Slabiny (z veřejných recenzí — použijte v námitkách)"]
    if rev:
        L.append(f"- {rev.get('place', '')}: {rev.get('rating', '?')}★ z {rev.get('count', '?')} recenzí")
        lows = [r for r in rev.get("reviews", []) if isinstance(r.get("stars"), (int, float))
                and r["stars"] <= 2 and r.get("text")]
        L += [f"- Stížnost ({r['stars']}★): {_q(r['text'][:160])}" for r in lows[:3]]
        if not lows: L.append("- (žádné čerstvé negativní recenze — silná stránka konkurenta)")
    else:
        L.append("- (recenze zatím nesbírány)")
    if evs:
        L += ["", "## Poslední pohyby"]
        L += [f"- {e['date']} · {e['type']}: {_q((e.get('note') or e.get('hook', ''))[:140])}" for e in evs]
    L += ["", "## Jak proti nim (doplní AI Obchodník)", "- …", "",
          "---", "*Zdroje: veřejný rejstřík, knihovny reklam (DSA) a veřejné recenze. "
          "Výstup může obsahovat veřejná jména osob ve vedení firmy; používejte je jen pro oprávněný obchodní kontext.*"]
    path = _p(a.root, "battlecards", f"{a.brand}.md")
    _save_text(path, "\n".join(L))
    print(json.dumps({"ok": True, "battlecard": path}, ensure_ascii=False))


def cmd_ceo_report(a):
    """Měsíční strategický roll-up pro AI CEO (board report) — z eventů za posledních 30 dní."""
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    try:
        evs = _read_events(_p(a.root, "events.jsonl"), since=cutoff)
    except FileNotFoundError:
        evs = []
    month = _today()[:7]
    names = {b["slug"]: b["name"] for b in wl["brands"]}
    L = [f"# Konkurence — měsíční přehled pro vedení ({month})", "",
         f"Štítky: `konkurence` `board-report` · období: posledních 30 dní · značek: {len(wl['brands'])}", ""]
    coverage_types = {"SOURCE_STALE", "SOURCE_UNAVAILABLE", "SOURCE_SKIPPED"}
    coverage = [e for e in evs if e.get("type") in coverage_types]
    if coverage:
        L += ["## Neúplné kontroly", ""]
        notes = list(dict.fromkeys(str(e.get("note") or "Neověřený zdroj") for e in coverage))
        L += [f"- {_q(note[:220])}" for note in notes[:8]] + [""]
    alerts = [e for e in evs if e["type"] == "ALERT"]
    if alerts:
        L += ["## 🔴 Zásadní události (vyžadují rozhodnutí)", ""]
        L += [f"- **{names.get(e['brand'], e['brand'])}**: {_q(e['note'])}" for e in alerts] + [""]
    order = ("RERUN", "REGISTRY_CHANGE", "VELOCITY", "SERP_ADS", "WEB_CHANGE", "REVIEWS",
             "GOOGLE_ADS", "LINKEDIN_ADS", "NEW", "KILLED", "BLOG_NEW", "JOBS_NEW", "MILESTONE")
    has_business_events = any(e.get("type") in order or e.get("type") == "ALERT" for e in evs)
    for slug, name in names.items():
        be = sorted((e for e in evs if e.get("brand") == slug and e["type"] in order),
                    key=lambda e: order.index(e["type"]))[:5]
        if not be: continue
        L += [f"## {name}", ""]
        L += [f"- {e['type']}: {_q((e.get('note') or e.get('hook', ''))[:160])}" for e in be] + [""]
    serp = [e for e in evs if e["type"] == "SERP_ADS"]
    if serp:
        L += ["## Vaše brandová slova", ""] + [f"- {_q(e['note'])}" for e in serp[:5]] + [""]
    if not has_business_events and not coverage:
        L += ["Za posledních 30 dní žádné podstatné změny u sledované konkurence — trh je klidný.", ""]
    L += ["---", "*Vygenerováno Stopařem konkurence. Detaily: týdenní digesty a situační přehled.*"]
    path = _p(a.root, "reports", f"{month}.md")
    _save_text(path, "\n".join(L))
    print(json.dumps({"ok": True, "report": path, "alerts": len(alerts), "eventu": len(evs)}, ensure_ascii=False))


# ---------- overview (situační board — z paměti, žádný scrape) ----------

def cmd_overview(a):
    wl = _watchlist(a.root)
    if wl is None: sys.exit("Nejdřív spusť: tracker.py init")
    entries, missing = [], []
    for b in wl["brands"]:
        prof = _load(_p(a.root, "history", b["slug"], "profile.json"), {})
        if not prof.get("updated"):
            missing.append(b["name"])
        entries.append({"name": b["name"], "slug": b["slug"],
                        "active": prof.get("active_creatives", 0),
                        "oldest": prof.get("oldest_days", 0),
                        "updated": prof.get("updated", "zatím bez snímku"),
                        "eu_reach_total": prof.get("eu_reach_total", 0),
                        "evergreens": prof.get("evergreens", []),
                        "top_by_reach": prof.get("top_by_reach", []),
                        "registry": _load(_p(a.root, "history", b["slug"], "registry.json"), {})})
    out_dir = _p(a.root, "overview"); os.makedirs(out_dir, exist_ok=True)
    out = board.render_overview(entries, _p(out_dir, "index.html"),
                                generated=f"Vygenerováno {_today()}, zdarma z uložených dat.")
    print(json.dumps({"ok": True, "board": out, "brands": len(entries),
                      "bez_snimku": missing,
                      "note": "Přehled je z posledních snímků — čerstvá data přes patrol."},
                     ensure_ascii=False, indent=1))


# ---------- status ----------

def cmd_status(a):
    wl = _watchlist(a.root)
    if wl is None:
        print(json.dumps({"initialized": False, "note": "Watchlist neexistuje — režim NASTAVENÍ."},
                         ensure_ascii=False)); return
    out = {"initialized": True, "country": wl.get("country"), "brands": []}
    for b in wl["brands"]:
        prof = _load(_p(a.root, "history", b["slug"], "profile.json"), {})
        out["brands"].append({"slug": b["slug"], "name": b["name"],
                              "updated": prof.get("updated", "nikdy"),
                              "active": prof.get("active_creatives", 0),
                              "oldest_days": prof.get("oldest_days", 0),
                              "evergreens": prof.get("evergreens", [])[:3],
                              "top_hooks": prof.get("top_hooks", [])[:3]})
    tail = _read_events(_p(a.root, "events.jsonl"))[-25:]
    out["recent_events"] = [e for e in tail if e.get("type") not in ("QUIET",)][-12:]
    digests = sorted(os.listdir(_p(a.root, "digest"))) if os.path.isdir(_p(a.root, "digest")) else []
    out["last_digest"] = _p(a.root, "digest", digests[-1], "index.html") if digests else None
    print(json.dumps(out, ensure_ascii=False, indent=1))


def cmd_find_ico(a):
    """Kandidáti z obchodního rejstříku podle jména — klient vybere, my nehádáme."""
    try:
        country = _country_code(a.country)
    except ValueError as exc:
        sys.exit(str(exc))
    cands = provider_registry.search(a.name, country)
    print(json.dumps({"country": country, "candidates": cands,
                      "note": "" if cands or country == "CZ"
                      else f"Trh {country} zatím bez rejstříkového providera "
                           f"(roadmapa: {provider_registry.ROADMAP.get(country, 'zatím bez plánu')})"},
                     ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description="Stopař konkurence — orchestrátor")
    ap.add_argument("--root", default=os.environ.get("COMPETITORS_ROOT", DEFAULT_ROOT))
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init"); i.add_argument("--country", default="CZ"); i.add_argument("--cap", type=int, default=50)
    i.add_argument("--apify-monthly-usd", dest="apify_monthly_usd", type=float,
                   default=DEFAULT_APIFY_MONTHLY_USD,
                   help="kladný měsíční bezpečnostní práh Apify v USD (výchozí 5)")
    f = sub.add_parser("find-ico"); f.add_argument("--name", required=True); f.add_argument("--country", default="CZ")
    b = sub.add_parser("add-brand"); b.add_argument("--name", required=True)
    b.add_argument("--query", default="", help="dotaz do Ad Library (default = name; může být i celá URL)")
    b.add_argument("--ico", default="", help="IČO pro úřední stopu (najdi přes find-ico)")
    b.add_argument("--youtube", default="", help="URL YouTube kanálu konkurenta (organika)")
    b.add_argument("--facebook", default="", help="URL/handle Facebook stránky konkurenta (organika)")
    b.add_argument("--instagram", default="", help="URL/handle Instagram profilu konkurenta (organika)")
    b.add_argument("--linkedin", default="", help="URL LinkedIn company page konkurenta (organika)")
    b.add_argument("--maps", default="", help="potvrzené místo na Google Mapách (URL nebo placeId) pro recenze — viz find-place")
    b.add_argument("--web", default=""); b.add_argument("--note", default="")
    au = sub.add_parser("add-url"); au.add_argument("--brand", required=True); au.add_argument("--url", required=True)
    le = sub.add_parser("log-event"); le.add_argument("--brand", required=True)
    le.add_argument("--type", required=True); le.add_argument("--note", required=True)
    p = sub.add_parser("patrol"); p.add_argument("--brand", default="", help="jen jedna značka (slug)")
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--country", default="")
    p.add_argument("--cap", type=int, default=0); p.add_argument("--fixture-dir", default="")
    p.add_argument("--deep", type=int, default=10,
                   help="kolik top kreativ na značku obohatit detailem (EU dosah + cílení); 0 = vypnout")
    p.add_argument("--force", action="store_true",
                   help="přepiš dnešní snímek (jinak same-day patrol značku přeskočí)")
    p.add_argument("--confirm-paid", action="store_true",
                   help="potvrzuje výslovný souhlas s placenými zdroji tohoto nebo naplánovaného běhu")
    k = sub.add_parser("add-keyword"); k.add_argument("--term", default="")
    k.add_argument("--own-web", dest="own_web", default="", help="vlastní doména klienta (pro SERP diff)")
    bc = sub.add_parser("battlecard"); bc.add_argument("--brand", required=True)
    sub.add_parser("ceo-report")
    sub.add_parser("status")
    sub.add_parser("overview")
    sb = sub.add_parser("set-budget"); sb.add_argument("--usd", type=float, required=True,
                                                       help="nový kladný měsíční bezpečnostní práh Apify v USD")
    fp = sub.add_parser("find-place"); fp.add_argument("--brand", required=True); fp.add_argument("--n", type=int, default=3)
    fp.add_argument("--confirm-paid", action="store_true", help="potvrzuje souhlas s placeným lookupem")
    sp = sub.add_parser("set-place"); sp.add_argument("--brand", required=True); sp.add_argument("--place", required=True)
    fg = sub.add_parser("find-page"); fg.add_argument("--brand", required=True)
    fg.add_argument("--confirm-paid", action="store_true", help="potvrzuje souhlas s placeným lookupem")
    sg = sub.add_parser("set-page"); sg.add_argument("--brand", required=True); sg.add_argument("--page", required=True)
    b.add_argument("--find-page", action="store_true",
                   help="po výslovném souhlasu spustit placené dohledání FB stránky při založení")
    b.add_argument("--confirm-paid", action="store_true", help="potvrzuje souhlas s placeným lookupem")
    b.add_argument("--no-find-page", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    handler = {
        "init": cmd_init,
        "find-ico": cmd_find_ico,
        "add-brand": cmd_add_brand,
        "add-url": cmd_add_url,
        "log-event": cmd_log_event,
        "add-keyword": cmd_add_keyword,
        "battlecard": cmd_battlecard,
        "ceo-report": cmd_ceo_report,
        "patrol": cmd_patrol,
        "status": cmd_status,
        "overview": cmd_overview,
        "set-budget": cmd_set_budget,
        "find-place": cmd_find_place,
        "set-place": cmd_set_place,
        "find-page": cmd_find_page,
        "set-page": cmd_set_page,
    }[a.cmd]
    try:
        handler(a)
    except (StateCorruptError, provider_ads.SourceError) as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
