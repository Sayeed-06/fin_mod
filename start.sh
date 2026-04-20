#!/bin/bash
# Minimal quick-start - just run the app

python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt
streamlit run app.py --client.toolbarMode=minimal
