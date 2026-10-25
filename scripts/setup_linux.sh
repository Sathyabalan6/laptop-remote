#!/usr/bin/env bash
# ==============================================================================
# Laptop Remote · Linux One-Time Setup (Wayland mouse support)
# ==============================================================================
# On Linux + Wayland, moving the mouse/typing requires injecting input through
# the kernel's uinput device. This is a Linux security feature: only members of
# the 'input' group (or root) may do this. This script sets that up once.
#
# On Windows, macOS, or Linux/Xorg this is NOT needed — those use native APIs.
#
# Usage:  bash setup_linux.sh
# ==============================================================================
set -e

echo ""
echo "=================================================="
echo "  Laptop Remote · Linux Setup"
echo "=================================================="

# 1) Ensure ydotool is installed (Debian/Ubuntu-family only).
if ! command -v ydotool >/dev/null 2>&1; then
  echo "📦 ydotool is not installed."
  if command -v apt-get >/dev/null 2>&1; then
    echo "   Installing ydotool via apt-get (this needs your password)..."
    sudo apt-get update -y
    sudo apt-get install -y ydotool
  else
    echo "   Please install 'ydotool' with your distro's package manager,"
    echo "   then re-run this script."
    exit 1
  fi
fi

# 2) Add the current user to the 'input' group so ydotool can open /dev/uinput.
if ! id -nG "$USER" | grep -qw input; then
  echo "👤 Adding '$USER' to the 'input' group (one-time)..."
  sudo usermod -aG input "$USER"
  echo ""
  echo "   ⚠️  You must log out and back in (or reboot) for group membership to apply."
  echo "   After re-login, restart Laptop Remote — mouse control will then work."
else
  echo "✅ '$USER' is already in the 'input' group."
fi

echo ""
echo "=================================================="
echo "  Setup complete."
echo "  If you just joined the 'input' group, log out/in first."
echo "  Laptop Remote will auto-start the ydotoold daemon on launch."
echo "=================================================="
echo ""
