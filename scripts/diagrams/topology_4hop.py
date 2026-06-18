"""Generate images/4hop-topology.svg.

Run from the repo root::

    python -m scripts.diagrams.topology_4hop

Layout: one source of truth for every named coordinate. Editing a constant
here propagates everywhere — M_n midpoints, 50 km labels, hop brackets, and
elbow path endpoints all derive from the QR centres.
"""

from __future__ import annotations

from pathlib import Path

from .svglib import Canvas, render_png
from . import quisp_icons as Q
from . import components as C


# ---------------------------------------------------------------------------
# LAYOUT — every figure-wide anchor lives here.
# ---------------------------------------------------------------------------

# Overall canvas
W, H = 1000, 580

# Node A (dilution fridge): column x, vessel extent
NODE_A_CX = 80
NODE_A_TOP = 20
NODE_A_BOT = 290
CHAND_TOP_W = 140
CHAND_BOT_W = 110

# Node B (UHV trap + room-temp QFC bench)
NODE_B_CX = 920
NODE_B_OUTLINE_TOP = 12
NODE_B_OUTLINE_BOT = 294
CHAMBER_TOP = 58
CHAMBER_BOT = 196
CHAMBER_W = 100

# Qubit column geometry (shared y-positions in both nodes)
Y_DQ = 78  # nudged up from 88 to give more room between DQ and MQ
Y_MQ = 118
Y_CQ = 165
Y_PHOTON_NEAR_CQ = 184
Y_FIBER_LINK_FROM = 176  # CQ bottom edge
Y_TRANSDUCER_TOP = 229  # centres the 55-tall block in the chandelier bottom
Y_TRANSDUCER_BOT = 284  # box (between last narrowing ~y=222 and base y=290)
TRANSDUCER_W = 80
TRANSDUCER_H = 55

# Horizontal photonic axis
AXIS_Y = 430

# Repeater positions. With the L-shape elbow adding ~177 px of non-horizontal
# distance to hops 1 and 4, the QR centres are chosen so all four hops have
# the same visual path length (~300 px).
QR_CENTRES = (200, 500, 800)
QR_WIDTH = 140
QBIT_GAP = 22  # spacing between L/C/R centres in each QR
# Outer face of the QFC block, measured from the QR centre. Inside qr_node the
# QFC rect sits at l_x - 39 = cx - QBIT_GAP - 39 = cx - 61. So a fibre that
# wants to *touch* the QFC's outer face should terminate at cx ± QR_QFC_FACE.
QR_QFC_FACE = QBIT_GAP + 39  # = 61

# M1/M4 sit at the visual midpoint between each node's fibre exit and the axis
Y_M1_M4 = 360

# Matter-photon interface — y where the conceptual line between the matter
# qubits (DQ, MQ, repeater memory C) and the photonic / network subsystem
# (CQ, transducers, photonic axis, repeater comm L/R, BSMs) sits. Midway
# between MQ (y=118) and CQ (y=165). Above this line: long-lived matter
# qubits holding compute state and stored entanglement. Below: the
# short-coherence photon-facing layer that gets reset every entanglement
# attempt, plus everything optical. NOT to be confused with an LOCC
# boundary — LOCC is a protocol class, not a spatial region. See the LOCC
# callout on /entanglement for that distinction.
INTERFACE_Y = 142

# Hop bracket strip
HOP_BRACKET_Y = 498

# Legend
LEGEND_Y = 550


# ---------------------------------------------------------------------------
# STYLES — single CSS block referenced by every component.
# ---------------------------------------------------------------------------

