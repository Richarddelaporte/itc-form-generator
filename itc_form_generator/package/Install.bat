@echo off
title ITC Form Generator - Installer
echo.
echo Starting ITC Form Generator Installer...
echo.

:: Run PowerShell installer with execution policy bypass
powershell -ExecutionPolicy Bypass -File "%~dp0Install.ps1"

:: If PowerShell fails, show manual instructions
if errorlevel 1 (
    echo.
    echo ============================================
    echo   Manual Installation Instructions
    echo ============================================
    echo.
    echo 1. Copy ITC_Form_Generator_Web.exe to a folder
    echo 2. Double-click the exe to run the application
    echo 3. Your browser will open automatically
    echo.
    pause
)
