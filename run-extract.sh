#!/bin/bash
# Run the Zotero annotation extraction script
#
# Prerequisites:
# 1. Zotero must be running
# 2. Enable: Settings → Advanced → "Allow other applications to communicate with Zotero"
# 3. Select an item in Zotero before running this script

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_FILE="$SCRIPT_DIR/extract-annotations-cli.js"

if [ ! -f "$SCRIPT_FILE" ]; then
    echo "Error: Script not found at $SCRIPT_FILE"
    exit 1
fi

# Send to Zotero's debug endpoint
RESPONSE=$(curl -s -X POST "http://127.0.0.1:23119/debug" \
    -H "Content-Type: application/javascript" \
    --data-binary "@$SCRIPT_FILE" 2>&1)

if [ $? -ne 0 ]; then
    echo "Error: Could not connect to Zotero."
    echo "Make sure Zotero is running and remote debugging is enabled."
    echo "Settings → Advanced → Allow other applications to communicate with Zotero"
    exit 1
fi

echo "$RESPONSE"
