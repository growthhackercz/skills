#!/usr/bin/env python3
"""Finální sestavení (ffmpeg) z manifestu. Stdlib-only.

Vezme video (overlay render muted, NEBO klipy s xfade) + namixuje audio
(VO beaty + hudba s fade + SFX na beaty) + outro fade do černé. Viz references/assembly.md.

Použití:  python3 assemble.py --manifest mix.json

mix.json schéma:
{
  "video": "overlay_render.mp4",                 // muted video s textem (overlay render)
  // NEBO: "clips": ["c1.mp4","c2.mp4","c3.mp4"], "xfades": [{"t":"smoothleft","d":0.6,"off":14.47}, ...]
  "out": "output/final.mp4",
  "duration": 42.6,                              // -t finálu
  "music": {"file":"sfx/music.mp3","vol":0.14,"fade_st":38.3,"fade_d":4.2},
  "beats": [{"file":"beats/o1.mp3","start":0.2,"vol":1.15}, ...],
  "sfx":   [{"file":"sfx/pop.mp3","start":11.0,"vol":0.5,"trim":null}, ...],
  "outro": {"freeze":0.7,"v_fade_st":41.95,"v_fade_d":0.65,"a_fade_st":41.5,"a_fade_d":1.0}
}
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

def ms(t): return int(round(float(t) * 1000))

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
        from dialogue_qa import validate_saved_report  # type: ignore
        return validate_saved_report
    raise RuntimeError("dialogue_qa.py nenalezen v cs-skills/_lib")

def require_dialogue_qa(manifest, manifest_path):
    config = manifest.get("dialogueQa") or {}
    if not isinstance(config, dict):
        sys.exit("Dialogue QA konfigurace musí být objekt")
    if not config.get("required"):
        return
    reports = config.get("reports") or []
    if not isinstance(reports, list) or not reports or not all(isinstance(path, str) and path.strip() for path in reports):
        sys.exit("Dialogue QA je povinné, ale manifest neobsahuje dialogueQa.reports")
    validate_saved_report = load_dialogue_qa()
    failures = []
    for raw_path in reports:
        report_path = Path(raw_path)
        if not report_path.is_absolute():
            report_path = manifest_path.parent / report_path
        if not report_path.exists():
            failures.append(f"{report_path}: chybí")
            continue
        try:
            report = json.load(open(report_path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"{report_path}: neplatný report ({exc})")
            continue
        if not isinstance(report, dict):
            failures.append(f"{report_path}: report musí být objekt")
            continue
        media = report.get("mediaPath")
        ok, reason = validate_saved_report(report, media if media else None)
        if not ok:
            failures.append(f"{report_path}: {reason}")
    if failures:
        sys.exit("Dialogue QA blokuje assembly: " + "; ".join(failures))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--manifest", required=True)
    manifest_path = Path(ap.parse_args().manifest).resolve()
    m = json.load(open(manifest_path, encoding="utf-8"))
    require_dialogue_qa(m, manifest_path)
    out = m["out"]; os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    inputs, fc, vlabel = [], [], None

    # ---- VIDEO ----
    if "video" in m:
        inputs.append(m["video"]); base = len(inputs)  # video je input 0
        vsrc = "[0:v]"
    else:  # klipy + xfade
        clips = m["clips"]; xf = m.get("xfades", [])
        for c in clips: inputs.append(c)
        for i in range(len(clips)):
            fc.append(f"[{i}:v]scale=1280:720,setsar=1,fps=30[v{i}]")
        cur = "[v0]"
        for i, x in enumerate(xf):
            nxt = f"[vx{i}]"
            fc.append(f"{cur}[v{i+1}]xfade=transition={x['t']}:duration={x['d']}:offset={x['off']}{nxt}")
            cur = nxt
        vsrc = cur
        base = len(clips)
    # outro: freeze last frame + fade do černé
    outro = m.get("outro", {})
    vchain = vsrc
    if outro.get("freeze"):
        fc.append(f"{vchain}tpad=stop_mode=clone:stop_duration={outro['freeze']}[vf]"); vchain = "[vf]"
    if outro.get("v_fade_st") is not None:
        fc.append(f"{vchain}fade=t=out:st={outro['v_fade_st']}:d={outro.get('v_fade_d',0.7)}[vv]"); vchain = "[vv]"
    vlabel = vchain

    # ---- AUDIO ----
    labels = []
    mus = m.get("music")
    if mus:
        inputs.append(mus["file"]); idx = len(inputs) - 1
        ch = f"[{idx}:a]volume={mus.get('vol',0.14)}"
        if mus.get("fade_st") is not None:
            ch += f",afade=t=out:st={mus['fade_st']}:d={mus.get('fade_d',4)}"
        ch += "[bed]"; fc.append(ch); labels.append("[bed]")
    for n, b in enumerate(m.get("beats", [])):
        inputs.append(b["file"]); idx = len(inputs) - 1
        fc.append(f"[{idx}:a]adelay={ms(b['start'])}:all=1,volume={b.get('vol',1.15)}[vo{n}]"); labels.append(f"[vo{n}]")
    for n, s in enumerate(m.get("sfx", [])):
        inputs.append(s["file"]); idx = len(inputs) - 1
        ch = f"[{idx}:a]"
        if s.get("trim"): ch += f"atrim=0:{s['trim']},asetpts=PTS-STARTPTS,afade=t=out:st={max(0,float(s['trim'])-0.4)}:d=0.4,"
        ch += f"volume={s.get('vol',0.5)},adelay={ms(s['start'])}:all=1[s{n}]"; fc.append(ch); labels.append(f"[s{n}]")
    achain = "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,alimiter=limit=0.95"
    if outro.get("a_fade_st") is not None:
        achain = "".join(labels) + (f"amix=inputs={len(labels)}:normalize=0:duration=longest,"
            f"apad=pad_dur={outro.get('freeze',0.7)+0.2},afade=t=out:st={outro['a_fade_st']}:d={outro.get('a_fade_d',1.0)},alimiter=limit=0.95")
    fc.append(achain + "[aout]")

    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for i in inputs: args += ["-i", i]
    args += ["-filter_complex", ";".join(fc), "-map", vlabel, "-map", "[aout]",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k"]
    if m.get("duration"): args += ["-t", str(m["duration"])]
    args += [out]
    subprocess.run(args, check=True)
    d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",out],
                       capture_output=True, text=True).stdout.strip()
    print(f"[assemble] HOTOVO → {os.path.abspath(out)} ({d}s)")

if __name__ == "__main__":
    main()
