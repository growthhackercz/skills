"""safe_html.py — jediný bezpečný Markdown → HTML renderer pro Sales Engine.

Řeší audit P1-04 (stored HTML/script injection ve čtyřech rozdílných kopiích
rendereru).

Princip: vstup se NEJDŘÍV celý escapuje, teprve potom se aplikují Markdown
transformace. Jediné značky ve výstupu jsou ty, které generuje tento modul —
autorský HTML se do výstupu nedostane už z konstrukce, ne díky filtrování.

Odkazy: povolené jen `https://` a `http://`. Cokoli jiného (`javascript:`,
`data:`, `file:`, `vbscript:`, relativní i protokolově relativní) se vykreslí
jako čistý text, ne jako odkaz.

Vstup může přijít z nedůvěryhodného zdroje — CRM poznámka, přepis hovoru,
výstup modelu. Nikdy se mu nevěří.

Tento soubor je runtime-local součást skillu; upravuj jej společně s jeho callery a testy.
"""

import re
import secrets

SCHEMA_VERSION = "1.1"

# Strop délky vstupu. Přepis hovoru se do něj pohodlně vejde; delší vstup
# je buď chyba, nebo pokus o zahlcení.
MAX_INPUT = 262_144

# Řídicí znaky, které nemají v HTML co dělat: NUL rozbíjí Postgres i XML,
# osamocený surrogát shodí .encode("utf-8") při odesílání.
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _sanitize_input(v):
    t = str(v)
    if len(t) > MAX_INPUT:
        t = t[:MAX_INPUT] + "\n\n[zkráceno — vstup přesáhl limit]"
    t = _CTRL.sub("", t)
    # Osamocené surrogáty (běžný artefakt výstupu modelu) → nahradit.
    return t.encode("utf-8", "replace").decode("utf-8", "replace")

# Povolená schémata odkazů. Vše ostatní se degraduje na text.
_SAFE_SCHEMES = ("https://", "http://")


def esc(s):
    """Escapuje text tak, aby z něj nemohla vzniknout značka ani entita."""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _safe_url(raw):
    """Vrátí bezpečnou URL, nebo None když schéma není povolené."""
    if raw is None:
        return None
    # Escapované znaky zpět na surové jen pro kontrolu schématu.
    u = str(raw).replace("&amp;", "&").strip()
    # Kontrola schématu běží nad OČIŠTĚNOU kopií (obchází se přes "java\tscript:"),
    # ale vrací se původní řetězec — jinak by se z ?q=a b stalo ?q=ab a odkaz
    # by mířil jinam, než autor zamýšlel.
    probe = re.sub(r"[\x00-\x20\x7f]", "", u)
    if not probe.lower().startswith(_SAFE_SCHEMES):
        return None
    if any(c in u for c in ('"', "'", "<", ">", "`")):
        return None
    return esc(u)


def _link(m):
    label, url = m.group(1), m.group(2)
    safe = _safe_url(url)
    if safe is None:
        # Nebezpečné schéma: zůstane čitelný text, žádný klikatelný odkaz.
        return label
    return f'<a href="{safe}">{label}</a>'


def _image(m):
    alt, url = m.group(1), m.group(2)
    safe = _safe_url(url)
    label = f"[obrázek: {alt}]" if alt else "[obrázek]"
    if safe is None:
        return label
    return f'<a href="{safe}">{label}</a>'


def _list_block(t, pattern, tag):
    lines = t.split("\n")
    out, buf = [], []

    def flush():
        if buf:
            items = "".join(f"<li>{re.sub(pattern, '', b).strip()}</li>" for b in buf)
            out.append(f"<{tag}>{items}</{tag}>")
            buf.clear()

    for ln in lines:
        if re.match(pattern, ln):
            buf.append(ln)
        else:
            flush()
            out.append(ln)
    flush()
    return "\n".join(out)


def _is_table_separator(row):
    r"""Řádek typu `|---|:--:|`. Bez regexu — původní vzor měl překrývající se
    `\s*` a `[\s:\-|]+`, což u dlouhého řádku mezer vedlo na kvadratické
    backtrackování (40 kB = 11 s)."""
    r = row.strip()
    return bool(r) and "-" in r and not (set(r) - set(" \t:-|"))


def _tables_to_bullets(t):
    """GHL neumí tabulky — převede je na odrážky se zachovaným pořadím."""
    lines = t.split("\n")
    out, block = [], []

    def flush():
        if len(block) >= 2:
            rows = [
                [c.strip() for c in r.strip().strip("|").split("|")]
                for r in block
                if not _is_table_separator(r)
            ]
            if rows:
                head = rows[0]
                items = []
                for r in rows[1:]:
                    pairs = [
                        # Tučný prefix hlavičky — kontrakt v references/
                        # ghl-html-konverze.md. Hlavička je už escapovaná,
                        # <strong> přidáváme my.
                        f"<strong>{head[i]}:</strong> {c}"
                        if i < len(head) and head[i] else c
                        for i, c in enumerate(r)
                        if c
                    ]
                    if pairs:
                        items.append("<li>" + " · ".join(pairs) + "</li>")
                if items:
                    out.append("<ul>" + "".join(items) + "</ul>")
                    block.clear()
                    return
        out.extend(block)
        block.clear()

    for ln in lines:
        if "|" in ln and ln.strip().startswith("|"):
            block.append(ln)
        else:
            flush()
            out.append(ln)
    flush()
    return "\n".join(out)


