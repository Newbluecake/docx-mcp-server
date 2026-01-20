#!/bin/bash
set -e

# Detect OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    IS_WINDOWS=true
else
    IS_WINDOWS=false
fi

echo "🚀 Building Docx Server Launcher using uv..."

# 1. Check uv
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install it: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 2. Setup Virtual Environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
fi

# 3. Install Dependencies
echo "⬇️ Installing dependencies..."
# uv automatically respects pyproject.toml
uv pip install ".[gui]" pyinstaller

# 4. Build EXE
echo "🔨 Running PyInstaller..."
# Use uv run to execute pyinstaller within the environment
uv run pyinstaller --clean --noconfirm docx-server-launcher.spec

echo "✅ Build complete!"
if [ "$IS_WINDOWS" = true ]; then
    echo "📁 Artifact: dist\\DocxServerLauncher.exe"
else
    echo "📁 Artifact: dist/DocxServerLauncher"
fi
