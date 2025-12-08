import subprocess, psutil, os, webbrowser, json, time, pythoncom
import win32gui, win32con, win32process, win32api, win32com.client
from core.registry import action, file_registry
from core.base_module import BaseModule
from configs.config import PROCESS_NAMES_PATH, SCREENSHOTS_FOLDER
from pathlib import Path        
from PIL.ImageGrab import grab






class AppController(BaseModule):
    def __init__(self):
        self.file_registry = file_registry
        # load apps process names
        with open(PROCESS_NAMES_PATH, "r") as file:
            self.process_names = json.load(file)


    # ------------- Launch & close functions ------------ 

    @action(name="open_app", params={"app_name", "app_path", "browser"})
    def open_app(self, app_name: str = None, app_path: str = None, browser: str = "chrome"):
        if app_name:
            app_path = self.file_registry.get_path(app_name)

        if not app_path:
            return self.failure("App path not found.")

        try:
            if isinstance(app_path, str) and app_path.startswith(("http://", "https://")):
                browser_path = self.file_registry.get_path(browser)
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


    @action(name="minimize_app", params={"app_name"})
    def minimize_app(self, app_name: str):
        process = self.process_names.get(app_name, app_name).lower()
        windows = self._get_windows_by_process_and_title(process)

        if not windows:
            return self.failure(f"No visible window found for {process}")

        hwnd = windows[0]["hwnd"]

        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return self.success(f"Minimized {process}", data={"hwnd": hwnd})

        except Exception as e:
            return self.failure(f"Failed to minimize {process}: {e}")
        

    @action(name="maximize_app", params={"app_name"})
    def maximize_app(self, app_name: str):
        process = self.process_names.get(app_name, app_name).lower()
        windows = self._get_windows_by_process_and_title(process)

        if not windows:
            return self.failure(f"No visible window found for {process}")

        hwnd = windows[0]["hwnd"]

        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return self.success(f"Maximized {process}", data={"hwnd": hwnd})

        except Exception as e:
            return self.failure(f"Failed to maximize {process}: {e}")


    @action(name="restore_app", params={"app_name"})
    def restore_app(self, app_name: str):
        process = self.process_names.get(app_name, app_name).lower()
        windows = self._get_windows_by_process_and_title(process)

        if not windows:
            return self.failure(f"No visible window found for {process}")

        hwnd = windows[0]["hwnd"]

        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            return self.success(f"Restored {process}", data={"hwnd": hwnd})

        except Exception as e:
            return self.failure(f"Failed to restore {process}: {e}")


    @action(name="move_resize_app", params={"app_name", "x", "y", "width", "height"})
    def move_resize_app(self, app_name: str, x: int, y: int, width: int, height: int):
        process = self.process_names.get(app_name, app_name).lower()
        windows = self._get_windows_by_process_and_title(process)

        if not windows:
            return self.failure(f"No visible window found for {process}")

        hwnd = windows[0]["hwnd"]

        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # ensure window is not minimized
            win32gui.SetWindowPos(
                hwnd,
                None,
                x, y,
                width, height,
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )
            return self.success(
                f"Moved and resized {process}",
                data={"hwnd": hwnd, "x": x, "y": y, "w": width, "h": height}
            )

        except Exception as e:
            return self.failure(f"Failed to move/resize {process}: {e}")


    @action(name="snap_window", params={"app_name", "position"})
    def snap_window(self, app_name: str, position: str = "right"):
        position = position.lower()
        if position not in ["left", "right", "top", "bottom"]:
            return self.failure("Invalid position. Use left/right/top/bottom.")

        process = self.process_names.get(app_name, app_name).lower()
        windows = self._get_windows_by_process_and_title(process)

        if not windows or process == "explorer" and len(windows) <= 1:
            return self.failure(f"No visible window found for {process}")

        hwnd = windows[0]["hwnd"]

        try:
            screen_w = win32api.GetSystemMetrics(0)
            screen_h = win32api.GetSystemMetrics(1)

            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            if position == "left":
                x, y = 0, 0
                w, h = screen_w // 2, screen_h

            elif position == "right":
                x, y = screen_w // 2, 0
                w, h = screen_w // 2, screen_h

            elif position == "top":
                x, y = 0, 0
                w, h = screen_w, screen_h // 2

            else:  # bottom
                x, y = 0, screen_h // 2
                w, h = screen_w, screen_h // 2

            win32gui.SetWindowPos(
                hwnd,
                None,
                x, y, w, h,
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )

            return self.success(f"Snapped {process} {position}", data={"hwnd": hwnd})

        except Exception as e:
            return self.failure(f"Failed snapping {position}: {e}")


    # --------- Multi instances and state ----------

    @action(name="is_running", params={"app_name"})
    def is_running(self, app_name: str):
        process = self.process_names.get(app_name, app_name).lower()

        try:
            for proc in psutil.process_iter(["name"]):
                try:
                    name = proc.info["name"]
                    if name and name.lower().split(".")[0] == process:
                        return self.success(f"{process} is running", data={"running": True})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return self.failure(f"{process} is not running", data={"running": False})

        except Exception as e:
            return self.failure(f"Error while checking process: {e}", data={"running": False})


    @action(name="list_instances", params={"app_name"})
    def list_instances(self, app_name: str):
        process = self.process_names.get(app_name, app_name).lower()
        instances = []

        try:
            windows = self._get_windows_by_process_and_title(process)
            for w in windows:
                instances.append({
                    "hwnd": w["hwnd"],
                    "title": w["title"],
                    "pid": w["pid"]
                })

            # Include running processes that may not have visible windows
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    name = proc.info["name"]
                    if name and name.lower().split(".")[0] == process:
                        if not any(inst["pid"] == proc.pid for inst in instances):
                            instances.append({
                                "hwnd": None,
                                "title": None,
                                "pid": proc.pid
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if not instances:
                return self.failure(f"No running instances of {process}", data={"instances": []})

            return self.success(f"Found {len(instances)} instances of {process}", data={"instances": instances})

        except Exception as e:
            return self.failure(f"Error listing instances: {e}", data={"instances": []})


    @action(name="switch_instance", params={"app_name", "instance_number"})
    def switch_instance(self, app_name: str, instance_number: int):
        process = self.process_names.get(app_name, app_name).lower()
        instances_result = self.list_instances(app_name)

        if not instances_result["success"] or not instances_result["data"]["instances"]:
            return self.failure(f"No running instances of {process} to switch")

        instances = instances_result["data"]["instances"]

        if instance_number < 1 or instance_number > len(instances):
            return self.failure(f"Instance number {instance_number} out of range (1-{len(instances)})")

        target = instances[instance_number - 1]
        hwnd = target.get("hwnd")
        pid = target.get("pid")
        title = target.get("title") or f"PID {pid}"

        if hwnd is None:
            return self.failure(f"Instance {instance_number} ({title}) has no visible window to focus")

        try:
            # Restore window if minimized
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # Proper focus handling
            fg = win32gui.GetForegroundWindow()
            fg_thread, _ = win32process.GetWindowThreadProcessId(fg)
            target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)

            win32process.AttachThreadInput(fg_thread, target_thread, True)
            win32gui.SetForegroundWindow(hwnd)
            win32process.AttachThreadInput(fg_thread, target_thread, False)

            return self.success(f"Switched focus to instance {instance_number} ({title})", data={"hwnd": hwnd, "pid": pid})

        except Exception as e:
            return self.failure(f"Failed to switch to instance {instance_number} ({title}): {e}")


    # --------- Shortcuts or automation ---------------

    @action(name="send_key", params={"app_name", "key_combo"})
    def send_key(self, app_name: str, key_combo: str):
        windows = self._get_windows_by_process_and_title(self.process_names.get(app_name, app_name))
        if not windows:
            return self.failure(f"No visible window found for {app_name}")

        hwnd = windows[0]["hwnd"]

        try:
            # Focus window first
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            fg = win32gui.GetForegroundWindow()
            fg_thread, _ = win32process.GetWindowThreadProcessId(fg)
            target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
            win32process.AttachThreadInput(fg_thread, target_thread, True)
            win32gui.SetForegroundWindow(hwnd)
            win32process.AttachThreadInput(fg_thread, target_thread, False)

            # Parse simple key combos like "ctrl+c", "alt+tab"
            keys = key_combo.lower().split("+")
            key_map = {
                "ctrl": win32con.VK_CONTROL,
                "alt": win32con.VK_MENU,
                "shift": win32con.VK_SHIFT,
                "win": win32con.VK_LWIN,
            }

            # Press keys down
            for k in keys:
                vk = key_map.get(k, ord(k.upper()))
                win32api.keybd_event(vk, 0, 0, 0)
                time.sleep(0.02)

            # Release keys
            for k in reversed(keys):
                vk = key_map.get(k, ord(k.upper()))
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.02)

            return self.success(f"Sent key combo '{key_combo}' to {app_name}", data={"hwnd": hwnd})

        except Exception as e:
            return self.failure(f"Failed to send key combo to {app_name}: {e}")


    @action(name="send_text", params={"app_name", "text"})
    def send_text(self, app_name: str, text: str):
        windows = self._get_windows_by_process_and_title(self.process_names.get(app_name, app_name))
        if not windows:
            return self.failure(f"No visible window found for {app_name}")

        hwnd = windows[0]["hwnd"]

        try:
            # Focus window first
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            fg = win32gui.GetForegroundWindow()
            fg_thread, _ = win32process.GetWindowThreadProcessId(fg)
            target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
            win32process.AttachThreadInput(fg_thread, target_thread, True)
            win32gui.SetForegroundWindow(hwnd)
            win32process.AttachThreadInput(fg_thread, target_thread, False)

            # Type each character
            for char in text:
                vk = ord(char.upper())
                win32api.keybd_event(vk, 0, 0, 0)
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.02)

            return self.success(f"Sent text to {app_name}", data={"hwnd": hwnd})

        except Exception as e:
            return self.failure(f"Failed to send text to {app_name}: {e}")
        

    @action(name="screenshot_app", params={"app_name"})
    def screenshot_app(self, app_name: str):
        windows = self._get_windows_by_process_and_title(self.process_names.get(app_name, app_name))
        if not windows:
            return self.failure(f"No visible window found for {app_name}")

        hwnd = windows[0]["hwnd"]

        try:
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            left, top = win32gui.ClientToScreen(hwnd, (left, top))
            right, bottom = win32gui.ClientToScreen(hwnd, (right, bottom))

            img = grab(bbox=(left, top, right, bottom))

            
            os.makedirs(SCREENSHOTS_FOLDER, exist_ok=True)
            temp_path = f"{SCREENSHOTS_FOLDER}/{app_name}_screenshot.png"
            img.save(temp_path)

            return self.success(f"Screenshot captured for {app_name}", data={"hwnd": hwnd, "path": temp_path})

        except Exception as e:
            return self.failure(f"Failed to capture screenshot for {app_name}: {e}")


    # ----------- Advanced Controls ---------------

    @action(name="pin_to_taskbar", params={"app_name"})
    def pin_to_taskbar(self, app_name: str):
        path = self.file_registry.get_path(app_name)
        if not path:
            return self.failure(f"Path not found for {app_name}")

        path = Path(path)
        if not path.exists() or not path.is_file():
            return self.failure(f"Invalid file path: {path}")

        try:
            pythoncom.CoInitialize()
            shell = win32com.client.Dispatch("Shell.Application")
            folder = shell.NameSpace(str(path.parent))
            item = folder.ParseName(path.name)

            # Check if 'Pin to Taskbar' verb exists
            verbs = [v.Name.lower() for v in item.Verbs()]
            if "pin to taskbar" in verbs:
                for v in item.Verbs():
                    if v.Name.lower() == "pin to taskbar":
                        v.DoIt()
                        return self.success(f"Pinned {app_name} to taskbar")
            else:
                return self.failure(f"'Pin to Taskbar' not available for {app_name}")

        except Exception as e:
            return self.failure(f"Failed to pin {app_name}: {e}")
        

    @action(name="unpin_from_taskbar", params={"app_name"})
    def unpin_from_taskbar(self, app_name: str):
        path = self.file_registry.get_path(app_name)
        if not path:
            return self.failure(f"Path not found for {app_name}")

        path = Path(path)
        if not path.exists() or not path.is_file():
            return self.failure(f"Invalid file path: {path}")

        try:
            shell = win32com.client.Dispatch("Shell.Application")
            folder = shell.NameSpace(str(path.parent))
            item = folder.ParseName(path.name)

            # Check if 'Unpin from Taskbar' verb exists
            verbs = [v.Name.lower() for v in item.Verbs()]
            if "unpin from taskbar" in verbs:
                for v in item.Verbs():
                    if v.Name.lower() == "unpin from taskbar":
                        v.DoIt()
                        return self.success(f"Unpinned {app_name} from taskbar")
            else:
                return self.failure(f"'Unpin from Taskbar' not available for {app_name}")

        except Exception as e:
            return self.failure(f"Failed to unpin {app_name}: {e}")
        
        finally:
            pythoncom.CoUninitialize()


    @action(name="get_app_info", params={"app_name"})
    def get_app_info(self, app_name: str):
        import psutil
        from pathlib import Path
        import win32process

        path = self.file_registry.get_path(app_name)
        if not path:
            return self.failure(f"Path not found for {app_name}")

        process_name = self.process_names.get(app_name, app_name).lower()
        instances = []

        # Gather all running instances
        for proc in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                if proc.info["name"] and proc.info["name"].lower().split(".")[0] == process_name:
                    mem = proc.info.get("memory_info")
                    mem_usage = mem.rss if mem else None
                    instances.append({
                        "pid": proc.pid,
                        "memory": mem_usage
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Attempt to get version info
        version = None
        exe_path = Path(path)
        if exe_path.exists() and exe_path.is_file():
            try:
                import win32api
                info = win32api.GetFileVersionInfo(str(exe_path), "\\")
                ms = info['FileVersionMS']
                ls = info['FileVersionLS']
                version = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
            except:
                pass

        return self.success(
            f"App info for {app_name}",
            data={
                "path": path,
                "version": version,
                "instances": instances
            }
        )



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
            

            if proc.name().lower().split(".")[0] != target_proc.lower():
                return

            title = win32gui.GetWindowText(hwnd)
            if title and (target_title is None or target_title.lower() in title.lower()):
                results.append({"hwnd": hwnd, "title": title, "pid": pid})

        win32gui.EnumWindows(callback, None)
        return results
