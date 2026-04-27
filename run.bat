@echo off
REM DeepAgents GUI Launcher for Windows

echo ============================================================
echo   DeepAgents GUI - Multi-Agent System with LangChain
echo ============================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install dependencies if needed
if not exist .deps_installed (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo. > .deps_installed
)

REM Check .env file
if not exist .env (
    echo WARNING: .env file not found
    echo Copy .env.example to .env and add your API key
    echo.
)

REM Run application
echo Starting DeepAgents GUI...
echo.
python app.py

pause
