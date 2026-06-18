/**
 * stacking.ts — per-region greedy 1-D rectangle packing for platform
 * glyphs. Direct port of render.py's compute_stacking().
 *
 * Each platform falls into a region (= freq-axis segment its center lies in).
 * Within a region, platforms are sorted by frequency ascending and assigned
 * the lowest level whose existing boxes don't overlap. The monotonic-level
 * constraint ensures higher-frequency platforms end up on higher levels even
 * when they don't overlap anything (so Trapped Ions, isolated at 813 THz,
 * stacks above the lower-freq cluster instead of dropping to level 0).
 *
 * All level heights are natural box heights (3-line: 52 px, 4-line: 66 px),
 * with INTER_TRACK_GAP between each pair of adjacent levels. Both regions
 * share the level-0 baseline so SC qubits and Photonic QC sit at the same y.
 */

import type { Geom } from "./geom";
import type { PlatformBase } from "./data";
import { platformFreqCenter } from "./data";

export const LINE_GAP = 14;
export const FIRST_BASELINE_DY = 17;
export const DESCENDER_PAD = 7;
export const INTER_TRACK_GAP = 16;
export const PAD_X = 10;

/* Capability chip strip (C / M / S) at the top-right of each box.
   These constants match render.py exactly so the Python and web
   pipelines lay out boxes identically. */
export const ROLE_ORDER = ["compute", "memory", "source"] as const;
export const CHIP_LETTER: Record<typeof ROLE_ORDER[number], string> = {
  compute: "C", memory: "M", source: "S",
};
export const CHIP_W = 13;
export const CHIP_GAP = 2;
export const CHIP_PAD_RIGHT = 6;
export const CHIP_PAD_TOP = 4;
export const CHIP_PAD_LEFT = 6;
export const CHIP_STRIP_W =
  CHIP_W * ROLE_ORDER.length + CHIP_GAP * (ROLE_ORDER.length - 1) + CHIP_PAD_RIGHT;

export interface PlatformLayout {
  p: PlatformBase;
  xl: number;
  xr: number;
  anchors: number[];
  boxH: number;
  isRange: boolean;
  region: number;
  level: number;
  boxTop: number;
  boxBot: number;
  /** Lines of text, one per body row (title, subtitle, vendor lines, optional academic). */
  bodyLines: { cls: "p-name" | "p-sub" | "vendor"; text: string }[];
  color: string;
}

export function boxHeightFor(nLines: number): number {
  return FIRST_BASELINE_DY + (nLines - 1) * LINE_GAP + DESCENDER_PAD;
}

function regionFor(layout: { xl: number; xr: number }, g: Geom): number {
  const cx = (layout.xl + layout.xr) / 2;
  for (let i = 0; i < g.segXs.length; i++) {
    const [, xb] = g.segXs[i];
    if (cx <= xb) return i;
  }
  return g.segXs.length - 1;
}

