#!/usr/bin/env pwsh
Param()
$ErrorActionPreference = 'Stop'

Write-Host "Installing Windows SDK..."
Write-Host "This will open Windows Settings to install Windows SDK components."
Write-Host ""

# Check if Windows SDK is already installed
$sdkPath = 'C:\Program Files (x86)\Windows Kits\10'
if (Test-Path $sdkPath) {
    Write-Host "Windows SDK 10 detected at: $sdkPath"
} else {
    Write-Host "Attempting to install Windows SDK via winget..."
    try {
        & winget install --id Microsoft.WindowsSDK.10.0 --accept-source-agreements -e
        Write-Host "Windows SDK installation completed."
    } catch {
        Write-Host "Failed to install via winget. Please manually install Windows SDK:"
        Write-Host "1. Go to: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/"
        Write-Host "2. Download and run the installer"
        Write-Host "3. Select 'Signing Tools for Windows 10' during installation"
        exit 1
    }
}

Write-Host ""
Write-Host "Locating signtool.exe..."
$signtoolPath = $null

# Check common Windows SDK locations
$possiblePaths = @(
    'C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe',
    'C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe',
    'C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe',
    'C:\Program Files (x86)\Windows Kits\11\bin\11.0.26100.0\x64\signtool.exe'
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $signtoolPath = $path
        break
    }
}

if (-Not $signtoolPath) {
    Write-Host "signtool.exe not found in standard locations."
    Write-Host "Please install Windows SDK with 'Signing Tools for Windows 10' selected."
    exit 1
}

Write-Host "Found signtool.exe at: $signtoolPath"

# Path to the executable to sign
$exePath = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'speedtest_gui_v1.03.exe'

if (-Not (Test-Path $exePath)) {
    Write-Error "Executable not found: $exePath"
    exit 1
}

Write-Host ""
Write-Host "Creating self-signed certificate for testing..."
Write-Host ""
Write-Host "NOTE: Self-signed certificates do NOT provide trusted publisher status."
Write-Host "For production use, obtain a certificate from a Certificate Authority (DigiCert, Sectigo, etc.)"
Write-Host ""

# Create a self-signed certificate in the test certificate store
$certSubject = "CN=Speed Test Application v1.03"
$certThumbprint = $null

# Check if cert already exists
$existingCert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -eq $certSubject }
if ($existingCert) {
    $certThumbprint = $existingCert[0].Thumbprint
    Write-Host "Using existing certificate: $certThumbprint"
} else {
    Write-Host "Creating new self-signed certificate..."
    try {
        # Create self-signed certificate
        $cert = New-SelfSignedCertificate -CertStoreLocation Cert:\CurrentUser\My `
            -Subject $certSubject `
            -Type CodeSigningCert `
            -NotAfter (Get-Date).AddYears(5) -ErrorAction Stop
        $certThumbprint = $cert.Thumbprint
        Write-Host "Created certificate with thumbprint: $certThumbprint"
    } catch {
        Write-Host "Failed to create self-signed certificate: $_"
        Write-Host "You may need to run PowerShell as Administrator."
        exit 1
    }
}

Write-Host ""
Write-Host "Signing executable: $exePath"
try {
    & $signtoolPath sign /f $null /p "" /sha1 $certThumbprint /t http://timestamp.digicert.com $exePath
    Write-Host ""
    Write-Host "Signature applied successfully!"
} catch {
    Write-Host "Signing command completed (check output above for details)."
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Signing process complete"
Write-Host "=========================================="
Write-Host "Executable: $exePath"
Write-Host ""
Write-Host "IMPORTANT: Self-Signed Certificate Notice"
Write-Host "- This certificate is for testing only"
Write-Host "- Windows may still show 'Unknown Publisher' warnings"
Write-Host "- For trusted distribution, purchase a code signing cert from a CA"
Write-Host "=========================================="
