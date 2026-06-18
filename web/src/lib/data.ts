/**
 * data.ts — typed access to the spectrum subject's data.yaml. Single
 * source of truth for both render.py (the per-subject Python pipeline
 * at spectrum/render.py) and this shared Astro app.
 */

import dataRaw from "../../../spectrum/data.yaml";
import { hzOfNm } from "./geom";

export interface PlatformBase {
  id: string;
  label: string;
  subtitle?: string;
  color: string;
  kind?: "memory" | "source";
  hidden?: boolean;
  vendors?: string[];
  vendor_lines?: string[];
  freq_range_hz?: [number, number];
  wavelength_nm?: number;
  wavelength_range_nm?: [number, number];
  academic?: string;
  min_width?: number;
  /** Layout hint: snap this platform's box to the same level as the
   * platform with the given id, after the regular greedy pass. Used to
   * reflect family relationships (e.g. Er³⁺ memory aligned with the
   * other rare-earth-ion box) that frequency-only stacking misses. */
  align_with?: string;
  /** Like align_with but places this box on the first level *above*
   * the target where the x-range fits. Used when the box and the
   * target share a family tie but the box's x-range can't fit on the
   * target's level (e.g. NV centre relative to Rare-earth memory). */
  align_above?: string;
  /** Capabilities the platform supports — `compute`, `memory`,
   * `source` (single-photon / entangled-pair). Multiple are common
   * (NV, neutral atoms, trapped ions). The chart renders this as a
   * three-letter chip strip (C / M / S) at the top-right of each box;
   * the cards mirror the same semantics. Replaces the old single
   * `kind` field for chart purposes — `kind` is now only used for
   * routing into the bottom table's two columns. */
  roles?: ("compute" | "memory" | "source")[];
}

export interface Annotation {
  kind: "arrow";
  label: string;
  sublabel: string;
  from_hz: number;
  to_hz: number;
  color: string;
}

export interface FiberBand {
  id: string;
  range_nm: [number, number];
  name: string;
  color: string;
  emphasis?: boolean;
}

export interface FreqSegment { min_hz: number; max_hz: number; width_pct: number; }

export interface AxisTick { hz: number; label: string; wavelength: string; }

export interface RegionDef {
  label: string;
  from_hz: number;
  to_hz: number;
  color?: string;
  gradient?: string;
  label_at_hz?: number;
  label_row?: number;
}

export interface RainbowStop { nm: number; color: string; }

export interface SpectrumData {
  title: string;
  canvas: { width: number; height: number; margin: { left: number; right: number; top: number; bottom: number } };
  freq_axis: { segments: FreqSegment[]; gap_pct: number };
  tracks: { top_y: number };
  platforms: PlatformBase[];
  fiber_bands: FiberBand[];
  annotations: Annotation[];
  flagship_machines: Record<string, string>;
  axis_ticks: AxisTick[];
  regions: RegionDef[];
  rainbow_stops?: RainbowStop[];
}

export const data = dataRaw as SpectrumData;

export const visiblePlatforms = data.platforms.filter((p) => !p.hidden);
export const computers = visiblePlatforms.filter((p) => !p.kind);
export const memories  = visiblePlatforms.filter((p) => p.kind === "memory");
export const sources   = visiblePlatforms.filter((p) => p.kind === "source");

export function platformBy(id: string): PlatformBase | undefined {
  return data.platforms.find((p) => p.id === id);
}

export function platformVendorList(p: PlatformBase): string[] {
  if (p.vendor_lines) return p.vendor_lines.flatMap((l) => l.split(/\s*·\s*/));
  return p.vendors ?? [];
}

export function platformVendorRows(p: PlatformBase): string[] {
  if (p.vendor_lines) return [...p.vendor_lines];
  if (p.vendors) return [p.vendors.join(" · ")];
  return [];
}

/** Frequency center for stacking sort. */
export function platformFreqCenter(p: PlatformBase): number {
  if (p.freq_range_hz) return (p.freq_range_hz[0] + p.freq_range_hz[1]) / 2;
  if (p.wavelength_range_nm) {
    const nmAvg = (p.wavelength_range_nm[0] + p.wavelength_range_nm[1]) / 2;
    return hzOfNm(nmAvg);
  }
  if (p.wavelength_nm) return hzOfNm(p.wavelength_nm);
  return 0;
}

export function freqOrdersOfMagnitude(): number {
  const allHz: number[] = [];
  for (const p of visiblePlatforms) {
    if (p.freq_range_hz) allHz.push(...p.freq_range_hz);
    if (p.wavelength_nm) allHz.push(hzOfNm(p.wavelength_nm));
    if (p.wavelength_range_nm) {
      allHz.push(hzOfNm(p.wavelength_range_nm[0]));
      allHz.push(hzOfNm(p.wavelength_range_nm[1]));
    }
  }
  return Math.log10(Math.max(...allHz) / Math.min(...allHz));
}

export function uniqueVendorCount(): number {
  const set = new Set<string>();
  for (const p of visiblePlatforms) {
    for (const v of platformVendorList(p)) {
      const cleaned = v.replace(/\(.*?\)/g, "").trim();
      if (cleaned) set.add(cleaned);
    }
  }
  return set.size;
}
