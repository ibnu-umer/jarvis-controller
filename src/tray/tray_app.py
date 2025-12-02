# jarvis_tray.py
import threading
import time
import webbrowser
import requests
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as Item, Menu
import ctypes





BACKEND_BASE = "http://127.0.0.1:6000"       # your Jarvis backend
HEALTH_ENDPOINT = "/health"                 # must return 200 for OK
UI_URL = "http://127.0.0.1:6000"            # url to open with "Open UI"
PING_INTERVAL = 6                           # seconds between health checks
ICON_SIZE = (64, 64)
TEXT_ICON_CHAR = "J"


# Internal state
_state = {
    "healthy": False,
    "last_checked": None,
    "tray": None,   # will hold pystray.Icon instance
    "menu_items": {}
}

def make_icon(healthy: bool) -> Image.Image:
    """Create a small dynamic icon: green circle when healthy, red when not."""
    size = ICON_SIZE
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # background circle
    bbox = [4, 4, size[0]-4, size[1]-4]
    color = (88, 214, 141, 255) if healthy else (239, 68, 68, 255)
    draw.ellipse(bbox, fill=color)

    # center letter
    try:
        f = ImageFont.truetype("Segoe UI.ttf", 28)
    except Exception:
        f = ImageFont.load_default()

    # compute text width/height
    bbox = draw.textbbox((0, 0), TEXT_ICON_CHAR, font=f)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    draw.text(((size[0]-w)/2, (size[1]-h)/2), TEXT_ICON_CHAR, fill=(255,255,255,255), font=f)
    return img

def backend_ping() -> bool:
    url = BACKEND_BASE.rstrip("/") + HEALTH_ENDPOINT
    try:
        r = requests.get(url, timeout=2)
        return r.status_code == 200
    except requests.RequestException:
        return False

def build_menu():
    status_text = "Backend: OK" if _state["healthy"] else "Backend: DOWN"
    last_text = f"Last: {_state['last_checked']}" if _state["last_checked"] else "Last: never"

    return pystray.Menu(
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.MenuItem(last_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open UI", open_ui),
        pystray.MenuItem("Ping backend", reload_now),
        pystray.MenuItem("Do Shutdown (backend)", lambda icon, item: call_action(icon, item, "shutdown")),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )


def _update_menu_labels():
    if _state["tray"]:
        _state["tray"].menu = build_menu()
        _state["tray"].icon = make_icon(_state["healthy"])

def health_worker(stop_event: threading.Event):
    """Background loop that pings backend and updates the tray."""
    while not stop_event.is_set():
        healthy = backend_ping()
        _state["healthy"] = healthy
        _state["last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
        # Update menu labels on main thread via Icon.update_menu will be okay
        _update_menu_labels()
        # Sleep but wake sooner if asked to stop
        for _ in range(int(PING_INTERVAL*10)):
            if stop_event.is_set():
                break
            time.sleep(0.1)

def open_ui(icon, item):
    webbrowser.open(UI_URL)

def reload_now(icon, item):
    """Manual ping and keep menu in sync."""
    ok = backend_ping()
    _state["healthy"] = ok
    _state["last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _update_menu_labels()

def call_action(icon, item, action_name):
    """Call an arbitrary action on backend (POST). Example: POST /action/shutdown"""
    url = f"{BACKEND_BASE.rstrip('/')}/action/{action_name}"
    try:
        r = requests.post(url, timeout=3)
        if r.status_code == 200:
            # optionally show a temporary notification (platform dependent)
            print(f"Action {action_name} OK: {r.text}")
        else:
            print(f"Action {action_name} returned {r.status_code}: {r.text}")
    except Exception as e:
        print("Action call failed:", e)
    # update health after action
    reload_now(icon, item)

def quit_app(icon, item):
    # stop background thread and shutdown tray
    print("Quitting tray...")
    stop_event.set()
    icon.stop()

def build_menu():
    # Dynamic status items
    status_item = Item("Backend: checking...", lambda icon, item: None, enabled=False)
    last_item = Item("Last: never", lambda icon, item: None, enabled=False)

    # Static actions
    open_item = Item("Open UI", open_ui)
    reload_item = Item("Ping backend", reload_now)

    refresh_item = Item(
        "Refresh Data",
        lambda icon, item: call_action(icon, item, "refresh")
    )

    # Quit
    quit_item = Item("Quit", quit_app)

    # Store references for dynamic updates
    _state["menu_items"]["status"] = status_item
    _state["menu_items"]["last_checked"] = last_item

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


def send_intent(name, payload=None):
    try:
        requests.post("http://127.0.0.1:6000/intent", json={
            "intent": name,
            "payload": payload or {}
        })
    except:
        print("Intent send failed")

menu = (
    Item("Restart Backend", lambda _: send_intent("restart_backend")),
    Item("Shutdown", lambda _: send_intent("shutdown")),
    Item("Refresh", lambda _: send_intent("refresh")),
    Item("Quit", quit_app)
)



def confirm_with_popup(message, title="Confirm"):
    MB_YESNO = 0x04
    IDYES = 6
    result = ctypes.windll.user32.MessageBoxW(0, message, title, MB_YESNO)
    return result == IDYES




# Main entry
if __name__ == "__main__":
    from src.api.listener import run_server
    run_server()


    stop_event = threading.Event()

    icon_image = make_icon(False)
    menu = build_menu()
    tray_icon = pystray.Icon("jarvis-tray", icon_image, "Jarvis", menu)
    _state["tray"] = tray_icon

    # Start background thread
    bg_thread = threading.Thread(target=health_worker, args=(stop_event,), daemon=True)
    bg_thread.start()

    try:
        tray_icon.run()  # blocks until icon.stop()
    except KeyboardInterrupt:
        quit_app(tray_icon, None)
    finally:
        stop_event.set()
        bg_thread.join(timeout=2)
        print("Tray stopped.")
