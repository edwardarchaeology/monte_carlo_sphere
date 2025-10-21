@echo off
REM Windows launcher for 3D Monte Carlo Pi Approximation

echo Starting 3D Monte Carlo Pi Approximation...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Run the application
python main.py

if errorlevel 1 (
    echo.
    echo ERROR: Application exited with an error
    pause
)
