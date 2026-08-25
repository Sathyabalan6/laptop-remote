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
pip install flask pyautogui pywin32 qrcode pyinstaller pillow flask-socketio simple-websocket zeroconf ifaddr --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

:: Prompt build choice
echo.
echo Which executable would you like to build?
echo   [1] GUI Companion App (LaptopRemote.exe)
echo   [2] Terminal Only / No-GUI (LaptopRemote-CLI.exe)
echo   [3] Build Both (LaptopRemote.exe + LaptopRemote-CLI.exe)
echo.
set /p choice="Enter choice (1, 2, or 3) [default: 3]: "
if "%choice%"=="" set choice=3

:: Clean previous build artifacts (both build cache and dist)
echo [2/3] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: Build based on choice
if "%choice%"=="1" (
    echo [3/3] Building LaptopRemote.exe (GUI Edition)...
    pyinstaller laptop_remote.spec --noconfirm
) else if "%choice%"=="2" (
    echo [3/3] Building LaptopRemote-CLI.exe (Terminal Edition)...
    pyinstaller laptop_remote_cli.spec --noconfirm
) else (
    echo [3/3] Building BOTH LaptopRemote.exe and LaptopRemote-CLI.exe...
    pyinstaller laptop_remote.spec --noconfirm
    pyinstaller laptop_remote_cli.spec --noconfirm
)

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD SUCCESSFUL!
echo   Executables created in: dist\
if exist dist\LaptopRemote.exe echo    - dist\LaptopRemote.exe (GUI Companion)
if exist dist\LaptopRemote-CLI.exe echo    - dist\LaptopRemote-CLI.exe (Terminal / No-GUI)
echo ========================================
echo.
pause

