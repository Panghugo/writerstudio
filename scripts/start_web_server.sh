#!/bin/bash

# Writer Studio Web Server Auto-Start Script
# This script is designed to be run by launchd or manually

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_DIR"

# Log file for debugging
LOG_FILE="$PROJECT_DIR/web_server.log"

echo "=== Writer Studio Web Server Starting at $(date) ===" >> "$LOG_FILE"
echo "Working directory: $PROJECT_DIR" >> "$LOG_FILE"

if /usr/sbin/lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo "Port 5001 is already listening; leaving existing server in place." >> "$LOG_FILE"
    exit 0
fi

# Use virtual environment python if available
if [ -f "$PROJECT_DIR/venv/bin/python3" ]; then
    echo "Using virtual environment python..." >> "$LOG_FILE"
    PYTHON_CMD="$PROJECT_DIR/venv/bin/python3"
else
    echo "Using system python3..." >> "$LOG_FILE"
    PYTHON_CMD="python3"
fi

# Start the web server
echo "Starting Flask server on port 5001..." >> "$LOG_FILE"
exec "$PYTHON_CMD" -u "$PROJECT_DIR/web.py" >> "$LOG_FILE" 2>&1
