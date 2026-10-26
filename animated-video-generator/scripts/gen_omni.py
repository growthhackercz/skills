#!/usr/bin/env python3
"""Omni (Google Gemini Omni Flash, FAL) — mluvící animované postavy s CZ lip-syncem.
Viz references/omni.md.

Subcommandy:
  render:     python3 gen_omni.py render --brief brief.json --list
              python3 gen_omni.py render --brief brief.json --only s1 --dry-run
              python3 gen_omni.py render --brief brief.json --only s1          # proof (~$0.13/s)
              python3 gen_omni.py render --brief brief.json --all [--force]
  transcribe: python3 gen_omni.py transcribe _shots/s1.mp4 --brief brief.json --scene s1
              # jeden stávající whisper call → raw transcript + dialogue QA report

brief.json: {"style":"<styl deskriptor>","aspect_ratio":"16:9","no_music_suffix":" No background music...",
  "characters":[{"id":"A","ref_image":"refA.png"}], "scenes":[
    {"id":"s1","mode":"ref2v","duration":8,"prompt":"...","line":{"text":"<verbatim CZ replika>"}},
    {"id":"s2","mode":"img2v","start_image":"screen.png","duration":5,"prompt":"..."}]}

ref2v: reference-to-video s character lockem (image_urls + <IMAGE_REF_n> v promptu).
img2v: image-to-video ze start_image (inserty/end-card/fallback). Per-scene guard.
VŽDY nejdřív --dry-run + STOP. Vyžaduje FAL_KEY.

⚠️ Spouštěj **systémovým python3** (fleet: 3.11, lokál mac: /usr/bin/python3 3.9 — oba mají fal_client 1.0.0
   i funkční pyexpat). NE homebrew python 3.14 (rozbitý pyexpat → fal_client neimportuje).
   `fal_client.subscribe` řeší frontu i stažení; ruční urllib response_url poll u těchto FAL video
   endpointů vrací 404 (pojmenovaná chyba — NEpoužívat, viz seedance.md).
"""
import argparse, json, os, sys, time, urllib.request
from pathlib import Path

EP_REF = "google/gemini-omni-flash/reference-to-video"
EP_IMG = "google/gemini-omni-flash/image-to-video"
EP_WHISPER = "fal-ai/whisper"
COST_PER_SEC = 0.13

def load_key():
    k = os.environ.get("FAL_KEY")
    if k: return k
    for p in [".claude/settings.local.json", os.path.expanduser("~/.claude/settings.local.json")]:
        try: k = json.load(open(p)).get("env", {}).get("FAL_KEY")
        except FileNotFoundError: k = None
        if k: return k
    sys.exit("FAL_KEY nenalezen")

def _fal():
    os.environ["FAL_KEY"] = load_key()  # fal_client čte FAL_KEY z env
    try:
        import fal_client
    except Exception as e:
        sys.exit(f"fal_client nejde importovat ({e}). Spusť systémovým python3 (NE homebrew 3.14).")
    return fal_client

def _dialogue_qa():
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
        from dialogue_qa import compare_dialogue, report_exit_code, sha256_file  # type: ignore
        return compare_dialogue, report_exit_code, sha256_file
    sys.exit("dialogue_qa.py nenalezen v cs-skills/_lib")

def upload_retry(fal_client, path, tries=4):
    """fal_client.upload_file s retry (transientní 'Invalid storage type' / 400 na upload/initiate)."""
    last = None
    for n in range(1, tries + 1):
        try:
            return fal_client.upload_file(str(path))
        except Exception as e:
            last = e; print(f"  upload retry {n}/{tries}: {str(e)[:120]}"); time.sleep(3 * n)
    raise RuntimeError(f"FAL upload selhal: {last}")

def scene_prompt(brief, sc):
    style = brief.get("style", "") if sc["mode"] == "ref2v" else ""
    return style + sc["prompt"] + brief.get("no_music_suffix", "")

def render_scene(fal_client, base, brief, sc, char_urls):
    out_dir = base / "_shots"; out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{sc['id']}.mp4"
    args = {"prompt": scene_prompt(brief, sc), "aspect_ratio": brief.get("aspect_ratio", "16:9"),
            "duration": int(sc.get("duration", 5))}
    if sc["mode"] == "ref2v":
        args["image_urls"] = char_urls; ep = EP_REF
    else:
        start = base / sc["start_image"]
        if not start.exists(): print(f"❌ [{sc['id']}] chybí start_image: {start}"); return None
        print(f"→ [{sc['id']}] img2v — upload {start.name} …")
        args["image_url"] = upload_retry(fal_client, start); ep = EP_IMG
    print(f"→ [{sc['id']}] subscribe {ep} ({args['duration']}s) …")
    r = fal_client.subscribe(ep, arguments=args)
    vid = r.get("video")
    url = vid.get("url") if isinstance(vid, dict) else (vid or r.get("video_url"))
    if not url and isinstance(r.get("videos"), list) and r["videos"]: url = r["videos"][0].get("url")
    if not url: print(f"❌ [{sc['id']}] žádná video URL: {str(r)[:250]}"); return None
    urllib.request.urlretrieve(url, out)
    print(f"✅ [{sc['id']}] → {out} ({out.stat().st_size//1024} KB)"); return out