CSS = """
  .vessel-A   { fill: #fff8ef; stroke: #b8783c; stroke-width: 1.4; }
  .vessel-B   { fill: #f3f8fd; stroke: #5a83b3; stroke-width: 1.4; }
  .nodeB-bdy  { fill: none; stroke: #5a83b3; stroke-width: 1.1; stroke-dasharray: 5 3; opacity: 0.7; }
  .repeater   { fill: #ecfaf2; stroke: #2f8a55; stroke-width: 1.4; }
  .m2o-blk    { fill: #fdeacf; stroke: #b8783c; stroke-width: 1.3; }
  .qfc-blk    { fill: #e2eef9; stroke: #5a83b3; stroke-width: 1.3; }
  .viewport   { fill: #f3f8fd; stroke: #5a83b3; stroke-width: 1.2; }
  .cold-zone  { fill: #d6e8f6; fill-opacity: 0.55; stroke: #2c5d8f; stroke-width: 1.0; stroke-dasharray: 4 2; }
  .cold-tag   { font: 700 7.5px sans-serif; fill: #2c5d8f; text-anchor: middle; }
  .t2-tag     { font: italic 7.5px sans-serif; fill: #5a6472; }
  .plate      { stroke: #b8783c; stroke-width: 0.7; opacity: 0.55; }

  .data       { fill: #f29453; stroke: #8a3f0e; stroke-width: 1; }
  .comm       { fill: #22c55e; stroke: #15803d; stroke-width: 1; }
  .memory     { fill: #9b87c4; stroke: #6048a3; stroke-width: 1; }
  .photon     { fill: #2f6fd6; stroke: #1a4a99; stroke-width: 0.8; }

  .node-ttl   { font: 700 13px sans-serif; fill: #1a1f2a; text-anchor: middle; }
  .node-sub   { font: 9.5px sans-serif; fill: #4a4f57; text-anchor: middle; }
  .lbl        { font: 600 11px sans-serif; fill: #1a1f2a; text-anchor: middle; }
  .blk-ttl    { font: 700 10px sans-serif; fill: #1a1f2a; text-anchor: middle; }
  .blk-line   { font: 8px sans-serif; fill: #3a4150; text-anchor: middle; }
  .plate-tag  { font: 7.5px sans-serif; fill: #8a5a30; text-anchor: start; opacity: 0.9; }
  .mini       { font: 8.5px sans-serif; fill: #5a6472; text-anchor: middle; }
  .qbit-in    { font: 700 9px sans-serif; fill: #ffffff; text-anchor: middle; dominant-baseline: middle; }
  .qbit-side  { font: 600 9px sans-serif; fill: #1a1f2a; }
  .km         { font: 600 9px sans-serif; fill: #5a6472; text-anchor: middle; }
  .hop        { font: 700 10.5px sans-serif; fill: #1a3458; text-anchor: middle; }
  .midline    { stroke: #aab0ba; stroke-width: 1; fill: none; stroke-dasharray: 3 2; }
  .swap-link  { stroke: #9b87c4; stroke-width: 1.2; fill: none; stroke-dasharray: 3 2; }

  .plane-matter    { fill: #f7f4fb; }
  .plane-photonic  { fill: #eff5fc; }
  .interface-line  { stroke: #6a7280; stroke-width: 0.9; fill: none; stroke-dasharray: 4 3; opacity: 0.55; }
  .plane-tag       { font: 700 9px sans-serif; fill: #6a7280; opacity: 0.75; }

  .fiber           { stroke: #5a6472; stroke-width: 1.4; fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .fiber--quantum  { stroke: #2f6fd6; stroke-width: 1.6; fill: none; stroke-linecap: round; stroke-linejoin: round; opacity: 0.55; }
  .fiber--stub     { stroke: #2f6fd6; stroke-width: 1.8; fill: none; stroke-linecap: butt; }
  .fiber--uv       { stroke: #8c6ad6; stroke-width: 1.3; fill: none; stroke-linecap: round; stroke-dasharray: 4 2; opacity: 0.7; }

  /* End-to-end entanglement wavy line between MQ-A and MQ-B (workspace
     convention — magenta sinusoid; see /entanglement, /swapping). */
  .entanglement    { stroke: #c84a9b; stroke-width: 1.6; fill: none; stroke-linecap: round; }
  .entanglement-lbl{ font: 600 9px sans-serif; fill: #c84a9b; text-anchor: middle; }

  /* Numbered teleportation-protocol steps overlaid on the figure.
     dominant-baseline: central on BOTH the badge number and the caption
     text — otherwise the caption defaults to baseline-aligned (visual
     centre above y) while the badge number is geometrically centred at y,
     leaving the digits sitting visibly lower than the words. */
  .step-num   { font: 700 11px sans-serif; fill: #ffffff; text-anchor: middle; dominant-baseline: central; }
  .step-num-bg{ fill: #1a3458; stroke: none; }
  .step-txt   { font: 600 10px sans-serif; fill: #1a3458; text-anchor: start; dominant-baseline: central; }
"""


# ---------------------------------------------------------------------------
# Figure assembly
# ---------------------------------------------------------------------------


def build() -> Canvas:
    cv = Canvas(
        width=W,
        height=H,
        title=(
            "4-hop heterogeneous quantum network — transmon QPU + M-O at Node A "
            "(in a dilution fridge), 171-Yb+ trap + QFC bench at Node B, three SiV "
            "repeaters with internal QFCs along the photonic chain, midpoint BSM at "
            "M1-M4 using the QuISP BSA glyph."
        ),
        css=CSS,
    )
    Q.register(cv, "quisp-bsa-white", "bsm-meter")

    _background(cv)  # MUST come first — paints behind everything else
    _node_A(cv)
    _node_B(cv)
    _photonic_chain(cv)
    _midpoints(cv)
    _hop_brackets(cv)
    _entanglement_overlay(cv)
    _protocol_steps(cv)
    _lifetime_panel(cv)
    _legend(cv)
    return cv


