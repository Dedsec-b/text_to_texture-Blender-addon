@echo off
REM ============================================================================
REM AI Texture Generator - Local Backend Installer
REM Installs Python and all dependencies needed to run locally
REM ============================================================================

echo.
echo ====================================================================
echo    AI Texture Generator - Local Backend Installer
echo ====================================================================
echo.
echo This script will install everything needed to run the local backend:
echo   - Python 3.10 (if not already installed)
echo   - CUDA toolkit for NVIDIA GPUs
echo   - All required Python packages
echo   - AI model (4GB download)
echo.
echo Requirements:
echo   - Windows 10/11
echo   - 10GB free disk space
echo   - Internet connection (for initial setup)
echo   - Optional: NVIDIA GPU with 6GB+ VRAM
echo.
pause

REM ============================================================================
REM Check for Administrator privileges
REM ============================================================================
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrator privileges
) else (
    echo.
    echo [WARNING] Not running as administrator!
    echo Some installations may fail without admin rights.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
)

REM ============================================================================
REM Check if Python is installed
REM ============================================================================
echo.
echo [1/5] Checking Python installation...
echo.

python --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Python is already installed!
    python --version
    
    REM Check Python version
    for /f "tokens=2 delims= " %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo Python version: %PYTHON_VERSION%
    
    REM Check if version is 3.10 or 3.11
    echo %PYTHON_VERSION% | findstr /C:"3.10" >nul
    if %errorLevel% == 0 (
        echo [OK] Python 3.10 detected - compatible!
        goto :skip_python_install
    )
    
    echo %PYTHON_VERSION% | findstr /C:"3.11" >nul
    if %errorLevel% == 0 (
        echo [OK] Python 3.11 detected - compatible!
        goto :skip_python_install
    )
    
    echo.
    echo [WARNING] Python %PYTHON_VERSION% detected
    echo Recommended: Python 3.10 or 3.11
    echo Do you want to continue anyway? (Y/N)
    set /p CONTINUE="Continue? (Y/N): "
    if /i not "%CONTINUE%"=="Y" exit /b
    
    goto :skip_python_install
)

echo [INFO] Python not found. Installing Python 3.10...
echo.

REM Download Python installer
echo Downloading Python 3.10.11 installer...
powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe' -OutFile 'python_installer.exe'}"

if not exist python_installer.exe (
    echo [ERROR] Failed to download Python installer
    echo Please download manually from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing Python 3.10.11...
echo Please check "Add Python to PATH" in the installer!
echo.
start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

REM Clean up installer
del python_installer.exe

REM Refresh environment variables
call refreshenv >nul 2>&1

REM Verify installation
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Python installed successfully!
    python --version
) else (
    echo [ERROR] Python installation failed
    echo Please install manually from: https://www.python.org/downloads/
    pause
    exit /b 1
)

:skip_python_install

REM ============================================================================
REM Check for NVIDIA GPU and CUDA
REM ============================================================================
echo.
echo [2/5] Checking GPU and CUDA...
echo.

nvidia-smi >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] NVIDIA GPU detected!
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    echo.
    echo CUDA will be installed with PyTorch...
) else (
    echo [WARNING] No NVIDIA GPU detected or driver not installed
    echo.
    echo The backend will run on CPU (VERY SLOW - 10-30x slower)
    echo.
    echo Recommendations:
    echo   1. If you have NVIDIA GPU: Install latest driver from nvidia.com
    echo   2. If no GPU: Use Cloud Mode instead (faster and free)
    echo.
    set /p CONTINUE="Continue with CPU mode? (Y/N): "
    if /i not "%CONTINUE%"=="Y" exit /b
)

REM ============================================================================
REM Upgrade pip
REM ============================================================================
echo.
echo [3/5] Upgrading pip...
echo.

python -m pip install --upgrade pip
if %errorLevel% == 0 (
    echo [OK] pip upgraded
) else (
    echo [WARNING] pip upgrade failed, continuing anyway...
)

REM ============================================================================
REM Install PyTorch with CUDA support
REM ============================================================================
echo.
echo [4/5] Installing PyTorch (this may take 5-10 minutes)...
echo.

REM Check if NVIDIA GPU exists for CUDA installation
nvidia-smi >nul 2>&1
if %errorLevel% == 0 (
    echo Installing PyTorch with CUDA 11.8 support...
    python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
) else (
    echo Installing PyTorch (CPU version)...
    python -m pip install torch torchvision torchaudio
)

if %errorLevel% == 0 (
    echo [OK] PyTorch installed
) else (
    echo [ERROR] PyTorch installation failed
    pause
    exit /b 1
)

REM ============================================================================
REM Install remaining dependencies
REM ============================================================================
echo.
echo [5/5] Installing AI libraries (this may take 5-10 minutes)...
echo.

python -m pip install -r requirements_local.txt

if %errorLevel% == 0 (
    echo [OK] All dependencies installed!
) else (
    echo [ERROR] Dependency installation failed
    pause
    exit /b 1
)

REM ============================================================================
REM Installation complete
REM ============================================================================
echo.
echo ====================================================================
echo    Installation Complete!
echo ====================================================================
echo.
echo Next steps:
echo   1. Run "start_local_backend.bat" to start the server
echo   2. Wait for model download (4GB, first time only)
echo   3. Copy URL: http://127.0.0.1:5000
echo   4. Paste into Blender addon "Backend URL" field
echo   5. Generate amazing textures!
echo.
echo Tips:
echo   - First run downloads AI model (10-15 minutes)
echo   - After that, works 100%% offline!
echo   - Keep the backend window open while using Blender
echo   - Press Ctrl+C in backend window to stop
echo.
echo Want to start the backend now? (Y/N)
set /p START_NOW="Start now? (Y/N): "
if /i "%START_NOW%"=="Y" (
    echo.
    echo Starting local backend...
    call start_local_backend.bat
) else (
    echo.
    echo Run "start_local_backend.bat" when you're ready!
)

pause
