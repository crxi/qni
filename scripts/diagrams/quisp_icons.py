"""QuISP icon loader.

Reads the QuISP SVG icons from `icons/` and turns each into a `<symbol>`
fragment that can be added to a Canvas's defs and referenced via `<use>`.

The QuISP icons are 100x100 viewBox each. After registration, a caller does:

    canvas.use("#quisp-bsa", x, y, width, height)

to drop the BSA glyph anywhere.
"""

from __future__ import annotations

import re
from pathlib import Path

# Icons live under images/ so the Astro app can also serve them as static
# assets if a page wants the standalone glyph (e.g. inline in prose). The
# generator only reads them at SVG-build time.
ICONS_DIR = Path(__file__).resolve().parents[2] / "images"

# Map symbol id -> source filename (under ICONS_DIR)
KNOWN = {
    "quisp-bsa": "icon-bsa.svg",
    "quisp-bsa-white": "icon-bsa-white.svg",  # rotated 180°, white background fill
    "quisp-epps": "icon-epps.svg",
    "quisp-rep1g": "icon-rep1g.svg",
    "quisp-mem": "icon-mem.svg",
    "quisp-comp": "icon-comp.svg",
    "bsm-meter": "icon-bsm-meter.svg",
}


def _extract_symbol_body(svg_text: str) -> str:
    """Pull the drawing payload out of a QuISP icon file.

    QuISP icons are Inkscape-exported. We strip the outer <svg>, the
    <sodipodi:namedview>, and the <defs> block (which only contains Inkscape
    path-effect metadata, not anything the drawing references). What remains
    are the actual paths inside <g id="layer1">.
    """
    # Drop sodipodi namedview
    svg_text = re.sub(
        r"<sodipodi:namedview[^>]*?(/>|>.*?</sodipodi:namedview>)",
        "",
        svg_text,
        flags=re.DOTALL,
    )
    # Drop defs (Inkscape path-effects only)
    svg_text = re.sub(r"<defs[^>]*>.*?</defs>", "", svg_text, flags=re.DOTALL)
    # Extract the inner content of the root <svg> element
    m = re.search(r"<svg[^>]*>(.*)</svg>", svg_text, flags=re.DOTALL)
    if not m:
        raise ValueError("Couldn't find <svg> root in icon source")
    inner = m.group(1)
    # Strip XML comments
    inner = re.sub(r"<!--.*?-->", "", inner, flags=re.DOTALL)
    # Strip Inkscape-namespaced attributes that some renderers complain about
    inner = re.sub(r'\s+(inkscape|sodipodi):[^=]+="[^"]*"', "", inner)
    return inner.strip()


def symbol_block(symbol_id: str) -> str:
    """Return a `<symbol id=...>…</symbol>` fragment for the given icon."""
    if symbol_id not in KNOWN:
        raise KeyError(f"Unknown QuISP symbol id: {symbol_id}")
    src = (ICONS_DIR / KNOWN[symbol_id]).read_text()
    body = _extract_symbol_body(src)
    # Read viewBox from source (QuISP icons are 100x100; the meter icon is 32x32).
    vb_m = re.search(r'viewBox="([^"]+)"', src)
    vb = vb_m.group(1) if vb_m else "0 0 100 100"
    return (
        f'<symbol id="{symbol_id}" viewBox="{vb}" overflow="visible">'
        f"{body}"
        f"</symbol>"
    )


def register_all(canvas) -> None:
    """Register every known QuISP icon on the canvas as a <symbol>."""
    for sid in KNOWN:
        canvas.add_def(symbol_block(sid))


def register(canvas, *symbol_ids: str) -> None:
    """Register a subset of QuISP icons by id."""
    for sid in symbol_ids:
        canvas.add_def(symbol_block(sid))
