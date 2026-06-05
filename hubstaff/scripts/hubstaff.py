"""Hubstaff CLI — entrypoint pro skill `hubstaff`.

Tenký wrapper nad Hubstaff API v2. Žádná interpretace dat, žádné zprávy, žádné anomálie —
jen čisté získání dat ve zvoleném formátu (JSON / CSV / tabulka).
Orchestrující skill nebo agent si výstup interpretuje sám.

Použití:
    python3 hubstaff.py <command> [options]

Příkazy:
    auth-check                    Ověří PAT a vypíše identitu + výchozí organizaci
    me                            `/v2/users/me`
    orgs                          Výpis organizací
    members [--org ID]            Členové organizace
    clients [--org ID]            Klienti organizace
    teams [--org ID]              Týmy organizace
    projects [--org ID]           Projekty organizace
    tasks [--org ID] [--project]  Úkoly organizace
    activities --from --to [...]  Aktivita v 10-min blocích
    time-entries --from --to [...] Časové záznamy (souhrnné úseky práce)
    time-offs --from --to [...]   Žádosti o volno za období
    screenshots --from --to [...] Metadata snímků (žádné stahování obrázků)
    apps --from --to [...]        Top aplikace
    urls --from --to [...]        Top URL
    shifts --from --to [...]      Plánované směny
    breaks --from --to [...]      Přestávky

Globální parametry (lze přidat k libovolnému příkazu):
    --format {json|csv|table}     Výchozí: json
    --max-pages N                 Limit stránek (výchozí 50)
"""
from __future__ import annotations

import argparse
import sys
from typing import Any

import client
import formatters


def _add_org_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--org", type=int, default=None, help="ID organizace (výchozí: první přístupná)")


def _add_window_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--from", dest="date_from", required=True, help="Začátek období (YYYY-MM-DD nebo ISO 8601)")
    parser.add_argument("--to", dest="date_to", required=True, help="Konec období (YYYY-MM-DD nebo ISO 8601)")
    parser.add_argument("--member", type=int, action="append", help="Filtr na ID člena (lze opakovat)")
    parser.add_argument("--project", type=int, action="append", help="Filtr na ID projektu (lze opakovat)")


def _add_format_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["json", "csv", "table"], default="json", help="Formát výstupu (výchozí json)")
    parser.add_argument("--max-pages", type=int, default=50, help="Maximum stránek při paginaci (výchozí 50)")
    parser.add_argument("--columns", help="Čárkou oddělené sloupce pro CSV/table (volitelné)")
    parser.add_argument("--limit", type=int, default=None, help="Omezí počet vrácených záznamů (po stažení, klient-side)")


def _normalize_window(value: str) -> str:
    """Pokud uživatel dá YYYY-MM-DD, doplní T00:00:00Z (Hubstaff očekává ISO 8601)."""
    if "T" in value:
        return value
    return f"{value}T00:00:00Z"


def _normalize_window_end(value: str) -> str:
    if "T" in value:
        return value
    return f"{value}T23:59:59Z"


def _resolve_org(args: argparse.Namespace) -> int:
    if args.org:
        return args.org
    return client.get_default_org_id()


def _emit(items: list[dict[str, Any]], args: argparse.Namespace) -> None:
    if args.limit:
        items = items[: args.limit]
    columns = [c.strip() for c in args.columns.split(",")] if args.columns else None
    print(formatters.render(items, args.format, columns=columns))


def cmd_auth_check(_args: argparse.Namespace) -> int:
    me = client.whoami().get("user", {})
    org_id = client.get_default_org_id()
    print(f"Přihlášen jako {me.get('email', '?')} ({me.get('name', '?')}). Výchozí organizace ID: {org_id}.")
    return 0


def cmd_me(args: argparse.Namespace) -> int:
    resp = client.whoami()
    _emit([resp.get("user", resp)], args)
    return 0


def cmd_orgs(args: argparse.Namespace) -> int:
    items = client.get_paginated("/v2/organizations", {"page_limit": 100})
    _emit(items, args)
    return 0


