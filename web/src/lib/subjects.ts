/**
 * Workspace-level subject registry. Single source of truth for the
 * SiteNav rail and the landing page card grid; both read this same
 * array so they never disagree.
 *
 * Reading order is foundations → components → network →
 * applications → market → reference. Each subject builds
 * vocabulary used by the next; readers can stop anywhere and have a
 * coherent fragment.
 *
 * Adding a new subject:
 *   1. Create <subject>/{data.yaml, render.py, Makefile} for the
 *      print-ready static export pipeline.
 *   2. Add web/src/pages/<subject>.astro for the web page.
 *   3. Flip the row's status from "planned" to "shipped" here.
 */

export type SubjectStatus = "shipped" | "planned";

/**
 * Tier groups subjects by their role in the reading sequence.
 *   A — Foundations (qubits, entanglement, …)
 *   B — Components (memories, transduction, the spectrum cheat-sheet)
 *   C — Network (distribution, repeaters, links, protocols)
 *   D — Applications (use-cases + TRL)
 *   E — Ecosystem (companies, academia, real-world deployments)
 *   F — Reference (records, standards catalogues)
 */
export type SubjectTier = "A" | "B" | "C" | "D" | "E" | "F";

export const TIER_LABEL: Record<SubjectTier, string> = {
  A: "Foundations",
  B: "Components",
  C: "Network",
  D: "Applications",
  E: "Ecosystem",
  F: "Reference",
};

export interface Subject {
  slug: string;
  /** Full title used as the subject page H1 + SEO <title>. Can be
   *  descriptive ("Quantum teleportation — sending an unknown qubit
   *  through a Bell pair"). */
  title: string;
  /** Short title used on the home-page landing cards. Falls back to
   *  `title` when absent. Keep it under ~3 words. */
  cardTitle?: string;
  /** Short label used in the SiteNav rail; falls back to title when absent. */
  navLabel?: string;
  /** Card blurb on the landing page; can be longer than navLabel. */
  blurb: string;
  status: SubjectStatus;
  tier: SubjectTier;
}

