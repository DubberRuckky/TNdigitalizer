@echo off
title Intelligent Land Record Digitization & Validation System (SIH 2026)
color 0A
echo ==============================================================================
echo   Intelligent Land Record Digitization and Validation System
echo   Smart India Hackathon (SIH 2026) - GovTech Software Prototype
echo ==============================================================================
echo.
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH! Please install Python 3.10+
    pause
    exit /b 1
)

echo [2/3] Checking dependencies...
python -m pip install -r requirements.txt --quiet

echo [3/3] Launching Web Server on http://localhost:8000 ...
echo.
echo ==============================================================================
echo   APPLICATION IS READY!
echo   * Main Dashboard:     http://localhost:8000
echo   * SIH 2026 Slides:    http://localhost:8000/presentation
echo   * API Documentation:  http://localhost:8000/docs
echo ==============================================================================
echo.
start http://localhost:8000
python run_server.py
pause
