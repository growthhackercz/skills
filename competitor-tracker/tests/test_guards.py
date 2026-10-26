#!/usr/bin/env python3
"""Testy bezpečnostních a odolnostních brán trackeru.

    python3 tests/test_guards.py

Bez závislostí a bez sítě — DNS se podvrhuje. Každý scénář hlídá konkrétní
chybu z revize 29. 7. 2026; scénáře označené REGRESE se nikdy nemažou.
"""
import pathlib
import socket
import sys

sys.dont_write_bytecode = True
ZDE = pathlib.Path(__file__).resolve().parent
SCRIPTS = ZDE.parent / "scripts"
for cache in SCRIPTS.rglob("__pycache__"):
    for f in cache.glob("*.pyc"):
        f.unlink()
sys.path.insert(0, str(SCRIPTS))

import net_guard  # noqa: E402
import provider_extras  # noqa: E402

ZELENA, CERVENA, KONEC = "\033[32m", "\033[31m", "\033[0m"
vysledky = []


def zkontroluj(jmeno, podminka, detail=""):
    vysledky.append((jmeno, bool(podminka), detail))
    print("%s %-46s %s" % (ZELENA + "✅" + KONEC if podminka else CERVENA + "❌" + KONEC,
                           jmeno, detail))


def podvrhni_dns(mapa):
    """socket.getaddrinfo → pevná tabulka. Testy nesmí sahat na síť."""
    def _fake(host, port, *args, **kw):
        if host not in mapa:
            raise socket.gaierror("neznámý host v testu: %s" % host)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port or 443)) for ip in mapa[host]]
    net_guard.socket.getaddrinfo = _fake


# ─────────────────────────── SSRF ───────────────────────────

def test_ssrf():
    podvrhni_dns({
        "konkurent.cz":      ["93.184.216.34"],
        "zlomyslny.cz":      ["127.0.0.1"],
        "metadata.test":     ["169.254.169.254"],
        "vnitrni.test":      ["10.0.0.5"],
        "cgnat.test":        ["100.64.0.1"],
        "smiseny.test":      ["93.184.216.34", "192.168.1.1"],
        "control-center":    ["172.18.0.3"],
    })

    ok = net_guard.zkontroluj_url("https://konkurent.cz/cenik")
    zkontroluj("veřejná adresa projde", ok.startswith("https://konkurent.cz"), ok)

    for jmeno, url in [
        ("REGRESE: loopback",            "http://zlomyslny.cz/"),
        ("REGRESE: cloud metadata",      "http://metadata.test/latest/meta-data/"),
        ("REGRESE: privátní rozsah",     "http://vnitrni.test/"),
        ("REGRESE: CGNAT 100.64/10",     "http://cgnat.test/"),
        ("REGRESE: Control Center",      "http://control-center:3000/api/tasks"),
        ("REGRESE: doména s vnitřní IP",  "https://smiseny.test/"),
    ]:
        try:
            net_guard.zkontroluj_url(url)
            zkontroluj(jmeno, False, "PROŠLO, ale nemělo!")
        except net_guard.UnsafeURL as e:
            zkontroluj(jmeno, True, str(e)[:44])

    # Schéma a port
    for jmeno, url in [("file:// neprojde", "file:///etc/passwd"),
                       ("gopher:// neprojde", "gopher://konkurent.cz/"),
                       ("nestandardní port neprojde", "http://konkurent.cz:8080/")]:
        try:
            net_guard.zkontroluj_url(url)
            zkontroluj(jmeno, False, "PROŠLO, ale nemělo!")
        except net_guard.UnsafeURL:
            zkontroluj(jmeno, True)

    # Přesměrování se nesmí následovat automaticky
    zkontroluj("REGRESE: redirect handler je vypnutý",
               net_guard._BezPresmerovani().redirect_request(None, None, 302, "", {}, "x") is None,
               "redirect_request vrací None")


# ─────────────────── fallback chain (kredity + falešné STALE) ───────────────────

class _Volani:
    """Počítadlo — kolik actorů se reálně zavolalo."""
    def __init__(self, chovani):
        self.chovani = chovani
        self.volani = []

    def __call__(self, actor, inp, cap, timeout):
        self.volani.append(actor)
        v = self.chovani[actor]
        if isinstance(v, Exception):
            raise v
        return v


def _chain_s(chovani, usable=lambda o: bool(o)):
    puvodni = provider_extras.provider_ads._run_actor
    volac = _Volani(chovani)
    provider_extras.provider_ads._run_actor = volac
    try:
        chain = list(chovani.keys())
        try:
            out = provider_extras._run_chain(chain, lambda a: {}, lambda a, raw: raw, usable, 5)
            chyba = None
        except provider_extras.SourceError as e:
            out, chyba = None, e
        return volac.volani, out, chyba
    finally:
        provider_extras.provider_ads._run_actor = puvodni