export function computeStacking(layouts: PlatformLayout[], g: Geom): void {
  if (layouts.length === 0) return;

  const byRegion = new Map<number, PlatformLayout[]>();
  for (const L of layouts) {
    L.region = regionFor(L, g);
    const bucket = byRegion.get(L.region) ?? [];
    bucket.push(L);
    byRegion.set(L.region, bucket);
  }

  const byId = new Map<string, PlatformLayout>();
  for (const L of layouts) byId.set(L.p.id, L);

  const xFits = (L: PlatformLayout, lvlBoxes: PlatformLayout[]): boolean =>
    lvlBoxes.every((b) => L.xr <= b.xl || L.xl >= b.xr);

  const regionLevels = new Map<number, PlatformLayout[][]>();
  for (const [region, items] of byRegion) {
    items.sort((a, b) => platformFreqCenter(a.p) - platformFreqCenter(b.p));
    // Honor align_above sort hints: move each hinted platform to
    // immediately after its target in the freq-sorted list, so the
    // monotonic pass-1 placer assigns it a level >= target's and the
    // cascade pushes any later (higher-freq) platforms above it. This
    // matches the Python pipeline.
    const hintItems = items.filter((L) => L.p.align_above);
    for (const L of hintItems) {
      const idx = items.indexOf(L);
      if (idx >= 0) items.splice(idx, 1);
    }
    for (const L of hintItems) {
      const targetId = L.p.align_above!;
      const targetIdx = items.findIndex((T) => T.p.id === targetId);
      if (targetIdx === -1) {
        // eslint-disable-next-line no-console
        console.warn(`align_above=${targetId} for '${L.p.label}' could not find target; falling back to natural sort order`);
        items.push(L);
      } else {
        items.splice(targetIdx + 1, 0, L);
      }
    }
    // align_with remains a same-level snap handled in pass 2.
    const regular = items.filter((L) => !L.p.align_with);
    const aligned = items.filter((L) =>  L.p.align_with);
    const levels: PlatformLayout[][] = [];
    let prevLevel = 0;
    for (let i = 0; i < regular.length; i++) {
      const L = regular[i];
      const minLevel = i === 0 ? 0 : prevLevel;
      let lvl = minLevel;
      for (;;) {
        if (lvl >= levels.length) levels.push([]);
        if (xFits(L, levels[lvl])) {
          levels[lvl].push(L);
          L.level = lvl;
          prevLevel = lvl;
          break;
        }
        lvl++;
      }
    }
    // Pass 2: align_with platforms snap to the target's level if the
    // x-range fits there; otherwise they fall through to a normal
    // greedy placement.
    const regularSet = new Set(regular);
    for (const L of aligned) {
      const targetId = L.p.align_with!;
      const target = byId.get(targetId);
      let placed = false;
      if (
        target &&
        target.region === region &&
        regularSet.has(target) &&
        xFits(L, levels[target.level])
      ) {
        levels[target.level].push(L);
        L.level = target.level;
        placed = true;
      }
      if (!placed) {
        if (target) {
          // eslint-disable-next-line no-console
          console.warn(
            `align_with=${targetId} for '${L.p.label}' could not be honored; falling back to greedy placement`
          );
        }
        let lvl = 0;
        for (;;) {
          if (lvl >= levels.length) levels.push([]);
          if (xFits(L, levels[lvl])) {
            levels[lvl].push(L);
            L.level = lvl;
            break;
          }
          lvl++;
        }
      }
    }
    regionLevels.set(region, levels);
  }

  const regionStackH = new Map<number, number>();
  for (const [region, levels] of regionLevels) {
    const levelsH = levels.map((lvl) => Math.max(...lvl.map((b) => b.boxH)));
    const total = levelsH.reduce((a, h) => a + h, 0) + (levels.length - 1) * INTER_TRACK_GAP;
    regionStackH.set(region, total);
  }
  const maxStack = Math.max(...regionStackH.values());
  g.trackBottom = g.trackTop + maxStack;

  for (const [, levels] of regionLevels) {
    let bottom = g.trackBottom;
    for (const lvlBoxes of levels) {
      const levelH = Math.max(...lvlBoxes.map((b) => b.boxH));
      for (const L of lvlBoxes) {
        L.boxBot = bottom;
        L.boxTop = bottom - L.boxH;
      }
      bottom = bottom - levelH - INTER_TRACK_GAP;
    }
  }
}

export function warnOverlaps(layouts: PlatformLayout[]): string[] {
  const warnings: string[] = [];
  for (let i = 0; i < layouts.length; i++) {
    for (let j = i + 1; j < layouts.length; j++) {
      const a = layouts[i], b = layouts[j];
      const xOverlap = Math.min(a.xr, b.xr) - Math.max(a.xl, b.xl);
      const yOverlap = Math.min(a.boxBot, b.boxBot) - Math.max(a.boxTop, b.boxTop);
      if (xOverlap > 0 && yOverlap > 0) {
        warnings.push(
          `'${a.p.label}' overlaps '${b.p.label}' by ${xOverlap.toFixed(0)}×${yOverlap.toFixed(0)}px`
        );
      }
    }
  }
  return warnings;
}
