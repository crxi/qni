"""Generate images/ops-primitives.svg (served as /images/ via the web/public/images symlink).

Run from the repo root::

    python -m scripts.diagrams.entanglement_ops

Five-row primitives figure shown on /entanglement, modelled on Aliro's
network-operations diagram. Each row pairs a *before* and *after* network
state with a chevron arrow between them. Rows, top-to-bottom:

  1. Elementary entanglement generation (EEG) — MidpointSource via BSA,
     including the matter-photon emission bonds.
  2. Heralded entanglement generation — same topology + a ✓ herald.
  3. Distillation / purification — two pairs in, one cleaner pair out.
  4. Entanglement swapping — A↔BSA↔B becomes A↔B; BSA empty after.
  5. Teleportation — user qubit hops across a four-node chain, consuming
     the resource state.

A legend strip at the bottom names every glyph used in the figure.
"""

from __future__ import annotations

import math
from pathlib import Path

from .svglib import Canvas
from . import quisp_icons as Q


# ---------------------------------------------------------------------------
# LAYOUT
# ---------------------------------------------------------------------------

W = 760
ROW_H = 128
N_ROWS = 4
LEGEND_H = 70
TOP_PAD = 8
H = TOP_PAD + N_ROWS * ROW_H + LEGEND_H + 14

# Per-row panel geometry. The text column on the left is kept narrow so
# both before/after panels can share the same width and read as a fair
# before-vs-after comparison rather than a wide AFTER beside a cramped
# BEFORE. The arrow between them is a small chevron (see `_arrow`), so
# the gap can be tight without crowding. Long titles (HEG, HEP) get an
# extra line so their last word fits within TITLE_W; see _row_heg / _row_hep.
TITLE_X = 12          # left edge of title text
TITLE_W = 120
BEFORE_X = 130
BEFORE_W = 290
ARROW_X = 431         # chevron CENTRE (see _arrow) — balanced midway between panels
AFTER_X = 442
AFTER_W = 290

# Row inner padding (panel top/bottom)
PANEL_TOP = 12
PANEL_BOT = 116
ROW_CENTRE_Y = 60     # within-row y for the main beam / qubit row

# Standardised classical-line offset from panel top. The classical line
# sits 10 px above the panel bottom in every row, so the visual rhythm
# is consistent rather than each row picking its own gap.
CLASS_LINE_Y = PANEL_BOT - 10   # = 106; relative to y0

# Qubit radius
QR = 11
USER_QR = 11
PHOTON_R = 8

# BSA icon size
BSA_SIZE = 28


# ---------------------------------------------------------------------------
# COLOUR PALETTE — copied from topology_4hop.py
# ---------------------------------------------------------------------------

CSS = """
  .data       { fill: #f29453; stroke: #8a3f0e; stroke-width: 1; }
  .comm       { fill: #22c55e; stroke: #15803d; stroke-width: 1; }
  .memory     { fill: #9b87c4; stroke: #6048a3; stroke-width: 1; }
  .user       { fill: #d97706; stroke: #7c3a05; stroke-width: 1; }
  .photon     { fill: #2f6fd6; stroke: #1a4a99; stroke-width: 0.8; }

  .panel      { fill: none; stroke: #c9ced6; stroke-width: 1; }
  .node       { fill: #ffffff; stroke: #8a929e; stroke-width: 1; }
  .fibre      { stroke: #2f6fd6; stroke-width: 1.6; fill: none; opacity: 0.6; }
  .fibre-dot  { stroke: #aab0ba; stroke-width: 1; fill: none; stroke-dasharray: 3 3; opacity: 0.7; }
  .classical  { stroke: #9aa3af; stroke-width: 1; fill: none; }
  .bond       { stroke: #1a4a99; stroke-width: 1.7; fill: none; }
  .bond--thick{ stroke: #1a4a99; stroke-width: 3.0; fill: none; }
  .bond--matter-photon { stroke: #1a4a99; stroke-width: 1.4; fill: none; opacity: 0.85; }
  /* Raw entanglement bond — used for the post-BSM, pre-correction Bell pair.
     Grey because the entanglement exists but is in one of four random Bell
     states until the classical correction arrives; once corrected it
     becomes a canonical |Φ+⟩ rendered as `bond--thick` (photon-blue).
     Initial opacity 0; the JS toggles it visible at sub 2–3 and hides it
     again at sub ≥ 4 when the canonical bond takes over. */
  .bond--raw  { stroke: #9aa3af; stroke-width: 3.0; fill: none; opacity: 0; }
  .bond-lbl   { font: 600 10px sans-serif; fill: #1a4a99; text-anchor: middle; }

  .row-ttl    { font: 700 13px sans-serif; fill: #1a1f2a; text-anchor: start; }
  .row-sub    { font: 11px sans-serif; fill: #5a6472; text-anchor: start; }
  .herald     { font: 700 11px sans-serif; fill: #15803d; text-anchor: middle; }
  .credit     { font: italic 9.5px sans-serif; fill: #8a929e; text-anchor: start; }
  .legend-ttl { font: 700 11px sans-serif; fill: #1a1f2a; text-anchor: start; }
  .legend-txt { font: 10.5px sans-serif; fill: #3a4150; text-anchor: start; dominant-baseline: middle; }
  .qbit-in    { font: 700 10px sans-serif; fill: #ffffff; text-anchor: middle; dominant-baseline: central; }
  .arrow      { fill: #6a7280; opacity: 0.55; }
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _node(cv: Canvas, x: float, y: float, w: float, h: float, name: str = "") -> None:
    cv.rect(x, y, w, h, cls="node", rx=6, name=name)


def _qubit(cv: Canvas, cx: float, cy: float, role: str, letter: str | None = None,
           name: str = "") -> None:
    cv.circle(cx, cy, QR, cls=role, name=name)
    if letter:
        cv.text(cx, cy, letter, cls="qbit-in", font_size=10, name=f"{name}-in")


def _photon(cv: Canvas, cx: float, cy: float, name: str = "") -> None:
    """Fuzzy blue radial cloud at (cx, cy) using shared #ops-cloud gradient."""
    cv.add(
        f'<circle cx="{cx}" cy="{cy}" r="{PHOTON_R}" '
        f'fill="url(#ops-cloud)"/>',
        kind="shape", name=name,
    )