def _wrap_paras(t):
    blocks = re.split(r"\n\s*\n", t)
    out = []
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        if b.startswith("<") and re.match(r"^<(ul|ol|p|blockquote)\b", b):
            out.append(b)
        else:
            out.append("<p>" + b.replace("\n", "<br/>") + "</p>")
    return "\n".join(out)


def _extract_fences(t, tok, holds):
    """Vytáhne ```bloky``` jedním průchodem.

    Původní `re.sub(r"```[a-z]*\n?(.*?)```", …, flags=DOTALL)` je u vstupu
    složeného ze samých zpětných apostrofů kvadratický — líné `.*?` skenuje
    dopředu z každé pozice (200 kB = 9,9 s).
    """
    out, i = [], 0
    while True:
        j = t.find("```", i)
        if j < 0:
            out.append(t[i:]); break
        k = t.find("```", j + 3)
        if k < 0:
            out.append(t[i:]); break
        body = t[j + 3:k]
        nl = body.find("\n")
        if nl >= 0 and body[:nl].strip().replace("_", "").replace("+", "").replace("-", "").isalnum():
            body = body[nl + 1:]          # zahodit jazykový tag na prvním řádku
        elif nl >= 0 and not body[:nl].strip():
            body = body[nl + 1:]
        holds.append(esc(body.strip()))
        out.append(t[i:j])
        out.append(f"\x01{tok}{len(holds) - 1}\x01")
        i = k + 3
    return "".join(out)


def _inline_pairs(t, mark, tag, limit=500):
    """Spáruje `mark ... mark` jedním průchodem.

    Regex `mark([^mark\n]{1,N})mark` je i s omezeným kvantifikátorem
    superlineární — u 200 kB samých značek zkouší N pozic pro každý výskyt
    (naměřeno 9,5 s). Lineární scanner dělá totéž v konstantním čase na znak.
    """
    out, i, m = [], 0, len(mark)
    while True:
        j = t.find(mark, i)
        if j < 0:
            out.append(t[i:]); break
        k = t.find(mark, j + m)
        if k < 0:
            out.append(t[i:]); break
        content = t[j + m:k]
        if not content or "\n" in content or len(content) > limit:
            out.append(t[i:j + m]); i = j + m; continue
        out.append(t[i:j]); out.append(f"<{tag}>{content}</{tag}>"); i = k + m
    return "".join(out)


def render(md, tables=True):
    """Markdown → bezpečné HTML.

    tables=True převádí Markdown tabulky na odrážky (GHL je neumí).
    """
    if md is None:
        return ""

    # 1) Kódové bloky vytáhnout PŘED escapem, ať se jejich obsah nerozbije
    #    transformacemi, a vrátit je jako escapovaný blockquote.
    holds = []
    # Náhodný token per volání — literál v nedůvěryhodném vstupu tak nemůže
    # padělat placeholder a dosadit si obsah cizího kódového bloku.
    tok = secrets.token_hex(8)

    t = _extract_fences(_sanitize_input(md).strip(), tok, holds)

    # 2) Escapovat VŠECHNO ostatní. Od tohoto bodu ve stringu neexistuje
    #    žádná autorská značka — jen náš vlastní markup přidaný níž.
    t = esc(t)

    # 3) Markdown transformace nad escapovaným textem.
    if tables:
        t = _tables_to_bullets(t)
    t = re.sub(r"^#{3,6}\s+(.+)$", r"<p><strong><em>\1</em></strong></p>", t, flags=re.MULTILINE)
    t = re.sub(r"^#{1,2}\s+(.+)$", r"<p><strong>\1</strong></p>", t, flags=re.MULTILINE)
    t = _list_block(t, r"^\s*\d+\.\s+", "ol")
    t = _list_block(t, r"^\s*[-*]\s+", "ul")
    t = _inline_pairs(t, "`", "em")
    t = _inline_pairs(t, "**", "strong")
    t = re.sub(r"(?<![\w\*])\*([^\*\n]+)\*(?![\w\*])", r"<em>\1</em>", t)
    t = _inline_pairs(t, "~~", "s")
    t = re.sub(r"!\[([^\]\n]{0,300})\]\(([^)\s]{1,2048})\)", _image, t)
    t = re.sub(r"\[([^\]\n]{1,300})\]\(([^)\s]{1,2048})\)", _link, t)
    t = re.sub(r"^---+\s*$", r"<p>— — —</p>", t, flags=re.MULTILINE)

    t = _wrap_paras(t).strip()

    # 4) Vrátit kódové bloky (už escapované v kroku 1).
    #    Jedním průchodem — smyčka `str.replace` per blok skenovala celý
    #    řetězec znovu a znovu (100 kB samých apostrofů = 16 666 bloků,
    #    100 000 volání replace, 2,4 s).
    if holds:
        t = re.sub(
            rf"\x01{tok}(\d+)\x01",
            lambda m: f"<blockquote>{holds[int(m.group(1))]}</blockquote>"
            if int(m.group(1)) < len(holds) else "",
            t,
        )
    return t


# --- Kompatibilita s dosavadními názvy ve skillech ---------------------------
def md_to_ghl_html(md):
    return render(md, tables=True)


def md_to_html(md):
    return render(md, tables=False)
