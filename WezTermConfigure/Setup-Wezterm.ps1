<#
.SYNOPSIS
    Interactive WezTerm terminal setup for Windows.

.DESCRIPTION
    Walks you through each installation step ONE AT A TIME, waiting for each to
    complete before moving on. Provides verbose error messages on failure and
    lets you exit elegantly while still seeing the error that occurred.

    Adapted for Windows (PowerShell) from Josean Martinez's WezTerm guide.
    Uses winget/scoop instead of Homebrew, Starship instead of Powerlevel10k.

.NOTES
    Run in an elevated PowerShell session (Run as Administrator) for best results.
    Execution policy may need relaxing:
        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#>

# ---------------------------------------------------------------------------
#  Framework
# ---------------------------------------------------------------------------

$ErrorActionPreference = 'Stop'
$script:StepNumber     = 0
$script:TotalSteps     = 0

function Write-Banner {
    param([string]$Text)
    Write-Host ''
    Write-Host ('=' * 74) -ForegroundColor DarkCyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host ('=' * 74) -ForegroundColor DarkCyan
}

function Write-Info    { param($m) Write-Host "[i] $m" -ForegroundColor Gray }
function Write-Ok      { param($m) Write-Host "[+] $m" -ForegroundColor Green }
function Write-WarnMsg { param($m) Write-Host "[!] $m" -ForegroundColor Yellow }
function Write-ErrMsg  { param($m) Write-Host "[x] $m" -ForegroundColor Red }

# Pause so the user can read output / errors before anything closes.
function Pause-ForUser {
    param([string]$Message = 'Press ENTER to continue (or type Q then ENTER to quit)...')
    $answer = Read-Host "`n$Message"
    if ($answer -match '^(q|quit|exit)$') {
        Write-WarnMsg 'Exiting at your request. No further steps will run.'
        Exit-Cleanly 0
    }
}

# Graceful exit that keeps the window open so errors remain visible.
function Exit-Cleanly {
    param([int]$Code = 0)
    Write-Host ''
    Write-Host ('-' * 74) -ForegroundColor DarkGray
    if ($Code -eq 0) {
        Write-Ok 'Session ended.'
    } else {
        Write-ErrMsg "Session ended with exit code $Code. Review the messages above."
    }
    Read-Host 'Press ENTER to close this window'
    exit $Code
}

<#
  Runs a single named step. The provided script block does the work and
  should throw on failure. We catch, print a verbose error, and let the user
  decide whether to retry, skip, or quit — all without losing the error text.