def _bond_wave(cv: Canvas, x0: float, x1: float, y: float, *,
               cls: str = "bond", amp: float = 6, half_wl: float = 14,
               name: str = "") -> None:
    """Sinusoidal wavy line from (x0,y) to (x1,y). Two-cycle minimum."""
    n_half = max(int((x1 - x0) / half_wl), 2)
    span = n_half * half_wl
    pad = (x1 - x0 - span) / 2
    sx = x0 + pad
    parts = [f"M {x0} {y} L {sx} {y}"]
    parts.append(f"q {half_wl/2} {-amp} {half_wl} 0")
    for _ in range(n_half - 1):
        parts.append(f"t {half_wl} 0")
    parts.append(f"L {x1} {y}")
    cv.add(f'<path d="{" ".join(parts)}" class="{cls}"/>',
           kind="shape", name=name)


def _bond_wave_arch(cv: Canvas, x0: float, y0: float, x1: float, y1: float,
                    *, peak_dy: float = 36, amp: float = 4,
                    cls: str = "bond", name: str = "") -> None:
    """Wavy bond along a parabolic arc peaking ``peak_dy`` above the chord.

    Samples the arc densely; at each sample, offsets perpendicular by a
    sinusoidal waviness whose amplitude tapers to zero at the endpoints so the
    line lands cleanly on the qubit circles. Use this whenever an entanglement
    bond has to clear an obstacle (empty relay during swapping, intervening
    nodes during teleportation). Wavy-arched, never Bezier-smooth — straight or
    smooth-arched lines are reserved for classical channels.
    """
    L = math.hypot(x1 - x0, y1 - y0)
    cycles = max(int(L / 14), 3)
    n = max(60, int(L / 4))
    pts: list[tuple[float, float]] = []
    for i in range(n + 1):
        t = i / n
        # Parabolic arc: chord + downward parabola scaled by peak_dy.
        cx = x0 + (x1 - x0) * t
        cy_arc = y0 + (y1 - y0) * t - 4 * peak_dy * t * (1 - t)
        # Tangent (numerical) for the perpendicular waviness offset.
        dt = 1e-3
        ta, tb = max(0, t - dt), min(1, t + dt)
        xa = x0 + (x1 - x0) * ta
        ya = y0 + (y1 - y0) * ta - 4 * peak_dy * ta * (1 - ta)
        xb = x0 + (x1 - x0) * tb
        yb = y0 + (y1 - y0) * tb - 4 * peak_dy * tb * (1 - tb)
        tx, ty = xb - xa, yb - ya
        tl = math.hypot(tx, ty) or 1
        nx, ny = -ty / tl, tx / tl
        taper = math.sin(t * math.pi)
        offset = amp * math.sin(t * cycles * 2 * math.pi) * taper
        pts.append((cx + nx * offset, cy_arc + ny * offset))
    d = "M " + " L ".join(f"{p[0]:.2f} {p[1]:.2f}" for p in pts)
    cv.add(f'<path d="{d}" class="{cls}"/>', kind="shape", name=name)


def _arrow(cv: Canvas, cx: float, cy: float) -> None:
    """Small chevron arrow centred on (cx, cy). 12 px wide, 10 px tall."""
    cv.add(
        f'<path d="M {cx-6} {cy-5} L {cx+6} {cy} L {cx-6} {cy+5} L {cx-3} {cy} Z" '
        f'class="arrow"/>',
        kind="shape", name="arrow",
    )


def _panel(cv: Canvas, x: float, y: float, w: float, h: float, name: str) -> None:
    cv.rect(x, y, w, h, cls="panel", rx=6, name=name)


