import subprocess
from ..core.registry import action
from ..core.base_module import BaseModule
from ..core.helpers import confirm_with_timeout




class SystemController(BaseModule):
    NIRCMD = r"C:\Tools\nircmd\nircmd.exe"

    def _run(self, cmd):
        subprocess.Popen(cmd, shell=True)

    @action(name="shutdown")
    def shutdown(self):
        if confirm_with_timeout("Shutdown in 5 seconds?", "Confirm Shutdown"):
            self._run("shutdown /s /t 0")
            return self.success("Shutting down")
        return self.success("Cancelled")
    

    @action(name="restart")
    def restart(self):
        if confirm_with_timeout("Restart in 5 seconds?", "Confirm Restart"):
            self._run("shutdown /r /t 0")
            return self.success("Restarting")
        return self.success("Cancelled")
    

    @action(name="logout")
    def logout(self):
        if confirm_with_timeout("Logout in 5 seconds?", "Confirm Logout"):
            self._run("shutdown /l")
            return self.success("Logging out")
        return self.success("Cancelled")
    

    @action(name="sleep")
    def sleep(self):
        if confirm_with_timeout("Sleep in 5 seconds?", "Confirm Sleep"):
            self._run("powershell -command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)\"")
            return self.success("Sleeping")
        return self.success("Cancelled")
    

    @action(name="lock")
    def lock(self):
        self._run("rundll32.exe user32.dll,LockWorkStation")
        return self.success("Locked")
    

    @action(name="brightness", params={"value"})
    def brightness(self, value):
        value = max(0, min(100, value))
        self._run(f"\"{self.NIRCMD}\" setbrightness {value}")
        return self.success(f"Brightness set to {value}%")
    

    @action(name="volume", params={"value"})
    def volume(self, value):
        system_value = int(65535 * (value / 100))
        self._run(f"\"{self.NIRCMD}\" setsysvolume {system_value}")
        return self.success(f"Volume set to {value}%")
    

if __name__ == "__main__":
    sc = SystemController()
    print(sc.lock())
