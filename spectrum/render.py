#!/usr/bin/env python3
"""Render 'Quantum platforms on the electromagnetic spectrum' from data.yaml.

Default output: output/spectrum.svg
Optional formats: --format png | pdf  (require the cairosvg package)
"""
from __future__ import annotations

import argparse
import html
import math
import sys
from datetime import datetime
from pathlib import Path

C_M_S = 299_792_458

# Platform box layout. Each box has three text rows (name, subtitle, vendors);
# track height is derived so the third descender clears the bottom border.
DEFAULT_LINES = 3
LINE_GAP = 14            # baseline-to-baseline spacing inside a box
FIRST_BASELINE_DY = 17   # box_top to first text baseline
DESCENDER_PAD = 7        # last baseline to box bottom
INTER_TRACK_GAP = 16     # vertical breathing room between tracks
PAD_X = 10               # horizontal padding from text edge to box edge

# Capability chips (C / M / S) sit at the top-right of every platform
# box. Each chip is filled with the platform colour when the role is
# supported, and outlined-only when not. The strip occupies the right
# part of the title row: title text must end before the strip starts.
ROLE_ORDER = ("compute", "memory", "source")
CHIP_LETTER = {"compute": "C", "memory": "M", "source": "S"}
CHIP_W = 13              # chip side length (square)
CHIP_GAP = 2             # gap between adjacent chips
CHIP_PAD_RIGHT = 6       # gap from rightmost chip to box right edge
CHIP_PAD_TOP = 4         # gap from box top to chip top
CHIP_PAD_LEFT = 6        # min gap between title text and the chip strip
CHIP_STRIP_W = (
    CHIP_W * len(ROLE_ORDER) + CHIP_GAP * (len(ROLE_ORDER) - 1) + CHIP_PAD_RIGHT
)

# Real font metrics (via Pillow + Helvetica Bold) so box widths reflect the
# actual rendered text extent, not a per-character estimate. Falls back to
# a coarse char-width factor if Pillow or the font isn't available — in
# which case the visible padding will vary slightly between boxes.
_FONT_CANDIDATES = [
    ("/System/Library/Fonts/Helvetica.ttc",                       1),  # Bold face
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",      0),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 0),
    ("C:\\Windows\\Fonts\\arialbd.ttf",                           0),
]
_FONT_SIZE = {"p-name": 13.0, "p-sub": 10.5, "vendor": 10.5}


def _font_loader():
    try:
        from PIL import ImageFont
    except ImportError:
        return None
    for path, idx in _FONT_CANDIDATES:
        try:
            ImageFont.truetype(path, 10, index=idx)
            from functools import lru_cache

            @lru_cache(maxsize=8)
            def loader(size: float):
                return ImageFont.truetype(path, size, index=idx)
            return loader
        except (OSError, FileNotFoundError):
            continue
    return None


_FONT = _font_loader()
_FALLBACK_CHAR_W = {"p-name": 7.0, "p-sub": 5.8, "vendor": 5.8}


def measure_text(text: str, cls: str) -> float:
    if _FONT is not None:
        return _FONT(_FONT_SIZE[cls]).getlength(text)
    return len(text) * _FALLBACK_CHAR_W[cls]


def content_box_width(body_lines: list[tuple[str, str]]) -> float:
    """Width that fits the widest content line plus uniform PAD_X each
    side, with extra right-side reservation on the title row so the
    capability chip strip never overlaps title text. Title is the only
    line that has to clear the chip strip (it sits on the same y); all
    other rows are below the strip and use the full inner width."""
    title_w = next((measure_text(t, c) for c, t in body_lines if c == "p-name"), 0)
    other_w = max((measure_text(t, c) for c, t in body_lines if c != "p-name"),
                  default=0)
    needed_for_title = title_w + PAD_X + CHIP_PAD_LEFT + CHIP_STRIP_W
    needed_for_other = other_w + 2 * PAD_X
    return max(needed_for_title, needed_for_other)


def box_height_for(n_lines: int) -> float:
    return FIRST_BASELINE_DY + (n_lines - 1) * LINE_GAP + DESCENDER_PAD


def n_lines_for(p: dict) -> int:
    """Number of text rows a platform box will contain: title + subtitle +
    vendor row(s) + optional academic line."""
    lines = 2  # title + subtitle
    if "vendor_lines" in p:
        lines += len(p["vendor_lines"])
    elif "vendors" in p:
        lines += 1
    if p.get("academic"):
        lines += 1
    return lines


DEFAULT_BOX_H = box_height_for(DEFAULT_LINES)


def load_data(path: Path) -> dict:
    import re

    import yaml

    # PyYAML follows YAML 1.1 and rejects unsigned exponents like "1.0e9";
    # broaden the float resolver so the natural form parses as a float.
    yaml.SafeLoader.add_implicit_resolver(
        "tag:yaml.org,2002:float",
        re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$"),
        list("-+0123456789."),
    )
    return yaml.safe_load(path.read_text())


