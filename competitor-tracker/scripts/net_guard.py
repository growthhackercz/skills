#!/usr/bin/env python3
"""competitor-tracker — bezpečné stahování uživatelem zadaných URL (anti-SSRF).

Sledované stránky konkurence zadává klient (`add-url`). Bez kontroly by šlo skillu
podstrčit vnitřní adresu a nechat ho ji stáhnout — kontejner openclaw vidí na
`control-center:3000` i na metadata službu cloudu. Proto tenhle modul:

  • povolí jen http/https a porty 80/443,
  • přeloží host a odmítne VŠECHNY neveřejné adresy (loopback, privátní rozsahy,
    link-local včetně 169.254.169.254, CGNAT, multicast, rezervované, IPv6 ULA),
  • NENÁSLEDUJE přesměrování automaticky — každý hop se validuje znovu
    (externí URL smí přesměrovat na vnitřní; to je klasické obejití allowlistu),
  • omezí velikost odpovědi.

Zbytkové riziko (vědomě neřešeno): DNS rebinding. Validujeme přeložené adresy a
teprve pak stahujeme, takže mezi kontrolou a spojením je krátké okno, ve kterém
může DNS odpovědět jinak. Uzavřít to znamená spojit se přímo na ověřenou IP
a přepsat hlavičku Host, což rozbíjí TLS SNI u řady webů. Pro tenhle scénář —
adresu zadává sám klient, ne cizí návštěvník — je ta výměna nevýhodná.
"""
import ipaddress
import socket
import urllib.error
import urllib.parse
import urllib.request

POVOLENA_SCHEMATA = ("http", "https")
POVOLENE_PORTY = (80, 443)
MAX_HOPU = 3
MAX_BAJTU = 1_500_000


class UnsafeURL(ValueError):
    """URL neprošla bezpečnostní kontrolou. Zpráva je určená klientovi."""


def _adresa_je_verejna(ip_text):
    ip = ipaddress.ip_address(ip_text)
    # is_global samo o sobě nestačí — u některých verzí Pythonu pustí sdílený
    # CGNAT rozsah 100.64/10, který v kontejneru běžně vede do vnitřní sítě.
    if not ip.is_global:
        return False
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        return False
    if ip.version == 4 and ip in ipaddress.ip_network("100.64.0.0/10"):
        return False
    return True


def zkontroluj_url(url):
    """Ověří jednu URL. Vrací normalizovanou URL, nebo vyhodí UnsafeURL.

    Volá se i z `add-url`, aby klient dostal chybu hned při zadání a ne až
    za týden při obchůzce.
    """
    if not url or not isinstance(url, str):
        raise UnsafeURL("Prázdná adresa.")
    url = url.strip()
    if "://" not in url:
        url = "https://" + url

    p = urllib.parse.urlsplit(url)
    if p.scheme.lower() not in POVOLENA_SCHEMATA:
        raise UnsafeURL("Povolené jsou jen adresy http a https (dostal jsem „%s“)." % p.scheme)

    host = p.hostname
    if not host:
        raise UnsafeURL("V adrese chybí doména.")

    try:
        port = p.port
    except ValueError:
        raise UnsafeURL("Neplatné číslo portu v adrese.")
    if port is not None and port not in POVOLENE_PORTY:
        raise UnsafeURL("Povolené jsou jen porty 80 a 443 (dostal jsem %s)." % port)

    try:
        info = socket.getaddrinfo(host, port or (443 if p.scheme == "https" else 80),
                                  proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise UnsafeURL("Doménu „%s“ se nepodařilo přeložit (%s)." % (host, e))

    adresy = {zaznam[4][0] for zaznam in info}
    if not adresy:
        raise UnsafeURL("Doména „%s“ nemá žádnou adresu." % host)

    # VŠECHNY přeložené adresy musí být veřejné. Stačí jedna vnitřní a URL padá —
    # jinak by šlo cíl schovat za doménu s víc A záznamy.
    for a in sorted(adresy):
        if not _adresa_je_verejna(a):
            raise UnsafeURL(
                "Adresa „%s“ vede na vnitřní síť (%s). Sledovat jde jen veřejné stránky." % (host, a))

    return urllib.parse.urlunsplit(p)


class _BezPresmerovani(urllib.request.HTTPRedirectHandler):
    """Vrátí odpověď s přesměrováním místo jeho automatického následování.

    Bez tohohle by kontrola nad URL nic neznamenala: veřejná adresa smí odpovědět
    `302 Location: http://169.254.169.254/…` a urllib by tam poslušně skočil.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def bezpecne_stahni(url, timeout=30, hlavicky=None):
    """Stáhne text stránky. Vrací str, nebo vyhodí UnsafeURL / urllib chybu.

    Přesměrování se řeší ručně: každý hop projde `zkontroluj_url` znovu.
    """
    cil = zkontroluj_url(url)
    opener = urllib.request.build_opener(_BezPresmerovani)

    for _ in range(MAX_HOPU):
        req = urllib.request.Request(cil, headers=hlavicky or {})
        try:
            odpoved = opener.open(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                dalsi = e.headers.get("Location")
                if not dalsi:
                    raise UnsafeURL("Přesměrování bez cílové adresy.")
                # Relativní Location je potřeba doplnit na absolutní, jinak by
                # kontrola dostala nesmyslný vstup.
                cil = zkontroluj_url(urllib.parse.urljoin(cil, dalsi))
                continue
            raise
        with odpoved:
            data = odpoved.read(MAX_BAJTU + 1)
            if len(data) > MAX_BAJTU:
                raise UnsafeURL(
                    "Stránka je větší než povolený limit %d bajtů; nestahuji ji celou." % MAX_BAJTU
                )
            return data.decode("utf-8", "ignore")

    raise UnsafeURL("Příliš mnoho přesměrování (víc než %d)." % MAX_HOPU)
