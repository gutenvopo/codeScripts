#!/usr/bin/env pwsh
Param(
    [string]$PythonExe,
    [string]$ScriptPath = (Join-Path $PSScriptRoot 'ytube_dwloader_v2.py'),
    [string]$PngIconPath = (Join-Path $PSScriptRoot 'youtube_dldr_image.png'),
    [string]$IcoPath = (Join-Path $PSScriptRoot 'youtube_dldr_image.ico'),
    [string]$ExeName = 'ytube_dwloader_v2',
    [string]$DistPath = (Join-Path $PSScriptRoot 'dist'),
    [string]$BuildPath = (Join-Path $PSScriptRoot 'build'),
    [string]$SpecPath = $PSScriptRoot,
    [string]$PfxPath,
    [string]$PfxPasswordPlain,
    [string]$Thumbprint,
    [string]$TimestampServer = 'http://timestamp.digicert.com',
    [switch]$UseLocalMachineStore,
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'

if (-not $PythonExe) {
    $preferredPython = Join-Path $PSScriptRoot 'rwakiDev_v3\Scripts\python.exe'
    if (Test-Path -LiteralPath $preferredPython) {
        $PythonExe = $preferredPython
    }
    else {
        $PythonExe = 'python'
    }
}

$signScript = Join-Path $PSScriptRoot 'sign_ytube_dwloader_v2.ps1'
$convertScript = Join-Path $PSScriptRoot 'convert_png_to_ico.py'
$exePath = Join-Path $DistPath "$ExeName.exe"

if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "Script not found: $ScriptPath"
}

if (-not (Test-Path -LiteralPath $signScript)) {
    throw "Signing script not found: $signScript"
}

if (-not $SkipBuild) {
    if (-not (Test-Path -LiteralPath $PngIconPath)) {
        throw "PNG icon not found: $PngIconPath"
    }

    if (-not (Test-Path -LiteralPath $convertScript)) {
        throw "Icon conversion script not found: $convertScript"
    }

    Write-Host "Using Python: $PythonExe"
    Write-Host "Ensuring build dependencies..."
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install pyinstaller pillow

    Write-Host "Converting PNG icon to ICO..."
    & $PythonExe $convertScript --in $PngIconPath --out $IcoPath

    Write-Host "Building single-file executable..."
    & $PythonExe -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --icon $IcoPath `
        --name $ExeName `
        --distpath $DistPath `
        --workpath $BuildPath `
        --specpath $SpecPath `
        $ScriptPath
}

if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Built EXE not found: $exePath"
}

Write-Host "Signing executable: $exePath"

$signArgs = @{
    ExePath = $exePath
    TimestampServer = $TimestampServer
}

if ($UseLocalMachineStore) {
    $signArgs.UseLocalMachineStore = $true
}

if (-not [string]::IsNullOrWhiteSpace($PfxPath)) {
    $signArgs.PfxPath = $PfxPath
    $signArgs.PfxPasswordPlain = $PfxPasswordPlain
}
elseif (-not [string]::IsNullOrWhiteSpace($Thumbprint)) {
    $signArgs.Thumbprint = $Thumbprint
}
else {
    throw "Provide signing input: either -PfxPath with -PfxPasswordPlain, or -Thumbprint."
}

& $signScript @signArgs

Write-Host ""
Write-Host "Release complete"
Write-Host "Executable: $exePath"
