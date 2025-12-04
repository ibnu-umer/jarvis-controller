import subprocess
from core.registry import action
from core.base_module import BaseModule
from tray.tray_app import JarvisTray
from datetime import datetime
import pytz, psutil




class SystemController(BaseModule):
    NIRCMD = r"C:\Tools\nircmd\nircmd.exe"

    def _run(self, cmd):
        subprocess.Popen(cmd, shell=True)

    @action(name="shutdown")
    def shutdown(self):
        if JarvisTray.confirm_with_popup("Shutdown in 5 seconds?", "Confirm Shutdown"):
            self._run("shutdown /s /t 0")
            return self.success("Shutting down")
        return self.success("Cancelled")
    

    @action(name="restart")
    def restart(self):
        if JarvisTray.confirm_with_popup("Restart in 5 seconds?", "Confirm Restart"):
            self._run("shutdown /r /t 0")
            return self.success("Restarting")
        return self.success("Cancelled")
    

    @action(name="logout")
    def logout(self):
        if JarvisTray.confirm_with_popup("Logout in 5 seconds?", "Confirm Logout"):
            self._run("shutdown /l")
            return self.success("Logging out")
        return self.success("Cancelled")
    

    @action(name="sleep")
    def sleep(self):
        if JarvisTray.confirm_with_popup("Sleep in 5 seconds?", "Confirm Sleep"):
            self._run("powershell -command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)\"")
            return self.success("Sleeping")
        return self.success("Cancelled")
    

    @action(name="lock")
    def lock(self):
        if JarvisTray.confirm_with_popup("Lock in 5 seconds?", "Confirm Lock?"):
            self._run("rundll32.exe user32.dll,LockWorkStation")
            return self.success("Locked")
        return self.success("cancelled")
    

    @action(name="brightness", params={"value", "mode"})
    def set_brightness(self, value, mode="set"):
        if mode not in ("set", "inc", "dec"):
            return self.failure("Invalid mode")
        
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
    def set_volume(self, value, mode="set"):
        if mode not in ("set", "inc", "dec"):
            return self.failure("Invalid mode")
        
        if mode == "inc":
            self._run(f"\"{self.NIRCMD}\" changesysvolume {int(65535 * (value / 100))}")
            return self.success(f"Volume increased by {value}%")

        if mode == "dec":
            self._run(f"\"{self.NIRCMD}\" changesysvolume -{int(65535 * (value / 100))}")
            return self.success(f"Volume decreased by {value}%")

        system_value = int(65535 * (value / 100))
        self._run(f"\"{self.NIRCMD}\" setsysvolume {system_value}")
        return self.success(f"Volume set to {value}%")
    

    @action(name="datetime")
    def get_datetime(self):
        tz = pytz.timezone("Asia/Kolkata")
        now = datetime.now(tz)
        date, day, time = now.date(), now.strftime("%A"), now.strftime("%H:%M:%S")
        return self.success(
            f"Datetime fetched successfully.",
            data={"day": day, "time": str(time), "date": str(date)}
        )
    

    @action(name="battery")
    def get_battery_status(self):
        battery = psutil.sensors_battery()
        return self.success(
            f"Battery status fetched successfully",
            data={"percent": battery.percent, "is_plugged": battery.power_plugged}
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

    

if __name__ == "__main__":
    sc = SystemController()
    print(sc.lock())
