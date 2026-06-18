"""Generate the three entanglement-distribution architecture figures.

After Jones et al., New J. Phys. 18 083015 (2016) — three single-link
architectures: MeetInTheMiddle (MM), SenderReceiver (SR), MidpointSource
(MS). Each figure is a single SVG drawn from the same visual vocabulary
as `topology_4hop.py` (green comm-qubit `C`, purple memory `M`, telecom
fibre stroke, QuISP BSA glyph, magenta entanglement sinusoid).

Run from the repo root::

    python -m scripts.diagrams.distribution_architectures
"""

from __future__ import annotations

from pathlib import Path

from .svglib import Canvas
from . import quisp_icons as Q
from . import components as C


# ---------------------------------------------------------------------------
# LAYOUT — shared anchors used by all three figures.
# ---------------------------------------------------------------------------

W, H = 720, 280

# Endpoint x-positions (Alice on the left, Bob on the right). The figure is
# symmetric about cx = W/2.
A_CX = 110
B_CX = W - 110
MID_X = W / 2

# Vertical anchors
Y_TITLE = 28          # "MeetInTheMiddle (MM)" — figure title
Y_NAME = 50           # "Alice" / "Bob" node names
Y_M = 100             # purple memory qubit row
Y_C = 140             # green comm qubit row (also the photonic axis)
Y_AXIS = Y_C          # fibre runs along the comm-qubit row
Y_ENT = 210           # magenta entanglement wavy line, after the herald
Y_HOP = 242           # hop bracket strip
Y_CAPTION = 268       # one-line caption inside the SVG

BSM_SIZE = 28
EPPS_SIZE = 32

# Endpoint-card box (a thin rounded rect that groups M, C and the node name).
CARD_W = 90
CARD_TOP = 64
CARD_BOT = 170

# Qubit radii (match the 4-hop figure's `qr_node` and `qubit_column`).
R_QBIT = 11
R_PHOTON_BIG = 6
R_PHOTON_SMALL = 4


# ---------------------------------------------------------------------------
# STYLES — kept in sync with topology_4hop.py so the figures read as one
# family. Anything not used here is stripped to keep the SVGs small.
# ---------------------------------------------------------------------------

CSS = """
  .endpoint-card { fill: #f6f8fc; stroke: #aab0ba; stroke-width: 1.1; }
  .qfc-blk    { fill: #e2eef9; stroke: #5a83b3; stroke-width: 1.3; }

  .comm       { fill: #22c55e; stroke: #15803d; stroke-width: 1; }
  .memory     { fill: #9b87c4; stroke: #6048a3; stroke-width: 1; }
  .photon     { fill: #2f6fd6; stroke: #1a4a99; stroke-width: 0.8; }

  .fig-title  { font: 700 14px sans-serif; fill: #1a1f2a; text-anchor: middle; }
  .node-ttl   { font: 700 12px sans-serif; fill: #1a1f2a; text-anchor: middle; }
  .node-sub   { font: 9.5px sans-serif; fill: #4a4f57; text-anchor: middle; }
  .lbl        { font: 600 11px sans-serif; fill: #1a1f2a; text-anchor: middle; }
  .mini       { font: 8.5px sans-serif; fill: #5a6472; text-anchor: middle; }
  .qbit-in    { font: 700 9px sans-serif; fill: #ffffff; text-anchor: middle; dominant-baseline: middle; }
  .qbit-side  { font: 600 9px sans-serif; fill: #1a1f2a; }
  .hop        { font: 700 10px sans-serif; fill: #1a3458; text-anchor: middle; }
  .midline    { stroke: #aab0ba; stroke-width: 1; fill: none; stroke-dasharray: 3 2; }
  .caption    { font: 600 10px sans-serif; fill: #4a4f57; text-anchor: middle; }

  .fiber--quantum  { stroke: #2f6fd6; stroke-width: 1.6; fill: none; stroke-linecap: round; opacity: 0.55; }
  .fiber--classical{ stroke: #6a7280; stroke-width: 1.2; fill: none; stroke-linecap: round; stroke-dasharray: 4 3; opacity: 0.7; }

  .entanglement    { stroke: #c84a9b; stroke-width: 1.6; fill: none; stroke-linecap: round; }
  .entanglement-lbl{ font: 600 9px sans-serif; fill: #c84a9b; text-anchor: middle; }

  .epps-box   { fill: #e2eef9; stroke: #2f6fd6; stroke-width: 1.4; }
  .epps-ttl   { font: 700 10px sans-serif; fill: #1a3458; text-anchor: middle; }
"""


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------


