#!/usr/bin/env python3
"""competitor-tracker — provider ÚŘEDNÍ STOPA (per-trh VÝMĚNNÝ, vše zdarma, bez klíčů).

CZ = ARES v3 REST (ares.gov.cz) — základní záznam + veřejný rejstřík (VR):
statutáři, společníci, kapitál, stav subjektu, likvidace/insolvence hint z ostatních
skutečností. Ověřeno živě 2026-07-10 (Notino).

Jiné trhy = stejný kontrakt, jiný modul (roadmapa: GB = Companies House REST,
zdarma s klíčem CH_API_KEY · ES = Registro Mercantil/BORME). Nepodporovaná země
-> None + česká poznámka (degradace, nikdy neblokuje).

Kontrakt: search(name, country) -> [kandidáti] · fetch(ico, country) -> record | None
          diff(prev, curr) -> [(typ, note, severity)]"""
import http.cookiejar, json, re, sys, urllib.request, urllib.error

ARES = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest"
SUPPORTED = {"CZ"}
ROADMAP = {"GB": "Companies House API (zdarma, klíč CH_API_KEY)", "ES": "Registro Mercantil / BORME",
           "SK": "RPO / ORSR"}


def _get(url, data=None, timeout=30):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "cliqsales-competitor-tracker"},
                                 method="POST" if data else "GET")
    try:
        return json.load(urllib.request.urlopen(req, timeout=timeout))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as e:
        print(f"[registry] {url.split('/rest')[-1][:40]}: {e}", file=sys.stderr)
        return None


def search(name, country="CZ", limit=5):
    """Najdi kandidáty podle jména -> [{ico, name, address}] (klient vybere, nevybíráme sami)."""
    if country != "CZ":
        return []
    d = _get(f"{ARES}/ekonomicke-subjekty/vyhledat", {"obchodniJmeno": name, "pocet": limit})
    return [{"ico": s.get("ico"), "name": s.get("obchodniJmeno"),
             "address": (s.get("sidlo") or {}).get("textovaAdresa", "")}
            for s in (d or {}).get("ekonomickeSubjekty", [])[:limit]]


def _people(members):
    out = []
    for c in members or []:
        if not isinstance(c, dict) or c.get("datumVymazu"):
            continue
        # statutáři mají fyzickaOsoba/pravnickaOsoba přímo, společníci pod klíčem `osoba`
        base = c.get("osoba") if isinstance(c.get("osoba"), dict) else c
        fo = base.get("fyzickaOsoba") if isinstance(base.get("fyzickaOsoba"), dict) else base
        po = base.get("pravnickaOsoba") or {}
        n = " ".join(x for x in (fo.get("jmeno"), fo.get("prijmeni")) if x) \
            or po.get("obchodniJmeno", "") or base.get("obchodniJmeno", "")
        if n: out.append(n)
    return sorted(set(out))


def fetch(ico, country="CZ"):
    """Snapshot úřední stopy firmy. None = trh nepodporovaný nebo zdroj nedostupný."""
    if country not in SUPPORTED:
        return None
    basic = _get(f"{ARES}/ekonomicke-subjekty/{ico}")
    if not basic:
        return None
    vr = _get(f"{ARES}/ekonomicke-subjekty-vr/{ico}") or {}
    z = (vr.get("zaznamy") or [{}])[0]
    execs = []
    for org in z.get("statutarniOrgany") or []:
        execs += _people(org.get("clenoveOrganu"))
    owners = []
    for org in z.get("spolecnici") or []:
        owners += _people(org.get("spolecnik") if isinstance(org, dict) else None)
    owners = sorted(set(owners))
    # hodnota je přímo string (ověřeno živě na VR JSON)
    ost = " ".join(str(o.get("hodnota", "")) for o in z.get("ostatniSkutecnosti") or []
                   if isinstance(o, dict) and not o.get("datumVymazu")).lower()
    kap = ((z.get("zakladniKapital") or [{}])[0].get("vklad") or {}).get("hodnota", "") \
        if isinstance(z.get("zakladniKapital"), list) and z.get("zakladniKapital") else ""
    return {"country": country, "ico": str(ico), "name": basic.get("obchodniJmeno", ""),
            "established": basic.get("datumVzniku", ""), "dissolved": basic.get("datumZaniku") or "",
            "address": (basic.get("sidlo") or {}).get("textovaAdresa", ""),
            "vat_active": (basic.get("seznamRegistraci") or {}).get("stavZdrojeDph") == "AKTIVNI",
            "status": z.get("stavSubjektu", ""), "capital": str(kap),
            "executives": sorted(set(execs)), "owners": owners,
            "file_ref": str(z.get("spisovaZnacka") or ""),
            "flag_likvidace": "likvidac" in ost or bool(basic.get("datumZaniku")),
            "flag_insolvence": bool(re.search(r"insolven|konkurs|úpadk", ost))}


