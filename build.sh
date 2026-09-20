#!/usr/bin/env bash
# ==============================================================================
# Laptop Remote · Linux Executable Builder
# ==============================================================================
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "📦 Initializing virtual environment (.venv)..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
fi

echo "[1/3] Ensuring dependencies are installed..."
.venv/bin/pip install -e . pyinstaller --quiet

echo "[2/3] Cleaning previous build artifacts..."
rm -rf build dist

echo "[3/3] Compiling LaptopRemote-CLI standalone executable..."
.venv/bin/pyinstaller laptop_remote_cli.spec --noconfirm

echo ""
echo "=================================================="
echo "  BUILD SUCCESSFUL!"
echo "  Standalone binary created at: dist/LaptopRemote-CLI"
echo "=================================================="
