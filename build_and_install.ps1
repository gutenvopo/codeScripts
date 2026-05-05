#!/usr/bin/env pwsh
Param()
$ErrorActionPreference = 'Stop'

# Paths
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonVenv = Join-Path $projectRoot '..\.venv\Scripts\python.exe'
if (Test-Path $pythonVenv) { $python = $pythonVenv } else { $python = 'python' }

Write-Host "Using Python: $python"

Write-Host "Installing build dependencies (pyinstaller, pillow)..."
& $python -m pip install --upgrade pip
& $python -m pip install pyinstaller pillow

# Icon and script paths are relative to this script's folder (codeScripts)
$pngPath = Join-Path $projectRoot 'internet_test_icon.png'
$icoPath = Join-Path $projectRoot 'internet_test_icon.ico'
$scriptPath = Join-Path $projectRoot 'speedtest_gui_v1.02.py'
$convertScript = Join-Path $projectRoot 'convert_png_to_ico.py'
$distPath = [Environment]::GetFolderPath('MyDocuments')

if (-Not (Test-Path $pngPath)) {
    Write-Error "Icon PNG not found: $pngPath"
    exit 1
}

Write-Host "Converting PNG to ICO..."
& $python $convertScript --in $pngPath --out $icoPath

Write-Host "Building single-file executable into: $distPath"
& $python -m PyInstaller --noconfirm --onefile --windowed --icon $icoPath --distpath $distPath $scriptPath

# Determine exe path
$exeName = [IO.Path]::GetFileNameWithoutExtension($scriptPath) + '.exe'
$exePath = Join-Path $distPath $exeName

if (-Not (Test-Path $exePath)) {
    Write-Error "Expected EXE not found: $exePath"
    exit 1
}

Write-Host "Creating Desktop shortcut..."
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$linkPath = Join-Path $desktop 'SpeedTest Application.lnk'
$shortcut = $shell.CreateShortcut($linkPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $distPath
$shortcut.IconLocation = $icoPath
$shortcut.Save()
Write-Host "Desktop shortcut created: $linkPath"

Write-Host "Attempting to pin EXE to taskbar (may fail depending on system policy)..."
try {
    $shellApp = New-Object -ComObject Shell.Application
    $folder = $shellApp.Namespace((Split-Path $exePath -Parent))
    $item = $folder.ParseName((Split-Path $exePath -Leaf))
    $verbs = $item.Verbs()
    $pinned = $false
    for ($i=0; $i -lt $verbs.Count; $i++) {
        $verb = $verbs.Item($i)
        $name = $verb.Name.Replace('&','')
        if ($name -match 'Pin to taskbar|Pin to Tas') {
            $verb.DoIt()
            $pinned = $true
            break
        }
    }
    if ($pinned) { Write-Host "Pinned to taskbar." } else { Write-Host "Pin verb not found or pin failed." }
} catch {
    Write-Host "Pin to taskbar attempt failed: $_" -ForegroundColor Yellow
}

Write-Host "Build and shortcut creation complete. EXE located at: $exePath"
