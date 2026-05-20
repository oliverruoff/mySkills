---
name: wetter-forecast
description: Recherchiert das Wetter für die nächsten 3 Tage anhand von PLZ und Land. Gibt Temperatur, Wetterlage (Sonne, Wolken, Regen, Schnee etc.) und eine Kleidungsempfehlung aus. Verwendet Open-Meteo und Nominatim (OpenStreetMap). Kein API-Key nötig. Standard-Standort ist 74239 DE.
compatibility: Benötigt Python 3 und Internet-Zugang.
metadata:
  version: "1.0"
---

# Wetter-Forecast

Zeigt das Wetter für die nächsten 3 Tage an einem per PLZ angegebenen Ort.

## Parameter

- `plz` – Postleitzahl (Default: `74239`)
- `land` – Ländercode, 2-stellig (Default: `DE`)

## Ausführung

```bash
./scripts/wetter.py [PLZ] [LAND]
```

Beispiele:

```bash
./scripts/wetter.py                # Default: 74239, DE
./scripts/wetter.py 10115 DE       # Berlin
./scripts/wetter.py 80331 DE       # München
```

## Ausgabe

Das Script liefert pro Tag:

- Datum & Wochentag (Heute / Morgen / Übermorgen)
- Temperaturspanne (min – max)
- Wetterlage mit Emoji (Sonne, Wolken, Regen, Schnee, Gewitter etc.)
- Niederschlagsmenge (falls vorhanden)
- Kleidungsempfehlung basierend auf Temperatur und Wetter

## Quellen

- **Geocoding:** Nominatim (OpenStreetMap)
- **Wetterdaten:** Open-Meteo API (kostenlos, keine Registrierung nötig)