def _bsa(cv: Canvas, cx: float, cy: float, size: float = BSA_SIZE,
         name: str = "bsa") -> None:
    cv.use("#quisp-bsa-white", cx - size / 2, cy - size / 2, size, size, name=name)


def _meter(cv: Canvas, cx: float, cy: float, size: float = 32,
           name: str = "bsm-meter") -> None:
    """Matter-side BSM glyph (semicircular gauge inside a rectangular box).

    The source icon is 36×28; ``size`` here is the rendered *width* in figure
    pixels, with height scaled to preserve aspect. Centred horizontally on
    ``cx`` and vertically on ``cy``.
    """
    w = size
    h = size * 28 / 36
    cv.use("#bsm-meter", cx - w / 2, cy - h / 2, w, h, name=name)


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """Greedy word-wrap returning lines of at most ``max_chars`` each.

    SVG ``<text>`` is single-line per element, so callers that want
    natural wrapping in the narrow title column have to break long
    strings up front. A word that is itself longer than ``max_chars``
    overflows on its own line (we don't hyphenate).
    """
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for w in words:
        if current and len(" ".join(current + [w])) > max_chars:
            lines.append(" ".join(current))
            current = [w]
        else:
            current.append(w)
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def _class_line_with_stubs(cv: Canvas, y0: float, x_start: float, x_end: float,
                            stubs: list[tuple[float, float]], name: str) -> None:
    """Solid grey classical channel + vertical stubs UP into each device.

    ``stubs`` is a list of ``(cx, top_y)`` pairs — one per device that
    sits on this row. The horizontal line spans ``x_start..x_end`` at
    ``y0 + CLASS_LINE_Y``; each stub is a short vertical line from the
    classical line up to ``top_y`` at ``cx``. Same visual recipe as the
    swapping page's 1G repeater figure.
    """
    line_y = y0 + CLASS_LINE_Y
    cv.line(x_start, line_y, x_end, line_y,
            cls="classical", name=name)
    for i, (cx, top_y) in enumerate(stubs):
        cv.line(cx, top_y, cx, line_y,
                cls="classical", name=f"{name}-stub-{i}")


