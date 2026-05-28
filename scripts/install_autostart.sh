#!/bin/bash

# Writer Studio Web Server Auto-Start Installer
# This script installs a launchd service to auto-start the web server on login

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
PLIST_NAME="com.writerstudio.webserver.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_DEST="$LAUNCH_AGENTS_DIR/$PLIST_NAME"
PYTHON_PATH="$PROJECT_DIR/venv/bin/python3"
WEB_PY_PATH="$PROJECT_DIR/web.py"
LOG_DIR="$HOME/Library/Logs/WriterStudio"

echo "🚀 Writer Studio Web Server Auto-Start Installer"
echo "=================================================="
echo ""

# Check if Python exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Error: Python not found at $PYTHON_PATH"
    echo "Please ensure the virtual environment is set up."
    exit 1
fi

# Check if web.py exists
if [ ! -f "$WEB_PY_PATH" ]; then
    echo "❌ Error: web.py not found at $WEB_PY_PATH"
    exit 1
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"
mkdir -p "$LOG_DIR"

# Create plist file directly (no template needed)
echo "📝 Creating launchd configuration..."
cat > "$PLIST_DEST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.writerstudio.webserver</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-lc</string>
        <string>cd "$PROJECT_DIR" &amp;&amp; exec "$PYTHON_PATH" -u "$WEB_PY_PATH"</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$LOG_DIR/web_server_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/web_server_stderr.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

chmod 644 "$PLIST_DEST"

echo "🔄 Stopping existing service if present..."
launchctl bootout "gui/$(id -u)" "$PLIST_DEST" 2>/dev/null || true
launchctl remove "com.writerstudio.webserver" 2>/dev/null || true

# Load the service
echo "✅ Installing service..."
launchctl bootstrap "gui/$(id -u)" "$PLIST_DEST"
launchctl kickstart -k "gui/$(id -u)/com.writerstudio.webserver"

echo ""
echo "✨ Installation complete!"
echo ""
echo "The web server will now start automatically when you log in."
echo "You can access it at: http://localhost:5001"
echo ""
echo "To check if it's running:"
echo "  launchctl list | grep writerstudio"
echo ""
echo "To view logs:"
echo "  tail -f $PROJECT_DIR/web_server.log"
echo ""
echo "To uninstall, run:"
echo "  ./uninstall_autostart.sh"
echo ""
