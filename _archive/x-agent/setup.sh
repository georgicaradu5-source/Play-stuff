#!/bin/bash
# X Agent Setup Script for Linux/macOS

set -e

echo "================================================"
echo "X Agent - Setup Script"
echo "================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9+ from your package manager"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
python3 -m venv .venv

echo "[2/5] Activating virtual environment..."
source .venv/bin/activate

echo "[3/5] Installing dependencies..."
pip install -r requirements.txt

echo "[4/5] Creating configuration files..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from template"
else
    echo ".env already exists, skipping"
fi

if [ ! -f config.yaml ]; then
    cp config.example.yaml config.yaml
    echo "Created config.yaml from template"
else
    echo "config.yaml already exists, skipping"
fi

echo "[5/5] Creating data directory..."
mkdir -p data

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env with your X API credentials"
echo "2. Customize config.yaml with your topics and queries"
echo "3. Run: python src/main.py --authorize"
echo "4. Test: python src/main.py --dry-run --mode both"
echo ""
echo "See QUICKSTART.md for detailed instructions"
echo ""
