# Building Tray App as an Elevated EXE

## Objective
Run the tray app with **administrator privileges** so system-level actions (Wi-Fi/Bluetooth toggle, volume/brightness control) work reliably.


## Process Overview
1. Add a **manifest file** requesting admin rights.
2. Build the app into an **EXE** using PyInstaller.
3. Include **all project dependencies** and folders (e.g., configs).
4. Test EXE to ensure system actions execute properly.


## Requirements
- Python installed with all dependencies (`psutil`, `pycaw`, `wmi`, etc.)
- PyInstaller
- Correct project folder structure
- Admin account for testing
- Optional: devcon or proper PowerShell commands for Bluetooth


## Considerations / Cautions
- EXE must be **run elevated** to toggle system hardware.
- Include **all data/config folders** explicitly in PyInstaller build.
- Avoid relative imports; use absolute paths or modify `sys.path`.
- Test carefully; misconfigured commands can disable Wi-Fi/Bluetooth.
- UAC prompts are unavoidable unless using Task Scheduler or helper services.


## Pros
- Full access to system-level actions.
- Consistent behavior on Windows, avoids “silent failures”.
- Cleaner deployment for end users.
- Easier to test privileged features early in development.

