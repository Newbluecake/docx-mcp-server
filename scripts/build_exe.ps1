# Build script for Windows (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "🚀 Building Docx Server Launcher..." -ForegroundColor Cyan

# 1. Check Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Python is not installed or not in PATH."
    exit 1
}

# 2. Setup Virtual Environment
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv
Write-Host "🔌 Activating virtual environment..."
$venvScript = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvScript) {
    . $venvScript
} else {
    Write-Error "❌ Virtual environment script not found at $venvScript"
    exit 1
}

# 3. Install Dependencies
Write-Host "⬇️ Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install ".[gui]"
pip install pyinstaller

# 4. Build EXE
Write-Host "🔨 Running PyInstaller..." -ForegroundColor Yellow
pyinstaller --clean --noconfirm docx-server-launcher.spec

if (Test-Path "dist\DocxServerLauncher.exe") {
    Write-Host "✅ Build complete!" -ForegroundColor Green
    Write-Host "📁 Artifact: dist\DocxServerLauncher.exe" -ForegroundColor Cyan
} else {
    Write-Error "❌ Build failed. Artifact not found."
    exit 1
}
