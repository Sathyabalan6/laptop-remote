# 💻 Laptop Remote — Comprehensive Feature & Functionality Guide

## 📌 Overview

**Laptop Remote** is a production-grade, lightweight, zero-build cross-platform remote control application. It allows you to control your laptop (Linux, Windows, or macOS) from any smartphone or tablet web browser over local Wi-Fi without installing mobile apps.

---

## 🏗️ Architectural Blueprint

```
 ┌──────────────────────────────────────────────────────────┐
 │                Mobile / Phone Web Browser               │
 │           (Zero-Build ES6 Modules + PWA CSS)             │
 └────────────────────────────┬─────────────────────────────┘
                              │
                    WebSocket / HTTP REST
                              │
 ┌────────────────────────────▼─────────────────────────────┐
 │                      server.py                           │
 │         (Flask + Flask-SocketIO Event Server)            │
 └──────┬─────────────────────┬──────────────────────┬──────┘
        │                     │                      │
 ┌──────▼──────┐       ┌──────▼──────┐        ┌──────▼──────┐
 │ core/auth.py│       │core/input.py│        │core/audio.py│
 │ (PIN / Tokens)      │(Mouse & Keys)        │(Master Vol) │
 └─────────────┘       └─────────────┘        └─────────────┘
```

---

## 🎮 Features & Subsystem Breakdown

### 1. 🎵 Media Control Hub (`static/js/media.js`, `core/input.py`)
- **Player Profiles / Presets**:
  - **Universal**: Standard media keys (`play/pause`, `space`, `left/right` arrows) for Netflix, Prime Video, Disney+, etc.
  - **YouTube / Hotstar**: Hotkeys (`k` for play/pause, `j/l` for 10s skips, `m` for mute, `f` for fullscreen).
  - **VLC Media Player**: VLC-specific shortcuts (`space`, `n` next track, `p` prev track, `ctrl+up/down` volume).
- **Playback Controls**:
  - **Play / Pause Circle**: Toggles playback on active player.
  - **Seek Buttons**: Instant -10s, +10s, +30s jump buttons.
  - **Browser Navigation**: Go back (`Alt+Left` / `BrowserBack`).
  - **Subtitles & Audio**: Subtitle toggle, subtitle sync advance/delay (`G/H`), subtitle font sizing, and audio dub track cycling (`A/B`).
  - **Playback Speed**: Incremental speed up (`Shift+>`) and speed down (`Shift+<`).

---

### 2. 🖱️ High-Precision Touch Trackpad (`static/js/trackpad.js`, `core/input.py`)
- **Velocity Acceleration Engine**: Applies sub-linear acceleration (`ad ** 1.35`) for pixel-exact fine positioning during slow finger movement, while enabling fast cursor snaps across multi-monitor setups.
- **Zero-Latency Processing**: PyAutoGUI parameters configured (`PAUSE = 0`, `MINIMUM_DURATION = 0`) to eliminate frame delays and provide instantaneous response.
- **Continuous Tactile Scroll**: Vertical scroll column with press-and-hold tactile buttons, plus two-finger continuous trackpad swipe scrolling.
- **Left & Right Click Buttons**: Dedicated tactile click buttons and tap-to-click gesture support.

---

### 3. ⌨️ Keypad & Live Search (`static/js/media.js`, `core/input.py`)
- **Live Text Search Bar**: Type text on phone keyboard and stream it directly to active text inputs or search fields on laptop.
- **Shortcut Focus Buttons**:
  - `Focus Search (/)`: Triggers in-page search input across web applications.
  - `URL Bar (Ctrl+L)`: Instantly highlights browser address bar.
- **Directional D-Pad & Navigation Grid**: 5-way D-pad (Up, Down, Left, Right, OK/Enter) plus ESC, TAB, Shift+TAB, and Backspace.
- **Hotkeys Grid**: Skip Intro (`S`), Theater Mode (`T`), Miniplayer (`I`), Reload (`F5`), Next Tab (`Ctrl+Tab`), Previous Tab (`Ctrl+Shift+Tab`).

---

### 4. 📊 Presentation & Laser Pointer Mode (`static/js/presentation.js`, `core/overlay.py    # Platform selection and Windows overlay
### 4. 📊 Presentation & Laser Pointer Mode (`static/js/presentation.js`, `core/overlay_x11.py # Linux X11 SHAPE overlay
- **Slide Deck Control**: Dedicated Next Slide (`PageDown`/`Right`) and Previous Slide (`PageUp`/`Left`) triggers.
- **Slideshow Launcher**: Launches presentation slideshow (`F5` / `Ctrl+F5`).
- **Laser Pointer Touchpad**: Real-time laser touchpad; touching and dragging on phone moves the onscreen red laser dot or updates hardware mouse pointer.
- **Elapsed Presentation Timer**: Built-in presentation stopwatch timer (`00:00`) tracking talk duration.
- **Blackout Overlay Toggle**: Instantly blanks the laptop display screen for audience focus.

#### Laser overlay support

| Display platform | Laser overlay |
|---|---|
| Windows | Supported by the native Tk overlay |
| Linux X11 | Supported when the server provides X11 SHAPE 1.1 |
| Linux Wayland | Not supported directly; XWayland works only when `DISPLAY` and SHAPE 1.1 are available |
| macOS | Not yet implemented |

The Linux overlay uses a shaped red X11 window with an empty input shape, allowing
pointer events to pass through. If the display or extension is unavailable, the
server reports the laser as unavailable instead of moving the system cursor.