def _endpoint_card(cv: Canvas, cx: float, name: str, sub: str = "") -> None:
    """Box around Alice/Bob with name + (M, C) qubit stack inside.

    Layout (top→bottom):
        ┌─────────┐
        │  Alice  │
        │ memory  │ ← optional subtitle
        │   (M)   │ ← purple memory qubit at Y_M
        │   (C)   │ ← green comm qubit at Y_C (sits on the photonic axis)
        └─────────┘
    """
    cv.rect(
        cx - CARD_W / 2, CARD_TOP, CARD_W, CARD_BOT - CARD_TOP,
        cls="endpoint-card", rx=6, name=f"{name}-card",
    )
    cv.text(cx, Y_NAME + 28, name, cls="node-ttl", font_size=12, name=f"{name}-ttl")
    if sub:
        # Role tag sits ABOVE the card so it never collides with the M qubit.
        cv.text(cx, CARD_TOP - 5, f"({sub})", cls="node-sub",
                font_size=9.5, name=f"{name}-sub")
    # Memory qubit (purple, "M")
    cv.circle(cx, Y_M, R_QBIT, cls="memory", name=f"{name}-M")
    cv.text(cx, Y_M, "M", cls="qbit-in", font_size=9, name=f"{name}-M-in")
    # Comm qubit (green, "C") — on the photonic axis
    cv.circle(cx, Y_C, R_QBIT, cls="comm", name=f"{name}-C")
    cv.text(cx, Y_C, "C", cls="qbit-in", font_size=9, name=f"{name}-C-in")


def _hop_bracket(cv: Canvas, x0: float, x1: float, label: str) -> None:
    """One-segment hop bracket with end ticks. Matches the 4-hop figure."""
    tick_h = 4
    cv.line(x0, Y_HOP, x1, Y_HOP, cls="midline", name=f"hop-line-{label}")
    cv.line(x0, Y_HOP - tick_h, x0, Y_HOP + tick_h,
            style="stroke:#aab0ba;stroke-width:1", name=f"hop-tick-L-{label}")
    cv.line(x1, Y_HOP - tick_h, x1, Y_HOP + tick_h,
            style="stroke:#aab0ba;stroke-width:1", name=f"hop-tick-R-{label}")
    cv.text((x0 + x1) / 2, Y_HOP + 14, label,
            cls="hop", font_size=10, anchor="middle", name=f"hop-lbl-{label}")


def _entanglement_wave(cv: Canvas, x0: float, x1: float, y: float, name: str) -> None:
    """Magenta sinusoid between A.C and B.C — the delivered Bell pair."""
    half_wl = 10
    amp = 4
    n_half = int((x1 - x0) / half_wl)
    if n_half < 2:
        return
    span = n_half * half_wl
    pad = (x1 - x0 - span) / 2
    sx = x0 + pad
    parts = [f"M {sx} {y} q {half_wl/2} {-amp} {half_wl} 0"]
    parts.extend("t {} 0".format(half_wl) for _ in range(n_half - 1))
    cv.line(x0, y, sx, y, cls="entanglement", name=f"{name}-in")
    cv.add(f'<path d="{" ".join(parts)}" class="entanglement"/>', kind="path", name=name)
    cv.line(sx + span, y, x1, y, cls="entanglement", name=f"{name}-out")


def _photon(cv: Canvas, cx: float, cy: float, name: str, r: float = R_PHOTON_BIG) -> None:
    cv.circle(cx, cy, r, cls="photon", name=name)


def _caption(cv: Canvas, text: str) -> None:
    cv.text(W / 2, Y_CAPTION, text, cls="caption", font_size=10, anchor="middle", name="caption")


def _figure_title(cv: Canvas, text: str) -> None:
    cv.text(W / 2, Y_TITLE, text, cls="fig-title", font_size=14, anchor="middle", name="title")


# ---------------------------------------------------------------------------
# Figure 1 — MeetInTheMiddle (MM)
# ---------------------------------------------------------------------------


