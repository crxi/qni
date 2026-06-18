# Infographics web app

Shared Astro app for the infographics workspace. One page per subject; each subject's `data.yaml` lives next to its Python pipeline under `<subject>/`. The Python pipeline produces static SVG/PNG/PDF for print; the web pipeline produces an interactive web infographic where every chart element is a real first-class DOM node.

## Architecture

```
qni/
├── web/                                   ← THIS DIRECTORY (one Astro app, all subjects)
│   ├── astro.config.mjs
│   ├── package.json                       name: "info-web"
│   └── src/
│       ├── data/sources.yaml              cross-subject citations
│       ├── lib/                           spectrum-specific today; will split per
│       │   ├── data.ts                    typed YAML loader (imports ../../spectrum/data.yaml)
│       │   ├── geom.ts                    Geom — segmented log-axis math
│       │   ├── stacking.ts                per-region greedy 1-D stacking
│       │   ├── text-metrics.ts            build-time text-width estimation
│       │   └── chart-helpers.ts           lighten(), buildLayout(), …
│       ├── components/
│       │   ├── chart/                     spectrum chart pieces
│       │   ├── PlatformCard.astro
│       │   ├── StatCallout.astro
│       │   ├── AnnotationCallout.astro
│       │   ├── SourceNote.astro
│       │   ├── ReferencesList.astro
│       │   └── {Stack,Grid,Center}.astro
│       ├── scripts/chart-interactions.ts
│       ├── layouts/Infographic.astro
│       ├── pages/
│       │   ├── index.astro                subject landing
│       │   └── spectrum.astro             quantum-platforms-on-EM-spectrum subject
│       └── styles/{tokens,reset,print}.css
└── spectrum/                              ← one subject
    ├── data.yaml                          single source of truth (Python + web both read this)
    ├── render.py                          Python pipeline → output/spectrum.svg
    └── output/spectrum.{svg,png,pdf}
```

**Each platform glyph is its own SVG `<g class="platform-glyph" data-platform-id="...">` element**, not part of a baked-in PNG/SVG export. That means:

- Hover or keyboard-focus a glyph → it lights up while siblings dim (CSS state on the SVG root)
- Click (or Enter on a focused glyph) → smooth-scroll to the matching `<article id="platform-trapped-ions">` card and update the URL hash
- Hover the card below → matching glyph in the chart highlights too (bidirectional)
- Visit `…/#platform-photonic` → page loads scrolled to the card with the chart glyph briefly flashed
- The whole layout (greedy stacking, broken-axis math, per-region monotonic levels) is reproduced in TypeScript and runs at build time, so the static HTML already has the correct geometry — JavaScript only adds the interactions on top

## Bootstrap

```bash
cd web
npm install
npm run dev          # http://localhost:4321
```

The dev server serves `/` (subject landing) and one route per subject (`/spectrum`, …).

The dev server picks up changes to `data.yaml`, refs, and any `.astro`/`.css` file. It does **not** re-run `render.py` — but it doesn't need to. The web infographic builds its own chart from `data.yaml` directly; `render.py` is the separate static-export path.

## Build

```bash
npm run build        # → dist/index.html + dist/<subject>/index.html (static, no JS runtime)
npm run preview      # serve dist/
npm run build:pdf    # → dist/spectrum.pdf via Paged.js (landscape A4)
```

## Theming

`src/styles/tokens.css` is the single visual file. Three tiers:

1. **Primitives** — raw colors (OKLCH neutrals + the platform hexes mirrored from data.yaml)
2. **Semantic** — `--color-accent`, `--color-text`, `--color-computer`, `--color-memory`, `--color-source`
3. **Component** — `--card-bg`, `--stat-value-color`, `--source-marker`, …

Re-skinning the page = editing tier 1 only. The platform colors (`--platform-*`) intentionally mirror `data.yaml` — keep them in sync if you change a platform's color there.

## Content

`src/lib/data.ts` is the typed entrypoint. It exports:

- `data` — the raw YAML, typed as `SpectrumData`
- `visiblePlatforms` / `computers` / `memories` / `sources` — pre-filtered lists
- `freqOrdersOfMagnitude()` — total span across the platform set
- `uniqueVendorCount()` — deduped vendor count

Add a new section in `src/pages/index.astro` by composing existing components. Don't inline numbers or vendor names — they belong in `data.yaml`.

## What's *not* here (yet)

- **Pixel-perfect text-width measurement.** The build pass uses an average-glyph-advance heuristic (~7 px/char for Inter Bold 13 px). The visual padding is within ~5 px of the Python+Pillow rendering. If that gap matters, add a client re-layout in `scripts/chart-interactions.ts` — re-measure every glyph's `<text>` via `canvas.measureText` and re-run `computeStacking()`.
- **Scrollytelling step-through.** The chart is too information-dense to walk step by step; a dedicated explainer (e.g. how QFC works, single-photon source timing) would be a separate piece using dedicated scrollytelling step components.
- **Per-vendor landing pages.** Add a dynamic route under `pages/vendor/[slug].astro` and walk `data.flagship_machines`.
- **PDF export pipeline.** The skeleton's `npm run build:pdf` script invokes `pagedjs-cli`, but landscape pagination on this content is untested. The Python pipeline still produces the canonical print artefact.
