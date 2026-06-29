/**
 * Site changelog — single source of truth for the /changelog page.
 *
 * Newest first. Each entry is one major, reader-relevant change to the site
 * or its data. Keep entries concise and factual: what changed, not how it was
 * built. Date is ISO (YYYY-MM-DD).
 */
export interface ChangelogEntry {
  date: string;
  summary: string;
}

export const CHANGELOG: ChangelogEntry[] = [
  {
    date: "2026-06-29",
    summary:
      "Added an all-photonic entanglement-distribution records section, separating post-selected from heralded (event-ready) results so distance records are not conflated with heralding-efficiency milestones.",
  },
  {
    date: "2026-06-29",
    summary:
      "Added Peng et al., Nature Physics (2026) — the first single-photon teleportation to beat direct transmission unconditionally — to the citation registry.",
  },
];