def build_mm() -> Canvas:
    cv = Canvas(
        width=W, height=H,
        title="MeetInTheMiddle (MM) — both endpoints emit photons toward a midpoint Bell-state analyser.",
        css=CSS,
    )
    cv.add(
        '<desc>MeetInTheMiddle entanglement-distribution architecture after Jones et al. '
        'NJP 18 083015 (2016). Alice and Bob each hold a comm qubit (C, green) and a memory '
        'qubit (M, purple). Each endpoint emits a photon entangled with its own C; the two '
        'photons each travel L/2 along telecom fibre to a midpoint Bell-state analyser (QuISP '
        'BSA glyph). A coincidence click heralds an entangled Bell pair between the two '
        'comm qubits (magenta sinusoid). Classical heralding signal is sent back to both '
        'endpoints (dashed grey).</desc>',
        kind="shape", name="desc-mm",
    )
    Q.register(cv, "quisp-bsa-white")

    _figure_title(cv, "MeetInTheMiddle (MM)")

    _endpoint_card(cv, A_CX, "Alice")
    _endpoint_card(cv, B_CX, "Bob")

    # Two fibre segments: A.C → BSM (L/2) and BSM → B.C (L/2)
    cv.line(A_CX + R_QBIT, Y_AXIS, MID_X - BSM_SIZE / 2, Y_AXIS,
            cls="fiber--quantum", name="fibre-A-mid")
    cv.line(MID_X + BSM_SIZE / 2, Y_AXIS, B_CX - R_QBIT, Y_AXIS,
            cls="fiber--quantum", name="fibre-mid-B")

    # Photons in flight — one from each side, mid-flight, headed toward the BSM
    _photon(cv, A_CX + 55, Y_AXIS, "photon-A")
    _photon(cv, B_CX - 55, Y_AXIS, "photon-B")

    # Midpoint BSA (QuISP BSA glyph) sits on the axis
    C.midpoint_bsm(cv, MID_X, Y_AXIS, size=BSM_SIZE, label="BSA", label_pos="above")

    # Hop brackets — both halves labelled "L/2" to make the symmetry explicit
    _hop_bracket(cv, A_CX, MID_X, "L/2")
    _hop_bracket(cv, MID_X, B_CX, "L/2")

    # Classical heralding return — dashed grey, well above the axis so the
    # arc clears the BSM glyph and its "BSM" label.
    _classical_return(cv, MID_X, A_CX, B_CX, y_offset=-38)

    # Magenta entanglement wave between A.C and B.C (after the herald)
    _entanglement_wave(cv, A_CX + R_QBIT, B_CX - R_QBIT, Y_ENT, "ent-mm")
    cv.text(MID_X, Y_ENT - 8, "heralded Bell pair", cls="entanglement-lbl",
            font_size=9, anchor="middle", name="ent-lbl")

    _caption(cv, "Two photons, two half-link transmissions, two-photon interference at the midpoint.")
    return cv


def _classical_return(cv: Canvas, mid_x: float, a_cx: float, b_cx: float,
                      y_offset: float = -14) -> None:
    """Dashed grey arc from the BSM back to both endpoints. The BSA fires
    locally; both endpoints must learn the heralding bit by classical
    channel before they can use the entanglement. Drawn as two short
    angled segments above the photonic axis."""
    y_top = Y_AXIS + y_offset
    # left arm
    cv.add(
        f'<path d="M {mid_x} {Y_AXIS - BSM_SIZE/2} '
        f'C {mid_x - 30} {y_top}, {a_cx + 30} {y_top}, {a_cx} {Y_AXIS - 3}" '
        f'class="fiber--classical"/>',
        kind="path", name="classical-L",
    )
    cv.add(
        f'<path d="M {mid_x} {Y_AXIS - BSM_SIZE/2} '
        f'C {mid_x + 30} {y_top}, {b_cx - 30} {y_top}, {b_cx} {Y_AXIS - 3}" '
        f'class="fiber--classical"/>',
        kind="path", name="classical-R",
    )
    cv.text(mid_x, y_top - 4, "classical herald", cls="mini",
            font_size=8.5, anchor="middle", name="classical-lbl")


# ---------------------------------------------------------------------------
# Figure 2 — SenderReceiver (SR)
# ---------------------------------------------------------------------------