# -- Background: two-tone shading + LOCC line ------------------------------


def _background(cv: Canvas) -> None:
    """Two-tone background marking the matter-photon interface.

    Upper band (matter qubits — DQ + MQ at the nodes, C inside each QR) is
    pale lavender. Lower band (photonic / network subsystem — CQ, the
    transducers, the photonic axis, the comm qubits in each QR, BSMs) is
    pale azure. The dashed line at INTERFACE_Y marks where matter qubits
    hand entanglement off to flying photons.

    This is NOT an LOCC boundary — LOCC is a protocol class (not a region),
    and both bands run LOCC at various points (CQ during entanglement
    generation, DQ+MQ during teleportation). See /entanglement#locc.

    Inside each QR the central memory C sits geometrically in the lower
    band but conceptually belongs with the matter plane — that's a quirk
    of collapsing the QR's L-C-R triple onto a horizontal axis; the split
    is fundamentally a *qubit-role* one, not a y-coordinate one.
    """
    # Stop the lower band just above the hop-bracket strip, so the bracket
    # ticks read cleanly against white.
    bottom_y = HOP_BRACKET_Y - 12
    cv.rect(0, 0, W, INTERFACE_Y, cls="plane-matter", name="bg-matter")
    cv.rect(0, INTERFACE_Y, W, bottom_y - INTERFACE_Y, cls="plane-photonic", name="bg-photonic")
    # Dashed boundary, full-width, behind the foreground elements.
    cv.line(0, INTERFACE_Y, W, INTERFACE_Y, cls="interface-line", name="interface-line")
    # One-liner explainer for the dashed boundary, placed below the line.
    # The split is fundamentally a *qubit-role* one (matter vs flying) — the
    # line marks the matter–photon handoff that every quantum-network link
    # has to cross.
    cv.text(
        W / 2, INTERFACE_Y + 14,
        "above: qubits hold the entanglement at the nodes.   below: photons fly between nodes to establish it.",
        cls="plane-tag", anchor="middle", font_size=9,
        name="plane-tag-interface",
    )


# -- Node A -----------------------------------------------------------------


def _node_A(cv: Canvas) -> None:
    # Chandelier silhouette
    C.chandelier(
        cv,
        cx=NODE_A_CX,
        top_y=NODE_A_TOP,
        bottom_y=NODE_A_BOT,
        top_width=CHAND_TOP_W,
        bottom_width=CHAND_BOT_W,
        stages=[(60, "50 K"), (140, "4 K"), (210, "15 mK")],
    )
    # Title
    cv.text(NODE_A_CX, 38, "Node A", cls="node-ttl", font_size=13, name="A-title")
    cv.text(NODE_A_CX, 52, "transmon QPU + M-O", cls="node-sub", font_size=9.5, name="A-sub")

    # Qubit column. Side labels go to the LEFT of Node A's column (anchor=end),
    # leaving the inner-facing side free for a future "entanglement wriggly
    # line" between MQ-A and MQ-B that should not be obscured by labels.
    C.qubit_column(
        cv,
        cx=NODE_A_CX,
        side_anchor="end",
        qubits=[
            (Y_DQ, "data", "ψ", "DQ-A"),
            (Y_MQ, "memory", "M", "MQ-A"),
            (Y_CQ, "comm", "C", "CQ-A"),
        ],
    )

    # Matter-side BSM between DQ-A (data qubit holding |ψ⟩) and MQ-A
    # (Alice's half of the long-distance Bell pair). This is the local
    # CNOT + H + readout that consumes |ψ⟩ and the Bell-pair half and
    # produces the 2 classical bits that travel to Bob.
    C.matter_bsm(cv, NODE_A_CX, (Y_DQ + Y_MQ) / 2, size=20,
                 name="A-matter-bsm")

    # SWAP between MQ and CQ
    C.swap_arrow(cv, NODE_A_CX, Y_MQ + 11, Y_CQ - 11)

    # Per-qubit lifetime tag — bare value, no 'T₂ ≈' prefix (the panel
    # title already establishes that the dimension being shown is T₂).
    # MQ-A is a *different* qubit hardware than DQ/CQ — typically a 3D
    # bosonic cavity coupled to a transmon ancilla, giving ~10 ms vs the
    # bare-transmon ~100 µs. That role distinction is the reason MQ
    # exists separately from DQ at all.
    for y, val in ((Y_DQ, "100 µs"), (Y_MQ, "10 ms"), (Y_CQ, "100 µs")):
        cv.text(NODE_A_CX - 20, y + 14, val, cls="t2-tag",
                font_size=7.5, anchor="end", name=f"A-t2@{y}")

    # CQ-A microwave link to M-O
    cv.line(
        NODE_A_CX, Y_FIBER_LINK_FROM, NODE_A_CX, Y_TRANSDUCER_TOP,
        cls="fiber", name="A-mw-link",
    )
    cv.circle(NODE_A_CX, Y_PHOTON_NEAR_CQ, 7, cls="photon", name="A-mw-photon")

    # M-O block
    C.transducer_block(
        cv,
        cx=NODE_A_CX,
        top_y=Y_TRANSDUCER_TOP,
        width=TRANSDUCER_W,
        height=TRANSDUCER_H,
        title="M-O",
        line_in="60 mm · 5 GHz",         # wavelength · frequency (matches QFC convention)
        line_out="1550 nm · 193 THz",
        cls="m2o-blk",
    )

    # Elbow fibre to QR-1 left edge
    C.elbow_path(
        cv,
        start_x=NODE_A_CX,
        start_y=Y_TRANSDUCER_BOT,
        end_x=QR_CENTRES[0] - QR_QFC_FACE,  # touches QR-1 left QFC outer face
        end_y=AXIS_Y,
        radius=35,
        name="A-elbow",
    )


