/**
 * Company-dossier loader.
 *
 * Reads every YAML file in qni/companies/ at build time via Vite's
 * import.meta.glob (eager). The qni/companies/ directory is the
 * single source of truth — one YAML file per company, written by hand
 * against the documented dossier schema.
 *
 * Coupling is one-way: YAML → this loader → Astro pages. Nothing in the
 * site writes back to the YAML files.
 */

export type Category =
  | "qc"
  | "qkd"
  | "memory"
  | "network"
  | "source-detect"
  | "sensing"
  | "software"
  | "enabling";

export const CATEGORY_LABEL: Record<Category, string> = {
  qc: "Quantum computers",
  qkd: "QKD",
  memory: "Quantum memory",
  network: "Networking",
  "source-detect": "Sources & detectors",
  sensing: "Quantum sensing",
  software: "Software & middleware",
  enabling: "Enabling supply chain",
};

/** Display order on the landing page. */
export const CATEGORY_ORDER: Category[] = [
  "qc",
  "qkd",
  "memory",
  "network",
  "source-detect",
  "sensing",
  "software",
  "enabling",
];

export type CompanyStatus = "public" | "private" | "acquired" | "defunct";
export type SourceType =
  | "paper"
  | "preprint"
  | "press"
  | "blog"
  | "conf-talk"
  | "filing";

export interface Milestone {
  date: string; // YYYY or YYYY-MM
  tag?: Category;
  headline: string;
  source_url: string;
  source_type: SourceType;
}

export interface RoadmapItem {
  target: string; // YYYY or "Q3 2025"
  item: string;
  source_url?: string;
  tag?: Category;
}

export interface Reference {
  kind: SourceType;
  citation_key: string | null;
  url: string;
  note?: string;
}

/** Modality-specific data. Each block is optional. */
export interface ModalityQC {
  qubit_type: string;
  physical_qubits_current: number | null;
  logical_qubits_current: number | null;
  one_q_fidelity: number | null;
  two_q_fidelity: number | null;
  coherence_t1_ms: number | null;
  coherence_t2_ms: number | null;
  ec_code: string | null;
  connectivity: string | null;
  gate_set: string[];
}

export interface ModalityQKD {
  protocol: string[];
  rate_distance: string;
  deployed_demos: string[];
}

export interface ModalityMemory {
  platform: string;
  storage_time_ms: number | null;
  retrieval_efficiency: number | null;
  fidelity: number | null;
  wavelength_nm: number | null;
  mode_capacity: number | null;
}

export interface ModalityNetwork {
  role: string;
  products: string[];
}

export interface Modalities {
  qc?: ModalityQC;
  qkd?: ModalityQKD;
  memory?: ModalityMemory;
  network?: ModalityNetwork;
  // The remaining four are open-shape for now; tighten as data lands.
  "source-detect"?: Record<string, unknown>;
  sensing?: Record<string, unknown>;
  software?: Record<string, unknown>;
  enabling?: Record<string, unknown>;
}

export interface CompanyLogoSpec {
  /** Domain for Clearbit's logo API (https://logo.clearbit.com/{domain}). */
  domain?: string;
  /** Path under web/public — used in preference to Clearbit if present. */
  local?: string;
}

export interface Company {
  slug: string;
  name: string;
  categories: Category[];
  hq: string;
  /** Additional significant facilities (manufacturing plants, R&D
   *  campuses, regional headquarters) outside the `hq` country.
   *  Each entry uses the same "City, Region, Country" shape as `hq`
   *  and contributes to the country filter chips so the dossier
   *  surfaces under every relevant country. */
  additional_locations?: string[];
  founded: number;
  status: CompanyStatus;
  parent: string | null;
  logo?: CompanyLogoSpec;
  positioning: string;
  modalities: Modalities;
  milestones: Milestone[];
  roadmap: RoadmapItem[];
  current_flagship: { name: string; generation: string } | null;
  /** Leadership / key personnel — CEO, founders, chief scientists, etc.
   *  Each entry: role, name, optional `since` year, optional source URL. */
  key_personnel?: {
    role: string;
    name: string;
    since?: number | string;
    source_url?: string;
  }[];
  references: Reference[];
  partial: string[];
  last_verified: string;
  verification_method: "web" | "reference-library" | "mixed";
}