def build_sr() -> Canvas:
    cv = Canvas(
        width=W, height=H,
        title="SenderReceiver (SR) — sender's photon traverses the full link; receiver runs the analyser locally.",
        css=CSS,
    )
    cv.add(
        '<desc>SenderReceiver entanglement-distribution architecture after Jones et al. '
        'NJP 18 083015 (2016). Alice (sender) emits a photon entangled with her comm qubit '
        '(C, green) and sends it across the full link. Bob (receiver) holds his own comm '
        'qubit plus the Bell-state analyser; he performs a BSM between Alice\'s incoming '
        'photon and his local C. A successful BSM heralds an entangled pair between A.C '
        'and B.C (magenta sinusoid). Only one photon crosses the link; no two-photon '
        'interference at distance.</desc>',
        kind="shape", name="desc-sr",
    )
    Q.register(cv, "quisp-bsa-white")

    _figure_title(cv, "SenderReceiver (SR)")

    _endpoint_card(cv, A_CX, "Alice", sub="sender")
    _endpoint_card(cv, B_CX, "Bob", sub="receiver")

    # BSM sits just OUTSIDE Bob's card on the link side — visually unambiguous
    # that it is Bob's local analyser (short stub into his C) but big enough
    # to render cleanly without overlapping the card border.
    bob_card_left = B_CX - CARD_W / 2
    bsm_x = bob_card_left - 6 - BSM_SIZE / 2

    # Single quantum-fibre run from A.C across the full link to Bob's BSM
    cv.line(A_CX + R_QBIT, Y_AXIS, bsm_x - BSM_SIZE / 2, Y_AXIS,
            cls="fiber--quantum", name="fibre-A-B")

    # One photon in flight, midway along the link
    _photon(cv, (A_CX + bsm_x) / 2, Y_AXIS, "photon-A")

    # Local BSA glyph at Bob
    C.midpoint_bsm(cv, bsm_x, Y_AXIS, size=BSM_SIZE, label="BSA", label_pos="above")

    # Short stub from BSA into Bob's C — local link, drawn as a thick blue
    # butt-cap segment (same convention as the QR internal stubs in 4hop).
    cv.line(bsm_x + BSM_SIZE / 2, Y_AXIS, B_CX - R_QBIT, Y_AXIS,
            style="stroke:#2f6fd6;stroke-width:1.8;fill:none;stroke-linecap:butt",
            name="fibre-bsm-local")

    # Bob's own photon — emitted from his C, on the local stub, heading INTO
    # the BSA where it interferes with Alice's incoming photon. Without it
    # there is nothing for the BSA to measure against.
    _photon(cv, (bsm_x + BSM_SIZE / 2 + B_CX - R_QBIT) / 2, Y_AXIS, "photon-B")

    # One full-link hop bracket
    _hop_bracket(cv, A_CX, B_CX, "L (full link)")

    # Magenta entanglement wave between A.C and B.C after the herald
    _entanglement_wave(cv, A_CX + R_QBIT, B_CX - R_QBIT, Y_ENT, "ent-sr")
    cv.text(MID_X, Y_ENT - 8, "heralded Bell pair", cls="entanglement-lbl",
            font_size=9, anchor="middle", name="ent-lbl")

    _caption(cv, "One photon traverses the link; the BSA is local at the receiver.")
    return cv


# ---------------------------------------------------------------------------
# Figure 3 — MidpointSource (MS)
# ---------------------------------------------------------------------------


