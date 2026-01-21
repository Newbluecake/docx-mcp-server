# Build script for Windows (PowerShell) using uv
$ErrorActionPreference = "Stop"

# Ensure UTF-8 encoding for emojis and special characters
chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 Building Docx Server Launcher using uv..." -ForegroundColor Cyan

# 1. Check uv
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Error "❌ uv is not installed. Please install it: powershell -c ""irm https://astral.sh/uv/install.ps1 | iex"""
    exit 1
}

# 2. Setup Virtual Environment
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    uv venv
}

# 3. Install Dependencies
Write-Host "⬇️ Installing dependencies..." -ForegroundColor Yellow
uv pip install ".[gui]" pyinstaller

# 4. Compile Translations (if needed)
$qmFile = "src\docx_server_launcher\resources\translations\zh_CN.qm"
if (-not (Test-Path $qmFile)) {
    Write-Host "🌐 Compiling translations..." -ForegroundColor Yellow
    try {
        & "$PSScriptRoot\compile_translations.ps1"
    } catch {
        Write-Host "⚠️  Warning: Translation compilation failed. Using pre-compiled files." -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ Translation files already compiled" -ForegroundColor Green
}

# 5. Build EXE
Write-Host "🔨 Running PyInstaller..." -ForegroundColor Yellow
uv run pyinstaller --clean --noconfirm docx-server-launcher.spec

if (Test-Path "dist\DocxServerLauncher.exe") {
    Write-Host "✅ Build complete!" -ForegroundColor Green
    Write-Host "📁 Artifact: dist\DocxServerLauncher.exe" -ForegroundColor Cyan
} else {
    Write-Error "❌ Build failed. Artifact not found."
    exit 1
}
