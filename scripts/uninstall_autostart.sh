#!/bin/bash

# Writer Studio Web Server Auto-Start Uninstaller
# This script removes the launchd service

set -e

PLIST_NAME="com.writerstudio.webserver.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_DEST="$LAUNCH_AGENTS_DIR/$PLIST_NAME"

echo "🗑️  Writer Studio Web Server Auto-Start Uninstaller"
echo "===================================================="
echo ""

# Check if service is installed
if [ ! -f "$PLIST_DEST" ]; then
    echo "ℹ️  Service is not installed."
    exit 0
fi

# Unload the service
echo "🔄 Stopping service..."
launchctl bootout "gui/$(id -u)" "$PLIST_DEST" 2>/dev/null || true
launchctl remove "com.writerstudio.webserver" 2>/dev/null || true

# Remove the plist file
echo "🗑️  Removing configuration..."
rm -f "$PLIST_DEST"

echo ""
echo "✅ Uninstallation complete!"
echo ""
echo "The web server will no longer start automatically."
echo "You can still start it manually using Start_Web.command"
echo ""
