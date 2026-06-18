# QuISP network icons

Standardised topology-icon set from the QuISP simulator project:
<https://github.com/sfc-aqua/quisp/tree/master/Network%20icons>.

Licence: see the upstream QuISP repository.

| File              | Glyph                              | Symbol id (in generator) |
| ----------------- | ---------------------------------- | ------------------------ |
| `icon-bsa.svg`    | Bell-State Analyser                | `quisp-bsa`              |
| `icon-epps.svg`   | Entangled-Photon-Pair Source       | `quisp-epps`             |
| `icon-rep1g.svg`  | 1st-generation repeater            | `quisp-rep1g`            |
| `icon-mem.svg`    | Quantum memory                     | `quisp-mem`              |
| `icon-comp.svg`   | Quantum compute end-node           | `quisp-comp`             |

These SVGs are inlined as `<symbol>` definitions by
`scripts/diagrams/quisp_icons.py` so generated figures can reference them
with `<use href="#quisp-bsa" .../>`. They can also be served directly by
the Astro app if a page needs a standalone glyph.

CLAUDE.md mandates this icon set for all topology diagrams in the workspace.
Reach for these glyphs whenever a figure draws nodes + links.
