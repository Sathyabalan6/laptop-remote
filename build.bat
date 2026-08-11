@echo off
echo.
echo ========================================
echo   Laptop Remote - EXE Builder
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Installing dependencies...
pip install flask pyautogui pywin32 qrcode pyinstaller pillow flask-socketio simple-websocket --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

:: Clean previous build
echo [2/3] Cleaning previous build...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

:: Build exe
echo [3/3] Building LaptopRemote.exe ...
pyinstaller laptop_remote.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD SUCCESSFUL
echo   Your exe is at: dist\LaptopRemote.exe
echo   Share that single file with anyone!
echo ========================================
echo.
pause
