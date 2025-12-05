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
        windows = self._get_windows_by_process_and_title(process_name)
        if not windows: # if not got, then check for the applicationframehost
            windows = self._get_windows_by_process_and_title("applicationframehost", process_name)

        if not windows:
            return self.failure(f"No visible window found for {app_name}")
        
        if process_name == "explorer" and len(windows) <= 1:
            return self.failure(f"No visible window found for explorer")
        
        hwnd = windows[0]["hwnd"]
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


    # ------------- Window management --------------

    @action(name="focus_app", params={"app_name"})
    def focus_app(self, app_name: str):
        process_name = self.process_names.get(app_name, app_name).lower()
        windows = self._get_windows_by_process_and_title(process_name)
        if not windows: # if not got, then check for the applicationframehost
            windows = self._get_windows_by_process_and_title("applicationframehost", process_name)

        if not windows:
            return self.failure(f"No visible window found for {process_name}")

        # The first verified match
        hwnd = windows[0]["hwnd"]   
        title = windows[0]["title"]

        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            fg = win32gui.GetForegroundWindow()
            fg_thread, _ = win32process.GetWindowThreadProcessId(fg)
            target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)

            win32process.AttachThreadInput(fg_thread, target_thread, True)
            win32gui.SetForegroundWindow(hwnd)
            win32process.AttachThreadInput(fg_thread, target_thread, False)

            return self.success(f"Focused {title}", data={"hwnd": hwnd})

        except Exception as e:
            return self.failure(f"Failed to focus window: {e}")





    # --------- Helpers -------------

    def _get_windows_by_process_and_title(self, target_proc, target_title=None):
        results = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd) or not win32gui.IsWindowEnabled(hwnd):
                return

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                proc = psutil.Process(pid)
            except psutil.NoSuchProcess:
                return
            
            # print(target_proc, proc.name())

            if proc.name().lower().split(".")[0] != target_proc.lower():
                return

            title = win32gui.GetWindowText(hwnd)
            if title and (target_title is None or target_title.lower() in title.lower()):
                results.append({"hwnd": hwnd, "title": title, "pid": pid})

        win32gui.EnumWindows(callback, None)
        return results
