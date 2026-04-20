#!/bin/bash

# Quick Start Guide for Options Pricing Dashboard

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Options Pricing Dashboard${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is required. Please install it first."
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found"

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo -e "${GREEN}✓${NC} Virtual environment ready"

# Activate venv
source venv/bin/activate

# Install deps
echo "Installing dependencies..."
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt

echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Starting Dashboard...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Open your browser to: ${GREEN}http://localhost:8501${NC}"
echo "Press Ctrl+C to stop the server"
echo ""

# Run Streamlit
streamlit run app.py \
    --client.showErrorDetails=false \
    --client.toolbarMode=minimal \
    --logger.level=error
