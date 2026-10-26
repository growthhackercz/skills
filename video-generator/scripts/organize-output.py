#!/usr/bin/env python3
"""
organize-output.py — verzování finálu + struktura výstupní složky videa.
Práce běží uvnitř assets/ (cwd), sem se jen PROMOTE hotový render do rootu jako final-vN.

Konvence:
  <kampaň>/
    final-v1.mp4  final-v2.mp4 …   ← JEN verzované finály v rootu (poslední = nejvyšší číslo)
    assets/                          ← všechno ostatní (galerie ignoruje kvůli „_" prefixu)
      video-brief.json, _base.mp4, _trim.txt, _shots/, _shots_trim/, hf/,
      screens/, refs/, images/, music/, sfx/, logs/ …
      proof/                       ← kontrolní PNG strily

Použití:
  organize-output.py <dir>                  # migrace starých složek: legacy final.mp4 → final-v1.mp4, zbytek do assets/
  organize-output.py <dir> --promote <mp4>  # <mp4> → root jako DALŠÍ final-vN.mp4 (běžné použití)

Idempotentní: opakované spuštění nic nerozbije (root už má jen final-vN + assets).
Skripty pak pouštěj s cwd=<dir>/_work (relativní cesty v briefu drží).
"""
from __future__ import annotations
import argparse, re, shutil, sys
from pathlib import Path

FINAL_RE = re.compile(r"final-v(\d+)\.mp4$")


def next_version(root: Path) -> int:
    ns = [int(m.group(1)) for p in root.iterdir()
          if (m := FINAL_RE.match(p.name))]
    return (max(ns) + 1) if ns else 1


def move_into(src: Path, dstdir: Path):
    """Přesun src do dstdir; když cíl existuje jako složka, slij obsah."""
    target = dstdir / src.name
    if target.exists():
        if src.is_dir() and target.is_dir():
            for sub in list(src.iterdir()):
                move_into(sub, target)
            if not any(src.iterdir()):
                src.rmdir()
            return
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    shutil.move(str(src), str(target))


def organize(root, promote):
    root = root.resolve()
    work = root / "assets"; work.mkdir(exist_ok=True)
    proof = work / "proof"; proof.mkdir(exist_ok=True)

    # 1) legacy final.mp4 → final-vN (jen když ještě žádné final-v* není)
    legacy = root / "final.mp4"
    if legacy.exists() and not any(FINAL_RE.match(p.name) for p in root.iterdir()):
        v = next_version(root)
        legacy.rename(root / f"final-v{v}.mp4")
        print(f"legacy final.mp4 → final-v{v}.mp4")

    # 2) promote vyrenderovaný mp4 → další final-vN
    if promote:
        promote = Path(promote).resolve()
        if not promote.exists():
            print(f"❌ promote soubor neexistuje: {promote}"); sys.exit(2)
        v = next_version(root)
        dst = root / f"final-v{v}.mp4"
        shutil.move(str(promote), str(dst))
        print(f"→ {dst.name}")

    # 3) vše z rootu kromě final-vN a _work → do _work
    for item in list(root.iterdir()):
        if item.name == "assets" or FINAL_RE.match(item.name):
            continue
        move_into(item, work)

    # 4) kontrolní obrázky (top-level v _work) → assets/_proof
    for pat in ("*.png", "*.jpg", "*.jpeg"):
        for img in list(work.glob(pat)):
            move_into(img, proof)

    finals = sorted(p.name for p in root.iterdir() if FINAL_RE.match(p.name))
    print(f"✅ {root.name}: root = {finals + ['assets/']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--promote", default=None, help="vyrenderovaný mp4 → další final-vN.mp4")
    a = ap.parse_args()
    organize(Path(a.dir), (a.promote if a.promote else None))


if __name__ == "__main__":
    main()
