#!/usr/bin/env python3
"""
playwright_recheck.py — re-check the NEEDS-HUMAN URLs from link-check-patches.md
using a real browser via Playwright.

Why: httpx-based check_links.py is blocked by aggressive UA-sniffing (LinkedIn 999,
Cloudflare 202, equal1/qolab returning 404 to bots) on a class of URLs that work
fine in a normal browser. Playwright drives a real Chromium and gets through.

Output: same status taxonomy as check_links.py, written to
link-check-recheck.md next to the original report.

Usage:
    python3 scripts/playwright_recheck.py
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PATCHES_PATH = REPO_ROOT / "link-check-patches.md"
OUTPUT_PATH = REPO_ROOT / "link-check-recheck.md"

TIMEOUT_MS = 25_000  # per page, includes navigation + initial paint
CONCURRENCY = 6      # parallel browser contexts


def extract_needs_human_urls(text: str) -> list[str]:
    """Pull every URL from rows whose Status column is NEEDS-HUMAN.

    The patches file has two-pipe-table form:
      | source | line | old | new | confidence | reason |
    Rows where confidence==NEEDS-HUMAN are the targets. The 'old' URL is what we
    re-check. (Sometimes the 'new' column also contains NEEDS-HUMAN as a sentinel.)
    """
    urls: list[str] = []
    seen: set[str] = set()
    url_re = re.compile(r"https?://[^\s)|]+")
    for line in text.splitlines():
        if "NEEDS-HUMAN" not in line:
            continue
        if not line.lstrip().startswith("|"):
            continue
        # Skip rows that are clearly footer notes rather than table data.
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        # Find URL(s) in the third column (old URL).
        for m in url_re.finditer(cells[2]):
            url = m.group(0).rstrip(".,;:")
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


async def check_one(browser, url: str) -> dict:
    """Open a fresh context (no shared cookies), navigate, classify.

    Cloudflare "Just A Moment" interstitials return HTTP 202 with a JS
    challenge that resolves in 2-5 s. Read content twice — once after
    domcontentloaded, then again after waiting for networkidle + a short
    settle delay — so the post-challenge body is what gets classified.
    The first read just sets the geometry; the second is authoritative.
    """
    from playwright.async_api import Error as PWError, TimeoutError as PWTimeout
    ctx = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
        locale="en-US",
    )
    page = await ctx.new_page()
    started = time.monotonic()
    result = {"url": url, "status": "unknown", "http_status": None, "final_url": url, "note": ""}
    try:
        resp = await page.goto(url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
        # Let any anti-bot interstitial run. networkidle waits until no in-flight
        # requests for 500 ms; the extra sleep covers JS-driven redirects that
        # finish just after networkidle (Cloudflare's "Just A Moment" pattern).
        try:
            await page.wait_for_load_state("networkidle", timeout=10_000)
        except PWTimeout:
            pass
        await page.wait_for_timeout(1500)
        elapsed = time.monotonic() - started
        if resp is None:
            result.update(status="suspicious", note="no response object")
        else:
            result["http_status"] = resp.status
            result["final_url"] = page.url
            try:
                body = (await page.content())[:8000].lower()
            except PWError:
                body = ""  # page navigated mid-read; classify by HTTP status alone
            title = (await page.title()).strip().lower() if body else ""
            challenge_markers = (
                "just a moment",  # Cloudflare interstitial title
                "checking your browser",
                "captcha", "cf-challenge", "challenge-platform",
                "are you human",
            )
            looks_like_challenge = any(m in body for m in challenge_markers) or "just a moment" in title

            # The HTTP status reported by Playwright is the *final* response
            # after any client-side redirect chain. If the body resolved past
            # the Cloudflare challenge, the page is genuinely live regardless
            # of the original 202 / 999 status.
            if not looks_like_challenge and resp.status in (200, 202) and len(body) >= 500:
                result.update(status="ok", note=f"loaded in {elapsed:.1f}s (final HTTP {resp.status})")
            elif resp.status == 200:
                if looks_like_challenge:
                    result.update(status="captcha", note=f"challenge body still present after {elapsed:.1f}s")
                elif len(body) < 500:
                    result.update(status="suspicious", note=f"tiny body ({len(body)}b)")
                else:
                    result.update(status="ok", note=f"loaded in {elapsed:.1f}s")
            elif resp.status == 202:
                # Body didn't clear past the challenge in time. Page is live;
                # Cloudflare is just stricter than our wait window.
                result.update(status="captcha", note=f"CF challenge unresolved after {elapsed:.1f}s")
            elif resp.status in (301, 302, 303, 307, 308):
                result.update(status="redirect-stable", note=f"→ {page.url}")
            elif resp.status in (404, 410):
                result.update(status="gone", note=f"HTTP {resp.status}")
            elif resp.status == 429:
                result.update(status="rate-limited", note=f"HTTP {resp.status}")
            elif resp.status == 999:
                # LinkedIn anti-bot. Treat as live; their slugs are stable and
                # the link target is by definition a person, not content.
                result.update(status="captcha", note="LinkedIn 999 — anti-bot, URL likely valid")
            elif 500 <= resp.status < 600:
                result.update(status="server-error", note=f"HTTP {resp.status}")
            else:
                result.update(status="suspicious", note=f"HTTP {resp.status}")
    except PWTimeout:
        result.update(status="slow", note=f"timeout after {TIMEOUT_MS/1000:.0f}s")
    except PWError as e:
        msg = str(e).split("\n", 1)[0]
        if "ERR_NAME_NOT_RESOLVED" in msg or "ERR_CONNECTION_REFUSED" in msg:
            result.update(status="gone", note=msg)
        elif "ERR_CERT" in msg or "SSL" in msg:
            result.update(status="tls-error", note=msg)
        else:
            result.update(status="suspicious", note=msg)
    finally:
        try:
            await ctx.close()
        except Exception:
            pass
    return result


async def main() -> int:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("error: playwright not installed (pip install playwright)", file=sys.stderr)
        return 2

    if not PATCHES_PATH.exists():
        print(f"error: {PATCHES_PATH} not found — run the link checker first", file=sys.stderr)
        return 2

    urls = extract_needs_human_urls(PATCHES_PATH.read_text(encoding="utf-8"))
    if not urls:
        print("no NEEDS-HUMAN URLs found", file=sys.stderr)
        return 0
    print(f"re-checking {len(urls)} NEEDS-HUMAN URLs via Playwright...", file=sys.stderr)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        sem = asyncio.Semaphore(CONCURRENCY)

        async def bound(u: str) -> dict:
            async with sem:
                return await check_one(browser, u)

        results = await asyncio.gather(*(bound(u) for u in urls))
        await browser.close()

    # Group by status, broken-first
    order = ["gone", "tls-error", "suspicious", "captcha", "rate-limited", "slow",
             "server-error", "redirect-stable", "ok"]
    grouped: dict[str, list[dict]] = {s: [] for s in order}
    for r in results:
        grouped.setdefault(r["status"], []).append(r)

    lines = ["# Playwright re-check of NEEDS-HUMAN URLs", "",
             f"Re-checked {len(results)} URLs via headless Chromium.", "",
             "## Summary", ""]
    for s in order:
        if grouped.get(s):
            lines.append(f"- `{s}` — {len(grouped[s])}")
    lines.append("")

    for s in order:
        rows = grouped.get(s, [])
        if not rows:
            continue
        lines.append(f"## {s} ({len(rows)})")
        lines.append("")
        for r in rows:
            lines.append(f"- `{r['url']}`")
            lines.append(f"  - HTTP {r.get('http_status')} — {r.get('note')}")
            if r.get("final_url") and r["final_url"] != r["url"]:
                lines.append(f"  - final: `{r['final_url']}`")
        lines.append("")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
