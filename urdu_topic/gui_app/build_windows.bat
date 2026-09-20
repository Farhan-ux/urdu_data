@echo off
REM ============================================================
REM Build UrduScraper.exe for Windows
REM ============================================================
REM
REM Usage: Just double-click this file on Windows.
REM
REM Prerequisites:
REM   - Python 3.10+ from https://www.python.org/downloads/
REM   - During install, tick "Add Python to PATH"
REM
REM Output:
REM   dist\UrduScraper.exe  (single-file Windows executable)

echo ============================================
echo   Urdu Scraper - Windows Build Script
echo ============================================
echo.

REM Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install from https://www.python.org/downloads/
    echo During install, tick "Add Python to PATH"
    pause
    exit /b 1
)

REM Install dependencies
echo [1/3] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install requests beautifulsoup4 lxml pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo     done.
echo.

REM Build the executable
echo [2/3] Building UrduScraper.exe...
pyinstaller --clean --noconsole --onefile ^
    --name UrduScraper ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.filedialog ^
    --hidden-import tkinter.messagebox ^
    --hidden-import tkinter.scrolledtext ^
    --hidden-import requests ^
    --hidden-import bs4 ^
    --hidden-import lxml ^
    --hidden-import xml.etree.ElementTree ^
    urdu_scraper_gui.py
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)
echo     done.
echo.

REM Show output
echo [3/3] Build complete!
echo.
echo Output: dist\UrduScraper.exe
echo.
dir dist\UrduScraper.exe
echo.
echo You can now:
echo   1. Copy dist\UrduScraper.exe to any Windows machine
echo   2. Double-click to run
echo   3. No Python installation needed on target machine
echo.
pause
