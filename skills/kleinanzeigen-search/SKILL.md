---
name: kleinanzeigen-search
description: Search kleinanzeigen.de (German classifieds) by any postal code and radius. Returns top-N listings with title, price, location, date, and link as chat-friendly Markdown or JSON. Use when the user wants to find listings on Kleinanzeigen / eBay Kleinanzeigen.
compatibility: Self-contained skill. Requires Python 3 and a Chromium browser installed via Playwright. First-time setup: `bash scripts/setup.sh`.
metadata:
  version: "1.0"
  author: pi.lot contributors
---

# Kleinanzeigen Search

Quick CLI for searching [kleinanzeigen.de](https://www.kleinanzeigen.de) — Germany's largest classifieds marketplace (formerly eBay Kleinanzeigen). The skill wraps a headless Chromium browser, navigates to the location- and radius-scoped search results, and extracts the top-N listings.

## Features

- **Location-precise search** — any postal code + place in Germany (e.g. `10115 Berlin`, `80331 München`, `50667 Köln`)
- **Adjustable radius** — default 40 km, configurable via `--radius`
- **Top-N extraction** — title, price, location, date, direct link
- **Two output formats** — Markdown (chat-friendly) or JSON (for programmatic use)
- **Standalone** — no other skills, no API keys, no cookies required

## Setup

One-time setup from the skill directory:

```bash
cd skills/kleinanzeigen-search
bash scripts/setup.sh
```

This installs Python dependencies (`playwright`) and downloads the Chromium browser. In minimal containers you may need to run `sudo playwright install-deps chromium` afterwards.

Manual setup:

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
# Minimal — search requires both --query and --plz
python scripts/search.py --query "apple macbook" --plz "80331 München"

# Custom radius and result count
python scripts/search.py --query "mac mini" --plz "74072 Heilbronn" --radius 20 --top 5

# JSON output for programmatic processing
python scripts/search.py --query "iphone 14" --plz "10115 Berlin" --format json

# Show the browser window (useful for debugging)
python scripts/search.py --query "playstation 5" --plz "80331 München" --show-browser
```

## CLI Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--query` | `-q` | **required** | Search term (becomes URL slug) |
| `--plz` | `-p` | **required** | Postal code + place, e.g. `"10115 Berlin"` |
| `--radius` | `-r` | `40` | Radius in km |
| `--top` | `-n` | `10` | Number of top results to return |
| `--format` | `-f` | `markdown` | `markdown` or `json` |
| `--show-browser` | — | `false` | Run Chromium visibly (debug) |

## Output Example

```
## 🔍 Kleinanzeigen Search: "apple macbook"
📍 80331 München · Radius 40 km · 163 total results

🥇 MacBook Pro 2020 13.3" Touch Bar
💰 430 € · 📍 74189 Weinsberg (13 km) · 📅 14.08.2026
🔗 https://www.kleinanzeigen.de/s-anzeige/apple-macbook-pro-2020-13-3-touch-bar/3484410412-278-9242

🥈 Apple Mac mini M2 / 16 GB / 256 GB SSD
💰 529 € · 📍 74081 Heilbronn (23 km) · 📅 Heute
🔗 https://www.kleinanzeigen.de/s-anzeige/apple-mac-mini-m2-16-gb-ram-256-gb-ssd-sehr-guter-zustand/3485960227-228-9246
```

## How It Works

1. **URL construction** — `https://www.kleinanzeigen.de/s-<query>/k0?locationStr=<plz>&radius=<r>`
   Direct URL navigation sidesteps the custom search widget (which does not respond to programmatic input).
2. **Headless Chromium** loads the page and waits for `<article>` elements.
3. **Extraction**:
   - **Title + description** from JSON-LD (`<script type="application/ld+json">`)
   - **Price** via regex `\d{1,3}(?:[.,]\d{3})*\s*(?:€|EUR|VB)`
   - **Location** via regex `\d{5}\s+([^\(]+)\s*\((\d+) km\)`
   - **Date** via regex `(Heute|Gestern|\d{2}\.\d{2}\.\d{4})`
   - **Link** from the first `<a>` with text > 10 characters
4. **Total count** is parsed from the breadcrumb line (`163 Ergebnissen`).
5. **Output** is rendered as Markdown (default) or JSON.

## Extracted Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Listing title |
| `price` | string | Price as shown (e.g. `430 €`, `1.900 € VB`) |
| `location` | string | PLZ + place + distance (e.g. `74189 Weinsberg (13 km)`) |
| `date` | string | Heute / Gestern / DD.MM.YYYY |
| `link` | string | Direct URL to the listing |
| `description` | string | First 300 characters of the listing description |

## Known Limitations

- **Dealer / "Ankauf" listings** are not pre-filtered — they often appear at the top. Filter manually by title keywords (`"Ankauf"`, `"Händler"`, `"MWST"`) if unwanted.
- **Min/Max price filters** are not exposed via the URL. Kleinanzeigen requires internal filter IDs that are not derivable from the postal code. Add a future enhancement by clicking the sidebar price filter.
- **Detail scraper** is not included — this skill only extracts the search results page. A separate `detail.py` could open a listing, parse JSON-LD, and download images.
- **Login-gated actions** (sending a message, posting an ad) are out of scope. They require a persistent session with cookies.

## Possible Extensions (Backlog)

- Filter for "Privat only" by excluding dealer keywords
- Min/Max price filter via UI click
- Auto-pagination across all result pages
- Persistent `state/shown_ads.json` to avoid re-suggesting the same listings
- `detail.py` for opening a single listing and extracting images, seller profile, shipping options

## Privacy

This skill does not authenticate, store cookies, or send personal data. It fetches only public search results from kleinanzeigen.de.
