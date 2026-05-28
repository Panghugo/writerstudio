#!/bin/bash
cd "$(dirname "$0")"

if [ -f "venv/bin/python3" ]; then
    ./venv/bin/python3 app.py
else
    python3 app.py
fi

read -p "Press Enter to close..."
