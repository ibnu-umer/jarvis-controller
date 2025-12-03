import sys
import os
import threading

# Add src folder to sys.path
SRC_PATH = os.path.join(os.path.dirname(__file__), "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from tray.tray_app import JarvisTray
from api.listener import WindowsListener 
from core.registry import load_registry






def run_tray():
    tray = JarvisTray()
    tray.run()




if __name__ == "__main__":
    load_registry()

    windows_listener = WindowsListener()
    listener_thread = threading.Thread(target=windows_listener.start, daemon=True)
    listener_thread.start()


    run_tray()
