import os, sys, logging
from pathlib import Path



WIN_HOST = "0.0.0.0"
WIN_PORT = 6001

WSL_HOST = "172.29.130.227"     # dynamically read or configured
WSL_PORT = 6000

PING_INTERVAL = 6  # seconds
WIN_BASE_URL = f"http://{WIN_HOST}:{WIN_PORT}"

WSL_CONNECT_HOST = "172.29.130.227"
WSL_BASE_URL = f"http://{WSL_CONNECT_HOST}:6000"



IS_FROZEN = getattr(sys, "frozen", False)

# Base directory where the app lives (exe dir or project root)
APP_DIR = Path(sys.executable).parent if IS_FROZEN else Path(__file__).resolve().parents[1]

# Base directory for bundled resources (MEIPASS or project root)
RESOURCE_DIR = Path(sys._MEIPASS) if IS_FROZEN else APP_DIR

# Ensure predictable working directory (important for startup)
os.chdir(APP_DIR)


def get_resource_path(relative: str) -> Path:
    """Return absolute path to a bundled resource."""
    return RESOURCE_DIR / "configs" / relative

LOG_FILE = APP_DIR / "logs" / "app.log"
FILE_REGISTRY_PATH = get_resource_path("file_registry.json")
PROCESS_NAMES_PATH = get_resource_path("process_names.json")
SCREENSHOTS_FOLDER = "data/screenshots"
SCREENTIME_DATA = "data/screentime.json"

SCREENTIME_TIMEOUT = 60
SCREENTIME_POLL_INTERVAL = 1.0
SCREENTIME_SAVE_INTERVAL = 60

LOG_LEVEL = logging.INFO

ICON_PATH = get_resource_path("assets/app.ico")
OFFLINE_ICON_PATH = get_resource_path("assets/app_offline.ico")




# UI CONFIGS
WINDOW_HEIGHT = 260
WINDOW_WIDTH = 320
ICON_SIZE = 64

SCREEN_USAGE_WIN_WIDTH = 520 
SCREEN_USAGE_WIN_HEIGHT = 340