# ---- Sbírka listin (justice.cz — Wicket, chce cookie session; ověřeno curl 2026-07-10) ----
_JUA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
_VALUABLE = re.compile(r"účetní závěrka|výroční zpráva|zpráva auditora", re.I)


def filings(ico, timeout=45):
    """Seznam listin ve sbírce (id, typ, založena). None = nedostupné (fail-open).
    Výroční zprávy/závěrky = tržby a zisk konkurenta (PDF si stáhne člověk/agent ručně)."""
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def get(url):
        try:
            return op.open(urllib.request.Request(url, headers=_JUA), timeout=timeout)\
                     .read().decode("utf-8", "ignore")
        except Exception as e:
            print(f"[filings] {url[:60]}: {e}", file=sys.stderr)
            return None

    h = get(f"https://or.justice.cz/ias/ui/rejstrik-$firma?ico={ico}&jenPlatne=PLATNE&polozek=10")
    m = re.search(r"vypis-sl-firma\?subjektId=(\d+)", h or "")
    if not m:
        return None
    h = get(f"https://or.justice.cz/ias/ui/vypis-sl-firma?subjektId={m.group(1)}")
    if not h:
        return None
    out = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S):
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c.replace("&nbsp;", " ")))
                 .replace("\xa0", " ").strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        if len(cells) >= 5 and cells[0] and "/SL" in cells[0]:
            out.append({"id": cells[0], "typ": cells[1], "zalozena": cells[4] or cells[2]})
    return out


def diff_filings(prev_ids, curr):
    """[(note, valuable)] — nové listiny; závěrky/výroční zprávy zvýrazněné (tržby!)."""
    if curr is None:
        return []
    new = [f for f in curr if f["id"] not in set(prev_ids or [])]
    notes = []
    for f in new[:5]:
        val = bool(_VALUABLE.search(f["typ"]))
        note = f"Nová listina ve sbírce: {f['typ']} (založena {f['zalozena']})"
        if val:
            note += " — obsahuje tržby/hospodaření, stojí za stažení a přečtení."
        notes.append((note, val))
    if len(new) > 5:
        notes.append((f"+ {len(new) - 5} dalších nových listin ve sbírce", False))
    return notes


def diff(prev, curr):
    """[(typ, note, severity)] — severity 'alert' = nejvyšší akční hodnota v celém trackeru."""
    ev = []
    if not prev or not curr:
        return ev
    if curr["flag_insolvence"] and not prev.get("flag_insolvence"):
        ev.append(("ALERT", "V rejstříku se objevila zmínka o insolvenci/úpadku — ověřte v ISIR. "
                            "Příležitost: kampaň na zákazníky tohoto konkurenta.", "alert"))
    if curr["flag_likvidace"] and not prev.get("flag_likvidace"):
        ev.append(("ALERT", "Firma vstoupila do likvidace / zanikla — jejich zákazníci budou hledat náhradu.", "alert"))
    if prev.get("vat_active") and not curr.get("vat_active"):
        ev.append(("ALERT", "Přestala být aktivním plátcem DPH — možný signál útlumu.", "alert"))
    for field, label in (("name", "název"), ("address", "sídlo"), ("capital", "základní kapitál")):
        if prev.get(field) != curr.get(field) and (prev.get(field) or curr.get(field)):
            ev.append(("REGISTRY_CHANGE", f"Změna: {label} „{prev.get(field, '')}“ → „{curr.get(field, '')}“", "info"))
    for field, label in (("executives", "jednatelé/statutáři"), ("owners", "společníci")):
        old, new = set(prev.get(field) or []), set(curr.get(field) or [])
        if old != new:
            plus, minus = sorted(new - old), sorted(old - new)
            det = (" přišli: " + ", ".join(plus) if plus else "") + (" odešli: " + ", ".join(minus) if minus else "")
            ev.append(("REGISTRY_CHANGE", f"Změna ve vedení ({label}):{det}", "info"))
    return ev
