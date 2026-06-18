#!/usr/bin/env python3
"""
check_hidden_cascade.py — catch the `[hidden]` cascade trap in .astro files.

Background
----------

Filter UIs in this workspace toggle visibility by setting the `hidden`
attribute on cards:

    card.hidden = !visible;

This relies on the UA stylesheet rule `[hidden] { display: none }`. But
if author CSS sets `display: …` on the same class at equal specificity
— e.g. `.cs-card { display: grid }` — author CSS wins the cascade tie
and `[hidden]` becomes a no-op. The filter looks like it ran (the
attribute is set), but the cards stay visible.

This script flags any .astro file where:

  (a) the inline script toggles `.hidden` on DOM elements, AND
  (b) author CSS sets `display:` on a class, AND
  (c) there is no `.<class>[hidden] { display: none }` override and no
      global `[hidden] { display: none !important }` rule.

Exit codes
----------
  0   clean
  1   one or more violations
  2   usage / IO error

Usage
-----
    python3 scripts/check_hidden_cascade.py             # walk the workspace
    python3 scripts/check_hidden_cascade.py web/src/    # specific path

Designed to run in CI alongside the build — fast, no network, no browser.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", ".astro", ".git", "__pycache__"}

# Matches `something.hidden = ...` in a script. Capture group 1 is the
# expression to the left of `.hidden`. We use it as a heuristic that
# the file relies on the hidden-attribute path for visibility.
HIDDEN_ASSIGN_RE = re.compile(r"\b(\w+)\.hidden\s*=", re.MULTILINE)

# Matches CSS rules of the form `.classname { … display: … }`. We pick
# up the class name and ignore display-values that don't establish a
# box (display: contents / display: none — these don't trigger the bug).
CSS_RULE_RE = re.compile(
    r"\.([a-zA-Z_][\w-]*)\s*(?:,[^{]+)?\{[^}]*\bdisplay\s*:\s*([a-zA-Z-]+)",
    re.DOTALL,
)

# `<class>[hidden] { display: none }` (or any explicit none-or-contents
# override) cancels the trap for that class.
HIDDEN_OVERRIDE_RE = re.compile(
    r"\.([a-zA-Z_][\w-]*)\[hidden\][^{]*\{[^}]*\bdisplay\s*:\s*none",
)

# A global `[hidden] { display: none !important }` cancels the trap
# universally. (Without `!important`, an author `.X { display: grid }`
# at specificity 0,1,0 still beats `[hidden]` at specificity 0,1,0 by
# source order if author comes later.)
GLOBAL_HIDDEN_RE = re.compile(
    r"(?<![\w.\-])\[hidden\][^{]*\{[^}]*\bdisplay\s*:\s*none\s*!important",
)

SAFE_DISPLAY = {"none", "contents"}  # these don't establish a box, no trap


def split_style_blocks(src: str) -> list[str]:
    """Extract the contents of every <style> block in an .astro file."""
    return re.findall(r"<style[^>]*>(.*?)</style>", src, re.DOTALL)


def split_script_blocks(src: str) -> list[str]:
    """Extract every <script> block (any flavour)."""
    return re.findall(r"<script[^>]*>(.*?)</script>", src, re.DOTALL)


def find_violations_in_file(path: Path, global_hidden_seen: bool) -> list[str]:
    """Return a list of violation messages for this file."""
    try:
        src = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"{path}: read failed ({e})"]

    scripts = "\n".join(split_script_blocks(src))
    if not HIDDEN_ASSIGN_RE.search(scripts):
        return []  # File doesn't toggle .hidden — nothing to check.

    styles = "\n".join(split_style_blocks(src))
    # Local global override?
    if GLOBAL_HIDDEN_RE.search(styles) or global_hidden_seen:
        return []  # `[hidden] { display: none !important }` covers everything.

    risky_classes = {
        cls
        for cls, disp in CSS_RULE_RE.findall(styles)
        if disp not in SAFE_DISPLAY
    }
    if not risky_classes:
        return []

    overridden = set(HIDDEN_OVERRIDE_RE.findall(styles))
    missing = sorted(risky_classes - overridden)
    if not missing:
        return []

    rel = path.as_posix()
    return [
        f"{rel}: class `.{cls}` sets `display:` in author CSS but has no "
        f"`.{cls}[hidden] {{ display: none }}` override. JS toggles "
        f"`.hidden` in this file — cards/rows won't actually hide. "
        f"Add `.{cls}[hidden] {{ display: none !important; }}`."
        for cls in missing
    ]


def scan_global_hidden_in_styles(roots: list[Path]) -> bool:
    """Return True if any CSS file (under the given roots) contains the
    global `[hidden] { display: none !important }` rule. If so, every
    page that loads the layout inherits it and the per-file check can
    skip the override requirement."""
    for root in roots:
        for css in root.rglob("*.css"):
            if any(skip in css.parts for skip in SKIP_DIRS):
                continue
            try:
                if GLOBAL_HIDDEN_RE.search(css.read_text(encoding="utf-8")):
                    return True
            except (OSError, UnicodeDecodeError):
                continue
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Files or directories to scan. Defaults to the repo's web/src/.",
    )
    args = parser.parse_args()

    if args.paths:
        roots = [p.resolve() for p in args.paths]
    else:
        repo_root = Path(__file__).resolve().parent.parent
        roots = [repo_root / "web" / "src"]
        if not roots[0].exists():
            print(
                f"error: default path {roots[0]} does not exist; "
                f"pass a path explicitly",
                file=sys.stderr,
            )
            return 2

    astro_files: list[Path] = []
    for root in roots:
        if root.is_file():
            astro_files.append(root)
            continue
        for p in root.rglob("*.astro"):
            if any(skip in p.parts for skip in SKIP_DIRS):
                continue
            astro_files.append(p)

    # Search CSS roots once for a global override (e.g.
    # `web/src/styles/reset.css`) before we scan files.
    css_roots = []
    for root in roots:
        if root.is_dir():
            css_roots.append(root)
        else:
            css_roots.append(root.parent)
    global_hidden_seen = scan_global_hidden_in_styles(css_roots)

    violations: list[str] = []
    for path in sorted(astro_files):
        violations.extend(find_violations_in_file(path, global_hidden_seen))

    if violations:
        print("✗ Hidden-cascade violations:\n", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(
            f"\n{len(violations)} violation(s) across {len({v.split(':',1)[0] for v in violations})} file(s).",
            file=sys.stderr,
        )
        return 1

    print(f"✓ {len(astro_files)} .astro files clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
