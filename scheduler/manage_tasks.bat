@echo off
title Institutional Screener - Windows Task Scheduler Manager
cd /d "%~dp0"
echo ===================================================
echo  INSTITUTIONAL SCREENER - TASK SCHEDULER MANAGER
echo ===================================================
echo.
echo 1. Register All Scheduled Tasks (PreMarket, Opening, MidDay, EOD, PostMarket + Daemon)
echo 2. Check Status of Registered Tasks
echo 3. Unregister All Tasks
echo 4. Exit
echo.
set /p choice="Select option (1-4): "

if "%choice%"=="1" (
    powershell -ExecutionPolicy Bypass -File "%~dp0register_windows_tasks.ps1" -Action Register
    pause
) else if "%choice%"=="2" (
    powershell -ExecutionPolicy Bypass -File "%~dp0register_windows_tasks.ps1" -Action Status
    pause
) else if "%choice%"=="3" (
    powershell -ExecutionPolicy Bypass -File "%~dp0register_windows_tasks.ps1" -Action Unregister
    pause
) else (
    exit /b
)
