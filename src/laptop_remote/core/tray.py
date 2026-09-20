import os
import sys
import threading
import webbrowser

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False

class SystemTrayManager:
    """
    Cross-platform system tray manager for Remote Deck using pystray.
    Provides background tray execution, connection info shortcuts,
    PIN regeneration, and graceful application termination.
    """
    def __init__(self, get_state_cb=None, on_show_gui_cb=None, regenerate_pin_cb=None, revoke_cb=None, quit_cb=None):
        self.get_state = get_state_cb
        self.on_show_gui = on_show_gui_cb
        self.regenerate_pin = regenerate_pin_cb
        self.revoke_devices = revoke_cb
        self.quit_app = quit_cb
        
        self.icon = None
        self.thread = None
        self.is_running = False

    def _create_icon_image(self, active=True):
        """Generates a high-DPI 64x64 icon image with OLED theme colors."""
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw outer rounded box
        bg_color = (14, 18, 13, 255)  # Dark OLED green surface
        border_color = (105, 240, 174, 255) if active else (239, 68, 68, 255)
        draw.rounded_rectangle([2, 2, size - 3, size - 3], radius=14, fill=bg_color, outline=border_color, width=3)

        # Draw inner emblem / text 'RD'
        try:
            # Attempt to use default PIL font
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Draw circuit accent / status dot
        dot_color = (0, 230, 118, 255) if active else (239, 68, 68, 255)
        draw.ellipse([size - 20, 6, size - 8, 18], fill=dot_color)

        # Draw center letters "RD"
        draw.text((16, 22), "RD", fill=(232, 245, 233, 255), font=font)
        return img

    def _on_show_info(self, icon, item):
        if self.on_show_gui:
            self.on_show_gui()

    def _on_copy_url(self, icon, item):
        if self.get_state:
            state = self.get_state()
            url = state.get("url", "http://127.0.0.1:5000")
            try:
                import tkinter as tk
                r = tk.Tk()
                r.withdraw()
                r.clipboard_clear()
                r.clipboard_append(url)
                r.update()
                r.destroy()
            except Exception:
                pass

    def _on_regen_pin(self, icon, item):
        if self.regenerate_pin:
            new_pin = self.regenerate_pin()
            if self.icon:
                self.icon.notify(f"New Pairing PIN: {new_pin}", title="Remote Deck")

    def _on_open_browser(self, icon, item):
        if self.get_state:
            state = self.get_state()
            url = state.get("url", "http://127.0.0.1:5000")
            webbrowser.open(url)

    def _on_revoke(self, icon, item):
        if self.revoke_devices:
            self.revoke_devices()
            if self.icon:
                self.icon.notify("All paired sessions revoked", title="Remote Deck")

    def _on_quit(self, icon, item):
        self.stop()
        if self.quit_app:
            self.quit_app()

    def start(self):
        """Starts the system tray icon in a dedicated daemon thread."""
        if not HAS_PYSTRAY:
            print("[Tray] pystray not installed or display server unavailable. Running without tray icon.")
            return False

        if self.is_running:
            return True

        menu = pystray.Menu(
            pystray.MenuItem("⚡ Remote Deck", self._on_show_info, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📱 Show GUI / PIN", self._on_show_info),
            pystray.MenuItem("📋 Copy Connection URL", self._on_copy_url),
            pystray.MenuItem("🔄 Generate New PIN", self._on_regen_pin),
            pystray.MenuItem("🌐 Open Web Deck", self._on_open_browser),
            pystray.MenuItem("🔒 Revoke All Sessions", self._on_revoke),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit Remote Deck", self._on_quit)
        )

        image = self._create_icon_image(active=True)
        self.icon = pystray.Icon("remote_deck", image, "Remote Deck · Server", menu)

        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()
        self.is_running = True
        return True

    def stop(self):
        """Stops and removes the system tray icon."""
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
        self.is_running = False
