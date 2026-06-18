/**
 * text-metrics.ts — text width estimation for build-time layout.
 *
 * The Python pipeline uses Pillow + Helvetica Bold for pixel-perfect widths.
 * The web build runs in Node and we don't want to bundle a font file, so we
 * approximate by classifying each character (caps, lowercase, digit, narrow
 * punctuation) and summing per-class advance widths. The constants are
 * calibrated against Helvetica Bold at 10.5pt and scaled for other sizes.
 *
 * Why not a single per-class average advance × character count? Because
 * vendor lines like "Atom Comp. · Infleqtion · Pasqal · QuEra" are ~30%
 * narrow chars (`·`, ` `, `.`) at 2.9 px each — a uniform 5.9 average
 * over-estimates the line by 35 px, enough to push Neutral atoms off the
 * Photonic-QC level when it should fit.
 */

export type TextClass = "p-name" | "p-sub" | "vendor";

export const FONT_SIZE_PX: Record<TextClass, number> = {
  "p-name": 13,
  "p-sub":  10.5,
  "vendor": 10.5,
};

// Per-character advance widths for Helvetica Bold at 10.5pt, measured via
// Pillow's ImageFont.getlength(). Other sizes scale linearly.
const W_CAP    = 7.4;   // caps avg = 7.22 + safety
const W_LOWER  = 5.75;  // lower avg = 5.66 + safety
const W_DIGIT  = 5.95;  // digit avg = 5.84 + safety
const W_NARROW = 3.05;  // ' ', '·', '.', ',', '/' = 2.92
const W_PUNCT  = 3.6;   // '(', ')', '-' = 3.50
const W_ENDASH = 5.95;  // '–' = 5.84
const W_OTHER  = 5.75;  // unknown / non-ASCII default to lowercase width

const NARROW = new Set(" ·.,/");
const PUNCT  = new Set("()-");

function charAdvance(c: string): number {
  if (c >= "A" && c <= "Z") return W_CAP;
  if (c >= "a" && c <= "z") return W_LOWER;
  if (c >= "0" && c <= "9") return W_DIGIT;
  if (NARROW.has(c)) return W_NARROW;
  if (PUNCT.has(c))  return W_PUNCT;
  if (c === "–")     return W_ENDASH;
  return W_OTHER;
}

export function measureText(text: string, cls: TextClass): number {
  const ratio = FONT_SIZE_PX[cls] / 10.5;
  let w = 0;
  for (const c of text) w += charAdvance(c);
  return w * ratio;
}

export function maxLineWidth(lines: { cls: TextClass; text: string }[]): number {
  return Math.max(...lines.map((l) => measureText(l.text, l.cls)));
}
