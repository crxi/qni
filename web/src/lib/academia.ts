/**
 * Academia-dossier loader.
 *
 * Reads every YAML file in qni/academia/ at build time via Vite's
 * import.meta.glob (eager). Mirrors the companies loader — the schema
 * is intentionally aligned with companies/*.yaml so most fields are
 * shared (categories, modalities, milestones, references, partial,
 * last_verified). Three fields are academia-specific:
 *
 *   institution  — host university + lab/centre name
 *   group_website — public landing page for the PI's group
 *   current_focus — the current major research thrust (parallel to
 *                   `current_flagship` for a vendor)
 *
 * Plus two field replacements vs companies:
 *   status: "active" | "dormant" | "spinout"   — not public/private/...
 *   funding_sources                            — replaces shareholders
 *
 * Reuses the Category / Milestone / Reference / Modalities types from
 * the companies loader so a future shared component can render either.
 */

import type {
  Category,
  Milestone,
  Reference,
  Modalities,
} from "./companies";
export {
  CATEGORY_LABEL,
  CATEGORY_ORDER,
  STALE_THRESHOLD_DAYS,
  formatDateLabel,
} from "./companies";

export type AcademiaStatus = "active" | "dormant" | "spinout";

export interface AcademiaInstitution {
  name: string;
  lab?: string;
  /** Optional second affiliation (joint appointments, dual labs). */
  also?: string;
}

export interface FundingSource {
  /** Grant agency / programme name. */
  name: string;
  /** Optional one-line role (e.g. "Core funding since 2020", "Co-funder"). */
  role?: string;
  /** Optional public URL for the agency / programme. */
  source_url?: string;
}

export interface AcademiaGroup {
  slug: string;
  name: string;
  categories: Category[];
  hq: string;
  additional_locations?: string[];
  founded?: number | null; // year group was established (PI started in role)
  status: AcademiaStatus;
  /** Spinout company slug when status === "spinout" or the group has
   *  a commercial counterpart — e.g. Simmons → SQC. */
  spinout_company?: string | null;
  institution: AcademiaInstitution;
  group_website?: string;
  positioning: string;
  modalities: Modalities;
  milestones: Milestone[];
  /** Parallel to companies' `roadmap` — anticipated next directions. */
  roadmap?: { target: string; item: string; source_url?: string }[];
  key_personnel: {
    role: string;
    name: string;
    since?: number | string;
    source_url?: string;
  }[];
  funding_sources?: FundingSource[];
  current_focus?: { name: string; description?: string } | null;
  references: Reference[];
  partial: string[];
  last_verified: string;
  verification_method: "web" | "reference-library" | "mixed";
}

const yamls = import.meta.glob<AcademiaGroup>("../../../academia/*.yaml", {
  eager: true,
  import: "default",
});

/** All academia dossiers, sorted by group name. */
export const ACADEMIA: AcademiaGroup[] = Object.values(yamls).sort((a, b) =>
  a.name.localeCompare(b.name),
);

/** Academia entries whose primary (index-0) category equals `c`. */
export function academiaByPrimary(c: Category): AcademiaGroup[] {
  return ACADEMIA.filter((g) => g.categories[0] === c);
}

export function academiaBySlug(slug: string): AcademiaGroup | undefined {
  return ACADEMIA.find((g) => g.slug === slug);
}

export function daysSinceVerified(g: AcademiaGroup): number {
  const verified = new Date(g.last_verified).getTime();
  const now = Date.now();
  return Math.floor((now - verified) / (1000 * 60 * 60 * 24));
}