#>
function Invoke-Step {
    param(
        [Parameter(Mandatory)][string]$Title,
        [Parameter(Mandatory)][scriptblock]$Action,
        [string]$Description = '',
        [scriptblock]$Verify  = $null,   # optional: returns $true if already done
        [switch]$Optional                 # allow skipping without warning
    )

    $script:StepNumber++
    Write-Banner ("STEP {0}/{1}: {2}" -f $script:StepNumber, $script:TotalSteps, $Title)
    if ($Description) { Write-Info $Description }

    # Skip if already satisfied.
    if ($Verify) {
        try {
            if (& $Verify) {
                Write-Ok 'Already installed / configured — skipping.'
                return
            }
        } catch { }
    }

    Pause-ForUser 'Press ENTER to run this step (or Q to quit, S to skip)...'
    if ($script:LastReadWasSkip) { $script:LastReadWasSkip = $false; return }

    while ($true) {
        try {
            & $Action
            Write-Ok "Step completed: $Title"
            return
        }
        catch {
            Write-Host ''
            Write-ErrMsg "Step FAILED: $Title"
            Write-Host  '--- Verbose error details -------------------------------------------' -ForegroundColor DarkRed
            Write-Host  ("Message   : {0}" -f $_.Exception.Message)              -ForegroundColor Red
            Write-Host  ("Category  : {0}" -f $_.CategoryInfo.Category)          -ForegroundColor Red
            if ($_.InvocationInfo) {
                Write-Host ("Location  : line {0}, col {1}" -f `
                    $_.InvocationInfo.ScriptLineNumber, $_.InvocationInfo.OffsetInLine) -ForegroundColor Red
                if ($_.InvocationInfo.Line) {
                    Write-Host ("Command   : {0}" -f $_.InvocationInfo.Line.Trim()) -ForegroundColor Red
                }
            }
            if ($_.ScriptStackTrace) {
                Write-Host 'Stack     :' -ForegroundColor Red
                Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
            }
            Write-Host  '---------------------------------------------------------------------' -ForegroundColor DarkRed

            $choice = Read-Host "`n(R)etry, (S)kip this step, or (Q)uit and keep this error visible? [R/S/Q]"
            switch -Regex ($choice) {
                '^(r|retry)?$' { Write-Info 'Retrying...'; continue }
                '^(s|skip)$'   {
                    if ($Optional) { Write-Info 'Skipping optional step.' }
                    else           { Write-WarnMsg 'Skipping — later steps may fail without this.' }
                    return
                }
                '^(q|quit|exit)$' { Exit-Cleanly 1 }
                default { Write-Info 'Retrying...'; continue }
            }
        }
    }
}

# Helper to override the built-in "run this step" pause with a skip option.
function Read-StepChoice { }  # reserved

# ---------------------------------------------------------------------------
#  Environment helpers
# ---------------------------------------------------------------------------

function Test-Command { param($Name) [bool](Get-Command $Name -ErrorAction SilentlyContinue) }

function Update-SessionPath {
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                [System.Environment]::GetEnvironmentVariable('Path','User')
}

function Invoke-Winget {
    param([string[]]$WingetArgs)
    if (-not (Test-Command winget)) {
        throw "winget (App Installer) is not available. Install 'App Installer' from the Microsoft Store, then re-run."
    }
    Write-Info ("Running: winget {0}" -f ($WingetArgs -join ' '))
    & winget @WingetArgs
    # winget uses non-zero for 'no upgrade found' etc.; treat only hard failures as errors.
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189) {
        throw "winget exited with code $LASTEXITCODE."
    }
}

# PowerShell profile path used for prompt / tool init.
$script:ProfilePath = $PROFILE.CurrentUserAllHosts

function Add-ToProfile {
    param([string]$Line, [string]$MatchPattern)
    $dir = Split-Path $script:ProfilePath -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (-not (Test-Path $script:ProfilePath)) { New-Item -ItemType File -Path $script:ProfilePath -Force | Out-Null }
    $existing = Get-Content $script:ProfilePath -Raw -ErrorAction SilentlyContinue
    if ($existing -and $MatchPattern -and ($existing -match [regex]::Escape($MatchPattern))) {
        Write-Info "Profile already contains this entry — not adding again."
        return
    }
    Add-Content -Path $script:ProfilePath -Value $Line
    Write-Ok "Added to profile: $($script:ProfilePath)"
}

# ---------------------------------------------------------------------------
#  Intro
# ---------------------------------------------------------------------------

Clear-Host
Write-Banner 'WezTerm Terminal Setup for Windows (interactive)'
Write-Host @"
This script installs and configures a WezTerm-based terminal on Windows,
one step at a time. After each step you choose to continue, skip, or quit.

If a step fails you'll get a verbose error and can Retry / Skip / Quit —
quitting always leaves the error on screen so you can read it.

  * Package manager : winget (App Installer)
  * Prompt          : Starship  (swapped in for Powerlevel10k)
  * Shell prompt    : configured via your PowerShell profile
"@ -ForegroundColor Gray

if (-not (Test-Command winget)) {
    Write-WarnMsg "winget was not found. Install 'App Installer' from the Microsoft Store first."
}

Pause-ForUser 'Press ENTER to begin (or Q to quit)...'

# Total step count (keep in sync with the Invoke-Step calls below).
$script:TotalSteps = 11

# ---------------------------------------------------------------------------
#  STEP 1 — Upgrade Bash   (moved to the TOP per request)
# ---------------------------------------------------------------------------

Invoke-Step -Title 'Upgrade Bash (newer Git Bash / Bash for Windows)' -Description @'
On Windows the modern Bash you want ships with Git for Windows (Git Bash).
This gives you an up-to-date bash used by tools and by WezTerm launch menus.
Installing/upgrading Git also installs (or updates) Git Bash.
'@ -Verify {
    if (Test-Command bash) {
        $v = (& bash --version 2>$null | Select-Object -First 1)
        if ($v) { Write-Info "Found: $v" }
        return $true
    }
    return $false
} -Action {
    Invoke-Winget @('install','--id','Git.Git','-e','--source','winget',
                    '--accept-package-agreements','--accept-source-agreements')
    Update-SessionPath
    if (Test-Command bash) {
        Write-Info ("Bash now: " + ((& bash --version 2>$null | Select-Object -First 1)))
    } else {
        Write-WarnMsg 'bash not on PATH yet — open a new terminal after setup to pick it up.'
    }
}

