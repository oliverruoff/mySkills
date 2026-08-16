#!/usr/bin/env bash
# Setup helper for kleinanzeigen-search skill.
# Installs Python deps and downloads the Chromium browser for Playwright.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "▶ Installing Python dependencies from requirements.txt..."
pip install -r "$SKILL_DIR/requirements.txt"

echo "▶ Installing Playwright Chromium browser..."
playwright install chromium

# Optional: install system dependencies (needed in minimal containers)
if command -v playwright >/dev/null 2>&1; then
    echo "▶ Trying to install system dependencies for Chromium (may require sudo)..."
    if playwright install-deps chromium 2>/dev/null; then
        echo "✓ System dependencies installed."
    else
        echo "⚠ Could not install system dependencies automatically (needs sudo?)."
        echo "  Run manually if Chromium fails to launch: sudo playwright install-deps chromium"
    fi
fi

echo "✓ Setup complete. Try:"
echo "    python $SCRIPT_DIR/search.py --query \"apple macbook\" --plz \"80331 München\""
