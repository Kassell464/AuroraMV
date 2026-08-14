@echo off
rem AuroraMV launcher - double-click to run (optional args pass through)
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo [AuroraMV] venv not found. Run: python -m venv venv ^&^& venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
venv\Scripts\python.exe main.py %*
if errorlevel 1 pause