# ---------------------------------------------------------------------------
#  STEP 2 — Verify winget / package manager
# ---------------------------------------------------------------------------

Invoke-Step -Title 'Verify package manager (winget)' -Description @'
On macOS the guide uses Homebrew. On Windows we use winget (App Installer),
which ships with Windows 10/11. This step just confirms it works.
'@ -Verify {
    Test-Command winget
} -Action {
    if (-not (Test-Command winget)) {
        throw "winget not found. Install 'App Installer' from the Microsoft Store, then retry."
    }
    & winget --version | Out-Host
}

# ---------------------------------------------------------------------------
#  STEP 3 — Install WezTerm
# ---------------------------------------------------------------------------

Invoke-Step -Title 'Install WezTerm' -Description 'Installs the WezTerm terminal emulator.' -Verify {
    Test-Command wezterm -or (Test-Path "$env:ProgramFiles\WezTerm\wezterm.exe")
} -Action {
    Invoke-Winget @('install','--id','wez.wezterm','-e','--source','winget',
                    '--accept-package-agreements','--accept-source-agreements')
    Update-SessionPath
}

# ---------------------------------------------------------------------------
#  STEP 4 — Install Git (confirm)
# ---------------------------------------------------------------------------

Invoke-Step -Title 'Confirm Git is installed' -Description 'Git was likely installed in Step 1; this confirms it.' -Verify {
    Test-Command git
} -Action {
    if (-not (Test-Command git)) {
        Invoke-Winget @('install','--id','Git.Git','-e','--source','winget',
                        '--accept-package-agreements','--accept-source-agreements')
        Update-SessionPath
    }
    & git --version | Out-Host
}

# ---------------------------------------------------------------------------
#  STEP 5 — Install Meslo Nerd Font
# ---------------------------------------------------------------------------

