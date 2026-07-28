#Requires -Version 7.0

<#
    KAZI TRACKER // BUILD CONSOLE

    Project:
        C:\Users\kirwa\Documents\coding\codeScripts\kazi-tracker

    Pipeline:
        npm run lint
        npm run build
        firebase deploy --only hosting

    This script uses a PowerShell background job so the Windows Forms
    interface remains responsive. A compiled .NET guard owns the emergency
    close path, so the window can still close if a PowerShell UI callback
    throws PipelineStoppedException.
#>

Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()
[System.Windows.Forms.Application]::SetUnhandledExceptionMode(
    [System.Windows.Forms.UnhandledExceptionMode]::CatchException
)

# ============================================================================
# .NET-LEVEL WINDOWS FORMS SAFETY GUARD
# ============================================================================

if (-not ("KaziTracker.BuildConsole.WinFormsGuardV2" -as [type])) {
    $guardSource = @'
using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Windows.Forms;

namespace KaziTracker.BuildConsole
{
    public static class WinFormsGuardV2
    {
        private static Form mainForm;
        private static string emergencyLogPath;
        private static int handlingException;
        private static int emergencyClosing;
        private static bool threadHandlerAttached;
        private static bool closeButtonAttached;

        public static void Attach(Form form, string logPath)
        {
            mainForm = form;
            emergencyLogPath = logPath;

            if (!threadHandlerAttached)
            {
                Application.ThreadException += OnThreadException;
                threadHandlerAttached = true;
            }
        }

        public static void SetEmergencyLogPath(string logPath)
        {
            emergencyLogPath = logPath;
        }

        public static void AttachCloseButton(Button closeButton)
        {
            if (closeButton == null || closeButtonAttached)
            {
                return;
            }

            closeButton.Click += OnCloseButtonClick;
            closeButtonAttached = true;
        }

        private static void OnCloseButtonClick(object sender, EventArgs args)
        {
            try
            {
                Form form = mainForm;

                if (form == null || form.IsDisposed)
                {
                    EmergencyClose();
                    return;
                }

                form.Close();
            }
            catch (Exception exception)
            {
                WriteEmergencyLog(
                    "The native close-button handler failed.",
                    exception
                );

                EmergencyClose();
            }
        }

        private static void OnThreadException(
            object sender,
            ThreadExceptionEventArgs args
        )
        {
            if (Interlocked.Exchange(ref handlingException, 1) == 1)
            {
                EmergencyClose();
                return;
            }

            try
            {
                Exception exception = args == null ? null : args.Exception;
                bool pipelineStopped = IsPipelineStopped(exception);

                WriteEmergencyLog(
                    pipelineStopped
                        ? "A PowerShell UI pipeline was stopped."
                        : "An unhandled Windows Forms callback error occurred.",
                    exception
                );

                if (!pipelineStopped)
                {
                    try
                    {
                        MessageBox.Show(
                            "The build console encountered an unexpected " +
                            "interface error and will close safely.\r\n\r\n" +
                            "Details were written to the diagnostic log.",
                            "Kazi Tracker Build Console",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Error
                        );
                    }
                    catch
                    {
                        // Never let error reporting prevent shutdown.
                    }
                }
            }
            catch
            {
                // Never throw from the final UI exception boundary.
            }
            finally
            {
                EmergencyClose();
                Interlocked.Exchange(ref handlingException, 0);
            }
        }

        private static bool IsPipelineStopped(Exception exception)
        {
            Exception current = exception;

            while (current != null)
            {
                if (String.Equals(
                    current.GetType().FullName,
                    "System.Management.Automation.PipelineStoppedException",
                    StringComparison.Ordinal
                ))
                {
                    return true;
                }

                current = current.InnerException;
            }

            return false;
        }

        private static void WriteEmergencyLog(
            string heading,
            Exception exception
        )
        {
            try
            {
                string path = emergencyLogPath;

                if (String.IsNullOrWhiteSpace(path))
                {
                    path = Path.Combine(
                        Path.GetTempPath(),
                        "KaziTrackerBuildConsole-emergency.log"
                    );
                }

                string directory = Path.GetDirectoryName(path);

                if (!String.IsNullOrWhiteSpace(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                StringBuilder entry = new StringBuilder();
                entry.AppendLine();
                entry.Append("[");
                entry.Append(DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff"));
                entry.AppendLine("] [EMERGENCY UI ERROR]");
                entry.AppendLine(heading ?? "No error heading was available.");

                if (exception != null)
                {
                    entry.Append("Exception type: ");
                    entry.AppendLine(exception.GetType().FullName);
                    entry.Append("Exception message: ");
                    entry.AppendLine(exception.Message);
                    entry.AppendLine(exception.ToString());
                }

                File.AppendAllText(path, entry.ToString(), Encoding.UTF8);
            }
            catch
            {
                // The emergency logger must never throw.
            }
        }

        public static void EmergencyClose()
        {
            if (Interlocked.Exchange(ref emergencyClosing, 1) == 1)
            {
                return;
            }

            try
            {
                Form form = mainForm;

                if (form != null && !form.IsDisposed)
                {
                    try
                    {
                        form.Hide();
                    }
                    catch
                    {
                    }

                    try
                    {
                        form.Dispose();
                    }
                    catch
                    {
                    }
                }
            }
            catch
            {
            }
            finally
            {
                try
                {
                    Application.ExitThread();
                }
                catch
                {
                }

                Interlocked.Exchange(ref emergencyClosing, 0);
            }
        }
    }
}
'@

    # Supplying -ReferencedAssemblies replaces Add-Type's normal reference
    # set. Include PowerShell's complete .NET reference set plus WinForms.
    $guardReferences = @(
        Get-ChildItem `
            -LiteralPath (Join-Path $PSHOME "ref") `
            -Filter "*.dll" |
            ForEach-Object {
                $_.FullName
            }
    )
    $guardReferences += [System.Windows.Forms.Form].Assembly.Location

    Add-Type `
        -TypeDefinition $guardSource `
        -Language CSharp `
        -ReferencedAssemblies $guardReferences `
        -ErrorAction Stop
}

# ============================================================================
# CONFIGURATION AND STATE
# ============================================================================

$projectPath = "C:\Users\kirwa\Documents\coding\codeScripts\kazi-tracker"
$emergencyLogPath = Join-Path $env:TEMP "KaziTrackerBuildConsole-emergency.log"

$script:buildJob = $null
$script:logFile = $null
$script:lastRunSuccessful = $false
$script:finalEventReceived = $false
$script:isClosing = $false
$script:cleanupStarted = $false
$script:monitorFailureReported = $false

# ============================================================================
# COLOR PALETTE
# ============================================================================

$colorBackground = [System.Drawing.Color]::FromArgb(6, 9, 16)
$colorPanel = [System.Drawing.Color]::FromArgb(11, 17, 28)
$colorConsole = [System.Drawing.Color]::FromArgb(2, 6, 12)
$colorTrack = [System.Drawing.Color]::FromArgb(24, 33, 47)
$colorText = [System.Drawing.Color]::FromArgb(224, 234, 244)
$colorMuted = [System.Drawing.Color]::FromArgb(126, 148, 171)
$colorCyan = [System.Drawing.Color]::FromArgb(0, 229, 255)
$colorBlue = [System.Drawing.Color]::FromArgb(91, 151, 255)
$colorGreen = [System.Drawing.Color]::FromArgb(54, 255, 138)
$colorYellow = [System.Drawing.Color]::FromArgb(255, 205, 86)
$colorRed = [System.Drawing.Color]::FromArgb(255, 72, 101)
$colorPurple = [System.Drawing.Color]::FromArgb(194, 112, 255)

# ============================================================================
# MAIN WINDOW
# ============================================================================

$form = [System.Windows.Forms.Form]::new()
$form.Text = "Kazi Tracker // Build Console"
$form.ClientSize = [System.Drawing.Size]::new(1040, 760)
$form.MinimumSize = [System.Drawing.Size]::new(900, 680)
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
$form.BackColor = $colorBackground
$form.ForeColor = $colorText
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::Sizable
$form.MaximizeBox = $true
$form.MinimizeBox = $true
$form.KeyPreview = $true

[KaziTracker.BuildConsole.WinFormsGuardV2]::Attach(
    $form,
    $emergencyLogPath
)

$headerPanel = [System.Windows.Forms.Panel]::new()
$headerPanel.Dock = [System.Windows.Forms.DockStyle]::Top
$headerPanel.Height = 108
$headerPanel.BackColor = $colorPanel

$titleLabel = [System.Windows.Forms.Label]::new()
$titleLabel.Location = [System.Drawing.Point]::new(26, 17)
$titleLabel.Size = [System.Drawing.Size]::new(690, 39)
$titleLabel.Text = "KAZI TRACKER // BUILD CONSOLE"
$titleLabel.ForeColor = $colorCyan
$titleLabel.Font = [System.Drawing.Font]::new(
    "Segoe UI",
    18,
    [System.Drawing.FontStyle]::Bold
)

$subtitleLabel = [System.Windows.Forms.Label]::new()
$subtitleLabel.Location = [System.Drawing.Point]::new(29, 62)
$subtitleLabel.Size = [System.Drawing.Size]::new(720, 23)
$subtitleLabel.Text = "AUTOMATED CODE QUALITY // PRODUCTION BUILD SYSTEM"
$subtitleLabel.ForeColor = $colorMuted
$subtitleLabel.Font = [System.Drawing.Font]::new("Consolas", 10)

$statusLabel = [System.Windows.Forms.Label]::new()
$statusLabel.Anchor = (
    [System.Windows.Forms.AnchorStyles]::Top -bor
    [System.Windows.Forms.AnchorStyles]::Right
)
$statusLabel.Location = [System.Drawing.Point]::new(819, 27)
$statusLabel.Size = [System.Drawing.Size]::new(190, 42)
$statusLabel.Text = "[ READY ]"
$statusLabel.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$statusLabel.BackColor = $colorBackground
$statusLabel.ForeColor = $colorCyan
$statusLabel.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
$statusLabel.Font = [System.Drawing.Font]::new(
    "Consolas",
    11,
    [System.Drawing.FontStyle]::Bold
)

$accentLine = [System.Windows.Forms.Panel]::new()
$accentLine.Dock = [System.Windows.Forms.DockStyle]::Bottom
$accentLine.Height = 3
$accentLine.BackColor = $colorCyan

$headerPanel.Controls.AddRange(@(
    $titleLabel,
    $subtitleLabel,
    $statusLabel,
    $accentLine
))

$outputTitle = [System.Windows.Forms.Label]::new()
$outputTitle.Anchor = (
    [System.Windows.Forms.AnchorStyles]::Top -bor
    [System.Windows.Forms.AnchorStyles]::Left
)
$outputTitle.Location = [System.Drawing.Point]::new(26, 123)
$outputTitle.Size = [System.Drawing.Size]::new(600, 25)
$outputTitle.Text = "SYSTEM OUTPUT // LIVE TELEMETRY"
$outputTitle.ForeColor = $colorBlue
$outputTitle.Font = [System.Drawing.Font]::new(
    "Consolas",
    10,
    [System.Drawing.FontStyle]::Bold
)

$outputBox = [System.Windows.Forms.RichTextBox]::new()
$outputBox.Anchor = (
    [System.Windows.Forms.AnchorStyles]::Top -bor
    [System.Windows.Forms.AnchorStyles]::Bottom -bor
    [System.Windows.Forms.AnchorStyles]::Left -bor
    [System.Windows.Forms.AnchorStyles]::Right
)
$outputBox.Location = [System.Drawing.Point]::new(26, 152)
$outputBox.Size = [System.Drawing.Size]::new(988, 454)
$outputBox.BackColor = $colorConsole
$outputBox.ForeColor = $colorText
$outputBox.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
$outputBox.ReadOnly = $true
$outputBox.WordWrap = $false
$outputBox.DetectUrls = $false
$outputBox.HideSelection = $false
$outputBox.ScrollBars = [System.Windows.Forms.RichTextBoxScrollBars]::Both
$outputBox.Font = [System.Drawing.Font]::new("Consolas", 10)

$progressText = [System.Windows.Forms.Label]::new()
$progressText.Anchor = (
    [System.Windows.Forms.AnchorStyles]::Bottom -bor
    [System.Windows.Forms.AnchorStyles]::Left -bor
    [System.Windows.Forms.AnchorStyles]::Right
)
$progressText.Location = [System.Drawing.Point]::new(26, 621)
$progressText.Size = [System.Drawing.Size]::new(988, 22)
$progressText.Text = "PIPELINE PROGRESS: 0%"
$progressText.ForeColor = $colorMuted
$progressText.Font = [System.Drawing.Font]::new(
    "Consolas",
    9,
    [System.Drawing.FontStyle]::Bold
)

$progressTrack = [System.Windows.Forms.Panel]::new()
$progressTrack.Anchor = (
    [System.Windows.Forms.AnchorStyles]::Bottom -bor
    [System.Windows.Forms.AnchorStyles]::Left -bor
    [System.Windows.Forms.AnchorStyles]::Right
)
$progressTrack.Location = [System.Drawing.Point]::new(26, 648)
$progressTrack.Size = [System.Drawing.Size]::new(988, 11)
$progressTrack.BackColor = $colorTrack

$progressFill = [System.Windows.Forms.Panel]::new()
$progressFill.Location = [System.Drawing.Point]::new(0, 0)
$progressFill.Size = [System.Drawing.Size]::new(0, 11)
$progressFill.BackColor = $colorCyan
$progressTrack.Controls.Add($progressFill)

function Set-ButtonStyle {
    param(
        [Parameter(Mandatory)]
        [System.Windows.Forms.Button]$Button,

        [Parameter(Mandatory)]
        [System.Drawing.Color]$AccentColor
    )

    $Button.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
    $Button.FlatAppearance.BorderSize = 1
    $Button.FlatAppearance.BorderColor = $AccentColor
    $Button.FlatAppearance.MouseOverBackColor = (
        [System.Drawing.Color]::FromArgb(21, 34, 49)
    )
    $Button.FlatAppearance.MouseDownBackColor = (
        [System.Drawing.Color]::FromArgb(30, 48, 68)
    )
    $Button.BackColor = $colorPanel
    $Button.ForeColor = $AccentColor
    $Button.Cursor = [System.Windows.Forms.Cursors]::Hand
    $Button.Font = [System.Drawing.Font]::new(
        "Segoe UI",
        10,
        [System.Drawing.FontStyle]::Bold
    )
}

$buttonPanel = [System.Windows.Forms.TableLayoutPanel]::new()
$buttonPanel.Anchor = (
    [System.Windows.Forms.AnchorStyles]::Bottom -bor
    [System.Windows.Forms.AnchorStyles]::Left -bor
    [System.Windows.Forms.AnchorStyles]::Right
)
$buttonPanel.Location = [System.Drawing.Point]::new(26, 681)
$buttonPanel.Size = [System.Drawing.Size]::new(988, 48)
$buttonPanel.ColumnCount = 4
$buttonPanel.RowCount = 1
$buttonPanel.BackColor = $colorBackground
$buttonPanel.ColumnStyles.Add(
    [System.Windows.Forms.ColumnStyle]::new(
        [System.Windows.Forms.SizeType]::Percent,
        25
    )
)
$buttonPanel.ColumnStyles.Add(
    [System.Windows.Forms.ColumnStyle]::new(
        [System.Windows.Forms.SizeType]::Percent,
        25
    )
)
$buttonPanel.ColumnStyles.Add(
    [System.Windows.Forms.ColumnStyle]::new(
        [System.Windows.Forms.SizeType]::Percent,
        25
    )
)
$buttonPanel.ColumnStyles.Add(
    [System.Windows.Forms.ColumnStyle]::new(
        [System.Windows.Forms.SizeType]::Percent,
        25
    )
)

$startButton = [System.Windows.Forms.Button]::new()
$startButton.Dock = [System.Windows.Forms.DockStyle]::Fill
$startButton.Margin = [System.Windows.Forms.Padding]::new(0, 0, 9, 0)
$startButton.Text = "START PIPELINE"
Set-ButtonStyle -Button $startButton -AccentColor $colorGreen

$openLogButton = [System.Windows.Forms.Button]::new()
$openLogButton.Dock = [System.Windows.Forms.DockStyle]::Fill
$openLogButton.Margin = [System.Windows.Forms.Padding]::new(3, 0, 6, 0)
$openLogButton.Text = "OPEN FULL LOG"
$openLogButton.Enabled = $false
Set-ButtonStyle -Button $openLogButton -AccentColor $colorBlue

$clearButton = [System.Windows.Forms.Button]::new()
$clearButton.Dock = [System.Windows.Forms.DockStyle]::Fill
$clearButton.Margin = [System.Windows.Forms.Padding]::new(6, 0, 3, 0)
$clearButton.Text = "CLEAR CONSOLE"
Set-ButtonStyle -Button $clearButton -AccentColor $colorYellow

$closeButton = [System.Windows.Forms.Button]::new()
$closeButton.Dock = [System.Windows.Forms.DockStyle]::Fill
$closeButton.Margin = [System.Windows.Forms.Padding]::new(9, 0, 0, 0)
$closeButton.Text = "CLOSE"
Set-ButtonStyle -Button $closeButton -AccentColor $colorRed

$buttonPanel.Controls.Add($startButton, 0, 0)
$buttonPanel.Controls.Add($openLogButton, 1, 0)
$buttonPanel.Controls.Add($clearButton, 2, 0)
$buttonPanel.Controls.Add($closeButton, 3, 0)

# The close button is intentionally owned by compiled .NET code. It therefore
# remains functional even when PowerShell can no longer invoke Click handlers.
[KaziTracker.BuildConsole.WinFormsGuardV2]::AttachCloseButton($closeButton)

$form.Controls.AddRange(@(
    $headerPanel,
    $outputTitle,
    $outputBox,
    $progressText,
    $progressTrack,
    $buttonPanel
))

# ============================================================================
# UI AND CLEANUP HELPERS
# ============================================================================

function Test-IsPipelineStoppedException {
    param(
        [AllowNull()]
        [System.Exception]$Exception
    )

    $current = $Exception

    while ($null -ne $current) {
        if (
            $current.GetType().FullName -eq
            "System.Management.Automation.PipelineStoppedException"
        ) {
            return $true
        }

        $current = $current.InnerException
    }

    return $false
}

function Remove-AnsiCodes {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Text
    )

    if ($null -eq $Text) {
        return ""
    }

    $escapeCharacter = [char]27
    $ansiPattern = "$escapeCharacter\[[0-?]*[ -/]*[@-~]"

    return ($Text -replace $ansiPattern, "")
}

function Get-LevelColor {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Level
    )

    switch ($Level) {
        "SYSTEM" { return $colorCyan }
        "INFO" { return $colorText }
        "OUTPUT" {
            return [System.Drawing.Color]::FromArgb(187, 203, 218)
        }
        "SECTION" { return $colorPurple }
        "SUCCESS" { return $colorGreen }
        "WARNING" { return $colorYellow }
        "ERROR" { return $colorRed }
        "DIAGNOSTIC" { return $colorBlue }
        default { return $colorText }
    }
}

function Write-UiLog {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Message = "",

        [ValidateSet(
            "SYSTEM",
            "INFO",
            "OUTPUT",
            "SECTION",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "DIAGNOSTIC"
        )]
        [string]$Level = "INFO",

        [AllowNull()]
        [AllowEmptyString()]
        [string]$Timestamp = ""
    )

    try {
        if ($null -eq $Message) {
            $Message = ""
        }

        if ([string]::IsNullOrWhiteSpace($Timestamp)) {
            $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
        }

        $cleanMessage = Remove-AnsiCodes -Text $Message
        $lineColor = Get-LevelColor -Level $Level

        if ([string]::IsNullOrWhiteSpace($cleanMessage)) {
            $formattedLine = ""
        }
        else {
            $formattedLine = "[$Timestamp] [$Level] $cleanMessage"
        }

        if (
            -not $script:isClosing -and
            $null -ne $outputBox -and
            -not $outputBox.IsDisposed
        ) {
            $outputBox.SelectionStart = $outputBox.TextLength
            $outputBox.SelectionLength = 0
            $outputBox.SelectionColor = $lineColor
            $outputBox.AppendText(
                $formattedLine + [Environment]::NewLine
            )
            $outputBox.SelectionColor = $outputBox.ForeColor
            $outputBox.ScrollToCaret()
        }

        Write-Host $formattedLine

        if (-not [string]::IsNullOrWhiteSpace($script:logFile)) {
            Add-Content `
                -LiteralPath $script:logFile `
                -Value $formattedLine `
                -Encoding UTF8 `
                -ErrorAction Stop
        }
    }
    catch [System.Management.Automation.PipelineStoppedException] {
        [KaziTracker.BuildConsole.WinFormsGuardV2]::EmergencyClose()
    }
    catch {
        if (Test-IsPipelineStoppedException -Exception $_.Exception) {
            [KaziTracker.BuildConsole.WinFormsGuardV2]::EmergencyClose()
            return
        }

        try {
            $fallbackTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
            Write-Host (
                "[$fallbackTime] [GUI LOGGING FAILURE] " +
                $_.Exception.Message
            )
        }
        catch {
            # Never recurse back into the UI logger.
        }
    }
}

