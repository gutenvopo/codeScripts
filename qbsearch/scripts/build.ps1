[CmdletBinding()]
param(
    [string]$IsccPath = $env:ISCC_PATH
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

function Remove-GeneratedPath {
    param([Parameter(Mandatory)][string]$RelativePath)

    $target = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $RelativePath))
    $rootPrefix = $RepoRoot.TrimEnd("\") + "\"
    if (-not $target.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the repository: $target"
    }
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install it from https://docs.astral.sh/uv/ and retry."
}

uv sync --python 3.13 --system-certs

$activateScript = Join-Path $RepoRoot ".venv\Scripts\Activate.ps1"
if (-not (Test-Path -LiteralPath $activateScript)) {
    throw "uv sync did not create .venv\Scripts\Activate.ps1."
}
. $activateScript

python -c "import sys; assert sys.version_info[:2] == (3, 13), f'Python 3.13 required, got {sys.version}'"

$metadataJson = python -c "import json; from qbsearch.version import APP_ID, APP_NAME, __version__; print(json.dumps({'app_id': APP_ID, 'app_name': APP_NAME, 'version': __version__}))"
$metadata = $metadataJson | ConvertFrom-Json

Remove-GeneratedPath "build\pyinstaller"
Remove-GeneratedPath "dist"

pyinstaller --clean --noconfirm --distpath dist --workpath build\pyinstaller build\qbsearch.spec

if (-not $IsccPath) {
    $isccCommand = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($isccCommand) {
        $IsccPath = $isccCommand.Source
    }
}
if (-not $IsccPath) {
    $isccCandidates = @(
        (Join-Path ([Environment]::GetFolderPath("ProgramFilesX86")) "Inno Setup 6\ISCC.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
    )
    foreach ($candidate in $isccCandidates) {
        if (Test-Path -LiteralPath $candidate) {
            $IsccPath = $candidate
            break
        }
    }
}
if (-not $IsccPath -or -not (Test-Path -LiteralPath $IsccPath)) {
    throw "ISCC.exe was not found. Install Inno Setup 6 or pass -IsccPath."
}

& $IsccPath `
    "/DAppId=$($metadata.app_id)" `
    "/DAppName=$($metadata.app_name)" `
    "/DAppVersion=$($metadata.version)" `
    "installer\qbsearch.iss"

$installer = Join-Path $RepoRoot "dist\installer\qbsearch-$($metadata.version)-setup.exe"
if (-not (Test-Path -LiteralPath $installer)) {
    throw "Inno Setup completed without producing the expected installer: $installer"
}

Write-Host "Installer created: $installer"