# -- Node B -----------------------------------------------------------------


def _node_B(cv: Canvas) -> None:
    # Dashed Node B outline wraps chamber + QFC bench
    C.node_outline(
        cv,
        cx=NODE_B_CX,
        top_y=NODE_B_OUTLINE_TOP,
        bottom_y=NODE_B_OUTLINE_BOT,
        width=124,
    )
    cv.text(NODE_B_CX, 28, "Node B", cls="node-ttl", font_size=13, name="B-title")
    cv.text(NODE_B_CX, 40, "¹⁷¹Yb⁺ trap + QFC bench", cls="node-sub", font_size=9.5, name="B-sub")

    # UHV chamber (capsule) with side viewports above/below the qubit column
    C.vacuum_chamber(
        cv,
        cx=NODE_B_CX,
        top_y=CHAMBER_TOP,
        bottom_y=CHAMBER_BOT,
        width=CHAMBER_W,
        viewport_rows=(78, 186),
    )
    # Cold region — wraps just the qubit cluster *tightly* (3-px buffer
    # each side of the radius-11 circles). The temperature tag lives
    # OUTSIDE the zone on the inner-facing side, as a horizontal two-line
    # label placed low (near CQ-B) so the MQ row stays clear for the
    # MQ-A ↔ MQ-B entanglement wavy line above.
    cold_x = NODE_B_CX - 14   # 906 — just outside qubit right edge (931 minus circle, wait)
    cold_y = 64               # 3 px above DQ-B top (67)
    cold_w = 28               # right edge at 934 — 3 px outside qubit right edge (931)
    cold_h = 115              # bottom at y=179 — 3 px below CQ-B bottom (176)
    cv.rect(cold_x, cold_y, cold_w, cold_h, cls="cold-zone", rx=8, name="B-cold-zone")
    # Two-line tag, right-anchored against the cold-zone left edge, vertical
    # midpoint at CQ-B height. Reads as a normal horizontal label.
    tag_x = cold_x - 4
    tag_y = Y_CQ
    cv.add(
        f'<text x="{tag_x}" y="{tag_y}" class="cold-tag" '
        f'style="text-anchor:end">'
        f'<tspan x="{tag_x}" dy="-0.5em">Yb⁺ ions</tspan>'
        f'<tspan x="{tag_x}" dy="1.1em">~mK</tspan>'
        f'</text>',
        kind="text",
        name="B-cold-tag",
    )
    # Ultra-High Vacuum · 300 K — flush against the LEFT wall of the Node B
    # outline, in the band between the chamber and the QFC bench. Kept off the
    # central x-axis so the dashed UV photon link from CQ-B down to the QFC
    # stays unblocked. Two stacked lines: expanded acronym on top, temperature
    # below.
    _uhv_x = NODE_B_CX - 62 + 4  # node-outline width is 124, so left wall = cx-62
    _uhv_y = (CHAMBER_BOT + Y_TRANSDUCER_TOP) / 2 + 3
    cv.add(
        f'<text x="{_uhv_x}" y="{_uhv_y}" class="plate-tag" '
        f'style="text-anchor:start;fill:#2a5288;font-size:7.5px">'
        f'<tspan x="{_uhv_x}" dy="-1.1em">Ultra-High</tspan>'
        f'<tspan x="{_uhv_x}" dy="1.1em">Vacuum</tspan>'
        f'<tspan x="{_uhv_x}" dy="1.1em">300 K</tspan>'
        f'</text>',
        kind="text",
        name="B-uhv-tag",
    )

    # Qubit column. Side labels go to the RIGHT of Node B's column
    # (anchor=start) — mirror of Node A. Inner-facing sides of both nodes
    # are kept free for a future entanglement wriggly-line between MQs.
    C.qubit_column(
        cv,
        cx=NODE_B_CX,
        side_anchor="start",
        qubits=[
            # DQ-B is empty (no ψ glyph) — the teleportation hasn't fired
            # yet at the moment this snapshot is captured, so the data slot
            # at Bob's side is still vacant. Once Alice's BSM produces the
            # 2 classical bits and Bob applies his Pauli correction, the
            # state ends up here.
            (Y_DQ, "data", "", "DQ-B"),
            (Y_MQ, "memory", "M", "MQ-B"),
            (Y_CQ, "comm", "C", "CQ-B"),
        ],
    )
    C.swap_arrow(cv, NODE_B_CX, Y_MQ + 11, Y_CQ - 11)

    # Per-qubit lifetime tag — bare value, same convention as Node A.
    for y in (Y_DQ, Y_MQ, Y_CQ):
        cv.text(NODE_B_CX + 20, y + 14, "10 s", cls="t2-tag",
                font_size=7.5, anchor="start", name=f"B-t2@{y}")

    # UV link from CQ-B (via chamber viewport) to the QFC bench below
    cv.line(
        NODE_B_CX, Y_FIBER_LINK_FROM, NODE_B_CX, Y_TRANSDUCER_TOP,
        cls="fiber--uv", name="B-uv-link",
    )
    # UV photon sits adjacent to CQ-B (matches CQ-A microwave photon spacing).
    cv.circle(NODE_B_CX, 179, 3, cls="photon", name="B-uv-photon")

    # QFC block on the room-temperature bench
    C.transducer_block(
        cv,
        cx=NODE_B_CX,
        top_y=Y_TRANSDUCER_TOP,
        width=TRANSDUCER_W,
        height=TRANSDUCER_H,
        title="QFC",
        line_in="369 nm · 812 THz",
        line_out="1550 nm · 193 THz",
        cls="qfc-blk",
    )
    # ("300 K bench" tag removed — already covered by "UHV · 300 K" on the
    # chamber and the "QFC bench" subtitle below "Node B".)

    # Elbow fibre from QFC bottom to QR-3 right edge
    C.elbow_path(
        cv,
        start_x=NODE_B_CX,
        start_y=Y_TRANSDUCER_BOT,
        end_x=QR_CENTRES[-1] + QR_QFC_FACE,  # touches QR-3 right QFC outer face
        end_y=AXIS_Y,
        radius=35,
        name="B-elbow",
    )


