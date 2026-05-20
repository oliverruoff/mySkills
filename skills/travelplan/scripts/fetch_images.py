#!/usr/bin/env python3
"""
Lädt Bilder für einen Reiseplan herunter (Wikimedia Commons + Brave Search Fallback).

Usage:
    python3 fetch_images.py <plan.json> <output_dir>

Schreibt plan_with_images.json mit "local_image" Pfaden.
"""

import json
import os
import sys
import time
import urllib.parse

import requests

BRAVE_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY")
HEADERS_BRAVE = {
    "Accept": "application/json",
    "X-Subscription-Token": BRAVE_API_KEY or "",
}

WM_API = "https://commons.wikimedia.org/w/api.php"
REQUESTS_TIMEOUT = 20

# Wikimedia requires a proper User-Agent for both API and download
HEADERS_WM = {
    "User-Agent": "pi-travelplan/1.0 (pi.agent@localhost)",
}
HEADERS_DOWNLOAD = {
    "User-Agent": "pi-travelplan/1.0 (pi.agent@localhost)",
    "Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}

_last_wm_call = 0
_last_brave_call = 0


def _rate_limit_wm(delay=0.6):
    """Wikimedia Commons API: max ~2 req/s realistically."""
    global _last_wm_call
    elapsed = time.time() - _last_wm_call
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _last_wm_call = time.time()


def _rate_limit_brave(delay=1.2):
    """Brave Free Plan: max 1 req/s."""
    global _last_brave_call
    elapsed = time.time() - _last_brave_call
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _last_brave_call = time.time()


def sanitize_filename(name):
    """Erzeugt einen sicheren Dateinamen."""
    name = name.replace(" ", "_").replace("/", "_")
    return "".join(c for c in name if c.isalnum() or c in "_-").rstrip("_")[:60]


def _clean_url(url):
    """Entfernt Tracking-Query-Params von Wikimedia-URLs."""
    if not url:
        return url
    parsed = urllib.parse.urlparse(url)
    # Keep only necessary path, drop utm_ params
    return urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, "", "", "")
    )


def search_wikimedia(query, limit=5):
    """Sucht bei Wikimedia Commons nach Bildern."""
    _rate_limit_wm()
    try:
        r = requests.get(
            WM_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srnamespace": 6,
                "format": "json",
                "srlimit": limit,
                "origin": "*",
            },
            headers=HEADERS_WM,
            timeout=REQUESTS_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        results = data.get("query", {}).get("search", [])
        titles = [r["title"] for r in results]
        if not titles:
            return []
        _rate_limit_wm()
        r2 = requests.get(
            WM_API,
            params={
                "action": "query",
                "titles": "|".join(titles),
                "prop": "imageinfo",
                "iiprop": "url|size|extmetadata",
                "format": "json",
                "origin": "*",
            },
            headers=HEADERS_WM,
            timeout=REQUESTS_TIMEOUT,
        )
        r2.raise_for_status()
        pages = r2.json().get("query", {}).get("pages", {})
        urls = []
        for page in pages.values():
            info = page.get("imageinfo", [{}])[0]
            url = info.get("url")
            if url:
                urls.append(_clean_url(url))
        return urls
    except Exception as e:
        print(f'Wikimedia-Fehler für "{query}": {e}')
        return []


def search_brave_images(query, count=5):
    """Sucht über Brave Search Images. Free-Plan: max 1 req/s."""
    if not BRAVE_API_KEY:
        print("Kein BRAVE_SEARCH_API_KEY gesetzt, überspringe Brave Images.")
        return []
    _rate_limit_brave()
    try:
        r = requests.get(
            "https://api.search.brave.com/res/v1/images/search",
            headers=HEADERS_BRAVE,
            params={"q": query, "count": count},
            timeout=REQUESTS_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        urls = []
        for res in results:
            url = res.get("image") or res.get("properties", {}).get("url")
            if url:
                urls.append(_clean_url(url))
        return urls
    except Exception as e:
        print(f'Brave-Fehler für "{query}": {e}')
        return []


def download_image(url, output_path):
    """Lädt ein Bild herunter und speichert es."""
    url = _clean_url(url)
    try:
        # Small delay to be nice to image servers
        time.sleep(0.2)
        r = requests.get(url, headers=HEADERS_DOWNLOAD, timeout=REQUESTS_TIMEOUT)
        r.raise_for_status()
        # Basic content-type check
        content_type = r.headers.get("Content-Type", "")
        if "image" not in content_type and "octet-stream" not in content_type:
            print(f"Skip {url}: not an image ({content_type})")
            return False
        with open(output_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"Download-Fehler {url}: {e}")
        return False


def get_image_for_keyword(keyword, output_dir, prefix):
    """Versucht Bild für ein Keyword zu finden und herunterzuladen."""
    if not keyword:
        return None
    safe_name = sanitize_filename(prefix + "_" + keyword)
    output_path = os.path.join(output_dir, f"{safe_name}.jpg")
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
        return output_path

    # 1. Wikimedia versuchen
    urls = search_wikimedia(keyword)
    for url in urls:
        if download_image(url, output_path):
            return output_path

    # 2. Brave Fallback
    urls = search_brave_images(keyword)
    for url in urls:
        if download_image(url, output_path):
            return output_path

    # 3. Wikimedia Direct FilePath Fallback
    direct_name = keyword.replace(" ", "_")
    for ext in ("jpg", "jpeg", "png"):
        direct_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{direct_name}.{ext}"
        if download_image(direct_url, output_path):
            return output_path

    return None


def fetch_all_images(plan, output_dir):
    """Durchläuft den Plan und lädt alle benötigten Bilder."""
    os.makedirs(output_dir, exist_ok=True)

    # Deckblatt / Titelbild
    if plan.get("hero_keyword"):
        path = get_image_for_keyword(plan["hero_keyword"], output_dir, "hero")
        if path:
            plan["hero_image"] = path

    # Städte-Übersicht
    for i, city in enumerate(plan.get("overview_map", {}).get("cities", []), 1):
        kw = city.get("image_keyword") or city.get("name")
        path = get_image_for_keyword(kw, output_dir, f"city_{i:02d}")
        if path:
            city["local_image"] = path

    # Tage & POIs
    for day in plan.get("days", []):
        for j, item in enumerate(day.get("schedule", []), 1):
            kw = item.get("image_keyword")
            if kw:
                path = get_image_for_keyword(kw, output_dir, f"day_{day['day_num']:02d}_poi_{j:02d}")
                if path:
                    item["local_image"] = path

    return plan


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 fetch_images.py <plan.json> <output_dir>")
        sys.exit(1)

    plan_path = sys.argv[1]
    output_dir = sys.argv[2]

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    plan = fetch_all_images(plan, output_dir)

    out_path = os.path.join(os.path.dirname(plan_path), "plan_with_images.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print(f"Plan mit Bild-Pfaden gespeichert: {out_path}")


if __name__ == "__main__":
    main()