function Set-UiStatus {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Text = "UNKNOWN",

        [Parameter(Mandatory)]
        [System.Drawing.Color]$Color
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        $Text = "UNKNOWN"
    }

    if (-not $statusLabel.IsDisposed) {
        $statusLabel.Text = "[ $Text ]"
        $statusLabel.ForeColor = $Color
    }
}

function Set-PipelineProgress {
    param(
        [Parameter(Mandatory)]
        [int]$Value
    )

    $safeValue = [Math]::Max(0, [Math]::Min(100, $Value))
    $progressText.Text = "PIPELINE PROGRESS: $safeValue%"

    $newWidth = [Math]::Round(
        $progressTrack.ClientSize.Width * ($safeValue / 100)
    )

    $progressFill.Width = [int]$newWidth

    if ($safeValue -eq 100 -and $script:lastRunSuccessful) {
        $progressFill.BackColor = $colorGreen
    }
    elseif ($safeValue -eq 100) {
        $progressFill.BackColor = $colorRed
    }
    else {
        $progressFill.BackColor = $colorCyan
    }
}

function New-BuildLogFile {
    $logDirectory = Join-Path $projectPath "build-logs"

    try {
        if (
            -not (
                Test-Path `
                    -LiteralPath $logDirectory `
                    -PathType Container
            )
        ) {
            New-Item `
                -ItemType Directory `
                -Path $logDirectory `
                -Force `
                -ErrorAction Stop |
                Out-Null
        }
    }
    catch {
        $logDirectory = Join-Path $env:TEMP "KaziTrackerBuildLogs"

        if (
            -not (
                Test-Path `
                    -LiteralPath $logDirectory `
                    -PathType Container
            )
        ) {
            New-Item `
                -ItemType Directory `
                -Path $logDirectory `
                -Force `
                -ErrorAction Stop |
                Out-Null
        }
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $path = Join-Path $logDirectory "kazi-build_$timestamp.log"

    New-Item `
        -ItemType File `
        -Path $path `
        -Force `
        -ErrorAction Stop |
        Out-Null

    return $path
}

function Stop-BuildJobSafely {
    if ($script:cleanupStarted) {
        return
    }

    $script:cleanupStarted = $true

    try {
        $job = $script:buildJob
        $script:buildJob = $null

        if ($null -eq $job) {
            return
        }

        try {
            if ($job.State -eq "Running") {
                Stop-Job -Job $job -ErrorAction SilentlyContinue
            }
        }
        catch [System.Management.Automation.PipelineStoppedException] {
            # The host is already stopping; native UI shutdown remains available.
        }
        catch {
            try {
                Write-Host "[JOB STOP WARNING] $($_.Exception.Message)"
            }
            catch {
            }
        }

        try {
            Remove-Job `
                -Job $job `
                -Force `
                -ErrorAction SilentlyContinue
        }
        catch [System.Management.Automation.PipelineStoppedException] {
        }
        catch {
            try {
                Write-Host "[JOB CLEANUP WARNING] $($_.Exception.Message)"
            }
            catch {
            }
        }
    }
    finally {
        $script:cleanupStarted = $false
    }
}

function Invoke-SafeUiAction {
    param(
        [Parameter(Mandatory)]
        [string]$HandlerName,

        [Parameter(Mandatory)]
        [scriptblock]$Action,

        [switch]$CloseOnFailure
    )

    try {
        & $Action
    }
    catch [System.Management.Automation.PipelineStoppedException] {
        [KaziTracker.BuildConsole.WinFormsGuardV2]::EmergencyClose()
    }
    catch {
        if (Test-IsPipelineStoppedException -Exception $_.Exception) {
            [KaziTracker.BuildConsole.WinFormsGuardV2]::EmergencyClose()
            return
        }

        try {
            Write-UiLog `
                -Level "ERROR" `
                -Message "$HandlerName encountered an unexpected error."

            Write-UiLog `
                -Level "ERROR" `
                -Message "Exception type: $($_.Exception.GetType().FullName)"

            Write-UiLog `
                -Level "ERROR" `
                -Message "Exception message: $($_.Exception.Message)"

            if ($_.ScriptStackTrace) {
                Write-UiLog `
                    -Level "DIAGNOSTIC" `
                    -Message "Stack trace: $($_.ScriptStackTrace)"
            }
        }
        catch {
        }

        if ($CloseOnFailure) {
            [KaziTracker.BuildConsole.WinFormsGuardV2]::EmergencyClose()
        }
    }
}

# ============================================================================
# BACKGROUND JOB OUTPUT PROCESSING
# ============================================================================

function Process-JobRecords {
    param(
        [AllowNull()]
        [object[]]$Records
    )

    foreach ($record in @($Records)) {
        if ($null -eq $record) {
            continue
        }

        try {
            if ($null -eq $record.PSObject.Properties["EventType"]) {
                Write-UiLog -Level "OUTPUT" -Message ([string]$record)
                continue
            }

            $eventType = [string]$record.EventType
            $message = if ($null -eq $record.Message) {
                ""
            }
            else {
                [string]$record.Message
            }

            $timestamp = if (
                [string]::IsNullOrWhiteSpace([string]$record.Timestamp)
            ) {
                Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
            }
            else {
                [string]$record.Timestamp
            }

            $parsedProgress = -1

            if (
                [int]::TryParse(
                    [string]$record.Progress,
                    [ref]$parsedProgress
                ) -and
                $parsedProgress -ge 0
            ) {
                Set-PipelineProgress -Value $parsedProgress
            }

            switch ($eventType.ToUpperInvariant()) {
                "STATUS" {
                    Set-UiStatus -Text $message -Color $colorCyan
                }
                "SYSTEM" {
                    Write-UiLog `
                        -Message $message `
                        -Level "SYSTEM" `
                        -Timestamp $timestamp
                }
                "INFO" {
                    Write-UiLog `
                        -Message $message `
                        -Level "INFO" `
                        -Timestamp $timestamp
                }
                "OUTPUT" {
                    Write-UiLog `
                        -Message $message `
                        -Level "OUTPUT" `
                        -Timestamp $timestamp
                }
                "SECTION" {
                    Write-UiLog `
                        -Message $message `
                        -Level "SECTION" `
                        -Timestamp $timestamp
                }
                "SUCCESS" {
                    Write-UiLog `
                        -Message $message `
                        -Level "SUCCESS" `
                        -Timestamp $timestamp
                }
                "WARNING" {
                    Write-UiLog `
                        -Message $message `
                        -Level "WARNING" `
                        -Timestamp $timestamp
                }
                "ERROR" {
                    Write-UiLog `
                        -Message $message `
                        -Level "ERROR" `
                        -Timestamp $timestamp
                }
                "DIAGNOSTIC" {
                    Write-UiLog `
                        -Message $message `
                        -Level "DIAGNOSTIC" `
                        -Timestamp $timestamp
                }
                "FINAL" {
                    $script:finalEventReceived = $true
                    $success = $false
                    [void][bool]::TryParse(
                        [string]$record.Success,
                        [ref]$success
                    )
                    $script:lastRunSuccessful = $success

                    if ($success) {
                        Set-UiStatus `
                            -Text "BUILD COMPLETE" `
                            -Color $colorGreen

                        Write-UiLog `
                            -Message $message `
                            -Level "SUCCESS" `
                            -Timestamp $timestamp
                    }
                    else {
                        Set-UiStatus `
                            -Text "PIPELINE FAILED" `
                            -Color $colorRed

                        Write-UiLog `
                            -Message $message `
                            -Level "ERROR" `
                            -Timestamp $timestamp
                    }

                    Set-PipelineProgress -Value 100
                }
                default {
                    Write-UiLog `
                        -Level "WARNING" `
                        -Timestamp $timestamp `
                        -Message (
                            "Unknown event type '$eventType'. " +
                            "Original message: $message"
                        )
                }
            }
        }
        catch [System.Management.Automation.PipelineStoppedException] {
            throw
        }
        catch {
            Write-UiLog `
                -Level "ERROR" `
                -Message (
                    "One background output record could not be processed. " +
                    "Monitoring will continue."
                )

            Write-UiLog `
                -Level "ERROR" `
                -Message "Exception type: $($_.Exception.GetType().FullName)"

            Write-UiLog `
                -Level "ERROR" `
                -Message "Exception message: $($_.Exception.Message)"
        }
    }
}

