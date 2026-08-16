#!/usr/bin/env python3
"""
Kleinanzeigen Search — quick CLI for searching kleinanzeigen.de by location and radius.

Standalone skill: ships its own Playwright dependency, no external configuration required.

Usage:
    python scripts/search.py --query "apple macbook" --plz "80331 München"
    python scripts/search.py --query "mac mini" --plz "74072 Heilbronn" --radius 20 --top 5
    python scripts/search.py --query "iphone 14" --plz "10115 Berlin" --radius 30 --format json
"""

import argparse
import json
import re
import sys
from urllib.parse import quote_plus

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print(
        "Error: playwright is not installed.\n"
        "Run: pip install -r requirements.txt && playwright install chromium",
        file=sys.stderr,
    )
    sys.exit(1)

BASE_URL = "https://www.kleinanzeigen.de"
DEFAULT_RADIUS = 40
DEFAULT_TOP = 10


def build_search_url(query: str, plz: str, radius: int) -> str:
    """Build the Kleinanzeigen search URL with location and radius."""
    # Kleinanzeigen uses dash-separated search terms in the URL slug
    query_slug = query.strip().replace(" ", "-")
    return (
        f"{BASE_URL}/s-{quote_plus(query_slug)}/k0"
        f"?locationStr={quote_plus(plz)}&radius={radius}"
    )


def extract_items(page, top_n: int) -> list:
    """Extract the top-N search results from the results page."""
    items = page.query_selector_all("article")
    results = []

    for item in items[:top_n]:
        # JSON-LD for title + description
        data = {}
        json_ld = item.query_selector("script[type='application/ld+json']")
        if json_ld:
            try:
                data = json.loads(json_ld.inner_text())
            except (json.JSONDecodeError, ValueError):
                pass

        # Fallback: text regex for price, location, date
        raw_text = item.inner_text() or ""

        # Price (often appears multiple times, take first match)
        price_match = re.search(r"(\d{1,3}(?:[.,]\d{3})*)\s*(?:€|EUR|VB)", raw_text)
        price = price_match.group(0) if price_match else ""

        # Location (PLZ + place + distance)
        loc_match = re.search(r"(\d{5})\s+([^()]+?)\s*\((\d+)\s*km\)", raw_text)
        location = loc_match.group(0) if loc_match else ""

        # Date (Heute / Gestern / DD.MM.YYYY)
        date_match = re.search(r"(Heute|Gestern|\d{2}\.\d{2}\.\d{4})", raw_text)
        date = date_match.group(0) if date_match else ""

        # Link from the listing title anchor
        link = ""
        for a in item.query_selector_all("a"):
            anchor_text = (a.inner_text() or "").strip()
            if len(anchor_text) > 10:
                href = a.get_attribute("href") or ""
                if href.startswith("/"):
                    link = BASE_URL + href
                elif href.startswith("http"):
                    link = href
                break

        results.append({
            "title": (data.get("title") or "").strip(),
            "price": price.strip(),
            "location": location.strip(),
            "date": date.strip(),
            "link": link,
            "description": (data.get("description") or "").strip()[:300],
        })

    return results


def search(query: str, plz: str, radius: int, top_n: int, headless: bool = True) -> dict:
    """
    Run the search and return a dict with:
    - query, plz, radius, url
    - total_results (if readable)
    - items (top-N results)
    """
    url = build_search_url(query, plz, radius)
    payload = {"query": query, "plz": plz, "radius": radius, "url": url, "items": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # Wait for the first listing (vanishes if no results)
            try:
                page.wait_for_selector("article", timeout=20000)
            except PlaywrightTimeoutError:
                payload["total_results"] = 0
                return payload

            # Total result count from the breadcrumb text
            try:
                body_text = page.inner_text("body") or ""
                count_match = re.search(
                    r"(\d{1,3}(?:\.\d{3})*)\s+Ergebnissen", body_text
                )
                if count_match:
                    payload["total_results"] = count_match.group(1)
            except Exception:
                pass

            payload["items"] = extract_items(page, top_n)
        finally:
            browser.close()

    return payload


def format_markdown(payload: dict) -> str:
    """Format the results as a compact Markdown list (chat-friendly)."""
    query = payload.get("query", "")
    plz = payload.get("plz", "")
    radius = payload.get("radius", "")
    total = payload.get("total_results", "?")
    items = payload.get("items", [])

    lines = []
    lines.append(f"## 🔍 Kleinanzeigen Search: \"{query}\"")
    lines.append(
        f"📍 **{plz}** · Radius **{radius} km** · "
        f"**{total}** total results"
    )
    lines.append("")

    if not items:
        lines.append("⚠️ No listings found.")
        return "\n".join(lines)

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for i, r in enumerate(items, 1):
        medal = medals.get(i, f"**{i}.**")
        title = r["title"] or "(no title)"
        price = r["price"] or "Price on request"
        location = r["location"] or "Location unknown"
        date = r["date"] or "Date unknown"
        link = r["link"] or ""

        lines.append(f"{medal} **{title}**")
        lines.append(f"💰 {price} · 📍 {location} · 📅 {date}")
        if link:
            lines.append(f"🔗 {link}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quick Kleinanzeigen.de search with location and radius.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--query", "-q", required=True, help="Search term")
    parser.add_argument(
        "--plz",
        "-p",
        required=True,
        help="Postal code + place (e.g. '10115 Berlin', '80331 München')",
    )
    parser.add_argument(
        "--radius", "-r", type=int, default=DEFAULT_RADIUS, help="Search radius in km"
    )
    parser.add_argument(
        "--top", "-n", type=int, default=DEFAULT_TOP, help="Number of top results"
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--show-browser", action="store_true", help="Show browser window (debug)"
    )
    args = parser.parse_args()

    try:
        payload = search(
            query=args.query,
            plz=args.plz,
            radius=args.radius,
            top_n=args.top,
            headless=not args.show_browser,
        )
    except Exception as e:
        print(f"❌ Search failed: {e}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(payload))

    return 0


if __name__ == "__main__":
    sys.exit(main())
