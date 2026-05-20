#!/usr/bin/env python3
"""
Generiert Karten-PNGs aus einem Reiseplan-JSON.

Usage:
    python3 generate_maps.py <plan.json> <output_dir>
"""

import json
import math
import os
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont
from staticmap import StaticMap, IconMarker, Line

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SMALL = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def create_numbered_marker(num, size=36):
    """Erzeugt ein nummeriertes Marker-PNG."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Roter Kreis mit weißem Rand
    draw.ellipse(
        [1, 1, size - 2, size - 2],
        fill=(220, 53, 69, 255),
        outline=(255, 255, 255, 255),
        width=2,
    )
    try:
        font = ImageFont.truetype(FONT_PATH, 16)
    except Exception:
        font = ImageFont.load_default()
    text = str(num)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) / 2, (size - th) / 2 - 1),
        text,
        fill=(255, 255, 255, 255),
        font=font,
    )
    return img


def calculate_zoom(latitudes, longitudes, width, height, padding=1.5):
    """Berechnet einen passenden Zoom für eine Bounding Box."""
    if not latitudes or not longitudes:
        return 10
    min_lat, max_lat = min(latitudes), max(latitudes)
    min_lon, max_lon = min(longitudes), max(longitudes)

    lat_diff = (max_lat - min_lat) * padding
    lon_diff = (max_lon - min_lon) * padding
    if lat_diff < 0.01:
        lat_diff = 0.01
    if lon_diff < 0.01:
        lon_diff = 0.01

    # Padding um die Box herum
    lat_center = (min_lat + max_lat) / 2
    min_lat = lat_center - lat_diff / 2
    max_lat = lat_center + lat_diff / 2
    lon_center = (min_lon + max_lon) / 2
    min_lon = lon_center - lon_diff / 2
    max_lon = lon_center + lon_diff / 2

    def lon_to_x(lon, zoom):
        return (lon + 180) / 360 * (256 * (2 ** zoom))

    def lat_to_y(lat, zoom):
        lat_rad = math.radians(lat)
        return (1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * (256 * (2 ** zoom))

    for zoom in range(18, 0, -1):
        x_min = lon_to_x(min_lon, zoom)
        x_max = lon_to_x(max_lon, zoom)
        y_min = lat_to_y(max_lat, zoom)  # nördlicher = kleinerer y-Wert
        y_max = lat_to_y(min_lat, zoom)

        if (x_max - x_min) <= width and (y_max - y_min) <= height:
            return zoom
    return 1


def generate_overview_map(plan, output_path):
    """Generiert die große Übersichtskarte mit allen Städten."""
    cities = plan.get("overview_map", {}).get("cities", [])
    if not cities:
        print("Keine Städte für Übersichtskarte gefunden.")
        return

    lats = [c["lat"] for c in cities]
    lons = [c["lon"] for c in cities]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    width, height = 1200, 800
    zoom = calculate_zoom(lats, lons, width, height, padding=1.3)

    m = StaticMap(width, height, url_template="https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
    m.add_line(Line([(c["lon"], c["lat"]) for c in cities], "#e74c3c", 3))

    for i, city in enumerate(cities, 1):
        marker_path = os.path.join(tempfile.gettempdir(), f"marker_city_{i}.png")
        create_numbered_marker(i, size=40).save(marker_path)
        m.add_marker(
            IconMarker(
                (city["lon"], city["lat"]),
                marker_path,
                offset_x=20,
                offset_y=20,
            )
        )

    image = m.render(center=(center_lon, center_lat), zoom=zoom)
    image.save(output_path)
    print(f"Übersichtskarte gespeichert: {output_path}")


def generate_day_map(day, output_path):
    """Generiert eine Tageskarte mit nummerierten POIs."""
    schedule = day.get("schedule", [])
    pois = [s for s in schedule if "lat" in s and "lon" in s]
    if not pois:
        print(f"Tag {day['day_num']}: Keine POIs mit Koordinaten gefunden.")
        return

    lats = [p["lat"] for p in pois]
    lons = [p["lon"] for p in pois]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    width, height = 1000, 700
    zoom = calculate_zoom(lats, lons, width, height, padding=1.4)

    m = StaticMap(width, height, url_template="https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")

    # Route-Linie zwischen allen POIs
    if len(pois) > 1:
        m.add_line(Line([(p["lon"], p["lat"]) for p in pois], "#3498db", 3))

    for i, poi in enumerate(pois, 1):
        marker_path = os.path.join(tempfile.gettempdir(), f"marker_day_{day['day_num']}_{i}.png")
        create_numbered_marker(i, size=36).save(marker_path)
        m.add_marker(
            IconMarker(
                (poi["lon"], poi["lat"]),
                marker_path,
                offset_x=18,
                offset_y=18,
            )
        )

    image = m.render(center=(center_lon, center_lat), zoom=zoom)
    image.save(output_path)
    print(f"Tageskarte Tag {day['day_num']} gespeichert: {output_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 generate_maps.py <plan.json> <output_dir>")
        sys.exit(1)

    plan_path = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    overview_path = os.path.abspath(os.path.join(output_dir, "overview_map.png"))
    generate_overview_map(plan, overview_path)
    if os.path.exists(overview_path):
        plan["overview_map"]["local_image"] = overview_path

    for day in plan.get("days", []):
        day_map_path = os.path.abspath(os.path.join(output_dir, f"day_{day['day_num']:02d}_map.png"))
        generate_day_map(day, day_map_path)
        if os.path.exists(day_map_path):
            day["map_image"] = day_map_path

    out_path = os.path.join(os.path.dirname(plan_path), "plan_with_maps.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print(f"Plan mit Karten gespeichert: {out_path}")


if __name__ == "__main__":
    main()
