/**
 * Standards catalogue loader.
 *
 * Reads every YAML file in qni/standards/ at build time via Vite's
 * import.meta.glob (eager). One file per standards body; each contains
 * a `body` block and a `standards` array.
 *
 * Coupling is one-way: YAML → this loader → the /standards Astro page.
 */

export type StandardTag =
  | "qkd-protocol"
  | "qkdn"
  | "qnet"
  | "security"
  | "sensing"
  | "qrng"
  | "crypto-meta"
  | "policy";

export const TAG_LABEL: Record<StandardTag, string> = {
  "qkd-protocol": "QKD protocol",
  qkdn: "QKD network",
  qnet: "Quantum network",
  security: "Security",
  sensing: "Sensing",
  qrng: "QRNG",
  "crypto-meta": "Crypto / PQC",
  policy: "Policy",
};

/** Display order for filter chips and group headings. */
export const TAG_ORDER: StandardTag[] = [
  "qkd-protocol",
  "qkdn",
  "qnet",
  "security",
  "sensing",
  "qrng",
  "crypto-meta",
  "policy",
];

export type StandardType =
  | "recommendation"
  | "technical-report"
  | "supplement"
  | "draft"
  | "charter"
  | "guideline"
  | "regulatory";

export const TYPE_LABEL: Record<StandardType, string> = {
  recommendation: "Recommendation",
  "technical-report": "Technical Report",
  supplement: "Supplement",
  draft: "Draft",
  charter: "Charter",
  guideline: "Guideline",
  regulatory: "Regulatory",
};

export type StandardStatus =
  | "in-force"
  | "superseded"
  | "draft"
  | "planned"
  | "informational";

export const STATUS_LABEL: Record<StandardStatus, string> = {
  "in-force": "In force",
  superseded: "Superseded",
  draft: "Draft",
  planned: "Planned",
  informational: "Informational",
};

export interface Standard {
  id: string;
  title: string;
  type: StandardType;
  date: string; // YYYY or YYYY-MM
  group?: string;
  tags: StandardTag[];
  status: StandardStatus;
  url?: string;
  pdf?: string;
  summary: string;
  note?: string;
}

export interface Body {
  id: string;
  name: string;
  short_name: string;
  url: string;
  scope: string;
  notes?: string;
}

export interface BodyData {
  body: Body;
  standards: Standard[];
}

const yamls = import.meta.glob<BodyData>("../../../standards/*.yaml", {
  eager: true,
  import: "default",
});

/** All bodies, sorted by short_name. */
export const BODIES: BodyData[] = Object.values(yamls).sort((a, b) =>
  a.body.short_name.localeCompare(b.body.short_name),
);

/** Flat list of every standard with its body attached. Newest first by date. */
export interface StandardWithBody {
  body: Body;
  standard: Standard;
}
export const ALL_STANDARDS: StandardWithBody[] = BODIES.flatMap((b) =>
  b.standards.map((s) => ({ body: b.body, standard: s })),
).sort((a, b) => (a.standard.date < b.standard.date ? 1 : -1));

/** Counts by tag — for the summary panel. */
export function countByTag(): Record<StandardTag, number> {
  const out = Object.fromEntries(
    TAG_ORDER.map((t) => [t, 0]),
  ) as Record<StandardTag, number>;
  for (const { standard } of ALL_STANDARDS) {
    for (const t of standard.tags) {
      if (t in out) out[t] += 1;
    }
  }
  return out;
}

/** Counts by body short_name — for the summary panel. */
export function countByBody(): { body: Body; count: number }[] {
  return BODIES.map((b) => ({ body: b.body, count: b.standards.length }));
}
