@echo off
title VoiceMate Laptop Agent
chcp 65001 > nul
echo ========================================================
echo        Starting VoiceMate Laptop Voice Agent...
echo ========================================================
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Launching in CLI mode...
    python main.py --cli
)
pause
