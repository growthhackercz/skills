#!/bin/bash
# Lokální render přes oficiální HyperFrames CLI + gates + POVINNÉ proof framy.
# ŽÁDNÝ cloud render (fleet renderuje lokálně v openclaw kontejneru).
# Použití: bash render.sh --project <dir> [--draft|--final] [--output final.mp4] [--fps 30] [--skip-gates]
set -uo pipefail

HF="npx --yes hyperframes@0.6.97"
PROJECT="" MODE="draft" OUTPUT="" FPS="" SKIP_GATES=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2;;
    --draft) MODE="draft"; shift;;
    --final) MODE="final"; shift;;
    --output) OUTPUT="$2"; shift 2;;
    --fps) FPS="$2"; shift 2;;
    --skip-gates) SKIP_GATES=1; shift;;
    *) echo "neznámý argument: $1"; exit 2;;
  esac
done
[[ -z "$PROJECT" ]] && { echo "Použití: render.sh --project <dir> [--draft|--final]"; exit 2; }
SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # resolve PŘED cd do projektu
cd "$PROJECT" || exit 2
[[ -z "$OUTPUT" ]] && OUTPUT="${MODE}.mp4"

echo "== ENV =="
# fleet: system chromium (openclaw kontejner). hyperframes si pod 8GB sám pinuje 1 worker.
if [[ -x /usr/bin/chromium ]]; then
  export PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
  echo "fleet profil: chromium=/usr/bin/chromium"
else
  echo "dev profil (Mac)"
fi

echo "== PREFLIGHT =="
# vendored JS, ne CDN (fleet je offline pro render)
if grep -rn "cdn.jsdelivr.net\|unpkg.com\|cdnjs" index.html compositions/ 2>/dev/null | grep -vi binary; then
  echo "⚠ CDN reference nalezeny — pro fleet vendoruj do assets/vendor/ (dev OK)"
fi

if [[ $SKIP_GATES -eq 0 ]]; then
  echo "== GATES (lint + validate) =="
  $HF lint 2>&1 | grep -vE "deprecated|npm warn" | tail -3 || { echo "lint ERROR"; exit 4; }
  $HF validate 2>&1 | grep -vE "deprecated|npm warn" | tail -3 || true
fi

echo "== RENDER ($MODE) =="
RFLAGS="--output $OUTPUT"
[[ -n "$FPS" ]] && RFLAGS="$RFLAGS --fps $FPS"
[[ "$MODE" == "draft" ]] && RFLAGS="$RFLAGS --quality draft"
$HF render $RFLAGS 2>&1 | grep -vE "deprecated|npm warn|^\[2K" | grep -iE "ERROR|◇|completed|is not defined" | tail -5 || { echo "RENDER ERROR"; exit 5; }

echo "== PROOF FRAMY (povinné — kontroluj VŠECHNY) =="
mkdir -p qa
# rovnoměrné vzorky + 0.3s po startu každé scény (z data-start v index.html)
TIMES=$(python3 - "$OUTPUT" <<'PY'
import sys, re, subprocess
out = sys.argv[1]
dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",out],
                           capture_output=True,text=True).stdout.strip() or 5)
ts = {round(dur*(i+0.5)/8,2) for i in range(8)}
try:
    for m in re.finditer(r'data-composition-src[^>]*data-start="([\d.]+)"|data-start="([\d.]+)"[^>]*data-composition-src', open("index.html").read()):
        t = float(m.group(1) or m.group(2)) + 0.3
        if t < dur: ts.add(round(t,2))
except FileNotFoundError: pass
print(" ".join("proof%02d=%s" % (i, t) for i, t in enumerate(sorted(ts))))
PY
)
# Sařin extract_proof_frames.py: --time label=čas
ARGS=""; for kv in $TIMES; do ARGS="$ARGS --time $kv"; done
python3 "$SCRIPTS/extract_proof_frames.py" "$OUTPUT" $ARGS -o qa/proof --contact-sheet qa/proof/sheet.jpg 2>&1 | tail -3

echo ""
echo "HOTOVO: $PROJECT/$OUTPUT"
echo "⚠️  POVINNÉ: zkontroluj qa/proof/*.png VIZUÁLNĚ (Read) — gates nechytí neviditelný text/flash/mrtvou scénu."
echo "⚠️  Při změně prvku: prohledej i DALŠÍ scénu na carryover kopii (viz references/continuity-and-qa.md)."
