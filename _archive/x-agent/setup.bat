@echo off
REM X Agent Setup Script for Windows

echo ================================================
echo X Agent - Setup Script
echo ================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/5] Creating configuration files...
if not exist .env (
    copy .env.example .env
    echo Created .env from template
) else (
    echo .env already exists, skipping
)

if not exist config.yaml (
    copy config.example.yaml config.yaml
    echo Created config.yaml from template
) else (
    echo config.yaml already exists, skipping
)

echo [5/5] Creating data directory...
if not exist data mkdir data

echo.
echo ================================================
echo Setup Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Edit .env with your X API credentials
echo 2. Customize config.yaml with your topics and queries
echo 3. Run: python src\main.py --authorize
echo 4. Test: python src\main.py --dry-run --mode both
echo.
echo See QUICKSTART.md for detailed instructions
echo.
pause