def cmd_members(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    items = client.get_paginated(f"/v2/organizations/{org}/members", {"page_limit": 100})
    _emit(items, args)
    return 0


def cmd_projects(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    items = client.get_paginated(f"/v2/organizations/{org}/projects", {"page_limit": 100})
    _emit(items, args)
    return 0


def cmd_clients(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    items = client.get_paginated(f"/v2/organizations/{org}/clients", {"page_limit": 100})
    _emit(items, args)
    return 0


def cmd_teams(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    items = client.get_paginated(f"/v2/organizations/{org}/teams", {"page_limit": 100})
    _emit(items, args)
    return 0


def cmd_tasks(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    params: dict[str, Any] = {"page_limit": 100}
    if args.project:
        params["project_ids[]"] = args.project
    items = client.get_paginated(f"/v2/organizations/{org}/tasks", params)
    _emit(items, args)
    return 0


def _window_params(args: argparse.Namespace) -> dict[str, Any]:
    params: dict[str, Any] = {
        "time_slot[start]": _normalize_window(args.date_from),
        "time_slot[stop]": _normalize_window_end(args.date_to),
        "page_limit": 500,
    }
    if args.member:
        params["user_ids[]"] = args.member
    if args.project:
        params["project_ids[]"] = args.project
    return params


def cmd_activities(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    items = client.get_paginated(f"/v2/organizations/{org}/activities", _window_params(args), max_pages=args.max_pages)
    _emit(items, args)
    return 0


def cmd_screenshots(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    items = client.get_paginated(f"/v2/organizations/{org}/screenshots", _window_params(args), max_pages=args.max_pages)
    _emit(items, args)
    return 0


def cmd_apps(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    items = client.get_paginated(f"/v2/organizations/{org}/applications", _window_params(args), max_pages=args.max_pages)
    _emit(items, args)
    return 0


def cmd_urls(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    items = client.get_paginated(f"/v2/organizations/{org}/urls", _window_params(args), max_pages=args.max_pages)
    _emit(items, args)
    return 0


def cmd_shifts(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    params = {
        "date[start]": args.date_from,
        "date[stop]": args.date_to,
        "page_limit": 500,
    }
    if args.member:
        params["user_ids[]"] = args.member
    items = client.get_paginated(f"/v2/organizations/{org}/shifts", params, max_pages=args.max_pages)
    _emit(items, args)
    return 0


def cmd_breaks(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    items = client.get_paginated(f"/v2/organizations/{org}/work_breaks", _window_params(args), max_pages=args.max_pages)
    _emit(items, args)
    return 0


def cmd_time_entries(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    items = client.get_paginated(f"/v2/organizations/{org}/time_entries", _window_params(args), max_pages=args.max_pages)
    _emit(items, args)
    return 0


def cmd_time_offs(args: argparse.Namespace) -> int:
    org = _resolve_org(args)
    params: dict[str, Any] = {
        "date[start]": args.date_from,
        "date[stop]": args.date_to,
        "page_limit": 100,
    }
    if args.member:
        params["user_ids[]"] = args.member
    items = client.get_paginated(f"/v2/organizations/{org}/time_offs", params, max_pages=args.max_pages)
    _emit(items, args)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hubstaff", description="Tenký wrapper Hubstaff API — read-only.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("auth-check", help="Ověří PAT, vypíše identitu a výchozí organizaci")
    p.set_defaults(func=cmd_auth_check)

    p = sub.add_parser("me", help="Identita vlastníka tokenu")
    _add_format_args(p)
    p.set_defaults(func=cmd_me)

    p = sub.add_parser("orgs", help="Výpis organizací, ke kterým má PAT přístup")
    _add_format_args(p)
    p.set_defaults(func=cmd_orgs)

    p = sub.add_parser("members", help="Členové organizace")
    _add_org_arg(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_members)

    p = sub.add_parser("projects", help="Projekty organizace (vč. rozpočtů)")
    _add_org_arg(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_projects)

    p = sub.add_parser("clients", help="Klienti organizace (CRM-like entity v Hubstaffu)")
    _add_org_arg(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_clients)

    p = sub.add_parser("teams", help="Týmy organizace (logické seskupení členů)")
    _add_org_arg(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_teams)

    p = sub.add_parser("tasks", help="Úkoly organizace (volitelný filtr na projekt)")
    _add_org_arg(p)
    p.add_argument("--project", type=int, action="append", help="Filtr na ID projektu (lze opakovat)")
    _add_format_args(p)
    p.set_defaults(func=cmd_tasks)

    p = sub.add_parser("activities", help="Aktivita v 10-min blocích za období")
    _add_org_arg(p)
    _add_window_args(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_activities)

    p = sub.add_parser("screenshots", help="Metadata snímků (žádné stahování obrázků)")
    _add_org_arg(p)
    _add_window_args(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_screenshots)

    p = sub.add_parser("apps", help="Top aplikace (vyžaduje, aby měl PAT příslušná oprávnění)")
    _add_org_arg(p)
    _add_window_args(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_apps)

    p = sub.add_parser("urls", help="Top URL (vyžaduje, aby měl PAT příslušná oprávnění)")
    _add_org_arg(p)
    _add_window_args(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_urls)

    p = sub.add_parser("shifts", help="Plánované směny za období")
    _add_org_arg(p)
    _add_window_args(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_shifts)

    p = sub.add_parser("breaks", help="Přestávky (`work_breaks`) za období")
    _add_org_arg(p)
    _add_window_args(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_breaks)

    p = sub.add_parser("time-entries", help="Časové záznamy (souhrnné úseky práce, vč. ručně přidaných)")
    _add_org_arg(p)
    _add_window_args(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_time_entries)

    p = sub.add_parser("time-offs", help="Žádosti o volno (`time_offs`) za období")
    _add_org_arg(p)
    _add_window_args(p)
    _add_format_args(p)
    p.set_defaults(func=cmd_time_offs)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except client.HubstaffError as exc:
        print(f"Chyba: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
