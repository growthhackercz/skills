#!/usr/bin/env python3
"""
render-pdf.py

Vyrenderuje produkční PDF lead magnetu z markdown obsahu.
Načte DESIGN.md, namapuje tokeny na CSS proměnné, sestaví HTML šablonu
a vyrenderuje PDF přes Playwright/Chromium.

Usage:
    python3 render-pdf.py \\
        --markdown /documents/lead-magnets/<slug>/03-content.md \\
        --design /documents/brand/DESIGN.md \\
        --output /documents/lead-magnets/<slug>/lead-magnet.pdf \\
        [--cover /documents/lead-magnets/<slug>/cover.png] \\
        [--author "Jméno Autora"] \\
        [--title "Vlastní název"]

Dependencies:
    pip install playwright markdown pyyaml
    playwright install chromium
"""

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import markdown as md
    import yaml
    from playwright.async_api import async_playwright
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install playwright markdown pyyaml && playwright install chromium")
    sys.exit(1)


# ── Default tokens (fallback when DESIGN.md is missing or incomplete) ──
DEFAULT_TOKENS = {
    "color-primary": "#08090a",
    "color-secondary": "#f7f8f8",
    "color-accent": "#5e6ad2",
    "color-text": "#08090a",
    "color-text-muted": "#6b7280",
    "color-bg": "#ffffff",
    "color-bg-subtle": "#f7f8f8",
    "color-success": "#10b981",
    "color-warning": "#f59e0b",
    "color-error": "#ef4444",
    "color-border": "#e5e7eb",

    "font-display": '"Inter", -apple-system, system-ui, sans-serif',
    "font-body": '"Inter", -apple-system, system-ui, sans-serif',
    "font-mono": '"JetBrains Mono", monospace',

    "fs-display": "48pt",
    "fs-h1": "28pt",
    "fs-h2": "20pt",
    "fs-h3": "14pt",
    "fs-body": "11pt",
    "fs-small": "9pt",

    "lh-tight": "1.1",
    "lh-normal": "1.5",
    "lh-loose": "1.7",

    "ls-display": "-0.022em",
    "ls-body": "0",

    "fw-normal": "400",
    "fw-medium": "500",
    "fw-semibold": "600",
    "fw-bold": "700",

    "space-1": "4pt",
    "space-2": "8pt",
    "space-3": "12pt",
    "space-4": "16pt",
    "space-5": "20pt",
    "space-6": "24pt",
    "space-8": "32pt",
    "space-12": "48pt",
    "space-16": "64pt",

    "radius-sm": "4pt",
    "radius-md": "8pt",
    "radius-lg": "16pt",
    "radius-full": "9999pt",
}


def px_to_pt(value):
    """Convert '16px' → '12pt' (1px = 0.75pt). Pass-through for non-px."""
    if isinstance(value, (int, float)):
        return f"{value * 0.75}pt"
    if not isinstance(value, str):
        return str(value)
    m = re.match(r"^([\d.]+)px$", value.strip())
    if m:
        pts = float(m.group(1)) * 0.75
        return f"{pts}pt"
    return value


