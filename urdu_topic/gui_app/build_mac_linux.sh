#!/usr/bin/env bash
# ============================================================
# Build UrduScraper for macOS / Linux
# ============================================================
#
# Usage: Open Terminal, then:
#   chmod +x build_mac_linux.sh
#   ./build_mac_linux.sh
#
# Prerequisites:
#   - Python 3.10+ from https://www.python.org/downloads/
#   - On Linux (Debian/Ubuntu): sudo apt install python3-tk
#   - On Mac: brew install python-tk
#
# Output:
#   dist/UrduScraper  (single-file executable)

set -e

echo "============================================"
echo "  Urdu Scraper - macOS/Linux Build Script"
echo "============================================"
echo

# Check Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install from https://www.python.org/downloads/"
    exit 1
fi

# Check tkinter
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "ERROR: tkinter not found."
    echo "On Ubuntu/Debian: sudo apt install python3-tk"
    echo "On macOS: brew install python-tk"
    exit 1
fi

# Install dependencies
echo "[1/3] Installing dependencies..."
python3 -m pip install --upgrade pip --user
python3 -m pip install requests beautifulsoup4 lxml pyinstaller --user
echo "    done."
echo

# Build the executable
echo "[2/3] Building UrduScraper..."
python3 -m PyInstaller --clean --noconsole --onefile \
    --name UrduScraper \
    --hidden-import tkinter \
    --hidden-import tkinter.ttk \
    --hidden-import tkinter.filedialog \
    --hidden-import tkinter.messagebox \
    --hidden-import tkinter.scrolledtext \
    --hidden-import requests \
    --hidden-import bs4 \
    --hidden-import lxml \
    --hidden-import xml.etree.ElementTree \
    urdu_scraper_gui.py
echo "    done."
echo

# Show output
echo "[3/3] Build complete!"
echo
echo "Output: dist/UrduScraper"
ls -lh dist/UrduScraper
echo
echo "You can now:"
echo "  1. Move dist/UrduScraper to any macOS/Linux machine"
echo "  2. Run: ./UrduScraper"
echo "  3. No Python installation needed on target machine"
echo
