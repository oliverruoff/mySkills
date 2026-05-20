#!/usr/bin/env python3
"""
Wetter-Skill für pi.
Nutzt Open-Meteo API (kostenlos, kein API-Key nötig).
Parameter: <plz> <land>
Default: 74239 DE
"""

import sys
import urllib.request
import urllib.parse
import json
from datetime import datetime

PLZ_DEFAULT = "74239"
LAND_DEFAULT = "DE"

WETTER_CODES = {
    0:  "Klarer Himmel / Sonnig",
    1:  "Meist sonnig",
    2:  "Teilweise bewölkt",
    3:  "Bedeckt",
    45: "Nebel",
    48: "Nebel mit Reifbildung",
    51: "Leichter Nieselregen",
    53: "Mäßiger Nieselregen",
    55: "Starker Nieselregen",
    56: "Leichter gefrierender Niesel",
    57: "Starker gefrierender Niesel",
    61: "Leichter Regen",
    63: "Mäßiger Regen",
    65: "Starker Regen",
    66: "Leichter gefrierender Regen",
    67: "Starker gefrierender Regen",
    71: "Leichter Schneefall",
    73: "Mäßiger Schneefall",
    75: "Starker Schneefall",
    77: "Schneegriesel",
    80: "Leichte Regenschauer",
    81: "Mäßige Regenschauer",
    82: "Starke Regenschauer",
    85: "Leichte Schneeschauer",
    86: "Starke Schneeschauer",
    95: "Gewitter",
    96: "Gewitter mit leichtem Hagel",
    99: "Gewitter mit schwerem Hagel",
}


def empfehlung(t_min, t_max, code):
    """Gibt eine Kleidungsempfehlung basierend auf Temperatur und Wetter."""
    t_mittel = (t_min + t_max) / 2

    teile = []
    if t_max < 0:
        teile.append("🧥 Sehr warm anziehen: Winterjacke, Mütze, Schal, Handschuhe, warme Schuhe.")
    elif t_max < 5:
        teile.append("🧥 Warm anziehen: Winterjacke, Mütze und Schal empfohlen.")
    elif t_max < 10:
        teile.append("🧥 Jacke und Pullover sind angesagt.")
    elif t_max < 15:
        teile.append("🧥 Leichte Jacke oder dicker Pullover.")
    elif t_max < 20:
        teile.append("👕 T-Shirt + leichte Jacke oder Langarm.")
    elif t_max < 25:
        teile.append("👕 T-Shirt, kurze Hose ist möglich.")
    else:
        teile.append("🩳 Leichte Sommerkleidung, kurze Hose und T-Shirt.")

    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        teile.append("☔ Regenjacke/Schirm nicht vergessen!")
    elif code in (71, 73, 75, 77, 85, 86):
        teile.append("❄️ Wasserfeste warme Schuhe empfohlen.")
    elif code in (95, 96, 99):
        teile.append("⛈️ Achtung Gewitter – besser drinnen bleiben wenn möglich.")
    elif code in (45, 48):
        teile.append("🌫️ Sicht kann eingeschränkt sein.")

    return " ".join(teile)


def hole_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "pi-wetter-skill/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    plz = sys.argv[1] if len(sys.argv) > 1 else PLZ_DEFAULT
    land = sys.argv[2] if len(sys.argv) > 2 else LAND_DEFAULT

    # 1. Geocoding (Nominatim für PLZ)
    geo_url = (
        "https://nominatim.openstreetmap.org/search?"
        + urllib.parse.urlencode({
            "postalcode": plz,
            "country": land.upper(),
            "format": "json",
            "limit": 1,
        })
    )
    req = urllib.request.Request(geo_url, headers={"User-Agent": "pi-wetter-skill/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            geo = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Fehler beim Geocoding: {e}")
        sys.exit(1)

    if not geo:
        print(f"Kein Ort für PLZ {plz} ({land}) gefunden.")
        sys.exit(1)

    ort = geo[0]
    name = ort.get("display_name", plz).split(",")[0].strip()
    lat = float(ort["lat"])
    lon = float(ort["lon"])

    # 2. Wetter
    wetter_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urllib.parse.urlencode({
            "latitude": lat,
            "longitude": lon,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "Europe/Berlin",
            "forecast_days": 3,
        })
    )
    wetter = hole_json(wetter_url)
    daily = wetter["daily"]

    tage = ["Heute", "Morgen", "Übermorgen"]
    heute = datetime.now().date()

    print(f"📍 Wetter für {name} ({plz}, {land.upper()}) – nächste 3 Tage:\n")

    for i in range(3):
        datum = daily["time"][i]
        tag_name = tage[i]
        code = daily["weather_code"][i]
        t_min = daily["temperature_2m_min"][i]
        t_max = daily["temperature_2m_max"][i]
        regen = daily["precipitation_sum"][i]
        beschreibung = WETTER_CODES.get(code, f"Unbekannt (Code {code})")

        regen_text = f" | 🌧️ Niederschlag: {regen} mm" if regen and regen > 0 else ""

        print(f"{tag_name} ({datum}):")
        print(f"  🌡️ {t_min}°C – {t_max}°C")
        print(f"  🌤️ {beschreibung}{regen_text}")
        print(f"  👕 {empfehlung(t_min, t_max, code)}")
        print()


if __name__ == "__main__":
    main()