def build_ms() -> Canvas:
    cv = Canvas(
        width=W, height=H,
        title="MidpointSource (MS) — entangled-pair source at the link midpoint emits one photon toward each endpoint, which runs a local BSM with its memory.",
        css=CSS,
    )
    cv.add(
        '<desc>MidpointSource entanglement-distribution architecture after Jones et al. '
        'NJP 18 083015 (2016). An entangled-photon-pair source (EPPS, typically SPDC) sits '
        'at the link midpoint. The source emits two entangled photons outward; each travels '
        'L/2 to one of the endpoints. At each endpoint, a local Bell-state analyser '
        'interferes the arriving photon with a photon entangled with the local comm qubit '
        '(C, green). When both endpoint BSMs herald successfully, the two comm qubits are '
        'entangled (magenta sinusoid). The source-side herald is independent of link loss; '
        'no two-photon interference at distance.</desc>',
        kind="shape", name="desc-ms",
    )
    Q.register(cv, "quisp-bsa-white", "quisp-epps")

    _figure_title(cv, "MidpointSource (MS)")

    _endpoint_card(cv, A_CX, "Alice")
    _endpoint_card(cv, B_CX, "Bob")

    # Endpoint BSMs sit just OUTSIDE each card, on the photonic axis. The
    # arriving photon interferes there with a photon from the local C qubit.
    alice_card_right = A_CX + CARD_W / 2
    bob_card_left = B_CX - CARD_W / 2
    bsm_a_x = alice_card_right + 6 + BSM_SIZE / 2
    bsm_b_x = bob_card_left - 6 - BSM_SIZE / 2

    # EPPS midpoint box — small light-blue rect with the QuISP EPPS glyph
    # inside. Draw the rect first so the icon sits on top, and add the
    # text label below.
    epps_x = MID_X
    epps_y = Y_AXIS
    cv.rect(
        epps_x - EPPS_SIZE / 2, epps_y - EPPS_SIZE / 2,
        EPPS_SIZE, EPPS_SIZE,
        cls="epps-box", rx=4, name="epps-box",
    )
    # Use the QuISP EPPS icon at slightly smaller size, centred inside the box.
    cv.use("#quisp-epps",
           epps_x - EPPS_SIZE / 2 + 3, epps_y - EPPS_SIZE / 2 + 3,
           EPPS_SIZE - 6, EPPS_SIZE - 6,
           name="epps-icon")
    cv.text(epps_x, epps_y - EPPS_SIZE / 2 - 16, "EPPS",
            cls="epps-ttl", font_size=10, anchor="middle", name="epps-ttl")
    cv.text(epps_x, epps_y - EPPS_SIZE / 2 - 5, "midpoint pair source",
            cls="mini", font_size=8.5, anchor="middle", name="epps-sub")

    # Two fibre segments: EPPS → A.BSM and EPPS → B.BSM, each ~L/2
    cv.line(epps_x - EPPS_SIZE / 2, Y_AXIS, bsm_a_x + BSM_SIZE / 2, Y_AXIS,
            cls="fiber--quantum", name="fibre-mid-A")
    cv.line(epps_x + EPPS_SIZE / 2, Y_AXIS, bsm_b_x - BSM_SIZE / 2, Y_AXIS,
            cls="fiber--quantum", name="fibre-mid-B")

    # Two photons in flight — one moving LEFT toward Alice, one moving
    # RIGHT toward Bob. Place them roughly midway along each half.
    _photon(cv, (epps_x - EPPS_SIZE / 2 + bsm_a_x + BSM_SIZE / 2) / 2, Y_AXIS, "photon-L")
    _photon(cv, (epps_x + EPPS_SIZE / 2 + bsm_b_x - BSM_SIZE / 2) / 2, Y_AXIS, "photon-R")

    # Endpoint BSAs (local, one per side)
    C.midpoint_bsm(cv, bsm_a_x, Y_AXIS, size=BSM_SIZE, label="BSA", label_pos="above")
    C.midpoint_bsm(cv, bsm_b_x, Y_AXIS, size=BSM_SIZE, label="BSA", label_pos="above")

    # Short local stubs from each BSA to its endpoint C
    cv.line(bsm_a_x - BSM_SIZE / 2, Y_AXIS, A_CX + R_QBIT, Y_AXIS,
            style="stroke:#2f6fd6;stroke-width:1.8;fill:none;stroke-linecap:butt",
            name="stub-A")
    cv.line(bsm_b_x + BSM_SIZE / 2, Y_AXIS, B_CX - R_QBIT, Y_AXIS,
            style="stroke:#2f6fd6;stroke-width:1.8;fill:none;stroke-linecap:butt",
            name="stub-B")

    # Local photons emitted from each endpoint C, heading INTO the local BSA
    # to interfere with the arriving EPPS photon. Two photons per BSA — one
    # from EPPS (drawn above) and one from local C (drawn here).
    _photon(cv, (bsm_a_x - BSM_SIZE / 2 + A_CX + R_QBIT) / 2, Y_AXIS, "photon-A-local")
    _photon(cv, (bsm_b_x + BSM_SIZE / 2 + B_CX - R_QBIT) / 2, Y_AXIS, "photon-B-local")

    # Hop brackets — two half-link segments
    _hop_bracket(cv, A_CX, MID_X, "L/2")
    _hop_bracket(cv, MID_X, B_CX, "L/2")

    # Magenta entanglement wave between A.C and B.C after both heralds fire
    _entanglement_wave(cv, A_CX + R_QBIT, B_CX - R_QBIT, Y_ENT, "ent-ms")
    cv.text(MID_X, Y_ENT - 8, "heralded Bell pair",
            cls="entanglement-lbl", font_size=9, anchor="middle", name="ent-lbl")

    _caption(cv, "Source at the midpoint emits a pair outward; each endpoint runs a local BSA.")
    return cv


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


FIGURES = [
    ("distribution-mm.svg", build_mm),
    ("distribution-sr.svg", build_sr),
    ("distribution-ms.svg", build_ms),
]


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    images_dir = repo_root / "images"
    web_dir = repo_root / "web" / "public" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    for fname, builder in FIGURES:
        cv = builder()
        svg = cv.to_svg()
        out = images_dir / fname
        out.write_text(svg)
        print(f"wrote {out}")
        if web_dir.exists():
            (web_dir / fname).write_text(svg)
            print(f"wrote {web_dir / fname}")
        overlaps = cv.check_text_overlaps(pad=0.5)
        if overlaps:
            print(f"  WARN: {len(overlaps)} text overlaps in {fname}:")
            for a, b in overlaps[:8]:
                print(f"    - {a.name!r} ↔ {b.name!r}")


if __name__ == "__main__":
    main()
