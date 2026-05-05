#!/usr/bin/env pwsh
Param()
$ErrorActionPreference = 'Stop'

Write-Host "=========================================="
Write-Host "Installing Windows SDK for Code Signing"
Write-Host "=========================================="
Write-Host ""

# Try multiple methods to install Windows SDK
Write-Host "Method 1: Checking for Visual Studio Build Tools..."
$vsWhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
if (Test-Path $vsWhere) {
    Write-Host "Visual Studio detected. Attempting to install SDK components..."
    # This would require Visual Studio Installer, skip for now
}

Write-Host "Method 2: Downloading Windows SDK installer..."
$sdkUrl = "https://go.microsoft.com/fwlink/?linkid=2271442"
$sdkInstaller = "$env:TEMP\WindowsSDKInstaller.exe"

try {
    Write-Host "Downloading Windows SDK installer..."
    (New-Object System.Net.WebClient).DownloadFile($sdkUrl, $sdkInstaller)
    
    if (Test-Path $sdkInstaller) {
        Write-Host "Starting Windows SDK installation (this may take 10-30 minutes)..."
        Write-Host "Please check the installation window and select 'Signing Tools for Windows' feature."
        Write-Host ""
        
        # Run installer with parameters for signing tools
        & $sdkInstaller /Quiet /NoRestart /Features OptionId.WindowsDesktopDevelopmentTools,OptionId.DesktopCPPx64,OptionId.SigningTools
        
        Write-Host "Installation started. Please wait for it to complete..."
        Start-Sleep -Seconds 30
        
        # Check if it installed
        $signtoolPath = Get-ChildItem "C:\Program Files (x86)\Windows Kits" -Recurse -Filter "signtool.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($signtoolPath) {
            Write-Host "Windows SDK installed successfully!"
            Write-Host "signtool.exe found at: $($signtoolPath.FullName)"
        } else {
            Write-Host "Installation in progress. Check Windows Update or Apps & Features for 'Windows SDK'."
        }
    }
} catch {
    Write-Host "Could not auto-download. Please manually install Windows SDK:"
    Write-Host ""
    Write-Host "Steps:"
    Write-Host "1. Visit: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/"
    Write-Host "2. Download 'Windows SDK for Windows 11 (or 10)'"
    Write-Host "3. Run the installer"
    Write-Host "4. Select 'Signing Tools for Windows' when prompted"
    Write-Host "5. Complete installation"
    Write-Host "6. Re-run this script"
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Alternative: Self-Sign with PowerShell"
Write-Host "=========================================="
Write-Host ""

Write-Host "Creating self-signed certificate for testing..."

$certSubject = "CN=Speed Test Application v1.03"
$certPath = "$env:TEMP\speedtest_cert.pfx"
$certPassword = "TestSigningCert2024"

try {
    # Remove existing cert if present
    $existingCert = Get-ChildItem Cert:\CurrentUser\My -ErrorAction SilentlyContinue | 
        Where-Object { $_.Subject -eq $certSubject }
    if ($existingCert) {
        Remove-Item "Cert:\CurrentUser\My\$($existingCert[0].Thumbprint)" -Force -ErrorAction SilentlyContinue
        Write-Host "Removed existing certificate."
    }
    
    # Create new self-signed cert
    Write-Host "Creating new certificate: $certSubject"
    $cert = New-SelfSignedCertificate -CertStoreLocation Cert:\CurrentUser\My `
        -Subject $certSubject `
        -Type CodeSigningCert `
        -NotAfter (Get-Date).AddYears(5) `
        -KeyExportPolicy Exportable
    
    Write-Host "Certificate created with thumbprint: $($cert.Thumbprint)"
    
    # Export to PFX
    Write-Host "Exporting certificate to PFX..."
    $securePassword = ConvertTo-SecureString $certPassword -AsPlainText -Force
    Export-PfxCertificate -Cert $cert -FilePath $certPath -Password $securePassword -Force | Out-Null
    
    Write-Host "Certificate exported to: $certPath"
    Write-Host ""
    Write-Host "NOTE: This is a self-signed certificate for testing only."
    Write-Host "Windows will still show 'Unknown Publisher' warning when running the .exe"
    Write-Host ""
    Write-Host "For trusted distribution:"
    Write-Host "1. Purchase code signing cert from: DigiCert, Sectigo, or similar CA"
    Write-Host "2. Install the certificate to Cert:\CurrentUser\My"
    Write-Host "3. Re-run signtool with the purchased certificate"
    
} catch {
    Write-Host "Error creating certificate: $_"
    Write-Host "Make sure you run PowerShell as Administrator."
    exit 1
}

Write-Host ""
Write-Host "=========================================="
Write-Host "Certificate Ready"
Write-Host "=========================================="
Write-Host "Self-signed certificate created."
Write-Host "File: $certPath"
Write-Host ""
Write-Host "To manually sign the EXE once Windows SDK is installed:"
Write-Host ""
Write-Host 'signtool sign /f "$certPath" /p "$certPassword" /t http://timestamp.digicert.com C:\Users\kirwa\OneDrive\Documents\speedtest_gui_v1.03.exe'
Write-Host ""