# -- QR chain ---------------------------------------------------------------


def _photonic_chain(cv: Canvas) -> None:
    # Telecom fibre segments — each segment runs from the OUTER FACE of one
    # QR's QFC to the outer face of the next QR's QFC. Drawing the fibre in
    # discrete segments (rather than one line through the QRs) is what lets a
    # future revision animate a photon moving along each segment.
    for i in range(len(QR_CENTRES) - 1):
        x0 = QR_CENTRES[i] + QR_QFC_FACE      # right QFC outer face of QR_i
        x1 = QR_CENTRES[i + 1] - QR_QFC_FACE  # left QFC outer face of QR_{i+1}
        cv.line(x0, AXIS_Y, x1, AXIS_Y, cls="fiber--quantum", name=f"axis-fibre-{i}")

    for cx in QR_CENTRES:
        C.qr_node(
            cv,
            cx=cx,
            axis_y=AXIS_Y,
            label=f"QR-{QR_CENTRES.index(cx) + 1}",
            width=QR_WIDTH,
            qbit_gap=QBIT_GAP,
        )


def _midpoints(cv: Canvas) -> None:
    """M1 / M4 on the elbow verticals; M2 / M3 between the QR chain pairs.

    On the verticals, the BSA icon sits on top of the fibre — so its label
    goes to the side, not above. On the horizontal axis the label goes
    above; the fibre passes through the icon centre without text collision.
    """
    BSM_SIZE = 24
    # M1 — Node A side, label points outward (left, toward Node A)
    C.midpoint_bsm(cv, NODE_A_CX, Y_M1_M4, size=BSM_SIZE, label="M1", label_pos="left")
    # M4 — Node B side, label points outward (right, toward Node B)
    C.midpoint_bsm(cv, NODE_B_CX, Y_M1_M4, size=BSM_SIZE, label="M4", label_pos="right")
    # M2 between QR-1 R₁ and QR-2 L₂
    r1 = QR_CENTRES[0] + QBIT_GAP
    l2 = QR_CENTRES[1] - QBIT_GAP
    m2_x = (r1 + l2) / 2
    C.midpoint_bsm(cv, m2_x, AXIS_Y, size=BSM_SIZE, label="M2", label_pos="above")
    # M3 between QR-2 R₂ and QR-3 L₃
    r2 = QR_CENTRES[1] + QBIT_GAP
    l3 = QR_CENTRES[2] - QBIT_GAP
    m3_x = (r2 + l3) / 2
    C.midpoint_bsm(cv, m3_x, AXIS_Y, size=BSM_SIZE, label="M3", label_pos="above")

    # SNSPD temperature tags — every BSM station is shorthand for "fibre
    # bench at 300 K + SNSPD chip in a He cryostat at ~2 K". Knaut Nature
    # 629.573 uses Photon Spot SNSPDs; ETSI GR QKD 003 §5 lists 0.12–2.3 K
    # sensor temps for NbN/WSi nanowires at 1550 nm. Two lines: name on top,
    # temperature below.
    #
    # Placement:
    #   * M1 (Node-A side, label="M1" on the left) → tag on the RIGHT
    #   * M4 (Node-B side, label="M4" on the right) → tag on the LEFT
    #   * M2 / M3 (on axis, label above) → tag centred below
    bsm_half = 12  # BSM_SIZE / 2
    side_gap = 4
    tag_specs = [
        # (cx, cy, anchor, name)
        (NODE_A_CX + bsm_half + side_gap, Y_M1_M4, "start",  "bsm-temp-M1"),
        (NODE_B_CX - bsm_half - side_gap, Y_M1_M4, "end",    "bsm-temp-M4"),
        (m2_x,                            AXIS_Y + 24, "middle", "bsm-temp-M2"),
        (m3_x,                            AXIS_Y + 24, "middle", "bsm-temp-M3"),
    ]
    for x, y, anchor, name in tag_specs:
        cv.add(
            f'<text x="{x}" y="{y}" class="cold-tag" '
            f'style="text-anchor:{anchor};font-size:6.5px">'
            f'<tspan x="{x}" dy="-0.15em">SNSPDs</tspan>'
            f'<tspan x="{x}" dy="1.1em">~2 K</tspan>'
            f'</text>',
            kind="text",
            name=name,
        )


