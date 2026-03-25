# ITC Form Generator - Installer Script
# This script creates a desktop shortcut and optionally copies files to Program Files

param(
    [switch]$CreateShortcut = $true,
    [switch]$InstallToPrograms = $false
)

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExeName = "ITC_Form_Generator_Web.exe"
$ExePath = Join-Path $ScriptDir $ExeName

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ITC Form Generator - Installer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if exe exists
if (-not (Test-Path $ExePath)) {
    Write-Host "ERROR: $ExeName not found in $ScriptDir" -ForegroundColor Red
    Write-Host "Make sure the exe is in the same folder as this script."
    Read-Host "Press Enter to exit"
    exit 1
}

# Create Desktop shortcut
if ($CreateShortcut) {
    Write-Host "Creating desktop shortcut..." -ForegroundColor Yellow

    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = Join-Path $DesktopPath "ITC Form Generator.lnk"

    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = $ExePath
        $Shortcut.WorkingDirectory = $ScriptDir
        $Shortcut.Description = "ITC Form Generator Web Application"
        $Shortcut.Save()

        Write-Host "Desktop shortcut created successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "Could not create shortcut: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "To run the application:"
Write-Host "  - Double-click the desktop shortcut, OR"
Write-Host "  - Double-click $ExeName directly"
Write-Host ""
Write-Host "The app will open your browser to http://localhost:8080"
Write-Host ""

Read-Host "Press Enter to exit"
