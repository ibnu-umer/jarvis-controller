import subprocess, psutil, os, webbrowser, json, win32gui, win32con, win32process
from core.registry import action, registry
from core.base_module import BaseModule
from configs.config import PROCESS_NAMES_PATH
from core.logger import logger
from pathlib import Path





class AppController(BaseModule):
    def __init__(self):
        self.registry = registry
        # load apps process names
        with open(PROCESS_NAMES_PATH, "r") as file:
            self.process_names = json.load(file)

        self.UWP_HOSTS = ("applicationframehost")


    # ------------- Launch & close functions ------------ 

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
            elif isinstance(app_path, str) and app_path.startswith("ms"):
                subprocess.run(f'start "" "{app_path}"', shell=True)
            else:
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
        windows = self._get_app_windows(process_name)

        if not windows:
            return self.failure(f"No visible window found for {app_name}")
        
        if process_name == "explorer" and len(windows) <= 1:
            return self.failure(f"No visible window found for explorer")
        print(windows)
        
        hwnd = windows[0]
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        return self.success(f"Closed one instance of {app_name}", data={"hwnd": hwnd, "closed": True})
    

    @action(name="close_all_instances", params={"app_name", "force"})
    def close_all_instances(self, app_name: str, force: bool = False):
        process_name = self.process_names.get(app_name, app_name).lower()

        if force:  # Kill every instances on the process directly
            
            if process_name == "explorer":
                return self.failure("Cannot force stop explorer")  # it will distroy other windows tools

            killed = 0
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if proc.info["name"] and proc.info["name"].lower().split(".")[0] == process_name:
                        proc.kill()
                        killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if killed == 0:
                return self.failure(f"No running processes found for {app_name}", data={"killed": 0})

            return self.success(f"Force-killed {killed} instances of {app_name}", data={"killed": killed})

        # Close all visible windows of the process
        windows = self._get_app_windows(process_name)

        if not windows:
            return self.failure(f"No visible windows found for {app_name}", data={"closed": 0})

        closed_count = 0
        for hwnd in windows:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                closed_count += 1
            except:
                pass

        return self.success(
            f"Closed {closed_count} visible windows of {app_name}",
            data={"closed": closed_count}
        )


    # --------- Helpers -------------

    def _get_app_windows(self, process_name: str):
        windows = []
        process_name = self.process_names.get(process_name, process_name)
       
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    proc = psutil.Process(pid)
                    exe = proc.name().lower().split(".")[0]
                    if exe == process_name  or exe in self.UWP_HOSTS:
                        windows.append(hwnd)
                except:
                    pass
            return True

        win32gui.EnumWindows(callback, None)
        return windows


    # ------------- Window management --------------

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


