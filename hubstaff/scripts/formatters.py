"""Formátovače výstupu — JSON / CSV / lidsky čitelná tabulka (česky).

Tabulkový režim je určen k zobrazení v chatu agenta. CSV a JSON jsou pro strojové zpracování
orchestračními skilly nad `hubstaff`.
"""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable


def render(items: list[dict[str, Any]], fmt: str, columns: list[str] | None = None) -> str:
    if fmt == "json":
        return json.dumps(items, ensure_ascii=False, indent=2)
    if fmt == "csv":
        return _render_csv(items, columns)
    if fmt == "table":
        return _render_table(items, columns)
    raise ValueError(f"Neznámý formát výstupu: {fmt}. Použij json, csv nebo table.")


def _flatten(item: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Plochá reprezentace vnořeného dictu — pro CSV / tabulku."""
    out: dict[str, Any] = {}
    for key, value in item.items():
        flat_key = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(_flatten(value, prefix=f"{flat_key}."))
        elif isinstance(value, list):
            out[flat_key] = json.dumps(value, ensure_ascii=False)
        else:
            out[flat_key] = value
    return out


def _collect_keys(items: Iterable[dict[str, Any]]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for item in items:
        for key in _flatten(item):
            if key not in seen:
                seen.add(key)
                keys.append(key)
    return keys


def _render_csv(items: list[dict[str, Any]], columns: list[str] | None) -> str:
    if not items:
        return ""
    flat = [_flatten(it) for it in items]
    cols = columns or _collect_keys(flat)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    for row in flat:
        writer.writerow({k: row.get(k, "") for k in cols})
    return buf.getvalue()


def _render_table(items: list[dict[str, Any]], columns: list[str] | None) -> str:
    if not items:
        return "(žádné záznamy)"
    flat = [_flatten(it) for it in items]
    cols = columns or _collect_keys(flat)
    # zkrátit dlouhé hodnoty
    rows = [[_short(str(row.get(c, ""))) for c in cols] for row in flat]
    widths = [max(len(c), *(len(r[i]) for r in rows)) for i, c in enumerate(cols)]
    sep = "  "
    header = sep.join(c.ljust(widths[i]) for i, c in enumerate(cols))
    divider = sep.join("-" * w for w in widths)
    body = "\n".join(sep.join(r[i].ljust(widths[i]) for i in range(len(cols))) for r in rows)
    return f"{header}\n{divider}\n{body}"


def _short(value: str, limit: int = 60) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"
