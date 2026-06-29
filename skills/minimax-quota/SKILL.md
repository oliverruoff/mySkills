---
name: minimax-quota
description: Lädt die aktuellen Quotas (5h-Fenster + Wochenfenster) eines MiniMax Coding-Plan API-Keys und gibt sie als kompakten ASCII-Ladebalken aus, telegram-tauglich (kurze Zeilen, kein fancy formatting).
compatibility: Benötigt Python 3 und Internet-Zugang.
metadata:
  version: "1.0"
---

# MiniMax Coding-Plan Quota

Zeigt die Quotas (5h-Fenster + Wochenfenster) des MiniMax Coding-Plan
über die offizielle API als ASCII-Ladebalken an.

## Voraussetzung

Der API-Key muss als Umgebungsvariable gesetzt sein:

```bash
export MINIMAX_API_KEY="sk-cp-..."
```

## Parameter

- keine – das Skript nutzt immer die Env-Variable.

## Ausführung

```bash
./scripts/quota.py
```

## Ausgabe (Beispiel)

```
MiniMax Coding-Plan (Werte = freier Anteil)

5h    [████████████████████] 99% frei  frisch
      reset in 50m

Wk    [████████████████████] 99% frei  frisch
      reset in 6d04h
```

Kurze Zeilen, ASCII-Art, telegram-tauglich.

## Interpretation

Die Prozentzahlen sind der **noch freie** Anteil, nicht der verbrauchte:

- `99% frei` = quasi ungenutzt, gerade frisch resettet
- `50-75%` = normaler Betrieb
- `<25%` = knapp, bald Reset abwarten
- `0%` = Fenster voll, kein Traffic mehr möglich

Status-Icon rechts:
- `frisch` = ≥75% frei
- `ok`     = 25-74% frei
- `! knapp` = <25% frei
- `X voll` = 0% frei
- `n/a`    = Status 3 (Fenster inaktiv)

## Endpoint

- `GET https://api.MiniMax.io/v1/api/openplatform/coding_plan/remains`
- Header: `Authorization: Bearer $MINIMAX_API_KEY`

Felder im Response (für "general"-Modell):

- `current_interval_remaining_percent` – freier Anteil im 5h-Fenster (0-100)
- `current_weekly_remaining_percent` – freier Anteil im Wochenfenster (0-100)
- `current_interval_status` / `current_weekly_status` – Status (3 = inaktiv)
- `end_time` / `weekly_end_time` – Reset-Zeitpunkt (ms seit Epoch, UTC)
