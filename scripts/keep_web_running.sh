#!/bin/bash

# Keep Web Server Running Script
# This script starts the web server and keeps it running in the background

cd "$(dirname "$0")/.."

# Check if already running
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Web server is already running on port 5001"
    echo "You can access it at: http://localhost:5001"
    exit 0
fi

# Start the server in background
echo "🚀 Starting web server..."
nohup ./venv/bin/python3 -u web.py >> web_server.log 2>> web_server_error.log &

# Wait a moment for it to start
sleep 2

# Check if it started successfully
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Web server started successfully!"
    echo "📍 Access at: http://localhost:5001"
    echo "📋 Logs: tail -f web_server.log"
else
    echo "❌ Failed to start web server"
    echo "Check web_server.log for errors"
    exit 1
fi
