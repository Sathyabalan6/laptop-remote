# 📱 Laptop Remote

Control your laptop playback and mouse cursor directly from your phone. Built with a responsive dark-mode touch interface.

---

## 🚀 How to Run (Using the `.exe`)

If you have the precompiled **`LaptopRemote.exe`** (located in the `dist/` folder):

1. **Launch the Remote**: Double-click `LaptopRemote.exe`. A terminal window will open showing the server status and connection info.
2. **Connect Your Phone**:
   * Make sure your phone and laptop are connected to the **same Wi-Fi network** (or connect your laptop to your phone's mobile hotspot).
   * Scan the **QR Code** printed in the terminal using your phone's camera, or type the URL (e.g., `http://192.168.1.X:5000`) manually in your phone's web browser.
3. **Pair**: The first time you connect, enter the **6-digit Pairing PIN** shown in the terminal (next to the QR code). Your device is remembered after that.
4. **Control**: You can now control your laptop! Keep the terminal window running in the background.

---

## 🛠️ Features & Controls

### 🎵 Media Tab
* **Playback Preset Selector** (New!):
  * **Universal / Netflix / Prime / VLC**: Uses arrow keys for skipping (10s skip natively on Netflix/Prime, works with local players like VLC and most websites).
  * **YouTube / Hotstar**: Uses `J` (Skip back 10s), `L` (Skip forward 10s), and `Shift + N` (Next video/episode) keys.
* **⏯️ Play / Pause**: Universal toggle.
* **⏪ / ⏩ Skip 10s**: Skips forward or backward.
* **⏭️ Skip 30s**: Batches skip inputs to jump forward quickly.
* **⛶ Fullscreen**: Toggle fullscreen mode.

### 🔊 Audio Controls
* **Mute / Volume Up / Volume Down**:
  * **Note**: These controls change the **system-wide OS volume** of your laptop rather than the in-page player volume.
  * **Why?** This guarantees volume changes work 100% of the time, even if you are clicked out of the web browser, if the browser is in the background, or if the page has scrolled.

### 💬 Subtitles (CC / Subs)
* **YouTube & Prime Video**: Toggles subtitles on/off (presses the `C` key).
* **Netflix & Disney+ Hotstar**: These platforms **do not have built-in keyboard shortcuts** to toggle subtitles.
  * *Solution*: Switch to the **Mouse** tab on the remote and use the trackpad to click the subtitles speech-bubble icon directly on the video player.

### 🖱️ Mouse Tab
* **Trackpad**: Drag with one finger to move the cursor smoothly. Uses screen DPI scaling for consistent sensitivity.
* **Tap-to-Click**: Lightly tap the trackpad with one finger to left-click.
* **Left & Right Click**: Dedicated physical buttons for clicking.
* **2-Finger Scroll**: Drag two fingers up or down on the trackpad to scroll pages with physics-based momentum (inertia decay).
* **Precision tuning**: The sensitivity slider also tunes the host's smoothing/acceleration curve for a snappier, "gaming-mouse" feel.

### 📊 Present Tab
* **Laser Pointer**: Touch and hold on the pad to move a red laser dot over the host screen — great for highlighting slides in a presentation.
* **Prev / Next Slide**: Dedicated buttons mapped to `Alt+Left` / preset `next`.
* **Elapsed Timer**: Auto-starts on first laser touch.

> The Present tab is hidden automatically when the host can't display the overlay (e.g. no tkinter available).

---

## 💻 Developer Setup & Rebuilding the `.exe`

If you modify the source files (e.g. `server.py` or `static/index.html`) and want to compile a new `.exe`:

1. **Prerequisites**: Install Python (check "Add to PATH" during installation).
2. **Build**: Double-click **`build.bat`**. This will automatically:
   * Install python dependencies (`flask`, `pyautogui`, `qrcode`, `pywin32`, `pillow`, `flask-socketio`, `simple-websocket`, `pyinstaller`).
   * Clean old build files.
   * Package everything into a single, portable executable located at `dist/LaptopRemote.exe`.

**Transport note**: The app talks to your phone over a **WebSocket** (low-latency mouse/pointer streaming) with automatic fallback to plain HTTP if a connection can't be established. The `static/socket.io.min.js` client is bundled with the app, so it stays fully self-contained (no CDN required).