export const SUBJECTS: Subject[] = [
  {
    slug: "qubits",
    title: "What is a qubit",
    cardTitle: "Qubits",
    navLabel: "Qubits",
    blurb: "Modalities, encodings, what 0 and 1 actually mean in each platform — the vocabulary every other subject builds on.",
    status: "shipped",
    tier: "A",
  },
  {
    slug: "entanglement",
    title: "Entanglement and Bell pairs",
    cardTitle: "Entanglement",
    navLabel: "Entanglement",
    blurb: "What makes the network-relevant correlations stronger than classical correlation, and why Bell pairs are the resource quantum networks deliver.",
    status: "shipped",
    tier: "A",
  },
  {
    slug: "teleportation",
    title: "Quantum teleportation — sending an unknown qubit through a Bell pair",
    cardTitle: "Teleportation",
    navLabel: "Teleportation",
    blurb: "How a shared Bell pair plus two classical bits transfers an unknown qubit. The fundamental quantum-internet primitive — the network's replacement for sending a copy.",
    status: "shipped",
    tier: "A",
  },
  {
    slug: "swapping",
    title: "Entanglement swapping — extending a Bell pair across an extra hop",
    cardTitle: "Swapping",
    navLabel: "Swapping",
    blurb: "Bell-state measurement at a relay station joins two Bell pairs into one across a longer distance, without the endpoints ever interacting. The primitive every memory-based repeater is built on.",
    status: "shipped",
    tier: "A",
  },
  {
    slug: "purification",
    title: "Entanglement purification — trading throughput for fidelity",
    cardTitle: "Purification",
    navLabel: "Purification",
    blurb: "Why fidelity matters for distributed protocols, and the BBPSSW pattern of trading two low-fidelity pairs for one higher-fidelity pair. Also called distillation.",
    status: "shipped",
    tier: "A",
  },
  {
    slug: "metrics",
    title: "Loss & Errors — what bounds a quantum link",
    cardTitle: "Loss & Errors",
    navLabel: "Loss & Errors",
    blurb: "The two impairments a quantum network has to manage — channel loss (which HEG fights) and qubit errors as fidelity + decoherence (which HEP fights). Grounded in fibre 0.20 dB/km, hollow-core 0.091 dB/km, memory T₂, and Bell-pair fidelity thresholds.",
    status: "shipped",
    tier: "A",
  },
  {
    slug: "memories",
    title: "Quantum memories — what stores a qubit, and for how long",
    cardTitle: "Quantum memories",
    navLabel: "Memories",
    blurb: "Storage time, fidelity, and TRL across atomic ensembles, trapped ions, solid-state defects, quantum dots, photonic, and superconducting memories.",
    status: "shipped",
    tier: "B",
  },
  {
    slug: "transduction",
    title: "Transduction and quantum frequency conversion",
    cardTitle: "Transduction",
    navLabel: "Transduction",
    blurb: "Bridging microwave qubits to telecom and visible-band photons to telecom — the two open problems on the frequency axis.",
    status: "shipped",
    tier: "B",
  },
  {
    slug: "spectrum",
    title: "Spectrum — quantum platforms across the EM range",
    cardTitle: "Spectrum",
    navLabel: "Spectrum",
    blurb: "Eleven qubit, memory, and photon-source platforms placed by transition frequency, with vendor flagship machines and the C-band fibre window.",
    status: "shipped",
    tier: "B",
  },
  {
    slug: "distribution",
    title: "Entanglement distribution — the network's core service",
    cardTitle: "Entanglement distribution",
    navLabel: "Distribution",
    blurb: "Multi-hop swap chains, why MidpointSource wins on long links, and the layered service contract of an entanglement-delivery network.",
    status: "shipped",
    tier: "C",
  },
  {
    slug: "repeaters",
    title: "Quantum repeaters — 1G / 2G / 3G families",
    cardTitle: "Quantum repeaters",
    navLabel: "Repeaters",
    blurb: "Three architectural families compared side by side, including the 50 % linear-optics BSM ceiling and the boosted-BSM workarounds.",
    status: "shipped",
    tier: "C",
  },
  {
    slug: "all-photonic",
    title: "All-photonic quantum repeaters",
    cardTitle: "All-photonic repeaters",
    navLabel: "All-photonic QR",
    blurb: "Tree- and graph-state distribution as an alternative to memory-based repeaters — Azuma 2015 and the architectures it inspired.",
    status: "shipped",
    tier: "C",
  },
  {
    slug: "links",
    title: "Links — fibre, hollow-core fibre, free-space, satellite",
    cardTitle: "Links",
    navLabel: "Links",
    blurb: "Where each link medium wins on loss, latency, and reach. ITU fibre bands, hollow-core attenuation, FSO atmospheric turbulence, and Micius-style satellite links.",
    status: "shipped",
    tier: "C",
  },
  {
    slug: "stacks",
    title: "Quantum-internet stacks — layered protocol architectures",
    cardTitle: "Stacks",
    navLabel: "Stacks",
    blurb: "Wehner / Van Meter / RFC 9340 stacks side by side, the link-layer service primitive, and how naming and addressing are deliberately deferred.",
    status: "shipped",
    tier: "C",
  },
  {
    slug: "applications",
    title: "Applications of the quantum internet",
    cardTitle: "Applications",
    navLabel: "Applications",
    blurb: "Distributed quantum computing, blind quantum computing, position verification, and multiparty consensus — what each needs from the network.",
    status: "shipped",
    tier: "D",
  },
  {
    slug: "secure-comms",
    title: "Secure communication",
    cardTitle: "Secure communication",
    navLabel: "Secure communication",
    blurb: "Why QKD exists: symmetric encryption needs a shared key, and the three ways to distribute it — classical public-key (RSA/ECDH, broken by a CRQC), post-quantum ML-KEM, and QKD — differ in what their security rests on. Plus how QKD is realised on the network (BB84, BBM92, MDI-QKD, TF-QKD, HD-QKD).",
    status: "shipped",
    tier: "D",
  },
  {
    slug: "sensing",
    title: "Networked & distributed quantum sensing",
    cardTitle: "Sensing",
    navLabel: "Sensing",
    blurb: "Sensing where the network is load-bearing: entangling sensors at separated nodes to beat the standard quantum limit on a global parameter. Networked atomic clocks, quantum-enhanced telescopy, and distributed estimation, with a reviewed reading list to the primary papers.",
    status: "shipped",
    tier: "D",
  },
  {
    slug: "maturity",
    title: "Maturity — TRL across platforms",
    cardTitle: "Maturity & TRL",
    navLabel: "Maturity",
    blurb: "Purohit's QTRL framework over Meddeb's per-platform memory-TRL benchmark, with capability-aware ratings rather than one-size-fits-all numbers.",
    status: "shipped",
    tier: "D",
  },
  {
    slug: "companies",
    title: "Companies — vendor landscape",
    cardTitle: "Companies",
    navLabel: "Companies",
    blurb: "A growing per-vendor index with milestone timelines, public roadmaps, and links to canonical announcements. Maintained as the field evolves.",
    status: "shipped",
    tier: "E",
  },
  {
    slug: "academia",
    title: "Academia — research groups and PIs",
    cardTitle: "Academia",
    navLabel: "Academia",
    blurb: "Sibling to Companies — university research groups and principal investigators (Pan Jianwei at USTC, Lukin at Harvard, Hanson at Delft, Simmons at UNSW, …) carrying the field's experimental load. Same dossier shape as Companies, scoped to academic teams.",
    status: "shipped",
    tier: "E",
  },
  {
    slug: "case-studies",
    title: "Case studies — real-world quantum networks",
    cardTitle: "Case studies",
    navLabel: "Case studies",
    blurb: "Operational and recently-operating quantum networks profiled with operator, location, technology family, scale, status, and commercial model. Covers commercial QKD trunks, entanglement-based testbeds, and the new commercial QNaaS model.",
    status: "shipped",
    tier: "E",
  },
  {
    slug: "records",
    title: "Records — quantum-networking distance and time",
    cardTitle: "Records",
    navLabel: "Records",
    blurb: "Distance and time records for QKD, entanglement distribution, qubit coherence, and memory storage — sortable tables grounded in primary peer-reviewed sources.",
    status: "shipped",
    tier: "F",
  },
  {
    slug: "standards",
    title: "Standards — QKD, QKDN, and quantum-network specifications",
    cardTitle: "Standards",
    navLabel: "Standards",
    blurb: "A live catalogue of quantum-tech standards and standardisation work across ITU-T, ETSI, IETF, IEEE, ISO/IEC, GSMA, and national bodies. Filterable by topic (QKD protocol, QKD network, entanglement-based quantum network, security, sensing, QRNG, crypto, policy) and status.",
    status: "shipped",
    tier: "F",
  },
];

export const SHIPPED_SUBJECTS = SUBJECTS.filter((s) => s.status === "shipped");
export const PLANNED_SUBJECTS = SUBJECTS.filter((s) => s.status === "planned");