def _row_title(cv: Canvas, y0: float, title, sublines: list[str]) -> None:
    """Render the left-rail row title + sublines.

    ``title`` accepts either a single string (one line) or a list of strings
    (multi-line, ~2–3 lines). Sublines are auto-wrapped to fit ``TITLE_W``
    using a rough chars/px heuristic for the 11 px subline font; callers
    can still pass shorter strings if they want a specific break. The
    whole block is anchored so the title's last line sits just above the
    sublines, keeping vertical centring stable across rows.
    """
    title_lines = title if isinstance(title, list) else [title]
    # ~6 px per char for an 11 px sans-serif at this weight.
    sub_max_chars = max(8, TITLE_W // 6)
    wrapped_subs: list[str] = []
    for s in sublines:
        wrapped_subs.extend(_wrap_text(s, sub_max_chars))
    block_h = len(title_lines) * 16 + len(wrapped_subs) * 14
    y_start = y0 + (ROW_H - block_h) / 2 + 14
    for i, line in enumerate(title_lines):
        cv.text(TITLE_X, y_start + i * 16, line, cls="row-ttl", font_size=13,
                anchor="start", name=f"ttl-{title_lines[0]}-{i}")
    sub_y0 = y_start + len(title_lines) * 16 + 4
    for i, s in enumerate(wrapped_subs):
        cv.text(TITLE_X, sub_y0 + i * 14, s, cls="row-sub", font_size=11,
                anchor="start", name=f"sub-{title_lines[0]}-{i}")


def _row_heg(cv: Canvas, y0: float) -> None:
    title = ["Heralded", "Entanglement", "Generation", "(HEG)"]
    sub = ["single hop via", "midpoint BSA"]
    tag = "HEG"
    cv.begin_group(data_op_row="generation")
    _row_title(cv, y0, title, sub)

    cy = y0 + ROW_CENTRE_Y

    # ---- BEFORE panel
    cv.begin_group(data_op_side="before")
    _panel(cv, BEFORE_X, y0 + PANEL_TOP, BEFORE_W, PANEL_BOT - PANEL_TOP,
           name=f"{tag}-before")
    # Two nodes
    nA_x = BEFORE_X + 16
    nB_x = BEFORE_X + BEFORE_W - 16 - 56
    _node(cv, nA_x, cy - 24, 56, 48, name=f"{tag}-A")
    _node(cv, nB_x, cy - 24, 56, 48, name=f"{tag}-B")
    # Comm qubits inside (right edge of A, left edge of B)
    qA_x = nA_x + 14
    qB_x = nB_x + 56 - 14
    _qubit(cv, qA_x, cy, "comm", "C", name=f"{tag}-CA")
    _qubit(cv, qB_x, cy, "comm", "C", name=f"{tag}-CB")
    # Matter-photon entanglement bonds — short wavy line from each comm
    # qubit out into a photon glyph travelling toward the central BSA.
    phA_x = qA_x + 28
    phB_x = qB_x - 28
    _bond_wave(cv, qA_x + QR, phA_x - PHOTON_R, cy,
               cls="bond--matter-photon", amp=4, half_wl=8,
               name=f"{tag}-mp-A")
    _bond_wave(cv, phB_x + PHOTON_R, qB_x - QR, cy,
               cls="bond--matter-photon", amp=4, half_wl=8,
               name=f"{tag}-mp-B")
    # Photons in transit
    _photon(cv, phA_x, cy, name=f"{tag}-phA")
    _photon(cv, phB_x, cy, name=f"{tag}-phB")
    # BSA in the middle
    bsa_cx = (BEFORE_X + BEFORE_X + BEFORE_W) / 2
    _bsa(cv, bsa_cx, cy, name=f"{tag}-bsa-before")
    # Short fibres from photons to BSA edge
    cv.line(phA_x + PHOTON_R, cy, bsa_cx - BSA_SIZE / 2, cy,
            cls="fibre", name=f"{tag}-fA")
    cv.line(bsa_cx + BSA_SIZE / 2, cy, phB_x - PHOTON_R, cy,
            cls="fibre", name=f"{tag}-fB")
    # Classical channel + vertical stubs into both nodes and the BSA.
    _class_line_with_stubs(cv, y0, nA_x, nB_x + 56,
                            stubs=[(nA_x + 28, cy + 24),
                                   (bsa_cx,     cy + BSA_SIZE / 2),
                                   (nB_x + 28, cy + 24)],
                            name=f"{tag}-classical-before")
    cv.end_group()

    # ---- arrow
    _arrow(cv, ARROW_X, cy)

    # ---- AFTER panel
    cv.begin_group(data_op_side="after")
    _panel(cv, AFTER_X, y0 + PANEL_TOP, AFTER_W, PANEL_BOT - PANEL_TOP,
           name=f"{tag}-after")
    nA2_x = AFTER_X + 16
    nB2_x = AFTER_X + AFTER_W - 16 - 56
    _node(cv, nA2_x, cy - 24, 56, 48, name=f"{tag}-A2")
    _node(cv, nB2_x, cy - 24, 56, 48, name=f"{tag}-B2")
    qA2_x = nA2_x + 28
    qB2_x = nB2_x + 28
    _qubit(cv, qA2_x, cy, "comm", "C", name=f"{tag}-CA2")
    _qubit(cv, qB2_x, cy, "comm", "C", name=f"{tag}-CB2")
    # Classical channel + vertical stubs into both nodes.
    _class_line_with_stubs(cv, y0, nA2_x, nB2_x + 56,
                            stubs=[(nA2_x + 28, cy + 24),
                                   (nB2_x + 28, cy + 24)],
                            name=f"{tag}-classical-after")
    # Wavy bond from CA2 to CB2 — small arch, no obstacle to clear
    _bond_wave_arch(cv, qA2_x + QR, cy, qB2_x - QR, cy,
                    peak_dy=22, amp=4, cls="bond",
                    name=f"{tag}-bond")
    # Herald tick — sit above the bond's peak (~cy-22) with clearance, so
    # text and waveline don't crowd each other.
    cv.text((qA2_x + qB2_x) / 2, cy - 36, "✓ herald", cls="herald",
            font_size=11, anchor="middle", name=f"{tag}-herald")
    cv.end_group()
    cv.end_group()


def _row_hep(cv: Canvas, y0: float) -> None:
    # Fidelity labels use BBPSSW (Bennett et al. PRL 76, 722 (1996)):
    # one round on two Werner pairs of fidelity F yields F' = (F² + ε²) /
    # (F² + 2Fε + 5ε²) with ε = (1−F)/3. F=0.70 → F'≈0.7353 → 0.74 (2dp).
    title = ["Heralded", "Entanglement", "Purification", "(HEP)"]
    sub = ["two noisy pairs in,", "one cleaner pair out"]
    tag = "HEP"
    cv.begin_group(data_op_row="purification")
    _row_title(cv, y0, title, sub)

    cy = y0 + ROW_CENTRE_Y

    # BEFORE
    cv.begin_group(data_op_side="before")
    _panel(cv, BEFORE_X, y0 + PANEL_TOP, BEFORE_W, PANEL_BOT - PANEL_TOP,
           name=f"{tag}-before")
    nA_x = BEFORE_X + 16
    nB_x = BEFORE_X + BEFORE_W - 16 - 56
    _node(cv, nA_x, cy - 38, 56, 76, name=f"{tag}-A")
    _node(cv, nB_x, cy - 38, 56, 76, name=f"{tag}-B")
    # Two memory qubits per side, stacked
    # Pairs spaced ±22 from cy (centre-to-centre 44 px) — wider than
    # the original ±18 so the local CNOT decoration injected at runtime
    # (vertical line + control dot + target ⊕) has clear vertical room,
    # but still leaves a ~5 px margin to the node-box top/bottom edges.
    qA1 = (nA_x + 28, cy - 22)
    qA2 = (nA_x + 28, cy + 22)
    qB1 = (nB_x + 28, cy - 22)
    qB2 = (nB_x + 28, cy + 22)
    for (qx, qy), qname in [(qA1, "MA1"), (qA2, "MA2"), (qB1, "MB1"), (qB2, "MB2")]:
        _qubit(cv, qx, qy, "memory", "M", name=f"{tag}-{qname}")
    # Two parallel wavy bonds, both at noisy fidelity F = 0.70
    _bond_wave(cv, qA1[0] + QR, qB1[0] - QR, qA1[1],
               cls="bond", amp=4, half_wl=14, name=f"{tag}-pair1")
    _bond_wave(cv, qA2[0] + QR, qB2[0] - QR, qA2[1],
               cls="bond", amp=4, half_wl=14, name=f"{tag}-pair2")
    # Fidelity label between the two pairs
    cv.text((qA1[0] + qB1[0]) / 2, cy, "F = 0.70", cls="bond-lbl",
            font_size=10, anchor="middle", name=f"{tag}-F-before")
    # Classical channel + stubs into both (taller) nodes — bottom at cy+38.
    _class_line_with_stubs(cv, y0, nA_x, nB_x + 56,
                            stubs=[(nA_x + 28, cy + 38),
                                   (nB_x + 28, cy + 38)],
                            name=f"{tag}-classical-before")
    cv.end_group()

    _arrow(cv, ARROW_X, cy)

    # AFTER
    cv.begin_group(data_op_side="after")
    _panel(cv, AFTER_X, y0 + PANEL_TOP, AFTER_W, PANEL_BOT - PANEL_TOP,
           name=f"{tag}-after")
    nA2x = AFTER_X + 16
    nB2x = AFTER_X + AFTER_W - 16 - 56
    # AFTER nodes match BEFORE (76 tall) — same convention as row 4.
    _node(cv, nA2x, cy - 38, 56, 76, name=f"{tag}-A2")
    _node(cv, nB2x, cy - 38, 56, 76, name=f"{tag}-B2")
    qA = (nA2x + 28, cy)
    qB = (nB2x + 28, cy)
    _qubit(cv, *qA, role="memory", letter="M", name=f"{tag}-MA")
    _qubit(cv, *qB, role="memory", letter="M", name=f"{tag}-MB")
    _bond_wave(cv, qA[0] + QR, qB[0] - QR, cy,
               cls="bond--thick", amp=6, half_wl=14, name=f"{tag}-pair-out")
    cv.text((qA[0] + qB[0]) / 2, cy - 14, "F = 0.74", cls="bond-lbl",
            font_size=10, anchor="middle", name=f"{tag}-F-after")
    # Herald tick above the purified pair
    cv.text((qA[0] + qB[0]) / 2, cy - 30, "✓ herald", cls="herald",
            font_size=11, anchor="middle", name=f"{tag}-herald")
    _class_line_with_stubs(cv, y0, nA2x, nB2x + 56,
                            stubs=[(nA2x + 28, cy + 38),
                                   (nB2x + 28, cy + 38)],
                            name=f"{tag}-classical-after")
    cv.end_group()
    cv.end_group()


def _row_swapping(cv: Canvas, y0: float) -> None:
    title = "Swapping"
    cv.begin_group(data_op_row="swapping")
    _row_title(cv, y0, title, ["matter-side BSM at the repeater", "extends the reach"])

    cy = y0 + ROW_CENTRE_Y

    # BEFORE — three nodes, M qubits, the relay's two M qubits are about to be
    # measured in the Bell basis (meter glyph straddling them).
    cv.begin_group(data_op_side="before")
    _panel(cv, BEFORE_X, y0 + PANEL_TOP, BEFORE_W, PANEL_BOT - PANEL_TOP,
           name=f"{title}-before")
    nA_x = BEFORE_X + 14
    nR_x = BEFORE_X + BEFORE_W / 2 - 28
    nB_x = BEFORE_X + BEFORE_W - 14 - 56
    _node(cv, nA_x, cy - 24, 56, 48, name=f"{title}-A")
    _node(cv, nR_x, cy - 24, 56, 48, name=f"{title}-R")
    _node(cv, nB_x, cy - 24, 56, 48, name=f"{title}-B")
    qA = (nA_x + 28, cy)
    qRL = (nR_x + 14, cy)
    qRR = (nR_x + 42, cy)
    qB = (nB_x + 28, cy)
    # Bonds drawn BEFORE qubits so the M balls render on top and hide
    # the inner ~QR of each bond endpoint — gives a clean "ball sitting
    # on a wavy line" look rather than a wavy line writing INTO the
    # ball. Bond endpoints are at qubit centres for the same reason.
    # Thick — the swapping row consumes purified (HEP-output) pairs,
    # so the inputs and the output are all drawn at the post-HEP weight.
    _bond_wave(cv, qA[0], qRL[0], cy,
               cls="bond--thick", amp=5, half_wl=12, name=f"{title}-AR")
    _bond_wave(cv, qRR[0], qB[0], cy,
               cls="bond--thick", amp=5, half_wl=12, name=f"{title}-RB")
    # Raw end-to-end Bell pair created the instant the BSM fires (sub 2).
    # The MA / MB qubits ARE entangled at this point — but in one of four
    # random Bell states. The classical bit (travelling at sub 3) tells
    # Bob which one, so he can apply the Pauli correction. Drawn in
    # channel-grey to flag "entanglement present but pending classical
    # resolution"; replaced by the canonical photon-blue bond in the
    # AFTER panel at sub ≥ 4.
    _bond_wave_arch(cv, qA[0], cy, qB[0], cy,
                    peak_dy=36, amp=5, cls="bond--raw",
                    name=f"{title}-bond-raw")
    _qubit(cv, *qA, role="memory", letter="M", name=f"{title}-MA")
    _qubit(cv, *qRL, role="memory", letter="M", name=f"{title}-MRL")
    _qubit(cv, *qRR, role="memory", letter="M", name=f"{title}-MRR")
    _qubit(cv, *qB, role="memory", letter="M", name=f"{title}-MB")
    # Matter-side BSM meter on the relay. Sits BELOW the two M qubits it
    # consumes (cy + 26), close to the classical line, so the post-BSM
    # classical bit emerges naturally from the meter.
    _meter(cv, (qRL[0] + qRR[0]) / 2, cy + 26, size=36,
           name=f"{title}-bsm")
    # Classical channel + stubs into A, the relay R (at the BSM meter), and B.
    _class_line_with_stubs(cv, y0, nA_x, nB_x + 56,
                            stubs=[(nA_x + 28, cy + 24),
                                   (nR_x + 28, cy + 24),
                                   (nB_x + 28, cy + 24)],
                            name=f"{title}-classical-before")
    cv.end_group()

    _arrow(cv, ARROW_X, cy)

    # AFTER
    cv.begin_group(data_op_side="after")
    _panel(cv, AFTER_X, y0 + PANEL_TOP, AFTER_W, PANEL_BOT - PANEL_TOP,
           name=f"{title}-after")
    nA2 = AFTER_X + 14
    nR2 = AFTER_X + AFTER_W / 2 - 28
    nB2 = AFTER_X + AFTER_W - 14 - 56
    _node(cv, nA2, cy - 24, 56, 48, name=f"{title}-A2")
    _node(cv, nR2, cy - 24, 56, 48, name=f"{title}-R2")  # empty
    _node(cv, nB2, cy - 24, 56, 48, name=f"{title}-B2")
    qA2c = (nA2 + 28, cy)
    qB2c = (nB2 + 28, cy)
    # Bond drawn BEFORE qubits so the M balls layer on top (centre-to-
    # centre, ball hides the inner part of the wave). Thick — the
    # inputs were HEP-purified pairs and the BSM hands the same
    # high-fidelity weight forward to the extended A↔B pair.
    _bond_wave_arch(cv, qA2c[0], cy, qB2c[0], cy,
                    peak_dy=36, amp=5, cls="bond--thick",
                    name=f"{title}-bond")
    _qubit(cv, *qA2c, role="memory", letter="M", name=f"{title}-MA2")
    _qubit(cv, *qB2c, role="memory", letter="M", name=f"{title}-MB2")
    # Classical channel + stubs into A, the (now empty) relay R, and B.
    _class_line_with_stubs(cv, y0, nA2, nB2 + 56,
                            stubs=[(nA2 + 28, cy + 24),
                                   (nR2 + 28, cy + 24),
                                   (nB2 + 28, cy + 24)],
                            name=f"{title}-classical-after")
    cv.end_group()
    cv.end_group()


def _row_teleportation(cv: Canvas, y0: float) -> None:
    title = "Teleportation"
    cv.begin_group(data_op_row="teleportation")
    _row_title(cv, y0, title, ["consume an end-to-end pair;", "move the data qubit"])

    cy = y0 + ROW_CENTRE_Y

    # Same node footprint as swap + HEG (56 × 48) so the row reads as
    # part of the same family. D and ML sit SIDE-BY-SIDE inside N0 —
    # same recipe as swap's relay (qRL + qRR side-by-side) — instead of
    # being stacked vertically; the BSM straddles N0's bottom edge.
    node_h = 48
    node_w = 56
    node_top = cy - node_h / 2

    # BEFORE — four nodes in a chain. N0 holds Alice's D and ML; N3
    # holds Bob's MR. Intervening N1 / N2 are empty (just the
    # classical-channel relay path). Alice's BSM measures (D, ML)
    # jointly; the meter straddles N0's bottom edge.
    cv.begin_group(data_op_side="before")
    _panel(cv, BEFORE_X, y0 + PANEL_TOP, BEFORE_W, PANEL_BOT - PANEL_TOP,
           name=f"{title}-before")
    n_count = 4
    avail = BEFORE_W - 24
    gap = (avail - node_w * n_count) / (n_count - 1)
    nx = [BEFORE_X + 12 + i * (node_w + gap) for i in range(n_count)]
    for i, x in enumerate(nx):
        _node(cv, x, node_top, node_w, node_h, name=f"{title}-N{i}")
    # D on the LEFT of N0, ML on the RIGHT (closer to the bond exit
    # toward N3). MR centred in N3 — Bob's qubit stays in the same slot
    # across BEFORE / AFTER (it gets relabelled M → D by his Pauli
    # correction, not physically moved).
    qD   = (nx[0]  + 14, cy)
    qM_L = (nx[0]  + 42, cy)
    qM_R = (nx[-1] + 28, cy)
    # Bond drawn BEFORE qubits so the M balls layer on top of the wave
    # endpoints. Centre-to-centre endpoints — the inner ~QR of the wave
    # is hidden by the ball, giving a clean attachment. Thick weight,
    # matching swap/HEP-output convention for purified pairs.
    # No "raw" grey bond here: Alice's BSM measures (D, ML) — that
    # destroys the ML↔MR entanglement entirely. What's left at MR is a
    # Pauli-rotated copy of D's state, *not* a Bell pair. The "?" label
    # on MR (toggled at sub 2 by the JS) carries that meaning instead.
    _bond_wave_arch(cv, qM_L[0], qM_L[1],
                    qM_R[0], qM_R[1],
                    peak_dy=36, amp=5, cls="bond--thick",
                    name=f"{title}-bond")
    _qubit(cv, *qM_L, role="memory", letter="M", name=f"{title}-ML")
    _qubit(cv, *qM_R, role="memory", letter="M", name=f"{title}-MR")
    cv.circle(qD[0], qD[1], USER_QR, cls="data", name=f"{title}-D")
    cv.text(qD[0], qD[1], "D", cls="qbit-in", font_size=10, name=f"{title}-Din")
    # "?" overlay on MR: hidden by default, faded in by the JS at sub 2
    # when the BSM consumes (D, ML) and MR drops into a Pauli-rotated
    # but unknown state. The "M" label (`-MR-in`) fades out at the same
    # beat so only one of the two is visible at a time.
    cv.text(qM_R[0], qM_R[1], "?", cls="qbit-in", font_size=10,
            style="opacity:0", name=f"{title}-MR-q")
    # Matter-side BSM meter straddling N0's BOTTOM edge — same recipe as
    # the swapping-relay meter. Centred horizontally between D and ML
    # (the two qubits it consumes); same `cy + 26` straddle and `size=36`
    # as swap so the two BSMs read identically.
    _meter(cv, (qD[0] + qM_L[0]) / 2, cy + 26, size=36, name=f"{title}-bsm")
    # Classical channel + stubs into all four nodes in the chain.
    _class_line_with_stubs(cv, y0, nx[0], nx[-1] + node_w,
                            stubs=[(x + node_w / 2, node_top + node_h) for x in nx],
                            name=f"{title}-classical-before")
    cv.end_group()

    _arrow(cv, ARROW_X, cy)

    # AFTER — same node chain, all matter qubits + bond consumed; data qubit
    # now sits at N3. Classical line stays (the 2 result bits travelled along
    # it from Alice → Bob during the operation).
    cv.begin_group(data_op_side="after")
    _panel(cv, AFTER_X, y0 + PANEL_TOP, AFTER_W, PANEL_BOT - PANEL_TOP,
           name=f"{title}-after")
    avail2 = AFTER_W - 24
    gap2 = (avail2 - node_w * n_count) / (n_count - 1)
    nx2 = [AFTER_X + 12 + i * (node_w + gap2) for i in range(n_count)]
    for i, x in enumerate(nx2):
        _node(cv, x, node_top, node_w, node_h, name=f"{title}-N{i}-after")
    # Data qubit appears at the far-right node, centred — the physical
    # qubit that was MR in BEFORE has been "converted" into D by Bob's
    # Pauli correction. Same position as MR so the reader sees the
    # qubit stay put across the operation.
    dx2 = nx2[-1] + node_w / 2
    dy2 = cy
    cv.circle(dx2, dy2, USER_QR, cls="data", name=f"{title}-D-after")
    cv.text(dx2, dy2, "D", cls="qbit-in", font_size=10, name=f"{title}-Din-after")
    # Classical channel + stubs into all four nodes in the chain.
    _class_line_with_stubs(cv, y0, nx2[0], nx2[-1] + node_w,
                            stubs=[(x + node_w / 2, node_top + node_h) for x in nx2],
                            name=f"{title}-classical-after")
    cv.end_group()
    cv.end_group()


# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------


def _legend(cv: Canvas, y0: float) -> None:
    """Bottom legend strip — names every glyph used in the figure.

    Items are arranged across two rows so each label has breathing room.
    Top row: qubit-role glyphs + photon. Bottom row: bonds + BSM glyphs +
    classical channel.
    """
    cv.line(TITLE_X, y0, W - TITLE_X, y0,
            cls="panel", name="legend-rule")
    rows: list[list[tuple[str, str]]] = [
        # Top row — qubit roles + photon
        [
            ("memory", "memory qubit"),
            ("comm",   "comm qubit"),
            ("data",   "data qubit"),
            ("photon", "photon"),
        ],
        # Bottom row — bonds, BSMs, and the two channel types. Only HEG
        # has a live quantum channel (photons in flight to the BSA); the
        # other rows are local matter operations and use the classical
        # channel only.
        [
            ("bond",      "entanglement"),
            ("bsa",       "photonic BSM (BSA)"),
            ("meter",     "matter-side BSM"),
            ("fibre",     "quantum channel"),
            ("classical", "classical channel"),
        ],
    ]
    row_dy = 22
    for r_i, items in enumerate(rows):
        row_y = y0 + 18 + r_i * row_dy
        slot_w = (W - 2 * TITLE_X) / len(items)
        for i, (kind, label) in enumerate(items):
            slot_cx = TITLE_X + slot_w * i + slot_w / 2
            # Centre each "icon + label" pair on the slot centre rather
            # than left-anchoring it. Label width estimated from the
            # legend font (0.55 × font_size per char). icon-to-text
            # offset is 22 px; icon glyph half-width ≈ 10 px.
            label_w = 0.55 * 10.5 * len(label)
            pair_w = 22 + label_w
            icon_x = slot_cx - pair_w / 2 + 10
            text_x = icon_x + 22
            if kind in ("data", "comm", "memory", "user"):
                letter = {"data": "D", "comm": "C", "memory": "M",
                          "user": "U"}[kind]
                cv.circle(icon_x, row_y, 9, cls=kind, name=f"legend-{kind}")
                cv.text(icon_x, row_y, letter, cls="qbit-in",
                        font_size=9, name=f"legend-{kind}-in")
            elif kind == "photon":
                cv.add(
                    f'<circle cx="{icon_x}" cy="{row_y}" r="9" '
                    f'fill="url(#ops-cloud)"/>',
                    kind="shape", name="legend-photon",
                )
            elif kind == "bond":
                _bond_wave(cv, icon_x - 10, icon_x + 10, row_y,
                           cls="bond", amp=3, half_wl=7, name="legend-bond")
            elif kind == "bsa":
                _bsa(cv, icon_x, row_y, size=22, name="legend-bsa")
            elif kind == "meter":
                _meter(cv, icon_x, row_y, size=22, name="legend-meter")
            elif kind == "fibre":
                cv.line(icon_x - 10, row_y, icon_x + 10, row_y,
                        cls="fibre", name="legend-fibre")
            elif kind == "classical":
                cv.line(icon_x - 10, row_y, icon_x + 10, row_y,
                        cls="classical", name="legend-classical")
            cv.text(text_x, row_y, label, cls="legend-txt",
                    font_size=10.5, anchor="start",
                    name=f"legend-txt-{kind}")


# ---------------------------------------------------------------------------
# Figure assembly
# ---------------------------------------------------------------------------


def _extra_defs() -> list[str]:
    # Shared radial gradient for photon glyphs (same recipe as #ops-photon-cloud
    # in entanglement.astro). Colour stops use the photon stroke colour from
    # 4hop-topology so the cloud reads as the same resource family.
    blue = "#2f6fd6"
    return [
        '<radialGradient id="ops-cloud">'
        f'<stop offset="0%"   stop-color="{blue}" stop-opacity="1"/>'
        f'<stop offset="35%"  stop-color="{blue}" stop-opacity="0.92"/>'
        f'<stop offset="70%"  stop-color="{blue}" stop-opacity="0.45"/>'
        f'<stop offset="100%" stop-color="{blue}" stop-opacity="0"/>'
        '</radialGradient>'
    ]


def build() -> Canvas:
    cv = Canvas(
        width=W, height=H,
        title=("Four basic operations on Bell pairs — HEG, HEP, "
               "swapping, teleportation."),
        css=CSS,
    )
    Q.register(cv, "quisp-bsa-white", "bsm-meter")
    for d in _extra_defs():
        cv.add_def(d)

    # The "Inspired by Aliro" credit lives in the surrounding HTML
    # toolbar (AnimatedOpsPrimitives.astro), not inside the SVG —
    # this saves a row of vertical space at the top of the figure.

    # Rows
    rows = [
        lambda y: _row_heg(cv, y),
        lambda y: _row_hep(cv, y),
        lambda y: _row_swapping(cv, y),
        lambda y: _row_teleportation(cv, y),
    ]
    for i, fn in enumerate(rows):
        fn(TOP_PAD + i * ROW_H)

    # Legend
    _legend(cv, TOP_PAD + N_ROWS * ROW_H + 8)
    return cv


def main(out: Path | None = None) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = out or (repo_root / "images" / "ops-primitives.svg")
    cv = build()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(cv.to_svg())
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
