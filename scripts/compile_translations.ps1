# PowerShell script to compile Qt translation files
$ErrorActionPreference = "Stop"

# Ensure UTF-8 encoding
chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 Compiling translation files..." -ForegroundColor Cyan

# Output directory
$TRANS_DIR = "src\docx_server_launcher\resources\translations"

# Try to find lrelease (could be lrelease, lrelease6, or pyside6-lrelease)
$lrelease = $null
foreach ($cmd in @("pyside6-lrelease", "lrelease6", "lrelease")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $lrelease = $cmd
        Write-Host "✓ Found: $cmd" -ForegroundColor Green
        break
    }
}

if (-not $lrelease) {
    Write-Host "❌ Error: lrelease not found." -ForegroundColor Red
    Write-Host "Please install Qt tools:" -ForegroundColor Yellow
    Write-Host "  uv pip install pyqt6-tools" -ForegroundColor Yellow
    Write-Host "  or" -ForegroundColor Yellow
    Write-Host "  uv pip install pyside6" -ForegroundColor Yellow
    exit 1
}

# Compile zh_CN
$tsFile = "$TRANS_DIR\zh_CN.ts"
$qmFile = "$TRANS_DIR\zh_CN.qm"

Write-Host "Compiling $tsFile..." -ForegroundColor Yellow
& $lrelease $tsFile -qm $qmFile

if (Test-Path $qmFile) {
    Write-Host "✅ Compiled $qmFile" -ForegroundColor Green
} else {
    Write-Error "❌ Failed to compile translation file"
    exit 1
}
