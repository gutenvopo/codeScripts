#!/usr/bin/env pwsh
Param(
    [string]$ExePath = (Join-Path $PSScriptRoot 'dist\ytube_dwloader_v2.exe'),
    [string]$PfxPath,
    [string]$PfxPasswordPlain,
    [string]$Thumbprint,
    [string]$TimestampServer = 'http://timestamp.digicert.com',
    [switch]$UseLocalMachineStore
)

$ErrorActionPreference = 'Stop'

function Get-SecureStringFromPlainText {
    Param([Parameter(Mandatory = $true)][string]$PlainText)
    return (ConvertTo-SecureString -String $PlainText -AsPlainText -Force)
}

function Get-CertificateFromPfx {
    Param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][securestring]$Password
    )

    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password)
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        $flags = [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable -bor
                 [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::PersistKeySet
        return [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($Path, $plain, $flags)
    }
    finally {
        if ($bstr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
    }
}

if (-not (Test-Path -LiteralPath $ExePath)) {
    throw "EXE not found: $ExePath"
}

if ([string]::IsNullOrWhiteSpace($PfxPath) -and [string]::IsNullOrWhiteSpace($Thumbprint)) {
    throw "Provide either -PfxPath (recommended for CA-issued cert) or -Thumbprint."
}

$cert = $null

if (-not [string]::IsNullOrWhiteSpace($PfxPath)) {
    if (-not (Test-Path -LiteralPath $PfxPath)) {
        throw "PFX not found: $PfxPath"
    }

    if ([string]::IsNullOrWhiteSpace($PfxPasswordPlain)) {
        throw "When using -PfxPath, also provide -PfxPasswordPlain."
    }

    $securePassword = Get-SecureStringFromPlainText -PlainText $PfxPasswordPlain
    $cert = Get-CertificateFromPfx -Path $PfxPath -Password $securePassword
}
else {
    $storeLocation = if ($UseLocalMachineStore) { 'Cert:\LocalMachine\My' } else { 'Cert:\CurrentUser\My' }
    $cert = Get-ChildItem -Path $storeLocation | Where-Object { $_.Thumbprint -eq $Thumbprint } | Select-Object -First 1

    if (-not $cert) {
        throw "Certificate not found for thumbprint $Thumbprint in $storeLocation"
    }
}

Write-Host "Signing: $ExePath"
Write-Host "Signer Subject: $($cert.Subject)"

$signature = Set-AuthenticodeSignature -FilePath $ExePath -Certificate $cert -TimestampServer $TimestampServer

Write-Host ""
Write-Host "Signature result: $($signature.Status)"
Write-Host "Message: $($signature.StatusMessage)"

$verify = Get-AuthenticodeSignature -FilePath $ExePath

Write-Host ""
Write-Host "Verification status: $($verify.Status)"
Write-Host "Verification message: $($verify.StatusMessage)"

if ($verify.SignerCertificate) {
    Write-Host "Signer thumbprint: $($verify.SignerCertificate.Thumbprint)"
    Write-Host "Signer subject: $($verify.SignerCertificate.Subject)"
}

if ($verify.TimeStamperCertificate) {
    Write-Host "Timestamp subject: $($verify.TimeStamperCertificate.Subject)"
}

if ($verify.Status -eq 'Valid') {
    Write-Host ""
    Write-Host "SUCCESS: Executable is digitally signed and validates on this machine."
}
else {
    Write-Host ""
    Write-Host "INFO: Signature is attached, but trust depends on certificate chain trust on the target machine."
}
