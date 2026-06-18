/**
 * case-studies — single source of truth for the tier F case-study list.
 *
 * Imported by:
 *   - /pages/case-studies.astro       (the index page cards)
 *   - /components/SiteNav.astro       (the left rail, tier F entries)
 *
 * Each case study has a long `title` (used on the index card and inside
 * the case-study page hero) and a short `navLabel` (used in the rail).
 * `categories`, `country`, and `statusKey` drive the search-and-filter
 * UI on the index page.
 */

// Technology categories — the *what* of the demo. Roadmap-only entries
// (announced but not demonstrated) are flagged via `statusKey: roadmap`;
// they still get categorised by the technology they plan to use.
export type CaseCategory = "qkd" | "entanglement" | "hybrid";
export type CaseStatus   = "operational" | "demo" | "roadmap";

export const CATEGORY_LABEL: Record<CaseCategory, string> = {
  qkd:          "QKD",
  entanglement: "Entanglement",
  hybrid:       "Hybrid",
};

export const CATEGORY_ORDER: CaseCategory[] = [
  "entanglement",
  "qkd",
  "hybrid",
];

export const STATUS_LABEL: Record<CaseStatus, string> = {
  operational: "Operational",
  demo:        "Demonstration",
  roadmap:     "Roadmap",
};

export const STATUS_ORDER: CaseStatus[] = [
  "operational",
  "demo",
  "roadmap",
];

export interface CaseStudy {
  slug: string;
  title: string;
  /** Short label for the left-rail. Falls back to `title` if omitted. */
  navLabel?: string;
  operator: string;
  location: string;
  /** Short country / region key for the country filter chip. */
  country: string;
  year: string;
  technology: string;
  scale: string;
  status: string;
  /** Coarse status used by the filter chip (more granular than `status`). */
  statusKey: CaseStatus;
  model: string;
  blurb: string;
  /** Categories used by the colour chips and category filter. */
  categories: CaseCategory[];
}

