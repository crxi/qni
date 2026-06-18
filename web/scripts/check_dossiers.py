#!/usr/bin/env python3
"""Validate every company dossier against the structural invariants the
companies page relies on. Run standalone (`python3 scripts/check_dossiers.py`
from web/, or `npm run check`); the same checks also run at build time inside
src/lib/companies.ts, so a violation fails `npm run build` too — this script
is the explicit, runner-free version for CI or a quick local check.

The motivating bug: a dossier with `categories: [sources]` (not a valid enum
token — the correct one is `source-detect`) was silently dropped from the
grid by companiesByPrimary(), which groups by the valid category set, while
the country/category counters still counted it. Result: the Denmark chip read
"1" but filtering by Denmark showed no card. These checks make that class of
mistake fail loudly instead.

Checks per dossier:
  1. `categories` is a non-empty list.
  2. every category token is in the allowed enum.
  3. `slug` matches the filename.
  4. `slug` is unique across all dossiers.

Allowed categories mirror `Category` / `CATEGORY_ORDER` in
web/src/lib/companies.ts — keep the two in sync.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Mirror of CATEGORY_ORDER in web/src/lib/companies.ts (single source of truth
# lives there; this list must match it).
ALLOWED_CATEGORIES = {
    "qc",
    "qkd",
    "memory",
    "network",
    "source-detect",
    "sensing",
    "software",
    "enabling",
}

# companies/ sits two levels up from web/scripts/.
COMPANIES_DIR = Path(__file__).resolve().parents[2] / "companies"


def main() -> int:
    if not COMPANIES_DIR.is_dir():
        print(f"check_dossiers: directory not found: {COMPANIES_DIR}", file=sys.stderr)
        return 2

    errors: list[str] = []
    slugs: dict[str, str] = {}
    files = sorted(COMPANIES_DIR.glob("*.yaml"))

    for path in files:
        rel = f"companies/{path.name}"
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"{rel}: YAML parse error: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{rel}: top-level YAML is not a mapping")
            continue

        cats = data.get("categories")
        if not isinstance(cats, list) or not cats:
            errors.append(f"{rel}: 'categories' must be a non-empty list")
        else:
            for cat in cats:
                if cat not in ALLOWED_CATEGORIES:
                    allowed = ", ".join(sorted(ALLOWED_CATEGORIES))
                    errors.append(
                        f"{rel}: invalid category '{cat}'. Allowed: {allowed}"
                    )

        slug = data.get("slug")
        expected = path.stem
        if slug != expected:
            errors.append(
                f"{rel}: slug '{slug}' does not match filename ('{expected}' expected)"
            )
        elif slug in slugs:
            errors.append(f"{rel}: duplicate slug '{slug}' (also in {slugs[slug]})")
        else:
            slugs[slug] = rel

    if errors:
        print(f"check_dossiers: {len(errors)} problem(s) in {len(files)} dossiers:\n")
        for e in errors:
            print(f"  ✗ {e}")
        return 1

    print(f"check_dossiers: OK — {len(files)} dossiers, all categories/slugs valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
