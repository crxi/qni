"""Render 2K PNGs (longest side = 2048 px) for the workspace's figure SVGs
using headless Chrome — so the rasterisation matches what a browser
actually shows. Inter (the site's primary typeface) is loaded from
Google Fonts inside the wrapper page, and Chrome handles per-glyph font
fallback through its real text-rendering pipeline. No tspan tricks, no
cairosvg quirks — what you see in DevTools is what the PNG looks like.

Each output is saved alongside the source as `<basename>_2k.png`, and
mirrored into `web/public/images/` if a copy of the SVG lives there.

Usage:
    python3 scripts/render_png_2k.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LONG_SIDE = 2048

REPO_ROOT = Path(__file__).resolve().parents[1]

# Substantive SVGs worth rendering at 2K. Icons, vendor logos, and QuISP
# glyphs are excluded — they're small and used at icon sizes on the site.
TARGETS = [
    "images/4hop-topology.svg",
    "images/4hop-swap-tree.svg",
    "images/BSM.svg",
    "images/q1-stack.svg",
    "images/transduction.svg",
    "images/swapping-chain.svg",
    "images/swapping-chain-narrow.svg",
    "images/swapping-chain-4hop.svg",
    "images/distribution-mm.svg",
    "images/distribution-sr.svg",
    "images/distribution-ms.svg",
    "images/ops-primitives.svg",
    "spectrum/output/spectrum.svg",
]


# Chrome locations to try (macOS first, then common Linux paths).
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def find_chrome() -> str:
    for cand in CHROME_CANDIDATES:
        if Path(cand).exists():
            return cand
    on_path = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chrome")
    if on_path:
        return on_path
    raise RuntimeError("Chrome / Chromium not found. Install Google Chrome.")


_VIEWBOX = re.compile(r'viewBox="([\d.\-eE +]+)"')
_W = re.compile(r'\bwidth="([\d.]+)(?:px)?"')
_H = re.compile(r'\bheight="([\d.]+)(?:px)?"')


def svg_dimensions(svg_path: Path) -> tuple[float, float]:
    """Read (width, height) in user units from the SVG. Prefer viewBox over
    the width/height attributes (which may carry CSS units we don't want
    to interpret)."""
    text = svg_path.read_text(encoding="utf-8")
    m = _VIEWBOX.search(text)
    if m:
        parts = m.group(1).split()
        if len(parts) == 4:
            return float(parts[2]), float(parts[3])
    mw, mh = _W.search(text), _H.search(text)
    if mw and mh:
        return float(mw.group(1)), float(mh.group(1))
    raise RuntimeError(f"could not read dimensions from {svg_path}")


HTML_WRAPPER = """<!doctype html>
<html><head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  html, body {{
    margin: 0;
    padding: 0;
    background: #ffffff;
    width: {w}px;
    height: {h}px;
    overflow: hidden;
  }}
  /* Make 'sans-serif' resolve to Inter to match the live site. */
  body {{ font-family: "Inter", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif; }}
  svg {{
    display: block;
    width: {w}px;
    height: {h}px;
  }}
</style>
</head>
<body>
{svg}
</body>
</html>
"""


def render(svg_path: Path, png_path: Path, chrome: str) -> None:
    sw, sh = svg_dimensions(svg_path)
    if sw >= sh:
        out_w = LONG_SIDE
        out_h = round(LONG_SIDE * sh / sw)
    else:
        out_h = LONG_SIDE
        out_w = round(LONG_SIDE * sw / sh)

    svg_text = svg_path.read_text(encoding="utf-8")
    html = HTML_WRAPPER.format(w=out_w, h=out_h, svg=svg_text)

    # Chrome headless needs a file:// URL.
    with tempfile.NamedTemporaryFile(
        suffix=".html", mode="w", delete=False, encoding="utf-8"
    ) as f:
        f.write(html)
        html_path = Path(f.name)

    try:
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            # ARGB hex: FF alpha = opaque white, so downloaded PNGs aren't
            # transparent (transparent reads as black in some viewers/slides).
            "--default-background-color=FFFFFFFF",
            f"--window-size={out_w},{out_h}",
            f"--screenshot={png_path}",
            # Wait long enough for the Inter @font-face to download +
            # render before the screenshot is captured.
            "--virtual-time-budget=4000",
            html_path.as_uri(),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"  ! chrome exit {result.returncode}: {result.stderr[:200]}",
                  file=sys.stderr)
    finally:
        html_path.unlink(missing_ok=True)

    print(f"  {svg_path.relative_to(REPO_ROOT)}  →  {png_path.name}  ({out_w}×{out_h})")


def main() -> int:
    chrome = find_chrome()
    print(f"Using {chrome}")
    missing: list[str] = []
    for rel in TARGETS:
        src = REPO_ROOT / rel
        if not src.exists():
            missing.append(rel)
            continue
        dst = src.with_name(f"{src.stem}_2k.png")
        render(src, dst, chrome)

        web_src = REPO_ROOT / "web" / "public" / "images" / src.name
        if web_src.exists():
            web_dst = web_src.with_name(f"{src.stem}_2k.png")
            render(web_src, web_dst, chrome)

    if missing:
        print("\nSkipped (not present):")
        for m in missing:
            print(f"  {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
