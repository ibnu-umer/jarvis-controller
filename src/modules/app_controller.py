import subprocess, psutil, os, webbrowser
from core.registry import action, registry
from core.base_module import BaseModule





class AppController(BaseModule):
    registry = registry

    @action("open_app", params={"app_name", "app_path", "browser"})
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
    def close_app(self, app_name: str = None):
        closed = False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() == app_name.lower():
                try:
                    proc.terminate()
                    closed = True
                except Exception as e:
                    self.failure(f"Error closing {app_name}: {e}")
        return self.success(f"App closed: {closed}")


    @action(name="is_running", params={"app_name"})
    def is_app_running(self, app_name: str) -> bool:
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == app_name.lower():
                    return self.success(f"App is running: {app_name}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return self.failure(f"App is not running: {app_name}")
