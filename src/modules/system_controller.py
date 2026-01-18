import subprocess, pytz, psutil, pyperclip
from core.registry import action
from core.base_module import BaseModule
from datetime import datetime, timedelta
from pathlib import Path




class SystemController(BaseModule):
    NIRCMD = r"C:\Tools\nircmd\nircmd.exe"

    def _run(self, cmd):
        subprocess.Popen(cmd, shell=True)

    @action(name="shutdown")
    def shutdown(self):
        self._run("shutdown /s /t 0")
        return self.success("Shutting down")
    

    @action(name="restart")
    def restart(self):
        self._run("shutdown /r /t 0")
        return self.success("Restarting")


    @action(name="logout")
    def logout(self):
        self._run("shutdown /l")
        return self.success("Logging out")
    

    @action(name="sleep")
    def sleep(self):
        self._run("powershell -command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)\"")
        return self.success("Sleeping")
    

    @action(name="lock")
    def lock(self):
        self._run("rundll32.exe user32.dll,LockWorkStation")
        return self.success("Locked")
    

    @action(name="brightness", params={"value", "mode"})
    def set_brightness(self, value, mode="set"):
        if mode not in ("set", "inc", "dec"):
            return self.failure("Invalid mode")
        
        value = 10 if value is None else value

        if mode == "inc":
            self._run(f"\"{self.NIRCMD}\" changebrightness {value}")
            return self.success(f"Brightness increased by {value}%")

        if mode == "dec":
            self._run(f"\"{self.NIRCMD}\" changebrightness -{value}")
            return self.success(f"Brightness decreased by {value}%")

        value = max(0, min(100, value))
        self._run(f"\"{self.NIRCMD}\" setbrightness {value}")
        return self.success(f"Brightness set to {value}%")
    

    @action(name="volume", params={"value", "mode"})
    def set_volume(self, value = None, mode="set"):
        if mode not in ("set", "inc", "dec"):
            return self.failure("Invalid mode")
        
        value = 10 if value is None else value
        
        if mode == "inc":
            self._run(f"\"{self.NIRCMD}\" changesysvolume {int(65535 * (value / 100))}")
            return self.success(f"Volume increased by {value}%")

        if mode == "dec":
            self._run(f"\"{self.NIRCMD}\" changesysvolume -{int(65535 * (value / 100))}")
            return self.success(f"Volume decreased by {value}%")

        system_value = int(65535 * (value / 100))
        self._run(f"\"{self.NIRCMD}\" setsysvolume {system_value}")
        return self.success(f"Volume set to {value}%")
    

    @action(name="get_datetime", params={"get", "day"})
    def get_datetime(self, get, day="today"):
        tz = pytz.timezone("Asia/Kolkata")
        now = datetime.now(tz)
        if day == "yesterday":
            target = now - timedelta(days=1)
        elif day == "tomorrow":
            target = now + timedelta(days=1)
        else:
            target = now

        date_str = target.strftime("%A, %d %B %Y")
        time_str = target.strftime("%I:%M %p")
        day_str = target.strftime("%A")

        messages = {
            "time": f"The time is {time_str}",
            "date": f"{day} is {date_str}",
            "day": f"Its {day_str}"
        }
        
        if get not in messages:
            return self.failure("Invalid get value")
        
        return self.success(
            messages.get(get)
        )
    

    @action(name="get_battery_status", params={"get"})
    def get_battery_status(self, get):
        battery = psutil.sensors_battery()
        percent, plugged = battery.percent, battery.power_plugged
        messages = {
            "level": f"its {percent}%",
            "plugged": "yes it is plugged" if plugged else "Not plugged",
            "status": f"{percent}% battery level and {"" if plugged else "not"} charging"
        }
        return self.success(
            messages.get(get),
            data={"percent": percent, "plugged": plugged}
        )
    

    @action(name="wifi", params={"mode"})
    def toggle_wifi(self, mode):
        interface_name = "WiFi"

        if mode == "enable":
            self._run(f"netsh interface set interface {interface_name} enable")
            return self.success("Wi-Fi enable")

        elif mode == "disabled":
            self._run(f"netsh interface set interface {interface_name} disable")
            return self.success("Wi-Fi disabled")
        
        elif mode == "disconnect":
            self._run("netsh wlan disconnect")
            return self.success("Wi-Fi disconnected")

        return self.failure("Invalid mode")


    @action(name="bluetooth", params={"mode"})
    def toggle_bluetooth(self, mode):
        if mode == "enable":
            self._run('powershell "Get-PnpDevice -Class Bluetooth | Enable-PnpDevice -Confirm:$false"')
            return self.success("Bluetooth enabled")

        if mode == "disable":
            self._run('powershell "Get-PnpDevice -Class Bluetooth | Disable-PnpDevice -Confirm:$false"')
            return self.success("Bluetooth disabled")

        return self.failure("Invalid mode")


    @action(name="get_copied_value", params={"_as"})
    def get_copied_value(self, _as=None):
        copied = pyperclip.paste().strip()

        if not copied:
            return self.failure("Clipboard is empty")

        if _as == "path":
            path_obj = Path(copied)
            if not path_obj.exists():
                
                return self.failure(f"Path does not exist: {copied[:10]}...")

            if path_obj.is_file():
                return self.success("Clipboard value as path", data={
                    "folder": str(path_obj.parent.resolve()),
                    "file": path_obj.name
                })
            else:
                return self.success("Clipboard value as path", data={
                    "folder": str(path_obj.resolve()),
                    "file": None
                })

        return self.success("Clipboard value", data={"text": copied})


    @action(name="resolve_path", params={"path"})
    def resolve_path(self, path: str):

        if not path:
            raise ValueError("No path provided")

        raw_path = path.strip()
        path_obj = Path(raw_path)

        if not path_obj.exists():
            raise ValueError(f"Path does not exist: {raw_path}")

        if path_obj.is_file():
            return {"folder": str(path_obj.parent), "file": path_obj.name}

        return {"folder": str(path_obj), "file": None}
    



if __name__ == "__main__":
    sc = SystemController()
    print(sc.lock())
