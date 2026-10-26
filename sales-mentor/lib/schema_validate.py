"""schema_validate.py — validace proti DEKLAROVANÉMU JSON Schema.

Řeší audit P1-14: `SKILL.md` slibuje jako povinná pole `verdict`, `parts[]`,
detailní `objections[]`, `closing_rozbor`, `signaly_cteni`, `coaching.plan[]`.
Schéma ale na top-level vyžadovalo jen `meta`, `scores`, `coaching` a writer
validoval vlastní podmnožinu — takže prázdná kostra detailu prošla a scorecard
s českým klíčem námitky se zapsal, přestože ho schéma odmítá.

Modul dělá dvě věci:
  1. Validuje proti skutečnému schématu (jsonschema, když je; jinak vlastní
     kontrola podmnožiny draft-07, kterou naše schémata používají).
  2. Nabízí `require_deep()` — kontrolu polí, která slib v SKILL.md dělá
     povinnými, s jasnými českými chybami pro agenta.

Tento soubor je runtime-local součást skillu; upravuj jej společně s jeho callery a testy.
"""

import json
import re
from pathlib import Path

SCHEMA_VERSION = "1.0"

try:  # jsonschema je hezčí, ale nesmí být podmínkou běhu
    import jsonschema  # type: ignore
    _HAS_JSONSCHEMA = True
except Exception:  # noqa: BLE001
    _HAS_JSONSCHEMA = False


# --------------------------------------------------------------- mini-validátor
def _type_ok(val, t):
    return {
        "object": isinstance(val, dict),
        "array": isinstance(val, list),
        "string": isinstance(val, str),
        "number": isinstance(val, (int, float)) and not isinstance(val, bool),
        "integer": isinstance(val, int) and not isinstance(val, bool),
        "boolean": isinstance(val, bool),
        "null": val is None,
    }.get(t, True)


def _walk(data, schema, path, errs):
    """Podmnožina draft-07, kterou naše schémata reálně používají."""
    if not isinstance(schema, dict):
        return

    t = schema.get("type")
    if t:
        types = t if isinstance(t, list) else [t]
        if not any(_type_ok(data, x) for x in types):
            errs.append(f"{path or '<root>'}: očekáván typ {'/'.join(types)}, "
                        f"je {type(data).__name__}")
            return

    if "enum" in schema and data not in schema["enum"]:
        errs.append(f"{path}: hodnota {data!r} není v povolené sadě {schema['enum']}")

    if isinstance(data, dict):
        for req in schema.get("required", []):
            if req not in data:
                errs.append(f"{path or '<root>'}: chybí povinné pole '{req}'")
        props = schema.get("properties", {})
        for k, v in data.items():
            if k in props:
                _walk(v, props[k], f"{path}.{k}" if path else k, errs)
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path or '<root>'}: pole '{k}' není ve schématu povolené")

    if isinstance(data, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for i, v in enumerate(data):
                _walk(v, items, f"{path}[{i}]", errs)
        if "minItems" in schema and len(data) < schema["minItems"]:
            errs.append(f"{path}: očekáváno aspoň {schema['minItems']} položek, je {len(data)}")

    if isinstance(data, (int, float)) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]:
            errs.append(f"{path}: {data} je pod minimem {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errs.append(f"{path}: {data} je nad maximem {schema['maximum']}")

    if isinstance(data, str) and "pattern" in schema:
        if not re.search(schema["pattern"], data):
            errs.append(f"{path}: '{data}' nesedí na vzor {schema['pattern']}")


def validate(data, schema):
    """Vrátí seznam chyb. Prázdný seznam = validní.

    Používá `jsonschema`, když je k dispozici; jinak vlastní kontrolu. V obou
    případech se validuje SKUTEČNÉ schéma, ne podmnožina zvolená writerem.
    """
    if _HAS_JSONSCHEMA:
        v = jsonschema.Draft7Validator(schema)
        out = []
        for e in sorted(v.iter_errors(data), key=lambda x: list(x.path)):
            loc = ".".join(str(p) for p in e.path) or "<root>"
            out.append(f"{loc}: {e.message}")
        return out
    errs = []
    _walk(data, schema, "", errs)
    return errs


def load_schema(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ------------------------------------------------------- hloubka slíbená v SKILL
DEEP_REQUIRED = {
    "verdict": "jednovětý verdikt hovoru",
    "parts": "rozbor po částech s přepisy dialogů",
    "closing_rozbor": "rozbor závěru hovoru (objekt s citací, chybami a jak to mělo znít)",
    "signaly_cteni": "čtení signálů zákazníka",
}


def require_deep(sc):
    """Kontrola polí, která SKILL.md slibuje jako povinná.

    Audit P1-14: prose instrukce modelu není runtime kontrakt. Prázdná kostra
    detailu prošla validací, takže klient nedostal slíbenou hloubku.
    """
    errs = []
    for key, label in DEEP_REQUIRED.items():
        val = sc.get(key)
        if val in (None, "", [], {}):
            errs.append(f"chybí '{key}' ({label}) — SKILL.md ho označuje za povinný")

    parts = sc.get("parts")
    if isinstance(parts, list):
        if len(parts) < 2:
            errs.append("parts: rozbor musí mít aspoň 2 části hovoru")
        for i, p in enumerate(parts):
            if not isinstance(p, dict):
                errs.append(f"parts[{i}]: očekáván objekt")
                continue
            for f in ("nazev", "co_se_stalo"):
                if not p.get(f):
                    errs.append(f"parts[{i}]: chybí '{f}'")

    # `objections` musí být přítomné VŽDY. Když námitka nebyla, patří tam
    # prázdné pole — chybějící klíč je nejednoznačný stav.
    if "objections" not in sc:
        errs.append("chybí 'objections' — když námitka nebyla, uveďte prázdné pole []")
    elif not isinstance(sc["objections"], list):
        errs.append("objections: očekáváno pole")

    coaching = sc.get("coaching") or {}
    if not coaching.get("plan"):
        errs.append("coaching.plan: chybí plán rozvoje")
    if not (coaching.get("drills") or coaching.get("drill")):
        errs.append("coaching: chybí cvičení do příště ('drill' nebo 'drills')")
    return errs