const yamls = import.meta.glob<Company>("../../../companies/*.yaml", {
  eager: true,
  import: "default",
});

// Build-time invariant. A dossier that uses a category token outside the
// allowed enum (e.g. "sources" instead of "source-detect", or "memories"
// instead of "memory") is silently dropped by companiesByPrimary() — which
// groups by the valid set — while the country / category counters still
// tally it, so a chip reads "Denmark 1" but filtering shows nothing. Fail
// the build instead, naming the file and the bad token. Also catch an
// empty categories list and a slug that drifts from its filename. The
// standalone equivalent is scripts/check_dossiers.py.
const ALLOWED_CATEGORIES = new Set<string>(CATEGORY_ORDER);
for (const [path, co] of Object.entries(yamls)) {
  const file = path.split("/").pop() ?? path;
  const where = `companies/${file}`;
  if (!Array.isArray(co.categories) || co.categories.length === 0) {
    throw new Error(`[companies] ${where}: 'categories' must be a non-empty array`);
  }
  for (const cat of co.categories) {
    if (!ALLOWED_CATEGORIES.has(cat)) {
      throw new Error(
        `[companies] ${where}: invalid category '${cat}'. Allowed: ${CATEGORY_ORDER.join(", ")}`,
      );
    }
  }
  const expectedSlug = file.replace(/\.ya?ml$/, "");
  if (co.slug !== expectedSlug) {
    throw new Error(
      `[companies] ${where}: slug '${co.slug}' does not match filename ('${expectedSlug}' expected)`,
    );
  }
}

/** All company dossiers, sorted by name. */
export const COMPANIES: Company[] = Object.values(yamls).sort((a, b) =>
  a.name.localeCompare(b.name),
);

/** Companies whose primary (index-0) category equals `c`. */
export function companiesByPrimary(c: Category): Company[] {
  return COMPANIES.filter((co) => co.categories[0] === c);
}

/** Look up by slug. Returns undefined if not present. */
export function companyBySlug(slug: string): Company | undefined {
  return COMPANIES.find((c) => c.slug === slug);
}

/**
 * Days since `last_verified`. Used for the staleness badge — entries
 * older than 90 days are flagged on the per-vendor page.
 */
export function daysSinceVerified(company: Company): number {
  const verified = new Date(company.last_verified).getTime();
  const now = Date.now();
  return Math.floor((now - verified) / (1000 * 60 * 60 * 24));
}

export const STALE_THRESHOLD_DAYS = 90;

/**
 * Format a milestone / roadmap date for display.
 *
 * YAML parses an unquoted `YYYY-MM-DD` literal into a JS Date, and
 * `String(date)` then yields "Thu Nov 20 2025 00:00:00 GMT+0000 (UTC)"
 * — h:m:s noise nobody wants in a timeline. Coerce everything back to
 * a tidy "YYYY-MM-DD", "YYYY-MM", or "YYYY" depending on what we have.
 */
export function formatDateLabel(input: string | number | Date | null | undefined): string {
  if (input == null) return "";
  if (input instanceof Date) {
    const y = input.getUTCFullYear();
    const m = String(input.getUTCMonth() + 1).padStart(2, "0");
    const d = String(input.getUTCDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }
  if (typeof input === "number") return String(input);
  const s = String(input).trim();
  if (/^Q[1-4]\s+\d{4}$/i.test(s)) return s;
  const isoMatch = s.match(/^(\d{4})-(\d{2})(?:-(\d{2}))?/);
  if (isoMatch) {
    const [, y, m, d] = isoMatch;
    return d ? `${y}-${m}-${d}` : `${y}-${m}`;
  }
  return s;
}
