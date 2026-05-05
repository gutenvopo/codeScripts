Param(
    [string]$LnkPath
)
$ErrorActionPreference = 'Stop'

if (-not $LnkPath) {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $LnkPath = Join-Path $desktop 'SpeedTest Application.lnk'
}

if (-not (Test-Path $LnkPath)) {
    Write-Error "Shortcut not found: $LnkPath"
    exit 1
}

$pinnedFolder = Join-Path $env:APPDATA 'Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar'
if (-not (Test-Path $pinnedFolder)) {
    New-Item -ItemType Directory -Path $pinnedFolder -Force | Out-Null
}

$dest = Join-Path $pinnedFolder (Split-Path $LnkPath -Leaf)
Copy-Item -Path $LnkPath -Destination $dest -Force

Write-Host "Copied shortcut to pinned folder: $dest"

try {
    Write-Host "Restarting Explorer to apply pin..."
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
    Start-Process explorer
    Write-Host "Explorer restarted. Check the taskbar for the pinned icon.";
} catch {
    Write-Warning "Failed to restart Explorer: $_"
}
