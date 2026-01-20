#!/bin/bash
set -e

# Detect OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    IS_WINDOWS=true
else
    IS_WINDOWS=false
fi

echo "🚀 Building Docx Server Launcher..."

# 1. Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed."
    exit 1
fi

# 2. Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate venv
if [ "$IS_WINDOWS" = true ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# 3. Install Dependencies
echo "⬇️ Installing dependencies..."
pip install --upgrade pip
pip install ".[gui]"
pip install pyinstaller

# 4. Build EXE
echo "🔨 Running PyInstaller..."
pyinstaller --clean --noconfirm docx-server-launcher.spec

echo "✅ Build complete!"
if [ "$IS_WINDOWS" = true ]; then
    echo "📁 Artifact: dist\\DocxServerLauncher.exe"
else
    echo "📁 Artifact: dist/DocxServerLauncher"
fi
