#!/usr/bin/env python3
"""
MiniMax Coding-Plan Quota -> ASCII-Ladebalken
Liest Key aus env MINIMAX_API_KEY.
Telegram-tauglich: kurze Zeilen, keine Sonderzeichen ausser Balken.
"""

import os
import sys
import json
import urllib.request
from datetime import datetime, timezone

ENDPOINT  = "https://api.MiniMax.io/v1/api/openplatform/coding_plan/remains"
BAR_WIDTH = 20  # Laenge des Ladebalkens in Zeichen
FULL, EMPTY = "#", "-"


def bar(pct: int) -> str:
    """ASCII-Ladebalken, 20 Zeichen breit."""
    pct = max(0, min(100, pct))
    f = round(pct / 100 * BAR_WIDTH)
    return "[" + FULL * f + EMPTY * (BAR_WIDTH - f) + "]"


def reset_str(end_ms: int, now: datetime) -> str:
    """Reset-Zeitpunkt kompakt: in XhYm / XdYh."""
    end_dt = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc)
    delta  = end_dt - now
    s = int(delta.total_seconds())
    if s <= 0:
        return "reset now"
    if s < 3600:
        return f"reset in {s // 60}m"
    if s < 86400:
        return f"reset in {s // 3600}h{(s % 3600) // 60:02d}m"
    return f"reset in {s // 86400}d{(s % 86400) // 3600:02d}h"


def status_icon(status: int, pct: int) -> str:
    """Mini-Icon je nach freiem Anteil.

    pct ist hier der VERBLEIBENDE (freie) Anteil in Prozent.
    99% frei = frisch, 0% frei = voll.
    """
    if status == 3:
        return "n/a"
    if pct <= 0:
        return "X voll"
    if pct < 25:
        return "! knapp"
    if pct >= 75:
        return "frisch"
    return "ok"


def main() -> int:
    key = os.environ.get("MINIMAX_API_KEY")
    if not key:
        print("ERR: env MINIMAX_API_KEY fehlt", file=sys.stderr)
        return 1

    req = urllib.request.Request(
        ENDPOINT, headers={"Authorization": f"Bearer {key}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.load(resp)
    except Exception as e:
        print(f"ERR: API call failed: {e}", file=sys.stderr)
        return 2

    items  = data.get("model_remains", []) or []
    general = next((m for m in items if m.get("model_name") == "general"), None)
    if not general:
        print("ERR: kein 'general'-Eintrag", file=sys.stderr)
        return 3

    now = datetime.now(timezone.utc)

    p5   = int(general["current_interval_remaining_percent"])
    end5 = int(general["end_time"])
    s5   = int(general["current_interval_status"])

    pw   = int(general["current_weekly_remaining_percent"])
    endw = int(general["weekly_end_time"])
    sw   = int(general["current_weekly_status"])

    print("MiniMax Coding-Plan (Werte = freier Anteil)")
    print()
    print(f"5h {bar(p5)} {p5:>3d}% frei  {status_icon(s5, p5)}")
    print(f"   {reset_str(end5, now)}")
    print()
    print(f"Wk {bar(pw)} {pw:>3d}% frei  {status_icon(sw, pw)}")
    print(f"   {reset_str(endw, now)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
