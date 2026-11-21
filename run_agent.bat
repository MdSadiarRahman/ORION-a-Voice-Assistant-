@echo off
title VoiceMate Laptop Agent (ORION)
chcp 65001 > nul
cd /d "%~dp0"
set "PYTHONPATH=%~dp0"

echo ========================================================
echo        Starting VoiceMate Laptop Voice Agent (ORION)...
echo ========================================================

REM Find Python executable
set "PY_EXE="
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PY_EXE=py"
    ) else (
        where python >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            set "PY_EXE=python"
        )
    )
)

if "%PY_EXE%"=="" (
    echo [ERROR] Python not found on system!
    echo Please make sure Python 3.10+ is installed.
    pause
    exit /b 1
)

echo Using Python: %PY_EXE%
echo Starting GUI...
"%PY_EXE%" main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo GUI closed or not available. Launching in Terminal CLI mode...
    "%PY_EXE%" main.py --cli
)
pause