def parse_design_md(design_path: Path) -> dict:
    """Extract YAML frontmatter from DESIGN.md and map to CSS tokens."""
    if not design_path.exists():
        print(f"⚠️  DESIGN.md not found at {design_path} — using defaults")
        return dict(DEFAULT_TOKENS)

    content = design_path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        print("⚠️  DESIGN.md has no YAML frontmatter — using defaults")
        return dict(DEFAULT_TOKENS)

    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        print(f"⚠️  DESIGN.md YAML parse error: {e} — using defaults")
        return dict(DEFAULT_TOKENS)

    tokens = dict(DEFAULT_TOKENS)

    # Colors
    colors = data.get("colors", {}) or {}
    color_aliases = {
        "primary": "color-primary",
        "secondary": "color-secondary",
        "tertiary": "color-accent",
        "accent": "color-accent",
        "text": "color-text",
        "text-muted": "color-text-muted",
        "bg": "color-bg",
        "background": "color-bg",
        "bg-subtle": "color-bg-subtle",
        "success": "color-success",
        "warning": "color-warning",
        "error": "color-error",
        "border": "color-border",
    }
    for src, dst in color_aliases.items():
        if src in colors and colors[src]:
            tokens[dst] = str(colors[src]).lower()

    # Typography
    typo = data.get("typography", {}) or {}
    typo_map = {
        "display-xl": ("fs-display", "lh-tight", "ls-display", "fw-bold", "font-display"),
        "heading-1": ("fs-h1", None, None, "fw-semibold", None),
        "heading-2": ("fs-h2", None, None, "fw-semibold", None),
        "heading-3": ("fs-h3", None, None, "fw-medium", None),
        "body-md": ("fs-body", "lh-normal", "ls-body", "fw-normal", "font-body"),
        "body-sm": ("fs-small", None, None, None, None),
    }
    for src, (fs, lh, ls, fw, ff) in typo_map.items():
        spec = typo.get(src) or {}
        if "fontSize" in spec and fs:
            tokens[fs] = px_to_pt(spec["fontSize"])
        if "lineHeight" in spec and lh:
            tokens[lh] = str(spec["lineHeight"])
        if "letterSpacing" in spec and ls:
            tokens[ls] = str(spec["letterSpacing"])
        if "fontWeight" in spec and fw:
            tokens[fw] = str(spec["fontWeight"])
        if "fontFamily" in spec and ff:
            family = str(spec["fontFamily"]).strip()
            if family and not family.startswith('"'):
                family = f'"{family}"'
            tokens[ff] = f'{family}, -apple-system, system-ui, sans-serif'

    # Spacing
    spacing = data.get("spacing", {}) or {}
    for k, v in spacing.items():
        key = f"space-{k}"
        if v is not None:
            tokens[key] = px_to_pt(v) if isinstance(v, str) else f"{int(v) * 4}pt"

    # Rounded
    rounded = data.get("rounded", {}) or {}
    for src, dst in [("sm", "radius-sm"), ("md", "radius-md"), ("lg", "radius-lg"), ("full", "radius-full")]:
        if src in rounded and rounded[src]:
            tokens[dst] = px_to_pt(rounded[src])

    return tokens


def detect_google_fonts(tokens: dict) -> list:
    """Detect known Google Fonts in font tokens and return list of family names."""
    google_fonts_known = {
        "inter", "roboto", "open sans", "lato", "montserrat", "poppins",
        "plus jakarta sans", "manrope", "dm sans", "work sans", "playfair display",
        "merriweather", "source serif pro", "ibm plex sans", "ibm plex serif",
        "ibm plex mono", "jetbrains mono", "fira code", "space grotesk",
    }
    found = set()
    for key in ("font-display", "font-body", "font-mono"):
        value = tokens.get(key, "").lower()
        for gf in google_fonts_known:
            if gf in value:
                found.add(gf.title())
    return sorted(found)


def generate_font_links(tokens: dict) -> str:
    """Generate <link> tags for Google Fonts detected in DESIGN.md."""
    fonts = detect_google_fonts(tokens)
    if not fonts:
        return ""
    families = "&".join(
        f"family={f.replace(' ', '+')}:wght@400;500;600;700"
        for f in fonts
    )
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        f'<link href="https://fonts.googleapis.com/css2?{families}&display=block" rel="stylesheet">'
    )


def tokens_to_css_root(tokens: dict) -> str:
    """Render tokens dict as :root CSS variables."""
    return "\n      ".join(f"--{k}: {v};" for k, v in tokens.items())


def parse_markdown_metadata(content: str):
    """Extract optional YAML frontmatter and return (metadata_dict, body)."""
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return {}, content
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, content[m.end():]


