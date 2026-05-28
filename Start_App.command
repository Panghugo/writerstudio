#!/bin/bash
cd "$(dirname "$0")"
echo "Writer Studio desktop GUI has been replaced by the web app."
echo "Starting Writer Studio Web at http://localhost:5001 ..."
exec ./Start_Web.command
