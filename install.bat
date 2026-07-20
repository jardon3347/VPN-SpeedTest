@echo off
title NodeBench - Install Dependencies
cd /d "%~dp0"
echo.
echo ============================================================
echo   NodeBench - Dependency Installer
echo ============================================================
echo.
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Python not found. Install Python 3.9+ first.
    echo   https://www.python.org/downloads/
    pause
    exit /b 1
)
echo   Python found:
python --version
echo.
echo   Installing dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo   [ERROR] Installation failed.
    pause
    exit /b 1
)
echo.
echo ============================================================
echo   Installation complete! Double-click NodeBench-GUI.exe
echo   Or run: python main.py --help
echo ============================================================
pause