def extract_title_from_markdown(body: str, fallback="Lead Magnet"):
    m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def generate_toc_html(body: str) -> str:
    """Generate <li> entries for top-level # headings."""
    headings = re.findall(r"^#\s+(.+)$", body, re.MULTILINE)
    if not headings:
        return ""
    return "\n      ".join(f"<li><span>{h.strip()}</span></li>" for h in headings)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  {font_links}
  <style>
    :root {{
      {root_vars}
    }}

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    @page {{
      size: A4;
      margin: 25mm 20mm;
      @bottom-center {{
        content: counter(page);
        font-family: var(--font-body);
        font-size: var(--fs-small);
        color: var(--color-text-muted);
      }}
    }}

    @page :first {{
      margin: 0;
      @bottom-center {{ content: none; }}
    }}

    @media print {{
      * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
    }}

    html, body {{
      font-family: var(--font-body);
      font-size: var(--fs-body);
      line-height: var(--lh-normal);
      color: var(--color-text);
      background: var(--color-bg);
    }}

    .cover {{
      page-break-after: always;
      width: 210mm;
      height: 297mm;
      padding: 30mm 25mm;
      background: var(--color-primary);
      color: var(--color-bg);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    .cover-image {{
      width: 100%;
      height: 45%;
      background-size: cover;
      background-position: center;
      border-radius: var(--radius-lg);
      background-image: {cover_bg};
    }}

    .cover-title {{
      font-family: var(--font-display);
      font-size: var(--fs-display);
      font-weight: var(--fw-bold);
      line-height: var(--lh-tight);
      letter-spacing: var(--ls-display);
      margin-top: var(--space-8);
    }}

    .cover-author {{ font-size: var(--fs-h3); opacity: 0.85; margin-top: var(--space-4); }}
    .cover-date {{ font-size: var(--fs-small); opacity: 0.6; }}

    .toc {{ page-break-after: always; padding-top: var(--space-12); }}
    .toc h1 {{
      font-family: var(--font-display);
      font-size: var(--fs-h1);
      margin-bottom: var(--space-8);
      color: var(--color-primary);
    }}
    .toc ol {{ list-style: none; counter-reset: toc-item; }}
    .toc li {{
      counter-increment: toc-item;
      padding: var(--space-3) 0;
      border-bottom: 1pt solid var(--color-border);
    }}
    .toc li::before {{
      content: counter(toc-item) ". ";
      color: var(--color-accent);
      font-weight: var(--fw-semibold);
      margin-right: var(--space-3);
    }}

    .content h1 {{
      font-family: var(--font-display);
      font-size: var(--fs-h1);
      font-weight: var(--fw-bold);
      line-height: var(--lh-tight);
      color: var(--color-primary);
      margin-top: var(--space-12);
      margin-bottom: var(--space-6);
      page-break-before: always;
      page-break-after: avoid;
    }}
    .content h1:first-child {{ page-break-before: auto; }}

    .content h2 {{
      font-family: var(--font-display);
      font-size: var(--fs-h2);
      font-weight: var(--fw-semibold);
      color: var(--color-primary);
      margin-top: var(--space-8);
      margin-bottom: var(--space-4);
      page-break-after: avoid;
    }}

    .content h3 {{
      font-size: var(--fs-h3);
      font-weight: var(--fw-medium);
      color: var(--color-primary);
      margin-top: var(--space-6);
      margin-bottom: var(--space-3);
      page-break-after: avoid;
    }}

    .content p {{ margin-bottom: var(--space-4); orphans: 3; widows: 3; }}

    .content blockquote {{
      border-left: 4pt solid var(--color-accent);
      padding: var(--space-3) var(--space-4);
      margin: var(--space-6) 0;
      background: var(--color-bg-subtle);
      border-radius: var(--radius-sm);
      font-style: italic;
      color: var(--color-text-muted);
    }}

    .content ul, .content ol {{ margin-bottom: var(--space-4); padding-left: var(--space-6); }}
    .content li {{ margin-bottom: var(--space-2); }}

    .content table {{
      width: 100%;
      border-collapse: collapse;
      margin: var(--space-6) 0;
      font-size: var(--fs-small);
      page-break-inside: avoid;
    }}
    .content th {{
      background: var(--color-primary);
      color: var(--color-bg);
      padding: var(--space-3);
      text-align: left;
    }}
    .content td {{ padding: var(--space-3); border-bottom: 1pt solid var(--color-border); }}

    .content code {{
      font-family: var(--font-mono);
      background: var(--color-bg-subtle);
      padding: 2pt 4pt;
      border-radius: var(--radius-sm);
      font-size: 90%;
    }}
    .content pre {{
      background: var(--color-bg-subtle);
      padding: var(--space-4);
      border-radius: var(--radius-md);
      page-break-inside: avoid;
    }}

    .content a {{ color: var(--color-accent); text-decoration: underline; }}
  </style>
</head>
<body>

  <section class="cover">
    <div></div>
    <div class="cover-image"></div>
    <div>
      <h1 class="cover-title">{title}</h1>
      <p class="cover-author">{author}</p>
      <p class="cover-date">{date}</p>
    </div>
  </section>

  {toc_section}

  <section class="content">
    {content_html}
  </section>

</body>
</html>
"""


def build_html(args, tokens, body_md, metadata):
    title = args.title or metadata.get("title") or extract_title_from_markdown(body_md)
    author = args.author or metadata.get("author") or ""
    date = metadata.get("date") or datetime.now().strftime("%B %Y")

    cover_bg = "linear-gradient(135deg, var(--color-primary), var(--color-accent))"
    if args.cover and Path(args.cover).exists():
        cover_url = Path(args.cover).resolve().as_uri()
        cover_bg = f"url('{cover_url}')"

    content_html = md.markdown(
        body_md,
        extensions=["tables", "fenced_code", "attr_list", "toc", "footnotes"],
    )

    toc_inner = generate_toc_html(body_md)
    toc_section = (
        f'<section class="toc"><h1>Obsah</h1><ol>{toc_inner}</ol></section>'
        if toc_inner
        else ""
    )

    return HTML_TEMPLATE.format(
        title=title,
        font_links=generate_font_links(tokens),
        root_vars=tokens_to_css_root(tokens),
        cover_bg=cover_bg,
        author=author or "",
        date=date,
        toc_section=toc_section,
        content_html=content_html,
    )


async def render_pdf(html_path: Path, output_path: Path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(html_path.as_uri(), wait_until="networkidle")
        await page.evaluate("document.fonts.ready")
        await page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            prefer_css_page_size=True,
            display_header_footer=False,
        )
        await browser.close()


async def main():
    parser = argparse.ArgumentParser(description="Render lead magnet PDF from markdown.")
    parser.add_argument("--markdown", required=True, help="Path to source markdown file")
    parser.add_argument("--design", default="/documents/brand/DESIGN.md", help="Path to DESIGN.md")
    parser.add_argument("--output", required=True, help="Path to output PDF")
    parser.add_argument("--cover", help="Path to cover image (optional)")
    parser.add_argument("--author", help="Author name (overrides frontmatter)")
    parser.add_argument("--title", help="Title (overrides frontmatter)")
    args = parser.parse_args()

    markdown_path = Path(args.markdown)
    if not markdown_path.exists():
        print(f"❌ Markdown not found: {markdown_path}")
        sys.exit(1)

    raw = markdown_path.read_text(encoding="utf-8")
    metadata, body = parse_markdown_metadata(raw)

    tokens = parse_design_md(Path(args.design))
    html = build_html(args, tokens, body, metadata)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = output_path.parent / "_temp"
    temp_dir.mkdir(exist_ok=True)
    html_path = temp_dir / "content.html"
    html_path.write_text(html, encoding="utf-8")

    print(f"📄 HTML built → {html_path}")
    print(f"🚀 Rendering PDF via Playwright/Chromium…")

    await render_pdf(html_path, output_path)

    size_kb = output_path.stat().st_size / 1024
    print(f"✅ PDF created → {output_path}")
    print(f"   Size: {size_kb:.1f} KB")


if __name__ == "__main__":
    asyncio.run(main())
