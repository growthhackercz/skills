#!/usr/bin/env python3
"""scorecard_write.py — zapíše scorecard hovoru (SINGLE-WRITER: jen mentor).

Vstup = JSON scorecard dle cliqsales-closing-system/schemas/scorecard.schema.json (model ho
sestaví z hodnocení). Skript ověří strukturu, spočítá kontrolní total z vah,
uloží do /documents/sales/scorecards/<obchodnik>/<datum>-<firma>.json a vyrobí
human-readable kartu pro obchodníka.

DRY-RUN je default — reálný zápis až s --execute (fail-closed vzor jako assistant).

Použití:
  python3 scorecard_write.py --input /tmp/scorecard.json            # náhled (dry-run)
  python3 scorecard_write.py --input /tmp/scorecard.json --card      # + vytiskni kartu
  python3 scorecard_write.py --input /tmp/scorecard.json --execute   # zapiš

Exit: 0 OK · 3 chyba vstupu/validace · 4 chyba zápisu.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- Sdílené moduly (audit P1-13, P1-14) ----------------------------------
import sys as _syss
from pathlib import Path as _Paths
_syss.path.insert(0, str(_Paths(__file__).resolve().parent.parent / "lib"))
import schema_validate as _sv  # noqa: E402
import atomic_state as _as  # noqa: E402
import taxonomy as _tax  # noqa: E402

# Verze skillu se zapisuje do manifestu bundlu (audit P1-12).
SKILL_VERSION = "1.0"  # musí odpovídat `version:` ve SKILL.md

# Audit P2-03: taxonomie i pásma mají jediný zdroj — kb/taxonomy.json.
CATEGORIES = _tax.categories()
CAT_LABEL = _tax.cat_labels()
DOCS_ROOT = Path("/documents/sales/scorecards")
# Technický klíč → český název. Do výstupů VŽDY česky (klíč je jen pro data).
OBJ_LABEL = _tax.obj_labels()


def slug(s: str) -> str:
    s = (s or "").strip().lower()
    repl = {"á": "a", "č": "c", "ď": "d", "é": "e", "ě": "e", "í": "i", "ň": "n",
            "ó": "o", "ř": "r", "š": "s", "ť": "t", "ú": "u", "ů": "u", "ý": "y", "ž": "z"}
    s = "".join(repl.get(ch, ch) for ch in s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "neznamy"


def _schema_path():
    """Schéma hledáme ve vendorované KB pod {baseDir}/kb/."""
    return _Paths(__file__).resolve().parent.parent / "kb" / "schemas" / "scorecard.schema.json"


def validate(sc: dict) -> list[str]:
    """Validace proti DEKLAROVANÉMU schématu + vynucení slíbené hloubky.

    Audit P1-14: dřív se validovala vlastní podmnožina, takže prázdná kostra
    detailu prošla a scorecard s českým klíčem námitky se zapsal, přestože
    ho schéma odmítá. Teď se validuje skutečné schéma; když chybí, běh se
    zastaví — mlčky validovat proti ničemu je horší než spadnout.
    """
    errs: list[str] = []
    sp = _schema_path()
    if sp.exists():
        errs += _sv.validate(sc, _sv.load_schema(sp))
    else:
        errs.append(f"nenalezeno schéma {sp} — bez něj se scorecard nezapisuje")
    errs += _sv.require_deep(sc)
    meta = sc.get("meta") or {}
    for f in ("obchodnik", "datum", "firma"):
        if not meta.get(f):
            errs.append(f"meta.{f} chybí")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(meta.get("datum", ""))):
        errs.append("meta.datum musí být YYYY-MM-DD")
    scores = sc.get("scores") or {}
    total = scores.get("total")
    if not isinstance(total, (int, float)) or not (0 <= total <= 100):
        errs.append("scores.total musí být 0–100")
    cats = scores.get("categories") or []
    if len(cats) != 8:
        errs.append(f"scores.categories musí mít 8 položek (má {len(cats)})")
    keys = [c.get("key") for c in cats]
    if sorted(keys) != sorted(CATEGORIES):
        errs.append("scores.categories.key neodpovídá 8 kategoriím z SCORING_ENGINE")
    vaha_sum = sum((c.get("vaha") or 0) for c in cats)
    if cats and abs(vaha_sum - 100) > 0.5:
        errs.append(f"součet vah musí být 100 (je {vaha_sum})")
    for c in cats:
        sk = c.get("skore")
        if not (isinstance(sk, (int, float)) and 0 <= sk <= 100):
            errs.append(f"kategorie {c.get('key')}: skore musí být číslo 0–100")
        if not str(c.get("duvod") or "").strip():
            errs.append(f"kategorie {c.get('key')}: chybí duvod (evidence)")
    coaching = sc.get("coaching") or {}
    for f in ("primary_issue", "focus_skill", "next_behavior", "drill", "metric"):
        if not str(coaching.get(f) or "").strip():
            errs.append(f"coaching.{f} chybí")
    return errs


def computed_total(sc: dict) -> float:
    cats = (sc.get("scores") or {}).get("categories") or []
    return round(sum((c.get("vaha") or 0) * (c.get("skore") or 0) / 100 for c in cats), 1)


def render_card(sc: dict) -> str:
    meta = sc["meta"]
    scores = sc["scores"]
    total = scores["total"]
    lines = [f"# Prodejní hodnocení - obchodník {meta['obchodnik']} - {meta['datum']}",
             f"_{meta['firma']}"
             + (f" · {meta.get('produkt')}" if meta.get("produkt") else "")
             + (f" · výsledek: {meta.get('vysledek')}" if meta.get("vysledek") else "") + "_",
             "", f"## Skóre: {round(total)} %", ""]
    for c in scores["categories"]:
        bod = round((c.get("vaha") or 0) * (c.get("skore") or 0) / 100, 1)
        lines.append(f"- **{CAT_LABEL.get(c['key'], c['key'])}**: {bod} / {c['vaha']} b  ·  {c.get('duvod','')}")
    # Dynamika hovoru — jen když je Conversation Intelligence (dodá fireflies skill); jinak vynech
    ci = sc.get("conversation_intelligence") or {}
    row = []
    if ci.get("talk_ratio_obchodnik") is not None:
        row.append(f"poměr mluvení obch./lead {ci['talk_ratio_obchodnik']} / {ci.get('talk_ratio_lead', '?')} %")
    if ci.get("longest_monologue"):
        row.append(f"nejdelší monolog {ci['longest_monologue']}")
    if ci.get("questions_obchodnik") is not None:
        row.append(f"otázky obchodníka {ci['questions_obchodnik']}")
    if ci.get("filler_words") is not None:
        row.append(f"výplňová slova {ci['filler_words']}")
    if ci.get("sentiment"):
        row.append(f"sentiment klienta {ci['sentiment']}")
    if row:
        lines += ["", "## Dynamika hovoru (z nahrávky)", "- " + " · ".join(row)]
    strengths = sc.get("strengths") or []
    if strengths:
        lines += ["", "## Co se povedlo"] + [f"- {s}" for s in strengths[:3]]
    co = sc.get("coaching") or {}
    lines += ["", "## Jedna věc ke zlepšení",
              f"- **Hlavní příčina:** {co.get('primary_issue','')}",
              f"- **Dovednost:** {co.get('focus_skill','')}",
              f"- **Na příštím hovoru:** {co.get('next_behavior','')}",
              f"- **Cvičení:** {co.get('drill','')}",
              f"- **Měříme:** {co.get('metric','')}"]
    unc = sc.get("uncertainties") or []
    if unc:
        lines += ["", "## Nejistoty (chybějící data)"] + [f"- {u}" for u in unc]
    eth = sc.get("ethics") or {}
    if eth.get("manipulace_detekovana"):
        lines += ["", "> ⚠️ Detekována manipulativní technika — viz evidence. Skóre je proto stropováno."]
    lines += ["", "_Detailní rozbor hovoru (fáze, citace, všechny námitky) v souboru `…-detail.md` vedle._"]
    return "\n".join(lines) + "\n"


def render_detail(sc: dict) -> str:
    """Detailní rozbor hovoru — souhrn, proč skóre v 8 oblastech, rozbor po částech
    s přepisy dialogů, hloubkový rozbor námitek a závěru, signály a plán.
    Karta = 1 věc ke zlepšení (souhrn). Detail = celý obraz, ze kterého se prodejce učí."""
    meta = sc["meta"]
    scores = sc["scores"]
    total = round(scores["total"])
    band = _tax.band(total)
    L = [f"# Hodnocení obchodníka: {meta['obchodnik']}",
         f"_{meta['firma']}"
         + (f" · {meta.get('produkt')}" if meta.get("produkt") else "")
         + f" · {meta['datum']}"
         + (f" · výsledek: {meta.get('vysledek')}" if meta.get("vysledek") else "") + "_",
         "", f"## Skóre: {total} % — {band}"]
    if sc.get("verdict"):
        L += ["", sc["verdict"]]

    # 1) PROČ TOHLE SKÓRE — všech 8 oblastí s odůvodněním
    L += ["", "## Proč tohle skóre — rozbor osmi oblastí", ""]
    for c in scores["categories"]:
        bod = round((c.get("vaha") or 0) * (c.get("skore") or 0) / 100, 1)
        L.append(f"**{CAT_LABEL.get(c['key'], c['key'])} — {bod} / {c['vaha']} b "
                 f"({round(c.get('skore') or 0)} %)**")
        L.append(f"{c.get('duvod', '')}")
        L.append("")

    # 2) ROZBOR PO ČÁSTECH — dialogy + co se stalo / jak mělo znít / dopad
    parts = sc.get("parts") or []
    if parts:
        L += ["## Detailní rozbor hovoru", "",
              "_Hovor rozsekaný na části: co přesně zaznělo, proč to zafungovalo nebo ne, "
              "a jak to mělo znít._", ""]
        for i, p in enumerate(parts, 1):
            head = f"### Část {i}"
            if p.get("cas"):
                head += f" · {p['cas']}"
            L.append(head)
            if p.get("nazev"):
                L.append(f"**{p['nazev']}**")
            if p.get("faze"):
                L.append(f"_Fáze: {p['faze']}_")
            for t in p.get("dialog") or []:
                who = t.get("kdo") or "?"
                pozn = f" _({t['poznamka']})_" if t.get("poznamka") else ""
                L.append(f"> **{who}:** {t.get('text', '')}{pozn}")
            if p.get("co_se_stalo"):
                L.append(f"- **Co se stalo:** {p['co_se_stalo']}")
            if p.get("jak_melo_znit"):
                L.append(f"- **Jak to mělo znít:** „{p['jak_melo_znit']}“")
            if p.get("dopad"):
                L.append(f"- **Dopad na obchod:** {p['dopad']}")
            L.append("")

    # 3) NÁMITKY DO HLOUBKY — u každé postup krok za krokem
    obj = sc.get("objections") or []
    if obj:
        L += ["## Práce s námitkami — do hloubky", "",
              "_Nejčastější místo, kde se obchody ztrácejí._", ""]
        for o in obj:
            nazev = OBJ_LABEL.get(o.get("typ", ""), o.get("typ", "námitka"))
            stav = "vyřešeno" if o.get("vyreseno") else "nevyřešeno"
            L.append(f"### Námitka — {nazev} · {stav}")
            if o.get("pricina"):
                L.append(f"_Skutečná příčina: {o['pricina']}_")
            if o.get("citace"):
                L.append(f"> **Klient:** {o['citace']}")
            if o.get("reakce"):
                L.append(f"> **Obchodník:** {o['reakce']}")
            if o.get("osetreni"):
                L.append(f"- **Co se stalo:** {o['osetreni']}")
            for j, krok in enumerate(o.get("postup") or [], 1):
                L.append(f"{j}. {krok}")
            L.append("")

    # 4) ZÁVĚR DO HLOUBKY
    cl = sc.get("closing_rozbor") or {}
    if cl:
        L += ["## Closing a další krok — do hloubky", ""]
        if cl.get("citace"):
            L.append(f"> **Obchodník:** {cl['citace']}")
        if cl.get("chyby"):
            L.append("**Co bylo špatně:**")
            L += [f"- {ch}" for ch in cl["chyby"]]
        if cl.get("jak_melo_znit"):
            L.append(f"**Jak to mělo znít:** „{cl['jak_melo_znit']}“")
        for j, krok in enumerate(cl.get("postup") or [], 1):
            L.append(f"{j}. {krok}")
        if cl.get("dopad"):
            L.append(f"**Dopad na obchod:** {cl['dopad']}")
        L.append("")

    # 5) SIGNÁLY
    tt = sc.get("three_tens") or {}
    ci = sc.get("conversation_intelligence") or {}
    sig = []
    if tt:
        sig.append(f"jistota produkt {tt.get('produkt', '?')}/10 · obchodník "
                   f"{tt.get('obchodnik', '?')}/10 · firma {tt.get('firma', '?')}/10")
    if ci.get("talk_ratio_obchodnik") is not None:
        sig.append(f"poměr mluvení {ci['talk_ratio_obchodnik']}/{ci.get('talk_ratio_lead', '?')} %")
    if ci.get("longest_monologue"):
        sig.append(f"nejdelší monolog {ci['longest_monologue']}")
    if ci.get("questions_obchodnik") is not None:
        sig.append(f"otázky obchodníka {ci['questions_obchodnik']}")
    if ci.get("sentiment"):
        sig.append(f"sentiment klienta {ci['sentiment']}")
    if sig:
        L += ["## Signály z hovoru", "- " + " · ".join(sig)]
        if sc.get("signaly_cteni"):
            L.append(f"- **Čtení:** {sc['signaly_cteni']}")
        L.append("")

    # 6) CO SE POVEDLO + PLÁN
    strengths = sc.get("strengths") or []
    if strengths:
        L += ["## Co se povedlo"] + [f"- {s}" for s in strengths] + [""]
    co = sc.get("coaching") or {}
    L += ["## Plán na příští hovor"]
    for j, krok in enumerate(co.get("plan") or [], 1):
        L.append(f"{j}. {krok}")
    L += [f"- **Hlavní příčina:** {co.get('primary_issue', '')}",
          f"- **Dovednost:** {co.get('focus_skill', '')}",
          f"- **Na příštím hovoru:** {co.get('next_behavior', '')}"]

    # 7) CVIČENÍ DO PŘÍŠTĚ — samostatná sekce na konci
    drills = co.get("drills") or []
    if drills:
        L += ["", "## Cvičení do příště", "",
              "_Krátký trénink na to, co v hovoru chybělo. Nacvičte nanečisto, "
              "než půjdete do dalšího jednání._", ""]
        for i, d in enumerate(drills, 1):
            head = f"### {i}. {d.get('nazev', 'Cvičení')}"
            L.append(head)
            meta_l = [x for x in [d.get("cil") and f"Cíl: {d['cil']}", d.get("trvani")] if x]
            if meta_l:
                L.append(f"_{' · '.join(meta_l)}_")
            for j, v in enumerate(d.get("vety") or [], 1):
                L.append(f"{j}. „{v}“")
            if d.get("jak_trenovat"):
                L.append(f"- **Jak trénovat:** {d['jak_trenovat']}")
            L.append("")
    elif co.get("drill"):
        L += ["", "## Cvičení do příště", f"- {co['drill']}"]

    metriky = co.get("metriky") or ([co["metric"]] if co.get("metric") else [])
    if metriky:
        L += ["", "## Co měříme na příštím hovoru"] + [f"- {m}" for m in metriky]

    unc = sc.get("uncertainties") or []
    if unc:
        L += ["", "## Nejistoty (chybějící data)"] + [f"- {u}" for u in unc]
    return "\n".join(L) + "\n"



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="cesta k JSON scorecardu (nebo - pro stdin)")
    ap.add_argument("--execute", action="store_true", help="reálně zapiš (default dry-run)")
    ap.add_argument("--call-id", default=None,
                    help="stabilní ID hovoru (audit P1-13) — jinak se odvodí z obsahu")
    ap.add_argument("--revise", action="store_true",
                    help="přepsat existující bundle jako novou revizi")
    ap.add_argument("--card", action="store_true", help="vytiskni human-readable kartu")
    ap.add_argument("--root", default=str(DOCS_ROOT), help="kořen scorecards (default /documents/sales/scorecards)")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    try:
        sc = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"CHYBA: vstup není validní JSON: {e}", file=sys.stderr)
        sys.exit(3)

    errs = validate(sc)
    if errs:
        print("CHYBA validace scorecardu:\n- " + "\n- ".join(errs), file=sys.stderr)
        sys.exit(3)

    # Runtime i checkpoint musí poznat přesnou verzi writeru bez odhadu z
    # názvu souboru nebo volného textu v manifestu.
    sc["skillVersion"] = SKILL_VERSION

    ct = computed_total(sc)
    given = sc["scores"]["total"]
    if abs(ct - given) > 1.0:
        print(f"POZOR: scores.total ({given}) neodpovídá součtu z vah ({ct}) — "
              f"opravuji na {ct}.", file=sys.stderr)
        sc["scores"]["total"] = ct

    # Etický strop (SCORING_ENGINE pravidlo 3): doložená manipulace drží total pod 60.
    # MUSÍ být až po přepočtu z vah, jinak by přepočet strop potichu zrušil.
    if (sc.get("ethics") or {}).get("manipulace_detekovana") and sc["scores"]["total"] >= 60:
        print("POZOR: manipulace detekována → total stropuji na 59 "
              "(SCORING_ENGINE pravidlo 3).", file=sys.stderr)
        sc["scores"]["total"] = 59

    meta = sc["meta"]
    out_dir = Path(args.root) / slug(meta["obchodnik"])
    # Audit P1-13: stabilní identita hovoru. Dřív se při kolizi vyrobil
    # `-2`, `-3`, takže stejný hovor zpracovaný dvakrát měl dva scorecardy
    # a Analytik pak zkresloval průměry. `callId` je povinný nebo se odvodí
    # deterministicky z obsahu — stejný vstup dá stejné jméno.
    call_id = meta.get("callId") or meta.get("call_id") or args.call_id
    if not call_id:
        import hashlib as _hl
        seed = "|".join(str(meta.get(k, "")) for k in ("obchodnik", "datum", "firma", "cas"))
        seed += "|" + str(sc.get("verdict", ""))[:200]
        call_id = _hl.sha256(seed.encode("utf-8")).hexdigest()[:10]
    base = f"{meta['datum']}-{slug(meta['firma'])}-{slug(str(call_id))}"
    fname = base
    json_path = out_dir / f"{fname}.json"
    card_path = out_dir / f"{fname}.md"
    detail_path = out_dir / f"{fname}-detail.md"
    card = render_card(sc)
    detail = render_detail(sc)

    if args.card or not args.execute:
        print(card)

    if not args.execute:
        print(f"[dry-run] zapsal bych:\n  {json_path}\n  {card_path} (souhrn)\n"
              f"  {detail_path} (detailní rozbor)\nSpusť s --execute pro reálný zápis.", file=sys.stderr)
        return

    # Audit P1-13: tři samostatné zápisy bez commitu nechaly po pádu jen část
    # bundlu. Teď se všechno zapíše do temp, zvaliduje a přejmenuje — buď
    # celý scorecard, nebo nic. Zámek drží po celou dobu, takže dva souběžné
    # běhy stejného hovoru se nemohou překřížit.
    bundle_dir = out_dir / fname
    try:
        with _as.locked(bundle_dir):
            written, why = _as.write_bundle(
                bundle_dir,
                {f"{fname}.json": json.dumps(sc, ensure_ascii=False, indent=2),
                 f"{fname}.md": card,
                 f"{fname}-detail.md": detail},
                manifest={"callId": str(call_id), "obchodnik": meta.get("obchodnik"),
                          "firma": meta.get("firma"), "datum": meta.get("datum"),
                          "skore": sc["scores"]["total"],
                          "skillVersion": SKILL_VERSION,
                          "kbVerze": sc.get("meta", {}).get("kb_verze")},
                overwrite=bool(args.revise))
    except TimeoutError as e:
        print(f"CHYBA: {e}", file=sys.stderr)
        sys.exit(4)
    except OSError as e:
        print(f"CHYBA zápisu: {e}", file=sys.stderr)
        sys.exit(4)

    if not written:
        # Stejný callId podruhé není chyba — je to idempotence.
        print(json.dumps({"success": True, "already_written": True,
                          "skillVersion": SKILL_VERSION,
                          "callId": str(call_id), "bundle": str(bundle_dir),
                          "poznamka": why}, ensure_ascii=False))
        return
    print(f"OK: scorecard uložen → {bundle_dir} (skóre {round(sc['scores']['total'])} %)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
