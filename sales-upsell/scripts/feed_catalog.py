#!/usr/bin/env python3
"""feed_catalog.py — Google Shopping feed (XML) → katalog pro AI Upsell agent (v0.1).

Bezpečně stáhne/načte produktový feed a uloží kompaktní katalog JSON: id, skupina variant
(item_group_id), název, cena, dostupnost, kategorie, odkaz, gtin/mpn.

Použití:
  python3 feed_catalog.py --feed <veřejná HTTPS URL nebo cesta k XML> \
      --output /documents/sales/.upsell-state/catalog.json [--max-items 20000]

Vzdálené URL: pouze HTTPS:443, veřejné DNS/IP, ručně validované redirecty,
DNS-pinned TLS spojení, výchozí strop 20 MB / 30 s / 3 redirecty.
Bez externích závislostí (stdlib only).
"""
import argparse
from contextlib import contextmanager
import http.client
import io
import ipaddress
import json
import re
import signal
import socket
import ssl
import stat
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import atomic_state as _as  # noqa: E402

USER_AGENT = "Mozilla/5.0 (compatible; CliqSales-Upsell/0.1; +https://cliqsales.cz)"
DEFAULT_MAX_BYTES = 20 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_REDIRECTS = 3
HARD_MAX_BYTES = 50 * 1024 * 1024
HARD_MAX_TIMEOUT_SECONDS = 60
HARD_MAX_REDIRECTS = 5
HARD_MAX_ITEMS = 50000

FIELDS = {
    "id", "item_group_id", "title", "price", "sale_price", "availability",
    "product_type", "google_product_category", "link", "gtin", "mpn", "brand",
}


def local(tag):
    return tag.rsplit("}", 1)[-1].lower()


def parse_price(raw):
    """'1 299,00 CZK' / '1299.00 CZK' / '1299 Kč' → (float, 'CZK') nebo (None, '')."""
    if not raw:
        return None, ""
    cur = ""
    m = re.search(r"([A-Za-z]{2,3}|Kč|€|\$)\s*$", raw.strip())
    if m:
        cur = {"Kč": "CZK", "€": "EUR", "$": "USD"}.get(m.group(1), m.group(1).upper())
    num = re.sub(r"[^\d,.\-]", "", raw)
    if "," in num and "." in num:
        num = num.replace(",", "") if num.rfind(".") > num.rfind(",") else num.replace(".", "").replace(",", ".")
    elif "," in num:
        num = num.replace(",", ".") if re.search(r",\d{1,2}$", num) else num.replace(",", "")
    try:
        return float(num), cur
    except ValueError:
        return None, cur


class FeedSecurityError(RuntimeError):
    pass


def _validate_limits(max_bytes, timeout, max_redirects):
    if max_bytes <= 0 or max_bytes > HARD_MAX_BYTES:
        raise FeedSecurityError(f"max-bytes musí být v rozsahu 1–{HARD_MAX_BYTES}")
    if timeout <= 0 or timeout > HARD_MAX_TIMEOUT_SECONDS:
        raise FeedSecurityError(
            f"timeout musí být v rozsahu 1–{HARD_MAX_TIMEOUT_SECONDS} sekund"
        )
    if max_redirects < 0 or max_redirects > HARD_MAX_REDIRECTS:
        raise FeedSecurityError(f"max-redirects musí být v rozsahu 0–{HARD_MAX_REDIRECTS}")


@contextmanager
def _wall_clock_limit(seconds):
    """Bound DNS/TLS/read even when the system resolver itself stalls."""
    if (
        not hasattr(signal, "setitimer")
        or threading.current_thread() is not threading.main_thread()
    ):
        yield
        return
    started = time.monotonic()
    previous_handler = signal.getsignal(signal.SIGALRM)

    def timeout_handler(_signum, _frame):
        raise FeedSecurityError("vypršel celkový časový limit stahování feedu")

    signal.signal(signal.SIGALRM, timeout_handler)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            elapsed = time.monotonic() - started
            signal.setitimer(
                signal.ITIMER_REAL,
                max(0.001, previous_timer[0] - elapsed),
                previous_timer[1],
            )


def _validate_remote_url(url):
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise FeedSecurityError(f"neplatná feed URL: {exc}") from exc
    if parsed.scheme.lower() != "https":
        raise FeedSecurityError("vzdálený feed musí používat HTTPS; HTTP a jiné protokoly jsou zakázané")
    if parsed.username or parsed.password:
        raise FeedSecurityError("feed URL nesmí obsahovat přihlašovací údaje")
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host:
        raise FeedSecurityError("feed URL nemá hostname")
    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise FeedSecurityError("feed hostname není platný") from exc
    if port not in (None, 443):
        raise FeedSecurityError("vzdálený feed smí používat jen standardní HTTPS port 443")
    path = parsed.path or "/"
    return urlunsplit(("https", host, path, parsed.query, "")), host, 443


