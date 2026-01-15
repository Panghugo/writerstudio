#!/bin/bash
# 1. Enter directory
cd "$(dirname "$0")"

# 2. Check if Flask is installed, if not, install it
if ! ./venv/bin/pip freeze | grep Flask > /dev/null; then
    echo "Installing Flask..."
    ./venv/bin/pip install flask
fi

# 3. Open Browser (wait a bit for server to start)
(sleep 2 && open "http://localhost:5001") &

# 4. Run Flask Server
echo "Starting Web Server..."
./venv/bin/python3 web.py
