import sys
import time
import threading

IS_WINDOWS = sys.platform.startswith('win')

try:
    import tkinter as tk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

try:
    import pyautogui
    SCREEN_W, SCREEN_H = pyautogui.size()
except Exception:
    SCREEN_W, SCREEN_H = 1920, 1080

class LaserOverlay:
    def __init__(self):
        self.root = None
        self.dot = None
        self.canvas = None
        self.visible = False
        self.blackout = False
        self.last_activity = time.time()

    def init_with_parent(self, parent_root):
        if not (HAS_TKINTER and IS_WINDOWS and parent_root):
            return
        try:
            self.root = tk.Toplevel(parent_root)
            self.root.attributes('-alpha', 1.0)
            self.root.attributes('-topmost', True)
            self.root.attributes('-transparentcolor', 'black')
            self.root.overrideredirect(True)
            self.root.geometry(f"{SCREEN_W}x{SCREEN_H}+0+0")
            self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
            self.canvas.pack(fill='both', expand=True)
            self.dot = self.canvas.create_oval(-50, -50, -30, -30, fill='red', outline='')
            self.root.withdraw()
            threading.Thread(target=self._watchdog_loop, daemon=True).start()
        except Exception as e:
            print(f"⚠️ Failed to attach laser overlay to parent: {e}")
            self.root = None

    def start(self):
        if not (HAS_TKINTER and IS_WINDOWS):
            return
        threading.Thread(target=self._run, daemon=True).start()
        for _ in range(20):
            if self.root is not None:
                break
            time.sleep(0.05)
        threading.Thread(target=self._watchdog_loop, daemon=True).start()

    def _watchdog_loop(self):
        while True:
            time.sleep(0.5)
            if self.visible and not self.blackout and (time.time() - self.last_activity > 2.0):
                self.hide()

    def _run(self):
        try:
            self.root = tk.Tk()
            self.root.attributes('-alpha', 1.0)
            self.root.attributes('-topmost', True)
            self.root.attributes('-transparentcolor', 'black')
            self.root.overrideredirect(True)
            self.root.geometry(f"{SCREEN_W}x{SCREEN_H}+0+0")
            self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
            self.canvas.pack(fill='both', expand=True)
            self.dot = self.canvas.create_oval(-50, -50, -30, -30, fill='red', outline='')
            self.root.withdraw()
            self.root.mainloop()
        except Exception as e:
            print(f"⚠️ Failed to initialize laser overlay: {e}")
            self.root = None

    def show(self):
        self.last_activity = time.time()
        if self.blackout:
            return
        if self.root:
            try:
                self.root.after(0, self.root.deiconify)
            except Exception:
                pass
        self.visible = True

    def hide(self):
        if self.blackout:
            return
        if self.root:
            try:
                self.root.after(0, self.root.withdraw)
            except Exception:
                pass
        self.visible = False

    def set_blackout(self, on):
        on = bool(on)
        self.blackout = on
        self.last_activity = time.time()
        if not self.root:
            return
        def _apply():
            if on:
                self.canvas.config(bg='#000001')
                self.canvas.coords(self.dot, -50, -50, -30, -30)
                self.root.deiconify()
            else:
                self.canvas.config(bg='black')
                self.root.withdraw()
        self.root.after(0, _apply)
        self.visible = on

    def move(self, x, y):
        self.last_activity = time.time()
        if self.root:
            try:
                self.root.after(0, lambda: self.canvas.coords(self.dot, x-12, y-12, x+12, y+12))
            except Exception:
                pass
