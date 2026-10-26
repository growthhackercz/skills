"""state_version.py — verzování a migrace trvalého stavu.

Řeší audit P1-12: skilly si mezi běhy drží stav (snapshoty pipeline, seen-sady
objednávek, kohorty vln, katalog feedu), ale žádný soubor neříká, jakým
schématem a jakou verzí skillu byl zapsaný. Po upgradu skillu se starý stav
načte novou logikou, která mu rozumí jinak — a nikdo si toho nevšimne.

Zásady:
  1. Každý trvalý stav nese `_meta` se `schemaVersion`, `skill`, `skillVersion`.
  2. Neverzovaný stav (zapsaný před touhle změnou) se pozná a bez ztráty dat
     označkuje — migrace je idempotentní, druhý běh nic nemění.
  3. Stav zapsaný NOVĚJŠÍM schématem než umíme se odmítne (fail-closed).
     Downgrade nesmí data mlčky přeinterpretovat.

Tento soubor je runtime-local součást skillu; upravuj jej společně s jeho callery a testy.
"""

import time

# Verze schématu trvalého stavu napříč Sales Engine.
STATE_SCHEMA_VERSION = "1.0"

META_KEY = "_meta"


def _major(v):
    try:
        return int(str(v).split(".")[0])
    except (ValueError, AttributeError):
        return 0


def stamp(data, skill, skill_version, schema_version=STATE_SCHEMA_VERSION):
    """Vrátí kopii stavu s `_meta`. Nedestruktivní — vstup nemění."""
    if not isinstance(data, dict):
        return data
    out = dict(data)
    prev = out.get(META_KEY) or {}
    out[META_KEY] = {
        "schemaVersion": schema_version,
        "skill": skill,
        "skillVersion": str(skill_version),
        "writtenAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "firstWrittenAt": prev.get("firstWrittenAt")
                          or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    return out


def read_meta(data):
    """`_meta` stavu. Prázdný dict = neverzovaný stav (před P1-12)."""
    if isinstance(data, dict) and isinstance(data.get(META_KEY), dict):
        return dict(data[META_KEY])
    return {}


def migrate(data, skill, skill_version, migrations=None,
            schema_version=STATE_SCHEMA_VERSION):
    """Připraví načtený stav pro aktuální verzi skillu.

    `migrations` je {cílová_verze: funkce(data) -> data} — aplikují se ve
    vzestupném pořadí a jen ty, které stav ještě neprošel.

    Vrací (stav, poznámky, ok). `ok=False` znamená fail-closed odmítnutí:
    volající NESMÍ takový stav použít ani přepsat, jen ohlásit.
    """
    notes = []
    if not isinstance(data, dict):
        return data, notes, True

    meta = read_meta(data)
    found = meta.get("schemaVersion")

    if found is None:
        notes.append("stav byl neverzovaný (zápis před auditem P1-12) — "
                     f"označkován jako schemaVersion {schema_version}, data zachována")
    elif _major(found) > _major(schema_version):
        return data, [
            f"ODMÍTNUTO: stav má schemaVersion {found}, tento skill umí "
            f"nejvýš {schema_version}. Zapsala ho novější verze skillu; "
            "starší běh by ho přeinterpretoval. Nasaďte novější verzi, "
            "nebo stav odložte."], False

    for target in sorted((migrations or {}).keys(), key=_major):
        if found is not None and _major(found) >= _major(target):
            continue
        data = (migrations or {})[target](data)
        notes.append(f"migrace na schemaVersion {target} proběhla")

    prev_skill_v = meta.get("skillVersion")
    if prev_skill_v and prev_skill_v != str(skill_version):
        notes.append(f"stav zapsán verzí skillu {prev_skill_v}, "
                     f"teď běží {skill_version}")

    return stamp(data, skill, skill_version, schema_version), notes, True


def warn_lines(notes):
    """Řádky pro stderr. Prázdný seznam = není co hlásit."""
    return [f"STAV: {n}" for n in (notes or [])]


# --------------------------------------------------- verze na úrovni složky
# Většina trvalého stavu jsou mapy `id -> záznam` (kontakty, objednávky,
# příležitosti). Vložit do nich `_meta` by znamenalo, že každá iterace přes
# `.items()` narazí na klíč, který není záznam. Verze proto žije v jednom
# sidecar souboru na složku stavu.
DIR_META_FILE = ".state-version.json"


def check_dir(state_dir, skill, skill_version, schema_version=STATE_SCHEMA_VERSION):
    """Ověří a označkuje složku trvalého stavu.

    Vrací (poznámky, ok). `ok=False` = fail-closed: stav zapsala novější verze
    skillu, tento běh se ho nesmí ani dotknout.
    """
    import json
    from pathlib import Path

    d = Path(state_dir)
    d.mkdir(parents=True, exist_ok=True)
    f = d / DIR_META_FILE
    notes = []

    prev = {}
    if f.exists():
        try:
            prev = json.loads(f.read_text(encoding="utf-8")) or {}
        except (OSError, ValueError):
            return [
                f"ODMÍTNUTO: {DIR_META_FILE} je nečitelný. Poškozený stav se "
                "nepřepíše; nejdřív jej opravte nebo archivujte."
            ], False
    else:
        has_state = any(p.name != DIR_META_FILE for p in d.iterdir()) if d.exists() else False
        if has_state:
            notes.append("stav ve složce byl neverzovaný (zápis před auditem P1-12) — "
                         f"označkován jako schemaVersion {schema_version}, data zachována")

    found = prev.get("schemaVersion")
    if found and _major(found) > _major(schema_version):
        return [f"ODMÍTNUTO: stav ve {d} má schemaVersion {found}, tento skill umí "
                f"nejvýš {schema_version}. Zapsala ho novější verze skillu; "
                "starší běh by ho přeinterpretoval. Nasaďte novější verzi."], False

    prev_skill_v = prev.get("skillVersion")
    if prev_skill_v and prev_skill_v != str(skill_version):
        notes.append(f"stav zapsán verzí skillu {prev_skill_v}, teď běží {skill_version}")

    payload = {
        "schemaVersion": schema_version,
        "skill": skill,
        "skillVersion": str(skill_version),
        "writtenAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "firstWrittenAt": prev.get("firstWrittenAt") or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    import os as _os
    import tempfile as _tempfile
    fd, tmp = _tempfile.mkstemp(prefix=f.name + ".", suffix=".tmp", dir=str(d))
    try:
        with _os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            _os.fsync(handle.fileno())
        _os.replace(tmp, f)
    except Exception:
        try:
            _os.unlink(tmp)
        except OSError:
            pass
        raise
    return notes, True
