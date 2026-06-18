/**
 * useScene — minimal animation-driver utility shared across all
 * animated infographics.
 *
 * Three responsibilities:
 *   1. Start the scene's animation only when its container scrolls
 *      into view (IntersectionObserver), and pause when out of view.
 *      Keeps off-screen pages from consuming CPU.
 *   2. Honour `prefers-reduced-motion: reduce` by never starting the
 *      animation — the SSR'd end-state stays as-is. Every animated
 *      scene must therefore render a meaningful still frame at SSR.
 *   3. Provide a `requestAnimationFrame` loop with delta-time so
 *      per-frame callbacks aren't tied to any specific frame rate.
 *
 * Use from a scene's <script> island:
 *
 *   import { mountScene } from "../../lib/anim/useScene";
 *
 *   mountScene(document.querySelector("#my-scene")!, ({ t, dt }) => {
 *     // update DOM/SVG attributes from t (seconds since play start)
 *     // and dt (seconds since last frame).
 *   });
 *
 * The function returns an unmount handle in case the caller wants to
 * tear the scene down explicitly (e.g. on framework HMR).
 */

export interface SceneTick {
  /** Seconds elapsed since playback started. */
  t: number;
  /** Seconds since the previous frame; clamped to <= 0.1 to avoid huge
   *  jumps after the tab regains focus. */
  dt: number;
}

export interface SceneOptions {
  /** Override the default visibility threshold (0–1). Default 0.15 —
   *  start as soon as ~15 % of the scene is on screen. */
  visibleThreshold?: number;
  /** If true, ignore reduced-motion preferences. Use only for purely
   *  decorative / very-low-amplitude motion. Default false. */
  ignoreReducedMotion?: boolean;
}

export type SceneTickFn = (tick: SceneTick) => void;

export interface SceneHandle {
  /** Tear down listeners and cancel any pending RAF. Safe to call
   *  multiple times. */
  unmount(): void;
  /** Whether reduced-motion was detected at mount time. The caller
   *  can use this to render an alternative static representation if
   *  the SSR end-state isn't sufficient. */
  reducedMotion: boolean;
}

export function mountScene(
  container: Element,
  onTick: SceneTickFn,
  options: SceneOptions = {},
): SceneHandle {
  const reducedMotion =
    !options.ignoreReducedMotion &&
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true;

  if (reducedMotion) {
    // Reduced-motion: never start the loop. SSR end-state stays.
    return { unmount() {}, reducedMotion: true };
  }

  let raf = 0;
  let startMs = 0;
  let lastMs = 0;
  let playing = false;

  const step = (now: number) => {
    if (!playing) return;
    if (startMs === 0) {
      startMs = now;
      lastMs = now;
    }
    const t = (now - startMs) / 1000;
    const dt = Math.min((now - lastMs) / 1000, 0.1);
    lastMs = now;
    onTick({ t, dt });
    raf = requestAnimationFrame(step);
  };

  const play = () => {
    if (playing) return;
    playing = true;
    // Reset the clock — animations restart from t=0 when the scene
    // re-enters the viewport. For looping animations that is what
    // the reader expects; persistent state can be carried in the
    // caller's closure if needed.
    startMs = 0;
    lastMs = 0;
    raf = requestAnimationFrame(step);
  };

  const pause = () => {
    if (!playing) return;
    playing = false;
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
  };

  const observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) play();
      else pause();
    },
    { threshold: options.visibleThreshold ?? 0.15 },
  );
  observer.observe(container);

  return {
    unmount() {
      pause();
      observer.disconnect();
    },
    reducedMotion: false,
  };
}
