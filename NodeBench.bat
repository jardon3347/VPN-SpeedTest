@echo off
title NodeBench - CLI
cd /d "%~dp0"

:: Find Python
set PYTHON=
where python >nul 2>&1 && set PYTHON=python
if "%PYTHON%"=="" (
    echo [ERROR] Python not found in PATH.
    echo Please install Python 3.9+ and add to PATH.
    pause
    exit /b 1
)

echo ============================================================
echo   NodeBench - CLI Launcher
echo ============================================================
echo.
echo   1. Interactive Menu
echo   2. Stage 1 (Latency)
echo   3. Stage 2 (Bandwidth)
echo   4. Full Test (Stage 1 + 2)
echo   5. GUI Mode
echo   6. Demo (Self-test)
echo   0. Exit
echo.

set /p CHOICE="   Choice: "

if "%CHOICE%"=="1" goto menu
if "%CHOICE%"=="2" goto stage1
if "%CHOICE%"=="3" goto stage2
if "%CHOICE%"=="4" goto full
if "%CHOICE%"=="5" goto gui
if "%CHOICE%"=="6" goto demo
goto end

:menu
%PYTHON% menu.py
pause
goto end

:stage1
%PYTHON% main.py --stage 1 --save-cache cache.json
pause
goto end

:stage2
%PYTHON% main.py --stage 2 --load-cache cache.json
pause
goto end

:full
%PYTHON% main.py --stage 2
pause
goto end

:gui
start "" pythonw main.py --gui
goto end

:demo
%PYTHON% main.py --demo
pause
goto end

:end
