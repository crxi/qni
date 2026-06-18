/**
 * geom.ts — coordinate mapping for the broken/segmented log frequency axis.
 *
 * Direct port of render.py's Geom class. Same data.yaml shapes the same
 * positions in both pipelines.
 */

import type { SpectrumData, FreqSegment } from "./data";

export const C_M_S = 299_792_458;

export function hzOfNm(nm: number): number {
  return C_M_S / (nm * 1e-9);
}

export class Geom {
  W: number;
  H: number;
  x0: number;
  x1: number;
  segments: FreqSegment[];
  gapPct: number;
  segXs: [number, number][];
  gapXs: [number, number][];
  trackTop: number;
  trackBottom: number;

  constructor(data: SpectrumData) {
    const { canvas, freq_axis, tracks } = data;
    const m = canvas.margin;
    this.W = canvas.width;
    this.H = canvas.height;
    this.x0 = m.left;
    this.x1 = this.W - m.right;
    this.segments = freq_axis.segments;
    this.gapPct = freq_axis.gap_pct ?? 6;

    const plotW = this.x1 - this.x0;
    const nSeg = this.segments.length;
    const nGap = Math.max(0, nSeg - 1);
    const gapW = nGap > 0 ? plotW * (this.gapPct / 100) : 0;
    const segWTotal = plotW - gapW * nGap;
    const segWPctTotal = this.segments.reduce((a, s) => a + s.width_pct, 0);

    this.segXs = [];
    let cursor = this.x0;
    for (const s of this.segments) {
      const w = segWTotal * (s.width_pct / segWPctTotal);
      this.segXs.push([cursor, cursor + w]);
      cursor += w + gapW;
    }
    this.gapXs = [];
    for (let i = 0; i < nSeg - 1; i++) {
      this.gapXs.push([this.segXs[i][1], this.segXs[i + 1][0]]);
    }

    this.trackTop = (tracks as { top_y: number }).top_y;
    this.trackBottom = this.trackTop;
  }

  xOfHz(hz: number): number {
    for (let i = 0; i < this.segments.length; i++) {
      const s = this.segments[i];
      const [xa, xb] = this.segXs[i];
      if (hz >= s.min_hz && hz <= s.max_hz) {
        const lo = Math.log10(s.min_hz);
        const hi = Math.log10(s.max_hz);
        return xa + ((Math.log10(hz) - lo) / (hi - lo)) * (xb - xa);
      }
    }
    for (let i = 0; i < this.segments.length - 1; i++) {
      const fLeft = this.segments[i].max_hz;
      const fRight = this.segments[i + 1].min_hz;
      if (hz > fLeft && hz < fRight) {
        const xbLeft = this.segXs[i][1];
        const xaRight = this.segXs[i + 1][0];
        const lo = Math.log10(fLeft);
        const hi = Math.log10(fRight);
        return xbLeft + ((Math.log10(hz) - lo) / (hi - lo)) * (xaRight - xbLeft);
      }
    }
    if (hz < this.segments[0].min_hz) return this.segXs[0][0];
    return this.segXs[this.segXs.length - 1][1];
  }

  xOfNm(nm: number): number {
    return this.xOfHz(hzOfNm(nm));
  }

  hzVisible(hz: number): boolean {
    return this.segments.some((s) => hz >= s.min_hz && hz <= s.max_hz);
  }

  /** Visible canvas x-ranges for [loHz, hiHz], including gaps so backgrounds span. */
  xRangesIn(loHz: number, hiHz: number): [number, number][] {
    const intervals: [number, number][] = [];
    for (let i = 0; i < this.segments.length; i++) {
      intervals.push([this.segments[i].min_hz, this.segments[i].max_hz]);
      if (i < this.segments.length - 1) {
        intervals.push([this.segments[i].max_hz, this.segments[i + 1].min_hz]);
      }
    }
    const out: [number, number][] = [];
    for (const [fLo, fHi] of intervals) {
      const a = Math.max(loHz, fLo);
      const b = Math.min(hiHz, fHi);
      if (a < b) out.push([this.xOfHz(a), this.xOfHz(b)]);
    }
    return out;
  }
}
