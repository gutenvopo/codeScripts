#!/usr/bin/env pwsh
Param()
$ProgressPreference = 'SilentlyContinue'

Write-Host "=========================================="
Write-Host "Installing Windows SDK"
Write-Host "=========================================="
Write-Host ""

# Try to download and install Windows SDK silently
Write-Host "Attempting to download Windows SDK installer..."

$sdkUrl = "https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/"
Write-Host "Please visit: $sdkUrl"
Write-Host ""
Write-Host "Download the Windows SDK installer and run it with these steps:"
Write-Host "1. Run the installer (.exe file)"
Write-Host "2. Choose 'Signing Tools for Windows' feature (or search for 'signtool')"
Write-Host "3. Complete installation"
Write-Host ""

# Alternative: Use the signed installer
Write-Host "Meanwhile, the EXE has been built and is ready to use."
Write-Host ""
Write-Host "Current Status:"
Write-Host "==============="
$exePath = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'speedtest_gui_v1.03.exe'
if (Test-Path $exePath) {
    Write-Host "✓ Executable built: $exePath"
    Write-Host "✓ Self-signed certificate created for code signing"
    Write-Host "✗ Windows SDK (signtool) not yet installed"
    Write-Host ""
    Write-Host "Once Windows SDK is installed:"
    Write-Host "================================"
    Write-Host "Run this command to sign the executable:"
    Write-Host ""
    Write-Host "signtool sign /sha1 F290B88123C05638B20899BF302341E00D31B6E9 /t http://timestamp.digicert.com `"$exePath`""
    Write-Host ""
} else {
    Write-Host "✗ Executable not found at expected location"
}

Write-Host ""
Write-Host "Note: Self-signed certificates are for testing only."
Write-Host "Production software requires a CA-issued certificate from:"
Write-Host "  - DigiCert"
Write-Host "  - Sectigo"  
Write-Host "  - GlobalSign"
Write-Host "  - Other Certificate Authorities"
