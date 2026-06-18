"""Generate five standalone glyph SVGs used by the network-ops figures.

Run from the repo root::

    python -m scripts.diagrams.qubit_icons

Emits to ``images/`` (which ``web/public/images`` symlinks to):

* ``icon-data-qubit.svg``     — orange (data role from 4hop-topology)
* ``icon-comms-qubit.svg``    — green (comm role)
* ``icon-memory-qubit.svg``   — purple (memory role)
* ``icon-flying-qubit.svg``   — blue radial-gradient cloud (flying photon)
* ``icon-bsm-meter.svg``      — semicircular gauge for matter-side BSM

Colour palette is copied verbatim from ``topology_4hop.py`` so every page in
the workspace reads the same colour-to-role mapping. The three matter icons
carry a single thin letter (D / C / M) at 8 px; the flying-qubit icon uses
the same radial-gradient recipe as ``#ops-photon-cloud`` in entanglement.astro
(stops at 0%, 35%, 70%, 100%).
"""

from __future__ import annotations

from pathlib import Path


# Shared palette — keep in lockstep with topology_4hop.py.
PALETTE = {
    "data":   {"fill": "#f29453", "stroke": "#8a3f0e", "letter": "D"},
    "comm":   {"fill": "#22c55e", "stroke": "#15803d", "letter": "C"},
    "memory": {"fill": "#9b87c4", "stroke": "#6048a3", "letter": "M"},
}

# Photon stroke colour from 4hop — used by the flying-qubit gradient stops.
PHOTON_BLUE = "#2f6fd6"


def _matter_icon_svg(role: str) -> str:
    spec = PALETTE[role]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" '
        'width="32" height="32" '
        f'role="img" aria-label="{role} qubit icon">'
        f'<circle cx="16" cy="16" r="12" fill="{spec["fill"]}" '
        f'stroke="{spec["stroke"]}" stroke-width="1.4"/>'
        f'<text x="16" y="16" text-anchor="middle" dominant-baseline="central" '
        f'font-family="sans-serif" font-size="11" font-weight="700" '
        f'fill="#ffffff">{spec["letter"]}</text>'
        '</svg>\n'
    )


def _meter_icon_svg() -> str:
    # Dial + needle wrapped in a rectangular instrument enclosure, so the BSM
    # reads as a discrete box at the node rather than an isolated gauge.
    # ViewBox is square (36×36) with the rectangle centred vertically — keeps
    # the icon usable in square CSS boxes (e.g. the .bsm-key__icon 48×48 slot)
    # without letterboxing.
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" '
        'width="36" height="36" '
        'role="img" aria-label="matter-side BSM meter">'
        # Enclosure (centred vertically: y=6, height=24 → spans 6..30)
        '<rect x="2" y="6" width="32" height="24" rx="2" '
        'fill="#ffffff" stroke="#1a1f2a" stroke-width="1.6"/>'
        # Dial (half-disc, flat side down) inside the enclosure
        '<path d="M 6 26 A 12 12 0 0 1 30 26 Z" '
        'fill="none" stroke="#1a1f2a" stroke-width="1.4"/>'
        # Tick marks on the rim
        '<line x1="10" y1="17" x2="8"  y2="15" stroke="#1a1f2a" stroke-width="1.1"/>'
        '<line x1="18" y1="14" x2="18" y2="12" stroke="#1a1f2a" stroke-width="1.1"/>'
        '<line x1="26" y1="17" x2="28" y2="15" stroke="#1a1f2a" stroke-width="1.1"/>'
        # Needle: pivots at dial centre, points upper-right
        '<line x1="18" y1="26" x2="27" y2="16" '
        'stroke="#d97706" stroke-width="2.0" stroke-linecap="round"/>'
        # Pivot dot
        '<circle cx="18" cy="26" r="1.6" fill="#1a1f2a"/>'
        '</svg>\n'
    )


def _flying_icon_svg() -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" '
        'width="32" height="32" '
        'role="img" aria-label="flying photon qubit icon">'
        '<defs>'
        '<radialGradient id="flying-cloud">'
        f'<stop offset="0%"   stop-color="{PHOTON_BLUE}" stop-opacity="1"/>'
        f'<stop offset="35%"  stop-color="{PHOTON_BLUE}" stop-opacity="0.92"/>'
        f'<stop offset="70%"  stop-color="{PHOTON_BLUE}" stop-opacity="0.45"/>'
        f'<stop offset="100%" stop-color="{PHOTON_BLUE}" stop-opacity="0"/>'
        '</radialGradient>'
        '</defs>'
        '<circle cx="16" cy="16" r="14" fill="url(#flying-cloud)"/>'
        '</svg>\n'
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    writes = [
        ("icon-data-qubit.svg",   _matter_icon_svg("data")),
        ("icon-comms-qubit.svg",  _matter_icon_svg("comm")),
        ("icon-memory-qubit.svg", _matter_icon_svg("memory")),
        ("icon-flying-qubit.svg", _flying_icon_svg()),
        ("icon-bsm-meter.svg",    _meter_icon_svg()),
    ]
    for name, svg in writes:
        path = out_dir / name
        path.write_text(svg)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
