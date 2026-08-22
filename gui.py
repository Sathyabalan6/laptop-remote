import os
import sys
import time
import io
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox
import qrcode
from PIL import Image, ImageTk

class CompanionApp:
    def __init__(self, get_state_callback=None, regenerate_pin_callback=None):
        self.get_state = get_state_callback
        self.regenerate_pin_cb = regenerate_pin_callback
        
        self.root = tk.Tk()
        self.root.title("Remote Deck · Server Companion")
        self.root.geometry("420x540")
        self.root.resizable(False, False)
        self.root.configure(bg="#0e0e11")

        self.server_url = "http://127.0.0.1:5000"
        self.pin = "------"
        self.connected_count = 0
        self.active_profile = "Universal"
        self.qr_photo = None

        self._build_ui()
        self.update_data(self.server_url, self.pin, 0, "Universal")
        self._update_loop()

    def _build_ui(self):
        # Header bar
        header_frame = tk.Frame(self.root, bg="#0c0e14", height=44)
        header_frame.pack(fill="x", side="top")

        title_lbl = tk.Label(header_frame, text="⚡ Remote Deck · Companion", font=("Segoe UI", 11, "bold"), fg="#e2e1eb", bg="#0c0e14")
        title_lbl.pack(side="left", padx=16, pady=10)

        self.status_badge = tk.Label(header_frame, text="● Active · Port 5000", font=("Segoe UI", 9, "bold"), fg="#22c55e", bg="#1e1f26", padx=8, pady=3)
        self.status_badge.pack(side="right", padx=16, pady=8)

        # Main container
        container = tk.Frame(self.root, bg="#0e0e11", padx=16, pady=6)
        container.pack(fill="both", expand=True)

        # QR Code Card
        qr_card = tk.Frame(container, bg="#1e1f26", highlightbackground="#464553", highlightthickness=1, padx=10, pady=8)
        qr_card.pack(fill="x", pady=(0, 6))

        # Note: Do not specify text-character width/height on Label containing an image
        self.qr_label = tk.Label(qr_card, bg="#0c0e14", bd=0)
        self.qr_label.pack(pady=2)

        scan_hint = tk.Label(qr_card, text="Scan with phone camera to connect instantly", font=("Segoe UI", 9), fg="#c7c5d6", bg="#1e1f26")
        scan_hint.pack(pady=(2, 2))

        # PIN Card
        pin_card = tk.Frame(container, bg="#1e1f26", highlightbackground="#464553", highlightthickness=1, padx=10, pady=6)
        pin_card.pack(fill="x", pady=(0, 6))

        pin_header_row = tk.Frame(pin_card, bg="#1e1f26")
        pin_header_row.pack(fill="x", pady=(0, 3))

        pin_title = tk.Label(pin_header_row, text="🔒 PAIRING PIN", font=("Segoe UI", 9, "bold"), fg="#c7c5d6", bg="#1e1f26")
        pin_title.pack(side="left")

        pin_copy_hint = tk.Label(pin_header_row, text="(Click to copy)", font=("Segoe UI", 8), fg="#c1c1ff", bg="#1e1f26", cursor="hand2")
        pin_copy_hint.pack(side="right")
        pin_copy_hint.bind("<Button-1>", lambda e: self.copy_pin())

        # 6 digit boxes
        boxes_row = tk.Frame(pin_card, bg="#1e1f26")
        boxes_row.pack(fill="x", pady=2)

        self.pin_boxes = []
        for i in range(6):
            box = tk.Label(boxes_row, text="-", font=("Consolas", 17, "bold"), fg="#c1c1ff", bg="#0c0e14",
                           width=3, height=1, highlightbackground="#464553", highlightthickness=1, cursor="hand2")
            box.pack(side="left", expand=True, padx=2, fill="x")
            box.bind("<Button-1>", lambda e: self.copy_pin())
            self.pin_boxes.append(box)

        # Network Info Card
        net_card = tk.Frame(container, bg="#1e1f26", highlightbackground="#464553", highlightthickness=1, padx=10, pady=6)
        net_card.pack(fill="x", pady=(0, 6))

        self.url_lbl = tk.Label(net_card, text="🌐 " + self.server_url, font=("Consolas", 9, "bold"), fg="#e2e1eb", bg="#1e1f26", anchor="w")
        self.url_lbl.pack(fill="x", pady=1)

        # Status Badges Row
        stat_row = tk.Frame(net_card, bg="#1e1f26")
        stat_row.pack(fill="x", pady=(3, 0))

        self.device_badge = tk.Label(stat_row, text="📱 0 Connected", font=("Segoe UI", 8, "bold"), fg="#ffb955", bg="#12131a", padx=6, pady=2)
        self.device_badge.pack(side="left", padx=(0, 6))

        self.profile_badge = tk.Label(stat_row, text="🎯 Universal", font=("Segoe UI", 8, "bold"), fg="#c1c1ff", bg="#12131a", padx=6, pady=2)
        self.profile_badge.pack(side="left")

        # Action Buttons
        btn_frame = tk.Frame(container, bg="#0e0e11")
        btn_frame.pack(fill="x", pady=(2, 0))

        copy_btn = tk.Button(btn_frame, text="📋 Copy Connection URL", font=("Segoe UI", 10, "bold"), bg="#8083ff", fg="#0c0e14",
                             activebackground="#c1c1ff", activeforeground="#0c0e14", relief="flat", padx=10, pady=5, cursor="hand2",
                             command=self.copy_url)
        copy_btn.pack(fill="x", pady=(0, 4))

        sub_btns = tk.Frame(btn_frame, bg="#0e0e11")
        sub_btns.pack(fill="x")

        regen_btn = tk.Button(sub_btns, text="🔄 New PIN", font=("Segoe UI", 9, "bold"), bg="#33343c", fg="#e2e1eb",
                              activebackground="#383940", activeforeground="#ffffff", relief="flat", pady=4, cursor="hand2",
                              command=self.on_regenerate_pin)
        regen_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

        open_btn = tk.Button(sub_btns, text="🌐 Open Web Deck", font=("Segoe UI", 9, "bold"), bg="#33343c", fg="#e2e1eb",
                             activebackground="#383940", activeforeground="#ffffff", relief="flat", pady=4, cursor="hand2",
                             command=self.open_browser)
        open_btn.pack(side="right", fill="x", expand=True, padx=(2, 0))

    def update_data(self, url, pin, connected_count=0, active_profile="Universal"):
        self.server_url = url
        self.pin = str(pin)
        self.connected_count = connected_count
        self.active_profile = active_profile

        # Update PIN boxes
        for idx, box in enumerate(self.pin_boxes):
            val = self.pin[idx] if idx < len(self.pin) else "-"
            box.config(text=val)

        # Update labels
        self.url_lbl.config(text="🌐 " + self.server_url)
        self.device_badge.config(text=f"📱 {self.connected_count} Connected")
        self.profile_badge.config(text=f"🎯 {self.active_profile}")

        # Generate QR code image
        try:
            qr = qrcode.QRCode(box_size=4, border=1)
            qr.add_data(self.server_url)
            qr.make(fit=True)
            pil_img = qr.make_image(fill_color="#c1c1ff", back_color="#0c0e14").convert("RGB")
            pil_img = pil_img.resize((150, 150), Image.Resampling.NEAREST)
            self.qr_photo = ImageTk.PhotoImage(pil_img)
            self.qr_label.config(image=self.qr_photo)
            self.qr_label.image = self.qr_photo
        except Exception as e:
            print("QR render error:", e)

    def copy_url(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.server_url)
        self._flash_toast("URL copied to clipboard!")

    def copy_pin(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.pin)
        self._flash_toast(f"PIN ({self.pin}) copied!")

    def open_browser(self):
        webbrowser.open(self.server_url)

    def on_regenerate_pin(self):
        if self.regenerate_pin_cb:
            new_pin = self.regenerate_pin_cb()
            if new_pin:
                self.pin = new_pin
                self.update_data(self.server_url, self.pin, self.connected_count, self.active_profile)
                self._flash_toast("New PIN generated!")

    def _flash_toast(self, msg):
        try:
            toast = tk.Toplevel(self.root)
            toast.wm_overrideredirect(True)
            toast.attributes("-topmost", True)
            toast.configure(bg="#e2e1eb")
            
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 100
            y = self.root.winfo_y() + self.root.winfo_height() - 60
            toast.geometry(f"200x28+{x}+{y}")
            
            lbl = tk.Label(toast, text=msg, font=("Segoe UI", 9, "bold"), fg="#12131a", bg="#e2e1eb")
            lbl.pack(expand=True, fill="both")
            toast.after(1500, toast.destroy)
        except Exception:
            pass

    def _update_loop(self):
        if self.get_state:
            try:
                state = self.get_state()
                if state:
                    self.update_data(
                        state.get("url", self.server_url),
                        state.get("pin", self.pin),
                        state.get("connected_count", self.connected_count),
                        state.get("active_profile", self.active_profile)
                    )
            except Exception:
                pass
        self.root.after(1500, self._update_loop)

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = CompanionApp()
    app.update_data("http://192.168.1.15:5000", "482910", 1, "YouTube / Hotstar")
    app.run()
