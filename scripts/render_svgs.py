#!/usr/bin/env python3
"""
render_svgs.py — render SVG files to PNG via headless Chrome.

Useful when SVGs need to be embedded in a tool that can't display them
(e.g. Word, PowerPoint). ImageMagick's SVG renderer drops <use><symbol>
references and several other commonly-used features, so we go through
Chrome which renders SVG the way browsers do.

Usage:
    # Render specific files
    python3 scripts/render_svgs.py --out /tmp/out  images/BSM.svg images/foo.svg

    # Higher resolution (default DPI ≈ 2× the viewBox width)
    python3 scripts/render_svgs.py --out /tmp/out --scale 3  images/BSM.svg

Notes:
    - Output PNG width = viewBox.width * scale. Aspect ratio preserved.
    - Background is white (most Office paste targets expect opaque).
"""

from __future__ import annotations
import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

VIEWBOX_RE = re.compile(
    r'viewBox\s*=\s*["\']\s*'
    r'(-?[\d.]+)\s+(-?[\d.]+)\s+([\d.]+)\s+([\d.]+)\s*["\']'
)


def viewbox(svg_path: Path):
    """Return (vbx, vby, vbw, vbh). Falls back to (0, 0, 800, 600)."""
    text = svg_path.read_text(encoding="utf-8", errors="replace")
    m = VIEWBOX_RE.search(text)
    if not m:
        print(f"warn: no viewBox in {svg_path}, using 800×600", file=sys.stderr)
        return 0, 0, 800, 600
    return float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))


def render(svg_path: Path, out_path: Path, scale: float = 2.0):
    """Render one SVG to PNG via Chrome headless."""
    _, _, vbw, vbh = viewbox(svg_path)
    width = int(round(vbw * scale))
    height = int(round(vbh * scale))

    # Inline the SVG content into a tiny HTML so we control sizing.
    svg_text = svg_path.read_text(encoding="utf-8", errors="replace")
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
html, body {{ margin: 0; padding: 0; background: white; }}
body > svg {{ display: block; width: 100vw; height: 100vh; }}
</style></head><body>{svg_text}</body></html>
"""
    with tempfile.NamedTemporaryFile(
        suffix=".html", mode="w", encoding="utf-8", delete=False
    ) as f:
        f.write(html)
        wrapper = f.name

    try:
        cmd = [
            CHROME,
            "--headless", "--disable-gpu", "--hide-scrollbars",
            "--no-first-run", "--no-default-browser-check",
            f"--window-size={width},{height}",
            f"--screenshot={out_path}",
            f"file://{wrapper}",
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if not out_path.exists():
            sys.exit(f"Chrome failed to write {out_path}: "
                     f"stderr={result.stderr.decode(errors='replace')[-400:]}")
        return width, height
    finally:
        os.unlink(wrapper)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("svgs", nargs="*", type=Path,
                    help="SVG files to render")
    ap.add_argument("--out", type=Path,
                    help="output dir (default: CWD)")
    ap.add_argument("--scale", type=float, default=2.0,
                    help="output px per viewBox unit (default 2.0)")
    args = ap.parse_args()

    if not Path(CHROME).exists():
        sys.exit(f"Chrome not found at {CHROME}")

    svgs = args.svgs
    out_dir = args.out or Path.cwd()

    if not svgs:
        sys.exit("No SVGs to render. Pass one or more SVG paths.")

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Rendering {len(svgs)} SVG(s) → {out_dir} at scale {args.scale}×")
    for svg in svgs:
        if not svg.exists():
            print(f"  skip (missing): {svg}", file=sys.stderr)
            continue
        png = out_dir / (svg.stem + ".png")
        w, h = render(svg, png, args.scale)
        size_kb = png.stat().st_size // 1024
        print(f"  {svg.name}  →  {png.relative_to(REPO_ROOT) if png.is_relative_to(REPO_ROOT) else png}  ({w}×{h}, {size_kb} KB)")


if __name__ == "__main__":
    main()
