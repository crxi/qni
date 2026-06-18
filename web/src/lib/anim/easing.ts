/**
 * easing — small set of named easing functions for animated scenes.
 *
 * Each takes a normalized progress value t ∈ [0, 1] and returns a
 * shaped value, also in [0, 1] for the "in/out" cases. Use these so
 * timings feel uniform across scenes; pulling random cubic-beziers
 * per scene leads to a sloppy mismatch.
 */

export const linear = (t: number): number => t;

/** Slow start, fast end. Good for "release" or "reveal" motion. */
export const inCubic = (t: number): number => t * t * t;

/** Fast start, slow end. Good for "settle" or "land" motion. */
export const outCubic = (t: number): number => 1 - Math.pow(1 - t, 3);

/** Symmetric ease in and out. Good for path-following motion that
 *  starts and ends at rest. */
export const inOutCubic = (t: number): number =>
  t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

/** Symmetric quadratic. Slightly less aggressive than inOutCubic. */
export const inOutQuad = (t: number): number =>
  t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;

/** Saw-toothed loop helper. Given an absolute time `t` and a `period`
 *  in seconds, returns a normalised progress 0→1 that resets every
 *  period. Use for repeating cycles inside an onTick handler. */
export const loop = (t: number, period: number): number =>
  ((t % period) + period) % period / period;

/** Symmetric ping-pong. Returns 0→1→0 over the given period. */
export const pingPong = (t: number, period: number): number => {
  const p = loop(t, period);
  return p < 0.5 ? p * 2 : (1 - p) * 2;
};
