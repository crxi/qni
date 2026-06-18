/**
 * chart-interactions.ts — client behaviour for SpectrumChart.
 *
 * Adds three things to the otherwise-static SVG chart:
 *
 *   1. Bidirectional highlight. Hovering or focusing a glyph in the chart
 *      adds [data-active] to it, and hovering a detail card below the
 *      chart highlights the matching chart glyph. The chart wrapper gets
 *      `has-active` while *anything* is active so siblings dim.
 *
 *   2. Click-to-scroll. Clicking (or pressing Enter on a focused) glyph
 *      smooth-scrolls to the corresponding `#platform-<id>` detail card
 *      and also updates the URL hash so the link is bookmarkable.
 *
 *   3. Deep links. On load, if the URL hash matches a platform card, the
 *      chart glyph is highlighted alongside the scroll target.
 *
 * Re-measurement / re-layout (canvas.measureText + greedy stacking on the
 * client) is intentionally omitted. The build-time heuristic gets within
 * ~5 px of the real font metrics, which is below visual significance for
 * this dataset. If a future change makes that gap matter, the right place
 * to re-layout is here, calling `computeStacking` from lib/stacking.ts.
 */

let initialised = false;

export function initSpectrumChart(): void {
  if (initialised) return;
  initialised = true;

  if (typeof document === "undefined") return;

  const init = () => {
    document.querySelectorAll<SVGElement>(".spectrum-chart").forEach(setupChart);
    setupCardLinks();
    handleInitialHash();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
}

function setupChart(chartEl: Element): void {
  const svg = chartEl.querySelector<SVGSVGElement>("svg.chart-svg");
  if (!svg) return;

  const glyphs = svg.querySelectorAll<SVGGElement>(".platform-glyph");

  glyphs.forEach((glyph) => {
    const id = glyph.dataset.platformId;
    if (!id) return;

    glyph.addEventListener("mouseenter", () => activate(svg, id));
    glyph.addEventListener("mouseleave", () => deactivate(svg));
    glyph.addEventListener("focus",      () => activate(svg, id));
    glyph.addEventListener("blur",       () => deactivate(svg));

    glyph.addEventListener("click", () => scrollToPlatform(id));
    glyph.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        scrollToPlatform(id);
      }
    });
  });
}

function setupCardLinks(): void {
  document.querySelectorAll<HTMLElement>("[data-platform-card-id]").forEach((card) => {
    const id = card.dataset.platformCardId;
    if (!id) return;
    card.addEventListener("mouseenter", () => activateAll(id));
    card.addEventListener("mouseleave", () => deactivateAll());
    card.addEventListener("focusin",    () => activateAll(id));
    card.addEventListener("focusout",   () => deactivateAll());
  });
}

function activate(svg: SVGSVGElement, id: string): void {
  svg.classList.add("has-active");
  svg.querySelectorAll<SVGGElement>(".platform-glyph").forEach((g) => {
    if (g.dataset.platformId === id) g.dataset.active = "yes";
    else delete g.dataset.active;
  });
  // Promote the active platform's leader(s) from the back layer to the
  // front layer so they paint on top of every box. Without this the
  // hover behaviour depends on platform source order — earlier
  // platforms (e.g. Superconducting) would have their leader stay
  // behind later platforms' boxes even when active.
  const back  = svg.querySelector<SVGGElement>(".leaders-back");
  const front = svg.querySelector<SVGGElement>(".leaders-front");
  if (back && front) {
    back.querySelectorAll<SVGElement>(`.leader[data-platform-id="${CSS.escape(id)}"]`)
      .forEach((leader) => {
        leader.dataset.active = "yes";
        front.appendChild(leader);
      });
  }
}

function deactivate(svg: SVGSVGElement): void {
  svg.classList.remove("has-active");
  svg.querySelectorAll<SVGGElement>(".platform-glyph").forEach((g) => {
    delete g.dataset.active;
  });
  // Move any promoted leaders back to the back layer so the next hover
  // starts from a clean state.
  const back  = svg.querySelector<SVGGElement>(".leaders-back");
  const front = svg.querySelector<SVGGElement>(".leaders-front");
  if (back && front) {
    front.querySelectorAll<SVGElement>(".leader").forEach((leader) => {
      delete leader.dataset.active;
      back.appendChild(leader);
    });
  }
}

function activateAll(id: string): void {
  document.querySelectorAll<SVGSVGElement>(".chart-svg").forEach((svg) => activate(svg, id));
}

function deactivateAll(): void {
  document.querySelectorAll<SVGSVGElement>(".chart-svg").forEach((svg) => deactivate(svg));
}

function scrollToPlatform(id: string): void {
  const target = document.getElementById(`platform-${id}`);
  if (!target) return;
  history.replaceState(null, "", `#platform-${id}`);
  target.scrollIntoView({ behavior: "smooth", block: "start" });
  target.focus({ preventScroll: true });
  target.classList.add("flash");
  setTimeout(() => target.classList.remove("flash"), 1200);
}

function handleInitialHash(): void {
  const hash = window.location.hash;
  const match = hash.match(/^#platform-(.+)$/);
  if (!match) return;
  const id = match[1];
  // Briefly highlight on load.
  activateAll(id);
  setTimeout(deactivateAll, 1500);
}
