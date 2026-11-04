@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Estimate Generation System - Python
echo ========================================
echo.
echo Python is starting...
echo.
echo Keep this window open while using the server.
echo.
echo ========================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed.
    echo Download from: https://www.python.org/
    pause
    exit /b 1
)

python --version

if not exist "venv" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo.
echo Installing packages...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install packages.
    pause
    exit /b 1
)

echo.
echo Starting Flask server...
python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Server failed to start.
    pause
    exit /b 1
)
