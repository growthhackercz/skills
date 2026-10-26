#!/usr/bin/env python3
"""
build-finishing.py — vygeneruje hf/index.html (HyperFrames finishing) z briefu.

POSLEDNÍ KROK před schválením. Titulky se časují SLOVO-NA-SLOVO z FINÁLNÍHO
sestříhaného videa (whisper na _base.mp4 = přesná timeline po všech mid-cutech),
NE z per-scene klipů — jinak titulky „lítají“. Viz references/finishing-hyperframes.md.

Vstup:
  --brief   video-brief.json (obsahuje subtitles.lines, flashes, punch, subtitles.gradient/font/bottom_px)
  --base    _base.mp4 (concat ořezaných klipů = finální dialogová stopa)
  --trim    _trim.txt (výstup trim-clips.py — starts/durations scén)
  --hf      HyperFrames projekt (default: <brief_dir>/hf) s assets/clips/<scene>.mp4 a assets/vendor/fonts/
Výstup: <hf>/index.html + výpis časování.

brief["subtitles"]["lines"] = { "<scene_id>": [ [pre, big, post], ... ] }
  pre  = běžná slova před klíčovým (může být "")
  big  = velké gradientové klíčové slovo/fráze na vlastním řádku (může být "")
  post = běžná slova za klíčovým (může být "")
Jedna položka = jedna replika (mluvčí se NEmíchají).

Vyžaduje ffmpeg. FAL_KEY a fal_client jsou potřeba jen tehdy, když pro aktuální
media hash neexistuje uložený transcript nebo operátor výslovně žádá refresh.
"""
from __future__ import annotations
import argparse, asyncio, json, os, re, subprocess, sys
from pathlib import Path

UR_LAT = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
UR_EXT = "U+0100-02AF,U+0304,U+0308,U+0329,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"


# whisper píše čísla ČÍSLICEMI („30"), brief slovy („třicet") → sjednotit, jinak char-aligner ujede
NUM_CZ = {
    "0": "nula", "1": "jedna", "2": "dva", "3": "tři", "4": "čtyři", "5": "pět",
    "6": "šest", "7": "sedm", "8": "osm", "9": "devět", "10": "deset", "11": "jedenáct",
    "12": "dvanáct", "13": "třináct", "14": "čtrnáct", "15": "patnáct", "20": "dvacet",
    "30": "třicet", "40": "čtyřicet", "50": "padesát", "60": "šedesát", "70": "sedmdesát",
    "80": "osmdesát", "90": "devadesát", "100": "sto",
}


def _n(x):
    # čísla → slova (aby délka znaků odpovídala briefu), pak strip nealfanum
    x = re.sub(r"\d+", lambda m: NUM_CZ.get(m.group(0), m.group(0)), x.lower())
    return re.sub(r"[^\wáčďéěíňóřšťúůýž]+", "", x)


async def whisper_words(base: Path) -> list:
    import fal_client
    async def up(p, t=5):
        for i in range(t):
            try:
                return await fal_client.upload_file_async(str(p))
            except Exception:
                if i == t - 1:
                    raise
                await asyncio.sleep(4 * (i + 1))
    for i in range(5):
        try:
            u = await up(base)
            h = await fal_client.submit_async("fal-ai/whisper",
                    arguments={"audio_url": u, "language": "cs", "chunk_level": "word"})
            r = await h.get()
            return [[c["text"].strip(), c.get("timestamp")] for c in r.get("chunks", [])]
        except Exception:
            if i == 4:
                raise
            await asyncio.sleep(4 * (i + 1))


def parse_trim(trim_path: Path):
    starts, durs = {}, {}
    for ln in open(trim_path):
        if "start ve videu" in ln:
            sid = ln.split(":")[0].strip()
            durs[sid] = float(ln.split("] =")[1].split("s |")[0])
            starts[sid] = float(ln.rsplit("start ve videu:", 1)[1].replace("s", "").strip())
    return starts, durs