---

### 5. 🔊 Master Audio System (`core/audio.py`)
- **True OS Volume Control**: Controls hardware master output volume directly, not just application volume:
  - **Linux**: Interoperable support for `wpctl`, `amixer`, and `pactl`.
  - **Windows**: Low-latency COM interface via `pycaw`.
  - **macOS**: Native AppleScript control (`osascript`).
- **Volume Slider Sync**: 0–100% volume slider with real-time bidirectional WebSocket state updates.
- **Mobile Volume Keys**: Pressing hardware volume buttons on your mobile phone dynamically targets laptop master volume.

---

### 6. 🔒 Security & Authentication Architecture (`core/auth.py`, `core/network.py`)
- **6-Digit Rolling PIN Pairing**: Requires entering a 6-digit PIN displayed on laptop startup to pair new mobile devices.
- **Session Tokens**: Cryptographically secure bearer tokens stored in browser `localStorage`.
- **IP Rate-Limiting & Exponential Backoff**: Prevents brute-force PIN attempts; locks offending IPs for 10 minutes after repeated failures.
- **Loopback-Only Management Endpoints**: The QR image endpoint (`/qr.png`) is locked strictly to loopback (`127.0.0.1` / `::1`).
- **HTTPS / TLS Encryption**: Optional `--ssl` flag with automatic self-signed certificate generation.

---

## 🛠️ Module Directory Structure

```
laptop-remote/
├── pyproject.toml            # Packaging metadata & dependencies
├── requirements.txt          # Runtime dependencies
├── run.sh                    # One-click Linux launcher (X11 + Wayland setup)
├── setup_linux.sh            # One-time Wayland (ydotool) setup
├── build.sh                  # PyInstaller standalone binary builder (Linux)
├── build.bat / build_cli.bat # PyInstaller builders (Windows)
├── src/
│   └── laptop_remote/        # Main application package
│       ├── __main__.py       # python -m laptop_remote
│       ├── cli.py            # Terminal-only headless launcher
│       ├── server/           # Flask & SocketIO server package
│       │   ├── __init__.py   # Public API & registration hookup
│       │   ├── _app.py       # app/socketio construction & shared runtime state
│       │   ├── state.py      # build_state() helper
│       │   ├── routes_auth.py    # Pairing, revoke, QR endpoints
│       │   ├── routes_input.py   # Mouse, key, text, pointer, volume endpoints
│       │   ├── websocket.py      # Socket.IO event handlers
│       │   ├── discovery.py      # mDNS/Zeroconf & preset-change monitor
│       │   └── main.py           # main() entry point & CLI
│       ├── core/
│       │   ├── audio.py      # Cross-platform master audio controller
│       │   ├── auth.py       # Security, rate-limiting & PIN authentication
│       │   ├── config.py     # Presets loader & storage
│       │   ├── input.py      # Mouse & keyboard backend (Win/macOS/X11/Wayland)
│       │   ├── keys.py       # Key-name → Linux input-event keycode mapping
│       │   ├── network.py    # IP discovery & TLS certificate generator
│       │   ├── overlay.py    # Platform selection and Windows overlay
│       │   ├── overlay_x11.py # Linux X11 SHAPE overlay
│       │   ├── power.py      # Battery status reader
│       │   ├── tray.py       # System tray icon (pystray)
│       │   └── window.py     # Active window & auto-preset detector
│       └── static/
│           ├── index.html    # Semantic HTML5 PWA single-page interface
│           ├── css/
│           │   ├── tokens.css      # OLED dark design tokens & typography
│           │   ├── base.css        # Layout structure & sticky headers
│           │   └── components.css  # Cards, trackpad, D-pad, laser pad
│           └── js/
│               ├── state.js        # App state, presets & wake lock
│               ├── transport.js    # Socket.IO & HTTP network client
│               ├── media.js        # Media player, search & shortcuts
│               ├── trackpad.js     # Gesture math & sensitivity scaling
│               ├── presentation.js # Laser pointer pad & presentation timer
│               └── app.js          # DOM binding & service worker initialization
└── presets.json                # Keyboard shortcut profiles (user-editable)
```

---

## 🚀 Quick Execution Commands

```bash
# Standard Launch
./run.sh

# Run in background system tray mode
./run.sh --tray

# Enable HTTPS encryption
./run.sh --ssl
```

## 🐧 Linux & Wayland: Mouse Input Setup

Mouse/keyboard control works out of the box on **Windows**, **macOS**, and **Linux (Xorg)** via native system APIs.

On **Linux + Wayland** (the default on modern GNOME/KDE), the OS does not allow apps to move the real cursor through the X11 API, so Laptop Remote needs a small helper tool (`ydotool`) and membership in the Linux `input` group.

This is a **one-time** setup (and only for Linux/Wayland users):

```bash
# One-time setup (installs ydotool + adds you to the input group)
bash setup_linux.sh

# Log out and back in, then start Laptop Remote normally
./run.sh
```

Laptop Remote auto-starts the `ydotoold` daemon on launch when possible, and prints a clear message if the `input` group membership is still missing.

| Operating System | Needs `ydotool`? |
|---|---|
| Windows | ❌ No (native `win32api`) |
| macOS | ❌ No (native `Quartz`) |
| Linux (Xorg session) | ❌ No (PyAutoGUI/X11) |
| Linux (Wayland session) | ✅ Yes (one-time `setup_linux.sh`) |
