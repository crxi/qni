"""Generate the colourful QR-code SVG embedded on the home page.

Run from the repo root::

    python scripts/gen_qr.py

Re-run if the deployed URL ever changes.

Visual design: every dark module is rendered in one of the three
project qubit palette colours — data orange, comms green, memory
purple. Data modules use small filled circles (a "qubit grid" look);
the three corner finder patterns and the central alignment pattern
keep their solid-square shape so phone scanners can still find and
orient the code, but they're recoloured per palette (one colour per
finder corner). Error correction stays at level L since the QR is
displayed on a clean screen — that keeps the module grid small
(25×25 for this URL) rather than the 37×37 the higher-ECC levels
needed.

Output: ``images/qr-qni.svg`` (also visible via the
``web/public/images`` symlink).
"""

from __future__ import annotations

from pathlib import Path
import qrcode

# Bare URL (no scheme) — 13 chars × byte-mode fits comfortably in
# version-2 + level-L capacity, pinned to the desired 25×25 module
# grid via version=2 below. Adding "https://" would bump the version.
# Modern phone scanners (iOS Camera, Android Lens, etc.) auto-prepend
# the scheme when they recognise a bare domain, so this scans as
# https://qni.pages.dev on every common scanner.
URL = "qni.pages.dev"
DISPLAY_URL = "https://" + URL  # what the dialog shows beneath the QR
OUT = Path(__file__).resolve().parent.parent / "images" / "qr-qni.svg"

# Project qubit-and-photon palette — fills + strokes match the .data,
# .comm, .memory, .photon CSS rules in entanglement_ops.py /
# ops-primitives.svg, so the QR reads as the same colour family as the
# diagrams across the workspace.
COLOURS = [
    ("#f29453", "#8a3f0e"),  # 0: data    (orange)
    ("#22c55e", "#15803d"),  # 1: comms   (green)
    ("#9b87c4", "#6048a3"),  # 2: memory  (purple)
    ("#2f6fd6", "#1a4a99"),  # 3: photon  (blue)
]
# One palette colour per finder corner + alignment pattern — TL data,
# TR comms, BL memory, alignment photon. Data-module circles cycle
# through all four (COLOURS[idx % len(COLOURS)]).
FINDER_TL = COLOURS[0]
FINDER_TR = COLOURS[1]
FINDER_BL = COLOURS[2]
ALIGN_COL = COLOURS[3]

# Build a QR at version 2 + level L = 25×25 module grid (capacity 32
# bytes at L — fits this 31-char URL). The code is shown on a clean
# screen so the low ECC is fine; the small grid means fewer, larger
# qubit circles per side.
qr = qrcode.QRCode(
    version=2,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=0,       # no built-in quiet zone — we add our own below
)
qr.add_data(URL)
qr.make(fit=True)  # version 2 fits cleanly with the bare URL above

matrix = qr.get_matrix()
n = len(matrix)     # actual module count (25 for v2)
BORDER = 2          # quiet-zone, in modules — added manually around the grid
BOX = 10            # px per module
size_px = (n + 2 * BORDER) * BOX


def finder_colour(row: int, col: int):
    """Palette colour for a finder-pattern module, or None if (row,
    col) isn't inside one of the three 7×7 finder patterns. Used to
    suppress per-module rendering inside finders so they can be drawn
    once as an annulus + dot (cleaner shapes, better scan reliability).
    """
    if row < 7 and col < 7:
        return FINDER_TL
    if row < 7 and col >= n - 7:
        return FINDER_TR
    if row >= n - 7 and col < 7:
        return FINDER_BL
    return None


# Centre (module-grid) coordinates of each finder pattern + the
# radial-gradient id to halo it with.
FINDER_PATTERNS = [
    (3,       3,       FINDER_TL, "glow-data"),
    (3,       n - 4,   FINDER_TR, "glow-comms"),
    (n - 4,   3,       FINDER_BL, "glow-memory"),
]


def alignment_centres(n_modules: int) -> list[tuple[int, int]]:
    """Approximate locations of the alignment-pattern centres for the
    QR version this matrix corresponds to. For version 1 (21 modules)
    there is no alignment pattern; for v≥2 there is one centre at
    (n-7, n-7). Higher versions add more; we treat any version we hit
    with a single centre, which is correct up to version 6 (41
    modules), well above what we need for a short URL.
    """
    if n_modules == 21:  # version 1
        return []
    return [(n_modules - 7, n_modules - 7)]


ALIGN_CENTRES = alignment_centres(n)


def in_alignment(row: int, col: int) -> bool:
    """True if (row, col) is inside the 5×5 alignment pattern."""
    for cr, cc in ALIGN_CENTRES:
        if cr - 2 <= row <= cr + 2 and cc - 2 <= col <= cc + 2:
            return True
    return False


parts: list[str] = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'viewBox="0 0 {size_px} {size_px}" '
    f'width="{size_px}" height="{size_px}" '
    f'role="img" aria-label="QR code linking to {URL}">'
)
# Per-palette radial-gradient glow defs — same stop palette as the
# `#ops-cloud` gradient in entanglement_ops.py / ops-primitives.svg.
# Used as a soft halo BEHIND each finder pattern + the alignment
# pattern so the QR fiducials read as photon-style glows without
# softening the crisp dark/light geometry scanners need.
GRADIENT_IDS = ["glow-data", "glow-comms", "glow-memory", "glow-photon"]
defs_chunks = ["<defs>"]
for gid, (hex_fill, _) in zip(GRADIENT_IDS, COLOURS):
    defs_chunks.append(
        f'<radialGradient id="{gid}">'
          f'<stop offset="0%"   stop-color="{hex_fill}" stop-opacity="0.95"/>'
          f'<stop offset="35%"  stop-color="{hex_fill}" stop-opacity="0.85"/>'
          f'<stop offset="70%"  stop-color="{hex_fill}" stop-opacity="0.40"/>'
          f'<stop offset="100%" stop-color="{hex_fill}" stop-opacity="0"/>'
        '</radialGradient>'
    )
