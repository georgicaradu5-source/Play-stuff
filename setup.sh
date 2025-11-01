#!/bin/bash
# X Agent Unified - Unix/Linux/Mac Setup Script

set -e

echo "========================================"
echo "X Agent Unified - Setup"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.9+"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
python3 -m venv .venv

echo "[2/5] Activating virtual environment..."
source .venv/bin/activate

echo "[3/5] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/5] Creating configuration files..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env - PLEASE EDIT WITH YOUR CREDENTIALS"
else
    echo ".env already exists, skipping"
fi

if [ ! -f config.yaml ]; then
    cp config.example.yaml config.yaml
    echo "Created config.yaml"
else
    echo "config.yaml already exists, skipping"
fi

mkdir -p data

echo "[5/5] Setup complete!"
echo ""
echo "========================================"
echo "NEXT STEPS:"
echo "========================================"
echo "1. Edit .env with your X API credentials"
echo "2. Edit config.yaml to customize behavior"
echo "3. Run dry-run test:"
echo "   python src/main.py --mode both --dry-run true"
echo ""
echo "TWEEPY MODE (OAuth 1.0a):"
echo "  - Set X_AUTH_MODE=tweepy in .env"
echo "  - Add API keys/tokens to .env"
echo ""
echo "OAUTH2 MODE (OAuth 2.0 PKCE):"
echo "  - Set X_AUTH_MODE=oauth2 in .env"
echo "  - Run: python src/main.py --authorize"
echo "========================================"
echo ""
