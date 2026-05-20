---
name: travelplan
description: Erstellt einen vollrecherchierten, druckfertigen Reiseplan als PDF mit Karten, Bildern, Zeitplan und Infos. Der Agent (pi) führt Recherche und Planung durch; die Skripte bauen Karten, laden Bilder und rendern die PDF via WeasyPrint.
---

# Travelplan – Reiseplan als PDF

## Setup

Einmalig vor dem ersten Gebrauch:

```bash
cd /workspace/skills/travelplan
pip install -r requirements.txt
```

Voraussetzungen:
- `BRAVE_SEARCH_API_KEY` als Umgebungsvariable (für Web-Recherche & Bilder)
- Internetzugang für Karten-Tiles (OpenStreetMap)

---

## Workflow (pi führt Schritt für Schritt aus)

### 1. Reisekontext erfassen
Der User gibt Ziel, Zeitraum, Dauer, Städte, Interessen und ggf. Budget bekannt.

### 2. Recherche durchführen
Nutze den **brave-search Skill** (oder direkt die API) und recherchiere pro Stadt/Region:
- Top-Sehenswürdigkeiten & POIs
- Öffnungszeiten & Eintrittspreise
- Anreise/Transport zwischen Städten (Zug, Flug, Bus)
- Lokale Transportmittel (Metro, Bus, Taxi)
- Restaurant-Empfehlungen in der Nähe von POIs
- Wetter für die Reisezeit (nutze ggf. den wetter-forecast Skill)
- Praktische Infos: Visum, Währung, Notfallnummern, Strom, Zeitzone, Apps

### 3. JSON-Plan erstellen
Erstelle eine Datei `plan.json` mit folgendem Schema. **Pi erstellt dieses JSON manuell** basierend auf der Recherche.

#### Schema

```json
{
  "title": "Reisetitel (z.B. 10 Tage China)",
  "dates": "15. – 24. Juni 2026",
  "travelers": "2 Personen",
  "subtitle": "Optionaler Untertitel",
  "hero_keyword": "Suchbegriff für Deckblatt-Bild (z.B. Great Wall of China)",
  "overview_map": {
    "cities": [
      {
        "name": "Peking",
        "lat": 39.9042,
        "lon": 116.4074,
        "nights": 4,
        "description": "Kurze Beschreibung der Stadt",
        "image_keyword": "Beijing cityscape"
      }
    ]
  },
  "weather": [
    {
      "city": "Peking",
      "date": "15.06.2026",
      "temp_max": 28,
      "temp_min": 18,
      "condition": "Sonne"
    }
  ],
  "days": [
    {
      "day_num": 1,
      "date": "15. Juni 2026",
      "city": "Peking",
      "highlights": "Ankunft, Tiananmen, Verbotene Stadt",
      "estimated_cost": "ca. 80 €",
      "weather": {
        "temp_max": 28,
        "temp_min": 18,
        "condition": "Sonne"
      },
      "schedule": [
        {
          "time": "09:00",
          "title": "Ankunft Flughafen Peking",
          "description": "Langere Beschreibung des POIs...",
          "type": "transport",
          "lat": 39.9042,
          "lon": 116.4074,
          "image_keyword": "Beijing Capital Airport",
          "duration": "–",
          "price": "–",
          "transport_info": "Flug LH722, dann Airport Express (30 min, 25 CNY)"
        },
        {
          "time": "14:00",
          "title": "Tiananmen-Platz",
          "description": "Der größte Platz der Welt...",
          "type": "sight",
          "lat": 39.9055,
          "lon": 116.3976,
          "image_keyword": "Tiananmen Square Beijing",
          "duration": "1,5 h",
          "price": "kostenlos",
          "transport_info": "Metro Line 1 zum Tiananmen East"
        }
      ],
      "daily_tip": "Nehmt Wasser mit – auf dem Platz gibt es kaum Schatten.",
      "map_image": "wird von generate_maps.py gesetzt"
    }
  ],
  "general_info": {
    "visa": "Deutsche Staatsbürger brauchen ein Visum...",
    "currency": "Yuan (CNY), 1 € ≈ 7,8 CNY (Stand 2026)",
    "emergency": "110 Polizei, 120 Krankenwagen, 119 Feuerwehr",
    "timezone": "UTC+8 (6h vor Mitteleuropa)",
    "language": "Mandarin (Putonghua)",
    "electricity": "220V, Stecker Typ A/C/I – Adapter nötig",
    "apps": "WeChat, DiDi (Taxi), Baidu Maps, Pleco (Übersetzer)",
    "customs": "Trinkgeld ist unüblich..."
  },
  "destinations": [
    {
      "name": "Peking",
      "nights": 5,
      "description": "Ausführliche Beschreibung der Stadt...",
      "highlights": [
        {"name": "Verbotene Stadt", "desc": "Kurzbeschreibung"},
        {"name": "Große Mauer", "desc": "Mutianyu-Sektion"}
      ],
      "must_try_food": [
        {"name": "Peking-Ente", "desc": "Knusprige Haut mit Pfannkuchen"}
      ],
      "tips": "Praktische Tipps für die Stadt...",
      "practical_info": "Transport, Sprache, etc.",
      "local_customs": "Lokale Bräuche und Kultur...",
      "best_time_to_visit": "Frühling und Herbst ideal..."
    }
  ],
  "packlist": [
    "Reisepass + Kopien",
    "Visum",
    "Adapter Typ A/C/I",
    "..."
  ]
}
```