$pollTimer = [System.Windows.Forms.Timer]::new()
$pollTimer.Interval = 150

$pollTimer.Add_Tick({
    Invoke-SafeUiAction `
        -HandlerName "Pipeline monitor" `
        -CloseOnFailure `
        -Action {
            if ($script:isClosing) {
                return
            }

            if ($null -eq $script:buildJob) {
                $pollTimer.Stop()
                return
            }

            try {
                $records = @(
                    Receive-Job `
                        -Job $script:buildJob `
                        -ErrorAction SilentlyContinue
                )

                Process-JobRecords -Records $records

                if ($script:buildJob.State -eq "Running") {
                    return
                }

                $remainingRecords = @(
                    Receive-Job `
                        -Job $script:buildJob `
                        -ErrorAction SilentlyContinue
                )

                Process-JobRecords -Records $remainingRecords
                $pollTimer.Stop()
                $startButton.Enabled = $true
                $openLogButton.Enabled = (
                    -not [string]::IsNullOrWhiteSpace($script:logFile)
                )

                if (-not $script:finalEventReceived) {
                    $script:lastRunSuccessful = $false
                    Set-UiStatus -Text "JOB CRASHED" -Color $colorRed
                    Set-PipelineProgress -Value 100

                    Write-UiLog `
                        -Level "ERROR" `
                        -Message (
                            "The background job ended without returning " +
                            "a FINAL pipeline result."
                        )

                    if ($script:buildJob.ChildJobs.Count -gt 0) {
                        $reason = (
                            $script:buildJob.ChildJobs[0].JobStateInfo.Reason
                        )

                        if ($null -ne $reason) {
                            Write-UiLog `
                                -Level "ERROR" `
                                -Message (
                                    "Background job exception type: " +
                                    $reason.GetType().FullName
                                )

                            Write-UiLog `
                                -Level "ERROR" `
                                -Message (
                                    "Background job exception message: " +
                                    $reason.Message
                                )
                        }
                    }
                }

                Stop-BuildJobSafely
            }
            catch [System.Management.Automation.PipelineStoppedException] {
                throw
            }
            catch {
                if (-not $script:monitorFailureReported) {
                    $script:monitorFailureReported = $true
                    $pollTimer.Stop()
                    $startButton.Enabled = $true
                    $script:lastRunSuccessful = $false

                    Set-UiStatus -Text "MONITOR ERROR" -Color $colorRed
                    Set-PipelineProgress -Value 100

                    Write-UiLog `
                        -Level "ERROR" `
                        -Message (
                            "The GUI could not continue monitoring the " +
                            "background pipeline."
                        )

                    Write-UiLog `
                        -Level "ERROR" `
                        -Message (
                            "Monitoring exception type: " +
                            $_.Exception.GetType().FullName
                        )

                    Write-UiLog `
                        -Level "ERROR" `
                        -Message (
                            "Monitoring exception message: " +
                            $_.Exception.Message
                        )
                }

                Stop-BuildJobSafely
            }
        }
})

# ============================================================================
# START PIPELINE
# ============================================================================

$startButton.Add_Click({
    Invoke-SafeUiAction `
        -HandlerName "Start pipeline handler" `
        -Action {
            if (
                $null -ne $script:buildJob -and
                $script:buildJob.State -eq "Running"
            ) {
                Write-UiLog `
                    -Level "WARNING" `
                    -Message "A lint/build pipeline is already running."
                return
            }

            $outputBox.Clear()
            $script:lastRunSuccessful = $false
            $script:finalEventReceived = $false
            $script:monitorFailureReported = $false
            $script:logFile = New-BuildLogFile

            [KaziTracker.BuildConsole.WinFormsGuardV2]::SetEmergencyLogPath(
                $script:logFile
            )

            $startButton.Enabled = $false
            $openLogButton.Enabled = $true
            Set-PipelineProgress -Value 0
            Set-UiStatus -Text "INITIALIZING" -Color $colorCyan

            Write-UiLog `
                -Level "SYSTEM" `
                -Message "Kazi Tracker automated pipeline initialized."

            Write-UiLog `
                -Level "INFO" `
                -Message "Project directory: $projectPath"

            Write-UiLog `
                -Level "INFO" `
                -Message "Full diagnostic log: $script:logFile"

            Write-UiLog `
                -Level "INFO" `
                -Message (
                    "The pipeline will lint, build, then deploy Firebase " +
                    "Hosting."
                )

            try {
                $script:buildJob = Start-Job `
                    -ArgumentList $projectPath `
                    -ErrorAction Stop `
                    -ScriptBlock {
                        param(
                            [Parameter(Mandatory)]
                            [string]$ProjectPath
                        )

                        $ErrorActionPreference = "Stop"
                        $PSNativeCommandUseErrorActionPreference = $false
                        $npmPath = $null
                        $nodePath = $null
                        $firebasePath = $null

                        function Emit {
                            param(
                                [Parameter(Mandatory)]
                                [ValidateSet(
                                    "STATUS",
                                    "SYSTEM",
                                    "INFO",
                                    "OUTPUT",
                                    "SECTION",
                                    "SUCCESS",
                                    "WARNING",
                                    "ERROR",
                                    "DIAGNOSTIC",
                                    "FINAL"
                                )]
                                [string]$EventType,

                                [AllowNull()]
                                [AllowEmptyString()]
                                [string]$Message = "",

                                [int]$Progress = -1,

                                [AllowNull()]
                                $Success = $null
                            )

                            if ($null -eq $Message) {
                                $Message = ""
                            }

                            [PSCustomObject]@{
                                EventType = $EventType
                                Message = $Message
                                Progress = $Progress
                                Success = $Success
                                Timestamp = (
                                    Get-Date -Format (
                                        "yyyy-MM-dd HH:mm:ss.fff"
                                    )
                                )
                            } | Write-Output
                        }

                        function Emit-SystemDiagnostics {
                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message (
                                    "========== SYSTEM DIAGNOSTICS =========="
                                )

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message (
                                    "Operating system: " +
                                    [Environment]::OSVersion.VersionString
                                )

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message (
                                    "Machine name: " +
                                    [Environment]::MachineName
                                )

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message (
                                    "PowerShell: " +
                                    $PSVersionTable.PSVersion +
                                    " (" +
                                    $PSVersionTable.PSEdition +
                                    ")"
                                )

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message "Working directory: $(Get-Location)"

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message "Node executable: $nodePath"

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message "npm executable: $npmPath"

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message (
                                    "Firebase executable: $firebasePath"
                                )

                            if ($nodePath) {
                                try {
                                    $nodeVersion = (
                                        & $nodePath --version 2>&1 |
                                        Out-String
                                    ).Trim()

                                    Emit `
                                        -EventType "DIAGNOSTIC" `
                                        -Message (
                                            "Node.js version: $nodeVersion"
                                        )
                                }
                                catch {
                                    Emit `
                                        -EventType "WARNING" `
                                        -Message (
                                            "Could not read the Node.js " +
                                            "version: " +
                                            $_.Exception.Message
                                        )
                                }
                            }

                            if ($npmPath) {
                                try {
                                    $npmVersion = (
                                        & $npmPath --version 2>&1 |
                                        Out-String
                                    ).Trim()

                                    Emit `
                                        -EventType "DIAGNOSTIC" `
                                        -Message "npm version: $npmVersion"
                                }
                                catch {
                                    Emit `
                                        -EventType "WARNING" `
                                        -Message (
                                            "Could not read the npm version: " +
                                            $_.Exception.Message
                                        )
                                }
                            }

                            if ($firebasePath) {
                                try {
                                    $firebaseVersion = (
                                        & $firebasePath --version 2>&1 |
                                        Out-String
                                    ).Trim()

                                    Emit `
                                        -EventType "DIAGNOSTIC" `
                                        -Message (
                                            "Firebase CLI version: " +
                                            $firebaseVersion
                                        )
                                }
                                catch {
                                    Emit `
                                        -EventType "WARNING" `
                                        -Message (
                                            "Could not read the Firebase " +
                                            "CLI version: " +
                                            $_.Exception.Message
                                        )
                                }
                            }

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message (
                                    "package.json exists: " +
                                    (
                                        Test-Path `
                                            -LiteralPath ".\package.json" `
                                            -PathType Leaf
                                    )
                                )

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message (
                                    "node_modules exists: " +
                                    (
                                        Test-Path `
                                            -LiteralPath ".\node_modules" `
                                            -PathType Container
                                    )
                                )

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message (
                                    "========================================"
                                )
                        }

                        function Emit-LatestNpmLog {
                            if (-not $npmPath) {
                                return
                            }

                            try {
                                $cachePath = (
                                    & $npmPath config get cache 2>&1 |
                                    Out-String
                                ).Trim()

                                if (
                                    [string]::IsNullOrWhiteSpace($cachePath)
                                ) {
                                    Emit `
                                        -EventType "WARNING" `
                                        -Message (
                                            "npm did not report a cache path."
                                        )
                                    return
                                }

                                $npmLogDirectory = Join-Path `
                                    $cachePath `
                                    "_logs"

                                Emit `
                                    -EventType "DIAGNOSTIC" `
                                    -Message (
                                        "npm log directory: " +
                                        $npmLogDirectory
                                    )

                                if (
                                    -not (
                                        Test-Path `
                                            -LiteralPath $npmLogDirectory `
                                            -PathType Container
                                    )
                                ) {
                                    Emit `
                                        -EventType "WARNING" `
                                        -Message (
                                            "No npm log directory was found."
                                        )
                                    return
                                }

                                $latestLog = Get-ChildItem `
                                    -LiteralPath $npmLogDirectory `
                                    -File `
                                    -ErrorAction SilentlyContinue |
                                    Sort-Object LastWriteTime -Descending |
                                    Select-Object -First 1

                                if ($null -eq $latestLog) {
                                    Emit `
                                        -EventType "WARNING" `
                                        -Message "No npm debug log was found."
                                    return
                                }

                                Emit `
                                    -EventType "DIAGNOSTIC" `
                                    -Message (
                                        "Latest npm log: " +
                                        $latestLog.FullName
                                    )

                                Get-Content `
                                    -LiteralPath $latestLog.FullName `
                                    -Tail 35 `
                                    -ErrorAction Stop |
                                    ForEach-Object {
                                        $safeLine = (
                                            [string]$_ -replace (
                                                "(?i)(authorization|" +
                                                "password|token|secret)" +
                                                "\s*[=:]\s*\S+"
                                            ), '$1=<REDACTED>'
                                        )

                                        Emit `
                                            -EventType "DIAGNOSTIC" `
                                            -Message "NPM-LOG > $safeLine"
                                    }
                            }
                            catch {
                                Emit `
                                    -EventType "WARNING" `
                                    -Message (
                                        "Unable to read the latest npm log: " +
                                        $_.Exception.Message
                                    )
                            }
                        }

                        function Invoke-ExternalStep {
                            param(
                                [Parameter(Mandatory)]
                                [string]$Name,

                                [Parameter(Mandatory)]
                                [string]$DisplayedCommand,

                                [Parameter(Mandatory)]
                                [string]$ExecutablePath,

                                [Parameter(Mandatory)]
                                [string[]]$Arguments,

                                [Parameter(Mandatory)]
                                [int]$StartProgress,

                                [Parameter(Mandatory)]
                                [int]$EndProgress
                            )

                            Emit -EventType "SECTION" -Message ""
                            Emit `
                                -EventType "SECTION" `
                                -Message (
                                    "========================================" +
                                    "========"
                                )
                            Emit `
                                -EventType "SECTION" `
                                -Message "STARTING: $Name"
                            Emit `
                                -EventType "SECTION" `
                                -Message "COMMAND: $DisplayedCommand"
                            Emit `
                                -EventType "SECTION" `
                                -Message "DIRECTORY: $(Get-Location)"
                            Emit `
                                -EventType "SECTION" `
                                -Message (
                                    "========================================" +
                                    "========"
                                )
                            Emit `
                                -EventType "STATUS" `
                                -Message $Name `
                                -Progress $StartProgress

                            $startedAt = Get-Date
                            $exitCode = $null

                            try {
                                & $ExecutablePath @Arguments 2>&1 |
                                    ForEach-Object {
                                        $line = [string]$_

                                        if (
                                            -not (
                                                [string]::IsNullOrWhiteSpace(
                                                    $line
                                                )
                                            )
                                        ) {
                                            Emit `
                                                -EventType "OUTPUT" `
                                                -Message $line
                                        }
                                    }

                                $exitCode = $LASTEXITCODE
                            }
                            catch {
                                Emit `
                                    -EventType "ERROR" `
                                    -Message "$Name could not be started."
                                Emit `
                                    -EventType "ERROR" `
                                    -Message (
                                        "Exception type: " +
                                        $_.Exception.GetType().FullName
                                    )
                                Emit `
                                    -EventType "ERROR" `
                                    -Message (
                                        "Exception message: " +
                                        $_.Exception.Message
                                    )
                                throw
                            }

                            $seconds = (
                                (Get-Date) - $startedAt
                            ).TotalSeconds

                            Emit `
                                -EventType "INFO" `
                                -Message (
                                    "{0} duration: {1:N2} seconds" -f
                                    $Name,
                                    $seconds
                                )

                            Emit `
                                -EventType "INFO" `
                                -Message "$Name exit code: $exitCode"

                            if ($null -eq $exitCode) {
                                throw [System.InvalidOperationException]::new(
                                    "$Name did not return an exit code."
                                )
                            }

                            if ($exitCode -ne 0) {
                                Emit `
                                    -EventType "ERROR" `
                                    -Message "$Name FAILED."
                                Emit `
                                    -EventType "ERROR" `
                                    -Message "Command: $DisplayedCommand"
                                Emit `
                                    -EventType "ERROR" `
                                    -Message (
                                        "Working directory: " +
                                        "$(Get-Location)"
                                    )
                                Emit `
                                    -EventType "ERROR" `
                                    -Message "Command exit code: $exitCode"
                                Emit `
                                    -EventType "ERROR" `
                                    -Message (
                                        "Review the preceding command output " +
                                        "for the exact failure details."
                                    )

                                throw [System.Exception]::new(
                                    "$Name failed with command exit code " +
                                    "$exitCode."
                                )
                            }

                            Emit `
                                -EventType "SUCCESS" `
                                -Message "$Name completed successfully."
                            Emit `
                                -EventType "STATUS" `
                                -Message "$Name COMPLETE" `
                                -Progress $EndProgress
                        }

                        try {
                            Emit `
                                -EventType "STATUS" `
                                -Message "VALIDATING ENVIRONMENT" `
                                -Progress 5

                            Emit `
                                -EventType "SYSTEM" `
                                -Message (
                                    "Beginning Kazi Tracker pipeline " +
                                    "validation."
                                )

                            Emit `
                                -EventType "INFO" `
                                -Message (
                                    "Expected project path: $ProjectPath"
                                )

                            if (
                                -not (
                                    Test-Path `
                                        -LiteralPath $ProjectPath `
                                        -PathType Container
                                )
                            ) {
                                throw [System.IO.DirectoryNotFoundException]::new(
                                    "Project directory not found: " +
                                    $ProjectPath
                                )
                            }

                            Emit `
                                -EventType "INFO" `
                                -Message (
                                    "Changing directory using: " +
                                    "cd C:\Users\kirwa\Documents\coding\" +
                                    "codeScripts\kazi-tracker"
                                )

                            Set-Location -LiteralPath $ProjectPath

                            Emit `
                                -EventType "SUCCESS" `
                                -Message (
                                    "Successfully entered the project " +
                                    "directory."
                                )

                            Emit `
                                -EventType "INFO" `
                                -Message (
                                    "Resolved working directory: " +
                                    "$(Get-Location)"
                                )

                            Emit `
                                -EventType "STATUS" `
                                -Message "CHECKING TOOLCHAIN" `
                                -Progress 10

                            $npmCommand = Get-Command `
                                -Name "npm.cmd" `
                                -ErrorAction SilentlyContinue

                            if ($null -eq $npmCommand) {
                                $npmCommand = Get-Command `
                                    -Name "npm" `
                                    -ErrorAction SilentlyContinue
                            }

                            if ($null -eq $npmCommand) {
                                throw [System.Management.Automation.CommandNotFoundException]::new(
                                    "npm was not found. Install Node.js and " +
                                    "ensure npm is available in PATH."
                                )
                            }

                            $nodeCommand = Get-Command `
                                -Name "node.exe" `
                                -ErrorAction SilentlyContinue

                            if ($null -eq $nodeCommand) {
                                $nodeCommand = Get-Command `
                                    -Name "node" `
                                    -ErrorAction SilentlyContinue
                            }

                            if ($null -eq $nodeCommand) {
                                throw [System.Management.Automation.CommandNotFoundException]::new(
                                    "Node.js was not found in PATH."
                                )
                            }

                            $npmPath = if ($npmCommand.Source) {
                                $npmCommand.Source
                            }
                            else {
                                $npmCommand.Path
                            }

                            $nodePath = if ($nodeCommand.Source) {
                                $nodeCommand.Source
                            }
                            else {
                                $nodeCommand.Path
                            }

                            $firebaseCommand = Get-Command `
                                -Name "firebase.cmd" `
                                -ErrorAction SilentlyContinue

                            if ($null -eq $firebaseCommand) {
                                $firebaseCommand = Get-Command `
                                    -Name "firebase" `
                                    -ErrorAction SilentlyContinue
                            }

                            if ($null -eq $firebaseCommand) {
                                throw [System.Management.Automation.CommandNotFoundException]::new(
                                    "Firebase CLI was not found. Install it " +
                                    "with 'npm install -g firebase-tools', " +
                                    "then authenticate with 'firebase login'."
                                )
                            }

                            $firebasePath = if ($firebaseCommand.Source) {
                                $firebaseCommand.Source
                            }
                            else {
                                $firebaseCommand.Path
                            }

                            Emit-SystemDiagnostics

                            if (
                                -not (
                                    Test-Path `
                                        -LiteralPath ".\package.json" `
                                        -PathType Leaf
                                )
                            ) {
                                throw [System.IO.FileNotFoundException]::new(
                                    "package.json was not found in " +
                                    "$(Get-Location)."
                                )
                            }

                            $packageJsonText = Get-Content `
                                -LiteralPath ".\package.json" `
                                -Raw `
                                -ErrorAction Stop

                            $packageJson = $packageJsonText |
                                ConvertFrom-Json -ErrorAction Stop

                            Emit `
                                -EventType "INFO" `
                                -Message "Package name: $($packageJson.name)"

                            Emit `
                                -EventType "INFO" `
                                -Message (
                                    "Package version: " +
                                    "$($packageJson.version)"
                                )

                            if ($null -eq $packageJson.scripts) {
                                throw [System.InvalidOperationException]::new(
                                    "package.json does not contain a " +
                                    "scripts object."
                                )
                            }

                            $scripts = @(
                                $packageJson.scripts.PSObject.Properties.Name
                            )

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message (
                                    "Available npm scripts: " +
                                    ($scripts -join ", ")
                                )

                            if ("lint" -notin $scripts) {
                                throw [System.InvalidOperationException]::new(
                                    "package.json does not contain a lint " +
                                    "script."
                                )
                            }

                            if ("build" -notin $scripts) {
                                throw [System.InvalidOperationException]::new(
                                    "package.json does not contain a build " +
                                    "script."
                                )
                            }

                            Invoke-ExternalStep `
                                -Name "LINT VALIDATION" `
                                -DisplayedCommand "npm run lint" `
                                -ExecutablePath $npmPath `
                                -Arguments @("run", "lint") `
                                -StartProgress 20 `
                                -EndProgress 45

                            Invoke-ExternalStep `
                                -Name "PRODUCTION BUILD" `
                                -DisplayedCommand "npm run build" `
                                -ExecutablePath $npmPath `
                                -Arguments @("run", "build") `
                                -StartProgress 50 `
                                -EndProgress 75

                            Invoke-ExternalStep `
                                -Name "FIREBASE HOSTING DEPLOYMENT" `
                                -DisplayedCommand (
                                    "firebase deploy --only hosting"
                                ) `
                                -ExecutablePath $firebasePath `
                                -Arguments @(
                                    "deploy",
                                    "--only",
                                    "hosting"
                                ) `
                                -StartProgress 80 `
                                -EndProgress 95

                            Emit -EventType "SECTION" -Message ""
                            Emit `
                                -EventType "SUCCESS" `
                                -Message (
                                    "========================================" +
                                    "========"
                                )
                            Emit `
                                -EventType "SUCCESS" `
                                -Message (
                                    "KAZI TRACKER PIPELINE COMPLETED " +
                                    "SUCCESSFULLY"
                                )
                            Emit `
                                -EventType "SUCCESS" `
                                -Message "LINT STATUS: PASSED"
                            Emit `
                                -EventType "SUCCESS" `
                                -Message "BUILD STATUS: PASSED"
                            Emit `
                                -EventType "SUCCESS" `
                                -Message "HOSTING DEPLOY STATUS: PASSED"
                            Emit `
                                -EventType "SUCCESS" `
                                -Message (
                                    "========================================" +
                                    "========"
                                )
                            Emit `
                                -EventType "FINAL" `
                                -Message (
                                    "Lint validation, production build, and " +
                                    "Firebase Hosting deployment completed " +
                                    "successfully."
                                ) `
                                -Progress 100 `
                                -Success $true
                        }
                        catch {
                            Emit -EventType "ERROR" -Message ""
                            Emit `
                                -EventType "ERROR" `
                                -Message (
                                    "########################################" +
                                    "########"
                                )
                            Emit `
                                -EventType "ERROR" `
                                -Message (
                                    "KAZI TRACKER PIPELINE TERMINATED " +
                                    "WITH AN ERROR"
                                )
                            Emit `
                                -EventType "ERROR" `
                                -Message (
                                    "########################################" +
                                    "########"
                                )
                            Emit `
                                -EventType "ERROR" `
                                -Message (
                                    "Exception type: " +
                                    $_.Exception.GetType().FullName
                                )
                            Emit `
                                -EventType "ERROR" `
                                -Message (
                                    "Exception message: " +
                                    $_.Exception.Message
                                )
                            Emit `
                                -EventType "ERROR" `
                                -Message (
                                    "PowerShell category: " +
                                    $_.CategoryInfo.Category
                                )
                            Emit `
                                -EventType "ERROR" `
                                -Message (
                                    "Fully qualified error ID: " +
                                    $_.FullyQualifiedErrorId
                                )

                            if ($_.InvocationInfo) {
                                Emit `
                                    -EventType "DIAGNOSTIC" `
                                    -Message (
                                        "Failed command: " +
                                        $_.InvocationInfo.MyCommand
                                    )
                                Emit `
                                    -EventType "DIAGNOSTIC" `
                                    -Message (
                                        "Worker line: " +
                                        $_.InvocationInfo.ScriptLineNumber
                                    )
                                Emit `
                                    -EventType "DIAGNOSTIC" `
                                    -Message (
                                        "Position: " +
                                        $_.InvocationInfo.PositionMessage
                                    )
                            }

                            if ($_.ScriptStackTrace) {
                                Emit `
                                    -EventType "DIAGNOSTIC" `
                                    -Message (
                                        "PowerShell stack trace: " +
                                        $_.ScriptStackTrace
                                    )
                            }

                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message (
                                    "Current directory: $(Get-Location)"
                                )
                            Emit `
                                -EventType "DIAGNOSTIC" `
                                -Message "Project path: $ProjectPath"

                            Emit-SystemDiagnostics
                            Emit-LatestNpmLog

                            Emit `
                                -EventType "FINAL" `
                                -Message (
                                    "The lint/build/deploy pipeline failed. " +
                                    "Review the detailed diagnostics above."
                                ) `
                                -Progress 100 `
                                -Success $false
                        }
                    }

                $pollTimer.Start()
            }
            catch {
                $startButton.Enabled = $true
                $script:lastRunSuccessful = $false
                Set-UiStatus -Text "STARTUP ERROR" -Color $colorRed
                Set-PipelineProgress -Value 100

                Write-UiLog `
                    -Level "ERROR" `
                    -Message (
                        "The background build process could not be started."
                    )

                Write-UiLog `
                    -Level "ERROR" `
                    -Message (
                        "Startup exception type: " +
                        $_.Exception.GetType().FullName
                    )

                Write-UiLog `
                    -Level "ERROR" `
                    -Message (
                        "Startup exception message: " +
                        $_.Exception.Message
                    )
            }
        }
})

# ============================================================================
# OPEN LOG AND CLEAR
# ============================================================================

$openLogButton.Add_Click({
    Invoke-SafeUiAction `
        -HandlerName "Open log handler" `
        -Action {
            if (
                [string]::IsNullOrWhiteSpace($script:logFile) -or
                -not (
                    Test-Path `
                        -LiteralPath $script:logFile `
                        -PathType Leaf
                )
            ) {
                [void][System.Windows.Forms.MessageBox]::Show(
                    "No diagnostic log is currently available.",
                    "Kazi Tracker Build Console",
                    [System.Windows.Forms.MessageBoxButtons]::OK,
                    [System.Windows.Forms.MessageBoxIcon]::Information
                )
                return
            }

            Start-Process `
                -FilePath "notepad.exe" `
                -ArgumentList @($script:logFile) `
                -ErrorAction Stop
        }
})

$clearButton.Add_Click({
    Invoke-SafeUiAction `
        -HandlerName "Clear console handler" `
        -Action {
            $outputBox.Clear()
            Write-UiLog `
                -Level "SYSTEM" `
                -Message "Console output cleared by the user."
        }
})

# ============================================================================
# SAFE WINDOW CLOSING AND FINAL CLEANUP
# ============================================================================

$form.Add_FormClosing({
    param(
        $sender,
        [System.Windows.Forms.FormClosingEventArgs]$eventArgs
    )

    try {
        if ($script:isClosing) {
            $eventArgs.Cancel = $false
            return
        }

        if (
            $null -ne $script:buildJob -and
            $script:buildJob.State -eq "Running"
        ) {
            $answer = [System.Windows.Forms.MessageBox]::Show(
                (
                    "A lint/build pipeline is still running." +
                    [Environment]::NewLine +
                    [Environment]::NewLine +
                    "Stop the pipeline and close the window?"
                ),
                "Pipeline Still Running",
                [System.Windows.Forms.MessageBoxButtons]::YesNo,
                [System.Windows.Forms.MessageBoxIcon]::Warning
            )

            if ($answer -eq [System.Windows.Forms.DialogResult]::No) {
                $eventArgs.Cancel = $true
                return
            }
        }

        # Once closing begins, cleanup errors must never cancel the close.
        $script:isClosing = $true
        $eventArgs.Cancel = $false

        try {
            $pollTimer.Stop()
        }
        catch {
        }

        Stop-BuildJobSafely
    }
    catch [System.Management.Automation.PipelineStoppedException] {
        $eventArgs.Cancel = $false
        [KaziTracker.BuildConsole.WinFormsGuardV2]::EmergencyClose()
    }
    catch {
        $eventArgs.Cancel = $false

        if (Test-IsPipelineStoppedException -Exception $_.Exception) {
            [KaziTracker.BuildConsole.WinFormsGuardV2]::EmergencyClose()
            return
        }

        # Never trap the user inside the application because cleanup failed.
        [KaziTracker.BuildConsole.WinFormsGuardV2]::EmergencyClose()
    }
})

$form.Add_FormClosed({
    try {
        $script:isClosing = $true

        try {
            $pollTimer.Stop()
        }
        catch {
        }

        Stop-BuildJobSafely
    }
    catch {
        # The form is already closed; suppress all final cleanup exceptions.
    }
    finally {
        try {
            [System.Windows.Forms.Application]::ExitThread()
        }
        catch {
        }
    }
})

$form.Add_Shown({
    Invoke-SafeUiAction `
        -HandlerName "Initial window handler" `
        -CloseOnFailure `
        -Action {
            $form.Activate()
            Write-UiLog `
                -Level "SYSTEM" `
                -Message "Kazi Tracker Build Console is online."
            Write-UiLog `
                -Level "INFO" `
                -Message (
                    "Press START PIPELINE to lint, build, and deploy " +
                    "Firebase Hosting."
                )
            Write-UiLog `
                -Level "INFO" `
                -Message "Project target: $projectPath"
            Write-UiLog `
                -Level "DIAGNOSTIC" `
                -Message (
                    "Emergency UI log: $emergencyLogPath"
                )
        }
})

# ============================================================================
# SHOW APPLICATION
# ============================================================================

try {
    [void]$form.ShowDialog()
}
catch [System.Management.Automation.PipelineStoppedException] {
    [KaziTracker.BuildConsole.WinFormsGuardV2]::EmergencyClose()
}
catch {
    if (Test-IsPipelineStoppedException -Exception $_.Exception) {
        [KaziTracker.BuildConsole.WinFormsGuardV2]::EmergencyClose()
    }
    else {
        try {
            Add-Content `
                -LiteralPath $emergencyLogPath `
                -Value (
                    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff')] " +
                    "[FATAL STARTUP ERROR] $($_.Exception)"
                ) `
                -Encoding UTF8 `
                -ErrorAction SilentlyContinue
        }
        catch {
        }

        [KaziTracker.BuildConsole.WinFormsGuardV2]::EmergencyClose()
    }
}
finally {
    try {
        $pollTimer.Stop()
    }
    catch {
    }

    try {
        Stop-BuildJobSafely
    }
    catch {
    }

    try {
        if (-not $form.IsDisposed) {
            $form.Dispose()
        }
    }
    catch {
    }
}
