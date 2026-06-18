#!/usr/bin/env python3
"""
check_links.py — verify every http(s) URL in any YAML file is reachable.

Schema-agnostic: walks the parsed YAML tree, collects every string value
that starts with `http://` or `https://` regardless of key name, then
probes each URL in parallel.

Usage:
    # All YAMLs under the repo (auto-discovers, skips node_modules / dist / .git)
    python3 scripts/check_links.py

    # Specific files
    python3 scripts/check_links.py standards/itu-t.yaml companies/cisco.yaml

    # A directory tree
    python3 scripts/check_links.py standards/

    # Options
    python3 scripts/check_links.py --workers 20 --timeout 20 --only-fail
    python3 scripts/check_links.py --csv out.csv

Output:
    Each row shows  STATUS  file::yaml-path  URL  [note]
    The yaml-path lets you grep the source file straight to the entry.
    Exits 1 if any link is broken, 0 otherwise — usable in CI.
"""

from __future__ import annotations
import argparse
import csv as csvmod
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip3 install requests pyyaml")

try:
    import yaml
except ImportError:
    sys.exit("PyYAML not installed. Run: pip3 install pyyaml")

# Resolve repo root from this file's location (scripts/check_links.py → repo/).
REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_DIR_NAMES = {"node_modules", "dist", ".git", ".astro"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.5 Safari/605.1.15"
    ),
    # Some hosts (BSI in particular) reject `Accept: */*` — match what a
    # real browser sends.
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

OK_STATUSES = {200, 301, 302, 303, 307, 308}


# ---- YAML walking ------------------------------------------------------------

def is_url(s) -> bool:
    return isinstance(s, str) and (s.startswith("http://") or s.startswith("https://"))


def walk(node, path: str = ""):
    """Yield (yaml_path, url) for every URL-shaped string in the tree."""
    if isinstance(node, dict):
        for k, v in node.items():
            child_path = f"{path}.{k}" if path else str(k)
            yield from walk(v, child_path)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")
    elif is_url(node):
        yield (path, node.strip())


def collect_urls(yaml_path: Path):
    """Return [(yaml_path, url), ...] for one file. None on parse error."""
    try:
        with yaml_path.open() as f:
            doc = yaml.safe_load(f)
    except yaml.YAMLError:
        return None
    return list(walk(doc))


def discover_yamls(start: Path):
    """Recursive find of *.yaml / *.yml, skipping build / vcs / scratch dirs."""
    out = []
    for root, dirs, files in os.walk(start):
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES]
        for fn in files:
            if fn.endswith((".yaml", ".yml")):
                out.append(Path(root) / fn)
    return sorted(out)


# ---- Probe -------------------------------------------------------------------

def probe(url: str, timeout: int = 15):
    """Return (status_code or None, note). None means network failure."""
    try:
        r = requests.head(url, headers=HEADERS, allow_redirects=True,
                          timeout=timeout, verify=True)
        if r.status_code in OK_STATUSES:
            return r.status_code, ""
        if r.status_code in (400, 403, 405, 501):
            # Some hosts block HEAD (BSI returns 400, others 403/405/501).
            # Retry with GET; doubled timeout for the slow-server case.
            r = requests.get(url, headers=HEADERS, allow_redirects=True,
                             timeout=timeout * 2, stream=True, verify=True)
            r.close()
            return r.status_code, "via GET"
        return r.status_code, ""
    except requests.exceptions.SSLError as e:
        return None, f"SSL: {type(e).__name__}"
    except requests.exceptions.Timeout:
        return None, "timeout"
    except requests.exceptions.ConnectionError as e:
        return None, f"connection: {type(e).__name__}"
    except requests.exceptions.RequestException as e:
        return None, f"req: {type(e).__name__}"


# ---- Formatting --------------------------------------------------------------

