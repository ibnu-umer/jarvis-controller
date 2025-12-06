import os, sys




WIN_HOST = "0.0.0.0"
WIN_PORT = 6001

WSL_HOST = "172.29.128.1"     # dynamically read or configured
WSL_PORT = 6000

PING_INTERVAL = 6  # seconds
WIN_BASE_URL = f"http://{WIN_HOST}:{WIN_PORT}"
WSL_BASE_URL = f"http://{WSL_HOST}:{WSL_PORT}"



def get_resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, f"configs/{relative}")
    return os.path.join(os.path.dirname(__file__), relative)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = "logs/app.log"

FILE_REGISTRY_PATH = get_resource_path("file_registry.json")
PROCESS_NAMES_PATH = get_resource_path("process_names.json")
SCREENSHOTS_FOLDER = "data/screenshots"
