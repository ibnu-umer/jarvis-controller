# AppModule

`AppModule` provides advanced control and automation over desktop applications. It is designed to handle launching, window management, multi-instance handling, and app-specific automation.


## **1. Launch & Close**

| Function | Parameters | Description |
|----------|------------|-------------|
| `open_app(app_name, args=None)` | `app_name: str`, `args: list[str] \| None` | Launches the specified application with optional arguments. |
| `close_app(app_name, force=False)` | `app_name: str`, `force: bool` | Closes the application. Forces termination if `force=True`. |
| `close_all_instances(app_name)` | `app_name: str` | Closes all running instances of the specified app. |


## **2. Window Management**

| Function | Parameters | Description |
|----------|------------|-------------|
| `focus_app(app_name)` | `app_name: str` | Brings the app window to the foreground. |
| `minimize_app(app_name)` | `app_name: str` | Minimizes the app window. |
| `maximize_app(app_name)` | `app_name: str` | Maximizes the app window. |
| `restore_app(app_name)` | `app_name: str` | Restores the app from minimized or maximized state. |
| `move_app(app_name, x, y)` | `app_name: str`, `x: int`, `y: int` | Moves the app window to specified screen coordinates. |
| `resize_app(app_name, width, height)` | `app_name: str`, `width: int`, `height: int` | Resizes the app window. |


## **3. Multi-Instance & State**

| Function | Parameters | Description |
|----------|------------|-------------|
| `is_running(app_name)` | `app_name: str` | Returns `True` if the app is currently running. |
| `list_instances(app_name)` | `app_name: str` | Returns all running instances (PIDs/windows) of the app. |
| `switch_instance(app_name, instance_number)` | `app_name: str`, `instance_number: int` | Switches focus between multiple instances of the app. |


## **4. App-Specific Shortcuts / Automation**

| Function | Parameters | Description |
|----------|------------|-------------|
| `send_key(app_name, key_combo)` | `app_name: str`, `key_combo: str` | Sends a keyboard shortcut to the app. |
| `send_text(app_name, text)` | `app_name: str`, `text: str` | Automates typing into the app. |
| `screenshot_app(app_name)` | `app_name: str` | Captures a screenshot of the app window. |


## **5. Advanced Controls**

| Function | Parameters | Description |
|----------|------------|-------------|
| `pin_to_taskbar(app_name)` | `app_name: str` | Pins the application to the taskbar. |
| `unpin_from_taskbar(app_name)` | `app_name: str` | Unpins the application from the taskbar. |
| `set_always_on_top(app_name, enable=True)` | `app_name: str`, `enable: bool` | Sets the app window to always be on top. |
| `get_app_info(app_name)` | `app_name: str` | Retrieves app info: path, version, PID, memory usage. |

---

## **Notes**

- All functions are designed to handle exceptions and return meaningful error messages.
- Supports multi-instance applications and can target windows individually.
- Intended for integration with a command listener or automation engine.