def _display_source(value):
    """Persist provenance without leaking signed query parameters."""
    if not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", str(value)):
        return str(value)
    try:
        parsed = urlsplit(str(value))
        host = (parsed.hostname or "").rstrip(".").lower()
        return urlunsplit((parsed.scheme.lower(), host, parsed.path or "/", "", ""))
    except ValueError:
        return "<remote-feed>"


def _resolve_public_ips(host, port):
    try:
        answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise FeedSecurityError(f"DNS lookup feedu selhal: {exc}") from exc
    addresses = []
    for answer in answers:
        raw = answer[4][0]
        try:
            address = ipaddress.ip_address(raw)
        except ValueError:
            continue
        if not address.is_global:
            raise FeedSecurityError(f"feed DNS směřuje na neveřejnou adresu {address}")
        if str(address) not in addresses:
            addresses.append(str(address))
    if not addresses:
        raise FeedSecurityError("feed DNS nevrátil žádnou veřejnou IP adresu")
    return addresses


def _bounded_read(stream, max_bytes, deadline, content_length=None):
    if content_length is not None:
        try:
            declared = int(content_length)
        except (TypeError, ValueError):
            declared = None
        if declared is not None and declared > max_bytes:
            raise FeedSecurityError(
                f"feed deklaruje {declared} B, limit je {max_bytes} B"
            )
    chunks = []
    total = 0
    while True:
        if time.monotonic() >= deadline:
            raise FeedSecurityError("vypršel celkový časový limit stahování feedu")
        chunk = stream.read(min(65536, max_bytes + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise FeedSecurityError(f"feed překročil limit {max_bytes} B")
    return b"".join(chunks)


def _https_get_once(url, approved_ip, timeout, max_bytes, deadline):
    """GET through the exact DNS-approved IP while validating TLS for hostname."""
    normalized, host, port = _validate_remote_url(url)
    parsed = urlsplit(normalized)
    remaining = min(timeout, max(0.1, deadline - time.monotonic()))
    context = ssl.create_default_context()
    raw_socket = socket.create_connection((approved_ip, port), timeout=remaining)
    connection = http.client.HTTPSConnection(host, port, timeout=remaining, context=context)
    try:
        try:
            connection.sock = context.wrap_socket(raw_socket, server_hostname=host)
        except Exception:
            raw_socket.close()
            raise
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        connection.request("GET", target, headers={
            "Host": host,
            "User-Agent": USER_AGENT,
            "Accept": "application/xml,text/xml,application/rss+xml,*/*;q=0.1",
            "Connection": "close",
        })
        response = connection.getresponse()
        headers = {key.lower(): value for key, value in response.getheaders()}
        if response.status in {301, 302, 303, 307, 308}:
            return response.status, headers, b""
        body = _bounded_read(response, max_bytes, deadline, headers.get("content-length"))
        return response.status, headers, body
    finally:
        connection.close()


def _fetch_remote_bounded(src, max_bytes, timeout, max_redirects):
    _validate_limits(max_bytes, timeout, max_redirects)
    deadline = time.monotonic() + timeout
    current = src
    visited = set()
    for redirect_count in range(max_redirects + 1):
        if time.monotonic() >= deadline:
            raise FeedSecurityError("vypršel celkový časový limit stahování feedu")
        normalized, host, port = _validate_remote_url(current)
        if normalized in visited:
            raise FeedSecurityError("feed redirect vytvořil smyčku")
        visited.add(normalized)
        approved_ips = _resolve_public_ips(host, port)
        response = None
        errors = []
        for approved_ip in approved_ips:
            try:
                response = _https_get_once(
                    normalized,
                    approved_ip,
                    min(10, timeout),
                    max_bytes,
                    deadline,
                )
                break
            except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
                errors.append(f"{approved_ip}: {type(exc).__name__}")
        if response is None:
            raise FeedSecurityError("bezpečné spojení k feedu selhalo: " + ", ".join(errors))
        status, headers, body = response
        if status in {301, 302, 303, 307, 308}:
            location = headers.get("location")
            if not location:
                raise FeedSecurityError("feed redirect nemá Location")
            if redirect_count >= max_redirects:
                raise FeedSecurityError("feed překročil povolený počet redirectů")
            current = urljoin(normalized, location)
            continue
        if status != 200:
            raise FeedSecurityError(f"feed vrátil HTTP {status}")
        return io.BytesIO(body), normalized
    raise FeedSecurityError("feed překročil povolený počet redirectů")


def fetch_remote(src, max_bytes=DEFAULT_MAX_BYTES,
                 timeout=DEFAULT_TIMEOUT_SECONDS,
                 max_redirects=DEFAULT_MAX_REDIRECTS):
    with _wall_clock_limit(timeout):
        return _fetch_remote_bounded(src, max_bytes, timeout, max_redirects)


def load_feed(src, max_bytes=DEFAULT_MAX_BYTES,
              timeout=DEFAULT_TIMEOUT_SECONDS,
              max_redirects=DEFAULT_MAX_REDIRECTS):
    _validate_limits(max_bytes, timeout, max_redirects)
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", src):
        return fetch_remote(src, max_bytes=max_bytes, timeout=timeout,
                            max_redirects=max_redirects)
    path = Path(src)
    try:
        metadata = path.stat()
    except OSError as exc:
        raise FeedSecurityError(f"lokální feed nelze otevřít: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise FeedSecurityError(f"lokální feed není běžný soubor: {path}")
    size = metadata.st_size
    if size > max_bytes:
        raise FeedSecurityError(f"lokální feed má {size} B, limit je {max_bytes} B")
    deadline = time.monotonic() + timeout
    with path.open("rb") as handle, _wall_clock_limit(timeout):
        body = _bounded_read(handle, max_bytes, deadline, size)
    return io.BytesIO(body), str(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", required=True, help="URL nebo cesta k XML feedu")
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-items", type=int, default=20000)
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    ap.add_argument("--max-redirects", type=int, default=DEFAULT_MAX_REDIRECTS)
    args = ap.parse_args()

    if not 1 <= args.max_items <= HARD_MAX_ITEMS:
        ap.error(f"max-items musí být v rozsahu 1–{HARD_MAX_ITEMS}")
    try:
        _validate_limits(args.max_bytes, args.timeout_seconds, args.max_redirects)
    except FeedSecurityError as exc:
        ap.error(str(exc))

    try:
        with _as.locked(Path(args.output), timeout=args.timeout_seconds + 10):
            feed, effective_source = load_feed(
                args.feed,
                max_bytes=args.max_bytes,
                timeout=args.timeout_seconds,
                max_redirects=args.max_redirects,
            )
            items, dropped, truncated = {}, 0, False
            with feed:
                cur = None
                for event, el in ET.iterparse(feed, events=("start", "end")):
                    name = local(el.tag)
                    if event == "start" and name in ("item", "entry"):
                        cur = {}
                        continue
                    if cur is None:
                        continue
                    if event == "end" and name in FIELDS and name not in cur:
                        cur[name] = (el.text or "").strip()
                    elif event == "end" and name in ("item", "entry"):
                        pid = cur.get("id")
                        if pid:
                            if len(items) >= args.max_items:
                                truncated = True
                                cur = None
                                el.clear()
                                continue
                            price, currency = parse_price(cur.get("sale_price") or cur.get("price"))
                            items[pid] = {
                                "group": cur.get("item_group_id") or pid,
                                "title": cur.get("title", ""),
                                "price": price,
                                "currency": currency,
                                "availability": (cur.get("availability") or "").lower(),
                                "category": cur.get("product_type") or cur.get("google_product_category", ""),
                                "link": cur.get("link", ""),
                                "gtin": cur.get("gtin", ""),
                                "mpn": cur.get("mpn", ""),
                                "brand": cur.get("brand", ""),
                            }
                        else:
                            dropped += 1
                        cur = None
                        el.clear()

            out = {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source": _display_source(args.feed),
                "effective_source": _display_source(effective_source),
                "count": len(items),
                "items": items,
            }
            _as.write_json_atomic(args.output, out)
    except (FeedSecurityError, ET.ParseError, TimeoutError) as exc:
        print(f"CHYBA: katalog nebyl změněn: {exc}", file=sys.stderr)
        return 3

    msg = f"OK katalog: {len(items)} produktů → {args.output}"
    if dropped:
        msg += f" (přeskočeno {dropped} položek bez id)"
    if truncated:
        msg += f" ⚠️ USEKNUTO na {args.max_items} položek — velký feed, zvaž vyšší --max-items"
    print(msg)
    return 0


# ------------------------------------------------- sdílený helper pro ostatní
def load_catalog(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def build_index(catalog, match_key):
    """Index kód → produkt podle párovacího klíče (salesDNA §11, Feed).
    match_key: feed_id (g:id) | sku (g:mpn) | ean (g:gtin)."""
    idx = {}
    field = {"feed_id": None, "sku": "mpn", "ean": "gtin"}.get(match_key)
    for pid, it in (catalog or {}).get("items", {}).items():
        code = pid if field is None else it.get(field, "")
        if code:
            idx.setdefault(str(code).strip().lower(), (pid, it))
    return idx


def build_name_index(catalog):
    idx = {}
    for pid, it in (catalog or {}).get("items", {}).items():
        t = re.sub(r"\s+", " ", it.get("title", "").strip().lower())
        if t:
            idx.setdefault(t, (pid, it))
    return idx


if __name__ == "__main__":
    raise SystemExit(main())
