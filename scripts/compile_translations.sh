#!/bin/bash
set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Output directory
TRANS_DIR="src/docx_server_launcher/resources/translations"

echo "🚀 Compiling translation files..."

# Check for lrelease6
if ! command -v lrelease6 &> /dev/null; then
    echo "❌ Error: lrelease6 is not installed. Please install PyQt6 tools."
    exit 1
fi

# Compile zh_CN
lrelease6 "$TRANS_DIR/zh_CN.ts" -qm "$TRANS_DIR/zh_CN.qm"

echo "✅ Compiled $TRANS_DIR/zh_CN.qm"
