#!/usr/bin/env python3
"""
trim-clips.py — ořez mrtvých pauz (hluché přikyvování) z omni scén podle briefu.

Auto: silencedetect → ořez [lead .. konec řeči + pad]. Scéna s "trim": {lead, out}
v briefu použije fixní okno (obrazovkové inserty, které mají "dýchat" celé).
Zapisuje _shots_trim/<id>.mp4 + vypíše řečová okna (podklad pro titulky).

Použití: python3 trim-clips.py --brief video-brief.json [--pad 0.4] [--lead-max 0.6]
"""
from __future__ import annotations
import argparse, json, re, subprocess
from pathlib import Path


def probe_dur(p: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "default=nk=1:nw=1", str(p)]).decode().strip())


def silences(p: Path):
    out = subprocess.run(["ffmpeg", "-i", str(p), "-af", "silencedetect=noise=-30dB:d=0.3", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return [(m.group(1), float(m.group(2))) for m in re.finditer(r"silence_(start|end): ([\d.]+)", out)]


def plan(p: Path, pad: float, lead_max: float):
    dur = probe_dur(p)
    ev = silences(p)
    out_t, lead = dur, 0.0
    if ev:
        last_typ, last_t = ev[-1]
        starts = [t for ty, t in ev if ty == "start"]
        if last_typ == "start":
            out_t = min(dur, last_t + pad)          # ticho běží do konce → mrtvý ocas
        elif last_typ == "end" and (dur - last_t) < 0.12 and starts:
            out_t = min(dur, starts[-1] + pad)
        if ev[0][0] == "start" and ev[0][1] < 0.2:  # hluchá hlava
            fe = next((t for ty, t in ev if ty == "end"), 0.0)
            if fe > lead_max and fe < out_t - 0.8:
                lead = max(0.0, fe - 0.15)
    if out_t - lead < 1.8:                           # podlaha proti mikro-střihům
        out_t = min(dur, lead + 1.8)
    return lead, out_t, dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--pad", type=float, default=0.4)
    ap.add_argument("--lead-max", type=float, default=0.6)
    a = ap.parse_args()

    brief_path = Path(a.brief).resolve()
    base = brief_path.parent
    brief = json.load(open(brief_path, encoding="utf-8"))
    src_d, dst_d = base / "_shots", base / "_shots_trim"
    dst_d.mkdir(parents=True, exist_ok=True)

    total, timeline = 0.0, 0.0
    print("scéna | ořez | řečové okno v cílovém videu (pro titulky)")
    for sc in brief["scenes"]:
        k = sc["id"]
        src = src_d / f"{k}.mp4"
        if not src.exists():
            print(f"❌ chybí {src}"); continue
        fixed = sc.get("trim")
        if fixed and fixed.get("lead") is not None:
            lead, out_t = float(fixed["lead"]), float(fixed["out"]); dur = probe_dur(src)
            out_t = min(out_t, dur)
        else:
            lead, out_t, dur = plan(src, a.pad, a.lead_max)
        length = out_t - lead
        dst = dst_d / f"{k}.mp4"
        subprocess.run(["ffmpeg", "-y", "-ss", f"{lead:.3f}", "-to", f"{out_t:.3f}", "-i", str(src),
                        "-vf", "fps=24", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                        "-pix_fmt", "yuv420p",
                        "-af", "afade=t=in:st=0:d=0.06,afade=t=out:st=%.2f:d=0.10" % max(0.0, length - 0.10),
                        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(dst)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{k}: {dur:.2f}s -> [{lead:.2f}..{out_t:.2f}] = {length:.2f}s | start ve videu: {timeline:.2f}s")
        timeline += length
        total += length
    print(f"CELKEM po ořezu = {total:.2f}s  (klipy v {dst_d})")


if __name__ == "__main__":
    main()
