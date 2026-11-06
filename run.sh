#!/usr/bin/env bash
set -e
pip install -r requirements.txt --break-system-packages 2>/dev/null || pip install -r requirements.txt
python3 src/generate_data.py
python3 src/pipeline.py
python3 src/build_html.py
pytest tests/ -v
echo ""
echo "Done. Open public/index.html in a browser."
