#!/usr/bin/env python3
"""
mux-final.py — finální zvukový mix: dialog + hudba s gradací → final.mp4

Vstupy:
  --video   vyrenderované video (HyperFrames render = silent; nebo concat s dialogem)
  --dialog  zdroj dialogové stopy (concat ořezaných klipů); vynech, pokud --video už dialog má
  --music   hudební podklad (WAV/MP3, HeyGen)
  --cta     čas (s), kdy začíná CTA/end-card — vrchol hudby (default: 80 % délky)

Hudba: intro tiché (0.09) → lineární build → vrchol (0.40) na CTA → fade-out 2.8 s.
Ducking: sidechaincompress pod dialogem. Výstup --out (default final.mp4).

Použití:
    python3 mux-final.py --video hf/renders/last.mp4 --dialog _base.mp4 --music music/track.wav --cta 16.4
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path


def dur(p: str) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "default=nk=1:nw=1", p]).decode().strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--dialog", help="video/audio s dialogovou stopou; default = --video")
    ap.add_argument("--music", required=True)
    ap.add_argument("--cta", type=float)
    ap.add_argument("--vmin", type=float, default=0.09)
    ap.add_argument("--vmid", type=float, default=0.38)
    ap.add_argument("--vpeak", type=float, default=0.40)
    ap.add_argument("--fadeout", type=float, default=2.8)
    ap.add_argument("--out", default="final.mp4")
    a = ap.parse_args()

    dialog = a.dialog or a.video
    T = dur(a.video)
    cta = a.cta if a.cta is not None else round(T * 0.8, 2)
    intro = 2.0
    span = max(0.5, cta - intro)
    fo = max(0.0, T - a.fadeout)
    vol = (f"if(lt(t,{intro}),{a.vmin},"
           f"if(lt(t,{cta:.2f}),{a.vmin}+(t-{intro})/{span:.2f}*({a.vmid}-{a.vmin}),{a.vpeak}))")

    filt = (
        f"[1:a]atrim=0:{T:.3f},asetpts=N/SR/TB,asplit=2[dlg1][dlg2];"
        f"[2:a]aloop=loop=-1:size=2e9,atrim=0:{T:.3f},asetpts=N/SR/TB,"
        f"volume='{vol}':eval=frame,afade=t=in:st=0:d=1.0,afade=t=out:st={fo:.2f}:d={a.fadeout}[mus];"
        f"[mus][dlg2]sidechaincompress=threshold=0.04:ratio=8:attack=5:release=280[mduck];"
        f"[dlg1][mduck]amix=inputs=2:duration=first:normalize=0[aout]"
    )
    cmd = ["ffmpeg", "-y", "-i", a.video, "-i", dialog, "-i", a.music,
           "-filter_complex", filt, "-map", "0:v", "-map", "[aout]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", a.out]
    print(f"→ mux: T={T:.2f}s CTA={cta:.2f}s fade-out={a.fadeout}s")
    subprocess.run(cmd, check=True)
    print(f"✅ {a.out} ({Path(a.out).stat().st_size//1024} KB)")


if __name__ == "__main__":
    sys.exit(main())
