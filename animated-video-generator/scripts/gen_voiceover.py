#!/usr/bin/env python3
"""Český voiceover po beatech (Gemini TTS na FAL). Každý beat = věta + mikro-nálada.
Generuje, retry na glitch, ořízne ticho, sjednotí hlasitost (loudnorm). Stdlib-only.

Použití:
  python3 gen_voiceover.py --beats beats.json --out-dir assets/audio/beats [--voice Enceladus]

beats.json: [{"id":"o1","text":"Léto se blíží...","style":"breezy, light, a little teasing"}, ...]
Výstup: <out-dir>/<id>.mp3 (oříznuté ticho + loudnorm I=-15). Tyto pak posadíš na časy v assemble.
"""
import argparse, json, os, sys, subprocess, time, urllib.request

ENDPOINT = "fal-ai/gemini-3.1-flash-tts"
BASE_STYLE = ("Deep, rich, warm, VERY PLAYFUL and characterful Czech male voice — like a charismatic "
              "friend telling a fun story, never an announcer. Expressive, smiling, natural Czech accent. ")

def load_key():
    k = os.environ.get("FAL_KEY")
    if k: return k
    for p in [".claude/settings.local.json", os.path.expanduser("~/.claude/settings.local.json")]:
        try: k = json.load(open(p)).get("env", {}).get("FAL_KEY")
        except FileNotFoundError: k = None
        if k: return k
    sys.exit("FAL_KEY nenalezen")

def dur(f):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],
                                capture_output=True, text=True).stdout.strip() or 0)

def gen(text, style, voice, key):
    H = {"Authorization": "Key " + key, "Content-Type": "application/json"}
    args = {"prompt": text, "voice": voice, "language_code": "Czech (Czech Republic)",
            "style_instructions": BASE_STYLE + "Tone for THIS line: " + style + "."}
    sub = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://queue.fal.run/" + ENDPOINT, data=json.dumps(args).encode(), headers=H), timeout=120))
    surl, rurl = sub["status_url"], sub["response_url"]
    for _ in range(45):
        time.sleep(3)
        s = json.load(urllib.request.urlopen(urllib.request.Request(surl, headers={"Authorization":"Key "+key}), timeout=30))
        if s.get("status") == "COMPLETED": break
    r = json.load(urllib.request.urlopen(urllib.request.Request(rurl, headers={"Authorization":"Key "+key}), timeout=120))
    a = r.get("audio")
    return a.get("url") if isinstance(a, dict) else a

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beats", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--voice", default="Enceladus")
    ap.add_argument("--min-dur", type=float, default=0.6, help="kratší = glitch → retry")
    a = ap.parse_args()
    beats = json.load(open(a.beats)); os.makedirs(a.out_dir, exist_ok=True)
    key = load_key(); trim = ("silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.04,"
        "areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.04,areverse,"
        "loudnorm=I=-15:TP=-1.5:LRA=11")
    for b in beats:
        raw = os.path.join(a.out_dir, f"_{b['id']}_raw.mp3"); out = os.path.join(a.out_dir, f"{b['id']}.mp3")
        for at in range(5):
            try: url = gen(b["text"], b.get("style","natural, warm"), a.voice, key)
            except Exception as e: print(f"  {b['id']} retry {at+1}: {e}"); time.sleep(3); continue
            urllib.request.urlretrieve(url, raw)
            if dur(raw) > a.min_dur: break
            print(f"  {b['id']} attempt {at+1}: {dur(raw):.1f}s (glitch, retry)")
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",raw,"-af",trim,out], check=True)
        print(f"{b['id']}: {dur(out):.2f}s  ({b['text'][:42]}…)")
    print(f"[vo] hotovo → {os.path.abspath(a.out_dir)} (posaď beaty na časy v assemble)")

if __name__ == "__main__":
    main()