def load_dialogue_qa():
    script_path = Path(__file__).resolve()
    candidates = [script_path.parents[2] / "_lib"]
    for env_name in ("OPENCLAW_HOME", "CC_OPENCLAW_HOME"):
        raw = os.environ.get(env_name, "").strip()
        if raw:
            home = Path(raw).expanduser()
            candidates.extend([home / "cs-skills" / "_lib", home / ".openclaw" / "cs-skills" / "_lib"])
    candidates.append(Path.home() / ".openclaw" / "cs-skills" / "_lib")
    for lib_dir in candidates:
        if not (lib_dir / "dialogue_qa.py").exists():
            continue
        if str(lib_dir) not in sys.path:
            sys.path.insert(0, str(lib_dir))
        from dialogue_qa import compare_dialogue, sha256_file  # type: ignore
        return compare_dialogue, sha256_file
    raise RuntimeError("dialogue_qa.py nenalezen v cs-skills/_lib")


def write_dialogue_qa_report(brief, brief_path: Path, base: Path, words, starts, durs):
    compare_dialogue, sha256_file = load_dialogue_qa()
    qa_config = brief.get("dialogueQa") or {}
    required = int(brief.get("briefVersion") or 1) >= 2 or bool(qa_config.get("required"))
    scenes = []
    for scene in brief.get("scenes", []):
        scene_id = scene.get("id")
        line = scene.get("line") or {}
        expected = line.get("text") or ""
        start = starts.get(scene_id)
        duration = durs.get(scene_id)
        scene_words = []
        if start is not None and duration is not None:
            end = start + duration
            for text, timestamp in words:
                if not timestamp:
                    continue
                word_start = timestamp[0] if timestamp[0] is not None else timestamp[1]
                if word_start is not None and start - 0.08 <= float(word_start) < end:
                    scene_words.append({"text": text, "timestamp": timestamp})
        aliases = dict(qa_config.get("aliases") or {})
        aliases.update(line.get("qaAliases") or {})
        scenes.append(compare_dialogue(expected, scene_words, scene_id=scene_id, aliases=aliases))

    report = {
        "reportVersion": 1,
        "required": required,
        "briefPath": str(brief_path),
        "briefSha256": sha256_file(brief_path),
        "mediaPath": str(base),
        "mediaSha256": sha256_file(base),
        "scenes": scenes,
        "ok": all(scene.get("status") in {"pass", "not_applicable"} for scene in scenes),
    }
    logs = brief_path.parent / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "final-whisper-words.json").write_text(
        json.dumps({
            "mediaPath": str(base),
            "mediaSha256": report["mediaSha256"],
            "words": words,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path = logs / "dialogue-qa-final.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report, report_path


def cached_whisper_words(brief_path: Path, base: Path):
    _, sha256_file = load_dialogue_qa()
    cache_path = brief_path.parent / "logs" / "final-whisper-words.json"
    if not cache_path.exists():
        return None
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if cache.get("mediaSha256") != sha256_file(base) or not isinstance(cache.get("words"), list):
        return None
    return cache["words"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--base", default="_base.mp4")
    ap.add_argument("--trim", default="_trim.txt")
    ap.add_argument("--hf", default=None)
    ap.add_argument("--refresh-transcript", action="store_true", help="ignoruj hashovaný transcript cache a proveď nový placený Whisper call")
    args = ap.parse_args()

    brief_path = Path(args.brief).resolve()
    d = brief_path.parent
    base = (d / args.base) if not os.path.isabs(args.base) else Path(args.base)
    trim = (d / args.trim) if not os.path.isabs(args.trim) else Path(args.trim)
    hf = Path(args.hf) if args.hf else (d / "hf")
    brief = json.load(open(brief_path))

    subs_cfg = brief.get("subtitles", {})
    LINES = subs_cfg.get("lines", {})   # {scene_id: [[pre,big,post], ...]}
    if not LINES:
        print("❌ brief.subtitles.lines chybí — doplň repliky per scéna."); sys.exit(2)
    g = subs_cfg.get("gradient", ["#5AE8FF", "#14A8FF", "#0056C8"])
    grad = f"linear-gradient(150deg,{g[0]} 0%,{g[1]} 50%,{g[2]} 100%)"
    bp = subs_cfg.get("bottom_px", 420)
    # dokumentární režim (rodina „dokument“): žádné velké kinetické big-slovo — klíčová slova
    # se vykreslí jako běžná decentní slova (native pocit, ne reklama). Viz finishing-hyperframes.md.
    DOC = subs_cfg.get("style") == "documentary"

    starts, durs = parse_trim(trim)
    order = [s["id"] for s in brief["scenes"]]
    T = round(sum(durs.values()), 2)
    cuts = [round(starts[s], 3) for s in brief.get("flashes", []) if s in starts]

    if not base.exists():
        print(f"❌ finální base chybí: {base}"); sys.exit(2)
    BW = None if args.refresh_transcript else cached_whisper_words(brief_path, base)
    if BW is not None:
        print(f"→ používám hashovaný transcript cache pro {base.name} (bez provider callu)")
    else:
        if not os.environ.get("FAL_KEY"):
            print("❌ FAL_KEY není nastavený a pro aktuální media hash neexistuje transcript cache"); sys.exit(2)
        print(f"→ whisper FINÁLNÍHO videa {base.name} (absolutní časy) …")
        BW = asyncio.run(whisper_words(base))
    bwords = [(w, ts) for w, ts in BW if ts]
    qa_report, qa_report_path = write_dialogue_qa_report(brief, brief_path, base, BW, starts, durs)
    if not qa_report["ok"]:
        failed = [
            f"{scene.get('sceneId')}={scene.get('status')}"
            for scene in qa_report["scenes"]
            if scene.get("status") not in {"pass", "not_applicable"}
        ]
        detail = ", ".join(failed)
        if qa_report["required"]:
            print(f"❌ Dialogue QA blokuje finishing: {detail}. Report: {qa_report_path}")
            sys.exit(3)
        print(f"⚠️ Legacy brief: dialogue QA našlo {detail}; finishing pokračuje jen kvůli kompatibilitě. Report: {qa_report_path}")
    else:
        print(f"✅ Dialogue QA: {qa_report_path}")

    # Vizuální střihy ve finálním _base = concaty scén (jisté) + interní omni shot-cuty (detekce).
    # Titulek nesmí přesáhnout přes střih do dalšího záběru (jinak „problikne").
    det = subprocess.run(["ffmpeg", "-i", str(base), "-filter:v",
                          "select='gt(scene,0.25)',showinfo", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    CUTS = sorted(set([round(starts[s], 3) for s in order[1:]]
                      + [float(x) for x in re.findall(r"pts_time:([0-9.]+)", det)]))

    def next_cut_after(t):
        for c in CUTS:
            if c > t + 0.2:
                return c
        return None

    # ploché display slovo v pořadí scén
    flat = []
    for sid in order:
        for ui, (pre, big, post) in enumerate(LINES.get(sid, [])):
            for w in pre.split(): flat.append([sid, ui, "pre", w])
            for w in big.split(): flat.append([sid, ui, "big", w])
            for w in post.split(): flat.append([sid, ui, "post", w])

    # Zarovnání display→whisper po ZNACÍCH — zvládá OBA směry:
    #   • whisper slovo rozdělené na víc tokenů („e" + „-maily" pro „e-maily")  → jinak se vše za tím posune
    #   • whisper slova slepená („dorána" pro „do" + „rána")
    # Každé display slovo spotřebuje přesně tolik znaků z whisper char-streamu, kolik má (přes hranice tokenů).
    def _tok(k):
        w0, ts = bwords[min(k, len(bwords) - 1)]
        t0, t1 = ts; t1 = t1 or t0 + 0.35
        t0c = round(t1 - 0.6, 3) if (t1 - t0) > 1.2 else t0   # de-stretch přes ticho
        return _n(w0), t0c, t1
    times = []; j = 0; coff = 0   # coff = kolik znaků aktuálního whisper tokenu už spotřebováno
    for (sid, ui, part, w) in flat:
        if not bwords:
            times.append(0.0); continue
        nn, t0c, t1 = _tok(j)
        L = max(1, len(nn))
        times.append(round(t0c + (min(coff, L) / L) * (t1 - t0c), 3))   # čas = pozice v tokenu
        need = len(_n(w))
        while need > 0 and j < len(bwords):
            nn, _, _ = _tok(j)
            avail = len(nn) - coff
            if avail <= 0:
                j += 1; coff = 0; continue
            take = min(need, avail); coff += take; need -= take
            if coff >= len(nn):
                j += 1; coff = 0

    # 1. pass — posbírej repliky (uid, idxs, t_first, t_last) pro lookahead na hold
    utt = []
    gi = 0
    for sid in order:
        for ui, (pre, big, post) in enumerate(LINES.get(sid, [])):
            pre_w, big_w, post_w = pre.split(), big.split(), post.split()
            # 🛑 VŽDY JEN JEDNO zvýrazněné klíčové slovo (big). Když je v big víc slov,
            # přebytek přesuň doleva do běžných slov (pre) a zvýrazni jen POSLEDNÍ (pointa).
            if len(big_w) > 1:
                pre_w = pre_w + big_w[:-1]
                big_w = big_w[-1:]
            big = big_w[0] if big_w else ""
            n = len(pre_w) + len(big_w) + len(post_w)
            idxs = list(range(gi, gi + n)); gi += n
            if not idxs:
                continue
            utt.append({"sid": sid, "ui": ui, "big": big, "pre_w": pre_w, "big_w": big_w, "post_w": post_w,
                        "idxs": idxs, "t_first": times[idxs[0]], "t_last": times[idxs[-1]]})

    # hold titulku: doznění po poslední slově + zaručená čitelnost, ale titulek se
    # NEroztahuje přes pauzu až k další replice — když je mezi replikami ticho, titulek
    # po doznění zmizí (nevisí zbytečně). Zároveň NIKDY moc krátce (musí být čitelný).
    HOLD_MIN, HOLD_TAIL, GAP = 1.2, 0.85, 0.12   # HOLD_MIN = min. viditelnost od náběhu (čitelnost)
    for i, u in enumerate(utt):
        nxt = utt[i + 1]["t_first"] if i + 1 < len(utt) else None
        hide = max(u["t_last"] + HOLD_TAIL, u["t_first"] + HOLD_MIN)   # doznění NEBO min čitelnost
        if nxt is not None:
            hide = min(hide, nxt - GAP)                                # nikdy nepřekryj další repliku
            hide = max(hide, u["t_first"] + 0.6)                       # pojistka: i těsně před další ať je vidět
        # 🛑 titulek NIKDY nesmí přesáhnout přes vizuální STŘIH do dalšího záběru (jinak „problikne").
        # Platí pro hranice scén I interní omni shot-cuty. Clamp = nejbližší střih po konci řeči.
        scene_end = starts[u["sid"]] + durs[u["sid"]]
        hide = min(hide, scene_end - 0.06)
        nc = next_cut_after(u["t_last"])
        if nc is not None:
            hide = min(hide, nc - 0.06)
        u["hide"] = round(hide, 3)

    # 2. pass — postav HTML/JS
    subs_html, js, dump = [], [], []
    for u in utt:
            sid, ui = u["sid"], u["ui"]
            pre_w, big_w, post_w, big = u["pre_w"], u["big_w"], u["post_w"], u["big"]
            idxs = u["idxs"]
            for gidx in idxs:
                dump.append((round(times[gidx], 2), sid, flat[gidx][3], "BIG" if flat[gidx][2] == "big" else ""))
            t_first = u["t_first"]; hide = u["hide"]
            uid = f"{sid}u{ui}"
            def spans(words, off):
                return "".join(f'<span class="word" id="w-{uid}-{off+k}">{w2}</span>' for k, w2 in enumerate(words))
            if DOC:
                # dokument: všechna slova (vč. klíčových) jako běžná decentní slova v jednom toku, bez big/pop
                allw = pre_w + big_w + post_w
                inner = f'<div class="line">{spans(allw,0)}</div>' if allw else ""
                subs_html.append(f'      <div id="sub-{uid}" class="sub docsub clip" data-start="{max(0,round(t_first-0.05,2))}" '
                                 f'data-duration="{round(hide-t_first+0.1,2)}" data-track-index="2">{inner}</div>')
                for k in range(len(allw)):
                    js.append(f'tl.fromTo("#w-{uid}-{k}",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.22,ease:"power2.out"}},{times[idxs[k]]});')
                js.append(f'tl.to("#sub-{uid}",{{opacity:0,duration:0.22,ease:"power2.in"}},{hide});')
            else:
                inner = ""
                if pre_w: inner += f'<div class="line">{spans(pre_w,0)}</div>'
                if big_w: inner += f'<div class="big" id="w-{uid}-big">{big}</div>'
                if post_w: inner += f'<div class="line">{spans(post_w,len(pre_w)+len(big_w))}</div>'
                subs_html.append(f'      <div id="sub-{uid}" class="sub clip" data-start="{max(0,round(t_first-0.05,2))}" '
                                 f'data-duration="{round(hide-t_first+0.1,2)}" data-track-index="2">{inner}</div>')
                for k in range(len(pre_w)):
                    js.append(f'tl.fromTo("#w-{uid}-{k}",{{opacity:0,y:26,filter:"blur(5px)"}},{{opacity:1,y:0,filter:"blur(0px)",duration:0.18,ease:"power3.out"}},{times[idxs[k]]});')
                if big_w:
                    js.append(f'tl.fromTo("#w-{uid}-big",{{opacity:0,scale:0.72,y:12}},{{opacity:1,scale:1,y:0,duration:0.24,ease:"back.out(1.7)"}},{times[idxs[len(pre_w)]]});')
                for k in range(len(post_w)):
                    di = len(pre_w) + len(big_w) + k
                    js.append(f'tl.fromTo("#w-{uid}-{di}",{{opacity:0,y:26,filter:"blur(5px)"}},{{opacity:1,y:0,filter:"blur(0px)",duration:0.18,ease:"power3.out"}},{times[idxs[di]]});')
                js.append(f'tl.to("#sub-{uid}",{{opacity:0,duration:0.18,ease:"power2.in"}},{hide});')

    # clamp prekryvu (mluvci se NEmichaji)
    def sd(html):
        m = re.search(r'data-start="([\d.]+)" data-duration="([\d.]+)"', html); return float(m.group(1)), float(m.group(2))
    subs_html.sort(key=lambda h: sd(h)[0])
    for i in range(len(subs_html) - 1):
        st, du = sd(subs_html[i]); nst, _ = sd(subs_html[i + 1])
        maxdu = round(max(0.3, nst - 0.1 - st), 2)
        if du > maxdu:
            subs_html[i] = subs_html[i].replace(f'data-duration="{du}"', f'data-duration="{maxdu}"', 1)

    # video klipy
    vids = "\n".join(
        f'        <video id="v-{sid}" class="clip clipvid" src="assets/clips/{sid}.mp4" data-start="{starts[sid]}" '
        f'data-duration="{round((starts[order[i+1]] if i+1<len(order) else T)-starts[sid]-0.002,3)}" '
        f'data-track-index="0" muted playsinline></video>'
        for i, sid in enumerate(order))

    flashes_html = "\n".join(
        f'      <div id="flash{i+1}" class="flash clip" data-start="{round(c-0.7,2)}" data-duration="1.55" data-track-index="3"></div>'
        for i, c in enumerate(cuts))

    # punch (volitelné): {"text": "...", "scene": "<id>", "word": "<slovo>"} -> pop na absolutní čas slova
    punch = brief.get("punch")
    punch_html = punch_js = ""
    if punch and punch.get("text"):
        pw = _n(punch.get("word", punch["text"]))
        pt = next((t0 for w, (t0, t1) in bwords if _n(w).startswith(pw)), None)
        if pt is not None:
            punch_html = f'      <div id="punch" class="clip" data-start="{round(pt-0.4,2)}" data-duration="1.1" data-track-index="5"><span>{punch["text"]}</span></div>'
            punch_js = (f'tl.fromTo("#punch",{{opacity:0,scale:0.55}},{{opacity:1,scale:1,duration:0.14,ease:"back.out(2)"}},{round(pt,2)});'
                        f'tl.set("#punch",{{opacity:0}},{round(pt,2)}+0.85);')

    fonts = "".join(f'''
      @font-face {{ font-family:"Poppins"; font-weight:{w}; font-display:block; src:url("assets/vendor/fonts/poppins-{w}-latin{e}.woff2") format("woff2"); unicode-range:{ur}; }}'''
        for w in (500, 800, 900) for e, ur in (("", UR_LAT), ("ext", UR_EXT)))

    html = f"""<!doctype html>
<html lang="cs" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{fonts}
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
      body {{ font-family:"Poppins", sans-serif; }}
      .clipvid {{ position:absolute; inset:0; width:1080px; height:1920px; object-fit:cover; }}
      #scrim {{ position:absolute; left:0; right:0; bottom:0; height:640px; z-index:15;
               background:linear-gradient(to top, rgba(1,7,26,.74) 0%, rgba(1,7,26,.34) 48%, rgba(1,7,26,0) 100%); }}
      .sub {{ position:absolute; left:0; right:0; width:100%; bottom:{bp}px; padding:0 44px; z-index:20;
             display:flex; flex-direction:column; align-items:center; text-align:center; gap:6px; }}
      .sub .line {{ width:100%; display:flex; flex-wrap:wrap; justify-content:center; gap:0 16px; line-height:0.98; }}
      .sub .line .word {{ font-weight:500; font-size:74px; letter-spacing:-1.5px; color:#fff;
                         text-shadow:0 4px 24px rgba(0,0,0,.9); will-change:transform,opacity; }}
      .sub .big {{ font-weight:800; font-size:172px; letter-spacing:-6px; line-height:1.06; padding-bottom:0.06em;
                  background:{grad}; -webkit-background-clip:text; background-clip:text;
                  -webkit-text-fill-color:transparent; filter:drop-shadow(0 6px 24px rgba(23,198,255,.5)); will-change:transform,opacity; }}
      /* dokumentární režim: decentní menší titulky, žádné velké gradientové slovo (native pocit) */
      .docsub .line .word {{ font-weight:500; font-size:52px; letter-spacing:-1px; color:#fff;
                            text-shadow:0 2px 14px rgba(0,0,0,.85); }}
      .flash {{ position:absolute; inset:0; background:#fff; opacity:0; z-index:40; }}
      #punch {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
               z-index:50; font-weight:900; font-size:300px; letter-spacing:-9px; will-change:transform,opacity; }}
      #punch span {{ background:{grad}; -webkit-background-clip:text; background-clip:text;
                    -webkit-text-fill-color:transparent; filter:drop-shadow(0 8px 30px rgba(0,120,200,.35)); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{T}" data-width="1080" data-height="1920">
      <div data-layout-ignore>
{vids}
      </div>
      <div id="scrim"></div>
{chr(10).join(subs_html)}
{flashes_html}
{punch_html}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      "+l for l in js)}
      {json.dumps(cuts)}.forEach((cut, i) => {{
        const f = "#flash" + (i + 1);
        tl.fromTo(f, {{ opacity:0 }}, {{ opacity:1, duration:0.50, ease:"sine.inOut" }}, cut - 0.54);
        tl.to(f, {{ opacity:0, duration:0.58, ease:"sine.inOut" }}, cut + 0.10);
      }});
      {punch_js}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>"""
    (hf / "index.html").write_text(html)
    print(f"✅ {hf}/index.html  T={T}s  cuts={cuts}  punch={'ano' if punch_html else 'ne'}")
    print("=== ČASOVÁNÍ TITULKŮ (z finálního videa) ===")
    for t, sid, w, tag in dump:
        print(f"  {t:5.2f}s  {sid}  {w} {tag}")


if __name__ == "__main__":
    main()
