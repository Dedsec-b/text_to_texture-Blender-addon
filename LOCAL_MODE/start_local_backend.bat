@echo off
REM ============================================================================
REM AI Texture Generator - Start Local Backend
REM Starts the local backend server
REM ============================================================================

echo.
echo ====================================================================
echo    AI Texture Generator - Local Backend
echo ====================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if not %errorLevel% == 0 (
    echo [ERROR] Python is not installed!
    echo Please run "install.bat" first
    echo.
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import torch" >nul 2>&1
if not %errorLevel% == 0 (
    echo [ERROR] Required packages not installed!
    echo Please run "install.bat" first
    echo.
    pause
    exit /b 1
)

echo Starting local backend server...
echo.
echo Tips:
echo   - First run will download AI model (4GB, 10-15 min)
echo   - Keep this window open while using Blender
echo   - Press Ctrl+C to stop the server
echo.
echo ====================================================================
echo.

REM Start the backend
python local_backend.py

pause