def hz_of_nm(nm: float) -> float:
    return C_M_S / (nm * 1e-9)


def esc(s) -> str:
    return html.escape(str(s), quote=True)


_BOLD_RE = __import__("re").compile(r"\*([^*]+)\*")


def text_with_bold(s: str) -> str:
    """Convert *foo* markers in a string into <tspan font-weight="700">
    fragments suitable for use as inner text of a <text> element. Used to
    flag future/planned machine names inline in the flagship-machines table."""
    out = []
    last = 0
    for m in _BOLD_RE.finditer(s):
        out.append(esc(s[last:m.start()]))
        out.append(f'<tspan font-weight="700">{esc(m.group(1))}</tspan>')
        last = m.end()
    out.append(esc(s[last:]))
    return "".join(out)


def render_capability_chips(
    box_xl: float, box_top: float, box_xr: float,
    color: str, roles: list[str] | tuple[str, ...] | None,
) -> list[str]:
    """Render the C / M / S capability chip strip in the top-right of a
    platform box. A role present in `roles` gets a filled chip in the
    platform colour with a white letter; an absent role gets an outline-
    only chip with a faint letter so the trio always reads as a complete
    triplet (the chart shows what a platform *isn't* used for, not just
    what it is). The strip's left edge sits CHIP_PAD_LEFT inside the
    title-text right edge — content_box_width() guarantees that gap by
    sizing the box to fit title + strip + padding."""
    roles_set = set(roles or [])
    parts: list[str] = []
    strip_xr = box_xr - CHIP_PAD_RIGHT
    strip_xl = strip_xr - (CHIP_W * len(ROLE_ORDER) + CHIP_GAP * (len(ROLE_ORDER) - 1))
    for i, role in enumerate(ROLE_ORDER):
        cx = strip_xl + i * (CHIP_W + CHIP_GAP)
        cy = box_top + CHIP_PAD_TOP
        on = role in roles_set
        fill = color if on else "#ffffff"
        stroke = color if on else "#bbbbbb"
        letter_fill = "#ffffff" if on else "#999999"
        parts.append(rect(
            cx, cy, CHIP_W, CHIP_W,
            rx=2, ry=2, fill=fill, stroke=stroke, stroke_width=1,
        ))
        # Letter centred inside the chip. Helvetica caps sit roughly
        # 0.7× the font size above the baseline, so anchoring the
        # baseline at chip-bottom - 3 px puts the cap mid-chip.
        # font-size and font-weight are inlined (not just on .cap-chip
        # class) because cairosvg's PNG renderer ignores class-based
        # rules inside <style> for individual <text> elements — without
        # the inline attributes the chip letters fall back to 16 px and
        # spill out of the 13×13 chip.
        # `fill` goes through `style=` rather than the presentation
        # attribute because the SVG-level `text { fill: #222 }` rule is
        # author CSS and outranks the presentation attribute regardless
        # of specificity (SVG spec). Inline style wins.
        parts.append(text(
            cx + CHIP_W / 2, cy + CHIP_W - 3,
            CHIP_LETTER[role],
            cls="cap-chip", text_anchor="middle",
            style=f"fill:{letter_fill}",
            font_size="9", font_weight="700",
        ))
    return parts


