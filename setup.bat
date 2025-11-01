@echo off
REM X Agent Unified - Windows Setup Script

echo ========================================
echo X Agent Unified - Setup
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.9+
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    exit /b 1
)

echo [2/5] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

echo [4/5] Creating configuration files...
if not exist .env (
    copy .env.example .env
    echo Created .env - PLEASE EDIT WITH YOUR CREDENTIALS
) else (
    echo .env already exists, skipping
)

if not exist config.yaml (
    copy config.example.yaml config.yaml
    echo Created config.yaml
) else (
    echo config.yaml already exists, skipping
)

if not exist data mkdir data

echo [5/5] Setup complete!
echo.
echo ========================================
echo NEXT STEPS:
echo ========================================
echo 1. Edit .env with your X API credentials
echo 2. Edit config.yaml to customize behavior
echo 3. Run dry-run test:
echo    python src/main.py --mode both --dry-run true
echo.
echo TWEEPY MODE (OAuth 1.0a):
echo   - Set X_AUTH_MODE=tweepy in .env
echo   - Add API keys/tokens to .env
echo.
echo OAUTH2 MODE (OAuth 2.0 PKCE):
echo   - Set X_AUTH_MODE=oauth2 in .env
echo   - Run: python src/main.py --authorize
echo ========================================
echo.

pause