export const CASE_STUDIES: CaseStudy[] = [
  {
    slug: "epb",
    title: "EPB Quantum Network (Chattanooga)",
    navLabel: "EPB Chattanooga",
    operator: "EPB · Qubitekk · Aliro · (IonQ from 2025)",
    location: "Chattanooga, Tennessee, USA",
    country: "USA",
    year: "2022",
    technology: "Entanglement-based",
    scale: "Metro (~8 km loop)",
    status: "Operational paid testbed",
    statusKey: "operational",
    model: "Quantum-as-a-service subscription",
    blurb: "First commercially-available quantum network in the US. Customer-configurable entangled-photon testbed on EPB dark fibre, with Aliro AliroNet as controller. IonQ trapped-ion system added under a $22 M deal in April 2025.",
    categories: ["entanglement"],
  },
  {
    slug: "china-backbone",
    title: "Beijing–Shanghai QKD backbone",
    navLabel: "Beijing–Shanghai backbone",
    operator: "USTC / QuantumCTek / state operators",
    location: "Beijing ↔ Jinan ↔ Hefei ↔ Shanghai, China",
    country: "China",
    year: "2017",
    technology: "Prepare-and-measure QKD (decoy-state BB84)",
    scale: "National trunk (~2,032 km, 32 trusted nodes)",
    status: "Operational",
    statusKey: "operational",
    model: "Government / financial-sector service",
    blurb: "The longest deployed terrestrial QKD trunk. Trusted-node relay between four cities, integrated with the Micius satellite for a 4,600 km space–ground link. Not entanglement-based — keys are reconstructed at each trusted relay.",
    categories: ["qkd"],
  },
  {
    slug: "micius",
    title: "Micius satellite quantum-communication mission",
    navLabel: "Micius satellite",
    operator: "USTC / Pan group · Chinese Academy of Sciences",
    location: "LEO (~500 km); ground stations across China and Austria",
    country: "China",
    year: "2016–",
    technology: "Entanglement-based + prepare-and-measure QKD over free-space (satellite ↔ ground)",
    scale: "1,200 km satellite-to-ground; 1,120 km between two ground stations via satellite; 4,600 km space-ground integrated",
    status: "Operational mission",
    statusKey: "operational",
    model: "National research mission (not commercial)",
    blurb: "World's first quantum-science satellite. Distributed polarisation Bell pairs across a 1,200 km satellite-to-ground link (Yin et al., Science 2017) and used the satellite as an entanglement midpoint between two ground stations 1,120 km apart (Yin et al., Nature 2020), removing the trusted-node assumption for the QKD link itself.",
    categories: ["hybrid"],
  },
  {
    slug: "jinan-1",
    title: "Jinan-1 quantum microsatellite",
    navLabel: "Jinan-1 satellite",
    operator: "USTC · JIQT · SECM · Hefei National Lab",
    location: "LEO (~500 km); ground stations across China",
    country: "China",
    year: "2022–",
    technology: "Prepare-and-measure decoy-state BB84 over free-space",
    scale: "~23 kg microsatellite; satellite-to-ground QKD",
    status: "Operational",
    statusKey: "operational",
    model: "National research / state-comms infrastructure",
    blurb: "Engineering follow-up to Micius: a small-bus microsatellite carrying a decoy-state BB84 transmitter with real-time on-board key sifting, designed as a precursor to a low-cost quantum-satellite constellation. Launched 27 July 2022, operates as the space segment of the Jinan metropolitan QKD network (Li et al., Nature 2025).",
    categories: ["qkd"],
  },
  {
    slug: "cisco-qunnect-brooklyn",
    title: "Cisco × Qunnect Brooklyn–Manhattan metro entanglement-swap",
    navLabel: "Cisco × Qunnect Brooklyn",
    operator: "Qunnect · Cisco · NYU · QTD Systems (GothamQ testbed)",
    location: "Brooklyn ↔ 60 Hudson Street, New York City, USA",
    country: "USA",
    year: "2026",
    technology: "Entanglement-based (warm-Rb sources, BSM hub)",
    scale: "Metro (17.6 km, 3-node hub-and-spoke)",
    status: "Vendor-run demonstration",
    statusKey: "demo",
    model: "Industrial demo on commercial fibre; not yet sold as a service",
    blurb: "First metro-scale entanglement-swap over deployed commercial telecom fibre. Two Qunnect Carina warm-rubidium sources at Brooklyn end nodes; Bell-state-measurement hub at 60 Hudson Street with SNSPDs; Cisco control plane handling White Rabbit timing and polarization compensation. 5,400 swapped pairs/hour at >99 % fidelity. Announced 18 February 2026.",
    categories: ["entanglement"],
  },
  {
    slug: "cisco-uqs",
    title: "Cisco Universal Quantum Switch (UQS)",
    navLabel: "Cisco UQS",
    operator: "Cisco (Santa Monica Quantum Labs); partners IBM, Qunnect, Atom Computing",
    location: "Santa Monica, California, USA (lab)",
    country: "USA",
    year: "2026",
    technology: "Photonic switch across polarisation / time-bin / frequency-bin / path encodings",
    scale: "Research prototype (single switch device)",
    status: "Working research prototype",
    statusKey: "demo",
    model: "Vendor research demonstration; not yet sold",
    blurb: "Research prototype that routes quantum information between four photonic encodings — polarisation, time-bin, frequency-bin and path — via a Cisco-patented in-line conversion engine. Room-temperature on telecom fibre, 1 ns electro-optic switching, sub-watt power, ≤ 4 % per-conversion fidelity loss; announced 23 April 2026.",
    categories: ["entanglement"],
  },
  {
    slug: "ibm-cisco-qnu",
    title: "IBM × Cisco × SQMS Quantum Networking Units (QNU) plan",
    navLabel: "IBM × Cisco QNU",
    operator: "IBM · Cisco · Fermilab/SQMS",
    location: "Multi-site (Yorktown Heights, Cisco labs, Fermilab)",
    country: "USA",
    year: "2025 (announcement) — early 2030s target",
    technology: "Superconducting qubits + microwave-to-optical transduction + optical-fibre entanglement distribution between cryostats",
    scale: "Target: tens-to-hundreds of thousands of qubits across multiple cryostats",
    status: "Roadmap announcement — no demonstrated link yet",
    statusKey: "roadmap",
    model: "Vendor R&D programme",
    blurb: "Joint IBM, Cisco, and Fermilab/SQMS roadmap announced 20 November 2025 to network superconducting processors across multiple cryostats by the early 2030s, with a proof-of-concept targeted for end of 2030. The three named components — microwave-to-optical transducers, IBM Quantum Networking Units at each node, and inter-cryostat entanglement-distribution protocols — are open R&D problems, not deliverables.",
    categories: ["entanglement"],
  },
  {
    slug: "oxford-main",
    title: "Oxford trapped-ion distributed-compute demonstration",
    navLabel: "Oxford distributed-compute",
    operator: "University of Oxford (Lucas group) on lab-bench fibre",
    location: "Oxford, UK (lab)",
    country: "UK",
    year: "2025",
    technology: "Entanglement-based; mixed-species trapped ions (⁸⁸Sr⁺ network qubit + ⁴³Ca⁺ circuit qubit)",
    scale: "Two-module, ~2 m optical link",
    status: "Research demonstration",
    statusKey: "demo",
    model: "Academic / EPSRC research",
    blurb: "First distributed quantum algorithm executed across two physically separate quantum-computing modules. Heralded photonic entanglement between ⁸⁸Sr⁺ network qubits is swapped onto ⁴³Ca⁺ circuit qubits and consumed for a deterministic teleported CNOT (~86 % fidelity), with a two-qubit Grover's search run end-to-end across the link. Main et al., Nature (2025).",
    categories: ["entanglement"],
  },
  {
    slug: "knaut-boston",
    title: "Harvard SiV two-node Boston-metro loop",
    navLabel: "Harvard SiV Boston",
    operator: "Harvard (Lukin / Lončar / Park) on Verizon fibre",
    location: "Boston-Cambridge, Massachusetts, USA",
    country: "USA",
    year: "2024",
    technology: "Entanglement-based (silicon-vacancy memory nodes)",
    scale: "Metro (35 km deployed loop)",
    status: "Research demonstration",
    statusKey: "demo",
    model: "Academic / sponsored research",
    blurb: "Heralded entanglement between two silicon-vacancy quantum-memory nodes through 35 km of installed telecom fibre under a Boston urban environment. Published as Knaut et al., Nature 629.573 (2024).",
    categories: ["entanglement"],
  },
  {
    slug: "delft-three-node",
    title: "Delft three-node NV-centre network",
    navLabel: "Delft NV three-node",
    operator: "QuTech / TU Delft (Hanson group)",
    location: "Delft, Netherlands",
    country: "Netherlands",
    year: "2021",
    technology: "Entanglement-based (NV-centre memory nodes)",
    scale: "Lab-scale three-node chain",
    status: "Research demonstration",
    statusKey: "demo",
    model: "Academic / EU Quantum Internet Alliance",
    blurb: "First entanglement-based three-node network with two non-neighbouring endpoints linked by a midpoint repeater node. Demonstrated entanglement distribution and entanglement swapping (Pompili et al., Science 372.259, 2021); a 2022 follow-up added qubit teleportation between non-neighbours.",
    categories: ["entanglement"],
  },
  {
    slug: "madqci",
    title: "MadQCI — Madrid Quantum Communications Infrastructure",
    navLabel: "MadQCI Madrid",
    operator: "UPM / Telefónica / Huawei / partners",
    location: "Madrid metro, Spain",
    country: "Spain",
    year: "2021–",
    technology: "Heterogeneous QKD on production fibre (SDN-managed)",
    scale: "Metro (9 nodes, 28 QKD modules)",
    status: "Operational testbed on production network",
    statusKey: "operational",
    model: "Telco-led research consortium",
    blurb: "Europe's largest and longest-running QKD testbed. Nine SDN-managed nodes co-existing with commercial Telefónica traffic; supports multiple QKD vendors and ETSI-aligned key management. Documented in Martin et al., npj QI 10.80 (2024).",
    categories: ["qkd"],
  },
  {
    slug: "bt-london",
    title: "BT–Toshiba London commercial QKD metro",
    navLabel: "BT–Toshiba London",
    operator: "BT · Toshiba (first customer: EY)",
    location: "London, UK",
    country: "UK",
    year: "2022",
    technology: "Prepare-and-measure QKD on dark fibre",
    scale: "Metro (London ring)",
    status: "Operational commercial service trial",
    statusKey: "operational",
    model: "Paid commercial trial (initial 3-year term)",
    blurb: "First commercial QKD-secured metro network sold as a service in the UK. Toshiba supplies the QKD hardware; BT operates the fibre and managed service. EY connected its Canary Wharf and London Bridge offices as the launch customer.",
    categories: ["qkd"],
  },
  {
    slug: "qbird-rotterdam",
    title: "Q*Bird Port of Rotterdam MDI-QKD pilot",
    navLabel: "Q*Bird Rotterdam",
    operator: "Q*Bird · Single Quantum · Cisco · Eurofiber · Port of Rotterdam Authority (under Quantum Delta NL)",
    location: "Port of Rotterdam, Netherlands",
    country: "Netherlands",
    year: "2024",
    technology: "Measurement-Device-Independent QKD (MDI-QKD)",
    scale: "Metro hub-and-spoke (Falqon hub in Eurofiber DC + Port Authority and Customs end nodes)",
    status: "Operational pilot; QUEST expansion in progress",
    statusKey: "operational",
    model: "Public-private pilot under Quantum Delta NL",
    blurb: "First multi-node MDI-QKD pilot in a working industrial port. Q*Bird's Falqon hub installed in a Eurofiber data centre performs Bell-state measurements between photons from Port of Rotterdam Authority and Dutch Customs end nodes — moving detector trust out of the end users' premises into a neutral middle. QUEST follow-on extends the architecture across South Holland.",
    categories: ["qkd"],
  },
];
