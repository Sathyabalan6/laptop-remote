# 📱 Laptop Remote

[![CI](https://github.com/Sathyabalan6/laptop-remote/actions/workflows/ci.yml/badge.svg)](https://github.com/Sathyabalan6/laptop-remote/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/laptop-remote.svg)](https://pypi.org/project/laptop-remote/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#-platform-support)

Turn your smartphone into a low-latency remote control for your laptop. Control media playback, stream a precision trackpad, type text, and present with a real-time laser pointer over local Wi-Fi.

<p align="center">
  <img src="docs/images/laser-trackpad-demo.gif" alt="Laser Pointer & Trackpad Demo" width="650">
</p>

> ⚠️ **LAN-only tool:** Designed for trusted local networks (home Wi-Fi / hotspot). Never expose it to the public internet — see [.github/SECURITY.md](.github/SECURITY.md).

---

## 📸 Screenshots

| Media Remote | Precision Trackpad | Presentation Deck | Terminal Companion |
| :---: | :---: | :---: | :---: |
| ![Media](docs/images/media.png) | ![Trackpad](docs/images/trackpad.png) | ![Presentation](docs/images/presentation.png) | ![Terminal](docs/images/laptopScreen.png) |

---

## 🚀 Quick Start

### Run Instantly (via `uv`)
```bash
uvx laptop-remote
```

### Or Install via `pip` / `pipx`
```bash
pipx install laptop-remote
laptop-remote
```

### Or Run from Source
```bash
git clone https://github.com/Sathyabalan6/laptop-remote.git
cd laptop-remote
pip install -e .

# Launch (Linux users can also run ./scripts/run.sh)
laptop-remote
```

Scan the terminal QR code or visit `http://<your-laptop-ip>:5000` (or `http://remotedeck.local:5000`) on your phone and enter the 6-digit pairing PIN.

---

## ✨ Features

- **🖱️ Precision Trackpad**: DPI-scaled cursor movement, tap-to-click, 2-finger right-click, pinch-to-zoom, and a 1-thumb right-edge scroll rail with tactile haptics.
- **🎵 Media Controls & Smart Focus**: Instant playback, volume slider, and auto-switching profiles for YouTube, VLC, Netflix, Prime Video, and Spotify.
- **⌨️ Keys & Typing**: Live phone-to-laptop text streaming, 5-way D-Pad for navigation, and quick system macros (`Lock PC`, `Close Window`, `Screenshot`).
- **📊 Presentation Mode**: Real-time screen laser pointer, timer, slide counter, and blackout mode.
- **🔒 Secure Pairing**: Rolling 6-digit PIN, cryptographic session tokens, persistent pairing across restarts, and LAN-wide brute-force lockout.
- **📱 PWA & Offline-First**: Installable to phone home screen with full offline caching via service workers. Zero cloud dependencies.

---

## 🖥️ Platform Support

| Platform | Mouse & Keyboard | Laser Pointer | Active App Sensing |
|---|---|---|---|
| **Windows** | ✅ Native (`win32api`) | ✅ Native overlay | ✅ Native (`win32gui`) |
| **macOS** | ✅ Native (`Quartz`) | ❌ Unsupported | ✅ Native (`osascript`) |
| **Linux (X11)** | ✅ PyAutoGUI / XTest | ✅ X11 SHAPE overlay | ✅ Native (`xprop`) |
| **Linux (Wayland)** | ✅ Kernel `ydotool` (via `scripts/setup_linux.sh`) | ⚠️ XWayland only | ⚠️ XWayland only |

---

## ⚙️ Customization

Edit [`presets.json`](presets.json) in the project root to customize application hotkeys and shortcuts.

---

## 🧪 Testing

```bash
# Python backend tests (169 tests)
pytest

# Frontend unit tests (49 Vitest tests)
npm test
```

---

## 📖 Documentation

For deep-dive architecture details, API specs, and packaging guides, check the [`docs/`](docs/) directory:
- [Module Architecture & Developer Guide](docs/DOCUMENTATION.md)
- [Keyboard Shortcuts Reference](docs/research.md)
- [Roadmap & Milestones](docs/ROADMAP.md)

---

## 🤝 Contributing

Contributions are welcome! Please read [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) and [.github/CODE_OF_CONDUCT.md](.github/CODE_OF_CONDUCT.md).

---

## 📄 License

MIT License — see [LICENSE](LICENSE).
