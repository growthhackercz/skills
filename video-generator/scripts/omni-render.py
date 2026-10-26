#!/usr/bin/env python3
"""
omni-render.py — render scén podle video-brief.json přes Gemini Omni Flash (FAL).

ref2v scény: reference-to-video s character lockem (image_urls + <IMAGE_REF_n>).
img2v scény: image-to-video ze start_image (inserty, end-card, content-policy fallback).
Per-scene guard: pád jedné scény neshodí ostatní. Existující klipy se přeskakují.

Použití (z campaign složky):
    python3 omni-render.py --brief video-brief.json --list
    python3 omni-render.py --brief video-brief.json --only s1a --dry-run
    python3 omni-render.py --brief video-brief.json --only s1a          # proof (~$0.13/s)
    python3 omni-render.py --brief video-brief.json --all               # zbytek (skip existující)
    python3 omni-render.py --brief video-brief.json --all --force
Vyžaduje: FAL_KEY, fal_client. Výstup: _shots/<scene>.mp4
"""
from __future__ import annotations
import argparse, asyncio, json, os, sys, urllib.request
from pathlib import Path

EP_REF = "google/gemini-omni-flash/reference-to-video"
EP_IMG = "google/gemini-omni-flash/image-to-video"


def load_brief(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def scene_prompt(brief: dict, sc: dict) -> str:
    style = brief.get("style", "") if sc["mode"] == "ref2v" else ""
    return style + sc["prompt"] + brief.get("no_music_suffix", "")


async def render(fal_client, base: Path, brief: dict, sc: dict, char_urls: list[str]) -> Path | None:
    out_dir = base / "_shots"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{sc['id']}.mp4"
    args = {"prompt": scene_prompt(brief, sc),
            "aspect_ratio": brief.get("aspect_ratio", "9:16"),
            "duration": int(sc.get("duration", 5))}
    if sc["mode"] == "ref2v":
        args["image_urls"] = char_urls
        ep = EP_REF
    else:
        start = base / sc["start_image"]
        if not start.exists():
            print(f"❌ [{sc['id']}] chybí start_image: {start}"); return None
        print(f"→ [{sc['id']}] img2v — upload {start.name} …")
        args["image_url"] = await fal_client.upload_file_async(str(start))
        ep = EP_IMG
    print(f"→ [{sc['id']}] submit {ep} ({args['duration']}s) …")
    handler = await fal_client.submit_async(ep, arguments=args)
    result = await handler.get()
    url = (result.get("video") or {}).get("url") or result.get("video_url")
    if not url and isinstance(result.get("videos"), list) and result["videos"]:
        url = result["videos"][0].get("url")
    if not url:
        print(f"❌ [{sc['id']}] žádná video URL: {str(result)[:300]}"); return None
    urllib.request.urlretrieve(url, out)
    print(f"✅ [{sc['id']}] -> {out} ({out.stat().st_size//1024} KB)")
    return out


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--only")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    brief_path = Path(a.brief).resolve()
    base = brief_path.parent
    brief = load_brief(brief_path)
    scenes = brief["scenes"]
    total = sum(int(s.get("duration", 5)) for s in scenes)

    if a.list:
        for s in scenes:
            line = (s.get("line") or {}).get("text", "—")
            print(f"{s['id']} [{s['mode']}] {s.get('duration',5)}s: {line[:80]}")
        print(f"celkem {total}s ≈ ${total*0.13:.2f} (omni ~$0.13/s)")
        return

    keys = [a.only] if a.only else ([s["id"] for s in scenes] if a.all else [])
    if not keys:
        print("nic k práci — použij --only <id> nebo --all"); return
    todo = [s for s in scenes if s["id"] in keys]

    if a.dry_run:
        for s in todo:
            print(f"\n===== {s['id']} [{s['mode']}] ({s.get('duration',5)}s) =====")
            print(scene_prompt(brief, s))
        print(f"\n🟡 --dry-run — bez FAL útraty. Odhad: {sum(int(s.get('duration',5)) for s in todo)}s ≈ "
              f"${sum(int(s.get('duration',5)) for s in todo)*0.13:.2f}")
        return

    try:
        import fal_client
    except ImportError:
        print("❌ fal_client není nainstalovaný"); sys.exit(2)
    if not os.environ.get("FAL_KEY"):
        print("❌ FAL_KEY není nastavený"); sys.exit(2)

    if not a.force:
        skip = [s["id"] for s in todo if (base / "_shots" / f"{s['id']}.mp4").exists()]
        for k in skip:
            print(f"• [{k}] existuje, přeskočeno (--force pro re-render)")
        todo = [s for s in todo if s["id"] not in skip]
    if not todo:
        print("všechny scény existují."); return

    # character lock: upload jednou, sdílet mezi scénami
    char_urls: list[str] = []
    if any(s["mode"] == "ref2v" for s in todo):
        chars = brief.get("characters", [])
        paths = [base / c["ref_image"] for c in chars]
        missing = [str(p) for p in paths if not p.exists()]
        if missing:
            print(f"❌ chybí character reference: {missing}"); sys.exit(2)
        print(f"→ upload {len(paths)} character refs …")
        char_urls = list(await asyncio.gather(*[fal_client.upload_file_async(str(p)) for p in paths]))

    async def guarded(sc):
        try:
            return (sc["id"], await render(fal_client, base, brief, sc, char_urls))
        except Exception as e:
            print(f"❌ [{sc['id']}] SELHALO: {str(e)[:300]}")
            return (sc["id"], None)

    res = await asyncio.gather(*[guarded(s) for s in todo])
    ok = [k for k, p in res if p]; bad = [k for k, p in res if not p]
    print("HOTOVO:", ", ".join(ok) or "nic", "| SELHALO:", ", ".join(bad) or "nic")
    if bad:
        print("↪ content-policy? Viz references/omni-engine.md — dvojzáběr / img2v fallback.")


if __name__ == "__main__":
    asyncio.run(main())
