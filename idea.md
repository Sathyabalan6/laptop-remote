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
* **File**: [server.py](file:///E:/laptop-remote/server.py)
* **Status**: 
  * Hosts a lightweight Flask server on port `5000` bound to all interfaces (`0.0.0.0`) so it is accessible from the local network.
  * Primary transport is a **WebSocket** (Flask-SocketIO over `simple-websocket`) for low-latency mouse/pointer streaming, with automatic HTTP fallback if WebSockets can't be established.
  * **Secure by default**: a 6-digit pairing PIN is shown in the terminal; the phone pairs once and stores a session token. Every mouse/key/pointer action is authenticated, and `POST /revoke` kills all sessions instantly.
  * Automatically resolves the host laptop's local IP address and renders a scannable ASCII QR code in the terminal on startup.
  * Pushes real-time state to connected clients (screen size, battery %, detected playback preset) instead of polling.
  * Utilizes `pyautogui` to simulate keystrokes and scroll events, falling back gracefully if advanced libraries are missing.
  * Utilizes low-level `win32api` (part of `pywin32`) to achieve instantaneous mouse cursor movement.

### 2. 📱 Frontend Client (HTML5/CSS3/JS)
* **File**: [static/index.html](file:///E:/laptop-remote/static/index.html)
* **Status**:
  * Designed with a modern, responsive, dark-theme layout (SF Pro typography, vibrant accent gradients, and glassmorphism styling).
  * **Media Tab**:
    * Houses play/pause, volume, skip buttons, CC, and full-screen toggles.
    * Features a **Preset Selector** enabling dynamic key mapping depending on the active website (e.g. `Universal` vs `YouTube / Hotstar`).
    * Shows the host's live battery level in the header.
  * **Mouse Tab**:
    * A full-viewport trackpad supporting smooth dragging.
    * Uses `devicePixelRatio` to scale drag coordinates consistently across different mobile screen DPIs.
    * Employs gesture logic: Single-finger tap to left-click, two-finger drag to scroll the page.
    * Implements scroll momentum (inertia decay) so that quick two-finger flicks scroll long pages naturally.
    * Sensitivity slider tunes the host's smoothing/acceleration curve for a precise, high-sensitivity feel.
  * **Present Tab**:
    * Touch-and-hold laser pointer that projects a red dot over the host screen, plus Prev/Next slide controls and an auto-start elapsed timer.
    * Auto-hidden when the host can't show the overlay.
  * **Network Status**: Driven by the WebSocket connection (instant green/red state) with an animated retry banner; falls back to a slow HTTP heartbeat only if WebSockets are unavailable.
  * **Pairing Flow**: On first connect a 6-digit PIN overlay pairs the phone; the token is stored so reconnects are silent. A "Forget Device" action revokes all sessions.
  * **PWA**: Installable ("Add to Home Screen") with a self-contained manifest, icon, and service worker.

### 3. 📦 Distribution & Tooling
* **Status**:
  * Uses PyInstaller configured via [laptop_remote.spec](file:///E:/laptop-remote/laptop_remote.spec) to package the python backend and the static client directory into a single, standalone executable: `dist/LaptopRemote.exe`.
  * **No Dependencies**: End-users do not need Python, Flask, or any library installed. They just double-click the `.exe` file.
  * Dev tooling includes [build.bat](file:///E:/laptop-remote/build.bat) to clean build folders and compile fresh executables in one click, and [.gitignore](file:///E:/laptop-remote/.gitignore) to exclude binary outputs from source code repositories.
