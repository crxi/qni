/**
 * chart-helpers.ts — small utilities shared across chart components.
 */

import type { Geom } from "./geom";
import type { PlatformBase } from "./data";
import {
  boxHeightFor, PAD_X, CHIP_STRIP_W, CHIP_PAD_LEFT, type PlatformLayout,
} from "./stacking";
import { measureText, maxLineWidth } from "./text-metrics";

/** Blend a #rrggbb color toward white. amount=1 → white, 0 → original. */
export function lighten(hex: string, amount = 0.78): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const mix = (c: number) => Math.round(c * (1 - amount) + 255 * amount);
  return `#${mix(r).toString(16).padStart(2, "0")}${mix(g).toString(16).padStart(2, "0")}${mix(b).toString(16).padStart(2, "0")}`;
}

/** Convert *foo* asterisk-bold markers to <strong> tags (HTML output). */
export function textWithBoldHtml(s: string): string {
  return s.replace(/&/g, "&amp;")
    .replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*([^*]+)\*/g, '<strong class="future">$1</strong>');
}

/** Build initial layout for a platform (xl, xr, anchors, body lines, height). */
export function platformExtent(
  p: PlatformBase,
  g: Geom,
): { xl: number; xr: number; anchors: number[]; isRange: boolean } {
  let a: number, b: number;
  if (p.freq_range_hz) {
    a = g.xOfHz(p.freq_range_hz[0]);
    b = g.xOfHz(p.freq_range_hz[1]);
  } else if (p.wavelength_range_nm) {
    const [lo, hi] = p.wavelength_range_nm;
    a = g.xOfNm(hi);
    b = g.xOfNm(lo);
  } else {
    a = b = g.xOfNm(p.wavelength_nm!);
  }
  const xl = Math.min(a, b), xr = Math.max(a, b);
  const anchors = a === b ? [a] : [a, b];
  return { xl, xr, anchors, isRange: a !== b };
}

export function buildLayout(p: PlatformBase, g: Geom): PlatformLayout {
  const { xl: xlNat, xr: xrNat, anchors, isRange } = platformExtent(p, g);
  const center = (xlNat + xrNat) / 2;

  const bodyLines: PlatformLayout["bodyLines"] = [
    { cls: "p-name", text: p.label },
  ];
  if (p.subtitle) bodyLines.push({ cls: "p-sub", text: p.subtitle });
  const vendorRows = p.vendor_lines ?? (p.vendors ? [p.vendors.join(" · ")] : []);
  for (const v of vendorRows) bodyLines.push({ cls: "vendor", text: v });
  if (p.academic) bodyLines.push({ cls: "vendor", text: p.academic });

  // Box width must fit the widest content line plus PAD_X each side,
  // AND leave room for the capability chip strip on the title row
  // (chips sit at top-right; only the title shares its y, so only the
  // title needs to clear the strip). content_box_width() in render.py
  // does the equivalent calculation; keep them in sync.
  const titleW = measureText(p.label, "p-name");
  const otherW = bodyLines
    .filter((l) => l.cls !== "p-name")
    .reduce((m, l) => Math.max(m, measureText(l.text, l.cls)), 0);
  const titleNeed = titleW + PAD_X + CHIP_PAD_LEFT + CHIP_STRIP_W;
  const otherNeed = otherW + 2 * PAD_X;
  const targetW = Math.max(titleNeed, otherNeed);
  let xl = center - targetW / 2;
  let xr = center + targetW / 2;
  if (xl < g.x0 + 4) { xr += g.x0 + 4 - xl; xl = g.x0 + 4; }
  if (xr > g.x1 - 4) { xl -= xr - (g.x1 - 4); xr = g.x1 - 4; }

  return {
    p, xl, xr, anchors,
    boxH: boxHeightFor(bodyLines.length),
    isRange,
    bodyLines,
    color: p.color,
    region: 0, level: 0, boxTop: 0, boxBot: 0,
  };
}
