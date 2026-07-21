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

:menu
cls
echo.
echo ============================================================
echo   NodeBench - CLI Launcher
echo ============================================================
echo.
echo   ¡¾1¡¿Stage 1 (Latency)
echo   ¡¾2¡¿Stage 2 (Bandwidth)
echo   ¡¾3¡¿GUI Mode
echo   ¡¾4¡¿Settings
echo   ¡¾0¡¿Exit
echo.

set /p CHOICE="   Choice: "

if "%CHOICE%"=="1" goto stage1
if "%CHOICE%"=="2" goto stage2
if "%CHOICE%"=="3" goto gui
if "%CHOICE%"=="4" goto settings
if "%CHOICE%"=="0" goto end
echo   Invalid choice, try again.
pause
goto menu

:stage1
cls
echo   Running Stage 1 (Latency)...
echo.
%PYTHON% main.py --stage 1 --save-cache cache.json
echo.
echo   ------------------------------------------------------------
echo   Enter node numbers above to test (e.g. 1,3-5)
echo   or press Enter to skip (use top-N auto selection later).
set /p NODES="   > "
if not "%NODES%"=="" (
    echo.
    echo   Running Stage 2 with selected nodes...
    echo.
    %PYTHON% main.py --stage 2 --load-cache cache.json --nodes "%NODES%"
)
pause
goto menu

:stage2
cls
echo   Running Stage 2 (Bandwidth)...
echo.
%PYTHON% main.py --stage 2 --load-cache cache.json
pause
goto menu

:gui
start "" pythonw main.py --gui
goto menu

:settings
cls
echo.
echo ============================================================
echo   NodeBench - Settings
echo ============================================================
echo.
%PYTHON% menu.py --settings
goto menu

:end
