#!/usr/bin/env bash
# ==============================================================================
# Laptop Remote · Linux One-Click Launcher
# ==============================================================================
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "📦 Initializing virtual environment (.venv)..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# Make the package importable (src layout) if not already installed.
if ! .venv/bin/python -c "import laptop_remote" 2>/dev/null; then
    .venv/bin/pip install -e . --quiet
fi

# Enable local X11/Xwayland connection access for PyAutoGUI/mouse controls
if command -v xhost >/dev/null 2>&1; then
    xhost +local: >/dev/null 2>&1 || true
fi

# Detect dynamic Xwayland auth if needed
if [ -z "$XAUTHORITY" ] && [ -n "$XDG_RUNTIME_DIR" ]; then
    M_AUTH=$(ls -d "$XDG_RUNTIME_DIR"/.mutter-Xwaylandauth* 2>/dev/null | head -n 1)
    if [ -n "$M_AUTH" ]; then
        export XAUTHORITY="$M_AUTH"
    fi
fi

# ── Wayland mouse support ─────────────────────────────────────────────────────
# On Wayland, mouse injection needs ydotool + membership in the 'input' group.
# This is a one-time requirement (see setup_linux.sh). Auto-start the daemon if
# the user can already access /dev/uinput (i.e. is in the input group).
if [ -n "$WAYLAND_DISPLAY" ] && [ "${XDG_SESSION_TYPE:-}" != "x11" ]; then
  if ! command -v ydotool >/dev/null 2>&1; then
    echo "⚠️  Wayland detected but 'ydotool' is missing. Run: bash setup_linux.sh"
  elif [ ! -w /dev/uinput ] && ! id -nG | grep -qw input; then
    echo "⚠️  You are not in the 'input' group yet. Run once: bash setup_linux.sh"
  elif ! pgrep -x ydotoold >/dev/null 2>&1; then
    echo "🖱️  Starting ydotoold for Wayland mouse control..."
    ydotoold &
  fi
fi

echo "🚀 Starting Laptop Remote on Linux..."
exec .venv/bin/python -m laptop_remote "$@"
