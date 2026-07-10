#!/usr/bin/env python3
"""
build-review.py

Vytvoří HTML review grid se všemi vygenerovanými stránkami pro batch schválení.
Uživatel vidí všechny stránky najednou v gridu, klikem na stránku zvětší detail,
a může označit stránky k regeneraci.

Usage:
    python3 build-review.py \\
        --pages-dir /documents/lead-magnets/<slug>/_pages/ \\
        --output /documents/lead-magnets/<slug>/_review.html \\
        [--plan /documents/lead-magnets/<slug>/page-plan.json]
"""

import argparse
import json
import re
from pathlib import Path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <title>Lead Magnet — Review</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
      background: #f5f5f7;
      padding: 32px;
      color: #1c1c1e;
    }}
    h1 {{ font-size: 28px; margin-bottom: 8px; }}
    .meta {{ color: #6e6e73; margin-bottom: 32px; font-size: 14px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 24px;
    }}
    .page {{
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      transition: transform 0.15s, box-shadow 0.15s;
      cursor: pointer;
    }}
    .page:hover {{
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }}
    .page-img {{
      width: 100%;
      aspect-ratio: 1240/1754;
      object-fit: cover;
      background: #ebebf0;
    }}
    .page-meta {{
      padding: 12px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
    }}
    .page-num {{ font-weight: 600; }}
    .page-type {{ color: #6e6e73; }}
    .page-actions {{
      padding: 0 16px 12px;
      display: flex;
      gap: 8px;
    }}
    .btn {{
      padding: 6px 12px;
      border-radius: 6px;
      border: none;
      font-size: 12px;
      cursor: pointer;
      font-weight: 500;
    }}
    .btn-approve {{ background: #34c759; color: white; }}
    .btn-regen {{ background: #ff3b30; color: white; }}
    .btn-approved {{ background: #d1f4d4; color: #1d6e2e; }}
    .btn-flagged {{ background: #ffe5e3; color: #b3251a; }}
    .summary {{
      position: sticky;
      bottom: 16px;
      background: white;
      padding: 16px 20px;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      margin-top: 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 14px;
    }}
    .regen-list {{
      font-family: monospace;
      background: #f5f5f7;
      padding: 8px 12px;
      border-radius: 6px;
      color: #1c1c1e;
    }}

    /* Modal */
    .modal {{
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.85);
      z-index: 100;
      cursor: pointer;
    }}
    .modal.open {{ display: flex; align-items: center; justify-content: center; }}
    .modal img {{
      max-width: 90vw;
      max-height: 90vh;
      object-fit: contain;
    }}
  </style>
</head>
<body>
  <h1>{slug} — Review</h1>
  <p class="meta">{n_pages} stránek • {resolution} • klikni na stránku pro zvětšení • označ stránky k regeneraci</p>

  <div class="grid">
    {grid_html}
  </div>

  <div class="summary">
    <div>
      <strong id="approved-count">0</strong> schváleno •
      <strong id="flagged-count">0</strong> k regeneraci
    </div>
    <div>
      <span>Pages to regenerate:</span>
      <span class="regen-list" id="regen-list">—</span>
      <button class="btn btn-approve" onclick="copyRegenList()">📋 Copy list</button>
    </div>
  </div>

  <div class="modal" id="modal" onclick="closeModal()">
    <img id="modal-img" />
  </div>

  <script>
    const state = {{}};

    function toggleApprove(n) {{
      state[n] = state[n] === 'approved' ? null : 'approved';
      updateUI(n);
      updateSummary();
    }}

    function toggleRegen(n) {{
      state[n] = state[n] === 'flagged' ? null : 'flagged';
      updateUI(n);
      updateSummary();
    }}

    function updateUI(n) {{
      const btnA = document.getElementById(`btn-a-${{n}}`);
      const btnR = document.getElementById(`btn-r-${{n}}`);
      btnA.className = 'btn ' + (state[n] === 'approved' ? 'btn-approved' : 'btn-approve');
      btnR.className = 'btn ' + (state[n] === 'flagged' ? 'btn-flagged' : 'btn-regen');
      btnA.textContent = state[n] === 'approved' ? '✓ OK' : 'OK';
      btnR.textContent = state[n] === 'flagged' ? '✗ Regen' : 'Regen';
    }}

    function updateSummary() {{
      const approved = Object.values(state).filter(s => s === 'approved').length;
      const flagged = Object.entries(state).filter(([_, s]) => s === 'flagged').map(([n]) => n).sort((a,b)=>+a-+b);
      document.getElementById('approved-count').textContent = approved;
      document.getElementById('flagged-count').textContent = flagged.length;
      document.getElementById('regen-list').textContent = flagged.length ? flagged.join(',') : '—';
    }}

    function copyRegenList() {{
      const txt = document.getElementById('regen-list').textContent;
      if (txt === '—') return;
      navigator.clipboard.writeText(txt);
      alert('Copied: ' + txt);
    }}

    function openModal(src) {{
      document.getElementById('modal-img').src = src;
      document.getElementById('modal').classList.add('open');
    }}
    function closeModal() {{
      document.getElementById('modal').classList.remove('open');
    }}
  </script>
</body>
</html>
"""


def get_page_type(plan_pages: list, page_n: int) -> str:
    for p in plan_pages:
        if p.get("n") == page_n:
            return p.get("type", "—")
    return "—"


def main():
    parser = argparse.ArgumentParser(description="Build review HTML grid for lead magnet pages")
    parser.add_argument("--pages-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--plan", help="Optional page-plan.json for type labels")
    args = parser.parse_args()

    pages_dir = Path(args.pages_dir)
    output_path = Path(args.output)

    plan_pages = []
    if args.plan and Path(args.plan).exists():
        plan_pages = json.loads(Path(args.plan).read_text(encoding="utf-8")).get("pages", [])

    images = sorted(pages_dir.glob("page-*.png"))
    if not images:
        print(f"❌ No page-*.png files in {pages_dir}")
        return 1

    grid_items = []
    for img in images:
        m = re.match(r"page-(\d+)\.png", img.name)
        if not m:
            continue
        page_n = int(m.group(1))
        page_type = get_page_type(plan_pages, page_n)
        rel_path = img.relative_to(output_path.parent) if img.is_absolute() else img
        grid_items.append(f"""
        <div class="page">
          <img class="page-img" src="{rel_path}" onclick="openModal('{rel_path}')" />
          <div class="page-meta">
            <span class="page-num">Page {page_n:02d}</span>
            <span class="page-type">{page_type}</span>
          </div>
          <div class="page-actions">
            <button class="btn btn-approve" id="btn-a-{page_n}" onclick="toggleApprove({page_n})">OK</button>
            <button class="btn btn-regen" id="btn-r-{page_n}" onclick="toggleRegen({page_n})">Regen</button>
          </div>
        </div>
        """)

    # Detect resolution from first image
    resolution = "—"
    try:
        from PIL import Image
        with Image.open(images[0]) as im:
            resolution = f"{im.width}×{im.height}"
    except Exception:
        pass

    html = HTML_TEMPLATE.format(
        slug=output_path.parent.name,
        n_pages=len(images),
        resolution=resolution,
        grid_html="\n".join(grid_items),
    )

    output_path.write_text(html, encoding="utf-8")
    print(f"✅ Review grid → {output_path}")
    print(f"   Open in browser: file://{output_path.resolve()}")


if __name__ == "__main__":
    main()