def cmd_render(a):
    brief_path = Path(a.brief).resolve(); base = brief_path.parent
    brief = json.load(open(brief_path, encoding="utf-8")); scenes = brief["scenes"]
    total = sum(int(s.get("duration", 5)) for s in scenes)
    if a.list:
        for s in scenes:
            line = (s.get("line") or {}).get("text", "—")
            print(f"{s['id']} [{s['mode']}] {s.get('duration',5)}s: {line[:80]}")
        print(f"celkem {total}s ≈ ${total*COST_PER_SEC:.2f} (omni ~${COST_PER_SEC}/s)"); return
    keys = [a.only] if a.only else ([s["id"] for s in scenes] if a.all else [])
    if not keys: print("nic k práci — --only <id> nebo --all"); return
    todo = [s for s in scenes if s["id"] in keys]
    if a.dry_run:
        for s in todo:
            print(f"\n===== {s['id']} [{s['mode']}] ({s.get('duration',5)}s) =====\n{scene_prompt(brief, s)}")
        d = sum(int(s.get('duration',5)) for s in todo)
        print(f"\n🟡 --dry-run — bez FAL útraty. Odhad: {d}s ≈ ${d*COST_PER_SEC:.2f}"); return
    fal_client = _fal()
    if not a.force:
        keep = []
        for s in todo:
            if (base/"_shots"/f"{s['id']}.mp4").exists():
                print(f"• [{s['id']}] existuje, skip (--force pro re-render)")
            else:
                keep.append(s)
        todo = keep
    if not todo: print("všechny scény existují."); return
    char_urls = []
    if any(s["mode"] == "ref2v" for s in todo):
        paths = [base / c["ref_image"] for c in brief.get("characters", [])]
        missing = [str(p) for p in paths if not p.exists()]
        if missing: sys.exit(f"❌ chybí character reference: {missing}")
        print(f"→ upload {len(paths)} character portrétů …")
        char_urls = [upload_retry(fal_client, p) for p in paths]
    ok, bad = [], []
    for s in todo:  # sekvenčně + guard (pád scény neshodí ostatní)
        try:
            r = render_scene(fal_client, base, brief, s, char_urls); (ok if r else bad).append(s["id"])
        except Exception as e:
            print(f"❌ [{s['id']}] SELHALO: {str(e)[:250]}"); bad.append(s["id"])
    print("HOTOVO:", ", ".join(ok) or "nic", "| SELHALO:", ", ".join(bad) or "nic")
    if bad: print("↪ viz references/omni.md — u animace zkontroluj prompt (styl/replika), u UI insertů img2v.")

def cmd_transcribe(a):
    fal_client = _fal()
    clip = Path(a.clip).resolve()
    print(f"→ upload {clip} …"); url = upload_retry(fal_client, clip)
    print("→ whisper (chunk_level=word) …")
    r = fal_client.subscribe(EP_WHISPER, arguments={"audio_url": url, "chunk_level": "word", "language": "cs"})
    print("\n=== PŘEPIS ===\n" + (r.get("text") or "—"))
    chunks = r.get("chunks") or r.get("words") or []
    if chunks:
        print("\n=== WORD TIMESTAMPY (pro cut-fix / titulky) ===")
        for c in chunks[:200]:
            ts = c.get("timestamp") or [c.get("start"), c.get("end")]
            print(f"  {ts}  {c.get('text','')}")
    qa_dir = clip.parent.parent / "_qa" if clip.parent.name == "_shots" else clip.parent / "_qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    raw_path = Path(a.raw_out).resolve() if a.raw_out else qa_dir / f"{clip.stem}-whisper.json"
    raw_path.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"→ raw transcript: {raw_path}")

    if not a.brief and not a.scene:
        return 0
    if not a.brief or not a.scene:
        print("❌ Pro dialogue QA zadej současně --brief a --scene")
        return 2
    brief_path = Path(a.brief).resolve()
    brief = json.load(open(brief_path, encoding="utf-8"))
    scene = next((item for item in brief.get("scenes", []) if item.get("id") == a.scene), None)
    if not scene:
        print(f"❌ Scéna {a.scene} není v briefu {brief_path}")
        return 2
    line = scene.get("line") or {}
    qa_config = brief.get("dialogueQa") or {}
    aliases = dict(qa_config.get("aliases") or {})
    aliases.update(line.get("qaAliases") or {})
    compare_dialogue, report_exit_code, sha256_file = _dialogue_qa()
    report = compare_dialogue(line.get("text") or "", chunks, scene_id=a.scene, aliases=aliases)
    report.update({
        "briefPath": str(brief_path),
        "briefSha256": sha256_file(brief_path),
        "mediaPath": str(clip),
        "mediaSha256": sha256_file(clip),
    })
    report_path = Path(a.report).resolve() if a.report else qa_dir / f"{a.scene}-dialogue-qa.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"→ dialogue QA: {report.get('status')} ({report_path})")
    return report_exit_code(report)

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render"); r.add_argument("--brief", required=True)
    r.add_argument("--only"); r.add_argument("--all", action="store_true")
    r.add_argument("--list", action="store_true"); r.add_argument("--force", action="store_true")
    r.add_argument("--dry-run", action="store_true")
    t = sub.add_parser("transcribe"); t.add_argument("clip")
    t.add_argument("--brief"); t.add_argument("--scene")
    t.add_argument("--raw-out"); t.add_argument("--report")
    a = ap.parse_args()
    return (cmd_render if a.cmd == "render" else cmd_transcribe)(a) or 0

if __name__ == "__main__":
    raise SystemExit(main())
