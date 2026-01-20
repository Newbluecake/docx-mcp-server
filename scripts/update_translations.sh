#!/bin/bash
set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Output directory
TRANS_DIR="src/docx_server_launcher/resources/translations"
mkdir -p "$TRANS_DIR"

echo "🚀 Updating translation files..."

# Check for pylupdate6
if ! command -v pylupdate6 &> /dev/null; then
    echo "❌ Error: pylupdate6 is not installed. Please install PyQt6 tools."
    exit 1
fi

# List of source files to scan
# We scan the gui directory and language manager
SOURCES="src/docx_server_launcher/gui/main_window.py src/docx_server_launcher/core/language_manager.py"

# Update/Create the .ts file for Simplified Chinese
pylupdate6 $SOURCES -ts "$TRANS_DIR/zh_CN.ts"

echo "✅ Updated $TRANS_DIR/zh_CN.ts"
echo "👉 Now open this file with Qt Linguist or a text editor to add translations."
