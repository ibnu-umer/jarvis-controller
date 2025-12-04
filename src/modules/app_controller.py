import subprocess, psutil, os, webbrowser, json, win32gui, win32con, win32process
from core.registry import action, registry
from core.base_module import BaseModule
from configs.config import PROCESS_NAMES_PATH
from core.logger import logger





class AppController(BaseModule):
    def __init__(self):
        self.registry = registry
        # load apps process names
        with open(PROCESS_NAMES_PATH, "r") as file:
            self.process_names = json.load(file)


    @action(name="open_app", params={"app_name", "app_path", "browser"})
    def open_app(self, app_name: str = None, app_path: str = None, browser: str = "chrome"):
        if app_name:
            app_path = self.registry.get_path(app_name)

        if not app_path:
            return self.failure("App path not found.")

        try:
            if isinstance(app_path, str) and app_path.startswith(("http://", "https://")):
                browser_path = self.registry.get_path(browser)
                webbrowser.get(f'"{browser_path}" %s').open(app_path)
            else:
                from pathlib import Path
                path = Path(app_path)

                if path.exists() and path.is_file() and path.suffix.lower() in (".exe", ".bat", ".cmd", ".msi"):
                    subprocess.Popen([str(path)])
                elif path.exists() and path.is_file():
                    os.startfile(str(path))
                else:
                    subprocess.Popen([app_path])

            return self.success(f"App opened successfully: {app_path}")
        except Exception as e:
            return self.failure(f"Error opening {app_path}: {e}")
            

    @action(name="close_app", params={"app_name"})
    def close_app(self, app_name: str):
        process_name = self.process_names.get(app_name, app_name).lower()
        closed = False

        def enum_window_callback(hwnd, _):
            nonlocal closed
            if not win32gui.IsWindowVisible(hwnd) or not win32gui.GetWindowText(hwnd):
                return True

            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                exe = proc.name().lower()
                if exe.split(".")[0] == process_name:
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    closed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            return True

        try:
            win32gui.EnumWindows(enum_window_callback, None)
        except Exception:
            pass

        if closed:
            return self.success(f"Closed {app_name}", data={"closed": True})

        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] and proc.info["name"].lower().split(".")[0] == process_name:
                    return self.failure(
                        f"{app_name} running in background but has no window to close.",
                        data={"closed": False, "background": True}
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return self.failure(f"No running instance of {app_name}", data={"closed": False})
    

    @action(name="focus_app", params={"app_name"})
    def focus_app(self, app_name: str):
        if app_name in self.process_names:
            app_name = self.process_names[app_name].lower()

        focused = False

        def callback(hwnd, _):
            nonlocal focused
            title = win32gui.GetWindowText(hwnd).lower()

            if app_name in title and win32gui.IsWindowVisible(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # if minimized
                win32gui.SetForegroundWindow(hwnd)
                focused = True
                return False  

            return True 

        try:
            win32gui.EnumWindows(callback, None)
        except Exception as e:
            logger.error(f"Error while focusing windows: {e}")

        if focused:
            return self.success(f"Focus changed to {app_name}")
        else:
            return self.failure(f"No window found for {app_name}")


