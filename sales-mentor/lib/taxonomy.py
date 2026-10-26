"""taxonomy.py — jediný zdroj taxonomie a bodových pásem.

Řeší audit P2-03: české labely námitek byly ručně duplikované ve čtyřech
místech (TAXONOMY.md, scorecard.schema.json, scorecard_write.py,
analytik_aggregate.py) a bodová pásma ve dvou (SCORING_ENGINE.md,
scorecard_write.py). Kterákoli změna se musela udělat čtyřikrát a rozjezd
nikdo nepoznal — Mentor by pak psal jiný label než Analytik agreguje.

Data žijí v `{baseDir}/kb/taxonomy.json`. Markdown dokumentace se proti nim
kontroluje testem, ne opisuje.

Tento soubor je runtime-local součást skillu; upravuj jej společně s jeho callery a testy.
"""

import json
from pathlib import Path

SCHEMA_VERSION = "1.0"
_CACHE = {}


def _path(base=None):
    if base:
        return Path(base)
    # {baseDir}/kb/taxonomy.json — lib/ i scripts/ leží vedle kb/
    return Path(__file__).resolve().parent.parent / "kb" / "taxonomy.json"


def load(base=None):
    p = _path(base)
    key = str(p)
    if key not in _CACHE:
        _CACHE[key] = json.loads(p.read_text(encoding="utf-8"))
    return _CACHE[key]


def categories(base=None):
    """Klíče kategorií v deklarovaném pořadí."""
    return [c["key"] for c in load(base)["categories"]]


def cat_labels(base=None):
    return {c["key"]: c["label"] for c in load(base)["categories"]}


def obj_labels(base=None):
    return {o["key"]: o["label"] for o in load(base)["objections"]}


def obj_keys(base=None):
    return [o["key"] for o in load(base)["objections"]]


def band(total, base=None):
    """Název pásma pro celkové skóre. Pásma pokrývají 0–100 bez děr."""
    try:
        t = float(total)
    except (TypeError, ValueError):
        return ""
    for b in sorted(load(base)["score_bands"], key=lambda x: -x["min"]):
        if t >= b["min"]:
            return b["label"]
    return ""


def bands(base=None):
    return list(load(base)["score_bands"])
