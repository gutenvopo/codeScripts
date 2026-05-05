#!/usr/bin/env pwsh
Param()
$ErrorActionPreference = 'Stop'

# Paths
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonVenv = Join-Path $projectRoot '..\.venv\Scripts\python.exe'
if (Test-Path $pythonVenv) { $python = $pythonVenv } else { $python = 'python' }

Write-Host "Using Python: $python"

Write-Host "Installing build dependencies..."
& $python -m pip install --upgrade pip -q
& $python -m pip install pyinstaller pillow -q

# Icon and script paths
$pngPath = Join-Path $projectRoot 'internet_test_icon_v2.png'
$icoPath = Join-Path $projectRoot 'internet_test_icon_v2.ico'
$scriptPath = Join-Path $projectRoot 'speedtest_gui_v1.03.py'
$convertScript = Join-Path $projectRoot 'convert_png_to_ico.py'
$distPath = [Environment]::GetFolderPath('MyDocuments')

if (-Not (Test-Path $pngPath)) {
    Write-Error "Icon PNG not found: $pngPath"
    exit 1
}

Write-Host "Converting PNG to ICO..."
& $python $convertScript --in $pngPath --out $icoPath

Write-Host "Building single-file executable into: $distPath"
& $python -m PyInstaller --noconfirm --onefile --windowed --icon $icoPath --hidden-import=speedtest --distpath $distPath $scriptPath

# Determine exe path
$exeName = [IO.Path]::GetFileNameWithoutExtension($scriptPath) + '.exe'
$exePath = Join-Path $distPath $exeName

if (-Not (Test-Path $exePath)) {
    Write-Error "Expected EXE not found: $exePath"
    exit 1
}

Write-Host "Build complete: $exePath"

Write-Host "Attempting digital signature..."
$signtoolPath = 'C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe'
if (-Not (Test-Path $signtoolPath)) {
    Write-Host "signtool.exe not found at expected location. Checking alternative paths..."
    $signtoolPath = (Get-Command signtool -ErrorAction SilentlyContinue).Source
    if (-Not $signtoolPath) {
        Write-Host "WARNING: signtool.exe not found. Windows SDK may not be installed."
        Write-Host "For code signing, install Windows SDK or use a code signing certificate."
    }
}

if ($signtoolPath -and (Test-Path $signtoolPath)) {
    Write-Host "Found signtool at: $signtoolPath"
    Write-Host "NOTE: Without a code signing certificate, the application cannot be digitally signed."
    Write-Host "To sign, you need a certificate from a Certificate Authority (CA) or a self-signed cert."
} else {
    Write-Host "signtool.exe not found. Skipping digital signature."
}

Write-Host "Creating Desktop shortcut..."
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$linkPath = Join-Path $desktop 'Speed Test v1.03.lnk'
$shortcut = $shell.CreateShortcut($linkPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $distPath
$shortcut.IconLocation = $icoPath
$shortcut.Save()
Write-Host "Desktop shortcut created: $linkPath"

Write-Host ""
Write-Host "=========================================="
Write-Host "Release build complete!"
Write-Host "=========================================="
Write-Host "Executable: $exePath"
Write-Host "Desktop Shortcut: $linkPath"
Write-Host ""
Write-Host "NOTE: Digital Signature"
Write-Host "The application is not yet signed because:"
Write-Host "1. A valid code signing certificate is required"
Write-Host "2. Certificates are issued by Certificate Authorities (e.g., DigiCert, Sectigo)"
Write-Host "3. To obtain: Go to a CA's website and purchase a Code Signing certificate"
Write-Host ""
Write-Host "For testing purposes, the app will run but Windows may show security warnings."
Write-Host "=========================================="