# Kept around in case a future revision wants per-segment distance tags,
# but currently unused — the hop brackets below already encode "100 km" each.
def _kilometre_labels_unused(cv: Canvas) -> None:
    """Eight '50 km' tags around the four hops."""
    # Upper-leg (vertical) labels on each elbow — outside the chandelier/Node B
    cv.text(
        NODE_A_CX - 30, (NODE_A_BOT + Y_M1_M4) / 2, "50 km",
        cls="km", font_size=9, anchor="middle",
        style="writing-mode:vertical-rl;",  # rotates without transform headaches
        name="km-A-upper",
    )
    cv.text(
        NODE_B_CX + 30, (NODE_A_BOT + Y_M1_M4) / 2, "50 km",
        cls="km", font_size=9, anchor="middle",
        style="writing-mode:vertical-rl;",
        name="km-B-upper",
    )
    # Lower-leg label sits below the horizontal section of the elbow
    cv.text(
        (QR_CENTRES[0] - QR_WIDTH / 2 + NODE_A_CX) / 2 + 30, AXIS_Y + 18, "50 km",
        cls="km", font_size=9, anchor="middle", name="km-A-lower",
    )
    cv.text(
        (QR_CENTRES[-1] + QR_WIDTH / 2 + NODE_B_CX) / 2 - 30, AXIS_Y + 18, "50 km",
        cls="km", font_size=9, anchor="middle", name="km-B-lower",
    )

    # Horizontal-segment labels: midpoints of each (R_n -> M_x -> L_{n+1}) half
    r1 = QR_CENTRES[0] + QBIT_GAP
    l2 = QR_CENTRES[1] - QBIT_GAP
    m2 = (r1 + l2) / 2
    r2 = QR_CENTRES[1] + QBIT_GAP
    l3 = QR_CENTRES[2] - QBIT_GAP
    m3 = (r2 + l3) / 2
    for x, name in [((r1 + m2) / 2, "h21"), ((m2 + l2) / 2, "h22"),
                    ((r2 + m3) / 2, "h31"), ((m3 + l3) / 2, "h32")]:
        cv.text(x, AXIS_Y + 48, "50 km", cls="km", font_size=9, anchor="middle", name=f"km-{name}")


