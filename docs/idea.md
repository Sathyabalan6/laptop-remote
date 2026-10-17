# 💡 Project Idea & Current State: Laptop Remote

## 🎯 Current Idea
**Laptop Remote** is a lightweight, zero-configuration utility designed to turn any mobile phone or tablet into a responsive remote control for a laptop. 

Unlike traditional remote control apps that require cloud accounts, client-side app store downloads, or complex network configurations, Laptop Remote focuses on speed and simplicity:
1. **No App Installs**: The phone interface is a clean web page served directly from the laptop.
2. **Instant QR Code Connection**: Simply scan the terminal-printed QR code on the same Wi-Fi network to connect.
3. **Low Latency & High Response**:
   * Uses `win32api` directly on Windows for near-zero latency mouse movements.
   * Optimizes network event batching (throttling) to ensure smooth trackpad dragging and scrolling.
4. **Universal Media Controls**: Features native OS volume control and selectable website presets (YouTube, Hotstar, Netflix, Prime Video, VLC, etc.) to handle different key bindings automatically.

---

## 🚦 Current State of the Project

The project is currently fully functional, clean, and packaged for distribution. Here is the breakdown of the system components:

### 1. ⚙️ Backend (Python/Flask)
* **Architecture**: Modular Python package in `src/laptop_remote/`
  * `core/`: Cross-platform input (Wayland ydotool/dotool, X11, Win32, AppKit), audio, auth, config, network, power, window, logger.
  * `server/`: Flask & Flask-SocketIO routes, discovery (mDNS zeroconf), WebSocket event handlers, state broadcasts.
* **Status**: 
  * Hosts a lightweight Flask server on port `5000` (configurable via `--port`) bound to `0.0.0.0` for local network access.
  * Primary transport is a **WebSocket** (`simple-websocket`) for ultra-low latency mouse/pointer streaming, with automatic HTTP fallback.
  * **Secure by default**: 4-digit PIN pairing shown in terminal or QR code; tokens authenticated with constant-time verification. Supports multi-device tracking and per-device revocation.
  * Automatically resolves host laptop's local IP, prints an ASCII QR code, and registers mDNS (`remotedeck.local`).
  * Cross-platform input backend: native `win32api` on Windows, native `ydotool`/`dotool` on Linux Wayland, `python-xlib` on X11, and `AppKit` on macOS.

### 2. 📱 Frontend Client (PWA / Vanilla JS)
* **Directory**: `src/laptop_remote/static/`
* **Status**:
  * Clean Apple HIG glassmorphism design with Dark Glass and OLED Pitch Black themes.
  * **Trackpad Tab**:
    * 1-finger drag for smooth pointer movement with acceleration curve.
    * 1-finger tap for Left Click, 2-finger tap for Right Click.
    * 2-finger calibrated drag with smooth inertia deceleration.
    * 2-finger pinch-to-zoom with gesture intent lock and visual HUD feedback.
    * Dual sensitivity sliders for Pointer Speed and Scroll Speed.
  * **Media & Presets Tab**:
    * Play/pause, volume slider, mute toggle, seek buttons, fullscreen.
    * Presets Editor modal to customize hotkeys for Universal, YouTube, Hotstar, and VLC.
  * **Presentation Tab**:
    * Laser pointer overlay with transparent multi-monitor projection.
    * Large slide navigation buttons (Prev / Next) and elapsed presentation timer.
  * **PWA & Offline**:
    * Service worker precaching (`sw.js`) with versioned cache invalidation.

### 3. 📦 Distribution & Tooling
* **Status**:
  * One-line instant launch: `uvx laptop-remote` (no pre-installation required).
  * Package managers: `pipx install laptop-remote` or `pip install laptop-remote`.
  * Standalone Windows binary: `LaptopRemote-CLI.exe` generated via PyInstaller and automated in GitHub Releases.
  * Comprehensive test suite: Pytest backend tests and Vitest frontend touch physics tests.