def fmt(rel_file, ypath, url, status, note) -> str:
    short_url = url if len(url) <= 70 else url[:67] + "..."
    if status in OK_STATUSES:
        marker = "OK   "
    elif status is None:
        marker = "ERR  "
    else:
        marker = f"{status:>4} "
    locator = f"{rel_file}::{ypath}" if ypath else rel_file
    if len(locator) > 50:
        locator = locator[:47] + "..."
    note_str = ("  " + note) if note else ""
    return f"{marker}  {locator:<50}  {short_url}{note_str}"


# ---- Entry point -------------------------------------------------------------

def expand_targets(args_files):
    """Turn CLI args into a list of yaml Paths."""
    if not args_files:
        return discover_yamls(REPO_ROOT)
    paths = []
    for a in args_files:
        p = Path(a)
        if not p.is_absolute() and not p.exists():
            alt = REPO_ROOT / a
            if alt.exists():
                p = alt
        if p.is_dir():
            paths.extend(discover_yamls(p))
        elif p.suffix in (".yaml", ".yml"):
            paths.append(p)
        else:
            print(f"warn: skipping non-yaml target {p}", file=sys.stderr)
    return sorted(set(paths))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("paths", nargs="*",
                    help="yaml files or directories (default: whole repo)")
    ap.add_argument("--workers", type=int, default=12,
                    help="parallel probes (default 12)")
    ap.add_argument("--timeout", type=int, default=15,
                    help="per-request HEAD timeout in s (GET fallback gets 2x)")
    ap.add_argument("--csv", metavar="PATH",
                    help="also write a full CSV report")
    ap.add_argument("--only-fail", action="store_true",
                    help="suppress OK rows from stdout")
    args = ap.parse_args()

    yaml_paths = expand_targets(args.paths)
    if not yaml_paths:
        sys.exit("No yaml files found.")

    urls = []  # (rel_file, yaml-path, url)
    bad_files = []
    for yp in yaml_paths:
        try:
            rel = yp.relative_to(REPO_ROOT)
        except ValueError:
            rel = yp
        found = collect_urls(yp)
        if found is None:
            bad_files.append(str(rel))
            continue
        for ypath, u in found:
            urls.append((str(rel), ypath, u))

    if bad_files:
        print("warn: failed to parse these yaml files:", file=sys.stderr)
        for f in bad_files:
            print(f"  {f}", file=sys.stderr)

    print(f"Probing {len(urls)} URLs across {len(yaml_paths)} yaml files "
          f"(workers={args.workers}, timeout={args.timeout}s)\n",
          file=sys.stderr)

    started = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(probe, u, args.timeout): (rel, yp, u)
                   for (rel, yp, u) in urls}
        done = 0
        for fut in as_completed(futures):
            rel, yp, u = futures[fut]
            status, note = fut.result()
            results.append((rel, yp, u, status, note))
            done += 1
            if done % 25 == 0 or done == len(urls):
                print(f"  ... {done}/{len(urls)}", file=sys.stderr)

    fails = [r for r in results if r[3] not in OK_STATUSES]
    oks   = [r for r in results if r[3] in OK_STATUSES]

    fails.sort(key=lambda r: (r[0], r[1]))
    oks.sort(key=lambda r: (r[0], r[1]))

    if fails:
        print(f"\n{len(fails)} broken / suspect:\n")
        for r in fails:
            print(fmt(*r))
    if not args.only_fail and oks:
        print(f"\n{len(oks)} OK:\n")
        for r in oks:
            print(fmt(*r))

    elapsed = time.time() - started
    print(f"\nDone in {elapsed:.1f}s — {len(oks)} OK, {len(fails)} broken/suspect.",
          file=sys.stderr)

    if args.csv:
        with open(args.csv, "w", newline="") as cf:
            w = csvmod.writer(cf)
            w.writerow(["file", "yaml_path", "url", "status", "note"])
            for r in results:
                w.writerow(r)
        print(f"Wrote {args.csv}", file=sys.stderr)

    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
