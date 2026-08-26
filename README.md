# 📱 Laptop Remote (Remote Deck)

> Turn your smartphone into a powerful, low-latency remote control for your laptop. Control media playback, stream a high-precision trackpad, navigate with a virtual D-Pad and keyboard, and present with a real-time screen laser pointer.

---

## ✨ Features at a Glance

* **🖥️ Desktop Companion & CLI Editions**: Choose between a modern Dark Mode GUI Companion app or a lightweight headless Terminal edition.
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

### Option 1: GUI Companion App (`LaptopRemote.exe`)
Ideal for everyday desktop use.

1. **Launch**: Double-click `dist/LaptopRemote.exe`.
2. **Scan & Connect**:
   * Ensure your phone and laptop are on the **same Wi-Fi network** (or phone hotspot).
   * Scan the on-screen **QR Code** with your phone's camera, or navigate to the displayed URL (e.g., `http://192.168.1.X:5000` or `http://remotedeck.local:5000`).
3. **Pair**: Enter the **6-digit Pairing PIN** shown in the companion window.
4. **Enjoy**: Use the remote from your phone browser or install it as a PWA!

### Option 2: Terminal / Headless Edition (`LaptopRemote-CLI.exe`)
Ideal for power users, scripts, or low-resource environments.

```bash
# Run with auto-generated PIN and ASCII QR Code
LaptopRemote-CLI.exe

# Run with a custom PIN/password
LaptopRemote-CLI.exe --pin 123456
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
# Install required Python dependencies
pip install flask pyautogui pywin32 qrcode pyinstaller pillow flask-socketio simple-websocket zeroconf ifaddr

# Run GUI Companion App
python server.py

# Run in Terminal-only / CLI mode
python cli.py
```

### Compiling Executables (`.exe`)
Use the included automated build batch scripts:

* **Interactive / Both Editions**: Double-click **`build.bat`** and select:
  * `[1]` GUI Companion App (`dist/LaptopRemote.exe`)
  * `[2]` Terminal Edition (`dist/LaptopRemote-CLI.exe`)
  * `[3]` Build Both Executables
* **Direct CLI Build**: Double-click **`build_cli.bat`** to build `dist/LaptopRemote-CLI.exe`.

---

## 📁 Project Structure

```
laptop-remote/
├── core/
│   ├── auth.py          # PIN generation, bearer token management, rate limiting
│   ├── config.py        # Presets JSON loader and path resolver
│   ├── input.py         # Mouse/keyboard drivers (win32api / Quartz / PyAutoGUI)
│   ├── network.py       # Local IP resolution utility
│   ├── overlay.py       # Fullscreen transparent Tkinter laser pointer & blackout overlay
│   ├── power.py         # Battery status monitor
│   └── window.py        # Foreground window title detection & auto-preset matching
├── static/
│   ├── index.html       # Mobile web remote interface (Media, Mouse, Keypad, Present)
│   ├── companion.html   # Web companion overview page
│   ├── socket.io.min.js # Bundled offline WebSocket client
│   ├── manifest.webmanifest # PWA metadata configuration
│   └── sw.js            # Service worker for offline caching
├── gui.py               # Tkinter desktop companion window (Dark UI, PIN display, QR preview)
├── cli.py               # Headless terminal entry point
├── server.py            # Main Flask + Flask-SocketIO backend & mDNS server
├── presets.json         # Keyboard shortcut profiles (Universal, YouTube, VLC, etc.)
├── build.bat            # Automated PyInstaller build script (GUI & CLI)
├── build_cli.bat        # PyInstaller build script for CLI edition
└── README.md            # Project documentation
```

---

## 📄 License
This project is open-source and free to use for personal and educational purposes.
