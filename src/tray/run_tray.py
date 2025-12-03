import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(ROOT)

from src.tray.tray_app import JarvisTray

if __name__ == "__main__":
    tray_app = JarvisTray()
    tray_app.run()