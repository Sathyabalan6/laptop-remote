@echo off
echo.
echo ========================================
echo   Laptop Remote - Terminal EXE Builder
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
echo [1/3] Checking dependencies...
pip install flask pyautogui pywin32 qrcode pyinstaller pillow flask-socketio simple-websocket zeroconf ifaddr --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

:: Clean previous build artifacts
echo [2/3] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist\LaptopRemote-CLI.exe del /f /q dist\LaptopRemote-CLI.exe

:: Build exe
echo [3/3] Building LaptopRemote-CLI.exe ...
pyinstaller laptop_remote_cli.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD SUCCESSFUL
echo   Your Terminal exe is at: dist\LaptopRemote-CLI.exe
echo   Runs strictly in terminal with PIN / password (no GUI window)!
echo ========================================
echo.
pause
