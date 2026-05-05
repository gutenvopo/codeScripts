#!/usr/bin/env pwsh
Param()
$ErrorActionPreference = 'Stop'

# Determine project root
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
# Prefer venv python if present
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = 'python'
}

Write-Host "Using Python: $python"

# Upgrade pip and install build deps
& $python -m pip install --upgrade pip
& $python -m pip install pyinstaller pillow

# Paths
$csvPath = Join-Path $projectRoot 'codeScripts\internet_speed_log.csv'
$iconPath = Join-Path $projectRoot 'codeScripts\generated_icon.ico'
$scriptPath = Join-Path $projectRoot 'codeScripts\speedtest_gui_v1.02.py'
$distPath = [Environment]::GetFolderPath('MyDocuments')

Write-Host "Generating icon from CSV: $csvPath"
& $python (Join-Path $projectRoot 'codeScripts\make_icon_from_csv.py') --csv $csvPath --out $iconPath

Write-Host "Building single-file executable and placing in: $distPath"
& $python -m PyInstaller --noconfirm --onefile --windowed --icon $iconPath --distpath $distPath $scriptPath

Write-Host "Build finished. Check your Documents folder for the EXE."