Invoke-Step -Title 'Install Meslo Nerd Font' -Description @'
Nerd Fonts render the icons used by the prompt and file listings.
This downloads the Meslo Nerd Font archive from the official Nerd Fonts
GitHub release and installs the .ttf files for the current user (no admin
needed). If the download fails it falls back to winget.
'@ -Verify {
    # Consider it done if any MesloLGS Nerd Font file is already installed.
    $userFonts = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
    (Test-Path (Join-Path $env:WINDIR 'Fonts\MesloLGSNerdFont-Regular.ttf')) -or
    ((Test-Path $userFonts) -and (Get-ChildItem $userFonts -Filter 'MesloLGS*NerdFont*.ttf' -ErrorAction SilentlyContinue))
} -Action {

    function Install-FontFile {
        param([string]$Path)
        $fontsDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
        if (-not (Test-Path $fontsDir)) { New-Item -ItemType Directory -Path $fontsDir -Force | Out-Null }
        $dest = Join-Path $fontsDir (Split-Path $Path -Leaf)
        Copy-Item $Path $dest -Force
        # Register per-user so apps see it without admin rights.
        $regPath = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
        if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }
        $name = [System.IO.Path]::GetFileNameWithoutExtension($Path) + ' (TrueType)'
        New-ItemProperty -Path $regPath -Name $name -Value $dest -PropertyType String -Force | Out-Null
    }

    $installedViaDownload = $false
    try {
        $tmp = Join-Path $env:TEMP ("meslo-nf-" + [guid]::NewGuid())
        New-Item -ItemType Directory -Path $tmp -Force | Out-Null
        $zip = Join-Path $tmp 'Meslo.zip'
        # Stable release-asset URL: 'latest' + the fixed asset name 'Meslo.zip'.
        $url = 'https://github.com/ryanoasis/nerd-fonts/releases/latest/download/Meslo.zip'

        Write-Info "Downloading Meslo Nerd Font from: $url"
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $ProgressPreference = 'SilentlyContinue'   # much faster download
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing

        Write-Info 'Extracting...'
        Expand-Archive -Path $zip -DestinationPath $tmp -Force

        # Install just the 'MesloLGS' mono/regular variants used by the config.
        $ttfs = Get-ChildItem $tmp -Recurse -Filter 'MesloLGS*NerdFont*.ttf'
        if (-not $ttfs) { $ttfs = Get-ChildItem $tmp -Recurse -Filter 'MesloLGS*.ttf' }
        if (-not $ttfs) { throw 'No MesloLGS .ttf files found inside the archive.' }

        foreach ($f in $ttfs) {
            Install-FontFile -Path $f.FullName
            Write-Ok ("Installed: " + $f.Name)
        }
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
        $installedViaDownload = $true
    }
    catch {
        Write-WarnMsg "Direct download failed ($($_.Exception.Message)). Falling back to winget..."
    }

    if (-not $installedViaDownload) {
        # Fallback: try the winget font package (publisher DEVCOM ships Nerd Fonts).
        try {
            Invoke-Winget @('install','--id','DEVCOM.MesloLGMNerdFont','-e','--source','winget',
                            '--accept-package-agreements','--accept-source-agreements')
        } catch {
            throw ("Both the direct download and winget failed. " +
                   "Install manually from https://www.nerdfonts.com (download 'Meslo', " +
                   "unzip, right-click the .ttf files > Install). Underlying error: " + $_.Exception.Message)
        }
    }

    Write-Info "Font family to select in WezTerm / your terminal: 'MesloLGS Nerd Font Mono'"
}

# ---------------------------------------------------------------------------
#  STEP 6 — Create ~/.wezterm.lua config
# ---------------------------------------------------------------------------

Invoke-Step -Title 'Create WezTerm config (.wezterm.lua)' -Description @'
Creates a .wezterm.lua in your home folder with a sensible base config,
the Meslo Nerd Font, and the coolnight colour scheme.
'@ -Action {
    $cfgPath = Join-Path $HOME '.wezterm.lua'
    if (Test-Path $cfgPath) {
        $bak = "$cfgPath.bak-$(Get-Date -Format yyyyMMddHHmmss)"
        Copy-Item $cfgPath $bak
        Write-WarnMsg "Existing config backed up to: $bak"
    }
    $lua = @'
-- Pull in the wezterm API
local wezterm = require("wezterm")

-- This will hold the configuration.
local config = wezterm.config_builder()

-- Windows default shell (comment out to use your system default)
config.default_prog = { "pwsh.exe" }

config.font = wezterm.font("MesloLGS Nerd Font Mono")
config.font_size = 12

config.enable_tab_bar = false
config.window_decorations = "RESIZE"
config.window_background_opacity = 0.9

-- coolnight colorscheme
config.colors = {
    foreground = "#CBE0F0",
    background = "#011423",
    cursor_bg = "#47FF9C",
    cursor_border = "#47FF9C",
    cursor_fg = "#011423",
    selection_bg = "#033259",
    selection_fg = "#CBE0F0",
    ansi = { "#214969", "#E52E2E", "#44FFB1", "#FFE073", "#0FC5ED", "#a277ff", "#24EAF7", "#24EAF7" },
    brights = { "#214969", "#E52E2E", "#44FFB1", "#FFE073", "#A277FF", "#a277ff", "#24EAF7", "#24EAF7" },
}

-- and finally, return the configuration to wezterm
return config
'@
    Set-Content -Path $cfgPath -Value $lua -Encoding UTF8
    Write-Ok "Wrote $cfgPath"
    Write-Info 'Edit this file anytime to change the colour scheme or font.'
}

# ---------------------------------------------------------------------------
#  STEP 7 — Install Starship  (replaces Powerlevel10k)
# ---------------------------------------------------------------------------