def _hop_brackets(cv: Canvas) -> None:
    bounds = [NODE_A_CX, QR_CENTRES[0], QR_CENTRES[1], QR_CENTRES[2], NODE_B_CX]
    labels = [f"Hop {i+1} — 100 km" for i in range(4)]
    C.hop_brackets(cv, HOP_BRACKET_Y, bounds, labels)


def _protocol_steps(cv: Canvas) -> None:
    """Overlay the five teleportation steps. Reads bottom-up (1 lowest,
    5 highest). Steps 1-2 sit just below the matter–photon interface
    explainer line; steps 3-5 sit above the entanglement wavy line in
    the matter band. All numbers are left-aligned in a single column;
    the column is positioned so the whole block (badge + longest text)
    is horizontally centred in the figure."""
    # All five steps stacked, bottom-up (step 1 lowest, step 5 highest),
    # in the open photonic-band strip below the interface explainer line.
    # Numbers are left-aligned in a single column; the whole block (badge
    # column + longest line of text) is horizontally centred on the figure.
    captions = [
        "Generate Bell pairs per hop — 10³–10⁵ heralded retries per pair (fibre loss + 50% photonic BSM).",
        "Distil per hop, then matter-matter swap end-to-end — gated by memory T₂ in the wait.",
        "Load |ψ⟩ onto DQ-A — must beat MQ-A's coherence budget or the chain restarts.",
        "Local matter-matter BSM on (DQ-A, MQ-A) destroys |ψ⟩, yields 2 classical bits.",
        "Bits travel to DC-B; apply Pauli to MQ-B — |ψ⟩ at B (classical-channel latency only).",
    ]
    badge_r = 7
    gap = 6
    font_size = 9
    row_gap = 20
    # Shift the block RIGHT of canvas centre so the T₂ coherence-budget
    # inset panel can sit to its left without overlap. centre_y picks the
    # vertical band a bit higher to leave breathing room below the dashed
    # matter-photon interface line.
    centre_x = 605
    centre_y = 250
    # Width heuristic — the rendered prose is narrower than the svglib
    # collision-bbox default (0.55), so an over-estimated width pulls the
    # badge column too far LEFT and the block looks left-lopsided.
    # 0.48 matches the actual render of the longest line (step 1) so the
    # block visually centres on centre_x.
    text_w = lambda s: 0.48 * font_size * len(s)
    block_w = badge_r * 2 + gap + max(text_w(c) for c in captions)
    badge_x = centre_x - block_w / 2 + badge_r   # left-aligned column
    text_x = badge_x + badge_r + gap
    n = len(captions)
    block_h = row_gap * (n - 1)
    top_y = centre_y - block_h / 2
    for i, txt in enumerate(captions, start=1):
        y = top_y + (n - i) * row_gap   # step 1 at bottom, step 5 at top
        cv.circle(badge_x, y, badge_r, cls="step-num-bg", name=f"step{i}-badge")
        cv.text(badge_x, y, str(i), cls="step-num", font_size=10, name=f"step{i}-num")
        cv.text(text_x, y, txt,
                cls="step-txt", font_size=font_size, anchor="start",
                name=f"step{i}-txt")


