#!/usr/bin/env python3
"""Spojí PNG/JPG slidy do jednoho PDF pro LinkedIn document/carousel post.

Používá jen Pillow (na fleet VPS dostupné, img2pdf/reportlab ne). Validovaný wrapper —
žádný přímý shell, žádné HTTP. Slidy musí být předané v pořadí (slide-01, slide-02, …).

Použití:
    python3 slides_to_pdf.py <out.pdf> <slide-01.png> <slide-02.png> [...]

LinkedIn document: max 300 stran / 100 MB (GHL). My držíme 5–10 slidů (carousel sweet spot).
"""
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("CHYBA: Pillow není dostupné (import PIL selhal).")


def slides_to_pdf(slide_paths, out_pdf):
    if not slide_paths:
        sys.exit("CHYBA: žádné slidy k sestavení.")
    imgs = []
    for p in slide_paths:
        if not os.path.isfile(p):
            sys.exit(f"CHYBA: slide neexistuje: {p}")
        # PDF nepodporuje alfa kanál → převod na RGB (bílé pozadí pod průhledností)
        im = Image.open(p)
        if im.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            im = im.convert("RGBA")
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        imgs.append(im)
    imgs[0].save(out_pdf, "PDF", save_all=True, append_images=imgs[1:], resolution=150.0)
    return out_pdf


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Použití: slides_to_pdf.py <out.pdf> <slide-01.png> [slide-02.png ...]")
    out = sys.argv[1]
    slides = sys.argv[2:]
    path = slides_to_pdf(slides, out)
    size = os.path.getsize(path)
    print(f"PDF hotové: {path} ({len(slides)} stran, {size} B)")
    if size > 100 * 1024 * 1024:
        print("VAROVÁNÍ: PDF přes 100 MB — LinkedIn limit. Zmenši slidy (nižší kvalita/JPEG).")
