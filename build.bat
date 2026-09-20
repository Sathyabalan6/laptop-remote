@echo off
echo.
echo ========================================
echo   Laptop Remote - EXE Builder (CLI)
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
pip install -e . pyinstaller --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

:: Clean previous build artifacts
echo [2/3] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: Build
echo [3/3] Building LaptopRemote-CLI.exe (Terminal Edition)...
pyinstaller laptop_remote_cli.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD SUCCESSFUL!
echo   Executable created in: dist\
if exist dist\LaptopRemote-CLI.exe echo    - dist\LaptopRemote-CLI.exe (Terminal / No-GUI)
echo ========================================
echo.
pause
