// Capture a high-fidelity PNG of the canonical 1G repeater figure on
// the /swapping page. The in-browser canvas download loses CSS
// variables and external fonts, so for a clean snapshot use playwright.
//
// Usage (with the dev server running on localhost:4321):
//   npm run dev           # in one terminal
//   node scripts/shoot_onegen.mjs [output.png] [phase]
//
//   phase ∈ { "hold", "eg-start", "es1", "es2", "result" }
//   Default phase: "hold" (everything lit final scene).
//
// Requires playwright installed locally — already on the dev box:
//   npx playwright install chromium  (one-time)

import { chromium } from "playwright";

const OUT   = process.argv[2] || "images/canonical-1g-repeater_2k.png";
const PHASE = process.argv[3] || "hold";
const URL   = process.env.SHOOT_URL || "http://localhost:4321/swapping";

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1600, height: 1000 },
  deviceScaleFactor: 2,
});
await page.goto(URL, { waitUntil: "networkidle" });

const fig = page.locator("figure.onegen").first();
await fig.scrollIntoViewIfNeeded();

// Drive the animation to the requested phase via the toolbar controls
// then pause so the screenshot is a stable still frame.
await page.evaluate((phase) => {
  const fwd  = document.querySelector('[data-1g-ctl="fwd"]');
  const back = document.querySelector('[data-1g-ctl="back"]');
  const play = document.querySelector('[data-1g-ctl="play"]');
  // Step back to the very start.
  for (let i = 0; i < 6; i++) back && back.click();
  const stepsByPhase = { "eg-start": 0, "es1": 1, "es2": 2, "result": 3, "hold": 4 };
  const n = stepsByPhase[phase] ?? 4;
  for (let i = 0; i < n; i++) fwd && fwd.click();
  // Ensure paused so the still frame doesn't drift.
  // The button is currently showing the Pause icon (aria-label='Pause')
  // when the engine is playing; clicking it pauses for the snapshot.
  if (play && play.getAttribute("aria-label") === "Pause") play.click();
}, PHASE);

await page.waitForTimeout(600);
await fig.screenshot({ path: OUT });
console.log("Saved", OUT, "(phase:", PHASE + ")");
await browser.close();