**Wichtige Regeln für das JSON:**
- Jeder POI mit `lat`/`lon` erscheint auf der Tageskarte.
- `image_keyword` wird für die Bildersuche genutzt (Wikimedia Commons + Brave Fallback).
- `type` kann sein: `transport`, `sight`, `food`, `hotel`, `activity`.
- `hero_keyword` sollte ein sehr bekannter Begriff sein, damit ein schönes Deckblatt-Bild gefunden wird.
- `destinations` liefert ausführliche Stadt-Guides mit Highlights, Food-Tipps, Bräuchen und praktischen Infos.

### 4. Karten generieren

```bash
cd /workspace/skills/travelplan
python3 scripts/generate_maps.py /pfad/zu/plan.json /pfad/zu/output/maps
```

Dies erzeugt:
- `overview_map.png` (alle Städte mit Route)
- `day_01_map.png`, `day_02_map.png`, ... (nummerierte POIs pro Tag)

und schreibt die Pfade in `plan_with_maps.json`.

### 5. Bilder laden

```bash
cd /workspace/skills/travelplan
python3 scripts/fetch_images.py /pfad/zu/plan_with_maps.json /pfad/zu/output/images
```

Dies lädt pro Stadt und POI passende Bilder herunter (Wikimedia Commons bevorzugt, Brave Search als Fallback) und speichert das Ergebnis als `plan_with_images.json`.

### 6. Bilder komprimieren (optional, für kleinere PDF)

```bash
cd /workspace/skills/travelplan
python3 scripts/compress_images.py /pfad/zu/output/images
```

Skaliert Bilder auf max 900–1200px und komprimiert als JPEG (Qualität 80–85%).

### 7. PDF generieren

```bash
cd /workspace/skills/travelplan
python3 scripts/generate_pdf.py /pfad/zu/plan_with_images.json /pfad/zu/output/Reiseplan.pdf
```

WeasyPrint rendert das HTML-Template mit dem Magazine-Layout. Es entsteht eine druckfertige A4-PDF mit:
- Vollflächigem Deckblatt
- Übersichtskarte & Reiseübersicht
- Pro Tag: Header, Tageskarte, Timeline mit POIs, Bildern & Tipps
- Allgemeine Infos, Packliste, Budget-Tabelle

### 8. PDF an User senden
Nutze `send_telegram_file`, um die fertige PDF zu übermitteln.

---

## Dateistruktur

```
travelplan/
├── SKILL.md                  # Diese Datei
├── requirements.txt
├── scripts/
│   ├── generate_maps.py      # OSM-Karten mit nummerierten Markern
│   ├── fetch_images.py       # Wikimedia Commons + Brave Images
│   ├── compress_images.py    # Bilder für PDF komprimieren
│   └── generate_pdf.py       # WeasyPrint HTML → PDF
└── assets/
    ├── template.html         # Jinja2-Template für die PDF
    └── style.css             # Magazine-Layout CSS
```

---

## Tipps für die Recherche (pi)

- Recherchiere **immer aktuelle Öffnungszeiten** und **Eintrittspreise** – veraltete Infos sind ärgerlich vor Ort.
- Prüfe **Wetter** für jeden Tag (wetter-forecast Skill) und erwähne es im Plan.
- Berücksichtige **geografische Nähe** bei der Tagesplanung: POIs, die nah beieinander liegen, gehören an einen Tag.
- Füge pro Tag einen **Restaurant-Tipp** zur Mittagszeit hinzu – am besten in der Nähe des nächsten POIs.
- Gib bei Transport zwischen Städten immer **Dauer, Kosten und Buchungs-App/Website** an.
- Wenn möglich, füge einen **Plan B bei schlechtem Wetter** ein (Museum, Markthalle, etc.).
- Nutze für `image_keyword` englische Begriffe – die Bildersuche funktioniert damit besser.

---

## Beispiel-Aufruf (komplett)

```bash
cd /workspace/skills/travelplan
mkdir -p /workspace/travelplans/china/output

# Pi erstellt /workspace/travelplans/china/plan.json

python3 scripts/generate_maps.py \
  /workspace/travelplans/china/plan.json \
  /workspace/travelplans/china/output/maps

python3 scripts/fetch_images.py \
  /workspace/travelplans/china/output/plan_with_maps.json \
  /workspace/travelplans/china/output/images

python3 scripts/compress_images.py \
  /workspace/travelplans/china/output/images

python3 scripts/generate_pdf.py \
  /workspace/travelplans/china/output/plan_with_images.json \
  /workspace/travelplans/china/output/Reiseplan_China.pdf
```
