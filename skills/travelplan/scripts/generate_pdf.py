#!/usr/bin/env python3
"""
Generiert die finale PDF aus dem Reiseplan-JSON mit WeasyPrint.

Usage:
    python3 generate_pdf.py <plan.json> <output.pdf>
"""

import json
import os
import sys

import jinja2
from weasyprint import HTML, CSS

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(SKILL_DIR, "assets", "template.html")
CSS_PATH = os.path.join(SKILL_DIR, "assets", "style.css")


def generate_pdf(plan_path, output_path):
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    # Stelle sicher, dass alle Pfade absolute Pfade sind
    def fix_path(p):
        if p and not os.path.isabs(p):
            return os.path.abspath(os.path.join(os.path.dirname(plan_path), p))
        return p

    if plan.get("hero_image"):
        plan["hero_image"] = fix_path(plan["hero_image"])
    if plan.get("overview_map", {}).get("local_image"):
        plan["overview_map"]["local_image"] = fix_path(plan["overview_map"]["local_image"])
    for city in plan.get("overview_map", {}).get("cities", []):
        if city.get("local_image"):
            city["local_image"] = fix_path(city["local_image"])
    for day in plan.get("days", []):
        if day.get("map_image"):
            day["map_image"] = fix_path(day["map_image"])
        for item in day.get("schedule", []):
            if item.get("local_image"):
                item["local_image"] = fix_path(item["local_image"])

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template_src = f.read()

    template = jinja2.Template(template_src)
    html_content = template.render(**plan)

    # Temporäre HTML-Datei für Debugging (optional)
    html_debug = os.path.splitext(output_path)[0] + ".html"
    with open(html_debug, "w", encoding="utf-8") as f:
        f.write(html_content)

    HTML(string=html_content, base_url=SKILL_DIR).write_pdf(
        output_path, stylesheets=[CSS(filename=CSS_PATH)]
    )
    print(f"PDF generiert: {output_path}")
    print(f"Debug-HTML: {html_debug}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 generate_pdf.py <plan.json> <output.pdf>")
        sys.exit(1)

    plan_path = sys.argv[1]
    output_path = sys.argv[2]
    generate_pdf(plan_path, output_path)


if __name__ == "__main__":
    main()
