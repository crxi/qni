# Contributing

Thanks for helping improve the Quantum Network Infographics. This is a
content-first project: most contributions are corrections to the data,
new vendor/research dossiers, or fixes to the explainer pages. This guide
covers the repository layout, how to run the site locally, and the
conventions that keep the content consistent.

If you've spotted an error and don't want to open a PR, just
[open an issue](https://github.com/crxi/qni/issues) — that's genuinely
useful too.

## Repository layout

Each subject owns its data; the shared Astro app renders one route per
subject.

```
qni/
  web/                 Astro app — one project, one `npm install`
    src/pages/         one .astro page per subject (entanglement, swapping, …)
    src/components/    shared components (figures, cards, tables)
    src/lib/           data loaders (read the YAML below at build time)
    src/data/          sources.yaml — the shared citation index
    src/styles/        tokens.css + shared CSS (the visual identity)
  companies/           one YAML per vendor → /companies/<slug>
  academia/            one YAML per research group → /academia/<slug>
  standards/           one YAML per standards body → /standards
  spectrum/            data.yaml + render.py for the platforms chart
  images/              source SVGs referenced by the pages
  scripts/             helper scripts (SVG→PNG render, link check, …)
```

The web pages import each subject's data via a relative path, so editing
a YAML file and rebuilding is all it takes to see the change.

## Running the site locally

```bash
cd web
npm install        # first run only; idempotent afterwards
npm run dev        # http://localhost:4321
```

Or from the repo root: `./dev.sh`.

To produce the deployable build (this also runs Pagefind search indexing
and a final HTML-minification pass):

```bash
cd web
npm run build
npm run preview    # serve the built site locally
```

Always run `npm run build` before opening a PR that touches data or pages —
if the page renders, your YAML fits the schema.

## Editing or adding a company dossier

One YAML file per vendor at `companies/<slug>.yaml`, where `<slug>`
matches `^[a-z0-9-]+$` and equals the `slug` field inside the file (it
becomes the URL path, e.g. `/companies/ionq`). `ionq.yaml` is a good
file to copy as a starting point.

### Schema (abridged)

```yaml
slug: ionq
name: IonQ
categories: [qc]            # one or more; index 0 is the primary group.
                            # qc | qkd | memory | network | source-detect |
                            # sensing | software | enabling
hq: College Park, MD, USA
founded: 2015
status: public              # public | private | acquired | defunct
parent: null                # parent company slug if acquired

positioning: >
  Plain-English description of what the company makes and who it sells
  to. 500–650 characters, 2–5 sentences. Don't enumerate every product
  or deployment city — those belong in modalities / milestones.

modalities:                 # only the blocks the company operates in
  qc:
    qubit_type: trapped-ion
    physical_qubits_current: 36
    one_q_fidelity: 0.99962
    two_q_fidelity: 0.9943
    # … numbers go in, or stay null — never invent a value
  qkd:
    protocol: [BB84, decoy-state]
    rate_distance: "1 Mbps @ 50 km SMF"
    deployed_demos: []
  # memory | network | source-detect | sensing | software | enabling
  # blocks follow the same one-block-per-category pattern.

milestones:                 # most-recent first; project-level, not people
  - date: 2024-09
    tag: qc                 # optional category filter
    headline: Forte Enterprise commercial launch, 36 algorithmic qubits
    source_url: https://www.ionq.com/...
    source_type: press      # paper | preprint | press | blog | conf-talk | filing

shareholders:               # required for public/acquired; skip for private
  - holder: Honeywell
    stake_percent: 54       # null when only the class is known
    stake_class: controlling # controlling | minority | strategic | founder
    as_of: 2024-12
    source_url: https://www.sec.gov/...

key_personnel:
  - role: CEO
    name: Peter Chapman
    since: 2019
    source_url: https://www.ionq.com/team/...

roadmap:
  - target: 2025
    item: 64 algorithmic qubits (Tempo)
    source_url: ...

current_flagship:
  name: Forte Enterprise
  generation: trapped-ion gen-3

references:
  - kind: paper             # paper | preprint | blog | press | conf-talk
    citation_key: chen-prl-2024   # null if not in the citation index
    url: https://arxiv.org/abs/...
    note: 36 algorithmic qubits demo

partial:                    # fields you couldn't verify — rendered as "—"
  - modalities.qc.coherence_t1_ms                  # bare path = no value
  - field: modalities.qc.ec_code                   # value present, weak source
    as_of: 2026-05-13
    note: announced in vendor press; peer-reviewed citation pending

last_verified: 2026-05-12
verification_method: web    # web | reference-library | mixed
```

### Source priority

Fill each field from the most authoritative source available, in this
order:

1. Peer-reviewed paper.
2. arXiv preprint.
3. Vendor blog / technology page (for product specs).
4. Vendor press release (for milestones, funding, partnerships).
5. Regulatory filing (10-K, DEF 14A, S-1, or the non-US equivalent — for
   ownership).
6. Industry tracker / journalism — last resort, never the sole source
   for a technical claim.

Wikipedia is fine for company-history facts (founding year, HQ), never
for numbers. When a value can't be verified to a strong source, put the
field path in `partial:` rather than guessing — the page renders the gap
visibly.

### Two content rules worth reading twice

**No ranking, no favouritism.** The listings track the field; they are
not a "best of". Order is alphabetical. Descriptions are factual — what a
company makes, has published, and ships. Avoid comparative or superlative
language ("the leading", "world-class", "the canonical…") and don't
hand-pick a "top players" sub-list anywhere. If a reader needs landscape
context, the index page already gives it.

**Neutral toward the subject's own claims.** Report what a company has
announced and what it has published; don't editorialise about the gap or
imply a claim is doubtful. Record provenance as a neutral fact: use the
`partial:` object form with a note about *citation status*
("announced in vendor press; peer-reviewed citation pending") — not
skeptical phrasing like "claims to", "purportedly", or "unverified".

## Adding an academia dossier

Same workflow, source priority, length target, and tone as company
dossiers, but the file goes in `academia/<slug>.yaml` (slug convention:
`<surname>-<institution>`, e.g. `lukin-harvard`). A few fields differ —
`status` is `active | dormant | spinout`, `institution` replaces
`parent`, `funding_sources` replaces `shareholders` (grant agencies, no
equity), and `current_focus` replaces `current_flagship`. Copy any
existing file in `academia/` as a template; `web/src/lib/academia.ts`
documents the exact types.

## Adding a standards entry

One YAML per standards body at `standards/<body>.yaml` (filename slug
matches `body.id`). Append to the `standards` array:

```yaml
- id: Y.3800                 # canonical short identifier
  title: Overview on networks supporting quantum key distribution
  type: recommendation       # recommendation | technical-report | supplement |
                             # draft | charter | guideline | regulatory
  date: 2019-10              # YYYY or YYYY-MM
  group: SG13
  tags: [qkdn]               # qkd-protocol | qkdn | qnet | security |
                             # sensing | qrng | crypto-meta | policy
  status: in-force           # in-force | superseded | draft | planned |
                             # informational
  url: https://www.itu.int/rec/T-REC-Y.3800/en
  summary: >
    One or two sentences on what the document covers.
```

When a revision supersedes an old standard, keep the old entry and set
its `status: superseded` — the page is a longitudinal record. Read a
document's scope page before assigning tags; don't infer them from the
title.

## The platforms spectrum chart

`spectrum/data.yaml` is the source of truth; `spectrum/render.py` emits
the SVG. Run it from inside `spectrum/`:

```bash
cd spectrum
python3 render.py            # → output/spectrum.svg
make all                     # SVG + PNG + PDF
```

`render.py` runs an overlap detector before emitting — if you see a
`warning: 'X' overlaps 'Y'` line on stderr, fix it before treating the
render as done. Box widths auto-fit their content; don't set a global
width. Vendor lists are alphabetical.

## Citations

Shared citation index: `web/src/data/sources.yaml`. Reference an entry by
its `id` from a page's `<SourceNote id="…" />`. When you cite a number,
cite the source of that number.

## Design conventions

The site has a deliberately consistent visual language — recurring SVG
glyphs (beam splitters, detectors, entanglement drawn as wavy lines) and
shared animation behaviours. If you're adding or editing a figure, open
the most similar existing page first and reuse its approach rather than
inventing a new one. Every figure honours `prefers-reduced-motion` with a
meaningful still frame. The shared theme lives in
`web/src/styles/tokens.css` — re-skinning the site means editing tokens,
not individual pages.

## Tone

The audience is senior professionals evaluating and planning quantum
technology. Write clearly and directly, define each technical term on
first use, and let claims carry their own weight — no marketing language,
no throat-clearing. Match the register of the source literature.

## Submitting

1. Branch from `main`.
2. Make your change; run `npm run build` (and `python3 render.py` if you
   touched the spectrum data).
3. Open a PR describing what changed and citing your sources.

Data corrections that update a `last_verified` date, fix a number against
a better source, or add a missing milestone are all welcome.