defs_chunks.append("</defs>")
parts.append("".join(defs_chunks))
parts.append(f'<rect width="{size_px}" height="{size_px}" fill="#ffffff"/>')

# Each data module renders as a small coloured circle (0.42 × box).
# The three finder patterns and the alignment pattern get drawn AFTER
# the per-module loop as clean annulus + dot pairs (one per finder /
# alignment), matching the deployed designer-QR style — outer ring
# spans 1 module thick, inner ring (white gap) is 1 module thick, the
# centre dot covers the 3×3 dark core. This preserves the scanner's
# 1:1:3:1:1 ratio along all scan lines.
DATA_R = BOX * 0.42
idx = 0
for row in range(n):
    for col in range(n):
        if not matrix[row][col]:
            continue
        # Skip individual modules inside finder / alignment regions —
        # they're redrawn as clean annulus + dot shapes below.
        if finder_colour(row, col) is not None:
            continue
        if in_alignment(row, col):
            continue
        x = (col + BORDER) * BOX
        y = (row + BORDER) * BOX
        cx = x + BOX / 2
        cy = y + BOX / 2
        fill, stroke = COLOURS[idx % len(COLOURS)]
        idx += 1
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{DATA_R}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="0.8"/>'
        )


def annulus_path(cx: float, cy: float, r_outer: float, r_inner: float) -> str:
    """SVG path d-string for an annulus (donut) — two circles, the
    inner one acting as a hole via even-odd fill rule. Draw each
    circle as a pair of half-arcs so the path is self-contained."""
    return (
        f"M {cx - r_outer},{cy} "
        f"a {r_outer},{r_outer} 0 1,0 {2 * r_outer},0 "
        f"a {r_outer},{r_outer} 0 1,0 {-2 * r_outer},0 "
        f"M {cx - r_inner},{cy} "
        f"a {r_inner},{r_inner} 0 1,0 {2 * r_inner},0 "
        f"a {r_inner},{r_inner} 0 1,0 {-2 * r_inner},0"
    )


# Draw each finder pattern as an annulus (radii 3.5 → 2.5 modules)
# plus a centre dot (radius 1.5 modules), with a per-colour soft halo
# painted behind and a white mask in between (same recipe as the
# alignment pattern below). Scan-line ratio across the centre stays
# 1:1:3:1:1 because the crisp shapes sit on top of an opaque white
# disc the size of the outer ring.
R_OUTER = 3.5 * BOX
R_INNER = 2.5 * BOX
R_DOT   = 1.5 * BOX
R_GLOW  = R_OUTER * 1.25  # halo extends 25% beyond the outer ring
for (r_centre, c_centre, colour, glow_id) in FINDER_PATTERNS:
    fill, stroke = colour
    cx = (c_centre + BORDER) * BOX + BOX / 2
    cy = (r_centre + BORDER) * BOX + BOX / 2
    # 1) Soft per-colour glow behind everything.
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{R_GLOW}" fill="url(#{glow_id})"/>'
    )
    # 2) White mask covering the finder's inner area out to R_OUTER —
    #    keeps the 1-module light gap between dot and annulus actually
    #    white, instead of glow-tinted.
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{R_OUTER}" fill="#ffffff"/>'
    )
    # 3) Crisp annulus + centre dot on top.
    parts.append(
        f'<path d="{annulus_path(cx, cy, R_OUTER, R_INNER)}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="0.4" '
        f'fill-rule="evenodd"/>'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{R_DOT}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="0.4"/>'
    )


# Alignment pattern (5×5: 1-module dark ring + 1-module white gap +
# 1-module centre dot). Draw as a small annulus + centre dot in the
# photon-blue colour, scaled to the 5×5 footprint, with a soft
# photon-style radial-gradient glow painted BEHIND. The glow extends
# ~50% beyond the alignment outer ring so the pattern visually
# resembles the fuzzy photon cloud on the workspace diagrams, but the
# crisp annulus + dot on top preserve the scanner-detectable dark /
# light geometry.
ALIGN_R_OUTER = 2.5 * BOX
ALIGN_R_INNER = 1.5 * BOX
ALIGN_R_DOT   = 0.5 * BOX
ALIGN_R_GLOW  = ALIGN_R_OUTER * 1.25  # halo radius — small extension only
for (cr, cc) in ALIGN_CENTRES:
    fill, stroke = ALIGN_COL
    cx = (cc + BORDER) * BOX + BOX / 2
    cy = (cr + BORDER) * BOX + BOX / 2
    # 1) Soft photon-blue glow first (sits behind everything).
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{ALIGN_R_GLOW}" '
        f'fill="url(#glow-photon)"/>'
    )
    # 2) Solid-white mask covering the alignment pattern's inner area
    #    out to the OUTER ring. Hides the glow inside the pattern so
    #    the 1-module gap between the centre dot and the annulus reads
    #    as clean white (which scanners need). The visible halo is
    #    therefore only the thin ring from R_OUTER → R_GLOW.
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{ALIGN_R_OUTER}" fill="#ffffff"/>'
    )
    # 3) Crisp annulus + centre dot on top — scanner-readable.
    parts.append(
        f'<path d="{annulus_path(cx, cy, ALIGN_R_OUTER, ALIGN_R_INNER)}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="0.4" '
        f'fill-rule="evenodd"/>'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{ALIGN_R_DOT}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="0.4"/>'
    )

parts.append("</svg>")
OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"wrote {OUT}  ->  {URL}  ({n}×{n} modules)")
