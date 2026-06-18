"""Tiny SVG-building library with bounding-box bookkeeping.

Why this exists: hand-editing 4hop-topology.svg meant every coordinate had
to be recomputed in my head every time something moved, and labels routinely
overlapped after a tweak. This library keeps a registry of element bboxes
so a final overlap check can flag collisions before the SVG ships.

Conventions
-----------
* All coordinates are in viewBox units.
* Text bbox uses a heuristic: width = 0.55 * font_size * len(text), height =
  font_size. Good enough to catch obvious collisions; not glyph-accurate.
* Elements track an optional `name` so collision reports point at the
  offender by name rather than by raw coords.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


def _inject_attr(svg: str, attr: str, value: str) -> str:
    """Insert `attr="value"` into the opening tag of a leaf SVG element.

    The svglib emitters return self-contained snippets like
    `<circle cx=… cy=… r=…/>`. We find the tag's name and inject a new
    attribute after it. Safe to call only on opening leaf tags.
    """
    safe = value.replace('"', "&quot;")
    # Match the tag name (e.g. "circle", "rect") immediately after "<".
    return re.sub(r"^<([a-zA-Z][a-zA-Z0-9]*)\b", rf'<\1 {attr}="{safe}"', svg, count=1)


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


@dataclass
class BBox:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def overlaps(self, other: "BBox", pad: float = 0.0) -> bool:
        return not (
            self.right + pad <= other.x
            or other.right + pad <= self.x
            or self.bottom + pad <= other.y
            or other.bottom + pad <= self.y
        )


@dataclass
class Element:
    svg: str
    bbox: BBox | None = None
    kind: str = "shape"  # "text" | "shape" | "guide"
    name: str = ""


@dataclass
class Canvas:
    """Top-level SVG canvas. Collects elements + style defs + symbol defs."""

    width: float
    height: float
    title: str = ""
    css: str = ""
    extra_defs: list[str] = field(default_factory=list)
    elements: list[Element] = field(default_factory=list)

    # -- registration ------------------------------------------------------

    def add(
        self,
        svg: str,
        bbox: BBox | None = None,
        kind: str = "shape",
        name: str = "",
    ) -> None:
        # Surface the `name=` tag in the emitted SVG as a `data-name`
        # attribute. Downstream JS (animations, interactivity) can then
        # locate each named element by stable selector without us having
        # to mint per-call `**extra` kwargs in every primitive.
        if name and not svg.startswith("</"):
            svg = _inject_attr(svg, "data-name", name)
        self.elements.append(Element(svg=svg, bbox=bbox, kind=kind, name=name))

    def add_def(self, svg: str) -> None:
        self.extra_defs.append(svg)

    def begin_group(self, **extra) -> None:
        """Open a `<g>` wrapping every subsequent primitive until `end_group()`.

        Useful for tagging a logical region (a row, a side, an operation step)
        with `data-*` attributes that downstream JS animation can target.
        Groups can nest. Each `begin_group` must be matched by `end_group`.
        Kwargs are emitted as kebab-case attributes (`data_op_row` → `data-op-row`).
        """
        attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in extra.items())
        self.add(f"<g {attrs}>" if attrs else "<g>", kind="open-group")

    def end_group(self) -> None:
        self.add("</g>", kind="close-group")

    # -- primitives --------------------------------------------------------

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        cls: str = "",
        rx: float = 0,
        style: str = "",
        name: str = "",
    ) -> None:
        attrs = [f'x="{x}"', f'y="{y}"', f'width="{w}"', f'height="{h}"']
        if rx:
            attrs.append(f'rx="{rx}"')
        if cls:
            attrs.append(f'class="{cls}"')
        if style:
            attrs.append(f'style="{style}"')
        self.add(f"<rect {' '.join(attrs)}/>", BBox(x, y, w, h), "shape", name)

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        cls: str = "",
        style: str = "",
        name: str = "",
    ) -> None:
        attrs = [f'cx="{cx}"', f'cy="{cy}"', f'r="{r}"']
        if cls:
            attrs.append(f'class="{cls}"')
        if style:
            attrs.append(f'style="{style}"')
        self.add(
            f"<circle {' '.join(attrs)}/>",
            BBox(cx - r, cy - r, 2 * r, 2 * r),
            "shape",
            name,
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        cls: str = "",
        style: str = "",
        name: str = "",
    ) -> None:
        attrs = [f'x1="{x1}"', f'y1="{y1}"', f'x2="{x2}"', f'y2="{y2}"']
        if cls:
            attrs.append(f'class="{cls}"')
        if style:
            attrs.append(f'style="{style}"')
        # Line bbox is the axis-aligned bounding box of the segment.
        x, y = min(x1, x2), min(y1, y2)
        w, h = abs(x2 - x1), abs(y2 - y1)
        self.add(
            f"<line {' '.join(attrs)}/>",
            BBox(x, y, w or 1, h or 1),
            "guide",
            name,
        )

    def path(self, d: str, cls: str = "", style: str = "", name: str = "", **extra) -> None:
        attrs = [f'd="{d}"']
        if cls:
            attrs.append(f'class="{cls}"')
        if style:
            attrs.append(f'style="{style}"')
        for k, v in extra.items():
            attrs.append(f'{k.replace("_", "-")}="{v}"')
        # No bbox for paths (would need to parse `d`). Caller passes None;
        # overlap check ignores it.
        self.add(f"<path {' '.join(attrs)}/>", None, "shape", name)

    def text(
        self,
        x: float,
        y: float,
        s: str,
        cls: str = "",
        font_size: float = 10,
        anchor: str = "middle",
        style: str = "",
        name: str = "",
        raw: bool = False,
    ) -> None:
        """Add a text element with a heuristic bbox.

        anchor: "start" | "middle" | "end" — controls x reference of the bbox.
        font_size: must be set explicitly if `cls` does not encode it, so the
            bbox heuristic gets the right width.
        raw: if True, `s` may contain inline SVG (e.g. <tspan>); skips XML
            escape. Caller is responsible for safe content.
        """
        attrs = [f'x="{x}"', f'y="{y}"']
        if cls:
            attrs.append(f'class="{cls}"')
        # text-anchor MUST go in the inline style attribute (not as a
        # presentation attribute), because class CSS in <style> beats SVG
        # presentation attributes — so `.mini { text-anchor: middle }`
        # would silently override `text-anchor="start"` and centre the label
        # over its slot anchor. Inline style beats class CSS.
        style_parts = []
        if anchor:
            style_parts.append(f"text-anchor:{anchor}")
        if style:
            style_parts.append(style)
        if style_parts:
            attrs.append(f'style="{";".join(style_parts)}"')
        body = s if raw else _xml_escape(s)
        # Heuristic bbox. Ignore tspans inside `s` — they affect width but
        # we don't parse them.
        # Approximate character count by stripping tspan markup.
        import re

        plain = re.sub(r"<[^>]+>", "", s)
        approx_w = 0.55 * font_size * max(len(plain), 1)
        approx_h = font_size
        if anchor == "start":
            bx = x
        elif anchor == "end":
            bx = x - approx_w
        else:  # middle
            bx = x - approx_w / 2
        by = y - approx_h * 0.8  # baseline is near bottom of bbox
        self.add(
            f"<text {' '.join(attrs)}>{body}</text>",
            BBox(bx, by, approx_w, approx_h),
            "text",
            name,
        )

    def use(
        self,
        href: str,
        x: float,
        y: float,
        width: float,
        height: float,
        name: str = "",
        **extra,
    ) -> None:
        """Reference a `<symbol>` defined in extra_defs."""
        attrs = [f'href="{href}"', f'x="{x}"', f'y="{y}"', f'width="{width}"', f'height="{height}"']
        for k, v in extra.items():
            attrs.append(f'{k.replace("_", "-")}="{v}"')
        self.add(
            f"<use {' '.join(attrs)}/>",
            BBox(x, y, width, height),
            "shape",
            name,
        )

    def group(self, body: str, transform: str = "", name: str = "") -> None:
        attrs = []
        if transform:
            attrs.append(f'transform="{transform}"')
        self.add(f"<g {' '.join(attrs)}>{body}</g>", None, "shape", name)

    # -- render ------------------------------------------------------------

    def to_svg(self) -> str:
        defs_block = ""
        if self.css or self.extra_defs:
            parts = ["<defs>"]
            if self.css:
                parts.append(f"<style>{self.css}</style>")
            parts.extend(self.extra_defs)
            parts.append("</defs>")
            defs_block = "\n  ".join(parts)
        title = f'\n  <title>{_xml_escape(self.title)}</title>' if self.title else ""
        body = "\n  ".join(e.svg for e in self.elements)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {self.width} {self.height}" role="img">'
            f"{title}\n  "
            f"{defs_block}\n  "
            f"{body}\n"
            f"</svg>\n"
        )

    # -- overlap check -----------------------------------------------------

    def check_text_overlaps(self, pad: float = 1.0) -> list[tuple[Element, Element]]:
        """Return pairs of overlapping text bboxes."""
        texts = [e for e in self.elements if e.kind == "text" and e.bbox]
        bad: list[tuple[Element, Element]] = []
        for i, a in enumerate(texts):
            for b in texts[i + 1 :]:
                if a.bbox.overlaps(b.bbox, pad=pad):
                    bad.append((a, b))
        return bad


def render_png(svg_path: str, png_path: str, output_width: int = 1600) -> None:
    """Convenience wrapper around cairosvg for previewing."""
    import cairosvg

    cairosvg.svg2png(
        url=svg_path,
        write_to=png_path,
        output_width=output_width,
        background_color="white",
    )