Invoke-Step -Title 'Install Starship prompt' -Description @'
Starship is a fast, cross-shell prompt written in Rust. It replaces the
Powerlevel10k theme from the original macOS/zsh guide and works natively
with PowerShell on Windows.
'@ -Verify {
    Test-Command starship
} -Action {
    Invoke-Winget @('install','--id','Starship.Starship','-e','--source','winget',
                    '--accept-package-agreements','--accept-source-agreements')
    Update-SessionPath
    if (-not (Test-Command starship)) {
        throw 'starship not found on PATH after install. Open a new terminal and re-run this step, or add it to PATH manually.'
    }
    & starship --version | Out-Host
}

# ---------------------------------------------------------------------------
#  STEP 8 — Enable Starship in PowerShell profile
# ---------------------------------------------------------------------------

Invoke-Step -Title 'Enable Starship in your PowerShell profile' -Description @'
Adds the Starship init line to your PowerShell profile so the prompt loads
in every new session. (This is the Windows equivalent of sourcing p10k in
~/.zshrc.)
'@ -Action {
    Add-ToProfile -Line 'Invoke-Expression (&starship init powershell)' -MatchPattern 'starship init powershell'
    Write-Info 'To customise the prompt, create a config at:'
    Write-Info "  $env:USERPROFILE\.config\starship.toml"
    Write-Info 'Docs: https://starship.rs/config/'
}

# ---------------------------------------------------------------------------
#  STEP 9 — PSReadLine history / arrow-key completion
# ---------------------------------------------------------------------------

Invoke-Step -Title 'Better history completion (up/down arrows)' -Description @'
The macOS guide configures zsh history search. On Windows PSReadLine provides
the same: HistorySearch on the up/down arrows plus inline prediction.
'@ -Action {
    $block = @'

# ---- PSReadLine history search (up/down arrows) ----
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineKeyHandler -Key UpArrow   -Function HistorySearchBackward
Set-PSReadLineKeyHandler -Key DownArrow -Function HistorySearchForward
'@
    Add-ToProfile -Line $block -MatchPattern 'HistorySearchBackward'
}

# ---------------------------------------------------------------------------
#  STEP 10 — zoxide (better cd)
# ---------------------------------------------------------------------------

Invoke-Step -Title 'Install zoxide (better cd)' -Description @'
zoxide remembers directories you visit so you can jump with a partial name.
Installs zoxide and wires it into your profile with a `cd` alias.
'@ -Verify {
    Test-Command zoxide
} -Action {
    Invoke-Winget @('install','--id','ajeetdsouza.zoxide','-e','--source','winget',
                    '--accept-package-agreements','--accept-source-agreements')
    Update-SessionPath
    if (-not (Test-Command zoxide)) { throw 'zoxide not found on PATH after install.' }
    Add-ToProfile -Line @'

# ---- zoxide (better cd) ----
Invoke-Expression (& { (zoxide init powershell --cmd cd | Out-String) })
'@ -MatchPattern 'zoxide init powershell'
}

# ---------------------------------------------------------------------------
#  STEP 11 — eza (better ls)
# ---------------------------------------------------------------------------

Invoke-Step -Title 'Install eza (better ls)' -Optional -Description @'
eza is a modern replacement for ls with icons and colours. Optional.
'@ -Verify {
    Test-Command eza
} -Action {
    Invoke-Winget @('install','--id','eza-community.eza','-e','--source','winget',
                    '--accept-package-agreements','--accept-source-agreements')
    Update-SessionPath
    Add-ToProfile -Line @'

# ---- eza (better ls) ----
function ls { eza --icons=always @args }
'@ -MatchPattern 'eza --icons'
}

# ---------------------------------------------------------------------------
#  Done
# ---------------------------------------------------------------------------

Write-Banner "You're Done! 🚀"
Write-Host @"
Next steps:
  1. Close this window and open WezTerm.
  2. Open a NEW PowerShell session so profile changes take effect.
  3. Set WezTerm's font to 'MesloLGS Nerd Font Mono' if icons look wrong.
  4. Customise your prompt at %USERPROFILE%\.config\starship.toml

Profile edited: $script:ProfilePath
"@ -ForegroundColor Gray

Exit-Cleanly 0