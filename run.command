#!/bin/bash
cd "$(dirname "$0")"

echo "Writer Studio legacy generator CLI."
echo "For the current web app, use ./Start_Web.command and open http://localhost:5001."
echo ""

if [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="./venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

"$PYTHON_CMD" app.py

read -r -p "Press Enter to close..."
