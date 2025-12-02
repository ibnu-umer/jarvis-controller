import threading
import time
import webbrowser
import requests
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as Item, Menu
import ctypes
from configs.config import WIN_BASE_URL, WSL_BASE_URL





class JarvisTray:
    ICON_SIZE = (64, 64)
    TEXT_ICON_CHAR = "J"
    PING_INTERVAL = 6  # seconds

    def __init__(self, backend_base=WSL_BASE_URL, ui_url=WIN_BASE_URL):
        self.backend_base = backend_base.rstrip("/")
        self.ui_url = ui_url

        self.healthy = False
        self.last_checked = None
        self.tray_icon = None
        self.stop_event = threading.Event()
        self.bg_thread = None

    # --- Icon ---
    def make_icon(self) -> Image.Image:
        size = self.ICON_SIZE
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        bbox = [4, 4, size[0]-4, size[1]-4]
        color = (88, 214, 141, 255) if self.healthy else (239, 68, 68, 255)
        draw.ellipse(bbox, fill=color)

        try:
            f = ImageFont.truetype("Segoe UI.ttf", 28)
        except Exception:
            f = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), self.TEXT_ICON_CHAR, font=f)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text(((size[0]-w)/2, (size[1]-h)/2), self.TEXT_ICON_CHAR, fill=(255,255,255,255), font=f)
        return img

    # --- Backend ping ---
    def backend_ping(self) -> bool:
        url = f"{self.backend_base}/health"
        try:
            r = requests.get(url, timeout=2)
            return r.status_code == 200
        except requests.RequestException:
            return False

    # --- Menu ---
    def build_menu(self):
        status_item = Item(f"Backend: {'OK' if self.healthy else 'DOWN'}", lambda icon, item: None, enabled=False)
        last_item = Item(f"Last: {self.last_checked if self.last_checked else 'never'}", lambda icon, item: None, enabled=False)

        open_item = Item("Open UI", self.open_ui)
        reload_item = Item("Ping backend", self.reload_now)
        refresh_item = Item("Refresh Data", lambda icon, item: self.call_action("refresh"))
        quit_item = Item("Quit", self.quit_app)

        return Menu(
            status_item,
            last_item,
            Menu.SEPARATOR,
            open_item,
            reload_item,
            Menu.SEPARATOR,
            refresh_item,
            Menu.SEPARATOR,
            quit_item
        )

    def update_menu(self):
        if self.tray_icon:
            self.tray_icon.menu = self.build_menu()
            self.tray_icon.icon = self.make_icon()

    # --- Background ---
    def health_worker(self):
        while not self.stop_event.is_set():
            self.healthy = self.backend_ping()
            self.last_checked = time.strftime("%Y-%m-%d %H:%M:%S")
            self.update_menu()
            for _ in range(int(self.PING_INTERVAL*10)):
                if self.stop_event.is_set():
                    break
                time.sleep(0.1)

    # --- Actions ---
    def open_ui(self, icon=None, item=None):
        webbrowser.open(self.ui_url)

    def reload_now(self, icon=None, item=None):
        self.healthy = self.backend_ping()
        self.last_checked = time.strftime("%Y-%m-%d %H:%M:%S")
        self.update_menu()

    def call_action(self, action_name):
        url = f"{self.backend_base}/action/{action_name}"
        print("calling action: ", url)
        try:
            r = requests.post(url, timeout=3)
            if r.status_code == 200:
                print(f"Action {action_name} OK: {r.text}")
            else:
                print(f"Action {action_name} returned {r.status_code}: {r.text}")
        except Exception as e:
            print("Action call failed:", e)
        self.reload_now()

    def quit_app(self, icon=None, item=None):
        print("Quitting tray...")
        self.stop_event.set()
        if self.tray_icon:
            self.tray_icon.stop()

    @staticmethod
    def confirm_with_popup(message, title="Confirm"):
        MB_YESNO = 0x04
        IDYES = 6

        # Ensure the message box is always on top and attached to active window
        MB_TOPMOST = 0x00040000
        MB_SETFOREGROUND = 0x00010000

        hwnd = ctypes.windll.user32.GetForegroundWindow()

        return ctypes.windll.user32.MessageBoxW(
            hwnd, message, title, MB_YESNO | MB_TOPMOST | MB_SETFOREGROUND
        ) == IDYES

    # --- Run ---
    def run(self):
        # Optional: start Windows listener if needed
        try:
            from src.api.listener import run_server
            run_server()
        except ImportError:
            pass

        self.tray_icon = pystray.Icon("jarvis-tray", self.make_icon(), "Jarvis", self.build_menu())
        self.bg_thread = threading.Thread(target=self.health_worker, daemon=True)
        self.bg_thread.start()

        try:
            self.tray_icon.run()
        finally:
            self.stop_event.set()
            self.bg_thread.join(timeout=2)
            print("Tray stopped.")


