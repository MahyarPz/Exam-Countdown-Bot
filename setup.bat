@echo off
echo ========================================
echo Exam Countdown Bot - Quick Setup
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Make sure Python 3.11+ is installed
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo [1/4] Virtual environment already exists
)

echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed

echo.
echo [4/4] Checking configuration...
if not exist ".env" (
    echo WARNING: .env file not found!
    echo.
    echo Please:
    echo 1. Get bot token from https://t.me/BotFather
    echo 2. Open .env file and add your BOT_TOKEN
    echo.
    pause
) else (
    echo ✓ .env file exists
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run the bot:
echo   1. Edit .env and add your BOT_TOKEN
echo   2. Run: python -m app.main
echo.
echo For testing with fast notifications (60s):
echo   - Uncomment DEBUG_FAST_SCHEDULE=1 in .env
echo.
pause
