/**
 * Post-build minification pass over the published artifact.
 *
 * Astro never touches this site's client code: every script is
 * `<script is:inline>` and `inlineStylesheets: "always"` keeps CSS
 * inline, so the bundler's minifier doesn't run. This pass walks the
 * built `dist/**.html`, minifies the inline `<script>` (terser) and
 * `<style>` (clean-css), strips comments, and collapses whitespace —
 * so the deployed pages are smaller and carry no source comments.
 *
 * Source `.astro` files are untouched; only the build output is
 * stripped. Re-run-safe: minifying already-minified HTML is a no-op.
 * Run from `web/` as the final build step (after pagefind, which
 * indexes text content and is unaffected by minification).
 */
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { minify } from "html-minifier-terser";

const DIST = fileURLToPath(new URL("../dist/", import.meta.url));

const OPTS = {
  collapseWhitespace: true,
  // Keep at least one space between inline content — never collapse to
  // zero — so prose spacing around <a>, <em>, <strong>, math, etc. is
  // preserved.
  conservativeCollapse: true,
  removeComments: true,
  minifyCSS: true,
  minifyJS: true,
  // Preserve SVG attribute casing (viewBox, preserveAspectRatio, …) and
  // the self-closing slash that inline SVG relies on.
  caseSensitive: true,
  keepClosingSlash: true,
};

const files = readdirSync(DIST, { recursive: true }).filter(
  (f) =>
    typeof f === "string" &&
    f.endsWith(".html") &&
    // Pagefind ships its own already-minified assets.
    !f.split(/[\\/]/).includes("pagefind"),
);

let before = 0;
let after = 0;
let skipped = 0;

for (const rel of files) {
  const path = join(DIST, rel);
  const src = readFileSync(path, "utf8");
  before += Buffer.byteLength(src);
  try {
    const out = await minify(src, OPTS);
    writeFileSync(path, out);
    after += Buffer.byteLength(out);
  } catch (err) {
    // One unparseable inline script shouldn't fail the whole deploy —
    // leave that file as-is and report it so it can be looked at.
    skipped++;
    after += Buffer.byteLength(src);
    console.warn(`minify: skipped ${rel} — ${err.message}`);
  }
}

const pct = before ? ((1 - after / before) * 100).toFixed(1) : "0.0";
console.log(
  `minify: ${files.length} HTML files, ` +
    `${(before / 1024).toFixed(0)} KB → ${(after / 1024).toFixed(0)} KB ` +
    `(-${pct}%)${skipped ? `, ${skipped} skipped` : ""}`,
);