def lighten(hex_color: str, amount: float = 0.78) -> str:
    """Blend a #rrggbb color toward white. amount=1.0 → white, 0.0 → original.
    Used to give platform boxes an opaque pastel fill so the rainbow and
    ITU strips behind them don't bleed through."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = round(r * (1 - amount) + 255 * amount)
    g = round(g * (1 - amount) + 255 * amount)
    b = round(b * (1 - amount) + 255 * amount)
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------- SVG element helpers ----------

def _attrs(items: dict) -> str:
    parts = []
    for k, v in items.items():
        if v is None or v is False:
            continue
        key = k.replace("_", "-")
        if isinstance(v, float):
            v = f"{v:.1f}"
        parts.append(f'{key}="{esc(v)}"')
    return " ".join(parts)


def rect(x, y, w, h, **attrs) -> str:
    return f'<rect {_attrs({"x": x, "y": y, "width": w, "height": h, **attrs})}/>'


def line(x1, y1, x2, y2, **attrs) -> str:
    return f'<line {_attrs({"x1": x1, "y1": y1, "x2": x2, "y2": y2, **attrs})}/>'


def circle(cx, cy, r, **attrs) -> str:
    return f'<circle {_attrs({"cx": cx, "cy": cy, "r": r, **attrs})}/>'


def text(x, y, body, cls=None, **attrs) -> str:
    a = {"class": cls, "x": x, "y": y, **attrs}
    return f'<text {_attrs(a)}>{body}</text>'


class Geom:
    """Coordinate mapping for a piecewise-log frequency axis with one or
    more visible segments separated by visual gaps.
    """

    def __init__(self, canvas: dict, freq_axis: dict, tracks: dict):
        m = canvas["margin"]
        self.W = canvas["width"]
        self.H = canvas["height"]
        self.x0 = m["left"]
        self.x1 = self.W - m["right"]
        self.segments = freq_axis["segments"]
        self.gap_pct = freq_axis.get("gap_pct", 6)

        plot_w = self.x1 - self.x0
        n_seg = len(self.segments)
        n_gap = max(0, n_seg - 1)
        gap_w = plot_w * (self.gap_pct / 100) if n_gap else 0
        seg_w_total = plot_w - gap_w * n_gap
        seg_w_pct_total = sum(s["width_pct"] for s in self.segments)

        self.seg_xs: list[tuple[float, float]] = []
        cursor = self.x0
        for s in self.segments:
            w = seg_w_total * (s["width_pct"] / seg_w_pct_total)
            self.seg_xs.append((cursor, cursor + w))
            cursor += w + gap_w

        self.gap_xs: list[tuple[float, float]] = [
            (self.seg_xs[i][1], self.seg_xs[i + 1][0]) for i in range(n_seg - 1)
        ]

        # Stack top: y of the top-edge of the tallest region's topmost
        # box. track_bottom is filled in by render_svg after greedy
        # stacking based on the deepest region's stack height, so the
        # chart reflows automatically as platforms are added or content
        # changes.
        self.track_top = tracks["top_y"]
        self.track_bottom = self.track_top  # provisional; updated post-stack

    def x_of_hz(self, hz: float) -> float:
        for s, (xa, xb) in zip(self.segments, self.seg_xs):
            if s["min_hz"] <= hz <= s["max_hz"]:
                lo, hi = math.log10(s["min_hz"]), math.log10(s["max_hz"])
                return xa + (math.log10(hz) - lo) / (hi - lo) * (xb - xa)
        for i in range(len(self.segments) - 1):
            f_left = self.segments[i]["max_hz"]
            f_right = self.segments[i + 1]["min_hz"]
            if f_left < hz < f_right:
                xb_left = self.seg_xs[i][1]
                xa_right = self.seg_xs[i + 1][0]
                lo, hi = math.log10(f_left), math.log10(f_right)
                return xb_left + (math.log10(hz) - lo) / (hi - lo) * (xa_right - xb_left)
        if hz < self.segments[0]["min_hz"]:
            return self.seg_xs[0][0]
        return self.seg_xs[-1][1]

    def x_of_nm(self, nm: float) -> float:
        return self.x_of_hz(hz_of_nm(nm))

    def hz_visible(self, hz: float) -> bool:
        return any(s["min_hz"] <= hz <= s["max_hz"] for s in self.segments)

    def x_ranges_in(self, lo_hz: float, hi_hz: float) -> list[tuple[float, float]]:
        """Canvas x-ranges that [lo_hz, hi_hz] occupies, including the gap
        slices between segments so background fills span the break."""
        intervals = []
        for i, s in enumerate(self.segments):
            intervals.append((s["min_hz"], s["max_hz"]))
            if i < len(self.segments) - 1:
                intervals.append((s["max_hz"], self.segments[i + 1]["min_hz"]))
        out = []
        for f_lo, f_hi in intervals:
            a, b = max(lo_hz, f_lo), min(hi_hz, f_hi)
            if a < b:
                out.append((self.x_of_hz(a), self.x_of_hz(b)))
        return out


def _region_for(layout: dict, g: "Geom") -> int:
    """Return the index of the freq-axis segment (0 = leftmost) the platform's
    box-center falls into. Each segment becomes its own stacking region; the
    optical and microwave stacks are computed independently."""
    cx = (layout["xl"] + layout["xr"]) / 2
    for i, (xa, xb) in enumerate(g.seg_xs):
        if cx <= xb:
            return i
    return len(g.seg_xs) - 1


def compute_stacking(layouts: list[dict], g: "Geom") -> None:
    """Per-region greedy 1-D rectangle packing. Each platform is assigned
    to the lowest level where its x-range doesn't intersect any already-
    placed box in the same region. Levels stack upward from g.track_bottom
    with a uniform INTER_TRACK_GAP between every pair of adjacent boxes;
    each level's height is the natural box-height of the tallest box on
    it (so 3-line boxes take 52 px, 4-line boxes take 66 px, etc.).

    Mutates each layout dict in place: sets `box_top`, `box_bot`,
    `region`, and `level`. Nothing about the layout is hard-coded — every
    position is derived from the data + measured content extents."""
    if not layouts:
        return

    # Bucket layouts by region (= freq-axis segment index).
    by_region: dict[int, list[dict]] = {}
    for L in layouts:
        L["region"] = _region_for(L, g)
        by_region.setdefault(L["region"], []).append(L)

    # Greedy stack each region in ascending-frequency order so higher-freq
    # platforms end up on higher levels visually (mirrors how the spectrum
    # axis is read), regardless of x-order.
    def _freq_center(p: dict) -> float:
        if "freq_range_hz" in p:
            return (p["freq_range_hz"][0] + p["freq_range_hz"][1]) / 2
        if "wavelength_range_nm" in p:
            nm_avg = (p["wavelength_range_nm"][0] + p["wavelength_range_nm"][1]) / 2
            return hz_of_nm(nm_avg)
        if "wavelength_nm" in p:
            return hz_of_nm(p["wavelength_nm"])
        return 0.0

    by_id = {L["p"]["id"]: L for L in layouts}

    def _x_fits(L: dict, lvl_boxes: list[dict]) -> bool:
        return all(L["xr"] <= b["xl"] or L["xl"] >= b["xr"] for b in lvl_boxes)

    region_levels: dict[int, list[list[dict]]] = {}
    for region, items in by_region.items():
        # Sort by frequency ascending so platforms get assigned levels
        # bottom-up in freq order. Constrain each box's level to be >=
        # the previous (lower-freq) box's level so a high-freq isolated
        # box (like Trapped ions, which doesn't overlap anything else)
        # can't fall back to level 0 — it'll instead pile on top.
        items.sort(key=lambda L: _freq_center(L["p"]))
        # Honor align_above sort hints by moving each hinted platform
        # to immediately after its target in the freq-sorted list. The
        # monotonic-level pass-1 placer then assigns it a level
        # >= target's, with any x-overlap pushing it higher and
        # cascading later (higher-freq) platforms up alongside it.
        # Use sort-order rather than a level-snap so the cascade
        # happens naturally — the alternative left a vacated level
        # below and didn't push higher-freq platforms above the
        # promoted box.
        hint_items = [L for L in items if "align_above" in L["p"]]
        for L in hint_items:
            items.remove(L)
        for L in hint_items:
            target_id = L["p"]["align_above"]
            target_idx = next(
                (i for i, T in enumerate(items)
                 if T["p"]["id"] == target_id),
                None,
            )
            if target_idx is None:
                # Target missing or in another region — fall back to
                # natural freq order at the end.
                print(
                    f"warning: align_above={target_id} for "
                    f"'{L['p']['label']}' could not find target; "
                    f"falling back to natural sort order",
                    file=sys.stderr,
                )
                items.append(L)
            else:
                items.insert(target_idx + 1, L)
        # Pass 1 packs everything except align_with hints. align_with
        # remains a same-level snap handled in pass 2.
        regular = [L for L in items if "align_with" not in L["p"]]
        aligned = [L for L in items if "align_with" in L["p"]]
        levels: list[list[dict]] = []
        prev_level = 0
        for i, L in enumerate(regular):
            min_level = 0 if i == 0 else prev_level
            lvl = min_level
            while True:
                if lvl >= len(levels):
                    levels.append([])
                if _x_fits(L, levels[lvl]):
                    levels[lvl].append(L)
                    L["level"] = lvl
                    prev_level = lvl
                    break
                lvl += 1
        # Pass 2: align_with platforms snap to the target's level if
        # the x-range fits there; otherwise they fall through to a
        # normal greedy placement and a warning is emitted.
        for L in aligned:
            target_id = L["p"]["align_with"]
            target = by_id.get(target_id)
            placed = False
            if target is not None and target.get("region") == region \
               and "level" in target and _x_fits(L, levels[target["level"]]):
                levels[target["level"]].append(L)
                L["level"] = target["level"]
                placed = True
            if not placed:
                if target is not None:
                    print(
                        f"warning: align_with={target_id} for "
                        f"'{L['p']['label']}' could not be honored "
                        f"(x-range conflict or different region); "
                        f"falling back to greedy placement",
                        file=sys.stderr,
                    )
                lvl = 0
                while True:
                    if lvl >= len(levels):
                        levels.append([])
                    if _x_fits(L, levels[lvl]):
                        levels[lvl].append(L)
                        L["level"] = lvl
                        break
                    lvl += 1
        region_levels[region] = levels

    # Compute the stack height (top-of-topmost-box → bottom-of-level-0) per
    # region. The tallest region anchors track_bottom at g.track_top + its
    # height; shorter regions also have level 0 at that shared track_bottom
    # so SC qubits, Photonic QC, etc. all sit on the same baseline.
    region_stack_h: dict[int, float] = {}
    for region, levels in region_levels.items():
        levels_h = [max(b["box_h"] for b in lvl) for lvl in levels]
        region_stack_h[region] = sum(levels_h) + (len(levels) - 1) * INTER_TRACK_GAP

    g.track_bottom = g.track_top + max(region_stack_h.values())

    for region, levels in region_levels.items():
        bottom = g.track_bottom
        for lvl_idx, lvl_boxes in enumerate(levels):
            level_h = max(b["box_h"] for b in lvl_boxes)
            for L in lvl_boxes:
                L["box_bot"] = bottom
                L["box_top"] = bottom - L["box_h"]
            bottom = bottom - level_h - INTER_TRACK_GAP


def _warn_track_overlaps(layouts: list[dict]) -> None:
    """Print a warning to stderr for any pair of platform boxes whose
    final 2D footprints intersect. Catches both same-track horizontal
    collisions and cross-track collisions (e.g. a tall multi-line box
    extending upward into the row above)."""
    n = len(layouts)
    for i in range(n):
        a = layouts[i]
        for j in range(i + 1, n):
            b = layouts[j]
            x_overlap = min(a["xr"], b["xr"]) - max(a["xl"], b["xl"])
            y_overlap = min(a["box_bot"], b["box_bot"]) - max(a["box_top"], b["box_top"])
            if x_overlap > 0 and y_overlap > 0:
                print(
                    f"warning: '{a['p']['label']}' overlaps "
                    f"'{b['p']['label']}' by {x_overlap:.0f}×{y_overlap:.0f}px "
                    f"(shrink content, raise track, or rework layout)",
                    file=sys.stderr,
                )


def platform_extent(p: dict, g: Geom) -> tuple[float, float, list[float]]:
    """Return (x_left, x_right, anchor_xs) in canvas coords."""
    if "freq_range_hz" in p:
        a = g.x_of_hz(p["freq_range_hz"][0])
        b = g.x_of_hz(p["freq_range_hz"][1])
    elif "wavelength_range_nm" in p:
        nm_lo, nm_hi = p["wavelength_range_nm"]
        a = g.x_of_nm(nm_hi)  # longer wavelength → lower freq → smaller x
        b = g.x_of_nm(nm_lo)
    else:
        x = g.x_of_nm(p["wavelength_nm"])
        a = b = x
    x_left, x_right = min(a, b), max(a, b)
    anchors = [a] if a == b else [a, b]
    return x_left, x_right, anchors


# ---------- SVG composition ----------

STYLE = """
text { fill: #222; }
.title       { font-size: 22px; font-weight: 700; fill: #111; }
.region      { font-size: 11px; letter-spacing: 2px; fill: #888; font-weight: 600; }
.tick        { font-size: 11px; fill: #333; }
.tick-sub    { font-size: 10px; fill: #777; }
.p-name      { font-weight: 700; font-size: 13px; fill: #111; }
.p-sub       { font-weight: 700; font-size: 10.5px; fill: #222; }
.vendor      { font-weight: 700; font-size: 10.5px; fill: #555; }
.legend-h    { font-size: 11px; fill: #444; font-weight: 600; }
.legend      { font-size: 10px; fill: #444; }
.itu-letter  { font-size: 11px; fill: #555; font-weight: 600; }
.ann-label   { font-size: 12px; font-weight: 700; }
.ann-sub     { font-size: 10px; fill: #555; }
.machines-h  { font-size: 12px; font-weight: 700; fill: #222; }
.machines-p  { font-size: 10.5px; font-weight: 700; fill: #222; }
.machines-v  { font-size: 10.5px; fill: #444; }
.timestamp   { font-size: 9px; fill: #999; }
.cap-chip    { font-size: 9px; font-weight: 700; }
"""


PAGE_BG = "#fdfdfb"


def _rainbow_defs(g: Geom, stops: list[dict]) -> list[str]:
    stop_xs = [g.x_of_nm(s["nm"]) for s in stops]
    x_lo, x_hi = min(stop_xs), max(stop_xs)
    span = (x_hi - x_lo) or 1
    parts = [
        f'<linearGradient id="rainbow" x1="{x_lo:.1f}" y1="0" '
        f'x2="{x_hi:.1f}" y2="0" gradientUnits="userSpaceOnUse">'
    ]
    for s, sx in zip(stops, stop_xs):
        parts.append(
            f'<stop offset="{(sx - x_lo) / span * 100:.1f}%" '
            f'stop-color="{esc(s["color"])}"/>'
        )
    parts.append("</linearGradient>")
    return parts


def _arrow_marker_def(marker_id: str, color: str) -> str:
    return (
        f'<marker id="{esc(marker_id)}" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="8" markerHeight="8" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 Z" fill="{esc(color)}"/></marker>'
    )


def _stagger_rows(xs: list[float], min_gap: float, n_rows: int = 2) -> list[int]:
    """Assign each x to a row 0..n_rows-1 so labels in each row stay >= min_gap
    apart. Used to stagger crowded axis ticks."""
    last_x_per_row = [-math.inf] * n_rows
    rows = []
    for x in xs:
        for r in range(n_rows):
            if x - last_x_per_row[r] >= min_gap:
                rows.append(r)
                last_x_per_row[r] = x
                break
        else:
            rows.append(n_rows - 1)
            last_x_per_row[-1] = x
    return rows


def render_svg(data: dict) -> str:
    cv = data["canvas"]
    g = Geom(cv, data["freq_axis"], data["tracks"])

    # ---- Build platform layouts and run greedy per-region stacking ----
    # Done up-front so g.track_top can reflect the actual stacking before
    # downstream rendering uses it (region shading, ITU strip, etc.).
    layouts: list[dict] = []
    for p in data["platforms"]:
        if p.get("hidden"):
            continue
        xl_nat, xr_nat, anchors = platform_extent(p, g)
        center = (xl_nat + xr_nat) / 2
        body_lines = [
            ("p-name", esc(p["label"])),
            ("p-sub",  esc(p["subtitle"])),
        ]
        vendor_rows = list(p["vendor_lines"]) if "vendor_lines" in p \
            else [" · ".join(p["vendors"])]
        if p.get("academic"):
            vendor_rows.append(p["academic"])
        for v in vendor_rows:
            body_lines.append(("vendor", esc(v)))
        # Box width = content width with uniform PAD_X margins.
        target_w = content_box_width(body_lines)
        xl, xr = center - target_w / 2, center + target_w / 2
        if xl < g.x0 + 4:
            xr += (g.x0 + 4) - xl
            xl = g.x0 + 4
        if xr > g.x1 - 4:
            xl -= xr - (g.x1 - 4)
            xr = g.x1 - 4
        layouts.append({
            "p": p, "xl": xl, "xr": xr, "anchors": anchors,
            "box_h": box_height_for(len(body_lines)),
            "body_lines": body_lines,
            "color": p["color"],
            "is_range": "wavelength_range_nm" in p or "freq_range_hz" in p,
        })

    compute_stacking(layouts, g)
    if layouts:
        g.track_top = min(L["box_top"] for L in layouts)

    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {g.W} {g.H}" '
        f'width="{g.W}" height="{g.H}" '
        f'font-family="Helvetica, Arial, sans-serif">',
        f"<style>{STYLE}</style>",
    ]

    # All <defs> in one place: rainbow gradient + per-annotation arrowheads.
    defs: list[str] = []
    if data.get("rainbow_stops"):
        defs.extend(_rainbow_defs(g, data["rainbow_stops"]))
    for i, ann in enumerate(data.get("annotations", [])):
        defs.append(_arrow_marker_def(f"arrow-{i}", ann.get("color", "#444")))
    if defs:
        out.append("<defs>")
        out.extend(defs)
        out.append("</defs>")

    out.append(rect(0, 0, g.W, g.H, fill=PAGE_BG))

    # Region shading. Each region spans the visible segments + the gap
    # between them; the rainbow region uses a gradient fill, others a tint.
    region_top = g.track_top - 10
    region_bot = g.track_bottom + 60
    for r in data.get("regions", []):
        if r.get("gradient") == "rainbow":
            fill, opacity = "url(#rainbow)", 0.42
        else:
            fill, opacity = r["color"], 0.55
        for xl, xr in g.x_ranges_in(r["from_hz"], r["to_hz"]):
            out.append(rect(xl, region_top, xr - xl, region_bot - region_top,
                            fill=fill, opacity=opacity))

    out.append(text(g.x0, 28, esc(data["title"]), cls="title"))

    # ITU fibre bands: full-height semi-transparent vertical strips behind
    # the platforms (so each band's range is visible at a glance), plus a
    # colored top bar with letter labels. Strip is anchored close to the
    # title (~34 px gap title-baseline → ULCSEO letter-baseline) so the
    # chart header stays compact.
    strip_h = 14
    strip_top = 70
    band_top_for_strip = strip_top + strip_h
    for b in data["fiber_bands"]:
        xl, xr = g.x_of_nm(b["range_nm"][1]), g.x_of_nm(b["range_nm"][0])
        emph = bool(b.get("emphasis"))
        out.append(rect(xl, band_top_for_strip, xr - xl,
                        region_bot - band_top_for_strip,
                        fill=b["color"], opacity=0.22 if emph else 0.14))
        # Top colored bar + letter
        out.append(rect(
            xl, strip_top - (4 if emph else 0), xr - xl, strip_h + (4 if emph else 0),
            fill=b["color"], stroke="#222" if emph else "#666",
            stroke_width=1.4 if emph else 0.6, rx=2, ry=2,
        ))
        out.append(text((xl + xr) / 2, strip_top - 8, esc(b["id"]),
                        cls="itu-letter", text_anchor="middle",
                        font_weight="800" if emph else "600"))

    # ITU fibre band legend — placed inside the chart, in the otherwise
    # empty microwave region (left segment, above the SC qubits track).
    legend_x = g.seg_xs[0][0] + 8
    legend_y = g.track_top + 12
    out.append(text(legend_x, legend_y, "ITU-T fibre bands",
                    cls="legend-h"))
    for i, b in enumerate(data["fiber_bands"]):
        row_y = legend_y + 16 + i * 14
        weight = "700" if b.get("emphasis") else "400"
        # color swatch
        out.append(rect(legend_x, row_y - 8, 10, 10,
                        fill=b["color"], stroke="#666", stroke_width=0.5))
        body = (f'<tspan font-weight="700">{esc(b["id"])}</tspan>  '
                f'{b["range_nm"][0]}–{b["range_nm"][1]} nm  · "{esc(b["name"])}"')
        out.append(text(legend_x + 16, row_y, body, cls="legend", font_weight=weight))

    # Sanity check: warn on horizontal overlap between boxes that share a
    # track. The vertical-track scheme assumes boxes on the same row don't
    # collide; if they do, the chart is misleading.
    _warn_track_overlaps(layouts)

    # Pass 1: dotted anchor leaders for every platform. Drawn before any
    # box so the line is naturally obscured where it passes behind a
    # lower-track box, and clearly visible in the open space — making
    # which axis dot belongs to which box unambiguous.
    axis_dot_y = g.track_bottom + 6
    for L in layouts:
        for ax in L["anchors"]:
            out.append(line(ax, L["box_bot"], ax, axis_dot_y,
                            stroke=L["color"], stroke_opacity=0.95,
                            stroke_width=1.6, stroke_dasharray="3,3"))

    # Pass 2: boxes, text, anchor notches, axis dots, range extent lines.
    for L in layouts:
        xl, xr = L["xl"], L["xr"]
        box_top, box_bot, color = L["box_top"], L["box_bot"], L["color"]
        # Opaque pastel fill (color blended with white) so the rainbow
        # and ITU strips behind don't show through the box; full-colour
        # border. The chart now uses capability chips (C/M/S) at top-
        # right of each box to convey compute / memory / source role
        # support, replacing the previous dashed-vs-solid distinction
        # (which conveyed a single primary kind and was hard to spot).
        out.append(rect(xl, box_top, xr - xl, L["box_h"],
                        rx=6, ry=6, fill=lighten(color),
                        stroke=color, stroke_width=1.5))
        for i, (cls, body) in enumerate(L["body_lines"]):
            y = box_top + FIRST_BASELINE_DY + i * LINE_GAP
            out.append(text(xl + PAD_X, y, body, cls=cls))
        out.extend(render_capability_chips(
            xl, box_top, xr, color, L["p"].get("roles"),
        ))
        for ax in L["anchors"]:
            if xl <= ax <= xr:
                out.append(line(ax, box_bot - 4, ax, box_bot,
                                stroke=color, stroke_width=2))
            out.append(circle(ax, axis_dot_y, 3, fill=color))
        if L["is_range"] and len(L["anchors"]) == 2:
            a1, a2 = sorted(L["anchors"])
            out.append(line(a1, box_bot, a2, box_bot,
                            stroke=color, stroke_width=1.5))

    # X-axis: one solid line per segment + a zigzag break marker per gap.
    axis_y = g.track_bottom + 6
    for xa, xb in g.seg_xs:
        out.append(line(xa, axis_y, xb, axis_y, stroke="#333", stroke_width=1.2))
    for ga, gb in g.gap_xs:
        cx = (ga + gb) / 2
        out.append(rect(ga - 1, axis_y - 4, gb - ga + 2, 9, fill=PAGE_BG))
        for off in (-6, 6):
            out.append(line(cx + off - 3, axis_y + 5, cx + off + 3, axis_y - 5,
                            stroke="#333", stroke_width=1.2))

    # Tick marks + dual labels. Skip ticks inside a gap; stagger labels in
    # up to two rows so close neighbours don't collide.
    ticks = [t for t in sorted(data["axis_ticks"], key=lambda t: t["hz"])
             if g.hz_visible(t["hz"])]
    tick_xs = [g.x_of_hz(tk["hz"]) for tk in ticks]
    rows = _stagger_rows(tick_xs, min_gap=50, n_rows=2)
    for tk, x, row in zip(ticks, tick_xs, rows):
        out.append(line(x, axis_y, x, axis_y + 6, stroke="#333", stroke_width=1))
        y_main = axis_y + 20 + row * 24
        out.append(text(x, y_main, esc(tk["label"]),
                        cls="tick", text_anchor="middle"))
        out.append(text(x, y_main + 13, esc(tk["wavelength"]),
                        cls="tick-sub", text_anchor="middle"))

    # Region labels. Each region may set label_at_hz (default: midpoint) and
    # label_row (default: 0) to nudge crowded labels onto a second row.
    region_label_y0 = axis_y + 76
    for r in data.get("regions", []):
        cx = g.x_of_hz(r.get("label_at_hz", (r["from_hz"] + r["to_hz"]) / 2))
        y = region_label_y0 + r.get("label_row", 0) * 16
        out.append(text(cx, y, esc(r["label"]),
                        cls="region", text_anchor="middle"))

    # Bottom annotations (M-O transducer + QFC) — both arrows on the SAME
    # horizontal line, converging at the C-band tip. Each label sits over
    # the midpoint of its own arrow; midpoints fall in different x ranges
    # (one in the broken-axis gap, one in the visible region) so the two
    # labels don't collide.
    ann_y = region_label_y0 + 44
    for i, ann in enumerate(data.get("annotations", [])):
        x_from, x_to = g.x_of_hz(ann["from_hz"]), g.x_of_hz(ann["to_hz"])
        col = ann.get("color", "#444")
        out.append(line(x_from, ann_y, x_to, ann_y,
                        stroke=col, stroke_width=1.8,
                        marker_end=f"url(#arrow-{i})"))
        cx = (x_from + x_to) / 2
        out.append(text(cx, ann_y - 6, esc(ann["label"]),
                        cls="ann-label", text_anchor="middle", fill=col))
        out.append(text(cx, ann_y + 16, esc(ann["sublabel"]),
                        cls="ann-sub", text_anchor="middle"))

    # Flagship-machines table — split into two columns: Quantum Computers
    # on the left, Quantum Memories / Sources on the right. *Asterisks*
    # in the source data mark future-planned names (rendered bold).
    machines = data.get("flagship_machines") or {}
    if machines:
        # Bottom of the deepest annotation text (both arrows now share one
        # horizontal level, so the lowest text is the single sublabel row
        # at ann_y + 16). Was previously over-estimated for stacked arrows.
        last_ann_y = ann_y + 16 if data.get("annotations") else region_label_y0 + 44

        comp = [p for p in data["platforms"]
                if p["id"] in machines and p.get("kind") not in ("memory", "source")]
        mem = [p for p in data["platforms"]
               if p["id"] in machines and p.get("kind") in ("memory", "source")]

        col_left_x = g.x0
        col_right_x = g.x0 + 760
        sub_y = last_ann_y + 36   # column sub-headers; both at same y

        out.append(text(
            col_left_x, sub_y,
            text_with_bold("Quantum Computers  — *bold* = future / planned"),
            cls="machines-p",
        ))
        out.append(text(col_right_x, sub_y, esc("Quantum Memories & Sources"),
                        cls="machines-p"))

        # Each column lays out rows independently with its own platform-name
        # column width so vendor text lines up cleanly within each column.
        def render_column(platforms: list[dict], col_x: float, y_start: float):
            if not platforms:
                return
            name_w = max(measure_text(p["label"], "p-sub") for p in platforms) + 24
            for i, p in enumerate(platforms):
                row_y = y_start + i * 16
                sw_x = col_x + 4
                dashed = p.get("kind") in ("memory", "source")
                out.append(circle(sw_x, row_y - 4, 4.5,
                                  fill=lighten(p["color"], 0.5),
                                  stroke=p["color"], stroke_width=1.2,
                                  stroke_dasharray="2,1.5" if dashed else None))
                out.append(text(sw_x + 12, row_y, esc(p["label"]),
                                cls="machines-p"))
                out.append(text(col_x + name_w, row_y,
                                text_with_bold(machines[p["id"]]),
                                cls="machines-v"))

        rows_y = sub_y + 18
        render_column(comp, col_left_x, rows_y)
        render_column(mem, col_right_x, rows_y)

    # Top-right timestamp so the rendered chart carries its build time.
    ts = datetime.now().strftime("%Y%m%d-%H:%M:%S")
    out.append(text(g.W - cv["margin"]["right"] - 2,
                    cv["margin"]["top"] + 4,
                    esc(ts), cls="timestamp", text_anchor="end"))

    out.append("</svg>")
    return "\n".join(out)


# ---------- CLI ----------

def main() -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=str(here / "data.yaml"),
                    help="Path to data.yaml (default: ./data.yaml)")
    ap.add_argument("--format", choices=["svg", "png", "pdf"], default="svg")
    ap.add_argument("-o", "--output", default=None,
                    help="Output path (default: ./output/spectrum.<fmt>)")
    args = ap.parse_args()

    data = load_data(Path(args.data))
    svg = render_svg(data)

    out_dir = here / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = Path(args.output) if args.output else out_dir / f"spectrum.{args.format}"

    if args.format == "svg":
        out_path.write_text(svg, encoding="utf-8")
    else:
        try:
            import cairosvg  # type: ignore
        except ImportError:
            print("error: --format png|pdf requires cairosvg. Install with:\n"
                  "  pip install cairosvg", file=sys.stderr)
            return 2
        kwargs = {"bytestring": svg.encode("utf-8"), "write_to": str(out_path)}
        if args.format == "png":
            cairosvg.svg2png(output_width=2 * data["canvas"]["width"], **kwargs)
        else:
            cairosvg.svg2pdf(**kwargs)

    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