def test_fallback():
    SE = provider_extras.SourceError

    volani, out, chyba = _chain_s({"primar": [{"x": 1}], "zaloha": [{"y": 2}]})
    zkontroluj("primár s daty → záloha se nevolá", volani == ["primar"], str(volani))

    # REGRESE: klidný konkurent (0 reklam) je běžný stav, ne důvod platit zálohu
    volani, out, chyba = _chain_s({"primar": [], "zaloha": [{"y": 2}]})
    zkontroluj("REGRESE: prázdný primár → záloha se NEVOLÁ",
               volani == ["primar"], str(volani))
    zkontroluj("REGRESE: prázdný primár není STALE", chyba is None,
               "chyba=%s" % chyba)

    # REGRESE: selhání zálohy nesmí přebít čistou odpověď primáru
    volani, out, chyba = _chain_s({"primar": [], "zaloha": SE("záloha umřela")})
    zkontroluj("REGRESE: pád zálohy nepřebije prázdno primáru",
               chyba is None and volani == ["primar"], "volani=%s chyba=%s" % (volani, chyba))

    # Skutečný výpadek primáru → záloha naskočí
    volani, out, chyba = _chain_s({"primar": SE("primár umřel"), "zaloha": [{"y": 2}]})
    zkontroluj("pád primáru → naskočí záloha", volani == ["primar", "zaloha"] and out, str(volani))

    # Oba padly → STALE
    volani, out, chyba = _chain_s({"primar": SE("a"), "zaloha": SE("b")})
    zkontroluj("oba padly → STALE", isinstance(chyba, SE), str(chyba)[:40])

    # Neznámý formát → zkusí zálohu, pak STALE
    volani, out, chyba = _chain_s({"primar": [{"cizi": 1}], "zaloha": [{"cizi": 2}]},
                                  usable=lambda o: False)
    zkontroluj("neznámý formát → zkusí zálohu, pak STALE",
               volani == ["primar", "zaloha"] and isinstance(chyba, SE), str(volani))

    # Výjimka v normalizéru je schema drift jednoho actoru, ne důvod přeskočit zálohu.
    puvodni = provider_extras.provider_ads._run_actor
    volac = _Volani({"primar": [{"x": 1}], "zaloha": [{"y": 2}]})
    provider_extras.provider_ads._run_actor = volac
    try:
        def normalize(actor, raw):
            if actor == "primar":
                raise ValueError("schema drift")
            return raw
        out = provider_extras._run_chain(
            ["primar", "zaloha"], lambda actor: {}, normalize, lambda obj: bool(obj), 5,
        )
        zkontroluj("normalizační chyba → zkusí zálohu",
                   volac.volani == ["primar", "zaloha"] and out == [{"y": 2}], str(volac.volani))
    finally:
        provider_extras.provider_ads._run_actor = puvodni


# ─────────────────────── YouTube vstupní schémata ───────────────────────

def test_youtube_vstupy():
    inp = provider_extras._in_youtube("https://youtube.com/@znacka", 8)
    prim = inp("streamers~youtube-scraper")
    zal = inp("grow_media~youtube-channel-video-scraper")

    zkontroluj("REGRESE: primár řadí přes sortVideosBy",
               "sortVideosBy" in prim and "sortingOrder" not in prim, str(sorted(prim)))
    zkontroluj("primár posílá startUrls", "startUrls" in prim)
    zkontroluj("REGRESE: záloha nemá videoType 'all'",
               zal.get("videoType") in ("long", "short"), "videoType=%s" % zal.get("videoType"))
    zkontroluj("záloha posílá channelUrls + sortOrder",
               "channelUrls" in zal and zal.get("sortOrder") in ("latest", "popular", "oldest"))


def main():
    print("\n%s" % ("─" * 78))
    print("SSRF"); print("─" * 78); test_ssrf()
    print("\nFallback chain"); print("─" * 78); test_fallback()
    print("\nYouTube vstupy"); print("─" * 78); test_youtube_vstupy()

    padly = [j for j, ok, _ in vysledky if not ok]
    print("─" * 78)
    print("%d/%d prošlo" % (len(vysledky) - len(padly), len(vysledky)))
    if padly:
        print("%sPADLO: %s%s" % (CERVENA, ", ".join(padly), KONEC))
        sys.exit(1)
    print("%sVšechny brány drží.%s" % (ZELENA, KONEC))


if __name__ == "__main__":
    main()