def _lifetime_panel(cv: Canvas) -> None:
    """T₂ coherence-budget inset. Sits to the LEFT of the 5-step block in
    the matter-band, telling the orders-of-magnitude story (µs → 10 s) for
    the four qubit roles in the figure. Same span as the step block so the
    two sit as a balanced pair, with the steps on the right answering
    "what happens" and the panel on the left answering "how much time
    each qubit has to do its job".

    Numbers are representative ranges drawn from Lauk QST 2020, Bradley
    PRX 2019 (¹³C nuclear memory), Knaut Nature 2024 (SiV electron), and
    Brown PRA 2018 (¹⁷¹Yb⁺ hyperfine). Not platform-leading records — the
    typical operating numbers that fit a procurement-grade conversation."""
    # Start past Node A's chandelier outline (which extends to ~x=150)
    # with a small breathing margin so the panel doesn't impinge on it.
    # py is chosen so the row stride (20 px, matching the step block's
    # row_gap) places each panel row at exactly the same y as the
    # corresponding step in the 5-step block — the two read as a pair.
    px, py, pw, ph = 160, 182, 200, 118
    cv.rect(
        px, py, pw, ph, rx=6,
        style="fill: #fafbfc; stroke: #c4cad3; stroke-width: 1; stroke-dasharray: 4 3",
        name="lifetime-panel-bg",
    )
    cv.text(
        px + pw / 2, py + 14, "T₂ coherence budget",
        cls="step-txt", font_size=10.5, anchor="middle",
        style="font-weight: 700",
        name="lifetime-panel-ttl",
    )
    rows = [
        ("data",   "transmon (DQ-A, CQ-A)", "100 µs"),
        ("memory", "cavity memory (MQ-A)",  "10 ms"),
        ("comm",   "SiV electron (C)",      "1 ms"),
        ("memory", "¹³C nuclear (M)",       "1 s"),
        ("data",   "¹⁷¹Yb⁺ (Node B)",       "10 s"),
    ]
    # Row stride matches the step block's row_gap (20) so panel rows
    # land at the same y values as the steps. With py=182, y0=210
    # equals the top step's y; subsequent rows land on step4, step3, …
    y0, dy = py + 28, 20
    for i, (role, label, value) in enumerate(rows):
        y = y0 + i * dy
        # Dot centred on the text baseline (the text is drawn at y with
        # dominant-baseline central from .step-txt CSS, so the dot's
        # geometric centre should also be at y).
        cv.circle(px + 14, y, 5, cls=role, name=f"lt-sw-{i}")
        cv.text(
            px + 26, y, label,
            cls="step-txt", font_size=9.5, anchor="start",
            name=f"lt-lbl-{i}",
        )
        cv.text(
            px + pw - 10, y, value,
            cls="step-txt", font_size=9.5, anchor="end",
            style="font-style: italic",
            name=f"lt-val-{i}",
        )


def _entanglement_overlay(cv: Canvas) -> None:
    """Magenta wavy line from MQ-A (Node A) to MQ-B (Node B) — depicts the
    delivered end-to-end Bell pair held in the two endpoint memories. The
    network plumbing below (QRs + BSMs) produced this pair via four
    heralded hops and two levels of swapping; the line is the resource it
    delivered, ready to be consumed by teleportation."""
    x0 = NODE_A_CX + 9   # MQ-A inner edge
    x1 = NODE_B_CX - 9   # MQ-B inner edge
    y = Y_MQ
    half_wl = 10  # px between alternating crests
    amp = 4
    n_half = int((x1 - x0) / half_wl)
    span = n_half * half_wl  # snap to integer half-wavelengths
    # Centre the wave between the two endpoints
    pad = (x1 - x0 - span) / 2
    sx = x0 + pad
    parts = [f"M {sx} {y} q {half_wl/2} {-amp} {half_wl} 0"]
    parts.extend("t {} 0".format(half_wl) for _ in range(n_half - 1))
    # Lead-in / lead-out straight segments to meet the qubit edges flush
    cv.line(x0, y, sx, y, cls="entanglement", name="entg-lead-in")
    cv.add(
        f'<path d="{" ".join(parts)}" class="entanglement"/>',
        kind="path",
        name="entg-wave",
    )
    cv.line(sx + span, y, x1, y, cls="entanglement", name="entg-lead-out")


def _legend(cv: Canvas) -> None:
    C.legend_row(
        cv,
        base_y=LEGEND_Y,
        items=[
            {"kind": "rect",    "cls": "repeater", "label": "SiV⁻ Repeater (QR)"},
            {"kind": "circle",  "cls": "data",     "label": "Data Qubit (DQ)"},
            {"kind": "circle",  "cls": "comm",     "label": "Comm Qubit (CQ)"},
            {"kind": "circle",  "cls": "memory",   "label": "Memory Qubit (MQ)"},
            {"kind": "photons", "sizes": [7, 4, 2], "label": "Photon (size = λ)"},
        ],
    )
    # BSM glyph isn't a rect/circle/photons - render manually next to first item
    # Actually let the QuISP BSA appear in the figure itself; readers see it
    # at M1/M2/M3/M4 with labels already attached.


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main(out: Path | None = None, preview_png: Path | None = None) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = out or (repo_root / "images" / "4hop-topology.svg")
    cv = build()
    svg = cv.to_svg()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg)
    print(f"wrote {out}")

    # web/public/images is a symlink → ../../images, so the Astro app
    # already serves whatever we wrote above. No mirror-on-write needed.

    overlaps = cv.check_text_overlaps(pad=0.5)
    if overlaps:
        print(f"WARN: {len(overlaps)} text overlaps:")
        for a, b in overlaps[:10]:
            print(f"  - {a.name!r:30s} ↔ {b.name!r}")

    if preview_png:
        render_png(str(out), str(preview_png), output_width=1600)
        print(f"preview PNG: {preview_png}")


if __name__ == "__main__":
    import sys

    preview = Path("/tmp/4hop.png") if "--preview" in sys.argv else None
    main(preview_png=preview)
