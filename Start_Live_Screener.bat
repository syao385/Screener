@echo off
title Institutional Live Real-Time Screener
cd /d "%~dp0"
echo ===================================================
echo Starting Institutional Real-Time Live Screener...
echo Auto-refreshing dashboard every 60 seconds.
echo Press Ctrl+C in this window to stop.
echo ===================================================
"C:\Users\jfan\AppData\Local\Programs\Python\Python312\python.exe" run_screener.py --realtime
pause
