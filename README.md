# 📱 Laptop Remote (Remote Deck)

[![CI](https://github.com/Sathyabalan6/laptop-remote/actions/workflows/ci.yml/badge.svg)](https://github.com/Sathyabalan6/laptop-remote/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#-platform-support)

> Turn your smartphone into a powerful, low-latency remote control for your laptop. Control media playback, stream a high-precision trackpad, navigate with a virtual D-Pad and keyboard, and present with a real-time screen laser pointer.

> ⚠️ **LAN-only tool.** Designed for trusted local networks (home Wi-Fi / hotspot). Do **not** expose it to the public internet — see [SECURITY.md](SECURITY.md).

---

## ✨ Features at a Glance

* **⚡ Terminal / Headless Edition**: A lightweight, no-GUI server that prints a QR code and pairing PIN directly in the terminal.
* **🌐 Zero-Config Discovery**: Connect instantly via QR code scan, local IP, or mDNS (`http://remotedeck.local:5000`).
* **🔒 Secure PIN Pairing**: Protected with 6-digit rolling PIN verification, session Bearer tokens, and brute-force IP rate limiting.
* **🎵 Smart Media Deck**: Context-aware media controls for YouTube, Netflix, Disney+ Hotstar, Prime Video, VLC, and web players.
* **🔍 Auto-Profile Detection**: Automatically detects the active foreground window and switches key mappings on the fly.
* **🖱️ Low-Latency Trackpad**: Smooth mouse movement powered by WebSockets, native OS input simulation, DPI scaling, tap-to-click, and 2-finger inertia scrolling.
* **⌨️ Keyboard & Navigation Keypad**: Send text input/search queries directly to your laptop, use a 5-way D-Pad, and trigger 1-touch hotkey tiles (skip intro, cycle audio tracks, speed +/-).
* **📊 Presentation Mode with Laser Pointer**: Projects a red laser dot across your laptop screen in real time, with slide controls, blackout mode, and an elapsed presentation timer.
* **📱 Progressive Web App (PWA)**: Installable to your phone's home screen for a distraction-free, full-screen remote experience.
* **🔋 Host Status**: Live laptop battery percentage and active profile indicators.

---

## 🚀 Quick Start

### From a prebuilt executable (`LaptopRemote-CLI.exe`)

1. **Launch**: Double-click `dist/LaptopRemote-CLI.exe` (or run it from a terminal).
2. **Scan & Connect**:
   * Ensure your phone and laptop are on the **same Wi-Fi network** (or phone hotspot).
   * Scan the **QR Code** printed in the terminal with your phone's camera, or navigate to the displayed URL (e.g., `http://192.168.1.X:5000` or `http://remotedeck.local:5000`).
3. **Pair**: Enter the **6-digit Pairing PIN** shown in the terminal.
4. **Enjoy**: Use the remote from your phone browser or install it as a PWA!

### From source (Python 3.10+)

```bash
# One-time: install dependencies
pip install -e .

# Run with an auto-generated PIN and ASCII QR code
python -m laptop_remote

# Run with a custom PIN / different port
python -m laptop_remote --pin 123456 --port 5000

# Enable HTTPS/WSS (self-signed cert auto-generated)
python -m laptop_remote --ssl
```

Or use the Linux launcher (also sets up Wayland mouse support if needed):

```bash
./run.sh
```

---

## 🛠️ Remote Deck Controls & Tabs

### 🎵 1. Media Tab
* **Active Profile**: Auto-detects or lets you manually switch between **YouTube / Hotstar**, **VLC Media Player**, and **Universal (Netflix / Prime / Web)**.
* **Playback Controls**: Play / Pause toggle, Skip Backward 10s (`⏪`), Skip Forward 10s (`⏩`), Fast Skip 30s (`⏭️`).
* **Navigation & View**: Previous / Next episode/track, Fullscreen toggle (`⛶`).
* **🔊 OS-Level Audio Controls**: Volume Up, Volume Down, and Mute buttons adjust the host system volume directly — ensuring 100% reliability regardless of browser focus or scrolling.
* **💬 Subtitles & Tracks**: One-tap toggle for closed captions, subtitle sync delay/advance (`Z` / `Shift+Z` / `G` / `H`), and multi-language audio stream cycling.

---

### 🖱️ 2. Mouse & Trackpad Tab
* **High-Precision Trackpad**: Move cursor with one finger. Backed by native OS cursor calls (`win32api` / macOS Quartz) with DPI-scaled acceleration curves for smooth, responsive movement.
* **Tap-to-Click**: Tap trackpad surface for instant left-click.
* **Physical Click Buttons**: Dedicated Left Click and Right Click pads.
* **2-Finger Momentum Scroll**: Drag with two fingers to scroll web pages, documents, or timelines with natural physics decay.
* **Sensitivity Slider**: Fine-tune cursor speed and acceleration response directly from your phone.

---

### ⌨️ 3. Keyboard & Keypad Tab
* **Live Search & Text Typing**: Type queries or URLs on your phone and press **Search** to send them to the active text field on your laptop (supports rapid clipboard pasting).
* **Targeted Focus**:
  * `/ Focus Search`: Focuses in-page search bars on YouTube, streaming sites, and web apps.
  * `Ctrl+L URL Bar`: Immediately jumps focus to the browser's address bar.
* **5-Way D-Pad & Navigation**: Dedicated `Up`, `Down`, `Left`, `Right`, and `OK` (Enter) buttons, plus `ESC`, `TAB`, `⇧ TAB`, and `Backspace`.
* **Streaming & Quick Hotkey Grid**:
  | Hotkey Tile | Shortcut Action | Supported Apps |
  | :--- | :--- | :--- |
  | **Skip Intro** (`S`) | Skips intros & recaps | Netflix, Prime, Hotstar |
  | **Theater Mode** (`T`) | Expands player view | YouTube, Twitch |
  | **Miniplayer** (`I`) | Picture-in-Picture mode | YouTube, Browsers |
  | **Audio Dub** (`A`/`B`) | Cycle audio language tracks | VLC, Streaming |
  | **Speed +/-** (`>`/`<`) | Speed up / slow down playback | YouTube, VLC |
  | **Sub Sync +/-** | Shift subtitle timing forward/back | VLC, Media Players |
  | **Next Tab** (`Ctrl+Tab`)| Cycle forward through browser tabs | Chrome, Firefox, Edge |
  | **Reload** (`F5`) | Refresh current web page | All Browsers |
  | **Sub Size +/-** | Increase or decrease caption font size | Supported Players |

---

### 📊 4. Present Tab
* **Screen Laser Pointer**: Touch and drag your finger across the pad to project a smooth, hardware-rendered red laser dot over your laptop screen in real time.
* **Slide Navigation**: Dedicated Next Slide and Previous Slide buttons.
* **Auto-Start Presentation**: Mapped to `F5` (or `Ctrl+F5` when Google Slides, Canva, Prezi, or Docs are active).
* **Blackout Screen**: Blank the laptop display with one tap during presentations or breaks.
* **Slide Counter & Live Timer**: Track slide numbers and presentation duration automatically from first touch.

---

## 🔒 Security & Connection Details

* **Rolling One-Time PIN**: A fresh 6-digit PIN is generated upon startup and regenerated after each successful pairing or manual revocation.
* **Brute-Force Protection**: IP-based lockout triggers automatically after 5 consecutive incorrect PIN attempts (30-second escalating lockout).
* **Bearer Token Authorization**: Paired devices receive a cryptographically secure 48-character session token stored locally on your device.
* **Dual Transport**: High-frequency mouse coordinates and laser pointer positions stream over **WebSockets** for minimal latency, with automatic fallback to REST endpoints if required.
* **Offline Self-Contained**: Socket.IO client library and assets are fully bundled locally — **no internet connection or CDN required**.

---

## ⚙️ Configuration & Custom Presets

Key mappings are defined in [`presets.json`](file:///E:/laptop-remote/presets.json). You can customize or add hotkeys for your favorite applications:

```json
{
  "youtube_hotstar": {
    "play_pause": "space",
    "skip_forward": "l",
    "skip_back": "j",
    "skip_forward_30": ["l", "l", "l"],
    "next": ["shift", "n"],
    "fullscreen": "f",
    "subtitles": "c",
    "speed_up": ["shift", "."]
  },
  "universal": {
    "play_pause": "space",
    "skip_forward": "right",
    "skip_back": "left",
    "fullscreen": "f"
  }
}
```

---

## 💻 Developer Setup & Building Executables

### Prerequisites
* Python 3.10+ installed and added to your system `PATH`.

### Running from Source
```bash
# Install the package in editable mode (pulls in all dependencies)
pip install -e .

# Run the server (terminal edition)
python -m laptop_remote
```

### Compiling a Standalone Executable (`.exe`)

* **Windows**: Double-click **`build.bat`** to build `dist/LaptopRemote-CLI.exe`.
* **Linux**: Run **`./build.sh`** to build `dist/LaptopRemote-CLI`.

---

## 📁 Project Structure

```
laptop-remote/
├── pyproject.toml              # Packaging metadata & dependencies
├── requirements.txt            # Runtime dependencies
├── run.sh / build.sh           # Linux launcher / builder
├── build.bat / build_cli.bat   # Windows builders
├── setup_linux.sh              # One-time Wayland (ydotool) setup on Linux
├── presets.json                # Keyboard shortcut profiles (user-editable)
├── logo.ico                    # App icon
├── src/
│   └── laptop_remote/          # Main application package
│       ├── __init__.py
│       ├── __main__.py         # python -m laptop_remote
│       ├── server/             # Flask + SocketIO server package
│       │   ├── __init__.py     # public API (app, socketio, main)
│       │   ├── _app.py         # app construction & shared runtime state
│       │   ├── state.py        # build_state()
│       │   ├── routes_auth.py  # pairing, revoke, QR
│       │   ├── routes_input.py # mouse/key/text/pointer/volume
│       │   ├── websocket.py    # Socket.IO handlers
│       │   ├── discovery.py    # mDNS + preset monitor
│       │   └── main.py         # main() entry point
│       ├── cli.py              # Terminal/headless entry point
│       ├── core/               # Platform backends & utilities
│       │   ├── input.py        # Mouse/keyboard drivers (Windows/macOS/X11/Wayland)
│       │   ├── keys.py         # Key-name → Linux input-event keycode mapping
│       │   ├── auth.py         # PIN generation, bearer tokens, rate limiting
│       │   ├── config.py       # Presets JSON loader & path resolver
│       │   ├── network.py      # Local IP resolution & SSL certificate setup
│       │   ├── overlay.py      # Laser pointer & blackout Tk overlay
│       │   ├── power.py        # Battery status monitor
│       │   ├── window.py       # Foreground window detection & auto-preset
│       │   ├── audio.py        # Cross-platform volume control
│       │   └── tray.py         # System tray icon manager
│       └── static/             # Web frontend (served as the remote UI)
│           ├── index.html
│           ├── css/            # tokens.css, base.css, components.css
│           └── js/             # app.js, transport.js, trackpad.js, ...
├── docs/                       # Design notes & research
├── tests/                      # pytest test suite
└── README.md
```

---

## 🖥️ Platform Support

| Platform | Mouse / Keyboard | Presentation Laser Pointer |
|---|---|---|
| **Windows** | ✅ Native (`win32api`) | ✅ Red dot overlay |
| **macOS** | ✅ Native (`Quartz`) | ❌ Not yet |
| **Linux (X11)** | ✅ `pyautogui` / XTest | ❌ Not yet (see note) |
| **Linux (Wayland)** | ✅ `ydotool` / `dotool` — one-time `bash setup_linux.sh` | ❌ Not available |

> **Laser pointer note:** the on-screen red-dot overlay is currently **Windows only**.
> It relies on a transparent, click-through always-on-top window, which GNOME/KDE
> Wayland does not allow for normal apps. On other platforms the Present tab still
> provides **slide navigation, the elapsed timer, and blackout mode**, and the laser
> pad is hidden with an explanatory message. Contributions to add X11/XWayland
> overlay support are welcome — see the issues.

---

## 🧪 Running Tests

```bash
pip install -e ".[dev]"
pytest
```

Tests run automatically on Linux, Windows, and macOS via GitHub Actions.

---

## 🤝 Contributing

Contributions are very welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup
instructions, coding guidelines, and platform testing notes. Please also read our
[Code of Conduct](CODE_OF_CONDUCT.md).

- 🐛 [Report a bug](https://github.com/Sathyabalan6/laptop-remote/issues/new?template=bug_report.yml)
- ✨ [Request a feature](https://github.com/Sathyabalan6/laptop-remote/issues/new?template=feature_request.yml)
- 💬 [Ask a question](https://github.com/Sathyabalan6/laptop-remote/discussions)

---

## 🔐 Security

This is a **LAN-only** tool. Please read [SECURITY.md](SECURITY.md) before
reporting vulnerabilities or deploying it.

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE).
Free to use, modify, and distribute for personal and commercial purposes.
