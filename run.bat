@echo off
:: ═══════════════════════════════════════════════════════════════════
::  WorldForge AI — Windows Setup & Run Script
::  Double-click or run from command prompt
:: ═══════════════════════════════════════════════════════════════════

setlocal EnableDelayedExpansion
set SCRIPT_DIR=%~dp0

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║       ⚔  WorldForge AI  ⚔                ║
echo  ║   AI Smart Story World Generator          ║
echo  ╚═══════════════════════════════════════════╝
echo.

:: Load .env file if it exists
if exist "%SCRIPT_DIR%.env" (
  echo 📄 Loading .env file...
  for /f "usebackq tokens=1,* delims==" %%A in ("%SCRIPT_DIR%.env") do (
    set line=%%A
    if not "!line:~0,1!"=="#" (
      if not "%%A"=="" set %%A=%%B
    )
  )
  echo ✅ Environment variables loaded
)

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
  echo ❌ Python is not installed. Download from https://python.org
  pause
  exit /b 1
)
echo ✅ Python found

:: Create/activate venv
if not exist "%SCRIPT_DIR%venv" (
  echo 📦 Creating virtual environment...
  python -m venv "%SCRIPT_DIR%venv"
)
call "%SCRIPT_DIR%venv\Scripts\activate.bat"
echo ✅ Virtual environment active

:: Install deps
echo 📦 Installing dependencies...
pip install -q -r "%SCRIPT_DIR%backend\requirements.txt"
echo ✅ Dependencies installed

:: Check API key
if "%ANTHROPIC_API_KEY%"=="" (
  echo.
  echo ⚠️  ANTHROPIC_API_KEY not set.
  echo    Option 1: Create a .env file in this folder with:
  echo              ANTHROPIC_API_KEY=sk-ant-your-key-here
  echo    Get a key at: https://console.anthropic.com
  echo.
  set /p ANTHROPIC_API_KEY="   Enter your Anthropic API key (or press Enter to skip): "
)

:: Create database dir
if not exist "%SCRIPT_DIR%database" mkdir "%SCRIPT_DIR%database"

:: Launch
echo.
echo 🚀 Starting WorldForge AI...
echo    Open http://127.0.0.1:5000 in your browser
echo    Press Ctrl+C to stop
echo.

cd "%SCRIPT_DIR%backend"
python app.py
pause
